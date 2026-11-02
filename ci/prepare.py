#!/usr/bin/env python3
"""Apply the native port patches only to their pinned upstream source tree."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
from port_sources import missing_port_sources

parser = argparse.ArgumentParser()
parser.add_argument("source", type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
source = args.source.resolve()
pin = json.loads((root / "upstream.json").read_text())
actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
if actual != pin["commit"]:
    raise SystemExit("Upstream commit differs from upstream.json; refusing to apply a mismatched patch")
patches = [
    root / "patches" / "ayugram-ghost-mode.patch",
    root / "patches" / "ayugram-custom-features.patch",
    root / "patches" / "ayugram-followup-features.patch",
    root / "patches" / "ayugram-developer-badges.patch",
    root / "patches" / "ayugram-interface-controls.patch",
    root / "patches" / "ayugram-badge-alignment.patch",
    root / "patches" / "ayugram-haptics-material.patch",
    root / "patches" / "ayugram-attachment-menu-motion.patch",
    root / "patches" / "ayugram-lyrics-word-sync.patch",
    root / "patches" / "ayugram-formatting-toolbar-layout.patch",
    root / "patches" / "ayugram-fixed-leading-badges.patch",
    root / "patches" / "ayugram-plugin-dialogs-keyboard.patch",
    root / "patches" / "ayugram-music-reference.patch",
    root / "patches" / "ayugram-peer-search.patch",
    root / "patches" / "ayugram-player-toolbar-refinements.patch",
    root / "patches" / "ayugram-music-inline-queue.patch",
    root / "patches" / "ayugram-fixed-player-fades.patch",
    root / "patches" / "ayugram-expanded-lyrics.patch",
    root / "patches" / "ayugram-big-update.patch",
    root / "patches" / "ayugram-settings-optimization.patch",
]
for patch in patches:
    subprocess.run(["git", "apply", "--recount", "--check", str(patch)], cwd=source, check=True)
    subprocess.run(["git", "apply", "--recount", str(patch)], cwd=source, check=True)

# The largest in-app logo is 100 pt (AyuSettingsHeaderItem); the icon picker is
# at most 72 pt. Ship 300 px previews for 3x screens instead of decoding 1254 px
# launcher artwork in these rows. Icon Composer keeps its full-size originals.
for name in ("Brand", "Blue", "Graphite"):
    preview = root / "assets/branding/previews" / (name + ".png")
    image_set = source / "submodules/TelegramUI/Images.xcassets/AyuGram" / (name + ".imageset")
    shutil.copy2(preview, image_set / "AyuGram.png")
    contents_path = image_set / "Contents.json"
    contents = json.loads(contents_path.read_text())
    contents["images"][0]["scale"] = "3x"
    contents_path.write_text(json.dumps(contents, indent=2) + "\n")

for badge_name in ("ExteraBadge", "ExteraDeveloperBadge"):
    badge_src = root / "assets" / "branding" / f"{badge_name}.imageset"
    if badge_src.is_dir():
        badge_dst = source / "submodules" / "TelegramUI" / "Images.xcassets" / "AyuGram" / f"{badge_name}.imageset"
        badge_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(badge_src, badge_dst, dirs_exist_ok=True)

app_badge_src = root / "assets" / "branding" / "AppBadge@3x.png"
if app_badge_src.is_file():
    app_badge_dst = source / "submodules" / "TelegramUI" / "Images.xcassets" / "Components" / "AppBadge.imageset" / "AppBadge@3x.png"
    app_badge_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(app_badge_src, app_badge_dst)

# TelegramUIResources includes Resources/**/* in the application bundle.
font_src = root / "assets" / "fonts" / "YSMusic-HeadlineBold.ttf"
font_dst = source / "submodules" / "TelegramUI" / "Resources" / font_src.name
font_dst.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(font_src, font_dst)

# AyuGram settings pull-down easter egg image, bundled the same way.
eblan_src = root / "assets" / "easter" / "AyuEblan.png"
if eblan_src.is_file():
    shutil.copy2(eblan_src, source / "submodules" / "TelegramUI" / "Resources" / eblan_src.name)

missing = missing_port_sources(source)
if missing:
    raise SystemExit("Port patch is missing required native source files:\n" + "\n".join(missing))
print("Applied native AyuGram changes to " + actual)
