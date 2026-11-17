# banner

`make_banner.py` rebuilds the wordmark on an exact pixel lattice: every glyph pixel is one `CELL`
square and every gap is one `CELL`, so the grid scales by whole numbers with no seams. Glyphs are
the original 4 x 3 blocks, unchanged.

- `banner.svg` — still, drop-in replacement for `banner.png`
- `banner-reveal.svg` — two separate beats: the background wipes in from the left, then the word
  drops in letter by letter (bottom row first), squashing on contact and being pushed down by the
  row landing on it
- `banner.json` — `cell`, `origin`, `floor` and the lit cells, for anything that wants to drive the
  lattice

SMIL and inline attributes only. No JS, no CSS, no external font, since GitHub serves this through
an `<img>`.

```
python3 make_banner.py
python3 shot_banner.py /tmp/frames 0.2 0.6 1.0   # needs playwright + chromium
```