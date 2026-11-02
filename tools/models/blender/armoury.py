"""
Оружейная мастерская (armoury): 5×5×4. Открытый спереди цех: кран-балка идёт по рельсам и опускает захват к поворотному столу
со стволом лазгана, сварочный манипулятор варит и искрит; у стен стойки с готовыми лазганами, знамя Механикус сзади.
"""
import math
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "kit.py"), encoding="utf-8").read())

LOOP, STEPS = 6.0, 48
W = 2.25
RAIL_Z = 3.3


def lasgun(b, x, y, z, s=1.0, axis="X"):
    """Лазган вдоль X или Z: приклад, корпус, ствол, магазин."""
    if axis == "X":
        b.box((x - 0.62 * s, y - 0.035, z - 0.05), (x - 0.25 * s, y + 0.035, z + 0.05), "dark")
        b.box((x - 0.25 * s, y - 0.05, z - 0.08), (x + 0.2 * s, y + 0.05, z + 0.08), "hull")
        b.box((x + 0.2 * s, y - 0.025, z - 0.025), (x + 0.68 * s, y + 0.025, z + 0.025), "steel")
        b.box((x - 0.05 * s, y - 0.04, z - 0.2), (x + 0.1 * s, y + 0.04, z - 0.08), "rust")
    else:
        b.box((x - 0.035, y - 0.05, z - 0.62 * s), (x + 0.035, y + 0.05, z - 0.25 * s), "dark")
        b.box((x - 0.05, y - 0.08, z - 0.25 * s), (x + 0.05, y + 0.08, z + 0.2 * s), "hull")
        b.box((x - 0.025, y - 0.025, z + 0.2 * s), (x + 0.025, y + 0.025, z + 0.68 * s), "steel")
        b.box((x - 0.04, y + 0.08, z - 0.05 * s), (x + 0.04, y + 0.2, z + 0.1 * s), "rust")


def frame(m):
    f = m.bone("frame")
    f.plinth(-2.48, -2.48, 2.48, 2.48)
    f.box((-W, -W, 0.3), (W, W, 0.38), "dark", bevel=0.015)
    # ---- колонны, рельсы крана, задняя стена, боковые стенки
    for sx in (-1, 1):
        for y in (-W + 0.1, 0, W - 0.1):
            f.box((sx * W - 0.14, y - 0.14, 0.38), (sx * W + 0.14, y + 0.14, RAIL_Z), "hull", bevel=0.03)
            f.lathe((sx * W, y, RAIL_Z + 0.16), [(0.11, 0), (0.02, 0.38)], 4, "dark", phase=math.pi / 4, base=False)
        f.box((sx * W - 0.11, -W, RAIL_Z), (sx * W + 0.11, W, RAIL_Z + 0.2), "dark", bevel=0.02)
        f.box((sx * W - 0.04, -W, RAIL_Z + 0.2), (sx * W + 0.04, W, RAIL_Z + 0.24), "steel")
        # стенка с лазганами на стойке
        f.box((sx * W - 0.05, -0.1, 0.38), (sx * W + 0.05, W - 0.2, 2.45), "hull")
        for k in range(4):
            z = 0.85 + k * 0.42
            f.box((sx * (W - 0.1) - 0.04, 0.05, z - 0.03), (sx * (W - 0.1) + 0.04, W - 0.35, z + 0.03), "dark")
            for i in range(3):
                lasgun(f, sx * (W - 0.16), 0.3 + i * 0.55, z + 0.32, 0.42, "Z")
    f.box((-W, W - 0.1, 0.38), (W, W + 0.05, 2.95), "hull")
    f.box((-W, W - 0.13, 2.1), (W, W - 0.08, 2.2), "brass")
    # знамя с шестернёй и черепом
    f.box((-0.62, W - 0.16, 1.1), (0.62, W - 0.12, 2.75), "red")
    f.gear((0, W - 0.17, 2.05), 0.34, 0.46, 0.04, 12, "brass", "Y")
    f.skull(0, W - 0.2, 2.06, 0.5)
    f.lathe((-0.62, W - 0.14, 1.1), [(0.03, 0), (0.03, 1.24)], 6, "brass", "X")
    # верстаки, тиски и лампы вдоль задней стены
    for sx in (-1, 1):
        f.box((sx * 1.32 - 0.55, 1.28, 0.38), (sx * 1.32 + 0.55, 2.05, 0.98), "dark", bevel=0.03)
        f.box((sx * 1.32 - 0.6, 1.24, 0.98), (sx * 1.32 + 0.6, 2.08, 1.04), "steel", bevel=0.012)
        f.box((sx * 1.32 - 0.15, 1.42, 1.04), (sx * 1.32 + 0.15, 1.7, 1.2), "hull", bevel=0.02)
        f.lathe((sx * 1.32, 1.56, 1.04), [(0.05, 0), (0.05, 0.3)], 6, "steel", base=False)
        lasgun(f, sx * 1.1, 1.92, 1.1, 0.5)
        f.lathe((sx * 1.05, W - 0.2, 2.5), [(0.03, 0), (0.03, 0.38)], 6, "steel", "Y", base=False)
        f.lathe((sx * 1.05, W - 0.48, 2.42), [(0.15, 0), (0.05, 0.16)], 8, "dark", base=False)
        f.lathe((sx * 1.05, W - 0.48, 2.4), [(0.11, 0), (0.11, 0.02)], 8, "stain_gold", base=False)
    # поворотный стол: неподвижное основание и его жаровня с огнём
    f.lathe((0, 0.0, 0.38), [(0.72, 0), (0.72, 0.16), (0.55, 0.22), (0.55, 0.42)], 16, "hull", base=False)
    f.ring((0, 0, 0.56), 0.56, 0.7, 0.05, 16, "brass", "Z")
    # основание манипулятора
    f.lathe((1.18, -0.7, 0.38), [(0.3, 0), (0.3, 0.1), (0.18, 0.2), (0.14, 0.72)], 10, "dark", base=False)
    f.pipe([(1.18, -0.7, 0.55), (1.6, -1.1, 0.5), (2.1, -1.4, 0.45)], 0.04, 6, "rubber")
    f.box((1.78, -1.75, 0.38), (2.2, -1.2, 1.15), "hull", bevel=0.03)
    f.box((1.76, -1.72, 0.55), (1.79, -1.23, 1.0), "screen")
    f.seal((-1.75, 1.22, 0.85), "Y", -1)
    f.seal((-W - 0.04, -1.2, 2.0), "Y", -1) if False else None
    # стеллаж с компонентами спереди-слева
    f.box((-2.2, -1.8, 0.38), (-1.52, -1.1, 0.42), "dark")
    for x, y, h in ((-2.02, -1.62, 0.5), (-1.72, -1.62, 0.5), (-2.02, -1.3, 0.5), (-1.72, -1.3, 0.36)):
        f.box((x - 0.13, y - 0.13, 0.42), (x + 0.13, y + 0.13, 0.42 + h), "rust", bevel=0.012)
        f.box((x - 0.14, y - 0.14, 0.42 + h - 0.06), (x + 0.14, y + 0.14, 0.42 + h - 0.02), "brass")


def moving(m):
    # ---- кран-балка: мост по рельсам, тележка с тросом и захватом — отдельные кости
    g = m.bone("gantry", (0, 0, RAIL_Z + 0.3))
    g.box((-W + 0.05, -0.17, RAIL_Z + 0.26), (W - 0.05, 0.17, RAIL_Z + 0.48), "dark", bevel=0.025)
    g.box((-W + 0.05, -0.19, RAIL_Z + 0.35), (W - 0.05, 0.19, RAIL_Z + 0.39), "hazard")
    for sx in (-1, 1):
        g.box((sx * W - 0.16, -0.25, RAIL_Z + 0.2), (sx * W + 0.16, 0.25, RAIL_Z + 0.32), "hull", bevel=0.02)
    t = m.bone("trolley", (0, 0, RAIL_Z))
    t.box((-0.22, -0.26, RAIL_Z + 0.12), (0.22, 0.26, RAIL_Z + 0.27), "brass", bevel=0.02)
    t.lathe((0, 0, RAIL_Z - 0.45), [(0.04, 0), (0.04, 0.6)], 6, "steel", base=False)
    t.box((-0.16, -0.16, RAIL_Z - 0.6), (0.16, 0.16, RAIL_Z - 0.45), "dark", bevel=0.02)
    for s in (-1, 1):
        t.beam((s * 0.14, 0, RAIL_Z - 0.6), (s * 0.08, 0, RAIL_Z - 0.95), 0.04, 0.09, "steel")
    # ---- стол с лазганом в сборке
    tb = m.bone("table", (0, 0, 0.8))
    tb.lathe((0, 0, 0.8), [(0.5, 0), (0.5, 0.05)], 14, "steel", base=False)
    for k in range(4):
        a = k * math.pi / 2
        tb.box((0.34 * math.cos(a) - 0.05, 0.34 * math.sin(a) - 0.05, 0.85), (0.34 * math.cos(a) + 0.05, 0.34 * math.sin(a) + 0.05, 0.92), "dark")
    lasgun(tb, 0, 0, 1.02, 0.72)
    # ---- сварочный манипулятор: качается над столом, на конце искра
    a = m.bone("welder", (1.18, -0.7, 1.1))
    a.box((1.08, -0.8, 1.0), (1.28, -0.6, 1.22), "hull", bevel=0.02)
    a.beam((1.18, -0.7, 1.12), (0.68, -0.42, 1.55), 0.08, 0.08, "steel")
    a.beam((0.68, -0.42, 1.55), (0.35, -0.2, 1.2), 0.05, 0.05, "brass")
    a.lathe((0.34, -0.19, 1.1), [(0.012, 0), (0.04, 0.1)], 6, "dark", base=False)
    a.lathe((0.34, -0.19, 1.04), [(0.045, 0), (0.008, 0.07)], 5, "screen", base=False)
    # ---- искры: мерцающее пятно под соплом
    s = m.bone("sparkle", (0.34, -0.19, 1.04))
    for i in range(5):
        an = i * 1.26
        s.beam((0.34, -0.19, 1.04), (0.34 + 0.16 * math.cos(an), -0.19 + 0.16 * math.sin(an), 1.14 + 0.04 * (i % 2)), 0.012, 0.012, "fire")


def pose(t):
    a = 2 * math.pi * t
    gantry = 0.9 * math.sin(a)
    trolley = -1.0 + 2.0 * (t * 2 if t < 0.5 else 2 - t * 2)
    drop = -0.32 * max(0, math.sin(2 * a))
    weld = 1 if math.sin(9 * a) * math.sin(a) > 0.0 else 0
    return {
        "gantry": {"pos": (0, gantry, 0)},
        "trolley": {"pos": (0.7 * trolley, gantry, drop)},
        "table": {"rot": (0, 0, -360 * t)},
        "welder": {"rot": (0, 0, -12 * math.sin(2 * a))},
        "sparkle": {"scale": (weld, weld, weld)},
    }


m = Machine("armoury")
frame(m)
moving(m)
sc, tris = m.build("WB_Armoury")
light_scene(sc, int(LOOP * 24))
auto_animate(m.objects, sc, pose, LOOP)
tracks = lambda: auto_tracks(pose, LOOP, STEPS)
print("костей:", len(m.objects), "треугольников:", tris)
