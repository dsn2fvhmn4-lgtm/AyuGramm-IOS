"""The main VoidGram icons, from mark.py. Run from this folder (needs rsvg-convert and Pillow):
Brand, Blue and Graphite (light) at 1254 px, the two glass icons' backdrop and glass logo at
1024 px, and the in-app previews (300 px, 256 px for glass)."""
import subprocess
from PIL import Image
import mark

def render(svg, path):
    open("icon.svg", "w").write(svg)
    subprocess.run(["rsvg-convert", "icon.svg", "-o", path], check=True)

def flatten(path):
    Image.open(path).convert("RGB").save(path, optimize=True)

FULL = {
    "Brand": (("#3B3B3B", "#070707"), "#FFFFFF", "#BBBBBB"),
    "Blue": (("#2B4C9B", "#0A1636"), "#FFFFFF", "#A9BCEB"),
    "Graphite": (("#F4F4F4", "#C7C7C7"), "#121212", "#6F6F6F"),
}
for name, (background, blade, core) in FULL.items():
    render(mark.svg(1254, background, blade, core), name + ".png")
    flatten(name + ".png")
    Image.open(name + ".png").resize((300, 300), Image.LANCZOS).save("../previews/%s.png" % name, optimize=True)

GLASS = {"GlassBlue": ("#2B4C9B", "#0A1636"), "GlassGraphite": ("#4A4A4A", "#0B0B0B")}
for name, background in GLASS.items():
    render(mark.svg(1024, background, scale=0.0001), name + "-Background.png")
    flatten(name + "-Background.png")
    render(mark.svg(1024, None, "#FFFFFF", "#D6D6D6"), name + "-Logo.png")
    render(mark.svg(256, background), name + "-Preview.png")
    flatten(name + "-Preview.png")

render(mark.svg(1254, None, scale=0.8), "VoidGram-mark.png")
open("VoidGram-mark.svg", "w").write(mark.svg(1024, None, scale=0.8))
open("VoidGram-icon.svg", "w").write(mark.svg(1024, ("#3B3B3B", "#070707")))
