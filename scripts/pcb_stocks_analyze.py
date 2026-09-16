# -*- coding: utf-8 -*-
"""PCB 代表性个股 - 指标合成与分层"""
import sys, os, json, statistics as stx
sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")

raw = json.load(open(os.path.join(OUT, "pcb_raw.json"), encoding="utf-8"))
new = json.load(open(os.path.join(OUT, "pcb_new_raw.json"), encoding="utf-8"))
snapd = json.load(open(os.path.join(OUT, "pcb_snap.json"), encoding="utf-8"))
SNAP = snapd["snap"]

ITEMS = {it["name"]: it for it in raw["items"]}
for it in new["items"]:
    ITEMS[it["name"]] = it
for it in raw["items"]:
    if it["group"] == "基准":
        ITEMS.pop(it["name"], None)

# 交易日轴: 用中证全指
axis = [r["d"] for r in json.load(open(os.path.join(OUT, "pcb_raw.json"), encoding="utf-8"))["items"][0]["rows"]]
AX = None
for it in raw["items"]:
    if it["name"] == "中证全指":
        AX = [r["d"] for r in it["rows"]]
axis = AX

BASE_D, NEW_D, END_D = "2026-07-31", "2026-09-01", "2026-09-15"

rows = []
for name, it in ITEMS.items():
    s = {r["d"]: r for r in it["rows"]}
    ds = [d for d in axis if d in s]
    if BASE_D not in s:
        # 新股(嘉立创): 以首个交易日为基准
        b0 = ds[0]
    else:
        b0 = BASE_D
    c0 = s[b0]["c"]
    last = s[ds[-1]]["c"]
    r_win = (last / c0 - 1) * 100
    # 7月
    j0 = "2026-07-01" if "2026-07-01" in s else b0
    r_jul = (s[BASE_D]["c"] / s[j0]["c"] - 1) * 100 if (BASE_D in s and j0 != BASE_D) else None
    # 8月
    r_aug = (s["2026-08-31"]["c"] / s[BASE_D]["c"] - 1) * 100 if ("2026-08-31" in s and BASE_D in s) else None
    # 9月
    r_sep = (s[ds[-1]]["c"] / s["2026-08-31"]["c"] - 1) * 100 if ("2026-08-31" in s) else None
    # 高点
    seg = [(d, s[d]["h"]) for d in ds if d >= b0]
    hi_d, hi = max(seg, key=lambda x: x[1])
    # 最大回撤
    peak, mdd, pk = s[ds[0]]["c"], 0.0, ds[0]
    for d in ds:
        if d < b0:
            continue
        peak = max(peak, s[d]["c"])
        dd = s[d]["c"] / peak - 1
        mdd = min(mdd, dd)
    # 量能: 7月/8月/9月 日均成交额
    def amt(d):
        return s[d]["v"] * (s[d]["h"] + s[d]["l"] + s[d]["c"]) / 3 / 1e8
    a7 = [amt(d) for d in ds if d.startswith("2026-07")]
    a8 = [amt(d) for d in ds if d.startswith("2026-08")]
    a9 = [amt(d) for d in ds if d.startswith("2026-09")]
    # 换手放大倍数(9月/8月)
    vr = (sum(a9) / len(a9)) / (sum(a8) / len(a8)) if a8 and a9 else None

    code = it["secid"][2:]
    sn = SNAP.get(code, {})
    rows.append({
        "name": name, "code": code, "secid": it["secid"], "group": it["group"],
        "ret": r_win, "ret_jul": r_jul, "ret_aug": r_aug, "ret_sep": r_sep,
        "hi_d": hi_d, "hi_ret": (hi / c0 - 1) * 100 if c0 else None,
        "from_hi": (last / hi - 1) * 100,
        "mdd": mdd * 100,
        "amt8": sum(a8) / len(a8) if a8 else None,
        "amt9": sum(a9) / len(a9) if a9 else None,
        "vr": vr,
        "mv": float(sn["total_mv"]) if sn.get("total_mv") else None,
        "pe": float(sn["pe"]) if sn.get("pe") else None,
        "pb": float(sn["pb"]) if sn.get("pb") else None,
        "turnover": float(sn["turnover"]) if sn.get("turnover") else None,
        "price": float(sn["price"]) if sn.get("price") else None,
        "chg_today": float(sn["chg_pct"]) if sn.get("chg_pct") else None,
        "new_stock": b0 != BASE_D,
    })

rows.sort(key=lambda x: -(x["ret"] or 0))

# 分层
def tier(r):
    mv = r["mv"] or 0
    if mv >= 800:
        return "① 大市值(≥800亿)"
    if mv >= 300:
        return "② 中大市值(300-800亿)"
    if mv >= 100:
        return "③ 中市值(100-300亿)"
    return "④ 小市值(<100亿)"


for r in rows:
    r["tier"] = tier(r)

def fm(v, w=8, d=1):
    return f"{'—':>{w}}" if v is None else f"{v:>{w}.{d}f}"


print(f"样本 {len(rows)} 只\n")
print(f"{'名称':<10}{'代码':<8}{'分层':<20}{'8月以来':>9}{'7月':>9}{'9月':>9}{'距高':>8}{'市值亿':>10}{'PE':>9}{'PB':>7}{'换手%':>8}{'9月/8月量':>9}")
for r in rows:
    print(f"{r['name']:<10}{r['code']:<8}{r['tier']:<20}"
          f"{fm(r['ret'], 8)}{fm(r['ret_jul'], 8)}{fm(r['ret_sep'], 8)}"
          f"{fm(r['from_hi'], 7)}{fm(r['mv'], 9, 0)}"
          f"{fm(r['pe'], 9)}{fm(r['pb'], 7, 2)}"
          f"{fm(r['turnover'], 7, 2)}{fm(r['vr'], 8, 2)}")

# 相关性: 7月 vs 8月以来
a = [r for r in rows if r["ret_jul"] is not None and not r["new_stock"]]
xs = [r["ret_jul"] for r in a]
ys = [r["ret"] for r in a]
n = len(xs)
mx, my = sum(xs) / n, sum(ys) / n
cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
sx = sum((x - mx) ** 2 for x in xs) ** .5
sy = sum((y - my) ** 2 for y in ys) ** .5
rr = cov / (sx * sy)
slope = cov / (sx ** 2)
print(f"\n相关性(7月跌幅 vs 8月以来涨幅): r={rr:.3f}  n={n}  斜率={slope:.3f}")

# 分组均值
print("\n按分层:")
by = {}
for r in rows:
    by.setdefault(r["tier"], []).append(r)
for t in sorted(by):
    g = by[t]
    print(f"  {t:<20} n={len(g):>2}  中位涨幅 {stx.median([x['ret'] for x in g]):>7.1f}%  "
          f"中位回撤 {stx.median([x['mdd'] for x in g]):>7.1f}%  中位换手 {stx.median([x['turnover'] or 0 for x in g]):>5.2f}%")

print("\n按板块:")
by2 = {}
for r in rows:
    by2.setdefault(r["group"], []).append(r)
for t in sorted(by2):
    g = by2[t]
    print(f"  {t:<8} n={len(g):>2}  中位涨幅 {stx.median([x['ret'] for x in g]):>7.1f}%  "
          f"中位市值 {stx.median([x['mv'] or 0 for x in g]):>7.0f}亿")

json.dump({"stocks": rows, "corr": {"r": rr, "slope": slope, "n": n},
           "fetched_at": snapd["fetched_at"]},
          open(os.path.join(OUT, "pcb_stocks_stats.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("\n[saved] out/pcb_stocks_stats.json")
