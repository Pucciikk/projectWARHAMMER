"""
Когитаторий (cogitatorium): 5×5×4. Зал логических машин: ряды шкафов с лампами и катушками лент, посредине стол с платой и
паяльной рукой, сверху голова сервитора в проводах, из щели ползёт перфолента. Лампы мигают, катушки крутятся.
"""
import math
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "kit.py"), encoding="utf-8").read())

LOOP, STEPS = 4.0, 48
W = 2.25
BANK_Y = (0.55, 1.45)      # ряды шкафов по глубине
REELS = ((-1.65, 1.82), (-0.95, 1.82), (0.95, 1.82), (1.65, 1.82))   # x, z катушек на задних шкафах


def bank(f, x0, x1, y, z1, front=-1):
    """Шкаф с лицевой панелью, лампами и решёткой."""
    f.box((x0, y - 0.28, 0.38), (x1, y + 0.28, z1), "hull", bevel=0.03)
    fy = y + front * 0.28
    f.box((x0 + 0.04, fy + front * 0.012, 0.5), (x1 - 0.04, fy, z1 - 0.1), "dark")
    n = int((x1 - x0) / 0.2)
    for k in range(n):
        x = x0 + 0.12 + k * 0.2
        f.lathe((x, fy + front * 0.02, z1 - 0.28), [(0.04, 0), (0.04, front * 0.02)], 6, "brass", "Y", base=False)
        f.box((x - 0.06, fy + front * 0.018, 0.56), (x + 0.06, fy + front * 0.012, 0.9), "rust")


def frame(m):
    f = m.bone("frame")
    f.plinth(-2.48, -2.48, 2.48, 2.48)
    f.box((-W, -W, 0.3), (W, W, 0.38), "dark", bevel=0.012)
    # ---- стойки, балки и готическая крыша-каркас
    for sx in (-1, 1):
        for y in (-W + 0.08, -0.2, W - 0.08):
            f.box((sx * W - 0.12, y - 0.12, 0.38), (sx * W + 0.12, y + 0.12, 3.15), "hull", bevel=0.025)
            f.lathe((sx * W, y, 3.27), [(0.09, 0), (0.015, 0.34)], 4, "dark", phase=math.pi / 4, base=False)
        f.box((sx * W - 0.1, -W, 3.05), (sx * W + 0.1, W, 3.27), "dark", bevel=0.02)
    for y in (-W + 0.08, W - 0.08):
        f.box((-W, y - 0.1, 3.05), (W, y + 0.1, 3.27), "dark", bevel=0.02)
    f.box((-2.46, -2.46, 3.27), (2.46, 2.46, 3.36), "dark", bevel=0.02)
    f.loft([(3.36, 2.3, 2.3, 0), (3.92, 0.9, 0.9, 0)], "rust")
    for s1 in (-1, 1):
        for s2 in (-1, 1):
            f.beam((s1 * 2.3, s2 * 2.3, 3.37), (s1 * 0.9, s2 * 0.9, 3.93), 0.08, 0.08, "dark")
    f.box((-0.95, -0.95, 3.92), (0.95, 0.95, 3.98), "brass", bevel=0.012)
    f.box((-W, W - 0.1, 0.38), (W, W + 0.05, 3.05), "hull")
    # ---- шкафы: ряд у задней стены и два боковых
    bank(f, -2.1, -0.35, 1.72, 2.55)
    bank(f, 0.35, 2.1, 1.72, 2.55)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 2.1, sx * 1.55))
        f.box((x0, -0.1, 0.38), (x1, 1.2, 2.2), "hull", bevel=0.03)
        f.box((min(sx * 1.55, sx * 1.56), 0.0, 0.55), (max(sx * 1.55, sx * 1.56), 1.1, 1.95), "dark")
    # окна катушек на задних шкафах
    for x, z in REELS:
        f.lathe((x, 1.42, z), [(0.28, 0), (0.28, -0.02)], 12, "dark", "Y", base=False)
    # ---- центральный рабочий стол и стойка с платой
    f.box((-0.8, -0.72, 0.38), (0.8, 0.35, 0.92), "dark", bevel=0.03)
    f.box((-0.85, -0.78, 0.92), (0.85, 0.42, 0.98), "steel", bevel=0.012)
    f.box((-0.42, -0.5, 0.98), (0.42, 0.12, 1.0), "screen")
    for x in (-0.3, -0.1, 0.1, 0.3):
        f.box((x - 0.02, -0.46, 1.0), (x + 0.02, 0.08, 1.01), "brass")
    # ---- голова сервитора под куполом и пучки кабелей
    f.lathe((0, 1.28, 1.72), [(0.26, 0), (0.26, 0.55), (0.1, 0.65)], 10, "hull", base=False)
    f.skull(0, 1.05, 2.32, 0.72)
    f.gear((0, 1.08, 2.32), 0.46, 0.6, 0.05, 12, "brass", "Y")
    for s in (-1, 1):
        f.pipe([(s * 0.3, 1.0, 2.42), (s * 0.7, 1.3, 2.82), (s * 1.3, 1.5, 2.6)], 0.028, 5, "rubber")
        f.pipe([(s * 0.26, 1.0, 2.2), (s * 0.6, 1.25, 2.0), (s * 1.2, 1.45, 1.75)], 0.028, 5, "rubber")
    # ---- щель перфоленты слева
    f.box((-1.56, 0.6, 1.0), (-1.46, 1.05, 1.25), "dark", bevel=0.01)
    f.box((-1.46, 0.72, 0.38), (-1.1, 0.95, 0.46), "parchment")
    f.seal((-0.9, 1.44, 2.0), "Y", -1)
    f.seal((0.9, 1.44, 2.0), "Y", -1)
    f.seal((W, 0.3, 2.3), "X", 1)


def moving(m):
    # ---- катушки лент: две пары вращаются навстречу
    for i, (x, z) in enumerate(REELS):
        r = m.bone(f"reel_{i}", (x, 1.4, z))
        r.ring((x, 1.4, z), 0.08, 0.24, 0.05, 12, "steel", "Y")
        for k in range(3):
            a = k * 2 * math.pi / 3
            r.beam((x, 1.4, z), (x + 0.2 * math.cos(a), 1.4, z + 0.2 * math.sin(a)), 0.03, 0.03, "dark")
    # ---- лампы трёх групп мигают по очереди
    for i in range(3):
        l = m.bone(f"lamps_{i}", (0, 1.4, 2.3))
        for x0, x1 in ((-2.1, -0.35), (0.35, 2.1)):
            n = int((x1 - x0) / 0.2)
            for k in range(n):
                if k % 3 != i:
                    continue
                x = x0 + 0.12 + k * 0.2
                l.lathe((x, 1.4, 2.27), [(0.03, 0), (0.03, -0.015)], 6, "stain_red" if i == 0 else "stain_gold" if i == 1 else "screen", "Y", base=False)
    # ---- паяльная рука над платой
    a = m.bone("solder", (1.15, -0.2, 1.05))
    a.lathe((1.15, -0.2, 0.98), [(0.2, 0), (0.15, 0.2), (0.08, 0.3)], 8, "dark", base=False)
    a.beam((1.15, -0.2, 1.28), (0.65, -0.2, 1.55), 0.06, 0.06, "steel")
    a.beam((0.65, -0.2, 1.55), (0.1, -0.2, 1.14), 0.04, 0.04, "brass")
    a.lathe((0.1, -0.2, 1.02), [(0.008, 0), (0.035, 0.12)], 6, "dark", base=False)
    a.lathe((0.1, -0.2, 1.0), [(0.03, 0), (0.005, 0.03)], 5, "fire", base=False)
    # ---- перфолента: ползёт вниз из щели
    t = m.bone("tape", (-1.42, 0.83, 1.0))
    t.box((-1.46, 0.75, 0.45), (-1.43, 0.91, 1.1), "parchment")
    for k in range(6):
        t.box((-1.47, 0.79, 0.5 + k * 0.1), (-1.46, 0.87, 0.53 + k * 0.1), "dark")


def pose(t):
    a = 2 * math.pi * t
    p = {
        "solder": {"rot": (0, 0, -14 * math.sin(2 * a))},
        "tape": {"pos": (0, 0, -0.1 * ((t * 4) % 1))},
    }
    for i in range(4):
        p[f"reel_{i}"] = {"rot": (0, (1 if i % 2 else -1) * 360 * 2 * t, 0)}
    for i in range(3):
        k = 1 if math.sin(a * (5 + i) + i * 2) > -0.3 else 0
        p[f"lamps_{i}"] = {"scale": (k, k, k)}
    return p


m = Machine("cogitatorium")
frame(m)
moving(m)
sc, tris = m.build("WB_Cogitatorium")
light_scene(sc, int(LOOP * 24))
auto_animate(m.objects, sc, pose, LOOP)
tracks = lambda: auto_tracks(pose, LOOP, STEPS)
print("костей:", len(m.objects), "треугольников:", tris)
