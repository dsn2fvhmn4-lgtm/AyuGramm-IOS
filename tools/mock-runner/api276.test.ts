// Tests of the 27.6 plugin APIs: the helpers that run in the plugin and the wrappers of host calls.
// PRELUDE points at AyuScriptRuntime.swift or at a patch that adds it.
import assert from "node:assert/strict";
import path from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { loadPrelude, Sandbox } from "./mock.ts";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const prelude = loadPrelude(process.env.PRELUDE ?? path.join(root, "patches/ayugram-port-fixes.patch"));

function run(source: string, responders = {}) {
  const sandbox = new Sandbox({ prelude, responders });
  sandbox.load(`globalThis.out = (function () { ${source} })();`);
  const raw = (sandbox as any).context.out;
  // Values made in the sandbox have its own Array and Object; compare them as plain JSON.
  const out = raw && typeof raw.then === "function" ? raw.then((v: unknown) => JSON.parse(JSON.stringify(v))) : JSON.parse(JSON.stringify(raw));
  return { out, sandbox };
}

test("text helpers", () => {
  const { out } = run(`return [
    ayu.text.capitalize('привет'), ayu.text.titleCase('hello big world'), ayu.text.reverse('a👍b'),
    ayu.text.truncate('abcdefgh', 5), ayu.text.slugify('Привет, Мир!'), ayu.text.wordCount("it's a good-day, ok"),
    ayu.text.charCount('👍🏽ab'), ayu.text.stripEmoji('hi 👋 there'), ayu.text.escapeHtml('<a href="x">'),
    ayu.text.unescapeHtml('&lt;b&gt; &amp;'), ayu.text.translit('Щука ёж'), ayu.text.swapLayout('ghbdtn'),
    ayu.text.mock('hello'), ayu.text.between('a[b]c', '[', ']'), ayu.text.template('Hi {name}, {x}', { name: 'Mei' })
  ];`);
  assert.deepEqual(out, ["Привет", "Hello Big World", "b👍a", "abcd…", "privet-mir", 4, 4, "hi there", "&lt;a href=&quot;x&quot;&gt;",
    "<b> &", "Shchuka yozh", "привет", "hElLo", "b", "Hi Mei, {x}"]);
});

test("date helpers", () => {
  const { out } = run(`
    const d = new Date(2026, 10, 3, 9, 5, 7);
    return [ayu.date.format(d, 'DD.MM.YYYY HH:mm:ss'), ayu.date.format(ayu.date.addDays(d, 30), 'YYYY-MM-DD'),
      ayu.date.diffDays(new Date(2026, 0, 1), new Date(2026, 0, 31)), ayu.date.isToday(Date.now()),
      ayu.date.startOfDay(d).getHours(), ayu.date.parseDuration('1h 30m'), ayu.date.parseDuration('nope'),
      ayu.date.formatDuration(3723000, 'en'), ayu.date.formatDuration(90000, 'ru'),
      ayu.date.relative(Date.now() - 5 * 60000, 'ru'), ayu.date.relative(Date.now() + 2 * 3600000, 'en'),
      ayu.date.relative(Date.now() - 22 * 86400000, 'ru')];`);
  assert.deepEqual(out, ["03.11.2026 09:05:07", "2026-12-03", 30, true, 0, 5400000, null, "1h 2m 3s", "1 мин 30 с",
    "5 минут назад", "in 2 hours", "22 дня назад"]);
});

test("color, math and format helpers", () => {
  const { out } = run(`return [
    ayu.color.hexToRgb('#0a0'), ayu.color.rgbToHex(255, 128, 0), ayu.color.lighten('#000000', 0.5), ayu.color.darken('#FFFFFF', 0.25),
    ayu.color.mix('#FF0000', '#0000FF'), ayu.color.contrastText('#FFFF00'), /^#[0-9A-F]{6}$/.test(ayu.color.random()),
    ayu.math.clamp(15, 0, 10), ayu.math.lerp(0, 10, 0.25), ayu.math.round(3.14159, 2), ayu.math.sum([1, 2, '3']),
    ayu.math.average([2, 4]), ayu.math.median([5, 1, 3, 2]), ayu.math.percent(1, 4),
    (() => { const n = ayu.math.randomInt(1, 3); return n >= 1 && n <= 3 && Number.isInteger(n); })(),
    (() => { const n = ayu.math.random(5, 6); return n >= 5 && n < 6; })(),
    ayu.format.bytes(1536), ayu.format.bytes(512), ayu.format.number(1234567.891), ayu.format.plural(21, ['яблоко', 'яблока', 'яблок']),
    ayu.format.plural(12, ['яблоко', 'яблока', 'яблок']), ayu.format.plural(3, ['яблоко', 'яблока', 'яблок'])
  ];`);
  assert.deepEqual(out, [{ r: 0, g: 170, b: 0 }, "#FF8000", "#808080", "#BFBFBF", "#800080", "#000000", true, 10, 2.5, 3.14, 6, 3, 2.5, 25,
    true, true, "1.5 KB", "512 B", "1 234 567,89", "яблоко", "яблок", "яблока"]);
});

test("url, array, extract helpers", () => {
  const { out } = run(`return [
    ayu.url.parse('https://Example.com:8080/a/b?x=1&y=hello%20world#top'), ayu.url.build('https://a.b/c', { q: 'x y', n: 1, skip: null }),
    ayu.url.param('https://a.b/?id=42', 'id'), ayu.url.isUrl('https://t.me/x'), ayu.url.isUrl('nope'),
    ayu.url.extract('see https://a.b/c, and t.me/void.'), ayu.url.domain('https://www.github.com/x'),
    ayu.array.chunk([1, 2, 3, 4, 5], 2), ayu.array.unique([1, 1, 2, 3, 3]), ayu.array.unique([{ id: 1 }, { id: 1 }], 'id').length,
    ayu.array.shuffle([1, 2, 3]).sort(), [1, 2].includes(ayu.array.sample([1, 2])), ayu.array.groupBy([1, 2, 3, 4], (n) => n % 2 ? 'odd' : 'even'),
    ayu.array.sortBy([{ n: 2 }, { n: 1 }], 'n').map((x) => x.n), ayu.array.sortBy([1, 3, 2], (x) => x, true),
    ayu.extract.mentions('hi @neosay and @ab, mail a@b.com'), ayu.extract.hashtags('#Привет и #ios_26'), ayu.extract.emails('write me: me@void.gram!')
  ];`);
  assert.deepEqual(out, [
    { protocol: "https", host: "example.com", port: 8080, path: "/a/b", query: { x: "1", y: "hello world" }, hash: "top" },
    "https://a.b/c?q=x%20y&n=1", "42", true, false, ["https://a.b/c", "t.me/void"], "github.com",
    [[1, 2], [3, 4], [5]], [1, 2, 3], 1, [1, 2, 3], true, { odd: [1, 3], even: [2, 4] }, [1, 2], [3, 2, 1],
    ["@neosay"], ["#Привет", "#ios_26"], ["me@void.gram"]]);
});

test("host wrappers pass arguments and unwrap values", async () => {
  const { out, sandbox } = run(`return [
    ayu.crypto.sha256('abc'), ayu.crypto.uuid(), ayu.encoding.base64Encode('hi'), ayu.app.name(), ayu.app.plugins(),
    ayu.device.model(), ayu.device.darkMode(), ayu.speech.speak('привет', { rate: 0.5 }), ayu.notify.schedule({ title: 't', seconds: 10 }),
    ayu.haptics.pattern(['light', 'heavy'], 80)
  ];`, {
    "crypto.sha256": (a: any) => ({ value: "hash:" + a.text }), "crypto.uuid": () => ({ value: "u-1" }),
    "encoding.base64Encode": (a: any) => ({ value: Buffer.from(a.text).toString("base64") }), "app.name": () => ({ value: "VoidGram" }),
    "app.plugins": () => ({ value: [{ id: "x" }] }), "device.model": () => ({ value: "iPhone17,1" }), "device.darkMode": () => ({ value: true }),
    "notify.schedule": (a: any) => ({ value: "id-" + a.seconds })
  });
  assert.deepEqual(out, ["hash:abc", "u-1", "aGk=", "VoidGram", [{ id: "x" }], "iPhone17,1", true, true, "id-10", true]);
  const calls = sandbox.calls.map((c) => c.op);
  assert.ok(calls.includes("speech.speak") && calls.includes("haptics.pattern"));
  assert.deepEqual(sandbox.calls.find((c) => c.op === "haptics.pattern")!.args, { styles: ["light", "heavy"], interval: 80 });
  sandbox.dispose();
});

test("async helpers", async () => {
  const { out, sandbox } = run(`
    let tries = 0;
    return Promise.all([
      ayu.async.sleep(5).then(() => 'slept'),
      ayu.async.retry(() => { tries++; if (tries < 3) throw new Error('x'); return tries; }, 5, 1),
      ayu.async.timeout(new Promise(() => {}), 10).catch((e) => e.message),
      ayu.async.timeout(Promise.resolve(7), 50)
    ]);`);
  assert.deepEqual(await out, ["slept", 3, "Timed out after 10 ms", 7]);
  sandbox.dispose();
});
