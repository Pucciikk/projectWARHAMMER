#!/usr/bin/env python3
"""
Пиксель-арт предметов, блоков и техножрецов для главы 1.

    python3 tools/textures/gen_items.py

Блоки и предметы — 16x16, скины техножрецов — 64x64 в раскладке скина игрока.
Знак Омниссии берёт рисунок иконки квеста «Ответ» из gen_ui.py.
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(__file__))
import gen_ui  # noqa: E402

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEX = os.path.join(ROOT, "src/main/resources/assets/warpbound/textures")
rng = random.Random(77)


def save(img, *path):
    p = os.path.join(TEX, *path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    img.save(p)
    print("  ", os.path.relpath(p, ROOT))


class Canvas:
    def __init__(self, w=16, h=16):
        self.a = np.zeros((h, w, 4), np.uint8)

    def px(self, x, y, c, a=255):
        h, w = self.a.shape[:2]
        if 0 <= x < w and 0 <= y < h:
            self.a[y, x] = (*c[:3], a)

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.px(x, y, c)

    def noisy(self, x0, y0, x1, y1, c, amp):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                k = rng.randint(-amp, amp)
                self.px(x, y, tuple(max(0, min(255, v + k)) for v in c))

    def get(self, x, y):
        return tuple(self.a[y, x][:3])

    def img(self):
        return Image.fromarray(self.a, "RGBA")


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


# ------------------------------------------------------------------ блоки

def hull(base, seam, rivet, embers=False):
    c = Canvas()
    c.noisy(0, 0, 15, 15, base, 5)
    for i in range(16):
        for k in (0, 8):
            c.px(k, i, seam)
            c.px(i, k, seam)
            c.px(k + 1, i, shade(base, 1.18))
            c.px(i, k + 1, shade(base, 1.18))
    for x in (3, 12):
        for y in (3, 12):
            c.px(x, y, rivet)
            c.px(x + 1, y + 1, shade(base, 0.6))
    if embers:
        for _ in range(9):
            x, y = rng.randrange(16), rng.randrange(16)
            if c.get(x, y) == seam or rng.random() < 0.4:
                c.px(x, y, rng.choice([(220, 90, 20), (180, 40, 10), (255, 150, 40)]))
    return c.img()


def brass():
    """Латунный пояс: горизонтальные рёбра и заклёпки."""
    c = Canvas()
    c.noisy(0, 0, 15, 15, (150, 112, 44), 7)
    for y in (0, 15):
        c.rect(0, y, 15, y, (92, 66, 24))
    for y in (4, 11):
        c.rect(0, y, 15, y, (196, 156, 70))
        c.rect(0, y + 1, 15, y + 1, (100, 72, 28))
    for x in range(1, 16, 4):
        c.px(x, 2, (230, 200, 110))
        c.px(x, 13, (230, 200, 110))
    return c.img()


def beacon_side():
    c = Canvas()
    c.noisy(0, 0, 15, 15, (58, 60, 66), 4)
    c.rect(0, 0, 15, 0, (138, 106, 42))
    c.rect(0, 15, 15, 15, (138, 106, 42))
    for y in range(4, 12, 2):
        c.rect(3, y, 12, y, (24, 24, 28))
    c.px(2, 2, (200, 170, 70))
    c.px(13, 2, (200, 170, 70))
    return c.img()


def beacon_top():
    c = Canvas()
    c.noisy(0, 0, 15, 15, (58, 60, 66), 4)
    for i in range(16):
        c.px(i, 0, (138, 106, 42))
        c.px(i, 15, (138, 106, 42))
        c.px(0, i, (138, 106, 42))
        c.px(15, i, (138, 106, 42))
    for y in range(3, 13):
        for x in range(3, 13):
            if (x + y) % 2 == 0:
                c.px(x, y, (30, 30, 34))
    c.rect(7, 7, 8, 8, (170, 172, 178))
    return c.img()


def beacon_front(repaired):
    c = Image.open(os.path.join(TEX, "block", "vox_beacon_side.png")).copy()
    cv = Canvas()
    cv.a = np.array(c)
    cv.rect(2, 3, 13, 12, (138, 106, 42))
    if repaired:
        cv.noisy(3, 4, 12, 11, (10, 50, 24), 4)
        for y in (6, 8, 10):
            for x in range(4, 4 + rng.randint(4, 8)):
                cv.px(x, y, (80, 240, 120))
        cv.px(7, 4, (220, 210, 180))
        cv.px(8, 4, (220, 210, 180))
    else:
        cv.noisy(3, 4, 12, 11, (14, 18, 16), 3)
        x, y = 5, 4
        while y < 12:
            cv.px(x, y, (90, 96, 100))
            x += rng.choice([-1, 0, 1])
            y += 1
        cv.px(10, 9, (90, 96, 100))
        cv.px(11, 10, (90, 96, 100))
        cv.px(11, 5, (220, 40, 30))
    return cv.img()


# ------------------------------------------------------------------ предметы

def slate(screen, glyph):
    c = Canvas()
    c.rect(3, 1, 12, 14, (120, 92, 40))
    c.rect(4, 2, 11, 13, (70, 60, 50))
    c.rect(5, 3, 10, 10, screen)
    for y in (4, 6, 8):
        for x in range(5, 5 + rng.randint(3, 6)):
            c.px(x, y, glyph)
    c.px(6, 12, (200, 30, 30))
    c.px(9, 12, (60, 220, 90))
    for x, y in ((3, 1), (12, 1), (3, 14), (12, 14)):
        c.px(x, y, (200, 170, 70))
    return c.img()


def vox_module():
    c = Canvas()
    c.rect(3, 6, 12, 14, (40, 42, 48))
    c.rect(4, 7, 11, 13, (92, 96, 104))
    c.rect(5, 9, 8, 12, (180, 100, 60))
    for y in (9, 11):
        c.rect(5, y, 8, y, (220, 140, 90))
    c.px(10, 9, (80, 240, 120))
    c.px(10, 11, (220, 40, 30))
    for y in range(1, 7):
        c.px(11, y, (140, 146, 156))
    c.px(10, 1, (80, 240, 120))
    c.px(12, 1, (80, 240, 120))
    return c.img()


def from_icon(fn):
    S = 8
    img = Image.new("RGBA", (32 * S, 32 * S), (0, 0, 0, 0))
    fn(ImageDraw.Draw(img), S)
    small = img.resize((16, 16), Image.LANCZOS)
    a = np.array(small)
    a[..., 3] = np.where(a[..., 3] > 110, 255, 0)
    return Image.fromarray(a, "RGBA")


def schematic(paper, ink, mark):
    """Развёрнутый свиток-чертёж: сетка линий и знак в центре."""
    c = Canvas()
    c.noisy(3, 3, 12, 12, paper, 6)
    for x in (4, 7, 10):
        for y in range(4, 12):
            c.px(x, y, ink)
    for y in (5, 8, 11):
        for x in range(4, 12):
            c.px(x, y, ink)
    for x, rows in ((1, (2, 13)), (2, (2, 13)), (13, (2, 13)), (14, (2, 13))):
        for y in range(rows[0], rows[1] + 1):
            c.px(x, y, shade(paper, 0.75 if x in (1, 14) else 0.95))
    c.rect(6, 6, 9, 9, mark)
    c.px(6, 6, paper)
    c.px(9, 6, paper)
    c.px(6, 9, paper)
    c.px(9, 9, paper)
    c.rect(7, 7, 8, 8, shade(mark, 0.5))
    return c.img()


# ------------------------------------------------------------------ техножрецы

def skin(robe, trim, metal, eye):
    c = Canvas(64, 64)
    robe_d = shade(robe, 0.7)

    def box(u, v, w, h, d, fill):
        """Заливка развёртки куба w x h x d с UV-углом (u, v), как у скина игрока."""
        for (x0, y0, ww, hh) in ((u + d, v, w, d), (u + d + w, v, w, d), (u, v + d, d, h),
                                 (u + d, v + d, w, h), (u + d + w, v + d, d, h), (u + d + w + d, v + d, w, h)):
            for y in range(y0, y0 + hh):
                for x in range(x0, x0 + ww):
                    fill(c, x, y, x - x0, y - y0, ww, hh)

    def robe_fill(cv, x, y, lx, ly, w, h):
        col = robe_d if lx % 3 == 1 else robe
        cv.px(x, y, shade(col, 1 + rng.uniform(-0.06, 0.06)))

    # голова: капюшон, лицо в тени
    box(0, 0, 8, 8, 8, robe_fill)
    c.rect(8, 8, 15, 15, (20, 16, 16))
    c.rect(9, 12, 14, 15, metal)
    for x in range(9, 15):
        if x % 2 == 0:
            c.px(x, 13, shade(metal, 0.5))
            c.px(x, 14, shade(metal, 0.5))
    c.px(10, 11, eye)
    c.px(13, 11, eye)
    # кайма капюшона на слое шляпы
    for x in range(40, 48):
        c.px(x, 8, trim)
    for y in range(8, 16):
        c.px(40, y, trim)
        c.px(47, y, trim)
    box(32, 0, 8, 8, 8, lambda cv, x, y, lx, ly, w, h: cv.px(x, y, robe) if not (40 <= x < 48 and 8 <= y < 16) else None)
    for y in range(9, 16):
        for x in range(41, 47):
            c.px(x, y, (0, 0, 0), 0)
    # тело
    box(16, 16, 8, 12, 4, robe_fill)
    c.rect(20, 26, 27, 27, (30, 26, 24))
    c.rect(23, 26, 24, 27, trim)
    for (x, y) in ((23, 21), (24, 21), (22, 22), (25, 22), (22, 23), (25, 23), (23, 24), (24, 24)):
        c.px(x, y, trim)
    c.px(23, 22, metal)
    c.px(24, 23, metal)
    # руки: рукава и металлические кисти
    for (u, v) in ((40, 16), (32, 48)):
        box(u, v, 4, 12, 4, robe_fill)
        for y in range(v + 13, v + 16):
            for x in range(u, u + 16):
                c.px(x, y, shade(metal, 1 + rng.uniform(-0.1, 0.1)))
        for x in range(u, u + 16):
            c.px(x, v + 12, trim)
    # ноги: подол и сапоги
    for (u, v) in ((0, 16), (16, 48)):
        box(u, v, 4, 12, 4, robe_fill)
        for y in range(v + 13, v + 16):
            for x in range(u, u + 16):
                c.px(x, y, (26, 22, 22))
    return c.img()


def eyes(eye):
    c = Canvas(64, 64)
    c.px(10, 11, eye)
    c.px(13, 11, eye)
    return c.img()


if __name__ == "__main__":
    print("Блоки:")
    save(hull((70, 74, 82), (40, 42, 48), (150, 154, 160)), "block", "hull_plating.png")
    save(hull((40, 36, 34), (18, 16, 16), (90, 84, 80), embers=True), "block", "scorched_hull_plating.png")
    save(brass(), "block", "brass_trim.png")
    save(beacon_side(), "block", "vox_beacon_side.png")
    save(beacon_top(), "block", "vox_beacon_top.png")
    save(beacon_front(False), "block", "vox_beacon_front_broken.png")
    save(beacon_front(True), "block", "vox_beacon_front.png")
    print("Предметы:")
    save(slate((60, 40, 10), (230, 170, 50)), "item", "data_slate_storm.png")
    save(slate((40, 10, 30), (220, 80, 160)), "item", "data_slate_navigator.png")
    save(slate((8, 40, 18), (80, 240, 120)), "item", "data_slate_ship.png")
    save(vox_module(), "item", "vox_module.png")
    save(from_icon(gen_ui.ic_answer), "item", "omnissiah_sigil.png")
    save(schematic((200, 190, 150), (40, 60, 120), (170, 30, 30)), "item", "forge_schematic.png")
    save(schematic((70, 60, 70), (150, 60, 170), (190, 30, 60)), "item", "obelisk_schematic.png")
    print("Техножрецы:")
    save(skin((132, 24, 22), (201, 162, 39), (120, 124, 132), (80, 255, 120)), "entity", "tech_priest.png")
    save(eyes((80, 255, 120)), "entity", "tech_priest_eyes.png")
    save(skin((34, 28, 38), (120, 40, 150), (90, 80, 70), (255, 50, 40)), "entity", "dark_tech_priest.png")
    save(eyes((255, 50, 40)), "entity", "dark_tech_priest_eyes.png")
