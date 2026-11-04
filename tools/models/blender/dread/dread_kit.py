"""
Дредноуты из исходных моделей автора (references/models3d): STL на сотни тысяч граней режется на кости, упрощается до игрового бюджета,
а мелкие детали исходника запекаются в текстуру (нормали, затенение, цвет) с исходного меша на упрощённый.

Концепт описывает: файлы, центр и масштаб, кости (родитель и точка вращения), правило «грань -> кость», правило «грань -> материал».
Запуск внутри Blender: tools/models/blender/dread/<концепт>.py. Папка references не в git, результат — в assets (geo/entity, textures/entity, animations/entity).

Оси как у машин: 1 м = 1 блок, перед в -Y, Z вверх. Правая сторона машины — это -X.
"""
import json
import math
import os
import time

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = r"C:/Users/Name/projectWARHAMMER"
REFS = os.path.join(ROOT, "references/models3d")
ASSETS = os.path.join(ROOT, "src/main/resources/assets/warpbound")

COLORS = {
    # имя: (цвет, размер пятен, сила пятен)
    "blue": ((0.012, 0.042, 0.2), 0.16),
    "green": ((0.008, 0.045, 0.022), 0.2),
    "red": ((0.17, 0.008, 0.008), 0.18),
    "black": ((0.012, 0.012, 0.016), 0.3),
    "dark": ((0.022, 0.024, 0.03), 0.4),
    "steel": ((0.2, 0.21, 0.23), 0.35),
    "gold": ((0.42, 0.22, 0.035), 0.3),
    "brass": ((0.26, 0.14, 0.035), 0.4),
    "copper": ((0.36, 0.13, 0.05), 0.4),
    "bone": ((0.42, 0.36, 0.23), 0.3),
    "rubber": ((0.01, 0.01, 0.012), 0.2),
    "parchment": ((0.66, 0.56, 0.36), 0.35),
}
MAT_NAMES = list(COLORS)


def _material(name):
    color, wear = COLORS[name]
    mat = bpy.data.materials.get("DR_" + name) or bpy.data.materials.new("DR_" + name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(p.outputs[0], out.inputs[0])
    p.inputs["Metallic"].default_value = 0.0      # цвет запекается проходом DIFFUSE: у металла он был бы чёрным
    p.inputs["Roughness"].default_value = 0.6
    coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 46.0
    noise.inputs["Detail"].default_value = 9.0
    nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[1].position = 0.42, 0.68
    ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
    k = 1 - wear
    ramp.color_ramp.elements[1].color = (k, k, k, 1)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    rgb = nt.nodes.new("ShaderNodeRGB")
    rgb.outputs[0].default_value = (*color, 1)
    sc = nt.nodes.new("ShaderNodeVectorMath")
    sc.operation = "SCALE"
    nt.links.new(rgb.outputs[0], sc.inputs[0])
    nt.links.new(ramp.outputs[0], sc.inputs["Scale"])
    nt.links.new(sc.outputs[0], p.inputs["Base Color"])
    return mat


def load_stl(path):
    """Вершины и треугольники как массивы numpy. Объект в сцене не остаётся."""
    bpy.ops.wm.stl_import(filepath=path)
    ob = bpy.context.view_layer.objects.active
    me = ob.data
    v = np.zeros(len(me.vertices) * 3, dtype=np.float64)
    me.vertices.foreach_get("co", v)
    me.calc_loop_triangles()
    t = np.zeros(len(me.loop_triangles) * 3, dtype=np.int64)
    me.loop_triangles.foreach_get("vertices", t)
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)
    return v.reshape(-1, 3), t.reshape(-1, 3)


def islands(n_verts, tris):
    """Связные части меша: номер и размер (диагональ) для каждой вершины считаются снаружи. Кабели, заклёпки, черепа в STL часто отдельные куски."""
    labels = np.arange(n_verts)
    a = np.concatenate((tris[:, 0], tris[:, 1]))
    b = np.concatenate((tris[:, 1], tris[:, 2]))
    for _ in range(200):
        before = labels.copy()
        m = np.minimum(labels[a], labels[b])
        np.minimum.at(labels, a, m)
        np.minimum.at(labels, b, m)
        labels = labels[labels]
        if np.array_equal(before, labels):
            break
    return labels


def island_size(verts, labels):
    n = labels.max() + 1
    lo = np.full((n, 3), 1e9)
    hi = np.full((n, 3), -1e9)
    for c in range(3):
        np.minimum.at(lo[:, c], labels, verts[:, c])
        np.maximum.at(hi[:, c], labels, verts[:, c])
    return np.linalg.norm(hi - lo, axis=1)


def _mesh(name, verts, tris, mat_idx=None, materials=()):
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(verts))
    me.vertices.foreach_set("co", verts.astype(np.float32).ravel())
    me.loops.add(tris.size)
    me.loops.foreach_set("vertex_index", tris.astype(np.int32).ravel())
    me.polygons.add(len(tris))
    me.polygons.foreach_set("loop_start", np.arange(len(tris), dtype=np.int32) * 3)
    me.update(calc_edges=True)
    for m in materials:
        me.materials.append(m)
    if mat_idx is not None:
        me.polygons.foreach_set("material_index", mat_idx.astype(np.int32))
    me.update()
    return me


def remesh(me, voxel, scene):
    ob = bpy.data.objects.new("tmp_rm", me)
    scene.collection.objects.link(ob)
    r = ob.modifiers.new("r", "REMESH")
    r.mode = "VOXEL"
    r.voxel_size = voxel
    r.use_smooth_shade = False
    bpy.context.view_layer.update()
    out = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(ob, do_unlink=True)
    return out


def cluster(me, cell, materials):
    """Слияние вершин по сетке: грубое, зато не зависит от качества меша."""
    v = np.zeros(len(me.vertices) * 3, dtype=np.float64)
    me.vertices.foreach_get("co", v)
    v = v.reshape(-1, 3)
    me.calc_loop_triangles()
    t = np.zeros(len(me.loop_triangles) * 3, dtype=np.int64)
    me.loop_triangles.foreach_get("vertices", t)
    t = t.reshape(-1, 3)
    mi = np.zeros(len(me.loop_triangles), dtype=np.int64)
    pi = np.zeros(len(me.loop_triangles), dtype=np.int64)
    me.loop_triangles.foreach_get("polygon_index", pi)
    pm = np.zeros(len(me.polygons), dtype=np.int64)
    me.polygons.foreach_get("material_index", pm)
    mi = pm[pi]
    keys = np.floor(v / cell).astype(np.int64)
    _, inv = np.unique(keys, axis=0, return_inverse=True)
    inv = inv.ravel()
    n = inv.max() + 1
    # новая вершина — среднее сливающихся
    sums = np.zeros((n, 3))
    np.add.at(sums, inv, v)
    counts = np.bincount(inv, minlength=n)[:, None]
    nv = sums / counts
    nt = inv[t]
    ok = (nt[:, 0] != nt[:, 1]) & (nt[:, 1] != nt[:, 2]) & (nt[:, 0] != nt[:, 2])
    return _mesh("tmp", nv, nt[ok], mi[ok], materials)


class Concept:
    def __init__(self, name, height=3.6):
        self.name, self.height = name, height
        self.verts, self.tris, self.bone_of, self.mat_of, self.sizes = [], [], [], [], []
        self.bones = {}   # имя -> (родитель, точка вращения, бюджет граней)
        self.scene = None
        self.objects = {}
        self.voxel = 0.016
        self.parts = []

    def add_part(self, verts, tris, bone_fn, mat_fn):
        """verts уже в игровых координатах. bone_fn и mat_fn получают центры граней (N×3) и размер куска каждой грани, возвращают номера."""
        labels = islands(len(verts), tris)
        size = island_size(verts, labels)
        centers = verts[tris].mean(axis=1)
        face_size = size[labels[tris[:, 0]]]
        offset = sum(len(v) for v in self.verts)
        self.verts.append(verts)
        self.tris.append(tris + offset)
        self.bone_of.append(bone_fn(centers, face_size))
        self.mat_of.append(mat_fn(centers, face_size))
        self.sizes.append(face_size)
        self.parts.append((verts, tris, bone_fn, face_size))

    def bone(self, name, parent, pivot, budget):
        self.bones[name] = (parent, Vector(pivot), budget)

    def build(self, min_island=0.14):
        """Сцена с костями низкой детализации и общий меш высокой детализации (упрощён только до разумного размера)."""
        verts = np.concatenate(self.verts)
        tris = np.concatenate(self.tris)
        bone_of = np.concatenate(self.bone_of)
        mat_of = np.concatenate(self.mat_of)
        sizes = np.concatenate(self.sizes)
        names = list(self.bones)
        sc = bpy.data.scenes.get("WB_" + self.name) or bpy.data.scenes.new("WB_" + self.name)
        bpy.context.window.scene = sc
        for o in list(sc.collection.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        self.scene = sc
        mats = [_material(n) for n in MAT_NAMES]
        deps = bpy.context.evaluated_depsgraph_get()

        def decimate(me, ratio, name):
            ob = bpy.data.objects.new(name, me)
            sc.collection.objects.link(ob)
            d = ob.modifiers.new("d", "DECIMATE")
            d.ratio = ratio
            d.use_collapse_triangulate = True
            bpy.context.view_layer.update()
            dg = bpy.context.evaluated_depsgraph_get()
            out = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
            bpy.data.objects.remove(ob, do_unlink=True)
            return out

        # исходник собран из пересекающихся оболочек, упрощение напрямую рвёт его на осколки. Поэтому деталь целиком оборачивается
        # сплошной воксельной оболочкой (только замкнутая деталь это выдерживает) и уже потом режется на кости. Детали вернёт запекание
        low_v = {i: [] for i in range(len(names))}
        low_t = {i: [] for i in range(len(names))}
        low_n = {i: 0 for i in range(len(names))}
        for pv, pt, bone_fn, face_size in self.parts:
            keep = face_size >= min_island
            t = pt[keep]
            used, inv = np.unique(t, return_inverse=True)
            me = remesh(_mesh("tmp", pv[used], inv.reshape(-1, 3)), self.voxel, sc)
            rv = np.zeros(len(me.vertices) * 3, dtype=np.float64)
            me.vertices.foreach_get("co", rv)
            rv = rv.reshape(-1, 3)
            me.calc_loop_triangles()
            rt = np.zeros(len(me.loop_triangles) * 3, dtype=np.int64)
            me.loop_triangles.foreach_get("vertices", rt)
            rt = rt.reshape(-1, 3)
            owner = bone_fn(rv[rt].mean(axis=1), np.full(len(rt), 99.0))
            for i in np.unique(owner):
                sel = rt[owner == i]
                u, ii = np.unique(sel, return_inverse=True)
                low_v[int(i)].append(rv[u])
                low_t[int(i)].append(ii.reshape(-1, 3) + low_n[int(i)])
                low_n[int(i)] += len(u)
        total = 0
        for i, name in enumerate(names):
            parent, pivot, budget = self.bones[name]
            n_in = sum(len(x) for x in low_t[i])
            if n_in == 0:
                me = bpy.data.meshes.new(f"{self.name}_{name}")
            else:
                me = _mesh("tmp", np.concatenate(low_v[i]), np.concatenate(low_t[i]), None, mats)
                for _ in range(3):
                    if len(me.polygons) <= budget * 1.05:
                        break
                    me = decimate(me, max(0.03, budget / len(me.polygons)), "tmp_ob")
            sel = low_t[i]
            bm = bmesh.new()
            bm.from_mesh(me)
            bmesh.ops.translate(bm, verts=list(bm.verts), vec=-pivot)
            out = bpy.data.meshes.new(f"{self.name}_{name}")
            bm.to_mesh(out)
            bm.free()
            for m in mats if not out.materials else ():
                out.materials.append(m)
            ob = bpy.data.objects.new(name + "." + self.name, out)
            ob.location = pivot
            ob.rotation_mode = "XYZ"
            ob["pivot"] = list(pivot)
            ob["bone"] = name
            ob["parent"] = parent or ""
            sc.collection.objects.link(ob)
            self.objects[name] = ob
            total += len(out.polygons)
            print(name, "оболочка", n_in, "итог", len(out.polygons))
        print("всего граней:", total)
        # иерархия для просмотра в Blender
        bpy.context.view_layer.update()
        for name, ob in self.objects.items():
            p = self.bones[name][0]
            if p:
                ob.parent = self.objects[p]
                ob.matrix_parent_inverse = self.objects[p].matrix_world.inverted()
        # высокая детализация для запекания
        hi = _mesh(self.name + "_hi", verts, tris, mat_of, mats)
        if len(tris) > 700000:
            hi = decimate(hi, 700000 / len(tris), "hi_tmp")
        self.hi = hi
        self.verts, self.tris, self.bone_of, self.mat_of, self.sizes, self.parts = [], [], [], [], [], []
        return sc

    def add_kit_bone(self, name, parent, pivot, fill):
        """Кость, сделанная вручную из примитивов (fill(bm) пишет в мировых координатах)."""
        raise NotImplementedError


def _to_srgb(linear):
    linear = np.clip(linear, 0, 1)
    return np.where(linear <= 0.0031308, linear * 12.92, 1.055 * np.power(linear, 1 / 2.4) - 0.055)


def _blur(a, r):
    out = a.copy()
    for axis in (0, 1):
        s = np.zeros_like(out)
        for d in range(-r, r + 1):
            s += np.roll(out, d, axis=axis)
        out = s / (2 * r + 1)
    return out


def bake_export(c, size=2048, samples=20, tracks=None):
    """Развёртка, запекание с высокой детализации на низкую, цвет с подсветкой из нормалей, файлы мода."""
    name = c.name
    work = bpy.data.scenes.get("WB_Bake") or bpy.data.scenes.new("WB_Bake")
    for o in list(work.collection.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    window = bpy.context.window
    keep = window.scene
    window.scene = work
    try:
        work.render.engine = "CYCLES"
    except TypeError as e:
        raise RuntimeError(f"нужен Cycles: {e}")
    work.cycles.device = "CPU"
    work.cycles.samples = samples
    work.cycles.use_denoising = False
    work.render.bake.margin = 8
    work.render.bake.use_clear = True

    # все кости одним мешем в позе покоя; в слое граней номер кости
    names = list(c.objects)
    bm = bmesh.new()
    layer = bm.faces.layers.int.new("bone")
    for i, bone in enumerate(names):
        ob = c.objects[bone]
        pivot = ob["pivot"]
        tmp = bmesh.new()
        tmp.from_mesh(ob.data)
        vmap = {v: bm.verts.new((v.co.x + pivot[0], v.co.y + pivot[1], v.co.z + pivot[2])) for v in tmp.verts}
        for f in tmp.faces:
            try:
                nf = bm.faces.new([vmap[v] for v in f.verts])
            except ValueError:
                continue
            nf[layer] = i
        tmp.free()
    bmesh.ops.join_triangles(bm, faces=list(bm.faces), angle_face_threshold=math.radians(8), angle_shape_threshold=math.radians(60),
                             cmp_seam=False, cmp_sharp=False, cmp_uvs=False, cmp_vcols=False, cmp_materials=False)
    me = bpy.data.meshes.new(name + "_atlas")
    bm.to_mesh(me)
    bm.free()
    target = bpy.data.materials.new(name + "_target")
    target.use_nodes = True
    node = target.node_tree.nodes.new("ShaderNodeTexImage")
    target.node_tree.nodes.active = node
    me.materials.append(target)
    low = bpy.data.objects.new(name + "_atlas", me)
    hi = bpy.data.objects.new(name + "_hi", c.hi)
    work.collection.objects.link(low)
    work.collection.objects.link(hi)
    bpy.context.view_layer.objects.active = low
    low.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(50), island_margin=0.004, scale_to_bounds=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    hi.select_set(True)
    low.select_set(True)
    bpy.context.view_layer.objects.active = low
    diag = max(c.height, 1)

    def bake(kind, bake_type, **kw):
        t0 = time.time()
        img = bpy.data.images.get(f"{name}_{kind}")
        if img:
            bpy.data.images.remove(img)
        img = bpy.data.images.new(f"{name}_{kind}", size, size, alpha=True, float_buffer=True)
        node.image = img
        bpy.ops.object.bake(type=bake_type, use_selected_to_active=True, cage_extrusion=0.03 * diag, max_ray_distance=0.08 * diag, **kw)
        px = np.zeros(size * size * 4, dtype=np.float32)
        img.pixels.foreach_get(px)
        print(kind, round(time.time() - t0), "с")
        return px.reshape(size, size, 4)

    color = bake("color", "DIFFUSE", pass_filter={"COLOR"})
    normal = bake("normal", "NORMAL", normal_space="OBJECT")
    ao = bake("ao", "AO")

    n = normal[..., :3] * 2 - 1
    filled = (normal[..., 3] > 0.5)[..., None]
    n = n * filled + np.array([0, 0, 1], dtype=np.float32) * (1 - filled)
    top = n[..., 2:3] * 0.5 + 0.5
    # подсветка из нормалей исходника: верх светлее, бок к стрелку с лёгким бликом. Так мелкие детали видны без настоящей геометрии
    shade = 0.5 + 0.72 * top
    glint = np.clip(top - 0.72, 0, 1) ** 2 * 1.6
    cav = 0.25 + 0.75 * np.clip(ao[..., :1], 0, 1)
    # кромка: где нормаль отличается от усреднённой, там ребро. Рёбра стёрты до светлого металла
    edge = np.clip(np.linalg.norm(n - _blur(n, 3), axis=2, keepdims=True) * 2.2 - 0.12, 0, 1)
    lit = color[..., :3] * shade * cav * 1.5
    lit = lit * (1 + 1.2 * edge) + 0.045 * edge + glint * (0.08 + color[..., :3] * 0.6) * cav
    rgba = np.dstack((_to_srgb(lit), np.ones((size, size))))
    out_img = bpy.data.images.new("dr_save", size, size, alpha=True)
    out_img.pixels.foreach_set(rgba.astype(np.float32).ravel())
    tex = os.path.join(ASSETS, "textures", "entity", name + ".png")
    os.makedirs(os.path.dirname(tex), exist_ok=True)
    out_img.filepath_raw = tex
    out_img.file_format = "PNG"
    out_img.save()
    bpy.data.images.remove(out_img)

    # ---- меш по костям
    bm = bmesh.new()
    bm.from_mesh(me)
    uvl = bm.loops.layers.uv.active
    layer = bm.faces.layers.int.get("bone")
    out, total = [], 0
    for i, bone in enumerate(names):
        ob = c.objects[bone]
        pivot = ob["pivot"]
        positions, uvs, polys = [], [], []
        pos_idx, uv_idx = {}, {}
        for f in bm.faces:
            if f[layer] != i or len(f.verts) > 4:
                continue
            poly = []
            for loop in f.loops:
                p = loop.vert.co
                key = (round(p.x * 16, 3), round(p.z * 16, 3), round(p.y * 16, 3))
                pi = pos_idx.setdefault(key, len(pos_idx))
                if pi == len(positions) // 3:
                    positions.extend(key)
                uv = loop[uvl].uv
                ukey = (round(uv.x, 5), round(1 - uv.y, 5))
                ui = uv_idx.setdefault(ukey, len(uv_idx))
                if ui == len(uvs) // 2:
                    uvs.extend(ukey)
                poly.append([pi, 0, ui])
            if len(poly) == 3:
                poly.append(poly[-1])
            polys.append(poly)
        total += len(polys)
        entry = {"name": bone, "pivot": [round(pivot[0] * 16, 3), round(pivot[2] * 16, 3), round(pivot[1] * 16, 3)]}
        if ob["parent"]:
            entry["parent"] = ob["parent"]
        if polys:
            entry["poly_mesh"] = {"normalized_uvs": True, "positions": positions, "normals": [0, 1, 0], "uvs": uvs, "polys": polys}
        out.append(entry)
    bm.free()
    geo = {"format_version": "1.12.0", "minecraft:geometry": [{
        "description": {"identifier": f"geometry.warpbound.{name}", "texture_width": size, "texture_height": size},
        "bones": out}]}
    os.makedirs(os.path.join(ASSETS, "geo", "entity"), exist_ok=True)
    with open(os.path.join(ASSETS, "geo", "entity", name + ".geo.json"), "w", encoding="utf-8") as f:
        json.dump(geo, f, separators=(",", ":"))
    if tracks:
        os.makedirs(os.path.join(ASSETS, "animations", "entity"), exist_ok=True)
        with open(os.path.join(ASSETS, "animations", "entity", name + ".animation.json"), "w", encoding="utf-8") as f:
            json.dump({"format_version": "1.8.0", "animations": tracks}, f, separators=(",", ":"))
    window.scene = keep
    print(name, "граней в игре", total, "костей", len(out))
    return total


# ------------------------------------------------------------------ анимация

def tracks_from(pose, length, steps, loop=True, events=()):
    """Дорожки GeckoLib: поворот (X, -Z, Y) Blender, позиция (x, z, y) × 16."""
    bones = {}
    for i in range(steps + 1):
        t = i / steps
        key = f"{length * t:.4f}"
        for name, st in pose(t).items():
            b = bones.setdefault(name, {})
            if "rot" in st:
                x, y, z = st["rot"]
                b.setdefault("rotation", {})[key] = [round(x, 3), round(-z, 3), round(y, 3)]
            if "pos" in st:
                x, y, z = st["pos"]
                b.setdefault("position", {})[key] = [round(x * 16, 3), round(z * 16, 3), round(y * 16, 3)]
    out = {"loop": loop, "animation_length": length, "bones": bones}
    if events:
        out["sound_effects"] = {f"{at:.4f}": {"effect": name} for at, name in events}
    return out


def preview(c, pose, length):
    """Ключи в Blender: посмотреть движение до запуска игры."""
    frames = max(2, int(length * 24))
    rest = {n: ob.location.copy() for n, ob in c.objects.items()}
    for ob in c.objects.values():
        ob.animation_data_clear()
    for f in range(frames + 1):
        for name, st in pose(f / frames).items():
            ob = c.objects.get(name)
            if not ob:
                continue
            ob.location = rest[name] + Vector(st.get("pos", (0, 0, 0)))
            ob.rotation_euler = tuple(math.radians(v) for v in st.get("rot", (0, 0, 0)))
            ob.keyframe_insert("location", frame=f + 1)
            ob.keyframe_insert("rotation_euler", frame=f + 1)
    c.scene.frame_start, c.scene.frame_end = 1, frames + 1
    c.scene.frame_set(1)
