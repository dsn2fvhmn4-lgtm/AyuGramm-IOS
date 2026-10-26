"""Pinned CPython framework preparation and unsigned IPA resource packaging."""
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import plistlib
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile

VERSION = '3.13-b15'
SHA256 = '80175765a31babe43b0910395cf86ba4e8412adf1902b069d55b74d523ecc5d1'
URL = 'https://github.com/beeware/Python-Apple-support/releases/download/3.13-b15/Python-3.13-iOS-support.b15.tar.gz'


def archive_path(cache):
    cache = Path(cache)
    cache.mkdir(parents=True, exist_ok=True)
    archive = cache / 'Python-3.13-iOS-support.b15.tar.gz'
    if not archive.exists():
        temporary = archive.with_suffix('.download')
        with urllib.request.urlopen(URL, timeout=120) as response, temporary.open('wb') as output:
            shutil.copyfileobj(response, output)
        if hashlib.sha256(temporary.read_bytes()).hexdigest() != SHA256:
            temporary.unlink()
            raise ValueError('Python support archive SHA-256 mismatch')
        temporary.replace(archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
        raise ValueError('Cached Python support archive SHA-256 mismatch')
    return archive


def slice_name(configuration):
    return 'ios-arm64_x86_64-simulator' if configuration == 'debug_sim_arm64' else 'ios-arm64'


def prepare(source, cache, configuration):
    archive = archive_path(cache)
    target = Path(source) / 'third-party/ayu-python'
    target.mkdir(parents=True, exist_ok=True)
    prefix = 'Python.xcframework/' + slice_name(configuration) + '/'
    with tarfile.open(archive) as bundle:
        for item in bundle:
            if item.isfile() and item.name.startswith(prefix + 'Python.framework/'):
                relative = PurePosixPath(item.name[len(prefix):])
                if '..' in relative.parts:
                    raise ValueError('Unexpected framework archive path')
                destination = target / str(relative)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(bundle.extractfile(item).read())
    if not (target / 'Python.framework/Python').is_file():
        raise ValueError('Python device framework is missing')
    (target / 'BUILD').write_text('''load("@build_bazel_rules_apple//apple:apple.bzl", "apple_dynamic_framework_import")
apple_dynamic_framework_import(
    name = "Python",
    framework_imports = glob(["Python.framework/**"]),
    visibility = ["//visibility:public"],
)
''', encoding='utf-8')
    return archive


def resource_files(archive, runtime, configuration):
    """Match BeeWare's lib + lib-arm64 layout, including signed-framework markers."""
    files = {}
    prefixes = [('Python.xcframework/lib/', 'python/lib/'),
                ('Python.xcframework/' + slice_name(configuration) + '/lib-arm64/', 'python/lib/')]
    with tarfile.open(archive) as bundle:
        for prefix, destination in prefixes:
            for item in bundle.getmembers():
                if not item.isfile() or not item.name.startswith(prefix):
                    continue
                relative = PurePosixPath(item.name[len(prefix):])
                if '..' in relative.parts:
                    raise ValueError('Unexpected standard-library path')
                if any(part in ('test', 'tests', '__pycache__', 'idlelib', 'tkinter', 'ensurepip') for part in relative.parts):
                    continue
                name = destination + relative.as_posix()
                contents = bundle.extractfile(item).read()
                if name.endswith('.so'):
                    # PEP 730: extension modules are frameworks, not unsigned .so resources.
                    module = relative.name.split('.')[0]
                    framework = 'Frameworks/' + module + '.framework/'
                    binary = framework + module
                    marker = name[:-3] + '.fwork'
                    files[binary] = contents
                    files[framework + module + '.origin'] = (marker + '\n').encode()
                    files[marker] = (binary + '\n').encode()
                    files[framework + 'Info.plist'] = plistlib.dumps({
                        'CFBundleExecutable': module, 'CFBundleIdentifier': 'one.ayugram.python.' + module.replace('_', '-'),
                        'CFBundleName': module, 'CFBundlePackageType': 'FMWK', 'CFBundleVersion': '1',
                        'CFBundleShortVersionString': '1.0', 'MinimumOSVersion': '15.0',
                        'CFBundleSupportedPlatforms': ['iPhoneSimulator' if configuration == 'debug_sim_arm64' else 'iPhoneOS'],
                    })
                else:
                    files[name] = contents
    runtime = Path(runtime)
    for path in sorted((runtime / 'python').rglob('*.py')):
        files['ayu-python-runtime/python/' + path.relative_to(runtime / 'python').as_posix()] = path.read_bytes()
    files['ayu-python-runtime/hook_map.json'] = (runtime / 'hook_map.json').read_bytes()
    files['ayu-python-runtime/build.json'] = json.dumps({'pythonSupport': VERSION, 'sha256': SHA256, 'converter': 2}).encode()
    for name in ['python/lib/python3.13/encodings/__init__.py', 'ayu-python-runtime/python/_ayu_converter.py']:
        if name not in files:
            raise ValueError('Required Python resource is missing: ' + name)
    return files


def package(ipa, archive, runtime, configuration):
    ipa = Path(ipa)
    files = resource_files(archive, runtime, configuration)
    with zipfile.ZipFile(ipa) as source:
        prefix = next(name[:-len('Info.plist')] for name in source.namelist()
                      if name.startswith('Payload/') and name.count('/') == 2 and name.endswith('.app/Info.plist'))
        if prefix + 'Frameworks/Python.framework/Python' not in source.namelist():
            raise ValueError('Bazel did not embed the linked Python framework')
    # This runs only for the unsigned compilation workflow. Sign the new binary
    # frameworks ad hoc; the final installer must re-sign all nested frameworks.
    if sys.platform == 'darwin':
        with tempfile.TemporaryDirectory(prefix='ayu-python-sign-') as folder:
            stage = Path(folder)
            for name, contents in files.items():
                if name.startswith('Frameworks/'):
                    path = stage / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(contents)
            for framework in sorted((stage / 'Frameworks').glob('*.framework')):
                subprocess.run(['codesign', '--force', '--sign', '-', '--timestamp=none', str(framework)], check=True)
            for path in (stage / 'Frameworks').rglob('*'):
                if path.is_file():
                    files[path.relative_to(stage).as_posix()] = path.read_bytes()
    destination = ipa.with_suffix('.python.ipa')
    with zipfile.ZipFile(ipa) as source, zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as output:
        for item in source.infolist():
            relative = item.filename[len(prefix):] if item.filename.startswith(prefix) else ''
            if relative in files or relative.startswith('_CodeSignature/'):
                continue
            output.writestr(item, source.read(item.filename))
        for name, contents in sorted(files.items()):
            output.writestr(prefix + name, contents)
    with zipfile.ZipFile(destination) as result:
        if result.testzip() is not None:
            raise ValueError('Repacked Python IPA failed ZIP integrity validation')
    destination.replace(ipa)
    return {'support': VERSION, 'archive_sha256': SHA256,
            'extension_frameworks': sum(name.endswith('.origin') for name in files), 'converter': 2}
