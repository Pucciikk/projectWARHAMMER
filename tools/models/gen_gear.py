#!/usr/bin/env python3
"""
3D-снаряжение Сезона 1 (GeckoLib, предметы и броня): лазган, цепной меч, флак-броня гвардейца, респиратор.

    python3 tools/models/gen_gear.py

Пишет geo/item/<имя>.geo.json, animations/item/<имя>.animation.json, textures/item/<имя>.png;
для оружия — models/item/<предмет>.json (builtin/entity с положениями в руках, на поясе и в инвентаре).
Броня — по шаблону брони GeckoLib: кости armorHead, armorBody, armorRightArm/LeftArm, armorRightLeg/LeftLeg,
armorRightBoot/LeftBoot; координаты как у модели игрока (голова y 24–32, тело 12–24, ноги 0–12).
Референсы брони — Pictures/AstraMilitarum (кадианский гвардеец): зелёные пластины, хаки, подсумки, череп на ремне.
"""
import json
import os
import sys
import zlib

sys.path.insert(0, os.path.dirname(__file__))
import hd  # noqa: E402
from geo import MATERIALS, Model, save_png, write_animations, write_json  # noqa: E402

PAL = dict(
    flak=(78, 100, 54), khaki=(150, 136, 98), fatigue=(118, 108, 76), leather=(78, 54, 34), dark=(36, 36, 40),
    metal=(110, 114, 122), steel=(168, 172, 180), hull=(74, 78, 86), brass=(190, 148, 58), gold=(214, 170, 66),
    wood=(98, 64, 36), bone=(214, 204, 176), glow=(110, 230, 140), lens=(232, 140, 40), screen=(20, 24, 22),
    rubber=(46, 46, 50), cable=(30, 30, 34), trim=(70, 90, 46), red=(130, 22, 24),
)
MATERIALS.update({
    "g_flak": hd.hd_metal("flak", rivets=False, panels=False, rust=0.0),
    "g_flak_riv": hd.hd_metal("flak", rivets=True, panels=False),
    "g_cloth": hd.hd_cloth("khaki", folds=True, dirty=True),
    "g_fatigue": hd.hd_cloth("fatigue", folds=True, dirty=True),
    "g_leather": hd.hd_leather("leather"),
    "g_dark": hd.hd_metal("dark", rivets=False, panels=False),
    "g_metal": hd.hd_metal("metal", rivets=True, panels=False),
    "g_steel": hd.hd_metal("steel", rivets=False, panels=False),
    "g_brass": hd.hd_brass("brass"),
    "g_gold": hd.hd_brass("gold"),
    "g_wood": hd.hd_wood("wood"),
    "g_bone": hd.hd_flat("bone", 4),
    "g_glow": hd.hd_flat("glow", 3, edge=False),
    "g_lens": hd.hd_flat("lens", 3, edge=False),
    "g_rubber": hd.hd_flat("rubber", 4),
    "g_red": hd.hd_flat("red", 4),
})


def finish(m, name, idle=None):
    print(name)
    m.build(kind="item")
    base, _ = m.paint(PAL, seed=zlib.crc32(name.encode()))
    save_png(base, "item", f"{name}.png")
    write_animations(name, {"misc.idle": {"length": 1.0, "loop": True, "bones": idle or {}}}, kind="item")


def item_json(item, display):
    write_json({"parent": "builtin/entity", "display": display, "textures": {"particle": f"warpbound:item/{item}"}},
               "models", "item", f"{item}.json")


# ------------------------------------------------------------------ лазган (кадианский образец), ствол к −Z

def lasgun():
    m = Model("lasgun_3d", S=4, atlas_w=128)
    g = m.bone("gun", [0, 0, 0])
    # приклад и затыльник
    g.cube([-1.4, 2.5, 5], [2.8, 3.6, 8], "g_wood")
    g.cube([-1.5, 1.6, 12.4], [3, 5, 1.2], "g_dark")
    g.cube([-1.2, 1.8, 7], [2.4, 1.2, 5], "g_wood")
    # ствольная коробка, пистолетная рукоять, спусковая скоба
    g.cube([-1.7, 3.6, -6], [3.4, 4.2, 11.5], "g_dark")
    g.cube([-1.75, 6.8, -6], [3.5, 0.6, 11.5], "g_metal")
    g.cube([-1.2, -0.6, 2.2], [2.4, 4.4, 2.4], "g_wood", rotation=[-18, 0, 0], pivot=[0, 3.6, 3.4])
    g.cube([-0.3, 1.6, -0.2], [0.6, 2, 2.4], "g_dark")
    # лазпакет перед рукоятью: корпус, зелёная шкала заряда
    g.cube([-1.5, 0.6, -4.2], [3, 3.2, 3.6], "g_metal")
    g.cube([-1.55, 1.4, -3.6], [0.1, 1.4, 2.4], "g_glow")
    g.cube([1.45, 1.4, -3.6], [0.1, 1.4, 2.4], "g_glow")
    # цевьё и кожух ствола с прорезями, латунные кольца, дульный срез с линзой
    g.cube([-1.6, 3.8, -12.5], [3.2, 3, 6.6], "g_wood")
    g.cube([-1.25, 5, -21], [2.5, 2.5, 9], "g_steel")
    for z in (-19.5, -17.5, -15.5):
        g.cube([-1.3, 5.6, z], [2.6, 1.2, 0.8], "g_dark")
    for z in (-12.6, -20.4):
        g.cube([-1.4, 4.9, z], [2.8, 2.7, 0.6], "g_brass")
    g.cube([-1, 5.25, -23], [2, 2, 2], "g_dark")
    g.cube([-0.55, 5.7, -23.05], [1.1, 1.1, 0.1], "g_lens")
    # планка и прицелы
    g.cube([-0.6, 7.8, -9], [1.2, 0.6, 10], "g_dark")
    g.cube([-0.5, 8.4, -10], [1, 1.2, 0.8], "g_dark")
    g.cube([-0.8, 8.4, 0], [1.6, 1.4, 1], "g_dark")
    # штык-нож под стволом
    g.cube([-0.25, 3.6, -26], [0.5, 1.3, 7], "g_steel")
    g.cube([-0.4, 3.4, -19.4], [0.8, 1.7, 1], "g_dark")
    finish(m, "lasgun_3d")
    item_json("lasgun", {
        "thirdperson_righthand": {"rotation": [0, 180, 0], "translation": [0, 3, 1], "scale": [0.45, 0.45, 0.45]},
        "thirdperson_lefthand": {"rotation": [0, 180, 0], "translation": [0, 3, 1], "scale": [0.45, 0.45, 0.45]},
        "firstperson_righthand": {"rotation": [0, 177, 0], "translation": [-2, 1, 1], "scale": [0.35, 0.35, 0.35]},
        "firstperson_lefthand": {"rotation": [0, 183, 0], "translation": [-2, 1, 1], "scale": [0.35, 0.35, 0.35]},
        "gui": {"rotation": [20, 115, 0], "translation": [1.5, -1, 0], "scale": [0.42, 0.42, 0.42]},
        "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.35, 0.35, 0.35]},
        "fixed": {"rotation": [0, 90, 0], "translation": [0, 0, 0], "scale": [0.5, 0.5, 0.5]},
        "head": {"rotation": [0, 180, 0], "translation": [0, 6, 0], "scale": [0.6, 0.6, 0.6]},
    })


# ------------------------------------------------------------------ цепной меч, клинок вверх (+Y), зубья к −Z

def chainsword():
    m = Model("chainsword_3d", S=4, atlas_w=128)
    s = m.bone("sword", [0, 0, 0])
    # рукоять с обмоткой и навершием
    s.cube([-1, 0, -1], [2, 6, 2], "g_leather")
    for y in (1, 2.5, 4):
        s.cube([-1.1, y, -1.1], [2.2, 0.5, 2.2], "g_dark")
    s.cube([-1.3, -1, -1.3], [2.6, 1, 2.6], "g_brass")
    # латунная гарда-аквила
    s.cube([-1.3, 6, -4], [2.6, 1.4, 8], "g_brass")
    s.cube([-1, 6.3, -5], [2, 0.8, 1], "g_gold")
    s.cube([-1, 6.3, 4], [2, 0.8, 1], "g_gold")
    # корпус мотора с выхлопом
    s.cube([-1.6, 7.4, -3.2], [3.2, 4.4, 6.4], "g_metal")
    s.cube([-1.7, 8.2, 1.6], [3.4, 2.6, 1.4], "g_dark")
    s.cube([-0.5, 10.6, 2.6], [1, 1.6, 1], "g_dark")
    # кожух клинка: тёмный металл, стальная полоса-дол, красная полоса печати
    s.cube([-0.9, 11.8, -2.4], [1.8, 22, 4.4], "g_metal")
    s.cube([-1.0, 13, -1.2], [2.0, 19.5, 1.6], "g_steel")
    s.cube([-1.05, 14, 1.2], [2.1, 6, 0.6], "g_red" if "g_red" in MATERIALS else "g_brass")
    s.cube([-1, 11.8, 1.6], [2, 22, 0.6], "g_dark")
    s.cube([-0.9, 33.8, -2.4], [1.8, 1.2, 4], "g_metal")
    # цепь: пилообразные зубья по кромке и вокруг острия, тёмные и светлые через один
    for i in range(23):
        s.cube([-0.45, 12 + i, -3.4], [0.9, 1.1, 1.1], "g_dark" if i % 2 else "g_steel",
               rotation=[45, 0, 0], pivot=[0, 12.5 + i, -2.85])
    for i in range(4):
        s.cube([-0.45, 34.6, -2.4 + i * 1.1], [0.9, 1.1, 1.1], "g_steel" if i % 2 else "g_dark",
               rotation=[45, 0, 0], pivot=[0, 35.1, -1.85 + i * 1.1])
    finish(m, "chainsword_3d")
    # клинок модели уже лежит как ванильный меч после своих поворотов (вверх по Y, плоскость YZ),
    # поэтому поворотов почти нет: в третьем лице клинок вперёд из кулака, в первом — наклон к экрану
    item_json("chainsword", {
        "thirdperson_righthand": {"rotation": [90, 0, 0], "translation": [0, 3, 0.5], "scale": [0.5, 0.5, 0.5]},
        "thirdperson_lefthand": {"rotation": [90, 0, 0], "translation": [0, 3, 0.5], "scale": [0.5, 0.5, 0.5]},
        "firstperson_righthand": {"rotation": [10, 0, -15], "translation": [1.5, 5, 0], "scale": [0.32, 0.32, 0.32]},
        "firstperson_lefthand": {"rotation": [10, 0, 15], "translation": [1.5, 5, 0], "scale": [0.32, 0.32, 0.32]},
        "gui": {"rotation": [0, 90, -45], "translation": [-1, -1, 0], "scale": [0.42, 0.42, 0.42]},
        "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.35, 0.35, 0.35]},
        "fixed": {"rotation": [0, 90, 0], "translation": [0, -2, 0], "scale": [0.5, 0.5, 0.5]},
    })


# ------------------------------------------------------------------ флак-броня кадианского гвардейца

def armor_bones(m):
    return {
        "head": m.bone("armorHead", [0, 24, 0]),
        "body": m.bone("armorBody", [0, 24, 0]),
        "rarm": m.bone("armorRightArm", [-5, 22, 0]),
        "larm": m.bone("armorLeftArm", [5, 22, 0]),
        "rleg": m.bone("armorRightLeg", [-1.9, 12, 0]),
        "lleg": m.bone("armorLeftLeg", [1.9, 12, 0]),
        "rboot": m.bone("armorRightBoot", [-1.9, 12, 0]),
        "lboot": m.bone("armorLeftBoot", [1.9, 12, 0]),
    }


def flak_armor():
    m = Model("flak_armor", S=4, atlas_w=128)
    b = armor_bones(m)
    h = b["head"]
    # шлем: купол, кромка, наушники; лицо открыто
    h.cube([-4.7, 30.4, -4.7], [9.4, 2.2, 9.4], "g_flak")
    h.cube([-4, 32.6, -4], [8, 0.7, 8], "g_flak")
    h.cube([-5, 29.6, -5], [10, 0.8, 10], "g_flak_riv")
    h.cube([-4.7, 25.6, 3.9], [9.4, 4, 0.8], "g_flak")
    for x in (-4.7, 3.9):
        h.cube([x, 25.6, -3], [0.8, 4, 7], "g_flak")
    h.cube([-1.6, 30.7, -5.05], [3.2, 1.3, 0.3], "g_gold")             # аквила на лбу
    h.cube([-4.6, 29.9, -5.2], [9.2, 0.6, 0.3], "g_leather")           # ремень очков
    for x in (-3.4, 0.6):
        h.cube([x, 29.7, -5.4], [2.8, 1.5, 0.6], "g_lens")             # очки на козырьке
    h.cube([4.5, 26.6, -1.2], [0.7, 2.2, 2.4], "g_dark")               # вокс у уха
    for x in (-4.4, 4.1):
        h.cube([x, 24.2, -3.5], [0.3, 4.4, 0.3], "g_leather")          # подбородочный ремень
    # тело: гимнастёрка, нагрудник из двух пластин, живот, спина, шарф, лямки, ремень с черепом, подсумки
    t = b["body"]
    t.cube([-4.25, 12, -2.25], [8.5, 12, 4.5], "g_fatigue")
    for x in (-4.5, 0.2):
        t.cube([x, 17.4, -3], [4.3, 6, 1], "g_flak_riv")
    t.cube([-3.6, 14.4, -2.85], [7.2, 2.8, 0.7], "g_flak")
    t.cube([-4.5, 14.8, 2.2], [9, 8.6, 1], "g_flak")
    t.cube([-3.2, 23, -2.7], [6.4, 1.2, 5.4], "g_cloth")
    for x in (-3.3, 2.5):
        t.cube([x, 14.5, -3.15], [0.8, 9.4, 0.3], "g_leather")
    t.cube([-4.5, 12, -2.6], [9, 1.5, 5.2], "g_leather")
    t.cube([-0.9, 12.1, -2.95], [1.8, 1.3, 0.4], "g_bone")
    for x in (-4, 2.1):
        t.cube([x, 10.8, -3.2], [1.9, 2.2, 1.1], "g_leather")
    t.cube([2.6, 11, 2.4], [1.8, 2.6, 1.4], "g_cloth")                 # фляга сзади
    # руки: рукава, большие наплечники, налокотники, перчатки
    for key, sx in (("rarm", -1), ("larm", 1)):
        a = b[key]
        x0 = -8.25 if sx < 0 else 3.75
        a.cube([x0, 12, -2.25], [4.5, 12, 4.5], "g_fatigue")
        px = -9 if sx < 0 else 3.6
        a.cube([px, 20.4, -2.9], [5.4, 3.8, 5.8], "g_flak")
        a.cube([px + 0.4, 23.6, -2.5], [4.6, 1.2, 5], "g_flak_riv")
        a.cube([px + 0.2, 19.6, -2.7], [5, 0.8, 5.4], "g_trim" if "g_trim" in MATERIALS else "g_flak")
        a.cube([x0 + (3.9 if sx > 0 else -0.45), 15.4, -1.6], [0.8, 2.6, 3.2], "g_flak")
        a.cube([x0 - 0.1, 12, -2.35], [4.7, 1.4, 4.7], "g_rubber")
    # ноги: штаны, набедренники, наколенники
    for key, sx in (("rleg", -1), ("lleg", 1)):
        l = b[key]
        x0 = -4.15 if sx < 0 else -0.35
        l.cube([x0, 2, -2.25], [4.5, 10, 4.5], "g_fatigue")
        l.cube([x0 + 0.3, 7.6, -2.75], [3.9, 3.4, 0.7], "g_flak")
        l.cube([x0 + 0.5, 4.6, -2.9], [3.5, 2.2, 1], "g_flak_riv")
        l.cube([x0 + (3.9 if sx > 0 else -0.6), 8, -1.2], [1.2, 2.4, 2.4], "g_leather")   # набедренный подсумок
    # ботинки и щитки голеней
    for key, sx in (("rboot", -1), ("lboot", 1)):
        f = b[key]
        x0 = -4.2 if sx < 0 else -0.4
        f.cube([x0, 0, -2.6], [4.6, 2.4, 5], "g_leather")
        f.cube([x0 + 0.1, 0, -2.8], [4.4, 0.6, 5.3], "g_rubber")
        f.cube([x0 + 0.3, 2.2, -2.8], [4, 2.2, 0.8], "g_flak")
    finish(m, "flak_armor")


def respirator():
    m = Model("respirator_mask", S=4, atlas_w=64)
    b = armor_bones(m)
    h = b["head"]
    # маска на нижнюю половину лица, решётка, два фильтра по бокам, шланг, ремни
    h.cube([-3.2, 24.6, -4.9], [6.4, 3.6, 1], "g_rubber")
    h.cube([-2.2, 24.2, -5.4], [4.4, 2.6, 0.6], "g_dark")
    for x in (-1.6, -0.4, 0.8):
        h.cube([x, 24.6, -5.5], [0.6, 1.8, 0.2], "g_steel")
    for x in (-4.6, 3.0):
        h.cube([x, 24.4, -5.6], [1.6, 2.2, 2.2], "g_flak")
        h.cube([x + 0.2, 24.6, -5.8], [1.2, 1.8, 0.3], "g_dark")
    h.cube([-4.4, 27.6, -4.6], [8.8, 0.5, 9.2], "g_leather")
    h.cube([-0.6, 22.2, -4.6], [1.2, 2.2, 1.2], "g_rubber")
    finish(m, "respirator_mask")


if __name__ == "__main__":
    lasgun()
    chainsword()
    flak_armor()
    respirator()
