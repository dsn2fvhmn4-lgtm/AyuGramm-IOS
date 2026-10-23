# Known limitations

- A first partial native Ghost Mode implementation is integrated in source; device/network verification is pending. Other AyuGram features remain unimplemented.
- Native iOS compilation and simulator execution remain untested; current machine is Windows.
- GitHub CLI access and own Telegram credentials are configured. CI targets the matching xcode-27 image with Xcode 27.1. Signing identity/profiles and target iPhone/iOS version remain outstanding.
- The supplied Android repository exposes an old 2023 rewrite snapshot. Its completeness/current-release parity is not established. `AyuMessagesController` imports `com.radolyn.ayugram.proprietary.AyuMessageUtils`; availability and licensing of this dependency require inspection.
- Shallow history is insufficient for a complete upstream-delta audit. No claim of exhaustive diff analysis is made.
- GPL and per-file/dependency compatibility review is incomplete; root license text alone is not enough.
- Ghost behavior conflicts with Telegram API Terms 1.4; protected-message expiration must be preserved. Local cosmetic options do not confer server Premium benefits.
- Push notifications, background behavior and calls require real-device verification and app-specific capabilities.
- CI is configured to produce unsigned native artifacts. Consult TEST_RESULTS.md and the linked run for actual build results. Successful authentication, installation and hidden receipts require device testing.
- Ghost Mode suppresses ordinary cloud history/discussion receipts, explicit online status and selected input activities. It preserves secret-chat read/expiration processing, media-consumption receipts, story views and group-call speaking indicators. Sending a message, another logged-in client or already transmitted requests can reveal activity. Later reads with the mode disabled can acknowledge earlier messages.
- Settings update observers are per Network instance. Restarted extensions load the persisted account file, but live cross-process notification is not implemented.
