#!/usr/bin/env python3
"""
make_banner.py  ·  builds banner-reveal.svg, the banner.

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


TEXT_STEP = 0.121                    # seconds between ink cells (scaled with the build)
BG_SECONDS = 9.0                     # the page's whole build
BG_LEAD = 1.2                        # nothing is down when the first frame paints
SPREAD = 700.0                       # how far a cell may be pulled forward at the corners


def reveal():
    """Two beats, both built out of the grid.

    The page comes in as a wall of blocks laying themselves down in a ragged diagonal order, so it
    reads as being built rather than wiped. Only once the page is down does the word appear, left
    to right, one letter at a time."""
    page = [(c, r) for r in range(-1, ROWS + 1) for c in range(-1, COLS + 1)]
    out = [head()]

    # --- beat 1: the page. A ragged diagonal with jitter, so no two neighbours land together and
    # the edge scatters. The race is in the order, not the pace: a corner diagonal only has a few
    # neighbours, so taking cells in diagonal order puts a fraction of them at each end. The order
    # is loosened instead, each cell's turn shuffled by a spread that is wide where the diagonal is
    # short and tight in the middle, so the corners give up their cells early and keep landing
    # while the front passes.
    peak = ROWS + COLS * 0.8
    page.sort(key=lambda p: ((p[0] * 0.8 + p[1]) + rnd(p[0] * 7.3 + p[1] * 13.1) * 7
                             - rnd(p[1] * 3.1 + p[0] * 19.7) * SPREAD
                             * max(0.0, 1 - abs(p[0] * 0.8 + p[1]) / peak)))
    span = BG_SECONDS - BG_LEAD
    for i, (c, r) in enumerate(page):
        t0 = BG_LEAD + span * i / (len(page) - 1)
        # full-bleed cells: blocks tile exactly, so the page reads as one surface at any scale
        out.append(f'<rect x="{c * CELL}" y="{r * CELL}" width="{CELL}" height="{CELL}" '
                   f'fill="{BG}" opacity="1">'
                   f'<set attributeName="opacity" to="0" begin="0s" end="{t0:.3f}s"/></rect>')

    # --- beat 2: the word, left to right, started while the last band is still closing behind it
    text_start = BG_LEAD + span
    for idx, (c, r, _letter) in enumerate(sorted(cells(), key=lambda c: (c[0], c[1]))):
        x, y = to_px(c, r)
        t0 = text_start + idx * TEXT_STEP
        out.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" fill="{INK}" opacity="0">'
            f'<set attributeName="opacity" to="1" begin="{t0:.3f}s"/></rect>')
    out.append("</svg>")
    return "".join(out)


if __name__ == "__main__":
    open("banner-reveal.svg", "w").write(reveal())
    print(f"mark {MARK_W}x{MARK_H} cells, {len(list(cells()))} lit squares")