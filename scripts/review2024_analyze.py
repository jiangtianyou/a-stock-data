# -*- coding: utf-8 -*-
"""
2024 年小盘股行情复盘 - 分析
输入: out/review2024_raw.json
输出: out/review2024_stats.json
"""
import sys, os, json
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")

raw = json.load(open(os.path.join(OUT, "review2024_raw.json"), encoding="utf-8"))
P, V = {}, {}
meta = {}
for it in raw["items"]:
    df = pd.DataFrame(it["rows"])
    df = df.sort_values("d").reset_index(drop=True)
    df["ret"] = df["c"].pct_change()
    P[it["name"]] = pd.Series(df["ret"].values, index=df["d"])
    V[it["name"]] = pd.Series(df["v"].values, index=df["d"])
    meta[it["name"]] = {"group": it["group"], "sym": it["sym"]}
C = pd.DataFrame({k: [None] * len(v) for k, v in P.items()})  # placeholder
CLOSE = {}
for it in raw["items"]:
    df = pd.DataFrame(it["rows"]).sort_values("d")
    CLOSE[it["name"]] = pd.Series(df["c"].values, index=df["d"])
CL = pd.DataFrame(CLOSE)


def ret(name, a, b):
    s = CL[name].dropna()
    s = s[(s.index >= a) & (s.index <= b)]
    if len(s) < 2:
        return None
    return round((s.iloc[-1] / s.iloc[0] - 1) * 100, 2)


SEGS = [
    ("前期抱团", "2023-06-01", "2024-01-02"),
    ("暴跌", "2024-01-02", "2024-02-05"),
    ("V型反弹", "2024-02-05", "2024-03-21"),
    ("二次探底", "2024-03-21", "2024-09-18"),
    ("924暴涨", "2024-09-18", "2024-10-08"),
    ("年末震荡", "2024-10-08", "2024-12-31"),
    ("2024全年", "2024-01-02", "2024-12-31"),
    ("底部到年末", "2024-02-05", "2024-12-31"),
]

ORDER = ["国证2000", "中证1000", "中证500", "深证成指", "上证指数", "沪深300",
         "上证50", "创业板指", "科创50", "证券公司", "中证白酒"]

print("=== 分段涨跌幅 (%) ===")
hdr = f"{'指数':<10}" + "".join(f"{s[0]:>10}" for s in SEGS)
print(hdr)
seg_data = {}
for name in ORDER:
    if name not in CL:
        continue
    vals = []
    print(f"{name:<10}", end="")
    for tag, a, b in SEGS:
        v = ret(name, a, b)
        vals.append(v)
        print(f"{(v if v is not None else '-'):>10}", end="")
    print()
    seg_data[name] = {"group": meta[name]["group"], "segs": vals}

# 关键高/低点
print("\n=== 2024 年内关键点位 ===")
for name in ["国证2000", "中证1000", "中证500", "沪深300"]:
    s = CL[name].dropna()
    s24 = s[(s.index >= "2024-01-01") & (s.index <= "2024-12-31")]
    hi, lo = s24.idxmax(), s24.idxmin()
    print(f"  {name:<8} 年内最高 {hi} ({s24.max():.0f})   年内最低 {lo} ({s24.min():.0f})   "
          f"最大回撤 {(s24.min()/s24.cummax().max()-1)*100:.2f}%")

# 暴跌期跌幅梯度
print("\n=== 暴跌期(2024-01-02 ~ 2024-02-05) 跌幅梯度 ===")
grad = []
for name in ORDER:
    if name not in CL:
        continue
    s = CL[name].dropna()
    a = s[s.index >= "2024-01-02"].iloc[0]
    seg = s[(s.index >= "2024-01-02") & (s.index <= "2024-02-05")]
    low = seg.min()
    grad.append((name, meta[name]["group"], round((low / a - 1) * 100, 2), seg.idxmin()))
for g in sorted(grad, key=lambda x: x[2]):
    print(f"  {g[0]:<10}{g[1]:<6}{g[2]:>8.2f}%   低点 {g[3]}")

# 单日极端
print("\n=== 最惨单日跌幅 TOP6 (2024年, 各指数) ===")
for name in ["国证2000", "中证1000", "中证500", "沪深300"]:
    s = P[name].dropna()
    s = s[(s.index >= "2024-01-01") & (s.index <= "2024-12-31")]
    worst = s.nsmallest(6)
    print(f"  {name}: " + "  ".join(f"{d[5:]}:{v*100:+.2f}%" for d, v in worst.items()))
print("\n=== 最强单日涨幅 TOP6 (2024年) ===")
for name in ["国证2000", "中证1000", "中证500", "沪深300"]:
    s = P[name].dropna()
    s = s[(s.index >= "2024-01-01") & (s.index <= "2024-12-31")]
    best = s.nlargest(6)
    print(f"  {name}: " + "  ".join(f"{d[5:]}:{v*100:+.2f}%" for d, v in best.items()))

# 成交量: 暴跌期 vs 基准
print("\n=== 成交量(相对2023年6月-12月均值) ===")
periods = [("2023-06~12", "2023-06-01", "2023-12-31"),
           ("2024-01上旬", "2024-01-01", "2024-01-19"),
           ("2024-01下旬", "2024-01-22", "2024-01-31"),
           ("暴跌末段", "2024-02-01", "2024-02-05"),
           ("反弹期", "2024-02-06", "2024-03-21"),
           ("二次探底", "2024-08-01", "2024-09-18"),
           ("924行情", "2024-09-24", "2024-10-08")]
print(f"{'指数':<10}" + "".join(f"{p[0]:>13}" for p in periods))
vol_data = {}
for name in ["国证2000", "中证1000", "中证500", "沪深300"]:
    v = V[name].dropna()
    base = v[(v.index >= "2023-06-01") & (v.index <= "2023-12-31")].mean()
    vals = []
    print(f"{name:<10}", end="")
    for tag, a, b in periods:
        x = v[(v.index >= a) & (v.index <= b)]
        r = round(x.mean() / base * 100, 1) if len(x) else None
        vals.append(r)
        print(f"{(r if r is not None else '-'):>13}", end="")
    print()
    vol_data[name] = vals

json.dump({"segs": [[t[0], t[1], t[2]] for t in SEGS], "seg_data": seg_data,
           "grad": grad, "vol": vol_data, "vol_periods": [p[0] for p in periods],
           "order": ORDER},
          open(os.path.join(OUT, "review2024_stats.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n-> out/review2024_stats.json")
