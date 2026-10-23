#!/usr/bin/env python3
"""Build with the pinned native toolchain; never label an unsigned archive installable."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import struct
import subprocess
import sys
import zipfile

parser = argparse.ArgumentParser()
parser.add_argument("source", type=Path)
parser.add_argument("--phase", choices=["baseline", "port"], required=True)
parser.add_argument("--configuration", choices=["debug_arm64", "debug_sim_arm64"], default="debug_arm64")
args = parser.parse_args()
source = args.source.resolve()
port_root = Path(__file__).resolve().parent.parent
versions = json.loads((source / "versions.json").read_text())
if sys.platform != "darwin":
    raise SystemExit("Native build requires the macOS runner")
actual_xcode = subprocess.check_output(["xcodebuild", "-version"], text=True).splitlines()[0].split()[1]
if actual_xcode != versions["xcode"]:
    raise SystemExit(f"Required Xcode {versions['xcode']}; found {actual_xcode}")
macos = subprocess.check_output(["sw_vers", "-productVersion"], text=True).strip()
if macos.split(".")[0] != versions["macos"].split(".")[0]:
    raise SystemExit(f"Required macOS major {versions['macos']}; found {macos}")

# This changes only build-time packaging for explicitly unsigned compilation. It neither
# supplies a fake profile nor changes the OS signing/install requirements on an iPhone.
if args.configuration == "debug_arm64":
    rules = source / "build-system/bazel-rules/rules_apple"
    rules_pin = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=rules, text=True).strip()
    if rules_pin != "485016eb5b0948cc17307064e7977a6d68e94046":
        raise SystemExit("Unsigned build support requires the pinned rules_apple revision")
    rules_patch = str(port_root / "patches/unsigned-build-rules.patch")
    reverse = subprocess.run(["git", "apply", "--reverse", "--check", rules_patch], cwd=rules,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if reverse.returncode != 0:
        subprocess.run(["git", "apply", "--check", rules_patch], cwd=rules, check=True)
        subprocess.run(["git", "apply", rules_patch], cwd=rules, check=True)

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
if args.configuration == "debug_arm64":
    unsigned_flags = "build --features=ayu_unsigned_compilation --features=disable_legacy_signing\n"
    if unsigned_flags not in rc.read_text():
        with rc.open("a") as output:
            output.write(unsigned_flags)

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
    expected_platform = 7 if args.configuration == "debug_sim_arm64" else 2
    platform_id = None
    cursor = 32
    for _ in range(struct.unpack_from("<I", binary, 16)[0]):
        if cursor + 8 > len(binary):
            raise SystemExit("Truncated Mach-O load command")
        command_id, command_size = struct.unpack_from("<II", binary, cursor)
        if command_size < 8 or cursor + command_size > len(binary):
            raise SystemExit("Invalid Mach-O load command size")
        if command_id == 0x32 and command_size >= 24:  # LC_BUILD_VERSION
            platform_id = struct.unpack_from("<I", binary, cursor + 8)[0]
        cursor += command_size
    if platform_id != expected_platform:
        raise SystemExit(f"Wrong Mach-O platform: expected {expected_platform}, found {platform_id}")
    if any(name.endswith("embedded.mobileprovision") for name in archive.namelist()):
        raise SystemExit("Unsigned compilation artifact unexpectedly contains provisioning material")
manifest = dict(phase=args.phase, configuration=args.configuration, xcode=actual_xcode, macos=macos,
                native_arm64=True, macho_platform=platform_id,
                signing="unsigned or ad-hoc / no provisioning", install_verified=False,
                telegram_credentials_configured=has_credentials,
                sha256=hashlib.sha256(ipa.read_bytes()).hexdigest())
(artifacts / "manifest.json").write_text(json.dumps(manifest, indent=2))
print(json.dumps(manifest, indent=2))
summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
if summary_path:
    with open(summary_path, "a") as summary:
        summary.write(f"\n### {args.phase}\n\nNative arm64 compilation succeeded. **Unsigned; installation not verified.**\n\n")
        summary.write("Own Telegram API credentials: " + ("configured" if has_credentials else "absent; compilation only") + ".\n")
