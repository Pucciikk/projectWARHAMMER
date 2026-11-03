"""
Экспорт машины из сцены Blender в мод: меш (geo.json с poly_mesh), запечённый атлас, карта свечения, анимации.

    machine_export("ore_crusher", bone_tracks, length_s, core_offset_y=1.0)

Blender: 1 м = 1 блок, перед в -Y. Модель: пиксели, x как в кубах Bedrock, y = высота, z = вглубь. Преобразование
(x, y, z) -> (x, z, y) × 16 вместе с минусом по x в GeckoLib — чистый поворот, зеркала нет и обход граней сохраняется.
core_offset_y: где середина блока-ядра по -Y (ядро в середине переднего ряда, поэтому 1.0 для машины шириной 3).
"""
import json
import math
import os

import bmesh
import bpy
import numpy as np

ASSETS = r"C:/Users/Name/projectWARHAMMER/src/main/resources/assets/warpbound"
BAKE_SIZE = [1024]    # размер атласа: у исполинских машин 2048
EXPOSURE = 1.5        # игра темнее рендера: нет бликов и света со всех сторон


def _gather(scene, skip=("WB_Key", "WB_Fill"), locators=()):
    """Все кости в одном меше в позе покоя; в слое граней — номер кости."""
    bones = [o for o in scene.objects if o.type == "MESH" and o.name not in skip]
    bm = bmesh.new()
    layer = bm.faces.layers.int.new("bone")
    for i, ob in enumerate(bones):
        pivot = ob["pivot"]
        tmp = bmesh.new()
        if ob.get("bone") not in locators:     # руки и точки: заглушка только для просмотра, в игру не идёт
            tmp.from_mesh(ob.data)
        vmap = {v: bm.verts.new((v.co.x + pivot[0], v.co.y + pivot[1], v.co.z + pivot[2])) for v in tmp.verts}
        for f in tmp.faces:
            nf = bm.faces.new([vmap[v] for v in f.verts])
            nf.material_index = f.material_index
            nf[layer] = i
        tmp.free()
    # выпуклые и вогнутые n-угольники режем: в игре только четырёхугольники и треугольники
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4], quad_method="BEAUTY", ngon_method="BEAUTY")
    # каждая грань в игре — 4 вершины, поэтому пара треугольников в одной плоскости должна стать одной гранью
    bmesh.ops.join_triangles(bm, faces=[f for f in bm.faces if len(f.verts) == 3], angle_face_threshold=math.radians(1),
                             angle_shape_threshold=math.radians(180), cmp_seam=False, cmp_sharp=False, cmp_uvs=False,
                             cmp_vcols=False, cmp_materials=True)
    return bones, bm


def _bake_atlas(scene, atlas, name):
    """Цвет, затенение по углам (AO) и свечение одним проходом Cycles по развёртке."""
    try:
        scene.render.engine = "CYCLES"
    except TypeError as e:
        raise RuntimeError(f"нужен Cycles: {e}")
    scene.cycles.device = "CPU"
    scene.cycles.samples = 16
    scene.cycles.use_denoising = False
    scene.render.bake.margin = 6
    scene.render.bake.use_clear = True
    bpy.context.view_layer.objects.active = atlas
    atlas.select_set(True)

    def image(kind):
        img = bpy.data.images.get(f"{name}_{kind}")
        if img:
            bpy.data.images.remove(img)
        return bpy.data.images.new(f"{name}_{kind}", BAKE_SIZE[0], BAKE_SIZE[0], alpha=True, float_buffer=True)

    def bake(kind, bake_type, **kw):
        img = image(kind)
        for mat in atlas.data.materials:
            nt = mat.node_tree
            node = nt.nodes.get("WB_Target") or nt.nodes.new("ShaderNodeTexImage")
            node.name = "WB_Target"
            node.image = img
            nt.nodes.active = node
        bpy.ops.object.bake(type=bake_type, **kw)
        px = np.zeros(BAKE_SIZE[0] * BAKE_SIZE[0] * 4, dtype=np.float32)
        img.pixels.foreach_get(px)
        return px.reshape(BAKE_SIZE[0], BAKE_SIZE[0], 4)

    metals = {}
    for mat in atlas.data.materials:                      # цвет металла иначе запечётся чёрным
        p = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        metals[mat.name] = p.inputs["Metallic"].default_value
        p.inputs["Metallic"].default_value = 0
    color = bake("color", "DIFFUSE", pass_filter={"COLOR"})
    ao = bake("ao", "AO")
    emit = bake("emit", "EMIT")
    # кромки: фаска в шейдере отличается от настоящей нормали только у рёбер — это и есть маска потёртостей
    links = {}
    for mat in atlas.data.materials:
        nt = mat.node_tree
        out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        p = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        links[mat.name] = (nt, p, out)
        extra = []
        bevel = nt.nodes.new("ShaderNodeBevel")
        bevel.samples = 6
        bevel.inputs["Radius"].default_value = 0.02
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        dot = nt.nodes.new("ShaderNodeVectorMath")
        dot.operation = "DOT_PRODUCT"
        em = nt.nodes.new("ShaderNodeEmission")
        inv = nt.nodes.new("ShaderNodeMath")
        inv.operation = "SUBTRACT"
        inv.inputs[0].default_value = 1.0
        nt.links.new(bevel.outputs[0], dot.inputs[0])
        nt.links.new(geo.outputs["True Normal"], dot.inputs[1])
        nt.links.new(dot.outputs["Value"], inv.inputs[1])
        nt.links.new(inv.outputs[0], em.inputs["Color"])
        nt.links.new(em.outputs[0], out.inputs["Surface"])
        links[mat.name] += ((bevel, geo, dot, em, inv),)
    edge = bake("edge", "EMIT")
    for nt, p, out, nodes in links.values():
        for n in nodes:
            nt.nodes.remove(n)
        nt.links.new(p.outputs[0], out.inputs["Surface"])
    for mat in atlas.data.materials:
        next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Metallic"].default_value = metals[mat.name]
        n = mat.node_tree.nodes.get("WB_Target")
        if n:
            mat.node_tree.nodes.remove(n)
    return color, ao, emit, edge


def _to_srgb(linear):
    linear = np.clip(linear, 0, 1)
    return np.where(linear <= 0.0031308, linear * 12.92, 1.055 * np.power(linear, 1 / 2.4) - 0.055)


def _save(rgba, path):
    img = bpy.data.images.new("wb_save", BAKE_SIZE[0], BAKE_SIZE[0], alpha=True)
    img.pixels.foreach_set(rgba.astype(np.float32).ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def machine_export(name, tracks, length, core_offset_y=1.0, idle=None, size=1024, work_name="work.active", work_loop=True, folder="block", locators=()):
    """work_name и work_loop: ручной пресс бьёт одним ударом по триггеру (work.strike), а не крутит цикл."""
    BAKE_SIZE[0] = size
    scene = bpy.context.scene
    bones, bm = _gather(scene, locators=locators)
    work = bpy.data.scenes.get("WB_Bake") or bpy.data.scenes.new("WB_Bake")
    for o in list(work.collection.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    me = bpy.data.meshes.new(name + "_atlas")
    bm.to_mesh(me)
    bm.free()
    for m in bones[0].data.materials:
        me.materials.append(m)
    atlas = bpy.data.objects.new(name + "_atlas", me)
    work.collection.objects.link(atlas)
    window = bpy.context.window
    keep = window.scene
    window.scene = work
    bpy.context.view_layer.objects.active = atlas
    atlas.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(40), island_margin=0.006, scale_to_bounds=True)
    bpy.ops.object.mode_set(mode="OBJECT")

    color, ao, emit, edge = _bake_atlas(work, atlas, name)
    # в игре нет теней от модели: углы затемняем в самой текстуре
    shade = 0.32 + 0.68 * np.clip(ao[..., :1], 0, 1)
    mask = (emit[..., :3].max(axis=2) > 0.02).astype(np.float32)
    # свечение ложится на цвет сложением: под ним основа тёмная, иначе огонь уходит в жёлтый и белый
    wear = np.clip(edge[..., :1] * 7, 0, 1)
    lit = color[..., :3] * shade * EXPOSURE
    lit = lit * (1 + 1.3 * wear) + 0.025 * wear     # кромки стёрты до светлого металла: так форма читается без бликов
    rgb = _to_srgb(lit) * (1 - 0.8 * mask[..., None])
    base = np.dstack((rgb, np.ones(rgb.shape[:2])))
    # яркость делим по самому яркому каналу: оттенок сохраняется, а не срезается по единице
    peak = np.maximum(emit[..., :3].max(axis=2, keepdims=True), 1.0)
    glow_rgb = _to_srgb(emit[..., :3] / peak)
    glow = np.dstack((glow_rgb * mask[..., None], mask))
    tex = os.path.join(ASSETS, "textures", folder)
    _save(base, os.path.join(tex, name + ".png"))
    _save(glow, os.path.join(tex, name + "_glow.png"))

    # ---- меш по костям
    bm = bmesh.new()
    bm.from_mesh(me)
    uvl = bm.loops.layers.uv.active
    layer = bm.faces.layers.int.get("bone")
    out = []
    faces_total = 0
    glowing = {i for i, m in enumerate(me.materials) if any(
        n.type == "BSDF_PRINCIPLED" and n.inputs["Emission Strength"].default_value > 0 for n in m.node_tree.nodes)}
    for i, ob in enumerate(bones):
        pivot = ob["pivot"]
        positions, uvs, polys = [], [], []
        pos_idx, uv_idx = {}, {}
        for f in bm.faces:
            if f[layer] != i:
                continue
            poly = []
            for loop in f.loops:
                c = loop.vert.co
                # в пиксели, ядро стоит в начале координат
                key = (round(c.x * 16, 3), round(c.z * 16, 3), round((c.y + core_offset_y) * 16, 3))
                p = pos_idx.setdefault(key, len(pos_idx))
                if p == len(positions) // 3:
                    positions.extend(key)
                uv = loop[uvl].uv
                ukey = (round(uv.x, 5), round(1 - uv.y, 5))
                u = uv_idx.setdefault(ukey, len(uv_idx))
                if u == len(uvs) // 2:
                    uvs.extend(ukey)
                # второе число в тройке — не нормаль (её считает игра), а признак светящейся грани
                poly.append([p, 1 if f.material_index in glowing else 0, u])
            if len(poly) == 3:
                poly.append(poly[-1])
            polys.append(poly)
        faces_total += len(polys)
        entry = {"name": ob["bone"], "pivot": [round(pivot[0] * 16, 3), round(pivot[2] * 16, 3), round((pivot[1] + core_offset_y) * 16, 3)]}
        if polys:
            entry["poly_mesh"] = {"normalized_uvs": True, "positions": positions, "normals": [0, 1, 0], "uvs": uvs, "polys": polys}
        out.append(entry)
    bm.free()
    names = {b["name"] for b in out}
    for anim in [tracks, (idle or {}).get("bones", {})]:
        lost = set(anim) - names
        if lost:
            raise RuntimeError(f"{name}: дорожки без кости: {sorted(lost)}")
    geo = {"format_version": "1.12.0", "minecraft:geometry": [{
        "description": {"identifier": f"geometry.warpbound.{name}", "texture_width": size, "texture_height": size},
        "bones": out}]}
    os.makedirs(os.path.join(ASSETS, "geo", folder), exist_ok=True)
    os.makedirs(os.path.join(ASSETS, "animations", folder), exist_ok=True)
    with open(os.path.join(ASSETS, "geo", folder, name + ".geo.json"), "w", encoding="utf-8") as f:
        json.dump(geo, f, separators=(",", ":"))

    anims = {"misc.idle": idle or {"loop": True, "animation_length": 2.0, "bones": {}},
             work_name: {"loop": work_loop, "animation_length": length, "bones": tracks}}
    with open(os.path.join(ASSETS, "animations", folder, name + ".animation.json"), "w", encoding="utf-8") as f:
        json.dump({"format_version": "1.8.0", "animations": anims}, f, indent=1)
    window.scene = keep
    print(f"{name}: граней {faces_total}, костей {len(out)}")


FLAME_OFF = {"loop": True, "animation_length": 2.0, "bones": {"stack_flame": {"scale": {"0": [0, 0, 0]}}}}
