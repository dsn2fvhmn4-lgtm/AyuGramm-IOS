# Device verification — pending

Target supplied by the user: iPhone 11 Pro, iOS 27 Developer Beta 1. Build target: arm64 device, minimum iOS 15. The SDK version alone does not prove beta compatibility.

## Installation

The current CI pipeline builds without provisioning profiles. Signing and installation are separate gates. Use your own Apple account/certificate. One Windows option is [Sideloadly](https://sideloadly.io/), whose official site lists Windows, iOS 27+ and free/paid Apple ID support. Its general compatibility statement is not a device test of this client. Enter Apple account credentials only into the chosen signing tool; never commit them or send them to CI logs.

Free-account signing may impose extension/app-ID/capability limits. Record the install log and actual entitlements; do not assume upstream push notifications, app groups, keychain sharing or all extensions work under a different signature. Removing extensions may change notification/share behavior and must be documented. No device-side changes have been performed by this task.

Concrete startup gate in this snapshot: `submodules/TelegramUI/Sources/AppDelegate.swift` requests `group.<bundle_id>` and presents `Error 2` if `containerURL(forSecurityApplicationGroupIdentifier:)` is nil (around line 699). Thus a signature that merely installs the app but drops its app-group entitlement is insufficient. PasscodeEnvironment also configures its group/keychain at startup. Signing must preserve compatible capabilities; a generic sideloading tool's device support does not establish that.

## Functional tests after a signed installation

Use a second account/device to observe server-visible behavior. Keep other sessions of the test account inactive so their read/online updates do not contaminate the test.

1. With all Ghost Mode options off: log in (including 2FA when enabled), open a cloud conversation, send/receive text and media, check typing/read receipts and a call.
2. Enable only cloud-read suppression: open a new incoming text, confirm the other account sees no new read acknowledgement. Test private chat, group, supergroup and a discussion thread separately. Verify local unread counters and no repeated synchronization loop.
3. Turn suppression off and read a new message. Confirm ordinary receipt behavior returns; earlier messages may become acknowledged by Telegram's maximum-read-ID semantics.
4. Enable only online suppression while foregrounded, then background/foreground the app. Observe explicit status changes. Record any implicit presence caused by sending messages or by other sessions rather than claiming absolute invisibility.
5. Test typing, voice/video recording and document/photo/video upload indicators with their individual switches both on and off. Group-call speaking indicators should remain functional.
6. Restart the app, switch accounts and verify persistence and account isolation. Newly created accounts must default to ordinary behavior.
7. Verify secret-chat reads, disappearing-message expiration and media-consumption receipts retain upstream behavior. Story views retain upstream behavior. Never claim these are hidden by this implementation.
8. Verify notification actions, extension launches, logout/account deletion and re-login. Live settings propagation between separate processes is not implemented; restarted instances reload the account file.

UI verification must include the project's required simulator frame recording before declaring the native settings screen visually verified. Current UI status: source added, no simulator/device screenshot or recording.
