# AyuGramm-IOS

An unofficial native Telegram-iOS adaptation with AyuGram-inspired features. The first [Ghost Mode preview](https://github.com/dsn2fvhmn4-lgtm/AyuGramm-IOS/releases/tag/v0.1.0-ghost-preview) is available. The owner reports it works on their device; independent device verification is pending.

## Current implementation

This repository contains a reproducible native source patch against Telegram-iOS commit `fb0e62ba8a147f0821da6aa63c09da7d79a10111`. `ci/prepare.py` checks the exact commit before applying it. The complete upstream client supplies authentication, chats, media and calls; these still require regression testing for this port.

Experimental Ghost Mode adds per-account persistent controls for cloud chat/discussion read receipts, explicit online status, typing/recording and upload progress. Open **Settings → Privacy and Security → AyuGram · Ghost Mode**. All options default off. Secret-chat read handling, media consumption/expiration and story-view receipts retain upstream behavior. This is not an absolute-invisibility guarantee. New reads after disabling the mode can acknowledge earlier messages. Already transmitted requests cannot be retracted.

Ghost Mode conflicts with [Telegram API Terms section 1.4](https://core.telegram.org/api/terms). Server Premium features are not unlocked. Message history and other AyuGram features are not implemented yet.

## Cloud builds from Windows

GitHub Actions checks the real settings-store source, parses changed Swift files and builds the native application on the `xcode-27` runner with Xcode 27.1. New builds default to `release_arm64` and build the port directly. An upstream baseline is optional through manual dispatch. See **Actions → Native iOS port** for actual results.

Codemagic uses the same release configuration on the free Mac M2 tier. Import the `telegram_credentials` variable group with Secure `TELEGRAM_API_ID` and `TELEGRAM_API_HASH`. Its reusable Bazel disk cache is capped at 2.5 GB to fit the personal-plan quota; the first successful release build populates it. Cache reuse and speed gains still require measurement.

### Next build (not included in v0.1.0)

- AyuGram branding using the original AyuGram Desktop SVG (see upstream attribution below).
- A direct **AyuGram · Ghost Mode** entry near the top of Settings, retaining the existing Privacy and Security entry.
- A ghost button next to the chat header controls: outlined ghost when any Ghost Mode option is active, crossed ghost when all are off. Tapping opens the settings. The indicator reflects local policy, not server-confirmed invisibility.
- After a successful cloud-message send, reassert offline status when Hide Online is enabled. A brief server-visible activity window remains possible; failures do not alter send results.

These next-build changes require native compilation and simulator/device verification, including light/dark themes, narrow screens, selection mode and returning from settings. They are not present in the already uploaded IPA. Full AyuGram feature parity remains unfinished; see `docs/FEATURE_MATRIX.md`.

Configure your own `TELEGRAM_API_ID` and `TELEGRAM_API_HASH` as repository secrets. The workflow does not use third-party API credentials. Artifacts built without those secrets are compilation-only and cannot log in.

Current pipeline outputs have **no provisioning profiles or distribution signature**. They require a separate signing/install process and device verification. A successful compile does not establish successful login, hidden network receipts or installation on an iPhone. No App Store/TestFlight publishing is configured.

For local macOS preparation:

```sh
git clone https://github.com/TelegramMessenger/Telegram-iOS.git telegram
git -C telegram checkout fb0e62ba8a147f0821da6aa63c09da7d79a10111
python3 ci/prepare.py telegram
```

Follow the pinned upstream README for signed development/distribution builds with your own bundle identity, team and provisioning profiles. The unsigned compilation identity used by CI is not an Apple signing identity.

## Attribution and source availability

Based on [Telegram-iOS](https://github.com/TelegramMessenger/Telegram-iOS). Feature research references [AyuGram4A](https://github.com/AyuGram/AyuGram4A) and [AyuGramDesktop](https://github.com/AyuGram/AyuGramDesktop), maintained by their respective authors. The Swift adaptation is new code; Android/Desktop source files are not copied into this patch. Preserve upstream notices and comply with applicable source-distribution and dependency licenses before distributing binaries.

Planning, feature scope, limitations and verification are recorded in the accompanying Markdown documents. Read their current status before treating a feature as tested.
