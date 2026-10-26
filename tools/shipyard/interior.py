"""
Интерьер лёгкого крейсера внутри его корпуса (модель автора, масштаб 2,0 → 45×55×153 блоков).

Отсеки вырезаются только там, где корпус сплошной, и никогда — во внешнем слое: снаружи корабль не меняется.
Стенка корпуса остаётся толщиной в блок; со стороны отсека её облицовывают по палитре отсека.
Компоновка и приёмы — по docs/research/ship-interior.md:
  корма      — энгинариум на всю высоту: плазменный реактор в свинцовом кольце, варп-двигатель за решётками,
               мостки на двух ярусах, трубы, алтарь Омниссии;
  середина   — хребет-неф: центральный проход под рёбрами-арками, по бортам орудийные палубы с казённиками,
               над ними галереи-кубрики с койками;
  надстройка — мостик-амфитеатр: трон на возвышении, пульт, голостол, ауспики, обзорный иллюминатор в нос,
               над ним купол навигатора; под мостиком — анклав Механикус и телепортариум;
  нос        — внизу торпедный отсек, наверху часовня под нервюрным сводом;
  вход       — люк в киле-плавнике и шахта с лестницей в неф.
Координаты: x поперёк (центр CX), y вверх, z от кормы к носу.
"""
from collections import defaultdict

CX = 22

# ---------------------------------------------------------------- блоки
B = dict(
    hull="warpbound:hull_plating", panel="warpbound:plasteel_panel", riveted="warpbound:riveted_plasteel_panel",
    vent="warpbound:plasteel_vent", hazard="warpbound:hazard_panel", grating="warpbound:deck_grating",
    brass="warpbound:brass_trim", lead="warpbound:lead_block",
    gothic="minecraft:polished_blackstone_bricks", gothic2="minecraft:chiseled_polished_blackstone",
    gilded="minecraft:gilded_blackstone", deep="minecraft:polished_deepslate", tiles="minecraft:deepslate_tiles",
    dbricks="minecraft:deepslate_bricks", tuff="minecraft:tuff_bricks", ctuff="minecraft:chiseled_tuff",
    gold="minecraft:gold_block", red="minecraft:red_concrete", redwool="minecraft:red_wool", dark="minecraft:blackstone",
    copper="minecraft:waxed_cut_copper", copper2="minecraft:waxed_oxidized_cut_copper", cgrate="minecraft:waxed_copper_grate",
    oak="minecraft:dark_oak_planks", glass="minecraft:glass", stained="minecraft:orange_stained_glass",
    glow="minecraft:shroomlight", soul="minecraft:soul_lantern[hanging=false]", magma="minecraft:magma_block",
    chain="minecraft:chain[axis=y]", bars="minecraft:iron_bars", candle="minecraft:candle[candles=4,lit=true]",
    skull="minecraft:skeleton_skull", part="warpbound:fixture_part", air="minecraft:air",
)
STAIRS = "minecraft:polished_blackstone_brick_stairs"
SLAB = "minecraft:polished_blackstone_brick_slab"
TSTAIRS = "minecraft:deepslate_tile_stairs"


def stairs(facing, top=False, kind=STAIRS):
    return f"{kind}[facing={facing},half={'top' if top else 'bottom'}]"


def slab(top=False, kind=SLAB):
    return f"{kind}[type={'top' if top else 'bottom'}]"


def lumen(facing):
    return f"warpbound:lumen_wall[facing={facing}]"


def red_lamp(facing):
    return f"warpbound:emergency_lumen[facing={facing}]"


def rad(facing):
    return f"warpbound:radiation_sign[facing={facing}]"


def cog(facing):
    return f"warpbound:cogitator_bank[facing={facing}]"


def pipe(axis):
    return f"warpbound:coolant_pipe[axis={axis}]"


def conduit(axis):
    return f"warpbound:geller_conduit[axis={axis}]"


def door():
    return "warpbound:bulkhead_door[open=false,locked=false]"


def banner(facing):
    return f"minecraft:red_wall_banner[facing={facing}]"


class Interior:
    """Режет отсеки в сплошном корпусе и ставит убранство. Пишет прямо в словарь клеток корабля."""

    def __init__(self, cells, solid, outer):
        self.cells = cells          # (x, y, z) -> (блок, этап)
        self.solid = solid
        self.outer = outer
        self.air = set()            # вырезанные клетки
        self.room_of = {}           # клетка воздуха -> палитра отсека
        self.reactor = None
        self.spawn = None

    # ---- базовые операции
    def free(self, p):
        return p in self.solid and p not in self.outer

    def carve(self, x0, x1, y0, y1, z0, z1, pal):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    p = (x, y, z)
                    if self.free(p):
                        self.air.add(p)
                        self.room_of[p] = pal

    def put(self, x, y, z, block, force=False):
        """Убранство — только в вырезанный воздух (или на облицовку, если force)."""
        p = (x, y, z)
        if p in self.air or force and self.free(p):
            if block == B["air"]:
                self.cells.pop(p, None)
            else:
                self.cells[p] = (block, "modules")
            return True
        return False

    def is_air(self, x, y, z):
        return (x, y, z) in self.air

    # ---- облицовка: стены, пол, потолок по палитре отсека; лишняя толща корпуса не ставится вовсе
    def finish(self):
        dirs = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
        lining = {}
        for p in self.air:
            pal = self.room_of[p]
            for d in dirs:
                n = (p[0] + d[0], p[1] + d[1], p[2] + d[2])
                if n in self.air or n not in self.solid:
                    continue
                if n in self.outer and n in self.cells and d[1] == 0:
                    # внешний слой со стороны отсека — облицовка поверх (снаружи тот же блок не виден)
                    pass
                lining.setdefault(n, (pal, d))
        for n, (pal, d) in lining.items():
            if n in self.outer:
                continue                      # внешний слой не трогаем: его видно снаружи
            if d[1] == 1:
                block = pal["ceiling"]
            elif d[1] == -1:
                block = pal["floor"](n)
            else:
                block = pal["wall"](n)
            self.cells[n] = (block, "modules")
        # толща корпуса, не граничащая ни с отсеком, ни с наружей, — не нужна (меньше блоков в структуре)
        for p in list(self.cells):
            if p in self.solid and p not in self.outer and p not in lining and p not in self.air:
                if self.cells[p][1] != "modules":
                    del self.cells[p]
        for p in self.air:
            if p in self.cells and self.cells[p][0] != B["air"] and self.cells[p][1] != "modules":
                del self.cells[p]

    # ---- приёмы детализации
    def ribs(self, x0, x1, y_floor, y_top, z0, z1, every=4, mat="gothic"):
        """Рёбра-шпангоуты: пилястры у стен, капитель, полуарки из перевёрнутых ступеней под потолком."""
        for z in range(z0 + 1, z1, every):
            for x, inward in ((x0, "east"), (x1, "west")):
                for y in range(y_floor, y_top - 1):
                    self.put(x, y, z, B[mat])
                self.put(x, y_top - 1, z, B["gothic2"])
            self.put(x0 + 1, y_top, z, stairs("west", True))
            self.put(x1 - 1, y_top, z, stairs("east", True))
            for x in range(x0 + 2, x1 - 1):
                self.put(x, y_top + 1 if self.is_air(x, y_top + 1, z) else y_top, z, slab(True))

    def hanging_lamps(self, xs, y_top, z0, z1, every=6, drop=(2, 3)):
        for i, z in enumerate(range(z0 + 2, z1, every)):
            for x in xs:
                d = drop[i % len(drop)]
                top = y_top
                while self.is_air(x, top + 1, z):
                    top += 1
                for k in range(d):
                    self.put(x, top - k, z, B["chain"])
                self.put(x, top - d, z, "warpbound:lumen_ceiling")

    def window(self, cells_xy, start, step, pal, glass, reach=8):
        """Окно наружу: от стенки отсека идём по направлению step до внешнего слоя, ставим стекло, толщу вырезаем."""
        for (a, b) in cells_xy:
            p = start(a, b)
            path = []
            for _ in range(reach):
                if p in self.outer:
                    for q in path:
                        self.air.add(q)
                        self.room_of[q] = pal
                    self.cells[p] = (glass, "modules")
                    break
                if p in self.solid:
                    path.append(p)
                p = (p[0] + step[0], p[1] + step[1], p[2] + step[2])

    def ceiling_run(self, x, y, z0, z1, block):
        for z in range(z0, z1 + 1):
            self.put(x, y, z, block)


# ---------------------------------------------------------------- палитры отсеков

def pal(wall, floor, ceiling):
    return {"wall": wall, "floor": floor, "ceiling": ceiling}


def panel_wall(p):
    """Стена: тёмный цоколь, утопленные панели между пилястрами, решётки вентиляции."""
    x, y, z = p
    if y % 7 in (0, 1):
        return B["tiles"]
    if z % 4 == 1:
        return B["gothic"]
    return B["riveted"] if (y + z) % 5 == 0 else (B["vent"] if y % 7 == 5 and z % 4 == 3 else B["panel"])


def gothic_wall(p):
    x, y, z = p
    if z % 4 == 1:
        return B["gothic2"] if y % 5 == 0 else B["gothic"]
    return B["dbricks"] if y % 6 < 2 else B["gothic"]


def machine_wall(p):
    x, y, z = p
    if z % 5 == 0:
        return B["hull"]
    return B["copper"] if y % 6 == 0 else (B["cgrate"] if (y + z) % 7 == 0 else B["hull"])


def deck_floor(p):
    x, y, z = p
    if x == CX:
        return B["brass"] if z % 4 else B["gilded"]
    return B["tiles"] if (x + z) % 2 else B["deep"]


def grate_floor(p):
    x, y, z = p
    return B["grating"] if (x + z) % 3 else B["hazard"] if z % 9 == 0 else B["deep"]


PAL_NAVE = pal(panel_wall, deck_floor, B["dbricks"])
PAL_CHAPEL = pal(gothic_wall, lambda p: B["red"] if abs(p[0] - CX) <= 1 else B["tiles"], B["gothic"])
PAL_ENGINE = pal(machine_wall, grate_floor, B["hull"])
PAL_BRIDGE = pal(gothic_wall, deck_floor, B["gothic"])
PAL_SERVICE = pal(panel_wall, lambda p: B["deep"], B["tiles"])
PAL_TORPEDO = pal(machine_wall, lambda p: B["hazard"] if p[2] % 6 == 0 else B["deep"], B["hull"])


# ---------------------------------------------------------------- отсеки

def enginarium(it):
    """Корма: зал на всю высоту. Реактор в свинцовом кольце, варп-двигатель у кормы, мостки, трубы, алтарь."""
    x0, x1, yf, yt, z0, z1 = 13, 31, 15, 34, 3, 31
    it.carve(x0, x1, yf, yt, z0, z1, PAL_ENGINE)
    # варп-двигатель: синяя стена пламени за решётками у кормы
    for x in range(16, 29):
        for y in range(yf, yf + 11):
            z = z0
            if it.is_air(x, y, z):
                it.put(x, y, z, B["soul"] if (x + y) % 3 == 0 and y % 2 == 0 else B["bars"])
        it.put(x, yf + 11, z0 + 1, B["gothic"])
    # плазменный реактор: ядро 3×3×4 + части, свинцовое кольцо, трубы охладителя к потолку
    rx, rz = CX, 16
    for dx in (-1, 0, 1):
        for dy in range(4):
            for dz in (-1, 0, 1):
                it.put(rx + dx, yf + dy, rz + dz, B["part"])
    it.put(rx, yf, rz, "warpbound:reactor_core[facing=north]")
    it.reactor = (rx, yf, rz)
    for x in range(rx - 4, rx + 5):
        for z in range(rz - 4, rz + 5):
            ring = max(abs(x - rx), abs(z - rz)) == 4
            if ring and abs(z - rz) > 1:
                it.put(x, yf, z, B["lead"])
                it.put(x, yf + 1, z, B["bars"] if (x + z) % 2 else B["lead"])
            elif max(abs(x - rx), abs(z - rz)) == 5:
                it.put(x, yf - 1, z, B["hazard"], force=True)
    for x, z in ((rx - 4, rz - 4), (rx + 4, rz - 4), (rx - 4, rz + 4), (rx + 4, rz + 4)):
        for y in range(yf + 2, yt + 1):
            it.put(x, y, z, pipe("y"))
    for y in (yt - 1, yt - 3):
        it.ceiling_run(rx - 4, y, z0 + 1, z1 - 1, pipe("z"))
        it.ceiling_run(rx + 4, y, z0 + 1, z1 - 1, pipe("z"))
    # мостки по бортам на втором ярусе, перила, лестницы
    gy = yf + 8
    for z in range(z0 + 1, z1):
        for x in (x0 + 1, x0 + 2, x1 - 2, x1 - 1):
            it.put(x, gy, z, B["grating"])
        it.put(x0 + 3, gy + 1, z, B["bars"])
        it.put(x1 - 3, gy + 1, z, B["bars"])
    for k in range(8):                                      # лестница на мостки у носовой стены
        it.put(x0 + 1, yf + k, z1 - 2 - k, stairs("north", kind=TSTAIRS))
        it.put(x1 - 1, yf + k, z1 - 2 - k, stairs("north", kind=TSTAIRS))
    # знаки радиации и красные лампы на стенах у реактора, пульты техножрецов
    for z in (rz - 3, rz + 3):
        it.put(x0, yf + 3, z, rad("east"))
        it.put(x1, yf + 3, z, rad("west"))
    for z in range(z0 + 3, z1, 6):
        it.put(x0 + 1, yf + 5, z, red_lamp("east"))
        it.put(x1 - 1, yf + 5, z, red_lamp("west"))
        it.put(x0 + 1, gy + 3, z, lumen("east"))
        it.put(x1 - 1, gy + 3, z, lumen("west"))
    for z in (rz - 6, rz + 6):
        it.put(x0 + 1, yf, z, cog("east"))
        it.put(x1 - 1, yf, z, cog("west"))
    # кормовые генераторы Поля Геллера по углам
    for x in (x0 + 2, x1 - 2):
        for dy in (1, 2):
            it.put(x, yf + dy, z0 + 4, B["part"])
        it.put(x, yf, z0 + 4, "warpbound:geller_node[facing=south]")
        for y in range(yf + 3, gy):
            it.put(x, y, z0 + 4, conduit("y"))
    # алтарь Омниссии у носовой стены: шестерня из меди, свечи, череп
    az = z1 - 1
    for x in range(CX - 2, CX + 3):
        it.put(x, yf, az, B["gothic"])
        it.put(x, yf + 1, az, B["candle"] if abs(x - CX) == 2 else B["copper"] if x != CX else B["skull"])
    it.put(CX, yf + 2, az, B["copper2"])
    it.put(CX - 1, yf + 3, az, B["copper2"])
    it.put(CX + 1, yf + 3, az, B["copper2"])
    it.put(CX, yf + 4, az, B["copper2"])
    it.hanging_lamps((CX - 6, CX + 6), yt, z0, z1, every=7, drop=(3, 5))


def nave(it):
    """Хребет: центральный неф под арками, по бортам орудийные палубы, над ними галереи-кубрики."""
    x0, x1, yf, yt, z0, z1 = 15, 29, 21, 31, 52, 94
    it.carve(x0, x1, yf, yt, z0, z1, PAL_NAVE)
    # аркада: колонны между нефом и бортовыми палубами
    for z in range(z0 + 2, z1, 4):
        for x in (CX - 3, CX + 3):
            it.put(x, yf, z, stairs("north"))
            for y in range(yf + 1, yf + 5):
                it.put(x, y, z, B["gothic"])
            it.put(x, yf + 5, z, B["gothic2"])
        it.put(CX - 2, yf + 5, z, stairs("west", True))
        it.put(CX + 2, yf + 5, z, stairs("east", True))
        it.put(CX - 2, yf + 3, z, lumen("east"))
        it.put(CX + 2, yf + 3, z, lumen("west"))
    # галереи над бортовыми палубами: пол, перила, койки в два яруса
    gy = yf + 5
    for z in range(z0 + 1, z1):
        for x in list(range(x0, CX - 3)) + list(range(CX + 4, x1 + 1)):
            it.put(x, gy, z, B["oak"] if (x + z) % 2 else B["deep"])
        it.put(CX - 4, gy + 1, z, B["bars"])
        it.put(CX + 4, gy + 1, z, B["bars"])
    for z in range(z0 + 3, z1 - 2, 3):
        for x, f in ((x0, "east"), (x1, "west")):
            it.put(x, gy + 1, z, f"minecraft:red_bed[facing={'west' if f == 'east' else 'east'},part=head]")
            it.put(x + (1 if f == "east" else -1), gy + 1, z, f"minecraft:red_bed[facing={'west' if f == 'east' else 'east'},part=foot]")
            it.put(x, gy + 3, z, B["chain"])
        it.put(x0 + 2, gy + 1, z + 1, "minecraft:barrel[facing=up]")
        it.put(x1 - 2, gy + 1, z + 1, "minecraft:barrel[facing=up]")
    for k in range(5):                                      # лестницы на галереи
        it.put(x0 + 2, yf + k, z0 + 2 + k, stairs("south", kind=TSTAIRS))
        it.put(x1 - 2, yf + k, z0 + 2 + k, stairs("south", kind=TSTAIRS))
    # бортовые батареи: казённики к борту, тележки со снарядами, красный свет
    for z in range(z0 + 4, z1 - 2, 8):
        for x, f in ((x0, "east"), (x1, "west")):
            d = 1 if f == "east" else -1
            for dz in (0, 1):
                it.put(x, yf, z + dz, B["dark"])
                it.put(x, yf + 1, z + dz, "minecraft:polished_basalt[axis=x]")
                it.put(x + d, yf + 1, z + dz, B["dark"])
            it.put(x + d * 2, yf, z, "minecraft:minecart")
            it.put(x + d, yf + 3, z + 2, red_lamp(f))
            it.put(x + d * 2, yf, z + 3, "minecraft:polished_basalt[axis=y]")
    # центральный проход: ковёр-дорожка, лампы на цепях, трубы под сводом, вокс-решётки
    it.hanging_lamps((CX,), yt, z0, z1, every=6, drop=(2, 4))
    it.ceiling_run(CX - 2, yt, z0 + 1, z1 - 1, conduit("z"))
    it.ceiling_run(CX + 2, yt, z0 + 1, z1 - 1, pipe("z"))
    for z in range(z0 + 6, z1, 12):
        it.put(CX - 2, yf + 4, z, "warpbound:vox_grille[facing=east]")
        it.put(CX + 2, yf + 4, z, banner("west"))
    # гермодвери в обоих концах
    for z in (z0, z1):
        for x in range(CX - 1, CX + 2):
            for y in range(yf, yf + 3):
                it.put(x, y, z, door())


def bridge(it):
    """Мостик-амфитеатр в надстройке: трон на возвышении, пульт, голостол, ауспики, иллюминатор в нос, купол навигатора."""
    x0, x1, yf, yt, z0, z1 = 12, 32, 40, 48, 36, 50
    it.carve(x0, x1, yf, yt, z0, z1, PAL_BRIDGE)
    it.ribs(x0, x1, yf, yt - 1, z0, z1, every=4)
    # возвышение у кормовой стены: трон смотрит в нос, перед ним пульт
    for x in range(CX - 4, CX + 5):
        for z in range(z0, z0 + 4):
            it.put(x, yf, z, B["deep"])
        it.put(x, yf, z0 + 4, stairs("north", kind=TSTAIRS))
    it.put(CX, yf + 1, z0 + 1, "warpbound:command_throne[facing=south]")
    it.put(CX, yf + 4, z0, B["gold"])
    for dx in (-1, 1):
        it.put(CX + dx, yf + 1, z0 + 3, B["part"])
    it.put(CX, yf + 1, z0 + 3, "warpbound:command_console[facing=north]")
    it.spawn = (CX, yf + 1, z0 + 6)
    # голостол навигации и ауспики у бортов
    for dx in (-1, 0, 1):
        for dz in (0, 1):
            it.put(CX + dx, yf, z0 + 8 + dz, B["part"])
    it.put(CX, yf, z0 + 8, "warpbound:nav_table[facing=north]")
    for x, f in ((x0 + 2, "east"), (x1 - 2, "west")):
        it.put(x, yf + 1, z0 + 9, B["part"])
        it.put(x, yf, z0 + 9, f"warpbound:auspex[facing={f}]")
    # ямы с когитаторами вдоль бортов, люмены, знамёна
    for z in range(z0 + 2, z1 - 1, 3):
        it.put(x0, yf, z, cog("east"))
        it.put(x1, yf, z, cog("west"))
        it.put(x0 + 1, yf + 3, z, lumen("east"))
        it.put(x1 - 1, yf + 3, z, lumen("west"))
    # обзорный иллюминатор в нос: сквозь толщу носовой стены надстройки — броневое стекло (ставни закроют его)
    it.window([(x, y) for x in range(CX - 6, CX + 7) for y in range(yf + 1, yt)],
              lambda x, y: (x, y, z0 + 6), (0, 0, 1), PAL_BRIDGE, B["glass"], reach=14)
    # люстры мостика: три ряда ламп на цепях
    it.hanging_lamps((CX - 6, CX, CX + 6), yt, z0, z1, every=4, drop=(2, 3))
    for x in (CX - 7, CX + 7):
        for y in range(yf + 1, yt - 1):
            it.put(x, y, z1, banner("north"))
    # купол навигатора над мостиком: колодец со стеклом наверху
    it.carve(CX - 3, CX + 3, yt + 1, yt + 5, z0 + 4, z0 + 10, PAL_BRIDGE)
    it.window([(x, z) for x in range(CX - 3, CX + 4) for z in range(z0 + 4, z0 + 11)],
              lambda x, z: (x, yf + 4, z), (0, 1, 0), PAL_BRIDGE, B["glass"], reach=14)
    it.put(CX, yt + 1, z0 + 7, "minecraft:lectern[facing=south]")


def hub(it):
    """Под мостиком: анклав Механикус, телепортариум и лестница вверх на мостик."""
    x0, x1, yf, yt, z0, z1 = 14, 30, 17, 25, 34, 50
    it.carve(x0, x1, yf, yt, z0, z1, PAL_SERVICE)
    # телепортариум: площадка 3×3 в полу
    tx, tz = CX - 4, z0 + 6
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            it.put(tx + dx, yf - 1, tz + dz, B["part"], force=True)
    it.put(tx, yf - 1, tz, "warpbound:teleportarium_pad[facing=south]", force=True)
    for dx, dz in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
        it.put(tx + dx, yf, tz + dz, conduit("y"))
        it.put(tx + dx, yf + 1, tz + dz, "minecraft:sea_lantern")
    # анклав Механикус: алтарь-когитатор, ниши сервиторов
    for z in (z0 + 4, z0 + 7, z0 + 10):
        it.put(x1, yf, z, cog("west"))
        it.put(x1, yf + 1, z, B["skull"])
        it.put(x1, yf + 3, z, lumen("west"))
    # шахта с лестницей на мостик — внутри левой опоры надстройки (середина между опорами открыта наружу)
    sx, sz = 16, 44
    it.carve(sx, sx, yf, 40, sz, sz, PAL_SERVICE)
    for y in range(yf, 40):
        it.put(sx, y, sz, "minecraft:ladder[facing=east]")
    # проход в неф
    for x in range(CX - 1, CX + 2):
        for y in range(yf, yf + 3):
            it.put(x, y, z1, door())


def prow(it):
    """Нос: внизу торпедный отсек со стеллажами, наверху часовня под сводом."""
    # торпедный отсек
    x0, x1, yf, yt, z0, z1 = 16, 28, 6, 16, 96, 134
    it.carve(x0, x1, yf, yt, z0, z1, PAL_TORPEDO)
    for z in range(z0 + 3, z1 - 3, 2):
        for x in (x0 + 1, x1 - 1):
            it.put(x, yf + 1, z, "minecraft:polished_basalt[axis=z]")
            it.put(x, yf + 3, z, "minecraft:polished_basalt[axis=z]")
        it.put(x0 + 1, yf, z, B["dark"])
        it.put(x1 - 1, yf, z, B["dark"])
    for z in range(z0 + 2, z1, 6):
        it.put(CX, yt, z, B["chain"])
        it.put(CX, yt - 1, z, B["chain"])
        it.put(CX, yt - 2, z, "minecraft:iron_block")
        it.put(x0 + 1, yf + 5, z, red_lamp("east"))
        it.put(x1 - 1, yf + 5, z, red_lamp("west"))
    for z in range(z0, z1):
        it.put(CX - 2, yf, z, "minecraft:rail")
        it.put(CX + 2, yf, z, "minecraft:rail")
    # часовня
    x0, x1, yf, yt, z0, z1 = 16, 28, 19, 32, 97, 124
    it.carve(x0, x1, yf, yt, z0, z1, PAL_CHAPEL)
    it.ribs(x0, x1, yf, yt - 1, z0, z1, every=3)
    for z in range(z0 + 3, z1 - 6, 2):                      # скамьи
        for x in list(range(x0 + 2, CX - 1)) + list(range(CX + 2, x1 - 1)):
            it.put(x, yf, z, stairs("north", kind="minecraft:dark_oak_stairs"))
    az = z1 - 2                                             # алтарь, аквила, свечи, статуя
    for x in range(CX - 2, CX + 3):
        it.put(x, yf, az, B["gothic2"])
    it.put(CX, yf + 1, az, "minecraft:lectern[facing=north]")
    for x in (CX - 2, CX + 2):
        it.put(x, yf + 1, az, B["candle"])
    for y, xs in ((yf + 5, range(CX - 4, CX + 5)), (yf + 6, range(CX - 2, CX + 3)), (yf + 4, range(CX - 1, CX + 2)),
                  (yf + 7, (CX,))):
        for x in xs:
            it.put(x, y, z1, B["gold"])
    for x in (CX - 1, CX, CX + 1):
        it.put(x, yf + 1, z1, B["gilded"])
        it.put(x, yf + 2, z1, B["gilded"])
    # витражи в бортах часовни: внешний слой — оранжевое стекло
    for z in range(z0 + 2, z1 - 2, 3):
        for y in range(yf + 3, yf + 9):
            for x in (x0 - 1, x1 + 1, x0 - 2, x1 + 2):
                if (x, y, z) in it.outer:
                    it.cells[(x, y, z)] = (B["stained"], "modules")
    it.hanging_lamps((CX - 3, CX + 3), yt, z0, z1, every=5, drop=(3, 4))
    for z in (z0, ):                                        # проход из нефа
        for x in range(CX - 1, CX + 2):
            for y in range(yf, yf + 3):
                it.put(x, y, z, door())
    # спуск из нефа в часовню и в торпедный отсек
    it.carve(CX - 1, CX + 1, 17, 22, 94, 97, PAL_SERVICE)
    for k in range(6):
        it.put(CX - 1, 22 - k, 95 + (k % 2), B["air"])


def entry(it):
    """Вход с верфи: люк сбоку киля-плавника, шахта с лестницей в неф."""
    x, z = CX, 53
    for y in range(0, 21):                                  # шахта: вырезаем и у самого низа (там киль — внешний слой)
        p = (x, y, z)
        if p in it.solid:
            it.air.add(p)
            it.room_of[p] = PAL_SERVICE
    for y in range(0, 21):
        it.put(x, y, z, "minecraft:ladder[facing=north]")
    # люк: внешний слой с бортов киля у самой палубы стапеля (2 блока высотой) — открытая гермодверь
    for y in (0, 1):
        for dx in (-1, 1):
            p = (x + dx, y, z)
            if p in it.solid:
                it.cells[p] = ("warpbound:boarding_hatch[open=true,locked=false]", "modules")


def build(cells, solid, outer):
    it = Interior(cells, solid, outer)
    enginarium(it)
    hub(it)
    bridge(it)
    nave(it)
    prow(it)
    entry(it)
    it.finish()
    return it
