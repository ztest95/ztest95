#!/usr/bin/env python3
"""Render real frames from a fight SVG with headless Chromium (cairosvg has no SMIL).
usage: shot.py SVG OUTDIR T [T ...]

The animation clock is driven by hand (setCurrentTime) so frames are exact and fast, and so a
timestamp past the end lands on the same pose the loop plays there."""
import os
import sys
from playwright.sync_api import sync_playwright

svg, outdir = sys.argv[1], sys.argv[2]
times = sorted(float(t) for t in sys.argv[3:])
os.makedirs(outdir, exist_ok=True)
with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page(viewport={"width": 830, "height": 277}, device_scale_factor=2)
    pg.goto("file://" + os.path.abspath(svg))
    pg.evaluate("document.querySelector('svg').pauseAnimations()")
    for t in times:
        pg.evaluate("t => document.querySelector('svg').setCurrentTime(t)", t)
        pg.screenshot(path=f"{outdir}/{t:05.2f}.png", clip={"x": 0, "y": 0, "width": 830, "height": 277})
        print(f"{outdir}/{t:05.2f}.png")
    b.close()