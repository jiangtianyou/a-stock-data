# -*- coding: utf-8 -*-
"""涨停复盘报告 20261030 vs 20261029（K 型撕裂 · 业绩接棒 · 旧主线逐条点杀）
用法：python scripts/zt_report_20261030.py 20261030
输入：out/zt_stats_20261030.json、out/zt_review_20261030.json、out/zt_review_20261029.json、out/zt_stats_20261029.json
     跌停明细 out/_dt1030.json / out/_dt1029.json；昨跌停股今日行情 out/_qdt1029.json；watchlist 概念/行业榜 out/_sw1030.json
输出：reports/涨停复盘对比-20261030.html
"""
import json, os, sys, html, re, glob, urllib.request, time, subprocess
from statistics import mean, median

ROOT = os.environ.get("ZT_ROOT") or os.getcwd()
OUT = os.path.join(ROOT, "out")
REP = os.path.join(ROOT, "reports")
TPL = os.path.join(ROOT, "scripts", "_report_tpl_20261030.html")
os.makedirs(REP, exist_ok=True)

D0 = sys.argv[1] if len(sys.argv) > 1 else "20261030"
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


def f1(v):
    return f"{v:+.1f}"


def f2(v):
    return f"{v:+.2f}"


def hhmm(v):
    s = str(int(v)).zfill(6)
    return s[:2] + ":" + s[2:4]


V = {}
V["D0"], V["D1"], V["D2"] = md(D0), md(D1), md(D2)
V["NEXT_D"] = "下周一 11/2"


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

# 跌停池叙事分组（传媒/AI 内容 · 机器人/汽车零部件 · 算力硬件）
G_MEDIA = ("广告营销", "数字媒体", "游戏Ⅱ", "出版", "影视院线", "电视广播", "文娱用品")
G_ROBO = ("汽车零部", "通用设备", "家电零部", "电机Ⅱ", "专用设备", "自动化设", "工程机械", "仪器仪表")
G_CHIP = ("元件", "通信设备", "半导体", "消费电子", "光学光电", "其他电子", "电子化学品")

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
assert TOUCH >= ZT and TOUCH_Y >= ZT_Y, "触及涨停 < 涨停家数，字段错位"
assert DT <= DTOUCH, "跌停 > 触及跌停，字段错位"

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

# 历史封板率 / 涨停区间（用于风险提示）
_seals, _zts = [], [ZT]
for p in sorted(glob.glob(os.path.join(OUT, "zt_stats_2026*.json"))):
    try:
        _d = json.load(open(p, encoding="utf-8"))
        _k = _d["D0"]
        _s = _d["senti"][_k]
        _seals.append(_s["seal_rate"] * 100)
        _zts.append(_s["zt"])
    except Exception:
        continue
V["SEAL_MIN"] = f"{min(_seals):.1f}"
V["SEAL_MAX"] = f"{max(_seals):.1f}"

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
V["AMT_UP_N"] = sum(1 for x in ix if (x["yoy"] or 0) < 0)   # 缩量数
V["AMT_DN_N"] = sum(1 for x in ix if (x["yoy"] or 0) > 0)   # 放量数
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
    INTRA.append({"nm": nm, "gap": (o["open"] / o["prev"] - 1) * 100, "high": (o["high"] / o["prev"] - 1) * 100,
                  "low": (o["low"] / o["prev"] - 1) * 100, "close": (o["close"] / o["prev"] - 1) * 100,
                  "reb": (o["close"] / o["low"] - 1) * 100, "draw": (o["close"] / o["high"] - 1) * 100})
V["N_BELOW_OPEN"] = sum(1 for x in INTRA if x["close"] < x["gap"])
V["N_ABOVE_OPEN"] = len(INTRA) - V["N_BELOW_OPEN"]
V["N_INTRA"] = len(INTRA)
V["N_REBOUND"] = sum(1 for x in INTRA if x["reb"] > 0)
V["N_CLOSE_LOW"] = sum(1 for x in INTRA if abs(x["close"] - x["low"]) < 0.06)
V["N_TURN_GREEN"] = sum(1 for x in INTRA if x["high"] > 0)

for key, nm in [("SH", "上证指数"), ("CY", "创业板指"), ("KC", "科创50"),
                ("GZ", "国证2000"), ("SH50", "上证50")]:
    x = next((y for y in INTRA if y["nm"] == nm), None)
    if x:
        V[key + "_GAP"] = f2(x["gap"])
        V[key + "_HIGH"] = f2(x["high"])
        V[key + "_LOW"] = f2(x["low"])
        V[key + "_PCT"] = f2(x["close"])
        V[key + "_REB"] = f"{x['reb']:.2f}"
        V[key + "_DRAW"] = f"{x['draw']:.2f}"
# 成交额环比（分指数）
for key, nm in [("CY", "创业板指"), ("KC", "科创50"), ("SH50", "上证50"), ("HS300", "沪深300"),
                ("SZ", "深证成指"), ("BJ", "北证50"), ("ZX100", "中小100")]:
    r = next((y for y in ix if y["name"] == nm), None)
    if r:
        V[key + "_YOY"] = f1(r["yoy"] or 0)
        V[key + "_YOY_ABS"] = f"{abs(r['yoy'] or 0):.1f}"
        V[key + "_AMT"] = f"{r['amt']:.0f}"
for key, nm in [("HS300", "沪深300"), ("SH50", "上证50")]:
    V[key + "_PCT"] = f2((i0.get(nm) or {}).get("pct") or 0)
V["SH50_PCT_Y"] = f"{(i1.get('上证50') or {}).get('pct') or 0:+.2f}"

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
assert len(_maxb) >= 1, "最高板名单为空"
V["MAXB_NAMES"] = "、".join(x["n"] for x in _maxb)
_mb = _maxb[0]
V.update({"MAXB_NAME": _mb["n"], "MAXB_HY": _mb["hybk"], "MAXB_FUND": f"{_mb['fund'] / 1e8:.2f}",
          "MAXB_AMT": f"{_mb['amount'] / 1e8:.2f}", "MAXB_TURN": f"{_mb['hs']:.1f}",
          "MAXB_FBT": hhmm(_mb["fbt"]),
          "MAXB_TYPE": (ths0.get(_mb["c"]) or {}).get("limit_up_type") or "换手板",
          "MAXB_RT": (ths0.get(_mb["c"]) or {}).get("reason_type") or ""})
V["LB_HY_N"] = len({x["hybk"] for x in zt0 if x["lbc"] >= 2})

_t = []
for k in sorted(set(list(lad0.keys()) + list(lad1.keys()))):
    a, b = lad0.get(k, 0), lad1.get(k, 0)
    d = a - b
    _t.append("<tr><td>%s</td><td class='hl'>%d</td><td>%d</td><td class='%s'>%s</td></tr>" % (
        ("首板" if k == 1 else f"{k} 板"), a, b, "up" if d > 0 else ("down" if d < 0 else "mut"),
        f"{d:+d}" if d else "0"))
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
V["LAD_LB_DN_N"] = sum(1 for p in _lbv if p["pct"] < 0)
V["LAD_LB_DT_N"] = sum(1 for p in _lbv if p["pct"] <= -9.5)
V["LAD_SHOU_DN_N"] = sum(1 for p in _sb if p["pct"] < 0)
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
    "ZT_MED_LTSZ": f"{median([x['ltsz'] for x in zt0]) / 1e8:.0f}",
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

# 吸金密度连续低于 3% 的天数（自 D0 向前逐日重算，不引用历史报告文本）
_share_streak = 0
for p in sorted(glob.glob(os.path.join(OUT, "zt_stats_2026*.json")), reverse=True):
    try:
        _d = json.load(open(p, encoding="utf-8"))
        _k = _d["D0"]
        _rev = json.load(open(os.path.join(OUT, f"zt_review_{_k}.json"), encoding="utf-8"))
        _Ax = _rev["dates"][_k]
        _th = {x["code"]: x for x in _Ax["ths_zt"]["info"]}
        _z = [x for x in pool(_Ax, "em_ZT") if not x["c"].startswith("92") and x["c"] in _th]
        _tot = sum(v["amount_wan"] for v in _rev["indexes"].values()
                   if isinstance(v, dict) and v.get("name") in ("上证指数", "深证成指")) / 1e4
        _ratio = (sum(x["amount"] for x in _z) / 1e8) / _tot * 100 if _tot else 99
        if _ratio < 3:
            _share_streak += 1
        else:
            break
    except Exception:
        break
V["SHARE_LOW_STREAK"] = _share_streak

# ================= 炸板 / 封板时间 =================
sealed = [z for z in zb0 if z["p"] >= z["ztp"]]
V["ZB_POOL_N"] = len(zb0)
V["ZB_SEALED_N"] = len(sealed)
V["ZB_SEAL_PCT"] = f"{len(sealed) / len(zb0) * 100:.1f}" if zb0 else "—"
V["ZB_MED"] = f"{median([(z.get('amount') or 0) for z in zb0]) / 1e8:.2f}"
V["ZB_MED_Y"] = f"{median([(z.get('amount') or 0) for z in pool(A1, 'em_ZB')]) / 1e8:.2f}"
V["ZB_BIG_N"] = sum(1 for z in zb0 if (z.get("ltsz") or 0) > 100e8)
_zbs = sorted(zb0, key=lambda z: -(z.get("amount") or 0))[:3]
V["ZB_TOP_TXT"] = "、".join(f"{z['n']}（{z['hybk']}，流通 {(z.get('ltsz') or 0) / 1e8:.0f} 亿，成交 {(z.get('amount') or 0) / 1e8:.2f} 亿，收 {z['zdp']:+.2f}%）" for z in _zbs)
# 连续零回封天数
_streak = 0
for p in sorted(glob.glob(os.path.join(OUT, "zt_review_2026*.json")), reverse=True):
    try:
        _b = json.load(open(p, encoding="utf-8"))
        _k = _b["D0"]
        _z = pool(_b["dates"][_k], "em_ZB")
        _n = sum(1 for z in _z if z["p"] >= z["ztp"])
        if _n == 0:
            _streak += 1
        else:
            break
    except Exception:
        break
V["ZB_ZERO_STREAK"] = _streak

ts, tm, ty = S["timeslot"], S["timeslot"]["today"], S["timeslot"]["yesterday"]
PM = tm.get("午后盘中", 0) + tm.get("尾盘", 0)
AM = tm.get("竞价/秒板", 0) + tm.get("开盘半小时", 0) + tm.get("上午盘中", 0)
PM_Y = ty.get("午后盘中", 0) + ty.get("尾盘", 0)
AM_Y = ty.get("竞价/秒板", 0) + ty.get("开盘半小时", 0) + ty.get("上午盘中", 0)
V.update({"TS_PM": PM, "TS_PM_PCT": f"{PM / ZT * 100:.1f}", "TS_AM": AM, "TS_AM_PCT": f"{AM / ZT * 100:.1f}",
          "TS_AM_Y": AM_Y, "TS_PM_Y": PM_Y, "TS_AM_PCT_Y": f"{AM_Y / ZT_Y * 100:.1f}",
          "TS_PM_PCT_Y": f"{PM_Y / ZT_Y * 100:.1f}",
          "TS_HALF2": tm.get("开盘半小时", 0)})

_order = [("竞价/秒板", "竞价/秒板"), ("开盘半小时", "开盘半小时"), ("上午盘中", "上午盘中"),
          ("午后盘中", "午后盘中"), ("尾盘", "尾盘")]
_t = []
for k, lbl in _order:
    a, b = tm.get(k, 0), ty.get(k, 0)
    d = a - b
    _t.append("<tr><td>%s</td><td class='hl'>%d</td><td>%d</td><td class='%s'>%s</td></tr>" % (
        lbl, a, b, "up" if d > 0 else ("down" if d < 0 else "mut"), f"{d:+d}" if d else "0"))
V["TBL_TS"] = "\n".join(_t)

type0, type1 = {}, {}
for x in A0["ths_zt"]["info"]:
    type0[x.get("limit_up_type") or "?"] = type0.get(x.get("limit_up_type") or "?", 0) + 1
for x in A1["ths_zt"]["info"]:
    type1[x.get("limit_up_type") or "?"] = type1.get(x.get("limit_up_type") or "?", 0) + 1
YIZI = type0.get("一字板", 0)
YIZI_Y = type1.get("一字板", 0)
CYB = [x for x in zt0 if x["c"].startswith(("300", "301", "688", "689"))]
_pf = {p["name"]: p for p in perf}
YZ_DT = [x["name"] for x in A1["ths_zt"]["info"]
         if x.get("limit_up_type") == "一字板" and (_pf.get(x["name"]) or {}).get("pct", 0) <= -9.8]
YZ_ADV = [x["name"] for x in A1["ths_zt"]["info"]
          if x.get("limit_up_type") == "一字板" and (_pf.get(x["name"]) or {}).get("pct", 0) >= 9.8]
assert len(YZ_DT) + len(YZ_ADV) + sum(
    1 for x in A1["ths_zt"]["info"]
    if x.get("limit_up_type") == "一字板" and x["name"] in _pf
    and -9.8 < _pf[x["name"]]["pct"] < 9.8) == YIZI_Y, "昨日一字板去向不闭合"
V.update({"YIZI": YIZI, "YIZI_Y": YIZI_Y, "YZ_DT_N": len(YZ_DT), "YZ_DT_NAMES": "、".join(YZ_DT),
          "YZ_ADV_N": len(YZ_ADV), "YZ_ADV_NAMES": "、".join(YZ_ADV),
          "TZI": type0.get("T字板", 0), "JINGJIA": tm.get("竞价/秒板", 0),
          "JINGJIA_PCT": f"{tm.get('竞价/秒板', 0) / ZT * 100:.0f}",
          "HUANSHOU": type0.get("换手板", 0),
          "HUANSHOU_PCT": f"{type0.get('换手板', 0) / ZT * 100:.0f}",
          "CYB_N": len(CYB), "CYB_PCT": f"{len(CYB) / ZT * 100:.0f}",
          "YIZI_NAMES": "、".join(f"{x['n']}（{x['hybk']}，{x['lbc']}板）" for x in zt0
                                if (ths0.get(x["c"]) or {}).get("limit_up_type") == "一字板") or "无"})

# 商业航天：概念榜唯一越过 40% 阈值的板块（缩圈高度化）
_bk0 = {x["name"]: x for x in A0["ths_block"]}
_bk1 = {x["name"]: x for x in A1["ths_block"]}
_a0, _a1 = _bk0.get("商业航天", {}), _bk1.get("商业航天", {})
_n0, _l0 = _a0.get("limit_up_num", 0), _a0.get("continuous_plate_num", 0)
_n1, _l1 = _a1.get("limit_up_num", 0), _a1.get("continuous_plate_num", 0)
_gt40 = [x["name"] for x in sorted(A0["ths_block"], key=lambda z: -(z["continuous_plate_num"] / z["limit_up_num"]))
         if x["limit_up_num"] and x["continuous_plate_num"] / x["limit_up_num"] > 0.4]
V.update({"SPACE_BK_N": _n0, "SPACE_BK_LB": _l0, "SPACE_BK_R": f"{_l0 / _n0 * 100:.0f}" if _n0 else "—",
          "SPACE_BK_N_Y": _n1, "SPACE_BK_LB_Y": _l1,
          "SPACE_BK_R_Y": f"{_l1 / _n1 * 100:.0f}" if _n1 else "—",
          "SPACE_BK_GT40": len(_gt40), "SPACE_BK_GT40_NAMES": "、".join(_gt40),
          "SPACE_BK_RANK": [i for i, x in enumerate(A0["ths_block"], 1) if x["name"] == "商业航天"][0]})

# ================= 簇：消费 / 医药 / PCB =================
HY_CONS = ("白酒Ⅱ", "休闲食品", "饮料乳品", "食品加工", "一般零售", "酒店餐饮", "农产品加",
           "服装家纺", "小家电", "调味发酵", "白色家电", "非白酒")
HY_MED = ("医疗服务", "中药Ⅱ", "医疗器械", "医药商业", "化学制药", "生物制品")
HY_PCB = ("元件", "其他电子", "半导体", "光学光电", "电子化学品")
KW_PERF = ("三季报", "业绩", "扭亏", "净利")
KW_ROBOT = ("机器人", "具身", "人形", "灵巧手", "减速器", "丝杠", "关节")
KW_AERO = ("商业航天", "卫星", "航天", "太空")


def grp(items, hys):
    r = [x for x in items if x["hybk"] in hys]
    amt = sum(x["amount"] for x in r) / 1e8
    return {"n": len(r), "amt": amt, "lb": sum(1 for x in r if x.get("lbc", 0) >= 2),
            "hy": len({x["hybk"] for x in r}), "list": r}


cons, med, pcb = grp(zt0, HY_CONS), grp(zt0, HY_MED), grp(zt0, HY_PCB)
V.update({
    "CONS_N": cons["n"], "CONS_AMT": f"{cons['amt']:.1f}", "CONS_SHARE": f"{cons['amt'] / AMT_SUM * 100:.1f}",
    "CONS_LB": cons["lb"], "CONS_LB_R": f"{cons['lb'] / cons['n'] * 100:.0f}" if cons["n"] else "0",
    "CONS_BIG_N": sum(1 for x in cons["list"] if x["ltsz"] > 200e8),
    "CONS_WATCH": "、".join(x["n"] for x in sorted(cons["list"], key=lambda z: -z["fund"])[:3]),
    "MED_N": med["n"], "MED_AMT": f"{med['amt']:.1f}", "MED_SHARE": f"{med['amt'] / AMT_SUM * 100:.1f}",
    "MED_LB": med["lb"],
    "PCB_N": pcb["n"], "PCB_AMT": f"{pcb['amt']:.1f}", "PCB_SHARE": f"{pcb['amt'] / AMT_SUM * 100:.1f}",
    "PCB_LB": pcb["lb"],
})
_kw = [x for x in zt0 if any(k in ((ths0.get(x["c"]) or {}).get("reason_type") or "") for k in KW_PERF)]
V.update({"KW_N": len(_kw), "KW_PCT": f"{len(_kw) / ZT * 100:.0f}",
          "KW_LB": sum(1 for x in _kw if x["lbc"] >= 2),
          "KW_HY": len({x["hybk"] for x in _kw}),
          "BIGZT_N": sum(1 for x in zt0 if x["ltsz"] > 200e8),
          "BIGZT_Y": sum(1 for x in zt1 if x["ltsz"] > 200e8)})
THEME = [x for x in zt0 if x not in cons["list"] and x not in med["list"] and x not in pcb["list"]]
_theme_amt = sum(x["amount"] for x in THEME) / 1e8
V.update({"THREE_N": cons["n"] + med["n"] + pcb["n"],
          "THREE_SHARE": f"{(cons['amt'] + med['amt'] + pcb['amt']) / AMT_SUM * 100:.1f}"})

# 簇明细表（消费 / 医药 / PCB / 业绩 / 其余）
_other = [x for x in zt0 if x not in cons["list"] and x not in med["list"] and x not in pcb["list"]]
_rows_cl = [
    ("消费簇", cons["n"], cons["amt"], cons["lb"], cons["hy"]),
    ("医药簇", med["n"], med["amt"], med["lb"], med["hy"]),
    ("PCB·元件簇", pcb["n"], pcb["amt"], pcb["lb"], pcb["hy"]),
    ("业绩簇（交叉计数）", len(_kw), sum(x["amount"] for x in _kw) / 1e8, sum(1 for x in _kw if x["lbc"] >= 2), len({x["hybk"] for x in _kw})),
    ("其余", len(_other), sum(x["amount"] for x in _other) / 1e8, sum(1 for x in _other if x["lbc"] >= 2), len({x["hybk"] for x in _other})),
]
_t = []
for nm, n, amt, lb, hy in _rows_cl:
    _t.append("<tr><td>%s</td><td class='hl'>%d</td><td>%.1f</td><td>%.1f%%</td><td>%d</td><td>%d</td></tr>" % (
        nm, n, amt, amt / AMT_SUM * 100, lb, hy))
V["TBL_CLUSTER"] = "\n".join(_t)


def kwgrp(items, th, kws):
    r = [x for x in items if any(k in ((th.get(x["c"]) or {}).get("reason_type") or "") for k in kws)]
    return r


rob = kwgrp(zt0, ths0, KW_ROBOT)
rob1 = kwgrp(zt1, ths1, KW_ROBOT)
aero = kwgrp(zt0, ths0, KW_AERO)
aero1 = kwgrp(zt1, ths1, KW_AERO)
_rob_amt = sum(x["amount"] for x in rob) / 1e8
_rob_amt_y = sum(x["amount"] for x in rob1) / 1e8
_aero_amt = sum(x["amount"] for x in aero) / 1e8
_aero_amt_y = sum(x["amount"] for x in aero1) / 1e8
# 纯题材并集（两条关键词簇有重叠，须去重后计家数与成交）
_tc0 = {x["c"]: x for x in rob}
_tc0.update({x["c"]: x for x in aero})
_tc1 = {x["c"]: x for x in rob1}
_tc1.update({x["c"]: x for x in aero1})
_theme_n, _theme_n_y = len(_tc0), len(_tc1)
_theme_amt0 = sum(x["amount"] for x in _tc0.values()) / 1e8
_theme_amt1 = sum(x["amount"] for x in _tc1.values()) / 1e8
AMT_SUM_Yv = AMT_SUM_Y
V.update({
    "ROBOT_N": len(rob), "ROBOT_N_Y": len(rob1), "ROBOT_LB": sum(1 for x in rob if x["lbc"] >= 2),
    "ROBOT_AMT": f"{_rob_amt:.1f}", "ROBOT_AMT_Y": f"{_rob_amt_y:.1f}",
    "ROBOT_SHARE_Y": f"{_rob_amt_y / AMT_SUM_Yv * 100:.0f}",
    "AERO_N": len(aero), "AERO_N_Y": len(aero1),
    "AERO_AMT": f"{_aero_amt:.1f}", "AERO_AMT_Y": f"{_aero_amt_y:.1f}",
    "AERO_SHARE_Y": f"{_aero_amt_y / AMT_SUM_Yv * 100:.0f}",
    "THEME_N": _theme_n, "THEME_N_Y": _theme_n_y, "THEME_AMT": f"{_theme_amt0:.1f}",
    "THEME_AMT_Y": f"{_theme_amt1:.1f}",
    "THEME_SHARE": f"{_theme_amt0 / AMT_SUM * 100:.0f}",
    "THEME_SHARE_Y": f"{_theme_amt1 / AMT_SUM_Yv * 100:.0f}",
    "THEME_DROP": f"{_theme_amt1 / max(0.01, _theme_amt0):.1f}",
})

# 泸州老窖 / 古井 / 迎驾 / 金安国纪
for code, key in [("000568", "LZLJ"), ("000596", "GJGJ"), ("603198", "YJGJ"), ("002636", "JAJG")]:
    _x = next((z for z in zt0 if z["c"] == code), None)
    V[key + "_LTSZ"] = f"{_x['ltsz'] / 1e8:.0f}" if _x else "—"
    V[key + "_AMT"] = f"{_x['amount'] / 1e8:.1f}" if _x else "—"

# ================= 概念榜 =================
blk = sorted(A0["ths_block"], key=lambda x: -(x["limit_up_num"] or 0))[:12]
_bd = {b["name"]: b for b in A0["ths_block"]}
_bd1 = {b["name"]: b for b in A1["ths_block"]}
_t = []
for b in blk:
    r = b["continuous_plate_num"] / b["limit_up_num"] * 100 if b["limit_up_num"] else 0
    _t.append("<tr><td>%s</td><td class='hl'>%d</td><td>%d</td><td>%.1f%%</td></tr>" % (
        b["name"], b["limit_up_num"], b["continuous_plate_num"], r))
V["TBL_CONC"] = "\n".join(_t)
JS_CONC = {"names": [b["name"] for b in blk][::-1],
           "num": [b["limit_up_num"] for b in blk][::-1],
           "lb": [b["continuous_plate_num"] for b in blk][::-1]}
_b1 = blk[0]
V["CONC_TOP1"] = _b1["name"]
V["CONC_TOP1_N"] = _b1["limit_up_num"]
V["CONC_TOP1_LB"] = _b1["continuous_plate_num"]
V["CONC_TOP1_R"] = f"{_b1['continuous_plate_num'] / max(1, _b1['limit_up_num']) * 100:.1f}"
V["CONC_TOP7"] = "、".join(f"{b['name']} {b['limit_up_num']}/{b['continuous_plate_num']}" for b in blk[:7])


def conc(name):
    b, b1 = _bd.get(name) or {}, _bd1.get(name) or {}
    n, l = b.get("limit_up_num", 0), b.get("continuous_plate_num", 0)
    return n, l, (l / n * 100 if n else 0)


_n, _l, _r = conc("机器人概念")
V.update({"CONC_ROBOT_N": _n, "CONC_ROBOT_LB": _l, "CONC_ROBOT_R": f"{_r:.1f}"})

# ================= 行业迁移 =================
hy0, hy1 = S["hy0"], S["hy1"]
allh = set(hy0) | set(hy1)
hrows = [(h, hy0.get(h, 0), hy1.get(h, 0)) for h in allh]
hrows.sort(key=lambda r: -((r[1] + r[2]) + abs(r[1] - r[2]) * 2))
_hs = hrows[:14][::-1]
V["ZT_HY_N"], V["ZT_HY_Y"] = len(hy0), len(hy1)
V["HY_NEW_N"] = sum(1 for r in hrows if r[2] == 0 and r[1] > 0)
V["HY_ZERO_N"] = sum(1 for r in hrows if r[1] == 0 and r[2] > 0)
JS_HY = {"names": [r[0] for r in _hs], "vals": [r[1] - r[2] for r in _hs]}
_t = []
for r in _hs[::-1]:
    d = r[1] - r[2]
    _t.append("<tr><td>%s</td><td>%d</td><td>%d</td><td class='%s'>%s</td></tr>" % (
        r[0], r[2], r[1], "up" if d > 0 else ("down" if d < 0 else "mut"), f"{d:+d}" if d else "0"))
V["TBL_HY"] = "\n".join(_t)
for h, k in [("白酒Ⅱ", "HY_BAIJIU"), ("元件", "HY_YJ"), ("医疗服务", "HY_YLFW"), ("休闲食品", "HY_XXSP"),
             ("医疗器械", "HY_YLQX"), ("通用设备", "HY_TY"), ("专用设备", "HY_ZY"), ("汽车零部", "HY_QC")]:
    V[k] = hy0.get(h, 0)
    V[k + "_Y"] = hy1.get(h, 0)

# ================= 昨日涨停股今日表现 =================
adv = [p for p in perf if p["again"]]
V.update({"ADV_N": len(adv), "ADV_TOT": len(perf), "ADV_RATE": f"{len(adv) / len(perf) * 100:.1f}",
          "PERF_MED": f2(median([p["pct"] for p in perf])),
          "PERF_MEAN": f2(mean([p["pct"] for p in perf])),
          "PERF_UP_N": sum(1 for p in perf if p["pct"] > 0), "PERF_DN_N": sum(1 for p in perf if p["pct"] < 0),
          "PERF_GT5_N": sum(1 for p in perf if p["pct"] < -5),
          "NEW_FACE": ZT - len(adv), "NEW_FACE_PCT": f"{(ZT - len(adv)) / ZT * 100:.0f}"})

sb, lbv = _sb, _lbv
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
          "GAP_L_DROP": f"{abs(median([p['pct'] for p in _lb1]) - LB_M):.2f}",
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
          "DT_BIG_N": sum(1 for x in dt0 if (x.get("ltsz") or 0) > 100e8),
          "DT_MED_AMT": f"{median([(x.get('amount') or 0) for x in dt0]) / 1e8:.2f}",
          "DT_MED_LTSZ": f"{median([(x.get('ltsz') or 0) for x in dt0]) / 1e8:.0f}",
          "DT_DIFF_N": len(dt0) - DT,
          "DT_Y_RAW": s1["dt"]})
V["DT_BIG_PCT"] = f"{V['DT_BIG_N'] / len(dt0) * 100:.0f}"

hycnt = {}
for x in dt0:
    hycnt[x.get("hybk")] = hycnt.get(x.get("hybk"), 0) + 1
_hysorted = sorted(hycnt.items(), key=lambda kv: (-kv[1], kv[0]))
V["DT_TOP_HY_N"] = _hysorted[0][1]
JS_DTCHAIN = {"names": [n for n, _ in _hysorted[:10]][::-1],
              "vals": [c for _, c in _hysorted[:10]][::-1],
              "chain": [n in G_MEDIA + G_ROBO + G_CHIP for n, _ in _hysorted[:10]][::-1]}

_t = []
for x in sorted(dt0, key=lambda z: -(z.get("amount") or 0))[:10]:
    _t.append("<tr><td>%s</td><td>%s</td><td class='down'>%.2f%%</td><td>%.2f</td><td>%.0f</td></tr>" % (
        x["n"], x.get("hybk"), x.get("zdp") or 0, (x.get("amount") or 0) / 1e8, (x.get("ltsz") or 0) / 1e8))
V["TBL_DT_TOP10"] = "\n".join(_t)
_dtop = max(dt0, key=lambda z: z.get("amount") or 0) if dt0 else {}
V["DT_TOP_NAME"] = _dtop.get("n", "—")
V["DT_TOP_HY"] = _dtop.get("hybk", "—")
V["DT_TOP_LTSZ"] = f"{(_dtop.get('ltsz') or 0) / 1e8:.0f}"
V["DT_TOP_AMT"] = f"{(_dtop.get('amount') or 0) / 1e8:.2f}"

# 三条旧主线归并
media, robo, chip = grp(dt0, G_MEDIA), grp(dt0, G_ROBO), grp(dt0, G_CHIP)
media1, robo1, chip1 = grp(dt1, G_MEDIA), grp(dt1, G_ROBO), grp(dt1, G_CHIP)
V.update({
    "C_MEDIA_N": media["n"], "C_MEDIA_N_Y": media1["n"], "C_MEDIA_AMT": f"{media['amt']:.1f}",
    "C_MEDIA_PCT": f"{media['n'] / len(dt0) * 100:.0f}",
    "C_MEDIA_AMT_PCT": f"{media['amt'] / DT_AMT * 100:.0f}",
    "C_ROBO_N": robo["n"], "C_ROBO_N_Y": robo1["n"], "C_ROBO_AMT": f"{robo['amt']:.1f}",
    "C_ROBO_AMT_PCT": f"{robo['amt'] / DT_AMT * 100:.0f}",
    "C_CHIP_N": chip["n"], "C_CHIP_N_Y": chip1["n"], "C_CHIP_AMT": f"{chip['amt']:.1f}",
    "C_CHIP_AMT_PCT": f"{chip['amt'] / DT_AMT * 100:.0f}",
    "C_CHIP_PCT": f"{chip['n'] / len(dt0) * 100:.0f}",
    "C_CHIP_PCT_Y": f"{chip1['n'] / len(dt1) * 100:.0f}",
    "C_TWO_N": media["n"] + robo["n"],
    "C_TWO_PCT": f"{(media['n'] + robo['n']) / len(dt0) * 100:.0f}",
    "C_TWO_AMT": f"{media['amt'] + robo['amt']:.1f}",
    "C_TWO_AMT_PCT": f"{(media['amt'] + robo['amt']) / DT_AMT * 100:.0f}",
    "C_ALL3_N": media["n"] + robo["n"] + chip["n"],
    "C_ALL3_PCT": f"{(media['n'] + robo['n'] + chip['n']) / len(dt0) * 100:.0f}",
    "DT_POOL_N_MINUS": len(dt0) - (media["n"] + robo["n"] + chip["n"]),
    "DT_HY_REST": len({x["hybk"] for x in dt0 if x["hybk"] not in G_MEDIA + G_ROBO + G_CHIP}),
})


def topn(items, k=3):
    return "、".join(x["n"] for x in sorted(items, key=lambda z: -(z.get("amount") or 0))[:k]) or "无"


_t = []
for nm, g0, g1 in [("传媒 / AI 内容", media, media1), ("机器人 / 汽车零部件", robo, robo1), ("算力硬件", chip, chip1)]:
    _t.append("<tr><td>%s</td><td>%d</td><td class='hl'>%d</td><td>%.1f</td><td>%.0f%%</td><td class='note'>%s</td></tr>" % (
        nm, g1["n"], g0["n"], g0["amt"], g0["amt"] / DT_AMT * 100, topn(g0["list"])))
V["TBL_DTGRP"] = "\n".join(_t)

# 昨日跌停池今日表现
QP = os.path.join(OUT, f"_qdt{D1[4:]}.json")
Q = {}
if os.path.exists(QP):
    Q = json.load(open(QP, encoding="utf-8"))
else:
    raise SystemExit(f"缺少 {QP}，请先抓取昨日跌停股今日行情")

dt1c = [x["c"] for x in dt1]
inter = sorted({x["code"] for x in A0["ths_zt"]["info"]} & set(dt1c))
vals = [Q[c]["pct"] for c in dt1c if c in Q]
V.update({
    "REL_MEAN": f2(mean(vals)), "REL_MED": f2(median(vals)),
    "REL_UP": sum(1 for v in vals if v > 0),
    "REL_DT": sum(1 for v in vals if v <= -9.8),
    "REL_BIG": sum(1 for v in vals if v > 5),
    "INTER_N": len(inter),
    "INTER_NAMES": "、".join(f"{Q[c]['name']} {Q[c]['pct']:+.2f}%" for c in inter if c in Q) if inter else "一只都没有",
    "INTER_PCT": f"{len(inter) / len(dt1c) * 100:.1f}",
    "REL_DT_PCT": f"{sum(1 for v in vals if v <= -9.8) / len(vals) * 100:.0f}",
    "DT_ODDS": f"{(sum(1 for v in vals if v <= -9.8) / max(1, len(inter))):.0f}",
})
_dt_sets = {x["c"] for x in dt0} & {x["c"] for x in dt1}
V["DT_CONT_N"] = len(_dt_sets)
_nm = {x["c"]: x["n"] for x in dt0}
V["DT_CONT_NAMES"] = "、".join(_nm.get(c, c) for c in _dt_sets) or "无"
V["DT_RULE_N"] = 12  # 可枚举清单：09-29/09-30/10-09/10-12/10-13/10-14/10-15/10-22/10-23/10-26/10-29/10-30

# 昨涨停 -> 今跌停
_dtset = {x["c"] for x in dt0}
_att = [p for p in perf if p["code"] in _dtset]
V["ATK_DT_N"] = len(_att)
V["ATK_DT_LB_N"] = sum(1 for p in _att if p["lbc"] >= 2)
V["ATK_DT_SB_N"] = sum(1 for p in _att if p["lbc"] == 1)
V["ATK_DT_PCT"] = f"{len(_att) / len(perf) * 100:.0f}"
V["ATK_DT_LAD_TXT"] = "、".join(f"{p['name']}（昨 {p['lbc']} 板）" for p in sorted(_att, key=lambda z: -z["lbc"])) or "无"
V["ATK_DT_NAMES"] = "、".join(f"{p['name']}（昨{p['lbc']}板，{p['hybk']}）" for p in sorted(_att, key=lambda z: -z["lbc"])) or "无"

_bins = [(-100, -9.8, "跌停"), (-9.8, -5, "跌5~停"), (-5, -2, "跌2~5"), (-2, 0, "跌0~2"),
         (0, 2, "涨0~2"), (2, 5, "涨2~5"), (5, 9.8, "涨5~停"), (9.8, 100, "涨停")]
JS_REL = {"labels": [b[2] for b in _bins], "vals": [], "colors": []}
for lo, hi, lbl in _bins:
    n = sum(1 for v in vals if v <= -9.8) if lbl == "跌停" else sum(1 for v in vals if lo < v <= hi)
    JS_REL["vals"].append(n)
    JS_REL["colors"].append("down" if hi <= 0 else "up")

# 昨日算力硬件 10 只今日表现
_c10 = [x for x in dt1 if x["hybk"] in G_CHIP]
_c10v = [Q[x["c"]]["pct"] for x in _c10 if x["c"] in Q]
V["CHIP10_DN"] = sum(1 for v in _c10v if v < 0)
V["CHIP10_UP"] = sum(1 for v in _c10v if v > 0)
V["CHIP10_MEAN"] = f2(mean(_c10v)) if _c10v else "—"
for nm, key in [("沪电股份", "HSDZ"), ("鹏鼎控股", "PDKG"), ("先导基电", "XDJD"),
                ("欧菲光", "OFG"), ("环旭电子", "HX"), ("澳弘电子", "AHDZ")]:
    _x = next((z for z in _c10 if z["n"] == nm), None)
    _q = Q.get(_x["c"]) if _x else None
    V[key + "_PCT"] = f2(_q["pct"]) if _q else "—"
    if key == "HSDZ":
        V["HSDZ_AMT"] = f"{_q['amount']:.1f}" if _q else "—"

# ================= 口径 =================
_bj = [x for x in zt_all if x["c"].startswith("92")]
V["BJ_N"] = len(_bj)
V["BJ_CODES"] = "、".join(f"{x['n']}（{x['c']}）" for x in _bj) or "无"
V["EM_ZT_N"] = len(zt0_em)
_DIFS = sorted({x["c"] for x in zt_all} - {x["c"] for x in zt0})
_bad = [c for c in _DIFS if not c.startswith("92")]
assert not _bad, f"东财差额里出现无法归因的沪深代码：{_bad}"

# ================= westock 交叉验证 =================
SWP = os.path.join(OUT, f"_sw{D0[4:]}.json")
_need = ["通信设备", "元件", "半导体", "软件开发", "IT服务Ⅱ", "游戏Ⅱ", "影视院线", "数字媒体",
         "酒店餐饮", "白酒Ⅱ", "航运港口", "白色家电", "饮料乳品", "医药商业", "中药Ⅱ", "医疗服务",
         "银行概念", "保险Ⅱ", "煤炭开采", "白酒概念", "CRO", "光芯片", "覆铜板", "人形机器人"]


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
if not SW:
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


def sw_out(nm):
    v = SW.get(nm)
    return f2(v["pct"]) if v else "—"


def sw_up(nm):
    v = (SW.get(nm) or {}).get("updown") or ""
    return v if "/" in v else "—"


def sw_flow(nm):
    v = SW.get(nm)
    return f"{v['flow'] / 10000:+.1f}" if v else "—"


for nm, key in [("通信设备", "SW_TX"), ("元件", "SW_YJ"), ("半导体", "SW_BDT"), ("软件开发", "SW_SOFT"),
                ("IT服务Ⅱ", "SW_ITS"), ("游戏Ⅱ", "SW_GAME"), ("影视院线", "SW_FILM"), ("数字媒体", "SW_DIGI"),
                ("酒店餐饮", "SW_HOTEL"), ("白酒Ⅱ", "SW_BAIJIU"), ("航运港口", "SW_SHIP"),
                ("白色家电", "SW_WHT"), ("饮料乳品", "SW_DRINK"), ("医药商业", "SW_PHARM"),
                ("中药Ⅱ", "SW_TCM"), ("医疗服务", "SW_MED_SW"), ("银行概念", "SW_BANK"), ("煤炭开采", "SW_COAL")]:
    V[key] = sw_out(nm)
    V[key + "_UP"] = sw_up(nm)

_rows = [
    ("申万二级", "通信设备", "通信设备"), ("申万二级", "元件（PCB / 覆铜板）", "元件"), ("申万二级", "半导体", "半导体"),
    ("申万二级", "软件开发", "软件开发"), ("申万二级", "IT 服务", "IT服务Ⅱ"), ("申万二级", "游戏", "游戏Ⅱ"),
    ("申万二级", "影视院线", "影视院线"), ("申万二级", "数字媒体", "数字媒体"),
    ("申万二级·对照", "酒店餐饮", "酒店餐饮"), ("申万二级·对照", "白酒Ⅱ", "白酒Ⅱ"), ("申万二级·对照", "航运港口", "航运港口"),
    ("申万二级·对照", "白色家电", "白色家电"), ("申万二级·对照", "饮料乳品", "饮料乳品"),
    ("申万二级·对照", "医药商业", "医药商业"), ("申万二级·对照", "中药Ⅱ", "中药Ⅱ"), ("申万二级·对照", "医疗服务", "医疗服务"),
    ("概念·对照", "银行概念", "银行概念"), ("概念·对照", "煤炭开采", "煤炭开采"),
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
            "high": [round(x["high"], 2) for x in INTRA], "close": [round(x["close"], 2) for x in INTRA]}
JS_AMT = {"names": [x["name"] for x in ix], "yoy": [None if x["yoy"] is None else round(x["yoy"], 1) for x in ix]}
JS_TS = {"labels": [k for k, _ in _order], "today": [tm.get(k, 0) for k, _ in _order],
         "prev": [ty.get(k, 0) for k, _ in _order]}
_other_n = ZT - cons["n"] - med["n"] - pcb["n"]
_other_amt = AMT_SUM - cons["amt"] - med["amt"] - pcb["amt"]
JS_CLUSTER = {"names": ["消费", "医药", "PCB·元件", "其余"], "amt": [round(cons["amt"], 1), round(med["amt"], 1), round(pcb["amt"], 1), round(_other_amt, 1)],
              "n": [cons["n"], med["n"], pcb["n"], _other_n]}
for k, v in [("JS_SENTI", JS_SENTI), ("JS_INTRA", JS_INTRA), ("JS_AMT", JS_AMT), ("JS_LAD", JS_LAD),
             ("JS_CONC", JS_CONC), ("JS_CLUSTER", JS_CLUSTER), ("JS_HY", JS_HY), ("JS_PF", JS_PF),
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

# 关键读数打印（供人工核对）
for k in ["ZT", "ZT_Y", "TOUCH", "TOUCH_Y", "SEAL", "SEAL_Y", "DT", "DT_Y", "DTOUCH", "DSEAL",
          "AMT", "AMT_Y", "AMT_PCT", "N_DN", "AMT_DN_N", "AMT_UP_N", "N_CLOSE_LOW",
          "ADV_RATE", "PERF_MED", "GAP", "GAP_Y", "ATK_DT_N", "CONS_N", "CONS_SHARE", "MED_N",
          "MED_SHARE", "PCB_N", "PCB_SHARE", "KW_N", "KW_PCT", "C_MEDIA_N", "C_ROBO_N", "C_CHIP_N",
          "C_TWO_AMT_PCT", "DT_RATIO", "INTER_N", "REL_UP", "REL_DT", "SHARE", "ZB_SEALED_N", "ZB_ZERO_STREAK"]:
    print("  %-14s %s" % (k, V.get(k)))
