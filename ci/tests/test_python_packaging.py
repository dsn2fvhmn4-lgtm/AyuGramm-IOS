import io
from pathlib import Path
import plistlib
import sys
import tarfile
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from python_support import resource_files, package


class PythonPackagingTests(unittest.TestCase):
    def test_stdlib_extensions_are_frameworks_with_round_trip_markers(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            archive = folder / 'support.tar.gz'
            members = {
                'Python.xcframework/lib/python3.13/encodings/__init__.py': b'# encoding',
                'Python.xcframework/lib/python3.13/test/skip.py': b'not bundled',
                'Python.xcframework/ios-arm64/lib-arm64/python3.13/lib-dynload/math.cpython-313-iphoneos.so': b'binary',
            }
            with tarfile.open(archive, 'w:gz') as output:
                for name, value in members.items():
                    item = tarfile.TarInfo(name); item.size = len(value)
                    output.addfile(item, io.BytesIO(value))
            runtime = folder / 'runtime'
            (runtime / 'python').mkdir(parents=True)
            (runtime / 'python/_ayu_converter.py').write_text('# converter', encoding='utf-8')
            (runtime / 'hook_map.json').write_text('{}', encoding='utf-8')
            files = resource_files(archive, runtime, 'release_arm64')
            self.assertNotIn('python/lib/python3.13/test/skip.py', files)
            self.assertEqual(files['Frameworks/math.framework/math'], b'binary')
            marker = 'python/lib/python3.13/lib-dynload/math.cpython-313-iphoneos.fwork'
            self.assertEqual(files[marker].decode().strip(), 'Frameworks/math.framework/math')
            self.assertEqual(files['Frameworks/math.framework/math.origin'].decode().strip(), marker)
            self.assertEqual(plistlib.loads(files['Frameworks/math.framework/Info.plist'])['CFBundleExecutable'], 'math')

    def test_missing_linked_framework_preserves_original_ipa(self):
        with tempfile.TemporaryDirectory() as folder:
            ipa = Path(folder) / 'app.ipa'
            with zipfile.ZipFile(ipa, 'w') as z:
                z.writestr('Payload/Test.app/Info.plist', plistlib.dumps({'CFBundleExecutable': 'Test'}))
            original = ipa.read_bytes()
            # A missing framework must fail before replacing the source artifact.
            from unittest.mock import patch
            with patch('python_support.resource_files', return_value={}):
                with self.assertRaisesRegex(ValueError, 'did not embed'):
                    package(ipa, 'unused', 'unused', 'release_arm64')
            self.assertEqual(ipa.read_bytes(), original)
