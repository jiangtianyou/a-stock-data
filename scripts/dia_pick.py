# -*- coding: utf-8 -*-
"""检查 ths_concept_all.json 中板块名称的编码情况，定位培育钻石板块"""
import json, sys, os
sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(BASE, "out", "ths_concept_all.json"), encoding="utf-8"))
items = d["items"]

# 用码点构造关键词，绝对避免源码编码问题
TARGET = "".join(chr(c) for c in (0x57F9, 0x80B2, 0x94BB, 0x77F3))  # 培育钻石
print("TARGET repr:", repr(TARGET), "len", len(TARGET))

hits = [it for it in items if TARGET in it["name"]]
print("hits:", len(hits))
for it in hits:
    print(f"  {it['name']}  code={it['code']}  ret={it['ret']*100:+.2f}%  "
          f"{it.get('base_date')}->{it.get('last_date')}  low={it.get('low_date')} "
          f"rebound={it.get('rd',0)*100:+.2f}%  n={it.get('n')}")

# 打印前 6 个名称的 repr，确认编码
for it in items[:6]:
    print("  sample:", repr(it["name"]), it["code"])
