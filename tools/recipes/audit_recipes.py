#!/usr/bin/env python3
"""
Проверка достижимости: чего игрок на самом деле может добыть, начиная с ванильного мира.

    python3 tools/recipes/audit_recipes.py

Считает неподвижную точку: ванилла и добыча из мира → рецепты верстака и печи → горн и пресс → ядра машин и блоки их шаблонов →
рецепты машин. В конце — список недостижимых предметов мода и машин. Падает с кодом 1, если что-то из MUST недостижимо.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
D = os.path.join(ROOT, "src/main/resources/data/warpbound")
J = os.path.join(ROOT, "src/main/java/dev/warpbound/core")

# что лежит в мире и достаётся без рецептов (Кинерис и прочие миры идут отдельной пометкой)
WORLD = {"warpbound:raw_lead", "warpbound:raw_sulfur", "warpbound:saltpeter", "warpbound:hull_scrap", "warpbound:scorched_hull_plating", "warpbound:hull_plating", "warpbound:brass_trim",
         "warpbound:data_slate_storm", "warpbound:data_slate_navigator", "warpbound:data_slate_ship"}
# награды и выдача по сюжету (квесты, прилёт техножреца); добыча блоков из мира; оборудование корабля выдаёт верфь
STORY = {"warpbound:forge_schematic", "warpbound:omnissiah_sigil", "warpbound:shipyard_schematic", "warpbound:obelisk_schematic", "warpbound:vox_beacon",
         "warpbound:vox_module", "warpbound:teleport_homer"}
BLOCKS_IN_WORLD = {"warpbound:lead_ore", "warpbound:deepslate_lead_ore", "warpbound:sulfur_ore", "warpbound:deepslate_sulfur_ore", "warpbound:saltpeter_ore",
                   "warpbound:bitumen_shale", "warpbound:promethium_seep", "warpbound:imperial_standard", "warpbound:imperial_standard_pole"}
OFFWORLD_BLOCKS = {"warpbound:adamantium_ore", "warpbound:radium_ore", "warpbound:warpstone_ore", "warpbound:psycrystal_cluster", "warpbound:ash_block",
                   "warpbound:ash_clay", "warpbound:ash_stone", "warpbound:charred_log", "warpbound:bone_pile", "warpbound:vitrified_glass",
                   "warpbound:amber_vitrified_glass", "warpbound:smoke_vitrified_glass"}
SHIP_FIXTURES = {"warpbound:nav_table", "warpbound:auspex", "warpbound:geller_node", "warpbound:reactor_core", "warpbound:teleportarium_pad", "warpbound:command_throne",
                 "warpbound:command_console", "warpbound:star_chart", "warpbound:grav_lift", "warpbound:warp_sampler", "warpbound:warp_drive", "warpbound:radiation_sign",
                 "warpbound:emergency_lumen", "warpbound:coolant_pipe", "warpbound:geller_conduit", "warpbound:bulkhead_door", "warpbound:boarding_hatch"}
OFFWORLD = {"warpbound:raw_radium", "warpbound:raw_adamantium", "warpbound:warpstone_shard", "warpbound:psycrystal", "warpbound:warp_sample"}
FLUIDS_FREE = {"minecraft:water"}
# обязательно к Сезону 1: без этого падаем
MUST = ["warpbound:lasgun", "warpbound:las_battery", "warpbound:chainsword", "warpbound:flak_chestplate", "warpbound:carapace_armour", "warpbound:bolt_round",
        "warpbound:steel_ingot", "warpbound:plasteel_plate", "warpbound:parchment", "warpbound:rockrete", "warpbound:ferrocrete",
        "warpbound:drill_head", "warpbound:deep_drill", "warpbound:promethium_gen", "warpbound:chem_reactor", "warpbound:powder_works"]


def load(path):
    return json.load(open(path, encoding="utf-8"))


def ings(obj):
    """Все ингредиенты рецепта: предмет; тег считаем доступным, если он не наш."""
    out = []
    def add(x):
        if isinstance(x, list):
            # любой из вариантов: для простоты берём первый
            add(x[0])
        elif isinstance(x, dict):
            if "item" in x:
                out.append(x["item"])
            elif "tag" in x and x["tag"].startswith("warpbound:"):
                out.append("#" + x["tag"])
    for k in obj.get("key", {}).values():
        add(k)
    for i in obj.get("ingredients", []):
        add(i)
    if "ingredient" in obj:
        add(obj["ingredient"])
    return out


recipes = []    # (что нужно, что нужно иметь как машину, выходы, откуда)
for path in glob.glob(os.path.join(D, "recipe", "**", "*.json"), recursive=True):
    r = load(path)
    rel = os.path.relpath(path, D)
    if "result" in r:
        res = r["result"]
        out = res["id"] if isinstance(res, dict) and "id" in res else res if isinstance(res, str) else res.get("item")
        needs = ings(r)
        kind = r.get("type", "")
        machine = "warpbound:salvage_forge" if "salvag" in kind else None
        recipes.append((needs, machine, [out], rel))
for path in glob.glob(os.path.join(D, "pressing", "*.json")):
    r = load(path)
    item = r.get("ingredient", r.get("input"))
    item = item.get("item") if isinstance(item, dict) else item
    res = r.get("result", r.get("output"))
    res = res.get("id", res.get("item")) if isinstance(res, dict) else res
    recipes.append(([item], "warpbound:manual_press", [res], os.path.relpath(path, D)))
for path in glob.glob(os.path.join(D, "machine_recipe", "*.json")):
    r = load(path)
    needs = [x["item"] for x in r["items_in"]] + ["~" + x["fluid"] for x in r["fluids_in"]]
    outs = [x["item"] for x in r["items_out"]] + ["~" + x["fluid"] for x in r["fluids_out"]]
    recipes.append((needs, r["machine"], outs, os.path.relpath(path, D)))
# блоки: кто что роняет
drops = {}
for path in glob.glob(os.path.join(D, "loot_table", "blocks", "*.json")):
    n = os.path.basename(path)[:-5]
    t = load(path)
    for pool in t.get("pools", []):
        for e in pool.get("entries", []):
            if e.get("type") == "minecraft:item":
                drops.setdefault(f"warpbound:{n}", e["name"])

# шаблоны машин: ядро + блоки шаблона
need_for_machine = {}
for path in glob.glob(os.path.join(D, "multiblock", "*.json")):
    t = load(path)
    n = "warpbound:" + os.path.basename(path)[:-5]
    used = set("".join("".join(row) for layer in t["layers"] for row in layer)) - {" ", ".", "C"}
    need_for_machine[n] = [t["key"][c] for c in used if c in t["key"] and not t["key"][c].startswith("#")]

known = {"~minecraft:water"} | set(WORLD) | set(OFFWORLD) | STORY | BLOCKS_IN_WORLD | OFFWORLD_BLOCKS | SHIP_FIXTURES
# сырой прометий качает экстрактор
sources = {"~warpbound:crude_promethium": "warpbound:promethium_extractor", "~minecraft:water": None}


def have(x):
    return x in known or x.startswith("minecraft:") or (x.startswith("~") and x[1:] in FLUIDS_FREE)


def machine_ready(m):
    if m is None:
        return True
    if not have(m):
        return False
    return all(have(b) for b in need_for_machine.get(m, []))


changed = True
order = []
while changed:
    changed = False
    for needs, machine, outs, src in recipes:
        if not machine_ready(machine) or not all(have(n) for n in needs):
            continue
        for o in outs:
            if o and not have(o):
                known.add(o)
                order.append((o, src))
                changed = True
    for fluid, m in sources.items():
        if fluid not in known and machine_ready(m):
            known.add(fluid)
            changed = True
    for block, item in drops.items():
        pass


def registered():
    ids = set()
    t = open(os.path.join(J, "ChainContentList.java"), encoding="utf-8").read()
    ids |= {"warpbound:" + x for x in re.findall(r'"([a-z0-9_]+)",?\s*$|"([a-z0-9_]+)"\)', t, re.M) for x in x if x and "aromatics" != x}
    for name in ("WarpboundItems.java", "WarpboundBlocks.java", "WarpboundBuildingBlocks.java"):
        t = open(os.path.join(J, name), encoding="utf-8").read()
        ids |= {"warpbound:" + x for x in re.findall(r'(?:register|block|item|simple|chainMachine|fixture|conduit)\w*\(\s*"([a-z0-9_]+)"', t)}
    return ids


all_ids = registered()
missing = sorted(i for i in all_ids if not have(i))
machines = sorted(m for m in need_for_machine if not machine_ready(m))
print("всего предметов и блоков:", len(all_ids), "достижимо:", len(all_ids) - len(missing))
print("\nНЕДОСТИЖИМЫЕ:")
for m in missing:
    print("  ", m)
print("\nМАШИНЫ, КОТОРЫЕ НЕЛЬЗЯ СОБРАТЬ:", machines)
stuck = {}
for needs, machine, outs, src in recipes:
    if machine_ready(machine) and all(have(n) for n in needs):
        continue
    gap = [n for n in needs if not have(n)]
    if machine and not machine_ready(machine):
        gap.append("машина " + machine)
    stuck[src] = gap
print("\nРЕЦЕПТЫ БЕЗ ВХОДА (причины):")
counts = {}
for gap in stuck.values():
    for g in gap:
        counts[g] = counts.get(g, 0) + 1
for g, c in sorted(counts.items(), key=lambda x: -x[1])[:40]:
    print(f"  {c:3}  {g}")
bad = [m for m in MUST if not have(m)]
print("\nОБЯЗАТЕЛЬНЫЕ недостижимы:" if bad else "\nВсё обязательное достижимо.", bad or "")
sys.exit(1 if bad else 0)
