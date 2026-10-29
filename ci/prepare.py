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
]
for patch in patches:
    subprocess.run(["git", "apply", "--recount", "--check", str(patch)], cwd=source, check=True)
    subprocess.run(["git", "apply", "--recount", str(patch)], cwd=source, check=True)

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

missing = missing_port_sources(source)
if missing:
    raise SystemExit("Port patch is missing required native source files:\n" + "\n".join(missing))
print("Applied native AyuGram changes to " + actual)
