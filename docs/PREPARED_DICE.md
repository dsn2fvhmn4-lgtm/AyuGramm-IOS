# Prepared dice (experimental)

Open a normal chat, long-press a message and choose **AyuGram · Prepared dice 🎲**
(Russian: **AyuGram · Готовый бросок 🎲**). Choose **Send 1–6** and confirm.
Preparation and validation run first. If they succeed, the app sends the
prepared roll to the original chat/topic automatically and returns to the chat.
There is no separate manual forwarding step.

This feature selects an existing, genuine Telegram dice result. It does not set
the outcome of a new server roll. Telegram's ordinary `inputMediaDice` accepts
the emoticon, not a requested result:
<https://core.telegram.org/api/dice>.

Preparation sends at most 24 random ordinary dice into Saved Messages, with a
two-second delay between rolls. It also forwards a test roll to Saved Messages
using the same `messages.forwardMessages` request used for the recipient. The
first roll and the selected result are checked, including the actual `fwd_from`
metadata returned by Telegram. If Telegram changes the value, retains a forward
header or omits a verifiable dice result, preparation stops before a recipient
send. A set `drop_author` request flag alone is not proof of author removal. Messages
created during preparation remain in Saved Messages. Flood errors stop the
operation; the client does not automatically retry them.

Forwarding uses Telegram's `drop_author` option:
<https://core.telegram.org/method/messages.forwardMessages>.
The public API documentation does not guarantee that dice results survive
forwarding. A successful self-test is not a guarantee for a later recipient
send. The UI reports the actual result returned for that send, including a
changed value or retained attribution. A failed final check reports that the
message was already sent; it does not silently retry or hide attribution locally.
It never changes incoming
media to pretend that a requested number was rolled.

The prepared result expires after ten minutes and belongs to its account.
Secret chats are excluded. No Stars payment is authorized. Closing the screen
disposes the operation; an already submitted request may still finish on the
server, so inspect Saved Messages/the destination before retrying after an
ambiguous response.

This adds native TelegramCore and TelegramUI code and requires rebuilding and
installing the IPA. Refreshing the OTA plugin support list does not add this
feature to an older IPA. Server forwarding behavior still requires a device
test; source validation alone does not establish it.
