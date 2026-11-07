#!/usr/bin/env python3
"""Сценарий player_states: игрок-Астартес в особых состояниях. Лестница (вверх, вниз, висит), бассейн (держится на воде, плывёт кролем),
щель в блок (ползком), лодка (сидит), кровать (спит), элитры, полёт творческого режима. Пишет tools/autotest/player_states.txt."""
import os

OX, Y = 29100, 280


def frames(tag, n, step=2):
    return "".join(f"wait {step}\nshot {tag}{i}\n" for i in range(n))


s = f"""# Игрок-Астартес: особые состояния
cmd time set noon
cmd weather clear
cmd gamerule doDaylightCycle false
cmd gamerule doMobSpawning false
cmd gamemode survival
cmd effect give @s minecraft:resistance infinite 10 true
cmd effect give @s minecraft:water_breathing infinite 0 true
cmd tp @s {OX} {Y + 2} 0 0 30
wait 60
cmd fill {OX - 30} {Y - 1} -30 {OX + 30} {Y - 1} 30 minecraft:polished_deepslate
wait 300
cmd fill {OX - 30} {Y} -20 {OX + 30} {Y + 12} 20 minecraft:air
wait 20
cmd kill @e[type=!minecraft:player]
cmd clear @s
cmd wb gene astartes
hud off
"""
# ---- лестница: стена и лестницы на южной стороне, игрок смотрит на север
s += f"cmd fill {OX - 1} {Y} -4 {OX + 1} {Y + 8} -4 minecraft:stone\ncmd fill {OX} {Y} -3 {OX} {Y + 8} -3 minecraft:ladder[facing=south]\n"
s += f"cmd tp @s {OX}.5 {Y} -1.5 180 -10\nwait 10\ncamera back\nwait 6\nkey forward on\n" + frames("ladder_up", 12) + "key forward off\n"
s += "wait 4\nshot ladder_hang0\nkey shift on\nwait 10\nshot ladder_hang1\nkey shift off\n" + frames("ladder_down", 8)
s += "wait 30\ncamera front\n"
# ---- бассейн: стекло, вода 4 в глубину
P0, P1 = OX + 6, OX + 20
s += f"cmd fill {P0} {Y} -6 {P1} {Y + 4} 6 minecraft:glass\ncmd fill {P0 + 1} {Y} -5 {P1 - 1} {Y + 4} 5 minecraft:water\nwait 10\n"
s += f"cmd tp @s {P0 + 7} {Y + 2} 0 90 0\nwait 4\ncamera front\n" + frames("tread", 8)
s += f"cmd tp @s {P1 - 2} {Y + 1.5} 0 90 10\nwait 6\nkey forward on\nkey sprint on\nwait 10\n" + frames("swim", 10, 1) + "key forward off\nkey sprint off\nwait 10\n"
s += f"cmd fill {P0} {Y} -6 {P1} {Y + 4} 6 minecraft:air\nwait 10\n"
# ---- щель в один блок: потолок над площадкой, игрок внутри — ползком
s += f"cmd fill {OX - 12} {Y + 1} 6 {OX - 4} {Y + 1} 10 minecraft:stone\ncmd tp @s {OX - 4}.5 {Y} 8.5 90 0\nwait 10\ncamera back\nkey forward on\n" + frames("crawl", 10) + "key forward off\nwait 10\n"
s += f"cmd fill {OX - 12} {Y + 1} 6 {OX - 4} {Y + 1} 10 minecraft:air\n"
# ---- лодка
s += f"cmd tp @s {OX} {Y} 8 180 10\ncmd summon minecraft:oak_boat {OX} {Y} 6\nwait 6\ncmd ride @s mount @e[type=minecraft:oak_boat,limit=1,sort=nearest]\nwait 10\ncamera front\nwait 6\nshot sit0\nwait 20\nshot sit1\ncmd ride @s dismount\ncmd kill @e[type=minecraft:oak_boat]\nwait 10\n"
# ---- кровать ночью
s += f"cmd setblock {OX + 4} {Y} 12 minecraft:red_bed[facing=south,part=foot]\ncmd setblock {OX + 4} {Y} 13 minecraft:red_bed[facing=south,part=head]\n"
s += f"cmd time set 18000\ncmd tp @s {OX + 4} {Y} 10 0 30\nwait 10\nuseblock {OX + 4} {Y} 12\nwait 30\ncamera front\nwait 4\nshot sleep0\ncamera back\nwait 4\nshot sleep1\n"
s += "cmd time set noon\nwait 10\nkey shift on\nwait 2\nkey shift off\nwait 20\n"
# ---- элитры: с высоты, прыжок в воздухе раскрывает
s += f"cmd item replace entity @s armor.chest with minecraft:elytra\ncmd tp @s {OX} {Y + 40} 0 180 10\nwait 4\ncamera back\nwait 10\nkey jump on\nwait 1\nkey jump off\nwait 2\nkey jump on\nwait 1\nkey jump off\n" + frames("glide", 10, 3)
s += f"cmd item replace entity @s armor.chest with minecraft:air\ncmd tp @s {OX} {Y} 0 180 0\nwait 30\n"
# ---- полёт творческого
s += f"cmd gamemode creative\ncmd tp @s {OX} {Y + 3} 0 180 0\nwait 4\nfly on\ncamera front\nwait 20\n" + frames("fly", 4, 5)
s += "key forward on\nwait 15\n" + frames("flymove", 4, 4) + "key forward off\nfly off\ncmd gamemode survival\nwait 30\n"
s += "cmd wb gene human\nquit\n"
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "player_states.txt"), "w", encoding="utf-8") as f:
    f.write(s)
