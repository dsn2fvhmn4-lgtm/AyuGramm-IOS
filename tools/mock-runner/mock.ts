// Runs AyuGram JavaScript plugins in Node, without a phone, on the app's real prelude.
// The prelude (the `ayu` API) is read from AyuScriptRuntime.swift or from the AyuGram patch, and the
// native bridge it talks to (`__ayuHost`) is mocked here, so plugin tests exercise the same code
// paths the app does.
import fs from "node:fs";
import vm from "node:vm";

export type HostCall = { op: string; args: Record<string, unknown> };
type Handler = (value: unknown, ctx?: unknown) => unknown;

/** Swift string literal body → JavaScript source. */
function unescapeSwift(body: string): string {
  const simple: Record<string, string> = { "\\\\": "\\", '\\"': '"', "\\n": "\n", "\\t": "\t", "\\r": "\r", "\\0": "\0", "\\'": "'" };
  let out = "";
  for (let i = 0; i < body.length; i++) {
    if (body[i] === "\\" && i + 1 < body.length) {
      const pair = body.slice(i, i + 2);
      if (pair in simple) {
        out += simple[pair];
        i += 1;
        continue;
      }
      const unicode = /^\\u\{([0-9a-fA-F]+)\}/.exec(body.slice(i));
      if (unicode) {
        out += String.fromCodePoint(parseInt(unicode[1], 16));
        i += unicode[0].length - 1;
        continue;
      }
      throw new Error(`Invalid Swift escape ${pair} in the prelude`);
    }
    out += body[i];
  }
  return out;
}

/** The prelude from AyuScriptRuntime.swift, or from the AyuGram patch that adds it. */
export function loadPrelude(path: string): string {
  let swift = fs.readFileSync(path, "utf8");
  if (path.endsWith(".patch")) {
    const marker = "+++ b/submodules/AccountContext/Sources/AyuScriptRuntime.swift";
    const start = swift.indexOf(marker);
    if (start < 0) throw new Error("AyuScriptRuntime.swift is not in this patch");
    const end = swift.indexOf("\ndiff --git", start);
    swift = swift.slice(start, end < 0 ? undefined : end).split("\n").filter((line) => line.startsWith("+") && !line.startsWith("+++")).map((line) => line.slice(1)).join("\n");
  }
  const open = 'static let prelude = """\n';
  const start = swift.indexOf(open);
  if (start < 0) throw new Error("No prelude found");
  const end = swift.indexOf('\n    """', start + open.length);
  const lines = swift.slice(start + open.length, end).split("\n").map((line) => line.startsWith("    ") ? line.slice(4) : line);
  return unescapeSwift(lines.join("\n"));
}

export interface SandboxOptions {
  prelude: string;
  pluginId?: string;
  /** Answers for host calls; asynchronous ones (net.fetch, ai.complete, messages.*) answer via uiResult. */
  responders?: Record<string, (args: Record<string, unknown>) => unknown>;
  permissions?: string[];
}

export class Sandbox {
  readonly logs: { level: string; text: string }[] = [];
  readonly toasts: string[] = [];
  readonly calls: HostCall[] = [];
  readonly storage = new Map<string, string>();
  private readonly hooks: { point: string; mode: string; fn: Handler }[] = [];
  private readonly events = new Map<string, Handler[]>();
  private readonly timers = new Map<number, NodeJS.Timeout>();
  private nextTimer = 1;
  private readonly context: vm.Context;
  private readonly permissions: Set<string>;
  private readonly asyncOps = new Set(["net.fetch", "ai.complete", "messages.send", "messages.edit", "messages.react", "messages.get", "permissions.request", "ui.alert", "ui.sheet", "ui.gifts.catalog.list"]);

  private readonly options: SandboxOptions;

  constructor(options: SandboxOptions) {
    this.options = options;
    this.permissions = new Set(options.permissions ?? ["ui", "menu", "profile", "overlay", "fonts", "badges", "clipboard", "device", "haptics", "network", "messages", "ai", "secrets", "composer", "commands", "screens", "links", "notifications"]);
    const pluginId = options.pluginId ?? "test-plugin";
    const host = {
      pluginId,
      log: (level: string, text: string) => this.logs.push({ level, text }),
      toast: (text: string) => this.toasts.push(text),
      hook: (point: string, mode: string, fn: Handler) => { this.hooks.push({ point, mode, fn }); return true; },
      feature: () => true,
      on: (event: string, fn: Handler) => { this.events.set(event, [...(this.events.get(event) ?? []), fn]); },
      settingsDeclare: () => true,
      settingGet: () => undefined,
      storageGet: (key: string) => this.storage.get(key),
      storageSet: (key: string, value: string | null) => { if (value === null) this.storage.delete(key); else this.storage.set(key, value); },
      setTimer: (fn: () => void, ms: number, repeats: boolean) => {
        const id = this.nextTimer++;
        this.timers.set(id, repeats ? setInterval(fn, ms) : setTimeout(() => { this.timers.delete(id); fn(); }, ms));
        return id;
      },
      clearTimer: (id: number) => { const timer = this.timers.get(id); if (timer) { clearTimeout(timer); this.timers.delete(id); } },
      playerState: () => ({}),
      playerControl: () => false,
      call: (op: string, args: Record<string, unknown>) => this.call(op, args ?? {}),
    };
    this.context = vm.createContext({ __ayuHost: host, Promise, JSON, Math, Date, Object, Array, String, Number, Boolean, Error, TypeError, RegExp, Map, Set });
    vm.runInContext(options.prelude, this.context, { filename: "prelude.js" });
  }

  private call(op: string, args: Record<string, unknown>): unknown {
    this.calls.push({ op, args });
    const responder = this.options.responders?.[op];
    if (op === "commands.register") {
      let name = String(args.name ?? "").toLowerCase();
      if (!name.startsWith(".")) name = "." + name;
      return this.permissions.has("commands") ? { ok: true, name } : null;
    }
    if (op === "i18n.language") return { language: "ru" };
    if (op === "permissions.has") return { has: this.permissions.has(String(args.name)) };
    if (this.asyncOps.has(op)) {
      const requestId = args.requestId;
      const value = responder ? responder(args) : { error: `no mock answer for ${op}` };
      setImmediate(() => this.emit("uiResult", { requestId, choice: value }));
      return { ok: true };
    }
    return responder ? responder(args) : { ok: true };
  }

  load(source: string, filename = "plugin.js"): this {
    vm.runInContext(source, this.context, { filename });
    this.emit("load", {});
    return this;
  }

  emit(event: string, payload: unknown): void {
    for (const fn of this.events.get(event) ?? []) fn(payload);
  }

  /** Runs the outgoing-text hooks like the app does; null means the message is dropped. */
  send(text: string, ctx: Record<string, unknown> = { peerId: "1" }): string | null {
    let value = text;
    for (const mode of ["before", "replace", "after"]) {
      for (const hook of this.hooks.filter((h) => h.point === "message.outgoing.text" && h.mode === mode)) {
        const result = hook.fn(value, ctx);
        if (typeof result === "string") value = result;
      }
    }
    return value === "\u0000" ? null : value;
  }

  hook(point: string, value: string, ctx: Record<string, unknown> = {}): string {
    let result = value;
    for (const hook of this.hooks.filter((h) => h.point === point)) {
      const changed = hook.fn(result, ctx);
      if (typeof changed === "string") result = changed;
    }
    return result;
  }

  dispose(): void {
    for (const timer of this.timers.values()) clearTimeout(timer);
    this.timers.clear();
  }
}
