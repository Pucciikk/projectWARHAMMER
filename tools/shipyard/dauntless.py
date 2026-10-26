"""
Лёгкий крейсер типа «Неустрашимый» (Dauntless) для верфи — из 3D-модели автора (Pictures/kreiser/Dauntless-V2.stl).

Форма — вокселизация модели (tools/shipyard/voxelize_stl.py, масштаб 1,3 → 31×36×100 блоков),
лежит в data/dauntless_vox.json. Здесь — раскраска блоками по зонам корабля и по нормалям поверхности
и раскладка по этапам постройки верфи.

Оси: x поперёк, y вверх, z от кормы (у пульта, z = 0) к носу. Зоны по профилю модели:
  z 0–13   корма: пучок маршевых двигателей;
  z 14–39  широкая часть: спонсоны по бортам, собор-мостик со шпилем, киль-плавники снизу;
  z 40–62  средний корпус: бортовые батареи, палуба;
  z 63–83  нос-клин: белая броня, гребень аквилы, знаки на скулах;
  z 84+    таран-копьё.
"""
import json
import os
from collections import defaultdict

HERE = os.path.dirname(__file__)

HULL = "warpbound:hull_plating"
HULL2 = "minecraft:polished_deepslate"
PANEL = "minecraft:deepslate_tiles"
DARK = "minecraft:blackstone"
GOTHIC = "minecraft:polished_blackstone_bricks"
GOTHIC2 = "minecraft:chiseled_polished_blackstone"
PROW = "warpbound:plasteel_panel"
PROW2 = "warpbound:riveted_plasteel_panel"
BRASS = "warpbound:brass_trim"
GOLD = "minecraft:gold_block"
RED = "minecraft:red_nether_bricks"
WINDOW = "minecraft:ochre_froglight"
STAINED = "minecraft:orange_stained_glass"
DOME = "minecraft:waxed_weathered_cut_copper"
STEEL = "minecraft:iron_block"
RIB = "warpbound:dock_girder"
VENT = "warpbound:plasteel_vent"
GLOW = "minecraft:shroomlight"
PLASMA = "minecraft:magma_block"
SEA = "minecraft:sea_lantern"
ROD = "minecraft:lightning_rod"

META = {}
DIRS = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))


# Границы зон ниже — в блоках при масштабе 1,3; при другом масштабе они растягиваются на K = scale / 1,3.
BASE_SCALE = 1.3


def load():
    with open(os.path.join(HERE, "data", "dauntless_vox.json")) as f:
        d = json.load(f)
    return d["size"], d["vox"], d.get("scale", BASE_SCALE), d.get("core", [])


def build():
    (W, H, L), vox, scale, core = load()
    K = scale / BASE_SCALE
    cx = W // 2
    occ = {(v[0], v[1], v[2]): v for v in vox}
    # силуэт: крайние x по каждому (y, z) — чтобы отличить нишу от выступа
    half = defaultdict(int)
    for (x, y, z) in occ:
        half[(y, z)] = max(half[(y, z)], abs(x - cx))
    rear = {}                                       # самая кормовая клетка в каждом (x, y)
    for (x, y, z) in occ:
        if (x, y) not in rear or z < rear[(x, y)]:
            rear[(x, y)] = z
    # задняя грань кормы: насколько клетка далеко от края силуэта — середина станет раскалённым соплом
    face = {(x, y) for (x, y), z in rear.items() if z <= 1}
    depth = {}
    frontier = [p for p in face if any((p[0] + a, p[1] + b) not in face for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for p in frontier:
        depth[p] = 0
    while frontier:
        nxt = []
        for (px, py) in frontier:
            for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (px + a, py + b)
                if q in face and q not in depth:
                    depth[q] = depth[(px, py)] + 1
                    nxt.append(q)
        frontier = nxt
    # четыре сопла 2×2 по задней грани: центры в четвертях её габарита
    fx = [p[0] for p in face]
    fy = [p[1] for p in face]
    bx0, bx1, by0, by1 = min(fx), max(fx), min(fy), max(fy)
    radius = min(bx1 - bx0, by1 - by0) / 4
    nozzles = [(bx0 + (bx1 - bx0) * a, by0 + (by1 - by0) * b) for a in (0.25, 0.75) for b in (0.27, 0.73)]

    def nozzle(x, y):
        return min(((x - nx_) ** 2 + (y - ny_) ** 2) ** 0.5 for nx_, ny_ in nozzles)

    top = defaultdict(lambda: -1)
    for (x, y, z) in occ:
        top[z] = max(top[z], y)

    cells = {}
    for (x, y, z), v in occ.items():
        nx, ny, nz, dist, ins = v[3], v[4], v[5], v[6], v[7]
        open_dirs = [d for d in DIRS if (x + d[0], y + d[1], z + d[2]) not in occ]
        side = any(d[0] for d in open_dirs)
        up = (0, 1, 0) in open_dirs
        down = (0, -1, 0) in open_dirs
        back = (0, 0, -1) in open_dirs
        dx = abs(x - cx)
        Z, Y, DX = z / K, y / K, dx / K                          # координаты в единицах масштаба 1,3
        thin = not ins and 6 - len(open_dirs) <= 2   # шпили и антенны: снаружи модели и почти без соседей
        block, stage = HULL, "hull"

        if Z <= 13:                                              # корма: двигатели
            stage = "warp_engine"
            r = nozzle(x, y) if (x, y) in face else 99
            if z == rear.get((x, y), -1) and r < radius - 0.6:
                continue                                         # сопло утоплено на блок
            if z == rear.get((x, y), -1) + 1 and r < radius - 0.6:
                block = GLOW if (x * 3 + y) % 4 else PLASMA      # раскалённое нутро
            elif back and r < radius + 0.4:
                block = BRASS                                    # латунный обод сопла
            elif back:
                block = HULL2
            elif side and z % 3 == 0:
                block = RIB                                      # рёбра охлаждения
            elif up and z % 4 == 2:
                block = VENT
            else:
                block = HULL if (y + z) % 5 else HULL2
        elif Z >= 84:                                            # таран-копьё
            block = BRASS if z % 4 == 0 else STEEL
            if z == L - 1 or (z, y) == (max(k for (_, _, k) in occ), y):
                block = STEEL
        elif Z >= 63:                                            # нос-клин
            block = PROW2 if (y + z) % 6 == 0 else PROW
            if Y >= 22:
                block, stage = GOLD, "modules"                   # гребень аквилы
            elif up and side and Y >= 15:
                block = BRASS                                    # золотая кромка скулы
            elif side and 9 <= Y <= 15 and 70 <= Z <= 76:
                edge = abs(Y - 9) < 1 / K or abs(Y - 15) < 1 / K or abs(Z - 70) < 1 / K or abs(Z - 76) < 1 / K
                block, stage = (GOLD if edge else RED), "modules"   # красно-золотой знак на скуле
            elif down:
                block = HULL2
        else:
            tower = 20 <= Z <= 33 and Y >= 25
            if tower:                                            # собор-мостик
                stage = "modules"
                if Y >= 32:
                    block = DOME if y < top[z] or Y < 34 else GOLD
                elif side and y % 3 == 1 and z % 2 == 0:
                    block = STAINED if Y >= 28 else WINDOW
                elif up:
                    block = GOTHIC2
                else:
                    block = GOTHIC
            elif Y <= 6:                                         # киль-плавники
                block, stage = (BRASS if down else HULL2), "keel"
            elif Z <= 39 and DX >= 8:                            # спонсоны широкой части
                stage = "modules"
                block = HULL2 if up and side else (GOTHIC if z % 4 == 0 else HULL)
                if side and DX >= 12 and y % 4 == 1 and z % 3 == 0:
                    block = WINDOW
            else:                                                # средний корпус и палуба
                recessed = side and dx < half[(y, z)] - 0
                if down:
                    block, stage = HULL2, "keel"
                elif up and side:
                    block = BRASS if Y >= 20 else HULL2              # латунь — только по кромке палубы
                elif up:
                    block, stage = (PANEL if DX <= 2 else HULL), ("reactor" if 40 <= Z <= 62 and DX <= 2 else "hull")
                elif side and recessed and DX < 5:
                    block, stage = DARK, "modules"               # глубина бортовой ниши
                elif side and (z - 40) % 5 == 0:
                    block = GOTHIC                               # контрфорс
                elif side and round(Y) in (14, 17, 20) and z % 2 == 1 and not recessed:
                    block, stage = WINDOW, "modules"             # ряды огней
                else:
                    block = PANEL if (y // 3 + z // 5) % 2 else HULL
        if thin and Z < 84 and not (Z <= 13):
            block, stage = (GOTHIC if Y < 30 else BRASS), "geller_field"   # шпили, антенны, проекторы Поля
        cells[(x, y, z)] = (block, stage)

    # интерьер: отсеки вырезаются в сплошном корпусе (tools/shipyard/interior.py)
    import interior
    solid = set(occ) | {tuple(c) for c in core}
    nb = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
    outer = {p for p in solid if any((p[0] + a, p[1] + b, p[2] + c) not in solid for a, b, c in nb)}
    global META
    inside = interior.build(cells, solid, outer)
    META = {"spawn": inside.spawn, "reactor": inside.reactor}

    # шпиль-громоотвод на вершине мостика и огни-маяки на корме
    peak = max(((x, y, z) for (x, y, z) in occ if 20 <= z / K <= 33), key=lambda p: p[1])
    cells[(peak[0], peak[1] + 1, peak[2])] = (ROD, "modules")
    for (x, y, z) in occ:
        if z == round(14 * K) and y == top[z] and (x + y) % 4 == 0:
            cells[(x, y + 1, z)] = (SEA, "modules")
    # мостик — готический зал вместо тесной надстройки модели (tools/shipyard/bridge_hall.py)
    import bridge_hall
    META["spawn"] = bridge_hall.build(cells)
    return cells, (W, max(p[1] for p in cells) + 1, L)
