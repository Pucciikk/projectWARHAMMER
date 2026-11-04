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
    # снаряд в полёте: первые кадры после выстрела, от бедра и из прицела
    t += "".join(f"gun fire 1\nwait {w}\nshot {tag}_fly{w}\nwait 24\n" for w in (1, 2, 3, 5))
    t += "gun aim on\nwait 18\n" + "".join(f"gun fire 1\nwait {w}\nshot {tag}_afly{w}\nwait 24\n" for w in (1, 3)) + "gun aim off\nwait 14\n"
    t += "gun reload\n"
    for i, gap in enumerate(frames_reload):
        t += f"wait {gap}\nshot {tag}_r{i}\n"
    t += "wait 30\n"
    t += f"camera back\ncmd tp @s {OX} 200 0 0 0\nwait 14\nshot {tag}_third\ngun fire 1\nwait 1\nshot {tag}_third_f1\nwait 2\nshot {tag}_third_f2\nwait 20\ncamera front\nwait 8\nshot {tag}_front\ncmd tp @s {OX} 200 0 90 0\nwait 4\ngun fire 1\nwait 1\nshot {tag}_side_f1\nwait 2\nshot {tag}_side_f2\nwait 20\ncamera first\ncmd tp @s {OX} 200 0 0 0\nwait 6\n"
    return t


s += gun("lasgun", "las", [5, 5, 4, 5, 5, 6, 5, 5, 5, 3])
s += gun("bolter_guard", "bolt", [6, 6, 4, 6, 6, 6, 6, 5, 6, 4])
# как оружие лежит в руке со стороны: зомби на расстоянии вытянутой руки, смотрят поперёк взгляда
for i, it in enumerate(("lasgun", "bolter_guard", "chainsword")):
    s += f"cmd summon minecraft:zombie {OX - 2.2 + i * 2.2} 200 4 {{NoAI:1b,Rotation:[90f,0f],HandItems:[{{id:\"warpbound:{it}\",count:1}},{{}}]}}\n"
s += "cmd item replace entity @s weapon.mainhand with minecraft:air\nwait 10\nshot held_side\n"
s += "cmd kill @e[type=minecraft:zombie,distance=..8]\nwait 4\n"
# цепной меч: покой, обороты, все три удара по кадрам, вид со стороны
s += "cmd item replace entity @s weapon.mainhand with warpbound:chainsword\nwait 30\nshot sword_idle\ngun rev on\nwait 12\nshot sword_rev\n"
for i in range(3):
    s += "gun swing\n" + "".join(f"wait 2\nshot sword_s{i}_{k}\n" for k in range(6)) + "wait 20\n"
s += f"gun rev off\ncamera front\nwait 8\nshot sword_front\ncmd tp @s {OX} 200 0 90 0\nwait 6\nshot sword_side\ncamera first\ncmd tp @s {OX} 200 0 0 0\nwait 6\n"
s += "cmd item replace entity @s hotbar.1 with warpbound:chainsword\ncmd item replace entity @s hotbar.2 with warpbound:bolter_guard\n"
s += "cmd item replace entity @s weapon.mainhand with warpbound:lasgun[warpbound:gun_ammo=12]\nwait 4\npress inventory\nwait 10\nshot inventory\nclose\nwait 4\nquit\n"
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "guns.txt"), "w", encoding="utf-8") as f:
    f.write(s)

# ---- снаряд в полёте: время замедлено в 10 раз, снимки между тиками. Сценарий gunfly
f = f"""cmd time set noon
cmd weather clear
cmd gamemode creative
cmd tp @s {OX} 215 0 0 0
wait 60
cmd fill {OX - 30} 199 -10 {OX + 30} 199 60 minecraft:polished_deepslate
cmd fill {OX - 30} 200 -10 {OX + 30} 215 60 minecraft:air
wait 120
cmd tp @s {OX} 200 0 0 0
clearchat
"""


def fly(item, tag):
    t = f"cmd item replace entity @s weapon.mainhand with warpbound:{item}[warpbound:gun_ammo=30]\nwait 30\ncmd tick rate 2\nwait 2\nclearchat\n"
    for mode, pre in (("hip", ""), ("aim", "gun aim on\nwait 12\n"), ("third", "gun aim off\ncamera back\nwait 6\n")):
        t += pre + f"gun fire 1\ndelayshot 25 {tag}_{mode}0\ndelayshot 70 {tag}_{mode}1\ndelayshot 130 {tag}_{mode}2\ndelayshot 230 {tag}_{mode}3\nwait 10\n"
    t += "camera first\ncmd tick rate 20\nwait 10\n"
    return t


f += fly("lasgun", "las") + fly("bolter_guard", "bolt")
f += "cmd item replace entity @s weapon.mainhand with warpbound:chainsword\nwait 30\ngun rev on\nwait 10\nclearchat\n"
for i in range(3):
    f += "gun swing\n" + "".join(f"wait 2\nshot sword_s{i}_{k}\n" for k in range(6)) + "wait 20\n"
f += "quit\n"
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gunfly.txt"), "w", encoding="utf-8") as out:
    out.write(f)
