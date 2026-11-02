#!/usr/bin/env python3
"""Сетка кадров цикла: tools/models/blender/grid.py <папка> <куда.png> <колонок> <кадр1> <кадр2> ... (без .png)"""
import os
import sys

from PIL import Image

src, out, cols, names = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4:]
W, H = 427, 240
rows = (len(names) + cols - 1) // cols
sheet = Image.new("RGB", (W * cols, H * rows))
for i, n in enumerate(names):
    im = Image.open(os.path.join(src, n + ".png")).convert("RGB").resize((W, H))
    sheet.paste(im, ((i % cols) * W, (i // cols) * H))
sheet.save(out)
