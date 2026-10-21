#!/usr/bin/env python3
"""
Генератор модели и текстуры дредноута (v2, по референсам автора).

Координаты в описании — пространство машины в 1/32 блока:
    R — вправо (с точки зрения самого дредноута), U — вверх от земли, F — вперёд.
Рендерер масштабирует модель в 0.5, поэтому на 1 блок приходится 32 текселя:
текстура вдвое детальнее обычной майнкрафтовской.

    python3 tools/dreadnought/gen.py          # пишет модель и текстуры в ресурсы
    python3 tools/dreadnought/gen.py --dev    # плюс копирует в build/, чтобы F3+T в запущенной игре подхватил

Результат:
    src/main/resources/assets/warpbound/models/entity/dreadnought.json
    src/main/resources/assets/warpbound/textures/entity/dreadnought.png
    src/main/resources/assets/warpbound/textures/entity/dreadnought_glow.png
"""
import json
import math
import os
import random
import shutil
import sys

import numpy as np
from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEX = 1024
rng = random.Random(40000)

# =============================================================== описание модели

PARTS = []  # (имя, родитель, точка вращения (R,U,F), поворот (рад), [кубы])


def part(name, parent, pivot, cubes, rot=(0, 0, 0)):
    PARTS.append([name, parent, pivot, rot, list(cubes)])


def box(a, b, mat, deco=None, rot=None, center=None):
    """Куб от угла a до угла b (R,U,F). rot — поворот вокруг center (градусы, оси R,U,F)."""
    lo = tuple(min(a[i], b[i]) for i in range(3))
    hi = tuple(max(a[i], b[i]) for i in range(3))
    return {"lo": lo, "hi": hi, "mat": mat, "deco": deco or {}, "rot": rot, "center": center}


def cyl(axis, c, apothem, start, end, mat, deco=None):
    """Восьмигранный цилиндр из трёх кубов: крест и квадрат по диагоналям.
    Повёрнутые на 45° квадраты дали бы звезду, а не восьмигранник."""
    i = "RUF".index(axis)
    o = [j for j in range(3) if j != i]
    narrow = max(1, round(apothem * 0.414))
    corner = max(1, round(apothem * 0.707))
    out = []
    for h0, h1 in ((apothem, narrow), (narrow, apothem), (corner, corner)):
        a = [0, 0, 0]
        b = [0, 0, 0]
        a[i], b[i] = start, end
        a[o[0]], b[o[0]] = c[0] - h0, c[0] + h0
        a[o[1]], b[o[1]] = c[1] - h1, c[1] + h1
        out.append(box(a, b, mat, deco))
    return out


def mirror(cubes):
    out = []
    for c in cubes:
        d = dict(c["deco"])
        if "right" in d or "left" in d:
            r, l = d.pop("right", None), d.pop("left", None)
            if l: d["right"] = l
            if r: d["left"] = r
        lo = (-c["hi"][0], c["lo"][1], c["lo"][2])
        hi = (-c["lo"][0], c["hi"][1], c["hi"][2])
        center = None if c["center"] is None else (-c["center"][0], c["center"][1], c["center"][2])
        rot = None if c["rot"] is None else (c["rot"][0], -c["rot"][1], -c["rot"][2])
        out.append({"lo": lo, "hi": hi, "mat": c["mat"], "deco": d, "rot": rot, "center": center})
    return out


def mp(p):
    return (-p[0], p[1], p[2])


# ---------- ноги (правая; левая — зеркало)
LEG = [
    # огромный приводной барабан бедра
    *cyl("R", (46, 0), 12, 8, 34, "iron", {"right": "drum_end", "front": "drum", "back": "drum", "top": "drum"}),
    *cyl("R", (46, 0), 8, 34, 37, "steel", {"right": "drum_end"}),
    box((16, 30, -7), (28, 42, 5), "iron", {"front": "piston"}),            # шатун до колена
]
SHIN = [
    box((15, 23, -7), (29, 33, 7), "iron", {}),                                # колено
    box((11, 9, -8), (33, 29, 10), "blue", {"right": "plate", "left": "plate"}),
    box((12, 12, 10), (32, 29, 14), "blue", {"front": "knee"}),               # лобовой щиток с черепом
    box((18, 8, -13), (26, 25, -8), "iron", {"back": "piston"}),             # задний поршень
    box((10, 25, -9), (34, 29, 11), "blue_edge", {}),                         # верхний край щитка
]
FOOT = [
    box((14, 4, -9), (30, 12, 9), "iron", {}),                                 # голеностоп
    box((8, 0, -14), (36, 5, 14), "iron", {"front": "hazard_none"}),
    box((8, 0, 11), (21, 8, 27), "blue", {"front": "toe", "top": "toe_top"}),
    box((23, 0, 11), (36, 8, 27), "blue", {"front": "toe", "top": "toe_top"}),
    box((14, 0, -22), (30, 7, -11), "blue", {"back": "toe", "top": "toe_top"}),
    box((5, 0, -6), (9, 6, 8), "blue", {}),                                    # боковые упоры
    box((35, 0, -6), (39, 6, 8), "blue", {}),
]
part("body", "root", (0, 50, 0), [
    box((-14, 34, -12), (14, 58, 12), "iron", {"front": "grill"}),           # таз
    box((-25, 52, -18), (25, 61, 16), "iron", {"front": "ribs", "back": "ribs"}),  # поясное кольцо
    box((-9, 32, 12), (9, 54, 17), "blue_trim", {"front": "codpiece"}),       # щиток между ног
    box((-14, 40, -4), (14, 50, 4), "steel", {}),                              # ось бёдер
    box((-7, 26, 17), (-2, 40, 18), "seal", {"front": "seal"}),
])
part("leg_r", "body", (22, 46, 0), LEG)
part("shin_r", "leg_r", (22, 30, 0), SHIN)
part("foot_r", "shin_r", (22, 10, 0), FOOT)
part("leg_l", "body", mp((22, 46, 0)), mirror(LEG))
part("shin_l", "leg_l", mp((22, 30, 0)), mirror(SHIN))
part("foot_l", "shin_l", mp((22, 10, 0)), mirror(FOOT))

# ---------- корпус
part("torso", "body", (0, 60, 0), [
    # саркофаг — выступает вперёд из корпуса
    box((-14, 58, -6), (14, 114, 30), "blue", {"front": "sarcophagus", "right": "cables", "left": "cables", "top": "plate"}),
    box((-12, 114, -4), (12, 118, 26), "blue_edge", {}),
    # бронеблоки по бокам
    box((15, 60, -26), (42, 112, 22), "blue", {"front": "slab_r", "right": "slab_side", "top": "slab_top", "back": "plate"}),
    box((-42, 60, -26), (-15, 112, 22), "blue", {"front": "slab_l", "left": "slab_side", "top": "slab_top", "back": "plate"}),
    # скошенные верхние кромки бронеблоков, как на референсах
    box((16, 106, 13), (41, 109, 25), "blue_edge", {"top": "plate"}, rot=(45, 0, 0), center=(28, 109, 19)),
    box((-41, 106, 13), (-16, 109, 25), "blue_edge", {"top": "plate"}, rot=(45, 0, 0), center=(-28, 109, 19)),
    box((15, 54, -20), (38, 61, 16), "iron", {"front": "ribs"}),               # механика под блоками
    box((-38, 54, -20), (-15, 61, 16), "iron", {"front": "ribs"}),
    # кабели в щелях между саркофагом и блоками
    box((13, 70, 18), (16, 100, 26), "cable_bundle", {}),
    box((-16, 70, 18), (-13, 100, 26), "cable_bundle", {}),
    # двигатель сзади
    box((-24, 64, -40), (24, 106, -26), "iron", {"back": "engine", "right": "vents", "left": "vents", "top": "ribs"}),
    box((-12, 72, -43), (12, 100, -40), "blue_trim", {"back": "back_grill"}),
    box((-24, 112, -26), (24, 116, 0), "iron", {"top": "deck"}),               # верхняя палуба
    box((-8, 116, -22), (-4, 120, -6), "steel", {}),                           # рёбра
    box((-2, 116, -22), (2, 120, -6), "steel", {}),
    box((4, 116, -22), (8, 120, -6), "steel", {}),
    # дымовые трубы
    *cyl("U", (13, -33), 5, 98, 132, "iron", {"front": "perforated", "back": "perforated", "right": "perforated", "left": "perforated", "top": "pipe_top"}),
    *cyl("U", (-13, -33), 5, 98, 132, "iron", {"front": "perforated", "back": "perforated", "right": "perforated", "left": "perforated", "top": "pipe_top"}),
    *cyl("U", (13, -33), 6, 96, 99, "steel", {}),
    *cyl("U", (-13, -33), 6, 96, 99, "steel", {}),
])
part("head", "torso", (0, 116, 16), [
    box((-6, 114, 12), (6, 122, 28), "iron", {"front": "sensor"}),
    box((-4, 116, 28), (4, 120, 30), "lens", {}),
])

# ---------- правая рука: штурмовая пушка
part("arm_r", "torso", (46, 86, 0), [
    *cyl("R", (86, 0), 10, 41, 50, "iron", {"right": "drum_end"}),
    box((50, 62, -18), (66, 98, 18), "blue", {"right": "gun_side", "top": "slab_top", "front": "plate", "left": "plate"}),
    box((60, 52, -6), (67, 64, 6), "steel", {"right": "belt", "front": "belt"}),   # лента
])
GUN = [
    box((50, 70, 14), (66, 90, 32), "iron", {"front": "ribs", "right": "ribs"}),
    box((54, 76, 32), (62, 84, 70), "iron", {}),
    *cyl("F", (58, 80), 10, 36, 40, "steel", {}),
    *cyl("F", (58, 80), 10, 60, 64, "steel", {}),
    *cyl("F", (58, 80), 9, 70, 74, "iron", {"front": "muzzles"}),
]
for k in range(6):
    a = math.radians(30 + 60 * k)
    cx, cy = 58 + 5.5 * math.cos(a), 80 + 5.5 * math.sin(a)
    cx, cy = round(cx), round(cy)
    GUN.append(box((cx - 2, cy - 2, 32), (cx + 2, cy + 2, 72), "barrel", {"front": "bore"}))
part("gun", "arm_r", (58, 80, 8), GUN)

# ---------- левая рука: силовой кулак
part("arm_l", "torso", (-46, 84, 0), [
    *cyl("R", (84, 0), 10, -50, -41, "iron", {"left": "drum_end"}),
    box((-64, 72, -16), (-50, 96, 10), "blue", {"left": "fist_shoulder", "top": "slab_top", "front": "plate"}),
])
part("fist", "arm_l", (-58, 74, 6), [
    *cyl("F", (-58, 72), 13, -12, 30, "blue", {"front": "plate", "top": "forearm", "left": "forearm", "right": "forearm", "bottom": "forearm"}),
    *cyl("F", (-58, 72), 11, 30, 35, "iron", {}),
    box((-69, 61, 34), (-47, 83, 41), "iron", {"front": "knuckles"}),
    box((-68, 76, 41), (-61, 83, 58), "claw", {"front": "claw_tip"}),           # пальцы
    box((-58, 76, 41), (-51, 83, 58), "claw", {"front": "claw_tip"}),
    box((-50, 66, 41), (-45, 76, 55), "claw", {"front": "claw_tip"}),
    box((-62, 59, 41), (-54, 66, 54), "claw", {"front": "claw_tip"}),           # большой палец
    box((-48, 64, 6), (-44, 80, 26), "lens_blue", {}),                          # катушка поля
])

# =============================================================== развёртка

def faces(u, v, w, h, d):
    return {
        "top": (u + d, v, w, d),
        "bottom": (u + d + w, v, w, d),
        "right": (u, v + d, d, h),     # -x модели = правый борт машины
        "front": (u + d, v + d, w, h),
        "left": (u + d + w, v + d, d, h),
        "back": (u + d + w + d, v + d, w, h),
    }


class Packer:
    def __init__(self, size):
        self.size, self.x, self.y, self.row = size, 0, 0, 0

    def place(self, w, h):
        if self.x + w > self.size:
            self.x, self.y, self.row = 0, self.y + self.row, 0
        if self.y + h > self.size:
            raise SystemExit("развёртка не влезла в %d" % self.size)
        at = (self.x, self.y)
        self.x += w + 1
        self.row = max(self.row, h + 1)
        return at


# =============================================================== палитра и кисти

def hx(s):
    return np.array([int(s[i:i + 2], 16) for i in (1, 3, 5)], dtype=float)


MATS = {
    "blue": (hx("#4469b4"), hx("#7c9ee0"), hx("#22386e")),
    "blue_trim": (hx("#4469b4"), hx("#7c9ee0"), hx("#22386e")),
    "blue_edge": (hx("#4a70bd"), hx("#88a8e6"), hx("#2a4580")),
    "iron": (hx("#2c2e33"), hx("#5b606a"), hx("#151619")),
    "steel": (hx("#5a5f68"), hx("#a3a9b3"), hx("#2e3136")),
    "barrel": (hx("#3a3d43"), hx("#8d939c"), hx("#1b1c1f")),
    "claw": (hx("#34363b"), hx("#7d828b"), hx("#18191c")),
    "seal": (hx("#dccca2"), hx("#f1e6c6"), hx("#a8966c")),
    "lens": (hx("#d01e12"), hx("#ff7050"), hx("#700a06")),
    "lens_blue": (hx("#3a6fd0"), hx("#a8d8ff"), hx("#1a3170")),
    "cable_bundle": (hx("#2a2a2c"), hx("#555555"), hx("#111111")),
}
GOLD = (hx("#c9a24a"), hx("#f3d98a"), hx("#7b5a1c"))
BONE = hx("#e4dcc4")
WHITE = hx("#ebe8de")
WAX = hx("#9a1a12")
RUST = hx("#7a3e1c")
RED_LIGHT, GREEN_LIGHT, ORANGE_LIGHT = hx("#ff3a22"), hx("#4cff6a"), hx("#ffa23a")

tex = np.zeros((TEX, TEX, 4), dtype=float)
glow = np.zeros((TEX, TEX, 4), dtype=np.uint8)


def px(x, y, c, a=255):
    if 0 <= x < TEX and 0 <= y < TEX:
        tex[y, x, :3] = np.clip(c, 0, 255)
        tex[y, x, 3] = a


def blend(x, y, c, k):
    if 0 <= x < TEX and 0 <= y < TEX:
        tex[y, x, :3] = np.clip(tex[y, x, :3] * (1 - k) + np.asarray(c) * k, 0, 255)


def lit(x, y, c, strength=255):
    px(x, y, c)
    if 0 <= x < TEX and 0 <= y < TEX:
        glow[y, x] = (int(min(255, c[0])), int(min(255, c[1])), int(min(255, c[2])), strength)


def rect(r, x, y, w, h, c):
    for j in range(h):
        for i in range(w):
            px(r[0] + x + i, r[1] + y + j, c + rng.uniform(-5, 5))


def frame(r, x, y, w, h, mat, t=1):
    base, light, shadow = mat
    for k in range(t):
        for i in range(x + k, x + w - k):
            px(r[0] + i, r[1] + y + k, light if k == 0 else base)
            px(r[0] + i, r[1] + y + h - 1 - k, shadow if k == 0 else base * 0.9)
        for j in range(y + k, y + h - k):
            px(r[0] + x + k, r[1] + j, base * 1.05)
            px(r[0] + x + w - 1 - k, r[1] + j, base * 0.8)


def sprite(r, x, y, art, palette):
    for j, row in enumerate(art):
        for i, ch in enumerate(row):
            if ch in palette:
                c = palette[ch]
                if isinstance(c, tuple) and c[0] == "glow":
                    lit(r[0] + x + i, r[1] + y + j, c[1])
                else:
                    px(r[0] + x + i, r[1] + y + j, c + rng.uniform(-6, 6))


def rivet_row(r, x, y, w, step=4):
    for i in range(x, x + w, step):
        px(r[0] + i, r[1] + y, hx("#a8b0bc"))
        px(r[0] + i + 1, r[1] + y + 1, hx("#1c2a4c"))


def base_paint(r, mat, face, w, h):
    """Основа: шум, вертикальный градиент грязи, фаски, сколы, ржавые потёки."""
    base, light, shadow = MATS[mat]
    x0, y0 = r[0], r[1]
    tint = {"top": 1.1, "bottom": 0.62}.get(face, 1.0)
    painted = mat.startswith("blue")
    for y in range(h):
        grime = 1.0 - 0.18 * (y / max(1, h - 1)) ** 1.6 if face not in ("top", "bottom") else 1.0
        for x in range(w):
            n = rng.gauss(0, 3.0)
            c = base * tint * grime + n
            px(x0 + x, y0 + y, c)
    if w >= 3 and h >= 3:
        for x in range(w):
            px(x0 + x, y0, light * tint)
            px(x0 + x, y0 + h - 1, shadow)
        for y in range(h):
            blend(x0, y0 + y, light, 0.5)
            px(x0 + w - 1, y0 + y, shadow * 1.1)
    if painted and w * h > 60:
        # сколы по краям: сначала тёмная грунтовка, в середине — голый металл
        for _ in range(max(1, (w + h) // 9)):
            side = rng.randrange(4)
            t = rng.random()
            ex = int(t * (w - 1)) if side < 2 else (1 if side == 2 else w - 2)
            ey = int(t * (h - 1)) if side >= 2 else (1 if side == 0 else h - 2)
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    if rng.random() < 0.55:
                        blend(x0 + ex + dx, y0 + ey + dy, hx("#1d2433"), 0.7)
            px(x0 + ex, y0 + ey, hx("#9aa0a8"))
        # царапины в середине
        for _ in range(w * h // 420):
            sx, sy = rng.randrange(w), rng.randrange(h)
            for k in range(rng.randrange(2, 6)):
                blend(x0 + min(w - 1, sx + k), y0 + min(h - 1, sy + k // 2), light, 0.45)
        # ржавые потёки от верхнего края
        if face not in ("top", "bottom") and h > 12:
            for _ in range(max(1, w // 14)):
                sx = rng.randrange(1, max(2, w - 1))
                length = rng.randrange(h // 5, h // 2)
                for k in range(length):
                    blend(x0 + sx, y0 + 2 + k, RUST, 0.38 * (1 - k / length))
    if not painted and w * h > 20:
        for _ in range(w * h // 120):
            sx, sy = rng.randrange(w), rng.randrange(h)
            blend(x0 + sx, y0 + sy, light, 0.35)
        if face not in ("top", "bottom") and h > 10:
            for _ in range(max(1, w // 18)):
                sx = rng.randrange(w)
                length = rng.randrange(h // 4, h)
                for k in range(length):
                    blend(x0 + sx, y0 + k, RUST, 0.25 * (1 - k / length))
    if mat == "blue_trim" and w >= 6 and h >= 6:
        frame(r, 0, 0, w, h, GOLD, 1)


# ---------- пиксель-арт (собственные рисунки)
SKULL = [
    "..####..",
    ".######.",
    "########",
    "#..##..#",
    "#..##..#",
    "########",
    ".##..##.",
    "..####..",
    "..#.#.#.",
]
WINGS = [  # свой крылатый знак для саркофага, 24x9
    "##....................##",
    "###..................###",
    ".####..............####.",
    ".######..........######.",
    "..#######......#######..",
    "...#######....#######...",
    "....######....######....",
    ".....####......####.....",
    "......##........##......",
]
EMBLEM = [  # крылатый клинок — герб ордена (своя эмблема)
    ".......##.......",
    "......####......",
    "......####......",
    "#.....####.....#",
    "##....####....##",
    "###...####...###",
    ".###..####..###.",
    "..############..",
    "...##########...",
    ".....######.....",
    "......####......",
    "......####......",
    ".......##.......",
]
LAUREL = [
    "#..........#",
    "##........##",
    ".#........#.",
    ".##......##.",
    "..##....##..",
    "...######...",
]
NUM_IV = [
    "###.#...#",
    ".#..#...#",
    ".#..#...#",
    ".#...#.#.",
    ".#...#.#.",
    ".#....#..",
    "###...#..",
]


def skull(r, x, y, bone=BONE, eye=hx("#141414")):
    sprite(r, x, y, SKULL, {"#": bone})
    for (i, j) in ((1, 3), (2, 3), (1, 4), (2, 4), (5, 3), (6, 3), (5, 4), (6, 4)):
        px(r[0] + x + i, r[1] + y + j, eye)
    px(r[0] + x + 3, r[1] + y + 6, eye)
    px(r[0] + x + 4, r[1] + y + 6, eye)


def seal(r, x, y, w=5, h=12):
    rect(r, x + 1, y + 3, w - 2, h - 3, BONE)
    for j in range(5, h, 2):
        for i in range(1, w - 1):
            if rng.random() < 0.6:
                px(r[0] + x + i, r[1] + y + j, hx("#5e4c36"))
    for j in range(4):
        for i in range(w):
            if (i - w / 2 + 0.5) ** 2 + (j - 1.5) ** 2 < 5:
                px(r[0] + x + i, r[1] + y + j, WAX + rng.uniform(-12, 12))


def light(r, x, y, color, size=2):
    for j in range(size):
        for i in range(size):
            lit(r[0] + x + i, r[1] + y + j, color)
    px(r[0] + x - 1, r[1] + y - 1, hx("#16171a"))
    px(r[0] + x + size, r[1] + y + size, hx("#16171a"))


def slots(r, x, y, w, n, gap=3, glow_c=None):
    for k in range(n):
        for i in range(w):
            c = hx("#121316")
            if glow_c is not None:
                lit(r[0] + x + i, r[1] + y + k * gap, glow_c * (0.7 + 0.3 * rng.random()))
            else:
                px(r[0] + x + i, r[1] + y + k * gap, c)
                px(r[0] + x + i, r[1] + y + k * gap + 1, hx("#5a6070"))


def decorate(r, what, mat):
    x0, y0, w, h = r
    if what == "sarcophagus":
        frame(r, 0, 0, w, h, GOLD, 2)
        rect(r, 6, 4, w - 12, 3, hx("#1a1b1e"))                         # смотровая щель
        for i in range(7, w - 7):
            lit(x0 + i, y0 + 5, RED_LIGHT * 0.8, 200)
        frame(r, 4, 10, w - 8, h - 20, GOLD, 1)
        sprite(r, (w - 24) // 2, 14, WINGS, {"#": GOLD[1]})
        for j, row in enumerate(WINGS):
            for i, ch in enumerate(row):
                if ch == "#" and j > 4:
                    px(x0 + (w - 24) // 2 + i, y0 + 14 + j, GOLD[0])
        skull(r, (w - 8) // 2, 21)
        # свиток под знаком
        rect(r, 5, 33, w - 10, 6, BONE)
        for i in range(7, w - 7):
            if rng.random() < 0.65:
                px(x0 + i, y0 + 35 + rng.randrange(2), hx("#4a3a28"))
        rivet_row(r, 4, h - 6, w - 8, 4)
        seal(r, w - 9, h - 18, 5, 12)
    elif what == "slab_r":
        frame(r, 2, 2, w - 4, h - 4, MATS["blue"], 1)
        sprite(r, 6, 6, NUM_IV, {"#": WHITE})
        light(r, w - 7, 6, RED_LIGHT)
        sprite(r, 7, 17, LAUREL, {"#": GOLD[1]})
        skull(r, 9, 14, BONE)
        light(r, 6, 32, ORANGE_LIGHT, 3)
        seal(r, w - 9, 30, 5, 13)
        slots(r, 5, h - 10, w - 10, 3)
        rivet_row(r, 3, h - 3, w - 6, 4)
    elif what == "slab_l":
        frame(r, 2, 2, w - 4, h - 4, MATS["blue"], 1)
        sprite(r, (w - 16) // 2, 6, EMBLEM, {"#": WHITE})
        for k in range(3):                                                  # отметки отделения
            rect(r, 7 + k * 5, 23, 3, 8, WHITE * 0.92)
        light(r, 6, 36, RED_LIGHT)
        light(r, 11, 36, GREEN_LIGHT)
        rect(r, w - 12, 34, 8, 6, hx("#202226"))
        for i in range(w - 12, w - 4, 2):
            for j in range(34, 40, 2):
                px(x0 + i, y0 + j, hx("#55595f"))
        slots(r, 5, h - 10, w - 10, 3)
        rivet_row(r, 3, h - 3, w - 6, 4)
    elif what == "slab_side":
        slots(r, 6, 10, w - 12, 4)
        skull(r, w // 2 - 4, h - 22, BONE * 0.95)
        light(r, w - 8, 6, RED_LIGHT)
        rivet_row(r, 3, 3, w - 6, 5)
    elif what == "slab_top":
        for i in range(2, w - 2):
            px(x0 + i, y0 + h // 2, hx("#2a3f6e"))
        rivet_row(r, 2, 2, w - 4, 5)
    elif what == "plate":
        rivet_row(r, 2, 2, w - 4, 5)
        if h > 12:
            for i in range(2, w - 2):
                px(x0 + i, y0 + h // 2, MATS["blue"][2])
    elif what == "cables":
        for i in range(w):
            col = [hx("#a01810"), hx("#c8a020"), hx("#2a8a30"), hx("#1a1a1c")][(i // 2) % 4]
            for j in range(4, h - 4):
                px(x0 + i, y0 + j, col * (0.75 + 0.25 * math.sin(j * 0.7 + i)))
    elif what == "cable_bundle":
        pass
    elif what == "knee":
        for j in range(12):                                                 # белый круг с черепом
            for i in range(12):
                if (i - 5.5) ** 2 + (j - 5.5) ** 2 < 33:
                    px(x0 + (w - 12) // 2 + i, y0 + 5 + j, WHITE)
        skull(r, (w - 8) // 2, 7, hx("#1a1a1c"), WHITE)
        seal(r, w - 7, 3, 4, 10)
    elif what == "shin":
        rivet_row(r, 2, 2, w - 4, 4)
        frame(r, 1, 1, w - 2, h - 2, MATS["blue"], 1)
    elif what == "toe":
        rivet_row(r, 2, 2, w - 4, 4)
    elif what == "toe_top":
        for i in range(w):
            px(x0 + i, y0 + h - 2, MATS["blue"][2])
    elif what == "drum":
        for j in range(2, h, 5):
            for i in range(w):
                px(x0 + i, y0 + j, hx("#3a3d44"))
        for i in range(w // 3, w, w // 3):
            for j in range(h):
                px(x0 + i, y0 + j, hx("#141518"))
    elif what == "drum_end":
        cx, cy = w / 2 - 0.5, h / 2 - 0.5
        for j in range(h):
            for i in range(w):
                d2 = (i - cx) ** 2 + (j - cy) ** 2
                if d2 < (w / 2 - 1) ** 2 and d2 > (w / 2 - 3) ** 2:
                    px(x0 + i, y0 + j, hx("#5e646e"))
                if d2 < 3:
                    px(x0 + i, y0 + j, hx("#9aa0aa"))
    elif what == "piston":
        for j in range(1, h - 1):
            px(x0 + w // 2, y0 + j, hx("#a0a8b2"))
            px(x0 + w // 2 + 1, y0 + j, hx("#6a7078"))
    elif what == "grill" or what == "back_grill":
        frame(r, 1, 1, w - 2, h - 2, MATS["steel"], 1)
        for j in range(3, h - 3):
            for i in range(3, w - 3):
                if (i + j) % 3 == 0 or (i - j) % 3 == 0:
                    px(x0 + i, y0 + j, hx("#4a4e56"))
                else:
                    px(x0 + i, y0 + j, hx("#0e0f11"))
        if what == "back_grill":
            for j in range(h // 2 - 2, h // 2 + 2):
                for i in range(w // 2 - 2, w // 2 + 2):
                    lit(x0 + i, y0 + j, ORANGE_LIGHT)
    elif what == "codpiece":
        slots(r, 3, 5, w - 6, 4)
        rivet_row(r, 2, h - 3, w - 4, 3)
    elif what == "ribs":
        for i in range(1, w - 1, 4):
            for j in range(1, h - 1):
                px(x0 + i, y0 + j, hx("#55595f"))
                px(x0 + i + 1, y0 + j, hx("#101113"))
    elif what == "vents":
        slots(r, 2, 4, w - 4, max(1, (h - 8) // 4), 4, glow_c=ORANGE_LIGHT * 0.9)
    elif what == "engine":
        frame(r, 2, 2, w - 4, h - 4, MATS["steel"], 1)
        slots(r, 6, 6, 10, 6, 3, glow_c=ORANGE_LIGHT)
        slots(r, w - 16, 6, 10, 6, 3, glow_c=ORANGE_LIGHT)
        skull(r, w // 2 - 4, h - 14, BONE * 0.9)
    elif what == "deck":
        for i in range(0, w, 6):
            for j in range(h):
                px(x0 + i, y0 + j, hx("#15161a"))
    elif what == "perforated":
        for j in range(2, h - 2, 4):
            for i in range(1 + (j // 4) % 2 * 2, w - 1, 4):
                px(x0 + i, y0 + j, hx("#060606"))
                lit(x0 + i, y0 + j, hx("#ff6a2a") * 0.35, 120)
    elif what == "pipe_top":
        for j in range(2, h - 2):
            for i in range(2, w - 2):
                px(x0 + i, y0 + j, hx("#060606"))
    elif what == "sensor":
        rect(r, 2, 2, w - 4, h - 4, hx("#1a1b1e"))
        light(r, 3, 3, RED_LIGHT)
        light(r, w - 5, 3, GREEN_LIGHT)
    elif what == "gun_side":
        frame(r, 2, 2, w - 4, h - 4, MATS["blue"], 1)
        rect(r, 6, 8, w - 12, 10, hx("#1d1f23"))
        for i in range(7, w - 7, 3):
            for j in range(9, 17):
                px(x0 + i, y0 + j, hx("#5d626b"))
        skull(r, w // 2 - 4, h - 16, BONE)
        light(r, 5, 4, RED_LIGHT)
    elif what == "belt":
        for j in range(0, h, 3):
            for i in range(w):
                px(x0 + i, y0 + j, hx("#c49a3a"))
                px(x0 + i, y0 + j + 1, hx("#7a5a1c"))
    elif what == "muzzles":
        cx, cy = w / 2 - 0.5, h / 2 - 0.5
        for j in range(h):
            for i in range(w):
                if (i - cx) ** 2 + (j - cy) ** 2 < 9:
                    px(x0 + i, y0 + j, hx("#070707"))
    elif what == "bore":
        rect(r, 1, 1, w - 2, h - 2, hx("#060606"))
    elif what == "fist_shoulder":
        frame(r, 2, 2, w - 4, h - 4, GOLD, 1)
        skull(r, w // 2 - 4, 6, BONE)
        sprite(r, w // 2 - 6, 9, LAUREL, {"#": GOLD[1]})
        seal(r, 4, h - 16, 5, 12)
    elif what == "forearm":
        for j in range(h):
            px(x0 + w // 3, y0 + j, MATS["blue"][2])
            px(x0 + w // 3 + 1, y0 + j, MATS["blue"][1] * 0.9)
    elif what == "knuckles":
        for i in range(3, w - 3, 6):
            rect(r, i, 3, 4, h - 6, hx("#4c5058"))
    elif what == "claw_tip":
        frame(r, 0, 0, w, h, MATS["steel"], 1)
    elif what == "hull":
        pass


# =============================================================== сборка

packer = Packer(TEX)
pivots = {p[0]: p[2] for p in PARTS}
json_parts = []
extra = []


def to_model(p):
    """(R,U,F) → координаты модели Minecraft (x влево, y вниз, z назад)."""
    return (-p[0], 24 - p[1], -p[2])


def emit_cube(c):
    lo, hi = c["lo"], c["hi"]
    w, h, d = (hi[i] - lo[i] for i in range(3))
    assert w > 0 and h > 0 and d > 0, c
    u, v = packer.place(2 * (w + d), d + h)
    rects = faces(u, v, w, h, d)
    for face, r in rects.items():
        base_paint(r, c["mat"], face, r[2], r[3])
    for face, what in c["deco"].items():
        decorate(rects[face], what, c["mat"])
    if c["mat"] in ("lens", "lens_blue"):
        col = RED_LIGHT if c["mat"] == "lens" else hx("#8cc8ff")
        for r in rects.values():
            for j in range(r[3]):
                for i in range(r[2]):
                    lit(r[0] + i, r[1] + j, col * (0.8 + 0.2 * rng.random()))
    # минимальный угол куба в модели: x и z инвертированы, y вниз
    mlo = to_model((hi[0], hi[1], hi[2]))
    return (u, v), mlo, (w, h, d)


for name, parent, pivot, rot, cubes in PARTS:
    ppiv = to_model(pivots[parent]) if parent != "root" else (0, 0, 0)
    mpiv = to_model(pivot)
    plain = []
    sub = 0
    for c in cubes:
        uv, mlo, size = emit_cube(c)
        if c["rot"] is None:
            plain.append({"uv": uv, "from": [mlo[i] - mpiv[i] for i in range(3)], "size": size})
        else:
            # повёрнутый куб — отдельная дочерняя часть с осью в центре куба
            mc = to_model(c["center"])
            sub += 1
            extra.append({
                "name": "%s_r%d" % (name, sub), "parent": name,
                "offset": [mc[i] - mpiv[i] for i in range(3)],
                "rotation": [math.radians(a) for a in c["rot"]],
                "cubes": [{"uv": uv, "from": [mlo[i] - mc[i] for i in range(3)], "size": size}],
            })
    json_parts.append({
        "name": name, "parent": parent,
        "offset": [mpiv[i] - ppiv[i] for i in range(3)],
        "rotation": list(rot),
        "cubes": plain,
    })
    json_parts.extend(extra)
    extra = []

used = packer.y + packer.row
model = {"texture": [TEX, TEX], "parts": json_parts}

res = os.path.join(ROOT, "src/main/resources/assets/warpbound")
paths = {
    "model": os.path.join(res, "models/entity/dreadnought.json"),
    "tex": os.path.join(res, "textures/entity/dreadnought.png"),
    "glow": os.path.join(res, "textures/entity/dreadnought_glow.png"),
}
for p in paths.values():
    os.makedirs(os.path.dirname(p), exist_ok=True)
with open(paths["model"], "w", encoding="utf-8") as fh:
    json.dump(model, fh, ensure_ascii=False, separators=(",", ":"))
Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8), "RGBA").save(paths["tex"])
Image.fromarray(glow, "RGBA").save(paths["glow"])

if "--dev" in sys.argv:
    build = os.path.join(ROOT, "build/resources/main/assets/warpbound")
    for key, p in paths.items():
        dst = os.path.join(build, os.path.relpath(p, res))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(p, dst)

ncubes = sum(len(p["cubes"]) for p in json_parts)
print("частей:", len(json_parts), "кубов:", ncubes, "развёртка занята до y =", used, "из", TEX)
