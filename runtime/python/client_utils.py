"""exteraGram `client_utils` on the AyuGram iOS runtime.

Text sending and queues are implemented. Raw TL requests, media sending and
the Android controllers have no iOS bridge yet; they raise
`UnsupportedJavaCall` (controllers return opaque stubs whose methods raise).
"""
import threading

import _ayu_bridge
import _ayu_java
from _ayu_java import UnsupportedJavaCall

STAGE_QUEUE = "stageQueue"
GLOBAL_QUEUE = "globalQueue"
CACHE_CLEAR_QUEUE = "cacheClearQueue"
SEARCH_QUEUE = "searchQueue"
PHONE_BOOK_QUEUE = "phoneBookQueue"
THEME_QUEUE = "themeQueue"
EXTERNAL_NETWORK_QUEUE = "externalNetworkQueue"
PLUGINS_QUEUE = "pluginsQueue"

_queues = {}
_queues_lock = threading.Lock()


class _Queue:
    """A serial worker thread, like Android's DispatchQueue."""

    def __init__(self, name):
        self.name = name
        self.condition = threading.Condition()
        self.items = []
        self.thread = threading.Thread(target=self._run, name="ayu-" + name, daemon=True)
        self.thread.start()

    def post(self, fn, delay_ms=0):
        owner = _ayu_java.current_plugin()
        if delay_ms > 0:
            def later():
                with _ayu_java.active(owner):
                    self.post(fn)
            timer = threading.Timer(delay_ms / 1000.0, later)
            timer.daemon = True
            timer.start()
            return
        with self.condition:
            self.items.append((owner, fn))
            self.condition.notify()

    def _run(self):
        while True:
            with self.condition:
                while not self.items:
                    self.condition.wait()
                owner, fn = self.items.pop(0)
            with _ayu_java.active(owner):
                try:
                    fn()
                except Exception as error:
                    _ayu_java.record_error(owner, error)


def get_queue_by_name(name):
    with _queues_lock:
        queue = _queues.get(name)
        if queue is None:
            queue = _queues[name] = _Queue(name)
        return queue


def run_on_queue(fn, queue=PLUGINS_QUEUE, delay_ms=0):
    get_queue_by_name(queue).post(fn, delay_ms)


def send_text(peer_id, text, replyToMsg=None, parse_mode=None, account=None):
    return send_message({"peer": peer_id, "message": text, "replyToMsg": replyToMsg}, parse_mode=parse_mode, account=account)


def send_message(params, parse_mode=None, account=None):
    params = dict(params or {})
    unsupported = [key for key in ("photo", "document", "path", "replyMarkup", "ttl", "caption") if params.get(key)]
    if unsupported:
        _ayu_java.note("unsupportedSdk", "send_message:" + ",".join(unsupported))
        raise UnsupportedJavaCall("client_utils.send_message with " + ", ".join(unsupported))
    text = params.get("message")
    if not isinstance(text, str) or not text:
        raise ValueError("send_message needs a nonempty 'message'")
    reply = params.get("replyToMsg")
    reply_id = getattr(reply, "id", reply) if reply is not None else None
    _ayu_bridge.call("message.send", account=account or 0, peer=int(params["peer"]), text=text,
                     parseMode=(parse_mode or "").lower() or None, replyTo=reply_id if isinstance(reply_id, int) else None,
                     silent=params.get("notify") is False, scheduleDate=int(params.get("scheduleDate") or 0))


def _unsupported(name):
    def function(*args, **kwargs):
        _ayu_java.note("unsupportedSdk", name)
        raise UnsupportedJavaCall("client_utils." + name)
    function.__name__ = name
    return function


send_photo = _unsupported("send_photo")
send_document = _unsupported("send_document")
send_video = _unsupported("send_video")
send_audio = _unsupported("send_audio")
edit_message = _unsupported("edit_message")
send_request = _unsupported("send_request")


class RequestCallback:
    def __init__(self, fn):
        self.fn = fn


def _controller(class_name):
    def getter(account=None):
        _ayu_java.note("javaObjects", class_name)
        return _ayu_java.JavaObject(_ayu_java.JavaClass(class_name))
    return getter


get_last_fragment = _controller("org.telegram.ui.ActionBar.BaseFragment")
get_account_instance = _controller("org.telegram.messenger.AccountInstance")
get_messages_controller = _controller("org.telegram.messenger.MessagesController")
get_contacts_controller = _controller("org.telegram.messenger.ContactsController")
get_media_data_controller = _controller("org.telegram.messenger.MediaDataController")
get_connections_manager = _controller("org.telegram.tgnet.ConnectionsManager")
get_location_controller = _controller("org.telegram.messenger.LocationController")
get_notifications_controller = _controller("org.telegram.messenger.NotificationsController")
get_messages_storage = _controller("org.telegram.messenger.MessagesStorage")
get_send_messages_helper = _controller("org.telegram.messenger.SendMessagesHelper")
get_file_loader = _controller("org.telegram.messenger.FileLoader")
get_secret_chat_helper = _controller("org.telegram.messenger.SecretChatHelper")
get_download_controller = _controller("org.telegram.messenger.DownloadController")
get_notifications_settings = _controller("android.content.SharedPreferences")
get_notification_center = _controller("org.telegram.messenger.NotificationCenter")
get_media_controller = _controller("org.telegram.messenger.MediaController")


def get_user_config(account=None):
    return _ayu_java.STATIC_IMPLEMENTATIONS["org.telegram.messenger.UserConfig"]["getInstance"](account or 0)


class NotificationCenterDelegate:
    def didReceivedNotification(self, id, account, args):
        pass


class _AccountClient:
    """`self.client(account)` helper: binds send helpers to one account."""

    def __init__(self, account):
        self.account = account

    def send_text(self, peer_id, text, replyToMsg=None, parse_mode=None):
        return send_text(peer_id, text, replyToMsg, parse_mode, account=self.account)

    def send_message(self, params, parse_mode=None):
        return send_message(params, parse_mode, account=self.account)
