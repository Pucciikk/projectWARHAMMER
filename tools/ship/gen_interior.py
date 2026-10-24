#!/usr/bin/env python3
"""
Интерьер фрегата v1 из отсеков. Каждый отсек — отдельная структура .nbt, а раскладка
корабля (какие отсеки и где) — JSON. Позже модули корабля будут добавлять свои отсеки.

    python3 tools/ship/gen_interior.py

Пишет:
  data/warpbound/structure/interior/<отсек>.nbt
  data/warpbound/ship_layout/frigate.json

Система координат раскладки: начало — центр палубы участка корабля (ShipInteriors.origin),
нос смотрит на +Z (туда же «туннель» неба варпа), палуба — y = 0.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "shipyard"))
from gen import write_nbt, DATA_VERSION  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "src/main/resources/data/warpbound"

FLOOR = "minecraft:polished_deepslate"
FLOOR2 = "minecraft:deepslate_tiles"
WALL = "minecraft:deepslate_tiles"
WALL2 = "minecraft:polished_blackstone_bricks"
CEIL = "minecraft:deepslate_bricks"
RIB = "warpbound:brass_trim"
HULL = "warpbound:hull_plating"
GLASS = "minecraft:tinted_glass"
WINDOW = "minecraft:glass"
LIGHT = "minecraft:sea_lantern"
GRATE = "minecraft:iron_bars"
CANDLE = "minecraft:candle[candles=3,lit=true]"
CARPET = "minecraft:red_carpet"
AIR = "minecraft:air"


class Room:
    """Коробка отсека: стены, пол, потолок с освещением; внутри — воздух. Смещение — левый-нижний-кормовой угол."""

    def __init__(self, name, w, h, l):
        self.name, self.w, self.h, self.l = name, w, h, l
        self.cells = {}

    def put(self, x, y, z, block):
        if 0 <= x < self.w and 0 <= y < self.h and 0 <= z < self.l:
            self.cells[(x, y, z)] = block

    def shell(self, wall=WALL, floor=FLOOR, ceil=CEIL, ribs=True):
        for x in range(self.w):
            for y in range(self.h):
                for z in range(self.l):
                    edge_x = x in (0, self.w - 1)
                    edge_z = z in (0, self.l - 1)
                    if y == 0:
                        self.put(x, y, z, floor if (x + z) % 2 else FLOOR2)
                    elif y == self.h - 1:
                        self.put(x, y, z, LIGHT if x == self.w // 2 and z % 4 == 2 else ceil)
                    elif edge_x or edge_z:
                        self.put(x, y, z, RIB if ribs and edge_x and z % 4 == 0 else wall)
                    else:
                        self.put(x, y, z, AIR)

    def door(self, side, center, width=3, height=3):
        """Проём в стене: side — 'stern' (z=0), 'bow' (z=l-1), 'port' (x=0), 'star' (x=w-1)."""
        for d in range(-(width // 2), width // 2 + 1):
            for y in range(1, 1 + height):
                if side == "stern":
                    self.put(center + d, y, 0, AIR)
                elif side == "bow":
                    self.put(center + d, y, self.l - 1, AIR)
                elif side == "port":
                    self.put(0, y, center + d, AIR)
                elif side == "star":
                    self.put(self.w - 1, y, center + d, AIR)

    def portholes(self, side, every=4, y=3):
        for z in range(2, self.l - 2, every):
            x = 0 if side == "port" else self.w - 1
            self.put(x, y, z, GLASS)
            self.put(x, y + 1, z, GLASS)


def stern():
    r = Room("engine_room", 13, 7, 8)
    r.shell()
    r.door("bow", 6)
    # Варп-двигатель: синее пламя за решёткой
    for x in (3, 6, 9):
        for y in (1, 2, 3):
            r.put(x, y, 1, "minecraft:soul_lantern" if y == 2 else GRATE)
    for x in range(2, 11):
        r.put(x, 4, 1, WALL2)
    r.put(6, 1, 4, "warpbound:geller_node[facing=south]")
    return r


def reactor():
    r = Room("reactor_room", 11, 7, 7)
    r.shell()
    r.door("stern", 5)
    r.door("bow", 5)
    r.put(5, 1, 3, "warpbound:reactor_core[facing=south]")
    r.put(5, 2, 3, "warpbound:reactor_core[facing=south]")
    for x, z in ((3, 2), (7, 2), (3, 4), (7, 4)):
        r.put(x, 1, z, GRATE)
        r.put(x, 2, z, GRATE)
    return r


def corridor():
    r = Room("corridor", 7, 6, 17)
    r.shell()
    r.door("stern", 3)
    r.door("bow", 3)
    r.door("port", 4)
    r.door("star", 4)
    r.door("port", 12)
    r.door("star", 12)
    for z in range(1, 16):
        r.put(3, 0, z, "minecraft:red_concrete" if z % 2 else FLOOR)
    return r


def geller_room(name):
    r = Room(name, 7, 6, 7)
    r.shell()
    r.door("star" if name.endswith("port") else "port", 3)
    for z in (1, 3, 5):
        r.put(1 if name.endswith("port") else 5, 1, z, "warpbound:geller_node[facing=east]" if name.endswith("port")
              else "warpbound:geller_node[facing=west]")
    r.portholes("port" if name.endswith("port") else "star", every=3)
    return r


def chapel():
    r = Room("chapel", 7, 7, 7)
    r.shell(wall=WALL2)
    r.door("port", 3)
    # Алтарь Императора: аналой, свечи, ковровая дорожка
    r.put(5, 1, 3, "minecraft:lectern[facing=west]")
    r.put(5, 1, 1, CANDLE)
    r.put(5, 1, 5, CANDLE)
    for x in range(1, 5):
        r.put(x, 1, 3, CARPET)
    r.put(6, 3, 3, "minecraft:gold_block")
    r.put(6, 4, 3, "minecraft:gold_block")
    r.put(6, 3, 2, "minecraft:gold_block")
    r.put(6, 3, 4, "minecraft:gold_block")
    return r


def teleportarium():
    r = Room("teleportarium", 7, 6, 7)
    r.shell()
    r.door("star", 3)
    for x in (2, 4):
        for z in (2, 4):
            r.put(x, 0, z, "warpbound:teleportarium_pad[facing=south]")
    r.put(3, 0, 3, "warpbound:teleportarium_pad[facing=south]")
    for x, z in ((1, 1), (5, 1), (1, 5), (5, 5)):
        r.put(x, 1, z, GRATE)
        r.put(x, 2, z, LIGHT)
    return r


def bridge():
    r = Room("bridge", 15, 9, 14)
    r.shell(wall=WALL2)
    r.door("stern", 7)
    # Панорамное окно в нос: сквозь него видно варп
    for x in range(2, 13):
        for y in range(2, 8):
            r.put(x, y, 13, WINDOW)
    r.portholes("port", every=3, y=4)
    r.portholes("star", every=3, y=4)
    # Ступенчатый помост капитана и навигационный стол
    for x in range(4, 11):
        for z in range(3, 7):
            r.put(x, 1, z, "minecraft:polished_deepslate_slab[type=bottom]")
    r.put(7, 1, 4, "minecraft:polished_blackstone_stairs[facing=south]")
    r.put(7, 1, 9, "warpbound:nav_table[facing=north]")
    r.put(4, 1, 10, "warpbound:auspex[facing=east]")
    r.put(10, 1, 10, "warpbound:auspex[facing=west]")
    for z in range(1, 13):
        r.put(7, 0, z, CARPET.replace("carpet", "concrete"))
    return r


# Раскладка: отсек → смещение левого-нижнего-кормового угла от центра палубы
LAYOUT = [
    (stern(), (-6, 0, -26)),
    (reactor(), (-5, 0, -19)),
    (corridor(), (-3, 0, -13)),
    (geller_room("geller_port"), (-9, 0, -12)),
    (geller_room("geller_star"), (3, 0, -12)),
    (teleportarium(), (-9, 0, -4)),
    (chapel(), (3, 0, -4)),
    (bridge(), (-7, 0, 3)),
]
SPAWN = [0, 1, -9]  # посреди коридора


def parse(block):
    if "[" in block:
        name, props = block[:-1].split("[", 1)
        return name, dict(p.split("=") for p in props.split(","))
    return block, None


def write_room(room):
    palette, index, entries = [], {}, []
    for (x, y, z), block in sorted(room.cells.items()):
        if block not in index:
            index[block] = len(palette)
            name, props = parse(block)
            entry = {"Name": name}
            if props:
                entry["Properties"] = props
            palette.append(entry)
        entries.append({"pos": [x, y, z], "state": index[block]})
    write_nbt(DATA / f"structure/interior/{room.name}.nbt", {
        "DataVersion": DATA_VERSION,
        "size": [room.w, room.h, room.l],
        "palette": palette,
        "blocks": entries,
        "entities": [],
    })


def main():
    for room, _ in LAYOUT:
        write_room(room)
    layout = {
        "compartments": [{"structure": f"warpbound:interior/{room.name}", "offset": list(off)} for room, off in LAYOUT],
        "spawn": SPAWN,
    }
    out = DATA / "ship_layout/frigate.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(layout, indent=2) + "\n", encoding="utf-8")
    print("отсеков:", len(LAYOUT), "блоков:", sum(len(r.cells) for r, _ in LAYOUT))


if __name__ == "__main__":
    main()
