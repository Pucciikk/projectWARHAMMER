"""
Водозабор (water_intake): 3×3×3. Колодезное кольцо с водой, спаренный поршневой насос на коленвале,
маховик и улитка центробежного насоса с видимой крыльчаткой; нагнетательный коллектор сзади.
"""
import math
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "kit.py"), encoding="utf-8").read())

LOOP = 2.0
WELL = (-0.45, -0.3)
SHAFT_Z = 1.72
CRANK = 0.17
PIST_X = (-0.72, -0.18)
ROD = 0.62


def frame(m):
    f = m.bone("frame")
    f.plinth(-1.48, -1.48, 1.48, 1.48)
    # ---- колодец: каменное кольцо, стальной бандаж, вода
    x, y = WELL
    f.lathe((x, y, 0.3), [(0.92, 0), (0.92, 0.42), (0.98, 0.42), (0.98, 0.52), (0.76, 0.52), (0.76, 0.34)], 18, "brick", cap=False)
    f.ring((x, y, 0.52), 0.92, 1.0, 0.05, 18, "brass", "Z")
    for k in range(6):
        a = k * math.pi / 3
        f.bolt((x + 0.95 * math.cos(a), y + 0.95 * math.sin(a), 0.545), "Z", 0.035, 0.025, "steel")
    # ---- портал над колодцем: стойки, направляющие цилиндры
    for sy in (-0.42, 0.42):
        f.box((-1.32, y + sy - 0.08, 0.3), (-1.16, y + sy + 0.08, 2.1), "hull", bevel=0.02)
        f.box((0.26, y + sy - 0.08, 0.3), (0.42, y + sy + 0.08, 2.1), "hull", bevel=0.02)
    f.box((-1.32, y - 0.5, 2.1), (0.42, y + 0.5, 2.22), "dark", bevel=0.025)
    f.box((-1.34, y - 0.52, 2.14), (0.44, y + 0.52, 2.17), "brass")
    for px in PIST_X:
        f.lathe((px, y, 0.42), [(0.16, 0), (0.16, 0.08), (0.11, 0.12), (0.11, 0.62), (0.15, 0.65), (0.15, 0.72), (0.06, 0.76)], 10, "rust", base=False)
        f.pipe([(px, y, 0.62), (px, y - 0.28, 0.62), (px, y - 0.28, 0.36)], 0.04, 6, "steel")
    # подшипники коленвала
    for bx in (-1.08, 0.18):
        f.box((bx - 0.07, y - 0.15, SHAFT_Z - 0.16), (bx + 0.07, y + 0.15, SHAFT_Z + 0.16), "dark", bevel=0.015)
        f.beam((bx, y - 0.4, 2.1), (bx, y, SHAFT_Z + 0.1), 0.07, 0.07, "dark")
        f.beam((bx, y + 0.4, 2.1), (bx, y, SHAFT_Z + 0.1), 0.07, 0.07, "dark")
    # ---- мотор справа и привод
    f.box((0.5, -1.05, 0.3), (1.32, -0.2, 0.46), "dark", bevel=0.02)
    f.lathe((0.46, y, SHAFT_Z), [(0.06, 0), (0.06, 0.2)], 6, "steel", "X")
    f.lathe((0.65, -0.62, 0.46 + 0.32), [(0.32, 0), (0.32, 0.65)], 12, "hull", "X")
    for k in range(5):
        f.ring((0.72 + k * 0.13, -0.62, 0.78), 0.3, 0.37, 0.05, 12, "dark", "X")
    f.lathe((1.3, -0.62, 0.78), [(0.25, 0), (0.1, 0.08)], 8, "brass", "X", base=False)
    f.box((1.0, -0.98, 0.46), (1.25, -0.28, 0.5), "brass")
    # ---- улитка центробежного насоса
    f.ring((0.82, 0.62, 0.95), 0.32, 0.5, 0.34, 18, "hull", "Y")
    f.ring((0.82, 0.62 - 0.19, 0.95), 0.36, 0.52, 0.04, 18, "brass", "Y")
    f.pipe([(0.82, 0.62, 0.45), (0.82, 0.62, 0.3)], 0.12, 8, "dark")
    f.box((0.62, 0.42, 0.3), (1.02, 0.82, 0.46), "dark", bevel=0.02)
    # всасывание из колодца и напор в коллектор
    f.pipe([(0.4, -0.2, 0.46), (0.5, 0.28, 0.46), (0.5, 0.62, 0.95), (0.65, 0.62, 0.95)], 0.09, 8, "rust")
    f.pipe([(0.82, 0.8, 1.42), (0.82, 1.18, 1.65), (0.1, 1.18, 1.65)], 0.1, 8, "rust")
    # ---- коллектор сзади: три вывода с вентилями
    f.box((-1.3, 0.98, 0.3), (0.2, 1.38, 1.2), "hull", bevel=0.05)
    f.box((-1.32, 0.96, 0.82), (0.22, 1.4, 0.9), "brass")
    for bx in (-1.1, -0.55, 0):
        f.pipe([(bx, 1.18, 1.2), (bx, 1.18, 1.65)], 0.08, 8, "rust")
        f.ring((bx, 1.18, 1.42), 0.06, 0.15, 0.03, 10, "red", "Z")
    f.pipe([(-1.1, 1.18, 1.65), (0.1, 1.18, 1.65)], 0.1, 8, "steel")
    # манометр, череп на портале, печать
    f.lathe((0.9, -1.12, 1.3), [(0.12, 0), (0.12, -0.04), (0.1, -0.06)], 12, "brass", "Y", base=False)
    f.lathe((0.9, -1.18, 1.3), [(0.085, 0), (0.085, -0.004)], 12, "glass", "Y", base=False)
    f.box((0.8, -1.12, 0.46), (1.0, -1.06, 1.2), "dark")
    f.gear((-0.45, -0.84, 2.55), 0.2, 0.28, 0.04, 10, "brass", "Y")
    f.skull(-0.45, -0.82, 2.55, 0.32, augmetic=False)
    f.box((-0.62, -0.78, 2.22), (-0.28, -0.72, 2.34), "dark")
    f.seal((0.34, -0.8, 1.6), "Y", -1)


def moving(m):
    x, y = WELL
    # ---- вода: качается и «дышит» в такт насосу
    w = m.bone("water", (x, y, 0.72))
    w.lathe((x, y, 0.72), [(0.78, 0), (0.78, 0.02)], 18, "water", base=False)
    # ---- коленвал и маховик
    c = m.bone("crank", (0, y, SHAFT_Z))
    c.lathe((-1.14, y, SHAFT_Z), [(0.05, 0), (0.05, 1.8)], 8, "steel", "X")
    for i, px in enumerate(PIST_X):
        sign = 1 if i == 0 else -1
        for dx in (-0.09, 0.09):
            c.box((px + dx - 0.02, y - 0.05, SHAFT_Z + min(0, sign * CRANK) - 0.05), (px + dx + 0.02, y + 0.05, SHAFT_Z + max(0, sign * CRANK) + 0.05), "dark")
        c.lathe((px - 0.1, y, SHAFT_Z + sign * CRANK), [(0.035, 0), (0.035, 0.2)], 6, "steel", "X")
    c.ring((-0.45, y, SHAFT_Z), 0.3, 0.42, 0.08, 18, "hull")
    c.ring((-0.45, y, SHAFT_Z), 0.38, 0.43, 0.03, 18, "brass")
    for k in range(4):
        a = k * math.pi / 2
        c.beam((-0.45, y, SHAFT_Z), (-0.45, y + 0.34 * math.cos(a), SHAFT_Z + 0.34 * math.sin(a)), 0.035, 0.035, "hull")
    # ---- поршни: шток ходит по вертикали
    for i, px in enumerate(PIST_X):
        p = m.bone(f"piston_{i + 1}", (px, y, 1.16))
        p.lathe((px, y, 1.1), [(0.04, 0), (0.04, 0.35)], 6, "steel", base=False)
        p.box((px - 0.07, y - 0.07, 1.42), (px + 0.07, y + 0.07, 1.5), "dark", bevel=0.012)
    # ---- крыльчатка улитки
    im = m.bone("impeller", (0.82, 0.62, 0.95))
    im.lathe((0.82, 0.36, 0.95), [(0.08, 0), (0.08, 0.5)], 8, "steel", "Y")
    for k in range(6):
        a = k * math.pi / 3
        im.beam((0.82, 0.62, 0.95), (0.82 + 0.3 * math.cos(a), 0.62, 0.95 + 0.3 * math.sin(a)), 0.1, 0.24, "brass")


def state(t):
    a = 2 * math.pi * t
    p1 = CRANK * math.sin(a)
    return a, p1, -p1, 0.012 * math.sin(a)


def animate(objs, sc):
    frames = int(LOOP * 24)
    y = WELL[1]
    for f in range(frames + 1):
        a, p1, p2, dw = state(f / frames)
        objs["crank"].rotation_euler = (a, 0, 0)
        objs["impeller"].rotation_euler = (0, 2 * a, 0)
        objs["piston_1"].location = (PIST_X[0], y, 1.16 + p1)
        objs["piston_2"].location = (PIST_X[1], y, 1.16 + p2)
        objs["water"].location = (WELL[0], y, 0.72 + dw)
        for n, p in (("crank", "rotation_euler"), ("impeller", "rotation_euler"), ("piston_1", "location"), ("piston_2", "location"), ("water", "location")):
            objs[n].keyframe_insert(p, frame=f + 1)
    sc.frame_set(1)


def tracks():
    steps = 24
    p1, p2, w = {}, {}, {}
    for i in range(steps + 1):
        t = i / steps
        a, a1, a2, dw = state(t)
        key = f"{LOOP * t:.4f}"
        p1[key] = [0, round(a1 * 16, 3), 0]
        p2[key] = [0, round(a2 * 16, 3), 0]
        w[key] = [0, round(dw * 16, 3), 0]
    return {"crank": {"rotation": {f"{LOOP * i / 4:.4f}": [90.0 * i, 0, 0] for i in range(5)}},
            "impeller": {"rotation": {f"{LOOP * i / 8:.4f}": [0, 0, 90.0 * i] for i in range(9)}},
            "piston_1": {"position": p1}, "piston_2": {"position": p2}, "water": {"position": w}}, LOOP


m = Machine("water_intake")
frame(m)
moving(m)
sc, tris = m.build("WB_WaterIntake")
light_scene(sc, int(LOOP * 24))
animate(m.objects, sc)
print("костей:", len(m.objects), "треугольников:", tris)
