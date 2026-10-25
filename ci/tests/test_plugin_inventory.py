from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from analyze_plugin import analyze


class PluginInventoryTests(unittest.TestCase):
    def test_inventory_never_executes_plugin_and_does_not_claim_compatibility(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'example.plugin'
            marker = Path(folder) / 'executed.txt'
            source.write_text('__id__ = "example"\nfrom android.view import View\ndef hook():\n    from ui.settings import Switch\nopen(' + repr(str(marker)) + ', "w").write("executed")\n', encoding='utf-8')
            report = analyze(source)
            self.assertFalse(marker.exists())
            self.assertIn('ui.settings', report['imports'])
            self.assertEqual(report['status'], 'No complete native adapter implemented')
            self.assertEqual(report['metadata']['__id__'], 'example')

    def test_large_embedded_android_plugin_is_reported_without_loading_payloads(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'large.plugin'
            source.write_text('__id__ = "large"\nDEX_BEGIN = "__DEX_BEGIN__"\nNATIVE_BEGIN = "__NATIVE_BEGIN__"\n#' + 'A' * (600 * 1024), encoding='utf-8')
            report = analyze(source)
            self.assertTrue(report['embeddedAndroidRuntimeMarkers'])
            self.assertFalse(report['withinCurrentImportLimit'])
            self.assertEqual(report['status'], 'No complete native adapter implemented')
