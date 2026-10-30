'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const bridge = fs.readFileSync('runtime/whitegram/bridge.js', 'utf8');
const calls = [];
let nextTimer = 0;
const liveTimers = new Map();
const host = {
    call: (op, payload) => calls.push({ op, payload }),
    getInputText: () => 'draft',
    setTimeout: (fn) => { const id = ++nextTimer; liveTimers.set(id, fn); return id; },
    setInterval: (fn) => { const id = ++nextTimer; liveTimers.set(id, fn); return id; },
    clearTimeout: (id) => liveTimers.delete(id), clearInterval: (id) => liveTimers.delete(id)
};
const context = vm.createContext({});
vm.runInContext(bridge, context);
const runtime = context.AyuWhiteGram.create(host, {});
Object.assign(context, { wg: runtime.wg, setInterval: runtime.setInterval, clearInterval: runtime.clearInterval, setTimeout: runtime.setTimeout, clearTimeout: runtime.clearTimeout });
const path = process.argv[2] || 'runtime/tests/whitegram/fixture.js';
vm.runInContext(fs.readFileSync(path, 'utf8'), context, { timeout: 2000 });
assert.ok(calls.some(x => x.op === 'chat.button' && x.payload.id === 'tama_btn'));
assert.ok(calls.some(x => x.op === 'settings.page'));
assert.equal(liveTimers.size, 1);
runtime.emit('tama_open');
const sheet = calls.filter(x => x.op === 'ui.actionSheet').pop();
assert.ok(sheet && sheet.payload.options.length >= 3);
runtime.resolve(sheet.payload.callbackId, 0);
assert.ok(calls.some(x => x.op === 'vibrate'));
assert.ok(calls.some(x => x.op === 'storage.set' && x.payload.key === 'tamagotchi_state'));
const before = calls.length;
runtime.stop();
assert.equal(liveTimers.size, 0);
runtime.emit('tama_open');
assert.ok(calls.length >= before);
assert.ok(!calls.slice(before).some(x => x.op === 'ui.actionSheet'));
console.log('PASS: plugin lifecycle, chat controls, action callback, storage and cleanup: ' + path);

const second = context.AyuWhiteGram.create(host, {});
assert.equal(second.wg.getStorage('tamagotchi_state'), null, 'Storage is isolated per plugin');
second.stop();
