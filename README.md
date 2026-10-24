# AyuGramm-IOS

An unofficial native Telegram-iOS adaptation with AyuGram-inspired features. The latest [v0.2.0 Feature Preview, build 8](https://github.com/dsn2fvhmn4-lgtm/AyuGramm-IOS/releases/tag/v0.2.0-preview) is available. See the [release description](docs/releases/v0.2.0.md) for features, installation and verification limits. The earlier v0.1.0 release contains Ghost Mode only.

## Current implementation

This repository contains a reproducible native source patch against Telegram-iOS commit `fb0e62ba8a147f0821da6aa63c09da7d79a10111`. `ci/prepare.py` checks the exact commit before applying it. The complete upstream client supplies authentication, chats, media and calls; these still require regression testing for this port.

Experimental Ghost Mode adds per-account persistent controls for cloud chat/discussion read receipts, explicit online status, typing/recording and upload progress. Open **Settings → Privacy and Security → AyuGram · Ghost Mode**. All options default off. Secret-chat read handling, media consumption/expiration and story-view receipts retain upstream behavior. This is not an absolute-invisibility guarantee. New reads after disabling the mode can acknowledge earlier messages. Already transmitted requests cannot be retracted.

Ghost Mode conflicts with [Telegram API Terms section 1.4](https://core.telegram.org/api/terms). Server Premium features are not unlocked. The complete AyuGram feature set is still being ported.

The development sources add a local edit/deletion ledger, formatting and reaction snapshots, a bot-capture preference, message metadata, silent-send modes, local regex filtering and opt-in local media archiving. The build 8 preview is now published; feature-by-feature device regression remains pending. See [history verification](docs/LOCAL_HISTORY.md) and the [complete parity checklist](docs/PARITY_CHECKLIST.md).

## Chat appearance (development source)

Open **Settings → AyuGram → Chat Appearance**. Per-account controls show/hide the header ghost button, display timestamp seconds, and customize deleted/edited labels. Empty labels use the current app language. Save labels applies text; switches apply immediately. Reset affects appearance only. Deleted-text capture remains a separate opt-in under Message History. These changes are part of the build 8 preview; device verification remains pending.

## Media sending (development source)

Open **Settings → AyuGram → Sending Options**. Independent per-account switches confirm sticker/GIF sends and require native preview for ordinary voice/video-note recordings. All four default off. View-once recordings retain their native flow. See [scope and device checks](docs/MEDIA_SENDING.md). Native/device verification is pending.

## Interface and MessageShot (development source)

**Settings → AyuGram → Interface** controls copyable IDs in profiles, ordinary bubble quick-share buttons, the Chats tab unread badge and MessageShot visibility. MessageShot appears in a message context menu or the Share choices after selecting messages. It creates a bounded card image with authors, formatted text, dates and cached image previews; other media has a label. Preview/zoom and the native share/save sheet are available before export. Protected/expiring content is excluded and spoilers remain masked. See [scope and verification](docs/MESSAGE_SHOT_AND_INTERFACE.md). Native/device verification is pending.

## Message menu (development source after build 8)

The next source revision adds **Settings → AyuGram → Message Menu**: reaction-picker, read/reaction-summary, edit-information and Message Details visibility, plus **Messages from Author** using native group search. These per-account controls apply on the next menu opening and are not included in published build 8. See [scope and pending device checks](docs/MESSAGE_MENU.md).

## Cloud builds from Windows

Builds are run manually by the owner in **Codemagic**, using `release_arm64` and the pinned Xcode 27.1. GitHub Actions is disabled and has no push trigger. No build is started automatically by a source push.

Codemagic uses the same release configuration on the free Mac M2 tier. Import the `telegram_credentials` variable group with Secure `TELEGRAM_API_ID` and `TELEGRAM_API_HASH`. Its reusable Bazel disk cache is capped at 2.5 GB to fit the personal-plan quota; the first successful release build populates it. Cache reuse and speed gains still require measurement.

### Branding and Ghost Mode controls (build 8 preview)

- AyuGram branding using the original AyuGram Desktop SVG (see upstream attribution below).
- A direct **AyuGram · Ghost Mode** entry near the top of Settings, retaining the existing Privacy and Security entry.
- A ghost button next to the chat header controls: solid ghost when any Ghost Mode option is active, crossed outline when all are off. Tapping toggles Ghost Mode; detailed switches remain in AyuGram settings. The indicator reflects local policy, not server-confirmed invisibility.
- After a successful cloud-message send, reassert offline status when Hide Online is enabled. A brief server-visible activity window remains possible; failures do not alter send results.

The current source also fixes a Postbox raw-enum serialization trap and retains eligible deleted text inline with a Deleted label beside the message time. Clear Archive, expiry and eviction remove these local text tombstones. The app icon uses an edge-to-edge native background with a separate airplane foreground.

Build 8 is published as an owner-supplied preview. Simulator/device verification remains pending, including light/dark themes, narrow screens, selection mode and returning from settings. These changes are absent from the original v0.1.0 IPA. Full AyuGram feature parity remains unfinished; see `FEATURE_MATRIX.md`.

Configure your own `TELEGRAM_API_ID` and `TELEGRAM_API_HASH` as Secure Codemagic variables in the `telegram_credentials` group. The Codemagic workflow checks these before building. The variables are not copied from GitHub secrets.

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
