"""
Мини-конструктор моделей GeckoLib (формат Bedrock geometry 1.12.0) с процедурной текстурой.

Модель собирается из костей и кубов в пикселях модели (16 = 1 блок, ноги на y=0, перед смотрит в -Z,
правая рука — в -X, как в шаблонах Blockbench). Текстура раскладывается box-UV автоматически,
каждый куб красится своим материалом; светящиеся кубы попадают и в карту `_glow`.

Плотность текстуры — S пикселей PNG на пиксель модели (S=2 → 32 px на блок, как договорено в каталоге).
"""
import json
import math
import os
import random

import numpy as np
from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
ASSETS = os.path.join(ROOT, "src/main/resources/assets/warpbound")


def clamp(v):
    return max(0, min(255, int(v)))


def mix(a, b, t):
    return tuple(clamp(x + (y - x) * t) for x, y in zip(a, b))


def shade(c, f):
    return tuple(clamp(v * f) for v in c[:3])


# ------------------------------------------------------------------ геометрия

class Cube:
    def __init__(self, origin, size, mat, inflate=0.0, rotation=None, pivot=None, deco=None, glow=None, mirror=False,
                 tint=None, face_mat=None):
        # размеры кратны 1/S пикселя модели: при S=4 можно детали в полпикселя и четверть
        self.origin, self.size, self.mat = list(origin), [s if s % 1 else int(s) for s in size], mat
        # tint: {"east": 0.5} — затемнить/осветлить грань (изнанка капюшона, тень под пелериной)
        self.tint = tint or {}
        # face_mat: {"south": "robe_in"} — другой материал для отдельной грани
        self.face_mat = face_mat or {}
        self.inflate, self.rotation, self.pivot = inflate, rotation, pivot
        # deco: {"north": fn(face, S, pal)} — дорисовка грани (лицо, знак, руны)
        self.deco = deco or {}
        # glow: None | "all" | fn(face, S, pal) -> маска для карты свечения
        self.glow = glow
        self.mirror = mirror
        self.uv = None

    def uv_size(self):
        w, h, d = self.size
        return 2 * (w + d), d + h

    def json(self):
        j = {"origin": [round(v, 3) for v in self.origin], "size": self.size, "uv": self.uv}
        if self.inflate:
            j["inflate"] = self.inflate
        if self.rotation:
            j["rotation"] = self.rotation
            j["pivot"] = self.pivot
        if self.mirror:
            j["mirror"] = True
        return j


class Bone:
    def __init__(self, model, name, pivot, parent=None, rotation=None):
        self.model, self.name, self.pivot, self.parent, self.rotation = model, name, list(pivot), parent, rotation
        self.cubes = []

    def cube(self, origin, size, mat, **kw):
        c = Cube(origin, size, mat, **kw)
        self.cubes.append(c)
        return c

    def json(self):
        j = {"name": self.name, "pivot": self.pivot}
        if self.parent:
            j["parent"] = self.parent
        if self.rotation:
            j["rotation"] = self.rotation
        if self.cubes:
            j["cubes"] = [c.json() for c in self.cubes]
        return j


class Model:
    def __init__(self, name, S=2, atlas_w=128):
        self.name, self.S, self.atlas_w = name, S, atlas_w
        self.bones = []

    def bone(self, name, pivot, parent=None, rotation=None):
        b = Bone(self, name, pivot, parent, rotation)
        self.bones.append(b)
        return b

    def cubes(self):
        return [c for b in self.bones for c in b.cubes]

    def pack(self):
        """Полочная упаковка box-UV развёрток; возвращает размер атласа в пикселях модели."""
        cubes = sorted(self.cubes(), key=lambda c: -c.uv_size()[1])
        x = y = shelf = 0
        for c in cubes:
            w, h = c.uv_size()
            if w > self.atlas_w:
                raise ValueError(f"{self.name}: куб {c.size} шире атласа")
            if x + w > self.atlas_w:
                x, y, shelf = 0, y + shelf, 0
            c.uv = [x, y]
            x += w
            shelf = max(shelf, h)
        total = y + shelf
        th = 16
        while th < total:
            th *= 2
        return self.atlas_w, th

    def write_geo(self, tw, th, path_name=None, kind="entity"):
        top = max(c.origin[1] + c.size[1] for c in self.cubes())
        width = max(max(abs(c.origin[0]), abs(c.origin[0] + c.size[0]), abs(c.origin[2]), abs(c.origin[2] + c.size[2]))
                    for c in self.cubes())
        geo = {
            "format_version": "1.12.0",
            "minecraft:geometry": [{
                "description": {
                    "identifier": f"geometry.warpbound.{self.name}",
                    "texture_width": tw, "texture_height": th,
                    "visible_bounds_width": math.ceil(width * 2 / 16) + 2,
                    "visible_bounds_height": math.ceil(top / 16) + 2,
                    "visible_bounds_offset": [0, top / 32, 0],
                },
                "bones": [b.json() for b in self.bones],
            }],
        }
        write_json(geo, "geo", kind, (path_name or self.name) + ".geo.json")

    def paint(self, palette, seed):
        """Рисует базовую текстуру и карту свечения для палитры."""
        tw, th = self.atlas_size
        S = self.S
        base = np.zeros((th * S, tw * S, 4), np.uint8)
        glow = np.zeros_like(base)
        rng = random.Random(seed)
        for c in self.cubes():
            for face, (fx, fy, fw, fh) in faces(c):
                if fw == 0 or fh == 0:
                    continue
                x0, y0 = int(round(fx * S)), int(round(fy * S))
                x1, y1 = int(round((fx + fw) * S)), int(round((fy + fh) * S))
                if x1 <= x0 or y1 <= y0:
                    continue
                region = base[y0:y1, x0:x1]
                mat = c.face_mat.get(face, c.mat)
                MATERIALS[mat](region, face, palette, rng)
                if not mat.startswith("hd_"):  # у hd-материалов своя фаска
                    edge(region, face)
                if face in c.tint:
                    region[..., :3] = np.clip(region[..., :3] * c.tint[face], 0, 255).astype(np.uint8)
                if face in c.deco:
                    c.deco[face](region, S, palette)
                if c.glow:
                    g = glow[y0:y1, x0:x1]
                    if c.glow == "all":
                        g[...] = region
                        g[..., 3] = 255
                    else:
                        c.glow(g, region, face, S, palette)
        return Image.fromarray(base, "RGBA"), Image.fromarray(glow, "RGBA")

    def build(self, kind="entity"):
        """kind: entity — geo/entity, block — geo/block (машины с моделью GeckoLib)."""
        self.atlas_size = self.pack()
        self.write_geo(*self.atlas_size, kind=kind)


def faces(c):
    """Грани box-UV: (имя, x, y, ширина, высота) в пикселях модели."""
    u, v = c.uv
    w, h, d = c.size
    return [
        ("up", (u + d, v, w, d)),
        ("down", (u + d + w, v, w, d)),
        ("east", (u, v + d, d, h)),
        ("north", (u + d, v + d, w, h)),
        ("west", (u + d + w, v + d, d, h)),
        ("south", (u + 2 * d + w, v + d, w, h)),
    ]


def edge(region, face):
    """Тёмная кайма по краю грани — объём без настоящего освещения."""
    h, w = region.shape[:2]
    if h < 3 or w < 3:
        return
    k = 0.72 if face != "up" else 0.85
    for sl in (region[0, :], region[-1, :], region[:, 0], region[:, -1]):
        sl[..., :3] = (sl[..., :3] * k).astype(np.uint8)


# ------------------------------------------------------------------ материалы

def noise_fill(region, color, amp, rng, alpha=255):
    h, w = region.shape[:2]
    n = np.array([[rng.randint(-amp, amp) for _ in range(w)] for _ in range(h)])
    for i in range(3):
        region[..., i] = np.clip(color[i] + n, 0, 255)
    region[..., 3] = alpha


def face_light(face):
    return {"up": 1.12, "down": 0.7, "north": 1.0, "south": 0.88, "east": 0.93, "west": 0.93}[face]


def mat_cloth(key, folds=True, hem=None):
    def f(region, face, pal, rng):
        c = shade(pal[key], face_light(face))
        noise_fill(region, c, 6, rng)
        h, w = region.shape[:2]
        if folds and face not in ("up", "down"):
            for x in range(w):
                k = 0.86 + 0.14 * math.sin(x * 1.3 + rng.random() * 0.5)
                region[:, x, :3] = (region[:, x, :3] * k).astype(np.uint8)
        if hem and face not in ("up", "down") and h > 6:
            region[-3:, :, :3] = shade(pal[hem], face_light(face))
            region[-3, :, :3] = shade(pal[hem], 1.25)
    return f


def mat_rag(key):
    def f(region, face, pal, rng):
        c = shade(pal[key], face_light(face))
        noise_fill(region, c, 12, rng)
        h, w = region.shape[:2]
        # заплатки и потёки грязи
        for _ in range(max(1, w * h // 120)):
            x, y = rng.randrange(w), rng.randrange(h)
            pw, ph = rng.randint(2, 5), rng.randint(2, 5)
            region[y:y + ph, x:x + pw, :3] = shade(pal.get("patch", pal[key]), 0.8 + rng.random() * 0.3)
        if face not in ("up", "down") and h > 4:
            for x in range(w):
                if rng.random() < 0.3:
                    region[-rng.randint(1, 3):, x, 3] = 0  # рваный край
    return f


def mat_metal(key, rivets=True, panels=True):
    def f(region, face, pal, rng):
        c = shade(pal[key], face_light(face))
        noise_fill(region, c, 5, rng)
        h, w = region.shape[:2]
        if panels and w > 10 and h > 10:
            for x in range(0, w, 12):
                region[:, x, :3] = shade(c, 0.7)
            for y in range(0, h, 14):
                region[y, :, :3] = shade(c, 0.7)
        if rivets and w > 5 and h > 5:
            for (x, y) in ((2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3)):
                region[y, x, :3] = shade(c, 1.35)
        # царапины
        for _ in range(w * h // 60):
            x, y = rng.randrange(w), rng.randrange(h)
            region[y, x:x + rng.randint(1, 3), :3] = shade(c, 1.2)
    return f


def mat_brass(key="brass"):
    def f(region, face, pal, rng):
        c = shade(pal[key], face_light(face))
        noise_fill(region, c, 8, rng)
        h, w = region.shape[:2]
        if h > 2:
            region[1, :, :3] = shade(c, 1.3)
            region[-2, :, :3] = shade(c, 0.75)
    return f


def mat_skin(key, veins=None, mottle=10):
    def f(region, face, pal, rng):
        c = shade(pal[key], face_light(face))
        noise_fill(region, c, mottle, rng)
        h, w = region.shape[:2]
        if veins:
            vc = pal[veins]
            for _ in range(max(1, w * h // 90)):
                x, y = rng.randrange(w), rng.randrange(h)
                for _ in range(rng.randint(3, 7)):
                    if 0 <= x < w and 0 <= y < h:
                        region[y, x, :3] = vc
                    x += rng.choice((-1, 0, 1))
                    y += 1
    return f


def mat_flat(key, amp=4):
    def f(region, face, pal, rng):
        noise_fill(region, shade(pal[key], face_light(face)), amp, rng)
    return f


def mat_glow(key):
    def f(region, face, pal, rng):
        h, w = region.shape[:2]
        c = pal[key]
        noise_fill(region, c, 10, rng)
        cy, cx = (h - 1) / 2, (w - 1) / 2
        for y in range(h):
            for x in range(w):
                d = math.hypot((x - cx) / max(1, w / 2), (y - cy) / max(1, h / 2))
                region[y, x, :3] = mix(mix(c, (255, 255, 255), 0.55), c, min(1, d))
    return f


def mat_blade(key):
    def f(region, face, pal, rng):
        c = shade(pal[key], face_light(face))
        noise_fill(region, c, 6, rng)
        h, w = region.shape[:2]
        if face in ("north", "south", "east", "west") and w > 2:
            region[:, 0, :3] = shade(c, 1.6)
            region[:, -1, :3] = shade(c, 1.6)
    return f


MATERIALS = {
    "robe": mat_cloth("robe", hem="trim"),
    "robe_plain": mat_cloth("robe"),
    "sleeve": mat_cloth("robe", folds=False),
    "hood": mat_cloth("hood"),
    "rag": mat_rag("rag"),
    "rag2": mat_rag("rag2"),
    "leather": mat_flat("leather", 7),
    "metal": mat_metal("metal"),
    "metal_plain": mat_metal("metal", rivets=False, panels=False),
    "dark": mat_metal("dark"),
    "dark_plain": mat_metal("dark", rivets=False, panels=False),
    "brass": mat_brass(),
    "cable": mat_flat("cable", 10),
    "skin": mat_skin("skin"),
    "flesh": mat_skin("flesh", veins="vein"),
    "horn": mat_skin("horn", mottle=14),
    "claw": mat_flat("claw", 8),
    "blade": mat_blade("blade"),
    "face": mat_flat("face", 3),
    "glow": mat_glow("glow"),
    "glow2": mat_glow("glow2"),
    "interior": mat_metal("interior", rivets=False),
    "hull": mat_metal("hull"),
    "brick": None,  # заполняется ниже
    "grate": None,
    "screen": mat_flat("screen", 3),
    "red": mat_cloth("red", folds=False),
}


def mat_brick(region, face, pal, rng):
    """Шамотная кладка горна: кирпичи со смещением рядов и тёмными швами."""
    c = shade(pal["brick"], face_light(face))
    noise_fill(region, c, 10, rng)
    h, w = region.shape[:2]
    bh, bw = 6, 12
    for y in range(0, h, bh):
        region[y, :, :3] = shade(c, 0.55)
        off = (y // bh % 2) * (bw // 2)
        for x in range(off, w, bw):
            region[y:y + bh, x, :3] = shade(c, 0.55)


def mat_grate(region, face, pal, rng):
    """Решётка: тёмные прорези в металле."""
    c = shade(pal["dark"], face_light(face))
    noise_fill(region, c, 4, rng)
    h, w = region.shape[:2]
    for y in range(1, h - 1, 3):
        region[y, 1:-1, :3] = shade(c, 0.4)


MATERIALS["brick"] = mat_brick
MATERIALS["grate"] = mat_grate


# ------------------------------------------------------------------ рисунки на гранях

def draw_rect(region, S, x, y, w, h, c, alpha=255):
    region[int(y * S):int((y + h) * S), int(x * S):int((x + w) * S), :3] = c[:3]
    region[int(y * S):int((y + h) * S), int(x * S):int((x + w) * S), 3] = alpha


def star8(region, cx, cy, r, c):
    """Восьмиконечная звезда Хаоса: восемь лучей-стрелок из центра."""
    h, w = region.shape[:2]
    for k in range(8):
        a = k * math.pi / 4
        for t in range(int(r) + 1):
            x, y = int(round(cx + math.cos(a) * t)), int(round(cy + math.sin(a) * t))
            if 0 <= x < w and 0 <= y < h:
                region[y, x, :3] = c
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            x, y = int(cx) + dx, int(cy) + dy
            if 0 <= x < w and 0 <= y < h:
                region[y, x, :3] = c


def cog(region, cx, cy, r, c):
    """Шестерня Механикус: кольцо с зубцами."""
    h, w = region.shape[:2]
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - cx, y - cy)
            a = math.atan2(y - cy, x - cx)
            tooth = r + (1.5 if math.cos(a * 8) > 0.3 else 0)
            if r * 0.45 < d <= tooth:
                region[y, x, :3] = c


# ------------------------------------------------------------------ анимации

def track(fn, length, steps=16):
    """Ключи из функции fn(t ∈ [0,1)) → [x, y, z]; последняя точка повторяет первую — цикл без шва."""
    out = {}
    for i in range(steps + 1):
        t = i / steps
        out[f"{t * length:.4f}".rstrip("0").rstrip(".") or "0"] = [round(v, 2) for v in fn(t % 1.0 if i < steps else 0.0)]
    return out


def keys(points):
    """Ключи из списка (время, [x, y, z])."""
    return {(f"{t:.4f}".rstrip("0").rstrip(".") or "0"): v for t, v in points}


def sin(t, phase=0.0):
    return math.sin((t + phase) * 2 * math.pi)


def write_animations(name, anims, kind="entity"):
    """anims: {имя: {"length": с, "loop": True | "hold_on_last_frame" | False, "bones": {кость: {канал: ключи}}}}"""
    out = {"format_version": "1.8.0", "animations": {}}
    for an, a in anims.items():
        entry = {"animation_length": a["length"], "bones": {}}
        if a.get("loop"):
            entry["loop"] = a["loop"]
        for bone, chans in a["bones"].items():
            entry["bones"][bone] = chans
        out["animations"][an] = entry
    write_json(out, "animations", kind, name + ".animation.json")


def write_json(obj, *path):
    p = os.path.join(ASSETS, *path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    print("  ", os.path.relpath(p, ROOT))


def save_png(img, *path):
    p = os.path.join(ASSETS, "textures", *path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    img.save(p)
    print("  ", os.path.relpath(p, ROOT))


# ------------------------------------------------------------------ модели блоков (Java Block Model)

def write_block_model(m, name, texture, parent="minecraft:block/block", ao=True):
    """
    Пишет models/block/<name>.json из кубов модели m (координаты 0..16, перед — север).
    UV берутся из той же box-развёртки, что и у сущностей: атлас квадратный, 16 единиц UV = вся текстура.
    Поворот куба — block_rot = (ось, угол ±22.5/45, центр).
    """
    tw, th = m.atlas_size
    k = 16 / tw
    elements = []
    for c in m.cubes():
        x, y, z = c.origin
        w, h, d = c.size
        el = {"from": [x, y, z], "to": [x + w, y + h, z + d], "faces": {}}
        for face, (fx, fy, fw, fh) in faces(c):
            if fw == 0 or fh == 0:
                continue
            el["faces"][face] = {"uv": [round(fx * k, 4), round(fy * k, 4), round((fx + fw) * k, 4), round((fy + fh) * k, 4)],
                                 "texture": "#all"}
        rot = getattr(c, "block_rot", None)
        if rot:
            axis, angle, origin = rot
            el["rotation"] = {"angle": angle, "axis": axis, "origin": origin}
        if getattr(c, "shade", True) is False:
            el["shade"] = False
        elements.append(el)
    tex = f"warpbound:block/{texture}"
    model = {"parent": parent, "textures": {"all": tex, "particle": tex}, "elements": elements}
    if not ao:
        model["ambientocclusion"] = False
    write_json(model, "models", "block", name + ".json")
