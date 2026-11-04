#!/usr/bin/env python3
"""
Сводит звуки из tools/sounds/game/ (их пишет import_game_sounds.py) в готовые файлы tools/sounds/wav/ и wav_dread/: выстрел в игре собран из слоёв, здесь они смешиваются.
Потом tools/sounds/encode_ogg.py внутри Blender и tools/textures/gen_gun_fx.py (sounds.json). gen_gun_sounds.py эти файлы перезатрёт: синтез остался только для гильз, щелчков и метки попадания.

    python tools/sounds/mix_game_sounds.py
"""
import glob
import os
import sys

import numpy as np
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wwise_lookup as W

RATE = 44100
GAME = os.path.join(HERE, "game")
OUT, OUT_DREAD = os.path.join(HERE, "wav"), os.path.join(HERE, "wav_dread")
INDEX = {os.path.basename(p)[:-4]: p for p in glob.glob(os.path.join(GAME, "*", "*.wav"))}
BANKS = {}


def wems(bank, event):
    o = BANKS.setdefault(bank, W.read_hirc(bank))
    return W.event_wems(o, event) or set()


def load(wem):
    rate, a = wavfile.read(INDEX[str(wem)])
    a = a.astype(np.float64) / (32768 if a.dtype == np.int16 else 1)
    if a.ndim > 1:
        a = a.mean(axis=1)
    if rate != RATE:
        a = np.interp(np.arange(int(len(a) * RATE / rate)) * rate / RATE, np.arange(len(a)), a)
    return a


def stats(wem):
    a = load(wem)
    return len(a) / RATE, float(np.abs(a).max()), float(np.sqrt((a ** 2).mean()))


def pick(ids, lo, hi, n, min_peak=0.0, loudest=True):
    """Варианты нужной длины: самые громкие, порядок не зависит от запуска."""
    rows = []
    for w in sorted(ids):
        if str(w) not in INDEX:
            continue
        d, peak, rms = stats(w)
        if lo <= d <= hi and peak >= min_peak:
            rows.append((rms, w))
    rows.sort(reverse=loudest)
    return [w for _, w in rows[:n]]


def trim(a, level=0.01):
    """Убирает тишину в начале: выстрел должен звучать в момент нажатия."""
    i = np.argmax(np.abs(a) > level * max(1e-6, np.abs(a).max()))
    return a[max(0, i - 40):]


def hit_start(a, within=0.8, lead=0.012):
    """Файл начинается с момента удара: в записях шага удар идёт через 0,3-0,45 с после начала, и звук отставал от постановки ступни."""
    w = max(1, int(0.012 * RATE))
    part = a[:int(within * RATE)]
    energy = np.convolve(part * part, np.ones(w) / w, "same")
    i = max(0, int(np.argmax(energy)) - w - int(lead * RATE))
    out = a[i:].copy()
    n = min(len(out), int(0.003 * RATE))
    out[:n] *= np.linspace(0, 1, n)
    return out


def mix(*layers, length=None):
    """Слои (сигнал, усиление, задержка в секундах)."""
    n = max(len(x) + int(d * RATE) for x, _, d in layers)
    if length:
        n = min(n, int(length * RATE))
    out = np.zeros(n)
    for x, g, d in layers:
        i = int(d * RATE)
        m = min(n - i, len(x))
        if m > 0:
            out[i:i + m] += x[:m] * g
    return out


def fade(a, sec=0.06):
    n = min(len(a), int(sec * RATE))
    a = a.copy()
    a[-n:] *= np.linspace(1, 0, n)
    return a


def save(folder, name, a, peak=0.95, soft=True, fade_out=True):
    os.makedirs(folder, exist_ok=True)
    a = a / max(1e-6, np.abs(a).max()) * peak
    if soft:
        a = np.tanh(a * 1.25) / np.tanh(1.25)   # плотнее и громче без цифрового хруста
    if fade_out:
        a = fade(a)
    wavfile.write(os.path.join(folder, name + ".wav"), RATE, (a * 32767).astype(np.int16))
    print(name, f"{len(a) / RATE:.2f} c")


def main():
    # ---- болтер: тело выстрела, жёсткий хлопок у стрелка, хвост эха
    b2 = wems("wpn", "wpn_firearm_shoot_2d_bolter")
    b3 = wems("wpn", "wpn_firearm_shoot_3d_bolter")
    las = wems("wpn", "ai_imp_guard_lasgun")
    las_c = wems("chaos", "ai_cultist_lasgun")
    others = wems("wpn", "wpn_firearm_shoot_2d_bolt_pistol") | wems("wpn", "wpn_firearm_shoot_2d_bolt_carbine") | wems("wpn", "wpn_firearm_shoot_3d_bolter_heavy") | las
    own = b2 - others
    body = pick(own, 0.75, 0.85, 8)
    punch = pick(own, 0.55, 0.68, 6, 0.9)
    tails = pick(b2 - own - las, 2.9, 4.1, 6)
    print("болтер: тело", len(body), "хлопок", len(punch), "хвост", len(tails))
    for i in range(6):
        layers = [(trim(load(body[i % len(body)])), 1.0, 0.0), (trim(load(punch[i % len(punch)])), 0.5, 0.0)]
        if tails:
            layers.append((load(tails[i % len(tails)]), 1.5, 0.03))
        save(OUT, f"bolter_fire_{i}", mix(*layers, length=1.7))
    # ---- лазган гвардии: два своих слоя
    own_las = las - b3 - las_c
    las_a, las_b = pick(own_las, 0.45, 0.55, 10), pick(own_las, 0.95, 1.05, 10)
    print("лазган: тело", len(las_a), "хвост", len(las_b))
    for i in range(6):
        save(OUT, f"las_fire_{i}", mix((trim(load(las_a[i])), 1.0, 0.0), (trim(load(las_b[i])), 0.8, 0.0), length=1.1))
    # ---- тяжёлый болтер: пушка дредноута
    heavy = wems("wpn", "wpn_firearm_shoot_3d_bolter_heavy") - b3 - las
    hv_a = pick(heavy, 0.7, 0.8, 10)
    print("тяжёлый: тело", len(hv_a))
    for i in range(6):
        layers = [(trim(load(hv_a[i])), 1.0, 0.0)]
        if tails:
            layers.append((load(tails[i % len(tails)]), 1.6, 0.03))
        save(OUT_DREAD, f"dread_fire_{i}", mix(*layers, length=1.7))
    # ---- разрыв болта и попадание лазера: у пули и лазера общие поверхности, лазеру берём только своё
    bullet, laser = wems("common", "wpn_bullet_hit"), wems("common", "wpn_laser_hit")
    rocket = pick(wems("wpn", "wpn_projectile_exp_terminator_rocket"), 0.4, 1.3, 3)
    hits = pick(bullet - laser, 0.6, 1.2, 3, 0.5) or pick(bullet, 0.6, 1.2, 3, 0.5)
    print("разрыв: ракета", len(rocket), "пуля", len(hits))
    for i in range(3):
        layers = [(trim(load(hits[i % len(hits)])), 1.0, 0.0)]
        if rocket:
            layers.append((trim(load(rocket[i % len(rocket)])), 1.0, 0.0))
        save(OUT, f"bolt_explode_{i}", mix(*layers, length=1.4))
    las_only = pick(laser - bullet, 0.3, 1.0, 4, 0.3) or pick(laser, 0.3, 1.0, 4, 0.4)
    print("попадание лазера", len(las_only))
    for i, w in enumerate(las_only):
        save(OUT, f"las_hit_{i}", trim(load(w)))
    # ---- перезарядка: события общие на всё оружие, берём тяжёлые по звуку и короткие
    mo, mi = pick(wems("wpn", "wpn_firearm_reload_mag_out"), 0.6, 0.95, 2), pick(wems("wpn", "wpn_firearm_reload_mag_in"), 0.4, 0.7, 2)
    pull, rel = pick(wems("wpn", "wpn_firearm_reload_bolt_pull"), 0.3, 0.5, 2), pick(wems("wpn", "wpn_firearm_reload_bolt_release"), 0.4, 0.55, 2)
    save(OUT, "bolter_mag_out", trim(load(mo[0])), soft=False)
    save(OUT, "bolter_mag_in", trim(load(mi[0])), soft=False)
    save(OUT, "bolter_rack_back", trim(load(pull[0])), soft=False)
    save(OUT, "bolter_rack_fwd", trim(load(rel[0])), soft=False)
    save(OUT, "las_cell_out", trim(load(mo[1])), 0.8, soft=False)
    save(OUT, "las_cell_in", trim(load(mi[1])), 0.8, soft=False)
    save(OUT, "las_lever", trim(load(pull[1])), 0.7, soft=False)
    dry = pick(wems("wpn", "wpn_firearm_shoot_2d_bolter_empty_shoot"), 0.3, 0.6, 1)
    save(OUT, "gun_dry", trim(load(dry[0])), 0.8, soft=False)
    # ---- цепной меч: мотор, запуск, взмахи, укус
    idle = wems("wpn", "wpn_melee_chswd_idle_loop")
    start = wems("wpn", "wpn_melee_chswd_idle_start")
    loop = pick(idle - start, 5, 12, 1)
    save(OUT, "chainsword_engine", load(loop[0]), 0.85, soft=False, fade_out=False)
    for i, w in enumerate(pick(start, 1.3, 2.0, 2)):
        save(OUT, f"chainsword_start_{i}", trim(load(w)))
    slash = set()
    for k in range(1, 6):
        slash |= wems("wpn", f"wpn_melee_chswd_slash_{k}hit")
    for i, w in enumerate(pick(slash, 0.9, 1.8, 4)):
        save(OUT, f"chainsword_swing_{i}", trim(load(w)))
    impact = wems("wpn", "wpn_melee_heavy_fall_attack_chainsword_impact")
    bites = pick(impact, 1.5, 1.8, 3)
    for i, w in enumerate(bites):
        save(OUT, f"chainsword_bite_{i}", trim(load(w)))
    # ---- дредноут
    D = "imperium"
    for i, w in enumerate(pick(wems(D, "ai_imperium_dreadnought_step"), 0.8, 1.1, 6)):
        save(OUT_DREAD, f"dread_step_{i}", hit_start(load(w)))
    for i, w in enumerate(pick(wems(D, "ai_imperium_dreadnought_foley"), 1.0, 1.6, 6)):
        save(OUT_DREAD, f"dread_foley_{i}", load(w), 0.8, soft=False)
    for i, w in enumerate(pick(wems(D, "ai_imperium_dreadnought_servos"), 0.1, 0.3, 4)):
        save(OUT_DREAD, f"dread_servo_{i}", load(w), 0.8, soft=False)
    for i, w in enumerate(pick(wems(D, "ai_imperium_dreadnought_melee_stomp"), 2, 2.5, 3)):
        save(OUT_DREAD, f"dread_stomp_{i}", hit_start(load(w), 1.0))
    save(OUT_DREAD, "dread_idle", load(sorted(wems(D, "ai_imperium_dreadnought_idle_breath_start"))[0]), 0.7, soft=False, fade_out=False)
    fall = wems("chaos", "ai_chaos_helbrute_loco_death_fall")
    save(OUT_DREAD, "dread_fall", hit_start(load(sorted(fall)[0]), 1.0))
    punch_hits = pick(wems("wpn", "wpn_melee_heavy_fall_attack_pfist_impact"), 1.7, 2.6, 3)
    for i, w in enumerate(punch_hits):
        save(OUT_DREAD, f"dread_punch_{i}", hit_start(load(w), 1.0))


if __name__ == "__main__":
    main()
