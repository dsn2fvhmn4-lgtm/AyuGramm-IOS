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
    root / "patches" / "ayugram-port-fixes.patch",
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

# VoidGram artwork replaces the launcher icons the patches ship: the full-bleed
# Icon Composer layers and the glass icons' backdrop and glass logo.
voidgram = root / "assets/branding/voidgram"
icons = source / "Telegram/Telegram-iOS"
for name, folder in (("Brand", "Telegram"), ("Blue", "AyuBlue"), ("Graphite", "AyuGraphite")):
    shutil.copy2(voidgram / (name + ".png"), icons / (folder + ".icon") / "Assets" / "AyuGram.png")
for name in ("GlassBlue", "GlassGraphite"):
    for layer in ("Background", "Logo"):
        shutil.copy2(voidgram / f"{name}-{layer}.png", icons / f"Ayu{name}.icon" / "Assets" / f"{layer}.png")
    shutil.copy2(voidgram / f"{name}-Preview.png", source / "submodules/TelegramUI/Images.xcassets/AyuGram" / f"{name}.imageset" / "AyuGram.png")

# The classic styles, redrawn with the VoidGram mark (assets/branding/voidgram/styles.py), and
# the MeiMei mascot in the Chibi slot. Each is one full-bleed layer on its own background colour;
# the picker shows a 300 px preview. Chibi2 is gone.
classic_fills = {
    "Default": "#2B2242", "Alt": "#9C7CFF", "Discord": "#5865F2", "Spotify": "#121212",
    "Extera": "#E53935", "Nothing": "#F4F4F4", "Bard": "#FFFFFF", "Yaplus": "#FBF4F8",
    "Win95": "#008080", "Chibi": "#2A282A", "Extera2": "#E53935",
}
classic_art = {"Chibi": "MeiMei"}
shutil.rmtree(icons / "AyuOriginalChibi2.icon")
shutil.rmtree(source / "submodules/TelegramUI/Images.xcassets/AyuGram/OriginalChibi2.imageset")
for name, fill in classic_fills.items():
    art = classic_art.get(name, name)
    bundle = icons / f"AyuOriginal{name}.icon"
    for old in (bundle / "Assets").iterdir():
        old.unlink()
    shutil.copy2(voidgram / "classic" / f"{art}.png", bundle / "Assets" / "VoidGram.png")
    icon = json.loads((bundle / "icon.json").read_text())
    red, green, blue = (int(fill[i:i + 2], 16) / 255 for i in (1, 3, 5))
    icon["fill"] = {"solid": f"extended-srgb:{red:.5f},{green:.5f},{blue:.5f},1.00000"}
    for group in icon["groups"]:
        for layer in group["layers"]:
            layer["image-name"] = "VoidGram.png"
            layer["name"] = f"VoidGram {art}"
            layer.pop("position", None)
    (bundle / "icon.json").write_text(json.dumps(icon, indent=2) + "\n")

    image_set = source / "submodules/TelegramUI/Images.xcassets/AyuGram" / f"Original{name}.imageset"
    for old in image_set.iterdir():
        old.unlink()
    shutil.copy2(voidgram / "classic" / f"{art}-Preview.png", image_set / "VoidGram.png")
    contents = {"images": [{"idiom": "universal", "filename": "VoidGram.png", "scale": "3x"}], "info": {"author": "xcode", "version": 1}}
    (image_set / "Contents.json").write_text(json.dumps(contents, indent=2) + "\n")

# iOS caches each alternate icon's flat rendering by its name, so MeiMei under the old
# AyuOriginalChibi name kept showing the chibi outside the clear appearance. A new name
# makes SpringBoard render it afresh.
(icons / "AyuOriginalChibi.icon").rename(icons / "AyuMeiMei.icon")

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

# VoidGram settings pull-down easter egg image, bundled the same way.
eblan_src = root / "assets" / "easter" / "AyuEblan.png"
if eblan_src.is_file():
    shutil.copy2(eblan_src, source / "submodules" / "TelegramUI" / "Resources" / eblan_src.name)

missing = missing_port_sources(source)
if missing:
    raise SystemExit("Port patch is missing required native source files:\n" + "\n".join(missing))
print("Applied native VoidGram changes to " + actual)
