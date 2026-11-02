"""
Прокатный стан (rolling_mill): 7×3×3. Слева нагревательная печь, по рольгангу раскалённый сляб проходит две клети
(валки вращаются навстречу, нажимные цилиндры подрабатывают) и наматывается на барабан справа. Привод — маховик и валы сзади.
Ось линии — X. Ядро в середине переднего ряда.
"""
import math
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "kit.py"), encoding="utf-8").read())

LOOP = 6.0
LINE_Z = 1.0          # верх рольганга: по нему идёт сляб
STANDS = (-0.75, 1.0) # положение клетей по X
ROLL_R = 0.26
SLAB_Y = -0.35        # ось линии по глубине
FLY = (0.0, 1.05, 1.4)  # маховик: x, y, z


def stand(f, x):
    """Клеть: две станины, поперечины, нажимной цилиндр, крышки подшипников."""
    for y in (SLAB_Y - 0.72, SLAB_Y + 0.72):
        f.box((x - 0.3, y - 0.11, 0.3), (x + 0.3, y + 0.11, 2.15), "hull", bevel=0.035)
        f.box((x - 0.34, y - 0.13, 0.3), (x + 0.34, y + 0.13, 0.55), "dark", bevel=0.025)
        f.box((x - 0.19, y - 0.125, LINE_Z - 0.6), (x + 0.19, y + 0.125, LINE_Z + 0.65), "dark")   # окно под подушки
        f.lathe((x, y - 0.13, LINE_Z - ROLL_R - 0.02), [(0.13, 0), (0.13, -0.04)], 8, "brass", "Y", base=False)
        f.lathe((x, y - 0.13, LINE_Z + ROLL_R + 0.02), [(0.13, 0), (0.13, -0.04)], 8, "brass", "Y", base=False)
    f.box((x - 0.34, SLAB_Y - 0.86, 2.15), (x + 0.34, SLAB_Y + 0.86, 2.34), "dark", bevel=0.03)
    f.box((x - 0.35, SLAB_Y - 0.87, 2.22), (x + 0.35, SLAB_Y + 0.87, 2.27), "brass")
    f.lathe((x, SLAB_Y, 2.34), [(0.24, 0), (0.24, 0.1), (0.18, 0.13), (0.18, 0.42), (0.21, 0.44), (0.21, 0.52), (0.08, 0.55)], 10, "rust", base=False)


def frame(m):
    f = m.bone("frame")
    f.plinth(-3.48, -1.48, 3.48, 1.48)
    # ---- рольганг: продольные балки и неподвижные ролики
    for y in (SLAB_Y - 0.46, SLAB_Y + 0.46):
        f.box((-2.2, y - 0.05, 0.3), (2.35, y + 0.05, LINE_Z - 0.12), "dark")
    x = -2.1
    while x < 2.2:
        if all(abs(x - s) > 0.34 for s in STANDS):
            f.lathe((x, SLAB_Y - 0.46, LINE_Z - 0.07), [(0.07, 0), (0.07, 0.92)], 8, "steel", "Y")
        x += 0.28
    for s in STANDS:
        stand(f, s)
    # ---- нагревательная печь слева: кирпич, стальной каркас, заслонка, труба
    f.box((-3.42, -1.3, 0.3), (-2.15, 0.78, 2.1), "brick", bevel=0.06)
    f.box((-3.46, -1.34, 2.1), (-2.11, 0.82, 2.24), "dark", bevel=0.03)
    for y in (-1.3, -0.35, 0.78):
        f.box((-3.46, y - 0.06, 0.3), (-3.38, y + 0.06, 2.1), "hull")
    for z in (0.75, 1.5):
        f.box((-3.44, -1.33, z), (-2.13, -1.3, z + 0.08), "hull")
    f.box((-2.17, SLAB_Y - 0.48, LINE_Z - 0.1), (-2.13, SLAB_Y + 0.48, LINE_Z + 0.42), "fire")       # проём печи
    f.box((-2.14, SLAB_Y - 0.56, LINE_Z - 0.14), (-2.08, SLAB_Y - 0.48, LINE_Z + 0.62), "dark")
    f.box((-2.14, SLAB_Y + 0.48, LINE_Z - 0.14), (-2.08, SLAB_Y + 0.56, LINE_Z + 0.62), "dark")
    f.box((-2.14, SLAB_Y - 0.56, LINE_Z + 0.62), (-2.08, SLAB_Y + 0.56, LINE_Z + 0.72), "dark")
    f.box((-2.9, -1.33, 1.05), (-2.5, -1.3, 1.25), "fire")                                           # смотровое окно
    f.lathe((-2.8, 0.15, 2.24), [(0.28, 0), (0.28, 0.1), (0.2, 0.18), (0.2, 1.4), (0.26, 1.44), (0.26, 1.54), (0.2, 1.56)], 10, "rust", base=False)
    for z in (2.8, 3.3):
        f.ring((-2.8, 0.15, z), 0.18, 0.23, 0.06, 10, "brass", "Z")
    # череп над первой клетью
    f.skull(STANDS[0], SLAB_Y - 0.84, 1.75, 0.5)
    f.gear((STANDS[0], SLAB_Y - 0.86, 1.75), 0.3, 0.38, 0.04, 10, "brass", "Y")
    # ---- привод сзади: мотор, кожух шестерён, шпиндели к верхним и нижним валкам
    f.box((-1.45, 0.72, 0.3), (1.65, 1.42, 0.62), "dark", bevel=0.03)
    f.box((-1.25, 0.8, 0.62), (-0.2, 1.38, 1.6), "hull", bevel=0.05)
    f.box((-1.27, 0.78, 1.0), (-0.18, 1.4, 1.08), "brass")
    for k in range(5):
        z = 0.72 + k * 0.17
        f.box((-1.2, 1.38, z), (-0.25, 1.42, z + 0.08), "dark")
    f.lathe((FLY[0], FLY[1] + 0.3, FLY[2]), [(0.1, 0), (0.1, -0.5)], 8, "steel", "Y")
    f.box((-0.1, 0.8, FLY[2] - 0.82), (0.1, 1.4, FLY[2] - 0.5), "dark")
    # манометр, пульт и печати
    f.box((2.1, -1.45, 0.3), (2.35, -1.0, 1.25), "hull", bevel=0.03)
    f.box((2.12, -1.46, 0.65), (2.33, -1.445, 1.1), "screen")
    f.seal((STANDS[1], SLAB_Y - 0.84, 1.85), "Y", -1)
    f.seal((-2.3, -1.34, 1.85), "Y", -1)
    # ---- барабан справа: стойки
    for y in (SLAB_Y - 0.62, SLAB_Y + 0.62):
        f.wedge((2.75, y - 0.08, 0.3), (3.35, y + 0.08), (2.95, y - 0.06, 1.0), (3.15, y + 0.06), "dark")


def roll_pair(m, name, x):
    for tag, z, sign in (("top", LINE_Z + ROLL_R + 0.05, -1), ("low", LINE_Z - ROLL_R - 0.05, 1)):
        r = m.bone(f"{name}_{tag}", (x, SLAB_Y, z))
        r.lathe((x, SLAB_Y - 0.6, z), [(0.09, 0), (0.09, 0.08), (ROLL_R, 0.1), (ROLL_R, 1.1), (0.09, 1.12), (0.09, 1.2)], 14, "steel", "Y")
        r.lathe((x, SLAB_Y + 0.6, z), [(0.06, 0), (0.06, 0.95)], 6, "dark", "Y", base=False)        # шпиндель к приводу
        r.box((x - 0.09, SLAB_Y - 0.61, z - 0.09), (x + 0.09, SLAB_Y - 0.52, z + 0.09), "dark")
        for a in (0, 1):
            ang = a * math.pi / 2
            ca, sa = math.cos(ang) * ROLL_R * 0.98, math.sin(ang) * ROLL_R * 0.98
            r.box((x + ca - 0.02, SLAB_Y - 0.5, z + sa - 0.02), (x + ca + 0.02, SLAB_Y + 0.5, z + sa + 0.02), "rust")
            r.box((x - ca - 0.02, SLAB_Y - 0.5, z - sa - 0.02), (x - ca + 0.02, SLAB_Y + 0.5, z - sa + 0.02), "rust")


def moving(m):
    roll_pair(m, "roll_a", STANDS[0])
    roll_pair(m, "roll_b", STANDS[1])
    # ---- сляб
    s = m.bone("slab", (-2.2, SLAB_Y, LINE_Z + 0.05))
    s.box((-2.55, SLAB_Y - 0.36, LINE_Z), (-1.85, SLAB_Y + 0.36, LINE_Z + 0.09), "fire")
    # ---- заслонка печи
    d = m.bone("furnace_door", (-2.1, SLAB_Y, LINE_Z))
    d.box((-2.12, SLAB_Y - 0.48, LINE_Z - 0.1), (-2.08, SLAB_Y + 0.48, LINE_Z + 0.42), "hull", bevel=0.008)
    for z in (LINE_Z, LINE_Z + 0.15, LINE_Z + 0.3):
        d.box((-2.09, SLAB_Y - 0.46, z), (-2.06, SLAB_Y + 0.46, z + 0.05), "dark")
    # ---- маховик с шестью спицами и кривошипом
    fw = m.bone("flywheel", FLY)
    fw.ring(FLY, 0.46, 0.6, 0.18, 24, "hull", "Y")
    fw.ring((FLY[0], FLY[1] + 0.1, FLY[2]), 0.52, 0.61, 0.04, 24, "brass", "Y")
    fw.lathe((FLY[0], FLY[1] - 0.12, FLY[2]), [(0.13, 0), (0.13, 0.24)], 10, "dark", "Y")
    for k in range(6):
        a = k * math.pi / 3
        fw.beam((FLY[0], FLY[1], FLY[2]), (FLY[0] + 0.5 * math.cos(a), FLY[1], FLY[2] + 0.5 * math.sin(a)), 0.07, 0.07, "hull")
    # ---- барабан со стальной лентой
    c = m.bone("coil", (3.05, SLAB_Y, 1.0))
    c.lathe((3.05, SLAB_Y - 0.72, 1.0), [(0.07, 0), (0.07, 1.44)], 8, "steel", "Y")
    c.ring((3.05, SLAB_Y, 1.0), 0.14, 0.52, 0.84, 18, "steel", "Y")
    for s_ in (-1, 1):
        c.ring((3.05, SLAB_Y + s_ * 0.44, 1.0), 0.07, 0.58, 0.05, 12, "dark", "Y")
    for k in range(3):
        a = k * 2 * math.pi / 3
        c.box((3.05 + 0.5 * math.cos(a) - 0.035, SLAB_Y - 0.42, 1.0 + 0.5 * math.sin(a) - 0.035),
              (3.05 + 0.5 * math.cos(a) + 0.035, SLAB_Y + 0.42, 1.0 + 0.5 * math.sin(a) + 0.035), "rust")
    # ---- нажимные штоки на клетях
    for i, x in enumerate(STANDS):
        p = m.bone(f"press_{i + 1}", (x, SLAB_Y, 2.9))
        p.lathe((x, SLAB_Y, 2.86), [(0.05, 0), (0.05, 0.26)], 6, "steel", base=False)
        p.box((x - 0.12, SLAB_Y - 0.12, 3.1), (x + 0.12, SLAB_Y + 0.12, 3.16), "dark", bevel=0.012)
    # ---- факел трубы
    fl = m.bone("stack_flame", (-2.8, 0.15, 3.8))
    fl.lathe((-2.8, 0.15, 3.8), [(0.13, 0), (0.09, 0.16), (0.02, 0.38)], 6, "fire", base=False)


def smooth(x):
    return x * x * (3 - 2 * x)


def state(t):
    """door 0..1; slab: смещение по X от печи до барабана, длина и видимость."""
    door = 0.0
    if t < 0.08:
        door = smooth(t / 0.08)
    elif t < 0.3:
        door = 1.0
    elif t < 0.38:
        door = 1 - smooth((t - 0.3) / 0.08)
    # сляб выходит на 0.1 и идёт ровно: прокатка не бывает рывком
    k = min(1, max(0, (t - 0.06) / 0.62))
    x = 4.7 * k
    length = 1 + 1.4 * min(1, k * 1.5)
    vis = 0 if t < 0.06 or t >= 0.72 else 1
    return door * 0.6, x, length, vis


def animate(objs, sc):
    frames = int(LOOP * 24)
    for f in range(frames + 1):
        t = f / frames
        a = 2 * math.pi * t
        door, x, ln, vis = state(t)
        objs["furnace_door"].location = (-2.1, SLAB_Y, LINE_Z + door)
        objs["slab"].location = (-2.2 + x, SLAB_Y, LINE_Z + 0.05)
        objs["slab"].scale = (ln * vis, vis, vis)
        for n, sign in (("roll_a_top", 1), ("roll_a_low", -1), ("roll_b_top", 1), ("roll_b_low", -1)):
            objs[n].rotation_euler = (0, sign * 2 * a, 0)
            objs[n].keyframe_insert("rotation_euler", frame=f + 1)
        objs["flywheel"].rotation_euler = (0, a, 0)
        objs["coil"].rotation_euler = (0, 2 * a, 0)
        for i, st in enumerate(STANDS):
            n = f"press_{i + 1}"
            objs[n].location = (st, SLAB_Y, 2.9 + 0.06 * math.sin(2 * a + i))
            objs[n].keyframe_insert("location", frame=f + 1)
        for n, p in (("furnace_door", "location"), ("slab", "location"), ("slab", "scale"), ("flywheel", "rotation_euler"), ("coil", "rotation_euler")):
            objs[n].keyframe_insert(p, frame=f + 1)
    sc.frame_set(1)


def tracks():
    steps = 48
    door, slab_p, slab_s, flame = {}, {}, {}, {}
    p1, p2 = {}, {}
    for i in range(steps + 1):
        t = i / steps
        d, x, ln, vis = state(t)
        key = f"{LOOP * t:.4f}"
        a = 2 * math.pi * t
        door[key] = [0, round(d * 16, 3), 0]
        # в моделях GeckoLib x смотрит туда же, куда в Blender: позиция без смены знака
        slab_p[key] = [round(x * 16, 3), 0, 0]
        slab_s[key] = [round(ln * vis, 3), vis, vis]
        p1[key] = [0, round(0.06 * math.sin(2 * a) * 16, 3), 0]
        p2[key] = [0, round(0.06 * math.sin(2 * a + 1) * 16, 3), 0]
        flame[key] = [1, round(1 + 0.3 * math.sin(12 * math.pi * t) + 0.14 * math.sin(34 * math.pi * t), 3), 1]
    # поворот вокруг Y Blender = Z анимации; по ключу на четверть оборота, чтобы интерполяция не пошла назад
    spin = lambda sign, turns: {"rotation": {f"{LOOP * i / (4 * turns):.4f}": [0, 0, sign * 90.0 * i] for i in range(4 * turns + 1)}}
    return {"roll_a_top": spin(1, 2), "roll_a_low": spin(-1, 2), "roll_b_top": spin(1, 2), "roll_b_low": spin(-1, 2),
            "flywheel": spin(1, 1), "coil": spin(1, 2), "furnace_door": {"position": door},
            "slab": {"position": slab_p, "scale": slab_s}, "press_1": {"position": p1}, "press_2": {"position": p2},
            "stack_flame": {"scale": flame}}, LOOP


m = Machine("rolling_mill")
frame(m)
moving(m)
sc, tris = m.build("WB_RollingMill")
light_scene(sc, int(LOOP * 24))
animate(m.objects, sc)
print("костей:", len(m.objects), "треугольников:", tris)
