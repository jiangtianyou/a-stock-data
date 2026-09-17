# -*- coding: utf-8 -*-
"""通用渲染自检: python _shot.py <html相对路径> [滚动位置...]"""
import sys, os
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
target = sys.argv[1] if len(sys.argv) > 1 else "reports/a-share-seasonality.html"
scrolls = [int(x) for x in sys.argv[2:]] or [0]
tag = os.path.splitext(os.path.basename(target))[0]
url = "file:///" + os.path.join(BASE, target).replace("\\", "/")

with sync_playwright() as p:
    b = p.chromium.launch(args=["--no-sandbox", "--no-proxy-server"])
    pg = b.new_page(viewport={"width": 1280, "height": 1100})
    errs = []
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errs.append("PAGEERROR: " + str(e)))
    pg.goto(url, wait_until="load", timeout=45000)
    pg.wait_for_timeout(4500)
    for i, y in enumerate(scrolls):
        pg.evaluate(f"window.scrollTo(0, {y})")
        pg.wait_for_timeout(1400)
        pg.screenshot(path=os.path.join(BASE, "out", f"_shot_{tag}_{i}.png"))
        print("shot:", f"out/_shot_{tag}_{i}.png  @scroll={y}")
    info = pg.evaluate("""() => Array.from(document.querySelectorAll('div[id^="c_"]')).map(
        d => ({id:d.id, w:d.clientWidth, h:d.clientHeight, canvas:d.querySelectorAll('canvas').length}))""")
    print("图表容器:", info)
    print("控制台错误:", errs[:8] if errs else "无")
    b.close()
