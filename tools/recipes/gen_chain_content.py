#!/usr/bin/env python3
"""
Контент цепочки из docs/industry/loyalist-chain.json для построенных машин:

    python3 tools/recipes/gen_chain_content.py

Пишет описания машин (data/warpbound/machine_spec, порты и энергия), рецепты (data/warpbound/machine_recipe),
Java-список новых предметов и жидкостей, модели и значки предметов, переводы.
Цифры — черновой баланс: 1 единица жидкости в цепочке = 1 ведро = 1000 мБ, дробный выход предмета — шанс.
"""
import hashlib
import json
import os
import re

from PIL import Image, ImageDraw

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
A = os.path.join(ROOT, "src/main/resources/assets/warpbound")
D = os.path.join(ROOT, "src/main/resources/data/warpbound")
J = os.path.join(ROOT, "src/main/java/dev/warpbound/core")

# сооружение цепочки -> блок мода; энергия МС/т (0 — машина на топливе и самотёке)
MACHINES = {
    "crusher": ("ore_crusher", 12), "wash_vat": ("wash_vat", 6), "coke_oven": ("coke_oven", 0), "blast_furnace": ("blast_furnace", 8),
    "converter": ("converter", 16), "rolling_mill": ("rolling_mill", 20), "electrolyzer": ("electrolyzer", 30), "scriptorium": ("scriptorium", 4),
    "armoury": ("armoury", 16), "barrel_shop": ("barrel_shop", 12), "ammo_line": ("ammo_line", 10), "weavery": ("weavery", 6),
    "forge": ("mechanicus_forge", 10), "forge_smelter": ("forge_smelter", 8), "cogitatorium": ("cogitatorium", 8),
    "distiller": ("distiller", 24), "desulfurizer": ("desulfurizer", 20), "autoclave": ("autoclave", 18),
    "chem_reactor": ("chem_reactor", 14), "powder_works": ("powder_works", 12), "cement_mill": ("cement_mill", 10),
    "cracker": ("cracker", 22), "hydroponics": ("hydroponics", 6), "lumber": ("lumber", 10), "deep_drill": ("deep_drill", 40),
}
# Машины без рецептов цепочки
SPECIAL = {
    "water_intake": dict(kind="source", energy_use=4, source_fluid="minecraft:water", source_rate_mb=50),
    "coal_gen": dict(kind="generator", energy_output=60),
    "promethium_extractor": dict(kind="custom"),
    # жжёт жидкость, мБ/с: ведро прометия на 20 секунд, газ слабее, но его всё равно некуда девать
    "promethium_gen": dict(kind="fluid_generator", energy_output=240, fuel_fluids={"warpbound:promethium": 50, "warpbound:promethium_gas": 100}),
}
VANILLA = {"iron_ore": "raw_iron", "copper_ore": "raw_copper", "gold_ore": "raw_gold", "coal": "coal", "gravel": "gravel", "sand": "sand",
           "leather": "leather", "string": "string", "planks": "oak_planks", "copper_ingot": "copper_ingot", "gold_ingot": "gold_ingot",
           "redstone": "redstone", "quartz": "quartz", "lapis": "lapis_lazuli", "stone": "stone", "bone": "bone", "log": "oak_log", "bone_meal": "bone_meal"}
# изделия, что уже есть в моде под другим именем
ALIAS = {"lead_ore": "raw_lead", "sulfur_ore": "raw_sulfur", "servo_1": "servo_motor", "las_cell": "las_battery", "flak_armour": "flak_chestplate"}
BLOCKS_NO_ICON = set()


def existing_ids():
    ids = set()
    for name in ("WarpboundItems.java", "WarpboundBuildingBlocks.java", "WarpboundBlocks.java"):
        text = open(os.path.join(J, name), encoding="utf-8").read()
        ids |= set(re.findall(r'(?:register|block|item|simple)\w*\(\s*"([a-z0-9_]+)"', text))
    return ids


def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)


chain = json.load(open(os.path.join(ROOT, "docs/industry/loyalist-chain.json"), encoding="utf-8"))
ITEMS, RECIPES = chain["items"], chain["recipes"]
have = existing_ids()
new_items, fluids = {}, {}


def is_fluid(cid):
    return ITEMS[cid]["kind"] == "жидкость"


def fluid_id(cid):
    if cid == "water":
        return "minecraft:water"
    fluids[cid] = ITEMS[cid]["name"]
    return f"warpbound:{cid}"


def item_id(cid):
    if cid in VANILLA:
        return "minecraft:" + VANILLA[cid]
    name = ALIAS.get(cid, cid)
    if name not in have:
        new_items[name] = ITEMS[cid]["name"]
    return "warpbound:" + name


for old in os.listdir(os.path.join(D, "machine_recipe")) if os.path.isdir(os.path.join(D, "machine_recipe")) else []:
    os.remove(os.path.join(D, "machine_recipe", old))

specs = {}
for sid, (block, energy) in MACHINES.items():
    recs = [r for r in RECIPES if r["s"] == sid]
    si, so, ti, to = 0, 0, 0, 0
    for n, r in enumerate(recs):
        ii = [x for x in r["i"] if not is_fluid(x[0])]
        fi = [x for x in r["i"] if is_fluid(x[0])]
        io = [x for x in r["o"] if not is_fluid(x[0])]
        fo = [x for x in r["o"] if is_fluid(x[0])]
        si, so, ti, to = max(si, len(ii)), max(so, len(io)), max(ti, len(fi)), max(to, len(fo))
        rec = {
            "machine": f"warpbound:{block}",
            "seconds": r["t"],
            "items_in": [{"item": item_id(c), "count": max(1, round(a))} for c, a in ii],
            "items_out": [{"item": item_id(c), "count": max(1, int(a)), "chance": round(a, 3) if a < 1 else 1.0} for c, a in io],
            "fluids_in": [{"fluid": fluid_id(c), "mb": round(a * 1000)} for c, a in fi],
            "fluids_out": [{"fluid": fluid_id(c), "mb": round(a * 1000)} for c, a in fo],
        }
        dump(f"{D}/machine_recipe/{block}_{n}.json", rec)
    assert si <= 6 and so <= 3 and ti <= 2 and to <= 4, (sid, si, so, ti, to)
    specs[block] = dict(kind="processor", energy_use=energy, slots_in=si, slots_out=so, tanks_in=ti, tanks_out=to)

for block, sp in SPECIAL.items():
    base = dict(energy_use=0, slots_in=0, slots_out=0, tanks_in=0, tanks_out=0)
    base.update(sp)
    specs[block] = base
specs["water_intake"].update(tanks_out=1)
specs["coal_gen"].update(slots_in=1)
specs["promethium_extractor"].update(tanks_out=1)
specs["promethium_gen"].update(tanks_in=1)


def ports_for(block, sp):
    """Порты на цоколе: предметы по бокам, энергия по центру сзади, жидкости сзади слева и справа."""
    layers = json.load(open(f"{D}/multiblock/{block}.json", encoding="utf-8"))["layers"]
    base = layers[0]
    cz = next(z for z, row in enumerate(base) if "C" in row)
    cx = base[cz].index("C")
    w, d = len(base[0]), len(base)
    mid = d // 2 - cz
    x0, x1 = -cx, w - 1 - cx
    back = d - 1 - cz
    ports = []
    if sp["slots_in"]:
        ports.append(dict(kind="item", output=False, x=x0, y=0, z=mid, face="west"))
    if sp["slots_out"]:
        ports.append(dict(kind="item", output=True, x=x1, y=0, z=mid, face="east"))
    if sp.get("energy_use") or sp.get("energy_output"):
        ports.append(dict(kind="energy", output=bool(sp.get("energy_output")), x=0, y=0, z=back, face="south"))
    if sp["tanks_in"]:
        ports.append(dict(kind="fluid", output=False, x=x0, y=0, z=back, face="south"))
    if sp["tanks_out"]:
        ports.append(dict(kind="fluid", output=True, x=x1, y=0, z=back, face="south"))
    for p in ports:
        assert base[p["z"] + cz][p["x"] + cx] != " ", (block, p)
    return ports


for block, sp in specs.items():
    sp["ports"] = ports_for(block, sp)
    sp.setdefault("energy_output", 0)
    sp.setdefault("source_fluid", "")
    sp.setdefault("source_rate_mb", 0)
    sp.setdefault("fuel_fluids", {})
    dump(f"{D}/machine_spec/{block}.json", sp)

# ---------------------------------------------------------------- Java и ресурсы новых предметов


def colour(name):
    h = hashlib.md5(name.encode()).digest()
    return 70 + h[0] % 150, 70 + h[1] % 150, 70 + h[2] % 150


def icon(name):
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    base = colour(name)
    dark = tuple(int(c * 0.55) for c in base)
    light = tuple(min(255, int(c * 1.35)) for c in base)
    if "ingot" in name or name in ("coke", "slag", "pig_iron"):
        d.polygon([(2, 11), (5, 5), (14, 5), (12, 11)], fill=base, outline=dark)
        d.line([(5, 6), (13, 6)], fill=light)
    elif "plate" in name or name in ("armaplas", "fabric", "parchment"):
        d.rectangle((2, 3, 13, 12), fill=base, outline=dark)
        d.line([(3, 4), (12, 4)], fill=light)
    elif "rod" in name or "tube" in name or "barrel" in name:
        d.line([(3, 13), (13, 3)], fill=dark, width=4)
        d.line([(3, 12), (12, 3)], fill=base, width=2)
    elif "wire" in name or "coil" in name or name == "string":
        for y in (4, 7, 10):
            d.line([(3, y), (12, y + 1)], fill=base, width=2)
    elif any(k in name for k in ("crushed", "washed", "dust", "sulfur", "sawdust", "resin", "herbs", "incense", "powder", "propellant", "fyceline")):
        for x, y, r in ((5, 10, 3), (10, 10, 3), (8, 6, 3)):
            d.ellipse((x - r, y - r, x + r, y + r), fill=base, outline=dark)
    elif "gear" in name or "board" in name or "engine" in name or "receiver" in name or "fuse" in name or "feed" in name:
        d.rectangle((3, 3, 12, 12), fill=dark, outline=base)
        d.rectangle((6, 6, 9, 9), fill=light)
    elif any(k in name for k in ("round", "casing", "magazine", "belt", "canister")):
        d.rectangle((6, 3, 9, 12), fill=base, outline=dark)
        d.rectangle((6, 10, 9, 12), fill=light)
    else:
        d.polygon([(3, 12), (3, 7), (12, 3), (13, 5), (7, 8), (7, 12)], fill=base, outline=dark)
    return img


tex = os.path.join(A, "textures/item")
os.makedirs(tex, exist_ok=True)
for name in sorted(new_items):
    # настоящие значки рисует tools/textures/gen_chain_icons.py; заглушка только для совсем нового предмета
    if not os.path.exists(os.path.join(tex, name + ".png")):
        icon(name).save(os.path.join(tex, name + ".png"))
    dump(f"{A}/models/item/{name}.json", {"parent": "minecraft:item/generated", "textures": {"layer0": f"warpbound:item/{name}"}})

FLUID_COLOURS = {"holy_water": 0x9ad8ff, "sludge": 0x4a4032, "coal_tar": 0x20201c, "oxygen": 0xcfe8ff, "hydrogen": 0xf0f0ff, "heavy_water": 0x5a7fb0,
                 "deuterium": 0xc0a8ff, "crude_promethium": 0x2458b0, "heavy_fraction": 0x3a2a12, "sour_promethium": 0x2c8c8c, "aromatics": 0xb0702a,
                 "promethium_gas": 0x8fc8ff, "promethium": 0x46a6ff, "bitumen": 0x101010, "sacred_oil": 0xd4b04a,
                 "sulfuric_acid": 0xc8d24a, "nitric_acid": 0xe8a23c, "spent_acid": 0x7c6a3a}
lines = ["package dev.warpbound.core;", "", "import java.util.List;", "import java.util.Map;", "",
         "/** Предметы и жидкости цепочки. СГЕНЕРИРОВАНО tools/recipes/gen_chain_content.py — руками не править. */",
         "public final class ChainContentList {", "    public static final List<String> ITEMS = List.of("]
lines.append(",\n".join(f'            "{n}"' for n in sorted(new_items)) + ");")
lines.append("    /** Жидкость цепочки и её цвет в окне машины. */")
lines.append("    public static final Map<String, Integer> FLUIDS = Map.ofEntries(")
lines.append(",\n".join(f'            Map.entry("{n}", 0x{FLUID_COLOURS.get(n, 0x808080):06x})' for n in sorted(fluids)) + ");")
lines += ["", "    private ChainContentList() {", "    }", "}", ""]
open(os.path.join(J, "ChainContentList.java"), "w", encoding="utf-8").write("\n".join(lines))

ru = {f"item.warpbound.{n}": t for n, t in new_items.items()}
ru.update({f"fluid.warpbound.{n}": t for n, t in fluids.items()})
en = {k: k.split(".")[-1].replace("_", " ").title() for k in ru}
L = ["package dev.warpbound.client.datagen;", "", "import net.fabricmc.fabric.api.datagen.v1.provider.FabricLanguageProvider;", "",
     "/** Переводы контента цепочки. СГЕНЕРИРОВАНО tools/recipes/gen_chain_content.py — руками не править. */", "final class ChainLang {",
     "    private ChainLang() {", "    }", "", "    static void ru(FabricLanguageProvider.TranslationBuilder builder) {"]
L += [f'        builder.add("{k}", "{v}");' for k, v in sorted(ru.items())]
L += ["    }", "", "    static void en(FabricLanguageProvider.TranslationBuilder builder) {"]
L += [f'        builder.add("{k}", "{v}");' for k, v in sorted(en.items())]
L += ["    }", "}", ""]
open(os.path.join(ROOT, "src/client/java/dev/warpbound/client/datagen/ChainLang.java"), "w", encoding="utf-8").write("\n".join(L))
print("машин", len(specs), "новых предметов", len(new_items), "жидкостей", len(fluids), "рецептов", sum(1 for r in RECIPES if r["s"] in MACHINES))
