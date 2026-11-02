"""
Кислородный конвертер (converter): 3×3×5. Грушевидный сосуд на цапфах в портале. Цикл плавки: фурма опускается и дует кислород,
поднимается, сосуд наклоняется вперёд через зубчатый привод и льёт сталь в ковш, возвращается.
"""
import math
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "kit.py"), encoding="utf-8").read())

LOOP = 8.0
PZ = 2.1              # ось цапф
TILT = 65.0           # наклон при сливе, градусы
LIP = (-1.3, 2.62)    # куда сосуд сливает при полном наклоне: y, z
GX = 1.38             # плоскость зубчатого привода
RATIO = 28 / 12


def frame(m):
    f = m.bone("frame")
    f.plinth(-1.48, -1.48, 1.48, 1.48)
    # стойки цапф: от плиты сужаются к подшипникам
    for s in (-1, 1):
        a, b = sorted((s * 0.98, s * 1.32))
        f.wedge((a, -0.62, 0.3), (b, 0.62), (a, -0.3, PZ + 0.32), (b, 0.3), "hull")
        f.lathe((s * 0.98, 0, PZ), [(0.34, 0), (0.34, s * 0.34)], 10, "dark", "X", phase=math.pi / 10)
        f.ring((s * 1.33, 0, PZ), 0.15, 0.27, 0.05, 12, "brass")
    # портал: четыре колонны, верхняя рама, раскосы
    for sx in (-1, 1):
        for y in (-1.28, 1.28):
            f.box((sx * 1.3 - 0.12, y - 0.12, 0.3), (sx * 1.3 + 0.12, y + 0.12, 4.35), "dark", bevel=0.02)
        f.beam((sx * 1.3, -1.25, 0.8), (sx * 1.3, -0.45, 2.1), 0.09, 0.09, "steel")
        f.beam((sx * 1.3, 1.25, 0.8), (sx * 1.3, 0.45, 2.1), 0.09, 0.09, "steel")
    f.box((-1.44, -1.42, 4.35), (1.44, 1.42, 4.6), "hull", bevel=0.04)
    f.box((-1.46, -1.44, 4.44), (1.46, 1.44, 4.5), "brass")
    # вытяжной колпак над горловиной и направляющая фурмы
    f.loft([(3.82, 0.72, 0.72, 0), (4.35, 0.42, 0.42, 0), (4.35, 0.36, 0.36, 0), (3.84, 0.64, 0.64, 0)], "rust")
    f.lathe((0, 0, 4.6), [(0.2, 0), (0.2, 0.34), (0.26, 0.36), (0.26, 0.44), (0.12, 0.47)], 10, "dark", base=False)
    f.pipe([(0.32, 0.32, 4.1), (0.82, 0.95, 4.2), (0.82, 1.1, 4.6), (0.82, 1.1, 4.95)], 0.17, 8, "rust")
    # кислородный бак сзади и шланг к фурме
    f.tank((-0.62, 1.1, 0.3), 0.3, 2.6, 12, "steel", (0.2, 0.5, 0.8), band_mat="red")
    f.pipe([(-0.62, 1.1, 3.05), (-0.62, 1.1, 3.4), (-0.3, 0.8, 5.05), (0, 0.15, 5.12)], 0.035, 6, "rubber")
    f.lathe((-0.62, 0.8, 1.7), [(0.12, 0), (0.12, -0.04), (0.1, -0.06)], 12, "brass", "Y", base=False)
    f.lathe((-0.62, 0.74, 1.7), [(0.085, 0), (0.085, -0.004)], 12, "glass", "Y", base=False)
    # мотор и подшипник шестерни
    f.box((1.08, 0.5, PZ - 0.2), (1.32, 1.1, PZ + 0.2), "dark", bevel=0.02)
    f.lathe((1.3, 1.25, PZ - 0.75), [(0.2, 0), (0.2, 0.75)], 10, "hull", "Z", base=False)
    f.pipe([(1.3, 1.25, PZ), (1.3, 0.95, PZ)], 0.05, 6, "steel")
    # ковш на тележке и рельсы
    for x in (-0.36, 0.36):
        f.box((x - 0.03, -1.48, 0.32), (x + 0.03, -0.7, 0.38), "steel")
    f.box((-0.42, -1.45, 0.38), (0.42, -0.82, 0.5), "dark", bevel=0.02)
    f.lathe((0, -1.13, 0.5), [(0.27, 0), (0.33, 0.12), (0.36, 0.5), (0.38, 0.53), (0.3, 0.53), (0.27, 0.15)], 12, "hull", cap=False)
    f.lathe((0, -1.13, 0.87), [(0.31, 0), (0.31, 0.01)], 12, "fire", base=False)
    for s in (-1, 1):
        f.ring((s * 0.4, -1.13, 0.9), 0.04, 0.08, 0.03, 6, "dark")
    # пульт сбоку, печати
    f.box((-1.46, -0.5, 0.45), (-1.3, 0.5, 1.15), "hull", bevel=0.03)
    f.box((-1.47, -0.38, 0.6), (-1.455, 0.38, 1.02), "screen")
    f.seal((-1.12, -1.4, 3.6), "Y", -1)
    f.seal((1.12, -1.4, 3.6), "Y", -1)


def moving(m):
    # ---- сосуд: тело вращения, бандажи, цапфовое кольцо, шестерня; на лицевой стороне череп
    v = m.bone("vessel", (0, 0, PZ))
    v.lathe((0, 0, PZ), [(0.5, -1.3), (0.78, -1.08), (0.86, -0.6), (0.86, 0.55), (0.66, 1.08), (0.42, 1.42), (0.46, 1.5), (0.31, 1.5),
                         (0.27, 1.1), (0.3, 0.8)], 20, "hull", cap=False)
    v.lathe((0, 0, PZ - 1.3), [(0.5, 0), (0.4, -0.05)], 20, "dark", base=False)
    for z, r in ((-0.72, 0.84), (0.68, 0.8)):
        v.ring((0, 0, PZ + z), r - 0.05, r + 0.05, 0.09, 20, "brass", "Z")
    v.ring((0, 0, PZ), 0.82, 0.98, 0.26, 20, "dark", "Z")
    v.lathe((0, 0, PZ + 1.32), [(0.27, 0), (0.27, 0.02)], 12, "fire", base=False)
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        x, y = math.cos(a), math.sin(a)
        v.beam((0.88 * x, 0.88 * y, PZ - 0.6), (0.88 * x, 0.88 * y, PZ + 0.5), 0.08, 0.05, "dark")
    for s in (-1, 1):
        v.lathe((s * 0.92, 0, PZ), [(0.14, 0), (0.14, s * 0.42)], 10, "steel", "X")
    v.gear((GX, 0, PZ), 0.52, 0.6, 0.1, 28, "brass", "X", fill=0.5, flank=0.12)
    v.lathe((GX + 0.05, 0, PZ), [(0.13, 0), (0.09, 0.05)], 6, "dark", "X", base=False)
    v.skull(0, -0.78, PZ + 0.05, 0.62)

    # ---- ведущая шестерня
    p = m.bone("pinion", (GX, 0.8, PZ))
    p.gear((GX, 0.8, PZ), 0.2, 0.28, 0.1, 12, "steel", "X", phase=15, fill=0.5, flank=0.12)
    p.lathe((GX - 0.3, 0.8, PZ), [(0.05, 0), (0.05, 0.36)], 6, "steel", "X")

    # ---- кислородная фурма
    l = m.bone("lance", (0, 0, 4.6))
    l.lathe((0, 0, 3.72), [(0.06, 0), (0.06, 1.42)], 8, "steel")
    l.lathe((0, 0, 3.66), [(0.03, 0), (0.09, 0.08), (0.09, 0.12)], 8, "brass", base=False)
    l.box((-0.13, -0.13, 5.12), (0.13, 0.13, 5.2), "dark", bevel=0.015)

    # ---- пламя продувки над горловиной
    b = m.bone("blow", (0, 0, PZ + 1.5))
    for k in range(3):
        a = k * 2 * math.pi / 3
        b.lathe((0.14 * math.cos(a), 0.14 * math.sin(a), PZ + 1.5), [(0.13, 0), (0.09, 0.14), (0.015, 0.34)], 5, "fire", base=False)

    # ---- струя стали: растёт вниз от носика
    s = m.bone("pour", (0, LIP[0], LIP[1]))
    s.lathe((0, LIP[0] + 0.14, 0.87), [(0.05, 0), (0.09, LIP[1] - 0.87)], 6, "fire", base=False)

    # ---- факел трубы
    fl = m.bone("stack_flame", (0.82, 1.1, 4.96))
    fl.lathe((0.82, 1.1, 4.96), [(0.13, 0), (0.09, 0.16), (0.02, 0.4)], 6, "fire", base=False)


def smooth(x):
    return x * x * (3 - 2 * x)


def state(t):
    """tilt 0..1 наклона, lance 0..1 опускания, blow и pour 0..1."""
    lance = 0.0
    if t < 0.06:
        lance = smooth(t / 0.06)
    elif t < 0.4:
        lance = 1.0
    elif t < 0.48:
        lance = 1 - smooth((t - 0.4) / 0.08)
    blow = 1.0 if 0.06 <= t < 0.42 else 0.0
    tilt = 0.0
    if 0.5 <= t < 0.64:
        tilt = smooth((t - 0.5) / 0.14)
    elif 0.64 <= t < 0.84:
        tilt = 1.0
    elif 0.84 <= t < 0.98:
        tilt = 1 - smooth((t - 0.84) / 0.14)
    pour = 0.0
    if 0.64 <= t < 0.68:
        pour = (t - 0.64) / 0.04
    elif 0.68 <= t < 0.8:
        pour = 1.0
    elif 0.8 <= t < 0.84:
        pour = 1 - (t - 0.8) / 0.04
    return tilt * TILT, lance * -0.78, blow, pour


def animate(objs, sc):
    frames = int(LOOP * 24)
    for f in range(frames + 1):
        tilt, lance, blow, pour = state(f / frames)
        objs["vessel"].rotation_euler = (math.radians(tilt), 0, 0)
        objs["pinion"].rotation_euler = (-math.radians(tilt) * RATIO, 0, 0)
        objs["lance"].location = (0, 0, 4.6 + lance)
        objs["blow"].scale = (blow, blow, blow)
        objs["pour"].scale = (pour > 0, pour > 0, pour)
        for n, p in (("vessel", "rotation_euler"), ("pinion", "rotation_euler"), ("lance", "location"), ("blow", "scale"), ("pour", "scale")):
            objs[n].keyframe_insert(p, frame=f + 1)
    sc.frame_set(1)


def tracks():
    steps = 64
    vessel, pinion, lance, blow, pour, flame = {}, {}, {}, {}, {}, {}
    for i in range(steps + 1):
        t = i / steps
        tilt, ln, bl, po = state(t)
        key = f"{LOOP * t:.4f}"
        vessel[key] = [round(tilt, 3), 0, 0]
        pinion[key] = [round(-tilt * RATIO, 3), 0, 0]
        lance[key] = [0, round(ln * 16, 3), 0]
        k = bl * (1 + 0.3 * math.sin(40 * math.pi * t))
        blow[key] = [bl, round(k, 3), bl]
        pour[key] = [1 if po > 0 else 0, round(po, 3), 1 if po > 0 else 0]
        flame[key] = [1, round(1 + 0.3 * math.sin(16 * math.pi * t) + 0.15 * math.sin(46 * math.pi * t), 3), 1]
    return {"vessel": {"rotation": vessel}, "pinion": {"rotation": pinion}, "lance": {"position": lance}, "blow": {"scale": blow},
            "pour": {"scale": pour}, "stack_flame": {"scale": flame}}, LOOP


m = Machine("converter")
frame(m)
moving(m)
sc, tris = m.build("WB_Converter")
light_scene(sc, int(LOOP * 24))
animate(m.objects, sc)
print("костей:", len(m.objects), "треугольников:", tris)
