# Ghost Mode+, translation, export and archive tools (development source)

These blocks were added after the Chat Colors plugin and are not in any published IPA. Native compilation and device checks are pending; see `docs/CODEMAGIC_PREFLIGHT.md`.

## Ghost Mode+ (Settings → AyuGram → Ghost Mode+)

- **Send through scheduling.** While Ghost Mode is active, plain cloud text (no media, topics, inline stickers, story replies or self-destruct timers) is sent as a scheduled message 10 s–1 h ahead. Secret chats are unchanged.
- **Mark read after accepted send.** After the server accepts an ordinary cloud send, an explicit read receipt is sent for that chat and applied through the usual pts/local read state. Topics, forums, secret chats and scheduled sends are excluded. This intentionally reveals a read even when read receipts are hidden.
- The two modes are mutually exclusive; turning one on turns the other off. Settings validation rejects a contradictory stored state.

## Translation providers (Settings → AyuGram → General → Translation providers)

- Message menu → **AyuGram · Translate**. Text is sent to a provider only after tapping Translate.
- Providers: Telegram (no key), LibreTranslate (own HTTPS endpoint, optional key), DeepL API Free/Pro (key required).
- Keys are stored in the Keychain, scoped to the account, provider and endpoint (`AfterFirstUnlockThisDeviceOnly`). Endpoints must be HTTPS without credentials, query or fragment. Redirects are refused; responses are capped at 256 KB.

## Chat export (chat list or profile menu → Export chat / Saved Messages)

- HTML + JSON folder (`messages.html`, `result.json`, `media/`) for a UTC date range, up to 1,000,000 messages; cached media only, up to 250 MB per file and 1 GB total. Pages are spooled to disk, so memory use does not grow with the chat.
- Alternatively, forward the selected range to Saved Messages, oldest first. Protected, expiring and service messages are skipped; stopping does not undo accepted forwards.
- Copy-protected chats and secret chats are refused. The HTML escapes all text and ships a restrictive Content-Security-Policy.

## Media archive (Settings → AyuGram → Media Archive)

- Lists archived copies captured with local history, with usage, per-file and total limits (1–250 MB / 25–2000 MB), export through the system document picker, and removal. Removing media keeps the text history. Lowering limits does not delete older files.
- Files are staged and moved atomically; stale staging files are pruned after 5 minutes.

## Local Premium and status (Settings → AyuGram → Appearance → Local Premium and status)

- **Local Telegram Premium β** (Desktop/Android `localPremium`): this client treats your own account as Premium for presentation — badge, emoji status picker, Premium emoji and stickers. The subscription, limits (pinned chats, folders, saved GIFs/stickers, reactions per message) and server-enforced checks keep using the real server flag, so no limit is raised that the server would refuse.
- Without a real subscription, custom emoji in sent or edited text/captions are rewritten to `tg://emoji?id=<id>` text links (Saved Messages keep them). Any such link covering exactly one emoji renders as that custom emoji; stored entities, quotes and edits keep the link. Other clients show a linked plain emoji.
- Some screens pick the change up after an app restart; the AyuGram settings and account context update immediately.
- **Local emoji status** shows a chosen emoji status, with optional single-play animation, in your own profile/settings only. With local Premium and no subscription, tapping your status opens this local picker. The server status, subscription and other clients are not changed.

## Repeat (message menu → AyuGram · Repeat)

- Text/caption can be appended to the draft as before. For messages with attachments, **Send a copy** forwards the message with the sender hidden (media is reused server-side). Protected, expiring and secret-chat content is excluded.
