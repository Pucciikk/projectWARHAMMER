#!/usr/bin/env python3
"""
Генератор верфи Сезона 1: шаблон мультиблока «Стапель», класс корабля «Фрегат»
и шесть структур-этапов фрегата (.nbt), которые появляются в доке по очереди.

    python3 tools/shipyard/gen.py

Пишет:
  data/warpbound/multiblock/shipyard.json
  data/warpbound/ship_class/frigate.json
  data/warpbound/structure/frigate/<этап>.nbt

Без внешних зависимостей: NBT пишется вручную. Модель — временная, до моделей автора.
"""
import gzip
import json
import math
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "src/main/resources/data/warpbound"
DATA_VERSION = 3955  # Minecraft 1.21.1

# ---------------------------------------------------------------- рама верфи
# Шаблон для пульта, смотрящего на север: строки — по Z (от пульта вглубь дока), символы — по X.
# Стапель рассчитан на лёгкий крейсер (153 блока); фрегат помещается в нём же.
DOCK_W, DOCK_L, DOCK_H = 49, 160, 18
CORE_X = DOCK_W // 2
PYLON_Z = (1, DOCK_L // 3, 2 * DOCK_L // 3, DOCK_L - 1)


def shipyard_pattern():
    layers = []
    for y in range(DOCK_H):
        rows = []
        for z in range(DOCK_L):
            row = []
            for x in range(DOCK_W):
                c = " "
                edge = x in (0, DOCK_W - 1)
                if y == 0 and z == 0 and x == CORE_X:
                    c = "C"
                elif y == 0 and z >= 1 and edge:
                    c = "G"  # рельсы стапеля
                elif 1 <= y <= DOCK_H - 2 and edge and z in PYLON_Z:
                    c = "G"  # опоры
                elif y == DOCK_H - 1 and z in (PYLON_Z[0], PYLON_Z[-1]):
                    c = "G"  # поперечные балки крана
                row.append(c)
            rows.append("".join(row).rstrip() or " ")
        layers.append(rows)
    return {
        "name": "multiblock.warpbound.shipyard",
        "layers": layers,
        "key": {"G": "warpbound:dock_girder"},
        "core": "C",
        "mirrorable": False,
    }


# ---------------------------------------------------------------- фрегат
SHIP_W, SHIP_H, SHIP_L = 9, 10, 38
# Нижний угол корабля в координатах шаблона верфи → смещение от пульта
SHIP_ORIGIN = (CORE_X - SHIP_W // 2, 1, 3)

HULL = "warpbound:hull_plating"
DARK = "minecraft:polished_deepslate"
BRASS = "warpbound:brass_trim"
WINDOW = "minecraft:tinted_glass"
LIGHT = "minecraft:sea_lantern"
WARP = "minecraft:soul_lantern"
ENGINE = "minecraft:magma_block"
FIN = "minecraft:iron_bars"
SPIRE = "minecraft:polished_blackstone_bricks"

STAGES = ["keel", "hull", "reactor", "warp_engine", "geller_field", "modules"]


def frigate():
    """Возвращает {(x,y,z): (block, stage)}. Нос — на дальнем конце дока (+Z), двигатели — у пульта."""
    blocks = {}

    def put(x, y, z, block, stage):
        if 0 <= x < SHIP_W and 0 <= y < SHIP_H and 0 <= z < SHIP_L:
            blocks[(x, y, z)] = (block, stage)

    cx = SHIP_W // 2
    for z in range(SHIP_L):
        # Профиль корпуса: к носу сужается, у кормы чуть шире
        t = z / (SHIP_L - 1)
        prow = max(0.0, (t - 0.78) / 0.22)          # 0..1 на последних 22% длины
        half = 4 - round(prow * 3)                   # полуширина 4 → 1
        top = 6 - round(prow * 3)                    # высота корпуса 6 → 3
        for y in range(0, top + 1):
            for x in range(cx - half, cx + half + 1):
                inner = abs(x - cx) < half and 0 < y < top
                if inner:
                    continue
                if y == 0 and abs(x - cx) <= 1:
                    put(x, y, z, DARK, "keel")       # хребет-киль
                elif y == 0 or (abs(x - cx) == half and z % 4 == 0):
                    put(x, y, z, HULL if y else DARK, "keel" if z % 4 == 0 else "hull")
                elif y == 3 and abs(x - cx) == half:
                    put(x, y, z, BRASS, "hull")      # латунный пояс
                elif y == 2 and abs(x - cx) == half and z % 3 == 1 and prow == 0:
                    put(x, y, z, WINDOW, "modules")  # иллюминаторы
                elif y == top:
                    put(x, y, z, HULL, "reactor" if 8 <= z <= 24 else "hull")
                else:
                    put(x, y, z, HULL, "hull")
        # Шпангоуты киля через каждые 4 блока
        if z % 4 == 0:
            put(cx, 1, z, DARK, "keel")

    # Таран на носу
    for z in range(SHIP_L - 3, SHIP_L):
        put(cx, 1, z, BRASS, "modules")
        put(cx, 2, z, BRASS, "modules")

    # Реактор: светящийся хребет-радиатор на спине корабля
    for z in range(10, 24, 2):
        put(cx, 7, z, LIGHT, "reactor")
        put(cx - 1, 7, z, DARK, "reactor")
        put(cx + 1, 7, z, DARK, "reactor")

    # Варп-двигатель: три сопла у кормы, синее пламя
    for x in (cx - 3, cx, cx + 3):
        for y in (2, 3):
            put(x, y, 0, WARP, "warp_engine")
        put(x, 1, 1, ENGINE, "warp_engine")
        put(x, 4, 1, ENGINE, "warp_engine")
    for x in range(cx - 4, cx + 5):
        put(x, 5, 1, DARK, "warp_engine")

    # Поле Геллера: проекторы-плавники по бортам и кольцо посередине
    for z in (6, 14, 22):
        for side in (-1, 1):
            put(cx + side * 4, 4, z, FIN, "geller_field")
            put(cx + side * 4, 5, z, LIGHT, "geller_field")
    for x in range(cx - 4, cx + 5):
        put(x, 7, 26, FIN, "geller_field")

    # Отсеки: мостик-башня ближе к корме и готический шпиль
    for z in range(4, 9):
        for x in range(cx - 2, cx + 3):
            for y in range(7, 9):
                edge = x in (cx - 2, cx + 2) or z in (4, 8)
                if edge:
                    put(x, y, z, WINDOW if y == 8 and z == 8 else HULL, "modules")
        put(cx, 9, 6, SPIRE, "modules")
    put(cx, 9, 5, SPIRE, "modules")
    return blocks


# ---------------------------------------------------------------- NBT
def _tag_header(tag_id, name):
    raw = name.encode("utf-8")
    return struct.pack(">bH", tag_id, len(raw)) + raw


def _payload(value):
    """(tag_id, bytes) для поддерживаемых значений."""
    if isinstance(value, bool) or isinstance(value, int):
        return 3, struct.pack(">i", int(value))
    if isinstance(value, str):
        raw = value.encode("utf-8")
        return 8, struct.pack(">H", len(raw)) + raw
    if isinstance(value, list):
        if not value:
            return 9, struct.pack(">bi", 0, 0)
        items = [_payload(v) for v in value]
        tag_id = items[0][0]
        return 9, struct.pack(">bi", tag_id, len(items)) + b"".join(p for _, p in items)
    if isinstance(value, dict):
        out = b""
        for k, v in value.items():
            tid, p = _payload(v)
            out += _tag_header(tid, k) + p
        return 10, out + b"\x00"
    raise TypeError(value)


def write_nbt(path, root):
    tid, payload = _payload(root)
    data = _tag_header(tid, "") + payload
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wb") as f:
        f.write(data)


def _state(block):
    if "[" not in block:
        return {"Name": block}
    name, props = block[:-1].split("[", 1)
    return {"Name": name, "Properties": dict(p.split("=") for p in props.split(","))}


def write_structure(path, cells, size=None):
    palette, index, entries = [], {}, []
    for (x, y, z), block in sorted(cells.items()):
        if block not in index:
            index[block] = len(palette)
            palette.append(_state(block))
        entries.append({"pos": [x, y, z], "state": index[block]})
    write_nbt(path, {
        "DataVersion": DATA_VERSION,
        "size": list(size or (SHIP_W, SHIP_H, SHIP_L)),
        "palette": palette,
        "blocks": entries,
        "entities": [],
    })


# ---------------------------------------------------------------- класс корабля
STAGE_INFO = {
    "keel":         ("shipyard.warpbound.stage.keel",         [("warpbound:plasteel_plate", 8), ("minecraft:iron_ingot", 48), ("minecraft:stone", 64)], 60),
    "hull":         ("shipyard.warpbound.stage.hull",         [("warpbound:plasteel_plate", 16), ("minecraft:iron_ingot", 64), ("minecraft:deepslate", 64)], 90),
    "reactor":      ("shipyard.warpbound.stage.reactor",      [("warpbound:brass_gear", 16), ("minecraft:redstone", 48), ("minecraft:gold_ingot", 8), ("minecraft:blaze_rod", 4)], 90),
    "warp_engine":  ("shipyard.warpbound.stage.warp_engine",  [("warpbound:brass_gear", 8), ("minecraft:obsidian", 16), ("minecraft:diamond", 4), ("minecraft:soul_sand", 16)], 120),
    "geller_field": ("shipyard.warpbound.stage.geller_field", [("minecraft:amethyst_shard", 16), ("minecraft:gold_ingot", 16), ("minecraft:iron_bars", 16)], 90),
    "modules":      ("shipyard.warpbound.stage.modules",      [("warpbound:plasteel_plate", 8), ("warpbound:brass_gear", 8), ("minecraft:glass", 32), ("minecraft:lantern", 8)], 60),
}


def main():
    pattern = shipyard_pattern()
    out = DATA / "multiblock/shipyard.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(pattern, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    ship = frigate()
    by_stage = {s: {} for s in STAGES}
    for pos, (block, stage) in ship.items():
        by_stage[stage][pos] = block
    for stage, cells in by_stage.items():
        write_structure(DATA / f"structure/frigate/{stage}.nbt", cells)

    offset = [SHIP_ORIGIN[0] - CORE_X, SHIP_ORIGIN[1], SHIP_ORIGIN[2]]
    ship_class = {
        "name": "ship_class.warpbound.frigate",
        "stages": [
            {
                "name": STAGE_INFO[s][0],
                "requirements": [{"item": i, "count": c} for i, c in STAGE_INFO[s][1]],
                "structure": f"warpbound:frigate/{s}",
                "offset": offset,
                "build_seconds": STAGE_INFO[s][2],
            }
            for s in STAGES
        ],
    }
    out = DATA / "ship_class/frigate.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(ship_class, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # лёгкий крейсер типа «Неустрашимый» — корабль Сезона 1 (tools/shipyard/dauntless.py, из STL автора)
    import dauntless
    cr, cr_size = dauntless.build()
    cr_stages = {s: {} for s in STAGES}
    for pos, (block, stage) in cr.items():
        cr_stages[stage][pos] = block
    for stage, cells in cr_stages.items():
        write_structure(DATA / f"structure/cruiser/{stage}.nbt", cells, cr_size)
    cr_offset = [-(cr_size[0] // 2), 1, 3]
    cruiser_class = {
        "name": "ship_class.warpbound.light_cruiser",
        "stages": [
            {
                "name": STAGE_INFO[s][0],
                "requirements": [{"item": i, "count": c} for i, c in STAGE_INFO[s][1]],
                "structure": f"warpbound:cruiser/{s}",
                "offset": cr_offset,
                "build_seconds": STAGE_INFO[s][2],
            }
            for s in STAGES
        ],
    }
    (DATA / "ship_class/light_cruiser.json").write_text(json.dumps(cruiser_class, ensure_ascii=False, indent=2) + "\n",
                                                        encoding="utf-8")
    print("крейсер:", len(cr), "блоков,", ", ".join(f"{s} {len(c)}" for s, c in cr_stages.items()))

    girders = sum(row.count("G") for layer in pattern["layers"] for row in layer)
    print(f"верфь: {DOCK_W}x{DOCK_L}x{DOCK_H}, балок {girders}; фрегат: {len(ship)} блоков, "
          + ", ".join(f"{s} {len(c)}" for s, c in by_stage.items()))


if __name__ == "__main__":
    main()
