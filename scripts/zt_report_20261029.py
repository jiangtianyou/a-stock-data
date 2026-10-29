# -*- coding: utf-8 -*-
"""涨停复盘报告 20261029 vs 20261028（算力硬件链板块级崩塌 · 缩量杀跌 + 跌停潮 + 封板率分母型假改善）
用法：python scripts/zt_report_20261029.py 20261029
输入：out/zt_stats_20261029.json、out/zt_review_20261029.json、out/zt_review_20261028.json、out/zt_stats_20261028.json
     跌停明细 out/_dt1029.json / out/_dt1028.json；昨跌停股今日行情 out/_qdt1028.json；watchlist 概念/行业榜 out/_sw1029.json
输出：reports/涨停复盘对比-20261029.html
"""
import json, os, sys, html, re, urllib.request, time, subprocess
from statistics import mean, median

ROOT = os.environ.get("ZT_ROOT") or os.getcwd()
OUT = os.path.join(ROOT, "out")
REP = os.path.join(ROOT, "reports")
TPL = os.path.join(ROOT, "scripts", "_report_tpl_20261029.html")
os.makedirs(REP, exist_ok=True)

D0 = sys.argv[1] if len(sys.argv) > 1 else "20261029"
S = json.load(open(os.path.join(OUT, f"zt_stats_{D0}.json"), encoding="utf-8"))
D0, D1, D2 = S["D0"], S["D1"], S["D2"]
B = json.load(open(os.path.join(OUT, f"zt_review_{D0}.json"), encoding="utf-8"))
B1 = json.load(open(os.path.join(OUT, f"zt_review_{D1}.json"), encoding="utf-8"))
S1 = json.load(open(os.path.join(OUT, f"zt_stats_{D1}.json"), encoding="utf-8"))
perf = S["perf"]
s0, s1 = S["senti"][D0], S["senti"][D1]
A0, A1 = B["dates"][D0], B["dates"][D1]


def md(ds):
    return f"{int(ds[4:6])}/{int(ds[6:8])}"


def esc(s):
    return html.escape(str(s))


def hhmm(v):
    s = str(int(v)).zfill(6)
    return s[:2] + ":" + s[2:4]


def f1(v):
    return f"{v:+.1f}"


def f2(v):
    return f"{v:+.2f}"


V = {}
V["D0"], V["D1"], V["D2"] = md(D0), md(D1), md(D2)
V["NEXT_D"] = "10/30 周五"


def pool(zn, key):
    return (zn.get(key) or {}).get("pool") or []


ths0 = {x["code"]: x for x in A0["ths_zt"]["info"]}
ths1 = {x["code"]: x for x in A1["ths_zt"]["info"]}
zt_all = pool(A0, "em_ZT")
zt0 = [x for x in zt_all if not x["c"].startswith("92") and x["c"] in ths0]
zt0_em = [x for x in zt_all if not x["c"].startswith("92")]
zt1 = [x for x in pool(A1, "em_ZT") if not x["c"].startswith("92") and x["c"] in ths1]
zb0 = pool(A0, "em_ZB")


def load_dt(d):
    p = os.path.join(OUT, f"_dt{d[4:]}.json")
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8")).get("data", {}).get("pool") or []
    return []


dt0, dt1 = load_dt(D0), load_dt(D1)

# ================= 情绪 =================
ZT, ZT_Y = s0["zt"], s1["zt"]
TOUCH = A0["ths_zt"]["total"]["today"]["history_num"]
TOUCH_Y = A1["ths_zt"]["total"]["today"]["history_num"]
ZB, ZB_Y = s0["zb"], s1["zb"]
SEAL, SEAL_Y = s0["seal_rate"] * 100, s1["seal_rate"] * 100
_dc0 = A0["ths_zt"]["limit_down_count"]["today"]
_dc1 = A1["ths_zt"]["limit_down_count"]["today"]
_dcy0 = A1["ths_zt"]["limit_down_count"]["yesterday"]
DT, DT_Y = _dc0["num"], _dc1["num"]
DTOUCH, DTOUCH_Y = _dc0["history_num"], _dc1["history_num"]
DSEAL, DSEAL_Y = _dc0["rate"] * 100, _dc1["rate"] * 100
DT_OPEN_N = DTOUCH - DT
DT_OPEN_Y = DTOUCH_Y - DT_Y

V.update({
    "ZT": ZT, "ZT_Y": ZT_Y, "ZT_D": f"{ZT - ZT_Y:+d}", "ZT_PCT_D": f"{abs((ZT / ZT_Y - 1) * 100):.0f}",
    "TOUCH": TOUCH, "TOUCH_Y": TOUCH_Y, "TOUCH_D": f"{TOUCH - TOUCH_Y:+d}",
    "TOUCH_PCT": f"{abs((TOUCH / TOUCH_Y - 1) * 100):.0f}",
    "TOUCH_GAP": TOUCH - ZT,
    "SEAL": f"{SEAL:.1f}", "SEAL_Y": f"{SEAL_Y:.1f}", "SEAL_D": f"{SEAL - SEAL_Y:+.1f}",
    "SEAL_D_ABS": f"{abs(SEAL - SEAL_Y):.1f}",
    "SEAL_FAIL": f"{(1 - ZT / TOUCH) * 100:.1f}", "SEAL_FAIL_Y": f"{(1 - ZT_Y / TOUCH_Y) * 100:.1f}",
    "DT": DT, "DT_Y": DT_Y, "DT_D": f"{DT - DT_Y:+d}", "DT_X": f"{DT / DT_Y:.1f}",
    "DTOUCH": DTOUCH, "DTOUCH_Y": DTOUCH_Y,
    "DSEAL": f"{DSEAL:.1f}", "DSEAL_Y": f"{DSEAL_Y:.1f}",
    "DT_OPEN_N": DT_OPEN_N, "DT_OPEN_Y": DT_OPEN_Y,
    "DT_REBUY": f"{DT_OPEN_N / DTOUCH * 100:.1f}",
    "ZB": ZB, "ZB_Y": ZB_Y, "ZB_D": f"{ZB - ZB_Y:+d}",
})

# 三日阶梯（D2 列取 D1 文件自带的 yesterday）
days = [
    {"d": md(D2), "zt": s1["zt_prev"], "zb": s1["zb_prev"], "dt": s1["dt_prev"],
     "touch": s1["yest"].get("history_num", 0),
     "dtouch": _dcy0["history_num"]},
    {"d": md(D1), "zt": s1["zt"], "zb": s1["zb"], "dt": s1["dt"],
     "touch": TOUCH_Y, "dtouch": DTOUCH_Y},
    {"d": md(D0), "zt": s0["zt"], "zb": s0["zb"], "dt": s0["dt"],
     "touch": TOUCH, "dtouch": DTOUCH},
]
for x in days:
    x["seal"] = x["zt"] / x["touch"] * 100 if x["touch"] else 0.0
assert days[0]["dtouch"] != days[1]["dtouch"], "D2 列触及跌停与 D1 相同，取错文件"
assert days[0]["zt"] != days[1]["zt"], "D2 列涨停与 D1 相同，取错文件"
assert days[0]["dt"] != days[1]["dt"], "D2 列跌停与 D1 相同，取错文件"

V["ZTDT"] = f"{ZT / DT:.2f}"
V["ZTDT_Y"] = f"{ZT_Y / DT_Y:.2f}"
V["ZTDT_0"] = f"{days[0]['zt'] / days[0]['dt']:.2f}" if days[0]["dt"] else "—"
V["SEAL_0"] = f"{days[0]['seal']:.1f}"

_tbl = []
for nm, k in [("涨停家数", "zt"), ("炸板家数", "zb"), ("封板率", "seal"), ("触及涨停家数", "touch"),
              ("跌停家数", "dt"), ("触及跌停家数", "dtouch")]:
    vs = [x[k] for x in days]
    inv = k in ("zb", "dt", "dtouch")
    if k == "seal":
        cells = [f"{v:.1f}%" for v in vs]
        d = vs[2] - vs[1]
        cls = "up" if (d > 0) != inv else "down"
        chg = f'<span class="{cls}">{d:+.1f}pct</span>'
    else:
        cells = [f"{int(v)}" for v in vs]
        d = vs[2] - vs[1]
        cls = "up" if (d > 0) != inv else "down"
        chg = f'<span class="{cls}">{d:+d}</span>'
    _tbl.append("<tr><td>%s</td><td>%s</td><td>%s</td><td class='hl'>%s</td><td>%s</td></tr>" % (nm, cells[0], cells[1], cells[2], chg))
V["TBL_SENTI"] = "\n".join(_tbl)

# ================= 指数 =================
IX_ORDER = ["上证指数", "深证成指", "创业板指", "科创50", "沪深300", "中证500",
            "中证1000", "国证2000", "上证50", "中小100", "北证50"]
i0 = {v["name"]: v for v in B["indexes"].values() if isinstance(v, dict) and v.get("name")}
i1 = {v["name"]: v for v in B1["indexes"].values() if isinstance(v, dict) and v.get("name")}
TOT, TOT_Y = S["tot"]["today"], S["tot"]["prev"]
V["AMT"], V["AMT_Y"] = f"{TOT:.0f}", f"{TOT_Y:.0f}"
V["AMT_D"] = f"{TOT - TOT_Y:+.0f}"
AMT_PCT = (TOT / TOT_Y - 1) * 100
V["AMT_PCT"] = f1(AMT_PCT)
V["AMT_PCT_ABS"] = f"{abs(AMT_PCT):.1f}"

ix = []
for nm in IX_ORDER:
    v, p = i0.get(nm) or {}, i1.get(nm) or {}
    a0 = (v.get("amount_wan") or 0) / 10000.0
    a1v = (p.get("amount_wan") or 0) / 10000.0
    ix.append({"name": nm, "pct": v.get("pct") or 0.0, "amt": a0, "prev_pct": p.get("pct"),
               "yoy": ((a0 / a1v - 1) * 100) if a1v else None})
V["AMT_UP_N"] = sum(1 for x in ix if (x["yoy"] or 0) < 0)   # 本日口径：缩量数
V["AMT_DN_N"] = sum(1 for x in ix if (x["yoy"] or 0) > 0)   # 本日口径：放量数
V["N_UP"] = sum(1 for x in ix if x["pct"] > 0)
V["N_DN"] = sum(1 for x in ix if x["pct"] < 0)
_yoyv = [x["yoy"] for x in ix if x["yoy"] is not None]
V["YOY_MIN"] = f"{min(_yoyv):.1f}"
V["YOY_MAX"] = f"{max(_yoyv):.1f}"
V["YOY_RANGE"] = f"{max(_yoyv) - min(_yoyv):.1f}"

# 日内 OHLC
OHLC = {}
try:
    _op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for nm, sym in [("上证指数", "sh000001"), ("深证成指", "sz399001"), ("创业板指", "sz399006"),
                    ("科创50", "sh000688"), ("国证2000", "sz399303"), ("上证50", "sh000016")]:
        u = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=" + sym + ",day,,,12,qfq"
        d = json.loads(_op.open(u, timeout=20).read().decode("utf-8"))["data"][sym]
        rows = d.get("day") or d.get("qfqday")
        cur = [r for r in rows if r[0].replace("-", "") == D0][0]
        pre = [r for r in rows if r[0].replace("-", "") < D0][-1]
        OHLC[nm] = {"open": float(cur[1]), "close": float(cur[2]), "high": float(cur[3]),
                    "low": float(cur[4]), "prev": float(pre[2])}
except Exception as e:
    print("warn: 日线抓取失败", e)

INTRA = []
for nm in ["上证指数", "深证成指", "创业板指", "科创50", "国证2000", "上证50"]:
    o = OHLC.get(nm)
    if not o:
        continue
    INTRA.append({"nm": nm, "gap": (o["open"] / o["prev"] - 1) * 100,
                  "low": (o["low"] / o["prev"] - 1) * 100, "close": (o["close"] / o["prev"] - 1) * 100,
                  "reb": (o["close"] / o["low"] - 1) * 100, "draw": (o["close"] / o["high"] - 1) * 100})
V["N_BELOW_OPEN"] = sum(1 for x in INTRA if x["close"] < x["gap"])
V["N_ABOVE_OPEN"] = len(INTRA) - V["N_BELOW_OPEN"]
V["N_INTRA"] = len(INTRA)
V["N_REBOUND"] = sum(1 for x in INTRA if x["reb"] > 0)

for key, nm in [("SH", "上证指数"), ("CY", "创业板指"), ("KC", "科创50"),
                ("GZ", "国证2000"), ("SH50", "上证50")]:
    x = next((y for y in INTRA if y["nm"] == nm), None)
    if x:
        V[key + "_GAP"] = f2(x["gap"])
        V[key + "_LOW"] = f2(x["low"])
        V[key + "_PCT"] = f2(x["close"])
        V[key + "_REB"] = f"{x['reb']:.2f}"
        V[key + "_DRAW"] = f"{x['draw']:.2f}"
# 成交额环比（分指数）
for key, nm in [("CY", "创业板指"), ("KC", "科创50"), ("SH50", "上证50"), ("HS300", "沪深300"),
                ("ZX100", "中小100"), ("BJ", "北证50")]:
    r = next((y for y in ix if y["name"] == nm), None)
    if r:
        V[key + "_YOY"] = f1(r["yoy"] or 0)
        V[key + "_YOY_ABS"] = f"{abs(r['yoy'] or 0):.1f}"
        V[key + "_AMT"] = f"{r['amt']:.0f}"
V["CY_PCT_Y"] = f"{(i1.get('创业板指') or {}).get('pct') or 0:+.2f}"
V["SH50_PCT_Y"] = f"{(i1.get('上证50') or {}).get('pct') or 0:+.2f}"
V["SH_PCT_Y"] = f"{(i1.get('上证指数') or {}).get('pct') or 0:+.2f}"
V["GZ_PCT_Y"] = f"{(i1.get('国证2000') or {}).get('pct') or 0:+.2f}"

_t = []
for x in ix:
    yoy = "—" if x["yoy"] is None else f'<span class="{"up" if x["yoy"] > 0 else "down"}">{x["yoy"]:+.1f}%</span>'
    pp = "—" if x["prev_pct"] is None else f"{x['prev_pct']:+.2f}%"
    _t.append("<tr><td>%s</td><td class='%s'>%s</td><td class='mut'>%s</td><td>%.0f</td><td>%s</td></tr>" % (
        x["name"], "up" if x["pct"] > 0 else "down", f"{x['pct']:+.2f}%", pp, x["amt"], yoy))
V["TBL_IDX"] = "\n".join(_t)

# ================= 梯队 =================
lad0, lad1 = {}, {}
for x in zt0:
    lad0[x["lbc"]] = lad0.get(x["lbc"], 0) + 1
for x in zt1:
    lad1[x["lbc"]] = lad1.get(x["lbc"], 0) + 1
MAXB, MAXB_Y = max(lad0), max(lad1)
LB, LB_Y = sum(v for k, v in lad0.items() if k >= 2), sum(v for k, v in lad1.items() if k >= 2)
SHOU, SHOU_Y = lad0.get(1, 0), lad1.get(1, 0)
V.update({"MAXB": MAXB, "MAXB_Y": MAXB_Y, "LB": LB, "LB_Y": LB_Y, "SHOU": SHOU, "SHOU_Y": SHOU_Y,
          "SHOU_PCT": f"{SHOU / ZT * 100:.1f}", "SHOU_PCT_Y": f"{SHOU_Y / ZT_Y * 100:.1f}",
          "LAD2": lad0.get(2, 0), "LAD3": lad0.get(3, 0), "LAD4": lad0.get(4, 0), "LAD5": lad0.get(5, 0),
          "LAD2_Y": lad1.get(2, 0), "LAD3_Y": lad1.get(3, 0), "LAD4_Y": lad1.get(4, 0), "LAD5_Y": lad1.get(5, 0)})
_maxb = [x for x in zt0 if x["lbc"] == MAXB]
V["MAXB_NAMES"] = "、".join(x["n"] for x in _maxb)
_mb = _maxb[0]
V.update({"MAXB_NAME": _mb["n"], "MAXB_HY": _mb["hybk"], "MAXB_FUND": f"{_mb['fund'] / 1e8:.2f}",
          "MAXB_AMT": f"{_mb['amount'] / 1e8:.2f}", "MAXB_TURN": f"{_mb['hs']:.1f}",
          "MAXB_FBT": hhmm(_mb["fbt"]),
          "MAXB_RT": (ths0.get(_mb["c"]) or {}).get("reason_type") or ""})
V["LB_HY_N"] = len({x["hybk"] for x in zt0 if x["lbc"] >= 2})
V["LB_NAMES"] = "、".join(f"{x['n']}({x['lbc']}板)" for x in sorted([x for x in zt0 if x["lbc"] >= 2], key=lambda z: -z["lbc"]))

_t = []
for k in sorted(set(list(lad0.keys()) + list(lad1.keys()))):
    a, b = lad0.get(k, 0), lad1.get(k, 0)
    d = a - b
    _t.append("<tr><td>%s</td><td class='hl'>%d</td><td>%d</td><td class='%s'>%+d</td></tr>" % (
        ("首板" if k == 1 else f"{k} 板"), a, b, "up" if d > 0 else ("down" if d < 0 else "mut"), d))
V["TBL_LAD"] = "\n".join(_t)

_LBL = sorted(set(list(lad0.keys()) + list(lad1.keys())))
JS_LAD = {"labels": [("首板" if k == 1 else f"{k}板") for k in _LBL],
          "today": [lad0.get(k, 0) for k in _LBL], "prev": [lad1.get(k, 0) for k in _LBL]}

_t = []
for x in sorted([x for x in zt0 if x["lbc"] >= 2], key=lambda z: (-z["lbc"], -z["amount"])):
    rt = (ths0.get(x["c"]) or {}).get("reason_type") or ""
    _t.append("<tr><td>%s</td><td class='up'>%d</td><td>%s</td><td>%s</td><td>%.2f</td><td>%.2f</td><td>%.1f%%</td><td class='note'>%s</td></tr>" % (
        x["n"], x["lbc"], x["hybk"], hhmm(x["fbt"]), x["fund"] / 1e8, x["amount"] / 1e8, x["hs"], rt))
V["TBL_LIANBAN"] = "\n".join(_t)

# 昨日梯队去向
by = {}
for p in perf:
    by.setdefault(p["lbc"], []).append(p)
for k, pref in [(2, "LAD2Y"), (3, "LAD3Y"), (4, "LAD4Y"), (5, "LAD5Y")]:
    g = by.get(k, [])
    V[pref + "_N"] = len(g)
    V[pref + "_ADV_N"] = sum(1 for p in g if p["again"])
    V[pref + "_MED"] = f2(median([p["pct"] for p in g])) if g else "—"
    V[pref + "_NAMES"] = "、".join(f"{p['name']} {p['pct']:+.2f}%" for p in sorted(g, key=lambda z: -z["pct"])) or "无"
    V[pref + "_DT_N"] = sum(1 for p in g if p["pct"] <= -9.5)

_sb = [p for p in perf if p["lbc"] == 1]
_lbv = [p for p in perf if p["lbc"] >= 2]
V["LAD_SHOU_ADV"] = sum(1 for p in _sb if p["again"])
V["LAD_SHOU_RATE"] = f"{V['LAD_SHOU_ADV'] / len(_sb) * 100:.1f}"
V["LAD_LB_ADV"] = sum(1 for p in _lbv if p["again"])
V["LAD_LB_RATE"] = f"{V['LAD_LB_ADV'] / len(_lbv) * 100:.1f}"
assert V["LAD_SHOU_ADV"] + V["LAD_LB_ADV"] == sum(1 for p in perf if p["again"]), "晋级分组不闭合"

# ================= 成交 / 封单 =================
AMT_SUM = sum(x["amount"] for x in zt0) / 1e8
AMT_SUM_Y = sum(x["amount"] for x in zt1) / 1e8
FUND_SUM = sum(x["fund"] for x in zt0) / 1e8
FUND_SUM_Y = sum(x["fund"] for x in zt1) / 1e8
FUND_MED = median([x["fund"] for x in zt0]) / 1e8
FUND_MED_Y = median([x["fund"] for x in zt1]) / 1e8
MED_AMT = median([x["amount"] for x in zt0]) / 1e8
MED_AMT_Y = median([x["amount"] for x in zt1]) / 1e8
V.update({
    "AMT_SUM": f"{AMT_SUM:.1f}", "AMT_SUM_Y": f"{AMT_SUM_Y:.1f}",
    "AMT_SUM_PCT": f1((AMT_SUM / AMT_SUM_Y - 1) * 100), "AMT_SUM_PCT_ABS": f"{abs((AMT_SUM / AMT_SUM_Y - 1) * 100):.1f}",
    "FUND_SUM": f"{FUND_SUM:.1f}", "FUND_SUM_Y": f"{FUND_SUM_Y:.1f}",
    "FUND_SUM_PCT": f1((FUND_SUM / FUND_SUM_Y - 1) * 100), "FUND_SUM_PCT_ABS": f"{abs((FUND_SUM / FUND_SUM_Y - 1) * 100):.1f}",
    "FUND_MED": f"{FUND_MED:.2f}", "FUND_MED_Y": f"{FUND_MED_Y:.2f}",
    "FUND_MED_PCT": f1((FUND_MED / FUND_MED_Y - 1) * 100), "FUND_MED_PCT_ABS": f"{abs((FUND_MED / FUND_MED_Y - 1) * 100):.1f}",
    "MED_AMT": f"{MED_AMT:.2f}", "MED_AMT_Y": f"{MED_AMT_Y:.2f}",
    "MED_AMT_PCT": f1((MED_AMT / MED_AMT_Y - 1) * 100), "MED_AMT_PCT_ABS": f"{abs((MED_AMT / MED_AMT_Y - 1) * 100):.1f}",
    "SHARE": f"{AMT_SUM / TOT * 100:.2f}", "SHARE_Y": f"{AMT_SUM_Y / TOT_Y * 100:.2f}",
})
_f1 = max(zt0, key=lambda x: x["fund"])
_f1y = max(zt1, key=lambda x: x["fund"])
V.update({"FUND_TOP1_NAME": _f1["n"], "FUND_TOP1": f"{_f1['fund'] / 1e8:.2f}",
          "FUND_TOP1_SHARE": f"{_f1['fund'] / sum(x['fund'] for x in zt0) * 100:.1f}",
          "FUND_TOP1_Y_NAME": _f1y["n"], "FUND_TOP1_Y": f"{_f1y['fund'] / 1e8:.2f}",
          "FUND_TOP1_Y_SHARE": f"{_f1y['fund'] / sum(x['fund'] for x in zt1) * 100:.1f}"})

_sf = sorted(zt0, key=lambda z: -z["fund"])[:10]
_t = []
for x in _sf:
    _t.append("<tr><td>%s</td><td>%.2f</td><td>%.2f</td><td>%.1f 倍</td><td>%.1f%%</td></tr>" % (
        x["n"], x["fund"] / 1e8, x["amount"] / 1e8, x["fund"] / x["amount"], x["hs"]))
V["TBL_FUND_TOP"] = "\n".join(_t)
JS_FUND = {"names": [x["n"] for x in _sf][::-1], "vals": [round(x["fund"] / 1e8, 2) for x in _sf][::-1]}

_t = []
for x in sorted(zt0, key=lambda z: -z["amount"])[:8]:
    _t.append("<tr><td>%s</td><td class='hl'>%.2f</td><td>%.0f</td><td>%d</td><td>%s</td></tr>" % (
        x["n"], x["amount"] / 1e8, x["ltsz"] / 1e8, x["lbc"], x["hybk"]))
V["TBL_AMT_TOP"] = "\n".join(_t)

# ================= 炸板 / 封板时间 =================
sealed = [z for z in zb0 if z["p"] >= z["ztp"]]
V["ZB_POOL_N"] = len(zb0)
V["ZB_SEALED_N"] = len(sealed)
V["ZB_SEAL_NAME"] = "、".join(f"{z['n']} {z['zdp']:+.2f}%" for z in sealed) or "无"
V["ZB_SEAL_PCT"] = f"{len(sealed) / len(zb0) * 100:.1f}" if zb0 else "—"
V["ZB_BIG_N"] = sum(1 for z in zb0 if (z.get("ltsz") or 0) > 100e8)
V["ZB_MED"] = f"{median([(z.get('amount') or 0) for z in zb0]) / 1e8:.2f}"
_zbs = sorted(zb0, key=lambda z: -(z.get("amount") or 0))[:3]
V["ZB_TOP_TXT"] = "、".join(f"{z['n']}（{z['hybk']}，流通 {(z.get('ltsz') or 0) / 1e8:.0f} 亿，成交 {(z.get('amount') or 0) / 1e8:.2f} 亿，收 {z['zdp']:+.2f}%）" for z in _zbs)
_zbs2 = sorted(zb0, key=lambda z: -(z.get("ltsz") or 0))[:3]
V["ZB_BIG_TXT"] = "、".join(f"{z['n']}（流通 {(z.get('ltsz') or 0) / 1e8:.0f} 亿，收 {z['zdp']:+.2f}%）" for z in _zbs2)

ts, tm, ty = S["timeslot"], S["timeslot"]["today"], S["timeslot"]["yesterday"]
PM = tm.get("午后盘中", 0) + tm.get("尾盘", 0)
AM = tm.get("竞价/秒板", 0) + tm.get("开盘半小时", 0) + tm.get("上午盘中", 0)
PM_Y = ty.get("午后盘中", 0) + ty.get("尾盘", 0)
AM_Y = ty.get("竞价/秒板", 0) + ty.get("开盘半小时", 0) + ty.get("上午盘中", 0)
V.update({"TS_PM": PM, "TS_PM_PCT": f"{PM / ZT * 100:.1f}", "TS_AM": AM, "TS_AM_PCT": f"{AM / ZT * 100:.1f}",
          "TS_AM_Y": AM_Y, "TS_PM_Y": PM_Y, "TS_AM_PCT_Y": f"{AM_Y / ZT_Y * 100:.1f}",
          "TS_PM_PCT_Y": f"{PM_Y / ZT_Y * 100:.1f}",
          "TS_HALF": tm.get("竞价/秒板", 0) + tm.get("开盘半小时", 0),
          "TS_HALF_PCT": f"{(tm.get('竞价/秒板', 0) + tm.get('开盘半小时', 0)) / ZT * 100:.1f}"})

_order = [("竞价/秒板", "竞价/秒板"), ("开盘半小时", "开盘半小时"), ("上午盘中", "上午盘中"),
          ("午后盘中", "午后盘中"), ("尾盘", "尾盘")]
_t = []
for k, lbl in _order:
    a, b = tm.get(k, 0), ty.get(k, 0)
    d = a - b
    _t.append("<tr><td>%s</td><td class='hl'>%d</td><td>%d</td><td class='%s'>%+d</td></tr>" % (
        lbl, a, b, "up" if d > 0 else ("down" if d < 0 else "mut"), d))
V["TBL_TS"] = "\n".join(_t)

type0, type1 = {}, {}
for x in A0["ths_zt"]["info"]:
    type0[x.get("limit_up_type") or "?"] = type0.get(x.get("limit_up_type") or "?", 0) + 1
for x in A1["ths_zt"]["info"]:
    type1[x.get("limit_up_type") or "?"] = type1.get(x.get("limit_up_type") or "?", 0) + 1
YIZI, YIZI_Y = type0.get("一字板", 0), type1.get("一字板", 0)
TZI = type0.get("T字板", 0)
HS_ = type0.get("换手板", 0)
CYB = [x for x in zt0 if x["c"].startswith(("300", "301", "688", "689"))]
V.update({"YIZI": YIZI, "YIZI_Y": YIZI_Y, "TZI": TZI, "JINGJIA": tm.get("竞价/秒板", 0),
          "JINGJIA_PCT": f"{tm.get('竞价/秒板', 0) / ZT * 100:.0f}",
          "HUANSHOU": HS_, "HUANSHOU_PCT": f"{HS_ / ZT * 100:.0f}",
          "YIZI_PCT": f"{YIZI / ZT * 100:.0f}", "YIZI_PCT_Y": f"{YIZI_Y / ZT_Y * 100:.0f}",
          "CYB_N": len(CYB), "CYB_PCT": f"{len(CYB) / ZT * 100:.0f}"})

# ================= 主线一：机器人链（五日同口径） =================
KW = ["机器人", "具身", "人形", "灵巧手", "减速器", "丝杠", "关节", "机器视觉"]


def robot_stats(d):
    Bx = json.load(open(os.path.join(OUT, f"zt_review_{d}.json"), encoding="utf-8"))
    Ax = Bx["dates"][d]
    th = {x["code"]: x for x in Ax["ths_zt"]["info"]}
    em = pool(Ax, "em_ZT")
    z = [x for x in em if not x["c"].startswith("92") and x["c"] in th]
    r = [x for x in z if any(k in ((th.get(x["c"]) or {}).get("reason_type") or "") for k in KW)]
    lb = sum(1 for x in r if x["lbc"] >= 2)
    return {"n": len(r), "lb": lb, "r": lb / len(r) * 100 if r else 0.0,
            "hy": len({x["hybk"] for x in r}), "amt": sum(x["amount"] for x in r) / 1e8,
            "list": r}


RB = {d: robot_stats(d) for d in ["20261023", "20261026", "20261027", "20261028", "20261029"]}
rob, rob1 = RB[D0]["list"], RB[D1]["list"]
_rob_amt = sum(x["amount"] for x in rob)
_all_amt = sum(x["amount"] for x in zt0)
_rob_fund = sum(x["fund"] for x in rob)
_all_fund = sum(x["fund"] for x in zt0)
V.update({
    "ROBOT_N": len(rob), "ROBOT_N_Y": len(rob1), "ROBOT_LB": RB[D0]["lb"], "ROBOT_LB_Y": RB[D1]["lb"],
    "ROBOT_LB_PCT_OWN": f"{RB[D0]['r']:.1f}",
    "ROBOT_DROP": f"{abs((RB[D0]['n'] / RB[D1]['n'] - 1) * 100):.0f}",
    "ROBOT_LB_D": RB[D0]["lb"] - RB[D1]["lb"],
    "ROBOT_HY_N": RB[D0]["hy"], "ROBOT_HY_N_Y": RB[D1]["hy"],
    "ROBOT_AMT": f"{RB[D0]['amt']:.1f}", "ROBOT_AMT_Y": f"{RB[D1]['amt']:.1f}",
})
_t = []
for d in ["20261023", "20261026", "20261027", "20261028", "20261029"]:
    x = RB[d]
    _t.append("<tr><td>%s</td><td class='hl'>%d</td><td>%d</td><td>%.1f%%</td><td>%.1f</td><td>%d</td></tr>" % (
        md(d), x["n"], x["lb"], x["r"], x["amt"], x["hy"]))
V["TBL_ROBOT_TREND"] = "\n".join(_t)
JS_ROBOT = {"days": [md(d) for d in ["20261023", "20261026", "20261027", "20261028", "20261029"]],
            "n": [RB[d]["n"] for d in ["20261023", "20261026", "20261027", "20261028", "20261029"]],
            "lb": [RB[d]["lb"] for d in ["20261023", "20261026", "20261027", "20261028", "20261029"]],
            "r": [round(RB[d]["r"], 1) for d in ["20261023", "20261026", "20261027", "20261028", "20261029"]]}

_t = []
for x in sorted(rob, key=lambda z: -z["amount"]):
    _t.append("<tr><td>%s</td><td>%s</td><td>%.1f</td><td class='up'>%d</td><td class='note'>%s</td></tr>" % (
        x["n"], x["hybk"], x["amount"] / 1e8, x["lbc"], (ths0.get(x["c"]) or {}).get("reason_type") or ""))
V["TBL_ROBOT"] = "\n".join(_t)

# 机器人链在今日跌停池中的成员（曾于近四个交易日内以机器人叙事涨停）
dtset = {x["c"] for x in dt0}
dt1set = {x["c"] for x in dt1}
_dtname = {x["c"]: x["n"] for x in dt0}
robdt = []
for d in ["20261023", "20261026", "20261027", "20261028"]:
    Bx = json.load(open(os.path.join(OUT, f"zt_review_{d}.json"), encoding="utf-8"))
    for x in Bx["dates"][d]["ths_zt"]["info"]:
        if x["code"] in dtset and any(k in (x.get("reason_type") or "") for k in KW):
            if x["code"] not in [y["c"] for y in robdt]:
                robdt.append({"c": x["code"], "n": x["name"]})
V["ROBOT_DT_N"] = len(robdt)
V["ROBOT_DT_NAMES"] = "、".join(f"{x['n']}" for x in robdt) or "无"

# 10-26 的 3 板层去向
B26 = json.load(open(os.path.join(OUT, "zt_review_20261026.json"), encoding="utf-8"))
_A26 = B26["dates"]["20261026"]
_l3 = [x for x in pool(_A26, "em_ZT") if x["lbc"] == 3]
V["LAD3_1026_N"] = len(_l3)
V["LAD3_1026_DT"] = sum(1 for x in _l3 if x["c"] in dtset)
V["LAD3_1026_TXT"] = "、".join(f"{x['n']}{'（跌停）' if x['c'] in dtset else ''}" for x in _l3)
_xgzc = next((p for p in perf if p["code"] == "000678"), None)
V["XGZC_PCT"] = f2(_xgzc["pct"]) if _xgzc else "—"

# ================= 主线二：航天/卫星簇 =================
KWC = ["商业航天", "卫星", "航天", "太空"]


def aero_stats(d):
    Bx = json.load(open(os.path.join(OUT, f"zt_review_{d}.json"), encoding="utf-8"))
    Ax = Bx["dates"][d]
    th = {x["code"]: x for x in Ax["ths_zt"]["info"]}
    em = pool(Ax, "em_ZT")
    z = [x for x in em if not x["c"].startswith("92") and x["c"] in th]
    r = [x for x in z if any(k in ((th.get(x["c"]) or {}).get("reason_type") or "") for k in KWC)]
    return r


aero = aero_stats(D0)
aero1 = aero_stats(D1)
_aero_amt = sum(x["amount"] for x in aero)
_aero_fund = sum(x["fund"] for x in aero)
V.update({"AERO_N": len(aero), "AERO_N_Y": len(aero1),
          "AERO_LB": sum(1 for x in aero if x["lbc"] >= 2),
          "AERO_HY_N": len({x["hybk"] for x in aero}),
          "AERO_AMT": f"{_aero_amt / 1e8:.1f}",
          "AERO_AMT_SHARE": f"{_aero_amt / _all_amt * 100:.1f}",
          "AERO_FUND": f"{_aero_fund / 1e8:.2f}",
          "AERO_NAMES": "、".join(f"{x['n']}（{x['hybk']}，{x['lbc']}板，{x['amount'] / 1e8:.1f}亿）"
                                 for x in sorted(aero, key=lambda z: -z["amount"]))})

# 概念板块榜
blk = sorted(A0["ths_block"], key=lambda x: -(x["limit_up_num"] or 0))[:12]
_bd = {b["name"]: b for b in A0["ths_block"]}
_bd1 = {b["name"]: b for b in A1["ths_block"]}


def blk_v(nm, key, d=None):
    b = (_bd if d is None else _bd1).get(nm) or {}
    return b.get(key, 0)


_t = []
for b in blk:
    r = b["continuous_plate_num"] / b["limit_up_num"] * 100 if b["limit_up_num"] else 0
    _t.append("<tr><td>%s</td><td class='hl'>%d</td><td>%d</td><td>%.1f%%</td></tr>" % (
        b["name"], b["limit_up_num"], b["continuous_plate_num"], r))
V["TBL_CONC"] = "\n".join(_t)
JS_CONC = {"names": [b["name"] for b in blk][::-1],
           "num": [b["limit_up_num"] for b in blk][::-1],
           "lb": [b["continuous_plate_num"] for b in blk][::-1]}
V["CONC_TOP1"] = blk[0]["name"]
V["CONC_TOP1_R"] = f"{blk[0]['continuous_plate_num'] / max(1, blk[0]['limit_up_num']) * 100:.1f}"


def conc(name):
    b, b1 = _bd.get(name) or {}, _bd1.get(name) or {}
    n, l, n1, l1 = b.get("limit_up_num", 0), b.get("continuous_plate_num", 0), \
        b1.get("limit_up_num", 0), b1.get("continuous_plate_num", 0)
    return n, l, (l / n * 100 if n else 0), n1, l1, (l1 / n1 * 100 if n1 else 0)


_n, _l, _r, _n1, _l1, _r1 = conc("机器人概念")
V.update({"CONC_ROBOT_N": _n, "CONC_ROBOT_LB": _l, "CONC_ROBOT_R": f"{_r:.1f}",
          "CONC_ROBOT_N_Y": _n1, "CONC_ROBOT_LB_Y": _l1, "CONC_ROBOT_R_Y": f"{_r1:.1f}"})
_n, _l, _r, _n1, _l1, _r1 = conc("商业航天")
V.update({"CONC_AERO_N": _n, "CONC_AERO_LB": _l, "CONC_AERO_R": f"{_r:.1f}"})
_n, _l, _r, _n1, _l1, _r1 = conc("卫星导航")
V.update({"CONC_SAT_N": _n, "CONC_SAT_LB": _l, "CONC_SAT_R": f"{_r:.1f}"})

# 行业迁移
hy0, hy1 = S["hy0"], S["hy1"]
allh = set(hy0) | set(hy1)
hrows = [(h, hy0.get(h, 0), hy1.get(h, 0)) for h in allh]
hrows.sort(key=lambda r: -((r[1] + r[2]) + abs(r[1] - r[2]) * 2))
_hs = hrows[:14][::-1]
V["ZT_HY_N"], V["ZT_HY_Y"] = len(hy0), len(hy1)
V["HY_NEW_N"] = sum(1 for r in hrows if r[2] == 0 and r[1] > 0)
V["HY_ZERO_N"] = sum(1 for r in hrows if r[1] == 0 and r[2] > 0)
V["HY_ZERO_LIST"] = "、".join(f"{r[0]} {r[2]}" for r in sorted([r for r in hrows if r[1] == 0 and r[2] > 0], key=lambda z: (-z[2], z[0]))[:10])
JS_HY = {"names": [r[0] for r in _hs], "vals": [r[1] - r[2] for r in _hs]}
_t = []
for r in _hs[::-1]:
    d = r[1] - r[2]
    _t.append("<tr><td>%s</td><td>%d</td><td>%d</td><td class='%s'>%+d</td></tr>" % (
        r[0], r[2], r[1], "up" if d > 0 else ("down" if d < 0 else "mut"), d))
V["TBL_HY"] = "\n".join(_t)
for h, k in [("食品加工", "HY_SP"), ("航天装备", "HY_HT"), ("专业工程", "HY_ZYGC"), ("通用设备", "HY_TY"),
             ("汽车零部", "HY_QC"), ("元件", "HY_YJ"), ("半导体", "HY_BDT"), ("专用设备", "HY_ZY")]:
    V[k] = hy1.get(h, 0)
    V[k + "0"] = hy0.get(h, 0)

# ================= 昨日涨停股今日表现 =================
adv = [p for p in perf if p["again"]]
V.update({"ADV_N": len(adv), "ADV_TOT": len(perf), "ADV_RATE": f"{len(adv) / len(perf) * 100:.1f}",
          "PERF_MED": f2(median([p["pct"] for p in perf])),
          "PERF_MEAN": f2(mean([p["pct"] for p in perf])),
          "PERF_UP_N": sum(1 for p in perf if p["pct"] > 0), "PERF_DN_N": sum(1 for p in perf if p["pct"] < 0),
          "PERF_GT5_N": sum(1 for p in perf if p["pct"] < -5),
          "NEW_FACE": ZT - len(adv), "NEW_FACE_PCT": f"{(ZT - len(adv)) / ZT * 100:.0f}"})

sb = _sb
lbv = _lbv
SB_M, LB_M = median([p["pct"] for p in sb]), median([p["pct"] for p in lbv])
GAP = SB_M - LB_M
_sb1 = [p for p in S1["perf"] if p["lbc"] == 1]
_lb1 = [p for p in S1["perf"] if p["lbc"] >= 2]
GAP_Y = median([p["pct"] for p in _sb1]) - median([p["pct"] for p in _lb1])
V.update({"GAP_S_M": f2(SB_M), "GAP_L_M": f2(LB_M), "GAP": f"{GAP:+.2f}",
          "SB_MEAN": f2(mean([p["pct"] for p in sb])), "LB_MEAN": f2(mean([p["pct"] for p in lbv])),
          "SB_DN": sum(1 for p in sb if p["pct"] < 0),
          "LB_SB": sum(1 for p in lbv if p["pct"] < 0),
          "GAP_Y": f"{GAP_Y:+.2f}", "GAP_SWING": f"{abs(GAP - GAP_Y):.2f}",
          "GAP_Y_ABS": f"{abs(GAP_Y):.2f}", "GAP_ABS": f"{abs(GAP):.2f}",
          "GAP_SIGN": "连板强" if GAP < 0 else "首板强",
          "GAP_SIGN_Y": "连板强" if GAP_Y < 0 else "首板强",
          "GAP_S_M_Y": f2(median([p['pct'] for p in _sb1])), "GAP_L_M_Y": f2(median([p['pct'] for p in _lb1]))})
assert len(_sb1) + len(_lb1) == len(S1["perf"]), "昨日分组计数不闭合"

_t = []
for nm, g in [("全部", perf), ("昨日首板", sb), ("昨日连板", lbv)]:
    vs = [p["pct"] for p in g]
    _t.append("<tr><td>%s</td><td>%d</td><td>%d（%.1f%%）</td><td class='%s'>%s</td><td class='hl'>%s</td><td>%d</td></tr>" % (
        nm, len(g), sum(1 for p in g if p["again"]), sum(1 for p in g if p["again"]) / len(g) * 100,
        "up" if mean(vs) > 0 else "down", f2(mean(vs)), f2(median(vs)), sum(1 for v in vs if v < 0)))
V["TBL_PERF"] = "\n".join(_t)
_srt = sorted(perf, key=lambda x: x["pct"])
V["PERF_BOT"] = "、".join(f"{p['name']} {p['pct']:+.2f}%（昨{p['lbc']}板）" for p in _srt[:5])
V["PERF_TOP"] = "、".join(f"{p['name']} {p['pct']:+.2f}%（昨{p['lbc']}板）" for p in _srt[-5:][::-1])
JS_PF = {"names": [p["name"] for p in _srt], "vals": [round(p["pct"], 2) for p in _srt]}

# ================= 跌停池 =================
DT_AMT = sum(x.get("amount") or 0 for x in dt0) / 1e8
DT_AMT_Y = sum(x.get("amount") or 0 for x in dt1) / 1e8
V.update({"DT_AMT": f"{DT_AMT:.1f}", "DT_AMT_YD": f"{DT_AMT_Y:.1f}",
          "DT_RATIO": f"{DT_AMT / AMT_SUM:.2f}", "DT_RATIO_Y": f"{DT_AMT_Y / AMT_SUM_Y:.2f}",
          "DT_POOL_N": len(dt0), "DT_YD_N": len(dt1), "DT_X_AMT": f"{DT_AMT / DT_AMT_Y:.1f}",
          "DT_HY_N": len({x.get("hybk") for x in dt0}),
          "DT_AMT_YD_SHARE": f"{DT_AMT_Y / TOT_Y * 100:.2f}",
          "DT_BIG_N": sum(1 for x in dt0 if (x.get("ltsz") or 0) > 100e8)})
_diff = len(dt0) - DT
V["DT_DIFF_TXT"] = (f"东财池比同花顺汇总少 {abs(_diff)} 只、pool 非空且全为沪深代码、不可逐只归因" if _diff < 0
                    else (f"东财池比同花顺汇总多 {_diff} 只、均为沪深代码、不可逐只归因" if _diff else "两源一致"))

hycnt = {}
for x in dt0:
    hycnt[x.get("hybk")] = hycnt.get(x.get("hybk"), 0) + 1
_hysorted = sorted(hycnt.items(), key=lambda kv: (-kv[1], kv[0]))
V["DT_HY_TXT"] = "、".join(f"{n} {c}" for n, c in _hysorted)
_top4 = sum(c for _, c in _hysorted[:4])
V["DT_TOP4_PCT"] = f"{_top4 / len(dt0) * 100:.0f}"
JS_DTCHAIN = {"names": [n for n, _ in _hysorted[:10]][::-1],
              "vals": [c for _, c in _hysorted[:10]][::-1],
              "chain": [n in ("元件", "通信设备", "半导体", "消费电子", "光学光电", "其他电子", "电子化学品")
                        for n, _ in _hysorted[:10]][::-1]}

_t = []
for x in sorted(dt0, key=lambda z: -(z.get("amount") or 0)):
    _t.append("<tr><td>%s</td><td>%s</td><td class='down'>%.2f%%</td><td>%.2f</td><td>%.0f</td></tr>" % (
        x["n"], x.get("hybk"), x.get("zdp") or 0, (x.get("amount") or 0) / 1e8, (x.get("ltsz") or 0) / 1e8))
V["TBL_DT_TD"] = "\n".join(_t)
_dtop = max(dt0, key=lambda z: z.get("amount") or 0) if dt0 else {}
V["DT_TOP_NAME"] = _dtop.get("n", "—")
V["DT_TOP_HY"] = _dtop.get("hybk", "—")
V["DT_TOP_LTSZ"] = f"{(_dtop.get('ltsz') or 0) / 1e8:.0f}"
V["DT_TOP_AMT"] = f"{(_dtop.get('amount') or 0) / 1e8:.2f}"

# 算力硬件链跌停
CHAIN_HY = ("元件", "通信设备", "半导体", "消费电子", "光学光电", "其他电子", "电子化学品")
chain = [x for x in dt0 if x.get("hybk") in CHAIN_HY]
CHAIN_AMT = sum(x.get("amount") or 0 for x in chain) / 1e8
V.update({"CHAIN_N": len(chain), "CHAIN_PCT": f"{len(chain) / len(dt0) * 100:.0f}",
          "CHAIN_AMT": f"{CHAIN_AMT:.1f}", "CHAIN_AMT_PCT": f"{CHAIN_AMT / DT_AMT * 100:.0f}"})
_t = []
for x in sorted(chain, key=lambda z: -(z.get("amount") or 0)):
    _t.append("<tr><td>%s</td><td>%s</td><td class='down'>%.2f%%</td><td>%.2f</td><td>%.0f</td></tr>" % (
        x["n"], x.get("hybk"), x.get("zdp") or 0, (x.get("amount") or 0) / 1e8, (x.get("ltsz") or 0) / 1e8))
V["TBL_CHAIN"] = "\n".join(_t)

# 昨日跌停池今日表现
QP = os.path.join(OUT, f"_qdt{D1[4:]}.json")
Q = {}
if os.path.exists(QP):
    Q = json.load(open(QP, encoding="utf-8"))
else:
    _op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    codes = [x["c"] for x in dt1]
    for i in range(0, len(codes), 25):
        bt = codes[i:i + 25]
        u = "https://qt.gtimg.cn/q=" + ",".join(("sh" if c[0] == "6" else ("bj" if c[0] == "9" else "sz")) + c for c in bt)
        raw = _op.open(u, timeout=20).read().decode("gbk", errors="ignore")
        for line in raw.split(";"):
            if "=" not in line:
                continue
            fs = line.split("=", 1)[1].strip().strip('"').split("~")
            if len(fs) < 40:
                continue
            Q[fs[2]] = {"name": fs[1], "pct": float(fs[32] or 0), "amount": float(fs[37] or 0) / 1e4}
    json.dump(Q, open(QP, "w", encoding="utf-8"), ensure_ascii=False)

dt1c = [x["c"] for x in dt1]
inter = sorted({x["code"] for x in A0["ths_zt"]["info"]} & set(dt1c))
vals = [Q[c]["pct"] for c in dt1c if c in Q]
V.update({
    "REL_MEAN": f2(mean(vals)), "REL_MED": f2(median(vals)),
    "REL_UP": sum(1 for v in vals if v > 0), "REL_UP_PCT": f"{sum(1 for v in vals if v > 0) / len(vals) * 100:.0f}",
    "REL_DT": sum(1 for v in vals if v <= -9.8),
    "REL_DT_NAMES": "、".join(f"{Q[c]['name']} {Q[c]['pct']:.2f}%" for c in dt1c if c in Q and Q[c]["pct"] <= -9.8) or "无",
    "REL_BIG": sum(1 for v in vals if v > 5),
    "REL_AMT": f"{sum(Q[c]['amount'] for c in dt1c if c in Q):.1f}",
    "INTER_N": len(inter),
    "INTER_NAMES": "、".join(f"{Q[c]['name']} {Q[c]['pct']:+.2f}%" for c in inter if c in Q) if inter else "一只都没有",
})

_bins = [(-100, -9.8, "跌停"), (-9.8, -5, "跌5~停"), (-5, -2, "跌2~5"), (-2, 0, "跌0~2"),
         (0, 2, "涨0~2"), (2, 5, "涨2~5"), (5, 9.8, "涨5~停"), (9.8, 100, "涨停")]
JS_REL = {"labels": [b[2] for b in _bins], "vals": [], "colors": []}
for lo, hi, lbl in _bins:
    n = sum(1 for v in vals if v <= -9.8) if lbl == "跌停" else sum(1 for v in vals if lo < v <= hi)
    JS_REL["vals"].append(n)
    JS_REL["colors"].append("down" if hi <= 0 else "up")

# 昨涨停 -> 今跌停
_att = [p for p in perf if p["code"] in dtset]
V["ATK_DT_N"] = len(_att)
V["ATK_DT_NAMES"] = "、".join(f"{p['name']}（昨{p['lbc']}板，{p['hybk']}）" for p in _att) or "无"
# 昨涨停池中有多少落在今日跌停池（用于 lead 里那句"清算不打在昨天的钱上"）
V["YDAY_ZT_IN_DT"] = len(_att)
_dts = dtset & dt1set
V["DT_CONT_N"] = len(_dts)
V["DT_CONT_NAMES"] = "、".join(f"{_dtname.get(c, Q.get(c, {}).get('name', c))}" for c in _dts) or "无"

# ================= 口径披露 =================
_bj = [x for x in zt_all if x["c"].startswith("92")]
V["BJ_N"] = len(_bj)
V["BJ_CODES"] = "、".join(f"{x['n']}（{x['c']}）" for x in _bj) or "无"
V["EM_ZT_N"] = len(zt0_em)
V["EM_DIFF_N"] = len(zt0_em) - ZT
DIFS = sorted({x["c"] for x in zt_all} - {x["c"] for x in zt0})
V["EM_DIFF_CODES"] = "、".join(DIFS) or "无"
_bad = [c for c in DIFS if not c.startswith("92")]
assert not _bad, f"东财差额里出现无法归因的沪深代码：{_bad}"

# ================= westock 行业/概念榜交叉验证 =================
SWP = os.path.join(OUT, f"_sw{D0[4:]}.json")
_need = ["通信设备", "元件", "半导体", "消费电子", "银行概念", "城商行Ⅱ", "保险Ⅱ", "煤炭开采",
         "光芯片", "博通概念", "覆铜板", "光通信", "共封装光模块(CPO）", "航天系", "航天装备概念", "军工央企"]


def _parse_wt(txt):
    rows = {}
    for line in txt.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        p = [q.strip() for q in s.strip("|").split("|")]
        if len(p) < 10 or p[1] in ("name", "---") or set(p[1]) <= set("-"):
            continue
        try:
            rows[p[1]] = {"pct": float(p[2]), "flow": float(p[3]), "updown": p[8]}
        except Exception:
            continue
    return rows


SW = {}
if os.path.exists(SWP):
    SW = json.load(open(SWP, encoding="utf-8"))
else:
    _wx = "C:/Users/Administrator/.local/bin/westock.exe"
    try:
        for kind in ("industry", "concept"):
            r = subprocess.run([_wx, "sector", "ranking", "--kind", kind], capture_output=True, timeout=120)
            txt = r.stdout.decode("utf-8", errors="ignore")
            for k, v in _parse_wt(txt).items():
                if k in _need:
                    SW[k] = v
        json.dump(SW, open(SWP, "w", encoding="utf-8"), ensure_ascii=False)
    except Exception as e:
        print("warn: westock 取数失败", e)
if not SW:
    raise SystemExit("缺少 westock 行业/概念榜数据，无法生成三口径验证表")


def sw(nm, key="pct", dflt=0.0):
    return (SW.get(nm) or {}).get(key, dflt)


def sw_out(nm):
    v = SW.get(nm)
    return f2(v["pct"]) if v else "—"


def sw_up(nm):
    v = (SW.get(nm) or {}).get("updown") or ""
    return v if "/" in v else "—"


def sw_flow(nm):
    v = SW.get(nm)
    return f"{(v['flow'] / 10000):+.1f}" if v else "—"


V.update({
    "SW_TX": sw_out("通信设备"), "SW_TX_UP": sw_up("通信设备"), "SW_TX_FLOW": f"{sw('通信设备', 'flow') / 10000:.1f}",
    "SW_YJ": sw_out("元件"), "SW_YJ_UP": sw_up("元件"), "SW_YJ_FLOW": f"{sw('元件', 'flow') / 10000:.1f}",
    "SW_BDT": sw_out("半导体"), "SW_BDT_UP": sw_up("半导体"), "SW_BDT_FLOW": f"{sw('半导体', 'flow') / 10000:.1f}",
    "SW_XFD": sw_out("消费电子"), "SW_XFD_UP": sw_up("消费电子"), "SW_XFD_FLOW": f"{sw('消费电子', 'flow') / 10000:.1f}",
    "SW_BANK": sw_out("银行概念"), "SW_INS": sw_out("保险Ⅱ"), "SW_COAL": sw_out("煤炭开采"),
    "CN_OC": sw_out("光芯片"), "CN_OC_UP": sw_up("光芯片"),
    "CN_BT": sw_out("博通概念"), "CN_BT_UP": sw_up("博通概念"),
    "CN_FTB": sw_out("覆铜板"), "CN_FTB_UP": sw_up("覆铜板"),
    "CN_OC2": sw_out("光通信"), "CN_CPO": sw_out("共封装光模块(CPO）"),
    "SW_AERO": sw_out("航天系"), "SW_AERO_UP": sw_up("航天系"),
    "SW_AERO_FLOW": f"{sw('航天系', 'flow') / 10000:.2f}",
    "SW_AERO2": sw_out("航天装备概念"), "SW_AERO2_UP": sw_up("航天装备概念"),
    "SW_MIL": sw_out("军工央企"), "SW_MIL_UP": sw_up("军工央企"),
})

_rows = [
    ("申万二级", "通信设备", "通信设备"),
    ("申万二级", "元件（PCB / 覆铜板 / 被动件）", "元件"),
    ("申万二级", "半导体", "半导体"),
    ("申万二级", "消费电子", "消费电子"),
    ("概念板块", "光芯片", "光芯片"),
    ("概念板块", "覆铜板", "覆铜板"),
    ("概念板块", "光通信", "光通信"),
    ("概念板块", "共封装光模块 CPO", "共封装光模块(CPO）"),
    ("对照（正向）", "银行（概念口径）", "银行概念"),
    ("对照（正向）", "煤炭开采", "煤炭开采"),
    ("对照（正向）", "航天系", "航天系"),
]
_t = []
for src, nm, key in _rows:
    v = SW.get(key) or {}
    pct = f2(v.get("pct", 0))
    flow = f"{v.get('flow', 0) / 10000:+.1f}"
    _t.append("<tr><td>%s</td><td>%s</td><td class='%s'>%s%%</td><td>%s</td><td class='%s'>%s</td></tr>" % (
        src, nm, "up" if v.get("pct", 0) > 0 else "down", pct,
        (v.get("updown") or "—"), "up" if v.get("flow", 0) > 0 else "down", flow))
V["TBL_SW"] = "\n".join(_t)

# ================= JS =================
JS_SENTI = {"days": [x["d"] for x in days], "zt": [x["zt"] for x in days],
            "dt": [x["dt"] for x in days], "seal": [round(x["seal"], 1) for x in days]}
JS_INTRA = {"names": [x["nm"] for x in INTRA], "gap": [round(x["gap"], 2) for x in INTRA],
            "low": [round(x["low"], 2) for x in INTRA], "close": [round(x["close"], 2) for x in INTRA]}
JS_AMT = {"names": [x["name"] for x in ix], "yoy": [None if x["yoy"] is None else round(x["yoy"], 1) for x in ix]}
JS_TS = {"labels": [k for k, _ in _order], "today": [tm.get(k, 0) for k, _ in _order],
         "prev": [ty.get(k, 0) for k, _ in _order]}
for k, v in [("JS_SENTI", JS_SENTI), ("JS_INTRA", JS_INTRA), ("JS_AMT", JS_AMT), ("JS_LAD", JS_LAD),
             ("JS_CONC", JS_CONC), ("JS_ROBOT", JS_ROBOT), ("JS_HY", JS_HY), ("JS_PF", JS_PF),
             ("JS_REL", JS_REL), ("JS_TS", JS_TS), ("JS_FUND", JS_FUND), ("JS_DTCHAIN", JS_DTCHAIN)]:
    V[k] = json.dumps(v, ensure_ascii=False)
V["GEN_TIME"] = time.strftime("%Y-%m-%d %H:%M")

# ================= 渲染 =================
tpl = open(TPL, encoding="utf-8").read()
out = tpl
for k, v in sorted(V.items(), key=lambda kv: -len(kv[0])):
    out = out.replace("__" + k + "__", str(v))
res = sorted(set(re.findall(r"__[A-Z_0-9]+__", out)))
print("placeholder residue:", res)
if res:
    raise SystemExit("残留占位符，终止")
rp = os.path.join(REP, f"涨停复盘对比-{D0}.html")
open(rp, "w", encoding="utf-8").write(out)
print("saved ->", rp, len(out), "bytes")
