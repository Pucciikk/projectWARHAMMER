"""
Ритуальный разлом тёмного техножреца: знак проявляется на земле по символам, а не растёт кругом.

    python3 tools/models/warp_rift.py

Порядок появления (анимация misc.summon, 11,5 с; вспышка на 5,75 с — как BURST_AT в WarpRiftEntity):
кровавые письмена → внешнее кольцо с зубцами шестерни (Тёмные Механикус) → 16 рун Тёмного Языка по кругу,
одна за другой → кольцо мелкой вязи → шесть щупалец ползут от кольца к центру → восемь стрел звезды Хаоса
выстреливают из центра → в центре вспыхивает метка Тзинча. После вспышки всё гаснет в обратном порядке.

Всё рисуется только в карте свечения (_glow, складывается со сценой), основная текстура прозрачна:
линии мягкие, с ореолом, без квадратных краёв.

Ещё скрипт рисует спрайты частиц: warp_flame_0..7 (язык синего пламени, кадры анимации)
и warp_rune_0..15 (парящие руны и знаки богов).
"""
import math
import os
import random
import zlib

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import hd  # noqa: F401
from geo import ASSETS, MATERIALS, Model, keys, save_png, write_animations

S = 4                       # 64 px текстуры на блок: тонкие линии без лесенки
CYAN = (90, 200, 255)
VIOLET = (170, 80, 255)
BLOOD = (150, 10, 18)
WHITE = (235, 250, 255)
PAL = {}


# ------------------------------------------------------------------ рисование со свечением

def glow_image(w, h, draw, color, halo=0.9, k=4, blur=None):
    """Рисует штрихи белым на большом холсте, даёт ореол размытием и красит: ядро светлее, края — цветом."""
    W, H = w * k, h * k
    mask = Image.new("L", (W, H), 0)
    draw(ImageDraw.Draw(mask), W, H)
    core = np.asarray(mask.resize((w, h), Image.LANCZOS), np.float32) / 255
    r = blur if blur is not None else max(1.5, w / 90)
    soft = np.asarray(mask.resize((w, h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(r)), np.float32) / 255
    wide = np.asarray(mask.resize((w, h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(r * 3)), np.float32) / 255
    c = np.array(color, np.float32)
    rgb = (np.array(WHITE, np.float32) * core[..., None] * 0.85 + c * np.clip(soft * 1.6, 0, 1)[..., None]
           + c * 0.5 * np.clip(wide * 1.8, 0, 1)[..., None] * halo)
    return np.clip(rgb, 0, 255)


def glow_material(draw, color, halo=0.9, blur=None):
    """Материал: рисунок только на верхней грани, в карту свечения; основная текстура прозрачна."""
    def f(region, face, pal, rng):
        region[...] = 0
        if face != "up":
            return
        h, w = region.shape[:2]
        region[..., :3] = glow_image(w, h, lambda d, W, H: draw(d, W, H, rng), color, halo, blur=blur).astype(np.uint8)
        region[..., 3] = 1  # метка: грань нарисована (в glow_only уйдёт в ноль)
    return f


def glow_only(g, region, face, S_, pal):
    if face == "up":
        g[..., :3] = region[..., :3]
        g[..., 3] = 255
    region[...] = 0


# ------------------------------------------------------------------ символы

def _ring(d, cx, cy, r, w):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=255, width=int(w))


def draw_outer_ring(d, W, H, rng):
    """Двойное кольцо, наружу — зубья шестерни, сломанные через один (тёмная шестерня Механикус)."""
    cx, cy = W / 2, H / 2
    R = W * 0.485
    lw = W * 0.006
    _ring(d, cx, cy, R * 0.97, lw)
    _ring(d, cx, cy, R * 0.80, lw * 0.8)
    for i in range(48):
        a = i * math.pi * 2 / 48
        if i % 6 == 3:
            continue  # выбитый зуб
        r0, r1 = R * 0.97, R * (1.0 if i % 2 else 0.995)
        aw = 0.035
        pts = [(cx + math.cos(a - aw) * r0, cy + math.sin(a - aw) * r0), (cx + math.cos(a - aw * 0.6) * r1, cy + math.sin(a - aw * 0.6) * r1),
               (cx + math.cos(a + aw * 0.6) * r1, cy + math.sin(a + aw * 0.6) * r1), (cx + math.cos(a + aw) * r0, cy + math.sin(a + aw) * r0)]
        d.polygon(pts, fill=255)
    for i in range(96):  # риски между кольцами
        a = i * math.pi * 2 / 96
        r0, r1 = R * 0.80, R * (0.83 if i % 4 else 0.86)
        d.line([(cx + math.cos(a) * r0, cy + math.sin(a) * r0), (cx + math.cos(a) * r1, cy + math.sin(a) * r1)], fill=255, width=int(lw * 0.7))


def draw_script_ring(d, W, H, rng):
    """Кольцо мелкой вязи: непрерывная строка угловатых знаков."""
    cx, cy = W / 2, H / 2
    R = W * 0.47
    lw = W * 0.008
    _ring(d, cx, cy, R, lw)
    _ring(d, cx, cy, R * 0.82, lw)
    n = 44
    for i in range(n):
        a0 = i * math.pi * 2 / n
        pts = []
        for k in range(rng.randint(3, 5)):
            a = a0 + (rng.random() - 0.5) * 0.09
            r = R * (0.85 + rng.random() * 0.12)
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
        d.line(pts, fill=255, width=int(lw), joint="curve")


def _rune_strokes(rng, kind):
    """Руна Тёмного Языка в единичном квадрате: ствол, засечки, крюки, глаз; или знак бога."""
    strokes, dots, circles = [], [], []
    if kind == "tzeentch":
        circles.append((0.5, 0.42, 0.16))
        strokes.append([(0.18, 0.3), (0.22, 0.55), (0.38, 0.72), (0.5, 0.76), (0.62, 0.72), (0.78, 0.55), (0.82, 0.3)])
        strokes.append([(0.5, 0.76), (0.5, 0.95)])
        strokes.append([(0.18, 0.3), (0.08, 0.2), (0.12, 0.08)])
        strokes.append([(0.82, 0.3), (0.92, 0.2), (0.88, 0.08)])
        dots.append((0.5, 0.42))
    elif kind == "khorne":
        strokes += [[(0.15, 0.1), (0.85, 0.7)], [(0.85, 0.1), (0.15, 0.7)], [(0.1, 0.88), (0.9, 0.88)]]
    elif kind == "nurgle":
        circles += [(0.5, 0.3, 0.17), (0.3, 0.66, 0.17), (0.7, 0.66, 0.17)]
    elif kind == "slaanesh":
        circles.append((0.42, 0.55, 0.22))
        strokes += [[(0.58, 0.39), (0.88, 0.1)], [(0.68, 0.1), (0.88, 0.1), (0.88, 0.3)], [(0.42, 0.77), (0.42, 0.97)], [(0.3, 0.88), (0.54, 0.88)]]
    elif kind == "eye":
        strokes += [[(0.05, 0.5), (0.3, 0.3), (0.7, 0.3), (0.95, 0.5), (0.7, 0.7), (0.3, 0.7), (0.05, 0.5)]]
        circles.append((0.5, 0.5, 0.12))
        dots.append((0.5, 0.5))
    else:
        x = 0.35 + rng.random() * 0.3
        strokes.append([(x, 0.08), (x + (rng.random() - 0.5) * 0.15, 0.92)])  # ствол
        for _ in range(rng.randint(2, 4)):
            y = 0.15 + rng.random() * 0.7
            sx = 1 if rng.random() < 0.5 else -1
            ln = 0.2 + rng.random() * 0.3
            hook = rng.random() < 0.5
            pts = [(x, y), (x + sx * ln, y + (rng.random() - 0.5) * 0.3)]
            if hook:
                pts.append((pts[-1][0], pts[-1][1] + (0.15 if rng.random() < 0.5 else -0.15)))
            strokes.append(pts)
        if rng.random() < 0.4:
            circles.append((x + (rng.random() - 0.5) * 0.4, 0.15 + rng.random() * 0.2, 0.07))
        if rng.random() < 0.5:
            dots.append((0.2 + rng.random() * 0.6, 0.85))
    return strokes, dots, circles


def draw_rune(kind, seed):
    def draw(d, W, H, rng=None):
        r = random.Random(seed)
        strokes, dots, circles = _rune_strokes(r, kind)
        m = W * 0.12
        sx = lambda p: (m + p[0] * (W - 2 * m), m + p[1] * (H - 2 * m))
        lw = int(W * 0.075)
        for s in strokes:
            d.line([sx(p) for p in s], fill=255, width=lw, joint="curve")
        for (x, y, rr) in circles:
            c = sx((x, y))
            rad = rr * (W - 2 * m)
            d.ellipse([c[0] - rad, c[1] - rad, c[0] + rad, c[1] + rad], outline=255, width=lw)
        for p in dots:
            c = sx(p)
            d.ellipse([c[0] - lw, c[1] - lw, c[0] + lw, c[1] + lw], fill=255)
    return draw


RUNES = ["tzeentch", "rune", "rune", "eye", "rune", "khorne", "rune", "rune",
         "tzeentch", "rune", "nurgle", "rune", "eye", "rune", "slaanesh", "rune"]


def draw_arrow(d, W, H, rng):
    """Стрела звезды Хаоса: древко от центра (низ плоскости) к острию наверху."""
    cx = W / 2
    lw = W * 0.12
    d.line([(cx, H * 0.98), (cx, H * 0.2)], fill=255, width=int(lw))
    d.polygon([(cx, H * 0.01), (cx - W * 0.45, H * 0.3), (cx - W * 0.12, H * 0.24), (cx, H * 0.33),
               (cx + W * 0.12, H * 0.24), (cx + W * 0.45, H * 0.3)], fill=255)


def draw_tentacle(seed):
    """Щупальце: от корня (низ плоскости) закручивается к концу, сужается; присоски точками вдоль внутренней стороны."""
    def draw(d, W, H, rng=None):
        r = random.Random(seed)
        pts, x, y, a = [], W * 0.5, H * 0.98, -math.pi / 2
        curl = (0.004 + r.random() * 0.003) * (1 if seed % 2 else -1)
        n = 90
        for i in range(n):
            t = i / n
            pts.append((x, y, t))
            a += curl * (1 + 30 * t ** 3) + 0.012 * math.sin(t * 9 + seed)  # волной, к концу — в завиток
            step = H * 0.0105
            x += math.cos(a) * step
            y += math.sin(a) * step
        for i in range(len(pts) - 1):
            (x0, y0, t), (x1, y1, _) = pts[i], pts[i + 1]
            wdt = W * (0.2 * (1 - t) ** 1.1 + 0.015)
            d.line([(x0, y0), (x1, y1)], fill=255, width=max(1, int(wdt)))
        for i in range(4, len(pts) - 8, 5):  # присоски
            x0, y0, t = pts[i]
            x1, y1, _ = pts[i + 1]
            nx, ny = -(y1 - y0), (x1 - x0)
            ln = math.hypot(nx, ny) or 1
            off = W * 0.06 * (1 - t)
            px, py = x0 + nx / ln * off * (1 if curl > 0 else -1), y0 + ny / ln * off * (1 if curl > 0 else -1)
            rr = W * 0.022 * (1 - t) + 1
            d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=0)
    return draw


def draw_mark(d, W, H, rng):
    """Метка Тзинча в центре: око в чаше-полумесяце, рога-завитки, хвост вниз; вокруг — восемь точек."""
    lw = int(W * 0.045)
    cx, cy = W / 2, H * 0.44
    r = W * 0.15
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=255, width=lw)
    d.ellipse([cx - r * 0.35, cy - r * 0.35, cx + r * 0.35, cy + r * 0.35], fill=255)
    R = W * 0.3
    d.arc([cx - R, cy - R * 1.1, cx + R, cy + R * 1.0], 10, 170, fill=255, width=lw)
    for s in (-1, 1):  # рога закручиваются наружу и вверх
        x0, y0 = cx + s * R * 0.98, cy - R * 0.05
        pts = [(x0, y0)]
        a = -math.pi / 2 if s > 0 else -math.pi / 2
        x, y = x0, y0
        for i in range(30):
            a += s * 0.13
            x += math.cos(a) * W * 0.012 * (1 - i / 40)
            y += math.sin(a) * W * 0.012 * (1 - i / 40)
            pts.append((x, y))
        d.line(pts, fill=255, width=lw, joint="curve")
    d.line([(cx, cy + R * 1.0), (cx, H * 0.95)], fill=255, width=lw)
    d.line([(cx - W * 0.08, H * 0.86), (cx + W * 0.08, H * 0.86)], fill=255, width=lw)
    for i in range(8):
        a = i * math.pi / 4
        x, y = W / 2 + math.cos(a) * W * 0.46, H / 2 + math.sin(a) * H * 0.46
        d.ellipse([x - lw, y - lw, x + lw, y + lw], fill=255)


def draw_blood(d, W, H, rng):
    """Кровавые письмена: мазки и иероглифы между кольцами, потёки к центру, отпечатки ладоней."""
    cx, cy = W / 2, H / 2
    R = W * 0.5
    r = random.Random(11)
    for i in range(40):  # иероглифы — короткие толстые штрихи с потёками
        a = r.random() * math.pi * 2
        rad = R * (0.55 + r.random() * 0.33)
        x, y = cx + math.cos(a) * rad, cy + math.sin(a) * rad
        s = W * 0.025
        for _ in range(r.randint(2, 4)):
            dx, dy = (r.random() - 0.5) * s * 2, (r.random() - 0.5) * s * 2
            d.line([(x, y), (x + dx, y + dy)], fill=255, width=int(W * 0.008 + r.random() * W * 0.006))
            x, y = x + dx * 0.5, y + dy * 0.5
        # потёк к центру
        ln = r.random() * R * 0.15
        d.line([(x, y), (x - math.cos(a) * ln, y - math.sin(a) * ln)], fill=255, width=int(W * 0.004))
    for i in range(30):  # брызги
        a, rad = r.random() * math.pi * 2, R * (0.2 + r.random() * 0.75)
        x, y = cx + math.cos(a) * rad, cy + math.sin(a) * rad
        rr = W * (0.004 + r.random() * 0.01)
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=255)
    for a in (0.7, 3.4):  # смазанные ладони
        x, y = cx + math.cos(a) * R * 0.62, cy + math.sin(a) * R * 0.62
        d.ellipse([x - W * 0.025, y - W * 0.02, x + W * 0.025, y + W * 0.03], fill=255)
        for k in range(5):
            fa = a + math.pi + (k - 2) * 0.35
            d.line([(x, y), (x + math.cos(fa) * W * 0.045, y + math.sin(fa) * W * 0.045)], fill=255, width=int(W * 0.01))


MATERIALS.update({
    "rift_blood": glow_material(draw_blood, BLOOD, halo=0.5),
    "rift_outer": glow_material(draw_outer_ring, CYAN),
    "rift_script": glow_material(draw_script_ring, VIOLET),
    "rift_arrow": glow_material(draw_arrow, CYAN, blur=2.5),
    "rift_mark": glow_material(draw_mark, VIOLET, halo=1.3, blur=3),
})
for i, kind in enumerate(RUNES):
    MATERIALS[f"rift_rune_{i}"] = glow_material(draw_rune(kind, 100 + i), VIOLET if kind != "rune" else CYAN, halo=1.2, blur=2)
for i in range(6):
    MATERIALS[f"rift_tentacle_{i}"] = glow_material(draw_tentacle(200 + i), VIOLET, halo=0.8, blur=2)


# ------------------------------------------------------------------ модель

N_RUNES, N_ARROWS, N_TENT = len(RUNES), 8, 6


def build():
    m = Model("warp_rift", S=S, atlas_w=512)
    m.bone("root", [0, 0, 0])
    m.bone("blood", [0, 0, 0], "root").cube([-48, 0.2, -48], [96, 0, 96], "rift_blood", glow=glow_only)
    m.bone("ring_outer", [0, 0, 0], "root").cube([-48, 0.3, -48], [96, 0, 96], "rift_outer", glow=glow_only)
    m.bone("ring_script", [0, 0, 0], "root").cube([-30, 0.35, -30], [60, 0, 60], "rift_script", glow=glow_only)
    for i in range(N_RUNES):
        a = i * 360 / N_RUNES
        rad = 41.5
        x, z = math.sin(math.radians(a)) * rad, -math.cos(math.radians(a)) * rad
        b = m.bone(f"rune_{i}", [round(x, 3), 0, round(z, 3)], "root", rotation=[0, -a, 0])
        b.cube([x - 4.5, 0.4, z - 4.5], [9, 0, 9], f"rift_rune_{i}", glow=glow_only)
    for i in range(N_TENT):
        a = i * 360 / N_TENT + 15
        rad = 36
        x, z = math.sin(math.radians(a)) * rad, -math.cos(math.radians(a)) * rad
        # корень — у кольца, щупальце тянется к центру (по −Z плоскости после поворота)
        b = m.bone(f"tentacle_{i}", [round(x, 3), 0, round(z, 3)], "root", rotation=[0, -a + 180, 0])
        b.cube([x - 9, 0.45, z - 24], [18, 0, 24], f"rift_tentacle_{i}", glow=glow_only)
    for i in range(N_ARROWS):
        a = i * 45 + 22.5
        b = m.bone(f"arrow_{i}", [0, 0, 0], "root", rotation=[0, -a, 0])
        b.cube([-3, 0.5, -26], [6, 0, 20], "rift_arrow", glow=glow_only)
    m.bone("mark", [0, 0, 0], "root").cube([-8, 0.55, -8], [16, 0, 16], "rift_mark", glow=glow_only)
    return m


def appear(at, peak=1.35, hold_until=9.0, gone=None, settle=0.18):
    """Ключи масштаба: ноль до at, вспышка-«удар» до peak, оседание к 1, пульс во вспышке, исчезновение."""
    gone = gone if gone is not None else hold_until + 0.25
    pts = [(0, [0, 0, 0]), (at, [0, 0, 0]), (at + 0.07, [peak, 1, peak]), (at + 0.07 + settle, [1, 1, 1])]
    if at + 0.3 < 5.6:
        pts += [(5.6, [1, 1, 1]), (5.75, [1.18, 1, 1.18]), (6.1, [1, 1, 1])]
    pts += [(hold_until, [1, 1, 1]), (gone, [0, 0, 0])]
    pts = sorted({round(t, 3): v for t, v in pts}.items())
    return keys(pts)


def animations():
    bones = {
        "blood": {"scale": appear(0.0, peak=1.08, settle=0.5, hold_until=10.4, gone=11.2)},
        "ring_outer": {"scale": appear(0.45, peak=1.12, hold_until=10.0, gone=10.6),
                       "rotation": keys([(0, [0, 0, 0]), (11.5, [0, 40, 0])])},
        "ring_script": {"scale": appear(2.3, hold_until=9.6, gone=10.0),
                        "rotation": keys([(0, [0, 0, 0]), (11.5, [0, -120, 0])])},
        "mark": {"scale": appear(4.6, peak=2.2, settle=0.35, hold_until=8.6, gone=9.0),
                 "rotation": keys([(0, [0, 0, 0]), (4.6, [0, 0, 0]), (11.5, [0, 300, 0])])},
        "root": {"rotation": keys([(0, [0, 0, 0]), (11.5, [0, 25, 0])])},
    }
    for i in range(N_RUNES):  # руны проступают по кругу одна за другой и гаснут в том же порядке
        at = 0.9 + i * 0.085
        bones[f"rune_{i}"] = {"scale": appear(at, peak=1.7, hold_until=8.4 + i * 0.07, gone=8.6 + i * 0.07)}
    for i in range(N_TENT):  # щупальца выползают от кольца и шевелятся
        at = 2.6 + i * 0.16
        bones[f"tentacle_{i}"] = {
            "scale": keys([(0, [0, 0, 0]), (at, [0, 0, 0]), (at + 0.55, [1, 1, 1]), (8.8, [1, 1, 1]), (9.4, [0, 0, 0])]),
            "rotation": keys([(0, [0, 0, 0])] + [(round(at + k * 0.4, 2), [0, 7 * (1 if (k + i) % 2 else -1), 0]) for k in range(1, 16)]),
        }
    for i in range(N_ARROWS):  # стрелы звезды выстреливают из центра
        at = 3.7 + i * 0.07
        bones[f"arrow_{i}"] = {"scale": keys([(0, [0, 0, 0]), (at, [0, 0, 0]), (at + 0.1, [1.25, 1, 1.25]), (at + 0.3, [1, 1, 1]),
                                              (5.6, [1, 1, 1]), (5.75, [1.3, 1, 1.3]), (6.1, [1, 1, 1]),
                                              (9.2, [1, 1, 1]), (9.5, [0, 0, 0])])}
    return {"misc.summon": {"length": 11.5, "loop": "hold_on_last_frame", "bones": bones}}


# ------------------------------------------------------------------ спрайты частиц

def particle_png(name, img):
    p = os.path.join(ASSETS, "textures", "particle", name + ".png")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    img.save(p)


def flame_frames(n=8, size=32):
    """Язык синего пламени: белое ядро, голубые края, фиолетовый кончик; кадры — пламя дрожит и рвётся."""
    rng = np.random.default_rng(5)
    names = []
    for f in range(n):
        k = 6
        W = H = size * k
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        u = (xx / W - 0.5) * 2
        v = 1 - yy / H                                  # 0 внизу, 1 вверху
        phase = f / n * math.pi * 2
        sway = 0.18 * np.sin(v * 5 + phase) * v
        width = (0.85 * (1 - v) ** 0.7 * (0.7 + 0.3 * np.sin(v * 3.1 + 0.5)) + 0.03) * (1 - 0.12 * f / n)
        d = np.abs(u - sway) / np.maximum(width, 1e-3)
        noise = rng.random((H // 24 + 2, W // 24 + 2)).astype(np.float32)
        nimg = np.asarray(Image.fromarray((noise * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255
        dens = np.clip(1.15 - d - (nimg - 0.5) * 0.7 - v * 0.15 - f / n * 0.2, 0, 1)
        dens = dens ** 0.6
        core = np.clip(dens * 2.0 - 1.0, 0, 1) * np.clip(1.2 - v, 0, 1)
        blue = np.array((40, 120, 255), np.float32)
        col = np.array(VIOLET, np.float32) * (1 - dens[..., None]) + blue * dens[..., None]
        col = col * (1 - np.clip(dens * 1.5 - 0.3, 0, 1)[..., None]) + np.array(CYAN, np.float32) * np.clip(dens * 1.5 - 0.3, 0, 1)[..., None]
        col = col * (1 - core[..., None]) + np.array(WHITE, np.float32) * core[..., None]
        a = np.clip(dens * 2.0, 0, 1)
        img = np.dstack([np.clip(col, 0, 255), a * 255]).astype(np.uint8)
        im = Image.fromarray(img, "RGBA").resize((size, size), Image.LANCZOS)
        names.append(f"warp_flame_{f}")
        particle_png(names[-1], im)
    return names


def rune_sprites(size=32):
    names = []
    for i, kind in enumerate(RUNES):
        color = VIOLET if kind != "rune" else CYAN
        rgb = glow_image(size, size, lambda d, W, H: draw_rune(kind, 300 + i)(d, W, H), color, halo=1.2, k=8, blur=1.2)
        a = np.clip(rgb.max(axis=2) / 255 * 1.6, 0, 1)
        img = np.dstack([rgb, a * 255]).astype(np.uint8)
        names.append(f"warp_rune_{i}")
        particle_png(names[-1], Image.fromarray(img, "RGBA"))
    return names


def particle_json(name, textures):
    import json
    p = os.path.join(ASSETS, "particles", name + ".json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump({"textures": [f"warpbound:{t}" for t in textures]}, fh, indent=1)


def generate():
    m = build()
    print("warp_rift")
    m.build()
    base, glow = m.paint(PAL, seed=zlib.crc32(b"warp_rift"))
    save_png(base, "entity", "warp_rift.png")
    save_png(glow, "entity", "warp_rift_glow.png")
    write_animations("warp_rift", animations())
    particle_json("warp_flame", flame_frames())
    particle_json("warp_rune", rune_sprites())
    print("   частицы warp_flame, warp_rune")


if __name__ == "__main__":
    generate()
