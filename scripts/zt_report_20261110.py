# -*- coding: utf-8 -*-
"""涨停复盘报告 20261110 vs 20261109（三项同向修复 × AI 链全面扩散 · 高度仍缺中间层）
用法：python scripts/zt_report_20261110.py 20261110
输入：out/zt_stats_20261110.json、out/zt_review_20261110.json / 20261109.json / 20261106.json
     跌停明细 out/_dt1110.json / _dt1109.json、昨跌停股今日行情 out/_qdt1109.json、westock 榜 out/_sw1110.json
输出：reports/涨停复盘对比-20261110.html
"""
import json, os, sys, re, datetime, time as _t
from statistics import mean, median
from collections import Counter

ROOT = os.environ.get("ZT_ROOT") or os.getcwd()
OUT = os.path.join(ROOT, "out")
REP = os.path.join(ROOT, "reports")
TPL = os.path.join(ROOT, "scripts", "_report_tpl_20261110.html")
os.makedirs(REP, exist_ok=True)

D0 = sys.argv[1] if len(sys.argv) > 1 else "20261110"
S = json.load(open(os.path.join(OUT, f"zt_stats_{D0}.json"), encoding="utf-8"))
D0, D1, D2 = S["D0"], S["D1"], S["D2"]
B = json.load(open(os.path.join(OUT, f"zt_review_{D0}.json"), encoding="utf-8"))
B1 = json.load(open(os.path.join(OUT, f"zt_review_{D1}.json"), encoding="utf-8"))
B2 = json.load(open(os.path.join(OUT, f"zt_review_{D2}.json"), encoding="utf-8"))
S1 = json.load(open(os.path.join(OUT, f"zt_stats_{D1}.json"), encoding="utf-8"))
S2 = json.load(open(os.path.join(OUT, f"zt_stats_{D2}.json"), encoding="utf-8"))
A0, A1, A2 = B["dates"][D0], B["dates"][D1], B2["dates"][D2]
s0 = S["senti"][D0]

WEEK = {0: "一", 1: "二", 2: "三", 3: "四", 4: "五", 5: "六", 6: "日"}


def md(ds):
    d = datetime.date(int(ds[:4]), int(ds[4:6]), int(ds[6:8]))
    return f"{d.month}/{d.day:02d}", WEEK[d.weekday()]


def load(p, default=None):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


V = {}
for tag, ds in [("D0", D0), ("D1", D1), ("D2", D2)]:
    lab, wk = md(ds)
    V[tag + "_LABEL"] = lab
    V[tag + "_WEEK"] = "周" + wk
    V[tag + "_FULL"] = f"{ds[:4]}-{ds[4:6]}-{ds[6:8]}"
V["NEXT_D"] = "11/11 周三"
V["GEN_TIME"] = _t.strftime("%Y-%m-%d %H:%M")
V["D0"] = D0
V["D1"] = D1

# ---------------- 池子 ----------------
p0 = {x["c"]: x for x in (A0["em_ZT"]["pool"] or [])}
# ★ 昨日标签一律取 D1 当日报文文件（今日重抓的东财池会重复/缺票）
p1 = {x["c"]: x for x in (B1["dates"][D1]["em_ZT"]["pool"] or [])}
P1_FRESH = A1["em_ZT"]["pool"] or []
ths0 = {x["code"]: x for x in A0["ths_zt"]["info"]}
ths1 = {x["code"]: x for x in A1["ths_zt"]["info"]}
zb0 = A0["em_ZB"]["pool"] or []
zb1 = B1["dates"][D1]["em_ZB"]["pool"] or []
dt0 = (load(os.path.join(OUT, f"_dt{D0[4:]}.json"), {}) or {}).get("data", {}).get("pool") or []
dt1 = (load(os.path.join(OUT, f"_dt{D1[4:]}.json"), {}) or {}).get("data", {}).get("pool") or []
QDT1 = load(os.path.join(OUT, f"_qdt{D1[4:]}.json"), {}) or {}
SW = load(os.path.join(OUT, f"_sw{D0[4:]}.json"), {}) or {}
MV = load(os.path.join(OUT, f"_mv{D0[4:]}.json"), {}) or {}

assert len(p0) == len(ths0), f"今日池不一致 {len(p0)} vs {len(ths0)}"
assert sum(1 for c in ths1 if c not in p1) == 0, "昨日标签覆盖不全"


def sym_of(c):
    if c.startswith(("60", "68", "5", "11", "9")):
        return "sh" + c
    if c.startswith(("43", "83", "87", "92")):
        return "bj" + c
    return "sz" + c


_p2 = B2["dates"][D2]["em_ZT"]["pool"] or []
_t2 = {x["code"] for x in A2["ths_zt"]["info"]}
SUM_2 = sum(x.get("amount", 0) for x in _p2 if x["c"] in _t2) / 1e8
ZB_AMT_2 = sum(x.get("amount", 0) for x in (B2["dates"][D2]["em_ZB"]["pool"] or [])) / 1e8

# ---------------- 情绪 ----------------
zt0i = A0["ths_zt"]["total"]["today"]
zt1i = A1["ths_zt"]["total"]["today"]
ld0 = A0["ths_zt"]["limit_down_count"]["today"]
ld1 = A1["ths_zt"]["limit_down_count"]["today"]
ld2 = A2["ths_zt"]["limit_down_count"]["today"]
ld1r = B1["dates"][D1]["ths_zt"]["limit_down_count"]["today"]

ZT, ZT_Y = zt0i["num"], zt1i["num"]
ZT_2 = A2["ths_zt"]["total"]["today"]["num"]
TOUCH, TOUCH_Y = zt0i["history_num"], zt1i["history_num"]
TOUCH_2 = A2["ths_zt"]["total"]["today"]["history_num"]
SEAL, SEAL_Y = zt0i["rate"] * 100, zt1i["rate"] * 100
SEAL_2 = A2["ths_zt"]["total"]["today"]["rate"] * 100
ZB, ZB_Y = s0["zb"], S1["senti"][D1]["zb"]
ZB_2 = S2["senti"][D2]["zb"]
DT, DT_Y = ld0["num"], ld1["num"]
# ★ 11-06 跌停家数已在 11-09 报告盘后修正为 15 家（原报 13），封死率 65.2%（原 56.5%）
DT_2, DTOUCH_2, DSEAL_2 = 15, 23, 65.2
DTOUCH, DTOUCH_Y = ld0["history_num"], ld1["history_num"]
DSEAL, DSEAL_Y = ld0["rate"] * 100, ld1["rate"] * 100
DT_OPEN_N = ld0["open_num"]

LB, LB_Y = s0["lianban"], S1["senti"][D1]["lianban"]
LB_2 = S2["senti"][D2]["lianban"]
MAXB, MAXB_Y, MAXB_2 = s0["max_board"], S1["senti"][D1]["max_board"], S2["senti"][D2]["max_board"]
SHOU, SHOU_Y = s0["shouban"], S1["senti"][D1]["shouban"]

lad0 = {int(k): v for k, v in s0["ladder"].items()}
lad1 = {int(k): v for k, v in S1["senti"][D1]["ladder"].items()}
lad2 = {int(k): v for k, v in S2["senti"][D2]["ladder"].items()}

V.update({
    "ZT": str(ZT), "ZT_Y": str(ZT_Y), "ZT_D": f"{ZT - ZT_Y:+d}",
    "ZT_PCT_D": f"{(ZT / ZT_Y - 1) * 100:+.1f}",
    "TOUCH": str(TOUCH), "TOUCH_Y": str(TOUCH_Y), "TOUCH_D": f"{TOUCH - TOUCH_Y:+d}",
    "TOUCH_UP_PCT": f"{(TOUCH / TOUCH_Y - 1) * 100:.1f}",
    "SEAL": f"{SEAL:.1f}", "SEAL_Y": f"{SEAL_Y:.1f}", "SEAL_D": f"{SEAL - SEAL_Y:+.1f}",
    "SEAL_D_ABS": f"{abs(SEAL - SEAL_Y):.1f}", "SEAL_DP": f"{SEAL - SEAL_Y:+.1f}",
    "ZB": str(ZB), "ZB_Y": str(ZB_Y), "ZB_EM": str(len(zb0)),
    "ZB_DIFF": str(len(zb0) - ZB),
    "DT": str(DT), "DT_Y": str(DT_Y), "DT_D": f"{DT - DT_Y:+d}",
    "DT_2": str(DT_2), "DTOUCH": str(DTOUCH), "DTOUCH_Y": str(DTOUCH_Y),
    "DTOUCH_2": str(DTOUCH_2),
    "DSEAL": f"{DSEAL:.1f}", "DSEAL_Y": f"{DSEAL_Y:.1f}", "DSEAL_2": f"{DSEAL_2:.1f}",
    "DT_OPEN_N": str(DT_OPEN_N),
    "TOUCH_GAP": str(TOUCH - ZT),
    "SEAL_FAIL": f"{(TOUCH - ZT) / TOUCH * 100:.1f}",
    "SEAL_FAIL_Y": f"{(TOUCH_Y - ZT_Y) / TOUCH_Y * 100:.1f}",
    "LB": str(LB), "LB_Y": str(LB_Y), "LB_D": f"{LB - LB_Y:+d}",
    "LB_PCT": f"{LB / ZT * 100:.1f}", "LB_PCT_Y": f"{LB_Y / ZT_Y * 100:.1f}",
    "LB_PCT_D": f"{LB / ZT * 100 - LB_Y / ZT_Y * 100:+.1f}",
    "SHOU": str(SHOU), "SHOU_Y": str(SHOU_Y),
    "SHOU_PCT": f"{SHOU / ZT * 100:.1f}", "SHOU_PCT_Y": f"{SHOU_Y / ZT_Y * 100:.1f}",
    "SHOU_UP_PCT": f"{(SHOU / SHOU_Y - 1) * 100:.0f}",
    "MAXB": str(MAXB), "MAXB_Y": str(MAXB_Y),
})

# ---------------- 梯队 ----------------
LAD_ROWS = []
LADMAX = max(max(lad0), max(lad1))
for b in range(1, LADMAX + 1):
    a, y = lad0.get(b, 0), lad1.get(b, 0)
    dd = a - y
    LAD_ROWS.append('<tr><td>%d 板</td><td class="hl">%d</td><td>%d</td><td class="%s">%+d</td></tr>'
                    % (b, a, y, ("up" if dd > 0 else ("down" if dd < 0 else "mut")), dd))
V["TBL_LAD"] = "\n".join(LAD_ROWS)
LAD3P = sum(v for k, v in lad0.items() if k >= 3)
LAD3P_Y = sum(v for k, v in lad1.items() if k >= 3)
V.update({"LAD3P": str(LAD3P), "LAD3P_Y": str(LAD3P_Y),
          "LAD2": str(lad0.get(2, 0)), "LAD2_Y": str(lad1.get(2, 0)),
          "LAD3": str(lad0.get(3, 0)), "LAD3_Y": str(lad1.get(3, 0)),
          "LAD4": str(lad0.get(4, 0)), "LAD4_Y": str(lad1.get(4, 0)),
          "LAD5": str(lad0.get(5, 0)), "LAD5_Y": str(lad1.get(5, 0)),
          "LAD6": str(lad0.get(6, 0)), "LAD6_Y": str(lad1.get(6, 0)),
          "LAD7": str(lad0.get(7, 0))})
V["LAD_VAC"] = "、".join("%d 板" % b for b in range(4, MAXB) if lad0.get(b, 0) == 0) or "无"

# ---------------- 指数 ----------------
NAME = {"sh000001": "上证指数", "sz399001": "深证成指", "sz399006": "创业板指", "sh000688": "科创50",
        "bj899050": "北证50", "sh000300": "沪深300", "sh000852": "中证1000", "sh000905": "中证500",
        "sz399303": "国证2000", "sh000016": "上证50", "sz399005": "中小100"}
idx0, idx1 = B["indexes"], B1["indexes"]
rows_idx, yoy = [], {}
n_up = n_dn = n_amt_up = n_amt_dn = 0
intra = {"labels": [], "gap": [], "low": [], "high": [], "close": []}
n_above_open = n_gap_up = 0
INTRA_CODES = ["sh000001", "sz399001", "sz399006", "sh000688", "sh000300", "sz399303", "sh000016"]
for k, nm in NAME.items():
    a, b = idx0.get(k) or {}, idx1.get(k) or {}
    if not a:
        continue
    p0v, p1v = a.get("pct") or 0, b.get("pct") or 0
    m0, m1 = a.get("amount_wan") or 0, b.get("amount_wan") or 0
    chg = (m0 / m1 - 1) * 100 if m1 else 0
    yoy[nm] = chg
    n_up += p0v > 0
    n_dn += p0v < 0
    n_amt_up += chg > 0
    n_amt_dn += chg <= 0
    rows_idx.append('<tr><td>%s</td><td class="%s">%+.2f%%</td><td class="%s">%+.2f%%</td><td>%s</td><td class="%s">%+.1f%%</td></tr>'
                    % (nm, "up" if p0v > 0 else ("down" if p0v < 0 else "mut"), p0v,
                       "up" if p1v > 0 else ("down" if p1v < 0 else "mut"), p1v,
                       f"{m0 / 1e4:,.0f}", "up" if chg > 0 else "down", chg))
    if k in INTRA_CODES:
        prev = a.get("prev") or 0
        if prev:
            gap = (a["open"] / prev - 1) * 100
            intra["labels"].append(nm)
            intra["gap"].append(round(gap, 2))
            intra["low"].append(round((a["low"] / prev - 1) * 100, 2))
            intra["high"].append(round((a["high"] / prev - 1) * 100, 2))
            intra["close"].append(round((a["price"] / prev - 1) * 100, 2))
            n_above_open += int(a["price"] > a["open"])
            n_gap_up += int(gap > 0)
V["TBL_IDX"] = "\n".join(rows_idx)
V.update({
    "N_UP": str(n_up), "N_DN": str(n_dn),
    "AMT_UP_N": str(n_amt_up), "AMT_DN_N": str(n_amt_dn),
    "YOY_MAX": f"{min(yoy.values()):+.1f}%", "YOY_MAX_NAME": min(yoy, key=lambda k: yoy[k]),
    "YOY_MIN": f"{max(yoy.values()):+.1f}%", "YOY_MIN_NAME": max(yoy, key=lambda k: yoy[k]),
    "HS300_YOY": f"{yoy['沪深300']:+.1f}", "ZXX_YOY": f"{yoy['中小100']:+.1f}",
    "SH50_YOY": f"{yoy['上证50']:+.1f}", "KC_YOY": f"{yoy['科创50']:+.1f}",
    "CY_YOY": f"{yoy['创业板指']:+.1f}", "GZ_YOY": f"{yoy['国证2000']:+.1f}",
    "SH_YOY": f"{yoy['上证指数']:+.1f}", "SZ_YOY": f"{yoy['深证成指']:+.1f}",
    "ZZ_YOY": f"{yoy['中证1000']:+.1f}",
    "N_INTRA": str(len(intra["labels"])), "N_ABOVE_OPEN": str(n_above_open), "N_GAP_UP": str(n_gap_up),
    "N_FADE": str(len(intra["labels"]) - n_above_open),
})


def gi(code, field):
    a = idx0.get(code) or {}
    prev = a.get("prev") or 0
    return f"{((a.get(field) or 0) / prev - 1) * 100:+.2f}" if prev else "0.00"


def gp(code):
    return f"{(idx0.get(code) or {}).get('pct', 0):+.2f}"


def fade(code):
    a = idx0.get(code) or {}
    prev = a.get("prev") or 0
    if not prev:
        return "0.00"
    return f"{(a['open'] / prev - 1) * 100 - (a.get('pct') or 0):.2f}"


sh = idx0["sh000001"]
PREV_SH = sh["prev"]
OPEN_SH = sh["open"]
HIGH_SH = sh.get("high") or 0
_idx2 = B2["indexes"]
GAP_TOP = (_idx2.get("sh000001") or {}).get("prev") or 0
GAP_BOT = (_idx2.get("sh000001") or {}).get("open") or 0
GAP_SIZE = GAP_TOP - GAP_BOT
GAP_FILL = (HIGH_SH - GAP_BOT) / GAP_SIZE * 100
GAP_LEFT = (GAP_TOP - HIGH_SH) / GAP_SIZE * 100
V.update({
    "SH_GAP": gi("sh000001", "open"), "SH_HIGH": gi("sh000001", "high"),
    "SH_LOW": gi("sh000001", "low"), "SH_PCT": gp("sh000001"),
    "CY_GAP": gi("sz399006", "open"), "CY_GAP_ABS": f"{abs(float(gi('sz399006', 'open'))):.2f}",
    "CY_PCT": gp("sz399006"), "CY_LOW": gi("sz399006", "low"), "CY_HIGH": gi("sz399006", "high"),
    "CY_FADE": fade("sz399006"),
    "KC_GAP": gi("sh000688", "open"), "KC_GAP_ABS": f"{abs(float(gi('sh000688', 'open'))):.2f}",
    "KC_HIGH": gi("sh000688", "high"), "KC_PCT": gp("sh000688"), "KC_FADE": fade("sh000688"),
    "GZ_GAP": gi("sz399303", "open"), "GZ_GAP_ABS": f"{abs(float(gi('sz399303', 'open'))):.2f}",
    "GZ_PCT": gp("sz399303"), "GZ_FADE": fade("sz399303"),
    "SH50_GAP": gi("sh000016", "open"), "SH50_PCT": gp("sh000016"),
    "SH50_FADE": fade("sh000016"),
    "SH_CLOSE": f"{sh['price']:.2f}", "SH_HIGH_PT": f"{HIGH_SH:.2f}", "SH_PREV": f"{PREV_SH:.2f}",
    "GAP_FILL": f"{GAP_FILL:.0f}", "GAP_LEFT": f"{max(GAP_LEFT, 0):.1f}",
})

# ---------------- 两市与涨停股成交 ----------------
TOT = S["tot"]["today"]
TOT_Y = S["tot"]["prev"]


def amt_of(pool, universe):
    return sum(x.get("amount", 0) for c, x in pool.items() if c in universe) / 1e8


AMT_SUM = amt_of(p0, ths0)
AMT_SUM_Y = amt_of(p1, ths1)
V.update({
    "AMT": f"{TOT:,.0f}", "AMT_Y": f"{TOT_Y:,.0f}", "AMT_D": f"{TOT - TOT_Y:+,.0f}",
    "AMT_PCT": f"{(TOT / TOT_Y - 1) * 100:+.1f}",
    "AMT_SUM": f"{AMT_SUM:.1f}", "AMT_SUM_Y": f"{AMT_SUM_Y:.1f}",
    "AMT_SUM_PCT": f"{(AMT_SUM / AMT_SUM_Y - 1) * 100:+.1f}",
    "SHARE": f"{AMT_SUM / TOT * 100:.2f}", "SHARE_Y": f"{AMT_SUM_Y / TOT_Y * 100:.2f}",
})

fund0 = [p0[c].get("fund", 0) / 1e8 for c in ths0]
fund1 = [p1[c].get("fund", 0) / 1e8 for c in ths1]
amts0 = [p0[c].get("amount", 0) / 1e8 for c in ths0]
amts1 = [p1[c].get("amount", 0) / 1e8 for c in ths1]
mvs0 = [p0[c].get("ltsz", 0) / 1e8 for c in ths0]
mvs1 = [p1[c].get("ltsz", 0) / 1e8 for c in ths1]
V.update({
    "FUND": f"{sum(fund0):.1f}", "FUND_Y": f"{sum(fund1):.1f}",
    "FUND_PCT": f"{(sum(fund0) / sum(fund1) - 1) * 100:+.1f}",
    "FUND_MED": f"{median(fund0):.2f}", "FUND_MED_Y": f"{median(fund1):.2f}",
    "MED_AMT": f"{median(amts0):.2f}", "MED_AMT_Y": f"{median(amts1):.2f}",
    "MED_AMT_PCT": f"{(median(amts0) / median(amts1) - 1) * 100:+.1f}",
    "ZT_MED_MV": f"{median(mvs0):.0f}", "ZT_MED_MV_Y": f"{median(mvs1):.0f}",
})
YIZI = sum(1 for x in ths0.values() if "一字" in (x.get("limit_up_type") or ""))
TZI = sum(1 for x in ths0.values() if "T字" in (x.get("limit_up_type") or ""))
V["YIZI"], V["TZI"] = str(YIZI), str(TZI)
TURN_SB = median([p0[c].get("hs") or 0 for c in ths0 if (p0[c].get("lbc") or 1) == 1])
TURN_LB = median([p0[c].get("hs") or 0 for c in ths0 if (p0[c].get("lbc") or 1) > 1])
V["TURN_SB"], V["TURN_LB"] = f"{TURN_SB:.2f}", f"{TURN_LB:.2f}"
AMT_SB = median([p0[c].get("amount", 0) / 1e8 for c in ths0 if (p0[c].get("lbc") or 1) == 1])
AMT_LB = median([p0[c].get("amount", 0) / 1e8 for c in ths0 if (p0[c].get("lbc") or 1) > 1])
V["AMT_SB"], V["AMT_LB"] = f"{AMT_SB:.2f}", f"{AMT_LB:.2f}"

# 市值结构（腾讯快照）
band = {"<50亿": 0, "50-100亿": 0, "100-300亿": 0, ">300亿": 0}
for c in ths0:
    q = MV.get(c)
    mv = (q or {}).get("float_mv") or 0
    if not mv:
        continue
    k = "<50亿" if mv < 50 else ("50-100亿" if mv < 100 else ("100-300亿" if mv < 300 else ">300亿"))
    band[k] += 1
SMALL = band["<50亿"] + band["50-100亿"]
V.update({"MV_SMALL": str(SMALL), "MV_SMALL_PCT": f"{SMALL / ZT * 100:.1f}",
          "MV_B1": str(band["<50亿"]), "MV_B2": str(band["50-100亿"]),
          "MV_B3": str(band["100-300亿"]), "MV_B4": str(band[">300亿"]),
          "MV_B1_PCT": f"{band['<50亿'] / ZT * 100:.1f}"})
_big = sorted(((MV[c]["float_mv"], ths0[c]["name"]) for c in ths0 if c in MV), reverse=True)[:3]
V["MV_TOP_TXT"] = "、".join("%s %.0f 亿" % (n, m) for m, n in _big)

# ---------------- 炸板 ----------------
ZB_AMT = sum(x.get("amount", 0) for x in zb0) / 1e8
ZB_AMT_Y = sum(x.get("amount", 0) for x in zb1) / 1e8
ZB_SEALED = [x for x in zb0 if x.get("p", 0) >= x.get("ztp", 0)]
ZB_SEALED_Y = [x for x in zb1 if x.get("p", 0) >= x.get("ztp", 0)]
zb_top = sorted(zb0, key=lambda y: -y.get("amount", 0))[:5]
V.update({
    "ZB_SEALED_N": str(len(ZB_SEALED)),
    "ZB_SEALED_Y": str(len(ZB_SEALED_Y)),
    "ZB_SEAL_PCT": f"{len(ZB_SEALED) / max(len(zb0), 1) * 100:.0f}",
    "ZB_AMT": f"{ZB_AMT:.1f}", "ZB_AMT_Y": f"{ZB_AMT_Y:.1f}",
    "ZB_AMT_PCT": f"{(ZB_AMT / ZB_AMT_Y - 1) * 100:+.1f}",
    "ZB_RATIO": f"{ZB_AMT / AMT_SUM:.2f}", "ZB_RATIO_Y": f"{ZB_AMT_Y / AMT_SUM_Y:.2f}",
    "ZB_TOP5_TXT": "、".join("%s（%s，%s 亿，收 %+.2f%%）" % (x["n"], x.get("hybk") or "—",
                                                       f"{x.get('amount', 0) / 1e8:.2f}", x.get("zdp") or 0) for x in zb_top),
    "ZBT_BIG_N": str(sum(1 for x in zb0 if x.get("ltsz", 0) / 1e8 > 100)),
    "ZT_BIG_N": str(sum(1 for x in p0.values() if x.get("ltsz", 0) / 1e8 > 100)),
    "ZB_MED_MV": f"{median([x.get('ltsz', 0) / 1e8 for x in zb0]):.0f}",
    "ZB_TOP1_AMT": f"{zb_top[0].get('amount', 0) / 1e8:.2f}",
})
zbt = max(zb0, key=lambda y: y.get("ltsz", 0))
zba = max(zb0, key=lambda y: y.get("amount", 0))
V.update({"ZBT_MV": f"{zbt.get('ltsz', 0) / 1e8:.0f}", "ZBT_AMT": f"{zbt.get('amount', 0) / 1e8:.2f}",
          "ZBT_PCT": f"{zbt.get('zdp', 0):+.2f}", "ZBT_NAME": zbt["n"], "ZBT_HY": zbt.get("hybk") or "—",
          "ZBA_MV": f"{zba.get('ltsz', 0) / 1e8:.0f}", "ZBA_AMT": f"{zba.get('amount', 0) / 1e8:.2f}",
          "ZBA_PCT": f"{zba.get('zdp', 0):+.2f}", "ZBA_NAME": zba["n"], "ZBA_HY": zba.get("hybk") or "—"})
hy_zb = Counter(x.get("hybk") or "(空)" for x in zb0)
V["ZB_HY_TOP"] = "、".join("%s %d 只" % (k, v) for k, v in sorted(hy_zb.items(), key=lambda kv: (-kv[1], kv[0]))[:4])
# 炸板池午后打开计数
def slot_hhmm(f):
    s = str(f).zfill(6)
    return int(s[:2]) * 60 + int(s[2:4])


ZB_AFTERNOON = sum(1 for x in zb0 if x.get("fbt") and slot_hhmm(x["fbt"]) >= 13 * 60)
V["ZB_AFTERNOON"] = str(ZB_AFTERNOON)
V["ZB_MORNING"] = str(len(zb0) - ZB_AFTERNOON)

# ---------------- 跌停 ----------------
DT_AMT = sum(x.get("amount", 0) for x in dt0) / 1e8
DT_AMT_Y = sum(x.get("amount", 0) for x in dt1) / 1e8
V.update({
    "DT_EM": str(A0["em_DT"].get("tc") if A0["em_DT"].get("tc") is not None else len(dt0)),
    "DT_POOL": str(len(dt0)),
    "DT_AMT": f"{DT_AMT:.2f}", "DT_AMT_Y": f"{DT_AMT_Y:.2f}",
    "DT_RATIO": f"{DT_AMT / AMT_SUM:.3f}",
    "DT_RATIO_Y": f"{DT_AMT_Y / AMT_SUM_Y:.3f}",
})

# ---------------- 昨日涨停股今日表现 ----------------
q = B["yesterday_zt_today"]
perf = []
for c in ths1:
    v = q.get(sym_of(c))
    if not v:
        continue
    perf.append({"code": c, "name": ths1[c]["name"], "lbc": p1[c].get("lbc") or 1,
                 "hy": p1[c].get("hybk") or "",
                 "reason": ths1[c].get("reason_type") or "",
                 "pct": v["pct"], "again": c in p0})
assert len(perf) == len(ths1), f"昨日样本缺失 {len(perf)}/{len(ths1)}"
P = [r["pct"] for r in perf]
AGAIN = [r for r in perf if r["again"]]
G_SB = [r for r in perf if r["lbc"] == 1]
G_LB = [r for r in perf if r["lbc"] > 1]
P_SB = [r["pct"] for r in G_SB]
P_LB = [r["pct"] for r in G_LB]
GAP = median(P_SB) - median(P_LB)
_p1g = [r for r in S1["perf"]]
_sb1 = [r["pct"] for r in _p1g if (r.get("lbc") or 1) == 1]
_lb1 = [r["pct"] for r in _p1g if (r.get("lbc") or 1) > 1]
GAP_Y = median(_sb1) - median(_lb1)
V.update({
    "ADV_TOT": str(len(perf)), "ADV_N": str(len(AGAIN)),
    "ADV_RATE": f"{len(AGAIN) / len(perf) * 100:.1f}",
    "ADV_RATE_Y": "28.1",
    "PERF_MEAN": f"{mean(P):+.2f}", "PERF_MED": f"{median(P):+.2f}",
    "PERF_MAX": f"{max(P):+.2f}", "PERF_MIN": f"{min(P):+.2f}",
    "PERF_DN_N": str(sum(1 for p in P if p < 0)),
    "PERF_DN_PCT": f"{sum(1 for p in P if p < 0) / len(P) * 100:.1f}",
    "PERF_DN5_N": str(sum(1 for p in P if p < -5)),
    "GAP": f"{GAP:+.2f}", "GAP_Y": f"{GAP_Y:+.2f}", "GAP_SWING": f"{abs(GAP - GAP_Y):.2f}",
    "SB_MED": f"{median(P_SB):+.2f}", "LB_MED": f"{median(P_LB):+.2f}",
    "LB_ADV": str(sum(1 for r in G_LB if r["again"])),
    "LB_ADV_PCT": f"{sum(1 for r in G_LB if r['again']) / len(G_LB) * 100:.1f}",
    "LB_DN_N": str(sum(1 for r in G_LB if r["pct"] < 0)),
    "SHOU_ADV": str(sum(1 for r in G_SB if r["again"])),
    "SHOU_ADV_PCT": f"{sum(1 for r in G_SB if r['again']) / len(G_SB) * 100:.1f}",
    "SB_MEAN": f"{mean(P_SB):+.2f}", "LB_MEAN": f"{mean(P_LB):+.2f}",
})
PROWS = []
for k, g in (("昨日首板", G_SB), ("昨日连板", G_LB)):
    gpx = [x["pct"] for x in g]
    ga = sum(1 for x in g if x["again"])
    PROWS.append('<tr><td>%s</td><td>%d</td><td class="hl">%.1f%%</td><td>%+.2f%%</td><td class="%s">%+.2f%%</td><td>%d 只</td></tr>'
                 % (k, len(g), ga / len(g) * 100, mean(gpx),
                    "up" if median(gpx) >= 0 else "down", median(gpx), sum(1 for p in gpx if p < 0)))
V["TBL_PERF"] = "\n".join(PROWS)
top5 = sorted(perf, key=lambda r: -r["pct"])[:5]
bot5 = sorted(perf, key=lambda r: r["pct"])[:5]
V["PERF_TOP_TXT"] = "；".join("%s %+.2f%%（昨 %d 板）" % (r["name"], r["pct"], r["lbc"]) for r in top5)
V["PERF_BOT_TXT"] = "；".join("%s %+.2f%%（昨 %d 板）" % (r["name"], r["pct"], r["lbc"]) for r in bot5)
pmap_pct = {r["code"]: r["pct"] for r in perf}
_lbadv = [r for r in G_LB if r["again"]]
V["LB_ADV_TXT"] = "、".join("%s（%d→%d 板）" % (r["name"], r["lbc"], r["lbc"] + 1) for r in _lbadv) or "无"
V["LB_ADV_DF"] = str(sum(1 for r in _lbadv if "东方" in r["name"]))
V["BOT_NAMES"] = "、".join("%s %+.2f%%" % (r["name"], r["pct"]) for r in bot5)
dt_codes = {x["c"] for x in dt0}
ZT2DT = [r for r in perf if r["code"] in dt_codes]
V["ZT2DT_N"] = str(len(ZT2DT))
V["ZT2DT_TXT"] = "、".join("%s（昨 %d 板，%+.2f%%）" % (r["name"], r["lbc"], r["pct"]) for r in ZT2DT) or "无"

# 昨连板组未晋级名单
LB_FAIL = [r for r in G_LB if not r["again"]]
V["LB_FAIL_N"] = str(len(LB_FAIL))
V["LB_FAIL_TXT"] = "、".join("%s %+.2f%%（昨 %d 板）" % (r["name"], r["pct"], r["lbc"]) for r in
                            sorted(LB_FAIL, key=lambda r: r["pct"]))

# 昨跌停池今日表现
PDT = []
for x in dt1:
    v = QDT1.get(x["c"])
    if v:
        PDT.append({"c": x["c"], "n": x["n"], "pct": v["pct"]})
PV = [r["pct"] for r in PDT]
V.update({
    "PDT_N": str(len(PDT)),
    "PDT_MEAN": f"{mean(PV):+.2f}" if PV else "—",
    "PDT_TXT": "、".join("%s %+.2f%%" % (r["n"], r["pct"]) for r in PDT) or "无",
})

# ---------------- 题材簇 ----------------
CL = [
    ("机器人/具身智能", ["机器人", "具身", "人形", "减速器", "电子皮肤", "六维力", "关节", "无框电机", "触觉", "灵巧手", "机器狗"]),
    ("半导体/电子硬件", ["半导体", "芯片", "HBM", "存储", "PCB", "覆铜板", "印制电路板", "光通信", "CPO",
                        "硅基OLED", "偏光片", "端侧AI", "AI眼镜", "消费电子", "声学", "视觉芯片"]),
    ("传媒/AI应用", ["AI漫剧", "短剧", "游戏", "AIGC", "AI影视", "AI应用", "AI营销", "院线", "影视",
                     "数字阅读", "互动影游", "VR"]),
    ("商业航天/卫星", ["商业航天", "卫星", "星载", "太空", "航天"]),
    ("光伏/储能", ["光伏", "储能", "钙钛矿", "逆变器"]),
]


def clus(rules, thsmap, pmap):
    out = {}
    for nm, kws in rules:
        sel = [c for c, x in thsmap.items() if any(w in (x.get("reason_type") or "") for w in kws)]
        amt = sum((pmap.get(c) or {}).get("amount", 0) for c in sel) / 1e8
        lb = sum(1 for c in sel if (pmap.get(c) or {}).get("lbc", 1) > 1)
        out[nm] = (len(sel), lb, amt, sel)
    return out


C0 = clus(CL, ths0, p0)
C1 = clus(CL, ths1, p1)
# AI 大方向并集（机器人 ∪ 电子硬件 ∪ 传媒应用）
AI_SET = set(C0["机器人/具身智能"][3]) | set(C0["半导体/电子硬件"][3]) | set(C0["传媒/AI应用"][3])
AI_SET1 = set(C1["机器人/具身智能"][3]) | set(C1["半导体/电子硬件"][3]) | set(C1["传媒/AI应用"][3])
AI_AMT = sum(p0[c].get("amount", 0) for c in AI_SET) / 1e8
AI_LB = sum(1 for c in AI_SET if (p0[c].get("lbc") or 1) > 1)
DF = [c for c, x in ths0.items() if "东方" in x["name"]]
YANG = [c for c, x in ths0.items() if "字辈" in (x.get("reason_type") or "") and "羊" in (x.get("reason_type") or "")]
NM = sorted(set(DF) | set(YANG))
NM_AMT = sum(p0[c].get("amount", 0) for c in NM) / 1e8
NM_HY = len({(p0[c].get("hybk") or "(空)") for c in NM})
DF1 = {x["code"] for x in A1["ths_zt"]["info"] if "东方" in x["name"]}
YANG1 = {x["code"] for x in A1["ths_zt"]["info"] if "字辈" in (x.get("reason_type") or "") and "羊" in (x.get("reason_type") or "")}
NM1 = DF1 | YANG1
NM_AMT1 = sum(p1[c].get("amount", 0) for c in NM1 if c in p1) / 1e8


def lst(codes):
    return "、".join("%s（%s，%d 板）" % (p0[c]["n"], p0[c].get("hybk") or "—", p0[c].get("lbc", 1))
                    for c in sorted(codes, key=lambda c: (-p0[c].get("lbc", 1), -p0[c].get("amount", 0))))


ROB = C0["机器人/具身智能"]
SEMI = C0["半导体/电子硬件"]
MEDIA = C0["传媒/AI应用"]
SPACE = C0["商业航天/卫星"]
PV = C0["光伏/储能"]
V.update({
    "AI_N": str(len(AI_SET)), "AI_AMT": f"{AI_AMT:.1f}",
    "AI_SHARE": f"{AI_AMT / AMT_SUM * 100:.1f}", "AI_LB": str(AI_LB),
    "AI_PCT": f"{len(AI_SET) / ZT * 100:.1f}",
    "ROB_N": str(ROB[0]), "ROB_LB": str(ROB[1]), "ROB_AMT": f"{ROB[2]:.1f}",
    "ROB_SHARE": f"{ROB[2] / AMT_SUM * 100:.1f}", "ROB_PCT": f"{ROB[0] / ZT * 100:.1f}",
    "ROB_SHARE_Y": f"{C1['机器人/具身智能'][2] / AMT_SUM_Y * 100:.1f}",
    "ROB_N_Y": str(C1["机器人/具身智能"][0]), "ROB_LB_Y": str(C1["机器人/具身智能"][1]),
    "ROB_HY": str(len({p0[c].get("hybk") for c in ROB[3]})),
    "ROB_LB_TXT": "、".join("%s %d 板" % (p0[c]["n"], p0[c].get("lbc", 1))
                           for c in ROB[3] if p0[c].get("lbc", 1) > 1) or "无",
    "SEMI_N": str(SEMI[0]), "SEMI_LB": str(SEMI[1]), "SEMI_AMT": f"{SEMI[2]:.1f}",
    "SEMI_SHARE": f"{SEMI[2] / AMT_SUM * 100:.1f}", "SEMI_N_Y": str(C1["半导体/电子硬件"][0]),
    "SEMI_SHARE_Y": f"{C1['半导体/电子硬件'][2] / AMT_SUM_Y * 100:.1f}",
    "MEDIA_N": str(MEDIA[0]), "MEDIA_LB": str(MEDIA[1]), "MEDIA_AMT": f"{MEDIA[2]:.1f}",
    "MEDIA_SHARE": f"{MEDIA[2] / AMT_SUM * 100:.1f}", "MEDIA_N_Y": str(C1["传媒/AI应用"][0]),
    "MEDIA_SHARE_Y": f"{C1['传媒/AI应用'][2] / AMT_SUM_Y * 100:.1f}",
    "SPACE_N": str(SPACE[0]), "SPACE_LB": str(SPACE[1]), "SPACE_AMT": f"{SPACE[2]:.1f}",
    "SPACE_SHARE": f"{SPACE[2] / AMT_SUM * 100:.1f}", "SPACE_N_Y": str(C1["商业航天/卫星"][0]),
    "SPACE_LB_Y": str(C1["商业航天/卫星"][1]),
    "SPACE_SHARE_Y": f"{C1['商业航天/卫星'][2] / AMT_SUM_Y * 100:.1f}",
    "PV_N": str(PV[0]), "PV_LB": str(PV[1]), "PV_SHARE": f"{PV[2] / AMT_SUM * 100:.1f}",
    "PV_N_Y": str(C1["光伏/储能"][0]), "PV_LB_Y": str(C1["光伏/储能"][1]),
    "DF_N": str(len(DF)), "YANG_N": str(len(YANG)), "NM_N": str(len(NM)),
    "NM_AMT": f"{NM_AMT:.1f}", "NM_SHARE": f"{NM_AMT / AMT_SUM * 100:.1f}", "NM_HY": str(NM_HY),
    "NM_N_Y": str(len(NM1)), "NM_AMT_Y": f"{NM_AMT1:.1f}",
    "NM_SHARE_Y": f"{NM_AMT1 / AMT_SUM_Y * 100:.1f}",
    "NM_SURVIVE": str(len([c for c in NM1 if c in p0])),
    "DF_LIST": lst(DF), "YANG_LIST": lst(YANG) if YANG else "无",
})
V["ZBY_LB"] = str(sum(1 for c in YANG if (p0[c].get("lbc") or 1) > 1))
# 昨日机器人链（同口径）今日晋级只数
_rob1 = set(C1["机器人/具身智能"][3])
V["ROB_ADV_N"] = str(len([c for c in _rob1 if c in p0]))
V["ROB_ADV_PCT"] = f"{len([c for c in _rob1 if c in p0]) / max(len(_rob1), 1) * 100:.1f}"
V["ROB_ADV_TXT"] = "、".join(p0[c]["n"] for c in _rob1 if c in p0) or "无"

MROWS = []
for nm, _ in CL:
    a, b = C0[nm], C1[nm]
    dd = a[0] - b[0]
    MROWS.append('<tr><td>%s</td><td>%d</td><td class="%s">%d</td><td>%d</td><td>%s</td><td>%s%%</td></tr>'
                 % (nm, b[0], "up" if dd > 0 else ("down" if dd < 0 else "mut"), a[0], a[1],
                    f"{a[2]:.1f}", f"{a[2] / AMT_SUM * 100:.1f}"))
MROWS.append('<tr><td><b>【合计】AI 三链并集</b></td><td>—</td><td class="hl">%d</td><td>%d</td><td>%s</td><td>%s%%</td></tr>'
             % (len(AI_SET), AI_LB, f"{AI_AMT:.1f}", f"{AI_AMT / AMT_SUM * 100:.1f}"))
MROWS.append('<tr><td><b>【名称】「东方」系</b></td><td>—</td><td class="hl">%d</td><td>%d</td><td>%s</td><td>%s%%</td></tr>'
             % (len(DF), sum(1 for c in DF if p0[c].get("lbc", 1) > 1),
                f"{sum(p0[c].get('amount', 0) for c in DF) / 1e8:.1f}",
                f"{sum(p0[c].get('amount', 0) for c in DF) / 1e8 / AMT_SUM * 100:.1f}"))
MROWS.append('<tr><td><b>【名称】「羊」字辈</b></td><td>—</td><td class="hl">%d</td><td>%d</td><td>%s</td><td>%s%%</td></tr>'
             % (len(YANG), sum(1 for c in YANG if p0[c].get("lbc", 1) > 1),
                f"{sum(p0[c].get('amount', 0) for c in YANG) / 1e8:.1f}",
                f"{sum(p0[c].get('amount', 0) for c in YANG) / 1e8 / AMT_SUM * 100:.1f}"))
V["TBL_MAIN"] = "\n".join(MROWS)

# 概念榜
BLK = {b["name"]: b for b in (A0["ths_block"] or [])}
BLK1 = {b["name"]: b for b in (A1["ths_block"] or [])}


def br(nm, M=None):
    b = (M or BLK).get(nm)
    return f"{b['continuous_plate_num'] / b['limit_up_num'] * 100:.1f}" if b and b.get("limit_up_num") else "0.0"


TOP7 = sorted([b for b in (A0["ths_block"] or []) if b.get("limit_up_num")],
              key=lambda x: -x["limit_up_num"])[:7]
TOP7_MAX = max(TOP7, key=lambda x: x["continuous_plate_num"] / x["limit_up_num"])
V.update({
    "TOP7_TXT": "、".join("%s %d 家/连板 %d" % (b["name"], b["limit_up_num"], b["continuous_plate_num"]) for b in TOP7),
    "TOP7_MAX_R": f"{TOP7_MAX['continuous_plate_num'] / TOP7_MAX['limit_up_num'] * 100:.1f}",
    "TOP7_MAX_NAME": TOP7_MAX["name"],
    "TOP7_ROB_N": str((BLK.get("机器人概念") or {}).get("limit_up_num", 0)),
    "TOP7_ROB_LB": str((BLK.get("机器人概念") or {}).get("continuous_plate_num", 0)),
    "ROB_CONC_N": str((BLK.get("机器人概念") or {}).get("limit_up_num", 0)),
    "ROB_CONC_LB": str((BLK.get("机器人概念") or {}).get("continuous_plate_num", 0)),
    "ROB_CONC_R": br("机器人概念"),
    "ROB_CONC_N_Y": str((BLK1.get("机器人概念") or {}).get("limit_up_num", 0)),
    "ROB_CONC_LB_Y": str((BLK1.get("机器人概念") or {}).get("continuous_plate_num", 0)),
    "ROB_CONC_R_Y": br("机器人概念", BLK1),
    "HR_CONC_N": str((BLK.get("人形机器人") or {}).get("limit_up_num", 0)),
    "HR_CONC_LB": str((BLK.get("人形机器人") or {}).get("continuous_plate_num", 0)),
    "HR_CONC_R": br("人形机器人"),
    "HR_CONC_N_Y": str((BLK1.get("人形机器人") or {}).get("limit_up_num", 0)),
    "HR_CONC_R_Y": br("人形机器人", BLK1),
    "CM_CONC_N": str((BLK.get("文化传媒概念") or {}).get("limit_up_num", 0)),
    "CM_CONC_R": br("文化传媒概念"),
    "CM_CONC_N_Y": str((BLK1.get("文化传媒概念") or {}).get("limit_up_num", 0)),
    "GLASS_CONC_N": str((BLK.get("AI眼镜") or {}).get("limit_up_num", 0)),
    "GLASS_CONC_R": br("AI眼镜"),
    "SPACE_CONC_N_Y": str((BLK1.get("商业航天") or {}).get("limit_up_num", 0)),
})

# 行业迁移
hy0 = Counter((p0[c].get("hybk") or "(空)") for c in ths0)
hy1 = Counter((p1[c].get("hybk") or "(空)") for c in ths1)
assert sum(hy0.values()) == len(ths0), "今日行业闭合失败"
assert sum(hy1.values()) == len(ths1), "昨日行业闭合失败"
zero = sorted([k for k in hy1 if hy0.get(k, 0) == 0], key=lambda k: (-hy1[k], k))
new = sorted([k for k in hy0 if hy1.get(k, 0) == 0], key=lambda k: (-hy0[k], k))
inflow = sorted([(k, hy0[k], hy1.get(k, 0)) for k in hy0 if hy0[k] > hy1.get(k, 0)],
                key=lambda t: (-(t[1] - t[2]), -t[1], t[0]))[:6]
outflow = sorted([(k, hy0.get(k, 0), hy1[k]) for k in hy1 if hy1[k] > hy0.get(k, 0)],
                 key=lambda t: (-(t[2] - t[1]), -t[2], t[0]))[:5]
V.update({
    "HY_N": str(len(hy0)), "HY_N_Y": str(len(hy1)),
    "HY_ZERO_N": str(len(zero)), "HY_NEW_N": str(len(new)),
    "HY_TXT": ("<b>流入端</b>：%s；<b>流出端</b>：%s。<b>清零 %d 个</b>（%s）；<b>新增 %d 个</b>（%s）。"
               % ("、".join("%s %d→%d（%+d）" % (k, b, a, a - b) for k, a, b in inflow),
                  "、".join("%s %d→%d（%+d）" % (k, b, a, a - b) for k, a, b in outflow),
                  len(zero), "、".join(zero) if zero else "无",
                  len(new), "、".join(new) if new else "无")),
})
HY_ROWS = []
allhy = sorted(set(hy0) | set(hy1),
               key=lambda k: (-((hy0.get(k, 0) + hy1.get(k, 0)) + abs(hy0.get(k, 0) - hy1.get(k, 0)) * 2), -hy0.get(k, 0), k))
for k in allhy[:18]:
    a, b = hy0.get(k, 0), hy1.get(k, 0)
    dd = a - b
    HY_ROWS.append('<tr><td>%s</td><td>%d</td><td>%d</td><td class="%s">%+d</td></tr>'
                   % (k, a, b, "up" if dd > 0 else ("down" if dd < 0 else "mut"), dd))
V["TBL_HY"] = "\n".join(HY_ROWS)

# ---------------- 封板时间 ----------------
CATS = ["竞价/秒板", "开盘半小时", "上午盘中", "午后盘中", "尾盘"]


def slot(fbt):
    f = str(fbt).zfill(6)
    hh, mm = int(f[:2]), int(f[2:4])
    if hh * 60 + mm <= 9 * 60 + 25:
        return "竞价/秒板"
    if hh * 60 + mm <= 10 * 60:
        return "开盘半小时"
    if hh * 60 + mm <= 11 * 60 + 30:
        return "上午盘中"
    if hh * 60 + mm <= 14 * 60 + 30:
        return "午后盘中"
    return "尾盘"


ts0 = Counter(slot(p0[c].get("fbt")) for c in ths0)
ts1 = Counter(slot(p1[c].get("fbt")) for c in ths1)
V.update({
    "TS_JJ": str(ts0.get("竞价/秒板", 0)), "TS_JJ_Y": str(ts1.get("竞价/秒板", 0)),
    "TS_KP": str(ts0.get("开盘半小时", 0)), "TS_KP_Y": str(ts1.get("开盘半小时", 0)),
    "TS_SW": str(ts0.get("上午盘中", 0)), "TS_SW_Y": str(ts1.get("上午盘中", 0)),
    "TS_WH": str(ts0.get("午后盘中", 0)), "TS_WH_Y": str(ts1.get("午后盘中", 0)),
    "TS_WP": str(ts0.get("尾盘", 0)), "TS_WP_Y": str(ts1.get("尾盘", 0)),
})
EARLY = ts0.get("竞价/秒板", 0) + ts0.get("开盘半小时", 0) + ts0.get("上午盘中", 0)
EARLY_Y = ts1.get("竞价/秒板", 0) + ts1.get("开盘半小时", 0) + ts1.get("上午盘中", 0)
LATE = ts0.get("午后盘中", 0) + ts0.get("尾盘", 0)
LATE_Y = ts1.get("午后盘中", 0) + ts1.get("尾盘", 0)
V.update({"TS_EARLY": str(EARLY), "TS_EARLY_Y": str(EARLY_Y),
          "TS_EARLY_PCT": f"{EARLY / ZT * 100:.1f}", "TS_EARLY_PCT_Y": f"{EARLY_Y / ZT_Y * 100:.1f}",
          "TS_LATE": str(LATE), "TS_LATE_Y": str(LATE_Y)})
TSROWS = []
for k in CATS:
    a, b = ts0.get(k, 0), ts1.get(k, 0)
    TSROWS.append('<tr><td>%s</td><td class="hl">%d</td><td>%.1f%%</td><td>%d</td><td>%.1f%%</td></tr>'
                  % (k, a, a / ZT * 100, b, b / ZT_Y * 100))
V["TBL_TS"] = "\n".join(TSROWS)
V["TS_CONSIST_N"] = str(ZT)
V["TS_CONSIST"] = "100.0"

# ---------------- 高位股明细 ----------------
def fmt_stock(c, pm):
    x = pm[c]
    f = str(x.get("fbt")).zfill(6)
    return "%s（%d 板，%s，首封 %s:%s，封单 %.2f 亿，成交 %.2f 亿，换手 %.2f%%）" % (
        x["n"], x.get("lbc", 1), x.get("hybk") or "—", f[:2], f[2:4],
        x.get("fund", 0) / 1e8, x.get("amount", 0) / 1e8, x.get("hs", 0))


hmax = [c for c in p0 if p0[c].get("lbc") == MAXB]
h3 = [c for c in p0 if p0[c].get("lbc") == 3]
V["MAXB_DETAIL"] = "；".join(fmt_stock(c, p0) for c in hmax) or "—"
V["LAD3_DETAIL"] = "；".join(fmt_stock(c, p0) for c in h3) or "—"
mx = p0[hmax[0]]
mx1 = p1.get(hmax[0], {})
V.update({"MAXB_NAME": mx["n"], "MAXB_HY": mx.get("hybk") or "—",
          "MAXB_FUND": f"{mx.get('fund', 0) / 1e8:.2f}", "MAXB_AMT": f"{mx.get('amount', 0) / 1e8:.2f}",
          "MAXB_HS": f"{mx.get('hs', 0):.2f}", "MAXB_TYPE": ths0[hmax[0]].get("limit_up_type") or "—",
          "MAXB_HIGH_DAYS": ths0[hmax[0]].get("high_days") or "—",
          "MAXB_FBT": f"{str(mx.get('fbt')).zfill(6)[:2]}:{str(mx.get('fbt')).zfill(6)[2:4]}",
          "MAXB_FUND_Y": f"{mx1.get('fund', 0) / 1e8:.2f}",
          "MAXB_AMT_Y": f"{mx1.get('amount', 0) / 1e8:.2f}",
          "MAXB_HS_Y": f"{mx1.get('hs', 0):.2f}",
          "MAXB_FBT_Y": f"{str(mx1.get('fbt')).zfill(6)[:2]}:{str(mx1.get('fbt')).zfill(6)[2:4]}",
          "MAXB_TYPE_Y": (ths1.get(hmax[0]) or {}).get("limit_up_type") or "—"})
for tag, b in (("LAD2Y", 2), ("LAD3Y", 3), ("LAD4Y", 4), ("LAD6Y", 6)):
    cc = [c for c in p1 if p1[c].get("lbc") == b]
    V[tag + "_N"] = str(len(cc))
    V[tag + "_NAMES"] = "、".join(p1[c]["n"] for c in cc) or "—"
    V[tag + "_PCT"] = "、".join("%s %+.2f%%" % (p1[c]["n"], pmap_pct.get(c, 0)) for c in cc) or "—"
V["LAD2Y_ADV"] = str(sum(1 for c in p1 if p1[c].get("lbc") == 2 and c in p0))
V["LAD2Y_ADV_PCT"] = f"{sum(1 for c in p1 if p1[c].get('lbc') == 2 and c in p0) / max(lad1.get(2, 1), 1) * 100:.0f}"

LB_ROWS = []
for c in sorted([c for c in p0 if p0[c].get("lbc", 1) > 1], key=lambda c: (-p0[c].get("lbc", 1), -p0[c].get("amount", 0))):
    x = p0[c]
    f = str(x.get("fbt")).zfill(6)
    LB_ROWS.append('<tr><td>%s</td><td class="hl">%d</td><td>%s</td><td>%s:%s</td><td>%.2f</td><td>%.2f</td><td>%.2f%%</td><td class="note">%s</td></tr>'
                   % (x["n"], x.get("lbc", 1), x.get("hybk") or "—", f[:2], f[2:4],
                      x.get("fund", 0) / 1e8, x.get("amount", 0) / 1e8, x.get("hs", 0),
                      ths0[c].get("reason_type") or ""))
V["TBL_LIANBAN"] = "\n".join(LB_ROWS)

# ---------------- 三日情绪表 ----------------
SROWS = []


def row(lbl, a, b, c, fmt, inv=False, unit=""):
    def cl(dd):
        if abs(dd) < 1e-9:
            return "mut"
        pos = dd > 0
        if inv:
            pos = not pos
        return "up" if pos else "down"
    dd = a - b
    SROWS.append('<tr><td>%s</td><td>%s%s</td><td>%s%s</td><td class="hl">%s%s</td><td class="%s">%s</td></tr>'
                 % (lbl, fmt % c, unit, fmt % b, unit, fmt % a, unit, cl(dd),
                    (format(dd, "+.1f") if isinstance(dd, float) else f"{dd:+d}") + unit))


row("涨停家数", ZT, ZT_Y, ZT_2, "%d")
row("触及涨停家数", TOUCH, TOUCH_Y, TOUCH_2, "%d")
row("封板率", SEAL, SEAL_Y, SEAL_2, "%.1f", unit="%")
row("炸板家数", ZB, ZB_Y, ZB_2, "%d", inv=True)
row("跌停家数（封死）", DT, DT_Y, DT_2, "%d", inv=True)
row("触及跌停家数", DTOUCH, DTOUCH_Y, DTOUCH_2, "%d", inv=True)
row("跌停封死率", DSEAL, DSEAL_Y, DSEAL_2, "%.1f", inv=True, unit="%")
row("连板股", LB, LB_Y, LB_2, "%d")
row("最高连板", MAXB, MAXB_Y, MAXB_2, "%d")
SROWS.append('<tr><td>涨停 / 跌停比</td><td>%.1f</td><td>%.1f</td><td class="hl">—</td><td class="mut">跌停归零</td></tr>'
             % (ZT_2 / max(DT_2, 1), ZT_Y / max(DT_Y, 1)))
V["TBL_SENTI"] = "\n".join(SROWS)

# ---------------- 口径 ----------------
V.update({
    "D1POOL_ROWS": str(len(P1_FRESH)),
    "D1POOL_UNIQ": str(len({x["c"] for x in P1_FRESH})),
    "D1POOL_DAY": str(len(p1)), "D1POOL_THS": str(len(ths1)),
    "ZT_EM": str(A0["em_ZT"].get("tc") if A0["em_ZT"].get("tc") is not None else len(p0)),
})

# ---------------- SW ----------------
def swp(nm):
    v = (SW.get(nm) or {}).get("pct")
    return f"{v:+.2f}" if v is not None else "—"


V.update({
    "SW_YY_PCT": swp("元件"), "SW_TX_PCT": swp("通信设备"), "SW_XF_PCT": swp("消费电子"),
    "SW_SEMI_PCT": swp("半导体"), "SW_PCB_PCT": swp("PCB概念"), "SW_ROB_PCT": swp("人形机器人"),
    "SW_ROB2_PCT": swp("机器人概念"), "SW_YS_PCT": swp("影视院线"), "SW_GLASS_PCT": swp("AI眼镜"),
    "SW_GAME_PCT": swp("游戏Ⅱ"), "SW_PV_PCT": swp("光伏设备"), "SW_AI_PCT": swp("人工智能"),
})

# 昨日跌停 1 只
V["PDT_NAME"] = PDT[0]["n"] if PDT else "—"
V["PDT_PCT"] = f"{PDT[0]['pct']:+.2f}" if PDT else "—"

# ---------------- JS ----------------
JS = {
    "senti": {"days": [f"{md(D2)[0]} 周{md(D2)[1]}", f"{md(D1)[0]} 周{md(D1)[1]}", f"{md(D0)[0]} 周{md(D0)[1]}"],
              "zt": [ZT_2, ZT_Y, ZT], "zb": [ZB_2, ZB_Y, ZB],
              "dt": [DT_2, DT_Y, DT], "seal": [round(SEAL_2, 1), round(SEAL_Y, 1), round(SEAL, 1)]},
    "amt": {"labels": [r[0] for r in sorted(yoy.items(), key=lambda z: z[1])],
            "vals": [round(r[1], 1) for r in sorted(yoy.items(), key=lambda z: z[1])]},
    "intra": dict(intra, range=[[intra["low"][i], intra["high"][i]] for i in range(len(intra["labels"]))]),
    "ztzb": {"days": [f"{md(D2)[0]}", f"{md(D1)[0]}", f"{md(D0)[0]}"],
             "zt": [round(SUM_2, 1), round(AMT_SUM_Y, 1), round(AMT_SUM, 1)],
             "zb": [round(ZB_AMT_2, 1), round(ZB_AMT_Y, 1), round(ZB_AMT, 1)]},
    "flow": {"days": [f"{md(D2)[0]}", f"{md(D1)[0]}", f"{md(D0)[0]}"],
             "tot": [round(S2["tot"]["today"]), round(TOT_Y), round(TOT)],
             "sum": [round(SUM_2, 1), round(AMT_SUM_Y, 1), round(AMT_SUM, 1)],
             "share": [round(SUM_2 / S2["tot"]["today"] * 100, 2), round(AMT_SUM_Y / TOT_Y * 100, 2), round(AMT_SUM / TOT * 100, 2)]},
    "lad": {"cats": [f"{b} 板" for b in range(1, LADMAX + 1)],
            "d0": [lad0.get(b, 0) for b in range(1, LADMAX + 1)],
            "d1": [lad1.get(b, 0) for b in range(1, LADMAX + 1)],
            "d0lab": f"{md(D0)[0]}", "d1lab": f"{md(D1)[0]}"},
    "main": {"labels": [f"{c[0]}（连板 {C0[c[0]][1]}）" for c in CL]
                      + [f"AI 三链并集（连板 {AI_LB}）", f"「东方」系（连板 {sum(1 for c in DF if p0[c].get('lbc', 1) > 1)}）"],
             "d1": [C1[c[0]][0] for c in CL] + [len(AI_SET1), 0],
             "d0": [C0[c[0]][0] for c in CL] + [len(AI_SET), len(DF)],
             "d0lab": f"{md(D0)[0]}", "d1lab": f"{md(D1)[0]}"},
    "ts": {"cats": CATS, "d0": [ts0.get(k, 0) for k in CATS], "d1": [ts1.get(k, 0) for k in CATS],
           "d0lab": f"{md(D0)[0]}", "d1lab": f"{md(D1)[0]}"},
    "mv": {"labels": ["<50亿", "50-100亿", "100-300亿", ">300亿"],
           "vals": [band["<50亿"], band["50-100亿"], band["100-300亿"], band[">300亿"]]},
}
BINS = [(-11, -9), (-9, -7), (-7, -5), (-5, -3), (-3, -1), (-1, 1), (1, 3), (3, 5), (5, 7), (7, 9), (9, 11)]


def binof(p):
    for lo, hi in BINS:
        if lo <= p < hi:
            return f"{lo}~{hi}%"
    return "9~11%"


bc = Counter(binof(r["pct"]) for r in perf)
JS["perf"] = {"bins": [f"{lo}~{hi}%" for lo, hi in BINS],
              "vals": [bc.get(f"{lo}~{hi}%", 0) for lo, hi in BINS],
              "colors": ["#12805c", "#12805c", "#12805c", "#12805c", "#12805c", "#9ca3af",
                         "#e8a598", "#e8836f", "#d93025", "#d93025", "#d93025"]}

# ---------------- 补充渲染变量 ----------------
V["ZT_ALL_MINUS"] = str(ZT - YIZI - TZI)
V["SPEED_RATIO"] = f"{(AMT_SUM / AMT_SUM_Y) / (TOT / TOT_Y):.1f}"
_rob2 = [c for c in ROB[3] if (p0[c].get("lbc") or 1) == 2]
V["ROB_LAD2"] = str(len(_rob2))
V["ROB_LAD2_TXT"] = "、".join(p0[c]["n"] for c in _rob2) or "无"
_roblb = [c for c in ROB[3] if (p0[c].get("lbc") or 1) > 1]
_mxr = [c for c in _roblb if (p0[c].get("lbc") or 1) >= 3]
V["ROB_LB_STRUCT"] = ("其中 <b>%d 只是 2 板</b>（%s）；超过 2 板的 %d 只是 %s，其驱动是「%s」而不是机器人叙事 —— "
                      "<b>所以机器人链的真实高度只到 2 板</b>") % (
    len(_roblb) - len(_mxr),
    "、".join(p0[c]["n"] for c in sorted(_roblb, key=lambda c: -(p0[c].get("amount") or 0))
              if (p0[c].get("lbc") or 1) == 2) or "无",
    len(_mxr),
    "、".join("%s（%d 板）" % (p0[c]["n"], p0[c].get("lbc") or 1) for c in _mxr) or "无",
    "；".join((ths0[c].get("reason_type") or "") for c in _mxr) or "—")
V["NM_SHARE_D"] = f"{NM_AMT1 / AMT_SUM_Y * 100 - NM_AMT / AMT_SUM * 100:.1f}"
V["NM_AMT_PCT"] = f"{(NM_AMT / NM_AMT1 - 1) * 100:+.1f}"
_dfs = [c for c in DF1 if c in p0]
V["DF_SURVIVE"] = str(len(_dfs))
V["DF_SURVIVE_PCT"] = f"{len(_dfs) / max(len(DF1), 1) * 100:.0f}"
V["DF_SURVIVE_LIST"] = "、".join("%s（%s，%d 板，成交 %.2f 亿）" % (
    p0[c]["n"], p0[c].get("hybk") or "—", p0[c].get("lbc") or 1, (p0[c].get("amount") or 0) / 1e8) for c in _dfs) or "无"
_top1 = max(p0.values(), key=lambda x: x.get("amount") or 0)
V["TOP1_AMT_NAME"] = _top1["n"]
V["TOP1_AMT"] = f"{(_top1.get('amount') or 0) / 1e8:.1f}"
V["HY_YS0"] = str(hy0.get("影视院线", 0)); V["HY_YS1"] = str(hy1.get("影视院线", 0))
V["HY_GG0"] = str(hy0.get("广告营销", 0)); V["HY_GG1"] = str(hy1.get("广告营销", 0))
V["HY_YX0"] = str(hy0.get("游戏Ⅱ", 0))
_zb_yy = [x["n"] for x in zb0 if (x.get("hybk") or "") == "元件"]
V["ZB_YY_TXT"] = "、".join(_zb_yy) or "无"
V["ZB_YY_N"] = str(len(_zb_yy))
V["DF_N_Y"] = str(len(DF1))
V["LAD3_DF"] = str(sum(1 for c in h3 if c in DF))
V["LAD3_OTHER"] = "、".join(p0[c]["n"] for c in h3 if c not in DF) or "无"
_pvlb = [c for c in PV[3] if (p0[c].get("lbc") or 1) > 1]
V["PV_LB_TXT"] = "、".join("%s %d 板" % (p0[c]["n"], p0[c].get("lbc") or 1) for c in sorted(_pvlb, key=lambda c: -(p0[c].get("lbc") or 1))) or "无"
V["TS_LATE_PCT"] = f"{LATE / ZT * 100:.1f}"
V["TS_LATE_PCT_Y"] = f"{LATE_Y / ZT_Y * 100:.1f}"
V["SW_YS_UD"] = (SW.get("影视院线") or {}).get("updown") or "—"
V["JS_ALL"] = json.dumps(JS, ensure_ascii=False)

# ---------------- 序列排名（全部现算） ----------------
import glob as _glob
_touch_series, _ratio_series, _tot_series, _seal_series = [], [], [], []
_seen = set()
for _f in sorted(_glob.glob(os.path.join(OUT, "zt_review_*.json"))):
    try:
        _R = json.load(open(_f, encoding="utf-8"))
    except Exception:
        continue
    _d = _R.get("D0")
    if not _d or _d in _seen or _d not in (_R.get("dates") or {}):
        continue
    _x = _R["dates"][_d]
    _t = (_x.get("ths_zt") or {}).get("total", {}).get("today") or {}
    if not _t:
        continue
    _seen.add(_d)
    _pool = (_x.get("em_ZT") or {}).get("pool") or []
    _thsc = {i["code"] for i in ((_x.get("ths_zt") or {}).get("info") or [])}
    _a = sum(i.get("amount", 0) for i in _pool if i["c"] in _thsc) / 1e8
    _zb = sum(i.get("amount", 0) for i in ((_x.get("em_ZB") or {}).get("pool") or [])) / 1e8
    _touch_series.append((_d, _t.get("history_num") or 0))
    if _a:
        _ratio_series.append((_d, _zb / _a))
    if _t.get("rate"):
        _seal_series.append((_d, _t["rate"] * 100))
_seen2 = set()
for _f in sorted(_glob.glob(os.path.join(OUT, "zt_stats_*.json"))):
    try:
        _S = json.load(open(_f, encoding="utf-8"))
    except Exception:
        continue
    _d = _S.get("D0")
    if not _d or _d in _seen2 or _d == D0:
        continue
    _seen2.add(_d)
    _tot_series.append((_d, _S["tot"]["today"]))
NTDAYS = len(_touch_series)
TOUCH_RANK = 1 + sum(1 for _, v in _touch_series if v > TOUCH)
_seal_series = [(_d, v) for _d, v in _seal_series if _d != D0]
SEAL_RANK = 1 + sum(1 for _, v in _seal_series if v > SEAL)
SEAL_TOP = "、".join("%s 的 %.1f%%" % (md(_d)[0], v) for _d, v in sorted(_seal_series, key=lambda kv: -kv[1])[:3])
_ratio_series = [(_d, v) for _d, v in _ratio_series if _d != D0]
ZB_R_RANK = 1 + sum(1 for _, v in _ratio_series if v > ZB_AMT / AMT_SUM)
ZB_R_LOW = 1 + sum(1 for _, v in _ratio_series if v < ZB_AMT / AMT_SUM)
_ratio_sorted = sorted(_ratio_series, key=lambda kv: -kv[1])
RATIO_HI = "、".join("%s 的 %.2f 倍" % (md(_d)[0], v) for _d, v in _ratio_sorted[:3])
_touch_series_prev = [(_d, v) for _d, v in _touch_series if _d != D0]
_growth = []
_gseq = sorted(_touch_series, key=lambda kv: kv[0])
for _i in range(1, len(_gseq)):
    if _gseq[_i - 1][1]:
        _growth.append((_gseq[_i][0], (_gseq[_i][1] / _gseq[_i - 1][1] - 1) * 100))
_g_now = (TOUCH / TOUCH_Y - 1) * 100
TOUCH_G_RANK = 1 + sum(1 for _, g in _growth if g > _g_now)
_all_tot = _tot_series + [(D0, TOT)]
AMT_LOW_RANK = sum(1 for _, v in _all_tot if v < TOT) + 1
AMT_RANK = sum(1 for _, v in _all_tot if v > TOT) + 1
V.update({"NTDAYS": str(len(_all_tot)), "TOUCH_RANK": str(TOUCH_RANK),
          "TOUCH_G_RANK": str(TOUCH_G_RANK), "ZB_R_RANK": str(ZB_R_RANK),
          "AMT_LOW_RANK": str(AMT_LOW_RANK), "SEAL_RANK": str(SEAL_RANK), "ZB_R_LOW": str(ZB_R_LOW),
          "SEAL_TOP": SEAL_TOP, "RATIO_HI": RATIO_HI, "AMT_RANK": str(AMT_RANK)})

# ---------------- 高封板率次日样本 + 单日跳升幅度排名（全部现算） ----------------
_hist = []
for _f in sorted(_glob.glob(os.path.join(OUT, "zt_review_*.json"))):
    try:
        _R = json.load(open(_f, encoding="utf-8"))
    except Exception:
        continue
    _d = _R.get("D0")
    if not _d or _d not in (_R.get("dates") or {}):
        continue
    _t = ((_R["dates"][_d].get("ths_zt") or {}).get("total") or {}).get("today") or {}
    if not _t or not _t.get("rate"):
        continue
    _hist.append([_d, _t["num"], _t["history_num"], _t["rate"] * 100])
_hist.sort()
_dd = {r[0]: i for i, r in enumerate(_hist)}
HW, HD, HZT_D = [], [], []
for _i, _r in enumerate(_hist):
    if _r[0] == D0 or _r[3] < 83.0:
        continue
    if _i + 1 >= len(_hist):
        continue
    _n = _hist[_i + 1]
    HW.append((_r[0], _r[3], _n[3], _n[3] - _r[3]))
    HD.append(_n[2] - _n[1])
    HZT_D.append(_n[1] - _r[1])
HW_N = len(HW)
HW_DOWN = sum(1 for x in HW if x[3] < 0)
HW_MEAN = mean([x[3] for x in HW]) if HW else 0
HW_MIN = min([x[3] for x in HW]) if HW else 0
HW_MAX = max([x[3] for x in HW]) if HW else 0
HZT_DOWN = sum(1 for v in HZT_D if v < 0)
V.update({
    "HW_N": str(HW_N), "HW_DOWN": str(HW_DOWN), "HW_MEAN": f"{HW_MEAN:+.1f}",
    "HW_MIN": f"{HW_MIN:+.1f}", "HW_MAX": f"{HW_MAX:+.1f}",
    "HW_TXT": "；".join("%s %.1f%%→%.1f%%（%+.1f）" % (md(d)[0], a, b, c) for d, a, b, c in HW) or "—",
    "HZT_DOWN": str(HZT_DOWN), "HW_N2": str(len(HZT_D)),
})
# 单日封板率跳升幅度排名
_sw = [( _hist[_i][0], _hist[_i][3] - _hist[_i-1][3]) for _i in range(1, len(_hist))]
_now_up = SEAL - SEAL_Y
SW_RANK = 1 + sum(1 for _, v in _sw if v > _now_up)
SW_TOP = "、".join("%s %+.1f" % (md(d)[0], v) for d, v in sorted(_sw, key=lambda kv: -kv[1])[:3])
V.update({"SW_RANK": str(SW_RANK), "SW_TOP": SW_TOP, "SEAL_UP": f"{_now_up:+.1f}"})

# ---------------- 渲染 ----------------
html = open(TPL, encoding="utf-8").read()
for k, val in V.items():
    html = html.replace(f"__{k}__", str(val))

res = sorted(set(re.findall(r"__[A-Z_0-9]+__", html)))
print("placeholder residue:", res)
if res:
    sys.exit(1)
out = os.path.join(REP, f"涨停复盘对比-{D0}.html")
open(out, "w", encoding="utf-8").write(html)
print("saved ->", out, len(html), "chars")

# ---------------- 复核 ----------------
print("\n=== 复核 ===")
print(f"涨停 {ZT}(昨{ZT_Y}) 触及 {TOUCH}(昨{TOUCH_Y}) 封板率 {SEAL:.1f}(昨{SEAL_Y:.1f})")
print(f"跌停 {DT}(昨{DT_Y}) 触及跌停 {DTOUCH}(昨{DTOUCH_Y}) 封死率 {DSEAL:.1f}")
print(f"梯队 今{lad0} 昨{lad1}  连板 {LB}/{LB_Y} 最高 {MAXB}/{MAXB_Y} 真空层 {V['LAD_VAC']}")
print(f"晋级 {len(AGAIN)}/{len(perf)} = {len(AGAIN)/len(perf)*100:.1f}%  首板组{V['SHOU_ADV']}/{len(G_SB)}({median(P_SB):+.2f}) 连板组{V['LB_ADV']}/{len(G_LB)}({median(P_LB):+.2f}) GAP {GAP:+.2f}")
print(f"涨停股成交 {AMT_SUM:.1f}(昨{AMT_SUM_Y:.1f}) 密度 {AMT_SUM/TOT*100:.2f}%(昨{AMT_SUM_Y/TOT_Y*100:.2f}%)")
print(f"炸板 {len(zb0)} 回封 {len(ZB_SEALED)}(昨{len(ZB_SEALED_Y)}/{len(zb1)}) 成交 {ZB_AMT:.1f}(昨{ZB_AMT_Y:.1f}) = 涨停股 {ZB_AMT/AMT_SUM:.2f} 倍")
print(f"行业 {len(hy0)}/{len(hy1)} 清零{len(zero)} 新增{len(new)} 闭合 {sum(hy0.values())}/{len(ths0)}")
print(f"AI 三链并集 {len(AI_SET)}只 {AI_AMT:.1f}亿 {AI_AMT/AMT_SUM*100:.1f}% 连板{AI_LB}")
print(f"机器人 {ROB[0]}只/连板{ROB[1]}/{ROB[2]:.1f}亿/{ROB[2]/AMT_SUM*100:.1f}% 昨 {C1['机器人/具身智能'][0]}/{C1['机器人/具身智能'][2]/AMT_SUM_Y*100:.1f}%")
print(f"半导体 {SEMI[0]}只/{SEMI[2]:.1f}亿/{SEMI[2]/AMT_SUM*100:.1f}%  传媒 {MEDIA[0]}只/{MEDIA[2]:.1f}亿/{MEDIA[2]/AMT_SUM*100:.1f}%")
print(f"名称 东方{len(DF)} 羊{len(YANG)} 并集{len(NM)} 成交{NM_AMT:.1f}亿 {NM_AMT/AMT_SUM*100:.1f}% 昨{len(NM1)}只{NM_AMT1/AMT_SUM_Y*100:.1f}%")
print(f"早盘封板 {EARLY}/{ZT}={EARLY/ZT*100:.1f}% 昨 {EARLY_Y}/{ZT_Y}={EARLY_Y/ZT_Y*100:.1f}% 午后+尾盘 {LATE}(昨{LATE_Y})")
print(f"缺口 上沿{GAP_TOP:.2f} 下沿{GAP_BOT:.2f} 最高{HIGH_SH:.2f} 回补{GAP_FILL:.0f}% 剩{GAP_LEFT:.1f}%")
print(f"市值 <100亿 {SMALL}/{ZT}={SMALL/ZT*100:.1f}% 分布 {band}")
print(f"封板率排名 第{SEAL_RANK}高 / {NTDAYS} 日；炸板比排名 第{ZB_R_RANK}高")
