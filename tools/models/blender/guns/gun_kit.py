"""
Общее для оружия: кривые анимации, руки-заглушки для просмотра, выгрузка клипов.

Оси как у машин: 1 м = 1 блок, Z вверх, ствол смотрит в -Y, правая сторона оружия при взгляде от стрелка — это -X.
Клип — функция pose(t) (t от 0 до 1): {кость: {"pos": (x, y, z) метры, "rot": (x, y, z) градусы}}.
Псевдокость "_view" двигает всё оружие целиком в кадре. Руки ("arm_r", "arm_l") рисует игра: кожа игрока, в Blender только заглушка.
"""
import json
import math
import os

GUN_ASSETS = r"C:/Users/Name/projectWARHAMMER/src/main/resources/assets/warpbound"
ARM_LEN, ARM_W = 0.62, 0.175     # заглушка руки: совпадает с масштабом ARM_SCALE в GunRenderer


def ease(k, kind="io"):
    if kind == "lin":
        return k
    if kind == "in":
        return k * k * k
    if kind == "out":
        return 1 - (1 - k) ** 3
    if kind == "snap":       # резкий рывок с лёгким перелётом: руки ставят магазин
        return 1 - (1 - k) ** 4 * math.cos(k * 7.0)
    return k * k * k * (k * (6 * k - 15) + 10)     # плавно на входе и выходе


def kf(t, keys):
    """Ключи [(время 0..1, значение или кортеж[, вид кривой])]: вид относится к участку, который заканчивается на этом ключе."""
    if t <= keys[0][0]:
        return keys[0][1]
    for a, b in zip(keys, keys[1:]):
        if t <= b[0]:
            kind = b[2] if len(b) > 2 else "io"
            k = ease((t - a[0]) / max(1e-6, b[0] - a[0]), kind)
            if isinstance(a[1], tuple):
                return tuple(u + (v - u) * k for u, v in zip(a[1], b[1]))
            return a[1] + (b[1] - a[1]) * k
    return keys[-1][1]


def add(*vs):
    return tuple(sum(c) for c in zip(*vs))


def scale(v, k):
    return tuple(c * k for c in v)


def arm(m, name, pivot):
    """Рука-заглушка: кисть в pivot, локоть уходит назад по +Y."""
    b = m.bone(name, pivot)
    w = ARM_W / 2
    x, y, z = pivot
    b.box((x - w, y, z - w), (x + w, y + ARM_LEN, z + w), "bone")
    b.box((x - w - 0.004, y, z - w - 0.004), (x + w + 0.004, y + 0.14, z + w + 0.004), "wax")
    return b


def small_seal(b, at, side):
    """Печать чистоты в размер оружия: стандартная из kit сделана для машин и здесь была бы как тарелка."""
    x, y, z = at
    b.lathe((x, y, z), [(0.028, 0), (0.03, side * 0.006), (0.022, side * 0.012)], 8, "wax", "X")
    for dy, ln in ((-0.012, 0.075), (0.01, 0.1)):
        b.box((x + side * 0.002, y + dy - 0.007, z - ln), (x + side * 0.005, y + dy + 0.007, z - 0.012), "parchment")


def locator(m, name, at):
    """Точка без геометрии: дуло, окно выброса."""
    return m.bone(name, at)


def export_clips(name, clips, fps=30):
    """assets/warpbound/gun_anim/<имя>.json: дорожки с равным шагом, игра читает их сама и сводит с отдачей и покачиванием."""
    out = {"fps": fps, "clips": {}}
    for clip, data in clips.items():
        length, fn = data["length"], data["pose"]
        steps = max(1, int(round(length * fps)))
        tracks = {}
        for i in range(steps + 1):
            for bone, st in fn(i / steps).items():
                tr = tracks.setdefault(bone, {"pos": [], "rot": []})
                tr["pos"].append([round(c, 4) for c in st.get("pos", (0, 0, 0))])
                tr["rot"].append([round(c, 3) for c in st.get("rot", (0, 0, 0))])
        out["clips"][clip] = {"length": length, "loop": data.get("loop", False), "tracks": tracks,
                              "events": [[round(a, 3), e] for a, e in data.get("events", [])]}
    path = os.path.join(GUN_ASSETS, "gun_anim", name + ".json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, separators=(",", ":"))
    print(name, "клипов:", len(out["clips"]))


def preview(m, sc, pose, length, skip=("_view",)):
    """Ключи клипа в Blender: посмотреть движение рук и оружия до запуска игры."""
    from mathutils import Vector
    frames = max(1, int(length * 24))
    rest = {n: ob.location.copy() for n, ob in m.objects.items()}
    for ob in m.objects.values():
        ob.animation_data_clear()
    for f in range(frames + 1):
        for name, st in pose(f / frames).items():
            if name in skip or name not in m.objects:
                continue
            ob = m.objects[name]
            ob.location = rest[name] + Vector(st.get("pos", (0, 0, 0)))
            ob.rotation_euler = tuple(math.radians(c) for c in st.get("rot", (0, 0, 0)))
            ob.keyframe_insert("location", frame=f + 1)
            ob.keyframe_insert("rotation_euler", frame=f + 1)
    sc.frame_start, sc.frame_end = 1, frames + 1
    sc.frame_set(1)
