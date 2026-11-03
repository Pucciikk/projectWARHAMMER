"""
Значки машин для инвентаря: настоящий рендер каждого меша в изометрии с прозрачным фоном.

В Blender: exec этого файла, затем run_icons("crusher", ...) или run_icons() для всех. Рисует в scratch-папку, в мод сохраняет
textures/item/machine_<блок>.png (32×32). Модели предметов пишет register_chain.py.
"""
import os
import traceback

import bpy
from mathutils import Vector

HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
OUT = r"C:/Users/Name/projectWARHAMMER/src/main/resources/assets/warpbound/textures/item"
SIZE = 128     # Pillow в Blender нет: большой кадр ужимает tools/textures/shrink_machine_icons.py
ICONS = {
    "crusher": "ore_crusher", "wash_vat": "wash_vat", "coke_oven": "coke_oven", "blast_furnace": "blast_furnace", "converter": "converter",
    "rolling_mill": "rolling_mill", "electrolyzer": "electrolyzer", "water_intake": "water_intake", "coal_gen": "coal_gen", "scriptorium": "scriptorium",
    "armoury": "armoury", "barrel_shop": "barrel_shop", "ammo_line": "ammo_line", "weavery": "weavery", "distiller": "distiller",
    "desulfurizer": "desulfurizer", "autoclave": "autoclave", "forge_smelter": "forge_smelter", "cogitatorium": "cogitatorium",
    "mechanicus_forge": "mechanicus_forge", "extractor": "promethium_extractor", "chem_reactor": "chem_reactor", "powder_works": "powder_works",
    "cement_mill": "cement_mill", "cracker": "cracker", "promethium_gen": "promethium_gen", "hydroponics": "hydroponics", "lumber": "lumber",
    "deep_drill": "deep_drill", "manual_press": "manual_press", "salvage_forge": "salvage_forge",
}


def _frame(scene, cam):
    """Камера смотрит сверху спереди; масштаб по реальным вершинам, поэтому машина занимает весь значок."""
    direction = Vector((-0.72, -1.0, 0.72)).normalized()
    cam.rotation_euler = (-direction).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()
    right = cam.matrix_world.to_3x3() @ Vector((1, 0, 0))
    up = cam.matrix_world.to_3x3() @ Vector((0, 1, 0))
    points = []
    deps = bpy.context.evaluated_depsgraph_get()
    for ob in scene.objects:
        if ob.type != "MESH":
            continue
        me = ob.evaluated_get(deps).to_mesh()
        m = ob.matrix_world
        points += [m @ v.co for v in me.vertices]
        ob.evaluated_get(deps).to_mesh_clear()
    us = [p.dot(right) for p in points]
    vs = [p.dot(up) for p in points]
    uc, vc = (min(us) + max(us)) / 2, (min(vs) + max(vs)) / 2
    center = sum(points, Vector((0, 0, 0))) / len(points)
    # сдвигаем центр в плоскости кадра к середине рамки
    center += right * (uc - center.dot(right)) + up * (vc - center.dot(up))
    cam.location = center + direction * 60
    cam.data.ortho_scale = max(max(us) - min(us), max(vs) - min(vs)) * 1.03


def run_icons(*names):
    for script in names or ICONS:
        block = ICONS[script]
        try:
            ns = {}
            exec(open(os.path.join(HERE, script + ".py"), encoding="utf-8").read(), ns)
            scene = bpy.context.scene
            cam_data = bpy.data.cameras.get("WB_IconCam") or bpy.data.cameras.new("WB_IconCam")
            cam_data.type = "ORTHO"
            cam_data.clip_end = 200
            cam = bpy.data.objects.new("WB_IconCam", cam_data)
            scene.collection.objects.link(cam)
            scene.camera = cam
            scene.frame_set(1)
            _frame(scene, cam)
            r = scene.render
            try:
                r.engine = "BLENDER_EEVEE"
            except TypeError:
                r.engine = "BLENDER_EEVEE_NEXT"
            r.resolution_x = r.resolution_y = SIZE
            r.resolution_percentage = 100
            r.film_transparent = True
            r.image_settings.file_format = "PNG"
            r.image_settings.color_mode = "RGBA"
            scene.view_settings.view_transform = "Standard"
            scene.view_settings.exposure = 0.6      # значок мелкий: без этого тёмный корпус сливается в пятно
            r.filepath = os.path.join(OUT, "machine_" + block + ".png")
            bpy.ops.render.render(write_still=True)
            print(block, "готов")
            bpy.data.objects.remove(cam, do_unlink=True)
        except Exception:
            print(script, "ОШИБКА\n" + traceback.format_exc())
