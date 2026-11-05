"""
Основа Астартес: общий макет силовой брони, от которого пойдут легионы и игрок. Исходник — набор Retributor (references/models3d/armor), прямые ноги Legs_6, рука разгибается в рабочее положение.
Запуск внутри Blender. Потом: facet_export(c, prebuilt=stack_model(c, PIECES, BOXES), palette=PALETTE, decals=DECALS, tracks=ANIMS, fine=("head",), levels=CRISP_LEVELS, edge_light=1, pixel=1/64, grain=0.012, dead=0.007, relief=0.008).
Легион меняется таблицей LIVERY: форма общая, цвета — цепочка материалов ниже.
"""
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "dread", "dread_kit.py"), encoding="utf-8").read())
exec(open(os.path.join(_HERE, "astartes", "biped_gait.py"), encoding="utf-8").read())
exec(open(os.path.join(_HERE, "astartes", "voxel_kit.py"), encoding="utf-8").read())

SRC = os.path.join(REFS, "armor", "Retributor_Astartes")
HEIGHT = 2.2
RAW_H = 43.54
S = HEIGHT / RAW_H

# ---- цвета легиона: первичный цвет, отделка, вторичный цвет (Ультрамарины, как у дредноута)
COLORS["primary"] = ((0.01, 0.036, 0.17), 0.16)
COLORS["trim"] = ((0.42, 0.22, 0.035), 0.3)
COLORS["lens"] = ((0.75, 0.02, 0.015), 0.0)
MAT_NAMES[:] = list(COLORS)
m = {n: i for i, n in enumerate(MAT_NAMES)}


def G(x, y, z):
    return (x * S, y * S, z * S)


def to_game(v, offset=(0, 0, 0)):
    return (v + np.array(offset)) * S


def mirror(v, t):
    w = v.copy()
    w[:, 0] = -w[:, 0]
    return w, t[:, ::-1]


c = Concept("astartes", HEIGHT)
c.voxel = 0.0045

# ---- кости. Точки вращения в координатах сборки (ноги исходника), левая сторона +X
ARM_X, ARM_Y = 8.9, 1.0
SHOULDER_Z, ELBOW_Z, WRIST_Z = 30.3, 24.8, 16.0
c.bone("root", None, G(0, 0.3, 21), 1)
c.bone("pelvis", "root", G(0, 0.3, 21), 450)
c.bone("abdomen", "pelvis", G(0, 0.3, 24.3), 450)
c.bone("chest", "abdomen", G(0, 0.6, 28.4), 1200)
c.bone("head", "chest", G(0, 0.8, 37.0), 1100)
c.bone("backpack", "chest", G(0, 5.2, 33.5), 650)
HIP = (3.5, 0.3, 19.6)
KNEE = (4.6, -1.3, 12.6)
ANKLE = (5.0, 0.6, 3.0)
for s, k in (("l", 1), ("r", -1)):
    c.bone("thigh_" + s, "pelvis", G(HIP[0] * k, HIP[1], HIP[2]), 320)
    c.bone("shin_" + s, "thigh_" + s, G(KNEE[0] * k, KNEE[1], KNEE[2]), 360)
    c.bone("foot_" + s, "shin_" + s, G(ANKLE[0] * k, ANKLE[1], ANKLE[2]), 260)
    c.bone("tasset_" + s, "pelvis", G(5.5 * k, 0.2, 24.0), 50)
    c.bone("pad_" + s, "chest", G(11.0 * k, 1.0, 33.5), 180)
    c.bone("arm_" + s, "chest", G(ARM_X * k, ARM_Y, SHOULDER_Z), 200)
    c.bone("forearm_" + s, "arm_" + s, G(ARM_X * k, ARM_Y, ELBOW_Z), 220)
    c.bone("hand_" + s, "forearm_" + s, G(ARM_X * k, ARM_Y, WRIST_Z), 180)
    c.bone("fingers_" + s, "hand_" + s, G(ARM_X * k, 0.0, 13.2), 180)
    c.bone("thumb_" + s, "hand_" + s, G(ARM_X * k, -1.2, 14.8), 50)
c.bone("seal_thigh", "thigh_l", G(4.4, -5.0, 18.4), 130)
IDX = {n: i for i, n in enumerate(c.bones)}


def const_bone(name):
    return lambda ce, size: np.full(len(ce), IDX[name], dtype=np.int64)


# ---- ноги. Кости режут броню по настоящим стыкам: щитки бедра идут отдельно, чтобы не лезть в таз при шаге
lv, lt = load_stl(os.path.join(SRC, "Legs", "Legs_6_RESIZED.stl"))


def _leg_tree(k, s):
    """Срезы идут по стыкам брони. k = 1 для левой ноги (+X), -1 для правой. Плоскости заданы точками сборки, поэтому читаются прямо по чертежу."""
    # стопа: срез от подъёма спереди вниз к пятке
    foot = cut(G(0, 0, 3.6), (0, 2.8, 8), "shin_" + s, "foot_" + s)
    # щиток снаружи бедра, только на бедре
    upper = cut(G(k * 6.1, 0, 21), (k * 1, 0, 0.1), "tasset_" + s, "thigh_" + s)
    # колено: шар сустава остаётся на голени, срез выше спереди и ниже сзади
    knee = cut(G(0, -1.3, 14.2), (0, 2.7, 7), upper, foot)
    # таз: V-образный срез от промежности к верху бедра
    return cut(G(k * 3.5, 0, 19.6), (-k * 0.62, 0, 0.78), "pelvis", knee)

LEG_TREE = cut((0, 0, 0), (1, 0, 0), _leg_tree(1, "l"), _leg_tree(-1, "r"), cap=False)

def legs_mat(ce, size):
    x, y, z = ce[:, 0] / S, ce[:, 1] / S, ce[:, 2] / S
    ax = np.abs(x)
    out = np.full(len(ce), m["primary"], dtype=np.int64)
    out[z < 1.1] = m["dark"]                                                  # подошва
    out[(z > 12.4) & (z < 15.4) & (y > 1.2)] = m["rubber"]                    # гибкая часть под коленом
    out[(z > 21.6) & (z < 24.2) & (np.abs(y) < 3.5) & (ax > 5.0)] = m["dark"]
    out[(ax < 1.55 + (z - 15.0) * 0.1) & (z > 15.5) & (z < 20) & (y < -1.0)] = m["dark"]    # пах
    return out

c.add_part(to_game(lv), lt, LEG_TREE, legs_mat, max_edge=0.012)

# ---- торс: нижняя часть (рёбра и пояс) и нагрудник
tv, tt = load_stl(os.path.join(SRC, "Body", "Torso", "Torso.stl"))
TORSO_OFFSET = (-9.15, -1.45, 0)


TORSO_TREE = cut(G(0, 0, 28.6), (0, 0, 1), "chest", "abdomen")


def relief(ce, region, thresh=0.2):
    """Выступающий рельеф (череп, знак) на выпуклой плите: к передней поверхности подгоняем гладкую чашу, что выше неё на thresh, то и рельеф. Выбросы отсекаем в два прохода."""
    x, y, z = ce[:, 0] / S, ce[:, 1] / S, ce[:, 2] / S
    x0, x1, z0, z1 = region
    inside = (x > x0) & (x < x1) & (z > z0) & (z < z1)
    u, w = (x - (x0 + x1) / 2), (z - (z0 + z1) / 2)
    basis = np.c_[np.ones(len(u)), u, w, u * u, u * w, w * w]
    use = inside & (y < np.median(y[inside]) + 0.6)
    for _ in range(3):
        coef, *_r = np.linalg.lstsq(basis[use], y[use], rcond=None)
        res = y - basis @ coef
        use = inside & (np.abs(res) < 0.15)
    return inside & (res < -thresh)

def torso_mat(ce, size):
    x, y, z = ce[:, 0] / S, ce[:, 1] / S, ce[:, 2] / S
    out = np.full(len(ce), m["primary"], dtype=np.int64)
    out[z < 28.6] = m["rubber"]                                               # рёбра и шланги живота
    out[(z < 26.0)] = m["dark"]                                               # пояс
    out[(z < 26.5) & (np.hypot(x, z - 24.7) < 2.2) & (y < -2.0)] = m["trim"]  # пряжка
    out[(z > 35.4)] = m["dark"]                                               # горжет
    out[(y > 6.6) & (z < 28.6)] = m["dark"]
    return out

c.add_part(to_game(tv, TORSO_OFFSET), tt, TORSO_TREE, torso_mat, max_edge=0.012)

# ---- ранец
bv, bt = load_stl(os.path.join(SRC, "Body", "Torso", "backpack.stl"))


def pack_mat(ce, size):
    x, y, z = ce[:, 0] / S, ce[:, 1] / S, ce[:, 2] / S
    out = np.full(len(ce), m["primary"], dtype=np.int64)
    out[(size < 0.26) & (np.abs(x) < 2.6) & (y > 8)] = m["bone"]               # череп — отдельный кусок исходника
    out[(z > 38.8)] = m["dark"]
    return out

c.add_part(to_game(bv, TORSO_OFFSET), bt, const_bone("backpack"), pack_mat, max_edge=0.012)

# ---- шлем
hv, ht = load_stl(os.path.join(SRC, "Helmet", "Tactical Helm.stl"))
HELM_OFFSET = (0, 0.7, 39.0)


def helm_mat(ce, size):
    x, y, z = ce[:, 0] / S, (ce[:, 1] / S - 0.7), (ce[:, 2] / S - 39.0)
    ax = np.abs(x)
    raw = size / S                                                            # диагональ отдельного куска в единицах исходника: детали шлема — отдельные куски
    out = np.full(len(ce), m["primary"], dtype=np.int64)
    out[z < -2.0] = m["dark"]                                                 # шейное кольцо
    out[np.abs(raw - 4.75) < 0.4] = m["lens"]                                 # линзы
    out[np.abs(raw - 2.75) < 0.2] = m["rubber"]                               # фильтры
    out[np.abs(raw - 1.8) < 0.3] = m["steel"]
    out[(np.abs(raw - 3.25) < 0.25)] = m["steel"]                             # решётка и вокс-блоки
    return out

c.add_part(to_game(hv, HELM_OFFSET), ht, const_bone("head"), helm_mat, voxel=0.004, max_edge=0.01)

# ---- рука: разгибаем вниз, правая — зеркало левой
av, at = load_stl(os.path.join(SRC, "Arm", "Left arm lowered.stl"))
_ax = Vector((-0.02, 0.81, 0.59))
_sh = Vector((86.29, -2.64, 27.45)) + _ax * 8.7
ARM_M = Matrix.Translation((5.95, ARM_Y, SHOULDER_Z)) @ Matrix.Rotation(math.radians(53.9), 4, "X") @ Matrix.Translation(-Vector((83.55, _sh.y, _sh.z)))
av = (np.c_[av, np.ones(len(av))] @ np.array(ARM_M).T)[:, :3]


def arm_tree(s, k):
    hand = cut(G(0, 0, 13.2), (0, 0, 1), cut(G(0, -1.2, 15.2), (0, -1, -0.15), "thumb_" + s, "hand_" + s), "fingers_" + s)
    return cut(G(0, 0, ELBOW_Z), (0, 0, 1), "arm_" + s, cut(G(0, 0, WRIST_Z), (0, 0, 1), "forearm_" + s, hand))

def arm_mat(ce, size):
    raw = size / S                                                            # рука в исходнике собрана из отдельных кусков, по ним и красим: кромка без зубцов
    out = np.full(len(ce), m["primary"], dtype=np.int64)
    out[np.abs(raw - 6.1) < 0.25] = m["rubber"]                               # локтевой сгиб
    out[np.abs(raw - 6.7) < 0.25] = m["trim"]                                 # манжета запястья
    return out

c.add_part(to_game(av), at, arm_tree("l", 1), arm_mat, voxel=0.0035, max_edge=0.012)
_mv, _mt = mirror(av, at)
c.add_part(to_game(_mv), _mt, arm_tree("r", -1), arm_mat, voxel=0.0035, max_edge=0.012)

# ---- наплечники. Плита чистая: на ней потом знак легиона и номер отделения
pv, pt = load_stl(os.path.join(SRC, "Shoulder", "PRIMARIS BLANK SHOULDER PAD.stl"))
PAD_M = Matrix.Translation((10.2, 1.0, 27.6)) @ Matrix.Rotation(math.radians(90), 4, "Z")
_pv = (np.c_[pv, np.ones(len(pv))] @ np.array(PAD_M).T)[:, :3]


def pad_mat(ce, size):
    x, z = np.abs(ce[:, 0]) / S, ce[:, 2] / S
    out = np.full(len(ce), m["primary"], dtype=np.int64)
    out[(z < 28.5) | (x < 8.75)] = m["trim"]                                  # нижний край и край вокруг плеча
    return out

c.add_part(to_game(_pv), pt, const_bone("pad_l"), pad_mat, max_edge=0.012)
_mv, _mt = mirror(_pv, pt)
c.add_part(to_game(_mv), _mt, const_bone("pad_r"), pad_mat, max_edge=0.012)

# ---- печати чистоты: висят на своих костях и качаются от движения
sv, st = load_stl(os.path.join(SRC, "Belt Accessories", "Purity seal.stl"))
sv = sv - np.array(((sv[:, 0].min() + sv[:, 0].max()) / 2, (sv[:, 1].min() + sv[:, 1].max()) / 2, sv[:, 2].max()))


def seal_mat(ce, size):
    z = ce[:, 2] / S
    top = z.max()
    out = np.full(len(ce), m["parchment"], dtype=np.int64)
    out[z > top - 2.3] = m["red"]                                             # восковая печать сверху
    return out


for _bone, _at, _scale in (("seal_thigh", (4.4, -5.0, 18.5), 0.95),):
    # печать толще исходника: иначе тонкая лента рассыпается на блоки
    c.add_part((sv * np.array((_scale * 1.05, _scale * 1.8, _scale * 0.7)) + np.array(_at)) * S, st, const_bone(_bone), seal_mat, voxel=0.0025, max_edge=0.01)

# ---- мелкие детали ящиками: читаются в блочном виде и работают на силуэт. (кость, центр, размер, материал) в координатах сборки
c.bone("antenna", "backpack", G(-5.85, 6.75, 40.2), 40)
IDX = {n: i for i, n in enumerate(c.bones)}
DETAILS = [
    ("pelvis", (6.1, -2.7, 22.8), (2.2, 1.6, 2.7), "dark"), ("pelvis", (6.1, -2.7, 22.8), (1.0, 1.8, 0.6), "brass"),       # подсумки на поясе
    ("pelvis", (3.2, -4.3, 22.6), (1.7, 1.2, 2.2), "dark"), ("pelvis", (3.2, -4.4, 22.8), (0.8, 1.2, 0.5), "brass"),
    ("pelvis", (-6.1, -2.7, 22.8), (2.2, 1.6, 2.7), "dark"), ("pelvis", (-6.1, -2.7, 22.8), (1.0, 1.8, 0.6), "brass"),
    ("pelvis", (-3.2, -4.3, 22.6), (1.7, 1.2, 2.2), "dark"), ("pelvis", (-3.2, -4.4, 22.8), (0.8, 1.2, 0.5), "brass"),
    ("pelvis", (0, 4.6, 22.9), (3.4, 1.4, 2.0), "dark"),                                                                    # сзади на поясе
    ("thigh_r", (-7.1, -0.2, 17.0), (1.4, 3.0, 4.4), "dark"), ("thigh_r", (-7.5, -0.2, 18.0), (0.8, 3.2, 0.8), "brass"),    # кобура болт-пистолета
    ("thigh_r", (-7.2, -0.2, 19.6), (1.0, 1.4, 1.5), "black"),                                                               # рукоять
    ("antenna", (-5.85, 6.75, 42.0), (0.5, 0.5, 10.0), "steel"),                                                              # вокс-антенна
    ("forearm_l", (11.8, 1.0, 21.8), (0.7, 3.4, 2.6), "steel"), ("forearm_l", (12.2, 1.0, 21.8), (0.4, 1.8, 1.0), "lens"),   # ауспик на предплечье
]
for _bone, _c, _s, _mat in DETAILS:
    _bv, _bt = box_mesh(_c, _s)
    _idx = m[_mat]
    c.add_part(_bv * S, _bt, const_bone(_bone), (lambda i: lambda ce, size: np.full(len(ce), i, dtype=np.int64))(_idx), max_edge=0.01, low=False)

sc = c.build(min_island=0.03, cap=True, hi_limit=5000000)
BUILD = Build()
legs = Legs(c)
ANIMS = animations(legs, BUILD, tracks_from)
for _clip in ANIMS.values():
    _clip["bones"] = {k: v for k, v in _clip["bones"].items() if k in c.bones}
print("скорость клипов, блоков в секунду: шаг", round(BUILD.walk_speed, 3), "бег", round(BUILD.run_speed, 3))
preview(c, walk(legs, BUILD), BUILD.cycle)


# ---- рисунки по броне, пиксель в пиксель. Легион меняется здесь и в цветах первичного материала
GOLD = {"X": "trim", "H": "bone"}
AQUILA = (
    "XX.........H.........XX",
    "XXXX......HHH......XXXX",
    ".XXXXX...HHHHH...XXXXX.",
    "..XXXXXX.HHHHH.XXXXXX..",
    "...XXXXXXXHHHXXXXXXX...",
    "....XXXXXXHHHXXXXXX....",
    ".....XXX.XXXXX.XXX.....",
    "......X...XXX...X......",
    "...........X...........",
)
OMEGA = (
    "XXXXX...XXXXX",
    "XXXXX...XXXXX",
    "..XXX...XXX..",
    "..XXX...XXX..",
    ".XXX.....XXX.",
    ".XXX.....XXX.",
    ".XXX.....XXX.",
    "..XXX...XXX..",
    "...XXXXXXX...",
    "....XXXXX....",
)
ARROW = (
    "....XX....",
    "...XXXX...",
    "..XXXXXX..",
    ".XXXXXXXX.",
    "XXX.XX.XXX",
    "XX..XX..XX",
    "....XX....",
    "....XX....",
    "....XX....",
)
WHITE = {"X": "bone"}
EYES = (
    "LLLLL...LLLLL",
    ".LLLLL.LLLLL.",
    "..LLL...LLL..",
)
GRILLE = (
    "SDSDSDS",
    "SDSDSDS",
    "SDSDSDS",
    "SDSDSDS",
    ".SDSDS.",
)
DECALS = [
    Decal(["chest"], "y", -1, G(0, 0, 33.0)[0:1] + G(0, 0, 33.0)[2:], AQUILA, GOLD, pixel=1 / 66),
    Decal(["pad_l"], "x", 1, (1.0 * S, 31.5 * S), OMEGA, WHITE, pixel=1 / 66),
    Decal(["pad_r"], "x", -1, (1.0 * S, 31.5 * S), ARROW, WHITE, pixel=1 / 66),
    Decal(["head"], "y", -1, (0, 40.3 * S), EYES, {"L": "lens"}, pixel=1 / 66),
    Decal(["head"], "y", -1, (0, 38.2 * S), GRILLE, {"S": "steel", "D": "black"}, pixel=1 / 66),
]
PALETTE = {"primary": (42, 74, 160)}

# ---- простая форма: что из чего собрано. Фильтры — по точкам оболочки в координатах сборки
def R(fn):
    return lambda p: fn(p[:, 0] / S, p[:, 1] / S, p[:, 2] / S)


PIECES = {
    "foot_l": ((1, None),), "foot_r": ((1, None),),
    "backpack": (
        (2, R(lambda x, y, z: (np.abs(x) < 5.6) & (z < 38.8))),
        (0, R(lambda x, y, z: (np.abs(x) < 5.6) & (z >= 38.8))),
        (1, R(lambda x, y, z: (x >= 5.6) & (z > 32.0))),
        (1, R(lambda x, y, z: (x <= -5.6) & (z > 32.0))),
    ),
    "head": ((2, R(lambda x, y, z: np.abs(x) < 3.05)),),
    "seal_thigh": ((2, R(lambda x, y, z: z > 16.6)), (2, R(lambda x, y, z: z <= 16.6))),
}
BOXES = [(b_, (c_[0] * S, c_[1] * S, c_[2] * S), (s_[0] * S, s_[1] * S, s_[2] * S)) for b_, c_, s_, _m in DETAILS]
for _sx in (1, -1):
    BOXES += [
        ("head", (_sx * 3.45 * S, 1.3 * S, 39.0 * S), (1.0 * S, 2.3 * S, 2.3 * S)),          # вокс-блоки
        ("head", (_sx * 2.1 * S, -2.2 * S, 37.6 * S), (1.3 * S, 1.3 * S, 1.0 * S)),          # фильтры
        ("chest", (_sx * 5.3 * S, 0.9 * S, 35.6 * S), (2.6 * S, 4.6 * S, 0.9 * S)),          # плечевые накладки
        ("thigh_l" if _sx > 0 else "thigh_r", (_sx * 7.0 * S, -3.3 * S, 15.0 * S), (0.5 * S, 0.5 * S, 0.5 * S)),   # заклёпки бедра
        ("shin_l" if _sx > 0 else "shin_r", (_sx * 5.0 * S, -4.6 * S, 8.0 * S), (3.4 * S, 0.5 * S, 0.9 * S)),      # накладка голени
        ("foot_l" if _sx > 0 else "foot_r", (_sx * 5.2 * S, -5.6 * S, 1.3 * S), (4.0 * S, 0.6 * S, 0.9 * S)),      # носок сапога
    ]
BOXES += [("head", (0, -3.05 * S, 38.0 * S), (2.1 * S, 0.6 * S, 2.0 * S))]                    # решётка вперёд маски