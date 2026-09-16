# -*- coding: utf-8 -*-
"""探测东财 push2his 数字前缀镜像可用性"""
import requests, time

s = requests.Session()
s.trust_env = False
s.headers.update({"User-Agent": "Mozilla/5.0 Chrome/120", "Referer": "https://quote.eastmoney.com/"})

params = {"secid": "90.BK1036", "fields1": "f1,f2", "fields2": "f51,f53",
          "klt": 101, "fqt": 1, "beg": "20260731", "end": "20260915"}

PREFIX = ["", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13",
          "14", "15", "16", "17", "18", "19", "20", "22", "33", "44", "55", "66",
          "77", "88", "99", "21", "23", "24", "25"]
ok = []
for p in PREFIX:
    h = f"{p}.push2his.eastmoney.com" if p else "push2his.eastmoney.com"
    t = time.time()
    try:
        r = s.get(f"https://{h}/api/qt/stock/kline/get", params=params, timeout=5)
        d = (r.json().get("data") or {})
        n = len(d.get("klines") or [])
        if n:
            ok.append(h)
            print(f"{h:<34} OK  klines={n}  {time.time()-t:.2f}s")
        else:
            print(f"{h:<34} 200但空数据  {time.time()-t:.2f}s")
    except Exception as e:
        print(f"{h:<34} ERR {type(e).__name__}  {time.time()-t:.2f}s")
    time.sleep(0.2)

print("\n可用镜像:", ok)
