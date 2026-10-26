Media sending — development source

Path: Settings → AyuGram → Sending Options. This block adapts Desktop's stickerConfirmation, gifConfirmation, voiceConfirmation and roundConfirmation preferences to native iOS flows. All four switches default off and persist independently per account.

Sticker/GIF confirmation
- Applies to the chat controller's sticker send, saved GIF send and inline-result-as-GIF handlers.
- The first attempt checks native restrictions/slowmode before presenting the dialog. Cancel leaves the original send handler before input clearing, scheduling, paid-message prompts or enqueueing. The picker can remain open during/after confirmation.
- Send re-enters the original handler with the captured media/options, rechecking restrictions and preserving silent/scheduled posting, reply/input handling and the existing paid-message flow.
- A scoped approved kind prevents a second dialog during that re-entry. A one-shot decision rejects duplicate approvals and approval after Cancel. A weak reference to the visible confirmation suppresses overlapping dialogs without retaining a dismissed controller.
- This is not a global interception of every outgoing media API: forwards, ordinary inline-bot results and other external send paths remain native.

Recording preview
- A normal live voice/video-note .send action becomes native .preview when its corresponding option is enabled. The existing draft/playback/trim/delete/send UI handles the recorded data.
- Disable the paid-chat sendImmediately path for these previews, so it cannot immediately transmit a recording before review. Sending explicitly from the preview uses the original flow and does not loop back into another preview.
- Explicit view-once sends keep their native flow. An ordinary preview draft does not store that intent, so this feature never converts view-once into an ordinary draft.
- Pause, resume, dismissal, short-recording rejection, restrictions and file conversion remain native.

Pre-build checks
The actual Foundation model harness covers default-off behavior, independent media-type policies, migration, JSON persistence and preservation of unrelated ghost/silent settings. It also tests one-shot approval, duplicate approval and cancellation invalidation. The model harness runs in the native build pipeline.

Device/simulator regression checklist
1. Every switch off: sticker/GIF and ordinary recorder send behavior matches upstream.
2. Sticker/GIF on: test Cancel, Send, outside dismissal, rapid repeated taps, another media type after dismissal, silent send, schedule, reply and premium/paid/restricted/slowmode chats. Cancel enqueues nothing and keeps text/reply drafts. Approve enqueues exactly once.
3. Test saved and inline GIFs, keyboard stickers and sticker-pack screen sends. Closing the picker after approval is not forced by the deferred Boolean send result.
4. Voice/video preview on: release a recording, review, trim if available, delete, pause/resume and explicitly send. Paid chats must still wait for that explicit send. Very short recordings must follow native rejection behavior.
5. Verify view-once media still has its native expiration intent and flow.
6. Reopen/restart and switch accounts: choices persist and stay isolated; silent-send and Ghost Mode choices remain unchanged.
7. Record simulator frames per upstream AGENTS.md: confirmation must appear once, Cancel returns cleanly to the picker, Send must not flash a second confirmation, and recording transitions into a usable native preview without a blank input panel. Check light/dark themes, narrow layouts, large fonts and VoiceOver.
