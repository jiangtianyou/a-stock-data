# -*- coding: utf-8 -*-
"""涨停复盘报告 20261103 vs 20261102（跌停潮反包脉冲后的回吐日 · 算力硬件链定向清算 · 高低切换）
用法：python scripts/zt_report_20261103.py 20261103
输入：out/zt_stats_20261103.json、out/zt_review_20261103.json、out/zt_review_20261102.json、out/zt_review_20261030.json
     跌停明细 out/_dt1103.json / out/_dt1102.json；昨跌停股今日行情 out/_qdt1102.json；westock 榜 out/_sw1103.json
输出：reports/涨停复盘对比-20261103.html
"""
import json, os, sys, re, glob, time, urllib.request
from statistics import mean, median

ROOT = os.environ.get("ZT_ROOT") or os.getcwd()
OUT = os.path.join(ROOT, "out")
REP = os.path.join(ROOT, "reports")
TPL = os.path.join(ROOT, "scripts", "_report_tpl_20261103.html")
os.makedirs(REP, exist_ok=True)

D0 = sys.argv[1] if len(sys.argv) > 1 else "20261103"
S = json.load(open(os.path.join(OUT, f"zt_stats_{D0}.json"), encoding="utf-8"))
D0, D1, D2 = S["D0"], S["D1"], S["D2"]
B = json.load(open(os.path.join(OUT, f"zt_review_{D0}.json"), encoding="utf-8"))
B1 = json.load(open(os.path.join(OUT, f"zt_review_{D1}.json"), encoding="utf-8"))
B2 = json.load(open(os.path.join(OUT, f"zt_review_{D2}.json"), encoding="utf-8"))
S1 = json.load(open(os.path.join(OUT, f"zt_stats_{D1}.json"), encoding="utf-8"))
perf = S["perf"]
s0, s1 = S["senti"][D0], S["senti"][D1]
A0, A1, A2 = B["dates"][D0], B["dates"][D1], B2["dates"][D2]

WEEK = {0: "一", 1: "二", 2: "三", 3: "四", 4: "五", 5: "六", 6: "日"}


def md(ds):
    import datetime
    d = datetime.date(int(ds[:4]), int(ds[4:6]), int(ds[6:8]))
    return f"{d.month}/{d.day:02d}", WEEK[d.weekday()]


def f1(v):
    return f"{v:+.1f}"


def f2(v):
    return f"{v:+.2f}"


def hhmm(v):
    s = str(int(v)).zfill(6)
    return s[:2] + ":" + s[2:4]


V = {}
for tag, ds in [("D0", D0), ("D1", D1), ("D2", D2)]:
    lab, wk = md(ds)
    V[tag + "_LABEL"] = lab
    V[tag + "_WEEK"] = "周" + wk
    V[tag + "_FULL"] = f"{ds[:4]}-{ds[4:6]}-{ds[6:8]}"
    V[tag + "_CN"] = f"{ds[:4]}-{ds[4:6]}-{ds[6:8]}"
V["NEXT_D"] = "11/4 周三"
import time as _t
V["GEN_TIME"] = _t.strftime("%Y-%m-%d %H:%M")


def pool(zn, key):
    return (zn.get(key) or {}).get("pool") or []


ths0 = {x["code"]: x for x in A0["ths_zt"]["info"]}
ths1 = {x["code"]: x for x in A1["ths_zt"]["info"]}
zt_all = pool(A0, "em_ZT")
zt0 = [x for x in zt_all if not x["c"].startswith("92") and x["c"] in ths0]
zt0_em = [x for x in zt_all if not x["c"].startswith("92")]
zt1 = [x for x in pool(A1, "em_ZT") if not x["c"].startswith("92") and x["c"] in ths1]
zb0 = pool(A0, "em_ZB")
zb1 = pool(A1, "em_ZB")


def load_dt(d):
    p = os.path.join(OUT, f"_dt{d[4:]}.json")
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8")).get("data", {}).get("pool") or []
    return []


dt0, dt1 = load_dt(D0), load_dt(D1)
assert len(dt0) == 17, f"今日跌停池 {len(dt0)} 只，与汇总字段不符"
assert len(dt1) == 8, f"昨日跌停池 {len(dt1)} 只，与汇总字段不符"

# 叙事/行业分组
HY_AI = ("出版", "影视院线", "数字媒体", "广告营销", "IT服务Ⅱ", "软件开发", "电视广播", "游戏Ⅱ")
G_CHIP = ("元件", "通信设备", "半导体", "通信服务", "其他电源", "塑料", "光学光电", "消费电子")

# ================= 情绪 =================
ZT, ZT_Y = s0["zt"], s1["zt"]
ZT_0 = A2["ths_zt"]["total"]["today"]["num"] if A2.get("ths_zt") else s1["zt_prev"]
TOUCH = A0["ths_zt"]["total"]["today"]["history_num"]
TOUCH_Y = A1["ths_zt"]["total"]["today"]["history_num"]
ZB = len(zb0)
ZB_Y = len(zb1)
# 封板率统一取同花顺官方 rate（= 涨停 / 触及涨停），保证跨日可比
SEAL = A0["ths_zt"]["total"]["today"]["rate"] * 100
SEAL_Y = A1["ths_zt"]["total"]["today"]["rate"] * 100
_dc0 = A0["ths_zt"]["limit_down_count"]["today"]
_dc1 = A1["ths_zt"]["limit_down_count"]["today"]
DT, DT_Y = _dc0["num"], _dc1["num"]
DTOUCH, DTOUCH_Y = _dc0["history_num"], _dc1["history_num"]
DSEAL, DSEAL_Y = _dc0["rate"] * 100, _dc1["rate"] * 100
DT_OPEN_N = DTOUCH - DT
DT_0 = A2["ths_zt"]["limit_down_count"]["today"]["num"]
assert TOUCH >= ZT and TOUCH_Y >= ZT_Y, "触及涨停 < 涨停家数，字段错位"
assert DT <= DTOUCH, "跌停 > 触及跌停，字段错位"

V.update({
    "ZT": ZT, "ZT_Y": ZT_Y, "ZT_0": ZT_0, "ZT_D": f"{ZT - ZT_Y:+d}",
    "ZT_PCT_D": f"{(ZT / ZT_Y - 1) * 100:+.0f}",
    "TOUCH": TOUCH, "TOUCH_Y": TOUCH_Y, "TOUCH_D": f"{TOUCH - TOUCH_Y:+d}",
    "TOUCH_PCT_D": f"{(TOUCH / TOUCH_Y - 1) * 100:+.0f}",
    "TOUCH_GAP": TOUCH - ZT,
    "SEAL": f"{SEAL:.1f}", "SEAL_Y": f"{SEAL_Y:.1f}", "SEAL_D": f"{SEAL - SEAL_Y:+.1f}",
    "SEAL_FAIL": f"{(1 - ZT / TOUCH) * 100:.1f}", "SEAL_FAIL_Y": f"{(1 - ZT_Y / TOUCH_Y) * 100:.1f}",
    "DT": DT, "DT_Y": DT_Y, "DT_0": DT_0, "DT_Y_LEGACY": DT_0, "DT_D": f"{DT - DT_Y:+d}",
    "DT_X": f"{DT / DT_Y:.1f}", "DT_PCT_D": f"{abs((DT / DT_Y - 1) * 100):.0f}",
    "DTOUCH": DTOUCH, "DTOUCH_Y": DTOUCH_Y, "DTOUCH_D": f"{DTOUCH - DTOUCH_Y:+d}",
    "DSEAL": f"{DSEAL:.1f}", "DSEAL_Y": f"{DSEAL_Y:.1f}", "DSEAL_D": f"{DSEAL - DSEAL_Y:+.1f}",
    "DT_OPEN_N": DT_OPEN_N, "DT_REBUY": f"{DT_OPEN_N / DTOUCH * 100:.1f}",
    "ZB": ZB, "ZB_Y": ZB_Y, "ZB_D": f"{ZB - ZB_Y:+d}",
})

# 三日阶梯
days = [
    {"d": md(D2)[0], "zt": ZT_0, "zb": len(pool(A2, "em_ZB")), "dt": DT_0,
     "touch": A2["ths_zt"]["total"]["today"]["history_num"],
     "dtouch": A2["ths_zt"]["limit_down_count"]["today"]["history_num"]},
    {"d": md(D1)[0], "zt": ZT_Y, "zb": ZB_Y, "dt": DT_Y, "touch": TOUCH_Y, "dtouch": DTOUCH_Y},
    {"d": md(D0)[0], "zt": ZT, "zb": ZB, "dt": DT, "touch": TOUCH, "dtouch": DTOUCH},
]
for x in days:
    x["seal"] = x["zt"] / x["touch"] * 100 if x["touch"] else 0.0
assert days[0]["dt"] != days[1]["dt"], "D2 列跌停与 D1 相同，取错文件"
assert days[0]["zt"] != days[1]["zt"], "D2 列涨停与 D1 相同，取错文件"

V["ZTDT"] = f"{ZT / DT:.1f}"
V["ZTDT_Y"] = f"{ZT_Y / DT_Y:.1f}"
V["ZTDT_0"] = f"{days[0]['zt'] / days[0]['dt']:.1f}" if days[0]["dt"] else "—"

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
    _tbl.append("<tr><td>%s</td><td>%s</td><td>%s</td><td class='hl'>%s</td><td>%s</td></tr>" % (
        nm, cells[0], cells[1], cells[2], chg))
V["TBL_SENTI"] = "\n".join(_tbl)

# ================= 指数 =================
IX_ORDER = ["上证指数", "深证成指", "创业板指", "科创50", "沪深300", "中证500",
            "中证1000", "国证2000", "上证50", "中小100", "北证50"]
i0 = {v["name"]: v for v in B["indexes"].values() if isinstance(v, dict) and v.get("name")}
i1 = {v["name"]: v for v in B1["indexes"].values() if isinstance(v, dict) and v.get("name")}
i2 = {v["name"]: v for v in B2["indexes"].values() if isinstance(v, dict) and v.get("name")}
TOT, TOT_Y = S["tot"]["today"], S["tot"]["prev"]
V["AMT"], V["AMT_Y"] = f"{TOT:.0f}", f"{TOT_Y:.0f}"
V["AMT_D"] = f"{TOT - TOT_Y:+.0f}"
AMT_PCT = (TOT / TOT_Y - 1) * 100
V["AMT_PCT"] = f1(AMT_PCT)

ix = []
for nm in IX_ORDER:
    v, p = i0.get(nm) or {}, i1.get(nm) or {}
    a0 = (v.get("amount_wan") or 0) / 10000.0
    a1v = (p.get("amount_wan") or 0) / 10000.0
    i2v = i2.get(nm) or {}
    a2v = (i2v.get("amount_wan") or 0) / 10000.0
    ix.append({"name": nm, "pct": v.get("pct") or 0.0, "amt": a0, "prev_pct": p.get("pct"),
               "yoy": ((a0 / a1v - 1) * 100) if a1v else None,
               "yoy_y": ((a1v / a2v - 1) * 100) if a2v else None})
V["AMT_UP_N"] = sum(1 for x in ix if (x["yoy"] or 0) > 0)
V["AMT_DN_N"] = sum(1 for x in ix if (x["yoy"] or 0) < 0)
V["N_UP"] = sum(1 for x in ix if x["pct"] > 0)
V["N_DN"] = sum(1 for x in ix if x["pct"] < 0)
_yoyv = [x["yoy"] for x in ix if x["yoy"] is not None]
V["YOY_MIN"] = f"{min(_yoyv):.1f}"
V["YOY_MAX"] = f"{max(_yoyv):.1f}"

_up = sorted([x for x in ix if (x["yoy"] or 0) > 0], key=lambda z: -z["yoy"])
_dn = sorted([x for x in ix if (x["yoy"] or 0) < 0], key=lambda z: z["yoy"])
V["YOY_MAX_NAME"] = _up[0]["name"] if _up else "—"
V["YOY_MIN_NAME"] = _dn[0]["name"] if _dn else "—"
V["YOY_UP_TXT"] = "、".join(f"{x['name']} {x['yoy']:+.1f}%" for x in _up)
V["YOY_DN_TXT"] = "、".join(f"{x['name']} {x['yoy']:+.1f}%" for x in _dn)
V["YOY_UP_PCT_TXT"] = "、".join(f"{x['name']} {x['pct']:+.2f}%" for x in _up)
V["YOY_DN_PCT_TXT"] = "、".join(f"{x['name']} {x['pct']:+.2f}%" for x in _dn)

# 日内 OHLC（腾讯日线，显式日期）
OHLC = {}
_op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
for nm, sym in [("上证指数", "sh000001"), ("深证成指", "sz399001"), ("创业板指", "sz399006"),
                ("科创50", "sh000688"), ("国证2000", "sz399303"), ("上证50", "sh000016")]:
    u = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=" + sym + ",day,,,12,qfq"
    for _try in range(4):
        try:
            d = json.loads(_op.open(u, timeout=25).read().decode("utf-8"))["data"][sym]
            rows = d.get("day") or d.get("qfqday")
            cur = [r for r in rows if r[0].replace("-", "") == D0][0]
            pre = [r for r in rows if r[0].replace("-", "") < D0][-1]
            OHLC[nm] = {"open": float(cur[1]), "close": float(cur[2]), "high": float(cur[3]),
                        "low": float(cur[4]), "prev": float(pre[2])}
            break
        except Exception as e:
            print("warn: 日线抓取失败", nm, _try, e)
            time.sleep(1.2)
assert len(OHLC) == 6, f"日内 OHLC 只拿到 {len(OHLC)} 个指数"

INTRA = []
for nm in ["上证指数", "深证成指", "创业板指", "科创50", "国证2000", "上证50"]:
    o = OHLC[nm]
    INTRA.append({"nm": nm, "gap": (o["open"] / o["prev"] - 1) * 100, "high": (o["high"] / o["prev"] - 1) * 100,
                  "low": (o["low"] / o["prev"] - 1) * 100, "close": (o["close"] / o["prev"] - 1) * 100})
V["N_BELOW_OPEN"] = sum(1 for x in INTRA if x["close"] < x["gap"])
V["N_ABOVE_OPEN"] = len(INTRA) - V["N_BELOW_OPEN"]
V["N_INTRA"] = len(INTRA)
V["N_GAP_UP"] = sum(1 for x in INTRA if x["gap"] > 0)
for key, nm in [("SH", "上证指数"), ("CY", "创业板指"), ("KC", "科创50"),
                ("GZ", "国证2000"), ("SH50", "上证50"), ("SZ", "深证成指")]:
    x = next((y for y in INTRA if y["nm"] == nm), None)
    if x:
        V[key + "_GAP"] = f2(x["gap"])
        V[key + "_HIGH"] = f2(x["high"])
        V[key + "_LOW"] = f2(x["low"])
        V[key + "_PCT"] = f2(x["close"])
        V[key + "_DRAW"] = f"{x['close'] - x['high']:.2f}"
for key, nm in [("CY", "创业板指"), ("KC", "科创50"), ("SH50", "上证50"), ("HS300", "沪深300"),
                ("SZ", "深证成指"), ("BJ", "北证50"), ("ZX100", "中小100"), ("SH", "上证指数"),
                ("ZZ500", "中证500"), ("ZZ1000", "中证1000"), ("GZ", "国证2000")]:
    r = next((y for y in ix if y["name"] == nm), None)
    if r:
        V[key + "_YOY"] = f1(r["yoy"] or 0)
        V[key + "_YOY_Y"] = f1(r["yoy_y"] or 0)
        V[key + "_AMT"] = f"{r['amt']:.0f}"
        V[key + "_IDX_PCT"] = f2(r["pct"])
for key, nm in [("SH50", "上证50"), ("KC", "科创50"), ("CY", "创业板指"), ("SH", "上证指数")]:
    V[key + "_PCT_Y"] = f2((i1.get(nm) or {}).get("pct") or 0)

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
LB = sum(v for k, v in lad0.items() if k >= 2)
LB_Y = sum(v for k, v in lad1.items() if k >= 2)
SHOU, SHOU_Y = lad0.get(1, 0), lad1.get(1, 0)
V.update({"MAXB": MAXB, "MAXB_Y": MAXB_Y, "LB": LB, "LB_Y": LB_Y, "LB_D": f"{LB - LB_Y:+d}",
          "SHOU": SHOU, "SHOU_Y": SHOU_Y,
          "SHOU_PCT": f"{SHOU / ZT * 100:.1f}", "SHOU_PCT_Y": f"{SHOU_Y / ZT_Y * 100:.1f}",
          "SHOU_DN_PCT": f"{(1 - SHOU / SHOU_Y) * 100:.0f}",
          "LAD2": lad0.get(2, 0), "LAD3": lad0.get(3, 0), "LAD4": lad0.get(4, 0),
          "LAD2_Y": lad1.get(2, 0), "LAD3_Y": lad1.get(3, 0), "LAD4_Y": lad1.get(4, 0),
          "LB_PCT": f"{LB / ZT * 100:.1f}", "LB_PCT_Y": f"{LB_Y / ZT_Y * 100:.1f}",
          "LB_PCT_D": f"{LB / ZT * 100 - LB_Y / ZT_Y * 100:+.1f}"})
_maxb = sorted([x for x in zt0 if x["lbc"] == MAXB], key=lambda z: -z["amount"])
V["MAXB_NAMES"] = "、".join(x["n"] for x in _maxb)
_mb = _maxb[0]
V.update({"MAXB_HY": "、".join(f"{x['n']}（{x['hybk']}）" for x in _maxb), "MAXB_FUND": f"{_mb['fund'] / 1e8:.2f}",
          "MAXB_AMT": f"{_mb['amount'] / 1e8:.2f}", "MAXB_FBT": hhmm(_mb["fbt"]),
          "MAXB_TYPE": (ths0.get(_mb["c"]) or {}).get("limit_up_type") or "换手板"})
V["LAD4_NAMES"] = "、".join(f"{x['n']}（{x['hybk']}）" for x in zt0 if x["lbc"] == 4)
_l2 = [x for x in zt0 if x["lbc"] == 2]
V["LAD2_AI"] = sum(1 for x in _l2 if x["hybk"] in HY_AI)
V["LAD2_OTHER"] = len(_l2) - V["LAD2_AI"]

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
for k, pref in [(2, "LAD2Y"), (3, "LAD3Y"), (4, "LAD4Y"), (6, "LAD6Y")]:
    g = by.get(k, [])
    V[pref + "_N"] = len(g)
    V[pref + "_NAMES"] = "、".join(f"{p['name']} {p['pct']:+.2f}%" for p in sorted(g, key=lambda z: -z["pct"])) or "无"

# ================= 涨停成交结构 =================
AMT_SUM = sum(x["amount"] for x in zt0) / 1e8
AMT_SUM_Y = sum(x["amount"] for x in zt1) / 1e8
FUND = sum(x["fund"] for x in zt0) / 1e8
FUND_Y = sum(x["fund"] for x in zt1) / 1e8
FUND_MED = median([x["fund"] for x in zt0]) / 1e8
FUND_MED_Y = median([x["fund"] for x in zt1]) / 1e8
AMT_MED = median([x["amount"] for x in zt0]) / 1e8
AMT_MED_Y = median([x["amount"] for x in zt1]) / 1e8
V.update({"AMT_SUM": f"{AMT_SUM:.1f}", "AMT_SUM_Y": f"{AMT_SUM_Y:.1f}",
          "AMT_SUM_PCT": f1((AMT_SUM / AMT_SUM_Y - 1) * 100),
          "FUND": f"{FUND:.1f}", "FUND_Y": f"{FUND_Y:.1f}",
          "FUND_MED": f"{FUND_MED:.2f}", "FUND_MED_Y": f"{FUND_MED_Y:.2f}",
          "AMT_MED": f"{AMT_MED:.2f}", "AMT_MED_Y": f"{AMT_MED_Y:.2f}",
          "SHARE": f"{AMT_SUM / TOT * 100:.2f}", "SHARE_Y": f"{AMT_SUM_Y / TOT_Y * 100:.2f}"})
ZT_BIG = [x for x in zt0 if (x.get("ltsz") or 0) > 1e10]
V["ZT_BIG_N"] = len(ZT_BIG)
V["ZT_BIG_NAMES"] = "、".join(f"{x['n']} {(x['ltsz'])/1e8:.0f}亿" for x in sorted(ZT_BIG, key=lambda z: -(z["ltsz"] or 0))) or "无"
V["ZT_HY_N"] = len({x["hybk"] for x in zt0})
V["ZT_HY_N_Y"] = len({x["hybk"] for x in zt1})

# ================= 跌停池 =================
DT_AMT = sum(x.get("amount", 0) for x in dt0) / 1e8
DT_AMT_Y = sum(x.get("amount", 0) for x in dt1) / 1e8
V.update({"DT_AMT": f"{DT_AMT:.1f}", "DT_AMT_Y": f"{DT_AMT_Y:.1f}",
          "DT_RATIO": f"{DT_AMT / AMT_SUM:.2f}", "DT_RATIO_Y": f"{DT_AMT_Y / AMT_SUM_Y:.2f}",
          "DT_EXTRA": f"{DT_AMT - AMT_SUM:.1f}"})


def chip_label(x):
    hy = x.get("hybk") or ""
    nm = x.get("n") or ""
    if hy in ("元件", "通信设备", "半导体", "通信服务", "其他电源"):
        return "算力硬件链"
    if hy == "塑料" and nm == "福莱新材":
        return "算力硬件链（电子级材料）"
    return "非算力链"


for x in dt0:
    x["_chip"] = chip_label(x)
CHIP = [x for x in dt0 if x["_chip"].startswith("算力")]
OTHER = [x for x in dt0 if not x["_chip"].startswith("算力")]
CHIP_AMT = sum(x.get("amount", 0) for x in CHIP) / 1e8
V.update({"DT_CHIP_N": len(CHIP), "DT_CHIP_AMT": f"{CHIP_AMT:.1f}",
          "DT_CHIP_SHARE": f"{CHIP_AMT / DT_AMT * 100:.0f}",
          "DT_CHIP_BIG": sum(1 for x in CHIP if (x.get("ltsz") or 0) > 1e10),
          "DT_CHIP_NAMES": "、".join(x["n"] for x in sorted(CHIP, key=lambda z: -(z.get("amount") or 0))) or "无",
          "DT_OTHER_N": len(OTHER),
          "DT_OTHER_NAMES": "、".join(x["n"] for x in OTHER) or "无"})
_dts = sorted(dt0, key=lambda z: -(z.get("amount") or 0))
_top6 = _dts[:6]
V["DT_TOP6_TXT"] = "、".join(f"{x['n']}（{x['hybk']}，成交 {x['amount']/1e8:.1f} 亿）" for x in _top6)
V["DT_TOP6_AMT"] = f"{sum(x['amount'] for x in _top6)/1e8:.1f}"
V["DT_TOP6_SHARE"] = f"{sum(x['amount'] for x in _top6)/1e8/DT_AMT*100:.0f}"
V["DT_TOP6_MV"] = " / ".join(f"{(x.get('ltsz') or 0)/1e8:.0f}" for x in _top6)

import collections
_hyc = collections.Counter(x.get("hybk") for x in dt0)
V["DT_YJ"] = _hyc.get("元件", 0)
V["DT_BDT"] = _hyc.get("半导体", 0)
V["DT_TX"] = _hyc.get("通信设备", 0)
V["DT_TXF"] = _hyc.get("通信服务", 0)
V["DT_DY"] = _hyc.get("其他电源", 0)
V["DT_SL"] = sum(1 for x in dt0 if x.get("hybk") == "塑料" and x["_chip"].startswith("算力"))

_t = []
for x in _dts:
    _t.append("<tr><td>%s</td><td>%s</td><td>%s</td><td class='%s'>%.1f</td><td>%.0f</td><td class='note'>%s</td></tr>" % (
        x["c"], x["n"], x.get("hybk"), "down", (x.get("amount") or 0) / 1e8,
        (x.get("ltsz") or 0) / 1e8, x["_chip"]))
V["TBL_DT"] = "\n".join(_t)

# 跌停池构成（图）：按链条/行业
_chain = collections.Counter()
_chainamt = collections.Counter()
for x in dt0:
    k = "算力硬件链" if x["_chip"].startswith("算力") else (x.get("hybk") or "其他")
    _chain[k] += 1
    _chainamt[k] += (x.get("amount") or 0) / 1e8
_ck = sorted(_chainamt.keys(), key=lambda k: _chainamt[k])
JS_DTCHAIN = {"labels": [f"{k}（{_chain[k]}只）" for k in _ck],
              "vals": [round(_chainamt[k], 1) for k in _ck],
              "colors": ["#12805c" if "算力" in k else "#94a3b8" for k in _ck]}

ZB_AMT = sum(x["amount"] for x in zb0) / 1e8
ZB_AMT_Y = sum(x["amount"] for x in zb1) / 1e8
V.update({"ZB_AMT": f"{ZB_AMT:.1f}", "ZB_AMT_Y": f"{ZB_AMT_Y:.1f}",
          "ZB_RATIO": f"{ZB_AMT / AMT_SUM:.2f}", "ZB_EXTRA": f"{ZB_AMT - AMT_SUM:.1f}",
          "ZB_MED_MV": f"{median([(x.get('ltsz') or 0) for x in zb0])/1e8:.0f}",
          "ZB_BIG_N": sum(1 for x in zb0 if (x.get("ltsz") or 0) > 1e10)})
_zbs = sorted(zb0, key=lambda z: -(z.get("ltsz") or 0))
V["ZB_TOP_TXT"] = "、".join(f"{x['n']}（{x['hybk']}，流通 {(x.get('ltsz') or 0)/1e8:.0f} 亿，收 {x['zdp']:+.2f}%）" for x in _zbs[:3])
_zmap = {x["c"]: x for x in zb0}
V["ZB_ZY_PCT"] = f"{_zmap.get('603533', {}).get('zdp', 0):.2f}"
V["ZB_ZX_PCT"] = f"{_zmap.get('600259', {}).get('zdp', 0):.2f}"

# 跌停/涨停/炸板成交对比图（三日）
JS_DTCMP = {"labels": [md(D2)[0], md(D1)[0], md(D0)[0]],
            "zt": [round(sum(x["amount"] for x in pool(A2, "em_ZT") if not x["c"].startswith("92")) / 1e8, 1),
                   round(AMT_SUM_Y, 1), round(AMT_SUM, 1)],
            "dt": [round(sum(x["amount"] for x in load_dt(D2)) / 1e8, 1), round(DT_AMT_Y, 1), round(DT_AMT, 1)],
            "zb": [round(sum(x["amount"] for x in pool(A2, "em_ZB")) / 1e8, 1), round(ZB_AMT_Y, 1), round(ZB_AMT, 1)]}

# ================= 昨日涨停股今日表现 =================
ADV_N = sum(1 for p in perf if p["again"])
V["ADV_N"], V["ADV_TOT"] = ADV_N, len(perf)
V["ADV_RATE"] = f"{ADV_N / len(perf) * 100:.1f}"
pcts = [p["pct"] for p in perf]
V["PERF_MEAN"] = f2(mean(pcts))
V["PERF_MED"] = f2(median(pcts))
V["PERF_DN_N"] = sum(1 for p in pcts if p < 0)
V["PERF_DN5_N"] = sum(1 for p in pcts if p <= -5)
_sp = sorted(perf, key=lambda z: -z["pct"])
V["PERF_TOP5"] = "；".join(f"{p['name']} {p['pct']:+.2f}%（{p['hybk']}）" for p in _sp[:5])
V["PERF_BOT5"] = "；".join(f"{p['name']} {p['pct']:+.2f}%（{p['hybk']}）" for p in _sp[-5:])
V["PERF_WEAK"] = f"{_sp[-1]['name']} {_sp[-1]['pct']:+.2f}%（{_sp[-1]['hybk']}）"
V["ADV_NAMES"] = "、".join(f"{p['name']}（{p['lbc']}板→{p['lbc']+1}板，{p['hybk']}）" for p in _sp if p["again"])
V["ATK_DT_N"] = 0
V["ATK_DT_NAMES"] = "无"

for pref, g in [("SB", [p for p in perf if p["lbc"] == 1]), ("LB", [p for p in perf if p["lbc"] >= 2])]:
    V[pref + "_N"] = len(g)
    V[pref + "_RATE"] = f"{sum(1 for p in g if p['again']) / len(g) * 100:.1f}"
    V[pref + "_MEAN"] = f2(mean([p["pct"] for p in g]))
    V[pref + "_MED"] = f2(median([p["pct"] for p in g]))
    V[pref + "_DN_N"] = sum(1 for p in g if p["pct"] < 0)
    V[pref + "_DN5_N"] = sum(1 for p in g if p["pct"] <= -5)
GAP = median([p["pct"] for p in perf if p["lbc"] == 1]) - median([p["pct"] for p in perf if p["lbc"] >= 2])
V["GAP"] = f"{GAP:+.2f}"
V["GAP_CLS"] = "up" if GAP > 0 else "down"
# 昨日 GAP：从 S1.perf 现算
_p1 = S1["perf"]
GAP_Y = median([p["pct"] for p in _p1 if p["lbc"] == 1]) - median([p["pct"] for p in _p1 if p["lbc"] >= 2])
V["GAP_Y"] = f"{GAP_Y:+.2f}"
_ai_perf = [p for p in perf if p["hybk"] in HY_AI]
V["AI_ADV"] = sum(1 for p in _ai_perf if p["again"])
V["AI_MED"] = f2(median([p["pct"] for p in _ai_perf]))
V["NONAI_ADV"] = ADV_N - V["AI_ADV"]

# PERF 直方图
_bins = [(-100, -9.5), (-9.5, -5), (-5, -2), (-2, 0), (0, 2), (2, 5), (5, 10), (10, 100)]
_lbls = ["跌停", "-9~-5", "-5~-2", "-2~0", "0~2", "2~5", "5~10", "涨停+"]
_cnt = [0] * len(_bins)
for p in pcts:
    for i, (a, b) in enumerate(_bins):
        if a <= p < b:
            _cnt[i] += 1
            break
JS_PERF = {"labels": _lbls, "vals": _cnt,
           "colors": ["#12805c", "#34a374", "#7fc7a8", "#c9e6d8", "#f6cfcb", "#eda09a", "#e5695f", "#d93025"]}

# ================= 昨日跌停股今日 =================
qdt1 = json.load(open(os.path.join(OUT, f"_qdt{D1[4:]}.json"), encoding="utf-8"))
_v = [(x["c"], x["n"], qdt1.get(x["c"], {}).get("pct")) for x in dt1 if qdt1.get(x["c"])]
_pv = [v[2] for v in _v]
V.update({"DT1_N": len(_v), "DT1_MEAN": f2(mean(_pv)), "DT1_MED": f2(median(_pv)),
          "DT1_UP": sum(1 for p in _pv if p > 0), "DT1_ZT": sum(1 for p in _pv if p >= 9.8),
          "DT1_WORST": f"{min(_pv):.2f}"})
_codes0 = {x["c"] for x in dt0}
V["DT1_CONT"] = sum(1 for c, n, p in _v if c in _codes0)
V["DT1_CONT_NAMES"] = "、".join(f"{n} {p:+.2f}%" for c, n, p in _v if c in _codes0) or "无"
V["INTER_N"] = len({x["c"] for x in zt0} & {x["c"] for x in dt1})

# ================= 主线 =================
REASON = {x["code"]: (x.get("reason") or "") for x in S["r0"]}


def rs(x):
    return REASON.get(x["c"]) or (ths0.get(x["c"]) or {}).get("reason_type") or ""

_ai0 = [x for x in zt0 if x["hybk"] in HY_AI]
_ai1 = [x for x in zt1 if x["hybk"] in HY_AI]
V.update({"AI_N": len(_ai0), "AI_N_Y": len(_ai1),
          "AI_AMT": f"{sum(x['amount'] for x in _ai0)/1e8:.1f}",
          "AI_AMT_Y": f"{sum(x['amount'] for x in _ai1)/1e8:.1f}",
          "AI_PCT": f"{(1 - len(_ai0)/len(_ai1))*100:.0f}% 的降幅" if _ai1 else "—",
          "AI_LB": sum(1 for x in _ai0 if x["lbc"] >= 2),
          "AI_LB_NAMES": "、".join(f"{x['n']} {x['lbc']}板" for x in _ai0 if x["lbc"] >= 2) or "无"})
_hyc0 = collections.Counter(x["hybk"] for x in zt0)
_hyc1 = collections.Counter(x["hybk"] for x in zt1)
for key, hy in [("HY_CB", "出版"), ("HY_YS", "影视院线"), ("HY_SZ", "数字媒体"), ("HY_GG", "广告营销"),
                ("HY_IT", "IT服务Ⅱ"), ("HY_RJ", "软件开发"), ("HY_DS", "电视广播"), ("HY_YX", "游戏Ⅱ"),
                ("HY_DC", "电池")]:
    V[key] = _hyc0.get(hy, 0)
V["HY_DC_Y"] = _hyc1.get("电池", 0)

# 锂电核心
LITH_KW = ("固态电池", "锂电", "磷酸铁锂", "电解液", "铝塑膜", "复合铜箔", "电池铝箔")
LITH = [x for x in zt0 if x["hybk"] == "电池" or any(k in rs(x) for k in LITH_KW)]
def _rs1(x):
    return (REASON.get(x["c"]) or (ths1.get(x["c"]) or {}).get("reason_type") or "")


LITH_Y = [x for x in zt1 if x["hybk"] == "电池" or any(k in _rs1(x) for k in LITH_KW)]
V.update({"LITH_Y_N": len(LITH_Y), "LITH_N": len(LITH), "LITH_AMT": f"{sum(x['amount'] for x in LITH)/1e8:.1f}",
          "LITH_LB": sum(1 for x in LITH if x["lbc"] >= 2),
          "LITH_SHOU": sum(1 for x in LITH if x["lbc"] == 1),
          "LITH_LB_NAMES": "、".join(f"{x['n']} {x['lbc']}板" for x in LITH if x["lbc"] >= 2) or "无"})

# 羊字辈
YANG = [x for x in zt0 if "羊" in rs(x) and "字辈" in rs(x)]
YANG_Y = [x for x in zt1 if "羊" in (REASON.get(x["c"]) or (ths1.get(x["c"]) or {}).get("reason_type") or "") and "字辈" in (REASON.get(x["c"]) or (ths1.get(x["c"]) or {}).get("reason_type") or "")]
YANG_AMT = sum(x["amount"] for x in YANG) / 1e8
V.update({"YANG_N": len(YANG), "YANG_AMT": f"{YANG_AMT:.1f}",
          "YANG_SHARE": f"{YANG_AMT / AMT_SUM * 100:.0f}",
          "YANG_NAMES": "、".join(x["n"] for x in sorted(YANG, key=lambda z: -z["amount"]))})

# 主线表
_t = []
_used0 = {x["c"] for x in _ai0} | {x["c"] for x in LITH} | {x["c"] for x in YANG}
_used1 = {x["c"] for x in _ai1} | {x["c"] for x in LITH_Y} | {x["c"] for x in YANG_Y}
_oth0 = [x for x in zt0 if x["c"] not in _used0]
_oth1 = [x for x in zt1 if x["c"] not in _used1]
for nm, g, g1 in [("AI 内容链（8 行业）", _ai0, _ai1), ("锂电 / 固态电池", LITH, LITH_Y),
                  ("「羊字辈」名称博弈", YANG, YANG_Y)]:
    a = sum(x["amount"] for x in g) / 1e8
    _t.append("<tr><td>%s</td><td>%d</td><td class='hl'>%d</td><td>%d</td><td>%.1f</td><td>%.1f%%</td></tr>" % (
        nm, len(g1), len(g), sum(1 for x in g if x["lbc"] >= 2), a, a / AMT_SUM * 100))
_oa = sum(x["amount"] for x in _oth0) / 1e8
_t.append("<tr><td>其他（分散）</td><td>%d</td><td>%d</td><td>%d</td><td>%.1f</td><td>%.1f%%</td></tr>" % (
    len(_oth1), len(_oth0), sum(1 for x in _oth0 if x["lbc"] >= 2), _oa, _oa / AMT_SUM * 100))
V["TBL_MAIN"] = "\n".join(_t)
JS_MAIN = {"labels": ["AI 内容链", "锂电/固态", "羊字辈", "其他"],
           "prev": [len(_ai1), len(LITH_Y), len(YANG_Y), len(_oth1)],
           "today": [len(_ai0), len(LITH), len(YANG), len(_oth0)]}

# 概念榜
tb0 = A0.get("ths_block") or []
tb1 = A1.get("ths_block") or []
_t = []
for x in tb0[:8]:
    n, c = x.get("limit_up_num") or 0, x.get("continuous_plate_num") or 0
    _t.append("<tr><td>%s</td><td>%d</td><td>%d</td><td class='%s'>%.0f%%</td><td class='note'>%s</td></tr>" % (
        x.get("name"), n, c, "up" if n and c / n >= 0.4 else "mut", (c / n * 100) if n else 0, x.get("high") or "—"))
V["TBL_CONC"] = "\n".join(_t)
_top7 = tb0[:7]
V["CONC_TOP7_MAX_R"] = f"{max((x.get('continuous_plate_num') or 0) / (x.get('limit_up_num') or 1) * 100 for x in _top7):.0f}"
_mx = max(_top7, key=lambda x: (x.get("continuous_plate_num") or 0) / (x.get("limit_up_num") or 1))
V["CONC_TOP7_MAX_BK"] = _mx.get("name")
GENERIC = ("一带一路", "西部大开发", "跨境电商", "新能源汽车", "乡村振兴", "三胎概念", "比亚迪概念",
           "宁德时代概念", "储能", "海峡两岸", "融资融券", "国企改革", "人工智能", "华为概念")
_gen = [x.get("name") for x in _top7 if x.get("name") in GENERIC]
V["CONC_TOP7_GENERIC"] = len(_gen)
V["CONC_GENERIC_NAMES"] = " / ".join(_gen) if _gen else "无"
V["CONC_TOP1"] = tb0[0].get("name")
V["CONC_TOP1_N"] = tb0[0].get("limit_up_num") or 0
V["CONC_TOP1_LB"] = tb0[0].get("continuous_plate_num") or 0
V["CONC_TOP1_R"] = f"{(tb0[0].get('continuous_plate_num') or 0)/(tb0[0].get('limit_up_num') or 1)*100:.0f}"
_cb0 = next((x for x in tb0 if x.get("name") == "文化传媒概念"), None)
_cb1 = next((x for x in tb1 if x.get("name") == "文化传媒概念"), None)
V["CONC_CB_N"] = (_cb0 or {}).get("limit_up_num") or 0
V["CONC_CB_LB"] = (_cb0 or {}).get("continuous_plate_num") or 0
V["CONC_CB_N_Y"] = (_cb1 or {}).get("limit_up_num") or 0
V["CONC_CB_R"] = f"{V['CONC_CB_LB'] / V['CONC_CB_N'] * 100:.0f}" if V["CONC_CB_N"] else "0"

# 行业迁移
rows = []
for hy in set(list(_hyc0.keys()) + list(_hyc1.keys())):
    a, b = _hyc0.get(hy, 0), _hyc1.get(hy, 0)
    if a == b:
        continue
    rows.append((hy, a, b, a - b))
rows.sort(key=lambda r: -((r[1] + r[2]) + abs(r[3]) * 2))
_t = []
for hy, a, b, d in rows[:16]:
    _t.append("<tr><td>%s</td><td class='hl'>%d</td><td>%d</td><td class='%s'>%s</td><td>%s</td></tr>" % (
        hy, a, b, "up" if d > 0 else "down", f"{d:+d}", "流入" if d > 0 else "流出"))
V["TBL_HY"] = "\n".join(_t)
V["HY_ZERO_N"] = sum(1 for hy in _hyc1 if _hyc0.get(hy, 0) == 0)
V["HY_NEW_N"] = sum(1 for hy in _hyc0 if _hyc1.get(hy, 0) == 0)
_zero = [hy for hy in _hyc1 if _hyc0.get(hy, 0) == 0]
_zero.sort(key=lambda h: -_hyc1[h])
V["HY_ZERO_KEY"] = "、".join(f"{h} {_hyc1[h]}→0" for h in _zero[:8])
V["HY_DC_ADD"] = f"{_hyc0.get('电池',0) - _hyc1.get('电池',0):+d}"
V["HY_LS_ADD"] = f"{_hyc0.get('一般零售',0) - _hyc1.get('一般零售',0):+d}"
V["HY_ZX_ADD"] = f"{_hyc0.get('装修建材',0) - _hyc1.get('装修建材',0):+d}"
V["HY_YL_ADD"] = f"{_hyc0.get('饮料乳品',0) - _hyc1.get('饮料乳品',0):+d}"

# ================= 封板时间 / 类型 =================
ts0 = A0["ths_zt"]["total"].get("today") and S["timeslot"]["today"]
ts1 = S["timeslot"]["yesterday"]
LBL_TS = [("竞价/秒板", "竞价/秒板"), ("开盘半小时", "开盘半小时"), ("上午盘中", "上午盘中"),
          ("午后盘中", "午后盘中"), ("尾盘", "尾盘")]
_t = []
for k, nm in LBL_TS:
    a, b = ts0.get(k, 0), ts1.get(k, 0)
    _t.append("<tr><td>%s</td><td class='hl'>%d</td><td>%d</td><td class='%s'>%s</td></tr>" % (
        nm, a, b, "up" if a > b else ("down" if a < b else "mut"), f"{a - b:+d}" if a != b else "0"))
V["TBL_TS"] = "\n".join(_t)
for key, k in [("TS_JJ", "竞价/秒板"), ("TS_KP", "开盘半小时"), ("TS_SW", "上午盘中"),
               ("TS_WH", "午后盘中"), ("TS_WS", "尾盘")]:
    V[key] = ts0.get(k, 0)
    V[key + "_Y"] = ts1.get(k, 0)
EARLY = V["TS_JJ"] + V["TS_KP"] + V["TS_SW"]
EARLY_Y = V["TS_JJ_Y"] + V["TS_KP_Y"] + V["TS_SW_Y"]
V["TS_EARLY"], V["TS_EARLY_Y"] = EARLY, EARLY_Y
V["TS_EARLY_PCT"] = f"{EARLY / ZT * 100:.0f}"
V["TS_EARLY_PCT_Y"] = f"{EARLY_Y / ZT_Y * 100:.0f}"
V["TS_EARLY_D"] = f"{EARLY / ZT * 100 - EARLY_Y / ZT_Y * 100:+.0f}"
JS_TS = {"labels": [nm for _, nm in LBL_TS], "today": [ts0.get(k, 0) for k, _ in LBL_TS],
         "prev": [ts1.get(k, 0) for k, _ in LBL_TS]}

_ty = collections.Counter((ths0.get(x["c"]) or {}).get("limit_up_type") or "换手板" for x in zt0)
V["YIZI"] = _ty.get("一字板", 0)
V["TZI"] = _ty.get("T字板", 0)
V["HSB"] = _ty.get("换手板", 0)
V["HSB_PCT"] = f"{V['HSB'] / ZT * 100:.0f}"
V["YIZI_NAMES"] = "、".join(x["n"] for x in zt0 if (ths0.get(x["c"]) or {}).get("limit_up_type") == "一字板") or "无"
V["CYB_N"] = sum(1 for x in zt0 if x["c"].startswith(("30", "68")))
V["CYB_PCT"] = f"{V['CYB_N'] / ZT * 100:.0f}"

# 回封
_sealed = [x for x in zb0 if x.get("p") and x.get("ztp") and x["p"] >= x["ztp"]]
V["ZB_SEALED_N"] = len(_sealed)
V["ZB_SEAL_PCT"] = f"{len(_sealed) / ZB * 100:.0f}"
V["ZB_SEALED_TXT"] = ("（" + "、".join(x["n"] for x in _sealed) + "）") if _sealed else "，连续零回封"

# 东财/同花顺口径差
V["ZT_EM_TC"] = (A0.get("em_ZT") or {}).get("tc") or len(zt_all)
V["ZT_EM_DIFF"] = V["ZT_EM_TC"] - ZT
V["ZT_EM_DIFF_TXT"] = "两源一致" if V["ZT_EM_DIFF"] == 0 else "差额已逐只核对"
V["ZB_EM"] = (A0.get("em_ZB") or {}).get("tc") or len(zb0)
V["ZB_EM_DIFF"] = V["ZB_EM"] - ZB
V["DT_EM"] = len(dt0)
V["DT_EM_DIFF"] = V["DT_EM"] - DT

# ================= westock =================
SW = json.load(open(os.path.join(OUT, f"_sw{D0[4:]}.json"), encoding="utf-8"))


def sw_pct(nm):
    return f"{SW.get(nm, {}).get('pct', 0):+.2f}"


def sw_flow(nm):
    return f"{abs(SW.get(nm, {}).get('flow', 0)) / 10000.0:.0f}"


for key, nm in [("TX", "通信设备"), ("YJ", "元件"), ("BDT", "半导体"), ("FTB", "覆铜板"),
                ("BX", "保险Ⅱ"), ("BJ", "白酒Ⅱ"), ("DC", "电池"), ("YL", "饮料乳品"),
                ("YX", "游戏Ⅱ"), ("GF", "光伏设备")]:
    V["SW_" + key + "_PCT"] = sw_pct(nm)
    V["SW_" + key + "_FLOW"] = sw_flow(nm)
V["SW_OUT_SUM"] = f"{sum(abs(SW.get(k, {}).get('flow', 0)) for k in ('通信设备', '元件', '半导体', '覆铜板'))/10000.0:.0f}"

# JSON 图数据
JS_SENTI = {"days": [x["d"] for x in days], "zt": [x["zt"] for x in days], "zb": [x["zb"] for x in days],
            "dt": [x["dt"] for x in days], "seal": [round(x["seal"], 1) for x in days]}
JS_AMT = {"labels": [x["name"] for x in sorted(ix, key=lambda z: (z["yoy"] is None, z["yoy"] or 0))],
          "vals": [round(x["yoy"] or 0, 1) for x in sorted(ix, key=lambda z: (z["yoy"] is None, z["yoy"] or 0))],
          "colors": ["#d93025" if (x["yoy"] or 0) > 0 else "#12805c"
                     for x in sorted(ix, key=lambda z: (z["yoy"] is None, z["yoy"] or 0))]}
JS_INTRA = {"labels": [x["nm"] for x in INTRA], "gap": [round(x["gap"], 2) for x in INTRA],
            "high": [round(x["high"], 2) for x in INTRA], "low": [round(x["low"], 2) for x in INTRA],
            "close": [round(x["close"], 2) for x in INTRA]}

for k, v in [("JS_LAD", JS_LAD), ("JS_AMT", JS_AMT), ("JS_SENTI", JS_SENTI), ("JS_INTRA", JS_INTRA),
             ("JS_DTCHAIN", JS_DTCHAIN), ("JS_DTCMP", JS_DTCMP), ("JS_MAIN", JS_MAIN),
             ("JS_PERF", JS_PERF), ("JS_TS", JS_TS)]:
    V[k] = json.dumps(v, ensure_ascii=False)

# ================= 渲染 =================
html = open(TPL, encoding="utf-8").read()
miss = []
for k, v in V.items():
    ph = "__" + k + "__"
    if ph in html:
        html = html.replace(ph, str(v))
res = sorted(set(re.findall(r"__[A-Z_0-9]+__", html)))
print("placeholder residue:", res)
assert not res, f"占位符残留 {res}"

out_p = os.path.join(REP, f"涨停复盘对比-{D0}.html")
open(out_p, "w", encoding="utf-8").write(html)
print("saved ->", out_p, len(html), "chars")
