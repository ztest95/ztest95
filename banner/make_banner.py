"""Generates banner/banner-reveal.svg (the animated banner) and banner/banner.svg (the still).

The word is drawn from a 3x4 pixel font, lit cell by cell on a 10px grid, and uncovered as an
animation. Everything is SMIL: no JavaScript, no CSS, no external fonts.
"""
import json
import math

LETTER_W, GAP = 3, 1
CELL = 10
W, H = 1500, 400
COLS, ROWS = W // CELL, H // CELL


def rnd(i):
    x = math.sin(i * 12.9898 + 78.233) * 43758.5453
    return x - math.floor(x)


BG = "#f1f1f1"
INK = "#111111"

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
MARK_H = LETTER_H = 4
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
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"\n'
            '  shape-rendering="crispEdges">\n')


def still():
    """The still paints the background, so it stands alone wherever it is used. One rectangle, not
    the reveal's block grid, so nothing can show through between tiles."""
    rects = "".join(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" fill="{INK}"/>'
                    for x, y in ((to_px(c, r)) for c, r, _ in cells()))
    return head() + f'<rect width="{W}" height="{H}" fill="{BG}"/>' + rects + "</svg>"


TEXT_STEP = 0.028                    # seconds between ink cells
BG_SECONDS = 2.0                     # the page's whole build
BG_LEAD = 0.16                       # nothing is down when the first frame paints
CLOSE_LEVELS = 2                     # corner blocks still building when the ink starts
LEVELS = 5                           # how many times a corner may halve its block
EDGE = 3                             # the corner block's side, in cells
SLANT = 0.5                          # how far a row is pushed back, as a share of a line



def cut(n):
    """(start, size) runs covering a line, biggest at each corner and doubling towards the middle,
    so the corners offer few cells and the middle offers many."""
    half = (n + 1) // 2
    runs = []
    for flip in (False, True):
        pos, size = 0, EDGE
        while pos < half:
            size = min(size, half - pos)
            runs.append(((n - pos - size, size) if flip else (pos, size)))
            pos, size = pos + size, size * 2
    return runs


def reveal():
    """Two beats, both built out of the grid.

    The page comes in as a ragged diagonal of blocks, big at the corners and small in the middle.
    A corner diagonal has only a few neighbours, so a uniform beat would race through the corners
    and crawl in the middle; cutting the corners into big blocks leaves them few cells to put on
    offer, which levels the pace without losing the scatter. The word then types in left to right
    while the last corner blocks are still landing."""
    out = [head()]

    # --- beat 1: the page. Every block starts solid and is uncovered at its moment.
    xs, ys = cut(COLS + 2), cut(ROWS + 2)
    page = [((bx, by), (bs, ts)) for bx, bs in xs for by, ts in ys]
    # the diagonal position places a block in the sweep, the square root of its area pulls a big
    # block earlier than it sits, and the jitter breaks the bands without reordering much
    page.sort(key=lambda b: (b[0][0] + b[0][1] * SLANT) / b[1][1] ** 0.5
                             / (1 + rnd(b[0][0] * 7.3 + b[0][1] * 13.1) * 0.06))
    open_total = sum(b[1][1] ** 2 for b in page if b[1][0] > CLOSE_LEVELS)
    span = BG_SECONDS - BG_LEAD
    acc = 0.0
    for (bx, by), (bs, ts) in page:
        t0 = BG_LEAD + span * acc / open_total
        out.append(f'<rect x="{(bx - 1) * CELL}" y="{(by - 1) * CELL}" '
                   f'width="{bs * CELL}" height="{ts * CELL}" fill="{BG}" opacity="1">'
                   f'<set attributeName="opacity" to="0" begin="0s" end="{t0:.3f}s"/></rect>')
        if ts > CLOSE_LEVELS:
            acc += bs * ts

    # --- beat 2: the word, left to right, while the last corner blocks are still landing
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