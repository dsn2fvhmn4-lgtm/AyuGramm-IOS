# Native .plugin support - development source after Release 3

This introduces a versioned declarative plugin ABI, a per-account installation
registry, a native action runner and a reviewed Search+ adapter. It is not a
Python interpreter, a Java compatibility runtime or a universal exteraGram converter.
Release 3's already uploaded IPA is unchanged.

## Installation and use

1. Tap a downloaded `.plugin` in an ordinary cloud chat, open one from Files, or
   use **Settings -> AyuGram Preferences -> Plugins -> Import .plugin**.
2. Review its author, version, capabilities and conversion limitations, then choose
   **Import and enable**. Preparation and activation commit together after success.
3. Tap an installed plugin to open its details page with name, version, author,
   description and an enable switch.
4. Open an ordinary cloud message's menu -> **AyuGram -> Plugins**, then choose
   an action. Manual actions take explicitly entered input. Automatic outgoing
   rules instead process eligible outgoing text in the native enqueue path. The
   manager also supports disable, removal and .plugin export.

Plugin rows show a white puzzle piece on a blue circle. Downloaded `.plugin`
documents without thumbnails use a puzzle icon in the chat's native file control;
download progress/cancel controls retain their normal states. This affects this
client's rendering, not how other Telegram clients show the file.

All plugins use the same white puzzle piece on a blue circle, including Search+.
Individual icon metadata from older files is ignored. API versions 1, 2 and 3 are built into
this app; no separate SDK installation is needed. Authors can use
[plugin.schema.json](../plugins/plugin.schema.json) and the ready-to-import examples
in [plugins](../plugins).

## Activation

Enabling a plugin starts background compatibility checks and prepares its typed
native action manifest. A progress indicator remains visible while that work runs.
Only a successful result is committed as enabled. Invalid input, a changed/removed
plugin or a persistence failure leaves it disabled. Closing a details page cancels
an uncommitted manual re-enable; the fresh import-and-enable operation temporarily
blocks modal dismissal until commit or failure. This checks the local format and action
handlers, not end-to-end Telegram requests or Android method-hook compatibility.
The reviewed Search+ conversion is built into the app; the desktop converter is
optional. Literal outgoing-hook templates now convert locally as described in
[automatic conversion](PLUGIN_CONVERSION.md). Camera Flip 0.2.0 also has a reviewed native adapter. Other Android plugins require a dedicated adapter.

## Search+ conversion

The exact supplied **Search+ 2.6.1** file is recognized by SHA-256:
`802dd326787e3640f55f20ac5462539c03202184e540578a4531c693c2c3458a`.
On import it becomes the native manifest in [search_plus_ios.plugin](../plugins/search_plus_ios.plugin).
The original author remains credited. Original Android/Python code is never run.
Changed files and other versions require their own reviewed adapter.

The iOS action sends up to six normal Telegram searches for phrases separated by
`|` in the current chat/topic. Up to 40 results per phrase are deduplicated and
sorted newest first. Rows show message identifiers and dates; tap one to open
the native message, where formatting and spoilers retain native behavior.
Requests are cancelled on close or a replacement search, with a 15-second timeout.
There is no automatic pagination or claim to search the entire history.

**Not converted:** Android method hooks, injection into global search, user lookup
by phone/ID and Search+'s custom date/type/author filters. These limitations appear
before installation; the adapter does not advertise full original feature parity.

Optional Windows conversion without changing the original:

```powershell
python tools/convert_plugin.py search_plus.plugin search_plus_ios.plugin
```

## ABI versions 1, 2 and 3

Files use the `.plugin` extension and UTF-8 JSON, with format
`ayugram-ios-plugin`, apiVersion `1`, `2` or `3`, metadata and declared actions. See
[text_replace_example.plugin](../plugins/text_replace_example.plugin).

- `search`: a single current-chat search.
- `searchTerms`: merge current-chat searches separated by `|`.
- `replaceText`: literal text replacement, followed by result review and explicit
  append-to-draft confirmation. No automatic send; the native recording-discard,
  editing and send-permission checks remain in effect.
- `outgoingReplace`: automatic nonempty, nonexpanding literal replacement in plain
  outgoing cloud text. Optional `prefix` or a literal `condition` restricts
  matching. `replacementCount` optionally limits replacements to 0...4096.
  New condition/count fields require API version 2; older clients reject them. See the full
  [automatic conversion and hook scope](PLUGIN_CONVERSION.md).

- `cameraFlip` (API 3): native round-video camera gestures, configured on the plugin page.
  See the [reviewed adapter and five-file inventory](ANDROID_PLUGIN_BRIDGES.md).

Permissions derive from action kinds: `search.messages`, `draft.prepare` or
`messages.outgoing.modify` or `camera.switch`.
Unknown operation kinds and ABI versions are rejected. Limits: 512 KB per file,
12 plugins per account, 8 actions per plugin, 6 queries, 128 characters per query,
8192 input/output UTF-8 bytes and 4096 output UTF-16 units for draft text. IDs are
bounded path-free identifiers. Import/update validation happens before committing
account settings. Plugins cannot declare arbitrary native methods or file access.

## Verification status

The actual Foundation/CryptoKit models are added to the existing host regression
harness, covering import/export, limits, migration, state persistence, disabled
actions, failed transactions, query splitting and literal text transformation.
Preflight checks the actual plugin manager against the iOS SDK and a model-only
module compiled from actual source; this is not a full TelegramCore build.

Windows source/patch and converter checks are separate from macOS SDK compilation,
full native integration and iPhone runtime checks. No native build, simulator
recording or device test was performed for this block on the Windows host.
Before shipping, check import/cancel/replace/export, account switching, all actions,
network timeout/cancel, topic navigation, draft/recording interactions, file-icon
reuse, light/dark layouts, large fonts and VoiceOver. Inspect recorded simulator
frames before claiming visual verification.
