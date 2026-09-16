# -*- coding: utf-8 -*-
"""专项: 2月/6月效应逐年明细, 检验近年是否仍成立"""
import sys, os, json
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")

raw = json.load(open(os.path.join(OUT, "seasonality_raw.json"), encoding="utf-8"))
cur = pd.Timestamp.today().strftime("%Y-%m")

panel = {}
for it in raw["items"]:
    df = pd.DataFrame(it["rows"])
    df = df[(df["d"].str[:7] < cur) & (df["d"].str[:7] >= "2000-01")]
    if len(df) < 60:
        continue
    df = df.sort_values("d").reset_index(drop=True)
    df["ret"] = df["c"].pct_change()
    panel[it["name"]] = pd.Series(df["ret"].values, index=pd.PeriodIndex(df["d"].str[:7], freq="M"))
P = pd.DataFrame(panel)
YEARS = list(range(2000, 2027))


def series_of(name, month):
    s = P[name].dropna()
    s = s[s.index.month == month]
    return {str(p.year): round(float(v) * 100, 2) for p, v in s.items()}


def show(name, month, ref=None):
    a = series_of(name, month)
    print(f"\n{name} | {month}月 逐年收益(%)")
    ys = [y for y in YEARS if str(y) in a]
    line = []
    for y in ys:
        v = a[str(y)]
        line.append(f"{y}:{v:+.1f}")
    # 每行10个
    for i in range(0, len(line), 9):
        print("   " + "  ".join(line[i:i + 9]))
    vals = [a[str(y)] for y in ys]
    up = sum(1 for v in vals if v > 0)
    print(f"   平均 {np.mean(vals):+.2f}%  中位 {np.median(vals):+.2f}%  上涨 {up}/{len(vals)}")
    recent = [a[str(y)] for y in ys if y >= 2016]
    if recent:
        print(f"   2016年以来: 平均 {np.mean(recent):+.2f}%  上涨 {sum(1 for v in recent if v>0)}/{len(recent)}  "
              f"明细 {[round(v,1) for v in recent]}")


show("中证500", 2)
show("上证指数", 2)
show("中证1000", 2)
show("创业板综", 2)
show("上证红利", 6)
show("中证红利", 6)

# 全市场 2 月横截面胜率(每年)
print("\n\n各年 2 月: 全样本品种上涨占比")
feb = P[P.index.month == 2]
for y in YEARS:
    row = feb[feb.index.year == y]
    if row.empty:
        continue
    r = row.iloc[0].dropna()
    if len(r) < 10:
        continue
    print(f"   {y}: 上涨 {int((r>0).sum()):>2}/{len(r):<3} ({(r>0).mean()*100:>5.1f}%)  中位数 {r.median()*100:>+6.2f}%")

# 中证500 十二个月画像
print("\n\n中证500 十二个月画像 (2005-2026)")
s = P["中证500"].dropna()
for m in range(1, 13):
    x = s[s.index.month == m]
    if len(x) < 8:
        continue
    print(f"   {m:>2}月: 均 {x.mean()*100:>+6.2f}%  中位 {x.median()*100:>+6.2f}%  胜率 {(x>0).mean()*100:>5.1f}%  "
          f"最差 {x.min()*100:>+6.1f}%  最好 {x.max()*100:>+6.1f}%  n={len(x)}")
