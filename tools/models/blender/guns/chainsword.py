"""
Цепной меч офицера Астра Милитарум: мотор в основании клинка, полотно-направляющая с литанией, цепь из отдельных зубьев, гарда с орлом, рукоять в кожаной обмотке.
Каждый зуб — своя кость: клип "chain" за один шаг цепи переводит зуб на место следующего, поэтому цепь обегает полотно и на концах поворачивает как настоящая.
Клинок смотрит в -Y, рукоять в +Y, плоскость клинка YZ, режущая кромка сверху и снизу.
"""
import math
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "kit.py"), encoding="utf-8").read())
exec(open(os.path.join(_HERE, "guns", "gun_kit.py"), encoding="utf-8").read())

GRIP = (0.0, 0.13, 0.0)       # правая кисть
EXHAUST = (0.075, -0.2, 0.09)
# дорожка цепи: прямые участки и две полуокружности
TRACK_Y0, TRACK_Y1, TRACK_H = -1.08, -0.22, 0.078
TEETH = 36
_STRAIGHT = TRACK_Y1 - TRACK_Y0
_ARC = math.pi * TRACK_H
TRACK_LEN = 2 * _STRAIGHT + 2 * _ARC
PITCH = TRACK_LEN / TEETH


def track(s):
    """Точка дорожки и угол внешней нормали в плоскости YZ. Сверху цепь идёт к кончику, снизу обратно."""
    s %= TRACK_LEN
    if s < _STRAIGHT:
        return TRACK_Y1 - s, TRACK_H, math.pi / 2
    s -= _STRAIGHT
    if s < _ARC:
        a = math.pi / 2 + s / TRACK_H
        return TRACK_Y0 + TRACK_H * math.cos(a), TRACK_H * math.sin(a), a
    s -= _ARC
    if s < _STRAIGHT:
        return TRACK_Y0 + s, -TRACK_H, 3 * math.pi / 2
    s -= _STRAIGHT
    a = 3 * math.pi / 2 + s / TRACK_H
    return TRACK_Y1 + TRACK_H * math.cos(a), TRACK_H * math.sin(a), a


def tooth(m, i):
    s = i * PITCH
    y, z, a = track(s)
    b = m.bone(f"tooth_{i}", (0, y, z))
    n = (math.cos(a), math.sin(a))      # наружу в (y, z)
    t = (math.sin(a), -math.cos(a))     # по ходу цепи
    if s % TRACK_LEN < 0:
        t = (-t[0], -t[1])

    def pt(u, v):
        return (y + t[0] * u + n[0] * v, z + t[1] * u + n[1] * v)
    # звено цепи: темная пластина, заходит в паз
    contour(b, [pt(-0.03, -0.016), pt(0.03, -0.016), pt(0.032, 0.008), pt(-0.032, 0.008)], -0.0095, 0.0095, "gm_dark")
    # зуб с наклоном вперёд и острым жалом
    contour(b, [pt(-0.027, 0.005), pt(0.022, 0.005), pt(0.042, 0.056), pt(0.016, 0.044), pt(-0.017, 0.024)], -0.0065, 0.0065, "gm_steel")
    # заточенная кромка светлее
    contour(b, [pt(0.024, 0.03), pt(0.042, 0.056), pt(0.016, 0.044)], -0.0069, 0.0069, "steel")


def blade(b):
    # средняя плита с пазом под цепь и две щеки
    def stadium(h, y0, y1, n=8):
        pts = []
        for i in range(n + 1):
            a = math.pi / 2 + math.pi * i / n
            pts.append((y0 + h * math.cos(a), h * math.sin(a)))
        for i in range(n + 1):
            a = 3 * math.pi / 2 + math.pi * i / n
            pts.append((y1 + h * math.cos(a), h * math.sin(a)))
        return pts
    contour(b, stadium(TRACK_H - 0.008, TRACK_Y0, TRACK_Y1), -0.0065, 0.0065, "gm_dark")
    for s in (-1, 1):
        x0, x1 = (0.0065, 0.017) if s > 0 else (-0.017, -0.0065)
        contour(b, stadium(TRACK_H - 0.012, TRACK_Y0 + 0.002, TRACK_Y1), x0, x1, "gm_mid", bevel=0.003)
        x = s * 0.017
        # дол и латунная полоса с литанией: ряды рубленых знаков
        side_box(b, x, s, 0.0012, TRACK_Y0 + 0.07, TRACK_Y1 - 0.02, -0.03, 0.03, "gm_dark", bevel=0.0004)
        side_box(b, x + s * 0.0012, s, 0.0008, TRACK_Y0 + 0.08, TRACK_Y1 - 0.03, -0.021, 0.021, "gm_brass")
        y = TRACK_Y0 + 0.09
        k = 0
        while y < TRACK_Y1 - 0.04:
            w = (0.004, 0.008, 0.0055, 0.0065, 0.0035)[k % 5]
            h = (0.015, 0.01, 0.017, 0.008, 0.013)[k % 5]
            side_box(b, x + s * 0.002, s, 0.0005, y, y + w, -h, h, "gm_rubber")
            y += w + 0.0055
            k += 1
        # заклёпки вдоль кромки
        for i in range(10):
            yy = TRACK_Y0 + 0.05 + i * (TRACK_Y1 - TRACK_Y0 - 0.1) / 9
            for zz in (-0.05, 0.05):
                b.bolt((x, yy, zz), "X", 0.0052, s * 0.0028, "gm_steel")
    # оковка кончика
    for s in (-1, 1):
        x0, x1 = (0.016, 0.0205) if s > 0 else (-0.0205, -0.016)
        pts = [(TRACK_Y0 + 0.07, 0.062), (TRACK_Y0 + 0.02, 0.062), (TRACK_Y0 - 0.03, 0.04), (TRACK_Y0 - 0.058, 0.0), (TRACK_Y0 - 0.03, -0.04), (TRACK_Y0 + 0.02, -0.062), (TRACK_Y0 + 0.07, -0.062), (TRACK_Y0 + 0.1, 0.0)]
        contour(b, pts, x0, x1, "gm_gold", bevel=0.0015)
    b.lathe((0, TRACK_Y0, 0), [(0.0135, -0.0225), (0.0135, 0.0225)], 10, "gm_steel", "X")


def motor(b):
    # кожух мотора: ступенчатый, с рёбрами охлаждения и окном запала
    pts = [(-0.3, -0.075), (-0.3, 0.075), (-0.255, 0.098), (-0.09, 0.098), (-0.045, 0.082), (-0.03, 0.05), (-0.03, -0.055), (-0.06, -0.082), (-0.255, -0.098)]
    contour(b, pts, -0.056, 0.056, "gm_mid", bevel=0.007)
    for s in (-1, 1):
        x = s * 0.056
        contour(b, [(-0.285, -0.062), (-0.285, 0.062), (-0.25, 0.078), (-0.1, 0.078), (-0.06, 0.06), (-0.06, -0.06), (-0.09, -0.075), (-0.25, -0.078)], min(x, x + s * 0.004), max(x, x + s * 0.004), "gm_dark", bevel=0.0015)
        for i in range(6):
            y = -0.265 + i * 0.026
            side_box(b, x + s * 0.004, s, 0.0035, y - 0.0068, y + 0.0068, -0.066, -0.006, "gm_steel", bevel=0.0005)
        bars(b, -0.262, -0.122, 0.018, 0.06, x + s * 0.004, s, 6, glow="gm_ember")
        for y, z in ((-0.278, -0.055), (-0.278, 0.055), (-0.078, -0.052), (-0.078, 0.05)):
            screw(b, (x + s * 0.004, y, z), s, 0.0065, "gm_brass")
    aquila(b, (0.0645, -0.09, -0.03), 0.04, 1)
    # выхлопные трубы вверх и назад
    for i, y in enumerate((-0.24, -0.195)):
        b.pipe([(0.03, y, 0.09), (0.042, y + 0.012, 0.125), (0.042, y + 0.05, 0.15)], 0.0125, 8, "gm_steel")
        b.lathe((0.042, y + 0.05, 0.15), [(0.0145, 0), (0.0145, 0.02), (0.011, 0.024)], 10, "gm_dark", "Y", cap=False)
    # бак с крышкой
    b.lathe((-0.025, -0.17, 0.098), [(0.022, 0), (0.022, 0.018), (0.028, 0.02), (0.028, 0.032), (0.018, 0.038)], 12, "gm_brass", "Z", base=False)
    # кожаная лента с печатью
    purity_seal(b, (-0.06, -0.18, 0.02), -1, 1.0, ((-0.012, 0.1), (0.014, 0.135)))


def hilt(b):
    # гарда: поперечина и дужка, защищающая пальцы
    b.box((-0.066, -0.035, -0.11), (0.066, -0.005, 0.1), "gm_dark", bevel=0.007)
    b.box((-0.071, -0.028, -0.09), (0.071, -0.013, 0.08), "gm_brass", bevel=0.002)
    b.pipe([(0, -0.015, -0.105), (0, 0.04, -0.13), (0, 0.13, -0.135), (0, 0.235, -0.1), (0, 0.27, -0.045)], 0.0135, 8, "gm_gold")
    # черен: обмотка кожей, проволока поверх
    y0, y1 = -0.005, 0.26
    b.lathe((0, 0, 0), [(0.036, y0), (0.04, y0 + 0.03), (0.042, 0.13), (0.039, 0.22), (0.036, y1)], 14, "gm_leather", "Y", cap=False)
    for i in range(9):
        y = 0.02 + i * 0.027
        b.ring((0, y, 0), 0.03, 0.0445, 0.0065, 14, "gm_brass" if i % 3 == 0 else "gm_dark", "Y")
    # рычаг газа под пальцем
    # навершие: череп на кольце
    b.lathe((0, 0, 0), [(0.04, y1), (0.052, y1 + 0.012), (0.052, y1 + 0.03), (0.036, y1 + 0.042)], 14, "gm_brass", "Y", cap=False)
    b.lathe((0, 0, 0), [(0.03, y1 + 0.042), (0.036, y1 + 0.075), (0.026, y1 + 0.1), (0.001, y1 + 0.106)], 14, "gm_steel", "Y", cap=False)
    # шнур стартера с кольцом
    b.pipe([(-0.056, -0.05, -0.06), (-0.066, 0.0, -0.09), (-0.05, 0.06, -0.1)], 0.0045, 6, "gm_rubber")
    b.ring((-0.05, 0.075, -0.1), 0.009, 0.0145, 0.005, 10, "gm_brass", "X")


def build(m):
    b = m.bone("body")
    blade(b)
    motor(b)
    hilt(b)
    for i in range(TEETH):
        tooth(m, i)
    # рычаг газа
    tx, ty, tz = 0.0, 0.03, -0.042
    t = m.bone("throttle", (tx, ty, tz))
    t.beam((tx, ty, tz), (tx, ty + 0.05, tz - 0.022), 0.015, 0.009, "gm_steel")
    arm(m, "arm_r", GRIP)
    locator(m, "exhaust", EXHAUST)


# ------------------------------------------------------------------ клипы

ARM = {"pos": (0, 0, 0), "rot": (-14, 0, -18)}


def rest():
    return {"arm_r": dict(ARM), "throttle": {}, "_view": {}}


def pose_idle(t):
    return rest()


def pose_chain(t):
    """t от 0 до 1: цепь проходит один шаг."""
    out = {}
    for i in range(TEETH):
        s = i * PITCH
        y0, z0, a0 = track(s)
        y1, z1, a1 = track(s + t * PITCH)
        d = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        out[f"tooth_{i}"] = {"pos": (0, y1 - y0, z1 - z0), "rot": (math.degrees(d), 0, 0)}
    return out


def _swing(wind, strike, follow, t, hold=0.14, hit=0.3):
    """Замах, быстрый удар с разгоном и долгий возврат: вся тяжесть оружия в этой кривой."""
    return kf(t, [(0, (0, 0, 0)), (hold, wind, "out"), (hit, strike, "in"), (hit + 0.12, follow, "out"), (1, (0, 0, 0))])


def _make_swing(wp, wr, sp, sr, fp, fr):
    def pose(t):
        p = rest()
        p["_view"] = {"pos": _swing(wp, sp, fp, t), "rot": _swing(wr, sr, fr, t)}
        p["throttle"] = {"rot": (kf(t, [(0, 0.0), (0.1, -22.0, "out"), (0.7, -22.0), (1, 0.0)]), 0, 0)}
        return p
    return pose


# rot: (наклон вперёд, дуга в плоскости экрана, поворот). Справа налево, обратно слева направо, рубящий сверху
pose_swing_a = _make_swing((-0.1, 0.04, 0.14), (-8, -28, 0), (0.3, -0.06, 0.1), (8, 62, 0), (0.38, -0.02, 0.04), (14, 80, 0))
pose_swing_b = _make_swing((0.34, 0.02, 0.14), (0, 58, 0), (-0.02, -0.08, 0.12), (8, -30, 0), (-0.08, -0.04, 0.06), (14, -44, 0))
pose_swing_c = _make_swing((0.0, 0.12, 0.24), (-30, 8, 0), (0.1, -0.14, 0.02), (18, 12, 0), (0.12, -0.1, -0.04), (28, 14, 0))


def pose_equip(t):
    p = rest()
    p["_view"] = {"pos": kf(t, [(0, (0.04, 0.05, -0.42)), (1, (0, 0, 0), "out")]), "rot": kf(t, [(0, (56, 0, 26)), (1, (0, 0, 0), "out")])}
    return p


# цепной меч бьёт примерно раз в 0,9 с: темп задан в ChainswordItem
CLIPS = {
    "idle": {"length": 0.2, "pose": pose_idle, "loop": True},
    "chain": {"length": 0.4, "pose": pose_chain, "loop": True},
    "swing_a": {"length": 0.72, "pose": pose_swing_a},
    "swing_b": {"length": 0.72, "pose": pose_swing_b},
    "swing_c": {"length": 0.8, "pose": pose_swing_c},
    "equip": {"length": 0.5, "pose": pose_equip},
}

m = Machine("chainsword_3d")
build(m)
sc, tris = m.build("WB_Chainsword")
light_scene(sc, 60)
print("костей:", len(m.objects), "треугольников:", tris)
