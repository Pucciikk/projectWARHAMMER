"""
Ручной пресс (manual_press): 3×2×3. Винтовой пресс на дубовой станине: верхняя балка с гайкой, винт с крестовиной,
ползун бьёт по матрице. Анимация «work.strike» запускается ударом игрока, цикла нет.
Шаблон: ядро в середине переднего ряда; при глубине 2 смещение ядра 0,5.
"""
import math
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "kit.py"), encoding="utf-8").read())

LOOP, STEPS = 0.7, 28
AX, AY = 0.0, 0.0     # ось винта
ANVIL = 0.84          # верх матрицы
TOP = 2.3             # низ верхней балки
RAM_REST = 1.42       # низ ползуна в покое


def frame(m):
    f = m.bone("frame")
    # ---- каменная станина и деревянный настил
    f.box((-1.48, -0.98, 0), (1.48, 0.98, 0.2), "concrete", bevel=0.04)
    f.box((-1.4, -0.9, 0.2), (1.4, 0.9, 0.36), "wood", bevel=0.02)
    for x in (-1.15, -0.75, -0.35, 0.05, 0.45, 0.85, 1.25):
        f.box((x - 0.01, -0.91, 0.2), (x + 0.01, 0.91, 0.362), "dark")
    # ---- стойки: два тёмных дубовых столба с железной обвязкой
    for x in (-0.86, 0.86):
        f.box((x - 0.16, -0.22, 0.36), (x + 0.16, 0.22, 2.96), "wood", bevel=0.025)
        for z in (0.56, 1.5, 2.48):
            f.box((x - 0.18, -0.24, z), (x + 0.18, 0.24, z + 0.07), "dark")
            for s in (-1, 1):
                f.bolt((x + s * 0.11, -0.24, z + 0.035), "Y", 0.022, -0.016, "steel")
        for s in (-1, 1):
            f.wedge((x - 0.1, s * 0.22 - (0.42 if s < 0 else 0), 0.36), (x + 0.1, s * 0.22 + (0.42 if s > 0 else 0)),
                    (x - 0.1, s * 0.22 - (0.02 if s < 0 else 0), 0.9), (x + 0.1, s * 0.22 + (0.02 if s > 0 else 0)), "wood")
    # ---- верхняя балка и гайка
    f.box((-1.14, -0.26, TOP), (1.14, 0.26, TOP + 0.44), "wood", bevel=0.03)
    for x in (-0.86, 0.86):
        f.box((x - 0.2, -0.28, TOP + 0.12), (x + 0.2, 0.28, TOP + 0.34), "dark")
    f.lathe((AX, AY, TOP - 0.1), [(0.2, 0), (0.2, 0.68), (0.14, 0.72)], 10, "brass", base=False)
    f.ring((AX, AY, TOP + 0.1), 0.18, 0.24, 0.1, 10, "dark", "Z")
    # ---- направляющие ползуна
    for x in (-0.56, 0.56):
        f.lathe((x, 0, 0.36), [(0.035, 0), (0.035, TOP - 0.36)], 6, "steel", base=False)
    # ---- матрица
    f.box((-0.46, -0.42, 0.36), (0.46, 0.42, ANVIL - 0.1), "dark", bevel=0.02)
    f.lathe((AX, AY, ANVIL - 0.1), [(0.3, 0), (0.3, 0.1)], 12, "steel", base=False)
    f.ring((AX, AY, ANVIL), 0.2, 0.3, 0.012, 12, "brass", "Z")
    # ---- заготовка и готовые шестерни рядом
    f.gear((1.2, -0.48, 0.42), 0.13, 0.18, 0.05, 8, "brass", "Z")
    f.gear((1.2, -0.48, 0.48), 0.13, 0.18, 0.05, 8, "brass", "Z", phase=20)
    f.box((-1.32, -0.74, 0.36), (-0.92, -0.26, 0.44), "steel", bevel=0.008)
    f.box((-1.28, -0.7, 0.44), (-0.96, -0.3, 0.5), "steel", bevel=0.008)
    f.seal((0.86, -0.22, 1.25), "Y", -1)
    f.skull(0, -0.2, TOP + 0.21, 0.26, augmetic=False)


def moving(m):
    # ---- ползун с направляющими втулками
    r = m.bone("ram", (AX, AY, RAM_REST))
    r.box((-0.62, -0.18, RAM_REST), (0.62, 0.18, RAM_REST + 0.2), "dark", bevel=0.02)
    r.box((-0.64, -0.2, RAM_REST + 0.07), (0.64, 0.2, RAM_REST + 0.13), "brass")
    for x in (-0.56, 0.56):
        r.lathe((x, 0, RAM_REST - 0.02), [(0.07, 0), (0.07, 0.25)], 8, "steel")
    r.lathe((AX, AY, RAM_REST - 0.14), [(0.2, 0), (0.25, 0.14)], 10, "steel", base=True)
    # ---- винт и крестовина с грузами: вращается и опускается
    s = m.bone("screw", (AX, AY, RAM_REST + 0.2))
    s.lathe((AX, AY, RAM_REST + 0.2), [(0.09, 0), (0.09, TOP + 0.66 - RAM_REST - 0.2)], 8, "steel", base=False)
    for k in range(13):       # нарезка
        z = RAM_REST + 0.4 + k * 0.095
        s.ring((AX, AY, z), 0.085, 0.115, 0.022, 8, "dark", "Z")
    bar = TOP + 0.66
    s.lathe((AX, AY, bar), [(0.11, 0), (0.11, 0.14), (0.06, 0.18)], 8, "dark", base=False)
    for sg in (-1, 1):
        s.lathe((AX, AY, bar + 0.07), [(0.028, sg * 0.0), (0.028, sg * 0.9)], 5, "dark", "X", cap=False)
        s.lathe((AX + sg * 0.98, AY, bar + 0.07), [(0, -0.12), (0.09, -0.08), (0.11, 0), (0.09, 0.08), (0, 0.12)], 8, "rust", "X", cap=False)


def pose(t):
    # удар: 0→0.22 разгон вниз, удар, 0.3–1 возврат
    if t < 0.24:
        k = t / 0.24
        u = k * k
    elif t < 0.3:
        u = 1.0
    else:
        k = (t - 0.3) / 0.7
        u = 1 - k * k * (3 - 2 * k)
    drop = (RAM_REST - 0.14 - ANVIL) * u
    return {
        "ram": {"pos": (0, 0, -drop)},
        "screw": {"pos": (0, 0, -drop), "rot": (0, 0, -720 * u)},
    }


m = Machine("manual_press")
frame(m)
moving(m)
sc, tris = m.build("WB_ManualPress")
light_scene(sc, int(LOOP * 24))
auto_animate(m.objects, sc, pose, LOOP)
tracks = lambda: auto_tracks(pose, LOOP, STEPS)
print("костей:", len(m.objects), "треугольников:", tris)
