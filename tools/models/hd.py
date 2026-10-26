"""
Материалы высокой детализации (S = 4, 64 px на блок) для конструктора geo.py.

Плавный шум вместо попиксельного, фаска по краю (свет сверху-слева), грязь книзу, вышивка по кромке.
Имена начинаются с "hd_"; импорт модуля регистрирует их в geo.MATERIALS.
"""
import math

import numpy as np
from PIL import Image

from geo import MATERIALS, cog, face_light, mat_glow, shade


def vnoise(h, w, cell, rng):
    """Плавный шум [-1, 1]: случайная сетка, растянутая бикубически."""
    gh, gw = max(2, int(h / cell) + 2), max(2, int(w / cell) + 2)
    grid = np.array([[rng.random() for _ in range(gw)] for _ in range(gh)], np.float32)
    img = Image.fromarray((grid * 255).astype(np.uint8), "L").resize((w + int(cell) + 1, h + int(cell) + 1),
                                                                      Image.BICUBIC)
    return np.asarray(img, np.float32)[:h, :w] / 127.5 - 1


def streaks(h, w, rng):
    """Вертикальные складки [-1, 1]: 3 ряда узлов по высоте, узел на ~6 px по ширине."""
    gw = max(3, w // 5 + 2)
    grid = np.array([[rng.random() for _ in range(gw)] for _ in range(2)], np.float32)
    img = Image.fromarray((grid * 255).astype(np.uint8), "L").resize((w, h), Image.BICUBIC)
    a = np.asarray(img, np.float32) / 127.5 - 1
    # гребни складок: светлая кромка там, где шум пересекает ноль, тень — в глубине
    ridge = 1 - 2 * np.abs(np.clip(a * 1.4, -1, 1))
    return np.clip(ridge * 0.7 + a * 0.5, -1, 1)


def _base(region, color, face, rng, amp=10, cell=6, grain=4):
    h, w = region.shape[:2]
    c = np.array(shade(color, face_light(face)), np.float32)
    fine = np.random.default_rng(rng.randrange(1 << 30)).random((h, w)) - 0.5
    n = vnoise(h, w, cell, rng) * amp + fine * grain
    region[..., :3] = np.clip(c[None, None, :] + n[..., None], 0, 255).astype(np.uint8)
    region[..., 3] = 255
    return h, w


def _mul(region, k):
    region[..., :3] = np.clip(region[..., :3].astype(np.float32) * k, 0, 255).astype(np.uint8)


def bevel(region, k_hi=1.25, k_lo=0.65, wdt=1):
    """Фаска: светлая кромка сверху и слева, тёмная снизу и справа."""
    h, w = region.shape[:2]
    if h < 3 or w < 3:
        return
    _mul(region[:wdt, :], k_hi)
    _mul(region[wdt:, :wdt], (k_hi + 1) / 2)
    _mul(region[-wdt:, wdt:], k_lo)
    _mul(region[wdt:-wdt, -wdt:], (k_lo + 1) / 2)


def grime(region, strength=0.35, frac=0.3):
    """Грязь и копоть у нижней кромки грани."""
    h = region.shape[0]
    n = max(1, int(h * frac))
    for i in range(n):
        _mul(region[h - 1 - i:h - i], 1 - strength * (1 - i / n) ** 1.6)


def hd_cloth(key, hem=None, folds=True, dirty=True):
    def f(region, face, pal, rng):
        h, w = _base(region, pal[key], face, rng, amp=9, cell=5, grain=5)
        if folds and face not in ("up", "down"):
            # складки: шум, вытянутый вдоль ткани, — неровные, сходятся и расходятся книзу
            streak = streaks(h, w, rng)
            _mul(region, (0.86 + 0.16 * streak)[..., None])
        if dirty and face not in ("up", "down"):
            grime(region, 0.4, 0.25)
        if hem and face not in ("up", "down") and h >= 12:
            t = max(4, h // 10)
            band = region[h - t - 2:h - 2]
            band[..., :3] = shade(pal[hem], face_light(face))
            band[0, :, :3] = shade(pal[hem], 1.35)
            band[-1, :, :3] = shade(pal[hem], 0.6)
            for cx in range(t, w - t // 2, t * 2):  # вышитые шестерни по кромке
                cog(band, cx, t / 2 - 0.5, t * 0.34, shade(pal[hem], 0.55))
        if pal.get("chaos") and face not in ("up", "down") and h >= 12:
            # рваный подол: прорехи по нижнему краю (рендер GeckoLib — cutout, прозрачность работает)
            x = 0
            while x < w:
                ln, dp = rng.randint(1, 3), rng.randint(1, 3)
                if rng.random() < 0.45:
                    region[h - dp:, x:x + ln, 3] = 0
                x += ln + rng.randint(1, 3)
    return f


def hd_metal(key, rivets=True, panels=True, rust=0.0):
    def f(region, face, pal, rng):
        h, w = _base(region, pal[key], face, rng, amp=7, cell=8, grain=6)
        _mul(region, np.linspace(1.08, 0.88, h, dtype=np.float32)[:, None, None])  # сверху светлее
        c = shade(pal[key], face_light(face))
        if panels and w >= 20 and h >= 20:
            x = w // 2
            region[2:-2, x, :3] = shade(c, 0.55)
            region[2:-2, x + 1, :3] = shade(c, 1.2)
        if rivets and w >= 8 and h >= 8:
            for (x, y) in ((2, 2), (w - 4, 2), (2, h - 4), (w - 4, h - 4)):
                region[y:y + 2, x:x + 2, :3] = shade(c, 1.45)
                region[y + 2, x:x + 2, :3] = shade(c, 0.5)
        for _ in range(w * h // 90):  # царапины
            x, y = rng.randrange(w), rng.randrange(h)
            region[y, x:x + rng.randint(2, 5), :3] = shade(c, 1.3)
        r = rust or (0.22 if pal.get("chaos") else 0.0)  # у Хаоса металл ржавеет
        if r:
            n = vnoise(h, w, 4, rng)
            m = n > (1 - r * 2)
            region[m, :3] = np.array(shade(pal.get("rust", (120, 62, 32)), face_light(face)), np.uint8)
        bevel(region)
    return f


def hd_brass(key="brass"):
    def f(region, face, pal, rng):
        h, w = _base(region, pal[key], face, rng, amp=8, cell=4, grain=4)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        hl = np.clip(1 - np.abs((xx / max(1, w) - yy / max(1, h)) * 2.2), 0, 1) * 0.25  # блик полировки
        _mul(region, 1 + hl[..., None])
        n = vnoise(h, w, 3, rng)
        _mul(region, np.where(n > 0.55, 0.72, 1.0)[..., None])  # патина в углублениях
        bevel(region, 1.4, 0.55)
    return f


def hd_leather(key="leather"):
    def f(region, face, pal, rng):
        h, w = _base(region, pal[key], face, rng, amp=12, cell=3, grain=6)
        for _ in range(max(1, w * h // 60)):  # заломы
            x, y = rng.randrange(w), rng.randrange(h)
            region[y, x:x + rng.randint(2, 4), :3] = shade(pal[key], 0.6)
        if h > 5 and w > 5:  # строчка по краю
            region[1, 1:-1:2, :3] = shade(pal[key], 1.4)
            region[-2, 1:-1:2, :3] = shade(pal[key], 1.4)
        bevel(region, 1.2, 0.6)
    return f


def hd_cable(key="cable"):
    def f(region, face, pal, rng):
        h, w = _base(region, pal[key], face, rng, amp=4, cell=2, grain=4)
        c = shade(pal[key], face_light(face))
        if h >= w:
            region[::3, :, :3] = shade(c, 1.7)
        else:
            region[:, ::3, :3] = shade(c, 1.7)
    return f


def hd_flat(key, amp=5, edge=True):
    def f(region, face, pal, rng):
        _base(region, pal[key], face, rng, amp=amp, cell=4, grain=4)
        if edge:
            bevel(region)
    return f


def hd_parchment(region, face, pal, rng):
    """Лента печати чистоты: пергамент со строками литании."""
    h, w = _base(region, pal["parchment"], face, rng, amp=6, cell=3, grain=6)
    for y in range(2, h - 1, 3):
        for x in range(1, w - 1):
            if rng.random() < 0.7:
                region[y, x, :3] = (70, 50, 40)
    grime(region, 0.25, 0.3)


def hd_wax(region, face, pal, rng):
    h, w = _base(region, pal["wax"], face, rng, amp=6, cell=2, grain=3)
    cy, cx = (h - 1) / 2, (w - 1) / 2
    for y in range(h):
        for x in range(w):
            if math.hypot(x - cx, y - cy) < min(h, w) * 0.25:
                region[y, x, :3] = shade(pal["wax"], 0.65)
    region[1, 1:3, :3] = shade(pal["wax"], 1.6)


def hd_inner(region, face, pal, rng):
    """Чёрный поддоспешник: рубчик и блеск."""
    _base(region, pal["inner"], face, rng, amp=4, cell=3, grain=3)
    region[::2, :, :3] = shade(pal["inner"], 0.75)
    bevel(region, 1.5, 0.7)


def hd_bone(region, face, pal, rng):
    _base(region, pal["bone"], face, rng, amp=10, cell=3, grain=6)
    grime(region, 0.3, 0.5)
    bevel(region, 1.15, 0.6)


MATERIALS.update({
    "hd_robe": hd_cloth("robe", hem="trim"),
    "hd_robe_plain": hd_cloth("robe"),
    "hd_robe_clean": hd_cloth("robe", dirty=False),
    "hd_robe_in": hd_cloth("robe_in", folds=False, dirty=False),
    "hd_metal": hd_metal("metal"),
    "hd_metal_plain": hd_metal("metal", rivets=False, panels=False),
    "hd_dark": hd_metal("dark"),
    "hd_dark_plain": hd_metal("dark", rivets=False, panels=False),
    "hd_rusty": hd_metal("dark", rust=0.25),
    "hd_mask": hd_metal("mask", panels=False),
    "hd_brass": hd_brass(),
    "hd_leather": hd_leather(),
    "hd_cable": hd_cable(),
    "hd_parchment": hd_parchment,
    "hd_wax": hd_wax,
    "hd_inner": hd_inner,
    "hd_bone": hd_bone,
    "hd_glow": mat_glow("glow"),
    "hd_glow2": mat_glow("glow2"),
    "hd_screen": hd_flat("screen", 3, edge=False),
})


# ------------------------------------------------------------------ материалы машин (S = 2, 32 px на блок)

def hd_brick(key="brick"):
    """Шамотный кирпич: ряды со смещением, швы, копоть книзу и сколы."""
    def f(region, face, pal, rng):
        h, w = _base(region, pal[key], face, rng, amp=12, cell=3, grain=8)
        bh, bw = 4, 8
        mortar = shade(pal.get("mortar", (70, 64, 60)), face_light(face))
        for y in range(0, h, bh):
            region[y, :, :3] = mortar
            off = (y // bh % 2) * (bw // 2)
            for x in range(off, w, bw):
                region[y:y + bh, x, :3] = mortar
            # каждый кирпич — свой оттенок
            for x0 in range(off - bw, w, bw):
                k = 0.85 + rng.random() * 0.3
                xa, xb = max(0, x0 + 1), min(w, x0 + bw)
                if xb > xa:
                    _mul(region[y + 1:y + bh, xa:xb], k)
        if face not in ("up", "down"):
            grime(region, 0.45, 0.35)
    return f


def hd_stone(key="stone"):
    def f(region, face, pal, rng):
        h, w = _base(region, pal[key], face, rng, amp=14, cell=5, grain=8)
        for _ in range(max(1, w * h // 200)):  # трещины
            x, y = rng.randrange(w), rng.randrange(h)
            for _ in range(rng.randint(3, 8)):
                if 0 <= x < w and 0 <= y < h:
                    region[y, x, :3] = shade(pal[key], 0.55)
                x += rng.choice((-1, 0, 1))
                y += rng.choice((0, 1))
        bevel(region, 1.15, 0.7)
    return f


def hd_wood(key="wood"):
    def f(region, face, pal, rng):
        h, w = _base(region, pal[key], face, rng, amp=6, cell=2, grain=5)
        along_x = face in ("up", "down") or w > h
        n = 4
        if along_x:
            for y in range(0, h, n):
                region[y, :, :3] = shade(pal[key], 0.65)
        else:
            for x in range(0, w, n):
                region[:, x, :3] = shade(pal[key], 0.65)
        bevel(region, 1.2, 0.6)
    return f


def hd_water(region, face, pal, rng):
    h, w = _base(region, pal["water"], face, rng, amp=10, cell=4, grain=3)
    for _ in range(max(1, w * h // 40)):
        x, y = rng.randrange(w), rng.randrange(h)
        region[y, x:x + 2, :3] = shade(pal["water"], 1.5)


def hd_fire(region, face, pal, rng):
    """Нутро горна: от белого жара у пода к красному вверху."""
    h, w = region.shape[:2]
    n = vnoise(h, w, 3, rng)
    for y in range(h):
        t = y / max(1, h - 1)
        for x in range(w):
            k = min(1.0, max(0.0, t + n[y, x] * 0.25))
            c = (255, int(240 - 170 * (1 - k)), int(150 - 140 * (1 - k)))
            region[y, x, :3] = shade(c, 0.55 + 0.45 * k)
    region[..., 3] = 255


MATERIALS.update({
    "hd_brick": hd_brick(),
    "hd_stone": hd_stone(),
    "hd_wood": hd_wood(),
    "hd_water": hd_water,
    "hd_fire": hd_fire,
    "hd_soot": hd_metal("soot", rivets=False, panels=False),
})
