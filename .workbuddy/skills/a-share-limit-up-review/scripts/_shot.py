# -*- coding: utf-8 -*-
"""通用渲染自检（Playwright + 系统 Chrome）

用法：python _shot.py <html路径> [滚动位置...]
    # 相对路径按当前工作目录解析；截图写到 <CWD>/out/_shot_<tag>_<i>.png
    # 同时枚举 div[id^="c_"] 容器尺寸与 canvas 数量，并回显控制台错误

注意：**必须用系统 Python 3.11 运行**（playwright 只装在那里）：
    C:/Users/Administrator/AppData/Local/Programs/Python/Python311/python.exe
"""
import sys, os
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
target = os.path.abspath(sys.argv[1])
scrolls = [int(x) for x in sys.argv[2:]] or [0]
tag = os.path.splitext(os.path.basename(target))[0]
outdir = os.path.join(os.getcwd(), "out")
os.makedirs(outdir, exist_ok=True)
url = "file:///" + target.replace("\\", "/")

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
        pg.screenshot(path=os.path.join(outdir, f"_shot_{tag}_{i}.png"))
        print("shot:", f"out/_shot_{tag}_{i}.png  @scroll={y}")
    info = pg.evaluate("""() => Array.from(document.querySelectorAll('div[id^="c_"]')).map(
        d => ({id:d.id, w:d.clientWidth, h:d.clientHeight, canvas:d.querySelectorAll('canvas').length}))""")
    print("图表容器:", info)
    print("控制台错误:", errs[:8] if errs else "无")
    b.close()
