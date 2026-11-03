#!/usr/bin/env python3
"""
Текстуры прометиевого выхода и JSON генерации руд в мире.

    python3 tools/blocks/gen_ores.py

Сами блоки руд и битумного сланца — в tools/blocks/gen_block_set.py. Здесь то, что туда не укладывается:
анимированная лужа promethium_seep (блок со своим классом) и worldgen: серная руда, селитра, выход прометия.
"""
import json
import math
import os
import random

from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
A = os.path.join(ROOT, "src/main/resources/assets/warpbound")
D = os.path.join(ROOT, "src/main/resources/data/warpbound")
N = 32
FRAMES = 12


def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)


# ---------------------------------------------------------------- лужа: густой синий прометий, по нему ползут светлые разводы


def seep_frames():
    rng = random.Random(4711)
    img = Image.new("RGBA", (N, N * FRAMES))
    px = img.load()
    waves = [(rng.uniform(0, 2 * math.pi), rng.uniform(0, 2 * math.pi), rng.choice((1, 2)), rng.choice((1, 2))) for _ in range(4)]
    grain = [[rng.uniform(-0.04, 0.04) for _ in range(N)] for _ in range(N)]
    for f in range(FRAMES):
        t = f / FRAMES
        for y in range(N):
            for x in range(N):
                v = 0.0
                for pa, pb, kx, ky in waves:
                    v += math.sin(2 * math.pi * (kx * x / N + ky * y / N + t) + pa) * math.cos(2 * math.pi * (ky * x / N - kx * y / N) + pb)
                v = v / 4 + grain[y][x]
                if v > 0.5:
                    c = (24, 44, 84)
                elif v > 0.25:
                    c = (17, 28, 56)
                elif v > -0.2:
                    c = (12, 17, 34)
                else:
                    c = (9, 11, 22)
                px[x, y + f * N] = (*c, 255)
    return img


# ---------------------------------------------------------------- трещина: камень в битуме, по разлому течёт синий прометий


def shale(rng):
    """Тёмный камень с зернистостью: общий для всех кадров."""
    g = []
    for y in range(N):
        row = []
        for x in range(N):
            v = 34 + rng.randrange(-5, 6) + (6 if (x // 5 + y // 4) % 3 == 0 else 0)
            row.append((v, v - 1, v + 3))
        g.append(row)
    return g


def crack_top():
    rng = random.Random(90210)
    base = shale(rng)
    # ломаная от края до края и короткое ответвление
    cy = 15.0
    path = []
    for x in range(N):
        cy += rng.uniform(-1.3, 1.3)
        cy = max(6.0, min(25.0, cy))
        path.append((x, cy, 1.1 + 2.2 * math.sin(math.pi * x / N) + rng.uniform(-0.4, 0.4)))
    bx, by = 12, path[12][1]
    branch = []
    for i in range(12):
        bx += 1
        by += 1.1 + rng.uniform(-0.4, 0.4)
        if by < N:
            branch.append((bx, by, 1.0))
    img = Image.new("RGBA", (N, N * FRAMES))
    px = img.load()
    for f in range(FRAMES):
        t = f / FRAMES
        for y in range(N):
            for x in range(N):
                px[x, y + f * N] = (*base[y][x], 255)
        for sx, sy, w in path + branch:
            for y in range(N):
                d = abs(y - sy)
                if d < w + 2.4:
                    # край разлома темнее, затем синий ореол и текущая середина
                    flow = 0.5 + 0.5 * math.sin(2 * math.pi * (sx / 11 - t))
                    if d < w * 0.45:
                        c = (92, 160, 225) if flow > 0.72 else (48, 112, 196)
                    elif d < w:
                        c = (24, 70, 150)
                    elif d < w + 1.1:
                        c = (10, 10, 14)
                    else:
                        o = base[y][sx]
                        c = (o[0] // 2 + 4, o[1] // 2 + 8, o[2] // 2 + 22)
                    old = px[sx, y + f * N]
                    if sum(c) >= sum(old[:3]) or d < w + 1.1:
                        px[sx, y + f * N] = (*c, 255)
    return img


def crack_side():
    rng = random.Random(4242)
    base = shale(rng)
    drips = [(x, rng.randrange(9, 26), rng.randrange(FRAMES)) for x in (4, 9, 15, 21, 27)]
    img = Image.new("RGBA", (N, N * FRAMES))
    px = img.load()
    for f in range(FRAMES):
        for y in range(N):
            for x in range(N):
                px[x, y + f * N] = (*base[y][x], 255)
        for x in range(N):
            top = 2 + (x * 7 % 3)
            for y in range(top):
                px[x, y + f * N] = (24, 70, 150, 255)
        for x, length, start in drips:
            head = int(((f - start) % FRAMES) / FRAMES * length)
            for y in range(2, length):
                c = (70, 130, 205) if abs(y - head) < 2 else (22, 62, 134)
                px[x, y + f * N] = (*c, 255)
                if y < length - 3:
                    px[x + 1, y + f * N] = (16, 40, 90, 255)
    return img


seep_frames().save(os.path.join(A, "textures/block/promethium_seep.png"))
dump(f"{A}/textures/block/promethium_seep.png.mcmeta", {"animation": {"frametime": 16, "interpolate": True}})
dump(f"{A}/blockstates/promethium_seep.json", {"variants": {"": {"model": "warpbound:block/promethium_seep"}}})
dump(f"{A}/models/block/promethium_seep.json", {
    "ambientocclusion": False,
    "textures": {"particle": "warpbound:block/promethium_seep", "tar": "warpbound:block/promethium_seep"},
    "elements": [{"from": [0, 0, 0], "to": [16, 1, 16], "faces": {
        "up": {"texture": "#tar", "uv": [0, 0, 16, 16]},
        "north": {"texture": "#tar", "uv": [0, 15, 16, 16], "cullface": "north"},
        "south": {"texture": "#tar", "uv": [0, 15, 16, 16], "cullface": "south"},
        "west": {"texture": "#tar", "uv": [0, 15, 16, 16], "cullface": "west"},
        "east": {"texture": "#tar", "uv": [0, 15, 16, 16], "cullface": "east"},
        "down": {"texture": "#tar", "uv": [0, 0, 16, 16], "cullface": "down"}}}]})
crack_top().save(os.path.join(A, "textures/block/promethium_fissure_top.png"))
crack_side().save(os.path.join(A, "textures/block/promethium_fissure_side.png"))
for n in ("top", "side"):
    dump(f"{A}/textures/block/promethium_fissure_{n}.png.mcmeta", {"animation": {"frametime": 10, "interpolate": True}})
# четыре поворота: соседние блоки трещины не выглядят одинаковыми
dump(f"{A}/blockstates/promethium_fissure.json", {"variants": {"": [{"model": "warpbound:block/promethium_fissure", "y": y} for y in (0, 90, 180, 270)]}})
dump(f"{A}/models/block/promethium_fissure.json", {"parent": "minecraft:block/cube_bottom_top", "textures": {
    "top": "warpbound:block/promethium_fissure_top", "side": "warpbound:block/promethium_fissure_side", "bottom": "warpbound:block/bitumen_shale"}})
dump(f"{A}/models/item/promethium_fissure.json", {"parent": "warpbound:block/promethium_fissure"})
dump(f"{ROOT}/src/main/resources/data/warpbound/loot_table/blocks/promethium_fissure.json", {"type": "minecraft:block", "pools": [{"rolls": 1, "entries": [
    {"type": "minecraft:item", "name": "warpbound:bitumen_shale"}], "conditions": [{"condition": "minecraft:survives_explosion"}]}]})
for rel in ("mineable/pickaxe.json",):
    path = os.path.join(ROOT, "src/main/resources/data/minecraft/tags/block", rel)
    tag = json.load(open(path, encoding="utf-8"))
    if "warpbound:promethium_fissure" not in tag["values"]:
        tag["values"].append("warpbound:promethium_fissure")
        dump(path, tag)
dump(f"{A}/models/item/promethium_seep.json", {"parent": "minecraft:item/generated", "textures": {"layer0": "warpbound:item/promethium_seep"}})
dump(f"{ROOT}/src/main/resources/data/warpbound/loot_table/blocks/promethium_seep.json", {"type": "minecraft:block", "pools": []})


# ---------------------------------------------------------------- генерация


def ore_feature(name, size, stone_block, deep_block, discard=0.0):
    dump(f"{D}/worldgen/configured_feature/{name}.json", {"type": "minecraft:ore", "config": {
        "size": size, "discard_chance_on_air_exposure": discard, "targets": [
            {"target": {"predicate_type": "minecraft:tag_match", "tag": "minecraft:stone_ore_replaceables"},
             "state": {"Name": f"warpbound:{stone_block}"}},
            {"target": {"predicate_type": "minecraft:tag_match", "tag": "minecraft:deepslate_ore_replaceables"},
             "state": {"Name": f"warpbound:{deep_block}"}}]}})


def ore_placed(name, count, lo, hi, kind="trapezoid"):
    dump(f"{D}/worldgen/placed_feature/{name}.json", {"feature": f"warpbound:{name}", "placement": [
        {"type": "minecraft:count", "count": count},
        {"type": "minecraft:in_square"},
        {"type": "minecraft:height_range", "height": {"type": f"minecraft:{kind}", "min_inclusive": {"absolute": lo}, "max_inclusive": {"absolute": hi}}},
        {"type": "minecraft:biome"}]})


# Сера «у лавы, глубоко»: только глубокие слои. Селитра — в известняке и верхних пещерах: у открытого воздуха чаще (наросты)
ore_feature("sulfur_ore", 9, "sulfur_ore", "deepslate_sulfur_ore")
ore_placed("sulfur_ore", 6, -60, -8, "uniform")
ore_feature("saltpeter_ore", 7, "saltpeter_ore", "saltpeter_ore")
ore_placed("saltpeter_ore", 7, 0, 90)

# Выход прометия: каждый чанк один раз, дальше решает сам класс по полю залежей
dump(f"{D}/worldgen/configured_feature/promethium_seep.json", {"type": "warpbound:promethium_seep", "config": {}})
dump(f"{D}/worldgen/placed_feature/promethium_seep.json", {"feature": "warpbound:promethium_seep", "placement": [
    {"type": "minecraft:in_square"}, {"type": "minecraft:heightmap", "heightmap": "OCEAN_FLOOR_WG"}]})
# Серу можно выплавить и без дробильни: до главы 4 её мало кому надо, зато не тупик
for kind, time in (("smelting", 200), ("blasting", 100)):
    dump(f"{D}/recipe/sulfur_from_{kind}.json", {"type": f"minecraft:{kind}", "category": "misc", "ingredient": {"item": "warpbound:raw_sulfur"},
                                                  "result": {"id": "warpbound:sulfur"}, "experience": 0.2, "cookingtime": time})
print("руды и выход прометия готовы")
