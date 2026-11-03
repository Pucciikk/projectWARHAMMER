#!/usr/bin/env python3
"""
Окно машин цепочки в стиле Адептус Механикус: textures/gui/machine.png (фон 232×212) и textures/gui/machine_parts.png (детали).

    python3 tools/textures/gen_machine_gui.py [--preview путь.png]

Фон общий на все машины; слоты, манометры и баки экран расставляет сам по описанию машины, поэтому они лежат отдельными деталями.
Координаты деталей совпадают с константами в client/industry/ChainMachineScreen.java — менять вместе.
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(ROOT, "src/main/resources/assets/warpbound/textures/gui")
W, H = 232, 212
rng = random.Random(1945)

STEEL_D, STEEL, STEEL_L = (30, 32, 37), (47, 50, 57), (70, 74, 83)
BRASS_D, BRASS, BRASS_L, BRASS_H = (84, 58, 20), (150, 110, 44), (200, 158, 72), (240, 210, 130)
INK = (12, 12, 15)
CRT_D, CRT = (6, 20, 12), (10, 34, 20)


def bevel(d, x0, y0, x1, y1, fill, light, dark):
    """Прямоугольник с фаской: свет сверху слева. Границы включительно."""
    d.rectangle((x0, y0, x1, y1), fill=fill)
    d.line((x0, y0, x1 - 1, y0), fill=light)
    d.line((x0, y0, x0, y1 - 1), fill=light)
    d.line((x1, y0 + 1, x1, y1), fill=dark)
    d.line((x0 + 1, y1, x1, y1), fill=dark)


def rivet(d, x, y):
    d.point((x, y), fill=BRASS_H)
    d.point((x + 1, y), fill=BRASS_L)
    d.point((x, y + 1), fill=BRASS_L)
    d.point((x + 1, y + 1), fill=BRASS_D)


def noise(img, box, amp):
    px = img.load()
    for y in range(box[1], box[3]):
        for x in range(box[0], box[2]):
            r, g, b, a = px[x, y]
            n = rng.randint(-amp, amp)
            px[x, y] = (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n)), a)


def gear_shape(d, cx, cy, r_out, r_in, r_hole, teeth, angle, tooth, body, hole=INK):
    pts = []
    n = teeth * 4
    for i in range(n):
        a = angle + 2 * math.pi * i / n
        r = r_out if i % 4 in (1, 2) else r_in
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=tooth)
    d.ellipse((cx - r_in + 1.2, cy - r_in + 1.2, cx + r_in - 1.2, cy + r_in - 1.2), fill=body)
    d.ellipse((cx - r_hole, cy - r_hole, cx + r_hole, cy + r_hole), fill=hole)


SKULL = [
    "..#####..",
    ".#######.",
    "#########",
    "#..###..#",
    "#..###..#",
    "####.####",
    ".#######.",
    "..#.#.#..",
]


def skull(d, x, y, c=BRASS_D):
    for j, row in enumerate(SKULL):
        for i, ch in enumerate(row):
            if ch == "#":
                d.point((x + i, y + j), fill=c)


# ---------------------------------------------------------------- фон
bg = Image.new("RGBA", (W, H), (*STEEL, 255))
d = ImageDraw.Draw(bg)
noise(bg, (0, 0, W, H), 3)
# царапины на корпусе
for _ in range(36):
    x, y = rng.randrange(6, W - 10), rng.randrange(6, H - 6)
    dx, dy = rng.randint(2, 9), rng.randint(-2, 2)
    d.line((x, y, x + dx, y + dy), fill=(58, 61, 69))
# клёпаные плиты по низу: панели инвентаря
for y in (120, 181):
    d.line((6, y, W - 7, y), fill=STEEL_D)
    d.line((6, y + 1, W - 7, y + 1), fill=STEEL_L)
# латунная рама
for i, c in enumerate((INK, BRASS_D, BRASS, BRASS_L, BRASS, BRASS_D)):
    d.rectangle((i, i, W - 1 - i, H - 1 - i), outline=c)
# прорезь под рамкой
d.rectangle((6, 6, W - 7, H - 7), outline=STEEL_D)
# углы: тяжёлые косынки с заклёпками
for cx, cy, sx, sy in ((6, 6, 1, 1), (W - 7, 6, -1, 1), (6, H - 7, 1, -1), (W - 7, H - 7, -1, -1)):
    d.polygon([(cx, cy), (cx + sx * 15, cy), (cx, cy + sy * 15)], fill=BRASS)
    d.line((cx + sx * 15, cy, cx, cy + sy * 15), fill=BRASS_D)
    rivet(d, cx + sx * 3 - (0 if sx > 0 else 1), cy + sy * 3 - (0 if sy > 0 else 1))
# табличка с именем: латунь на всю ширину рабочей зоны
bevel(d, 22, 7, W - 23, 21, BRASS, BRASS_H, BRASS_D)
d.rectangle((24, 9, W - 25, 19), outline=BRASS_D)
for x in (26, W - 28):
    rivet(d, x, 13)
# черепа по краям таблички
skull(d, 31, 10)
skull(d, W - 41, 10)
# глубокая рабочая ниша
bevel(d, 8, 24, W - 9, 91, (24, 26, 30), STEEL_D, STEEL_L)
noise(bg, (9, 25, W - 9, 91), 2)
# ребристый канал по середине ниши: шина от входа к выходу
for x in range(9, W - 9, 6):
    d.line((x, 88, x + 2, 88), fill=(18, 19, 23))
for x, y in ((10, 26), (W - 12, 26), (10, 87), (W - 12, 87)):
    rivet(d, x, y)
# экран когитатора
bevel(d, 8, 94, W - 9, 116, BRASS_D, BRASS, BRASS_L)
d.rectangle((10, 96, W - 11, 114), fill=CRT, outline=INK)
for y in range(97, 114, 2):
    d.line((11, y, W - 12, y), fill=CRT_D)
for x in range(11, W - 11):
    for y in (97, 113):
        p = bg.getpixel((x, y))
        bg.putpixel((x, y), tuple(int(v * 0.6) for v in p[:3]) + (255,))
# полоса опасности над инвентарём
for x in range(9, W - 9):
    for y in (117, 118):
        c = (196, 150, 40) if ((x + y) // 4) % 2 == 0 else (22, 22, 26)
        bg.putpixel((x, y), (*c, 255))


# слоты инвентаря
def slot(dr, x, y, size=18):
    bevel(dr, x, y, x + size - 1, y + size - 1, (18, 19, 23), INK, STEEL_L)
    dr.point((x + size - 1, y), fill=STEEL)
    dr.point((x, y + size - 1), fill=STEEL)


INV_X, INV_Y, HOT_Y = 35, 124, 184
for row in range(3):
    for col in range(9):
        slot(d, INV_X + col * 18 - 1, INV_Y + row * 18 - 1)
for col in range(9):
    slot(d, INV_X + col * 18 - 1, HOT_Y - 1)
# декор слева и справа от инвентаря: вентиляция и шестерня Механикус
for y in range(128, 176, 4):
    d.line((14, y, 27, y), fill=INK)
    d.line((14, y + 1, 27, y + 1), fill=STEEL_L)
    d.line((W - 28, y, W - 15, y), fill=INK)
    d.line((W - 28, y + 1, W - 15, y + 1), fill=STEEL_L)
gear_shape(d, 21, 193, 7, 5.2, 1.8, 8, 0.2, BRASS_L, BRASS)
gear_shape(d, W - 22, 193, 7, 5.2, 1.8, 8, 0.2, BRASS_L, BRASS)
bg.save(os.path.join(OUT, "machine.png"))

# ---------------------------------------------------------------- детали
P = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
p = ImageDraw.Draw(P)
# слот входа 18×18 в (0,0); слот выхода 22×22 в (20,0): латунная рамка, готовая продукция заметнее
slot(p, 0, 0)
bevel(p, 20, 0, 41, 21, BRASS, BRASS_H, BRASS_D)
slot(p, 22, 2)
# манометр бака 14×64 в (0,24): рамка и тёмная колба
bevel(p, 0, 24, 13, 87, BRASS, BRASS_H, BRASS_D)
p.rectangle((1, 25, 12, 86), fill=INK)
p.rectangle((2, 26, 11, 85), fill=(10, 12, 16))
# стекло поверх жидкости 14×64 в (16,24): прозрачное, блик и деления
for yy in range(0, 60, 10):
    w = 5 if yy % 20 == 0 else 3
    p.line((18 + 10 - w, 26 + yy, 18 + 9, 26 + yy), fill=(235, 225, 190, 170))
p.line((19, 27, 19, 83), fill=(255, 255, 255, 64))
p.line((20, 27, 20, 83), fill=(255, 255, 255, 26))
p.rectangle((18, 26, 27, 27), fill=(0, 0, 0, 70))
# шкала энергии 12×64 в (32,24)
bevel(p, 32, 24, 43, 87, BRASS, BRASS_H, BRASS_D)
p.rectangle((33, 25, 42, 86), fill=INK)
p.rectangle((34, 26, 41, 85), fill=(26, 8, 8))
for yy in range(26, 86, 4):
    p.line((34, yy, 41, yy), fill=(14, 4, 4))
# заполнение энергии 8×60 в (46,26): секции от красного к жёлтому
for yy in range(60):
    k = 1 - yy / 59
    c = (int(180 + 70 * k), int(36 + 170 * k * k), int(20 + 60 * k * k * k))
    if yy % 4 == 0:
        c = tuple(v // 3 for v in c)
    p.line((46, 26 + yy, 53, 26 + yy), fill=(*c, 255))
# жидкость 10×60 в (60,26): серая, тянется по вертикали без шва; цвет задаёт экран
fluid_rng = random.Random(7)
for yy in range(60):
    wave = math.sin(2 * math.pi * yy / 60) * 18 + math.sin(2 * math.pi * 3 * yy / 60) * 7
    for xx in range(10):
        edge = -40 if xx == 0 or xx == 9 else (14 if xx == 2 else 0)
        v = int(205 + wave + edge + fluid_rng.randint(-9, 9))
        P.putpixel((60 + xx, 26 + yy), (min(255, v), min(255, v), min(255, v), 255))
# пузыри в жидкости
for _ in range(9):
    bx, by = fluid_rng.randrange(62, 67), fluid_rng.randrange(28, 84)
    P.putpixel((bx, by), (255, 255, 255, 255))
    P.putpixel((bx, by + 1), (235, 235, 235, 255))
# стрелка 36×14: пустая в (0,90), полная в (0,106)
arrow = [(0, 4), (24, 4), (24, 0), (35, 7), (24, 13), (24, 9), (0, 9)]
for oy, fill, edge in ((90, (20, 21, 25), (70, 74, 83)), (106, (232, 150, 40), (255, 222, 130))):
    pts = [(x, y + oy) for x, y in arrow]
    p.polygon(pts, fill=(*fill, 255), outline=(*edge, 255))
# лампы состояния 8×8 в (40,90): зелёная, жёлтая, красная, тёмная
for i, (c, h) in enumerate((((60, 220, 90), (200, 255, 210)), ((235, 170, 40), (255, 235, 170)), ((225, 50, 36), (255, 170, 150)), ((48, 46, 44), (84, 80, 76)))):
    x = 40 + i * 9
    p.ellipse((x, 90, x + 7, 97), fill=(*c, 255), outline=(*INK, 255))
    p.point((x + 2, 92), fill=(*h, 255))
    p.point((x + 3, 92), fill=(*h, 255))
# кнопки 10×14 в (80,90): назад, вперёд; вторая строка в (80,106) — наведено
for row, (f, l, dk, ar) in enumerate(((BRASS, BRASS_H, BRASS_D, INK), (BRASS_L, (255, 240, 190), BRASS, INK))):
    for i in range(2):
        x, y = 80 + i * 12, 90 + row * 16
        bevel(p, x, y, x + 9, y + 13, f, l, dk)
        tri = [(x + 6, y + 4), (x + 3, y + 7), (x + 6, y + 10)] if i == 0 else [(x + 3, y + 4), (x + 6, y + 7), (x + 3, y + 10)]
        p.polygon(tri, fill=ar)
# огонь топлива 14×14: пустой в (108,90), полный в (108,106)
flame = [(7, 0), (10, 4), (12, 8), (11, 12), (7, 13), (3, 12), (2, 8), (4, 5), (5, 7)]
for oy, c1, c2 in ((90, (40, 34, 30), (58, 50, 44)), (106, (232, 96, 30), (255, 210, 90))):
    p.polygon([(108 + x, oy + y) for x, y in flame], fill=(*c1, 255))
    p.polygon([(108 + 7, oy + 5), (108 + 9, oy + 9), (108 + 7, oy + 12), (108 + 5, oy + 9)], fill=(*c2, 255))
# шестерни 22×22, 8 кадров поворота на один зуб, в (0,124) и в (0,148) потускневшие
for row, (t, b) in enumerate((((BRASS_L, BRASS)), ((BRASS, BRASS_D)))) if False else enumerate(((BRASS_L, BRASS), (BRASS, BRASS_D))):
    for i in range(8):
        cx, cy = 11 + i * 24, 135 + row * 24
        gear_shape(p, cx, cy, 10.4, 7.6, 2.4, 10, i / 8 * (2 * math.pi / 10), t, b, hole=INK)
        p.point((cx, cy), fill=BRASS_H)
P.save(os.path.join(OUT, "machine_parts.png"))
print("окно машины готово")

if "--preview" in sys.argv:
    prev = bg.copy()
    for pos, box in (((10, 26), (32, 24, 44, 88)), ((26, 26), (0, 24, 14, 88)), ((80, 40), (0, 0, 18, 18)), ((102, 50), (0, 106, 36, 120)), ((146, 38), (20, 0, 42, 22))):
        c = P.crop(box)
        prev.paste(c, pos, c)
    prev.resize((W * 3, H * 3), Image.NEAREST).save(sys.argv[sys.argv.index("--preview") + 1])
