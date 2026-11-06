# -*- coding: utf-8 -*-
"""涨停复盘报告 20261106 vs 20261105（外部冲击 × 广度出清 · 算力链第5轮 · 缩量缺口日）
用法：python scripts/zt_report_20261106.py 20261106
输入：out/zt_stats_20261106.json、out/zt_review_20261106.json / 20261105.json / 20261104.json
     跌停明细 out/_dt1106.json；westock 榜 out/_sw1106.json
输出：reports/涨停复盘对比-20261106.html
"""
import json, os, sys, re, datetime, time as _t
from statistics import mean, median
from collections import Counter, defaultdict

ROOT = os.environ.get("ZT_ROOT") or os.getcwd()
OUT = os.path.join(ROOT, "out")
REP = os.path.join(ROOT, "reports")
TPL = os.path.join(ROOT, "scripts", "_report_tpl_20261106.html")
os.makedirs(REP, exist_ok=True)

D0 = sys.argv[1] if len(sys.argv) > 1 else "20261106"
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
V["NEXT_D"] = "11/9 周一"
V["GEN_TIME"] = _t.strftime("%Y-%m-%d %H:%M")
V["D0"] = D0
V["D1"] = D1

# ---------------- 池子 ----------------
p0 = {x["c"]: x for x in (A0["em_ZT"]["pool"] or [])}
# ★ 昨日标签必须取自 D1 当日报文文件（今日重抓的东财池有重复行 + 缺票，见口径节）
p1 = {x["c"]: x for x in (B1["dates"][D1]["em_ZT"]["pool"] or [])}
P1_FRESH = A1["em_ZT"]["pool"] or []
ths0 = {x["code"]: x for x in A0["ths_zt"]["info"]}
ths1 = {x["code"]: x for x in A1["ths_zt"]["info"]}
zb0 = A0["em_ZB"]["pool"] or []
zb1 = B1["dates"][D1]["em_ZB"]["pool"] or []
dt0 = (load(os.path.join(OUT, f"_dt{D0[4:]}.json"), {}) or {}).get("data", {}).get("pool") or []
SW = load(os.path.join(OUT, f"_sw{D0[4:]}.json"), {}) or {}

assert len(p0) == len(ths0), f"今日池不一致 {len(p0)} vs {len(ths0)}"
assert sum(1 for c in ths1 if c not in p1) == 0, "昨日标签覆盖不全"

_p2 = B2["dates"][D2]["em_ZT"]["pool"] or []
_t2 = {x["code"] for x in A2["ths_zt"]["info"]}
SUM_2 = sum(x.get("amount", 0) for x in _p2 if x["c"] in _t2) / 1e8

# ---------------- 情绪 ----------------
zt0i = A0["ths_zt"]["total"]["today"]
zt1i = A1["ths_zt"]["total"]["today"]
ld0 = A0["ths_zt"]["limit_down_count"]["today"]
ld1 = A1["ths_zt"]["limit_down_count"]["today"]
ld2 = S2["senti"][D2]["limit_down_count"]["today"]

ZT, ZT_Y = zt0i["num"], zt1i["num"]
ZT_2 = S2["senti"][D2]["zt"]
TOUCH, TOUCH_Y = zt0i["history_num"], zt1i["history_num"]
TOUCH_2 = A2["ths_zt"]["total"]["today"]["history_num"]
SEAL, SEAL_Y = zt0i["rate"] * 100, zt1i["rate"] * 100
SEAL_2 = S2["senti"][D2]["seal_rate"] * 100
ZB, ZB_Y = s0["zb"], S1["senti"][D1]["zb"]
DT, DT_Y, DT_2 = ld0["num"], ld1["num"], S2["senti"][D2]["dt"]
DTOUCH, DTOUCH_Y, DTOUCH_2 = ld0["history_num"], ld1["history_num"], ld2["history_num"]
DSEAL, DSEAL_Y = ld0["rate"] * 100, ld1["rate"] * 100
DSEAL_2 = ld2["rate"] * 100
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
    "ZT_PCT_D": f"{(ZT / ZT_Y - 1) * 100:+.1f}", "ZT_DN_PCT": f"{(1 - ZT / ZT_Y) * 100:.1f}",
    "TOUCH": str(TOUCH), "TOUCH_Y": str(TOUCH_Y), "TOUCH_D": f"{TOUCH - TOUCH_Y:+d}",
    "TOUCH_DN_PCT": f"{(1 - TOUCH / TOUCH_Y) * 100:.1f}",
    "SEAL": f"{SEAL:.1f}", "SEAL_Y": f"{SEAL_Y:.1f}", "SEAL_D": f"{SEAL - SEAL_Y:+.1f}",
    "SEAL_D_ABS": f"{abs(SEAL - SEAL_Y):.1f}",
    "ZB": str(ZB), "ZB_Y": str(ZB_Y), "ZB_EM": str(len(zb0)),
    "ZB_DIFF": str(len(zb0) - ZB),
    "DT": str(DT), "DT_Y": str(DT_Y), "DT_D": f"{DT - DT_Y:+d}",
    "DTOUCH": str(DTOUCH), "DTOUCH_Y": str(DTOUCH_Y), "DSEAL": f"{DSEAL:.1f}",
    "DSEAL_Y": f"{DSEAL_Y:.1f}", "DT_OPEN_N": str(DT_OPEN_N),
    "TOUCH_GAP": str(TOUCH - ZT),
    "SEAL_FAIL": f"{(TOUCH - ZT) / TOUCH * 100:.1f}",
    "SEAL_FAIL_Y": f"{(TOUCH_Y - ZT_Y) / TOUCH_Y * 100:.1f}",
    "LB": str(LB), "LB_Y": str(LB_Y), "LB_D": f"{LB - LB_Y:+d}",
    "LB_PCT": f"{LB / ZT * 100:.1f}", "LB_PCT_Y": f"{LB_Y / ZT_Y * 100:.1f}",
    "LB_PCT_D": f"{LB / ZT * 100 - LB_Y / ZT_Y * 100:+.1f}",
    "SHOU": str(SHOU), "SHOU_Y": str(SHOU_Y),
    "SHOU_PCT": f"{SHOU / ZT * 100:.1f}", "SHOU_PCT_Y": f"{SHOU_Y / ZT_Y * 100:.1f}",
    "SHOU_DN_PCT": f"{(1 - SHOU / SHOU_Y) * 100:.1f}",
    "MAXB": str(MAXB), "MAXB_Y": str(MAXB_Y),
})

# ---------------- 梯队 ----------------
LAD_ROWS = []
for b in range(1, max(max(lad0), max(lad1)) + 1):
    a, y = lad0.get(b, 0), lad1.get(b, 0)
    d = a - y
    LAD_ROWS.append("<tr><td>%d 板</td><td class=\"hl\">%d</td><td>%d</td><td class=\"%s\">%+d</td></tr>"
                    % (b, a, y, ("up" if d > 0 else ("down" if d < 0 else "mut")), d))
V["TBL_LAD"] = "\n".join(LAD_ROWS)
LAD3P, LAD3P_Y = sum(v for k, v in lad0.items() if k >= 3), sum(v for k, v in lad1.items() if k >= 3)
V["LAD3P"], V["LAD3P_Y"] = str(LAD3P), str(LAD3P_Y)
V["LAD2"], V["LAD2_Y"] = str(lad0.get(2, 0)), str(lad1.get(2, 0))
V["LAD2_DN_PCT"] = f"{(1 - lad0.get(2, 0) / max(lad1.get(2, 0), 1)) * 100:.1f}"
V["LAD3"], V["LAD3_Y"] = str(lad0.get(3, 0)), str(lad1.get(3, 0))
V["LAD4"], V["LAD4_Y"] = str(lad0.get(4, 0)), str(lad1.get(4, 0))
V["LAD5"] = str(lad0.get(5, 0)); V["LAD5_Y"] = str(lad1.get(5, 0))

# ---------------- 指数 ----------------
NAME = {"sh000001": "上证指数", "sz399001": "深证成指", "sz399006": "创业板指", "sh000688": "科创50",
        "bj899050": "北证50", "sh000300": "沪深300", "sh000852": "中证1000", "sh000905": "中证500",
        "sz399303": "国证2000", "sh000016": "上证50", "sz399005": "中小100"}
idx0, idx1 = B["indexes"], B1["indexes"]
rows_idx, yoy = [], []
n_up = n_dn = n_amt_up = n_amt_dn = 0
intra = {"labels": [], "gap": [], "low": [], "high": [], "close": []}
n_above_open = n_gap_up = 0
INTRA_CODES = ["sh000001", "sz399001", "sz399006", "sh000688", "sh000300", "sz399303"]
TOT = 0.0
for k, nm in NAME.items():
    a, b = idx0.get(k) or {}, idx1.get(k) or {}
    if not a:
        continue
    p0v, p1v = a.get("pct") or 0, b.get("pct") or 0
    m0, m1 = a.get("amount_wan") or 0, b.get("amount_wan") or 0
    chg = (m0 / m1 - 1) * 100 if m1 else 0
    n_up += p0v > 0; n_dn += p0v < 0
    n_amt_up += chg > 0; n_amt_dn += chg <= 0
    yoy.append((nm, chg, p0v))
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
    "YOY_MAX": f"{min(yoy, key=lambda r: r[1])[1]:+.1f}%", "YOY_MAX_NAME": min(yoy, key=lambda r: r[1])[0],
    "YOY_MIN": f"{max(yoy, key=lambda r: r[1])[1]:+.1f}%", "YOY_MIN_NAME": max(yoy, key=lambda r: r[1])[0],
    "N_INTRA": str(len(intra["labels"])), "N_ABOVE_OPEN": str(n_above_open), "N_GAP_UP": str(n_gap_up),
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
    "SH_GAP": gi("sh000001", "open"), "SH_HIGH": gi("sh000001", "high"),
    "SH_LOW": gi("sh000001", "low"), "SH_PCT": gp("sh000001"),
    "CY_GAP": gi("sz399006", "open"), "CY_PCT": gp("sz399006"),
    "KC_GAP": gi("sh000688", "open"), "KC_HIGH": gi("sh000688", "high"),
    "KC_LOW": gi("sh000688", "low"), "KC_PCT": gp("sh000688"),
    "KC_RANGE": f"{float(gi('sh000688', 'high')) - float(gi('sh000688', 'low')):.2f}",
    "KC_REBOUND": f"{float(gp('sh000688')) - float(gi('sh000688', 'low')):.2f}",
    "GZ_GAP": gi("sz399303", "open"), "GZ_PCT": gp("sz399303"),
    "SH50_GAP": gi("sh000016", "open"), "SH50_PCT": gp("sh000016"),
    "SH50_YOY": f"{yoy_of('sh000016'):+.1f}", "ZXX_YOY": f"{yoy_of('sz399005'):+.1f}",
    "ZZ500_YOY": f"{yoy_of('sh000905'):+.1f}", "KC_YOY": f"{yoy_of('sh000688'):+.1f}",
    "SH_OPEN": f"{idx0['sh000001']['open']:.2f}", "SH_PREV": f"{idx0['sh000001']['prev']:.2f}",
    "SH_LOW_PT": f"{idx0['sh000001']['low']:.2f}",
    "GAP_PTS": f"{idx0['sh000001']['prev'] - idx0['sh000001']['open']:.2f}",
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

fund0 = [x.get("fund", 0) / 1e8 for x in p0.values() if x["c"] in ths0]
fund1 = [x.get("fund", 0) / 1e8 for x in p1.values() if x["c"] in ths1]
amts0 = [x.get("amount", 0) / 1e8 for x in p0.values() if x["c"] in ths0]
amts1 = [x.get("amount", 0) / 1e8 for x in p1.values() if x["c"] in ths1]
mvs0 = [x.get("ltsz", 0) / 1e8 for x in p0.values() if x["c"] in ths0]
mvs1 = [x.get("ltsz", 0) / 1e8 for x in p1.values() if x["c"] in ths1]
FUND, FUND_Y = sum(fund0), sum(fund1)
V.update({
    "FUND": f"{FUND:.1f}", "FUND_Y": f"{FUND_Y:.1f}", "FUND_PCT": f"{(FUND / FUND_Y - 1) * 100:+.1f}",
    "FUND_MED": f"{median(fund0):.2f}", "FUND_MED_Y": f"{median(fund1):.2f}",
    "FUND_MED_DIR": "回升" if median(fund0) > median(fund1) else "下降",
    "FUND_TOP_Y": f"{max(fund1):.2f}",
    "MED_AMT": f"{median(amts0):.2f}", "MED_AMT_Y": f"{median(amts1):.2f}",
    "MED_AMT_PCT": f"{(median(amts0) / median(amts1) - 1) * 100:+.1f}",
    "ZT_MED_MV": f"{median(mvs0):.0f}", "ZT_MED_MV_Y": f"{median(mvs1):.0f}",
})
YIZI = sum(1 for x in ths0.values() if "一字" in (x.get("limit_up_type") or ""))
TZI = sum(1 for x in ths0.values() if "T字" in (x.get("limit_up_type") or ""))
V["YIZI"], V["TZI"] = str(YIZI), str(TZI)
# 外盘：媒体转述口径（新浪财经 / 21 世纪经济报道 2026-11-06），非本报告一手核实
V["SOX_PCT"] = "12.25"
V["NDX_PCT"] = "5.52"

# ---------------- 炸板 ----------------
ZB_AMT = sum(x.get("amount", 0) for x in zb0) / 1e8
ZB_AMT_Y = sum(x.get("amount", 0) for x in zb1) / 1e8
ZB_SEALED = [x for x in zb0 if x.get("p", 0) >= x.get("ztp", 0)]
zb_top = sorted(zb0, key=lambda y: -y.get("amount", 0))[:5]
V.update({
    "ZB_SEALED_N": str(len(ZB_SEALED)),
    "ZB_SEAL_PCT": f"{len(ZB_SEALED) / max(len(zb0), 1) * 100:.0f}",
    "ZB_AMT": f"{ZB_AMT:.1f}", "ZB_AMT_Y": f"{ZB_AMT_Y:.1f}",
    "ZB_RATIO": f"{ZB_AMT / AMT_SUM:.2f}", "ZB_RATIO_Y": f"{ZB_AMT_Y / AMT_SUM_Y:.2f}",
    "ZB_TOP5_TXT": "、".join("%s（%s，%s 亿）" % (x["n"], x.get("hybk") or "—", f"{x.get('amount', 0) / 1e8:.2f}") for x in zb_top),
})
zbt = max(zb0, key=lambda y: y.get("ltsz", 0))
zba = max(zb0, key=lambda y: y.get("amount", 0))
V.update({"ZBT_MV": f"{zbt.get('ltsz', 0) / 1e8:.0f}", "ZBT_AMT": f"{zbt.get('amount', 0) / 1e8:.2f}",
          "ZBT_PCT": f"{zbt.get('zdp', 0):+.2f}", "ZBT_NAME": zbt["n"], "ZBT_HY": zbt.get("hybk") or "—",
          "ZBA_MV": f"{zba.get('ltsz', 0) / 1e8:.0f}", "ZBA_AMT": f"{zba.get('amount', 0) / 1e8:.2f}",
          "ZBA_PCT": f"{zba.get('zdp', 0):+.2f}", "ZBA_NAME": zba["n"], "ZBA_HY": zba.get("hybk") or "—"})

# ---------------- 跌停 ----------------
DT_AMT = sum(x.get("amount", 0) for x in dt0) / 1e8
V.update({
    "DT_EM": str(len(dt0)), "DT_DIFF": str(len(dt0) - DT),
    "DT_AMT": f"{DT_AMT:.1f}", "DT_RATIO": f"{DT_AMT / AMT_SUM:.2f}", "DT_RATIO_Y": "0（昨无跌停）",
})
dt_sorted = sorted(dt0, key=lambda y: -y.get("amount", 0))
CALC_CODE = {"002384", "603083", "605058"}  # 元件/通信设备：东山精密、剑桥科技、澳弘电子
CALC = [x for x in dt0 if x["c"] in CALC_CODE]
OTHER = [x for x in dt0 if x["c"] not in CALC_CODE]
CALC_AMT = sum(x.get("amount", 0) for x in CALC) / 1e8
OTHER_AMT = sum(x.get("amount", 0) for x in OTHER) / 1e8
BIG = [x for x in dt0 if x.get("ltsz", 0) / 1e8 > 100]
BIG_AMT = sum(x.get("amount", 0) for x in BIG) / 1e8
hy_dt = Counter(x.get("hybk") or "(空)" for x in dt0)
V.update({
    "DT_HY_N": str(len(hy_dt)),
    "DT_HYN_DIST": "、".join("%s %d 只" % (k, v) for k, v in sorted(hy_dt.items(), key=lambda kv: (-kv[1], kv[0]))),
    "DT_BIG_N": str(len(BIG)), "DT_BIG_PCT": f"{len(BIG) / len(dt0) * 100:.0f}",
    "DT_BIG_AMT_SHARE": f"{BIG_AMT / DT_AMT * 100:.1f}",
    "DT_YY_N": str(sum(1 for x in dt0 if x.get("hybk") == "元件")),
    "DT_TX_N": str(sum(1 for x in dt0 if x.get("hybk") == "通信设备")),
    "DT_CALC_N": str(len(CALC)), "DT_CALC_AMT": f"{CALC_AMT:.1f}",
    "DT_CALC_SHARE": f"{CALC_AMT / DT_AMT * 100:.1f}",
    "DT_OTHER_N": str(len(OTHER)), "DT_OTHER_HY": str(len(Counter(x.get("hybk") for x in OTHER))),
    "DT_OTHER_AMT": f"{OTHER_AMT:.1f}",
    "CALC_ROUND": "5",
})
dp = p0.get("002384") or next((x for x in dt0 if x["c"] == "002384"), {})
DP_AMT = dp.get("amount", 0) / 1e8
jq = next((x for x in dt0 if x["c"] == "603083"), {})
V.update({
    "DP_AMT": f"{DP_AMT:.1f}", "DP_MV": f"{dp.get('ltsz', 0) / 1e8:.0f}",
    "DP_SHARE": f"{DP_AMT / DT_AMT * 100:.1f}", "DP_PCT": f"{dp.get('zdp', 0):+.2f}",
    "DP_MULT": f"{DP_AMT / (DT_AMT - DP_AMT):.2f}",
    "JQ_MV": f"{jq.get('ltsz', 0) / 1e8:.0f}", "JQ_AMT": f"{jq.get('amount', 0) / 1e8:.1f}",
})
DT_ROWS = []
for x in dt_sorted:
    note = ""
    if x["c"] in CALC_CODE:
        note = "算力硬件链"
    if x["c"] == "000678":
        note = "10-26 的 3 板机器人标的"
    DT_ROWS.append('<tr><td>%s</td><td>%s</td><td>%s</td><td class="down">%+.2f%%</td><td>%s</td><td>%s</td><td class="note">%s</td></tr>'
                   % (x["c"], x["n"], x.get("hybk") or "—", x.get("zdp", 0),
                      f"{x.get('amount', 0) / 1e8:.2f}", f"{x.get('ltsz', 0) / 1e8:.0f}", note))
V["TBL_DT"] = "\n".join(DT_ROWS)

# ---------------- 昨日涨停股今日表现 ----------------
q = B["yesterday_zt_today"]


def sym_of(c):
    if c.startswith(("60", "68", "5", "11", "9")):
        return "sh" + c
    if c.startswith(("43", "83", "87", "92")):
        return "bj" + c
    return "sz" + c


perf = []
for c in ths1:
    v = q.get(sym_of(c))
    if not v:
        continue
    perf.append({"code": c, "name": ths1[c]["name"], "lbc": p1[c].get("lbc") or 1,
                 "hy": p1[c].get("hybk") or "",
                 "reason": ths1[c].get("reason_type") or "",
                 "pct": v["pct"], "again": c in p0})
P = [r["pct"] for r in perf]
AGAIN = [r for r in perf if r["again"]]
G_SB = [r for r in perf if r["lbc"] == 1]
G_LB = [r for r in perf if r["lbc"] > 1]
P_SB = [r["pct"] for r in G_SB]
P_LB = [r["pct"] for r in G_LB]
GAP = median(P_SB) - median(P_LB)
GAP_Y = 6.00  # 11-05 报告的实测值
V.update({
    "ADV_TOT": str(len(perf)), "ADV_N": str(len(AGAIN)),
    "ADV_RATE": f"{len(AGAIN) / len(perf) * 100:.1f}",
    "PERF_MEAN": f"{mean(P):+.2f}", "PERF_MED": f"{median(P):+.2f}",
    "PERF_MAX": f"{max(P):+.2f}", "PERF_MIN": f"{min(P):+.2f}",
    "PERF_DN_N": str(sum(1 for p in P if p < 0)),
    "PERF_DN_PCT": f"{sum(1 for p in P if p < 0) / len(P) * 100:.1f}",
    "PERF_DN5_N": str(sum(1 for p in P if p < -5)),
    "GAP": f"{GAP:+.2f}", "GAP_Y": f"{GAP_Y:+.2f}", "GAP_SWING": f"{abs(GAP - GAP_Y):.2f}",
    "SB_MED": f"{median(P_SB):+.2f}", "LB_MED": f"{median(P_LB):+.2f}",
})
PROWS = []
for k, g in (("昨日首板", G_SB), ("昨日连板", G_LB)):
    gp_ = [x["pct"] for x in g]
    ga = sum(1 for x in g if x["again"])
    PROWS.append('<tr><td>%s</td><td>%d</td><td class="hl">%.1f%%</td><td>%+.2f%%</td><td class="%s">%+.2f%%</td><td>%d 只</td></tr>'
                 % (k, len(g), ga / len(g) * 100, mean(gp_),
                    "up" if median(gp_) >= 0 else "down", median(gp_), sum(1 for p in gp_ if p < 0)))
V["TBL_PERF"] = "\n".join(PROWS)
top5 = sorted(perf, key=lambda r: -r["pct"])[:5]
bot5 = sorted(perf, key=lambda r: r["pct"])[:5]
V["PERF_TOP_TXT"] = "；".join("%s %+.2f%%（昨 %d 板）" % (r["name"], r["pct"], r["lbc"]) for r in top5)
V["PERF_BOT_TXT"] = "；".join("%s %+.2f%%（昨 %d 板）" % (r["name"], r["pct"], r["lbc"]) for r in bot5)
dt_codes = {x["c"] for x in dt0}
ZT2DT = [r for r in perf if r["code"] in dt_codes]
V["ZT2DT_N"] = str(len(ZT2DT))
V["ZT2DT_TXT"] = "、".join("%s（昨 %d 板，%+.2f%%）" % (r["name"], r["lbc"], r["pct"]) for r in ZT2DT) or "无"

# ---------------- 题材簇 ----------------
CL = [
    ("光伏", ["光伏", "硅料", "硅片", "电池片", "组件", "银浆", "胶膜", "坩埚", "TOPCon", "HJT", "钙钛矿", "逆变器", "边框"]),
    ("储能/固态电池", ["储能", "固态电池", "电解液", "锂电", "电池铝箔"]),
    ("机器人/具身", ["机器人", "具身", "灵巧手"]),
    ("算力/数据中心", ["算力", "数据中心", "服务器", "光模块", "IDC", "液冷"]),
    ("AI/传媒内容", ["AI漫剧", "短剧", "影视", "AIGC", "AI营销", "IP运营", "院线", "AI应用", "智能体"]),
    ("半导体/芯片", ["半导体", "芯片", "存储", "光刻", "封测", "晶圆"]),
]


def clus(rules, thsmap, pmap):
    out = {}
    for nm, kws in rules:
        sel = [c for c, x in thsmap.items() if any(w in (x.get("reason_type") or "") for w in kws)]
        amt = sum((pmap.get(c) or {}).get("amount", 0) for c in sel) / 1e8
        lb = sum(1 for c in sel if (pmap.get(c) or {}).get("lbc", 1) > 1)
        out[nm] = (len(sel), lb, amt)
    return out


C0 = clus(CL, ths0, p0)
C1 = clus(CL, ths1, p1)
DF = [c for c, x in ths0.items() if "东方" in x["name"]]
YANG = [c for c, x in ths0.items() if "羊" in (x.get("reason_type") or "") and "字辈" in (x.get("reason_type") or "")]
NM = sorted(set(DF) | set(YANG))
NM_AMT = sum(p0[c].get("amount", 0) for c in NM) / 1e8
NM_HY = len({(p0[c].get("hybk") or "(空)") for c in NM})
NM_LB = sum(1 for c in NM if p0[c].get("lbc", 1) > 1)
V.update({
    "PV_N": str(C0["光伏"][0]), "PV_N_Y": str(C1["光伏"][0]),
    "PV_LB": str(C0["光伏"][1]), "PV_AMT": f"{C0['光伏'][2]:.1f}",
    "PV_SHARE": f"{C0['光伏'][2] / AMT_SUM * 100:.1f}",
    "PV_DN_PCT": f"{(1 - C0['光伏'][0] / max(C1['光伏'][0], 1)) * 100:.1f}",
    "PV_HY": str(sum(1 for c in ths0 if (p0.get(c) or {}).get("hybk") == "光伏设备")),
    "PV_HY_Y": str(sum(1 for c in ths1 if (p1.get(c) or {}).get("hybk") == "光伏设备")),
    "PV_FUND": f"{sum(p0[c].get('fund', 0) for c in ths0 if p0[c].get('hybk') == '光伏设备') / 1e8:.2f}",
    "DF_N": str(len(DF)), "YANG_N": str(len(YANG)), "NM_N": str(len(NM)),
    "NM_AMT": f"{NM_AMT:.1f}", "NM_SHARE": f"{NM_AMT / AMT_SUM * 100:.1f}",
    "NM_HY": str(NM_HY), "NM_LB": str(NM_LB),
    "DF_LIST": "、".join(f"{p0[c]['n']}（{p0[c].get('hybk') or '—'}，{p0[c].get('lbc', 1)} 板）" for c in sorted(DF, key=lambda c: -p0[c].get("lbc", 1))),
    "YANG_LIST": "、".join(f"{p0[c]['n']}（{p0[c].get('lbc', 1)} 板）" for c in sorted(YANG, key=lambda c: -p0[c].get("lbc", 1))),
})

_pvl = sorted([c for c in ths0 if any(w in (ths0[c].get("reason_type") or "") for w in CL[0][1])],
               key=lambda c: -p0[c].get("lbc", 1))[:3]
V["PV_LB_TXT"] = "、".join("%s %d 板" % (p0[c]["n"], p0[c].get("lbc", 1)) for c in _pvl)

MROWS = []
for nm, _ in CL:
    a, b = C0[nm], C1[nm]
    d = a[0] - b[0]
    MROWS.append('<tr><td>%s</td><td>%d</td><td class="%s">%d</td><td>%d</td><td>%s</td><td>%s%%</td></tr>'
                 % (nm, b[0], "up" if d > 0 else ("down" if d < 0 else "mut"), a[0], a[1],
                    f"{a[2]:.1f}", f"{a[2] / AMT_SUM * 100:.1f}"))
MROWS.append('<tr><td><b>【名称】「东方」字辈</b></td><td>—</td><td class="hl">%d</td><td>%d</td><td>%s</td><td>%s%%</td></tr>'
             % (len(DF), sum(1 for c in DF if p0[c].get("lbc", 1) > 1),
                f"{sum(p0[c].get('amount', 0) for c in DF) / 1e8:.1f}",
                f"{sum(p0[c].get('amount', 0) for c in DF) / 1e8 / AMT_SUM * 100:.1f}"))
MROWS.append('<tr><td><b>【名称】「羊」字辈</b></td><td>—</td><td class="hl">%d</td><td>%d</td><td>%s</td><td>%s%%</td></tr>'
             % (len(YANG), sum(1 for c in YANG if p0[c].get("lbc", 1) > 1),
                f"{sum(p0[c].get('amount', 0) for c in YANG) / 1e8:.1f}",
                f"{sum(p0[c].get('amount', 0) for c in YANG) / 1e8 / AMT_SUM * 100:.1f}"))
V["TBL_MAIN"] = "\n".join(MROWS)

# 概念板榜
BLK = {b["name"]: b for b in (A0["ths_block"] or [])}


def br(nm):
    b = BLK.get(nm)
    return f"{b['continuous_plate_num'] / b['limit_up_num'] * 100:.1f}" if b and b.get("limit_up_num") else "0.0"


V.update({
    "PV_CONC_N": str((BLK.get("光伏概念") or {}).get("limit_up_num", 0)),
    "PV_CONC_LB": str((BLK.get("光伏概念") or {}).get("continuous_plate_num", 0)),
    "PV_CONC_R": br("光伏概念"),
    "ES_CONC_N": str((BLK.get("储能") or {}).get("limit_up_num", 0)),
    "ES_CONC_LB": str((BLK.get("储能") or {}).get("continuous_plate_num", 0)),
    "ES_CONC_R": br("储能"),
    "XNY_R": br("新能源汽车"), "DS_R": br("DeepSeek概念"), "BYD_R": br("比亚迪概念"),
    "ROBOT_R": br("机器人概念"), "HW_R": br("华为概念"), "YDYL_R": br("一带一路"),
    "R40_N": str(sum(1 for _b in BLK.values()
                     if _b.get("limit_up_num") and _b["continuous_plate_num"] / _b["limit_up_num"] >= 0.4)),
})

# 行业迁移
hy0 = Counter((p0[c].get("hybk") or "(空)") for c in ths0)
hy1 = Counter((p1[c].get("hybk") or "(空)") for c in ths1)
assert sum(hy0.values()) == len(ths0), "今日行业闭合失败"
assert sum(hy1.values()) == len(ths1), "昨日行业闭合失败"
zero = sorted([k for k in hy1 if hy0.get(k, 0) == 0], key=lambda k: (-hy1[k], k))
new = sorted([k for k in hy0 if hy1.get(k, 0) == 0], key=lambda k: (-hy0[k], k))
V.update({
    "HY_N": str(len(hy0)), "HY_N_Y": str(len(hy1)),
    "HY_DIFF": str(len(hy1) - len(hy0)),
    "HY_ZERO_N": str(len(zero)), "HY_NEW_N": str(len(new)),
})
V["HY_TXT"] = ("<b>清零 %d 个</b>（%s）；<b>新增 %d 个</b>（%s）。最大流出是光伏设备 %d→%d（-%d）、专用设备 %d→0、半导体 %d→0。"
               % (len(zero), "、".join(zero[:10]) + ("等" if len(zero) > 10 else ""),
                  len(new), "、".join(new),
                  hy1.get("光伏设备", 0), hy0.get("光伏设备", 0), hy1.get("光伏设备", 0) - hy0.get("光伏设备", 0),
                  hy1.get("专用设备", 0), hy1.get("半导体", 0)))
HY_ROWS = []
allhy = sorted(set(hy0) | set(hy1), key=lambda k: (-((hy0.get(k, 0) + hy1.get(k, 0)) + abs(hy0.get(k, 0) - hy1.get(k, 0)) * 2), -hy0.get(k, 0), k))
for k in allhy[:18]:
    a, b = hy0.get(k, 0), hy1.get(k, 0)
    d = a - b
    HY_ROWS.append('<tr><td>%s</td><td>%d</td><td>%d</td><td class="%s">%+d</td></tr>'
                   % (k, a, b, "up" if d > 0 else ("down" if d < 0 else "mut"), d))
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
    if hh * 60 + mm <= 14 * 60 + 57:
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
V.update({"TS_EARLY": str(EARLY), "TS_EARLY_Y": str(EARLY_Y),
          "TS_EARLY_PCT": f"{EARLY / ZT * 100:.1f}", "TS_EARLY_PCT_Y": f"{EARLY_Y / ZT_Y * 100:.1f}"})
TSROWS = []
for k in CATS:
    a, b = ts0.get(k, 0), ts1.get(k, 0)
    TSROWS.append('<tr><td>%s</td><td class="hl">%d</td><td>%.1f%%</td><td>%d</td><td>%.1f%%</td></tr>'
                  % (k, a, a / ZT * 100, b, b / ZT_Y * 100))
V["TBL_TS"] = "\n".join(TSROWS)

# ---------------- 高位股明细 ----------------
def fmt_stock(c, pm):
    x = pm[c]
    return "%s（%d 板，%s，首封 %s，封单 %.2f 亿，成交 %.2f 亿）" % (
        x["n"], x.get("lbc", 1), x.get("hybk") or "—",
        str(x.get("fbt")).zfill(6)[:2] + ":" + str(x.get("fbt")).zfill(6)[2:4],
        x.get("fund", 0) / 1e8, x.get("amount", 0) / 1e8)


h5 = [c for c in p0 if p0[c].get("lbc") == 5]
h4 = [c for c in p0 if p0[c].get("lbc") == 4]
h3 = [c for c in p0 if p0[c].get("lbc") == 3]
V["MAXB_CN"] = str(len(h5))
V["MAXB_DETAIL"] = "；".join(fmt_stock(c, p0) for c in h5) or "—"
V["LAD4_DETAIL"] = "；".join(fmt_stock(c, p0) for c in h4) or "—"
V["LAD3_DETAIL"] = "；".join(fmt_stock(c, p0) for c in h3) or "—"
V["LAD4_BOARD"] = str(max((p0[c].get("lbc", 1) for c in h4), default=4))
h4y = [c for c in p1 if p1[c].get("lbc") == 4]
h3y = [c for c in p1 if p1[c].get("lbc") == 3]
pmap_pct = {r["code"]: r["pct"] for r in perf}
V["LAD4Y_N"] = str(len(h4y))
V["LAD4Y_NAMES"] = "、".join(p1[c]["n"] for c in h4y)
V["LAD4Y_PCT"] = "、".join("%s %+.2f%%" % (p1[c]["n"], pmap_pct.get(c, 0)) for c in h4y)
V["LAD3Y_N"] = str(len(h3y))
V["LAD3Y_NAMES"] = "、".join(p1[c]["n"] for c in h3y)
V["LAD3Y_PCT"] = "、".join("%s %+.2f%%" % (p1[c]["n"], pmap_pct.get(c, 0)) for c in h3y)
ADV_MAXB = sum(1 for c in h4y if c in p0)
V["MAXB_ADV_PCT"] = f"{ADV_MAXB / max(len(h4y), 1) * 100:.0f}"
LAD2_ADV = sum(1 for c in p1 if p1[c].get("lbc") == 2 and c in p0)
V["LAD2_ADV"] = str(LAD2_ADV)
V["LAD2_ADV_PCT"] = f"{LAD2_ADV / max(lad1.get(2, 0), 1) * 100:.1f}"
_one4 = None
for c in h4:
    hd = ths0[c].get("high_days") or ""
    if hd and hd != "首板" and "天4板" not in hd:
        _one4 = c
        break
_one4 = _one4 or (h4[0] if h4 else None)
V["LAD4_NAME_ONE"] = p0[_one4]["n"] if _one4 else "—"
V["LAD4_HIGH_ONE"] = ths0[_one4].get("high_days") if _one4 else "—"

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
    def cl(d):
        if abs(d) < 1e-9:
            return "mut"
        pos = d > 0
        if inv:
            pos = not pos
        return "up" if pos else "down"
    d = a - b
    SROWS.append('<tr><td>%s</td><td>%s%s</td><td>%s%s</td><td class="hl">%s%s</td><td class="%s">%s</td></tr>'
                 % (lbl, fmt % c, unit, fmt % b, unit, fmt % a, unit, cl(d),
                    (format(d, "+.1f") if isinstance(d, float) else f"{d:+d}") + unit))


row("涨停家数", ZT, ZT_Y, ZT_2, "%d", inv=False)
row("触及涨停家数", TOUCH, TOUCH_Y, TOUCH_2, "%d")
row("封板率", SEAL, SEAL_Y, SEAL_2, "%.1f", unit="%")
row("炸板家数", ZB, ZB_Y, S2["senti"][D2]["zb"], "%d", inv=True)
row("跌停家数（封死）", DT, DT_Y, DT_2, "%d", inv=True)
row("触及跌停家数", DTOUCH, DTOUCH_Y, DTOUCH_2, "%d", inv=True)
row("跌停封死率", DSEAL, DSEAL_Y, DSEAL_2, "%.1f", inv=True, unit="%")
row("连板股", LB, LB_Y, LB_2, "%d")
row("最高连板", MAXB, MAXB_Y, MAXB_2, "%d")
SROWS.append('<tr><td>涨停 / 跌停比</td><td>%.1f</td><td>—</td><td class="hl">%.1f</td><td class="mut">—</td></tr>'
             % (ZT_2 / max(DT_2, 1), ZT / max(DT, 1)))
V["TBL_SENTI"] = "\n".join(SROWS)

# ---------------- 口径缺陷 ----------------
rows_fresh = len(P1_FRESH)
uniq_fresh = len({x["c"] for x in P1_FRESH})
miss = [ths1[c]["name"] for c in ths1 if c not in {x["c"] for x in P1_FRESH}]
V.update({
    "D1POOL_ROWS": str(rows_fresh), "D1POOL_UNIQ": str(uniq_fresh),
    "D1POOL_DUP_N": str(rows_fresh - uniq_fresh), "D1POOL_MISS_N": str(len(miss)),
    "D1POOL_MISS_NAMES": "、".join(miss[:4]) + "等" if len(miss) > 4 else "、".join(miss),
    "D1POOL_DAY": str(len(p1)), "D1POOL_THS": str(len(ths1)),
    "ZT_EM": str(A0["em_ZT"].get("tc") or len(p0)),
})

# ---------------- SW ----------------
def sw(nm, key="pct"):
    return SW.get(nm, {}).get(key)


def swp(nm):
    v = sw(nm)
    return f"{v:+.2f}" if v is not None else "—"


def swf(nm):
    v = sw(nm, "flow")
    return f"{v / 1e4:.1f}" if v is not None else "—"


V.update({
    "SW_YY_PCT": swp("元件"), "SW_YY_UD": (SW.get("元件") or {}).get("updown", "—"),
    "SW_TX_PCT": swp("通信设备"), "SW_TX_UD": (SW.get("通信设备") or {}).get("updown", "—"),
    "SW_FTB_PCT": swp("覆铜板"), "SW_PCB_PCT": swp("PCB概念"), "SW_SEMI_PCT": swp("半导体"),
    "SW_DL_PCT": swp("电力"), "SW_MT_PCT": swp("煤炭开采"), "SW_BX_PCT": swp("保险Ⅱ"),
    "SW_PV_PCT": swp("光伏设备"), "SW_PVG_PCT": swp("光伏概念"), "SW_PV_FLOW": swf("光伏设备"),
})

# ---------------- JS ----------------
days = [f"{V['D2_FULL']}(周{md(D2)[1]})", f"{V['D1_FULL']}(周{md(D1)[1]})", f"{V['D0_FULL']}(周{md(D0)[1]})"]
JS = {
    "senti": {"days": [f"{md(D2)[0]} 周{md(D2)[1]}", f"{md(D1)[0]} 周{md(D1)[1]}", f"{md(D0)[0]} 周{md(D0)[1]}"],
              "zt": [ZT_2, ZT_Y, ZT], "zb": [S2["senti"][D2]["zb"], ZB_Y, ZB],
              "dt": [DT_2, DT_Y, DT], "seal": [round(SEAL_2, 1), round(SEAL_Y, 1), round(SEAL, 1)]},
    "amt": {"labels": [r[0] for r in sorted(yoy, key=lambda z: z[1])],
            "vals": [round(r[1], 1) for r in sorted(yoy, key=lambda z: z[1])]},
    "intra": dict(intra, range=[[intra["low"][i], intra["high"][i]] for i in range(len(intra["labels"]))]),
    "flow": {"days": [f"{md(D2)[0]}", f"{md(D1)[0]}", f"{md(D0)[0]}"],
             "tot": [round(S2["tot"]["today"]), round(S["tot"]["prev"]), round(S["tot"]["today"])],
             "sum": [round(SUM_2, 1), round(AMT_SUM_Y, 1), round(AMT_SUM, 1)],
             "share": [round(SUM_2 / S2["tot"]["today"] * 100, 2), round(AMT_SUM_Y / TOT_Y * 100, 2), round(AMT_SUM / TOT * 100, 2)]},
    "dt": {"labels": [f"{x['n']}" for x in dt_sorted[:8]],
           "vals": [round(x.get("amount", 0) / 1e8, 1) for x in dt_sorted[:8]],
           "colors": ["#b91c1c" if x["c"] in CALC_CODE else "#12805c" for x in dt_sorted[:8]]},
    "lad": {"cats": [f"{b} 板" for b in range(1, max(max(lad0), max(lad1)) + 1)],
            "d0": [lad0.get(b, 0) for b in range(1, max(max(lad0), max(lad1)) + 1)],
            "d1": [lad1.get(b, 0) for b in range(1, max(max(lad0), max(lad1)) + 1)],
            "d0lab": f"{md(D0)[0]}", "d1lab": f"{md(D1)[0]}"},
    "main": {"labels": [f"{c[0]}（连板 {C0[c[0]][1]}）" for c in CL]
                      + [f"「东方」字辈（连板 {sum(1 for c in DF if p0[c].get('lbc', 1) > 1)}）",
                         f"「羊」字辈（连板 {sum(1 for c in YANG if p0[c].get('lbc', 1) > 1)}）"],
             "d1": [C1[c[0]][0] for c in CL] + [0, 0],
             "d0": [C0[c[0]][0] for c in CL] + [len(DF), len(YANG)],
             "lb": [C0[c[0]][1] for c in CL] + [sum(1 for c in DF if p0[c].get("lbc", 1) > 1), sum(1 for c in YANG if p0[c].get("lbc", 1) > 1)],
             "d0lab": f"{md(D0)[0]}", "d1lab": f"{md(D1)[0]}"},
    "perf": {},
    "ts": {"cats": CATS, "d0": [ts0.get(k, 0) for k in CATS], "d1": [ts1.get(k, 0) for k in CATS],
           "d0lab": f"{md(D0)[0]}", "d1lab": f"{md(D1)[0]}"},
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
V["JS_ALL"] = json.dumps(JS, ensure_ascii=False)

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

# ---------------- 关键数字复核 ----------------
print("\n=== 复核 ===")
print(f"涨停 {ZT}(昨{ZT_Y}) 触及 {TOUCH}(昨{TOUCH_Y}) 封板率 {SEAL:.1f}(昨{SEAL_Y:.1f})")
print(f"跌停 {DT}(昨{DT_Y}) 触及跌停 {DTOUCH}(昨{DTOUCH_Y}) 封死率 {DSEAL:.1f}")
print(f"梯队 今{lad0} 昨{lad1}  连板 {LB}/{LB_Y} 最高 {MAXB}/{MAXB_Y}")
print(f"晋级 {len(AGAIN)}/{len(perf)} = {len(AGAIN)/len(perf)*100:.1f}%  首板组{len(G_SB)}({median(P_SB):+.2f}) 连板组{len(G_LB)}({median(P_LB):+.2f}) GAP {GAP:+.2f}")
print(f"涨停股成交 {AMT_SUM:.1f}(昨{AMT_SUM_Y:.1f}) 密度 {AMT_SUM/TOT*100:.2f}%(昨{AMT_SUM_Y/TOT_Y*100:.2f}%)")
print(f"跌停股成交 {DT_AMT:.1f} = {DT_AMT/AMT_SUM:.2f}倍  算力链{len(CALC)}只/{CALC_AMT:.1f}亿")
print(f"封单 {FUND:.2f}(昨{FUND_Y:.2f}) 中位 {median(fund0):.2f}/{median(fund1):.2f}")
print(f"炸板 {len(zb0)} 回封 {len(ZB_SEALED)} 成交 {ZB_AMT:.1f} = {ZB_AMT/AMT_SUM:.2f}倍")
print(f"行业 {len(hy0)}/{len(hy1)} 清零{len(zero)} 新增{len(new)} 闭合 {sum(hy0.values())}/{len(ths0)}")
print(f"名称簇 东方{len(DF)} 羊{len(YANG)} 并集{len(NM)} 成交{NM_AMT:.1f}亿 {NM_AMT/AMT_SUM*100:.1f}% 行业{NM_HY}")
print(f"光伏 {C0['光伏']} 昨{C1['光伏']}")
print(f"早盘封板 {EARLY}/{ZT}={EARLY/ZT*100:.1f}% 昨 {EARLY_Y}/{ZT_Y}={EARLY_Y/ZT_Y*100:.1f}%")
print(f"昨池重抓 行{rows_fresh} 唯一{uniq_fresh} 缺{len(miss)}")
print(f"昨涨停→今跌停 {len(ZT2DT)}")
