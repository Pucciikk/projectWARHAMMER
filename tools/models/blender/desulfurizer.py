"""
Сероочистка (desulfurizer): 3×3×4. Реактор с мешалкой, ротор-скруббер на боку, баллон водорода; из шнека падает жёлтая сера
в открытую вагонетку спереди.
"""
import math
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "kit.py"), encoding="utf-8").read())

LOOP, STEPS = 3.0, 48
RX, RY = -0.35, 0.3   # ось реактора
DROP = (0.75, -0.86, 1.32)   # откуда падает сера
CHUTE_Z = 0.62


def frame(m):
    f = m.bone("frame")
    f.plinth(-1.48, -1.48, 1.48, 1.48)
    # ---- реактор на опорах
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        x, y = RX + 0.72 * math.cos(a), RY + 0.72 * math.sin(a)
        f.box((x - 0.09, y - 0.09, 0.3), (x + 0.09, y + 0.09, 1.0), "dark", bevel=0.015)
    f.lathe((RX, RY, 0.72), [(0.3, 0), (0.72, 0.28), (0.9, 0.62), (0.9, 2.05), (0.72, 2.42), (0.3, 2.65), (0.2, 2.72)], 18, "hull", base=False)
    for z in (1.42, 2.1, 2.72):
        f.ring((RX, RY, z), 0.87, 0.95, 0.09, 18, "brass", "Z")
    for k in range(10):
        a = k * math.pi / 5
        f.bolt((RX + 0.93 * math.cos(a), RY + 0.93 * math.sin(a), 1.78), "Z", 0.03, 0.02, "steel")
    # окна с кипящей жёлтой средой
    for a in (-2.0, -1.2):
        x, y = RX + 0.88 * math.cos(a), RY + 0.88 * math.sin(a)
        f.lathe((x, y, 1.7), [(0.13, -0.2), (0.13, 0.28)], 6, "sulfur")
    # редуктор наверху реактора с мотором, вал мешалки на другой кости
    f.lathe((RX, RY, 3.4), [(0.26, 0), (0.26, 0.26), (0.14, 0.32)], 10, "rust", base=False)
    f.box((RX - 0.34, RY - 0.34, 3.26), (RX + 0.34, RY + 0.34, 3.4), "dark", bevel=0.02)
    # ---- баллон водорода и труба
    f.tank((1.02, 1.0, 0.3), 0.34, 2.1, 12, "steel", (0.2, 0.55, 0.85), band_mat="hazard")
    f.pipe([(1.02, 1.0, 2.72), (1.02, 1.0, 3.05), (0.2, 0.8, 3.1), (RX + 0.2, RY + 0.2, 3.05)], 0.05, 8, "rust")
    f.lathe((0.72, 1.0, 1.5), [(0.1, 0), (0.1, -0.04), (0.08, -0.06)], 10, "brass", "X", base=False)
    # ---- шнек серы: наклонная труба от реактора к выгрузке, мотор
    f.pipe([(RX + 0.75, RY - 0.42, 1.75), (0.75, -0.42, 1.55), (0.75, -0.75, 1.42)], 0.18, 10, "rust")
    f.box((0.57, -1.02, 1.18), (0.93, -0.68, 1.42), "dark", bevel=0.02)
    f.lathe((0.98, -0.42, 1.55), [(0.17, 0), (0.17, 0.3), (0.08, 0.36)], 10, "hull", "X", base=False)
    # ---- скруббер: кольцо, опоры и вентиль
    f.ring((-1.08, -0.72, 1.35), 0.42, 0.54, 0.12, 16, "hull", "Y")
    f.wedge((-1.42, -0.86, 0.3), (-0.74, -0.58), (-1.2, -0.78, 0.9), (-0.96, -0.66), "dark")
    f.pipe([(-1.08, -0.72, 1.88), (-1.08, -0.45, 2.25), (RX - 0.72, RY - 0.3, 2.4)], 0.07, 8, "rust")
    f.lathe((-1.08, -0.72, 1.88), [(0.09, 0), (0.09, 0.28), (0.14, 0.3), (0.14, 0.36), (0.05, 0.4)], 8, "dark", base=False)
    # ---- вагонетка с серой под шнеком
    for x in (0.4, 1.12):
        f.box((x - 0.03, -1.48, 0.3), (x + 0.03, -0.42, 0.36), "steel")
    f.loft([(0.42, 0.34, 0.34, -0.9), (CHUTE_Z, 0.42, 0.42, -0.9), (CHUTE_Z, 0.35, 0.35, -0.9), (0.46, 0.28, 0.28, -0.9)], "dark") if False else None
    f.box((0.34, -1.3, 0.36), (1.16, -0.52, 0.42), "dark", bevel=0.015)
    for s in (-1, 1):
        f.box((0.75 + s * 0.42 - 0.03, -1.3, 0.42), (0.75 + s * 0.42 + 0.03, -0.52, CHUTE_Z + 0.1), "rust")
        f.box((0.34, -0.91 + s * 0.42 - 0.03, 0.42), (1.16, -0.91 + s * 0.42 + 0.03, CHUTE_Z + 0.1), "rust")
    f.box((0.38, -1.27, 0.42), (1.12, -0.55, CHUTE_Z), "sulfur")
    for i, (x, y) in enumerate(((0.55, -1.1), (0.78, -0.82), (0.95, -1.08), (0.62, -0.72), (0.98, -0.72), (0.74, -1.14))):
        f.lathe((x, y, CHUTE_Z), [(0.09, 0), (0.07, 0.05), (0.02, 0.09)], 5, "sulfur", phase=i, base=False)
    # череп и пульт
    f.gear((RX, RY - 0.91, 2.42), 0.2, 0.28, 0.04, 10, "brass", "Y") if False else None
    f.skull(RX + 0.32, RY - 0.8, 2.3, 0.4, augmetic=False)
    f.box((-1.42, 0.5, 0.3), (-1.05, 1.32, 1.3), "hull", bevel=0.03)
    f.box((-1.43, 0.58, 0.62), (-1.415, 1.24, 1.15), "screen")
    f.seal((RX - 0.55, RY - 0.76, 1.3), "Y", -1)
    f.seal((1.2, 0.4, 2.4), "X", 1) if False else None


def moving(m):
    # ---- вал реактора над редуктором
    g = m.bone("stir", (RX, RY, 3.3))
    g.lathe((RX, RY, 3.05), [(0.055, 0), (0.055, 0.75)], 6, "steel", base=False)
    for s in (-1, 1):
        g.beam((RX, RY, 3.72), (RX + s * 0.26, RY, 3.82), 0.04, 0.04, "brass")
        g.lathe((RX + s * 0.26, RY, 3.82), [(0, -0.05), (0.05, -0.02), (0.05, 0.02), (0, 0.05)], 6, "brass", cap=False)
    # ---- ротор скруббера
    r = m.bone("scrubber", (-1.08, -0.72, 1.35))
    r.lathe((-1.08, -0.82, 1.35), [(0.07, 0), (0.07, 0.2)], 8, "steel", "Y")
    for k in range(5):
        a = k * 2 * math.pi / 5
        r.beam((-1.08, -0.72, 1.35), (-1.08 + 0.38 * math.cos(a), -0.72, 1.35 + 0.38 * math.sin(a)), 0.13, 0.03, "brass")
    # ---- падающие куски серы
    for i in range(3):
        c = m.bone(f"chunk_{i}", DROP)
        c.lathe((DROP[0] + (-0.08 + i * 0.08), DROP[1] + (0.04 - 0.04 * i), DROP[2] - 0.15), [(0.0, -0.05), (0.05, -0.02), (0.045, 0.03), (0.0, 0.06)], 5, "sulfur", cap=False)


def pose(t):
    a = 2 * math.pi * t
    p = {"stir": {"rot": (0, 0, -360 * t)}, "scrubber": {"rot": (0, 360 * 2 * t, 0)}}
    fall = DROP[2] - 0.15 - CHUTE_Z
    for i in range(3):
        u = (t * 2 + i / 3) % 1
        vis = 1 if u < 0.92 else 0
        p[f"chunk_{i}"] = {"pos": (0, 0, -fall * u * u), "scale": (vis, vis, vis)}
    return p


m = Machine("desulfurizer")
frame(m)
moving(m)
sc, tris = m.build("WB_Desulfurizer")
light_scene(sc, int(LOOP * 24))
auto_animate(m.objects, sc, pose, LOOP)
tracks = lambda: auto_tracks(pose, LOOP, STEPS)
print("костей:", len(m.objects), "треугольников:", tris)
