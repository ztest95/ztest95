#!/usr/bin/env python3
"""
make_banner.py  ·  builds banner.svg (still) and banner-reveal.svg (drop-in reveal) from the
same pixel lattice.

Every glyph pixel is ONE square. Cells and gaps are both `CELL` px, so the whole mark sits on a
regular lattice: cell k spans x = k * CELL, every cell is CELL x CELL, and a renderer can scale the
grid by any integer without seams. The glyphs are 4 x 3 as drawn in the original banner.

The canvas keeps GitHub's 1500 x 400 cap and gives the mark free rows underneath, so cells can drop
and be clipped at the floor without ever leaving the viewBox.

Everything is SMIL and inline attributes: GitHub serves this through an <img>, so no JS, no CSS
keyframes, no external font.
"""
import json

CELL = 10
LETTER_W, LETTER_H = 4, 3
GAP = 1                      # in cells: the original 6px gap / 40.5px letter cell
W, H = 1500, 400
BG = "#f1f1f1"
INK = "#111111"
FPS = 10

# 4 wide x 3 tall, row by row. Row 0 is above row 2.
GLYPHS = {
    "z": ["....", "##..", ".#.."],
    "t": ["#...", "##..", "#..."],
    "e": ["....", ".##.", "##.."],
    "s": ["....", ".##.", ".#.."],
    "9": ["###.", "#.#.", "###."],
    "5": ["###.", "##..", "..#."],
}
WORD = "ztest95"

ADVANCE = LETTER_W + GAP
MARK_W = len(WORD) * ADVANCE - GAP
MARK_H = LETTER_H
X0 = (W - MARK_W * CELL) // 2
Y0 = (H - (MARK_H + 7) * CELL) // 2
FLOOR = Y0 + (MARK_H + 7) * CELL


def cells():
    """(col, row, letter) of every lit cell, letter by letter."""
    for i, ch in enumerate(WORD):
        for r, line in enumerate(GLYPHS[ch]):
            for c, on in enumerate(line):
                if on == "#":
                    yield i * ADVANCE + c, r, i


def to_px(col, row):
    return X0 + col * CELL, Y0 + row * CELL


def head(extra=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<rect width="{W}" height="{H}" fill="{BG}"/>')


def still():
    rects = "".join(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" fill="{INK}"/>'
                    for x, y in ((to_px(c, r)) for c, r, _ in cells()))
    return head() + rects + "</svg>"


SPLINES = ';'.join(['0.33 0 0.67 1'] * 6)


def reveal():
    """Staggered drop-in, letter by letter, bottom row of each letter first. A cell starts above
    its home, falls, squashes on contact, and is pushed one row down by the rows landing on it, so
    every letter assembles top-down in the air and only settles at the end."""
    out = [head()]
    STEP = 0.011                         # seconds between cells
    cells_ = sorted(cells(), key=lambda c: (c[2], -c[1], c[0]))
    for idx, (c, r, _letter) in enumerate(cells_):
        x, y = to_px(c, r)
        # the rows above land on this one in the same beat: it is pushed down `rows_above` rows
        rows_above = LETTER_H - 1 - r
        t0 = idx * STEP
        fall = 0.20 + 0.035 * r          # higher rows fall further, so they take longer
        land = t0 + fall
        squash = land + 0.05          # squash on contact
        push_at = squash + 0.05      # the row above lands and shoves it down
        push_end = push_at + rows_above * 0.06 + 0.001
        settle = push_end + 0.11
        end = settle + 0.10
        kt = [0, t0, land, squash, push_at, push_end, end]
        k = ";".join(f"{t / end:.6f}" for t in kt)
        sy = [1, 1, 0.45, 1, 1, 1, 1]
        dy = [-CELL * (r + 1), 0, 0, 0, 0, rows_above * CELL, rows_above * CELL]
        out.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" fill="{INK}" opacity="0">'
            f'<set attributeName="opacity" to="1" begin="{t0:.3f}s"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="{";".join(f"{v} 0" for v in dy)}" keyTimes="{k}" dur="{end:.3f}s" '
            f'fill="freeze" calcMode="spline" keySplines="{SPLINES}"/>'
            f'<animateTransform attributeName="transform" type="scale" additive="sum" '
            f'values="{";".join(f"1 {v}" for v in sy)}" keyTimes="{k}" dur="{end:.3f}s" '
            f'fill="freeze" calcMode="spline" keySplines="{SPLINES}" '
            f'transform-origin="{x + CELL / 2} {y + CELL}"/>'
            "</rect>")
    out.append("</svg>")
    return "".join(out)


if __name__ == "__main__":
    open("banner.svg", "w").write(still())
    open("banner-reveal.svg", "w").write(reveal())
    open("banner.json", "w").write(json.dumps(
        {"cell": CELL, "origin": [X0, Y0], "floor": FLOOR, "cells": list(cells())}))
    print(f"mark {MARK_W}x{MARK_H} cells, {len(list(cells()))} lit squares")