"""VoidGram versions of AyuGram's twelve classic icon styles, with the VoidGram mark.

Run from this folder: python3 styles.py writes classic/<Name>.png at 1024 px (needs rsvg-convert)."""
import mark, subprocess, os
from PIL import Image, ImageChops

SIZE = 1024
LEFT, RIGHT = mark.paths["blades"].split(" M")
RIGHT = "M" + RIGHT

def icon(bg, left, right, core, defs="", extra="", scale=0.68, face=False):
    w = mark.bbox[2] - mark.bbox[0]; h = mark.bbox[3] - mark.bbox[1]
    k = SIZE * scale / w
    tx = SIZE / 2 - (mark.bbox[0] + w / 2) * k; ty = SIZE / 2 - (mark.bbox[1] + h / 2) * k
    body = '<rect width="%d" height="%d" fill="%s"/>' % (SIZE, SIZE, bg)
    g = '<g transform="translate(%.2f %.2f) scale(%.5f)"><path d="%s" fill="%s"/><path d="%s" fill="%s"/><path d="%s" fill="%s"/>%s</g>' % (
        tx, ty, k, LEFT, left, RIGHT, right, mark.paths["core"], core, face_marks() if face else "")
    return '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d"><defs>%s</defs>%s%s%s</svg>' % (SIZE, SIZE, defs, body, g, extra)

def face_marks():
    # Cat ears on the blades' tips and a small face on the core, in mark units.
    ears = ('<path d="M492 330 L520 205 L542 300 Z" fill="#FFFFFF"/><path d="M645 330 L617 205 L595 300 Z" fill="#FFFFFF"/>'
            '<path d="M508 300 L521 240 L532 290 Z" fill="#FF8FB8"/><path d="M629 300 L616 240 L605 290 Z" fill="#FF8FB8"/>')
    eyes = '<circle cx="541" cy="688" r="15" fill="#2B2242"/><circle cx="596" cy="688" r="15" fill="#2B2242"/><circle cx="546" cy="683" r="5" fill="#FFFFFF"/><circle cx="601" cy="683" r="5" fill="#FFFFFF"/>'
    blush = '<ellipse cx="519" cy="718" rx="14" ry="8" fill="#FF8FB8"/><ellipse cx="618" cy="718" rx="14" ry="8" fill="#FF8FB8"/>'
    mouth = '<path d="M556 716 q6 8 12.5 0 q6.5 8 12.5 0" stroke="#2B2242" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
    return ears + eyes + blush + mouth

def grad(id, stops, x2=1, y2=1):
    # Across the whole mark, in its own units, so every blade shares one gradient.
    s = "".join('<stop offset="%s" stop-color="%s"/>' % st for st in stops)
    x0, y0, x1, y1 = mark.bbox
    return '<linearGradient id="%s" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" gradientUnits="userSpaceOnUse">%s</linearGradient>' % (
        id, x0, y0, x0 + (x1 - x0) * x2, y0 + (y1 - y0) * y2, s)

STYLES = {
    "Default": icon("#2B2242", "#F4F2FA", "#B9A3FF", "#E9E4F7"),
    "Alt": icon("#9C7CFF", "#FFFFFF", "#FFFFFF", "#FFFFFF"),
    "Discord": icon("#5865F2", "#FFFFFF", "#FFFFFF", "#FFFFFF"),
    "Spotify": icon("#121212", "#1ED760", "#1ED760", "#1ED760"),
    "Extera": icon("#E53935", "url(#fade)", "url(#fade2)", "#FFFFFF",
                   defs=grad("fade", (("0", "#FFFFFF"), ("1", "#FFD2D0")), 0, 1) + grad("fade2", (("0", "#FFE2E1"), ("1", "#FFB3AF")), 0, 1)),
    "Nothing": icon("#F4F4F4", "#111111", "#D71921", "#111111"),
    "Bard": icon("#FFFFFF", "url(#bard)", "url(#bard)", "url(#bard)",
                 defs=grad("bard", (("0", "#4285F4"), ("0.55", "#9B72CB"), ("1", "#F28B54")))),
    "Yaplus": icon("#FBF4F8", "url(#ya)", "url(#ya)", "url(#ya)",
                   defs=grad("ya", (("0", "#FF5F45"), ("0.5", "#E0309A"), ("1", "#7B4BFF")))),
    "Win95": None,  # pixel art, drawn below
    # Chibi is the owner's snow leopard artwork (classic/Chibi.png), not drawn here.
    "Chibi2": icon("#C9B8FF", "#FFFFFF", "#FFFFFF", "#FFFFFF", face=True),
    "Extera2": icon("#E53935", "#FFFFFF", "#FFFFFF", "#FFC9C6"),
}

def render(svg, path):
    open("style.svg", "w").write(svg)
    subprocess.run(["rsvg-convert", "style.svg", "-o", path], check=True)

def pixelate(path, cells):
    im = Image.open(path).convert("RGB")
    im.resize((cells, cells), Image.BOX).resize((SIZE, SIZE), Image.NEAREST).save(path, optimize=True)

os.makedirs("classic", exist_ok=True)
for name, svg in STYLES.items():
    if svg is None:
        # Windows 95: silver blades with a white top-left and dark bottom-right bevel on teal, pixelated.
        teal = (0, 128, 128)
        render(icon("#008080", "#008080", "#008080", "#008080"), "classic/_background.png")
        render(icon("#008080", "#FFFFFF", "#FFFFFF", "#FFFFFF"), "classic/_shape.png")
        shape = ImageChops.difference(Image.open("classic/_shape.png").convert("RGB"), Image.new("RGB", (SIZE, SIZE), teal))
        shape = shape.convert("L").point(lambda v: 255 if v > 40 else 0)
        out = Image.open("classic/_background.png").convert("RGB")
        out.paste((255, 255, 255), (-14, -14), shape)
        out.paste((64, 64, 64), (14, 14), shape)
        out.paste((192, 192, 192), (0, 0), shape)
        out.save("classic/Win95.png")
        pixelate("classic/Win95.png", 64)
        for f in ("_background", "_shape"):
            os.remove("classic/%s.png" % f)
        continue
    render(svg, "classic/%s.png" % name)
    Image.open("classic/%s.png" % name).convert("RGB").save("classic/%s.png" % name, optimize=True)
for name in ("Chibi2",):
    pixelate("classic/%s.png" % name, 128)
