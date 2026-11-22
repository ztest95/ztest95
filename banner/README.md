# banner

`make_banner.py` rebuilds the wordmark on an exact pixel lattice: every glyph pixel is one `CELL`
square and every gap is one `CELL`, so the grid scales by whole numbers with no seams. Glyphs are
the original 3 x 4 blocks.

- `banner-reveal.svg` — the banner. Its background builds in cell by cell in a ragged diagonal,
  then the word types itself in left to right.
- `make_banner.py` — the generator
- `shot_banner.py` — frames out of the reveal, for looking at

SMIL and inline attributes only. No JS, no CSS, no external font, since GitHub serves this through
an `<img>`.

```
python3 make_banner.py
python3 shot_banner.py /tmp/frames 0.2 0.6 1.0   # needs playwright + chromium
```