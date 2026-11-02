# Settings icons and resource optimization

The new final patch, `patches/ayugram-settings-optimization.patch`, applies after
`ayugram-big-update.patch` through `ci/prepare.py`.

## Behaviour

- Appearance → Icons & badge has **Monochrome settings icons**. Its default is off,
  including for existing installations. The saved choice uses the existing app
  defaults store. Monochrome icons have white vector glyphs on a `#333333` tile.
- Switching refreshes the icon page and its open category/root pages. Row equality
  now includes the image, so an icon change causes a list update. Settings search
  exposes the switch and the icon page as well.
- Editable palette swatches retain their colours in either mode.
- The category row for Local Premium uses Telegram's `Item List/Icons/Premium`;
  local notifications use Telegram's notification glyph. Plugins, media archive
  and filters reuse the existing AyuGram vector assets.
- “Theme & background” now reads “Tabs, glass & effects”, matching its controls.
  “Customization” reads “Themes, colours & badges”, matching its palettes and
  colour controls. Category links, page titles and search labels agree in Russian
  and English. The misleading “Profile & settings” link now describes its message
  labels and MessageShot settings; the calls subtitle lists supported controls.

## Work removed

Settings icon rasterizations use a thread-safe NSCache keyed by glyph, colour,
dimensions and display scale, with a 256-entry / 4 MiB eviction budget. Opening the
root page requests 10 link icons instead of 36; category icons remain available.
The same rasterization is reused when rebuilding an unchanged list.

Three in-app logo previews are sized for their largest 100 pt use at 3x. Their PNG
resources total **4,188,615 → 223,145 bytes**. The original launcher artwork and all
alternate icon choices remain in the build. See `assets/branding/previews/README.md`.

Python resource packaging now copies existing IPA entries in 1 MiB chunks and
uses DEFLATE level 9, preserving each bundle file's contents and permissions.
`ci/ipa_archive.py INPUT OUTPUT` can also recompress an existing IPA into a separate
file, compare SHA-256 hashes of every entry, and atomically publish the result. It
keeps the smaller original encoding if recompression would grow the file.

The build manifest and job summary now report IPA, unpacked bundle and compiled
asset-catalog sizes so the next native build can be compared with its predecessor.

## Verification on Linux, 2026-11-02

- 84 Python tests passed, including bounded-memory copying, byte preservation,
  executable/symlink metadata, failure recovery and Python framework packaging.
- Applied the complete patch chain from scratch to pinned Telegram commit
  `fb0e62ba8a147f0821da6aa63c09da7d79a10111` in a separate worktree. All ten changed
  Swift files matched the development tree; required source and import/dependency
  contracts passed. The three previews, 3x declarations and full-size launcher
  hashes were checked against the source manifest.
- Recompressed the existing build 116 IPA: **163,295,306 → 163,099,328 bytes**,
  saving **195,978 bytes (0.12%)**. All **1,782** entry contents had identical
  SHA-256 hashes. This is the old build; it does not contain the new UI or previews.
- Reviewed the generated logo asset. No simulator screenshot or animation recording
  was produced on this host.

## Pending macOS validation

This Linux host has neither Xcode nor the iOS SDK. Swift type checking, the new
`testSettingsIconStyleAndCache` XCTest, the native release build and simulator/device
checks have **not** run. No new IPA containing these changes has been built, and no
runtime frame-rate gain or final IPA reduction is claimed.

On the pinned macOS/Xcode runner, run the normal source checks and release build.
Run the settings XCTest target, including the icon test. Record the following UI
paths as required by upstream `AGENTS.md` and inspect labelled frames:

1. Russian and English, light and dark: open Appearance, each renamed destination
   and the settings search result; the title must match the linked screen.
2. Turn monochrome on and off. The glyphs and tile sizes stay fixed, all visible
   row icons update, and returning to the category/root page shows the same style.
   Relaunch preserves the choice; a clean installation starts coloured.
3. Check Premium, Ghost Mode+, plugins and colour swatches. Glyphs must be visible
   and swatches must still show their editable colour.
4. Check the settings logo, app-icon picker, native theme picker and update screen
   at 2x and 3x, including iPad and large text: no cropping or soft edges.
5. Compare the new manifest sizes and use Instruments while repeatedly opening
   categories and changing settings. Verify ordinary messaging and existing
   settings still behave as before.
