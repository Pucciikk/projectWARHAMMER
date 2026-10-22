#!/usr/bin/env python3
"""
Генератор интерфейса окна квестов: фон с аквилой и черепами, рамки узлов, иконки квестов,
кнопка в инвентаре и экран инфопланшета.

    python3 tools/textures/gen_ui.py

Всё рисуется векторно в 4x и сжимается, поэтому края мягкие, а мелкие иконки остаются читаемыми.
Пишет в src/main/resources/assets/warpbound/textures/gui/.
"""
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "src/main/resources/assets/warpbound/textures/gui")
rng = random.Random(1040)

GOLD = (201, 162, 39)
GOLD_DARK = (122, 92, 28)
BRONZE = (138, 106, 42)
BONE = (214, 202, 172)
BONE_SHADE = (150, 138, 112)
BLOOD = (122, 18, 18)
IRON = (92, 96, 104)
IRON_DARK = (40, 42, 48)


def save(img, *path):
    p = os.path.join(OUT, *path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    img.save(p)
    print("  ", os.path.relpath(p, ROOT))


def down(img, size):
    return img.resize(size, Image.LANCZOS)


# ------------------------------------------------------------------ фигуры

def skull(d, cx, cy, s, bone=BONE, shade=BONE_SHADE, hole=(16, 12, 10)):
    """Череп анфас. s — ширина черепной коробки."""
    r = s / 2
    d.ellipse([cx - r, cy - r * 1.05, cx + r, cy + r * 0.85], fill=bone)
    # скулы и челюсть
    d.polygon([(cx - r * 0.8, cy + r * 0.2), (cx + r * 0.8, cy + r * 0.2),
               (cx + r * 0.55, cy + r * 1.2), (cx - r * 0.55, cy + r * 1.2)], fill=bone)
    d.rectangle([cx - r * 0.5, cy + r * 1.05, cx + r * 0.5, cy + r * 1.45], fill=shade)
    # глазницы
    for sx in (-1, 1):
        ex = cx + sx * r * 0.4
        d.ellipse([ex - r * 0.3, cy - r * 0.05, ex + r * 0.3, cy + r * 0.5], fill=hole)
    # нос
    d.polygon([(cx, cy + r * 0.5), (cx - r * 0.13, cy + r * 0.8), (cx + r * 0.13, cy + r * 0.8)], fill=hole)
    # зубы
    for i in range(-2, 3):
        x = cx + i * r * 0.2
        d.line([x, cy + r * 1.05, x, cy + r * 1.45], fill=hole, width=max(1, int(r * 0.05)))
    d.line([cx - r * 0.5, cy + r * 1.25, cx + r * 0.5, cy + r * 1.25], fill=hole, width=max(1, int(r * 0.05)))


def aquila(d, cx, cy, w, col, col2=None):
    """Двуглавый орёл Империума. w — размах крыльев."""
    col2 = col2 or col
    u = w / 2
    for sx in (-1, 1):
        # несущая кость крыла: от плеча вверх и наружу
        bar = [(cx + sx * u * 0.1, cy - u * 0.12), (cx + sx * u * 0.55, cy - u * 0.42),
               (cx + sx * u * 1.0, cy - u * 0.5)]
        d.polygon([bar[0], bar[1], bar[2], (cx + sx * u * 0.92, cy - u * 0.4),
                   (cx + sx * u * 0.52, cy - u * 0.3), (cx + sx * u * 0.12, cy - u * 0.02)], fill=col)
        # перья свисают с кости веером, два ряда
        for row, (lmul, c) in enumerate(((1.0, col2), (0.7, col))):
            for j in range(9):
                t = (j + 0.5) / 9
                bx = cx + sx * u * (0.14 + 0.8 * t)
                by = cy - u * (0.08 + 0.36 * t) + row * u * 0.04
                length = u * (0.25 + 0.42 * math.sin(math.pi * (0.25 + 0.6 * t))) * lmul
                a = math.radians(-100 + 45 * t)  # вниз и чуть наружу
                tip = (bx + sx * abs(math.cos(a)) * length, by - math.sin(a) * length)
                half = u * 0.045
                d.polygon([(bx - half, by), tip, (bx + half, by)], fill=c)
        # голова смотрит наружу, короткая шея
        d.polygon([(cx + sx * u * 0.03, cy - u * 0.2), (cx + sx * u * 0.1, cy - u * 0.4),
                   (cx + sx * u * 0.2, cy - u * 0.38), (cx + sx * u * 0.12, cy - u * 0.16)], fill=col)
        hx, hy = cx + sx * u * 0.16, cy - u * 0.44
        d.ellipse([hx - u * 0.075, hy - u * 0.065, hx + u * 0.075, hy + u * 0.065], fill=col)
        d.polygon([(hx + sx * u * 0.05, hy - u * 0.045), (hx + sx * u * 0.19, hy + u * 0.01),
                   (hx + sx * u * 0.13, hy + u * 0.035), (hx + sx * u * 0.05, hy + u * 0.04)], fill=col)
    # тело и хвост
    d.polygon([(cx - u * 0.12, cy - u * 0.22), (cx + u * 0.12, cy - u * 0.22),
               (cx + u * 0.08, cy + u * 0.22), (cx - u * 0.08, cy + u * 0.22)], fill=col)
    for i in range(-2, 3):
        a = math.radians(90 + i * 13)
        tip = (cx + math.cos(a) * u * 0.42, cy + u * 0.18 + math.sin(a) * u * 0.34)
        d.polygon([(cx - u * 0.045 + i * u * 0.02, cy + u * 0.18), tip,
                   (cx + u * 0.045 + i * u * 0.02, cy + u * 0.18)], fill=col2 if i % 2 else col)


def cog(d, cx, cy, r, teeth, col, hole=None, tooth=0.22):
    pts = []
    for i in range(teeth * 4):
        a = 2 * math.pi * i / (teeth * 4)
        rr = r if (i // 2) % 2 == 0 else r * (1 - tooth)
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    d.polygon(pts, fill=col)
    if hole:
        d.ellipse([cx - r * 0.45, cy - r * 0.45, cx + r * 0.45, cy + r * 0.45], fill=hole)


def octagon(cx, cy, r):
    return [(cx + math.cos(math.radians(22.5 + 45 * i)) * r, cy + math.sin(math.radians(22.5 + 45 * i)) * r)
            for i in range(8)]


def noise(w, h, scale, amp, seed):
    """Гладкий шум: случайная сетка, растянутая билинейно."""
    g = np.random.default_rng(seed).random((h // scale + 2, w // scale + 2)).astype(np.float32)
    img = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return (np.asarray(img).astype(np.float32) / 255 - 0.5) * amp


# ------------------------------------------------------------------ фон окна квестов

def background():
    W, H, S = 512, 320, 4
    w, h = W * S, H * S
    # тёмный металл с шумом и виньеткой
    n = noise(w, h, 64, 28, 1) + noise(w, h, 12, 10, 2)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    vign = 1 - 0.55 * (((xx / w - 0.5) * 1.6) ** 2 + ((yy / h - 0.5) * 1.9) ** 2)
    base = np.stack([20 + n, 16 + n * 0.8, 15 + n * 0.7], -1) * vign[..., None]
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")

    # аквила, приглушённая
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    aquila(ImageDraw.Draw(layer), w / 2, h / 2 + 40 * S, 330 * S, GOLD_DARK + (70,), BRONZE + (55,))
    img = Image.alpha_composite(img, layer.filter(ImageFilter.GaussianBlur(S)))

    d = ImageDraw.Draw(img)
    # рамка: бронза, тёмная кровь, бронза
    for inset, col, width in ((3, BRONZE, 3), (8, BLOOD, 2), (12, GOLD_DARK, 1)):
        i = inset * S
        d.rectangle([i, i, w - i - 1, h - i - 1], outline=col, width=width * S)
    # заклёпки по рамке
    for x in range(40, W - 30, 32):
        for y in (5.5, H - 5.5):
            d.ellipse([(x - 1.6) * S, (y - 1.6) * S, (x + 1.6) * S, (y + 1.6) * S], fill=GOLD)
    for y in range(40, H - 30, 32):
        for x in (5.5, W - 5.5):
            d.ellipse([(x - 1.6) * S, (y - 1.6) * S, (x + 1.6) * S, (y + 1.6) * S], fill=GOLD)
    # черепа в углах на бронзовых щитках
    for cx, cy in ((17, 17), (W - 17, 17), (17, H - 17), (W - 17, H - 17)):
        d.polygon(octagon(cx * S, cy * S, 14 * S), fill=IRON_DARK, outline=BRONZE)
        d.polygon(octagon(cx * S, cy * S, 14 * S), outline=BRONZE, width=2 * S)
        skull(d, cx * S, (cy - 3) * S, 13 * S)
    # череп-навершие по центру сверху и снизу
    for cy, flip in ((9, False), (H - 9, True)):
        cx = W / 2
        d.polygon([(cx - 34) * S, cy * S, (cx - 20) * S, (cy - 6) * S, (cx + 20) * S, (cy - 6) * S,
                   (cx + 34) * S, cy * S, (cx + 20) * S, (cy + 6) * S, (cx - 20) * S, (cy + 6) * S],
                  fill=IRON_DARK, outline=BRONZE)
        skull(d, cx * S, (cy - 3.5) * S, 9 * S)
        for sx in (-1, 1):
            # крылышки у черепа
            for k in range(3):
                d.polygon([((cx + sx * 7) * S, (cy - 2 + k * 2) * S),
                           ((cx + sx * (30 - k * 5)) * S, (cy - 4 + k * 3) * S),
                           ((cx + sx * 7) * S, (cy + k * 2) * S)], fill=GOLD_DARK)
    # печать чистоты: красный воск и полоски пергамента под списком глав
    px, py = 62, H - 88
    for k, off in enumerate((-5, 2, 8)):
        d.polygon([((px + off) * S, py * S), ((px + off + 5) * S, py * S),
                   ((px + off + 4 + k) * S, (py + 30 + k * 6) * S), ((px + off - 1 + k) * S, (py + 28 + k * 6) * S)],
                  fill=(196, 182, 140))
        for line in range(4):
            yl = py + 10 + line * 5 + k * 2
            d.line([(px + off + 1) * S, yl * S, (px + off + 4) * S, yl * S], fill=(90, 70, 50), width=S // 2 + 1)
    d.ellipse([(px - 9) * S, (py - 7) * S, (px + 9) * S, (py + 9) * S], fill=(150, 22, 22))
    d.ellipse([(px - 6) * S, (py - 4) * S, (px + 6) * S, (py + 6) * S], outline=(100, 10, 10), width=S)
    aquila(d, px * S, (py + 1.5) * S, 11 * S, (100, 10, 10))

    save(down(img, (W, H)), "quest", "background.png")


# ------------------------------------------------------------------ узлы

def node(name, frame, inner, glow=None):
    S, N = 8, 32
    img = Image.new("RGBA", (N * S, N * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = N * S / 2
    if glow:
        g = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(g).polygon(octagon(c, c, 15.5 * S), fill=glow)
        img = Image.alpha_composite(img, g.filter(ImageFilter.GaussianBlur(2 * S)))
        d = ImageDraw.Draw(img)
    d.polygon(octagon(c, c, 15 * S), fill=frame)
    d.polygon(octagon(c, c, 12.5 * S), fill=tuple(int(v * 0.55) for v in frame))
    d.polygon(octagon(c, c, 11.5 * S), fill=inner)
    for i in range(8):
        a = math.radians(22.5 + 45 * i)
        x, y = c + math.cos(a) * 13.8 * S, c + math.sin(a) * 13.8 * S
        d.ellipse([x - S * 0.9, y - S * 0.9, x + S * 0.9, y + S * 0.9], fill=tuple(min(255, int(v * 1.3)) for v in frame))
    save(down(img, (N, N)), "quest", name + ".png")


# ------------------------------------------------------------------ иконки квестов (32x32)

def icon(name, draw):
    S, N = 8, 32
    img = Image.new("RGBA", (N * S, N * S), (0, 0, 0, 0))
    draw(ImageDraw.Draw(img), S)
    # тёмный контур, чтобы иконка читалась на любом фоне
    a = img.split()[3].filter(ImageFilter.MaxFilter(2 * S + 1))
    outline = Image.new("RGBA", img.size, (10, 8, 8, 255))
    outline.putalpha(a)
    img = Image.alpha_composite(outline, img)
    save(down(img, (N, N)), "quest", "icon", name + ".png")


def ic_awakening(d, S):
    for i in range(12):
        a = 2 * math.pi * i / 12
        d.line([16 * S + math.cos(a) * 11 * S, 16 * S + math.sin(a) * 9 * S,
                16 * S + math.cos(a) * 14.5 * S, 16 * S + math.sin(a) * 13 * S], fill=GOLD, width=S)
    d.polygon([(3 * S, 16 * S), (16 * S, 7 * S), (29 * S, 16 * S), (16 * S, 25 * S)], fill=BONE)
    d.ellipse([10.5 * S, 10.5 * S, 21.5 * S, 21.5 * S], fill=(180, 30, 20))
    d.ellipse([13.5 * S, 13.5 * S, 18.5 * S, 18.5 * S], fill=(15, 5, 5))
    d.ellipse([14 * S, 12.5 * S, 15.5 * S, 14 * S], fill=(255, 230, 200))


def ic_capsule(d, S):
    for i in range(6):
        d.ellipse([(2 + i * 2) * S, (2 + i * 2) * S, (9 + i * 2) * S, (9 + i * 2) * S],
                  fill=(240, 120 - i * 10, 20, 200 - i * 20))
    d.polygon([(9 * S, 13 * S), (13 * S, 9 * S), (28 * S, 22 * S), (24 * S, 27 * S)], fill=IRON)
    d.ellipse([20 * S, 19 * S, 29.5 * S, 28.5 * S], fill=IRON)
    d.polygon([(15 * S, 13.5 * S), (17.5 * S, 11 * S), (19.5 * S, 13 * S), (17 * S, 15.5 * S)], fill=GOLD)
    d.line([11 * S, 13 * S, 25 * S, 25.5 * S], fill=(140, 146, 156), width=S)
    d.ellipse([20.5 * S, 18.5 * S, 24 * S, 22 * S], fill=(110, 200, 255))


def flame(d, cx, by, h, S, col=(240, 110, 20), core=(255, 220, 90)):
    d.polygon([(cx, by - h), (cx + h * 0.35, by - h * 0.35), (cx + h * 0.3, by), (cx - h * 0.3, by),
               (cx - h * 0.35, by - h * 0.4)], fill=col)
    d.polygon([(cx, by - h * 0.6), (cx + h * 0.17, by - h * 0.2), (cx, by), (cx - h * 0.17, by - h * 0.2)], fill=core)


def ic_fire_and_stone(d, S):
    flame(d, 22 * S, 29 * S, 16 * S, S)
    d.line([5 * S, 27 * S, 19 * S, 9 * S], fill=(110, 75, 40), width=3 * S)
    d.polygon([(8 * S, 5 * S), (18 * S, 6 * S), (25 * S, 13 * S), (23 * S, 15 * S), (17 * S, 10 * S), (8 * S, 8 * S)],
              fill=(130, 130, 134))


def ic_first_night(d, S):
    d.ellipse([3 * S, 3 * S, 23 * S, 23 * S], fill=(220, 220, 200))
    d.ellipse([9 * S, 0, 29 * S, 20 * S], fill=(0, 0, 0, 0))
    skull(d, 21 * S, 20 * S, 12 * S)


def ic_smoke(d, S):
    for k, x in enumerate((8, 17, 25)):
        for i in range(5):
            r = (2.2 + i * 0.7) * S
            yy = (24 - i * 4.5) * S
            xx = (x + math.sin(i + k) * 2) * S
            g = 120 + i * 12
            d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=(g, g, g + 6, 230 - i * 25))
    d.polygon([(2 * S, 30 * S), (6 * S, 24 * S), (12 * S, 26 * S), (18 * S, 23 * S), (24 * S, 27 * S),
               (30 * S, 25 * S), (30 * S, 30 * S)], fill=IRON_DARK)
    flame(d, 12 * S, 28 * S, 6 * S, S)


def ic_iron_and_copper(d, S):
    def ingot(x, y, col, hi):
        d.polygon([(x, y + 6 * S), (x + 4 * S, y), (x + 18 * S, y), (x + 22 * S, y + 6 * S)], fill=hi)
        d.rectangle([x, y + 6 * S, x + 22 * S, y + 10 * S], fill=col)
    ingot(5 * S, 18 * S, (190, 100, 60), (230, 140, 90))
    ingot(3 * S, 9 * S, (170, 172, 178), (220, 222, 226))
    d.line([12 * S, 25 * S, 30 * S, 7 * S], fill=(200, 20, 20), width=2 * S)
    d.ellipse([26 * S, 3 * S, 31 * S, 8 * S], fill=(255, 60, 40))


def ic_vox(d, S):
    for i, r in enumerate((6, 10, 14)):
        d.arc([16 * S - r * S, 8 * S - r * S, 16 * S + r * S, 8 * S + r * S], 200, 340,
              fill=(90, 230, 120, 255 - i * 50), width=S + S // 2)
    d.line([16 * S, 9 * S, 16 * S, 24 * S], fill=IRON, width=2 * S)
    d.ellipse([13.5 * S, 6.5 * S, 18.5 * S, 11.5 * S], fill=(90, 230, 120))
    d.polygon([(8 * S, 30 * S), (12 * S, 22 * S), (20 * S, 22 * S), (24 * S, 30 * S)], fill=IRON)
    d.rectangle([12 * S, 25 * S, 20 * S, 27 * S], fill=GOLD)


def ic_answer(d, S):
    cog(d, 16 * S, 16 * S, 15 * S, 8, (150, 30, 30), tooth=0.2)
    d.ellipse([5 * S, 5 * S, 27 * S, 27 * S], fill=(30, 26, 26))
    # череп Механикус: левая половина кость, правая — металл с оптикой
    skull(d, 16 * S, 14 * S, 15 * S)
    d.polygon([(16 * S, 5 * S), (24 * S, 8 * S), (24.5 * S, 22 * S), (16 * S, 25 * S)], fill=(120, 124, 132))
    d.ellipse([17.5 * S, 13 * S, 22.5 * S, 18 * S], fill=(60, 255, 90))
    for y in (20, 22.5):
        d.line([16 * S, y * S, 23 * S, y * S], fill=(60, 62, 70), width=S)


def ic_chapter_wreckage(d, S):
    aquila(d, 16 * S, 18 * S, 30 * S, GOLD, GOLD_DARK)
    d.line([12 * S, 4 * S, 17 * S, 15 * S, 14 * S, 22 * S, 19 * S, 30 * S], fill=(20, 10, 8), width=S + S // 2)


def ic_chapter_whisper(d, S):
    c = 16 * S
    for i in range(8):
        a = 2 * math.pi * i / 8
        tip = (c + math.cos(a) * 15 * S, c + math.sin(a) * 15 * S)
        d.line([c, c, tip[0], tip[1]], fill=(150, 20, 40), width=2 * S)
        side = (math.cos(a + 2.4) * 2.5 * S, math.sin(a + 2.4) * 2.5 * S)
        side2 = (math.cos(a - 2.4) * 2.5 * S, math.sin(a - 2.4) * 2.5 * S)
        d.polygon([tip, (tip[0] + side[0], tip[1] + side[1]), (tip[0] + side2[0], tip[1] + side2[1])], fill=(170, 30, 60))
    d.ellipse([c - 5 * S, c - 5 * S, c + 5 * S, c + 5 * S], fill=(90, 20, 110))
    d.ellipse([c - 2.5 * S, c - 2.5 * S, c + 2.5 * S, c + 2.5 * S], fill=(230, 180, 255))


# ------------------------------------------------------------------ кнопка в инвентаре

def button():
    S = 8
    sheet = Image.new("RGBA", (20, 36), (0, 0, 0, 0))
    for k, (frame, face) in enumerate(((BRONZE, (34, 30, 30)), (GOLD, (60, 44, 40)))):
        img = Image.new("RGBA", (20 * S, 18 * S), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, 20 * S - 1, 18 * S - 1], fill=frame)
        d.rectangle([S, S, 19 * S - 1, 17 * S - 1], fill=face)
        aquila(d, 10 * S, 10 * S, 17 * S, GOLD if k else (190, 150, 50), GOLD_DARK)
        sheet.paste(down(img, (20, 18)), (0, k * 18))
    save(sheet, "quest", "button.png")


# ------------------------------------------------------------------ экран инфопланшета

def slate():
    W, H, S = 256, 160, 4
    img = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, W * S - 1, H * S - 1], radius=10 * S, fill=(58, 50, 40))
    d.rounded_rectangle([3 * S, 3 * S, (W - 3) * S, (H - 3) * S], radius=8 * S, outline=BRONZE, width=2 * S)
    d.rectangle([12 * S, 14 * S, (W - 12) * S, (H - 16) * S], fill=(6, 22, 12))
    for x in (8, W - 8):
        for y in (8, H - 8):
            d.ellipse([(x - 2) * S, (y - 2) * S, (x + 2) * S, (y + 2) * S], fill=GOLD)
    skull(d, W / 2 * S, 5.5 * S, 6 * S)
    for i, col in enumerate(((200, 30, 30), (220, 170, 40), (60, 220, 90))):
        x = W - 30 + i * 7
        d.ellipse([(x - 2) * S, (H - 10) * S, (x + 2) * S, (H - 6) * S], fill=col)
    img = down(img, (W, H))
    # строки развёртки на экране
    px = img.load()
    for y in range(14, H - 16, 2):
        for x in range(12, W - 12):
            r, g, b, a = px[x, y]
            px[x, y] = (r, min(255, g + 6), b + 2, a)
    save(img, "slate.png")


if __name__ == "__main__":
    print("Интерфейс:")
    background()
    node("node_done", GOLD, (34, 26, 18))
    node("node_open", (170, 40, 40), (30, 20, 20), glow=(200, 40, 30, 150))
    node("node_locked", (64, 64, 70), (18, 18, 20))
    for name, fn in (("awakening", ic_awakening), ("capsule", ic_capsule), ("fire_and_stone", ic_fire_and_stone),
                     ("first_night", ic_first_night), ("smoke", ic_smoke), ("iron_and_copper", ic_iron_and_copper),
                     ("vox", ic_vox), ("answer", ic_answer), ("chapter_wreckage", ic_chapter_wreckage),
                     ("chapter_whisper", ic_chapter_whisper)):
        icon(name, fn)
    button()
    slate()
