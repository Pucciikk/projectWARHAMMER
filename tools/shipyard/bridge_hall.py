"""
Мостик крейсера — купол на месте тесной надстройки модели.

Зал — половина вытянутого эллипсоида (19 в ширину, 18 в высоту, 31 в длину), срезанная спереди плоской стеной:
она получается стрельчатой аркой, в ней высокие узкие окна на варп. Свод ребристый, по бокам — узкие ланцеты,
в макушке — стеклянный фонарь навигатора. Внутри: трон на возвышении у кормы, командный пульт перед ним,
по бортам ряды «пульт — кресло» лицом к носу, голостол у окон, ауспики, люстры на цепях.
Стекло мостика бронеставни не закрывают (ShipLaunch.scan): капитан смотрит в варп.
"""

CX = 22
ZC = 48                 # центр эллипсоида по длине
A, B, C = 9.5, 17.5, 20.5   # полуоси: ширина, высота, длина
Z0, Z1 = 28, 58         # корма зала (вершина яйца) и носовая стена (срез)
YF = 39                 # пол
GOTHIC = "minecraft:polished_blackstone_bricks"
RIB = "minecraft:chiseled_polished_blackstone"
DEEP = "minecraft:polished_deepslate"
TILES = "minecraft:deepslate_tiles"
HULL = "warpbound:hull_plating"
BRASS = "warpbound:brass_trim"
GOLD = "minecraft:gold_block"
GLASS = "minecraft:glass"
RED = "minecraft:red_concrete"
PART = "warpbound:fixture_part"
WALL_POST = "minecraft:polished_blackstone_wall"
STAIRS = "minecraft:polished_blackstone_brick_stairs"
TSTAIRS = "minecraft:deepslate_tile_stairs"
SEAT = "minecraft:dark_oak_stairs"
NB = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))


def st(facing, top=False, kind=STAIRS):
    return f"{kind}[facing={facing},half={'top' if top else 'bottom'}]"


def inside(x, y, z):
    """Точка внутри купола (вместе с оболочкой)."""
    if y < YF or z > Z1:
        return False
    return ((x - CX) / A) ** 2 + ((y - YF) / B) ** 2 + ((z - ZC) / C) ** 2 <= 1.0


def build(cells):
    """Пишет мостик в словарь клеток корабля (этап modules), сносит старую надстройку на его месте.
    Возвращает точку появления на борту."""
    def put(x, y, z, b):
        cells[(x, y, z)] = (b, "modules")

    xs = range(CX - 11, CX + 12)
    ys = range(YF, YF + 20)
    zs = range(Z0 - 1, Z1 + 2)
    vol = {(x, y, z) for x in xs for y in ys for z in zs if inside(x, y, z)}
    shell = {p for p in vol if p[1] == YF or p[2] == Z1
             or any((p[0] + a, p[1] + b, p[2] + c) not in vol for a, b, c in NB)}
    air = vol - shell

    def roof(x, z):
        """Нижняя клетка оболочки над (x, z) — потолок."""
        for y in ys:
            if (x, y, z) in shell and y > YF:
                return y
        return None

    def front_top(x):
        return max((y for y in ys if (x, y, Z1) in vol), default=YF)

    # снести старую надстройку в габарите купола
    for (x, y, z) in list(cells):
        if CX - 11 <= x <= CX + 11 and Z0 - 1 <= z <= Z1 + 1 and y >= YF:
            del cells[(x, y, z)]
    # шея: от верха корпуса до пола — цоколь из обшивки с готической кромкой
    tops = {}
    for (x, y, z) in cells:
        if y < YF and tops.get((x, z), -1) < y:
            tops[(x, z)] = y
    floor = {(x, z) for (x, y, z) in vol if y == YF}
    for (x, z) in floor:
        edge = any((x + a, z + c) not in floor for a, c in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        for y in range(tops.get((x, z), YF - 8) + 1, YF):
            put(x, y, z, GOTHIC if edge and (y + z) % 4 else DEEP)

    # ---- оболочка: кирпич, рёбра свода через 4, латунный конёк
    for (x, y, z) in shell:
        if y == YF:
            b = RED if x == CX and z >= Z0 + 9 else (TILES if (x + z) % 2 else DEEP)
        elif z == Z1:
            b = GOTHIC
        elif (z - Z0) % 4 == 0:
            b = RIB
        elif x == CX:
            b = BRASS
        else:
            b = GOTHIC if (x + y + z) % 5 else HULL
        put(x, y, z, b)
    # ---- носовая стена: стрельчатые окна разной ширины, средники с латунными кольцами, розетка
    for (x, y, z) in shell:
        if z != Z1 or y <= YF + 1:
            continue
        d = x - CX
        top = front_top(x)
        if abs(d) in (2, 5):                       # средники
            put(x, y, z, BRASS if (y - YF) % 4 == 0 else GOTHIC)
        elif abs(d) <= 1 and y <= YF + 11:         # центральное окно 3 в ширину
            put(x, y, z, GLASS)
        elif abs(d) in (3, 4, 6) and y <= top - 1:  # боковые узкие окна, острие упирается в свод
            put(x, y, z, GLASS)
    for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, 1), (0, -1)):  # розетка над центральным окном
        put(CX + dx, YF + 13 + dy, Z1, GLASS)
    put(CX - 1, YF + 12, Z1, st("east", True))
    put(CX + 1, YF + 12, Z1, st("west", True))
    # ---- бортовые ланцеты между рёбрами
    # только там, где стена отвесная: снаружи пусто, внутри воздух — ровная вертикальная полоса
    for (x, y, z) in shell:
        sx = 1 if x > CX else -1
        if ((z - Z0) % 4 == 2 and YF + 2 <= y <= YF + 7 and x != CX and Z0 + 3 < z < Z1 - 1
                and (x + sx, y, z) not in vol and (x - sx, y, z) in air):
            put(x, y, z, GLASS)
    # ---- фонарь навигатора в макушке
    for (x, y, z) in shell:
        if y >= YF + 14 and abs(x - CX) <= 2 and abs(z - ZC) <= 4:
            put(x, y, z, GLASS)

    # ---- снаружи: контрфорсы у основания рёбер, шпиль над носовой аркой, пинакли по краям арки
    for z in range(Z0 + 4, Z1, 4):
        side = [x for x in xs if (x, YF + 1, z) in shell]
        if not side:
            continue
        for x, d in ((min(side), -1), (max(side), 1)):
            for y in range(YF - 2, YF + 5):
                put(x + d, y, z, GOTHIC if y % 3 else RIB)
            put(x + d, YF + 5, z, st("east" if d < 0 else "west"))
    apex = front_top(CX)
    for y in range(apex + 1, apex + 5):
        put(CX, y, Z1, WALL_POST)
    put(CX, apex + 5, Z1, "minecraft:lightning_rod")
    for d in (-7, 7):
        t = front_top(CX + d)
        for y in range(t + 1, t + 3):
            put(CX + d, y, Z1, WALL_POST)

    # ---- убранство (ставим только в воздух купола)
    def put_in(x, y, z, b):
        if (x, y, z) in air:
            put(x, y, z, b)

    # возвышение трона: три ступени у кормы
    for step in range(3):
        for x in range(CX - 5 + step, CX + 6 - step):
            for z in range(Z0 + 1, Z0 + 9 - step):
                put_in(x, YF + 1 + step, z, DEEP if (x + z) % 2 else TILES)
            put_in(x, YF + 1 + step, Z0 + 9 - step, st("south", kind=TSTAIRS))
    put(CX, YF + 4, Z0 + 4, "warpbound:command_throne[facing=south]")
    # золотая аквила на своде за троном: крылья по оболочке кормы
    for y, half in ((YF + 9, 4), (YF + 10, 2), (YF + 8, 1)):
        for x in range(CX - half, CX + half + 1):
            z = min((z for z in zs if (x, y, z) in shell), default=None)
            if z is not None:
                put(x, y, z, GOLD)
    # командный пульт перед троном, лицом к нему
    put(CX - 1, YF + 4, Z0 + 6, PART)
    put(CX + 1, YF + 4, Z0 + 6, PART)
    put(CX, YF + 4, Z0 + 6, "warpbound:command_console[facing=north]")
    # ряды экипажа по бортам: пульт и кресло лицом к носу, каждый второй ряд на ступень выше
    for side in (range(CX - 8, CX - 2), range(CX + 3, CX + 9)):
        for i, z in enumerate(range(Z0 + 13, Z1 - 3, 4)):
            lift = 1 if i % 2 == 0 else 0
            for x in side:
                if not all((x, YF + 2 + lift, zz) in air for zz in (z, z + 1)):
                    continue
                if lift:
                    for zz in range(z - 1, z + 3):
                        put_in(x, YF + 1, zz, DEEP)
                put(x, YF + 1 + lift, z + 1, "warpbound:cogitator_bank[facing=north]")
                put(x, YF + 1 + lift, z, st("north", kind=SEAT))
    # голостол у окон и ауспики по краям
    for dx in (-1, 0, 1):
        for dz in (0, 1):
            put_in(CX + dx, YF + 1, Z1 - 6 + dz, PART)
    put(CX, YF + 1, Z1 - 6, "warpbound:nav_table[facing=north]")
    for x, f in ((CX - 6, "east"), (CX + 6, "west")):
        put_in(x, YF + 2, Z1 - 3, PART)
        put_in(x, YF + 1, Z1 - 3, f"warpbound:auspex[facing={f}]")
    # люмены на рёбрах и люстры на цепях из свода
    for z in range(Z0 + 4, Z1, 4):
        row = [x for x in xs if (x, YF + 4, z) in air]
        if row:
            put(min(row), YF + 4, z, "warpbound:lumen_wall[facing=east]")
            put(max(row), YF + 4, z, "warpbound:lumen_wall[facing=west]")
    for z in range(Z0 + 10, Z1 - 2, 6):
        for x in (CX - 4, CX + 4):
            r = roof(x, z)
            if r is None:
                continue
            for y in range(r - 3, r):
                put_in(x, y, z, "minecraft:chain[axis=y]")
            put_in(x, r - 4, z, "warpbound:lumen_ceiling")
    # лаз из шахты анклава (лестница в левой опоре) в пол мостика
    put(16, YF, 44, "minecraft:ladder[facing=east]")
    return (CX, YF + 4, Z0 + 5)   # точка появления: на возвышении между троном и пультом
