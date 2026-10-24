Next-build verification checklist

Expected visuals: the main Settings page shows AyuGram before Saved Messages. A 28 pt outlined ghost appears beside the chat avatar; it is crossed out when every option is off. It never replaces the avatar, call, search or message-selection controls. It opens Ghost Mode settings and updates after toggling options or switching accounts. Check narrow/regular layouts, light/dark themes, text scaling, reply threads and VoiceOver.

Record simulator navigation and toggle changes, inspect recorded frames per upstream AGENTS.md, and attach evidence before marking visual verification complete. No simulator is available in the current Windows workspace.

Use two accounts on separate devices to observe online status before/during/after sending text, photos, albums, forwards and inline-bot results. When Hide Online is off, no extra offline request should be issued. When on, the additional request should follow the successful server response, preserve the send result, and stop being issued after disabling the option. Repeat with network loss. Other devices can override account presence; no absolute invisibility claim.

Check the built IPA has device arm64 platform 2, AyuGram display name and icon, release_arm64 in manifest, and no embedded third-party profile. Record compressed and extracted sizes. The existing v0.1.0 asset is the original debug build and is not replaced by this source update.

Outstanding parity work: edit/deletion history with explicit retention and protected/self-destruct exclusions, local history UI and deletion controls, message/profile metadata, translation provider selection, appearance preferences and optional sync. Server subscription entitlements are unchanged. Each feature needs source-backed integration and device checks before being advertised.
