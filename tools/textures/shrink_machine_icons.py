#!/usr/bin/env python3
"""
Ужимает рендеры машин (tools/models/blender/render_icons.py) до значков 32×32: контрастнее и с тёмным контуром, чтобы читались в слоте.

    python3 tools/textures/shrink_machine_icons.py [--sheet путь.png]
"""
import glob
import os
import sys

from PIL import Image, ImageEnhance

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
TEX = os.path.join(ROOT, "src/main/resources/assets/warpbound/textures/item")
N = 32


def shrink(img):
    if img.width == N:
        return img
    small = img.resize((N, N), Image.LANCZOS)
    rgb = ImageEnhance.Contrast(small.convert("RGB")).enhance(1.25)
    rgb = ImageEnhance.Color(rgb).enhance(1.25)
    out = Image.merge("RGBA", (*rgb.split(), small.getchannel("A").point(lambda a: 255 if a > 90 else 0)))
    px = out.load()
    edge = []
    for y in range(N):
        for x in range(N):
            if px[x, y][3] == 0:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    u, v = x + dx, y + dy
                    if 0 <= u < N and 0 <= v < N and px[u, v][3]:
                        edge.append((x, y))
                        break
    for x, y in edge:
        px[x, y] = (12, 12, 15, 255)
    return out


names = sorted(glob.glob(os.path.join(TEX, "machine_*.png")))
done = []
for path in names:
    img = shrink(Image.open(path).convert("RGBA"))
    img.save(path)
    done.append(img)
print("значков машин:", len(done))
if "--sheet" in sys.argv:
    cols = 8
    rows = (len(done) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * 100, rows * 100), (139, 139, 139, 255))
    for k, img in enumerate(done):
        big = img.resize((96, 96), Image.NEAREST)
        sheet.paste(big, ((k % cols) * 100 + 2, (k // cols) * 100 + 2), big)
    sheet.save(sys.argv[sys.argv.index("--sheet") + 1])
