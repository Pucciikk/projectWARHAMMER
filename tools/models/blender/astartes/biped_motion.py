"""
Движения Астартес второго поколения: этот скелет и эти клипы потом получит игрок (генная модификация), поэтому скорости — игрока.
Ходьба 4,317, бег 5,612, присед 1,295 блока в секунду (решение автора 7.11.2026), медленный шаг 2,0 — для NPC.
Характер: атлет в броне. Быстрый и собранный, но каждый шаг весит тонну: короткое оседание после касания, корпус ровный, руки работают коротко.

Запускается после biped_gait.py (берёт оттуда smooth, track, bump, Legs, arm). Знаки Blender как там:
перед -Y, левая сторона +X, Z вверх. X+ уводит конечность назад (у головы — кивок вниз). Z+ поворачивает корпус влево
(правое плечо идёт вперёд). Y+ опускает левый бок.

Удар и вздрагивание здесь не клипы, а наложения (overlay): их кладёт поверх любого движения клиент (BipedConceptModel),
поэтому ноги продолжают бежать, пока руки бьют. Формат файла — overlay_json ниже.
"""
import math
import json
import os

import numpy as np

TAU = 2 * math.pi


def _cos(t, at):
    return math.cos(TAU * (t - at))


def _pulse(t, at, tau):
    """Отклик на удар ногой о землю: быстрое оседание и упругий возврат. t и at — доли цикла, tau — доля цикла."""
    x = (t - at) % 1.0
    return (x / tau) * math.exp(1 - x / tau)


# модель 2,2 единицы, в игре Астартес 2,4 блока, Громовой воин 2,3 (решения автора 7.11.2026): скорости и подъём — в блоках мира,
# ход ступни в клипе — в единицах модели, иначе при увеличении ступни поехали бы. GAME_HEIGHT задаёт скрипт модели до запуска этого файла
WORLD_SCALE = globals().get("GAME_HEIGHT", 2.4) / 2.2


class Gait:
    """Настройки одного аллюра. speed — блоков в секунду, cycle — секунд на два шага, duty — доля опоры одной ноги.
    stride — путь ступни под телом за опору (из скорости, чтобы ступня не скользила)."""

    def __init__(self, speed, cycle, duty, lift, crouch, lean, dip, impact, sway, roll, twist, chest_twist,
                 arm_amp, arm_bias, elbow, elbow_swing, out, curl, kick=0.0, heel=14.0, toe_off=40.0, cross=0.0, head_bob=1.0, flight=False):
        self.__dict__.update(locals())
        del self.__dict__["self"]
        self.stride = speed * duty * cycle / WORLD_SCALE


# ступня на земле: пятка ставится, носок отрывается. Ход ступни ограничен длиной ноги, поэтому ходьба на 4,3 блока в секунду — быстрый широкий шаг на полусогнутых
WALK = Gait(speed=4.317, cycle=0.52, duty=0.53, lift=0.13, crouch=0.085, lean=5.0, dip=0.012, impact=0.022, sway=0.022, roll=3.0, twist=7.0, chest_twist=9.0,
            arm_amp=19.0, arm_bias=-4.0, elbow=20.0, elbow_swing=22.0, out=7.0, curl=30.0, kick=0.15, heel=16.0, toe_off=42.0, cross=2.0)
RUN = Gait(speed=5.612, cycle=0.56, duty=0.36, lift=0.2, crouch=0.1, lean=12.0, dip=0.028, impact=0.035, sway=0.012, roll=2.0, twist=8.0, chest_twist=13.0,
           arm_amp=34.0, arm_bias=-9.0, elbow=84.0, elbow_swing=14.0, out=6.0, curl=78.0, kick=0.85, heel=6.0, toe_off=48.0, cross=7.0, head_bob=0.7, flight=True)
STROLL = Gait(speed=2.0, cycle=0.78, duty=0.6, lift=0.1, crouch=0.04, lean=2.5, dip=0.01, impact=0.016, sway=0.028, roll=2.6, twist=5.0, chest_twist=6.0,
              arm_amp=13.0, arm_bias=-2.0, elbow=16.0, elbow_swing=14.0, out=7.0, curl=26.0, kick=0.0, heel=14.0, toe_off=36.0, cross=0.0)
SNEAK = Gait(speed=1.295, cycle=0.86, duty=0.64, lift=0.1, crouch=0.2, lean=20.0, dip=0.008, impact=0.01, sway=0.03, roll=2.0, twist=4.0, chest_twist=5.0,
             arm_amp=8.0, arm_bias=-16.0, elbow=48.0, elbow_swing=10.0, out=10.0, curl=55.0, kick=0.0, heel=10.0, toe_off=30.0, cross=3.0, head_bob=0.6)
GAITS = {"stroll": STROLL, "walk": WALK, "run": RUN, "sneak": SNEAK}


def foot_path(legs, s, ph, g):
    """Голеностоп (y, z) и наклон ступни для фазы ph одной ноги. Опора: ступня неподвижна относительно земли, то есть едет назад
    под телом. Конец опоры: пятка поднимается вокруг носка. Вынос: в беге пятка сначала идёт к ягодице, потом колено выносит голень вперёд."""
    y0, ground, toe = legs.gait_y(s), legs.ground(s), legs.toe
    st = g.stride
    if ph < g.duty:
        k = ph / g.duty
        y = y0 - st / 2 + st * k
        land = g.heel * (1 - smooth(k / 0.16))                        # носок поднят при касании и хлопает об землю
        roll = g.toe_off * smooth((k - 0.62) / 0.38) ** 1.5           # отрыв пятки вокруг носка
        r = math.radians(roll)
        return y - math.sin(r) * toe * 0.3, ground + math.sin(r) * toe, roll - land
    k = (ph - g.duty) / (1 - g.duty)
    r0 = math.radians(g.toe_off)
    y_off, z_off = y0 + st / 2 - math.sin(r0) * toe * 0.3, ground + math.sin(r0) * toe
    # продвижение вперёд запаздывает при «захлёсте»: сначала пятка вверх, потом мах вперёд
    prog = smooth(k) if g.kick <= 0 else smooth(min(1.0, k ** (1 + 0.7 * g.kick) * 1.02))
    y = y_off + (y0 - st / 2 - y_off) * prog
    lift = g.lift * math.sin(math.pi * min(1.0, k ** 0.85)) ** 1.3
    kick = g.kick * 0.14 * math.sin(math.pi * min(1.0, k / 0.62)) ** 2   # пятка к ягодице
    z = ground + (z_off - ground) * (1 - smooth(k / 0.35)) + lift + kick
    pitch = g.toe_off * (1 - smooth(k / 0.45)) - g.heel * smooth((k - 0.55) / 0.45) + g.kick * 18 * math.sin(math.pi * min(1.0, k / 0.7))
    return y, z, pitch


def _arm_side(p, s, sign, swing, elbow, out, twist, wrist, curl):
    arm(p, s, sign, swing, elbow, out, wrist=wrist, curl=curl, twist=twist)


def locomotion(legs, g):
    """Один аллюр. Фаза 0 — касание левой пяткой, 0,5 — правой."""
    tau = 0.07 / g.cycle                                     # оседание после касания длится около 0,07 с при любом темпе

    def pose(t):
        a = TAU * t
        mid = g.duty / 2                                     # середина опоры левой ноги
        # ---- таз: высота. Ходьба: ниже всего в двойной опоре, выше на середине шага. Бег: ниже всего в середине опоры, выше в полёте
        if g.flight:
            dz = -g.crouch - g.dip * math.cos(2 * TAU * (t - mid))
        else:
            dz = -g.crouch - g.dip * math.cos(2 * a)
        hit = _pulse(t, 0.0, tau) + _pulse(t, 0.5, tau)
        dz -= g.impact * hit
        pitch = g.lean * 0.35 + 1.2 * hit * g.head_bob
        p = {}
        for s, shift in (("l", 0.0), ("r", 0.5)):
            y, z, ft = foot_path(legs, s, (t + shift) % 1, g)
            p.update(legs.solve(s, y, z, dz, ft, pitch))
        # ---- таз: вес над опорной ногой, бедро шагающей ноги идёт вперёд вместе с ней, бок над ногой в выносе проседает
        side = _cos(t, mid)                                  # +1 над левой ногой
        pel_z = -g.twist * math.cos(a - 0.25)                # левое бедро вперёд при касании левой
        pel_y = -g.roll * side
        p["root"] = {"pos": (g.sway * side, 0, dz)}
        p["pelvis"] = {"rot": (pitch, pel_y, pel_z)}
        # бедро гасит поворот и крен таза: колено смотрит по ходу, ступня в опоре не ездит вбок
        for s in "lr":
            r = p["thigh_" + s]["rot"]
            p["thigh_" + s]["rot"] = (r[0], -pel_y, -pel_z)
        # ---- плечи против таза и с опозданием; поясница берёт меньше, грудь больше
        sh_z = g.chest_twist * math.cos(a - 0.55)            # правое плечо вперёд, пока впереди левая нога
        abd = (g.lean * 0.3 + 0.6 * hit, -pel_y * 0.55, (sh_z - pel_z) * 0.42)
        breath = 0.5 * math.sin(a * 0.5)
        che = (g.lean * 0.35 + 1.6 * _pulse(t, 0.03, tau * 1.6) + 1.6 * _pulse(t, 0.53, tau * 1.6) + breath, -pel_y * 0.35, (sh_z - pel_z) * 0.58)
        p["abdomen"] = {"rot": abd}
        p["chest"] = {"rot": che}
        # ---- голова держит взгляд: гасит почти весь наклон и поворот корпуса, остаётся лёгкий кивок от шагов
        sum_x = pitch + abd[0] + che[0]
        sum_y = pel_y + abd[1] + che[1]
        sum_z = pel_z + abd[2] + che[2]
        nod = 1.8 * g.head_bob * (_pulse(t, 0.06, tau * 1.8) + _pulse(t, 0.56, tau * 1.8))
        p["head"] = {"rot": (-sum_x * 0.82 + 2.0 + nod, -sum_y * 0.9, -sum_z * 0.85)}
        p["backpack"] = {"rot": (0, 0, 0)}
        # ---- руки: против своей ноги, с опозданием; локоть доводит мах (follow-through)
        for s, sign, ph in (("l", 1, 0.5), ("r", -1, 0.0)):
            # фаза ph: рука впереди всего, когда противоположная нога касается земли
            c = math.cos(a - TAU * ph - 0.35)
            swing = g.arm_bias - g.arm_amp * c
            fwd = max(0.0, c)
            bend = g.elbow + g.elbow_swing * (0.5 + 0.5 * math.cos(a - TAU * ph - 0.9))
            out = g.out + 1.2 * side * sign - g.cross * fwd   # кисть уходит к середине груди на махе вперёд
            twist = -4 + g.cross * 1.4 * c                     # чуть отведена наружу, на махе вперёд идёт к середине
            wrist = -6 + 5 * math.cos(a - TAU * ph - 1.3)
            _arm_side(p, s, sign, swing, bend, out, twist, wrist, g.curl)
        return p
    return pose


IDLE_LENGTH = 12.0


def idle_pose(legs):
    """Стоит готовым: колени чуть согнуты, руки не висят плетьми, а держатся у корпуса (мешают наплечники и мышцы).
    Дыхание, перенос веса, взгляд перемещается рывками и задерживается. Клип 12 с."""
    def pose(t):
        a = TAU * t
        breathe = math.sin(a * 3)                         # 4 с на вдох и выдох
        shift = math.sin(a) * 0.7 + math.sin(a * 2 + 1.1) * 0.3
        dz = -0.035 + 0.004 * breathe - 0.007 * abs(shift)
        p = {}
        for s, sign in (("l", 1), ("r", -1)):
            p.update(legs.solve(s, legs.neutral_y(s) + (-0.05 if s == "l" else 0.06), legs.ground(s), dz - 0.012 * max(0.0, -shift * sign)))
        p["root"] = {"pos": (shift * 0.016, 0, dz)}
        p["pelvis"] = {"rot": (1.0, -shift * 1.4, shift * 2.0 + 3.0)}      # стоит чуть вполоборота: левая нога впереди
        p["abdomen"] = {"rot": (0.8 + breathe * 0.6, shift * 0.8, -shift * 1.0 - 1.5)}
        p["chest"] = {"rot": (-0.6 - breathe * 1.4, shift * 0.6, -shift * 1.1 - 1.0)}
        look = track(t, [(0, 0), (0.1, 0), (0.125, 22), (0.3, 19), (0.33, -6), (0.5, -5), (0.525, -28), (0.66, -25), (0.69, 3), (0.86, 2), (0.885, 12), (0.97, 10), (1.0, 0)])
        nod = track(t, [(0, 3), (0.125, -2), (0.3, 0), (0.33, 5), (0.5, 4), (0.525, -3), (0.66, -1), (0.69, 6), (0.885, 2), (1.0, 3)])
        p["head"] = {"rot": (nod + breathe * 0.6 - 1.0, look * 0.08, look * 0.8 - 0.5)}
        p["chest"]["rot"] = (p["chest"]["rot"][0], p["chest"]["rot"][1], p["chest"]["rot"][2] + look * 0.2)
        p["backpack"] = {"rot": (0, 0, 0)}
        flex = bump(t, 0.2, 0.025) + bump(t, 0.76, 0.025)
        shrug = bump(t, 0.44, 0.03)
        roll_l, roll_r = math.sin(a * 2 + 0.5), math.sin(a * 2 + 2.4)
        arm(p, "l", 1, -4 + roll_l * 1.2 + breathe * 0.6, 16 + 3 * roll_l + 10 * flex, 8.0 + shift * 1.0 + breathe * 0.5,
            wrist=-6 + math.sin(a * 3) * 2 - 8 * flex, curl=24 + 46 * flex * (0.5 + 0.5 * math.sin(t * 240)), thumb=20 + 14 * flex, twist=-5)
        arm(p, "r", -1, -3 + roll_r * 1.2 + breathe * 0.6 - 7 * shrug, 18 + 3 * roll_r + 6 * shrug, 8.0 - shift * 1.0 + breathe * 0.5 + 6 * shrug,
            wrist=-6 + math.sin(a * 3 + 2) * 2, curl=40 + 6 * math.sin(a * 2), thumb=26, twist=-5)
        p["pad_r"] = {"rot": (-3 * shrug, 0, -7 * shrug), "pos": (0, 0, 0.012 * shrug)}
        return p
    return pose


def sneak_idle_pose(legs):
    """Присел на месте (Shift без движения): таз низко, корпус вперёд, руки перед собой. Дыхание и медленный осмотр."""
    def pose(t):
        a = TAU * t
        breathe = math.sin(a * 2)
        dz = -0.2 + 0.004 * breathe
        p = {}
        for s in "lr":
            p.update(legs.solve(s, legs.neutral_y(s) + (-0.08 if s == "l" else 0.1), legs.ground(s), dz, 0, 7))
        p["root"] = {"pos": (0, 0, dz)}
        p["pelvis"] = {"rot": (7, 0, 4)}
        p["abdomen"] = {"rot": (6 + breathe * 0.5, 0, -2)}
        p["chest"] = {"rot": (7 - breathe * 1.2, 0, -2 + 6 * math.sin(a))}
        p["head"] = {"rot": (-16 + breathe * 0.5, 0, 14 * math.sin(a) - 6 * math.sin(a * 2))}
        p["backpack"] = {"rot": (0, 0, 0)}
        arm(p, "l", 1, -14 + breathe, 50, 10, wrist=-6, curl=55, twist=-4)
        arm(p, "r", -1, -18 + breathe, 54, 10, wrist=-6, curl=60, twist=-4)
        return p
    return pose


# ------------------------------------------------------------------ воздух: прыжок, падение, приземление

AIR_LENGTH = 1.2


def rise_pose(legs):
    """Взлёт: толчковая нога уходит назад, другая — коленом вверх; руки разводятся в стороны и вверх, правая вперёд (против левой ноги)."""
    def pose(t):
        a = TAU * t
        w = math.sin(a)
        p = {"root": {"pos": (0, 0, 0)}, "pelvis": {"rot": (3, 0, -3)}, "abdomen": {"rot": (-2, 0, 1.5)}, "chest": {"rot": (-4 + 0.6 * w, 0, 3)},
             "head": {"rot": (5, 0, -2)}, "backpack": {"rot": (0, 0, 0)}}
        p["thigh_l"] = {"rot": (-52, -12, 0)}
        p["shin_l"] = {"rot": (74, 0, 0)}
        p["foot_l"] = {"rot": (14, 0, 0)}
        p["thigh_r"] = {"rot": (16, 13, 0)}
        p["shin_r"] = {"rot": (38, 0, 0)}
        p["foot_r"] = {"rot": (30, 0, 0)}
        arm(p, "r", -1, -36 + 2 * w, 50, 8, wrist=-4, curl=34, twist=-(40 + 2 * w))
        arm(p, "l", 1, 10 - 2 * w, 38, 8, wrist=-4, curl=30, twist=-(46 - 2 * w))
        return p
    return pose


def fall_pose(legs):
    """Падение: ноги чуть согнуты и расставлены (одна впереди), руки широко в стороны для равновесия и слегка ловят воздух."""
    def pose(t):
        a = TAU * t
        w, w2 = math.sin(a), math.sin(a * 2 + 0.7)
        p = {"root": {"pos": (0, 0, 0)}, "pelvis": {"rot": (2, 0, -1)}, "abdomen": {"rot": (1, 0, 0.5)}, "chest": {"rot": (1 + 0.8 * w2, 0, 1)},
             "head": {"rot": (10, 0, 0)}, "backpack": {"rot": (0, 0, 0)}}
        p["thigh_l"] = {"rot": (-30, -16, 0)}
        p["shin_l"] = {"rot": (50, 0, 0)}
        p["foot_l"] = {"rot": (12, 0, 0)}
        p["thigh_r"] = {"rot": (-6, 16, 0)}
        p["shin_r"] = {"rot": (34, 0, 0)}
        p["foot_r"] = {"rot": (16, 0, 0)}
        arm(p, "r", -1, -22 + 3 * w, 40, 10, wrist=-2, curl=16, twist=-(58 + 5 * w2))
        arm(p, "l", 1, -12 - 3 * w, 36, 10, wrist=-2, curl=16, twist=-(58 - 5 * w2))
        return p
    return pose


LAND_LENGTH = 0.5


def land_delta(legs):
    """Приземление — добавка к любой позе: таз проседает и пружинит обратно, колени гасят удар, корпус кивает вперёд, руки уходят вниз и в стороны.
    Считается разницей двух поз (с оседанием и без), чтобы ступни остались на земле. Глубину задаёт клиент по скорости падения."""
    def k_of(sec):
        return smooth(sec / 0.06) * (1 - smooth((sec - 0.08) / 0.4))

    def stance(k):
        dz = -0.17 * k
        p = {}
        for s in "lr":
            p.update(legs.solve(s, legs.neutral_y(s) + (-0.04 if s == "l" else 0.05), legs.ground(s), dz, 0, 9 * k))
        p["root"] = {"pos": (0, 0, dz)}
        p["pelvis"] = {"rot": (9 * k, 0, 0)}
        p["abdomen"] = {"rot": (5 * k, 0, 0)}
        p["chest"] = {"rot": (6 * k, 0, 0)}
        p["head"] = {"rot": (-12 * k, 0, 0)}
        for s, sign in (("l", 1), ("r", -1)):
            p["arm_" + s] = {"rot": (-6 * k, 0, -sign * 12 * k)}
            p["forearm_" + s] = {"rot": (-22 * k, 0, 0)}
        return p

    zero = stance(0.0)

    def pose(t):
        cur = stance(k_of(t * LAND_LENGTH))
        out = {}
        for b, st in cur.items():
            z = zero.get(b, {})
            e = {}
            for key in ("rot", "pos"):
                if key in st:
                    base = z.get(key, (0, 0, 0))
                    e[key] = tuple(v - w for v, w in zip(st[key], base))
            out[b] = e
        return out
    return pose


# ------------------------------------------------------------------ особые состояния игрока: лестница, вода, ползком, верхом, сон, элитры, полёт
# Плавание, ползание и элитры: тело целиком кладёт клиент (как ванильный игрок), здесь поза в осях стоящей модели:
# «вверх» модели в этих клипах — вперёд по ходу.

def _limbs(p, legs_rot, arms):
    for b, r in legs_rot.items():
        p[b] = {"rot": r}
    for args, kw in arms:
        arm(p, *args, **kw)
    return p


CLIMB_STEP = 0.9     # блоков подъёма за цикл (два перехвата руками)


def climb_pose(legs):
    """Лестница: перехват руками над головой по очереди, ноги переступают со сдвигом в четверть цикла, корпус у лестницы.
    Фаза — от высоты (клиент), вниз клип идёт назад."""
    def pose(t):
        a = TAU * t
        p = {"root": {"pos": (0, -0.03, -0.02)}, "pelvis": {"rot": (-4, 0, 0)}, "abdomen": {"rot": (2, 0, 2 * math.sin(a))},
             "chest": {"rot": (4, 1.5 * math.sin(a), 3 * math.sin(a))}, "head": {"rot": (-14, 0, -3 * math.sin(a))}, "backpack": {"rot": (0, 0, 0)}}
        for s, sign, ph in (("l", 1, 0.0), ("r", -1, 0.5)):
            u = (t + ph) % 1
            reach = smooth(u / 0.35) if u < 0.35 else 1 - smooth((u - 0.35) / 0.65)       # быстро вверх, медленно подтягивается
            arm(p, s, sign, -150 + 52 * (1 - reach), 30 + 62 * (1 - reach), 6, wrist=-10, curl=70, twist=-6)
            v = (t + ph + 0.25) % 1
            step = smooth(v / 0.4) if v < 0.4 else 1 - smooth((v - 0.4) / 0.6)
            p["thigh_" + s] = {"rot": (-14 - 46 * step, 0, 0)}
            p["shin_" + s] = {"rot": (20 + 62 * step, 0, 0)}
            p["foot_" + s] = {"rot": (-8 - 14 * step, 0, 0)}
        return p
    return pose


def climb_idle_pose(legs):
    """Висит на лестнице: обе руки держат перекладины, одна нога выше, лёгкое дыхание."""
    def pose(t):
        b = math.sin(TAU * t * 2)
        p = {"root": {"pos": (0, -0.03, -0.02)}, "pelvis": {"rot": (-4, 0, 0)}, "abdomen": {"rot": (2 + 0.5 * b, 0, 0)},
             "chest": {"rot": (4 - b, 0, 0)}, "head": {"rot": (-6, 0, 0)}, "backpack": {"rot": (0, 0, 0)}}
        arm(p, "l", 1, -140, 46, 6, wrist=-10, curl=70, twist=-6)
        arm(p, "r", -1, -112, 78, 6, wrist=-10, curl=70, twist=-6)
        p["thigh_l"] = {"rot": (-44, 0, 0)}
        p["shin_l"] = {"rot": (70, 0, 0)}
        p["foot_l"] = {"rot": (-18, 0, 0)}
        p["thigh_r"] = {"rot": (-16, 0, 0)}
        p["shin_r"] = {"rot": (24, 0, 0)}
        p["foot_r"] = {"rot": (-8, 0, 0)}
        return p
    return pose


SWIM_STRIDE = 2.4    # блоков за цикл кролем (два гребка)


def swim_pose(legs):
    """Кроль: руки по очереди тянут из-за головы к бедру и возвращаются над водой через сторону; ноги часто бьют; корпус перекатывается."""
    def pose(t):
        a = TAU * t
        p = {"root": {"pos": (0, 0, 0)}, "pelvis": {"rot": (0, 0, 0)}, "abdomen": {"rot": (0, -6 * math.sin(a), 0)},
             "chest": {"rot": (0, -12 * math.sin(a), 0)}, "head": {"rot": (-28, 8 * math.sin(a), 0)}, "backpack": {"rot": (0, 0, 0)}}
        for s, sign, ph in (("l", 1, 0.0), ("r", -1, 0.5)):
            u = (t + ph) % 1
            if u < 0.55:             # гребок: из-за головы к бедру
                k = smooth(u / 0.55)
                arm(p, s, sign, -172 + 186 * k, 18 + 40 * math.sin(math.pi * k), 4, wrist=-8, curl=30, twist=-6)
            else:                    # возврат через сторону
                k = smooth((u - 0.55) / 0.45)
                arm(p, s, sign, 14 - 186 * k, 60 - 40 * k, 4, wrist=-4, curl=20, twist=-(10 + 50 * math.sin(math.pi * k)))
            kick = math.sin(2 * a + (0 if s == "l" else math.pi))
            p["thigh_" + s] = {"rot": (6 + 16 * kick, 0, 0)}
            p["shin_" + s] = {"rot": (14 + 12 * max(0.0, kick), 0, 0)}
            p["foot_" + s] = {"rot": (40, 0, 0)}
        return p
    return pose


def tread_pose(legs):
    """Держится на воде: ноги «взбивают» по кругу, руки гребут в стороны ладонями вниз, голова над водой."""
    def pose(t):
        a = TAU * t
        p = {"root": {"pos": (0, 0, 0)}, "pelvis": {"rot": (4, 0, 0)}, "abdomen": {"rot": (3, 0, 0)}, "chest": {"rot": (2 + math.sin(2 * a), 0, 0)},
             "head": {"rot": (-6, 0, 0)}, "backpack": {"rot": (0, 0, 0)}}
        for s, sign, ph in (("l", 1, 0.0), ("r", -1, 0.5)):
            u = TAU * ((t + ph) % 1)
            p["thigh_" + s] = {"rot": (-34 + 14 * math.sin(u), sign * -8, 0)}
            p["shin_" + s] = {"rot": (58 + 22 * math.cos(u), 0, 0)}
            p["foot_" + s] = {"rot": (20, 0, 0)}
            arm(p, s, sign, -30 + 6 * math.sin(2 * a), 44, 10, wrist=-10, curl=20, twist=-(38 + 16 * math.sin(2 * a + ph * TAU)))
        return p
    return pose


CRAWL_STRIDE = 0.8


def crawl_pose(legs):
    """Ползком (щель в блок): локти вперёд по очереди, колено той же стороны подтягивается вбок."""
    def pose(t):
        a = TAU * t
        p = {"root": {"pos": (0, 0, 0)}, "pelvis": {"rot": (0, 0, 4 * math.sin(a))}, "abdomen": {"rot": (0, 0, -3 * math.sin(a))},
             "chest": {"rot": (0, 0, -5 * math.sin(a))}, "head": {"rot": (-42, 0, 0)}, "backpack": {"rot": (0, 0, 0)}}
        for s, sign, ph in (("l", 1, 0.0), ("r", -1, 0.5)):
            u = (t + ph) % 1
            k = math.sin(math.pi * u) ** 2
            arm(p, s, sign, -150 + 40 * (u if u < 0.5 else 1 - u) * 2, 80 - 20 * k, 6, wrist=-6, curl=60, twist=-(14 + 10 * k))
            p["thigh_" + s] = {"rot": (-8 - 40 * k, sign * -(8 + 22 * k), 0)}
            p["shin_" + s] = {"rot": (16 + 60 * k, 0, 0)}
            p["foot_" + s] = {"rot": (30, 0, 0)}
        return p
    return pose


def sit_pose(legs):
    """Верхом, в лодке, в вагонетке: бёдра вперёд, голени вниз, кулаки на бёдрах, корпус ровно, лёгкое покачивание."""
    def pose(t):
        a = TAU * t
        p = {"root": {"pos": (0, 0, -0.07)}, "pelvis": {"rot": (-2, 0, 0)}, "abdomen": {"rot": (2 + 0.5 * math.sin(a * 3), 0, 0)},
             "chest": {"rot": (1 - 0.8 * math.sin(a * 3), 0, 0)}, "head": {"rot": (2, 0, 0)}, "backpack": {"rot": (0, 0, 0)}}
        for s, sign in (("l", 1), ("r", -1)):
            p["thigh_" + s] = {"rot": (-86, sign * -5, 0)}
            p["shin_" + s] = {"rot": (84, 0, 0)}
            p["foot_" + s] = {"rot": (0, 0, 0)}
            arm(p, s, sign, -34, 46, 6, wrist=-6, curl=40, twist=-4)
        return p
    return pose


def sleep_pose(legs):
    """Сон (кладёт клиент): прямые ноги, руки вдоль тела, голова чуть набок, медленное дыхание."""
    def pose(t):
        b = math.sin(TAU * t * 2)
        p = {"root": {"pos": (0, 0, 0)}, "pelvis": {"rot": (0, 0, 0)}, "abdomen": {"rot": (0.6 * b, 0, 0)}, "chest": {"rot": (-1.2 * b, 0, 0)},
             "head": {"rot": (0, 0, 14)}, "backpack": {"rot": (0, 0, 0)}}
        for s, sign in (("l", 1), ("r", -1)):
            p["thigh_" + s] = {"rot": (0, sign * -3, 0)}
            p["shin_" + s] = {"rot": (6, 0, 0)}
            p["foot_" + s] = {"rot": (10, 0, 0)}
            arm(p, s, sign, 0, 12, 4, wrist=0, curl=20, twist=-6)
        return p
    return pose


def glide_pose(legs):
    """Элитры: руки отведены назад вдоль тела и чуть в стороны, ноги вместе, голова поднята по ходу."""
    def pose(t):
        a = TAU * t
        p = {"root": {"pos": (0, 0, 0)}, "pelvis": {"rot": (0, 0, 0)}, "abdomen": {"rot": (-3, 0, 0)}, "chest": {"rot": (-4 + math.sin(a), 0, 0)},
             "head": {"rot": (-48, 0, 0)}, "backpack": {"rot": (0, 0, 0)}}
        for s, sign in (("l", 1), ("r", -1)):
            p["thigh_" + s] = {"rot": (6 + 2 * math.sin(a + (0 if s == "l" else 1)), sign * 2, 0)}
            p["shin_" + s] = {"rot": (8, 0, 0)}
            p["foot_" + s] = {"rot": (34, 0, 0)}
            arm(p, s, sign, 26, 14, 4, wrist=4, curl=24, twist=-(22 + 4 * math.sin(a * 2)))
        return p
    return pose


def fly_pose(legs):
    """Полёт в творческом: висит в воздухе, ноги свободно и чуть согнуты, руки разведены для равновесия, мягкое покачивание."""
    def pose(t):
        a = TAU * t
        bob = math.sin(a)
        p = {"root": {"pos": (0, 0, 0.012 * bob)}, "pelvis": {"rot": (4, 0, 0)}, "abdomen": {"rot": (2, 0, 0)}, "chest": {"rot": (-1 + bob, 0, 0)},
             "head": {"rot": (2, 0, 0)}, "backpack": {"rot": (0, 0, 0)}}
        p["thigh_l"] = {"rot": (-14 + 3 * bob, -6, 0)}
        p["shin_l"] = {"rot": (30 - 4 * bob, 0, 0)}
        p["foot_l"] = {"rot": (18, 0, 0)}
        p["thigh_r"] = {"rot": (-4 - 3 * bob, 6, 0)}
        p["shin_r"] = {"rot": (22 + 4 * bob, 0, 0)}
        p["foot_r"] = {"rot": (20, 0, 0)}
        arm(p, "l", 1, -10 + 2 * bob, 30, 6, wrist=-4, curl=24, twist=-(20 + 3 * bob))
        arm(p, "r", -1, -8 - 2 * bob, 30, 6, wrist=-4, curl=24, twist=-(20 - 3 * bob))
        return p
    return pose


def fly_move_pose(legs):
    """Полёт с ходом: корпус вперёд, руки назад и в стороны, ноги вытянуты назад."""
    def pose(t):
        a = TAU * t
        p = {"root": {"pos": (0, 0, 0)}, "pelvis": {"rot": (24, 0, 0)}, "abdomen": {"rot": (6, 0, 0)}, "chest": {"rot": (4 + math.sin(a), 0, 0)},
             "head": {"rot": (-28, 0, 0)}, "backpack": {"rot": (0, 0, 0)}}
        for s, sign in (("l", 1), ("r", -1)):
            p["thigh_" + s] = {"rot": (10 + 2 * math.sin(a + (0 if s == "l" else 1.5)), sign * -3, 0)}
            p["shin_" + s] = {"rot": (16, 0, 0)}
            p["foot_" + s] = {"rot": (30, 0, 0)}
            arm(p, s, sign, 30, 20, 4, wrist=4, curl=30, twist=-(26 + 4 * math.sin(a * 2)))
        return p
    return pose


# ------------------------------------------------------------------ вторичное движение: пружины

class Spring:
    """Затухающая пружина за целью: drive(i) — цель в кадре i, freq — собственная частота, Гц, zeta — затухание.
    Считаем несколько циклов подряд и берём последний: у зацикленного клипа он сам сходится к периодичному."""

    def __init__(self, bone, axis, drive, freq, zeta, add=True):
        self.__dict__.update(locals())
        del self.__dict__["self"]


def with_physics(pose, length, springs, n=None, cycles=6, loop=True):
    n = n or max(120, int(length * 240))
    ts = np.arange(n) / n
    frames = [pose(t) for t in ts]
    dz = np.array([f.get("root", {}).get("pos", (0, 0, 0))[2] for f in frames])
    dt = length / n
    # вертикальное ускорение таза, блоков в с²: от него подпрыгивают висячие детали
    acc = (np.roll(dz, -1) - 2 * dz + np.roll(dz, 1)) / (dt * dt) if loop else np.gradient(np.gradient(dz, dt), dt)
    ctx = dict(frames=frames, acc=acc, n=n, dt=dt)
    results = []
    for sp in springs:
        w = TAU * sp.freq
        x, v = None, 0.0
        hist = np.zeros(n)
        total = cycles if loop else 1
        for c_ in range(total):
            for i in range(n):
                target = sp.drive(i, ctx)
                if x is None:
                    x = target
                for _ in range(4):
                    a_ = w * w * (target - x) - 2 * sp.zeta * w * v
                    v += a_ * dt / 4
                    x += v * dt / 4
                if c_ == total - 1:
                    hist[i] = x
        results.append((sp, hist))

    def out(t):
        p = pose(t)
        f = (t % 1.0) * n if loop else min(t * n, n - 1.0)
        i0 = int(f) % n
        i1 = (i0 + 1) % n if loop else min(i0 + 1, n - 1)
        k = f - int(f)
        for sp, hist in results:
            val = hist[i0] * (1 - k) + hist[i1] * k
            st = p.setdefault(sp.bone, {})
            rot = list(st.get("rot", (0.0, 0.0, 0.0)))
            rot[sp.axis] = rot[sp.axis] + val if sp.add else val
            st["rot"] = tuple(rot)
        return p
    return out


def _rot(ctx, i, bone, axis):
    return ctx["frames"][i].get(bone, {}).get("rot", (0, 0, 0))[axis]


def standard_springs(heavy=1.0):
    """Наплечники отстают от плеча и подпрыгивают на каждом шаге, набедренники идут за бедром с запозданием, ранец кивает,
    антенна хлещет, печать на бедре висит отвесно и раскачивается."""
    S = []
    for s, sign in (("l", 1), ("r", -1)):
        # мах руки над головой (лестница, плавание) наплечник берёт не целиком: дальше ±60° он только приподнимается
        S.append(Spring("pad_" + s, 0, lambda i, c, s=s: float(np.clip(_rot(c, i, "arm_" + s, 0), -60, 50)) * 0.3, 3.2, 0.32))
        # наплечник поднимается вместе с отведённой рукой (иначе рука входит в него) и подпрыгивает на шагах
        S.append(Spring("pad_" + s, 1, lambda i, c, s=s: _rot(c, i, "arm_" + s, 1) * 0.55 + float(np.clip(-_rot(c, i, "arm_" + s, 0) - 60, 0, 90)) * (0.25 if s == "r" else -0.25), 4.5, 0.35))
        S.append(Spring("pad_" + s, 2, lambda i, c, sign=sign: sign * (0.8 - c["acc"][i] * 0.05), 4.0, 0.25))
        S.append(Spring("tasset_" + s, 0, lambda i, c, s=s: _rot(c, i, "thigh_" + s, 0) * 0.62, 5.0, 0.4))
        S.append(Spring("tasset_" + s, 2, lambda i, c, sign=sign: sign * (max(0.0, -c["acc"][i]) * 0.03), 4.0, 0.3))
    S.append(Spring("backpack", 0, lambda i, c: np.clip(-c["acc"][i] * 0.06, -3, 3), 3.0, 0.35))
    S.append(Spring("antenna", 0, lambda i, c: np.clip(-c["acc"][i] * 0.35, -8, 8) - (_rot(c, i, "chest", 0) - 0) * 0.3, 2.4, 0.12))
    S.append(Spring("antenna", 1, lambda i, c: -(_rot(c, i, "chest", 2) + _rot(c, i, "pelvis", 2)) * 0.25, 2.0, 0.12))
    # печать: висит отвесно, то есть гасит поворот бедра, и раскачивается от толчков
    # частоты между частотой цикла и частотой шагов всех аллюров (1,3–3,9 Гц), иначе резонанс раскачивает печать до груди
    S.append(Spring("seal_thigh", 0, lambda i, c: -(_rot(c, i, "thigh_l", 0) + _rot(c, i, "pelvis", 0)) * 0.85 - np.clip(c["acc"][i] * 0.2, -6, 6), 2.9, 0.24, add=False))
    S.append(Spring("seal_thigh", 2, lambda i, c: 3 + _rot(c, i, "pelvis", 1) * 1.5, 2.7, 0.24, add=False))
    # ткань Громового воина спереди и сзади: шагающее вперёд бедро толкает переднюю полу, отставшее — заднюю; плюс толчки шагов
    S.append(Spring("tabard_f", 0, lambda i, c: min(_rot(c, i, "thigh_l", 0), _rot(c, i, "thigh_r", 0)) * 0.75 - float(np.clip(c["acc"][i] * 0.15, -5, 5)), 3.0, 0.3, add=False))
    S.append(Spring("tabard_f", 2, lambda i, c: (_rot(c, i, "thigh_l", 0) - _rot(c, i, "thigh_r", 0)) * 0.08, 2.6, 0.3, add=False))
    S.append(Spring("tabard_b", 0, lambda i, c: max(_rot(c, i, "thigh_l", 0), _rot(c, i, "thigh_r", 0)) * 0.55 + float(np.clip(c["acc"][i] * 0.15, -5, 5)), 2.8, 0.3, add=False))
    return S


# ------------------------------------------------------------------ наложения: удар и прочее поверх любого движения

MELEE_LENGTH = 0.7
MELEE_HIT = 0.17
UPPER = ("abdomen", "chest", "head", "pad_l", "pad_r", "arm_l", "forearm_l", "hand_l", "fingers_l", "thumb_l",
         "arm_r", "forearm_r", "hand_r", "fingers_r", "thumb_r")
LOWER = ("root", "pelvis", "thigh_l", "shin_l", "foot_l", "thigh_r", "shin_r", "foot_r", "tasset_l", "tasset_r")


def melee_pose(legs, side="r"):
    """Удар кулаком с разворота: короткий замах (0,1 с), удар весом корпуса к 0,17 с, доводка и возврат.
    Бьёт правой — разворот влево. Ноги: короткий подшаг левой, используется только когда стоит на месте."""
    hs = -1 if side == "r" else 1            # знак руки для arm()
    hit, off = (("r", "l") if side == "r" else ("l", "r"))
    turn = 1 if side == "r" else -1          # Z+ (влево) для удара правой

    def pose(t):
        sec = t * MELEE_LENGTH
        sh = track(sec, [(0, -4), (0.1, 16), (0.17, -84, "in"), (0.26, -80), (0.7, -4)])
        el = track(sec, [(0, 20), (0.1, 112), (0.17, 12, "in"), (0.26, 16), (0.7, 20)])
        out = track(sec, [(0, 7), (0.1, 16), (0.17, -4, "in"), (0.26, -2), (0.7, 7)])
        tw = track(sec, [(0, 4), (0.1, 26), (0.17, -30, "in"), (0.26, -28), (0.7, 4)])
        body = track(sec, [(0, 0), (0.1, -16), (0.17, 22, "in"), (0.28, 20), (0.7, 0)])
        lean = track(sec, [(0, 0), (0.1, -3), (0.17, 9, "in"), (0.28, 8), (0.7, 0)])
        dz = track(sec, [(0, -0.035), (0.1, -0.05), (0.17, -0.11, "in"), (0.3, -0.1), (0.7, -0.035)])
        step = smooth(sec / 0.15) * (1 - smooth((sec - 0.35) / 0.3))
        p = {}
        p.update(legs.solve("l", legs.neutral_y("l") - 0.05 - 0.2 * step, legs.ground("l") + 0.06 * bump(sec / 0.7, 0.04, 0.08), dz))
        p.update(legs.solve("r", legs.neutral_y("r") + 0.06 + 0.1 * step, legs.ground("r"), dz, 8 * step))
        z = turn * body
        p["root"] = {"pos": (0, -0.04 * step, dz)}
        p["pelvis"] = {"rot": (lean * 0.3, 0, z * 0.35)}
        p["abdomen"] = {"rot": (lean * 0.3, 0, z * 0.3)}
        p["chest"] = {"rot": (lean * 0.4, -turn * 2 * smooth(sec / 0.17), z * 0.4)}
        p["head"] = {"rot": (-lean * 0.8 + 2, 0, -z * 0.85)}
        arm(p, hit, hs, sh, el, out, wrist=-6, curl=88, thumb=70, twist=tw)
        # вторая рука прикрывает корпус и уходит назад на ударе: противовес
        g_sh = track(sec, [(0, -4), (0.1, -26), (0.17, 10, "in"), (0.28, 8), (0.7, -4)])
        g_el = track(sec, [(0, 20), (0.1, 96), (0.17, 70, "in"), (0.7, 20)])
        arm(p, off, -hs, g_sh, g_el, 10, wrist=-4, curl=80, thumb=60, twist=8)
        p["pad_" + hit] = {"rot": (sh * 0.2, 0, hs * -max(0.0, out) * 0.5), "pos": (0, 0, 0.02 * smooth(-sh / 84))}
        p["pad_" + off] = {"rot": (g_sh * 0.2, 0, 0)}
        return p

    def weight(t):
        sec = t * MELEE_LENGTH
        return smooth(sec / 0.06) * (1 - smooth((sec - 0.36) / 0.3))
    return pose, weight


def overlay_json(path, clips, fps=60):
    """Наложения для клиента: на каждый клип длина, вес по кадрам и повороты костей в радианах уже во внутренних осях GeckoLib
    (из Blender: x -> -x, y -> z, z -> y), позиции в 1/16 блока (x, z, y). group: upper — всегда, lower — только когда стоит на месте."""
    out = {}
    for name, (pose, weight, length) in clips.items():
        frames = max(2, int(round(length * fps)))
        bones = {}
        ws = []
        for i in range(frames + 1):
            t = i / frames
            ws.append(round(weight(t), 4))
            for b, st in pose(t).items():
                e = bones.setdefault(b, {"group": "lower" if b in LOWER else "upper"})
                if "rot" in st:
                    x, y, z = st["rot"]
                    e.setdefault("rot", []).extend([round(math.radians(-x), 5), round(math.radians(z), 5), round(math.radians(y), 5)])
                if "pos" in st:
                    x, y, z = st["pos"]
                    e.setdefault("pos", []).extend([round(x * 16, 4), round(z * 16, 4), round(y * 16, 4)])
        out[name] = {"length": length, "frames": frames + 1, "weight": ws, "bones": bones}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, separators=(",", ":"))


def motion_json(path, clips):
    """Все движения для клиента (BipedMotion): клип = кадры поз костей. mode: loop — цикл, once — разово, add — добавка поверх позы.
    speed — скорость тела аллюра (блоков в секунду), weight — вес по кадрам (наложения вроде удара). Повороты — радианы во внутренних осях
    GeckoLib (из Blender: x -> -x, y -> z, z -> y), позиции — 1/16 блока (x, z, y). group lower — кости ног и таза."""
    out = {}
    for name, c in clips.items():
        pose, length, fps = c["pose"], c["length"], c.get("fps", 60)
        frames = max(2, int(round(length * fps)))
        loop = c["mode"] == "loop"
        n = frames if loop else frames + 1          # у цикла последний кадр совпадает с первым — его не пишем
        bones, ws = {}, []
        for i in range(n):
            t = i / frames
            if c.get("weight"):
                ws.append(round(c["weight"](t), 4))
            for b, st in pose(t).items():
                e = bones.setdefault(b, {"group": "lower" if b in LOWER else "upper"})
                if "rot" in st:
                    x, y, z = st["rot"]
                    e.setdefault("rot", []).extend([round(math.radians(-x), 5), round(math.radians(z), 5), round(math.radians(y), 5)])
                if "pos" in st:
                    x, y, z = st["pos"]
                    e.setdefault("pos", []).extend([round(x * 16, 4), round(z * 16, 4), round(y * 16, 4)])
        # кость могла встретиться не во всех кадрах: такие дорожки неполные, дополняем нулями в конце нельзя — отбрасываем
        for b in list(bones):
            for key in ("rot", "pos"):
                if key in bones[b] and len(bones[b][key]) != n * 3:
                    del bones[b][key]
        entry = {"mode": c["mode"], "length": length, "frames": n, "bones": bones}
        if ws:
            entry["weight"] = ws
        if "speed" in c:
            entry["speed"] = c["speed"]
        out[name] = entry
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, separators=(",", ":"))


def motion_set(legs, death_pose):
    """Набор движений Астартес для motion_json."""
    springs = standard_springs()
    clips = {
        "idle": dict(pose=with_physics(idle_pose(legs), IDLE_LENGTH, springs), length=IDLE_LENGTH, mode="loop", fps=20),
        "sneak_idle": dict(pose=with_physics(sneak_idle_pose(legs), 6.0, springs), length=6.0, mode="loop", fps=20),
        "air_rise": dict(pose=with_physics(rise_pose(legs), AIR_LENGTH, springs), length=AIR_LENGTH, mode="loop", fps=30),
        "air_fall": dict(pose=with_physics(fall_pose(legs), AIR_LENGTH, springs), length=AIR_LENGTH, mode="loop", fps=30),
        "land": dict(pose=land_delta(legs), length=LAND_LENGTH, mode="add", fps=60),
        "death": dict(pose=death_pose, length=DEATH_LENGTH, mode="once", fps=30),
    }
    for name, fn, length in (("climb", climb_pose, 1.0), ("climb_idle", climb_idle_pose, 4.0), ("swim", swim_pose, 1.0), ("tread", tread_pose, 1.6),
                             ("crawl", crawl_pose, 1.0), ("sit", sit_pose, 4.0), ("sleep", sleep_pose, 5.0), ("glide", glide_pose, 2.0),
                             ("fly", fly_pose, 3.0), ("fly_move", fly_move_pose, 2.0)):
        clips[name] = dict(pose=with_physics(fn(legs), length, springs), length=length, mode="loop", fps=30)
    clips["climb"]["speed"] = CLIMB_STEP
    clips["swim"]["speed"] = SWIM_STRIDE
    clips["crawl"]["speed"] = CRAWL_STRIDE
    for name, g in GAITS.items():
        clips[name] = dict(pose=with_physics(locomotion(legs, g), g.cycle, springs), length=g.cycle, mode="loop", fps=60, speed=g.speed)
    for side in "rl":
        pose, weight = melee_pose(legs, side)
        clips["melee_" + side] = dict(pose=pose, weight=weight, length=MELEE_LENGTH, mode="once", fps=60)
    return clips


def motion_clips(legs, tracks_from, death_clip, stasis_clip):
    """Все клипы Астартес. Скорости аллюров — в GAITS; клиент сверяет с ними скорость тела."""
    springs = standard_springs()
    clips = {"misc.idle": tracks_from(with_physics(idle_pose(legs), IDLE_LENGTH, springs), IDLE_LENGTH, 144, True),
             "misc.sneak_idle": tracks_from(with_physics(sneak_idle_pose(legs), 6.0, springs), 6.0, 72, True)}
    for name, g in GAITS.items():
        steps = max(24, int(round(g.cycle * 60)))
        clips["move." + name] = tracks_from(with_physics(locomotion(legs, g), g.cycle, springs), g.cycle, steps, True)
    clips["misc.death"] = death_clip
    clips["misc.stasis"] = stasis_clip
    return clips
