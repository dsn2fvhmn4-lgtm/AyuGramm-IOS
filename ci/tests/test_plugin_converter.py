import importlib.util
from pathlib import Path
import tempfile
import unittest
import sys

path = Path(__file__).resolve().parents[2] / 'tools/convert_plugin.py'
sys.path.insert(0, str(path.parent))
spec = importlib.util.spec_from_file_location('ayu_convert_plugin', path)
converter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(converter)


class PluginConverterTests(unittest.TestCase):
    def test_supported_hook_templates_convert_without_execution(self):
        import json
        for name in ['android_literal_hook', 'android_prefix_hook', 'android_typed_hook']:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as folder:
                source = path.parents[1] / 'plugins' / (name + '.plugin')
                destination = Path(folder) / 'converted.plugin'
                converter.convert(source, destination)
                manifest = json.loads(destination.read_text(encoding='utf-8'))
                self.assertEqual(manifest['actions'][0]['kind'], 'outgoingReplace')
                self.assertEqual(manifest['convertedFrom'], 'exteraGram/literal-send-hook-v1')
                self.assertEqual(manifest['actions'][0].get('prefix'), '[note]' if 'prefix' in name else None)

    def test_extra_code_and_expanding_rules_reject_the_entire_plugin(self):
        from plugin_patterns import compile_source
        template = (path.parents[1] / 'plugins/android_literal_hook.plugin').read_text(encoding='utf-8')
        for source in [template + '\nprint("unexpected")\n', template.replace('"tehh", "the"', '"a", "too long"'), template.replace('"tehh", "the"', '"a", ""'), template.replace('class LiteralHookDemo', '@arbitrary_decorator\nclass LiteralHookDemo')]:
            with self.subTest(source=source[-50:]), self.assertRaises(ValueError):
                compile_source(source.encode())

    def test_generic_class_and_method_parameters_are_rejected(self):
        from plugin_patterns import compile_source
        source = (path.parents[1] / 'plugins/android_literal_hook.plugin').read_text(encoding='utf-8')
        for changed in [source.replace('class LiteralHookDemo(', 'class LiteralHookDemo[T]('), source.replace('def on_plugin_load(', 'def on_plugin_load[T](')]:
            with self.assertRaises(ValueError):
                compile_source(changed.encode())

    def test_unsupported_replacement_count_is_rejected(self):
        from plugin_patterns import compile_source
        source = (path.parents[1] / 'plugins/android_literal_hook.plugin').read_text(encoding='utf-8')
        with self.assertRaises(ValueError):
            compile_source(source.replace('"tehh", "the"', '"tehh", "the", True').encode())

    def test_extended_hook_matrix_matches_expected_manifests(self):
        import json
        from plugin_patterns import compile_source
        matrix = json.loads((path.parents[1] / 'plugins/android_hook_matrix.json').read_text(encoding='utf-8'))
        for case in matrix:
            with self.subTest(case=case['name']):
                self.assertEqual(compile_source(case['source'].encode()), case['expected'])
                self.assertEqual(case['expected']['apiVersion'], 2, 'Extended conditions/counts must not be consumed by API-1 clients')

    def test_unsupported_conditions_and_counts_reject_whole_source(self):
        from plugin_patterns import compile_source
        source = (path.parents[1] / 'plugins/android_prefix_hook.plugin').read_text(encoding='utf-8')
        for expression in ['params.message.startswith("[note]") or True', 'params.message.endswith("[note]", 1)', '"x" in params.message.lower()', 'params.message == "x" == "y"']:
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                compile_source(source.replace('params.message.startswith("[note]")', expression).encode())
        source = (path.parents[1] / 'plugins/android_literal_hook.plugin').read_text(encoding='utf-8')
        for count in ['-1', '4097', 'True', '1.0', 'self.limit', '1, 2']:
            with self.subTest(count=count), self.assertRaises(ValueError):
                compile_source(source.replace('"tehh", "the"', '"tehh", "the", ' + count).encode())

    def test_camera_metadata_does_not_select_reviewed_adapter(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'camera_flip.plugin'
            destination = Path(folder) / 'native.plugin'
            source.write_text('__id__ = "camera_flip"\n__name__ = "Camera Flip"\nprint("extra")', encoding='utf-8')
            with self.assertRaises(ValueError):
                converter.convert(source, destination)
            self.assertFalse(destination.exists())

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
