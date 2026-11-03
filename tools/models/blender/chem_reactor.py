"""
Химический реактор (chem_reactor): 3×3×4. Открытая клеть с кипящей кислотой и мешалкой, сзади баллоны реагентов,
сбоку змеевик конденсатора, спереди капает готовая кислота в приёмник.
"""
import math
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "kit.py"), encoding="utf-8").read())

LOOP, STEPS = 2.4, 48
CX, CY = -0.18, -0.08                # ось клети
Z0, Z1 = 0.78, 2.72                  # низ и верх клети
LEVEL = 1.45                         # уровень кислоты в покое
SPOUT = (0.98, -1.08, 1.02)          # откуда капает
POT_Z = 0.62


def frame(m):
    f = m.bone("frame")
    f.plinth(-1.48, -1.48, 1.48, 1.48)
    # ---- чаша и клеть
    f.lathe((CX, CY, 0.3), [(0.82, 0), (0.82, 0.14), (0.7, 0.2), (0.7, Z0 - 0.3)], 18, "dark", base=False)
    f.ring((CX, CY, 0.46), 0.78, 0.88, 0.08, 18, "brass", "Z")
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        x, y = CX + 0.66 * math.cos(a), CY + 0.66 * math.sin(a)
        f.lathe((x, y, Z0), [(0.03, 0), (0.03, Z1 - Z0)], 5, "steel", base=False)
    for z in (Z0 + 0.62, Z0 + 1.3):
        f.ring((CX, CY, z), 0.63, 0.7, 0.05, 18, "brass", "Z")
    f.lathe((CX, CY, Z1), [(0.72, 0), (0.72, 0.1), (0.48, 0.3), (0.2, 0.42), (0.2, 0.48)], 18, "hull", base=False)
    for k in range(8):
        a = k * math.pi / 4
        f.bolt((CX + 0.68 * math.cos(a), CY + 0.68 * math.sin(a), Z1 + 0.1), "Z", 0.028, 0.018, "steel")
    # ---- мотор мешалки над крышкой
    f.lathe((CX, CY, Z1 + 0.48), [(0.26, 0), (0.26, 0.3), (0.19, 0.36), (0.1, 0.4)], 12, "rust", base=False)
    for k in range(3):
        f.ring((CX, CY, Z1 + 0.56 + k * 0.08), 0.26, 0.285, 0.03, 12, "dark", "Z")
    # ---- баллоны реагентов: серный (жёлтый пояс), кислородный (красный)
    for x, band in ((-1.03, "sulfur"), (1.03, "red")):
        f.tank((x, 1.0, 0.3), 0.36, 2.25, 12, "steel" if band == "red" else "hull", (0.18, 0.52, 0.86), band_mat=band)
    f.pipe([(-1.03, 1.0, 2.73), (-1.03, 0.9, 3.08), (CX - 0.2, 0.15, 3.18), (CX - 0.1, CY + 0.1, 3.14)], 0.055, 8, "rust")
    f.pipe([(1.03, 1.0, 2.73), (1.03, 0.9, 3.28), (CX + 0.2, 0.15, 3.3), (CX + 0.1, CY + 0.1, 3.16)], 0.055, 8, "rust")
    f.box((-0.72, 0.72, 0.3), (0.72, 1.3, 2.05), "hull", bevel=0.05)
    f.box((-0.74, 0.7, 1.56), (0.74, 1.32, 1.62), "brass")
    f.ring((0, 0.7, 1.08), 0.2, 0.3, 0.04, 14, "dark", "Y")
    # ---- змеевик конденсатора на правой стороне
    coil = []
    for i in range(40):
        a = i * math.pi / 5
        coil.append((1.0 + 0.3 * math.cos(a), -0.4 + 0.3 * math.sin(a), 1.02 + i * 0.038))
    f.pipe(coil, 0.032, 5, "brass")
    f.lathe((1.0, -0.4, 0.3), [(0.14, 0), (0.14, 2.38)], 8, "dark", base=False)
    f.pipe([coil[-1], (1.0, -0.15, 2.72), (CX + 0.72, CY + 0.08, 2.9)], 0.05, 6, "rust")
    f.pipe([coil[0], (1.0, -0.82, 1.08), SPOUT], 0.05, 6, "rust")
    f.lathe(SPOUT, [(0.07, -0.05), (0.07, 0.02), (0.1, 0.05)], 8, "brass", base=False)
    # ---- приёмник кислоты спереди справа
    f.lathe((SPOUT[0], SPOUT[1], 0.3), [(0.3, 0), (0.33, 0.38), (0.28, 0.38), (0.28, 0.3)], 12, "dark", base=False)
    f.lathe((SPOUT[0], SPOUT[1], POT_Z), [(0.28, 0), (0.28, 0.01)], 12, "acid", base=False)
    # ---- пульт слева: экран, рубильник, манометр, череп
    f.box((-1.42, -1.25, 0.3), (-0.98, -0.2, 1.7), "hull", bevel=0.03)
    f.box((-1.43, -1.1, 0.78), (-1.415, -0.36, 1.46), "screen")
    f.skull(-1.2, -1.15, 1.98, 0.36, augmetic=False)
    f.box((-1.32, -1.25, 1.7), (-1.08, -1.0, 1.8), "dark")
    # ---- вытяжка: две трубы над баллонами
    for x in (-1.05, 1.05):
        f.lathe((x, 0.05, 2.3) if False else (x, 0.42, 0.3), [(0.1, 0), (0.1, 3.1)], 8, "rust", base=False)
        f.lathe((x, 0.42, 3.4), [(0.1, 0), (0.17, 0.08), (0.17, 0.45), (0.1, 0.5)], 8, "dark", base=False)
    for x in (-1.05, 1.05):
        f.box((x - 0.22, 0.34, 3.92), (x + 0.22, 0.5, 3.96), "dark")
    f.seal((CX + 0.3, CY - 0.72, 0.62), "Y", -1)
    f.seal((1.45, -0.5, 0.9), "X", 1)


def moving(m):
    # ---- кислота: столб с дышащей поверхностью
    acid = m.bone("acid", (CX, CY, Z0))
    acid.lathe((CX, CY, Z0), [(0.6, 0), (0.6, LEVEL - Z0)], 16, "acid", base=False)
    # ---- мешалка: вал, лопасти и крестовина; видно над кислотой
    st = m.bone("stir", (CX, CY, Z1))
    st.lathe((CX, CY, 1.05), [(0.045, 0), (0.045, Z1 + 0.5 - 1.05)], 6, "steel", base=False)
    for z, d in ((1.68, 0), (2.28, 45)):
        for k in range(4):
            a = math.radians(d + k * 90)
            st.beam((CX, CY, z), (CX + 0.5 * math.cos(a), CY + 0.5 * math.sin(a), z), 0.17, 0.03, "brass")
    # ---- пузыри над поверхностью
    for i in range(5):
        a = i * 1.26
        x, y = CX + 0.36 * math.cos(a), CY + 0.36 * math.sin(a)
        b = m.bone(f"bubble_{i}", (x, y, LEVEL))
        b.lathe((x, y, LEVEL), [(0, -0.05), (0.05, -0.02), (0.05, 0.02), (0, 0.05)], 6, "acid", cap=False)
    # ---- капля
    d = m.bone("drop", SPOUT)
    d.lathe((SPOUT[0], SPOUT[1], SPOUT[2] - 0.08), [(0, -0.05), (0.03, -0.02), (0.018, 0.02), (0, 0.05)], 6, "acid", cap=False)
    # ---- вентиль и стрелка манометра
    v = m.bone("valve", (-0.5, 0.68, 1.08))
    v.ring((-0.5, 0.68, 1.08), 0.09, 0.13, 0.02, 10, "red", "Y")
    v.beam((-0.62, 0.68, 1.08), (-0.38, 0.68, 1.08), 0.02, 0.02, "red")
    n = m.bone("needle", (0, 0.68, 1.08))
    n.box((-0.006, 0.674, 1.076), (0.17, 0.68, 1.086), "eye")


def pose(t):
    a = 2 * math.pi * t
    p = {
        "stir": {"rot": (0, 0, 360 * 2 * t)},
        "acid": {"scale": (1, 1, 1 + 0.05 * math.sin(4 * a))},
        "valve": {"rot": (0, 30 * math.sin(a), 0)},
        "needle": {"rot": (0, 60 + 14 * math.sin(a) + 5 * math.sin(7 * a), 0)},
    }
    for i in range(5):
        u = (t * 2 + i / 5) % 1
        s = 0.3 + u if u < 0.85 else 0
        p[f"bubble_{i}"] = {"pos": (0, 0, 0.22 * u), "scale": (s, s, s)}
    u = (t * 3) % 1
    fall = SPOUT[2] - 0.08 - POT_Z
    p["drop"] = {"pos": (0, 0, -fall * u * u), "scale": (1, 1, 1) if u < 0.97 else (0, 0, 0)}
    return p


m = Machine("chem_reactor")
frame(m)
moving(m)
sc, tris = m.build("WB_ChemReactor")
light_scene(sc, int(LOOP * 24))
auto_animate(m.objects, sc, pose, LOOP)
tracks = lambda: auto_tracks(pose, LOOP, STEPS)
print("костей:", len(m.objects), "треугольников:", tris)
