"""
Блочный вид фигур: оболочка каждой кости переводится в воксели общей сетки, грани сливаются в прямоугольники, текстура — настоящие пиксели с ограниченной палитрой.
Мелкие детали исходника не теряются: каждый пиксель смотрит лучом на исходную модель и берёт оттуда материал, наклон поверхности и глубину.
Значки и глаза (decals) рисуются пиксель в пиксель по броне.

Запуск внутри Blender после c.build: voxel_export(c, tracks=ANIMS, palette=PALETTE, decals=DECALS, cell=1/32, texels=2).
Результат те же файлы мода, что у bake_export: geo/entity, textures/entity (и _glow), animations/entity.
"""
import json
import os

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

# Палитра sRGB: базовый цвет материала. Тени и блики идут ступенями от него, в тенях цвет чуть холоднее
BASE_PALETTE = {
    "primary": (44, 78, 168), "trim": (216, 168, 62), "lens": (255, 44, 30), "dark": (50, 52, 60), "rubber": (30, 30, 35),
    "steel": (142, 148, 158), "bone": (214, 200, 164), "parchment": (228, 212, 172), "red": (152, 30, 28), "gold": (226, 178, 70),
    "brass": (170, 124, 58), "copper": (176, 96, 60), "black": (26, 26, 30), "blue": (44, 78, 168), "green": (40, 92, 56),
    "bronze": (172, 116, 56), "crimson": (138, 24, 30), "skin": (204, 154, 122),
}
LEVELS = np.array((0.5, 0.64, 0.78, 0.9, 1.0, 1.12, 1.26))      # ступени яркости
LIGHT = np.array((0.3, -0.45, 0.84))


class Decal:
    """Рисунок по броне. rows — строки, символ -> цвет из colors (точка — пусто). Проекция вдоль оси view ('x', 'y'), центр (a, b) в блоках: для view='y' это (x, z), для 'x' — (y, z). sign — с какой стороны смотрит рисунок."""

    def __init__(self, bones, view, sign, center, rows, colors, flip=False, pixel=None):
        self.bones, self.view, self.sign, self.center, self.colors, self.flip, self.pixel = set(bones), view, sign, center, colors, flip, pixel
        self.rows = rows[::-1]                # снизу вверх: так считать проще
        self.h, self.w = len(rows), len(rows[0])

    def at(self, bone, p, n, size):
        if bone not in self.bones:
            return None
        axis = 0 if self.view == "x" else 1
        if n[axis] * self.sign < -0.5:        # с обратной стороны рисунка нет, боковые ступени получают его продолжение
            return None
        s = self.pixel or size
        a = p[1] if self.view == "x" else p[0]
        col = int(np.floor((a - self.center[0]) / s + self.w / 2))
        row = int(np.floor((p[2] - self.center[1]) / s + self.h / 2))
        if self.flip:
            col = self.w - 1 - col
        if 0 <= col < self.w and 0 <= row < self.h:
            return self.colors.get(self.rows[row][col])
        return None


def box_mesh(center, size):
    """Замкнутый ящик: мелкие детали брони (подсумки, гранаты, антенна). Координаты те же, что у исходника."""
    cx, cy, cz = center
    sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2
    v = np.array([(cx + a * sx, cy + b * sy, cz + c_ * sz) for a in (-1, 1) for b in (-1, 1) for c_ in (-1, 1)], dtype=np.float64)
    q = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    t = np.array([tri for a, b, c_, d in q for tri in ((a, b, c_), (a, c_, d))], dtype=np.int64)
    return v, t


def _occupancy(verts, tris, cell):
    """Клетки, которых касается поверхность. Точки — вершины и центры граней оболочки: они намного мельче клетки."""
    pts = np.concatenate((verts, verts[tris].mean(axis=1)))
    idx = np.floor(pts / cell).astype(np.int64)
    lo = idx.min(axis=0) - 1
    hi = idx.max(axis=0) + 2
    grid = np.zeros(hi - lo + 1, dtype=bool)
    i = idx - lo
    grid[i[:, 0], i[:, 1], i[:, 2]] = True
    return grid, lo


def _solid(grid):
    """Всё, до чего нельзя дойти снаружи, — тело. Полые места заполняются, а наружу смотрят только настоящие грани."""
    ext = np.zeros(grid.shape, dtype=bool)
    ext[0, :, :] = ext[-1, :, :] = ext[:, 0, :] = ext[:, -1, :] = ext[:, :, 0] = ext[:, :, -1] = True
    ext &= ~grid
    while True:
        grown = ext.copy()
        grown[1:] |= ext[:-1]
        grown[:-1] |= ext[1:]
        grown[:, 1:] |= ext[:, :-1]
        grown[:, :-1] |= ext[:, 1:]
        grown[:, :, 1:] |= ext[:, :, :-1]
        grown[:, :, :-1] |= ext[:, :, 1:]
        grown &= ~grid
        if grown.sum() == ext.sum():
            return ~ext
        ext = grown


def _neighbours(s):
    n = np.zeros(s.shape, dtype=np.int8)
    n[1:] += s[:-1]
    n[:-1] += s[1:]
    n[:, 1:] += s[:, :-1]
    n[:, :-1] += s[:, 1:]
    n[:, :, 1:] += s[:, :, :-1]
    n[:, :, :-1] += s[:, :, 1:]
    return n


def _clean(s):
    """Одиночные торчащие кубики и ямки выглядят как шум: убираем."""
    for _ in range(2):
        n = _neighbours(s)
        s = (s & (n >= 2)) | (~s & (n >= 5))
    return s


def _rects(s):
    """Жадное слияние открытых граней. Возвращает (ось, знак, номер плоскости, начало по двум другим осям, размеры)."""
    out = []
    for a in range(3):
        b, c_ = (a + 1) % 3, (a + 2) % 3
        arr = np.transpose(s, (a, b, c_))
        for sign in (1, -1):
            for k in range(arr.shape[0]):
                nb = arr[k + sign] if 0 <= k + sign < arr.shape[0] else np.zeros(arr.shape[1:], dtype=bool)
                mask = arr[k] & ~nb
                if not mask.any():
                    continue
                mask = mask.copy()
                for u in range(mask.shape[0]):
                    v = 0
                    while v < mask.shape[1]:
                        if not mask[u, v]:
                            v += 1
                            continue
                        h = 1
                        while v + h < mask.shape[1] and mask[u, v + h]:
                            h += 1
                        w = 1
                        while u + w < mask.shape[0] and mask[u + w, v:v + h].all():
                            w += 1
                        mask[u:u + w, v:v + h] = False
                        out.append((a, sign, k, u, v, w, h))
                        v += h
    return out


def _pack(rects, t):
    """Полки по убыванию высоты. Возвращает размер атласа и места прямоугольников."""
    order = sorted(range(len(rects)), key=lambda i: -rects[i][1][1] * t)
    for size in (128, 256, 512, 1024, 2048, 4096):
        x = y = shelf = 0
        place = {}
        ok = True
        for i in order:
            w, h = rects[i][1][0] * t, rects[i][1][1] * t
            if x + w > size:
                x, y, shelf = 0, y + shelf + 1, 0
            if y + h > size:
                ok = False
                break
            place[i] = (x, y)
            x += w + 1
            shelf = max(shelf, h)
        if ok:
            return size, place
    raise RuntimeError("не влезает в 4096")


def _srgb_to_linear(c):
    c = np.asarray(c, dtype=np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def voxel_export(c, tracks=None, palette=None, decals=(), cell=1 / 32, texels=2, name=None, write=True, cleanup=True, edges=0, grain=0.03, ao_reach=0.06, relief=0.004):
    name = name or c.name
    pal = dict(BASE_PALETTE)
    pal.update(palette or {})
    rng = np.random.default_rng(40)
    px = cell / texels

    # ---- воксели по костям
    bones = {}
    rect_list = []        # (кость, (w, h), данные)
    for bone, (verts, tris) in c.shells.items():
        grid, lo = _occupancy(verts, tris, cell)
        s = _solid(grid)
        if cleanup:
            s = _clean(s)
        bones[bone] = (s, lo)
        for a, sign, k, u, v, w, h in _rects(s):
            rect_list.append((bone, (w, h), (a, sign, k, u, v)))
    print(name, "прямоугольников", len(rect_list), "пикселей", sum(w * h for _, (w, h), _ in rect_list) * texels ** 2)

    size, place = _pack(rect_list, texels)
    print("атлас", size)

    # ---- луч на исходник
    work = bpy.data.scenes.get("WB_Bake") or bpy.data.scenes.new("WB_Bake")
    for o in list(work.collection.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    hi_ob = bpy.data.objects.new(name + "_hi", c.hi)
    work.collection.objects.link(hi_ob)
    keep = bpy.context.window.scene
    bpy.context.window.scene = work
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    tree = BVHTree.FromObject(hi_ob, deps)
    mat_of = np.zeros(len(c.hi.polygons), dtype=np.int32)
    c.hi.polygons.foreach_get("material_index", mat_of)
    mat_names = [m.name[3:] if m.name.startswith("DR_") else m.name for m in c.hi.materials]
    bpy.context.window.scene = keep

    img = np.zeros((size, size, 4), dtype=np.float64)
    glow = np.zeros((size, size, 4), dtype=np.float64)
    misses = 0
    for ri, (bone, (w, h), (a, sign, k, u, v)) in enumerate(rect_list):
        s, lo = bones[bone]
        b, c_ = (a + 1) % 3, (a + 2) % 3
        x0, y0 = place[ri]
        normal = np.zeros(3)
        normal[a] = sign
        plane = (lo[a] + k + (1 if sign > 0 else 0)) * cell
        for tx in range(w * texels):
            for ty in range(h * texels):
                p = np.zeros(3)
                p[a] = plane
                p[b] = (lo[b] + u + (tx + 0.5) / texels) * cell
                p[c_] = (lo[c_] + v + (ty + 0.5) / texels) * cell
                origin = p + normal * cell * 0.9
                hit, hn, idx, dist = tree.ray_cast(Vector(origin), Vector(-normal), cell * 3)
                if hit is None:
                    hit, hn, idx, dist = tree.find_nearest(Vector(p), cell * 4)
                    depth = 0.0
                    if hit is None:
                        misses += 1
                        continue
                else:
                    depth = dist - cell * 0.9
                mat = mat_names[mat_of[idx]]
                base = pal.get(mat, pal["dark"])
                n = np.array(hn)
                if n @ normal < 0:
                    n = -n
                # затенение считаем по исходной модели, а не по ступенькам: щели и панели видны, а блоки не рябят
                nv = Vector(n)
                hp = hit + nv * 0.012
                occ = sum(1 for dv_ in _hemisphere(n) if tree.ray_cast(hp, Vector(dv_), ao_reach)[0] is not None)
                cav = occ / 5
                # рельеф: глубина соседних пикселей по той же оси. Выступ светлеет, шов темнеет: так проявляются панели, заклёпки и кабели
                lap = 0.0
                count = 0
                for ob_, oc_ in ((px, 0), (-px, 0), (0, px), (0, -px)):
                    o2 = origin.copy()
                    o2[b] += ob_
                    o2[c_] += oc_
                    r2 = tree.ray_cast(Vector(o2), Vector(-normal), cell * 3)
                    if r2[0] is not None:
                        lap += r2[3] - cell * 0.9 - depth
                        count += 1
                lap = lap / count if count else 0.0
                shade = (0.66 + 0.56 * max(0.0, float(n @ LIGHT))) * (1 - 0.4 * max(0.0, cav - 0.2))
                shade += float(np.clip(lap / relief, -1.0, 1.0)) * (0.3 if lap < 0 else 0.26)
                lvl = int(np.abs(LEVELS - shade).argmin())

                # кромки клеток: выступ светлее, угол темнее. Это и даёт вид нарисованной вручную брони
                cu = (u + tx // texels)
                cv = (v + ty // texels)
                ij = [0, 0, 0]
                ij[a], ij[b], ij[c_] = k, cu, cv
                for db, dc, on in ((1, 0, tx % texels == texels - 1), (-1, 0, tx % texels == 0), (0, 1, ty % texels == texels - 1), (0, -1, ty % texels == 0)):
                    if not on:
                        continue
                    q = list(ij)
                    q[b] += db
                    q[c_] += dc
                    if not _get(s, q):
                        lvl += edges                                             # выпуклое ребро
                    else:
                        q[a] += sign
                        if _get(s, q):
                            lvl -= edges * 2                                     # внутренний угол
                if rng.random() < grain:
                    lvl += 1 if rng.random() < 0.5 else -1                       # лёгкая зернистость, как у ванильных текстур
                lvl = int(np.clip(lvl, 0, len(LEVELS) - 1))

                color = None
                for d in decals:
                    got = d.at(bone, p, normal, px)
                    if got is not None:
                        color = got
                glowing = mat == "lens"
                if color is not None:
                    if color == "lens":
                        glowing = True
                    base = pal.get(color, pal["dark"])
                    lvl = int(np.clip(lvl, 3, 5))                                # рисунок читается: без глубоких теней
                rgb = np.array(base) / 255.0 * LEVELS[lvl]
                if LEVELS[lvl] < 0.8:                                            # тени чуть холоднее, блики чуть теплее
                    rgb = rgb * np.array((0.94, 0.97, 1.08))
                elif LEVELS[lvl] > 1.05:
                    rgb = rgb * np.array((1.04, 1.02, 0.96))
                rgb = np.clip(rgb, 0, 1)
                py = y0 + ty
                ix = x0 + tx
                img[py, ix] = (*rgb, 1)
                if glowing:
                    glow[py, ix] = (*np.clip(np.array(base) / 255.0 * 1.15, 0, 1), 1)
    print("промахов луча", misses)

    # края чуть заливаем цветом соседа: при сильном удалении соседние пиксели не дают чёрных швов
    filled = img[..., 3] > 0
    for _ in range(1):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            shifted = np.roll(np.roll(img, dy, axis=0), dx, axis=1)
            take = ~filled & (shifted[..., 3] > 0)
            img[take] = shifted[take]
            filled |= take
    img[~filled] = (0, 0, 0, 1)

    # ---- меш и файлы
    objects = {}
    out = []
    faces_total = 0
    grouped = {}
    for ri, (bone, dims, data) in enumerate(rect_list):
        grouped.setdefault(bone, []).append((ri, dims, data))
    eps = 0.02 / size
    for bone in c.bones:
        pivot = list(c.bones[bone][1])
        parent = c.bones[bone][0]
        positions, uvs, polys = [], [], []
        pos_idx, uv_idx = {}, {}
        for ri, (w, h), (a, sign, k, u, v) in grouped.get(bone, []):
            s, lo = bones[bone]
            b, c_ = (a + 1) % 3, (a + 2) % 3
            x0, y0 = place[ri]
            corners = [(0, 0), (w, 0), (w, h), (0, h)]
            if sign < 0:
                corners = corners[::-1]
            poly = []
            for du, dv in corners:
                p = [0.0, 0.0, 0.0]
                p[a] = (lo[a] + k + (1 if sign > 0 else 0)) * cell
                p[b] = (lo[b] + u + du) * cell
                p[c_] = (lo[c_] + v + dv) * cell
                key = (round(p[0] * 16, 3), round(p[2] * 16, 3), round(p[1] * 16, 3))
                pi = pos_idx.setdefault(key, len(pos_idx))
                if pi == len(positions) // 3:
                    positions.extend(key)
                uu = (x0 + du * texels) / size + (eps if du == 0 else -eps)
                vv = (y0 + dv * texels) / size + (eps if dv == 0 else -eps)
                ukey = (round(uu, 6), round(vv, 6))
                ui = uv_idx.setdefault(ukey, len(uv_idx))
                if ui == len(uvs) // 2:
                    uvs.extend(ukey)
                poly.append([pi, 0, ui])
            polys.append(poly)
        faces_total += len(polys)
        entry = {"name": bone, "pivot": [round(pivot[0] * 16, 3), round(pivot[2] * 16, 3), round(pivot[1] * 16, 3)]}
        if parent:
            entry["parent"] = parent
        if polys:
            entry["poly_mesh"] = {"normalized_uvs": True, "positions": positions, "normals": [0, 1, 0], "uvs": uvs, "polys": polys}
        out.append(entry)
    print(name, "граней в игре", faces_total, "атлас", size)

    if write:
        assets = os.path.join(ROOT, "src/main/resources/assets/warpbound")
        _save_png(img, os.path.join(assets, "textures", "entity", name + ".png"))
        glow_path = os.path.join(assets, "textures", "entity", name + "_glow.png")
        if glow[..., 3].any():
            _save_png(glow, glow_path)
        geo = {"format_version": "1.12.0", "minecraft:geometry": [{"description": {"identifier": f"geometry.warpbound.{name}", "texture_width": size, "texture_height": size}, "bones": out}]}
        with open(os.path.join(assets, "geo", "entity", name + ".geo.json"), "w", encoding="utf-8") as f:
            json.dump(geo, f, separators=(",", ":"))
        if tracks:
            with open(os.path.join(assets, "animations", "entity", name + ".animation.json"), "w", encoding="utf-8") as f:
                json.dump({"format_version": "1.8.0", "animations": tracks}, f, separators=(",", ":"))
    _preview_scene(c, name, out, img, size)
    return faces_total


def _hemisphere(n):
    """Пять лучей вокруг нормали: прямо и под углом 55 градусов."""
    n = np.asarray(n)
    t = np.cross(n, (0.0, 0.0, 1.0) if abs(n[2]) < 0.9 else (1.0, 0.0, 0.0))
    t = t / np.linalg.norm(t)
    b = np.cross(n, t)
    return (n, n * 0.57 + t * 0.82, n * 0.57 - t * 0.82, n * 0.57 + b * 0.82, n * 0.57 - b * 0.82)


def _get(s, q):
    if min(q) < 0 or q[0] >= s.shape[0] or q[1] >= s.shape[1] or q[2] >= s.shape[2]:
        return False
    return bool(s[q[0], q[1], q[2]])


def _save_png(rgba, path):
    size = rgba.shape[0]
    im = bpy.data.images.new("vox_save", size, size, alpha=True)
    im.pixels.foreach_set(rgba[::-1].astype(np.float32).ravel())    # в Blender строки идут снизу вверх
    im.filepath_raw = path
    im.file_format = "PNG"
    im.save()
    bpy.data.images.remove(im)


def _preview_scene(c, name, geo_bones, img, size):
    """Сцена WB_vox_<имя>: кости отдельными объектами с пикселями без сглаживания, как в игре."""
    sc = bpy.data.scenes.get("WB_vox_" + name) or bpy.data.scenes.new("WB_vox_" + name)
    for o in list(sc.collection.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    im = bpy.data.images.get("vox_" + name)
    if im:
        bpy.data.images.remove(im)
    im = bpy.data.images.new("vox_" + name, size, size, alpha=True)
    im.pixels.foreach_set(img[::-1].astype(np.float32).ravel())
    im.pack()
    mat = bpy.data.materials.get("WB_vox_view_" + name) or bpy.data.materials.new("WB_vox_view_" + name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out_n = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = im
    tx.interpolation = "Closest"
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    dot.inputs[1].default_value = (0.25, -0.35, 0.9)
    nt.links.new(geo.outputs["Normal"], dot.inputs[0])
    ramp = nt.nodes.new("ShaderNodeMapRange")
    ramp.inputs["From Min"].default_value = -1
    ramp.inputs["From Max"].default_value = 1
    ramp.inputs["To Min"].default_value = 0.55
    ramp.inputs["To Max"].default_value = 1.05
    nt.links.new(dot.outputs["Value"], ramp.inputs["Value"])
    mul = nt.nodes.new("ShaderNodeVectorMath")
    mul.operation = "SCALE"
    nt.links.new(tx.outputs[0], mul.inputs[0])
    nt.links.new(ramp.outputs[0], mul.inputs["Scale"])
    nt.links.new(mul.outputs[0], em.inputs[0])
    nt.links.new(em.outputs[0], out_n.inputs[0])

    objects = {}
    for e in geo_bones:
        pivot = (e["pivot"][0] / 16, e["pivot"][2] / 16, e["pivot"][1] / 16)
        me = bpy.data.meshes.new(f"vox_{name}_{e['name']}")
        pm = e.get("poly_mesh")
        if pm:
            p = np.array(pm["positions"], dtype=np.float64).reshape(-1, 3) / 16
            verts = [(x - pivot[0], z - pivot[1], y - pivot[2]) for x, y, z in p]
            # треугольник в формате мода — четырёхугольник с повтором последней вершины
            polys_view = [poly[:3] if poly[2][0] == poly[3][0] else poly for poly in pm["polys"]]
            faces = [[v[0] for v in poly] for poly in polys_view]
            me.from_pydata(verts, [], faces)
            uv = me.uv_layers.new()
            uvs = np.array(pm["uvs"]).reshape(-1, 2)
            i = 0
            for poly in polys_view:
                for v in poly:
                    uu, vv = uvs[v[2]]
                    uv.data[i].uv = (uu, 1 - vv)
                    i += 1
            me.materials.append(mat)
        ob = bpy.data.objects.new(e["name"] + "." + name, me)
        ob.location = pivot
        ob.rotation_mode = "XYZ"
        ob["pivot"] = list(pivot)
        ob["bone"] = e["name"]
        sc.collection.objects.link(ob)
        objects[e["name"]] = ob
    bpy.context.window.scene = sc
    bpy.context.view_layer.update()
    for e in geo_bones:
        if e.get("parent"):
            child, par = objects[e["name"]], objects[e["parent"]]
            child.parent = par
            child.matrix_parent_inverse = par.matrix_world.inverted()
    c.objects = objects
    c.scene = sc


# ------------------------------------------------------------------ гранёный вид: те же пиксели, но форма из плоских фасеток, без ступенек

FINE_LEVELS = np.array((0.46, 0.56, 0.66, 0.76, 0.86, 0.95, 1.04, 1.14, 1.26))


def _taubin(v, q, steps=4):
    """Сглаживание без усадки: ступеньки сглаживаются, объём остаётся."""
    a = np.concatenate([q[:, i] for i in range(4)])
    b = np.concatenate([q[:, (i + 1) % 4] for i in range(4)])
    for _ in range(steps):
        for k in (0.5, -0.53):
            s = np.zeros_like(v)
            np.add.at(s, a, v[b])
            np.add.at(s, b, v[a])
            n = np.zeros(len(v))
            np.add.at(n, a, 1)
            np.add.at(n, b, 1)
            v = v + k * (s / np.maximum(n, 1)[:, None] - v)
    return v


def _surface(s, lo, cell):
    """Открытые грани вокселей с общими вершинами: замкнутая поверхность тела."""
    index = {}
    verts, quads = [], []

    def vid(i, j, k_):
        key = (i, j, k_)
        got = index.get(key)
        if got is None:
            got = index[key] = len(verts)
            verts.append(((i + lo[0]) * cell, (j + lo[1]) * cell, (k_ + lo[2]) * cell))
        return got

    pad = np.pad(s, 1)
    for a in range(3):
        b, c_ = (a + 1) % 3, (a + 2) % 3
        for sign in (1, -1):
            shifted = np.roll(pad, -sign, axis=a)
            cells = np.argwhere(pad & ~shifted) - 1
            for cl in cells.tolist():
                base = list(cl)
                if sign > 0:
                    base[a] += 1
                o = []
                for du, dv in ((0, 0), (1, 0), (1, 1), (0, 1)):
                    p = list(base)
                    p[b] += du
                    p[c_] += dv
                    o.append(vid(*p))
                quads.append(o if sign > 0 else o[::-1])
    return np.array(verts, dtype=np.float64), np.array(quads, dtype=np.int64)


def _decimated(verts, faces, budget, scene):
    """Упрощение до бюджета. Возвращает bmesh c плоскими фасетками, почти плоские пары треугольников объединены."""
    me = bpy.data.meshes.new("fac_tmp")
    me.from_pydata(verts.tolist(), [], faces.tolist())
    me.update()
    ob = bpy.data.objects.new("fac_tmp", me)
    scene.collection.objects.link(ob)
    n = max(1, sum(len(f) - 2 for f in faces.tolist()))
    if n > budget:
        d = ob.modifiers.new("d", "DECIMATE")
        d.ratio = max(0.01, budget / n)
        d.use_collapse_triangulate = True
    bpy.context.view_layer.update()
    out = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(ob, do_unlink=True)
    bm = bmesh.new()
    bm.from_mesh(out)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    bmesh.ops.join_triangles(bm, faces=list(bm.faces), angle_face_threshold=np.radians(6), angle_shape_threshold=np.radians(50), cmp_seam=False, cmp_sharp=False, cmp_uvs=False, cmp_vcols=False, cmp_materials=False)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bm.normal_update()
    return bm


def _tri_cells(uv):
    """Пиксели, чей центр внутри треугольника, и барицентрические координаты."""
    (x0, y0), (x1, y1), (x2, y2) = uv
    d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    if abs(d) < 1e-9:
        return
    for x in range(int(np.floor(min(x0, x1, x2))), int(np.ceil(max(x0, x1, x2)))):
        for y in range(int(np.floor(min(y0, y1, y2))), int(np.ceil(max(y0, y1, y2)))):
            px_, py_ = x + 0.5, y + 0.5
            w0 = ((y1 - y2) * (px_ - x2) + (x2 - x1) * (py_ - y2)) / d
            w1 = ((y2 - y0) * (px_ - x2) + (x0 - x2) * (py_ - y2)) / d
            w2 = 1 - w0 - w1
            if w0 >= -1e-6 and w1 >= -1e-6 and w2 >= -1e-6:
                yield x, y, w0, w1, w2


def facet_export(c, tracks=None, palette=None, decals=(), cell=1 / 32, pixel=1 / 80, fine=None, budget=0.8, exact=(), name=None, write=True,
                 grain=0.015, ao_reach=0.06, relief=0.004, smooth_steps=3, dead=0.0025, cells=None, prebuilt=None, edge_light=0, levels=None):
    """Гранёная модель с пиксельной текстурой. fine — кости с вдвое более мелкими пикселями (лицо). exact — кости, которые не проходят через воксели (линзы, антенна)."""
    name = name or c.name
    fine = set(fine or ())
    pal = dict(BASE_PALETTE)
    pal.update(palette or {})
    rng = np.random.default_rng(40)
    work = bpy.data.scenes.get("WB_Bake") or bpy.data.scenes.new("WB_Bake")
    for o in list(work.collection.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    keep = bpy.context.window.scene
    bpy.context.window.scene = work

    bms = prebuilt if prebuilt is not None else {}
    for bone, (verts, tris) in ({} if prebuilt is not None else c.shells).items():
        budget_b = max(12, int(c.bones[bone][2] * budget))
        if bone in exact:
            bms[bone] = _decimated(verts, tris, budget_b, work)
            continue
        bone_cell = (cells or {}).get(bone, cell)     # голове сетка мельче: иначе лицо не успевает сложиться
        grid, lo = _occupancy(verts, tris, bone_cell)
        s = _clean(_solid(grid))
        v, q = _surface(s, lo, bone_cell)
        if not len(q):
            continue
        bms[bone] = _decimated(_taubin(v, q, smooth_steps), q, budget_b, work)

    # ---- карты: связные грани с общей главной осью проецируются на её плоскость. Сетка пикселей совпадает с осями мира
    charts = []
    for bone, bm in bms.items():
        px = pixel / 2 if bone in fine else pixel
        bm.faces.ensure_lookup_table()
        done = set()
        key_of = {}
        for f in bm.faces:
            n = f.normal
            a = int(np.argmax(np.abs(n[:])))
            key_of[f.index] = (a, 1 if n[a] >= 0 else -1)
        for f in bm.faces:
            if f.index in done:
                continue
            a, sign = key_of[f.index]
            b_, c2 = (a + 1) % 3, (a + 2) % 3
            occupied = set()
            members = []
            stack = [f]
            while stack:
                g = stack.pop()
                if g.index in done or key_of[g.index] != (a, sign):
                    continue
                uv = [(v.co[b_] / px, v.co[c2] / px) for v in g.verts]
                vs = list(g.verts)
                cells = set()
                for tri in ((0, 1, 2), (0, 2, 3)) if len(vs) == 4 else ((0, 1, 2),):
                    cells.update((x, y) for x, y, *_w in _tri_cells([uv[i] for i in tri]))
                if cells & occupied:
                    continue       # наложилось на себя: уйдёт в другую карту
                occupied |= cells
                members.append(g)
                done.add(g.index)
                for e in g.edges:
                    for h in e.link_faces:
                        if h.index not in done:
                            stack.append(h)
            charts.append(dict(bone=bone, a=a, sign=sign, faces=members, px=px))

    # ---- упаковка
    PAD = 2
    for ch in charts:
        coords = [(v.co[(ch["a"] + 1) % 3] / ch["px"], v.co[(ch["a"] + 2) % 3] / ch["px"]) for f in ch["faces"] for v in f.verts]
        us, vs = zip(*coords)
        ch["u0"], ch["v0"] = int(np.floor(min(us))) - PAD, int(np.floor(min(vs))) - PAD
        ch["w"], ch["h"] = int(np.ceil(max(us))) + PAD - ch["u0"], int(np.ceil(max(vs))) + PAD - ch["v0"]
    order = sorted(range(len(charts)), key=lambda i: -charts[i]["h"])
    for size in (256, 512, 1024, 2048, 4096):
        x = y = shelf = 0
        ok = True
        for i in order:
            ch = charts[i]
            if x + ch["w"] > size:
                x, y, shelf = 0, y + shelf, 0
            if y + ch["h"] > size:
                ok = False
                break
            ch["x"], ch["y"] = x, y
            x += ch["w"]
            shelf = max(shelf, ch["h"])
        if ok:
            break
    else:
        raise RuntimeError("атлас не влез в 4096")
    print(name, "карт", len(charts), "атлас", size)

    # ---- луч на исходник
    hi_ob = bpy.data.objects.new(name + "_hi", c.hi)
    work.collection.objects.link(hi_ob)
    bpy.context.view_layer.update()
    tree = BVHTree.FromObject(hi_ob, bpy.context.evaluated_depsgraph_get())
    mat_of = np.zeros(len(c.hi.polygons), dtype=np.int32)
    c.hi.polygons.foreach_get("material_index", mat_of)
    mat_names = [m_.name[3:] if m_.name.startswith("DR_") else m_.name for m_ in c.hi.materials]
    bpy.context.window.scene = keep

    img = np.zeros((size, size, 4), dtype=np.float64)
    glow = np.zeros((size, size, 4), dtype=np.float64)
    painted = 0
    for ch in charts:
        a, sign, px, bone = ch["a"], ch["sign"], ch["px"], ch["bone"]
        b_, c2 = (a + 1) % 3, (a + 2) % 3
        normal = np.zeros(3)
        normal[a] = sign
        offset = 0.03
        cells = {}
        for f in ch["faces"]:
            vs = list(f.verts)
            uv = [(v.co[b_] / px, v.co[c2] / px) for v in vs]
            for tri in ((0, 1, 2), (0, 2, 3)) if len(vs) == 4 else ((0, 1, 2),):
                for x_, y_, w0, w1, w2 in _tri_cells([uv[i] for i in tri]):
                    cells[(x_, y_)] = w0 * vs[tri[0]].co[a] + w1 * vs[tri[1]].co[a] + w2 * vs[tri[2]].co[a]
        inner = set(cells)
        # край: пиксели вокруг карты тоже закрашиваем, иначе на стыках фасеток просвечивает фон
        for _ in range(2):
            grown = dict(cells)
            for (x_, y_), h in cells.items():
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    grown.setdefault((x_ + dx, y_ + dy), h)
            cells = grown
        res = {}
        for (x_, y_), plane in cells.items():
            ix, iy = x_ - ch["u0"] + ch["x"], y_ - ch["v0"] + ch["y"]
            if not (ch["x"] <= ix < ch["x"] + ch["w"] and ch["y"] <= iy < ch["y"] + ch["h"]):
                continue
            p = np.zeros(3)
            p[a], p[b_], p[c2] = plane, (x_ + 0.5) * px, (y_ + 0.5) * px
            origin = p + normal * offset
            hit, hn, idx, dist = tree.ray_cast(Vector(origin), Vector(-normal), 0.34)
            depth = (dist - offset) if hit is not None else 0.0
            if hit is None:
                hit, hn, idx, dist = tree.find_nearest(Vector(p), 0.4)
                if hit is None:
                    continue
            mat = mat_names[mat_of[idx]]
            base = pal.get(mat, pal["dark"])
            n = np.array(hn)
            if n @ normal < 0:
                n = -n
            nv = Vector(n)
            hp = hit + nv * 0.012
            occ = sum(1 for dv_ in _hemisphere(n) if tree.ray_cast(hp, Vector(dv_), ao_reach)[0] is not None)
            cav = occ / 5
            lap, count = 0.0, 0
            for ob_, oc_ in ((px, 0), (-px, 0), (0, px), (0, -px)):
                o2 = origin.copy()
                o2[b_] += ob_
                o2[c2] += oc_
                r2 = tree.ray_cast(Vector(o2), Vector(-normal), 0.34)
                if r2[0] is not None:
                    lap += r2[3] - offset - depth
                    count += 1
            lap = lap / count if count else 0.0
            shade = (0.68 + 0.42 * max(0.0, float(n @ LIGHT))) * (1 - 0.38 * max(0.0, cav - 0.3))
            # мелкая неровность скульптуры — не деталь: только настоящие швы и выступы
            lap = lap - np.sign(lap) * min(abs(lap), dead)
            shade += float(np.clip(lap / relief, -1.0, 1.0)) * (0.3 if lap < 0 else 0.2)
            ramp = FINE_LEVELS if levels is None else levels
            lvl = int(np.abs(ramp - shade).argmin())
            if rng.random() < grain:
                lvl += 1 if rng.random() < 0.5 else -1
            # светлая кромка по краю грани: как у нарисованной вручную брони, форма читается и без теней
            if edge_light and any((x_ + dx, y_ + dy) not in inner for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                lvl += edge_light
            lvl = int(np.clip(lvl, 0, len(ramp) - 1))
            color = None
            for d in decals:
                got = d.at(bone, p, normal, px)
                if got is not None:
                    color = got
            glowing = mat == "lens"
            if color is not None:
                glowing = color == "lens"
                base = pal.get(color, pal["dark"])
                lvl = int(np.clip(lvl, len(ramp) // 2, len(ramp) - 2))
            res[(ix, iy)] = (base, lvl, glowing, color is not None)
        # медиана по соседям того же цвета: одиночные пиксели шума уходят, линии панелей остаются
        for (ix, iy), (base, lvl, glowing, drawn) in res.items():
            if not drawn:
                near = [res[q][1] for q in ((ix + i, iy + j) for i in (-1, 0, 1) for j in (-1, 0, 1)) if q in res and res[q][0] == base and not res[q][3]]
                lvl = int(np.median(near)) if near else lvl
            k = ramp[lvl]
            rgb = np.array(base) / 255.0 * k
            if k < 0.7:
                rgb = rgb * np.array((0.94, 0.97, 1.07))
            elif k > 1.1:
                rgb = rgb * np.array((1.03, 1.02, 0.97))
            img[iy, ix] = (*np.clip(rgb, 0, 1), 1)
            painted += 1
            if glowing:
                glow[iy, ix] = (*np.clip(np.array(base) / 255.0, 0, 1), 1)
    img[img[..., 3] == 0] = (0, 0, 0, 1)
    print("пикселей", painted)

    # ---- файлы
    out = []
    total = 0
    by_bone = {}
    for ch in charts:
        by_bone.setdefault(ch["bone"], []).append(ch)
    eps = 0.0
    for bone in c.bones:
        pivot = list(c.bones[bone][1])
        positions, uvs, polys = [], [], []
        pos_idx, uv_idx = {}, {}
        for ch in by_bone.get(bone, []):
            b_, c2 = (ch["a"] + 1) % 3, (ch["a"] + 2) % 3
            for f in ch["faces"]:
                poly = []
                for v in f.verts:
                    co = v.co
                    key = (round(co.x * 16, 3), round(co.z * 16, 3), round(co.y * 16, 3))
                    pi = pos_idx.setdefault(key, len(pos_idx))
                    if pi == len(positions) // 3:
                        positions.extend(key)
                    uu = (co[b_] / ch["px"] - ch["u0"] + ch["x"]) / size
                    vv = (co[c2] / ch["px"] - ch["v0"] + ch["y"]) / size
                    ukey = (round(uu, 6), round(vv, 6))
                    ui = uv_idx.setdefault(ukey, len(uv_idx))
                    if ui == len(uvs) // 2:
                        uvs.extend(ukey)
                    poly.append([pi, 0, ui])
                if len(poly) == 3:
                    poly.append(poly[-1])
                polys.append(poly)
        total += len(polys)
        entry = {"name": bone, "pivot": [round(pivot[0] * 16, 3), round(pivot[2] * 16, 3), round(pivot[1] * 16, 3)]}
        if c.bones[bone][0]:
            entry["parent"] = c.bones[bone][0]
        if polys:
            entry["poly_mesh"] = {"normalized_uvs": True, "positions": positions, "normals": [0, 1, 0], "uvs": uvs, "polys": polys}
        out.append(entry)
    for bm in bms.values():
        bm.free()
    print(name, "граней в игре", total)
    if write:
        assets = os.path.join(ROOT, "src/main/resources/assets/warpbound")
        _save_png(img, os.path.join(assets, "textures", "entity", name + ".png"))
        if glow[..., 3].any():
            _save_png(glow, os.path.join(assets, "textures", "entity", name + "_glow.png"))
        geo = {"format_version": "1.12.0", "minecraft:geometry": [{"description": {"identifier": f"geometry.warpbound.{name}", "texture_width": size, "texture_height": size}, "bones": out}]}
        with open(os.path.join(assets, "geo", "entity", name + ".geo.json"), "w", encoding="utf-8") as f_:
            json.dump(geo, f_, separators=(",", ":"))
        if tracks:
            with open(os.path.join(assets, "animations", "entity", name + ".animation.json"), "w", encoding="utf-8") as f_:
                json.dump({"format_version": "1.8.0", "animations": tracks}, f_, separators=(",", ":"))
    _preview_scene(c, name, out, img, size)
    return total

# ------------------------------------------------------------------ простые формы: кольца и коробки, только четырёхугольники

CRISP_LEVELS = np.array((0.42, 0.58, 0.74, 0.88, 1.0, 1.14, 1.3))
_DIRS = [(np.cos(a), np.sin(a)) for a in np.radians(np.arange(0, 360, 45))]


def _octagon(pts2):
    """Восьмигранник вокруг точек: по осям и по диагоналям. Фаска есть всегда, поэтому у грани всегда четыре вершины."""
    ext = np.array([(pts2 @ np.array(d)).max() for d in _DIRS])
    for i in range(1, 8, 2):
        limit = (ext[i - 1] + ext[(i + 1) % 8]) / np.sqrt(2) - 0.006
        ext[i] = min(ext[i], limit)
    return ext


def _ring(ext):
    """Углы восьмигранника: пересечения соседних сторон, против часовой стрелки."""
    out = []
    for i in range(8):
        a1, a2 = np.array(_DIRS[i]), np.array(_DIRS[(i + 1) % 8])
        out.append(np.linalg.solve(np.array((a1, a2)), np.array((ext[i], ext[(i + 1) % 8]))))
    return out


def _simplify(ts, exts, tol):
    """Сокращает кольца: оставляет те, без которых контур уходит дальше tol."""
    keep = {0, len(ts) - 1}

    def walk(i, j):
        if j <= i + 1:
            return
        k = (ts[i + 1:j] - ts[i]) / max(ts[j] - ts[i], 1e-9)
        err = np.abs(exts[i] + k[:, None] * (exts[j] - exts[i]) - exts[i + 1:j]).max(axis=1)
        m_ = int(err.argmax())
        if err[m_] > tol:
            at = i + 1 + m_
            keep.add(at)
            walk(i, at)
            walk(at, j)
    walk(0, len(ts) - 1)
    return sorted(keep)


def _add_stack(bm, pts, axis, step, tol):
    if len(pts) < 8:
        return
    a, b_, c2 = axis, (axis + 1) % 3, (axis + 2) % 3
    t = pts[:, a]
    lo, hi = t.min(), t.max()
    n = max(1, int(np.ceil((hi - lo) / step)))
    ts, exts = [], []
    for i in range(n + 1):
        t0 = lo + (i - 0.5) * (hi - lo) / n
        t1 = lo + (i + 0.5) * (hi - lo) / n
        sel = pts[(t >= t0) & (t <= t1)]
        if len(sel) < 3:
            continue
        ts.append(lo + i * (hi - lo) / n)
        exts.append(_octagon(sel[:, [b_, c2]]))
    if len(ts) < 2:
        return
    ts, exts = np.array(ts), np.array(exts)
    keep = _simplify(ts, exts, tol)
    rings = []
    for i in keep:
        vs = []
        for u, v in _ring(exts[i]):
            co = [0.0, 0.0, 0.0]
            co[a], co[b_], co[c2] = ts[i], u, v
            vs.append(bm.verts.new(co))
        rings.append(vs)
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(8):
            j = (i + 1) % 8
            bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
    for ring, flip in ((rings[0], True), (rings[-1], False)):
        for q in ((0, 1, 2, 3), (0, 3, 4, 7), (7, 4, 5, 6)):
            vs = [ring[i] for i in q]
            bm.faces.new(vs[::-1] if flip else vs)


def _add_box(bm, center, size):
    v, t = box_mesh(center, size)
    vs = [bm.verts.new(x) for x in v.tolist()]
    for q in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
        bm.faces.new([vs[i] for i in q])


def stack_model(c, pieces, boxes, step=0.03, tol=0.012):
    """Кость -> список (ось, фильтр точек или None). Точки — оболочка кости из build. boxes: (кость, центр, размер) в игровых координатах."""
    bms = {}
    for bone, (verts, tris) in c.shells.items():
        bm = bms.setdefault(bone, bmesh.new())
        for axis, where in pieces.get(bone, ((2, None),)):
            pts = verts if where is None else verts[where(verts)]
            _add_stack(bm, pts, axis, step, tol)
    for bone, center, size in boxes:
        _add_box(bms.setdefault(bone, bmesh.new()), center, size)
    for bm in bms.values():
        bm.normal_update()
        bm.faces.ensure_lookup_table()
    return bms