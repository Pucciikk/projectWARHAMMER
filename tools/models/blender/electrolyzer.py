"""
Электролизёр (electrolyzer): 3×3×3. Две клетки с колонной воды, по которой поднимаются пузыри; сверху токосъёмная шина,
между шинами бьёт разряд; сзади вентилятор охлаждения; по бокам баллоны водорода и кислорода.
"""
import math
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "kit.py"), encoding="utf-8").read())

LOOP = 2.0
CELLS = ((-0.52, -0.25), (0.52, -0.25))   # x, y колонн
Z0, Z1 = 0.62, 2.05                       # низ и верх рабочей части колонны
BUBBLES = 6


def frame(m):
    f = m.bone("frame")
    f.plinth(-1.48, -1.48, 1.48, 1.48)
    # станина и клетки
    f.box((-1.15, -0.85, 0.3), (1.15, 0.75, 0.62), "hull", bevel=0.04)
    f.box((-1.17, -0.87, 0.5), (1.17, 0.77, 0.56), "brass")
    for x, y in CELLS:
        f.lathe((x, y, Z0), [(0.46, 0), (0.46, 0.05), (0.2, 0.08)], 12, "dark", base=False)
        f.lathe((x, y, Z0), [(0.2, 0), (0.2, Z1 - Z0)], 12, "water", base=False)                  # столб воды
        for k in range(6):                                                                         # прутья клетки
            a = k * math.pi / 3 + math.pi / 6
            f.lathe((x + 0.42 * math.cos(a), y + 0.42 * math.sin(a), Z0), [(0.025, 0), (0.025, Z1 - Z0)], 4, "steel", base=False)
        for z in (Z0 + 0.48, Z0 + 0.95):
            f.ring((x, y, z), 0.4, 0.45, 0.04, 12, "brass", "Z")
        f.lathe((x, y, Z1), [(0.46, 0), (0.46, 0.1), (0.3, 0.16), (0.22, 0.32), (0.22, 0.4)], 12, "hull", base=False)
    # шина с токосъёмниками и катушки
    f.box((-1.05, -0.45, 2.45), (1.05, -0.05, 2.55), "dark", bevel=0.02)
    f.box((-1.07, -0.47, 2.48), (1.07, -0.03, 2.51), "brass")
    for s in (-1, 1):
        f.lathe((s * 0.24, -0.25, 2.55), [(0.1, 0), (0.1, 0.05), (0.06, 0.09), (0.06, 0.3), (0.1, 0.33)], 8, "brass", base=False)
        for k in range(4):
            f.ring((s * 0.24, -0.25, 2.65 + k * 0.05), 0.07, 0.1, 0.022, 8, "rust", "Z")
    # задняя стенка, кожух вентилятора, пульт
    f.box((-1.15, 0.75, 0.3), (1.15, 1.2, 2.4), "hull", bevel=0.05)
    f.box((-1.17, 0.73, 2.15), (1.17, 1.22, 2.22), "brass")
    f.ring((0, 1.22, 1.35), 0.55, 0.66, 0.1, 16, "dark", "Y")
    f.box((-0.72, 1.2, 0.62), (0.72, 1.24, 0.72), "dark")
    f.box((-0.72, 1.2, 1.98), (0.72, 1.24, 2.08), "dark")
    # переходная панель спереди: экран, манометры, рубильник, череп
    f.box((-0.34, -0.87, 0.64), (0.34, -0.6, 1.5), "hull", bevel=0.03)
    f.box((-0.26, -0.88, 0.85), (0.26, -0.865, 1.3), "screen")
    f.skull(0, -0.72, 1.74, 0.42)
    for x, z in ((-0.86, 1.2), (0.86, 1.2)):
        f.box((x - 0.2, -0.6, z - 0.2), (x + 0.2, -0.5, z + 0.2), "dark", bevel=0.015)
        f.lathe((x, -0.6, z), [(0.13, 0), (0.13, -0.04), (0.11, -0.06)], 12, "brass", "Y", base=False)
        f.lathe((x, -0.66, z), [(0.09, 0), (0.09, -0.004)], 12, "glass", "Y", base=False)
    # баллоны газа: водород слева, кислород справа
    for s, band in ((-1, "brass"), (1, "red")):
        f.tank((s * 1.2, 0.72, 0.3), 0.22, 1.5, 10, "steel", (0.2, 0.55, 0.85), band_mat=band)
        f.pipe([(s * 0.52, -0.25, 2.3), (s * 0.95, -0.2, 2.3), (s * 1.2, 0.4, 2.15), (s * 1.2, 0.72, 2.05)], 0.05, 6, "rust")
        f.ring((s * 1.2, 0.72, 2.0), 0.0 + 0.04, 0.08, 0.05, 6, "dark", "Z")
    # слив и водяная подача
    f.pipe([(-1.15, -0.5, 0.5), (-1.42, -0.5, 0.5), (-1.42, -1.3, 0.5), (-1.42, -1.3, 0.3)], 0.06, 8, "rust")
    f.ring((-1.42, -0.9, 0.56), 0.06, 0.1, 0.03, 8, "red", "Z")
    f.seal((-0.9, -0.87, 0.92), "Y", -1)
    f.seal((1.17, 0.2, 1.55), "X", 1)


def moving(m):
    # ---- пузыри: кольцами вокруг столба, поднимаются на всю высоту и повторяются
    for c, (x, y) in enumerate(CELLS):
        for b in range(BUBBLES):
            n = m.bone(f"bubble_{c}_{b}", (x, y, Z0 + 0.1))
            a = b * 2.4 + c
            bx, by = x + 0.25 * math.cos(a), y + 0.25 * math.sin(a)
            n.lathe((bx, by, Z0 + 0.1), [(0.0, -0.045), (0.04, -0.02), (0.04, 0.02), (0.0, 0.045)], 6, "glass", cap=False)
    # ---- разряд между катушками: мерцает
    arc = m.bone("arc", (0, -0.25, 2.92))
    arc.beam((-0.2, -0.25, 2.92), (-0.06, -0.21, 3.02), 0.022, 0.022, "screen")
    arc.beam((-0.06, -0.21, 3.02), (0.08, -0.29, 2.9), 0.022, 0.022, "screen")
    arc.beam((0.08, -0.29, 2.9), (0.2, -0.25, 2.98), 0.022, 0.022, "screen")
    # ---- вентилятор
    fan = m.bone("fan", (0, 1.28, 1.35))
    fan.lathe((0, 1.25, 1.35), [(0.1, 0), (0.1, 0.05), (0.05, 0.08)], 8, "dark", "Y", base=False)
    for k in range(5):
        a = k * 2 * math.pi / 5
        fan.beam((0, 1.28, 1.35), (0.5 * math.cos(a), 1.28, 1.35 + 0.5 * math.sin(a)), 0.15, 0.025, "brass")
    # ---- стрелки манометров
    for i, x in enumerate((-0.86, 0.86)):
        s = m.bone(f"needle_{i + 1}", (x, -0.67, 1.2))
        s.box((x - 0.005, -0.674, 1.195), (x + 0.075, -0.67, 1.205), "eye")


def state_bubble(t, b):
    u = (t * 2 + b / BUBBLES) % 1
    return u * (Z1 - Z0 - 0.2), 0.0 if u > 0.92 or u < 0.03 else 1.0


def arc_scale(t):
    k = math.sin(38 * math.pi * t) * math.sin(14 * math.pi * t)
    return 1.0 if k > -0.25 else 0.0


def animate(objs, sc):
    frames = int(LOOP * 24)
    for f in range(frames + 1):
        t = f / frames
        for c in range(2):
            for b in range(BUBBLES):
                n = f"bubble_{c}_{b}"
                z, vis = state_bubble(t, b)
                objs[n].location = (CELLS[c][0], CELLS[c][1], Z0 + 0.1 + z)
                objs[n].scale = (vis, vis, vis)
                objs[n].keyframe_insert("location", frame=f + 1)
                objs[n].keyframe_insert("scale", frame=f + 1)
        s = arc_scale(t)
        objs["arc"].scale = (s, s, s)
        objs["arc"].keyframe_insert("scale", frame=f + 1)
        objs["fan"].rotation_euler = (0, 2 * math.pi * 2 * t, 0)
        objs["fan"].keyframe_insert("rotation_euler", frame=f + 1)
    sc.frame_set(1)


def tracks():
    steps = 48
    tr = {}
    for c in range(2):
        for b in range(BUBBLES):
            pos, sca = {}, {}
            for i in range(steps + 1):
                t = i / steps
                key = f"{LOOP * t:.4f}"
                z, vis = state_bubble(t, b)
                pos[key] = [0, round(z * 16, 3), 0]
                sca[key] = [vis, vis, vis]
            tr[f"bubble_{c}_{b}"] = {"position": pos, "scale": sca}
    arc = {}
    n1, n2 = {}, {}
    for i in range(steps + 1):
        t = i / steps
        key = f"{LOOP * t:.4f}"
        s = arc_scale(t)
        arc[key] = [s, s, s]
        a = 2 * math.pi * t
        n1[key] = [0, 0, round(-110 + 14 * math.sin(a) + 4 * math.sin(9 * a), 3)]
        n2[key] = [0, 0, round(-75 + 10 * math.sin(a + 2) + 5 * math.sin(7 * a), 3)]
    tr["arc"] = {"scale": arc}
    tr["needle_1"] = {"rotation": n1}
    tr["needle_2"] = {"rotation": n2}
    tr["fan"] = {"rotation": {f"{LOOP * i / 8:.4f}": [0, 0, 90.0 * i] for i in range(9)}}
    return tr, LOOP


m = Machine("electrolyzer")
frame(m)
moving(m)
sc, tris = m.build("WB_Electrolyzer")
light_scene(sc, int(LOOP * 24))
animate(m.objects, sc)
print("костей:", len(m.objects), "треугольников:", tris)
