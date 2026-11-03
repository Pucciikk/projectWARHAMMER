#!/usr/bin/env python3
"""Сценарий gui: окна машин разной раскладки, лесопилка с настоящими деревьями, трещина прометия. Пишет tools/autotest/gui.txt."""
import os

OX = 14000
MACHINES = ["ore_crusher", "ammo_line", "distiller", "wash_vat", "coal_gen", "promethium_gen", "chem_reactor", "rolling_mill", "lumber"]
s = f"""# Окна машин: сырьё кладём командой, чтобы было видно работу, статус и баки
cmd time set noon
cmd weather clear
cmd gamemode creative
cmd kill @e[type=item]
cmd tp @s {OX} 215 -10 0 30
wait 60
cmd fill {OX - 60} 199 -16 {OX + 60} 199 30 minecraft:polished_deepslate
hud off
wait 200
"""
for i, name in enumerate(MACHINES):
    x = OX - 50 + i * 12
    s += f"cmd setblock {x} 200 0 warpbound:{name}[facing=north]\ncmd tp @s {x} 200 -2 0 0\nwait 8\ncmd wb machine build\nwait 8\n"
s += "clearchat\ncmd kill @e[type=item]\n"
for i, name in enumerate(MACHINES):
    x = OX - 50 + i * 12
    s += f"cmd tp @s {x} 201 -3 0 0\nwait 10\nuseblock {x} 200 0\nwait 10\nshot gui_{name}\nclose\nwait 4\n"
# работающая машина: подаём сырьё и энергию прямо в окно нельзя, проверяем генератор на угле: статус, огонь, шкала
cgx = OX - 50 + 4 * 12
s += f"cmd item replace block {cgx} 200 0 container.0 with minecraft:coal 16\nwait 30\ncmd tp @s {cgx} 201 -3 0 0\nwait 6\nuseblock {cgx} 200 0\nwait 30\nshot gui_coal_gen_running\nclose\nwait 4\n"
lx = OX - 50 + 8 * 12
s += f"cmd tp @s {lx - 3.5} 203.5 -6.5 -20 12\nwait 25\nshot lumber_trees\n"
s += f"cmd tp @s {lx + 8} 205 8 90 20\nwait 25\nshot lumber_side\n"
s += "cmd tp @s 110000 150 110000 0 60\nwait 80\ncmd wb deposit tp\nwait 200\ncmd wb deposit tp\nwait 200\nclearchat\nshot fissure\nquit\n"
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui.txt"), "w", encoding="utf-8") as f:
    f.write(s)
