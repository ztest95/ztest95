# the fight

The top of the profile README looks like plain text. It isn't. `fight-light.svg` and
`fight-dark.svg` are a 31-second animated SVG loop (pure SMIL, no JavaScript) that GitHub renders
as-is. Adapted from [bulletchicken/bulletchicken](https://github.com/bulletchicken/bulletchicken) —
thanks for the choreography.

## changing the copy

Edit `PARAS` near the top of `make_fight.py`, then regenerate. Line 4 is the one the fight works
with: `Building` is kicked apart and typed back in, `Ted.` becomes the hole and later the bear, and
the `pixel` / `weird` / `README,` words are sliced. Renaming them means updating the same strings
where they are looked up further down.

## building

Widths come from `widths.json`, measured once from the page font itself so a word and the letters
it scatters into occupy exactly the same run of pixels. If you change `FONT_STACK`, the font size or
the copy, re-measure first:

```
python3 -m venv .venv && .venv/bin/pip install pillow playwright
.venv/bin/python -m playwright install chromium
.venv/bin/python widths.py
.venv/bin/python make_fight.py
```

## previewing

`cairosvg` can't render SMIL, so frames are taken with headless Chromium:

```
.venv/bin/python shot.py fight-light.svg /tmp/frames 5.6 6.4 9.4 11.4
```

`sheet.py out.png /tmp/frames/*.png` tiles frames into one contact sheet. Both are for looking at
the loop only; GitHub never runs them.