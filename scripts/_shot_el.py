# -*- coding: utf-8 -*-
"""按元素定位截图: python _shot_el.py <html相对路径> <css选择器> [前后留白px]"""
import sys, os
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
target = sys.argv[1]
sel = sys.argv[2]
pad = int(sys.argv[3]) if len(sys.argv) > 3 else 40
tag = os.path.splitext(os.path.basename(target))[0]
url = "file:///" + os.path.join(BASE, target).replace("\\", "/")

with sync_playwright() as p:
    b = p.chromium.launch(args=["--no-sandbox", "--no-proxy-server"])
    pg = b.new_page(viewport={"width": 1280, "height": 1100})
    pg.goto(url, wait_until="load", timeout=45000)
    pg.wait_for_timeout(4500)
    y = pg.evaluate(
        "(s) => {const e=document.querySelector(s); if(!e) return null;"
        "return e.getBoundingClientRect().top + window.scrollY;}", sel)
    if y is None:
        print("元素未找到:", sel)
    else:
        pg.evaluate("window.scrollTo(0, %d)" % max(0, int(y) - pad))
        pg.wait_for_timeout(1400)
        out = os.path.join(BASE, "out", "_shot_el_%s.png" % tag)
        pg.screenshot(path=out)
        print("shot:", out, "@top=", int(y))
    b.close()
