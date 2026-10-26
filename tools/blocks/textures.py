"""
Процедурные текстуры блоков (32×32) и предметов (16×16) для набора блоков Warpbound.

Каждая функция получает rng и возвращает массив RGBA (h, w, 4) uint8. Кадры анимации — список массивов.
Стиль — как у моделей (tools/models/hd.py): плавный шум, фаска, грязь книзу, заклёпки.
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "models"))
import hd  # noqa: E402
from geo import mix, shade  # noqa: E402

N = 32


def canvas(color, rng, amp=8, cell=6, grain=5, n=N):
    reg = np.zeros((n, n, 4), np.uint8)
    hd._base(reg, color, "north", rng, amp=amp, cell=cell, grain=grain)
    return reg


def mul(reg, k):
    hd._mul(reg, k)


def rivet(reg, x, y, c):
    reg[y, x, :3] = shade(c, 1.5)
    reg[y + 1, x + 1, :3] = shade(c, 0.5)
    reg[y, x + 1, :3] = shade(c, 1.1)
    reg[y + 1, x, :3] = shade(c, 0.8)


def seam_h(reg, y, c):
    reg[y, :, :3] = shade(c, 0.55)
    if y + 1 < reg.shape[0]:
        reg[y + 1, :, :3] = shade(c, 1.15)


def seam_v(reg, x, c):
    reg[:, x, :3] = shade(c, 0.55)
    if x + 1 < reg.shape[1]:
        reg[:, x + 1, :3] = shade(c, 1.15)


def scratches(reg, rng, c, n=10):
    h, w = reg.shape[:2]
    for _ in range(n):
        x, y = rng.randrange(w), rng.randrange(h)
        for k in range(rng.randint(2, 5)):
            if 0 <= x + k < w:
                reg[y, x + k, :3] = shade(c, 1.3)


def stains(reg, rng, color, frac=0.12, cell=4):
    h, w = reg.shape[:2]
    n = hd.vnoise(h, w, cell, rng)
    m = n > 1 - frac * 2
    reg[m, :3] = (reg[m, :3].astype(np.float32) * 0.5 + np.array(color, np.float32) * 0.5).astype(np.uint8)


def paint_icon(n, draw, k=6):
    img = Image.new("RGBA", (n * k, n * k), (0, 0, 0, 0))
    draw(ImageDraw.Draw(img), n * k)
    return np.asarray(img.resize((n, n), Image.LANCZOS)).copy()


def over(reg, icon, th=90):
    m = icon[..., 3] > th
    reg[m, :3] = icon[m, :3]
    return reg


# ------------------------------------------------------------------ корабль, имперская обшивка

HULL = (82, 88, 100)


def hull_plating(rng, base=HULL, scorched=False):
    reg = canvas(base, rng, amp=7, cell=8)
    mul(reg, np.linspace(1.08, 0.9, N, dtype=np.float32)[:, None, None])
    seam_h(reg, 15, base)
    seam_v(reg, 0 if rng.random() < 0.5 else 15, base)
    for x, y in ((2, 2), (28, 2), (2, 12), (28, 12), (2, 18), (28, 18), (2, 28), (28, 28)):
        rivet(reg, x, y, base)
    scratches(reg, rng, base, 8)
    if scorched:
        stains(reg, rng, (20, 18, 16), 0.35, 5)
        for _ in range(6):  # тлеющие трещины
            x, y = rng.randrange(4, 28), rng.randrange(4, 28)
            for k in range(rng.randint(3, 7)):
                xx, yy = x + k, y + rng.randint(-1, 1)
                if 0 <= xx < N and 0 <= yy < N:
                    reg[yy, xx, :3] = (200, 90, 30) if rng.random() < 0.6 else (110, 40, 20)
    else:
        stains(reg, rng, (110, 70, 40), 0.06, 3)
    hd.bevel(reg, 1.18, 0.65)
    return reg


def plasteel_panel(rng, rivets=False, base=(150, 154, 160)):
    reg = canvas(base, rng, amp=4, cell=10, grain=3)
    mul(reg, np.linspace(1.06, 0.92, N, dtype=np.float32)[:, None, None])
    reg[2, 2:-2, :3] = shade(base, 0.7)
    reg[-3, 2:-2, :3] = shade(base, 1.2)
    reg[2:-2, 2, :3] = shade(base, 0.7)
    reg[2:-2, -3, :3] = shade(base, 1.2)
    if rivets:
        for i in range(5, 28, 5):
            for x, y in ((i, 4), (i, 26), (4, i), (26, i)):
                rivet(reg, x, y, base)
        reg[15, 6:26, :3] = shade(base, 0.75)
        reg[16, 6:26, :3] = shade(base, 1.15)
    scratches(reg, rng, base, 6)
    hd.bevel(reg, 1.2, 0.62)
    return reg


def hazard_panel(rng):
    reg = plasteel_panel(rng, base=(120, 124, 130))
    for y in range(9, 23):
        for x in range(N):
            stripe = ((x + y) // 5) % 2 == 0
            reg[y, x, :3] = shade((206, 160, 30), 0.9 + rng.random() * 0.15) if stripe else (28, 26, 24)
    reg[8, :, :3] = (40, 40, 44)
    reg[23, :, :3] = (40, 40, 44)
    stains(reg, rng, (60, 50, 40), 0.1, 3)  # потёртости
    hd.bevel(reg, 1.15, 0.65)
    return reg


def plasteel_vent(rng):
    reg = plasteel_panel(rng, base=(110, 114, 122))
    for y in range(6, 27, 3):
        reg[y, 5:27, :3] = (14, 14, 16)
        reg[y + 1, 5:27, :3] = shade((110, 114, 122), 1.35)
    reg[5, 5:27, :3] = (30, 30, 34)
    return reg


def deck_grating(rng):
    base = (96, 100, 108)
    reg = canvas(base, rng, amp=6, cell=4)
    reg[..., 3] = 0
    for i in range(0, N, 8):  # несущие рёбра
        reg[i:i + 2, :, 3] = 255
        reg[:, i:i + 2, 3] = 255
        reg[i, :, :3] = shade(base, 1.25)
        reg[:, i, :3] = shade(base, 1.25)
        reg[i + 1, :, :3] = shade(base, 0.75)
    for i in range(4, N, 8):  # тонкая сетка
        reg[i, :, 3] = 255
        reg[:, i, 3] = 255
    stains(reg, rng, (90, 60, 40), 0.08, 3)
    return reg


def brass_trim(rng):
    base = (190, 148, 60)
    reg = canvas(base, rng, amp=8, cell=4)
    for y in (3, 13, 18, 28):
        seam_h(reg, y, base)
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    mul(reg, (1 + np.clip(1 - np.abs(xx / N - yy / N) * 2.5, 0, 1) * 0.22)[..., None])
    stains(reg, rng, (70, 110, 80), 0.08, 3)  # патина
    for x in range(4, N, 8):
        rivet(reg, x, 15, base)
    hd.bevel(reg, 1.35, 0.55)
    return reg


def dock_girder(rng, top=False):
    base = (60, 62, 68)
    reg = canvas(base, rng, amp=6, cell=6)
    if top:
        reg[...] = (36, 36, 40, 255)
        reg[2:-2, 13:19, :3] = shade(base, 1.0)
        reg[2:6, 2:-2, :3] = shade(base, 1.1)
        reg[-6:-2, 2:-2, :3] = shade(base, 1.1)
        hd.bevel(reg)
        return reg
    # двутавр с облегчающими отверстиями
    reg[:4, :, :3] = shade(base, 1.2)
    reg[-4:, :, :3] = shade(base, 0.9)
    for cx in (8, 24):
        for y in range(9, 23):
            for x in range(N):
                if (x - cx) ** 2 / 25 + (y - 16) ** 2 / 36 < 1:
                    reg[y, x, :3] = (18, 18, 20)
                elif (x - cx) ** 2 / 36 + (y - 16) ** 2 / 49 < 1:
                    reg[y, x, :3] = shade(base, 1.25)
    stains(reg, rng, (120, 60, 30), 0.12, 3)
    hd.bevel(reg)
    return reg


def hull_scrap(rng):
    """Груда лома: перекошенные листы обшивки, ржавчина, тёмные щели."""
    reg = np.zeros((N, N, 4), np.uint8)
    reg[..., :3] = (22, 20, 20)
    reg[..., 3] = 255
    cols = [HULL, (60, 62, 68), (120, 70, 40), (150, 154, 160), (40, 36, 34)]
    for _ in range(14):
        img = Image.new("RGBA", (N * 4, N * 4), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        cx, cy = rng.uniform(0, N * 4), rng.uniform(0, N * 4)
        w, h = rng.uniform(20, 70), rng.uniform(10, 34)
        a = rng.uniform(0, math.pi)
        pts = [(cx + math.cos(a) * dx - math.sin(a) * dy, cy + math.sin(a) * dx + math.cos(a) * dy)
               for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
        c = cols[rng.randrange(len(cols))]
        d.polygon(pts, fill=c + (255,), outline=shade(c, 0.4) + (255,))
        piece = np.asarray(img.resize((N, N), Image.LANCZOS))
        m = piece[..., 3] > 100
        noise = (np.random.default_rng(rng.randrange(1 << 30)).random((N, N)) - 0.5) * 18
        reg[m, :3] = np.clip(piece[m, :3].astype(np.float32) + noise[m][:, None], 0, 255).astype(np.uint8)
    stains(reg, rng, (130, 66, 30), 0.15, 3)
    hd.bevel(reg, 1.1, 0.7)
    return reg


def cogitator_frames(rng, n=8):
    """Лицевая панель когитатора: экран бинарика бежит вверх, лампы мигают — кадры для .mcmeta."""
    base = (52, 54, 60)
    panel = canvas(base, rng, amp=5, cell=6)
    panel[3:15, 4:28, :3] = (8, 18, 10)
    panel[2, 3:29, :3] = shade(base, 0.5)
    panel[15, 3:29, :3] = shade(base, 1.3)
    for y in range(19, 29, 3):
        for x in range(4, 28, 3):
            panel[y:y + 2, x:x + 2, :3] = (30, 30, 30)
    for x in (2, 29):
        panel[:, x, :3] = (170, 130, 50)
    lines = [[rng.random() < 0.7 for _ in range(12)] for _ in range(24)]
    lamps = [(x, y) for y in range(19, 29, 3) for x in range(4, 28, 3)]
    states = [[rng.random() < 0.4 for _ in lamps] for _ in range(n)]
    frames = []
    for f in range(n):
        reg = panel.copy()
        for row in range(4):
            line = lines[(row + f) % len(lines)]
            y = 4 + row * 3
            for i, on in enumerate(line):
                if on:
                    reg[y, 5 + i * 2:6 + i * 2, :3] = (110, 255, 140)
        for (x, y), on in zip(lamps, states[f]):
            if on:
                c = (255, 170, 40) if (x + y) % 2 else (110, 255, 140)
                reg[y:y + 2, x:x + 2, :3] = c
        hd.bevel(reg, 1.15, 0.65)
        frames.append(reg)
    return frames


def cogitator_side(rng):
    reg = plasteel_panel(rng, base=(52, 54, 60))
    for y in range(6, 27, 4):
        reg[y, 6:26, :3] = (24, 24, 28)
    return reg


def vox_grille(rng):
    base = (52, 54, 60)
    reg = canvas(base, rng, amp=5, cell=6)
    for y in range(N):
        for x in range(N):
            d = math.hypot(x - 15.5, y - 15.5)
            if d < 13 and (x % 3 == 0 and y % 3 == 0):
                reg[y, x, :3] = (8, 8, 10)
            if 13 <= d < 15:
                reg[y, x, :3] = shade((190, 148, 60), 1.0 - (d - 13) * 0.2)
    for x, y in ((3, 3), (27, 3), (3, 27), (27, 27)):
        rivet(reg, x, y, base)
    hd.bevel(reg)
    return reg


# ------------------------------------------------------------------ камень, руды, Кинерис

STONE = (118, 116, 112)
DEEPSLATE = (70, 70, 76)
ASH_STONE = (84, 82, 80)


def stone(rng, base=STONE, cracks=6):
    reg = canvas(base, rng, amp=14, cell=5, grain=9)
    n2 = hd.vnoise(N, N, 9, rng)
    mul(reg, (0.92 + 0.12 * n2)[..., None])
    for _ in range(cracks):
        x, y = rng.randrange(N), rng.randrange(N)
        for _ in range(rng.randint(4, 9)):
            if 0 <= x < N and 0 <= y < N:
                reg[y, x, :3] = shade(base, 0.6)
            x += rng.choice((-1, 0, 1))
            y += rng.choice((0, 1))
    return reg


def ore(rng, base, chunk, glint, n=6, glow=False):
    reg = stone(rng, base)
    for _ in range(n):
        cx, cy = rng.randrange(4, 28), rng.randrange(4, 28)
        r = rng.uniform(1.6, 3.2)
        for y in range(N):
            for x in range(N):
                d = math.hypot((x - cx) * 1.1, y - cy)
                if d < r + rng.random() * 0.6:
                    k = 1 - d / (r + 1)
                    reg[y, x, :3] = mix(chunk, glint, max(0, k - 0.2))
                    if d < r * 0.35:
                        reg[y, x, :3] = shade(glint, 1.2 if glow else 1.0)
    return reg


def ash_stone_bricks(rng):
    reg = stone(rng, ASH_STONE, 2)
    mortar = shade(ASH_STONE, 0.5)
    for y in (0, 8, 16, 24):
        reg[y, :, :3] = mortar
        off = (y // 8 % 2) * 8
        for x in range(off, N + off, 16):
            reg[y:y + 8, x % N, :3] = mortar
    for y in range(N):  # скол и пепел в щелях
        for x in range(N):
            if (reg[y, x, :3] == mortar).all() and rng.random() < 0.3:
                reg[y, x, :3] = (150, 146, 140)
    hd.bevel(reg, 1.1, 0.75)
    return reg


def ash(rng):
    reg = canvas((128, 124, 120), rng, amp=12, cell=3, grain=14)
    for _ in range(40):
        x, y = rng.randrange(N), rng.randrange(N)
        reg[y, x, :3] = (40, 38, 36) if rng.random() < 0.5 else (178, 172, 166)
    return reg


def ash_clay(rng):
    reg = canvas((150, 148, 146), rng, amp=7, cell=7, grain=4)
    stains(reg, rng, (120, 116, 112), 0.15, 6)
    return reg


def vitrified(rng, tint):
    reg = np.zeros((N, N, 4), np.uint8)
    n = hd.vnoise(N, N, 6, rng)
    reg[..., :3] = np.clip(np.array(tint, np.float32)[None, None] * (0.85 + 0.25 * n[..., None]), 0, 255).astype(np.uint8)
    reg[..., 3] = (150 + 50 * n).clip(110, 220).astype(np.uint8)
    for _ in range(5):  # трещины остекления
        x, y = rng.randrange(N), rng.randrange(N)
        for _ in range(rng.randint(6, 14)):
            if 0 <= x < N and 0 <= y < N:
                reg[y, x, :3] = shade(tint, 1.6)
                reg[y, x, 3] = 235
            x += rng.choice((-1, 0, 1))
            y += rng.choice((-1, 1))
    reg[0, :, 3] = reg[-1, :, 3] = reg[:, 0, 3] = reg[:, -1, 3] = 240
    reg[0, :, :3] = reg[:, 0, :3] = shade(tint, 1.5)
    return reg


def charred_bark(rng):
    reg = canvas((34, 30, 28), rng, amp=8, cell=3, grain=6)
    for x in range(0, N, 4):
        off = rng.randint(0, 3)
        reg[:, (x + off) % N, :3] = (14, 12, 12)
    for _ in range(5):  # тлеющие трещины
        x, y = rng.randrange(N), rng.randrange(N - 6)
        for k in range(rng.randint(3, 6)):
            reg[y + k, x, :3] = (190, 80, 30) if rng.random() < 0.5 else (120, 40, 20)
    return reg


def charred_top(rng):
    reg = canvas((48, 40, 34), rng, amp=6, cell=4)
    for y in range(N):
        for x in range(N):
            d = math.hypot(x - 15.5, y - 15.5)
            if int(d) % 3 == 0:
                reg[y, x, :3] = shade((48, 40, 34), 0.6)
            if d > 13:
                reg[y, x, :3] = (22, 18, 16)
    return reg


def lead_block(rng):
    base = (92, 98, 112)
    reg = canvas(base, rng, amp=6, cell=8)
    seam_h(reg, 15, base)
    seam_v(reg, 15, base)
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    mul(reg, (1 + np.clip(1 - np.abs(xx / N - yy / N + 0.2) * 3, 0, 1) * 0.15)[..., None])
    hd.bevel(reg, 1.25, 0.6)
    return reg


def crystal_cross(rng, c1, c2):
    """Спрайт друзы псайкристаллов для крестовой модели: острия веером снизу."""
    def draw(d, W):
        for i in range(5):
            x = W * (0.2 + i * 0.15)
            h = W * (0.45 + 0.4 * rng.random())
            w = W * 0.07
            lean = (rng.random() - 0.5) * W * 0.15
            d.polygon([(x - w, W), (x + lean, W - h), (x + w, W)], fill=c1 + (255,))
            d.polygon([(x, W), (x + lean, W - h), (x + w, W)], fill=c2 + (255,))
    return paint_icon(N, draw, k=6)


def bones(rng):
    """Спрайт груды костей для модели-«ковра»: череп, рёбра, кости вразброс сверху."""
    def draw(d, W):
        bone = (206, 196, 168, 255)
        dark = (120, 110, 90, 255)
        for _ in range(9):
            x, y = rng.uniform(0.1, 0.9) * W, rng.uniform(0.1, 0.9) * W
            a = rng.uniform(0, math.pi)
            ln = W * rng.uniform(0.15, 0.3)
            x1, y1 = x + math.cos(a) * ln, y + math.sin(a) * ln
            d.line([(x, y), (x1, y1)], fill=bone, width=int(W * 0.05))
            for px, py in ((x, y), (x1, y1)):
                d.ellipse([px - W * 0.035, py - W * 0.035, px + W * 0.035, py + W * 0.035], fill=bone)
        cx, cy = W * 0.5, W * 0.45  # череп
        d.ellipse([cx - W * 0.13, cy - W * 0.13, cx + W * 0.13, cy + W * 0.11], fill=bone)
        d.rectangle([cx - W * 0.07, cy + W * 0.05, cx + W * 0.07, cy + W * 0.15], fill=bone)
        for ex in (-1, 1):
            d.ellipse([cx + ex * W * 0.05 - W * 0.03, cy - W * 0.03, cx + ex * W * 0.05 + W * 0.03, cy + W * 0.03], fill=dark)
    return paint_icon(N, draw, k=6)


# ------------------------------------------------------------------ предметы 16×16

def item(draw):
    return paint_icon(16, draw, k=8)


def nugget_icon(c, hi, rng):
    def draw(d, W):
        pts = [(W * (0.5 + 0.38 * math.cos(a)) + rng.uniform(-1, 1) * W * 0.06,
                W * (0.55 + 0.32 * math.sin(a)) + rng.uniform(-1, 1) * W * 0.06) for a in np.linspace(0, 2 * math.pi, 9)[:-1]]
        d.polygon(pts, fill=c + (255,), outline=shade(c, 0.5) + (255,))
        d.polygon([(W * 0.35, W * 0.35), (W * 0.55, W * 0.3), (W * 0.48, W * 0.48)], fill=hi + (255,))
    return item(draw)


def ingot_icon(c):
    def draw(d, W):
        d.polygon([(W * 0.1, W * 0.62), (W * 0.32, W * 0.38), (W * 0.9, W * 0.38), (W * 0.7, W * 0.62)], fill=shade(c, 1.25) + (255,))
        d.polygon([(W * 0.1, W * 0.62), (W * 0.7, W * 0.62), (W * 0.7, W * 0.78), (W * 0.1, W * 0.78)], fill=c + (255,))
        d.polygon([(W * 0.7, W * 0.62), (W * 0.9, W * 0.38), (W * 0.9, W * 0.54), (W * 0.7, W * 0.78)], fill=shade(c, 0.7) + (255,))
    return item(draw)


def shard_icon(c, hi):
    def draw(d, W):
        d.polygon([(W * 0.45, W * 0.05), (W * 0.75, W * 0.45), (W * 0.55, W * 0.95), (W * 0.25, W * 0.55)], fill=c + (255,))
        d.polygon([(W * 0.45, W * 0.05), (W * 0.55, W * 0.95), (W * 0.25, W * 0.55)], fill=hi + (255,))
    return item(draw)


# ------------------------------------------------------------------ отсеки крейсера: реактор, охладитель, Поле Геллера

def radiation_sign(rng):
    reg = canvas((214, 176, 36), rng, amp=6, cell=6)
    reg[:2, :, :3] = reg[-2:, :, :3] = reg[:, :2, :3] = reg[:, -2:, :3] = (24, 22, 20)
    inner = reg[3:-3, 3:-3]

    def draw(d, W):
        cx = cy = W / 2
        r2 = W * 0.44
        for k in range(3):
            a0 = -90 + k * 120 - 30
            d.pieslice([cx - r2, cy - r2, cx + r2, cy + r2], a0, a0 + 60, fill=(24, 22, 20, 255))
        r1 = W * 0.1
        d.ellipse([cx - r1 * 1.7, cy - r1 * 1.7, cx + r1 * 1.7, cy + r1 * 1.7], fill=(214, 176, 36, 255))
        d.ellipse([cx - r1, cy - r1, cx + r1, cy + r1], fill=(24, 22, 20, 255))
    icon = paint_icon(inner.shape[0], draw, k=8)
    m = icon[..., 3] > 100
    inner[m, :3] = icon[m, :3]
    stains(reg, rng, (110, 80, 40), 0.08, 3)
    hd.bevel(reg, 1.15, 0.7)
    return reg


def coolant_pipe(rng):
    """Труба охладителя: зеленовато-серая, поперечные хомуты, конденсат."""
    base = (92, 108, 100)
    reg = canvas(base, rng, amp=5, cell=6)
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    mul(reg, (0.7 + 0.45 * np.sin(xx / (N - 1) * np.pi))[..., None])        # цилиндрический блик
    for y in (3, 4, 27, 28):
        reg[y, :, :3] = shade((60, 62, 66), 1.1 if y in (3, 27) else 0.7)
    for x in range(2, N, 6):
        rivet(reg, x, 3, (60, 62, 66))
    reg[14:18, 12:20, :3] = (170, 40, 30)                                      # красный вентиль-метка
    reg[15:17, 13:19, :3] = (220, 70, 50)
    for _ in range(6):                                                          # капли конденсата
        x, y = rng.randrange(N), rng.randrange(6, 26)
        reg[y:y + 2, x, :3] = shade(base, 1.5)
    return reg


def coolant_pipe_end(rng):
    reg = canvas((60, 62, 66), rng, amp=4, cell=4)
    for y in range(N):
        for x in range(N):
            d = math.hypot(x - 15.5, y - 15.5)
            if d < 9:
                reg[y, x, :3] = (40, 90, 110) if d < 7 else (120, 124, 130)
    hd.bevel(reg)
    return reg


def geller_conduit(rng):
    """Проводник Поля Геллера: тёмный кожух, по центру — светящийся синий канал с рунами-насечками."""
    reg = canvas((40, 42, 52), rng, amp=5, cell=6)
    reg[:, 11:21, :3] = (20, 24, 40)
    for x in range(12, 20):
        k = 1 - abs(x - 15.5) / 4.5
        reg[:, x, :3] = mix((40, 90, 200), (190, 235, 255), k)
    for y in range(2, N, 6):
        reg[y:y + 2, 11:21, :3] = (186, 146, 54)                               # латунные кольца
        reg[y + 3, 14:18, :3] = (230, 250, 255)                                # руна-насечка
    for x in (8, 23):
        reg[:, x, :3] = (186, 146, 54)
    hd.bevel(reg, 1.2, 0.6)
    return reg


def geller_conduit_end(rng):
    reg = canvas((40, 42, 52), rng, amp=4, cell=4)
    for y in range(N):
        for x in range(N):
            d = math.hypot(x - 15.5, y - 15.5)
            if d < 6:
                reg[y, x, :3] = mix((190, 235, 255), (40, 90, 200), d / 6)
            elif d < 8:
                reg[y, x, :3] = (186, 146, 54)
    return reg


def effect_icon():
    """Иконка эффекта «Радиация» 18×18."""
    img = Image.new("RGBA", (18 * 8, 18 * 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    W = 18 * 8
    d.ellipse([4, 4, W - 4, W - 4], fill=(214, 176, 36, 255), outline=(30, 26, 20, 255), width=8)
    cx = cy = W / 2
    r2 = W * 0.38
    for k in range(3):
        a0 = -90 + k * 120 - 30
        d.pieslice([cx - r2, cy - r2, cx + r2, cy + r2], a0, a0 + 60, fill=(24, 22, 20, 255))
    d.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=(214, 176, 36, 255))
    d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(24, 22, 20, 255))
    return np.asarray(img.resize((18, 18), Image.LANCZOS))


def bulkhead(rng, stripe=((206, 160, 30), (28, 26, 24))):
    """Гермодверь: тяжёлая плита, шов створок посередине, полосы по кромкам, заклёпки, глазок."""
    base = (96, 100, 108)
    reg = canvas(base, rng, amp=5, cell=8)
    for y in range(N):
        for x in list(range(0, 4)) + list(range(N - 4, N)):
            reg[y, x, :3] = stripe[0] if ((x + y) // 3) % 2 == 0 else stripe[1]
    reg[:, 15, :3] = (20, 20, 22)
    reg[:, 16, :3] = shade(base, 1.3)
    for y in (6, 25):
        reg[y:y + 2, 5:27, :3] = shade(base, 0.6)
    for x, y in ((6, 3), (24, 3), (6, 28), (24, 28), (10, 15), (21, 15)):
        rivet(reg, x, y, base)
    reg[11:14, 12:20, :3] = (30, 60, 40)                  # смотровая щель
    reg[11, 12:20, :3] = (90, 160, 110)
    stains(reg, rng, (90, 60, 40), 0.06, 3)
    hd.bevel(reg, 1.2, 0.6)
    return reg
