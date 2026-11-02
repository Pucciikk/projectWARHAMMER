"""
Домна Механикус (blast_furnace): 5×5×7. Конусная шахта в кольцах; кольцевой воздуховод с фурмами вокруг горна, лётка с жёлобом
расплава спереди; воздухонагреватель сбоку; наклонный скиповый подъёмник сзади с вагонеткой; загрузочный конус на колошнике.
Цикл: скип едет наверх, опрокидывается, конус опускается и садится обратно, скип возвращается.
"""
import math
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "kit.py"), encoding="utf-8").read())

LOOP = 8.0
FY = -0.1         # ось шахты
SK0 = (0.0, 2.25, 0.65)      # нижняя точка скипа
SK1 = (0.0, 0.85, 5.55)      # верхняя точка


def frame(m):
    f = m.bone("frame")
    f.box((-2.48, -2.48, 0), (2.48, 2.48, 0.2), "dark", bevel=0.05)
    f.box((-2.3, -2.3, 0.2), (2.3, 2.3, 0.36), "hull", bevel=0.03)
    for a, b in (((-2.3, -2.3), (2.3, -2.14)), ((-2.3, -2.14), (-2.14, 2.3)), ((2.14, -2.14), (2.3, 2.3))):
        f.box((a[0], a[1], 0.36), (b[0], b[1], 0.372), "hazard")
    for x in (-2.38, 0, 2.38):
        for y in (-2.38, 0, 2.38):
            if x or y:
                f.lathe((x, y, 0.2), [(0.07, 0), (0.07, 0.07), (0.04, 0.09)], 6, "steel", base=False)
    # ---- горн и шахта: тело вращения с ломаным профилем
    f.lathe((0, FY, 0.36), [(1.72, 0), (1.72, 0.38), (1.5, 0.45), (1.42, 1.25), (1.66, 1.4), (1.66, 1.55), (1.42, 1.7), (1.08, 4.3), (1.2, 4.42),
                            (1.2, 4.6), (0.95, 4.68), (0.82, 5.0), (0.95, 5.1), (0.95, 5.2), (0.72, 5.25)], 20, "brick", base=False)
    for z, r in ((1.0, 1.5), (2.45, 1.38), (3.05, 1.29), (3.65, 1.2), (4.2, 1.12)):    # стяжные кольца
        f.ring((0, FY, z), r - 0.08, r + 0.03, 0.11, 20, "hull", "Z")
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        x, y = math.cos(a), math.sin(a)
        f.beam((1.6 * x, FY + 1.6 * y, 0.36), (1.12 * x, FY + 1.12 * y, 4.45), 0.14, 0.14, "dark")   # пояс колонн
    # ---- кольцевой воздуховод и фурмы
    f.ring((0, FY, 2.05), 1.5, 1.82, 0.32, 20, "rust", "Z")
    for k in range(10):
        a = k * math.pi / 5
        x, y = math.cos(a), math.sin(a)
        f.pipe([(1.6 * x, FY + 1.6 * y, 1.9), (1.58 * x, FY + 1.58 * y, 1.62), (1.34 * x, FY + 1.34 * y, 1.2)], 0.055, 6, "steel")
        f.lathe((1.3 * x, FY + 1.3 * y, 1.1), [(0.08, 0), (0.08, 0.14)], 6, "fire", base=False)       # глазки фурм
    # ---- лётка, жёлоб расплава, ковш
    f.box((-0.52, FY - 1.86, 0.36), (0.52, FY - 1.32, 1.25), "brick", bevel=0.05)
    f.box((-0.28, FY - 1.87, 0.62), (0.28, FY - 1.8, 1.05), "fire")
    f.box((-0.34, FY - 1.9, 0.55), (0.34, FY - 1.82, 0.62), "dark")
    f.box((-0.34, FY - 1.9, 1.05), (0.34, FY - 1.82, 1.12), "dark")
    f.box((-0.22, -2.3, 0.45), (0.22, FY - 1.82, 0.55), "dark", bevel=0.02)
    f.box((-0.14, -2.3, 0.55), (0.14, FY - 1.82, 0.565), "fire")                    # жёлоб расплава
    # череп над лёткой
    f.skull(0, FY - 1.78, 1.82, 0.72)
    f.gear((0, FY - 1.76, 1.82), 0.44, 0.56, 0.05, 12, "brass", "Y")
    # ---- воздухонагреватель справа и дутьё
    f.tank((1.82, 1.45, 0.36), 0.55, 4.4, 14, "hull", (0.2, 0.5, 0.8))
    f.lathe((1.82, 1.45, 5.0), [(0.12, 0), (0.12, 0.95), (0.16, 0.98), (0.16, 1.05)], 8, "rust", base=False)
    f.pipe([(1.45, 1.1, 2.05), (1.4, 0.75, 2.05)], 0.16, 8, "rust")
    f.box((2.2, 1.3, 0.8), (2.38, 1.6, 2.6), "dark", bevel=0.02)
    f.box((2.36, 1.38, 0.95), (2.4, 1.52, 2.4), "fire")
    # воздуходувка слева: кожух и мотор; вращается крыльчатка
    f.lathe((-1.85, 1.45, 0.36), [(0.58, 0), (0.58, 0.12), (0.46, 0.2), (0.46, 0.78), (0.2, 0.86)], 12, "rust", base=False)
    f.ring((-1.85, 1.45, 1.55), 0.52, 0.6, 1.3, 16, "hull", "Z")
    f.pipe([(-1.5, 1.2, 2.05), (-1.32, 0.7, 2.05)], 0.16, 8, "rust")
    # ---- рама скипа: два рельса, балки, колошниковая площадка
    for s in (-1, 1):
        f.beam((s * 0.48, SK0[1] + 0.2, 0.36), (s * 0.48, SK1[1] - 0.25, 6.25), 0.09, 0.14, "steel")
        f.beam((s * 0.7, 2.35, 0.36), (s * 0.7, 2.0, 3.0), 0.15, 0.15, "dark")
    f.beam((-0.85, 1.75, 3.2), (0.85, 1.75, 3.2), 0.12, 0.12, "dark")
    f.box((-1.38, FY - 1.1, 5.56), (1.38, FY + 0.5, 5.68), "dark", bevel=0.025)
    for x in (-1.3, 1.3):
        for y in (FY - 1.02, FY + 0.42):
            f.box((x - 0.025, y - 0.025, 5.68), (x + 0.025, y + 0.025, 6.15), "steel")
    f.pipe([(-1.3, FY - 1.02, 6.15), (1.3, FY - 1.02, 6.15)], 0.03, 6, "hazard")
    # копёр с блоком наверху
    f.box((-0.65, 0.5, 6.25), (0.65, 0.76, 6.42), "dark", bevel=0.02)
    f.beam((-0.56, 0.62, 5.68), (-0.56, 0.62, 6.25), 0.1, 0.1, "dark")
    f.beam((0.56, 0.62, 5.68), (0.56, 0.62, 6.25), 0.1, 0.1, "dark")
    # лебёдка внизу и печати
    f.box((-0.72, 1.95, 0.36), (-0.3, 2.3, 0.76), "hull", bevel=0.03)
    f.lathe((-0.3, 2.15, 0.56), [(0.2, 0), (0.2, 0.42)], 10, "brass", "X")
    f.seal((-1.36, FY - 0.78, 1.45), "Y", -1)
    f.seal((0.72, FY - 1.86, 1.1), "Y", -1)


def moving(m):
    # ---- скип: кузов и колёса; идёт вдоль рельсов, на верху опрокидывается вокруг своей оси
    sk = m.bone("skip", SK0)
    x, y, z = SK0
    sk.loft([(z - 0.02, 0.36, 0.34, y), (z + 0.42, 0.42, 0.42, y), (z + 0.42, 0.34, 0.34, y), (z + 0.03, 0.28, 0.28, y)], "rust")
    sk.box((-0.38, y - 0.34, z - 0.1), (0.38, y + 0.34, z - 0.02), "dark", bevel=0.02)
    for s in (-1, 1):
        for d in (-0.26, 0.26):
            sk.lathe((s * 0.42, y + d, z - 0.08), [(0.09, -0.04), (0.09, 0.04)], 8, "steel", "X")
    for i, (a, b, h) in enumerate(((-0.12, -0.1, 0.1), (0.14, 0.04, 0.14), (0.0, 0.16, 0.08), (-0.2, 0.14, 0.11))):
        sk.lathe((a, y + b, z + 0.33), [(0.15, 0), (0.1, h), (0.03, h + 0.07)], 5, "dark", phase=i, base=False)
    # ---- загрузочный конус (колокол) на колошнике
    b = m.bone("bell", (0, FY, 5.62))
    b.lathe((0, FY, 5.62), [(0.62, 0), (0.15, 0.3), (0.11, 0.3), (0.11, 0.62)], 12, "steel", base=False)
    b.ring((0, FY, 5.92), 0.1, 0.17, 0.06, 8, "brass", "Z")
    # ---- крыльчатка воздуходувки и блок копра
    fan = m.bone("fan", (-1.85, 1.45, 1.55))
    fan.lathe((-1.85, 1.45, 1.0), [(0.07, 0), (0.07, 1.25)], 8, "steel", base=False)
    fan.lathe((-1.85, 1.45, 2.15), [(0.16, 0), (0.08, 0.1)], 6, "dark", base=False)
    for k in range(6):
        a = k * math.pi / 3
        fan.beam((-1.85, 1.45, 1.55), (-1.85 + 0.47 * math.cos(a), 1.45 + 0.47 * math.sin(a), 1.55), 0.09, 0.03, "brass")
    w = m.bone("wheel", (0, 0.63, 6.34))
    w.ring((0, 0.63, 6.34), 0.1, 0.26, 0.09, 12, "brass")
    w.lathe((-0.1, 0.63, 6.34), [(0.05, 0), (0.05, 0.2)], 6, "steel", "X")
    for k in range(2):
        a = math.pi / 4 + k * math.pi / 2
        w.beam((0, 0.63 + 0.22 * math.cos(a), 6.34 + 0.22 * math.sin(a)), (0, 0.63 - 0.22 * math.cos(a), 6.34 - 0.22 * math.sin(a)), 0.03, 0.03, "dark")
    # ---- пламя колошника
    fl = m.bone("stack_flame", (0, FY, 5.61))
    for k in range(4):
        a = k * math.pi / 2 + 0.6
        fl.lathe((0.46 * math.cos(a), FY + 0.46 * math.sin(a), 5.61), [(0.14, 0), (0.1, 0.16), (0.02, 0.5)], 5, "fire", base=False)


def smooth(x):
    return x * x * (3 - 2 * x)


def state(t):
    """travel: 0 внизу, 1 наверху; tip: градусы опрокидывания; bell: опускание конуса."""
    if t < 0.35:
        travel = smooth(t / 0.35)
    elif t < 0.6:
        travel = 1.0
    elif t < 0.95:
        travel = 1 - smooth((t - 0.6) / 0.35)
    else:
        travel = 0.0
    tip = 0.0
    if 0.35 <= t < 0.42:
        tip = smooth((t - 0.35) / 0.07)
    elif 0.42 <= t < 0.52:
        tip = 1.0
    elif 0.52 <= t < 0.6:
        tip = 1 - smooth((t - 0.52) / 0.08)
    bell = 0.0
    if 0.55 <= t < 0.62:
        bell = smooth((t - 0.55) / 0.07)
    elif 0.62 <= t < 0.74:
        bell = 1.0
    elif 0.74 <= t < 0.82:
        bell = 1 - smooth((t - 0.74) / 0.08)
    return travel, tip * 75.0, bell * -0.42


def animate(objs, sc):
    frames = int(LOOP * 24)
    for f in range(frames + 1):
        t = f / frames
        tr, tip, bell = state(t)
        objs["skip"].location = (0, SK0[1] + (SK1[1] - SK0[1]) * tr, SK0[2] + (SK1[2] - SK0[2]) * tr)
        objs["skip"].rotation_euler = (math.radians(tip), 0, 0)
        objs["bell"].location = (0, FY, 5.62 + bell)
        objs["fan"].rotation_euler = (0, 0, -2 * math.pi * 16 * t)
        objs["wheel"].rotation_euler = (2 * math.pi * 3 * tr, 0, 0)
        objs["skip"].keyframe_insert("location", frame=f + 1)
        objs["skip"].keyframe_insert("rotation_euler", frame=f + 1)
        objs["bell"].keyframe_insert("location", frame=f + 1)
        objs["fan"].keyframe_insert("rotation_euler", frame=f + 1)
        objs["wheel"].keyframe_insert("rotation_euler", frame=f + 1)
    sc.frame_set(1)


def tracks():
    steps = 64
    skip_p, skip_r, bell, wheel, flame = {}, {}, {}, {}, {}
    for i in range(steps + 1):
        t = i / steps
        tr, tip, b = state(t)
        key = f"{LOOP * t:.4f}"
        skip_p[key] = [0, round((SK1[2] - SK0[2]) * tr * 16, 3), round((SK1[1] - SK0[1]) * tr * 16, 3)]
        skip_r[key] = [round(tip, 3), 0, 0]
        bell[key] = [0, round(b * 16, 3), 0]
        wheel[key] = [round(360 * 3 * tr, 2), 0, 0]
        flame[key] = [1, round(0.9 + 0.35 * math.sin(10 * math.pi * t) + 0.2 * math.sin(26 * math.pi * t), 3), 1]
    # 16 оборотов за цикл: каждые четверть оборота — ключ, иначе интерполяция закрутит назад
    fan = {f"{LOOP * i / 64:.4f}": [0, 90.0 * i, 0] for i in range(65)}
    return {"skip": {"position": skip_p, "rotation": skip_r}, "bell": {"position": bell}, "fan": {"rotation": fan},
            "wheel": {"rotation": wheel}, "stack_flame": {"scale": flame}}, LOOP


m = Machine("blast_furnace")
frame(m)
moving(m)
sc, tris = m.build("WB_BlastFurnace")
light_scene(sc, int(LOOP * 24))
animate(m.objects, sc)
print("костей:", len(m.objects), "треугольников:", tris)
