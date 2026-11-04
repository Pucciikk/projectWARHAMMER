#!/usr/bin/env python3
"""
Звуки из папки автора D:/filesFromGWToMeOficial/extraction_sounds -> tools/sounds/game/<набор>/<номер>.wav (в git не нужны).
Набор — список событий Wwise. Для выбора вариантов печатает длину и громкость каждого файла.

    python tools/sounds/import_game_sounds.py <путь к vgmstream-cli.exe> [набор ...]
"""
import glob
import os
import subprocess
import sys

import numpy as np
from scipy.io import wavfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wwise_lookup as W

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "game")
SETS = {
    "bolter_2d": ("wpn", ["wpn_firearm_shoot_2d_bolter"]),
    "bolter_3d": ("wpn", ["wpn_firearm_shoot_3d_bolter"]),
    "bolter_tail": ("wpn", ["wpn_firearm_shoot_2d_bolter_tail"]),
    "heavy_3d": ("wpn", ["wpn_firearm_shoot_3d_bolter_heavy"]),
    "bolter_empty": ("wpn", ["wpn_firearm_shoot_2d_bolter_empty_shoot"]),
    "mag_out": ("wpn", ["wpn_firearm_reload_mag_out"]),
    "mag_in": ("wpn", ["wpn_firearm_reload_mag_in"]),
    "bolt_pull": ("wpn", ["wpn_firearm_reload_bolt_pull"]),
    "bolt_release": ("wpn", ["wpn_firearm_reload_bolt_release"]),
    "las_guard": ("wpn", ["ai_imp_guard_lasgun"]),
    "las_sniper": ("wpn", ["ai_sniper_cultist_lasgun"]),
    "las_cultist": ("chaos", ["ai_cultist_lasgun"]),
    "las_proj": ("common", ["wpn_projectile_lasgun"]),
    "chsw_idle": ("wpn", ["wpn_melee_chswd_idle_loop"]),
    "chsw_start": ("wpn", ["wpn_melee_chswd_idle_start"]),
    "dread_step": ("imperium", ["ai_imperium_dreadnought_step"]),
    "dread_servo": ("imperium", ["ai_imperium_dreadnought_servos"]),
    "dread_foley": ("imperium", ["ai_imperium_dreadnought_foley"]),
    "dread_breath": ("imperium", ["ai_imperium_dreadnought_idle_breath_start"]),
    "dread_stomp": ("imperium", ["ai_imperium_dreadnought_melee_stomp"]),
    "dread_jump": ("imperium", ["ai_imperium_dreadnought_jump"]),
    "dread_fall": ("chaos", ["ai_chaos_helbrute_loco_death_fall"]),
    "dread_hit": ("wpn", ["wpn_melee_heavy_fall_attack_pfist_impact"]),
    # цепной меч: удары по цели, взмахи, раскрутка мотора
    "chsw_slash": ("wpn", [f"wpn_melee_chswd_slash_{i}hit" for i in range(1, 6)]),
    "chsw_light": ("wpn", [f"wpn_melee_chswd_light_{i}hit" for i in range(1, 5)]),
    "chsw_charge": ("wpn", ["wpn_melee_chswd_charge_loop_start"]),
    "chsw_impact": ("wpn", ["wpn_melee_heavy_fall_attack_chainsword_impact"]),
    # снаряды: разрыв болта, попадание лазера и пули, пролёт
    "bolt_hit": ("common", ["wpn_bullet_hit"]),
    "las_hit": ("common", ["wpn_laser_hit"]),
    "bolt_fly": ("common", ["wpn_projectile_bolter"]),
    "rocket_exp": ("wpn", ["wpn_projectile_exp_terminator_rocket"]),
}


def find_wem(wem):
    p = W.find_wem(wem)
    if p:
        return p
    hits = glob.glob(os.path.join(W.ROOT, "wem_from_bnk", "desktop", "**", f"{wem}.wem"), recursive=True)
    return hits[0] if hits else None


def main():
    tool = sys.argv[1]
    wanted = sys.argv[2:] or list(SETS)
    banks = {}
    for name in wanted:
        bank, events = SETS[name]
        objects = banks.setdefault(bank, W.read_hirc(bank))
        wems = set()
        for e in events:
            w = W.event_wems(objects, e)
            if w is None:
                print(name, e, "НЕТ СОБЫТИЯ")
            else:
                wems |= w
        folder = os.path.join(OUT, name)
        os.makedirs(folder, exist_ok=True)
        rows = []
        for wem in sorted(wems):
            src = find_wem(wem)
            if not src:
                rows.append(f"{wem}: нет файла")
                continue
            dst = os.path.join(folder, f"{wem}.wav")
            if not os.path.exists(dst):
                subprocess.run([tool, "-o", dst, src], check=False, capture_output=True)
            if not os.path.exists(dst):
                rows.append(f"{wem}: не перевёлся")
                continue
            rate, x = wavfile.read(dst)
            x = x.astype(np.float64) / 32768
            if x.ndim > 1:
                ch = x.shape[1]
                x = x.mean(axis=1)
            else:
                ch = 1
            rows.append(f"{wem}: {len(x) / rate:.2f}c {ch}к пик {np.abs(x).max():.2f} rms {np.sqrt((x ** 2).mean()):.3f}")
        print(f"== {name}: {len(wems)}")
        for r in rows[:8]:
            print("  ", r)


if __name__ == "__main__":
    main()
