# WhiteGram JavaScript compatibility

The app can import `.js` files in the plugin manager. Enabled scripts run in
separate WebKit environments; their storage is isolated by account and plugin.
The initial compatibility layer is inferred from the supplied WhiteGram plugin
examples, not an official SDK implementation.

The iOS host provides plugin registration, lifecycle, timers, chat open events,
buttons and labels in the chat, local storage, settings rows and sliders, action
sheets, toast messages and basic vibration. The host removes overlays on chat
exit and stops the plugin on disable. Plugin settings become available after the
script has loaded; to remove a script, swipe its row in the plugin list.

The host also implements `wg.fetch` for HTTP and HTTPS with a 15-second timeout.
Modifying/sending messages, input access and context menus are not yet connected.
Unsupported calls are logged. Plugins using those methods do not fully work.
The separate screen hook API currently relies on the `onChatOpen` event supported
by the supplied Tamagotchi plugin. Full API behavior needs verification against
WhiteGram's SDK and actual plugin versions.

Run the repeatable synthetic test:

```
node runtime/tests/whitegram/test_bridge.js
```

Pass a path to the original Tamagotchi file to run the same scenario against it.
The test uses a fake host and Node's VM; it does not exercise WebKit, UIKit,
Telegram messages, a real iOS JavaScript engine or security boundaries. Build
and test the installed app on an iOS device before treating the integration as
verified.
