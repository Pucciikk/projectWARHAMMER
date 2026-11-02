"""
Снаряжательная линия (ammo_line): 7×3×3. Конвейер вдоль X шагом подаёт гильзы через три поста: штамп, дозатор заряда и обжимная
головка. Гильзы выходят из короба слева и уходят в ящик справа; на шагах конвейера посты стоят, в паузах работают.
"""
import math
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "kit.py"), encoding="utf-8").read())

LOOP, STEPS = 2.4, 48
BELT_Y, BELT_Z = -0.3, 0.92
PITCH = 0.44
X0, X1 = -2.75, 2.75       # концы ленты
STATIONS = (-1.32, 0.0, 1.32)


def frame(m):
    f = m.bone("frame")
    f.plinth(-3.48, -1.48, 3.48, 1.48)
    # ---- станина конвейера и лента
    for x in (-2.6, -0.66, 0.66, 2.6):
        f.wedge((x - 0.2, BELT_Y - 0.48, 0.3), (x + 0.2, BELT_Y + 0.48), (x - 0.12, BELT_Y - 0.38, BELT_Z - 0.14), (x + 0.12, BELT_Y + 0.38), "dark")
    for s in (-1, 1):
        f.box((X0 - 0.2, BELT_Y + s * 0.42 - 0.05, BELT_Z - 0.14), (X1 + 0.2, BELT_Y + s * 0.42 + 0.05, BELT_Z + 0.05), "hull", bevel=0.012)
    f.box((X0, BELT_Y - 0.37, BELT_Z - 0.04), (X1, BELT_Y + 0.37, BELT_Z), "rubber")
    # ---- посты: портал, цилиндр сверху, цветная табличка
    for x, mat in zip(STATIONS, ("rust", "brass", "steel")):
        for s in (-1, 1):
            f.box((x - 0.14, BELT_Y + s * 0.58 - 0.08, 0.3), (x + 0.14, BELT_Y + s * 0.58 + 0.08, 2.05), "hull", bevel=0.025)
        f.box((x - 0.2, BELT_Y - 0.68, 2.05), (x + 0.2, BELT_Y + 0.68, 2.25), "dark", bevel=0.025)
        f.lathe((x, BELT_Y, 2.25), [(0.2, 0), (0.2, 0.08), (0.15, 0.1), (0.15, 0.52), (0.18, 0.54), (0.18, 0.6), (0.05, 0.62)], 10, mat, base=False)
        f.ring((x, BELT_Y, 2.5), 0.14, 0.18, 0.04, 10, "dark", "Z")
    # бункер заряда над дозатором
    f.loft([(2.95, 0.12, 0.12, BELT_Y), (3.3, 0.3, 0.3, BELT_Y), (3.3, 0.24, 0.24, BELT_Y), (2.97, 0.08, 0.08, BELT_Y)], "brass")
    f.box((-0.04, BELT_Y - 0.04, 2.84), (0.04, BELT_Y + 0.04, 2.97), "steel")
    # ---- короб подачи слева: гильзы выходят из проёма
    f.box((-3.38, BELT_Y - 0.6, 0.3), (-2.72, BELT_Y + 0.6, 2.0), "hull", bevel=0.06)
    f.box((-3.4, BELT_Y - 0.62, 1.45), (-2.7, BELT_Y + 0.62, 1.52), "brass")
    f.box((-2.74, BELT_Y - 0.36, BELT_Z), (-2.71, BELT_Y + 0.36, BELT_Z + 0.42), "dark")
    f.loft([(2.0, 0.34, 0.5, BELT_Y), (2.5, 0.42, 0.62, BELT_Y), (2.5, 0.36, 0.56, BELT_Y), (2.02, 0.28, 0.44, BELT_Y)], "rust") if False else None
    f.box((-3.2, BELT_Y - 0.44, 2.0), (-2.9, BELT_Y + 0.44, 2.3), "rust", bevel=0.03)
    f.skull(-3.05, BELT_Y - 0.6, 1.2, 0.42, augmetic=False)
    f.gear((-3.05, BELT_Y - 0.62, 1.2), 0.24, 0.32, 0.04, 10, "brass", "Y")
    # ---- ящик приёма справа
    f.box((2.72, BELT_Y - 0.62, 0.3), (3.38, BELT_Y + 0.62, 1.05), "rust", bevel=0.03)
    f.box((2.76, BELT_Y - 0.56, 1.05), (3.34, BELT_Y + 0.56, 1.1), "dark")
    for k in range(7):
        for j in range(4):
            f.lathe((2.86 + j * 0.13, BELT_Y - 0.42 + k * 0.14, 1.1), [(0.05, 0), (0.05, 0.1), (0.018, 0.16)], 5, "brass", base=False)
    # ---- сзади: шкафы с лазпакетами, коллектор пневматики, мотор ленты
    f.box((-2.6, 0.62, 0.3), (1.5, 1.38, 1.35), "hull", bevel=0.04)
    f.box((-2.62, 0.6, 0.98), (1.52, 1.4, 1.05), "brass")
    for x in (-2.15, -1.25, -0.35, 0.55):
        f.box((x - 0.38, 0.6, 0.42), (x + 0.38, 0.62, 0.92), "dark")
        f.lathe((x + 0.25, 0.6, 0.67), [(0.03, 0), (0.03, -0.04)], 5, "brass", "Y", base=False)
    f.pipe([(-2.6, 1.0, 1.55), (1.5, 1.0, 1.55)], 0.06, 8, "steel")
    for x in STATIONS:
        f.pipe([(x, 1.0, 1.55), (x, 0.5, 2.0), (x, BELT_Y + 0.15, 2.55)], 0.03, 6, "rubber")
    f.lathe((2.1, 1.0, 0.3), [(0.32, 0), (0.32, 1.25), (0.2, 1.35)], 12, "hull", base=False)
    for z in (0.65, 1.0, 1.3):
        f.ring((2.1, 1.0, z), 0.3, 0.37, 0.05, 12, "dark", "Z")
    # манометр, пульт, печати
    f.box((-0.48, -1.42, 0.3), (0.48, -1.1, 1.05), "hull", bevel=0.03)
    f.box((-0.42, -1.43, 0.48), (0.42, -1.415, 0.95), "screen")
    f.seal((-3.1, BELT_Y - 0.62, 1.9), "Y", -1)
    f.seal((3.0, BELT_Y - 0.62, 0.95), "Y", -1)


def moving(m):
    # ---- гильзы на ленте: идут шагом ровно на PITCH, поэтому цикл бесшовный
    it = m.bone("rounds", (0, BELT_Y, BELT_Z))
    n = int((X1 - X0) / PITCH) + 1
    for k in range(n):
        x = X0 + k * PITCH
        # до дозатора гильза пустая и стальная, после него с латунным дном, после обжима с пулей
        it.lathe((x, BELT_Y, BELT_Z), [(0.1, 0), (0.1, 0.24), (0.075, 0.3)], 6, "brass", base=False)
        if x > STATIONS[1]:
            it.lathe((x, BELT_Y, BELT_Z + 0.3), [(0.06, 0), (0.06, 0.08), (0.015, 0.17)], 6, "steel", base=False)
    # ---- барабаны ленты
    for name, x in (("drum_a", X0), ("drum_b", X1)):
        d = m.bone(name, (x, BELT_Y, BELT_Z - 0.1))
        d.lathe((x, BELT_Y - 0.37, BELT_Z - 0.1), [(0.1, 0), (0.1, 0.74)], 8, "steel", "Y")
        d.box((x - 0.012, BELT_Y - 0.38, BELT_Z - 0.21), (x + 0.012, BELT_Y + 0.38, BELT_Z + 0.01), "dark")
    # ---- инструменты постов
    p1 = m.bone("press", (STATIONS[0], BELT_Y, 1.9))
    p1.lathe((STATIONS[0], BELT_Y, 1.5), [(0.05, 0), (0.05, 0.75)], 6, "steel", base=False)
    p1.box((STATIONS[0] - 0.16, BELT_Y - 0.16, 1.32), (STATIONS[0] + 0.16, BELT_Y + 0.16, 1.5), "dark", bevel=0.02)
    p2 = m.bone("nozzle", (STATIONS[1], BELT_Y, 1.9))
    p2.lathe((STATIONS[1], BELT_Y, 1.5), [(0.04, 0), (0.04, 0.75)], 6, "steel", base=False)
    p2.lathe((STATIONS[1], BELT_Y, 1.32), [(0.03, 0), (0.1, 0.2)], 8, "brass", base=False)
    p3 = m.bone("crimp", (STATIONS[2], BELT_Y, 1.9))
    p3.lathe((STATIONS[2], BELT_Y, 1.5), [(0.05, 0), (0.05, 0.75)], 6, "steel", base=False)
    p3.lathe((STATIONS[2], BELT_Y, 1.3), [(0.08, 0), (0.15, 0.1), (0.15, 0.2)], 10, "hull", base=False)
    p3.ring((STATIONS[2], BELT_Y, 1.42), 0.13, 0.17, 0.04, 10, "brass", "Z")
    # ---- мерцание огня дозатора и вращение обжимной головки на штоке выше не показываем отдельно
    c = m.bone("charge", (STATIONS[1], BELT_Y, 1.24))
    c.lathe((STATIONS[1], BELT_Y, 1.16), [(0.04, 0), (0.015, 0.16)], 5, "fire", base=False)


def pose(t):
    # 0..0.35 шаг ленты, потом посты опускаются и поднимаются
    u = min(1, t / 0.35)
    step = u * u * (3 - 2 * u)
    v = max(0, (t - 0.38) / 0.56)
    press = -0.3 * math.sin(math.pi * min(1, v)) if t > 0.38 else 0
    nozzle = -0.2 * math.sin(math.pi * min(1, v)) if t > 0.38 else 0
    crimp = -0.26 * math.sin(math.pi * min(1, v)) if t > 0.38 else 0
    glow = 1 if 0.5 < t < 0.8 else 0
    return {
        "rounds": {"pos": (PITCH * step, 0, 0)},
        "drum_a": {"rot": (0, 360 * step, 0)},
        "drum_b": {"rot": (0, 360 * step, 0)},
        "press": {"pos": (0, 0, press)},
        "nozzle": {"pos": (0, 0, nozzle)},
        "crimp": {"pos": (0, 0, crimp)},
        "charge": {"scale": (glow, glow, glow)},
    }


m = Machine("ammo_line")
frame(m)
moving(m)
sc, tris = m.build("WB_AmmoLine")
light_scene(sc, int(LOOP * 24))
auto_animate(m.objects, sc, pose, LOOP)
tracks = lambda: auto_tracks(pose, LOOP, STEPS)
print("костей:", len(m.objects), "треугольников:", tris)
