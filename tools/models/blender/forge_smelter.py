"""
Плавильня Кузни (forge_smelter): 3×3×3. Круглая кирпичная печь с тигелем на цапфах: тигель наклоняется и льёт металл в изложницы,
которые шагают по столу; кожаные мехи качают воздух. Сзади труба.
"""
import math
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "kit.py"), encoding="utf-8").read())

LOOP, STEPS = 5.0, 60
PZ = 1.62             # ось тигля
CY = 0.1              # ось печи
MOULD_Z = 0.62


def frame(m):
    f = m.bone("frame")
    f.plinth(-1.48, -1.48, 1.48, 1.48)
    # печь: кирпичный горн с поясами и окном топки
    f.lathe((0, CY, 0.3), [(1.0, 0), (1.0, 0.16), (0.88, 0.24), (0.84, 0.92), (0.92, 1.0), (0.92, 1.08), (0.7, 1.12), (0.62, 1.05)], 18, "brick", cap=False)
    f.lathe((0, CY, 1.34), [(0.62, 0), (0.62, 0.02)], 18, "fire", base=False)
    for z in (0.62, 1.05):
        f.ring((0, CY, z), 0.84, 0.92, 0.07, 18, "hull", "Z")
    f.box((-0.28, CY - 0.92, 0.42), (0.28, CY - 0.8, 0.8), "dark", bevel=0.02)
    f.box((-0.22, CY - 0.93, 0.47), (0.22, CY - 0.91, 0.75), "fire")
    for x in (-0.1, 0.1):
        f.box((x - 0.012, CY - 0.94, 0.45), (x + 0.012, CY - 0.92, 0.77), "dark")
    # портал тигля
    for s in (-1, 1):
        a, b = sorted((s * 0.88, s * 1.12))
        f.wedge((a, CY - 0.28, 0.3), (b, CY + 0.28), (a, CY - 0.12, PZ + 0.12), (b, CY + 0.12), "hull")
        f.ring((s * 1.12, CY, PZ), 0.06, 0.15, 0.04, 10, "brass")
    # стол изложниц спереди
    f.box((-1.3, -1.42, 0.3), (1.3, -0.72, MOULD_Z - 0.06), "dark", bevel=0.02)
    for x in (-1.2, 1.2):
        f.box((x - 0.03, -1.4, MOULD_Z - 0.06), (x + 0.03, -0.74, MOULD_Z), "steel")
    # кожух мехов слева и труба сзади
    f.box((-1.42, 0.45, 0.3), (-0.82, 1.3, 0.58), "dark", bevel=0.02)
    f.pipe([(-1.1, 0.55, 0.62), (-1.05, 0.28, 0.62), (-0.86, 0.28, 0.62)], 0.06, 6, "rust")
    f.lathe((0.72, 0.98, 0.3), [(0.3, 0), (0.3, 0.1), (0.2, 0.2), (0.2, 2.15), (0.27, 2.2), (0.27, 2.32), (0.2, 2.35)], 10, "rust", base=False)
    for z in (1.2, 1.9):
        f.ring((0.72, 0.98, z), 0.18, 0.24, 0.06, 10, "brass", "Z")
    f.pipe([(0.32, 0.6, 1.0), (0.6, 0.85, 1.05)], 0.1, 6, "rust")
    # череп и печать
    f.skull(0, CY - 0.82, 1.12, 0.36, augmetic=False)
    f.seal((-0.55, CY - 0.75, 0.95), "Y", -1)


def moving(m):
    # ---- тигель
    c = m.bone("crucible", (0, CY, PZ))
    c.lathe((0, CY, PZ - 0.32), [(0.22, 0), (0.34, 0.1), (0.38, 0.5), (0.42, 0.56), (0.34, 0.56), (0.3, 0.2)], 12, "hull", cap=False)
    c.lathe((0, CY, PZ + 0.04), [(0.3, 0), (0.3, 0.01)], 12, "fire", base=False)
    c.ring((0, CY, PZ), 0.36, 0.46, 0.1, 12, "dark", "Z")
    for s in (-1, 1):
        c.lathe((s * 0.42, CY, PZ), [(0.07, 0), (0.07, s * 0.68)], 8, "steel", "X")
    c.gear((1.2, CY, PZ), 0.2, 0.28, 0.06, 10, "brass", "X")
    # ---- струя металла
    p = m.bone("pour", (0, CY - 0.62, PZ - 0.05))
    p.lathe((0, CY - 0.62, MOULD_Z + 0.07), [(0.03, 0), (0.05, PZ - 0.05 - MOULD_Z - 0.07)], 6, "fire", base=False)
    # ---- изложницы шагают по столу: цикл замыкается на один шаг
    t = m.bone("moulds", (0, -1.07, MOULD_Z))
    for k in range(5):
        x = -1.1 + k * 0.55
        t.box((x - 0.2, -1.32, MOULD_Z), (x + 0.2, -0.82, MOULD_Z + 0.09), "dark", bevel=0.012)
        t.box((x - 0.15, -1.27, MOULD_Z + 0.09), (x + 0.15, -0.87, MOULD_Z + 0.1), "fire" if x > 0 else "steel")
    # ---- мехи: верхняя доска качается
    b = m.bone("bellows", (-1.12, 1.25, 0.72))
    b.plate([(1.25, 0.72), (1.25, 0.82), (0.5, 0.9), (0.5, 0.8)], -1.38, -0.86, "rust")
    b.plate([(1.25, 0.66), (1.25, 0.72), (0.5, 0.8), (0.5, 0.62)], -1.34, -0.9, "rubber")
    # ---- факел
    fl = m.bone("stack_flame", (0.72, 0.98, 2.68))
    fl.lathe((0.72, 0.98, 2.68), [(0.13, 0), (0.09, 0.15), (0.02, 0.36)], 6, "fire", base=False)


def smooth(x):
    return x * x * (3 - 2 * x)


def seg(t, a, b):
    return smooth(max(0.0, min(1.0, (t - a) / (b - a))))


def pose(t):
    tilt = seg(t, 0.15, 0.32) * (1 - seg(t, 0.62, 0.8))
    pour = 1 if 0.32 <= t < 0.62 else 0
    step = seg(t, 0.82, 1.0)
    a = 2 * math.pi * t
    return {
        "crucible": {"rot": (42 * tilt, 0, 0)},
        "pour": {"scale": (pour, pour, pour)},
        "moulds": {"pos": (0.55 * step, 0, 0)},
        "bellows": {"rot": (9 * math.sin(3 * a), 0, 0)},
        "stack_flame": {"scale": (1, 1, 1 + 0.3 * math.sin(3 * a) + 0.15 * math.sin(11 * a))},
    }


m = Machine("forge_smelter")
frame(m)
moving(m)
sc, tris = m.build("WB_ForgeSmelter")
light_scene(sc, int(LOOP * 24))
auto_animate(m.objects, sc, pose, LOOP)
tracks = lambda: auto_tracks(pose, LOOP, STEPS)
print("костей:", len(m.objects), "треугольников:", tris)
