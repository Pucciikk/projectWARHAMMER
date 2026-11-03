#!/usr/bin/env python3
"""
Звуки оружия, синтез на numpy: tools/sounds/wav/*.wav (в git не нужны). В OGG их переводит Blender (tools/sounds/encode_ogg.py),
Minecraft читает только OGG Vorbis.

    python3 tools/sounds/gen_gun_sounds.py

Лазган: сухой треск разряда и падающий свист. Болтер: хлопок вышибного заряда, рёв реактивной ракетки и лязг затвора.
Вариантов выстрела несколько: одинаковый звук подряд быстро начинает раздражать.
"""
import os

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

RATE = 44100
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wav")
os.makedirs(OUT, exist_ok=True)


def t(sec):
    return np.arange(int(sec * RATE)) / RATE


def noise(sec, rng):
    return rng.standard_normal(int(sec * RATE))


def band(x, lo, hi):
    return sosfilt(butter(3, [lo, hi], btype="band", fs=RATE, output="sos"), x)


def low(x, f):
    return sosfilt(butter(3, f, btype="low", fs=RATE, output="sos"), x)


def high(x, f):
    return sosfilt(butter(3, f, btype="high", fs=RATE, output="sos"), x)


def env(n, attack, decay):
    """Быстрый подъём, экспоненциальный спад."""
    tt = np.arange(n) / RATE
    return np.minimum(tt / max(attack, 1e-5), 1.0) * np.exp(-np.maximum(tt - attack, 0) / decay)


def sweep(sec, f0, f1, curve=4.0):
    """Падающий тон: частота спадает по экспоненте."""
    tt = t(sec)
    f = f1 + (f0 - f1) * np.exp(-tt / sec * curve)
    return np.sin(2 * np.pi * np.cumsum(f) / RATE)


def mix(length, *parts):
    n = int(length * RATE)
    out = np.zeros(n)
    for delay, x, gain in parts:
        i = int(delay * RATE)
        m = min(n - i, len(x))
        if m > 0:
            out[i:i + m] += x[:m] * gain
    return out


def echo(x, delay, gain, rng_len=3):
    """Простое эхо помещения: придаёт выстрелу объём."""
    out = x.copy()
    for k in range(1, rng_len + 1):
        i = int(delay * k * RATE)
        if i < len(x):
            out[i:] += x[:-i] * gain ** k
    return out


def save(name, x, peak=0.92):
    x = x / max(1e-6, np.max(np.abs(x))) * peak
    # мягкое ограничение: щелчки без цифрового хруста
    x = np.tanh(x * 1.6) / np.tanh(1.6)
    fade = int(0.004 * RATE)
    x[-fade:] *= np.linspace(1, 0, fade)
    wavfile.write(os.path.join(OUT, name + ".wav"), RATE, (x * 32767).astype(np.int16))


def click(rng, f=3200, decay=0.008, sec=0.05, q=0.5):
    """Металлический щелчок: шум в полосе плюс звон."""
    n = noise(sec, rng)
    tone = np.sin(2 * np.pi * f * t(sec)) * 0.6 + np.sin(2 * np.pi * f * 1.51 * t(sec)) * 0.3
    return (band(n, f * q, min(f * 2.2, 20000)) + tone * 0.5) * env(len(n), 0.0005, decay)


def thump(sec, f, decay):
    return np.sin(2 * np.pi * np.cumsum(f + 60 * np.exp(-t(sec) / 0.03)) / RATE) * env(int(sec * RATE), 0.001, decay)


# ---------------------------------------------------------------- лазган
for v in range(4):
    rng = np.random.default_rng(100 + v)
    pitch = 1 + (v - 1.5) * 0.04
    crack = high(noise(0.09, rng), 1800) * env(int(0.09 * RATE), 0.0004, 0.014)
    zap = sweep(0.2, 3400 * pitch, 420 * pitch, 6) * env(int(0.2 * RATE), 0.0006, 0.05)
    zap2 = sweep(0.16, 5200 * pitch, 900 * pitch, 7) * env(int(0.16 * RATE), 0.0006, 0.03)
    sizzle = band(noise(0.35, rng), 2500, 9000) * env(int(0.35 * RATE), 0.004, 0.09)
    body = thump(0.14, 120, 0.025)
    save(f"las_fire_{v}", echo(mix(0.5, (0, crack, 1.0), (0, zap, 0.8), (0, zap2, 0.35), (0.004, sizzle, 0.22), (0, body, 0.55)), 0.055, 0.2))
rng = np.random.default_rng(1)
save("las_hit", mix(0.35, (0, high(noise(0.3, rng), 2500) * env(int(0.3 * RATE), 0.001, 0.07), 1.0), (0, sweep(0.12, 1800, 500) * env(int(0.12 * RATE), 0.001, 0.03), 0.4)))
# зарядка лазпакета: нарастающий писк конденсатора
hum = sweep(0.7, 300, 300, 1) * 0
tt = t(0.7)
save("las_charge", (np.sin(2 * np.pi * np.cumsum(500 + 2600 * (tt / 0.7) ** 2) / RATE) * np.minimum(tt / 0.3, 1) * np.exp(-np.maximum(tt - 0.55, 0) / 0.05)), 0.5)
save("las_cell_out", mix(0.25, (0, click(rng, 2400, 0.01), 1), (0.02, click(rng, 1200, 0.03, 0.15), 0.8)))
save("las_cell_in", mix(0.3, (0, click(rng, 1900, 0.012), 1), (0.035, thump(0.1, 180, 0.03), 0.8), (0.05, click(rng, 3200, 0.01), 0.8)))
save("las_lever", mix(0.2, (0, click(rng, 4200, 0.006), 1), (0.06, click(rng, 2800, 0.012), 0.8)))

# ---------------------------------------------------------------- болтер
for v in range(4):
    rng = np.random.default_rng(200 + v)
    p = 1 + (v - 1.5) * 0.03
    blast = low(noise(0.2, rng), 3200) * env(int(0.2 * RATE), 0.0005, 0.035)
    boom = thump(0.3, 58 * p, 0.09)
    crack = high(noise(0.05, rng), 3000) * env(int(0.05 * RATE), 0.0003, 0.01)
    # ракетка: шипение быстро уходит вверх и вдаль
    hiss = high(noise(0.45, rng), 1500) * env(int(0.45 * RATE), 0.012, 0.13)
    whoosh = band(noise(0.5, rng), 500, 2600) * env(int(0.5 * RATE), 0.03, 0.12)
    bolt = click(rng, 1500, 0.02, 0.09)
    save(f"bolter_fire_{v}", echo(mix(0.75, (0, blast, 1.0), (0, boom, 1.1), (0, crack, 0.8), (0.012, hiss, 0.42), (0.02, whoosh, 0.5), (0.05, bolt, 0.55)), 0.08, 0.26))
rng = np.random.default_rng(3)
# разрыв масс-реактивного снаряда: двойной удар
for v in range(3):
    r = np.random.default_rng(300 + v)
    save(f"bolt_explode_{v}", echo(mix(0.9, (0, low(noise(0.4, r), 2400) * env(int(0.4 * RATE), 0.001, 0.08), 1.0), (0, thump(0.5, 46, 0.16), 1.2),
                                       (0.03, high(noise(0.3, r), 2500) * env(int(0.3 * RATE), 0.001, 0.05), 0.4)), 0.11, 0.3))
save("bolter_mag_out", mix(0.32, (0, click(rng, 1300, 0.018, 0.1), 1), (0.03, click(rng, 2600, 0.01), 0.7), (0.05, thump(0.12, 150, 0.04), 0.5)))
save("bolter_mag_in", mix(0.4, (0, click(rng, 900, 0.02, 0.1), 1), (0.012, thump(0.15, 110, 0.05), 1.0), (0.07, click(rng, 2100, 0.014), 0.9)))
save("bolter_rack_back", mix(0.25, (0, click(rng, 1100, 0.025, 0.12), 1), (0.05, band(noise(0.1, rng), 1500, 5000) * env(int(0.1 * RATE), 0.002, 0.03), 0.5)))
save("bolter_rack_fwd", mix(0.3, (0, click(rng, 800, 0.03, 0.14), 1), (0.008, thump(0.14, 95, 0.05), 0.9), (0.03, click(rng, 2400, 0.012), 0.6)))
for v in range(3):
    r = np.random.default_rng(400 + v)
    f = 3400 + v * 900
    save(f"casing_{v}", mix(0.25, (0, click(r, f, 0.02, 0.12, 0.8), 1), (0.09, click(r, f * 1.1, 0.012, 0.08, 0.8), 0.45), (0.15, click(r, f * 0.95, 0.008, 0.05, 0.8), 0.22)), 0.5)
save("gun_dry", mix(0.12, (0, click(rng, 3600, 0.006), 1), (0.03, click(rng, 1600, 0.008), 0.5)), 0.6)
save("gun_raise", mix(0.3, (0, band(noise(0.25, rng), 400, 2200) * env(int(0.25 * RATE), 0.04, 0.05), 0.6), (0.12, click(rng, 1700, 0.012), 0.6)), 0.5)
save("hit_marker", click(rng, 5200, 0.012, 0.06, 0.8), 0.5)
print("wav:", len(os.listdir(OUT)))
