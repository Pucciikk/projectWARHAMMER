#!/usr/bin/env python3
"""Сценарий tw: Громовой воин нового образца рядом с Астартес. Покой с трёх сторон, лицо крупно днём и ночью (свечение очков),
ходьба и бег по кадрам, игрок в форме Громового воина (третье и первое лицо). Пишет tools/autotest/tw.txt."""
import os

OX, Y = 29300, 280
A, T = "warpbound:astartes", "warpbound:thunder_warrior"
XA, XT = OX - 0.7, OX + 1.7


def clip(name):
    return '{NoAI:1b,Rotation:[0f,0f],Clip:"' + name + '"}'


s = f"""# Громовой воин
cmd time set noon
cmd weather clear
cmd gamerule doDaylightCycle false
cmd gamerule doMobSpawning false
cmd gamemode creative
cmd tp @s {OX} {Y + 2} 0 0 30
wait 60
cmd fill {OX - 30} {Y - 1} -30 {OX + 30} {Y - 1} 30 minecraft:polished_deepslate
wait 300
cmd fill {OX - 30} {Y} -20 {OX + 30} {Y + 12} 20 minecraft:air
wait 20
hud off
camera first
cmd kill @e[type=!minecraft:player]
wait 10
cmd summon {A} {XA} {Y} 0 {clip("misc.idle")}
cmd summon {T} {XT} {Y} 0 {clip("misc.idle")}
wait 60
cmd tp @s {OX + 0.5} {Y + 0.9} 5.2 180 2
wait 10
shot pair_front
cmd tp @s {OX + 5} {Y + 1.2} 3.5 125 6
wait 10
shot pair_quarter
cmd tp @s {OX + 0.5} {Y + 1} -5 0 2
wait 10
shot pair_back
cmd tp @s {XT} {Y + 1.4} 1.6 180 -2
wait 10
shot tw_face
cmd time set 18000
wait 10
shot tw_face_night
cmd time set noon
cmd kill @e[type=!minecraft:player]
wait 10
"""
for name, n, step in (("move.walk", 10, 1), ("move.run", 11, 1)):
    tag = name.split(".")[1]
    s += f"cmd summon {T} {OX + 0.5} {Y} 0.5 {clip(name)}\nwait 20\ncmd tp @s {OX + 5.3} {Y + 0.4} 0.5 90 4\nwait 6\n"
    s += "".join(f"wait {step}\nshot tw_{tag}{i}\n" for i in range(n))
    s += "cmd kill @e[type=!minecraft:player]\nwait 10\n"
s += f"""cmd gamemode survival
cmd wb gene thunder_warrior
cmd tp @s {OX} {Y} 0 180 0
wait 20
camera front
wait 10
shot player_front
look 215 0
wait 6
shot player_quarter
camera first
hud on
clearchat
wait 10
shot player_fp
hud off
cmd wb gene human
quit
"""
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tw.txt"), "w", encoding="utf-8") as f:
    f.write(s)
