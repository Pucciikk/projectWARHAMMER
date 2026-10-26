"""
Имперский челнок и десантная капсула — транспорт всех лоялистов (концепт автора: Chelnok.webp).

    python3 tools/models/shuttle.py

Челнок большой: 10 блоков в длину, 9 в размахе крыльев, 7 в высоту на выпущенных опорах.
Корпус оливково-серый в панелях, нос — бронированный короб с красной каймой и зубьями по нижней кромке,
кабина с узкими бойницами, на хребте — длинное орудие, под крыльями — турбины с круглыми воздухозаборниками,
сзади — кили и антенны. Под брюхом в захватах висит капсула; её же модель — отдельная сущность drop_capsule.

Кости челнока: hull, turret, gear_<front|back>_<left|right> (+_2 — шток), clamp_left/right, capsule,
thrust_<left|right> (вертикальная тяга турбин), exhaust_left/right (маршевые сопла).
Анимации: move.fly (опоры убраны), misc.land (опоры выпущены, турбины вниз), misc.deploy (захваты разжимаются).
Капсула: door_left/right, thrusters; misc.idle, misc.deploy (двери открыты), move.fly (взлёт обратно на орбиту).
"""
import math
import zlib

import numpy as np

import hd
from gen_blocks import aquila
from geo import MATERIALS, Model, keys, save_png, shade, sin, track, write_animations
from priest_hd import _icon, _paste, emblem

PAL = dict(
    hull=(126, 128, 104), hull2=(104, 108, 88), trim=(150, 40, 32), dark=(54, 54, 52), metal=(132, 132, 128),
    steel=(170, 170, 166), bone=(206, 200, 180), glass=(22, 40, 40), brass=(186, 146, 70), soot=(40, 38, 36),
    glow=(255, 190, 90), glow2=(120, 220, 255), mech=(138, 34, 30), cable=(30, 30, 32), inner=(26, 26, 28),
    lumen=(120, 255, 140), parchment=(214, 200, 160), wax=(130, 20, 24), leather=(80, 60, 40), screen=(16, 20, 18),
    rust=(110, 64, 36), lamp=(255, 170, 40),
)


# ------------------------------------------------------------------ материалы

def hd_hull(key="hull", grid=20):
    """Обшивка: панели с утопленными швами, заклёпки по швам, копоть и потёки сверху вниз, сколы краски."""
    def f(region, face, pal, rng):
        h, w = hd._base(region, pal[key], face, rng, amp=6, cell=10, grain=5)
        c = shade(pal[key], hd.face_light(face))
        step = grid * 2  # S = 2
        ox, oy = rng.randrange(step), rng.randrange(step)
        for x in range(ox, w, step):
            region[:, x, :3] = shade(c, 0.7)
            if x + 1 < w:
                region[:, x + 1, :3] = shade(c, 1.06)
            for y in range(3, h - 2, 6):
                if x + 3 < w:
                    region[y, x + 3, :3] = shade(c, 1.3)
        for y in range(oy, h, step):
            region[y, :, :3] = shade(c, 0.7)
            if y + 1 < h:
                region[y + 1, :, :3] = shade(c, 1.06)
        # одна панель из нескольких — другого оттенка (заменённый лист)
        for _ in range(max(1, (w // step) * (h // step) // 4)):
            px, py = ox + rng.randrange(max(1, w // step)) * step, oy + rng.randrange(max(1, h // step)) * step
            hd._mul(region[py + 2:py + step, px + 2:px + step], 0.9 + rng.random() * 0.18)
        if face not in ("up", "down"):
            st = hd.vnoise(h, w, 3, rng)  # потёки копоти вниз от швов
            drip = np.clip(st, 0, 1) * np.linspace(0.05, 0.3, h, dtype=np.float32)[:, None]
            hd._mul(region, (1 - drip)[..., None])
            hd.grime(region, 0.3, 0.2)
        n = hd.vnoise(h, w, 2, rng)
        region[n > 0.93, :3] = np.array(shade(pal["metal"], hd.face_light(face)), np.uint8)  # сколы до металла
        hd.bevel(region, 1.2, 0.62)
    return f


def hd_paint(key, chips=0.9):
    """Крашеный металл (красная кайма, капсула Механикус): ровный цвет, сколы, фаска."""
    def f(region, face, pal, rng):
        h, w = hd._base(region, pal[key], face, rng, amp=7, cell=5, grain=4)
        n = hd.vnoise(h, w, 2, rng)
        region[n > chips, :3] = np.array(shade(pal["dark"], 1.1), np.uint8)
        if face not in ("up", "down"):
            hd.grime(region, 0.3, 0.25)
        hd.bevel(region, 1.25, 0.6)
    return f


def hd_glass(region, face, pal, rng):
    h, w = hd._base(region, pal["glass"], face, rng, amp=4, cell=6, grain=2)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    band = np.abs((xx / max(1, w) + yy / max(1, h)) - 0.6) < 0.08  # блик
    hd._mul(region, np.where(band, 1.9, 1.0)[..., None])
    hd.bevel(region, 1.4, 0.5)


def hd_barrel(region, face, pal, rng):
    """Ствол: светлый, с тёмными кольцами охлаждения."""
    h, w = hd._base(region, pal["bone"], face, rng, amp=6, cell=4, grain=4)
    along = w if face in ("up", "down") else w
    for x in range(0, along, 10):
        region[:, x:x + 2, :3] = shade(pal["bone"], 0.55)
    hd.grime(region, 0.25, 0.3)
    hd.bevel(region, 1.2, 0.6)


def hd_vent(region, face, pal, rng):
    """Решётка: тёмные щели, светлые ламели."""
    h, w = hd._base(region, pal["dark"], face, rng, amp=4, cell=4, grain=3)
    for y in range(1, h - 1, 3):
        region[y, 1:-1, :3] = shade(pal["dark"], 0.35)
        region[y + 1 if y + 1 < h else y, 1:-1, :3] = shade(pal["dark"], 1.4)
    hd.bevel(region, 1.2, 0.6)


def hd_teeth(region, face, pal, rng):
    hd._base(region, pal["steel"], face, rng, amp=6, cell=3, grain=5)
    hd.bevel(region, 1.5, 0.5)


def hd_thrust(region, face, pal, rng):
    """Пламя турбины: голубовато-белое ядро, оранжевые края."""
    h, w = region.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.clip(np.hypot((xx - (w - 1) / 2) / max(1, w / 2), (yy - (h - 1) / 2) / max(1, h / 2)), 0, 1)
    core, rim = np.array((235, 245, 255), np.float32), np.array(pal["glow"], np.float32)
    region[..., :3] = (core * (1 - d[..., None]) + rim * d[..., None]).astype(np.uint8)
    region[..., 3] = 255


MATERIALS.update({
    "hd_hull": hd_hull(),
    "hd_hull2": hd_hull("hull2", grid=14),
    "hd_trim": hd_paint("trim"),
    "hd_mech": hd_paint("mech", chips=0.88),
    "hd_gun": hd.hd_metal("dark", rivets=False),
    "hd_steel": hd.hd_metal("steel", panels=False),
    "hd_glass": hd_glass,
    "hd_barrel": hd_barrel,
    "hd_vent": hd_vent,
    "hd_teeth": hd_teeth,
    "hd_thrust": hd_thrust,
    "hd_lumen": hd.mat_glow("lumen"),
    "hd_lamp": hd.mat_glow("lamp"),
})


# ------------------------------------------------------------------ рисунки на гранях

def window_slits(n):
    """Бойницы кабины: n узких тёмных окон с зелёным отсветом приборов."""
    def f(region, S, pal):
        h, w = region.shape[:2]
        gap = w / n
        for i in range(n):
            x0, x1 = int(i * gap + gap * 0.18), int((i + 1) * gap - gap * 0.18)
            region[int(h * 0.3):int(h * 0.75), x0:x1, :3] = pal["glass"]
            region[int(h * 0.3), x0:x1, :3] = shade(pal["glass"], 0.4)
            region[int(h * 0.68):int(h * 0.75), x0:x1, :3] = shade(pal["lumen"], 0.45)
    return f


def turbine(region, S, pal):
    """Воздухозаборник: обод, тёмная глубина, лопатки веером, кок в центре."""
    def draw(d, W, H):
        cx, cy, R = W / 2, H / 2, min(W, H) * 0.48
        d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=shade(pal["metal"], 1.1) + (255,))
        r2 = R * 0.84
        d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], fill=(20, 20, 22, 255))
        for i in range(14):
            a = i * math.pi * 2 / 14
            pts = [(cx + math.cos(a) * r2 * 0.25, cy + math.sin(a) * r2 * 0.25),
                   (cx + math.cos(a + 0.35) * r2 * 0.95, cy + math.sin(a + 0.35) * r2 * 0.95),
                   (cx + math.cos(a + 0.5) * r2 * 0.9, cy + math.sin(a + 0.5) * r2 * 0.9)]
            d.polygon(pts, fill=shade(pal["metal"], 0.62) + (255,))
        rc = R * 0.22
        d.ellipse([cx - rc, cy - rc, cx + rc, cy + rc], fill=shade(pal["steel"], 1.0) + (255,))
    h, w = region.shape[:2]
    _paste(region, _icon(w, h, draw))


def nozzle_ring(region, S, pal):
    """Сопло сзади: тёмный обод вокруг раскалённого нутра (нутро светится отдельным кубом)."""
    h, w = region.shape[:2]
    region[..., :3] = shade(pal["dark"], 0.8)
    region[2:-2, 2:-2, :3] = shade(pal["soot"], 0.6)


def chevrons(region, S, pal):
    """Красно-белые шевроны у законцовки крыла."""
    h, w = region.shape[:2]
    for y in range(h):
        for x in range(w):
            if ((x + y) // 6) % 2 == 0:
                region[y, x, :3] = shade(pal["trim"], 0.95)
            else:
                region[y, x, :3] = shade(pal["bone"], 0.95)


def hazard(region, S, pal):
    """Жёлто-чёрная разметка люка."""
    h, w = region.shape[:2]
    for y in range(h):
        for x in range(w):
            region[y, x, :3] = (190, 150, 30) if ((x + y) // 4) % 2 == 0 else (24, 22, 20)


def skull_stencil(region, S, pal):
    """Белый трафаретный череп с крыльями — знак борта."""
    def draw(d, W, H):
        c = shade(pal["bone"], 1.0) + (255,)
        cx, cy, r = W / 2, H * 0.45, min(W, H) * 0.2
        d.ellipse([cx - r, cy - r, cx + r, cy + r * 0.9], fill=c)
        d.rectangle([cx - r * 0.6, cy + r * 0.5, cx + r * 0.6, cy + r * 1.25], fill=c)
        for ex in (-1, 1):
            d.ellipse([cx + ex * r * 0.45 - r * 0.25, cy - r * 0.1, cx + ex * r * 0.45 + r * 0.25, cy + r * 0.38],
                      fill=(0, 0, 0, 0))
            for k in range(3):
                y = cy - r * 0.4 + k * r * 0.45
                d.polygon([(cx + ex * r * 1.1, y), (cx + ex * (r * 2.4 - k * r * 0.4), y - r * 0.2),
                           (cx + ex * (r * 2.3 - k * r * 0.4), y + r * 0.25), (cx + ex * r * 1.1, y + r * 0.3)], fill=c)
    h, w = region.shape[:2]
    icon = _icon(w, h, draw)
    m = icon[..., 3] > 100
    region[m, :3] = icon[m, :3]


def interior(region, S, pal):
    """Нутро капсулы: тёмная ниша, ложемент и зелёные полосы люменов (светятся отдельно)."""
    h, w = region.shape[:2]
    region[..., :3] = pal["inner"]
    region[int(h * 0.15):int(h * 0.85), int(w * 0.25):int(w * 0.75), :3] = shade(pal["leather"], 0.7)
    for x in (int(w * 0.12), int(w * 0.85)):
        region[int(h * 0.1):int(h * 0.9), x:x + 2, :3] = pal["lumen"]


def interior_glow(g, region, face, S, pal):
    if face != "north":
        return
    h, w = region.shape[:2]
    for x in (int(w * 0.12), int(w * 0.85)):
        g[int(h * 0.1):int(h * 0.9), x:x + 2, :3] = pal["lumen"]
        g[int(h * 0.1):int(h * 0.9), x:x + 2, 3] = 255


def purity_seal(region, S, pal):
    """Печать чистоты: красный сургуч и полоска пергамента вниз."""
    h, w = region.shape[:2]
    cx = w // 2
    region[int(h * 0.3):int(h * 0.95), cx - 2:cx + 2, :3] = pal["parchment"]
    for y in range(int(h * 0.35), int(h * 0.9), 3):
        region[y, cx - 1:cx + 1, :3] = (60, 50, 40)
    region[int(h * 0.15):int(h * 0.35), cx - 4:cx + 4, :3] = pal["wax"]


def window_glow(g, region, face, S, pal):
    if face != "north":
        return
    h, w = region.shape[:2]
    m = (region[..., 1] > region[..., 0] + 40)
    g[m, :3] = region[m, :3]
    g[m, 3] = 255


# ------------------------------------------------------------------ капсула (общая для челнока и сущности)

def capsule(m, parent, y0=0.0, doors=True):
    """
    Десантная капсула Механикус 28×44 px: восьмигранный корпус, двустворчатая дверь спереди, купол с проушиной.
    Ставится на y0 (у челнока — висит в захватах под брюхом).
    """
    b = m.bone("capsule" if parent else "body", [0, y0, 0], parent)
    # основание с тормозными соплами по углам
    b.cube([-15, y0, -15], [30, 4, 30], "hd_gun")
    for sx in (-1, 1):
        for sz in (-1, 1):
            b.cube([sx * 11 - 2.5, y0 - 1, sz * 11 - 2.5], [5, 1, 5], "hd_thrust", glow="all")
            b.cube([sx * 11 - 3, y0 + 0.5, sz * 11 - 3], [6, 3, 6], "hd_dark", inflate=0.25)
    # корпус: ниша спереди (дверной проём), рамы по краям
    b.cube([-13, y0 + 4, -9], [26, 30, 22], "hd_mech", face_mat={"north": "hd_inner"},
           deco={"north": interior}, glow=interior_glow)
    b.cube([-13, y0 + 4, -13], [3, 30, 4], "hd_gun")
    b.cube([10, y0 + 4, -13], [3, 30, 4], "hd_gun")
    b.cube([-13, y0 + 31, -13], [26, 3, 4], "hd_gun")
    b.cube([-10, y0 + 4, -13], [20, 1, 4], "hd_gun")
    # срезанные углы — восемь граней
    for sx in (-1, 1):
        for sz in (-1, 1):
            b.cube([sx * 13 - 3, y0 + 4, sz * 13 - 3], [6, 30, 6], "hd_mech", rotation=[0, 45, 0],
                   pivot=[sx * 13, y0, sz * 13])
    # латунные пояса и бронеплиты с печатями
    for y in (y0 + 9, y0 + 26):
        b.cube([-13.5, y, -9], [27, 2, 22.5], "hd_brass")
    b.cube([-14, y0 + 12, -4], [1, 12, 12], "hd_mech", deco={"east": emblem(0.4)})
    b.cube([13, y0 + 12, -4], [1, 12, 12], "hd_mech", deco={"west": emblem(0.4)})
    b.cube([-6, y0 + 12, 13], [12, 12, 1], "hd_mech", deco={"south": emblem(0.4)})
    # купол ступенями, проушина и вокс-антенна, янтарная лампа
    b.cube([-11, y0 + 34, -11], [22, 4, 22], "hd_gun")
    b.cube([-8, y0 + 38, -8], [16, 3, 16], "hd_mech")
    b.cube([-4, y0 + 41, -4], [8, 2, 8], "hd_brass")
    b.cube([-1.5, y0 + 43, -3], [3, 4, 1.5], "hd_steel")
    b.cube([-1.5, y0 + 43, 1.5], [3, 4, 1.5], "hd_steel")
    b.cube([-1.5, y0 + 46, -3], [3, 1.5, 6], "hd_steel")
    b.cube([7, y0 + 38, 5], [1, 9, 1], "hd_dark")
    b.cube([-9, y0 + 38, -9], [2.5, 2.5, 2.5], "hd_lamp", glow="all")
    # кабели вдоль граней
    for sx in (-1, 1):
        b.cube([sx * 13.6 - 0.75, y0 + 6, 6], [1.5, 26, 1.5], "hd_cable")
    if not doors:
        return b
    for side, sx in (("right", -1), ("left", 1)):
        d = m.bone(f"door_{side}" if parent is None else f"capsule_door_{side}", [sx * 10, y0 + 5, -12],
                   b.name)
        x0 = -10 if sx < 0 else 0
        d.cube([x0, y0 + 5, -14], [10, 26, 2], "hd_mech",
               deco={"north": emblem(0.42)} if sx < 0 else {"north": purity_seal},
               face_mat={"south": "hd_gun"})
        d.cube([x0 + (8.5 if sx < 0 else 0), y0 + 5, -14.5], [1.5, 26, 0.5], "hd_brass")
        d.cube([x0 + 2, y0 + 15, -15], [6, 2, 1], "hd_steel")
    return b


# ------------------------------------------------------------------ челнок

def build_shuttle():
    m = Model("shuttle", S=2, atlas_w=640)
    hull = m.bone("hull", [0, 70, 0])
    # фюзеляж
    hull.cube([-26, 50, -40], [52, 36, 92], "hd_hull")
    hull.cube([-22, 86, -36], [44, 5, 80], "hd_hull2")                         # крыша
    hull.cube([-26, 49, -40], [52, 1, 92], "hd_gun")                           # брюхо
    # бронированный нос-короб: красная кайма, зубья по нижней кромке, аквила
    hull.cube([-30, 48, -68], [60, 36, 28], "hd_hull", deco={"north": aquila_on_prow})
    hull.cube([-26, 84, -66], [52, 6, 26], "hd_hull2", rotation=[-14, 0, 0], pivot=[0, 84, -40])
    for x0, w in ((-30.5, 60.5 + 0.5),):
        hull.cube([x0, 46, -68.5], [w, 6, 29], "hd_trim")                      # нижний красный пояс
        hull.cube([x0, 82, -68.5], [w, 3, 29], "hd_trim")                      # верхний
    hull.cube([-30.5, 52, -68.5], [3, 30, 3], "hd_trim")
    hull.cube([27.5, 52, -68.5], [3, 30, 3], "hd_trim")
    for i in range(12):                                                        # зубья спереди
        x = -28 + i * 5
        hull.cube([x, 41, -69], [3.5, 5, 3.5], "hd_teeth", rotation=[0, 0, 45], pivot=[x + 1.75, 46, -67])
    for sx in (-1, 1):                                                         # и по бокам носа
        for i in range(5):
            z = -64 + i * 5
            hull.cube([sx * 30 - 1.75, 41, z], [3.5, 5, 3.5], "hd_teeth", rotation=[45, 0, 0],
                      pivot=[sx * 30, 46, z + 1.75])
    # кабина: бойницы над носом
    hull.cube([-18, 84, -48], [36, 9, 12], "hd_hull2", deco={"north": window_slits(5)}, glow=window_glow)
    hull.cube([-19, 93, -49], [38, 2, 14], "hd_gun")
    # бортовые плиты с красной полосой и люками
    for sx in (-1, 1):
        x = sx * 26 + (0 if sx > 0 else -3)
        hull.cube([x, 52, -38], [3, 30, 86], "hd_hull2")
        hull.cube([x - 0.25, 50, -38], [3.5, 4, 86], "hd_trim")
        hull.cube([x + (3 if sx > 0 else -0.5), 58, -30], [0.5, 20, 16], "hd_dark")        # люк
        hull.cube([x + (3.5 if sx > 0 else -1), 58, -12], [0.5, 4, 16], "hd_dark", deco={})
        hull.cube([x + (3 if sx > 0 else -0.5), 64, 18], [0.5, 12, 20], "hd_vent")
        hull.cube([x + (3 if sx > 0 else -0.5), 62, -10], [0.5, 16, 22], "hd_hull2",
                  deco={"east" if sx < 0 else "west": skull_stencil})
    # хребет, трубопроводы по бортам, скошенный подбородок под носом
    hull.cube([-4, 91, -30], [8, 3, 70], "hd_gun")
    for x in (-6, 6):
        hull.cube([x - 1, 91, -26], [2, 2, 60], "hd_cable")
    for sx in (-1, 1):
        for y in (80, 83):
            hull.cube([sx * 30.5 - 1, y, -36], [2, 2, 84], "hd_cable" if y == 80 else "hd_steel")
    hull.cube([-24, 44, -60], [48, 6, 20], "hd_hull2", rotation=[18, 0, 0], pivot=[0, 50, -40])
    # корма: блок двигателя и два маршевых сопла
    hull.cube([-24, 54, 52], [48, 30, 12], "hd_gun")
    hull.cube([-20, 84, 44], [40, 4, 18], "hd_vent")
    for sx in (-1, 1):
        hull.cube([sx * 12 - 7, 62, 64], [14, 14, 8], "hd_dark", deco={"south": nozzle_ring})
    for side, sx in (("right", -1), ("left", 1)):
        ex = m.bone(f"exhaust_{side}", [sx * 12, 69, 72], "hull")
        ex.cube([sx * 12 - 5, 64, 70.5], [10, 10, 2], "hd_thrust", glow="all")

    # орудие на хребте
    tur = m.bone("turret", [0, 91, -12], "hull")
    tur.cube([-10, 91, -22], [20, 6, 20], "hd_gun")
    tur.cube([-7, 97, -20], [14, 8, 14], "hd_hull2")
    tur.cube([-3, 98.5, -66], [6, 6, 46], "hd_barrel")
    tur.cube([-4, 97.5, -72], [8, 8, 8], "hd_gun")
    tur.cube([-1, 102, -18], [2, 6, 2], "hd_dark")
    # кили и антенны
    for sx in (-1, 1):
        hull.cube([sx * 16 - 1.5, 88, 34], [3, 24, 24], "hd_hull2", rotation=[-20, 0, sx * 18],
                  pivot=[sx * 16, 88, 46])
        hull.cube([sx * 16 - 2, 108, 46], [4, 3, 14], "hd_trim", rotation=[-20, 0, sx * 18], pivot=[sx * 16, 88, 46])
        hull.cube([sx * 8 - 0.5, 91, 20], [1, 22, 1], "hd_dark", rotation=[0, 0, sx * 10], pivot=[sx * 8, 91, 20])
        hull.cube([sx * 8 - 1, 109, 19.5], [2, 2, 2], "hd_lamp", glow="all", rotation=[0, 0, sx * 10],
                  pivot=[sx * 8, 91, 20])

    # крылья: корень, законцовка с шевронами, загнутый вниз киль
    for side, sx in (("right", -1), ("left", 1)):
        def X(a, w):
            return a if sx > 0 else -a - w
        hull.cube([X(26, 26), 66, -6], [26, 6, 40], "hd_hull")
        hull.cube([X(52, 20), 67, 2], [20, 4, 28], "hd_hull", deco={"up": chevrons})
        hull.cube([X(72, 3), 52, 4], [3, 19, 24], "hd_hull2")
        hull.cube([X(72, 3.5), 52, 4], [3.5, 3, 24], "hd_trim")
        hull.cube([X(26, 46), 72, -7], [46, 1, 2], "hd_trim")                  # передняя кромка
        # лазпушка под законцовкой
        hull.cube([X(60, 5), 61, -4], [5, 5, 20], "hd_gun")
        hull.cube([X(61, 3), 62, -30], [3, 3, 26], "hd_barrel")
        hull.cube([X(60.5, 4), 61.5, -33], [4, 4, 4], "hd_gun")
        # турбина: гондола, воздухозаборник с лопатками, вертикальная тяга вниз
        hull.cube([X(39, 18), 48, -12], [18, 18, 46], "hd_hull2")
        hull.cube([X(38, 20), 47, -16], [20, 20, 5], "hd_gun", deco={"north": turbine})
        hull.cube([X(38.5, 19), 47.5, 32], [19, 19, 5], "hd_gun", deco={"south": nozzle_ring})
        hull.cube([X(41, 14), 46, 0], [14, 2, 20], "hd_vent")
        hull.cube([X(42, 12), 66, -8], [12, 1, 30], "hd_dark")                 # пилон
        th = m.bone(f"thrust_{side}", [sx * 48, 46, 10], "hull")
        th.cube([X(42, 12), 40, 2], [12, 6, 16], "hd_thrust", glow="all")
        ex2 = m.bone(f"exhaust_{side}_2", [sx * 48, 57, 37], "hull")
        ex2.cube([X(41, 14), 50, 36.5], [14, 14, 1.5], "hd_thrust", glow="all")

    # опоры: стойка, шток и лапа; убираются, поворачиваясь вдоль брюха
    for name, sx, sz in (("gear_front_right", -1, -1), ("gear_front_left", 1, -1),
                         ("gear_back_right", -1, 1), ("gear_back_left", 1, 1)):
        x, z = sx * 20, (-30 if sz < 0 else 40)
        g = m.bone(name, [x, 52, z], "hull")
        g.cube([x - 4, 48, z - 4], [8, 6, 8], "hd_gun")
        g.cube([x - 3, 26, z - 3], [6, 24, 6], "hd_hull2")
        g.cube([x - 3.5, 40, z - 3.5], [7, 2, 7], "hd_trim")
        g2 = m.bone(name + "_2", [x, 28, z], name)
        g2.cube([x - 2, 4, z - 2], [4, 24, 4], "hd_steel")
        g2.cube([x - 1, 8, z + 2], [2, 18, 1.5], "hd_cable")
        g2.cube([x - 6, 0, z - 7], [12, 4, 14], "hd_gun")
        g2.cube([x - 5, 4, z - 5], [10, 2, 10], "hd_dark")

    # захваты капсулы и сама капсула под брюхом
    for side, sx in (("right", -1), ("left", 1)):
        c = m.bone(f"clamp_{side}", [sx * 12, 50, 0], "hull")
        X0 = sx * 12 - (0 if sx > 0 else 4)
        c.cube([X0, 40, -6], [4, 10, 12], "hd_gun")
        c.cube([X0 + (-3 if sx > 0 else 3), 38, -6], [4, 3, 12], "hd_steel")
    capsule(m, "hull", y0=5, doors=True)
    return m


def aquila_on_prow(region, S, pal):
    h, w = region.shape[:2]
    sub = region[int(h * 0.12):int(h * 0.62), int(w * 0.25):int(w * 0.75)]
    aquila(sub, S, {"brass": pal["bone"]})


def shuttle_anims():
    gear_up = {}
    for name, sz in (("gear_front_right", -1), ("gear_front_left", -1), ("gear_back_right", 1), ("gear_back_left", 1)):
        gear_up[name] = {"rotation": [85 if sz < 0 else -85, 0, 0]}
        gear_up[name + "_2"] = {"position": [0, 14, 0]}
    fly = {**gear_up,
           # в воздухе корпус гуляет на потоках: крен и тангаж на двух частотах, мелкая дрожь от турбин
           "hull": {"rotation": track(lambda t: [2.2 * sin(t) + 0.6 * sin(t * 3 % 1, 0.2) + 0.25 * sin(t * 13 % 1),
                                                 0.8 * sin(t, 0.4), 3.2 * sin(t, 0.3) + 0.8 * sin(t * 2 % 1, 0.1)
                                                 + 0.25 * sin(t * 11 % 1, 0.3)], 4.0, 96),
                    "position": track(lambda t: [0.4 * sin(t, 0.6), 1.6 * sin(t, 0.1) + 0.4 * sin(t * 3 % 1), 0], 4.0, 48)},
           "thrust_right": {"scale": [0.4, 0.4, 0.4]}, "thrust_left": {"scale": [0.4, 0.4, 0.4]},
           "exhaust_right": {"scale": track(lambda t: [1 + 0.15 * sin(t * 29 % 1), 1 + 0.15 * sin(t * 23 % 1), 1], 4.0, 96)},
           "exhaust_left": {"scale": track(lambda t: [1 + 0.15 * sin(t * 31 % 1), 1 + 0.15 * sin(t * 19 % 1), 1], 4.0, 96)},
           "turret": {"rotation": track(lambda t: [0, 6 * sin(t), 0], 4.0, 12)}}
    # на тяге и на опорах: тяжёлая масса покачивается, опоры пружинят, турбины подрагивают
    land = {"hull": {"position": track(lambda t: [0, 0.5 * sin(t * 2 % 1) + 0.12 * sin(t * 9 % 1), 0], 8.0, 96),
                     "rotation": track(lambda t: [0.9 * sin(t, 0.2) + 0.2 * sin(t * 7 % 1),
                                                  0.4 * sin(t, 0.5), 1.4 * sin(t * 2 % 1, 0.1) + 0.25 * sin(t * 11 % 1)], 8.0, 96)},
            "thrust_right": {"scale": track(lambda t: [1 + 0.1 * sin(t * 37 % 1), 1.3 + 0.3 * sin(t * 16 % 1), 1], 8.0, 96)},
            "thrust_left": {"scale": track(lambda t: [1 + 0.1 * sin(t * 41 % 1), 1.3 + 0.3 * sin(t * 16 % 1, 0.4), 1], 8.0, 96)},
            "exhaust_right": {"scale": [0.6, 0.6, 0.6]}, "exhaust_left": {"scale": [0.6, 0.6, 0.6]},
            "turret": {"rotation": track(lambda t: [0, 25 * sin(t), 0], 8.0, 12)},
            **{f"{g}_2": {"position": track(lambda t, i=i: [0, 0.35 * sin(t * 2 % 1, i * 0.1), 0], 8.0, 24)}
               for i, g in enumerate(("gear_front_right", "gear_front_left", "gear_back_right", "gear_back_left"))}}
    deploy = {
        "clamp_right": {"rotation": keys([(0, [0, 0, 0]), (0.5, [0, 0, -40])])},
        "clamp_left": {"rotation": keys([(0, [0, 0, 0]), (0.5, [0, 0, 40])])},
        "capsule": {"scale": [0, 0, 0]},
    }
    return {
        "move.fly": {"length": 4.0, "loop": True, "bones": fly},
        "misc.land": {"length": 8.0, "loop": True, "bones": land},
        # высадка: захваты разжались, капсула уже отдельная сущность — кость прячется
        "misc.deploy": {"length": 0.5, "loop": "hold_on_last_frame", "bones": deploy},
    }


def build_capsule():
    m = Model("drop_capsule", S=2, atlas_w=256)
    capsule(m, None, y0=0, doors=True)
    m.bone("thrusters", [0, 0, 0], "body").cube([-12, -6, -12], [24, 6, 24], "hd_thrust", glow="all")
    return m


def capsule_anims():
    doors_open = {
        "door_right": {"rotation": keys([(0, [0, 0, 0]), (0.25, [0, -10, 0]), (1.2, [0, -105, 0])])},
        "door_left": {"rotation": keys([(0, [0, 0, 0]), (0.25, [0, 10, 0]), (1.2, [0, 105, 0])])},
        "thrusters": {"scale": [0, 0, 0]},
    }
    return {
        "misc.idle": {"length": 2.0, "loop": True, "bones": {"thrusters": {"scale": [0, 0, 0]}}},
        "misc.deploy": {"length": 1.2, "loop": "hold_on_last_frame", "bones": doors_open},
        # спуск и взлёт: тормозные сопла горят, капсулу чуть потряхивает
        "move.fly": {"length": 0.6, "loop": True, "bones": {
            "thrusters": {"scale": track(lambda t: [1, 1 + 0.5 * sin(t), 1], 0.6, 8)},
            "body": {"rotation": track(lambda t: [0.8 * sin(t), 0, 0.8 * sin(t, 0.25)], 0.6, 8)},
        }},
    }


def finish(m, name, anims):
    print(name)
    m.build()
    base, glow = m.paint(PAL, seed=zlib.crc32(name.encode()))
    save_png(base, "entity", f"{name}.png")
    save_png(glow, "entity", f"{name}_glow.png")
    write_animations(name, anims)


def generate():
    finish(build_shuttle(), "shuttle", shuttle_anims())
    finish(build_capsule(), "drop_capsule", capsule_anims())


if __name__ == "__main__":
    generate()
