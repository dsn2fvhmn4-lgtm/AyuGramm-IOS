"""Convert reviewed Search+ or complete Android hook templates to native .plugin without execution."""
import argparse
import hashlib
import json
from plugin_patterns import compile_source
from pathlib import Path

CHAT_COLORS_SHA256 = 'a7217c0cc672615e3558b8f3391b522f7e031bc0900a84315b4eb4f53ece8de5'

CAMERA_FLIP_SHA256 = '61136472b21e9ac23fc32883e137173ef1a85314d2cc6c63719be003555f1e98'

SEARCH_PLUS_SHA256 = '802dd326787e3640f55f20ac5462539c03202184e540578a4531c693c2c3458a'


def convert(source: Path, output: Path):
    if source.suffix.lower() != '.plugin' or output.suffix.lower() != '.plugin':
        raise ValueError('Both input and output must use the .plugin extension')
    if source.resolve() == output.resolve():
        raise ValueError('Keep the original plugin; choose a different output path')
    if not 0 < source.stat().st_size <= 512 * 1024:
        raise ValueError('Plugin size must be between 1 byte and 512 KB')
    data = source.read_bytes()
    if hashlib.sha256(data).hexdigest() == SEARCH_PLUS_SHA256:
        output_data = (Path(__file__).resolve().parents[1] / 'plugins/search_plus_ios.plugin').read_bytes()
    elif hashlib.sha256(data).hexdigest() == CAMERA_FLIP_SHA256:
        output_data = (Path(__file__).resolve().parents[1] / 'plugins/camera_flip_ios.plugin').read_bytes()
    elif hashlib.sha256(data).hexdigest() == CHAT_COLORS_SHA256:
        output_data = (Path(__file__).resolve().parents[1] / 'plugins/chat_colors_ios.plugin').read_bytes()
    else:
        output_data = (json.dumps(compile_source(data), ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    # Exclusive create protects an existing plugin from accidental replacement.
    with output.open('xb') as destination:
        destination.write(output_data)
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
