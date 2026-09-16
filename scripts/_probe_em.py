# -*- coding: utf-8 -*-
"""东财板块接口可用性测试"""
import requests, json

s = requests.Session()
s.trust_env = False
s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"})

# 1) 板块列表
try:
    r = s.get("https://push2.eastmoney.com/api/qt/clist/get",
              params={"pn": 1, "pz": 20, "po": 1, "np": 1, "fltt": 2, "invt": 2,
                      "fid": "f3", "fs": "m:90+t:3", "fields": "f12,f14,f3"},
              timeout=15)
    j = r.json()
    print("板块列表 status:", r.status_code)
    diff = (j.get("data") or {}).get("diff")
    if diff:
        for d in diff[:10]:
            print("   ", d.get("f12"), d.get("f14"))
    else:
        print("  data=", json.dumps(j, ensure_ascii=False)[:300])
except Exception as e:
    print("板块列表失败:", type(e).__name__, e)

# 2) 板块K线
try:
    r2 = s.get("https://push2his.eastmoney.com/api/qt/stock/kline/get",
               params={"secid": "90.BK1036", "fields1": "f1,f2,f3",
                       "fields2": "f51,f52,f53,f54,f55,f56", "klt": 101, "fqt": 1,
                       "beg": "20260725", "end": "20260915", "lmt": 60},
               timeout=15)
    j2 = r2.json()
    kl = ((j2.get("data") or {}).get("klines")) or []
    print("\n板块K线 status:", r2.status_code, "根数:", len(kl), "名称:", (j2.get("data") or {}).get("name"))
    for k in kl[:3]:
        print("   ", k)
except Exception as e:
    print("板块K线失败:", type(e).__name__, e)
