# Message menu controls — development source after build 8

Path: **Settings → AyuGram → Message Menu** (Russian: «Меню сообщения»).

Five independent per-account switches:

- **Reaction picker:** show/hide the top reaction chooser in the main long-press message menu. Saved Messages tags retain their native chooser. Existing bubble reactions and their separate interaction paths are unchanged.
- **Read and reaction summary:** show/hide the combined native read/reaction summary row. This affects presentation, not receipt transmission or the fetching of menu data. Ghost Mode still owns receipt policy.
- **Edit information in menu:** show/hide the native edited-time header. Inline edited labels, captured edit history and message text are unchanged.
- **Message Details:** show/hide the AyuGram metadata action.
- **Messages from Author:** show/hide a new action for cloud group/supergroup messages with a known user author. It dismisses the menu and opens native in-chat search using the author filter. Private chats, broadcast channels, anonymous/channel authors and sponsored messages do not receive this action. The native search flow keeps topic and recording-discard behavior; it may query Telegram as normal search does.

All switches default on. Existing build 8 settings migrate with native controls visible; explicit false values survive reload. Changes take effect on the next menu opening. Disabling all AyuGram actions does not leave an extra separator. MessageShot visibility remains in Interface. Essential reply, copy, forward, delete and reporting actions keep upstream availability rules.

Desktop references: `showReactionsPanelInContextMenu`, `showViewsPanelInContextMenu`, `showMessageDetailsInContextMenu` and `showUserMessagesInContextMenu` in the inspected AyuGramDesktop `ayu_settings.h`. iOS uses visible/hidden switches; the Desktop modifier-key state is not implemented. The iOS read/reaction summary is one combined control. Edited-header visibility is an additional iOS setting.

Verification: source grammar/API review and pinned-patch application are checked on Windows. Actual Foundation tests now cover old-settings migration, explicit-false round trips and preservation of existing interface/ghost/media choices. These tests and the native target must run in the owner's manual Codemagic build; no new IPA was compiled or uploaded for this change. Published build 8 does not contain this block.

Device/simulator checks before reporting runtime or visual verification:

1. Open the submenu in Russian/English, toggle each control, restart and switch accounts. Other interface, Ghost Mode and media settings must remain intact.
2. Compare menu openings with controls enabled/disabled for incoming/outgoing group text, media and albums, edited messages and messages with read/reaction summaries. Verify no empty section or duplicate separator and preserve core actions.
3. Hide the reaction picker; check ordinary long-press menus, existing reaction taps and Saved Messages tags separately. Toggle the read summary while Ghost Mode is off/on; receipt policy must remain unchanged.
4. Select Messages from Author in a legacy group, supergroup and forum topic, including a bot author. Native search must show the author filter, return the matching messages and exit normally. Confirm absent actions for private, broadcast, anonymous, unknown-author and sponsored cases.
5. Start author search while recording to exercise the upstream discard prompt. Test menu reopening after changing settings, navigation away and rapid taps.
6. Record and inspect simulator frames per upstream AGENTS.md, including light/dark themes, narrow screens, large fonts and VoiceOver. No simulator/device verification was performed on this Windows host.
