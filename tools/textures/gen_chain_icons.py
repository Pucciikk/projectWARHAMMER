#!/usr/bin/env python3
"""
Настоящие значки предметов цепочки вместо заглушек из gen_chain_content.py: 16×16, ванильная манера, свет сверху слева.

    python3 tools/textures/gen_chain_icons.py [--sheet путь.png]

Форма — многоугольники с четырёхтоновой заливкой и автоматическим контуром; один материал — одна палитра,
поэтому слиток, лист и пруток из стали сразу читаются как одно семейство. --sheet собирает лист для просмотра.
"""
import os
import random
import sys
import zlib

from PIL import Image, ImageDraw

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
TEX = os.path.join(ROOT, "src/main/resources/assets/warpbound/textures/item")


def ramp(mid):
    """Четыре тона от материала: тень, середина, свет, блик."""
    d = tuple(int(c * 0.58) for c in mid)
    l = tuple(min(255, int(c * 1.28 + 14)) for c in mid)
    h = tuple(min(255, int(c * 1.55 + 42)) for c in mid)
    return d, tuple(mid), l, h


STEEL = ramp((132, 140, 150))
IRON = ramp((118, 112, 108))
PIG = ramp((86, 80, 78))
COPPER = ramp((186, 104, 62))
LEAD = ramp((96, 104, 128))
BRASS = ramp((190, 146, 60))
PLASTEEL = ramp((158, 170, 178))
CERAMITE = ramp((206, 198, 176))
GUNMETAL = ramp((60, 64, 72))
BLACK = ramp((38, 38, 44))
BONE = ramp((212, 200, 164))
RED = ramp((150, 30, 26))
GREEN = ramp((64, 124, 54))
OLIVE = ramp((96, 104, 60))
PAPER = ramp((214, 196, 150))
SULFUR = ramp((214, 186, 52))
SALT = ramp((222, 220, 210))
CONCRETE = ramp((142, 140, 134))
ASH = ramp((98, 96, 94))
RESIN = ramp((150, 92, 28))
WOOD = ramp((150, 112, 70))
PROMETH = ramp((54, 124, 210))
PLASMA = ramp((70, 200, 220))
RADIUM = ramp((110, 200, 70))
PURPLE = ramp((130, 70, 170))


class Icon:
    def __init__(self, name):
        self.name = name
        self.rng = random.Random(zlib.crc32(name.encode()))
        self.img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        self.px = self.img.load()

    def poly(self, pts, r, flat=False):
        """Многоугольник с заливкой: свет сверху слева, тень снизу справа."""
        mask = Image.new("1", (16, 16), 0)
        ImageDraw.Draw(mask).polygon(pts, fill=1)
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        span = max(1, (max(xs) - min(xs)) + (max(ys) - min(ys)))
        m = mask.load()
        for y in range(16):
            for x in range(16):
                if m[x, y]:
                    t = ((x - min(xs)) + (y - min(ys))) / span
                    t += self.rng.uniform(-0.05, 0.05)
                    c = r[1] if flat else (r[3] if t < 0.14 else r[2] if t < 0.42 else r[1] if t < 0.78 else r[0])
                    self.px[x, y] = (*c, 255)
        return self

    def rect(self, x0, y0, x1, y1, r, flat=False):
        return self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], r, flat)

    def line(self, pts, c):
        ImageDraw.Draw(self.img).line(pts, fill=(*c, 255))
        return self

    def dot(self, x, y, c):
        self.px[x, y] = (*c, 255)
        return self

    def blob(self, cx, cy, rx, ry, r):
        """Комок неправильной формы."""
        pts = []
        for i in range(9):
            import math
            a = 2 * math.pi * i / 9
            k = self.rng.uniform(0.8, 1.15)
            pts.append((cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)))
        return self.poly(pts, r)

    def disc(self, cx, cy, rad, r):
        for y in range(16):
            for x in range(16):
                if (x - cx) ** 2 + (y - cy) ** 2 <= rad * rad:
                    t = ((x - cx) + (y - cy)) / (2.0 * rad) + 0.5
                    c = r[3] if t < 0.2 else r[2] if t < 0.45 else r[1] if t < 0.8 else r[0]
                    self.px[x, y] = (*c, 255)
        return self

    def done(self):
        """Контур: прозрачный сосед непрозрачного пикселя становится тёмным цветом соседа."""
        out = self.img.copy()
        p = out.load()
        for y in range(16):
            for x in range(16):
                if self.px[x, y][3] == 0:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        u, v = x + dx, y + dy
                        if 0 <= u < 16 and 0 <= v < 16 and self.px[u, v][3]:
                            n = self.px[u, v]
                            p[x, y] = (int(n[0] * 0.28), int(n[1] * 0.28), int(n[2] * 0.3), 255)
                            break
        return out


# ---------------------------------------------------------------- формы-семейства

def ingot(i, r):
    i.poly([(2, 11), (5, 5), (14, 5), (12, 11)], r)
    i.line([(5, 6), (13, 6)], r[3])
    i.line([(3, 11), (11, 11)], r[0])


def plate(i, r):
    i.poly([(2, 5), (11, 3), (14, 10), (5, 13)], r)
    i.line([(3, 5), (11, 3)], r[3])
    for x, y in ((4, 6), (10, 5), (11, 9), (5, 11)):
        i.dot(x, y, r[0])


def rod(i, r):
    i.poly([(2, 12), (4, 14), (14, 4), (12, 2)], r)
    i.line([(3, 12), (12, 3)], r[3])
    i.dot(13, 3, r[3])
    i.line([(2, 13), (4, 14)], r[0])


def tube(i, r):
    i.poly([(2, 11), (5, 14), (14, 5), (11, 2)], r)
    i.line([(3, 11), (11, 3)], r[3])
    i.disc(12.5, 3.5, 2.2, r)
    i.dot(12, 3, BLACK[0])
    i.dot(13, 4, BLACK[0])
    i.dot(13, 3, BLACK[1])


def spool(i, r):
    i.rect(5, 3, 11, 13, WOOD)
    i.rect(3, 2, 13, 4, WOOD)
    i.rect(3, 12, 13, 14, WOOD)
    for y in range(5, 12):
        i.line([(4, y), (12, y)], r[3] if y % 3 == 0 else r[2] if y % 3 == 1 else r[1])


def crushed(i, r, clean=False):
    for cx, cy, rx, ry in ((5, 11, 3, 2.6), (11, 11, 3.2, 2.7), (8, 6, 3.2, 3)):
        i.blob(cx, cy, rx, ry, r)
    if clean:
        i.dot(5, 10, (240, 248, 255)).dot(10, 10, (240, 248, 255)).dot(8, 5, (240, 248, 255)).dot(9, 5, (210, 234, 255))
    else:
        for x, y in ((4, 12), (12, 12), (8, 7), (6, 9)):
            i.dot(x, y, ASH[0])


def dust(i, r):
    i.poly([(2, 13), (5, 8), (8, 5), (11, 8), (14, 13)], r)
    for x, y in ((6, 10), (9, 8), (11, 11), (4, 12), (8, 12)):
        i.dot(x, y, r[0])
    i.dot(1, 12, r[1]).dot(14, 11, r[2]).dot(12, 6, r[2])


def coil(i, r):
    i.rect(6, 2, 10, 14, GUNMETAL)
    for y in range(4, 13):
        i.line([(4, y), (12, y)], r[3] if y % 2 == 0 else r[0])
    i.rect(3, 2, 13, 3, GUNMETAL)
    i.rect(3, 13, 13, 14, GUNMETAL)


def board(i, chip=False):
    i.rect(2, 2, 13, 13, GREEN)
    for pts in (((3, 5), (7, 5), (7, 8)), ((3, 10), (6, 10)), ((9, 3), (9, 6), (12, 6)), ((12, 10), (9, 10), (9, 12))):
        i.line(list(pts), BRASS[2])
    i.rect(6, 6, 10, 10, BLACK, flat=True)
    i.dot(7, 7, BLACK[3])
    if chip:
        for x in (3, 12):
            for y in (3, 12):
                i.dot(x, y, (240, 60, 40))


def shell(i, r, tip):
    i.rect(6, 6, 10, 14, r)
    i.poly([(6, 6), (8, 2), (10, 6)], tip)
    i.line([(6, 12), (10, 12)], r[0])
    i.line([(6, 7), (6, 13)], r[3])


def gun(i, grid, palette):
    for y, row in enumerate(grid):
        for x, c in enumerate(row):
            if c != ".":
                i.dot(x, y, palette[c])


GUN_PAL = {"k": (22, 22, 26), "g": GUNMETAL[0], "G": GUNMETAL[1], "w": GUNMETAL[2], "W": GUNMETAL[3], "b": BRASS[0], "B": BRASS[1], "y": BRASS[3],
           "r": RED[0], "R": RED[1], "n": WOOD[0], "N": WOOD[1], "c": PLASMA[1], "C": PLASMA[3], "s": STEEL[1], "S": STEEL[3], "p": PROMETH[1], "P": PROMETH[3]}

BOLTER = ["............kkk.", "...........kSSSk", "..........kGwGsk", ".........kGGwGk.", "........kGwGGk..", ".......kBGwGk...",
          "......kGBGGk....", ".....kGGgGk.....", "....kGkrRGk.....", "...kgGkrRkk.....", "..kgGk.kk.......", ".kgGk...........",
          "kgGk............", "kkk.............", "................", "................"]
PISTOL = ["................", "................", "................", "...kkkkkkkkkk...", "..kGwwwwwwwSSk..", "..kGGGGGGGGGGk..", "..kgGGGBBGkkk...",
          "..kkkgGGGk......", "....kNNkrk......", "....kNNkk.......", "...kNNk.........", "...kNnk.........", "...kkk..........", "................",
          "................", "................"]
STORM = ["...........kkkk.", "..........kSSSSk", ".........kGwSSSk", "........kGGwGGk.", ".......kGwGGGGk.", "......kBGwGkkk..", ".....kGBGGGk....",
         "....kGGgGGk.....", "...kGkrRkGk.....", "..kgGkrRkkk.....", ".kgGk.kk........", "kgGk............", "kkk.............", "................",
         "................", "................"]
FLAMER = ["............kk..", "...........kPPk.", "..........kGwGPk", ".........kGwGk..", "........kGwGk...", ".......kGwGk....", "......kGwGkkk...",
          ".....kGGGGkRRk..", "....kGkGGkRRRRk.", "...kgGkkGkRRRRk.", "..kgGk..kkRRk...", ".kNNk....kkk....", "kNNk............", "kkk.............",
          "................", "................"]
PLASMA_G = ["...........kkkk.", "..........kCCCCk", ".........kGwCCCk", "........kGcwGGk.", ".......kGcwGk...", "......kGcwGGk...", ".....kGwcGGk....",
            "....kBGGGGk.....", "...kGkgRGk......", "..kgGkgRkk......", ".kgGk.kk........", "kgGk............", "kkk.............", "................",
            "................", "................"]

# ---------------------------------------------------------------- все значки


def draw(name):
    i = Icon(name)
    M = {
        "steel_ingot": lambda: ingot(i, STEEL),
        "pig_iron": lambda: ingot(i, PIG),
        "steel_plate": lambda: plate(i, STEEL),
        "ceramite_plate": lambda: plate(i, CERAMITE),
        "armaplas": lambda: (plate(i, OLIVE), i.line([(5, 7), (11, 5)], OLIVE[0]), i.line([(5, 9), (12, 7)], OLIVE[0])),
        "steel_rod": lambda: rod(i, STEEL),
        "steel_tube": lambda: tube(i, STEEL),
        "plasteel_tube": lambda: tube(i, PLASTEEL),
        "steel_wire": lambda: spool(i, STEEL),
        "copper_wire": lambda: spool(i, COPPER),
        "crushed_iron": lambda: crushed(i, IRON),
        "crushed_copper": lambda: crushed(i, COPPER),
        "crushed_lead": lambda: crushed(i, LEAD),
        "washed_iron": lambda: crushed(i, ramp((168, 160, 150)), True),
        "washed_copper": lambda: crushed(i, ramp((222, 134, 82)), True),
        "raw_sulfur": lambda: crushed(i, SULFUR),
        "saltpeter": lambda: (i.poly([(4, 13), (2, 8), (5, 6), (7, 11)], SALT), i.poly([(8, 13), (6, 6), (9, 2), (11, 7)], SALT), i.poly([(10, 13), (11, 8), (14, 7), (14, 12)], SALT)),
        "slag": lambda: (i.blob(8, 9, 5.6, 4.4, ASH), i.dot(6, 8, BLACK[0]), i.dot(10, 7, BLACK[0]), i.dot(8, 11, BLACK[0]), i.dot(11, 10, BLACK[0]), i.dot(5, 11, BLACK[0])),
        "coke": lambda: (i.blob(6, 10, 3.6, 3.2, BLACK), i.blob(10, 7, 3.6, 3.2, BLACK), i.dot(5, 8, GUNMETAL[3]), i.dot(9, 5, GUNMETAL[3]), i.dot(11, 8, GUNMETAL[2])),
        "gypsum": lambda: (i.blob(8, 9, 5, 4.2, SALT), i.line([(5, 7), (10, 11)], CONCRETE[1])),
        "rockrete": lambda: (i.rect(3, 4, 13, 12, CONCRETE), [i.dot(x, y, CONCRETE[0]) for x, y in ((5, 6), (9, 5), (11, 9), (6, 10), (8, 8))]),
        "ferrocrete": lambda: (i.rect(3, 4, 13, 12, CONCRETE), i.line([(3, 7), (13, 7)], STEEL[0]), i.line([(3, 10), (13, 10)], STEEL[0]), i.line([(6, 4), (6, 12)], STEEL[0]), i.line([(10, 4), (10, 12)], STEEL[0])),
        "sulfur": lambda: dust(i, SULFUR),
        "sawdust": lambda: dust(i, WOOD),
        "zinc_dust": lambda: dust(i, ramp((168, 178, 186))),
        "fyceline": lambda: (dust(i, ramp((206, 96, 32))), i.dot(8, 6, (255, 230, 150))),
        "bolt_propellant": lambda: (i.rect(5, 3, 11, 13, BRASS), i.rect(5, 6, 11, 10, RED), i.line([(6, 3), (6, 13)], BRASS[3])),
        "nitrocellulose": lambda: (i.blob(8, 9, 5.4, 4.2, SALT), [i.dot(x, y, SULFUR[1]) for x, y in ((6, 8), (9, 10), (10, 7), (5, 11))]),
        "cellulose": lambda: (i.rect(3, 5, 13, 12, PAPER), i.line([(3, 8), (13, 8)], PAPER[0]), i.line([(3, 10), (13, 10)], PAPER[0])),
        "polymer_resin": lambda: (i.blob(8, 10, 4.6, 3.4, RESIN), i.poly([(6, 8), (8, 3), (10, 8)], RESIN), i.dot(7, 7, RESIN[3])),
        "fabric": lambda: (i.poly([(2, 5), (13, 3), (14, 11), (3, 13)], OLIVE), [i.line([(3, y), (13, y - 2)], OLIVE[0]) for y in (7, 10)]),
        "parchment": lambda: (i.poly([(3, 3), (12, 3), (13, 13), (4, 13)], PAPER), i.rect(2, 2, 13, 3, PAPER), [i.line([(5, y), (11, y)], PAPER[0]) for y in (6, 8, 10)]),
        "herbs": lambda: (i.line([(8, 14), (8, 8)], GREEN[0]), i.poly([(8, 9), (3, 5), (6, 3)], GREEN), i.poly([(8, 8), (13, 4), (10, 2)], GREEN), i.poly([(8, 12), (3, 10), (5, 8)], GREEN), i.poly([(8, 12), (13, 9), (11, 7)], GREEN)),
        "incense": lambda: (i.rect(5, 8, 11, 13, BRASS), i.rect(4, 7, 12, 8, BRASS), i.line([(8, 6), (7, 4), (9, 2)], ASH[3])),
        "synthetic_crystal": lambda: (i.poly([(8, 1), (12, 6), (10, 14), (6, 14), (4, 6)], PLASMA), i.line([(8, 2), (8, 13)], PLASMA[3])),
        "radium_cell": lambda: (i.rect(5, 3, 11, 13, GUNMETAL), i.rect(6, 5, 10, 11, RADIUM), i.rect(5, 2, 11, 3, BRASS), i.rect(5, 13, 11, 14, BRASS)),
        "motive_coil": lambda: coil(i, COPPER),
        "containment_coil": lambda: (coil(i, PLASMA), i.dot(8, 8, PLASMA[3])),
        "cogitator_board": lambda: board(i),
        "logic_engine": lambda: (board(i, True), i.rect(5, 5, 11, 11, GUNMETAL), i.rect(7, 7, 9, 9, RED, flat=True)),
        "servo_2": lambda: (i.disc(8, 8, 5.5, PLASTEEL), i.disc(8, 8, 2.6, BRASS), i.dot(8, 8, BLACK[0])),
        "mr_fuse": lambda: (i.rect(6, 4, 10, 13, BRASS), i.poly([(6, 4), (8, 1), (10, 4)], RED), i.line([(6, 8), (10, 8)], BLACK[0])),
        "suspensor": lambda: (i.disc(8, 8, 5.5, GUNMETAL), i.disc(8, 8, 3.2, PLASMA), i.dot(7, 7, PLASMA[3]), i.line([(2, 8), (0, 8)], BRASS[1]), i.line([(14, 8), (15, 8)], BRASS[1])),
        "field_generator": lambda: (i.rect(3, 4, 13, 12, GUNMETAL), i.disc(8, 8, 3, PLASMA), i.dot(8, 8, PLASMA[3]), i.rect(5, 2, 11, 4, BRASS), i.rect(5, 12, 11, 14, BRASS)),
        "fibre_bundle": lambda: ([i.line([(2, 6 + k), (13, 3 + k * 2)], (PLASMA if k % 2 else COPPER)[2]) for k in range(5)], i.rect(6, 4, 9, 12, BLACK)),
        "neural_interface": lambda: (i.rect(4, 3, 12, 8, GUNMETAL), [i.line([(x, 8), (x, 14)], BRASS[2]) for x in (5, 8, 11)], i.dot(6, 5, (240, 60, 40)), i.dot(10, 5, (60, 240, 120))),
        "auto_senses": lambda: (i.poly([(3, 4), (13, 4), (13, 9), (10, 12), (6, 12), (3, 9)], BLACK), i.rect(4, 6, 7, 8, RED, flat=True), i.rect(9, 6, 12, 8, RED, flat=True)),
        "power_pack": lambda: (i.rect(4, 3, 12, 13, GUNMETAL), i.rect(6, 1, 8, 3, STEEL), i.rect(9, 1, 11, 3, STEEL), i.rect(6, 6, 10, 10, BRASS), i.dot(8, 8, PLASMA[3])),
        "ammo_feed": lambda: ([i.rect(2 + k * 3, 6, 4 + k * 3, 11, BRASS) for k in range(4)], i.rect(2, 8, 13, 9, GUNMETAL, flat=True)),
        "chain_teeth": lambda: ([i.poly([(2 + k * 4, 11), (4 + k * 4, 5), (6 + k * 4, 11)], STEEL) for k in range(3)], i.rect(2, 11, 14, 13, GUNMETAL)),
        "drill_head": lambda: (i.poly([(4, 3), (12, 3), (8, 14)], STEEL), i.line([(5, 5), (11, 7)], BLACK[0]), i.line([(6, 8), (10, 10)], BLACK[0]), i.rect(5, 1, 11, 3, BRASS)),
        "rifled_barrel": lambda: (tube(i, GUNMETAL), [i.dot(4 + k * 2, 12 - k * 2, BRASS[2]) for k in range(4)]),
        "heavy_barrel": lambda: (i.poly([(1, 11), (5, 15), (15, 5), (11, 1)], GUNMETAL), i.line([(2, 11), (11, 2)], GUNMETAL[3]), [i.line([(4 + k * 3, 12 - k * 3), (6 + k * 3, 14 - k * 3)], BRASS[1]) for k in range(3)]),
        "bolter_receiver": lambda: (i.rect(2, 5, 13, 11, GUNMETAL), i.rect(5, 3, 11, 5, BRASS), i.rect(4, 11, 7, 14, GUNMETAL), i.dot(9, 8, RED[1])),
        "bolt_casing": lambda: (i.rect(5, 5, 11, 14, BRASS), i.line([(6, 5), (6, 13)], BRASS[3]), i.rect(5, 13, 11, 14, BRASS[:], flat=True), i.rect(6, 3, 10, 5, BLACK)),
        "bolt_round": lambda: shell(i, BRASS, GUNMETAL),
        "bolt_magazine": lambda: (i.poly([(4, 3), (11, 3), (12, 14), (6, 14)], GUNMETAL), i.rect(5, 2, 10, 4, BRASS), i.line([(8, 6), (9, 12)], GUNMETAL[3])),
        "heavy_bolt_belt": lambda: ([i.rect(1 + k * 3, 4, 3 + k * 3, 11, BRASS) for k in range(5)], i.rect(1, 7, 14, 8, BLACK, flat=True), [i.poly([(1 + k * 3, 4), (2 + k * 3, 2), (3 + k * 3, 4)], GUNMETAL) for k in range(5)]),
        "promethium_canister": lambda: (i.rect(4, 4, 12, 14, RED), i.rect(6, 2, 10, 4, BRASS), i.rect(6, 7, 10, 11, PROMETH)),
        "carapace_armour": lambda: (i.poly([(3, 3), (6, 2), (8, 4), (10, 2), (13, 3), (12, 12), (8, 14), (4, 12)], ramp((104, 110, 70))), i.line([(8, 4), (8, 14)], OLIVE[0]), i.rect(6, 6, 10, 8, BRASS)),
        "bolter_guard": lambda: gun(i, BOLTER, GUN_PAL),
        "bolter_astartes": lambda: (gun(i, BOLTER, {**GUN_PAL, "G": BLACK[1], "w": BLACK[2], "g": BLACK[0], "B": BRASS[2], "b": BRASS[1]})),
        "bolt_pistol": lambda: gun(i, PISTOL, GUN_PAL),
        "storm_bolter": lambda: gun(i, STORM, GUN_PAL),
        "flamer": lambda: gun(i, FLAMER, GUN_PAL),
        "plasma_gun": lambda: gun(i, PLASMA_G, GUN_PAL),
        "promethium_seep": lambda: (i.poly([(2, 10), (6, 7), (11, 7), (14, 10), (11, 13), (5, 13)], PROMETH), i.line([(5, 9), (9, 9)], PROMETH[3]), i.dot(10, 11, PROMETH[3])),
    }
    if name not in M:
        return None
    M[name]()
    return i.img if name.startswith(("bolter_", "bolt_pistol", "storm_", "flamer", "plasma_gun")) else i.done()


def main():
    made = {}
    names = ["steel_ingot", "pig_iron", "steel_plate", "ceramite_plate", "armaplas", "steel_rod", "steel_tube", "plasteel_tube", "steel_wire",
             "copper_wire", "crushed_iron", "crushed_copper", "crushed_lead", "washed_iron", "washed_copper", "raw_sulfur", "saltpeter", "slag",
             "coke", "gypsum", "rockrete", "ferrocrete", "sulfur", "sawdust", "zinc_dust", "fyceline", "bolt_propellant", "nitrocellulose", "cellulose",
             "polymer_resin", "fabric", "parchment", "herbs", "incense", "synthetic_crystal", "radium_cell", "motive_coil", "containment_coil",
             "cogitator_board", "logic_engine", "servo_2", "mr_fuse", "suspensor", "field_generator", "fibre_bundle", "neural_interface", "auto_senses",
             "power_pack", "ammo_feed", "chain_teeth", "drill_head", "rifled_barrel", "heavy_barrel", "bolter_receiver", "bolt_casing", "bolt_round",
             "bolt_magazine", "heavy_bolt_belt", "promethium_canister", "carapace_armour", "bolter_guard", "bolter_astartes", "bolt_pistol",
             "storm_bolter", "flamer", "plasma_gun", "promethium_seep"]
    for n in names:
        img = draw(n)
        assert img is not None, n
        img.save(os.path.join(TEX, n + ".png"))
        made[n] = img
    print("значков:", len(made))
    if "--sheet" in sys.argv:
        path = sys.argv[sys.argv.index("--sheet") + 1]
        cols = 12
        rows = (len(names) + cols - 1) // cols
        sheet = Image.new("RGBA", (cols * 68, rows * 68), (62, 62, 68, 255))
        for k, n in enumerate(names):
            big = made[n].resize((64, 64), Image.NEAREST)
            sheet.paste(big, ((k % cols) * 68 + 2, (k // cols) * 68 + 2), big)
        sheet.save(path)


if __name__ == "__main__":
    main()
