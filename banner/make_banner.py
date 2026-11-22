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
GREY = "#a8a8a8"
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


def half_cells():
    """(half-col, row) of every lit half cell. Splitting each ink cell in two lets the word be read
    half a cell at a time, so a letter shows a tick after the head has passed it."""
    for col, row, letter in cells():
        yield col, row, letter
        yield col, row, letter


def to_px(col, row):
    return X0 + col * CELL, Y0 + row * CELL


def to_px_half(half_col, row):
    return X0 + half_col * CELL, Y0 + row * CELL


def head():
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"\n'
            '  shape-rendering="crispEdges">\n')


def still():
    """The still paints the background, so it stands alone wherever it is used. One rectangle, not
    the reveal's block grid, so nothing can show through between tiles."""
    rects = "".join(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" fill="{INK}"/>'
                    for x, y in ((to_px(c, r)) for c, r, _ in cells()))
    return head() + f'<rect width="{W}" height="{H}" fill="{BG}"/>' + rects + "</svg>"




SLOW = 1.6                           # period multiplier for the beats
TEXT_STEP = 0.028                    # seconds between ink cells
BG_SECONDS = 2.0                     # the page's whole build
BG_LEAD = 0.16                       # nothing is down when the first frame paints
CLOSE_ROWS = 4                       # rows of the last band still to close when the ink starts


def reveal():
    """Two beats, both built out of the grid.

    The page comes in as a wall of blocks laying themselves down in a ragged diagonal order, so it
    reads as being built rather than wiped. Only once the page is down does the word appear, left
    to right, one letter at a time."""
    page = [(c, r) for r in range(-1, ROWS + 1) for c in range(-1, COLS + 1)]
    out = [head()]

    # --- beat 1: the page. What the eye reads is area, so the pace is held at a constant area per
    # beat and the reveal is a band as tall as a full-width row advancing down the page. A band
    # nudged in from the top-left corner would only start with a few cells and race, so a second
    # front closes the matching band up from the bottom while the first opens the next one down;
    # the two together hold the band full width from the very first beat. Entries carry how many
    # cells they land at once, `1` or `2`, and that is what makes the rate constant.
    # One column of both rows per beat, so the band holds 600 cells while it opens and the two
    # rows can drift a cell apart between beats without changing the pace.
    queue = []
    for step in range(ROWS):
        top = [(c, step) for c in range(COLS)]
        bot = [(c, ROWS - 1 - step) for c in range(COLS)]
        for k in range(COLS):
            queue.append((top[k], 1.0))
            if step < ROWS // 2:
                queue.append((bot[k], 1.0))
    # The band runs until the closing rows the ink starts on are down, plus those still to go;
    # the word then takes over and the last rows land behind it, inside the ink's own run.
    total = sum(w for _, w in queue)
    open_total = total - CLOSE_ROWS * 2 * COLS
    span = BG_SECONDS - BG_LEAD
    acc = 0.0
    for (c, r), w in queue:
        t0 = BG_LEAD + span * acc / open_total
        out.append(f'<rect x="{c * CELL}" y="{r * CELL}" width="{CELL}" height="{CELL}" '
                   f'fill="{BG}" opacity="1">'
                   f'<set attributeName="opacity" to="0" begin="0s" end="{t0:.3f}s"/></rect>')
        acc += w

    # --- beat 2: the word, left to right, started while the last band is still closing behind it
    text_start = BG_LEAD + span
    for idx, (c, r, _letter) in enumerate(sorted(cells(), key=lambda c: (c[2], c[1], c[0]))):
        x, y = to_px(c, r)
        t0 = text_start + idx * TEXT_STEP
        out.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" fill="{INK}" opacity="0">'
            f'<set attributeName="opacity" to="1" begin="{t0:.3f}s"/></rect>')
    out.append("</svg>")
    return "".join(out)


if __name__ == "__main__":
    open("banner.svg", "w").write(still())
    open("banner-reveal.svg", "w").write(reveal())
    open("banner.json", "w").write(json.dumps(
        {"cell": CELL, "origin": [X0, Y0], "floor": FLOOR, "glyphs": GLYPHS, "word": WORD,
         "pitch": ADVANCE, "cells": list(cells())}, indent=1))
    print(f"mark {MARK_W}x{MARK_H} cells, {len(list(cells()))} lit squares")