"""
Предметы Сезона 1: оружие, броня и их компоненты (docs/content/season1-items.md).

    python3 tools/textures/gen_s1_items.py

Иконки 16×16 в ванильном стиле: оружие и компоненты — попиксельные сетки; иконки и слои брони — силуэт ванильной
железной брони (из клиентского jar Loom), перекрашенный во флак Гвардии. Пишет textures/item/*.png,
textures/models/armor/flak_layer_1.png, _layer_2.png, respirator_layer_1.png и модели предметов.
"""
import glob
import io
import json
import os
import zipfile

import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "src", "main", "resources", "assets", "warpbound")
JAR = glob.glob(os.path.expanduser("~/.gradle/caches/fabric-loom/1.21.1/minecraft-client.jar"))

P = {
    ".": (0, 0, 0, 0),
    "k": (28, 26, 30, 255), "s": (14, 14, 16, 255),
    "g": (66, 68, 76, 255), "G": (112, 116, 126, 255), "w": (172, 178, 188, 255), "W": (220, 224, 230, 255),
    "b": (126, 88, 28, 255), "B": (196, 150, 58, 255), "y": (238, 204, 118, 255),
    "r": (110, 18, 18, 255), "R": (190, 40, 30, 255),
    "o": (52, 58, 32, 255), "O": (90, 100, 58, 255), "l": (132, 142, 88, 255),
    "n": (68, 42, 22, 255), "N": (108, 70, 38, 255), "m": (146, 98, 58, 255),
    "c": (44, 116, 210, 255), "C": (150, 214, 255, 255),
    "e": (46, 170, 80, 255), "E": (150, 255, 170, 255),
    "p": (170, 92, 46, 255), "P": (214, 136, 80, 255),
    "f": (232, 120, 40, 255), "F": (255, 210, 120, 255),
}

GRIDS = {
    # лазган: приклад из тёмного дерева, ствольная коробка, лазпакет снизу, кожух ствола, синяя линза
    "lasgun": [
        "............kkk.",
        "...........kGGCk",
        "..........kGwkck",
        ".........kGwGk..",
        "........kGwGk...",
        ".......kgGGk....",
        "......kgwGgk....",
        ".....kggGgk.....",
        "....kNkgggk.....",
        "...kNmkeEkk.....",
        "..kNNkkeek......",
        ".kNmNk.kk.......",
        "kNNNk...........",
        "kNnk............",
        "kkk.............",
        "................",
    ],
    # цепной меч: рукоять, латунная гарда с мотором, клинок с зубьями цепи
    "chainsword": [
        "...........kkk..",
        "..........kwGtk.",
        ".........kwGkt..",
        "........kwGkt...",
        ".......kwGkt....",
        "......kwGkt.....",
        ".....kwGkt......",
        "....kwGkt.......",
        "..kkkGkt........",
        "..kBykkk........",
        "..kbBBk.........",
        "..ksbk..........",
        ".kssk...........",
        "kssk............",
        "kkk.............",
        "................",
    ],
    "focusing_lens": [
        "................",
        "................",
        ".....kkkkkk.....",
        "....kbBBBBbk....",
        "...kbBccccBbk...",
        "..kbBcCCcccBbk..",
        "..kBcCCccccbBk..",
        "..kBcCcccccbBk..",
        "..kBccccccsbBk..",
        "..kBcccccssbBk..",
        "..kbBccccsBbk...",
        "...kbBBBBBbk....",
        "....kbbbbbk.....",
        ".....kkkkk......",
        "................",
        "................",
    ],
    "capacitor": [
        "................",
        "......kkkk......",
        ".....kwWWwk.....",
        ".....kGwwGk.....",
        ".....kpPPpk.....",
        ".....kpPPpk.....",
        ".....kcCCck.....",
        ".....kcCCck.....",
        ".....kpPPpk.....",
        ".....kpPPpk.....",
        ".....kpPPpk.....",
        ".....kGwwGk.....",
        "......kkkk......",
        "......k..k......",
        "......k..k......",
        "................",
    ],
    "las_battery": [
        "................",
        "................",
        "...kkkkkkkkkk...",
        "...kGwwwwwwGk...",
        "...kgGGGGGGgk...",
        "...kgkkkkkkgk...",
        "...kgkeEeEkgk...",
        "...kgkeEeEkgk...",
        "...kgkeEeEkgk...",
        "...kgkkkkkkgk...",
        "...kgGGGGGGgk...",
        "...kgBbgGBbgk...",
        "...kgggggggk....",
        "...kkkkkkkkkk...",
        "................",
        "................",
    ],
    "las_battery_depleted": [
        "................",
        "................",
        "...kkkkkkkkkk...",
        "...kGwwwwwwGk...",
        "...kgGGGGGGgk...",
        "...kgkkkkkkgk...",
        "...kgksssskgk...",
        "...kgksssskgk...",
        "...kgkrRrRkgk...",
        "...kgkkkkkkgk...",
        "...kgGGGGGGgk...",
        "...kgBbgGBbgk...",
        "...kgggggggk....",
        "...kkkkkkkkkk...",
        "................",
        "................",
    ],
    "servo_motor": [
        "................",
        "..kk.kk.........",
        ".kBBkBBk........",
        "kBbyyybBk.......",
        ".kbykkybk.......",
        "kBbykkybBkkkkk..",
        ".kbyyybkGwwwwGk.",
        "kBBbbbBBkgGGGgk.",
        ".kkBkBkkpkPPPkpk",
        "...kkk.kpkPPPkpk",
        ".......kgGGGGGgk",
        ".......kGwwwwwGk",
        "........kkkkkkk.",
        "................",
        "................",
        "................",
    ],
    "chain_blade": [
        "................",
        "............kk..",
        "...........kwtk.",
        "..........kwGt..",
        ".........kwGt...",
        "........kwGt....",
        ".......kwGt.....",
        "......kwGt......",
        ".....kwGt.......",
        "....kwGt........",
        "...kwGt.........",
        "..kwGt..........",
        ".kGgt...........",
        ".kkt............",
        "................",
        "................",
    ],
    "flak_plate": [
        "................",
        "................",
        "..kkkkkkkkkkkk..",
        "..kllllllllllk..",
        "..klOOOOOOOOok..",
        "..klOgOOOOgOok..",
        "..klOOOOOOOOok..",
        "..kkkkkkkkkkkk..",
        "..kllllllllllk..",
        "..klOOOOOOOOok..",
        "..klOgOOOOgOok..",
        "..klOOOOOOOOok..",
        "..kooooooooook..",
        "..kkkkkkkkkkkk..",
        "................",
        "................",
    ],
    "respirator_filter": [
        "................",
        "................",
        "......kkkk......",
        ".....kGwwGk.....",
        "....kOOOOOOk....",
        "...kOlOOOOlOk...",
        "...kOkOkOkOOk...",
        "...kOkOkOkOOk...",
        "...kOkOkOkOOk...",
        "...kOlOOOOlOk...",
        "....kOOOOOOk....",
        ".....koooook....",
        "......kkkk......",
        "................",
        "................",
        "................",
    ],
    "respirator": [
        "................",
        "................",
        "................",
        "....kkkkkkkk....",
        "...kgGGGGGGgk...",
        "..kgGgkkkkgGgk..",
        "..kgkkskskkkgk..",
        ".kOkgksksksgkOk.",
        "kOlOkgsksksgkOlOk"[:16],
        "kOlOkgGGGGGgkOlO",
        "kOOOkkgGGGgkkOOO",
        ".kok..kgggk..kok",
        "......kNNk......",
        "......kNNk......",
        ".......kk.......",
        "................",
    ],
}


def grid(name):
    rows = GRIDS[name]
    img = np.zeros((16, 16, 4), np.uint8)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row[:16]):
            if ch == "t":                              # зубья цепи: светлый и тёмный через один
                img[y, x] = P["W"] if (x + y) % 2 else P["g"]
            else:
                img[y, x] = P[ch]
    return Image.fromarray(img, "RGBA")


def vanilla(path):
    with zipfile.ZipFile(JAR[0]) as z:
        return Image.open(io.BytesIO(z.read(path))).convert("RGBA")


def flak_recolor(img, base=(86, 96, 56), seed=7):
    """Перекраска ванильного железа во флак: яркость → оливковая шкала, лёгкая пятнистость ткани."""
    a = np.asarray(img).astype(np.float32)
    lum = (a[..., 0] * 0.3 + a[..., 1] * 0.59 + a[..., 2] * 0.11) / 255
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, 0.05, lum.shape)
    t = np.clip(lum * 1.15 + noise - 0.1, 0, 1)
    dark, light = np.array([34, 38, 22]), np.array([150, 158, 104])
    rgb = dark[None, None] * (1 - t[..., None]) + light[None, None] * t[..., None]
    rgb = rgb * (np.array(base) / np.array([86, 96, 56]))[None, None]
    out = a.copy()
    out[..., :3] = np.clip(rgb, 0, 255)
    return Image.fromarray(out.astype(np.uint8), "RGBA")


def save(img, *path):
    p = os.path.join(ROOT, *path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    img.save(p)


def item_model(name, handheld=False):
    p = os.path.join(ROOT, "models", "item", name + ".json")
    json.dump({"parent": "minecraft:item/handheld" if handheld else "minecraft:item/generated",
               "textures": {"layer0": "warpbound:item/" + name}}, open(p, "w"), indent=1)


def main():
    for name in GRIDS:
        save(grid(name), "textures", "item", name + ".png")
        if name not in ("lasgun", "chainsword"):                # у оружия 3D-модель (tools/models/gen_gear.py)
            item_model(name)
    # иконки флака — силуэт ванильного железа
    for piece in ("helmet", "chestplate", "leggings", "boots"):
        icon = flak_recolor(vanilla(f"assets/minecraft/textures/item/iron_{piece}.png"))
        save(icon, "textures", "item", f"flak_{piece}.png")
        item_model(f"flak_{piece}")
    # слои флака на модели игрока: ванильная раскладка железной брони, перекрашенная; латунные заклёпки на пластинах
    for layer in (1, 2):
        tex = flak_recolor(vanilla(f"assets/minecraft/textures/models/armor/iron_layer_{layer}.png"), seed=layer)
        a = np.asarray(tex).copy()
        h, w = a.shape[:2]
        for y in range(2, h, 6):
            for x in range(3, w, 7):
                if a[y, x, 3] > 0:
                    a[y, x, :3] = (196, 150, 58)
        save(Image.fromarray(a, "RGBA"), "textures", "models", "armor", f"flak_layer_{layer}.png")
    # респиратор на модели: только нижняя половина лица шлема — маска, решётка, два фильтра по бокам
    resp = np.zeros((32, 64, 4), np.uint8)
    for x in range(8, 16):
        for y in range(12, 16):
            resp[y, x] = (60, 62, 70, 255) if (x + y) % 2 else (48, 50, 56, 255)
    for x in (10, 12, 13, 15):
        resp[13, x - 1] = (18, 18, 20, 255)
        resp[14, x - 1] = (18, 18, 20, 255)
    for x in (8, 15):
        for y in (13, 14, 15):
            resp[y, x] = (90, 100, 58, 255)
    resp[11, 9:15] = (40, 40, 44, 255)                    # ремешок под глазами
    for x in (0, 7, 16, 23):                               # ремешок по бокам и затылку головы
        for y in range(10, 12):
            if 0 <= x < 64:
                resp[y, x:x + 8] = (40, 40, 44, 255)
    save(Image.fromarray(resp, "RGBA"), "textures", "models", "armor", "respirator_layer_1.png")
    print("предметов:", len(GRIDS) + 4)


if __name__ == "__main__":
    main()
