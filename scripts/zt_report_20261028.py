# -*- coding: utf-8 -*-
"""涨停复盘报告 20261028 vs 20261027（放量扩散型修复 · 参与度爆表 / 承接力史上最差）
用法：python scripts/zt_report_20261028.py 20261028
输入：out/zt_stats_20261028.json、out/zt_review_20261028.json、out/zt_review_20261027.json、out/zt_stats_20261027.json
     跌停明细 out/_dt1028.json / out/_dt1027.json；昨跌停股今日行情 out/_qdt1027.json
输出：reports/涨停复盘对比-20261028.html
"""
import json, os, sys, html, re, urllib.request, time
from statistics import mean, median

ROOT = os.environ.get("ZT_ROOT") or os.getcwd()
OUT = os.path.join(ROOT, "out")
REP = os.path.join(ROOT, "reports")
TPL = os.path.join(ROOT, "scripts", "_report_tpl_20261028.html")
os.makedirs(REP, exist_ok=True)

D0 = sys.argv[1] if len(sys.argv) > 1 else "20261028"
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
V["NEXT_D"] = "10/29 周四"


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
DT, DT_Y = _dc0["num"], _dc1["num"]
DTOUCH, DTOUCH_Y = _dc0["history_num"], _dc1["history_num"]
DSEAL, DSEAL_Y = _dc0["rate"] * 100, _dc1["rate"] * 100
DT_OPEN_N = DTOUCH - DT

V.update({
    "ZT": ZT, "ZT_Y": ZT_Y, "ZT_D": f"{ZT - ZT_Y:+d}", "ZT_PCT_D": f"{abs((ZT / ZT_Y - 1) * 100):.0f}",
    "TOUCH": TOUCH, "TOUCH_Y": TOUCH_Y, "TOUCH_D": f"{TOUCH - TOUCH_Y:+d}",
    "TOUCH_PCT": f"{abs((TOUCH / TOUCH_Y - 1) * 100):.0f}",
    "SEAL": f"{SEAL:.1f}", "SEAL_Y": f"{SEAL_Y:.1f}", "SEAL_D": f"{SEAL - SEAL_Y:+.1f}",
    "SEAL_D_ABS": f"{abs(SEAL - SEAL_Y):.1f}",
    "SEAL_FAIL": f"{(1 - ZT / TOUCH) * 100:.1f}", "SEAL_FAIL_Y": f"{(1 - ZT_Y / TOUCH_Y) * 100:.1f}",
    "DT": DT, "DT_Y": DT_Y, "DT_D": f"{DT - DT_Y:+d}", "DT_X": f"{DT / DT_Y:.1f}",
    "DTOUCH": DTOUCH, "DTOUCH_Y": DTOUCH_Y,
    "DSEAL": f"{DSEAL:.1f}", "DSEAL_Y": f"{DSEAL_Y:.1f}",
    "DT_OPEN_N": DT_OPEN_N, "DT_REBUY": f"{DT_OPEN_N / DTOUCH * 100:.1f}",
    "ZB": ZB, "ZB_Y": ZB_Y, "ZB_D": f"{ZB - ZB_Y:+d}",
})

# 三日阶梯（D2 列取 D1 文件自带的 yesterday）
days = [
    {"d": md(D2), "zt": s1["zt_prev"], "zb": s1["zb_prev"], "dt": s1["dt_prev"],
     "touch": s1["yest"].get("history_num", 0),
     "dtouch": A1["ths_zt"]["limit_down_count"]["yesterday"]["history_num"]},
    {"d": md(D1), "zt": s1["zt"], "zb": s1["zb"], "dt": s1["dt"],
     "touch": TOUCH_Y, "dtouch": DTOUCH_Y},
    {"d": md(D0), "zt": s0["zt"], "zb": s0["zb"], "dt": s0["dt"],
     "touch": TOUCH, "dtouch": DTOUCH},
]
for x in days:
    x["seal"] = x["zt"] / x["touch"] * 100 if x["touch"] else 0.0
assert days[0]["dtouch"] != days[1]["dtouch"], "D2 列触及跌停与 D1 相同，取错文件"
assert days[0]["zt"] != days[1]["zt"], "D2 列涨停与 D1 相同，取错文件"

V["ZTDT"] = f"{ZT / DT:.1f}"
V["ZTDT_Y"] = f"{ZT_Y / DT_Y:.1f}"
V["ZTDT_0"] = f"{days[0]['zt'] / days[0]['dt']:.1f}" if days[0]["dt"] else "—"
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
V["AMT_UP_N"] = sum(1 for x in ix if (x["yoy"] or 0) > 0)
V["AMT_DN_N"] = sum(1 for x in ix if (x["yoy"] or 0) < 0)
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
V["TOUCH_GAP"] = TOUCH - ZT

for key, nm in [("SH", "上证指数"), ("CY", "创业板指"), ("KC", "科创50"), ("GZ", "国证2000")]:
    x = next((y for y in INTRA if y["nm"] == nm), None)
    if x:
        V[key + "_GAP"] = f2(x["gap"])
        V[key + "_LOW"] = f2(x["low"])
        V[key + "_PCT"] = f2(x["close"])
        V[key + "_REB"] = f"{x['reb']:.2f}"
        V[key + "_DRAW"] = f"{x['draw']:.2f}"
for key, nm in [("SH50", "上证50"), ("CY", "创业板指"), ("KC", "科创50"), ("GZ", "国证2000")]:
    x = next((y for y in INTRA if y["nm"] == nm), None)
    if x:
        V[key + "_GAP"] = f2(x["gap"])
        V[key + "_LOW"] = f2(x["low"])
        V[key + "_PCT"] = f2(x["close"])
    r = next((y for y in ix if y["name"] == nm), None)
    if r:
        V[key + "_AMT"] = f"{r['amt']:.0f}"
        V[key + "_YOY"] = f1(r["yoy"] or 0)
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

# 行业指数（风格佐证）
SEC = {}
try:
    _op2 = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    raw = _op2.open("https://qt.gtimg.cn/q=sz399975,sz399986,sz399997,sz399808", timeout=20).read().decode("gbk", errors="ignore")
    for line in raw.split(";"):
        if "=" not in line:
            continue
        fs = line.split("=", 1)[1].strip().strip('"').split("~")
        if len(fs) < 40:
            continue
        SEC[fs[1]] = float(fs[32] or 0)
except Exception as e:
    print("warn: 行业指数抓取失败", e)
V["SEC_PCT"] = f2(SEC.get("证券公司", 0))
V["BANK_PCT"] = f2(SEC.get("中证银行", 0))
V["BJ_PCT"] = f2(SEC.get("中证白酒", 0))
V["NEWE_PCT"] = f2(SEC.get("中证新能", 0))

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
V["LAD4Y_ALL_BRK"] = "是" if all(not p["again"] for p in by.get(4, [])) else "否"

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

V["FUND_GE_N"] = sum(1 for x in zt0 if x["fund"] >= 1e8)
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

ts, tm, ty = S["timeslot"], S["timeslot"]["today"], S["timeslot"]["yesterday"]
PM = tm.get("午后盘中", 0) + tm.get("尾盘", 0)
AM = tm.get("竞价/秒板", 0) + tm.get("开盘半小时", 0) + tm.get("上午盘中", 0)
PM_Y = ty.get("午后盘中", 0) + ty.get("尾盘", 0)
AM_Y = ty.get("竞价/秒板", 0) + ty.get("开盘半小时", 0) + ty.get("上午盘中", 0)
V.update({"TS_PM": PM, "TS_PM_PCT": f"{PM / ZT * 100:.1f}", "TS_AM": AM, "TS_AM_PCT": f"{AM / ZT * 100:.1f}",
          "TS_AM_Y": AM_Y, "TS_PM_Y": PM_Y, "TS_AM_PCT_Y": f"{AM_Y / ZT_Y * 100:.1f}",
          "TS_PM_PCT_Y": f"{PM_Y / ZT_Y * 100:.1f}"})

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
          "HUANSHOU": HS_, "HUANSHOU_PCT": f"{HS_ / ZT * 100:.0f}",
          "CYB_N": len(CYB), "CYB_PCT": f"{len(CYB) / ZT * 100:.0f}"})

# ================= 主线：机器人链 =================
KW = ["机器人", "具身", "人形", "灵巧手", "减速器", "丝杠", "关节", "机器视觉"]
rob = [x for x in zt0 if any(k in ((ths0.get(x["c"]) or {}).get("reason_type") or "") for k in KW)]
rob1 = [x for x in zt1 if any(k in ((ths1.get(x["c"]) or {}).get("reason_type") or "") for k in KW)]
rob_hy = {}
for x in rob:
    rob_hy[x["hybk"]] = rob_hy.get(x["hybk"], 0) + 1
_rtop = sorted(rob_hy.items(), key=lambda kv: (-kv[1], kv[0]))
_rob_amt = sum(x["amount"] for x in rob)
_rob_fund = sum(x["fund"] for x in rob)
_all_amt = sum(x["amount"] for x in zt0)
_all_fund = sum(x["fund"] for x in zt0)
_rob1_amt = sum(x["amount"] for x in rob1)
_all1_amt = sum(x["amount"] for x in zt1)
V.update({
    "ROBOT_N": len(rob), "ROBOT_SHARE": f"{len(rob) / ZT * 100:.1f}",
    "ROBOT_LB": sum(1 for x in rob if x["lbc"] >= 2),
    "ROBOT_AMT": f"{_rob_amt / 1e8:.1f}", "ROBOT_AMT_SHARE": f"{_rob_amt / _all_amt * 100:.1f}",
    "ROBOT_FUND": f"{_rob_fund / 1e8:.2f}", "ROBOT_FUND_SHARE": f"{_rob_fund / _all_fund * 100:.1f}",
    "ROBOT_HY_N": len(rob_hy),
    "ROBOT_HY_TOP1": f"{_rtop[0][0]} {_rtop[0][1]}",
    "ROBOT_HY_TOP2": f"{_rtop[1][0]} {_rtop[1][1]}",
    "ROBOT_HY_TOP3": f"{_rtop[2][0]} {_rtop[2][1]}",
    "ROBOT_N_Y": len(rob1), "ROBOT_LB_Y": sum(1 for x in rob1 if x["lbc"] >= 2),
    "ROBOT_HY_N_Y": len({x["hybk"] for x in rob1}),
    "ROBOT_AMT_Y": f"{_rob1_amt / 1e8:.1f}",
    "ROBOT_AMT_SHARE_Y": f"{_rob1_amt / _all1_amt * 100:.1f}",
    "ROBOT_GROW": f"{abs((len(rob) / len(rob1) - 1) * 100):.0f}",
})
_lb_rob = sum(1 for x in zt0 if x["lbc"] >= 2 and x in rob)
V["ROBOT_LB_PCT"] = f"{_lb_rob / LB * 100:.0f}"
V["ROBOT_LB_IN"] = _lb_rob
V["ROBOT_LB_NAMES"] = "、".join(f"{x['n']}({x['lbc']}板)" for x in rob if x["lbc"] >= 2) or "无"
_dict1 = {x["c"] for x in rob1}
V["ROBOT_NEW_N"] = len([x for x in rob if x["c"] not in _dict1])
V["ROBOT_NEW_PCT"] = f"{len([x for x in rob if x['c'] not in _dict1]) / len(rob) * 100:.0f}"
_t = []
for x in sorted(rob, key=lambda z: -z["amount"]):
    _t.append("<tr><td>%s</td><td>%s</td><td>%.1f</td><td class='up'>%d</td><td class='note'>%s</td></tr>" % (
        x["n"], x["hybk"], x["amount"] / 1e8, x["lbc"], (ths0.get(x["c"]) or {}).get("reason_type") or ""))
V["TBL_ROBOT"] = "\n".join(_t)

# PCB / 覆铜板 / 元件链
PKW = ["PCB", "覆铜板", "MLCC", "离型膜", "线路板", "电子级", "铜箔", "覆膜"]
pcb = [x for x in zt0 if any(k in ((ths0.get(x["c"]) or {}).get("reason_type") or "") for k in PKW)]
pcb1 = [x for x in zt1 if any(k in ((ths1.get(x["c"]) or {}).get("reason_type") or "") for k in PKW)]
_pcb_amt = sum(x["amount"] for x in pcb)
V.update({"PCB_N": len(pcb), "PCB_LB": sum(1 for x in pcb if x["lbc"] >= 2),
          "PCB_AMT": f"{_pcb_amt / 1e8:.1f}", "PCB_AMT_SHARE": f"{_pcb_amt / _all_amt * 100:.1f}",
          "PCB_HY_N": len({x["hybk"] for x in pcb}), "PCB_N_Y": len(pcb1),
          "PCB_NAMES": "、".join(f"{x['n']}（{x['amount'] / 1e8:.1f} 亿）" for x in sorted(pcb, key=lambda z: -z["amount"]))})

# 三季报（催化层，非链条）
sjb = [x for x in zt0 if "三季" in ((ths0.get(x["c"]) or {}).get("reason_type") or "")]
V.update({"SJB_N": len(sjb), "SJB_LB": sum(1 for x in sjb if x["lbc"] >= 2),
          "SJB_AMT_SHARE": f"{sum(x['amount'] for x in sjb) / _all_amt * 100:.1f}",
          "SJB_HY_N": len({x["hybk"] for x in sjb}),
          "SJB_SHARE": f"{len(sjb) / ZT * 100:.1f}"})

blk = sorted(A0["ths_block"], key=lambda x: -(x["limit_up_num"] or 0))[:12]
_bt = []
for b in blk:
    r = b["continuous_plate_num"] / b["limit_up_num"] * 100 if b["limit_up_num"] else 0
    _bt.append("<tr><td>%s</td><td class='hl'>%d</td><td>%d</td><td>%.1f%%</td></tr>" % (
        b["name"], b["limit_up_num"], b["continuous_plate_num"], r))
V["TBL_CONC"] = "\n".join(_bt)
_bd = {b["name"]: b for b in A0["ths_block"]}
_bd1 = {b["name"]: b for b in A1["ths_block"]}
_cr, _ch = _bd.get("机器人概念") or {}, _bd.get("人形机器人") or {}
_cr1 = _bd1.get("机器人概念") or {}
_ch1 = _bd1.get("人形机器人") or {}
V.update({
    "CONC_ROBOT_N": _cr.get("limit_up_num", 0), "CONC_ROBOT_LB": _cr.get("continuous_plate_num", 0),
    "CONC_ROBOT_R": f"{_cr.get('continuous_plate_num', 0) / max(1, _cr.get('limit_up_num', 1)) * 100:.1f}",
    "CONC_ROBOT_N_Y": _cr1.get("limit_up_num", 0), "CONC_ROBOT_LB_Y": _cr1.get("continuous_plate_num", 0),
    "CONC_ROBOT_R_Y": f"{_cr1.get('continuous_plate_num', 0) / max(1, _cr1.get('limit_up_num', 1)) * 100:.1f}",
    "CONC_HUM_N": _ch.get("limit_up_num", 0), "CONC_HUM_LB": _ch.get("continuous_plate_num", 0),
    "CONC_HUM_R": f"{_ch.get('continuous_plate_num', 0) / max(1, _ch.get('limit_up_num', 1)) * 100:.1f}",
    "CONC_HUM_N_Y": _ch1.get("limit_up_num", 0), "CONC_HUM_LB_Y": _ch1.get("continuous_plate_num", 0),
    "CONC_HUM_R_Y": f"{_ch1.get('continuous_plate_num', 0) / max(1, _ch1.get('limit_up_num', 1)) * 100:.1f}",
    "CONC_TOP1": blk[0]["name"], "CONC_TOP1_R": f"{blk[0]['continuous_plate_num'] / max(1, blk[0]['limit_up_num']) * 100:.1f}",
})
JS_CONC = {"names": [b["name"] for b in blk][::-1],
           "num": [b["limit_up_num"] for b in blk][::-1],
           "lb": [b["continuous_plate_num"] for b in blk][::-1]}

# 行业迁移
hy0, hy1 = S["hy0"], S["hy1"]
allh = set(hy0) | set(hy1)
hrows = [(h, hy0.get(h, 0), hy1.get(h, 0)) for h in allh]
hrows.sort(key=lambda r: -((r[1] + r[2]) + abs(r[1] - r[2]) * 2))
_hs = hrows[:14][::-1]
V["ZT_HY_N"], V["ZT_HY_Y"] = len(hy0), len(hy1)
V["HY_NEW_N"] = sum(1 for r in hrows if r[2] == 0 and r[1] > 0)
V["HY_ZERO_N"] = sum(1 for r in hrows if r[1] == 0 and r[2] > 0)
V["HY_ZERO_LIST"] = "、".join(f"{r[0]} {r[2]}" for r in sorted([r for r in hrows if r[1] == 0 and r[2] > 0], key=lambda z: (-z[2], z[0]))[:8])
JS_HY = {"names": [r[0] for r in _hs], "vals": [r[1] - r[2] for r in _hs]}
_t = []
for r in _hs[::-1]:
    d = r[1] - r[2]
    _t.append("<tr><td>%s</td><td>%d</td><td>%d</td><td class='%s'>%+d</td></tr>" % (
        r[0], r[2], r[1], "up" if d > 0 else ("down" if d < 0 else "mut"), d))
V["TBL_HY"] = "\n".join(_t)
for h, k in [("通用设备", "HY_TY"), ("专用设备", "HY_ZY"), ("汽车零部", "HY_QC"), ("元件", "HY_YJ"),
             ("半导体", "HY_BDT"), ("电机Ⅱ", "HY_DJ"), ("一般零售", "HY_LS"), ("通信设备", "HY_TX"),
             ("影视院线", "HY_YS"), ("化学制品", "HY_HX"), ("自动化设", "HY_ZDH"), ("小家电", "HY_XJD"),
             ("消费电子", "HY_XFD"), ("生物制品", "HY_SW"), ("家居用品", "HY_JJ")]:
    V[k] = hy1.get(h, 0)
    V[k + "0"] = hy0.get(h, 0)

# ================= 昨日涨停股今日表现 =================
adv = [p for p in perf if p["again"]]
V.update({"ADV_N": len(adv), "ADV_TOT": len(perf), "ADV_RATE": f"{len(adv) / len(perf) * 100:.1f}",
          "PERF_MED": f2(median([p["pct"] for p in perf])),
          "PERF_MEAN": f2(mean([p["pct"] for p in perf])),
          "PERF_UP_N": sum(1 for p in perf if p["pct"] > 0), "PERF_DN_N": sum(1 for p in perf if p["pct"] < 0),
          "NEW_FACE": ZT - len(adv), "NEW_FACE_PCT": f"{(ZT - len(adv)) / ZT * 100:.0f}"})

sb = [p for p in perf if p["lbc"] == 1]
lb = [p for p in perf if p["lbc"] >= 2]
SB_M, LB_M = median([p["pct"] for p in sb]), median([p["pct"] for p in lb])
GAP = SB_M - LB_M
_sb1 = [p for p in S1["perf"] if p["lbc"] == 1]
_lb1 = [p for p in S1["perf"] if p["lbc"] >= 2]
GAP_Y = median([p["pct"] for p in _sb1]) - median([p["pct"] for p in _lb1])
V.update({"GAP_S_M": f2(SB_M), "GAP_L_M": f2(LB_M), "GAP": f"{GAP:+.2f}",
          "SB_MEAN": f2(mean([p["pct"] for p in sb])), "LB_MEAN": f2(mean([p["pct"] for p in lb])),
          "LB_SB": sum(1 for p in lb if p["pct"] < 0),
          "GAP_Y": f"{GAP_Y:+.2f}", "GAP_SWING": f"{abs(GAP - GAP_Y):.2f}",
          "GAP_SIGN": "连板强" if GAP < 0 else "首板强",
          "GAP_SIGN_Y": "连板强" if GAP_Y < 0 else "首板强",
          "GAP_S_M_Y": f2(median([p['pct'] for p in _sb1])), "GAP_L_M_Y": f2(median([p['pct'] for p in _lb1]))})
assert len(_sb1) + len(_lb1) == len(S1["perf"]), "昨日分组计数不闭合"

_t = []
for nm, g in [("全部", perf), ("昨日首板", sb), ("昨日连板", lb)]:
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
          "DT_POOL_N": len(dt0), "DT_YD_N": len(dt1), "DT_X_AMT": f"{DT_AMT / DT_AMT_Y:.2f}",
          "DT_HY_N": len({x.get("hybk") for x in dt0}),
          "DT_AMT_YD_SHARE": f"{DT_AMT_Y / TOT_Y * 100:.2f}",
          "DT_BIG_N": sum(1 for x in dt0 if (x.get("ltsz") or 0) > 100e8)})
_diff = len(dt0) - DT
V["DT_DIFF_TXT"] = (f"东财池比同花顺汇总多 {_diff} 只、均为沪深代码、不可逐只归因" if _diff else "两源一致")
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
V["DT_NAMES_ALL"] = "、".join(f"{x['n']}（{x.get('hybk')}，{x.get('zdp') or 0:.2f}%，成交 {(x.get('amount') or 0) / 1e8:.1f} 亿）" for x in sorted(dt0, key=lambda z: -(z.get("amount") or 0)))

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

dt1c = [x["c"] for x in dt1]
inter = sorted({x["code"] for x in A0["ths_zt"]["info"]} & set(dt1c))
vals = [Q[c]["pct"] for c in dt1c if c in Q]
_ex = [Q[c]["pct"] for c in dt1c if c in Q and c != "002731"]
V.update({
    "REL_MEAN": f2(mean(vals)), "REL_MED": f2(median(vals)),
    "REL_MEAN_EX": f2(mean(_ex)), "REL_MED_EX": f2(median(_ex)),
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
_dtset = {x["c"] for x in dt0}
_att = [p for p in perf if p["code"] in _dtset]
V["ATK_DT_N"] = len(_att)
V["ATK_DT_NAMES"] = "、".join(f"{p['name']}（昨{p['lbc']}板，{p['hybk']}）" for p in _att) or "无"
# 连续跌停
_dts = {x["c"] for x in dt0} & {x["c"] for x in dt1}
V["DT_CONT_N"] = len(_dts)
V["DT_CONT_NAMES"] = "、".join(f"{Q[c]['name']}" for c in _dts if c in Q) or "无"

# ================= 口径披露 =================
_bj = [x for x in zt_all if x["c"].startswith("92")]
V["BJ_N"] = len(_bj)
V["BJ_CODES"] = "、".join(f"{x['n']}（{x['c']}）" for x in _bj) or "无"
_hy_only = [x for x in zt0_em if x["c"] not in ths0]
V["EM_ONLY_N"] = len(_hy_only)
V["EM_ONLY_TXT"] = "、".join(f"{x['n']}（{x['c']}，{x['zdp']:+.2f}%）" for x in _hy_only) or "无"
V["EM_ZT_N"] = len(zt0_em)
V["EM_DIFF_N"] = len(zt0_em) - ZT
DIFS = sorted({x["c"] for x in zt0_em} - {x["c"] for x in zt0})
V["EM_DIFF_CODES"] = "、".join(DIFS) or "无"
V["EM_DIFF_IS_BJ"] = "是" if DIFS and all(c.startswith("92") for c in DIFS) else "否"
# 断言：东财 tc 差额必须全部可解释（北交所 + 退市整理股 002731）
_all_diff = sorted({x["c"] for x in zt_all} - {x["c"] for x in zt0})
_bad = [c for c in _all_diff if not c.startswith("92") and c != "002731"]
assert not _bad, f"东财差额里出现无法归因的沪深代码：{_bad}"

# 华正新材（昨跌停 → 今表现），链内轮换的硬证据
HZZC = Q.get("603186", {})
V["HZZC_PCT"] = f2(HZZC.get("pct", 0))
V["HZZC_AMT"] = f"{HZZC.get('amount', 0):.2f}"
GANGYAN = Q.get("600316", {})
V["HDHK_PCT"] = f2(GANGYAN.get("pct", 0))
ZG = Q.get("002049", {})
V["ZG_PCT"] = f2(ZG.get("pct", 0))

# 炸板池里的机器人权重
_zb_rob = [z for z in zb0 if any(k in ((z.get("hybk") or "") + (z.get("n") or "")) for k in [])]
V["ZB_ROB_TXT"] = "、".join(
    f"{z['n']}（{z.get('hybk')}，流通 {(z.get('ltsz') or 0) / 1e8:.0f} 亿，收 {z['zdp']:+.2f}%）"
    for z in sorted([z for z in zb0 if z["n"] in ("双环传动", "兆威机电", "模塑科技", "东材科技")], key=lambda z: -(z.get("amount") or 0)))

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
for k, v in sorted(V.items(), key=lambda kv: -len(kv[0])):
    out = out.replace("__" + k + "__", str(v))
res = sorted(set(re.findall(r"__[A-Z_0-9]+__", out)))
print("placeholder residue:", res)
if res:
    raise SystemExit("残留占位符，终止")
rp = os.path.join(REP, f"涨停复盘对比-{D0}.html")
open(rp, "w", encoding="utf-8").write(out)
print("saved ->", rp, len(out), "bytes")
