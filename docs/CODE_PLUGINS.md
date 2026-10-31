# Code plugins (JavaScript, Python, Rust)

Code plugins are JavaScript, Python or Rust (WebAssembly) files that run as code inside the app
and change how it behaves.
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

Python plugins run in [PocketPy](https://github.com/pocketpy/pocketpy) 2.1.8, built without its
`os`/`io` layer (no files, sockets, `system()` or `dlopen`) and with a watchdog that stops a
call running past its time limit. Rust plugins are WebAssembly modules run by WAMR's interpreter
(no JIT); their only import is `ayu.host`. Both engines live in `submodules/AyuPluginEngines` of
the port (see `patches/ayugram-big-update.patch`).

## Install

- Plugins screen → **+** → pick a `.js`, `.ayujs`, `.py`, `.ayupy` or `.wasm` file, or
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

### Injecting plugins (inject API)

These calls change the app itself, so they work only for **trusted** plugins (see *Safe zone*):

| Call | Effect |
| --- | --- |
| `ayu.player.state()` | `{ title, artist, duration, position, playing }` of the music player |
| `ayu.player.control(action)`, `play()`, `pause()`, `next()`, `previous()` | `play`, `pause`, `toggle`, `next`, `previous` |
| `ayu.on('trackChange', fn)` | `{ title, artist, duration }` when a new track starts |
| `ayu.hooks.before('lyrics.text', fn)` | song lyrics before they are shown, one line per `\n`; return the same number of lines (an empty line drops it, timings stay) |

A plugin declares that it injects with `// @inject true` (`# @inject true` in Python,
`"inject": true` in a Rust manifest).

### Plugin settings

`ayu.settings.declare([{ key, type: 'toggle' | 'text', title, subtitle, default }])` makes the app
draw the plugin's own settings (tap the plugin in the list; lyrics plugins also appear under
*Lyrics sources*). `ayu.settings.get(key)` reads a value (`"1"`/`"0"` for switches); the
`settingsChange` event reports changes.

### Interface API

Every call is declarative: the plugin describes, AyuGram draws, and everything a plugin created
disappears when it stops. Each group needs a permission in the header, e.g.
`// @permissions ui, menu, overlay` (`# @permissions …` in Python, `"permissions": ["ui"]` in a
Rust manifest). The install confirmation lists them; a call without its permission fails with a
console error.

| Call | Permission | Effect |
| --- | --- | --- |
| `ayu.ui.alert({ title, message, buttons: [{ id, title, style }] }, fn)` | `ui` | alert; `fn(buttonId)` |
| `ayu.ui.sheet({ title, message, items: [{ id, title }] }, fn)` | `ui` | action sheet; `fn(itemId or null)` |
| `ayu.ui.menu.add({ id, title, icon })` / `remove(id)` | `menu` | item in the message menu (5 per plugin, SF Symbol `icon`); taps send `menuAction` `{ itemId, messageId, peerId, text }` |
| `ayu.ui.profile.addBlock({ peerId?, block: { id, title, text } })` / `removeBlock(id)` | `profile` | text block in user profiles (all, or one `peerId`) |
| `ayu.ui.profile.addButton({ peerId?, button: { id, title } })` / `removeButton(id)` | `profile` | button in profiles; taps send `profileButton` `{ buttonId, peerId }` |
| `ayu.ui.overlay.create({ id, effect, amount, speed, color })` / `update(id, …)` / `remove(id)` | `overlay` | particles over the whole app: `snow`, `leaves`, `rain`, `stars`, `confetti`; `amount`/`speed` 0.1–3; never takes touches, paused by Reduce Motion |
| `ayu.ui.overlay.addText({ id, text, anchor, size, color })` | `overlay` | text pinned to `topLeft`, `topRight`, `bottomLeft`, `bottomRight` or `center` |
| `ayu.ui.font.set({ element, size })` / `reset(element)` | `fonts` | `messages` or `lists` text size in points (12–30), applied when the appearance is rebuilt |
| `ayu.ui.badge.add({ peerId, badge: { text } })` / `remove({ peerId })` | `badges` | badge beside a chat's name in the chat list |
| `ayu.registry.developers.isVerified(peerId)` / `info(peerId)` | — | AyuGram for iOS team label (Telegram user id) |
| `ayu.ui.gifts.catalog.list(fn)` → Promise | — | Telegram's gift catalog, read-only: `[{ giftId, title, stars, fileId, limited, remains, total, soldOut }]` (Python: `ayu.ui.gifts.catalog.list(fn)`) |
| `ayu.clipboard.write(text)` | `clipboard` | copy text |
| `ayu.device.info()` | `device` | `{ battery, charging, orientation, lowPowerMode, reduceMotion, locale }` |
| `ayu.haptics.play(style)` | `haptics` | `light`, `medium`, `heavy`, `soft`, `rigid`, `selection`, `success`, `warning`, `error` (off with “No vibration”) |

`peerId` is the value plugins receive in events and hook contexts. Python has the same names
(`ayu.ui.menu.add({...})`, `ayu.call('device.info')`); Rust has `ayugram_plugin::call(op, json)`
and helpers in `ayugram_plugin::ui`.

### Events

`load`, `unload`, `chatOpen`, `chatClose`, `profileOpen`, `profileClose`, `screenChange`,
`appForeground`, `appBackground`, `accountChange` (`{ accountId }`), `settingsChange`, `menuAction`,
`profileButton`, `uiResult` and, for injecting plugins, `trackChange`.

### Setting types

`ayu.settings.declare` accepts `toggle`, `text`, `slider` (`min`, `max`, `step`), `color`
(`#RRGGBB`), `select` (`options: [{ value, title }]`) and `preview` (read-only text).

## Safe zone

- Ordinary plugins (outgoing text, switching features off, storage, toasts, settings) install
  from anywhere.
- Injecting plugins install only when signed by AyuGram (Ed25519; the catalog's
  `signatures.json`, shown as **✓ official**).
- An unsigned injecting plugin is refused unless *Developer → Injecting plugins from unofficial
  sources* is on; then a disclaimer says the responsibility is entirely the user's.
- The inject API is also checked while the plugin runs: an untrusted plugin calling it gets an
  error in the console.

## Python plugins

One file with the same header in `#` comments; the `ayu` object is already defined and accepts
decorators:

```python
# ==AyuPlugin==
# @id shout
# @name Shout
# @author Me
# @version 1.0
# ==/AyuPlugin==

@ayu.hooks.before(ayu.hooks.points.outgoing_text)
def shout(text, ctx):
    return text + '!'
```

PocketPy is a Python 3 subset: no file imports, and `str.lower()`/`upper()` only fold Latin
letters. Example: [`examples/python/lyrics-cleaner.ayu.py`](examples/python/lyrics-cleaner.ayu.py).

## Rust plugins

Use the dependency-free SDK in [`sdk/rust`](../sdk/rust) and build a `cdylib`:

```sh
cd docs/examples/rust/emoji-shortcuts
cargo build --release --target wasm32-unknown-unknown
# target/wasm32-unknown-unknown/release/emoji_shortcuts_rs.wasm is the plugin
```

```rust
use ayugram_plugin::{hooks, manifest};

manifest!(br#"{"id":"shout-rs","name":"Shout","author":"Me","version":"1.0"}"#);

#[no_mangle]
pub extern "C" fn ayu_init() {
    hooks::before(hooks::OUTGOING_TEXT, |text, _ctx| Some(format!("{}!", text)));
}
```

The manifest is the `ayu.manifest` custom section the app reads before running anything. The
module exports `ayu_alloc`, `ayu_free` and `ayu_dispatch` (from the SDK) and imports only
`ayu.host`; every message is JSON. Example:
[`examples/rust/emoji-shortcuts`](examples/rust/emoji-shortcuts).

## Debugging

*Settings → AyuGram → Developer*: **Plugin console** shows `print`, errors and hook activity;
**Relaxed plugin limits** lengthens the hook timeout and turns script errors into toasts;
**Verbose logging** writes them to a shareable log file.

Example: [`examples/smart-quotes.ayu.js`](examples/smart-quotes.ayu.js).
Prelude tests: `node runtime/tests/ayuscript/test_prelude.js /path/to/prepared/telegram`.
