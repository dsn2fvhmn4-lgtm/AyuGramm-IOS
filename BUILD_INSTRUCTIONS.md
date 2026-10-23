# Native build baseline

Local host is Windows 10.0.26100. Git and the downloaded/checksum-verified GitHub CLI are operational. The bundled Python runtime successfully syntax-checked the CI scripts and modified Make.py. Native compilation is delegated to GitHub Actions; results are tracked in TEST_RESULTS.md.

## Configured GitHub pipeline

Repository: https://github.com/dsn2fvhmn4-lgtm/AyuGramm-IOS . The pipeline uses the xcode-27 ARM runner and explicitly selects Xcode_27.1.app. The runner-images manifest lists macOS 27 and Xcode 27.1; the actual job independently checks these versions.

Run `Native iOS port` from Actions. It tests the actual settings-store source, parses changed Swift, then builds baseline app sources and the patched app. Device debug_arm64 is the default; debug_sim_arm64 is available manually. The user's own TELEGRAM_API_ID and TELEGRAM_API_HASH are stored in Actions Secrets. Signing certificates/profiles have not been configured. Outputs are unsigned native compilation artifacts, not verified installable releases.

The repository contains upstream.json plus patches/ayugram-ghost-mode.patch; ci/prepare.py checks the pinned commit before applying it. The baseline uses only a build-level no-provisioning Bazel flag. Port Make.py additionally exposes that existing flag through --disableProvisioningProfiles.

## Exact current upstream pins

`Telegram-iOS/versions.json`: app 13.1.1, Xcode 27.1, macOS 27, Bazel 9.2.0. Bazel pin includes SHA-256 `dd466352a3e4d3581b8898740ee1ff208866ccbe25f8d367c5dcb950219587e6`. `Telegram/BUILD` sets minimum iOS to 15.0. Availability of a matching cloud machine has not been verified. Do not use version-check overrides as evidence of compatibility.

## Own configuration

On a macOS machine matching the pins, work inside Telegram-iOS. Copy `build-system/template_minimal_development_configuration.json` to an ignored local configuration. Set your own bundle_id, api_id/api_hash (https://my.telegram.org/apps), and team_id. Never commit credentials, certificates or profiles. Keep extension bundle IDs, app groups and entitlements consistent with your own identity. APNs and distribution capabilities require separate validation.

Upstream project-generation command, with local placeholders:

```sh
python3 build-system/Make/Make.py \
  --cacheDir="$HOME/telegram-bazel-cache" \
  generateProject \
  --configurationPath=/absolute/path/own-development.json \
  --xcodeManagedCodesigning
```

Upstream device release build pattern (not yet executed):

```sh
python3 build-system/Make/Make.py \
  --cacheDir="$HOME/telegram-bazel-cache" \
  build \
  --configurationPath=/absolute/path/own-distribution.json \
  --codesigningInformationPath=/absolute/path/own-signing-directory \
  --buildNumber=1 \
  --configuration=release_arm64
```

Follow README.md for profile layout and simulator provisioning options. Inspect all application/extension entitlements before configuring signing. Inspect `.gitmodules` and initialize dependencies if a pinned snapshot requires them. The current clone's `git submodule status` returned no entries; many directories named submodules are ordinary tracked source trees.

## Windows and CI

Windows is the editing/orchestration environment. Compilation, simulator verification and signing run on macOS with Xcode. The CI workflow checks toolchain pins and reports available disk resources. This task uses the user's existing remote repository.

Before release: verify the produced arm64 device bundle, signature/profiles/entitlements, install on the target iPhone, exercise real authentication and messaging, and record artifact hash plus test results. An unsigned archive or simulator bundle is not a verified installable IPA.
