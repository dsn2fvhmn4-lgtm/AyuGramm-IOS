#!/usr/bin/env node
// ayu-mock — run a JavaScript plugin against the app's prelude without a phone.
//
//   node tools/mock-runner/cli.ts --prelude patches/voidgram-big-update.patch plugin.js \
//        [--send "text"]... [--event name '{"json":1}']... [--link https://x.com/a]
import fs from "node:fs";
import { loadPrelude, Sandbox } from "./mock.ts";

const args = process.argv.slice(2);
let preludePath = "";
let pluginPath = "";
const actions: [string, string, string?][] = [];
for (let i = 0; i < args.length; i++) {
  const arg = args[i];
  if (arg === "--prelude") preludePath = args[++i];
  else if (arg === "--send") actions.push(["send", args[++i]]);
  else if (arg === "--link") actions.push(["link", args[++i]]);
  else if (arg === "--event") { actions.push(["event", args[i + 1], args[i + 2]]); i += 2; }
  else pluginPath = arg;
}
if (!preludePath || !pluginPath) {
  console.error("usage: cli.ts --prelude <AyuScriptRuntime.swift | voidgram-big-update.patch> <plugin.js> [--send text] [--event name json] [--link url]");
  process.exit(2);
}

const sandbox = new Sandbox({ prelude: loadPrelude(preludePath) });
sandbox.load(fs.readFileSync(pluginPath, "utf8"), pluginPath);
for (const [kind, value, extra] of actions) {
  if (kind === "send") console.log(`send ${JSON.stringify(value)} -> ${JSON.stringify(sandbox.send(value))}`);
  if (kind === "link") console.log(`link ${value} -> ${sandbox.hook("link.open", value)}`);
  if (kind === "event") { sandbox.emit(value, extra ? JSON.parse(extra) : {}); console.log(`event ${value}`); }
}
setTimeout(() => {
  for (const line of sandbox.logs) console.log(`[${line.level}] ${line.text}`);
  for (const toast of sandbox.toasts) console.log(`[toast] ${toast}`);
  for (const call of sandbox.calls) console.log(`[call] ${call.op} ${JSON.stringify(call.args)}`);
  sandbox.dispose();
}, 50);
