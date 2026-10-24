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
    if re.search(r'\.ayuVisibleMessageReactions(?:AndPeers)?\s*\(', source) and 'import AccountContext' not in source:
        errors.append('AyuGram reaction display helpers require AccountContext')
    return errors


def reaction_dependency_errors(source_file):
    text = source_file.read_text(encoding='utf-8')
    if not re.search(r'\.ayuVisibleMessageReactions(?:AndPeers)?\s*\(', text):
        return []
    for parent in source_file.parents:
        build = parent / 'BUILD'
        if build.is_file():
            if '//submodules/AccountContext' not in build.read_text(encoding='utf-8'):
                return ['AyuGram reaction display helpers require a direct AccountContext Bazel dependency']
            return []
    return ['No BUILD file found for AyuGram reaction display helpers']


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
        for error in reaction_dependency_errors(source / path):
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
    # This source deliberately uses only UIKit/ImageIO, so the actual renderer and
    # preview can be type-checked against the pinned Xcode SDK before Telegram builds.
    canvas = source / 'submodules/TelegramUI/Sources/Chat/AyuMessageShotCanvas.swift'
    if canvas.exists():
        sdk = subprocess.check_output(['xcrun', '--sdk', 'iphonesimulator', '--show-sdk-path'], text=True).strip()
        result = subprocess.run(['xcrun', 'swiftc', '-typecheck', '-swift-version', '5', '-warnings-as-errors',
                                 '-sdk', sdk, '-target', 'arm64-apple-ios15.0-simulator', str(canvas)], capture_output=True, text=True)
        if result.returncode:
            errors.append(f'MessageShot UIKit/ImageIO SDK type check:\n{result.stdout}{result.stderr}')
        else:
            print('PASS: actual MessageShot canvas/preview source type-checked against the iOS Simulator SDK')
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'PASS: {len(paths)} changed Swift sources parsed; UI import and Telegram API contracts checked. Full type checking still occurs during the native build.')


if __name__ == '__main__':
    main()
