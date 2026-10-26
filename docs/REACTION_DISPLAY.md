# Reaction display — development source after build 8

Path: **Settings → AyuGram → Chat Reactions** (Russian: «Реакции в чатах»).

Independent per-account switches show/hide reactions beneath messages in private chats, groups (including supergroups) and broadcast channels. All default on. **Reset reaction display** restores only this feature's defaults. Saved Messages/tags, ads, non-cloud messages and unknown peer types retain native behavior.

These controls affect presentation extraction only. They do not strip attributes from messages, modify Postbox, remove/send server reactions or disable the native reaction picker. Configure the picker and read/reaction summary separately in Message Menu. Message effects, view/reply counters, paid-send checks and unrelated star/balance information remain native. An ordinary star-reaction chip can be hidden with the other reaction chips.

The current pinned chat renderers use two AccountContext helpers at 23 extraction points across 18 source files: 16 reaction/peer pairs for date/status rendering and seven reaction-attribute extractions for bubble footers, rich data, stickers and video notes. Empty presentation values use the native removal/layout path, so no dedicated blank reaction row is inserted. Account setting changes reuse the existing presentation snapshot refresh for visible history.

Three previously indirect AccountContext dependencies were made direct in the FactCheck, Map and Restricted bubble BUILD files. Preflight now checks both the declaring Swift import and the nearest Bazel package dependency for these helpers; Python regression tests cover the missing-import/dependency cases.

Actual Foundation tests cover all eight scope combinations, native fallback/tag behavior, missing-key migration, explicit-false round trips, account-file persistence and isolated reset. These Swift tests run in the native build pipeline. Windows source/patch checks are not proof of a successful native build. Published build 8 does not include this block.

Device checks: toggle each scope independently across accounts and restarts; inspect text/media/albums, documents, polls, contacts, locations, static/animated stickers and video notes; remove/re-enable rows on already visible messages; verify compact spacing and reaction animations after changes; confirm reaction selection and summaries still use original data; preserve Saved Messages tags, unknown peers and ads; test custom/paid reactions, light/dark, narrow screens, large fonts and VoiceOver. Record simulator frames per upstream AGENTS.md before claiming visual verification.
