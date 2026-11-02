#!/usr/bin/env python3
"""Record the real advance widths of the page font so words and their letter-scatter share one
metric. Run once after changing FONT_SIZE / FONT_STACK in make_fight.py."""
import json
from playwright.sync_api import sync_playwright

FONT_STACK = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
CHARS = "".join(chr(c) for c in range(32, 127)) + "…'—"

with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page()
    pg.set_content(f"<body style='margin:0'><span id='m' style=\"font-family:{FONT_STACK};font-size:16px;white-space:pre\"></span></body>")
    out = {}
    for ch in CHARS:
        w = pg.evaluate("c => { const m = document.getElementById('m'); m.textContent = c; return m.getBoundingClientRect().width; }", ch)
        out[ch] = round(w, 3)
    w = pg.evaluate("() => { const m = document.getElementById('m'); m.style.fontWeight = '700'; m.textContent = 'x'; return m.getBoundingClientRect().width; }")
    out["__bold_x"] = round(w, 3)
    b.close()

json.dump(out, open("widths.json", "w"), indent=0, sort_keys=True)
print(len(out), "characters")
