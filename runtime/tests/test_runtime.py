"""Desktop tests of the iOS plugin runtime against the mock native bridge.

Run: python -m unittest discover -s runtime/tests
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "python"))

import _ayu_bridge  # noqa: E402
import _ayu_host  # noqa: E402
import _ayu_java  # noqa: E402

FIXTURES = os.path.join(HERE, "fixtures")


def host(op, **args):
    reply = json.loads(_ayu_host.call(json.dumps({"op": op, "args": args})))
    if not reply["ok"]:
        raise AssertionError(reply["error"] + "\n" + reply.get("trace", ""))
    return reply["result"]


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.data = tempfile.mkdtemp()
        _ayu_bridge.native = None
        _ayu_bridge._mock = None
        host("configure", dataDir=self.data)

    def tearDown(self):
        for plugin_id in list(_ayu_host.plugins):
            host("unload", id=plugin_id)
        shutil.rmtree(self.data, ignore_errors=True)

    def load(self, name):
        return host("load", path=os.path.join(FIXTURES, name))

    def test_send_hook_modifies_and_cancels(self):
        info = self.load("send_hook.plugin")
        self.assertTrue(info["sendHook"])
        self.assertEqual(host("sendMessage", text=".up hello", peer=1), {"text": "HELLO", "cancel": False})
        self.assertEqual(host("sendMessage", text=".nosend", peer=1)["cancel"], True)
        self.assertEqual(host("sendMessage", text="plain", peer=1), {"text": "plain", "cancel": False})

    def test_java_method_hook_is_wired_to_outgoing_event(self):
        info = self.load("java_send_hook.plugin")
        self.assertIn("org.telegram.messenger.SendMessagesHelper#sendMessage", info["diagnostics"]["wiredHooks"])
        self.assertEqual(host("sendMessage", text="hi", peer=5)["text"], "hi ~sig")
        self.assertTrue(host("sendMessage", text="block me", peer=5)["cancel"])

    def test_hooks_compose_in_order(self):
        self.load("send_hook.plugin")
        self.load("java_send_hook.plugin")
        self.assertEqual(host("sendMessage", text=".up a", peer=1)["text"], "A ~sig")

    def test_unload_removes_hooks(self):
        self.load("java_send_hook.plugin")
        host("unload", id="java_send_hook_fixture")
        self.assertEqual(host("sendMessage", text="hi", peer=5)["text"], "hi")

    def test_menu_click_settings_and_bulletin(self):
        info = self.load("menu_settings.plugin")
        self.assertEqual({i["menu"] for i in info["menuItems"]}, {"MESSAGE_CONTEXT_MENU", "CHAT_ACTION_MENU"})
        item = host("menuItems", menus=["MESSAGE_CONTEXT_MENU"])[0]
        host("menuClick", plugin=item["plugin"], id=item["id"], context={"dialog_id": 7, "message": {"id": 3, "text": "abc"}})
        mock = _ayu_bridge.mock()
        self.assertEqual(mock.ops("clipboard.set")[-1]["args"]["text"], "ABC!")
        self.assertEqual(mock.ops("bulletin.show")[-1]["args"]["kind"], "success")
        schema = host("settingsSchema", id="menu_settings_fixture")
        self.assertEqual([s["type"] for s in schema], ["header", "switch", "input", "selector"])
        host("settingChanged", id="menu_settings_fixture", index=3, value=0)
        host("settingChanged", id="menu_settings_fixture", index=2, value="?")
        host("menuClick", plugin=item["plugin"], id=item["id"], context={"message": {"id": 3, "text": "AbC"}})
        self.assertEqual(mock.ops("clipboard.set")[-1]["args"]["text"], "AbC?")
        with open(os.path.join(self.data, "settings", "menu_settings_fixture.settings.json"), encoding="utf-8") as handle:
            stored = json.load(handle)
        self.assertEqual(stored, {"mode": 0, "suffix": "?"})

    def test_alert_button_callback(self):
        self.load("menu_settings.plugin")
        item = host("menuItems", menus=["CHAT_ACTION_MENU"])[0]
        host("menuClick", plugin=item["plugin"], id=item["id"], context={})
        alert = _ayu_bridge.mock().ops("alert.show")[-1]["args"]
        self.assertEqual(alert["title"], "Question")
        positive = [b for b in alert["buttons"] if b["which"] == -1][0]
        self.assertTrue(host("callback", id=positive["callback"], value=-1))
        self.assertEqual(_ayu_host.plugins["menu_settings_fixture"].instance.get_setting("answered"), -1)

    def test_unsupported_android_calls_are_contained(self):
        info = self.load("android_ui.plugin")
        diagnostics = info["diagnostics"]
        self.assertIn("org.telegram.ui.Cells.ChatMessageCell#setMessageObject", diagnostics["unsupportedHooks"])
        self.assertIn("org.telegram.messenger.AndroidUtilities#getRealScreenSize", diagnostics["javaCalls"])
        self.assertIn("android.widget.TextView", diagnostics["javaObjects"])
        self.assertTrue(any("getRealScreenSize" in e for e in info["errors"]))
        self.assertEqual(_ayu_host.plugins["android_ui_fixture"].instance.padding, 8)

    def test_errors_are_reported_not_raised(self):
        path = os.path.join(self.data, "broken.plugin")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("__id__ = 'broken'\nraise RuntimeError('boom')\n")
        reply = json.loads(_ayu_host.call(json.dumps({"op": "load", "args": {"path": path}})))
        self.assertFalse(reply["ok"])
        self.assertIn("boom", reply["error"])
        self.assertNotIn("broken", _ayu_host.plugins)

    def test_unknown_operation(self):
        reply = json.loads(_ayu_host.call(json.dumps({"op": "nope"})))
        self.assertFalse(reply["ok"])


if __name__ == "__main__":
    unittest.main()
