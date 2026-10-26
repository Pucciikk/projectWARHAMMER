"""
Техножрец Механикус (М1) по концепту автора (Meh.jpg), 64 px на блок.

Длинная винно-малиновая ряса до земли с кремовой зубчатой кромкой по подолу, разрезу и манжетам;
высокий острый капюшон, внутри темнота и одна зелёная линза; пучок шлангов от лица в грудной прибор
с зелёным экраном; янтарная лампа на макушке. Справа — многосуставная серворука с буром над плечом,
слева — три ребристых механодендрита с клешнями. Широкий клёпаный пояс, два черепа на шлангах,
цепи и фонарь-кадило. Высокий Омниссианский топор (выше головы) — в левой руке.

Углы серворуки и механодендритов подобраны перебором так, чтобы они не проходили сквозь тело и капюшон.
"""
import zlib

import numpy as np

import hd
from geo import MATERIALS, Model, draw_rect, keys, mix, save_png, shade, sin, track, write_animations
from priest_hd import _icon, _paste, cog_blade, emblem, skull_side

PAL = dict(
    robe=(130, 46, 56), robe_in=(52, 16, 22), hood=(142, 54, 66), trim=(214, 204, 178), void=(16, 14, 16),
    metal=(150, 152, 156), hose=(132, 130, 126), dark=(50, 50, 54), brass=(180, 148, 80), bone=(206, 194, 160),
    leather=(80, 56, 40), cable=(34, 34, 38), glow=(150, 255, 110), glow2=(255, 196, 110), glow3=(255, 50, 40),
    screen=(10, 26, 12), mask=(70, 72, 76), inner=(34, 30, 32),
)

MATERIALS.update({
    "hd_trim": hd.hd_cloth("trim", folds=False, dirty=True),
    "hd_hood": hd.hd_cloth("hood", dirty=False),
    "hd_hose": hd.hd_cable("hose"),
    "hd_void": hd.hd_flat("void", 3, edge=False),
    "hd_glow3": __import__("geo").mat_glow("glow3"),
})


def _studded(region, face, pal, rng):
    """Широкий пояс: металл с двумя рядами заклёпок."""
    MATERIALS["hd_metal_plain"](region, face, pal, rng)
    h, w = region.shape[:2]
    for y in (2, h - 3):
        if 0 <= y < h:
            for x in range(2, w - 1, 4):
                region[y:y + 2, x:x + 2, :3] = shade(pal["metal"], 1.5)
                region[min(h - 1, y + 2), x:x + 2, :3] = shade(pal["metal"], 0.45)


def _chain(region, face, pal, rng):
    h, w = region.shape[:2]
    region[..., 3] = 0
    for y in range(0, h, 3):
        region[y:y + 2, :, :3] = shade(pal["metal"], 0.9 if (y // 3) % 2 else 0.6)
        region[y:y + 2, :, 3] = 255


MATERIALS["hd_studded"] = _studded
MATERIALS["hd_chain"] = _chain


# ------------------------------------------------------------------ рисунки

def cren_top(region, S, pal):
    """Кремовая кромка с зубцами вверх: квадратные выступы через один — как на концепте."""
    h, w = region.shape[:2]
    t, tw = S, int(1.5 * S)  # зубец: пиксель модели в высоту, полтора в ширину
    for x in range(0, w, 2 * tw):
        region[:t, x + tw:x + 2 * tw, :3] = shade(pal["robe"], 0.9)


def cren_side(region, S, pal):
    """Вертикальная кромка разреза: зубцы наружу."""
    h, w = region.shape[:2]
    tw = int(1.5 * S)
    for y in range(0, h, 2 * tw):
        region[y + tw:y + 2 * tw, w - S // 2:, :3] = shade(pal["robe"], 0.9)


def screen_wave(region, S, pal):
    h, w = region.shape[:2]
    region[...] = (*pal["screen"], 255)
    for x in range(1, w - 1):
        y = int(h / 2 + np.sin(x * 0.9) * h * 0.28)
        region[max(0, y):y + 1, x, :3] = pal["glow"]


def screen_glow(g, region, face, S, pal):
    if face != "north":
        return
    m = region[..., 1] > 120
    g[m, :3] = region[m, :3]
    g[m, 3] = 255


def skull_face(lens):
    """Череп на шланге: глазницы, нос, зубы; у одного — красная аугметическая линза, у другого шестерня."""
    def f(region, S, pal):
        h, w = region.shape[:2]
        hole = (26, 20, 16)

        def draw(d, W, H):
            for ex in (0.28, 0.72):
                d.ellipse([W * ex - W * 0.15, H * 0.3, W * ex + W * 0.15, H * 0.56], fill=hole + (255,))
            d.polygon([(W * 0.5, H * 0.55), (W * 0.42, H * 0.7), (W * 0.58, H * 0.7)], fill=hole + (255,))
            for i in range(5):
                x = W * (0.25 + i * 0.125)
                d.line([(x, H * 0.78), (x, H * 0.95)], fill=hole + (255,), width=max(1, W // 24))
            if lens == "cog":
                d.ellipse([W * 0.58, H * 0.12, W * 0.92, H * 0.46], outline=tuple(pal["brass"]) + (255,), width=W // 10)
        _paste(region, _icon(w, h, draw))
    return f


# ------------------------------------------------------------------ сборка

def mx(x, w, sx):
    """Правая сторона (−X) как есть, левая — зеркально."""
    return x if sx < 0 else -(x + w)


def tendril(m, name, parent, start, rots, segs, tip):
    """Цепочка костей вдоль +Y, каждое звено — шланг с муфтой; на конце — инструмент."""
    x, y, z = start
    bone_parent = parent
    for k, (r, ln) in enumerate(zip(rots, segs)):
        bn = name if k == 0 else f"{name}_{k + 1}"
        b = m.bone(bn, [x, y, z], bone_parent, rotation=r)
        b.cube([x - 0.5, y, z - 0.5], [1, ln, 1], "hd_hose")
        if k % 2:
            b.cube([x - 0.6, y + ln - 0.5, z - 0.6], [1.2, 0.5, 1.2], "hd_dark_plain")
        bone_parent, y = bn, y + ln
    t = m.bone(f"{name}_tip", [x, y, z], bone_parent)
    tip(t, x, y, z)


def claw(t, x, y, z):
    t.cube([x - 0.6, y, z - 0.6], [1.2, 0.9, 1.2], "hd_dark")
    t.cube([x - 0.65, y + 0.9, z - 0.25], [0.4, 1.75, 0.5], "hd_metal_plain", rotation=[0, 0, 22], pivot=[x - 0.45, y + 0.9, z])
    t.cube([x + 0.25, y + 0.9, z - 0.25], [0.4, 1.75, 0.5], "hd_metal_plain", rotation=[0, 0, -22], pivot=[x + 0.45, y + 0.9, z])


def build():
    m = Model("tech_priest", S=4, atlas_w=128)
    m.bone("root", [0, 0, 0])

    # --- ноги: тёмные штанины и кованые сапоги, видны в разрезе рясы
    for side, sx in (("right", -1), ("left", 1)):
        leg = m.bone(f"{side}_leg", [2 * sx, 12, 0], "root")
        leg.cube([mx(-3.75, 3.5, sx), 2, -1.75], [3.5, 10, 3.5], "hd_inner")
        leg.cube([mx(-4.25, 4.25, sx), 0, -3], [4.25, 2.25, 5], "hd_dark")
        leg.cube([mx(-4.25, 4.25, sx), 0, -3.75], [4.25, 1.5, 1], "hd_metal")

    body = m.bone("body", [0, 12, 0], "root")
    # --- ряса: две полы с разрезом спереди, кромка с зубцами по подолу и по разрезу
    for side, sx in (("right", -1), ("left", 1)):
        r = m.bone(f"robe_{side}", [2.75 * sx, 12, 0], "body")
        r.cube([mx(-5.25, 4.5, sx), 3.5, -3.75], [4.5, 8.5, 7.5], "hd_robe_plain", tint={"down": 0.3})
        r.cube([mx(-5.4, 4.65, sx), 0.5, -3.9], [4.65, 3, 7.8], "hd_trim",
               deco={f: cren_top for f in ("north", "south", "east", "west")})
        r.cube([mx(-1.75, 1.25, sx), 3.5, -3.95], [1.25, 8.5, 0.5], "hd_trim",
               deco={"north": cren_side})
    body.cube([-4.5, 12, -2.75], [9, 11.5, 5.5], "hd_robe_plain")
    body.cube([-4.9, 11, -3.2], [9.8, 2.25, 6.4], "hd_studded")
    # грудной прибор с экраном и пучок шлангов от лица
    body.cube([-2, 15, -3.9], [4, 3.5, 1.25], "hd_metal")
    body.cube([-1.5, 15.75, -4.05], [3, 2, 0.25], "hd_screen", deco={"north": screen_wave}, glow=screen_glow)
    for k, x in enumerate((-1.6, -0.8, 0, 0.8, 1.6)):
        body.cube([x - 0.3, 18.5, -3.7 + abs(x) * 0.15], [0.6, 6, 0.6], "hd_hose",
                  rotation=[0, 0, x * 4], pivot=[x, 18.5, -3.4])
    # шланги к черепам у пояса и сами черепа
    body.cube([-2.6, 8.75, -4.1], [0.6, 6.5, 0.6], "hd_hose", rotation=[0, 0, -8], pivot=[-2.3, 15, -3.8])
    body.cube([1.9, 7.75, -4.1], [0.6, 7.5, 0.6], "hd_hose", rotation=[0, 0, 6], pivot=[2.2, 15, -3.8])
    body.cube([-3.75, 6, -5], [2.75, 2.75, 2.5], "hd_bone", deco={"north": skull_face("red")})
    body.cube([-3.3, 7.6, -5.15], [0.7, 0.7, 0.25], "hd_glow3", glow="all")
    body.cube([0.9, 5, -5], [2.75, 2.75, 2.5], "hd_bone", deco={"north": skull_face("cog")})
    body.cube([-2.75, 2.5, -4.25], [0.5, 3.5, 0.5], "hd_hose")
    body.cube([2, 1.75, -4.25], [0.5, 3.25, 0.5], "hd_hose")
    # цепи с пояса
    body.cube([-4.4, 4, -3.5], [0.4, 7, 0.4], "hd_chain")
    body.cube([3.7, 3, -3.5], [0.4, 8, 0.4], "hd_chain")
    # ранец под рясой и шланги через плечи
    body.cube([-4.5, 17, 2.75], [4, 5.5, 2], "hd_dark")
    body.cube([-4, 18, 4.5], [3, 3.5, 0.5], "hd_metal_plain")
    body.cube([0.5, 14, 2.75], [4, 9, 1.75], "hd_dark")             # крепление механодендритов
    for sx in (-1, 1):
        x = 4.6 * sx - 0.4
        body.cube([x, 20.5, 3], [0.8, 3, 0.8], "hd_hose")
        body.cube([x, 23.4, -3.4], [0.8, 0.8, 7.2], "hd_hose")
        body.cube([x, 20.25, -3.75], [0.8, 3.25, 0.8], "hd_hose")
    # шланг по земле позади
    body.cube([-1.2, 0.75, 4.25], [0.8, 13.5, 0.8], "hd_hose")
    body.cube([-1.2, 0, 4.25], [0.8, 0.8, 9], "hd_hose")

    # пелерина с кромкой
    mantle = m.bone("mantle", [0, 23, 0], "body")
    mantle.cube([-6, 19.25, -3.4], [12, 4, 6.8], "hd_robe_plain", tint={"down": 0.35})
    mantle.cube([-6.15, 19, -3.55], [12.3, 1.25, 7.1], "hd_trim")

    # --- фонарь-кадило на правом бедре
    censer = m.bone("censer", [-5.2, 11, -1], "body")
    censer.cube([-5.4, 4.25, -1.2], [0.4, 6.75, 0.4], "hd_chain")
    censer.cube([-6.25, 1, -2.1], [2, 3.25, 2], "hd_brass")
    censer.cube([-6, 1.5, -2.25], [1.5, 2.25, 0.25], "hd_glow2", glow="all")
    censer.cube([-6.4, 4.25, -2.25], [2.3, 0.5, 2.3], "hd_dark_plain")

    # --- голова: темнота под капюшоном, одна зелёная линза, ребризер; капюшон высокий и острый
    head = m.bone("head", [0, 23, 0], "body")
    head.cube([-3.25, 22.75, -3], [6.5, 8.25, 6], "hd_void")
    head.cube([-1.1, 26.6, -3.45], [2.2, 2.2, 0.5], "hd_brass")
    head.cube([-0.75, 26.95, -3.6], [1.5, 1.5, 0.25], "hd_glow", glow="all")
    head.cube([1.4, 27.6, -3.2], [0.5, 0.5, 0.25], "hd_glow", glow="all")
    head.cube([-1.9, 25.9, -3.2], [0.5, 0.5, 0.25], "hd_glow", glow="all")
    head.cube([-1.75, 24, -3.4], [3.5, 1.5, 0.5], "hd_metal")
    hood = m.bone("hood", [0, 23, 0], "head")
    hood.cube([-4.75, 22.5, -5], [1.5, 9, 9.5], "hd_hood", tint={"west": 0.25})
    hood.cube([3.25, 22.5, -5], [1.5, 9, 9.5], "hd_hood", tint={"east": 0.25})
    hood.cube([-3.25, 22.5, 3], [6.5, 9, 1.25], "hd_hood")
    hood.cube([-4.75, 31, -5], [9.5, 1.5, 9.5], "hd_hood", tint={"down": 0.2})
    hood.cube([-4.75, 30.25, -5.75], [9.5, 1, 1], "hd_hood", tint={"down": 0.3})
    hood.cube([-2.75, 32.5, -3.5], [5.5, 1.5, 6], "hd_hood")
    hood.cube([-1.5, 34, -2], [3, 1, 3.5], "hd_hood")
    # янтарная лампа на макушке
    hood.cube([-1.25, 34.75, -1.25], [2.5, 0.5, 2.5], "hd_dark_plain")
    hood.cube([-0.9, 35.25, -0.9], [1.8, 2.25, 1.8], "hd_glow2", glow="all")
    hood.cube([-1.15, 37.5, -1.15], [2.3, 0.5, 2.3], "hd_brass")
    for x, z in ((-1.15, -1.15), (0.9, -1.15), (-1.15, 0.9), (0.9, 0.9)):
        hood.cube([x, 35.25, z], [0.25, 2.25, 0.25], "hd_dark_plain")

    # --- руки: рукава с кремовыми манжетами, аугметические кисти
    for side, sx in (("right", -1), ("left", 1)):
        arm = m.bone(f"{side}_arm", [5.75 * sx, 22, 0], "body", rotation=[10, 0, 0])
        arm.cube([mx(-7.75, 3.25, sx), 14, -2.25], [3.25, 8, 4.5], "hd_robe_plain")
        arm.cube([mx(-8.25, 4.25, sx), 10.5, -2.75], [4.25, 3.75, 5.5], "hd_robe_plain", tint={"down": 0.2})
        arm.cube([mx(-8.35, 4.45, sx), 10.5, -2.85], [4.45, 1.25, 5.7], "hd_trim")
        arm.cube([mx(-7.5, 2.75, sx), 8.5, -1.5], [2.75, 2.25, 3], "hd_metal")
        for k in range(4):
            arm.cube([mx(-7.5, 0.6, sx), 6.75, -1.5 + k * 0.8], [0.6, 1.75, 0.6], "hd_dark_plain")
        arm.cube([mx(-5, 0.6, sx), 7.5, -1.75], [0.6, 1.5, 0.6], "hd_dark_plain")
        arm.cube([mx(-6.5, 0.5, sx), 8.5, 1.25], [0.5, 2.5, 0.5], "hd_cable")

    # --- Омниссианский топор выше головы, в левой руке
    axe = m.bone("left_item", [6, 8.5, 0], "left_arm")
    axe.cube([5.5, -1, -0.5], [1, 42, 1], "hd_dark_plain")
    for y in (5, 14, 22, 30):
        axe.cube([5.25, y, -0.75], [1.5, 1, 1.5], "hd_brass")
    axe.cube([5.4, 7, -0.6], [1.2, 4, 1.2], "hd_leather")
    axe.cube([5.25, -2, -0.75], [1.5, 1, 1.5], "hd_brass")
    # лезвие — полудиск-шестерня вперёд от древка: ступени по дуге, зубцы по ободу, латунный обод, череп в центре
    cy, cz, R = 36.5, -0.5, 6.5
    for k in range(13):
        y = cy - R + k
        hw = (R * R - (y + 0.5 - cy) ** 2) ** 0.5
        if hw < 0.5:
            continue
        axe.cube([5.5, y, cz - hw], [1, 1, hw], "hd_metal")
    for a in range(-80, 81, 20):
        import math as _m
        y = cy + _m.sin(_m.radians(a)) * (R + 0.4) - 0.5
        z = cz - _m.cos(_m.radians(a)) * (R + 0.4) - 0.4
        axe.cube([5.6, y, z], [0.8, 1, 0.8], "hd_metal_plain")
    axe.cube([5.3, cy - 3, cz - 4], [1.4, 6, 1], "hd_brass")
    axe.cube([5.3, cy - 0.5, cz - 4.5], [1.4, 1, 4.5], "hd_brass")
    axe.cube([5.1, cy - 1.25, cz - 3.5], [1.8, 2.5, 2.25], "hd_bone", deco={"east": skull_side, "west": skull_side})
    axe.cube([5.75, 35.5, 0.5], [0.5, 1.25, 3.5], "hd_metal_plain")
    axe.cube([5.75, 41, -0.25], [0.5, 3, 0.5], "hd_brass")
    axe.cube([5.6, 44, -0.4], [0.8, 0.8, 0.8], "hd_glow2", glow="all")

    # --- серворука над правым плечом: вверх, вперёд, бур вниз перед плечом
    s1 = m.bone("servo_arm", [-3, 21, 4.5], "body", rotation=[5, 0, 40])
    s1.cube([-4.25, 19.75, 3.25], [2.5, 2.5, 2.5], "hd_metal")
    s1.cube([-4, 21, 3.5], [2, 11, 2], "hd_metal")
    s1.cube([-2.6, 22, 5.3], [0.6, 9, 0.6], "hd_metal_plain")
    s1.cube([-4.25, 26, 3.25], [2.5, 1, 2.5], "hd_brass")
    s2 = m.bone("servo_arm_2", [-3, 32, 4.5], "servo_arm", rotation=[80, 0, 0])
    s2.cube([-4.25, 30.75, 3.25], [2.5, 2.5, 2.5], "hd_dark")
    s2.cube([-3.9, 32, 3.6], [1.8, 8, 1.8], "hd_metal")
    s2.cube([-2.4, 33, 4.9], [0.5, 6, 0.5], "hd_cable")
    s3 = m.bone("servo_arm_3", [-3, 40, 4.5], "servo_arm_2", rotation=[120, 0, -80])
    s3.cube([-4.25, 38.75, 3.25], [2.5, 2.5, 2.5], "hd_dark")
    s3.cube([-3.75, 40, 3.75], [1.5, 5, 1.5], "hd_metal")
    s3.cube([-4.1, 43.5, 3.4], [2.2, 1, 2.2], "hd_brass")
    drill = m.bone("servo_drill", [-3, 45, 4.5], "servo_arm_3")
    drill.cube([-4.25, 45, 3.25], [2.5, 2, 2.5], "hd_dark")
    for k, (w, h) in enumerate(((2, 1.5), (1.5, 1.5), (1, 1.5), (0.5, 1.25))):
        y = 47 + k * 1.5
        drill.cube([-3 - w / 2, y, 4.5 - w / 2], [w, h, w], "hd_metal_plain")

    # --- механодендриты слева: у пояса, у груди и через плечо
    tendril(m, "mechadendrite_a", "body", [4, 15, 4.5], [[15, -75, -90]] + [[0, 0, -30]] * 4, [2.75] * 5, claw)
    tendril(m, "mechadendrite_b", "body", [4, 19, 4.5], [[0, 30, -75]] + [[20, 0, 15]] * 4, [2.75] * 5, claw)
    tendril(m, "mechadendrite_c", "body", [3, 22, 4.5], [[0, 30, -90]] + [[10, 0, 30]] * 4, [2.75] * 5, claw)
    return m


def _wave(name, segs, length, amp_x, amp_z, ph, lag, freq=1, steps=24):
    """Волна по цепочке костей: каждое звено отстаёт от предыдущего — дендрит извивается, как живой."""
    out = {}
    for k in range(segs):
        bn = name if k == 0 else f"{name}_{k + 1}"
        out[bn] = {"rotation": track(lambda t, k=k: [amp_x * sin(t * freq % 1, ph + k * lag),
                                                     0, amp_z * sin(t * freq % 1, ph + k * lag + 0.25)], length, steps)}
    return out


def _pulse(t, at, width):
    """Короткий импульс 0→1→0 около момента at (доли цикла) — рывок аугметики."""
    d = min(abs(t - at), 1 - abs(t - at))
    return max(0.0, 1 - d / width)


def animations():
    from gen_entities import humanoid_anims
    anims = humanoid_anims(walk_amp=16, arm_amp=12)

    # --- стоит: дышит, сканирует взглядом, правой рукой что-то подкручивает, сервоплечо осматривается,
    # бур временами прокручивается, дендриты извиваются и щёлкают клешнями, кадило качается
    L = 6.0
    idle = {
        "body": {"rotation": track(lambda t: [1.2 * sin(t * 2 % 1), 1.5 * sin(t), 0], L, 24),
                 "position": track(lambda t: [0, 0.12 * sin(t * 2 % 1), 0], L, 24)},
        "head": {"rotation": track(lambda t: [3 * sin(t * 2 % 1, 0.1) - 6 * _pulse(t, 0.62, 0.03),
                                              18 * sin(t) + 10 * _pulse(t, 0.35, 0.05), 4 * _pulse(t, 0.62, 0.03)], L, 48)},
        "right_arm": {"rotation": track(lambda t: [-14 + 5 * sin(t * 3 % 1), 6 * sin(t), 4 + 2 * sin(t * 6 % 1)], L, 48)},
        "left_arm": {"rotation": track(lambda t: [-2 * sin(t), 0, -2 - 1.5 * sin(t, 0.3)], L, 24)},
        "left_item": {"rotation": track(lambda t: [2 * sin(t, 0.4), 0, 1.5 * sin(t)], L, 24)},
        "robe_right": {"rotation": track(lambda t: [1.5 * sin(t * 2 % 1), 0, 0], L, 24)},
        "robe_left": {"rotation": track(lambda t: [-1.5 * sin(t * 2 % 1, 0.2), 0, 0], L, 24)},
        "censer": {"rotation": track(lambda t: [9 * sin(t * 2 % 1), 0, 4 * sin(t * 2 % 1, 0.25)], L, 24)},
        "mantle": {"rotation": track(lambda t: [0.8 * sin(t * 2 % 1, 0.15), 0, 0], L, 24)},
        "servo_arm": {"rotation": track(lambda t: [4 * sin(t, 0.1), 14 * sin(t), 5 * sin(t, 0.3)], L, 24)},
        "servo_arm_2": {"rotation": track(lambda t: [10 * sin(t, 0.2) - 8 * _pulse(t, 0.5, 0.06), 0, 0], L, 48)},
        "servo_arm_3": {"rotation": track(lambda t: [6 * sin(t * 2 % 1, 0.4), 0, 12 * sin(t, 0.45)], L, 24)},
        "servo_drill": {"rotation": keys([(0, [0, 0, 0]), (2.6, [0, 0, 0]), (3.6, [0, 1080, 0]), (6.0, [0, 1080, 0])])},
        "hood": {"rotation": track(lambda t: [0.6 * sin(t * 2 % 1, 0.3), 0, 0], L, 24)},
    }
    for n, ph in (("mechadendrite_a", 0.0), ("mechadendrite_b", 0.33), ("mechadendrite_c", 0.66)):
        idle.update(_wave(n, 5, L, 7, 9, ph, 0.11, freq=2))
        idle[f"{n}_tip"] = {"rotation": track(lambda t, ph=ph: [0, 40 * sin(t * 3 % 1, ph), 15 * _pulse(t, (0.2 + ph) % 1, 0.04)], L, 48)}

    # --- идёт: шаг в рясе, полы следуют за ногами, топор как посох, кадило и сервоплечо отстают по инерции,
    # дендриты волочатся и хлещут, голова держит горизонт
    W = 1.2
    walk = {
        "right_leg": {"rotation": track(lambda t: [20 * sin(t), 0, 0], W)},
        "left_leg": {"rotation": track(lambda t: [-20 * sin(t), 0, 0], W)},
        "robe_right": {"rotation": track(lambda t: [14 * sin(t, -0.04), 0, 0], W)},
        "robe_left": {"rotation": track(lambda t: [-14 * sin(t, -0.04), 0, 0], W)},
        "body": {"rotation": track(lambda t: [3, 4 * sin(t), 2 * sin(t, 0.25)], W),
                 "position": track(lambda t: [0, 0.45 * abs(sin(t)), 0], W)},
        "head": {"rotation": track(lambda t: [-2, -4 * sin(t), -2 * sin(t, 0.25)], W)},
        "right_arm": {"rotation": track(lambda t: [-16 * sin(t), 0, 4 + 2 * abs(sin(t))], W)},
        "left_arm": {"rotation": track(lambda t: [-8 + 6 * sin(t), 0, -3], W)},
        "left_item": {"rotation": track(lambda t: [-5 * sin(t, 0.1), 0, 2 * sin(t)], W)},
        "censer": {"rotation": track(lambda t: [-22 * sin(t, 0.2), 0, 8 * sin(t, 0.45)], W)},
        "mantle": {"rotation": track(lambda t: [2 * sin(t * 2 % 1, 0.1), 0, 0], W)},
        "servo_arm": {"rotation": track(lambda t: [5 * sin(t * 2 % 1, 0.15), 4 * sin(t, 0.1), 3 * sin(t, 0.35)], W)},
        "servo_arm_2": {"rotation": track(lambda t: [6 * sin(t * 2 % 1, 0.25), 0, 0], W)},
        "servo_arm_3": {"rotation": track(lambda t: [4 * sin(t * 2 % 1, 0.35), 0, 6 * sin(t, 0.4)], W)},
        "hood": {"rotation": track(lambda t: [1.5 * sin(t * 2 % 1, 0.3), 0, 0], W)},
    }
    for n, ph in (("mechadendrite_a", 0.0), ("mechadendrite_b", 0.2), ("mechadendrite_c", 0.4)):
        walk.update(_wave(n, 5, W, 9, 12, ph, 0.08, freq=1, steps=16))
        walk[f"{n}_tip"] = {"rotation": track(lambda t, ph=ph: [0, 25 * sin(t, ph), 0], W)}
    run = {k: v for k, v in walk.items()}
    R = 0.7
    run.update({
        "right_leg": {"rotation": track(lambda t: [32 * sin(t), 0, 0], R)},
        "left_leg": {"rotation": track(lambda t: [-32 * sin(t), 0, 0], R)},
        "robe_right": {"rotation": track(lambda t: [22 * sin(t, -0.04), 0, 0], R)},
        "robe_left": {"rotation": track(lambda t: [-22 * sin(t, -0.04), 0, 0], R)},
        "body": {"rotation": track(lambda t: [10, 5 * sin(t), 0], R), "position": track(lambda t: [0, 0.7 * abs(sin(t)), 0], R)},
        "right_arm": {"rotation": track(lambda t: [-30 * sin(t), 0, 6], R)},
        "censer": {"rotation": track(lambda t: [-35 * sin(t, 0.2), 0, 10 * sin(t, 0.45)], R)},
    })
    for k, v in list(run.items()):  # всё, что не переопределено, — с длиной бега
        if k.startswith("mechadendrite") or k.startswith("servo") or k in ("head", "left_arm", "left_item", "mantle", "hood"):
            run[k] = json_retime(v, W, R)
    anims["misc.idle"] = {"length": L, "loop": True, "bones": idle}
    anims["move.walk"] = {"length": W, "loop": True, "bones": walk}
    anims["move.run"] = {"length": R, "loop": True, "bones": run}
    anims["misc.interact"] = {"length": 2.2, "bones": {  # благословение: топор вверх, бур крутится, дендриты тянутся
        "left_arm": {"rotation": keys([(0, [0, 0, 0]), (0.5, [-35, 0, -15]), (1.4, [-35, 0, -15]), (2.2, [0, 0, 0])])},
        "right_arm": {"rotation": keys([(0, [0, 0, 0]), (0.5, [-70, 0, 20]), (1.4, [-70, 0, 20]), (2.2, [0, 0, 0])])},
        "head": {"rotation": keys([(0, [0, 0, 0]), (0.5, [-12, 0, 0]), (1.5, [10, 0, 0]), (2.2, [0, 0, 0])])},
        "servo_drill": {"rotation": keys([(0, [0, 0, 0]), (1.1, [0, 720, 0]), (2.2, [0, 1440, 0])])},
        "servo_arm_2": {"rotation": keys([(0, [0, 0, 0]), (0.6, [-15, 0, 0]), (1.6, [-15, 0, 0]), (2.2, [0, 0, 0])])},
        "mechadendrite_b": {"rotation": keys([(0, [0, 0, 0]), (0.6, [-20, 0, 25]), (2.2, [0, 0, 0])])},
        "mechadendrite_c": {"rotation": keys([(0, [0, 0, 0]), (0.6, [-25, 0, 15]), (2.2, [0, 0, 0])])},
    }}
    return anims


def json_retime(channels, old, new):
    """Переносит ключи дорожек на другую длину цикла (шаг → бег)."""
    out = {}
    for ch, kf in channels.items():
        if isinstance(kf, dict):
            out[ch] = {f"{float(t) * new / old:.4f}".rstrip("0").rstrip(".") or "0": v for t, v in kf.items()}
        else:
            out[ch] = kf
    return out


def generate():
    m = build()
    print("tech_priest")
    m.build()
    base, glow = m.paint(PAL, seed=zlib.crc32(b"tech_priest"))
    save_png(base, "entity", "tech_priest.png")
    save_png(glow, "entity", "tech_priest_glow.png")
    write_animations("tech_priest", animations())
