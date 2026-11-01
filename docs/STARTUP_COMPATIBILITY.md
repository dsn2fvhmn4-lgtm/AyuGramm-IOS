# Startup and signing compatibility

The source now supports an isolated main-app storage mode when a signing setup
does not provide the expected App Group or its shared Keychain entitlement.
This is intended to address one cause of blank startup screens after re-signing.
It does not establish compatibility with every installer or LiveContainer version.

- A usable shared container and Keychain keep the existing shared storage path.
- Missing App Group access selects `Application Support/AyuGramStandalone` and a
  persistent, random Keychain service namespace. A separate Telegram login may be
  required. Shared account and wallet data is neither copied nor removed.
- Once created, the isolated identity stays in use across launches even if signing
  later restores App Group access. Corrupt/missing identity markers next to an
  existing isolated database stop startup instead of creating replacement credentials.
- A locked or unavailable Keychain does not trigger a storage switch. The app
  displays a diagnostic screen. Passcode checks and biometric access controls remain.
- Shared-container extensions and the legacy wallet are unavailable in isolated
  mode. Background URL sessions do not request the missing shared container.
- The database directory is created before encryption-key generation. An unreadable
  or damaged existing key stops startup; generated key persistence is verified
  before opening the database.

## Compatibility notice after re-signing (27.5.0)

The old “Standalone storage” alert was recreated on every launch, including for an
existing, working standalone account. The shorter “Compatibility mode” notice is
now acknowledged once per standalone storage identity. Only tapping “Got it” saves
the acknowledgement; scheduling or presenting an alert does not. The preference
is outside the `ayu.` settings export and is independent of the app version,
account selection and display language. Shared storage never requests this notice.

This change does not grant App Group entitlements, migrate account databases or
re-enable extensions/the wallet. The notice describes the active storage mode
without claiming the current certificate necessarily lacks App Group access:
an existing standalone identity is intentionally retained after re-signing.

Source syntax was checked on Linux. Device checks remain: acknowledge and fully
relaunch; switch accounts; re-sign without deleting the app; verify the original
account remains available and the notice does not return. On a fresh standalone
installation the notice appears once; killing the app before acknowledgement must
leave it eligible for the next launch. Check shared-container installation too.

LiveContainer also has host-level restrictions, including guest entitlements,
extensions and remote notifications. App startup changes do not remove these:
[LiveContainer limitations](https://github.com/LiveContainer/LiveContainer#limitations).
Revoked certificates, rejected code signatures and failures before app code runs
require changes to the installation environment.

## Verification

Codemagic preflight type-checks the actual storage resolver and diagnostic view
against its iOS Simulator SDK before the full build. The host model-test step runs
the actual resolver through shared/private startup, restart, scope corruption,
Keychain errors and preservation of existing files. PasscodeCore XCTest coverage
adds query-isolation and configuration validation tests; these require the native
PasscodeCore test environment and are not run by the host model harness.

Installation regression checklist: signing, foreground/background startup, login, passcode, Face ID, downloads and relaunch for each installation method.
