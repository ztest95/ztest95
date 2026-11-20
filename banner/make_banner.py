#!/usr/bin/env python3
"""
make_banner.py  ·  builds banner.svg (still) and banner-reveal.svg (drop-in reveal) from the
same pixel lattice.

Every glyph pixel is ONE square. Cells and gaps are both `CELL` px, so the whole mark sits on a
regular lattice: cell k spans x = k * CELL, every cell is CELL x CELL, and a renderer can scale the
grid by any integer without seams.

The glyphs are 3 x 4, transcribed cell by cell from the original banner (Pixel Font 4x4 — the
letter cell is 4 cells wide including its 1-cell gap, so the ink is 3). Row 0 is the top row.

The canvas keeps GitHub's 1500 x 400 cap and gives the mark free rows underneath, so cells can drop
and be clipped at the floor without ever leaving the viewBox.

Everything is SMIL and inline attributes: GitHub serves this through an <img>, so no JS, no CSS
keyframes, no external font.
"""
import json
import math

CELL = 10
LETTER_W, LETTER_H = 3, 4
GAP = 1                      # in cells: the original 6px gap / 6px pixel
W, H = 1500, 400
COLS, ROWS = W // CELL, H // CELL


def rnd(i):
    x = math.sin(i * 12.9898 + 78.233) * 43758.5453
    return x - math.floor(x)
BG = "#f1f1f1"
INK = "#111111"
FPS = 10

# 3 wide x 4 tall, row by row, exactly as the banner draws them.
GLYPHS = {
    "z": ["...", "##.", ".#.", ".##"],
    "t": ["#..", "##.", "#..", ".##"],
    "e": ["...", ".##", "##.", "###"],
    "s": ["...", ".##", ".#.", "##."],
    "9": ["###", "#.#", "###", "..#"],
    "5": ["###", "##.", "..#", "###"],
}
WORD = "ztest95"

ADVANCE = LETTER_W + GAP
MARK_W = len(WORD) * ADVANCE - GAP
MARK_H = LETTER_H
# centre the ink itself: equal cells to the left/right and above/below of the lit mark. Cells are
# snapped to whole pixels, so the two margins can only differ by the odd pixel left over.
X0 = (W - (MARK_W - 1) * CELL) // 2
Y0 = (H - MARK_H * CELL) // 2
FLOOR = Y0 + MARK_H * CELL


def cells():
    """(col, row, letter) of every lit cell, letter by letter."""
    for i, ch in enumerate(WORD):
        for r, line in enumerate(GLYPHS[ch]):
            for c, on in enumerate(line):
                if on == "#":
                    yield i * ADVANCE + c, r, i


def to_px(col, row):
    return X0 + col * CELL, Y0 + row * CELL


def head():
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'


def still():
    """The still paints the background, so it stands alone wherever it is used."""
    rects = "".join(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" fill="{INK}"/>'
                    for x, y in ((to_px(c, r)) for c, r, _ in cells()))
    return head() + f'<rect width="{W}" height="{H}" fill="{BG}"/>' + rects + "</svg>"




SPLINES = ";".join(["0.33 0 0.67 1"] * 6)
SLOW = 1.6                           # period multiplier for the beats


def reveal():
    """Two beats, both built out of the grid.

    The page comes in as a wall of blocks laying themselves down in a ragged diagonal order, so it
    reads as being built rather than wiped. Only once the page is down does the word appear, one
    letter at a time, each cell snapping in with a quick squash and no travel."""
    page = [(c, r) for r in range(-1, ROWS + 1) for c in range(-1, COLS + 1)]
    bg_step = (1.5 * SLOW) / len(page)
    text_start = 2.0 * SLOW
    out = [head()]

    # --- beat 1: the page. The order is a diagonal sweep with jitter so no two neighbours land
    # on the same beat; every block starts solid and is uncovered at its moment.
    page.sort(key=lambda p: (p[0] * 0.8 + p[1]) + rnd(p[0] * 7.3 + p[1] * 13.1) * 7)
    for i, (c, r) in enumerate(page):
        t0 = i * bg_step
        # one pixel of overlap, so no hairline of the page shows between blocks
        out.append(f'<rect x="{c * CELL}" y="{r * CELL}" width="{CELL + 1}" height="{CELL + 1}" '
                   f'fill="{BG}" opacity="1">'
                   f'<set attributeName="opacity" to="0" begin="0s" end="{t0:.3f}s"/></rect>')

    # --- beat 2: the word, letter by letter, no travel
    for idx, (c, r, _letter) in enumerate(sorted(cells(), key=lambda c: (c[2], c[1], c[0]))):
        x, y = to_px(c, r)
        t0 = text_start + idx * 0.022
        end = t0 + 0.26
        out.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" fill="{INK}" opacity="0">'
            f'<set attributeName="opacity" to="1" begin="{t0:.3f}s"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 {CELL * 0.5};0 0;0 0" keyTimes="0;{0.45:.2f};1" '
            f'dur="{end - t0:.3f}s" fill="freeze" calcMode="spline" keySplines="{SPLINES[:27]}"/>'
            f'<animateTransform attributeName="transform" type="scale" '
            f'values="1 0.45;1 1;1 1" keyTimes="0;0.45;1" '
            f'dur="{end - t0:.3f}s" fill="freeze" calcMode="spline" keySplines="{SPLINES[:27]}" '
            f'transform-origin="{x} {y + CELL}"/>'
            "</rect>")
    out.append("</svg>")
    return "".join(out)


if __name__ == "__main__":
    open("banner.svg", "w").write(still())
    open("banner-reveal.svg", "w").write(reveal())
    open("banner.json", "w").write(json.dumps(
        {"cell": CELL, "origin": [X0, Y0], "floor": FLOOR, "glyphs": GLYPHS, "word": WORD,
         "pitch": ADVANCE, "cells": list(cells())}, indent=1))
    print(f"mark {MARK_W}x{MARK_H} cells, {len(list(cells()))} lit squares")