"""
Движения дредноута. Ноги считаются обратной кинематикой: задаём, где стоит ступня, колено и бедро получаются сами, поэтому ступни не проваливаются и не скользят по земле.
Вес передаётся тем, что всё запаздывает за шагом: корпус проседает после постановки ноги, затем его догоняют руки, стволы и кулак.

Знаки Blender: поворот по +X поднимает направление +Y к +Z. Вперёд у машины -Y, поэтому X+ опускает вперёд смотрящий ствол и уводит висящую ногу назад.
Звуковые метки клипа (имена step, step_run, servo, claw, shove, clank, thud, thud_big) разбирает DreadConceptEntity.
"""
import math

CYCLE = 0.9          # секунд на два шага
DUTY = 0.6           # доля цикла, когда ступня на земле
STRIDE = 1.1         # блоков проходит ступня относительно корпуса за опору
WALK_SPEED = STRIDE / (DUTY * CYCLE)     # блоков в секунду при нормальной скорости клипа: его знает Java
CROUCH = 0.09        # насколько машина всегда присела: прямые ноги не передают вес


def _ang(y, z):
    return math.atan2(z, y)


def _wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def smooth(k):
    k = max(0.0, min(1.0, k))
    return k * k * (3 - 2 * k)


def pulse(tau, attack=0.03, decay=0.09):
    """Удар: быстрый подъём и затухание. tau — время после события, в секундах."""
    if tau < 0:
        return 0.0
    return min(1.0, tau / attack) * math.exp(-max(0.0, tau - attack) / decay)


class Legs:
    """Точки ног в покое (y, z) и решение обратной задачи для каждой стороны."""

    def __init__(self, c):
        self.rest = {}
        for s in "lr":
            H, K, A = c.bones["thigh_" + s][1], c.bones["shin_" + s][1], c.bones["foot_" + s][1]
            h, k, a = (H.y, H.z), (K.y, K.z), (A.y, A.z)
            l1, l2 = math.dist(h, k), math.dist(k, a)
            self.rest[s] = dict(h=h, k=k, a=a, l1=l1, l2=l2, a1=_ang(k[0] - h[0], k[1] - h[1]), a2=_ang(a[0] - k[0], a[1] - k[1]))

    def neutral_y(self, s):
        return self.rest[s]["h"][0] - 0.02

    def ground(self, s):
        return self.rest[s]["a"][1]

    def solve(self, s, ty, tz, root_dz, pitch=0.0):
        """Куда поставить ступню (y, z), root_dz — сдвиг корпуса. Возвращает позы костей бедра, голени, стопы."""
        r = self.rest[s]
        hy, hz = r["h"][0], r["h"][1] + root_dz
        dy, dz = ty - hy, tz - hz
        d = min(math.hypot(dy, dz), (r["l1"] + r["l2"]) * 0.998)
        base = _ang(dy, dz)
        cos_a = (r["l1"] ** 2 + d * d - r["l2"] ** 2) / (2 * r["l1"] * d)
        alpha = math.acos(max(-1.0, min(1.0, cos_a)))
        a1 = base - alpha                 # колено вперёд, к -Y
        ky, kz = hy + r["l1"] * math.cos(a1), hz + r["l1"] * math.sin(a1)
        a2 = _ang(ty - ky, tz - kz)
        thigh = math.degrees(_wrap(a1 - r["a1"]))
        shin = math.degrees(_wrap(a2 - r["a2"])) - thigh
        foot = pitch - thigh - shin
        return {"thigh_" + s: {"rot": (thigh, 0, 0)}, "shin_" + s: {"rot": (shin, 0, 0)}, "foot_" + s: {"rot": (foot, 0, 0)}}


CLAW_DIRS = ((0.7, 0.7), (-0.7, 0.7), (-0.7, -0.7), (0.7, -0.7))


def claws(p, opened):
    """Раскрытие клешни, градусы. Малый поворот вокруг оси, поперечной пальцу: кончик уходит от центра."""
    for i, (dx, dz) in enumerate(CLAW_DIRS):
        p[f"claw_{i}"] = {"rot": (-dz * opened, 0, dx * opened)}


def _gait(legs, cycle, duty, stride, lift, crouch, lean, arms, sway, dip):
    def foot_at(s, ph):
        """Положение ступни в фазе цикла: на земле едет назад с постоянной скоростью, в выносе идёт дугой вперёд."""
        y0 = legs.neutral_y(s)
        g = legs.ground(s)
        if ph < duty:
            k = ph / duty
            # пятка отрывается в конце опоры
            return y0 - stride / 2 + stride * k, g, 10 * smooth((k - 0.82) / 0.18)
        k = (ph - duty) / (1 - duty)
        y = y0 + stride / 2 - stride * smooth(k)
        z = g + lift * math.sin(math.pi * k) ** 1.2
        # носок сначала вниз, к концу выноса вверх: нога ставится на пятку и тут же хлопает всей ступнёй
        pitch = 22 * (1 - k) ** 3 - 14 * math.sin(math.pi * k) * smooth((k - 0.35) / 0.65)
        return y, z, pitch

    def pose(t):
        sec = t * cycle
        half = cycle / 2
        tau = sec % half      # время после последней постановки ноги
        hit = pulse(tau) + pulse(tau - half)
        # корпус: проседает после удара ступни, между шагами поднимается
        dz = -crouch - dip * hit + 0.022 * math.cos(4 * math.pi * t)
        p = {}
        for s, shift in (("l", 0.0), ("r", 0.5)):
            y, z, pitch = foot_at(s, (t + shift) % 1)
            p.update(legs.solve(s, y, z, dz, pitch))
        lag = 0.08       # доля цикла: верх отстаёт от ног
        s1 = math.sin(2 * math.pi * (t - lag))
        c2 = pulse((sec - 0.05) % half)
        # перевалка на опорную ногу, разворот бёдер против хода
        p["root"] = {"pos": (math.sin(2 * math.pi * t) * 0.045 * sway, 0, dz), "rot": (-lean, 0, 0)}
        p["pelvis"] = {"rot": (0, math.sin(2 * math.pi * t) * 3.5 * sway, math.cos(2 * math.pi * t) * 3.5 * sway)}
        p["torso"] = {"rot": (3.5 + 2.6 * c2 * (dip / 0.055), -s1 * 4.0 * sway, -math.cos(2 * math.pi * (t - lag)) * 6.0 * sway)}
        # руки маятником, от удара вздрагивают с опозданием
        jolt = pulse((sec - 0.09) % half, 0.03, 0.11)
        arm = math.sin(2 * math.pi * (t - lag * 1.6))
        p["arm_l"] = {"rot": (arm * 9 * arms + 3 * jolt, 0, 2.2 * jolt)}
        p["fist_l"] = {"rot": (arm * 7 * arms - 4 * jolt, 0, 0)}
        p["arm_r"] = {"rot": (-arm * 4.5 * arms + 2 * jolt, 0, -1.5 * jolt)}
        p["barrels"] = {"pos": (0, 0.012 * jolt, -0.006 * jolt)}
        claws(p, 3 + 5 * jolt)
        return p
    return pose


def walk(legs):
    return _gait(legs, CYCLE, DUTY, STRIDE, 0.27, CROUCH, 0.0, 1.0, 1.0, 0.055)


RUN_CYCLE = 0.62     # секунд на два шага бегом
RUN_DUTY = 0.5       # на земле половину цикла: у тяжёлой машины нет фазы полёта, это тяжёлая рысь
RUN_STRIDE = 1.35
RUN_SPEED = RUN_STRIDE / (RUN_DUTY * RUN_CYCLE)


def run(legs):
    """Бег: присел глубже, наклон вперёд, руки ходят шире, корпус бьёт сильнее."""
    return _gait(legs, RUN_CYCLE, RUN_DUTY, RUN_STRIDE, 0.42, 0.17, 9.0, 2.0, 1.5, 0.1)


WALK_EVENTS = ((0.0, "step"), (CYCLE / 2, "step"))
RUN_EVENTS = ((0.0, "step_run"), (RUN_CYCLE / 2, "step_run"))
IDLE_LENGTH = 8.0
IDLE_EVENTS = ((2.3, "servo"), (5.3, "servo"), (6.75, "servo"))


def idle(legs):
    """Живое стояние: дыхание, переминание с ноги на ногу, корпус осматривается, кулак сжимается, пушка подправляется."""
    def bump(t, at, width):
        return smooth((t - at) / width) * (1 - smooth((t - at - width * 1.6) / (width * 2)))

    def pose(t):
        a = 2 * math.pi * t
        breathe = math.sin(a * 4)
        shift = math.sin(a) * 0.6 + math.sin(a * 2 + 1.1) * 0.4        # вес с ноги на ногу
        dz = -CROUCH + 0.014 * breathe - 0.012 * abs(shift)
        p = {}
        for s, side in (("l", 1), ("r", -1)):
            # ступни стоят чуть вразлёт и не двигаются, колено работает
            y0 = legs.neutral_y(s) + side * 0.05
            p.update(legs.solve(s, y0, legs.ground(s), dz - 0.014 * max(0.0, shift * side)))
        look = math.sin(a) * 7 + math.sin(a * 3 + 0.8) * 2.5 + 7 * bump(t, 0.58, 0.05) - 9 * bump(t, 0.3, 0.05)
        p["root"] = {"pos": (shift * 0.045, 0, dz)}
        p["pelvis"] = {"rot": (0, shift * 2.0, look * 0.15)}
        p["torso"] = {"rot": (2.5 + breathe * 0.8 + math.sin(a * 2) * 1.0, -shift * 1.6, look)}
        flex = bump(t, 0.28, 0.035)
        gun = bump(t, 0.64, 0.05)
        check = bump(t, 0.83, 0.04)
        p["arm_l"] = {"rot": (2 + math.sin(a * 2 + 0.5) * 3 - 10 * flex, 0, 2 + math.sin(a + 2.0) * 2.5)}
        p["fist_l"] = {"rot": (math.sin(a * 3) * 3 + 16 * flex - 7 * check, 0, -12 * check)}
        p["arm_r"] = {"rot": (2 + math.sin(a * 2 + 2.4) * 2.4 - 12 * gun + 4 * check, 0, -1.5 + math.sin(a + 0.7) * 2.2)}
        p["barrels"] = {"pos": (0, 0.03 * gun, 0)}
        claws(p, 4 + math.sin(a * 3) * 2 + 20 * flex - 4 * check)
        return p
    return pose


def fire():
    def pose(t):
        k = math.exp(-t * 7) * (1 if t > 0.03 else t / 0.03)
        return {"arm_r": {"rot": (-9 * k, 0, 1.5 * k), "pos": (0, 0.05 * k, 0)}, "barrels": {"pos": (0, 0.13 * k, 0)}}
    return pose


CLAW_LENGTH = 1.35
CLAW_EVENTS = ((0.04, "servo"), (0.42, "servo"), (0.56, "claw"))
CLAW_HIT = 0.56       # секунда смыкания: столько же ждёт DreadConceptEntity перед уроном


def claw_strike():
    """Удар клешнёй: корпус закручивается, рука уходит назад и вверх, пальцы раскрываются. Рывок вперёд, клешня смыкается на цели, рвёт её поворотом кисти, рука тяжело возвращается."""
    def track(sec, keys):
        if sec <= keys[0][0]:
            return keys[0][1]
        for a, b in zip(keys, keys[1:]):
            if sec <= b[0]:
                k = (sec - a[0]) / (b[0] - a[0])
                k = k * k * k if len(b) > 2 else smooth(k)
                return a[1] + (b[1] - a[1]) * k
        return keys[-1][1]

    def pose(t):
        sec = t * CLAW_LENGTH
        # замах вверх (X отрицательный), удар сверху до уровня цели перед собой
        shoulder = track(sec, [(0, 0), (0.38, 34), (0.56, -8, "in"), (0.7, -4), (0.86, -7), (1.35, 0)])
        wide = track(sec, [(0, 0), (0.38, 12), (0.56, -6), (1.35, 0)])
        wrist = track(sec, [(0, 0), (0.38, 26), (0.56, -2, "in"), (0.86, -2), (1.35, 0)])
        opened = track(sec, [(0, 3), (0.34, 36), (0.5, 40), (0.56, -9, "in"), (0.86, -8), (1.05, 6), (1.35, 3)])
        twist = track(sec, [(0, 0), (0.38, -24), (0.56, 26, "in"), (0.86, 20), (1.35, 0)])
        lurch = track(sec, [(0, 2), (0.38, -4), (0.56, 9, "in"), (0.86, 7), (1.35, 2)])
        rip = math.sin(max(0.0, sec - 0.58) * 24) * 7 * (1 - smooth((sec - 0.58) / 0.3)) if sec > 0.58 else 0.0
        reach = track(sec, [(0, 0), (0.38, 0.14), (0.56, -0.28, "in"), (0.86, -0.22), (1.35, 0)])
        # плечевой щиток почти неподвижен: удар идёт из локтя, кисть выбрасывает поршень
        p = {"arm_l": {"rot": (-shoulder * 0.18, 0, wide * 0.5)},
             "fist_l": {"rot": (-shoulder * 0.8 - wrist * 0.4, rip, 0), "pos": (0, reach * 0.7, 0)},
             "torso": {"rot": (lurch, 0, twist)}}
        claws(p, opened)
        return p
    return pose


SHOVE_LENGTH = 0.9
SHOVE_EVENTS = ((0.02, "servo"), (0.3, "shove"))
SHOVE_HIT = 0.3       # секунда удара: столько же ждёт DreadConceptEntity


def shove():
    """Толчок: кулак коротко отведён назад вместе с плечом и корпусом, потом прямой выброс вперёд на поршне, пальцы сжаты. Без замаха вверх: быстро, чтобы отгонять толпу."""
    def track(sec, keys):
        if sec <= keys[0][0]:
            return keys[0][1]
        for a, b in zip(keys, keys[1:]):
            if sec <= b[0]:
                k = (sec - a[0]) / (b[0] - a[0])
                k = k * k * k if len(b) > 2 else smooth(k)
                return a[1] + (b[1] - a[1]) * k
        return keys[-1][1]

    def pose(t):
        sec = t * SHOVE_LENGTH
        reach = track(sec, [(0, 0), (0.18, 0.3), (0.3, -0.62, "in"), (0.42, -0.56), (0.9, 0)])
        lift = track(sec, [(0, 0), (0.18, 6), (0.3, -10, "in"), (0.42, -8), (0.9, 0)])
        twist = track(sec, [(0, 0), (0.18, -20), (0.3, 24, "in"), (0.42, 20), (0.9, 0)])
        lurch = track(sec, [(0, 2), (0.18, -3), (0.3, 10, "in"), (0.42, 8), (0.9, 2)])
        p = {"arm_l": {"rot": (lift * 0.2, 0, 0)},
             "fist_l": {"rot": (lift, 0, 0), "pos": (0, reach, 0)},
             "torso": {"rot": (lurch, 0, twist)}}
        claws(p, track(sec, [(0, 3), (0.18, 10), (0.28, -10, "in"), (0.5, -8), (0.9, 3)]))
        return p
    return pose


DEATH_LENGTH = 5.4
DEATH_EVENTS = ((0.05, "clank"), (0.7, "clank"), (1.2, "servo"), (1.65, "clank"), (2.05, "clank"), (2.92, "thud_big"), (4.1, "thud"))


def death(legs):
    """Шатается, ноги подламываются, заваливается на бок, ударяется, перекатывается на спину и затихает."""
    def track(sec, keys):
        """Ключи (время, значение) с плавным переходом; вид 'in' — падение с разгоном."""
        if sec <= keys[0][0]:
            return keys[0][1]
        for a, b in zip(keys, keys[1:]):
            if sec <= b[0]:
                k = (sec - a[0]) / (b[0] - a[0])
                k = k * k * k if len(b) > 2 else smooth(k)
                return a[1] + (b[1] - a[1]) * k
        return keys[-1][1]

    def pose(t):
        sec = t * DEATH_LENGTH
        # ---- шатание: размах растёт, потом падение
        grow = smooth(sec / 2.0) * (1 - smooth((sec - 2.2) / 0.3))
        wob = math.sin(sec * 7.4) * 5.5 * grow + math.sin(sec * 3.1) * 7 * grow
        wob2 = math.sin(sec * 5.2 + 1) * 5 * grow
        roll = track(sec, [(0, 0), (2.15, 8), (2.92, 90, "in"), (3.04, 84), (3.15, 90), (3.45, 90), (4.1, 18, "in"), (4.25, 26), (4.45, 16), (5.4, 15)]) + wob
        back = track(sec, [(0, 0), (0.25, -7), (1.0, 3), (2.15, -4), (2.92, -6), (3.45, -8), (4.1, -86, "in"), (4.25, -80), (4.45, -86), (5.4, -86)]) + wob2
        # ---- колени подламываются, корпус идёт вниз и в сторону падения; лёжа центр корпуса низко над землёй
        z = track(sec, [(0, -CROUCH), (0.25, -0.2), (0.7, -0.12), (1.25, -0.28), (1.7, -0.2), (2.15, -0.36), (2.92, -0.55, "in"), (3.04, -0.47), (3.15, -0.55), (3.45, -0.55), (4.1, -0.6, "in"), (4.25, -0.5), (4.45, -0.6), (5.4, -0.6)])
        x = track(sec, [(0, 0), (2.15, 0.15), (2.92, 1.55, "in"), (3.45, 1.55), (4.1, 0.95, "in"), (5.4, 0.95)])
        yy = track(sec, [(0, 0), (0.25, 0.1), (1.0, 0.02), (2.15, 0.06), (3.45, 0.1), (4.1, 0.3), (5.4, 0.3)])
        p = {"root": {"pos": (x, yy, z), "rot": (back, roll, 0)}}
        # ---- ноги: пока стоит, ступни на земле; падая, отрываются и повисают согнутыми
        stand = 1 - smooth((sec - 2.05) / 0.3)
        limp = smooth((sec - 2.2) / 0.5)
        for s, sign in (("l", 1), ("r", -1)):
            q = legs.solve(s, legs.neutral_y(s) + sign * 0.12 * math.sin(sec * 2.1 + sign), legs.ground(s), min(z, -CROUCH) * 0.9)
            knee = 18 + 26 * limp + 7 * math.sin(sec * 1.7 + sign) * limp
            p["thigh_" + s] = {"rot": (q["thigh_" + s]["rot"][0] * stand + (-22 - sign * 9) * limp, 0, sign * 6 * limp)}
            p["shin_" + s] = {"rot": (q["shin_" + s]["rot"][0] * stand + knee * limp, 0, 0)}
            p["foot_" + s] = {"rot": (q["foot_" + s]["rot"][0] * stand + 26 * limp, 0, 0)}
        # ---- руки: сначала дёргаются, потом висят, при ударе подлетают и падают
        flail = grow
        slam = pulse(sec - 2.92, 0.05, 0.16) + pulse(sec - 4.1, 0.05, 0.16)
        drop = smooth((sec - 2.0) / 0.9)
        p["torso"] = {"rot": (6 * drop + math.sin(sec * 6) * 3 * flail, math.sin(sec * 4.3) * 5 * flail, math.sin(sec * 3.3) * 9 * flail - 12 * drop)}
        p["arm_l"] = {"rot": (math.sin(sec * 5.1) * 16 * flail + 24 * drop - 20 * slam, 0, 26 * drop + 12 * slam)}
        p["fist_l"] = {"rot": (math.sin(sec * 7) * 12 * flail + 14 * drop, 0, 0)}
        p["arm_r"] = {"rot": (math.sin(sec * 4.3 + 1) * 13 * flail + 34 * drop - 16 * slam, 0, -22 * drop - 10 * slam)}
        p["barrels"] = {"pos": (0, 0.06 * math.sin(sec * 11) * flail, 0)}
        p["pelvis"] = {"rot": (0, 0, 0)}
        claws(p, 3 + 22 * drop + 8 * slam)
        return p
    return pose


def dormant(legs):
    """Без пилота: неподвижно, присел, корпус и руки опущены вперёд. Клип без движения, чтобы переход в него и из него был плавным."""
    def pose(t):
        dz = -0.2
        p = {}
        for s, side in (("l", 1), ("r", -1)):
            p.update(legs.solve(s, legs.neutral_y(s) + side * 0.05, legs.ground(s), dz))
        p["root"] = {"pos": (0, 0, dz)}
        p["pelvis"] = {"rot": (0, 0, 0)}
        p["torso"] = {"rot": (15, 0, 0)}
        p["arm_l"] = {"rot": (4, 0, 2)}
        p["fist_l"] = {"rot": (20, 0, 0)}
        p["arm_r"] = {"rot": (8, 0, -2)}
        p["barrels"] = {"pos": (0, 0, 0)}
        claws(p, 8)
        return p
    return pose


def reverse(pose):
    return lambda t: pose(1 - t)


def with_hose(pose):
    """Шланг держится у плеча, нижний конец идёт за запястьем: поворот меньше, чем у кисти."""
    def out(t):
        p = pose(t)
        if "fist_l" in p:
            x = p["fist_l"].get("rot", (0, 0, 0))[0]
            p["arm_hose"] = {"rot": (x * 0.75, 0, 0)}
        return p
    return out


def animations(legs, tracks_from):
    return {
        "move.walk": tracks_from(with_hose(walk(legs)), CYCLE, 40, True, WALK_EVENTS),
        "move.run": tracks_from(with_hose(run(legs)), RUN_CYCLE, 30, True, RUN_EVENTS),
        # задний ход: тот же шаг наоборот. Нога ставится там, где в обычном шаге отрывалась
        "move.back": tracks_from(with_hose(reverse(walk(legs))), CYCLE, 40, True, ((1 - DUTY, "step"), ((1.5 - DUTY) % 1, "step"))),
        "misc.idle": tracks_from(with_hose(idle(legs)), IDLE_LENGTH, 96, True, IDLE_EVENTS),
        "misc.dormant": tracks_from(with_hose(dormant(legs)), 1.0, 1, True),
        "attack.fire": tracks_from(fire(), 0.35, 10, False),
        "attack.melee": tracks_from(with_hose(claw_strike()), CLAW_LENGTH, 40, False, CLAW_EVENTS),
        "attack.shove": tracks_from(with_hose(shove()), SHOVE_LENGTH, 27, False, SHOVE_EVENTS),
        "misc.death": tracks_from(with_hose(death(legs)), DEATH_LENGTH, 108, False, DEATH_EVENTS),
    }
