#!/usr/bin/env python3
"""Сценарий player_motion: игрок в модели Астартес (/wb gene astartes), камера третьего лица спереди.
Покой, ходьба, бег, присед, прыжок, удары в воздух, копание блока. Пишет tools/autotest/player_motion.txt.
Позже сюда же: лестница, плавание, ползание, езда, сон, предметы."""
import os

OX, Y = 29000, 280

s = f"""# Игрок-Астартес
cmd time set noon
cmd weather clear
cmd gamerule doDaylightCycle false
cmd gamerule doMobSpawning false
cmd gamemode survival
cmd effect give @s minecraft:resistance infinite 10 true
cmd effect give @s minecraft:saturation infinite 10 true
cmd tp @s {OX} {Y + 2} 0 0 30
wait 60
cmd fill {OX - 30} {Y - 1} -30 {OX + 30} {Y - 1} 60 minecraft:polished_deepslate
wait 320
cmd fill {OX - 12} {Y} -12 {OX + 12} {Y + 8} 30 minecraft:air
wait 20
cmd kill @e[type=!minecraft:player]
cmd wb gene astartes
hud off
cmd tp @s {OX} {Y} 0 180 0
wait 20
camera front
wait 10
shot idle0
wait 30
shot idle1
"""


def frames(tag, n, step=1):
    out = ""
    for i in range(n):
        out += f"wait {step}\nshot {tag}{i}\n"
    return out


# ходьба на камеру: игрок смотрит на юг (-Z — вперёд по взгляду yaw 180 = север). Камера спереди едет за игроком
s += "key forward on\nwait 20\n" + frames("walk", 12)
s += "key sprint on\nwait 20\n" + frames("run", 12)
s += "key sprint off\nkey forward off\nwait 20\n"
s += f"cmd tp @s {OX} {Y} 0 180 0\nwait 10\n"
s += "key shift on\nwait 15\nshot sneak_idle\nkey forward on\nwait 15\n" + frames("sneak", 14)
s += "key forward off\nkey shift off\nwait 20\n"
s += f"cmd tp @s {OX} {Y} 0 180 0\nwait 10\n"
# прыжок на месте
s += "key jump on\nwait 1\nkey jump off\n" + frames("jump", 14)
s += "wait 20\n"
# прыжок с разбега и падение с четырёх блоков
s += f"cmd tp @s {OX} {Y} 0 180 0\nwait 10\nkey forward on\nkey sprint on\nwait 25\nkey jump on\nwait 1\nkey jump off\n" + frames("runjump", 14) + "key forward off\nkey sprint off\nwait 20\n"
s += f"cmd tp @s {OX} {Y + 4} 0 180 0\n" + frames("drop", 18) + "wait 20\n"
s += f"cmd tp @s {OX} {Y} 0 180 0\nwait 10\n"
# удары в воздух: три одиночных
for k in range(3):
    s += "click attack\n" + frames(f"punch{k}_", 8) + "wait 6\n"
# копание: камень перед игроком на уровне груди, держим атаку
s += f"cmd setblock {OX} {Y + 1} -2 minecraft:stone\ncmd tp @s {OX} {Y} 0 180 25\nwait 10\nkey attack on\n" + frames("mine", 24) + "key attack off\nwait 10\n"
s += "cmd wb gene human\nquit\n"
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "player_motion.txt"), "w", encoding="utf-8") as f:
    f.write(s)
