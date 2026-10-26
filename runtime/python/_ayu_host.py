"""Plugin host: the only module the native side calls.

Native code calls `call(request_json) -> response_json`. Requests are
`{"op": ..., "args": {...}}`; responses are `{"ok": true, "result": ...}` or
`{"ok": false, "error": ...}`. Every plugin callback runs inside
`_ayu_java.active(plugin_id)` and behind an exception boundary, so a failing
plugin never takes the runtime or another plugin down.
"""
import ast
import json
import os
import sys
import threading
import traceback
import types

import _ayu_bridge
import _ayu_java

METADATA_KEYS = ("__id__", "__name__", "__description__", "__author__", "__version__", "__icon__",
                 "__app_version__", "__sdk_version__", "__min_version__", "__requirements__")

_lock = threading.RLock()
plugins = {}
_settings_dir = None


class LoadedPlugin:
    def __init__(self, plugin_id, metadata, module, instance, source_sha256):
        self.id = plugin_id
        self.metadata = metadata
        self.module = module
        self.instance = instance
        self.source_sha256 = source_sha256
        self.load_error = None


def read_metadata(source):
    """Top-level literal assignments only; nothing is executed."""
    tree = ast.parse(source)
    metadata = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id in METADATA_KEYS:
            try:
                metadata[node.targets[0].id.strip("_")] = ast.literal_eval(node.value)
            except ValueError:
                pass
    return metadata


def _guard(plugin_id, fn, *args):
    with _ayu_java.active(plugin_id):
        try:
            return fn(*args)
        except Exception as error:
            _ayu_java.record_error(plugin_id, error)
            return None


# ---------------------------------------------------------------- lifecycle

def configure(args):
    global _settings_dir
    root = args["dataDir"]
    _settings_dir = os.path.join(root, "settings")
    os.makedirs(_settings_dir, exist_ok=True)
    import file_utils
    file_utils._configure(os.path.join(root, "files"))
    return {"python": sys.version.split()[0], "hookMapVersion": _ayu_java.HOOK_MAP.get("version")}


def load(args):
    path = args["path"]
    with open(path, encoding="utf-8-sig") as handle:
        source = handle.read()
    metadata = read_metadata(source)
    plugin_id = str(metadata.get("id") or "")
    if not plugin_id:
        raise ValueError("plugin has no __id__")
    unload({"id": plugin_id})
    if metadata.get("requirements"):
        # pip packages are not installed on iOS; imports of them fail below and are reported.
        _ayu_java.note("unsupportedSdk", "__requirements__:" + ",".join(map(str, metadata["requirements"])), plugin_id)
    module = types.ModuleType("ayu_plugin_" + plugin_id.replace("-", "_"))
    module.__file__ = path
    module.__dict__["__builtins__"] = __builtins__
    with _ayu_java.active(plugin_id):
        code = compile(source, path, "exec")
        exec(code, module.__dict__)
    import base_plugin
    classes = [v for v in module.__dict__.values()
               if isinstance(v, type) and issubclass(v, base_plugin.BasePlugin) and v is not base_plugin.BasePlugin and v.__module__ == module.__name__]
    if not classes:
        raise ValueError("plugin defines no BasePlugin subclass")
    with _ayu_java.active(plugin_id):
        instance = classes[-1]()
        instance._ayu_attach(plugin_id, str(metadata.get("name") or plugin_id), _settings_dir or os.path.dirname(path))
    loaded = LoadedPlugin(plugin_id, metadata, module, instance, args.get("sha256"))
    with _lock:
        plugins[plugin_id] = loaded
    _guard(plugin_id, instance.on_plugin_load)
    return describe(loaded)


def unload(args):
    plugin_id = args["id"]
    with _lock:
        loaded = plugins.pop(plugin_id, None)
    if loaded is None:
        return False
    _guard(plugin_id, loaded.instance.on_plugin_unload)
    _ayu_java.remove_plugin_hooks(plugin_id)
    _ayu_bridge.drop_callbacks(plugin_id)
    return True


def describe(loaded):
    instance = loaded.instance
    return {
        "id": loaded.id,
        "metadata": {k: v for k, v in loaded.metadata.items() if isinstance(v, (str, list))},
        "sendHook": instance._send_hook_priority is not None,
        "requestHooks": [h[0] for h in instance._hooks],
        "menuItems": [menu_item_schema(loaded.id, item) for item in instance._menu_items.values()],
        "diagnostics": _ayu_java.diagnostics.get(loaded.id, {}),
        "errors": _ayu_java.errors.get(loaded.id, []),
    }


def status(args):
    with _lock:
        return [describe(p) for p in plugins.values()]


def app_event(args):
    import base_plugin
    event = base_plugin.AppEvent(args["event"])
    with _lock:
        loaded = list(plugins.values())
    for plugin in loaded:
        _guard(plugin.id, plugin.instance.on_app_event, event)
    _ayu_java.dispatch("app." + event.value.lower(), [])
    return True


# ------------------------------------------------------------ send message

def send_message(args):
    """Outgoing plain text. Returns {"text": str, "cancel": bool}."""
    import base_plugin
    params = _ayu_java.SendMessageParams(peer=args.get("peer", 0), message=args["text"], replyToMsg=args.get("replyTo"))
    account = int(args.get("account", 0))
    with _lock:
        hooked = sorted((p for p in plugins.values() if p.instance._send_hook_priority is not None),
                        key=lambda p: -p.instance._send_hook_priority)
    for plugin in hooked:
        result = _guard(plugin.id, plugin.instance.on_send_message_hook, account, params)
        if not isinstance(result, base_plugin.HookResult):
            continue
        if result.strategy == base_plugin.HookStrategy.CANCEL:
            return {"text": args["text"], "cancel": True}
        if result.strategy in (base_plugin.HookStrategy.MODIFY, base_plugin.HookStrategy.MODIFY_FINAL):
            if result.params is not None:
                params = result.params
            if result.strategy == base_plugin.HookStrategy.MODIFY_FINAL:
                break
    if _ayu_java.has_hooks("message.outgoing"):
        param = _ayu_java.dispatch("message.outgoing", [params])
        if param.returnEarly:
            return {"text": args["text"], "cancel": True}
        if param.args and isinstance(param.args[0], _ayu_java.SendMessageParams):
            params = param.args[0]
    text = params.message if isinstance(params.message, str) else args["text"]
    return {"text": text, "cancel": not text}


# --------------------------------------------------------------------- menus

def menu_item_schema(plugin_id, item):
    menu_type = getattr(item.menu_type, "value", str(item.menu_type))
    return {"plugin": plugin_id, "id": item.item_id, "menu": menu_type, "text": str(item.text),
            "subtext": item.subtext, "priority": item.priority, "condition": item.condition}


def menu_items(args):
    wanted = set(args.get("menus") or [])
    result = []
    with _lock:
        loaded = list(plugins.values())
    for plugin in loaded:
        for item in plugin.instance._menu_items.values():
            schema = menu_item_schema(plugin.id, item)
            if not wanted or schema["menu"] in wanted:
                result.append(schema)
    result.sort(key=lambda i: -(i["priority"] or 0))
    return result


def menu_click(args):
    with _lock:
        plugin = plugins.get(args["plugin"])
    if plugin is None:
        return False
    item = plugin.instance._menu_items.get(args["id"])
    if item is None:
        return False
    context = dict(args.get("context") or {})
    message = context.get("message")
    if isinstance(message, dict):
        context["message"] = _MessageObject(message)
    _guard(plugin.id, item.on_click, context)
    return True


class _MessageObject:
    """Read-only subset of Telegram Android MessageObject for menu callbacks."""

    def __init__(self, data):
        self.messageOwner = types.SimpleNamespace(id=data.get("id"), message=data.get("text", ""), date=data.get("date", 0),
                                                  from_id=types.SimpleNamespace(user_id=data.get("fromId", 0)), dialog_id=data.get("dialogId", 0))
        self.messageText = data.get("text", "")
        self._data = data

    def getId(self):
        return self._data.get("id")

    def getDialogId(self):
        return self._data.get("dialogId", 0)

    def getFromChatId(self):
        return self._data.get("fromId", 0)

    def isOut(self):
        return bool(self._data.get("outgoing"))

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return _ayu_java.JavaMember("org.telegram.messenger.MessageObject", name)


# ------------------------------------------------------------------ settings

def settings_schema(args):
    with _lock:
        plugin = plugins.get(args["id"])
    if plugin is None:
        return None
    items = _guard(plugin.id, plugin.instance.create_settings) or []
    result = []
    for index, item in enumerate(items):
        schema = item.schema() if hasattr(item, "schema") else {"type": "unknown"}
        schema["index"] = index
        key = schema.get("key")
        if key is not None:
            schema["value"] = plugin.instance.get_setting(key, schema.get("default"))
        result.append(schema)
    return result


def setting_changed(args):
    with _lock:
        plugin = plugins.get(args["id"])
    if plugin is None:
        return False
    items = _guard(plugin.id, plugin.instance.create_settings) or []
    index = int(args["index"])
    if not 0 <= index < len(items):
        return False
    item = items[index]
    if "value" in args and getattr(item, "key", None):
        plugin.instance.set_setting(item.key, args["value"])
        if item.on_change is not None:
            _guard(plugin.id, item.on_change, args["value"])
    elif item.on_click is not None:
        _guard(plugin.id, item.on_click, None)
    return True


def callback(args):
    entry = _ayu_bridge.take_callback(args["id"], keep=bool(args.get("keep")))
    if entry is None:
        return False
    owner, fn = entry
    _guard(owner, fn, args.get("value"))
    return True


# ------------------------------------------------------------------ dispatch

def convert(args):
    from _ayu_converter import compile_source
    if "sourceData" in args:
        import base64
        encoded = args["sourceData"]
        if not isinstance(encoded, str) or len(encoded) > 90000:
            raise ValueError("Plugin source limit is 64 KB")
        source = base64.b64decode(encoded, validate=True).decode("utf-8")
    else:
        source = args["source"]
    return compile_source(source)


OPERATIONS = {
    "convert": convert,
    "configure": configure,
    "load": load,
    "unload": unload,
    "status": status,
    "appEvent": app_event,
    "sendMessage": send_message,
    "menuItems": menu_items,
    "menuClick": menu_click,
    "settingsSchema": settings_schema,
    "settingChanged": setting_changed,
    "callback": callback,
}


def call(request_json):
    try:
        request = json.loads(request_json)
        operation = OPERATIONS[request["op"]]
        return json.dumps({"ok": True, "result": operation(request.get("args") or {})}, ensure_ascii=False, default=str)
    except Exception as error:
        return json.dumps({"ok": False, "error": "%s: %s" % (type(error).__name__, error), "trace": traceback.format_exc(limit=6)}, ensure_ascii=False)


def install_native(handler):
    """Called once by the iOS host with its C callback."""
    _ayu_bridge.native = handler
