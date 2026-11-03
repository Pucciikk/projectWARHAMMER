"""
Гидропонный отсек (hydroponics): 5×3×4. Три яруса лотков с растениями под тёплыми люменами; вдоль рядов ходит каретка-распылитель,
за стеллажом бак с питательным раствором и насос. Спереди сервочереп с манипулятором собирает урожай в короб.
"""
import math
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "kit.py"), encoding="utf-8").read())

LOOP, STEPS = 6.0, 72
TIERS = (0.86, 1.72, 2.58)     # верх почвы лотков
X0, X1 = -2.2, 1.35            # стеллаж
Y0, Y1 = -0.62, 0.62


def plant(b, x, y, z, s, kind, seed):
    """Кустик: стебель и 3–4 косо расставленных листа; 6–8 квадов, чтобы лоток не съел бюджет."""
    b.lathe((x, y, z), [(0.018 * s, 0), (0.012 * s, 0.2 * s)], 3, "leaf", base=False)
    for k in range(3 + kind % 2):
        a = seed + k * 2.2
        c, d = math.cos(a), math.sin(a)
        v0 = b.bm.verts.new((x, y, z + 0.14 * s))
        v1 = b.bm.verts.new((x + 0.1 * s * c - 0.06 * s * d, y + 0.1 * s * d + 0.06 * s * c, z + 0.3 * s))
        v2 = b.bm.verts.new((x + 0.24 * s * c, y + 0.24 * s * d, z + 0.26 * s))
        v3 = b.bm.verts.new((x + 0.1 * s * c + 0.06 * s * d, y + 0.1 * s * d - 0.06 * s * c, z + 0.3 * s))
        fc = b.bm.faces.new((v0, v3, v2, v1))
        fc.material_index = NAMES.index("leaf")
    if kind == 2:     # у трав есть цветок
        b.lathe((x, y, z + 0.28 * s), [(0.05 * s, 0), (0.03 * s, 0.05 * s)], 4, "lumen", base=False)


def frame(m):
    f = m.bone("frame")
    f.plinth(-2.48, -1.48, 2.48, 1.48)
    # ---- стойки и лотки
    for x in (X0, (X0 + X1) / 2, X1):
        for y in (Y0, Y1):
            f.box((x - 0.06, y - 0.06, 0.3), (x + 0.06, y + 0.06, 3.5), "dark", bevel=0.012)
    f.box((X0 - 0.1, Y0 - 0.1, 3.5), (X1 + 0.1, Y1 + 0.1, 3.62), "hull", bevel=0.02)
    for z in TIERS:
        f.box((X0 - 0.06, Y0 - 0.02, z - 0.2), (X1 + 0.06, Y1 + 0.02, z - 0.12), "dark", bevel=0.012)
        for y in (Y0 - 0.02, Y1 - 0.02):
            f.box((X0 - 0.06, y, z - 0.12), (X1 + 0.06, y + 0.05, z + 0.02), "steel")
        f.box((X0 - 0.03, Y0 + 0.03, z - 0.12), (X1 + 0.03, Y1 - 0.03, z), "soil")
        # трубка полива
        f.lathe((X0 - 0.02, Y1 - 0.09, z + 0.06), [(0.016, 0), (0.016, X1 - X0)], 4, "brass", "X")
        # люмены над ярусом
        lz = z + 0.68 if z != TIERS[-1] else 3.46
        f.box((X0 + 0.08, -0.1, lz - 0.05), (X1 - 0.08, 0.1, lz), "dark", bevel=0.008)
        f.box((X0 + 0.14, -0.06, lz - 0.075), (X1 - 0.14, 0.06, lz - 0.05), "lumen")
    # ---- растения: три вида, разная плотность
    for t, z in enumerate(TIERS):
        for i in range(10):
            x = X0 + 0.25 + i * (X1 - X0 - 0.5) / 9
            for j, y in enumerate((-0.32, 0.26)):
                plant(f, x + (j * 0.09), y, z, 1.0 + 0.2 * math.sin(i * 1.7 + t + j), t, i * 1.3 + j * 2 + t)
    # ---- короб с травами спереди
    f.box((-2.2, -1.42, 0.3), (-1.32, -0.9, 0.72), "wood", bevel=0.015)
    f.box((-2.14, -1.36, 0.65), (-1.38, -0.96, 0.73), "leaf")
    f.seal((-1.76, -1.42, 0.62), "Y", -1)
    # ---- правая секция: бак с раствором, насос, панель
    f.tank((2.0, 0.65, 0.3), 0.45, 2.2, 14, "steel", (0.2, 0.55, 0.88), band_mat="brass")
    f.box((1.92, 0.19, 0.7), (2.08, 0.22, 2.3), "water")
    f.box((1.89, 0.21, 0.67), (2.11, 0.25, 2.33), "dark")
    f.pipe([(2.0, 0.65, 2.95), (2.0, 0.65, 3.2), (X1 + 0.12, 0.54, 3.2), (X1 + 0.12, 0.54, 0.95)], 0.05, 6, "rust")
    for z in TIERS:
        f.pipe([(X1 + 0.12, 0.54, z + 0.06), (X1 - 0.02, Y1 - 0.09, z + 0.06)], 0.03, 4, "rust")
    f.box((1.55, -1.42, 0.3), (2.42, -0.72, 1.28), "hull", bevel=0.03)
    f.box((1.63, -1.43, 0.52), (2.34, -1.415, 1.08), "screen")
    f.skull(1.98, -1.02, 1.54, 0.38)
    f.lathe((2.0, -0.2, 0.3), [(0.28, 0), (0.28, 0.45), (0.2, 0.52)], 10, "rust", base=False)
    f.pipe([(2.0, -0.2, 0.82), (2.0, 0.2, 0.9)], 0.05, 6, "rust")
    f.seal((1.55, -0.92, 1.1), "X", -1)
    # рельс распылителя над фасадом
    f.box((X0, Y0 - 0.18, 3.34), (X1, Y0 - 0.1, 3.42), "brass")


def moving(m):
    # ---- каретка-распылитель: идёт вдоль рельса, на штанге три сопла
    c = m.bone("sprayer", (X0 + 0.2, Y0 - 0.14, 3.3))
    c.box((X0 + 0.08, Y0 - 0.22, 3.18), (X0 + 0.32, Y0 - 0.06, 3.34), "hull", bevel=0.015)
    c.lathe((X0 + 0.2, Y0 - 0.14, 0.72), [(0.022, 0), (0.022, 2.5)], 5, "steel", base=False)
    for z in TIERS:
        c.box((X0 + 0.1, Y0 - 0.17, z + 0.34), (X0 + 0.3, Y0 - 0.11, z + 0.39), "dark")
        c.lathe((X0 + 0.2, Y0 - 0.11, z + 0.36), [(0.03, 0), (0.018, 0.1)], 5, "brass", "Y", base=False)
    # ---- капли с распылителя
    for i, z in enumerate(TIERS):
        d = m.bone(f"mist_{i}", (X0 + 0.2, Y0 + 0.02, z + 0.3))
        d.lathe((X0 + 0.2, Y0 + 0.02, z + 0.3), [(0, -0.025), (0.02, 0), (0, 0.025)], 4, "water", cap=False)
    # ---- сервочереп на тросе: опускается к лотку
    s = m.bone("skull_servo", (-0.5, -1.05, 2.8))
    s.skull(-0.5, -0.92, 2.62, 0.3, teeth=False)
    s.lathe((-0.5, -1.05, 2.85), [(0.018, 0), (0.018, 0.65)], 4, "steel", base=False)
    s.beam((-0.42, -1.1, 2.48), (-0.28, -0.84, 2.22), 0.03, 0.03, "brass")
    s.beam((-0.28, -0.84, 2.22), (-0.32, -0.72, 2.12), 0.025, 0.025, "steel")
    # ---- крыльчатка насоса
    p = m.bone("pump_fan", (2.0, -0.2, 0.86))
    for k in range(4):
        a = k * math.pi / 2
        p.beam((2.0, -0.2, 0.85), (2.0 + 0.2 * math.cos(a), -0.2 + 0.2 * math.sin(a), 0.85), 0.1, 0.02, "brass")


def pose(t):
    a = 2 * math.pi * t
    # каретка едет туда и обратно с плавными остановками
    k = 0.5 - 0.5 * math.cos(a)
    run = (X1 - X0 - 0.4) * k
    p = {"sprayer": {"pos": (run, 0, 0)}, "pump_fan": {"rot": (0, 0, 360 * 4 * t)}}
    for i in range(3):
        u = (t * 6 + i * 0.33) % 1
        p[f"mist_{i}"] = {"pos": (run, 0.12 * u, -0.28 * u * u), "scale": (1, 1, 1) if u < 0.9 else (0, 0, 0)}
    b = 0.5 - 0.5 * math.cos(a * 2)
    p["skull_servo"] = {"pos": (0.8 * math.sin(a), 0, -0.55 * b)}
    return p


m = Machine("hydroponics")
frame(m)
moving(m)
sc, tris = m.build("WB_Hydroponics")
light_scene(sc, int(LOOP * 24))
auto_animate(m.objects, sc, pose, LOOP)
tracks = lambda: auto_tracks(pose, LOOP, STEPS)
print("костей:", len(m.objects), "треугольников:", tris)
