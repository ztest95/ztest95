# banner

`make_banner.py` rebuilds the wordmark on an exact pixel lattice: every glyph pixel is one `CELL`
square and every gap is one `CELL`, so the grid scales by whole numbers with no seams. Glyphs are
the original 3 x 4 blocks, unchanged.

The canvas is a fixed 1500 x 400 (GitHub's cap) and transparent — no background rectangle — so it
keeps today's banner dimensions and the page background shows through. The mark is centred on both
axes. There are two files because the ink has to flip: `banner-light.svg` (dark ink) and
`banner-dark.svg` (light ink), each with a `-reveal` variant carrying the drop-in animation.

- `banner-{light,dark}.svg` — still
- `banner-reveal-{light,dark}.svg` — the drop-in animation
- `banner.json` — `cell`, `origin`, `floor`, glyphs and cells, for anything that wants the lattice

SMIL and inline attributes only. No JS, no CSS, no external font, since GitHub serves this through
an `<img>`.

```
python3 make_banner.py
python3 shot_banner.py /tmp/frames 0.5 2.0 6.0   # needs playwright + chromium
```
