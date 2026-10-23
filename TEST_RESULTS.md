# Verification log — 2026-10-23

## Ghost Mode implementation update

- GitHub CLI installed from the official release archive and verified against its published SHA-256 list; authenticated to the user's existing repository.
- The user's own API credentials stored in GitHub Actions Secrets; no credentials added to tracked files.
- Added native persistence/UI/presence/input-activity/cloud-read hooks; secret read/expiry and media-consumption paths unchanged.
- `git diff --check` passes. Exported patch passes `git apply --reverse --check` against the modified local source tree.
- Bundled Python `py_compile` passes for ci/prepare.py, ci/build.py and patched build-system/Make/Make.py.
- Added 16 meaningful storage/observation checks (restart persistence, account isolation, write-failure rollback, corruption handling, observer removal and concurrent-transform serialization). Execution on macOS is pending.
- GitHub Actions native baseline/port pipeline prepared; cloud run results will be recorded below.

The following section records the earlier source-investigation baseline, before this implementation.

## Executed

- Read the complete user-attached porting specification.
- Environment check: Windows 10.0.26100; Git found; xcodebuild and bazel absent from PATH; Python executable resolves to WindowsApps alias.
- Retrieved shallow snapshots of Telegram-iOS, AyuGram4A and AyuGramDesktop; pinned commit IDs recorded in PORTING_PLAN.md.
- Android remote branch inventory: only `rewrite`, at 7013145676d36d82ee13c02a89f72097b7490dcd.
- Inspected Android configuration, regex filter and message-history controller; Desktop settings declarations and message storage; iOS README, toolchain pins and candidate module paths.
- Reviewed official Telegram API Terms and AyuGram documentation online.
- Initial iOS checkout hit long-filename errors. Enabled repository-local core.longpaths and restored files from the pinned HEAD. Final checkout status recorded separately after completion.
- Final `git -C Telegram-iOS status --porcelain` is empty: checkout recovery completed, with no application source edits.
- Filename search found no tracked Android `AyuMessageUtils`/`proprietary` implementation, although the history controller imports it. Treat Android history as an incomplete reference until resolved.

## Not executed

- Baseline native build, Swift compilation, simulator/device runs, unit/integration tests.
- Feature integration, authentication, messaging/media/calls regression checks.
- Signing/export or install verification. IPA artifact: none.

Next test gate: build unchanged Telegram-iOS on a matching macOS toolchain with the project's own configuration, then validate real-device installation before claiming a working port.
