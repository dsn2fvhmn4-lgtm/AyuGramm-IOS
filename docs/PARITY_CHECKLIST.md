Feature parity tracking

Reference Android source: AyuGram/AyuGram4A rewrite, 7013145676d36d82ee13c02a89f72097b7490dcd. This snapshot is from 2023 and imports missing AyuMessageUtils; it does not supply a complete ready-made iOS implementation. Desktop dev 0f2a31bb420de98f331990432265b131b8d836b5 supplies additional behavioral references. Flags alone are not counted as implemented features.

The published v0.1.0 IPA contains the initial Ghost Mode preview; v0.2.0-preview is the owner-supplied build 8 with expanded features. See its release notes for artifact evidence and verification limits. Message Menu was added after build 8. Native builds are available through Codemagic and GitHub Actions.

| Android option / feature | iOS state |
| --- | --- |
| sendReadPackets | Cloud chat/discussion suppression in preview; secret/media-consumption paths preserve expiration |
| sendOnlinePackets | Explicit online suppression in preview |
| sendOfflinePacketAfterOnline | Offline reassertion after accepted cloud sends in source; brief implicit online visibility remains possible |
| sendUploadProgress | Upload-activity suppression in preview |
| useScheduledMessages | Opt-in Ghost Mode+ scheduling of plain cloud text (10 s–1 h delay) while Ghost Mode is active, in source; media, topics and secret chats unchanged |
| markReadAfterSend | Opt-in explicit read receipt after a server-accepted ordinary cloud send, applied with pts/local read state, in source; mutually exclusive with scheduling |
| saveDeletedMessages | Transactional text archive in source |
| saveMessagesHistory | Previous text and formatting-only edit capture in source |
| saveFormatting | Codable entity snapshots and native formatted detail rendering in source |
| saveReactions | Reaction/count snapshots and detail summary in source |
| saveForBots | Per-account capture control in source |
| saveMedia | Opt-in local copy of cached photos and files up to 25 MB each, 250 MB quota per account in source |
| saveMediaInPrivateChats | Chat-type toggle in source |
| saveMediaInPublicChannels | Chat-type toggle in source |
| saveMediaInPrivateChannels | Chat-type toggle in source |
| saveMediaInPublicGroups | Chat-type toggle in source |
| saveMediaInPrivateGroups | Chat-type toggle in source |
| regexFiltersEnabled | Local loaded-history filtering in source |
| regexFiltersInChats | Channels by default; optional other cloud chats in source |
| regexFiltersCaseInsensitive | Compiled matcher cache invalidation and editor control in source |
| showGhostToggleInDrawer | iOS equivalent: Settings entry and configurable chat-header ghost control in source |
| showKillButtonInDrawer | Android lifecycle behavior; iOS implementation not defined |
| keepAliveService | Android foreground-service behavior; iOS background execution is platform controlled |
| disableAds | Unchanged; sponsored messages are excluded from local filters |
| localPremium | Desktop-style local Premium in source: own account shown as Premium in this client (badge, emoji statuses, Premium emoji/stickers), server limits and server-enforced checks keep the real subscription, custom emoji from a non-Premium sender go out as `tg://emoji?id=` links and render back as custom emoji; local-only emoji status in own profile/settings |
| syncEnabled | Pending; no sync transport or archive upload is enabled |
| useSecureConnection | Pending as part of sync; no insecure transport introduced |
| WALMode | Android Room implementation detail; account storage remains upstream Postbox |
| custom deleted/edited marks | Per-account Chat Appearance labels in source; eligible deleted text retained inline with local tombstones |
| showMessageSeconds (Desktop) | Native timestamp formatter with seconds, including full/imported dates, in source |
| reset chat appearance | Resets only visual settings and preserves Ghost Mode, history and sending policy, in source |
| stickerConfirmation / gifConfirmation (Desktop) | Opt-in per-account dialogs in sticker, saved GIF and inline GIF chat send handlers; one-shot approval in source |
| voiceConfirmation / roundConfirmation (Desktop) | iOS adaptation: opt-in native preview before ordinary recording sends; view-once keeps its native flow, in source |
| PeerIdDisplay (Desktop) | Optional copyable user/group/channel IDs in native profiles, with live refresh, in source |
| hideFastShare (Desktop) | Ordinary bubble quick-share hiding; comments and sponsored actions preserved, in source |
| hideNotificationBadge (Desktop) | Partial iOS adaptation: Chats tab unread badge visibility only; read state and system app-icon badge unchanged, in source |
| showMessageShot (Desktop) | Local selected-message card image, cached image previews, spoiler masking and native image share preview, in source |
| source sync URL/token settings | Pending; no token has been stored or transmitted |
| showReactionsPanelInContextMenu (Desktop) | Main long-press reaction-picker visibility in source after build 8; Saved Messages tags preserved |
| showViewsPanelInContextMenu (Desktop) | Combined native read/reaction-summary visibility in source after build 8; does not change receipts |
| showMessageDetailsInContextMenu (Desktop) | Metadata-action visibility in source after build 8 |
| showUserMessagesInContextMenu (Desktop) | Native author-filter search action for known user authors in cloud groups, in source after build 8 |
| edited information in menu (iOS) | Edited-header visibility independent of inline labels/history, in source after build 8 |
| showAddFilterInContextMenu (Desktop) | Literal message-text rule draft, explicit save, visibility control, duplicate/capacity checks in source after build 8 |
| regex rule management (iOS) | Saved/draft counts, confirmed account-local clearing and broadcast-only default scope correction in source after build 8 |
| MessageShot appearance (Desktop-inspired/iOS) | Per-account app/light/dark theme, outer-background transparency, author/date/header/media-preview switches and isolated reset in source after build 8 |
| showRepeatMessageInContextMenu (Desktop) | Text/caption append to draft, or confirmed sender-hidden copy with attachments (forward without author) in source; protected/expiring content excluded |
| message text tools (iOS) | Native phrase search and chat/message ID copying, with separate visibility switches in source after build 8 |
| showHideMessageInContextMenu (Desktop) | Reversible local cloud-message/album hiding, per-account bounded references, temporary bypass and restore-one/all manager in source after build 8; no database/server deletion |
| showPrivateChatReactions / showGroupReactions / showChannelReactions (Desktop) | Independent native chat reaction rendering controls with isolated reset in source after build 8; original message data and Saved Messages tags preserved |
| disableStories (Desktop) | Settings → AyuGram → General → Interface → Hide stories: the chat list and archive receive no story subscriptions; applies when the chat list is next created |
| hideSimilarChannels / collapseSimilarChannels (Desktop) | Hide similar channels: no channel recommendations are requested in channel chats |
| hidePremiumStatuses (Desktop) | Hide Premium statuses in chat list rows (emoji status and Premium star); verification marks unchanged |
| hideNotificationCounters (Desktop) | Hide unread counters: unread chats show a dot instead of a number, including the muted count |
| revealSpoilers (Desktop) | Reveal spoilers in message text rendering; media spoilers unchanged |
| filterZalgo (Desktop) | Filter zalgo text: more than two combining marks per character are dropped when rendering message text; emoji and variation selectors kept |
| disableGreetingSticker (Desktop) | Disable greeting sticker in empty private chats |
| disableOpenLinkWarning (Desktop) | Skip the "Open this link?" prompt for text links; disguised hosts (login part), proxies and forced prompts still ask |
| unlimitedRecentStickers (Desktop) | Local recent stickers cap raised from 20 to 200; the server list is unchanged |
| spoofWebviewAsAndroid (Desktop) | Mini apps are requested with platform "android" instead of "ios" |
| streamerMode (Desktop) | Streamer mode: the app window is left out of screenshots, screen recordings and screen sharing through Telegram's secret-chat secure layer; the system keyboard stays visible |
| hideAllChatsFolder (Desktop) | Hide All Chats folder: while at least one folder exists the tab is hidden and the first folder opens; the All Chats page stays last in the container |
| semiTransparentDeletedMessages (Desktop) | Semi-transparent deleted messages: bubble messages kept after deletion are drawn at 50% opacity |
| backgroundNotifications (iOS) | Background notifications (on by default): remote push cannot reach a sideloaded build, so new messages received while the app is in the background (right after closing it, during iOS background refresh) are shown as local notifications, honouring mute, category and preview settings |
Additional Desktop-only scope (not implemented by these flags): shadow bans, additional UI-element visibility controls and other per-account ghost options. These require individual native integrations rather than empty settings switches. Message metadata, conditional/always silent-send modes, translation providers (Telegram/LibreTranslate/DeepL), chat export (HTML+JSON, forward to Saved Messages) and the media archive manager already have source implementations.

Release gates: clean pinned-patch application, UI import/API-contract checks, parse all changed Swift sources, compile/run real Foundation models, full Telegram target type check/link/package, then device and recorded simulator checks. The 32-check result applies only to the earlier history revision; newly added regex/migration/metadata/media-archive tests have not yet run on a Mac.
