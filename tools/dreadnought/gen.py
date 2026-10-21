#!/usr/bin/env python3
"""
Генератор модели и текстуры дредноута (v2, по референсам автора).

Координаты в описании — пространство машины в 1/32 блока:
    R — вправо (с точки зрения самого дредноута), U — вверх от земли, F — вперёд.
Рендерер масштабирует модель в 0.5, поэтому на 1 блок приходится 32 текселя:
текстура вдвое детальнее обычной майнкрафтовской.

    python3 tools/dreadnought/gen.py          # пишет модель и текстуры в ресурсы
    python3 tools/dreadnought/gen.py --dev    # плюс копирует в build/, чтобы F3+T в запущенной игре подхватил

Результат:
    src/main/resources/assets/warpbound/models/entity/dreadnought.json
    src/main/resources/assets/warpbound/textures/entity/dreadnought.png
    src/main/resources/assets/warpbound/textures/entity/dreadnought_glow.png
"""
import json
import math
import os
import random
import shutil
import sys

import numpy as np
from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEX = 1024
rng = random.Random(40000)

# =============================================================== описание модели

PARTS = []  # (имя, родитель, точка вращения (R,U,F), поворот (рад), [кубы])


def part(name, parent, pivot, cubes, rot=(0, 0, 0)):
    PARTS.append([name, parent, pivot, rot, list(cubes)])


def box(a, b, mat, deco=None, rot=None, center=None):
    """Куб от угла a до угла b (R,U,F). rot — поворот вокруг center (градусы, оси R,U,F)."""
    lo = tuple(min(a[i], b[i]) for i in range(3))
    hi = tuple(max(a[i], b[i]) for i in range(3))
    return {"lo": lo, "hi": hi, "mat": mat, "deco": deco or {}, "rot": rot, "center": center}


def cyl(axis, c, apothem, start, end, mat, deco=None):
    """Восьмигранный цилиндр из трёх кубов: крест и квадрат по диагоналям.
    Повёрнутые на 45° квадраты дали бы звезду, а не восьмигранник."""
    i = "RUF".index(axis)
    o = [j for j in range(3) if j != i]
    narrow = max(1, round(apothem * 0.414))
    corner = max(1, round(apothem * 0.707))
    out = []
    for h0, h1 in ((apothem, narrow), (narrow, apothem), (corner, corner)):
        a = [0, 0, 0]
        b = [0, 0, 0]
        a[i], b[i] = start, end
        a[o[0]], b[o[0]] = c[0] - h0, c[0] + h0
        a[o[1]], b[o[1]] = c[1] - h1, c[1] + h1
        out.append(box(a, b, mat, deco))
    return out


def mirror(cubes):
    out = []
    for c in cubes:
        d = dict(c["deco"])
        if "right" in d or "left" in d:
            r, l = d.pop("right", None), d.pop("left", None)
            if l: d["right"] = l
            if r: d["left"] = r
        lo = (-c["hi"][0], c["lo"][1], c["lo"][2])
        hi = (-c["lo"][0], c["hi"][1], c["hi"][2])
        center = None if c["center"] is None else (-c["center"][0], c["center"][1], c["center"][2])
        rot = None if c["rot"] is None else (c["rot"][0], -c["rot"][1], -c["rot"][2])
        out.append({"lo": lo, "hi": hi, "mat": c["mat"], "deco": d, "rot": rot, "center": center})
    return out


def mp(p):
    return (-p[0], p[1], p[2])


def lift(cubes, du):
    out = []
    for c in cubes:
        c = dict(c)
        c["lo"] = (c["lo"][0], c["lo"][1] + du, c["lo"][2])
        c["hi"] = (c["hi"][0], c["hi"][1] + du, c["hi"][2])
        if c["center"] is not None:
            c["center"] = (c["center"][0], c["center"][1] + du, c["center"][2])
        out.append(c)
    return out


def up(p, du):
    return (p[0], p[1] + du, p[2])


def bolt(c, r, depth, axis="F"):
    """Выступающая головка болта: короткий восьмигранник на грани (по умолчанию лицом вперёд)."""
    i = "RUF".index(axis)
    o = [c[j] for j in range(3) if j != i]
    return cyl(axis, o, r, c[i], c[i] + depth, "steel", {})


def hose_arc(p0, p1, sag, r, n=3):
    """Гофрированный шланг из n отрезков по провисающей дуге от p0 к p1.
    Каждый отрезок — куб вдоль оси U, повёрнутый сперва вокруг R, потом вокруг F."""
    pts = []
    for k in range(n + 1):
        t = k / n
        p = [p0[j] + (p1[j] - p0[j]) * t for j in range(3)]
        p[1] -= sag * 4 * t * (1 - t)
        pts.append(p)
    out = []
    for a, b in zip(pts, pts[1:]):
        d = [b[j] - a[j] for j in range(3)]
        length = math.sqrt(sum(x * x for x in d))
        d = [x / length for x in d]
        # знак: ось куба смотрит «вниз» по U, если отрезок идёт вниз — разворачиваем
        if d[1] < 0:
            d = [-x for x in d]
        rx = math.degrees(math.asin(max(-1, min(1, d[2]))))
        rz = math.degrees(math.atan2(-d[0], d[1]))
        c = [(a[j] + b[j]) / 2 for j in range(3)]
        half = length / 2 + r * 0.5
        out.append(box((round(c[0] - r), round(c[1] - half), round(c[2] - r)),
                       (round(c[0] + r), round(c[1] + half), round(c[2] + r)),
                       "hose", {}, rot=(rx, 0, rz), center=tuple(c)))
    return out


def skull3d(c, s=1.0, axis="F", mat="bone"):
    """Объёмный череп: черепная коробка с глазницами и челюсть, утопленная назад.
    c — центр низа челюсти на грани; axis — куда смотрит лицо (F вперёд, R вправо, -R влево)."""
    w, h = max(4, round(8 * s)), max(3, round(7 * s))
    jw, jh = max(3, round(6 * s)), max(2, round(3 * s))
    dep, jdep = max(2, round(4 * s)), max(1, round(3 * s))
    parts = [  # (поперёк, вверх, наружу) от центра
        ((-w / 2, jh - 1, 0), (w / 2, jh - 1 + h, dep), "skull_face"),
        ((-jw / 2, 0, 0), (jw / 2, jh, jdep), "skull_jaw"),
        ((-w / 2 + 1, jh - 1 + h, 0), (w / 2 - 1, jh + h, dep - 1), None),     # свод черепа
    ]
    out = []
    for lo, hi, deco in parts:
        lo = tuple(round(v) for v in lo)
        hi = tuple(round(v) for v in hi)
        if axis == "F":
            a = (c[0] + lo[0], c[1] + lo[1], c[2] + lo[2])
            b = (c[0] + hi[0], c[1] + hi[1], c[2] + hi[2])
            face = "front"
        elif axis == "R":
            a = (c[0] + lo[2], c[1] + lo[1], c[2] - hi[0])
            b = (c[0] + hi[2], c[1] + hi[1], c[2] - lo[0])
            face = "right"
        elif axis == "-F":
            a = (c[0] - hi[0], c[1] + lo[1], c[2] - hi[2])
            b = (c[0] - lo[0], c[1] + hi[1], c[2] - lo[2])
            face = "back"
        else:  # "-R"
            a = (c[0] - hi[2], c[1] + lo[1], c[2] + lo[0])
            b = (c[0] - lo[2], c[1] + hi[1], c[2] + hi[0])
            face = "left"
        out.append(box(a, b, mat, {face: deco} if deco else {}))
    return out


# Всё выше ног поднято на LIFT: ноги v3 длиннее (бедро на 56, а не на 46), как на референсах 3ddd
LIFT = 10
HIP, KNEE, ANKLE = (24, 56, 0), (24, 34, 1), (24, 10, 1)

# ---------- ноги (правая; левая — зеркало)
LEG = [
    # огромный приводной барабан бедра
    *cyl("R", (56, 0), 13, 9, 36, "iron", {"right": "drum_end", "front": "drum", "back": "drum", "top": "drum"}),
    *cyl("R", (56, 0), 9, 36, 39, "steel", {"right": "drum_end"}),
    *bolt((39, 56, 0), 4, 3, axis="R"),                                                  # ступица
    # выпуклые стальные обручи на барабане: рельеф, как на референсе
    *[c for r0 in (12, 19, 26, 33) for c in cyl("R", (56, 0), 14, r0, r0 + 2, "steel", {})],
    box((17, 34, -7), (31, 50, 7), "iron", {"front": "piston", "back": "piston"}),       # бедренная тяга
    box((31, 36, -2), (34, 52, 2), "steel", {"right": "piston"}),                         # гидравлика снаружи
    box((14, 38, -3), (17, 50, 1), "hose", {}),                                           # шланг внутри
]
SHIN = [
    *cyl("R", (34, 1), 8, 15, 33, "steel", {"right": "drum_end", "left": "drum_end"}),   # колено
    box((18, 10, -6), (30, 32, 6), "iron", {"back": "piston"}),
    # большой гнутый щиток голени: лоб, верхняя кромка с наклоном назад, боковины
    box((12, 12, 6), (36, 34, 12), "blue", {"front": "knee"}),
    box((13, 32, 1), (35, 36, 10), "blue_edge", {"top": "plate"}, rot=(-20, 0, 0), center=(24, 34, 6)),
    box((11, 14, -5), (14, 32, 9), "blue", {"right": "plate"}),
    box((34, 14, -5), (37, 32, 9), "blue", {"left": "plate"}),
    box((19, 12, -10), (23, 30, -6), "steel", {"back": "piston"}),                       # задние поршни
    box((25, 12, -10), (29, 30, -6), "steel", {"back": "piston"}),
    # белый щит на колене и тёмный череп с красными глазами поверх
    *cyl("F", (24, 23), 6, 12, 13, "ivory", {}),
    *skull3d((24, 19, 13), 0.75, mat="iron"),
    box((14, 31, 11), (17, 34, 13), "steel", {}), box((31, 31, 11), (34, 34, 13), "steel", {}),
    box((14, 13, 11), (17, 16, 13), "steel", {}), box((31, 13, 11), (34, 16, 13), "steel", {}),
    # шланг от колена к голеностопу сзади
    *hose_arc((20, 30, -8), (20, 12, -9), -3, 2, 2),
]
FOOT = [
    box((16, 4, -8), (32, 13, 9), "iron", {"front": "ribs"}),                             # голеностоп
    box((9, 0, -14), (39, 5, 14), "iron", {}),
    box((9, 0, 12), (22, 9, 28), "blue", {"front": "toe", "top": "toe_top"}),
    box((26, 0, 12), (39, 9, 28), "blue", {"front": "toe", "top": "toe_top"}),
    box((10, 0, 27), (21, 6, 32), "blue_edge", {}, rot=(-25, 0, 0), center=(15.5, 3, 29.5)),
    box((27, 0, 27), (38, 6, 32), "blue_edge", {}, rot=(-25, 0, 0), center=(32.5, 3, 29.5)),
    box((16, 0, -25), (32, 8, -12), "blue", {"back": "toe", "top": "toe_top"}),
    box((5, 0, -6), (9, 7, 8), "blue", {}),                                               # боковые упоры
    box((39, 0, -6), (43, 7, 8), "blue", {}),
]
# ---------- таз: центральный блок между барабанами бёдер, как на референсе автора.
# Точка вращения на оси бёдер: таз качается и поворачивается под шагом, а «талия»
# (колокол и поясное кольцо) гасит это движение, чтобы саркофаг шёл ровно.
PELVIS = [
    box((-10, 44, -10), (10, 62, 10), "iron", {"right": "ribs", "left": "ribs", "back": "ribs"}),
    box((-8, 48, 10), (8, 62, 14), "iron", {"front": "grill"}),                 # решётка с отверстиями
    box((-7, 36, 11), (7, 48, 15), "blue_trim", {"front": "codpiece"}),          # щиток между ног
    box((-6, 26, 15), (-2, 40, 16), "seal", {"front": "seal"}),
    # скобы, которые держат барабаны сверху и снизу
    box((6, 60, -6), (13, 66, 6), "steel", {"top": "plate"}),
    box((-13, 60, -6), (-6, 66, 6), "steel", {"top": "plate"}),
    box((6, 44, -5), (12, 49, 5), "steel", {}),
    box((-12, 44, -5), (-6, 49, 5), "steel", {}),
    box((-14, 52, -4), (14, 60, 4), "steel", {}),                                # ось бёдер
    # крупные болты на решётке
    *bolt((-6, 60, 14), 2, 2), *bolt((6, 60, 14), 2, 2),
    *bolt((-6, 50, 14), 2, 2), *bolt((6, 50, 14), 2, 2),
    # гидроцилиндры от блока к барабанам: спереди и сзади
    *(PISTONS := [*cyl("R", (54, 7), 3, 8, 12, "iron", {}), *cyl("R", (54, 7), 2, 12, 15, "steel", {}),
                  *cyl("R", (50, -7), 3, 8, 12, "iron", {}), *cyl("R", (50, -7), 2, 12, 15, "steel", {})]),
    *mirror(PISTONS),
    # гофрированные шланги дугой от таза к барабанам
    *hose_arc((7, 63, 9), (11, 50, 11), 4, 2),
    *hose_arc((-7, 63, 9), (-11, 50, 11), 4, 2),
    *hose_arc((7, 63, -9), (11, 48, -10), 4, 2),
    *hose_arc((-7, 63, -9), (-11, 48, -10), 4, 2),
]
part("body", "root", (0, 56, 0), PELVIS)
# «Талия»: ребристый колокол и поясное кольцо под корпусом
part("waist", "body", (0, 64, 0), [
    *cyl("U", (0, 0), 7, 60, 64, "steel", {"front": "ribs", "back": "ribs", "right": "ribs", "left": "ribs"}),
    *cyl("U", (0, 0), 9, 64, 67, "iron", {"front": "ribs", "back": "ribs", "right": "ribs", "left": "ribs"}),
    *cyl("U", (0, 0), 12, 67, 70, "steel", {"front": "bolts", "back": "bolts", "right": "bolts", "left": "bolts"}),
    box((-18, 68, -14), (18, 73, 12), "iron", {"front": "ribs", "back": "ribs"}),   # поясное кольцо
    # шланги от кольца вниз к тазу
    *hose_arc((16, 67, 12), (9, 58, 9), 3, 2),
    *hose_arc((-16, 67, 12), (-9, 58, 9), 3, 2),
])
part("leg_r", "body", HIP, LEG)
part("shin_r", "leg_r", KNEE, SHIN)
part("foot_r", "shin_r", ANKLE, FOOT)
part("leg_l", "body", mp(HIP), mirror(LEG))
part("shin_l", "leg_l", mp(KNEE), mirror(SHIN))
part("foot_l", "shin_l", mp(ANKLE), mirror(FOOT))

# ---------- корпус
part("torso", "waist", (0, 60 + LIFT, 0), lift([
    # саркофаг — далеко выступает вперёд из корпуса, как нос корабля (по референсам сверху и сбоку)
    box((-14, 58, -6), (14, 114, 40), "blue", {"front": "sarcophagus", "right": "cables", "left": "cables", "top": "plate"}),
    box((-12, 114, -4), (12, 118, 36), "blue_edge", {}),
    # бронеблоки по бокам
    box((15, 60, -26), (42, 112, 22), "blue", {"front": "slab_r", "right": "slab_side", "top": "slab_top", "back": "plate"}),
    box((-42, 60, -26), (-15, 112, 22), "blue", {"front": "slab_l", "left": "slab_side", "top": "slab_top", "back": "plate"}),
    # скошенные верхние кромки бронеблоков
    box((16, 106, 13), (41, 109, 25), "blue_edge", {"top": "plate"}, rot=(45, 0, 0), center=(28, 109, 19)),
    box((-41, 106, 13), (-16, 109, 25), "blue_edge", {"top": "plate"}, rot=(45, 0, 0), center=(-28, 109, 19)),
    box((15, 54, -20), (38, 61, 16), "iron", {"front": "ribs"}),               # механика под блоками
    box((-38, 54, -20), (-15, 61, 16), "iron", {"front": "ribs"}),
    # кабели в щелях между саркофагом и блоками
    box((13, 62, 18), (16, 104, 27), "hose", {}),
    box((-16, 62, 18), (-13, 104, 27), "hose", {}),
    box((11, 50, 20), (15, 64, 24), "hose", {}, rot=(0, 0, -20), center=(13, 57, 22)),
    box((-15, 50, 20), (-11, 64, 24), "hose", {}, rot=(0, 0, 20), center=(-13, 57, 22)),
    # двигатель сзади
    box((-24, 64, -40), (24, 106, -26), "iron", {"back": "engine", "right": "vents", "left": "vents", "top": "ribs"}),
    box((-12, 72, -43), (12, 100, -40), "blue_trim", {"back": "back_grill"}),
    box((-22, 56, -38), (-18, 70, -34), "hose", {}),
    box((18, 56, -38), (22, 70, -34), "hose", {}),
    box((-24, 112, -26), (24, 116, 0), "iron", {"top": "deck"}),               # верхняя палуба
    box((-8, 116, -22), (-4, 120, -6), "steel", {}),                           # рёбра
    box((-2, 116, -22), (2, 120, -6), "steel", {}),
    box((4, 116, -22), (8, 120, -6), "steel", {}),
    # дымовые трубы
    *cyl("U", (13, -33), 5, 98, 132, "iron", {"front": "perforated", "back": "perforated", "right": "perforated", "left": "perforated", "top": "pipe_top"}),
    *cyl("U", (-13, -33), 5, 98, 132, "iron", {"front": "perforated", "back": "perforated", "right": "perforated", "left": "perforated", "top": "pipe_top"}),
    *cyl("U", (13, -33), 6, 96, 99, "steel", {}),
    *cyl("U", (-13, -33), 6, 96, 99, "steel", {}),
    # --- объёмные детали саркофага: козырёк над смотровой щелью, щёки, нижняя губа, череп
    box((-13, 110, 39), (13, 113, 45), "blue_edge", {"top": "plate"}),
    box((-14, 104, 40), (-11, 110, 43), "blue_edge", {}),
    box((11, 104, 40), (14, 110, 43), "blue_edge", {}),
    box((-11, 104, 40), (11, 106, 42), "blue_trim", {}),
    *skull3d((0, 85, 40), 1.0),
    box((-6, 82, 40), (6, 85, 43), "blue_trim", {}),                         # полочка под черепом
    *bolt((-11, 64, 40), 1, 1), *bolt((11, 64, 40), 1, 1),
    *bolt((-11, 100, 40), 1, 1), *bolt((11, 100, 40), 1, 1),
    # черепа на бронеблоках: спереди под лавровым венком и по бокам
    *skull3d((28, 89, 22), 1.0),
    *skull3d((42, 63, -2), 1.0, axis="R"),
    *skull3d((-42, 63, -2), 1.0, axis="-R"),
    *bolt((18, 108, 22), 1, 1), *bolt((39, 64, 22), 1, 1), *bolt((18, 64, 22), 1, 1),
    *bolt((-18, 108, 22), 1, 1), *bolt((-39, 64, 22), 1, 1), *bolt((-18, 64, 22), 1, 1),
    # шланги сзади: от двигателя к бронеблокам и вниз к поясу
    *hose_arc((24, 92, -34), (32, 74, -26), 5, 2),
    *hose_arc((-24, 92, -34), (-32, 74, -26), 5, 2),
    *hose_arc((20, 66, -36), (12, 56, -16), 4, 2),
    *hose_arc((-20, 66, -36), (-12, 56, -16), 4, 2),
    # череп под решёткой двигателя
    *skull3d((0, 64, -43), 1.0, axis="-F"),
], LIFT))
part("head", "torso", up((0, 116, 26), LIFT), lift([
    box((-6, 114, 22), (6, 122, 38), "iron", {"front": "sensor"}),
    box((-4, 116, 38), (4, 120, 40), "lens", {}),
    # козырёк над линзой, боковые датчики и антенна
    box((-7, 121, 32), (7, 123, 42), "steel", {"top": "plate"}),
    box((-7, 115, 38), (-4, 121, 41), "iron", {}),
    box((4, 115, 38), (7, 121, 41), "iron", {}),
    box((-9, 115, 26), (-6, 120, 36), "iron", {}), box((-9, 116, 36), (-7, 119, 37), "lens_blue", {}),
    box((6, 115, 26), (9, 120, 36), "iron", {}), box((7, 116, 36), (9, 119, 37), "lens_blue", {}),
    box((3, 122, 23), (5, 136, 25), "steel", {}),
    box((2, 132, 22), (6, 133, 26), "steel", {}),
], LIFT))

# ---------- правая рука: штурмовая пушка
part("arm_r", "torso", up((46, 86, 0), LIFT), lift([
    *cyl("R", (86, 0), 10, 41, 50, "iron", {"right": "drum_end"}),
    box((50, 62, -18), (66, 98, 18), "blue", {"right": "gun_side", "top": "slab_top", "front": "plate", "left": "plate"}),
    # лента патронов петлёй из короба вниз и обратно в руку, как на референсах
    box((60, 50, 2), (66, 64, 8), "belt_mat", {"right": "belt", "front": "belt", "left": "belt"}),
    box((60, 46, -12), (66, 52, 8), "belt_mat", {"right": "belt", "bottom": "belt"}),
    box((60, 50, -12), (66, 62, -6), "belt_mat", {"right": "belt", "back": "belt"}),
    *skull3d((66, 69, 0), 1.0, axis="R"),
    *hose_arc((52, 66, 14), (56, 74, 20), -3, 2, 2),                           # питание пушки
], LIFT))
GUN = [
    box((50, 70, 14), (66, 90, 32), "iron", {"front": "ribs", "right": "ribs"}),
    box((54, 76, 32), (62, 84, 70), "iron", {}),
    *cyl("F", (58, 80), 10, 36, 40, "steel", {}),
    *cyl("F", (58, 80), 10, 60, 64, "steel", {}),
    *cyl("F", (58, 80), 9, 70, 74, "iron", {"front": "muzzles"}),
]
for k in range(6):
    a = math.radians(30 + 60 * k)
    cx, cy = round(58 + 5.5 * math.cos(a)), round(80 + 5.5 * math.sin(a))
    GUN.append(box((cx - 2, cy - 2, 32), (cx + 2, cy + 2, 72), "barrel", {"front": "bore"}))
part("gun", "arm_r", up((58, 80, 8), LIFT), lift(GUN, LIFT))

# ---------- левая рука: силовой кулак
part("arm_l", "torso", up((-46, 84, 0), LIFT), lift([
    *cyl("R", (84, 0), 10, -50, -41, "iron", {"left": "drum_end"}),
    box((-64, 72, -16), (-50, 96, 10), "blue", {"left": "fist_shoulder", "top": "slab_top", "front": "plate"}),
    box((-52, 66, -10), (-48, 84, -6), "hose", {}),
    *skull3d((-64, 81, -3), 1.0, axis="-R"),
    *hose_arc((-50, 74, -12), (-54, 64, 2), 4, 2),
], LIFT))
part("fist", "arm_l", up((-58, 74, 6), LIFT), lift([
    *cyl("F", (-58, 72), 15, -12, 28, "blue", {"front": "plate", "top": "forearm", "left": "forearm", "right": "forearm", "bottom": "forearm"}),
    *cyl("F", (-58, 72), 12, 28, 34, "iron", {}),
    box((-70, 60, 33), (-46, 84, 41), "iron", {"front": "knuckles"}),
    # когти разведены веером
    box((-69, 77, 40), (-61, 84, 60), "claw", {"front": "claw_tip"}, rot=(-12, -8, 0), center=(-65, 80, 41)),
    box((-58, 77, 40), (-50, 84, 60), "claw", {"front": "claw_tip"}, rot=(-12, 8, 0), center=(-54, 80, 41)),
    box((-50, 64, 40), (-44, 76, 57), "claw", {"front": "claw_tip"}, rot=(0, 14, 0), center=(-47, 70, 41)),
    box((-63, 58, 40), (-54, 66, 56), "claw", {"front": "claw_tip"}, rot=(14, 0, 0), center=(-58, 62, 41)),
    box((-46, 62, 4), (-42, 82, 24), "lens_blue", {}),                          # катушка поля
], LIFT))

# Весь верх сдвинут вперёд относительно бёдер: ноги стоят под задней половиной корпуса
UPPER_FORWARD = 6
for p in PARTS:
    if p[0] in ("torso", "head", "arm_r", "gun", "arm_l", "fist"):
        p[2] = (p[2][0], p[2][1], p[2][2] + UPPER_FORWARD)
        for c in p[4]:
            c["lo"] = (c["lo"][0], c["lo"][1], c["lo"][2] + UPPER_FORWARD)
            c["hi"] = (c["hi"][0], c["hi"][1], c["hi"][2] + UPPER_FORWARD)
            if c["center"] is not None:
                c["center"] = (c["center"][0], c["center"][1], c["center"][2] + UPPER_FORWARD)

# =============================================================== развёртка

def faces(u, v, w, h, d):
    return {
        "top": (u + d, v, w, d),
        "bottom": (u + d + w, v, w, d),
        "right": (u, v + d, d, h),     # -x модели = правый борт машины
        "front": (u + d, v + d, w, h),
        "left": (u + d + w, v + d, d, h),
        "back": (u + d + w + d, v + d, w, h),
    }


class Packer:
    def __init__(self, size):
        self.size, self.x, self.y, self.row = size, 0, 0, 0

    def place(self, w, h):
        if self.x + w > self.size:
            self.x, self.y, self.row = 0, self.y + self.row, 0
        if self.y + h > self.size:
            raise SystemExit("развёртка не влезла в %d" % self.size)
        at = (self.x, self.y)
        self.x += w + 1
        self.row = max(self.row, h + 1)
        return at


# =============================================================== палитра и кисти

def hx(s):
    return np.array([int(s[i:i + 2], 16) for i in (1, 3, 5)], dtype=float)


MATS = {
    "blue": (hx("#4469b4"), hx("#7c9ee0"), hx("#22386e")),
    "blue_trim": (hx("#4469b4"), hx("#7c9ee0"), hx("#22386e")),
    "blue_edge": (hx("#4a70bd"), hx("#88a8e6"), hx("#2a4580")),
    "iron": (hx("#2c2e33"), hx("#5b606a"), hx("#151619")),
    "steel": (hx("#5a5f68"), hx("#a3a9b3"), hx("#2e3136")),
    "barrel": (hx("#3a3d43"), hx("#8d939c"), hx("#1b1c1f")),
    "claw": (hx("#34363b"), hx("#7d828b"), hx("#18191c")),
    "seal": (hx("#dccca2"), hx("#f1e6c6"), hx("#a8966c")),
    "lens": (hx("#d01e12"), hx("#ff7050"), hx("#700a06")),
    "lens_blue": (hx("#3a6fd0"), hx("#a8d8ff"), hx("#1a3170")),
    "cable_bundle": (hx("#2a2a2c"), hx("#555555"), hx("#111111")),
    "hose": (hx("#2b2a2d"), hx("#5d5a62"), hx("#121114")),
    "belt_mat": (hx("#8a6a2a"), hx("#e0c070"), hx("#4a3412")),
    "bone": (hx("#d8cfb4"), hx("#f4eedb"), hx("#8f8468")),
    "ivory": (hx("#e6e2d6"), hx("#fbf9f2"), hx("#a9a597")),
}
GOLD = (hx("#c9a24a"), hx("#f3d98a"), hx("#7b5a1c"))
BONE = hx("#e4dcc4")
WHITE = hx("#ebe8de")
WAX = hx("#9a1a12")
RUST = hx("#7a3e1c")
RED_LIGHT, GREEN_LIGHT, ORANGE_LIGHT = hx("#ff3a22"), hx("#4cff6a"), hx("#ffa23a")

tex = np.zeros((TEX, TEX, 4), dtype=float)
glow = np.zeros((TEX, TEX, 4), dtype=np.uint8)


def px(x, y, c, a=255):
    if 0 <= x < TEX and 0 <= y < TEX:
        tex[y, x, :3] = np.clip(c, 0, 255)
        tex[y, x, 3] = a


def blend(x, y, c, k):
    if 0 <= x < TEX and 0 <= y < TEX:
        tex[y, x, :3] = np.clip(tex[y, x, :3] * (1 - k) + np.asarray(c) * k, 0, 255)


def lit(x, y, c, strength=255):
    px(x, y, c)
    if 0 <= x < TEX and 0 <= y < TEX:
        glow[y, x] = (int(min(255, c[0])), int(min(255, c[1])), int(min(255, c[2])), strength)


def rect(r, x, y, w, h, c):
    for j in range(h):
        for i in range(w):
            px(r[0] + x + i, r[1] + y + j, c + rng.uniform(-5, 5))


def frame(r, x, y, w, h, mat, t=1):
    base, light, shadow = mat
    for k in range(t):
        for i in range(x + k, x + w - k):
            px(r[0] + i, r[1] + y + k, light if k == 0 else base)
            px(r[0] + i, r[1] + y + h - 1 - k, shadow if k == 0 else base * 0.9)
        for j in range(y + k, y + h - k):
            px(r[0] + x + k, r[1] + j, base * 1.05)
            px(r[0] + x + w - 1 - k, r[1] + j, base * 0.8)


def sprite(r, x, y, art, palette):
    for j, row in enumerate(art):
        for i, ch in enumerate(row):
            if ch in palette:
                c = palette[ch]
                if isinstance(c, tuple) and c[0] == "glow":
                    lit(r[0] + x + i, r[1] + y + j, c[1])
                else:
                    px(r[0] + x + i, r[1] + y + j, c + rng.uniform(-6, 6))


def rivet_row(r, x, y, w, step=4):
    for i in range(x, x + w, step):
        px(r[0] + i, r[1] + y, hx("#a8b0bc"))
        px(r[0] + i + 1, r[1] + y + 1, hx("#1c2a4c"))


def _smooth_noise(size, cell, seed):
    g = np.random.default_rng(seed).normal(0, 1, (size // cell + 2, size // cell + 2))
    img = Image.fromarray(((g - g.min()) / (g.max() - g.min()) * 255).astype(np.uint8))
    img = img.resize((size + 2 * cell, size + 2 * cell), Image.BICUBIC)
    return np.asarray(img, dtype=float)[cell:cell + size, cell:cell + size] / 255.0 - 0.5


# Крупные пятна (как ручная покраска) вместо попиксельного шума — приём из The Betweenlands
MOTTLE = _smooth_noise(TEX, 6, 7) * 0.7 + _smooth_noise(TEX, 2, 8) * 0.3
SHADOW_HUE = hx("#1c1640")   # тени уходят в фиолетово-синий, а не в чёрный
LIGHT_HUE = hx("#d8ecff")    # блики в холодный белый


def base_paint(r, mat, face, w, h):
    """Основа: пятнистая краска, сдвиг оттенка в тенях, затенение у нижней кромки,
    фаски, сколы, ржавые потёки."""
    base, light, shadow = MATS[mat]
    x0, y0 = r[0], r[1]
    tint = {"top": 1.1, "bottom": 0.62}.get(face, 1.0)
    painted = mat.startswith("blue")
    side = face not in ("top", "bottom")
    for y in range(h):
        t = y / max(1, h - 1)
        # затенение внизу граней (запечённая окклюзия) и лёгкий подсвет сверху
        ao = (0.55 * max(0.0, t - 0.65) / 0.35) ** 1.5 if side else 0.0
        top_light = 0.08 * max(0.0, 0.25 - t) / 0.25 if side else 0.0
        for x in range(w):
            m = MOTTLE[(y0 + y) % TEX, (x0 + x) % TEX]
            c = base * tint * (1.0 + 0.16 * m)
            c = c * (1 - ao) + SHADOW_HUE * ao
            c = c * (1 - top_light) + LIGHT_HUE * top_light
            if mat == "hose" and (y % 3 == 0 or (face in ("top", "bottom") and x % 3 == 0)):
                c = c * 0.55
            if mat == "belt_mat" and y % 4 < 2:
                c = hx("#c9a24a") * (1.0 + 0.2 * m) if y % 4 == 0 else hx("#6a4c18")
            px(x0 + x, y0 + y, c)
    if w >= 3 and h >= 3:
        for x in range(w):
            px(x0 + x, y0, light * tint)
            px(x0 + x, y0 + h - 1, shadow * 0.7 + SHADOW_HUE * 0.3)
        for y in range(h):
            blend(x0, y0 + y, light, 0.5)
            px(x0 + w - 1, y0 + y, shadow * 0.8 + SHADOW_HUE * 0.2)
    if painted and w * h > 60:
        # сколы по краям: сначала тёмная грунтовка, в середине — голый металл
        for _ in range(max(1, (w + h) // 9)):
            side = rng.randrange(4)
            t = rng.random()
            ex = int(t * (w - 1)) if side < 2 else (1 if side == 2 else w - 2)
            ey = int(t * (h - 1)) if side >= 2 else (1 if side == 0 else h - 2)
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    if rng.random() < 0.55:
                        blend(x0 + ex + dx, y0 + ey + dy, hx("#1d2433"), 0.7)
            px(x0 + ex, y0 + ey, hx("#9aa0a8"))
        # царапины в середине
        for _ in range(w * h // 420):
            sx, sy = rng.randrange(w), rng.randrange(h)
            for k in range(rng.randrange(2, 6)):
                blend(x0 + min(w - 1, sx + k), y0 + min(h - 1, sy + k // 2), light, 0.45)
        # ржавые потёки от верхнего края
        if face not in ("top", "bottom") and h > 12:
            for _ in range(max(1, w // 14)):
                sx = rng.randrange(1, max(2, w - 1))
                length = rng.randrange(h // 5, h // 2)
                for k in range(length):
                    blend(x0 + sx, y0 + 2 + k, RUST, 0.38 * (1 - k / length))
    if not painted and w * h > 20:
        for _ in range(w * h // 120):
            sx, sy = rng.randrange(w), rng.randrange(h)
            blend(x0 + sx, y0 + sy, light, 0.35)
        if face not in ("top", "bottom") and h > 10:
            for _ in range(max(1, w // 18)):
                sx = rng.randrange(w)
                length = rng.randrange(h // 4, h)
                for k in range(length):
                    blend(x0 + sx, y0 + k, RUST, 0.25 * (1 - k / length))
    if mat == "blue_trim" and w >= 6 and h >= 6:
        frame(r, 0, 0, w, h, GOLD, 1)


# ---------- пиксель-арт (собственные рисунки)
SKULL = [
    "..####..",
    ".######.",
    "########",
    "#..##..#",
    "#..##..#",
    "########",
    ".##..##.",
    "..####..",
    "..#.#.#.",
]
WINGS = [  # свой крылатый знак для саркофага, 24x9
    "##....................##",
    "###..................###",
    ".####..............####.",
    ".######..........######.",
    "..#######......#######..",
    "...#######....#######...",
    "....######....######....",
    ".....####......####.....",
    "......##........##......",
]
EMBLEM = [  # крылатый клинок — герб ордена (своя эмблема)
    ".......##.......",
    "......####......",
    "......####......",
    "#.....####.....#",
    "##....####....##",
    "###...####...###",
    ".###..####..###.",
    "..############..",
    "...##########...",
    ".....######.....",
    "......####......",
    "......####......",
    ".......##.......",
]
LAUREL = [
    "#..........#",
    "##........##",
    ".#........#.",
    ".##......##.",
    "..##....##..",
    "...######...",
]
NUM_IV = [
    "###.#...#",
    ".#..#...#",
    ".#..#...#",
    ".#...#.#.",
    ".#...#.#.",
    ".#....#..",
    "###...#..",
]


def skull(r, x, y, bone=BONE, eye=hx("#141414")):
    sprite(r, x, y, SKULL, {"#": bone})
    for (i, j) in ((1, 3), (2, 3), (1, 4), (2, 4), (5, 3), (6, 3), (5, 4), (6, 4)):
        px(r[0] + x + i, r[1] + y + j, eye)
    px(r[0] + x + 3, r[1] + y + 6, eye)
    px(r[0] + x + 4, r[1] + y + 6, eye)


def seal(r, x, y, w=5, h=12):
    rect(r, x + 1, y + 3, w - 2, h - 3, BONE)
    for j in range(5, h, 2):
        for i in range(1, w - 1):
            if rng.random() < 0.6:
                px(r[0] + x + i, r[1] + y + j, hx("#5e4c36"))
    for j in range(4):
        for i in range(w):
            if (i - w / 2 + 0.5) ** 2 + (j - 1.5) ** 2 < 5:
                px(r[0] + x + i, r[1] + y + j, WAX + rng.uniform(-12, 12))


def light(r, x, y, color, size=2):
    for j in range(size):
        for i in range(size):
            lit(r[0] + x + i, r[1] + y + j, color)
    px(r[0] + x - 1, r[1] + y - 1, hx("#16171a"))
    px(r[0] + x + size, r[1] + y + size, hx("#16171a"))


def slots(r, x, y, w, n, gap=3, glow_c=None):
    for k in range(n):
        for i in range(w):
            c = hx("#121316")
            if glow_c is not None:
                lit(r[0] + x + i, r[1] + y + k * gap, glow_c * (0.7 + 0.3 * rng.random()))
            else:
                px(r[0] + x + i, r[1] + y + k * gap, c)
                px(r[0] + x + i, r[1] + y + k * gap + 1, hx("#5a6070"))


def decorate(r, what, mat):
    x0, y0, w, h = r
    if what == "sarcophagus":
        frame(r, 0, 0, w, h, GOLD, 2)
        rect(r, 6, 4, w - 12, 3, hx("#1a1b1e"))                         # смотровая щель
        for i in range(7, w - 7):
            lit(x0 + i, y0 + 5, RED_LIGHT * 0.8, 200)
        frame(r, 4, 10, w - 8, h - 20, GOLD, 1)
        sprite(r, (w - 24) // 2, 14, WINGS, {"#": GOLD[1]})
        for j, row in enumerate(WINGS):
            for i, ch in enumerate(row):
                if ch == "#" and j > 4:
                    px(x0 + (w - 24) // 2 + i, y0 + 14 + j, GOLD[0])
        skull(r, (w - 8) // 2, 21)
        # свиток под знаком
        rect(r, 5, 33, w - 10, 6, BONE)
        for i in range(7, w - 7):
            if rng.random() < 0.65:
                px(x0 + i, y0 + 35 + rng.randrange(2), hx("#4a3a28"))
        rivet_row(r, 4, h - 6, w - 8, 4)
        seal(r, w - 9, h - 18, 5, 12)
    elif what == "slab_r":
        frame(r, 2, 2, w - 4, h - 4, MATS["blue"], 1)
        sprite(r, 6, 6, NUM_IV, {"#": WHITE})
        light(r, w - 7, 6, RED_LIGHT)
        sprite(r, 7, 17, LAUREL, {"#": GOLD[1]})
        skull(r, 9, 14, BONE)
        light(r, 6, 32, ORANGE_LIGHT, 3)
        seal(r, w - 9, 30, 5, 13)
        slots(r, 5, h - 10, w - 10, 3)
        rivet_row(r, 3, h - 3, w - 6, 4)
    elif what == "slab_l":
        frame(r, 2, 2, w - 4, h - 4, MATS["blue"], 1)
        sprite(r, (w - 16) // 2, 6, EMBLEM, {"#": WHITE})
        for k in range(3):                                                  # отметки отделения
            rect(r, 7 + k * 5, 23, 3, 8, WHITE * 0.92)
        light(r, 6, 36, RED_LIGHT)
        light(r, 11, 36, GREEN_LIGHT)
        rect(r, w - 12, 34, 8, 6, hx("#202226"))
        for i in range(w - 12, w - 4, 2):
            for j in range(34, 40, 2):
                px(x0 + i, y0 + j, hx("#55595f"))
        slots(r, 5, h - 10, w - 10, 3)
        rivet_row(r, 3, h - 3, w - 6, 4)
    elif what == "slab_side":
        slots(r, 6, 10, w - 12, 4)
        skull(r, w // 2 - 4, h - 22, BONE * 0.95)
        light(r, w - 8, 6, RED_LIGHT)
        rivet_row(r, 3, 3, w - 6, 5)
    elif what == "slab_top":
        for i in range(2, w - 2):
            px(x0 + i, y0 + h // 2, hx("#2a3f6e"))
        rivet_row(r, 2, 2, w - 4, 5)
    elif what == "plate":
        rivet_row(r, 2, 2, w - 4, 5)
        if h > 12:
            for i in range(2, w - 2):
                px(x0 + i, y0 + h // 2, MATS["blue"][2])
    elif what == "cables":
        for i in range(w):
            col = [hx("#a01810"), hx("#c8a020"), hx("#2a8a30"), hx("#1a1a1c")][(i // 2) % 4]
            for j in range(4, h - 4):
                px(x0 + i, y0 + j, col * (0.75 + 0.25 * math.sin(j * 0.7 + i)))
    elif what == "cable_bundle":
        pass
    elif what == "knee":
        for j in range(12):                                                 # белый круг с черепом
            for i in range(12):
                if (i - 5.5) ** 2 + (j - 5.5) ** 2 < 33:
                    px(x0 + (w - 12) // 2 + i, y0 + 5 + j, WHITE)
        skull(r, (w - 8) // 2, 7, hx("#1a1a1c"), WHITE)
        seal(r, w - 7, 3, 4, 10)
    elif what == "shin":
        rivet_row(r, 2, 2, w - 4, 4)
        frame(r, 1, 1, w - 2, h - 2, MATS["blue"], 1)
    elif what == "toe":
        rivet_row(r, 2, 2, w - 4, 4)
    elif what == "toe_top":
        for i in range(w):
            px(x0 + i, y0 + h - 2, MATS["blue"][2])
    elif what == "drum":
        for j in range(2, h, 5):
            for i in range(w):
                px(x0 + i, y0 + j, hx("#3a3d44"))
        for i in range(w // 3, w, w // 3):
            for j in range(h):
                px(x0 + i, y0 + j, hx("#141518"))
    elif what == "drum_end":
        cx, cy = w / 2 - 0.5, h / 2 - 0.5
        for j in range(h):
            for i in range(w):
                d2 = (i - cx) ** 2 + (j - cy) ** 2
                if d2 < (w / 2 - 1) ** 2 and d2 > (w / 2 - 3) ** 2:
                    px(x0 + i, y0 + j, hx("#5e646e"))
                if d2 < 3:
                    px(x0 + i, y0 + j, hx("#9aa0aa"))
    elif what == "piston":
        for j in range(1, h - 1):
            px(x0 + w // 2, y0 + j, hx("#a0a8b2"))
            px(x0 + w // 2 + 1, y0 + j, hx("#6a7078"))
    elif what == "grill" or what == "back_grill":
        frame(r, 1, 1, w - 2, h - 2, MATS["steel"], 1)
        for j in range(3, h - 3):
            for i in range(3, w - 3):
                if (i + j) % 3 == 0 or (i - j) % 3 == 0:
                    px(x0 + i, y0 + j, hx("#4a4e56"))
                else:
                    px(x0 + i, y0 + j, hx("#0e0f11"))
        if what == "back_grill":
            for j in range(h // 2 - 2, h // 2 + 2):
                for i in range(w // 2 - 2, w // 2 + 2):
                    lit(x0 + i, y0 + j, ORANGE_LIGHT)
    elif what == "codpiece":
        slots(r, 3, 5, w - 6, 4)
        rivet_row(r, 2, h - 3, w - 4, 3)
    elif what == "ribs":
        for i in range(1, w - 1, 4):
            for j in range(1, h - 1):
                px(x0 + i, y0 + j, hx("#55595f"))
                px(x0 + i + 1, y0 + j, hx("#101113"))
    elif what == "vents":
        slots(r, 2, 4, w - 4, max(1, (h - 8) // 4), 4, glow_c=ORANGE_LIGHT * 0.9)
    elif what == "engine":
        frame(r, 2, 2, w - 4, h - 4, MATS["steel"], 1)
        slots(r, 6, 6, 10, 6, 3, glow_c=ORANGE_LIGHT)
        slots(r, w - 16, 6, 10, 6, 3, glow_c=ORANGE_LIGHT)
        skull(r, w // 2 - 4, h - 14, BONE * 0.9)
    elif what == "deck":
        for i in range(0, w, 6):
            for j in range(h):
                px(x0 + i, y0 + j, hx("#15161a"))
    elif what == "perforated":
        for j in range(2, h - 2, 4):
            for i in range(1 + (j // 4) % 2 * 2, w - 1, 4):
                px(x0 + i, y0 + j, hx("#060606"))
                lit(x0 + i, y0 + j, hx("#ff6a2a") * 0.35, 120)
    elif what == "pipe_top":
        for j in range(2, h - 2):
            for i in range(2, w - 2):
                px(x0 + i, y0 + j, hx("#060606"))
    elif what == "sensor":
        rect(r, 2, 2, w - 4, h - 4, hx("#1a1b1e"))
        light(r, 3, 3, RED_LIGHT)
        light(r, w - 5, 3, GREEN_LIGHT)
    elif what == "gun_side":
        frame(r, 2, 2, w - 4, h - 4, MATS["blue"], 1)
        rect(r, 6, 8, w - 12, 10, hx("#1d1f23"))
        for i in range(7, w - 7, 3):
            for j in range(9, 17):
                px(x0 + i, y0 + j, hx("#5d626b"))
        skull(r, w // 2 - 4, h - 16, BONE)
        light(r, 5, 4, RED_LIGHT)
    elif what == "belt":
        for j in range(0, h, 3):
            for i in range(w):
                px(x0 + i, y0 + j, hx("#c49a3a"))
                px(x0 + i, y0 + j + 1, hx("#7a5a1c"))
    elif what == "muzzles":
        cx, cy = w / 2 - 0.5, h / 2 - 0.5
        for j in range(h):
            for i in range(w):
                if (i - cx) ** 2 + (j - cy) ** 2 < 9:
                    px(x0 + i, y0 + j, hx("#070707"))
    elif what == "bore":
        rect(r, 1, 1, w - 2, h - 2, hx("#060606"))
    elif what == "fist_shoulder":
        frame(r, 2, 2, w - 4, h - 4, GOLD, 1)
        skull(r, w // 2 - 4, 6, BONE)
        sprite(r, w // 2 - 6, 9, LAUREL, {"#": GOLD[1]})
        seal(r, 4, h - 16, 5, 12)
    elif what == "forearm":
        for j in range(h):
            px(x0 + w // 3, y0 + j, MATS["blue"][2])
            px(x0 + w // 3 + 1, y0 + j, MATS["blue"][1] * 0.9)
    elif what == "knuckles":
        for i in range(3, w - 3, 6):
            rect(r, i, 3, 4, h - 6, hx("#4c5058"))
    elif what == "claw_tip":
        frame(r, 0, 0, w, h, MATS["steel"], 1)
    elif what == "skull_face":
        # глазницы и нос; у тёмного металлического черепа глаза светятся
        glow_eyes = mat != "bone"
        ew = max(1, w // 4)
        ey = max(1, h // 4)
        for (ex, ) in ((max(1, w // 2 - ew - 1), ), (w // 2 + 1, )):
            for j in range(ey, min(h - 1, ey + max(1, h // 3))):
                for i in range(ex, min(w - 1, ex + ew)):
                    if glow_eyes:
                        lit(x0 + i, y0 + j, RED_LIGHT)
                    else:
                        px(x0 + i, y0 + j, hx("#18140f"))
        nx, ny = w // 2 - 1, min(h - 2, ey + max(1, h // 3) + 1)
        px(x0 + nx, y0 + ny, hx("#18140f"))
        px(x0 + nx + 1, y0 + ny, hx("#18140f"))
    elif what == "skull_jaw":
        for i in range(1, w - 1, 2):
            for j in range(0, h - 1):
                px(x0 + i, y0 + j, hx("#3a3226"))
    elif what == "bolts":
        for i in range(1, w - 1, 3):
            px(x0 + i, y0 + h // 2, hx("#c4cad4"))
            px(x0 + i, y0 + h // 2 + 1, hx("#202226"))
    elif what == "hull":
        pass


# =============================================================== сборка

packer = Packer(TEX)
pivots = {p[0]: p[2] for p in PARTS}
json_parts = []
extra = []


def to_model(p):
    """(R,U,F) → координаты модели Minecraft (x влево, y вниз, z назад)."""
    return (-p[0], 24 - p[1], -p[2])


def emit_cube(c):
    lo, hi = c["lo"], c["hi"]
    w, h, d = (hi[i] - lo[i] for i in range(3))
    assert w > 0 and h > 0 and d > 0, c
    u, v = packer.place(2 * (w + d), d + h)
    rects = faces(u, v, w, h, d)
    for face, r in rects.items():
        base_paint(r, c["mat"], face, r[2], r[3])
    for face, what in c["deco"].items():
        decorate(rects[face], what, c["mat"])
    if c["mat"] in ("lens", "lens_blue"):
        col = RED_LIGHT if c["mat"] == "lens" else hx("#8cc8ff")
        for r in rects.values():
            for j in range(r[3]):
                for i in range(r[2]):
                    lit(r[0] + i, r[1] + j, col * (0.8 + 0.2 * rng.random()))
    # минимальный угол куба в модели: x и z инвертированы, y вниз
    mlo = to_model((hi[0], hi[1], hi[2]))
    return (u, v), mlo, (w, h, d)


for name, parent, pivot, rot, cubes in PARTS:
    ppiv = to_model(pivots[parent]) if parent != "root" else (0, 0, 0)
    mpiv = to_model(pivot)
    plain = []
    sub = 0
    for c in cubes:
        uv, mlo, size = emit_cube(c)
        if c["rot"] is None:
            plain.append({"uv": uv, "from": [mlo[i] - mpiv[i] for i in range(3)], "size": size})
        else:
            # повёрнутый куб — отдельная дочерняя часть с осью в центре куба
            mc = to_model(c["center"])
            sub += 1
            extra.append({
                "name": "%s_r%d" % (name, sub), "parent": name,
                "offset": [mc[i] - mpiv[i] for i in range(3)],
                "rotation": [math.radians(a) for a in c["rot"]],
                "cubes": [{"uv": uv, "from": [mlo[i] - mc[i] for i in range(3)], "size": size}],
            })
    json_parts.append({
        "name": name, "parent": parent,
        "offset": [mpiv[i] - ppiv[i] for i in range(3)],
        "rotation": list(rot),
        "cubes": plain,
    })
    json_parts.extend(extra)
    extra = []

used = packer.y + packer.row
model = {"texture": [TEX, TEX], "parts": json_parts}

res = os.path.join(ROOT, "src/main/resources/assets/warpbound")
paths = {
    "model": os.path.join(res, "models/entity/dreadnought.json"),
    "tex": os.path.join(res, "textures/entity/dreadnought.png"),
    "glow": os.path.join(res, "textures/entity/dreadnought_glow.png"),
}
for p in paths.values():
    os.makedirs(os.path.dirname(p), exist_ok=True)
with open(paths["model"], "w", encoding="utf-8") as fh:
    json.dump(model, fh, ensure_ascii=False, separators=(",", ":"))
Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8), "RGBA").save(paths["tex"])
Image.fromarray(glow, "RGBA").save(paths["glow"])

if "--dev" in sys.argv:
    build = os.path.join(ROOT, "build/resources/main/assets/warpbound")
    for key, p in paths.items():
        dst = os.path.join(build, os.path.relpath(p, res))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(p, dst)

ncubes = sum(len(p["cubes"]) for p in json_parts)
print("частей:", len(json_parts), "кубов:", ncubes, "развёртка занята до y =", used, "из", TEX)
