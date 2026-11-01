// Tests of the app's JavaScript prelude (27.5 APIs), run with: node --test tools/mock-runner/prelude.test.ts
// PRELUDE points at AyuScriptRuntime.swift or at the AyuGram patch (default: the patch in this repo).
import assert from "node:assert/strict";
import path from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { loadPrelude, Sandbox } from "./mock.ts";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const prelude = loadPrelude(process.env.PRELUDE ?? path.join(root, "patches/ayugram-big-update.patch"));

test("dot commands replace or cancel the outgoing text", () => {
  const sandbox = new Sandbox({ prelude });
  sandbox.load(`
    ayu.commands.register('calc', 'Calculate', (args) => String(args.split('+').reduce((a, b) => a + Number(b), 0)));
    ayu.commands.register('.silent', 'Swallow', () => null);
  `);
  assert.equal(sandbox.send(".calc 2+3+4"), "9");
  assert.equal(sandbox.send(".silent anything"), null);
  assert.equal(sandbox.send("plain text"), "plain text");
  assert.equal(sandbox.send(".unknown x"), ".unknown x");
  sandbox.dispose();
});

test("commands need the commands permission", () => {
  const sandbox = new Sandbox({ prelude, permissions: [] });
  sandbox.load(`globalThis.ok = ayu.commands.register('calc', 'x', () => '1');`);
  assert.equal(sandbox.send(".calc"), ".calc");
  sandbox.dispose();
});

test("net.fetch resolves with status, headers, text and json()", async () => {
  const sandbox = new Sandbox({ prelude, responders: { "net.fetch": (args) => ({ status: 200, headers: { "content-type": "application/json" }, text: JSON.stringify({ url: args.url }) }) } });
  sandbox.load(`globalThis.result = ayu.net.fetch('https://api.example.com/x').then((r) => r.json().url + ' ' + r.status);`);
  const value = await (sandbox as any).context.result;
  assert.equal(value, "https://api.example.com/x 200");
  sandbox.dispose();
});

test("an error answer rejects the promise", async () => {
  const sandbox = new Sandbox({ prelude, responders: { "ai.complete": () => ({ error: "No AI service" }) } });
  sandbox.load(`globalThis.result = ayu.ai.complete('hi').then(() => 'resolved', (e) => 'rejected: ' + e.message);`);
  assert.equal(await (sandbox as any).context.result, "rejected: No AI service");
  sandbox.dispose();
});

test("bus messages from other plugins arrive, own ones are ignored", () => {
  const sandbox = new Sandbox({ prelude, pluginId: "me" });
  sandbox.load(`globalThis.got = []; ayu.bus.on('ping', (data, from) => globalThis.got.push(from + ':' + data.n));`);
  sandbox.emit("busMessage", { topic: "ping", data: { n: 1 }, from: "other" });
  sandbox.emit("busMessage", { topic: "ping", data: { n: 2 }, from: "me" });
  sandbox.emit("busMessage", { topic: "pong", data: { n: 3 }, from: "other" });
  assert.deepEqual([...(sandbox as any).context.got], ["other:1"]);
  sandbox.dispose();
});

test("i18n picks the app language, then English", () => {
  const sandbox = new Sandbox({ prelude });
  sandbox.load(`globalThis.a = ayu.i18n.t({ ru: 'привет', en: 'hi' }); globalThis.b = ayu.i18n.t({ en: 'hi' }); globalThis.c = ayu.i18n.language;`);
  const context = (sandbox as any).context;
  assert.equal(context.a, "привет");
  assert.equal(context.b, "hi");
  assert.equal(context.c, "ru");
  sandbox.dispose();
});

test("scheduler.at fires once and cancel stops it", async () => {
  const sandbox = new Sandbox({ prelude });
  sandbox.load(`globalThis.fired = 0; ayu.scheduler.at(Date.now() + 20, () => globalThis.fired++); const id = ayu.scheduler.at(Date.now() + 20, () => globalThis.fired += 10); ayu.scheduler.cancel(id);`);
  await new Promise((resolve) => setTimeout(resolve, 80));
  assert.equal((sandbox as any).context.fired, 1);
  sandbox.dispose();
});

test("link.open hooks rewrite URLs", () => {
  const sandbox = new Sandbox({ prelude });
  sandbox.load(`ayu.hooks.before(ayu.hooks.points.linkOpen, (url) => url.replace('https://x.com/', 'https://fxtwitter.com/'));`);
  assert.equal(sandbox.hook("link.open", "https://x.com/user/status/1"), "https://fxtwitter.com/user/status/1");
  sandbox.dispose();
});
