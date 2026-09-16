# -*- coding: utf-8 -*-
"""抓取半导体材料四股 + 基准指数 2026-07 以来的日线（腾讯 fqkline），落盘 out/semimat_daily.json"""
import json, time, ssl, sys, io
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SYMS = {
    "sh603650": "彤程新材",
    "sh600206": "有研新材",
    "sz002409": "雅克科技",
    "sz300666": "江丰电子",
    "sh000688": "科创50",
}
START, END = "2026-07-01", "2026-09-16"
OUT = "out/semimat_daily.json"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch(sym, retry=4):
    url = ("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param="
           f"{sym},day,{START},{END},640,qfq")
    for i in range(retry):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://gu.qq.com/"})
            raw = urllib.request.urlopen(req, context=ctx, timeout=15).read().decode("utf-8")
            js = json.loads(raw)
            d = js["data"][sym]
            rows = d.get("qfqday") or d.get("day")
            if not rows:
                raise ValueError("empty rows")
            # 字段顺序: [日期, 开, 收, 高, 低, 量(手)]
            return [{"date": r[0], "open": float(r[1]), "close": float(r[2]),
                     "high": float(r[3]), "low": float(r[4]), "vol": float(r[5])} for r in rows]
        except Exception as e:
            print(f"  retry {i+1} {sym}: {e}")
            time.sleep(3 * (i + 1))
    return None

result = {}
for sym, name in SYMS.items():
    rows = fetch(sym)
    if rows is None:
        print(f"FAIL {sym} {name}")
        sys.exit(1)
    result[name] = {"sym": sym, "rows": rows}
    print(f"OK {name} {sym}: {len(rows)} bars, {rows[0]['date']} ~ {rows[-1]['date']}")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False)
print("saved", OUT)
