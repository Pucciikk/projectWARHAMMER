#!/usr/bin/env python3
"""Сетка кадров с обрезкой по фигуре: crop_grid.py <папка> <куда.png> <колонок> <x0,y0,x1,y1> <кадр1> <кадр2> ... (без .png).
Каждый кадр подписан номером: удобно разбирать цикл ходьбы по фазам."""
import os
import sys

from PIL import Image, ImageDraw

src, out, cols, box, names = sys.argv[1], sys.argv[2], int(sys.argv[3]), tuple(int(v) for v in sys.argv[4].split(",")), sys.argv[5:]
w, h = box[2] - box[0], box[3] - box[1]
scale = 2 if w < 320 else 1
rows = (len(names) + cols - 1) // cols
sheet = Image.new("RGB", (w * scale * cols, h * scale * rows))
draw = ImageDraw.Draw(sheet)
for i, n in enumerate(names):
    im = Image.open(os.path.join(src, n + ".png")).convert("RGB").crop(box)
    if scale > 1:
        im = im.resize((w * scale, h * scale), Image.NEAREST)
    x, y = (i % cols) * w * scale, (i // cols) * h * scale
    sheet.paste(im, (x, y))
    draw.text((x + 4, y + 2), n, fill=(255, 255, 0))
sheet.save(out)
