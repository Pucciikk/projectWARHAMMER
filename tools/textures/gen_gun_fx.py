#!/usr/bin/env python3
"""
Эффекты оружия: вспышки у дула, лазерный импульс, огонь и след болта, текстура снаряда, гильза.

    python3 tools/textures/gen_gun_fx.py

Вспышка рисуется аддитивно, поэтому чёрный фон в текстуре просто не виден.
"""
import json
import math
import os
import random

import numpy as np
from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
A = os.path.join(ROOT, "src/main/resources/assets/warpbound")
EFFECT = os.path.join(A, "textures/effect")
os.makedirs(EFFECT, exist_ok=True)
os.makedirs(os.path.join(A, "textures/entity"), exist_ok=True)
os.makedirs(os.path.join(A, "textures/particle"), exist_ok=True)


def flash(path, seed, inner, outer, spikes, size=96):
    """Звезда: лучи разной длины вокруг горячей сердцевины."""
    rng = random.Random(seed)
    lengths = [rng.uniform(0.55, 1.0) for _ in range(spikes)]
    phase = [rng.uniform(0, 2 * math.pi) for _ in range(spikes)]
    yy, xx = np.mgrid[0:size, 0:size]
    dx, dy = (xx - size / 2 + 0.5) / (size / 2), (yy - size / 2 + 0.5) / (size / 2)
    r = np.sqrt(dx * dx + dy * dy)
    a = np.arctan2(dy, dx)
    shape = np.zeros_like(r)
    for L, p in zip(lengths, phase):
        d = np.abs(np.angle(np.exp(1j * (a - p))))
        spike = np.clip(1 - d * (spikes * 1.1) / np.maximum(1 - r / L, 0.03) / 3.0, 0, 1) * np.clip(1 - r / L, 0, 1)
        shape = np.maximum(shape, spike)
    core = np.clip(1 - r / 0.32, 0, 1) ** 1.3
    glow = np.clip(1 - r, 0, 1) ** 2.4 * 0.55
    v = np.clip(shape + core + glow, 0, 1)
    rgb = np.zeros((size, size, 3))
    for c in range(3):
        rgb[..., c] = (outer[c] + (inner[c] - outer[c]) * np.clip(v * 1.2 - 0.15, 0, 1) ** 1.5) * v
    out = np.dstack((rgb, np.clip(v * 255, 0, 255)))
    Image.fromarray(out.clip(0, 255).astype(np.uint8), "RGBA").save(path)


for i in range(2):
    flash(os.path.join(EFFECT, f"flash_las_{i}.png"), 10 + i, (255, 248, 210), (255, 170, 20), 7 + i)
    flash(os.path.join(EFFECT, f"flash_bolt_{i}.png"), 20 + i, (255, 245, 205), (255, 130, 25), 9 + i)


def ribbon(path, w, h, across, along):
    """Текстура ленты: across — поперечная яркость, along — вдоль (0 у хвоста, 1 у головы)."""
    yy, xx = np.mgrid[0:h, 0:w]
    u = (xx + 0.5) / w
    v = (yy + 0.5) / h
    val = across(np.abs(v - 0.5) * 2) * along(u)
    out = np.dstack((val * 255, val * 255, val * 255, val * 255))
    Image.fromarray(out.clip(0, 255).astype(np.uint8), "RGBA").save(path)


ribbon(os.path.join(EFFECT, "las_bolt.png"), 32, 16, lambda d: np.clip(1 - d, 0, 1) ** 1.4, lambda u: np.clip(u * 1.2, 0, 1) ** 0.6)
ribbon(os.path.join(EFFECT, "bolt_flame.png"), 32, 16, lambda d: np.clip(1 - d, 0, 1) ** 1.1, lambda u: np.clip(u, 0, 1) ** 1.6)
ribbon(os.path.join(EFFECT, "bolt_trail.png"), 64, 16, lambda d: np.clip(1 - d, 0, 1) ** 1.8, lambda u: np.clip(u, 0, 1) ** 2.2)

Image.new("RGBA", (4, 4), (255, 255, 255, 255)).save(os.path.join(EFFECT, "white.png"))

# корпус болта вдоль v: v=0 нос, v=1 сопло. Стальной колпачок, красный поясок, латунный корпус с проточками, тёмная хвостовая часть
tex = Image.new("RGBA", (16, 64))
px = tex.load()
for y in range(64):
    k = y / 63
    for x in range(16):
        n = random.Random(x * 31 + y * 7).randint(-5, 5)
        if k < 0.1:
            base = (70, 74, 82)
        elif k < 0.3:
            base = (168, 174, 184)
        elif k < 0.36:
            base = (150, 26, 22)
        elif k < 0.8:
            base = (196, 150, 66)
            if abs(k - 0.46) < 0.012 or abs(k - 0.7) < 0.012:
                base = (112, 80, 30)
            elif 0.5 < k < 0.66 and x % 4 == 0:
                base = (164, 122, 50)
        else:
            base = (54, 54, 60)
        px[x, y] = (base[0] + n, base[1] + n, base[2] + n, 255)
tex.save(os.path.join(A, "textures/entity/bolt_round.png"))

# гильза: латунный цилиндрик, 8×8
casing = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
p = casing.load()
for y in range(1, 7):
    for x in range(2, 6):
        p[x, y] = {2: (232, 198, 110, 255), 3: (214, 170, 84, 255), 4: (178, 134, 56, 255), 5: (120, 86, 34, 255)}[x]
for x in range(2, 6):
    p[x, 6] = (92, 66, 26, 255)
    p[x, 1] = (60, 44, 20, 255)
casing.save(os.path.join(A, "textures/particle/gun_casing.png"))
with open(os.path.join(A, "particles/gun_casing.json"), "w", encoding="utf-8") as f:
    json.dump({"textures": ["warpbound:gun_casing"]}, f)

# ---------------------------------------------------------------- sounds.json: добавляем записи оружия
SOUNDS = {
    "gun.las_fire": ([f"las_fire_{i}" for i in range(6)], 48),
    "gun.bolter_fire": ([f"bolter_fire_{i}" for i in range(6)], 80),
    "gun.bolt_explode": (["bolt_explode_0", "bolt_explode_1", "bolt_explode_2"], 56),
    "gun.casing": (["casing_0", "casing_1", "casing_2"], 16),
}
SOUNDS["gun.chainsword_engine"] = (["chainsword_engine"], 24)
SOUNDS["gun.chainsword_bite"] = (["chainsword_bite_0", "chainsword_bite_1", "chainsword_bite_2"], 24)
SOUNDS["gun.chainsword_swing"] = ([f"chainsword_swing_{i}" for i in range(4)], 16)
SOUNDS["gun.chainsword_start"] = (["chainsword_start_0", "chainsword_start_1"], 16)
SOUNDS["gun.las_hit"] = ([f"las_hit_{i}" for i in range(4)], 16)
for name in ("las_charge", "las_cell_out", "las_cell_in", "las_lever", "bolter_mag_out", "bolter_mag_in", "bolter_rack_back", "bolter_rack_fwd", "gun_dry", "gun_raise", "hit_marker"):
    SOUNDS["gun." + name] = ([name], 16)
path = os.path.join(A, "sounds.json")
data = json.load(open(path, encoding="utf-8"))
for name, (files, dist) in SOUNDS.items():
    data[name] = {"sounds": [{"name": f"warpbound:gun/{f}", "attenuation_distance": dist} for f in files]}
# дредноут: файлы в sounds/dread, длинные гул и мотор читаются потоком
DREAD = {"dread.step": ([f"dread_step_{i}" for i in range(6)], 32), "dread.foley": ([f"dread_foley_{i}" for i in range(6)], 20),
         "dread.servo": ([f"dread_servo_{i}" for i in range(4)], 16), "dread.stomp": ([f"dread_stomp_{i}" for i in range(3)], 48),
         "dread.fire": ([f"dread_fire_{i}" for i in range(6)], 96), "dread.punch": ([f"dread_punch_{i}" for i in range(3)], 32),
         "dread.fall": (["dread_fall"], 56), "dread.idle": (["dread_idle"], 18)}
for name, (files, dist) in DREAD.items():
    data[name] = {"sounds": [{"name": f"warpbound:dread/{f}", "attenuation_distance": dist, **({"stream": True} if name == "dread.idle" else {})} for f in files]}
data["gun.chainsword_engine"]["sounds"][0]["stream"] = True
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=1, ensure_ascii=False)

# ---------------------------------------------------------------- данные и модели предметов
D = os.path.join(ROOT, "src/main/resources/data/warpbound/gun")
os.makedirs(D, exist_ok=True)
GUNS = {
    "lasgun": dict(damage=6.0, speed=9.0, life_ticks=24, spread_hip=1.6, spread_aim=0.25, head=1.5, knockback=0.05),
    "bolter_guard": dict(damage=9.0, blast_damage=5.0, blast_radius=2.0, speed=6.5, speed_start=2.2, accel=1.55, life_ticks=40, spread_hip=2.4, spread_aim=0.5, head=1.5, knockback=0.35),
    "bolter_astartes": dict(damage=14.0, blast_damage=7.0, blast_radius=2.4, speed=7.5, speed_start=2.5, accel=1.55, life_ticks=40, spread_hip=2.0, spread_aim=0.35, head=1.5, knockback=0.45),
}
for name, spec in GUNS.items():
    with open(os.path.join(D, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=1)
# ось ствола — -Z модели. В руке: дуло вперёд от игрока; в инвентаре: боком, как на витрине
DISPLAY = {
    "thirdperson_righthand": {"rotation": [0, 0, 0], "translation": [-0.5, 3.5, -4.5], "scale": [0.72, 0.72, 0.72]},
    "thirdperson_lefthand": {"rotation": [0, 0, 0], "translation": [0.5, 3.5, -4.5], "scale": [0.72, 0.72, 0.72]},
    "firstperson_righthand": {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [0.5, 0.5, 0.5]},
    "firstperson_lefthand": {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [0.5, 0.5, 0.5]},
    "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.5, 0.5, 0.5]},
    "gui": {"rotation": [20, 112, 0], "translation": [0.8, 0.6, 0], "scale": [0.62, 0.62, 0.62]},
    "fixed": {"rotation": [0, 90, 0], "translation": [0, 0, 0], "scale": [0.8, 0.8, 0.8]},
    "head": {"rotation": [0, 0, 0], "translation": [0, 10, 0], "scale": [0.8, 0.8, 0.8]},
}
for name in GUNS:
    with open(os.path.join(A, "models/item", name + ".json"), "w", encoding="utf-8") as f:
        json.dump({"parent": "builtin/entity", "display": DISPLAY}, f, indent=1)
print("эффекты оружия готовы")
