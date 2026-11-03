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
    "chem_reactor": [["HCH", "HHH", "HHH"], ["FTF", "F F", "TTT"], ["FTF", "F F", "TTT"], ["S S", " S ", "S S"]],
    "cement_mill": [["HCH", "HHH", "HHH"], ["TFE", "EEE", "TTT"], ["FEF", "EEE", "F F"], ["SSS", "SSS", "SSS"]],
    "cracker": [["HCH", "HHH", "HHH"], ["TTF", "TTF", "TTF"], ["FTF", "TTF", "TTF"], [" T ", "TTT", " TF"], [" S ", "SSS", " SF"]],
    "powder_works": [["HHCHH", "HHHHH", "HHHHH"], ["TFFFF", "TFEFF", "TTTTT"], ["F F F", "    F", "TTTTT"], ["TTTTT", "TTTTT", "TTTTT"]],
    "promethium_gen": [["HHCHH", "HHHHH", "HHHHH"], ["FFFFE", "EEEEE", "TTTTT"], ["FFFF ", "FFFFT", "TTT T"], ["SSS S", "SSSSS", "     "]],
    "hydroponics": [["HHCHH", "HHHHH", "HHHHH"], ["F FFT", "FFFFT", "F FFT"], ["F FF ", "FFFFT", "F FFT"], ["TTTT ", "TTTTT", "TTTTT"]],
    "lumber": [
        ["HHCHH", "HHHHH", "HHHHH", "HHHHH", "HHHHH"],
        ["TFFFT", "TFFFT", "TFEFT", "TF FT", "T   T"],
        ["F F F", "F F F", "F E F", "F   F", "F   F"],
        ["FFFFF", "F   F", "F   F", "F   F", "FFFFF"],
    ],
    "deep_drill": [
        ["HHCHH", "HHHHH", "HHHHH", "HHHHH", "HHHHH"],
        ["TTFTT", "FFFFF", "FFEFF", "FFFFF", "TTFTT"],
    ] + [["F   F", "     ", "  F  ", "     ", "F   F"]] * 2 + [["     ", " F F ", "  F  ", " F F ", "     "]] * 4
      + [["     ", "     ", "  F  ", "     ", "     "]] * 4,
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
    dump(f"{D}/warpbound/loot_table/blocks/{name}.json", loot(name))
    dump(f"{D}/warpbound/multiblock/{name}.json", {"name": f"block.warpbound.{name}", "layers": layers, "key": KEY})
dump(f"{D}/warpbound/loot_table/blocks/promethium_extractor.json", loot("promethium_extractor"))
# Ядро машины: общая рама (тяжёлый кожух, шестерни) и один отличительный предмет — что-то из самой машины.
# Предмет не должен зависеть от того, что машина делает: иначе цикл (электролизёр даёт кислород для стали, поэтому сталь в нём нельзя).
# Проверка — tools/recipes/audit_recipes.py.
SIGNATURE = {
    # глава 2: только ванилла и детали пресса
    "ore_crusher": "minecraft:piston", "wash_vat": "minecraft:cauldron", "coke_oven": "minecraft:bricks", "water_intake": "minecraft:bucket",
    "coal_gen": "minecraft:furnace", "scriptorium": "minecraft:lectern", "forge_smelter": "minecraft:blast_furnace",
    "cogitatorium": "warpbound:vox_module", "electrolyzer": "warpbound:capacitor", "weavery": "minecraft:loom",
    "lumber": "minecraft:stonecutter", "hydroponics": "minecraft:composter", "cement_mill": "minecraft:grindstone",
    # глава 3: чугун и сталь по мере появления
    "blast_furnace": "minecraft:blast_furnace", "converter": "warpbound:pig_iron", "rolling_mill": "warpbound:steel_ingot",
    "armoury": "warpbound:steel_plate", "barrel_shop": "warpbound:steel_tube", "ammo_line": "warpbound:steel_rod",
    # глава 4: прометий и химия
    "promethium_extractor": "warpbound:steel_tube", "distiller": "warpbound:steel_tube", "desulfurizer": "warpbound:steel_plate",
    "autoclave": "warpbound:steel_plate", "cracker": "warpbound:steel_tube", "chem_reactor": "minecraft:glass_bottle",
    "powder_works": "warpbound:steel_plate", "promethium_gen": "warpbound:motive_coil", "deep_drill": "warpbound:drill_head",
}
for name in names + ["promethium_extractor"]:
    dump(f"{D}/warpbound/recipe/{name}.json", {"type": "minecraft:crafting_shaped", "category": "building", "pattern": ["HGH", "GXG", "HDH"],
         "key": {"H": {"item": "warpbound:heavy_casing"}, "G": {"item": "warpbound:brass_gear"}, "D": {"item": "warpbound:drive_block"},
                 "X": {"item": SIGNATURE[name]}},
         "result": {"id": f"warpbound:{name}", "count": 1}})
# Ядро Кузни: схема от техножреца, поэтому Кузня не раньше его прилёта (как пульт верфи)
dump(f"{D}/warpbound/recipe/mechanicus_forge.json", {"type": "minecraft:crafting_shaped", "category": "building", "pattern": ["BFB", "RSR", "III"],
     "key": {"B": {"item": "warpbound:brass_ingot"}, "F": {"item": "minecraft:furnace"}, "R": {"item": "minecraft:redstone"},
             "S": {"item": "warpbound:forge_schematic"}, "I": {"item": "minecraft:iron_ingot"}},
     "result": {"id": "warpbound:mechanicus_forge", "count": 1}})
# значок в инвентаре — рендер настоящего меша (render_icons.py + shrink_machine_icons.py), иначе все машины выглядят одним кубом
for name in names + ["promethium_extractor", "mechanicus_forge", "manual_press", "salvage_forge"]:
    dump(f"{A}/models/item/{name}.json", {"parent": "minecraft:item/generated", "textures": {"layer0": f"warpbound:item/machine_{name}"}})
add_tag("mineable/pickaxe.json", names + ["promethium_extractor"])
add_tag("needs_stone_tool.json", names + ["promethium_extractor"])
print("машин:", len(names))
