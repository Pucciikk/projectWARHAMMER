"""
Общее для оружия: кривые анимации, руки-заглушки для просмотра, выгрузка клипов.

Оси как у машин: 1 м = 1 блок, Z вверх, ствол смотрит в -Y, правая сторона оружия при взгляде от стрелка — это -X.
Клип — функция pose(t) (t от 0 до 1): {кость: {"pos": (x, y, z) метры, "rot": (x, y, z) градусы}}.
Псевдокость "_view" двигает всё оружие целиком в кадре. Руки ("arm_r", "arm_l") рисует игра: кожа игрока, в Blender только заглушка.
"""
import json
import math
import os

GUN_ASSETS = r"C:/Users/Name/projectWARHAMMER/src/main/resources/assets/warpbound"
ARM_LEN, ARM_W = 0.62, 0.175     # заглушка руки: совпадает с масштабом ARM_SCALE в GunRenderer


def ease(k, kind="io"):
    if kind == "lin":
        return k
    if kind == "in":
        return k * k * k
    if kind == "out":
        return 1 - (1 - k) ** 3
    if kind == "snap":       # резкий рывок с лёгким перелётом: руки ставят магазин
        return 1 - (1 - k) ** 4 * math.cos(k * 7.0)
    return k * k * k * (k * (6 * k - 15) + 10)     # плавно на входе и выходе


def kf(t, keys):
    """Ключи [(время 0..1, значение или кортеж[, вид кривой])]: вид относится к участку, который заканчивается на этом ключе."""
    if t <= keys[0][0]:
        return keys[0][1]
    for a, b in zip(keys, keys[1:]):
        if t <= b[0]:
            kind = b[2] if len(b) > 2 else "io"
            k = ease((t - a[0]) / max(1e-6, b[0] - a[0]), kind)
            if isinstance(a[1], tuple):
                return tuple(u + (v - u) * k for u, v in zip(a[1], b[1]))
            return a[1] + (b[1] - a[1]) * k
    return keys[-1][1]


def add(*vs):
    return tuple(sum(c) for c in zip(*vs))


def scale(v, k):
    return tuple(c * k for c in v)


def arm(m, name, pivot):
    """Рука-заглушка: кисть в pivot, локоть уходит назад по +Y."""
    b = m.bone(name, pivot)
    w = ARM_W / 2
    x, y, z = pivot
    b.box((x - w, y, z - w), (x + w, y + ARM_LEN, z + w), "bone")
    b.box((x - w - 0.004, y, z - w - 0.004), (x + w + 0.004, y + 0.14, z + w + 0.004), "wax")
    return b


def small_seal(b, at, side):
    """Печать чистоты в размер оружия: стандартная из kit сделана для машин и здесь была бы как тарелка."""
    x, y, z = at
    b.lathe((x, y, z), [(0.028, 0), (0.03, side * 0.006), (0.022, side * 0.012)], 8, "wax", "X")
    for dy, ln in ((-0.012, 0.075), (0.01, 0.1)):
        b.box((x + side * 0.002, y + dy - 0.007, z - ln), (x + side * 0.005, y + dy + 0.007, z - 0.012), "parchment")


def locator(m, name, at):
    """Точка без геометрии: дуло, окно выброса."""
    return m.bone(name, at)


def export_clips(name, clips, fps=30):
    """assets/warpbound/gun_anim/<имя>.json: дорожки с равным шагом, игра читает их сама и сводит с отдачей и покачиванием."""
    out = {"fps": fps, "clips": {}}
    for clip, data in clips.items():
        length, fn = data["length"], data["pose"]
        steps = max(1, int(round(length * fps)))
        tracks = {}
        for i in range(steps + 1):
            for bone, st in fn(i / steps).items():
                tr = tracks.setdefault(bone, {"pos": [], "rot": []})
                tr["pos"].append([round(c, 4) for c in st.get("pos", (0, 0, 0))])
                tr["rot"].append([round(c, 3) for c in st.get("rot", (0, 0, 0))])
        out["clips"][clip] = {"length": length, "loop": data.get("loop", False), "tracks": tracks,
                              "events": [[round(a, 3), e] for a, e in data.get("events", [])]}
    path = os.path.join(GUN_ASSETS, "gun_anim", name + ".json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, separators=(",", ":"))
    print(name, "клипов:", len(out["clips"]))


def preview(m, sc, pose, length, skip=("_view",)):
    """Ключи клипа в Blender: посмотреть движение рук и оружия до запуска игры."""
    from mathutils import Vector
    frames = max(1, int(length * 24))
    rest = {n: ob.location.copy() for n, ob in m.objects.items()}
    for ob in m.objects.values():
        ob.animation_data_clear()
    for f in range(frames + 1):
        for name, st in pose(f / frames).items():
            if name in skip or name not in m.objects:
                continue
            ob = m.objects[name]
            ob.location = rest[name] + Vector(st.get("pos", (0, 0, 0)))
            ob.rotation_euler = tuple(math.radians(c) for c in st.get("rot", (0, 0, 0)))
            ob.keyframe_insert("location", frame=f + 1)
            ob.keyframe_insert("rotation_euler", frame=f + 1)
    sc.frame_start, sc.frame_end = 1, frames + 1
    sc.frame_set(1)


# ------------------------------------------------------------------ материалы и примитивы оружия

_kit_material = _material

GUN_PALETTE = {
    "gm_dark": dict(color=(0.028, 0.03, 0.036), rough=0.42, metal=1.0, wear=0.45, scratch=0.9),
    "gm_mid": dict(color=(0.085, 0.09, 0.1), rough=0.38, metal=1.0, wear=0.45, scratch=0.8),
    "gm_steel": dict(color=(0.33, 0.34, 0.36), rough=0.28, metal=1.0, wear=0.3, scratch=0.5),
    "gm_brass": dict(color=(0.62, 0.38, 0.1), rough=0.3, metal=1.0, wear=0.4, scratch=0.4),
    "gm_gold": dict(color=(0.86, 0.58, 0.16), rough=0.22, metal=1.0, wear=0.3, scratch=0.25),
    "gm_copper": dict(color=(0.55, 0.22, 0.09), rough=0.35, metal=1.0, wear=0.45, scratch=0.3),
    "gm_wood": dict(color=(0.2, 0.085, 0.032), rough=0.5, metal=0.0, wear=0.35, grain=1.0),
    "gm_leather": dict(color=(0.075, 0.036, 0.02), rough=0.65, metal=0.0, wear=0.45, scratch=0.2),
    "gm_rubber": dict(color=(0.014, 0.014, 0.016), rough=0.8, metal=0.0, wear=0.25),
    "gm_crimson": dict(color=(0.3, 0.018, 0.016), rough=0.38, metal=0.2, wear=0.5, scratch=0.5),
    "gm_olive": dict(color=(0.085, 0.1, 0.05), rough=0.55, metal=0.2, wear=0.55, scratch=0.9),
    "gm_bone": dict(color=(0.62, 0.55, 0.4), rough=0.55, metal=0.0, wear=0.4),
    "gm_amber": dict(color=(1.0, 0.62, 0.1), rough=0.3, metal=0.0, wear=0.0, emit=2.4),
    "gm_ember": dict(color=(1.0, 0.24, 0.03), rough=0.3, metal=0.0, wear=0.0, emit=2.2),
}
PALETTE.update(GUN_PALETTE)
NAMES[:] = list(PALETTE)


def _material(name, color, rough=0.6, metal=0.8, wear=0.25, emit=0.0, stripes=False, scratch=0.0, grain=0.0):
    """Материалы оружия видно вплотную: кроме пятен нужны продольные царапины и волокна дерева."""
    if name not in GUN_PALETTE:
        return _kit_material(name, color, rough, metal, wear, emit, stripes)
    mat = bpy.data.materials.get("WB_" + name) or bpy.data.materials.new("WB_" + name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(p.outputs[0], out.inputs[0])
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    coord = nt.nodes.new("ShaderNodeTexCoord")

    def noise(scale_xyz, scale, lo, hi, v0, v1, detail=6.0):
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = scale_xyz
        nt.links.new(coord.outputs["Object"], mp.inputs["Vector"])
        tx = nt.nodes.new("ShaderNodeTexNoise")
        tx.inputs["Scale"].default_value = scale
        tx.inputs["Detail"].default_value = detail
        nt.links.new(mp.outputs[0], tx.inputs["Vector"])
        rp = nt.nodes.new("ShaderNodeValToRGB")
        rp.color_ramp.elements[0].position, rp.color_ramp.elements[1].position = lo, hi
        rp.color_ramp.elements[0].color = (v0, v0, v0, 1)
        rp.color_ramp.elements[1].color = (v1, v1, v1, 1)
        nt.links.new(tx.outputs["Fac"], rp.inputs["Fac"])
        return rp.outputs[0]

    layers = []
    if wear > 0:
        layers.append(noise((1, 1, 1), 34.0, 0.42, 0.66, 1.0, 1.0 - wear))
        layers.append(noise((1, 1, 1), 180.0, 0.45, 0.7, 1.0, 1.0 - wear * 0.5))
    if scratch > 0:     # царапины вдоль ствола: шум, сильно растянутый по Y, тонкий порог
        layers.append(noise((1, 0.05, 1), 240.0, 0.66, 0.72, 1.0, 1.0 + 2.6 * scratch, 3.0))
    if grain > 0:       # волокна дерева
        layers.append(noise((1, 0.035, 1), 120.0, 0.3, 0.72, 1.0 - 0.72 * grain, 1.0 + 0.5 * grain, 5.0))
        layers.append(noise((1, 0.1, 1), 16.0, 0.35, 0.68, 0.72, 1.18, 3.0))
    k = None
    for l in layers:
        if k is None:
            k = l
        else:
            m = nt.nodes.new("ShaderNodeMath")
            m.operation = "MULTIPLY"
            nt.links.new(k, m.inputs[0])
            nt.links.new(l, m.inputs[1])
            k = m.outputs[0]
    rgb = nt.nodes.new("ShaderNodeRGB")
    rgb.outputs[0].default_value = (*color, 1)
    if k is None:
        nt.links.new(rgb.outputs[0], p.inputs["Base Color"])
    else:
        sc = nt.nodes.new("ShaderNodeVectorMath")
        sc.operation = "SCALE"
        nt.links.new(rgb.outputs[0], sc.inputs[0])
        nt.links.new(k, sc.inputs["Scale"])
        nt.links.new(sc.outputs[0], p.inputs["Base Color"])
    if emit:
        p.inputs["Emission Color"].default_value = (*color, 1)
        p.inputs["Emission Strength"].default_value = emit
    return mat


def octa(b, sections, mat="gm_mid"):
    """Вытянутое по Y тело с фасками: сечения [(y, полуширина, низ z, верх z, фаска)]. Кожухи, коробки, магазины."""
    rings = []
    for y, hw, z0, z1, c in sections:
        pts = ((-hw + c, z0), (hw - c, z0), (hw, z0 + c), (hw, z1 - c), (hw - c, z1), (-hw + c, z1), (-hw, z1 - c), (-hw, z0 + c))
        rings.append([b.bm.verts.new((x, y, z)) for x, z in pts])
    faces = [b.bm.faces.new(rings[0]), b.bm.faces.new(list(reversed(rings[-1])))]
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(8):
            j = (i + 1) % 8
            faces.append(b.bm.faces.new((r0[i], r0[j], r1[j], r1[i])))
    b._paint(faces, mat)


def contour(b, pts, x0, x1, mat="gm_mid", bevel=0.0, seg=1):
    """Деталь по контуру (y, z) с толщиной по X и фаской: рукояти, цевьё, щёки коробки, силуэты."""
    tmp = bmesh.new()
    lo = [tmp.verts.new((x0, y, z)) for y, z in pts]
    hi = [tmp.verts.new((x1, y, z)) for y, z in pts]
    n = len(pts)
    tmp.faces.new(lo)
    tmp.faces.new(list(reversed(hi)))
    for i in range(n):
        j = (i + 1) % n
        tmp.faces.new((lo[j], lo[i], hi[i], hi[j]))
    if bevel:
        tmp.edges.ensure_lookup_table()
        bmesh.ops.bevel(tmp, geom=list(tmp.edges), offset=bevel, offset_type="OFFSET", segments=seg, profile=0.5, affect="EDGES", clamp_overlap=True)
    b._merge(tmp, Matrix.Identity(4), mat)
    tmp.free()


def side_box(b, x, side, depth, y0, y1, z0, z1, mat, bevel=0.0):
    """Накладка на боковую стенку: от плоскости x наружу на depth. side = знак стороны по X."""
    b.box((min(x, x + side * depth), y0, z0), (max(x, x + side * depth), y1, z1), mat, bevel=bevel)


def screw(b, at, side, size=0.009, mat="gm_steel"):
    """Винт на боковой стенке: головка с фаской и шлиц."""
    x, y, z = at
    b.lathe((x, y, z), [(size, 0), (size, side * 0.003), (size * 0.72, side * 0.0052)], 8, mat, "X", base=False)
    side_box(b, x + side * 0.0048, side, 0.0007, y - size * 0.7, y + size * 0.7, z - 0.0011, z + 0.0011, "gm_rubber")


def bars(b, y0, y1, z0, z1, x, side, count, mat="gm_dark", frame="gm_brass", glow="gm_amber"):
    """Светящееся окошко за решёткой: рамка, огонь в глубине, поперечные прутья. Настоящие прутья дают глубину, которой нет у текстуры."""
    side_box(b, x, side, 0.0008, y0, y1, z0, z1, glow)
    t = 0.0045
    side_box(b, x, side, 0.004, y0 - t, y1 + t, z1, z1 + t, frame)
    side_box(b, x, side, 0.004, y0 - t, y1 + t, z0 - t, z0, frame)
    side_box(b, x, side, 0.004, y0 - t, y0, z0, z1, frame)
    side_box(b, x, side, 0.004, y1, y1 + t, z0, z1, frame)
    for i in range(1, count):
        yy = y0 + (y1 - y0) * i / count
        side_box(b, x, side, 0.0034, yy - 0.0022, yy + 0.0022, z0, z1, mat)


def aquila(b, center, s, side, mat="gm_gold"):
    """Имперский орёл на боковой стенке: две головы и крылья с перьями, настоящий контур. center = (x, y, z), s — размах."""
    x, y, z = center
    th = 0.0035
    x0, x1 = (x, x + th) if side > 0 else (x - th, x)
    wing = [(0.10, 0.12), (0.34, 0.27), (0.62, 0.42), (1.0, 0.42), (0.86, 0.26), (0.97, 0.22), (0.78, 0.09), (0.86, 0.03), (0.62, -0.06), (0.66, -0.13), (0.40, -0.16), (0.10, -0.1)]
    head = [(0.0, 0.2), (0.12, 0.42), (0.28, 0.46), (0.42, 0.38), (0.3, 0.33), (0.2, 0.2), (0.07, 0.12)]
    for k in (-1, 1):
        for shape in (wing, head):
            contour(b, [(y + k * u * s, z + v * s) for u, v in shape], x0, x1, mat)
    body_pts = [(-0.11, 0.18), (0.11, 0.18), (0.13, -0.18), (0.06, -0.36), (0.0, -0.46), (-0.06, -0.36), (-0.13, -0.18)]
    contour(b, [(y + u * s, z + v * s) for u, v in body_pts], x0 - (0.0012 if side < 0 else 0), x1 + (0.0012 if side > 0 else 0), mat)


def purity_seal(b, at, side, s=1.0, strips=((-0.012, 0.085), (0.012, 0.115))):
    """Печать чистоты: восковой диск с ободом и выпуклым знаком, две полосы пергамента, загнутые от стенки."""
    x, y, z = at
    b.lathe((x, y, z), [(0.03 * s, 0), (0.033 * s, side * 0.004), (0.031 * s, side * 0.009), (0.024 * s, side * 0.011), (0.022 * s, side * 0.0085), (0.001, side * 0.0085)], 12, "gm_crimson", "X", base=False)
    side_box(b, x + side * 0.0085, side, 0.0035, y - 0.012 * s, y + 0.012 * s, z - 0.003 * s, z + 0.003 * s, "wax")
    side_box(b, x + side * 0.0085, side, 0.0035, y - 0.003 * s, y + 0.003 * s, z - 0.012 * s, z + 0.012 * s, "wax")
    for dy, ln in strips:
        ln *= s
        pts = [(0.012 * s, 0.002), (0.45 * ln, 0.003), (0.8 * ln, 0.0075), (ln, 0.0125)]
        w = 0.0085 * s
        for (d0, o0), (d1, o1) in zip(pts, pts[1:]):
            vs = [b.bm.verts.new((x + side * o, y + dy + q * w, z - d)) for d, o, q in ((d0, o0, -1), (d0, o0, 1), (d1, o1, 1), (d1, o1, -1))]
            b._paint([b.bm.faces.new(vs)], "parchment")


def rear_plate(b, y, hw, z0, z1, ring_z):
    """Задняя стенка коробки: при прицеливании она прямо перед глазами. Плита с болтами, золотое кольцо и крышка запала."""
    b.box((-hw, y, z0), (hw, y + 0.006, z1), "gm_dark", bevel=0.002)
    b.box((-hw + 0.009, y + 0.006, z0 + 0.009), (hw - 0.009, y + 0.009, z1 - 0.009), "gm_mid", bevel=0.001)
    for sx in (-1, 1):
        for z in (z0 + 0.016, z1 - 0.016):
            b.bolt((sx * (hw - 0.016), y + 0.009, z), "Y", 0.0065, 0.004, "gm_brass")
    r = min(hw, (z1 - z0) / 2) * 0.62
    b.ring((0, y + 0.012, ring_z), r * 0.7, r, 0.006, 18, "gm_gold", "Y")
    b.lathe((0, y + 0.009, ring_z), [(r * 0.7, 0), (r * 0.62, 0.005), (r * 0.25, 0.008), (0.001, 0.009)], 14, "gm_crimson", "Y", base=False)
