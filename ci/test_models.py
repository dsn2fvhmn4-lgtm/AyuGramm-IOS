"""Run the actual AyuGram models through the pinned Postbox codec before the app build.

Only the standalone codec and MurMurHash32 are compiled. No database, SDK stubs,
copied encoder implementations or TelegramCore module build is involved.
"""
import argparse
from pathlib import Path
import platform
import subprocess
import tempfile


def run(source: Path):
    if platform.system() != 'Darwin':
        raise SystemExit('The actual Postbox host tests require the macOS build machine.')
    source = source.resolve()
    with tempfile.TemporaryDirectory(prefix='ayu-postbox-tests-') as directory:
        output = Path(directory)
        murmur = source / 'submodules/MurMurHash32'
        header = murmur / 'PublicHeaders/MurMurHash32/MurMurHash32.h'
        (output / 'module.modulemap').write_text(
            'module MurMurHash32 { header "' + str(header) + '" export * }\n', encoding='utf-8')
        subprocess.run(['xcrun', 'clang', '-fmodules', '-fobjc-arc',
                        '-I', str(murmur / 'PublicHeaders'), '-c',
                        str(murmur / 'Sources/MurMurHash32.m'), '-o', str(output / 'murmur.o')], check=True)
        postbox = source / 'submodules/Postbox/Sources'
        codec = [postbox / 'Coding.swift', *sorted((postbox / 'Utils/Encoder').glob('*.swift')),
                 *sorted((postbox / 'Utils/Decoder').glob('*.swift'))]
        subprocess.run(['xcrun', 'swiftc', '-swift-version', '5', '-emit-library', '-emit-module',
                        '-module-name', 'Postbox', '-I', str(output),
                        '-emit-module-path', str(output / 'Postbox.swiftmodule'),
                        *map(str, codec), str(output / 'murmur.o'),
                        '-o', str(output / 'libPostbox.dylib')], check=True)
        ayu = source / 'submodules/TelegramCore/Sources/AyuGram'
        models = [ayu / name for name in ('AyuGhostModeSettings.swift', 'AyuAppearanceSettings.swift', 'AyuMediaSendSettings.swift', 'AyuInterfaceSettings.swift', 'AyuMessageShotPolicy.swift', 'AyuRegexSettings.swift',
                                         'AyuArchiveFileStore.swift', 'AyuMessageHistoryState.swift')]
        subprocess.run(['xcrun', 'swiftc', '-swift-version', '5', '-warnings-as-errors',
                        '-D', 'AYU_POSTBOX_TESTS', '-I', str(output), '-L', str(output), '-lPostbox',
                        '-Xlinker', '-rpath', '-Xlinker', str(output),
                        *map(str, models), str(source / 'tools/ayu-tests/main.swift'),
                        '-o', str(output / 'ayu-tests')], check=True)
        subprocess.run([str(output / 'ayu-tests')], check=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    run(parser.parse_args().source)
