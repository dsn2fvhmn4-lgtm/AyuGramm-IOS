# Supplied Android plugin examples and native bridge status

Source inventory: [exact versions, SHA-256 and dependencies](ANDROID_PLUGIN_INVENTORY.json).
The inventory reads Python AST and string metadata only. It does not execute any
plugin code or load embedded native libraries. Original source files remain unchanged.

| Supplied file | Required integration | Current source status |
| --- | --- | --- |
| camera_flip.plugin 0.2.0 | Round-camera touch events, existing flip action, settings | Native adapter added; macOS compilation and iPhone verification pending |
| chat_colors.plugin 1.0 | Chat-list row background, peer color storage, context/profile menus, color picker and brightness | No adapter implemented |
| game_arcade.plugin 1.1 | Native web view, 3 external game URLs, injected scripts, cookies/cache lifecycle, menus and intercepted dot commands | No adapter implemented |
| story_scheduler.plugin 1.1 | Durable media queue, story uploader/privacy/peer models, schedule picker, retries and wakeup lifecycle | No adapter implemented |
| unlim_accounts.plugin 1.0 | Android 12.10.6 account internals plus embedded DEX/JNI runtime | No adapter implemented; file exceeds current 512 KB import limit |

These examples need more than text-replacement rules. A Python interpreter alone
would not supply the referenced Java classes, Android views, DEX/JNI loader or
Telegram Android implementation. Equivalent iOS implementations must be connected
to native events. The inspected Unlim Accounts source explicitly requires Android
Telegram 12.10.6; changing an iOS account-limit constant would not reproduce its
runtime implementation. Raising the input size limit does not add that support.

Arcade Games loads remote sites (play2048.co, flappybird.io, chromedino.com), rather
than bundling three offline engines. Its source also injects browser scripts and
handles game-window teardown. Merely adding three links would be partial parity.

Story Scheduler's Android timer cannot establish iOS execution while the app is
suspended or terminated. A port needs a separately specified background behavior
and a tested persistence/recovery path. See Apple's [Background Tasks documentation](https://developer.apple.com/documentation/backgroundtasks).

## Camera Flip native adapter

- Exact supplied source hash: `61136472b21e9ac23fc32883e137173ef1a85314d2cc6c63719be003555f1e98`.
- Original author: @its240hz. Native actions declare plugin API 3 so older clients reject them.
- Import the unchanged original file or [camera_flip_ios.plugin](../plugins/camera_flip_ios.plugin).
- Open the installed plugin's settings: swipe either direction, up only, down only,
  or double tap; haptic feedback on/off. Defaults match the original (either swipe,
  haptic enabled). Settings remain per-account and persist across restart,
  disable/re-enable and replacement. The exported plugin manifest carries its
  functionality; personal gesture preferences stay in the account's settings.
- The modern iOS round-video screen observes single-finger touches passively.
  Controls and touches outside the circular camera preview are excluded. It does
  not prevent pinch or cancel touches delivered to native recording controls.
- Thresholds: vertical motion >60 points and >1.5 times horizontal motion; tap
  displacement <12 points, duration <250 ms, two releases <350 ms apart; cooldown
  800 ms. Multitouch/cancellation clears the in-progress sequence.
- The bridge calls the existing camera component's flip method, preserving its
  torch, brightness and readiness/transition behavior. It does not invoke Java
  reflection, emulate button names or introduce a second camera session.
- If several native camera providers are enabled, the first installed provider
  supplies the active configuration.
- The hook reads enabled settings on every event. Disabling/removing the plugin
  immediately prevents later events from invoking the feature.
- Scope is the current VideoMessageCameraScreen. Other capture screens and old
  legacy capture controllers have no new gesture hook. Original UI widgets are
  represented by native iOS settings; platform-exact appearance is not promised.

## Verification

Python checks cover unchanged-source hash dispatch and static-inventory behavior,
including large embedded source without execution. Actual Swift host tests cover
adapter equality, plugin API version, settings validation/persistence, lifecycle,
thresholds, direction, cooldown, duplicate moves, double tap, multitouch, long
press and invalid coordinates. Codemagic's SDK preflight includes the actual
UIKit recognizer and plugin settings against the actual model sources. These
Swift/SDK checks have been added but have not run on this Windows machine.

Before a release: build the native target; record and inspect simulator settings
frames; test all four modes on an iPhone while recording/locked, with pinch,
controls, front/back camera, torch/brightness, result preview, cancellation,
disable/remove, account switching and both camera backends. No new IPA or device
success is claimed by this source revision.

For future files, run:

```powershell
python tools/analyze_plugin.py input.plugin --output report.json
```

The report lists dependencies and source identity. It does not convert unknown
plugins or mark unimplemented bridges as available.
