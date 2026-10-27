import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from publish_plugin_catalog import native_manifest, package, ADAPTER_DOMAIN, CATALOG_DOMAIN


class RecordingSigner:
    def __init__(self): self.messages = []
    def sign(self, message):
        self.messages.append(message)
        return bytes(64)


class PluginCatalogTests(unittest.TestCase):
    def manifest(self):
        return json.loads((ROOT / 'plugins/android_branch_hook_ios.plugin').read_text(encoding='utf-8'))

    def test_adapter_binds_exact_source_bytes_and_uses_catalog_abi(self):
        original = self.manifest()
        native = native_manifest(original, b'original\r\nplugin')
        self.assertEqual(native['apiVersion'], 7)
        self.assertEqual(native['convertedFrom'], 'ayugram/catalog-v1')
        self.assertEqual(native['sourceSHA256'], hashlib.sha256(b'original\r\nplugin').hexdigest())
        self.assertEqual(native['actions'], original['actions'])

    def test_publisher_separates_catalog_and_adapter_signature_domains(self):
        signer = RecordingSigner()
        envelope = package([self.manifest()], signer, 3)
        self.assertTrue(signer.messages[0].startswith(ADAPTER_DOMAIN))
        self.assertTrue(signer.messages[1].startswith(CATALOG_DOMAIN))
        payload = json.loads(base64.b64decode(envelope['payload']))
        self.assertEqual(payload['revision'], 3)
        self.assertEqual(len(payload['adapters']), 1)

    def test_duplicate_source_hashes_and_unknown_actions_reject(self):
        with self.assertRaises(ValueError): package([self.manifest(), self.manifest()], RecordingSigner(), 1)
        value = self.manifest(); value['actions'][0]['kind'] = 'executePython'
        with self.assertRaises(ValueError): native_manifest(value)

    def test_reserved_or_unrelated_fields_are_not_signed_as_manifest_fields(self):
        value = self.manifest(); value['revision'] = 999; value['adapters'] = []
        value['catalogProof'] = {'signature': 'untrusted'}
        result = native_manifest(value)
        self.assertNotIn('revision', result)
        self.assertNotIn('adapters', result)
        self.assertNotIn('catalogProof', result)

    def test_public_catalog_contains_the_new_demo_file(self):
        envelope = json.loads((ROOT / 'plugin-catalog/catalog.json').read_text(encoding='utf-8'))
        payload = json.loads(base64.b64decode(envelope['payload']))
        expected = hashlib.sha256((ROOT / 'plugins/ota_lowercase_demo.plugin').read_bytes()).hexdigest()
        entries = [json.loads(base64.b64decode(item['manifestData'])) for item in payload['adapters']]
        self.assertTrue(any(e['sourceSHA256'] == expected and e['id'] == 'ota_lowercase_demo' for e in entries))
        self.assertEqual(len(base64.b64decode(envelope['signature'])), 64)
        self.assertEqual(len(base64.b64decode((ROOT / 'plugin-catalog/public-key.txt').read_text())), 32)

    def test_demo_requires_an_adapter_instead_of_silently_ignoring_helper_methods(self):
        sys.path.insert(0, str(ROOT / 'runtime/python'))
        from _ayu_converter import compile_source
        with self.assertRaises(ValueError): compile_source((ROOT / 'plugins/ota_lowercase_demo.plugin').read_text(encoding='utf-8'))

    def test_supplied_batch_report_matches_published_catalog_without_placeholder_adapters(self):
        report = json.loads((ROOT / 'docs/PLUGIN_BATCH_STATUS.json').read_text(encoding='utf-8'))
        envelope = json.loads((ROOT / 'plugin-catalog/catalog.json').read_text(encoding='utf-8'))
        payload = json.loads(base64.b64decode(envelope['payload']))
        entries = {json.loads(base64.b64decode(item['manifestData']))['sourceSHA256']: json.loads(base64.b64decode(item['manifestData'])) for item in payload['adapters']}
        self.assertEqual(len(report['plugins']), 28)
        supported = [row for row in report['plugins'] if row['status'] == 'supported_native_adapter']
        self.assertEqual(len(supported), 4)
        for row in supported:
            self.assertEqual(entries[row['sha256']]['id'], row['metadata']['__id__'])
            self.assertEqual(native_manifest(entries[row['sha256']]), entries[row['sha256']])
        for row in report['plugins']:
            if row['status'] == 'requires_engine_update':
                self.assertNotIn(row['sha256'], entries)
                self.assertTrue(row['engine_work'])
                self.assertTrue(row['note_ru'])

    def test_fixed_signed_catalog_fixture_keeps_rollback_tests_independent_of_publication(self):
        envelope = json.loads((ROOT / 'plugins/catalog_revision2.fixture.json').read_text(encoding='utf-8'))
        payload = json.loads(base64.b64decode(envelope['payload']))
        self.assertEqual(payload['revision'], 2)
        self.assertEqual(len(payload['adapters']), 5)

    def test_new_native_capabilities_publish_with_their_required_engine_api(self):
        for kind in ('groupMentions', 'petpet', 'reactionsTotal'):
            value = self.manifest()
            value['actions'] = [{'id': 'native', 'title': 'Native', 'kind': kind}]
            manifest = native_manifest(value)
            self.assertEqual(manifest['apiVersion'], 8)
            self.assertEqual(manifest['actions'][0]['kind'], kind)
