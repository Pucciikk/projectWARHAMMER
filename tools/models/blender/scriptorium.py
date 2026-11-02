"""
Скрипторий (scriptorium): 5×5×5. Готическая часовня-мастерская: контрфорсы, стрельчатые арки, крыша со шпилем и шестернёй,
витражное окно сзади. Внутри аналой с механическим пером, лента пергамента, свечи; с балок качаются кадила, вокруг летает сервочереп.
"""
import math
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "kit.py"), encoding="utf-8").read())

LOOP = 4.0
W = 2.15          # полуширина зала
TOP = 3.3         # высота стен
CY = 0.0


def arch(f, x, y0, y1, half, z0, z1, peak, mat="hull"):
    """Стрельчатая рама в плоскости XZ: снаружи и внутри контура."""
    outer = [(x - half, z0), (x - half, z1), (x - half * 0.6, z1 + peak * 0.62), (x, z1 + peak), (x + half * 0.6, z1 + peak * 0.62), (x + half, z1), (x + half, z0)]
    t = 0.09
    inner = [(x - half + t, z0), (x - half + t, z1), (x - (half - t) * 0.6, z1 + peak * 0.62 - t * 0.4), (x, z1 + peak - t * 1.5), (x + (half - t) * 0.6, z1 + peak * 0.62 - t * 0.4), (x + half - t, z1), (x + half - t, z0)]
    for i in range(len(outer) - 1):
        f.plate_xz([outer[i], outer[i + 1], inner[i + 1], inner[i]], y0, y1, mat)


def frame(m):
    f = m.bone("frame")
    f.plinth(-2.48, -2.48, 2.48, 2.48)
    # ---- пол, ступени входа
    f.box((-2.25, -2.25, 0.3), (2.25, 2.25, 0.42), "dark", bevel=0.02)
    for k in range(3):
        f.box((-0.9 - k * 0.1, -2.48 + k * 0.1 - 0.0, 0.3), (0.9 + k * 0.1, -2.25 + k * 0.1, 0.42 - k * 0.04), "hull")
    # ---- колонны и контрфорсы по углам и вдоль боков
    for sx in (-1, 1):
        for y in (-W, -0.72, 0.72, W):
            f.box((sx * W - 0.14, y - 0.14, 0.42), (sx * W + 0.14, y + 0.14, TOP), "hull", bevel=0.03)
            f.lathe((sx * W, y, TOP), [(0.16, 0), (0.1, 0.1), (0.12, 0.2), (0.01, 0.55)], 6, "dark", base=False)   # пинакль
            a, b = sorted((sx * (W + 0.1), sx * 2.45))
            c, d = sorted((sx * (W + 0.08), sx * (W + 0.13)))
            f.wedge((a, y - 0.08, 0.3), (b, y + 0.08), (c, y - 0.05, 2.2), (d, y + 0.05), "dark")
    # ---- передний портал и задняя стена с витражом
    for x in (-W, 0.0, W):
        pass
    arch(f, 0, -W - 0.05, -W + 0.08, 1.05, 0.42, 2.0, 1.12)
    f.box((-W, -W - 0.04, TOP - 0.2), (W, -W + 0.08, TOP), "hull")
    for sx in (-1, 1):
        f.box((sx * 1.05 + sx * 0.0 - 0.06, -W - 0.05, 0.42), (sx * 1.05 + 0.06, -W + 0.08, 2.0), "dark")
        f.box((sx * 1.6 - 0.45, -W - 0.04, 0.42), (sx * 1.6 + 0.45, -W + 0.06, TOP - 0.2), "hull")
    f.box((-W, W - 0.08, 0.42), (W, W + 0.05, TOP), "hull")
    # витраж: стрельчатая рама, цветные стёкла, свинцовые переплёты
    for iy, y0 in enumerate((W + 0.05, W - 0.09)):
        for k, mat in enumerate(("stain_red", "stain_gold", "stain_blue", "stain_gold")):
            z = 1.05 + k * 0.35
            f.box((-0.72, y0, z), (0.72, y0 + 0.01, z + 0.35), mat)
    arch(f, 0, W - 0.1, W + 0.07, 0.78, 1.0, 2.45, 0.62, "brass")
    for x in (-0.36, 0, 0.36):
        f.box((x - 0.018, W - 0.1, 1.05), (x + 0.018, W + 0.07, 2.45), "dark")
    for z in (1.4, 1.75, 2.1):
        f.box((-0.72, W - 0.1, z - 0.018), (0.72, W + 0.07, z + 0.018), "dark")
    # боковые стрельчатые окна между колоннами
    for sx in (-1, 1):
        for y0, y1 in ((-W + 0.14, -0.86), (-0.58, 0.58), (0.86, W - 0.14)):
            f.box((sx * W - 0.05, y0, 0.42), (sx * W + 0.05, y1, 1.15), "hull")
            mid = (y0 + y1) / 2
            half = (y1 - y0) / 2
            f.box((sx * W - 0.05, y0, 2.75), (sx * W + 0.05, y1, TOP), "hull")
            mat_a, mat_b = ("stain_red", "stain_gold") if abs(mid) < 0.1 else ("stain_blue", "stain_gold")
            for k in range(4):
                z = 1.15 + k * 0.4
                f.box((sx * W - 0.02, y0 + 0.06, z), (sx * W + 0.02, y1 - 0.06, z + 0.4), mat_a if k % 2 else mat_b)
                f.box((sx * W - 0.03, y0, z - 0.015), (sx * W + 0.03, y1, z + 0.015), "dark")
            f.box((sx * W - 0.03, mid - 0.015, 1.15), (sx * W + 0.03, mid + 0.015, 2.75), "dark")
            # стрелка окна: два наклонных бруса сходятся над проёмом
            f.beam((sx * W, y0 + 0.02, 2.4), (sx * W, mid, 2.74), 0.09, 0.09, "dark")
            f.beam((sx * W, y1 - 0.02, 2.4), (sx * W, mid, 2.74), 0.09, 0.09, "dark")
    # ---- крыша: скаты, конёк, шпиль с шестернёй
    f.box((-2.42, -2.42, TOP), (2.42, 2.42, TOP + 0.14), "dark", bevel=0.03)
    f.box((-2.44, -2.44, TOP + 0.05), (2.44, 2.44, TOP + 0.09), "brass")
    f.loft([(TOP + 0.14, 2.3, 2.3, 0), (TOP + 1.3, 0.42, 0.42, 0)], "brick")
    for s1 in (-1, 1):                                          # стальные рёбра по углам ската
        for s2 in (-1, 1):
            f.beam((s1 * 2.3, s2 * 2.3, TOP + 0.16), (s1 * 0.42, s2 * 0.42, TOP + 1.32), 0.1, 0.1, "dark")
    f.box((-0.46, -0.46, TOP + 1.3), (0.46, 0.46, TOP + 1.38), "dark", bevel=0.015)
    f.lathe((0, 0, TOP + 1.38), [(0.3, 0), (0.24, 0.1), (0.08, 0.3), (0.05, 1.0)], 8, "hull", base=False)
    f.gear((0, 0, TOP + 2.0), 0.14, 0.22, 0.05, 10, "brass", "Y")
    # над порталом — череп в шестерне
    f.gear((0, -W - 0.05, 2.55), 0.42, 0.54, 0.05, 12, "brass", "Y")
    f.skull(0, -W - 0.03, 2.56, 0.64)
    # ---- аналой, лента пергамента, книжные полки, свечи
    f.box((-0.42, 0.05, 0.42), (0.42, 0.65, 1.15), "brick", bevel=0.05)
    f.box((-0.62, 0.0, 1.15), (0.62, 0.72, 1.24), "dark", bevel=0.025)
    f.box((-0.52, 0.1, 1.24), (0.52, 0.62, 1.27), "parchment")
    f.lathe((-1.2, 0.4, 0.42), [(0.12, 0), (0.12, 0.75)], 8, "steel", "X")
    f.lathe((1.2 - 0.4, 0.4, 0.42), [(0.12, 0), (0.12, 0.75)], 8, "steel", "X")
    for sx in (-1, 1):
        f.box((sx * 1.72 - 0.2, -1.92, 0.42), (sx * 1.72 + 0.2, -0.95, 2.1), "brick", bevel=0.025)
        for z in (0.82, 1.22, 1.62):
            f.box((sx * 1.72 - 0.22, -1.94, z - 0.03), (sx * 1.72 + 0.22, -0.93, z + 0.03), "dark")
            for k in range(6):
                y = -1.85 + k * 0.15
                f.box((sx * 1.55 - 0.02, y, z + 0.03), (sx * 1.55 + 0.02, y + 0.11, z + 0.24 - 0.03 * (k % 2)), "parchment" if k % 2 else "wax")
    for x, y, h in ((-0.75, 1.2, 0.5), (0.75, 1.2, 0.5), (-0.95, 0.65, 0.9), (0.95, 0.65, 0.9)):
        f.lathe((x, y, 0.42), [(0.12, 0), (0.05, 0.12), (0.05, h), (0.1, h + 0.03)], 8, "brass", base=False)
        f.lathe((x, y, 0.42 + h + 0.03), [(0.06, 0), (0.06, 0.14)], 6, "parchment", base=False)
        f.lathe((x, y, 0.42 + h + 0.17), [(0.04, 0), (0.008, 0.14)], 5, "fire", base=False)
    # балка и подвески кадил
    f.box((-1.82, -0.74, 2.85), (1.82, -0.58, 3.02), "dark", bevel=0.02)
    f.seal((0.62, -W - 0.05, 1.3), "Y", -1)
    f.seal((-0.62, -W - 0.05, 1.3), "Y", -1)


def moving(m):
    # ---- перо на рычаге: выводит строку, переходя взад-вперёд
    q = m.bone("quill_arm", (0, 0.72, 2.0))
    q.box((-0.06, 0.66, 1.92), (0.06, 0.78, 2.08), "brass", bevel=0.015)
    q.beam((0, 0.72, 2.0), (0, 0.42, 1.42), 0.05, 0.05, "steel")
    q.beam((0, 0.42, 1.42), (0, 0.38, 1.28), 0.02, 0.02, "dark")
    q.beam((0, 0.42, 1.42), (0.06, 0.45, 1.72), 0.012, 0.09, "parchment")
    q.lathe((0, 0.72, 2.0), [(0.03, 0), (0.03, 0.85)], 6, "steel", base=False)
    # ---- лента: пергамент ползёт по аналою и свисает
    p = m.bone("parchment", (-1.2, 0.4, 1.27))
    p.box((-1.1, 0.15, 1.27), (-0.5, 0.58, 1.285), "parchment")
    # ---- кадила: качаются на цепях
    for i, x in enumerate((-1.2, 1.2)):
        c = m.bone(f"censer_{i + 1}", (x, -0.66, 2.85))
        c.lathe((x, -0.66, 2.0), [(0.015, 0), (0.015, 0.85)], 4, "steel", base=False)
        c.lathe((x, -0.66, 1.62), [(0.04, 0), (0.15, 0.1), (0.16, 0.24), (0.08, 0.34), (0.015, 0.44)], 8, "brass", base=False)
        c.lathe((x, -0.66, 1.86), [(0.165, 0), (0.165, 0.012)], 8, "fire", base=False)
    # ---- сервочереп: летит по кругу над залом и покачивается
    s = m.bone("servo_skull", (0, 0, 2.3))
    s.skull(0, -1.05, 2.3, 0.4, augmetic=True)
    s.lathe((0, -1.08, 2.02), [(0.05, 0), (0.04, -0.15), (0.015, -0.28)], 6, "dark", base=False)
    s.box((-0.3, -1.1, 2.26), (-0.14, -1.03, 2.31), "steel")
    s.box((0.14, -1.1, 2.26), (0.3, -1.03, 2.31), "steel")
    s.lathe((0.15, -1.25, 2.31), [(0.015, 0), (0.05, -0.05)], 6, "eye", "Y", base=False)


def state(t):
    a = 2 * math.pi * t
    quill = 8 * math.sin(4 * a) * math.cos(a)
    parchment = 0.25 * (t % 0.5) * 2
    censer1 = 16 * math.sin(a)
    censer2 = -16 * math.sin(a)
    bob = 0.14 * math.sin(2 * a)
    return a, quill, parchment, censer1, censer2, bob


def animate(objs, sc):
    frames = int(LOOP * 24)
    for f in range(frames + 1):
        a, q, pa, c1, c2, bob = state(f / frames)
        objs["quill_arm"].rotation_euler = (0, 0, math.radians(q))
        objs["parchment"].location = (-1.2 + pa, 0.4, 1.27)
        objs["censer_1"].rotation_euler = (math.radians(c1), 0, 0)
        objs["censer_2"].rotation_euler = (math.radians(c2), 0, 0)
        objs["servo_skull"].location = (0, 0, 2.3 + bob)
        objs["servo_skull"].rotation_euler = (0, 0, a)
        for n, p in (("quill_arm", "rotation_euler"), ("parchment", "location"), ("censer_1", "rotation_euler"), ("censer_2", "rotation_euler"),
                     ("servo_skull", "location"), ("servo_skull", "rotation_euler")):
            objs[n].keyframe_insert(p, frame=f + 1)
    sc.frame_set(1)


def tracks():
    steps = 64
    tr = {k: {} for k in ("q", "p", "c1", "c2", "b")}
    for i in range(steps + 1):
        t = i / steps
        a, q, pa, c1, c2, bob = state(t)
        key = f"{LOOP * t:.4f}"
        tr["q"][key] = [0, round(-q, 3), 0]           # поворот вокруг Z Blender = -Y анимации
        tr["p"][key] = [round(pa * 16, 3), 0, 0]
        tr["c1"][key] = [round(c1, 3), 0, 0]
        tr["c2"][key] = [round(c2, 3), 0, 0]
        tr["b"][key] = [0, round(bob * 16, 3), 0]
    orbit = {f"{LOOP * i / 8:.4f}": [0, -45.0 * i, 0] for i in range(9)}
    return {"quill_arm": {"rotation": tr["q"]}, "parchment": {"position": tr["p"]}, "censer_1": {"rotation": tr["c1"]},
            "censer_2": {"rotation": tr["c2"]}, "servo_skull": {"position": tr["b"], "rotation": orbit}}, LOOP


m = Machine("scriptorium")
frame(m)
moving(m)
sc, tris = m.build("WB_Scriptorium")
light_scene(sc, int(LOOP * 24))
animate(m.objects, sc)
print("костей:", len(m.objects), "треугольников:", tris)
