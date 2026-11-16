#!/usr/bin/env python3
"""Frames from banner-reveal.svg at full 1500x400, cropped around the mark for looking at.
usage: shot_banner.py OUTDIR T [T ...]  (reads banner-reveal.svg)"""
import os
import sys
from playwright.sync_api import sync_playwright

outdir, times = sys.argv[1], sorted(float(t) for t in sys.argv[2:])
os.makedirs(outdir, exist_ok=True)
with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page(viewport={"width": 1500, "height": 400}, device_scale_factor=2)
    pg.goto("file://" + os.path.abspath("banner-reveal.svg"))
    pg.evaluate("document.querySelector('svg').pauseAnimations()")
    for t in times:
        pg.evaluate("t => document.querySelector('svg').setCurrentTime(t)", t)
        pg.screenshot(path=f"{outdir}/{t:05.2f}.png", clip={"x": 540, "y": 130, "width": 420, "height": 150})
        print(f"{outdir}/{t:05.2f}.png")
    b.close()