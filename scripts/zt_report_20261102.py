# -*- coding: utf-8 -*-
"""涨停复盘报告 20261102 vs 20261030（跌停潮次日 · 同批股票反包 · AI 链一日铺开无高度）
用法：python scripts/zt_report_20261102.py 20261102
输入：out/zt_stats_20261102.json、out/zt_review_20261102.json、out/zt_review_20261030.json、out/zt_stats_20261030.json
     跌停明细 out/_dt1102.json / out/_dt1030.json；昨跌停股今日行情 out/_qdt1030.json；westock 榜 out/_sw1102.json
输出：reports/涨停复盘对比-20261102.html
"""
import json, os, sys, re, glob, urllib.request, time
from statistics import mean, median

ROOT = os.environ.get("ZT_ROOT") or os.getcwd()
OUT = os.path.join(ROOT, "out")
REP = os.path.join(ROOT, "reports")
TPL = os.path.join(ROOT, "scripts", "_report_tpl_20261102.html")
os.makedirs(REP, exist_ok=True)

D0 = sys.argv[1] if len(sys.argv) > 1 else "20261102"
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
V["NEXT_D"] = "11/3（周二）"


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
assert len(dt0) == 8, f"今日跌停池 {len(dt0)} 只，与汇总字段不符"

# 叙事分组
G_MEDIA = ("广告营销", "数字媒体", "游戏Ⅱ", "出版", "影视院线", "电视广播", "文娱用品")
G_SOFT = ("IT服务Ⅱ", "软件开发", "计算机设")
G_AI = G_MEDIA + G_SOFT
G_CHIP = ("元件", "通信设备", "半导体", "消费电子", "光学光电", "其他电子", "电子化学品")
HY_CONS = ("白酒Ⅱ", "休闲食品", "饮料乳品", "食品加工", "一般零售", "酒店餐饮", "农产品加",
           "服装家纺", "小家电", "调味发酵品", "白色家电", "非白酒")
HY_MED = ("医疗服务", "中药Ⅱ", "医疗器械", "医药商业", "化学制药", "生物制品")

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
assert TOUCH - ZT == ZB, f"触及-涨停({TOUCH - ZT}) ≠ 炸板({ZB})，口径异常"

V.update({
    "ZT": ZT, "ZT_Y": ZT_Y, "ZT_D": f"{ZT - ZT_Y:+d}", "ZT_PCT_D": f"{abs((ZT / ZT_Y - 1) * 100):.0f}",
    "TOUCH": TOUCH, "TOUCH_Y": TOUCH_Y, "TOUCH_D": f"{TOUCH - TOUCH_Y:+d}",
    "TOUCH_PCT": f"{abs((TOUCH / TOUCH_Y - 1) * 100):.0f}",
    "TOUCH_GAP": TOUCH - ZT,
    "SEAL": f"{SEAL:.1f}", "SEAL_Y": f"{SEAL_Y:.1f}", "SEAL_D": f"{SEAL - SEAL_Y:+.1f}",
    "SEAL_D_ABS": f"{abs(SEAL - SEAL_Y):.1f}",
    "SEAL_FAIL": f"{(1 - ZT / TOUCH) * 100:.1f}", "SEAL_FAIL_Y": f"{(1 - ZT_Y / TOUCH_Y) * 100:.1f}",
    "DT": DT, "DT_Y": DT_Y, "DT_D": f"{DT - DT_Y:+d}", "DT_X": f"{DT_Y / DT:.0f}",
    "DT_PCT_D": f"{abs((DT / DT_Y - 1) * 100):.0f}",
    # 跌停家数是反向指标：增加=情绪负面=绿(down)，减少=情绪正面=红(up)
    "DT_D_CLS": "down" if DT - DT_Y > 0 else "up",
    "ZT_D_CLS": "up" if ZT - ZT_Y > 0 else "down",
    "DTOUCH": DTOUCH, "DTOUCH_Y": DTOUCH_Y, "DTOUCH_D": f"{DTOUCH - DTOUCH_Y:+d}",
    "DSEAL": f"{DSEAL:.1f}", "DSEAL_Y": f"{DSEAL_Y:.1f}", "DSEAL_D": f"{DSEAL - DSEAL_Y:+.1f}",
    "DT_OPEN_N": DT_OPEN_N, "DT_OPEN_Y": DT_OPEN_Y,
    "DT_REBUY": f"{DT_OPEN_N / DTOUCH * 100:.1f}",
    "ZB": ZB, "ZB_Y": ZB_Y, "ZB_D": f"{ZB - ZB_Y:+d}",
})

# 三日阶梯（D2 列取 D1 文件自带的 yesterday）
days = [
    {"d": md(D2), "zt": s1["zt_prev"], "zb": s1["zb_prev"], "dt": s1["dt_prev"],
     "touch": s1["yest"].get("history_num", 0), "dtouch": _dcy0["history_num"]},
    {"d": md(D1), "zt": s1["zt"], "zb": s1["zb"], "dt": s1["dt"], "touch": TOUCH_Y, "dtouch": DTOUCH_Y},
    {"d": md(D0), "zt": s0["zt"], "zb": s0["zb"], "dt": s0["dt"], "touch": TOUCH, "dtouch": DTOUCH},
]
for x in days:
    x["seal"] = x["zt"] / x["touch"] * 100 if x["touch"] else 0.0
assert days[0]["dtouch"] != days[1]["dtouch"], "D2 列触及跌停与 D1 相同，取错文件"
assert days[0]["zt"] != days[1]["zt"], "D2 列涨停与 D1 相同，取错文件"
assert days[0]["dt"] != days[1]["dt"], "D2 列跌停与 D1 相同，取错文件"

V["ZTDT"] = f"{ZT / DT:.1f}"
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

_seals, _zts, _dts = [], [ZT], [DT]
for p in sorted(glob.glob(os.path.join(OUT, "zt_stats_2026*.json"))):
    try:
        _d = json.load(open(p, encoding="utf-8"))
        _k = _d["D0"]
        _s = _d["senti"][_k]
        _seals.append(_s["seal_rate"] * 100)
        _zts.append(_s["zt"])
        _dts.append(_s["dt"])
    except Exception:
        continue
V["SEAL_MIN"] = f"{min(_seals):.1f}"
V["SEAL_MAX"] = f"{max(_seals):.1f}"
V["ZT_HIST_MAX"] = max(_zts)
V["ZT_NEW_HIGH"] = "是" if ZT >= max(_zts) else "否"
V["DT_HIST_MIN"] = min(_dts)

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

# 日内 OHLC（腾讯日线，按显式日期取，不用 rows[-1]）
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
assert len(OHLC) == 6, f"日内 OHLC 只拿到 {len(OHLC)} 个指数"

INTRA = []
for nm in ["上证指数", "深证成指", "创业板指", "科创50", "国证2000", "上证50"]:
    o = OHLC[nm]
    INTRA.append({"nm": nm, "gap": (o["open"] / o["prev"] - 1) * 100, "high": (o["high"] / o["prev"] - 1) * 100,
                  "low": (o["low"] / o["prev"] - 1) * 100, "close": (o["close"] / o["prev"] - 1) * 100,
                  "reb": (o["close"] / o["low"] - 1) * 100, "draw": (o["close"] / o["high"] - 1) * 100})
V["N_BELOW_OPEN"] = sum(1 for x in INTRA if x["close"] < x["gap"])
V["N_ABOVE_OPEN"] = len(INTRA) - V["N_BELOW_OPEN"]
V["N_INTRA"] = len(INTRA)
V["N_REBOUND"] = sum(1 for x in INTRA if x["reb"] > 0)
V["N_GAP_UP"] = sum(1 for x in INTRA if x["gap"] > 0)
V["N_GAP_DN"] = sum(1 for x in INTRA if x["gap"] < 0)
V["N_HIGH_NEW"] = sum(1 for x in INTRA if x["high"] > 0)
for key, nm in [("SH", "上证指数"), ("CY", "创业板指"), ("KC", "科创50"),
                ("GZ", "国证2000"), ("SH50", "上证50"), ("SZ", "深证成指")]:
    x = next((y for y in INTRA if y["nm"] == nm), None)
    if x:
        V[key + "_GAP"] = f2(x["gap"])
        V[key + "_HIGH"] = f2(x["high"])
        V[key + "_LOW"] = f2(x["low"])
        V[key + "_PCT"] = f2(x["close"])
        V[key + "_REB"] = f"{x['reb']:.2f}"
        V[key + "_DRAW"] = f"{x['draw']:.2f}"
for key, nm in [("CY", "创业板指"), ("KC", "科创50"), ("SH50", "上证50"), ("HS300", "沪深300"),
                ("SZ", "深证成指"), ("BJ", "北证50"), ("ZX100", "中小100"), ("SH", "上证指数"),
                ("ZZ500", "中证500"), ("ZZ1000", "中证1000"), ("GZ", "国证2000")]:
    r = next((y for y in ix if y["name"] == nm), None)
    if r:
        V[key + "_YOY"] = f1(r["yoy"] or 0)
        V[key + "_YOY_ABS"] = f"{abs(r['yoy'] or 0):.1f}"
        V[key + "_AMT"] = f"{r['amt']:.0f}"
        V[key + "_IDX_PCT"] = f2(r["pct"])
for key, nm in [("HS300", "沪深300"), ("SH50", "上证50")]:
    V[key + "_PCT"] = f2((i0.get(nm) or {}).get("pct") or 0)
V["SH50_PCT_Y"] = f"{(i1.get('上证50') or {}).get('pct') or 0:+.2f}"
V["KC_PCT_Y"] = f"{(i1.get('科创50') or {}).get('pct') or 0:+.2f}"
V["CY_PCT_Y"] = f"{(i1.get('创业板指') or {}).get('pct') or 0:+.2f}"
V["SH_PCT_Y"] = f"{(i1.get('上证指数') or {}).get('pct') or 0:+.2f}"

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
# 连板股中属于 AI 链的只数（今日为 0，是核心论据）
V["LB_AI_N"] = sum(1 for x in zt0 if x["lbc"] >= 2 and x["hybk"] in G_AI)

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
    "ZT_MED_LTSZ_Y": f"{median([x['ltsz'] for x in zt1]) / 1e8:.0f}",
    "BIGZT_N": sum(1 for x in zt0 if x["ltsz"] > 200e8),
    "BIGZT_Y": sum(1 for x in zt1 if x["ltsz"] > 200e8),
})
_f1 = max(zt0, key=lambda x: x["fund"])
_f1y = max(zt1, key=lambda x: x["fund"])
V.update({"FUND_TOP1_NAME": _f1["n"], "FUND_TOP1": f"{_f1['fund'] / 1e8:.2f}",
          "FUND_TOP1_SHARE": f"{_f1['fund'] / sum(x['fund'] for x in zt0) * 100:.1f}",
          "FUND_TOP1_HY": _f1["hybk"], "FUND_TOP1_BOARD": _f1["lbc"],
          "FUND_TOP1_Y_NAME": _f1y["n"], "FUND_TOP1_Y": f"{_f1y['fund'] / 1e8:.2f}",
          "FUND_TOP1_Y_SHARE": f"{_f1y['fund'] / sum(x['fund'] for x in zt1) * 100:.1f}"})

_sf = sorted(zt0, key=lambda z: -z["fund"])[:10]
_t = []
for x in _sf:
    _t.append("<tr><td>%s</td><td>%.2f</td><td>%.2f</td><td>%.1f 倍</td><td>%.1f%%</td></tr>" % (
        x["n"], x["fund"] / 1e8, x["amount"] / 1e8, x["fund"] / max(x["amount"], 1), x["hs"]))
V["TBL_FUND_TOP"] = "\n".join(_t)
JS_FUND = {"names": [x["n"] for x in _sf][::-1], "vals": [round(x["fund"] / 1e8, 2) for x in _sf][::-1]}

# ================= 炸板 / 封板时间 =================
sealed = [z for z in zb0 if z["p"] >= z["ztp"]]
V["ZB_POOL_N"] = len(zb0)
V["ZB_SEALED_N"] = len(sealed)
V["ZB_SEAL_PCT"] = f"{len(sealed) / len(zb0) * 100:.1f}" if zb0 else "—"
V["ZB_SEALED_NAMES"] = "、".join(f"{z['n']}（{z['hybk']}，收 {z['zdp']:+.2f}%）" for z in sealed) or "无"
V["ZB_MED"] = f"{median([(z.get('amount') or 0) for z in zb0]) / 1e8:.2f}"
V["ZB_MED_Y"] = f"{median([(z.get('amount') or 0) for z in pool(A1, 'em_ZB')]) / 1e8:.2f}"
V["ZB_BIG_N"] = sum(1 for z in zb0 if (z.get("ltsz") or 0) > 100e8)
_zbs = sorted(zb0, key=lambda z: -(z.get("amount") or 0))[:3]
V["ZB_TOP_TXT"] = "、".join(f"{z['n']}（{z['hybk']}，流通 {(z.get('ltsz') or 0) / 1e8:.0f} 亿，成交 {(z.get('amount') or 0) / 1e8:.2f} 亿，收 {z['zdp']:+.2f}%）" for z in _zbs)
# 连续零回封天数（从 D1 往前数，不含 D0）
_streak = 0
for p in sorted(glob.glob(os.path.join(OUT, "zt_review_2026*.json")), reverse=True):
    try:
        _b = json.load(open(p, encoding="utf-8"))
        _k = _b["D0"]
        if _k >= D0:
            continue
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
          "TS_HALF2": tm.get("开盘半小时", 0), "TS_MID": tm.get("上午盘中", 0)})

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
_yz1 = [x for x in A1["ths_zt"]["info"] if x.get("limit_up_type") == "一字板"]
YZ_DT = [x["name"] for x in _yz1 if (_pf.get(x["name"]) or {}).get("pct", 0) <= -9.8]
YZ_ADV = [x["name"] for x in _yz1 if (_pf.get(x["name"]) or {}).get("pct", 0) >= 9.8]
YZ_OTHER = [x["name"] for x in _yz1 if x["name"] in _pf
            and -9.8 < _pf[x["name"]]["pct"] < 9.8]
assert len(YZ_DT) + len(YZ_ADV) + len(YZ_OTHER) == YIZI_Y, "昨日一字板去向不闭合"
V.update({"YIZI": YIZI, "YIZI_Y": YIZI_Y, "YZ_DT_N": len(YZ_DT), "YZ_DT_NAMES": "、".join(YZ_DT) or "无",
          "YZ_ADV_N": len(YZ_ADV), "YZ_ADV_NAMES": "、".join(YZ_ADV) or "无",
          "YZ_OTHER_N": len(YZ_OTHER), "YZ_OTHER_NAMES": "、".join(YZ_OTHER) or "无",
          "TZI": type0.get("T字板", 0), "JINGJIA": tm.get("竞价/秒板", 0),
          "JINGJIA_PCT": f"{tm.get('竞价/秒板', 0) / ZT * 100:.0f}",
          "HUANSHOU": type0.get("换手板", 0),
          "HUANSHOU_PCT": f"{type0.get('换手板', 0) / ZT * 100:.0f}",
          "CYB_N": len(CYB), "CYB_PCT": f"{len(CYB) / ZT * 100:.0f}",
          "YIZI_NAMES": "、".join(f"{x['n']}（{x['hybk']}，{x['lbc']}板）" for x in zt0
                                if (ths0.get(x["c"]) or {}).get("limit_up_type") == "一字板") or "无"})

# ================= 簇 =================
KW_PERF = ("三季报", "业绩", "扭亏", "净利")


def grp(items, hys):
    r = [x for x in items if x["hybk"] in hys]
    amt = sum(x["amount"] for x in r) / 1e8
    return {"n": len(r), "amt": amt, "lb": sum(1 for x in r if x.get("lbc", 0) >= 2),
            "hy": len({x["hybk"] for x in r}), "list": r}


media, soft, ai = grp(zt0, G_MEDIA), grp(zt0, G_SOFT), grp(zt0, G_AI)
media1, soft1, ai1 = grp(zt1, G_MEDIA), grp(zt1, G_SOFT), grp(zt1, G_AI)
cons, med = grp(zt0, HY_CONS), grp(zt0, HY_MED)
cons1, med1 = grp(zt1, HY_CONS), grp(zt1, HY_MED)
V.update({
    "MEDIA_N": media["n"], "MEDIA_N_Y": media1["n"], "MEDIA_AMT": f"{media['amt']:.1f}",
    "MEDIA_AMT_Y": f"{media1['amt']:.1f}", "MEDIA_LB": media["lb"], "MEDIA_HY": media["hy"],
    "MEDIA_SHARE": f"{media['amt'] / AMT_SUM * 100:.1f}",
    "SOFT_N": soft["n"], "SOFT_N_Y": soft1["n"], "SOFT_AMT": f"{soft['amt']:.1f}", "SOFT_LB": soft["lb"],
    "AI_N": ai["n"], "AI_N_Y": ai1["n"], "AI_AMT": f"{ai['amt']:.1f}", "AI_AMT_Y": f"{ai1['amt']:.1f}",
    "AI_LB": ai["lb"], "AI_HY": ai["hy"],
    "AI_SHARE": f"{ai['amt'] / AMT_SUM * 100:.1f}",
    "AI_HY_LIST": "、".join(f"{k} {sum(1 for x in ai['list'] if x['hybk'] == k)}"
                          for k in sorted({x["hybk"] for x in ai["list"]},
                                          key=lambda h: -sum(1 for x in ai["list"] if x["hybk"] == h))),
    "CONS_N": cons["n"], "CONS_N_Y": cons1["n"], "CONS_AMT": f"{cons['amt']:.1f}",
    "CONS_LB": cons["lb"], "CONS_SHARE": f"{cons['amt'] / AMT_SUM * 100:.1f}",
    "CONS_SHARE_Y": f"{cons1['amt'] / AMT_SUM_Y * 100:.1f}",
    "MEDC_N": med["n"], "MEDC_N_Y": med1["n"], "MEDC_AMT": f"{med['amt']:.1f}", "MEDC_LB": med["lb"],
    "MEDC_SHARE": f"{med['amt'] / AMT_SUM * 100:.1f}",
})
_kw = [x for x in zt0 if any(k in ((ths0.get(x["c"]) or {}).get("reason_type") or "") for k in KW_PERF)]
V.update({"KW_N": len(_kw), "KW_PCT": f"{len(_kw) / ZT * 100:.0f}",
          "KW_LB": sum(1 for x in _kw if x["lbc"] >= 2),
          "KW_HY": len({x["hybk"] for x in _kw}),
          "KW_AMT": f"{sum(x['amount'] for x in _kw) / 1e8:.1f}",
          "KW_SHARE": f"{sum(x['amount'] for x in _kw) / 1e8 / AMT_SUM * 100:.1f}",
          "UNIQ_HY": len({x["hybk"] for x in zt0}),
          "BIG_N": len({x["c"] for x in zt0})})

_other = [x for x in zt0 if x["c"] not in {y["c"] for y in ai["list"] + cons["list"] + med["list"]}]
_rows = [
    ("AI 内容链（传媒 7 行业 + 软件 3 行业）", ai["n"], ai["amt"], ai["lb"], ai["hy"]),
    ("消费簇", cons["n"], cons["amt"], cons["lb"], len({x["hybk"] for x in cons["list"]})),
    ("医药簇", med["n"], med["amt"], med["lb"], len({x["hybk"] for x in med["list"]})),
    ("业绩簇（交叉计数，不参与合计）", len(_kw), sum(x["amount"] for x in _kw) / 1e8,
     sum(1 for x in _kw if x["lbc"] >= 2), len({x["hybk"] for x in _kw})),
    ("其余（AI/消费/医药之外）", len(_other), sum(x["amount"] for x in _other) / 1e8,
     sum(1 for x in _other if x["lbc"] >= 2), len({x["hybk"] for x in _other})),
]
_t = []
for nm, n, amt, lb, hy in _rows:
    _t.append("<tr><td>%s</td><td class='hl'>%d</td><td>%.1f</td><td>%.1f%%</td><td>%d</td><td>%d</td></tr>" % (
        nm, n, amt, amt / AMT_SUM * 100, lb, hy))
V["TBL_CLUSTER"] = "\n".join(_t)
V["OTHER_N"] = len(_other)
V["OTHER_LB"] = sum(1 for x in _other if x["lbc"] >= 2)
V["OTHER_AMT"] = f"{sum(x['amount'] for x in _other) / 1e8:.1f}"
V["OTHER_SHARE"] = f"{sum(x['amount'] for x in _other) / 1e8 / AMT_SUM * 100:.1f}"
V["OTHER_HY"] = len({x['hybk'] for x in _other})
V["DT_MEDIA_N"] = sum(1 for x in dt0 if x.get("hybk") in G_MEDIA)
V["DT_MEDIA_NAMES"] = "、".join(f"{x['n']}（{x['hybk']}）" for x in dt0 if x.get("hybk") in G_MEDIA) or "无"
_worst = min(dt0, key=lambda z: z.get("zdp") or 0)
V["DT_WORST_NAME"] = _worst["n"]
V["DT_WORST_PCT"] = f"{_worst['zdp']:+.2f}"
V["DT_WORST_AMT"] = f"{(_worst.get('amount') or 0) / 1e8:.2f}"
_t3 = sorted(zt0, key=lambda z: -z["amount"])[:3]
V["TOP3_AMT_NAMES"] = "、".join(f"{x['n']}（{x['hybk']}）" for x in _t3)
_ai3 = sorted(ai["list"], key=lambda z: -z["amount"])[:3]
V["AI3_AMT_NAMES"] = "、".join(f"{x['n']}（{x['amount'] / 1e8:.1f} 亿）" for x in _ai3)
V["AI_CONS_MED_N"] = ai["n"] + cons["n"] + med["n"]
V["POOL_N"] = len(zt0)
assert V["AI_CONS_MED_N"] + len(_other) == len(zt0), "簇只数不闭合"
assert len(zt0) + (ZT - len(zt0)) == ZT

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
_r7 = [b["continuous_plate_num"] / b["limit_up_num"] * 100 for b in blk[:7] if b["limit_up_num"]]
V["CONC_TOP7_MAX_R"] = f"{max(_r7):.1f}"
V["CONC_TOP7_MAX_BK"] = blk[_r7.index(max(_r7))]["name"]
V["CONC_TOP1_N_Y"] = (_bd1.get(_b1["name"]) or {}).get("limit_up_num", 0)


def conc(name, src=None):
    b = (src or _bd).get(name) or {}
    n, l = b.get("limit_up_num", 0), b.get("continuous_plate_num", 0)
    return n, l, (l / n * 100 if n else 0)


for key, nm in [("CONC_AI", "人工智能"), ("CONC_AIGC", "AIGC概念"), ("CONC_SHORT", "短剧游戏"),
                ("CONC_IP", "IP经济(谷子经济)"), ("CONC_MEDIA", "文化传媒概念")]:
    n, l, r = conc(nm)
    n1, l1, r1 = conc(nm, _bd1)
    V.update({key + "_N": n, key + "_LB": l, key + "_R": f"{r:.1f}", key + "_N_Y": n1, key + "_LB_Y": l1,
              key + "_R_Y": f"{r1:.1f}"})

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
for h, k in [("广告营销", "HY_GG"), ("出版", "HY_CB"), ("影视院线", "HY_YS"), ("游戏Ⅱ", "HY_YX"),
             ("IT服务Ⅱ", "HY_IT"), ("软件开发", "HY_RJ"), ("数字媒体", "HY_SZ"), ("白酒Ⅱ", "HY_BJ"),
             ("一般零售", "HY_LS"), ("汽车零部", "HY_QC"), ("元件", "HY_YJ")]:
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

SB_M, LB_M = median([p["pct"] for p in _sb]), median([p["pct"] for p in _lbv])
GAP = SB_M - LB_M
_sb1 = [p for p in S1["perf"] if p["lbc"] == 1]
_lb1 = [p for p in S1["perf"] if p["lbc"] >= 2]
GAP_Y = median([p["pct"] for p in _sb1]) - median([p["pct"] for p in _lb1])
V.update({"GAP_S_M": f2(SB_M), "GAP_L_M": f2(LB_M), "GAP": f"{GAP:+.2f}",
          "SB_MEAN": f2(mean([p["pct"] for p in _sb])), "LB_MEAN": f2(mean([p["pct"] for p in _lbv])),
          "SB_DN": sum(1 for p in _sb if p["pct"] < 0),
          "LB_SB": sum(1 for p in _lbv if p["pct"] < 0),
          "GAP_Y": f"{GAP_Y:+.2f}", "GAP_SWING": f"{abs(GAP - GAP_Y):.2f}",
          "GAP_Y_ABS": f"{abs(GAP_Y):.2f}", "GAP_ABS": f"{abs(GAP):.2f}",
          "GAP_SIGN": "连板强" if GAP < 0 else "首板强",
          "GAP_SIGN_Y": "连板强" if GAP_Y < 0 else "首板强",
          "GAP_S_M_Y": f2(median([p['pct'] for p in _sb1])), "GAP_L_M_Y": f2(median([p['pct'] for p in _lb1]))})
assert len(_sb1) + len(_lb1) == len(S1["perf"]), "昨日分组计数不闭合"

_t = []
for nm, g in [("全部", perf), ("昨日首板", _sb), ("昨日连板", _lbv)]:
    vs = [p["pct"] for p in g]
    _t.append("<tr><td>%s</td><td>%d</td><td>%d（%.1f%%）</td><td class='%s'>%s</td><td class='hl'>%s</td><td>%d</td></tr>" % (
        nm, len(g), sum(1 for p in g if p["again"]), sum(1 for p in g if p["again"]) / len(g) * 100,
        "up" if mean(vs) > 0 else "down", f2(mean(vs)), f2(median(vs)), sum(1 for v in vs if v < 0)))
V["TBL_PERF"] = "\n".join(_t)
_srt = sorted(perf, key=lambda x: x["pct"])
V["PERF_BOT"] = "、".join(f"{p['name']} {p['pct']:+.2f}%（昨{p['lbc']}板）" for p in _srt[:5])
V["PERF_TOP"] = "、".join(f"{p['name']} {p['pct']:+.2f}%（昨{p['lbc']}板）" for p in _srt[-5:][::-1])
V["PERF_BOT1"] = f"{_srt[0]['pct']:+.2f}%"
JS_PF = {"names": [p["name"] for p in _srt], "vals": [round(p["pct"], 2) for p in _srt]}

# ================= 昨跌停池今日去向（本日核心） =================
QP = os.path.join(OUT, f"_qdt{D1[4:]}.json")
assert os.path.exists(QP), f"缺少 {QP}"
Q = json.load(open(QP, encoding="utf-8"))
dt1c = [x["c"] for x in dt1]
vals = [Q[c]["pct"] for c in dt1c if c in Q]
assert len(vals) == len(dt1c) == 82, f"昨跌停池报价不全 {len(vals)}/{len(dt1c)}"
inter_c = sorted({x["code"] for x in A0["ths_zt"]["info"]} & set(dt1c))
V.update({
    "REL_MEAN": f2(mean(vals)), "REL_MED": f2(median(vals)),
    "REL_UP": sum(1 for v in vals if v > 0),
    "REL_DT": sum(1 for v in vals if v <= -9.8),
    "REL_BIG": sum(1 for v in vals if v > 5),
    "REL_N": len(vals),
    "REL_UP_PCT": f"{sum(1 for v in vals if v > 0) / len(vals) * 100:.0f}",
    "INTER_N": len(inter_c),
    "INTER_PCT": f"{len(inter_c) / len(dt1c) * 100:.1f}",
    "INTER_NAMES": "、".join(Q[c]["name"] for c in inter_c if c in Q),
    "REL_DT_PCT": f"{sum(1 for v in vals if v <= -9.8) / len(vals) * 100:.0f}",
})
# 传媒系 vs 非传媒 分层
_m1 = [x for x in dt1 if x["hybk"] in G_MEDIA]
_m1v = [Q[x["c"]]["pct"] for x in _m1 if x["c"] in Q]
_nm1 = [x for x in dt1 if x["hybk"] not in G_MEDIA]
_nm1v = [Q[x["c"]]["pct"] for x in _nm1 if x["c"] in Q]
_inter_m = [x for x in _m1 if x["c"] in {y["code"] for y in A0["ths_zt"]["info"]}]
V.update({
    "D1M_N": len(_m1), "D1M_MEAN": f2(mean(_m1v)), "D1M_MED": f2(median(_m1v)),
    "D1M_UP": sum(1 for v in _m1v if v > 0), "D1M_REB": len(_inter_m),
    "D1M_REB_R": f"{len(_inter_m) / len(_m1) * 100:.0f}",
    "D1NM_N": len(_nm1), "D1NM_MEAN": f2(mean(_nm1v)), "D1NM_MED": f2(median(_nm1v)),
    "D1NM_UP": sum(1 for v in _nm1v if v > 0),
    "D1NM_REB": sum(1 for x in _nm1 if x["c"] in {y["code"] for y in A0["ths_zt"]["info"]}),
    "D1M_REB_NAMES": "、".join(Q[x["c"]]["name"] for x in _inter_m if x["c"] in Q),
})
# 剔除反包 17 只后的残余
_rest = [Q[x["c"]]["pct"] for x in dt1 if x["c"] in Q and x["c"] not in set(inter_c)]
V.update({"REST_N": len(_rest), "REST_MEAN": f2(mean(_rest)), "REST_MED": f2(median(_rest)),
          "REST_UP": sum(1 for v in _rest if v > 0)})
# 昨跌停算力硬件
_c5 = [x for x in dt1 if x["hybk"] in G_CHIP]
_c5v = [Q[x["c"]]["pct"] for x in _c5 if x["c"] in Q]
V.update({"CHIP_N": len(_c5), "CHIP_MEAN": f2(mean(_c5v)) if _c5v else "—",
          "CHIP_UP": sum(1 for v in _c5v if v > 0), "CHIP_DN": sum(1 for v in _c5v if v < 0),
          "CHIP_LIST": "、".join(f"{Q[x['c']]['name']} {Q[x['c']]['pct']:+.1f}%" for x in _c5 if x["c"] in Q)})

# 今日跌停池
DT_AMT = sum(x.get("amount") or 0 for x in dt0) / 1e8
DT_AMT_Y = sum(x.get("amount") or 0 for x in dt1) / 1e8
V.update({"DT_AMT": f"{DT_AMT:.1f}", "DT_AMT_YD": f"{DT_AMT_Y:.1f}",
          "DT_RATIO": f"{DT_AMT / AMT_SUM:.2f}", "DT_RATIO_Y": f"{DT_AMT_Y / AMT_SUM_Y:.2f}",
          "DT_POOL_N": len(dt0), "DT_YD_N": len(dt1), "DT_X_AMT": f"{DT_AMT_Y / DT_AMT:.0f}",
          "DT_HY_N": len({x.get("hybk") for x in dt0}),
          "DT_BIG_N": sum(1 for x in dt0 if (x.get("ltsz") or 0) > 100e8),
          "DT_MED_AMT": f"{median([(x.get('amount') or 0) for x in dt0]) / 1e8:.2f}",
          "DT_MED_LTSZ": f"{median([(x.get('ltsz') or 0) for x in dt0]) / 1e8:.0f}",
          "DT_DIFF_N": len(dt0) - DT, "DT_Y_RAW": s1["dt"]})
_t = []
for x in sorted(dt0, key=lambda z: -(z.get("amount") or 0)):
    _t.append("<tr><td>%s</td><td>%s</td><td class='down'>%.2f%%</td><td>%.2f</td><td>%.0f</td></tr>" % (
        x["n"], x.get("hybk"), x.get("zdp") or 0, (x.get("amount") or 0) / 1e8, (x.get("ltsz") or 0) / 1e8))
V["TBL_DT_ALL"] = "\n".join(_t)
_dtop = max(dt0, key=lambda z: z.get("amount") or 0)
V["DT_TOP_NAME"] = _dtop["n"]
V["DT_TOP_HY"] = _dtop["hybk"]
V["DT_TOP_LTSZ"] = f"{(_dtop.get('ltsz') or 0) / 1e8:.0f}"
V["DT_TOP_AMT"] = f"{(_dtop.get('amount') or 0) / 1e8:.2f}"
V["DT_TOP_SHARE"] = f"{(_dtop.get('amount') or 0) / sum(x.get('amount') or 0 for x in dt0) * 100:.0f}"
JS_DT = {"names": [x["n"] for x in sorted(dt0, key=lambda z: (z.get("amount") or 0))],
         "vals": [round((x.get("amount") or 0) / 1e8, 2) for x in sorted(dt0, key=lambda z: (z.get("amount") or 0))],
         "hy": [x.get("hybk") for x in sorted(dt0, key=lambda z: (z.get("amount") or 0))]}

# 昨涨停 -> 今跌停
_dtset = {x["c"] for x in dt0}
V["ATK_DT_N"] = sum(1 for p in perf if p["code"] in _dtset)
V["ATK_DT_PCT"] = f"{V['ATK_DT_N'] / len(perf) * 100:.0f}"
V["DT_CONT_N"] = len({x["c"] for x in dt0} & {x["c"] for x in dt1})
V["DT_CONT_NAMES"] = "、".join(x["n"] for x in dt0 if x["c"] in {y["c"] for y in dt1}) or "无"

# 昨日一字板今日去向（观察点⑤）
V["YZ_ANS"] = "第 4 次兑现（开板即跌停）" if YZ_DT else "没有第 4 次兑现"

# ================= westock 三口径 =================
SWP = os.path.join(OUT, f"_sw{D0[4:]}.json")
SW = json.load(open(SWP, encoding="utf-8"))
assert SW, "westock 榜为空"


def sw_out(nm):
    v = SW.get(nm)
    return f2(v["pct"]) if v else "—"


def sw_up(nm):
    v = (SW.get(nm) or {}).get("updown") or ""
    return v if "/" in v else "—"


def sw_flow(nm):
    v = SW.get(nm)
    return f"{v['flow'] / 10000:+.1f}" if v else "—"


_rows = [("申万二级", "广告营销", "广告营销"), ("申万二级", "出版", "出版"), ("申万二级", "影视院线", "影视院线"),
         ("申万二级", "游戏Ⅱ", "游戏Ⅱ"), ("申万二级", "数字媒体", "数字媒体"), ("申万二级", "软件开发", "软件开发"),
         ("申万二级", "IT 服务", "IT服务Ⅱ"), ("申万二级", "半导体", "半导体"), ("申万二级", "元件", "元件"),
         ("申万二级", "通信设备", "通信设备"),
         ("申万二级·对照", "白酒Ⅱ", "白酒Ⅱ"), ("申万二级·对照", "一般零售", "一般零售"),
         ("申万二级·对照", "汽车零部", "汽车零部"), ("申万二级·对照", "化学制品", "化学制品"),
         ("申万二级·对照", "光伏设备", "光伏设备"),
         ("概念·对照", "银行概念", "银行概念"), ("概念·对照", "煤炭开采", "煤炭开采")]
_t = []
for src, nm, key in _rows:
    v = SW.get(key) or {}
    _t.append("<tr><td>%s</td><td>%s</td><td class='%s'>%s%%</td><td>%s</td><td class='%s'>%s</td></tr>" % (
        src, nm, "up" if v.get("pct", 0) > 0 else "down", f2(v.get("pct", 0)),
        (v.get("updown") or "—"), "up" if v.get("flow", 0) > 0 else "down", f"{v.get('flow', 0) / 10000:+.1f}"))
V["TBL_SW"] = "\n".join(_t)
for nm, key in [("广告营销", "SW_GG"), ("出版", "SW_CB"), ("影视院线", "SW_YS"), ("游戏Ⅱ", "SW_YX"),
                ("数字媒体", "SW_SZ"), ("软件开发", "SW_RJ"), ("IT服务Ⅱ", "SW_IT"),
                ("半导体", "SW_BDT"), ("元件", "SW_YJ"), ("白酒Ⅱ", "SW_BJ"),
                ("银行概念", "SW_BANK"), ("汽车零部", "SW_QC")]:
    V[key] = sw_out(nm)
    V[key + "_UP"] = sw_up(nm)
    V[key + "_FLOW"] = sw_flow(nm)

# ================= 口径 =================
_bj = [x for x in zt_all if x["c"].startswith("92")]
V["BJ_N"] = len(_bj)
V["BJ_CODES"] = "、".join(f"{x['n']}（{x['c']}）" for x in _bj) or "无"
V["EM_ZT_N"] = len(zt0_em)
_DIFS = sorted({x["c"] for x in zt_all} - {x["c"] for x in zt0})
_bad = [c for c in _DIFS if not c.startswith("92")]
assert not _bad, f"东财差额里出现无法归因的沪深代码：{_bad}"
V["THS_ZT_N"] = len(A0["ths_zt"]["info"])

# ================= JS =================
JS_SENTI = {"days": [x["d"] for x in days], "zt": [x["zt"] for x in days],
            "dt": [x["dt"] for x in days], "seal": [round(x["seal"], 1) for x in days]}
JS_INTRA = {"names": [x["nm"] for x in INTRA], "gap": [round(x["gap"], 2) for x in INTRA],
            "high": [round(x["high"], 2) for x in INTRA], "close": [round(x["close"], 2) for x in INTRA]}
JS_AMT = {"names": [x["name"] for x in ix], "yoy": [None if x["yoy"] is None else round(x["yoy"], 1) for x in ix]}
JS_TS = {"labels": [k for k, _ in _order], "today": [tm.get(k, 0) for k, _ in _order],
         "prev": [ty.get(k, 0) for k, _ in _order]}
JS_CLUSTER = {"names": ["AI 内容链", "消费", "医药", "其余"],
              "amt": [round(ai["amt"], 1), round(cons["amt"], 1), round(med["amt"], 1),
                      round(AMT_SUM - ai["amt"] - cons["amt"] - med["amt"], 1)],
              "n": [ai["n"], cons["n"], med["n"], len(_other)]}
JS_REL = {"labels": ["昨跌停传媒系", "昨跌停非传媒"], "vals": [round(mean(_m1v), 2), round(mean(_nm1v), 2)],
          "n": [len(_m1v), len(_nm1v)], "reb": [len(_inter_m), V["D1NM_REB"]]}
for k, v in [("JS_SENTI", JS_SENTI), ("JS_INTRA", JS_INTRA), ("JS_AMT", JS_AMT), ("JS_LAD", JS_LAD),
             ("JS_CONC", JS_CONC), ("JS_CLUSTER", JS_CLUSTER), ("JS_HY", JS_HY), ("JS_PF", JS_PF),
             ("JS_REL", JS_REL), ("JS_TS", JS_TS), ("JS_FUND", JS_FUND), ("JS_DT", JS_DT)]:
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
print("saved ->", rp, len(out), "chars")

for k in ["ZT", "ZT_Y", "TOUCH", "SEAL", "SEAL_Y", "DT", "DT_Y", "DTOUCH", "DSEAL", "AMT", "AMT_PCT",
          "N_UP", "AMT_UP_N", "AMT_DN_N", "N_BELOW_OPEN", "N_GAP_DN", "ADV_RATE", "PERF_MED", "GAP",
          "GAP_Y", "AI_N", "AI_LB", "AI_AMT", "AI_SHARE", "MEDIA_N", "CONS_N", "CONS_LB", "INTER_N",
          "INTER_PCT", "D1M_REB", "D1M_MEAN", "D1NM_MEAN", "REST_MEAN", "REL_MEAN", "REL_MED",
          "SHARE", "SHARE_Y", "ZB_SEALED_N", "ZB_ZERO_STREAK", "ATK_DT_N", "LB", "SHOU_PCT",
          "MAXB", "MAXB_NAME", "ZT_HIST_MAX", "ZT_NEW_HIGH"]:
    print("  %-14s %s" % (k, V.get(k)))
