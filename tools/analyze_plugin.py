"""Static dependency inventory for Android .plugin source. Never loads plugin code."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

CHAT_COLORS_SHA256 = 'a7217c0cc672615e3558b8f3391b522f7e031bc0900a84315b4eb4f53ece8de5'
CAMERA_SHA256 = '61136472b21e9ac23fc32883e137173ef1a85314d2cc6c63719be003555f1e98'
ARCADE_SHA256 = '421911448e6fe62b3292b43b8593ebb24056b238278bab002576381d541238bc'
UNLIM_ACCOUNTS_SHA256 = '6c5e2f697da4d87b0409841d96dd9bf69f224073c44b555c6fd9de782c70d40f'
REVIEWED_STATUS = {
    CAMERA_SHA256: 'Reviewed native Camera Flip adapter in development source; macOS build and device tests pending',
    CHAT_COLORS_SHA256: 'Reviewed native Chat Colors adapter in development source; macOS build and device tests pending',
    ARCADE_SHA256: 'Reviewed native Arcade Games adapter (web view games, chat commands) in development source; device tests pending',
    UNLIM_ACCOUNTS_SHA256: 'Reviewed native Unlim Accounts adapter (client account limit) in development source; device tests pending',
}


def analyze(source: Path):
    size = source.stat().st_size
    if not 0 < size <= 8 * 1024 * 1024:
        raise ValueError('Analysis limit is 8 MB')
    data = source.read_bytes()
    tree = ast.parse(data.decode('utf-8-sig'), filename=source.name)
    metadata = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id in {'__id__', '__name__', '__author__', '__version__', '__description__', '__app_version__', '__min_version__', '__sdk_version__', '__requirements__'}:
            try:
                value = ast.literal_eval(node.value)
                if isinstance(value, str) and len(value) <= 2048 or isinstance(value, list) and all(isinstance(v, str) and len(v) <= 128 for v in value):
                    metadata[node.targets[0].id] = value
            except (ValueError, TypeError):
                pass
    modules, hooks, java_classes, urls = set(), set(), set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(item.name for item in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.add('.' * node.level + (node.module or ''))
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {'hook_method', 'hook_all_methods', 'add_on_send_message_hook', 'add_menu_item', 'get_setting', 'set_setting'}:
                hooks.add(node.func.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and len(node.value) <= 2048:
            if node.value.startswith(('android.', 'org.telegram.', 'java.', 'dalvik.', 'com.rezolve.')):
                java_classes.add(node.value)
            if node.value.startswith(('https://', 'http://')) and urlsplit(node.value).hostname:
                urls.add(node.value)
    embedded = all(marker in data for marker in [b'__DEX_BEGIN__', b'__NATIVE_BEGIN__'])
    bridges = []
    if any(m.startswith(('android.', 'org.telegram.', 'java', 'hook_utils')) for m in modules) or java_classes:
        bridges.append('Android/Java classes and method hooks need native iOS mappings')
    if any(m.startswith(('ui.settings', 'ui.alert', 'ui.bulletin')) for m in modules):
        bridges.append('Native settings, dialogs or status UI')
    if 'add_menu_item' in hooks:
        bridges.append('Native menu registration and cleanup')
    if 'get_setting' in hooks or 'set_setting' in hooks:
        bridges.append('Per-account plugin settings/storage')
    if 'threading' in modules or 'file_utils' in modules:
        bridges.append('Scheduling or local media/file lifecycle')
    if any('webkit' in c.lower() or 'webview' in c.lower() for c in java_classes):
        bridges.append('Native web view lifecycle and website behavior')
    if embedded:
        bridges.append('Source references embedded Android DEX/JNI payloads; native iOS mapping required')
    digest = hashlib.sha256(data).hexdigest()
    return dict(file=source.name, bytes=size, sha256=digest, metadata=metadata,
                imports=sorted(modules), sdkCalls=sorted(hooks), javaClasses=sorted(java_classes),
                externalURLs=sorted(urls), embeddedAndroidRuntimeMarkers=embedded,
                withinCurrentImportLimit=size <= 4 * 1024 * 1024,
                requiredBridges=bridges,
                status=REVIEWED_STATUS.get(digest, 'No complete native adapter implemented'),
                analysisScope='Static dependency inventory only. No source or embedded binary was executed. This is not a compatibility test.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sources', nargs='+', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = json.dumps([analyze(path) for path in args.sources], ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.write_text(result, encoding='utf-8')
    else:
        print(result, end='')
