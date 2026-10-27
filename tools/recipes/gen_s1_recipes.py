"""
Рецепты предметов Сезона 1 (docs/content/season1-items.md): компоненты, лазган, цепной меч, флак, респиратор,
подзарядка лазпакета в костре, недостающие рецепты корабельных блоков.

    python3 tools/recipes/gen_s1_recipes.py
"""
import json
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "src", "main", "resources", "data", "warpbound", "recipe")


def ing(x):
    return {"tag": x[1:]} if x.startswith("#") else {"item": x if ":" in x else "warpbound:" + x}


def shaped(name, pattern, key, result, count=1, category="equipment"):
    write(name, {"type": "minecraft:crafting_shaped", "category": category, "pattern": pattern,
                 "key": {k: ing(v) for k, v in key.items()},
                 "result": {"id": "warpbound:" + result, "count": count}})


def shapeless(name, items, result, count=1, category="misc"):
    write(name, {"type": "minecraft:crafting_shapeless", "category": category, "ingredients": [ing(i) for i in items],
                 "result": {"id": "warpbound:" + result, "count": count}})


def write(name, data):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)


def main():
    # ---- компоненты
    shapeless("focusing_lens", ["minecraft:amethyst_shard", "minecraft:glass_pane", "brass_ingot"], "focusing_lens")
    shaped("capacitor", [" C ", "RLR", " C "], {"C": "minecraft:copper_ingot", "R": "minecraft:redstone", "L": "lead_ingot"},
           "capacitor", 2, "misc")
    shaped("las_battery", ["LCL"], {"L": "lead_ingot", "C": "capacitor"}, "las_battery", 2, "misc")
    shaped("servo_motor", ["GRG", "PIP"], {"G": "brass_gear", "R": "minecraft:redstone", "P": "plasteel_plate",
                                           "I": "minecraft:iron_ingot"}, "servo_motor", 1, "misc")
    shaped("chain_blade", ["PCP", "PCP"], {"P": "plasteel_plate", "C": "minecraft:chain"}, "chain_blade", 1, "misc")
    shaped("flak_plate", ["WPW"], {"W": "#minecraft:wool", "P": "plasteel_plate"}, "flak_plate", 2, "misc")
    shapeless("respirator_filter", ["minecraft:charcoal", "minecraft:paper", "#minecraft:wool"], "respirator_filter", 2)
    # аварийная зарядка лазпакета в костре (лор)
    write("las_battery_recharge", {"type": "minecraft:campfire_cooking", "category": "misc",
                                   "ingredient": ing("las_battery_depleted"), "result": {"id": "warpbound:las_battery"},
                                   "experience": 0.1, "cookingtime": 600})
    # ---- оружие
    shaped("lasgun", [" PF", "PCG", "W  "], {"P": "plasteel_plate", "F": "focusing_lens", "C": "capacitor",
                                            "G": "brass_gear", "W": "#minecraft:planks"}, "lasgun")
    shaped("chainsword", [" B ", " B ", "GSG"], {"B": "chain_blade", "S": "servo_motor", "G": "brass_gear"}, "chainsword")
    # ---- броня
    F = {"F": "flak_plate"}
    shaped("flak_helmet", ["FFF", "F F"], F, "flak_helmet")
    shaped("flak_chestplate", ["F F", "FFF", "FFF"], F, "flak_chestplate")
    shaped("flak_leggings", ["FFF", "F F", "F F"], F, "flak_leggings")
    shaped("flak_boots", ["F F", "F F"], F, "flak_boots")
    shaped("respirator", [" L ", "XPX"], {"L": "minecraft:leather", "X": "respirator_filter", "P": "plasteel_plate"}, "respirator")
    # ---- недостающие корабельные блоки
    shaped("hull_plating", ["PP", "PP"], {"P": "plasteel_plate"}, "hull_plating", 4, "building")
    shaped("brass_trim", ["BB", "BB"], {"B": "brass_ingot"}, "brass_trim", 4, "building")
    print("рецептов: 18")


if __name__ == "__main__":
    main()
