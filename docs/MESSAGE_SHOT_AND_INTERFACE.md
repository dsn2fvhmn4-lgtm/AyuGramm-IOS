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
- The opaque image is 900 pixels wide, at most 8000 pixels high, scale 1. Image dimensions are checked before allocation. Thumbnail/cache reads have bounded waits. A loading indicator and in-progress guard prevent repeated render requests. No export file is written by this code; the native share sheet handles the owner's chosen destination.

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
