"""
Набор примитивов для машин Warpbound в Blender: 1 метр = 1 блок, перед машины смотрит в -Y, Z вверх.

Каждая кость — отдельный объект с началом в точке вращения (потом так же уйдёт в GeckoLib).
Запуск из Blender: exec(open(r"<проект>/tools/models/blender/crusher.py", encoding="utf-8").read())
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

AXES = {"Z": Matrix.Identity(4), "X": Matrix.Rotation(math.pi / 2, 4, "Y"), "Y": Matrix.Rotation(-math.pi / 2, 4, "X")}


# ------------------------------------------------------------------ материалы (предпросмотр, в игре их заменит атлас)

def _material(name, color, rough=0.6, metal=0.8, wear=0.25, emit=0.0, stripes=False):
    mat = bpy.data.materials.get("WB_" + name) or bpy.data.materials.new("WB_" + name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(p.outputs[0], out.inputs[0])
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    p.inputs["Base Color"].default_value = (*color, 1)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    if stripes:
        wave = nt.nodes.new("ShaderNodeTexWave")
        wave.bands_direction = "DIAGONAL"
        wave.inputs["Scale"].default_value = 3.2
        wave.inputs["Distortion"].default_value = 0
        nt.links.new(coord.outputs["Object"], wave.inputs["Vector"])
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.interpolation = "CONSTANT"
        ramp.color_ramp.elements[1].position = 0.5
        ramp.color_ramp.elements[0].color = (0.02, 0.02, 0.02, 1)
        ramp.color_ramp.elements[1].color = (*color, 1)
        nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs[0], p.inputs["Base Color"])
    elif wear > 0:
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 26.0
        noise.inputs["Detail"].default_value = 8.0
        nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.42
        ramp.color_ramp.elements[1].position = 0.68
        ramp.color_ramp.elements[0].color = (*color, 1)
        ramp.color_ramp.elements[1].color = (color[0] * (1 - wear), color[1] * (1 - wear * 1.2), color[2] * (1 - wear * 1.4), 1)
        nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs[0], p.inputs["Base Color"])
    if emit:
        p.inputs["Emission Color"].default_value = (*color, 1)
        p.inputs["Emission Strength"].default_value = emit
    return mat


PALETTE = {
    "hull": dict(color=(0.15, 0.165, 0.195), rough=0.55, wear=0.5),
    "dark": dict(color=(0.05, 0.053, 0.062), rough=0.6, wear=0.3),
    "steel": dict(color=(0.56, 0.58, 0.61), rough=0.33, wear=0.25),
    "rust": dict(color=(0.20, 0.085, 0.04), rough=0.85, metal=0.3, wear=0.5),
    "brass": dict(color=(0.60, 0.40, 0.11), rough=0.34, wear=0.35),
    "red": dict(color=(0.33, 0.028, 0.02), rough=0.55, metal=0.15, wear=0.4),
    "bone": dict(color=(0.60, 0.53, 0.38), rough=0.75, metal=0.0, wear=0.35),
    "hazard": dict(color=(0.75, 0.46, 0.02), rough=0.6, metal=0.1, stripes=True),
    "wax": dict(color=(0.42, 0.02, 0.02), rough=0.4, metal=0.0, wear=0.1),
    "parchment": dict(color=(0.72, 0.62, 0.42), rough=0.9, metal=0.0, wear=0.3),
    "brick": dict(color=(0.26, 0.085, 0.05), rough=0.9, metal=0.0, wear=0.55),
    "water": dict(color=(0.10, 0.34, 0.46), rough=0.2, metal=0.0, wear=0.25, emit=0.25),
    "screen": dict(color=(0.16, 0.85, 0.42), rough=0.3, metal=0.0, wear=0.0, emit=1.1),
    "stain_gold": dict(color=(0.95, 0.5, 0.06), rough=0.3, metal=0.0, wear=0.2, emit=0.9),
    "stain_red": dict(color=(0.72, 0.04, 0.03), rough=0.3, metal=0.0, wear=0.2, emit=0.95),
    "stain_blue": dict(color=(0.05, 0.16, 0.6), rough=0.3, metal=0.0, wear=0.2, emit=1.1),
    "sulfur": dict(color=(0.85, 0.68, 0.05), rough=0.8, metal=0.0, wear=0.3),
    "rubber": dict(color=(0.012, 0.012, 0.014), rough=0.7, metal=0.0, wear=0.0),
    "fire": dict(color=(1.0, 0.2, 0.015), rough=0.5, metal=0.0, wear=0.0, emit=2.6),
    "eye": dict(color=(1.0, 0.03, 0.015), rough=0.5, metal=0.0, wear=0.0, emit=5.0),
    "glass": dict(color=(0.65, 0.9, 0.55), rough=0.3, metal=0.0, wear=0.0, emit=1.3),
}
NAMES = list(PALETTE)


class Bone:
    """Кость: общий bmesh, пишем в мировых метрах, при сборке вычитаем точку вращения."""

    def __init__(self, machine, name, pivot=(0, 0, 0)):
        self.machine, self.name, self.pivot = machine, name, Vector(pivot)
        self.bm = bmesh.new()

    def _paint(self, faces, mat):
        idx = NAMES.index(mat)
        for f in faces:
            f.material_index = idx

    def box(self, lo, hi, mat="hull", bevel=0.0, rot=None, around=None):
        """Параллелепипед от lo до hi; bevel — фаска; rot=(ось, градусы) вокруг around (по умолчанию центр)."""
        lo, hi = Vector(lo), Vector(hi)
        tmp = bmesh.new()
        c = (lo + hi) / 2
        s = hi - lo
        bmesh.ops.create_cube(tmp, size=1.0, matrix=Matrix.Diagonal((s.x, s.y, s.z, 1)))
        if bevel:
            bmesh.ops.bevel(tmp, geom=list(tmp.verts) + list(tmp.edges), offset=bevel, offset_type="OFFSET", segments=1,
                            profile=0.5, affect="EDGES", clamp_overlap=True)
        m = Matrix.Translation(c)
        if rot:
            p = Vector(around) if around else c
            m = Matrix.Translation(p) @ Matrix.Rotation(math.radians(rot[1]), 4, rot[0]) @ Matrix.Translation(c - p)
        self._merge(tmp, m, mat)
        tmp.free()

    def lathe(self, center, profile, n=16, mat="steel", axis="Z", cap=True, phase=0.0, base=True):
        """Тело вращения: profile = [(радиус, высота вдоль оси)], грани плоские."""
        m = Matrix.Translation(center) @ AXES[axis]
        rings = []
        for r, h in profile:
            ring = []
            for i in range(n):
                a = phase + 2 * math.pi * i / n
                ring.append(self.bm.verts.new(m @ Vector((r * math.cos(a), r * math.sin(a), h))))
            rings.append(ring)
        faces = []
        for a, b in zip(rings, rings[1:]):
            for i in range(n):
                j = (i + 1) % n
                faces.append(self.bm.faces.new((a[i], a[j], b[j], b[i])))
        if cap:
            if base:
                faces.append(self.bm.faces.new(list(reversed(rings[0]))))
            faces.append(self.bm.faces.new(rings[-1]))
        self._paint(faces, mat)

    def ring(self, center, r_in, r_out, width, n=24, mat="steel", axis="X"):
        """Кольцо прямоугольного сечения: ободья, бандажи."""
        w = width / 2
        self.lathe(center, [(r_in, -w), (r_out, -w), (r_out, w), (r_in, w), (r_in, -w)], n, mat, axis, cap=False)

    def gear(self, center, r_root, r_tip, width, teeth, mat="brass", axis="X", phase=0.0, fill=0.5, flank=0.14):
        """Шестерня с трапециевидным зубом; phase — поворот в градусах, чтобы зубья входили в зацепление."""
        m = Matrix.Translation(center) @ AXES[axis]
        pitch = 2 * math.pi / teeth
        half = pitch * fill / 2
        prof = []
        for i in range(teeth):
            a = math.radians(phase) + i * pitch
            prof += [(r_root, a - half - pitch * flank), (r_tip, a - half + pitch * flank * 0.5),
                     (r_tip, a + half - pitch * flank * 0.5), (r_root, a + half + pitch * flank)]
        n = len(prof)
        lo = [self.bm.verts.new(m @ Vector((r * math.cos(a), r * math.sin(a), -width / 2))) for r, a in prof]
        hi = [self.bm.verts.new(m @ Vector((r * math.cos(a), r * math.sin(a), width / 2))) for r, a in prof]
        faces = [self.bm.faces.new(list(reversed(lo))), self.bm.faces.new(hi)]
        for i in range(n):
            j = (i + 1) % n
            faces.append(self.bm.faces.new((lo[i], lo[j], hi[j], hi[i])))
        self._paint(faces, mat)

    def loft(self, sections, mat="hull"):
        """Прямоугольные сечения [(z, полуширина X, полуглубина Y, центр Y)] — воронка, обшивка; низ открыт."""
        rings = []
        for z, hx, hy, cy in sections:
            rings.append([self.bm.verts.new(v) for v in
                          ((-hx, cy - hy, z), (hx, cy - hy, z), (hx, cy + hy, z), (-hx, cy + hy, z))])
        faces = []
        for a, b in zip(rings, rings[1:]):
            for i in range(4):
                j = (i + 1) % 4
                faces.append(self.bm.faces.new((a[i], a[j], b[j], b[i])))
        self._paint(faces, mat)

    def blob(self, sections, n=10, mat="bone"):
        """Тело из эллипсов вдоль Y: [(y, rx, rz, сдвиг x, сдвиг z)] — череп, кожухи сложной формы."""
        rings = []
        for pos, rx, rz, ox, oz in sections:
            ring = []
            for i in range(n):
                a = 2 * math.pi * i / n + math.pi / n
                ring.append(self.bm.verts.new((ox + rx * math.cos(a), pos, oz + rz * math.sin(a))))
            rings.append(ring)
        faces = [self.bm.faces.new(rings[0]), self.bm.faces.new(list(reversed(rings[-1])))]
        for a, b in zip(rings, rings[1:]):
            for i in range(n):
                j = (i + 1) % n
                faces.append(self.bm.faces.new((a[i], a[j], b[j], b[i])))
        self._paint(faces, mat)

    def wedge(self, base_lo, base_hi, top_lo, top_hi, mat="hull"):
        """Скошенный брус: нижний прямоугольник и верхний со своими x, y — контрфорсы и косынки."""
        (x0, y0, z0), (x1, y1) = base_lo, base_hi
        (u0, v0, z1), (u1, v1) = top_lo, top_hi
        b = [self.bm.verts.new(p) for p in ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0))]
        t = [self.bm.verts.new(p) for p in ((u0, v0, z1), (u1, v0, z1), (u1, v1, z1), (u0, v1, z1))]
        faces = [self.bm.faces.new(list(reversed(b))), self.bm.faces.new(t)]
        for i in range(4):
            j = (i + 1) % 4
            faces.append(self.bm.faces.new((b[i], b[j], t[j], t[i])))
        self._paint(faces, mat)

    def pipe(self, points, radius, n=8, mat="rust"):
        """Труба по ломаной: кольца перпендикулярны биссектрисе в каждом изломе."""
        pts = [Vector(p) for p in points]
        up = Vector((0.31, 0.17, 0.93))
        rings = []
        for i, p in enumerate(pts):
            d0 = (p - pts[i - 1]).normalized() if i else (pts[1] - p).normalized()
            d1 = (pts[i + 1] - p).normalized() if i < len(pts) - 1 else d0
            t = (d0 + d1).normalized()
            side = t.cross(up).normalized()
            ex = t.cross(side).normalized()
            k = 1 / max(0.5, d0.dot(t))
            ring = []
            for j in range(n):
                a = 2 * math.pi * j / n
                off = side * math.cos(a) * radius + ex * math.sin(a) * radius
                off += t * (off.dot(d0) * (k - 1))    # растяжение в изломе, чтобы сечение не сплющивалось
                ring.append(self.bm.verts.new(p + off))
            rings.append(ring)
        faces = [self.bm.faces.new(rings[0]), self.bm.faces.new(list(reversed(rings[-1])))]
        for a, b in zip(rings, rings[1:]):
            for i in range(n):
                j = (i + 1) % n
                faces.append(self.bm.faces.new((a[i], a[j], b[j], b[i])))
        self._paint(faces, mat)

    def beam(self, p0, p1, w=0.2, d=None, mat="hull", bevel=0.0):
        """Брус от точки к точке: стойки, раскосы."""
        p0, p1 = Vector(p0), Vector(p1)
        axis = p1 - p0
        tmp = bmesh.new()
        bmesh.ops.create_cube(tmp, size=1.0, matrix=Matrix.Diagonal((w, d or w, axis.length, 1)))
        if bevel:
            bmesh.ops.bevel(tmp, geom=list(tmp.verts) + list(tmp.edges), offset=bevel, offset_type="OFFSET", segments=1,
                            profile=0.5, affect="EDGES", clamp_overlap=True)
        m = Matrix.Translation((p0 + p1) / 2) @ axis.to_track_quat("Z", "Y").to_matrix().to_4x4()
        self._merge(tmp, m, mat)
        tmp.free()

    def plate(self, points, x0, x1, mat="hull"):
        """Плита по контуру в плоскости YZ, толщина от x0 до x1: головка коромысла, противовесы, косынки."""
        a = [self.bm.verts.new((x0, y, z)) for y, z in points]
        b = [self.bm.verts.new((x1, y, z)) for y, z in points]
        n = len(points)
        faces = [self.bm.faces.new(a), self.bm.faces.new(list(reversed(b)))]
        for i in range(n):
            j = (i + 1) % n
            faces.append(self.bm.faces.new((a[j], a[i], b[i], b[j])))
        self._paint(faces, mat)

    def plate_xz(self, points, y0, y1, mat="hull"):
        """Плита по контуру в плоскости XZ, толщина от y0 до y1: арки, рамы."""
        a = [self.bm.verts.new((x, y0, z)) for x, z in points]
        b = [self.bm.verts.new((x, y1, z)) for x, z in points]
        n = len(points)
        faces = [self.bm.faces.new(a), self.bm.faces.new(list(reversed(b)))]
        for i in range(n):
            j = (i + 1) % n
            faces.append(self.bm.faces.new((a[j], a[i], b[i], b[j])))
        self._paint(faces, mat)

    def ladder(self, x, y, z0, z1, width=0.34, step=0.3, mat="steel"):
        """Лестница вдоль Z в плоскости XZ."""
        for s in (-1, 1):
            self.box((x + s * width / 2 - 0.02, y - 0.02, z0), (x + s * width / 2 + 0.02, y + 0.02, z1), mat)
        z = z0 + step / 2
        while z < z1:
            self.box((x - width / 2, y - 0.012, z - 0.012), (x + width / 2, y + 0.012, z + 0.012), mat)
            z += step

    def skull(self, cx, back, cz, s=1.0, augmetic=True, teeth=True):
        """Череп анфас в -Y: back — задняя плоскость, cz — середина лица. Без нижней челюсти."""
        X, Y, Z = (lambda v: cx + v * s), (lambda v: back - v * s), (lambda v: cz + v * s)

        def ell(sections, n, mat):
            self.blob([(Y(y), r1 * s, r2 * s, X(ox), Z(oz)) for y, r1, r2, ox, oz in sections], n, mat)
        ell([(0.0, 0.30, 0.30, 0, 0.08), (0.12, 0.37, 0.38, 0, 0.08), (0.26, 0.38, 0.38, 0, 0.08),
             (0.38, 0.34, 0.33, 0, 0.07), (0.45, 0.25, 0.24, 0, 0.04)], 12, "bone")
        ell([(0.08, 0.27, 0.13, 0, -0.18), (0.28, 0.27, 0.15, 0, -0.18), (0.40, 0.19, 0.12, 0, -0.18), (0.43, 0.14, 0.08, 0, -0.18)], 10, "bone")
        self.box((X(-0.33), Y(0.49), Z(0.13)), (X(0.33), Y(0.35), Z(0.21)), "bone", bevel=0.03 * s)
        for side in (-1, 1):
            self.box((X(side * 0.3 - 0.09), Y(0.41), Z(-0.2)), (X(side * 0.3 + 0.09), Y(0.13), Z(-0.06)), "bone", bevel=0.03 * s)
            ell([(0.50, 0.10, 0.09, side * 0.15, 0.04), (0.38, 0.12, 0.11, side * 0.15, 0.04)], 8, "dark")
        if augmetic:
            ell([(0.525, 0.055, 0.055, 0.15, 0.04), (0.47, 0.075, 0.075, 0.15, 0.04)], 8, "steel")
            ell([(0.54, 0.04, 0.04, 0.15, 0.04), (0.52, 0.05, 0.05, 0.15, 0.04)], 8, "eye")
            ell([(0.515, 0.05, 0.05, -0.15, 0.04), (0.48, 0.06, 0.06, -0.15, 0.04)], 8, "eye")
            ell([(0.42, 0.17, 0.18, 0.17, 0.24), (0.29, 0.22, 0.19, 0.17, 0.24), (0.1, 0.22, 0.19, 0.17, 0.24)], 8, "steel")
        else:
            for side in (-1, 1):
                ell([(0.515, 0.05, 0.05, side * 0.15, 0.04), (0.48, 0.06, 0.06, side * 0.15, 0.04)], 8, "eye")
        self.wedge((X(-0.06), Y(0.465), Z(-0.14)), (X(0.06), Y(0.40)), (X(-0.015), Y(0.46), Z(0.0)), (X(0.015), Y(0.40)), "dark")
        if teeth:
            for i in range(7):
                x = -0.165 + i * 0.055
                self.box((X(x - 0.021), Y(0.43), Z(-0.335)), (X(x + 0.021), Y(0.36), Z(-0.24)), "bone", bevel=0.006 * s)

    def tank(self, center, r, h, n=16, mat="hull", bands=(), dome=True, band_mat="brass"):
        """Вертикальный бак: фланец, стенка, купол, пояса на долях высоты."""
        p = [(r * 1.08, 0), (r * 1.08, 0.08), (r, 0.12), (r, h)]
        if dome:
            p += [(r * 0.86, h + r * 0.28), (r * 0.5, h + r * 0.45), (r * 0.25, h + r * 0.5)]
        self.lathe(center, p, n, mat)
        for f in bands:
            self.ring((center[0], center[1], center[2] + h * f), r * 0.9, r * 1.04, 0.09, n, band_mat, "Z")

    def plinth(self, x0, y0, x1, y1):
        """Плита машины: две ступени, кромка опасности спереди и сзади, анкеры по углам. Верх на z=0.3."""
        self.box((x0, y0, 0), (x1, y1, 0.16), "dark", bevel=0.04)
        self.box((x0 + 0.1, y0 + 0.1, 0.16), (x1 - 0.1, y1 - 0.1, 0.3), "hull", bevel=0.025)
        for a, b in ((y0 + 0.1, y0 + 0.2), (y1 - 0.2, y1 - 0.1)):
            self.box((x0 + 0.1, a, 0.3), (x1 - 0.1, b, 0.31), "hazard")
        for x in (x0 + 0.05, x1 - 0.05):
            for y in (y0 + 0.05, y1 - 0.05):
                self.bolt((x, y, 0.16), "Z", 0.04, 0.03, "steel")

    def bolt(self, at, axis="Y", size=0.035, height=0.022, mat="brass"):
        """Шестигранная головка болта. height со знаком: куда торчит вдоль оси."""
        self.lathe(at, [(size, 0), (size * 0.6, height)], 4, mat, axis, phase=math.pi / 4, base=False)

    def seal(self, at, axis="Y", sign=-1):
        """Печать чистоты: восковой диск и свисающие полосы пергамента."""
        a = Vector(at)
        self.lathe(a, [(0.075, 0), (0.08, sign * 0.012), (0.06, sign * 0.03)], 10, "wax", axis)
        if axis == "Y":
            for dx, ln in ((-0.03, 0.2), (0.025, 0.27)):
                self.box((a.x + dx - 0.018, a.y + sign * 0.006, a.z - ln), (a.x + dx + 0.018, a.y + sign * 0.012, a.z - 0.03), "parchment")
        else:
            for dy, ln in ((-0.03, 0.2), (0.025, 0.27)):
                self.box((a.x + sign * 0.006, a.y + dy - 0.018, a.z - ln), (a.x + sign * 0.012, a.y + dy + 0.018, a.z - 0.03), "parchment")

    def _merge(self, tmp, m, mat):
        vmap = {v: self.bm.verts.new(m @ v.co) for v in tmp.verts}
        faces = [self.bm.faces.new([vmap[v] for v in f.verts]) for f in tmp.faces]
        self._paint(faces, mat)


class Machine:
    def __init__(self, name):
        self.name, self.bones, self.objects = name, {}, {}

    def bone(self, name, pivot=(0, 0, 0)):
        self.bones[name] = Bone(self, name, pivot)
        return self.bones[name]

    def build(self, scene_name):
        """Создаёт отдельную сцену (сцены автора не трогает) и объекты-кости. Возвращает сцену."""
        sc = bpy.data.scenes.get(scene_name) or bpy.data.scenes.new(scene_name)
        bpy.context.window.scene = sc
        for o in list(sc.collection.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        mats = [_material(n, **PALETTE[n]) for n in NAMES]
        quads = 0
        for b in self.bones.values():
            bmesh.ops.recalc_face_normals(b.bm, faces=list(b.bm.faces))
            bmesh.ops.translate(b.bm, verts=list(b.bm.verts), vec=-b.pivot)
            me = bpy.data.meshes.new(f"{self.name}_{b.name}")
            b.bm.to_mesh(me)
            quads += sum(max(1, len(f.verts) - 2) for f in b.bm.faces)
            b.bm.free()
            for m in mats:
                me.materials.append(m)
            ob = bpy.data.objects.new(b.name, me)
            ob.location = b.pivot
            ob.rotation_mode = "XYZ"
            ob["pivot"] = list(b.pivot)
            ob["bone"] = b.name     # имена объектов в Blender общие на все сцены: «door» второй машины станет «door.001»
            sc.collection.objects.link(ob)
            self.objects[b.name] = ob
        return sc, quads


def light_scene(sc, frames):
    """Свет предпросмотра и длина цикла анимации."""
    sc.frame_start, sc.frame_end = 1, frames
    sc.render.fps = 24
    w = sc.world or bpy.data.worlds.new("WB_MachineWorld")
    sc.world = w
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = (0.46, 0.53, 0.65, 1)
    bg.inputs[1].default_value = 0.55
    for name, energy, rot in (("WB_Key", 3.2, (52, 8, -32)), ("WB_Fill", 0.8, (65, -10, 140))):
        lamp = bpy.data.lights.get(name) or bpy.data.lights.new(name, "SUN")
        lamp.energy = energy
        lamp.angle = math.radians(6)
        ob = bpy.data.objects.new(name, lamp)
        ob.rotation_euler = tuple(math.radians(v) for v in rot)
        sc.collection.objects.link(ob)


def auto_animate(objs, sc, pose, loop):
    """Ключи в Blender для просмотра: каждый кадр из той же функции позы, что и анимация в игре."""
    frames = int(loop * 24)
    rest = {n: ob.location.copy() for n, ob in objs.items()}
    for f in range(frames + 1):
        for name, st in pose(f / frames).items():
            ob = objs[name]
            if "rot" in st:
                ob.rotation_euler = tuple(math.radians(v) for v in st["rot"])
                ob.keyframe_insert("rotation_euler", frame=f + 1)
            if "pos" in st:
                ob.location = rest[name] + Vector(st["pos"])
                ob.keyframe_insert("location", frame=f + 1)
            if "scale" in st:
                ob.scale = st["scale"]
                ob.keyframe_insert("scale", frame=f + 1)
    sc.frame_set(1)


def auto_tracks(pose, loop, steps):
    """Дорожки GeckoLib: поворот (X, -Z, Y) Blender, позиция (x, z, y) × 16, масштаб (x, z, y). Шаг должен быть меньше полуоборота."""
    out = {}
    for i in range(steps + 1):
        t = i / steps
        key = f"{loop * t:.4f}"
        for name, st in pose(t).items():
            bone = out.setdefault(name, {})
            if "rot" in st:
                x, y, z = st["rot"]
                bone.setdefault("rotation", {})[key] = [round(x, 3), round(-z, 3), round(y, 3)]
            if "pos" in st:
                x, y, z = st["pos"]
                bone.setdefault("position", {})[key] = [round(x * 16, 3), round(z * 16, 3), round(y * 16, 3)]
            if "scale" in st:
                x, y, z = st["scale"]
                bone.setdefault("scale", {})[key] = [round(x, 3), round(z, 3), round(y, 3)]
    return out, loop
