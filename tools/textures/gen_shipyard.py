#!/usr/bin/env python3
"""
Текстуры верфи: балка стапеля, пульт верфи, Омниссианский ключ. Временные, до текстур автора.

    python3 tools/textures/gen_shipyard.py
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
from gen_items import Canvas, save, shade  # noqa: E402

rng = random.Random(1201)

STEEL = (92, 96, 102)
STEEL_DARK = (52, 55, 60)
BRASS = (176, 138, 60)
HAZARD = (214, 168, 38)
SCREEN = (24, 46, 30)
GLOW = (124, 255, 154)


def girder():
    c = Canvas()
    c.noisy(0, 0, 15, 15, STEEL_DARK, 6)
    # Двутавр: полки сверху и снизу, стенка посередине
    c.noisy(0, 0, 15, 2, STEEL, 8)
    c.noisy(0, 13, 15, 15, STEEL, 8)
    c.noisy(6, 3, 9, 12, STEEL, 6)
    for x in range(16):
        c.px(x, 3, shade(STEEL, 0.6))
        c.px(x, 12, shade(STEEL, 1.25))
    # Заклёпки на полках
    for x in (2, 7, 12):
        c.px(x, 1, shade(STEEL, 1.4))
        c.px(x, 14, shade(STEEL, 1.4))
    # Предупредительные полосы по краям стенки
    for y in range(4, 12):
        for x in (6, 9):
            c.px(x, y, HAZARD if (x + y) % 4 < 2 else (30, 28, 24))
    return c.img()


def console_side():
    c = Canvas()
    c.noisy(0, 0, 15, 15, STEEL_DARK, 5)
    c.rect(0, 0, 15, 0, BRASS)
    c.rect(0, 15, 15, 15, shade(BRASS, 0.7))
    for y in (4, 8, 12):
        for x in range(2, 14):
            c.px(x, y, shade(STEEL_DARK, 0.7))
    for x in (2, 13):
        c.px(x, 2, shade(BRASS, 1.2))
    return c.img()


def console_front():
    c = Canvas()
    c.noisy(0, 0, 15, 15, STEEL_DARK, 5)
    c.rect(0, 0, 15, 0, BRASS)
    c.rect(0, 15, 15, 15, shade(BRASS, 0.7))
    # Латунная рамка экрана
    c.rect(2, 2, 13, 2, BRASS)
    c.rect(2, 10, 13, 10, BRASS)
    c.rect(2, 2, 2, 10, BRASS)
    c.rect(13, 2, 13, 10, BRASS)
    c.rect(3, 3, 12, 9, SCREEN)
    # Схема корабля на экране: силуэт фрегата
    for x in range(4, 12):
        c.px(x, 6, GLOW)
    for x in range(5, 10):
        c.px(x, 5, shade(GLOW, 0.7))
    c.px(11, 5, shade(GLOW, 0.6))
    c.px(5, 4, shade(GLOW, 0.8))
    c.px(4, 7, shade(GLOW, 0.5))
    # Рычаги и лампы под экраном
    for x, col in ((4, (220, 60, 40)), (7, GLOW), (10, HAZARD)):
        c.px(x, 12, col)
        c.px(x, 13, shade(STEEL, 1.1))
    return c.img()


def console_top():
    c = Canvas()
    c.noisy(0, 0, 15, 15, STEEL, 6)
    c.rect(0, 0, 15, 0, BRASS)
    c.rect(0, 15, 15, 15, BRASS)
    c.rect(0, 0, 0, 15, BRASS)
    c.rect(15, 0, 15, 15, BRASS)
    # Шестерня Механикус в центре
    for y in range(16):
        for x in range(16):
            d = ((x - 7.5) ** 2 + (y - 7.5) ** 2) ** 0.5
            if 3.0 < d < 5.0 or (5.0 <= d < 6.0 and (x + y) % 3 == 0):
                c.px(x, y, shade(BRASS, 1.1))
            elif d < 1.6:
                c.px(x, y, GLOW)
    return c.img()


def key_item():
    c = Canvas()
    # Головка-шестерня
    for y in range(16):
        for x in range(16):
            d = ((x - 4.5) ** 2 + (y - 4.5) ** 2) ** 0.5
            if d < 3.6 or (3.6 <= d < 4.6 and (x * 3 + y) % 4 == 0):
                c.px(x, y, shade(BRASS, 1.0 + (4.5 - y) * 0.04))
            if d < 1.2:
                c.px(x, y, (40, 30, 20))
    # Стержень по диагонали к правому нижнему углу
    for i in range(7, 15):
        c.px(i, i, shade(STEEL, 1.2))
        c.px(i - 1, i, STEEL_DARK)
    # Бородка ключа
    c.px(13, 11, BRASS)
    c.px(14, 12, BRASS)
    c.px(11, 13, BRASS)
    c.px(12, 14, BRASS)
    return c.img()


def main():
    save(girder(), "block", "dock_girder.png")
    save(console_side(), "block", "shipyard_console_side.png")
    save(console_front(), "block", "shipyard_console_front.png")
    save(console_top(), "block", "shipyard_console_top.png")
    save(key_item(), "item", "omnissian_key.png")


if __name__ == "__main__":
    main()
