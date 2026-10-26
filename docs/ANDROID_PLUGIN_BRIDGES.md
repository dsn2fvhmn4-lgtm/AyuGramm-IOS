# Supplied Android plugin examples and native bridge status

Source inventory: [exact versions, SHA-256 and dependencies](ANDROID_PLUGIN_INVENTORY.json).
The inventory reads Python AST and string metadata only. It does not execute any
plugin code or load embedded native libraries. Original source files remain unchanged.

| Supplied file | Required integration | Current source status |
| --- | --- | --- |
| camera_flip.plugin 0.2.0 | Round-camera touch events, existing flip action, settings | Native adapter added |
| chat_colors.plugin 1.0 | Chat-list row background, peer color storage, context/profile menus, color picker and brightness | Native adapter added |
| game_arcade.plugin 1.1 | Native web view, 3 external game URLs, injected scripts, cookies/cache lifecycle, menus and intercepted dot commands | Native adapter added |
| story_scheduler.plugin 1.1 | Durable media queue, story uploader/privacy/peer models, schedule picker, retries and wakeup lifecycle | No adapter implemented |
| unlim_accounts.plugin 1.0 | Android 12.10.6 account internals plus embedded DEX/JNI runtime | Native adapter added (client add-account limit 999) |

Story Scheduler still needs more than text-replacement rules. A Python interpreter alone
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

## Import behavior

Plugins are imported like in exteraGram: the confirmation shows the plugin's name,
version, author and description, and the plugin is enabled after **Install**.
Adapter notes and permission lists are not shown; the version and author are shown
without the port's `-ios.N` and `(original)` markers. Unsupported files show a short
"not supported yet" message and leave installed plugins unchanged. The import limit is
4 MB so Unlim Accounts (2.6 MB, recognised by SHA-256 only) can be imported.

## Arcade Games native adapter

- Exact source SHA-256: `421911448e6fe62b3292b43b8593ebb24056b238278bab002576381d541238bc`.
  Authors retained: @Art_727 & @lerowplug; actions declare plugin API 5.
- Games: 2048 (play2048.co), Flappy Bird (flappybird.io/play) and Chrome Dino
  (chromedino.com/embed) in a full-screen portrait WKWebView with the original
  background color. The plugin's ad-blocking script is injected at document end,
  after every load and every 600 ms, as on Android. Popups and main-frame navigation
  off the three game sites are refused.
- Launch: the plugin page (Games section), chat message menu -> Plugins, or the
  `.2048`, `.flappy`, `.dino` commands (case-insensitive, trimmed). A command opens
  the game and is not sent; the input is cleared. Scheduled sends are not intercepted.
- Plugin settings, as in the original: close button, exit confirmation and keeping
  the screen awake (through the app's idle-timer extension), all on by default, plus
  "Reset games data", which removes the three sites' website data. The Android drawer
  menu has no iOS equivalent; the plugin page and chat Plugins menu replace it.

## Unlim Accounts native adapter

- Exact source SHA-256: `6c5e2f697da4d87b0409841d96dd9bf69f224073c44b555c6fd9de782c70d40f`.
  Author retained: @rezolvePlugins; API 5.
- iOS limits accounts only in the client (3, or 4 with Premium). While the plugin is
  enabled in the current account, the Add Account checks in Settings, the logout and
  delete-account options and Settings search allow up to 999 accounts. The embedded
  Android DEX/JNI runtime is never extracted or loaded.
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

## Chat Colors native adapter

- Exact source SHA-256: `a7217c0cc672615e3558b8f3391b522f7e031bc0900a84315b4eb4f53ece8de5`.
- Authors retained: @lerowc and @lerowplug. Import the unchanged supplied file or
  [chat_colors_ios.plugin](../plugins/chat_colors_ios.plugin). New actions require
  API 4, so earlier clients reject them.
- Enable the installed plugin. Long-press a chat in the list, or open its profile
  menu, then choose **Chat color**. The current-chat plugin action opens the same picker.
- Native picker: all nine original presets, custom #RGB/#RRGGBB, external color
  website and removal. Validation happens before saving. No Android view or drawing
  bytecode runs.
- Plugin details -> Chat colors: feature switch, original 10%-100% brightness
  steps (default 30%), colored-chat list with account-local titles, reset-all
  confirmation, website and author channel. Personal preferences stay in the
  account; exported plugin manifests contain functionality, not those preferences.
- Colors use complete encoded iOS peer IDs, not Android dialog IDs or usernames.
  Different peer namespaces and accounts keep independent settings. Existing
  Android personal settings are not imported.
- Row nodes observe the active provider. Color/brightness changes, feature/plugin
  disable and uninstall update visible rows without a list reload. Reused nodes
  clear prior tint; delayed updates from a different account are ignored. No
  disk reads or title lookups run in the rendering callback.
- Tint overlays the normal/pinned base under text and native highlight layers.
  Selected rows retain native selection. Message-search rows, sponsored entries,
  community cards, placeholders and archive group references are excluded.
- Up to 1024 colored chats per provider/account. The first enabled Chat Colors
  provider supplies rendering; personal settings survive replacement and re-enable.
- Actual Swift host checks cover HEX normalization/rejection, exact Android alpha
  rounding, namespaced key separation, persistence, failed updates, account
  isolation, feature/plugin disable, replacement, removal and count/brightness
  validation. The UIKit picker is included in the cheap actual SDK check.
- Regression checklist: light/dark, pinned/selected/highlight/reveal, recycled cells,
  profile/list/message entry points, invalid HEX, save failure, removal while the
  picker is open, reset, multiple accounts and all brightness steps. No build was
  started by this source task.
