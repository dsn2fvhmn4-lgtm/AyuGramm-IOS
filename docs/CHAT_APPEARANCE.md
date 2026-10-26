Chat Appearance — development source

Path: Settings → AyuGram → Chat Appearance. This block follows Desktop's showMessageSeconds, deletedMark and editedMark options, plus the iOS equivalent of the configurable Ghost Mode shortcut.

- Show/hide the chat-header ghost button without changing Ghost Mode flags. The Settings entry always remains available.
- Message seconds use Telegram's existing withSeconds timestamp formatter, including full dates, edited-primary dates and imported-message dates. Scheduled “when online” placeholders retain their special behavior.
- Custom deleted/edited labels are per account. Empty strings use the current language. Labels are trimmed, bounded to 24 grapheme clusters/96 UTF-8 bytes, and reject embedded controls, newlines and bidi overrides. Emoji joiners remain supported.
- Switches save immediately. Text fields are drafts until Save Labels or the keyboard Done action. The Clear Text buttons clear drafts; empty saved drafts restore localized defaults.
- Reset restores only appearance defaults; it preserves Ghost Mode, silent sending, regex filters and the history ledger.
- Open history gets a new immutable ChatPresentationData snapshot on settings changes. Entry equality compares this identity, so loaded bubbles re-layout without restarting the app. Font creation and entry refresh run on the main queue.

Defaults: header ghost shown, seconds off, standard localized labels. Old account JSON files migrate these defaults. A corrupt appearance section falls back independently of the Ghost Mode flags. Persistence validation happens before disk writes and policy publication.

Verification status: source/API and patch checks only on Windows. Swift model and actual Postbox tests are configured in the pre-build Codemagic step; this revision has not executed those tests or a full native build here. GitHub Actions stays disabled and Codemagic has no push trigger.

Regression checklist:
1. Open the screen from AyuGram, toggle seconds, return to an already open chat: all visible ordinary bubble timestamps should update once, preserving scroll position and date format (12/24-hour, full/imported date).
2. Hide and show the ghost button: avatar/header stay usable and the current Ghost Mode policy survives hiding, reopening and restarting.
3. Edit both labels, leave without saving, reopen: old saved labels remain. Save new Unicode labels, reopen/restart: saved labels persist. Clear/save restores the current language's defaults.
4. Check text, photo/file captions, albums, stickers, edited messages and locally retained deletions. Labels must not duplicate, clip the time, overlap reactions or force a gap outside the bubble.
5. Check narrow layouts, large fonts, light/dark themes and VoiceOver. Record simulator frames for entering/leaving settings and applying each switch per upstream AGENTS.md before calling native visual verification complete.
6. Switch accounts and reset appearance: neither account's ghost/sending/history settings may change.
