"""Cheap source/API checks before invoking the expensive full Telegram build."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re
import subprocess


def contract_errors(source):
    errors = []
    if re.search(r'textAlertController\s*\(\s*context:', source) and 'import PresentationDataUtils' not in source:
        errors.append('textAlertController(context:) requires PresentationDataUtils')
    if 'stringWithAppliedEntities(' in source and 'import TextFormat' not in source:
        errors.append('stringWithAppliedEntities requires TextFormat')
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    source = args.source.resolve()
    paths = set()
    for arguments in (['diff', '--name-only', '-z', 'HEAD'], ['ls-files', '--others', '--exclude-standard', '-z']):
        output = subprocess.check_output(['git', *arguments], cwd=source)
        paths.update(path.decode('utf-8') for path in output.split(b'\0') if path.endswith(b'.swift'))
    errors = []
    for path in sorted(paths):
        for error in contract_errors((source / path).read_text(encoding='utf-8')):
            errors.append(f'{path}: {error}')
    scheme = (source / 'submodules/TelegramApi/swift_scheme.tl').read_text(encoding='utf-8')
    for method in ('sendMessage', 'sendMedia', 'sendMultiMedia', 'forwardMessages'):
        line = next((line for line in scheme.splitlines() if line.startswith(f'messages.{method}#')), '')
        if 'silent:flags.5?true' not in line:
            errors.append(f'Telegram API silent flag changed for messages.{method}')

    def parse(path):
        result = subprocess.run(['xcrun', 'swiftc', '-frontend', '-parse', str(source / path)], capture_output=True, text=True)
        return result.returncode, result.stdout + result.stderr

    with ThreadPoolExecutor(max_workers=2) as executor:
        for path, (code, output) in zip(sorted(paths), executor.map(parse, sorted(paths))):
            if code:
                errors.append(f'{path}:\n{output}')
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'PASS: {len(paths)} changed Swift sources parsed; UI import and Telegram API contracts checked. Full type checking still occurs during the native build.')


if __name__ == '__main__':
    main()
