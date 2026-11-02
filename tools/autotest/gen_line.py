#!/usr/bin/env python3
"""Сценарий line: рабочая линия. Уголь → генератор → кабель → дробильня → пневмопровод → сундук; водозабор → труба → чан. Пишет tools/autotest/line.txt."""
import os

G, Z, Y = 8000, -10, 200
C, W = G + 6, G + 15
V = W + 6
s = f"""# Рабочая линия: проверка в игре. Сундуки: руда, уголь, гравий; результат смотрим командой data get (ответ идёт в журнал)
cmd time set noon
cmd weather clear
cmd gamemode creative
cmd tp @s {G + 10} {Y + 8} {Z - 8} 0 30
wait 80
cmd fill {G - 6} {Y - 1} {Z - 8} {V + 8} {Y - 1} {Z + 8} minecraft:polished_deepslate
hud off
wait 200
"""


def machine(block, x):
    return f"cmd setblock {x} {Y} {Z} warpbound:{block}[facing=north]\ncmd tp @s {x} {Y} {Z - 2} 0 0\nwait 8\ncmd wb machine build\nwait 8\n"


def feeder(x, item, count):
    """Воронка смотрит на восток в порт, над ней сундук с материалом."""
    return (f"cmd setblock {x} {Y} {Z + 1} minecraft:hopper[facing=east]\ncmd setblock {x} {Y + 1} {Z + 1} minecraft:chest\n"
            f"cmd item replace block {x} {Y + 1} {Z + 1} container.0 with minecraft:{item} {count}\n")


s += machine("coal_gen", G) + machine("ore_crusher", C) + machine("water_intake", W) + machine("wash_vat", V)
s += f"cmd tp @s {G + 10} {Y + 3} {Z - 6} 0 10\nwait 4\n"
# кабель по задней стороне: генератор, дробильня, водозабор, обходом к чану
s += f"cmd fill {G} {Y} {Z + 3} {W} {Y} {Z + 3} warpbound:energy_cable\n"
s += f"cmd fill {W} {Y} {Z + 4} {V} {Y} {Z + 4} warpbound:energy_cable\ncmd setblock {V} {Y} {Z + 3} warpbound:energy_cable\n"
s += f"cmd fill {W + 1} {Y} {Z + 3} {V - 1} {Y} {Z + 3} warpbound:fluid_pipe\n"
s += feeder(G - 2, "coal", 16) + feeder(C - 2, "raw_iron", 16) + feeder(V - 2, "gravel", 32)
# выход дробильни: пневмопровод в сундук; выход чана: сундук вплотную к порту
s += f"cmd fill {C + 2} {Y} {Z + 1} {C + 3} {Y} {Z + 1} warpbound:item_tube\ncmd setblock {C + 4} {Y} {Z + 1} minecraft:chest\n"
s += f"cmd setblock {V + 2} {Y} {Z + 1} minecraft:chest\n"
s += "clearchat\nwait 300\n"
s += f"shot 01_line\ncmd tp @s {G + 8} {Y + 5} {Z + 11} 180 25\nwait 20\nshot 02_back\n"
s += f"cmd data get block {C + 4} {Y} {Z + 1} Items\nwait 2\ncmd data get block {V + 2} {Y} {Z + 1} Items\nwait 2\n"
s += f"cmd tp @s {C} {Y + 1} {Z - 3} 0 0\nwait 10\nuseblock {C} {Y} {Z}\nwait 10\nshot 03_crusher_gui\nclose\nwait 4\n"
s += f"cmd tp @s {V} {Y + 1} {Z - 3} 0 0\nwait 10\nuseblock {V} {Y} {Z}\nwait 10\nshot 04_vat_gui\nclose\nwait 4\n"
s += f"cmd tp @s {G} {Y + 1} {Z - 3} 0 0\nwait 10\nuseblock {G} {Y} {Z}\nwait 10\nshot 05_gen_gui\nclose\nwait 4\n"
s += "quit\n"
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "line.txt"), "w", encoding="utf-8") as f:
    f.write(s)
