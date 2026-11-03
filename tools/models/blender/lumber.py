"""
Лесопилка-культиватор (lumber): 5×5×4. Сзади делянка с молодыми деревьями под люменами, спереди стол с дисковой пилой:
каретка подаёт бревно, сервитор держит его за рельс, сбоку растёт куча досок, снизу сыплются опилки.
"""
import math
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "kit.py"), encoding="utf-8").read())

LOOP, STEPS = 5.0, 60
SAW = (0.0, -1.0, 1.08)      # центр диска, ось вдоль X
TABLE_Z = 1.0
Y_START, Y_END = -2.3, 0.15  # ход каретки с бревном по Y


def frame(m):
    f = m.bone("frame")
    f.plinth(-2.48, -2.48, 2.48, 2.48)
    # ---- делянка сзади
    f.box((-2.38, 0.42, 0.3), (2.38, 2.38, 0.42), "soil")
    for x in (-2.38, 2.34):
        f.box((x, 0.42, 0.3), (x + 0.04, 2.38, 0.5), "dark")
    f.box((-2.38, 2.34, 0.3), (2.38, 2.38, 0.5), "dark")
    # деревья на делянке — настоящие ванильные блоки, их рисует LumberTrees.java
    # каркас теплицы с люменами
    for x in (-2.35, 0, 2.35):
        for y in (0.45, 2.35):
            f.box((x - 0.05, y - 0.05, 0.42), (x + 0.05, y + 0.05, 3.62), "dark")
        f.box((x - 0.05, 0.45, 3.56), (x + 0.05, 2.35, 3.66), "dark")
    f.box((-2.4, 0.4, 3.56), (2.4, 0.5, 3.66), "hull", bevel=0.01)
    f.box((-2.4, 2.3, 3.56), (2.4, 2.4, 3.66), "hull", bevel=0.01)
    for x in (-1.65, -0.55, 0.55, 1.65):
        f.box((x - 0.26, 0.9, 3.5), (x + 0.26, 1.9, 3.56), "dark", bevel=0.008)
        f.box((x - 0.2, 0.96, 3.475), (x + 0.2, 1.84, 3.5), "lumen")
    # ---- стол пилы
    for s in (-1, 1):
        f.box((s * 0.82 - 0.09, -2.42, 0.3), (s * 0.82 + 0.09, 0.32, TABLE_Z - 0.07), "dark", bevel=0.015)
        f.box((s * 0.68 - 0.03, -2.42, TABLE_Z - 0.07), (s * 0.68 + 0.03, 0.32, TABLE_Z), "brass")
    f.box((-0.8, -2.42, TABLE_Z - 0.14), (-0.08, 0.32, TABLE_Z - 0.05), "hull")
    f.box((0.08, -2.42, TABLE_Z - 0.14), (0.8, 0.32, TABLE_Z - 0.05), "hull")
    # кожух диска, опоры вала, мотор
    f.lathe((SAW[0], SAW[1], SAW[2]), [(0.52, -0.1), (0.62, -0.08), (0.62, 0.08), (0.52, 0.1)], 16, "dark", "X") if False else None
    f.plate_xz([(-0.08, TABLE_Z - 0.14), (0.08, TABLE_Z - 0.14), (0.08, 0.32), (-0.08, 0.32)], SAW[1] - 0.2, SAW[1] + 0.2, "dark")
    f.lathe((1.3, SAW[1], 0.82), [(0.28, -0.34), (0.28, 0.34), (0.15, 0.42)], 12, "rust", "X", base=True)
    for k in range(4):
        f.ring((1.08 + k * 0.14, SAW[1], 0.82), 0.27, 0.32, 0.04, 12, "dark", "X")
    f.box((0.9, SAW[1] - 0.32, 0.3), (1.75, SAW[1] + 0.32, 0.5), "dark", bevel=0.02)
    # щит над пилой
    f.lathe((0, SAW[1], SAW[2]), [(0.62, -0.1), (0.66, -0.1)], 12, "hazard", "X", cap=False, phase=0.3) if False else None
    f.box((-0.14, SAW[1] - 0.72, SAW[2] + 0.48), (0.14, SAW[1] + 0.72, SAW[2] + 0.58), "hazard", bevel=0.01)
    f.box((-0.05, SAW[1] + 0.6, TABLE_Z), (0.05, SAW[1] + 0.7, SAW[2] + 0.48), "dark")
    # ---- рельс сервитора над столом
    for s in (-1, 1):
        f.box((s * 1.25 - 0.07, -2.3, 0.3), (s * 1.25 + 0.07, -2.16, 2.75), "dark", bevel=0.012)
        f.box((s * 1.25 - 0.07, 0.25, 0.3), (s * 1.25 + 0.07, 0.39, 2.75), "dark", bevel=0.012)
    f.box((-1.28, -2.32, 2.75), (1.28, -2.14, 2.87), "hull", bevel=0.02)
    f.box((-1.28, 0.23, 2.75), (1.28, 0.41, 2.87), "hull", bevel=0.02)
    for s in (-1, 1):
        f.box((s * 0.34 - 0.04, -2.14, 2.8), (s * 0.34 + 0.04, 0.23, 2.86), "steel")
    f.skull(0, -2.05, 2.5, 0.42)
    # ---- штабель досок справа и готовые доски слева
    for i in range(8):
        for j in range(2):
            z = 0.3 + i * 0.09
            x = 1.84 + j * 0.4 + (0.02 if i % 2 else -0.01)
            f.box((x - 0.2, -2.28, z), (x + 0.2, -0.6, z + 0.085), "wood", bevel=0.006)
    for i in range(3):
        f.lathe((-1.9, -1.9 + i * 0.5, 0.48), [(0.17, -0.45), (0.17, 0.45)], 8, "wood", "X", phase=i)
        f.lathe((-1.9, -1.9 + i * 0.5, 0.48), [(0.12, 0.45), (0.12, 0.46)], 8, "parchment", "X", phase=i, base=False)
    # куча опилок под столом
    f.lathe((0, SAW[1], 0.3), [(0.72, 0), (0.42, 0.14), (0.08, 0.3)], 9, "parchment", base=False)
    f.seal((-1.25, -2.17, 1.6), "Y", -1)
    # ---- пульт
    f.box((-2.42, 0.0, 0.3), (-1.72, 0.34, 1.35), "hull", bevel=0.025)
    f.box((-2.34, -0.015, 0.55), (-1.8, 0.0, 1.15), "screen")


def moving(m):
    # ---- диск: зубья треугольниками
    d = m.bone("saw", SAW)
    d.ring(SAW, 0.08, 0.5, 0.025, 14, "steel", "X")
    d.gear(SAW, 0.47, 0.57, 0.022, 16, "steel", "X", fill=0.3)
    d.lathe(SAW, [(0.1, -0.08), (0.1, 0.08)], 8, "brass", "X")
    # ---- шкив и ремень к мотору: шкив вращается
    b = m.bone("pulley", (0.28, SAW[1], SAW[2]))
    b.gear((0.28, SAW[1], SAW[2]), 0.13, 0.18, 0.1, 8, "brass", "X")
    b.lathe((0.28, SAW[1], SAW[2]), [(0.03, -0.3), (0.03, 0.15)], 6, "steel", "X")
    # ---- каретка с бревном: сервитор-манипулятор стоит на ней и держит бревно снизу
    cy = Y_START + 0.4
    c = m.bone("log", (0, cy, TABLE_Z))
    c.box((-0.6, cy - 0.3, TABLE_Z), (-0.14, cy + 0.3, TABLE_Z + 0.05), "dark")
    c.box((0.14, cy - 0.3, TABLE_Z), (0.6, cy + 0.3, TABLE_Z + 0.05), "dark")
    c.lathe((0, cy + 0.4, TABLE_Z + 0.27), [(0.21, -0.92), (0.21, 0.92)], 10, "wood", "Y")
    c.lathe((0, cy + 0.4, TABLE_Z + 0.27), [(0.16, -0.93), (0.16, -0.92)], 10, "parchment", "Y", base=False)
    for s in (-1, 1):
        c.box((s * 0.28 - 0.03, cy - 0.28, TABLE_Z + 0.05), (s * 0.28 + 0.03, cy - 0.22, TABLE_Z + 0.32), "steel")
        c.box((s * 0.28 - 0.03, cy + 0.82, TABLE_Z + 0.05), (s * 0.28 + 0.03, cy + 0.88, TABLE_Z + 0.32), "steel")
    # ---- опилки летят от пилы
    for i in range(5):
        s = m.bone(f"dust_{i}", (SAW[0], SAW[1], TABLE_Z - 0.14))
        s.lathe((SAW[0], SAW[1], TABLE_Z - 0.14), [(0, -0.02), (0.025, 0), (0, 0.02)], 4, "parchment", cap=False)


def pose(t):
    a = 2 * math.pi * t
    p = {"saw": {"rot": (360 * 6 * t, 0, 0)}, "pulley": {"rot": (360 * 12 * t, 0, 0)}}
    # каретка: подача 0→0.72 цикла, быстрый возврат
    u = min(1, t / 0.72)
    if t < 0.72:
        y = (Y_END - Y_START) * u
        cut = 1.0
    else:
        back = (t - 0.72) / 0.28
        y = (Y_END - Y_START) * (1 - back * back * (3 - 2 * back))
        cut = 0.0
    p["log"] = {"pos": (0, y, 0)}
    for i in range(5):
        k = (t * 5 + i / 5) % 1
        vis = 1 if cut and k < 0.85 else 0
        spread = (i - 2) * 0.12
        p[f"dust_{i}"] = {"pos": (spread * k, 0.15 * k, -0.45 * k * k), "scale": (vis, vis, vis)}
    return p


m = Machine("lumber")
frame(m)
moving(m)
sc, tris = m.build("WB_Lumber")
light_scene(sc, int(LOOP * 24))
auto_animate(m.objects, sc, pose, LOOP)
tracks = lambda: auto_tracks(pose, LOOP, STEPS)
print("костей:", len(m.objects), "треугольников:", tris)
