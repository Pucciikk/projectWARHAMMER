"""
Кузня Механикус (mechanicus_forge): 5×5×6, сердце главы 2. Открытый спереди зал под стальной кровлей: наковальня посредине, два молота на
сервоплечах бьют попеременно, сзади горн с огнём и мехами, огромная шестерня Омниссии с черепом и знамя; из кровли две трубы.
"""
import math
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "kit.py"), encoding="utf-8").read())

LOOP, STEPS = 2.0, 48
W = 2.25
ROOF = 3.95
ANVIL = (0, 0.2)     # x, y наковальни
HAMMER_Z = 2.15


def frame(m):
    f = m.bone("frame")
    f.plinth(-2.48, -2.48, 2.48, 2.48)
    f.box((-W, -W, 0.3), (W, W, 0.38), "dark", bevel=0.015)
    for k in range(3):
        f.box((-1.1 - k * 0.1, -2.48 + k * 0.08, 0.3), (1.1 + k * 0.1, -2.3 + k * 0.08, 0.38 - k * 0.02), "hull")
    # ---- колонны с контрфорсами, кровля ступенями
    for sx in (-1, 1):
        for y in (-W + 0.1, -0.5, 0.9, W - 0.1):
            f.box((sx * W - 0.15, y - 0.15, 0.38), (sx * W + 0.15, y + 0.15, ROOF), "hull", bevel=0.035)
            for z in (1.4, 2.6):
                f.box((sx * W - 0.18, y - 0.18, z), (sx * W + 0.18, y + 0.18, z + 0.08), "brass", bevel=0.012)
            a, b = sorted((sx * (W + 0.1), sx * 2.46))
            c, d = sorted((sx * (W + 0.1), sx * (W + 0.14)))
            f.wedge((a, y - 0.09, 0.3), (b, y + 0.09), (c, y - 0.05, 2.2), (d, y + 0.05), "dark")
        f.box((sx * W - 0.08, -0.35, 0.38), (sx * W + 0.08, 0.75, 2.2), "hull")
        f.box((sx * W - 0.08, 1.05, 0.38), (sx * W + 0.08, W - 0.2, 2.8), "hull")
    f.box((-W, W - 0.1, 0.38), (W, W + 0.05, ROOF), "hull")
    f.box((-2.46, -2.46, ROOF), (2.46, 2.46, ROOF + 0.18), "dark", bevel=0.035)
    f.box((-2.48, -2.48, ROOF + 0.07), (2.48, 2.48, ROOF + 0.11), "brass")
    f.loft([(ROOF + 0.18, 2.3, 2.3, 0), (ROOF + 0.72, 1.2, 1.2, 0)], "rust")
    f.box((-1.25, -1.25, ROOF + 0.72), (1.25, 1.25, ROOF + 0.82), "dark", bevel=0.02)
    # ---- трубы
    for x in (-0.75, 0.75):
        f.lathe((x, 0.9, ROOF + 0.82), [(0.28, 0), (0.28, 0.1), (0.18, 0.18), (0.18, 0.75), (0.24, 0.8), (0.24, 0.9), (0.17, 0.92)], 10, "rust", base=False)
        f.ring((x, 0.9, ROOF + 1.2), 0.17, 0.22, 0.05, 10, "brass", "Z")
    # ---- горн у задней стены: кирпич, жаровня, вытяжка
    f.box((-1.55, 1.12, 0.38), (1.55, 2.14, 1.28), "brick", bevel=0.06)
    f.box((-1.58, 1.08, 1.28), (1.58, 2.18, 1.36), "dark", bevel=0.02)
    f.box((-1.3, 1.1, 0.48), (1.3, 1.12, 1.12), "dark")
    for x in (-1.05, -0.35, 0.35, 1.05):
        f.box((x - 0.26, 1.09, 0.55), (x + 0.26, 1.11, 1.05), "fire")
        f.box((x - 0.3, 1.075, 0.78), (x + 0.3, 1.1, 0.82), "dark")
    f.box((-1.2, 1.3, 1.36), (1.2, 2.0, 1.4), "fire")
    f.loft([(2.4, 1.3, 0.52, 1.62), (3.1, 0.68, 0.36, 1.82), (3.1, 0.6, 0.3, 1.82), (2.42, 1.2, 0.44, 1.62)], "rust")
    f.lathe((0, 1.84, 3.1), [(0.32, 0), (0.32, ROOF - 3.1)], 10, "dark", base=False)
    # ---- знак: шестерня Омниссии, череп, знамя по бокам
    f.gear((0, W - 0.14, 2.52), 0.72, 0.92, 0.07, 14, "brass", "Y")
    f.ring((0, W - 0.18, 2.52), 0.28, 0.62, 0.05, 14, "dark", "Y")
    f.skull(0, W - 0.2, 2.52, 0.9)
    for s in (-1, 1):
        f.box((s * 1.55 - 0.3, W - 0.14, 1.4), (s * 1.55 + 0.3, W - 0.1, 3.3), "red")
        f.lathe((s * 1.55 - 0.32, W - 0.13, 3.3), [(0.025, 0), (0.025, 0.64)], 6, "brass", "X")
    # ---- наковальня на постаменте
    ax, ay = ANVIL
    f.lathe((ax, ay, 0.38), [(0.52, 0), (0.52, 0.1), (0.34, 0.2), (0.26, 0.78), (0.42, 0.86)], 12, "dark", base=False)
    f.box((ax - 0.62, ay - 0.26, 1.24), (ax + 0.62, ay + 0.26, 1.42), "steel", bevel=0.03)
    f.wedge((ax + 0.62, ay - 0.2, 1.26), (ax + 0.95, ay + 0.2), (ax + 0.62, ay - 0.16, 1.42), (ax + 0.74, ay + 0.16), "steel")
    f.box((ax - 0.74, ay - 0.2, 1.26), (ax - 0.62, ay + 0.2, 1.42), "hull")
    f.box((ax - 0.3, ay - 0.13, 1.42), (ax + 0.3, ay + 0.13, 1.47), "fire")     # раскалённая заготовка
    # ---- стойки сервоплеч и инструментальные стены
    for s in (-1, 1):
        f.lathe((s * 1.5, ANVIL[1], 0.38), [(0.34, 0), (0.34, 0.12), (0.2, 0.22), (0.16, HAMMER_Z - 0.55)], 10, "hull", base=False)
        f.ring((s * 1.5, ANVIL[1], 1.2), 0.15, 0.22, 0.07, 10, "brass", "Z")
    for x in (-1.92, 1.92):
        for k in range(4):
            f.box((x - 0.03, -1.6 + k * 0.3, 2.4), (x + 0.03, -1.52 + k * 0.3, 2.9), "steel")
    f.box((-2.2, -2.15, 0.38), (-1.55, -1.5, 0.9), "rust", bevel=0.03)
    f.box((1.55, -2.15, 0.38), (2.2, -1.5, 1.0), "dark", bevel=0.03)
    f.box((1.6, -2.16, 0.5), (2.15, -2.15, 0.92), "screen")
    f.seal((-1.0, 1.08, 1.2), "Y", -1)
    f.seal((1.0, 1.08, 1.2), "Y", -1)


def moving(m):
    # ---- два молота: плечо от стойки к наковальне, боёк на конце
    for i, s in enumerate((-1, 1)):
        h = m.bone(f"hammer_{i + 1}", (s * 1.5, ANVIL[1], HAMMER_Z))
        h.box((s * 1.5 - 0.14, ANVIL[1] - 0.14, HAMMER_Z - 0.14), (s * 1.5 + 0.14, ANVIL[1] + 0.14, HAMMER_Z + 0.14), "dark", bevel=0.03)
        h.lathe((s * 1.5, ANVIL[1] - 0.16, HAMMER_Z), [(0.1, 0), (0.1, 0.32)], 8, "brass", "Y")
        h.beam((s * 1.5, ANVIL[1], HAMMER_Z), (s * 0.22, ANVIL[1], HAMMER_Z - 0.1), 0.1, 0.14, "hull", 0.015)
        h.beam((s * 1.0, ANVIL[1], HAMMER_Z + 0.08), (s * 0.34, ANVIL[1], HAMMER_Z + 0.02), 0.05, 0.05, "steel")
        h.box((s * 0.22 - 0.16, ANVIL[1] - 0.17, HAMMER_Z - 0.34), (s * 0.22 + 0.16, ANVIL[1] + 0.17, HAMMER_Z + 0.0), "dark", bevel=0.025)
        h.box((s * 0.22 - 0.18, ANVIL[1] - 0.19, HAMMER_Z - 0.42), (s * 0.22 + 0.18, ANVIL[1] + 0.19, HAMMER_Z - 0.34), "steel", bevel=0.012)
    # ---- мехи горна
    b = m.bone("bellows", (0, 2.12, 1.42))
    b.plate([(2.12, 1.42), (2.12, 1.5), (1.45, 1.6), (1.45, 1.5)], -0.7, 0.7, "rust")
    b.plate([(2.12, 1.38), (2.12, 1.42), (1.45, 1.5), (1.45, 1.4)], -0.66, 0.66, "rubber")
    # ---- вращающаяся большая шестерня-привод сбоку за колонной и искры у наковальни
    g = m.bone("drive_gear", (2.28, -0.05, 2.9))
    g.gear((2.28, -0.05, 2.9), 0.36, 0.48, 0.1, 12, "brass", "X")
    g.lathe((2.34, -0.05, 2.9), [(0.1, 0), (0.06, 0.06)], 6, "dark", "X", base=False)
    sp = m.bone("sparks", (0, ANVIL[1], 1.5))
    for k in range(6):
        a = k * 1.05
        sp.beam((0, ANVIL[1], 1.5), (0.34 * math.cos(a), ANVIL[1] + 0.3 * math.sin(a), 1.72 + 0.08 * (k % 2)), 0.018, 0.018, "fire")
    # ---- факелы труб
    fl = m.bone("stack_flame", (0, 0.9, ROOF + 1.76))
    for x in (-0.75, 0.75):
        fl.lathe((x, 0.9, ROOF + 1.76), [(0.14, 0), (0.1, 0.16), (0.02, 0.4)], 6, "fire", base=False)


def strike(u):
    """Удар: быстрое падение, отскок, медленный подъём. u от 0 до 1."""
    if u < 0.2:
        return 1 - (u / 0.2) ** 2
    return min(1.0, (u - 0.2) / 0.8) ** 0.7


def pose(t):
    u1, u2 = t % 1, (t + 0.5) % 1
    a = 2 * math.pi * t
    # молоты висят на плечах: поворот вокруг Y приводит боёк к заготовке
    h1, h2 = strike(u1), strike(u2)
    hit = 1 if u1 < 0.12 or u2 < 0.12 else 0
    return {
        "hammer_1": {"rot": (0, 26 * h1 - 4, 0)},
        "hammer_2": {"rot": (0, -(26 * h2 - 4), 0)},
        "bellows": {"rot": (7 * math.sin(a), 0, 0)},
        "drive_gear": {"rot": (360 * t, 0, 0)},
        "sparks": {"scale": (hit, hit, hit)},
        "stack_flame": {"scale": (1, 1, 1 + 0.3 * math.sin(4 * a) + 0.14 * math.sin(11 * a))},
    }


m = Machine("mechanicus_forge")
frame(m)
moving(m)
sc, tris = m.build("WB_MechanicusForge")
light_scene(sc, int(LOOP * 24))
auto_animate(m.objects, sc, pose, LOOP)
tracks = lambda: auto_tracks(pose, LOOP, STEPS)
print("костей:", len(m.objects), "треугольников:", tris)
