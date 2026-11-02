"""
Промывочный чан (wash_vat): 3×3×3. Клёпаный чан с освящённой водой; привод на мосту вращает мешалку, насос качает воду,
кадильница над краем. Ядро в середине переднего ряда.
"""
import math
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "kit.py"), encoding="utf-8").read())

LOOP = 3.0
CX, CY = 0.0, 0.05    # ось чана
R = 1.14              # внешний радиус
TOP = 1.75            # верхний край


def frame(m):
    f = m.bone("frame")
    f.box((-1.48, -1.48, 0), (1.48, 1.48, 0.14), "dark", bevel=0.04)
    f.box((-1.36, -1.36, 0.14), (1.36, 1.36, 0.22), "hull", bevel=0.02)
    for a, b in (((-1.36, -1.36), (1.36, -1.26)), ((-1.36, 1.26), (1.36, 1.36)), ((-1.36, -1.26), (-1.26, 1.26)), ((1.26, -1.26), (1.36, 1.26))):
        f.box((a[0], a[1], 0.22), (b[0], b[1], 0.23), "hazard")
    # чаша: стенка снаружи, кромка, стенка внутри; бандажи и заклёпки
    f.lathe((CX, CY, 0.22), [(R * 0.86, 0), (R * 0.97, 0.2), (R, 0.45), (R, TOP - 0.22), (R * 1.04, TOP - 0.18), (R * 1.04, TOP),
                             (R * 0.93, TOP), (R * 0.93, TOP - 0.3), (R * 0.9, 0.5)], 24, "hull", cap=False)
    for z in (0.75, 1.3):
        f.ring((CX, CY, z), R * 0.98, R * 1.03, 0.11, 24, "brass", "Z")
    for k in range(12):
        a = k * math.pi / 6 + 0.13
        f.bolt((CX + R * 1.03 * math.cos(a), CY + R * 1.03 * math.sin(a), 1.02), "Z", 0.04, 0.03, "steel")
    # опоры чаши
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        x, y = 1.15 * math.cos(a), 1.15 * math.sin(a)
        f.wedge((x - 0.13, y - 0.13, 0.22), (x + 0.13, y + 0.13), (x * 0.92 - 0.07, y * 0.92 - 0.07, 0.9), (x * 0.92 + 0.07, y * 0.92 + 0.07), "dark")
    # мост с редуктором над чашей
    for s in (-1, 1):
        f.box((s * 1.2 - 0.09, -0.22 + CY, 0.22), (s * 1.2 + 0.09, 0.22 + CY, 2.55), "hull", bevel=0.03)
        f.wedge((s * 1.2 - 0.15, -0.5 + CY, 0.22), (s * 1.2 + 0.15, 0.5 + CY), (s * 1.2 - 0.09, -0.2 + CY, 1.2), (s * 1.2 + 0.09, 0.2 + CY), "dark")
    f.box((-1.32, -0.25 + CY, 2.45), (1.32, 0.25 + CY, 2.67), "dark", bevel=0.03)
    f.box((-0.5, -0.42 + CY, 2.3), (0.5, 0.42 + CY, 2.9), "hull", bevel=0.05)
    f.box((-0.52, -0.44 + CY, 2.56), (0.52, 0.44 + CY, 2.63), "brass")
    f.lathe((0, CY, 2.9), [(0.3, 0), (0.3, 0.05), (0.2, 0.09)], 10, "steel", base=False)
    f.gear((-0.28, -0.46 + CY, 2.52), 0.14, 0.2, 0.05, 10, "dark", "Y")     # неподвижная накладка редуктора
    # мотор на мосту, кабели
    f.lathe((0.45, CY, 2.67 + 0.14), [(0.17, 0), (0.17, 0.95)], 10, "rust", "X")
    for x in (0.65, 0.85, 1.05, 1.25):
        f.ring((x, CY, 2.81), 0.15, 0.2, 0.05, 10, "dark", "X")
    f.pipe([(1.2, CY, 2.66), (1.29, CY - 0.3, 2.1), (1.29, CY - 0.3, 0.3)], 0.03, 6, "rubber")
    # насос сзади, труба в чан и обратно
    f.tank((0.8, 1.15, 0.22), 0.27, 0.7, 10, "rust", (0.5,), dome=False)
    f.box((0.68, 1.03, 0.92), (0.92, 1.27, 1.42), "dark", bevel=0.02)       # направляющая плунжера
    f.pipe([(0.8, 1.15, 0.5), (0.2, 1.3, 0.5), (-0.45, 1.3, 0.8), (-0.45, 1.3, 2.05), (-0.45, 0.85, 2.15), (-0.45, 0.62, 1.95)], 0.055, 8, "steel")
    f.lathe((-0.45, 0.62, 1.95), [(0.1, 0), (0.1, -0.14)], 8, "brass")      # излив
    f.box((-0.6, 1.25, 1.65), (-0.3, 1.32, 1.95), "dark")
    # манометр и вентиль спереди, печати
    f.lathe((-0.72, CY - R * 0.9, 1.25), [(0.13, 0), (0.13, -0.05), (0.11, -0.07)], 12, "brass", "Y", base=False)
    f.lathe((-0.72, CY - R * 0.9 - 0.07, 1.25), [(0.095, 0), (0.095, -0.004)], 12, "glass", "Y", base=False)
    f.pipe([(0.72, CY - R * 0.85, 0.5), (0.72, -1.3, 0.5)], 0.06, 8, "rust")
    f.ring((0.72, -1.33, 0.5), 0.08, 0.13, 0.03, 10, "red", "Y")
    f.seal((-0.2, CY - R * 1.03, 1.05), "Y", -1)
    f.seal((1.2, CY + 0.25, 1.8), "Y", 1)
    # череп на лицевой стороне чана
    f.skull(0.3, CY - R * 0.9, 0.85, 0.42, augmetic=False)
    # кадильница на кронштейне над углом
    f.pipe([(-1.2, CY - 0.1, 2.3), (-1.32, -1.02, 2.3), (-1.2, -1.15, 2.2)], 0.025, 6, "brass")
    f.lathe((-1.2, -1.15, 1.72), [(0.04, 0), (0.13, 0.08), (0.13, 0.2), (0.07, 0.3), (0.02, 0.48)], 8, "brass", base=False)
    f.lathe((-1.2, -1.15, 1.93), [(0.135, 0), (0.135, 0.015)], 8, "fire", base=False)


def moving(m):
    # вода: качается по высоте; пена вращается с мешалкой
    w = m.bone("water", (CX, CY, 1.4))
    w.lathe((CX, CY, 1.4), [(R * 0.92, 0), (R * 0.92, 0.03)], 24, "water", base=False)
    # мешалка: вал, две лопасти с зубцами, крестовина над водой
    p = m.bone("agitator", (CX, CY, 1.4))
    p.lathe((CX, CY, 0.7), [(0.08, 0), (0.08, 1.65)], 10, "steel", base=False)
    p.ring((CX, CY, 2.22), 0.08, 0.22, 0.09, 10, "brass", "Z")
    for k in range(3):
        a = k * 2 * math.pi / 3
        x, y = math.cos(a), math.sin(a)
        end = (CX + x * 0.85, CY + y * 0.85, 1.42)
        p.beam((CX, CY, 1.42), end, 0.15, 0.05, "steel")
        p.beam((end[0] - x * 0.1, end[1] - y * 0.1, 1.12), (end[0], end[1], 1.52), 0.12, 0.05, "rust")
    # плунжер насоса
    q = m.bone("plunger", (0.8, 1.15, 1.0))
    q.lathe((0.8, 1.15, 0.95), [(0.05, 0), (0.05, 0.75)], 8, "steel", base=False)
    q.box((0.68, 1.06, 1.7), (0.92, 1.24, 1.78), "dark", bevel=0.015)


def state(t):
    a = 2 * math.pi * t
    return a, 0.02 * math.sin(2 * a), 0.2 * math.sin(2 * a)


def animate(objs, sc):
    frames = int(LOOP * 24)
    for f in range(frames + 1):
        a, dw, dq = state(f / frames)
        objs["agitator"].rotation_euler = (0, 0, -a)
        objs["water"].location = (CX, CY, 1.4 + dw)
        objs["plunger"].location = (0.8, 1.15, 1.0 + dq)
        objs["agitator"].keyframe_insert("rotation_euler", frame=f + 1)
        objs["water"].keyframe_insert("location", frame=f + 1)
        objs["plunger"].keyframe_insert("location", frame=f + 1)
    sc.frame_set(1)


def tracks():
    steps = 24
    water, plunger = {}, {}
    for i in range(steps + 1):
        t = i / steps
        a, dw, dq = state(t)
        water[f"{LOOP * t:.4f}"] = [0, round(dw * 16, 3), 0]
        plunger[f"{LOOP * t:.4f}"] = [0, round(dq * 16, 3), 0]
    # поворот вокруг Z Blender с минусом = +Y анимации (см. export_machine)
    spin = {f"{LOOP * i / 4:.4f}": [0, 90.0 * i, 0] for i in range(5)}
    return {"agitator": {"rotation": spin}, "water": {"position": water}, "plunger": {"position": plunger}}, LOOP


m = Machine("wash_vat")
frame(m)
moving(m)
sc, tris = m.build("WB_WashVat")
light_scene(sc, int(LOOP * 24))
animate(m.objects, sc)
print("костей:", len(m.objects), "треугольников:", tris)
