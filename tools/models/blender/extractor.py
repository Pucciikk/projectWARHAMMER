"""
Прометиевый экстрактор (pumpjack в цепочке): исполинская качалка 7×13 блоков, высота около 12.
Ядро в середине переднего ряда, начало координат — его центр, вглубь +Y. Кинематика: кривошип → шатун → коромысло → шток.
"""
import math
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "kit.py"), encoding="utf-8").read())

PY, PD = 8.25, 6.0            # ось коромысла: высота и глубина
TAIL, HEAD = 4.375, 4.5       # плечи назад и вперёд
CY, CD, CR = 3.125, 10.375, 0.875  # ось кривошипа и радиус
ROD = PY - CY
WELL = PD - HEAD              # глубина устья
LOOP = 4.0
ROD_X = 2.5


def frame(m):
    f = m.bone("frame")
    # ---- плита
    f.box((-3.5, -0.5, 0), (3.5, 12.5, 0.5), "dark", bevel=0.07)
    f.box((-3.25, -0.25, 0.5), (3.25, 12.25, 0.75), "hull", bevel=0.04)
    for a, b in (((-3.25, -0.25), (3.25, 0.0)), ((-3.25, 12.0), (3.25, 12.25)), ((-3.25, 0), (-3.0, 12)), ((3.0, 0), (3.25, 12))):
        f.box((a[0], a[1], 0.75), (b[0], b[1], 0.765), "hazard")
    for y in (0.2, 3.2, 6.2, 9.2, 12.0):
        for s in (-1, 1):
            f.lathe((s * 3.38, y, 0.5), [(0.09, 0), (0.09, 0.09), (0.05, 0.12)], 6, "steel", base=False)

    # ---- устье: фланцы, задвижки, манометр
    f.lathe((0, WELL, 0.75), [(1.05, 0), (1.05, 0.25), (0.8, 0.35), (0.8, 0.9), (1.0, 0.9), (1.0, 1.05), (0.75, 1.05), (0.75, 1.7),
                              (1.0, 1.7), (1.0, 1.85), (0.55, 1.85), (0.5, 2.4), (0.3, 2.6), (0.3, 3.0)], 16, "rust", base=False)
    for s in (-1, 1):
        for k in range(4):
            a = k * math.pi / 2 + math.pi / 4
            f.lathe((0.88 * math.cos(a), WELL + 0.88 * math.sin(a), 2.6), [(0.05, 0), (0.05, 0.06)], 6, "brass", base=False)
        f.pipe([(s * 0.75, WELL, 1.4), (s * 1.3, WELL, 1.4), (s * 1.65, WELL + 0.6, 1.4), (s * 1.65, 2.4, 1.4)], 0.14, 8, "rust")
        f.lathe((s * 1.25, WELL, 1.4), [(0.22, -0.1), (0.22, 0.1)], 8, "dark", "X")        # задвижка
        f.lathe((s * 1.25, WELL, 1.6), [(0.04, 0), (0.04, 0.42)], 6, "steel")
        f.ring((s * 1.25, WELL, 2.04), 0.16, 0.25, 0.05, 10, "red", "Z")
    f.lathe((0, WELL - 0.8, 1.45), [(0.22, 0), (0.24, -0.06), (0.2, -0.1)], 12, "brass", "Y", base=False)
    f.lathe((0, WELL - 0.9, 1.45), [(0.18, 0), (0.18, -0.006)], 12, "glass", "Y", base=False)

    # ---- баки сырого прометия
    for s in (-1, 1):
        x = s * 2.31
        f.tank((x, 3.5, 0.75), 1.0, 4.6, 16, "hull", (0.15, 0.5, 0.85))
        f.lathe((x, 3.5, 5.85), [(0.22, 0), (0.22, 0.3), (0.3, 0.3), (0.3, 0.38), (0.1, 0.42)], 8, "steel", base=False)
        f.box((x - 0.07, 2.43, 1.3), (x + 0.07, 2.47, 4.6), "dark")
        f.box((x - 0.035, 2.415, 1.45), (x + 0.035, 2.445, 4.45), "fire")                    # смотровая щель
        f.ladder(s * 3.34, 3.5, 0.75, 5.4)
        f.pipe([(x, 4.5, 2.0), (s * 2.6, 6.6, 1.2), (s * 2.3, 7.9, 1.2)], 0.1, 6, "rust")
        f.seal((x + s * 0.5, 2.63, 4.0), "Y", -1)

    # ---- А-образные башни, раскосы, ось
    for s in (-1, 1):
        x = s * 1.95
        top = (x, PD, PY - 0.2)
        for d in (-1, 1):
            base = (x, PD + d * 2.0, 0.75)
            f.beam(base, top, 0.42, 0.42, "hull", 0.04)
            f.box((x - 0.34, PD + d * 2.0 - 0.34, 0.75), (x + 0.34, PD + d * 2.0 + 0.34, 1.0), "dark", bevel=0.03)
            for z in (2.6, 4.4, 6.2):
                k = (z - 0.75) / (PY - 0.95)
                c = (x, PD + d * 2.0 * (1 - k), z)
                f.box((c[0] - 0.26, c[1] - 0.26, z - 0.05), (c[0] + 0.26, c[1] + 0.26, z + 0.05), "brass", bevel=0.012)
        # раскосы-иксы между ногами
        for z0, z1, w0, w1 in ((1.1, 3.6, 1.8, 1.2), (3.7, 6.1, 1.15, 0.55)):
            f.beam((x, PD - w0, z0), (x, PD + w1, z1), 0.12, 0.12, "dark")
            f.beam((x, PD + w0, z0), (x, PD - w1, z1), 0.12, 0.12, "dark")
        f.box((x - 0.5, PD - 0.62, PY - 0.75), (x + 0.5, PD + 0.62, PY - 0.2), "dark", bevel=0.05)
        f.lathe((x - 0.32, PD, PY), [(0.48, 0), (0.48, 0.64)], 12, "dark", "X")
        f.ring((x, PD, PY), 0.3, 0.55, 0.78, 12, "brass")
    f.lathe((-2.5, PD, PY), [(0.2, 0), (0.2, 5.0)], 10, "steel", "X")

    # ---- площадка обслуживания, перила, шестерня Омниссии
    f.box((-1.7, PD - 1.05, 4.7), (1.7, PD + 1.05, 4.9), "dark", bevel=0.03)
    for x in (-1.5, -0.5, 0.5, 1.5):
        for y in (PD - 0.95, PD + 0.95):
            f.box((x - 0.03, y - 0.03, 4.9), (x + 0.03, y + 0.03, 5.6), "steel")
    for y in (PD - 0.95, PD + 0.95):
        f.pipe([(-1.5, y, 5.6), (1.5, y, 5.6)], 0.04, 6, "hazard")
    f.gear((0, PD - 1.02, 5.3), 0.48, 0.62, 0.06, 12, "brass", "Y")
    f.ring((0, PD - 1.06, 5.3), 0.14, 0.34, 0.05, 10, "dark", "Y")
    f.ladder(0, PD - 1.15, 0.75, 4.7, 0.5)
    f.seal((0.95, PD - 1.0, 5.55), "Y", -1)

    # ---- привод: кожух, рёбра, цилиндры, пульт
    f.box((-2.55, 8.0, 0.75), (2.55, 11.85, 1.15), "dark", bevel=0.05)
    f.box((-2.4, 8.1, 1.15), (2.4, 11.75, 2.2), "hull", bevel=0.09)
    f.box((-1.95, 8.5, 2.2), (1.95, 11.3, 3.4), "rust", bevel=0.09)
    f.box((-2.0, 8.45, 2.65), (2.0, 11.35, 2.8), "brass", bevel=0.015)
    for k in range(7):
        y = 8.6 + k * 0.42
        for s in (-1, 1):
            f.box((s * 2.42 - 0.03, y, 1.3), (s * 2.42 + 0.03, y + 0.16, 2.05), "dark")
    f.box((-1.05, 8.03, 1.3), (1.05, 8.1, 2.05), "dark", bevel=0.015)
    f.box((-0.95, 8.0, 1.38), (0.95, 8.04, 1.97), "screen")
    for x in (-1.25, 0, 1.25):
        f.lathe((x, 9.3, 3.4), [(0.4, 0), (0.4, 0.12), (0.33, 0.16), (0.33, 0.85), (0.42, 0.88), (0.42, 1.02), (0.22, 1.08), (0.18, 1.2)], 12, "steel", base=False)
        f.ring((x, 9.3, 3.85), 0.32, 0.38, 0.06, 12, "brass", "Z")
        f.pipe([(x, 9.3, 4.5), (x, 9.3, 4.72), (x, 10.5, 4.72), (x * 1.1, 11.2, 3.2)], 0.055, 6, "rubber")

    # ---- дымовые трубы
    for s in (-1, 1):
        x = s * 1.75
        f.lathe((x, 11.875, 0.75), [(0.68, 0), (0.68, 0.3), (0.5, 0.45), (0.5, 7.2), (0.62, 7.26), (0.62, 7.4), (0.52, 7.46)], 12, "rust", base=False)
        for z in (2.5, 4.7, 6.9):
            f.ring((x, 11.875, z), 0.47, 0.57, 0.14, 12, "brass", "Z")
        f.lathe((x, 11.875, 8.15), [(0.6, 0), (0.72, 0.18), (0.66, 0.22)], 12, "dark", base=False)


def moving(m):
    # ---- кривошип с противовесами
    c = m.bone("crank", (0, CD, CY))
    c.lathe((-3.3, CD, CY), [(0.24, 0), (0.24, 6.6)], 12, "steel", "X")
    for s in (-1, 1):
        x = s * 2.9
        c.box((x - 0.14, CD - 0.42, CY - 0.42), (x + 0.14, CD + CR + 0.34, CY + 0.42), "dark", bevel=0.04)
        arc = [(CD - 0.25 + 0, CY + 0.3)]
        for k in range(9):
            a = math.radians(125 + k * 110 / 8)
            arc.append((CD + 2.0 * math.cos(a), CY + 2.0 * math.sin(a)))
        arc.append((CD - 0.25, CY - 0.3))
        c.plate(arc, x - 0.24, x + 0.24, "hull")
        band = [(CD + 2.02 * math.cos(math.radians(125 + k * 110 / 8)), CY + 2.02 * math.sin(math.radians(125 + k * 110 / 8))) for k in range(9)]
        band += [(CD + 1.82 * math.cos(math.radians(235 - k * 110 / 8)), CY + 1.82 * math.sin(math.radians(235 - k * 110 / 8))) for k in range(9)]
        c.plate(band, x - 0.27, x + 0.27, "dark")
        c.plate(band, x - 0.3, x - 0.26, "brass")
        c.plate(band, x + 0.26, x + 0.3, "brass")
        c.lathe((min(x, s * ROD_X), CD + CR, CY), [(0.14, 0), (0.14, abs(x - s * ROD_X) + 0.1)], 8, "steel", "X")

    # ---- шатуны
    for i, s in enumerate((-1, 1)):
        x = s * ROD_X
        y = PD + TAIL
        r = m.bone(f"rod_{i + 1}", (x, y, PY))
        r.ring((x, y, PY), 0.16, 0.33, 0.22, 12, "dark")
        r.ring((x, y, PY - ROD), 0.13, 0.3, 0.22, 12, "dark")
        r.box((x - 0.08, y - 0.14, PY - ROD + 0.26), (x + 0.08, y + 0.14, PY - 0.28), "steel", bevel=0.025)
        r.box((x - 0.12, y - 0.2, PY - ROD / 2 - 0.1), (x + 0.12, y + 0.2, PY - ROD / 2 + 0.1), "brass", bevel=0.02)

    # ---- коромысло: двутавры, рёбра, траверса, головка
    b = m.bone("beam", (0, PD, PY))
    y0, y1 = PD - HEAD + 0.7, PD + TAIL + 0.42
    for s in (-1, 1):
        x = s * 0.55
        b.box((x - 0.09, y0, PY - 0.38), (x + 0.09, y1, PY + 0.38), "hull")
        b.box((x - 0.27, y0, PY + 0.38), (x + 0.27, y1, PY + 0.5), "dark", bevel=0.02)
        b.box((x - 0.27, y0, PY - 0.5), (x + 0.27, y1, PY - 0.38), "dark", bevel=0.02)
        b.box((x - 0.28, y0, PY + 0.5), (x + 0.28, y1, PY + 0.53), "brass")
        for k in range(14):
            b.bolt((x + 0.18, y0 + 0.3 + k * 0.56, PY + 0.53), "Z", 0.04, 0.03, "steel")
            b.bolt((x - 0.18, y0 + 0.3 + k * 0.56, PY + 0.53), "Z", 0.04, 0.03, "steel")
    y = y0 + 0.4
    while y < y1:
        if abs(y - PD) > 0.8:
            b.box((-0.46, y, PY - 0.3), (0.46, y + 0.12, PY + 0.3), "dark")
        y += 1.1
    b.lathe((-2.75, PD + TAIL, PY), [(0.2, 0), (0.2, 5.5)], 10, "steel", "X")
    b.box((-0.85, PD + TAIL - 0.4, PY - 0.55), (0.85, PD + TAIL + 0.4, PY + 0.55), "rust", bevel=0.06)
    b.box((-1.1, PD - 0.65, PY - 0.65), (1.1, PD + 0.65, PY + 0.65), "dark", bevel=0.09)
    # головка-дуга над скважиной
    arc, rim = [], []
    for k in range(9):
        a = math.radians(-24 + k * 6)
        arc.append((PD - HEAD * math.cos(a), PY + HEAD * math.sin(a)))
        rim.append((PD - (HEAD + 0.06) * math.cos(a), PY + (HEAD + 0.06) * math.sin(a)))
    back = [(arc[-1][0] + 1.0, arc[-1][1] - 0.2), (arc[-1][0] + 1.5, PY + 0.5), (arc[-1][0] + 1.5, PY - 0.5), (arc[0][0] + 1.0, arc[0][1] + 0.2)]
    b.plate(arc + back, -0.62, 0.62, "hull")
    b.plate(rim + list(reversed(arc)), -0.6, 0.6, "dark")
    inner = [(PD - (HEAD - 0.2) * math.cos(math.radians(-24 + k * 6)), PY + (HEAD - 0.2) * math.sin(math.radians(-24 + k * 6))) for k in range(9)]
    for s in (-1, 1):
        a0, a1 = sorted((s * 0.6, s * 0.66))
        b.plate(rim + list(reversed(inner)), a0, a1, "brass")
    for s in (-1, 1):
        for k in (-1, 1):
            z = PY + k * 0.9
            b.bolt((s * 0.62, PD - HEAD + 0.5, z), "X", 0.07, s * 0.05, "steel")
    b.gear((0.65, PD - HEAD + 0.95, PY), 0.3, 0.42, 0.06, 10, "dark", "X")
    b.gear((-0.65, PD - HEAD + 0.95, PY), 0.3, 0.42, 0.06, 10, "dark", "X")
    b.skull(0, PD - HEAD + 0.1, PY - 0.05, 1.25, teeth=True)
    b.box((-0.24, PD - HEAD - 0.2, PY - 0.72), (0.24, PD - HEAD + 0.1, PY - 0.5), "bone", bevel=0.03)   # нижняя челюсть намертво
    for k in range(7):
        b.box((-0.2 + k * 0.066, PD - HEAD - 0.2, PY - 0.52), (-0.16 + k * 0.066, PD - HEAD - 0.12, PY - 0.42), "bone")
    b.lathe((0, PD - HEAD + 0.5, PY + 1.82), [(0.1, 0), (0.05, 0.9)], 6, "dark", base=False)            # шпиль

    # ---- шток
    s = m.bone("pump_rod", (0, WELL, PY))
    s.lathe((0, WELL, 3.6), [(0.08, 0), (0.08, PY - 1.85 - 3.6)], 8, "steel", base=False)
    s.lathe((0, WELL, PY - 2.15), [(0.2, 0), (0.2, 0.32)], 8, "dark")
    s.ring((0, WELL, PY - 2.0), 0.18, 0.25, 0.05, 8, "brass", "Z")

    # ---- огонь
    fl = m.bone("stack_flame", (0, 11.875, 8.3))
    for x in (-1.75, 1.75):
        fl.lathe((x, 11.875, 8.28), [(0.44, 0), (0.36, 0.3), (0.14, 0.72), (0.02, 1.05)], 6, "fire", base=False)


def state(t):
    a = 2 * math.pi * t
    phi = math.asin(CR * math.sin(a) / TAIL)
    ty, td = PY + TAIL * math.sin(phi), PD + TAIL * math.cos(phi)
    py, pd = CY + CR * math.sin(a), CD + CR * math.cos(a)
    rod = math.atan2(pd - td, ty - py)
    return a, phi, rod, ty - PY, td - (PD + TAIL), -HEAD * math.sin(phi)


def animate(objs, sc):
    frames = int(LOOP * 24)
    for f in range(frames + 1):
        a, phi, rod, dz, dy, head = state(f / frames)
        objs["crank"].rotation_euler = (a, 0, 0)
        objs["beam"].rotation_euler = (phi, 0, 0)
        for n, x in (("rod_1", -ROD_X), ("rod_2", ROD_X)):
            objs[n].rotation_euler = (rod, 0, 0)
            objs[n].location = (x, PD + TAIL + dy, PY + dz)
            objs[n].keyframe_insert("rotation_euler", frame=f + 1)
            objs[n].keyframe_insert("location", frame=f + 1)
        objs["pump_rod"].location = (0, WELL, PY + head)
        for n, p in (("crank", "rotation_euler"), ("beam", "rotation_euler"), ("pump_rod", "location")):
            objs[n].keyframe_insert(p, frame=f + 1)
    sc.frame_set(1)


def tracks():
    steps = 32
    beam, rod, rod_p, pump, flame = {}, {}, {}, {}, {}
    for i in range(steps + 1):
        t = i / steps
        key = f"{LOOP * t:.4f}"
        a, phi, r, dz, dy, head = state(t)
        beam[key] = [round(math.degrees(phi), 3), 0, 0]
        rod[key] = [round(math.degrees(r), 3), 0, 0]
        rod_p[key] = [0, round(dz * 16, 3), round(dy * 16, 3)]
        pump[key] = [0, round(head * 16, 3), 0]
        flame[key] = [1, round(1 + 0.3 * math.sin(3 * 2 * math.pi * t) + 0.14 * math.sin(11 * 2 * math.pi * t), 3), 1]
    crank = {f"{LOOP * i / 4:.4f}": [90.0 * i, 0, 0] for i in range(5)}
    return {"crank": {"rotation": crank}, "beam": {"rotation": beam}, "pump_rod": {"position": pump},
            "rod_1": {"rotation": rod, "position": rod_p}, "rod_2": {"rotation": rod, "position": rod_p},
            "stack_flame": {"scale": flame}}, LOOP


m = Machine("extractor")
frame(m)
moving(m)
sc, tris = m.build("WB_Extractor")
light_scene(sc, int(LOOP * 24))
animate(m.objects, sc)
print("костей:", len(m.objects), "треугольников:", tris)
