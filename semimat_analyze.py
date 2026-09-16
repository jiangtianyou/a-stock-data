# -*- coding: utf-8 -*-
"""半导体材料四股 8月以来走势对比分析，输出 out/semimat_stats.json"""
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open("out/semimat_daily.json", encoding="utf-8") as f:
    data = json.load(f)

BASE = "2026-07-31"   # 8月起点基期 = 7月收盘
CUT  = "2026-09-16"   # 个股数据截止

def series(name):
    rows = [r for r in data[name]["rows"] if r["date"] <= CUT]
    return rows

stats = {}
norm = {}   # 归一化序列（基期=100），用于对比图
for name in list(data.keys()):
    rows = series(name)
    dates = [r["date"] for r in rows]
    closes = [r["close"] for r in rows]
    vols = [r["vol"] for r in rows]
    bi = dates.index(BASE)
    b = closes[bi]
    n = len(closes)

    # 最大回撤（含峰值日）
    peak, pk_at, mdd, mdd_from, mdd_to = closes[bi], dates[bi], 0.0, None, None
    for i in range(bi, n):
        if closes[i] > peak:
            peak, pk_at = closes[i], dates[i]
        dd = closes[i] / peak - 1
        if dd < mdd:
            mdd, mdd_from, mdd_to = dd, pk_at, dates[i]

    hi_i = bi + closes[bi:].index(max(closes[bi:]))
    lo_i = bi + closes[bi:].index(min(closes[bi:]))

    aug = closes[[i for i,d in enumerate(dates) if d.startswith("2026-08")][-1]] / b - 1
    sep = closes[-1] / closes[[i for i,d in enumerate(dates) if d.startswith("2026-09")][0] - 1] - 1

    rets = [closes[i]/closes[i-1]-1 for i in range(bi+1, n)]
    up_days = sum(1 for r in rets if r > 0)
    std = (sum((r - sum(rets)/len(rets))**2 for r in rets)/ (len(rets)-1)) ** 0.5

    vols_aug = [vols[i] for i,d in enumerate(dates) if d.startswith("2026-08")]
    vols_sep = [vols[i] for i,d in enumerate(dates) if d.startswith("2026-09")]

    stats[name] = {
        "sym": data[name]["sym"],
        "base_close": b,
        "last_close": closes[-1],
        "last_date": dates[-1],
        "total_pct": closes[-1]/b - 1,
        "aug_pct": aug,
        "sep_pct": sep,
        "hi": closes[hi_i], "hi_at": dates[hi_i], "hi_off": closes[-1]/closes[hi_i]-1,
        "lo": closes[lo_i], "lo_at": dates[lo_i],
        "mdd": mdd, "mdd_from": mdd_from, "mdd_to": mdd_to,
        "up_days": up_days, "n_days": len(rets),
        "std": std,
        "vol_aug": sum(vols_aug)/len(vols_aug), "vol_sep": sum(vols_sep)/len(vols_sep),
    }
    norm[name] = {"dates": dates[bi:], "vals": [round(c/b*100, 2) for c in closes[bi:]]}
    print(f"{name}: 区间{stats[name]['total_pct']*100:+.2f}%  8月{aug*100:+.2f}%  9月{sep*100:+.2f}%  "
          f"MDD{mdd*100:.2f}%({mdd_from}→{mdd_to})  高点{stats[name]['hi']:.2f}@{stats[name]['hi_at']}(现价距高点{stats[name]['hi_off']*100:+.2f}%)  "
          f"9月量/8月量={stats[name]['vol_sep']/stats[name]['vol_aug']:.2f}")

# 相对科创50超额
bm = {d: v for d, v in zip(norm["科创50"]["dates"], norm["科创50"]["vals"])}
for name in stats:
    if name == "科创50": continue
    ex = []
    for d, v in zip(norm[name]["dates"], norm[name]["vals"]):
        if d in bm:
            ex.append((v/bm[d]-1)*100)
    stats[name]["excess_vs_kc50"] = ex[-1]

# 两两日收益相关性（8月以来）
import math
names = ["彤程新材","有研新材","雅克科技","江丰电子"]
rets_map = {}
for nm in names:
    rows = series(nm)
    dates = [r["date"] for r in rows]; closes=[r["close"] for r in rows]
    bi = dates.index(BASE)
    rets_map[nm] = {dates[i]: closes[i]/closes[i-1]-1 for i in range(bi+1, len(dates))}
corr = {}
for i, a in enumerate(names):
    for b_ in names[i+1:]:
        common = sorted(set(rets_map[a]) & set(rets_map[b_]))
        xa = [rets_map[a][d] for d in common]; xb = [rets_map[b_][d] for d in common]
        ma = sum(xa)/len(xa); mb = sum(xb)/len(xb)
        cov = sum((x-ma)*(y-mb) for x,y in zip(xa,xb))
        sa = math.sqrt(sum((x-ma)**2 for x in xa)); sb = math.sqrt(sum((y-mb)**2 for y in xb))
        corr[f"{a}|{b_}"] = round(cov/(sa*sb), 3)

out = {"stats": stats, "norm": norm, "corr": corr}
with open("out/semimat_stats.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("\ncorr:", json.dumps(corr, ensure_ascii=False))
print("saved out/semimat_stats.json")
