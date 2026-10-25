# AyuGramm-IOS

<img src="assets/branding/AyuGram-logo.png" width="128" alt="AyuGram for iOS logo">

An unofficial native Telegram-iOS adaptation with AyuGram-inspired features. [Release 3](https://github.com/dsn2fvhmn4-lgtm/AyuGramm-IOS/releases/tag/v0.3.0-preview) is available as **AyuGramm-IOS.ipa**. See the [complete Release 3 changelog](docs/releases/v0.3.0.md) for additions, fixes, installation and verification status. [Previous releases](https://github.com/dsn2fvhmn4-lgtm/AyuGramm-IOS/releases) remain available.

Release 3 source changes add message-menu controls, author search, filter management, MessageShot appearance, text-to-draft/search/ID tools, reversible local message hiding, reaction-display settings and updated app artwork. Reliability changes cover filter scope, image bounds, missing App Group access, startup diagnostics and database-key persistence. The detailed changelog distinguishes source changes from pending device verification.

## Current implementation

Development source adds **tap .plugin -> review -> Import and enable**, automatic local conversion of complete literal outgoing-text hook templates, atomic activation and restored hook behavior after restart. Direct Java/Xposed/UI hooks still need dedicated mappings. See [conversion patterns and exact scope](docs/PLUGIN_CONVERSION.md). Native compilation and iPhone verification remain pending.

The next development block reorganizes **AyuGram Preferences** into categories without a large header, adds the **@neosay1337** channel link, full plugin-details pages and a native app-icon picker with the owner's three variants plus all twelve original AyuGram Desktop presets. See [preferences and icon changes](docs/PREFERENCES_AND_ICONS.md) for scope and pending native verification. Release 3's existing IPA is unchanged.

Development source after Release 3 adds **Settings → AyuGram → Plugins**, native `.plugin` import/export and actions, a reviewed partial Search+ 2.6.1 adapter, and puzzle-piece icons. See [supported operations, conversion limits and verification](docs/PLUGINS.md). The already published Release 3 IPA does not contain this block.

This repository contains a reproducible native source patch against Telegram-iOS commit `fb0e62ba8a147f0821da6aa63c09da7d79a10111`. `ci/prepare.py` checks the exact commit before applying it. The complete upstream client supplies authentication, chats, media and calls; these still require regression testing for this port.

If you would like to support the repository authors, you can send a contribution to our TRC20 wallets or mono

murk-sus: only TRC20: TCPD7jzSMtQ4zkoSxSbUZi6RFoVdKqv78w

dsn2fvhmn4-lgtm (only mono): mono: 4874070019870151

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

## Filter management (development source after build 8)

The latest development sources also add **AyuGram · Add Filter** to eligible message menus, literal-text rule drafts, saved/editor rule counts and confirmed **Clear all rules**. The default channels-only scope now distinguishes broadcast channels from supergroups. See [filter management and verification](docs/FILTER_MANAGEMENT.md). These changes are not in build 8 and still await native/device checks.

## MessageShot appearance (development source after build 8)

The new **Settings → AyuGram → MessageShot Appearance** page controls theme (app/light/dark), outer-background transparency, author/date/header visibility and cached-media previews, with a reset limited to this feature. Changes affect newly generated images. See [appearance scope and verification](docs/MESSAGE_SHOT_AND_INTERFACE.md). This block is not in build 8 and still awaits native compilation/device rendering checks.

## Message text tools (development source after build 8)

Message menus now offer **Repeat Text** (confirmed append to a draft, no automatic send), **Find Phrase** (native in-chat search) and **Copy Message IDs**. Each has an account-specific visibility switch under Message Menu. See [scope, prior-block review and device checks](docs/TEXT_TOOLS.md). These changes still await native/device verification and are not in build 8.

## Hidden messages (development source after build 8)

**AyuGram · Hide Locally** hides an ordinary cloud message/album from the account's main chat history without deleting it. **Settings → AyuGram → Hidden Messages** offers a temporary bypass, individual restoration and confirmed restore-all, with a 200-item limit. The list stores references only. Search, selection and tagged/media views bypass both manual hiding and regex filtering. See [scope and pending device checks](docs/HIDDEN_MESSAGES.md). This block is not in build 8 and awaits native/device verification.

## Reaction display (development source after build 8)

**Settings → AyuGram → Chat Reactions** independently shows/hides reaction rendering in private chats, groups and channels. Saved Messages tags and unknown peer types retain native behavior. This does not remove server reactions or disable the menu picker. See [rendering scope and pending native checks](docs/REACTION_DISPLAY.md). The block is not included in build 8.

## Ghost Mode+, translation, export and archive (development source after Chat Colors)

Opt-in scheduled sending and read-after-send, Telegram/LibreTranslate/DeepL translation, HTML+JSON chat export or forwarding to Saved Messages, a media archive manager, a local-only emoji status and **AyuGram · Repeat** with a sender-hidden copy for attachments. See [scope and limits](docs/ADVANCED_FEATURES.md). These blocks are not in any published IPA and await native/device verification.

## Cloud builds from Windows

Builds are run manually by the owner in **Codemagic** with the pinned Xcode 27.1. `ayugram-ios-unsigned` builds `release_arm64` (optimized, published IPAs); `ayugram-ios-fast` builds `debug_arm64` for quick compile checks and test installs (unoptimized, no dSYM, larger and slower at runtime). Both run the cheap source checks before downloading the large native dependencies, so most source errors fail within minutes. GitHub Actions runs the same steps: pushes to `main` that change the port (`patches/`, `ci/`, `upstream.json`, the workflow) build `debug_arm64`, and **Run workflow** can choose `release_arm64`. Actions uses the repository secrets `TELEGRAM_API_ID` and `TELEGRAM_API_HASH`.

Codemagic uses the same release configuration on the free Mac M2 tier. Import the `telegram_credentials` variable group with Secure `TELEGRAM_API_ID` and `TELEGRAM_API_HASH`. Its reusable Bazel disk cache is capped at 2.5 GB to fit the personal-plan quota; the first successful release build populates it. Cache reuse and speed gains still require measurement.

### Branding and Ghost Mode controls (build 8 preview)

- AyuGram branding. The latest source uses the owner-provided Apple/airplane artwork with the external black surround removed; the app artwork is full-bleed and the standalone logo has transparency. See [branding assets](assets/branding/README.md). Published build 8 retains the earlier artwork.
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

The authors are not responsible for any crashes, errors, or other issues. By installing the client, you acknowledge that you are aware of all the rules for using the application.

Camera Flip native adapter and the supplied five-plugin dependency inventory: [bridge status](docs/ANDROID_PLUGIN_BRIDGES.md). Source changes require a new native build; the published IPA is unchanged.

Chat Colors 1.0 now has a reviewed native adapter in development source: presets/HEX, brightness, profile/list menus and account-local color settings. Native build and device verification remain pending.
