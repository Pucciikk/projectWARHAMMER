"""
Горн обломков (salvage_forge): 3×3×3. Кирпичный горн с пламенем, обвязка из корабельной обшивки, сбоку мехи,
спереди торчит лом. Анимация work.active — раздувание мехов; misc.idle — ровный огонь.
"""
import math
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "kit.py"), encoding="utf-8").read())

LOOP, STEPS = 1.4, 28
FIRE = (0.0, 0.0, 0.52)     # низ пламени
BX = 1.18                   # ось мехов по X


def frame(m):
    f = m.bone("frame")
    # ---- цоколь: обшивка и кирпичная кладка
    f.box((-1.48, -1.48, 0), (1.48, 1.48, 0.28), "hull", bevel=0.04)
    f.box((-1.32, -1.32, 0.28), (0.82, 1.32, 1.32), "brick", bevel=0.03)
    for z in (0.62, 0.96):
        f.box((-1.34, -1.34, z - 0.015), (0.84, 1.34, z + 0.015), "dark")
    # пояс из обшивки и заклёпки
    f.box((-1.36, -1.36, 1.32), (0.86, 1.36, 1.46), "hull", bevel=0.02)
    for i in range(6):
        x = -1.2 + i * 0.4
        f.bolt((x, -1.36, 1.39), "Y", 0.028, -0.018, "brass")
    # устье: арка, чаша углей
    f.plate_xz([(-0.62, 0.3), (0.6, 0.3), (0.6, 0.86), (0.28, 1.14), (-0.3, 1.14), (-0.62, 0.86)], -1.36, -1.32, "dark")
    f.plate_xz([(-0.5, 0.36), (0.48, 0.36), (0.48, 0.82), (0.22, 1.05), (-0.24, 1.05), (-0.5, 0.82)], -1.38, -1.36, "fire")
    for x in (-0.33, -0.1, 0.13, 0.36):
        f.box((x - 0.018, -1.42, 0.36), (x + 0.018, -1.38, 1.04), "dark")
    f.lathe((FIRE[0], FIRE[1], 1.46), [(0.62, 0), (0.62, 0.1), (0.5, 0.12), (0.5, 0.02)], 14, "dark", base=False)
    f.lathe((FIRE[0], FIRE[1], 1.5), [(0.5, 0), (0.5, 0.01)], 14, "fire", base=False)
    # ---- зонт и дымовая труба
    for x, y in ((-0.72, -0.72), (0.72, -0.72), (-0.72, 0.72), (0.72, 0.72)):
        f.beam((x, y, 1.46), (x * 0.82, y * 0.82, 2.2), 0.09, 0.09, "dark")
    f.loft([(2.2, 0.84, 0.84, 0), (2.48, 0.46, 0.46, 0), (2.56, 0.26, 0.26, 0)], "rust")
    f.lathe((0, 0, 2.5), [(0.22, 0), (0.22, 0.42), (0.28, 0.44), (0.28, 0.48)], 10, "rust", base=False)
    # ---- лом: куски обшивки торчат из углей и лежат у стены
    f.beam((-0.42, -0.2, 1.46), (-0.18, -0.02, 1.86), 0.24, 0.05, "hull")
    f.beam((0.28, 0.22, 1.46), (0.06, 0.18, 1.82), 0.2, 0.05, "rust")
    for x, y, r in ((-1.2, -1.2, 18), (-0.86, -1.25, -22)):
        f.box((x - 0.22, y - 0.12, 0.28), (x + 0.22, y + 0.12, 0.42), "rust", rot=("Z", r), bevel=0.01)
    # ---- опора мехов и сопло
    f.box((0.86, -0.72, 0.28), (1.46, 0.72, 0.42), "wood", bevel=0.015)
    f.pipe([(0.86, 0, 0.66), (0.5, 0, 0.72)], 0.08, 8, "dark")
    f.box((BX - 0.28, -0.46, 0.42), (BX + 0.28, 0.46, 0.5), "wood", bevel=0.012)
    f.seal((0.2, -1.36, 1.28), "Y", -1) if False else None
    f.seal((-0.86, -1.36, 1.2), "Y", -1)


def moving(m):
    # ---- верхняя доска мехов
    top = m.bone("bellows_top", (BX, 0.42, 0.86))
    top.box((BX - 0.27, -0.44, 0.84), (BX + 0.27, 0.44, 0.9), "wood", bevel=0.012)
    top.lathe((BX, -0.42, 0.92), [(0.04, 0), (0.03, 0.3)], 5, "steel", base=False)
    top.box((BX - 0.1, -0.46, 1.2), (BX + 0.1, -0.38, 1.26), "dark")
    # ---- кожа: сжимается вместе с доской (масштаб от оси на задней кромке)
    fold = m.bone("bellows_folds", (BX, 0.42, 0.5))
    fold.loft([(0.5, 0.26, 0.42, 0), (0.6, 0.29, 0.45, 0), (0.68, 0.24, 0.4, 0), (0.76, 0.28, 0.43, 0), (0.84, 0.25, 0.41, 0)], "rubber") if False else None
    n = 12
    sections = [(0.5, 0.26, 0.42), (0.6, 0.29, 0.45), (0.68, 0.24, 0.4), (0.76, 0.28, 0.43), (0.84, 0.25, 0.41)]
    rings = []
    for z, hx, hy in sections:
        rings.append([fold.bm.verts.new((BX + hx * sx, hy * sy, z)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    for a, b in zip(rings, rings[1:]):
        for i in range(4):
            j = (i + 1) % 4
            face = fold.bm.faces.new((a[i], a[j], b[j], b[i]))
            face.material_index = NAMES.index("rubber")
    # ---- живой огонь над чашей
    fire = m.bone("fire", (FIRE[0], FIRE[1], 1.5))
    for x, y, h in ((-0.2, -0.1, 0.46), (0.18, 0.05, 0.56), (-0.02, 0.2, 0.42), (0.05, -0.22, 0.36)):
        fire.lathe((x, y, 1.5), [(0.14, 0), (0.1, h * 0.5), (0, h)], 5, "fire", base=False)


def pose_flame(t, gain=1.0):
    a = 2 * math.pi * t
    return 1 + gain * (0.2 * math.sin(a * 3) + 0.1 * math.sin(a * 7 + 1))


def pose(t):
    a = 2 * math.pi * t
    k = 0.5 + 0.5 * math.cos(a)        # 1 — мехи раскрыты, 0 — сжаты
    drop = 0.26 * (1 - k)
    tilt = -math.degrees(math.atan2(drop, 0.84))
    return {
        "bellows_top": {"rot": (tilt, 0, 0)},
        "bellows_folds": {"scale": (1, 1, 1 - 0.68 * (1 - k))},
        # огонь растёт, когда мехи сжимаются
        "fire": {"scale": (1, 1, pose_flame(t, 1.0) + 0.35 * (1 - k))},
    }


# в простое мехи раскрыты и не двигаются, огонь ровный, без раздувания
def idle_tracks():
    keys = {}
    for i in range(17):
        t = i / 16
        keys[f"{2.0 * t:.4f}"] = [1.0, round(pose_flame(t, 0.5) * 0.8, 3), 1.0]
    return {"loop": True, "animation_length": 2.0, "bones": {"fire": {"scale": keys}}}


m = Machine("salvage_forge")
frame(m)
moving(m)
sc, tris = m.build("WB_SalvageForge")
light_scene(sc, int(LOOP * 24))
auto_animate(m.objects, sc, pose, LOOP)
tracks = lambda: auto_tracks(pose, LOOP, STEPS)
print("костей:", len(m.objects), "треугольников:", tris)
