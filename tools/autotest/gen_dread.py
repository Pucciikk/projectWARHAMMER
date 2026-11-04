#!/usr/bin/env python3
"""Сценарий dread: дредноут-саркофаг. Покой, ходьба крупным планом, стрельба, удар, упор в узкий проход, смерть по кадрам. Площадка высоко в небе: там сразу правильный свет. Пишет tools/autotest/dread.txt."""
import os

OX = 26000
Y = 280
NAME = "warpbound:dread_castraferrum"
TARGET = '{NoAI:1b,Health:5000f,attributes:[{id:"minecraft:generic.max_health",base:5000}]}'
s = f"""# Дредноут
cmd time set noon
cmd weather clear
cmd gamerule doDaylightCycle false
cmd gamerule doMobSpawning false
cmd gamemode creative
cmd tp @s {OX} {Y + 2} 0 0 30
wait 60
cmd fill {OX - 30} {Y - 1} -30 {OX + 30} {Y - 1} 30 minecraft:polished_deepslate
wait 80
hud off
cmd kill @e[type=!minecraft:player]
wait 6
"""
# ---- без пилота: стоит неподвижно
s += f"wait 30\ncmd kill @e[type=!minecraft:player]\nwait 6\ncmd summon {NAME} {OX} {Y} -25 {{Rotation:[0f,0f]}}\ncmd tp @s {OX + 5} {Y} -20 135 -4\nwait 30\nshot empty0\nwait 60\nshot empty1\ncmd tp @s {OX + 7} {Y} -25 90 -3\nwait 4\nshot empty_side\n"
# ---- за рулём: вид из кабины и со стороны
s += "cmd item replace entity @s weapon.mainhand with minecraft:air\ncmd ride @s mount @e[type=warpbound:dread_castraferrum,limit=1,sort=nearest]\nwait 14\nlook 0 0\nhud on\nclearchat\nshot cab0\n"
s += "pos старт\nkey forward on\nwait 40\nshot cab_walk\npos шаг40\nwait 40\npos шаг80\nkey sprint on\nwait 30\npos бег0\nshot cab_run\nwait 40\npos бег40\nkey sprint off\nkey forward off\nwait 30\nshot cab_stop\n"
s += "look 30 0\nwait 20\nshot cab_turn\nlook 0 0\nwait 20\n"
s += "dread fire on\nwait 6\nshot cab_fire0\nwait 3\nshot cab_fire1\ndread fire off\nwait 16\ndread claw\nwait 8\nshot cab_claw0\nwait 4\nshot cab_claw1\nwait 20\n"
s += "camera back\nlook 0 12\nwait 10\nshot rd_idle\nkey back on\nwait 16\nshot rd_back\nkey back off\nwait 14\ndread fire on\nwait 6\nshot rd_fire\ndread fire off\nwait 10\ndread claw\nwait 10\nshot rd_claw\nwait 30\ncamera first\nkey shift on\nwait 4\nkey shift off\nwait 10\nhud off\n"
s += f"cmd kill @e[type=!minecraft:player]\nwait 6\n"
# ---- толчок: зомби перед машиной, снимаем со стороны
s += f"wait 240\ncmd summon {NAME} {OX} {Y} -15 {{Rotation:[0f,0f]}}\ncmd tp @s {OX + 3} {Y} -15\nwait 2\ncmd ride @s mount @e[type=warpbound:dread_castraferrum,limit=1,sort=nearest]\nwait 14\nlook 0 0\nhud on\n"
for dz in (-12, -11):
    for dx in (-1, 1):
        s += f"cmd summon minecraft:zombie {OX + dx} {Y} {dz} {{Health:900f,attributes:[{{id:\"minecraft:generic.max_health\",base:900}}]}}\n"
s += "wait 10\ncmd data get entity @e[type=minecraft:zombie,limit=1,sort=nearest] Pos\nshot shove_cab0\ndread shove\nwait 7\nshot shove_cab1\nwait 6\nshot shove_cab2\ncmd data get entity @e[type=minecraft:zombie,limit=1,sort=nearest] Pos\nwait 30\ncamera back\nlook 0 12\ndread shove\nwait 5\nshot shove_rd0\nwait 4\nshot shove_rd1\nwait 30\ncamera first\nkey shift on\nwait 4\nkey shift off\nwait 10\n"
s += f"cmd kill @e[type=!minecraft:player]\nwait 6\n"
# ---- пустые баки: кабина с предупреждением, машина заглохла
s += f"wait 240\ncmd summon {NAME} {OX} {Y} -15 {{Rotation:[0f,0f],Fuel:0,Ammo:0}}\ncmd tp @s {OX + 3} {Y} -15\nwait 2\ncmd ride @s mount @e[type=warpbound:dread_castraferrum,limit=1,sort=nearest]\nwait 14\nlook 0 0\nshot cab_empty\nkey forward on\nwait 20\npos без_топлива\nkey forward off\nkey shift on\nwait 4\nkey shift off\nwait 10\nhud off\n"
s += f"cmd kill @e[type=!minecraft:player]\nwait 6\n"
# ---- смерть: сажаем пилота, убиваем и снимаем всё падение
s += f"cmd tp @s {OX + 6} {Y} 5 130 -4\ncmd summon {NAME} {OX} {Y} 0 {{Rotation:[0f,0f]}}\nwait 30\nshot death_before\ncmd kill @e[type={NAME},distance=..30]\n"
for i in range(14):
    s += f"wait 8\nshot death{i}\n"
s += "wait 100\nshot death_end\nwait 120\nshot death_gone\n"
s += f"cmd kill @e[type=!minecraft:player]\nwait 6\n"
# ---- цепной меч рядом с обычным мечом, от первого лица и со стороны
s += "hud on\ncmd gamemode creative\nclearchat\ncmd item replace entity @s weapon.mainhand with minecraft:iron_sword\nwait 16\nshot vanilla_first\ncmd item replace entity @s weapon.mainhand with warpbound:chainsword\nwait 16\nshot sword_first\ngun swing\nwait 4\nshot sword_swing\nwait 20\ncamera back\nwait 8\nshot sword_back\ncamera first\nquit\n"
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dread.txt"), "w", encoding="utf-8") as f:
    f.write(s)
