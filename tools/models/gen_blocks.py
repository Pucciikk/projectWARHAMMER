#!/usr/bin/env python3
"""
Модели-заглушки машин и корабельного оборудования (каталог М7, М16) — блочные модели Java из деталей.

    python3 tools/models/gen_blocks.py

Пишет assets/warpbound/models/block/<имя>.json и textures/block/<имя>_model.png (32 px на блок).
Перед модели — север: блокстейты поворачивают её к игроку. Когда придут модели автора
(Blockbench → Java Block), они ложатся в те же файлы.
"""
import math
import os
import sys
import zlib

sys.path.insert(0, os.path.dirname(__file__))
from geo import Model, cog, mix, save_png, write_block_model, write_json  # noqa: E402

MECH = dict(dark=(46, 44, 48), metal=(118, 120, 126), hull=(84, 86, 92), brass=(186, 146, 54), red=(130, 26, 24),
            brick=(96, 52, 40), screen=(14, 22, 16), glow=(90, 255, 130), glow2=(255, 150, 50), cable=(34, 34, 38),
            leather=(70, 46, 30), interior=(40, 30, 28))
SHIP = dict(MECH, hull=(78, 84, 96), metal=(112, 118, 130), dark=(40, 42, 50), screen=(10, 16, 24),
            glow=(110, 200, 255), glow2=(255, 140, 40))


# ------------------------------------------------------------------ рисунки на гранях

def screen_wave(color, phase=0.0):
    def f(region, S, pal):
        h, w = region.shape[:2]
        region[1:-1, 1:-1, :3] = pal["screen"]
        for x in range(2, w - 2):
            y = int(h / 2 + math.sin(x * 0.45 + phase) * h * 0.25)
            region[max(1, y):y + 2, x, :3] = color
        for y in range(2, h - 2, 4):
            region[y, 2:w - 2, :3] = mix(pal["screen"], color, 0.18)
    return f


def screen_dead(region, S, pal):
    """Разбитый экран сломанного маяка: тёмное стекло и трещины."""
    h, w = region.shape[:2]
    region[1:-1, 1:-1, :3] = (12, 12, 14)
    for (x0, y0, dx, dy) in ((w * 0.3, h * 0.2, 1, 1), (w * 0.7, h * 0.3, -1, 1), (w * 0.5, h * 0.6, 1, -1)):
        x, y = x0, y0
        for _ in range(int(min(w, h) * 0.5)):
            if 1 <= int(x) < w - 1 and 1 <= int(y) < h - 1:
                region[int(y), int(x), :3] = (70, 74, 80)
            x += dx * 0.8
            y += dy * 0.6


def radar(color):
    def f(region, S, pal):
        h, w = region.shape[:2]
        cx, cy, r = w / 2 - 0.5, h / 2 - 0.5, min(w, h) / 2 - 1.5
        for y in range(h):
            for x in range(w):
                dd = math.hypot(x - cx, y - cy)
                if dd <= r:
                    region[y, x, :3] = pal["screen"]
                    if abs(dd - r * 0.33) < 0.6 or abs(dd - r * 0.66) < 0.6 or abs(dd - r) < 0.8:
                        region[y, x, :3] = mix(pal["screen"], color, 0.5)
                    a = math.atan2(y - cy, x - cx)
                    if 0 < (a + 0.6) % (2 * math.pi) < 0.7:
                        region[y, x, :3] = mix(pal["screen"], color, 1 - ((a + 0.6) % (2 * math.pi)) / 0.7)
        for (bx, by) in ((0.62, 0.35), (0.3, 0.6), (0.7, 0.7)):
            region[int(h * by), int(w * bx), :3] = (255, 255, 255)
    return f


def starmap(region, S, pal):
    """Звёздная карта на столешнице: сетка, звёзды и курс."""
    h, w = region.shape[:2]
    m = 3
    region[m:h - m, m:w - m, :3] = pal["screen"]
    for k in range(m, w - m, 6):
        region[m:h - m, k, :3] = mix(pal["screen"], pal["glow"], 0.25)
        region[k, m:w - m, :3] = mix(pal["screen"], pal["glow"], 0.25)
    import random
    rng = random.Random(5)
    stars = [(rng.randrange(m + 1, w - m - 1), rng.randrange(m + 1, h - m - 1)) for _ in range(14)]
    for x, y in stars:
        region[y, x, :3] = (255, 255, 255)
    for (x0, y0), (x1, y1) in zip(stars[:4], stars[1:5]):
        for t in range(20):
            x, y = int(x0 + (x1 - x0) * t / 20), int(y0 + (y1 - y0) * t / 20)
            region[y, x, :3] = pal["glow2"]


def fire(region, S, pal):
    """Пламя в устье горна."""
    h, w = region.shape[:2]
    for y in range(h):
        for x in range(w):
            t = y / max(1, h - 1)
            flick = 0.5 + 0.5 * math.sin(x * 1.7 + y * 0.9)
            region[y, x, :3] = mix((255, 230, 120), (200, 40, 10), max(0, 1 - t - flick * 0.3))
    region[-2:, :, :3] = (255, 200, 80)


def embers(region, S, pal):
    """Остывший горн: тёмное нутро с редкими углями."""
    h, w = region.shape[:2]
    region[...,:3] = (22, 16, 14)
    for x in range(1, w - 1, 3):
        region[-2, x, :3] = (150, 50, 20)


def aquila(region, S, pal):
    """Двуглавый орёл на спинке трона: раскинутые крылья с перьями, две головы в стороны."""
    from PIL import Image, ImageDraw
    h, w = region.shape[:2]
    img = Image.new("RGBA", (w * 4, h * 4), (0, 0, 0, 0))  # рисуем крупно и сжимаем — края ровнее
    d = ImageDraw.Draw(img)
    W, H = w * 4, h * 4
    cx, top = W / 2, H * 0.12
    c, dk = tuple(pal["brass"]) + (255,), tuple(int(v * 0.6) for v in pal["brass"]) + (255,)
    for sx in (-1, 1):
        # крыло: веер из пяти перьев от плеча вниз-наружу
        for i in range(5):
            ang = math.radians(-30 + i * 22)
            x0, y0 = cx + sx * W * 0.06, top + H * 0.18
            ln = W * (0.46 - i * 0.04)
            x1, y1 = x0 + sx * math.cos(ang) * ln, y0 + math.sin(ang) * ln * 0.75
            d.line([(x0, y0), (x1, y1)], fill=c, width=int(W * 0.07))
            d.line([(x0, y0 + W * 0.03), (x1, y1 + W * 0.03)], fill=dk, width=int(W * 0.02))
        # голова и клюв, смотрят в стороны
        hx, hy = cx + sx * W * 0.1, top + H * 0.04
        d.ellipse([hx - W * 0.07, hy - W * 0.07, hx + W * 0.07, hy + W * 0.07], fill=c)
        d.polygon([(hx + sx * W * 0.06, hy - W * 0.02), (hx + sx * W * 0.16, hy + W * 0.02),
                   (hx + sx * W * 0.06, hy + W * 0.04)], fill=c)
    # тело и хвост
    d.polygon([(cx - W * 0.08, top + H * 0.1), (cx + W * 0.08, top + H * 0.1), (cx + W * 0.05, top + H * 0.42),
               (cx, top + H * 0.5), (cx - W * 0.05, top + H * 0.42)], fill=c)
    small = img.resize((w, h), Image.LANCZOS)
    import numpy as np
    a = np.array(small)
    mask = a[..., 3] > 110
    region[mask, :3] = a[mask, :3]


def keys(region, S, pal):
    """Клавиши и рычажки на пульте."""
    h, w = region.shape[:2]
    for y in range(2, h - 2, 3):
        for x in range(2, w - 2, 3):
            region[y:y + 2, x:x + 2, :3] = pal["brass"] if (x + y) % 4 else pal["red"]


def cog_face(region, S, pal):
    h, w = region.shape[:2]
    cog(region, w / 2, h / 2, min(w, h) * 0.38, pal["brass"])


def glow_ring(region, S, pal):
    """Кольцо телепортариума на полу."""
    h, w = region.shape[:2]
    cx, cy = w / 2 - 0.5, h / 2 - 0.5
    for y in range(h):
        for x in range(w):
            dd = math.hypot(x - cx, y - cy) / (w / 2)
            if 0.55 < dd < 0.75:
                region[y, x, :3] = pal["glow"]
            elif dd <= 0.55:
                region[y, x, :3] = mix(pal["screen"], pal["glow"], 0.35 * (1 - dd))


# ------------------------------------------------------------------ сборка

def build(name, texture, parts, pal):
    m = Model(texture, S=2)
    b = m.bone("block", [8, 0, 8])
    for p in parts:
        origin, size, mat = p[:3]
        opts = p[3] if len(p) > 3 else {}
        c = b.cube(origin, size, mat, deco=opts.get("deco"))
        if "rot" in opts:
            c.block_rot = opts["rot"]
    for aw in (32, 64, 128, 256):  # квадратный атлас: 16 единиц UV — вся текстура
        m.atlas_w = aw
        try:
            w, h = m.pack()
        except ValueError:
            continue
        if h <= aw:
            break
    m.atlas_size = (aw, aw)
    print(name)
    base, _ = m.paint(pal, seed=zlib.crc32(texture.encode()))
    save_png(base, "block", texture + ".png")
    write_block_model(m, name, texture)


def vox_beacon(broken):
    name = "vox_beacon_broken" if broken else "vox_beacon"
    parts = [
        ([1, 0, 1], [14, 3, 14], "hull"),
        ([2, 3, 3], [12, 8, 10], "dark"),
        ([3, 5, 2], [10, 5, 1], "screen", {"deco": {"north": screen_dead if broken else screen_wave(MECH["glow"])}}),
        ([2, 10, 3], [12, 1, 10], "brass"),
        ([3, 11, 4], [10, 1, 8], "dark"),
        ([12, 3, 13], [2, 7, 1], "cable"),
        ([3, 3, 13], [3, 4, 2], "grate"),
        ([10, 3, 13], [3, 4, 2], "grate"),
    ]
    if broken:
        parts += [
            ([7, 12, 7], [2, 4, 2], "metal", {"rot": ("z", 45, [8, 12, 8])}),   # погнутая мачта
            ([9, 3, 1], [5, 1, 4], "brass", {"rot": ("y", 22.5, [11, 3, 3])}),   # сорванная тарелка на станине
        ]
    else:
        parts += [
            ([7, 12, 7], [2, 4, 2], "metal"),
            ([4, 13, 9], [8, 3, 1], "brass", {"rot": ("x", -22.5, [8, 13, 9])}),  # тарелка антенны
            ([7, 15, 7], [2, 1, 2], "glow"),
        ]
    build(name, name + "_model", parts, MECH)


def salvage_forge(lit):
    name = "salvage_forge_on" if lit else "salvage_forge"
    parts = [
        ([0, 0, 2], [16, 12, 14], "brick"),
        ([0, 0, 0], [4, 12, 2], "brick"),
        ([12, 0, 0], [4, 12, 2], "brick"),
        ([4, 8, 0], [8, 4, 2], "brick"),
        ([4, 0, 0], [8, 2, 2], "dark"),
        ([4, 2, 1], [8, 6, 1], "screen", {"deco": {"north": fire if lit else embers}}),
        ([3, 7, -1], [10, 1, 1], "brass"),                  # латунная скоба над устьем
        ([1, 12, 1], [14, 2, 14], "dark"),                  # железный колпак
        ([5, 14, 7], [6, 2, 6], "metal"),                   # основание трубы
        ([0, 4, 4], [1, 4, 8], "leather"),                  # мехи сбоку
        ([1, 3, 0], [1, 9, 1], "metal"), ([14, 3, 0], [1, 9, 1], "metal"),
    ]
    build(name, name + "_model", parts, MECH)


def manual_press(down):
    name = "manual_press_down" if down else "manual_press"
    ram_y = 6 if down else 9
    parts = [
        ([1, 0, 1], [14, 4, 14], "dark"),
        ([2, 4, 2], [2, 10, 2], "metal"), ([12, 4, 2], [2, 10, 2], "metal"),
        ([2, 4, 12], [2, 10, 2], "metal"), ([12, 4, 12], [2, 10, 2], "metal"),
        ([1, 14, 1], [14, 2, 14], "brass", {"deco": {"up": cog_face}}),
        ([7, ram_y + 3, 7], [2, 14 - ram_y - 3, 2], "metal"),   # винт
        ([4, ram_y, 4], [8, 3, 8], "dark"),                      # пуансон
        ([5, 4, 5], [6, 1, 6], "metal"),                         # матрица
        ([3, 1, 0], [10, 2, 1], "brass"),
    ]
    build(name, name + "_model", parts, MECH)


def shipyard_console():
    parts = [
        ([3, 0, 3], [10, 2, 10], "dark"),
        ([5, 2, 6], [6, 7, 5], "hull", {"deco": {"north": cog_face}}),
        ([1, 9, 2], [14, 3, 12], "hull", {"deco": {"up": keys}}),
        ([1, 12, 2], [14, 1, 1], "brass"),
        ([2, 11, 11], [12, 7, 1], "screen", {"deco": {"north": screen_wave(MECH["glow"], 1.3)},
                                            "rot": ("x", 22.5, [8, 11, 12])}),
        ([0, 9, 6], [1, 6, 1], "cable"), ([15, 9, 6], [1, 6, 1], "cable"),
    ]
    build("shipyard_console", "shipyard_console_model", parts, MECH)


def nav_table():
    parts = [
        ([4, 0, 4], [8, 2, 8], "dark"),
        ([5, 2, 5], [6, 7, 6], "hull", {"deco": {"north": cog_face}}),
        ([0, 9, 0], [16, 3, 16], "hull", {"deco": {"up": starmap}}),
        ([0, 12, 0], [16, 1, 1], "brass"), ([0, 12, 15], [16, 1, 1], "brass"),
        ([0, 12, 1], [1, 1, 14], "brass"), ([15, 12, 1], [1, 1, 14], "brass"),
        ([7, 12, 7], [2, 1, 2], "glow"),
    ]
    build("nav_table", "nav_table_model", parts, SHIP)


def auspex():
    parts = [
        ([1, 0, 1], [14, 2, 14], "dark"),
        ([2, 2, 3], [12, 12, 11], "hull"),
        ([3, 3, 2], [10, 10, 1], "screen", {"deco": {"north": radar((90, 255, 130))}}),
        ([2, 13, 2], [12, 1, 1], "brass"), ([2, 2, 2], [12, 1, 1], "brass"),
        ([7, 14, 7], [2, 2, 2], "metal"),
        ([13, 4, 5], [1, 8, 7], "grate"), ([2, 4, 5], [1, 8, 7], "grate"),
    ]
    pal = dict(SHIP, screen=(8, 20, 10))
    build("auspex", "auspex_model", parts, pal)


def geller_node():
    parts = [
        ([1, 0, 1], [14, 3, 14], "hull"),
        ([1, 13, 1], [14, 3, 14], "hull", {"deco": {"up": cog_face}}),
        ([5, 3, 5], [6, 10, 6], "glow"),
        ([4, 5, 4], [8, 1, 8], "metal"), ([4, 10, 4], [8, 1, 8], "metal"),
        ([2, 3, 2], [2, 10, 2], "brass"), ([12, 3, 2], [2, 10, 2], "brass"),
        ([2, 3, 12], [2, 10, 2], "brass"), ([12, 3, 12], [2, 10, 2], "brass"),
    ]
    build("geller_node", "geller_node_model", parts, SHIP)


def reactor_core():
    parts = [
        ([0, 0, 0], [16, 3, 16], "dark"),
        ([2, 3, 1], [12, 10, 14], "hull"),
        ([1, 3, 2], [14, 10, 12], "hull"),
        ([4, 5, 0], [8, 6, 1], "screen", {"deco": {"north": fire}}),
        ([4, 7, 0], [8, 1, 1], "grate"),
        ([2, 13, 2], [12, 3, 12], "dark", {"deco": {"up": cog_face}}),
        ([0, 6, 6], [1, 4, 4], "metal"), ([15, 6, 6], [1, 4, 4], "metal"),
        ([1, 3, 1], [1, 10, 1], "brass"), ([14, 3, 1], [1, 10, 1], "brass"),
    ]
    build("reactor_core", "reactor_core_model", parts, SHIP)


def teleportarium_pad():
    parts = [
        ([0, 0, 0], [16, 15, 16], "hull"),
        ([0, 15, 0], [16, 1, 2], "brass"), ([0, 15, 14], [16, 1, 2], "brass"),
        ([0, 15, 2], [2, 1, 12], "brass"), ([14, 15, 2], [2, 1, 12], "brass"),
        ([2, 15, 2], [12, 1, 12], "screen", {"deco": {"up": glow_ring}}),
    ]
    build("teleportarium_pad", "teleportarium_pad_model", parts, SHIP)


def command_throne():
    parts = [
        ([2, 0, 2], [12, 3, 12], "dark"),
        ([3, 3, 3], [10, 3, 10], "hull"),
        ([3, 6, 3], [10, 2, 9], "red"),                       # сиденье
        ([3, 6, 12], [10, 16, 2], "red", {"deco": {"north": aquila}}),   # спинка до 1.5 блока
        ([3, 22, 12], [10, 2, 2], "brass"),
        ([1, 6, 3], [2, 5, 9], "brass", {"deco": {"up": keys}}),         # подлокотники с пультами
        ([13, 6, 3], [2, 5, 9], "brass", {"deco": {"up": keys}}),
        ([6, 24, 12], [4, 4, 2], "brass", {"deco": {"north": cog_face}}),
    ]
    build("command_throne", "command_throne_model", parts, SHIP)
    write_json({"variants": {f"facing={d}": ({"model": "warpbound:block/command_throne", "y": r} if r else
                                             {"model": "warpbound:block/command_throne"})
                             for d, r in (("north", 0), ("east", 90), ("south", 180), ("west", 270))}},
               "blockstates", "command_throne.json")
    write_json({"parent": "warpbound:block/command_throne"}, "models", "item", "command_throne.json")


def mechanicus_forge():
    """Ядро Кузни Механикус до освящения: алтарь-когитатор с шестернёй и красным покровом."""
    parts = [
        ([1, 0, 1], [14, 3, 14], "dark"),
        ([2, 3, 2], [12, 8, 12], "brick"),
        ([1.5, 7, 1.5], [13, 1, 13], "brass"),
        ([2, 11, 2], [12, 2, 12], "hull", {"deco": {"up": keys}}),
        ([4, 3, 1.5], [8, 8, 0.5], "red", {"deco": {"north": cog_face}}),
        ([3, 13, 9], [10, 7, 2], "screen", {"deco": {"north": screen_wave(MECH["glow"], 0.4)},
                                           "rot": ("x", -22.5, [8, 13, 10])}),
        ([2, 13, 3], [1.5, 4, 1.5], "brass"), ([12.5, 13, 3], [1.5, 4, 1.5], "brass"),
    ]
    build("mechanicus_forge", "mechanicus_forge_model", parts, MECH)
    write_json({"variants": {f"facing={d}": ({"model": "warpbound:block/mechanicus_forge", "y": r} if r else
                                             {"model": "warpbound:block/mechanicus_forge"})
                             for d, r in (("north", 0), ("east", 90), ("south", 180), ("west", 270))}},
               "blockstates", "mechanicus_forge.json")
    write_json({"parent": "warpbound:block/mechanicus_forge"}, "models", "item", "mechanicus_forge.json")


def command_console():
    """Командный пульт мостика в инвентаре (в мире его рисует крупная модель GeckoLib)."""
    parts = [
        ([1, 0, 4], [14, 2, 10], "dark"),
        ([2, 2, 5], [12, 6, 8], "hull"),
        ([1, 8, 3], [14, 1.5, 9], "dark", {"deco": {"up": keys}}),
        ([3, 9, 9], [10, 7, 2], "screen", {"deco": {"north": screen_wave(SHIP["glow"], 0.8)}}),
        ([6, 16, 9.5], [4, 3, 1], "brass", {"deco": {"north": cog_face}}),
    ]
    build("command_console", "command_console_model", parts, SHIP)
    write_json({"variants": {f"facing={d}": ({"model": "warpbound:block/command_console", "y": r} if r else
                                             {"model": "warpbound:block/command_console"})
                             for d, r in (("north", 0), ("east", 90), ("south", 180), ("west", 270))}},
               "blockstates", "command_console.json")
    write_json({"parent": "warpbound:block/command_console"}, "models", "item", "command_console.json")


if __name__ == "__main__":
    command_console()
    mechanicus_forge()
    for b in (False, True):
        vox_beacon(b)
        salvage_forge(b)
        manual_press(b)
    shipyard_console()
    nav_table()
    auspex()
    geller_node()
    reactor_core()
    teleportarium_pad()
    command_throne()
