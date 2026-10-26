#!/usr/bin/env python3
"""
Модели-заглушки сущностей Сезона 1 (каталог М1–М9) в формате GeckoLib.

    python3 tools/models/gen_entities.py

Пишет для каждой сущности:
    assets/warpbound/geo/entity/<имя>.geo.json
    assets/warpbound/animations/entity/<имя>.animation.json
    assets/warpbound/textures/entity/<имя>.png и <имя>_glow.png

Это временные модели: автор заменит их своими из Blockbench. Чтобы замена прошла без правок кода,
держим контракт (docs/content/models.md): имена костей, имена анимаций, кости вариантов.
"""
import os
import zlib
import sys

sys.path.insert(0, os.path.dirname(__file__))
from geo import (Model, cog, draw_rect, keys, save_png, sin, star8, track,  # noqa: E402
                 write_animations)

# ------------------------------------------------------------------ палитры

TECH_PRIEST = dict(robe=(140, 26, 24), trim=(201, 162, 39), hood=(120, 22, 20), leather=(70, 46, 30),
                   metal=(128, 132, 140), dark=(52, 54, 60), brass=(190, 150, 52), cable=(40, 40, 44),
                   face=(30, 30, 34), glow=(90, 255, 130), glow2=(255, 170, 60), skin=(200, 170, 150))
DARK_TECH_PRIEST = dict(TECH_PRIEST, robe=(36, 28, 42), trim=(120, 40, 150), hood=(28, 22, 34),
                        metal=(96, 88, 80), brass=(120, 92, 60), glow=(255, 50, 60), glow2=(200, 60, 255))
SERVITOR = dict(skin=(196, 180, 170), flesh=(196, 176, 168), vein=(150, 110, 120), metal=(122, 126, 132),
                dark=(54, 56, 60), brass=(170, 135, 60), cable=(36, 36, 40), face=(40, 40, 44),
                glow=(255, 40, 30), glow2=(120, 200, 255), leather=(60, 50, 44))
BLOODLETTER = dict(flesh=(176, 30, 26), vein=(110, 12, 14), skin=(170, 34, 30), horn=(70, 52, 40),
                   claw=(28, 20, 20), brass=(176, 120, 40), blade=(40, 34, 36), dark=(40, 30, 30),
                   glow=(255, 150, 40), glow2=(255, 60, 30), leather=(60, 26, 20))
PINK_HORROR = dict(flesh=(232, 110, 190), vein=(190, 70, 160), skin=(236, 128, 200), claw=(90, 40, 110),
                   face=(60, 10, 40), glow=(255, 120, 230), glow2=(120, 220, 255))
BLUE_HORROR = dict(PINK_HORROR, flesh=(70, 120, 220), vein=(40, 70, 170), skin=(80, 136, 228), claw=(30, 40, 90),
                   face=(14, 16, 50), glow=(100, 200, 255), glow2=(255, 120, 230))
CULTIST = [  # три варианта одежды на одной геометрии
    dict(rag=(92, 74, 56), rag2=(70, 60, 50), patch=(110, 40, 36), hood=(64, 50, 40), leather=(52, 38, 28),
         dark=(48, 48, 50), metal=(100, 100, 104), brass=(140, 110, 50), skin=(180, 150, 130), face=(40, 40, 42),
         glow=(255, 40, 40), blade=(150, 150, 156), cable=(40, 40, 40)),
    dict(rag=(60, 66, 52), rag2=(50, 48, 44), patch=(120, 30, 30), hood=(46, 50, 40), leather=(48, 40, 30),
         dark=(44, 46, 48), metal=(96, 98, 100), brass=(130, 100, 50), skin=(170, 140, 120), face=(36, 38, 40),
         glow=(255, 90, 30), blade=(150, 150, 156), cable=(40, 40, 40)),
    dict(rag=(96, 30, 28), rag2=(60, 24, 24), patch=(40, 36, 34), hood=(70, 20, 20), leather=(40, 30, 26),
         dark=(40, 38, 40), metal=(104, 100, 98), brass=(150, 110, 40), skin=(186, 156, 136), face=(30, 28, 30),
         glow=(255, 200, 60), blade=(150, 150, 156), cable=(40, 40, 40)),
]
PRIEST = dict(robe=(70, 18, 22), trim=(170, 130, 50), hood=(30, 24, 26), leather=(44, 32, 26), skin=(176, 150, 136),
              face=(170, 140, 126), brass=(170, 130, 50), dark=(36, 32, 34), metal=(110, 104, 100),
              horn=(60, 44, 40), claw=(30, 20, 24), flesh=(150, 40, 60), vein=(90, 10, 30),
              glow=(255, 60, 200), glow2=(120, 220, 255), cable=(40, 30, 30))
PRIEST_DAEMON = dict(PRIEST, skin=(150, 70, 90), face=(140, 60, 80), robe=(50, 12, 16), flesh=(170, 50, 80),
                     glow=(255, 80, 230))
POD = dict(dark=(46, 40, 42), metal=(92, 30, 28), brass=(150, 110, 44), interior=(60, 24, 24), cable=(30, 26, 26),
           glow=(255, 70, 30), glow2=(255, 200, 80), horn=(200, 190, 170))


# ------------------------------------------------------------------ рисунки лиц и знаков

def priest_face(region, S, pal):
    # вокс-решётка вместо рта
    for i in range(3):
        draw_rect(region, S, 2 + i * 1, 5, 0.5, 1.5, (20, 20, 22))


def servitor_face(region, S, pal):
    draw_rect(region, S, 1, 3, 1, 1, (60, 40, 40))       # живой глаз
    draw_rect(region, S, 1.5, 4.6, 3, 0.4, (90, 60, 60))  # зашитый рот
    for i in range(4):
        draw_rect(region, S, 1.6 + i * 0.8, 4.4, 0.2, 0.8, (50, 30, 30))


def bloodletter_face(region, S, pal):
    draw_rect(region, S, 0.5, 4, 4, 1, (40, 6, 6))  # оскал
    for i in range(5):
        draw_rect(region, S, 0.6 + i * 0.8, 4, 0.4, 0.6, (230, 220, 200))


def horror_face(region, S, pal):
    # лицо в торсе: два глаза и пасть до краёв
    draw_rect(region, S, 2, 2, 2, 2, (250, 250, 240))
    draw_rect(region, S, 8, 2, 2, 2, (250, 250, 240))
    draw_rect(region, S, 2.6, 2.6, 1, 1, (20, 0, 20))
    draw_rect(region, S, 8.6, 2.6, 1, 1, (20, 0, 20))
    draw_rect(region, S, 1, 6, 10, 3, pal["face"])
    for i in range(10):
        draw_rect(region, S, 1.2 + i, 6, 0.6, 1, (250, 245, 230))
        draw_rect(region, S, 1.6 + i, 8, 0.6, 1, (250, 245, 230))


def gasmask(region, S, pal):
    draw_rect(region, S, 0.5, 0.5, 1.5, 1.5, (20, 20, 20))
    draw_rect(region, S, 3, 0.5, 1.5, 1.5, (20, 20, 20))
    draw_rect(region, S, 2, 2.5, 1, 1, (30, 30, 30))


def star_deco(scale=0.42, key="brass"):
    def f(region, S, pal):
        h, w = region.shape[:2]
        star8(region, w / 2, h / 2, min(w, h) * scale, pal[key])
    return f


def cog_deco(region, S, pal):
    h, w = region.shape[:2]
    cog(region, w / 2, h / 2, min(w, h) * 0.36, pal["brass"])


def priest_face_human(region, S, pal):
    draw_rect(region, S, 1, 2.5, 1, 1, (30, 20, 20))
    draw_rect(region, S, 4, 2.5, 1, 1, (30, 20, 20))
    draw_rect(region, S, 2, 4.5, 2, 0.5, (90, 40, 40))


def rune_glow(g, region, face, S, pal):
    """Руны на клинке кровопускателя: светятся только они."""
    h, w = region.shape[:2]
    if face not in ("north", "south") or w < 2:
        return
    for y in range(2, h - 2, 5):
        g[y:y + 3, w // 2 - 1:w // 2 + 1, :3] = pal["glow2"]
        g[y:y + 3, w // 2 - 1:w // 2 + 1, 3] = 255
        region[y:y + 3, w // 2 - 1:w // 2 + 1, :3] = pal["glow2"]


def veins_glow(g, region, face, S, pal):
    """Кожа одержимого во второй фазе: варп светится в трещинах."""
    h, w = region.shape[:2]
    import random
    rng = random.Random(h * 31 + w)
    for _ in range(max(1, w * h // 70)):
        x, y = rng.randrange(w), rng.randrange(h)
        for _ in range(rng.randint(3, 8)):
            if 0 <= x < w and 0 <= y < h:
                g[y, x, :3] = pal["glow"]
                g[y, x, 3] = 255
                region[y, x, :3] = pal["glow"]
            x += rng.choice((-1, 0, 1))
            y += rng.choice((0, 1))


# ------------------------------------------------------------------ общие части

def hood(b, x0, y0, z0, w, h, d, mat="hood"):
    """Капюшон из пяти пластин: лицо остаётся открытым и утоплено на пиксель."""
    b.cube([x0, y0 + h - 1, z0], [w, 2, d], mat)
    b.cube([x0, y0, z0], [1, h - 1, d], mat)
    b.cube([x0 + w - 1, y0, z0], [1, h - 1, d], mat)
    b.cube([x0, y0, z0 + d - 1], [w, h - 1, 1], mat)
    b.cube([x0, y0 + h - 2, z0 - 0.5], [w, 1, 1], mat)


def humanoid_anims(walk_amp=28, arm_amp=22, bob=0.4, walk_len=1.0, run_len=0.6, extra_idle=None, extra_walk=None):
    """Базовый набор: misc.idle, move.walk, move.run, attack.swing, attack.shoot, attack.cast."""
    idle = {
        "body": {"rotation": track(lambda t: [1.5 * sin(t), 0, 0], 3.0, 12)},
        "head": {"rotation": track(lambda t: [2 * sin(t, 0.25), 6 * sin(t * 2 % 1), 0], 3.0, 12)},
        "right_arm": {"rotation": track(lambda t: [2 * sin(t), 0, 2 + 1.5 * sin(t)], 3.0, 12)},
        "left_arm": {"rotation": track(lambda t: [-2 * sin(t), 0, -2 - 1.5 * sin(t)], 3.0, 12)},
    }

    def walk(amp, aamp, length, lean):
        return {
            "right_leg": {"rotation": track(lambda t: [amp * sin(t), 0, 0], length)},
            "left_leg": {"rotation": track(lambda t: [-amp * sin(t), 0, 0], length)},
            "right_arm": {"rotation": track(lambda t: [-aamp * sin(t), 0, 3], length)},
            "left_arm": {"rotation": track(lambda t: [aamp * sin(t), 0, -3], length)},
            "body": {"rotation": track(lambda t: [lean, 3 * sin(t), 0], length),
                     "position": track(lambda t: [0, bob * abs(sin(t)), 0], length)},
            "head": {"rotation": track(lambda t: [-lean * 0.6, -3 * sin(t), 0], length)},
        }

    w = walk(walk_amp, arm_amp, walk_len, 2)
    r = walk(walk_amp * 1.5, arm_amp * 1.8, run_len, 12)
    if extra_idle:
        idle.update(extra_idle)
    if extra_walk:
        w.update(extra_walk)
    return {
        "misc.idle": {"length": 3.0, "loop": True, "bones": idle},
        "move.walk": {"length": walk_len, "loop": True, "bones": w},
        "move.run": {"length": run_len, "loop": True, "bones": r},
        "attack.swing": {"length": 0.6, "bones": {
            "right_arm": {"rotation": keys([(0, [0, 0, 0]), (0.18, [-150, 10, 0]), (0.32, [-20, -10, 0]), (0.6, [0, 0, 0])])},
            "body": {"rotation": keys([(0, [0, 0, 0]), (0.18, [-6, 12, 0]), (0.32, [10, -15, 0]), (0.6, [0, 0, 0])])},
        }},
        "attack.shoot": {"length": 0.5, "bones": {
            "right_arm": {"rotation": keys([(0, [-80, 0, 0]), (0.05, [-95, 0, 0]), (0.2, [-85, 0, 0]), (0.5, [-80, 0, 0])])},
            "left_arm": {"rotation": keys([(0, [-70, 30, 0]), (0.5, [-70, 30, 0])])},
        }},
        "attack.cast": {"length": 0.8, "bones": {
            "right_arm": {"rotation": keys([(0, [0, 0, 0]), (0.3, [-160, 0, 15]), (0.5, [-90, 0, 0]), (0.8, [0, 0, 0])])},
            "left_arm": {"rotation": keys([(0, [0, 0, 0]), (0.3, [-160, 0, -15]), (0.5, [-90, 0, 0]), (0.8, [0, 0, 0])])},
            "head": {"rotation": keys([(0, [0, 0, 0]), (0.3, [-20, 0, 0]), (0.8, [0, 0, 0])])},
        }},
    }


def finish(m, name, palettes, anims, extra_textures=()):
    """palettes: {суффикс текстуры: палитра}. Пустой суффикс — основная текстура."""
    print(name)
    m.build()
    for i, (suffix, pal) in enumerate(palettes.items()):
        base, glow = m.paint(pal, seed=zlib.crc32((name + suffix).encode()))
        save_png(base, "entity", f"{name}{suffix}.png")
        save_png(glow, "entity", f"{name}{suffix}_glow.png")
    if anims:
        write_animations(name, anims)


# ------------------------------------------------------------------ М1–М2: техножрец

def tech_priest():
    m = Model("tech_priest", atlas_w=128)
    m.bone("root", [0, 0, 0])
    rl = m.bone("right_leg", [-2, 11, 0], "root")
    rl.cube([-4, 0, -2], [4, 11, 4], "metal")
    ll = m.bone("left_leg", [2, 11, 0], "root")
    ll.cube([0, 0, -2], [4, 11, 4], "metal")

    body = m.bone("body", [0, 11, 0], "root")
    body.cube([-4.5, 11, -2.5], [9, 13, 5], "robe_plain")
    body.cube([-5, 13, -3], [10, 2, 6], "leather", deco={"north": cog_deco})
    body.cube([-1.5, 15, -3], [3, 8, 1], "brass")  # нагрудная полоса с шестернёй
    robe = m.bone("robe", [0, 13, 0], "body")
    robe.cube([-5, 0, -3.5], [10, 13, 7], "robe")
    pack = m.bone("backpack", [0, 18, 3], "body")
    pack.cube([-3.5, 13, 2.5], [7, 9, 3], "dark", deco={"south": cog_deco})
    pack.cube([-3, 22, 3], [1, 3, 1], "metal_plain")
    pack.cube([2, 22, 3], [1, 3, 1], "metal_plain")
    pack.cube([-1, 15, 5.5], [2, 3, 1], "glow2", glow="all")  # плазменный индикатор

    # механодендриты: три звена, каждое — кость, чтобы анимации могли их гнуть
    for side, sx in (("right", -1), ("left", 1)):
        x = 2.5 * sx
        a = m.bone(f"mechadendrite_{side}", [x, 20, 4], "body", rotation=[-50, 15 * sx, 0])
        a.cube([x - 0.5, 19.5, 4], [1, 1, 5], "cable")
        b = m.bone(f"mechadendrite_{side}_2", [x, 20, 9], f"mechadendrite_{side}", rotation=[-35, 0, 0])
        b.cube([x - 0.5, 19.5, 9], [1, 1, 5], "cable")
        c = m.bone(f"mechadendrite_{side}_tip", [x, 20, 14], f"mechadendrite_{side}_2", rotation=[-30, 0, 0])
        c.cube([x - 1, 19, 14], [2, 2, 2], "brass")
        c.cube([x - 0.5, 19.5, 16], [1, 1, 1], "glow", glow="all")

    head = m.bone("head", [0, 24, 0], "body")
    head.cube([-3.5, 24, -3.5], [7, 7, 7], "face", deco={"north": priest_face})
    head.cube([-2.5, 27, -4.5], [2, 2, 1], "glow", glow="all")
    head.cube([0.5, 27, -4.5], [2, 2, 1], "glow", glow="all")
    head.cube([-1, 24.5, -4.2], [2, 2, 1], "metal_plain")  # вокс-решётка
    hd = m.bone("hood", [0, 24, 0], "head")
    hood(hd, -4.5, 23.5, -4.5, 9, 9, 9)

    for side, sx in (("right", -1), ("left", 1)):
        arm = m.bone(f"{side}_arm", [6 * sx, 22, 0], "body")
        x0 = -7.5 if sx < 0 else 4.5
        arm.cube([x0, 14, -2], [3, 9, 4], "sleeve")
        arm.cube([x0 + 0.5, 11, -1.5], [2, 3, 3], "metal")
    item = m.bone("right_item", [-6, 12, 0], "right_arm")
    item.cube([-6.5, 3, -0.5], [1, 23, 1], "dark_plain")            # древко ключа-топора
    item.cube([-7, 20, -4.5], [2, 7, 4], "brass", deco={"east": cog_deco, "west": cog_deco})  # лезвие-шестерня
    item.cube([-7, 22, -1], [2, 3, 2], "metal")
    item.cube([-6.5, 26, -0.5], [1, 2, 1], "glow", glow="all")

    anims = humanoid_anims(walk_amp=18, arm_amp=14, extra_idle={
        "mechadendrite_right": {"rotation": track(lambda t: [6 * sin(t), 8 * sin(t, 0.3), 0], 4.0, 12)},
        "mechadendrite_right_2": {"rotation": track(lambda t: [10 * sin(t, 0.2), 0, 0], 4.0, 12)},
        "mechadendrite_left": {"rotation": track(lambda t: [6 * sin(t, 0.5), -8 * sin(t, 0.8), 0], 4.0, 12)},
        "mechadendrite_left_2": {"rotation": track(lambda t: [10 * sin(t, 0.7), 0, 0], 4.0, 12)},
        "robe": {"rotation": track(lambda t: [1 * sin(t), 0, 0], 3.0, 12)},
    }, extra_walk={
        "robe": {"rotation": track(lambda t: [4 * abs(sin(t)), 0, 2 * sin(t)], 1.0)},
        "mechadendrite_right": {"rotation": track(lambda t: [8 * sin(t), 0, 0], 1.0)},
        "mechadendrite_left": {"rotation": track(lambda t: [-8 * sin(t), 0, 0], 1.0)},
    })
    anims["misc.interact"] = {"length": 1.6, "bones": {  # благословение ключом-топором
        "right_arm": {"rotation": keys([(0, [0, 0, 0]), (0.4, [-150, 0, 10]), (0.9, [-150, 0, 10]), (1.2, [-60, 0, 0]),
                                        (1.6, [0, 0, 0])])},
        "head": {"rotation": keys([(0, [0, 0, 0]), (0.4, [-15, 0, 0]), (1.2, [10, 0, 0]), (1.6, [0, 0, 0])])},
        "mechadendrite_right": {"rotation": keys([(0, [0, 0, 0]), (0.6, [-30, 20, 0]), (1.6, [0, 0, 0])])},
        "mechadendrite_left": {"rotation": keys([(0, [0, 0, 0]), (0.6, [-30, -20, 0]), (1.6, [0, 0, 0])])},
    }}
    finish(m, "tech_priest", {"": TECH_PRIEST}, anims)
    # тёмный техножрец — та же геометрия и анимации, своя текстура
    base, glow = m.paint(DARK_TECH_PRIEST, seed=91)
    save_png(base, "entity", "dark_tech_priest.png")
    save_png(glow, "entity", "dark_tech_priest_glow.png")


# ------------------------------------------------------------------ М3: сервитор

def servitor():
    m = Model("servitor", atlas_w=128)
    m.bone("root", [0, 0, 0])
    for side, sx in (("right", -1), ("left", 1)):
        leg = m.bone(f"{side}_leg", [2.5 * sx, 11, 0], "root")
        x0 = -4.5 if sx < 0 else 1.5
        leg.cube([x0, 5, -2], [3, 6, 4], "metal")
        leg.cube([x0 + 0.5, 1, -1.5], [2, 4, 3], "cable")
        leg.cube([x0 - 0.5, 0, -3.5], [4, 2, 5], "dark")

    body = m.bone("body", [0, 11, 0], "root", rotation=[18, 0, 0])  # сгорблен
    body.cube([-4, 11, -2.5], [8, 3, 5], "dark")
    body.cube([-4, 14, -2], [8, 9, 5], "flesh")
    body.cube([-4.5, 18, -2.6], [9, 4, 1], "metal", deco={"north": cog_deco})
    body.cube([-1, 14, 2.5], [2, 9, 2], "cable")     # кабели вдоль позвоночника
    body.cube([-3, 20, 2.5], [6, 3, 2], "metal")
    body.cube([-2.5, 21, 4.5], [1, 1, 1], "glow2", glow="all")

    head = m.bone("head", [0, 23, -1], "body")
    head.cube([-3, 23, -4], [6, 6, 6], "skin", deco={"north": servitor_face})
    head.cube([-3.3, 26.5, -4.3], [3, 3, 7], "metal_plain")   # пластина на черепе
    head.cube([0.5, 25.5, -4.6], [2, 2, 1], "glow", glow="all")  # аугметический глаз
    head.cube([-0.5, 24, 2], [1, 1, 3], "cable")

    ra = m.bone("right_arm", [-5, 22, 0], "body")
    ra.cube([-6.5, 15, -1.5], [3, 7, 3], "flesh")
    item = m.bone("right_item", [-5, 15, 0], "right_arm")
    item.cube([-6.5, 9, -2], [3, 6, 4], "metal")            # сварочный аппарат вместо кисти
    item.cube([-5.5, 6, -1.5], [1, 3, 1], "dark_plain")
    item.cube([-5.5, 5, -1.5], [1, 1, 1], "glow2", glow="all")
    la = m.bone("left_arm", [5, 22, 0], "body")
    la.cube([3.5, 13, -1.5], [3, 9, 3], "metal")
    li = m.bone("left_item", [5, 13, 0], "left_arm")
    li.cube([3.5, 10, -2], [3, 3, 4], "dark")
    li.cube([3.5, 8, -2], [1, 2, 1], "metal_plain")          # клешня
    li.cube([5.5, 8, -2], [1, 2, 1], "metal_plain")

    anims = humanoid_anims(walk_amp=16, arm_amp=8, walk_len=1.3, bob=0.6)
    anims["work.repair"] = {"length": 1.2, "loop": True, "bones": {
        "right_arm": {"rotation": track(lambda t: [-70 + 6 * sin(t * 4 % 1), 4 * sin(t, 0.3), 0], 1.2)},
        "left_arm": {"rotation": track(lambda t: [-50, 0, -6 * sin(t)], 1.2)},
        "head": {"rotation": track(lambda t: [15, 4 * sin(t), 0], 1.2)},
    }}
    anims["misc.rest"] = {"length": 1.0, "loop": "hold_on_last_frame", "bones": {  # отключён
        "head": {"rotation": keys([(0, [0, 0, 0]), (1.0, [40, 0, 8])])},
        "right_arm": {"rotation": keys([(0, [0, 0, 0]), (1.0, [10, 0, 6])])},
        "left_arm": {"rotation": keys([(0, [0, 0, 0]), (1.0, [10, 0, -6])])},
        "body": {"rotation": keys([(0, [0, 0, 0]), (1.0, [12, 0, 0])])},
    }}
    finish(m, "servitor", {"": SERVITOR}, anims)


# ------------------------------------------------------------------ М4: кровопускатель

def bloodletter():
    m = Model("bloodletter", atlas_w=128)
    m.bone("root", [0, 0, 0])
    for side, sx in (("right", -1), ("left", 1)):
        x = 2.5 * sx
        leg = m.bone(f"{side}_leg", [x, 17, 0], "root")
        leg.cube([x - 1.5, 10, -3], [3, 7, 4], "flesh", rotation=[-20, 0, 0], pivot=[x, 17, 0])
        leg.cube([x - 1, 3, -0.5], [2, 8, 2], "flesh", rotation=[22, 0, 0], pivot=[x, 10, 0])
        leg.cube([x - 1.5, 0, -2.5], [3, 3, 3], "claw")      # копыто

    body = m.bone("body", [0, 17, 0], "root", rotation=[10, 0, 0])
    body.cube([-3, 17, -2], [6, 5, 4], "flesh")
    body.cube([-5, 22, -3], [10, 8, 6], "flesh")
    body.cube([-3.5, 15, -2.5], [7, 3, 5], "brass", deco={"north": star_deco(0.4, "dark")})
    for i in range(3):
        body.cube([-0.5, 23 + i * 2.5, 3], [1, 2, 2], "horn")   # шипы хребта

    head = m.bone("head", [0, 30, -1], "body")
    head.cube([-2.5, 30, -5], [5, 6, 6], "skin", deco={"north": bloodletter_face})
    head.cube([-2, 29, -6], [4, 2, 4], "skin")                 # вытянутая челюсть
    head.cube([-2, 33, -5.6], [1, 1, 1], "glow", glow="all")
    head.cube([1, 33, -5.6], [1, 1, 1], "glow", glow="all")
    for sx in (-1, 1):
        x = 2.2 * sx
        head.cube([x - 1, 35, -2], [2, 3, 2], "horn", rotation=[-25, 0, 12 * sx], pivot=[x, 35, -1])
        head.cube([x - 0.5, 37, -0.5], [1, 6, 1], "horn", rotation=[-55, 0, 14 * sx], pivot=[x, 37, 0])

    for side, sx in (("right", -1), ("left", 1)):
        arm = m.bone(f"{side}_arm", [6 * sx, 29, 0], "body")
        x0 = -8 if sx < 0 else 5
        arm.cube([x0, 17, -1.5], [3, 12, 3], "flesh")
        arm.cube([x0, 14, -2], [3, 3, 4], "claw")
    item = m.bone("right_item", [-6.5, 15, 0], "right_arm")
    item.cube([-7, 11, -0.5], [1, 5, 1], "dark_plain")       # рукоять
    item.cube([-8, 16, -1.5], [3, 1, 3], "brass")            # гарда
    item.cube([-7, 17, -1.5], [1, 17, 3], "blade", glow=rune_glow)  # адский клинок

    anims = humanoid_anims(walk_amp=26, arm_amp=20, walk_len=0.9, run_len=0.5, extra_idle={
        "body": {"rotation": track(lambda t: [3 * sin(t), 0, 0], 2.0, 12)},
    })
    anims["attack.swing"] = {"length": 0.6, "bones": {  # рубящий удар сверху
        "right_arm": {"rotation": keys([(0, [0, 0, 0]), (0.22, [-170, -10, 0]), (0.34, [-30, 10, 0]), (0.6, [0, 0, 0])])},
        "left_arm": {"rotation": keys([(0, [0, 0, 0]), (0.22, [-40, 0, -20]), (0.6, [0, 0, 0])])},
        "body": {"rotation": keys([(0, [0, 0, 0]), (0.22, [-10, 0, 0]), (0.34, [18, 0, 0]), (0.6, [0, 0, 0])])},
    }}
    finish(m, "bloodletter", {"": BLOODLETTER}, anims)


# ------------------------------------------------------------------ М5: розовый и синий ужасы

def horror():
    m = Model("pink_horror", atlas_w=128)
    m.bone("root", [0, 0, 0])
    for side, sx in (("right", -1), ("left", 1)):
        leg = m.bone(f"{side}_leg", [3 * sx, 7, 0], "root")
        x0 = -5 if sx < 0 else 1
        leg.cube([x0, 2, -2], [4, 5, 4], "flesh")
        leg.cube([x0 - 0.5, 0, -4], [5, 2, 5], "claw")
    body = m.bone("body", [0, 7, 0], "root")
    body.cube([-6, 7, -4], [12, 12, 8], "flesh", deco={"north": horror_face})
    head = m.bone("head", [0, 19, 0], "body")
    head.cube([-4, 19, -3], [8, 3, 6], "skin")
    head.cube([-2, 22, -2], [4, 2, 4], "skin")
    head.cube([-0.5, 24, -0.5], [1, 2, 1], "claw")
    for side, sx in (("right", -1), ("left", 1)):
        arm = m.bone(f"{side}_arm", [6.5 * sx, 17, 0], "body")
        x0 = -9.5 if sx < 0 else 6.5
        arm.cube([x0, 9, -1.5], [3, 8, 3], "skin", rotation=[0, 0, -12 * sx], pivot=[6.5 * sx, 17, 0])
        arm.cube([x0 - 0.5 * sx, 4, -2], [4, 5, 4], "skin")
        it = m.bone(f"{side}_item", [x0 + 1.5, 4, 0], f"{side}_arm")
        it.cube([x0, 0.5, -2], [3, 3, 3], "glow", glow="all")   # варп-пламя Тзинча в ладонях

    anims = {
        "misc.idle": {"length": 1.6, "loop": True, "bones": {
            "body": {"position": track(lambda t: [0, 0.6 * abs(sin(t)), 0], 1.6, 12),
                     "rotation": track(lambda t: [0, 0, 4 * sin(t)], 1.6, 12)},
            "right_arm": {"rotation": track(lambda t: [-20 + 25 * sin(t), 0, 10 * sin(t, 0.3)], 1.6, 12)},
            "left_arm": {"rotation": track(lambda t: [-20 + 25 * sin(t, 0.5), 0, -10 * sin(t, 0.8)], 1.6, 12)},
            "head": {"rotation": track(lambda t: [0, 10 * sin(t), 6 * sin(t, 0.25)], 1.6, 12)},
        }},
        "move.walk": {"length": 0.6, "loop": True, "bones": {
            "right_leg": {"rotation": track(lambda t: [30 * sin(t), 0, 0], 0.6)},
            "left_leg": {"rotation": track(lambda t: [-30 * sin(t), 0, 0], 0.6)},
            "body": {"position": track(lambda t: [0, 1.2 * abs(sin(t)), 0], 0.6),
                     "rotation": track(lambda t: [0, 0, 8 * sin(t)], 0.6)},
            "right_arm": {"rotation": track(lambda t: [-40 + 30 * sin(t), 0, 15], 0.6)},
            "left_arm": {"rotation": track(lambda t: [-40 - 30 * sin(t), 0, -15], 0.6)},
        }},
        "attack.cast": {"length": 0.7, "bones": {
            "right_arm": {"rotation": keys([(0, [0, 0, 0]), (0.25, [-60, 30, 0]), (0.4, [-95, -10, 0]), (0.7, [0, 0, 0])])},
            "left_arm": {"rotation": keys([(0, [0, 0, 0]), (0.25, [-60, -30, 0]), (0.4, [-95, 10, 0]), (0.7, [0, 0, 0])])},
            "body": {"rotation": keys([(0, [0, 0, 0]), (0.25, [-8, 0, 0]), (0.4, [10, 0, 0]), (0.7, [0, 0, 0])])},
        }},
    }
    finish(m, "pink_horror", {"": PINK_HORROR}, anims)
    base, glow = m.paint(BLUE_HORROR, seed=17)
    save_png(base, "entity", "blue_horror.png")
    save_png(glow, "entity", "blue_horror_glow.png")


# ------------------------------------------------------------------ М8: культист

def cultist():
    m = Model("cultist", atlas_w=128)
    m.bone("root", [0, 0, 0])
    for side, sx in (("right", -1), ("left", 1)):
        leg = m.bone(f"{side}_leg", [2 * sx, 11, 0], "root")
        x0 = -4 if sx < 0 else 0
        leg.cube([x0, 3, -2], [4, 8, 4], "rag2")
        leg.cube([x0, 0, -2.5], [4, 3, 5], "leather")
    body = m.bone("body", [0, 11, 0], "root")
    body.cube([-4, 11, -2], [8, 10, 4], "rag")
    body.cube([-4.5, 12, -2.5], [9, 2, 5], "leather", deco={"north": star_deco(0.45, "brass")})
    robe = m.bone("robe", [0, 12, 0], "body")
    robe.cube([-4.5, 6, -2.5], [9, 6, 5], "rag")
    head = m.bone("head", [0, 21, 0], "body")
    head.cube([-3.5, 21, -3.5], [7, 7, 7], "skin")
    head.cube([-2.5, 21.5, -4.5], [5, 4, 1], "dark_plain", deco={"north": gasmask})
    head.cube([-2, 24, -4.8], [1.5, 1, 1], "glow", glow="all")
    head.cube([0.5, 24, -4.8], [1.5, 1, 1], "glow", glow="all")
    head.cube([-1, 20.5, -5.5], [2, 2, 1], "metal_plain")    # фильтр респиратора
    hd = m.bone("hood", [0, 21, 0], "head")
    hood(hd, -4.5, 20.5, -4.5, 9, 9, 9)
    for side, sx in (("right", -1), ("left", 1)):
        arm = m.bone(f"{side}_arm", [5.5 * sx, 20, 0], "body")
        x0 = -7 if sx < 0 else 4
        arm.cube([x0, 10, -1.5], [3, 11, 3], "rag")
        arm.cube([x0, 9, -1.5], [3, 1, 3], "skin")
    item = m.bone("right_item", [-5.5, 10, 0], "right_arm")
    knife = m.bone("knife", [-5.5, 10, 0], "right_item")       # вариант 0
    knife.cube([-6, 8.5, -1], [1, 2, 1], "leather")
    knife.cube([-6, 9, -5], [1, 1, 4], "blade")
    autogun = m.bone("autogun", [-5.5, 10, 0], "right_item")   # вариант 1
    autogun.cube([-6.5, 8, -8], [2, 3, 9], "dark_plain")
    autogun.cube([-6.5, 5, -5], [2, 3, 2], "metal_plain")
    autogun.cube([-6, 9, -10], [1, 1, 2], "metal_plain")
    stubber = m.bone("stubber", [-5.5, 10, 0], "right_item")   # вариант 2
    stubber.cube([-7, 7, -10], [3, 4, 12], "dark")
    stubber.cube([-6, 8.5, -14], [1, 1, 4], "metal_plain")
    stubber.cube([-7, 3, -6], [3, 4, 3], "brass")

    anims = humanoid_anims(walk_amp=30, arm_amp=24)
    finish(m, "cultist", {"": CULTIST[0], "_1": CULTIST[1], "_2": CULTIST[2]}, anims)


# ------------------------------------------------------------------ М9: одержимый жрец культа

def possessed_priest():
    m = Model("possessed_priest", atlas_w=128)
    m.bone("root", [0, 0, 0])
    for side, sx in (("right", -1), ("left", 1)):
        leg = m.bone(f"{side}_leg", [2 * sx, 12, 0], "root")
        leg.cube([-4 if sx < 0 else 0, 0, -2], [4, 12, 4], "leather")
    body = m.bone("body", [0, 12, 0], "root")
    body.cube([-4.5, 12, -2.5], [9, 11, 5], "robe_plain", glow=veins_glow)
    body.cube([-1.5, 13, -3], [3, 9, 1], "brass", deco={"north": star_deco(0.6, "dark")})
    robe = m.bone("robe", [0, 14, 0], "body")
    robe.cube([-5, 0, -3.5], [10, 14, 7], "robe")
    head = m.bone("head", [0, 23, 0], "body")
    head.cube([-3, 23, -3], [6, 7, 6], "face", deco={"north": priest_face_human}, glow=veins_glow)
    head.cube([-2, 26, -3.3], [1, 1, 1], "glow", glow="all")
    head.cube([1, 26, -3.3], [1, 1, 1], "glow", glow="all")
    hd = m.bone("hood", [0, 23, 0], "head")
    hood(hd, -4, 22.5, -4, 8, 9, 8)

    # кости демона: скрыты в первой фазе, рендер включает их во второй
    horns = m.bone("daemon_horns", [0, 30, 0], "head")
    for sx in (-1, 1):
        x = 3 * sx
        horns.cube([x - 1, 29, -1], [2, 4, 2], "horn", rotation=[0, 0, 35 * sx], pivot=[x, 29, 0])
        horns.cube([x + 1.5 * sx - 0.5, 32, -0.5], [1, 6, 1], "horn", rotation=[-20, 0, 15 * sx], pivot=[x, 32, 0])
    jaw = m.bone("daemon_jaw", [0, 23, -3], "head")
    jaw.cube([-2.5, 21, -4.5], [5, 2, 3], "flesh", glow=veins_glow)
    jaw.cube([-2, 22.5, -4.6], [4, 1, 1], "glow", glow="all")
    spine = m.bone("daemon_spine", [0, 18, 2.5], "body")
    for i in range(4):
        spine.cube([-0.5, 13 + i * 3, 2.5], [1, 2, 3 + (i % 2)], "horn", rotation=[-30, 0, 0], pivot=[0, 13 + i * 3, 2.5])
    for sx in (-1, 1):
        spine.cube([-4 * sx - (2 if sx > 0 else 0) + (0 if sx > 0 else -0), 15, 2.5], [2, 6, 2], "flesh",
                   rotation=[0, 0, 20 * sx], pivot=[-3 * sx, 18, 3])

    for side, sx in (("right", -1), ("left", 1)):
        arm = m.bone(f"{side}_arm", [5.5 * sx, 22, 0], "body")
        x0 = -7.5 if sx < 0 else 4.5
        arm.cube([x0, 12, -2], [3, 10, 4], "sleeve")
        arm.cube([x0 + 0.5, 10, -1.5], [2, 2, 3], "skin")
        claw = m.bone(f"daemon_claw_{side}", [x0 + 1.5, 11, 0], f"{side}_arm")
        claw.cube([x0 - 0.5, 8, -2.5], [4, 4, 5], "flesh", glow=veins_glow)
        for k in range(3):
            claw.cube([x0 + k * 1.2 - 0.2, 3, -2.5 + k * 1.5], [1, 5, 1], "claw", rotation=[-15, 0, 0],
                      pivot=[x0 + k, 8, 0])
    staff = m.bone("right_item", [-6, 11, 0], "right_arm")
    staff.cube([-6.5, 2, -0.5], [1, 24, 1], "dark_plain")
    staff.cube([-8, 26, -0.5], [4, 4, 1], "brass", deco={"north": star_deco(0.5, "dark")})
    staff.cube([-6.5, 27.5, -1], [1, 1, 1], "glow", glow="all")

    anims = humanoid_anims(walk_amp=18, arm_amp=14, extra_walk={
        "robe": {"rotation": track(lambda t: [4 * abs(sin(t)), 0, 2 * sin(t)], 1.0)},
    })
    anims["misc.transform"] = {"length": 3.0, "bones": {  # демон рвёт жреца изнутри
        "body": {"rotation": keys([(0, [0, 0, 0]), (0.5, [20, 0, 0]), (1.0, [15, 6, -6]), (1.3, [18, -6, 6]),
                                   (2.0, [-25, 0, 0]), (2.6, [-10, 0, 0]), (3.0, [0, 0, 0])])},
        "head": {"rotation": keys([(0, [0, 0, 0]), (0.5, [30, 0, 0]), (1.6, [20, 10, 0]), (2.0, [-50, 0, 0]),
                                   (3.0, [0, 0, 0])])},
        "right_arm": {"rotation": keys([(0, [0, 0, 0]), (0.5, [-20, 0, 30]), (2.0, [-30, 0, 100]), (3.0, [0, 0, 0])])},
        "left_arm": {"rotation": keys([(0, [0, 0, 0]), (0.5, [-20, 0, -30]), (2.0, [-30, 0, -100]), (3.0, [0, 0, 0])])},
    }}
    anims["attack.swing"] = {"length": 0.7, "bones": {  # удар когтями во второй фазе
        "right_arm": {"rotation": keys([(0, [0, 0, 0]), (0.25, [-120, 0, 40]), (0.4, [-40, 0, -20]), (0.7, [0, 0, 0])])},
        "left_arm": {"rotation": keys([(0, [0, 0, 0]), (0.35, [-120, 0, -40]), (0.5, [-40, 0, 20]), (0.7, [0, 0, 0])])},
        "body": {"rotation": keys([(0, [0, 0, 0]), (0.25, [-8, 10, 0]), (0.45, [12, -10, 0]), (0.7, [0, 0, 0])])},
    }}
    finish(m, "possessed_priest", {"": PRIEST, "_daemon": PRIEST_DAEMON}, anims)


# ------------------------------------------------------------------ М6: десантный модуль

def boarding_pod():
    m = Model("boarding_pod", atlas_w=256)
    hull = m.bone("hull", [0, 0, 0])
    hull.cube([-10, 6, -10], [20, 42, 20], "interior")
    hull.cube([-8, 0, -8], [16, 6, 16], "dark")                     # нос, уходит в обшивку
    hull.cube([-4, -5, -4], [8, 5, 8], "metal_plain")               # бур
    hull.cube([-12, 48, -12], [24, 5, 24], "dark", deco={"up": star_deco(0.45, "brass")})
    for (x, z) in ((-8, -8), (4, -8), (-8, 4), (4, 4)):            # дюзы
        hull.cube([x, 53, z], [4, 4, 4], "metal_plain")
        hull.cube([x + 1, 56.5, z + 1], [2, 1, 2], "glow", glow="all")
    hull.cube([-6, 30, -6], [12, 3, 12], "glow2", glow="all")        # красный свет внутри
    for k, (sx, sz) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        hull.cube([10 * sx - 1, 52, 10 * sz - 1], [2, 8, 2], "horn", rotation=[-20 * sz, 0, 20 * -sx],
                  pivot=[10 * sx, 52, 10 * sz])                     # рога-шипы на корме

    # четыре лепестка: north/south вращаются по X, east/west — по Z
    petals = {
        "petal_north": ([0, 6, -12], [-12, 6, -15], [24, 42, 3]),
        "petal_south": ([0, 6, 12], [-12, 6, 12], [24, 42, 3]),
        "petal_east": ([12, 6, 0], [12, 6, -12], [3, 42, 24]),
        "petal_west": ([-12, 6, 0], [-15, 6, -12], [3, 42, 24]),
    }
    for name, (pivot, origin, size) in petals.items():
        p = m.bone(name, pivot, "hull")
        outer = {"petal_north": "north", "petal_south": "south", "petal_east": "west", "petal_west": "east"}[name]
        p.cube(origin, size, "metal", deco={outer: star_deco(0.36, "brass")})
        # бронированное ребро вдоль лепестка
        if size[0] > size[2]:
            p.cube([origin[0] + 10, origin[1] + 4, origin[2] + (-1 if pivot[2] < 0 else 3)], [4, 34, 1], "brass")
        else:
            p.cube([origin[0] + (-1 if pivot[0] < 0 else 3), origin[1] + 4, origin[2] + 10], [1, 34, 4], "brass")

    open_ = {"petal_north": [-95, 0, 0], "petal_south": [95, 0, 0], "petal_east": [0, 0, -95], "petal_west": [0, 0, 95]}
    anims = {
        "misc.idle": {"length": 2.0, "loop": True, "bones": {
            "hull": {"position": track(lambda t: [0.1 * sin(t * 5 % 1), 0, 0.1 * sin(t * 7 % 1)], 2.0, 12)},
        }},
        "misc.deploy": {"length": 1.4, "loop": "hold_on_last_frame", "bones": {
            name: {"rotation": keys([(0, [0, 0, 0]), (0.25, [r * 0.05 for r in rot]), (1.1, [r * 1.05 for r in rot]),
                                     (1.4, rot)])}
            for name, rot in open_.items()
        }},
        "misc.open": {"length": 0.1, "loop": "hold_on_last_frame", "bones": {
            name: {"rotation": keys([(0, rot), (0.1, rot)])} for name, rot in open_.items()
        }},
    }
    finish(m, "boarding_pod", {"": POD}, anims)


if __name__ == "__main__":
    import dark_priest
    import tech_priest
    tech_priest.generate()   # М1 по концепту автора (Meh.jpg)
    dark_priest.generate()   # М2 по концепту автора (DarkMeh.jpg), 2×3 блока
    servitor()
    bloodletter()
    horror()
    cultist()
    possessed_priest()
    boarding_pod()
