# Code plugins (JavaScript)

Code plugins are JavaScript files that run as code inside the app and change how it behaves.
They sit beside the existing declarative `.plugin` / `.iosplug` (JSON) plugins, which keep
working unchanged.

## Isolation

iOS does not let an app start processes or load downloaded native code, so each plugin gets
its own **JavaScriptCore virtual machine on its own serial queue**:

- an exception stays inside the plugin and is reported to the plugin console;
- a hook that does not answer within **250 ms** (2 s with *Developer → Relaxed plugin limits*)
  disables the plugin, removes all of its hooks and shows a notice, so a stuck plugin can never
  freeze the app again;
- plugins have **no network, account, file or message-sending API**. They only see the text
  passed to their hooks and their own 64 KB key-value storage.

## Install

- Plugins screen → **+** → pick a `.js` or `.ayujs` file, or
- tap a `.ayujs` / `.ayu.js` file in a chat, or
- Plugins screen → **bag icon** (Catalog) → pick a plugin from
  [murk-sus/AyuGramm-Plugins](https://github.com/murk-sus/AyuGramm-Plugins). The download must
  match the SHA-256 and `@id` in the catalog's `index.json`; a newer catalog version shows
  **Update**. To publish a plugin, open a pull request there.

The confirmation shows the plugin's header and what it may do. Toggle, restart (tap) and delete
(swipe) in the *Code plugins · JavaScript* section.

## Header

```js
// ==AyuPlugin==
// @id my-plugin            (a–z, 0–9, - and _; defaults to the file name)
// @name My plugin
// @author Me
// @version 1.0
// @description What it does.
// ==/AyuPlugin==
```

## API

| Call | Effect |
| --- | --- |
| `ayu.hooks.before(point, fn)` | runs `fn(text, ctx)` before the native handler |
| `ayu.hooks.replace(point, fn)` | **replaces** the native handler; only one plugin may replace a point (later ones become `after`) |
| `ayu.hooks.after(point, fn)` | runs after the native handler |
| `ayu.features.disable(name)` / `enable(name)` | switches a native feature off/on while the plugin runs |
| `ayu.on(event, fn)` | `load`, `unload`, `chatOpen` (`{ peerId }`) |
| `ayu.storage.get(key)` / `set(key, value)` | per-plugin strings, 64 KB total |
| `ayu.toast(text)`, `ayu.log/warn/error(...)`, `console.*`, `print` | messages and console output |
| `setTimeout`, `setInterval` (≥ 100 ms), `clearTimeout` | timers on the plugin queue |

A text hook returns the new text, or anything that is not a string to leave it unchanged.
`ctx` is `{ peerId, isSecret }`.

### Hook points

| Point | Native handler |
| --- | --- |
| `message.outgoing.text` (`ayu.hooks.points.outgoingText`) | JSON plugins' outgoing replacements; applies to plain cloud-chat text without entities or media, never secret chats |

### Features

`fastShare`, `messageShot`, `reactionPicker`, `readSummary`, `editedInfo`, `messageDetails`,
`stories`, `similarChannels`, `premiumStatuses`, `unreadCounters`, `greetingSticker`,
`openLinkWarning`, `doubleTapToEdit`, `formattingToolbar`, `keyboardHideOnScroll`.

Each maps onto the matching AyuGram interface setting, so every place that honours the setting
honours the plugin. Overrides are never written to the user's settings and vanish when the
plugin stops.

### WhiteGram compatibility

`wg.registerPlugin`, `wg.BasePlugin`, `wg.on`, `wg.log`, `wg.toast`, `wg.getStorage` and
`wg.setStorage` map onto the API above. UI-building calls of the old WhiteGram runtime are not
provided.

## Debugging

*Settings → AyuGram → Developer*: **Plugin console** shows `print`, errors and hook activity;
**Relaxed plugin limits** lengthens the hook timeout and turns script errors into toasts;
**Verbose logging** writes them to a shareable log file.

Example: [`examples/smart-quotes.ayu.js`](examples/smart-quotes.ayu.js).
Prelude tests: `node runtime/tests/ayuscript/test_prelude.js /path/to/prepared/telegram`.
