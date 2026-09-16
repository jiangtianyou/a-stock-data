# -*- coding: utf-8 -*-
"""验证新浪板块 K 线链路"""
import sys, json, re
import requests

sys.stdout.reconfigure(encoding="utf-8")
S = requests.Session()
S.trust_env = False
S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"})

# 1) 概念板块列表
r = S.get("http://money.finance.sina.com.cn/q/view/newFLJK.php", params={"param": "class"}, timeout=10)
r.encoding = "gbk"
txt = r.text
print("概念板块列表 长度:", len(txt))
m = re.search(r"=\s*(\{.*\})", txt, re.S)
if m:
    d = json.loads(m.group(1))
    print("概念板块数:", len(d))
    for i, (k, v) in enumerate(list(d.items())[:6]):
        print("   ", k, "->", v.split(",")[:3])

# 2) 行业板块列表
r2 = S.get("http://money.finance.sina.com.cn/q/view/newFLJK.php", params={"param": "industry"}, timeout=10)
r2.encoding = "gbk"
m2 = re.search(r"=\s*(\{.*\})", r2.text, re.S)
if m2:
    d2 = json.loads(m2.group(1))
    print("行业板块数:", len(d2))
    for k, v in list(d2.items())[:6]:
        print("   ", k, "->", v.split(",")[:3])

# 3) 板块 K 线
for sym in ["gn_hwqc", "gn_ai", "gn_5g"]:
    try:
        rk = S.get("http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData",
                   params={"symbol": sym, "scale": 240, "ma": "no", "datalen": 60}, timeout=10)
        print(f"\nK线 {sym}: status={rk.status_code} len={len(rk.text)}")
        print("  ", rk.text[:300])
    except Exception as e:
        print(f"K线 {sym} ERR", type(e).__name__)

# 4) 同花顺完整返回
try:
    rt = S.get("http://d.10jqka.com.cn/v6/line/bk_881121/01/last.js",
               headers={"Referer": "http://q.10jqka.com.cn/"}, timeout=10)
    print("\n同花顺 881121 完整:", rt.text[:500])
except Exception as e:
    print("同花顺 ERR", type(e).__name__)
