"""
Просмотр моделей GeckoLib мода в Blender — быстрый цикл правок без запуска Minecraft.

В Blender (Scripting или MCP):
    exec(open(r"<проект>/tools/models/blender_preview.py", encoding="utf-8").read())
    show(["tech_priest", ("tech_priest", "dark_tech_priest")])

Каждая модель встаёт в ряд вдоль X в отдельной сцене WB_Preview (сцены автора не трогаются).
Перед модели смотрит на -Y (вид спереди в Blender), правая рука — слева от зрителя, как в игре.
Повороты костей — как у GeckoLib: X и Y с обратным знаком, порядок Z·Y·X вокруг pivot.
"""
import json
import math
import os

import bpy
import bmesh
from mathutils import Matrix, Vector

try:
    ASSETS = os.path.join(PROJECT, "src/main/resources/assets/warpbound")  # noqa: F821 — задаётся перед exec
except NameError:
    ASSETS = r"C:/Users/Name/projectWARHAMMER/src/main/resources/assets/warpbound"


_KIND = ["entity"]  # block: — модели машин (geo/block, textures/block)


def _rot(r, pivot):
    """Матрица поворота GeckoLib вокруг pivot (в пикселях Bedrock)."""
    rx, ry, rz = (math.radians(v) for v in (r or [0, 0, 0]))
    p = Vector(pivot)
    m = Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(-ry, 4, "Y") @ Matrix.Rotation(-rx, 4, "X")
    return Matrix.Translation(p) @ m @ Matrix.Translation(-p)


def _scene():
    sc = bpy.data.scenes.get("WB_Preview") or bpy.data.scenes.new("WB_Preview")
    bpy.context.window.scene = sc
    for o in list(sc.collection.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in [
        e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE"
    world = sc.world or bpy.data.worlds.new("WB_World")
    sc.world = world
    world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = (0.55, 0.6, 0.68, 1)
    bg.inputs[1].default_value = 0.9
    sun = bpy.data.lights.get("WB_Sun") or bpy.data.lights.new("WB_Sun", "SUN")
    sun.energy = 3.0
    so = bpy.data.objects.new("WB_Sun", sun)
    so.rotation_euler = (math.radians(50), math.radians(10), math.radians(-35))
    sc.collection.objects.link(so)
    return sc


def _material(texture):
    name = "WB_" + texture
    mat = bpy.data.materials.get(name)
    if mat:
        bpy.data.materials.remove(mat)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.8
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.interpolation = "Closest"
    tex.image = _image(os.path.join(ASSETS, "textures/" + _KIND[0], texture + ".png"))
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    glow_path = os.path.join(ASSETS, "textures/" + _KIND[0], texture + "_glow.png")
    if os.path.exists(glow_path):
        g = nt.nodes.new("ShaderNodeTexImage")
        g.interpolation = "Closest"
        g.image = _image(glow_path)
        nt.links.new(g.outputs["Color"], bsdf.inputs["Emission Color"])
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = 4.0
        nt.links.new(g.outputs["Alpha"], mul.inputs[0])
        nt.links.new(mul.outputs[0], bsdf.inputs["Emission Strength"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    try:
        mat.blend_method = "CLIP"
    except Exception:
        pass
    return mat


def _image(path):
    img = bpy.data.images.get(os.path.basename(path))
    if img:
        img.filepath = path
        img.reload()
        return img
    return bpy.data.images.load(path)


def _faces(uv, size):
    """Box-UV: грани -> прямоугольник в пикселях текстуры (как в tools/models/geo.py)."""
    u, v = uv
    w, h, d = size
    return {
        "up": (u + d, v, w, d), "down": (u + d + w, v, w, d),
        "east": (u, v + d, d, h), "north": (u + d, v + d, w, h),
        "west": (u + d + w, v + d, d, h), "south": (u + 2 * d + w, v + d, w, h),
    }


def build(model, texture=None, offset=(0, 0, 0)):
    """Строит модель в текущей сцене; offset — сдвиг в блоках."""
    _KIND[0], model = ("block", model[6:]) if model.startswith("block:") else ("entity", model)
    with open(os.path.join(ASSETS, "geo", _KIND[0], model + ".geo.json"), encoding="utf-8") as f:
        geo = json.load(f)["minecraft:geometry"][0]
    tw, th = geo["description"]["texture_width"], geo["description"]["texture_height"]
    bones = {b["name"]: b for b in geo["bones"]}

    def world(name):
        b = bones[name]
        m = _rot(b.get("rotation"), b["pivot"])
        return world(b["parent"]) @ m if b.get("parent") else m

    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new()
    for b in geo["bones"]:
        mb = world(b["name"])
        for c in b.get("cubes", []):
            o, s, inf = Vector(c["origin"]), c["size"], c.get("inflate", 0)
            lo = o - Vector((inf, inf, inf))
            hi = o + Vector(s) + Vector((inf, inf, inf))
            mc = _rot(c.get("rotation"), c.get("pivot", [0, 0, 0])) if c.get("rotation") else Matrix.Identity(4)
            m = mb @ mc

            def P(x, y, z):
                p = m @ Vector((x, y, z))
                return bm.verts.new(((p.x + offset[0] * 16) / 16, (p.z + offset[1] * 16) / 16, (p.y + offset[2] * 16) / 16))

            x0, y0, z0 = lo
            x1, y1, z1 = hi
            # углы каждой грани: (левый-верх, правый-верх, правый-низ, левый-низ) как видит зритель снаружи
            quads = {
                "north": [(x1, y1, z0), (x0, y1, z0), (x0, y0, z0), (x1, y0, z0)],
                "south": [(x0, y1, z1), (x1, y1, z1), (x1, y0, z1), (x0, y0, z1)],
                "east": [(x0, y1, z1), (x0, y1, z0), (x0, y0, z0), (x0, y0, z1)],
                "west": [(x1, y1, z0), (x1, y1, z1), (x1, y0, z1), (x1, y0, z0)],
                "up": [(x1, y1, z1), (x0, y1, z1), (x0, y1, z0), (x1, y1, z0)],
                "down": [(x1, y0, z0), (x0, y0, z0), (x0, y0, z1), (x1, y0, z1)],
            }
            rects = _faces(c["uv"], s)
            for face, corners in quads.items():
                fx, fy, fw, fh = rects[face]
                if fw == 0 or fh == 0:
                    continue
                vs = [P(*p) for p in corners]
                try:
                    bf = bm.faces.new(vs)
                except ValueError:
                    continue
                uvs = [(fx, fy), (fx + fw, fy), (fx + fw, fy + fh), (fx, fy + fh)]
                for loop, (uu, vv) in zip(bf.loops, uvs):
                    loop[uvl].uv = (uu / tw, 1 - vv / th)
    me = bpy.data.meshes.new("WB_" + model)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(f"WB_{texture or model}", me)
    me.materials.append(_material(texture or model))
    bpy.context.scene.collection.objects.link(ob)
    return ob


def show(items, spacing=2.5):
    """items: имя модели или (модель, текстура). Ставит в ряд и возвращает имена объектов."""
    _scene()
    names = []
    for i, it in enumerate(items):
        model, tex = (it, None) if isinstance(it, str) else it
        names.append(build(model, tex, (i * spacing, 0, 0)).name)
    return names
