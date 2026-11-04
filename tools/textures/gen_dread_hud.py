#!/usr/bin/env python3
"""
Вид изнутри саркофага: наложение на весь экран, assets/warpbound/textures/gui/dread_cockpit.png (1920×1080).
Тёмная броня, большая смотровая щель посередине (прозрачная), ниши под приборы, аквила и мелкие детали: циферблаты, кабели, решётки, лампы, печати чистоты, табличка литании.
Щель симметрична относительно середины экрана: там прицел. Положения ниш совпадают с константами в client/entity/DreadCockpitHud.

    python3 tools/textures/gen_dread_hud.py
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(ROOT, "src/main/resources/assets/warpbound/textures/gui/dread_cockpit.png")
W, H = 1920, 1080
# доли экрана, должны совпадать с DreadCockpitHud
SLIT = (0.155, 0.31, 0.845, 0.69)
LEFT = (0.015, 0.31, 0.135, 0.69)
RIGHT = (0.865, 0.31, 0.985, 0.69)
BOTTOM = (0.36, 0.75, 0.64, 0.87)

rng = np.random.default_rng(40)
GOLD, GOLD_L, GOLD_D, GOLD_DD = (172, 128, 52), (232, 190, 104), (104, 74, 30), (54, 38, 16)
BRASS, IRON, IRON_L, SOOT = (120, 92, 44), (46, 46, 50), (84, 84, 90), (10, 10, 11)


def box(r):
    return (int(r[0] * W), int(r[1] * H), int(r[2] * W), int(r[3] * H))


# ---- основа: потёртый тёмный металл с вертикальными разводами
yy, xx = np.mgrid[0:H, 0:W]
coarse = np.array(Image.fromarray((rng.random((H // 40, W // 40)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), dtype=np.float32) / 255
fine = np.array(Image.fromarray((rng.random((H // 4, W // 4)) * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), dtype=np.float32) / 255
streak = np.array(Image.fromarray((rng.random((H // 30, W // 3)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), dtype=np.float32) / 255
base = 22 + coarse * 14 + fine * 7 + streak * 6
dx = (xx - W / 2) / (W / 2)
dy = (yy - H / 2) / (H / 2)
base *= np.clip(1.15 - (dx * dx + dy * dy) * 0.42, 0.4, 1.2)
img = Image.fromarray(np.clip(np.stack((base * 1.02, base, base * 1.04), axis=2), 0, 255).astype(np.uint8), "RGB").convert("RGBA")
d = ImageDraw.Draw(img)


def plate(r, light=48, dark=8):
    """Панель: тёмная разделка по контуру и светлая кромка сверху."""
    x0, y0, x1, y1 = box(r)
    d.rectangle((x0 - 5, y0 - 5, x1 + 5, y1 + 5), outline=(dark, dark, dark, 255), width=5)
    d.line((x0, y0, x1, y0), fill=(light, light, light + 4, 255), width=2)
    d.line((x0, y0, x0, y1), fill=(light - 10, light - 10, light - 6, 255), width=2)


def rivet(px, py, r=6):
    d.ellipse((px - r - 2, py - r - 1, px + r + 2, py + r + 3), fill=(*SOOT, 255))
    d.ellipse((px - r, py - r, px + r, py + r), fill=(*GOLD_D, 255))
    d.ellipse((px - r * 0.45, py - r * 0.7, px + r * 0.1, py - r * 0.15), fill=(*GOLD_L, 255))


def rivets(r, n, inset=18):
    x0, y0, x1, y1 = box(r)
    for i in range(n):
        for py in (y0 + inset, y1 - inset):
            rivet(x0 + inset + (x1 - x0 - 2 * inset) * i / max(1, n - 1), py)


def dial(cx, cy, r, value, tint=(214, 176, 92)):
    """Циферблат: латунное кольцо, деления, стрелка, красный сектор."""
    d.ellipse((cx - r - 7, cy - r - 7, cx + r + 7, cy + r + 7), fill=(*SOOT, 255))
    d.ellipse((cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4), fill=(*BRASS, 255))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(18, 20, 18, 255))
    for i in range(13):
        a = math.radians(150 + 240 * i / 12)
        long = i % 3 == 0
        p0 = (cx + math.cos(a) * r * (0.72 if long else 0.82), cy + math.sin(a) * r * (0.72 if long else 0.82))
        p1 = (cx + math.cos(a) * r * 0.93, cy + math.sin(a) * r * 0.93)
        d.line((p0, p1), fill=(*((200, 60, 40) if i > 9 else tint), 255), width=2)
    a = math.radians(150 + 240 * value)
    d.line(((cx, cy), (cx + math.cos(a) * r * 0.8, cy + math.sin(a) * r * 0.8)), fill=(226, 220, 200, 255), width=3)
    d.ellipse((cx - r * 0.14, cy - r * 0.14, cx + r * 0.14, cy + r * 0.14), fill=(*GOLD, 255))
    for t in (45, 135, 225, 315):
        rivet(cx + math.cos(math.radians(t)) * (r + 10), cy + math.sin(math.radians(t)) * (r + 10), 3)


def vent(x0, y0, x1, y1, n):
    """Решётка: тёмная ниша и косые планки."""
    d.rectangle((x0 - 4, y0 - 4, x1 + 4, y1 + 4), fill=(*IRON, 255))
    d.rectangle((x0, y0, x1, y1), fill=(*SOOT, 255))
    for i in range(n):
        y = y0 + 4 + (y1 - y0 - 8) * i / max(1, n - 1)
        d.line((x0 + 2, y, x1 - 2, y), fill=(*IRON_L, 255), width=3)
        d.line((x0 + 2, y + 3, x1 - 2, y + 3), fill=(24, 24, 26, 255), width=2)
    for px, py in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        rivet(px, py, 4)


def cable(points, w=12, color=(30, 28, 26)):
    """Гофрированный кабель по кривой Безье: тень, тело, блик и кольца."""
    samples = []
    n = len(points) - 1
    for k in range(61):
        t = k / 60
        x = sum(math.comb(n, i) * (1 - t) ** (n - i) * t ** i * p[0] for i, p in enumerate(points))
        y = sum(math.comb(n, i) * (1 - t) ** (n - i) * t ** i * p[1] for i, p in enumerate(points))
        samples.append((x, y))
    d.line([(x + 2, y + 4) for x, y in samples], fill=(*SOOT, 255), width=w + 4, joint="curve")
    d.line(samples, fill=(*color, 255), width=w, joint="curve")
    d.line([(x, y - w * 0.25) for x, y in samples], fill=(70, 66, 60, 255), width=max(1, w // 5), joint="curve")
    for x, y in samples[::4]:
        d.ellipse((x - w * 0.52, y - w * 0.52, x + w * 0.52, y + w * 0.52), outline=(14, 13, 12, 255), width=1)


def clamp(cx, cy, w=30, h=20):
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), radius=3, fill=(*BRASS, 255), outline=(*GOLD_DD, 255))
    rivet(cx - w / 2 + 6, cy, 3)
    rivet(cx + w / 2 - 6, cy, 3)


def lamps(x, y, colors, gap=30, r=7):
    d.rounded_rectangle((x - 14, y - 16, x + gap * (len(colors) - 1) + 14, y + 16), radius=4, fill=(*SOOT, 255), outline=(*GOLD_DD, 255))
    for i, c in enumerate(colors):
        px = x + i * gap
        d.ellipse((px - r - 2, y - r - 2, px + r + 2, y + r + 2), fill=(*GOLD_D, 255))
        d.ellipse((px - r, y - r, px + r, y + r), fill=(*c, 255))
        d.ellipse((px - r * 0.5, y - r * 0.6, px, y - r * 0.1), fill=tuple(min(255, v + 90) for v in c) + (255,))


def glyphs(x0, y, x1, h=10, color=GOLD_DD):
    """Строка «литании»: рубленые знаки, читать не надо."""
    x = x0
    k = 0
    while x < x1:
        w = int(rng.integers(4, 11))
        if k % 6 == 5:
            x += 8
        else:
            d.rectangle((x, y, x + w, y + h), fill=(*color, 255))
            if rng.random() < 0.4:
                d.rectangle((x + 1, y + h // 2, x + w - 1, y + h // 2 + 1), fill=(172, 128, 52, 255))
            x += w + 3
        k += 1


def plaque(x0, y0, x1, y1, lines):
    d.rectangle((x0 - 4, y0 - 4, x1 + 4, y1 + 4), fill=(*GOLD_DD, 255))
    d.rectangle((x0, y0, x1, y1), fill=(*BRASS, 255))
    d.line((x0, y0, x1, y0), fill=(*GOLD_L, 255), width=2)
    step = (y1 - y0 - 14) / lines
    for i in range(lines):
        glyphs(x0 + 16, y0 + 9 + i * step, x1 - 16, max(5, int(step * 0.55)))
    for px, py in ((x0 + 7, y0 + 7), (x1 - 7, y0 + 7), (x0 + 7, y1 - 7), (x1 - 7, y1 - 7)):
        rivet(px, py, 3)


def seal(cx, cy, r=26, strips=2):
    """Печать чистоты: пергамент и красный воск."""
    for i in range(strips):
        px = cx - 12 + i * 22
        ln = 90 + i * 24
        d.polygon([(px - 9, cy), (px + 9, cy), (px + 12, cy + ln), (px + 2, cy + ln - 8), (px - 7, cy + ln + 3)], fill=(170, 146, 98, 255), outline=(82, 66, 40, 255))
        for k in range(5):
            d.line((px - 5, cy + 26 + k * 12, px + 6, cy + 26 + k * 12), fill=(62, 48, 30, 255), width=1)
    d.ellipse((cx - r - 3, cy - r - 2, cx + r + 3, cy + r + 4), fill=(46, 8, 6, 255))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(126, 22, 18, 255))
    d.ellipse((cx - r * 0.72, cy - r * 0.72, cx + r * 0.72, cy + r * 0.72), outline=(176, 50, 40, 255), width=2)
    d.polygon([(cx, cy - r * 0.5), (cx + r * 0.42, cy + r * 0.1), (cx, cy + r * 0.5), (cx - r * 0.42, cy + r * 0.1)], fill=(92, 14, 12, 255))


def cog(cx, cy, r):
    """Шестерня Механикус."""
    teeth = 10
    pts = []
    for i in range(teeth * 4):
        a = 2 * math.pi * i / (teeth * 4)
        pts.append((cx + math.cos(a) * (r if i % 4 < 2 else r * 0.8), cy + math.sin(a) * (r if i % 4 < 2 else r * 0.8)))
    d.polygon(pts, fill=(*BRASS, 255), outline=(*GOLD_DD, 255))
    d.ellipse((cx - r * 0.56, cy - r * 0.56, cx + r * 0.56, cy + r * 0.56), fill=(*GOLD_D, 255))
    d.ellipse((cx - r * 0.3, cy - r * 0.3, cx + r * 0.3, cy + r * 0.3), fill=(*SOOT, 255))
    d.ellipse((cx - r * 0.14, cy - r * 0.14, cx + r * 0.14, cy + r * 0.14), fill=(200, 60, 40, 255))


# ------------------------------------------------------------------ аквила: рисуем крупно и уменьшаем, иначе перья рваные

def aquila(cx, cy, scale):
    SS = 3
    size = (int(700 * scale * SS), int(300 * scale * SS))
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    a = ImageDraw.Draw(layer)
    ox, oy = size[0] / 2, size[1] * 0.42
    k = scale * SS

    def P(x, y):
        return (ox + x * k, oy + y * k)

    def feather(side, x, y, angle, length, width, fill, edge, spine):
        """Перо от точки: вытянутый лист с тёмной кромкой и светлой осью."""
        c, s = math.cos(angle), math.sin(angle)
        def F(u, v):
            return P(x + side * (u * c - v * s), y + (u * s + v * c))
        pts = [F(0, -width * 0.4), F(length * 0.45, -width * 0.5), F(length * 0.82, -width * 0.36), F(length, 0), F(length * 0.82, width * 0.36), F(length * 0.45, width * 0.5), F(0, width * 0.4)]
        a.polygon(pts, fill=(*edge, 255))
        inner = [F(length * 0.03, -width * 0.26), F(length * 0.45, -width * 0.36), F(length * 0.8, -width * 0.24), F(length * 0.94, 0), F(length * 0.8, width * 0.2), F(length * 0.45, width * 0.26), F(length * 0.03, width * 0.2)]
        a.polygon(inner, fill=(*fill, 255))
        a.line((F(length * 0.04, -width * 0.04), F(length * 0.88, -width * 0.02)), fill=(*spine, 255), width=max(1, int(1.6 * k)))
        for t in (0.3, 0.5, 0.7):
            a.line((F(length * t, -width * 0.02), F(length * (t + 0.09), -width * 0.3)), fill=(*spine, 255), width=max(1, int(0.8 * k)))

    for side in (-1, 1):
        # маховые перья: веером вверх и в сторону, от длинных к коротким
        for i in range(10):
            t = i / 9
            ang = math.radians(-24 + 72 * t)
            feather(side, 40, -8 + t * 18, ang, 300 - 165 * t, 34 - 8 * t, GOLD if i % 2 else (190, 142, 62), GOLD_DD, GOLD_L)
        # кроющие перья средним рядом
        for i in range(8):
            t = i / 7
            ang = math.radians(-20 + 66 * t)
            feather(side, 38, -6 + t * 16, ang, 158 - 64 * t, 26 - 5 * t, (206, 158, 74), GOLD_DD, (244, 208, 130))
        # верхний ряд у плеча
        for i in range(6):
            t = i / 5
            ang = math.radians(-14 + 58 * t)
            feather(side, 34, -8 + t * 12, ang, 76 - 22 * t, 20 - 4 * t, (224, 178, 92), GOLD_D, (250, 224, 150))
        # шея и голова смотрит наружу, клюв крючком, глаз красный
        neck = [P(side * 8, -4), P(side * 34, -8), P(side * 42, -44), P(side * 58, -66), P(side * 40, -80), P(side * 18, -60), P(side * 6, -30)]
        a.polygon(neck, fill=(*GOLD, 255), outline=(*GOLD_DD, 255))
        for j in range(5):
            y = -16 - j * 12
            a.line((P(side * (10 + j * 2), y), P(side * (36 + j * 2), y - 3)), fill=(*GOLD_D, 255), width=max(1, int(1.2 * k)))
        head = [P(side * 16, -66), P(side * 26, -90), P(side * 50, -98), P(side * 72, -90), P(side * 84, -78), P(side * 96, -70), P(side * 92, -56), P(side * 80, -62), P(side * 70, -60), P(side * 48, -56), P(side * 26, -54)]
        a.polygon(head, fill=(*(214, 168, 84), 255), outline=(*GOLD_DD, 255))
        # клюв и его тёмная граница
        a.polygon([P(side * 70, -86), P(side * 86, -78), P(side * 98, -68), P(side * 92, -54), P(side * 82, -62), P(side * 68, -66)], fill=(*GOLD_L, 255), outline=(*GOLD_DD, 255))
        a.line((P(side * 68, -72), P(side * 90, -66)), fill=(*GOLD_DD, 255), width=max(1, int(1.2 * k)))
        # глаз
        ex, ey = P(side * 56, -78)
        r = 5.2 * k
        a.ellipse((ex - r, ey - r, ex + r, ey + r), fill=(*SOOT, 255))
        r = 3.4 * k
        a.ellipse((ex - r, ey - r, ex + r, ey + r), fill=(210, 40, 24, 255))
        a.ellipse((ex - r * 0.5, ey - r * 0.7, ex, ey - r * 0.1), fill=(255, 170, 130, 255))
        # чешуя на затылке
        for j in range(4):
            a.arc((*P(side * 26 - 10 * k / k, -86 + j * 8), *P(side * 26 + 14, -76 + j * 8)) if side > 0 else (*P(side * 26 - 14, -86 + j * 8), *P(side * 26 + 10, -76 + j * 8)), 0, 180, fill=(*GOLD_D, 255), width=max(1, int(k)))
        # лапа с когтями
        for j, off in enumerate((-8, 0, 8)):
            a.polygon([P(side * (18 + off * 0.3), 52), P(side * (24 + off * 0.7), 74), P(side * (28 + off), 88), P(side * (20 + off), 76), P(side * (12 + off * 0.4), 58)], fill=(*GOLD_D, 255), outline=(*GOLD_DD, 255))
    # хвост веером
    for i in range(5):
        ang = math.radians(90 + (i - 2) * 13)
        feather(1, 0, 54, ang, 78 - abs(i - 2) * 8, 20, GOLD, GOLD_DD, GOLD_L)
    # грудь: щит с черепом
    a.polygon([P(-30, -16), P(30, -16), P(38, 12), P(26, 52), P(0, 74), P(-26, 52), P(-38, 12)], fill=(*GOLD_D, 255), outline=(*GOLD_DD, 255))
    a.polygon([P(-24, -10), P(24, -10), P(30, 12), P(21, 46), P(0, 64), P(-21, 46), P(-30, 12)], fill=(36, 30, 24, 255), outline=(*GOLD, 255))
    a.ellipse((*P(-18, -8), *P(18, 26)), fill=(216, 200, 164, 255), outline=(70, 58, 40, 255))
    a.rectangle((*P(-11, 20), *P(11, 40)), fill=(216, 200, 164, 255), outline=(70, 58, 40, 255))
    for x in (-8, -3, 2, 7):
        a.line((P(x, 30), P(x, 40)), fill=(58, 46, 30, 255), width=max(1, int(k)))
    for x in (-8, 8):
        ex, ey = P(x, 9)
        r = 5.6 * k
        a.ellipse((ex - r, ey - r * 0.9, ex + r, ey + r * 0.9), fill=(18, 14, 12, 255))
    a.polygon([P(-3, 16), P(3, 16), P(0, 23)], fill=(30, 24, 18, 255))
    # перевязь с заклёпками поверх крыльев у плеч
    for side in (-1, 1):
        a.line((P(side * 30, -14), P(side * 46, 4)), fill=(*GOLD_L, 255), width=max(2, int(2.4 * k)))
    layer = layer.resize((size[0] // SS, size[1] // SS), Image.LANCZOS)
    # тень под орлом на броне
    shadow = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    shadow.putalpha(layer.getchannel("A").point(lambda v: v * 0.7))
    shadow = shadow.filter(ImageFilter.GaussianBlur(4))
    px, py = int(cx - layer.size[0] / 2), int(cy - layer.size[1] * 0.42)
    img.alpha_composite(shadow, (px + 4, py + 7))
    img.alpha_composite(layer, (px, py))


# ------------------------------------------------------------------ сборка

plate((0.015, 0.025, 0.985, 0.27))
plate((0.015, 0.73, 0.985, 0.975))
rivets((0.015, 0.025, 0.985, 0.27), 24)
rivets((0.015, 0.73, 0.985, 0.975), 24)

# ---- верх: решётки и приборы по сторонам от орла
vent(int(W * 0.035), int(H * 0.07), int(W * 0.15), int(H * 0.235), 9)
vent(int(W * 0.85), int(H * 0.07), int(W * 0.965), int(H * 0.235), 9)
dial(int(W * 0.205), int(H * 0.15), 62, 0.34)
dial(int(W * 0.285), int(H * 0.17), 42, 0.62, (160, 200, 150))
dial(int(W * 0.795), int(H * 0.15), 62, 0.71)
dial(int(W * 0.715), int(H * 0.17), 42, 0.28, (160, 200, 150))
lamps(int(W * 0.185), int(H * 0.055), [(70, 170, 70), (70, 170, 70), (214, 150, 40), (70, 170, 70), (180, 40, 30)])
lamps(int(W * 0.74), int(H * 0.055), [(180, 40, 30), (70, 170, 70), (70, 170, 70), (214, 150, 40), (70, 170, 70)])
# ---- кабели вдоль щели, с хомутами
cable([(W * 0.33, H * 0.262), (W * 0.2, H * 0.3), (W * 0.1, H * 0.2), (W * 0.03, H * 0.285)], 13)
cable([(W * 0.67, H * 0.262), (W * 0.8, H * 0.3), (W * 0.9, H * 0.2), (W * 0.97, H * 0.285)], 13)
cable([(W * 0.04, H * 0.72), (W * 0.12, H * 0.8), (W * 0.2, H * 0.71), (W * 0.33, H * 0.76)], 11, (44, 26, 20))
cable([(W * 0.96, H * 0.72), (W * 0.88, H * 0.8), (W * 0.8, H * 0.71), (W * 0.67, H * 0.76)], 11, (44, 26, 20))
for cx, cy in ((W * 0.175, H * 0.262), (W * 0.825, H * 0.262), (W * 0.15, H * 0.75), (W * 0.85, H * 0.75)):
    clamp(cx, cy)

# ---- разделка и рёбра вокруг щели
sx0, sy0, sx1, sy1 = box(SLIT)
for i, c in enumerate(((10, 10, 11), (62, 48, 24), (120, 92, 44), (40, 32, 18), (6, 6, 7))):
    m = 28 - i * 6
    d.rounded_rectangle((sx0 - m, sy0 - m, sx1 + m, sy1 + m), radius=max(4, m), fill=(*c, 255))
for x in np.linspace(sx0 + 30, sx1 - 30, 18):
    rivet(x, sy0 - 15, 4)
    rivet(x, sy1 + 15, 4)
# ---- ниши приборов
for r in (LEFT, RIGHT, BOTTOM):
    x0, y0, x1, y1 = box(r)
    d.rounded_rectangle((x0 - 10, y0 - 10, x1 + 10, y1 + 10), radius=12, fill=(58, 44, 22, 255))
    d.rounded_rectangle((x0 - 5, y0 - 5, x1 + 5, y1 + 5), radius=9, fill=(12, 12, 13, 255))
    d.rounded_rectangle((x0, y0, x1, y1), radius=6, fill=(8, 10, 9, 255))

# ---- аквила над щелью
aquila(W // 2, int(H * 0.145), 0.72)

# ---- низ: таблички литании, предохранители, шестерня, печати
plaque(int(W * 0.04), int(H * 0.795), int(W * 0.2), int(H * 0.945), 6)
plaque(int(W * 0.8), int(H * 0.795), int(W * 0.96), int(H * 0.945), 6)
dial(int(W * 0.26), int(H * 0.87), 56, 0.48)
dial(int(W * 0.74), int(H * 0.87), 56, 0.2)
cog(int(W * 0.325), int(H * 0.915), 40)
cog(int(W * 0.675), int(H * 0.915), 40)
vent(int(W * 0.385), int(H * 0.895), int(W * 0.615), int(H * 0.955), 5)
seal(int(W * 0.345), int(H * 0.05), 22)
seal(int(W * 0.655), int(H * 0.05), 22)
seal(int(W * 0.145), int(H * 0.775), 24, 2)
seal(int(W * 0.855), int(H * 0.775), 24, 2)
# ---- полосы опасности у нижней кромки
for i in range(0, 700, 44):
    x = int(W * 0.5) - 350 + i
    d.polygon([(x, int(H * 0.96)), (x + 22, int(H * 0.96)), (x + 9, int(H * 0.99)), (x - 13, int(H * 0.99))], fill=(112, 84, 14, 255))

# ---- сама щель прозрачная, края слегка размыты тенью
a = Image.new("L", (W, H), 255)
ad = ImageDraw.Draw(a)
ad.rounded_rectangle((sx0, sy0, sx1, sy1), radius=8, fill=0)
a = a.filter(ImageFilter.GaussianBlur(2))
img.putalpha(a)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
img.save(OUT)
print("готово", os.path.getsize(OUT) // 1024, "КБ")
