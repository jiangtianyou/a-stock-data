# -*- coding: utf-8 -*-
import requests, time

s = requests.Session()
s.trust_env = False
s.headers.update({"User-Agent": "Mozilla/5.0 Chrome/120", "Referer": "https://quote.eastmoney.com/"})

HOSTS = ["push2his.eastmoney.com", "1.push2his.eastmoney.com", "7.push2his.eastmoney.com",
         "82.push2his.eastmoney.com", "push2.eastmoney.com", "push2delay.eastmoney.com",
         "quote.eastmoney.com", "push2his.eastmoney.com"]

params = {"secid": "90.BK1036", "fields1": "f1,f2", "fields2": "f51,f53",
          "klt": 101, "fqt": 1, "beg": "20260731", "end": "20260915"}

for h in HOSTS:
    t = time.time()
    try:
        r = s.get(f"https://{h}/api/qt/stock/kline/get", params=params, timeout=8)
        d = (r.json().get("data") or {})
        print(f"{h:<32} {r.status_code}  klines={len(d.get('klines') or [])}  {time.time()-t:.2f}s")
    except Exception as e:
        print(f"{h:<32} ERR {type(e).__name__}  {time.time()-t:.2f}s")

# clist 是否还活着
t = time.time()
try:
    r = s.get("https://push2.eastmoney.com/api/qt/clist/get",
              params={"pn": 1, "pz": 5, "po": 1, "np": 1, "fltt": 2, "invt": 2,
                      "fid": "f3", "fs": "m:90+t:3", "fields": "f12,f14,f3"}, timeout=8)
    print("clist:", r.status_code, f"{time.time()-t:.2f}s", r.text[:150])
except Exception as e:
    print("clist ERR", type(e).__name__, f"{time.time()-t:.2f}s")
