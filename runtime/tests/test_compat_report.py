"""Checks of tools/plugin_compat_report.py on the runtime fixtures (static mode)."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
sys.path.insert(0, os.path.join(ROOT, "tools"))

import plugin_compat_report as report  # noqa: E402

FIXTURES = os.path.join(HERE, "fixtures")


def analyze(name):
    return report.analyze_source(os.path.join(FIXTURES, name))


class CompatReportTests(unittest.TestCase):
    def test_send_hook_runs(self):
        result = analyze("send_hook.plugin")
        self.assertEqual(result["verdict"], "runs")
        self.assertEqual(result["metadata"]["id"], "send_hook_fixture")

    def test_resolves_java_hook_targets(self):
        result = analyze("java_send_hook.plugin")
        features = [f["feature"] for f in result["features"]]
        self.assertIn("Java hook org.telegram.messenger.SendMessagesHelper#sendMessage", features)
        self.assertEqual(result["verdict"], "partial")

    def test_unmappable_ui_plugin(self):
        result = analyze("android_ui.plugin")
        self.assertEqual(result["verdict"], "unsupported")
        risks = [r["item"] for r in result["risks"]]
        self.assertIn("Java call org.telegram.messenger.AndroidUtilities#getRealScreenSize", risks)
        self.assertNotIn("Java call org.telegram.messenger.AndroidUtilities#dp", risks)

    def test_embedded_dex_blocks(self):
        entry = {"file": "x.plugin", "sha256": "0" * 64, "metadata": {"__name__": "X", "__version__": "1"},
                 "sdkCalls": ["hook_method"], "imports": ["base_plugin"], "javaClasses": [], "embeddedAndroidRuntimeMarkers": True}
        result = report.analyze_inventory(entry)
        self.assertEqual(result["verdict"], "unsupported")
        self.assertEqual(result["metadata"]["version"], "1")

    def test_every_wired_hook_has_an_event(self):
        for method in report.HOOK_MAP["methods"]:
            if method["status"] in report.WIRED:
                self.assertTrue(method.get("event"), method)


if __name__ == "__main__":
    unittest.main()
