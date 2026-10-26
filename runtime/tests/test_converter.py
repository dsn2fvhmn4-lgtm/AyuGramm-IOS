"""AST compiler coverage; plugin input is never executed."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
from _ayu_converter import compile_source
import _ayu_host

HEADER = '''from base_plugin import BasePlugin, HookResult, HookStrategy
__id__ = "converter_test"
__name__ = "Converter test"
class Example(BasePlugin):
    def on_plugin_load(self):
        self.add_on_send_message_hook()
    def on_send_message_hook(self, account, params):
'''


def plugin(body):
    return HEADER + ''.join('        ' + line + '\n' for line in body.splitlines()) + '        return HookResult(strategy=HookStrategy.MODIFY, params=params)\n'


class ConverterTests(unittest.TestCase):
    def test_chained_operations_and_alias_commit(self):
        source = plugin('text = params.message\ntext = text.strip().lower().replace("tehh", "the", 1)\nparams.message = text')
        result = compile_source(source)
        self.assertEqual(result['apiVersion'], 6)
        self.assertEqual([i['op'] for i in result['actions'][0]['program']['instructions']], ['strip', 'lower', 'replace'])
        self.assertEqual(result['actions'][0]['program']['instructions'][-1]['count'], 1)

    def test_branch_is_evaluated_once_for_a_whole_block(self):
        result = compile_source(plugin('if params.message.startswith("!"):\n    params.message = params.message.removeprefix("!").upper()\nelse:\n    params.message = "[note] " + params.message'))
        branch = result['actions'][0]['program']['instructions'][0]
        self.assertEqual(branch['op'], 'branch')
        self.assertEqual([i['op'] for i in branch['body']], ['removePrefix', 'upper'])
        self.assertEqual(branch['otherwise'], [{'op': 'prepend', 'value': '[note] '}])

    def test_deletion_and_expansion_are_bounded_native_instructions(self):
        result = compile_source(plugin('params.message = params.message.replace("x", "").replace("a", "longer")'))
        self.assertEqual(len(result['actions'][0]['program']['instructions']), 2)

    def test_comments_tabs_annotations_and_docstrings(self):
        source = plugin('"""Hook documentation."""\n# comment\nparams.message = params.message.upper()')
        source = source.replace('def on_send_message_hook(self, account, params):', 'def on_send_message_hook(self, account: int, params) -> HookResult:')
        self.assertEqual(compile_source(source)['id'], 'converter_test')

    def test_full_file_rejection_has_no_side_effects(self):
        with tempfile.TemporaryDirectory() as folder:
            marker = Path(folder) / 'executed.txt'
            source = plugin('params.message = params.message.lower()') + 'open(' + repr(str(marker)) + ', "w").write("oops")\n'
            with self.assertRaises(ValueError):
                compile_source(source)
            self.assertFalse(marker.exists())

    def test_unknown_calls_loops_and_partial_aliases_reject(self):
        for body in ['params.message = params.message.format("x")',
                     'params.message = arbitrary(params.message)',
                     'for i in range(5):\n    params.message = params.message.upper()',
                     'text = params.message\ntext = text.lower()',
                     'params.message = params.message.replace("", "x")',
                     'params.message = params.message.replace("x", "y", True)']:
            with self.subTest(body=body), self.assertRaises(ValueError):
                compile_source(plugin(body))

    def test_size_depth_and_instruction_limits(self):
        with self.assertRaises(ValueError):
            compile_source(plugin('\n'.join(['params.message = params.message.lower()'] * 65)))
        with self.assertRaises(ValueError):
            compile_source('x' * 65537)

    def test_native_dispatch_returns_manifest_or_a_real_error(self):
        result = json.loads(_ayu_host.call(json.dumps({'op': 'convert', 'args': {'source': plugin('params.message = params.message.upper()')}})))
        self.assertTrue(result['ok'])
        self.assertEqual(result['result']['convertedFrom'], 'exteraGram/ast-send-hook-v2')
        error = json.loads(_ayu_host.call(json.dumps({'op': 'convert', 'args': {'source': 'import android.view'}})))
        self.assertFalse(error['ok'])

    def test_bom_and_crlf_preserve_the_original_source_hash(self):
        import base64
        import hashlib
        source = ("\ufeff" + plugin('params.message = params.message.upper()')).replace("\n", "\r\n").encode('utf-8')
        result = json.loads(_ayu_host.call(json.dumps({'op': 'convert', 'args': {'sourceData': base64.b64encode(source).decode()}})))
        self.assertTrue(result['ok'])
        self.assertEqual(result['result']['sourceSHA256'], hashlib.sha256(source).hexdigest())

    def test_checked_in_native_fixture_matches_the_device_compiler(self):
        root = Path(__file__).resolve().parents[2]
        source = (root / 'plugins/android_branch_hook.plugin').read_text(encoding='utf-8')
        expected = json.loads((root / 'plugins/android_branch_hook_ios.plugin').read_text(encoding='utf-8'))
        self.assertEqual(compile_source(source), expected)
