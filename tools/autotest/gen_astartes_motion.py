#!/usr/bin/env python3
"""Сценарий astartes_motion: движения Астартес крупно. Аллюры на месте (NoAI + Clip) сбоку и спереди, по кадру на тик;
потом живой Астартес гонится за зомби, бьёт его и вздрагивает от попаданий. Пишет tools/autotest/astartes_motion.txt."""
import os

OX, Y = 28000, 280
A = "warpbound:astartes"
CLEAR = "cmd kill @e[type=!minecraft:player]\nwait 110\n"

s = f"""# Движения Астартес
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
# ---- аллюры на месте: клип крутится, тело стоит. Камеры: сбоку и спереди под углом
for clip, ticks in (("move.walk", 11), ("move.run", 12), ("move.stroll", 16), ("move.sneak", 18), ("misc.idle", 0)):
    tag = clip.split(".")[1]
    s += f'cmd summon {A} {OX + 0.5} {Y} 0.5 {{NoAI:1b,Rotation:[0f,0f],Clip:"{clip}"}}\nwait 20\n'
    s += f"cmd tp @s {OX + 5.3} {Y + 0.4} 0.5 90 4\nwait 6\n"
    if ticks:
        for i in range(ticks):
            s += f"wait 1\nshot {tag}_side{i}\n"
        s += f"cmd tp @s {OX + 3.6} {Y + 0.6} 4.3 140 6\nwait 6\n"
        for i in range(ticks):
            s += f"wait 1\nshot {tag}_front{i}\n"
    else:
        s += f"shot {tag}_side\ncmd tp @s {OX + 3.6} {Y + 0.6} 4.3 140 6\nwait 6\nshot {tag}_front\n"
    s += CLEAR
# ---- погоня: зомби стоит в 14 блоках, Астартес получает от него удар и бежит отвечать; камера сбоку от трассы
s += f"cmd summon minecraft:zombie {OX + 0.5} {Y} -9 {{NoAI:1b,Rotation:[180f,0f],Health:900f,attributes:[{{id:\"minecraft:generic.max_health\",base:900}}]}}\n"
s += f"cmd summon {A} {OX + 0.5} {Y} 6 {{Rotation:[180f,0f]}}\nwait 20\n"
s += f"cmd tp @s {OX + 9} {Y + 2.5} -1 90 12\nwait 6\n"
s += f"cmd damage @e[type={A},limit=1] 1 minecraft:mob_attack by @e[type=minecraft:zombie,limit=1]\n"
for i in range(36):
    s += f"wait 2\nshot chase{i}\n"
# ---- удары вблизи, и вздрагивание посреди удара
s += f"cmd tp @s {OX + 4.5} {Y + 0.8} -8 70 4\nwait 4\n"
for i in range(40):
    if i in (12, 27):
        s += f"cmd damage @e[type={A},limit=1] 1 minecraft:generic\n"
    s += f"wait 1\nshot punch{i}\n"
s += CLEAR + "quit\n"
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "astartes_motion.txt"), "w", encoding="utf-8") as f:
    f.write(s)
