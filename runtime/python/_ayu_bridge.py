"""Python side of the native bridge.

On iOS the host installs `native` (a C function taking one JSON string and
returning one JSON string) before any plugin loads. On a desktop the bridge
falls back to `MockNative`, which records calls so the shim can be tested and
plugins can be dry-run without a device.
"""
import json
import threading


class MockNative:
    """Desktop stand-in for the iOS host. Records every call."""

    def __init__(self):
        self.calls = []
        self.lock = threading.Lock()
        self.responses = {"account.info": {"account": 0, "userId": 0, "isPremium": False}}

    def __call__(self, payload):
        request = json.loads(payload)
        with self.lock:
            self.calls.append(request)
        return json.dumps({"ok": True, "result": self.responses.get(request["op"])})

    def ops(self, name=None):
        with self.lock:
            return [c for c in self.calls if name is None or c["op"] == name]


native = None
_mock = None


def mock():
    global _mock
    if _mock is None:
        _mock = MockNative()
    return _mock


def call(op, **args):
    """Send one operation to the host. UI operations are asynchronous on the
    native side, so this never waits for the main thread."""
    handler = native if native is not None else mock()
    reply = json.loads(handler(json.dumps({"op": op, "args": args}, ensure_ascii=False, default=str)))
    if not reply.get("ok", False):
        raise RuntimeError("native %s failed: %s" % (op, reply.get("error", "unknown")))
    return reply.get("result")


_callbacks = {}
_callback_lock = threading.Lock()
_next_callback = [0]


def register_callback(owner, fn):
    """Keep a Python callable the host can invoke later (dialog buttons)."""
    with _callback_lock:
        _next_callback[0] += 1
        identifier = "cb%d" % _next_callback[0]
        _callbacks[identifier] = (owner, fn)
        return identifier


def take_callback(identifier, keep=False):
    with _callback_lock:
        return _callbacks.get(identifier) if keep else _callbacks.pop(identifier, None)


def drop_callbacks(owner):
    with _callback_lock:
        for key in [k for k, v in _callbacks.items() if v[0] == owner]:
            del _callbacks[key]


def log(level, tag, message):
    try:
        call("log", level=level, tag=tag, message=str(message))
    except Exception:
        pass
