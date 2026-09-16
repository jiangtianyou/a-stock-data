# -*- coding: utf-8 -*-
"""提取 HTML 中的内联 JS 并用 node --check 校验"""
import sys, os, re, subprocess
sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NODE = r"C:\Users\Administrator\.workbuddy\binaries\node\versions\22.22.2-3\node.exe"

fn = sys.argv[1]
p = fn if os.path.isabs(fn) else os.path.join(BASE, fn)
html = open(p, encoding="utf-8").read()
blocks = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, re.S)
js = "\n;\n".join(b for b in blocks if b.strip())
tmp = os.path.join(BASE, "out", "_check.js")
open(tmp, "w", encoding="utf-8").write(js)
r = subprocess.run([NODE, "--check", tmp], capture_output=True, text=True, encoding="utf-8")
print(f"JS blocks: {len(blocks)}  chars: {len(js)}")
print("node --check:", "OK" if r.returncode == 0 else "FAIL")
if r.returncode != 0:
    print(r.stdout, r.stderr)
sys.exit(r.returncode)
