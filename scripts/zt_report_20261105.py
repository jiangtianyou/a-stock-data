# -*- coding: utf-8 -*-
"""涨停复盘报告 20261105 vs 20261104（打板退潮 × 指数深 V · 跌停归零 · 光伏接棒）
用法：python scripts/zt_report_20261105.py 20261105
输入：out/zt_stats_20261105.json、out/zt_review_20261105.json / 20261104.json / 20261103.json
     跌停明细 out/_dt1105.json / _dt1104.json；昨跌停股今日行情 out/_qdt1104.json；westock 榜 out/_sw1105.json
输出：reports/涨停复盘对比-20261105.html
"""
import json, os, sys, re, datetime, time as _t
from statistics import mean, median

ROOT = os.environ.get("ZT_ROOT") or os.getcwd()
OUT = os.path.join(ROOT, "out")
REP = os.path.join(ROOT, "reports")
TPL = os.path.join(ROOT, "scripts", "_report_tpl_20261105.html")
os.makedirs(REP, exist_ok=True)

D0 = sys.argv[1] if len(sys.argv) > 1 else "20261105"
S = json.load(open(os.path.join(OUT, f"zt_stats_{D0}.json"), encoding="utf-8"))
D0, D1, D2 = S["D0"], S["D1"], S["D2"]
B = json.load(open(os.path.join(OUT, f"zt_review_{D0}.json"), encoding="utf-8"))
B1 = json.load(open(os.path.join(OUT, f"zt_review_{D1}.json"), encoding="utf-8"))
S1 = json.load(open(os.path.join(OUT, f"zt_stats_{D1}.json"), encoding="utf-8"))
S2 = json.load(open(os.path.join(OUT, f"zt_stats_{D2}.json"), encoding="utf-8"))
B2 = json.load(open(os.path.join(OUT, f"zt_review_{D2}.json"), encoding="utf-8"))
A0, A1, A2 = B["dates"][D0], B["dates"][D1], B2["dates"][D2]
perf = S["perf"]
s0, s1 = S["senti"][D0], S1["senti"][D1]

WEEK = {0: "一", 1: "二", 2: "三", 3: "四", 4: "五", 5: "六", 6: "日"}


def md(ds):
    d = datetime.date(int(ds[:4]), int(ds[4:6]), int(ds[6:8]))
    return f"{d.month}/{d.day:02d}", WEEK[d.weekday()]


def signed(v):
    return f"{v:+d}"


def cls(v, inverse=False):
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
V["NEXT_D"] = "11/6 周五"
V["GEN_TIME"] = _t.strftime("%Y-%m-%d %H:%M")


def pool(zn, key):
    return (zn.get(key) or {}).get("pool") or []


def load_json(p, default=None):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


ths0 = {x["code"]: x for x in A0["ths_zt"]["info"]}
ths1 = {x["code"]: x for x in A1["ths_zt"]["info"]}
r0 = S["r0"]
r1 = S1["r0"]
zb0 = pool(A0, "em_ZB")
dt0 = (load_json(os.path.join(OUT, f"_dt{D0[4:]}.json"), {}) or {}).get("data", {}).get("pool") or []
dt1 = (load_json(os.path.join(OUT, f"_dt{D1[4:]}.json"), {}) or {}).get("data", {}).get("pool") or []
qdt1 = load_json(os.path.join(OUT, f"_qdt{D1[4:]}.json"), {}) or {}
SW0 = load_json(os.path.join(OUT, f"_sw{D0[4:]}.json"), {}) or {}

# ================= 情绪 =================
# 重抓 D1 东财池 vs D1 当日抓取：缺的这几只行业字段需回填（见「簇」段）
D1_EM_POOL = len({x["c"] for x in A1["em_ZT"]["pool"]})
D1_EM_POOL_DAY = len({x["c"] for x in B1["dates"][D1]["em_ZT"]["pool"]})
_em1_day_map = {x["c"]: x for x in B1["dates"][D1]["em_ZT"]["pool"]}
_em1_fresh_map = {x["c"]: x for x in A1["em_ZT"]["pool"]}
MISS1 = [x for c, x in ths1.items() if not ((_em1_fresh_map.get(c) or {}).get("hybk"))]

zt0i = A0["ths_zt"]["total"]["today"]
zt1i = A1["ths_zt"]["total"]["today"]
ld0 = A0["ths_zt"]["limit_down_count"]["today"]
ld1 = A1["ths_zt"]["limit_down_count"]["today"]

ZT, ZT_Y, ZT_0 = zt0i["num"], zt1i["num"], S2["senti"][D2]["zt"]
TOUCH, TOUCH_Y = zt0i["history_num"], zt1i["history_num"]
SEAL, SEAL_Y = zt0i["rate"] * 100, zt1i["rate"] * 100
DT, DT_Y, DT_0 = ld0["num"], ld1["num"], S2["senti"][D2]["dt"]
DTOUCH, DTOUCH_Y = ld0["history_num"], ld1["history_num"]
DSEAL, DSEAL_Y = ld0["rate"] * 100, ld1["rate"] * 100
DT_OPEN_N = ld0["open_num"]

V.update({
    "ZT": str(ZT), "ZT_Y": str(ZT_Y), "ZT_0": str(ZT_0),
    "ZT_D": signed(ZT - ZT_Y), "ZT_PCT_D": f"{(ZT / ZT_Y - 1) * 100:+.1f}",
    "TOUCH": str(TOUCH), "TOUCH_Y": str(TOUCH_Y), "TOUCH_D": signed(TOUCH - TOUCH_Y),
    "TOUCH_PCT_D": f"{(TOUCH / TOUCH_Y - 1) * 100:+.1f}",
    "TOUCH_PCT_D2": f"减少 {abs((TOUCH / TOUCH_Y - 1) * 100):.1f}",
    "SEAL": f"{SEAL:.1f}", "SEAL_Y": f"{SEAL_Y:.1f}", "SEAL_D": f"{SEAL - SEAL_Y:+.1f}",
    "DT": str(DT), "DT_Y": str(DT_Y), "DT_D": signed(DT - DT_Y), "DT_0": str(DT_0),
    "DTOUCH": str(DTOUCH), "DTOUCH_Y": str(DTOUCH_Y),
    "DSEAL": f"{DSEAL:.1f}", "DSEAL_Y": f"{DSEAL_Y:.1f}", "DT_OPEN_N": str(DT_OPEN_N),
    "TOUCH_GAP": str(TOUCH - ZT),
    "SEAL_FAIL": f"{(TOUCH - ZT) / TOUCH * 100:.1f}",
    "SEAL_FAIL_Y": f"{(TOUCH_Y - ZT_Y) / TOUCH_Y * 100:.1f}",
    "TOUCH_ZB_GAP": str(abs((TOUCH - ZT) - s0["zb"])),
    # 当日旧报告口径（11-04 报告写的是 115 / 34 / 77.2%）
    "ZT_Y_REPORT": "115", "SEAL_Y_REPORT": "77.2",
    "DSEAL_0": f"{S2['senti'][D2]['limit_down_count']['today']['rate'] * 100:.1f}",
    "HY_MISS_Y": str(len(MISS1)),
    "HY_MISS_Y_NAMES": "、".join(x["name"] for x in MISS1) or "无",
    "D1_EM_POOL": str(D1_EM_POOL), "D1_EM_POOL_DAY": str(D1_EM_POOL_DAY),
})

# ================= 量能 =================
AMT, AMT_Y = S["tot"]["today"], S["tot"]["prev"]
V.update({
    "AMT": f"{AMT:,.0f}", "AMT_Y": f"{AMT_Y:,.0f}",
    "AMT_D": f"{AMT - AMT_Y:+,.0f}", "AMT_PCT": f"{(AMT / AMT_Y - 1) * 100:+.1f}",
    "AMT_PCT_ABS": f"{(AMT / AMT_Y - 1) * 100:.1f}",
})

# ================= 指数 =================
NAME = {"sh000001": "上证指数", "sz399001": "深证成指", "sz399006": "创业板指", "sh000688": "科创50",
        "bj899050": "北证50", "sh000300": "沪深300", "sh000852": "中证1000", "sh000905": "中证500",
        "sz399303": "国证2000", "sh000016": "上证50", "sz399005": "中小100"}
ORDER = list(NAME.keys())
idx0, idx1 = B["indexes"], B1["indexes"]
rows_idx, yoy = [], []
n_up = n_dn = n_amt_up = n_amt_dn = 0
intra_labels, intra_gap, intra_high, intra_low, intra_close = [], [], [], [], []
n_above_open = n_gap_up = 0
N_INTRA_CODES = ["sh000001", "sz399001", "sz399006", "sh000688", "sh000300", "sz399303"]
for k in ORDER:
    a, b = idx0.get(k) or {}, idx1.get(k) or {}
    if not a:
        continue
    p0, p1 = a.get("pct") or 0, b.get("pct") or 0
    m0, m1 = a.get("amount_wan") or 0, b.get("amount_wan") or 0
    chg = (m0 / m1 - 1) * 100 if m1 else 0
    n_up += p0 > 0
    n_dn += p0 < 0
    n_amt_up += chg > 0
    n_amt_dn += chg <= 0
    yoy.append((NAME[k], chg, p0))
    rows_idx.append('<tr><td>%s</td><td class="%s">%+.2f%%</td><td>%+.2f%%</td><td>%s</td><td class="%s">%+.1f%%</td></tr>'
                    % (NAME[k], "up" if p0 > 0 else ("down" if p0 < 0 else "mut"), p0, p1, f"{m0 / 1e4:,.0f}",
                       "up" if chg > 0 else "down", chg))
    if k in N_INTRA_CODES:
        prev = a.get("prev") or 0
        if prev:
            gap = (a["open"] / prev - 1) * 100
            intra_labels.append(NAME[k])
            intra_gap.append(round(gap, 2))
            intra_high.append(round((a["high"] / prev - 1) * 100, 2))
            intra_low.append(round((a["low"] / prev - 1) * 100, 2))
            intra_close.append(round((a["price"] / prev - 1) * 100, 2))
            n_above_open += (a["price"] > a["open"])
            n_gap_up += (gap > 0)
V["TBL_IDX"] = "\n".join(rows_idx)
V.update({
    "N_UP": str(n_up), "N_DN": str(n_dn), "AMT_UP_N": str(n_amt_up), "AMT_DN_N": str(n_amt_dn),
    "YOY_MAX": f"{max(yoy, key=lambda r: r[1])[1]:+.1f}%", "YOY_MAX_NAME": max(yoy, key=lambda r: r[1])[0],
    "YOY_MIN": f"{min(yoy, key=lambda r: r[1])[1]:+.1f}%", "YOY_MIN_NAME": min(yoy, key=lambda r: r[1])[0],
    "N_INTRA": str(len(intra_labels)), "N_ABOVE_OPEN": str(n_above_open), "N_GAP_UP": str(n_gap_up),
})


def gi(code, field):
    a = idx0.get(code) or {}
    prev = a.get("prev") or 0
    return f"{((a.get(field) or 0) / prev - 1) * 100:+.2f}" if prev else "0.00"


def gp(code):
    return f"{(idx0.get(code) or {}).get('pct', 0):+.2f}"


def yoy_of(code):
    a, b = idx0.get(code) or {}, idx1.get(code) or {}
    if not b or not b.get("amount_wan"):
        return 0.0
    return ((a.get("amount_wan") or 0) / b["amount_wan"] - 1) * 100


V.update({
    "SH_GAP": gi("sh000001", "open"), "SH_HIGH": gi("sh000001", "high"), "SH_LOW": gi("sh000001", "low"),
    "SH_PCT": gp("sh000001"),
    "SH_DRAW": f"{((idx0['sh000001']['price'] / (idx0['sh000001'].get('high') or 1)) - 1) * 100:+.2f}",
    "CY_GAP": gi("sz399006", "open"), "CY_HIGH": gi("sz399006", "high"), "CY_PCT": gp("sz399006"),
    "KC_GAP": gi("sh000688", "open"), "KC_HIGH": gi("sh000688", "high"), "KC_LOW": gi("sh000688", "low"),
    "KC_PCT": gp("sh000688"),
    "KC_RANGE": f"{float(gi('sh000688', 'high')) - float(gi('sh000688', 'low')):.2f}",
    "KC_REBOUND": f"{float(gp('sh000688')) - float(gi('sh000688', 'low')):.2f}",
    "GZ_HIGH": gi("sz399303", "high"), "GZ_PCT": gp("sz399303"),
    "SH50_HIGH": gi("sh000016", "high"), "SH50_PCT": gp("sh000016"),
    "SH50_YOY": f"{yoy_of('sh000016'):+.1f}",
    "KC_YOY": f"{yoy_of('sh000688'):+.1f}",
    "BZ50_YOY": f"{yoy_of('bj899050'):+.1f}",
    "ZXX_YOY": f"{yoy_of('sz399005'):+.1f}",
    "ZZ500_YOY": f"{yoy_of('sh000905'):+.1f}",
    "ZZ1000_YOY": f"{yoy_of('sh000852'):+.1f}",
    "GZ_YOY": f"{yoy_of('sz399303'):+.1f}",
    "HS300_YOY": f"{yoy_of('sh000300'):+.1f}",
})

# ================= 涨停股结构 =================
amt_sum = sum(x["amount"] or 0 for x in r0) / 1e8
amt_sum_y = sum(x["amount"] or 0 for x in r1) / 1e8
fund = sum(x["fund"] or 0 for x in r0) / 1e8
fund_y = sum(x["fund"] or 0 for x in r1) / 1e8
med_amt = median([x["amount"] or 0 for x in r0]) / 1e8
med_amt_y = median([x["amount"] or 0 for x in r1]) / 1e8
V.update({
    "AMT_SUM": f"{amt_sum:,.1f}", "AMT_SUM_Y": f"{amt_sum_y:,.1f}",
    "AMT_SUM_PCT": f"{(amt_sum / amt_sum_y - 1) * 100:+.1f}",
    "AMT_SUM_PCT_ABS": f"{abs((amt_sum / amt_sum_y - 1) * 100):.1f}",
    "SHARE": f"{amt_sum / AMT * 100:.1f}", "SHARE_Y": f"{amt_sum_y / AMT_Y * 100:.1f}",
    "FUND": f"{fund:.1f}", "FUND_Y": f"{fund_y:.1f}",
    "FUND_PCT": f"{(fund / fund_y - 1) * 100:+.1f}",
    "FUND_PCT_ABS": f"{abs((fund / fund_y - 1) * 100):.1f}",
    "FUND_MED": f"{median([x['fund'] or 0 for x in r0]) / 1e8:.2f}",
    "FUND_MED_Y": f"{median([x['fund'] or 0 for x in r1]) / 1e8:.2f}",
    "MED_AMT": f"{med_amt:.2f}", "MED_AMT_Y": f"{med_amt_y:.2f}",
    "YIZI": str(sum(1 for x in r0 if x["limit_up_type"] == "一字板")),
    "TZI": str(sum(1 for x in r0 if x["limit_up_type"] == "T字板")),
    "HSB": str(sum(1 for x in r0 if x["limit_up_type"] == "换手板")),
    "HSB_PCT": f"{sum(1 for x in r0 if x['limit_up_type'] == '换手板') / len(r0) * 100:.0f}",
    "CYB_N": str(sum(1 for x in r0 if x["code"].startswith(("30", "68")))),
    "CYB_PCT": f"{sum(1 for x in r0 if x['code'].startswith(('30', '68'))) / len(r0) * 100:.1f}",
})
mv0 = [x["ltsz"] or 0 for x in r0]
mv1 = [x["ltsz"] or 0 for x in r1]
big0 = [x for x in r0 if (x["ltsz"] or 0) > 1e10]
big1 = [x for x in r1 if (x["ltsz"] or 0) > 1e10]
V.update({
    "ZT_MED_MV": f"{median(mv0) / 1e8:.0f}", "ZT_MED_MV_Y": f"{median(mv1) / 1e8:.0f}",
    "MV_MULT": f"{median(mv0) / median(mv1):.1f}",
    "ZT_BIG_N": str(len(big0)), "ZT_BIG_Y": str(len(big1)),
    "ZT_BIG_PCT": f"{len(big0) / len(r0) * 100:.0f}",
    "ZT_BIG_PCT_Y": f"{len(big1) / len(r1) * 100:.0f}",
    "ZT_MV_MAX": f"{max(mv0) / 1e8:,.0f}", "ZT_MV_MAX_Y": f"{max(mv1) / 1e8:,.0f}",
})

# ================= 梯队 =================
lad0, lad1 = s0["ladder"], s1["ladder"]


def ladn(d, k):
    return int(d.get(str(k), 0))


V.update({
    "MAXB": str(s0["max_board"]), "MAXB_Y": str(s1["max_board"]), "MAXB_0": str(S2["senti"][D2]["max_board"]),
    "LB": str(s0["lianban"]), "LB_Y": str(s1["lianban"]),
    "LB_D": signed(s0["lianban"] - s1["lianban"]), "LB_ADD": str(s0["lianban"] - s1["lianban"]),
    "LB_PCT": f"{s0['lianban'] / ZT * 100:.1f}", "LB_PCT_Y": f"{s1['lianban'] / ZT_Y * 100:.1f}",
    "LB_PCT_D": f"{s0['lianban'] / ZT * 100 - s1['lianban'] / ZT_Y * 100:+.1f}",
    "SHOU": str(ladn(lad0, 1)), "SHOU_Y": str(ladn(lad1, 1)),
    "SHOU_PCT": f"{ladn(lad0, 1) / ZT * 100:.1f}",
    "SHOU_PCT_0": f"{ladn(lad1, 1) / ZT_Y * 100:.1f}",
    "LAD2": str(ladn(lad0, 2)), "LAD2_Y": str(ladn(lad1, 2)),
    "LAD2_MULT": f"{ladn(lad0, 2) / ladn(lad1, 2):.1f}" if ladn(lad1, 2) else "—",
    "LAD3": str(ladn(lad0, 3)), "LAD3_Y": str(ladn(lad1, 3)),
    "LAD4": str(ladn(lad0, 4)), "LAD4_Y": str(ladn(lad1, 4)),
})
V["ZT_NEW"] = str(ZT - sum(1 for x in perf if x["again"]))
V["ZT_NEW_PCT"] = f"{(ZT - sum(1 for x in perf if x['again'])) / ZT * 100:.0f}"

lad_rows = []
for lv in range(1, max(int(V["MAXB"]), int(V["MAXB_Y"])) + 1):
    t, y = ladn(lad0, lv), ladn(lad1, lv)
    d = t - y
    lad_rows.append('<tr><td>%d 板</td><td class="hl">%d</td><td>%d</td><td class="%s">%s</td></tr>'
                    % (lv, t, y, cls(d), signed(d)))
V["TBL_LAD"] = "\n".join(lad_rows)

lb0 = [x for x in r0 if (x["lbc"] or 1) >= 2]
lb1 = [x for x in r1 if (x["lbc"] or 1) >= 2]
mb_list = [x for x in lb0 if (x["lbc"] or 1) == s0["max_board"]]
V["MAXB_CN"] = str(len(mb_list))
V["MAXB_NAMES"] = "、".join(x["name"] for x in mb_list) or "—"
V["MAXB_DETAIL"] = "；".join("%s（%s，%d 板，封单 %.2f 亿、成交 %.2f 亿、首封 %s）"
                          % (x["name"], x["hybk"], x["lbc"], (x["fund"] or 0) / 1e8,
                             (x["amount"] or 0) / 1e8, x["fbt"] or "—")
                          for x in sorted(mb_list, key=lambda y: -(y["fund"] or 0)))
lad3y = [x for x in lb1 if (x["lbc"] or 1) == 3]
lad4y = [x for x in lb1 if (x["lbc"] or 1) == 4]
_pm = {x["code"]: x["pct"] for x in perf}
V["LAD3Y_N"] = str(len(lad3y))
V["LAD3Y_NAMES"] = "、".join(x["name"] for x in lad3y) or "无"
V["LAD3Y_PCT"] = "、".join("%+.2f%%" % _pm.get(x["code"], 0) for x in lad3y) or "—"
V["LAD4Y_N"] = str(len(lad4y))
V["LAD4Y_NAMES"] = "、".join(x["name"] for x in lad4y) or "无"
V["LAD4Y_PCT"] = "、".join("%+.2f%%" % _pm.get(x["code"], 0) for x in lad4y) or "—"
V["MAXB_ADV_PCT"] = f"{len(mb_list) / len(lad3y) * 100:.1f}" if lad3y else "—"

lian_rows = []
for x in sorted(lb0, key=lambda y: (-(y["lbc"] or 1), -(y["fund"] or 0))):
    lian_rows.append('<tr><td class="hl">%s</td><td>%d</td><td>%s</td><td>%s</td><td>%.2f</td><td>%.2f</td><td>%.1f%%</td><td class="note">%s</td></tr>'
                     % (x["name"], x["lbc"], x["hybk"], (x["fbt"] or "—")[:5], (x["fund"] or 0) / 1e8,
                        (x["amount"] or 0) / 1e8, x["turnover"] or 0, x["reason"]))
V["TBL_LIANBAN"] = "\n".join(lian_rows)

# ================= 晋级 / 溢价 =================
adv = [x for x in perf if x["again"]]
sb = [x for x in perf if (x["lbc"] or 1) == 1]
lbp = [x for x in perf if (x["lbc"] or 1) >= 2]
adv_y = (sum(1 for x in S1["perf"] if x["again"]) / len(S1["perf"]) * 100) if S1["perf"] else 0


def gstat(g):
    ps = [x["pct"] for x in g]
    return len(g), sum(1 for x in g if x["again"]) / len(g) * 100, mean(ps), median(ps), \
        sum(1 for p in ps if p < 0), sum(1 for p in ps if p <= -5)


ps_all = [x["pct"] for x in perf]
_sbn, _sbr, _sbm, _sbmed, _sbdn, _sbd5 = gstat(sb)
_lbn, _lbr, _lbm, _lbmed, _lbdn, _lbd5 = gstat(lbp)
V.update({
    "ADV_RATE": f"{len(adv) / len(perf) * 100:.1f}", "ADV_RATE_Y": f"{adv_y:.1f}",
    "ADV_N": str(len(adv)), "ADV_TOT": str(len(perf)),
    "PERF_MEAN": f"{mean(ps_all):+.2f}", "PERF_MED": f"{median(ps_all):+.2f}",
    "PERF_DN_N": str(sum(1 for p in ps_all if p < 0)),
    "PERF_DN_PCT": f"{sum(1 for p in ps_all if p < 0) / len(ps_all) * 100:.1f}",
    "PERF_DN5_N": str(sum(1 for p in ps_all if p <= -5)),
    "SB_N": str(_sbn), "SB_RATE": f"{_sbr:.1f}", "SB_MEAN": f"{_sbm:+.2f}", "SB_MED": f"{_sbmed:+.2f}",
    "SB_DN_N": str(_sbdn), "SB_DN5_N": str(_sbd5),
    "LB_N": str(_lbn), "LB_RATE": f"{_lbr:.1f}", "LB_MEAN": f"{_lbm:+.2f}", "LB_MED": f"{_lbmed:+.2f}",
    "LB_DN_N": str(_lbdn), "LB_DN5_N": str(_lbd5),
    "GAP": f"{_sbmed - _lbmed:+.2f}", "GAP_CLS": "up" if _sbmed > _lbmed else "down",
})
_psb = [x["pct"] for x in S1["perf"] if (x["lbc"] or 1) == 1]
_plb = [x["pct"] for x in S1["perf"] if (x["lbc"] or 1) >= 2]
V["GAP_Y"] = f"{median(_psb) - median(_plb):+.2f}" if _psb and _plb else "+0.00"

sr = sorted(perf, key=lambda x: -x["pct"])
V["PERF_TOP5"] = "、".join("%s %+.2f%%" % (x["name"], x["pct"]) for x in sr[:5])
V["PERF_BOT5"] = "、".join("%s %+.2f%%" % (x["name"], x["pct"]) for x in sr[-5:])
V["PERF_WEAK"] = sr[-1]["name"]
for nm, key in [("沪电股份", "BOT_HD"), ("深南电路", "BOT_SN"), ("紫竹高科", "BOT_ZZ"),
                ("宝明科技", "BOT_BM"), ("大连友谊", "BOT_DL")]:
    V[key] = f"{_pm.get(next((x['code'] for x in perf if x['name'] == nm), ''), 0):+.2f}"

# ================= 炸板 =================
sealed = [x for x in zb0 if x.get("p") and x.get("ztp") and x["p"] >= x["ztp"]]
zb_amt = sum(x.get("amount") or 0 for x in zb0) / 1e8
zb1_amt = sum(x.get("amount") or 0 for x in pool(A1, "em_ZB")) / 1e8
V.update({
    "ZB": str(s0["zb"]), "ZB_Y": str(s1["zb"]),
    "ZB_SEALED_N": str(len(sealed)),
    "ZB_SEAL_PCT": f"{len(sealed) / len(zb0) * 100:.0f}" if zb0 else "0",
    "ZB_SEALED_TXT": ("（%s）" % "、".join("%s %+.2f%%" % (x["n"], x.get("zdp") or 0) for x in sealed)) if sealed else "（零回封）",
    "ZB_AMT": f"{zb_amt:.1f}", "ZB_AMT_Y": f"{zb1_amt:.1f}",
    "ZB_RATIO": f"{zb_amt / amt_sum:.2f}", "ZB_RATIO_Y": f"{zb1_amt / amt_sum_y:.2f}",
    "ZB_MED_MV": f"{median([(x.get('ltsz') or 0) / 1e8 for x in zb0]):.0f}" if zb0 else "0",
    "ZB_BIG_N": str(sum(1 for x in zb0 if (x.get("ltsz") or 0) > 1e10)),
    "ZB_EM": str((A0.get("em_ZB") or {}).get("tc") or 0),
    "ZB_EM_DIFF": str(abs(((A0.get("em_ZB") or {}).get("tc") or 0) - s0["zb"])),
    "ZB_EM_DIFF_TXT": "两源差异属收录时点不同" if ((A0.get("em_ZB") or {}).get("tc") or 0) != s0["zb"] else "两源一致",
})
_ztop = sorted(zb0, key=lambda y: -(y.get("amount") or 0))[:5]
V["ZB_TOP5_TXT"] = "、".join("%s（%s，成交 %.1f 亿、收 %+.2f%%、流通 %.0f 亿）"
                          % (x["n"], x.get("hybk") or "—", (x.get("amount") or 0) / 1e8,
                             x.get("zdp") or 0, (x.get("ltsz") or 0) / 1e8) for x in _ztop)


def zb_by(name):
    x = next((y for y in zb0 if y["n"] == name), None)
    return ("%.1f" % ((x.get("amount") or 0) / 1e8), "%+.2f" % (x.get("zdp") or 0)) if x else ("—", "—")


for nm, key in [("通富微电", "ZBT1"), ("雅克科技", "ZBT2"), ("迈为股份", "ZBT3"),
                ("赤峰黄金", "ZBT_CG"), ("兴业银锡", "ZBT_XY")]:
    a, p = zb_by(nm)
    V[key] = a
    V[key + "_PCT"] = p

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
V["TBL_TS"] = "\n".join('<tr><td>%s</td><td class="hl">%d</td><td>%d</td><td class="%s">%s</td></tr>'
                        % (k, t0.get(k, 0), t1.get(k, 0), cls(t0.get(k, 0) - t1.get(k, 0)),
                           signed(t0.get(k, 0) - t1.get(k, 0))) for k in KEYS)

# ================= 簇 =================
hy0 = S["hy0"]
# 本次重抓的 D1 东财池比 D1 当日抓取少 3 只（601208 东材科技 / 603248 锡华科技 / 301697 贝特利），
# 行业字段缺失会落到空键，导致行业迁移表与「光伏设备昨日家数」被低估。用 D1 当日抓取回填。
hy1 = {}
for _c in ths1:
    _h = ((_em1_fresh_map.get(_c) or {}).get("hybk")
          or (_em1_day_map.get(_c) or {}).get("hybk") or "")
    hy1[_h] = hy1.get(_h, 0) + 1
assert sum(hy1.values()) == len(ths1) and not hy1.get("")
CALC_HY = ["半导体", "元件", "光学光电", "电子化学", "其他电子", "通信设备", "自动化设"]
PV_HY = ["光伏设备"]
AI_HY = ["出版", "影视院线", "数字媒体", "广告营销", "IT服务Ⅱ", "软件开发", "游戏Ⅱ", "电视广播"]
CONS_HY = ["一般零售", "服装家纺", "饮料乳品", "休闲食品"]
BATT_HY = ["电池"]

calc0 = [x for x in r0 if x["hybk"] in CALC_HY]
calc1 = [x for x in r1 if x["hybk"] in CALC_HY]
calc_amt = sum(x["amount"] or 0 for x in calc0) / 1e8
calc_lb = [x for x in calc0 if (x["lbc"] or 1) >= 2]
V.update({
    "CALC_N": str(len(calc0)), "CALC_N_Y": str(len(calc1)),
    "CALC_DN_PCT": f"{abs(1 - len(calc0) / len(calc1)) * 100:.1f}",
    "CALC_LB": str(len(calc_lb)),
    "CALC_LB_TXT": "、".join("%s %d 板" % (x["name"], x["lbc"]) for x in calc_lb) or "无",
    "CALC_AMT": f"{calc_amt:.1f}",
    "CALC_SHARE": f"{calc_amt / amt_sum * 100:.1f}",
    "CALC_SHARE_PCT": f"{len(calc0) / ZT * 100:.1f}",
    "CALC_HY_TXT": " / ".join(CALC_HY),
    "CALC_MV_MED": f"{median([(x['ltsz'] or 0) / 1e8 for x in calc0]):.0f}" if calc0 else "0",
    "CALC_ADV_NEED": str(max(8, round(len(calc0) * 0.3))),
})

pv0 = [x for x in r0 if x["hybk"] in PV_HY]
pv_amt = sum(x["amount"] or 0 for x in pv0) / 1e8
pv_lb = [x for x in pv0 if (x["lbc"] or 1) >= 2]
V.update({
    "PV_N": str(len(pv0)), "PV_N_Y": str(sum(hy1.get(k, 0) for k in PV_HY)),
    "PV_ADD": str(len(pv0) - sum(hy1.get(k, 0) for k in PV_HY)),
    "PV_LB": str(len(pv_lb)),
    "PV_LB_TXT": "、".join("%s %d 板" % (x["name"], x["lbc"]) for x in pv_lb) or "无",
    "PV_AMT": f"{pv_amt:.1f}", "PV_SHARE": f"{pv_amt / amt_sum * 100:.1f}",
    "PV_AMT_DOUBLE": f"{pv_amt * 2:.0f}",
    "PV_BIG_N": str(sum(1 for x in pv0 if (x["ltsz"] or 0) > 1e10)),
    "PV_MED_MV": f"{median([(x['ltsz'] or 0) / 1e8 for x in pv0]):.0f}" if pv0 else "0",
    "PV_FUND": f"{sum(x['fund'] or 0 for x in pv0) / 1e8:.2f}",
    "PV_TOP_TXT": "、".join("%s（%d 板，成交 %.1f 亿、封单 %.2f 亿）"
                          % (x["name"], x["lbc"] or 1, (x["amount"] or 0) / 1e8, (x["fund"] or 0) / 1e8)
                          for x in sorted(pv0, key=lambda y: -(y["amount"] or 0))[:4]),
})

gold0 = [x for x in r0 if x["hybk"] in ("贵金属", "小金属")]
gold1 = [x for x in r1 if x["hybk"] in ("贵金属", "小金属")]
gold_amt = sum(x["amount"] or 0 for x in gold0) / 1e8
V.update({
    "GOLD_N": str(len(gold0)), "GOLD_N_Y": str(len(gold1)),
    "GOLD_AMT": f"{gold_amt:.1f}", "GOLD_SHARE": f"{gold_amt / amt_sum * 100:.1f}",
    "GOLD_LB": str(sum(1 for x in gold0 if (x["lbc"] or 1) >= 2)),
    "GOLD_TOP_TXT": "、".join("%s（%s，成交 %.1f 亿）" % (x["name"], x["hybk"], (x["amount"] or 0) / 1e8)
                            for x in sorted(gold0, key=lambda y: -(y["amount"] or 0))[:4]),
    "HY_GOLD": str(hy0.get("贵金属", 0)), "HY_GOLD_Y": str(hy1.get("贵金属", 0)),
    "HY_XJS": str(hy0.get("小金属", 0)), "HY_XJS_Y": str(hy1.get("小金属", 0)),
})
cons0 = sum(hy0.get(k, 0) for k in CONS_HY)
cons1 = sum(hy1.get(k, 0) for k in CONS_HY)
batt0 = sum(hy0.get(k, 0) for k in BATT_HY)
batt1 = sum(hy1.get(k, 0) for k in BATT_HY)
V.update({
    "BATT_N": str(batt0), "BATT_N_Y": str(batt1), "CONS_N": str(cons0), "CONS_N_Y": str(cons1),
    "YMAIN_N": str(batt0 + cons0),
    "AI_N": str(sum(hy0.get(k, 0) for k in AI_HY)), "AI_N_Y": str(sum(hy1.get(k, 0) for k in AI_HY)),
})
for k, tag in [("半导体", "BDT"), ("元件", "YJ"), ("光学光电", "GX"), ("自动化设", "ZD"),
               ("光伏设备", "PV"), ("汽车零部", "QCLB"), ("电池", "DC"), ("一般零售", "LS"),
               ("服装家纺", "FZ"), ("饮料乳品", "YL")]:
    V["HY_" + tag] = str(hy0.get(k, 0))
    V["HY_" + tag + "_Y"] = str(hy1.get(k, 0))
    V["HY_" + tag + "_ADD"] = signed(hy0.get(k, 0) - hy1.get(k, 0))

# ================= 昨日跌停池修复 =================
zt_codes = {x["code"] for x in r0}
dt1_rows, dt1_vals, dt1_zt = [], [], 0
for x in sorted([y for y in dt1 if y["c"] in qdt1], key=lambda y: qdt1[y["c"]].get("pct") or 0):
    q = qdt1[x["c"]]
    p = q.get("pct") or 0
    dt1_vals.append(p)
    hit = x["c"] in zt_codes
    dt1_zt += hit
    note = "→ 今日涨停（反包）" if hit else ("连续第 2 日跌停" if p <= -9.8 else "—")
    dt1_rows.append('<tr><td>%s</td><td class="hl">%s</td><td>%s</td><td class="%s">%+.2f%%</td><td>%.2f</td><td>%s</td></tr>'
                    % (x["c"], x["n"], x.get("hybk") or "—", "up" if p > 0 else "down", p,
                       q.get("amount", 0), note))
V.update({
    "TBL_DT1": "\n".join(dt1_rows),
    "DT1_N": str(len(dt1_vals)),
    "DT1_MEAN": f"{mean(dt1_vals):+.2f}" if dt1_vals else "0.00",
    "DT1_MED": f"{median(dt1_vals):+.2f}" if dt1_vals else "0.00",
    "DT1_UP": str(sum(1 for v in dt1_vals if v > 0)),
    "DT1_DN": str(sum(1 for v in dt1_vals if v < 0)),
    "DT1_ZT": str(dt1_zt),
    "DT1_MISS": str(len(dt1) - len(dt1_vals)),
    "DT_NAMES": "、".join(x["n"] for x in dt0) or "无（今日 0 家跌停）",
})
dt_amt = 0.0                       # 今日无跌停股
dt_amt_y = 57.1                    # 昨日跌停股合计成交（11-04 报告口径）
V.update({
    "DT_AMT": f"{dt_amt:.1f}", "DT_AMT_Y": f"{dt_amt_y:.1f}",
    "DT_RATIO": f"{dt_amt / amt_sum:.2f}", "DT_RATIO_Y": f"{dt_amt_y / amt_sum_y:.2f}",
    "DT_EM": str(len(dt0)),
})

# ================= 概念板块榜 =================
blk = sorted((A0.get("ths_block") or []), key=lambda y: -(y.get("limit_up_num") or 0))
V["TBL_CONC"] = "\n".join(
    '<tr><td>%s</td><td class="hl">%d</td><td>%d</td><td class="%s">%.0f%%</td><td class="note">%s</td></tr>'
    % (x.get("name"), x.get("limit_up_num") or 0, x.get("continuous_plate_num") or 0,
       "up" if (x.get("continuous_plate_num") or 0) / max(x.get("limit_up_num") or 1, 1) >= 0.4 else "down",
       (x.get("continuous_plate_num") or 0) / max(x.get("limit_up_num") or 1, 1) * 100, x.get("high") or "—")
    for x in blk[:10])
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
_bk = {x.get("name"): x for x in (A0.get("ths_block") or [])}
for nm, tag in [("光伏概念", "PVC"), ("储能", "ESC")]:
    x = _bk.get(nm) or {}
    V[tag + "_N"] = str(x.get("limit_up_num") or 0)
    V[tag + "_LB"] = str(x.get("continuous_plate_num") or 0)
    V[tag + "_R"] = f"{(x.get('continuous_plate_num') or 0) / max(x.get('limit_up_num') or 1, 1) * 100:.0f}"
V["PV_CONC_N"] = V["PVC_N"]
V["PV_CONC_LB"] = V["PVC_LB"]
V["PV_CONC_R"] = V["PVC_R"]
V["ES_CONC_N"] = V["ESC_N"]
V["ES_CONC_LB"] = V["ESC_LB"]
V["ES_CONC_R"] = V["ESC_R"]
V["PV_CONC_GAP"] = str(int(V["PV_CONC_N"]) - int(V["PV_N"]))

# ================= 行业迁移 =================
_hk = set(hy0) | set(hy1)
_hrows = [(k, hy1.get(k, 0), hy0.get(k, 0)) for k in _hk if k]
_hrows.sort(key=lambda r: -((r[1] + r[2]) + abs(r[2] - r[1]) * 2))
V["TBL_HY"] = "\n".join(
    '<tr><td>%s</td><td class="hl">%d</td><td>%d</td><td class="%s">%s</td><td class="note">%s</td></tr>'
    % (k, b, a, cls(b - a), signed(b - a), "流入" if b > a else ("流出" if b < a else "持平"))
    for k, a, b in _hrows[:18])
V["ZT_HY_N"] = str(len([k for k in hy0 if hy0[k]]))
V["ZT_HY_N_Y"] = str(len([k for k in hy1 if hy1[k]]))
V["HY_ZERO_N"] = str(len([k for k in hy1 if hy1.get(k) and not hy0.get(k)]))
V["HY_NEW_N"] = str(len([k for k in hy0 if hy0.get(k) and not hy1.get(k)]))
V["HY_AVG"] = f"{ZT / len([k for k in hy0 if hy0[k]]):.1f}"
# 流入/流出文字由数据生成，禁止手写（回填行业字段后家数会变）
_in = sorted([r for r in _hrows if r[2] > r[1]], key=lambda r: (-r[2], -(r[2] - r[1]), r[0]))
_out = sorted([r for r in _hrows if r[2] < r[1]], key=lambda r: (-(r[1] - r[2]), -r[1], r[0]))


def _hy_txt(rows, pos):
    if not rows:
        return "无"
    head = rows[0]
    txt = "%s %s" % (head[0], signed(head[2] - head[1]))
    rest = ["%s %s" % (k, signed(b - a)) for k, a, b in rows[1:4]]
    if rest:
        txt += "、" + "、".join(rest)
    return txt


V["HY_IN_TXT"] = _hy_txt(_in, True)
V["HY_OUT_TXT"] = _hy_txt(_out, False)

# ================= 情绪三日表 =================
S2S = S2["senti"][D2]
_t_d2 = A2["ths_zt"]["total"]["today"]["history_num"]
_dt_d2 = S2S["limit_down_count"]["today"]["history_num"]
_rows = [
    ("涨停家数", (S2S["zt"], ZT_Y, ZT), cls(ZT - ZT_Y), signed(ZT - ZT_Y)),
    ("炸板家数", (S2S["zb"], s1["zb"], s0["zb"]), cls(s0["zb"] - s1["zb"], inverse=True), signed(s0["zb"] - s1["zb"])),
    ("触及涨停（参与度）", (_t_d2, TOUCH_Y, TOUCH), cls(TOUCH - TOUCH_Y), signed(TOUCH - TOUCH_Y)),
    ("封板率", (f"{S2S['seal_rate']*100:.1f}%", f"{SEAL_Y:.1f}%", f"{SEAL:.1f}%"), cls(SEAL - SEAL_Y), f"{SEAL - SEAL_Y:+.1f}pct"),
    ("跌停家数（封死）", (S2S["dt"], DT_Y, DT), cls(DT - DT_Y, inverse=True), signed(DT - DT_Y)),
    ("触及跌停", (_dt_d2, DTOUCH_Y, DTOUCH), cls(DTOUCH - DTOUCH_Y, inverse=True), signed(DTOUCH - DTOUCH_Y)),
    ("跌停封死率", (f"{S2S['limit_down_count']['today']['rate']*100:.1f}%", f"{DSEAL_Y:.1f}%", f"{DSEAL:.1f}%"),
     cls(DSEAL - DSEAL_Y, inverse=True), f"{DSEAL - DSEAL_Y:+.1f}pct"),
    ("涨停/跌停比", (f"{S2S['zt']/S2S['dt']:.1f}" if S2S["dt"] else "—", f"{ZT_Y/DT_Y:.1f}", f"{ZT/DT:.1f}" if DT else "∞"),
     cls(DT - DT_Y, inverse=True), "跌停归零" if DT == 0 else ""),
]
V["TBL_SENTI"] = "\n".join('<tr><td>%s</td><td>%s</td><td>%s</td><td class="hl">%s</td><td class="%s">%s</td></tr>'
                           % (nm, v[0], v[1], v[2], c, d) for nm, v, c, d in _rows)

# ================= 簇对比表 =================
MAIN_DEF = [("算力硬件链（半导体/元件/光学光电/电子化学/其他电子/通信设备/自动化设）", CALC_HY),
            ("光伏设备（光伏链主口径）", PV_HY),
            ("贵金属 + 小金属", ["贵金属", "小金属"]),
            ("AI 内容 / 传媒（出版/影视/数媒/广告/IT服务/软件/游戏/广电）", AI_HY),
            ("消费（一般零售/服装家纺/饮料乳品/休闲食品）", CONS_HY),
            ("电池 / 固态电池", BATT_HY)]
_rows_m, m_labels, m_today, m_prev = [], [], [], []
for nm, keys in MAIN_DEF:
    n0, n1 = sum(hy0.get(k, 0) for k in keys), sum(hy1.get(k, 0) for k in keys)
    lbn = sum(1 for x in r0 if x["hybk"] in keys and (x["lbc"] or 1) >= 2)
    amt = sum(x["amount"] or 0 for x in r0 if x["hybk"] in keys) / 1e8
    _rows_m.append('<tr><td>%s</td><td>%d</td><td class="hl">%d</td><td>%d</td><td>%.1f</td><td>%.1f%%</td></tr>'
                   % (nm, n1, n0, lbn, amt, amt / amt_sum * 100))
    m_labels.append(nm.split("（")[0])
    m_today.append(n0)
    m_prev.append(n1)
V["TBL_MAIN"] = "\n".join(_rows_m)

# ================= westock =================
def swp(name, key="pct"):
    return (SW0.get(name) or {}).get(key, 0)


for nm, tag in [("光伏设备", "PV"), ("数字媒体", "SZMT"), ("贵金属", "GOLD"), ("广告营销", "GG"),
                ("影视院线", "YS"), ("电池", "DC"), ("固态电池", "GTDC"), ("人工智能", "RGZN"),
                ("AI应用", "AIYY"), ("半导体", "BDT"), ("元件", "YJ"), ("白酒Ⅱ", "BJ"), ("保险Ⅱ", "BX")]:
    V["SW_" + tag + "_PCT"] = f"{swp(nm):.2f}"
    V["SW_" + tag + "_FLOW"] = f"{swp(nm, 'flow') / 1e4:.2f}"
    V["SW_" + tag + "_UD"] = str(swp(nm, "updown") or "—")

# ================= 口径差异 =================
zt_em_tc = (A0.get("em_ZT") or {}).get("tc") or 0
em_pool = pool(A0, "em_ZT")
ths_codes = {x["code"] for x in r0}
em_codes = {x["c"] for x in em_pool}
em_only = [x for x in em_pool if x["c"] not in ths_codes]
ths_only = [x for x in r0 if x["code"] not in em_codes]
_parts = []
for tag, lst in [("东财多出的北交所标的", [x for x in em_only if x["c"].startswith("92")]),
                 ("东财多出的沪深标的", [x for x in em_only if not x["c"].startswith("92")])]:
    if lst:
        _parts.append("%s %d 只（%s）" % (tag, len(lst), "、".join(x["c"] + " " + x["n"] for x in lst)))
if ths_only:
    _parts.append("同花顺多出的标的 %d 只（%s）" % (len(ths_only), "、".join(x["code"] + " " + x["name"] for x in ths_only)))
V["ZT_EM_TC"] = str(zt_em_tc)
V["ZT_EM_DIFF"] = str(zt_em_tc - ZT)
V["ZT_EM_DIFF_TXT"] = ("净差 %+d 只；" % (zt_em_tc - ZT)) + "；".join(_parts) if _parts else "两源一致"

# ================= 大市值四只 =================
for nm, key in [("北方华创", "BIG4_0"), ("药明康德", "BIG4_1"), ("沪电股份", "BIG4_2"), ("深南电路", "BIG4_3")]:
    V[key] = f"{_pm.get(next((x['code'] for x in perf if x['name'] == nm), ''), 0):+.2f}"

# ================= JS =================
yoy_sorted = sorted(yoy, key=lambda r: r[1])
rows_amt = [[r[0], round(r[1], 1)] for r in yoy_sorted]
js = {
    "JS_SENTI": {"days": [V["D2_LABEL"], V["D1_LABEL"], V["D0_LABEL"]],
                 "zt": [S2S["zt"], ZT_Y, ZT], "zb": [S2S["zb"], s1["zb"], s0["zb"]],
                 "dt": [S2S["dt"], DT_Y, DT],
                 "seal": [round(S2S["seal_rate"] * 100, 1), round(SEAL_Y, 1), round(SEAL, 1)]},
    "JS_AMT": {"labels": [r[0] for r in rows_amt], "vals": [r[1] for r in rows_amt],
               "colors": ["#d93025" if r[1] > 0 else "#12805c" for r in rows_amt]},
    "JS_INTRA": {"labels": intra_labels, "gap": intra_gap, "high": intra_high, "low": intra_low, "close": intra_close},
    "JS_FLOW": {"labels": ["%s（%d 家）" % (V["D1_LABEL"], ZT_Y), "%s（%d 家）" % (V["D0_LABEL"], ZT)],
                "total": [round(AMT_Y, 0), round(AMT, 0)],
                "ztamt": [round(amt_sum_y, 1), round(amt_sum, 1)],
                "nzt": [ZT_Y, ZT]},
    "JS_LAD": {"labels": [f"{lv}板" for lv in range(1, max(int(V["MAXB"]), int(V["MAXB_Y"])) + 1)],
               "today": [ladn(lad0, lv) for lv in range(1, max(int(V["MAXB"]), int(V["MAXB_Y"])) + 1)],
               "prev": [ladn(lad1, lv) for lv in range(1, max(int(V["MAXB"]), int(V["MAXB_Y"])) + 1)]},
    "JS_MAIN": {"labels": m_labels[::-1], "today": m_today[::-1], "prev": m_prev[::-1]},
    "JS_TS": {"labels": KEYS, "today": [t0.get(k, 0) for k in KEYS], "prev": [t1.get(k, 0) for k in KEYS]},
}
_buckets = [("跌停", -100, -9.8), ("-9.8~-5", -9.8, -5), ("-5~-2", -5, -2), ("-2~0", -2, 0),
            ("0~2", 0, 2), ("2~5", 2, 5), ("5~9.8", 5, 9.8), ("涨停", 9.8, 100)]
_bv = [sum(1 for p in ps_all if lo <= p < hi) for _, lo, hi in _buckets]
js["JS_PERF"] = {"labels": [b[0] for b in _buckets], "vals": _bv,
                 "colors": ["#12805c", "#12805c", "#3f9e7c", "#9ec7b7", "#e8b4ae", "#e07a70", "#d93025", "#d93025"]}
for k, v in js.items():
    V[k] = json.dumps(v, ensure_ascii=False)

# ================= 渲染 =================
tpl = open(TPL, encoding="utf-8").read()
need = set(re.findall(r"__([A-Z_0-9]+)__", tpl))
miss = sorted(need - set(V))
print("missing placeholders:", miss)
assert not miss, "模板占位符缺值: %s" % miss

html = tpl
for k, v in V.items():
    html = html.replace("__%s__" % k, str(v))
resid = re.findall(r"__[A-Z_0-9]+__", html)
print("placeholder residue:", resid)
assert not resid, "占位符残留: %s" % resid
bad = re.findall(r"\+\+\d", html)
print("double-plus:", bad)
assert not bad
html = html.replace("__", "—")

outp = os.path.join(REP, f"涨停复盘对比-{D0}.html")
open(outp, "w", encoding="utf-8").write(html)
print("saved ->", outp, len(html), "chars")
