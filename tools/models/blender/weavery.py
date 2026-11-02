"""
Флак-мастерская (weavery): 5×3×3. Механический ткацкий станок: нити идут со шпулярника сзади через ремизки, челнок бегает поперёк,
батан прибивает уток, полотно наматывается на вал спереди. Сбоку пресс флак-пластин и манекен в готовой броне.
"""
import math
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "kit.py"), encoding="utf-8").read())

LOOP, STEPS = 2.0, 48
HW = 1.15             # полуширина полотна
LOOM_Z = 1.18         # высота зева
ROLL = (0.0, -1.05, 0.72)


def frame(m):
    f = m.bone("frame")
    f.plinth(-2.48, -1.48, 2.48, 1.48)
    # ---- рама станка: две боковины и поперечины
    for s in (-1, 1):
        x = s * (HW + 0.22)
        f.box((x - 0.09, -1.15, 0.3), (x + 0.09, 1.1, 0.5), "dark", bevel=0.02)
        for y in (-0.95, 0.15, 0.95):
            f.box((x - 0.08, y - 0.08, 0.5), (x + 0.08, y + 0.08, 2.1), "hull", bevel=0.02)
        f.box((x - 0.08, -1.05, 2.1), (x + 0.08, 1.05, 2.25), "dark", bevel=0.02)
        f.box((x - 0.09, -1.06, 2.16), (x + 0.09, 1.06, 2.2), "brass")
    f.box((-HW - 0.3, 0.87, 2.0), (HW + 0.3, 1.03, 2.15), "dark", bevel=0.02)
    # полотно: готовая ткань от батана к валу, нити основы от батана к навою
    f.box((-HW, -0.95, LOOM_Z - 0.01), (HW, -0.28, LOOM_Z + 0.008), "red")
    for k in range(25):
        x = -HW + 0.04 + k * (2 * HW - 0.08) / 24
        f.beam((x, -0.28, LOOM_Z), (x, 0.82, LOOM_Z + 0.02), 0.012, 0.012, "parchment")
    f.lathe((-HW, 0.85, LOOM_Z + 0.02), [(0.1, 0), (0.1, 2 * HW)], 10, "brass", "X")
    # ---- шпулярник сзади: ряды шпуль; самую заметную строку вращаем отдельно
    f.box((-1.45, 1.08, 0.3), (1.45, 1.38, 0.42), "dark")
    for x in (-1.42, 1.42):
        f.box((x - 0.05, 1.12, 0.42), (x + 0.05, 1.34, 2.2), "hull")
    for z in (0.8, 1.3):
        f.lathe((-1.42, 1.22, z), [(0.02, 0), (0.02, 2.84)], 4, "steel", "X", base=False)
        for k in range(7):
            f.lathe((-1.22 + k * 0.41, 1.22, z), [(0.06, 0), (0.12, 0.03), (0.12, 0.28), (0.06, 0.31)], 8, "parchment", "X", base=False)
    # ---- кожух привода с мотором слева
    f.box((-2.42, -1.05, 0.3), (-1.62, 0.5, 1.6), "hull", bevel=0.06)
    f.box((-2.44, -1.07, 1.02), (-1.6, 0.52, 1.09), "brass")
    for k in range(5):
        f.box((-2.44, -0.9 + k * 0.28, 0.5), (-2.42, -0.75 + k * 0.28, 0.92), "dark")
    f.lathe((-2.02, -0.28, 1.6), [(0.24, 0), (0.24, 0.42), (0.1, 0.5)], 10, "rust", base=False)
    f.box((-1.7, -1.06, 1.3), (-2.32, -1.05, 1.32), "dark") if False else None
    f.box((-2.28, -1.07, 1.15), (-1.76, -1.05, 1.5), "screen")
    f.lathe((-1.62, 0.1, 1.0), [(0.08, 0), (0.08, 0.28)], 8, "steel", "X")
    # череп над кожухом
    f.skull(-2.02, -1.0, 2.25, 0.36, augmetic=False)
    f.box((-2.2, -1.0, 1.6), (-1.84, -0.8, 2.05), "dark", bevel=0.02)
    # ---- справа: пресс флак-пластин и манекен в броне
    f.box((1.68, -0.1, 0.3), (2.4, 0.9, 0.86), "dark", bevel=0.04)
    for s in (-1, 1):
        f.box((2.04 + s * 0.3 - 0.05, 0.1, 0.86), (2.04 + s * 0.3 + 0.05, 0.7, 2.05), "hull", bevel=0.012)
    f.box((1.68, 0.05, 2.05), (2.4, 0.75, 2.25), "dark", bevel=0.02)
    f.box((1.84, 0.2, 0.86), (2.24, 0.6, 0.93), "steel")
    f.box((1.87, 0.23, 0.93), (2.21, 0.57, 0.97), "brick")
    f.lathe((2.04, 0.4, 2.25), [(0.14, 0), (0.14, 0.28), (0.06, 0.32)], 8, "brass", base=False)
    # манекен
    mx, my = 2.02, -0.82
    f.lathe((mx, my, 0.3), [(0.32, 0), (0.32, 0.05), (0.05, 0.1), (0.05, 0.92)], 10, "dark", base=False)
    f.box((mx - 0.26, my - 0.17, 1.2), (mx + 0.26, my + 0.17, 1.82), "brick", bevel=0.06)
    f.box((mx - 0.28, my - 0.19, 1.62), (mx + 0.28, my + 0.19, 1.78), "hull", bevel=0.02)
    f.box((mx - 0.2, my - 0.2, 1.3), (mx + 0.2, my - 0.17, 1.58), "hull")
    for s in (-1, 1):
        f.box((mx + s * 0.34 - 0.1, my - 0.13, 1.6), (mx + s * 0.34 + 0.1, my + 0.13, 1.84), "hull", bevel=0.03)
    f.lathe((mx, my, 1.84), [(0.11, 0), (0.13, 0.1), (0.1, 0.24), (0.03, 0.28)], 8, "hull", base=False)
    f.box((mx - 0.09, my - 0.135, 1.93), (mx + 0.09, my - 0.1, 1.99), "stain_red")
    f.seal((-1.4, -1.0, 1.95), "Y", -1)
    f.seal((1.4, -1.0, 1.95), "Y", -1)


def moving(m):
    # ---- вал с намотанной тканью
    r = m.bone("cloth_roll", ROLL)
    r.lathe((-HW, ROLL[1], ROLL[2]), [(0.42, 0), (0.42, 2 * HW)], 14, "red", "X")
    r.lathe((-HW - 0.2, ROLL[1], ROLL[2]), [(0.06, 0), (0.06, 2 * HW + 0.4)], 6, "steel", "X")
    for x in (-HW, HW):
        r.ring((x, ROLL[1], ROLL[2]), 0.1, 0.44, 0.03, 12, "brass")
    r.box((-HW, ROLL[1] - 0.012, ROLL[2] + 0.38), (HW, ROLL[1] + 0.012, ROLL[2] + 0.43), "brick")
    # ---- батан: качается вокруг нижней оси и прибивает уток
    b = m.bone("batten", (0, -0.3, 0.55))
    b.box((-HW - 0.05, -0.34, 0.5), (HW + 0.05, -0.26, 0.62), "dark", bevel=0.012)
    b.box((-HW - 0.05, -0.34, LOOM_Z + 0.2), (HW + 0.05, -0.26, LOOM_Z + 0.3), "dark", bevel=0.012)
    for k in range(14):
        x = -HW + k * 2 * HW / 13
        b.box((x - 0.006, -0.31, 0.62), (x + 0.006, -0.29, LOOM_Z + 0.2), "steel")
    for s in (-1, 1):
        b.box((s * (HW + 0.02) - 0.03, -0.33, 0.5), (s * (HW + 0.02) + 0.03, -0.27, LOOM_Z + 0.3), "hull")
    # ---- ремизки: ходят вверх-вниз попеременно, образуя зев
    for i, y in enumerate((0.16, 0.34)):
        h = m.bone(f"heddle_{i + 1}", (0, y, LOOM_Z))
        h.box((-HW, y - 0.04, LOOM_Z - 0.45), (HW, y + 0.04, LOOM_Z - 0.38), "brick")
        h.box((-HW, y - 0.04, LOOM_Z + 0.42), (HW, y + 0.04, LOOM_Z + 0.5), "brick")
        for k in range(10):
            x = -HW + 0.1 + k * (2 * HW - 0.2) / 9
            h.box((x - 0.008, y - 0.01, LOOM_Z - 0.38), (x + 0.008, y + 0.01, LOOM_Z + 0.42), "steel")
        h.box((-HW - 0.1, y - 0.02, LOOM_Z + 0.5), (-HW - 0.05, y + 0.02, 2.2), "steel")
        h.box((HW + 0.05, y - 0.02, LOOM_Z + 0.5), (HW + 0.1, y + 0.02, 2.2), "steel")
    # ---- челнок
    s = m.bone("shuttle", (0, -0.12, LOOM_Z + 0.03))
    s.lathe((-0.22, -0.12, LOOM_Z + 0.03), [(0.005, 0), (0.045, 0.1), (0.045, 0.34), (0.005, 0.44)], 6, "brass", "X", cap=False)
    s.box((-0.09, -0.15, LOOM_Z + 0.03), (0.09, -0.09, LOOM_Z + 0.075), "red")


def pose(t):
    a = 2 * math.pi * t
    sh = 1.0 * math.sin(a)
    # челнок почти прямолинеен: краткие остановки на концах дают мягкий косинус
    batt = -5 + 11 * max(0, math.sin(2 * a))
    he = 0.13 * math.sin(a + math.pi / 2)
    return {
        "cloth_roll": {"rot": (-360 * t, 0, 0)},
        "batten": {"rot": (batt, 0, 0)},
        "heddle_1": {"pos": (0, 0, he)},
        "heddle_2": {"pos": (0, 0, -he)},
        "shuttle": {"pos": (sh, 0, 0)},
    }


m = Machine("weavery")
frame(m)
moving(m)
sc, tris = m.build("WB_Weavery")
light_scene(sc, int(LOOP * 24))
auto_animate(m.objects, sc, pose, LOOP)
tracks = lambda: auto_tracks(pose, LOOP, STEPS)
print("костей:", len(m.objects), "треугольников:", tris)
