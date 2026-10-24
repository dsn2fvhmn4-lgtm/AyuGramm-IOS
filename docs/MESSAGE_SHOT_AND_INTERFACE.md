MessageShot and interface controls — development source

Settings → AyuGram → Interface:
- Show IDs in profiles: a native Telegram ID row for users, groups and channels. Tap/hold copies the ID and shows the native copy toast. User IDs are raw; legacy groups use a minus prefix; channels/supergroups use the Bot API -100 prefix. Profile data refreshes when this option changes.
- Hide bubble quick-share buttons: affects ordinary bubble arrows before their layout width is computed. Comment controls and sponsored-message actions retain native behavior. Other special message renderers keep their native controls.
- Hide Chats tab unread badge: updates the native Chats tab reactively. Read counters, read receipts, list-row badges and the system app-icon badge are not modified.
- MessageShot: shown by default; controls its context-menu and selection-share entry points. Interface preferences are per account and independent of Chat Appearance reset.

MessageShot entry points:
1. Long press an ordinary message/album → AyuGram · MessageShot.
2. Select messages → Share → MessageShot. The Messages choice keeps the original native share flow. Disabling MessageShot restores direct native sharing.
3. Review the generated card image, scroll/pinch to zoom, then use the Share button for the system image share/save sheet. Done closes the preview. The generated image is a composed card layout, not a pixel-identical snapshot of the chat window.

Content and bounds:
- Locally present messages from one cloud chat; up to 20 messages, 8 KB UTF-8 per message and 32 KB total text. Missing/ineligible messages reject the entire selection instead of silently omitting them.
- Author names, formatted text and localized dates appear in chronological order. Author/file labels have display bounds. Long message text is never silently truncated: output that exceeds the image-height limit is rejected with a select-fewer-messages prompt.
- Cached photos and file preview images are downsampled to 512 pixels using ImageIO. This feature never starts a media fetch. Files larger than 25 MB, missing cache entries and media without previews receive textual media labels. Audio/video playback, full document rendering, polls and live media are not embedded in the static image.
- Media spoilers never load a thumbnail. Text spoilers are masked using UTF-16 offsets before formatting; overlapping ranges remain masked and malformed ranges mask the entire text. Entities overlapping spoilers or outside the text are not applied.
- Secret/ephemeral/expiring, restricted and copy-protected content is excluded. Current peer/cached-user protection is checked transactionally and checked again before external sharing. Sponsored messages are excluded from MessageShot.
- The image is 900 pixels wide, at most 8000 pixels high, scale 1; it is opaque by default. Image dimensions are checked before allocation. Thumbnail/cache reads have bounded waits. A loading indicator and in-progress guard prevent repeated render requests. No export file is written by this code; the native share sheet handles the owner's chosen destination.

Appearance options — source added after build 8:
- **Settings → AyuGram → MessageShot Appearance** (Russian: «Оформление MessageShot»). Tap Theme to cycle Follow app → Light → Dark. The selected theme controls card/text colors independently of the app theme; automatic follows the current app theme when rendering.
- Independent switches show/hide the outer image background, author names, dates/times, AyuGram header and cached media previews. Disabling background produces alpha transparency around the opaque cards. The preview's system background or the receiving app can visually flatten that transparency; export-format behavior needs device verification.
- Hidden author/date/header areas are removed from the layout rather than leaving their former empty space. Hiding names only hides the author heading; message text, captions and attachments can still identify people.
- With media previews off, the pipeline skips cache reads and image decoding entirely, while retaining textual attachment labels. Protected/expiry rules, spoiler masking and image/text bounds remain in effect.
- Settings persist per account and are snapshotted when generation starts; an already open preview does not change. Reset MessageShot appearance affects this block only, preserving Ghost Mode, archives, filters, media-send settings and MessageShot menu visibility. Defaults preserve the previous rendering.
- The Foundation test harness includes migration/defaults, explicit-false serialization, unknown-theme fallback, theme cycling/selection, account-file persistence and isolated reset. The actual canvas remains standalone UIKit/ImageIO and participates in the early SDK type check. These new changes have not been natively compiled or rendered on this Windows host and are absent from published build 8.

Pre-build verification:
- ci/preflight.py parses changed Swift files and type-checks the actual standalone AyuMessageShotCanvas.swift against the Xcode iPhone Simulator SDK, with warnings as errors. This catches UIKit/ImageIO renderer/preview API errors before building Telegram; it does not type-check the remaining Telegram integration.
- ci/test_models.py includes actual interface and MessageShot policy sources. Tests cover migration, persistence, non-destructive appearance reset, Bot API ID formatting, byte/count bounds, Unicode offsets, overlapping/invalid spoilers and unchanged ordinary text.
- These SDK/Swift tests and the complete native target remain pending the owner's manual Codemagic run. Local Windows checks establish syntax/patch consistency only.

Native/device release checks:
1. Default interface settings, toggle profiles while already open, copy user/group/channel IDs, restart and switch accounts. Confirm tap/hold toast and exact clipboard contents.
2. Toggle Chats tab badge while unread counts change. Restore the badge and verify native counts. Toggle ordinary bubble quick-share; comments/ads must stay actionable and bubble widths must have no empty arrow gap.
3. Export one text, a captioned cached photo, an album, selections including offscreen loaded messages, voice/file placeholders and content with formatting/emoji/spoilers. Selection is retained for retry; normal sharing still clears it as before.
4. Test missing cache, unavailable messages, 21 messages, oversized text and an image exceeding 8000 pixels. No crash, indefinite loader or silently missing selected message is acceptable.
5. Change protection or remove a message while the preview is open; external sharing must revalidate. Verify secret, expiring and restricted content has no usable export path. Check text/media spoilers in the actual pixels.
6. Test preview zoom/rotation, Close, repeated Share, native Save Image, iPad popover anchoring, large fonts, VoiceOver, Russian/English and light/dark.
7. Record and inspect simulator frames per upstream AGENTS.md for all changed UI paths before claiming visual verification. Simulator/device image generation has not been verified on this Windows host.
8. Compare default output to build 8, then test each new appearance switch and all combinations with no headings/date/media. Check compact card spacing and no overlap/clipping. Test forced light/dark under the opposite app theme, transparent corners in an alpha-capable export, media placeholders with previews disabled, account switching/restart, existing-preview stability and isolated reset.
