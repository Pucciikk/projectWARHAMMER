#!/usr/bin/env python3
"""
Цельные модели собранных мультиблоков (GeckoLib, рисует ядро машины), 32 px на блок.

    python3 tools/models/gen_machines.py

Пишет assets/warpbound/geo/block/<машина>.geo.json, animations/block/<машина>.animation.json,
textures/block/<машина>.png и _glow.png.

Система координат модели — пиксели от центра низа ядра: ядро смотрит на север (−Z), шаблон
(data/warpbound/multiblock/<машина>.json) уходит от ядра назад (+Z) — ряды шаблона идут по Z от переда к заду.
"""
import math
import os
import sys
import zlib

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import hd  # noqa: E402,F401 — hd_-материалы
from geo import Model, keys, save_png, sin, track, write_animations  # noqa: E402
from priest_hd import emblem  # noqa: E402
from geo import MATERIALS, shade  # noqa: E402

MATERIALS["hd_steel"] = hd.hd_metal("steel", panels=False)

FORGE = dict(brick=(118, 58, 42), mortar=(64, 58, 54), stone=(96, 94, 92), dark=(52, 52, 56), soot=(40, 38, 38),
             metal=(140, 142, 148), brass=(196, 152, 60), leather=(92, 60, 36), wood=(104, 74, 46),
             bone=(214, 204, 176), glow=(255, 170, 60), glow2=(255, 110, 40), water=(40, 70, 110),
             screen=(20, 20, 20), cable=(32, 32, 36))


def finish(m, name, pal, anims):
    print(name)
    m.build(kind="block")
    base, glow = m.paint(pal, seed=zlib.crc32(name.encode()))
    save_png(base, "block", f"{name}.png")
    save_png(glow, "block", f"{name}_glow.png")
    write_animations(name, anims, kind="block")


# ------------------------------------------------------------------ горн обломков, 3×3×3

def salvage_forge():
    m = Model("salvage_forge", S=2, atlas_w=256)
    root = m.bone("forge", [0, 0, 0])
    # цоколь и порог
    root.cube([-24, 0, -8], [48, 4, 48], "hd_stone")
    root.cube([-20, 0, -11], [40, 2, 3], "hd_stone")
    # топка: тело, передняя стена с зевом
    root.cube([-18, 4, 0], [36, 26, 36], "hd_brick")
    root.cube([-18, 4, -6], [10, 26, 6], "hd_brick")
    root.cube([8, 4, -6], [10, 26, 6], "hd_brick")
    root.cube([-8, 20, -6], [16, 10, 6], "hd_brick")
    root.cube([-8, 4, -6], [16, 2, 6], "hd_stone")
    # латунная рамка зева и знак над ним
    root.cube([-9.5, 6, -7], [1.5, 15.5, 1.5], "hd_brass")
    root.cube([8, 6, -7], [1.5, 15.5, 1.5], "hd_brass")
    root.cube([-9.5, 20, -7], [19, 1.5, 1.5], "hd_brass")
    root.cube([-4.5, 22.5, -7], [9, 7, 1], "hd_brass", deco={"north": emblem(0.47)})
    # открытая заслонка
    root.cube([-16, 7, -7.5], [6, 12, 0.75], "hd_dark")
    root.cube([-11, 12, -8], [1, 2, 0.75], "hd_brass")
    # железные углы и пояс
    for x, z in ((-19, -7), (17.5, -7), (-19, 34.5), (17.5, 34.5)):
        root.cube([x, 4, z], [1.5, 26, 1.5], "hd_dark")
    root.cube([-18.5, 14, -6.5], [9.5, 1.5, 0.5], "hd_dark")
    root.cube([9, 14, -6.5], [9.5, 1.5, 0.5], "hd_dark")
    # смотровые щели по бокам — светятся, когда горн работает
    root.cube([-18.5, 10, 10], [0.5, 2, 12], "hd_fire", glow="all")
    root.cube([18, 10, 10], [0.5, 2, 12], "hd_fire", glow="all")
    # колпак ступенями и труба с латунными кольцами
    root.cube([-21, 30, -8], [42, 3, 46], "hd_dark")
    root.cube([-15, 33, -2], [30, 3, 34], "hd_soot")
    root.cube([-10, 36, 6], [20, 3, 22], "hd_soot")
    root.cube([-6, 39, 10], [12, 22, 12], "hd_brick")
    for y in (44, 54):
        root.cube([-6.75, y, 9.25], [13.5, 1.5, 13.5], "hd_brass")
    root.cube([-7.5, 61, 8.5], [15, 2, 2], "hd_dark")
    root.cube([-7.5, 61, 20.5], [15, 2, 2], "hd_dark")
    root.cube([-7.5, 61, 10.5], [2, 2, 10], "hd_dark")
    root.cube([5.5, 61, 10.5], [2, 2, 10], "hd_dark")
    root.cube([-5.5, 60.5, 10.5], [11, 1, 10], "hd_fire", glow="all")
    # приёмник лома на колпаке: воронка и обломки обшивки
    root.cube([-6, 33, -6], [12, 4, 8], "hd_rusty")
    root.cube([-4.5, 37, -5], [4, 1.5, 3], "hd_metal", rotation=[0, 20, 15], pivot=[-2.5, 37, -3.5])
    root.cube([0.5, 37, -4.5], [3.5, 1, 4], "hd_rusty", rotation=[10, -25, 0], pivot=[2, 37, -2.5])
    # труба от колпака к трубе сзади
    root.cube([10, 33, 26], [2.5, 12, 2.5], "hd_rusty")
    root.cube([6, 43, 26], [6.5, 2.5, 2.5], "hd_rusty")
    # инструмент на правой стене: клещи и молот
    root.cube([-20, 10, 4], [1, 12, 22], "hd_wood")
    root.cube([-21, 9, 8], [0.75, 11, 0.75], "hd_metal_plain")
    root.cube([-21, 9, 10], [0.75, 11, 0.75], "hd_metal_plain")
    root.cube([-21, 10, 16], [0.75, 10, 0.75], "hd_wood")
    root.cube([-22, 19, 14.5], [2.5, 2.5, 4], "hd_dark")

    # зев: жар и угли — отдельная кость, она «дышит» в работе
    fire = m.bone("fire", [0, 6, -3], "forge")
    fire.cube([-8, 6, -1], [16, 14, 1], "hd_fire", glow="all")
    fire.cube([-8, 6, -6], [16, 1.5, 5], "hd_fire", glow="all")

    # мехи на левой стене: нижняя доска неподвижна, верхняя качается на петле у стены
    m.bone("bellows", [18, 6, 18], "forge").cube([18, 6, 10], [6, 1.5, 16], "hd_wood")
    folds = m.bone("bellows_folds", [18, 7.5, 18], "forge")
    for i in range(3):
        folds.cube([18.5, 7.5 + i * 1.5, 10.5 + i * 0.5], [5, 1.5, 15 - i], "hd_leather")
    top = m.bone("bellows_top", [18, 12, 18], "forge")
    top.cube([18, 12, 10], [6, 1.5, 16], "hd_wood")
    top.cube([20, 13.5, 24], [1.5, 7, 1.5], "hd_wood")
    m.bone("bellows_nozzle", [18, 8, 18], "forge").cube([17, 8, 17], [2, 2, 2], "hd_brass")

    anims = {
        "misc.idle": {"length": 2.0, "loop": True, "bones": {
            "fire": {"scale": track(lambda t: [1, 0.85, 1], 2.0, 2)},
        }},
        "work.active": {"length": 1.4, "loop": True, "bones": {
            "bellows_top": {"rotation": track(lambda t: [0, 0, -10 + 10 * sin(t)], 1.4)},
            "bellows_folds": {"scale": track(lambda t: [1, 1 + 0.5 * sin(t, 0.0), 1], 1.4)},
            "fire": {"scale": track(lambda t: [1, 1.05 + 0.06 * sin(t * 3 % 1), 1], 1.4)},
        }},
    }
    finish(m, "salvage_forge", FORGE, anims)


# ------------------------------------------------------------------ рисунки на гранях

def gauge(region, S, pal):
    """Манометр: латунный обод, светлая шкала, красный сектор, стрелка."""
    import math
    from priest_hd import _icon, _paste

    def draw(d, W, H):
        cx, cy, R = W / 2, H / 2, min(W, H) * 0.46
        d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=tuple(pal["brass"]) + (255,))
        r = R * 0.8
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=tuple(pal["bone"]) + (255,))
        d.pieslice([cx - r, cy - r, cx + r, cy + r], -40, 20, fill=(170, 30, 20, 255))
        for i in range(9):
            a = math.radians(140 + i * 32.5)
            d.line([(cx + math.cos(a) * r * 0.75, cy + math.sin(a) * r * 0.75), (cx + math.cos(a) * r * 0.95, cy + math.sin(a) * r * 0.95)],
                   fill=(30, 30, 30, 255), width=max(1, int(W * 0.04)))
        a = math.radians(-30)
        d.line([(cx, cy), (cx + math.cos(a) * r * 0.85, cy + math.sin(a) * r * 0.85)], fill=(20, 20, 20, 255), width=max(1, int(W * 0.06)))
    h, w = region.shape[:2]
    _paste(region, _icon(w, h, draw))


def screen_text(region, S, pal):
    """Экран когитатора: зелёные строки бинарика."""
    import random
    rng = random.Random(3)
    h, w = region.shape[:2]
    region[..., :3] = (8, 20, 12)
    for y in range(2, h - 2, 3):
        x = 2
        while x < w - 3:
            ln = rng.randint(1, 4)
            if rng.random() < 0.75:
                region[y, x:min(w - 2, x + ln), :3] = pal["glow3"]
            x += ln + 1


def screen_glow(g, region, face, S, pal):
    if face != "north":
        return
    m = region[..., 1] > 120
    g[m, :3] = region[m, :3]
    g[m, 3] = 255


def hazard(region, S, pal):
    h, w = region.shape[:2]
    for y in range(h):
        for x in range(w):
            if ((x + y) // 4) % 2 == 0:
                region[y, x, :3] = (190, 150, 30)
            else:
                region[y, x, :3] = (26, 24, 22)


def big_cog(region, S, pal):
    """Шестерня Механикус с черепом — вырезная: вне зубьев грань прозрачна (у GeckoLib — cutout)."""
    import math
    from priest_hd import _icon
    h, w = region.shape[:2]
    brass, dark, bone = tuple(pal["brass"]), tuple(int(v * 0.45) for v in pal["brass"]), tuple(pal["bone"])

    def draw(d, W, H):
        cx, cy = W / 2, H / 2
        R, r = W * 0.5, W * 0.4
        pts = []
        for i in range(12 * 4):  # 12 зубьев: вершина, вершина, впадина, впадина
            a = i * math.pi * 2 / 48 - math.pi / 2
            rad = R if (i % 4) in (0, 1) else r
            pts.append((cx + math.cos(a) * rad, cy + math.sin(a) * rad))
        d.polygon(pts, fill=brass + (255,))
        d.ellipse([cx - r * 0.86, cy - r * 0.86, cx + r * 0.86, cy + r * 0.86], fill=dark + (255,))
        d.ellipse([cx - r * 0.78, cy - r * 0.78, cx + r * 0.78, cy + r * 0.78], fill=brass + (255,))
        # череп: свод, глазницы, нос, челюсть с зубами
        s = r * 0.62
        d.ellipse([cx - s * 0.7, cy - s * 0.8, cx + s * 0.7, cy + s * 0.45], fill=bone + (255,))
        d.rectangle([cx - s * 0.42, cy + s * 0.2, cx + s * 0.42, cy + s * 0.72], fill=bone + (255,))
        for ex in (-1, 1):
            d.ellipse([cx + ex * s * 0.33 - s * 0.2, cy - s * 0.25, cx + ex * s * 0.33 + s * 0.2, cy + s * 0.12], fill=(20, 16, 14, 255))
        d.polygon([(cx, cy + s * 0.12), (cx - s * 0.1, cy + s * 0.32), (cx + s * 0.1, cy + s * 0.32)], fill=(20, 16, 14, 255))
        for k in range(-2, 3):
            d.line([(cx + k * s * 0.15, cy + s * 0.45), (cx + k * s * 0.15, cy + s * 0.72)], fill=(60, 50, 40, 255), width=max(1, int(W * 0.012)))
    icon = _icon(w, h, draw)
    shade_k = region[..., :3].astype(np.float32).mean(axis=2, keepdims=True) / max(1.0, region[..., :3].mean())
    rgb = np.clip(icon[..., :3].astype(np.float32) * (0.85 + 0.15 * shade_k), 0, 255).astype(np.uint8)
    m = icon[..., 3] > 110
    region[m, :3] = rgb[m]
    region[..., 3] = np.where(m, 255, 0)


def window_glow(g, region, face, S, pal):
    if face in ("north", "south", "east", "west"):
        g[..., :3] = region[..., :3]
        g[..., 3] = 255


# ------------------------------------------------------------------ ручной пресс, 3×2×3

PRESS = dict(FORGE, steel=(168, 170, 176), glow3=(120, 255, 140), robe=(130, 34, 30), trim=(196, 152, 60),
             parchment=(214, 200, 160), wax=(120, 18, 22), glow=(140, 255, 160))


def manual_press():
    m = Model("manual_press", S=2, atlas_w=256)
    root = m.bone("press", [0, 0, 0])
    # станина: каменный цоколь на всю площадь шаблона, железная окантовка, рабочий стол со штампом
    root.cube([-24, 0, -8], [48, 6, 32], "hd_stone")
    root.cube([-24.5, 5, -8.5], [49, 1.5, 33], "hd_dark")
    root.cube([-10, 6.5, -7], [20, 4, 14], "hd_metal")
    root.cube([-6, 10.5, -5], [12, 2, 10], "hd_dark", deco={"up": emblem(0.42)})
    root.cube([-10.5, 6.5, -7.5], [21, 1, 1], "hd_rusty")
    for x in (-14, 10):  # ящики с заготовками по бокам стола
        root.cube([x, 6.5, -6], [4, 3, 8], "hd_wood")
        root.cube([x + 0.5, 9.5, -5.5], [3, 0.8, 7], "hd_metal_plain")
    # стойки рамы: толстые, с латунными поясами и заклёпками
    for sx in (-1, 1):
        x0 = 15 if sx > 0 else -21
        root.cube([x0, 6.5, -6], [6, 36, 10], "hd_dark")
        root.cube([x0 - 0.5, 6.5, -6.5], [7, 4, 11], "hd_rusty")
        for y in (16, 28, 38):
            root.cube([x0 - 0.5, y, -6.5], [7, 1.5, 11], "hd_brass")
        root.cube([x0 + (6 if sx > 0 else -1), 10, -2], [1, 28, 1], "hd_cable")
    # балка: дерево в железных обоймах, знак Механикус спереди
    root.cube([-24, 42, -7], [48, 8, 30], "hd_wood")
    for x in (-24.5, -10, 8, 22.5):
        root.cube([x, 41.5, -7.5], [2, 9, 31], "hd_dark")
    root.cube([-6, 43, -8.5], [12, 6, 1.5], "hd_brass", deco={"north": emblem(0.44)})
    # гайка винта в балке
    root.cube([-4, 40, -4], [8, 3, 8], "hd_brass")
    # паровой цилиндр сзади (поршень шаблона), манометр, вентиль, трубы в балку
    root.cube([-8, 6.5, 10], [16, 22, 12], "hd_brass")
    for y in (10, 18, 25):
        root.cube([-8.5, y, 9.5], [17, 1.5, 13], "hd_dark")
    root.cube([-3, 28.5, 13], [6, 3, 6], "hd_dark")
    root.cube([-1, 31.5, 15], [2, 10.5, 2], "hd_rusty")
    root.cube([-9.5, 16, 12], [1, 6, 6], "hd_dark", deco={"west": gauge})
    root.cube([8, 20, 14], [3, 3, 3], "hd_rusty")
    root.cube([11, 19, 13], [1, 5, 5], "hd_dark")
    root.cube([5, 28.5, 18], [2, 13.5, 2], "hd_cable")
    # фонарь-люмен и печать чистоты на стойке
    root.cube([-22.5, 30, -7.5], [2, 3, 2], "hd_glow", glow="all")
    root.cube([16, 22, -7], [4, 6, 0.5], "hd_parchment")
    root.cube([17, 27, -7.3], [2, 2, 1], "hd_wax")

    # винт и боёк: винт крутится, боёк ходит вниз по удару
    ram = m.bone("ram", [0, 24, 0], "press")
    ram.cube([-7, 20, -6], [14, 8, 12], "hd_steel")
    ram.cube([-7.5, 26, -6.5], [15, 1.5, 13], "hd_brass")
    ram.cube([-5, 18, -4], [10, 2, 8], "hd_dark")
    for sx in (-1, 1):  # направляющие по стойкам
        ram.cube([sx * 8.5 - (1.5 if sx < 0 else 0) + (0 if sx < 0 else 0), 21, -2], [1.5, 6, 4], "hd_dark")
    screw = m.bone("screw", [0, 28, 0], "ram")
    screw.cube([-1.5, 28, -1.5], [3, 22, 3], "hd_steel")
    for y in range(29, 49, 2):
        screw.cube([-2, y, -2], [4, 0.75, 4], "hd_metal_plain")
    wheel = m.bone("wheel", [0, 50, 0], "screw")
    wheel.cube([-3, 50, -3], [6, 2, 6], "hd_brass")
    for rot in (0, 90):
        wheel.cube([-14, 50.5, -0.75], [28, 1.5, 1.5], "hd_dark", rotation=[0, rot, 0], pivot=[0, 51, 0])
    for x, z in ((-14, 0), (14, 0), (0, -14), (0, 14)):
        wheel.cube([x - 1, 52, z - 1], [2, 4, 2], "hd_wood")

    anims = {
        "misc.idle": {"length": 3.0, "loop": True, "bones": {}},
        # удар: штурвал рывком проворачивается, винт тянет боёк вниз — удар — подъём
        "work.strike": {"length": 0.7, "bones": {
            "ram": {"position": keys([(0, [0, 0, 0]), (0.18, [0, -7.5, 0]), (0.24, [0, -7, 0]), (0.7, [0, 0, 0])])},
            "screw": {"rotation": keys([(0, [0, 0, 0]), (0.18, [0, 120, 0]), (0.7, [0, 0, 0])])},
        }},
    }
    finish(m, "manual_press", PRESS, anims)


# ------------------------------------------------------------------ Кузня Механикус, 5×5×6

KUZNYA = dict(FORGE, steel=(168, 170, 176), glow3=(120, 255, 140), robe=(132, 30, 28), trim=(196, 152, 60),
              robe_in=(70, 18, 16), stone=(112, 106, 100), dark=(46, 46, 50), parchment=(214, 200, 160), wax=(120, 18, 22),
              lamp=(255, 190, 90), glow=(255, 190, 90))


def mechanicus_forge():
    m = Model("mechanicus_forge", S=2, atlas_w=512)
    root = m.bone("forge", [0, 0, 0])
    # --- пол: плита на весь шаблон, латунная инкрустация, ступени перед входом, жёлто-чёрная кромка
    root.cube([-40, 0, -8], [80, 4, 80], "hd_stone")
    root.cube([-36, 4, -8], [72, 0.5, 4], "hd_dark", deco={"up": hazard})
    root.cube([-24, 0, -12], [48, 2, 4], "hd_stone")
    root.cube([-0.75, 4, 4], [1.5, 0.3, 60], "hd_brass")
    root.cube([-20, 4, 31.25], [40, 0.3, 1.5], "hd_brass")
    # --- колонны по углам: металл, латунные капители, контрфорсы, кабели
    for sx in (-1, 1):
        for z0 in (-8, 60):
            x0 = 28 if sx > 0 else -40
            root.cube([x0, 4, z0], [12, 60, 12], "hd_dark")
            root.cube([x0 - 1, 4, z0 - 1], [14, 6, 14], "hd_rusty")
            root.cube([x0 - 1, 56, z0 - 1], [14, 4, 14], "hd_brass")
            root.cube([x0 - 1.5, 60, z0 - 1.5], [15, 4, 15], "hd_dark")
            for y in (22, 40):
                root.cube([x0 - 0.5, y, z0 - 0.5], [13, 2, 13], "hd_brass")
    # --- стены по бокам и сзади: камень понизу, решётчатые окна с отсветом горна, трубы вдоль
    for sx in (-1, 1):
        x0 = 34 if sx > 0 else -40
        root.cube([x0, 4, 4], [6, 28, 56], "hd_stone")
        root.cube([x0, 32, 4], [6, 6, 56], "hd_brick")
        root.cube([x0 + (0 if sx > 0 else 5.5), 38, 6], [0.5, 16, 52], "hd_fire", glow=window_glow)
        for z in range(6, 58, 6):
            root.cube([x0 + (-0.25 if sx > 0 else 4.75), 38, z], [1.5, 16, 1], "hd_dark")
        root.cube([x0, 54, 4], [6, 6, 56], "hd_brick")
        root.cube([x0 + (-2 if sx > 0 else 6), 8, 10], [2, 2, 44], "hd_rusty")
        root.cube([x0 + (-2 if sx > 0 else 6), 12, 10], [2, 2, 44], "hd_cable")
    root.cube([-28, 4, 66], [56, 56, 6], "hd_brick")
    # --- горн у задней стены: топка, раскалённый зев, колпак, меха
    root.cube([-16, 4, 50], [32, 30, 16], "hd_brick")
    root.cube([-17, 4, 49], [34, 3, 18], "hd_stone")
    root.cube([-10, 8, 49], [20, 16, 1], "hd_dark")
    root.cube([-11, 7, 48.5], [22, 1.5, 1], "hd_brass")
    root.cube([-11, 24, 48.5], [22, 1.5, 1], "hd_brass")
    root.cube([-18, 34, 46], [36, 4, 20], "hd_soot")
    root.cube([-12, 38, 50], [24, 6, 14], "hd_soot")
    fire = m.bone("hearth_fire", [0, 8, 49], "forge")
    fire.cube([-9, 9, 48.8], [18, 14, 0.5], "hd_fire", glow="all")
    fire.cube([-9, 9, 45], [18, 1, 4], "hd_fire", glow="all")
    # --- трубы над крышей с латунными кольцами
    for sx in (-1, 1):
        x0 = sx * 16 - 4
        root.cube([x0, 44, 44], [8, 70, 8], "hd_brick")
        for y in (70, 90, 108):
            root.cube([x0 - 0.75, y, 43.25], [9.5, 2, 9.5], "hd_brass")
        root.cube([x0 + 1, 113.5, 45], [6, 0.5, 6], "hd_fire", glow="all")
    # --- крыша: обшивка ступенями, латунный пояс
    root.cube([-41, 64, -9], [82, 4, 82], "hd_dark")
    root.cube([-41.5, 64, -9.5], [83, 1.5, 83], "hd_brass")
    root.cube([-34, 68, -2], [68, 4, 68], "hd_dark")
    root.cube([-26, 72, 6], [52, 4, 52], "hd_dark")
    for x in range(-24, 25, 12):  # вентиляционные решётки
        root.cube([x - 3, 76, 20], [6, 1, 20], "hd_rusty")
    # --- фронтон: ступенчатый щипец над входом, на нём огромная шестерня с черепом
    root.cube([-30, 64, -10], [60, 10, 4], "hd_dark")
    root.cube([-22, 74, -10], [44, 8, 4], "hd_dark")
    root.cube([-14, 82, -10], [28, 6, 4], "hd_dark")
    root.cube([-31, 63.5, -10.5], [62, 1.5, 5], "hd_brass")
    cog = m.bone("cog", [0, 76, -11], "forge")
    cog.cube([-15, 61, -12], [30, 30, 0], "hd_brass", deco={"north": big_cog, "south": big_cog})
    root.cube([-3, 73, -11], [6, 6, 1], "hd_dark")                       # ось шестерни
    # --- арка входа: перекладина и свисающие знамёна Механикус на колоннах
    root.cube([-28, 54, -9], [56, 10, 6], "hd_dark")
    root.cube([-28, 53, -9.5], [56, 1.5, 7], "hd_brass")
    for sx in (-1, 1):
        b = m.bone(f"banner_{'right' if sx < 0 else 'left'}", [sx * 34, 52, -9.5], "forge")
        x0 = sx * 34 - 5
        b.cube([x0, 22, -10], [10, 30, 0.75], "hd_robe", deco={"north": emblem(0.4)})
        b.cube([x0 - 0.5, 51, -10.25], [11, 1.5, 1.25], "hd_brass")
    # лампы-люмены по колоннам
    for sx in (-1, 1):
        for z0 in (-9.5, 59.5):
            lamp = m.bone(f"lamp_{'r' if sx < 0 else 'l'}{'f' if z0 < 0 else 'b'}", [sx * 34, 48, z0], "forge")
            lamp.cube([sx * 34 - 1.5, 46, z0 - 1], [3, 4, 2], "hd_glow", glow="all")
            lamp.cube([sx * 34 - 2, 50, z0 - 1.25], [4, 1, 2.5], "hd_dark")
    # --- алтарь-когитатор на ядре: пюпитр, экран бинарика, череп, свечи
    root.cube([-6, 4, -6], [12, 10, 10], "hd_dark")
    root.cube([-7, 14, -7], [14, 2, 12], "hd_brass")
    root.cube([-6, 16, -2], [12, 10, 2], "hd_dark", rotation=[-25, 0, 0], pivot=[0, 16, -1])
    root.cube([-5, 17, -2.5], [10, 8, 0.5], "hd_screen", deco={"north": screen_text}, glow=screen_glow,
              rotation=[-25, 0, 0], pivot=[0, 16, -1])
    root.cube([-2, 16, 1], [4, 4, 4], "hd_bone")
    for x in (-6, 5):
        root.cube([x, 16, -6], [1.2, 3, 1.2], "hd_wax")
        root.cube([x + 0.3, 19, -5.7], [0.6, 1, 0.6], "hd_glow", glow="all")
    root.cube([-6.5, 6, -6.5], [5, 7, 0.5], "hd_parchment")
    # --- наковальня в центре (A шаблона)
    root.cube([-8, 4, 26], [16, 4, 12], "hd_stone")
    root.cube([-5, 8, 28], [10, 6, 8], "hd_dark")
    root.cube([-10, 14, 27], [20, 5, 10], "hd_steel")
    root.cube([10, 15, 29], [6, 3, 6], "hd_steel")
    root.cube([-11, 15, 29.5], [2, 3, 5], "hd_dark")
    ingot = m.bone("ingot", [0, 19, 32], "forge")
    ingot.cube([-4, 19, 30], [8, 2, 4], "hd_fire", glow="all")
    # --- кабели под потолком и сервоплечи с молотами (работают, когда рядом техножрец)
    root.cube([-30, 60, 30], [60, 3, 4], "hd_dark")
    for z in (12, 52):
        root.cube([-30, 61, z], [60, 1.5, 1.5], "hd_cable")
    for side, sx in (("right", -1), ("left", 1)):
        x = sx * 12
        mount = m.bone(f"arm_{side}", [x, 60, 32], "forge")
        mount.cube([x - 3, 56, 29], [6, 4, 6], "hd_brass")
        mount.cube([x - 2, 36, 30], [4, 20, 4], "hd_dark")
        mount.cube([x - 2.5, 44, 29.5], [5, 2, 5], "hd_rusty")
        elbow = m.bone(f"arm_{side}_2", [x, 36, 32], f"arm_{side}")
        elbow.cube([x - 2.5, 33.5, 29.5], [5, 5, 5], "hd_brass")
        elbow.cube([x - 1.5, 22, 30.5], [3, 12, 3], "hd_rusty")
        elbow.cube([x - 0.5, 23, 33.5], [1, 10, 1], "hd_cable")
        head = m.bone(f"hammer_{side}", [x, 22, 32], f"arm_{side}_2")
        head.cube([x - 4, 17, 29], [8, 5, 6], "hd_steel")
        head.cube([x - 4.5, 19, 28.5], [9, 1, 7], "hd_brass")
    # наклон рук к наковальне в покое: молоты подняты
    rest = {"arm_right": [0, 0, 18], "arm_left": [0, 0, -18], "arm_right_2": [0, 0, -30], "arm_left_2": [0, 0, 30]}
    for name, rot in rest.items():
        next(b for b in m.bones if b.name == name).rotation = rot
    # --- черепа в нишах на задней стене, печати чистоты на колоннах
    for x in (-24, 20):
        root.cube([x, 40, 65], [4, 4, 1], "hd_dark")
        root.cube([x + 0.5, 40.5, 64.5], [3, 3, 1], "hd_bone")
    for sx in (-1, 1):
        root.cube([sx * 34 - 2, 12, -9.5], [4, 7, 0.5], "hd_parchment")
        root.cube([sx * 34 - 1, 18.5, -9.8], [2, 2, 1], "hd_wax")

    lamps = {f"lamp_{a}{b}": {"scale": track(lambda t, k=i: [1, 1, 1 + 0.06 * sin(t * 3 % 1, k * 0.3)], 4.0, 16)}
             for i, (a, b) in enumerate((("r", "f"), ("l", "f"), ("r", "b"), ("l", "b")))}
    banners = {f"banner_{s}": {"rotation": track(lambda t, ph=ph: [2.5 * sin(t, ph), 0, 1.2 * sin(t, ph + 0.25)], 4.0, 16)}
               for s, ph in (("right", 0.0), ("left", 0.4))}
    idle = {"cog": {"rotation": track(lambda t: [0, 0, 360 * t], 40.0, 16)},
            "hearth_fire": {"scale": track(lambda t: [1, 0.55 + 0.05 * sin(t * 2 % 1), 1], 4.0, 16)},
            "ingot": {"scale": [0, 0, 0]},
            **lamps, **banners}
    # работа: молоты бьют по очереди, горн пылает, шестерня вращается быстрее, раскалённая заготовка на наковальне
    L = 1.6

    def strike(sx, ph):
        pts = []
        for i in range(17):
            t = i / 16
            u = (t - ph) % 1
            # замах медленно, удар быстро, отскок
            if u < 0.55:
                a = -12 * (u / 0.55)
            elif u < 0.62:
                a = -12 + 46 * ((u - 0.55) / 0.07)
            elif u < 0.7:
                a = 34 - 6 * ((u - 0.62) / 0.08)
            else:
                a = 28 * (1 - (u - 0.7) / 0.3)
            pts.append((round(t * L, 4), [0, 0, -sx * a * 0.5]))
        return keys(pts)

    def strike2(sx, ph):
        pts = []
        for i in range(17):
            t = i / 16
            u = (t - ph) % 1
            a = 0 if u < 0.55 else (40 if u < 0.7 else 40 * (1 - (u - 0.7) / 0.3))
            pts.append((round(t * L, 4), [0, 0, sx * a]))
        return keys(pts)

    work = {"cog": {"rotation": track(lambda t: [0, 0, 360 * t], 8.0, 16)},
            "hearth_fire": {"scale": track(lambda t: [1 + 0.05 * sin(t * 4 % 1), 1.05 + 0.12 * sin(t * 2 % 1), 1], L, 16)},
            "arm_right": {"rotation": strike(-1, 0.0)}, "arm_left": {"rotation": strike(1, 0.5)},
            "arm_right_2": {"rotation": strike2(-1, 0.0)}, "arm_left_2": {"rotation": strike2(1, 0.5)},
            "ingot": {"scale": track(lambda t: [1, 1 + 0.15 * max(0, sin(t * 2 % 1)), 1], L, 16)},
            **lamps, **banners}
    anims = {"misc.idle": {"length": 40.0, "loop": True, "bones": idle},
             "work.active": {"length": L, "loop": True, "bones": work}}
    finish(m, "mechanicus_forge", KUZNYA, anims)


# ------------------------------------------------------------------ оборудование корабля (крупные модели в отсеках)
# Модель рисует ядро-блок отсека; соседние клетки заняты невидимыми частями (tools/ship/gen_interior.py).

SHIP = dict(FORGE, hull=(78, 84, 96), metal=(112, 118, 130), dark=(40, 42, 50), steel=(160, 166, 176),
            glow=(110, 200, 255), glow2=(255, 140, 40), glow3=(120, 255, 140), screen=(10, 16, 24),
            parchment=(214, 200, 160), wax=(120, 18, 22), stone=(70, 72, 78), brass=(186, 146, 54))
MATERIALS["hd_hull"] = hd.hd_metal("hull")
MATERIALS["hd_blue"] = MATERIALS["hd_glow"]
MATERIALS["hd_red"] = hd.mat_glow("red")


def hd_vent(region, face, pal, rng):
    """Решётка: тёмные щели и светлые ламели."""
    h, w = hd._base(region, pal["dark"], face, rng, amp=4, cell=4, grain=3)
    for y in range(1, h - 1, 3):
        region[y, 1:-1, :3] = shade(pal["dark"], 0.35)
        if y + 1 < h:
            region[y + 1, 1:-1, :3] = shade(pal["dark"], 1.4)
    hd.bevel(region, 1.2, 0.6)


MATERIALS["hd_vent"] = hd_vent
MATERIALS["hd_glow3"] = hd.mat_glow("glow3")
SHIP["red"] = (255, 70, 50)


def radar(region, S, pal):
    """Экран ауспика: круги, сектор развёртки, засветки."""
    import math
    h, w = region.shape[:2]
    cx, cy, R = (w - 1) / 2, (h - 1) / 2, min(w, h) / 2 - 0.5
    region[..., :3] = (6, 18, 10)
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - cx, y - cy)
            a = math.atan2(y - cy, x - cx)
            if abs(d - R * 0.95) < 0.6 or abs(d - R * 0.6) < 0.5 or abs(d - R * 0.3) < 0.5 or abs(x - cx) < 0.5 or abs(y - cy) < 0.5:
                region[y, x, :3] = (40, 140, 70)
            if d < R and 0 < (a + 0.4) % (2 * math.pi) < 0.6:
                region[y, x, :3] = (60, 200, 100)
    for (x, y) in ((cx + R * 0.4, cy - R * 0.2), (cx - R * 0.5, cy + R * 0.35)):
        region[int(y), int(x), :3] = pal["glow3"]


def starmap(region, S, pal):
    """Звёздная карта стола: сетка, звёзды, маршрут."""
    import random
    rng = random.Random(9)
    h, w = region.shape[:2]
    region[..., :3] = (6, 12, 24)
    for x in range(0, w, 6):
        region[:, x, :3] = (14, 34, 60)
    for y in range(0, h, 6):
        region[y, :, :3] = (14, 34, 60)
    pts = []
    for _ in range(w * h // 40):
        x, y = rng.randrange(w), rng.randrange(h)
        region[y, x, :3] = (200, 230, 255) if rng.random() < 0.3 else (90, 160, 230)
        pts.append((x, y))
    for (x0, y0), (x1, y1) in zip(pts[:5], pts[1:6]):  # пунктир маршрута
        for t in range(0, 20, 2):
            x, y = int(x0 + (x1 - x0) * t / 20), int(y0 + (y1 - y0) * t / 20)
            region[y, x, :3] = pal["glow2"]


def runic_circle(region, S, pal):
    """Круг телепортариума: два кольца и знаки между ними."""
    import math
    h, w = region.shape[:2]
    cx, cy, R = (w - 1) / 2, (h - 1) / 2, min(w, h) / 2 - 1
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - cx, y - cy)
            a = math.atan2(y - cy, x - cx)
            if abs(d - R) < 0.8 or abs(d - R * 0.78) < 0.7 or abs(d - R * 0.25) < 0.7:
                region[y, x, :3] = pal["glow"]
            elif R * 0.8 < d < R * 0.97 and int((a + math.pi) / (2 * math.pi) * 24) % 2 == 0 and abs(math.sin(a * 24)) < 0.35:
                region[y, x, :3] = pal["glow"]


def lit_glow(g, region, face, S, pal):
    """Светятся только яркие пиксели грани (линии экранов и кругов)."""
    m = region[..., :3].max(axis=2) > 100
    g[m, :3] = region[m, :3]
    g[m, 3] = 255


# ------------------------------------------------------------------ исполинские машины крейсера (16 px на блок)
# Реактор 7×7×19, варп-двигатель 11×13×5, генератор Поля Геллера 3×3×7: размеры «как в лоре» — машина-собор,
# у которой человек — по колено. Текстура 1 px на пиксель модели (S=1), иначе атлас не влезет.

SHIP.update(banner=(112, 14, 18), banner_dk=(70, 8, 12), gold=(214, 170, 66), warp1=(70, 110, 255),
            warp2=(176, 70, 255), warp3=(20, 10, 60), skull=(214, 204, 176), oil=(24, 22, 20))
MATERIALS["hd_banner"] = hd.hd_cloth("banner", hem="gold")
MATERIALS["hd_gold"] = hd.hd_brass("gold")


def warp_swirl(region, S, pal):
    """Воронка варпа: спиральные рукава синего и фиолетового, тёмный глаз в центре; прозрачные зазоры."""
    h, w = region.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = (w - 1) / 2, (h - 1) / 2
    r = np.hypot(xx - cx, yy - cy) / (min(w, h) / 2)
    a = np.arctan2(yy - cy, xx - cx)
    arm = 0.5 + 0.5 * np.sin(a * 3 + r * 9)
    c1, c2, c3 = (np.array(pal[k], np.float32) for k in ("warp1", "warp2", "warp3"))
    col = c1 * arm[..., None] + c2 * (1 - arm[..., None])
    col = col * (1 - np.clip(1 - r * 3, 0, 1))[..., None] + c3 * np.clip(1 - r * 3, 0, 1)[..., None]
    col = np.clip(col * (0.7 + 0.6 * arm[..., None]), 0, 255)
    region[..., :3] = col.astype(np.uint8)
    region[..., 3] = np.where((arm > 0.35) & (r < 1.0) | (r < 0.35), 255, 0).astype(np.uint8)


def rune_face(region, S, pal):
    """Светящаяся руна Механикус: шестерня из штрихов."""
    h, w = region.shape[:2]
    region[..., :3] = pal["dark"]
    region[1:-1, w // 2 - 1:w // 2 + 1, :3] = pal["glow"]
    region[h // 2 - 1:h // 2 + 1, 1:-1, :3] = pal["glow"]
    region[1, 1:-1, :3] = pal["glow"]
    region[-2, 1:-1, :3] = pal["glow"]


def skull_face(region, S, pal):
    """Череп спереди: глазницы и зубы."""
    h, w = region.shape[:2]
    region[..., :3] = pal["skull"]
    ew = max(1, w // 4)
    region[h // 3:h // 3 + max(1, h // 4), w // 5:w // 5 + ew, :3] = (30, 26, 22)
    region[h // 3:h // 3 + max(1, h // 4), w - w // 5 - ew:w - w // 5, :3] = (30, 26, 22)
    region[h - h // 4:h - 1, w // 3:w - w // 3, :3] = (90, 84, 70)
    region[h - h // 4:h - 1, w // 3:w - w // 3:2, :3] = (30, 26, 22)


def octagon(bone, origin_xz, y, size, h, mat, **kw):
    """Восьмигранная призма: квадрат и такой же, повёрнутый на 45°."""
    cx, cz = origin_xz
    bone.cube([cx - size / 2, y, cz - size / 2], [size, h, size], mat, **kw)
    bone.cube([cx - size / 2, y, cz - size / 2], [size, h, size], mat, rotation=[0, 45, 0], pivot=[cx, y, cz], **kw)


def seal(bone, x, y, z, face_z=-1):
    """Печать чистоты: восковая печать и свисающий пергамент."""
    bone.cube([x, y - 10, z], [5, 12, 0.5], "hd_parchment")
    bone.cube([x + 0.5, y, z - 1.5 * face_z], [4, 4, 2], "hd_wax")   # при S=1 тоньше 2 px воск не рисуется


def reactor_core():
    m = Model("reactor_core", S=1, atlas_w=1024)
    root = m.bone("reactor", [0, 0, 0])
    # цоколь: восьмигранник 7 блоков, кромка опасности, ступени к пульту
    octagon(root, (0, 0), 0, 104, 12, "hd_dark")
    root.cube([-50, 12, -50], [100, 1, 100], "hd_dark", deco={"up": hazard})
    octagon(root, (0, 0), 13, 76, 6, "hd_hull")
    root.cube([-20, 0, -60], [40, 6, 8], "hd_dark")
    # сосуд удержания: восьмигранник 4 блока, тяжёлые плиты брони, между плитами — щели с плазмой
    octagon(root, (0, 0), 19, 64, 92, "hd_hull")
    for k in range(8):
        rot = dict(rotation=[0, k * 45, 0], pivot=[0, 0, 0])
        root.cube([-15, 24, -36], [12, 82, 5], "hd_rusty" if k % 3 else "hd_dark", **rot)
        root.cube([3, 24, -36], [12, 82, 5], "hd_rusty" if k % 3 else "hd_dark", **rot)
        root.cube([-3, 28, -35], [6, 74, 1], "hd_fire", glow="all", **rot)
        for y in (30, 54, 78, 100):                       # заклёпанные стяжки поперёк щели
            root.cube([-4, y, -37], [8, 2, 2], "hd_brass", **rot)
    root.cube([-16, 40, -38], [32, 44, 4], "hd_brass")                 # смотровое окно в ядро
    root.cube([-12, 44, -39], [24, 36, 1], "hd_fire", glow="all")
    for x in (-5, 3):
        root.cube([x, 44, -40], [2, 36, 1], "hd_dark")
    plasma = m.bone("plasma", [0, 64, 0], "reactor")
    plasma.cube([-26, 22, -26], [52, 86, 52], "hd_fire", glow="all")
    for y in (19, 62, 108):
        octagon(root, (0, 0), y, 72, 5, "hd_brass")
    # гидравлические тараны на диагоналях: цилиндр, шток (качается), упор в венец
    for i, (sx, sz) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        x, z = sx * 42, sz * 42
        root.cube([x - 9, 13, z - 9], [18, 44, 18], "hd_dark")
        root.cube([x - 10, 30, z - 10], [20, 3, 20], "hd_brass")
        rod = m.bone(f"ram_{i + 1}", [x, 57, z], "reactor")
        rod.cube([x - 4, 57, z - 4], [8, 40, 8], "hd_steel")
        rod.cube([x - 9, 97, z - 9], [18, 10, 18], "hd_dark")
    # три кольца удержания, вращаются в разные стороны
    for i, y in enumerate((34, 90)):
        ring = m.bone(f"ring_{i + 1}", [0, y, 0], "reactor")
        r = 41
        for rot in (0, 90, 180, 270):
            ring.cube([-r, y - 5, -r - 5], [2 * r, 10, 6], "hd_dark", rotation=[0, rot, 0], pivot=[0, y, 0])
            ring.cube([-r, y - 1, -r - 5.5], [2 * r, 2, 0.5], "hd_brass", rotation=[0, rot, 0], pivot=[0, y, 0])
            ring.cube([-4, y - 6, -r - 8], [8, 12, 3], "hd_blue", glow="all", rotation=[0, rot + 45, 0], pivot=[0, y, 0])
    # венец: ступени, восемь рёбер-радиаторов, купол, вытяжная труба до потолка отсека
    octagon(root, (0, 0), 111, 84, 10, "hd_dark")
    for k in range(8):
        root.cube([-3, 121, -52], [6, 32, 30], "hd_dark", rotation=[0, k * 45 + 22.5, 0], pivot=[0, 0, 0])
        root.cube([-3.5, 152, -52], [7, 2, 30], "hd_brass", rotation=[0, k * 45 + 22.5, 0], pivot=[0, 0, 0])
    octagon(root, (0, 0), 121, 60, 26, "hd_hull")
    octagon(root, (0, 0), 147, 64, 4, "hd_brass")
    octagon(root, (0, 0), 151, 44, 10, "hd_dark")
    octagon(root, (0, 0), 161, 28, 8, "hd_hull")
    octagon(root, (0, 0), 169, 30, 135, "hd_rusty")
    for y in range(184, 300, 30):
        octagon(root, (0, 0), y, 36, 5, "hd_dark")
        octagon(root, (0, 0), y + 1, 37, 2, "hd_brass")
    for sx in (-1, 1):
        root.cube([sx * 26 - 5, 161, -5], [10, 143, 10], "hd_rusty")
        for y in (200, 250):
            root.cube([sx * 26 - 6, y, -6], [12, 4, 12], "hd_brass")
    vent = m.bone("vent", [0, 170, 0], "reactor")
    vent.cube([-8, 172, -16], [16, 8, 0.5], "hd_fire", glow="all")
    # четыре магистрали охладителя: от цоколя в венец
    for rot in (0, 90, 180, 270):
        kw = dict(rotation=[0, rot, 0], pivot=[0, 0, 0])
        root.cube([-6, 13, -52], [12, 100, 12], "hd_rusty", **kw)
        for y in (24, 56, 88):
            root.cube([-7, y, -53], [14, 4, 14], "hd_brass", **kw)
        root.cube([-6, 105, -52], [12, 12, 22], "hd_rusty", **kw)
    # лицевая сторона: пульт, знак Механикус, черепа, печати
    root.cube([-16, 6, -64], [32, 18, 10], "hd_dark")
    root.cube([-14, 22, -62], [28, 10, 3], "hd_screen", deco={"north": screen_text}, glow=screen_glow,
              rotation=[-30, 0, 0], pivot=[0, 22, -60])
    for x in (-24, 18):
        root.cube([x, 10, -60], [6, 6, 1], "hd_dark", deco={"north": gauge})
    root.cube([-14, 60, -42], [28, 28, 2], "hd_brass", deco={"north": emblem(0.45)})
    for x in (-30, 24):
        root.cube([x, 112, -44], [6, 7, 6], "hd_bone", deco={"north": skull_face})
    seal(root, 7, 54, -42)
    seal(root, -13, 96, -42)
    for x in (-40, -20, 18, 38):
        root.cube([x, 12, -66], [3, 2, 130], "hd_cable")
    anims = {"misc.idle": {"length": 8.0, "loop": True, "bones": {
        "plasma": {"scale": track(lambda t: [1 + 0.05 * sin(t * 4 % 1), 1, 1 + 0.05 * sin(t * 4 % 1)], 8.0, 32)},
        "ring_1": {"rotation": track(lambda t: [0, 360 * t, 0], 8.0, 24)},
        "ring_2": {"rotation": track(lambda t: [0, -360 * t, 0], 8.0, 24)},
        "vent": {"scale": track(lambda t: [1, 1 + 0.5 * max(0.0, sin(t * 4 % 1)), 1], 8.0, 32)},
        **{f"ram_{i + 1}": {"position": track(lambda t, i=i: [0, -6 * max(0.0, sin((t * 2 + i / 4) % 1)), 0], 8.0, 32)}
           for i in range(4)},
    }}}
    finish(m, "reactor_core", SHIP, anims)


def geller_node():
    m = Model("geller_node", S=1, atlas_w=512)
    root = m.bone("node", [0, 0, 0])
    # основание 3×3 с кромкой опасности и стойками по углам
    root.cube([-24, 0, -24], [48, 10, 48], "hd_dark")
    root.cube([-23, 10, -23], [46, 1, 46], "hd_dark", deco={"up": hazard})
    root.cube([-19, 11, -19], [38, 6, 38], "hd_hull")
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * 18, sz * 18
            root.cube([x - 4, 11, z - 4], [8, 70, 8], "hd_hull")
            for y in (24, 48, 72):
                root.cube([x - 5, y, z - 5], [10, 3, 10], "hd_brass")
    # колонна-восьмигранник с синими рунами
    octagon(root, (0, 0), 17, 20, 62, "hd_hull")
    for k in range(8):
        root.cube([-1, 22, -10.6], [2, 52, 1], "hd_blue", glow="all", rotation=[0, k * 45, 0], pivot=[0, 0, 0])
    # катушки: четыре кольца вокруг колонны, крутятся навстречу друг другу
    for i, y in enumerate((28, 40, 52, 64)):
        coil = m.bone(f"coil_{i + 1}", [0, y, 0], "node")
        for rot in (0, 90, 180, 270):
            coil.cube([-14, y - 2, -15], [28, 4, 3], "hd_brass" if i % 2 else "hd_steel", rotation=[0, rot, 0], pivot=[0, y, 0])
        coil.cube([-2, y - 2.5, -17], [4, 5, 2], "hd_blue", glow="all")
    # площадка и когти, держащие кристалл
    root.cube([-20, 79, -20], [40, 6, 40], "hd_dark")
    root.cube([-21, 82, -21], [42, 2, 42], "hd_brass")
    for k in range(4):
        root.cube([-2, 85, -18], [4, 30, 4], "hd_brass", rotation=[-22, k * 90 + 45, 0], pivot=[0, 85, 0])
    crystal = m.bone("crystal", [0, 100, 0], "node")
    crystal.cube([-7, 90, -7], [14, 20, 14], "hd_blue", glow="all", rotation=[0, 45, 0], pivot=[0, 100, 0])
    crystal.cube([-4, 86, -4], [8, 28, 8], "hd_blue", glow="all")
    halo = m.bone("field", [0, 100, 0], "node")
    for rot in (0, 60, 120):
        halo.cube([-24, 99.5, -0.5], [48, 1, 1], "hd_blue", glow="all", rotation=[0, rot, 0], pivot=[0, 100, 0])
    # дуги разрядов от стоек к кристаллу: мерцают
    arcs = m.bone("arcs", [0, 81, 0], "node")
    for k in range(4):
        arcs.cube([-0.5, 81, -24], [1, 1, 22], "hd_blue", glow="all", rotation=[38, k * 90 + 45, 0], pivot=[0, 81, 0])
    # кабели, череп, печать
    for x in (-10, 6):
        root.cube([x, 0, 20], [3, 3, 8], "hd_cable")
    root.cube([-4, 30, -14], [8, 9, 6], "hd_bone", deco={"north": skull_face})
    seal(root, 5, 60, -11)
    anims = {"misc.idle": {"length": 4.0, "loop": True, "bones": {
        "crystal": {"rotation": track(lambda t: [0, 360 * t, 0], 4.0, 16),
                    "position": track(lambda t: [0, 2 * sin(t), 0], 4.0, 16)},
        "field": {"rotation": track(lambda t: [0, -720 * t, 0], 4.0, 16),
                  "scale": track(lambda t: [1 + 0.2 * sin(t * 2 % 1), 1, 1 + 0.2 * sin(t * 2 % 1)], 4.0, 16)},
        **{f"coil_{i + 1}": {"rotation": track(lambda t, i=i: [0, (1 if i % 2 else -1) * 360 * t, 0], 4.0, 16)} for i in range(4)},
        "arcs": {"scale": keys([(t / 10, [1, 1, 1] if k % 3 else [0, 0, 0]) for k, t in enumerate(range(0, 41))])},
    }}}
    finish(m, "geller_node", SHIP, anims)


def warp_drive():
    m = Model("warp_drive", S=1, atlas_w=1024)
    root = m.bone("drive", [0, 0, 0])
    cy = 104                                            # центр воронки
    # станина и задняя стена машины
    root.cube([-88, 0, -40], [176, 14, 80], "hd_hull")
    root.cube([-86, 14, -40], [172, 1, 6], "hd_dark", deco={"up": hazard})
    root.cube([-88, 14, 18], [176, 194, 22], "hd_dark")
    # восьмигранная рама врат: восемь брусьев вокруг оси Z
    for k in range(8):
        root.cube([-33, cy - 80, -14], [66, 28, 32], "hd_rusty" if k % 2 else "hd_hull",
                  rotation=[0, 0, k * 45], pivot=[0, cy, 0])
        root.cube([-6, cy - 84, -16], [12, 10, 34], "hd_brass", rotation=[0, 0, k * 45 + 22.5], pivot=[0, cy, 0])
    # воронка варпа: два диска крутятся навстречу, кольцо рун — в третью сторону
    vortex = m.bone("vortex", [0, cy, 0], "drive")
    vortex.cube([-54, cy - 54, 6], [108, 108, 1], "hd_blue", glow="all", deco={"north": warp_swirl})
    vortex2 = m.bone("vortex2", [0, cy, 0], "drive")
    vortex2.cube([-50, cy - 50, 2], [100, 100, 1], "hd_blue", glow="all", deco={"north": warp_swirl},
                 rotation=[0, 0, 45], pivot=[0, cy, 0])
    runes = m.bone("runes", [0, cy, 0], "drive")
    for k in range(16):
        runes.cube([-4, cy + 60, -16], [8, 12, 2], "hd_dark", glow=lit_glow, deco={"north": rune_face},
                   rotation=[0, 0, k * 22.5], pivot=[0, cy, 0])
    # колонны-цилиндры по бокам: корпус, латунные пояса, штоки качаются
    for i, sx in enumerate((-1, 1)):
        x = sx * 76
        root.cube([x - 12, 14, -30], [24, 170, 26], "hd_dark")
        for y in (30, 70, 110, 150):
            root.cube([x - 13, y, -31], [26, 5, 28], "hd_brass")
        piston = m.bone(f"piston_{i + 1}", [x, 184, -17], "drive")
        piston.cube([x - 5, 184, -22], [10, 18, 10], "hd_steel")
        piston.cube([x - 10, 200, -26], [20, 8, 18], "hd_dark")
    # магистрали к раме, верхняя балка с черепом и знаком Механикус
    for sx in (-1, 1):
        root.cube([sx * 54 - 6, 14, -26], [12, 40, 12], "hd_rusty")
        root.cube([sx * 54 - 7, 40, -27], [14, 4, 14], "hd_brass")
    root.cube([-80, 190, -24], [160, 18, 42], "hd_hull")
    root.cube([-26, 186, -28], [52, 40, 6], "hd_brass", deco={"north": emblem(0.48)})
    root.cube([-6, 170, -30], [12, 13, 10], "hd_bone", deco={"north": skull_face})
    seal(root, -70, 120, -31)
    seal(root, 64, 96, -31)
    for x in (-60, -30, 26, 56):
        root.cube([x, 14, -42], [3, 2, 50], "hd_cable")
    anims = {"misc.idle": {"length": 6.0, "loop": True, "bones": {
        "vortex": {"rotation": track(lambda t: [0, 0, -360 * t], 6.0, 24)},
        "vortex2": {"rotation": track(lambda t: [0, 0, 720 * t], 6.0, 24),
                    "scale": track(lambda t: [1 + 0.04 * sin(t * 3 % 1), 1 + 0.04 * sin(t * 3 % 1), 1], 6.0, 24)},
        "runes": {"rotation": track(lambda t: [0, 0, 180 * t], 6.0, 24)},
        "piston_1": {"position": track(lambda t: [0, -8 * max(0.0, sin(t * 2 % 1)), 0], 6.0, 24)},
        "piston_2": {"position": track(lambda t: [0, -8 * max(0.0, sin((t * 2 + 0.5) % 1)), 0], 6.0, 24)},
    }}}
    finish(m, "warp_drive", SHIP, anims)


FLAG = os.path.join(os.path.dirname(__file__), "ref", "imperial_flag.png")   # флаг от автора: аквила, «I», череп


def flag_cloth(region, S, pal):
    """Полотнище штандарта по флагу автора: светлое поле, тёмно-красная кайма, фестоны сверху, три косицы снизу;
    эмблема (чёрная аквила, красная «I», череп) переносится с картинки как есть — чёрное и красное, белое = поле."""
    from PIL import Image
    h, w = region.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    region[..., :3] = pal["cloth"]
    region[..., 3] = 255
    # лёгкая неровность ткани: тени складок по вертикали
    fold = (0.93 + 0.07 * np.sin(xx / w * np.pi * 6))[..., None]
    region[..., :3] = (region[..., :3] * fold).astype(np.uint8)
    # кайма
    b = max(2, w // 24)
    edge = (xx < b) | (xx >= w - b) | (yy < b + h // 32)
    region[edge, :3] = pal["banner"]
    # фестоны по верху: полукруглые вырезы между петлями
    loops = 5
    for k in range(loops):
        cx = (k + 0.5) * w / loops
        cut = ((xx - cx) ** 2 + (yy * 1.6) ** 2) < (w / loops * 0.32) ** 2
        region[cut & (yy < h // 16), 3] = 0
    # три косицы снизу: треугольные вырезы
    tail = int(h * 0.16)
    third = w / 3
    for k in range(3):
        x0 = k * third
        local = (xx - x0) / third                     # 0..1 в пределах косицы
        depth = (1 - np.abs(local - 0.5) * 2) * tail  # острие в середине косицы
        cut = (yy > h - tail + depth) & (xx >= x0) & (xx < x0 + third)
        region[cut, 3] = 0
        region[(yy > h - tail - b) & (yy <= h - tail + depth) & (yy > h - tail + depth - b) & (xx >= x0) & (xx < x0 + third), :3] = pal["banner"]
    for k in (1, 2):                                   # шов между косицами
        x = int(k * third)
        region[h - tail:, max(0, x - 1):x + 1, :3] = pal["banner_dk"]
    # эмблема: картинка, вписанная по ширине поля в верхнюю половину
    src = Image.open(FLAG).convert("RGBA")
    ew = int(w * 0.96)
    eh = int(src.height * ew / src.width)
    em = np.asarray(src.resize((ew, eh), Image.LANCZOS)).astype(np.int32)
    ox, oy = (w - ew) // 2, max(b + h // 16, (h - tail - eh) // 2 + h // 40)
    lum = em[..., :3].sum(axis=2)
    ink = (em[..., 3] > 100) & (lum < 600)            # не белое
    sub = region[oy:oy + eh, ox:ox + ew]
    ink = ink[:sub.shape[0], :sub.shape[1]]
    sub[ink, :3] = em[:sub.shape[0], :sub.shape[1]][ink, :3].astype(np.uint8)


def imperial_standard(pole):
    """Штандарт: навершие-аквила, перекладина, полотнище 2.25×1.5 блока — флаг автора в его пропорциях.
    Настенный — на кронштейне (полотнище свисает от блока вниз), напольный — на древке."""
    name = "imperial_standard_pole" if pole else "imperial_standard"
    m = Model(name, S=4, atlas_w=128)
    pal = dict(SHIP, cloth=(226, 218, 200))
    root = m.bone("standard", [0, 0, 0])
    top = 14 if not pole else 64
    z = -2
    if pole:
        root.cube([-6, 0, -6], [12, 3, 12], "hd_dark")
        root.cube([-5, 3, -5], [10, 2, 10], "hd_brass")
        root.cube([-1.5, 5, -1.5], [3, top + 4, 3], "hd_dark")
        for y in (22, 44):
            root.cube([-2.5, y, -2.5], [5, 2, 5], "hd_brass")
    else:
        root.cube([-4, top - 6, 6], [8, 10, 2], "hd_dark")            # кронштейн у стены
        root.cube([-1.5, top - 1, -1], [3, 3, 8], "hd_dark")
        root.cube([-1.5, top + 2, -1.5], [3, 3, 3], "hd_dark")
    root.cube([-20, top, z - 1], [40, 2, 2], "hd_dark")              # перекладина с латунными наконечниками
    for x in (-22, 19):
        root.cube([x, top - 1, z - 1.5], [3, 4, 3], "hd_brass")
    # навершие: серая аквила над перекладиной (тело, две головы, крылья ступенями)
    ay = top + 4
    root.cube([-1.5, top + 2, z - 1], [3, 3, 2], "hd_steel")
    root.cube([-2, ay, z - 1], [4, 6, 2], "hd_steel")
    for sx in (-1, 1):
        root.cube([sx * 2.5 - 1, ay + 5, z - 1], [2, 2, 2], "hd_steel")   # головы
        for i, (w_, h_, y_) in enumerate(((5, 4, 2), (5, 3, 3.5), (4, 2, 5))):
            x = sx * (2 + i * 4) - (w_ if sx < 0 else 0)
            root.cube([x, ay + y_ - 1, z - 0.75], [w_, h_, 1.5], "hd_steel")
    cloth = m.bone("cloth", [0, top, z], "standard")
    cloth.cube([-18, top - 24, z - 0.5], [36, 24, 1], "hd_banner", deco={"north": flag_cloth, "south": flag_cloth})
    anims = {"misc.idle": {"length": 6.0, "loop": True, "bones": {
        "cloth": {"rotation": track(lambda t: [2.0 * sin(t), 0, 0.8 * sin(t, 0.25)], 6.0, 24)},
    }}}
    finish(m, name, pal, anims)


# ------------------------------------------------------------------ варп-пробоотборник анклава Механикус (5×2×4)
# Стол со стенкой: аквила, черепа, пробирки, контейнеры; в стене — порт в варп. Рука Механикус берёт пустую колбу
# с подставки, вставляет в порт на 20 с и достаёт колбу с красной варп-материей (WarpSamplerBlockEntity: те же 33 с).

SHIP["glassy"] = (176, 204, 212)
MATERIALS["hd_glassy"] = hd.hd_flat("glassy", 4)
SAMPLER_S = (16, 23, -12)          # плечо руки
SAMPLER_L1, SAMPLER_L2 = 18, 20    # плечо → локоть, локоть → центр колбы в захвате
# Знаки поворотов в ключах: наклон (X) — как в предпросмотре Blender, поворот основания (Y) — обратный:
# в игре GeckoLib отражает модель по X относительно предпросмотра (проверено по снимкам цикла в анклаве)
SX, SY = -1, 1


def sampler_ik(t):
    """Углы (поворот основания, плечо, локоть) в градусах, чтобы центр колбы в захвате пришёл в точку t."""
    sx, sy, sz = SAMPLER_S
    hx, hz, v = t[0] - sx, t[2] - sz, t[1] - sy
    d = math.hypot(hx, hz)
    yaw = math.degrees(math.atan2(-hx, -hz))
    r = min(math.hypot(d, v), SAMPLER_L1 + SAMPLER_L2 - 0.01)
    alpha = math.atan2(d, v)
    beta = math.acos((SAMPLER_L1 ** 2 + r ** 2 - SAMPLER_L2 ** 2) / (2 * SAMPLER_L1 * r))
    gamma = math.acos((SAMPLER_L1 ** 2 + SAMPLER_L2 ** 2 - r ** 2) / (2 * SAMPLER_L1 * SAMPLER_L2))
    return yaw, math.degrees(alpha - beta), math.degrees(math.pi - gamma)


def warp_sampler():
    m = Model("warp_sampler", S=2, atlas_w=512)
    root = m.bone("sampler", [0, 0, 0])
    # стол: столешница, латунная кромка, ножки, нижняя полка с ящиками
    root.cube([-40, 14, -24], [80, 3, 32], "hd_dark")
    root.cube([-40, 16.5, -24.5], [80, 1, 1], "hd_brass")
    for x in (-39, 35):
        for z in (-23, 3):
            root.cube([x, 0, z], [4, 14, 4], "hd_dark")
    root.cube([-38, 4, -22], [76, 2, 28], "hd_hull")
    for x, w in ((-34, 12), (-18, 10), (20, 14)):
        root.cube([x, 6, -18], [w, 8, 14], "hd_rusty")
        root.cube([x - 0.5, 9, -18.5], [w + 1, 1, 15], "hd_brass")
    # задняя стенка: пилястры, карниз, аквила, черепа, экран когитатора
    root.cube([-40, 17, 2], [80, 48, 6], "hd_hull")
    for x in (-42, 36):
        root.cube([x, 14, 0], [6, 54, 8], "hd_dark")
        root.cube([x - 0.5, 62, -1], [7, 4, 9], "hd_brass")
    root.cube([-42, 64, -2], [84, 4, 10], "hd_dark")
    root.cube([-18, 50, 1], [36, 12, 1], "hd_gold", deco={"north": lambda r, S, p: __import__("gen_blocks").aquila(r, S, dict(p, brass=p["gold"]))})
    for x in (-30, 24):
        root.cube([x, 50, -2], [6, 7, 4], "hd_bone", deco={"north": skull_face})
    root.cube([-36, 24, 1], [14, 10, 1], "hd_screen", deco={"north": screen_text}, glow=screen_glow)
    root.cube([22, 22, 1], [12, 14, 1], "hd_dark", deco={"north": gauge})
    seal(root, 14, 46, 1.5)
    # порт в варп: восьмигранное латунное кольцо, тёмный зев, красное свечение изнутри
    cy = 36
    for k in range(8):
        root.cube([-4.5, cy - 11, -3], [9, 4, 6], "hd_brass", rotation=[0, 0, k * 45], pivot=[0, cy, 0])
    root.cube([-7, cy - 7, 1], [14, 14, 1], "hd_dark_plain")
    port = m.bone("port_glow", [0, cy, 1], "sampler")
    port.cube([-6, cy - 6, 0.5], [12, 12, 0.5], "hd_red", glow="all")
    for k in range(8):
        root.cube([-1, cy - 15, -1.5], [2, 3, 1], "hd_dark", glow=lit_glow, deco={"north": rune_face},
                  rotation=[0, 0, k * 45 + 22.5], pivot=[0, cy, 0])
    # подставка с колбами: пустая — для пробы, рядом пара готовых и зелёный реагент
    root.cube([-20, 17, -16], [16, 2, 8], "hd_brass")
    root.cube([-20, 23, -15], [16, 1, 1], "hd_brass")

    def vial(bone, x, z, mat, glow=None):
        bone.cube([x - 1.5, 19, z - 1.5], [3, 8, 3], mat, glow=glow)
        bone.cube([x - 2, 27, z - 2], [4, 2, 4], "hd_brass")
    vial(root, -18, -12, "hd_glassy")
    vial(root, -6, -12, "hd_glow3", glow="all")
    rack = m.bone("vial_rack", [-12, 19, -12], "sampler")
    vial(rack, -12, -12, "hd_glassy")
    red_rack = m.bone("vial_red_rack", [-12, 19, -12], "sampler")
    vial(red_rack, -12, -12, "hd_red", glow="all")
    # контейнеры, свитки кабелей, свеча
    root.cube([26, 17, -6], [9, 12, 9], "hd_rusty")
    for y in (19, 26):
        root.cube([25.5, y, -6.5], [10, 1, 10], "hd_brass")
    root.cube([28, 29, -4], [5, 2, 5], "hd_dark")
    root.cube([-34, 17, -8], [8, 5, 8], "hd_dark")
    root.cube([-33, 22, -7], [6, 1, 6], "hd_glow3", glow="all")
    for x in (-28, 6):
        root.cube([x, 17, -22], [3, 1.5, 20], "hd_cable")
    # рука Механикус: основание на столе, поворотная колонна, плечо, предплечье, захват с колбой
    sx, sy, sz = SAMPLER_S
    root.cube([sx - 5, 17, sz - 5], [10, 3, 10], "hd_dark")
    arm = m.bone("arm", [sx, 20, sz], "sampler")
    arm.cube([sx - 3, 20, sz - 3], [6, 3, 6], "hd_brass")
    upper = m.bone("upper", [sx, sy, sz], "arm")
    upper.cube([sx - 3, sy - 3, sz - 3], [6, 6, 6], "hd_dark")
    upper.cube([sx - 2, sy, sz - 2], [4, SAMPLER_L1, 4], "hd_steel")
    upper.cube([sx - 2.5, sy + 6, sz - 2.5], [5, 2, 5], "hd_brass")
    upper.cube([sx + 2, sy + 2, sz - 0.5], [1, SAMPLER_L1 - 4, 1], "hd_cable")
    ey = sy + SAMPLER_L1
    fore = m.bone("fore", [sx, ey, sz], "upper")
    fore.cube([sx - 2.5, ey - 2.5, sz - 2.5], [5, 5, 5], "hd_brass")
    fore.cube([sx - 1.5, ey, sz - 1.5], [3, 14, 3], "hd_steel")
    fore.cube([sx - 3, ey + 14, sz - 3], [6, 2, 6], "hd_dark")
    for dx in (-3, 2):                                    # пальцы захвата
        fore.cube([sx + dx, ey + 15, sz - 1], [1, 8, 2], "hd_brass")
    held = m.bone("vial_claw", [sx, ey + 16, sz], "fore")
    held.cube([sx - 1.5, ey + 16, sz - 1.5], [3, 8, 3], "hd_glassy")
    held.cube([sx - 2, ey + 14.5, sz - 2], [4, 2, 4], "hd_brass")
    held_red = m.bone("vial_claw_red", [sx, ey + 16, sz], "fore")
    held_red.cube([sx - 1.5, ey + 16, sz - 1.5], [3, 8, 3], "hd_red", glow="all")
    held_red.cube([sx - 2, ey + 14.5, sz - 2], [4, 2, 4], "hd_brass")

    # ---- анимации: позы руки из обратной кинематики
    rest = (16, 48, -20)
    rack_up, rack_at = (-12, 35, -12), (-12, 26, -12)
    port_near, port_in = (0, cy, -8), (0, cy, -1)
    timeline = [(0, rest), (1.5, rack_up), (2.3, rack_at), (2.7, rack_at), (3.4, rack_up), (5.0, port_near), (6.0, port_in),
                (26.0, port_in), (27.0, port_near), (28.6, rack_up), (29.6, rack_at), (30.2, rack_at), (31.0, rack_up),
                (32.5, rest), (33.0, rest)]

    def channel(i, sign, axis):
        out = {}
        for t, target in timeline:
            a = sampler_ik(target)[i] * sign
            v = [0, 0, 0]
            v[axis] = round(a, 2)
            out[f"{t:.2f}".rstrip("0").rstrip(".") or "0"] = v
        return out
    hide, show = [0, 0, 0], [1, 1, 1]

    def vis(points):
        return keys([(t, v) for t, v in points])
    yaw0, sh0, el0 = sampler_ik(rest)
    pulse = {f"{6.5 + i * 0.5:.1f}": [1 + 0.15 * (i % 2)] * 3 for i in range(38)}
    pulse.update({"6": [0, 0, 0], "6.5": [1, 1, 1], "25.5": [1, 1, 1], "26": [0, 0, 0]})
    anims = {
        "misc.idle": {"length": 4.0, "loop": True, "bones": {
            "arm": {"rotation": keys([(0, [0, yaw0 * SY, 0])])},
            "upper": {"rotation": track(lambda t: [-SX * sh0 + 1.5 * sin(t), 0, 0], 4.0, 8)},
            "fore": {"rotation": keys([(0, [-SX * el0, 0, 0])])},
            "vial_claw": {"scale": keys([(0, hide)])},
            "vial_claw_red": {"scale": keys([(0, hide)])},
            "vial_red_rack": {"scale": keys([(0, hide)])},
            "port_glow": {"scale": track(lambda t: [0.25 + 0.1 * sin(t)] * 3, 4.0, 8)},
        }},
        "misc.sample": {"length": 33.0, "loop": False, "bones": {
            "arm": {"rotation": channel(0, SY, 1)},
            "upper": {"rotation": channel(1, -SX, 0)},
            "fore": {"rotation": channel(2, -SX, 0)},
            "vial_rack": {"scale": vis([(0, show), (2.5, show), (2.55, hide), (33.0, hide)])},
            "vial_claw": {"scale": vis([(0, hide), (2.5, hide), (2.55, show), (16.0, show), (16.05, hide), (33.0, hide)])},
            "vial_claw_red": {"scale": vis([(0, hide), (16.0, hide), (16.05, show), (30.0, show), (30.05, hide), (33.0, hide)])},
            "vial_red_rack": {"scale": vis([(0, hide), (30.0, hide), (30.05, show), (33.0, show)])},
            "port_glow": {"scale": dict(sorted(pulse.items(), key=lambda kv: float(kv[0])))},
        }},
    }
    finish(m, "warp_sampler", SHIP, anims)


def nav_table():
    m = Model("nav_table", S=2, atlas_w=256)
    root = m.bone("table", [0, 0, 0])
    root.cube([-20, 0, -4], [40, 4, 24], "hd_dark")
    root.cube([-14, 4, 0], [28, 8, 16], "hd_hull")
    root.cube([-24, 12, -8], [48, 4, 32], "hd_hull")
    root.cube([-24.5, 15, -8.5], [49, 1.5, 33], "hd_brass")
    root.cube([-21, 15.5, -5], [42, 1, 26], "hd_screen", deco={"up": starmap}, glow=lit_glow)
    # пульты по переднему краю, проектор в середине
    for x in (-20, 8):
        root.cube([x, 12, -11], [12, 5, 4], "hd_dark", rotation=[20, 0, 0], pivot=[x, 12, -8])
    root.cube([-3, 16.5, 5], [6, 2, 6], "hd_brass")
    root.cube([-1.5, 18.5, 6.5], [3, 1, 3], "hd_blue", glow="all")
    # колонны-когитаторы по углам задней кромки
    for sx in (-1, 1):
        root.cube([sx * 22 - 3, 16, 18], [6, 10, 6], "hd_dark")
        root.cube([sx * 22 - 2, 22, 17.5], [4, 3, 0.5], "hd_screen", deco={"north": screen_text}, glow=screen_glow)
        root.cube([sx * 22 - 3.5, 26, 17.5], [7, 1.5, 7], "hd_brass")
    # голограмма: планета, орбита, лучи проектора
    holo = m.bone("holo", [0, 30, 8], "table")
    holo.cube([-4, 26, 4], [8, 8, 8], "hd_blue", glow="all", rotation=[0, 45, 20], pivot=[0, 30, 8])
    orbit = m.bone("orbit", [0, 30, 8], "holo")
    for rot in (0, 90):
        orbit.cube([-12, 29.75, 7.75], [24, 0.5, 0.5], "hd_blue", glow="all", rotation=[0, rot, 0], pivot=[0, 30, 8])
    orbit.cube([10.5, 29, 7], [2, 2, 2], "hd_fire", glow="all")
    anims = {"misc.idle": {"length": 8.0, "loop": True, "bones": {
        "holo": {"rotation": track(lambda t: [0, 360 * t, 0], 8.0, 16), "position": track(lambda t: [0, 0.6 * sin(t * 2 % 1), 0], 8.0, 16)},
        "orbit": {"rotation": track(lambda t: [8 * sin(t), -720 * t, 0], 8.0, 24)},
    }}}
    finish(m, "nav_table", SHIP, anims)


def auspex():
    m = Model("auspex", S=2, atlas_w=128)
    root = m.bone("auspex", [0, 0, 0])
    root.cube([-7, 0, -6], [14, 4, 12], "hd_dark")
    root.cube([-6, 4, -4], [12, 14, 9], "hd_hull")
    root.cube([-6.5, 10, -4.5], [13, 1.5, 10], "hd_brass")
    root.cube([-5, 12, -6], [10, 8, 3], "hd_dark", rotation=[-20, 0, 0], pivot=[0, 12, -4])
    root.cube([-4, 13, -6.4], [8, 6, 0.5], "hd_screen", deco={"north": radar}, glow=lit_glow, rotation=[-20, 0, 0], pivot=[0, 12, -4])
    root.cube([-6, 5, -4.5], [12, 3, 0.5], "hd_dark")
    root.cube([-1.5, 18, 0], [3, 6, 3], "hd_steel")
    dish = m.bone("dish", [0, 24, 1.5], "auspex")
    dish.cube([-1, 24, 0.5], [2, 3, 2], "hd_brass")
    dish.cube([-6, 26, -1], [12, 7, 1.5], "hd_steel", rotation=[-25, 0, 0], pivot=[0, 26, 0])
    dish.cube([-0.5, 28, -5], [1, 1, 5], "hd_dark")
    dish.cube([-1, 27.5, -6], [2, 2, 1], "hd_fire", glow="all")
    for x in (-5, 4):
        root.cube([x, 2, 5], [1.5, 1.5, 3], "hd_cable")
    anims = {"misc.idle": {"length": 6.0, "loop": True, "bones": {
        "dish": {"rotation": track(lambda t: [0, 360 * t, 0], 6.0, 16)},
    }}}
    finish(m, "auspex", SHIP, anims)


def teleportarium_pad():
    m = Model("teleportarium_pad", S=2, atlas_w=256)
    root = m.bone("pad", [0, 0, 0])
    root.cube([-24, 0, -24], [48, 15, 48], "hd_dark")
    root.cube([-23, 15, -23], [46, 1.5, 46], "hd_hull")
    root.cube([-20, 16.5, -20], [40, 0.3, 40], "hd_screen", deco={"up": runic_circle}, glow=lit_glow)
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * 20, sz * 20
            root.cube([x - 2.5, 16, z - 2.5], [5, 4, 5], "hd_brass")
            root.cube([x - 1.5, 20, z - 1.5], [3, 6, 3], "hd_steel")
            tip = m.bone(f"emitter_{'l' if sx > 0 else 'r'}{'b' if sz > 0 else 'f'}", [x, 27, z], "pad")
            tip.cube([x - 1, 26, z - 1], [2, 2, 2], "hd_blue", glow="all")
    root.cube([-3, 16.5, -3], [6, 1, 6], "hd_brass")
    halo = m.bone("halo", [0, 62, 0], "pad")
    for rot in (0, 90, 180, 270):
        halo.cube([-18, 61.5, -19], [36, 1, 1], "hd_blue", glow="all", rotation=[0, rot, 0], pivot=[0, 62, 0])
    emit = {f"emitter_{a}{b}": {"scale": track(lambda t, k=k: [1 + 0.4 * max(0, sin(t * 2 % 1, k * 0.25))] * 3, 4.0, 16)}
            for k, (a, b) in enumerate((("l", "b"), ("r", "b"), ("l", "f"), ("r", "f")))}
    anims = {"misc.idle": {"length": 4.0, "loop": True, "bones": {
        "halo": {"rotation": track(lambda t: [0, 90 * t, 0], 4.0, 16),
                 "position": track(lambda t: [0, 1.5 * sin(t), 0], 4.0, 16)},
        **emit,
    }}}
    finish(m, "teleportarium_pad", SHIP, anims)


def command_console():
    """Командный пульт мостика 3×1: три наклонных экрана (состояние, звёздная карта, реактор), клавиатуры, латунь, шестерня."""
    m = Model("command_console", S=2, atlas_w=256)
    root = m.bone("console", [0, 0, 0])
    # основание: ступенчатый цоколь на три клетки
    root.cube([-24, 0, -6], [48, 3, 14], "hd_dark")
    root.cube([-22, 3, -4], [44, 10, 11], "hd_hull")
    root.cube([-22.5, 8, -4.5], [45, 1.5, 12], "hd_brass")
    for x in (-22, -8, 8):
        root.cube([x, 3.5, -4.6], [14, 4, 0.5], "hd_vent")
    # столешница с клавиатурами, наклон к оператору (на север)
    root.cube([-23, 13, -7], [46, 2, 12], "hd_dark")
    root.cube([-23.5, 14.5, -7.5], [47, 1, 1], "hd_brass")
    for x in (-21, -7, 7):
        root.cube([x, 15, -6], [14, 1, 6], "hd_steel", deco={"up": keys_face})
    for x, c in ((-20, "hd_red"), (-14, "hd_glow3"), (12, "hd_red"), (18, "hd_glow3")):
        root.cube([x, 15.5, -1], [1.5, 1, 1.5], c, glow="all")
    # экраны: центральный выше, боковые развёрнуты к оператору
    screens = m.bone("screens", [0, 16, 2], "console")
    screens.cube([-8, 16, 1], [16, 13, 3], "hd_dark")
    screens.cube([-7, 17, 0.6], [14, 11, 0.5], "hd_screen", deco={"north": status_screen}, glow=screen_glow)
    for sx, deco in ((-1, starmap), (1, reactor_screen)):
        x0 = sx * 15 - 7
        screens.cube([x0, 16, 1], [14, 10, 3], "hd_dark", rotation=[0, -sx * 18, 0], pivot=[sx * 8, 16, 2])
        screens.cube([x0 + 1, 17, 0.6], [12, 8, 0.5], "hd_screen", deco={"north": deco}, glow=lit_glow,
                     rotation=[0, -sx * 18, 0], pivot=[sx * 8, 16, 2])
    # венец: латунная рамка, шестерня с черепом, кабели к потолку
    root.cube([-9, 29, 1], [18, 2, 3], "hd_brass")
    root.cube([-4, 31, 1.5], [8, 8, 1.5], "hd_brass", deco={"north": emblem(0.46)})
    for x in (-6, 5):
        root.cube([x, 31, 4], [1.5, 12, 1.5], "hd_cable")
    for x in (-23, 21.5):
        root.cube([x, 13, 5], [1.5, 16, 1.5], "hd_cable")
        root.cube([x - 0.5, 26, 4.5], [2.5, 3, 2.5], "hd_brass")
    lamps = m.bone("lamps", [0, 30, 0], "console")
    for x in (-22.5, 21):
        lamps.cube([x, 29, 4.5], [2, 2, 2], "hd_glow", glow="all")
    root.cube([14, 20, 0.5], [3, 6, 0.5], "hd_parchment")
    root.cube([14.5, 25, 0.2], [2, 2, 1], "hd_wax")
    anims = {"misc.idle": {"length": 2.0, "loop": True, "bones": {
        "lamps": {"scale": keys([(0, [1, 1, 1]), (0.9, [1, 1, 1]), (1.0, [0.6, 0.6, 0.6]), (1.1, [1, 1, 1]), (2.0, [1, 1, 1])])},
        "screens": {"scale": track(lambda t: [1, 1, 1 + 0.01 * sin(t * 7 % 1)], 2.0, 8)},
    }}}
    finish(m, "command_console", SHIP, anims)


def keys_face(region, S, pal):
    """Клавиатура когитатора: ряды тёмных клавиш с латунными метками."""
    h, w = region.shape[:2]
    for y in range(1, h - 1, 3):
        for x in range(1, w - 1, 3):
            region[y:y + 2, x:x + 2, :3] = (34, 34, 38) if (x + y) % 7 else (186, 146, 54)


def status_screen(region, S, pal):
    """Экран состояния: заголовок, полосы-шкалы зелёным, янтарным, синим."""
    h, w = region.shape[:2]
    region[..., :3] = (8, 20, 12)
    region[1, 1:-1, :3] = (120, 255, 140)
    for i, (c, k) in enumerate((((110, 200, 255), 0.8), ((255, 170, 60), 0.6), ((120, 255, 140), 0.4), ((255, 80, 60), 0.15))):
        y = 4 + i * 4
        if y + 2 >= h:
            break
        region[y:y + 2, 2:w - 2, :3] = (20, 40, 26)
        region[y:y + 2, 2:2 + int((w - 4) * k), :3] = c


def reactor_screen(region, S, pal):
    """Экран реактора: схема ядра — кольцо, плазма, стрелки потоков."""
    import math
    h, w = region.shape[:2]
    region[..., :3] = (20, 12, 6)
    cx, cy, r = (w - 1) / 2, (h - 1) / 2, min(w, h) / 2 - 1
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - cx, y - cy)
            if abs(d - r) < 0.7:
                region[y, x, :3] = (255, 170, 60)
            elif d < r * 0.45:
                region[y, x, :3] = (255, 230, 160)


if __name__ == "__main__":
    command_console()
    salvage_forge()
    manual_press()
    mechanicus_forge()
    reactor_core()
    geller_node()
    warp_drive()
    imperial_standard(False)
    imperial_standard(True)
    warp_sampler()
    nav_table()
    auspex()
    teleportarium_pad()
