# -*- coding: utf-8 -*-
"""最近两年(2025/2026) 2月各指数表现 vs 历史2月均值"""
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
    s = pd.Series(df["ret"].values, index=pd.PeriodIndex(df["d"].str[:7], freq="M"))
    P[it["name"]] = {"grp": it["group"], "s": s}

MAIN = ["上证指数", "深证成指", "沪深300", "中证500", "中证1000", "上证50", "创业板指", "创业板综",
        "科创50", "中证全指", "中小100", "上证380", "中证红利", "上证红利", "300成长",
        "中证消费", "中证医药", "中证金融", "中证信息", "全指能源", "全指材料", "全指工业",
        "全指可选", "全指消费", "全指医药", "全指金融", "全指信息", "全指通信", "全指公用",
        "中证白酒", "中证煤炭", "中证银行", "证券公司", "中证军工", "中证医疗", "中证新能",
        "中证传媒", "有色金属", "食品饮料", "医药生物", "细分化工", "细分有色", "中证农业",
        "科技100", "生物医药", "农林指数", "军工指数", "中证环保", "基建工程", "智能家居",
        "CS新能车", "移动互联", "中证TMT", "医药100", "大农业", "深证医药", "细分医药",
        "细分食品", "细分地产", "细分金融", "中证能源", "中证手机"]


def get(name, ym):
    d = P.get(name)
    if not d:
        return None
    try:
        v = d["s"].get(pd.Period(ym, freq="M"))
    except Exception:
        return None
    return None if v is None or pd.isna(v) else round(float(v) * 100, 2)


def hist_feb(name):
    d = P.get(name)
    if not d:
        return None, None
    s = d["s"].dropna()
    f = s[(s.index.month == 2) & (s.index.year <= 2026)]
    if len(f) < 5:
        return None, None
    return round(float(f.mean()) * 100, 2), round(float((f > 0).mean()) * 100, 1)


rows = []
for n in MAIN:
    if n not in P:
        continue
    a, b = get(n, "2025-02"), get(n, "2026-02")
    hm, hw = hist_feb(n)
    g = P[n]["grp"]
    if a is None and b is None:
        continue
    rows.append((n, g, a, b, hm, hw))

# 按 2026-02 降序
rows.sort(key=lambda r: (r[3] is None, -(r[3] or -999)))

print(f"{'品种':<12}{'组':<5}{'2025-02':>9}{'2026-02':>9}{'历史2月均':>10}{'历史胜率':>9}  距今起点")
for n, g, a, b, hm, hw in rows:
    print(f"{n:<12}{g:<5}{(a if a is not None else '-'):>9}{(b if b is not None else '-'):>9}"
          f"{(hm if hm is not None else '-'):>10}{(hw if hw is not None else '-'):>9}")

# 连续月份对照: 看春季躁动是否移位
print("\n\n=== 1-3月连续对照 (%) ===")
print(f"{'品种':<12}{'25-01':>8}{'25-02':>8}{'25-03':>8}  |{'26-01':>8}{'26-02':>8}{'26-03':>8}")
for n in ["上证指数", "深证成指", "沪深300", "中证500", "中证1000", "创业板指", "科创50",
          "中证红利", "上证红利", "中证白酒", "证券公司", "中证军工", "中证银行", "有色金属",
          "中证煤炭", "全指信息"]:
    if n not in P:
        continue
    v25 = [get(n, f"2025-0{m}") for m in (1, 2, 3)]
    v26 = [get(n, f"2026-0{m}") for m in (1, 2, 3)]
    f = lambda x: f"{x:>8.2f}" if x is not None else f"{'-':>8}"
    print(f"{n:<12}{f(v25[0])}{f(v25[1])}{f(v25[2])}  |{f(v26[0])}{f(v26[1])}{f(v26[2])}")

# 横截面广度
print("\n\n=== 2月横截面广度 ===")
for y in (2024, 2025, 2026):
    vals = []
    for n in P:
        v = get(n, f"{y}-02")
        if v is not None:
            vals.append(v)
    if vals:
        arr = np.array(vals)
        print(f"  {y}年2月: 上涨 {int((arr>0).sum())}/{len(arr)} ({(arr>0).mean()*100:.1f}%)  "
              f"中位数 {np.median(arr):+.2f}%  均值 {arr.mean():+.2f}%  最好 {arr.max():+.1f}%  最差 {arr.min():+.1f}%")

json.dump([{"name": r[0], "group": r[1], "y2025": r[2], "y2026": r[3],
            "hist_mean": r[4], "hist_win": r[5]} for r in rows],
          open(os.path.join(OUT, "feb_recent.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n-> out/feb_recent.json")
