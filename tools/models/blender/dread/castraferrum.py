"""Концепт 1: дредноут-саркофаг «Кастраферрум», исходник references/models3d/ultramarines-dreadnought. Правая рука — штурмовая пушка, левая — силовой кулак."""
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender/dread"
exec(open(os.path.join(_HERE, "dread_kit.py"), encoding="utf-8").read())
exec(open(os.path.join(_HERE, "gait.py"), encoding="utf-8").read())

SRC = os.path.join(REFS, "ultramarines-dreadnought")
CX, CY, GROUND, RAW_H = 19.3, 14.7, -2.79, 34.4
S = 3.6 / RAW_H


def game(v):
    out = (v - np.array([CX, CY, GROUND])) * S
    return out


def R(x, y, z):
    """Точка в координатах исходника -> игровые."""
    return ((x - CX) * S, (y - CY) * S, (z - GROUND) * S)


def slab_center(verts, mask):
    return tuple(verts[mask].mean(axis=0))


c = Concept("dread_castraferrum", 3.6)
m = {n: i for i, n in enumerate(MAT_NAMES)}

# ---- ноги: сначала грузим, из тонких срезов берём точки вращения
lv, lt = load_stl(os.path.join(SRC, "Legs.stl"))
lg = game(lv)


def zr(a, b):
    return ((a - GROUND) * S, (b - GROUND) * S)


piv = {}
for side, sign in (("l", 1), ("r", -1)):
    outer = lg[:, 0] * sign > 0.42
    for key, (a, b) in (("thigh", zr(12.5, 14.5)), ("shin", zr(8.8, 10.4)), ("foot", zr(0.0, 1.6))):
        mask = outer & (lg[:, 2] > a) & (lg[:, 2] < b)
        piv[key + "_" + side] = slab_center(lg, mask)

BONES = ["root", "pelvis", "torso", "thigh_l", "shin_l", "foot_l", "thigh_r", "shin_r", "foot_r", "arm_l", "fist_l", "arm_r", "barrels", "arm_hose", "claw_0", "claw_1", "claw_2", "claw_3"]
IDX = {n: i for i, n in enumerate(BONES)}
c.bone("root", None, R(CX, CY, 14), 1)
c.bone("pelvis", "root", R(CX, CY, 13), 260)
c.bone("torso", "root", R(CX, CY + 1, 15), 2300)
for s in "lr":
    c.bone("thigh_" + s, "pelvis", piv["thigh_" + s], 260)
    c.bone("shin_" + s, "thigh_" + s, piv["shin_" + s], 420)
    c.bone("foot_" + s, "shin_" + s, piv["foot_" + s], 300)
c.bone("arm_l", "torso", R(33.5, 15.5, 24), 500)
c.bone("fist_l", "arm_l", R(35, 12.5, 15), 700)
c.bone("arm_r", "torso", R(7.5, 15, 23), 800)
c.bone("barrels", "arm_r", R(5.6, 6, 22.5), 240)
# шланг от плеча к запястью: своя кость, иначе половинки расходятся при движении кисти
c.bone("arm_hose", "arm_l", (1.8, 0.82, 2.2), 150)
# пальцы клешни вокруг оси кисти, по диагоналям
CLAW_AXIS = (1.575, 1.3)
CLAW_DIRS = ((0.7, 0.7), (-0.7, 0.7), (-0.7, -0.7), (0.7, -0.7))
for i, (dx, dz) in enumerate(CLAW_DIRS):
    c.bone(f"claw_{i}", "fist_l", (CLAW_AXIS[0] + dx * 0.28, -0.72, CLAW_AXIS[1] + dz * 0.28), 170)


def legs_bone(ce, size):
    out = np.zeros(len(ce), dtype=np.int64)
    x, z = ce[:, 0], ce[:, 2]
    z0 = zr(0.5, 9.5)
    for sign, s in ((1, "l"), (-1, "r")):
        side = x * sign > 0
        out[side & (z > z0[1])] = IDX["thigh_" + s]
        out[side & (z > z0[0]) & (z <= z0[1])] = IDX["shin_" + s]
        out[side & (z <= z0[0])] = IDX["foot_" + s]
    out[(np.abs(x) < 0.42) & (z > zr(7, 8)[0])] = IDX["pelvis"]
    return out


def legs_mat(ce, size):
    out = np.full(len(ce), m["dark"], dtype=np.int64)
    z = ce[:, 2]
    out[(z > zr(1.5, 8.6)[0]) & (z < zr(1.5, 8.6)[1])] = m["blue"]           # броня голени
    out[z <= zr(0.4, 1)[0]] = m["blue"]                                        # стопы
    out[size < 0.32] = m["brass"]
    out[(size < 0.9) & (size >= 0.32)] = m["steel"]
    return out


c.add_part(lg, lt, legs_bone, legs_mat)

# ---- корпус
v, t = load_stl(os.path.join(SRC, "Body.stl"))


def body_mat(ce, size):
    out = np.full(len(ce), m["blue"], dtype=np.int64)
    x, y, z = ce[:, 0], ce[:, 1], ce[:, 2]
    out[(np.abs(x) < 0.62) & (y < -0.25) & (z > 1.55)] = m["gold"]               # рама саркофага
    out[(np.abs(x) < 0.34) & (y < -0.25) & (z > 1.85)] = m["bone"]               # сам саркофаг
    out[(np.abs(x) < 0.62) & (y < -0.25) & (z <= 1.55)] = m["dark"]
    out[size < 0.25] = m["gold"]
    out[(size >= 0.25) & (size < 0.8)] = m["steel"]
    out[(z < 1.75)] = np.where(out[(z < 1.75)] == m["blue"], m["dark"], out[(z < 1.75)])
    return out


c.add_part(game(v), t, lambda ce, size: np.full(len(ce), IDX["torso"], dtype=np.int64), body_mat)

# ---- левая рука: плечо и кулак
v, t = load_stl(os.path.join(SRC, "Hend L.stl"))
split = (18 - GROUND) * S


HOSE = np.array([(0.82, 2.2), (0.75, 1.7), (0.55, 1.4), (0.3, 1.2), (0.1, 1.07), (-0.1, 0.95), (-0.5, 0.8)])


def hose_mask(ce):
    """Грани шланга: близко к его ломаной в плоскости (y, z), снаружи кисти."""
    p = ce[:, 1:3]
    best = np.full(len(ce), 9.0)
    for a0, a1 in zip(HOSE, HOSE[1:]):
        d = a1 - a0
        k = np.clip(((p - a0) @ d) / (d @ d), 0, 1)
        best = np.minimum(best, np.linalg.norm(p - (a0 + k[:, None] * d), axis=1))
    return (best < 0.15) & (ce[:, 1] > -0.55)


def claw_index(ce):
    """Номер пальца или -1: впереди барабана и в стороне от оси."""
    dx, dz = ce[:, 0] - CLAW_AXIS[0], ce[:, 2] - CLAW_AXIS[1]
    out = np.full(len(ce), -1, dtype=np.int64)
    ring = (ce[:, 1] < -0.72) & (np.hypot(dx, dz) > 0.16)
    quad = np.where(dz >= 0, np.where(dx >= 0, 0, 1), np.where(dx < 0, 2, 3))
    out[ring] = quad[ring]
    return out


def arm_l_bone(ce, size):
    out = np.where(ce[:, 2] > split, IDX["arm_l"], IDX["fist_l"])
    out[hose_mask(ce)] = IDX["arm_hose"]
    claw = claw_index(ce)
    for i in range(4):
        out[claw == i] = IDX[f"claw_{i}"]
    return out


def arm_l_mat(ce, size):
    out = np.full(len(ce), m["blue"], dtype=np.int64)
    out[ce[:, 2] > split] = m["dark"]
    out[size < 0.3] = m["gold"]
    out[(size >= 0.3) & (size < 1.1)] = m["rubber"]
    out[hose_mask(ce)] = m["rubber"]
    out[claw_index(ce) >= 0] = m["steel"]
    return out


c.add_part(game(v), t, arm_l_bone, arm_l_mat)

# ---- правая рука: штурмовая пушка
v, t = load_stl(os.path.join(SRC, "Hend R.stl"))
barrel_y = (5.4 - CY) * S


def arm_r_bone(ce, size):
    return np.where(ce[:, 1] < barrel_y, IDX["barrels"], IDX["arm_r"])


def arm_r_mat(ce, size):
    out = np.full(len(ce), m["dark"], dtype=np.int64)
    out[ce[:, 1] < barrel_y] = m["steel"]
    out[size < 0.3] = m["brass"]
    return out


c.add_part(game(v), t, arm_r_bone, arm_r_mat)

sc = c.build()
legs = Legs(c)
ANIMS = animations(legs, tracks_from)
print("скорость при нормальном клипе, блоков в секунду: ходьба", round(WALK_SPEED, 3), "бег", round(RUN_SPEED, 3))
preview(c, walk(legs), CYCLE)
