#!/usr/bin/env python3
"""Сценарий factory: все машины цепочки на одной площадке, замер FPS, цикл автоклава и генераториума. Пишет tools/autotest/factory.txt."""
import os

OX = 7000
ROW1 = ["ore_crusher", "wash_vat", "coke_oven", "blast_furnace", "converter", "rolling_mill", "electrolyzer", "water_intake", "coal_gen"]
ROW2 = ["scriptorium", "armoury", "barrel_shop", "ammo_line", "weavery", "distiller", "desulfurizer", "autoclave", "promethium_extractor"]
STEP = 10
pos = {}
s = f"""# Все машины цепочки: общий вид и FPS. Площадка новая, сверху пусто, поэтому очищать воздух не нужно (лимит fill 32768)
cmd time set noon
cmd weather clear
cmd gamemode creative
cmd wb deposit everywhere
cmd tp @s {OX} 215 -30 0 30
wait 60
cmd fill {OX - 50} 199 -40 {OX + 50} 199 45 minecraft:polished_deepslate
hud off
wait 300
"""
for z, row in ((-12, ROW1), (10, ROW2)):
    for i, name in enumerate(row):
        x = OX - 40 + i * STEP
        pos[name] = (x, z)
        s += f"cmd setblock {x} 200 {z} warpbound:{name}[facing=north]\ncmd tp @s {x} 200 {z - 2} 0 0\nwait 8\ncmd wb machine build\nwait 8\n"
s += f"clearchat\ncmd tp @s {OX} 218 -34 0 24\nwait 120\nshot all\nfps все 18 машин в кадре\n"
s += f"cmd tp @s {OX} 212 60 180 20\nwait 100\nfps все машины в кадре с другой стороны\ncmd tp @s {OX} 280 -34 180 -50\nwait 100\nfps машины за спиной\n"
ax, az = pos["autoclave"]
s += f"cmd tp @s {ax - 2} 203 {az - 5.5} -15 15\nwait 10\n"
for i in range(8):
    s += f"shot au_{i}\nwait 20\n"
gx, gz = pos["coal_gen"]
s += f"cmd tp @s {gx + 3.5} 202.6 {gz - 3.5} 40 12\nwait 10\n"
for i in range(4):
    s += f"shot cg_{i}\nwait 10\n"
wx, wz = pos["water_intake"]
s += f"cmd tp @s {wx - 3} 203 {wz - 3.5} -35 18\nwait 10\n"
for i in range(2):
    s += f"shot wi_{i}\nwait 10\n"
ex, ez = pos["promethium_extractor"]
s += f"cmd tp @s {ex + 10} 206 {ez + 6} 90 5\nwait 20\nshot ex_0\nwait 20\nshot ex_1\n"
s += "quit\n"
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "factory.txt"), "w", encoding="utf-8") as f:
    f.write(s)
