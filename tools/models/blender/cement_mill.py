"""
Цементная мельница (cement_mill): 3×3×4. Шаровая мельница: лежащий барабан с зубчатым венцом крутится на бандажах,
сверху бункер шихты, снизу шнек сыплет серый порошок в ящик спереди.
"""
import math
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "kit.py"), encoding="utf-8").read())

LOOP, STEPS = 3.0, 48
AXIS_Z, AXIS_Y = 1.42, 0.12     # ось барабана: идёт вдоль X
R = 0.82                        # радиус барабана
DROP = (-0.62, -1.0, 0.95)      # откуда сыплется
BOX_Z = 0.6


def frame(m):
    f = m.bone("frame")
    f.plinth(-1.48, -1.48, 1.48, 1.48)
    # ---- опоры барабана
    for x in (-1.2, 1.2):
        f.plate_xz([(x - 0.2, 0.3), (x + 0.2, 0.3), (x + 0.2, AXIS_Z - 0.02), (x - 0.2, AXIS_Z - 0.02)], AXIS_Y - 0.58, AXIS_Y + 0.58, "dark")
        f.box((x - 0.22, AXIS_Y - 0.6, AXIS_Z - 0.02), (x + 0.22, AXIS_Y + 0.6, AXIS_Z + 0.08), "hull", bevel=0.02)
        for s in (-1, 1):
            f.wedge((x - 0.2, AXIS_Y + s * 0.58 - 0.09, 0.3), (x + 0.2, AXIS_Y + s * 0.58 + 0.09),
                    (x - 0.08, AXIS_Y + s * 0.5 - 0.05, 1.1), (x + 0.08, AXIS_Y + s * 0.5 + 0.05), "dark")
    # ---- кожух венца и редуктор сзади справа
    f.box((0.46, AXIS_Y + 0.92, 0.3), (1.34, 1.42, 1.3), "hull", bevel=0.03)
    f.box((0.44, AXIS_Y + 0.9, 1.0), (1.36, 1.44, 1.06), "brass")
    # ---- мотор: цилиндр с рёбрами, вал уходит в редуктор
    f.lathe((-0.42, 1.12, 0.78), [(0.3, -0.42), (0.3, 0.46), (0.18, 0.54)], 12, "rust", "X", base=True)
    for k in range(6):
        f.ring((-0.72 + k * 0.13, 1.12, 0.78), 0.28, 0.335, 0.03, 12, "dark", "X")
    f.box((-0.92, 0.8, 0.3), (0.1, 1.42, 0.5), "dark", bevel=0.02)
    # ---- бункер шихты над барабаном
    for x in (-0.86, 0.86):
        f.box((x - 0.07, AXIS_Y - 0.86, 0.3), (x + 0.07, AXIS_Y - 0.72, 2.75), "dark", bevel=0.01)
        f.box((x - 0.07, AXIS_Y + 0.72, 1.3), (x + 0.07, AXIS_Y + 0.86, 2.75), "dark", bevel=0.01)
    f.box((-0.94, AXIS_Y - 0.92, 2.68), (0.94, AXIS_Y + 0.92, 2.8), "hull", bevel=0.02)
    f.loft([(2.5, 0.2, 0.2, AXIS_Y), (2.8, 0.7, 0.72, AXIS_Y), (3.58, 0.92, 0.96, AXIS_Y), (3.76, 0.92, 0.96, AXIS_Y)], "rust")
    f.box((-0.96, AXIS_Y - 0.98, 3.36), (0.96, AXIS_Y + 0.98, 3.44), "brass")
    f.lathe((0, AXIS_Y, 2.32), [(0.15, 0), (0.15, 0.2)], 8, "dark", base=False)
    # шихта виднеется в бункере
    f.box((-0.84, AXIS_Y - 0.88, 3.7), (0.84, AXIS_Y + 0.88, 3.72), "concrete")
    for x, y in ((-0.45, -0.3), (0.2, 0.15), (0.5, -0.5), (-0.2, 0.55), (0.6, 0.55)):
        f.lathe((x, AXIS_Y + y, 3.71), [(0.17, 0), (0.08, 0.1), (0.02, 0.14)], 5, "concrete", base=False)
    # ---- разгрузка: шнек и ящик
    f.pipe([(-0.62, AXIS_Y - 0.55, 0.8), (-0.62, -0.75, 1.0), (DROP[0], DROP[1], DROP[2] + 0.1)], 0.13, 8, "hull")
    f.box((-0.8, -1.1, DROP[2] - 0.05), (-0.44, -0.86, DROP[2] + 0.18), "dark", bevel=0.015)
    # ящик с цементом
    for s in (-1, 1):
        f.box((-0.62 + s * 0.5 - 0.03, -1.38, 0.3), (-0.62 + s * 0.5 + 0.03, -0.72, BOX_Z + 0.1), "wood")
        f.box((-1.15, -1.05 + s * 0.33 - 0.03, 0.3), (-0.09, -1.05 + s * 0.33 + 0.03, BOX_Z + 0.1), "wood")
    f.box((-1.1, -1.35, 0.32), (-0.14, -0.75, BOX_Z), "concrete")
    f.lathe((-0.62, -1.05, BOX_Z), [(0.3, 0), (0.15, 0.1), (0.03, 0.17)], 8, "concrete", base=False)
    # ---- пульт и печати
    f.box((0.55, -1.42, 0.3), (1.35, -1.02, 1.05), "hull", bevel=0.025)
    f.box((0.62, -1.43, 0.42), (1.28, -1.415, 0.82), "screen")
    f.skull(0.95, -1.05, 1.28, 0.32, augmetic=False)
    f.seal((0.72, -1.415, 0.95), "Y", -1) if False else None
    f.seal((-1.0, AXIS_Y - 0.74, 2.45), "Y", -1)
    # ---- фильтр пыли сзади слева
    f.lathe((-1.1, 0.95, 1.02), [(0.25, 0), (0.25, 1.05), (0.1, 1.22)], 10, "steel", base=False)
    f.pipe([(-1.1, 0.95, 2.22), (-1.1, 0.5, 2.5), (-0.62, AXIS_Y + 0.2, 2.72)], 0.05, 6, "rust")


def moving(m):
    # ---- барабан: корпус, бандажи, венец, ряды клёпки и лючок — видно, что вращается
    d = m.bone("drum", (0, AXIS_Y, AXIS_Z))
    c = (0, AXIS_Y, AXIS_Z)
    d.lathe(c, [(0.28, -1.08), (R - 0.12, -0.98), (R, -0.82), (R, 0.82), (R - 0.12, 0.98), (0.28, 1.08)], 18, "hull", "X", phase=0.0)
    for x in (-0.72, 0.2):
        d.ring((x, AXIS_Y, AXIS_Z), R - 0.02, R + 0.05, 0.12, 18, "steel", "X")
    d.gear((0.72, AXIS_Y, AXIS_Z), R + 0.02, R + 0.14, 0.16, 28, "brass", "X")
    for k in range(10):
        a = k * math.pi / 5
        for x in (-0.28, -0.05, 0.42):
            d.bolt((x, AXIS_Y + (R - 0.002) * math.cos(a), AXIS_Z + (R - 0.002) * math.sin(a)), "X", 0.03, 0.024, "steel") if False else None
    for k in range(6):
        a = k * math.pi / 3
        y, z = AXIS_Y + R * math.cos(a), AXIS_Z + R * math.sin(a)
        d.beam((-0.6, y, z), (0.6, y, z), 0.08, 0.03, "dark")
    # люк и красная метка
    d.box((-0.2, AXIS_Y - 0.2, AXIS_Z + R - 0.01), (0.2, AXIS_Y + 0.2, AXIS_Z + R + 0.05), "red", bevel=0.012)
    # ---- ведущая шестерня: зацеплена с венцом сзади снизу
    a = math.radians(-58)
    py, pz = AXIS_Y + (R + 0.28) * math.cos(a), AXIS_Z + (R + 0.28) * math.sin(a)
    g = m.bone("pinion", (0.72, py, pz))
    g.gear((0.72, py, pz), 0.16, 0.25, 0.18, 8, "brass", "X")
    g.lathe((0.72, py, pz), [(0.05, -0.2), (0.05, 0.2)], 6, "steel", "X")
    # ---- порошок: две струйки и пыль
    for i in range(4):
        p = m.bone(f"grit_{i}", DROP)
        p.lathe((DROP[0] + (i - 1.5) * 0.04, DROP[1], DROP[2] - 0.03), [(0, -0.04), (0.035, -0.015), (0.03, 0.02), (0, 0.04)], 5, "concrete", cap=False)
    # ---- стрелка
    n = m.bone("needle", (0.95, -1.43, 0.62))
    n.box((0.948, -1.438, 0.615), (1.13, -1.43, 0.626), "eye")


def pose(t):
    p = {"drum": {"rot": (360 * t, 0, 0)}, "pinion": {"rot": (-360 * (28 / 8) * t, 0, 0)},
         "needle": {"rot": (0, 25 * math.sin(2 * math.pi * 2 * t) - 15, 0)}}
    fall = DROP[2] - 0.03 - BOX_Z - 0.17
    for i in range(4):
        u = (t * 3 + i / 4) % 1
        p[f"grit_{i}"] = {"pos": (0, 0, -fall * u * u), "scale": (1, 1, 1) if u < 0.95 else (0, 0, 0)}
    return p


m = Machine("cement_mill")
frame(m)
moving(m)
sc, tris = m.build("WB_CementMill")
light_scene(sc, int(LOOP * 24))
auto_animate(m.objects, sc, pose, LOOP)
tracks = lambda: auto_tracks(pose, LOOP, STEPS)
print("костей:", len(m.objects), "треугольников:", tris)
