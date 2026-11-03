"""VoidGram mark: two 60° blades split by a vertical gap, a small triangle between them."""
import math, sys

S = 0.5714  # tan 30°: the blades' edges run at 60° to the base

def fillet_path(points, radii):
    n = len(points); out = []
    for i in range(n):
        p = points[i]; a = points[i - 1]; b = points[(i + 1) % n]; r = radii[i]
        u = ((a[0]-p[0]), (a[1]-p[1])); lu = math.hypot(*u); u = (u[0]/lu, u[1]/lu)
        v = ((b[0]-p[0]), (b[1]-p[1])); lv = math.hypot(*v); v = (v[0]/lv, v[1]/lv)
        ang = math.acos(max(-1, min(1, u[0]*v[0] + u[1]*v[1])))
        d = r / math.tan(ang / 2)
        p1 = (p[0]+u[0]*d, p[1]+u[1]*d); p2 = (p[0]+v[0]*d, p[1]+v[1]*d)
        cross = u[0]*v[1] - u[1]*v[0]
        sweep = 1 if cross < 0 else 0
        out.append((p1, p2, r, sweep))
    s = "M%.2f %.2f " % out[0][0]
    for i, (p1, p2, r, sweep) in enumerate(out):
        if i: s += "L%.2f %.2f " % p1
        s += "A%.2f %.2f 0 0 %d %.2f %.2f " % (r, r, sweep, p2[0], p2[1])
    return s + "Z"

cx, base, gap = 568.5, 750.0, 26.5
apex = 231.0
outer_bottom = cx - gap - (base - apex) * S       # outer blade edge meets the base
inner_top = 529.5
inner_bottom = cx - gap - (base - inner_top) * S
left = [(cx - gap, apex), (cx - gap, inner_top), (inner_bottom, base), (outer_bottom, base)]
left_r = [4, 4, 4, 34]
right = [(2*cx - x, y) for x, y in reversed(left)]
right_r = list(reversed(left_r))
tri_apex = 572.0
half = (base - tri_apex) * S
tri = [(cx, tri_apex), (cx + half, base), (cx - half, base)]
tri_r = [9, 9, 9]

paths = {"blades": fillet_path(left, left_r) + " " + fillet_path(right, right_r), "core": fillet_path(tri, tri_r)}
# mark bounding box in these units
bbox = (outer_bottom, apex, 2*cx - outer_bottom, base)

def svg(size, bg=None, blade="#FFFFFF", core="#BBBBBB", scale=0.66, dy=0.0):
    w = bbox[2] - bbox[0]; h = bbox[3] - bbox[1]
    k = size * scale / w
    tx = size/2 - (bbox[0] + w/2) * k; ty = size/2 - (bbox[1] + h/2) * k + dy*size
    defs = ""; rect = ""
    if bg:
        defs = '<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient></defs>' % bg
        rect = '<rect width="%d" height="%d" fill="url(#g)"/>' % (size, size)
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">%s%s'
            '<g transform="translate(%.3f %.3f) scale(%.5f)"><path d="%s" fill="%s"/><path d="%s" fill="%s"/></g></svg>'
            % (size, size, size, size, defs, rect, tx, ty, k, paths["blades"], blade, paths["core"], core))

if __name__ == "__main__":
    print(svg(1148, ("#3B3B3B", "#070707")))
