#!/usr/bin/env python3
"""Build layered Icon Composer variants from the existing AyuBlue logo; requires Pillow."""
import argparse
import json
import math
from pathlib import Path
from PIL import Image, ImageChops, ImageFilter


def generate(source: Path) -> None:
    root = source / "Telegram/Telegram-iOS"
    original = Image.open(root / "AyuBlue.icon/Assets/AyuGram.png").convert("RGB").resize((1024, 1024), Image.Resampling.LANCZOS)
    # The supplied logo is white on blue. Minimum RGB isolates its original silhouette,
    # including the airplane cutouts, without introducing another logo drawing.
    red, green, blue = original.split()
    minimum = ImageChops.darker(ImageChops.darker(red, green), blue)
    mask = minimum.point(lambda value: max(0, min(255, (value - 80) * 255 // 160)))
    edge = ImageChops.subtract(mask, mask.filter(ImageFilter.MinFilter(5)))
    for name, preview, dark in [("AyuGlassBlue", "GlassBlue", False), ("AyuGlassGraphite", "GlassGraphite", True)]:
        folder = root / (name + ".icon")
        (folder / "Assets").mkdir(parents=True, exist_ok=True)
        background = Image.new("RGB", original.size)
        pixels = []
        for y in range(1024):
            for x in range(1024):
                glow = math.exp(-(((x / 1024 - .24) / .8) ** 2 + ((y / 1024 - .10) / .65) ** 2))
                ribbon = math.exp(-((x / 1024 + y / 1024 * .48 - .7) / .21) ** 2)
                if dark:
                    color = (13 + 44 * glow + 13 * ribbon, 17 + 49 * glow + 14 * ribbon, 26 + 64 * glow + 18 * ribbon)
                else:
                    color = (12 + 30 * glow + 8 * ribbon, 27 + 99 * glow + 18 * ribbon, 83 + 137 * glow + 24 * ribbon)
                pixels.append(tuple(min(255, round(c)) for c in color))
        background.putdata(pixels)
        background.save(folder / "Assets/Background.png", optimize=True)
        foreground = Image.new("RGBA", original.size, (229, 242, 255, 0))
        alpha = Image.new("L", original.size)
        alpha.putdata([round(184 + 62 * (1 - y / 1023)) for y in range(1024) for _ in range(1024)])
        alpha = ImageChops.multiply(mask, alpha)
        foreground.putalpha(ImageChops.lighter(alpha, edge))
        foreground.save(folder / "Assets/Logo.png", optimize=True)
        manifest = {
            "fill": {"automatic-gradient": "extended-srgb:0.04,0.08,0.18,1.00000"},
            "groups": [
                {"layers": [{"image-name": "Background.png", "name": "Backdrop", "glass": False}], "shadow": {"kind": "neutral", "opacity": 0}, "specular": False},
                {"layers": [{"image-name": "Logo.png", "name": "VoidGram glass", "glass": True}], "lighting": "combined", "shadow": {"kind": "neutral", "opacity": .35}, "specular": True, "translucency": {"enabled": True, "value": .85}},
            ],
            "supported-platforms": {"squares": "shared"},
        }
        (folder / "icon.json").write_text(json.dumps(manifest, indent=2) + "\n")
        imageset = source / "submodules/TelegramUI/Images.xcassets/AyuGram" / (preview + ".imageset")
        imageset.mkdir(parents=True, exist_ok=True)
        Image.alpha_composite(background.convert("RGBA"), foreground).convert("RGB").resize((256, 256), Image.Resampling.LANCZOS).save(imageset / "AyuGram.png")
        (imageset / "Contents.json").write_text(json.dumps({"images": [{"idiom": "universal", "filename": "AyuGram.png"}], "info": {"author": "xcode", "version": 1}}, indent=2) + "\n")
        print(name + ": layered .icon + settings preview")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    generate(parser.parse_args().source.resolve())
