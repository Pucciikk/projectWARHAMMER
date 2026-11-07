"""
Основа Астартес: общий макет силовой брони, от которого пойдут легионы и игрок. Исходник — набор Retributor (references/models3d/armor), прямые ноги Legs_6, рука разгибается в рабочее положение.
VARIANT = "thunder_warrior" (задаёт thunder_warrior.py) — Громовой воин на том же теле и скелете: кубическая голова с пиксельным лицом,
открытый шлем с гребнем, очки с красными линзами, бронза с молниями, ткань спереди и сзади, без ранца и печатей.
Запуск внутри Blender. Потом: facet_export(c, prebuilt=stack_model(c, PIECES, BOXES, **STACK), palette=PALETTE, decals=DECALS, tracks=ANIMS, fine=("head",), levels=CRISP_LEVELS, edge_light=1, pixel=1/64, grain=0.012, dead=0.007, relief=0.008).
Легион меняется таблицей LIVERY: форма общая, цвета — цепочка материалов ниже.
"""
import os

VARIANT = globals().get("VARIANT", "astartes")
TW = VARIANT == "thunder_warrior"
GAME_HEIGHT = 2.3 if TW else 2.4          # рост в игре, блоков (решения автора 7.11.2026): модель одна, 2,2 единицы

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "dread", "dread_kit.py"), encoding="utf-8").read())
exec(open(os.path.join(_HERE, "astartes", "biped_gait.py"), encoding="utf-8").read())
exec(open(os.path.join(_HERE, "astartes", "voxel_kit.py"), encoding="utf-8").read())
exec(open(os.path.join(_HERE, "astartes", "biped_motion.py"), encoding="utf-8").read())

SRC = os.path.join(REFS, "armor", "Retributor_Astartes")
HEIGHT = 2.2
RAW_H = 43.54
S = HEIGHT / RAW_H

# ---- цвета легиона: первичный цвет, отделка, вторичный цвет (Ультрамарины, как у дредноута)
COLORS["primary"] = ((0.15, 0.075, 0.022), 0.25) if TW else ((0.01, 0.036, 0.17), 0.16)       # у Громового воина бронза
COLORS["trim"] = ((0.42, 0.22, 0.035), 0.3)
COLORS["lens"] = ((0.75, 0.02, 0.015), 0.0)
COLORS["crimson"] = ((0.12, 0.007, 0.012), 0.2)
COLORS["skin"] = ((0.3, 0.17, 0.11), 0.1)
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


c = Concept(VARIANT, HEIGHT)
c.voxel = 0.0045

# ---- кости. Точки вращения в координатах сборки (ноги исходника), левая сторона +X
ARM_X, ARM_Y = 8.9, 1.0
SHOULDER_Z, ELBOW_Z, SRC_WRIST_Z = 30.3, 24.8, 16.0
# руки в исходнике длинные: пальцы ниже колена. Предплечье сжато по длине до 0,68, кисть до 0,85 — кулак у середины бедра (решение автора 7.11.2026)
FORE_K, HAND_K = 0.68, 0.85
WRIST_Z = ELBOW_Z - (ELBOW_Z - SRC_WRIST_Z) * FORE_K


def arm_z(z):
    """Высота точки руки исходника после укорочения (выше локтя без изменений)."""
    z = np.asarray(z, dtype=np.float64)
    return np.where(z >= ELBOW_Z, z, np.where(z >= SRC_WRIST_Z, ELBOW_Z - (ELBOW_Z - z) * FORE_K, WRIST_Z - (SRC_WRIST_Z - z) * HAND_K))


def arm_z_inv(z):
    z = np.asarray(z, dtype=np.float64)
    return np.where(z >= ELBOW_Z, z, np.where(z >= WRIST_Z, ELBOW_Z - (ELBOW_Z - z) / FORE_K, SRC_WRIST_Z - (WRIST_Z - z) / HAND_K))


def AZ(z):
    return float(arm_z(z))
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
    c.bone("fingers_" + s, "hand_" + s, G(ARM_X * k, 0.0, AZ(13.2)), 180)
    c.bone("thumb_" + s, "hand_" + s, G(ARM_X * k, -1.2, AZ(14.8)), 50)
c.bone("seal_thigh", "thigh_l", G(4.4, -5.0, 18.4), 130)
if TW:
    c.bone("visor", "head", G(0, 0.8, 37.0), 40)                 # красное стекло очков: рисуется только в проходе свечения
    c.bone("tabard_f", "pelvis", G(0, -4.3, 22.6), 60)           # ткань спереди и сзади, качается за бёдрами
    c.bone("tabard_b", "pelvis", G(0, 5.0, 22.8), 60)
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

if not TW:                                                     # у Громовых воинов ранца не было
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

if not TW:                                                     # у Громового воина голова собрана из ящиков ниже
    c.add_part(to_game(hv, HELM_OFFSET), ht, const_bone("head"), helm_mat, voxel=0.004, max_edge=0.01)

# ---- рука: разгибаем вниз, правая — зеркало левой
av, at = load_stl(os.path.join(SRC, "Arm", "Left arm lowered.stl"))
_ax = Vector((-0.02, 0.81, 0.59))
_sh = Vector((86.29, -2.64, 27.45)) + _ax * 8.7
ARM_M = Matrix.Translation((5.95, ARM_Y, SHOULDER_Z)) @ Matrix.Rotation(math.radians(53.9), 4, "X") @ Matrix.Translation(-Vector((83.55, _sh.y, _sh.z)))
av = (np.c_[av, np.ones(len(av))] @ np.array(ARM_M).T)[:, :3]
# цвета руки считаем на исходной длине (они по размеру кусков), потом переносим на укороченную по положению точки
_alab = islands(len(av), at)
_asize = island_size(to_game(av), _alab)[_alab[at[:, 0]]]


def arm_tree(s, k):
    hand = cut(G(0, 0, AZ(13.2)), (0, 0, 1), cut(G(0, -1.2, AZ(15.2)), (0, -1, -0.15), "thumb_" + s, "hand_" + s), "fingers_" + s)
    return cut(G(0, 0, ELBOW_Z), (0, 0, 1), "arm_" + s, cut(G(0, 0, WRIST_Z), (0, 0, 1), "forearm_" + s, hand))

def arm_mat(ce, size):
    raw = size / S                                                            # рука в исходнике собрана из отдельных кусков, по ним и красим: кромка без зубцов
    out = np.full(len(ce), m["primary"], dtype=np.int64)
    out[np.abs(raw - 6.1) < 0.25] = m["rubber"]                               # локтевой сгиб
    out[np.abs(raw - 6.7) < 0.25] = m["trim"]                                 # манжета запястья
    return out

_amat = arm_mat(to_game(av)[at].mean(axis=1), _asize)
_ACELL = 0.35
_ahash = {}
for _p, _m in zip(np.floor(av[at].mean(axis=1) / _ACELL).astype(np.int64), _amat):
    _ahash.setdefault(tuple(_p), _m)


def short_arm_mat(ce, size):
    """Материал точки укороченной руки: возвращаем её на исходную длину и берём цвет ближайшего куска исходника."""
    src = ce / S
    src[:, 0] = np.abs(src[:, 0])
    src[:, 2] = arm_z_inv(src[:, 2])
    out = np.full(len(ce), m["primary"], dtype=np.int64)
    cells = np.floor(src / _ACELL).astype(np.int64)
    for i, (cx, cy, cz) in enumerate(cells):
        for d in ((0, 0, 0), (0, 0, 1), (0, 0, -1), (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)):
            v = _ahash.get((cx + d[0], cy + d[1], cz + d[2]))
            if v is not None:
                out[i] = v
                break
    return out


_sv = av.copy()
_sv[:, 2] = arm_z(_sv[:, 2])
c.add_part(to_game(_sv), at, arm_tree("l", 1), short_arm_mat, voxel=0.0035, max_edge=0.012)
_mv, _mt = mirror(_sv, at)
c.add_part(to_game(_mv), _mt, arm_tree("r", -1), short_arm_mat, voxel=0.0035, max_edge=0.012)

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


for _bone, _at, _scale in () if TW else (("seal_thigh", (4.4, -5.0, 18.5), 0.95),):
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
] + ([] if TW else [
    ("antenna", (-5.85, 6.75, 42.0), (0.5, 0.5, 10.0), "steel"),                                                              # вокс-антенна
    ("forearm_l", (11.8, 1.0, AZ(21.8)), (0.7, 3.4, 2.4), "steel"), ("forearm_l", (12.2, 1.0, AZ(21.8)), (0.4, 1.8, 1.0), "lens"),   # ауспик на предплечье
])
# детали Mk VII: пятый элемент — ось восьмигранной призмы (круглые детали), без него ящик
for _k, _s in ((1, "l"), (-1, "r")):
    DETAILS += [
        ("shin_" + _s, (4.8 * _k, -5.9, 13.9), (4.7, 0.6, 4.9), "black", 1),                   # тень под наколенником: контур
        ("shin_" + _s, (4.8 * _k, -6.6, 13.9), (4.1, 1.4, 4.3), "primary", 1),                 # наколенник
        ("shin_" + _s, (4.8 * _k, -7.4, 13.9), (0.8, 0.5, 3.4), "primary"),                    # ребро наколенника
        ("shin_" + _s, (4.8 * _k, 4.0, 6.4), (2.4, 1.8, 2.6), "dark"),                          # решётка икры
    ] + [("shin_" + _s, (4.8 * _k, 4.95, _z), (2.6, 0.4, 0.35), "steel") for _z in (5.5, 6.4, 7.3)] + [
        ("pelvis", (3.6 * _k, 4.4, 21.8), (1.5, 1.5, 2.0), "dark", 2),                          # фраг-граната
        ("pelvis", (3.6 * _k, 4.4, 23.0), (0.9, 0.9, 0.5), "steel", 2),
        ("abdomen", (3.6 * _k, -1.9, 26.6), (1.0, 1.0, 3.4), "dark", 2),                       # кабель живота
    ] + [("abdomen", (3.6 * _k, -1.9, _z), (1.35, 1.35, 0.4), "steel", 2) for _z in (25.5, 26.6, 27.7)] + ([] if TW else [
        ("backpack", (3.0 * _k, 9.0, 41.4), (2.0, 2.0, 2.2), "steel", 2),                      # сопло ранца
        ("backpack", (3.0 * _k, 9.0, 42.45), (1.2, 1.2, 0.3), "black", 2),
    ])
DETAILS += [] if TW else [
    ("backpack", (0, 8.9, 30.4), (5.0, 1.8, 3.6), "dark"),                                       # решётка сзади на ранце
] + [("backpack", (0, 9.85, _z), (4.6, 0.3, 0.4), "steel") for _z in (29.3, 30.4, 31.5)] + [
    ("pad_r", (-10.5, -3.1, 32.4), (1.8, 0.7, 1.8), "red", 1),                                    # печать чистоты на наплечнике
    ("pad_r", (-10.9, -3.2, 29.6), (0.7, 0.25, 3.2), "parchment"),
    ("pad_r", (-10.1, -3.2, 29.9), (0.6, 0.25, 2.6), "parchment"),
    ("head", (0, 5.4, 37.0), (1.3, 2.2, 1.3), "rubber", 1),                                      # кабель шлема к ранцу
]
DETAILS += [("forearm_r", (-11.0, 1.5, AZ(20.2)), (0.6, 2.8, 3.2), "primary")]                    # накладка предплечья

# ---- Громовой воин: голова-куб как у персонажа Minecraft, открытый шлем с гребнем, очки, ткань
HEAD_C, HEAD_S = (0, 0.6, 40.2), 6.6           # куб головы: центр и ребро, единицы исходника; лицо — сетка 8×8 по передней грани
FACE_Y = HEAD_C[1] - HEAD_S / 2
FACE_PX = HEAD_S / 8
EYE_X, EYE_Z = 1.8, HEAD_C[2] + HEAD_S / 2 - FACE_PX * 3.5       # глаза — четвёртый ряд сверху, столбцы 2–3 и 6–7
if TW:
    _hx = HEAD_S / 2
    DETAILS += [
        ("head", HEAD_C, (HEAD_S, HEAD_S, HEAD_S), "skin"),                                                   # голова
        ("head", (0, HEAD_C[1], HEAD_C[2] + _hx + 0.4), (HEAD_S + 0.6, HEAD_S + 0.6, 0.9), "primary"),        # купол шлема
        ("head", (0, HEAD_C[1] + _hx + 0.35, HEAD_C[2] + 0.2), (HEAD_S + 0.6, 0.8, HEAD_S + 0.2), "primary"), # затылок
        ("head", (0, FACE_Y - 0.25, HEAD_C[2] + _hx - FACE_PX * 1.0), (HEAD_S + 0.8, 0.9, FACE_PX * 1.6), "trim"),  # козырёк над лицом
        ("head", (0, HEAD_C[1], HEAD_C[2] + _hx + 0.95), (1.8, HEAD_S + 0.9, 0.35), "trim"),                  # основание гребня
        # гребень: плюмаж ступенями — выше всего посередине, к затылку спадает
        ("head", (0, HEAD_C[1] - 2.2, HEAD_C[2] + _hx + 2.0), (1.2, 2.4, 2.0), "crimson"),
        ("head", (0, HEAD_C[1] + 0.1, HEAD_C[2] + _hx + 2.6), (1.3, 2.6, 3.2), "crimson"),
        ("head", (0, HEAD_C[1] + 2.4, HEAD_C[2] + _hx + 2.2), (1.2, 2.4, 2.4), "crimson"),
        ("head", (0, HEAD_C[1] + 4.0, HEAD_C[2] + _hx + 1.1), (1.1, 1.2, 1.6), "crimson"),
        ("head", (0, FACE_Y - 0.15, HEAD_C[2] + _hx + 1.2), (1.0, 0.8, 1.6), "trim"),                        # кокарда у гребня
        ("head", (0, -3.5, 36.4), (5.2, 1.0, 0.8), "trim"),                                                  # подбородочный ремень
    ]
    for _k in (1, -1):
        DETAILS += [
            ("head", (_k * (_hx + 0.35), HEAD_C[1] + 0.5, HEAD_C[2] + 0.2), (0.8, HEAD_S - 0.6, HEAD_S + 0.2), "primary"),   # щёки шлема
            ("head", (_k * (_hx + 0.3), FACE_Y + 0.15, HEAD_C[2] - 1.2), (0.95, 1.2, 3.6), "trim"),                          # нащёчники спереди
            ("head", (_k * (_hx + 0.85), HEAD_C[1] + 0.5, EYE_Z), (0.35, HEAD_S - 0.4, 0.75), "black"),                      # ремень очков
            # оправа очков: рамка из четырёх брусков — сквозь неё видны глаза
            ("head", (_k * EYE_X, FACE_Y - 0.3, EYE_Z + 0.78), (2.5, 0.6, 0.34), "brass"),
            ("head", (_k * EYE_X, FACE_Y - 0.3, EYE_Z - 0.78), (2.5, 0.6, 0.34), "brass"),
            ("head", (_k * (EYE_X + 1.08), FACE_Y - 0.3, EYE_Z), (0.34, 0.6, 1.22), "brass"),
            ("head", (_k * (EYE_X - 1.08), FACE_Y - 0.3, EYE_Z), (0.34, 0.6, 1.22), "brass"),
            ("visor", (_k * EYE_X, FACE_Y - 0.42, EYE_Z), (1.84, 0.12, 1.24), "lens"),                                       # красное стекло
        ]
    DETAILS += [("head", (0, FACE_Y - 0.3, EYE_Z), (1.2, 0.5, 0.36), "brass")]                                # перемычка очков
    DETAILS += [
        ("tabard_f", (0, -4.65, 18.3), (5.0, 0.35, 8.2), "crimson"), ("tabard_f", (0, -4.7, 22.3), (5.6, 0.5, 0.8), "trim"),      # передняя пола
        ("tabard_b", (0, 5.45, 18.4), (6.2, 0.35, 8.6), "crimson"), ("tabard_b", (0, 5.5, 22.5), (6.8, 0.5, 0.8), "trim"),        # задняя пола
    ]

for _bone, _c, _s, _mat, *_ax in DETAILS:
    _bv, _bt = prism_mesh(_c, _s, _ax[0]) if _ax else box_mesh(_c, _s)
    _idx = m[_mat]
    c.add_part(_bv * S, _bt, const_bone(_bone), (lambda i: lambda ce, size: np.full(len(ce), i, dtype=np.int64))(_idx), max_edge=0.01, low=False)

sc = c.build(min_island=0.03, cap=True, hi_limit=5000000)
BUILD = Build()
legs = Legs(c)
# движения второго поколения (biped_motion.py): скорости игрока, удар и вздрагивание — наложения на клиенте
ANIMS = motion_clips(legs, tracks_from, tracks_from(death(legs, BUILD), DEATH_LENGTH, 81, False), tracks_from(stasis(legs, BUILD), 1.0, 1, True))
for _clip in ANIMS.values():
    _clip["bones"] = {k: v for k, v in _clip["bones"].items() if k in c.bones}
# все движения, которые играет клиент сам (своя фаза шага, смешивание аллюров, воздух, удар): assets/warpbound/motion/astartes.json
motion_json(os.path.join(ROOT, "src/main/resources/assets/warpbound/motion", VARIANT + ".json"), motion_set(legs, death(legs, BUILD)))
print("скорости аллюров, блоков в секунду:", {k: g.speed for k, g in GAITS.items()}, "ход ступни:", {k: round(g.stride, 3) for k, g in GAITS.items()})
preview(c, with_physics(locomotion(legs, RUN), RUN.cycle, standard_springs()), RUN.cycle)


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
# ---- Громовой воин: молнии и лицо пикселями 8×8, как у персонажа Minecraft (верхние ряды — под козырьком)
BOLT = (
    ".....XXXX.",
    "....XXXX..",
    "...XXXX...",
    "..XXXX....",
    ".XXXXXXXX.",
    "....XXXX..",
    "...XXXX...",
    "..XXX.....",
    ".XX.......",
    "X.........",
)
BOLT_S = (
    "...XXX",
    "..XXX.",
    ".XXXXX",
    "...XX.",
    "..XX..",
    ".X....",
)
FACE = (
    "HHHHHHHH",
    "HHHHHHHH",
    "SBBSSBBS",
    "SWPSSPWS",
    "SSSNNSSS",
    "SSNssNSS",
    "SSMMMMSS",
    "SsSSSSsS",
)
FACE_C = {"H": "hair", "S": "skin", "s": "shadow", "B": "hair", "W": "bone", "P": "black", "N": "shadow", "M": "mouth"}
TW_DECALS = [
    Decal(["head"], "y", -1, (0, HEAD_C[2] * S), FACE, FACE_C, pixel=FACE_PX * S),
    Decal(["chest"], "y", -1, (0, 32.6 * S), BOLT, {"X": "trim"}, pixel=1 / 52),
    Decal(["pad_l"], "x", 1, (1.0 * S, 31.5 * S), BOLT, {"X": "trim"}, pixel=1 / 60),
    Decal(["pad_r"], "x", -1, (1.0 * S, 31.5 * S), BOLT, {"X": "trim"}, pixel=1 / 60, flip=True),
    Decal(["tabard_f"], "y", -1, (0, 18.0 * S), BOLT_S, {"X": "trim"}, pixel=1 / 44),
    Decal(["tabard_b"], "y", 1, (0, 18.0 * S), BOLT_S, {"X": "trim"}, pixel=1 / 44, flip=True),
    Decal(["shin_l"], "y", -1, (4.8 * S, 13.9 * S), BOLT_S, {"X": "trim"}, pixel=1 / 80),
    Decal(["shin_r"], "y", -1, (-4.8 * S, 13.9 * S), BOLT_S, {"X": "trim"}, pixel=1 / 80, flip=True),
]
DECALS = TW_DECALS if TW else [
    Decal(["chest"], "y", -1, G(0, 0, 33.0)[0:1] + G(0, 0, 33.0)[2:], AQUILA, GOLD, pixel=1 / 66),
    Decal(["pad_l"], "x", 1, (1.0 * S, 31.5 * S), OMEGA, WHITE, pixel=1 / 66),
    Decal(["pad_r"], "x", -1, (1.0 * S, 31.5 * S), ARROW, WHITE, pixel=1 / 66),
    Decal(["head"], "y", -1, (0, 40.3 * S), EYES, {"L": "lens"}, pixel=1 / 66),
    Decal(["head"], "y", -1, (0, 38.2 * S), GRILLE, {"S": "steel", "D": "black"}, pixel=1 / 66),
]
PALETTE = {"primary": (124, 78, 40), "trim": (204, 152, 58), "brass": (176, 128, 52), "crimson": (150, 22, 26), "skin": (198, 146, 112),
           "shadow": (160, 108, 82), "hair": (62, 40, 28), "mouth": (110, 52, 44), "lens": (235, 30, 22)} if TW else {"primary": (42, 74, 160)}

# ---- простая форма: что из чего собрано. Фильтры — по точкам оболочки в координатах сборки
def R(fn):
    return lambda p: fn(p[:, 0] / S, p[:, 1] / S, p[:, 2] / S)


# ровные кольца: фаска 18–38 % грани, сглаживание по трём кольцам, концы уже 40 % срезаны торцом, допуск больше пикселя — без клиньев и полос
STACK = dict(tol=0.02, even=((0.18, 0.38), 3, 0.4))

PIECES = {
    "foot_l": ((2, None),), "foot_r": ((2, None),),       # сапог кольцами по вертикали: вдоль ступни носок сходился в клин
    "backpack": (
        (2, R(lambda x, y, z: (np.abs(x) < 5.6) & (z < 38.8))),
        (0, R(lambda x, y, z: (np.abs(x) < 5.6) & (z >= 38.8))),
        (1, R(lambda x, y, z: (x >= 5.6) & (z > 32.0))),
        (1, R(lambda x, y, z: (x <= -5.6) & (z > 32.0))),
    ),
    "head": () if TW else ((2, R(lambda x, y, z: np.abs(x) < 3.05)),),
    "seal_thigh": ((2, R(lambda x, y, z: z > 16.6)), (2, R(lambda x, y, z: z <= 16.6))),
}
BOXES = [(b_, (c_[0] * S, c_[1] * S, c_[2] * S), (s_[0] * S, s_[1] * S, s_[2] * S), *ax_) for b_, c_, s_, _m, *ax_ in DETAILS]
for _sx in (1, -1):
    BOXES += [] if TW else [
        ("head", (_sx * 3.45 * S, 1.3 * S, 39.0 * S), (1.0 * S, 2.3 * S, 2.3 * S)),          # вокс-блоки
        ("head", (_sx * 2.1 * S, -2.2 * S, 37.6 * S), (1.3 * S, 1.3 * S, 1.0 * S)),          # фильтры
    ]
    BOXES += [
        ("chest", (_sx * 5.3 * S, 0.9 * S, 35.6 * S), (2.6 * S, 4.6 * S, 0.9 * S)),          # плечевые накладки
        ("thigh_l" if _sx > 0 else "thigh_r", (_sx * 7.0 * S, -3.3 * S, 15.0 * S), (0.5 * S, 0.5 * S, 0.5 * S)),   # заклёпки бедра
        ("shin_l" if _sx > 0 else "shin_r", (_sx * 5.0 * S, -4.6 * S, 8.0 * S), (3.4 * S, 0.5 * S, 0.9 * S)),      # накладка голени
        ("foot_l" if _sx > 0 else "foot_r", (_sx * 5.2 * S, -5.6 * S, 1.3 * S), (4.0 * S, 0.6 * S, 0.9 * S)),      # носок сапога
    ]
BOXES += [] if TW else [("head", (0, -3.05 * S, 38.0 * S), (2.1 * S, 0.6 * S, 2.0 * S))]       # решётка вперёд маски