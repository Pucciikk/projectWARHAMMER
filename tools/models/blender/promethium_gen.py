"""
Прометиевый генераториум (promethium_gen): 5×3×4. Рядный трёхцилиндровый мотор с открытым коленвалом, маховиком и динамо-катушкой;
сзади баки топлива с окошком синего прометия, на выхлопе синее пламя.
"""
import math
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "kit.py"), encoding="utf-8").read())

LOOP, STEPS = 1.2, 36
CRANK_Z, CRANK_Y = 0.98, -0.32   # ось коленвала вдоль X
CRANK_R = 0.2                    # радиус кривошипа
ROD = 0.68                       # длина шатуна
CYLS = (-1.25, -0.5, 0.25)       # x цилиндров
PHASE = (0, 120, 240)            # углы кривошипов
FLY_X = 1.2


def frame(m):
    f = m.bone("frame")
    f.plinth(-2.48, -1.48, 2.48, 1.48)
    # ---- картер: опоры вала и поддон, вал виден между опорами
    f.box((-1.8, CRANK_Y - 0.48, 0.3), (0.8, CRANK_Y + 0.48, 0.58), "dark", bevel=0.03)
    for x in (-1.72, -0.88, -0.12, 0.72):
        f.box((x - 0.08, CRANK_Y - 0.44, 0.58), (x + 0.08, CRANK_Y + 0.44, CRANK_Z + 0.1), "hull", bevel=0.02)
        f.ring((x, CRANK_Y, CRANK_Z), 0.05, 0.13, 0.2, 10, "brass", "X")
    # ---- блок цилиндров на колоннах
    z = CRANK_Z + CRANK_R + ROD + 0.1
    for x in (-1.72, -0.88, -0.12, 0.72):
        for s in (-1, 1):
            f.box((x - 0.06, CRANK_Y + s * 0.34 - 0.06, CRANK_Z + 0.1), (x + 0.06, CRANK_Y + s * 0.34 + 0.06, z), "dark")
    f.box((-1.82, CRANK_Y - 0.44, z), (0.82, CRANK_Y + 0.44, z + 0.1), "hull", bevel=0.02)
    for x in CYLS:
        f.lathe((x, CRANK_Y, z + 0.1), [(0.33, 0), (0.33, 0.72), (0.24, 0.8), (0.24, 0.88)], 12, "hull", base=False)
        for k in range(5):
            f.ring((x, CRANK_Y, z + 0.2 + k * 0.11), 0.32, 0.385, 0.035, 12, "dark", "Z")
        f.lathe((x, CRANK_Y, z + 0.98), [(0.14, 0), (0.14, 0.08), (0.06, 0.14)], 8, "brass", base=False)
        # свеча и провод
        f.pipe([(x, CRANK_Y, z + 1.1), (x, CRANK_Y + 0.25, z + 1.18), (x, 0.5, z + 1.0)], 0.018, 4, "rubber")
    # коллектор выхлопа: от головок к трубе справа
    f.pipe([(CYLS[0], CRANK_Y - 0.28, z + 0.6), (CYLS[0], CRANK_Y - 0.52, z + 0.62), (0.75, CRANK_Y - 0.52, z + 0.62), (0.95, CRANK_Y - 0.18, z + 0.92), (0.95, 0.2, z + 1.1)], 0.09, 8, "rust")
    for x in CYLS[1:]:
        f.pipe([(x, CRANK_Y - 0.28, z + 0.6), (x, CRANK_Y - 0.48, z + 0.62)], 0.07, 6, "rust")
    f.lathe((0.95, 0.2, 2.5), [(0.14, 0), (0.14, 1.0), (0.2, 1.08), (0.2, 1.42)], 10, "rust", base=False)
    f.ring((0.95, 0.2, 3.2), 0.13, 0.2, 0.06, 10, "hazard", "Z")
    # ---- маховик: кожух, опоры; динамо за маховиком
    for s in (-1, 1):
        f.box((FLY_X + 0.16, CRANK_Y + s * 0.42 - 0.08, 0.3), (FLY_X + 0.3, CRANK_Y + s * 0.42 + 0.08, CRANK_Z + 0.08), "dark", bevel=0.015)
    f.box((FLY_X + 0.14, CRANK_Y - 0.52, CRANK_Z + 0.05), (FLY_X + 0.32, CRANK_Y + 0.52, CRANK_Z + 0.16), "hull", bevel=0.015)
    f.lathe((1.98, CRANK_Y, CRANK_Z), [(0.4, -0.38), (0.48, -0.32), (0.48, 0.32), (0.4, 0.38)], 14, "hull", "X")
    for k in range(7):
        f.ring((1.68 + k * 0.1, CRANK_Y, CRANK_Z), 0.46, 0.51, 0.045, 14, "brass", "X")
    f.box((1.62, CRANK_Y - 0.5, 0.3), (2.34, CRANK_Y + 0.5, 0.56), "dark", bevel=0.02)
    # щит шин и токовые изоляторы
    f.box((1.55, CRANK_Y + 0.5, 0.3), (2.42, 0.62, 2.05), "hull", bevel=0.03)
    f.box((1.68, 0.2, 1.3), (2.3, 0.21, 1.9), "screen")
    f.skull(1.98, 0.2, 2.26, 0.38)
    for x in (1.7, 1.98, 2.26):
        f.lathe((x, 0.4, 2.05), [(0.05, 0), (0.05, 0.12), (0.08, 0.14), (0.08, 0.2), (0.02, 0.25)], 6, "bone", base=False)
    # ---- баки топлива сзади: окошки с синим прометием
    for x in (-1.92, -0.7, 0.52):
        f.tank((x, 0.92, 0.3), 0.48, 2.0, 14, "hull", (0.18, 0.9), band_mat="brass")
        f.box((x - 0.08, 0.92 - 0.5, 0.65), (x + 0.08, 0.92 - 0.46, 2.0), "prometh")
        f.box((x - 0.11, 0.92 - 0.47, 0.62), (x + 0.11, 0.92 - 0.44, 2.03), "dark")
        for zz in (0.95, 1.3, 1.65):
            f.box((x - 0.1, 0.92 - 0.52, zz), (x + 0.1, 0.92 - 0.49, zz + 0.025), "steel")
    f.pipe([(-1.92, 0.42, 0.72), (-1.92, 0.25, 0.64), (0.52, 0.25, 0.64)], 0.05, 6, "rust")
    for x in (-0.7, 0.52):
        f.pipe([(x, 0.42, 0.72), (x, 0.25, 0.64)], 0.05, 6, "rust")
    f.pipe([(-1.0, 0.25, 0.64), (-1.0, CRANK_Y + 0.5, 0.64), (-1.0, CRANK_Y + 0.4, z + 0.5), (-1.0, CRANK_Y + 0.32, z + 0.72)], 0.04, 6, "brass")
    # площадка и печати
    f.seal((-2.05, 0.44, 1.5), "Y", -1)
    f.seal((1.6, CRANK_Y - 0.5, 1.8), "Y", -1) if False else None


def moving(m):
    # ---- коленвал: шейки и щёки при нулевом угле кривошипа (вверх)
    cr = m.bone("crank", (0, CRANK_Y, CRANK_Z))
    cr.lathe((0, CRANK_Y, CRANK_Z), [(0.05, -1.82), (0.05, 1.4)], 8, "steel", "X")
    for x, ph in zip(CYLS, PHASE):
        a = math.radians(ph)
        # вращение вокруг X: ось Y → вперёд; верхняя точка кривошипа при фазе 0
        y = CRANK_Y + CRANK_R * math.sin(a)
        zz = CRANK_Z + CRANK_R * math.cos(a)
        for s in (-1, 1):
            cr.beam((x + s * 0.09, CRANK_Y, CRANK_Z), (x + s * 0.09, y, zz), 0.045, 0.13, "hull")
        cr.lathe((x, y, zz), [(0.045, -0.12), (0.045, 0.12)], 8, "steel", "X")
    # ---- шатуны и поршни — позы из кинематики
    for i, x in enumerate(CYLS):
        r = m.bone(f"rod_{i}", (x, CRANK_Y, CRANK_Z + CRANK_R))
        r.box((x - 0.05, CRANK_Y - 0.04, CRANK_Z + CRANK_R), (x + 0.05, CRANK_Y + 0.04, CRANK_Z + CRANK_R + ROD), "steel", bevel=0.012)
        r.lathe((x, CRANK_Y, CRANK_Z + CRANK_R), [(0.08, -0.07), (0.08, 0.07)], 8, "brass", "X")
        p = m.bone(f"piston_{i}", (x, CRANK_Y, CRANK_Z + CRANK_R + ROD))
        # крейцкопф и шток: шток уходит в блок цилиндров сквозь плиту
        p.lathe((x, CRANK_Y, CRANK_Z + CRANK_R + ROD), [(0.1, -0.09), (0.16, -0.06), (0.16, 0.05), (0.1, 0.09)], 10, "brass")
        p.lathe((x, CRANK_Y, CRANK_Z + CRANK_R + ROD), [(0.05, 0.09), (0.05, 0.62)], 6, "steel", base=False)
    # ---- маховик со спицами и красной меткой; вал динамо крутится с ним
    fw = m.bone("flywheel", (FLY_X, CRANK_Y, CRANK_Z))
    fw.ring((FLY_X, CRANK_Y, CRANK_Z), 0.47, 0.62, 0.26, 24, "dark", "X")
    fw.ring((FLY_X, CRANK_Y, CRANK_Z), 0.57, 0.6, 0.28, 24, "brass", "X")
    for k in range(5):
        a = k * 2 * math.pi / 5
        fw.beam((FLY_X, CRANK_Y, CRANK_Z), (FLY_X, CRANK_Y + 0.5 * math.cos(a), CRANK_Z + 0.5 * math.sin(a)), 0.08, 0.14, "hull")
    fw.box((FLY_X - 0.14, CRANK_Y - 0.08, CRANK_Z + 0.58), (FLY_X + 0.14, CRANK_Y + 0.08, CRANK_Z + 0.64), "red")
    fw.lathe((FLY_X + 0.42, CRANK_Y, CRANK_Z), [(0.05, -0.3), (0.05, 0.05)], 6, "steel", "X")
    # ---- синее пламя выхлопа
    fl = m.bone("stack_flame", (0.95, 0.2, 3.92))
    fl.lathe((0.95, 0.2, 3.92), [(0.13, 0), (0.17, 0.05), (0.11, 0.14), (0.04, 0.24), (0, 0.28)], 7, "prometh", base=False)
    # ---- искра на контактах
    a = m.bone("arc", (1.98, 0.4, 2.3))
    a.beam((1.7, 0.4, 2.27), (1.84, 0.37, 2.36), 0.018, 0.018, "screen")
    a.beam((1.84, 0.37, 2.36), (1.98, 0.41, 2.26), 0.018, 0.018, "screen")
    a.beam((1.98, 0.41, 2.26), (2.26, 0.4, 2.3), 0.018, 0.018, "screen")


def pose(t):
    p = {"crank": {"rot": (360 * t, 0, 0)}, "flywheel": {"rot": (360 * t, 0, 0)}}
    for i, ph in enumerate(PHASE):
        # поворот вокруг X на θ переводит палец (R sin ф, R cos ф) в (R sin(ф−θ), R cos(ф−θ))
        a = math.radians(ph - 360 * t)
        pz = CRANK_Z + CRANK_R * math.cos(a)
        px = CRANK_Y + CRANK_R * math.sin(a)
        dz = math.sqrt(max(0.0, ROD * ROD - (px - CRANK_Y) ** 2))
        top = pz + dz
        p[f"piston_{i}"] = {"pos": (0, 0, top - (CRANK_Z + CRANK_R + ROD))}
        # шатун: нижний конец идёт за пальцем, поворот к поршню
        tilt = math.degrees(math.atan2(px - CRANK_Y, dz))
        p[f"rod_{i}"] = {"pos": (0, px - CRANK_Y, pz - (CRANK_Z + CRANK_R)), "rot": (tilt, 0, 0)}
    a = 2 * math.pi * t
    s = 1.0 + 0.3 * math.sin(a * 3) * math.sin(a * 5)
    p["stack_flame"] = {"scale": (1, 1, max(0.5, s))}
    vis = 1 if math.sin(a * 11) * math.sin(a * 3) > -0.3 else 0
    p["arc"] = {"scale": (vis, vis, vis)}
    return p


m = Machine("promethium_gen")
frame(m)
moving(m)
sc, tris = m.build("WB_PromethiumGen")
light_scene(sc, int(LOOP * 24))
auto_animate(m.objects, sc, pose, LOOP)
tracks = lambda: auto_tracks(pose, LOOP, STEPS)
print("костей:", len(m.objects), "треугольников:", tris)
