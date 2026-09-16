# -*- coding: utf-8 -*-
"""枚举同花顺板块代码,建立 代码->名称 映射"""
import sys, re, json, time
import requests

sys.stdout.reconfigure(encoding="utf-8")
S = requests.Session()
S.trust_env = False
S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
                  "Referer": "http://q.10jqka.com.cn/"})

found = {}


def probe(code):
    try:
        r = S.get(f"http://d.10jqka.com.cn/v6/line/{code}/01/last.js", timeout=6)
        if r.status_code != 200 or "name" not in r.text:
            return None
        m = re.search(r'"name":"([^"]+)"', r.text)
        if not m:
            return None
        return m.group(1)
    except Exception:
        return None


ranges = [("bk_%d" % c) for c in range(881101, 881181)] + \
         [("bk_%d" % c) for c in range(885300, 885400)]

for i, code in enumerate(ranges, 1):
    n = probe(code)
    if n:
        found[code] = n
    time.sleep(0.12)

print(f"共找到 {len(found)} 个板块")
for k, v in found.items():
    print(f"  {k}  {v}")
json.dump(found, open("D:/Desktop/Playground/a-stock-data/out/_ths_codes.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
