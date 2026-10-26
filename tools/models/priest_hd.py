"""
Техножрец Механикус (М1) и тёмный техножрец (М2) — детальная модель-заглушка, 64 px на блок.

Образ — энжинсир: тяжёлая красная ряса с пелериной, маска с бионическим глазом и россыпью линз,
глубокий капюшон, ранец с плазменным ядром и трубами, серворука над левым плечом, два механодендрита
с инструментами справа, Омниссианский ключ-топор (шестерня с черепом), кадило, печати чистоты.
Тёмный — та же геометрия: чёрная ряса, потускневшая латунь, красные линзы, звезда Хаоса вместо шестерни.
"""
import math

import numpy as np

import hd  # noqa: F401 — регистрирует hd_-материалы
from geo import Model, cog, draw_rect, keys, mix, save_png, shade, sin, star8, track, write_animations

TECH_PRIEST = dict(
    robe=(150, 28, 24), robe_in=(60, 12, 10), trim=(200, 160, 62), tabard=(38, 34, 36),
    mask=(58, 60, 66), inner=(30, 30, 33), metal=(156, 160, 166), dark=(58, 60, 66), brass=(198, 158, 64),
    leather=(84, 56, 34), cable=(32, 32, 36), glow=(110, 255, 140), glow2=(255, 160, 60),
    parchment=(226, 208, 162), wax=(160, 22, 20), bone=(216, 206, 178), screen=(10, 26, 14),
)
DARK_TECH_PRIEST = dict(
    TECH_PRIEST, robe=(34, 30, 34), robe_in=(14, 10, 12), trim=(116, 78, 46), tabard=(104, 18, 22),
    mask=(62, 56, 58), inner=(22, 18, 24), metal=(118, 110, 104), dark=(46, 40, 44), brass=(132, 100, 62),
    leather=(54, 38, 34), glow=(255, 40, 40), glow2=(255, 90, 40), wax=(60, 10, 14), bone=(190, 180, 150),
    screen=(30, 6, 10), chaos=True,
)


# ------------------------------------------------------------------ рисунки

def _icon(w, h, draw):
    """Рисует значок крупно (×6) и уменьшает — края ровные даже в 12 пикселях."""
    from PIL import Image, ImageDraw
    k = 6
    img = Image.new("RGBA", (w * k, h * k), (0, 0, 0, 0))
    draw(ImageDraw.Draw(img), w * k, h * k)
    return np.asarray(img.resize((w, h), Image.LANCZOS))


def _paste(region, icon, threshold=100):
    m = icon[..., 3] > threshold
    region[m, :3] = icon[m, :3]


def emblem(scale=0.42):
    """Знак Механикус: шестерня, в ней череп. У тёмного — восьмиконечная звезда Хаоса."""
    def f(region, S, pal):
        h, w = region.shape[:2]
        light = region[..., :3].mean() > 110  # на латуни рисуем тёмным, на ткани — латунью
        c = tuple(shade(pal["brass"], 0.42 if light else 1.0)) + (255,)
        dk = tuple(shade(pal["brass"], 0.25 if light else 0.5)) + (255,)
        bone = tuple(pal["bone"]) + (255,)
        hole = (18, 14, 12, 255)

        def draw(d, W, H):
            cx, cy, R = W / 2, H / 2, min(W, H) * scale
            if pal.get("chaos"):
                for i in range(8):
                    a = i * math.pi / 4
                    tip = (cx + math.cos(a) * R, cy + math.sin(a) * R)
                    side = R * 0.16
                    p1 = (cx + math.cos(a + math.pi / 2) * side, cy + math.sin(a + math.pi / 2) * side)
                    p2 = (cx - math.cos(a + math.pi / 2) * side, cy - math.sin(a + math.pi / 2) * side)
                    d.polygon([p1, tip, p2], fill=c)
                    head = [(tip[0] - math.cos(a - 0.5) * R * 0.3, tip[1] - math.sin(a - 0.5) * R * 0.3), tip,
                            (tip[0] - math.cos(a + 0.5) * R * 0.3, tip[1] - math.sin(a + 0.5) * R * 0.3)]
                    d.polygon(head, fill=c)
                d.ellipse([cx - R * 0.28, cy - R * 0.28, cx + R * 0.28, cy + R * 0.28], fill=c)
                d.ellipse([cx - R * 0.14, cy - R * 0.14, cx + R * 0.14, cy + R * 0.14], fill=dk)
                return
            # шестерня: 12 зубцов и обод
            for i in range(12):
                a = i * math.pi / 6
                pts = []
                for da, rr in ((-0.13, R * 0.78), (-0.09, R), (0.09, R), (0.13, R * 0.78)):
                    pts.append((cx + math.cos(a + da) * rr, cy + math.sin(a + da) * rr))
                d.polygon(pts, fill=c)
            d.ellipse([cx - R * 0.82, cy - R * 0.82, cx + R * 0.82, cy + R * 0.82], fill=c)
            d.ellipse([cx - R * 0.6, cy - R * 0.6, cx + R * 0.6, cy + R * 0.6], fill=dk)
            # череп: свод, скулы, челюсть с зубами
            sr = R * 0.5
            d.ellipse([cx - sr * 0.85, cy - sr * 0.95, cx + sr * 0.85, cy + sr * 0.55], fill=bone)
            d.rectangle([cx - sr * 0.5, cy + sr * 0.3, cx + sr * 0.5, cy + sr * 0.8], fill=bone)
            for ex in (-1, 1):
                d.ellipse([cx + ex * sr * 0.42 - sr * 0.24, cy - sr * 0.3, cx + ex * sr * 0.42 + sr * 0.24,
                           cy + sr * 0.15], fill=hole)
            d.polygon([(cx, cy + sr * 0.12), (cx - sr * 0.12, cy + sr * 0.35), (cx + sr * 0.12, cy + sr * 0.35)], fill=hole)
            for tx in range(-2, 3):
                d.line([(cx + tx * sr * 0.2, cy + sr * 0.5), (cx + tx * sr * 0.2, cy + sr * 0.8)], fill=hole,
                       width=max(1, int(W / 60)))

        _paste(region, _icon(w, h, draw))
    return f


def tabard_emblem(region, S, pal):
    h, w = region.shape[:2]
    top = region[int(h * 0.06):int(h * 0.06) + w]
    emblem(0.44)(top, S, pal)


def mask_face(region, S, pal):
    """Пластины маски: швы, заклёпки, вентиляционные прорези на щеках."""
    h, w = region.shape[:2]
    c = shade(pal["mask"], 0.55)
    region[int(h * 0.42), 1:-1, :3] = c
    region[1:-1, w // 2, :3] = c
    for y in range(int(h * 0.55), h - 2, 2):
        region[y, 2:5, :3] = shade(pal["mask"], 0.4)
        region[y, w - 5:w - 2, :3] = shade(pal["mask"], 0.4)


def grille(region, S, pal):
    h, w = region.shape[:2]
    for x in range(1, w - 1, 2):
        region[1:-1, x, :3] = (14, 14, 16)


def chest_ribs(region, S, pal):
    h, w = region.shape[:2]
    for y in range(2, h - 1, 3):
        region[y, 1:-1, :3] = shade(pal["metal"], 0.55)
        region[y - 1, 1:-1, :3] = shade(pal["metal"], 1.25)


def slate_screen(region, S, pal):
    h, w = region.shape[:2]
    region[2:-2, 1:-1, :3] = pal["screen"]
    for y in range(3, h - 3, 2):
        ln = 1 + (y * 7) % max(2, w - 3)
        region[y, 1:1 + ln, :3] = mix(pal["screen"], pal["glow"], 0.8)


def skull_side(region, S, pal):
    """Череп на втулке топора: глазницы и зубы."""
    h, w = region.shape[:2]
    draw_rect(region, 1, w * 0.18, h * 0.3, w * 0.25, h * 0.22, (24, 20, 18))
    draw_rect(region, 1, w * 0.57, h * 0.3, w * 0.25, h * 0.22, (24, 20, 18))
    for x in range(1, w - 1, 2):
        region[int(h * 0.75):, x, :3] = (40, 34, 30)


def cog_blade(region, S, pal):
    """Лезвие-шестерня: тёмная прорезь-обод и заточенная кромка спереди."""
    h, w = region.shape[:2]
    cog(region, w * 0.62, h / 2, min(w, h) * 0.38, shade(pal["metal"], 0.6))
    region[:, :2, :3] = shade(pal["metal"], 1.45)  # кромка


def _glow_screen(g, region, face):
    """Светится только текст экрана инфопланшета."""
    if face != "east":
        return
    bright = region[..., 1] > 90
    g[bright, :3] = region[bright, :3]
    g[bright, 3] = 255


def core_window(region, S, pal):
    h, w = region.shape[:2]
    for x in range(0, w, max(2, w // 4)):
        region[:, x, :3] = shade(pal["dark"], 0.6)


# ------------------------------------------------------------------ модель

def X(x, w):
    """Зеркало куба на левую сторону: x → −(x + w)."""
    return -(x + w)


def build():
    m = Model("tech_priest", S=4, atlas_w=128)
    m.bone("root", [0, 0, 0])

    # --- ноги: аугметика под рясой, видны ступни с когтями
    for side, sx in (("right", -1), ("left", 1)):
        leg = m.bone(f"{side}_leg", [2 * sx, 12, 0], "root")
        def L(x, w):
            return x if sx < 0 else X(x, w)
        leg.cube([L(-3.5, 3), 2, -1.5], [3, 10, 3], "hd_inner")
        leg.cube([L(-4, 4), 0, -2.5], [4, 2.5, 4.5], "hd_dark")
        leg.cube([L(-3.75, 3.5), 2.5, -2.25], [3.5, 4, 0.75], "hd_metal_plain")
        for k in range(2):
            leg.cube([L(-3.75 + k * 2, 1.25), 0, -3.5], [1.25, 0.75, 1.25], "hd_dark_plain")

    body = m.bone("body", [0, 12, 0], "root")
    # подол: две полы, идут за ногами вполсилы (анимация), спереди табард, сзади панель
    for side, sx in (("right", -1), ("left", 1)):
        r = m.bone(f"robe_{side}", [2.5 * sx, 12, 0], "body")
        r.cube([-5 if sx < 0 else 0, 5, -3.5], [5, 7, 7], "hd_robe_plain")
        r.cube([-5.75 if sx < 0 else 0, 1, -4], [5.75, 4.5, 8], "hd_robe", tint={"down": 0.35})
    body.cube([-2, 2, -4.25], [4, 12.5, 0.5], "hd_tabard", deco={"north": tabard_emblem})
    body.cube([-2.5, 2, 3.75], [5, 12, 0.5], "hd_robe")

    # торс: поддоспешник, рёбра грудной пластины между полами рясы
    body.cube([-4, 12, -2], [8, 11, 4], "hd_inner")
    body.cube([-2, 14.5, -2.5], [4, 7.5, 0.5], "hd_metal", deco={"north": chest_ribs})
    body.cube([-1.5, 18.5, -3], [3, 3, 0.5], "hd_brass", deco={"north": emblem(0.46)})
    body.cube([-4.5, 12, -2.75], [2.5, 11, 5.5], "hd_robe_plain")
    body.cube([2, 12, -2.75], [2.5, 11, 5.5], "hd_robe_plain")
    body.cube([-2, 12, 2], [4, 11, 0.75], "hd_robe_plain")
    # пояс, пряжка, подсумки, инфопланшет
    body.cube([-4.75, 12, -3], [9.5, 1.5, 6], "hd_leather")
    body.cube([-1, 11.75, -3.4], [2, 2, 0.5], "hd_brass", deco={"north": emblem(0.4)})
    body.cube([-4.5, 10, -3.25], [2, 2.5, 1.5], "hd_leather")
    body.cube([2.5, 10, -3.25], [2, 2.5, 1.5], "hd_leather")
    body.cube([4.6, 8.5, -1.5], [0.75, 4, 3], "hd_dark_plain", deco={"west": slate_screen})
    body.cube([-5.1, 8, 0.5], [0.5, 4.5, 0.75], "hd_metal_plain")              # гаечный ключ на поясе
    body.cube([-5.25, 7.25, 0.25], [0.8, 1, 1.25], "hd_metal_plain")
    # печати чистоты: на груди и на табарде
    body.cube([1.25, 19, -3.1], [1.5, 1.5, 0.5], "hd_wax")
    body.cube([1.4, 15.25, -2.85], [0.5, 3.75, 0], "hd_parchment")
    body.cube([2.1, 15.75, -2.85], [0.5, 3.25, 0], "hd_parchment")
    body.cube([-0.75, 7, -4.6], [1.5, 1.5, 0.5], "hd_wax")
    body.cube([-0.6, 3.25, -4.4], [0.5, 3.75, 0], "hd_parchment")
    body.cube([0.2, 3.75, -4.4], [0.5, 3.25, 0], "hd_parchment")
    # кабели от маски в грудь
    body.cube([-2.25, 20, -3.25], [0.5, 3.5, 0.5], "hd_cable")
    body.cube([1.75, 20, -3.25], [0.5, 3.5, 0.5], "hd_cable")

    # пелерина и горжет, спинной плащ со знаком
    mantle = m.bone("mantle", [0, 23, 0], "body")
    mantle.cube([-5.75, 19.5, -3.25], [11.5, 3.5, 6.75], "hd_robe_clean", tint={"down": 0.4})
    mantle.cube([-3.5, 22.5, -2.75], [7, 1.25, 5.5], "hd_dark")
    mantle.cube([-6.25, 17, -3.5], [12.5, 3, 7.25], "hd_robe", tint={"down": 0.35})
    mantle.cube([-5.5, 19.25, -3.9], [1.5, 1.5, 0.5], "hd_wax")                 # печать на пелерине
    mantle.cube([-5.35, 15.75, -3.65], [0.5, 3.5, 0], "hd_parchment")
    mantle.cube([-4.65, 16.25, -3.65], [0.5, 3, 0], "hd_parchment")
    cape = m.bone("cape", [0, 20, 3.5], "body")
    cape.cube([-5, 6, 3.25], [10, 14, 0.5], "hd_robe")
    cape.cube([-2, 14, 3.75], [4, 4, 0.5], "hd_brass", deco={"south": emblem(0.46)})

    # --- голова: маска, бионический глаз, россыпь линз, вокс-решётка
    head = m.bone("head", [0, 23, 0], "body")
    head.cube([-3, 23.25, -3], [6, 6.5, 6], "hd_mask", deco={"north": mask_face})
    head.cube([-2.9, 26.25, -3.75], [2.4, 2.4, 0.75], "hd_brass")
    head.cube([-2.5, 26.65, -4], [1.6, 1.6, 0.25], "hd_glow", glow="all")
    head.cube([0.6, 27, -3.5], [1.25, 1.25, 0.5], "hd_glow", glow="all")
    head.cube([2, 26.25, -3.5], [0.75, 0.75, 0.5], "hd_glow", glow="all")
    head.cube([1, 25.5, -3.4], [0.5, 0.5, 0.4], "hd_glow", glow="all")
    head.cube([-1.5, 23.75, -3.6], [3, 2, 0.6], "hd_metal_plain", deco={"north": grille})
    head.cube([-2.75, 23.5, -3.25], [0.75, 1, 0.75], "hd_cable")
    head.cube([2, 23.5, -3.25], [0.75, 1, 0.75], "hd_cable")
    head.cube([4.75, 26, 0], [0.5, 4.5, 0.5], "hd_metal_plain")        # антенна вокса сбоку капюшона
    head.cube([4.65, 30.5, -0.1], [0.7, 0.7, 0.7], "hd_glow2", glow="all")
    hood = m.bone("hood", [0, 23, 0], "head")
    # глубокий капюшон: лицо утоплено на 2.5 px, изнанка в тени
    hood.cube([-4.75, 30, -5.5], [9.5, 1.75, 9.75], "hd_robe_clean", tint={"down": 0.25})
    hood.cube([-4.75, 22.5, -5.5], [1.5, 7.5, 9.75], "hd_robe_clean", tint={"west": 0.3})
    hood.cube([3.25, 22.5, -5.5], [1.5, 7.5, 9.75], "hd_robe_clean", tint={"east": 0.3})
    hood.cube([-3.25, 22.5, 3], [6.5, 7.5, 1.25], "hd_robe_clean")
    hood.cube([-4.75, 29.25, -6], [9.5, 1, 1], "hd_robe_clean", tint={"down": 0.35})
    hood.cube([-1.75, 30.5, -6.75], [3.5, 1.25, 1.5], "hd_robe_clean", tint={"down": 0.35})
    hood.cube([-2.25, 31.75, -3], [4.5, 0.75, 6], "hd_robe_clean")
    hood.cube([-1.5, 32.5, -1], [3, 0.5, 3], "hd_robe_clean")

    # --- руки: широкие рукава с кромкой, аугметические кисти
    for side, sx in (("right", -1), ("left", 1)):
        arm = m.bone(f"{side}_arm", [5.5 * sx, 22, 0], "body", rotation=[12, 0, 0])
        def A(x, w):
            return x if sx < 0 else X(x, w)
        arm.cube([A(-7.5, 3), 14.5, -2], [3, 7.5, 4], "hd_robe_plain")
        arm.cube([A(-8.25, 4.5), 11, -2.75], [4.5, 4, 5.5], "hd_robe_plain", tint={"down": 0.2})
        arm.cube([A(-8.35, 4.7), 11, -2.85], [4.7, 0.5, 5.7], "hd_brass")
        arm.cube([A(-7, 2), 11, -1.25], [2, 1.5, 2.5], "hd_inner")
        arm.cube([A(-7.25, 2.5), 9.5, -1.5], [2.5, 2, 3], "hd_metal_plain")
        for k in range(3):
            arm.cube([A(-7.25, 0.75), 8, -1.5 + k * 1.1], [0.75, 1.5, 0.75], "hd_dark_plain")
        arm.cube([A(-5, 0.75), 9.5, -1.75], [0.75, 1.25, 0.75], "hd_dark_plain")

    # --- инфопланшет в левой руке
    slate = m.bone("left_item", [6, 9.5, 0], "left_arm")
    slate.cube([5.25, 6.5, -3.5], [1.5, 4, 3.5], "hd_dark_plain", rotation=[-25, 0, 0], pivot=[6, 9, -1])
    slate.cube([5, 6.75, -3.25], [0.25, 3.5, 3], "hd_screen", rotation=[-25, 0, 0], pivot=[6, 9, -1],
               deco={"east": slate_screen}, glow=lambda g, r, f, S, pal: _glow_screen(g, r, f))

    # --- Омниссианский ключ-топор в правой руке
    axe = m.bone("right_item", [-6, 9.5, 0], "right_arm")
    axe.cube([-6.5, 0, -0.5], [1, 27, 1], "hd_dark_plain")
    for y in (4, 12, 18):
        axe.cube([-6.75, y, -0.75], [1.5, 1, 1.5], "hd_brass")
    axe.cube([-6.6, 7.5, -0.6], [1.2, 3.5, 1.2], "hd_leather")
    axe.cube([-6.75, -1, -0.75], [1.5, 1, 1.5], "hd_brass")
    axe.cube([-6.75, 15, -0.75], [1.5, 1.5, 1.5], "hd_glow2", glow="all")
    axe.cube([-7, 19, -5.5], [1, 8, 5], "hd_metal", deco={"east": cog_blade, "west": cog_blade})
    for y in (19.25, 21.25, 23.25, 25.25):
        axe.cube([-6.75, y, -6.25], [0.5, 1, 0.75], "hd_metal_plain")
    for z in (-5, -3):
        axe.cube([-6.75, 27, z], [0.5, 0.75, 1], "hd_metal_plain")
    axe.cube([-7.2, 21.5, -4], [1.4, 3.25, 3], "hd_brass")
    axe.cube([-7.4, 22, -3.5], [1.8, 2.25, 2], "hd_bone", deco={"east": skull_side, "west": skull_side})
    axe.cube([-6.75, 23, 0.5], [0.5, 1, 3], "hd_metal_plain")
    axe.cube([-6.75, 27, -0.25], [0.5, 2.5, 0.5], "hd_brass")

    # --- ранец: корпус, окно плазменного ядра, рёбра охлаждения, трубы
    pack = m.bone("backpack", [0, 18, 3], "body")
    pack.cube([-3.5, 13, 2.75], [7, 9, 3.25], "hd_dark")
    pack.cube([-1.5, 15, 5.9], [3, 4.5, 0.35], "hd_glow2", glow="all")
    pack.cube([-1.5, 16.25, 6.1], [3, 0.5, 0.25], "hd_brass")
    pack.cube([-1.5, 18, 6.1], [3, 0.5, 0.25], "hd_brass")
    for i in range(5):
        pack.cube([-4.25, 13.75 + i * 1.5, 3.25], [0.75, 0.5, 2.5], "hd_metal_plain")
        pack.cube([3.5, 13.75 + i * 1.5, 3.25], [0.75, 0.5, 2.5], "hd_metal_plain")
    pack.cube([-3, 22, 3.5], [1.25, 4.5, 1.25], "hd_rusty")
    pack.cube([-3.25, 26.5, 3.25], [1.75, 0.75, 1.75], "hd_dark_plain")
    pack.cube([-1.25, 22, 4.25], [1, 3, 1], "hd_rusty")
    pack.cube([-1.5, 25, 4], [1.5, 0.5, 1.5], "hd_dark_plain")
    pack.cube([3.6, 18.5, 3.5], [0.5, 3, 3], "hd_brass", deco={"west": emblem(0.48)})
    pack.cube([1.5, 19.5, 6.05], [1.25, 1.25, 0.4], "hd_wax")
    pack.cube([1.65, 16.25, 6.3], [0.4, 3.25, 0], "hd_parchment")
    pack.cube([2.25, 16.75, 6.3], [0.4, 2.75, 0], "hd_parchment")
    pack.cube([-2.5, 21.5, 3.25], [0.6, 0.6, 2.5], "hd_cable", rotation=[-35, 0, 0], pivot=[-2.2, 21.8, 3.25])
    pack.cube([1.9, 21.5, 3.25], [0.6, 0.6, 2.5], "hd_cable", rotation=[-35, 0, 0], pivot=[2.2, 21.8, 3.25])

    # --- серворука над левым плечом: плечо вверх, предплечье вперёд-вниз, клешня
    # отклонена наружу, чтобы не резать капюшон; клешня встаёт у левой щеки
    s1 = m.bone("servo_arm", [2.5, 22, 5], "backpack", rotation=[0, 0, -25])
    s1.cube([1.75, 21.25, 4.25], [1.5, 1.5, 1.5], "hd_brass")
    s1.cube([2, 22.5, 4.5], [1, 6, 1], "hd_metal_plain")
    s1.cube([2.75, 23, 5.25], [0.4, 5, 0.4], "hd_metal_plain")
    s2 = m.bone("servo_arm_2", [2.5, 28.5, 5], "servo_arm", rotation=[105, 0, 0])
    s2.cube([1.75, 27.75, 4.25], [1.5, 1.5, 1.5], "hd_brass")
    s2.cube([2, 28.5, 4.6], [1, 7, 0.8], "hd_dark")
    s2.cube([2.4, 29, 5.5], [0.4, 5.5, 0.4], "hd_metal_plain")
    claw = m.bone("servo_claw", [2.5, 35.5, 5], "servo_arm_2")
    claw.cube([1.75, 35.5, 4.25], [1.5, 1, 1.5], "hd_dark_plain")
    claw.cube([1.75, 36.5, 4.25], [0.5, 2, 0.5], "hd_metal_plain", rotation=[0, 0, -18], pivot=[2, 36.5, 4.5])
    claw.cube([2.75, 36.5, 4.25], [0.5, 2, 0.5], "hd_metal_plain", rotation=[0, 0, 18], pivot=[3, 36.5, 4.5])
    claw.cube([2.25, 36.5, 5.25], [0.5, 2, 0.5], "hd_metal_plain", rotation=[18, 0, 0], pivot=[2.5, 36.5, 5.5])

    # --- два механодендрита справа: резак и сканер; каждое звено — кость
    # углы подобраны перебором: дендрит A перегибается через правое плечо к лицу, B огибает бок на уровне груди
    for name, (x, y, r1, tool) in {"mechadendrite_a": (-2.75, 20.5, [90, 20, 60], "cutter"),
                                   "mechadendrite_b": (-1.5, 17, [80, 0, 60], "lens")}.items():
        parent, z = "backpack", 6
        for k in range(4):
            bn = name if k == 0 else f"{name}_{k + 1}"
            b = m.bone(bn, [x, y, z], parent, rotation=r1 if k == 0 else [30, 0, 0])
            b.cube([x - 0.3, y - 0.3, z], [0.6, 0.6, 3], "hd_cable")
            b.cube([x - 0.4, y - 0.4, z + 2.6], [0.8, 0.8, 0.6], "hd_brass")
            parent, z = bn, z + 3
        tip = m.bone(f"{name}_tip", [x, y, z], parent, rotation=[18, 0, 0])
        if tool == "cutter":
            tip.cube([x - 0.5, y - 0.5, z], [1, 1, 1.5], "hd_dark_plain")
            tip.cube([x - 0.25, y - 0.25, z + 1.5], [0.5, 0.5, 0.75], "hd_glow2", glow="all")
        else:
            tip.cube([x - 0.75, y - 0.75, z], [1.5, 1.5, 0.75], "hd_brass")
            tip.cube([x - 0.5, y - 0.5, z + 0.75], [1, 1, 0.25], "hd_glow", glow="all")

    # --- кадило на правом бедре
    censer = m.bone("censer", [-4.5, 12, -2.5], "body")
    censer.cube([-4.6, 8.5, -2.6], [0.25, 3.5, 0.25], "hd_metal_plain")
    censer.cube([-5.25, 7, -3.25], [1.5, 1.5, 1.5], "hd_brass")
    censer.cube([-5, 8.5, -3], [1, 0.5, 1], "hd_brass")
    censer.cube([-4.75, 7.5, -3.4], [0.5, 0.5, 0.15], "hd_glow2", glow="all")
    return m


def animations():
    from gen_entities import humanoid_anims  # общий набор: idle, walk, run, удары
    anims = humanoid_anims(walk_amp=18, arm_amp=14, extra_idle={
        "servo_arm": {"rotation": track(lambda t: [3 * sin(t), 4 * sin(t, 0.3), 0], 5.0, 12)},
        "servo_arm_2": {"rotation": track(lambda t: [6 * sin(t, 0.2), 0, 0], 5.0, 12)},
        "servo_claw": {"rotation": track(lambda t: [0, 25 * sin(t * 2 % 1), 0], 5.0, 12)},
        "mechadendrite_a": {"rotation": track(lambda t: [6 * sin(t), 8 * sin(t, 0.3), 0], 4.0, 12)},
        "mechadendrite_a_2": {"rotation": track(lambda t: [10 * sin(t, 0.2), 0, 0], 4.0, 12)},
        "mechadendrite_a_3": {"rotation": track(lambda t: [10 * sin(t, 0.4), 0, 0], 4.0, 12)},
        "mechadendrite_b": {"rotation": track(lambda t: [6 * sin(t, 0.5), -8 * sin(t, 0.8), 0], 3.0, 12)},
        "mechadendrite_b_2": {"rotation": track(lambda t: [10 * sin(t, 0.7), 0, 0], 3.0, 12)},
        "mechadendrite_b_3": {"rotation": track(lambda t: [12 * sin(t, 0.9), 0, 0], 3.0, 12)},
        "censer": {"rotation": track(lambda t: [8 * sin(t), 0, 4 * sin(t, 0.25)], 3.0, 12)},
        "cape": {"rotation": track(lambda t: [1.5 + 1.5 * sin(t), 0, 0], 3.0, 12)},
    }, extra_walk={
        "robe_right": {"rotation": track(lambda t: [11 * sin(t), 0, 0], 1.0)},
        "robe_left": {"rotation": track(lambda t: [-11 * sin(t), 0, 0], 1.0)},
        "cape": {"rotation": track(lambda t: [6 + 3 * abs(sin(t)), 0, 2 * sin(t)], 1.0)},
        "censer": {"rotation": track(lambda t: [-20 * sin(t, 0.15), 0, 6 * sin(t)], 1.0)},
        "mechadendrite_a": {"rotation": track(lambda t: [8 * sin(t), 0, 0], 1.0)},
        "mechadendrite_b": {"rotation": track(lambda t: [-8 * sin(t), 0, 0], 1.0)},
        "servo_arm_2": {"rotation": track(lambda t: [4 * sin(t * 2 % 1), 0, 0], 1.0)},
    })
    for a in ("move.run",):
        anims[a]["bones"]["robe_right"] = {"rotation": track(lambda t: [16 * sin(t), 0, 0], 0.6)}
        anims[a]["bones"]["robe_left"] = {"rotation": track(lambda t: [-16 * sin(t), 0, 0], 0.6)}
        anims[a]["bones"]["cape"] = {"rotation": track(lambda t: [18 + 4 * abs(sin(t)), 0, 0], 0.6)}
    anims["misc.interact"] = {"length": 2.0, "bones": {  # благословение: ключ вверх, серворука и дендриты тянутся вперёд
        "right_arm": {"rotation": keys([(0, [0, 0, 0]), (0.45, [-150, 0, 10]), (1.2, [-150, 0, 10]), (1.5, [-60, 0, 0]),
                                        (2.0, [0, 0, 0])])},
        "left_arm": {"rotation": keys([(0, [0, 0, 0]), (0.5, [-40, 0, -20]), (1.5, [-40, 0, -20]), (2.0, [0, 0, 0])])},
        "head": {"rotation": keys([(0, [0, 0, 0]), (0.45, [-15, 0, 0]), (1.5, [12, 0, 0]), (2.0, [0, 0, 0])])},
        "servo_arm_2": {"rotation": keys([(0, [0, 0, 0]), (0.7, [-25, 0, 0]), (1.6, [-25, 0, 0]), (2.0, [0, 0, 0])])},
        "servo_claw": {"rotation": keys([(0, [0, 0, 0]), (0.8, [0, 90, 0]), (1.2, [0, 0, 0]), (2.0, [0, 0, 0])])},
        "mechadendrite_a": {"rotation": keys([(0, [0, 0, 0]), (0.6, [-30, 20, 0]), (2.0, [0, 0, 0])])},
        "mechadendrite_b": {"rotation": keys([(0, [0, 0, 0]), (0.6, [-20, 30, 0]), (2.0, [0, 0, 0])])},
    }}
    return anims


def generate():
    import zlib
    from geo import MATERIALS
    from hd import hd_cloth
    MATERIALS["hd_tabard"] = hd_cloth("tabard", hem="trim", folds=False)
    m = build()
    print("tech_priest")
    m.build()
    for name, pal in (("tech_priest", TECH_PRIEST), ("dark_tech_priest", DARK_TECH_PRIEST)):
        base, glow = m.paint(pal, seed=zlib.crc32(name.encode()))
        save_png(base, "entity", f"{name}.png")
        save_png(glow, "entity", f"{name}_glow.png")
    write_animations("tech_priest", animations())
