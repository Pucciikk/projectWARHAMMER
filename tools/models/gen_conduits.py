#!/usr/bin/env python3
"""
Трубы, кабели и пневмопроводы: блоки с соединениями на шесть сторон, текстуры, рецепты, плюс рамка порта машины.

    python3 tools/models/gen_conduits.py
"""
import json
import os
import random

from PIL import Image, ImageDraw

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
A = os.path.join(ROOT, "src/main/resources/assets/warpbound")
D = os.path.join(ROOT, "src/main/resources/data")


def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1)


# название, основной цвет, цвет полосы и материал рецепта
KINDS = {
    "fluid_pipe": ((88, 92, 102), (176, 138, 58), "minecraft:iron_ingot"),
    "energy_cable": ((38, 36, 36), (206, 58, 40), "minecraft:copper_ingot"),
    "item_tube": ((150, 112, 50), (220, 180, 80), "warpbound:brass_ingot"),
}


def texture(name, base, band):
    """64 px на блок: потёртая труба с тёмными панелями и швом, фланец с болтами, бандаж с заклёпками."""
    rng = random.Random(name)
    img = Image.new("RGB", (64, 64), base)
    px = img.load()
    for y in range(64):
        for x in range(64):
            k = rng.randint(-9, 9) + (14 if y < 8 else -18 if y > 54 else 0) + (-10 if (x + y * 3) % 37 == 0 else 0)
            px[x, y] = tuple(max(0, min(255, c + k)) for c in base)
    d = ImageDraw.Draw(img)
    d.line([(0, 31), (63, 31)], fill=tuple(int(c * 0.45) for c in base))
    d.line([(0, 33), (63, 33)], fill=tuple(min(255, int(c * 1.3)) for c in base))
    for x in range(4, 64, 12):
        d.rectangle((x, 30, x + 1, 34), fill=tuple(int(c * 0.55) for c in base))
    os.makedirs(f"{A}/textures/block", exist_ok=True)
    img.save(f"{A}/textures/block/{name}.png")
    fl = Image.new("RGB", (64, 64), tuple(int(c * 0.6) for c in base))
    d = ImageDraw.Draw(fl)
    d.rectangle((0, 0, 63, 63), outline=tuple(int(c * 0.3) for c in base), width=3)
    d.rectangle((3, 3, 60, 6), fill=tuple(min(255, int(c * 1.0)) for c in base))
    for x, y in ((10, 10), (53, 10), (10, 53), (53, 53), (32, 10), (32, 53), (10, 32), (53, 32)):
        d.rectangle((x - 3, y - 3, x + 3, y + 3), fill=(110, 90, 48))
        d.rectangle((x - 2, y - 2, x + 1, y + 1), fill=(205, 170, 92))
    fl.save(f"{A}/textures/block/{name}_flange.png")
    bd = Image.new("RGB", (64, 64), band)
    d = ImageDraw.Draw(bd)
    d.rectangle((0, 0, 63, 8), fill=tuple(min(255, int(c * 1.35)) for c in band))
    d.rectangle((0, 55, 63, 63), fill=tuple(int(c * 0.55) for c in band))
    for x in range(6, 64, 13):
        d.rectangle((x, 28, x + 4, 32), fill=tuple(int(c * 0.5) for c in band))
    bd.save(f"{A}/textures/block/{name}_band.png")


def models(name):
    t = f"warpbound:block/{name}"
    f = f"warpbound:block/{name}_flange"
    b = f"warpbound:block/{name}_band"
    all_faces = lambda tex: {k: {"texture": tex, "uv": [0, 0, 16, 16]} for k in ("north", "south", "east", "west", "up", "down")}
    box = lambda a, c, tex: {"from": a, "to": c, "faces": all_faces(tex)}
    tx = {"particle": t, "body": t, "flange": f, "band": b}
    # узел без утолщения: на прямом участке труба ровная, чтобы шло длинное окно; на стыке блоков фланец с болтами
    dump(f"{A}/models/block/{name}_core.json", {"textures": tx, "elements": [box([5, 5, 5], [11, 11, 11], "#body")]})
    dump(f"{A}/models/block/{name}_arm.json", {"textures": tx, "elements": [
        box([5, 5, 0], [11, 11, 5], "#body"),
        box([3.6, 3.6, 0], [12.4, 12.4, 1.2], "#flange"),
        box([3.2, 7.2, 0.15], [3.6, 8.8, 1.05], "#band"), box([12.4, 7.2, 0.15], [12.8, 8.8, 1.05], "#band"),
        box([7.2, 3.2, 0.15], [8.8, 3.6, 1.05], "#band"), box([7.2, 12.4, 0.15], [8.8, 12.8, 1.05], "#band"),
    ]})
    rot = {"north": {}, "east": {"y": 90}, "south": {"y": 180}, "west": {"y": 270}, "up": {"x": 270}, "down": {"x": 90}}
    parts = [{"apply": {"model": f"warpbound:block/{name}_core"}}]
    for side, r in rot.items():
        parts.append({"when": {side: "true"}, "apply": {"model": f"warpbound:block/{name}_arm", "uvlock": False, **r}})
    dump(f"{A}/blockstates/{name}.json", {"multipart": parts})
    # предмет: прямой кусок трубы
    dump(f"{A}/models/item/{name}.json", {"parent": f"warpbound:block/{name}_arm", "display": {"gui": {"rotation": [30, 45, 0], "scale": [1.1, 1.1, 1.1]}}})


for name, (base, band, mat) in KINDS.items():
    texture(name, base, band)
    models(name)
    dump(f"{D}/warpbound/loot_table/blocks/{name}.json", {"type": "minecraft:block", "pools": [{"rolls": 1, "bonus_rolls": 0,
         "entries": [{"type": "minecraft:item", "name": f"warpbound:{name}"}], "conditions": [{"condition": "minecraft:survives_explosion"}]}],
         "random_sequence": f"warpbound:blocks/{name}"})
    dump(f"{D}/warpbound/recipe/{name}.json", {"type": "minecraft:crafting_shaped", "category": "building", "pattern": ["MMM", "   ", "MMM"],
         "key": {"M": {"item": mat}}, "result": {"id": f"warpbound:{name}", "count": 8}})



def pipe_window():
    """Рамка окна: латунь, скруглённое тёмное стекло; и поток — яркие струи и пузырьки, цвет даёт рендер."""
    w = Image.new("RGBA", (16, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(w)
    d.rectangle((0, 0, 15, 63), fill=(150, 112, 48, 255))
    d.rectangle((0, 0, 15, 1), fill=(212, 172, 92, 255))
    d.rectangle((0, 62, 15, 63), fill=(92, 66, 26, 255))
    d.rectangle((0, 0, 1, 63), fill=(190, 150, 74, 255))
    d.rectangle((14, 0, 15, 63), fill=(104, 76, 32, 255))
    d.rectangle((3, 3, 12, 60), fill=(14, 16, 20, 255))
    d.line([(4, 5), (4, 58)], fill=(44, 50, 58, 255))
    w.save(f"{A}/textures/block/pipe_window.png")
    rng = random.Random(3)
    f = Image.new("RGBA", (16, 64), (255, 255, 255, 215))
    px = f.load()
    for y in range(64):
        for x in range(16):
            band = 200 + int(45 * ((y % 16) / 16))
            edge = 0.72 if x < 2 or x > 13 else 1.0
            v = int(band * edge)
            px[x, y] = (v, v, v, 225)
    d = ImageDraw.Draw(f)
    for _ in range(9):
        x, y = rng.randint(2, 12), rng.randint(0, 60)
        d.ellipse((x, y, x + 2, y + 3), fill=(255, 255, 255, 255))
    f.save(f"{A}/textures/block/pipe_flow.png")


def machine_hatch():
    """Люк предметов: 64×64, области в PortRenderer. Сталь с заклёпками, стекло в раме, тёмное нутро, резина, цветная полоса."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, 31, 31), fill=(88, 92, 104, 255), outline=(44, 46, 54, 255))
    d.rectangle((1, 1, 30, 2), fill=(128, 132, 146, 255))
    for x, y in ((4, 4), (27, 4), (4, 27), (27, 27)):
        d.rectangle((x - 1, y - 1, x + 1, y + 1), fill=(196, 160, 86, 255))
    d.rectangle((32, 0, 63, 31), fill=(58, 60, 68, 255))
    d.rectangle((35, 3, 60, 28), fill=(150, 196, 214, 90))
    d.line([(38, 25), (48, 6)], fill=(220, 240, 250, 160))
    d.rectangle((0, 32, 31, 63), fill=(14, 14, 16, 255))
    d.line([(0, 62), (31, 62)], fill=(40, 40, 44, 255))
    d.rectangle((32, 32, 39, 63), fill=(24, 24, 26, 255))
    d.line([(33, 33), (33, 62)], fill=(52, 52, 56, 255))
    d.rectangle((40, 32, 63, 63), fill=(235, 235, 235, 255), outline=(60, 60, 62, 255))
    for x in range(42, 62, 6):
        d.line([(x, 62), (x + 8, 34)], fill=(60, 60, 62, 255), width=2)
    img.save(f"{A}/textures/block/machine_hatch.png")


pipe_window()
machine_hatch()
# рамка порта: белая с тёмной окантовкой, цвет задаёт рендер
img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rectangle((1, 1, 30, 30), fill=(40, 40, 44, 255), outline=(20, 20, 22, 255))
d.rectangle((4, 4, 27, 27), fill=(245, 245, 245, 255))
d.rectangle((10, 10, 21, 21), fill=(30, 30, 34, 255))
d.rectangle((13, 13, 18, 18), fill=(245, 245, 245, 255))
img.save(f"{A}/textures/block/machine_port.png")



def holder(name, body, band, elements):
    tex = {"particle": f"warpbound:block/{name}", "body": f"warpbound:block/{name}"}
    img = Image.new("RGB", (32, 32), body)
    px = img.load()
    rng = random.Random(name)
    for y in range(32):
        for x in range(32):
            k = rng.randint(-8, 8) + (8 if x < 3 else -10 if x > 28 else 0)
            px[x, y] = tuple(max(0, min(255, c + k)) for c in body)
    d = ImageDraw.Draw(img)
    for y in (4, 26):
        d.rectangle((0, y, 31, y + 2), fill=band)
    img.save(f"{A}/textures/block/{name}.png")
    all_faces = {k: {"texture": "#body", "uv": [0, 0, 16, 16]} for k in ("north", "south", "east", "west", "up", "down")}
    dump(f"{A}/models/block/{name}.json", {"textures": tex, "elements": [{"from": a, "to": b, "faces": all_faces} for a, b in elements]})
    dump(f"{A}/models/item/{name}.json", {"parent": f"warpbound:block/{name}"})
    dump(f"{A}/blockstates/{name}.json", {"variants": {"": {"model": f"warpbound:block/{name}"}}})
    dump(f"{D}/warpbound/loot_table/blocks/{name}.json", {"type": "minecraft:block", "pools": [{"rolls": 1, "bonus_rolls": 0,
         "entries": [{"type": "minecraft:item", "name": f"warpbound:{name}"}], "conditions": [{"condition": "minecraft:survives_explosion"}]}],
         "random_sequence": f"warpbound:blocks/{name}"})


holder("fluid_tank", (96, 100, 112), (176, 138, 58), [([1, 1, 1], [15, 15, 15]), ([0, 0, 0], [16, 2, 16]), ([0, 14, 0], [16, 16, 16]), ([6, 15, 6], [10, 16, 10])])
holder("flare_stack", (62, 44, 36), (200, 150, 60), [([2, 0, 2], [14, 3, 14]), ([5, 3, 5], [11, 14, 11]), ([4, 13, 4], [12, 16, 12])])
dump(f"{D}/warpbound/recipe/fluid_tank.json", {"type": "minecraft:crafting_shaped", "category": "building", "pattern": ["III", "IBI", "III"],
     "key": {"I": {"item": "minecraft:iron_ingot"}, "B": {"item": "minecraft:bucket"}}, "result": {"id": "warpbound:fluid_tank", "count": 1}})
dump(f"{D}/warpbound/recipe/flare_stack.json", {"type": "minecraft:crafting_shaped", "category": "building", "pattern": [" F ", "III", " I "],
     "key": {"I": {"item": "minecraft:iron_ingot"}, "F": {"item": "minecraft:flint_and_steel"}}, "result": {"id": "warpbound:flare_stack", "count": 1}})
dump(f"{D}/warpbound/recipe/herbs.json", {"type": "minecraft:crafting_shapeless", "category": "misc", "ingredients": [{"tag": "minecraft:flowers"}],
     "result": {"id": "warpbound:herbs", "count": 2}})



def conveyor():
    """Лента: текстура из восьми кадров со сдвигом и .mcmeta, поэтому движется сама и не требует кода."""
    rng = random.Random(7)
    belt = Image.new("RGB", (32, 32 * 8))
    base = Image.new("RGB", (32, 32), (34, 34, 38))
    b = base.load()
    for y in range(32):
        for x in range(32):
            b[x, y] = tuple(max(0, 34 + rng.randint(-5, 5) + (9 if 2 < x < 29 else -12)) for _ in range(3))
    d = ImageDraw.Draw(base)
    for y in (0, 16):
        d.rectangle((2, y, 29, y + 3), fill=(70, 70, 76))
    for f in range(8):
        shift = f * 4
        for y in range(32):
            for x in range(32):
                # лента едет в сторону верха текстуры (север модели)
                belt.putpixel((x, f * 32 + y), base.getpixel((x, (y + shift) % 32)))
    belt.save(f"{A}/textures/block/conveyor_belt.png")
    dump(f"{A}/textures/block/conveyor_belt.png.mcmeta", {"animation": {"frametime": 2}})
    side = Image.new("RGB", (32, 32), (78, 80, 90))
    d = ImageDraw.Draw(side)
    d.rectangle((0, 18, 31, 31), fill=(56, 58, 66))
    for k in range(0, 32, 8):
        d.rectangle((k + 2, 22, k + 5, 25), fill=(190, 150, 70))
    d.line([(0, 18), (31, 18)], fill=(190, 150, 70))
    side.save(f"{A}/textures/block/conveyor_side.png")
    t = {"particle": "warpbound:block/conveyor_side", "belt": "warpbound:block/conveyor_belt", "side": "warpbound:block/conveyor_side"}
    sf = {k: {"texture": "#side", "uv": [0, 0, 16, 16]} for k in ("north", "south", "east", "west", "up", "down")}
    dump(f"{A}/models/block/conveyor.json", {"textures": t, "elements": [
        {"from": [0, 2, 0], "to": [16, 5, 16], "faces": {**sf, "up": {"texture": "#belt", "uv": [0, 0, 16, 16]}}},
        {"from": [0, 0, 1], "to": [2, 7, 15], "faces": sf},
        {"from": [14, 0, 1], "to": [16, 7, 15], "faces": sf},
        {"from": [1, 0, 2], "to": [15, 2, 4], "faces": sf},
        {"from": [1, 0, 12], "to": [15, 2, 14], "faces": sf},
    ]})
    dump(f"{A}/models/item/conveyor.json", {"parent": "warpbound:block/conveyor"})
    dump(f"{A}/blockstates/conveyor.json", {"variants": {f"facing={k}": {"model": "warpbound:block/conveyor", "y": v} for k, v in
                                                         (("north", 0), ("east", 90), ("south", 180), ("west", 270))}})
    dump(f"{D}/warpbound/loot_table/blocks/conveyor.json", {"type": "minecraft:block", "pools": [{"rolls": 1, "bonus_rolls": 0,
         "entries": [{"type": "minecraft:item", "name": "warpbound:conveyor"}], "conditions": [{"condition": "minecraft:survives_explosion"}]}],
         "random_sequence": "warpbound:blocks/conveyor"})
    dump(f"{D}/warpbound/recipe/conveyor.json", {"type": "minecraft:crafting_shaped", "category": "building", "pattern": ["LLL", "IRI"],
         "key": {"L": {"item": "minecraft:leather"}, "I": {"item": "minecraft:iron_ingot"}, "R": {"item": "minecraft:redstone"}},
         "result": {"id": "warpbound:conveyor", "count": 8}})


conveyor()
path = f"{D}/minecraft/tags/block/mineable/pickaxe.json"
data = json.load(open(path, encoding="utf-8"))
for name in list(KINDS) + ["fluid_tank", "flare_stack", "conveyor"]:
    if f"warpbound:{name}" not in data["values"]:
        data["values"].append(f"warpbound:{name}")
dump(path, data)
print("ok")
