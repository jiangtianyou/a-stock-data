# -*- coding: utf-8 -*-
"""提取 HTML 中的内联 JS 并用 node --check 校验

用法：python _check_js.py <html路径>   # 相对路径按当前工作目录解析
退出码 = node --check 的退出码（0 = 通过）
"""
import sys, os, re, subprocess, tempfile
sys.stdout.reconfigure(encoding="utf-8")
NODE = r"C:\Users\Administrator\.workbuddy\binaries\node\versions\22.22.2-3\node.exe"

p = os.path.abspath(sys.argv[1])
html = open(p, encoding="utf-8").read()
blocks = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, re.S)
js = "\n;\n".join(b for b in blocks if b.strip())
tmp = os.path.join(tempfile.gettempdir(), "_check_inline.js")
open(tmp, "w", encoding="utf-8").write(js)
r = subprocess.run([NODE, "--check", tmp], capture_output=True, text=True, encoding="utf-8")
print(f"JS blocks: {len(blocks)}  chars: {len(js)}")
print("node --check:", "OK" if r.returncode == 0 else "FAIL")
if r.returncode != 0:
    print(r.stdout, r.stderr)
sys.exit(r.returncode)
