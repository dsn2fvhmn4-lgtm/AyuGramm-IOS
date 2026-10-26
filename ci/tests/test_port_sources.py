import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from port_sources import missing_port_sources


class PortSourceExportTests(unittest.TestCase):
    def test_missing_model_input_is_reported_before_sdk_invocation(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            names = ['AyuAdvancedSettings.swift', 'AyuChatExportModels.swift', 'AyuTranslationRequest.swift']
            manifest = source / 'manifest.json'
            manifest.write_text(json.dumps(names), encoding='utf-8')
            self.assertEqual(missing_port_sources(source, manifest), names)
            for name in names:
                (source / name).write_text('import Foundation\n', encoding='utf-8')
            self.assertEqual(missing_port_sources(source, manifest), [])
            (source / names[1]).unlink()
            self.assertEqual(missing_port_sources(source, manifest), [names[1]])
