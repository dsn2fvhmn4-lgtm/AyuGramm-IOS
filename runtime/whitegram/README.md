# WhiteGram JavaScript compatibility: work in progress

`bridge.js` implements a compatibility layer inferred from the user's WhiteGram
`.js` examples. It is not an official SDK and is not wired into the iOS app yet.
The app still cannot import or run WhiteGram scripts. A native host must isolate
plugins, provide the host calls, persist storage separately per plugin and account,
install/uninstall scripts, and connect lifecycle and chat events before shipping.

Implemented bridge calls are events, `BasePlugin`, registration, timers, storage,
chat controls, settings rows/pages, screen hooks, action sheets, notifications,
vibration, draft access, message operations and fetch. These are messages to the
host; their native behavior is not implemented by the bridge itself. Unsupported
host operations must report errors and must not silently claim success. Actual
availability, permissions, error behavior and SDK signatures need verification
against WhiteGram's documentation and source.

Run the repeatable synthetic test:

```
node runtime/tests/whitegram/test_bridge.js
```

Pass a path to the original Tamagotchi file to run the same integration scenario
against it. The test uses a fake host and Node's VM; it does not exercise UIKit,
Telegram messages, a real iOS JavaScript engine or security boundaries.
