# -*- coding: utf-8 -*-
"""涨停复盘报告 20261023 vs 20261022（深 V 反转 · 换血式反弹）

用法：python zt_report_20261023.py 20261023
输入：out/zt_stats_20261023.json、out/zt_review_20261023.json、out/zt_review_20261022.json
     跌停池明细 out/_dt1023.json / out/_dt1022.json（东财 getTopicDTPool，sort=fund:asc）
     昨日跌停股今日行情：腾讯快照（脚本内实时抓取，带本地缓存 out/_qdt1022.json）
输出：reports/涨停复盘对比-20261023.html
"""
import json, os, sys, html, re, urllib.request, time
from statistics import mean, median

ROOT = os.environ.get("ZT_ROOT") or os.getcwd()
OUT = os.path.join(ROOT, "out")
REP = os.path.join(ROOT, "reports")
TPL = os.path.join(ROOT, "scripts", "_report_tpl_20261023.html")
os.makedirs(REP, exist_ok=True)

D0 = sys.argv[1] if len(sys.argv) > 1 else "20261023"
S = json.load(open(os.path.join(OUT, f"zt_stats_{D0}.json"), encoding="utf-8"))
D0, D1, D2 = S["D0"], S["D1"], S["D2"]
B = json.load(open(os.path.join(OUT, f"zt_review_{D0}.json"), encoding="utf-8"))
B1 = json.load(open(os.path.join(OUT, f"zt_review_{D1}.json"), encoding="utf-8"))
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


def a1(v):
    return f"{abs(v):.1f}"


def a2(v):
    return f"{abs(v):.2f}"


V = {}
V["D0"], V["D1"], V["D2"] = md(D0), md(D1), md(D2)
V["NEXT_D"] = "10/26（周一）"


def pool(zn, key):
    return (zn.get(key) or {}).get("pool") or []


zt0_all, zt1_all = pool(A0, "em_ZT"), pool(A1, "em_ZT")
zt0 = [x for x in zt0_all if not x["c"].startswith("92")]
zt1 = [x for x in zt1_all if not x["c"].startswith("92")]
zb0, zb1 = pool(A0, "em_ZB"), pool(A1, "em_ZB")
ths0 = {x["code"]: x for x in A0["ths_zt"]["info"]}
ths1 = {x["code"]: x for x in A1["ths_zt"]["info"]}
DTS = {}  # 跌停池


def load_dt(d):
    p = os.path.join(OUT, f"_dt{d[4:]}.json")
    if os.path.exists(p):
        return (json.load(open(p, encoding="utf-8")).get("data") or {}).get("pool") or []
    return []


dt0, dt1 = load_dt(D0), load_dt(D1)

# ================= 情绪 =================
ZT, ZT_Y = len(zt0), len(zt1)
TOUCH, TOUCH_Y = A0["ths_zt"]["total"]["today"]["history_num"], A1["ths_zt"]["total"]["today"]["history_num"]
TOUCH_0 = s1["yest"]["history_num"]
ZB, ZB_Y = s0["zb"], s1["zb"]
SEAL = s0["seal_rate"] * 100
SEAL_Y = s1["seal_rate"] * 100
SEAL_0 = s1["zt_prev"] / TOUCH_0 * 100
DT, DT_Y = s0["dt"], s1["dt"]
_dc0 = A0["ths_zt"]["limit_down_count"]["today"]
_dc1 = A1["ths_zt"]["limit_down_count"]["today"]
_dc0_prev = A1["ths_zt"]["limit_down_count"]["yesterday"]  # 10-21 的跌停统计（A0 的 yesterday 是 10-22，勿用）
DTOUCH, DTOUCH_Y = _dc0["history_num"], _dc1["history_num"]
DTOUCH_0 = _dc0_prev["history_num"]
DSEAL, DSEAL_Y = _dc0["rate"] * 100, _dc1["rate"] * 100
DSEAL_0 = _dc0_prev["rate"] * 100 if _dc0_prev else 0.0
DT_OPEN_N = DTOUCH - DT

V.update({
    "ZT": ZT, "ZT_Y": ZT_Y, "ZT_D": f"{ZT - ZT_Y:+d}", "ZT_PCT_D": f"{abs((ZT / ZT_Y - 1) * 100):.0f}",
    "TOUCH": TOUCH, "TOUCH_Y": TOUCH_Y, "TOUCH_D": f"{TOUCH - TOUCH_Y:+d}", "TOUCH_PCT": f"{abs((TOUCH / TOUCH_Y - 1) * 100):.0f}",
    "SEAL": f"{SEAL:.1f}", "SEAL_Y": f"{SEAL_Y:.1f}", "SEAL_D": f"{SEAL - SEAL_Y:+.1f}",
    "SEAL_FAIL": f"{(ZT / TOUCH * 0 - 1 + 1) * 0 + (1 - ZT / TOUCH) * 100:.1f}",
    "SEAL_FAIL_Y": f"{(1 - ZT_Y / TOUCH_Y) * 100:.1f}",
    "DT": DT, "DT_Y": DT_Y, "DT_D": f"{DT - DT_Y:+d}",
    "DTOUCH": DTOUCH, "DTOUCH_Y": DTOUCH_Y, "DTOUCH_X": f"{DTOUCH / DTOUCH_Y:.1f}",
    "DSEAL": f"{DSEAL:.1f}", "DSEAL_Y": f"{DSEAL_Y:.1f}",
    "DT_OPEN_N": DT_OPEN_N, "DT_REBUY": f"{DT_OPEN_N / DTOUCH * 100:.1f}",
    "ZB": ZB, "ZB_Y": ZB_Y,
})

# 三日阶梯
days = [
    {"d": md(D2), "zt": s1["zt_prev"], "zb": s1["zb_prev"], "dt": s1["dt_prev"], "touch": TOUCH_0, "dtouch": DTOUCH_0},
    {"d": md(D1), "zt": s1["zt"], "zb": s1["zb"], "dt": s1["dt"], "touch": TOUCH_Y, "dtouch": DTOUCH_Y},
    {"d": md(D0), "zt": s0["zt"], "zb": s0["zb"], "dt": s0["dt"], "touch": TOUCH, "dtouch": DTOUCH},
]
for x in days:
    x["seal"] = x["zt"] / x["touch"] * 100 if x["touch"] else 0.0

V["ZTDT"] = f"{ZT / DT:.1f}" if DT else "—"
V["ZTDT_Y"] = f"{ZT_Y / DT_Y:.1f}" if DT_Y else "—"
V["ZTDT_0"] = f"{days[0]['zt'] / days[0]['dt']:.1f}" if days[0]["dt"] else "—"

_tbl = []
_rows = [("涨停家数", "zt"), ("炸板家数", "zb"), ("封板率", "seal"), ("触及涨停家数", "touch"),
         ("跌停家数", "dt"), ("触及跌停家数", "dtouch")]
for nm, k in _rows:
    vs = [x[k] for x in days]
    if k == "seal":
        cells = [f"{v:.1f}%" for v in vs]
        d = vs[2] - vs[1]
        chg = f'<span class="{"up" if d > 0 else "down"}">{d:+.1f}pct</span>'
    else:
        cells = [f"{int(v)}" for v in vs]
        d = vs[2] - vs[1]
        chg = f'<span class="{"up" if d > 0 else "down"}">{d:+d}</span>'
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
V["AMT_UP_N"] = sum(1 for x in ix if (x["yoy"] or 0) > 0)
V["N_UP"] = sum(1 for x in ix if x["pct"] > 0)

# 日内 OHLC（腾讯日线，独立于 index_hist 的窗口滑动）
OHLC = {}
try:
    _op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for nm, sym in [("上证指数", "sh000001"), ("深证成指", "sz399001"), ("创业板指", "sz399006"),
                    ("科创50", "sh000688"), ("国证2000", "sz399303"), ("上证50", "sh000016")]:
        u = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=" + sym + ",day,,,10,qfq"
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
                  "reb": (o["close"] / o["low"] - 1) * 100})

V["N_BELOW_OPEN"] = sum(1 for x in INTRA if x["close"] < x["gap"])

for key, nm in [("SH", "上证指数"), ("CY", "创业板指"), ("KC", "科创50"), ("GZ", "国证2000")]:
    x = next((y for y in INTRA if y["nm"] == nm), None)
    if x:
        V[key + "_GAP"] = f2(x["gap"])
        V[key + "_LOW"] = f2(x["low"])
        V[key + "_PCT"] = f2(x["close"])
        V[key + "_PCT_ABS"] = f"{x['close']:.2f}"
        V[key + "_REB"] = f"{x['reb']:.2f}"
V["SH50_GAP"] = f2(next((y["gap"] for y in INTRA if y["nm"] == "上证50"), 0))
V["SH50_PCT"] = f2(next((y["close"] for y in INTRA if y["nm"] == "上证50"), 0))
V["SH50_PCT_ABS"] = f"{next((y['close'] for y in INTRA if y['nm'] == '上证50'), 0):.2f}"
for key, nm in [("SH50", "上证50"), ("CY", "创业板指")]:
    r = next((y for y in ix if y["name"] == nm), None)
    if r:
        V[key + "_AMT"] = f"{r['amt']:.0f}"
        V[key + "_YOY"] = f1(r["yoy"] or 0)

_t = []
for x in ix:
    yoy = "—" if x["yoy"] is None else f'<span class="{"up" if x["yoy"] > 0 else "down"}">{x["yoy"]:+.1f}%</span>'
    pp = "—" if x["prev_pct"] is None else f"{x['prev_pct']:+.2f}%"
    _t.append("<tr><td>%s</td><td class='%s'>%s</td><td class='mut'>%s</td><td>%.0f</td><td>%s</td></tr>" % (
        x["name"], "up" if x["pct"] > 0 else "down", f"{x['pct']:+.2f}%", pp, x["amt"], yoy))
V["TBL_IDX"] = "\n".join(_t)

# ================= 梯队 =================
LAD = {1: 68, 2: 9, 3: 1, 6: 2}
lad0 = {}
for x in zt0:
    lad0[x["lbc"]] = lad0.get(x["lbc"], 0) + 1
lad1 = {}
for x in zt1:
    lad1[x["lbc"]] = lad1.get(x["lbc"], 0) + 1
MAXB = max(lad0)
MAXB_Y = max(lad1)
LB, LB_Y = sum(v for k, v in lad0.items() if k >= 2), sum(v for k, v in lad1.items() if k >= 2)
SHOU, SHOU_Y = lad0.get(1, 0), lad1.get(1, 0)
V.update({"MAXB": MAXB, "MAXB_Y": MAXB_Y, "LB": LB, "LB_Y": LB_Y, "SHOU": SHOU,
          "SHOU_PCT": f"{SHOU / ZT * 100:.1f}", "SHOU_PCT_Y": f"{SHOU_Y / ZT_Y * 100:.1f}",
          "LAD2": lad0.get(2, 0), "LAD3": lad0.get(3, 0), "LAD2_Y": lad1.get(2, 0), "LAD3_Y": lad1.get(3, 0)})
_maxb = [x for x in zt0 if x["lbc"] == MAXB]
V["MAXB_NAMES"] = "、".join(f"{x['n']}（{ths0.get(x['c'], {}).get('high_days', '')}）" for x in _maxb)
V["LB_HY_N"] = len({x["hybk"] for x in zt0 if x["lbc"] >= 2})

_t = []
for k in sorted(set(list(lad0.keys()) + list(lad1.keys()))):
    a, b = lad0.get(k, 0), lad1.get(k, 0)
    d = a - b
    _t.append("<tr><td>%s</td><td class='hl'>%d</td><td>%d</td><td class='%s'>%+d</td></tr>" % (
        ("首板" if k == 1 else f"{k} 板"), a, b, "up" if d > 0 else ("down" if d < 0 else "mut"), d))
V["TBL_LAD"] = "\n".join(_t)

JS_LAD = {"labels": [("首板" if k == 1 else f"{k}板") for k in range(1, MAXB + 1)],
          "today": [lad0.get(k, 0) for k in range(1, MAXB + 1)],
          "prev": [lad1.get(k, 0) for k in range(1, MAXB + 1)]}

_t = []
for x in sorted([x for x in zt0 if x["lbc"] >= 2], key=lambda z: (-z["lbc"], -z["amount"])):
    rt = (ths0.get(x["c"]) or {}).get("reason_type") or ""
    _t.append("<tr><td>%s</td><td class='up'>%d</td><td>%s</td><td>%s</td><td>%.2f</td><td>%.2f</td><td>%.1f%%</td><td class='note'>%s</td></tr>" % (
        x["n"], x["lbc"], x["hybk"], hhmm(x["fbt"]), x["fund"] / 1e8, x["amount"] / 1e8, x["hs"], rt))
V["TBL_LIANBAN"] = "\n".join(_t)

_dy = next(x for x in zt0 if x["n"] == "大业股份")
_hyw = next(x for x in zt0 if x["n"] == "海洋王")
V.update({"DY_FUND": f"{_dy['fund'] / 1e8:.2f}", "DY_AMT": f"{_dy['amount'] / 1e8:.2f}",
          "DY_TURN": f"{_dy['hs']:.1f}", "DY_RATIO": f"{_dy['fund'] / _dy['amount'] * 100:.1f}",
          "HYW_FUND": f"{_hyw['fund'] / 1e8:.2f}", "HYW_AMT": f"{_hyw['amount'] / 1e8:.2f}",
          "HYW_TURN": f"{_hyw['hs']:.1f}", "HYW_RATIO": f"{_hyw['fund'] / _hyw['amount'] * 100:.1f}"})

# 昨日梯队去向
by = {}
for p in perf:
    by.setdefault(p["lbc"], []).append(p)
V["LAD2Y_N"] = len(by.get(2, []))
V["LAD2Y_ADV_N"] = sum(1 for p in by.get(2, []) if p["again"])
V["LAD2Y_ADV_NAMES"] = "、".join(p["name"] for p in by.get(2, []) if p["again"]) or "无"
V["LAD3Y_N"] = len(by.get(3, []))
V["LAD3Y_ADV_N"] = sum(1 for p in by.get(3, []) if p["again"])
V["LAD3Y_NAMES"] = "、".join(f"{p['name']} {p['pct']:+.2f}%" for p in sorted(by.get(3, []), key=lambda z: -z["pct"]))
V["LAD2Y_MED"] = f2(median([p["pct"] for p in by.get(2, [])]))
V["LAD3Y_MED"] = f2(median([p["pct"] for p in by.get(3, [])]))

# 昨日电机Ⅱ → 今日（回答 10-22 观察点③）
_mj = [p for p in perf if p["hybk"] == "电机Ⅱ"]
V["MJ_Y"] = len(_mj)
V["MJ_ADV"] = sum(1 for p in _mj if p["again"])
V["MJ_MED"] = f2(median([p["pct"] for p in _mj]))

# ================= 成交 / 封单 =================
AMT_SUM = sum(x["amount"] for x in zt0) / 1e8
AMT_SUM_Y = sum(x["amount"] for x in zt1) / 1e8
FUND_SUM = sum(x["fund"] for x in zt0) / 1e8
FUND_SUM_Y = sum(x["fund"] for x in zt1) / 1e8
FUND_MED = median([x["fund"] for x in zt0]) / 1e8
FUND_MED_Y = median([x["fund"] for x in zt1]) / 1e8
V.update({
    "AMT_SUM": f"{AMT_SUM:.1f}", "AMT_SUM_Y": f"{AMT_SUM_Y:.1f}",
    "AMT_SUM_PCT": f1((AMT_SUM / AMT_SUM_Y - 1) * 100), "AMT_SUM_PCT_ABS": f"{abs((AMT_SUM / AMT_SUM_Y - 1) * 100):.1f}",
    "FUND_SUM": f"{FUND_SUM:.1f}", "FUND_SUM_Y": f"{FUND_SUM_Y:.1f}",
    "FUND_SUM_PCT": f1((FUND_SUM / FUND_SUM_Y - 1) * 100), "FUND_SUM_PCT_ABS": f"{abs((FUND_SUM / FUND_SUM_Y - 1) * 100):.1f}",
    "FUND_MED": f"{FUND_MED:.2f}", "FUND_MED_Y": f"{FUND_MED_Y:.2f}",
    "FUND_MED_PCT": f1((FUND_MED / FUND_MED_Y - 1) * 100), "FUND_MED_PCT_ABS": f"{abs((FUND_MED / FUND_MED_Y - 1) * 100):.1f}",
    "SHARE": f"{AMT_SUM / TOT * 100:.2f}", "SHARE_Y": f"{AMT_SUM_Y / TOT_Y * 100:.2f}",
})
_f1 = max(zt0, key=lambda x: x["fund"])
_f1y = max(zt1, key=lambda x: x["fund"])
V.update({"FUND_TOP1_NAME": _f1["n"], "FUND_TOP1": f"{_f1['fund'] / 1e8:.2f}",
          "FUND_TOP1_SHARE": f"{_f1['fund'] / sum(x['fund'] for x in zt0) * 100:.1f}",
          "FUND_TOP1_Y_NAME": _f1y["n"], "FUND_TOP1_Y": f"{_f1y['fund'] / 1e8:.2f}",
          "FUND_TOP1_Y_SHARE": f"{_f1y['fund'] / sum(x['fund'] for x in zt1) * 100:.1f}"})

_t = []
for x in sorted(zt0, key=lambda z: -z["fund"])[:12]:
    _t.append("<tr><td>%s</td><td>%.2f</td><td>%.2f</td><td>%.1f%%</td><td>%.1f%%</td></tr>" % (
        x["n"], x["fund"] / 1e8, x["amount"] / 1e8, x["fund"] / x["amount"] * 100, x["hs"]))
V["TBL_FUND_TOP"] = "\n".join(_t)
JS_FUND = {"names": [x["n"] for x in sorted(zt0, key=lambda z: -z["fund"])[:10]][::-1],
           "vals": [round(x["fund"] / 1e8, 2) for x in sorted(zt0, key=lambda z: -z["fund"])[:10]][::-1]}

_t = []
for x in sorted(zt0, key=lambda z: -z["amount"])[:8]:
    _t.append("<tr><td>%s</td><td class='hl'>%.2f</td><td>%.0f</td><td>%d</td><td>%s</td></tr>" % (
        x["n"], x["amount"] / 1e8, x["ltsz"] / 1e8, x["lbc"], x["hybk"]))
V["TBL_AMT_TOP"] = "\n".join(_t)

# ================= 炸板 / 封板时间 =================
V["ZB_POOL_N"] = len(zb0)
V["ZB_SEALED_N"] = sum(1 for z in zb0 if z["p"] >= z["ztp"])
V["ZB_ZERO_SEQ"] = 8

ts = S["timeslot"]
tm = ts["today"]
ty = ts["yesterday"]
PM = tm.get("午后盘中", 0) + tm.get("尾盘", 0)
AM = tm.get("竞价/秒板", 0) + tm.get("开盘半小时", 0) + tm.get("上午盘中", 0)
PM_Y = ty.get("午后盘中", 0) + ty.get("尾盘", 0)
AM_Y = ty.get("竞价/秒板", 0) + ty.get("开盘半小时", 0) + ty.get("上午盘中", 0)
V.update({"TS_PM": PM, "TS_PM_PCT": f"{PM / ZT * 100:.1f}", "TS_AM": AM, "TS_AM_Y": AM_Y, "TS_PM_Y": PM_Y})

_order = [("竞价/秒板", "竞价/秒板"), ("开盘半小时", "开盘半小时"), ("上午盘中", "上午盘中"), ("午后盘中", "午后盘中"), ("尾盘", "尾盘")]
_t = []
for k, lbl in _order:
    a, b = tm.get(k, 0), ty.get(k, 0)
    d = a - b
    _t.append("<tr><td>%s</td><td class='hl'>%d</td><td>%d</td><td class='%s'>%+d</td></tr>" % (
        lbl, a, b, "up" if d > 0 else ("down" if d < 0 else "mut"), d))
V["TBL_TS"] = "\n".join(_t)

type0 = {}
for x in A0["ths_zt"]["info"]:
    type0[x.get("limit_up_type") or "?"] = type0.get(x.get("limit_up_type") or "?", 0) + 1
type1 = {}
for x in A1["ths_zt"]["info"]:
    type1[x.get("limit_up_type") or "?"] = type1.get(x.get("limit_up_type") or "?", 0) + 1
YIZI, YIZI_Y = type0.get("一字板", 0), type1.get("一字板", 0)
HS_ = type0.get("换手板", 0)
CYB = [x for x in zt0 if x["c"].startswith(("300", "301", "688", "689"))]
V.update({"YIZI": YIZI, "YIZI_Y": YIZI_Y, "JINGJIA": tm.get("竞价/秒板", 0),
          "HUANSHOU": HS_, "HUANSHOU_PCT": f"{HS_ / ZT * 100:.0f}",
          "CYB_N": len(CYB), "CYB_PCT": f"{len(CYB) / ZT * 100:.0f}"})

# ================= 主线：机器人链 =================
KW = ["机器人", "具身智能", "物理AI", "灵巧手", "机器视觉"]
rob = [x for x in zt0 if any(k in ((ths0.get(x["c"]) or {}).get("reason_type") or "") for k in KW)]
rob_hy = {}
for x in rob:
    rob_hy[x["hybk"]] = rob_hy.get(x["hybk"], 0) + 1
_rtop = sorted(rob_hy.items(), key=lambda kv: (-kv[1], kv[0]))
V.update({
    "ROBOT_N": len(rob), "ROBOT_SHARE": f"{len(rob) / ZT * 100:.1f}",
    "ROBOT_LB": sum(1 for x in rob if x["lbc"] >= 2),
    "ROBOT_AMT": f"{sum(x['amount'] for x in rob) / 1e8:.1f}",
    "ROBOT_AMT_SHARE": f"{sum(x['amount'] for x in rob) / sum(x['amount'] for x in zt0) * 100:.1f}",
    "ROBOT_FUND": f"{sum(x['fund'] for x in rob) / 1e8:.2f}",
    "ROBOT_FUND_SHARE": f"{sum(x['fund'] for x in rob) / sum(x['fund'] for x in zt0) * 100:.1f}",
    "ROBOT_HY_N": len(rob_hy),
    "ROBOT_HY_TOP1": f"{_rtop[0][1]}", "ROBOT_HY_TOP2": f"{_rtop[1][1]}", "ROBOT_HY_TOP3": f"{_rtop[2][1]}",
})
_t = []
for x in sorted(rob, key=lambda z: -z["amount"]):
    _t.append("<tr><td>%s</td><td>%s</td><td>%.1f</td><td class='up'>%d</td><td class='note'>%s</td></tr>" % (
        x["n"], x["hybk"], x["amount"] / 1e8, x["lbc"], (ths0.get(x["c"]) or {}).get("reason_type") or ""))
V["TBL_ROBOT"] = "\n".join(_t)

blk = sorted(A0["ths_block"], key=lambda x: -(x["limit_up_num"] or 0))[:12]
_bt = []
for b in blk:
    r = b["continuous_plate_num"] / b["limit_up_num"] * 100 if b["limit_up_num"] else 0
    _bt.append("<tr><td>%s</td><td class='hl'>%d</td><td>%d</td><td>%.1f%%</td></tr>" % (
        b["name"], b["limit_up_num"], b["continuous_plate_num"], r))
V["TBL_CONC"] = "\n".join(_bt)
_bd = {b["name"]: b for b in A0["ths_block"]}
_cr = _bd.get("机器人概念") or {}
_ch = _bd.get("人形机器人") or {}
V.update({
    "CONC_ROBOT_N": _cr.get("limit_up_num", 0), "CONC_ROBOT_LB": _cr.get("continuous_plate_num", 0),
    "CONC_ROBOT_R": f"{_cr.get('continuous_plate_num', 0) / max(1, _cr.get('limit_up_num', 1)) * 100:.1f}",
    "CONC_HUM_N": _ch.get("limit_up_num", 0), "CONC_HUM_LB": _ch.get("continuous_plate_num", 0),
    "CONC_HUM_R": f"{_ch.get('continuous_plate_num', 0) / max(1, _ch.get('limit_up_num', 1)) * 100:.1f}",
})
JS_CONC = {"names": [b["name"] for b in blk][::-1],
           "num": [b["limit_up_num"] for b in blk][::-1],
           "lb": [b["continuous_plate_num"] for b in blk][::-1]}

# 行业迁移
hy0, hy1 = S["hy0"], S["hy1"]
allh = set(hy0) | set(hy1)
hrows = [(h, hy0.get(h, 0), hy1.get(h, 0)) for h in allh]
hrows.sort(key=lambda r: -((r[1] + r[2]) + abs(r[1] - r[2]) * 2))
_hs = hrows[:16][::-1]
V["ZT_HY_N"], V["ZT_HY_Y"] = len(hy0), len(hy1)
V["HY_NEW_N"] = sum(1 for r in hrows if r[2] == 0 and r[1] > 0)
V["HY_ZERO_N"] = sum(1 for r in hrows if r[1] == 0 and r[2] > 0)
JS_HY = {"names": [r[0] for r in _hs], "vals": [r[1] - r[2] for r in _hs]}
_t = []
for r in _hs[::-1]:
    d = r[1] - r[2]
    _t.append("<tr><td>%s</td><td>%d</td><td>%d</td><td class='%s'>%+d</td></tr>" % (
        r[0], r[2], r[1], "up" if d > 0 else ("down" if d < 0 else "mut"), d))
V["TBL_HY"] = "\n".join(_t)
for h, k in [("IT服务Ⅱ", "HY_IT"), ("软件开发", "HY_RJ"), ("自动化设", "HY_ZDH"), ("专用设备", "HY_ZY"),
             ("汽车零部", "HY_QC"), ("半导体", "HY_BDT"), ("电池", "HY_DC"), ("电机Ⅱ", "HY_DJ")]:
    V[k] = hy1.get(h, 0)
    V[k + "0"] = hy0.get(h, 0)
V["MJ"] = hy0.get("电机Ⅱ", 0)

# ================= 昨日涨停股今日表现 =================
adv = [p for p in perf if p["again"]]
V.update({"ADV_N": len(adv), "ADV_TOT": len(perf), "ADV_RATE": f"{len(adv) / len(perf) * 100:.1f}",
          "PERF_MED": f2(median([p["pct"] for p in perf])),
          "PERF_UP_N": sum(1 for p in perf if p["pct"] > 0), "PERF_DN_N": sum(1 for p in perf if p["pct"] < 0),
          "NEW_FACE": ZT - len(adv), "NEW_FACE_PCT": f"{(ZT - len(adv)) / ZT * 100:.0f}"})

sb = [p for p in perf if p["lbc"] == 1]
lb = [p for p in perf if p["lbc"] >= 2]
SB_M, LB_M = median([p["pct"] for p in sb]), median([p["pct"] for p in lb])
GAP = SB_M - LB_M
V.update({"GAP_S_M": f2(SB_M), "GAP_L_M": f2(LB_M), "GAP": f"{GAP:.2f}",
          "SB_MEAN": f2(mean([p["pct"] for p in sb])), "LB_MEAN": f2(mean([p["pct"] for p in lb])),
          "LB_SB": sum(1 for p in lb if p["pct"] < 0),
          "GAP_PREV": "12.32", "GAP_PREV_DATE": "10-08 为 12.32pct；昨日 10-22 为 3.98pct"})
_t = []
for nm, g in [("全部", perf), ("昨日首板", sb), ("昨日连板", lb)]:
    vs = [p["pct"] for p in g]
    _t.append("<tr><td>%s</td><td>%d</td><td>%d（%.0f%%）</td><td class='%s'>%s</td><td class='hl'>%s</td><td>%d</td></tr>" % (
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
          "DT_POOL_N": len(dt0), "DT_YD_N": len(dt1),
          "DT_HY_N": len({x.get("hybk") for x in dt0}),
          "DT_AMT_YD_SHARE": f"{DT_AMT_Y / TOT_Y * 100:.2f}"})
_diff = len(dt0) - DT
V["DT_DIFF_TXT"] = f"差额 {abs(_diff)} 只不可归因，东财池全为沪深代码" if _diff else "两源一致"
_t = []
for x in sorted(dt0, key=lambda z: -(z.get("amount") or 0)):
    _t.append("<tr><td>%s</td><td>%s</td><td class='down'>%.2f%%</td><td>%.2f</td><td>%.0f</td></tr>" % (
        x["n"], x.get("hybk"), x.get("zdp") or 0, (x.get("amount") or 0) / 1e8, (x.get("ltsz") or 0) / 1e8))
V["TBL_DT_TD"] = "\n".join(_t)
_dtop = max(dt0, key=lambda z: z.get("amount") or 0) if dt0 else {}
V["DT_TOP_LTSZ"] = f"{(_dtop.get('ltsz') or 0) / 1e8:.0f}"
V["DT_TOP_AMT"] = f"{(_dtop.get('amount') or 0) / 1e8:.2f}"

# 昨日跌停池今日表现
QP = os.path.join(OUT, f"_qdt{D1[4:]}.json")
if os.path.exists(QP):
    Q = json.load(open(QP, encoding="utf-8"))
else:
    Q = {}
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

ztc = {x["code"] for x in A0["ths_zt"]["info"]}
dt1c = [x["c"] for x in dt1]
inter = sorted(ztc & set(dt1c))
vals = [Q[c]["pct"] for c in dt1c if c in Q]
V.update({
    "REL_MEAN": f2(mean(vals)), "REL_MED": f2(median(vals)),
    "REL_UP": sum(1 for v in vals if v > 0), "REL_UP_PCT": f"{sum(1 for v in vals if v > 0) / len(vals) * 100:.0f}",
    "REL_DT": sum(1 for v in vals if v <= -9.8),
    "REL_DT_NAMES": "、".join(f"{Q[c]['name']} {Q[c]['pct']:.2f}%" for c in dt1c if c in Q and Q[c]["pct"] <= -9.8) or "无",
    "REL_BIG": sum(1 for v in vals if v > 5),
    "REL_AMT": f"{sum(Q[c]['amount'] for c in dt1c if c in Q):.1f}",
    "INTER_N": len(inter), "INTER_SEQ": 2,
    "INTER_NAMES": "、".join(Q[c]["name"] if c in Q else c for c in inter) if inter else "一只都没有",
})
_hy = {}
for x in dt1:
    _hy[x.get("hybk")] = _hy.get(x.get("hybk"), 0) + 1
V["REL_HY_TXT"] = "、".join(f"{k} {v} 只" for k, v in sorted(_hy.items(), key=lambda kv: (-kv[1], kv[0]))[:8])

_bins = [(-100, -9.8, "跌停"), (-9.8, -5, "跌5~停"), (-5, -2, "跌2~5"), (-2, 0, "跌0~2"),
         (0, 2, "涨0~2"), (2, 5, "涨2~5"), (5, 9.8, "涨5~停"), (9.8, 100, "涨停")]
JS_REL = {"labels": [b[2] for b in _bins], "vals": [], "colors": []}
for lo, hi, lbl in _bins:
    n = sum(1 for v in vals if v <= -9.8) if lbl == "跌停" else sum(1 for v in vals if lo < v <= hi)
    JS_REL["vals"].append(n)
    JS_REL["colors"].append("down" if hi <= 0 else "up")

# ================= 北交所差额 =================
V.update({"EM_ZT_N": len(zt0_all), "EM_DIFF_N": len(zt0_all) - ZT,
          "EM_DIFF_CODES": "、".join(sorted({x["c"] for x in zt0_all} - {x["c"] for x in zt0})) or "无"})

# ================= JS =================
JS_SENTI = {"days": [x["d"] for x in days], "zt": [x["zt"] for x in days],
            "dt": [x["dt"] for x in days], "seal": [round(x["seal"], 1) for x in days]}
JS_INTRA = {"names": [x["nm"] for x in INTRA], "gap": [round(x["gap"], 2) for x in INTRA],
            "low": [round(x["low"], 2) for x in INTRA], "close": [round(x["close"], 2) for x in INTRA]}
JS_AMT = {"names": [x["name"] for x in ix], "yoy": [None if x["yoy"] is None else round(x["yoy"], 1) for x in ix]}
JS_TS = {"labels": [k for k, _ in _order], "today": [tm.get(k, 0) for k, _ in _order],
         "prev": [ty.get(k, 0) for k, _ in _order]}
for k, v in [("JS_SENTI", JS_SENTI), ("JS_INTRA", JS_INTRA), ("JS_AMT", JS_AMT), ("JS_LAD", JS_LAD),
             ("JS_CONC", JS_CONC), ("JS_HY", JS_HY), ("JS_PF", JS_PF), ("JS_REL", JS_REL),
             ("JS_TS", JS_TS), ("JS_FUND", JS_FUND)]:
    V[k] = json.dumps(v, ensure_ascii=False)
V["GEN_TIME"] = time.strftime("%Y-%m-%d %H:%M")

# ================= 渲染 =================
tpl = open(TPL, encoding="utf-8").read()
out = tpl
for k, v in V.items():
    out = out.replace("__" + k + "__", str(v))
res = sorted(set(re.findall(r"__[A-Z_0-9]+__", out)))
print("placeholder residue:", res)
if res:
    raise SystemExit("残留占位符，终止")
rp = os.path.join(REP, f"涨停复盘对比-{D0}.html")
open(rp, "w", encoding="utf-8").write(out)
print("saved ->", rp, len(out), "bytes")
