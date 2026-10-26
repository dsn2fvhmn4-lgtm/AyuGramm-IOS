"""exteraGram `base_plugin` API on the AyuGram iOS runtime."""
import enum
import json
import logging
import os

import _ayu_bridge
import _ayu_java


class HookStrategy(enum.Enum):
    DEFAULT = "DEFAULT"
    CANCEL = "CANCEL"
    MODIFY = "MODIFY"
    MODIFY_FINAL = "MODIFY_FINAL"


class HookResult:
    def __init__(self, strategy=HookStrategy.DEFAULT, request=None, response=None, update=None, updates=None, params=None):
        self.strategy = strategy
        self.request = request
        self.response = response
        self.update = update
        self.updates = updates
        self.params = params


class AppEvent(enum.Enum):
    START = "START"
    STOP = "STOP"
    PAUSE = "PAUSE"
    RESUME = "RESUME"


class MenuItemType(enum.Enum):
    MESSAGE_CONTEXT_MENU = "MESSAGE_CONTEXT_MENU"
    DRAWER_MENU = "DRAWER_MENU"
    MAIN_MENU = "MAIN_MENU"
    CHAT_ACTION_MENU = "CHAT_ACTION_MENU"
    PROFILE_ACTION_MENU = "PROFILE_ACTION_MENU"


class MenuItemData:
    def __init__(self, menu_type, text, on_click, item_id=None, icon=None, subtext=None, condition=None, priority=0):
        self.menu_type = menu_type
        self.text = text
        self.on_click = on_click
        self.item_id = item_id
        self.icon = icon
        self.subtext = subtext
        self.condition = condition
        self.priority = priority


class MethodHook:
    def before_hooked_method(self, param):
        pass

    def after_hooked_method(self, param):
        pass


class MethodReplacement:
    def replace_hooked_method(self, param):
        return None


class XposedHook(MethodHook):
    pass


class _PluginLogger(logging.LoggerAdapter):
    def __init__(self, plugin_id):
        super().__init__(logging.getLogger("plugin." + plugin_id), {})
        self.plugin_id = plugin_id

    def log(self, level, msg, *args, **kwargs):
        text = msg % args if args else str(msg)
        if kwargs.get("exc_info"):
            import traceback
            text += "\n" + traceback.format_exc()
        _ayu_bridge.log(logging.getLevelName(level).lower(), self.plugin_id, text)

    def dump(self, obj):
        self.log(logging.DEBUG, "%r", obj)


class BasePlugin:
    """Base class of every exteraGram plugin. The host sets `id`, `name` and
    the settings directory before calling `on_plugin_load`."""

    def __init__(self):
        self.id = getattr(self, "id", None) or "plugin"
        self.name = getattr(self, "name", None) or self.id
        self._settings_path = None
        self._settings = {}
        self._hooks = []
        self._send_hook_priority = None
        self._menu_items = {}
        self._unhooks = []
        self.logger = _PluginLogger(self.id)

    # --------------------------------------------------- host-side setup

    def _ayu_attach(self, plugin_id, name, settings_dir):
        # Plugins that override __init__ without calling super() still work.
        for attribute, value in (("_hooks", []), ("_send_hook_priority", None), ("_menu_items", {}), ("_unhooks", [])):
            self.__dict__.setdefault(attribute, value)
        self.id = plugin_id
        self.name = name
        self.logger = _PluginLogger(plugin_id)
        self._settings_path = os.path.join(settings_dir, plugin_id + ".settings.json")
        try:
            with open(self._settings_path, encoding="utf-8") as handle:
                loaded = json.load(handle)
            self._settings = loaded if isinstance(loaded, dict) else {}
        except (OSError, ValueError):
            self._settings = {}

    # -------------------------------------------------------- lifecycle

    def on_plugin_load(self):
        pass

    def on_plugin_unload(self):
        pass

    def on_app_event(self, event_type):
        pass

    def create_settings(self):
        return []

    # ------------------------------------------------------------ hooks

    def add_hook(self, name, match_substring=False, priority=0):
        self._hooks.append((name, match_substring, priority))
        _ayu_java.note("unsupportedSdk", "add_hook:" + str(name), self.id)

    def remove_hook(self, name):
        self._hooks = [h for h in self._hooks if h[0] != name]

    def add_on_send_message_hook(self, priority=0):
        self._send_hook_priority = priority

    def remove_on_send_message_hook(self):
        self._send_hook_priority = None

    def pre_request_hook(self, request_name, account, request):
        return HookResult()

    def post_request_hook(self, request_name, account, response, error):
        return HookResult()

    def on_update_hook(self, update_name, account, update):
        return HookResult()

    def on_updates_hook(self, container_name, account, updates):
        return HookResult()

    def on_send_message_hook(self, account, params):
        return HookResult()

    def hook_method(self, method, handler=None, priority=0, before=None, after=None, **kwargs):
        unhook = _ayu_java.register_hook(self.id, method, handler, before, after, priority)
        self._unhooks.append(unhook)
        return unhook

    def hook_all_methods(self, cls, method_name, handler=None, priority=0, before=None, after=None, **kwargs):
        if not isinstance(cls, _ayu_java.JavaClass):
            cls = _ayu_java.find_class(getattr(cls, "name", str(cls)))
        unhook = _ayu_java.register_hook(self.id, _ayu_java.JavaMethodRef(cls, method_name), handler, before, after, priority)
        self._unhooks.append(unhook)
        return [unhook]

    def hook_all_constructors(self, cls, handler=None, priority=0, before=None, after=None, **kwargs):
        name = getattr(cls, "name", str(cls))
        unhook = _ayu_java.register_hook(self.id, _ayu_java.JavaMethodRef(_ayu_java.find_class(name), "<init>"), handler, before, after, priority)
        self._unhooks.append(unhook)
        return [unhook]

    def unhook_method(self, unhook):
        for item in unhook if isinstance(unhook, (list, tuple)) else [unhook]:
            if item is not None:
                item.unhook()

    # ------------------------------------------------------------- menu

    def add_menu_item(self, item):
        item_id = item.item_id or "%s_%d" % (self.id, len(self._menu_items) + 1)
        item.item_id = item_id
        self._menu_items[item_id] = item
        return item_id

    def remove_menu_item(self, item_id):
        return self._menu_items.pop(item_id, None) is not None

    # --------------------------------------------------------- settings

    def get_setting(self, key, default=None):
        return self._settings.get(key, default)

    def set_setting(self, key, value, reload_settings=False):
        self._settings[key] = value
        self._save_settings()

    def export_settings(self):
        return dict(self._settings)

    def import_settings(self, settings, reload_settings=True):
        self._settings = dict(settings or {})
        self._save_settings()

    def _save_settings(self):
        if not self._settings_path:
            return
        temporary = self._settings_path + ".tmp"
        with open(temporary, "w", encoding="utf-8") as handle:
            json.dump(self._settings, handle, ensure_ascii=False, default=str)
        os.replace(temporary, self._settings_path)

    # ------------------------------------------------------------- misc

    def log(self, message):
        _ayu_bridge.log("info", self.id, message)

    def client(self, account=0):
        import client_utils
        return client_utils._AccountClient(account)
