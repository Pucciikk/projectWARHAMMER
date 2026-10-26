#!/usr/bin/env python3
"""
Фон экрана командного пульта мостика (когитатор): латунная рама с шестернями по углам,
череп-аквила сверху, тёмно-зелёный экран с развёрткой и сеткой.

    python3 tools/textures/gen_console_gui.py

Пишет assets/warpbound/textures/gui/command_console.png (320×208, рисуется 1:1 в ConsoleScreen).
"""
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "src/main/resources/assets/warpbound/textures/gui/command_console.png")
W, H = 320, 208
K = 4  # рисуем крупно и сжимаем — ровные края

BRASS = (176, 138, 60)
BRASS_HI = (232, 196, 110)
BRASS_LO = (96, 70, 30)
IRON = (46, 44, 46)
SCREEN = (8, 20, 12)


def cog(d, cx, cy, r, teeth=10, fill=BRASS, hole=IRON):
    pts = []
    for i in range(teeth * 4):
        a = i * math.pi * 2 / (teeth * 4)
        rr = r if (i % 4) in (0, 1) else r * 0.8
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    d.polygon(pts, fill=fill + (255,), outline=BRASS_LO + (255,))
    d.ellipse([cx - r * 0.35, cy - r * 0.35, cx + r * 0.35, cy + r * 0.35], fill=hole + (255,))


def main():
    rng = random.Random(4)
    img = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = K
    # железная подложка и латунная рама в два канта
    d.rounded_rectangle([0, 0, W * s - 1, H * s - 1], radius=10 * s, fill=IRON + (255,))
    d.rounded_rectangle([3 * s, 3 * s, (W - 3) * s, (H - 3) * s], radius=8 * s, outline=BRASS + (255,), width=3 * s)
    d.rounded_rectangle([7 * s, 7 * s, (W - 7) * s, (H - 7) * s], radius=6 * s, outline=BRASS_LO + (255,), width=s)
    # экран
    d.rectangle([10 * s, 34 * s, (W - 10) * s, (H - 10) * s], fill=SCREEN + (255,))
    # полоса вкладок
    d.rectangle([10 * s, 12 * s, (W - 10) * s, 31 * s], fill=(24, 22, 22, 255))
    # заклёпки по раме
    for x in range(16, W - 12, 24):
        for y in (5, H - 6):
            d.ellipse([(x - 1.2) * s, (y - 1.2) * s, (x + 1.2) * s, (y + 1.2) * s], fill=BRASS_HI + (255,))
    # шестерни по углам
    for cx, cy in ((10, 10), (W - 10, 10), (10, H - 10), (W - 10, H - 10)):
        cog(d, cx * s, cy * s, 9 * s)
    # череп в шестерне сверху по центру
    cx, cy = W / 2 * s, 4 * s
    cog(d, cx, cy + 6 * s, 9 * s, teeth=12)
    d.ellipse([cx - 4.2 * s, cy + 1.5 * s, cx + 4.2 * s, cy + 9.5 * s], fill=(214, 204, 176, 255))
    for ex in (-1.6, 1.6):
        d.ellipse([cx + (ex - 1.1) * s, cy + 4 * s, cx + (ex + 1.1) * s, cy + 6.2 * s], fill=(20, 16, 14, 255))
    small = img.resize((W, H), Image.LANCZOS)
    a = np.asarray(small).astype(np.float32)
    # развёртка и сетка экрана, шум латуни
    yy, xx = np.mgrid[0:H, 0:W]
    screen = (xx >= 11) & (xx <= W - 11) & (yy >= 35) & (yy <= H - 11)
    a[screen & (yy % 2 == 0), :3] *= 0.82
    grid = screen & ((xx - 11) % 16 == 0) | screen & ((yy - 35) % 16 == 0)
    a[grid, 1] += 10
    a[grid, :3] += 4
    noise = np.random.default_rng(3).random((H, W)) * 14 - 7
    brass = (a[..., 0] > 120) & (a[..., 2] < 120)
    a[brass, :3] += noise[brass, None]
    # мягкое свечение экрана к краям темнее
    vign = 1 - 0.35 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - (H + 25) / 2) / (H / 2)) ** 2)
    a[screen, :3] *= np.clip(vign[screen], 0.6, 1)[:, None]
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out.save(OUT)
    print(os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
