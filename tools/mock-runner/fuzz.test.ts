// Fuzzing of the plugin API surface, run with: node --test tools/mock-runner/fuzz.test.ts
// Every function reachable from `ayu` is called with random arguments. The prelude may refuse
// bad input by throwing, but it must never pass the host anything that is not JSON, never hang,
// and the plugin must keep working afterwards.
import assert from "node:assert/strict";
import path from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { loadPrelude, Sandbox } from "./mock.ts";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const prelude = loadPrelude(process.env.PRELUDE ?? path.join(root, "patches/voidgram-big-update.patch"));
const iterations = Number(process.env.FUZZ_ITERATIONS ?? 3000);

// A small deterministic PRNG so failures can be replayed with FUZZ_SEED.
function rng(seed: number) {
  let state = seed >>> 0 || 1;
  return () => {
    state ^= state << 13;
    state ^= state >>> 17;
    state ^= state << 5;
    return (state >>> 0) / 0x100000000;
  };
}

const samples = ["", "a", "ℵ\u0000￿", "🧪".repeat(50), "x".repeat(70000), "{\"json\":1}", "../../etc/passwd", "javascript:alert(1)", "\\u0000", "-1", "1e309"];

function value(random: () => number, depth = 0): unknown {
  const pick = Math.floor(random() * 11);
  switch (pick) {
    case 0: return undefined;
    case 1: return null;
    case 2: return random() < 0.5;
    case 3: return [0, -1, 1.5, Number.MAX_SAFE_INTEGER, NaN, Infinity][Math.floor(random() * 6)];
    case 4: return samples[Math.floor(random() * samples.length)];
    case 5: return () => samples[Math.floor(random() * samples.length)];
    case 6: return depth > 2 ? {} : Object.fromEntries(Array.from({ length: Math.floor(random() * 4) }, (_, i) => ["k" + i, value(random, depth + 1)]));
    case 7: return depth > 2 ? [] : Array.from({ length: Math.floor(random() * 4) }, () => value(random, depth + 1));
    case 8: return { peerId: "123", messageId: 5, text: "hi", id: "x", title: "t" };
    case 9: return Symbol("s");
    default: return BigInt(7);
  }
}

function collect(object: unknown, prefix: string, out: [string, Function][], seen = new Set<unknown>()) {
  if (!object || (typeof object !== "object" && typeof object !== "function") || seen.has(object)) return;
  seen.add(object);
  for (const key of Object.getOwnPropertyNames(object)) {
    if (key === "prototype" || key === "constructor") continue;
    let child: unknown;
    try { child = (object as any)[key]; } catch { continue; }
    if (typeof child === "function") out.push([prefix + key, child as Function]);
    if (child && typeof child === "object") collect(child, prefix + key + ".", out, seen);
  }
}

test("random calls never reach the host with non-JSON arguments", async () => {
  const seed = Number(process.env.FUZZ_SEED ?? 27_5_0);
  const random = rng(seed);
  const sandbox = new Sandbox({ prelude });
  sandbox.load("globalThis.ayuRef = ayu;");
  const functions: [string, Function][] = [];
  collect((sandbox as any).context.ayuRef, "ayu.", functions);
  assert.ok(functions.length > 40, `expected the full API surface, found ${functions.length}`);

  for (let i = 0; i < iterations; i++) {
    const [name, fn] = functions[Math.floor(random() * functions.length)];
    const args = Array.from({ length: Math.floor(random() * 4) }, () => value(random));
    const before = sandbox.calls.length;
    try {
      const result = fn(...args);
      if (result && typeof (result as any).then === "function") (result as Promise<unknown>).catch(() => {});
    } catch {
      // Refusing bad input by throwing is fine.
    }
    for (const call of sandbox.calls.slice(before)) {
      assert.equal(typeof call.op, "string", `${name}: op must be a string (seed ${seed}, step ${i})`);
      assert.doesNotThrow(() => JSON.stringify(call.args), `${name}: host args must be JSON (seed ${seed}, step ${i})`);
    }
  }

  // The plugin still works after the storm.
  sandbox.load(`ayu.commands.register('ping', 'Ping', () => 'pong');`);
  assert.equal(sandbox.send(".ping"), "pong");
  sandbox.dispose();
});
