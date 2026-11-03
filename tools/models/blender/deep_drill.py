"""
Глубинный бур (deep_drill): 5×5×12. Решётчатая вышка с кронблоком, колонна бура вращается и шагает вниз, лебёдка сматывает трос.
У подножия роторный стол, два бака прометия с окошками, дизель с маховиком и рукав промывки; из устья летит порода.
"""
import math
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "kit.py"), encoding="utf-8").read())

LOOP, STEPS = 4.0, 64
TOP = 11.4          # высота кронблока
BX, BY = 0.0, 0.3   # ось скважины
STROKE = 2.2        # ход колонны за цикл
DECK = 1.25         # пол вышки


def frame(m):
    f = m.bone("frame")
    f.plinth(-2.48, -2.48, 2.48, 2.48)
    # ---- пол вышки на балках и роторный стол
    for s in (-1, 1):
        f.box((BX + s * 1.5 - 0.12, BY - 1.6, 0.3), (BX + s * 1.5 + 0.12, BY + 1.6, DECK - 0.08), "dark", bevel=0.02)
        f.box((BX - 1.6, BY + s * 1.5 - 0.12, 0.3), (BX + 1.6, BY + s * 1.5 + 0.12, DECK - 0.08), "dark", bevel=0.02)
    f.box((BX - 1.7, BY - 1.7, DECK - 0.08), (BX + 1.7, BY + 1.7, DECK), "hull", bevel=0.015)
    f.box((BX - 1.72, BY - 1.72, DECK - 0.04), (BX + 1.72, BY - 1.62, DECK + 0.01), "hazard")
    f.lathe((BX, BY, DECK), [(0.62, 0), (0.62, 0.14), (0.42, 0.2)], 14, "dark", base=False)
    # обсадная колонна уходит в грунт: видна под столом
    f.lathe((BX, BY, 0.3), [(0.26, 0), (0.26, 0.95)], 10, "steel", base=False)
    f.ring((BX, BY, 0.62), 0.24, 0.32, 0.1, 10, "brass", "Z")
    # ---- вышка: четыре ноги сходятся к кронблоку, пояса и раскосы
    legs = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    wide, narrow = 1.5, 0.5
    levels = [DECK + i * (TOP - DECK) / 5 for i in range(6)]

    def corner(z, sx, sy):
        k = (z - DECK) / (TOP - DECK)
        w = wide + (narrow - wide) * k
        return (BX + sx * w, BY + sy * w, z)

    for sx, sy in legs:
        f.beam(corner(DECK, sx, sy), corner(TOP, sx, sy), 0.14, 0.14, "red", bevel=0.012)
    for i, z in enumerate(levels):
        for j in range(4):
            a, b = legs[j], legs[(j + 1) % 4]
            f.beam(corner(z, *a), corner(z, *b), 0.07, 0.07, "red")
            if i < 5:
                zz = levels[i + 1]
                if i % 2 == 0:
                    f.beam(corner(z, *a), corner(zz, *b), 0.05, 0.05, "dark")
                else:
                    f.beam(corner(z, *b), corner(zz, *a), 0.05, 0.05, "dark")
    # лестница с задней стороны и площадка
    f.ladder(BX + 0.9, BY + 1.4, DECK, 5.0)
    z = levels[2]
    k = corner(z, 1, 1)[0] - BX
    f.box((BX - k - 0.5, BY + k, z - 0.05), (BX + k + 0.5, BY + k + 0.55, z), "dark", bevel=0.008)
    for x in (-k - 0.48, k + 0.48):
        f.box((BX + x - 0.015, BY + k + 0.52, z), (BX + x + 0.015, BY + k + 0.55, z + 0.36), "steel")
    f.box((BX - k - 0.48, BY + k + 0.52, z + 0.34), (BX + k + 0.48, BY + k + 0.55, z + 0.36), "steel")
    # ---- кронблок: рама и шкивы-пояса
    f.box((BX - 0.7, BY - 0.7, TOP), (BX + 0.7, BY + 0.7, TOP + 0.16), "hull", bevel=0.02)
    f.box((BX - 0.72, BY - 0.72, TOP + 0.04), (BX + 0.72, BY + 0.72, TOP + 0.09), "brass")
    f.box((BX - 0.5, BY - 0.12, TOP + 0.16), (BX - 0.38, BY + 0.12, TOP + 0.5), "dark")
    f.box((BX + 0.38, BY - 0.12, TOP + 0.16), (BX + 0.5, BY + 0.12, TOP + 0.5), "dark")
    f.lathe((BX, BY, TOP + 0.47), [(0.035, -0.5), (0.035, 0.5)], 6, "steel", "X")
    # красный огонь наверху
    f.lathe((BX, BY - 0.55, TOP + 0.16), [(0.06, 0), (0.08, 0.1), (0.04, 0.2)], 6, "eye", base=False)
    # ---- череп-герб на поясе вышки и пергаментные печати
    f.box((BX - 0.55, BY - 1.32, 3.4), (BX + 0.55, BY - 1.22, 4.4), "hull", bevel=0.02)
    f.skull(BX, BY - 1.32, 3.9, 0.7, augmetic=True)
    f.seal((BX - 0.42, BY - 1.32, 3.62), "Y", -1) if False else None
    # ---- баки прометия: окошки синие
    for x in (-1.86, -0.92):
        f.tank((x, -1.62, 0.3), 0.42, 1.65, 12, "hull", (0.2, 0.88), band_mat="brass")
        f.box((x - 0.07, -2.05, 0.6), (x + 0.07, -2.03, 1.75), "prometh")
        f.box((x - 0.1, -2.03, 0.57), (x + 0.1, -2.0, 1.78), "dark")
    f.pipe([(-1.86, -1.62, 2.4), (-1.86, -1.62, 2.55), (-0.92, -1.62, 2.55), (0.55, -1.15, 1.9), (1.36, -0.95, 1.3)], 0.05, 6, "rust")
    # ---- дизель справа спереди: блок, цилиндры, выхлоп
    f.box((0.75, -2.32, 0.3), (2.28, -0.8, 0.6), "dark", bevel=0.025)
    f.box((0.95, -2.2, 0.6), (2.08, -1.2, 1.34), "hull", bevel=0.03)
    for x in (1.2, 1.52, 1.84):
        f.lathe((x, -1.7, 1.34), [(0.14, 0), (0.14, 0.3), (0.09, 0.36)], 8, "rust", base=False)
        for j in range(2):
            f.ring((x, -1.7, 1.42 + j * 0.1), 0.13, 0.17, 0.025, 8, "dark", "Z")
    f.pipe([(1.84, -1.2, 1.25), (2.2, -1.1, 1.3), (2.22, -1.05, 3.0)], 0.075, 8, "rust")
    f.lathe((2.22, -1.05, 3.0), [(0.08, 0), (0.14, 0.06), (0.14, 0.34), (0.08, 0.4)], 8, "dark", base=False)
    # ---- лебёдка слева сзади
    f.box((-2.32, 0.52, 0.3), (-1.2, 2.3, 0.56), "dark", bevel=0.02)
    for y in (0.7, 2.1):
        f.box((-2.25, y - 0.1, 0.56), (-1.3, y + 0.1, 1.5), "hull", bevel=0.02)
    # ---- бункер породы и шлам
    f.box((1.15, 0.75, 0.3), (2.34, 2.3, 1.0), "rust", bevel=0.03)
    f.box((1.22, 0.82, 0.92), (2.27, 2.23, 1.01), "concrete")
    for x, y in ((1.5, 1.2), (1.95, 1.8), (1.75, 1.05), (1.45, 1.9), (2.05, 1.25)):
        f.lathe((x, y, 1.0), [(0.16, 0), (0.08, 0.1), (0.02, 0.15)], 5, "concrete", base=False)
    f.pipe([(BX + 0.32, BY + 0.05, 0.75), (1.1, 1.0, 0.9), (1.3, 1.2, 1.1)], 0.09, 8, "hull")
    # пульт на полу вышки
    f.box((BX - 1.62, BY + 0.5, DECK), (BX - 1.0, BY + 1.15, 2.2), "hull", bevel=0.02)
    f.box((BX - 1.0, BY + 0.58, 1.5), (BX - 0.985, BY + 1.07, 2.05), "screen")
    f.seal((BX - 0.98, BY + 0.72, 1.45), "X", 1)


def moving(m):
    # ---- колонна: кел-вал с гранями и верхний привод, вращается
    z0 = DECK + 0.2
    k = m.bone("kelly", (BX, BY, z0))
    k.lathe((BX, BY, z0 - 0.15), [(0.13, 0), (0.13, STROKE + 2.3)], 6, "steel", base=False)
    k.ring((BX, BY, z0 + 0.5), 0.11, 0.17, 0.08, 6, "brass", "Z")
    k.ring((BX, BY, z0 + 2.0), 0.11, 0.17, 0.08, 6, "brass", "Z")
    k.gear((BX, BY, z0 + 0.05), 0.2, 0.3, 0.1, 10, "dark", "Z")
    # ---- верхний привод: едет по вышке вместе с колонной, но не вращается
    z1 = z0 - 0.15 + STROKE + 2.3
    h = m.bone("topdrive", (BX, BY, z1))
    h.box((BX - 0.42, BY - 0.3, z1), (BX + 0.42, BY + 0.3, z1 + 0.62), "hull", bevel=0.03)
    h.box((BX - 0.44, BY - 0.32, z1 + 0.42), (BX + 0.44, BY + 0.32, z1 + 0.48), "brass")
    h.lathe((BX, BY, z1 + 0.62), [(0.16, 0), (0.16, 0.26), (0.08, 0.32)], 8, "rust", base=False)
    h.lathe((BX, BY, z1 + 0.94), [(0.03, 0), (0.03, TOP + 0.45 - z1 - 0.94)], 4, "dark", base=False)
    for s in (-1, 1):
        h.lathe((BX + s * 0.34, BY, z1 + 0.62), [(0.015, 0), (0.015, TOP + 0.45 - z1 - 0.62)], 3, "rubber", base=False)
    # ---- шкивы кронблока
    for i, x in enumerate((-0.2, 0.2)):
        s = m.bone(f"sheave_{i}", (BX + x, BY, TOP + 0.47))
        s.gear((BX + x, BY, TOP + 0.47), 0.18, 0.24, 0.1, 8, "brass", "X")
    # ---- барабан лебёдки
    d = m.bone("winch", (-1.78, 1.4, 1.02))
    d.lathe((-1.78, 1.4, 1.02), [(0.1, -0.62), (0.38, -0.6), (0.38, -0.5), (0.28, -0.48), (0.28, 0.48), (0.38, 0.5), (0.38, 0.6), (0.1, 0.62)], 12, "brass", "Y")
    for k_ in range(6):
        a = k_ * math.pi / 3
        d.beam((-1.78 + 0.28 * math.cos(a), 1.0, 1.02 + 0.28 * math.sin(a)), (-1.78 + 0.28 * math.cos(a), 1.8, 1.02 + 0.28 * math.sin(a)), 0.05, 0.05, "rubber")
    # ---- маховик дизеля
    w = m.bone("flywheel", (0.78, -1.7, 1.0))
    w.ring((0.78, -1.7, 1.0), 0.28, 0.42, 0.1, 14, "dark", "X")
    w.lathe((0.78, -1.7, 1.0), [(0.06, -0.08), (0.06, 0.08)], 6, "steel", "X")
    for j in range(4):
        a = j * math.pi / 2
        w.beam((0.78, -1.7, 1.0), (0.78, -1.7 + 0.32 * math.cos(a), 1.0 + 0.32 * math.sin(a)), 0.05, 0.08, "hull")
    # ---- порода: летит из устья в бункер
    for i in range(4):
        r = m.bone(f"rock_{i}", (1.3, 1.2, 1.1))
        r.lathe((1.3, 1.2, 1.1), [(0, -0.05), (0.05, -0.02), (0.05, 0.02), (0, 0.05)], 5, "concrete", cap=False)
    # ---- пламя дизельного выхлопа
    fl = m.bone("stack_flame", (2.22, -1.05, 3.4))
    fl.lathe((2.22, -1.05, 3.4), [(0.08, 0), (0.12, 0.06), (0.06, 0.2), (0, 0.32)], 6, "fire", base=False)


def pose(t):
    a = 2 * math.pi * t
    # колонна идёт вниз на STROKE и быстро поднимается
    u = (t / 0.82) if t < 0.82 else 1 - (t - 0.82) / 0.18
    drop = -STROKE * max(0, min(1, u))
    p = {
        "kelly": {"rot": (0, 0, 360 * 6 * t), "pos": (0, 0, drop)},
        "topdrive": {"pos": (0, 0, drop)},
        "sheave_0": {"rot": (720 * drop / STROKE, 0, 0)},
        "sheave_1": {"rot": (-720 * drop / STROKE, 0, 0)},
        "winch": {"rot": (0, 360 * drop / STROKE, 0)},
        "flywheel": {"rot": (360 * 8 * t, 0, 0)},
        "stack_flame": {"scale": (1, 1, 1 + 0.25 * math.sin(a * 7) * math.sin(a * 3))},
    }
    for i in range(4):
        k = (t * 3 + i / 4) % 1
        vis = 1 if k < 0.8 else 0
        p[f"rock_{i}"] = {"pos": (0.45 * k, 0.5 * k, 0.15 * math.sin(math.pi * k) - 0.32 * k * k), "scale": (vis, vis, vis)}
    return p


m = Machine("deep_drill")
frame(m)
moving(m)
sc, tris = m.build("WB_DeepDrill")
light_scene(sc, int(LOOP * 24))
auto_animate(m.objects, sc, pose, LOOP)
tracks = lambda: auto_tracks(pose, LOOP, STEPS)
print("костей:", len(m.objects), "треугольников:", tris)
