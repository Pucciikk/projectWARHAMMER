"""
Полимерный автоклав (autoclave): 3×3×4. Лежачий сосуд высокого давления с откидной круглой крышкой на петле. Цикл: засовы уходят,
крышка распахивается, поддон с листами выезжает, возвращается, крышка закрывается, засовы встают; в работе сбрасывается пар.
"""
import math
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "kit.py"), encoding="utf-8").read())

LOOP, STEPS = 8.0, 64
AX, AZ = 0.0, 1.5     # ось сосуда: x, z
R = 1.02
FRONT = -0.9          # плоскость фланца
HINGE = (R + 0.08, FRONT - 0.04)


def frame(m):
    f = m.bone("frame")
    f.plinth(-1.48, -1.48, 1.48, 1.48)
    # ---- сёдла
    for y in (-0.4, 0.8):
        f.box((-1.0, y - 0.13, 0.3), (1.0, y + 0.13, 0.75), "dark", bevel=0.03)
    # ---- корпус: лежачий цилиндр, сферическое дно, бандажи, фланец
    f.lathe((AX, FRONT, AZ), [(R + 0.12, 0), (R + 0.12, 0.14), (R, 0.2), (R, 1.82), (R * 0.84, 2.08), (R * 0.5, 2.26), (R * 0.2, 2.32)], 20, "hull", "Y", base=False)
    for y in (-0.35, 0.3, 0.85):
        f.ring((AX, y, AZ), R - 0.03, R + 0.06, 0.1, 20, "brass", "Y")
    for k in range(10):
        a = k * math.pi / 5
        f.bolt((AX + (R + 0.05) * math.cos(a), 0.0, AZ + (R + 0.05) * math.sin(a)), "Y", 0.03, 0.02, "steel")
    # внутренность сосуда и пазы поддона
    f.lathe((AX, FRONT + 0.02, AZ), [(R - 0.02, 0.02), (R - 0.14, 0.02), (R - 0.14, 1.4)], 20, "dark", "Y", cap=False)
    f.lathe((AX, FRONT + 1.4, AZ), [(R - 0.15, 0), (R - 0.15, 0.02)], 20, "fire", "Y", base=False)
    for x in (-0.55, 0.55):
        f.box((x - 0.05, FRONT + 0.02, AZ - 0.62), (x + 0.05, 0.5, AZ - 0.58), "steel")
    # ---- упоры петли и засовов
    f.box((R + 0.02, FRONT - 0.1, AZ - 0.8), (R + 0.2, FRONT + 0.14, AZ + 0.8), "dark", bevel=0.02)
    for z in (AZ + 1.02, AZ - 1.02):
        f.box((-0.28, FRONT - 0.03, z - 0.12), (0.28, FRONT + 0.14, z + 0.12), "dark", bevel=0.02)
    # ---- паропроводы, клапан, труба сброса, манометр
    f.pipe([(0.3, 0.3, AZ + R), (0.3, 0.3, 3.05), (0.75, 0.55, 3.25), (0.75, 0.55, 3.45)], 0.07, 8, "rust")
    f.lathe((0.75, 0.55, 3.45), [(0.11, 0), (0.11, 0.2), (0.15, 0.22), (0.15, 0.3), (0.05, 0.34)], 8, "brass", base=False)
    f.pipe([(-0.5, 0.6, AZ + R - 0.05), (-0.5, 0.6, 3.0), (-1.0, 1.0, 3.0), (-1.0, 1.0, 0.3)], 0.06, 6, "rust")
    f.lathe((-0.25, 0.3, AZ + R), [(0.16, 0), (0.16, 0.1), (0.12, 0.14), (0.05, 0.18)], 8, "dark", base=False)
    f.lathe((-0.72, -0.4, AZ + R - 0.18), [(0.14, 0), (0.14, 0.18), (0.11, 0.2)], 12, "brass", base=False)
    f.lathe((-0.72, -0.4, AZ + R + 0.0), [(0.1, 0), (0.1, 0.02)], 12, "glass", base=False)
    # ---- стол выдачи перед машиной, пульт, бак смолы
    f.box((-0.9, -1.48, 0.3), (0.9, FRONT - 0.15, AZ - 0.72), "dark", bevel=0.02)
    f.tank((1.1, 1.05, 0.3), 0.3, 1.5, 10, "rust", (0.3, 0.7), band_mat="hazard")
    f.pipe([(1.1, 1.05, 1.95), (1.1, 1.05, 2.25), (0.7, 0.9, 2.3)], 0.05, 6, "steel")
    f.box((-1.42, -1.2, 0.3), (-1.08, -0.45, 1.2), "hull", bevel=0.03)
    f.box((-1.43, -1.1, 0.55), (-1.415, -0.55, 1.08), "screen")
    f.seal((-1.0, -0.78, 2.1), "Y", -1) if False else None
    f.seal((-0.95, -0.2, 2.12), "Y", -1) if False else None
    f.skull(0, 0.0, AZ + R + 0.22, 0.0001) if False else None
    f.gear((0, 1.38, AZ), 0.28, 0.38, 0.05, 12, "brass", "Y")


def moving(m):
    # ---- крышка: выпуклая, с ребрами и черепом; вращается на петле (ось вдоль Z на правом краю)
    d = m.bone("door", (HINGE[0], HINGE[1], AZ))
    y = FRONT - 0.04
    d.lathe((AX, y, AZ), [(R + 0.08, 0.02), (R + 0.08, -0.07), (R * 0.9, -0.14), (R * 0.45, -0.22), (R * 0.2, -0.24)], 20, "hull", "Y", base=False)
    d.ring((AX, y - 0.08, AZ), R - 0.02, R + 0.1, 0.05, 20, "brass", "Y")
    for k in range(8):
        a = k * math.pi / 4
        d.beam((AX + 0.2 * math.cos(a), y - 0.24, AZ + 0.2 * math.sin(a)), (AX + R * 0.88 * math.cos(a), y - 0.15, AZ + R * 0.88 * math.sin(a)), 0.06, 0.05, "dark")
    d.gear((AX, y - 0.22, AZ), 0.26, 0.36, 0.05, 12, "brass", "Y")
    d.skull(AX, y - 0.22, AZ + 0.02, 0.5)
    for z in (AZ - 0.62, AZ, AZ + 0.62):
        d.box((HINGE[0] - 0.14, y - 0.09, z - 0.09), (HINGE[0] + 0.02, y + 0.03, z + 0.09), "dark", bevel=0.012)
    d.lathe((HINGE[0], y, AZ - 0.85), [(0.05, 0), (0.05, 1.7)], 8, "steel", base=False)
    # ---- два засова: верхний и нижний, уходят на корпус
    for name, sign in (("bolt_top", 1), ("bolt_low", -1)):
        z = AZ + sign * 1.02
        b = m.bone(name, (0, y, z))
        b.box((-0.22, y - 0.08, z - 0.07), (0.22, y + 0.16, z + 0.07), "steel", bevel=0.012)
        b.box((-0.24, y - 0.09, z - 0.03), (0.24, y - 0.05, z + 0.03), "hazard")
    # ---- поддон с листами армапласа
    t = m.bone("tray", (0, FRONT + 0.5, AZ - 0.55))
    t.box((-0.62, FRONT + 0.05, AZ - 0.58), (0.62, FRONT + 1.05, AZ - 0.53), "steel", bevel=0.008)
    for k in range(4):
        z = AZ - 0.5 + k * 0.08
        t.box((-0.54, FRONT + 0.12, z), (0.54, FRONT + 0.98, z + 0.05), "stain_gold" if k == 3 else "rust")
    t.box((-0.62, FRONT + 0.02, AZ - 0.58), (0.62, FRONT + 0.08, AZ - 0.32), "dark")
    # ---- рычаг клапана
    v = m.bone("valve", (0.75, 0.55, 3.72))
    v.beam((0.75, 0.55, 3.72), (0.75 + 0.3, 0.55, 3.8), 0.03, 0.03, "red")
    v.lathe((1.06, 0.55, 3.76), [(0.05, 0), (0.05, 0.08)], 6, "brass", base=False)


def smooth(x):
    return x * x * (3 - 2 * x)


def seg(t, a, b):
    return smooth(max(0.0, min(1.0, (t - a) / (b - a))))


def pose(t):
    bolts = seg(t, 0.02, 0.1) * (1 - seg(t, 0.9, 0.98))
    door = seg(t, 0.1, 0.24) * (1 - seg(t, 0.76, 0.9))
    tray = seg(t, 0.24, 0.38) * (1 - seg(t, 0.62, 0.76))
    a = 2 * math.pi * t
    return {
        "door": {"rot": (0, 0, 118 * door)},
        "bolt_top": {"pos": (0, 0.22 * bolts, 0)},
        "bolt_low": {"pos": (0, 0.22 * bolts, 0)},
        "tray": {"pos": (0, -1.06 * tray, 0)},
        "valve": {"rot": (0, 0, -20 * math.sin(3 * a))},
    }


m = Machine("autoclave")
frame(m)
moving(m)
sc, tris = m.build("WB_Autoclave")
light_scene(sc, int(LOOP * 24))
auto_animate(m.objects, sc, pose, LOOP)
tracks = lambda: auto_tracks(pose, LOOP, STEPS)
print("костей:", len(m.objects), "треугольников:", tris)
