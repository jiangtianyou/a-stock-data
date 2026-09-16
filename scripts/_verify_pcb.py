# -*- coding: utf-8 -*-
"""复核报告中的手工数字"""
import sys, os, json, statistics as stx
sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")
RAW = json.load(open(os.path.join(OUT, "pcb_raw.json"), encoding="utf-8"))
ITEMS = RAW["items"]
BY = {it["name"]: it for it in ITEMS}
PCB = [it["name"] for it in ITEMS if it["group"] in ("PCB制造", "覆铜板", "PCB设备")]
axis = [r["d"] for r in BY["中证全指"]["rows"]]
S = {n: {r["d"]: r for r in BY[n]["rows"]} for n in PCB}

# 等权指数: 6/30 = 100 -> 7/31
def eq_at(base_d, target_d):
    cur = 100.0
    active = [d for d in axis if base_d < d <= target_d]
    for d in active:
        rs = []
        for n in PCB:
            s = S[n]
            ds = [x for x in axis if x < d and x >= base_d and x in s]
            if d in s and ds:
                rs.append(s[d]["c"] / s[ds[-1]]["c"] - 1)
        if rs:
            cur *= (1 + sum(rs) / len(rs))
    return cur

jul = eq_at("2026-06-30", "2026-07-31")
print(f"等权指数 7 月（6/30->7/31）: {jul-100:+.2f}%   (6/30=100 -> {jul:.2f})")
aug = eq_at("2026-07-31", "2026-08-31")
print(f"等权指数 8 月（7/31->8/31）: {aug-100:+.2f}%")
print(f"等权指数 9 月至今（8/31->9/15）: {(156.96/141.19-1)*100:+.2f}%")

# 修正后的三段
print("\n-- 三段式 --")
for a, b, lab in [("2026-07-31", "2026-08-18", "①暴反"), ("2026-08-18", "2026-08-24", "②急跌"),
                  ("2026-08-24", "2026-09-15", "③新高")]:
    print(f"  {lab} {a} -> {b}: {eq_at(a, b)-100:+.2f}%")

# 7月个股跌幅统计 (6/30 -> 7/31)
r7 = []
for n in PCB:
    s = S[n]
    if "2026-06-30" in s and "2026-07-31" in s:
        r7.append((s["2026-07-31"]["c"] / s["2026-06-30"]["c"] - 1) * 100)
print(f"\n7月个股(6/30->7/31) 下跌只数 {sum(1 for x in r7 if x<0)}/{len(r7)}  中位数 {stx.median(r7):+.2f}%  "
      f"均值 {sum(r7)/len(r7):+.2f}%  min {min(r7):+.2f}%  max {max(r7):+.2f}%")
r7b = []
for n in PCB:
    s = S[n]
    if "2026-07-01" in s and "2026-07-31" in s:
        r7b.append((s["2026-07-31"]["c"] / s["2026-07-01"]["c"] - 1) * 100)
print(f"7月个股(7/1->7/31) 下跌只数 {sum(1 for x in r7b if x<0)}/{len(r7b)}  中位数 {stx.median(r7b):+.2f}%")

# 单日|涨跌|>=5% 次数 & 全同向日
import json as _j
stats = _j.load(open(os.path.join(OUT, "pcb_stats.json"), encoding="utf-8"))
big = [d for d in stats["daily"] if abs(d["eq_chg"]) >= 5]
allup = [d["d"] for d in stats["daily"] if d["up"] >= len(PCB)]
alldn = [d["d"] for d in stats["daily"] if d["dn"] >= len(PCB)]
print(f"\n单日|板块|>=5%: {len(big)}次 -> {[ (d['d'][5:], d['eq_chg']) for d in big]}")
print(f"全涨日({len(PCB)}/{len(PCB)}): {len(allup)}次 {[d[5:] for d in allup]}")
print(f"全跌日: {len(alldn)}次 {[d[5:] for d in alldn]}")

# 区间最大回撤(收盘)
eq = stats["eq_all"]
ds = stats["axis"]
peak, mdd, pk_d, lo_d = eq[0], 0, ds[0], ds[0]
for v, d in zip(eq, ds):
    if v > peak:
        peak, pk_d = v, d
    dd = v / peak - 1
    if dd < mdd:
        mdd, lo_d = dd, d
print(f"\n区间最大回撤(收盘口径): {mdd*100:.2f}%  ({pk_d} -> {lo_d})")

# 8/18 前五交易日
print(f"\n8月前5个交易日(8/3-8/7): {eq_at('2026-07-31','2026-08-07')-100:+.2f}%")
