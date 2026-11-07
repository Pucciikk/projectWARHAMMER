"""
УСТАРЕЛ 7.11.2026 (автор: «модель убогая»), новый — thunder_warrior.py. Громовой воин: цельная скульптура THUNDER WARRIOR 1 (references/models3d/armor/reduced/tw1.stl, сжатая из conceptARMOR), порезанная плоскостями на кости. Скелет как у Астартес (biped_gait.py),
но мечом и болтером он держит оружие прямо в исходнике: руки согнуты в покое, поэтому анимации работают поверх этой позы (hold_arms).
Запуск внутри Blender. Потом: facet_export(c, prebuilt=stack_model(c, PIECES, BOXES), palette=PALETTE, decals=DECALS, tracks=ANIMS, fine=("head",), levels=CRISP_LEVELS, edge_light=1, pixel=1/64, grain=0.012, relief=0.01, dead=0.009).
Координаты точек сняты по ортогональным видам с сеткой.
"""
import os

_HERE = r"C:/Users/Name/projectWARHAMMER/tools/models/blender"
exec(open(os.path.join(_HERE, "dread", "dread_kit.py"), encoding="utf-8").read())
exec(open(os.path.join(_HERE, "astartes", "biped_gait.py"), encoding="utf-8").read())
exec(open(os.path.join(_HERE, "astartes", "voxel_kit.py"), encoding="utf-8").read())

SRC = os.path.join(REFS, "armor", "reduced", "tw1.stl")
HEIGHT = 2.1
RAW_H = 47.5       # от земли до верха гребня, знамя выше
S = HEIGHT / RAW_H
CX = 1.5           # ось тела в исходнике

COLORS["bronze"] = ((0.15, 0.075, 0.022), 0.25)
COLORS["crimson"] = ((0.12, 0.007, 0.012), 0.2)
COLORS["skin"] = ((0.3, 0.17, 0.11), 0.1)
MAT_NAMES[:] = list(COLORS)
m = {n: i for i, n in enumerate(MAT_NAMES)}


def G(x, y, z):
    return ((x - CX) * S, y * S, z * S)


def raw(ce):
    return ce[:, 0] / S + CX, ce[:, 1] / S, ce[:, 2] / S


# голова скульптуры смотрит вбок: вырезаем её и разворачиваем вперёд
HEAD_X, HEAD_Y, HEAD_TURN, HEAD_SCALE = 3.0, 1.0, 28.0, 1.22     # голова крупнее исходной: иначе лицо не читается
COLORS["lens"] = ((0.75, 0.02, 0.015), 0.0)
MAT_NAMES[:] = list(COLORS)
m = {n: i for i, n in enumerate(MAT_NAMES)}

c = Concept("thunder_warrior", HEIGHT)
c.voxel = 0.005

c.bone("root", None, G(CX, 0, 21), 1)
c.bone("pelvis", "root", G(CX, 0, 21), 600)
c.bone("abdomen", "pelvis", G(CX, 0.5, 24.8), 500)
c.bone("chest", "abdomen", G(CX, 1, 28), 1200)
c.bone("head", "chest", G(HEAD_X, HEAD_Y, 37.2), 1500)
c.bone("visor", "head", G(HEAD_X, HEAD_Y, 37.2), 40)
c.bone("backpack", "chest", G(CX, 8, 33), 800)
c.bone("banner", "backpack", G(3.3, 7, 41), 380)
c.bone("chain", "backpack", G(4, 10.5, 29), 130)
c.bone("tabard_f", "pelvis", G(CX, -3, 21.5), 170)
c.bone("tabard_b", "pelvis", G(CX, 5.5, 21.5), 170)
for s, hip, knee, ankle, pad, shoulder, elbow, wrist in (
        ("l", (5.5, 0.7, 21), (10.5, -0.8, 13.3), (10.5, 2.0, 4.5), (11.5, 1.5, 36), (11.5, 3.5, 29.5), (11.5, -0.8, 26.5), (11.5, -8.4, 25.5)),
        ("r", (-2.7, -0.5, 21), (-7, -2.6, 13.3), (-8.5, -0.8, 4.5), (-8.5, 2.5, 36), (-9, 5, 29.5), (-8.5, 3.8, 27), (-7.5, -3.7, 27))):
    c.bone("thigh_" + s, "pelvis", G(*hip), 360)
    c.bone("shin_" + s, "thigh_" + s, G(*knee), 420)
    c.bone("foot_" + s, "shin_" + s, G(*ankle), 280)
    c.bone("tasset_" + s, "pelvis", G(hip[0] + (3.5 if s == "l" else -3.5), hip[1], 23), 120)
    c.bone("pad_" + s, "chest", G(*pad), 420)
    c.bone("arm_" + s, "chest", G(*shoulder), 170)
    c.bone("forearm_" + s, "arm_" + s, G(*elbow), 190)
    c.bone("hand_" + s, "forearm_" + s, G(*wrist), 400 if s == "l" else 560)    # кисть вместе с оружием


const_bone_head = lambda ce, size: np.full(len(ce), list(c.bones).index("head"), dtype=np.int64)
v, t = load_stl(SRC)
v = (v - np.array((CX, 0, 0))) * S


def P(x, y, z):
    return G(x, y, z)


# Дерево разрезов читается сверху вниз: сначала то, что торчит вперёд дальше всего (оружие), потом голова и ранец, потом руки, потом ноги
arm_l = cut(P(0, -8.0, 0), (0, 1, 0), cut(P(0, -1.2, 0), (0, 1, 0), "arm_l", "forearm_l"), "hand_l")
arm_r = cut(P(0, -3.7, 0), (0, 1, 0), cut(P(0, 3.8, 0), (0, 1, 0), "arm_r", "forearm_r"), "hand_r")
side_l = cut(P(0, -4.5, 30.1), (0, 3.7, 13), "pad_l", arm_l)
side_r = cut(P(0, 0, 30.6), (0, 3, 8), "pad_r", arm_r)

torso = cut(P(0, 0, 28), (0, 0, 1), "chest", "abdomen")
upper = cut(P(8.2, 0, 0), (1, 0, 0), side_l, cut(P(-5.0, 0, 0), (1, 0, 0), torso, side_r))
waist = cut(P(0, 0, 24.7), (0, 0, 1), upper, "pelvis")

head = cut(P(0, 0, 37.6), (0, 0, 1), cut(P(6.2, 0, 0), (1, 0, 0), waist, cut(P(0.0, 0, 0), (1, 0, 0), "head", waist)), waist)

pack = cut(P(0, 0, 27), (0, 0, 1), "backpack", "chain")
body_top = cut(P(0, 6.7, 0), (0, 1, 0), pack, head)


def leg(s, knee_z, ankle_z, knee_y, tass_x, sign):
    foot = cut(P(0, 0, ankle_z), (0, 1.2, 8), "shin_" + s, "foot_" + s)
    thigh = cut(P(tass_x, 0, 15.5), (sign, 0, 0.35), "tasset_" + s, "thigh_" + s)
    return cut(P(0, knee_y, knee_z), (0, 2.2, 7), thigh, foot)


legs_part = cut(P(CX, 0, 0), (1, 0, 0), leg("l", 14.2, 5.2, -0.8, 11.5, 1), leg("r", 14.2, 5.2, -2.6, -6.5, -1), cap=False)
# ткань спереди и сзади висит между ног
tab_f = cut(P(0, -0.8, 0), (0, 1, 0), legs_part, cut(P(6.3, 0, 0), (1, 0, 0), legs_part, cut(P(-3.3, 0, 0), (1, 0, 0), "tabard_f", legs_part)))
tab_b = cut(P(0, 4.0, 0), (0, 1, 0), cut(P(7.5, 0, 0), (1, 0, 0), tab_f, cut(P(-4.5, 0, 0), (1, 0, 0), "tabard_b", tab_f)), tab_f)
# выше ранца: знамя за наклонной плоскостью, перед ней голова с гребнем
above = cut(P(0, 6.7, 41), (0, 9, 3.2), "banner", cut(P(8.8, 0, 0), (1, 0, 0), "chest", cut(P(-1.4, 0, 0), (1, 0, 0), "head", "chest")))
lower = cut(P(0, 0, 22), (0, 0, 1), cut(P(0, 0, 41), (0, 0, 1), above, body_top), tab_b)

TREE = cut(P(0, -8.7, 0), (0, 1, 0), lower, cut(P(CX, 0, 0), (1, 0, 0), "hand_l", "hand_r"))


def mat(ce, size):
    x, y, z = raw(ce)
    out = np.full(len(ce), m["bronze"], dtype=np.int64)
    # кромки наплечников: полоса вдоль нижнего края и верхняя накладка, колени и носки сапог — светлый металл
    out[(x > 8.2) & (z > 30.1 - (y + 4.5) * 0.285) & (z < 31.6 - (y + 4.5) * 0.285)] = m["gold"]
    out[(x < -5.0) & (z > 30.6 - y * 0.375) & (z < 32.1 - y * 0.375)] = m["gold"]
    out[(x > 8.2) & (z > 38.0)] = m["gold"]
    out[(x < -5.0) & (z > 37.5)] = m["gold"]
    out[(z > 10) & (z < 17) & (y < -5.2)] = m["gold"]                         # наколенники
    out[(z < 4.2) & (y < -2.4)] = m["gold"]                                   # носки
    # ткань
    out[(z < 22) & (z > 5.5) & (y < -0.8) & (x > -3.3) & (x < 6.3)] = m["crimson"]
    out[(z < 22) & (y > 4.0) & (x > -4.5) & (x < 7.5)] = m["crimson"]
    out[(z > 41.5) & (y > 6)] = m["crimson"]                                  # знамя
    # оружие и кисти
    gun = (x < CX) & (y < -8.7)
    out[gun] = m["dark"]
    out[gun & (z > 29.5)] = m["steel"]
    sword = (x > CX) & (y < -8.7)
    out[sword] = m["steel"]
    out[sword & (z < 27.5)] = m["skin"]                                       # рука на рукояти
    out[sword & (z < 22.9)] = m["gold"]                                       # навершие
    # пояс и живот
    out[(z > 23.0) & (z < 24.7) & (x > -4) & (x < 7) & (y < 0)] = m["gold"]
    out[(z > 25.0) & (z < 27.6) & (x > -4) & (x < 7) & (y < 1)] = m["dark"]
    # диск на груди
    out[(np.hypot(x - 1.9, z - 31.2) < 2.7) & (y < -2.0) & (z > 28)] = m["gold"]
    # ранец: тёмный металл, верхний цилиндр латунный
    out[(y > 6.7) & (z > 27) & (z < 41.5)] = m["dark"]
    out[(y > 6.7) & (z > 37.5) & (z < 41.5)] = m["brass"]
    out[(y > 11.5) & (z > 27) & (z < 37.5)] = m["steel"]
    out[(y > 7.5) & (z < 27) & (z > 16)] = m["bone"]                          # черепа на цепи
    # подошвы
    out[z < 0.9] = m["dark"]
    return out

_ce = v[t].mean(axis=1)
_x, _y, _z = raw(_ce)
HEAD_MASK = (_z > 37.6) & (_y > -6.0) & (_y < 7.0) & ((_y - 6.7) * 9 + (_z - 41) * 3.2 < 0) & (((_z > 41) & (_x > -1.4) & (_x < 8.8)) | ((_z <= 41) & (_x > 0.0) & (_x < 6.2)))
_turn = np.array(Matrix.Rotation(math.radians(HEAD_TURN), 3, "Z"))
_piv = np.array(G(HEAD_X, HEAD_Y, 37.2))
_hused, _hinv = np.unique(t[HEAD_MASK], return_inverse=True)
_head_pose = lambda p: (p - _piv) @ _turn.T * HEAD_SCALE + _piv
hv = _head_pose(v[_hused])
ht = _hinv.reshape(-1, 3)


def _crest_mask(x, y, z):
    return (z > 41.7) & ((np.hypot(y - 1.2, z - 41.84) > 5.2) | (np.abs(x - HEAD_X) > 3.7))


def head_mat(ce, size):
    x, y, z = raw(ce)
    out = np.full(len(ce), m["gold"], dtype=np.int64)
    out[_crest_mask(x, y, z)] = m["crimson"]                                     # гребень: дуга вокруг купола
    out[z < 41.6] = m["bronze"]                                                  # нащёчники
    out[(z > 37.9) & (z < 41.05) & (np.abs(x - HEAD_X) < 2.3) & (y < -0.9)] = m["skin"]   # лицо
    return out

# оболочка берётся из цельной статуи (иначе дыра ломает её замыкание) и поворачивается уже после вырезания
c.bone_xform["head"] = _head_pose
c.add_part(hv, ht, const_bone_head, head_mat, max_edge=0.006, low=False)
c.add_part(v, t, TREE, mat, max_edge=0.008, hi_mask=~HEAD_MASK)

# очки: рамка на голове, сквозь неё видны глаза; красное стекло рисуется отдельным прозрачным проходом
EYE_Y, EYE_Z, EYE_DX = -3.25, 40.5, 1.05
_rubber = lambda ce, size: np.full(len(ce), m["rubber"], dtype=np.int64)
_lensm = lambda ce, size: np.full(len(ce), m["lens"], dtype=np.int64)
BOXES = []


def _box(bone, center, size, mat_fn):
    """Деталь и в запекании, и в простой форме. Координаты исходника."""
    gc = ((center[0] - CX) * S, center[1] * S, center[2] * S)
    gs = (size[0] * S, size[1] * S, size[2] * S)
    bv_, bt_ = box_mesh(gc, gs)
    c.add_part(bv_, bt_, const_bone_head, mat_fn, max_edge=0.006, low=False)
    BOXES.append((bone, gc, gs))


for _sx in (1, -1):
    _ex = HEAD_X + _sx * EYE_DX
    for _c, _s in (((_ex, EYE_Y, EYE_Z + 0.42), (1.5, 0.42, 0.18)), ((_ex, EYE_Y, EYE_Z - 0.42), (1.5, 0.42, 0.18)), ((_ex + 0.68, EYE_Y, EYE_Z), (0.16, 0.42, 1.0)), ((_ex - 0.68, EYE_Y, EYE_Z), (0.16, 0.42, 1.0))):
        _box("head", _c, _s, _rubber)
    _box("visor", (_ex, EYE_Y - 0.16, EYE_Z), (1.24, 0.1, 0.72), _lensm)
_box("head", (HEAD_X, EYE_Y, EYE_Z), (0.62, 0.3, 0.2), _rubber)
_skinm = lambda ce, size: np.full(len(ce), m["skin"], dtype=np.int64)
_goldm = lambda ce, size: np.full(len(ce), m["gold"], dtype=np.int64)
_box("head", (HEAD_X, EYE_Y - 0.1, 39.4), (0.8, 0.5, 1.1), _skinm)            # нос
_box("head", (HEAD_X, 1.0, 41.5), (7.0, 7.6, 0.5), _goldm)                    # поля шлема
_box("banner", (3.3, 7.0, 60.6), (15.0, 0.7, 0.7), _goldm)                    # перекладина знамени
_box("banner", (3.3, 7.0, 61.6), (0.9, 0.9, 1.6), _goldm)
_box("head", (HEAD_X, EYE_Y - 0.45, 41.5), (5.6, 1.0, 0.45), _goldm)          # козырёк
sc = c.build(min_island=0.03, cap=True, hi_limit=5000000)

BUILD = Build(cycle=0.95, duty=0.62, stride=0.7, lift=0.15, crouch=0.03, sway=1.35, arm=0.7, run_cycle=0.62, run_duty=0.44, run_stride=0.98, run_lift=0.24, run_crouch=0.09, run_lean=9.0, bob=1.25)
legs = Legs(c, even=True)


def hold_arms(pose):
    """Оружие в руках: качание рук приглушено, поверх него небольшой ход, ствол и клинок почти неподвижны относительно корпуса. Висящие детали — ткань, знамя, цепь с черепами."""
    def out(t):
        p = pose(t)
        a = 2 * math.pi * t
        for s in "lr":
            arm_x, arm_y, arm_z = p["arm_" + s]["rot"]
            sign = 1 if s == "l" else -1
            p["arm_" + s] = {"rot": (arm_x * 0.28, 0, (arm_z + sign * 5) * 0.3)}
            p["forearm_" + s] = {"rot": ((p["forearm_" + s]["rot"][0] + 14) * 0.22, 0, 0)}
            p["hand_" + s] = {"rot": (p["hand_" + s]["rot"][0] * 0.35, 0, 0)}
            p.pop("fingers_" + s)
            p.pop("thumb_" + s)
        tl, tr = p["thigh_l"]["rot"][0], p["thigh_r"]["rot"][0]
        p["tabard_f"] = {"rot": ((tl + tr) * 0.1 + min(tl, tr) * 0.25 + 2 * math.sin(a * 2 - 0.5), 0, (tl - tr) * 0.05)}
        p["tabard_b"] = {"rot": ((tl + tr) * 0.1 + max(tl, tr) * 0.25 + 2 * math.sin(a * 2 - 1.2), 0, (tr - tl) * 0.05)}
        p["banner"] = {"rot": (1.4 * math.sin(a * 2 - 0.9) + 1.5, 0, 2.2 * math.sin(a - 1.2))}
        p["chain"] = {"rot": (6 * math.sin(a * 2 - 1.6) + 2, 0, 5 * math.sin(a - 1.4))}
        return p
    return out


def known(pose):
    return lambda t: {k: v for k, v in pose(t).items() if k in c.bones}


ANIMS = {
    "misc.idle": tracks_from(known(hold_arms(idle(legs, BUILD))), IDLE_LENGTH, 144, True),
    "move.walk": tracks_from(known(hold_arms(walk(legs, BUILD))), BUILD.cycle, 32, True),
    "move.run": tracks_from(known(hold_arms(run(legs, BUILD))), BUILD.run_cycle, 26, True),
    "misc.stasis": tracks_from(known(hold_arms(stasis(legs, BUILD))), 1.0, 1, True),
    "attack.melee": tracks_from(known(melee(legs, BUILD, side="l", gain=0.62)), MELEE_LENGTH, 34, False),
    "misc.hurt": tracks_from(known(hurt(legs, BUILD)), HURT_LENGTH, 14, False),
    "misc.death": tracks_from(known(hold_arms(death(legs, BUILD))), DEATH_LENGTH, 81, False),
}
print("скорость клипов, блоков в секунду: шаг", round(BUILD.walk_speed, 3), "бег", round(BUILD.run_speed, 3))
preview(c, known(hold_arms(walk(legs, BUILD))), BUILD.cycle)


# ---- рисунки: молния Громовых воинов на знамени, груди и наплечниках, глаза на лице
BOLT = (
    "....XXX.",
    "...XXX..",
    "..XXX...",
    ".XXXXXX.",
    "....XXX.",
    "...XXX..",
    "..XX....",
    ".X......",
)
BOLT_BIG = (
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
# лицо пикселями: глаза за стеклом, брови, нос, рот. Шрам — по канону эти воины не щадили себя
EYE = (
    "BBBBBBBB",
    ".WWDDWW.",
    ".WWDDWW.",
)
NOSE = (
    "..NN..",
    "..NN..",
    "..NN..",
    ".NNNN.",
    "NN..NN",
)
MOUTH = (
    "NMMMMMMMMN",
    "..NNNNNN..",
)
SCAR = (
    "S...",
    ".S..",
    "..S.",
    "...S",
)
FACE_C = {"B": "rubber", "W": "bone", "D": "black", "N": "shadow", "M": "rubber", "S": "red"}
DECALS = [
    Decal(["head"], "y", -1, ((HEAD_X + EYE_DX - CX) * S, 40.48 * S), EYE, FACE_C),
    Decal(["head"], "y", -1, ((HEAD_X - EYE_DX - CX) * S, 40.48 * S), EYE, FACE_C),
    Decal(["head"], "y", -1, ((HEAD_X - CX) * S, 39.45 * S), NOSE, FACE_C),
    Decal(["head"], "y", -1, ((HEAD_X - CX) * S, 38.5 * S), MOUTH, FACE_C),
    Decal(["head"], "y", -1, ((HEAD_X + 1.5 - CX) * S, 39.3 * S), SCAR, FACE_C),
    Decal(["chest"], "y", -1, ((1.9 - CX) * S, 31.2 * S), BOLT, {"X": "crimson"}),
    Decal(["banner"], "y", -1, ((3.3 - CX) * S, 54.0 * S), BOLT_BIG, {"X": "gold"}, pixel=0.042),
    Decal(["banner"], "y", 1, ((3.3 - CX) * S, 54.0 * S), BOLT_BIG, {"X": "gold"}, pixel=0.042, flip=True),
    Decal(["pad_l"], "y", -1, ((12.5 - CX) * S, 33.0 * S), BOLT, {"X": "crimson"}),
    Decal(["pad_r"], "y", -1, ((-9.0 - CX) * S, 33.0 * S), BOLT, {"X": "crimson"}, flip=True),
]
PALETTE = {"lens": (130, 12, 8), "shadow": (140, 92, 72), "bronze": (136, 88, 44), "gold": (186, 132, 46), "dark": (60, 58, 62), "skin": (196, 142, 110), "steel": (150, 154, 162)}

def Q(fn):
    return lambda p: fn(p[:, 0] / S + CX, p[:, 1] / S, p[:, 2] / S)


PIECES = {
    "foot_l": ((1, None),), "foot_r": ((1, None),),
    "head": (
        (1, Q(lambda x, y, z: _crest_mask(x, y, z))),                           # гребень
        (2, Q(lambda x, y, z: (z > 41.5) & ~_crest_mask(x, y, z))),             # купол шлема
        (2, Q(lambda x, y, z: (z <= 41.5) & (np.abs(x - HEAD_X) < 3.4))),       # лицо и нащёчники
    ),
    "hand_l": (
        (2, Q(lambda x, y, z: z > 27.8)),                                       # клинок
        (2, Q(lambda x, y, z: z <= 27.8)),                                      # кисть и рукоять
    ),
    "hand_r": (
        (1, Q(lambda x, y, z: (y < -8.7) & (z >= 24.6))),                       # ствол и короб
        (2, Q(lambda x, y, z: (y < -8.7) & (z < 24.6))),                        # магазин
        (1, Q(lambda x, y, z: y >= -8.7)),                                      # кисть
    ),
    "backpack": (
        (2, Q(lambda x, y, z: z < 37.5)),
        (0, Q(lambda x, y, z: z >= 37.5)),
    ),
    "forearm_l": ((1, None),), "forearm_r": ((1, None),),
}