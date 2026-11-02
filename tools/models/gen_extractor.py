#!/usr/bin/env python3
"""
Прометиевый экстрактор: исполинская качалка Механикус, 7×13 блоков, высота почти 12 (GeckoLib).

    python3 tools/models/gen_extractor.py

Координаты — пиксели от центра низа ядра: ядро в середине переднего ряда, вглубь +Z (шаблон multiblock/promethium_extractor.json).
Спереди устье скважины и головка с черепом; посередине А-образные башни с осью коромысла; сзади привод, кривошипы с
противовесами, шатуны и дымовые трубы; по бокам баки сырого прометия. Шатуны считаются по настоящей кинематике.
"""
import math

import gen_machines as gm
from gen_machines import SHIP, emblem, gauge, hazard, octagon, screen_glow, screen_text, seal, skull_face
from geo import Model, keys, sin

PX, PY, PZ = 0, 132, 96       # ось коромысла
TAIL, HEAD = 70, 72           # плечи коромысла назад и вперёд
CY, CZ, CR = 50, 166, 14      # ось кривошипа и радиус
ROD = PY - CY                 # длина шатуна
LOOP = 4.0                    # секунды на оборот


def k(t):
    return f"{t * LOOP:.4f}".rstrip("0").rstrip(".") or "0"


def beam_angle(a):
    return math.degrees(math.asin(CR * math.sin(a) / TAIL))


def work_tracks(steps=32):
    beam, crank, rod, rod_pos, head_rod = {}, {}, {}, {}, {}
    for i in range(steps + 1):
        t = i / steps
        a = 2 * math.pi * t
        phi = beam_angle(a)
        crank[k(t)] = [round(360 * t, 2), 0, 0]
        beam[k(t)] = [round(phi, 2), 0, 0]
        # хвост коромысла и палец кривошипа: шатун висит от хвоста до пальца
        ty, tz = PY + TAIL * math.sin(math.radians(phi)), PZ + TAIL * math.cos(math.radians(phi))
        py, pz = CY + CR * math.sin(a), CZ + CR * math.cos(a)
        rod[k(t)] = [round(math.degrees(math.atan2(pz - tz, ty - py)), 2), 0, 0]
        rod_pos[k(t)] = [0, round(ty - PY, 2), 0]
        # головка опускается, когда хвост поднимается: шток ходит за ней
        head_rod[k(t)] = [0, round(-HEAD * math.sin(math.radians(phi)), 2), 0]
    return beam, crank, rod, rod_pos, head_rod


def build():
    m = Model("promethium_extractor", S=1, atlas_w=1024)
    r = m.bone("extractor", [0, 0, 0])

    # ---- плита: ступени, кромка опасности, анкеры
    r.cube([-56, 0, -8], [112, 8, 208], "hd_dark")
    r.cube([-52, 8, -4], [104, 4, 200], "hd_hull")
    r.cube([-53, 12, -5], [106, 1, 202], "hd_dark", deco={"up": hazard})
    for z in (4, 60, 132, 188):
        for x in (-52, 46):
            r.cube([x, 8, z], [6, 7, 6], "hd_brass")

    # ---- устье скважины: восьмигранный оголовок, фланцы, задвижки, манометры, череп
    wz = PZ - HEAD
    octagon(r, (0, wz), 13, 34, 12, "hd_dark")
    octagon(r, (0, wz), 25, 26, 20, "hd_rusty")
    for y in (28, 40):
        octagon(r, (0, wz), y, 30, 3, "hd_brass")
    octagon(r, (0, wz), 45, 14, 8, "hd_steel")
    for sx in (-1, 1):                                   # отводы и маховики задвижек
        r.cube([sx * 24 - 8, 30, wz - 5], [16, 10, 10], "hd_rusty")
        r.cube([sx * 32 - 2, 26, wz - 8], [4, 18, 16], "hd_dark")
        r.cube([sx * 30 - 1, 42, wz - 1], [2, 8, 2], "hd_steel")
        r.cube([sx * 30 - 6, 49, wz - 6], [12, 2, 12], "hd_red")
    r.cube([-5, 28, wz - 16], [10, 10, 2], "hd_dark", deco={"north": gauge})

    # ---- баки сырого прометия: два вертикальных восьмигранника, смотровые щели, пояса, трубы к устью
    for sx in (-1, 1):
        x = sx * 37
        octagon(r, (x, 56), 13, 30, 72, "hd_hull")
        for y in (20, 44, 68):
            octagon(r, (x, 56), y, 33, 3, "hd_brass")
        octagon(r, (x, 56), 85, 22, 6, "hd_dark")
        octagon(r, (x, 56), 91, 10, 6, "hd_steel")
        r.cube([x - 2, 26, 56 - 16.5], [4, 40, 1], "hd_fire", glow="all")
        r.cube([sx * 15 - (0 if sx > 0 else 8) , 20, 28], [8, 8, 24], "hd_rusty")
        r.cube([sx * 20 - 8, 20, 44], [16, 8, 8], "hd_rusty")
    seal(r, -44, 62, 39)
    seal(r, 30, 50, 39)

    # ---- А-образные башни: стойки вразлёт, раскосы, поперечина, площадка с перилами, опорная ось
    for sx in (-1, 1):
        x = sx * 34
        r.cube([x - 9, 13, PZ - 44], [18, 8, 88], "hd_dark")
        for sz, rot in ((-1, -15), (1, 15)):             # ноги сходятся к оси
            base = PZ + sz * 30
            r.cube([x - 6, 15, base - 6], [12, 112, 12], "hd_hull", rotation=[rot, 0, 0], pivot=[x, 15, base])
            for y in (40, 72, 104):                      # хомуты: тот же поворот вокруг основания ноги
                r.cube([x - 7, y, base - 7], [14, 3, 14], "hd_brass", rotation=[rot, 0, 0], pivot=[x, 15, base])
        r.cube([x - 8, PY - 12, PZ - 10], [16, 22, 20], "hd_dark")
        r.cube([x - 10, PY - 6, PZ - 6], [20, 12, 12], "hd_brass")
    r.cube([-40, 66, PZ - 3], [80, 6, 6], "hd_rusty")
    r.cube([-40, PY - 3, PZ - 3], [80, 6, 6], "hd_steel")
    r.cube([-26, 74, PZ - 14], [52, 3, 28], "hd_dark")                  # площадка обслуживания
    for sx in (-1, 1):
        r.cube([sx * 26 - 1, 77, PZ - 14], [2, 10, 28], "hd_steel")
    r.cube([-13, 77, PZ - 10], [26, 22, 3], "hd_brass", deco={"north": emblem(0.45)})

    # ---- привод: кожух двигателя, редуктор, поршни, экран, дымовые трубы с огнём
    r.cube([-40, 13, 128], [80, 22, 60], "hd_hull")
    r.cube([-42, 13, 126], [84, 5, 64], "hd_dark")
    r.cube([-30, 35, 136], [60, 20, 44], "hd_rusty")
    r.cube([-34, 44, 132], [68, 3, 52], "hd_brass")
    for x in (-24, 0, 24):                               # головки цилиндров
        r.cube([x - 7, 55, 140], [14, 8, 14], "hd_dark")
        r.cube([x - 5, 63, 142], [10, 4, 10], "hd_steel")
    r.cube([-16, 20, 125.5], [32, 12, 1], "hd_screen", deco={"north": screen_text}, glow=screen_glow)
    for sx in (-1, 1):
        x = sx * 28
        octagon(r, (x, 190), 13, 16, 110, "hd_rusty")
        for y in (40, 76, 112):
            octagon(r, (x, 190), y, 19, 3, "hd_brass")
        octagon(r, (x, 190), 123, 21, 7, "hd_dark")
    flame = m.bone("stack_flame", [0, 130, 190], "extractor")
    for sx in (-1, 1):
        flame.cube([sx * 28 - 5, 130, 185], [10, 7, 10], "hd_fire", glow="all")

    # ---- кривошипы с противовесами (крутятся), шатуны (качаются), вал
    crank = m.bone("crank", [0, CY, CZ], "extractor")
    crank.cube([-52, CY - 4, CZ - 4], [104, 8, 8], "hd_steel")
    for sx in (-1, 1):
        x = sx * 46
        crank.cube([x - 3, CY - 8, CZ - 6], [6, 16, CR + 12], "hd_dark")       # щека к пальцу (+Z)
        crank.cube([x - 5, CY - 16, CZ - 34], [10, 32, 30], "hd_hull")         # противовес (−Z)
        crank.cube([x - 5.5, CY - 5, CZ - 34.5], [11, 10, 1], "hd_brass")
    for i, sx in enumerate((-1, 1)):
        rod = m.bone(f"rod_{i + 1}", [sx * 40, PY, PZ + TAIL], "extractor")
        x = sx * 40
        rod.cube([x - 3, PY - ROD, PZ + TAIL - 3], [6, ROD, 6], "hd_steel")
        rod.cube([x - 5, PY - 6, PZ + TAIL - 5], [10, 10, 10], "hd_dark")
        rod.cube([x - 5, PY - ROD - 5, PZ + TAIL - 5], [10, 10, 10], "hd_dark")
        rod.cube([x - 3.5, PY - ROD / 2, PZ + TAIL - 3.5], [7, 3, 7], "hd_brass")

    # ---- коромысло: двойная балка, рёбра, хвостовой траверс, головка-череп
    beam = m.bone("beam", [PX, PY, PZ], "extractor")
    for sx in (-1, 1):
        beam.cube([sx * 14 - 5, PY - 8, PZ - HEAD + 10], [10, 16, HEAD + TAIL - 4], "hd_hull")
        beam.cube([sx * 14 - 5.5, PY + 8, PZ - HEAD + 10], [11, 2, HEAD + TAIL - 4], "hd_brass")
    for z in range(int(PZ - HEAD + 18), int(PZ + TAIL), 18):
        beam.cube([-9, PY - 5, z], [18, 10, 3], "hd_dark")
    beam.cube([-44, PY - 6, PZ + TAIL - 6], [88, 12, 12], "hd_rusty")
    beam.cube([-20, PY - 12, PZ - 12], [40, 24, 24], "hd_dark")
    # головка: дуга из трёх плит над скважиной, череп спереди, шпиль
    z0 = PZ - HEAD
    beam.cube([-13, PY - 22, z0 - 6], [26, 44, 16], "hd_hull")
    beam.cube([-11, PY + 22, z0 + 2], [22, 8, 14], "hd_hull")
    beam.cube([-11, PY - 30, z0 + 2], [22, 8, 14], "hd_hull")
    beam.cube([-14, PY - 18, z0 - 8], [28, 3, 20], "hd_brass")
    beam.cube([-14, PY + 15, z0 - 8], [28, 3, 20], "hd_brass")
    beam.cube([-10, PY - 11, z0 - 13], [20, 22, 8], "hd_bone", deco={"north": skull_face})
    beam.cube([-1.5, PY + 30, z0 + 7], [3, 16, 3], "hd_dark")
    # шток: ходит вертикально за головкой
    pump = m.bone("pump_rod", [0, PY, z0], "extractor")
    pump.cube([-2, 48, z0 - 2], [4, PY - 48 - 22, 4], "hd_steel")
    pump.cube([-5, PY - 30, z0 - 5], [10, 8, 10], "hd_dark")

    beam_k, crank_k, rod_k, rod_pos, head_k = work_tracks()
    bones = {
        "beam": {"rotation": beam_k}, "crank": {"rotation": crank_k}, "pump_rod": {"position": head_k},
        "rod_1": {"rotation": rod_k, "position": rod_pos}, "rod_2": {"rotation": rod_k, "position": rod_pos},
        "stack_flame": {"scale": keys([(i * LOOP / 8, [1, 1 + 0.5 * abs(sin(i / 8)), 1]) for i in range(9)])},
    }
    anims = {
        "misc.idle": {"length": 4.0, "loop": True, "bones": {"stack_flame": {"scale": keys([(0, [0, 0, 0])])}}},
        "work.active": {"length": LOOP, "loop": True, "bones": bones},
    }
    gm.finish(m, "promethium_extractor", SHIP, anims)


if __name__ == "__main__":
    build()
