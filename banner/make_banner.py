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
TEXT_STEP = 0.034                    # seconds every typed column lasts
TYPED = (MARK_W + 1) // 2            # typed columns, rounded up so the line ends clean
X_END = W + CELL                     # canvas width plus one cell of air
# The word is typed in backwards, a cell at a time, behind a grey head that walks in from the
# right edge and sets it open. The head is given whole cells of air to travel before it meets the
# mark, because a block whose only visible width is a sliver off the canvas edge is rounded away
# and looks frozen: `HEAD_FROM` is a cell right of the mark, `HEAD_IN` starts it at the edge.
HEAD_FROM = X0 + MARK_W * CELL + CELL
HEAD_IN = HEAD_FROM + ((W - HEAD_FROM - CELL) // CELL) * CELL
PAD = 2 * CELL                       # a head never gets narrower than this, so it stays legible
WORK = (HEAD_IN - HEAD_FROM) // CELL + TYPED + 4   # head steps, mark, then clear of it


def reveal():
    """Two beats, both built out of the grid.

    The page comes in as a wall of blocks laying themselves down in a ragged diagonal order, so it
    reads as being built rather than wiped. Only once the page is down does the word appear, one
    letter at a time, each cell snapping in with a quick squash and no travel."""
    page = [(c, r) for r in range(-1, ROWS + 1) for c in range(-1, COLS + 1)]
    bg_step = (2.6 * SLOW) / len(page)
    text_start = 2.6 * SLOW + 0.15
    out = [head()]

    # --- beat 1: the page. The order is a diagonal sweep with jitter so no two neighbours land
    # on the same beat; every block starts solid and is uncovered at its moment.
    page.sort(key=lambda p: (p[0] * 0.8 + p[1]) + rnd(p[0] * 7.3 + p[1] * 13.1) * 7)
    for i, (c, r) in enumerate(page):
        t0 = i * bg_step
        # full-bleed cells: blocks tile exactly, so the page reads as one surface at any scale
        out.append(f'<rect x="{c * CELL}" y="{r * CELL}" width="{CELL}" height="{CELL}" '
                   f'fill="{BG}" opacity="1">'
                   f'<set attributeName="opacity" to="0" begin="0s" end="{t0:.3f}s"/></rect>')

    # --- beat 2: the word. A single grey head is typed in from the right edge, over the word,
    # and opens a gap as it goes so each letter reads. It walks right to left because the word
    # then assembles the way it is read, and the tail is the late letter, which is what makes the
    # end feel finished. Steps are whole cells, so a line is complete before the head reaches it;
    # a plain wipe had been cutting shorter lines in half.
    for hc, r, _letter in sorted(half_cells(), key=lambda c: (c[1], -c[0]), reverse=True):
        x, y = to_px_half(hc, r)
        # the head edge rounds up to the cell it is in, so the ink starts on it and reads outward
        # it at half a cell a step (`sorted` makes that read the way it is typed in)
        t0 = text_start + ((HEAD_FROM - x) // CELL + 1) * TEXT_STEP
        out.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" fill="{INK}" opacity="0">'
            f'<set attributeName="opacity" to="1" begin="{t0:.3f}s"/></rect>')

    # One head, typed in from the right edge and opening the word as it goes. It only ever moves
    # left, a cell per step, so its edge is where the ink stops. It starts with a couple of cells
    # of width and no more: from the canvas edge it would be rounded off, and where the walk
    # continues off the mark a block only ever holds what is still worth showing.
    xs, widths = [HEAD_IN], [X_END - HEAD_IN]
    for step in range(1, WORK):
        g = HEAD_IN - step * CELL
        xs.append(g)
        widths.append(max(X_END - max(g - CELL, HEAD_FROM), PAD))
    # keyTimes have to close on 1, and the first steps share time 0 while the head is off screen
    lead = 2
    times = [max(step - lead, 0) / (WORK - 1 - lead) for step in range(WORK)]
    out.append(
        f'<rect x="{xs[0]}" y="{Y0}" width="{widths[0]}" height="{MARK_H * CELL}" fill="{GREY}">'
        f'<animate attributeName="x" values="{";".join(map(str, xs))}" '
        f'keyTimes="{";".join(f"{t:.4f}" for t in times)}" dur="{WORK * TEXT_STEP:.3f}s" '
        f'begin="{text_start - TEXT_STEP:.3f}s" fill="freeze" calcMode="discrete"/>'
        f'<animate attributeName="width" values="{";".join(map(str, widths))}" '
        f'keyTimes="{";".join(f"{t:.4f}" for t in times)}" dur="{WORK * TEXT_STEP:.3f}s" '
        f'begin="{text_start - TEXT_STEP:.3f}s" fill="freeze" calcMode="discrete"/></rect>')
    out.append("</svg>")
    return "".join(out)


if __name__ == "__main__":
    open("banner.svg", "w").write(still())
    open("banner-reveal.svg", "w").write(reveal())
    open("banner.json", "w").write(json.dumps(
        {"cell": CELL, "origin": [X0, Y0], "floor": FLOOR, "glyphs": GLYPHS, "word": WORD,
         "pitch": ADVANCE, "cells": list(cells())}, indent=1))
    print(f"mark {MARK_W}x{MARK_H} cells, {len(list(cells()))} lit squares")