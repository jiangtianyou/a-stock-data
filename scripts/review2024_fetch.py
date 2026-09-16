# -*- coding: utf-8 -*-
"""
2024 年小盘股行情复盘 - 数据抓取
数据源: 腾讯财经日线(前复权), 含成交量
输出: out/review2024_raw.json
"""
import sys, os, json, time, random
import requests

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")

S = requests.Session()
S.trust_env = False
S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
                  "Referer": "https://gu.qq.com/"})

# 候选: 含中证2000 的多种前缀变体, 用于试探哪个可用
CANDS = [
    ("sz399303", "国证2000", "小盘"),
    ("sh000852", "中证1000", "小盘"),
    ("sh000905", "中证500", "中盘"),
    ("sh000300", "沪深300", "大盘"),
    ("sh000016", "上证50", "大盘"),
    ("sh000001", "上证指数", "大盘"),
    ("sz399001", "深证成指", "大盘"),
    ("sz399006", "创业板指", "成长"),
    ("sh000688", "科创50", "成长"),
    ("sz399997", "中证白酒", "主题"),
    ("sz399975", "证券公司", "主题"),
    ("sh932000", "中证2000", "小盘"),
    ("sz932000", "中证2000", "小盘"),
]
A, B = "2023-06-01", "2025-02-01"

_last = [0.0]


def get(url, params, mi=0.6, retries=4):
    for i in range(retries):
        w = mi - (time.time() - _last[0])
        if w > 0:
            time.sleep(w + random.uniform(0.05, 0.2))
        try:
            _last[0] = time.time()
            r = S.get(url, params=params, timeout=25)
            if r.status_code == 200 and r.text.strip():
                return r.json()
        except Exception:
            pass
        time.sleep(0.8 * (2 ** i))
    return None


def day(sym, a=A, b=B, n=600):
    j = get("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get",
            {"param": f"{sym},day,{a},{b},{n},qfq"})
    if not j:
        return None
    d = (j.get("data") or {}).get(sym) or {}
    kl = d.get("qfqday") or d.get("day") or []
    rows = []
    for k in kl:
        try:
            rows.append({"d": k[0], "o": float(k[1]), "c": float(k[2]),
                         "h": float(k[3]), "l": float(k[4]), "v": float(k[5])})
        except Exception:
            continue
    return rows or None


res, fail = [], []
for sym, nm, grp in CANDS:
    rows = day(sym)
    if rows and len(rows) >= 200:
        res.append({"sym": sym, "name": nm, "group": grp, "rows": rows})
        print(f"  {nm:<10} {len(rows):>4}个交易日  {rows[0]['d']} -> {rows[-1]['d']}")
    else:
        fail.append(nm)
        print(f"  {nm:<10} 无数据 ({len(rows) if rows else 0})")
    time.sleep(random.uniform(0.3, 0.6))

json.dump({"fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"), "range": [A, B],
           "count": len(res), "items": res},
          open(os.path.join(OUT, "review2024_raw.json"), "w", encoding="utf-8"), ensure_ascii=False)
print(f"\n成功 {len(res)}/{len(CANDS)}  失败 {fail}")
