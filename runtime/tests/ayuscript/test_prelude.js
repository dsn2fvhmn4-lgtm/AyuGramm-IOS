// Exercises the AyuGram code-plugin prelude (AyuScriptRuntime.prelude) against a fake host.
// It does not run JavaScriptCore or the app; it checks the JavaScript API contract.
//   node runtime/tests/ayuscript/test_prelude.js /path/to/prepared/telegram
'use strict';
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const telegram = process.argv[2] || path.join(__dirname, '../../../.work/telegram');
const swift = fs.readFileSync(path.join(telegram, 'submodules/AccountContext/Sources/AyuScriptRuntime.swift'), 'utf8');
const match = swift.match(/static let prelude = """\n([\s\S]*?)\n    """/);
assert(match, 'prelude not found');
const prelude = match[1].replace(/^    /gm, '');

function makeHost() {
    const calls = { hooks: [], features: [], logs: [], toasts: [], storage: {}, events: {}, timers: [] };
    const host = {
        pluginId: 'test-plugin',
        log: (level, text) => calls.logs.push([level, text]),
        hook: (point, mode, fn) => { calls.hooks.push({ point, mode, fn }); return true; },
        feature: (name, disabled) => { calls.features.push([name, disabled]); return true; },
        on: (event, fn) => { (calls.events[event] = calls.events[event] || []).push(fn); },
        storageGet: (key) => calls.storage[key],
        storageSet: (key, value) => { if (value === null) delete calls.storage[key]; else calls.storage[key] = value; },
        toast: (text) => calls.toasts.push(text),
        setTimer: (fn, ms, repeats) => { calls.timers.push({ fn, ms, repeats }); return calls.timers.length; },
        clearTimer: () => {}
    };
    return { host, calls };
}

function run(plugin) {
    const { host, calls } = makeHost();
    const sandbox = { __ayuHost: host };
    sandbox.globalThis = sandbox;
    vm.createContext(sandbox);
    vm.runInContext(prelude, sandbox);
    assert.strictEqual(sandbox.__ayuHost, undefined, 'host object must be hidden from plugins');
    vm.runInContext(plugin, sandbox);
    return { sandbox, calls };
}

// 1. replace the outgoing text handler; non-string results leave the text unchanged.
{
    const { calls } = run(`
        ayu.hooks.replace(ayu.hooks.points.outgoingText, (text, ctx) => text.toUpperCase() + ' #' + ctx.peerId);
        ayu.hooks.after('message.outgoing.text', (text) => 42);
    `);
    assert.strictEqual(calls.hooks.length, 2);
    assert.deepStrictEqual(calls.hooks.map((h) => h.mode), ['replace', 'after']);
    assert.strictEqual(calls.hooks[0].point, 'message.outgoing.text');
    assert.strictEqual(calls.hooks[0].fn('hi', { peerId: '7' }), 'HI #7');
    assert.strictEqual(calls.hooks[1].fn('hi', {}), undefined);
}

// 2. features, storage, console, toast.
{
    const { calls } = run(`
        ayu.features.disable('fastShare');
        ayu.features.enable('stories');
        ayu.storage.set('n', 5);
        console.log('stored', ayu.storage.get('n'), { a: 1 });
        ayu.toast('hello');
    `);
    assert.deepStrictEqual(calls.features, [['fastShare', true], ['stories', false]]);
    assert.strictEqual(calls.storage.n, '5');
    assert.deepStrictEqual(calls.logs[0], ['info', 'stored 5 {"a":1}']);
    assert.deepStrictEqual(calls.toasts, ['hello']);
}

// 3. WhiteGram compatibility: registerPlugin runs onLoad and maps onUnload.
{
    const { calls } = run(`
        class P extends wg.BasePlugin { onLoad() { wg.log('loaded'); wg.setStorage('k', 'v'); } onUnload() { wg.log('bye'); } }
        wg.registerPlugin(new P());
    `);
    assert.deepStrictEqual(calls.logs[0], ['info', 'loaded']);
    assert.strictEqual(calls.storage.k, 'v');
    calls.events.unload[0]();
    assert.deepStrictEqual(calls.logs[1], ['info', 'bye']);
}

// 4. API objects are frozen and invalid handlers are rejected.
{
    assert.throws(() => run(`ayu.hooks.replace('message.outgoing.text', 'nope');`), /must be a function/);
    const { sandbox } = run(`ayu.hooks.replace = null;`);
    assert.strictEqual(typeof sandbox.ayu.hooks.replace, 'function');
}

console.log('ayuscript prelude: all checks passed');
