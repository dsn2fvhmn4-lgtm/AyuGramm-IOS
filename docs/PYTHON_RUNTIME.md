# exteraGram plugin converter: embedded Python runtime (prototype)

This is the start of **option B**: run exteraGram `.plugin` files on iOS by
embedding CPython and reimplementing the exteraGram SDK in Python, with a
mapping table from Android Java hooks to native iOS events. It extends — does
not replace — the existing declarative plugin ABI and the reviewed native
adapters (Search+, Camera Flip, Chat Colors, Arcade Games, Unlim Accounts),
which keep running unchanged and take precedence by SHA-256 on import.

**Status: prototype. The Python runtime is implemented and tested on desktop
Python. The Swift/Objective-C host integration is present in source.
`Python.xcframework` is not embedded, so interpreter-backed execution remains
inactive in the IPA; existing native adapters keep handling supported plugins.**

## What runs today (verified on desktop CPython 3.12)

`runtime/tests` passes (`python -m unittest discover -s runtime/tests`): send
hooks modify and cancel outgoing text, Java method hooks on
`SendMessagesHelper.sendMessage` reach the same event, hooks compose and unload
cleanly, menu clicks / settings / bulletins / alert callbacks round-trip, and
unsupported Android calls raise `UnsupportedJavaCall` that is contained to the
failing callback instead of crashing the runtime.

## Architecture

```
.plugin (Python)
   │  import base_plugin, client_utils, ui.*, org.telegram.*, android.*
   ▼
runtime/python/            ← bundled into the app as ayu-python-runtime/python
   _ayu_host.py            the only entry point the native side calls
   base_plugin.py          BasePlugin, HookResult/Strategy, MenuItem*, settings
   client_utils.py         send_text/send_message (text), queues, controllers*
   android_utils.py        run_on_ui_thread, copy_to_clipboard, R, listeners
   hook_utils.py           find_class, (static) private-field reflection
   file_utils.py           sandbox directory + file helpers
   ui/{bulletin,alert,settings}.py   native toasts, dialogs, settings schema
   extera_utils/text_formatting.py   parse_text (entities parsed host-side)
   _ayu_java.py            import finder for Java packages + hook dispatcher
   _ayu_bridge.py          JSON transport + callback registry (+ desktop mock)
   │  JSON over one C function: native(request) -> response
   ▼
Swift / Objective-C host
   AyuPythonBridgeObjC.{h,m}   CPython C API, PyConfig, native() trampoline
   AyuPythonRuntime.swift      serial queue, operations, native-call router (TelegramCore)
   AyuPythonBootstrap.swift    paths, interpreter adapter, host handler (TelegramUI)
```

`runtime/hook_map.json` is the Java→iOS table: each Android method is `wired`,
`partial`, `planned` or `unmappable`, with the native event it maps to. The
compatibility report and the runtime both read it, so a plugin is never told a
hook works unless the table says the runtime implements it.

## Isolation and safety

- Every plugin callback runs inside `_ayu_java.active(plugin_id)` behind an
  exception boundary. One plugin's failure disables one feature, not the
  runtime or other plugins.
- There is no JVM. `import org.telegram.*` / `android.*` resolve to stub
  classes; a call with no iOS implementation raises `UnsupportedJavaCall`.
- `__requirements__` (pip packages) are not installed; such imports fail and
  are reported.
- Embedded Android DEX/JNI payloads (e.g. Unlim Accounts) cannot load; the
  report marks them unsupported, and their reviewed native adapter is used
  instead when one exists.
- Interpreter is isolated (`PyConfig_InitIsolatedConfig`), no bytecode writing,
  no signal handlers, UTF-8 mode on.

## Compatibility report

`tools/plugin_compat_report.py` grades a `.plugin` (or the static inventory)
against the runtime without executing it:

```
python tools/plugin_compat_report.py plugins/*.plugin \
  --inventory docs/ANDROID_PLUGIN_INVENTORY.json \
  --markdown docs/PYTHON_RUNTIME_COMPAT.md --json docs/PYTHON_RUNTIME_COMPAT.json
```

`--dry-run` additionally loads each plugin with the mock bridge (this executes
plugin code — only for trusted files). Current output is in
[PYTHON_RUNTIME_COMPAT.md](PYTHON_RUNTIME_COMPAT.md).

## Next steps (require macOS / Xcode; none verifiable on Windows)

1. Embed `Python.xcframework` from BeeWare Python-Apple-support
   **3.13-b15** (Python 3.13.15, iOS asset
   `Python-3.13-iOS-support.b15.tar.gz`, sha256
   `80175765a31babe43b0910395cf86ba4e8412adf1902b069d55b74d523ecc5d1`). b15 is
   chosen over the newer b17/b18 as it has been out since 4 Sep. Bundle
   `runtime/python` as `ayu-python-runtime/` and process `.so` modules into
   `Frameworks/*.framework` with `.fwork` markers (App Store rule; see the
   CPython iOS guide).
2. Add a Bazel target for `AyuPythonBridgeObjC` + the `Python` framework dep,
   put `AyuPython/` Swift on the TelegramUI graph, and call
   `AyuPythonBootstrap.shared.install(context:)` from
   `AuthorizedApplicationContext`.
3. Wire the outgoing seam: call `AyuPythonRuntime.shared.transformOutgoing(...)`
   in `enqueueMessages` next to the existing `plugins.outgoingText(text)`,
   guarded by `isAvailable` (inert until the framework is embedded).
4. Surface Python plugins in the existing **Settings → AyuGram → Plugins**
   manager (import stores the `.plugin` under the data dir's `sources/`, shows
   the compatibility verdict before enabling) and render menu items / settings
   schema / bulletins / alerts from the host handler.
5. Measure IPA size impact (support package ≈ 30 MB compressed) and confirm the
   runtime starts on device. Sideload only: App Store forbids downloaded
   executable code, so this stays an unsigned/sideload feature.
