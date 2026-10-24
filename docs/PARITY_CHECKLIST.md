Feature parity tracking

Reference Android source: AyuGram/AyuGram4A rewrite, 7013145676d36d82ee13c02a89f72097b7490dcd. This snapshot is from 2023 and imports missing AyuMessageUtils; it does not supply a complete ready-made iOS implementation. Desktop dev 0f2a31bb420de98f331990432265b131b8d836b5 supplies additional behavioral references. Flags alone are not counted as implemented features.

The published v0.1.0 IPA contains the initial Ghost Mode preview. All subsequent rows marked "source" still require full native compilation/device verification. Builds are run manually by the owner in Codemagic; GitHub Actions is disabled and push triggering is removed.

| Android option / feature | iOS state |
| --- | --- |
| sendReadPackets | Cloud chat/discussion suppression in preview; secret/media-consumption paths preserve expiration |
| sendOnlinePackets | Explicit online suppression in preview |
| sendOfflinePacketAfterOnline | Offline reassertion after accepted cloud sends in source; brief implicit online visibility remains possible |
| sendUploadProgress | Upload-activity suppression in preview |
| useScheduledMessages | Pending; requires scheduling/delivery semantics audit |
| markReadAfterSend | Pending; needs a deliberate receipt override with correct pts/local-state handling |
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
| localPremium | No server entitlement changes; cosmetic mapping remains to be designed |
| syncEnabled | Pending; no sync transport or archive upload is enabled |
| useSecureConnection | Pending as part of sync; no insecure transport introduced |
| WALMode | Android Room implementation detail; account storage remains upstream Postbox |
| custom deleted/edited marks | Per-account Chat Appearance labels in source; eligible deleted text retained inline with local tombstones |
| showMessageSeconds (Desktop) | Native timestamp formatter with seconds, including full/imported dates, in source |
| reset chat appearance | Resets only visual settings and preserves Ghost Mode, history and sending policy, in source |
| source sync URL/token settings | Pending; no token has been stored or transmitted |

Additional Desktop-only scope (not implemented by these flags): translation providers, message screenshots, shadow bans, UI-element visibility controls and other per-account ghost options. These require individual native integrations rather than empty settings switches. Message metadata and conditional/always silent-send modes already have source implementations.

Release gates: clean pinned-patch application, UI import/API-contract checks, parse all changed Swift sources, compile/run real Foundation models, full Telegram target type check/link/package, then device and recorded simulator checks. The 32-check result applies only to the earlier history revision; newly added regex/migration/metadata/media-archive tests have not yet run on a Mac.
