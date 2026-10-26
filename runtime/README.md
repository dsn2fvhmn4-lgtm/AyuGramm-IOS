# AyuGram iOS Python plugin runtime

Embeds CPython to run exteraGram `.plugin` files on iOS. See
[../docs/PYTHON_RUNTIME.md](../docs/PYTHON_RUNTIME.md) for the full design and
status (prototype: Python side tested, native host unbuilt).

## Layout

- `python/` — the Python runtime, bundled into the app as `ayu-python-runtime/python`.
- `hook_map.json` — Android Java method → iOS native event mapping table.
- `tests/` — desktop tests against the mock native bridge.

## Test

```
python -m unittest discover -s runtime/tests
```

(uses only the standard library; runs on CPython 3.9+.)

## Native entry point

The iOS host calls `_ayu_host.call(request_json) -> response_json` and installs
one C function via `_ayu_host.install_native(fn)`. Requests are
`{"op": ..., "args": {...}}`. Operations: `configure`, `load`, `unload`,
`status`, `appEvent`, `sendMessage`, `menuItems`, `menuClick`,
`settingsSchema`, `settingChanged`, `callback`.
