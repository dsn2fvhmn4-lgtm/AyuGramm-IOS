"""Run the real settings snapshots in the pinned iOS simulator; never build an IPA."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import python_support
from build_logging import run_logged_build

parser = argparse.ArgumentParser()
parser.add_argument("source", type=Path)
args = parser.parse_args()
source = args.source.resolve()
if sys.platform != "darwin":
    raise SystemExit("Settings snapshots require macOS and Xcode")
versions = json.loads((source / "versions.json").read_text())
xcode = subprocess.check_output(["xcodebuild", "-version"], text=True).splitlines()[0].split()[1]
if xcode != versions["xcode"]:
    raise SystemExit(f"Required Xcode {versions['xcode']}; found {xcode}")
runtimes = json.loads(subprocess.check_output(["xcrun", "simctl", "list", "runtimes", "-j"], text=True))["runtimes"]
if not any(r.get("version") == "26.5" and r.get("isAvailable") and "iOS" in r.get("name", "") for r in runtimes):
    raise SystemExit("Install the pinned iOS 26.5 simulator runtime before capturing baselines")
temp = Path(os.environ.get("RUNNER_TEMP", "/tmp"))
configuration = json.loads((source / "build-system/template_minimal_development_configuration.json").read_text())
configuration.update(bundle_id="one.ayugram.snapshot.tests", api_id="0", api_hash="", team_id="AYUCOMPILE", app_specific_url_scheme="ayugram-tests", is_internal_build="false")
config = temp / "ayu-snapshot-configuration.json"
config.write_text(json.dumps(configuration))
config.chmod(0o600)
rc = source / ".bazelrc"
flag = "build --//Telegram:disableProvisioningProfiles\n"
if flag not in rc.read_text():
    with rc.open("a") as output:
        output.write("\n" + flag)
python_support.prepare(source, temp / "ayu-python-support", "debug_sim_arm64")
artifacts = source / "artifacts/snapshots"
artifacts.mkdir(parents=True, exist_ok=True)
command = [sys.executable, "build-system/Make/Make.py", "--cacheDir=" + str(temp / "ayu-bazel-cache"),
           "test", "--configurationPath=" + str(config), "--xcodeManagedCodesigning",
           "--target=//submodules/SettingsUI:AyuSettingsSnapshotTests"]
run_logged_build(command, source, artifacts / "test.log", [])
