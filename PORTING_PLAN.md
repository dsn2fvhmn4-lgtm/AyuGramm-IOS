# AyuGram for iOS — initial source investigation

Date: 2026-10-23. Status: first native Ghost Mode implementation written; cloud verification pending.

## Current implementation update

The user selected Ghost Mode and authorized GitHub builds. The existing repository is https://github.com/dsn2fvhmn4-lgtm/AyuGramm-IOS. It stores a pinned upstream reference plus the native patch, avoiding a duplicated vendored source tree. GitHub CLI is authenticated; the user's own Telegram API credentials are stored as repository Actions secrets, not source files.

Implemented source: account-scoped persistent policy, native settings entry, online presence filtering, typing/recording/upload activity filtering, cloud history/discussion receipt call sites. Secret-chat read handling, media consumption and story receipts are intentionally unchanged. These are implemented hooks, not yet runtime-verified behavior. Native baseline/port builds and storage tests are configured in GitHub Actions on xcode-27/Xcode 27.1.

## Pinned source snapshots

| Directory | Upstream | Branch | Commit | Commit date |
|---|---|---|---|---|
| Telegram-iOS | https://github.com/TelegramMessenger/Telegram-iOS | master | fb0e62ba8a147f0821da6aa63c09da7d79a10111 | 2026-10-22 |
| AyuGram4A | https://github.com/AyuGram/AyuGram4A | rewrite | 7013145676d36d82ee13c02a89f72097b7490dcd | 2023-07-28 |
| AyuGramDesktop | https://github.com/AyuGram/AyuGramDesktop | dev | 0f2a31bb420de98f331990432265b131b8d836b5 | 2026-10-20 |

Clones are shallow. Source retrieval is not build validation. Android's remote currently exposes only `rewrite`; this is an old source snapshot, not evidence of parity with current Android releases. Full historical/upstream diffs remain pending.

## Architecture verified in the iOS tree

Use TelegramCore for engine/state, TelegramApi for generated protocol types, Postbox for storage, MtProtoKit for transport, SSignalKit/SwiftSignalKit for reactive state, SettingsUI for settings and TelegramUI for chats. Preserve upstream authorization, media and calls. Do not add a second Telegram networking stack.

## Execution sequence

1. DONE: retrieve the three source snapshots and inspect configuration, filtering and history implementations.
2. DONE: identify initial iOS module counterparts; see FEATURE_MATRIX.md.
3. DONE: user selected Ghost Mode.
4. PENDING: provision macOS matching versions.json; prove an unmodified upstream build before feature integration.
5. PENDING: own app identity/API configuration, signing and reproducible CI. Do not copy upstream private signing infrastructure.
6. SOURCE IMPLEMENTED: persistent per-account Ghost Mode settings and native UI; compilation/device verification pending.
7. PENDING: implement selected group, verify on simulator/device, update documentation.
8. PENDING: regression checks for authentication, messaging, media, account isolation and calls; then signed IPA.

## Source and distribution review

Android root LICENSE contains GPL v2; Desktop root LICENSE contains GPL v3. These observations do not establish compatibility for copying arbitrary files between projects. No root LICENSE file was found in this iOS snapshot; its README requires license compliance and source publication. Audit the applicable iOS licensing statements, per-file exceptions, dependencies and attribution before copying implementation. Prefer native adaptations with source references. Publish required corresponding sources when distributing.

Official API terms: https://core.telegram.org/api/terms (reviewed 2026-10-23). Section 1.4 explicitly prohibits interference with read/online/typing and self-destruct behavior; section 2.1 requires own api_id; section 3.3 requires sponsored-message support. These are product constraints, not claims of technical impossibility.
