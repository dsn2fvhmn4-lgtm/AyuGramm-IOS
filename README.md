# AyuGramm-IOS

An unofficial native Telegram-iOS adaptation with AyuGram-inspired features. Under development; no verified installable release yet.

## Current implementation

This repository contains a reproducible native source patch against Telegram-iOS commit `fb0e62ba8a147f0821da6aa63c09da7d79a10111`. `ci/prepare.py` checks the exact commit before applying it. The complete upstream client supplies authentication, chats, media and calls; these still require regression testing for this port.

Experimental Ghost Mode adds per-account persistent controls for cloud chat/discussion read receipts, explicit online status, typing/recording and upload progress. Open **Settings → Privacy and Security → AyuGram · Ghost Mode**. All options default off. Secret-chat read handling, media consumption/expiration and story-view receipts retain upstream behavior. This is not an absolute-invisibility guarantee. New reads after disabling the mode can acknowledge earlier messages. Already transmitted requests cannot be retracted.

Ghost Mode conflicts with [Telegram API Terms section 1.4](https://core.telegram.org/api/terms). Server Premium features are not unlocked. Message history and other AyuGram features are not implemented yet.

## Cloud builds from Windows

GitHub Actions checks the real settings-store source, parses changed Swift files and then builds the native application on the `xcode-27` runner with Xcode 27.1. By default the app sources are first built without the port, then patched and rebuilt. See **Actions → Native iOS port** for actual results.

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
