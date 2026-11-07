#!/usr/bin/env python3
"""Сценарий player_actions: игрок-Астартес использует предметы и бьёт. Щит, лук, арбалет (зарядка и изготовка), трезубец, подзорная труба,
золотое яблоко, зелье, лазган, копание киркой, удары мечом. Камера третьего лица вполоборота. Пишет tools/autotest/player_actions.txt."""
import os

OX, Y = 29200, 280


def frames(tag, n, step=2):
    return "".join(f"wait {step}\nshot {tag}{i}\n" for i in range(n))


def give(main, off="air"):
    return f"cmd item replace entity @s weapon.mainhand with {main}\ncmd item replace entity @s weapon.offhand with minecraft:{off}\n"


s = f"""# Игрок-Астартес: действия
cmd time set noon
cmd weather clear
cmd gamerule doDaylightCycle false
cmd gamemode survival
cmd effect give @s minecraft:resistance infinite 10 true
cmd tp @s {OX} {Y + 2} 0 0 30
wait 60
cmd fill {OX - 30} {Y - 1} -30 {OX + 30} {Y - 1} 30 minecraft:polished_deepslate
wait 300
cmd fill {OX - 30} {Y} -20 {OX + 30} {Y + 12} 20 minecraft:air
wait 20
cmd kill @e[type=!minecraft:player]
cmd clear @s
cmd item replace entity @s hotbar.8 with minecraft:arrow 64
cmd wb gene astartes
hud off
cmd tp @s {OX} {Y} 0 180 0
wait 10
camera front
look 215 0
wait 10
"""
for tag, item, off, ticks in (("shield", "minecraft:shield", "air", 14), ("bow", "minecraft:bow", "air", 26), ("crossbow", "minecraft:crossbow", "air", 30),
                              ("trident", "minecraft:trident", "air", 14), ("spyglass", "minecraft:spyglass", "air", 10),
                              ("apple", "minecraft:golden_apple", "air", 20), ("potion", "minecraft:potion", "air", 20)):
    s += give(item, off) + "wait 6\nkey usekey on\n" + frames(tag, 5, max(1, ticks // 5)) + "key usekey off\nwait 10\n"
    if tag == "crossbow":
        s += frames("crossbow_hold", 2, 4)
s += give("warpbound:lasgun") + "wait 10\n" + frames("lasgun", 2, 4)
s += "look 215 30\nwait 4\nshot lasgun_down\nlook 215 -25\nwait 4\nshot lasgun_up\nlook 215 0\n"
s += give("minecraft:diamond_sword") + "wait 6\n"
for k in range(2):
    s += "click attack\n" + frames(f"sword{k}_", 6, 1) + "wait 8\n"
s += f"cmd setblock {OX + 1} {Y + 1} -2 minecraft:stone\ncmd tp @s {OX} {Y} 0 200 25\nwait 6\n" + give("minecraft:iron_pickaxe") + "key attack on\n" + frames("mine", 16, 1) + "key attack off\n"
s += "cmd clear @s\ncmd wb gene human\nquit\n"
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "player_actions.txt"), "w", encoding="utf-8") as f:
    f.write(s)
