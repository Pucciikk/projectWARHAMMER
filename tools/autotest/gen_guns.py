#!/usr/bin/env python3
"""Сценарий guns: лазган и болтер от первого лица: бедро, прицел, выстрелы, перезарядка по кадрам, снаряд в полёте, вид со стороны. Пишет tools/autotest/guns.txt."""
import os

OX = 20000
s = f"""# Оружие. Площадка своя, мишени — стойки для брони
cmd time set noon
cmd weather clear
cmd gamerule doDaylightCycle false
cmd gamemode creative
cmd tp @s {OX} 215 0 0 30
wait 60
cmd fill {OX - 30} 199 -10 {OX + 30} 199 60 minecraft:polished_deepslate
cmd fill {OX - 30} 200 -10 {OX + 30} 215 60 minecraft:air
cmd fill {OX - 8} 200 40 {OX + 8} 210 41 minecraft:stone_bricks
cmd summon minecraft:zombie {OX - 2} 200 18 {{NoAI:1b,Health:200f,Attributes:[{{id:"max_health",base:200}}]}}
cmd summon minecraft:zombie {OX + 3} 200 22 {{NoAI:1b,Health:200f,Attributes:[{{id:"max_health",base:200}}]}}
wait 200
cmd tp @s {OX} 200 0 0 0
cmd clear @s
"""


def gun(item, tag, frames_reload):
    t = f"cmd item replace entity @s weapon.mainhand with warpbound:{item}[warpbound:gun_ammo=30]\nwait 30\nclearchat\nshot {tag}_hip\n"
    # выстрел: вспышку держим для снимка
    t += f"gun flash on\ngun fire 1\nwait 2\nshot {tag}_fire0\ngun flash off\nwait 2\nshot {tag}_fire1\nwait 18\n"
    t += f"gun aim on\nwait 18\nshot {tag}_aim\ngun flash on\ngun fire 1\nwait 2\nshot {tag}_aimfire\ngun flash off\nwait 12\ngun aim off\nwait 14\nshot {tag}_hud\n"
    # очередь: подъём ствола и снаряды
    t += f"gun fire 8\nwait 6\nshot {tag}_burst0\nwait 8\nshot {tag}_burst1\nwait 40\n"
    t += "gun reload\n"
    for i, gap in enumerate(frames_reload):
        t += f"wait {gap}\nshot {tag}_r{i}\n"
    t += "wait 30\n"
    t += f"camera back\ncmd tp @s {OX} 200 0 0 0\nwait 14\nshot {tag}_third\ngun fire 2\nwait 3\nshot {tag}_third_fire\nwait 10\ncamera first\nwait 6\n"
    return t


s += gun("lasgun", "las", [5, 5, 4, 5, 5, 6, 5, 5, 5, 3])
s += gun("bolter_guard", "bolt", [6, 6, 4, 6, 6, 6, 6, 5, 6, 4])
s += "cmd item replace entity @s weapon.mainhand with warpbound:lasgun[warpbound:gun_ammo=12]\nwait 4\npress inventory\nwait 10\nshot inventory\nclose\nwait 4\nquit\n"
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "guns.txt"), "w", encoding="utf-8") as f:
    f.write(s)
