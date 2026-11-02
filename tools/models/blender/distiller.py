"""
Перегонная колонна (distiller): 3×3×9. Высокая тарельчатая колонна с поясами и площадками, четыре отвода фракций на разных
уровнях (баки-приёмники внизу), конденсатор с вентилятором наверху, факел попутного газа, топка в основании, смотровые окна с кипением.
"""
import math
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "kit.py"), encoding="utf-8").read())

LOOP, STEPS = 3.0, 48
CX, CY = -0.1, 0.1    # ось колонны
R = 0.74
OUT = ((2.0, "brick", -1), (3.6, "brass", 1), (5.2, "steel", -1), (6.6, "water", 1))   # отводы: высота, цвет бака, сторона


def frame(m):
    f = m.bone("frame")
    f.plinth(-1.48, -1.48, 1.48, 1.48)
    # ---- топка в основании
    f.box((-1.0, -1.05, 0.3), (0.8, 1.25, 1.05), "brick", bevel=0.06)
    f.box((-1.03, -1.08, 0.3), (0.83, 1.28, 0.42), "dark", bevel=0.02)
    f.box((-0.5, -1.07, 0.48), (0.3, -1.04, 0.9), "dark")
    f.box((-0.44, -1.08, 0.53), (0.24, -1.065, 0.85), "fire")
    for x in (-0.3, -0.1, 0.1):
        f.box((x - 0.012, -1.09, 0.5), (x + 0.012, -1.07, 0.88), "dark")
    # ---- колонна: тело вращения с тарельчатыми фланцами
    prof = [(R + 0.08, 0), (R + 0.08, 0.08), (R, 0.14)]
    z = 0.8
    while z < 6.8:
        prof += [(R, z), (R + 0.07, z + 0.02), (R + 0.07, z + 0.1), (R, z + 0.12)]
        z += 0.8
    prof += [(R, 7.05), (R * 0.82, 7.3), (R * 0.45, 7.5), (R * 0.32, 7.6)]
    f.lathe((CX, CY, 1.05), prof, 16, "hull", base=False)
    for z in (2.65, 4.25, 5.85):
        f.ring((CX, CY, z), R - 0.04, R + 0.05, 0.07, 16, "brass", "Z")
    # смотровые окна: тёмная рама и огонь кипения за ними
    for z, mat in ((1.65, "fire"), (3.1, "stain_gold"), (4.7, "stain_gold"), (6.3, "glass")):
        f.box((CX - 0.15, CY - R - 0.06, z - 0.25), (CX + 0.15, CY - R + 0.05, z + 0.25), "dark", bevel=0.015)
        f.box((CX - 0.1, CY - R - 0.07, z - 0.2), (CX + 0.1, CY - R - 0.05, z + 0.2), mat)
    # ---- отводы фракций и баки-приёмники: у каждого свой цвет полосы
    for i, (z, mat, s) in enumerate(OUT):
        x = CX + s * R
        ex = s * 1.27
        f.pipe([(x, CY, z), (ex, CY + 0.2, z), (ex, CY + 0.2 + i * 0.1, z - 0.4)], 0.07, 8, "rust")
        f.ring((ex * 0.82, CY + 0.1, z), 0.06, 0.13, 0.03, 8, "red", "X")
    # баки по углам
    for (x, y), mat in zip(((1.05, 0.85), (-1.15, 0.9), (1.05, -0.85), (-1.15, -0.85)), ("brick", "steel", "brass", "water")):
        f.tank((x, y, 0.3), 0.3, 1.2, 10, "hull", (0.3, 0.72), band_mat=mat)
    f.pipe([(1.27, CY + 0.3, 3.2), (1.3, 0.85, 2.0), (1.05, 0.85, 1.78)], 0.05, 6, "rust")
    f.pipe([(-1.27, CY + 0.2, 1.6), (-1.27, 0.75, 1.6), (-1.15, 0.9, 1.78)], 0.05, 6, "rust")
    f.pipe([(1.27, CY + 0.5, 6.2), (1.4, -0.3, 4.0), (1.05, -0.85, 1.78)], 0.05, 6, "rust")
    f.pipe([(-1.27, CY + 0.4, 4.8), (-1.4, -0.3, 3.0), (-1.15, -0.85, 1.78)], 0.05, 6, "rust")
    # ---- площадка на половине высоты: балки, настил, перила, лестница
    z = 4.45
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        f.beam((sx * 1.2, sy * 1.2, 0.3), (sx * 0.95, sy * 0.95, z), 0.12, 0.12, "dark")
    f.ring((CX, CY, z + 0.04), R + 0.02, 1.32, 0.08, 16, "dark", "Z")
    for k in range(12):
        a = k * math.pi / 6
        f.box((CX + 1.28 * math.cos(a) - 0.02, CY + 1.28 * math.sin(a) - 0.02, z + 0.08), (CX + 1.28 * math.cos(a) + 0.02, CY + 1.28 * math.sin(a) + 0.02, z + 0.72), "steel")
    f.ring((CX, CY, z + 0.72), 1.24, 1.31, 0.05, 16, "hazard", "Z")
    f.ladder(CX, CY + R + 0.12, 1.1, z, 0.42)
    f.ladder(CX, CY + R + 0.12, z + 0.1, 7.05, 0.42)
    # ---- конденсатор на верхушке: кожух, рёбра, кольцо вентилятора
    f.lathe((CX, CY, 8.25), [(0.2, -0.62), (0.2, 0), (0.62, 0.0), (0.62, 0.22), (0.2, 0.22)], 14, "hull", cap=False)
    for k in range(6):
        f.ring((CX, CY, 7.76 + k * 0.08), 0.2, 0.44, 0.022, 10, "dark", "Z")
    # факел попутного газа сбоку
    f.pipe([(CX + 0.32, CY, 7.45), (1.2, CY - 0.3, 7.6), (1.2, CY - 0.3, 8.2)], 0.06, 8, "rust")
    f.lathe((1.2, CY - 0.3, 8.2), [(0.1, 0), (0.15, 0.12)], 8, "dark", base=False)
    # череп, шестерня, печати
    f.gear((CX, CY - R - 0.02, 2.4), 0.3, 0.4, 0.05, 12, "brass", "Y")
    f.skull(CX, CY - R - 0.04, 2.42, 0.46)
    f.seal((CX + 0.5, CY - R, 3.95), "Y", -1)
    f.seal((CX - 0.5, CY - R, 5.55), "Y", -1)
    f.box((0.4, -1.42, 0.3), (1.2, -1.15, 0.5), "dark")
    f.box((0.5, -1.4, 0.5), (1.1, -1.2, 1.15), "hull", bevel=0.02)
    f.box((0.53, -1.41, 0.62), (1.07, -1.395, 1.08), "screen")


def moving(m):
    # ---- вентилятор конденсатора и факел
    fan = m.bone("fan", (CX, CY, 8.36))
    fan.lathe((CX, CY, 8.3), [(0.08, 0), (0.08, 0.1)], 6, "dark", base=False)
    for k in range(5):
        a = k * 2 * math.pi / 5
        fan.beam((CX, CY, 8.36), (CX + 0.5 * math.cos(a), CY + 0.5 * math.sin(a), 8.36), 0.13, 0.02, "brass")
    fl = m.bone("stack_flame", (1.2, CY - 0.3, 8.32))
    fl.lathe((1.2, CY - 0.3, 8.32), [(0.13, 0), (0.1, 0.18), (0.015, 0.5)], 6, "fire", base=False)
    # ---- маховик подачи у топки
    w = m.bone("pump", (0.88, CY + 0.15, 0.82))
    w.ring((0.88, CY + 0.15, 0.82), 0.16, 0.24, 0.06, 12, "brass")
    for k in range(4):
        a = k * math.pi / 2
        w.beam((0.88, CY + 0.15, 0.82), (0.88, CY + 0.15 + 0.2 * math.cos(a), 0.82 + 0.2 * math.sin(a)), 0.03, 0.03, "steel")
    # ---- пузыри кипения за нижним окном: снаружи на раме, как индикатор
    for i in range(4):
        b = m.bone(f"bubble_{i}", (CX, CY - R - 0.08, 1.45))
        b.lathe((CX - 0.06 + i * 0.04, CY - R - 0.08, 1.45), [(0, -0.03), (0.022, -0.012), (0.022, 0.012), (0, 0.03)], 5, "stain_gold", cap=False)


def pose(t):
    a = 2 * math.pi * t
    p = {
        "fan": {"rot": (0, 0, -360 * 3 * t)},
        "pump": {"rot": (360 * t, 0, 0)},
        "stack_flame": {"scale": (1, 1, 1 + 0.35 * math.sin(4 * a) + 0.18 * math.sin(11 * a))},
    }
    for i in range(4):
        u = (t * 3 + i * 0.25) % 1
        vis = 1 if u < 0.92 else 0
        p[f"bubble_{i}"] = {"pos": (0, 0, 0.38 * u), "scale": (vis, vis, vis)}
    return p


m = Machine("distiller")
frame(m)
moving(m)
sc, tris = m.build("WB_Distiller")
light_scene(sc, int(LOOP * 24))
auto_animate(m.objects, sc, pose, LOOP)
tracks = lambda: auto_tracks(pose, LOOP, STEPS)
print("костей:", len(m.objects), "треугольников:", tris)
