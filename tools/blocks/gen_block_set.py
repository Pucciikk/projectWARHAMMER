#!/usr/bin/env python3
"""
Набор блоков Warpbound: корабельная обшивка и отделка, руды, камень и грунт Кинериса.

    python3 tools/blocks/gen_block_set.py

Одна спецификация (BLOCKS, ITEMS ниже) — и из неё всё сразу:
  textures/block/*.png (32×32, анимация — .mcmeta), textures/item/*.png (16×16),
  blockstates, models/block, models/item, loot_table/blocks, recipe, теги инструментов,
  Java: core/WarpboundBuildingBlocks.java (регистрация) и client/datagen/BuildingBlockLang.java (переводы).
Сгенерированные Java-файлы руками не править — менять спецификацию здесь.
"""
import json
import os
import random
import sys
import zlib

import numpy as np
from PIL import Image

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "models"))
import textures as T  # noqa: E402
from gen_blocks import build as build_parts, MECH  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
ASSETS = os.path.join(ROOT, "src/main/resources/assets/warpbound")
DATA = os.path.join(ROOT, "src/main/resources/data")
JAVA = os.path.join(ROOT, "src/main/java/dev/warpbound/core/WarpboundBuildingBlocks.java")
LANG = os.path.join(ROOT, "src/client/java/dev/warpbound/client/datagen/BuildingBlockLang.java")

# Свойства по материалу: Java-выражение, теги инструмента
MATS = {
    "metal": ("BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(4f, 9f).sound(SoundType.NETHERITE_BLOCK)"
              ".requiresCorrectToolForDrops()", "pickaxe", "stone"),
    "light_metal": ("BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(2.5f, 6f).sound(SoundType.COPPER)"
                    ".requiresCorrectToolForDrops()", "pickaxe", None),
    "stone": ("BlockBehaviour.Properties.of().mapColor(MapColor.STONE).strength(1.5f, 6f).sound(SoundType.STONE)"
              ".requiresCorrectToolForDrops()", "pickaxe", None),
    "ore": ("BlockBehaviour.Properties.of().mapColor(MapColor.STONE).strength(3f, 3f).sound(SoundType.STONE)"
            ".requiresCorrectToolForDrops()", "pickaxe", "stone"),
    "deep_ore": ("BlockBehaviour.Properties.of().mapColor(MapColor.DEEPSLATE).strength(4.5f, 3f).sound(SoundType.DEEPSLATE)"
                 ".requiresCorrectToolForDrops()", "pickaxe", "stone"),
    "hard_ore": ("BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_BLACK).strength(8f, 1200f).sound(SoundType.ANCIENT_DEBRIS)"
                 ".requiresCorrectToolForDrops()", "pickaxe", "diamond"),
    "crystal": ("BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_PURPLE).strength(1.5f).sound(SoundType.AMETHYST_CLUSTER)"
                ".noOcclusion()", "pickaxe", None),
    "ash": ("BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_GRAY).strength(0.5f).sound(SoundType.SAND)", "shovel", None),
    "clay": ("BlockBehaviour.Properties.of().mapColor(MapColor.CLAY).strength(0.6f).sound(SoundType.GRAVEL)", "shovel", None),
    "glass": ("BlockBehaviour.Properties.of().mapColor(MapColor.NONE).strength(0.6f).sound(SoundType.GLASS).noOcclusion()"
              ".isValidSpawn((s, l, p, e) -> false).isRedstoneConductor((s, l, p) -> false)"
              ".isSuffocating((s, l, p) -> false).isViewBlocking((s, l, p) -> false)", "pickaxe", None),
    "wood": ("BlockBehaviour.Properties.of().mapColor(MapColor.COLOR_BLACK).strength(2f).sound(SoundType.WOOD)", "axe", None),
    "bone": ("BlockBehaviour.Properties.of().mapColor(MapColor.SAND).strength(0.3f).sound(SoundType.BONE_BLOCK).noOcclusion()"
             ".noCollission()", None, None),
    "lamp": ("BlockBehaviour.Properties.of().mapColor(MapColor.METAL).strength(1f).sound(SoundType.LANTERN).noOcclusion()",
             "pickaxe", None),
}

# kind: cube | column | pillar | orientable | glass | cutout_cube | ore | falling | stairs | slab | wall | cross | carpet | parts
BLOCKS = [
    # --- корабль и имперская отделка (S1)
    dict(id="hull_plating", ru="Обшивка корабля", en="Hull Plating", kind="cube", mat="metal", tex="hull_plating", existing=True),
    dict(id="scorched_hull_plating", ru="Обгоревшая обшивка", en="Scorched Hull Plating", kind="cube", mat="metal",
         tex="scorched_hull_plating", existing=True),
    dict(id="brass_trim", ru="Латунная отделка", en="Brass Trim", kind="cube", mat="metal", tex="brass_trim", existing=True),
    dict(id="dock_girder", ru="Балка стапеля", en="Dock Girder", kind="column", mat="metal", tex="dock_girder", existing=True),
    dict(id="hull_scrap", ru="Пластальной лом", en="Plasteel Scrap", kind="cube", mat="light_metal", tex="hull_scrap"),
    dict(id="plasteel_panel", ru="Пласталевая панель", en="Plasteel Panel", kind="cube", mat="metal", tex="plasteel_panel"),
    dict(id="riveted_plasteel_panel", ru="Клёпаная пласталевая панель", en="Riveted Plasteel Panel", kind="cube", mat="metal",
         tex="riveted_plasteel_panel"),
    dict(id="hazard_panel", ru="Панель с полосой опасности", en="Hazard Panel", kind="cube", mat="metal", tex="hazard_panel"),
    dict(id="plasteel_vent", ru="Вентиляционная решётка", en="Plasteel Vent", kind="cube", mat="metal", tex="plasteel_vent"),
    dict(id="deck_grating", ru="Палубная решётка", en="Deck Grating", kind="cutout_cube", mat="metal", tex="deck_grating"),
    dict(id="hull_plating_stairs", ru="Ступени из обшивки", en="Hull Plating Stairs", kind="stairs", mat="metal", base="hull_plating"),
    dict(id="hull_plating_slab", ru="Плита из обшивки", en="Hull Plating Slab", kind="slab", mat="metal", base="hull_plating"),
    dict(id="plasteel_panel_stairs", ru="Пласталевые ступени", en="Plasteel Stairs", kind="stairs", mat="metal", base="plasteel_panel"),
    dict(id="plasteel_panel_slab", ru="Пласталевая плита", en="Plasteel Slab", kind="slab", mat="metal", base="plasteel_panel"),
    dict(id="cogitator_bank", ru="Когитаторная стойка", en="Cogitator Bank", kind="orientable", mat="metal", light=6,
         tex=dict(front="cogitator_bank_front", side="cogitator_bank_side", top="plasteel_panel")),
    dict(id="vox_grille", ru="Вокс-решётка", en="Vox Grille", kind="orientable", mat="metal",
         tex=dict(front="vox_grille", side="riveted_plasteel_panel", top="plasteel_panel")),
    dict(id="lumen_wall", ru="Настенный люмен", en="Wall Lumen", kind="parts", mat="lamp", light=14, wall=True,
         shape=(4, 3, 9, 12, 13, 16)),
    dict(id="lumen_ceiling", ru="Подвесной люмен", en="Hanging Lumen", kind="parts", mat="lamp", light=15,
         shape=(4, 2, 4, 12, 16, 12)),
    # --- отсеки крейсера: реактор, охладитель, Поле Геллера
    dict(id="radiation_sign", ru="Знак радиационной опасности", en="Radiation Warning Sign", kind="parts", mat="lamp", wall=True,
         shape=(1, 1, 15, 15, 15, 16)),
    dict(id="emergency_lumen", ru="Аварийный люмен", en="Emergency Lumen", kind="parts", mat="lamp", light=10, wall=True,
         shape=(4, 3, 9, 12, 13, 16)),
    dict(id="purity_seal", ru="Печать чистоты", en="Purity Seal", kind="parts", mat="lamp", wall=True,
         shape=(4, 0, 14, 12, 15, 16)),
    dict(id="coolant_pipe", ru="Труба охладителя", en="Coolant Pipe", kind="pillar", mat="metal",
         tex=dict(side="coolant_pipe", end="coolant_pipe_end")),
    dict(id="geller_conduit", ru="Проводник Поля Геллера", en="Geller Conduit", kind="pillar", mat="metal", light=9,
         tex=dict(side="geller_conduit", end="geller_conduit_end")),
    dict(id="bulkhead_door", ru="Гермодверь", en="Bulkhead Door", kind="door", mat="metal", tex="bulkhead_door"),
    dict(id="boarding_hatch", ru="Внешний люк", en="Boarding Hatch", kind="hatch", mat="metal", tex="boarding_hatch"),
    # --- руды
    dict(id="lead_ore", ru="Свинцовая руда", en="Lead Ore", kind="ore", mat="ore", tex="lead_ore", drop="raw_lead", xp=(0, 2)),
    dict(id="deepslate_lead_ore", ru="Глубинная свинцовая руда", en="Deepslate Lead Ore", kind="ore", mat="deep_ore",
         tex="deepslate_lead_ore", drop="raw_lead", xp=(0, 2)),
    dict(id="lead_block", ru="Свинцовый блок", en="Block of Lead", kind="cube", mat="metal", tex="lead_block"),
    dict(id="radium_ore", ru="Радиевая руда", en="Radium Ore", kind="ore", mat="ore", tex="radium_ore", drop="raw_radium",
         xp=(2, 5), light=7, glow=0x7CFF6A),
    dict(id="adamantium_ore", ru="Адамантиевый сырец", en="Adamantium Ore", kind="ore", mat="hard_ore", tex="adamantium_ore",
         drop="raw_adamantium", xp=(4, 8)),
    dict(id="warpstone_ore", ru="Варп-камень", en="Warpstone Ore", kind="ore", mat="ore", tex="warpstone_ore",
         drop="warpstone_shard", xp=(3, 7), light=5, glow=0xB45CFF),
    dict(id="psycrystal_cluster", ru="Друза псайкристаллов", en="Psycrystal Cluster", kind="cross", mat="crystal", light=6,
         tex="psycrystal_cluster", drop="psycrystal", shape=(3, 0, 3, 13, 12, 13)),
    # --- Кинерис Терциус
    dict(id="ash_block", ru="Пепел", en="Ash", kind="falling", mat="ash", tex="ash_block", color=0xFF807C78),
    dict(id="ash_stone", ru="Пепельный камень", en="Ash Stone", kind="cube", mat="stone", tex="ash_stone"),
    dict(id="ash_stone_bricks", ru="Пепельные кирпичи", en="Ash Stone Bricks", kind="cube", mat="stone", tex="ash_stone_bricks"),
    dict(id="ash_stone_brick_stairs", ru="Ступени из пепельных кирпичей", en="Ash Stone Brick Stairs", kind="stairs", mat="stone",
         base="ash_stone_bricks"),
    dict(id="ash_stone_brick_slab", ru="Плита из пепельных кирпичей", en="Ash Stone Brick Slab", kind="slab", mat="stone",
         base="ash_stone_bricks"),
    dict(id="ash_stone_brick_wall", ru="Стена из пепельных кирпичей", en="Ash Stone Brick Wall", kind="wall", mat="stone",
         base="ash_stone_bricks"),
    dict(id="ash_clay", ru="Пепельная глина", en="Ash Clay", kind="cube", mat="clay", tex="ash_clay"),
    dict(id="vitrified_glass", ru="Остеклованный грунт", en="Vitrified Glass", kind="glass", mat="glass", tex="vitrified_glass"),
    dict(id="amber_vitrified_glass", ru="Янтарный остеклованный грунт", en="Amber Vitrified Glass", kind="glass", mat="glass",
         tex="amber_vitrified_glass"),
    dict(id="smoke_vitrified_glass", ru="Дымчатый остеклованный грунт", en="Smoky Vitrified Glass", kind="glass", mat="glass",
         tex="smoke_vitrified_glass"),
    dict(id="charred_log", ru="Обугленное бревно", en="Charred Log", kind="pillar", mat="wood",
         tex=dict(side="charred_log", end="charred_log_top")),
    dict(id="bone_pile", ru="Груда костей", en="Bone Pile", kind="carpet", mat="bone", tex="bone_pile", shape=(0, 0, 0, 16, 2, 16)),
]

ITEMS = [
    dict(id="raw_lead", ru="Свинцовый сырец", en="Raw Lead"),
    dict(id="lead_ingot", ru="Свинцовый слиток", en="Lead Ingot"),
    dict(id="raw_radium", ru="Сырой радий", en="Raw Radium"),
    dict(id="raw_adamantium", ru="Адамантиевый сырец", en="Raw Adamantium"),
    dict(id="warpstone_shard", ru="Осколок варп-камня", en="Warpstone Shard"),
    dict(id="psycrystal", ru="Псайкристалл", en="Psycrystal"),
]


# ------------------------------------------------------------------ текстуры

def rng_for(name):
    return random.Random(zlib.crc32(name.encode()))


def block_textures():
    r = rng_for
    tex = {
        "hull_plating": T.hull_plating(r("hull")),
        "scorched_hull_plating": T.hull_plating(r("scorch"), base=(44, 40, 38), scorched=True),
        "brass_trim": T.brass_trim(r("brass")),
        "dock_girder": T.dock_girder(r("girder")),
        "dock_girder_top": T.dock_girder(r("girder_top"), top=True),
        "hull_scrap": T.hull_scrap(r("scrap")),
        "plasteel_panel": T.plasteel_panel(r("panel")),
        "riveted_plasteel_panel": T.plasteel_panel(r("rpanel"), rivets=True),
        "hazard_panel": T.hazard_panel(r("hazard")),
        "plasteel_vent": T.plasteel_vent(r("vent")),
        "deck_grating": T.deck_grating(r("grating")),
        "cogitator_bank_side": T.cogitator_side(r("cogside")),
        "vox_grille": T.vox_grille(r("vox")),
        "lead_ore": T.ore(r("lead"), T.STONE, (70, 74, 90), (150, 160, 190)),
        "deepslate_lead_ore": T.ore(r("dlead"), T.DEEPSLATE, (64, 68, 84), (150, 160, 190)),
        "lead_block": T.lead_block(r("leadb")),
        "radium_ore": T.ore(r("radium"), T.ASH_STONE, (60, 130, 50), (190, 255, 150), n=7, glow=True),
        "adamantium_ore": T.ore(r("adam"), (40, 40, 44), (50, 70, 64), (170, 200, 190), n=4),
        "warpstone_ore": T.ore(r("warp"), T.ASH_STONE, (90, 40, 140), (210, 140, 255), n=6, glow=True),
        "psycrystal_cluster": T.crystal_cross(r("psy"), (80, 90, 220), (170, 190, 255)),
        "ash_block": T.ash(r("ash")),
        "ash_stone": T.stone(r("ashstone"), T.ASH_STONE),
        "ash_stone_bricks": T.ash_stone_bricks(r("ashbricks")),
        "ash_clay": T.ash_clay(r("ashclay")),
        "vitrified_glass": T.vitrified(r("vg"), (90, 140, 120)),
        "amber_vitrified_glass": T.vitrified(r("avg"), (200, 130, 40)),
        "smoke_vitrified_glass": T.vitrified(r("svg"), (60, 60, 70)),
        "charred_log": T.charred_bark(r("log")),
        "charred_log_top": T.charred_top(r("logtop")),
        "bone_pile": T.bones(r("bones")),
        "radiation_sign": T.radiation_sign(r("radsign")),
        "bulkhead_door": T.bulkhead(r("bulkhead")),
        "boarding_hatch": T.bulkhead(r("hatch"), stripe=((180, 30, 26), (220, 214, 200))),
        "coolant_pipe": T.coolant_pipe(r("pipe")),
        "coolant_pipe_end": T.coolant_pipe_end(r("pipeend")),
        "geller_conduit": T.geller_conduit(r("conduit")),
        "geller_conduit_end": T.geller_conduit_end(r("conduitend")),
    }
    for name, arr in tex.items():
        save(Image.fromarray(arr, "RGBA"), "block", name)
    frames = T.cogitator_frames(r("cog"))
    strip = np.concatenate(frames, axis=0)
    save(Image.fromarray(strip, "RGBA"), "block", "cogitator_bank_front")
    with open(os.path.join(ASSETS, "textures/block/cogitator_bank_front.png.mcmeta"), "w", encoding="utf-8") as f:
        json.dump({"animation": {"frametime": 5}}, f)
    p = os.path.join(ASSETS, "textures/mob_effect/radiation.png")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    Image.fromarray(T.effect_icon(), "RGBA").save(p)


def item_textures():
    r = rng_for
    icons = {
        "raw_lead": T.nugget_icon((96, 102, 120), (170, 180, 200), r("rawlead")),
        "lead_ingot": T.ingot_icon((110, 118, 136)),
        "raw_radium": T.nugget_icon((70, 150, 60), (200, 255, 160), r("rawrad")),
        "raw_adamantium": T.nugget_icon((50, 64, 60), (170, 200, 190), r("rawadam")),
        "warpstone_shard": T.shard_icon((120, 50, 180), (220, 160, 255)),
        "psycrystal": T.shard_icon((70, 90, 220), (180, 200, 255)),
    }
    for name, arr in icons.items():
        save(Image.fromarray(arr, "RGBA"), "item", name)


def save(img, kind, name):
    p = os.path.join(ASSETS, "textures", kind, name + ".png")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    img.save(p)


# ------------------------------------------------------------------ модели и состояния

def wj(obj, *path):
    p = os.path.join(*path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def bs(name, obj):
    wj(obj, ASSETS, "blockstates", name + ".json")


def model(name, obj):
    wj(obj, ASSETS, "models", "block", name + ".json")


def item_model(name, obj):
    wj(obj, ASSETS, "models", "item", name + ".json")


def wb(t):
    return f"warpbound:block/{t}"


FACINGS = (("north", 0), ("east", 90), ("south", 180), ("west", 270))


def stairs_states(name, base_tex):
    m = wb(name)
    for suffix, parent in (("", "stairs"), ("_inner", "inner_stairs"), ("_outer", "outer_stairs")):
        model(name + suffix, {"parent": f"minecraft:block/{parent}",
                              "textures": {"bottom": wb(base_tex), "top": wb(base_tex), "side": wb(base_tex)}})
    variants = {}
    yrot = {"east": 0, "south": 90, "west": 180, "north": 270}
    for facing in ("east", "north", "south", "west"):
        for half in ("bottom", "top"):
            for shape in ("straight", "inner_left", "inner_right", "outer_left", "outer_right"):
                mm = m + ("_inner" if shape.startswith("inner") else "_outer" if shape.startswith("outer") else "")
                y = yrot[facing]
                if shape in ("inner_left", "outer_left"):
                    y = (y - 90) % 360
                x = 0
                if half == "top":
                    x = 180
                    if shape in ("inner_left", "outer_left"):
                        y = (y + 90) % 360
                    elif shape in ("inner_right", "outer_right"):
                        y = (y + 90) % 360
                v = {"model": mm}
                if x:
                    v["x"] = x
                if y:
                    v["y"] = y
                if x or y:
                    v["uvlock"] = True
                variants[f"facing={facing},half={half},shape={shape}"] = v
    bs(name, {"variants": variants})
    item_model(name, {"parent": m})


def slab_states(name, base_name, base_tex):
    model(name, {"parent": "minecraft:block/slab", "textures": {"bottom": wb(base_tex), "top": wb(base_tex), "side": wb(base_tex)}})
    model(name + "_top", {"parent": "minecraft:block/slab_top",
                          "textures": {"bottom": wb(base_tex), "top": wb(base_tex), "side": wb(base_tex)}})
    bs(name, {"variants": {"type=bottom": {"model": wb(name)}, "type=top": {"model": wb(name + "_top")},
                           "type=double": {"model": wb(base_name)}}})
    item_model(name, {"parent": wb(name)})


def wall_states(name, base_tex):
    t = {"wall": wb(base_tex)}
    model(name + "_post", {"parent": "minecraft:block/template_wall_post", "textures": t})
    model(name + "_side", {"parent": "minecraft:block/template_wall_side", "textures": t})
    model(name + "_side_tall", {"parent": "minecraft:block/template_wall_side_tall", "textures": t})
    model(name + "_inventory", {"parent": "minecraft:block/wall_inventory", "textures": t})
    mp = [{"when": {"up": "true"}, "apply": {"model": wb(name + "_post")}}]
    for side, y in (("north", 0), ("east", 90), ("south", 180), ("west", 270)):
        for h, suf in (("low", "_side"), ("tall", "_side_tall")):
            a = {"model": wb(name + suf), "uvlock": True}
            if y:
                a["y"] = y
            mp.append({"when": {side: h}, "apply": a})
    bs(name, {"multipart": mp})
    item_model(name, {"parent": wb(name + "_inventory")})


def lumen_parts(name):
    glow = {"deco": {"north": lambda r, S, p: r.__setitem__((Ellipsis, slice(0, 3)), p["glow2"])}}
    if name == "radiation_sign":
        sign = np.asarray(Image.open(os.path.join(ASSETS, "textures/block/radiation_sign.png")))

        def paste(r, S, p):
            h, w = r.shape[:2]
            r[...] = np.asarray(Image.fromarray(sign).resize((w, h), Image.NEAREST))
        parts = [([1, 1, 15], [14, 14, 1], "brass", {"deco": {"north": paste}}),
                 ([3, 15, 15.5], [1, 1, 0.5], "dark"), ([12, 15, 15.5], [1, 1, 0.5], "dark")]
        build_parts(name, name + "_model", parts, MECH)
        return
    if name == "emergency_lumen":
        red = {"deco": {"north": lambda r, S, p: r.__setitem__((Ellipsis, slice(0, 3)), (255, 60, 40))}}
        parts = [
            ([6, 6, 14], [4, 4, 2], "dark"),
            ([5, 4, 10], [6, 8, 4], "dark"),
            ([5.5, 4.5, 9.5], [5, 7, 0.5], "metal", red),
            ([4.5, 3, 9], [7, 1, 5], "brass"), ([4.5, 12, 9], [7, 1, 5], "brass"),
            ([7.5, 3.5, 9], [1, 9, 0.5], "dark"),
        ]
        build_parts(name, name + "_model", parts, MECH)
        return
    if name == "purity_seal":
        fill = lambda c: {"deco": {"north": lambda r, S, p: r.__setitem__((Ellipsis, slice(0, 3)), c)}}

        def wax(r, S, p):
            h, w = r.shape[:2]
            r[..., :3] = (120, 18, 22)
            r[1:-1, 1:-1, :3] = (150, 26, 30)
            r[h // 2 - 1:h // 2 + 1, w // 2 - 1:w // 2 + 1, :3] = (210, 170, 70)
        parts = [
            ([5.5, 1, 15.3], [2, 9, 0.5], "metal", fill((214, 200, 160))),
            ([8.5, 2.5, 15.3], [2, 7.5, 0.5], "metal", fill((200, 186, 146))),
            ([5, 9, 14.5], [6, 6, 1.5], "red", {"deco": {"north": wax}}),
        ]
        build_parts(name, name + "_model", parts, MECH)
        return
    if name == "lumen_wall":
        parts = [
            ([6, 6, 14], [4, 4, 2], "brass"),
            ([7, 7, 10.5], [2, 2, 3.5], "dark"),
            ([4.5, 4, 9], [7, 9, 2], "dark"),
            ([5, 4.5, 8.5], [6, 8, 0.5], "metal", glow),
            ([4, 3, 8], [8, 1, 3], "brass"), ([4, 12, 8], [8, 1, 3], "brass"),
            ([6.5, 3.5, 8], [0.5, 9, 0.5], "dark"), ([9, 3.5, 8], [0.5, 9, 0.5], "dark"),
        ]
    else:
        parts = [
            ([7.5, 11, 7.5], [1, 5, 1], "dark"),
            ([6, 10, 6], [4, 1, 4], "brass"),
            ([4.5, 4, 4.5], [7, 6, 7], "dark"),
            ([5, 2.5, 5], [6, 1.5, 6], "metal", {"deco": {"down": lambda r, S, p: r.__setitem__((Ellipsis, slice(0, 3)), p["glow2"])}}),
            ([4, 7, 4], [8, 1, 8], "brass"),
        ]
    pal = dict(MECH, glow2=(255, 214, 140))
    build_parts(name, name + "_model", parts, pal)


def models_and_states():
    for b in BLOCKS:
        n, kind = b["id"], b["kind"]
        if kind in ("door", "hatch"):
            model(n, {"parent": "minecraft:block/cube_all", "textures": {"all": wb(b["tex"])}})
            bs(n, {"variants": {"": {"model": wb(n)}}})
            item_model(n, {"parent": wb(n)})
        elif kind in ("cube", "ore", "falling", "glass", "cutout_cube"):
            if not b.get("existing"):
                model(n, {"parent": "minecraft:block/cube_all", "textures": {"all": wb(b["tex"])}})
                bs(n, {"variants": {"": {"model": wb(n)}}})
                item_model(n, {"parent": wb(n)})
        elif kind == "column":
            model(n, {"parent": "minecraft:block/cube_column", "textures": {"end": wb(b["tex"] + "_top"), "side": wb(b["tex"])}})
            bs(n, {"variants": {"": {"model": wb(n)}}})
            item_model(n, {"parent": wb(n)})
        elif kind == "pillar":
            t = {"end": wb(b["tex"]["end"]), "side": wb(b["tex"]["side"])}
            model(n, {"parent": "minecraft:block/cube_column", "textures": t})
            model(n + "_horizontal", {"parent": "minecraft:block/cube_column_horizontal", "textures": t})
            bs(n, {"variants": {"axis=y": {"model": wb(n)}, "axis=z": {"model": wb(n + "_horizontal"), "x": 90},
                                "axis=x": {"model": wb(n + "_horizontal"), "x": 90, "y": 90}}})
            item_model(n, {"parent": wb(n)})
        elif kind == "orientable":
            t = b["tex"]
            model(n, {"parent": "minecraft:block/orientable", "textures": {"front": wb(t["front"]), "side": wb(t["side"]), "top": wb(t["top"])}})
            bs(n, {"variants": {f"facing={d}": ({"model": wb(n), "y": y} if y else {"model": wb(n)}) for d, y in FACINGS}})
            item_model(n, {"parent": wb(n)})
        elif kind == "stairs":
            stairs_states(n, b["base"])
        elif kind == "slab":
            slab_states(n, b["base"], b["base"])
        elif kind == "wall":
            wall_states(n, b["base"])
        elif kind == "cross":
            model(n, {"parent": "minecraft:block/cross", "textures": {"cross": wb(b["tex"])}})
            bs(n, {"variants": {"": {"model": wb(n)}}})
            item_model(n, {"parent": "minecraft:item/generated", "textures": {"layer0": wb(b["tex"])}})
        elif kind == "carpet":
            model(n, {"parent": "minecraft:block/carpet", "textures": {"wool": wb(b["tex"])}})
            bs(n, {"variants": {"": {"model": wb(n)}}})
            item_model(n, {"parent": "minecraft:item/generated", "textures": {"layer0": wb(b["tex"])}})
        elif kind == "parts":
            lumen_parts(n)
            if b.get("wall"):
                bs(n, {"variants": {f"facing={d}": ({"model": wb(n), "y": y} if y else {"model": wb(n)}) for d, y in FACINGS}})
            else:
                bs(n, {"variants": {"": {"model": wb(n)}}})
            item_model(n, {"parent": wb(n)})
    for it in ITEMS:
        item_model(it["id"], {"parent": "minecraft:item/generated", "textures": {"layer0": f"warpbound:item/{it['id']}"}})


# ------------------------------------------------------------------ лут, рецепты, теги

SURVIVES = [{"condition": "minecraft:survives_explosion"}]
SILK = {"condition": "minecraft:match_tool", "predicate": {"predicates": {"minecraft:enchantments": [
    {"enchantments": "minecraft:silk_touch", "levels": {"min": 1}}]}}}


def loot(name, pool):
    wj({"type": "minecraft:block", "pools": [pool], "random_sequence": f"warpbound:blocks/{name}"},
       DATA, "warpbound", "loot_table", "blocks", name + ".json")


def self_pool(name):
    return {"rolls": 1, "bonus_rolls": 0, "entries": [{"type": "minecraft:item", "name": f"warpbound:{name}"}], "conditions": SURVIVES}


def loot_tables():
    for b in BLOCKS:
        n, kind = b["id"], b["kind"]
        if b.get("existing"):
            continue
        if kind in ("ore", "cross"):
            drop = {"type": "minecraft:item", "name": f"warpbound:{b['drop']}", "functions": [
                {"function": "minecraft:apply_bonus", "enchantment": "minecraft:fortune", "formula": "minecraft:ore_drops"},
                {"function": "minecraft:explosion_decay"}]}
            if kind == "cross":
                drop["functions"].insert(0, {"function": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": 1, "max": 3}})
            loot(n, {"rolls": 1, "bonus_rolls": 0, "entries": [{"type": "minecraft:alternatives", "children": [
                {"type": "minecraft:item", "name": f"warpbound:{n}", "conditions": [SILK]}, drop]}]})
        elif kind == "glass":
            loot(n, {"rolls": 1, "bonus_rolls": 0, "entries": [{"type": "minecraft:item", "name": f"warpbound:{n}"}], "conditions": [SILK]})
        elif kind == "slab":
            loot(n, {"rolls": 1, "bonus_rolls": 0, "entries": [{"type": "minecraft:item", "name": f"warpbound:{n}", "functions": [
                {"function": "minecraft:set_count", "count": 2, "add": False, "conditions": [
                    {"condition": "minecraft:block_state_property", "block": f"warpbound:{n}", "properties": {"type": "double"}}]},
                {"function": "minecraft:explosion_decay"}]}]})
        else:
            loot(n, self_pool(n))


def recipe(name, obj):
    wj(obj, DATA, "warpbound", "recipe", name + ".json")


def shaped(name, pattern, key, result, count=1):
    recipe(name, {"type": "minecraft:crafting_shaped", "category": "building", "pattern": pattern,
                  "key": {k: ({"tag": v[1:]} if v.startswith("#") else {"item": v}) for k, v in key.items()},
                  "result": {"id": result, "count": count}})


def shapeless(name, items, result, count=1):
    recipe(name, {"type": "minecraft:crafting_shapeless", "category": "building",
                  "ingredients": [{"item": i} for i in items], "result": {"id": result, "count": count}})


def cutting(name, src, result, count=1):
    recipe(name, {"type": "minecraft:stonecutting", "ingredient": {"item": src}, "result": {"id": result, "count": count}})


def recipes():
    w = "warpbound:"
    for b in BLOCKS:
        n, base = b["id"], b.get("base")
        if b["kind"] == "stairs":
            shaped(n, ["#  ", "## ", "###"], {"#": w + base}, w + n, 4)
            cutting(n + "_stonecutting", w + base, w + n)
        elif b["kind"] == "slab":
            shaped(n, ["###"], {"#": w + base}, w + n, 6)
            cutting(n + "_stonecutting", w + base, w + n, 2)
        elif b["kind"] == "wall":
            shaped(n, ["###", "###"], {"#": w + base}, w + n, 6)
            cutting(n + "_stonecutting", w + base, w + n)
    shaped("plasteel_panel", ["PP", "PP"], {"P": w + "plasteel_plate"}, w + "plasteel_panel", 4)
    for v in ("riveted_plasteel_panel", "plasteel_vent"):
        cutting(v, w + "plasteel_panel", w + v)
    shapeless("hazard_panel", [w + "plasteel_panel", "minecraft:yellow_dye", "minecraft:black_dye"], w + "hazard_panel")
    shaped("deck_grating", ["BPB"], {"B": "minecraft:iron_bars", "P": w + "plasteel_plate"}, w + "deck_grating", 4)
    shaped("cogitator_bank", ["PRP", "GCG", "PRP"], {"P": w + "plasteel_plate", "R": "minecraft:redstone",
                                                     "G": "minecraft:glass_pane", "C": "minecraft:copper_ingot"}, w + "cogitator_bank")
    shaped("vox_grille", [" I ", "ICI", " I "], {"I": "minecraft:iron_bars", "C": "minecraft:copper_ingot"}, w + "vox_grille")
    shapeless("lumen_wall", [w + "plasteel_plate", "minecraft:glowstone_dust", "minecraft:glowstone_dust"], w + "lumen_wall", 2)
    shaped("lumen_ceiling", ["C", "P", "G"], {"C": "minecraft:chain", "P": w + "plasteel_plate", "G": "minecraft:glowstone"},
           w + "lumen_ceiling", 2)
    shaped("ash_stone_bricks", ["##", "##"], {"#": w + "ash_stone"}, w + "ash_stone_bricks", 4)
    cutting("ash_stone_bricks_stonecutting", w + "ash_stone", w + "ash_stone_bricks")
    for kind in ("smelting", "blasting"):
        recipe(f"lead_ingot_from_{kind}", {"type": f"minecraft:{kind}", "category": "misc", "ingredient": {"item": w + "raw_lead"},
                                           "result": {"id": w + "lead_ingot"}, "experience": 0.7,
                                           "cookingtime": 200 if kind == "smelting" else 100})
    shaped("lead_block", ["###", "###", "###"], {"#": w + "lead_ingot"}, w + "lead_block")
    shapeless("lead_ingot_from_block", [w + "lead_block"], w + "lead_ingot", 9)
    # лом в горне обломков — два слитка пластали
    wj({"type": "warpbound:salvaging", "category": "misc", "ingredient": {"item": w + "hull_scrap"},
        "result": {"id": w + "plasteel_ingot", "count": 2}, "experience": 0.2, "cookingtime": 260},
       DATA, "warpbound", "recipe", "salvaging", "plasteel_from_scrap.json")


def merge_tag(path, values):
    p = os.path.join(DATA, *path)
    old = []
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            old = json.load(f).get("values", [])
    out = old + [v for v in values if v not in old]
    wj({"replace": False, "values": out}, p)


def tags():
    by_tool, by_level = {}, {}
    for b in BLOCKS:
        _, tool, level = MATS[b["mat"]]
        if tool:
            by_tool.setdefault(tool, []).append("warpbound:" + b["id"])
        if level:
            by_level.setdefault(level, []).append("warpbound:" + b["id"])
    for tool, ids in by_tool.items():
        merge_tag(("minecraft", "tags", "block", "mineable", tool + ".json"), ids)
    for level, ids in by_level.items():
        merge_tag(("minecraft", "tags", "block", f"needs_{level}_tool.json"), ids)
    merge_tag(("minecraft", "tags", "block", "mineable", "pickaxe.json"), ["warpbound:mechanicus_forge"])
    merge_tag(("minecraft", "tags", "block", "walls.json"), ["warpbound:ash_stone_brick_wall"])
    merge_tag(("minecraft", "tags", "block", "stairs.json"), [f"warpbound:{b['id']}" for b in BLOCKS if b["kind"] == "stairs"])
    merge_tag(("minecraft", "tags", "block", "slabs.json"), [f"warpbound:{b['id']}" for b in BLOCKS if b["kind"] == "slab"])
    merge_tag(("minecraft", "tags", "block", "logs.json"), ["warpbound:charred_log"])
    merge_tag(("c", "tags", "block", "ores.json"), [f"warpbound:{b['id']}" for b in BLOCKS if b["kind"] == "ore"])


# ------------------------------------------------------------------ Java

def const(n):
    return n.upper()


def java_expr(b):
    props = MATS[b["mat"]][0]
    if b.get("light"):
        props += f".lightLevel(s -> {b['light']})"
    k = b["kind"]
    if k in ("cube", "column"):
        return f"new Block({props})"
    if k == "door":
        return f"new BulkheadDoorBlock({props}.noOcclusion())"
    if k == "hatch":
        return f"new BoardingHatchBlock({props}.noOcclusion())"
    if k == "cutout_cube":
        return f"new TransparentBlock({props}.noOcclusion())"
    if k == "glass":
        return f"new TransparentBlock({props})"
    if k == "pillar":
        return f"new RotatedPillarBlock({props})"
    if k == "orientable":
        return f"new FacingDecorBlock({props}, false, Shapes.block())"
    if k == "ore":
        xp = b["xp"]
        if b.get("glow"):
            return f"new GlowingOreBlock(UniformInt.of({xp[0]}, {xp[1]}), 0x{b['glow']:06X}, {props})"
        return f"new DropExperienceBlock(UniformInt.of({xp[0]}, {xp[1]}), {props})"
    if k == "falling":
        return f"new ColoredFallingBlock(new ColorRGBA(0x{b['color']:08X}), {props})"
    if k == "stairs":
        base = next(x for x in BLOCKS if x["id"] == b["base"])
        owner = "WarpboundBlocks." if base.get("existing") else ""
        return f"new StairBlock({owner}{const(b['base'])}.defaultBlockState(), {props})"
    if k == "slab":
        return f"new SlabBlock({props})"
    if k == "wall":
        return f"new WallBlock({props}.forceSolidOn())"
    if k in ("cross", "carpet"):
        s = b["shape"]
        return f"new DecorBlock({props}{'.noCollission()' if k == 'cross' else ''}, Block.box({s[0]}, {s[1]}, {s[2]}, {s[3]}, {s[4]}, {s[5]}))"
    if k == "parts":
        s = b["shape"]
        box = f"Block.box({s[0]}, {s[1]}, {s[2]}, {s[3]}, {s[4]}, {s[5]})"
        if b.get("wall"):
            return f"new FacingDecorBlock({props}, true, {box})"
        return f"new DecorBlock({props}, {box})"
    raise ValueError(k)


def java():
    lines = []
    lines.append("package dev.warpbound.core;\n")
    lines.append("import dev.warpbound.Warpbound;")
    lines.append("import dev.warpbound.ship.block.BoardingHatchBlock;")
    lines.append("import dev.warpbound.ship.block.BulkheadDoorBlock;")
    lines.append("import net.minecraft.core.Registry;")
    lines.append("import net.minecraft.core.registries.BuiltInRegistries;")
    lines.append("import net.minecraft.util.ColorRGBA;")
    lines.append("import net.minecraft.util.valueproviders.UniformInt;")
    lines.append("import net.minecraft.world.item.BlockItem;")
    lines.append("import net.minecraft.world.item.Item;")
    lines.append("import net.minecraft.world.level.block.*;")
    lines.append("import net.minecraft.world.level.block.state.BlockBehaviour;")
    lines.append("import net.minecraft.world.level.material.MapColor;")
    lines.append("import net.minecraft.world.phys.shapes.Shapes;\n")
    lines.append("import java.util.List;\n")
    lines.append("/**")
    lines.append(" * Набор блоков: корабельная отделка, руды, камень и грунт Кинериса.")
    lines.append(" * СГЕНЕРИРОВАНО tools/blocks/gen_block_set.py — руками не править, менять спецификацию в скрипте.")
    lines.append(" * Блоки, которые уже были в WarpboundBlocks (обшивка, латунь, балка), здесь не регистрируются.")
    lines.append(" */")
    lines.append("public final class WarpboundBuildingBlocks {")
    for b in BLOCKS:
        if b.get("existing"):
            continue
        lines.append(f"    public static final Block {const(b['id'])} = block(\"{b['id']}\", {java_expr(b)});")
    lines.append("")
    for it in ITEMS:
        lines.append(f"    public static final Item {const(it['id'])} = item(\"{it['id']}\");")
    lines.append("")
    blocks = [const(b["id"]) for b in BLOCKS if not b.get("existing")]
    lines.append("    /** Все блоки набора — для вкладки творческого режима. */")
    lines.append("    public static final List<Block> ALL = List.of(" + ", ".join(blocks) + ");")
    lines.append("    public static final List<Item> ITEMS = List.of(" + ", ".join(const(i["id"]) for i in ITEMS) + ");")
    cut = [const(b["id"]) for b in BLOCKS if b["kind"] in ("cutout_cube", "cross", "carpet", "parts") and not b.get("existing")]
    tr = [const(b["id"]) for b in BLOCKS if b["kind"] == "glass"]
    lines.append("    /** Блоки с прозрачными пикселями (cutout) и полупрозрачные (стекло) — для слоёв рендера на клиенте. */")
    lines.append("    public static final List<Block> CUTOUT = List.of(" + ", ".join(cut) + ");")
    lines.append("    public static final List<Block> TRANSLUCENT = List.of(" + ", ".join(tr) + ");")
    lines.append("")
    lines.append("    private WarpboundBuildingBlocks() {\n    }\n")
    lines.append("    private static Block block(String name, Block block) {")
    lines.append("        Registry.register(BuiltInRegistries.BLOCK, Warpbound.id(name), block);")
    lines.append("        Registry.register(BuiltInRegistries.ITEM, Warpbound.id(name), new BlockItem(block, new Item.Properties()));")
    lines.append("        return block;\n    }\n")
    lines.append("    private static Item item(String name) {")
    lines.append("        return Registry.register(BuiltInRegistries.ITEM, Warpbound.id(name), new Item(new Item.Properties()));\n    }\n")
    lines.append("    /** Вызывается из Warpbound.onInitialize, чтобы класс загрузился до заморозки реестров. */")
    lines.append("    public static void register() {\n    }")
    lines.append("}")
    with open(JAVA, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    lang = ["package dev.warpbound.client.datagen;\n",
            "import net.fabricmc.fabric.api.datagen.v1.provider.FabricLanguageProvider;\n",
            "/** Переводы набора блоков. СГЕНЕРИРОВАНО tools/blocks/gen_block_set.py — руками не править. */",
            "final class BuildingBlockLang {", "    private BuildingBlockLang() {\n    }\n"]
    for lang_id in ("ru", "en"):
        lang.append(f"    static void {lang_id}(FabricLanguageProvider.TranslationBuilder builder) {{")
        for b in BLOCKS:
            if not b.get("existing"):
                lang.append(f"        builder.add(\"block.warpbound.{b['id']}\", \"{b[lang_id]}\");")
        for it in ITEMS:
            lang.append(f"        builder.add(\"item.warpbound.{it['id']}\", \"{it[lang_id]}\");")
        lang.append("    }\n")
    lang.append("}")
    with open(LANG, "w", encoding="utf-8") as f:
        f.write("\n".join(lang) + "\n")


if __name__ == "__main__":
    block_textures()
    item_textures()
    models_and_states()
    loot_tables()
    recipes()
    tags()
    java()
    print("блоков:", len(BLOCKS), "предметов:", len(ITEMS))
