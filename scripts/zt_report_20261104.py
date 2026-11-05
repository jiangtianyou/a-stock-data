# -*- coding: utf-8 -*-
"""涨停复盘报告 20261104 vs 20261103（定向清算次日 · 算力硬件链原路买回 · 宽度型反包）
用法：python scripts/zt_report_20261104.py 20261104
输入：out/zt_stats_20261104.json、out/zt_review_20261104.json、out/zt_review_20261103.json
     跌停明细 out/_dt1104.json / out/_dt1103.json；昨跌停股今日行情 out/_qdt1103.json；westock 榜 out/_sw1104.json / _sw1103.json
输出：reports/涨停复盘对比-20261104.html
"""
import json, os, sys, re, datetime, glob, time as _t
from statistics import mean, median

ROOT = os.environ.get("ZT_ROOT") or os.getcwd()
OUT = os.path.join(ROOT, "out")
REP = os.path.join(ROOT, "reports")
TPL = os.path.join(ROOT, "scripts", "_report_tpl_20261104.html")
os.makedirs(REP, exist_ok=True)

D0 = sys.argv[1] if len(sys.argv) > 1 else "20261104"
S = json.load(open(os.path.join(OUT, f"zt_stats_{D0}.json"), encoding="utf-8"))
D0, D1, D2 = S["D0"], S["D1"], S["D2"]
B = json.load(open(os.path.join(OUT, f"zt_review_{D0}.json"), encoding="utf-8"))
B1 = json.load(open(os.path.join(OUT, f"zt_review_{D1}.json"), encoding="utf-8"))
S1 = json.load(open(os.path.join(OUT, f"zt_stats_{D1}.json"), encoding="utf-8"))
S2 = json.load(open(os.path.join(OUT, f"zt_stats_{D2}.json"), encoding="utf-8"))
B2 = json.load(open(os.path.join(OUT, f"zt_review_{D2}.json"), encoding="utf-8"))
A2 = B2["dates"][D2]
perf = S["perf"]
s0 = S["senti"][D0]
A0 = B["dates"][D0]
A1 = B["dates"][D1]

WEEK = {0: "一", 1: "二", 2: "三", 3: "四", 4: "五", 5: "六", 6: "日"}


def md(ds):
    d = datetime.date(int(ds[:4]), int(ds[4:6]), int(ds[6:8]))
    return f"{d.month}/{d.day:02d}", WEEK[d.weekday()]


def f1(v):
    return f"{v:+.1f}"


def f2(v):
    return f"{v:+.2f}"


def signed(v, nd=0):
    """整型/浮点带符号，避免 ++ 双符号"""
    if nd == 0:
        return f"{v:+d}"
    return f"{v:+.{nd}f}"


def cls(v, inverse=False):
    """v>0 红(up)，v<0 绿(down)；inverse=True 用于反向指标（跌停/炸板）"""
    if v == 0:
        return "mut"
    pos = v > 0
    if inverse:
        pos = not pos
    return "up" if pos else "down"


V = {}
for tag, ds in [("D0", D0), ("D1", D1), ("D2", D2)]:
    lab, wk = md(ds)
    V[tag + "_LABEL"] = lab
    V[tag + "_WEEK"] = "周" + wk
    V[tag + "_FULL"] = f"{ds[:4]}-{ds[4:6]}-{ds[6:8]}"
    V[tag + "_CN"] = f"{ds[:4]}-{ds[4:6]}-{ds[6:8]}"
V["NEXT_D"] = "11/5 周四"
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
zt_all_1 = pool(A1, "em_ZT")


def load_json(p, default=None):
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    return default


dt0 = (load_json(os.path.join(OUT, f"_dt{D0[4:]}.json"), {}) or {}).get("data", {}).get("pool") or []
dt1 = (load_json(os.path.join(OUT, f"_dt{D1[4:]}.json"), {}) or {}).get("data", {}).get("pool") or []
qdt1 = load_json(os.path.join(OUT, f"_qdt{D1[4:]}.json"), {}) or {}
SW0 = load_json(os.path.join(OUT, f"_sw{D0[4:]}.json"), {}) or {}
SW1 = load_json(os.path.join(OUT, f"_sw{D1[4:]}.json"), {}) or {}

# ================= 情绪 =================
zt0_info = A0["ths_zt"]["total"]["today"]
zt1_info = A1["ths_zt"]["total"]["today"]
ld0 = A0["ths_zt"]["limit_down_count"]["today"]
ld1 = A1["ths_zt"]["limit_down_count"]["today"]

ZT = zt0_info["num"]
ZT_Y = zt1_info["num"]
ZT_0 = S2["senti"][D2]["zt"]
TOUCH = zt0_info["history_num"]
TOUCH_Y = zt1_info["history_num"]
SEAL = zt0_info["rate"] * 100
SEAL_Y = zt1_info["rate"] * 100
DT = ld0["num"]
DT_Y = ld1["num"]
DTOUCH = ld0["history_num"]
DTOUCH_Y = ld1["history_num"]
DSEAL = ld0["rate"] * 100
DSEAL_Y = ld1["rate"] * 100
DT_OPEN_N = ld0["open_num"]
DT_0 = S2["senti"][D2]["dt"]
MAXB_0 = S2["senti"][D2]["max_board"]

V.update({
    "ZT": str(ZT), "ZT_Y": str(ZT_Y), "ZT_0": str(ZT_0),
    "ZT_D": signed(ZT - ZT_Y), "ZT_PCT_D": f"{(ZT / ZT_Y - 1) * 100:+.1f}".replace("+", ""),
    "TOUCH": str(TOUCH), "TOUCH_Y": str(TOUCH_Y),
    "TOUCH_D": signed(TOUCH - TOUCH_Y),
    "TOUCH_PCT_D": f"{(TOUCH / TOUCH_Y - 1) * 100:+.1f}",
    "TOUCH_PCT_D2": f"{(TOUCH / TOUCH_Y - 1) * 100:.1f}",
    "SEAL": f"{SEAL:.1f}", "SEAL_Y": f"{SEAL_Y:.1f}", "SEAL_D": f"{SEAL - SEAL_Y:+.1f}",
    "DT": str(DT), "DT_Y": str(DT_Y), "DT_D": signed(DT - DT_Y), "DT_0": str(DT_0),
    "DTOUCH": str(DTOUCH), "DTOUCH_Y": str(DTOUCH_Y),
    "DSEAL": f"{DSEAL:.1f}", "DSEAL_Y": f"{DSEAL_Y:.1f}", "DT_OPEN_N": str(DT_OPEN_N),
    "TOUCH_GAP": str(TOUCH - ZT),
    "SEAL_FAIL": f"{(TOUCH - ZT) / TOUCH * 100:.1f}",
    "SEAL_FAIL_Y": f"{(TOUCH_Y - ZT_Y) / TOUCH_Y * 100:.1f}",
    "ZTDT": f"{ZT / DT:.1f}" if DT else "—",
    "ZTDT_Y": f"{ZT_Y / DT_Y:.1f}" if DT_Y else "—",
    "ZTDT_0": f"{ZT_0 / DT_0:.1f}" if DT_0 else "—",
    "ZT_VS_0": signed(ZT - ZT_0),
    "TOUCH_ZB_GAP": str(abs((TOUCH - ZT) - s0["zb"])),
})

# ================= 量能 =================
AMT = S["tot"]["today"]
AMT_Y = S["tot"]["prev"]
V.update({
    "AMT": f"{AMT:,.0f}", "AMT_Y": f"{AMT_Y:,.0f}",
    "AMT_D": f"{AMT - AMT_Y:+,.0f}", "AMT_PCT": f"{(AMT / AMT_Y - 1) * 100:+.1f}",
})

NAME = {"sh000001": "上证指数", "sz399001": "深证成指", "sz399006": "创业板指", "sh000688": "科创50",
        "bj899050": "北证50", "sh000300": "沪深300", "sh000852": "中证1000", "sh000905": "中证500",
        "sz399303": "国证2000", "sh000016": "上证50", "sz399005": "中小100"}
ORDER = ["sh000001", "sz399001", "sz399006", "sh000688", "bj899050", "sh000300",
         "sh000852", "sh000905", "sz399303", "sh000016", "sz399005"]
idx0 = B["indexes"]
idx1 = B1["indexes"]
rows_amt, rows_idx = [], []
n_up = n_dn = n_amt_up = n_amt_dn = 0
yoy = []
intra_labels, intra_gap, intra_high, intra_low, intra_close = [], [], [], [], []
n_above_open = n_gap_up = 0
N_INTRA_CODES = ["sh000001", "sz399001", "sz399006", "sh000688", "sh000300", "sz399303"]
for k in ORDER:
    a = idx0.get(k) or {}
    b = idx1.get(k) or {}
    if not a:
        continue
    p0, p1 = a.get("pct") or 0, b.get("pct") or 0
    m0, m1 = a.get("amount_wan") or 0, b.get("amount_wan") or 0
    chg = (m0 / m1 - 1) * 100 if m1 else 0
    if p0 > 0:
        n_up += 1
    elif p0 < 0:
        n_dn += 1
    if chg > 0:
        n_amt_up += 1
    else:
        n_amt_dn += 1
    yoy.append((NAME[k], chg, p0))
    cls_p = "up" if p0 > 0 else ("down" if p0 < 0 else "mut")
    rows_idx.append(
        "<tr><td>%s</td><td class=\"%s\">%s%%</td><td>%s%%</td><td>%s</td><td class=\"%s\">%s%%</td></tr>" % (
            NAME[k], cls_p, f"{p0:+.2f}", f"{p1:+.2f}", f"{m0 / 1e4:,.0f}",
            "up" if chg > 0 else "down", f"{chg:+.1f}"))
    if k in N_INTRA_CODES:
        prev = a.get("prev") or 0
        if prev:
            gap = (a["open"] / prev - 1) * 100
            hi = (a["high"] / prev - 1) * 100
            lo = (a["low"] / prev - 1) * 100
            cl = (a["price"] / prev - 1) * 100
            intra_labels.append(NAME[k])
            intra_gap.append(round(gap, 2))
            intra_high.append(round(hi, 2))
            intra_low.append(round(lo, 2))
            intra_close.append(round(cl, 2))
            if cl > gap:
                n_above_open += 1
            if gap > 0:
                n_gap_up += 1

# 成交额环比图（升序 → 类目轴首项在底部时视觉为降序）
yoy_sorted = sorted(yoy, key=lambda r: r[1])
rows_amt = [[r[0], round(r[1], 1)] for r in yoy_sorted]
V.update({
    "N_UP": str(n_up), "N_DN": str(n_dn), "AMT_UP_N": str(n_amt_up), "AMT_DN_N": str(n_amt_dn),
    "YOY_MAX": f"{max(yoy, key=lambda r: r[1])[1]:+.1f}",
    "YOY_MAX_NAME": max(yoy, key=lambda r: r[1])[0],
    "YOY_MIN": f"{min(yoy, key=lambda r: r[1])[1]:+.1f}",
    "YOY_MIN_NAME": min(yoy, key=lambda r: r[1])[0],
    "N_INTRA": str(len(intra_labels)), "N_ABOVE_OPEN": str(n_above_open), "N_GAP_UP": str(n_gap_up),
})


def gidx(code):
    return idx0.get(code) or {}


def gi(name, field, nd=2):
    a = gidx(name)
    prev = a.get("prev") or 0
    if not prev:
        return "0.0"
    return f"{(a.get(field) / prev - 1) * 100:+.{nd}f}"


V["SH_GAP"] = gi("sh000001", "open")
V["SH_HIGH"] = gi("sh000001", "high")
V["SH_LOW"] = gi("sh000001", "low")
V["SH_PCT"] = f"{gidx('sh000001').get('pct', 0):+.2f}"
_shh = (gidx("sh000001").get("high") or 0)
V["SH_DRAW"] = f"{(gidx('sh000001').get('price', 0) / _shh - 1) * 100:+.2f}" if _shh else "0.00"
V["CY_GAP"] = gi("sz399006", "open")
V["CY_HIGH"] = gi("sz399006", "high")
V["CY_LOW"] = gi("sz399006", "low")
V["CY_PCT"] = f"{gidx('sz399006').get('pct', 0):+.2f}"
V["KC_GAP"] = gi("sh000688", "open")
V["KC_HIGH"] = gi("sh000688", "high")
V["KC_LOW"] = gi("sh000688", "low")
V["KC_PCT"] = f"{gidx('sh000688').get('pct', 0):+.2f}"
V["GZ_HIGH"] = gi("sz399303", "high")
V["GZ_PCT"] = f"{gidx('sz399303').get('pct', 0):+.2f}"
V["SH50_HIGH"] = gi("sh000016", "high")
V["SH50_PCT"] = f"{gidx('sh000016').get('pct', 0):+.2f}"
V["SH50_PCT_Y"] = f"{(idx1.get('sh000016') or {}).get('pct', 0):+.2f}"
V["KC_PCT_Y"] = f"{(idx1.get('sh000688') or {}).get('pct', 0):+.2f}"


def yoy_of(code):
    a = idx0.get(code) or {}
    b = idx1.get(code) or {}
    if not b or not b.get("amount_wan"):
        return 0.0
    return ((a.get("amount_wan") or 0) / b["amount_wan"] - 1) * 100


V["SH50_YOY"] = f"{yoy_of('sh000016'):+.1f}"
V["SH50_YOY_Y"] = "—"
V["KC_YOY"] = f"{yoy_of('sh000688'):+.1f}"
V["KC_YOY_Y"] = "—"
V["ZZ500_YOY"] = f"{yoy_of('sh000905'):+.1f}"
V["ZZ1000_YOY"] = f"{yoy_of('sh000852'):+.1f}"
V["GZ_YOY"] = f"{yoy_of('sz399303'):+.1f}"
V["HS300_YOY"] = f"{yoy_of('sh000300'):+.1f}"

# ================= 涨停股结构 =================
r0 = S["r0"]
amt_sum = sum(x["amount"] or 0 for x in r0) / 1e8
amt_sum_y = sum(x["amount"] or 0 for x in S1["r0"]) / 1e8
fund = sum(x["fund"] or 0 for x in r0) / 1e8
fund_y = sum(x["fund"] or 0 for x in S1["r0"]) / 1e8
V.update({
    "AMT_SUM": f"{amt_sum:,.1f}", "AMT_SUM_Y": f"{amt_sum_y:,.1f}",
    "AMT_SUM_PCT": f"{(amt_sum / amt_sum_y - 1) * 100:+.1f}",
    "AMT_SUM_MULT": f"{amt_sum / amt_sum_y:.1f}",
    "SHARE": f"{amt_sum / AMT * 100:.1f}", "SHARE_Y": f"{amt_sum_y / AMT_Y * 100:.2f}",
    "FUND": f"{fund:.1f}", "FUND_Y": f"{fund_y:.1f}",
    "FUND_MED": f"{median([x['fund'] or 0 for x in r0]) / 1e8:.2f}",
    "FUND_MED_Y": f"{median([x['fund'] or 0 for x in S1['r0']]) / 1e8:.2f}",
    "YIZI": str(sum(1 for x in r0 if x["limit_up_type"] == "一字板")),
    "TZI": str(sum(1 for x in r0 if x["limit_up_type"] == "T字板")),
    "HSB": str(sum(1 for x in r0 if x["limit_up_type"] == "换手板")),
    "HSB_PCT": f"{sum(1 for x in r0 if x['limit_up_type'] == '换手板') / len(r0) * 100:.0f}",
    "CYB_N": str(sum(1 for x in r0 if x["code"].startswith(("30", "68")))),
    "CYB_PCT": f"{sum(1 for x in r0 if x['code'].startswith(('30', '68'))) / len(r0) * 100:.1f}",
})

# 市值结构
mv0 = [x["ltsz"] or 0 for x in r0]
mv1 = [x["ltsz"] or 0 for x in S1["r0"]]
big0 = [x for x in r0 if (x["ltsz"] or 0) > 1e10]
big1 = [x for x in S1["r0"] if (x["ltsz"] or 0) > 1e10]
V.update({
    "ZT_MED_MV": f"{median(mv0) / 1e8:.0f}", "ZT_MED_MV_Y": f"{median(mv1) / 1e8:.0f}",
    "MV_MULT": f"{median(mv0) / median(mv1):.1f}",
    "ZT_BIG_N": str(len(big0)), "ZT_BIG_Y": str(len(big1)),
    "ZT_BIG_PCT": f"{len(big0) / len(r0) * 100:.0f}",
    "ZT_BIG_PCT_Y": f"{len(big1) / len(S1['r0']) * 100:.0f}",
    "ZT_MV_MAX": f"{max(mv0) / 1e8:,.0f}", "ZT_MV_MAX_Y": f"{max(mv1) / 1e8:,.0f}",
})

# ================= 梯队 =================
lad0 = s0["ladder"]
lad1 = S1["senti"][D1]["ladder"]


def ladn(d, k):
    return int(d.get(str(k), 0))


V.update({
    "MAXB": str(s0["max_board"]), "MAXB_Y": str(S1["senti"][D1]["max_board"]), "MAXB_0": str(MAXB_0),
    "LB": str(s0["lianban"]), "LB_Y": str(S1["senti"][D1]["lianban"]),
    "LB_D": signed(s0["lianban"] - S1["senti"][D1]["lianban"]),
    "LB_PCT": f"{s0['lianban'] / ZT * 100:.1f}",
    "LB_PCT_Y": f"{S1['senti'][D1]['lianban'] / ZT_Y * 100:.1f}",
    "LB_PCT_D": f"{s0['lianban'] / ZT * 100 - S1['senti'][D1]['lianban'] / ZT_Y * 100:+.1f}",
    "SHOU": str(ladn(lad0, 1)), "SHOU_Y": str(ladn(lad1, 1)),
    "SHOU_PCT": f"{ladn(lad0, 1) / ZT * 100:.1f}",
    "SHOU_PCT_0": f"{s0['shouban'] / ZT * 100:.1f}",
    "LAD2": str(ladn(lad0, 2)), "LAD2_Y": str(ladn(lad1, 2)),
    "LAD3": str(ladn(lad0, 3)), "LAD3_Y": str(ladn(lad1, 3)),
    "LAD4": str(ladn(lad0, 4)), "LAD4_Y": str(ladn(lad1, 4)),
    "ZT_NEW": str(ZT - sum(1 for x in perf if x["again"])),
})
# 首板占比 D2 用 stats 现算
V["SHOU_PCT_0"] = f"{S2['senti'][D2]['shouban'] / S2['senti'][D2]['zt'] * 100:.1f}"

lad_rows = []
for lv in range(1, max(int(V["MAXB"]), int(V["MAXB_Y"]), int(V["MAXB_0"])) + 1):
    t, y = ladn(lad0, lv), ladn(lad1, lv)
    d = t - y
    lad_rows.append("<tr><td>%d 板</td><td class=\"hl\">%d</td><td>%d</td><td class=\"%s\">%s</td></tr>"
                    % (lv, t, y, "up" if d > 0 else ("down" if d < 0 else "mut"), signed(d)))
V["TBL_LAD"] = "\n".join(lad_rows)

lb0 = [x for x in r0 if (x["lbc"] or 1) >= 2]
lb1 = [x for x in S1["r0"] if (x["lbc"] or 1) >= 2]
maxb_names = "、".join(x["name"] for x in lb0 if (x["lbc"] or 1) == s0["max_board"])
V["MAXB_NAMES"] = maxb_names or "—"
mb_list = [x for x in lb0 if (x["lbc"] or 1) == s0["max_board"]]
V["MAXB_CN"] = str(len(mb_list))
V["MAXB_DETAIL"] = "；".join("%s（%s，封单 %.2f 亿、成交 %.2f 亿、首封 %s）"
                          % (x["name"], x["hybk"], (x["fund"] or 0) / 1e8, (x["amount"] or 0) / 1e8, x["fbt"] or "—")
                          for x in sorted(mb_list, key=lambda y: -(y["fund"] or 0)))
lad4y = [x for x in lb1 if (x["lbc"] or 1) == 4]
lad3y = [x for x in lb1 if (x["lbc"] or 1) == 3]
V["LAD4Y_N"] = str(len(lad4y))
V["LAD3Y_N"] = str(len(lad3y))
V["LAD4Y_NAMES"] = "、".join(x["name"] for x in lad4y) or "无"
V["LAD3Y_NAMES"] = "、".join(x["name"] for x in lad3y) or "无"
V["LAD3_SAVE"] = str(sum(1 for x in lb0 if (x["lbc"] or 1) == 3))
_pm = {x["code"]: x["pct"] for x in perf}
V["LAD4Y_PCT"] = "、".join("%+.2f%%" % _pm.get(x["code"], 0) for x in lad4y) or "—"
V["LAD3Y_PCT"] = "、".join("%+.2f%%" % _pm.get(x["code"], 0) for x in lad3y) or "—"
V["LAD4_N"] = str(ladn(lad0, 4))

lian_rows = []
for x in sorted(lb0, key=lambda y: (-(y["lbc"] or 1), -(y["fund"] or 0))):
    lian_rows.append("<tr><td class=\"hl\">%s</td><td>%d</td><td>%s</td><td>%s</td><td>%.2f</td><td>%.2f</td><td>%.1f%%</td><td class=\"note\">%s</td></tr>"
                     % (x["name"], x["lbc"], x["hybk"], (x["fbt"] or "—")[:5],
                        (x["fund"] or 0) / 1e8, (x["amount"] or 0) / 1e8, x["turnover"] or 0, x["reason"]))
V["TBL_LIANBAN"] = "\n".join(lian_rows)

# ================= 晋级 / 溢价 =================
adv = [x for x in perf if x["again"]]
sb = [x for x in perf if (x["lbc"] or 1) == 1]
lbp = [x for x in perf if (x["lbc"] or 1) >= 2]
adv_y = 0
if S1["perf"]:
    adv_y = sum(1 for x in S1["perf"] if x["again"]) / len(S1["perf"]) * 100


def gstat(g):
    if not g:
        return 0, 0, 0, 0, 0, 0
    ps = [x["pct"] for x in g]
    return len(g), sum(1 for x in g if x["again"]) / len(g) * 100, mean(ps), median(ps), \
        sum(1 for x in ps if x < 0), sum(1 for x in ps if x <= -5)


perf_ps = [x["pct"] for x in perf]
V.update({
    "ADV_RATE": f"{len(adv) / len(perf) * 100:.1f}", "ADV_RATE_Y": f"{adv_y:.1f}",
    "ADV_N": str(len(adv)), "ADV_TOT": str(len(perf)),
    "PERF_MEAN": f"{mean(perf_ps):+.2f}", "PERF_MED": f"{median(perf_ps):+.2f}",
    "PERF_DN_N": str(sum(1 for p in perf_ps if p < 0)),
    "PERF_DN_PCT": f"{sum(1 for p in perf_ps if p < 0) / len(perf_ps) * 100:.1f}",
    "PERF_DN5_N": str(sum(1 for p in perf_ps if p <= -5)),
})
_sbn, _sbr, _sbm, _sbmed, _sbdn, _sbd5 = gstat(sb)
_lbn, _lbr, _lbm, _lbmed, _lbdn, _lbd5 = gstat(lbp)
V.update({
    "SB_N": str(_sbn), "SB_RATE": f"{_sbr:.1f}", "SB_MEAN": f"{_sbm:+.2f}", "SB_MED": f"{_sbmed:+.2f}",
    "SB_DN_N": str(_sbdn), "SB_DN5_N": str(_sbd5),
    "LB_N": str(_lbn), "LB_RATE": f"{_lbr:.1f}", "LB_MEAN": f"{_lbm:+.2f}", "LB_MED": f"{_lbmed:+.2f}",
    "LB_DN_N": str(_lbdn), "LB_DN5_N": str(_lbd5),
    "GAP": f"{_sbmed - _lbmed:+.2f}", "GAP_CLS": "up" if _sbmed > _lbmed else "down",
})
gap_y = 0.0
if S1["perf"]:
    _psb = [x["pct"] for x in S1["perf"] if (x["lbc"] or 1) == 1]
    _plb = [x["pct"] for x in S1["perf"] if (x["lbc"] or 1) >= 2]
    if _psb and _plb:
        gap_y = median(_psb) - median(_plb)
V["GAP_Y"] = f"{gap_y:+.2f}"

sr = sorted(perf, key=lambda x: -x["pct"])
V["PERF_TOP5"] = "、".join("%s %+.2f%%" % (x["name"], x["pct"]) for x in sr[:5])
V["PERF_BOT5"] = "、".join("%s %+.2f%%" % (x["name"], x["pct"]) for x in sr[-5:])
V["PERF_WEAK"] = sr[-1]["name"]
V["ADV_NAMES"] = "、".join(x["name"] for x in adv)

dt0_codes = {x["c"]: x["n"] for x in dt0}
atk_dt = [x for x in perf if x["code"] in dt0_codes]
V["ATK_DT_N"] = str(len(atk_dt))
V["ATK_DT_NAMES"] = "、".join("%s（昨 %d 板）" % (x["name"], x["lbc"] or 1) for x in atk_dt) or "无"

# ================= 炸板 =================
zb_n = s0["zb"]
sealed = [x for x in zb0 if x.get("p") and x.get("ztp") and x["p"] >= x["ztp"]]
zb_amt = sum(x.get("amount") or 0 for x in zb0) / 1e8
zb1_amt = sum(x.get("amount") or 0 for x in zb1) / 1e8
V.update({
    "ZB": str(zb_n), "ZB_Y": str(s0["zb_prev"]),
    "ZB_SEALED_N": str(len(sealed)),
    "ZB_SEAL_PCT": f"{len(sealed) / len(zb0) * 100:.0f}" if zb0 else "0",
    "ZB_SEALED_TXT": "（%s）" % "、".join("%s %+.2f%%" % (x["n"], x.get("zdp") or 0) for x in sealed) if sealed else "（零回封）",
    "ZB_AMT": f"{zb_amt:.1f}", "ZB_AMT_Y": f"{zb1_amt:.1f}",
    "ZB_RATIO": f"{zb_amt / amt_sum:.2f}", "ZB_RATIO_Y": f"{zb1_amt / amt_sum_y:.2f}",
    "ZB_MED_MV": f"{median([(x.get('ltsz') or 0) / 1e8 for x in zb0]):.0f}" if zb0 else "0",
    "ZB_BIG_N": str(sum(1 for x in zb0 if (x.get("ltsz") or 0) > 1e10)),
    "ZB_EM": str((A0.get("em_ZB") or {}).get("tc") or 0),
})
_ztop = sorted(zb0, key=lambda y: -(y.get("amount") or 0))[:3]
V["ZB_TOP_TXT"] = "、".join("%s（%s，成交 %.1f 亿、收 %+.2f%%）"
                          % (x["n"], x.get("hybk") or "", (x.get("amount") or 0) / 1e8, x.get("zdp") or 0) for x in _ztop)

# ================= 封板时间 =================
TS = S["timeslot"]
t0, t1 = TS["today"], TS["yesterday"]
KEYS = ["竞价/秒板", "开盘半小时", "上午盘中", "午后盘中", "尾盘"]
V.update({
    "TS_JJ": str(t0.get("竞价/秒板", 0)), "TS_JJ_Y": str(t1.get("竞价/秒板", 0)),
    "TS_KP": str(t0.get("开盘半小时", 0)), "TS_KP_Y": str(t1.get("开盘半小时", 0)),
    "TS_SW": str(t0.get("上午盘中", 0)), "TS_SW_Y": str(t1.get("上午盘中", 0)),
    "TS_WH": str(t0.get("午后盘中", 0)), "TS_WH_Y": str(t1.get("午后盘中", 0)),
    "TS_WS": str(t0.get("尾盘", 0)), "TS_WS_Y": str(t1.get("尾盘", 0)),
})
te0 = t0.get("竞价/秒板", 0) + t0.get("开盘半小时", 0) + t0.get("上午盘中", 0)
te1 = t1.get("竞价/秒板", 0) + t1.get("开盘半小时", 0) + t1.get("上午盘中", 0)
V.update({
    "TS_EARLY": str(te0), "TS_EARLY_PCT": f"{te0 / ZT * 100:.1f}",
    "TS_EARLY_Y": str(te1), "TS_EARLY_PCT_Y": f"{te1 / ZT_Y * 100:.1f}",
    "TS_EARLY_D": f"{te0 / ZT * 100 - te1 / ZT_Y * 100:+.1f}",
    "TS_WH_PCT": f"{t0.get('午后盘中', 0) / ZT * 100:.1f}",
})
ts_rows = []
for k in KEYS:
    a, b = t0.get(k, 0), t1.get(k, 0)
    d = a - b
    ts_rows.append("<tr><td>%s</td><td class=\"hl\">%d</td><td>%d</td><td class=\"%s\">%s</td></tr>"
                   % (k, a, b, "up" if d > 0 else ("down" if d < 0 else "mut"), signed(d)))
V["TBL_TS"] = "\n".join(ts_rows)

# ================= 簇：算力硬件链 / AI 内容链 / 贵金属 =================
CALC_HY = ["半导体", "元件", "光学光电", "电子化学", "其他电子", "通信设备", "自动化设"]
AI_HY = ["出版", "影视院线", "数字媒体", "广告营销", "IT服务Ⅱ", "软件开发", "游戏Ⅱ", "电视广播"]
hy0, hy1 = S["hy0"], S["hy1"]
calc0 = [x for x in r0 if x["hybk"] in CALC_HY]
calc1 = [x for x in S1["r0"] if x["hybk"] in CALC_HY]
calc_amt = sum(x["amount"] or 0 for x in calc0) / 1e8
calc_fund = sum(x["fund"] or 0 for x in calc0) / 1e8
V.update({
    "CALC_N": str(len(calc0)), "CALC_N_Y": str(len(calc1)),
    "CALC_LB": str(sum(1 for x in calc0 if (x["lbc"] or 1) >= 2)),
    "CALC_LB_TXT": "、".join("%s %d 板" % (x["name"], x["lbc"]) for x in calc0 if (x["lbc"] or 1) >= 2) or "仅 1 只",
    "CALC_SHOU": str(sum(1 for x in calc0 if (x["lbc"] or 1) == 1)),
    "CALC_AMT": f"{calc_amt:,.1f}",
    "CALC_HY_TXT": " / ".join(CALC_HY),
    "CALC_MV_MED": f"{median([(x['ltsz'] or 0) / 1e8 for x in calc0]):.0f}",
    "CALC_ADV_NEED": str(max(8, round(len(calc0) * 0.3))),
})
V["CALC_SHARE"] = f"{calc_amt / amt_sum * 100:.1f}"
V["CALC_FUND_SHARE"] = f"{calc_fund / fund * 100:.1f}"

# 今日算力链的昨日涨跌幅（已由 _x1104c 落盘？改为现算：从 out/_calc_y 缓存）
CALC_Y_CACHE = os.path.join(OUT, f"_calcy_{D0}.json")
calc_y = {}
if os.path.exists(CALC_Y_CACHE):
    calc_y = json.load(open(CALC_Y_CACHE, encoding="utf-8"))
if calc_y:
    vals = list(calc_y.values())
    V.update({
        "CALC_MEAN_Y": f"{mean(vals):+.2f}", "CALC_MED_Y": f"{median(vals):+.2f}",
        "CALC_DN_N": str(sum(1 for v in vals if v < 0)),
        "CALC_DN_PCT": f"{sum(1 for v in vals if v < 0) / len(vals) * 100:.0f}",
        "CALC_DN5_N": str(sum(1 for v in vals if v <= -5)),
        "CALC_DN10_N": str(sum(1 for v in vals if v <= -10)),
    })
    worst = sorted([(x["name"], calc_y.get(x["code"], 0)) for x in calc0 if x["code"] in calc_y], key=lambda t: t[1])[:3]
    V["CALC_WORST_TXT"] = "、".join("%s %+.2f%%" % (n, v) for n, v in worst)
    V["CALC_MEAN_ABS"] = f"{abs(mean(vals)):.2f}"

ai0 = sum(hy0.get(k, 0) for k in AI_HY)
ai1 = sum(hy1.get(k, 0) for k in AI_HY)
ai0_list = [x for x in r0 if x["hybk"] in AI_HY]
ai_amt = sum(x["amount"] or 0 for x in ai0_list) / 1e8

CONS_HY = ["一般零售", "服装家纺", "饮料乳品", "休闲食品"]
BATT_HY = ["电池"]
MED_HY = ["医疗服务", "化学制药", "中药Ⅱ"]
cons0 = sum(hy0.get(k, 0) for k in CONS_HY)
cons1 = sum(hy1.get(k, 0) for k in CONS_HY)
batt0 = sum(hy0.get(k, 0) for k in BATT_HY)
batt1 = sum(hy1.get(k, 0) for k in BATT_HY)
med0 = sum(hy0.get(k, 0) for k in MED_HY)
med1 = sum(hy1.get(k, 0) for k in MED_HY)
cons_amt = sum((x["amount"] or 0) for x in r0 if x["hybk"] in CONS_HY) / 1e8
batt_amt = sum((x["amount"] or 0) for x in r0 if x["hybk"] in BATT_HY) / 1e8
med_amt = sum((x["amount"] or 0) for x in r0 if x["hybk"] in MED_HY) / 1e8

# 「羊字辈」：名称或涨停原因含「羊」（含「羊字辈」标签）
yang = [x for x in perf if ("羊" in (x["name"] or "")) or ("羊" in (x["reason"] or ""))]
yang_ps = [x["pct"] for x in yang]
yang_zt = [x for x in yang if x["pct"] >= 9.8]
yang_dt = [x for x in yang if x["pct"] <= -9.8]
V.update({
    "CONS_N": str(cons0), "CONS_N_Y": str(cons1), "CONS_AMT": f"{cons_amt:.1f}",
    "BATT_N": str(batt0), "BATT_N_Y": str(batt1), "BATT_AMT": f"{batt_amt:.1f}",
    "MED_N": str(med0), "MED_N_Y": str(med1), "MED_AMT": f"{med_amt:.1f}",
    "YMAIN_N": str(batt0 + cons0), "YMAIN_N_Y": str(batt1 + cons1),
    "YMAIN_DN_PCT": f"{(1 - (batt0 + cons0) / (batt1 + cons1)) * 100:.1f}" if (batt1 + cons1) else "0.0",
    "YMAIN_SHARE": f"{(batt0 + cons0) / ZT * 100:.1f}",
    "YMAIN_SHARE_Y": f"{(batt1 + cons1) / ZT_Y * 100:.1f}",
    "YANG_N": str(len(yang)),
    "YANG_MEAN": f"{mean(yang_ps):+.2f}" if yang_ps else "0.00",
    "YANG_MED": f"{median(yang_ps):+.2f}" if yang_ps else "0.00",
    "YANG_ZT": str(len(yang_zt)), "YANG_DT": str(len(yang_dt)),
    "YANG_DN": str(sum(1 for p in yang_ps if p < 0)),
    "YANG_ZT_NAMES": "、".join(x["name"] for x in yang_zt) or "无",
    "YANG_DT_NAMES": "、".join(x["name"] for x in yang_dt) or "无",
})
_y1 = [x for x in S1["r0"] if ("羊" in (x["name"] or "")) or ("羊" in (x["reason"] or ""))]
_y1_amt = sum(x["amount"] or 0 for x in _y1) / 1e8
V["YANG_SHARE_Y"] = f"{_y1_amt / amt_sum_y * 100:.1f}"
V["YANG_AMT_Y"] = f"{_y1_amt:.1f}"
V.update({
    "AI_N": str(ai0), "AI_N_Y": str(ai1),
    "AI_DN_PCT": f"{(1 - ai0 / ai1) * 100:.1f}" if ai1 else "0.0",
    "AI_SHARE": f"{ai0 / ZT * 100:.1f}", "AI_SHARE_Y": f"{ai1 / ZT_Y * 100:.1f}",
    "AI_LB": str(sum(1 for x in ai0_list if (x["lbc"] or 1) >= 2)),
    "AI_AMT": f"{ai_amt:.1f}",
})
for k, tag in [("半导体", "BDT"), ("元件", "YJ"), ("光学光电", "GX"), ("自动化设", "ZD"),
               ("影视院线", "YS"), ("IT服务Ⅱ", "IT"), ("数字媒体", "SZ"), ("出版", "CB"),
               ("广告营销", "GG"), ("游戏Ⅱ", "YX"), ("软件开发", "RJ"), ("专用设备", "ZY"),
               ("贵金属", "GOLD"), ("小金属", "XJS"), ("汽车零部", "QCLB"), ("电池", "DC"),
               ("一般零售", "LS"), ("服装家纺", "FZ"), ("饮料乳品", "YL")]:
    V["HY_" + tag] = str(hy0.get(k, 0))
    V["HY_" + tag + "_Y"] = str(hy1.get(k, 0))
    V["HY_" + tag + "_ADD"] = signed(hy0.get(k, 0) - hy1.get(k, 0))

# 贵金属
gold0 = [x for x in r0 if x["hybk"] in ("贵金属", "小金属")]
gold_amt = sum(x["amount"] or 0 for x in gold0) / 1e8
V.update({
    "GOLD_N": str(len(gold0)), "GOLD_AMT": f"{gold_amt:.1f}",
    "GOLD_SHARE": f"{gold_amt / amt_sum * 100:.1f}",
    "GOLD_LB": str(sum(1 for x in gold0 if (x["lbc"] or 1) >= 2)),
    "HY_GOLD": str(hy0.get("贵金属", 0)), "HY_XJS": str(hy0.get("小金属", 0)),
    "GOLD_TOP_TXT": "、".join("%s（%s，成交 %.1f 亿）" % (x["name"], x["hybk"], (x["amount"] or 0) / 1e8)
                            for x in sorted(gold0, key=lambda y: -(y["amount"] or 0))[:4]),
})

# 大市值代表
_big4 = sorted(big0, key=lambda y: -(y["ltsz"] or 0))[:4]
V["BIG_TXT_LIST"] = "、".join(
    "<b>%s</b>（流通 %.0f 亿）" % (y["name"], (y["ltsz"] or 0) / 1e8) for y in _big4
) or "—"
# ================= 昨日跌停池修复 =================
dt1_rows = []
dt1_vals, dt1_zt = [], 0
zt0_codes = {x["code"] for x in r0}
CALC_DT_HY = {"元件", "通信设备", "半导体", "通信服务", "其他电源"}
for x in dt1:
    q = qdt1.get(x["c"], {})
    p = q.get("pct")
    if p is None:
        continue
    dt1_vals.append(p)
    if x["c"] in zt0_codes:
        dt1_zt += 1
V.update({
    "DT1_N": str(len(dt1_vals)),
    "DT1_MEAN": f"{mean(dt1_vals):+.2f}" if dt1_vals else "0.00",
    "DT1_MED": f"{median(dt1_vals):+.2f}" if dt1_vals else "0.00",
    "DT1_UP": str(sum(1 for v in dt1_vals if v > 0)),
    "DT1_ZT": str(dt1_zt),
    "DT1_DN": str(sum(1 for v in dt1_vals if v < 0)),
    "DT_AMT": "0", "DT_AMT_Y": "0",
})
# 跌停股成交（今日/昨日）
_qt = A0.get("today_zt_quotes") or {}
# 今日跌停池成交用 _dt1104 的 fund 不可靠 → 从腾讯快照另取（已由 _x1104b 打印），此处用 stats 外置文件

DMETA = load_json(os.path.join(OUT, f"_dtmeta_{D0}.json"), {}) or {}
V["DT_AMT"] = f"{DMETA.get('dt_amt', 0):.1f}"
V["DT_AMT_Y"] = f"{DMETA.get('dt_amt_y', 0):.1f}"
V["DT_RATIO"] = f"{DMETA.get('dt_amt', 0) / amt_sum:.2f}"
V["DT_RATIO_Y"] = f"{DMETA.get('dt_amt_y', 0) / amt_sum_y:.2f}"

# 算力链 vs 非算力链（昨日跌停池）
chip_dt = [x for x in dt1 if (x.get("hybk") in CALC_DT_HY) or (x.get("hybk") == "塑料" and x.get("n") == "福莱新材")]
oth_dt = [x for x in dt1 if x not in chip_dt]
chip_vals = [qdt1[x["c"]]["pct"] for x in chip_dt if x["c"] in qdt1 and qdt1[x["c"]].get("pct") is not None]
oth_vals = [qdt1[x["c"]]["pct"] for x in oth_dt if x["c"] in qdt1 and qdt1[x["c"]].get("pct") is not None]
V.update({
    "DT_CHIP_N": str(len(chip_dt)),
    "DT_CHIP_MEAN": f"{mean(chip_vals):+.2f}" if chip_vals else "0.00",
    "DT_CHIP_MED": f"{median(chip_vals):+.2f}" if chip_vals else "0.00",
    "DT_OTHER_N": str(len(oth_dt)),
    "DT_OTHER_MEAN": f"{mean(oth_vals):+.2f}" if oth_vals else "0.00",
    "DT_CHIP_TXT": "、".join("%s %+.2f%%" % (x["n"], qdt1[x["c"]]["pct"]) for x in
                           sorted(chip_dt, key=lambda y: -(qdt1.get(y["c"], {}).get("pct") or -99))),
})
V["DT_NAMES"] = "、".join(x["n"] for x in dt0)
V["DT_HY_N"] = str(len({x.get("hybk") for x in dt0 if x.get("hybk")}))
_hc = {}
for x in dt0:
    h = x.get("hybk") or "—"
    _hc[h] = _hc.get(h, 0) + 1
V["DT_HY_MAX"] = str(max(_hc.values())) if _hc else "0"

# 昨日跌停池明细表（按今日涨跌幅升序）
_dt1_sorted = sorted([x for x in dt1 if x["c"] in qdt1], key=lambda x: qdt1[x["c"]].get("pct") or 0)
_dtr = []
for x in _dt1_sorted:
    q = qdt1[x["c"]]
    p = q.get("pct") or 0
    note = "→ 今日涨停" if x["c"] in zt0_codes else ("算力硬件链" if x in chip_dt else "—")
    _dtr.append("<tr><td>%s</td><td class=\"hl\">%s</td><td>%s</td><td class=\"%s\">%+.2f%%</td><td>%.2f</td><td>%.0f</td><td>%s</td></tr>"
                % (x["c"], x["n"], x.get("hybk") or "—", "up" if p > 0 else "down", p,
                   q.get("amount", 0), (x.get("ltsz") or 0) / 1e8, note))
V["TBL_DT1"] = "\n".join(_dtr)

# ================= 概念板块榜 =================
blk = sorted((A0.get("ths_block") or []), key=lambda y: -(y.get("limit_up_num") or 0))
_br = []
for x in blk[:10]:
    lu = x.get("limit_up_num") or 0
    cp = x.get("continuous_plate_num") or 0
    r = cp / lu * 100 if lu else 0
    _br.append("<tr><td>%s</td><td class=\"hl\">%d</td><td>%d</td><td class=\"%s\">%.0f%%</td><td class=\"note\">%s</td></tr>"
               % (x.get("name"), lu, cp, "up" if r >= 40 else "down", r, x.get("high") or "—"))
V["TBL_CONC"] = "\n".join(_br)
if blk:
    t1b = blk[0]
    V.update({
        "CONC_TOP1": str(t1b.get("name")), "CONC_TOP1_N": str(t1b.get("limit_up_num") or 0),
        "CONC_TOP1_LB": str(t1b.get("continuous_plate_num") or 0),
        "CONC_TOP1_R": f"{(t1b.get('continuous_plate_num') or 0) / (t1b.get('limit_up_num') or 1) * 100:.0f}",
        "CONC_TOP1_SHARE": f"{(t1b.get('limit_up_num') or 0) / ZT * 100:.0f}",
    })
    _top7 = sorted(blk[:7], key=lambda y: -((y.get("continuous_plate_num") or 0) / (y.get("limit_up_num") or 1)))
    V["CONC_TOP7_MAX_BK"] = str(_top7[0].get("name"))
    V["CONC_TOP7_MAX_R"] = f"{( _top7[0].get('continuous_plate_num') or 0) / (_top7[0].get('limit_up_num') or 1) * 100:.0f}"

# ================= 行业迁移表 =================
_hk = set(hy0) | set(hy1)
_hrows = [(k, hy1.get(k, 0), hy0.get(k, 0)) for k in _hk if k]
_hrows.sort(key=lambda r: -((r[1] + r[2]) + abs(r[2] - r[1]) * 2))
_html = []
for k, a, b in _hrows[:18]:
    d = b - a
    _html.append("<tr><td>%s</td><td class=\"hl\">%d</td><td>%d</td><td class=\"%s\">%s</td><td class=\"note\">%s</td></tr>"
                 % (k, b, a, "up" if d > 0 else ("down" if d < 0 else "mut"), signed(d),
                    "流入" if d > 0 else ("流出" if d < 0 else "持平")))
V["TBL_HY"] = "\n".join(_html)
V["ZT_HY_N"] = str(len([k for k in hy0 if hy0[k]]))
V["ZT_HY_N_Y"] = str(len([k for k in hy1 if hy1[k]]))
V["HY_ZERO_N"] = str(len([k for k in hy1 if hy1.get(k) and not hy0.get(k)]))
V["HY_NEW_N"] = str(len([k for k in hy0 if hy0.get(k) and not hy1.get(k)]))

# ================= 情绪三日表 =================
_senti_rows = []


def _senti_row(label, zt, zb, touch, seal, dt, dseal, dtouch, inv_zt=False):
    cls_zt = cls(zt, inv_zt)
    return ("<tr><td>涨停家数</td><td>%d</td><td>%d</td><td class=\"hl\">%d</td><td class=\"%s\">%s</td></tr>"
            % (zt[0], zt[1], zt[2], cls_zt, signed(zt[2] - zt[1])))


S2S = S2["senti"][D2]
S1S = S1["senti"][D1]
_zt_seq = (S2S["zt"], ZT_Y, ZT)
_zb_seq = (S2S["zb"], s0["zb_prev"], s0["zb"])
_t_d2 = A2["ths_zt"]["total"]["today"]["history_num"]
_dt_d2 = S2["senti"][D2]["limit_down_count"]["today"]["history_num"]
_touch_seq = (_t_d2, TOUCH_Y, TOUCH)
_rows = [
    ("涨停家数", (_zt_seq[0], _zt_seq[1], _zt_seq[2]), cls(_zt_seq[2] - _zt_seq[1]), signed(_zt_seq[2] - _zt_seq[1])),
    ("炸板家数", (_zb_seq[0], _zb_seq[1], _zb_seq[2]), cls(_zb_seq[2] - _zb_seq[1], inverse=True), signed(_zb_seq[2] - _zb_seq[1])),
    ("触及涨停（参与度）", (_touch_seq[0], TOUCH_Y, TOUCH), cls(TOUCH - TOUCH_Y), signed(TOUCH - TOUCH_Y)),
    ("封板率", (f"{S2S['seal_rate'] * 100:.1f}%", f"{SEAL_Y:.1f}%", f"{SEAL:.1f}%"), cls(SEAL - SEAL_Y), f"{SEAL - SEAL_Y:+.1f}pct"),
    ("跌停家数（封死）", (S2S["dt"], DT_Y, DT), cls(DT - DT_Y, inverse=True), signed(DT - DT_Y)),
    ("触及跌停", (_dt_d2, DTOUCH_Y, DTOUCH), cls(DTOUCH - DTOUCH_Y, inverse=True), signed(DTOUCH - DTOUCH_Y)),
    ("跌停封死率", (f"{S2S['limit_down_count']['today']['rate'] * 100:.1f}%", f"{DSEAL_Y:.1f}%", f"{DSEAL:.1f}%"),
     cls(DSEAL - DSEAL_Y, inverse=True), f"{DSEAL - DSEAL_Y:+.1f}pct"),
]
_senti_html = []
for nm, vals, c, d in _rows:
    _senti_html.append("<tr><td>%s</td><td>%s</td><td>%s</td><td class=\"hl\">%s</td><td class=\"%s\">%s</td></tr>"
                       % (nm, vals[0], vals[1], vals[2], c, d))
V["TBL_SENTI"] = "\n".join(_senti_html)

# ================= 簇对比表 =================
def cnt_hy(h, keys):
    return sum(h.get(k, 0) for k in keys)


MAIN_DEF = [("算力硬件链（半导体/元件/光学光电/电子化学/其他电子/通信设备/自动化设）", CALC_HY, calc_amt),
            ("贵金属 + 小金属", ["贵金属", "小金属"], gold_amt),
            ("电池 / 固态电池", BATT_HY, batt_amt),
            ("消费（一般零售/服装家纺/饮料乳品/休闲食品）", CONS_HY, cons_amt),
            ("汽车零部件", ["汽车零部"], sum((x["amount"] or 0) for x in r0 if x["hybk"] == "汽车零部") / 1e8),
            ("医疗服务 / 化学制药 / 中药", MED_HY, med_amt)]
_main_html, main_labels, main_today, main_prev = [], [], [], []
for nm, keys, amt in MAIN_DEF:
    n0 = cnt_hy(hy0, keys)
    n1 = cnt_hy(hy1, keys)
    lbn = sum(1 for x in r0 if x["hybk"] in keys and (x["lbc"] or 1) >= 2)
    _main_html.append("<tr><td>%s</td><td>%d</td><td class=\"hl\">%d</td><td>%d</td><td>%.1f</td><td>%.1f%%</td></tr>"
                      % (nm, n1, n0, lbn, amt, amt / amt_sum * 100))
    main_labels.append(nm.split("（")[0])
    main_today.append(n0)
    main_prev.append(n1)
V["TBL_MAIN"] = "\n".join(_main_html)

# ================= 指数表 =================
V["TBL_IDX"] = "\n".join(rows_idx)

# ================= westock =================
def swp(name, key="pct"):
    return (SW0.get(name) or {}).get(key, 0)


def swp_y(name):
    return (SW1.get(name) or {}).get("pct", 0)


for nm, tag in [("半导体", "BDT"), ("元件", "YJ"), ("通信设备", "TX"), ("覆铜板", "FTB"),
                ("白酒Ⅱ", "BJ"), ("保险Ⅱ", "BX"), ("饮料乳品", "YL"), ("服装家纺", "FZF"),
                ("贵金属", "GOLD"), ("黄金概念", "GA")]:
    V["SW_" + tag + "_PCT"] = f"{swp(nm):.2f}"
    V["SW_" + tag + "_FLOW"] = f"{swp(nm, 'flow') / 1e4:.2f}"
    V["SW_" + tag + "_UD"] = str(swp(nm, "updown") or "—")
V["SW_BDT_FLOW"] = f"{swp('半导体', 'flow') / 1e4:.0f}"
V["SW_YJ_FLOW"] = f"{swp('元件', 'flow') / 1e4:.0f}"
V["SW_TX_FLOW"] = f"{swp('通信设备', 'flow') / 1e4:.0f}"
V["SW_FTB_FLOW"] = f"{swp('覆铜板', 'flow') / 1e4:.0f}"
V["SW_BJ_FLOW"] = f"{abs(swp('白酒Ⅱ', 'flow')) / 1e4:.0f}"
V["SW_GOLD_FLOW"] = f"{swp('贵金属', 'flow') / 1e4:.1f}"
V["SW_GA_FLOW"] = f"{swp('黄金概念', 'flow') / 1e4:.1f}"
V["SW_OUT_SUM"] = f"{(swp('半导体', 'flow') + swp('元件', 'flow') + swp('通信设备', 'flow') + swp('覆铜板', 'flow')) / 1e4:.0f}"
V["SW_BX_PCT_Y"] = f"{swp_y('保险Ⅱ'):.2f}"
V["SW_BJ_PCT_Y"] = f"{swp_y('白酒Ⅱ'):.2f}"

# ================= 其他口径 =================
zt_em_tc = (A0.get("em_ZT") or {}).get("tc") or 0
zt_em_pool = pool(A0, "em_ZT")
aj_em_pool = zt_em_pool
ths_codes = {x["code"] for x in r0}
em_codes = {x["c"] for x in aj_em_pool}
em_only = [x for x in aj_em_pool if x["c"] not in ths_codes]
ths_only = [x for x in r0 if x["code"] not in em_codes]
em_only_bj = [x for x in em_only if x["c"].startswith("92")]
em_only_hs = [x for x in em_only if not x["c"].startswith("92")]
_diff_parts = []
if em_only_bj:
    _diff_parts.append("东财多出的北交所标的 %d 只（%s）"
                       % (len(em_only_bj), "、".join(x["c"] + " " + x["n"] for x in em_only_bj)))
if em_only_hs:
    _diff_parts.append("东财多出的沪深标的 %d 只（%s）"
                       % (len(em_only_hs), "、".join(x["c"] + " " + x["n"] for x in em_only_hs)))
if ths_only:
    _diff_parts.append("同花顺多出的标的 %d 只（%s）"
                       % (len(ths_only), "、".join(x["code"] + " " + x["name"] for x in ths_only)))
V["ZT_EM_TC"] = str(zt_em_tc)
V["ZT_EM_DIFF"] = str(zt_em_tc - ZT)
V["ZT_EM_DIFF_TXT"] = ("净差 %+d 只；" % (zt_em_tc - ZT)) + "；".join(_diff_parts) if _diff_parts else "两源一致"
zb_em = (A0.get("em_ZB") or {}).get("tc") or 0
V["ZB_EM_DIFF"] = str(abs(zb_em - s0["zb"]))
V["ZB_EM_DIFF_TXT"] = "两源差异属收录时点不同" if zb_em != s0["zb"] else "两源一致"
dt_em = len(dt0)
V["DT_EM"] = str(dt_em)
V["DT_EM_DIFF"] = str(abs(dt_em - DT))
V["DT_EM_DIFF_TXT"] = "两源一致" if dt_em == DT else "差额 %d 只，按同花顺汇总口径取 %d 家" % (abs(dt_em - DT), DT)

# 关键词口径
KW = ["PCB", "印制电路", "覆铜板", "封装", "存储", "半导体", "光模块", "CPO", "光通信", "磷化铟",
      "电子布", "靶材", "晶圆", "探针", "铜箔", "基板", "HBM", "硅光", "芯片"]
kw = [x for x in r0 if any(k in (x["reason"] or "") for k in KW)]
kw_amt = sum(x["amount"] or 0 for x in kw) / 1e8
V.update({
    "KW_N": str(len(KW)), "KW_ZT_N": str(len(kw)), "KW_AMT": f"{kw_amt:.1f}",
    "KW_SHARE": f"{kw_amt / amt_sum * 100:.1f}", "KW_DIFF": str(len(kw) - len(calc0)),
    "KW_HY_N": str(len({x["hybk"] for x in kw})),
})

# ================= JS =================
js_senti = {"days": [V["D2_LABEL"], V["D1_LABEL"], V["D0_LABEL"]],
            "zt": [_zt_seq[0], _zt_seq[1], _zt_seq[2]],
            "zb": [_zb_seq[0], _zb_seq[1], _zb_seq[2]],
            "dt": [S2S["dt"], DT_Y, DT],
            "seal": [round(S2S["seal_rate"] * 100, 1), round(SEAL_Y, 1), round(SEAL, 1)]}
js_amt = {"labels": [r[0] for r in rows_amt], "vals": [r[1] for r in rows_amt],
          "colors": ["#d93025" if r[1] > 0 else "#12805c" for r in rows_amt]}
js_intra = {"labels": intra_labels, "gap": intra_gap, "high": intra_high, "low": intra_low, "close": intra_close}
_dp = sorted([(x["n"], round(qdt1[x["c"]]["pct"], 2)) for x in dt1 if x["c"] in qdt1], key=lambda t: t[1])
js_dtpay = {"labels": [d[0] for d in _dp], "vals": [d[1] for d in _dp],
            "colors": ["#d93025" if d[1] > 0 else "#12805c" for d in _dp]}
js_dtcmp = {"labels": [V["D1_LABEL"], V["D0_LABEL"]],
            "zt": [round(amt_sum_y, 1), round(amt_sum, 1)],
            "dt": [round(float(V["DT_AMT_Y"]), 1), round(float(V["DT_AMT"]), 1)],
            "zb": [round(zb1_amt, 1), round(zb_amt, 1)]}
js_lad = {"labels": [f"{lv}板" for lv in range(1, max(int(V["MAXB"]), int(V["MAXB_Y"]), int(V["MAXB_0"])) + 1)],
          "today": [ladn(lad0, lv) for lv in range(1, max(int(V["MAXB"]), int(V["MAXB_Y"]), int(V["MAXB_0"])) + 1)],
          "prev": [ladn(lad1, lv) for lv in range(1, max(int(V["MAXB"]), int(V["MAXB_Y"]), int(V["MAXB_0"])) + 1)]}
js_main = {"labels": main_labels[::-1], "today": main_today[::-1], "prev": main_prev[::-1]}
_buckets = [("跌停", -100, -9.8), ("-9.8~-5", -9.8, -5), ("-5~-2", -5, -2), ("-2~0", -2, 0),
            ("0~2", 0, 2), ("2~5", 2, 5), ("5~9.8", 5, 9.8), ("涨停", 9.8, 100)]
_bv = []
for nm, lo, hi in _buckets:
    _bv.append(sum(1 for p in perf_ps if lo <= p < hi))
js_perf = {"labels": [b[0] for b in _buckets], "vals": _bv,
           "colors": ["#12805c", "#12805c", "#3f9e7c", "#9ec7b7", "#e8b4ae", "#e07a70", "#d93025", "#d93025"]}
js_ts = {"labels": KEYS, "today": [t0.get(k, 0) for k in KEYS], "prev": [t1.get(k, 0) for k in KEYS]}

V.update({
    "JS_SENTI": json.dumps(js_senti, ensure_ascii=False),
    "JS_AMT": json.dumps(js_amt, ensure_ascii=False),
    "JS_INTRA": json.dumps(js_intra, ensure_ascii=False),
    "JS_DTPAY": json.dumps(js_dtpay, ensure_ascii=False),
    "JS_DTCMP": json.dumps(js_dtcmp, ensure_ascii=False),
    "JS_LAD": json.dumps(js_lad, ensure_ascii=False),
    "JS_MAIN": json.dumps(js_main, ensure_ascii=False),
    "JS_PERF": json.dumps(js_perf, ensure_ascii=False),
    "JS_TS": json.dumps(js_ts, ensure_ascii=False),
})

# ================= 渲染 =================
tpl = open(TPL, encoding="utf-8").read()
html = tpl
for k, v in V.items():
    html = html.replace("__%s__" % k, str(v))
html = html.replace("__", "\u2014")

resid = re.findall(r"__[A-Z_0-9]+__", html)
print("placeholder residue:", resid)
assert not resid, "占位符残留: %s" % resid
bad = re.findall(r"\+\+\d", html)
print("double-plus:", bad)
assert not bad

outp = os.path.join(REP, f"涨停复盘对比-{D0}.html")
open(outp, "w", encoding="utf-8").write(html)
print("saved ->", outp, len(html), "chars")
