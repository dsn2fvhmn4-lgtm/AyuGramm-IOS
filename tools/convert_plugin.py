"""Convert the reviewed Search+ file to the native .plugin ABI without executing it."""
import argparse
import hashlib
from pathlib import Path

SEARCH_PLUS_SHA256 = '802dd326787e3640f55f20ac5462539c03202184e540578a4531c693c2c3458a'


def convert(source: Path, output: Path):
    if source.suffix.lower() != '.plugin' or output.suffix.lower() != '.plugin':
        raise ValueError('Both input and output must use the .plugin extension')
    if source.resolve() == output.resolve():
        raise ValueError('Keep the original plugin; choose a different output path')
    if not 0 < source.stat().st_size <= 512 * 1024:
        raise ValueError('Plugin size must be between 1 byte and 512 KB')
    if hashlib.sha256(source.read_bytes()).hexdigest() != SEARCH_PLUS_SHA256:
        raise ValueError('No reviewed native adapter for this file/version. Android code was not executed.')
    adapter = Path(__file__).resolve().parents[1] / 'plugins/search_plus_ios.plugin'
    # Exclusive create protects an existing plugin from accidental replacement.
    with output.open('xb') as destination:
        destination.write(adapter.read_bytes())
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    try:
        print(convert(args.source, args.output))
    except (ValueError, OSError) as error:
        raise SystemExit(str(error))
