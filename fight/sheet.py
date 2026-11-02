#!/usr/bin/env python3
"""Tile frame PNGs into one contact sheet with their timestamps. usage: sheet.py OUT.png FRAME..."""
import sys
from PIL import Image, ImageDraw

out, frames = sys.argv[1], sys.argv[2:]
th = 166
cols = 3
tiles = []
for f in frames:
    im = Image.open(f).convert("RGB")
    im = im.resize((int(im.width * th / im.height), th))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 40, 14), fill="black")
    d.text((3, 2), f.rsplit("/", 1)[-1].split(".")[0], fill="yellow")
    tiles.append(im)
w, h = tiles[0].size
sheet = Image.new("RGB", (cols * (w + 4), ((len(tiles) + cols - 1) // cols) * (h + 4)), (40, 40, 40))
for i, t in enumerate(tiles):
    sheet.paste(t, ((i % cols) * (w + 4), (i // cols) * (h + 4)))
sheet.save(out)
print(out, sheet.size)