Manual Codemagic builds

The owner controls when to compile. GitHub Actions is disabled; source pushes do not start builds. The workflow defaults to release_arm64 on Mac M2 with Xcode 27.1.

Before the full Telegram target, the workflow installs/probes Metal, checks ccache/sysctl in Bazel's restricted PATH, validates Telegram API variables, applies the patch to the exact pinned source revision, checks patch whitespace, executes CI helper tests, parses all changed Swift sources and checks known UI-import/API contracts. It then compiles and runs the actual Foundation settings/history/regex/archive model sources with warnings treated as errors. The same fast host test also builds the pinned Postbox serialization implementation and round-trips the actual history schema, covering the raw-enum crash that JSONEncoder did not detect.

Preflight does not type-check UIKit/Postbox integration against all Telegram dependencies. That happens during the full native build. This limitation must be stated when reporting uncompiled changes; source checks are not proof that an IPA will build or work.

The native wrapper uses --continueOnError to collect independent compilation failures in one pass. Artifacts include a redacted build.log, the IPA/manifest when packaging succeeds, and model-test output. No API values are intentionally printed into the build log. The existing personal-tier cache is bounded at 2.5 GB and is populated by successful Codemagic builds; speed gains are not guaranteed.

Current evidence: four Python CI-helper tests pass locally. The previous 32 Foundation checks passed on a Mac before the regex/metadata/media-archive additions. Expanded Swift checks and new UI/Core integration have not been compiled since the owner selected manual Codemagic-only builds.
