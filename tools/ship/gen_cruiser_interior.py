#!/usr/bin/env python3
"""
Интерьер лёгкого крейсера типа «Неустрашимый» (10 отсеков) — корабль Сезона 1.

    python3 tools/ship/gen_cruiser_interior.py

Пишет data/warpbound/structure/interior/cruiser/<отсек>.nbt и data/warpbound/ship_layout/light_cruiser.json.

От кормы к носу (+Z): двигательный отсек → реакторный зал → хребет-коридор с шестью боковыми отсеками
(генераторные Поля Геллера по бортам, казарма и трюм, телепортариум и часовня) → мостик.
Крупное оборудование (реактор, генераторы Поля, стол, ауспики, пульт) — ядро + невидимые части вокруг.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_interior import (CANDLE, CARPET, DATA, FLOOR, GRATE, LIGHT, PART, WALL2, WINDOW, Room,  # noqa: E402
                          write_room)

LEAD = "warpbound:lead_block"
HAZARD = "warpbound:hazard_panel"
GRATING = "warpbound:deck_grating"
PANEL = "warpbound:plasteel_panel"
RIVETED = "warpbound:riveted_plasteel_panel"
VENT = "warpbound:plasteel_vent"
HULL = "warpbound:hull_plating"
BRASS = "warpbound:brass_trim"
GOLD = "minecraft:gold_block"
LUMEN_C = "warpbound:lumen_ceiling"
SOUL = "minecraft:soul_lantern"
MAGMA = "minecraft:magma_block"


def lumen(d):
    return f"warpbound:lumen_wall[facing={d}]"


def red(d):
    return f"warpbound:emergency_lumen[facing={d}]"


def rad(d):
    return f"warpbound:radiation_sign[facing={d}]"


def cog(d):
    return f"warpbound:cogitator_bank[facing={d}]"


def pipe(axis="y"):
    return f"warpbound:coolant_pipe[axis={axis}]"


def conduit(axis="y"):
    return f"warpbound:geller_conduit[axis={axis}]"


def fixture(block, facing):
    return f"warpbound:{block}[facing={facing}]"


def big(r, x, y, z, block, facing, cells):
    """Крупное оборудование: части по списку смещений, ядро последним (поверх своей клетки)."""
    for dx, dy, dz in cells:
        r.put(x + dx, y + dy, z + dz, PART)
    r.put(x, y, z, fixture(block, facing))


def ceiling_lumens(r, every=4):
    for z in range(2, r.l - 1, every):
        r.put(r.w // 2, r.h - 2, z, LUMEN_C)


# ---------------------------------------------------------------- отсеки

def engine_room():
    r = Room("cruiser/engine_room", 15, 9, 11)
    r.shell()
    r.door("bow", 7)
    # варп-двигатель: синее пламя за решётками у кормовой стены, плазменные двигатели по бокам
    for x in (5, 7, 9):
        for y in (1, 2, 3, 4):
            r.put(x, y, 1, SOUL if y in (2, 3) else GRATE)
    for x in (2, 12):
        for y in (1, 2, 3):
            r.put(x, y, 1, MAGMA)
            r.put(x, y, 2, GRATE)
    for x in range(3, 12):
        r.put(x, 5, 1, WALL2)
        r.put(x, 0, 2, HAZARD)
    # кормовой генератор Поля и проводники к нему вдоль потолка
    big(r, 7, 1, 6, "geller_node", "north", [(0, 1, 0), (0, 2, 0)])
    for z in range(2, r.l - 1):
        r.put(7, r.h - 2, z, conduit("z"))
    # трубы охладителя в углах, когитаторы и мостки
    for x, z in ((1, 1), (13, 1), (1, 9), (13, 9)):
        for y in range(1, r.h - 1):
            r.put(x, y, z, pipe())
    r.put(1, 1, 5, cog("east"))
    r.put(13, 1, 5, cog("west"))
    for z in range(3, 10):
        r.put(7, 0, z, GRATING)
    r.put(1, 4, 5, red("east"))
    r.put(13, 4, 5, red("west"))
    return r


def reactor_room():
    r = Room("cruiser/reactor_room", 17, 10, 15)
    r.shell(wall=WALL2)
    r.door("stern", 8)
    r.door("bow", 8)
    cx, cz = 8, 7
    # свинцовая защита кольцом с проходами по оси корабля, жёлто-чёрная разметка за ней
    for x in range(cx - 4, cx + 5):
        for z in range(cz - 4, cz + 5):
            ring = max(abs(x - cx), abs(z - cz)) == 4
            if ring and abs(x - cx) > 1:
                r.put(x, 1, z, LEAD)
                r.put(x, 2, z, LEAD if (x + z) % 2 else GRATE)
    for x in range(cx - 5, cx + 6):
        for z in range(cz - 5, cz + 6):
            if max(abs(x - cx), abs(z - cz)) == 5:
                r.put(x, 0, z, HAZARD)
    # реактор 3×3×4
    cells = [(dx, dy, dz) for dx in (-1, 0, 1) for dy in (0, 1, 2, 3) for dz in (-1, 0, 1)]
    big(r, cx, 1, cz, "reactor_core", "north", cells)
    # трубы охладителя: стойки по углам защиты и магистраль под потолком к стенам
    for x, z in ((cx - 4, cz - 4), (cx + 4, cz - 4), (cx - 4, cz + 4), (cx + 4, cz + 4)):
        for y in range(3, r.h - 1):
            r.put(x, y, z, pipe())
    for x in range(1, r.w - 1):
        r.put(x, r.h - 2, cz - 4, pipe("x"))
        r.put(x, r.h - 2, cz + 4, pipe("x"))
    # пульт реакторщика, знаки радиации, аварийные лампы
    r.put(1, 1, 3, cog("east"))
    r.put(1, 1, 11, cog("east"))
    r.put(15, 1, 3, cog("west"))
    r.put(15, 1, 11, cog("west"))
    for z in (4, 10):
        r.put(1, 3, z, rad("east"))
        r.put(15, 3, z, rad("west"))
    for x in (4, 12):
        r.put(x, 3, 1, rad("south"))
        r.put(x, 3, 13, rad("north"))
    for z in (2, 7, 12):
        r.put(1, 5, z, red("east"))
        r.put(15, 5, z, red("west"))
    for x in (2, 14):
        for z in (1, 13):
            r.put(x, 1, z, VENT)
    return r


def spine():
    r = Room("cruiser/spine", 7, 7, 31)
    r.shell()
    r.door("stern", 3)
    r.door("bow", 3)
    for z in (5, 15, 25):
        r.door("port", z)
        r.door("star", z)
    for z in range(1, 30):
        r.put(3, 0, z, "minecraft:red_concrete" if z % 2 else FLOOR)
        # проводники Поля по верхним углам — синий свет вдоль всего хребта
        r.put(1, 5, z, conduit("z"))
        r.put(5, 5, z, conduit("z"))
    ceiling_lumens(r, 5)
    for z in (10, 20):
        r.put(1, 1, z, cog("east"))
        r.put(5, 1, z, cog("west"))
        r.put(1, 3, z, lumen("east"))
        r.put(5, 3, z, lumen("west"))
    return r


def geller_room(side):
    port = side == "port"
    r = Room(f"cruiser/geller_{side}", 11, 8, 11)
    r.shell()
    r.door("star" if port else "port", 5)
    wall_x = 1 if port else 9
    facing = "east" if port else "west"
    for z in (2, 5, 8):
        big(r, wall_x, 1, z, "geller_node", facing, [(0, 1, 0), (0, 2, 0)])
        for y in range(4, r.h - 1):
            r.put(wall_x, y, z, conduit())
    for z in range(1, r.l - 1):
        r.put(wall_x, r.h - 2, z, conduit("z"))
    for x in range(1, r.w - 1):
        r.put(x, 0, 5, GRATING)
    r.put(5, 1, 1, cog("south"))
    r.put(5, 1, 9, cog("north"))
    r.portholes(side, every=3, y=4)
    ceiling_lumens(r, 4)
    return r


def quarters():
    r = Room("cruiser/quarters", 11, 6, 9)
    r.shell()
    r.door("star", 4)
    for z in (1, 3, 5, 7):
        r.put(1, 1, z, "minecraft:red_bed[facing=west,part=head]")
        r.put(2, 1, z, "minecraft:red_bed[facing=west,part=foot]")
        if z in (3, 7):
            r.put(1, 3, z, lumen("east"))
    for z in (1, 3, 5, 7):
        r.put(9, 1, z, "minecraft:barrel[facing=west]")
        r.put(9, 2, z, "minecraft:barrel[facing=west]")
    r.put(5, 1, 4, "minecraft:polished_deepslate_slab[type=bottom]")
    r.put(5, 2, 4, CANDLE)
    ceiling_lumens(r, 4)
    return r


def cargo():
    r = Room("cruiser/cargo", 11, 7, 9)
    r.shell()
    r.door("port", 4)
    for x in range(1, r.w - 1):
        for z in range(1, r.l - 1):
            r.put(x, 0, z, GRATING if (x + z) % 2 else FLOOR)
    for x, z in ((8, 1), (8, 2), (9, 1), (9, 2), (8, 6), (9, 6), (9, 7), (2, 7), (3, 7)):
        r.put(x, 1, z, "minecraft:barrel[facing=up]")
    for x, z in ((8, 1), (9, 2), (9, 6)):
        r.put(x, 2, z, "minecraft:barrel[facing=up]")
    r.put(2, 1, 1, "minecraft:chest[facing=south]")
    r.put(3, 1, 1, "minecraft:chest[facing=south]")
    for x in (3, 7):
        for y in range(3, r.h - 1):
            r.put(x, y, 4, "minecraft:chain")
    r.put(1, 3, 4, HAZARD)
    ceiling_lumens(r, 4)
    return r


def teleportarium():
    r = Room("cruiser/teleportarium", 9, 7, 9)
    r.shell()
    r.door("star", 4)
    cells = [(dx, 0, dz) for dx in (-1, 0, 1) for dz in (-1, 0, 1)]
    big(r, 4, 0, 4, "teleportarium_pad", "south", cells)
    for x, z in ((1, 1), (7, 1), (1, 7), (7, 7)):
        r.put(x, 1, z, GRATE)
        r.put(x, 2, z, conduit())
        r.put(x, 3, z, LIGHT)
    r.put(4, 1, 1, cog("south"))
    return r


def chapel():
    r = Room("cruiser/chapel", 9, 8, 9)
    r.shell(wall=WALL2)
    r.door("port", 4)
    r.put(7, 1, 4, "minecraft:lectern[facing=west]")
    for z in (2, 6):
        r.put(7, 1, z, CANDLE)
        r.put(7, 2, z, CANDLE)
    for x in range(1, 7):
        r.put(x, 1, 4, CARPET)
    # аквила на алтарной стене и витражи
    for y, xs in ((3, (3, 4, 5)), (4, (2, 3, 4, 5, 6)), (5, (4,))):
        for z in xs:
            r.put(8, y, z, GOLD)
    for z in (1, 7):
        for y in (3, 4, 5):
            r.put(8, y, z, "minecraft:orange_stained_glass")
    return r


def bridge():
    r = Room("cruiser/bridge", 21, 12, 19)
    r.shell(wall=WALL2)
    r.door("stern", 10)
    # панорамное окно в нос и узкие иллюминаторы по бортам
    for x in range(3, 18):
        for y in range(3, 10):
            r.put(x, y, 18, WINDOW)
    r.portholes("port", every=3, y=5)
    r.portholes("star", every=3, y=5)
    # помост капитана: ступени, трон смотрит в нос
    for x in range(7, 14):
        for z in range(3, 8):
            r.put(x, 1, z, "minecraft:polished_deepslate")
    for x in range(7, 14):
        r.put(x, 1, 8, "minecraft:polished_blackstone_stairs[facing=north]")
    r.put(10, 2, 5, "warpbound:command_throne[facing=south]")
    # командный пульт перед троном (оператор стоит на помосте и смотрит в нос)
    big(r, 10, 2, 7, "command_console", "north", [(-1, 0, 0), (1, 0, 0)])
    # навигационный стол 3×2 и ауспики по бокам
    big(r, 10, 1, 12, "nav_table", "north", [(dx, 0, dz) for dx in (-1, 0, 1) for dz in (0, 1)])
    big(r, 5, 1, 13, "auspex", "east", [(0, 1, 0)])
    big(r, 15, 1, 13, "auspex", "west", [(0, 1, 0)])
    # когитаторы вдоль бортов, люмены, ковровая дорожка
    for z in range(3, 16, 3):
        r.put(1, 1, z, cog("east"))
        r.put(19, 1, z, cog("west"))
        r.put(1, 4, z, lumen("east"))
        r.put(19, 4, z, lumen("west"))
    for z in range(1, 3):
        r.put(10, 0, z, "minecraft:red_concrete")
    for z in range(9, 17):
        if z not in (12, 13):
            r.put(10, 0, z, "minecraft:red_concrete")
    # знамёна-аквилы над окном
    for x in (2, 18):
        for y in range(4, 10):
            r.put(x, y, 17, "minecraft:red_wool")
        r.put(x, 10, 17, GOLD)
    ceiling_lumens(r, 4)
    return r


LAYOUT = [
    (engine_room(), (-7, 0, -47)),
    (reactor_room(), (-8, 0, -36)),
    (spine(), (-3, 0, -21)),
    (geller_room("port"), (-14, 0, -21)),
    (geller_room("star"), (4, 0, -21)),
    (quarters(), (-14, 0, -10)),
    (cargo(), (4, 0, -10)),
    (teleportarium(), (-12, 0, 0)),
    (chapel(), (4, 0, 0)),
    (bridge(), (-10, 0, 10)),
]
SPAWN = [0, 1, -6]          # середина хребта
REACTOR = [0, 1, -29]       # ядро реактора: реакторный зал (-8, 0, -36) + (8, 1, 7)


def main():
    for room, _ in LAYOUT:
        write_room(room)
    layout = {
        "compartments": [{"structure": f"warpbound:interior/{room.name}", "offset": list(off)} for room, off in LAYOUT],
        "spawn": SPAWN,
        "reactor": REACTOR,
    }
    out = DATA / "ship_layout/light_cruiser.json"
    out.write_text(json.dumps(layout, indent=2) + "\n", encoding="utf-8")
    print("cruiser rooms:", len(LAYOUT), "blocks:", sum(len(r.cells) for r, _ in LAYOUT))


if __name__ == "__main__":
    main()
