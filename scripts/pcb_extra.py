# -*- coding: utf-8 -*-
"""PCB 板块补充统计: 量能/相关性/分段"""
import sys, os, json, math
sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")
RAW = json.load(open(os.path.join(OUT, "pcb_raw.json"), encoding="utf-8"))
ITEMS = RAW["items"]
BY = {it["name"]: it for it in ITEMS}
PCB = [it["name"] for it in ITEMS if it["group"] in ("PCB制造", "覆铜板", "PCB设备")]
axis = [r["d"] for r in BY["中证全指"]["rows"]]
S = {n: {r["d"]: r for r in BY[n]["rows"]} for n in PCB}


def seg_ret(n, d0, d1):
    s = S[n]
    if d0 not in s or d1 not in s:
        return None
    return (s[d1]["c"] / s[d0]["c"] - 1) * 100


def corr(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    vx = math.sqrt(sum((a - mx) ** 2 for a in xs))
    vy = math.sqrt(sum((b - my) ** 2 for b in ys))
    return cov / (vx * vy) if vx and vy else float("nan")


# ---- 1. 量能: 成交量(万手)与成交额 ----
def vol_stat(mon):
    ds = [d for d in axis if d.startswith(mon)]
    v = sum(sum(S[n][d]["v"] for n in PCB if d in S[n]) for d in ds) / max(len(ds), 1)
    a = sum(sum(S[n][d]["v"] * (S[n][d]["h"] + S[n][d]["l"] + S[n][d]["c"]) / 3 for n in PCB if d in S[n])
            for d in ds) / max(len(ds), 1) / 1e8
    return round(v / 1e4, 1), round(a, 1)


print("== 日均量能 ==")
for m in ("2026-06", "2026-07", "2026-08", "2026-09"):
    v, a = vol_stat(m)
    print(f"  {m}: 成交量 {v:>8.1f}万手   成交额 {a:>7.1f}亿")

# ---- 2. 分段涨幅 ----
SEGS = [("7月", "2026-06-30", "2026-07-31"),
        ("8/3-8/7 暴反", "2026-07-31", "2026-08-07"),
        ("8/10-8/13 回调", "2026-08-07", "2026-08-13"),
        ("8/14-8/18 二次上攻", "2026-08-13", "2026-08-18"),
        ("8/19-8/24 急跌", "2026-08-18", "2026-08-24"),
        ("8/25-8/31 修复", "2026-08-24", "2026-08-31"),
        ("9/1-9/4 再回调", "2026-08-31", "2026-09-04"),
        ("9/7-9/15 新高", "2026-09-04", "2026-09-15")]

print("\n== 各标的分段涨幅 ==")
hdr = "  " + f"{'标的':<8}" + "".join(f"{s[0]:>16}" for s in SEGS)
print(hdr)
recs = []
for n in PCB:
    r7 = seg_ret(n, "2026-06-30", "2026-07-31")
    r8 = seg_ret(n, "2026-07-31", "2026-09-15")
    recs.append({"n": n, "r7": r7, "r8": r8,
                 "segs": [seg_ret(n, a, b) for _, a, b in SEGS]})
for r in sorted(recs, key=lambda x: -(x["r8"] or -999)):
    line = f"  {r['n']:<8}" + "".join(
        f"{(v if v is not None else 0):>15.1f}%" for v in r["segs"])
    print(line)

xs = [r["r7"] for r in recs if r["r7"] is not None and r["r8"] is not None]
ys = [r["r8"] for r in recs if r["r7"] is not None and r["r8"] is not None]
print(f"\n== 相关性: 7月涨跌幅 vs 8月以来涨跌幅  r = {corr(xs, ys):.3f}  (n={len(xs)}) ==")

# 拟合线 (y = a + b x)
mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
b = sum((a - mx) * (c - my) for a, c in zip(xs, ys)) / sum((a - mx) ** 2 for a in xs)
a0 = my - b * mx
print(f"   回归: 8月涨幅 = {a0:.1f} + {b:.3f} x 7月涨幅   -> 7月每多跌1%, 8月多涨{abs(b):.2f}%")

# ---- 3. 波动率 ----
eq = None
RETS = {}
for n in PCB:
    prev, rr = None, []
    for d in axis:
        if d in S[n]:
            if prev is not None:
                rr.append(S[n][d]["c"] / prev - 1)
            prev = S[n][d]["c"]
    RETS[n] = rr
# 等权日收益
lens = min(len(v) for v in RETS.values())
eqr = [sum(RETS[n][-lens + i] for n in PCB) / len(PCB) for i in range(lens)]
def vol_of(rs):
    m = sum(rs) / len(rs)
    return math.sqrt(sum((r - m) ** 2 for r in rs) / (len(rs) - 1)) * math.sqrt(252) * 100
print(f"\n== 板块等权日波动率(年化) ==")
print(f"   近{lens}日全样本: {vol_of(eqr):.1f}%")
aug = eqr[-lens + [i for i, d in enumerate(axis) if d >= '2026-08-03'][0]:]
print(f"   8月以来: {vol_of(aug):.1f}%")

json.dump({"vol": {m: vol_stat(m) for m in ("2026-06", "2026-07", "2026-08", "2026-09")},
           "segs": [s[0] for s in SEGS],
           "stocks": recs,
           "corr_r7_r8": round(corr(xs, ys), 3),
           "reg": [round(a0, 2), round(b, 3)],
           "vol_ann": {"all": round(vol_of(eqr), 1), "aug": round(vol_of(aug), 1)}},
          open(os.path.join(OUT, "pcb_extra.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("\n[saved] out/pcb_extra.json")
