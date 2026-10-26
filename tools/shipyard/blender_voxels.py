"""
Просмотр блочных построек (корабль на верфи) в Blender: JSON [[x, y, z, "id блока"], ...] → меш из видимых граней.

В Blender (MCP или Scripting):
    VOXELS = r"<путь к json>"
    exec(open(r"<проект>/tools/shipyard/blender_voxels.py", encoding="utf-8").read())
Цвета — приблизительные цвета блоков; Minecraft Y (вверх) идёт в Blender Z.
"""
import json

import bmesh
import bpy

COL = {"hull_plating": (0.32, 0.34, 0.39), "polished_deepslate": (0.22, 0.22, 0.24), "deepslate_tiles": (0.2, 0.2, 0.22),
       "polished_blackstone_bricks": (0.17, 0.15, 0.17), "chiseled_polished_blackstone": (0.2, 0.18, 0.2),
       "polished_blackstone_wall": (0.17, 0.15, 0.17), "plasteel_panel": (0.75, 0.76, 0.78),
       "riveted_plasteel_panel": (0.7, 0.71, 0.73), "brass_trim": (0.75, 0.58, 0.24), "gold_block": (0.95, 0.8, 0.25),
       "red_nether_bricks": (0.4, 0.05, 0.06), "ochre_froglight": (1, 0.85, 0.5), "orange_stained_glass": (1, 0.55, 0.15),
       "waxed_weathered_cut_copper": (0.4, 0.6, 0.5), "waxed_oxidized_copper": (0.3, 0.65, 0.55), "iron_block": (0.8, 0.8, 0.82),
       "polished_basalt": (0.3, 0.3, 0.32), "dock_girder": (0.25, 0.25, 0.28), "plasteel_vent": (0.4, 0.42, 0.45),
       "deck_grating": (0.38, 0.4, 0.42), "shroomlight": (1, 0.6, 0.3), "magma_block": (0.9, 0.35, 0.1),
       "soul_lantern": (0.3, 0.8, 1), "iron_bars": (0.5, 0.5, 0.5), "lightning_rod": (0.8, 0.5, 0.3), "end_rod": (1, 1, 0.9),
       "chain": (0.3, 0.3, 0.35), "blackstone": (0.1, 0.09, 0.1), "amethyst_block": (0.6, 0.4, 0.9), "sea_lantern": (0.7, 0.9, 1),
       "hazard_panel": (0.7, 0.6, 0.1), "stone_bricks": (0.45, 0.45, 0.45), "smooth_stone": (0.6, 0.6, 0.6),
       "riveted_plasteel_panel": (0.7, 0.71, 0.73), "lead_block": (0.36, 0.38, 0.44), "gilded_blackstone": (0.35, 0.28, 0.12),
       "deepslate_bricks": (0.26, 0.26, 0.28), "tuff_bricks": (0.4, 0.42, 0.38), "red_concrete": (0.55, 0.1, 0.1),
       "red_wool": (0.6, 0.12, 0.12), "waxed_cut_copper": (0.75, 0.45, 0.3), "waxed_oxidized_cut_copper": (0.3, 0.65, 0.55),
       "waxed_copper_grate": (0.7, 0.42, 0.28), "dark_oak_planks": (0.25, 0.17, 0.1), "tinted_glass": (0.15, 0.12, 0.18),
       "candle": (0.9, 0.85, 0.6), "skeleton_skull": (0.85, 0.85, 0.8), "fixture_part": (0.3, 0.3, 0.3),
       "coolant_pipe": (0.36, 0.42, 0.4), "geller_conduit": (0.3, 0.55, 0.9), "lumen_wall": (1, 0.85, 0.6),
       "lumen_ceiling": (1, 0.85, 0.6), "emergency_lumen": (1, 0.2, 0.15), "radiation_sign": (0.85, 0.7, 0.1),
       "cogitator_bank": (0.2, 0.4, 0.25), "vox_grille": (0.2, 0.2, 0.22), "bulkhead_door": (0.6, 0.55, 0.2),
       "red_bed": (0.6, 0.1, 0.1), "barrel": (0.45, 0.32, 0.2), "minecart": (0.4, 0.4, 0.4), "ladder": (0.55, 0.4, 0.25),
       "rail": (0.5, 0.45, 0.4), "lectern": (0.5, 0.36, 0.22), "dark_oak_stairs": (0.25, 0.17, 0.1),
       "polished_blackstone_brick_stairs": (0.17, 0.15, 0.17), "polished_blackstone_brick_slab": (0.17, 0.15, 0.17),
       "deepslate_tile_stairs": (0.2, 0.2, 0.22), "red_wall_banner": (0.6, 0.1, 0.12), "command_throne": (0.6, 0.12, 0.1),
       "command_console": (0.2, 0.5, 0.3), "nav_table": (0.2, 0.4, 0.7), "auspex": (0.2, 0.5, 0.3),
       "reactor_core": (1, 0.6, 0.2), "geller_node": (0.3, 0.6, 1), "teleportarium_pad": (0.3, 0.8, 0.9)}
DIRS = [((1, 0, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]), ((-1, 0, 0), [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)]),
        ((0, 1, 0), [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)]), ((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]),
        ((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]), ((0, 0, -1), [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)])]


def build_voxels(path, name="WB_voxels"):
    data = json.load(open(path))
    occ = {(x, y, z) for x, y, z, b in data}
    sc = bpy.data.scenes.get("WB_Preview") or bpy.data.scenes.new("WB_Preview")
    bpy.context.window.scene = sc
    for o in list(sc.collection.objects):
        if o.name.startswith(name):
            bpy.data.objects.remove(o, do_unlink=True)
    bm = bmesh.new()
    col = bm.loops.layers.color.new("col")
    cache = {}

    def V(p):
        if p not in cache:
            cache[p] = bm.verts.new(p)
        return cache[p]

    for x, y, z, b in data:
        c = COL.get(b.split(":")[1].split("[")[0], (1, 0, 1))
        for (dx, dy, dz), corners in DIRS:
            if (x + dx, y + dy, z + dz) in occ:
                continue
            try:
                f = bm.faces.new([V((x + cx, z + cz, y + cy)) for cx, cy, cz in corners])
            except ValueError:
                continue
            for lp in f.loops:
                lp[col] = (*c, 1)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    mat = bpy.data.materials.get("WB_vox") or bpy.data.materials.new("WB_vox")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    vc = next((n for n in nt.nodes if n.type == "VERTEX_COLOR"), None) or nt.nodes.new("ShaderNodeVertexColor")
    vc.layer_name = "col"
    nt.links.new(vc.outputs[0], bsdf.inputs[0])
    me.materials.append(mat)
    return ob


build_voxels(VOXELS)  # noqa: F821 — задаётся перед exec
