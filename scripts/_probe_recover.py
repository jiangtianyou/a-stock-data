# -*- coding: utf-8 -*-
"""测试东财各域名 K 线接口是否恢复"""
import requests, time

s = requests.Session()
s.trust_env = False
s.headers.update({"User-Agent": "Mozilla/5.0 Chrome/120", "Referer": "https://quote.eastmoney.com/"})

params = {"secid": "90.BK1036", "fields1": "f1,f2", "fields2": "f51,f53",
          "klt": 101, "fqt": 1, "beg": "20260731", "end": "20260915"}

HOSTS = ["push2his.eastmoney.com", "7.push2his.eastmoney.com", "push2.eastmoney.com",
         "hsmarketwg.eastmoney.com", "emhsmarketwg.eastmoney.com", "wap.eastmoney.com",
         "quote.eastmoney.com", "datacenter-web.eastmoney.com"]

for h in HOSTS:
    t = time.time()
    try:
        r = s.get(f"https://{h}/api/qt/stock/kline/get", params=params, timeout=6)
        d = (r.json().get("data") or {})
        print(f"{h:<34} {r.status_code} klines={len(d.get('klines') or [])} {time.time()-t:.2f}s")
    except Exception as e:
        print(f"{h:<34} ERR {type(e).__name__} {time.time()-t:.2f}s")

# 同花顺概念板块代码抽样
print("\n--- 同花顺板块代码抽样 ---")
for c in [885401, 885500, 885600, 885700, 885800, 885900, 886000, 881200, 881300, 881400]:
    try:
        r = s.get(f"http://d.10jqka.com.cn/v6/line/bk_{c}/01/last.js",
                  headers={"Referer": "http://q.10jqka.com.cn/"}, timeout=6)
        n = "有" if '"name"' in r.text else "无"
        import re
        m = re.search(r'"name":"([^"]+)"', r.text)
        print(f"  bk_{c}: {n} {m.group(1) if m else ''}")
    except Exception as e:
        print(f"  bk_{c}: ERR {type(e).__name__}")
