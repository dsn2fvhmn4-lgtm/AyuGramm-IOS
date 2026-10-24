# Local message hiding — development source after build 8

Long press an ordinary cloud message → **AyuGram · Hide Locally** → confirm. An album is treated as one item. This enables local hiding for the current account and removes the item from its ordinary chat-history rendering. The engine re-reads the selected IDs locally before the confirmation; a missing/ineligible message rejects the entire batch. No server deletion, message database deletion or media download is requested.

**Settings → AyuGram → Hidden Messages** provides:

- **Apply local hiding:** temporarily show hidden items without forgetting their marks; turn it back on to apply the same list.
- **Individual restore:** tap a row identified by chat ID and message ID to remove its hiding mark. An album row restores the entire album. The list uses identifiers rather than persisting message text or media.
- **Restore all messages:** confirmation removes all hiding marks for the account. This does not restore content already deleted from Telegram. A restored item may still match a separate regex rule.
- A count of marked messages/albums, bounded to **200**. Duplicate messages and album components do not consume extra entries. Capacity/invalid-ID failures are atomic and do not partially hide a batch.

**Settings → AyuGram → Message Menu → Hide Message Locally** controls action visibility; it does not clear marks or disable already configured hiding. Settings and references persist in the account-owned settings file. Logout/account-directory removal owns their lifetime. Other feature settings and archives are preserved.

Scope and limitations:

- Ordinary cloud users, legacy groups, channels and supergroups. Secret chats, service/sponsored messages and unsent/local IDs have no hiding action. This mechanism stores references only, including an album grouping key; it can hide protected/expiring cloud content without copying that content.
- Hiding is a reversible display filter, not a confidentiality feature. Search, selection, direct message subjects and tagged/media views bypass AyuGram display filters. Chat-list previews, notifications, server state and other devices retain native behavior. No promise is made to conceal all traces of a message.
- The active-search state is now explicitly propagated to history rendering through a value signal. It bypasses both manual hiding and regex filtering while search is open, and re-applies them when search closes. The signal is updated after the new interface state is assigned. Tagged/media views also bypass both filters.
- Existing settings-change subscriptions cause the current history to rebuild after hiding/restoring; no app restart should be required. This interaction still needs device verification.
- Hiding does not preserve removed/expired content or change its lifetime. Stale marks can remain after server deletion until the owner restores them or clears the list. Album components loaded later match the same peer-scoped grouping key.

Reference: AyuGramDesktop `AddHideMessageAction` and `showHideMessageInContextMenu`. This iOS adaptation intentionally uses a bounded reference list and history rendering rather than destroying local database items.

Verification: Windows checks cover source grammar/import contracts, complete pinned-patch application and Python CI tests. The actual Foundation harness was extended for empty defaults, exact-peer/namespace matching, duplicate/album grouping, temporary bypass persistence, restore-one/all, invalid-ID and capacity atomicity, account-file persistence and old-schema migration. The manual Codemagic pre-build step includes the new model. These Swift tests, the native target and simulator/device UI have not been executed here. Published build 8 does not contain this block.

Device checks before reporting runtime/visual verification: hide/confirm/cancel text and albums; scroll away/back and restart; switch accounts; load more album components; reach capacity; disable/re-enable hiding; restore individual/all; keep a regex matching a restored item; open/close native search and selection; inspect direct links, media views, chat-list previews and notifications; expire/delete a marked message; exclude ads/services/secret and pending sends; test privacy settings and persistence errors. Record and inspect simulator frames per upstream AGENTS.md, including light/dark, narrow layouts, large fonts and VoiceOver.
