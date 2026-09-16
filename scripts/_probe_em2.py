# -*- coding: utf-8 -*-
import requests, time

s = requests.Session()
s.trust_env = False
s.headers.update({"User-Agent": "Mozilla/5.0 Chrome/120", "Referer": "https://quote.eastmoney.com/"})

for secid in ["90.BK1036", "90.BK1326", "90.BK1137", "90.BK0877", "90.BK1128", "90.BK1036"]:
    t = time.time()
    try:
        r = s.get("https://push2his.eastmoney.com/api/qt/stock/kline/get",
                  params={"secid": secid, "fields1": "f1,f2", "fields2": "f51,f53",
                          "klt": 101, "fqt": 1, "beg": "20260731", "end": "20260915"},
                  timeout=10)
        d = (r.json().get("data") or {})
        print(f"{secid}  {r.status_code}  name={d.get('name')}  klines={len(d.get('klines') or [])}  {time.time()-t:.2f}s")
    except Exception as e:
        print(f"{secid}  ERR {type(e).__name__}  {time.time()-t:.2f}s")
