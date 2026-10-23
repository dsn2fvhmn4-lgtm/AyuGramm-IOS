#!/usr/bin/env python3
"""Build with the pinned native toolchain; never label an unsigned archive installable."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import subprocess
import sys
import zipfile

parser = argparse.ArgumentParser()
parser.add_argument("source", type=Path)
parser.add_argument("--phase", choices=["baseline", "port"], required=True)
parser.add_argument("--configuration", choices=["debug_arm64", "debug_sim_arm64"], default="debug_arm64")
args = parser.parse_args()
source = args.source.resolve()
versions = json.loads((source / "versions.json").read_text())
if sys.platform != "darwin":
    raise SystemExit("Native build requires the macOS runner")
actual_xcode = subprocess.check_output(["xcodebuild", "-version"], text=True).splitlines()[0].split()[1]
if actual_xcode != versions["xcode"]:
    raise SystemExit(f"Required Xcode {versions['xcode']}; found {actual_xcode}")
macos = subprocess.check_output(["sw_vers", "-productVersion"], text=True).strip()
if macos.split(".")[0] != versions["macos"].split(".")[0]:
    raise SystemExit(f"Required macOS major {versions['macos']}; found {macos}")

api_id = os.environ.get("TELEGRAM_API_ID", "").strip()
api_hash = os.environ.get("TELEGRAM_API_HASH", "").strip()
has_credentials = bool(api_id and api_hash)
if has_credentials:
    if not api_id.isdigit() or int(api_id) <= 0 or not re.fullmatch(r"[0-9a-fA-F]{32}", api_hash):
        raise SystemExit("Telegram API credentials have an unexpected format")
else:
    # This mode establishes compilation only. It cannot authenticate a Telegram account.
    api_id, api_hash = "0", ""
    print("::warning::No own Telegram API credentials: compilation-only artifact, login unavailable")

configuration = json.loads((source / "build-system/template_minimal_development_configuration.json").read_text())
configuration.update(bundle_id="one.ayugram.unofficial.ios", api_id=api_id, api_hash=api_hash,
                     team_id="AYUCOMPILE", app_specific_url_scheme="ayugram", is_internal_build="false")
temp = Path(os.environ.get("RUNNER_TEMP", "/tmp"))
config_path = temp / "ayu-compilation-configuration.json"
config_path.write_text(json.dumps(configuration))
config_path.chmod(0o600)

# Baseline app sources are untouched. This build-only Bazel flag removes profile requirements.
# The port exposes the same existing Bazel switch through Make.py as a CLI option.
rc = source / ".bazelrc"
flag = "build --//Telegram:disableProvisioningProfiles\n"
if flag not in rc.read_text():
    with rc.open("a") as output:
        output.write("\n" + flag)

artifacts = source / "artifacts" / args.phase
artifacts.mkdir(parents=True, exist_ok=True)
command = [sys.executable, "build-system/Make/Make.py", "--cacheDir=" + str(temp / "ayu-bazel-cache"),
           "build", "--configurationPath=" + str(config_path), "--xcodeManagedCodesigning",
           "--buildNumber=" + os.environ.get("GITHUB_RUN_NUMBER", "1"),
           "--configuration=" + args.configuration, "--outputBuildArtifactsPath=" + str(artifacts)]
if args.phase == "port":
    command.append("--disableProvisioningProfiles")
try:
    subprocess.run(command, cwd=source, check=True)
finally:
    config_path.unlink(missing_ok=True)

ipa = artifacts / "Telegram.ipa"
if not ipa.is_file():
    raise SystemExit("Build command returned without an IPA artifact")
with zipfile.ZipFile(ipa) as archive:
    info = plistlib.loads(archive.read("Payload/Telegram.app/Info.plist"))
    binary = archive.read("Payload/Telegram.app/" + info["CFBundleExecutable"])
    if binary[:4] != b"\xcf\xfa\xed\xfe":
        raise SystemExit("Expected a 64-bit Mach-O executable")
    if int.from_bytes(binary[4:8], "little") != 0x0100000C:
        raise SystemExit("Expected arm64 CPU type")
    if any(name.endswith("embedded.mobileprovision") for name in archive.namelist()):
        raise SystemExit("Unsigned compilation artifact unexpectedly contains provisioning material")
manifest = dict(phase=args.phase, configuration=args.configuration, xcode=actual_xcode, macos=macos,
                native_arm64=True, signing="unsigned / no provisioning", install_verified=False,
                telegram_credentials_configured=has_credentials,
                sha256=hashlib.sha256(ipa.read_bytes()).hexdigest())
(artifacts / "manifest.json").write_text(json.dumps(manifest, indent=2))
print(json.dumps(manifest, indent=2))
summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
if summary_path:
    with open(summary_path, "a") as summary:
        summary.write(f"\n### {args.phase}\n\nNative arm64 compilation succeeded. **Unsigned; installation not verified.**\n\n")
        summary.write("Own Telegram API credentials: " + ("configured" if has_credentials else "absent; compilation only") + ".\n")
