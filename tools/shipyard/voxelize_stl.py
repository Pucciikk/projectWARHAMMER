"""
Перевод 3D-модели (STL) в блоки: клетка сетки — блок, если её центр внутри модели
(чётность пересечений луча) или ближе 0,38 блока к поверхности (тонкие шпили и антенны).
Глубже 1,6 блока от поверхности — пусто: корпус выходит оболочкой, а не сплошным камнем.

Запускать в Blender (MCP или Scripting):
    STL, OUT, SCALE = r"<модель.stl>", r"<voxels.json>", 1.3
    exec(open(r"<проект>/tools/shipyard/voxelize_stl.py", encoding="utf-8").read())

Оси: Blender Z → Y Майнкрафта; нос модели (−Y Blender) уходит в +Z (корма у пульта верфи, z = 0).
Пишет {"size": [W, H, L], "vox": [[x, y, z, nx, ny, nz, dist, inside], ...], "core": [[x, y, z], ...]}:
vox — оболочка (нормаль ближайшей грани в осях MC), core — клетки глубже оболочки, внутри корпуса (место под отсеки).
"""
import json
import math

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def voxelize(stl, out, scale):
    sc = bpy.data.scenes.get("WB_Preview") or bpy.data.scenes.new("WB_Preview")
    bpy.context.window.scene = sc
    old = bpy.data.objects.get("WB_stl")
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    bpy.ops.wm.stl_import(filepath=stl)
    ob = bpy.context.selected_objects[0]
    ob.name = "WB_stl"
    bvh = BVHTree.FromObject(ob, bpy.context.evaluated_depsgraph_get())
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    x0, x1 = min(v.x for v in bb), max(v.x for v in bb)
    y1 = max(v.y for v in bb)
    y0 = min(v.y for v in bb)
    z0, z1 = min(v.z for v in bb), max(v.z for v in bb)
    cx = (x0 + x1) / 2
    W = int(math.ceil((x1 - x0) * scale)) + 3
    L = int(math.ceil((y1 - y0) * scale)) + 1
    H = int(math.ceil((z1 - z0) * scale)) + 1
    ray = Vector((0.0013, 0.0007, 1))

    def inside(p):
        n, q = 0, p.copy()
        for _ in range(80):
            hit = bvh.ray_cast(q, ray)
            if hit[0] is None:
                break
            n += 1
            q = hit[0] + ray * 1e-4
        return n % 2 == 1

    vox, core = [], []
    for ix in range(W):
        for iy in range(H):
            for iz in range(L):
                p = Vector((cx + (ix - W // 2) / scale, y1 - (iz + 0.5) / scale, z0 + (iy + 0.5) / scale))
                loc, nrm, _, dist = bvh.find_nearest(p)
                if loc is None:
                    continue
                if dist * scale > 1.6:
                    if inside(p):
                        core.append([ix, iy, iz])          # глубже оболочки — место под отсеки
                    continue
                ins = inside(p)
                if ins or dist * scale < 0.38:
                    vox.append([ix, iy, iz, round(nrm.x, 2), round(nrm.z, 2), round(-nrm.y, 2), round(dist * scale, 2), int(ins)])
    ob.hide_set(True)
    with open(out, "w") as f:
        json.dump({"size": [W, H, L], "scale": scale, "vox": vox, "core": core}, f)
    print(W, H, L, len(vox), len(core))


voxelize(STL, OUT, SCALE)  # noqa: F821 — задаются перед exec
