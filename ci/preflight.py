"""Cheap source/API checks before invoking the expensive full Telegram build."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re
import subprocess
import tempfile
import plistlib


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
    # These standalone sources use SDK frameworks only. Type-check their actual
    # implementations before the expensive full Telegram build.
    sdk_sources = [source / 'submodules/TelegramUI/Sources' / name for name in (
        'Chat/AyuMessageShotCanvas.swift', 'AyuStartupStorage.swift', 'AyuStartupFailureController.swift')]
    sdk_sources.append(source / 'submodules/Display/Source/AyuPluginAvatar.swift')
    sdk_sources.append(source / 'submodules/Display/Source/AyuChatColorPickerController.swift')
    sdk_sources.append(source / 'submodules/TelegramPresentationData/Sources/AyuAppIconCatalog.swift')
    sdk_sources.extend(source / 'submodules/SettingsUI/Sources' / name for name in (
        'AyuPreferencesHubController.swift', 'AyuAppIconPickerController.swift'))
    if any(path.exists() for path in sdk_sources):
        sdk = subprocess.check_output(['xcrun', '--sdk', 'iphonesimulator', '--show-sdk-path'], text=True).strip()
        for path in sdk_sources:
            if not path.exists():
                continue
            result = subprocess.run(['xcrun', 'swiftc', '-typecheck', '-swift-version', '5', '-warnings-as-errors',
                                     '-sdk', sdk, '-target', 'arm64-apple-ios15.0-simulator', str(path)], capture_output=True, text=True)
            if result.returncode:
                errors.append(f'{path.name} SDK type check:\n{result.stdout}{result.stderr}')
            else:
                print(f'PASS: actual {path.name} type-checked against the iOS Simulator SDK')
        # Model-only harness from real source, without Telegram network/database stubs.
        # It checks the actual plugin manager against UIKit and actual model signatures.
        manager = source / 'submodules/SettingsUI/Sources/AyuPluginManagerController.swift'
        if manager.exists():
            ayu = source / 'submodules/TelegramCore/Sources/AyuGram'
            models = [ayu / name for name in (
                'AyuPlugins.swift', 'AyuAndroidPluginConverter.swift', 'AyuCameraFlipPolicy.swift', 'AyuChatColorSettings.swift', 'AyuGhostModeSettings.swift', 'AyuAppearanceSettings.swift',
                'AyuMediaSendSettings.swift', 'AyuInterfaceSettings.swift', 'AyuMessageShotSettings.swift',
                'AyuHiddenMessagesSettings.swift', 'AyuReactionDisplaySettings.swift', 'AyuRegexSettings.swift')]
            with tempfile.TemporaryDirectory(prefix='ayu-plugin-sdk-') as directory:
                flags = ['xcrun', 'swiftc', '-swift-version', '5', '-warnings-as-errors',
                         '-sdk', sdk, '-target', 'arm64-apple-ios15.0-simulator']
                result = subprocess.run([*flags, '-emit-module', '-module-name', 'TelegramCore',
                                         '-emit-module-path', str(Path(directory) / 'TelegramCore.swiftmodule'),
                                         *map(str, models)], capture_output=True, text=True)
                if result.returncode:
                    errors.append(f'Actual plugin model SDK harness:\n{result.stdout}{result.stderr}')
                else:
                    result = subprocess.run([*flags, '-emit-module', '-module-name', 'Display',
                                             '-emit-module-path', str(Path(directory) / 'Display.swiftmodule'),
                                             str(source / 'submodules/Display/Source/AyuPluginAvatar.swift')], capture_output=True, text=True)
                    if result.returncode:
                        errors.append(f'Actual plugin avatar SDK harness:\n{result.stdout}{result.stderr}')
                    else:
                        result = subprocess.run([*flags, '-typecheck', '-I', directory, str(manager),
                                                 str(source / 'submodules/SettingsUI/Sources/AyuPluginDetailsController.swift'),
                                                 str(source / 'submodules/SettingsUI/Sources/AyuPreferencesHubController.swift'),
                                                 str(source / 'submodules/TelegramUI/Components/VideoMessageCameraScreen/Sources/AyuCameraFlipGestureRecognizer.swift')], capture_output=True, text=True)
                        if result.returncode:
                            errors.append(f'Actual plugin manager UIKit SDK check:\n{result.stdout}{result.stderr}')
                        else:
                            print('PASS: actual plugin manager checked against UIKit and actual model-only harness; full Telegram integration remains separate')
        # Compile just the actual artwork before starting the full Telegram target.
        icon_root = source / 'Telegram/Telegram-iOS'
        if (icon_root / 'AyuBlue.icon').exists():
            icon_names = ['Telegram'] + sorted(path.stem for path in icon_root.glob('Ayu*.icon'))
            alternate_args = [argument for name in icon_names[1:] for argument in ('--alternate-app-icon', name)]
            with tempfile.TemporaryDirectory(prefix='ayu-icon-sdk-') as directory:
                result = subprocess.run(['xcrun', 'actool', '--compile', directory,
                                         '--platform', 'iphoneos', '--minimum-deployment-target', '15.0',
                                         '--target-device', 'iphone', '--target-device', 'ipad',
                                         '--app-icon', 'Telegram', *alternate_args,
                                         '--output-partial-info-plist', str(Path(directory) / 'icons.plist'),
                                         *[str(icon_root / (name + '.icon')) for name in icon_names]],
                                        capture_output=True, text=True)
                if result.returncode:
                    errors.append(f'Icon Composer SDK compilation:\n{result.stdout}{result.stderr}')
                else:
                    compiled_icons = plistlib.loads((Path(directory) / 'icons.plist').read_bytes())
                    alternates = compiled_icons.get('CFBundleIcons', {}).get('CFBundleAlternateIcons', {})
                    if not set(icon_names[1:]).issubset(alternates):
                        errors.append('Icon Composer metadata is missing declared AyuGram alternate icons before the full build')
                    else:
                        print(f'PASS: {len(icon_names)} Icon Composer bundles and their metadata compiled before the full build')
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'PASS: {len(paths)} changed Swift sources parsed; UI import and Telegram API contracts checked. Full type checking still occurs during the native build.')


if __name__ == '__main__':
    main()
