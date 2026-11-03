"""
Пороховой цех (powder_works): 5×3×4. Линия под бронещитами: нитрационная ванна с мешалкой → лента с лотками → пресс-формовщик
→ бункер готового заряда. Сверху лёгкая вышибная крыша и красный проблесковый маяк: цех взрывоопасен.
"""
import math
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "kit.py"), encoding="utf-8").read())

LOOP, STEPS = 4.0, 64
BELT_Z = 0.86          # верх ленты
BELT_Y = -0.45
X0, X1 = -1.0, 1.75    # ход лотков
TRAYS = 4
VAT = (-1.65, -0.25)
PRESS_X = 0.7


def frame(m):
    f = m.bone("frame")
    f.plinth(-2.48, -1.48, 2.48, 1.48)
    # ---- бронещит сзади с контрфорсами
    f.box((-2.4, 0.75, 0.3), (2.4, 1.2, 2.95), "hull", bevel=0.05)
    f.box((-2.42, 0.73, 2.55), (2.42, 1.22, 2.63), "hazard")
    f.box((-2.42, 0.73, 0.82), (2.42, 1.22, 0.9), "brass")
    for x in (-2.0, -0.7, 0.7, 2.0):
        f.wedge((x - 0.13, 1.2, 0.3), (x + 0.13, 1.46), (x - 0.13, 1.2, 2.5), (x + 0.13, 1.25), "dark")
    for i in range(9):
        x = -2.2 + i * 0.55
        for z in (1.2, 2.25):
            f.bolt((x, 0.73, z), "Y", 0.035, -0.02, "steel")
    # ---- крыша-вышибной щит на стойках, между ними видна линия
    for x in (-2.32, -0.02, 2.32):
        f.box((x - 0.08, -1.3, 0.3), (x + 0.08, -1.14, 3.0), "dark", bevel=0.015)
        f.wedge((x - 0.06, -1.14, 2.5), (x + 0.06, 0.75), (x - 0.06, -1.14, 3.0), (x + 0.06, 0.75), "dark")
    f.box((-2.45, -1.38, 3.0), (2.45, 1.25, 3.12), "hull", bevel=0.03)
    f.box((-2.47, -1.4, 2.92), (2.47, -1.26, 3.0), "hazard")
    for x in (-1.6, -0.5, 0.6, 1.7):
        f.box((x - 0.42, -1.05, 3.12), (x + 0.42, 1.05, 3.2), "rust", bevel=0.015)
    # ---- нитрационная ванна слева
    x, y = VAT
    f.lathe((x, y, 0.3), [(0.72, 0), (0.76, 0.76), (0.82, 0.8), (0.82, 0.86), (0.68, 0.86), (0.68, 0.68)], 16, "dark", base=False)
    f.ring((x, y, 0.56), 0.73, 0.82, 0.08, 16, "brass", "Z")
    f.lathe((x, y, 0.98), [(0.68, 0), (0.68, 0.01)], 16, "sulfur", base=False)
    f.box((x - 0.08, y + 0.5, 0.3), (x + 0.08, y + 0.68, 2.45), "dark")
    f.box((x - 0.1, y - 0.1, 2.25), (x + 0.1, y + 0.68, 2.42), "dark", bevel=0.015)
    f.lathe((x, y, 2.42), [(0.18, 0), (0.18, 0.28), (0.1, 0.34)], 10, "rust", base=False)
    # кислотные баки у щита и подача в ванну
    for bx, band in ((-2.08, "acid"), (-1.28, "sulfur")):
        f.tank((bx, 0.42, 1.5), 0.26, 0.72, 10, "steel", (0.3, 0.7), band_mat=band)
        f.pipe([(bx, 0.42, 1.5), (bx, 0.2, 1.3), (x + (bx - x) * 0.25, y + 0.2, 1.18)], 0.035, 6, "rust")
        f.box((bx - 0.22, 0.45, 0.3), (bx + 0.22, 0.7, 1.5), "dark", bevel=0.015)
    # ---- станина ленты
    f.box((X0 - 0.18, BELT_Y - 0.38, 0.3), (X1 + 0.3, BELT_Y + 0.38, BELT_Z - 0.2), "hull", bevel=0.025)
    f.box((X0 - 0.18, BELT_Y - 0.4, BELT_Z - 0.1), (X1 + 0.3, BELT_Y - 0.34, BELT_Z + 0.04), "brass")
    f.box((X0 - 0.18, BELT_Y + 0.34, BELT_Z - 0.1), (X1 + 0.3, BELT_Y + 0.4, BELT_Z + 0.04), "brass")
    f.box((X0 - 0.14, BELT_Y - 0.33, BELT_Z - 0.2), (X1 + 0.26, BELT_Y + 0.33, BELT_Z - 0.01), "rubber")
    # ---- пресс-формовщик: портал над лентой
    for s in (-1, 1):
        for c in (-1, 1):     # четыре стойки: шток и лоток под ним должны быть видны спереди
            px = PRESS_X + c * 0.36
            f.box((px - 0.07, BELT_Y + s * 0.52 - 0.07, 0.3), (px + 0.07, BELT_Y + s * 0.52 + 0.07, 2.38), "dark", bevel=0.015)
    f.box((PRESS_X - 0.48, BELT_Y - 0.62, 2.0), (PRESS_X + 0.48, BELT_Y + 0.62, 2.48), "hull", bevel=0.03)
    f.box((PRESS_X - 0.5, BELT_Y - 0.64, 2.2), (PRESS_X + 0.5, BELT_Y + 0.64, 2.26), "brass")
    f.lathe((PRESS_X, BELT_Y, 2.48), [(0.2, 0), (0.2, 0.3), (0.12, 0.36)], 10, "steel", base=False)
    # ---- бункер готового заряда справа
    f.loft([(0.3, 0.32, 0.32, -0.45), (0.86, 0.32, 0.32, -0.45), (1.28, 0.42, 0.42, -0.45)], "hull") if False else None
    f.box((1.78, BELT_Y - 0.42, 0.3), (2.42, BELT_Y + 0.42, 0.82), "dark", bevel=0.02)
    f.box((1.84, BELT_Y - 0.36, 0.76), (2.36, BELT_Y + 0.36, 0.83), "bone")
    f.skull(2.1, BELT_Y - 0.28, 1.25, 0.34, augmetic=False) if False else None
    # ---- стеллаж с зарядами: связки у щита
    for i in range(4):
        cx = 1.75 + (i % 2) * 0.32
        z = 0.42 + (i // 2) * 0.24
        f.lathe((cx - 0.12, 0.5, z), [(0.11, -0.2), (0.11, 0.2)], 8, "brass", "X")
    # ---- пульт и череп в середине, печати
    f.box((-0.62, 0.52, 0.9), (0.42, 0.75, 1.92), "hull", bevel=0.02)
    f.box((-0.54, 0.5, 1.02), (0.34, 0.52, 1.72), "screen")
    f.skull(-0.1, 0.72, 2.25, 0.42)
    f.seal((-2.05, 0.73, 2.2), "Y", -1)
    f.seal((1.55, 0.73, 2.2), "Y", -1)
    # ---- маяк: основание
    f.lathe((0, -0.6, 3.12), [(0.17, 0), (0.17, 0.12), (0.09, 0.16)], 10, "dark", base=False)
    # ---- сброс паров
    f.pipe([(-1.65, 0.5, 2.7), (-1.65, 0.6, 3.05), (-1.65, 0.6, 3.72)], 0.09, 8, "rust")
    f.lathe((-1.65, 0.6, 3.72), [(0.09, 0), (0.15, 0.06), (0.15, 0.24), (0.06, 0.28)], 8, "dark", base=False)


def moving(m):
    # ---- мешалка ванны: кривошип и лопасть
    x, y = VAT
    st = m.bone("stir", (x, y, 2.3))
    st.lathe((x, y, 1.0), [(0.04, 0), (0.04, 1.3)], 6, "steel", base=False)
    for k in range(3):
        a = k * 2 * math.pi / 3
        st.beam((x, y, 1.12), (x + 0.48 * math.cos(a), y + 0.48 * math.sin(a), 1.12), 0.2, 0.03, "brass")
    # ---- лотки с порошком на ленте
    for i in range(TRAYS):
        t = m.bone(f"tray_{i}", (X0, BELT_Y, BELT_Z))
        t.box((X0 - 0.22, BELT_Y - 0.25, BELT_Z), (X0 + 0.22, BELT_Y + 0.25, BELT_Z + 0.07), "rust", bevel=0.012)
        t.box((X0 - 0.17, BELT_Y - 0.2, BELT_Z + 0.07), (X0 + 0.17, BELT_Y + 0.2, BELT_Z + 0.09), "bone")
    # ---- шток и матрица пресса
    r = m.bone("ram", (PRESS_X, BELT_Y, 2.0))
    r.lathe((PRESS_X, BELT_Y, 1.25), [(0.07, 0), (0.07, 0.82)], 8, "steel", base=False)
    r.box((PRESS_X - 0.26, BELT_Y - 0.28, 1.12), (PRESS_X + 0.26, BELT_Y + 0.28, 1.28), "dark", bevel=0.02)
    # ---- красный маяк и шторка, бегущая вокруг него
    b = m.bone("beacon", (0, -0.6, 3.36))
    b.lathe((0, -0.6, 3.28), [(0.09, 0), (0.09, 0.14), (0.04, 0.2)], 8, "eye", base=False)
    b.beam((0, -0.73, 3.28), (0, -0.73, 3.42), 0.06, 0.05, "steel")
    b.beam((0, -0.47, 3.28), (0, -0.47, 3.42), 0.06, 0.05, "steel")


def pose(t):
    a = 2 * math.pi * t
    p = {"stir": {"rot": (0, 0, 360 * t)}, "beacon": {"rot": (0, 0, 360 * 4 * t)}}
    # лоток идёт с шагом: стоит под прессом, пока пресс бьёт
    for i in range(TRAYS):
        u = (t * 2 + i / TRAYS) % 1
        d = u * (X1 - X0)
        vis = 0 if u > 0.97 else 1
        p[f"tray_{i}"] = {"pos": (d, 0, 0), "scale": (vis, vis, vis)}
    k = (t * 4) % 1
    down = (1 - (1 - min(1, k / 0.22)) ** 2) if k < 0.22 else 1 - min(1, (k - 0.22) / 0.5)
    p["ram"] = {"pos": (0, 0, -0.27 * max(0, down))}
    return p


m = Machine("powder_works")
frame(m)
moving(m)
sc, tris = m.build("WB_PowderWorks")
light_scene(sc, int(LOOP * 24))
auto_animate(m.objects, sc, pose, LOOP)
tracks = lambda: auto_tracks(pose, LOOP, STEPS)
print("костей:", len(m.objects), "треугольников:", tris)
