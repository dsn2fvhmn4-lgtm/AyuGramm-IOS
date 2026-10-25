import importlib.util
from pathlib import Path
import tempfile
import unittest

path = Path(__file__).resolve().parents[2] / 'tools/convert_plugin.py'
spec = importlib.util.spec_from_file_location('ayu_convert_plugin', path)
converter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(converter)


class PluginConverterTests(unittest.TestCase):
    def test_unreviewed_python_metadata_does_not_select_an_adapter(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'search_plus.plugin'
            output = Path(folder) / 'converted.plugin'
            source.write_text('__id__ = "search_plus"\n__version__ = "2.6.1"\nraise Exception()', encoding='utf-8')
            with self.assertRaises(ValueError):
                converter.convert(source, output)
            self.assertFalse(output.exists())

    def test_same_path_preserves_original(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'original.plugin'
            source.write_bytes(b'original')
            with self.assertRaises(ValueError):
                converter.convert(source, source)
            self.assertEqual(source.read_bytes(), b'original')

    def test_plugin_extension_is_required(self):
        with self.assertRaises(ValueError):
            converter.convert(Path('input.py'), Path('output.plugin'))
        with self.assertRaises(ValueError):
            converter.convert(Path('input.plugin'), Path('output.py'))

    def test_oversized_file_is_rejected_before_conversion(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'large.plugin'
            source.write_bytes(b'x' * (512 * 1024 + 1))
            with self.assertRaises(ValueError):
                converter.convert(source, Path(folder) / 'output.plugin')


if __name__ == '__main__':
    unittest.main()
