# -*- coding: utf-8 -*-
"""
PCB 板块 8 月以来走势复盘 - 分析
输入: out/pcb_raw.json
输出: out/pcb_stats.json  + 控制台摘要
"""
import sys, os, json, math

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")

with open(os.path.join(OUT, "pcb_raw.json"), encoding="utf-8") as f:
    RAW = json.load(f)

ITEMS = RAW["items"]
BY = {it["name"]: it for it in ITEMS}
GROUP = {it["name"]: it["group"] for it in ITEMS}

BENCH = ["上证指数", "沪深300", "创业板指", "中证全指", "中证全指信息技术", "中证全指通信", "中证半导体"]
PCB_ALL = [it["name"] for it in ITEMS if it["group"] in ("PCB制造", "覆铜板", "PCB设备")]
PCB_CORE = [it["name"] for it in ITEMS if it["group"] == "PCB制造"]

# ---- 交易日轴: 以中证全指为准 ----
axis = [r["d"] for r in BY["中证全指"]["rows"]]
idx = {d: i for i, d in enumerate(axis)}


def series(name):
    """返回 dict{date: row}"""
    return {r["d"]: r for r in BY[name]["rows"] if r["d"] in idx}


SR = {n: series(n) for n in PCB_ALL + BENCH}

# 过滤: 8/1 之前必须有数据(停牌/新股剔除)
first_ok = set()
for n in PCB_ALL:
    if axis[0] in SR[n] or any(d <= "2026-08-01" for d in SR[n]):
        first_ok.add(n)
PCB_ALL = [n for n in PCB_ALL if n in first_ok]
PCB_CORE = [n for n in PCB_CORE if n in first_ok]

BASE_D = "2026-07-31"          # 基期
START_D = "2026-08-03"         # 8月首个交易日


def ret_series(name):
    """日收益率 dict{date: ret}"""
    s = SR[name]
    out, prev = {}, None
    for d in axis:
        r = s.get(d)
        if r is None:
            continue
        if prev is not None:
            out[d] = r["c"] / prev - 1.0
        prev = r["c"]
    return out


RET = {n: ret_series(n) for n in PCB_ALL + BENCH}


def eq_index(names, base_d=BASE_D):
    """等权指数, 基期日收盘=100, 基期当日收益不计入"""
    vals, cur = {}, 100.0
    for d in axis:
        if d < base_d:
            continue
        if d == base_d:
            vals[d] = 100.0
            continue
        rs = [RET[n][d] for n in names if d in RET[n]]
        if not rs:
            vals[d] = cur
            continue
        cur *= (1 + sum(rs) / len(rs))
        vals[d] = cur
    return vals


def amt_at(name, d):
    r = SR[name].get(d)
    if not r:
        return 0.0
    return r["v"] * (r["h"] + r["l"] + r["c"]) / 3.0 / 1e8   # 亿元(估算)


def pct(a, b):
    return (b / a - 1) * 100


# ===== 1. 板块指数 =====
EQ = eq_index(PCB_ALL)
EQ_CORE = eq_index(PCB_CORE)
BENCH_SER = {b: {d: 100.0 for d in [BASE_D]} for b in BENCH}
for b in BENCH:
    s = SR[b]
    bd = s[BASE_D]["c"]
    BENCH_SER[b] = {d: s[d]["c"] / bd * 100 for d in axis if d >= BASE_D and d in s}

# ===== 2. 区间统计 =====
DATES = [d for d in axis if d >= BASE_D]
SCAN = [d for d in axis if d >= START_D]


def stat_block(names):
    s = SR[names[0]]
    return s


rows_pcb = []
for n in PCB_ALL:
    s = SR[n]
    if BASE_D not in s or axis[-1] not in s:
        continue
    r0 = s[BASE_D]["c"]
    hi_d = max((d for d in axis if d >= BASE_D), key=lambda d: s[d]["h"] if d in s else -1)
    lo_d = min((d for d in axis if d >= BASE_D), key=lambda d: s[d]["l"] if d in s else 9e9)
    hi = s[hi_d]["h"]
    lo = s[lo_d]["l"]
    rows_pcb.append({
        "name": n, "group": GROUP[n],
        "ret": pct(r0, s[axis[-1]]["c"]),
        "hi_d": hi_d, "hi_ret": pct(r0, hi),
        "cur_from_hi": pct(hi, s[axis[-1]]["c"]),
        "lo_d": lo_d, "lo_ret": pct(r0, lo),
        "ret_jul": pct(s["2026-07-01"]["c"], r0) if "2026-07-01" in s else None,
    })
rows_pcb.sort(key=lambda x: -x["ret"])

bench_ret = {}
for b in BENCH:
    s = SR[b]
    bench_ret[b] = pct(s[BASE_D]["c"], s[axis[-1]]["c"])

# 等权指数走势关键点
eq_hi_d = max(SCAN, key=lambda d: EQ[d])
eq_hi = EQ[eq_hi_d]
eq_last = EQ[axis[-1]]

# ===== 3. 量能 =====
amt_all = []
for d in DATES:
    tot = sum(amt_at(n, d) for n in PCB_ALL)
    amt_all.append({"d": d, "amt": tot})

# 均量对比: 7月 vs 8月 vs 9月
def avg_amt(mon):
    ds = [d for d in axis if d.startswith(mon)]
    vs = [sum(amt_at(n, d) for n in PCB_ALL) for d in ds]
    return sum(vs) / len(vs) if vs else 0


# ===== 4. 涨跌家数 =====
breadth = []
for d in DATES:
    up = sum(1 for n in PCB_ALL if d in RET[n] and RET[n][d] > 0.0001)
    dn = sum(1 for n in PCB_ALL if d in RET[n] and RET[n][d] < -0.0001)
    breadth.append({"d": d, "up": up, "dn": dn, "n": len(PCB_ALL)})

# ===== 5. 逐日明细 =====
daily = []
prev_eq = 100.0
for d in DATES:
    rs = sorted(((n, RET[n][d]) for n in PCB_ALL if d in RET[n]), key=lambda x: -x[1])
    if not rs:
        continue
    cur_eq = EQ.get(d, prev_eq)
    daily.append({
        "d": d,
        "eq": round(cur_eq, 2),
        "eq_chg": round((cur_eq / prev_eq - 1) * 100, 2),
        "hs300_chg": round(RET["沪深300"][d] * 100, 2) if d in RET["沪深300"] else None,
        "amt": round(sum(amt_at(n, d) for n in PCB_ALL), 1),
        "up": sum(1 for n in PCB_ALL if d in RET[n] and RET[n][d] > 0.0001),
        "dn": sum(1 for n in PCB_ALL if d in RET[n] and RET[n][d] < -0.0001),
        "best": [rs[0][0], round(rs[0][1] * 100, 2)],
        "worst": [rs[-1][0], round(rs[-1][1] * 100, 2)],
    })
    prev_eq = cur_eq

out = {
    "meta": {"base": BASE_D, "last": axis[-1], "n_pcb": len(PCB_ALL), "n_core": len(PCB_CORE),
             "source": RAW["source"], "fetched_at": RAW["fetched_at"]},
    "axis": DATES,
    "eq_all": [round(EQ[d], 2) for d in DATES],
    "eq_core": [round(EQ_CORE[d], 2) if d in EQ_CORE else None for d in DATES],
    "bench": {b: [round(BENCH_SER[b].get(d), 2) if d in BENCH_SER[b] else None for d in DATES] for b in BENCH},
    "amt": [{"d": a["d"], "amt": round(a["amt"], 1)} for a in amt_all],
    "breadth": breadth,
    "daily": daily,
    "stocks": rows_pcb,
    "bench_ret": bench_ret,
    "avg_amt": {"2026-07": round(avg_amt("2026-07"), 1), "2026-08": round(avg_amt("2026-08"), 1),
                "2026-09": round(avg_amt("2026-09"), 1)},
    "eq_hi": {"d": eq_hi_d, "v": round(eq_hi, 2), "from_hi": round(pct(eq_hi, eq_last), 2)},
}
with open(os.path.join(OUT, "pcb_stats.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False)

# ===== 打印摘要 =====
print(f"样本: {len(PCB_ALL)} 只(PCB制造{len(PCB_CORE)})  基期 {BASE_D} -> {axis[-1]}")
print(f"\n等权板块指数: 100 -> {EQ[axis[-1]]:.2f}  ({EQ[axis[-1]]-100:+.2f}%)")
print(f"  区间最高 {eq_hi:.2f} @ {eq_hi_d}, 距高点 {out['eq_hi']['from_hi']:+.2f}%")
print("\n基准同期:")
for b in BENCH:
    print(f"  {b:<12} {bench_ret[b]:>7.2f}%")
print(f"\n日均成交额(估算,亿元): 7月 {out['avg_amt']['2026-07']} | 8月 {out['avg_amt']['2026-08']} | 9月 {out['avg_amt']['2026-09']}")
print("\n逐日:")
for r in daily:
    print(f"  {r['d']}  指数{r['eq']:>7.2f}  {r['eq_chg'] if r['eq_chg'] is not None else 0:>6.2f}%  "
          f"HS300 {r['hs300_chg'] if r['hs300_chg'] is not None else 0:>6.2f}%  额{r['amt']:>7.1f}亿  "
          f"涨{r['up']:>2}/跌{r['dn']:>2}  最强{r['best'][0]}({r['best'][1]:+.1f}%) 最弱{r['worst'][0]}({r['worst'][1]:+.1f}%)")
print("\n个股区间涨幅 (7/31 -> 9/15):")
for r in rows_pcb:
    print(f"  {r['name']:<8}{r['group']:<6} {r['ret']:>7.2f}%  最高{r['hi_d']}({r['hi_ret']:+.1f}%)  距高{r['cur_from_hi']:+.2f}%  7月{r['ret_jul'] if r['ret_jul'] is None else round(r['ret_jul'],2)}%")
print("\n[saved] out/pcb_stats.json")
