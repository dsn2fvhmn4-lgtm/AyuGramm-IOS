"""Run the actual embedded bridge/converter in an isolated iOS Simulator control app."""
import json
from pathlib import Path
import plistlib
import shutil
import subprocess
import tempfile
import time
import zipfile

import python_support


MAIN = r'''
#import <UIKit/UIKit.h>
#import "AyuPythonBridgeObjC.h"

@interface ControlDelegate : UIResponder <UIApplicationDelegate>
@property(nonatomic, strong) UIWindow *window;
@end

@implementation ControlDelegate
- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)options {
    (void)application; (void)options;
    self.window = [[UIWindow alloc] initWithFrame:UIScreen.mainScreen.bounds];
    self.window.rootViewController = [UIViewController new];
    [self.window makeKeyAndVisible];
    NSString *root = NSBundle.mainBundle.resourcePath;
    NSString *home = [root stringByAppendingPathComponent:@"python"];
    NSString *stdlib = [home stringByAppendingPathComponent:@"lib/python3.13"];
    NSString *runtime = [root stringByAppendingPathComponent:@"ayu-python-runtime/python"];
    NSURL *documents = [NSFileManager.defaultManager URLsForDirectory:NSDocumentDirectory inDomains:NSUserDomainMask].firstObject;
    [NSFileManager.defaultManager createDirectoryAtURL:documents withIntermediateDirectories:YES attributes:nil error:nil];
    AyuPythonBridgeObjC *bridge = [AyuPythonBridgeObjC new];
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
        NSString *failure = [bridge startWithPythonHome:home stdlibPath:stdlib
            dynloadPath:[stdlib stringByAppendingPathComponent:@"lib-dynload"]
            runtimePath:runtime dataDir:documents.path
            handler:^NSString *(NSString *request) { (void)request; return @"{\"ok\":false,\"error\":\"control has no native actions\"}"; }];
        // A different thread exercises GIL ownership across calls.
        dispatch_async(dispatch_get_main_queue(), ^{
            NSString *response;
            if (failure != nil) {
                NSData *data = [NSJSONSerialization dataWithJSONObject:@{@"ok": @NO, @"error": failure} options:0 error:nil];
                response = [[NSString alloc] initWithData:data encoding:NSUTF8StringEncoding];
            } else {
                NSString *source = @"from base_plugin import BasePlugin, HookResult, HookStrategy\n__id__='sim_control'\n__name__='Simulator control'\nclass Control(BasePlugin):\n def on_plugin_load(self):\n  self.add_on_send_message_hook()\n def on_send_message_hook(self, account, params):\n  params.message=params.message.strip().upper()\n  return HookResult(strategy=HookStrategy.MODIFY, params=params)\n";
                NSData *request = [NSJSONSerialization dataWithJSONObject:@{@"op": @"convert", @"args": @{@"source": source}} options:0 error:nil];
                response = [bridge call:[[NSString alloc] initWithData:request encoding:NSUTF8StringEncoding]];
            }
            [response writeToURL:[documents URLByAppendingPathComponent:@"result.json"] atomically:YES encoding:NSUTF8StringEncoding error:nil];
        });
    });
    return YES;
}
@end

int main(int argc, char **argv) {
    @autoreleasepool { return UIApplicationMain(argc, argv, nil, NSStringFromClass(ControlDelegate.class)); }
}
'''


def command(*args):
    return subprocess.check_output(list(args), text=True).strip()


def run(source, runtime):
    listing = json.loads(command('xcrun', 'simctl', 'list', '-j'))
    runtimes = [r for r in listing['runtimes'] if r.get('isAvailable') and r['identifier'].startswith('com.apple.CoreSimulator.SimRuntime.iOS-')]
    if not runtimes:
        print('::notice::No iOS Simulator runtime installed; interpreter execution control was not run. SDK/model checks are separate.')
        return
    selected_runtime = sorted(runtimes, key=lambda r: tuple(int(p) for p in r['version'].split('.')))[-1]
    phones = [d for d in listing['devicetypes'] if d['name'].startswith('iPhone')]
    phone = phones[-1]
    device = command('xcrun', 'simctl', 'create', 'AyuPython-converter-control', phone['identifier'], selected_runtime['identifier'])
    try:
        subprocess.run(['xcrun', 'simctl', 'boot', device], check=True)
        subprocess.run(['xcrun', 'simctl', 'bootstatus', device, '-b'], check=True, timeout=180)
        source = Path(source)
        with tempfile.TemporaryDirectory(prefix='ayu-python-simulator-') as folder:
            folder = Path(folder)
            app = folder / 'Payload/Control.app'
            app.mkdir(parents=True)
            (app / 'Info.plist').write_bytes(plistlib.dumps({
                'CFBundleIdentifier': 'one.ayugram.converter.control', 'CFBundleExecutable': 'Control',
                'CFBundlePackageType': 'APPL', 'CFBundleVersion': '1', 'CFBundleShortVersionString': '1.0',
                'MinimumOSVersion': '15.0', 'CFBundleSupportedPlatforms': ['iPhoneSimulator'],
                'LSRequiresIPhoneOS': True,
            }))
            bridge = source / 'submodules/AyuPythonBridge/Sources'
            framework = source / 'third-party/ayu-python'
            main = folder / 'main.m'
            main.write_text(MAIN, encoding='utf-8')
            sdk = command('xcrun', '--sdk', 'iphonesimulator', '--show-sdk-path')
            subprocess.run(['xcrun', 'clang', '-fobjc-arc', '-fmodules', '-isysroot', sdk,
                            '-target', 'arm64-apple-ios15.0-simulator', '-I', str(bridge), '-F', str(framework),
                            '-framework', 'UIKit', '-framework', 'Foundation', '-framework', 'Python',
                            '-Wl,-rpath,@executable_path/Frameworks', str(main), str(bridge / 'AyuPythonBridgeObjC.m'),
                            '-o', str(app / 'Control')], check=True)
            shutil.copytree(framework / 'Python.framework', app / 'Frameworks/Python.framework')
            archive = folder / 'Control.ipa'
            with zipfile.ZipFile(archive, 'w') as output:
                for path in app.rglob('*'):
                    if path.is_file(): output.write(path, path.relative_to(folder).as_posix())
            cache = Path(__import__('os').environ.get('RUNNER_TEMP', '/tmp')) / 'ayu-python-support'
            python_support.package(archive, python_support.archive_path(cache), runtime, 'debug_sim_arm64')
            with zipfile.ZipFile(archive) as bundle:
                for item in bundle.infolist():
                    if item.is_dir(): continue
                    target = folder / item.filename
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(bundle.read(item))
                    target.chmod((item.external_attr >> 16) & 0o777 or 0o644)
            (app / 'Control').chmod(0o755)
            subprocess.run(['codesign', '--force', '--deep', '--sign', '-', str(app)], check=True)
            subprocess.run(['xcrun', 'simctl', 'install', device, str(app)], check=True)
            container = Path(command('xcrun', 'simctl', 'get_app_container', device, 'one.ayugram.converter.control', 'data'))
            subprocess.run(['xcrun', 'simctl', 'launch', device, 'one.ayugram.converter.control'], check=True)
            result_path = container / 'Documents/result.json'
            deadline = time.monotonic() + 60
            while not result_path.exists() and time.monotonic() < deadline:
                time.sleep(1)
            if not result_path.exists(): raise RuntimeError('Python interpreter control produced no result within 60 seconds')
            result = json.loads(result_path.read_text(encoding='utf-8'))
            if not result.get('ok'): raise RuntimeError('Real iOS Python startup/conversion failed: ' + str(result.get('error')))
            manifest = result['result']
            if manifest.get('apiVersion') != 6 or [i['op'] for i in manifest['actions'][0]['program']['instructions']] != ['strip', 'upper']:
                raise RuntimeError('Real iOS converter returned an unexpected native program')
            print('PASS: actual embedded CPython starts and converts source to API 6 inside the iOS Simulator; GIL thread transition checked')
    finally:
        subprocess.run(['xcrun', 'simctl', 'shutdown', device], check=False)
        subprocess.run(['xcrun', 'simctl', 'delete', device], check=False)


if __name__ == '__main__':
    import sys
    run(Path(sys.argv[1]), Path(__file__).resolve().parents[1] / 'runtime')
