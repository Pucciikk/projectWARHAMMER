"""
Карта Империума для мостика (по образцу карт из книг: пергамент Империума Санктус, тёмный Империум Нихилус
за Великим Разломом, Око Ужаса, варп-штормы, сегментумы, сетка вокруг Терры, роза ветров, латунная рамка).

Пишет:
  assets/warpbound/textures/gui/star_map.png      1400×800 — экран карты и табло на стене (StarChartRenderer)
  assets/warpbound/textures/item/star_chart.png   16×16 — иконка блока

Подписи не рисуются: их выводит экран (переводы ru/en). Точки миров — те же координаты, что в StarChartScreen.WORLDS.
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "src", "main", "resources", "assets", "warpbound", "textures")
W, H = 1400, 800
RNG = np.random.default_rng(40000)

# миры канона [x, y] от 0 до 1 — совпадают с StarChartScreen.WORLDS
WORLDS = {
    "terra": (0.340, 0.470), "mars": (0.356, 0.497), "necromunda": (0.392, 0.438), "cadia": (0.282, 0.205),
    "fenris": (0.168, 0.272), "vigilus": (0.405, 0.172), "armageddon": (0.470, 0.222), "prospero": (0.120, 0.470),
    "catachan": (0.300, 0.780), "macragge": (0.800, 0.700), "baal": (0.880, 0.550), "nocturne": (0.660, 0.840),
}
TERRA = WORLDS["terra"]
EYE = (0.215, 0.115)
# Великий Разлом: ломаная от верхнего края через галактику к правому краю
RIFT = [(0.30, -0.02), (0.345, 0.08), (0.40, 0.17), (0.46, 0.26), (0.55, 0.305), (0.66, 0.325), (0.78, 0.345),
        (0.90, 0.37), (1.02, 0.41)]


def noise(scale, seed):
    """Сглаженный шум 0..1: случайная сетка, растянутая бикубически."""
    r = np.random.default_rng(seed)
    gw, gh = max(2, int(W / scale)), max(2, int(H / scale))
    g = (r.random((gh, gw)) * 255).astype(np.uint8)
    return np.asarray(Image.fromarray(g).resize((W, H), Image.BICUBIC), dtype=np.float32) / 255.0


def fbm(seed, scales=(220, 90, 40, 16)):
    out = np.zeros((H, W), np.float32)
    amp, total = 1.0, 0.0
    for i, s in enumerate(scales):
        out += noise(s, seed + i) * amp
        total += amp
        amp *= 0.5
    return out / total


def rift_y(u):
    """y Разлома над столбцом u (до начала Разлома — None)."""
    pts = RIFT
    if u < pts[0][0]:
        return None
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= u <= x1:
            t = (u - x0) / (x1 - x0)
            return y0 + (y1 - y0) * t
    return pts[-1][1]


def main():
    u = np.linspace(0, 1, W, dtype=np.float32)[None, :].repeat(H, 0)
    v = np.linspace(0, 1, H, dtype=np.float32)[:, None].repeat(W, 1)
    n1, n2, n3 = fbm(1), fbm(11), fbm(21, (60, 24, 10, 5))

    # галактика: неровный эллипс, за ним — пустота
    disk = ((u - 0.50) / 0.60) ** 2 + ((v - 0.50) / 0.66) ** 2 + 0.55 * (n1 - 0.5)
    galaxy = disk < 1.0
    # Нихилус — над Разломом
    ry = np.full(W, np.nan, np.float32)
    for x in range(W):
        y = rift_y(x / W)
        ry[x] = np.nan if y is None else y
    ryy = ry[None, :].repeat(H, 0) + (n2 - 0.5) * 0.06
    nihilus = np.nan_to_num(v < ryy, nan=False).astype(bool)
    dist = np.abs(v - np.nan_to_num(ryy, nan=-9))
    width = 0.010 + 0.022 * n3 + 0.01 * np.clip((u - 0.35) * 2, 0, 1)
    rift = (dist < width) & ~np.isnan(ryy)
    rift_edge = (dist < width + 0.006) & ~rift & ~np.isnan(ryy)

    img = np.zeros((H, W, 3), np.float32)
    space = np.array([13, 15, 21], np.float32)
    parch = np.array([222, 209, 182], np.float32)
    nih = np.array([38, 42, 56], np.float32)
    img[:] = space
    mott = (n3[..., None] - 0.5) * 34 + (n1[..., None] - 0.5) * 20
    img[galaxy] = (parch + mott)[galaxy]
    img[galaxy & nihilus] = (nih + mott * 0.6)[galaxy & nihilus]
    # к краю галактики пергамент темнеет и «обгорает»
    edge = np.clip((disk - 0.78) / 0.22, 0, 1)[..., None]
    img = img * (1 - 0.45 * edge * galaxy[..., None])

    # пылевые облака: серые разводы на пергаменте
    dust = (fbm(31, (120, 50, 20)) > 0.6) & galaxy & ~nihilus
    img[dust] = img[dust] * 0.82 + np.array([90, 84, 78], np.float32) * 0.18
    # варп-штормы: рваные красные пятна с тёмной каймой; языки шторма свисают с Разлома
    storms = [(0.11, 0.63, 0.05), (0.53, 0.64, 0.035), (0.87, 0.80, 0.045), (0.46, 0.90, 0.03), (0.72, 0.52, 0.025),
              (0.20, 0.36, 0.022), (0.63, 0.72, 0.02)]
    for k in range(14):
        tu = 0.36 + 0.6 * RNG.random()
        storms.append((tu, rift_y(tu) + 0.03 + 0.05 * RNG.random(), 0.012 + 0.022 * RNG.random()))
    for (sx, sy, sr) in storms:
        d2 = np.sqrt(((u - sx) * W / H) ** 2 + (v - sy) ** 2) / sr + (n3 - 0.5) * 2.4 + (n1 - 0.5) * 0.8
        rim = (d2 >= 1.0) & (d2 < 1.14) & galaxy & ~nihilus
        m = (d2 < 1.0) & galaxy
        img[rim] = np.array([95, 16, 18], np.float32)
        img[m] = np.array([158, 22, 28], np.float32) + (n3[m, None] - 0.5) * 70
    # Разлом
    img[rift_edge & galaxy] = np.array([120, 18, 22], np.float32)
    img[rift] = np.array([172, 26, 30], np.float32) + (n3[rift, None] - 0.5) * 50
    # Око Ужаса: спираль
    ex, ey = EYE
    dx, dy = (u - ex) * W / H, v - ey
    r = np.sqrt(dx ** 2 + dy ** 2)
    ang = np.arctan2(dy, dx)
    eye = r < 0.075
    swirl = np.clip(0.5 + 0.7 * np.sin(ang * 2 + r * 170 + n3 * 3), 0, 1)
    col = np.stack([60 + 130 * swirl, 8 + 14 * swirl, 40 + 50 * (1 - swirl)], -1)
    fade = np.clip(1 - r / 0.075, 0, 1)[..., None]
    img = np.where(eye[..., None], img * (1 - fade) + col * fade, img)
    core = r < 0.012
    img[core] = np.array([25, 5, 18], np.float32)

    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    gal = galaxy
    nih_mask = nihilus

    # звёзды: тёмная тушь на пергаменте, белые точки во тьме
    for _ in range(2600):
        x, y = int(RNG.random() * W), int(RNG.random() * H)
        s = 1 if RNG.random() < 0.8 else 2
        if gal[y, x] and not nih_mask[y, x]:
            d.ellipse((x - s, y - s, x + s, y + s), fill=(70, 55, 42, 150))
        else:
            d.ellipse((x - s, y - s, x + s, y + s), fill=(235, 235, 245, 200 if s == 1 else 240))
    # сетка вокруг Терры: кольца и лучи
    tx, ty = TERRA[0] * W, TERRA[1] * H
    for k in range(1, 12):
        rr = k * 70
        d.ellipse((tx - rr, ty - rr, tx + rr, ty + rr), outline=(90, 70, 50, 55), width=1)
    for a in range(0, 360, 30):
        x2, y2 = tx + math.cos(math.radians(a)) * 1600, ty + math.sin(math.radians(a)) * 1600
        d.line((tx, ty, x2, y2), fill=(90, 70, 50, 40), width=1)
    # границы сегментумов: пунктир от круга Солар
    def dashed(p0, p1, color, w=2, dash=14, gap=9):
        x0, y0 = p0
        x1, y1 = p1
        length = math.hypot(x1 - x0, y1 - y0)
        n = int(length / (dash + gap))
        for i in range(n):
            a0, a1 = i * (dash + gap) / length, (i * (dash + gap) + dash) / length
            d.line((x0 + (x1 - x0) * a0, y0 + (y1 - y0) * a0, x0 + (x1 - x0) * a1, y0 + (y1 - y0) * a1), fill=color, width=w)
    solar = 120
    for a in range(0, 360, 6):
        a0, a1 = math.radians(a), math.radians(a + 3.5)
        d.line((tx + math.cos(a0) * solar, ty + math.sin(a0) * solar, tx + math.cos(a1) * solar, ty + math.sin(a1) * solar),
               fill=(110, 35, 30, 170), width=2)
    for (ex2, ey2) in ((0.06, 0.16), (0.03, 0.66), (0.44, 1.0), (0.55, 0.0)):
        ang2 = math.atan2(ey2 * H - ty, ex2 * W - tx)
        dashed((tx + math.cos(ang2) * solar, ty + math.sin(ang2) * solar), (ex2 * W, ey2 * H), (110, 35, 30, 150))
    # точки миров канона: кольцо тушью
    for name, (wx, wy) in WORLDS.items():
        x, y = wx * W, wy * H
        dark = nih_mask[int(min(y, H - 1)), int(min(x, W - 1))]
        ink = (230, 225, 210, 230) if dark else (60, 30, 24, 230)
        rr = 7 if name == "terra" else 5
        d.ellipse((x - rr, y - rr, x + rr, y + rr), outline=ink, width=2)
        d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=ink)
    # роза ветров
    cx, cy, R = 0.935 * W, 0.15 * H, 62
    ink = (205, 196, 175, 220)
    for rr in (R, R - 6, R * 0.45):
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=ink, width=2)
    for k in range(8):
        a = math.radians(k * 45 - 90)
        L = R + 12 if k % 2 == 0 else R * 0.7
        side = math.radians(k * 45 - 90 + 90)
        wdt = 9 if k % 2 == 0 else 6
        pts = [(cx + math.cos(a) * L, cy + math.sin(a) * L), (cx + math.cos(side) * wdt, cy + math.sin(side) * wdt),
               (cx, cy), (cx - math.cos(side) * wdt, cy - math.sin(side) * wdt)]
        d.polygon(pts, fill=ink if k % 2 == 0 else (150, 140, 120, 200))
    im = Image.alpha_composite(im.convert("RGBA"), ov)

    # латунная рамка с заклёпками и уголками
    fr = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fr)
    B = 16
    for i in range(B):
        t = i / (B - 1)
        c = (int(105 + 110 * math.sin(t * math.pi)), int(75 + 80 * math.sin(t * math.pi)), int(28 + 30 * math.sin(t * math.pi)), 255)
        fd.rectangle((i, i, W - 1 - i, H - 1 - i), outline=c)
    fd.rectangle((B, B, W - 1 - B, H - 1 - B), outline=(30, 20, 10, 255), width=2)
    for (x, y) in ((0, 0), (W - 46, 0), (0, H - 46), (W - 46, H - 46)):
        fd.rectangle((x, y, x + 45, y + 45), fill=(176, 132, 52, 255), outline=(70, 45, 15, 255), width=3)
        fd.ellipse((x + 15, y + 15, x + 30, y + 30), fill=(222, 182, 92, 255), outline=(70, 45, 15, 255), width=2)
    for x in range(80, W - 60, 70):
        for y in (B // 2, H - B // 2 - 1):
            fd.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(225, 190, 110, 255), outline=(70, 45, 15, 255))
    for y in range(80, H - 60, 70):
        for x in (B // 2, W - B // 2 - 1):
            fd.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(225, 190, 110, 255), outline=(70, 45, 15, 255))
    im = Image.alpha_composite(im, fr).convert("RGB")

    os.makedirs(os.path.join(ROOT, "gui"), exist_ok=True)
    im.save(os.path.join(ROOT, "gui", "star_map.png"), optimize=True)
    icon = im.resize((16, 16), Image.LANCZOS)
    os.makedirs(os.path.join(ROOT, "item"), exist_ok=True)
    icon.save(os.path.join(ROOT, "item", "star_chart.png"))
    print("карта:", im.size)


if __name__ == "__main__":
    main()
