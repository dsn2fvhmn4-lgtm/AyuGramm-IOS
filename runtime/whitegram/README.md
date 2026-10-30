# WhiteGram JavaScript compatibility

The app installs WhiteGram `.js` plugins from the plugin manager ("+") or by tapping a `.js`
file in a chat; installation asks for confirmation and shows the plugin's name, author and
description. Enabled scripts run in separate JavaScriptCore contexts on the main thread; their
storage is isolated by account and plugin. The API is inferred from real WhiteGram plugins, not
from an official SDK: no public JavaScript SDK documentation was found.

| API | iOS behaviour |
| --- | --- |
| `wg.on`, `wg.registerPlugin`, `wg.BasePlugin` | Events and `onLoad`/`onUnload` lifecycle |
| `onChatOpen(peerId)`, `onActivate`, `onAppForeground`, `onAppBackground` | Emitted by the host |
| `wg.ui.hookScreen({screen: "chat", event: "open"})` | Hook is emitted on chat open |
| `onMessageReceive({peerId, messageId, text, out})` | Own text messages after the server confirms them, in the open chat (any chat, not only Saved Messages) |
| `wg.editMessage(peerId, messageId, text)` | Edits a cloud message; also works after leaving the chat |
| `wg.getInputText`, `wg.setInputText`, `wg.sendMessage` | Input field of the open chat |
| `wg.chat.addButton`, `addLabel`, `removeView` | Overlays on the chat; removed on chat exit |
| `wg.settings.addRow`, `registerPage` (rows, sliders) | Plugin settings screen (tap the plugin in the list) |
| `wg.addContextMenuItem` | Shown in the "Действия" section of the plugin settings |
| `wg.ui.actionSheet`, `wg.toast`, `wg.vibrate(style)`, `wg.log` | Native UI |
| `wg.fetch(url, cb)` | HTTP(S) GET, 15 s timeout, 1 MiB text limit |
| `setTimeout`/`setInterval`, `console.log` | Native timers, cleared on disable |

Not available: secret chats, incoming messages from other people, and editing other people's
messages (the server rejects it). A plugin with an infinite loop blocks the app.

Tests (fake host on Node's VM; they do not exercise JavaScriptCore, UIKit or Telegram):

```
node runtime/tests/whitegram/test_bridge.js
node runtime/tests/whitegram/test_plugins.js "/path/to/folder/with/plugins"
```

`test_plugins.js` loads every `.js` in the folder, drives chat open, button taps, settings rows
and text commands, and fails on any exception or on an operation the iOS host does not implement.
