"""Exercise real stdlib/framework packaging; this creates a temporary control, not an app build."""
from pathlib import Path
import plistlib
import tempfile
import zipfile
import python_support


def run(source, cache, runtime):
    source = Path(source)
    archive = python_support.archive_path(cache)
    with tempfile.TemporaryDirectory(prefix='ayu-python-package-check-') as folder:
        ipa = Path(folder) / 'PackagingControl.ipa'
        with zipfile.ZipFile(ipa, 'w') as output:
            output.writestr('Payload/Control.app/Info.plist', plistlib.dumps({'CFBundleExecutable': 'Control'}))
            output.writestr('Payload/Control.app/Control', b'Packaging control only; not an executable app')
            output.writestr('Payload/Control.app/Frameworks/Python.framework/Python',
                            (source / 'third-party/ayu-python/Python.framework/Python').read_bytes())
        report = python_support.package(ipa, archive, runtime, 'debug_sim_arm64')
        with zipfile.ZipFile(ipa) as result:
            if result.testzip() is not None or any(name.endswith('.so') for name in result.namelist()):
                raise ValueError('Python package integrity/module conversion check failed')
        print('PASS: real Python stdlib packaging and framework signatures; '
              + str(report['extension_frameworks']) + ' extension frameworks (packaging control only)')
