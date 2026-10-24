Local text history — development branch

This feature is not included in the published v0.1.0 IPA or the separate branding release build at commit 99b82fd.

Entry point: Settings → AyuGram → Message History. Capture of edits and deletions has separate opt-ins, both off by default. The existing Privacy and Security → AyuGram · Ghost Mode path remains available.

The previous text is captured immediately before an EditMessage replay replaces it. Text is captured before DeleteMessages and DeleteMessagesWithGlobalIds remove a cached message. The bounded ledger is a PreferencesEntry in the same account's Postbox transaction; rollback also rolls back archive changes. Main chat deletion, read receipts and media removal retain upstream behavior.

Limits: 100 total entries, 8 KB UTF-8 per entry, seven-day retention. Expired records are removed on update replay or opening the archive, rather than by a guaranteed background timer. Oversized texts are skipped without truncation. Repeated identical replay events are deduplicated. This is a text-only archive, not recovery of uncached messages or copies of media attachments; text containing ordinary webpage previews is eligible.

Secret namespaces, copy-protected messages/chats, message auto-remove/auto-clear attributes and ephemeral message attributes are excluded. Chat lifetime must be known and disabled. Unknown chat metadata is skipped. The end of replay and archive reads recheck chat eligibility and remove records for peers that become protected or use auto-removal. No archive leaves the account database. Turning capture off stops new entries; Clear Archive removes existing content after confirmation. Account removal owns database lifetime.

Verification required before release:
- Full native compilation of TelegramCore and SettingsUI (parse-only checks are insufficient).
- Device regression: ordinary private/group/channel text edits and deletions; both cloud deletion paths; repeated replay; text with webpage; missing cached message.
- Exclusion checks: secret chat, protected user/group/channel, unknown cached lifetime, auto-delete enabled, message-specific expiry, all ephemeral variants, media attachments.
- Privacy changes after capture must purge peer records; normal updates, message deletion, media expiration and unread state must still work.
- Account isolation, restart, duplicate events, oldest-entry eviction, seven-day boundary, Clear Archive and settings toggles.
- Native UI: list and detail screens in Russian/English, light/dark modes, large fonts, VoiceOver, records disappearing while details are open. Record and inspect simulator frames per upstream AGENTS.md.

Foundation model tests cover opt-ins, Codable round trip, duplicate events, record identifiers, account/state value isolation, capacity eviction, expiry, targeted purge, Unicode byte limit and clear. They do not establish Postbox or device integration correctness.
