"""
DODECA CORE - generates a regular dodecahedron (12 pentagon plates) for GeckoLib / Blockbench:

  dodeca_core.bbmodel          editable in Blockbench (animated_entity_model, same format as meteor_v2.bbmodel)
  dodeca_core.png              texture: 12 tiles of 64x64 (rock + lava edges + cracks), pentagon on transparent square
  dodeca_core_glowmask.png     emissive lava (GeckoLib auto-glow)
  apercu_dodecaedre.png        ray-traced preview built from the same plate data

Each face = one very thin cube (a square plate) rotated so that its up face looks outward; the pentagon shape comes
from the transparent corners of the texture. Edit DIAMETER_BLOCKS to resize (odd = centred on a block).

Rotation convention (cube rotation in Blockbench): R = Rz(rz) * Ry(ry) * Rx(rx), degrees, pivot = cube centre.
If the faces do not meet in Blockbench, run with  --flip  (negates rx and ry) and re-open.
Run:  python dodeca_core_gen.py [--flip]
"""
import base64, io, json, math, random, sys, uuid
import numpy as np
from PIL import Image

DIAMETER_BLOCKS = 7           # circumscribed sphere diameter, in blocks (16 model units = 1 block)
THICK = 0.4                   # plate thickness (model units)
TILE = 64                     # px per face tile
COLS, ROWS = 4, 3
FLIP = "--flip" in sys.argv
PHI = (1 + 5 ** 0.5) / 2
rng = random.Random(0xD0DECA)

def uid(): return str(uuid.UUID(int=rng.getrandbits(128)))

# ------------------------------------------------------------------ geometry
V = []
for sx in (-1, 1):
    for sy in (-1, 1):
        for sz in (-1, 1): V.append((sx, sy, sz))
for s1 in (-1, 1):
    for s2 in (-1, 1):
        V += [(0, s1 / PHI, s2 * PHI), (s1 / PHI, s2 * PHI, 0), (s2 * PHI, 0, s1 / PHI)]
V = np.array(V, float)                      # 20 vertices, circumradius sqrt(3)
R_WORLD = DIAMETER_BLOCKS / 2 * 16
S = R_WORLD / math.sqrt(3)
V = V * S
EDGE = 2 / PHI * S

def candidate_normals(a, b):
    out = []
    for s1 in (-1, 1):
        for s2 in (-1, 1):
            out += [(0, s1 * a, s2 * b), (s1 * a, s2 * b, 0), (s2 * b, 0, s1 * a)]
    return np.array(out, float)

best = None
for a, b in ((1, PHI), (PHI, 1)):
    N = candidate_normals(a, b); ok = True; faces = []
    for n in N:
        n = n / np.linalg.norm(n); d = V @ n; m = d.max()
        idx = np.where(d > m - 1e-6)[0]
        if len(idx) != 5: ok = False; break
        faces.append((n, idx))
    if ok: best = faces; break
assert best, "no dodecahedron faces found"

R5 = EDGE / (2 * math.sin(math.radians(36)))          # pentagon circumradius (world)
RP_PX = 31.0                                          # pentagon circumradius in the tile (px)
L = R5 * TILE / RP_PX                                 # plate side = tile width, so the textured pentagon has circumradius R5

plates = []
for n, idx in best:
    pts = V[idx]; c = pts.mean(axis=0)
    d0 = pts[0] - c; d0 -= n * (d0 @ n); d0 /= np.linalg.norm(d0)      # direction to a pentagon vertex
    Z = -d0; Y = n; X = np.cross(Y, Z)
    Rm = np.stack([X, Y, Z], axis=1)
    assert abs(np.linalg.det(Rm) - 1) < 1e-6
    plates.append(dict(n=n, c=c, X=X, Y=Y, Z=Z, R=Rm, pts=pts))

def euler_zyx(Rm):
    sy = max(-1, min(1, -Rm[2, 0])); ry = math.asin(sy); cy = math.cos(ry)
    if abs(cy) > 1e-6:
        rx = math.atan2(Rm[2, 1], Rm[2, 2]); rz = math.atan2(Rm[1, 0], Rm[0, 0])
    else:
        rx = math.atan2(-Rm[1, 2], Rm[1, 1]); rz = 0.0
    return [math.degrees(rx), math.degrees(ry), math.degrees(rz)]

def rot_from_euler(e):
    rx, ry, rz = [math.radians(v) for v in e]
    Rx = np.array([[1, 0, 0], [0, math.cos(rx), -math.sin(rx)], [0, math.sin(rx), math.cos(rx)]])
    Ry = np.array([[math.cos(ry), 0, math.sin(ry)], [0, 1, 0], [-math.sin(ry), 0, math.cos(ry)]])
    Rz = np.array([[math.cos(rz), -math.sin(rz), 0], [math.sin(rz), math.cos(rz), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx

for p in plates:
    e = [round(v, 4) for v in euler_zyx(p["R"])]
    assert np.abs(rot_from_euler(e) - p["R"]).max() < 1e-5, "euler round trip"
    p["euler"] = [-e[0], -e[1], e[2]] if FLIP else e

# check: texture pentagon vertices land on the true vertices
for p in plates:
    for k in range(5):
        a = math.radians(-90 + 72 * k)
        lx = RP_PX * math.cos(a) / TILE * L; lz = RP_PX * math.sin(a) / TILE * L
        w = p["c"] + lx * p["X"] + lz * p["Z"]
        assert np.min(np.linalg.norm(p["pts"] - w, axis=1)) < 0.02 * R_WORLD, "pentagon mismatch"

# ------------------------------------------------------------------ textures
def edge_dist(px, py, cx, cy, Rp):
    verts = [(cx + Rp * math.cos(math.radians(-90 + 72 * k)), cy + Rp * math.sin(math.radians(-90 + 72 * k))) for k in range(5)]
    best = np.full(px.shape, 1e9)
    for k in range(5):
        x0, y0 = verts[k]; x1, y1 = verts[(k + 1) % 5]
        ex, ey = x1 - x0, y1 - y0; ln = math.hypot(ex, ey)
        # inward normal (polygon is clockwise in image coords with y down -> use cross sign test with centre)
        nx, ny = -ey / ln, ex / ln
        if (cx - x0) * nx + (cy - y0) * ny < 0: nx, ny = -nx, -ny
        best = np.minimum(best, (px - x0) * nx + (py - y0) * ny)
    return best, verts

def make_tile(seed):
    """Cristal translucide : facettes sombres semi-transparentes, inclusions lumineuses, arêtes chaudes."""
    r = random.Random(seed)
    cx = cy = TILE / 2
    yy, xx = np.mgrid[0:TILE, 0:TILE]; px, py = xx + 0.5, yy + 0.5
    d, verts = edge_dist(px, py, cx, cy, RP_PX)
    inside = d >= 0
    dist = np.hypot(px - cx, py - cy) / RP_PX
    deg = (np.degrees(np.arctan2(py - cy, px - cx)) + 90) % 360
    facet = (deg // 72).astype(int) % 5
    shade = np.array([0.80 + 0.45 * r.random() for _ in range(5)])
    sh = shade[facet]
    # fond : violet profond, plus clair vers les arêtes de facettes (effet cristal), cœur chaud
    base = np.zeros((TILE, TILE, 3))
    base[..., 0] = 34 + 40 * sh; base[..., 1] = 14 + 16 * sh; base[..., 2] = 78 + 70 * sh
    core = np.clip(1 - dist / 0.75, 0, 1) ** 1.6
    base += core[..., None] * np.array([150, 28, 70])
    # fines lignes de facettes (rayons du centre vers les sommets)
    fdist = np.minimum(np.abs(((deg % 72) - 0)), np.abs(72 - (deg % 72)))   # distance angulaire aux rayons
    ray = np.clip(1 - (fdist * np.pi / 180 * dist * RP_PX) / 0.9, 0, 1)
    base += ray[..., None] * np.array([70, 45, 110]) * 0.6
    alpha = np.where(inside, 112 + 38 * sh + 70 * core + 40 * ray, 0.0)
    col = base.copy(); gl = np.zeros((TILE, TILE, 3)); ga = np.zeros((TILE, TILE))
    gl += core[..., None] * np.array([210, 50, 120]) * 0.22           # lueur interne douce
    def put(x, y, c, a, g=None, ga_=None):
        xi, yi = int(x), int(y)
        if 0 <= xi < TILE and 0 <= yi < TILE and inside[yi, xi] and d[yi, xi] > 2.2:
            col[yi, xi] = c; alpha[yi, xi] = max(alpha[yi, xi], a)
            if g is not None: gl[yi, xi] = g
    def seg(x0, y0, x1, y1, c, a, g):
        n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        for i in range(n + 1):
            t = i / n; put(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, c, a, g)
    # inclusions : lignes rose-blanc depuis le cœur vers 2-3 sommets, plus quelques fractures courtes
    for k in r.sample(range(5), 3):
        vx, vy = verts[k]; seg(cx + r.uniform(-2, 2), cy + r.uniform(-2, 2), cx + (vx - cx) * 0.78, cy + (vy - cy) * 0.78,
                               [255, 175, 205], 235, [255, 105, 150])
    for _ in range(4):
        x0, y0 = cx + r.uniform(-16, 16), cy + r.uniform(-16, 16); an = r.uniform(0, 6.283); ln = r.uniform(5, 10)
        seg(x0, y0, x0 + math.cos(an) * ln, y0 + math.sin(an) * ln, [235, 205, 255], 190, [190, 140, 255])
    # reflet spéculaire diagonal sur une facette
    kf_ = r.randrange(5)
    sp = inside & (facet == kf_) & (np.abs((px - py) - r.uniform(-6, 6)) < 1.6) & (d > 4)
    col[sp] = [235, 235, 255]; alpha[sp] = 210; gl[sp] = [150, 150, 210]
    # étincelles
    for _ in range(14):
        put(r.randrange(TILE), r.randrange(TILE), [255, 245, 255], 255, [255, 230, 255])
    # arêtes chaudes : cœur blanc-chaud puis rose-orangé puis carmin qui se fond dans le cristal
    m1 = inside & (d < 0.7); m2 = inside & (d >= 0.7) & (d < 1.6); m3 = inside & (d >= 1.6) & (d < 2.6); m4 = inside & (d >= 2.6) & (d < 4.2)
    col[m1] = [255, 240, 225]; alpha[m1] = 255; gl[m1] = [255, 225, 200]
    col[m2] = [255, 150, 130]; alpha[m2] = 255; gl[m2] = [255, 140, 120]
    col[m3] = [215, 55, 105]; alpha[m3] = 250; gl[m3] = [200, 50, 100]
    k4 = np.clip((4.2 - d) / 1.6, 0, 1)
    col[m4] = col[m4] * (1 - 0.6 * k4[m4][:, None]) + np.array([170, 40, 100]) * 0.6 * k4[m4][:, None]
    alpha[m4] = np.maximum(alpha[m4], 150 + 80 * k4[m4])
    gl[m4] = np.maximum(gl[m4], (np.array([200, 50, 110]) * 0.30 * k4[m4][:, None]))
    img = np.zeros((TILE, TILE, 4), np.uint8); glow = np.zeros((TILE, TILE, 4), np.uint8)
    img[..., :3] = np.clip(col, 0, 255).astype(np.uint8); img[..., 3] = np.clip(np.where(inside, alpha, 0), 0, 255).astype(np.uint8)
    glow[..., :3] = np.clip(gl, 0, 255).astype(np.uint8)
    glow[..., 3] = np.where(inside & (gl.sum(axis=2) > 14), 255, 0)
    return img, glow

TEX_W, TEX_H = COLS * TILE, ROWS * TILE
tex = np.zeros((TEX_H, TEX_W, 4), np.uint8); gmask = np.zeros((TEX_H, TEX_W, 4), np.uint8)
for i, p in enumerate(plates):
    cx0, cy0 = (i % COLS) * TILE, (i // COLS) * TILE
    t_img, t_glow = make_tile(1000 + i * 17)
    tex[cy0:cy0 + TILE, cx0:cx0 + TILE] = t_img; gmask[cy0:cy0 + TILE, cx0:cx0 + TILE] = t_glow
    p["uv"] = [cx0, cy0, cx0 + TILE, cy0 + TILE]
Image.fromarray(tex, "RGBA").save("dodeca_core.png"); Image.fromarray(gmask, "RGBA").save("dodeca_core_glowmask.png")
buf = io.BytesIO(); Image.fromarray(tex, "RGBA").save(buf, "PNG"); png_b64 = base64.b64encode(buf.getvalue()).decode()

# ------------------------------------------------------------------ bbmodel
elements = []
for i, p in enumerate(plates):
    c = p["c"]; h = L / 2
    off = {"texture": None, "uv": [0, 0, 0, 0]}
    faces = {k: dict(off) for k in ("north", "east", "south", "west")}
    faces["up"] = {"uv": p["uv"], "texture": 0}
    faces["down"] = {"uv": [p["uv"][2], p["uv"][1], p["uv"][0], p["uv"][3]], "texture": 0}
    elements.append({"name": f"face_{i}", "box_uv": False, "rescale": False, "locked": False, "render_order": "default",
        "allow_mirror_modeling": True,
        "from": [round(c[0] - h, 4), round(c[1] - THICK / 2, 4), round(c[2] - h, 4)],
        "to": [round(c[0] + h, 4), round(c[1] + THICK / 2, 4), round(c[2] + h, 4)],
        "autouv": 0, "color": i % 8, "origin": [round(float(v), 4) for v in c], "rotation": p["euler"],
        "faces": faces, "type": "cube", "uuid": uid()})
# each cube is centred on its own pivot (origin = face centre); its local +Y is the outward normal after rotation
root_uuid = uid()
def kf(channel, t, x, y, z, interp="linear"):
    return {"channel": channel, "data_points": [{"x": x, "y": y, "z": z}], "uuid": uid(), "time": t, "color": -1, "interpolation": interp}
anim = {"uuid": uid(), "name": "idle", "loop": "loop", "override": False, "length": 16.0, "snapping": 20, "selected": False,
        "anim_time_update": "", "blend_weight": "", "start_delay": "", "loop_delay": "",
        "animators": {root_uuid: {"name": "root", "type": "bone", "keyframes": [
            kf("rotation", 0.0, 0, 0, 0), kf("rotation", 16.0, 0, 360, 0),
            kf("position", 0.0, 0, 0, 0), kf("position", 4.0, 0, 2, 0, "catmullrom"), kf("position", 8.0, 0, 0, 0, "catmullrom"),
            kf("position", 12.0, 0, -2, 0, "catmullrom"), kf("position", 16.0, 0, 0, 0, "catmullrom")]}}}
bb = {"meta": {"format_version": "4.10", "model_format": "animated_entity_model", "box_uv": False},
      "name": "dodeca_core", "model_identifier": "dodeca_core", "modded_entity_flip_y": True, "visible_box": [8, 8, 0],
      "variable_placeholders": "", "variable_placeholder_buttons": [], "timeline_setups": [], "unhandled_root_fields": {},
      "resolution": {"width": TEX_W, "height": TEX_H}, "elements": elements,
      "groups": [{"name": "root", "origin": [0, 0, 0], "rotation": [0, 0, 0], "color": 0, "uuid": root_uuid, "export": True,
                  "mirror_uv": False, "isOpen": True, "locked": False, "visibility": True, "autouv": 0}],
      "outliner": [{"name": "root", "origin": [0, 0, 0], "color": 0, "uuid": root_uuid, "export": True, "mirror_uv": False,
                    "isOpen": True, "locked": False, "visibility": True, "autouv": 0, "children": [e["uuid"] for e in elements]}],
      "textures": [{"path": "", "name": "dodeca_core.png", "folder": "", "namespace": "lab", "id": "0", "group": "",
                    "width": TEX_W, "height": TEX_H, "uv_width": TEX_W, "uv_height": TEX_H, "particle": False,
                    "use_as_default": True, "layers_enabled": False, "sync_to_project": "", "render_mode": "default",
                    "render_sides": "auto", "frame_time": 1, "frame_order_type": "loop", "frame_order": "",
                    "frame_interpolate": False, "visible": True, "internal": True, "saved": True, "uuid": uid(),
                    "relative_path": "../src/main/resources/assets/lab/textures/entity/dodeca_core.png",
                    "source": "data:image/png;base64," + png_b64}],
      "animations": [anim]}
json.dump(bb, open("dodeca_core.bbmodel", "w"), separators=(",", ":"))

# ------------------------------------------------------------------ preview (ray traced from the same plates)
def render(az, el, size=560):
    az, el = math.radians(az), math.radians(el)
    w = -np.array([math.cos(el) * math.sin(az), math.sin(el), math.cos(el) * math.cos(az)])   # ray direction
    up0 = np.array([0, 1, 0]); right = np.cross(w, up0); right /= np.linalg.norm(right); up = np.cross(right, w)
    ext = R_WORLD * 1.25
    ii, jj = np.mgrid[0:size, 0:size]
    a = (jj / size - 0.5) * 2 * ext; b = (0.5 - ii / size) * 2 * ext
    o = -w * (R_WORLD * 3) + a[..., None] * right + b[..., None] * up
    zbuf = np.full((size, size), 1e9); rgb = np.zeros((size, size, 3)); gl = np.zeros((size, size, 3))
    light = np.array([0.35, 0.8, 0.5]); light /= np.linalg.norm(light)
    for i, p in enumerate(plates):
        n = p["n"]; den = n @ w
        if den >= -1e-6: continue
        r_in = n @ p["c"]; t = (r_in - o @ n) / den
        pt = o + t[..., None] * w
        rel = pt - p["c"]
        u = (rel @ p["X"] / L + 0.5) * TILE; v = (rel @ p["Z"] / L + 0.5) * TILE
        ok = (u >= 0) & (u < TILE) & (v >= 0) & (v < TILE)
        ui = np.clip(u.astype(int), 0, TILE - 1) + (i % COLS) * TILE; vi = np.clip(v.astype(int), 0, TILE - 1) + (i // COLS) * TILE
        al = tex[vi, ui, 3] > 0
        hit = ok & al & (t < zbuf)
        zbuf = np.where(hit, t, zbuf)
        shade = 0.45 + 0.55 * max(0, n @ light)
        rgb[hit] = tex[vi, ui, :3][hit] * shade
        gl[hit] = gmask[vi, ui, :3][hit] * (gmask[vi, ui, 3][hit] / 255.0)[..., None]
    bg = np.zeros((size, size, 3)); 
    yy, xx = np.mgrid[0:size, 0:size]; dd = np.hypot(xx - size / 2, yy - size / 2) / size
    bg[...] = np.array([14, 8, 24]) * (1 - dd[..., None] * 0.9)
    covered = zbuf < 1e8
    out = np.where(covered[..., None], rgb, bg)
    out = np.where(covered[..., None], np.maximum(out, gl), out)
    # bloom
    from PIL import ImageFilter
    g = Image.fromarray(np.clip(gl, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(7))
    out = out + np.asarray(g, float) * 0.55
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

views = [render(20, 18), render(145, 30), render(260, -15)]
sheet = Image.new("RGB", (560 * 3, 560))
for i, v in enumerate(views): sheet.paste(v, (560 * i, 0))
sheet.save("apercu_dodecaedre.png")
print("ok  L=%.2f R5=%.2f edge=%.2f  euler[0]=%s" % (L, R5, EDGE, plates[0]["euler"]))
