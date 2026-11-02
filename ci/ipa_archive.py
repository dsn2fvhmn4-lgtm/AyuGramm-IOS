"""Lossless, bounded-memory IPA compression. Bundle files are never stripped or edited."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import zipfile

COMPRESSION_LEVEL = 9
COPY_BUFFER_SIZE = 1024 * 1024


def copy_entry(source, output, item):
    """Preserve ZIP metadata and stream even the largest framework in 1 MiB chunks."""
    target = copy.copy(item)
    target.compress_type = zipfile.ZIP_STORED if item.is_dir() else zipfile.ZIP_DEFLATED
    # ZipInfo.compress_level is public only from Python 3.13 onwards. CI also uses 3.12.
    target._compresslevel = COMPRESSION_LEVEL
    with source.open(item) as reader, output.open(target, 'w') as writer:
        shutil.copyfileobj(reader, writer, length=COPY_BUFFER_SIZE)


def content_hashes(archive):
    result = {}
    for item in archive.infolist():
        if item.filename in result:
            raise ValueError('Duplicate IPA entry: ' + item.filename)
        digest = hashlib.sha256()
        with archive.open(item) as source:
            for chunk in iter(lambda: source.read(COPY_BUFFER_SIZE), b''):
                digest.update(chunk)
        result[item.filename] = digest.hexdigest()
    return result


def optimize(source, destination):
    """Write a separate IPA, verify every file, and publish it with an atomic rename."""
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve():
        raise ValueError('Choose a separate output path; the original IPA is preserved')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.ayu-ipa-', dir=destination.parent) as folder:
        temporary = Path(folder) / 'optimized.ipa'
        with zipfile.ZipFile(source) as original:
            hashes = content_hashes(original)
            with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED,
                                 compresslevel=COMPRESSION_LEVEL) as output:
                output.comment = original.comment
                for item in original.infolist():
                    copy_entry(original, output, item)
        with zipfile.ZipFile(temporary) as output:
            if content_hashes(output) != hashes:
                raise ValueError('Optimized IPA differs from the original bundle')
        # Some IPAs were already compressed by a stronger compressor. Never grow them.
        if temporary.stat().st_size >= source.stat().st_size:
            shutil.copyfile(source, temporary)
        report = {'original_bytes': source.stat().st_size,
                  'optimized_bytes': temporary.stat().st_size,
                  'saved_bytes': source.stat().st_size - temporary.stat().st_size,
                  'verified_entries': len(hashes), 'bundle_contents_identical': True}
        temporary.replace(destination)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    print(json.dumps(optimize(args.source, args.destination), indent=2))
