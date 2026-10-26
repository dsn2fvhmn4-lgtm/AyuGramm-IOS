# exteraGram plugin converter: embedded Python runtime (prototype)

This is the start of **option B**: run exteraGram `.plugin` files on iOS by
embedding CPython and reimplementing the exteraGram SDK in Python, with a
mapping table from Android Java hooks to native iOS events. It extends — does
not replace — the existing declarative plugin ABI and the reviewed native
adapters (Search+, Camera Flip, Chat Colors, Arcade Games, Unlim Accounts),
which keep running unchanged and take precedence by SHA-256 on import.

**The wider Python SDK is a desktop-tested prototype. Source builds now embed
CPython for the [on-device AST converter](AST_CONVERTER.md), which translates
supported hooks to persisted native programs. The app does not load arbitrary
Python plugins. Existing native adapters keep priority. Release 4 remains the
previous artifact without this new interpreter/converter block.**

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

## Native converter integration

The build downloads and verifies BeeWare Python 3.13-b15, links its framework,
and packages the standard library with framework-wrapped binary modules.
The native bridge now acquires the GIL for each queue call and releases it after
initialization, so serial GCD queue thread changes do not reuse a foreign Python
thread state. CPython startup/configuration failures are returned to the importer.

The converter uses only the `convert` host operation. It reads the complete AST,
emits a native API 6 manifest and leaves activation/persistence to the existing
plugin manager. No downloaded source is executed. Native program execution does
not need Python on the message-send path. The other host APIs and Java-hook shims
remain a separate prototype rather than general Android compatibility.

See [AST converter details](AST_CONVERTER.md) for supported statements, bounds,
packaging checks and signing requirements.
