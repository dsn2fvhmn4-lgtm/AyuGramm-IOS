/* WhiteGram-compatible JavaScript API. Each plugin gets its own host and storage. */
(function (root) {
    'use strict';
    function create(host, initialStorage) {
        const events = new Map();
        const timers = new Set();
        const callbacks = new Map();
        const storage = Object.assign(Object.create(null), initialStorage || {});
        let nextCallback = 1;
        let plugin = null;
        let stopped = false;
        function call(op, payload) { if (!stopped) host.call(op, payload || {}); }
        function on(name, handler) {
            if (typeof name !== 'string' || typeof handler !== 'function') throw new TypeError('Invalid event handler');
            const list = events.get(name) || [];
            list.push(handler); events.set(name, list);
        }
        function emit(name, value) {
            if (stopped) return;
            for (const handler of (events.get(name) || []).slice()) {
                try { handler(value); } catch (error) { call('error', { event: name, message: String(error) }); }
            }
        }
        function timer(fn, ms, repeat) {
            if (typeof fn !== 'function') throw new TypeError('Timer callback must be a function');
            let id;
            const wrapped = function () {
                if (!repeat) timers.delete(id);
                if (!stopped) try { fn(); } catch (error) { call('error', { message: String(error) }); }
            };
            id = repeat ? host.setInterval(wrapped, Math.max(10, Number(ms) || 0)) : host.setTimeout(wrapped, Math.max(0, Number(ms) || 0));
            timers.add(id); return id;
        }
        function clear(id) { host.clearTimeout(id); host.clearInterval(id); timers.delete(id); }
        function request(op, payload, callback) {
            if (typeof callback !== 'function') throw new TypeError('Callback is required');
            const id = nextCallback++;
            callbacks.set(id, callback);
            call(op, Object.assign({}, payload, { callbackId: id }));
        }
        class BasePlugin { onLoad() {} onUnload() {} }
        const wg = {
            BasePlugin, on,
            registerPlugin(value) {
                if (!value || plugin) throw new Error('Only one plugin may be registered');
                plugin = value;
                if (typeof value.onLoad === 'function') value.onLoad();
            },
            getStorage(key) { return Object.prototype.hasOwnProperty.call(storage, key) ? storage[key] : null; },
            setStorage(key, value) {
                key = String(key); value = String(value);
                storage[key] = value; call('storage.set', { key, value });
            },
            toast(text) { call('toast', { text: String(text) }); },
            log(text) { call('log', { text: String(text) }); },
            vibrate(style) { call('vibrate', { style: style || 'light' }); },
            getInputText() { return host.getInputText(); },
            setInputText(text) { call('input.set', { text: String(text) }); },
            sendMessage() { call('message.send', {}); },
            editMessage(peerId, messageId, text) { call('message.edit', { peerId: String(peerId), messageId, text: String(text) }); },
            fetch(url, callback) { request('fetch', { url: String(url) }, callback); },
            addContextMenuItem(title, hookName) { call('menu.add', { title, hookName }); },
            chat: {
                addButton(spec) { call('chat.button', spec); },
                addLabel(spec) { call('chat.label', spec); },
                removeView(id) { call('chat.remove', { id }); }
            },
            settings: {
                addRow(spec) { call('settings.row', spec); },
                registerPage(spec) { call('settings.page', spec); }
            },
            ui: {
                hookScreen(spec) { call('screen.hook', spec); },
                actionSheet(title, message, options, callback) { request('ui.actionSheet', { title, message, options }, callback); }
            }
        };
        return {
            wg, emit,
            setTimeout: (fn, ms) => timer(fn, ms, false),
            setInterval: (fn, ms) => timer(fn, ms, true),
            clearTimeout: clear, clearInterval: clear,
            resolve(id, ...args) {
                if (stopped || !callbacks.has(id)) return;
                const callback = callbacks.get(id); callbacks.delete(id);
                try { callback(...args); } catch (error) { call('error', { message: String(error) }); }
            },
            stop() {
                if (stopped) return;
                if (plugin && typeof plugin.onUnload === 'function') {
                    try { plugin.onUnload(); } catch (error) { call('error', { message: String(error) }); }
                }
                for (const id of timers) clear(id);
                callbacks.clear(); events.clear(); stopped = true;
            }
        };
    }
    root.AyuWhiteGram = { create };
})(globalThis);
