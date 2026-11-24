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


TEXT_STEP = 0.03                     # seconds between ink cells
BG_SECONDS = 3.4                     # the page's whole build
BG_LEAD = 0.6                        # nothing is down when the first frame paints
TEXT_START = 1.0                     # the word begins once the top strip is down
SPREAD = 160.0                       # how far a cell may be pulled forward at the corners
FLAT = 0.15                          # share of the run the front is held flat at the start
BUCKETS = 1500                        # slices of the run the rate is evened across


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
    # The page is padded and the row runs to COLS + 2, so a bare corner would wrap across the full
    # width on the padded rows at once. Ordinarily the front is near-isometric, but pulled flat
    # while all rows are still 2 cells in, so the build starts as a strip along the top and spills
    # into the rows underneath. `FLAT` share of the run is spent flattened.
    slant = 0.8 - 0.75 * FLAT * (1 - FLAT * (1 - FLAT) * 4)
    peak = 1.0 + (COLS + 1) * 0.55
    page.sort(key=lambda p: (((p[0] + 1) * 0.55 + (p[1] + 1)) + rnd(p[0] * 7.3 + p[1] * 13.1) * 7
                             - rnd(p[1] * 3.1 + p[0] * 19.7) * SPREAD
                             * max(0.0, 1 - abs((p[0] + 1) * 0.55 + (p[1] + 1)) / peak)))
    span = BG_SECONDS - BG_LEAD
    # Where each cell's turn sits in the run. On the bare diagonal a corner is short, so the first
    # and last cells are the only ones due and land in a batch; the order is equalised against time
    # instead. The cells are split into `BUCKETS` slices of the run and a slice that came up short
    # borrows spare cells from the wide diagonals past it, so the rate starts at one cell, climbs
    # evenly and falls back to one. `BUCKETS` 1 is the plain diagonal.
    n = len(page) - 1
    # Rather than slanting the shape, the final time is kept as the diagonal order — the rate is
    # even, so the strip stays sparse across the whole width instead of becoming solid and tall.
    band = [0] * BUCKETS
    for i, (c, row) in enumerate(page):
        b = min((i * BUCKETS) // (n + 1), BUCKETS - 1)
        band[b] += (((c + 1) * slant + (row + 1)) / peak)  # this slice's diagonal weight
    seen = 0.0
    for i, (c, row) in enumerate(page):
        b = min((i * BUCKETS) // (n + 1), BUCKETS - 1)
        u = ((b + seen / band[b]) if band[b] else b + 0.5) / BUCKETS
        t0 = BG_LEAD + span * u
        seen += 1.0
        if seen >= band[b]:
            seen = 0.0
        # full-bleed cells: blocks tile exactly, so the page reads as one surface at any scale
        out.append(f'<rect x="{c * CELL}" y="{row * CELL}" width="{CELL}" height="{CELL}" '
                   f'fill="{BG}" opacity="1">'
                   f'<set attributeName="opacity" to="0" begin="0s" end="{t0:.3f}s"/></rect>')

    # --- beat 2: the word, left to right. It starts once the top strip is down and the last of it
    # types while the final corner is still closing, so the two beats overlap rather than queue.
    for idx, (c, r, _letter) in enumerate(sorted(cells(), key=lambda c: (c[0], c[1]))):
        x, y = to_px(c, r)
        t0 = TEXT_START + idx * TEXT_STEP
        out.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" fill="{INK}" opacity="0">'
            f'<set attributeName="opacity" to="1" begin="{t0:.3f}s"/></rect>')
    out.append("</svg>")
    return "".join(out)


if __name__ == "__main__":
    open("banner-reveal.svg", "w").write(reveal())
    print(f"mark {MARK_W}x{MARK_H} cells, {len(list(cells()))} lit squares")
    print(f"page {BG_LEAD:.1f}s..{BG_SECONDS:.1f}s, word {TEXT_START:.2f}s..{TEXT_START + 46 * TEXT_STEP:.2f}s, "
          f"whole {max(BG_SECONDS, TEXT_START + 46 * TEXT_STEP):.2f}s")