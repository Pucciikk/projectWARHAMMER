#!/usr/bin/env python3
"""
Ресурсы машин цепочки: состояния блока, модель несобранного ядра, предмет, лут, шаблон мультиблока, теги.

    python3 tools/models/blender/register_chain.py

Шаблон пока только по размеру сооружения: стоимость постройки будем решать вместе с балансом.
Первая строка каждого слоя — передний ряд, ядро C — в его середине.
"""
import json
import os

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
A = os.path.join(ROOT, "src/main/resources/assets/warpbound")
D = os.path.join(ROOT, "src/main/resources/data")

KEY = {"H": "warpbound:heavy_casing", "F": "warpbound:support_frame", "E": "warpbound:drive_block",
       "T": "warpbound:riveted_plasteel_panel", "S": "warpbound:plasteel_vent"}

TEMPLATES = {
    "ore_crusher": [["HCH", "HHH", "HHH"], ["FEF", "FEF", "TTT"], ["FEF", "F F", "T T"], ["SSS", "S S", "SSS"]],
    "wash_vat": [["HCH", "HHH", "HHH"], ["TTT", "T T", "TET"], ["FEF", "   ", "F F"]],
    "coke_oven": [["HCH", "HHH", "HHH"], ["TTT", "T T", "TET"], ["SSS", "S S", "SSS"]],
    "converter": [["HCH", "HHH", "HHH"], ["FEF", "F F", "FEF"], ["FTF", "T T", "FTF"], ["F F", "   ", "F F"], ["SSS", "SSS", "SSS"]],
    "rolling_mill": [["HHHCHHH", "HHHHHHH", "HHHHHHH"], ["TTFEF  ", "TTFEF F", "TTFEEEF"], ["TT F F ", "TT F F ", "T  EEE "]],
    "electrolyzer": [["HCH", "HHH", "HHH"], ["FTF", "FTF", "TET"], ["SFS", "S S", "TET"]],
    "water_intake": [["HCH", "HHH", "HHH"], ["F E", "F E", "TTT"], ["FFF", "   ", "   "]],
    "coal_gen": [["HCH", "HHH", "HHH"], ["TTE", "TTE", "TTE"], ["TTF", "TTF", "SFF"], ["FS ", "   ", "S  "]],
    "scriptorium": [
        ["HHCHH", "HHHHH", "HHHHH", "HHHHH", "HHHHH"],
        ["F   F", "T   T", "T   T", "T   T", "FTTTF"],
        ["F   F", "T   T", "T   T", "T   T", "FTTTF"],
        ["FTTTF", "T   T", "T   T", "T   T", "FTTTF"],
        ["SSSSS", "S   S", "S   S", "S   S", "SSSSS"],
    ],
    "armoury": [
        ["HHCHH", "HHHHH", "HHHHH", "HHHHH", "HHHHH"],
        ["F   F", "     ", "F E F", "T   T", "TTTTT"],
        ["F   F", "     ", "F   F", "T   T", "TTTTT"],
        ["FFFFF", "F   F", "F   F", "F   F", "FFFFF"],
    ],
    "barrel_shop": [["HHHCHHH", "HHHHHHH", "HHHHHHH"], ["EEFFFEE", "EEFFFEE", "EEF TTT"], ["FF    F", "F      ", "F  T   "]],
    "ammo_line": [["HHHCHHH", "HHHHHHH", "HHHHHHH"], ["TF F FT", "TF F FT", "EEEEEEE"], ["TF F F ", "TF F F ", "SSSSSSS"]],
    "weavery": [["HHCHH", "HHHHH", "HHHHH"], ["EFF F", "EFF E", "TFFFE"], [" F F ", " F F ", " FFF "]],
    "distiller": [["HCH", "HHH", "HHH"], ["TTT", "TTT", "TTT"]] + [["FTF", "TTT", "FTF"]] * 6 + [["SFS", "FTF", "SFS"]],
    "desulfurizer": [["HCH", "HHH", "HHH"], ["FTF", "TTT", "FTE"], ["FTF", "TTT", "FTE"], [" S ", "SSS", " S "]],
    "autoclave": [["HCH", "HHH", "HHH"], ["TTT", "TTT", "TET"], ["TTT", "TTT", "TET"], ["FSF", "S S", "FSF"]],
    "forge_smelter": [["HCH", "HHH", "HHH"], ["TTF", "TTF", "EET"], ["F F", " F ", "  S"]],
    "cogitatorium": [
        ["HHCHH", "HHHHH", "HHHHH", "HHHHH", "HHHHH"],
        ["F   F", "     ", "F E F", "T E T", "TTTTT"],
        ["F   F", "     ", "F   F", "T   T", "TTTTT"],
        ["FFFFF", "F   F", "F   F", "F   F", "FFFFF"],
    ],
    "blast_furnace": [
        ["HHCHH", "HHHHH", "HHHHH", "HHHHH", "HHHHH"],
        ["TTTTT", "T   T", "T   T", "T   T", "TEEET"],
        ["FTTTF", "T   T", "T   T", "T   T", "FTETF"],
        [" TTT ", "T   T", "T   T", "T   T", " TET "],
        [" TTT ", "T   T", "T   T", "T   T", " TET "],
        ["  S  ", " S S ", "S   S", " S S ", "  S  "],
        ["     ", " FFF ", " F F ", " FFF ", "     "],
    ],
}


def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)


def state_file(name):
    variants = {}
    for formed in ("true", "false"):
        for facing in ("north", "south", "east", "west"):
            for lit in ("true", "false"):
                variants[f"formed={formed},facing={facing},lit={lit}"] = {"model": f"warpbound:block/{name}"}
    return {"variants": variants}


def loot(name):
    return {"type": "minecraft:block", "pools": [{"rolls": 1, "bonus_rolls": 0,
            "entries": [{"type": "minecraft:item", "name": f"warpbound:{name}"}],
            "conditions": [{"condition": "minecraft:survives_explosion"}]}],
            "random_sequence": f"warpbound:blocks/{name}"}


def add_tag(rel, names):
    path = os.path.join(D, "minecraft/tags/block", rel)
    data = json.load(open(path, encoding="utf-8"))
    for n in names:
        v = f"warpbound:{n}"
        if v not in data["values"]:
            data["values"].append(v)
    dump(path, data)


names = list(TEMPLATES)
for name, layers in TEMPLATES.items():
    dump(f"{A}/blockstates/{name}.json", state_file(name))
    dump(f"{A}/models/block/{name}.json", {"parent": "minecraft:block/cube_bottom_top", "textures": {
        "side": "warpbound:block/drive_block", "top": "warpbound:block/heavy_casing", "bottom": "warpbound:block/heavy_casing"}})
    dump(f"{A}/models/item/{name}.json", {"parent": f"warpbound:block/{name}"})
    dump(f"{D}/warpbound/loot_table/blocks/{name}.json", loot(name))
    dump(f"{D}/warpbound/multiblock/{name}.json", {"name": f"block.warpbound.{name}", "layers": layers, "key": KEY})
dump(f"{D}/warpbound/loot_table/blocks/promethium_extractor.json", loot("promethium_extractor"))
# ядро машины: черновой рецепт, у всех одинаковый, пока нет баланса
for name in names + ["promethium_extractor"]:
    dump(f"{D}/warpbound/recipe/{name}.json", {"type": "minecraft:crafting_shaped", "category": "building", "pattern": ["HGH", "GDG", "HGH"],
         "key": {"H": {"item": "warpbound:heavy_casing"}, "G": {"item": "warpbound:brass_gear"}, "D": {"item": "warpbound:drive_block"}},
         "result": {"id": f"warpbound:{name}", "count": 1}})
add_tag("mineable/pickaxe.json", names + ["promethium_extractor"])
add_tag("needs_stone_tool.json", names + ["promethium_extractor"])
print("машин:", len(names))
