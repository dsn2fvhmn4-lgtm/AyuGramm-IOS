from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ipa_archive import COPY_BUFFER_SIZE, optimize


class IPAArchiveTests(unittest.TestCase):
    def test_lossless_compression_preserves_bundle_and_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            source, destination = Path(folder) / 'original.ipa', Path(folder) / 'small.ipa'
            contents = {
                'Payload/Test.app/Test': b'Mach-O fixture' * 10000,
                'Payload/Test.app/_CodeSignature/CodeResources': b'signed resources',
                'Payload/Test.app/Frameworks/F.framework/F': b'framework' * 10000,
                'Payload/Test.app/empty': b'',
                'Payload/Test.app/link': b'Test',
            }
            with zipfile.ZipFile(source, 'w') as archive:
                archive.comment = b'archive comment'
                for name, data in contents.items():
                    item = zipfile.ZipInfo(name, date_time=(2026, 11, 2, 12, 0, 0))
                    item.create_system = 3
                    mode = stat.S_IFLNK | 0o777 if name.endswith('/link') else stat.S_IFREG | 0o755
                    item.external_attr = mode << 16
                    item.comment = b'entry comment'
                    archive.writestr(item, data)
            original = source.read_bytes()
            real_open = zipfile.ZipFile.open
            read_sizes = []

            class Reader:
                def __init__(self, stream): self.stream = stream
                def __enter__(self): return self
                def __exit__(self, *args): self.stream.close()
                def read(self, size=-1):
                    read_sizes.append(size)
                    return self.stream.read(size)

            def opened(archive, name, mode='r', **kwargs):
                stream = real_open(archive, name, mode, **kwargs)
                return Reader(stream) if mode == 'r' else stream

            with patch.object(zipfile.ZipFile, 'open', opened):
                report = optimize(source, destination)
            self.assertTrue(all(0 < n <= COPY_BUFFER_SIZE for n in read_sizes))
            self.assertEqual(source.read_bytes(), original)
            self.assertGreater(report['saved_bytes'], 0)
            self.assertEqual(report['verified_entries'], len(contents))
            with zipfile.ZipFile(source) as before, zipfile.ZipFile(destination) as after:
                self.assertEqual(after.comment, before.comment)
                self.assertEqual(after.namelist(), before.namelist())
                for old in before.infolist():
                    new = after.getinfo(old.filename)
                    self.assertEqual(after.read(new), contents[old.filename])
                    for attr in ('external_attr', 'create_system', 'date_time', 'comment'):
                        self.assertEqual(getattr(old, attr), getattr(new, attr))

    def test_failure_leaves_both_paths_untouched(self):
        with tempfile.TemporaryDirectory() as folder:
            source, destination = Path(folder) / 'original.ipa', Path(folder) / 'small.ipa'
            with zipfile.ZipFile(source, 'w') as archive: archive.writestr('file', b'contents')
            original = source.read_bytes()
            destination.write_bytes(b'previous output')
            with patch('ipa_archive.copy_entry', side_effect=OSError('disk full')):
                with self.assertRaisesRegex(OSError, 'disk full'): optimize(source, destination)
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(destination.read_bytes(), b'previous output')
            self.assertEqual(len(list(Path(folder).iterdir())), 2)

    def test_never_overwrites_source_or_grows_already_compressed_ipa(self):
        with tempfile.TemporaryDirectory() as folder:
            source, destination = Path(folder) / 'original.ipa', Path(folder) / 'small.ipa'
            with zipfile.ZipFile(source, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
                archive.writestr('file', b'compressible' * 100)
            with self.assertRaises(ValueError): optimize(source, source)
            report = optimize(source, destination)
            self.assertGreaterEqual(report['saved_bytes'], 0)
