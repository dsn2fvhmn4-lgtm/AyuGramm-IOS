"""Java compatibility layer for exteraGram plugins on iOS.

exteraGram plugins run under Chaquopy inside Telegram Android and reach Java
classes directly. iOS has no JVM and no Android classes, so this module
replaces them with stubs:

* `import org.telegram.*`, `android.*`, `java.*` ... resolve to `JavaClass`
  stubs through a meta-path finder, so plugins import without errors.
* Hooks on Java methods (`hook_method`, `hook_all_methods`) are looked up in
  `hook_map.json`. Methods with an iOS equivalent are attached to a native
  event; everything else is recorded as unsupported and becomes a no-op.
* Calling a Java method with no Python implementation raises
  `UnsupportedJavaCall`. The host catches it at the plugin callback boundary,
  so one unsupported call disables one feature, not the whole plugin.
"""
import importlib.abc
import importlib.machinery
import json
import os
import sys
import threading
import types

import _ayu_bridge

JAVA_PREFIXES = ("org.telegram.", "android.", "androidx.", "java.", "javax.", "kotlin.", "com.exteragram.", "dalvik.", "com.google.android.")

_here = os.path.dirname(os.path.abspath(__file__))
_state = threading.local()
_lock = threading.RLock()


class UnsupportedJavaCall(NotImplementedError):
    def __init__(self, name):
        super().__init__("%s has no iOS implementation" % name)
        self.name = name


# ---------------------------------------------------------------- diagnostics

diagnostics = {}


def current_plugin():
    return getattr(_state, "plugin", None) or "<unknown>"


class active:
    """Context manager marking which plugin a callback belongs to."""

    def __init__(self, plugin_id):
        self.plugin_id = plugin_id

    def __enter__(self):
        self.previous = getattr(_state, "plugin", None)
        _state.plugin = self.plugin_id

    def __exit__(self, *exc):
        _state.plugin = self.previous
        return False


def note(kind, name, plugin_id=None):
    plugin_id = plugin_id or current_plugin()
    with _lock:
        entry = diagnostics.setdefault(plugin_id, {})
        bucket = entry.setdefault(kind, {})
        bucket[name] = bucket.get(name, 0) + 1


# ------------------------------------------------------------------ hook map

def _load_map():
    for candidate in (os.path.join(_here, "hook_map.json"), os.path.join(_here, "..", "hook_map.json")):
        if os.path.exists(candidate):
            with open(candidate, encoding="utf-8") as handle:
                return json.load(handle)
    return {"methods": [], "classes": []}


HOOK_MAP = _load_map()
_methods = {(m["class"], m["method"]): m for m in HOOK_MAP.get("methods", [])}
WIRED = {"wired", "partial"}


def method_entry(class_name, method_name):
    return _methods.get((class_name, method_name))


# --------------------------------------------------------------- Java stubs

class JavaMember:
    """An unresolved field or method. Calling it is unsupported; as a value it
    is an opaque zero-like constant (resource ids, flags)."""

    def __init__(self, owner, name):
        self._owner = owner
        self._name = name

    def __call__(self, *args, **kwargs):
        full = "%s#%s" % (self._owner, self._name)
        note("javaCalls", full)
        raise UnsupportedJavaCall(full)

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return JavaMember("%s.%s" % (self._owner, self._name), name)

    def __int__(self):
        return 0

    __index__ = __int__

    def __bool__(self):
        return False

    def __repr__(self):
        return "<java %s.%s>" % (self._owner, self._name)


class JavaMethodRef:
    def __init__(self, cls, name, parameter_types=()):
        self.cls = cls
        self.name = name
        self.parameter_types = parameter_types

    def getName(self):
        return self.name

    def setAccessible(self, flag):
        return None

    def getDeclaringClass(self):
        return self.cls

    def __repr__(self):
        return "<method %s#%s>" % (self.cls.name, self.name)


class JavaObject:
    """An instance of a stub class. Field reads give opaque members."""

    def __init__(self, cls, args=()):
        object.__setattr__(self, "_cls", cls)
        object.__setattr__(self, "_fields", {})

    def __getattr__(self, name):
        fields = object.__getattribute__(self, "_fields")
        if name in fields:
            return fields[name]
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "getClass":
            return lambda: object.__getattribute__(self, "_cls")
        return JavaMember(object.__getattribute__(self, "_cls").name, name)

    def __setattr__(self, name, value):
        object.__getattribute__(self, "_fields")[name] = value

    def __repr__(self):
        return "<java object %s>" % object.__getattribute__(self, "_cls").name


class JavaClass:
    """Stub for a Java class. Python implementations of selected static
    members come from `STATIC_IMPLEMENTATIONS`."""

    _cache = {}

    def __new__(cls, name):
        with _lock:
            existing = cls._cache.get(name)
            if existing is not None:
                return existing
            instance = super().__new__(cls)
            instance.name = name
            cls._cache[name] = instance
            return instance

    def __call__(self, *args, **kwargs):
        factory = CONSTRUCTORS.get(self.name)
        if factory is not None:
            return factory(*args, **kwargs)
        note("javaObjects", self.name)
        return JavaObject(self, args)

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        implemented = STATIC_IMPLEMENTATIONS.get(self.name, {}).get(name)
        if implemented is not None:
            return implemented
        if name in ("getDeclaredMethod", "getMethod"):
            return lambda method_name, *types: JavaMethodRef(self, method_name, types)
        if name in ("getDeclaredConstructor", "getConstructor"):
            return lambda *types: JavaMethodRef(self, "<init>", types)
        if name == "getName":
            return lambda: self.name
        if name == "getClass":
            return lambda: JavaClass("java.lang.Class")
        if name in ("class_", "_class", "klass"):
            return self
        if name[:1].isupper() and not name.isupper():
            return JavaClass(self.name + "$" + name)
        return JavaMember(self.name, name)

    def __instancecheck__(self, instance):
        return isinstance(instance, JavaObject) and object.__getattribute__(instance, "_cls") is self

    def __repr__(self):
        return "<java class %s>" % self.name


def find_class(name):
    if not isinstance(name, str) or not name:
        return None
    return JavaClass(name)


# ------------------------------------------- Python implementations of Java

def _run_later(runnable, delay=0):
    target = runnable.run if hasattr(runnable, "run") else runnable
    owner = current_plugin()

    def run():
        with active(owner):
            try:
                target()
            except Exception as error:  # Reported, never propagated to the host thread.
                record_error(owner, error)

    timer = threading.Timer(max(0, delay) / 1000.0, run)
    timer.daemon = True
    timer.start()


def _clipboard(text, *rest):
    _ayu_bridge.call("clipboard.set", text=str(text))
    return True


class _UserConfig:
    def __init__(self, account):
        self.account = account

    def getClientUserId(self):
        return int((_ayu_bridge.call("account.info") or {}).get("userId", 0))

    def isPremium(self):
        return bool((_ayu_bridge.call("account.info") or {}).get("isPremium", False))

    def isClientActivated(self):
        return True


STATIC_IMPLEMENTATIONS = {
    "org.telegram.messenger.AndroidUtilities": {
        "dp": lambda value: int(round(float(value))),
        "dpf2": lambda value: float(value),
        "runOnUIThread": _run_later,
        "addToClipboard": _clipboard,
        "isTablet": lambda: False,
    },
    "org.telegram.messenger.UserConfig": {
        "selectedAccount": 0,
        "MAX_ACCOUNT_COUNT": 3,
        "getInstance": lambda account=0: _UserConfig(account),
    },
    "org.telegram.messenger.LocaleController": {
        "getString": lambda *args: str(args[-1] if len(args) > 1 and isinstance(args[-1], str) else args[0]),
        "formatString": lambda key, res=None, *args: str(key),
        "isRTL": False,
    },
    "org.telegram.messenger.FileLog": {
        "d": lambda message: _ayu_bridge.log("debug", current_plugin(), message),
        "e": lambda message, *rest: _ayu_bridge.log("error", current_plugin(), message),
        "w": lambda message: _ayu_bridge.log("warn", current_plugin(), message),
    },
    "java.lang.System": {
        "currentTimeMillis": lambda: int(__import__("time").time() * 1000),
    },
}

CONSTRUCTORS = {
    "java.lang.String": lambda value="": str(value),
    "java.util.ArrayList": lambda *args: list(args[0]) if args and not isinstance(args[0], int) else [],
    "java.util.HashMap": lambda *args: {},
}


class SendMessageParams:
    """Python model of Telegram Android `SendMessagesHelper.SendMessageParams`
    for plain text sends. Unknown fields read as opaque Java members."""

    def __init__(self, peer=0, message="", replyToMsg=None, entities=None):
        self.peer = peer
        self.message = message
        self.caption = None
        self.replyToMsg = replyToMsg
        self.replyToTopMsg = None
        self.entities = entities if entities is not None else []
        self.notify = True
        self.scheduleDate = 0
        self.photo = None
        self.document = None
        self.replyMarkup = None
        self.params = None
        self.ttl = 0

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        note("javaFields", "SendMessageParams." + name)
        return JavaMember("SendMessageParams", name)


CONSTRUCTORS["org.telegram.messenger.SendMessagesHelper$SendMessageParams"] = lambda *a, **k: SendMessageParams()


# ---------------------------------------------------------------- hooking

class MethodHookParam:
    def __init__(self, method, this_object, args):
        self.method = method
        self.thisObject = this_object
        self.args = list(args)
        self._result = None
        self._throwable = None
        self.returnEarly = False

    def getResult(self):
        return self._result

    def setResult(self, value):
        self._result = value
        self.returnEarly = True

    def getThrowable(self):
        return self._throwable

    def hasThrowable(self):
        return self._throwable is not None

    def setThrowable(self, throwable):
        self._throwable = throwable
        self.returnEarly = True

    def getResultOrThrowable(self):
        return self._result


class Unhook:
    def __init__(self, record):
        self.record = record

    def unhook(self):
        with _lock:
            for hooks in _event_hooks.values():
                if self.record in hooks:
                    hooks.remove(self.record)

    def getHookedMethod(self):
        return self.record.ref


class _HookRecord:
    def __init__(self, plugin_id, ref, entry, handler, before, after, priority):
        self.plugin_id = plugin_id
        self.ref = ref
        self.entry = entry
        self.handler = handler
        self.before = before
        self.after = after
        self.priority = priority


_event_hooks = {}


def register_hook(plugin_id, ref, handler=None, before=None, after=None, priority=0):
    if isinstance(ref, (list, tuple)):
        return [register_hook(plugin_id, item, handler, before, after, priority) for item in ref]
    if not isinstance(ref, JavaMethodRef):
        note("unsupportedHooks", repr(ref), plugin_id)
        return Unhook(None)
    entry = method_entry(ref.cls.name, ref.name)
    key = "%s#%s" % (ref.cls.name, ref.name)
    record = _HookRecord(plugin_id, ref, entry, handler, before, after, priority)
    if entry is None or entry.get("status") not in WIRED:
        note("unsupportedHooks", key, plugin_id)
        return Unhook(record)
    note("wiredHooks", key, plugin_id)
    with _lock:
        hooks = _event_hooks.setdefault(entry["event"], [])
        hooks.append(record)
        hooks.sort(key=lambda r: -r.priority)
    return Unhook(record)


def remove_plugin_hooks(plugin_id):
    with _lock:
        for hooks in _event_hooks.values():
            hooks[:] = [r for r in hooks if r.plugin_id != plugin_id]


def has_hooks(event):
    with _lock:
        return bool(_event_hooks.get(event))


def dispatch(event, args, this_object=None, original=None):
    """Run all hooks for a native event. Returns the final MethodHookParam;
    `returnEarly` means a hook skipped the original operation."""
    with _lock:
        hooks = list(_event_hooks.get(event, []))
    param = MethodHookParam(None, this_object, args)
    for record in hooks:
        param.method = record.ref
        with active(record.plugin_id):
            try:
                if record.handler is not None and hasattr(record.handler, "replace_hooked_method"):
                    param.setResult(record.handler.replace_hooked_method(param))
                    break
                before = record.before or getattr(record.handler, "before_hooked_method", None)
                if before is not None:
                    before(param)
            except Exception as error:
                record_error(record.plugin_id, error)
        if param.returnEarly:
            break
    if not param.returnEarly and original is not None:
        param._result = original(param.args)
    for record in hooks:
        after = record.after or getattr(record.handler, "after_hooked_method", None)
        if after is None:
            continue
        with active(record.plugin_id):
            try:
                after(param)
            except Exception as error:
                record_error(record.plugin_id, error)
    return param


errors = {}


def record_error(plugin_id, error):
    with _lock:
        errors.setdefault(plugin_id, []).append("%s: %s" % (type(error).__name__, error))
        del errors[plugin_id][:-20]
    if isinstance(error, UnsupportedJavaCall):
        _ayu_bridge.log("warn", plugin_id, str(error))
    else:
        _ayu_bridge.log("error", plugin_id, "%s: %s" % (type(error).__name__, error))


# ----------------------------------------------------- the `java` module

def _java_module():
    module = types.ModuleType("java")
    module.__path__ = []
    module.__ayu_stub__ = True

    def jclass(name):
        return JavaClass(name)

    def dynamic_proxy(*interfaces):
        class Proxy(object):
            _interfaces = interfaces
        return Proxy

    def static_proxy(*args, **kwargs):
        return dynamic_proxy(*args)

    def jarray(element_type):
        return lambda values=(): list(values)

    def cast(cls, value):
        return value

    def identity(value=0):
        return value

    module.jclass = jclass
    module.dynamic_proxy = dynamic_proxy
    module.static_proxy = static_proxy
    module.jarray = jarray
    module.cast = cast
    module.jvoid = None
    for primitive in ("jboolean", "jbyte", "jshort", "jint", "jlong", "jfloat", "jdouble", "jchar"):
        setattr(module, primitive, identity)
    module.JavaException = Exception
    module.Override = lambda *a, **k: (lambda f: f)
    module.method = lambda *a, **k: (lambda f: f)
    module.constructor = lambda *a, **k: (lambda f: f)
    return module


class _JavaPackage(types.ModuleType):
    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return JavaClass(self.__name__ + "." + name)


class JavaFinder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def find_spec(self, fullname, path, target=None):
        # A Java package itself, or a parent of one ("org", "org.telegram").
        if fullname.startswith(JAVA_PREFIXES) or any(prefix.startswith(fullname + ".") for prefix in JAVA_PREFIXES):
            return importlib.machinery.ModuleSpec(fullname, self, is_package=True)
        return None

    def create_module(self, spec):
        if spec.name == "java":
            return _java_module()
        module = _JavaPackage(spec.name)
        module.__path__ = []
        return module

    def exec_module(self, module):
        if getattr(module, "__ayu_stub__", False):
            return
        note("javaImports", module.__name__)


_installed = False


def install():
    global _installed
    if not _installed:
        sys.meta_path.insert(0, JavaFinder())
        _installed = True


install()
