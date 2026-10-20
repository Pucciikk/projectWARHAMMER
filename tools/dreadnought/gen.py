#!/usr/bin/env python3
"""
Генератор модели и текстуры дредноута.

Описание модели ниже (кубы в абсолютных координатах модели, пиксели = 1/16 блока,
земля на y=24, y растёт вниз, -z — вперёд, -x — правая сторона машины).
Скрипт сам раскладывает развёртку, рисует текстуру и пишет Java-класс с мешем:

    python3 tools/dreadnought/gen.py

Результат:
    src/client/java/dev/warpbound/client/entity/DreadnoughtMesh.java
    src/main/resources/assets/warpbound/textures/entity/dreadnought.png
    src/main/resources/assets/warpbound/textures/entity/dreadnought_glow.png
"""
import os
import random

import numpy as np
from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEX = 256
rng = random.Random(40000)

# ---------------------------------------------------------------- модель

# part: (имя, родитель, точка вращения (абс.), [кубы])
# куб: (from, to, материал, {грань: украшение})
PARTS = []


def part(name, parent, pivot, cubes):
    PARTS.append((name, parent, pivot, cubes))


def shift_y(cubes, dy):
    return [((a[0], a[1] + dy, a[2]), (b[0], b[1] + dy, b[2]), m, d) for a, b, m, d in cubes]


def mirror_x(cubes):
    out = []
    for frm, to, mat, deco in cubes:
        d = dict(deco)
        # при отражении правая и левая грани меняются местами
        if "right" in d or "left" in d:
            d["right"], d["left"] = deco.get("left"), deco.get("right")
            d = {k: v for k, v in d.items() if v is not None}
        out.append(((-to[0], frm[1], frm[2]), (-frm[0], to[1], to[2]), mat, d))
    return out


part("body", None, (0, -6, 0), [
    ((-9, -9, -6), (9, -1, 6), "metal", {}),
    ((-10, -10, -7), (10, -7, 7), "blue", {}),                     # пояс
    ((-5, -7, -10), (-2, 3, -9), "seal", {"front": "seal"}),        # печать чистоты
    ((-5, -8, -9), (5, 1, -7), "blue_trim", {"front": "panel"}),   # передний щиток между ног
])

LEG = [
    ((-14, -8, -4), (-6, 0, 4), "metal", {}),                      # тазобедренный шарнир
    ((-15, -2, -5), (-5, 10, 5), "blue", {"front": "panel"}),      # бедро
]
SHIN = [
    ((-14, 8, -5), (-6, 21, 3), "blue", {"front": "panel"}),       # голень
    ((-15, 5, -7), (-5, 13, -4), "blue_trim", {}),                  # наколенник
    ((-13, 13, 3), (-7, 19, 5), "metal", {}),                       # поршень сзади
]
FOOT = [
    ((-16, 20, -10), (-4, 24, 5), "dark", {}),
    ((-15, 21, -13), (-5, 24, -10), "metal", {}),                   # носок
]
part("leg_r", "body", (-10, -4, 0), LEG)
part("shin_r", "leg_r", (-10, 9, -1), SHIN)
part("foot_r", "shin_r", (-10, 21, -1), FOOT)
part("leg_l", "body", (10, -4, 0), mirror_x(LEG))
part("shin_l", "leg_l", (10, 9, -1), mirror_x(SHIN))
part("foot_l", "shin_l", (10, 21, -1), mirror_x(FOOT))

part("torso", "body", (0, -9, 0), [
    ((-13, -35, -10), (13, -9, 10), "blue", {"front": "hull", "back": "hull", "right": "hull", "left": "hull"}),
    ((-8, -25, -13), (8, -11, -10), "blue_trim", {"front": "emblem"}),   # саркофаг
    ((-10, -33, -12), (10, -30, -10), "dark", {"front": "slit"}),        # смотровая щель
    ((-12, -37, -9), (12, -35, 9), "blue_trim", {}),                      # крыша
    ((-10, -44, 6), (-6, -30, 10), "metal", {"top": "pipe"}),             # трубы
    ((6, -44, 6), (10, -30, 10), "metal", {"top": "pipe"}),
    ((-11, -46, 5), (-5, -44, 11), "dark", {"top": "pipe"}),              # колпаки труб
    ((5, -46, 5), (11, -44, 11), "dark", {"top": "pipe"}),
    ((-8, -31, 10), (8, -15, 15), "metal", {"back": "vents"}),            # реактор
    ((9, -24, -11), (12, -14, -10), "seal", {"front": "seal"}),           # печать на корпусе
])
part("head", "torso", (0, -35, -4), [
    ((-4, -40, -9), (4, -35, -1), "blue_trim", {}),
    ((-3, -38, -10), (3, -36, -9), "lens", {}),
])
# Руки опущены на 3 px относительно крыши, чтобы наплечники не торчали над корпусом
ARM_DROP = 3
part("arm_r", "torso", (-17, -30 + ARM_DROP, 0), shift_y([
    ((-26, -37, -8), (-14, -26, 8), "blue_trim", {"right": "squad", "top": "rim"}),
    ((-23, -27, -5), (-15, -19, 5), "metal", {}),
], ARM_DROP))
part("gun", "arm_r", (-19, -19 + ARM_DROP, 0), shift_y([
    ((-24, -23, -7), (-14, -13, 7), "blue", {"right": "panel", "left": "panel"}),
    ((-27, -22, -1), (-24, -14, 6), "metal", {"right": "panel"}),             # короб с лентой
    ((-22, -13, -4), (-16, -11, 3), "dark", {}),                               # подача ленты
    ((-22, -21, -25), (-16, -15, -7), "barrels", {"front": "muzzles"}),
    ((-23, -22, -28), (-15, -14, -25), "dark", {"front": "muzzles"}),
    ((-21, -24, -18), (-17, -23, -8), "metal", {}),                            # ребро над стволами
], ARM_DROP))
part("arm_l", "torso", (17, -30 + ARM_DROP, 0), shift_y([
    ((14, -37, -8), (26, -26, 8), "blue_trim", {"left": "emblem", "top": "rim"}),
    ((15, -27, -5), (23, -19, 5), "metal", {}),
], ARM_DROP))
part("fist", "arm_l", (19, -19 + ARM_DROP, 0), shift_y([
    ((14, -21, -6), (24, -9, 6), "blue", {"front": "panel", "left": "panel"}),
    ((13, -9, -7), (25, 1, 6), "dark", {}),
    ((13, 1, -7), (16, 6, -3), "metal", {}),
    ((17, 1, -7), (20, 6, -3), "metal", {}),
    ((21, 1, -7), (24, 6, -3), "metal", {}),
    ((12, -6, -9), (15, -1, -6), "metal", {}),                            # большой палец
    ((24, -8, -4), (26, -2, 4), "lens_dim", {}),                          # катушки силового поля
], ARM_DROP))

# ---------------------------------------------------------------- развёртка

class Packer:
    """Полки: куб занимает прямоугольник 2(w+d) x (d+h)."""

    def __init__(self, size):
        self.size = size
        self.x = 0
        self.y = 0
        self.row_h = 0

    def place(self, w, h):
        if self.x + w > self.size:
            self.x = 0
            self.y += self.row_h
            self.row_h = 0
        if self.y + h > self.size:
            raise SystemExit("развёртка не влезла в %d px" % self.size)
        at = (self.x, self.y)
        self.x += w
        self.row_h = max(self.row_h, h)
        return at


def faces(u, v, w, h, d):
    """Прямоугольники граней (x, y, ширина, высота) в стандартной развёртке Minecraft."""
    return {
        "top": (u + d, v, w, d),
        "bottom": (u + d + w, v, w, d),
        "left": (u, v + d, d, h),
        "front": (u + d, v + d, w, h),
        "right": (u + d + w, v + d, d, h),
        "back": (u + d + w + d, v + d, w, h),
    }


# ---------------------------------------------------------------- палитра

def hexc(s):
    return np.array([int(s[i:i + 2], 16) for i in (1, 3, 5)], dtype=float)


MATS = {
    #           основа      свет       тень
    "blue": (hexc("#2b4fa6"), hexc("#5b83d6"), hexc("#16295e")),
    "blue_trim": (hexc("#2b4fa6"), hexc("#5b83d6"), hexc("#16295e")),
    "gold": (hexc("#c49a2a"), hexc("#f2d36b"), hexc("#7c5b12")),
    "metal": (hexc("#5c6168"), hexc("#9aa1aa"), hexc("#2f3237")),
    "barrels": (hexc("#4b4f55"), hexc("#868c94"), hexc("#26282c")),
    "dark": (hexc("#2a2c30"), hexc("#4c4f55"), hexc("#151618")),
    "seal": (hexc("#d8c79c"), hexc("#efe3c2"), hexc("#a4926a")),
    "lens": (hexc("#c81e14"), hexc("#ff6a4a"), hexc("#6e0a06")),
    "lens_dim": (hexc("#3a6fd0"), hexc("#9fd0ff"), hexc("#1a3170")),
}
GOLD = MATS["gold"]
WHITE = hexc("#e9e6dc")
WAX = hexc("#8e1610")
GLOW_RED = (255, 60, 30, 255)
GLOW_ORANGE = (255, 140, 40, 255)
GLOW_BLUE = (120, 190, 255, 255)

EMBLEM = [
    ".....##.....",
    ".....##.....",
    "....####....",
    "#...####...#",
    "##..####..##",
    "###.####.###",
    ".##########.",
    "..########..",
    "....####....",
    "....####....",
    ".....##.....",
    ".....##.....",
]
SQUAD = [
    "#.......#",
    "##.....##",
    ".##...##.",
    "..##.##..",
    "...###...",
    "....#....",
]

tex = np.zeros((TEX, TEX, 4), dtype=float)
glow = np.zeros((TEX, TEX, 4), dtype=np.uint8)


def px(x, y, c, a=255):
    if 0 <= x < TEX and 0 <= y < TEX:
        tex[y, x, :3] = np.clip(c, 0, 255)
        tex[y, x, 3] = a


def fill_face(rect, mat, face):
    x0, y0, w, h = rect
    base, light, shadow = MATS[mat]
    # верх светлее, низ темнее — металл ловит свет сверху
    tint = {"top": 1.12, "bottom": 0.7}.get(face, 1.0)
    for y in range(h):
        for x in range(w):
            n = rng.uniform(-9, 9)
            c = base * tint + n
            # мягкий вертикальный градиент: потёки и грязь внизу
            c = c * (1.04 - 0.12 * (y / max(1, h - 1)))
            px(x0 + x, y0 + y, c)
    # фаски: светлая сверху-слева, тёмная снизу-справа
    if w >= 3 and h >= 3:
        for x in range(w):
            px(x0 + x, y0, light * tint)
            px(x0 + x, y0 + h - 1, shadow)
        for y in range(h):
            px(x0, y0 + y, (light * tint + base) / 2)
            px(x0 + w - 1, y0 + y, shadow)
    # сколы краски: серебро под синим
    if mat in ("blue", "blue_trim") and w * h > 12:
        for _ in range(max(1, w * h // 70)):
            sx, sy = x0 + rng.randrange(w), y0 + rng.randrange(h)
            px(sx, sy, MATS["metal"][1])
    if mat == "blue_trim" and w >= 4 and h >= 4:
        border(rect, GOLD, 1)


def border(rect, mat, width):
    x0, y0, w, h = rect
    base, light, shadow = mat
    for i in range(width):
        for x in range(i, w - i):
            px(x0 + x, y0 + i, light)
            px(x0 + x, y0 + h - 1 - i, shadow)
        for y in range(i, h - i):
            px(x0 + i, y0 + y, base)
            px(x0 + w - 1 - i, y0 + y, base * 0.85)


def stamp(rect, pattern, color, glow_color=None):
    x0, y0, w, h = rect
    ph, pw = len(pattern), len(pattern[0])
    ox = x0 + (w - pw) // 2
    oy = y0 + (h - ph) // 2
    for j, row in enumerate(pattern):
        for i, ch in enumerate(row):
            if ch == "#":
                px(ox + i, oy + j, color + rng.uniform(-6, 6))
                if glow_color:
                    glow[oy + j, ox + i] = glow_color


def rivets(rect, step):
    x0, y0, w, h = rect
    for x in range(2, w - 2, step):
        for y in (2, h - 3):
            if 0 <= y < h:
                px(x0 + x, y0 + y, MATS["metal"][1])


def panel_lines(rect):
    x0, y0, w, h = rect
    dark = MATS["blue"][2]
    for y in range(h // 3, h, max(4, h // 3)):
        for x in range(2, w - 2):
            px(x0 + x, y0 + y, dark)
            px(x0 + x, y0 + y + 1, MATS["blue"][1] * 0.8)


def decorate(rect, deco):
    x0, y0, w, h = rect
    if deco == "emblem":
        border(rect, GOLD, 1)
        stamp(rect, EMBLEM, WHITE)
    elif deco == "squad":
        border(rect, GOLD, 1)
        stamp(rect, SQUAD, WHITE)
    elif deco == "rim":
        border(rect, GOLD, 1)
    elif deco == "panel":
        panel_lines(rect)
        rivets(rect, 3)
    elif deco == "hull":
        panel_lines(rect)
        rivets(rect, 4)
    elif deco == "slit":
        for x in range(1, w - 1):
            px(x0 + x, y0 + h // 2, (20, 20, 22))
            glow[y0 + h // 2, x0 + x] = (180, 30, 20, 160)
    elif deco == "pipe":
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                px(x0 + x, y0 + y, (18, 18, 20))
    elif deco == "vents":
        for y in range(2, h - 2, 3):
            for x in range(2, w - 2):
                px(x0 + x, y0 + y, (60, 25, 10))
                glow[y0 + y, x0 + x] = GLOW_ORANGE
    elif deco == "muzzles":
        # четыре ствола: тёмные дыры
        for cx, cy in ((w // 3, h // 3), (2 * w // 3, h // 3), (w // 3, 2 * h // 3), (2 * w // 3, 2 * h // 3)):
            px(x0 + cx, y0 + cy, (10, 10, 12))
            px(x0 + cx - 1, y0 + cy, (24, 24, 26))
    elif deco == "seal":
        # пергамент с «текстом» и красная восковая печать сверху
        for y in range(3, h, 2):
            for x in range(0, w):
                if rng.random() < 0.6:
                    px(x0 + x, y0 + y, (90, 70, 50))
        for y in range(0, 2):
            for x in range(w):
                px(x0 + x, y0 + y, WAX + rng.uniform(-10, 10))


def paint_material_extras(rect_map, mat):
    if mat == "lens":
        for name, (x0, y0, w, h) in rect_map.items():
            for y in range(h):
                for x in range(w):
                    glow[y0 + y, x0 + x] = GLOW_RED
    if mat == "lens_dim":
        for name, (x0, y0, w, h) in rect_map.items():
            for y in range(h):
                for x in range(w):
                    if (x + y) % 2 == 0:
                        glow[y0 + y, x0 + x] = GLOW_BLUE


# ---------------------------------------------------------------- сборка

packer = Packer(TEX)
pivots = {name: pivot for name, _, pivot, _ in PARTS}
java_parts = []
for name, parent, pivot, cubes in PARTS:
    boxes = []
    for frm, to, mat, deco in cubes:
        w, h, d = (to[i] - frm[i] for i in range(3))
        assert w > 0 and h > 0 and d > 0, (name, frm, to)
        u, v = packer.place(2 * (w + d), d + h)
        rects = faces(u, v, w, h, d)
        for face, rect in rects.items():
            fill_face(rect, mat, face)
        for face, what in deco.items():
            decorate(rects[face], what)
        paint_material_extras(rects, mat)
        rel = tuple(frm[i] - pivot[i] for i in range(3))
        boxes.append((u, v, rel, (w, h, d)))
    ppos = pivots[parent] if parent else (0, 0, 0)
    offset = tuple(pivot[i] - ppos[i] for i in range(3))
    java_parts.append((name, parent, offset, boxes))


def f(x):
    return ("%g" % x) + "F"


lines = []
for name, parent, offset, boxes in java_parts:
    parent_var = (parent if parent else "root")
    cl = "CubeListBuilder.create()"
    for u, v, rel, size in boxes:
        cl += "\n                        .texOffs(%d, %d).addBox(%s, %s, %s, %s, %s, %s)" % (
            u, v, f(rel[0]), f(rel[1]), f(rel[2]), f(size[0]), f(size[1]), f(size[2]))
    lines.append(
        "        PartDefinition %s = %s.addOrReplaceChild(\"%s\", %s,\n                PartPose.offset(%s, %s, %s));"
        % (name, parent_var, name, cl, f(offset[0]), f(offset[1]), f(offset[2])))

java = """package dev.warpbound.client.entity;

import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;

/**
 * СГЕНЕРИРОВАНО tools/dreadnought/gen.py — правьте модель там, а не здесь.
 */
public final class DreadnoughtMesh {
    private DreadnoughtMesh() {
    }

    @SuppressWarnings("unused")
    public static LayerDefinition create() {
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition root = mesh.getRoot();
%s
        return LayerDefinition.create(mesh, %d, %d);
    }
}
""" % ("\n".join(lines), TEX, TEX)

out_java = os.path.join(ROOT, "src/client/java/dev/warpbound/client/entity/DreadnoughtMesh.java")
out_tex = os.path.join(ROOT, "src/main/resources/assets/warpbound/textures/entity")
os.makedirs(out_tex, exist_ok=True)
with open(out_java, "w", encoding="utf-8") as fh:
    fh.write(java)
Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8), "RGBA").save(os.path.join(out_tex, "dreadnought.png"))
Image.fromarray(glow, "RGBA").save(os.path.join(out_tex, "dreadnought_glow.png"))
print("частей:", len(PARTS), "кубов:", sum(len(p[3]) for p in PARTS), "развёртка до y =", packer.y + packer.row_h)
