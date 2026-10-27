"""
Мостик крейсера — узкая высокая башня-собор на месте тесной надстройки модели (арты автора: kapitan2.jpg,
kreiserSoStoroni.png в Pictures/kreiser; по просьбе автора — «уже и выше, как шпиль собора»).

Снаружи: зал 13×25 на узкой шее с консолями, пилястры, высокие стрельчатые светящиеся окна; над залом два уступа —
каждый уже предыдущего, со своими окнами и пинаклями — и тонкий шпиль с громоотводом; спереди щипец над круглым
иллюминатором. Внутри (10 блоков высотой): трон на помосте у кормы с аквилой на стене и штандартами по бокам,
перед троном командный пульт, с помоста две лестницы с балюстрадой и черепами; медальон в полу с голостолом под
световым колодцем, уходящим в шпиль; по левому борту — карта Империума над когитаторами, по правому — когитаторы
с креслами; гравилифт в анклав. Стекло иллюминатора бронеставни не закрывают (ShipLaunch.scan).
"""
import math
import random

CX = 22
X0, X1 = 16, 28          # стены по ширине
Z0, Z1 = 32, 56          # кормовая и носовая стены
YF = 39                  # пол
YC = YF + 11             # потолок
ZD = 46                  # центр медальона, голостола и светового колодца
LIFT = (26, 43)          # гравилифт: та же вертикаль, что в анклаве (interior.hub)

GOTHIC = "minecraft:polished_blackstone_bricks"
RIB = "minecraft:chiseled_polished_blackstone"
DBR = "minecraft:deepslate_bricks"
DEEP = "minecraft:polished_deepslate"
TILES = "minecraft:deepslate_tiles"
HULL = "warpbound:hull_plating"
BRASS = "warpbound:brass_trim"
GOLD = "minecraft:gold_block"
GLASS = "minecraft:glass"
LIT = "minecraft:ochre_froglight"           # светящиеся окна башни (под ставни не попадают)
RED = "minecraft:red_concrete"
MEDAL = "minecraft:orange_terracotta"
MEDAL2 = "minecraft:brown_terracotta"
PART = "warpbound:fixture_part"
POST = "minecraft:polished_blackstone_wall"
COG = "warpbound:cogitator_bank"
STAIRS = "minecraft:polished_blackstone_brick_stairs"
TSTAIRS = "minecraft:deepslate_tile_stairs"
SEAT = "minecraft:dark_oak_stairs"
SKULL = "minecraft:skeleton_skull[rotation=0]"
ROD = "minecraft:lightning_rod"


def st(facing, top=False, kind=STAIRS):
    return f"{kind}[facing={facing},half={'top' if top else 'bottom'}]"


def build(cells):
    """Пишет мостик в словарь клеток корабля (этап modules), сносит старую надстройку на его месте.
    Возвращает точку появления на борту."""
    def put(x, y, z, b):
        cells[(x, y, z)] = (b, "modules")

    def clear(x, y, z):
        cells.pop((x, y, z), None)

    # снести старую надстройку
    for (x, y, z) in list(cells):
        if 10 <= x <= 34 and 27 <= z <= 60 and y >= YF:
            del cells[(x, y, z)]

    # ---- шея: от верха корпуса до пола, уже зала на блок; под свесом — консоли
    tops = {}
    for (x, y, z) in cells:
        if y < YF and tops.get((x, z), -1) < y:
            tops[(x, z)] = y
    for x in range(X0 + 1, X1):
        for z in range(Z0 + 1, Z1):
            edge = x in (X0 + 1, X1 - 1) or z in (Z0 + 1, Z1 - 1)
            for y in range(tops.get((x, z), YF - 8) + 1, YF):
                put(x, y, z, (RIB if y % 4 == 0 else GOTHIC) if edge else DEEP)
    for x in range(X0, X1 + 1):
        put(x, YF - 1, Z0, st("north", True))
        put(x, YF - 1, Z1, st("south", True))
    for z in range(Z0, Z1 + 1):
        put(X0, YF - 1, z, st("west", True))
        put(X1, YF - 1, z, st("east", True))

    # ---- зал: пол, стены, кессонный потолок
    for x in range(X0, X1 + 1):
        for z in range(Z0, Z1 + 1):
            wall = x in (X0, X1) or z in (Z0, Z1)
            for y in range(YF, YC + 1):
                if y == YF:
                    put(x, y, z, TILES if (x + z) % 2 else DEEP)
                elif y == YC:
                    put(x, y, z, BRASS if x in (CX - 3, CX + 3) else RIB if (z - Z0) % 3 == 0 else HULL)
                elif wall:
                    corner = x in (X0, X1) and z in (Z0, Z1)
                    put(x, y, z, RIB if corner or y == YF + 6 else GOTHIC)
                else:
                    clear(x, y, z)
    for z in range(Z0 + 6, Z1):
        put(CX, YF, z, RED)
    for x in range(CX - 5, CX + 6):
        for z in range(ZD - 5, ZD + 6):
            r = math.hypot(x - CX, z - ZD)
            if r < 3.5:
                put(x, YF, z, MEDAL2 if 2.2 <= r < 3.0 or r < 0.8 else MEDAL)
            elif r < 4.5:
                put(x, YF, z, BRASS)

    # ---- снаружи: пилястры и высокие стрельчатые окна во внешнем слое (изнутри зал каменный)
    for z in range(Z0 + 1, Z1, 3):
        for x, out in ((X0 - 1, "west"), (X1 + 1, "east")):
            for y in range(YF - 1, YC + 1):
                put(x, y, z, RIB if y % 4 == 0 else GOTHIC)
            put(x, YC + 1, z, st("west" if out == "east" else "east"))
            put(x, YC + 2, z, POST)
    rows = (YF + 2, YF + 3, YF + 4, YF + 5, YF + 7, YF + 8, YF + 9, YF + 10)
    for z in range(Z0 + 1, Z1):
        if (z - Z0) % 3 == 1:
            continue
        lancet = (z - Z0) % 3 == 2 and Z0 + 1 < z < Z1 - 1
        for x in (X0 - 1, X1 + 1):
            for y in range(YF - 1, YC + 1):
                put(x, y, z, LIT if lancet and y in rows else RIB if y in (YF + 6, YC) else GOTHIC)
    for x in range(X0 + 1, X1):
        for y in range(YF - 1, YC + 1):
            win = y in rows and x in (X0 + 2, X1 - 2)
            put(x, y, Z0 - 1, LIT if win else RIB if y in (YF + 6, YC) else GOTHIC)
    # кровля зала, зубчатый парапет, пинакли по углам
    for x in range(X0, X1 + 1):
        for z in range(Z0, Z1 + 1):
            put(x, YC + 1, z, HULL)
            if x in (X0, X1) or z in (Z0, Z1):
                put(x, YC + 2, z, RIB if (x + z) % 2 == 0 else POST)
    for x, z in ((X0, Z0), (X1, Z0), (X0, Z1), (X1, Z1)):
        for y in range(YC + 2, YC + 6):
            put(x, y, z, POST if y > YC + 2 else RIB)
        put(x, YC + 6, z, ROD)

    def tier(xa, xb, za, zb, y0, h, every=2):
        """Уступ башни: стены с окнами-ланцетами, угловые контрфорсы, кровля, пинакли."""
        for x in range(xa, xb + 1):
            for z in range(za, zb + 1):
                side = x in (xa, xb) or z in (za, zb)
                corner = x in (xa, xb) and z in (za, zb)
                for y in range(y0, y0 + h):
                    if not side:
                        put(x, y, z, DEEP)
                        continue
                    along = z - za if x in (xa, xb) else x - xa
                    win = not corner and along % every == 1 and y0 + 1 <= y <= y0 + h - 2
                    put(x, y, z, RIB if corner else LIT if win else GOTHIC)
                put(x, y0 + h, z, HULL)
                if side:
                    put(x, y0 + h + 1, z, RIB if (x + z) % 2 == 0 else POST)
        for x, z in ((xa, za), (xb, za), (xa, zb), (xb, zb)):
            put(x, y0 + h + 2, z, POST)
            put(x, y0 + h + 3, z, ROD)

    # два уступа и шпиль
    t2 = (CX - 4, CX + 4, ZD - 9, ZD + 7, YC + 2, 8)
    tier(*t2)
    t3 = (CX - 2, CX + 2, ZD - 5, ZD + 3, t2[4] + t2[5] + 2, 6)
    tier(*t3)
    ys = t3[4] + t3[5] + 2                          # основание шпиля
    for k, (hx, hz) in enumerate(((2, 3), (2, 3), (1, 2), (1, 2), (1, 1), (1, 1), (0, 1), (0, 0), (0, 0), (0, 0))):
        y = ys + k
        for x in range(CX - hx, CX + hx + 1):
            for z in range(ZD - 1 - hz, ZD - 1 + hz + 1):
                edge = abs(x - CX) == hx and abs(z - (ZD - 1)) == hz
                put(x, y, z, BRASS if edge and hx else TILES if hx else (POST if k >= 7 else RIB))
        if k == 1:
            for x, z in ((CX, ZD - 1 - hz), (CX, ZD - 1 + hz)):
                put(x, y, z, LIT)                   # слуховые окошки шпиля
    apex = ys + 10
    put(CX, apex, ZD - 1, ROD)
    # световой колодец: из зала сквозь уступы под шпиль; люстра на цепи над голостолом
    for x in range(CX - 1, CX + 2):
        for z in range(ZD - 1, ZD + 2):
            for y in range(YC, t3[4] + t3[5]):
                clear(x, y, z)
    for y in range(YF + 7, t3[4] + t3[5]):
        put(CX, y, ZD, "minecraft:chain[axis=y]")
    put(CX, YF + 6, ZD, "warpbound:lumen_ceiling")
    # щипец над иллюминатором
    for k in range(6):
        half = 5 - k
        for x in range(CX - half, CX + half + 1):
            put(x, YC + 2 + k, Z1, RIB if abs(x - CX) == half else GOTHIC)
    for y in range(YC + 8, YC + 10):
        put(CX, y, Z1, POST)
    put(CX, YC + 10, Z1, ROD)

    # ---- круглый иллюминатор в носу: латунное кольцо, стекло на варп
    wy = YF + 5.5
    for x in range(CX - 6, CX + 7):
        for y in range(YF + 1, YC):
            r = math.hypot(x - CX, y - wy)
            if r < 4.3:
                put(x, y, Z1, GLASS)
            elif r < 5.2 and X0 < x < X1:
                put(x, y, Z1, BRASS)

    # ---- помост трона у кормы: 3 блока, с него — две лестницы по бортам
    for x in range(X0 + 1, X1):
        for z in range(Z0 + 1, Z0 + 6):
            for y in range(YF + 1, YF + 4):
                put(x, y, z, (DEEP if (x + z) % 2 else TILES) if y == YF + 3 else GOTHIC)
    for (xa, xb) in ((X0 + 1, X0 + 2), (X1 - 2, X1 - 1)):
        for i, z in enumerate(range(Z0 + 6, Z0 + 9)):
            top = YF + 3 - i
            for x in range(xa, xb + 1):
                for y in range(YF + 1, top):
                    put(x, y, z, GOTHIC)
                put(x, top, z, st("north", kind=TSTAIRS))
        inner = xb + 1 if xa == X0 + 1 else xa - 1
        for i, z in enumerate(range(Z0 + 6, Z0 + 9)):
            for y in range(YF + 1, YF + 4 - i):
                put(inner, y, z, GOTHIC)
            put(inner, YF + 4 - i, z, POST)
            if i == 0:
                put(inner, YF + 5, z, SKULL)
    for x in range(X0 + 3, X1 - 2):                 # балюстрада передней кромки, под ней — экраны
        put(x, YF + 4, Z0 + 5, POST)
        if x in (CX - 2, CX + 2):
            put(x, YF + 5, Z0 + 5, SKULL)
            put(x, YF + 1, Z0 + 6, f"{COG}[facing=south]")
            put(x, YF + 2, Z0 + 6, RIB)
    put(CX, YF + 4, Z0 + 2, "warpbound:command_throne[facing=south]")
    put(CX - 1, YF + 4, Z0 + 4, PART)
    put(CX + 1, YF + 4, Z0 + 4, PART)
    put(CX, YF + 4, Z0 + 4, "warpbound:command_console[facing=north]")
    for y, half in ((YF + 7, 4), (YF + 8, 2), (YF + 6, 1)):          # золотая аквила на кормовой стене
        for x in range(CX - half, CX + half + 1):
            put(x, y, Z0, GOLD)
    put(CX, YF + 9, Z0, GOLD)
    for x in (X0 + 2, X1 - 2):                                       # штандарты на древках по бокам трона
        put(x, YF + 4, Z0 + 2, "warpbound:imperial_standard_pole[facing=south]")

    # ---- голостол в центре медальона
    for dx in (-1, 0, 1):
        for dz in (0, 1):
            put(CX + dx, YF + 1, ZD + dz, PART)
    put(CX, YF + 1, ZD, "warpbound:nav_table[facing=north]")

    # ---- левый борт: карта Империума над когитаторами с креслами
    chart_z = ZD + 1
    for z in range(chart_z - 3, chart_z + 4):
        for y in range(YF + 4, YF + 8):
            put(X0 + 1, y, z, PART)
        put(X0 + 1, YF + 1, z, f"{COG}[facing=east]")
        put(X0 + 1, YF + 2, z, f"{COG}[facing=east]")
        put(X0 + 2, YF + 1, z, st("east", kind=SEAT))
    put(X0 + 1, YF + 4, chart_z, "warpbound:star_chart[facing=east]")
    # правый борт: когитаторы с креслами, гравилифт в анклав
    for z in range(Z0 + 9, Z1 - 3):
        put(X1 - 1, YF + 1, z, f"{COG}[facing=west]")
        put(X1 - 1, YF + 2, z, f"{COG}[facing=west]")
        if z % 2 == 0 and z != LIFT[1]:
            put(X1 - 2, YF + 1, z, st("west", kind=SEAT))
    put(LIFT[0], YF + 1, LIFT[1], "warpbound:grav_lift")
    # ауспики у иллюминатора
    for x, f in ((X0 + 2, "east"), (X1 - 2, "west")):
        put(x, YF + 2, Z1 - 3, PART)
        put(x, YF + 1, Z1 - 3, f"warpbound:auspex[facing={f}]")
    # свет
    for z in range(Z0 + 8, Z1 - 1, 4):
        put(X1 - 1, YF + 6, z, "warpbound:lumen_wall[facing=west]")
        if abs(z - chart_z) > 4:
            put(X0 + 1, YF + 6, z, "warpbound:lumen_wall[facing=east]")
    for z in (Z0 + 8, ZD, Z1 - 4):
        for x in (CX - 3, CX + 3):
            put(x, YC - 1, z, "warpbound:lumen_ceiling")

    # ---- износ: трещины в кирпиче и копоть на обшивке
    rng = random.Random(2042)
    for p, (b, stage) in list(cells.items()):
        if X0 <= p[0] <= X1 and Z0 <= p[2] <= Z1 and YF <= p[1] <= YC:
            if b == GOTHIC and rng.random() < 0.12:
                cells[p] = ("minecraft:cracked_polished_blackstone_bricks", stage)
            elif b == HULL and rng.random() < 0.1:
                cells[p] = ("warpbound:scorched_hull_plating", stage)
            elif b == TILES and rng.random() < 0.1:
                cells[p] = ("minecraft:cracked_deepslate_tiles", stage)
    return (CX, YF + 4, Z0 + 3)   # точка появления: на помосте между троном и пультом
