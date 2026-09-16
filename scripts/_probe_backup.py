# -*- coding: utf-8 -*-
"""查看已有东财抓取中间结果 + 探测备份数据源"""
import sys, os, json
import requests

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")

print("=== 已抓到的东财板块(中途存档) ===")
p = os.path.join(OUT, "_tmp_tech_perf.json")
if os.path.exists(p):
    d = json.load(open(p, encoding="utf-8"))
    its = sorted(d.get("items", []), key=lambda x: -x["ret"])
    for x in its:
        print(f"  {x['name']:<20}{x['ret']*100:>+7.2f}%  低点{x['low_date']}  反弹{x['rebound_from_low']*100:>+6.2f}%")
    print("  fail:", d.get("fail"))

print("\n=== 探测备份数据源 ===")
S = requests.Session()
S.trust_env = False
S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"})

# 1) push2delay clist
try:
    r = S.get("https://push2delay.eastmoney.com/api/qt/clist/get",
              params={"pn": 1, "pz": 5, "po": 1, "np": 1, "fltt": 2, "invt": 2, "fid": "f3",
                      "fs": "m:90+t:3", "fields": "f12,f14,f3,f24,f25"}, timeout=8)
    j = r.json()
    diff = (j.get("data") or {}).get("diff")
    print("push2delay clist:", r.status_code, "条数:", len(diff) if diff else 0,
          (diff[0] if diff else r.text[:120]))
except Exception as e:
    print("push2delay clist ERR", type(e).__name__)

# 2) 同花顺板块日线
try:
    r = S.get("http://d.10jqka.com.cn/v6/line/bk_881121/01/last.js",
              headers={"Referer": "http://q.10jqka.com.cn/"}, timeout=8)
    print("同花顺 881121:", r.status_code, r.text[:160])
except Exception as e:
    print("同花顺 ERR", type(e).__name__)

# 3) 新浪概念板块
try:
    r = S.get("http://money.finance.sina.com.cn/q/view/newFLJK.php",
              params={"param": "class"}, timeout=8)
    r.encoding = "gbk"
    print("新浪板块:", r.status_code, r.text[:160])
except Exception as e:
    print("新浪 ERR", type(e).__name__)

# 4) 东财 push2his 是否解封
try:
    r = S.get("https://7.push2his.eastmoney.com/api/qt/stock/kline/get",
              params={"secid": "90.BK1036", "fields1": "f1,f2", "fields2": "f51,f53",
                      "klt": 101, "fqt": 1, "beg": "20260731", "end": "20260915"}, timeout=8)
    print("7.push2his:", r.status_code, len(r.text))
except Exception as e:
    print("7.push2his ERR", type(e).__name__)
