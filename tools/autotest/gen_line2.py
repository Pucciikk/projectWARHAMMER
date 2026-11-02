#!/usr/bin/env python3
"""
Сценарий line2: прометий и конвейер. Экстрактор → труба → колонна → бак и горелка; уголь → генератор → кабель к колонне и дробильне;
руда → воронка → конвейер → дробильня → конвейер → сундук. Рядом новые машины для осмотра. Пишет tools/autotest/line2.txt.
Порты: выход экстрактора (x+3, z+12) на юг; у машины 3×3 вход жидкости (x-1, z+2), энергия (x, z+2), выход (x+1, z+2) — на юг;
предметы вход (x-1, z+1) на запад, выход (x+1, z+1) на восток.
"""
import os

OX, Z, Y = 14000, -10, 200
EX = OX
DX, DZ = OX + 8, Z + 10
GX, GZ = OX + 14, Z + 16
CX, CZ = OX + 24, Z + 16
ROW = Z + 26


def b(x, z, block, y=Y):
    return f"cmd setblock {x} {y} {z} {block}\n"


def fill(x0, z0, x1, z1, block):
    return f"cmd fill {x0} {Y} {z0} {x1} {Y} {z1} {block}\n"


def machine(block, x, z):
    return f"cmd setblock {x} {Y} {z} warpbound:{block}[facing=north]\ncmd tp @s {x} {Y} {z - 2} 0 0\nwait 8\ncmd wb machine build\nwait 8\n"


pipe = "warpbound:fluid_pipe"
cable = "warpbound:energy_cable"
s = f"""# Прометий и конвейер: проверка в игре
cmd time set noon
cmd weather clear
cmd gamemode creative
cmd tp @s {OX + 12} {Y + 10} {Z + 8} 0 40
wait 100
cmd fill {OX - 8} {Y - 1} {Z - 3} {OX + 36} {Y - 1} {Z + 40} minecraft:polished_deepslate
hud off
wait 240
"""
s += machine("promethium_extractor", EX, Z) + machine("distiller", DX, DZ) + machine("coal_gen", GX, GZ) + machine("ore_crusher", CX, CZ)
s += machine("forge_smelter", OX, ROW) + machine("cogitatorium", OX + 10, ROW) + machine("mechanicus_forge", OX + 20, ROW)
s += f"cmd tp @s {OX + 12} {Y + 6} {Z + 8} 0 25\nwait 6\n"
# прометий: порт экстрактора → вход колонны
s += fill(EX + 3, Z + 13, DX - 1, Z + 13, pipe)
# выход колонны: в бак и горелку
s += fill(DX + 1, DZ + 3, DX + 3, DZ + 3, pipe)
s += b(DX + 4, DZ + 3, "warpbound:fluid_tank") + b(DX + 2, DZ + 4, "warpbound:flare_stack")
# энергия: генератор → колонна и дробильня
s += fill(DX, DZ + 3, DX, GZ + 3, cable) + fill(DX, GZ + 3, CX, GZ + 3, cable) + b(CX, CZ + 3, cable)
s += b(GX - 2, GZ + 1, "minecraft:hopper[facing=east]") + b(GX - 2, GZ + 1, "minecraft:chest", Y + 1)
s += f"cmd item replace block {GX - 2} {Y + 1} {GZ + 1} container.0 with minecraft:coal 64\n"
# руда на конвейере
s += b(CX - 6, CZ + 1, "minecraft:hopper[facing=east]") + b(CX - 6, CZ + 1, "minecraft:chest", Y + 1)
s += f"cmd item replace block {CX - 6} {Y + 1} {CZ + 1} container.0 with minecraft:raw_iron 32\n"
s += fill(CX - 5, CZ + 1, CX - 2, CZ + 1, "warpbound:conveyor[facing=east]")
s += fill(CX + 2, CZ + 1, CX + 5, CZ + 1, "warpbound:conveyor[facing=east]") + b(CX + 6, CZ + 1, "minecraft:chest")
# люки снимаем сразу, пока лента полна; вход и выход по нескольку кадров
s += "clearchat\nwait 30\n"
s += f"cmd tp @s {CX - 4.2} {Y + 1.05} {CZ + 1.5} -90 14\nwait 12\n"
for i in range(4):
    s += f"shot h_in_{i}\nwait 7\n"
s += "wait 200\n"
s += f"cmd tp @s {CX + 4.2} {Y + 1.05} {CZ + 1.5} 90 14\nwait 12\n"
for i in range(8):
    s += f"shot h_out_{i}\nwait 12\n"
s += "wait 1500\nshot 01_all\n"
s += f"cmd tp @s {EX + 5} {Y + 1.1} {Z + 11.4} 0 25\nwait 10\nshot 09_pipe\nwait 6\nshot 10_pipe\n"
s += f"cmd tp @s {DX + 2.5} {Y + 1.4} {DZ + 1.6} 0 40\nwait 10\nshot 11_tee\n"
s += f"cmd tp @s {OX + 8} {Y + 4} {ROW - 7} 0 12\nwait 20\nshot 04_row\nwait 12\nshot 05_row\n"
s += f"cmd tp @s {OX + 22} {Y + 2.5} {ROW - 7} 0 8\nwait 20\nshot 06_forge\n"
s += f"cmd data get block {CX + 6} {Y} {CZ + 1} Items\nwait 2\ncmd data get block {DX + 4} {Y} {DZ + 3} amount\nwait 2\ncmd data get block {DX + 4} {Y} {DZ + 3} variant\nwait 2\n"
s += f"cmd tp @s {DX} {Y + 1} {DZ - 3} 0 0\nwait 10\nuseblock {DX} {Y} {DZ}\nwait 10\nshot 07_distiller_gui\nclose\nwait 4\n"
s += f"cmd tp @s {OX + 20} {Y + 1} {ROW - 3} 0 0\nwait 10\nuseblock {OX + 20} {Y} {ROW}\nwait 10\nshot 08_forge_gui\nclose\nwait 4\nquit\n"
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "line2.txt"), "w", encoding="utf-8") as f:
    f.write(s)
