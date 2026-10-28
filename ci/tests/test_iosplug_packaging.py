import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("iosplug_packager", ROOT / "tools/package_iosplug.py")
PACKAGER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGER)
EMPTY_CATALOG = {"payload": base64.b64encode(b'{"adapters":[]}').decode()}


class IOSPlugPackagingTests(unittest.TestCase):
    def test_unique_sources_are_packaged_without_executing_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            code = b"raise RuntimeError('Plugin source must not execute')\n"
            (source / "one.plugin").write_bytes(code)
            (source / "one (2).plugin").write_bytes(code)
            digest = hashlib.sha256(code).hexdigest()
            native = {"id": "pill_labels", "name": "Pill Labels", "version": "1", "author": "Author", "description": "UI"}
            registry = {"sources": {digest: {"native": native, "minimum_app": "batch 2", "limitations": ["Profile only"]}}}
            result = PACKAGER.package(source, root / "output", registry, EMPTY_CATALOG)
            self.assertEqual((result["unique_sources"], result["package_count"]), (1, 1))
            self.assertEqual((source / "one.plugin").read_bytes(), code)
            card = json.loads((root / "output/pill_labels.iosplug").read_text())
            self.assertEqual(card["format"], "ayu-iosplug-1")
            self.assertEqual(result["plugins"][0]["duplicates"], ["one (2).plugin"])

    def test_unknown_source_gets_a_reason_instead_of_a_fake_plugin(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "source").mkdir()
            (root / "source/unknown.plugin").write_text("pass")
            result = PACKAGER.package(root / "source", root / "output", {"sources": {}}, EMPTY_CATALOG)
            self.assertEqual(result["package_count"], 0)
            self.assertEqual(list((root / "output").glob("*.iosplug")), [])
            self.assertEqual(result["plugins"][0]["status"], "not_ported")
            with self.assertRaises(FileExistsError):
                PACKAGER.package(root / "source", root / "output", {"sources": {}}, EMPTY_CATALOG)

    def test_publication_retains_the_actual_adapter_signature(self):
        catalog = PACKAGER.read_json(ROOT / "plugin-catalog/catalog.json")
        for digest, adapter in PACKAGER.signed_adapters(catalog).items():
            proof = adapter["catalogProof"]
            original = json.loads(base64.b64decode(proof["manifestData"]))
            self.assertEqual(digest, original["sourceSHA256"])
            self.assertEqual(original, {key: value for key, value in adapter.items() if key != "catalogProof"})
            self.assertEqual(len(base64.b64decode(proof["signature"])), 64)

    def test_all_published_files_have_their_source_and_audited_mapping(self):
        report = PACKAGER.read_json(ROOT / "plugins/iosplug/compatibility.json")
        cards = list((ROOT / "plugins/iosplug").glob("*.iosplug"))
        self.assertEqual(report["package_count"], len(cards))
        self.assertEqual(len(report["plugins"]), report["unique_sources"])
        expected = {row["file"] for row in report["plugins"] if "file" in row}
        self.assertEqual(expected, {path.name for path in cards})
        for row in report["plugins"]:
            self.assertTrue(row.get("limitations") or row.get("reason"))
            if row["status"] == "not_ported":
                self.assertIsInstance(row["required_entrypoints"], list)
                self.assertTrue(all(isinstance(value, str) for value in row["required_entrypoints"]))
        for path in cards:
            self.assertLessEqual(path.stat().st_size, PACKAGER.CARD_LIMIT)
            card = PACKAGER.read_json(path)
            self.assertIn(card["format"], ["ayu-iosplug-1", "ayu-iosplug-2"])
            if card["format"] == "ayu-iosplug-2":
                self.assertEqual(card["minimumEngineVersion"], 2)
                self.assertIn("catalogProof", card["adapter"])

    def test_source_directory_cannot_be_used_for_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                PACKAGER.package(root, root / "output", {"sources": {}}, EMPTY_CATALOG)


if __name__ == "__main__":
    unittest.main()
