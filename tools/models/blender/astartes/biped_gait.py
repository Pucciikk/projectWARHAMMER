"""
Движения двуногих в силовой броне: Астартес и Громовой воин (один скелет, разный вес). Ориентир автора — Fresh Animations:
колени и локти всегда работают, движение идёт волной от бёдер к кистям, тело никогда не замирает, у каждой висячей детали своя инерция.

Знаки Blender: перед у модели -Y, левая сторона +X, Z вверх.
X+ уводит висящую конечность назад, X- вперёд. Z+ поворачивает тело влево. Y- отводит левую руку наружу (правую Y+).
Ноги считает обратная кинематика: ступня стоит на земле и не скользит, колено и бедро получаются сами.

Скелет: root > pelvis > (thigh > shin > foot, tasset), pelvis > abdomen > chest > (head, backpack, pad, arm > forearm > hand > fingers, thumb).
"""
import math


def smooth(k):
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


def bump(t, at, width):
    """Плавный подъём в момент at и спад: разовое движение внутри зацикленного клипа."""
    return smooth((t - at) / width) * (1 - smooth((t - at - width * 1.6) / (width * 2)))


def track(sec, keys):
    """Ключи (время, значение[, 'in']) с плавным переходом; 'in' — разгон, как у падения или удара."""
    if sec <= keys[0][0]:
        return keys[0][1]
    for a, b in zip(keys, keys[1:]):
        if sec <= b[0]:
            k = (sec - a[0]) / (b[0] - a[0])
            k = k * k * k if len(b) > 2 else smooth(k)
            return a[1] + (b[1] - a[1]) * k
    return keys[-1][1]


def _ang(y, z):
    return math.atan2(z, y)


def _wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


class Build:
    """Настройки телосложения: одна и та же походка у Астартес и у более грузного Громового воина."""

    def __init__(self, cycle=0.86, duty=0.6, stride=0.74, lift=0.17, crouch=0.035, sway=1.0, arm=1.0,
                 run_cycle=0.56, run_duty=0.4, run_stride=1.02, run_lift=0.3, run_crouch=0.1, run_lean=13.0, bob=1.0):
        self.__dict__.update(locals())
        self.walk_speed = stride / (duty * cycle)
        self.run_speed = run_stride / (run_duty * run_cycle)


class Legs:
    def __init__(self, c, toe=0.2, even=False):
        self.toe = toe           # от оси голеностопа до носка, блоков: нужен, чтобы пятка поднималась вокруг носка
        self.even = even         # ступни в исходнике стоят вразнобой: при шаге нейтраль общая, иначе хромает
        self.rest = {}
        for s in "lr":
            H, K, A = c.bones["thigh_" + s][1], c.bones["shin_" + s][1], c.bones["foot_" + s][1]
            h, k, a = (H.y, H.z), (K.y, K.z), (A.y, A.z)
            l1, l2 = math.dist(h, k), math.dist(k, a)
            self.rest[s] = dict(h=h, k=k, a=a, l1=l1, l2=l2, a1=_ang(k[0] - h[0], k[1] - h[1]), a2=_ang(a[0] - k[0], a[1] - k[1]))

    def neutral_y(self, s):
        return self.rest[s]["a"][0]

    def gait_y(self, s):
        return (self.rest["l"]["a"][0] + self.rest["r"]["a"][0]) / 2 if self.even else self.rest[s]["a"][0]

    def ground(self, s):
        return self.rest[s]["a"][1]

    def solve(self, s, ty, tz, root_dz, pitch=0.0, pelvis_pitch=0.0):
        """Куда поставить голеностоп (y, z), root_dz — сдвиг бёдер, pitch — наклон ступни к земле, pelvis_pitch — наклон таза (его компенсируем)."""
        r = self.rest[s]
        hy, hz = r["h"][0], r["h"][1] + root_dz
        dy, dz = ty - hy, tz - hz
        d = min(math.hypot(dy, dz), (r["l1"] + r["l2"]) * 0.999)
        base = _ang(dy, dz)
        cos_a = (r["l1"] ** 2 + d * d - r["l2"] ** 2) / (2 * r["l1"] * d)
        alpha = math.acos(max(-1.0, min(1.0, cos_a)))
        a1 = base - alpha                 # колено вперёд, к -Y
        ky, kz = hy + r["l1"] * math.cos(a1), hz + r["l1"] * math.sin(a1)
        a2 = _ang(ty - ky, tz - kz)
        thigh = math.degrees(_wrap(a1 - r["a1"]))
        shin = math.degrees(_wrap(a2 - r["a2"])) - thigh
        foot = pitch - thigh - shin
        return {"thigh_" + s: {"rot": (thigh - pelvis_pitch, 0, 0)}, "shin_" + s: {"rot": (shin, 0, 0)}, "foot_" + s: {"rot": (foot, 0, 0)}}


def arm(p, s, sign, swing, elbow, out=4.0, wrist=0.0, curl=12.0, twist=0.0, thumb=None):
    """Рука: swing < 0 вперёд, elbow > 0 согнуть локоть (всегда немного согнут), curl сжать пальцы.
    Внимание: out — поворот вокруг вертикали (у висящей руки разворачивает локоть), а в сторону руку отводит twist: twist < 0 — наружу."""
    p["arm_" + s] = {"rot": (swing, sign * twist, -sign * out)}
    p["forearm_" + s] = {"rot": (-elbow, 0, 0)}
    p["hand_" + s] = {"rot": (wrist, 0, 0)}
    p["fingers_" + s] = {"rot": (0, sign * curl, 0)}
    p["thumb_" + s] = {"rot": (0, sign * (curl if thumb is None else thumb) * 0.5, 0)}


def secondary(p, swing_l, swing_r, thigh_l, thigh_r, shake=0.0):
    """Детали с инерцией: наплечники идут за рукой не полностью, юбка брони — за бедром."""
    p["pad_l"] = {"rot": (swing_l * 0.28, 0, shake * 2.0)}
    p["pad_r"] = {"rot": (swing_r * 0.28, 0, -shake * 2.0)}
    p["tasset_l"] = {"rot": (thigh_l * 0.55, 0, shake * 1.5 + max(0.0, -thigh_l) * 0.12)}
    p["tasset_r"] = {"rot": (thigh_r * 0.55, 0, -shake * 1.5 - max(0.0, -thigh_r) * 0.12)}


def _feet(legs, s, ph, duty, stride, lift):
    """Голеностоп в фазе цикла: на земле едет назад, пятка отрывается в конце опоры вокруг носка, в выносе нога идёт дугой, ставится на пятку."""
    y0 = legs.gait_y(s)
    g = legs.ground(s)
    if ph < duty:
        k = ph / duty
        y = y0 - stride / 2 + stride * k
        # сначала пятка: первые 12 % опоры носок ещё поднят и хлопает об землю
        slap = 17 * (1 - smooth(k / 0.14))
        roll = 44 * smooth((k - 0.66) / 0.34) ** 1.4      # отрыв пятки
        z = g + math.sin(math.radians(roll)) * legs.toe
        # X+ опускает носок: отрыв пятки положительный, постановка на пятку отрицательная
        return y - math.sin(math.radians(roll)) * legs.toe * 0.25, z, roll - slap
    k = (ph - duty) / (1 - duty)
    y = y0 + stride / 2 - stride * smooth(k)
    # подъём стопы быстрый, опускание длиннее: вынос не похож на синус
    z = g + math.sin(math.radians(44)) * legs.toe * (1 - smooth(k / 0.4)) + lift * math.sin(math.pi * k ** 0.8) ** 1.2
    pitch = 44 * (1 - smooth(k / 0.55)) - 17 * smooth((k - 0.55) / 0.45)
    return y, z, pitch


def gait(legs, b, cycle, duty, stride, lift, crouch, lean, arms, elbow0, dip):
    def pose(t):
        a = 2 * math.pi * t
        # таз: опускается в начале опоры, поднимается на середине; дважды за цикл
        dz = -crouch + b.bob * dip * math.cos(2 * a - 0.55)
        pitch = lean * 0.3
        p = {}
        for s, shift in (("l", 0.0), ("r", 0.5)):
            y, z, ft = _feet(legs, s, (t + shift) % 1, duty, stride, lift)
            p.update(legs.solve(s, y, z, dz, ft, pitch))
        thigh_l, thigh_r = p["thigh_l"]["rot"][0], p["thigh_r"]["rot"][0]
        side = math.sin(a + 0.5)              # вес на опорной ноге. Левая в опоре на первой половине цикла
        p["root"] = {"pos": (0.022 * b.sway * side, 0, dz)}
        p["pelvis"] = {"rot": (pitch, math.sin(a + 0.2) * 3.4 * b.sway, math.cos(a) * 5.0 * b.sway)}
        lag = 0.07
        # плечи идут против таза и с опозданием; поясница гасит половину
        p["abdomen"] = {"rot": (lean * 0.35, -math.sin(a + 0.2 - 0.25) * 2.6 * b.sway, -math.cos(a - 0.3) * 6.5 * b.sway)}
        breath = math.sin(a * 0.5) * 0.4
        p["chest"] = {"rot": (lean * 0.35 + 1.1 * math.cos(2 * a - 1.1) + breath, -math.sin(a - 0.45) * 1.2 * b.sway, -math.cos(a - 0.6) * 7.0 * b.sway)}
        # голова смотрит вперёд и гасит качание тела, плюс лёгкий кивок от шагов
        p["head"] = {"rot": (-lean * 0.65 - 1.4 * math.cos(2 * a - 1.6), math.sin(a - 0.5) * 1.6 * b.sway, math.cos(a - 0.7) * 8.5 * b.sway)}
        p["backpack"] = {"rot": (1.0 * math.cos(2 * a - 1.9), 0, math.cos(a - 1.0) * 0.8), "pos": (0, 0, -0.005 * math.cos(2 * a - 1.5))}
        # руки маятником против ног, локоть догоняет плечо с опозданием и сгибается на махе вперёд
        sw = math.sin(a - 2 * math.pi * lag + math.pi / 2)
        sw_l, sw_r = arms * sw, -arms * sw
        for s, sign, swing, ph in (("l", 1, sw_l, 0.0), ("r", -1, sw_r, math.pi)):
            bend = elbow0 + (0.5 + 0.5 * math.sin(a - 2 * math.pi * lag * 2 + ph - math.pi / 2)) * arms * 0.62
            out = 5.0 + 1.5 * math.cos(2 * a - 0.7 + ph) + max(0.0, -swing) * 0.05
            arm(p, s, sign, swing, bend, out, wrist=math.sin(a - 1.7 + ph) * 5 - 4, curl=18 + 8 * math.sin(a - 1.3 + ph), twist=swing * 0.14)
        secondary(p, sw_l, sw_r, thigh_l, thigh_r, math.cos(2 * a - 0.9))
        return p
    return pose


def walk(legs, b):
    return gait(legs, b, b.cycle, b.duty, b.stride, b.lift, b.crouch + 0.012, 3.0, 19.0 * b.arm, 14.0, 0.016)


def run(legs, b):
    """Бег: присел глубже, корпус вперёд, руки согнуты сильно и работают от плеча, есть короткая фаза полёта."""
    return gait(legs, b, b.run_cycle, b.run_duty, b.run_stride, b.run_lift, b.run_crouch, b.run_lean, 36.0 * b.arm, 60.0, 0.03)


IDLE_LENGTH = 12.0


def idle(legs, b):
    """Живое стояние. Дыхание постоянно, вес ходит с ноги на ногу, голова осматривается рывками, как у живого, кисть разминается, плечо иногда поправляется."""
    def pose(t):
        a = 2 * math.pi * t
        breathe = math.sin(a * 3)                      # 4 секунды на вдох и выдох
        shift = math.sin(a) * 0.65 + math.sin(a * 2 + 1.1) * 0.35
        dz = -b.crouch + 0.004 * breathe - 0.008 * abs(shift)
        p = {}
        for s, sign in (("l", 1), ("r", -1)):
            # опорная нога прямее, вторая расслаблена
            p.update(legs.solve(s, legs.neutral_y(s), legs.ground(s), dz - 0.012 * max(0.0, -shift * sign)))
        p["root"] = {"pos": (shift * 0.018, 0, dz)}
        p["pelvis"] = {"rot": (0, -shift * 1.3, shift * 2.2)}
        p["abdomen"] = {"rot": (0.6 + breathe * 0.6, shift * 0.8, -shift * 1.1)}
        p["chest"] = {"rot": (-0.8 - breathe * 1.3, shift * 0.7, -shift * 1.2)}
        # взгляд: перемещается быстро, держится подолгу
        look = track(t, [(0, 0), (0.1, 0), (0.13, 20), (0.31, 18), (0.34, -6), (0.5, -5), (0.53, -27), (0.66, -24), (0.7, 3), (0.86, 2), (0.9, 12), (0.97, 10), (1.0, 0)])
        nod = track(t, [(0, 3), (0.13, -2), (0.31, 0), (0.34, 5), (0.5, 4), (0.53, -3), (0.66, -1), (0.7, 6), (0.9, 2), (1.0, 3)])
        p["head"] = {"rot": (nod + breathe * 0.5, look * 0.09, look + math.sin(a * 5) * 0.6)}
        p["chest"]["rot"] = (p["chest"]["rot"][0], p["chest"]["rot"][1], p["chest"]["rot"][2] + look * 0.16)
        p["backpack"] = {"rot": (0.5 * math.sin(a * 3 + 0.8), 0, 0)}
        # левая кисть разминается, правая поправляет наплечник рывком плеча
        flex = bump(t, 0.2, 0.025) + bump(t, 0.76, 0.025)
        shrug = bump(t, 0.44, 0.03)
        roll_l = math.sin(a * 2 + 0.5)
        roll_r = math.sin(a * 2 + 2.4)
        arm(p, "l", 1, -2 + roll_l * 1.5 + breathe * 0.5, 12 + 3 * roll_l + 9 * flex, 5.5 + shift * 1.2 + breathe * 0.4,
            wrist=-5 + math.sin(a * 3) * 2 - 8 * flex, curl=20 + 44 * flex * (0.5 + 0.5 * math.sin(t * 240)), thumb=20 + 14 * flex)
        arm(p, "r", -1, -1 + roll_r * 1.5 + breathe * 0.5 - 7 * shrug, 13 + 3 * roll_r + 6 * shrug, 5.5 - shift * 1.2 + breathe * 0.4 + 6 * shrug,
            wrist=-5 + math.sin(a * 3 + 2) * 2, curl=26 + 6 * math.sin(a * 2), thumb=24)
        p["pad_l"] = {"rot": (0, 0, 0.5 + breathe * 0.5)}
        p["pad_r"] = {"rot": (-3 * shrug, 0, -0.5 - breathe * 0.5 - 7 * shrug), "pos": (0, 0, 0.012 * shrug)}
        secondary_t = p["thigh_l"]["rot"][0], p["thigh_r"]["rot"][0]
        p["tasset_l"] = {"rot": (secondary_t[0] * 0.5, 0, 0)}
        p["tasset_r"] = {"rot": (secondary_t[1] * 0.5, 0, 0)}
        return p
    return pose


def stasis(legs, b):
    """В стазисе или без сознания: неподвижно, голова опущена, руки висят. Для Громового воина в капсуле главы 5."""
    def pose(t):
        p = {}
        for s in "lr":
            p.update(legs.solve(s, legs.neutral_y(s), legs.ground(s), -b.crouch))
        p["root"] = {"pos": (0, 0, -b.crouch)}
        p["abdomen"] = {"rot": (2, 0, 0)}
        p["chest"] = {"rot": (3, 0, 0)}
        p["head"] = {"rot": (24, 0, 0)}
        arm(p, "l", 1, 1, 4, 3, wrist=3, curl=12)
        arm(p, "r", -1, 1, 4, 3, wrist=3, curl=12)
        return p
    return pose


MELEE_LENGTH = 0.85
MELEE_HIT = 0.3


def melee(legs, b, side="r", gain=1.0):
    """Удар сверху вниз и через корпус. Вся цепочка от бедра: таз, спина, плечо, локоть. side — бьющая рука, gain — размах (у воина с мечом в согнутой руке меньше)."""
    hit, off, hit_sign, off_sign = ("r", "l", -1, 1) if side == "r" else ("l", "r", 1, -1)

    def pose(t):
        sec = t * MELEE_LENGTH
        shoulder = track(sec, [(0, -2), (0.2, -112), (0.3, -62, "in"), (0.42, -52), (0.85, -2)])
        elbow = track(sec, [(0, 12), (0.2, 96), (0.3, 18, "in"), (0.42, 22), (0.85, 12)])
        out = track(sec, [(0, 5), (0.2, 26), (0.3, -6, "in"), (0.42, -4), (0.85, 5)])
        twist = track(sec, [(0, 0), (0.2, 26), (0.3, -32, "in"), (0.42, -28), (0.85, 0)])
        lean = track(sec, [(0, 0), (0.2, -6), (0.3, 13, "in"), (0.42, 11), (0.85, 0)])
        dz = track(sec, [(0, -b.crouch), (0.2, -b.crouch - 0.02), (0.3, -b.crouch - 0.09, "in"), (0.5, -b.crouch - 0.07), (0.85, -b.crouch)])
        p = {}
        p.update(legs.solve("l", legs.neutral_y("l") - 0.14, legs.ground("l"), dz))
        p.update(legs.solve("r", legs.neutral_y("r") + 0.16, legs.ground("r"), dz))
        p["root"] = {"pos": (0, 0, dz)}
        tw = -hit_sign * twist       # правая рука: закручиваемся влево, потом вправо; левая — наоборот
        p["pelvis"] = {"rot": (0, 0, tw * 0.3)}
        p["abdomen"] = {"rot": (lean * 0.45, 0, tw * 0.35)}
        p["chest"] = {"rot": (lean * 0.55, 0, tw * 0.45)}
        p["head"] = {"rot": (-lean * 0.7, 0, -tw * 0.75)}
        arm(p, hit, hit_sign, shoulder * gain, elbow * gain, out * gain, wrist=-8 * gain, curl=64, thumb=50)
        counter = track(sec, [(0, -2), (0.2, 14), (0.3, -28, "in"), (0.42, -24), (0.85, -2)])
        arm(p, off, off_sign, counter * gain, (30 + counter * -0.3) * gain, 9 * gain, wrist=-4 * gain, curl=34)
        p["pad_" + hit] = {"rot": (shoulder * 0.16 * gain, 0, hit_sign * max(0.0, out) * 0.7 * gain), "pos": (0, 0, 0.02 * smooth(-shoulder / 90) * gain)}
        p["pad_" + off] = {"rot": (counter * 0.2 * gain, 0, 0)}
        p["tasset_l"] = {"rot": (p["thigh_l"]["rot"][0] * 0.5, 0, 0)}
        p["tasset_r"] = {"rot": (p["thigh_r"]["rot"][0] * 0.5, 0, 0)}
        return p
    return pose


HURT_LENGTH = 0.4


def hurt(legs, b):
    """Вздрагивание от попадания поверх любого другого клипа: двигается только верх тела."""
    def pose(t):
        k = math.exp(-t * 5) * min(1.0, t * 8)
        return {"chest": {"rot": (-11 * k, 0, 6 * k)}, "head": {"rot": (9 * k, 0, -7 * k)}, "abdomen": {"rot": (-3 * k, 0, 2 * k)},
                "arm_l": {"rot": (9 * k, 0, -10 * k)}, "arm_r": {"rot": (6 * k, 0, 12 * k)}}
    return pose


DEATH_LENGTH = 2.7


def death(legs, b):
    """Колени подламываются, падает на одно колено и заваливается вперёд и набок. Руки тянутся до конца, потом обмякают."""
    def pose(t):
        sec = t * DEATH_LENGTH
        z = track(sec, [(0, -b.crouch), (0.25, -0.1), (0.8, -0.34), (1.1, -0.42), (1.5, -0.56, "in"), (1.62, -0.5), (1.75, -0.56), (2.7, -0.56)])
        y = track(sec, [(0, 0), (0.8, 0.02), (1.5, -0.22, "in"), (1.75, -0.28), (2.7, -0.28)])
        pitch = track(sec, [(0, 0), (0.25, -9), (0.8, 7), (1.1, 12), (1.55, 76, "in"), (1.65, 68), (1.78, 76), (2.7, 77)])
        roll = track(sec, [(0, 0), (0.8, 4), (1.1, 5), (1.55, 22, "in"), (2.7, 24)])
        p = {"root": {"pos": (0.05 * smooth(sec), y, z), "rot": (pitch, roll, 0)}}
        limp = smooth((sec - 1.05) / 0.4)
        stand = 1 - limp
        for s, sign, kneel in (("l", 1, 0.26), ("r", -1, 0.05)):
            q = legs.solve(s, legs.neutral_y(s) - kneel * smooth(sec / 0.8), legs.ground(s) + 0.02, z)
            bend = 58 if s == "l" else 24
            p["thigh_" + s] = {"rot": (q["thigh_" + s]["rot"][0] * stand + (-68 if s == "l" else -30) * limp, 0, sign * 7 * limp)}
            p["shin_" + s] = {"rot": (q["shin_" + s]["rot"][0] * stand + (bend + 34) * limp, 0, 0)}
            p["foot_" + s] = {"rot": (q["foot_" + s]["rot"][0] * stand + 34 * limp, 0, 0)}
            p["tasset_" + s] = {"rot": (p["thigh_" + s]["rot"][0] * 0.5, 0, sign * 7 * limp)}
        p["abdomen"] = {"rot": (track(sec, [(0, 0), (0.25, -8), (0.8, 10), (1.55, 12), (2.7, 9)]), 0, 4)}
        p["chest"] = {"rot": (track(sec, [(0, 0), (0.25, -12), (0.8, 8), (1.55, 10), (2.7, 7)]), 0, -5)}
        p["head"] = {"rot": (track(sec, [(0, 0), (0.25, -18), (0.8, 16), (1.55, -24), (1.8, 8), (2.7, 14)]), 8, track(sec, [(0, 0), (1.6, 18), (2.7, 24)]))}
        reach = track(sec, [(0, -2), (0.25, 8), (0.8, -34), (1.3, -62), (1.55, -96), (2.7, -116)])
        arm(p, "r", -1, reach, track(sec, [(0, 12), (0.8, 40), (1.5, 18), (2.7, 8)]), track(sec, [(0, 5), (1.5, 20), (2.7, 28)]), wrist=-10, curl=track(sec, [(0, 20), (0.8, 60), (1.3, 22), (2.7, 10)]))
        swing = track(sec, [(0, -2), (0.25, 14), (0.8, -18), (1.55, -48), (2.7, -38)])
        arm(p, "l", 1, swing, track(sec, [(0, 12), (0.8, 30), (1.55, 62), (2.7, 52)]), track(sec, [(0, 5), (2.7, 30)]), wrist=-8, curl=track(sec, [(0, 20), (0.8, 42), (2.7, 14)]))
        return p
    return pose


def with_seals(pose, length, gain):
    """Висячие печати: маятник с собственным периодом, толчки идут от движения тела. Период кратен длине клипа, иначе петля дёргается."""
    n = max(1, round(length / 0.62))

    def out(t):
        p = pose(t)
        a = 2 * math.pi * t * n
        p["seal_chest"] = {"rot": (-p.get("chest", {}).get("rot", (0, 0, 0))[0] * 0.8 + math.sin(a) * 3.5 * gain, 0, math.cos(a * 0.5 if n % 2 == 0 else a) * 3 * gain)}
        p["seal_thigh"] = {"rot": (-p.get("thigh_l", {}).get("rot", (0, 0, 0))[0] * 0.75 + math.sin(a - 0.8) * 3 * gain, 0, 3 + math.cos(a) * 2 * gain)}
        return p
    return out


def animations(legs, b, tracks_from):
    return {
        "misc.idle": tracks_from(with_seals(idle(legs, b), IDLE_LENGTH, 0.5), IDLE_LENGTH, 144, True),
        "move.walk": tracks_from(with_seals(walk(legs, b), b.cycle, 1.6), b.cycle, 32, True),
        "move.run": tracks_from(with_seals(run(legs, b), b.run_cycle, 3.0), b.run_cycle, 26, True),
        "misc.stasis": tracks_from(stasis(legs, b), 1.0, 1, True),
        "attack.melee": tracks_from(melee(legs, b), MELEE_LENGTH, 34, False),
        "misc.hurt": tracks_from(hurt(legs, b), HURT_LENGTH, 14, False),
        "misc.death": tracks_from(death(legs, b), DEATH_LENGTH, 81, False),
    }
