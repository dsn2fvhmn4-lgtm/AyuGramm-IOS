'use strict';
// Smoke test: loads every WhiteGram .js plugin in a directory against the bridge and a fake host,
// drives chat open, button taps, settings rows and text commands, and fails on any operation the
// iOS host does not implement or on any exception raised by a plugin.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const bridge = fs.readFileSync(path.join(__dirname, '../../whitegram/bridge.js'), 'utf8');
// Operations handled by AyuWhiteGramEngine.handle in AyuWhiteGramRuntime.swift.
const supported = new Set(['storage.set', 'chat.remove', 'chat.button', 'chat.label', 'ui.actionSheet', 'vibrate', 'toast',
    'input.set', 'message.send', 'message.edit', 'settings.row', 'settings.page', 'menu.add', 'screen.hook', 'fetch', 'log']);
const commands = ['/ping example.com', '/roll', '/roll 10', '/fact', '/random пицца или суши', '2+2*2', '/weather Москва', 'привет'];
const directory = process.argv[2] || path.join(__dirname, 'plugins');
const files = fs.readdirSync(directory).filter(name => name.endsWith('.js')).sort();
assert.ok(files.length > 0, 'No plugins in ' + directory);
let failed = 0;
for (const file of files) {
    const calls = [], timers = new Map();
    let input = 'draft', nextTimer = 0;
    const host = {
        call: (op, payload) => { calls.push({ op, payload }); if (op === 'input.set') input = payload.text; },
        getInputText: () => input,
        setTimeout: (fn) => { const id = ++nextTimer; timers.set(id, fn); return id; },
        setInterval: (fn) => { const id = ++nextTimer; timers.set(id, fn); return id; },
        clearTimeout: (id) => timers.delete(id), clearInterval: (id) => timers.delete(id)
    };
    try {
        const context = vm.createContext({ console: { log() {}, error() {}, warn() {} } });
        vm.runInContext(bridge, context);
        const runtime = context.AyuWhiteGram.create(host, {});
        Object.assign(context, { wg: runtime.wg, setInterval: runtime.setInterval, clearInterval: runtime.clearInterval, setTimeout: runtime.setTimeout, clearTimeout: runtime.clearTimeout });
        vm.runInContext(fs.readFileSync(path.join(directory, file), 'utf8'), context, { timeout: 2000, filename: file });
        runtime.emit('onActivate', null);
        runtime.emit('onChatOpen', '777');
        for (const hook of calls.filter(x => x.op === 'screen.hook').map(x => x.payload.hookName)) runtime.emit(hook, '777');
        const hooks = new Set(calls.filter(x => ['chat.button', 'settings.row', 'menu.add'].includes(x.op)).map(x => x.payload.hookName));
        for (const hook of hooks) runtime.emit(hook, null);
        commands.forEach((text, index) => runtime.emit('onMessageReceive', { peerId: '777', messageId: 100 + index, text, out: true }));
        for (let i = 0; i < 3; i++) {
            for (const call of calls.filter(x => x.op === 'fetch' && !x.done)) { call.done = true; runtime.resolve(call.payload.callbackId, 'offline', null); }
            for (const call of calls.filter(x => x.op === 'ui.actionSheet' && !x.done)) { call.done = true; runtime.resolve(call.payload.callbackId, 0); }
        }
        for (const fn of [...timers.values()]) fn();
        runtime.stop();
        const errors = calls.filter(x => x.op === 'error');
        const unsupported = [...new Set(calls.map(x => x.op).filter(op => !supported.has(op) && op !== 'error'))];
        const used = [...new Set(calls.map(x => x.op))].sort().join(', ');
        if (errors.length || unsupported.length) {
            failed++;
            console.log('FAIL ' + file + (unsupported.length ? ' unsupported: ' + unsupported.join(', ') : '') + errors.map(x => '\n  ' + x.payload.message).join(''));
        } else {
            const edits = calls.filter(x => x.op === 'message.edit').length;
            console.log('PASS ' + file + ' [' + used + ']' + (edits ? ' edits=' + edits : ''));
        }
    } catch (error) {
        failed++;
        console.log('FAIL ' + file + ': ' + error);
    }
}
if (failed) { console.log(failed + ' of ' + files.length + ' plugins failed'); process.exit(1); }
console.log('PASS: ' + files.length + ' WhiteGram plugins');
