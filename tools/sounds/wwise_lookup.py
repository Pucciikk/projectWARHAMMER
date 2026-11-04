#!/usr/bin/env python3
"""
Какие .wem играет событие Wwise: разбирает .bnk (HIRC), от события через действия и контейнеры доходит до звуков.

    python tools/sounds/wwise_lookup.py list <банк> [фильтр]        имена событий банка (из таблиц stats)
    python tools/sounds/wwise_lookup.py wems <банк> <событие> ...   номера и размеры .wem каждого события

Имя события превращается в номер хешем FNV-1 (32 бита, строчные буквы). Формат контейнеров меняется от версии к версии, поэтому их список потомков
ищется по признаку: число, за которым идёт столько же номеров объектов банка. Микшеры (тип 7) пропускаются: через них можно уйти к чужим звукам.
"""
import csv
import glob
import os
import struct
import sys

ROOT = r"D:/filesFromGWToMeOficial/extraction_sounds"
BNK = os.path.join(ROOT, "sounds/desktop")
WEM = os.path.join(ROOT, "wem")


def fnv1(name):
    h = 2166136261
    for c in name.lower().encode():
        h = (h * 16777619) & 0xFFFFFFFF
        h ^= c
    return h


def read_hirc(bank):
    data = open(os.path.join(BNK, bank + ".bnk"), "rb").read()
    objects, i = {}, 0
    while i + 8 <= len(data):
        tag, size = data[i:i + 4], struct.unpack_from("<I", data, i + 4)[0]
        if tag == b"HIRC":
            n = struct.unpack_from("<I", data, i + 8)[0]
            p = i + 12
            for _ in range(n):
                kind, length = struct.unpack_from("<BI", data, p)
                oid = struct.unpack_from("<I", data, p + 5)[0]
                objects[oid] = (kind, data[p + 9:p + 5 + length])
                p += 5 + length
        i += 8 + size
    return objects


def sound_source(body):
    # тип 2: плагин (4), вид хранения (1), номер источника (4)
    return struct.unpack_from("<I", body, 5)[0]


def children(objects, body):
    """Список потомков контейнера: число и сразу за ним столько же номеров объектов банка. Родитель записан в теле одиночным числом, поэтому вверх отсюда не уйти."""
    best = []
    for off in range(0, len(body) - 7):
        n = struct.unpack_from("<I", body, off)[0]
        if n <= len(best) or n > 2000 or off + 4 + n * 4 > len(body):
            continue
        ids = struct.unpack_from(f"<{n}I", body, off + 4)
        if all(i in objects and objects[i][0] in (2, 5, 6, 9) for i in ids):
            best = list(ids)
    return best


def walk(objects, start, seen, out):
    if start in seen or start not in objects:
        return
    seen.add(start)
    kind, body = objects[start]
    if kind == 2:
        out.add(sound_source(body))
    elif kind == 3:
        # действие: тип (2), цель (4)
        walk(objects, struct.unpack_from("<I", body, 2)[0], seen, out)
    elif kind in (5, 6, 9):
        for v in children(objects, body):
            walk(objects, v, seen, out)


def event_wems(objects, name):
    h = fnv1(name)
    if h not in objects or objects[h][0] != 4:
        return None
    body = objects[h][1]
    # число действий: 1 байт в новых версиях, 4 в старых. Проверяем, что дальше идут номера действий
    for fmt, size in (("<B", 1), ("<I", 4)):
        n = struct.unpack_from(fmt, body, 0)[0]
        if size + n * 4 == len(body):
            ids = struct.unpack_from(f"<{n}I", body, size)
            out = set()
            seen = set()
            for a in ids:
                walk(objects, a, seen, out)
            return out
    return None


def find_wem(wem):
    for path in glob.glob(os.path.join(WEM, "*", f"{wem}.wem")):
        return path
    return None


def list_events(bank, flt=""):
    names = set()
    for f in glob.glob(os.path.join(ROOT, "sounds/stats/*events.csv")):
        with open(f, encoding="utf-8", newline="") as h:
            for row in csv.DictReader(h):
                if row["bank"] == bank and flt in row["event"]:
                    names.add(row["event"])
    return sorted(names)


if __name__ == "__main__":
    if sys.argv[1] == "list":
        for e in list_events(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else ""):
            print(e)
    else:
        objects = read_hirc(sys.argv[2])
        print("объектов", len(objects))
        for name in sys.argv[3:]:
            w = event_wems(objects, name)
            if w is None:
                print(name, "не найдено")
                continue
            paths = [(x, find_wem(x)) for x in sorted(w)]
            print(name, len(paths), [(x, os.path.getsize(p) if p else None) for x, p in paths][:14])
