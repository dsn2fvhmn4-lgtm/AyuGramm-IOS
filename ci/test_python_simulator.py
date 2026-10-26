"""Run the actual embedded bridge/converter in an isolated iOS Simulator control app."""
import json
from pathlib import Path
import plistlib
import re
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
    [@"starting interpreter" writeToURL:[documents URLByAppendingPathComponent:@"stage.txt"] atomically:YES encoding:NSUTF8StringEncoding error:nil];
    AyuPythonBridgeObjC *bridge = [AyuPythonBridgeObjC new];
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
        NSString *failure = [bridge startWithPythonHome:home stdlibPath:stdlib
            dynloadPath:[stdlib stringByAppendingPathComponent:@"lib-dynload"]
            runtimePath:runtime dataDir:documents.path
            handler:^NSString *(NSString *request) { (void)request; return @"{\"ok\":false,\"error\":\"control has no native actions\"}"; }];
        [@"interpreter startup returned" writeToURL:[documents URLByAppendingPathComponent:@"stage.txt"] atomically:YES encoding:NSUTF8StringEncoding error:nil];
        // A different thread exercises GIL ownership across calls.
        dispatch_async(dispatch_get_main_queue(), ^{
            [@"converting on second thread" writeToURL:[documents URLByAppendingPathComponent:@"stage.txt"] atomically:YES encoding:NSUTF8StringEncoding error:nil];
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
    print('Control command: ' + ' '.join(args), flush=True)
    return subprocess.check_output(list(args), text=True, timeout=60).strip()


def run(source, runtime):
    listing = json.loads(command('xcrun', 'simctl', 'list', '-j'))
    runtimes = [r for r in listing['runtimes'] if r.get('isAvailable') and r['identifier'].startswith('com.apple.CoreSimulator.SimRuntime.iOS-')]
    if not runtimes:
        print('::notice::No iOS Simulator runtime installed; interpreter execution control was not run. SDK/model checks are separate.')
        return
    selected_runtime = sorted(runtimes, key=lambda r: tuple(int(p) for p in r['version'].split('.')))[-1]
    phones = [d for d in listing['devicetypes'] if d['name'].startswith('iPhone')]
    # CoreSimulator lists historical types as well as current ones; its list is
    # not ordered by runtime compatibility. Prefer types already paired with
    # this runtime, then try newer phones, rejecting incompatible pairs.
    paired = {d.get('deviceTypeIdentifier') for d in listing.get('devices', {}).get(selected_runtime['identifier'], []) if d.get('isAvailable')}
    def rank(phone):
        numbers = re.findall(r'\d+', phone['name'])
        preferred = {'iPhone 17 Pro': 4, 'iPhone 17': 3, 'iPhone 16 Pro': 2, 'iPhone 16': 1}
        return (preferred.get(phone['name'], 0), int(numbers[0]) if numbers else 0, phone['identifier'] in paired)
    device = None
    for phone in sorted(phones, key=rank, reverse=True):
        created = subprocess.run(['xcrun', 'simctl', 'create', 'AyuPython-converter-control', phone['identifier'], selected_runtime['identifier']], capture_output=True, text=True, timeout=30)
        if created.returncode == 0:
            device = created.stdout.strip()
            print('Interpreter control device: ' + phone['name'] + ' / ' + selected_runtime['version'], flush=True)
            break
        if 'Incompatible device' not in created.stderr:
            raise RuntimeError('Simulator creation failed: ' + created.stderr)
    if device is None:
        raise RuntimeError('No compatible iPhone type for the available iOS Simulator runtime')
    try:
        print('Booting interpreter control device', flush=True)
        subprocess.run(['xcrun', 'simctl', 'boot', device], check=True, timeout=150)
        subprocess.run(['xcrun', 'simctl', 'bootstatus', device, '-b'], check=True, timeout=60)
        print('Compiling interpreter control application', flush=True)
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
                            '-o', str(app / 'Control')], check=True, timeout=180)
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
            subprocess.run(['codesign', '--force', '--deep', '--sign', '-', str(app)], check=True, timeout=60)
            print('Installing interpreter control application', flush=True)
            subprocess.run(['xcrun', 'simctl', 'install', device, str(app)], check=True, timeout=60)
            container = Path(command('xcrun', 'simctl', 'get_app_container', device, 'one.ayugram.converter.control', 'data'))
            print('Launching interpreter control application', flush=True)
            console = folder / 'control-console.log'
            with console.open('wb') as output:
                launch = subprocess.Popen(['xcrun', 'simctl', 'launch', '--console', device, 'one.ayugram.converter.control'], stdout=output, stderr=subprocess.STDOUT)
            result_path = container / 'Documents/result.json'
            deadline = time.monotonic() + 60
            while not result_path.exists() and time.monotonic() < deadline:
                if launch.poll() is not None: break
                time.sleep(1)
            try:
                subprocess.run(['xcrun', 'simctl', 'terminate', device, 'one.ayugram.converter.control'], check=False, timeout=15)
            except subprocess.TimeoutExpired:
                pass
            if launch.poll() is None:
                launch.terminate()
            if not result_path.exists():
                stage = container / 'Documents/stage.txt'
                print('Control startup stage: ' + (stage.read_text(encoding='utf-8') if stage.exists() else 'application delegate not reached'), flush=True)
                print(console.read_text(encoding='utf-8', errors='replace')[-16000:], flush=True)
                raise RuntimeError('Python interpreter control did not return a conversion result')
            result = json.loads(result_path.read_text(encoding='utf-8'))
            if not result.get('ok'): raise RuntimeError('Real iOS Python startup/conversion failed: ' + str(result.get('error')))
            manifest = result['result']
            if manifest.get('apiVersion') != 6 or [i['op'] for i in manifest['actions'][0]['program']['instructions']] != ['strip', 'upper']:
                raise RuntimeError('Real iOS converter returned an unexpected native program')
            print('PASS: actual embedded CPython starts and converts source to API 6 inside the iOS Simulator; GIL thread transition checked')
    finally:
        for operation in ('shutdown', 'delete'):
            try:
                subprocess.run(['xcrun', 'simctl', operation, device], check=False, timeout=15)
            except subprocess.TimeoutExpired:
                print('::warning::Simulator control cleanup timed out: ' + operation, flush=True)


if __name__ == '__main__':
    import sys
    run(Path(sys.argv[1]), Path(__file__).resolve().parents[1] / 'runtime')
