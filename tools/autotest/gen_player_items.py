#!/usr/bin/env python3
"""Сценарий player_items: игрок-Астартес с предметами. Первое лицо (перчатка пустой руки, взмах), третье лицо спереди и вполоборота
с мечом, киркой, луком, щитом в левой руке. Пишет tools/autotest/player_items.txt."""
import os

OX, Y = 29000, 280

s = f"""# Игрок-Астартес: предметы и первое лицо
cmd time set noon
cmd weather clear
cmd gamerule doDaylightCycle false
cmd gamemode survival
cmd effect give @s minecraft:resistance infinite 10 true
cmd tp @s {OX} {Y + 2} 0 0 30
wait 60
cmd fill {OX - 30} {Y - 1} -30 {OX + 30} {Y - 1} 60 minecraft:polished_deepslate
wait 320
cmd fill {OX - 12} {Y} -12 {OX + 12} {Y + 8} 30 minecraft:air
wait 20
cmd kill @e[type=!minecraft:player]
cmd clear @s
cmd wb gene astartes
cmd tp @s {OX} {Y} 0 180 10
wait 20
hud on
camera first
wait 10
shot fp_empty
click attack
"""
for i in range(6):
    s += f"wait 1\nshot fp_swing{i}\n"
s += "wait 10\ncmd item replace entity @s weapon.mainhand with minecraft:diamond_sword\nwait 10\nshot fp_sword\n"
s += "cmd item replace entity @s weapon.mainhand with minecraft:air\ncmd item replace entity @s weapon.offhand with minecraft:torch\nwait 10\nshot fp_offhand\n"
s += "hud off\ncamera front\n"
for item, off in (("diamond_sword", "air"), ("iron_pickaxe", "air"), ("bow", "air"), ("iron_axe", "shield"), ("air", "torch")):
    s += f"cmd item replace entity @s weapon.mainhand with minecraft:{item}\ncmd item replace entity @s weapon.offhand with minecraft:{off}\n"
    s += f"cmd tp @s {OX} {Y} 0 180 0\nwait 12\nshot tp_{item}_front\nlook 220 0\nwait 6\nshot tp_{item}_q1\nlook 140 0\nwait 6\nshot tp_{item}_q2\n"
s += "cmd clear @s\ncmd wb gene human\nquit\n"
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "player_items.txt"), "w", encoding="utf-8") as f:
    f.write(s)
