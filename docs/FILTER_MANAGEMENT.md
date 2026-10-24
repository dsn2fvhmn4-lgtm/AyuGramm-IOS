# Filter management — source after build 8

## Add a rule from a message

Long press an eligible ordinary cloud message → **AyuGram · Add Filter**. This opens **Regex Filters** with an additional draft rule. It does not save, enable filtering or expand the chat scope automatically. Review the editor and press **Save rules**; use the separate filtering/scope switches as needed. The resulting rule belongs to the account-wide rule list, not just the source conversation. The menu action can be hidden under **AyuGram → Message Menu → Add Filter from Message**.

The phrase is escaped as literal text, so punctuation such as `.*`, `[x]` and backslashes is not interpreted as regex syntax. Newline/control characters use ICU hexadecimal escapes to keep a multiline phrase on one editor line. Limits apply after escaping: at most 32 rules, 512 UTF-8 bytes per rule. Blank phrases and oversize rules are rejected without truncation or changing stored settings. Exact duplicate patterns are reused, including at the 32-rule limit. Long messages can be handled by manually entering a shorter phrase in the editor.

The action is hidden for secret, protected, expiring, service and sponsored messages using the existing MessageShot eligibility policy. Before opening the draft editor, a local engine transaction re-reads the message and peer protection/lifetime state; missing/ineligible content is rejected. No media download is started. Source-message access can subsequently change while an editor is open; already created drafts are not continuously tied to source-message lifetime.

## Saved/editor counts and clearing

The Regex Filters page shows separate **Saved rules** and **Editor** counts. Text is applied with Save rules; enable/scope/case switches continue to apply immediately. Leaving without saving discards the added text, while any explicitly toggled switches remain saved.

**Clear all rules** asks for confirmation. Cancel changes nothing. Approval removes the current account's saved rules and unsaved editor text, and turns filtering off. Other account settings, archives and messages are preserved. Persistence failure is reported and leaves the editor unchanged.

## Scope correction

Previously channels-only filtering used the CloudChannel namespace, which also includes supergroups. It now requires a known TelegramChannel with broadcast info and the current peer ID. Unknown peer type and group chats remain unfiltered unless the wider scope is explicitly enabled. This aligns behavior with the existing scope switch and description.

## Review and verification

Before implementing this block, the preceding Message Menu revision was reviewed against the pinned native API: `ChatSearchDomain.member(EngineRawPeer)`, `beginMessageSearch`, the recording-discard callback and thread-aware `fromId` search. Its five modified sources passed grammar checks, the complete patch passed clean application, and all four Python CI tests passed. No new source/API error was found in that block. This was not a native build or device test.

The new actual Foundation tests cover escaped punctuation, backslashes, CRLF/Unicode separators/emoji, single-line editor serialization, duplicate/capacity boundaries, nonmutating drafts, expansion limits and visibility migration. They are configured for the manual Codemagic pre-build step; they have not run on this Windows host. Native compilation, rendering and device behavior remain pending. Published build 8 contains neither this block nor Message Menu controls.

Device checks: add/review/save/cancel ordinary text and captions; verify disabled filters stay disabled and scope does not expand; test 32 rules, duplicates, long messages and multiline/spoiler text; clear/cancel/restart/switch accounts; change source access before invoking the action; compare broadcast/supergroup/private/secret scopes; test albums and originals in search/selection. Record and inspect simulator frames per upstream AGENTS.md before claiming visual verification.
