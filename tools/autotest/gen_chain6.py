#!/usr/bin/env python3
"""Сценарий chain6: десять новых машин глав 1–4 на мешах, цикл анимации, настоящая лужа прометия из генерации. Пишет tools/autotest/chain6.txt."""
import math
import os

OX = 12000
ROWS = [
    # имя, x, z, куда встать для кадра: смещение камеры, поворот
    ("chem_reactor", -40, -10), ("powder_works", -28, -10), ("cement_mill", -16, -10), ("cracker", -4, -10), ("promethium_gen", 10, -10),
    ("hydroponics", -40, 12), ("lumber", -26, 12), ("deep_drill", -10, 12),
]
s = f"""# Новые машины. Площадка новая: после заливки ждём пересчёт света
cmd time set noon
cmd weather clear
cmd gamerule doDaylightCycle false
cmd gamemode creative
cmd tp @s {OX} 215 -30 0 30
wait 60
cmd fill {OX - 50} 199 -30 {OX + 30} 199 40 minecraft:polished_deepslate
hud off
wait 300
"""
for name, dx, z in ROWS:
    x = OX + dx
    s += f"cmd setblock {x} 200 {z} warpbound:{name}[facing=north]\ncmd tp @s {x} 200 {z - 2} 0 0\nwait 8\ncmd wb machine build\nwait 8\n"
# горн и пресс строятся из своих блоков: как и у остальных, команда сама ставит шаблон
for name, dx, z in (("salvage_forge", 18, 12), ("manual_press", 26, 12)):
    x = OX + dx
    s += f"cmd setblock {x} 200 {z} warpbound:{name}[facing=north]\ncmd tp @s {x} 200 {z - 2} 0 0\nwait 8\ncmd wb machine build\nwait 8\n"
# старые ядра при пересборке падают предметами прямо перед машиной
s += "clearchat\ncmd kill @e[type=item]\n"


def closeup(name, x, z, depth, h, r, tag="", side=0.55):
    """Камера спереди сбоку, взгляд точно в центр машины."""
    cx, cy, cz = x + 0.5, 200 + h / 2, z + depth / 2
    px, py, pz = cx + r * side, cy + r * 0.35, cz - r
    yaw = math.degrees(math.atan2(-(cx - px), cz - pz))
    pitch = math.degrees(math.atan2(py - cy, math.hypot(cx - px, cz - pz)))
    # игрок стоит на ногах, камера на 1.62 выше
    return f"cmd tp @s {px:.2f} {py - 1.62:.2f} {pz:.2f} {yaw:.1f} {pitch:.1f}\nwait 25\nshot {name}{tag}\n"


DIM = {"chem_reactor": (3, 4, 5.5), "powder_works": (3, 4, 6.5), "cement_mill": (3, 4, 5.5), "cracker": (3, 5, 6.5), "promethium_gen": (3, 4, 6.5),
       "hydroponics": (3, 4, 6.5), "lumber": (5, 4, 7.5), "deep_drill": (5, 12, 14), "salvage_forge": (3, 3, 4.5), "manual_press": (2, 3, 4)}
for name, dx, z in ROWS + [("salvage_forge", 18, 12), ("manual_press", 26, 12)]:
    d, h, r = DIM[name]
    s += closeup(name, OX + dx, z, d, h, r)
    if name in ("powder_works", "promethium_gen", "lumber", "cement_mill"):
        s += "wait 16\n" + f"shot {name}_b\n"
s += f"cmd tp @s {OX - 5} 225 -32 0 30\nwait 60\nfps все новые машины в кадре\nshot all\n"
# лужа из настоящей генерации: далеко на новых чанках
s += "cmd tp @s 60000 150 60000 0 60\nwait 80\ncmd wb deposit tp\nwait 200\ncmd wb deposit tp\nwait 200\nclearchat\nshot seep_far\nwait 40\nshot seep_b\nquit\n"
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "chain6.txt"), "w", encoding="utf-8") as f:
    f.write(s)
