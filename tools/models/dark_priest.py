"""
Тёмный техножрец (М2) по концепту автора (DarkMeh.jpg): огромный магос Тёмных Механикус, 2×3 блока.

Человек сросся с механической люлькой: люлька стоит на четырёх ногах-клешнях, как паук; у магоса четыре руки —
свои маленькие и две большие механические (правая — клешня, левая — спаренный ствол со щитком поперёк).

Кошмар и варп: маленький рваный капюшон с тремя глазами и щупальцами-кабелями из маски; массивный ржавый
корпус в потёках крови; в животе вывороченное мутировавшее мясо с вертикальной пастью и варп-свечением;
две рамы-реликварии с черепами, зелёными лампами и шипами; шипастый нимб-кольцо с черепами и пурпурным
варп-ядром; бак с зелёной жижей; левая рука — спаренный ствол со щитом, правая — паучья лапа с когтями,
третья рука-клешня из-за спины; механические ноги коленями вперёд с красными бронеплитами,
золотым крестом и шипами; наросты мяса с варп-глазами на суставах.
"""
import math
import zlib

import numpy as np

import hd
from geo import MATERIALS, Model, keys, mat_glow, mix, save_png, shade, sin, track, write_animations
from priest_hd import _icon, _paste

PAL = dict(
    armor=(74, 62, 60), red=(150, 38, 36), gold=(170, 128, 76), drape=(64, 14, 16), void=(10, 8, 10),
    flesh=(168, 72, 82), vein=(96, 18, 40), metal=(128, 122, 116), dark=(40, 34, 34), hose=(92, 86, 82),
    bone=(196, 180, 144), brass=(150, 112, 60), cable=(30, 26, 26), rust=(92, 44, 28),
    glow=(140, 255, 90), glow2=(200, 70, 255), glow3=(255, 80, 40), tank=(110, 190, 50), screen=(10, 10, 10),
    leather=(60, 40, 32), mask=(52, 46, 46), inner=(30, 24, 26), robe=(64, 14, 16), trim=(170, 128, 76),
)


# ------------------------------------------------------------------ материалы

def _blood(region, rng, n=None):
    """Потёки крови сверху вниз."""
    h, w = region.shape[:2]
    for _ in range(n if n is not None else max(1, w // 7)):
        x = rng.randrange(w)
        ln = rng.randint(h // 4, max(h // 4 + 1, h * 3 // 4))
        y0 = rng.randrange(max(1, h // 3))
        for y in range(y0, min(h, y0 + ln)):
            k = 1 - (y - y0) / max(1, ln)
            region[y, x, :3] = mix(tuple(int(v) for v in region[y, x, :3]), (90, 8, 10), 0.75 * k + 0.2)
            if rng.random() < 0.15 and x + 1 < w:
                region[y, x + 1, :3] = mix(tuple(int(v) for v in region[y, x + 1, :3]), (90, 8, 10), 0.5 * k)


def hd_armor(region, face, pal, rng):
    hd.hd_metal("armor", rust=0.16)(region, face, pal, rng)
    if face not in ("up", "down"):
        _blood(region, rng)


def hd_red_armor(region, face, pal, rng):
    """Крашеная красная броня: сколы до ржавого металла, золотая кайма, кровь."""
    h, w = hd._base(region, pal["red"], face, rng, amp=10, cell=4, grain=6)
    n = hd.vnoise(h, w, 3, rng)
    chips = n > 0.6
    region[chips, :3] = np.array(shade(pal["rust"], 0.9), np.uint8)
    if h > 6 and w > 6:
        g = shade(pal["gold"], 1.0)
        region[:2, :, :3] = g
        region[-2:, :, :3] = shade(pal["gold"], 0.7)
        region[:, :2, :3] = g
        region[:, -2:, :3] = shade(pal["gold"], 0.7)
    if face not in ("up", "down"):
        _blood(region, rng, max(1, w // 10))
    hd.bevel(region, 1.2, 0.6)


def hd_flesh(region, face, pal, rng):
    """Мутировавшее мясо: влажный блеск, тёмные жилы."""
    h, w = hd._base(region, pal["flesh"], face, rng, amp=26, cell=3, grain=8)
    hd._mul(region, np.linspace(1.1, 0.75, h, dtype=np.float32)[:, None, None])
    for _ in range(max(1, w * h // 50)):
        x, y = rng.randrange(w), rng.randrange(h)
        for _ in range(rng.randint(3, 9)):
            if 0 <= x < w and 0 <= y < h:
                region[y, x, :3] = pal["vein"]
            x += rng.choice((-1, 0, 1))
            y += rng.choice((-1, 0, 1))
    for _ in range(max(1, w * h // 160)):  # влажные блики
        x, y = rng.randrange(w), rng.randrange(h)
        region[y, x, :3] = (255, 200, 210)


def hd_drape(region, face, pal, rng):
    """Кроваво-красная ткань: складки, пятна, рваный низ."""
    hd.hd_cloth("drape", dirty=True)(region, face, pal, rng)
    h, w = region.shape[:2]
    _blood(region, rng, max(1, w // 6))
    if face not in ("up", "down") and h > 8:
        x = 0
        while x < w:
            ln, dp = rng.randint(1, 4), rng.randint(2, max(3, h // 5))
            if rng.random() < 0.55:
                region[h - dp:, x:x + ln, 3] = 0
            x += ln + rng.randint(1, 3)


def hd_spike(region, face, pal, rng):
    hd.hd_metal("dark", rivets=False, panels=False)(region, face, pal, rng)
    h = region.shape[0]
    hd._mul(region, np.linspace(0.7, 1.35, h, dtype=np.float32)[::-1][:, None, None])  # к острию светлее


def hd_gold(region, face, pal, rng):
    hd.hd_brass("gold")(region, face, pal, rng)
    if face not in ("up", "down"):
        _blood(region, rng, 1)


MATERIALS.update({
    "hd_armor": hd_armor, "hd_red_armor": hd_red_armor, "hd_flesh": hd_flesh, "hd_drape": hd_drape,
    "hd_spike": hd_spike, "hd_gold": hd_gold,
    "hd_tank": mat_glow("tank"), "hd_warp": mat_glow("glow2"), "hd_glow3": mat_glow("glow3"),
    "hd_hose": hd.hd_cable("hose"), "hd_void": hd.hd_flat("void", 3, edge=False),
})


# ------------------------------------------------------------------ рисунки и свечение

def warp_veins(g, region, face, S, pal):
    """Пурпурные варп-жилы светятся сквозь мясо."""
    import random
    h, w = region.shape[:2]
    rng = random.Random(h * 131 + w)
    for _ in range(max(1, w * h // 90)):
        x, y = rng.randrange(w), rng.randrange(h)
        for _ in range(rng.randint(4, 10)):
            if 0 <= x < w and 0 <= y < h:
                g[y, x, :3] = pal["glow2"]
                g[y, x, 3] = 255
                region[y, x, :3] = mix(pal["glow2"], (255, 255, 255), 0.2)
            x += rng.choice((-1, 0, 1))
            y += rng.choice((-1, 0, 1))


def maw(region, S, pal):
    """Вертикальная пасть в животе: тёмная щель, зубы по краям, варп внутри."""
    h, w = region.shape[:2]

    def draw(d, W, H):
        d.ellipse([W * 0.3, H * 0.05, W * 0.7, H * 0.95], fill=(30, 0, 30, 255))
        d.ellipse([W * 0.42, H * 0.2, W * 0.58, H * 0.8], fill=tuple(pal["glow2"]) + (255,))
        for i in range(7):
            y = H * (0.12 + i * 0.12)
            d.polygon([(W * 0.3, y), (W * 0.45, y + H * 0.04), (W * 0.3, y + H * 0.08)], fill=(240, 230, 200, 255))
            d.polygon([(W * 0.7, y + H * 0.04), (W * 0.55, y + H * 0.08), (W * 0.7, y + H * 0.12)], fill=(240, 230, 200, 255))
    _paste(region, _icon(w, h, draw))


def maw_glow(g, region, face, S, pal):
    warp_veins(g, region, face, S, pal)
    if face != "north":
        return
    m = (region[..., 2] > 200) & (region[..., 0] > 150)
    g[m, :3] = region[m, :3]
    g[m, 3] = 255


def skull_stack(region, S, pal):
    """Рама-реликварий: три черепа один над другим в тёмной нише."""
    h, w = region.shape[:2]

    def draw(d, W, H):
        d.rectangle([W * 0.18, H * 0.08, W * 0.82, H * 0.92], fill=(20, 14, 12, 255))
        for i in range(3):
            cy = H * (0.22 + i * 0.28)
            r = W * 0.26
            d.ellipse([W / 2 - r, cy - r, W / 2 + r, cy + r * 0.8], fill=tuple(pal["bone"]) + (255,))
            for ex in (-1, 1):
                d.ellipse([W / 2 + ex * r * 0.45 - r * 0.25, cy - r * 0.2, W / 2 + ex * r * 0.45 + r * 0.25,
                           cy + r * 0.25], fill=(20, 14, 12, 255))
    _paste(region, _icon(w, h, draw))


def gold_cross(region, S, pal):
    """Золотой крест-клинок на бронеплите, как на наколенниках концепта."""
    h, w = region.shape[:2]

    def draw(d, W, H):
        c = tuple(pal["gold"]) + (255,)
        d.polygon([(W * 0.5, H * 0.08), (W * 0.58, H * 0.3), (W * 0.54, H * 0.92), (W * 0.46, H * 0.92),
                   (W * 0.42, H * 0.3)], fill=c)
        d.polygon([(W * 0.18, H * 0.3), (W * 0.5, H * 0.24), (W * 0.82, H * 0.3), (W * 0.5, H * 0.38)], fill=c)
    _paste(region, _icon(w, h, draw))


def warp_eye(region, S, pal):
    """Глаз в мясе: жёлтое яблоко, щель-зрачок."""
    h, w = region.shape[:2]

    def draw(d, W, H):
        d.ellipse([W * 0.1, H * 0.2, W * 0.9, H * 0.8], fill=(255, 220, 60, 255))
        d.ellipse([W * 0.42, H * 0.22, W * 0.58, H * 0.78], fill=(20, 0, 20, 255))
    _paste(region, _icon(w, h, draw))


def eye_glow(g, region, face, S, pal):
    if face != "north":
        return
    m = region[..., 0] > 220
    g[m, :3] = region[m, :3]
    g[m, 3] = 255


# ------------------------------------------------------------------ сборка

def mx(x, w, sx):
    return x if sx < 0 else -(x + w)


def spike(b, base, rot, length=3.0, thick=1.0, mat="hd_spike"):
    """Шип из трёх сужающихся кубов вдоль +Y от основания, повёрнутый rot вокруг основания."""
    x, y, z = base
    seg = length / 3
    for k in range(3):
        t = thick * (1 - k * 0.3)
        b.cube([x - t / 2, y + k * seg, z - t / 2], [t, seg, t], mat, rotation=rot, pivot=[x, y, z])


def _R(axis, a):
    c, s = math.cos(a), math.sin(a)
    if axis == "x":
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if axis == "y":
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def _rot(r):
    """Поворот кости как у GeckoLib: Z·Y·X, X и Y с обратным знаком."""
    rx, ry, rz = (math.radians(v) for v in r)
    return _R("z", rz) @ _R("y", -ry) @ _R("x", -rx)


def _aim(v):
    """Углы [rx, 0, rz], которые разворачивают ось +Y кости по направлению v."""
    v = np.asarray(v, float) / np.linalg.norm(v)
    rx = -math.degrees(math.asin(max(-1.0, min(1.0, v[2]))))
    rz = math.degrees(math.atan2(-v[0], v[1]))
    return [round(rx, 2), 0, round(rz, 2)]


def limb(m, name, parent, points, segment, joint=None):
    """
    Конечность по точкам суставов (в пикселях модели): кость на каждое звено, звено вдоль +Y.
    segment(bone, x, y, z, length, k) рисует звено k; joint(bone, x, y, z, k) — шарнир в его начале.
    Возвращает имя последней кости и точку конца — к ней крепится кисть, клешня или ступня.
    """
    world = np.eye(3)
    bone_parent = parent
    for k in range(len(points) - 1):
        a, b = np.array(points[k], float), np.array(points[k + 1], float)
        local = world.T @ (b - a)
        r = _aim(local)
        world = world @ _rot(r)
        bn = name if k == 0 else f"{name}_{k + 1}"
        bone = m.bone(bn, [round(v, 3) for v in a], bone_parent, rotation=r)
        length = float(np.linalg.norm(b - a))
        x, y, z = a
        if joint:
            joint(bone, x, y, z, k)
        segment(bone, x, y, z, length, k)
        bone_parent = bn
    return bone_parent, points[-1], world


def build():
    m = Model("dark_tech_priest", S=4, atlas_w=256)
    m.bone("root", [0, 0, 0])
    body = m.bone("body", [0, 18, 0], "root")

    # --- люлька: чаша-корпус, золотой обод, ткань спереди, реликварии на передних углах
    body.cube([-7.5, 12, -6.5], [15, 10.5, 13], "hd_armor")
    body.cube([-8, 22, -7], [16, 1, 14], "hd_gold")
    body.cube([-6.5, 9.5, -5.5], [13, 2.5, 11], "hd_dark")
    body.cube([-5.5, 2.5, -7.25], [11, 13, 0.75], "hd_drape")
    for sx in (-1, 1):
        body.cube([mx(-7.75, 0.75, sx), 5, -5], [0.75, 9, 7], "hd_drape")
        x0 = mx(-9.5, 4, sx)
        body.cube([x0, 11.5, -7.75], [4, 11, 1.5], "hd_gold", deco={"north": skull_stack})
        body.cube([x0 + 0.75, 22.5, -7.6], [2.5, 2.5, 1.5], "hd_glow", glow="all")
        body.cube([x0 + 0.5, 25, -7.8], [3, 0.6, 2], "hd_gold")
        ex = x0 if sx < 0 else x0 + 4
        for k in range(4):
            spike(body, [ex, 12.5 + k * 2.75, -7], [0, 0, 90 * sx], 2.25, 0.7)
        # опухоли с варп-глазами на боках люльки
        body.cube([mx(-8.5, 1.75, sx), 14, 0], [1.75, 3, 3.5], "hd_flesh", glow=warp_veins)
        body.cube([mx(-8.6, 0.25, sx), 15, 0.75], [0.25, 1.25, 1.25], "hd_flesh",
                  deco={"east" if sx < 0 else "west": warp_eye}, glow=eye_glow)
    # --- человек, вросший в люльку: мясо на стыке, торс, пасть в животе, наплечники
    body.cube([-5, 21.5, -5.25], [10, 1.75, 8.5], "hd_flesh", glow=warp_veins)
    body.cube([-5, 22.5, -4.75], [10, 9.5, 7], "hd_armor")
    gut = m.bone("gut", [0, 25, -5], "body")
    gut.cube([-3.25, 22.75, -5.75], [6.5, 5.5, 1.5], "hd_flesh", deco={"north": maw}, glow=maw_glow)
    body.cube([-5.25, 30.5, -5], [10.5, 1.5, 7.5], "hd_gold")
    body.cube([-9.5, 28, -4.5], [5, 5, 8], "hd_red_armor")
    body.cube([4.5, 28, -4.5], [5, 5, 8], "hd_armor")
    body.cube([4.25, 28, -4.75], [5.5, 0.75, 8.5], "hd_gold")
    for sx, x in ((-1, -7), (1, 7)):
        for k in range(3):
            spike(body, [x, 33, -3 + k * 3], [0, 0, 20 * -sx], 3.5, 1)
    # опухоль с глазами на левом плече
    tumor = m.bone("tumor", [7, 32, 0], "body")
    tumor.cube([5, 31.5, -2.5], [4, 3, 4.5], "hd_flesh", glow=warp_veins)
    tumor.cube([5.75, 34.5, -1.75], [2.5, 2, 3], "hd_flesh", glow=warp_veins)
    for (x, y) in ((5.5, 32.5), (7.25, 33.25)):
        tumor.cube([x, y, -2.75], [1.25, 1.25, 0.25], "hd_flesh", deco={"north": warp_eye}, glow=eye_glow)
    # бак с зелёной жижей за левым плечом, шланги в люльку
    body.cube([3, 25, 3.5], [4.5, 13, 4.5], "hd_tank", glow="all")
    body.cube([2.5, 38, 3], [5.5, 1.5, 5.5], "hd_gold")
    body.cube([2.5, 23.5, 3], [5.5, 1.5, 5.5], "hd_gold")
    body.cube([0, 22.5, 5.5], [0.8, 11, 0.8], "hd_hose")
    body.cube([-2.5, 22.5, 5], [0.8, 8, 0.8], "hd_hose")

    # --- нимб за спиной: кольцо, шипы, черепа, варп-ядро
    halo = m.bone("halo", [0, 36, 7.5], "body")
    R, cy0 = 9, 36
    for i in range(10):
        a = math.radians(i * 36)
        cx, cy = math.sin(a) * R, cy0 + math.cos(a) * R
        halo.cube([cx - 3, cy - 1, 6.75], [6, 2, 1.5], "hd_armor", rotation=[0, 0, -i * 36], pivot=[cx, cy, 7.5])
    for i in range(12):
        a = i * 30
        r = math.radians(a)
        spike(halo, [math.sin(r) * (R + 0.8), cy0 + math.cos(r) * (R + 0.8), 7.5], [0, 0, -a], 4.5 if i % 2 else 3, 1.1)
    for i in (1, 4, 6, 9):
        a = math.radians(i * 36)
        halo.cube([math.sin(a) * R - 1.1, cy0 + math.cos(a) * R - 1.1, 5.75], [2.2, 2.2, 1.5], "hd_bone")
    halo.cube([-2.25, cy0 - 2.25, 6.5], [4.5, 4.5, 1.5], "hd_warp", glow="all")

    # --- голова: маленькая, рваный капюшон, три глаза, щупальца-кабели на грудь
    head = m.bone("head", [0, 32, -2], "body")
    head.cube([-2.5, 31.75, -6], [5, 5, 4.5], "hd_mask")
    head.cube([-2, 34.25, -6.3], [1.25, 1.25, 0.3], "hd_glow3", glow="all")
    head.cube([0.75, 34.5, -6.3], [1.25, 1.25, 0.3], "hd_glow3", glow="all")
    head.cube([-0.5, 35.5, -6.3], [1, 1, 0.3], "hd_glow3", glow="all")
    hood = m.bone("hood", [0, 32, -2], "head")
    hood.cube([-3.5, 36.75, -6.75], [7, 1.25, 7], "hd_drape", tint={"down": 0.2})
    hood.cube([-3.5, 31.5, -6.75], [1, 5.25, 7], "hd_drape", tint={"west": 0.25})
    hood.cube([2.5, 31.5, -6.75], [1, 5.25, 7], "hd_drape", tint={"east": 0.25})
    hood.cube([-3.5, 31.5, -0.75], [7, 5.25, 1], "hd_drape")
    hood.cube([-1.5, 38, -4], [3, 1, 3.5], "hd_drape")
    for i, x in enumerate((-1.8, -0.6, 0.6, 1.8)):
        name, parent, y = f"tentacle_{i + 1}", "head", 32
        for k in range(4):
            bn = name if k == 0 else f"{name}_{k + 1}"
            rot = [-15 + i * 6, 0, x * 6] if k == 0 else [12 * (1 if i % 2 else -1), 0, 8 * (1 if x > 0 else -1)]
            b = m.bone(bn, [x, y, -6], parent, rotation=rot)
            b.cube([x - 0.3, y - 1.75, -6.3], [0.6, 1.75, 0.6], "hd_hose")
            parent, y = bn, y - 1.75

    # --- свои руки: маленькие, человеческие, согнуты к груди
    for side, sx in (("right", -1), ("left", 1)):
        arm = m.bone(f"{side}_arm", [4.75 * sx, 29.5, -1], "body")
        arm.cube([mx(-6.25, 1.75, sx), 25, -2], [1.75, 4.5, 1.75], "hd_armor")
        fore = m.bone(f"{side}_fore", [5.4 * sx, 25.25, -1.1], f"{side}_arm", rotation=[-65, 0, -15 * sx])
        fore.cube([mx(-6.1, 1.4, sx), 20.5, -1.8], [1.4, 4.75, 1.4], "hd_rusty")
        for k in range(3):
            fore.cube([mx(-6.2 + k * 0.6, 0.35, sx), 18, -1.6], [0.35, 2.5, 0.35], "hd_spike",
                      rotation=[15, 0, (k - 1) * 12], pivot=[5.4 * sx, 20.5, -1.1])

    # --- четыре ноги-клешни, как у паука; на коленях красные плиты с шипами
    def leg_segment(b, x, y, z, ln, k):
        if k == 0:
            b.cube([x - 1.25, y, z - 1.25], [2.5, ln, 2.5], "hd_rusty")
            b.cube([x + 0.9, y + 2, z - 0.4], [0.6, ln - 4, 0.6], "hd_metal_plain")
        else:
            b.cube([x - 1, y, z - 1], [2, ln - 4, 2], "hd_rusty")
            b.cube([x - 2, y + 1, z - 2], [4, 7, 4], "hd_red_armor")
            for s in range(3):
                spike(b, [x, y + 2 + s * 2, z - 2], [-90, 0, 0], 2.5, 0.8)
            b.cube([x - 0.5, y + 3, z + 2], [1, 1, 1], "hd_gold")
            for s in range(3):  # острие клешни: сужается к земле
                t = 1.8 - s * 0.55
                b.cube([x - t / 2, y + ln - 4 + s * 1.4, z - t / 2], [t, 1.4, t], "hd_spike")

    def leg_joint(b, x, y, z, k):
        b.cube([x - 1.75, y - 1.75, z - 1.75], [3.5, 3.5, 3.5], "hd_dark" if k == 0 else "hd_armor")

    for name, sx, sz in (("leg_front_right", -1, -1), ("leg_back_right", -1, 1),
                         ("leg_front_left", 1, -1), ("leg_back_left", 1, 1)):
        hip = (6.5 * sx, 13, 4.5 * sz)
        knee = (12.5 * sx, 21, 9.5 * sz)
        foot = (15 * sx, 0, 13 * sz)
        limb(m, name, "body", [hip, knee, foot], leg_segment, leg_joint)

    # --- большая левая рука: спаренный ствол, поперёк — красный щиток
    ga = m.bone("gun_arm", [7.5, 22, 1], "body")
    ga.cube([6.5, 19.5, -1.5], [4.5, 5, 5], "hd_dark")
    ga.cube([7, 18.75, -2], [3.5, 6.5, 6], "hd_gold")
    ga.cube([10, 20, -1], [4, 4, 4], "hd_rusty")
    ga.cube([13.5, 21, 0], [0.8, 0.8, 4], "hd_hose")
    gun = m.bone("left_item", [14, 20, 0], "gun_arm")
    gun.cube([11.5, 16, -9], [6, 7, 11], "hd_armor")
    gun.cube([11.75, 23, -7], [5.5, 1, 7], "hd_gold")
    for x in (12, 15):
        gun.cube([x, 18.5, -27], [2.5, 2.5, 18], "hd_dark")
        gun.cube([x - 0.25, 18.25, -27.5], [3, 3, 1.25], "hd_rusty")
        gun.cube([x - 0.25, 18.25, -21], [3, 3, 0.75], "hd_gold")
        gun.cube([x - 0.25, 18.25, -15], [3, 3, 0.75], "hd_gold")
    gun.cube([12.5, 13, -5], [4, 3, 4.5], "hd_rusty")
    # щиток поперёк ствола: стволы проходят над его верхним краем
    gun.cube([10, 6, -12.5], [9.5, 12.5, 1.25], "hd_red_armor", deco={"north": gold_cross})
    for (x, y) in ((11.5, 8), (17.5, 8), (11.5, 15), (17.5, 15), (14.5, 11.5)):
        spike(gun, [x, y, -12.5], [-90, 0, 0], 2.5, 0.8)

    # --- большая правая рука: вверх и в сторону, локоть, огромная клешня вперёд-вниз
    def arm_segment(b, x, y, z, ln, k):
        b.cube([x - 1.25, y, z - 1.25], [2.5, ln, 2.5], "hd_rusty")
        b.cube([x + 1, y + 1, z - 0.3], [0.6, ln - 2, 0.6], "hd_metal_plain")
        if k == 1:
            b.cube([x - 1.75, y + ln - 4, z - 1.75], [3.5, 3, 3.5], "hd_red_armor")

    def arm_joint(b, x, y, z, k):
        b.cube([x - 2, y - 2, z - 2], [4, 4, 4], "hd_dark" if k else "hd_gold")

    last, wrist, world = limb(m, "claw_arm", "body",
                              [(-7.5, 24, 2), (-14, 32, 3), (-16.5, 26, -6), (-15.5, 25, -13)], arm_segment, arm_joint)
    wx, wy, wz = wrist
    claw = m.bone("right_item", [wx, wy, wz], last)
    claw.cube([wx - 2, wy - 1, wz - 2], [4, 3, 4], "hd_armor")
    claw.cube([wx - 2.5, wy + 0.5, wz - 2.5], [5, 2, 5], "hd_red_armor")
    for side, rz, sgn in (("claw_upper", 28, 1), ("claw_lower", -28, -1)):
        jaw = m.bone(side, [wx, wy + 2, wz], "right_item", rotation=[0, 0, rz])
        jaw.cube([wx - 1.25, wy + 2, wz - 1.75], [2.5, 6.5, 3.5], "hd_rusty")
        jaw.cube([wx - 1, wy + 8.5, wz - 1.5], [2, 3.5, 3], "hd_spike")
        jaw.cube([wx - 0.5, wy + 12, wz - 1], [1, 2, 2], "hd_spike")
        for k in range(4):  # зубцы по внутренней кромке челюсти
            jaw.cube([wx - sgn * 1.25 - (0.75 if sgn > 0 else 0), wy + 3 + k * 2.2, wz - 0.5], [0.75, 0.9, 1],
                     "hd_spike")
    return m


def _pulse(t, at, width):
    """Импульс 0→1→0 около доли цикла at — рывок, удар сердца, щелчок клешни."""
    d = min(abs(t - at), 1 - abs(t - at))
    return max(0.0, 1 - d / width)


def _heart(t):
    """Двойной удар больного сердца: тук-тук… пауза."""
    return _pulse(t, 0.1, 0.05) + 0.7 * _pulse(t, 0.22, 0.05)


LEGS = (("leg_front_right", -1, 0.0), ("leg_back_left", 1, 0.0), ("leg_front_left", 1, 0.5), ("leg_back_right", -1, 0.5))


def _tentacles(length, ax, az, freq, steps):
    out = {}
    for i in range(4):
        for k in range(4):
            bn = f"tentacle_{i + 1}" if k == 0 else f"tentacle_{i + 1}_{k + 1}"
            out[bn] = {"rotation": track(lambda t, i=i, k=k: [ax * sin(t * freq % 1, i * 0.23 + k * 0.12), 0,
                                                              az * sin(t, i * 0.31 + k * 0.15)], length, steps)}
    return out


def animations():
    # --- стоит: люлька тяжело дышит, больное сердце в пасти бьётся двойными ударами, ноги-клешни
    # переступают по одной, большая клешня щёлкает, ствол водит по сторонам, голова дёргается
    L = 6.0
    idle = {
        "body": {"position": track(lambda t: [0, 0.6 * sin(t * 2 % 1) - 0.25 * _heart(t * 2 % 1), 0], L, 48),
                 "rotation": track(lambda t: [1.2 * sin(t * 2 % 1, 0.2), 2.5 * sin(t), 1.2 * sin(t, 0.3)], L, 24)},
        "gut": {"scale": track(lambda t: [1 + 0.12 * _heart(t * 3 % 1), 1 + 0.08 * _heart(t * 3 % 1),
                                          1 + 0.18 * _heart(t * 3 % 1)], L, 72)},
        "tumor": {"scale": track(lambda t: [1 + 0.1 * _heart((t * 3 + 0.4) % 1)] * 3, L, 72)},
        "halo": {"rotation": track(lambda t: [0, 0, 360 * t], L, 24)},
        "head": {"rotation": track(lambda t: [4 * sin(t * 2 % 1) - 14 * _pulse(t, 0.31, 0.02) + 9 * _pulse(t, 0.77, 0.02),
                                              14 * sin(t, 0.1) + 22 * _pulse(t, 0.55, 0.03),
                                              10 * _pulse(t, 0.31, 0.02) - 12 * _pulse(t, 0.86, 0.02)], L, 96)},
        "right_arm": {"rotation": track(lambda t: [-6 * sin(t * 2 % 1), 0, -4 * sin(t, 0.2) - 10 * _pulse(t, 0.45, 0.03)], L, 72)},
        "left_arm": {"rotation": track(lambda t: [-6 * sin(t * 2 % 1, 0.4), 0, 4 * sin(t, 0.6) + 10 * _pulse(t, 0.12, 0.03)], L, 72)},
        "right_fore": {"rotation": track(lambda t: [10 * sin(t * 3 % 1), 0, 12 * _pulse(t, 0.45, 0.03)], L, 72)},
        "left_fore": {"rotation": track(lambda t: [10 * sin(t * 3 % 1, 0.5), 0, -12 * _pulse(t, 0.12, 0.03)], L, 72)},
        "gun_arm": {"rotation": track(lambda t: [3 * sin(t * 2 % 1, 0.3), 12 * sin(t, 0.15), 0], L, 24)},
        "left_item": {"rotation": track(lambda t: [2 * sin(t, 0.4) - 4 * _pulse(t, 0.7, 0.04), 0, 0], L, 48)},
        "claw_arm": {"rotation": track(lambda t: [4 * sin(t, 0.6), 6 * sin(t, 0.2), 3 * sin(t * 2 % 1)], L, 24)},
        "claw_arm_2": {"rotation": track(lambda t: [6 * sin(t * 2 % 1, 0.25), 0, 0], L, 24)},
        "claw_arm_3": {"rotation": track(lambda t: [5 * sin(t, 0.5), 0, 8 * _pulse(t, 0.4, 0.05)], L, 48)},
        # клешня приоткрывается и дважды резко щёлкает
        "claw_upper": {"rotation": track(lambda t: [0, 0, 10 + 8 * sin(t * 2 % 1)
                                                    - 20 * (_pulse(t, 0.4, 0.015) + _pulse(t, 0.44, 0.015))], L, 120)},
        "claw_lower": {"rotation": track(lambda t: [0, 0, -10 - 8 * sin(t * 2 % 1)
                                                    + 20 * (_pulse(t, 0.4, 0.015) + _pulse(t, 0.44, 0.015))], L, 120)},
        **_tentacles(L, 10, 13, 2, 24),
    }
    for i, (name, sx, ph) in enumerate(LEGS):
        at = (0.15 + i * 0.22) % 1  # ноги переступают по очереди
        idle[name] = {"rotation": track(lambda t, at=at, sx=sx: [0, 6 * _pulse(t, at, 0.05) * sx,
                                                                 -sx * 14 * _pulse(t, at, 0.05)], L, 96)}
        idle[f"{name}_2"] = {"rotation": track(lambda t, at=at: [-10 * _pulse(t, at, 0.05), 0, 0], L, 96)}

    def walk(length, amp, lift, bob):
        # паучья походка: диагональные пары, нога поднимается в переносе и опускается с упором
        bones = {}
        for name, sx, ph in LEGS:
            bones[name] = {"rotation": track(lambda t, ph=ph, sx=sx: [0, amp * sin(t, ph),
                                                                      -sx * lift * max(0, sin(t, ph + 0.25))], length)}
            bones[f"{name}_2"] = {"rotation": track(lambda t, ph=ph: [-lift * 0.8 * max(0, sin(t, ph + 0.25)), 0, 0], length)}
        bones.update({
            "body": {"position": track(lambda t: [0, bob * abs(sin(t * 2 % 1, 0.1)), 0], length),
                     "rotation": track(lambda t: [2 + 2 * sin(t * 2 % 1), 4 * sin(t), 3 * sin(t, 0.25)], length)},
            "head": {"rotation": track(lambda t: [-2 * sin(t * 2 % 1), -5 * sin(t), -3 * sin(t, 0.25)], length)},
            "gut": {"scale": track(lambda t: [1 + 0.06 * sin(t * 2 % 1, 0.3), 1 - 0.05 * sin(t * 2 % 1, 0.3),
                                              1 + 0.1 * sin(t * 2 % 1, 0.35)], length)},
            "tumor": {"position": track(lambda t: [0, -0.4 * sin(t * 2 % 1, 0.2), 0], length)},
            "halo": {"rotation": track(lambda t: [4 * sin(t * 4 % 1, 0.2), 0, 360 * t], length * 4)},
            "claw_arm": {"rotation": track(lambda t: [8 * sin(t, 0.5), 6 * sin(t), 0], length)},
            "claw_arm_2": {"rotation": track(lambda t: [6 * sin(t * 2 % 1, 0.3), 0, 0], length)},
            "claw_upper": {"rotation": track(lambda t: [0, 0, 12 + 10 * sin(t)], length)},
            "claw_lower": {"rotation": track(lambda t: [0, 0, -12 - 10 * sin(t)], length)},
            "gun_arm": {"rotation": track(lambda t: [-3 * sin(t * 2 % 1, 0.2), -3 * sin(t), 0], length)},
            "right_arm": {"rotation": track(lambda t: [-10 * sin(t), 0, -6 * abs(sin(t))], length)},
            "left_arm": {"rotation": track(lambda t: [10 * sin(t), 0, 6 * abs(sin(t))], length)},
            "right_fore": {"rotation": track(lambda t: [12 * sin(t, 0.2), 0, 0], length)},
            "left_fore": {"rotation": track(lambda t: [-12 * sin(t, 0.2), 0, 0], length)},
        })
        bones.update(_tentacles(length, 14, 10, 2, 16))  # щупальца мотаются от шагов
        return bones

    return {
        "misc.idle": {"length": L, "loop": True, "bones": idle},
        "move.walk": {"length": 1.4, "loop": True, "bones": walk(1.4, 18, 16, 0.9)},
        "move.run": {"length": 0.9, "loop": True, "bones": walk(0.9, 26, 22, 1.3)},
        "attack.swing": {"length": 0.9, "bones": {  # удар большой клешнёй
            "claw_arm": {"rotation": keys([(0, [0, 0, 0]), (0.35, [-30, 0, -20]), (0.5, [25, 0, 15]), (0.9, [0, 0, 0])])},
            "claw_upper": {"rotation": keys([(0, [0, 0, 0]), (0.35, [0, 0, 30]), (0.5, [0, 0, -5]), (0.9, [0, 0, 0])])},
            "claw_lower": {"rotation": keys([(0, [0, 0, 0]), (0.35, [0, 0, -30]), (0.5, [0, 0, 5]), (0.9, [0, 0, 0])])},
        }},
        "attack.shoot": {"length": 0.6, "bones": {
            "left_item": {"position": keys([(0, [0, 0, 0]), (0.05, [0, 0.5, 2.5]), (0.25, [0, 0, 0.5]), (0.6, [0, 0, 0])])},
        }},
        "misc.interact": {"length": 2.4, "bones": {  # варп-вспышка: свои руки в стороны, нимб раскручивается
            "right_arm": {"rotation": keys([(0, [0, 0, 0]), (0.6, [-40, 0, -40]), (1.8, [-40, 0, -40]), (2.4, [0, 0, 0])])},
            "left_arm": {"rotation": keys([(0, [0, 0, 0]), (0.6, [-40, 0, 40]), (1.8, [-40, 0, 40]), (2.4, [0, 0, 0])])},
            "head": {"rotation": keys([(0, [0, 0, 0]), (0.6, [-25, 0, 0]), (1.8, [-25, 0, 0]), (2.4, [0, 0, 0])])},
            "halo": {"rotation": keys([(0, [0, 0, 0]), (2.4, [0, 0, 1080])])},
            "gut": {"scale": keys([(0, [1, 1, 1]), (0.8, [1.25, 1.2, 1.4]), (1.8, [1.25, 1.2, 1.4]), (2.4, [1, 1, 1])])},
        }},
    }


def generate():
    m = build()
    print("dark_tech_priest")
    m.build()
    base, glow = m.paint(PAL, seed=zlib.crc32(b"dark_tech_priest"))
    save_png(base, "entity", "dark_tech_priest.png")
    save_png(glow, "entity", "dark_tech_priest_glow.png")
    write_animations("dark_tech_priest", animations())
