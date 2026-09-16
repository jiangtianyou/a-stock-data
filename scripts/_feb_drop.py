# -*- coding: utf-8 -*-
"""定位"2月小盘股暴跌"的年份: 历年2月大小盘表现与分化"""
import sys, os, json
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")

raw = json.load(open(os.path.join(OUT, "seasonality_raw.json"), encoding="utf-8"))
P = {}
for it in raw["items"]:
    df = pd.DataFrame(it["rows"])
    if len(df) < 24:
        continue
    df = df.sort_values("d").reset_index(drop=True)
    df["ret"] = df["c"].pct_change()
    P[it["name"]] = pd.Series(df["ret"].values, index=pd.PeriodIndex(df["d"].str[:7], freq="M"))


def r(name, ym):
    if name not in P:
        return None
    v = P[name].get(pd.Period(ym, freq="M"))
    return None if v is None or pd.isna(v) else float(v) * 100


SMALL = "中证1000"
BIG = "沪深300"

print(f"{'年份':<6}{'中证1000(小)':>13}{'沪深300(大)':>12}{'上证指数':>10}{'创业板指':>10}{'上证50':>9}{'小-大':>9}")
rows = []
for y in range(2006, 2027):
    ym = f"{y}-02"
    s, b, si, cy, sz50 = r(SMALL, ym), r(BIG, ym), r("上证指数", ym), r("创业板指", ym), r("上证50", ym)
    if s is None and b is None:
        continue
    diff = (s - b) if (s is not None and b is not None) else None
    f = lambda v, w=7: f"{v:>{w}.2f}" if v is not None else f"{'-':>{w}}"
    print(f"{y:<6}{f(s,13)}{f(b,12)}{f(si,10)}{f(cy,10)}{f(sz50,9)}{f(diff,9)}")
    rows.append({"y": y, "small": s, "big": b, "sh": si, "cyb": cy, "sz50": sz50, "diff": diff})

print("\n=== 按「小盘跌幅」排序 (最惨的5个2月) ===")
for x in sorted([r for r in rows if r["small"] is not None], key=lambda z: z["small"])[:5]:
    print(f"  {x['y']}年2月: 中证1000 {x['small']:+.2f}%  沪深300 {x['big']:+.2f}%  小-大 {x['diff']:+.2f}pct")

print("\n=== 按「小盘跑输大盘」排序 (最极端的5个2月) ===")
for x in sorted([r for r in rows if r["diff"] is not None], key=lambda z: z["diff"])[:5]:
    print(f"  {x['y']}年2月: 中证1000 {x['small']:+.2f}%  沪深300 {x['big']:+.2f}%  小-大 {x['diff']:+.2f}pct")

print("\n=== 相邻1月对照 (看暴跌是否起始于1月) ===")
print(f"{'年份':<6}{'1月中证1000':>13}{'1月沪深300':>12}{'2月中证1000':>13}{'2月沪深300':>12}{'1-2月小-大':>13}")
for y in [2016, 2018, 2022, 2024, 2025, 2026]:
    s1, b1 = r(SMALL, f"{y}-01"), r(BIG, f"{y}-01")
    s2, b2 = r(SMALL, f"{y}-02"), r(BIG, f"{y}-02")
    f = lambda v, w=9: f"{v:>{w}.2f}" if v is not None else f"{'-':>{w}}"
    cum = (s1 + s2 - b1 - b2) if None not in (s1, s2, b1, b2) else None
    print(f"{y:<6}{f(s1,13)}{f(b1,12)}{f(s2,13)}{f(b2,12)}{f(cum,13)}")

json.dump(rows, open(os.path.join(OUT, "feb_drop.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n-> out/feb_drop.json")
