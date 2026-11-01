// AyuGram plugin SDK for AssemblyScript.
//
// Build:  npx asc plugin.ts -o plugin.wasm --runtime stub -O3z --noAssert --use abort=
// Then:   ayu pack plugin.wasm manifest.json plugin.wasm
//
// Same ABI as the Rust, Zig and TinyGo SDKs. Re-export the entry points from your plugin:
//
//   export { ayu_alloc, ayu_free, ayu_dispatch } from "./ayu";
//   import { log, before, OUTGOING_TEXT } from "./ayu";
//   export function ayu_init(): void {
//     before(OUTGOING_TEXT, (text: string, peerId: string): string | null => text.toUpperCase());
//     log("loaded");
//   }

@external("ayu", "host")
declare function host(pointer: usize, length: usize): u64;

export const OUTGOING_TEXT = "message.outgoing.text";
export const LYRICS_TEXT = "lyrics.text";
export const LINK_OPEN = "link.open";
export const MESSAGE_RENDER = "message.render";

export function ayu_alloc(length: usize): usize {
  return heap.alloc(length > 0 ? length : 1);
}

export function ayu_free(pointer: usize, length: usize): void {
  if (pointer != 0) heap.free(pointer);
}

function give(text: string): u64 {
  const bytes = String.UTF8.encode(text);
  const length = <usize>bytes.byteLength;
  const pointer = ayu_alloc(length);
  memory.copy(pointer, changetype<usize>(bytes), length);
  return (<u64>pointer << 32) | <u64>length;
}

function take(pointer: usize, length: usize): string {
  const text = String.UTF8.decodeUnsafe(pointer, length);
  ayu_free(pointer, length);
  return text;
}

/** Sends a JSON request to the app and returns its JSON answer ("" when there is none). */
export function request(message: string): string {
  const bytes = String.UTF8.encode(message);
  const packed = host(changetype<usize>(bytes), <usize>bytes.byteLength);
  if (packed == 0) return "";
  return take(<usize>(packed >> 32), <usize>(packed & 0xffffffff));
}

/** JSON string literal. */
export function quote(text: string): string {
  let out = "\"";
  for (let i = 0; i < text.length; i++) {
    const c = text.charCodeAt(i);
    if (c == 0x22) out += "\\\"";
    else if (c == 0x5c) out += "\\\\";
    else if (c == 0x0a) out += "\\n";
    else if (c == 0x0d) out += "\\r";
    else if (c == 0x09) out += "\\t";
    else if (c < 0x20) out += "\\u00" + (c < 16 ? "0" : "") + c.toString(16);
    else out += String.fromCharCode(c);
  }
  return out + "\"";
}

/** The value of `"key":"…"` in a flat JSON object. */
export function stringField(json: string, key: string): string | null {
  const needle = "\"" + key + "\":";
  let index = json.indexOf(needle);
  if (index < 0) return null;
  index += needle.length;
  while (index < json.length && json.charCodeAt(index) == 0x20) index++;
  if (index >= json.length || json.charCodeAt(index) != 0x22) return null;
  index++;
  let out = "";
  while (index < json.length) {
    const c = json.charCodeAt(index);
    if (c == 0x22) return out;
    if (c == 0x5c && index + 1 < json.length) {
      index++;
      const e = json.charCodeAt(index);
      out += e == 0x6e ? "\n" : e == 0x74 ? "\t" : e == 0x72 ? "\r" : String.fromCharCode(e);
    } else {
      out += String.fromCharCode(c);
    }
    index++;
  }
  return null;
}

function numberField(json: string, key: string): i32 {
  const needle = "\"" + key + "\":";
  let index = json.indexOf(needle);
  if (index < 0) return 0;
  index += needle.length;
  let value = 0;
  while (index < json.length) {
    const c = json.charCodeAt(index);
    if (c < 0x30 || c > 0x39) break;
    value = value * 10 + (c - 0x30);
    index++;
  }
  return value;
}

export function log(text: string): void {
  request("{\"op\":\"log\",\"level\":\"info\",\"text\":" + quote(text) + "}");
}

export function toast(text: string): void {
  request("{\"op\":\"toast\",\"text\":" + quote(text) + "}");
}

/** Any extended API; `argsJson` is an object such as `{"id":"a","title":"A"}`. */
export function call(op: string, argsJson: string): string {
  const inner = argsJson.trim();
  const body = inner.length > 2 ? inner.substring(1, inner.length - 1).trim() : "";
  return request("{\"op\":" + quote(op) + (body.length > 0 ? "," + body : "") + "}");
}

type TextHandler = (text: string, peerId: string) => string | null;
type EventHandler = (payload: string) => void;

const textHandlers: TextHandler[] = [];
const eventNames: string[] = [];
const eventHandlers: EventHandler[] = [];

function register(point: string, mode: string, handler: TextHandler): void {
  textHandlers.push(handler);
  request("{\"op\":\"hook\",\"point\":" + quote(point) + ",\"mode\":" + quote(mode) + ",\"handler\":" + textHandlers.length.toString() + "}");
}

export function before(point: string, handler: TextHandler): void { register(point, "before", handler); }
export function after(point: string, handler: TextHandler): void { register(point, "after", handler); }
export function replace(point: string, handler: TextHandler): void { register(point, "replace", handler); }

export function on(event: string, handler: EventHandler): void {
  eventNames.push(event);
  eventHandlers.push(handler);
  request("{\"op\":\"on\",\"event\":" + quote(event) + "}");
}

export function ayu_dispatch(pointer: usize, length: usize): u64 {
  const message = take(pointer, length);
  const op = stringField(message, "op");
  if (op == "hook") {
    const id = numberField(message, "handler");
    if (id < 1 || id > textHandlers.length) return give("{\"text\":null}");
    const text = stringField(message, "text");
    const peer = stringField(message, "peerId");
    const result = textHandlers[id - 1](text != null ? text : "", peer != null ? peer : "");
    return give(result != null ? "{\"text\":" + quote(result) + "}" : "{\"text\":null}");
  }
  if (op == "event") {
    const name = stringField(message, "event");
    for (let i = 0; i < eventNames.length; i++) {
      if (eventNames[i] == name) eventHandlers[i](message);
    }
  }
  return give("{}");
}
