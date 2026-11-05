#!/usr/bin/env python3
"""Сценарий astartes: Астартес и Громовой воин в игре. Покой с четырёх сторон, рядом с ориентиром ростом с игрока, ходьба и бег по кадрам, удар, смерть. Пишет tools/autotest/astartes.txt."""
import os

OX = 28000
Y = 280
A, T = "warpbound:astartes", "warpbound:thunder_warrior"
XA, XT = OX - 0.8, OX + 1.8      # игрок телепортируется в середину блока, поэтому пара стоит вокруг OX + 0.5
CLEAR = "cmd kill @e[type=!minecraft:player]\nwait 110\n"    # тело лежит 100 тиков


def clip(name):
    return '{NoAI:1b,Rotation:[0f,0f],Clip:"' + name + '"}'


def pair(name):
    return f"cmd summon {A} {XA} {Y} 0 {clip(name)}\ncmd summon {T} {XT} {Y} 0 {clip(name)}\n"


s = f"""# Астартес и Громовой воин
cmd time set noon
cmd weather clear
cmd gamerule doDaylightCycle false
cmd gamerule doMobSpawning false
cmd gamemode creative
cmd tp @s {OX} {Y + 2} 0 0 30
wait 60
cmd fill {OX - 30} {Y - 1} -30 {OX + 30} {Y - 1} 30 minecraft:polished_deepslate
wait 320
hud off
camera first
cmd kill @e[type=!minecraft:player]
wait 110
"""
s += pair("misc.idle")
s += f"cmd summon minecraft:armor_stand {OX + 4} {Y} 0 {{NoGravity:1b,ShowArms:1b,Rotation:[0f,0f]}}\nwait 30\n"
s += f"cmd tp @s {OX} {Y + 1} 5 180 0\nwait 12\nshot pair_front\n"
s += f"cmd tp @s {OX + 6} {Y + 1} 0 90 0\nwait 12\nshot pair_side\n"
s += f"cmd tp @s {OX} {Y + 1} -5 0 0\nwait 12\nshot pair_back\n"
s += f"cmd tp @s {OX - 3.5} {Y + 1.4} 3 225 0\nwait 12\nshot pair_quarter\n"
s += f"cmd tp @s {XA - 0.5} {Y + 0.2} 1.5 180 -8\nwait 12\nshot astartes_face\n"
s += f"cmd tp @s {XT - 0.1} {Y + 0.4} 1.1 180 -2\nwait 12\nshot warrior_face\n"
s += CLEAR
s += pair("misc.stasis")
s += f"wait 20\ncmd tp @s {OX} {Y + 1} 5 180 0\nwait 12\nshot stasis\n"
s += CLEAR
# ---- клипы: вид сбоку спереди
for name, frames, step in (("move.walk", 8, 2), ("move.run", 8, 1)):
    tag = name.split(".")[1]
    s += pair(name) + f"wait 14\ncmd tp @s {OX + 5} {Y + 1} 3 120 0\nwait 8\n"
    for i in range(frames):
        s += f"wait {step}\nshot {tag}{i}\n"
    s += CLEAR
# ---- живое поведение: бродит и смотрит на игрока; удар в ответ
s += f"cmd summon {A} {OX} {Y} 0 {{Rotation:[0f,0f]}}\ncmd tp @s {OX + 3} {Y + 1} 3 135 0\nwait 40\nshot live_look\n"
s += f"cmd summon minecraft:husk {OX} {Y} -1.4 {{NoAI:1b,Rotation:[180f,0f],Health:900f,attributes:[{{id:\"minecraft:generic.max_health\",base:900}}]}}\ncmd damage @e[type={A},limit=1] 1 minecraft:mob_attack by @e[type=minecraft:husk,limit=1]\nwait 10\n"
for i in range(6):
    s += f"wait 2\nshot melee{i}\n"
s += CLEAR
# ---- смерть
s += f"cmd summon {A} {XA} {Y} 0 {{NoAI:1b,Rotation:[0f,0f]}}\ncmd summon {T} {XT} {Y} 0 {{NoAI:1b,Rotation:[0f,0f]}}\nwait 16\ncmd tp @s {OX + 5} {Y + 1} 3 120 0\nwait 8\ncmd kill @e[type={A}]\ncmd kill @e[type={T}]\n"
for i in range(7):
    s += f"wait 8\nshot death{i}\n"
s += "wait 30\nshot death_end\nquit\n"
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "astartes.txt"), "w", encoding="utf-8") as f:
    f.write(s)
