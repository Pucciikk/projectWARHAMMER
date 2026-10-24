#!/usr/bin/env python3
"""
Текстуры первой индустрии Сезона 1 и оборудования корабля: горн, пресс, пласталь, латунь, шестерни,
пластины, шихта; навигационный стол, ауспик, узел Поля Геллера, ядро реактора, телепортариум, телепорт-маяк.
Временные, до текстур автора.

    python3 tools/textures/gen_industry.py
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
from gen_items import Canvas, save, shade  # noqa: E402

rng = random.Random(1202)

DEEP = (54, 54, 60)
IRON = (150, 152, 156)
PLASTEEL = (126, 140, 150)
BRASS = (176, 138, 60)
FIRE = (255, 140, 40)
EMBER = (255, 210, 90)


def forge_side():
    c = Canvas()
    c.noisy(0, 0, 15, 15, DEEP, 7)
    for y in (0, 5, 10, 15):
        for x in range(16):
            c.px(x, y, shade(DEEP, 0.7))
    for y in range(16):
        c.px(0 if y % 10 < 5 else 8, y, shade(DEEP, 0.7))
    c.rect(0, 13, 15, 15, shade(IRON, 0.6))
    return c.img()


def forge_front(lit):
    c = Canvas()
    c.noisy(0, 0, 15, 15, DEEP, 7)
    c.rect(0, 13, 15, 15, shade(IRON, 0.6))
    # Зев горна с решёткой
    c.rect(3, 5, 12, 11, (16, 12, 10))
    for x in range(3, 13):
        c.px(x, 4, BRASS)
    for x in (3, 6, 9, 12):
        for y in range(5, 12):
            c.px(x, y, shade(IRON, 0.8))
    if lit:
        for y in range(6, 12):
            for x in (4, 5, 7, 8, 10, 11):
                c.px(x, y, FIRE if rng.random() < 0.6 else EMBER)
    # Латунная печать Механикус над зевом
    c.px(7, 2, BRASS)
    c.px(8, 2, BRASS)
    c.px(7, 1, shade(BRASS, 1.2))
    c.px(8, 1, shade(BRASS, 1.2))
    return c.img()


def forge_top():
    c = Canvas()
    c.noisy(0, 0, 15, 15, DEEP, 6)
    c.rect(5, 5, 10, 10, (20, 16, 14))
    c.rect(6, 6, 9, 9, (40, 30, 26))
    return c.img()


def press():
    c = Canvas()
    c.noisy(0, 0, 15, 15, IRON, 8)
    for x in range(16):
        c.px(x, 0, shade(IRON, 1.25))
        c.px(x, 15, shade(IRON, 0.6))
    for y in range(16):
        c.px(0, y, shade(IRON, 1.15))
        c.px(15, y, shade(IRON, 0.7))
    for x, y in ((2, 2), (13, 2), (2, 13), (13, 13)):
        c.px(x, y, shade(BRASS, 1.1))
    return c.img()


def ingot(color):
    c = Canvas()
    for y in range(6, 11):
        for x in range(2 + (10 - y) // 2, 14 - (y - 6) // 2):
            c.px(x, y, shade(color, 1.15 if y == 6 else 0.75 if y == 10 else 1.0))
    for x in range(4, 12):
        c.px(x, 7, shade(color, 1.35))
    return c.img()


def plate():
    c = Canvas()
    c.rect(2, 3, 13, 12, PLASTEEL)
    for x in range(2, 14):
        c.px(x, 3, shade(PLASTEEL, 1.3))
        c.px(x, 12, shade(PLASTEEL, 0.65))
    for y in range(3, 13):
        c.px(2, y, shade(PLASTEEL, 1.15))
        c.px(13, y, shade(PLASTEEL, 0.7))
    for x, y in ((4, 5), (11, 5), (4, 10), (11, 10)):
        c.px(x, y, shade(PLASTEEL, 0.55))
    return c.img()


def gear():
    c = Canvas()
    for y in range(16):
        for x in range(16):
            d = ((x - 7.5) ** 2 + (y - 7.5) ** 2) ** 0.5
            tooth = (round((x - 7.5) * 2) % 4 == 0) or (round((y - 7.5) * 2) % 4 == 0)
            if d < 4.8 or (d < 6.6 and tooth):
                c.px(x, y, shade(BRASS, 1.0 + (7.5 - y) * 0.03))
            if d < 1.6:
                c.px(x, y, (0, 0, 0), 0)
    return c.img()


def blend():
    c = Canvas()
    for _ in range(70):
        x, y = 3 + rng.randint(0, 9), 5 + rng.randint(0, 7)
        col = rng.choice([IRON, PLASTEEL, BRASS, (40, 40, 40)])
        c.px(x, y, shade(col, 0.8 + rng.random() * 0.4))
    return c.img()


def main():
    save(forge_side(), "block", "salvage_forge_side.png")
    save(forge_front(False), "block", "salvage_forge_front.png")
    save(forge_front(True), "block", "salvage_forge_front_on.png")
    save(forge_top(), "block", "salvage_forge_top.png")
    save(press(), "block", "manual_press.png")
    save(ingot(PLASTEEL), "item", "plasteel_ingot.png")
    save(ingot(BRASS), "item", "brass_ingot.png")
    save(plate(), "item", "plasteel_plate.png")
    save(gear(), "item", "brass_gear.png")
    save(blend(), "item", "plasteel_blend.png")
    fixtures()


# ---------------------------------------------------------------- оборудование корабля
SCREEN = (20, 44, 28)
GLOW = (124, 255, 154)
BLUE = (110, 200, 255)


def fixture_side():
    c = Canvas()
    c.noisy(0, 0, 15, 15, DEEP, 5)
    c.rect(0, 0, 15, 0, BRASS)
    c.rect(0, 15, 15, 15, shade(BRASS, 0.7))
    for x in (3, 12):
        for y in range(2, 14):
            c.px(x, y, shade(DEEP, 0.75))
    return c.img()


def nav_top():
    c = Canvas()
    c.rect(0, 0, 15, 15, SCREEN)
    c.rect(0, 0, 15, 0, BRASS)
    c.rect(0, 15, 15, 15, BRASS)
    c.rect(0, 0, 0, 15, BRASS)
    c.rect(15, 0, 15, 15, BRASS)
    # Звёздная карта: миры и маршрут между ними
    for x, y in ((4, 4), (11, 6), (6, 11), (12, 12)):
        c.px(x, y, GLOW)
    for t in range(8):
        c.px(4 + t, 4 + t // 4, shade(GLOW, 0.5))
    c.px(8, 8, (255, 200, 80))
    return c.img()


def screen_front(color, pattern):
    c = Canvas()
    c.noisy(0, 0, 15, 15, DEEP, 5)
    c.rect(2, 2, 13, 13, BRASS)
    c.rect(3, 3, 12, 12, (14, 18, 20))
    for x, y in pattern:
        c.px(x, y, color)
    return c.img()


def pad_top():
    c = Canvas()
    c.noisy(0, 0, 15, 15, DEEP, 4)
    for y in range(16):
        for x in range(16):
            d = ((x - 7.5) ** 2 + (y - 7.5) ** 2) ** 0.5
            if 5 < d < 6.5:
                c.px(x, y, BLUE)
            elif d < 2:
                c.px(x, y, shade(BLUE, 1.2))
    return c.img()


def homer():
    c = Canvas()
    c.rect(5, 3, 10, 13, DEEP)
    c.rect(6, 4, 9, 7, (14, 18, 20))
    c.px(7, 5, BLUE)
    c.px(8, 5, BLUE)
    c.rect(6, 9, 9, 12, shade(BRASS, 0.9))
    c.px(7, 2, BRASS)
    c.px(7, 1, shade(BLUE, 1.2))
    return c.img()


def fixtures():
    save(fixture_side(), "block", "nav_table_side.png")
    save(nav_top(), "block", "nav_table_top.png")
    sweep = [(7 + int(4 * math.cos(a / 3)), 7 + int(4 * math.sin(a / 3))) for a in range(19)]
    save(screen_front(GLOW, sweep + [(7, 7), (10, 5)]), "block", "auspex_front.png")
    save(screen_front(BLUE, [(x, 7 + int(2 * math.sin(x))) for x in range(3, 13)]), "block", "geller_node_front.png")
    save(screen_front((255, 150, 50), [(x, y) for x in range(5, 11) for y in range(5, 11) if (x + y) % 2]), "block", "reactor_core_front.png")
    save(pad_top(), "block", "teleportarium_pad_top.png")
    save(homer(), "item", "teleport_homer.png")


if __name__ == "__main__":
    main()
