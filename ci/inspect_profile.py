#!/usr/bin/env python3
"""Inspect profile metadata without printing certificates, device IDs or private keys.

XML extraction is metadata inspection only; CMS signature/trust must be verified by the
macOS signing pipeline. This helper does not claim a profile is valid or authorizes a device.
"""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib

parser = argparse.ArgumentParser()
parser.add_argument("profile", type=Path)
args = parser.parse_args()
raw = args.profile.read_bytes()
start = raw.find(b"<?xml")
end = raw.find(b"</plist>", start)
if start < 0 or end < 0:
    raise SystemExit("Embedded XML plist not found; use security cms on macOS")
profile = plistlib.loads(raw[start:end + len(b"</plist>")])
entitlements = profile.get("Entitlements", {})
result = dict(
    cms_signature_verified=False,
    created=str(profile.get("CreationDate")), expires=str(profile.get("ExpirationDate")),
    team=profile.get("TeamIdentifier"),
    application_identifier=entitlements.get("application-identifier"),
    app_groups=entitlements.get("com.apple.security.application-groups", []),
    keychain_groups=entitlements.get("keychain-access-groups", []),
    aps_environment=entitlements.get("aps-environment"),
    all_devices=profile.get("ProvisionsAllDevices", False),
    device_count=len(profile.get("ProvisionedDevices", [])),
    developer_certificate_sha256=[hashlib.sha256(cert).hexdigest() for cert in profile.get("DeveloperCertificates", [])],
)
print(json.dumps(result, indent=2))
