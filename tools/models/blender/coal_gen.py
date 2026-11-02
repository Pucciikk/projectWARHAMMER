"""
Угольный генераториум (coal_gen): 3×3×4. Котёл с топкой, бункер и шнек подачи, паровой цилиндр с шатуном и маховиком,
якорь генератора с искрением, центробежный регулятор наверху, труба.
"""
import math
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "kit.py"), encoding="utf-8").read())

LOOP = 2.0
AX, AZ = 0.55, 1.25   # ось маховика: y, z; плоскость X ниже
FX = 1.2              # плоскость маховика
CRANK, ROD = 0.28, 1.0
CYL_X = 1.2


def frame(m):
    f = m.bone("frame")
    f.plinth(-1.48, -1.48, 1.48, 1.48)
    # ---- котёл: лежачий цилиндр на сёдлах, топка спереди
    c = (-0.25, 0.2, 1.4)
    f.lathe((c[0], -1.05, c[2]), [(0.74, 0), (0.86, 0.08), (0.86, 2.2), (0.74, 2.3)], 18, "hull", "Y")
    for y in (-0.55, 0.15, 0.85):
        f.ring((c[0], y, c[2]), 0.82, 0.9, 0.09, 18, "brass", "Y")
    for k in range(10):
        a = k * math.pi / 5
        f.bolt((c[0] + 0.88 * math.cos(a), -0.2, c[2] + 0.88 * math.sin(a)), "Z", 0.03, 0.02, "steel")
    for y in (-0.7, 0.8):
        f.wedge((c[0] - 0.75, y - 0.12, 0.3), (c[0] + 0.75, y + 0.12), (c[0] - 0.55, y - 0.09, 0.85), (c[0] + 0.55, y + 0.09), "dark")
    # топка: стальной щит, дверца с огнём (дверца подвижна), зольник
    f.box((-1.1, -1.25, 0.3), (0.6, -1.03, 1.98), "hull", bevel=0.05)
    f.box((-0.66, -1.27, 0.62), (0.16, -1.25, 1.16), "dark")
    f.box((-0.6, -1.275, 0.68), (0.1, -1.26, 1.1), "fire")
    f.box((-0.66, -1.3, 0.34), (0.16, -1.25, 0.52), "dark", bevel=0.012)
    f.skull(-0.25, -1.25, 1.52, 0.5)
    f.gear((-0.25, -1.27, 1.52), 0.28, 0.37, 0.04, 10, "brass", "Y")
    # ---- бункер угля и наклонный шнек к топке (шнек виден через окно)
    f.loft([(2.15, 0.34, 0.34, -0.8), (2.72, 0.6, 0.55, -0.8), (2.72, 0.52, 0.47, -0.8), (2.18, 0.28, 0.28, -0.8)], "rust")
    for i, (x, y, h) in enumerate(((-0.15, -0.9, 0.08), (0.14, -0.72, 0.1), (0.0, -0.98, 0.06), (0.2, -0.95, 0.08), (-0.2, -0.65, 0.09))):
        f.lathe((x, y, 2.6), [(0.14, 0), (0.1, h), (0.04, h + 0.06)], 5, "dark", phase=i, base=False)
    f.box((-0.34, -1.14, 1.95), (0.34, -0.46, 2.18), "dark", bevel=0.02)
    f.lathe((0.6, -0.8, 2.3), [(0.2, 0), (0.2, 0.3)], 10, "hull", "X")           # мотор шнека
    # ---- труба
    f.lathe((-0.9, 0.95, 2.1), [(0.32, 0), (0.32, 0.1), (0.2, 0.2), (0.2, 1.75), (0.27, 1.8), (0.27, 1.92), (0.2, 1.95)], 10, "rust", base=False)
    for z in (2.65, 3.2):
        f.ring((-0.9, 0.95, z), 0.18, 0.24, 0.06, 10, "brass", "Z")
    f.pipe([(-0.9, 0.6, 2.05), (-0.9, 0.95, 2.1)], 0.18, 8, "rust")
    # ---- паропровод: купол и труба к цилиндру
    f.lathe((0.15, 0.5, 2.15), [(0.22, 0), (0.22, 0.18), (0.14, 0.3), (0.06, 0.36)], 10, "brass", base=False)
    f.pipe([(0.15, 0.5, 2.3), (0.15, 1.3, 2.28), (CYL_X, 1.3, 1.88), (CYL_X, 1.3, AZ + 0.2)], 0.06, 8, "steel")
    # ---- станина паровой машины: цилиндр сзади, параллели, подшипник маховика
    f.box((0.72, -0.25, 0.3), (1.05, 1.42, 0.92), "dark", bevel=0.03)
    f.box((0.86, -0.1, 0.92), (1.05, 0.9, AZ + 0.2), "hull", bevel=0.02)
    f.lathe((CYL_X, 1.0, AZ), [(0.14, 0), (0.14, 0.06), (0.2, 0.08), (0.2, 0.46), (0.14, 0.48)], 12, "brass", "Y")
    f.ring((CYL_X, 1.25, AZ), 0.19, 0.23, 0.05, 12, "dark", "Y")
    for dz in (-0.14, 0.14):
        f.box((CYL_X - 0.04, 0.3, AZ + dz - 0.022), (CYL_X + 0.04, 1.02, AZ + dz + 0.022), "steel")
    f.box((1.0, 0.3, AZ - 0.2), (1.28, 0.38, AZ + 0.2), "dark")
    f.box((1.0, 0.98, AZ - 0.2), (1.28, 1.05, AZ + 0.2), "dark")
    f.lathe((1.05, -0.45, AZ), [(0.17, 0), (0.17, -0.15)], 8, "dark", "X")
    # ---- генератор: корпус и шины к щиту
    f.box((-0.05, -1.0, 0.3), (0.55, -0.35, 0.38), "dark")
    f.ring((0.72, -0.45, AZ), 0.3, 0.46, 0.46, 16, "hull")
    f.ring((0.72, -0.45, AZ), 0.44, 0.49, 0.06, 16, "brass")
    f.pipe([(0.6, -0.82, AZ), (0.6, -1.2, AZ - 0.2), (0.6, -1.2, 0.4)], 0.03, 6, "rubber")
    f.box((0.46, -1.42, 0.3), (1.2, -1.1, 1.3), "hull", bevel=0.03)
    f.box((0.54, -1.43, 0.55), (1.12, -1.415, 1.15), "screen")
    # ---- опора центробежного регулятора
    f.lathe((0.15, 0.5, 2.45), [(0.05, 0), (0.05, 0.1)], 6, "steel", base=False)
    f.seal((-0.95, -1.25, 1.8), "Y", -1)
    f.seal((0.76, -1.42, 1.2), "Y", -1)


def moving(m):
    # ---- маховик с якорем генератора на одном валу
    w = m.bone("flywheel", (FX, AX - 1.0, AZ))
    y = AX - 1.0
    w.ring((FX, y, AZ), 0.44, 0.58, 0.16, 24, "hull")
    w.ring((FX, y, AZ), 0.54, 0.59, 0.05, 24, "brass")
    w.lathe((0.9, y, AZ), [(0.05, 0), (0.05, 0.42)], 8, "steel", "X")
    w.lathe((FX - 0.07, y, AZ), [(0.13, 0), (0.13, 0.14)], 8, "dark", "X")
    w.lathe((FX + 0.08, y + CRANK, AZ), [(0.05, 0), (0.05, 0.1)], 8, "steel", "X")
    w.box((FX + 0.06, y + 0.05, AZ - 0.06), (FX + 0.09, y + CRANK + 0.06, AZ + 0.06), "dark", bevel=0.01)
    for k in range(5):
        a = k * 2 * math.pi / 5
        w.beam((FX, y, AZ), (FX, y + 0.48 * math.cos(a), AZ + 0.48 * math.sin(a)), 0.06, 0.06, "hull")
    # якорь: крутится в корпусе генератора
    ar = m.bone("armature", (0.72, -0.45, AZ))
    ar.lathe((0.5, -0.45, AZ), [(0.27, 0), (0.27, 0.44)], 8, "rust", "X")
    for k in range(4):
        a = k * math.pi / 2
        ar.box((0.5, -0.45 + 0.27 * math.cos(a) - 0.03, AZ + 0.27 * math.sin(a) - 0.03), (0.94, -0.45 + 0.27 * math.cos(a) + 0.03, AZ + 0.27 * math.sin(a) + 0.03), "brass")
    # ---- шатун и ползун
    y0 = y + CRANK
    rod = m.bone("conrod", (FX + 0.2, y0, AZ))
    rod.ring((FX + 0.2, y0, AZ), 0.05, 0.09, 0.05, 10, "dark")
    rod.box((FX + 0.18, y0 + 0.07, AZ - 0.032), (FX + 0.22, y0 + ROD - 0.05, AZ + 0.032), "steel", bevel=0.005)
    rod.ring((FX + 0.2, y0 + ROD, AZ), 0.03, 0.065, 0.05, 10, "dark")
    ch = m.bone("crosshead", (FX + 0.2, y0 + ROD, AZ))
    y1 = y0 + ROD
    ch.box((FX + 0.15, y1 - 0.09, AZ - 0.11), (FX + 0.25, y1 + 0.09, AZ + 0.11), "dark", bevel=0.012)
    ch.lathe((FX + 0.2, y1 + 0.08, AZ), [(0.03, 0), (0.03, 0.42)], 6, "steel", "Y")
    # ---- центробежный регулятор: два шара на рычагах
    g = m.bone("governor", (0.15, 0.5, 2.6))
    g.lathe((0.15, 0.5, 2.5), [(0.025, 0), (0.025, 0.5)], 6, "steel", base=False)
    for s in (-1, 1):
        g.beam((0.15, 0.5, 2.96), (0.15 + s * 0.26, 0.5, 2.68), 0.025, 0.025, "brass")
        g.lathe((0.15 + s * 0.26, 0.5, 2.64), [(0.0, -0.06), (0.07, -0.03), (0.07, 0.03), (0.0, 0.06)], 8, "brass", cap=False)
    # ---- искрение на щётках и факел
    arc = m.bone("arc", (0.25, -0.45, AZ))
    arc.beam((0.27, -0.72, AZ + 0.22), (0.2, -0.62, AZ + 0.14), 0.02, 0.02, "screen")
    arc.beam((0.2, -0.62, AZ + 0.14), (0.28, -0.55, AZ + 0.05), 0.02, 0.02, "screen")
    fl = m.bone("stack_flame", (-0.9, 0.95, 4.05))
    fl.lathe((-0.9, 0.95, 4.05), [(0.13, 0), (0.09, 0.16), (0.02, 0.36)], 6, "fire", base=False)


def state(t):
    a = 2 * math.pi * t
    yc = AX - 1.0
    py, pz = yc + CRANK * math.cos(a), AZ + CRANK * math.sin(a)
    dz = AZ - pz
    chy = py + math.sqrt(ROD * ROD - dz * dz)
    return a, py, pz, math.atan2(dz, chy - py), chy


def animate(objs, sc):
    frames = int(LOOP * 24)
    yc = AX - 1.0
    for f in range(frames + 1):
        a, py, pz, r, chy = state(f / frames)
        objs["flywheel"].rotation_euler = (a, 0, 0)
        objs["armature"].rotation_euler = (a, 0, 0)
        objs["governor"].rotation_euler = (0, 0, -2 * a)
        objs["conrod"].location = (FX + 0.2, py, pz)
        objs["conrod"].rotation_euler = (r, 0, 0)
        objs["crosshead"].location = (FX + 0.2, chy, AZ)
        for n, p in (("flywheel", "rotation_euler"), ("armature", "rotation_euler"), ("governor", "rotation_euler"), ("conrod", "location"),
                     ("conrod", "rotation_euler"), ("crosshead", "location")):
            objs[n].keyframe_insert(p, frame=f + 1)
    sc.frame_set(1)


def tracks():
    steps = 24
    yc = AX - 1.0
    y0 = yc + CRANK
    rot, pos, ch, arc, flame = {}, {}, {}, {}, {}
    for i in range(steps + 1):
        t = i / steps
        a, py, pz, r, chy = state(t)
        key = f"{LOOP * t:.4f}"
        rot[key] = [round(math.degrees(r), 3), 0, 0]
        pos[key] = [0, round((pz - AZ) * 16, 3), round((py - y0) * 16, 3)]
        ch[key] = [0, 0, round((chy - (y0 + ROD)) * 16, 3)]
        s = 1 if math.sin(30 * math.pi * t) * math.sin(12 * math.pi * t) > -0.2 else 0
        arc[key] = [s, s, s]
        flame[key] = [1, round(1 + 0.28 * math.sin(6 * math.pi * t) + 0.14 * math.sin(18 * math.pi * t), 3), 1]
    spin = lambda: {f"{LOOP * i / 4:.4f}": [90.0 * i, 0, 0] for i in range(5)}
    return {"flywheel": {"rotation": spin()}, "armature": {"rotation": spin()},
            "governor": {"rotation": {f"{LOOP * i / 8:.4f}": [0, 90.0 * i, 0] for i in range(9)}},
            "conrod": {"rotation": rot, "position": pos}, "crosshead": {"position": ch}, "arc": {"scale": arc},
            "stack_flame": {"scale": flame}}, LOOP


m = Machine("coal_gen")
frame(m)
moving(m)
sc, tris = m.build("WB_CoalGen")
light_scene(sc, int(LOOP * 24))
animate(m.objects, sc)
print("костей:", len(m.objects), "треугольников:", tris)
