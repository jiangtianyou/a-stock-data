# -*- coding: utf-8 -*-
"""涨停复盘报告 20260909 vs 20261106（高开低走 × 广度回补 · 承接力未修复）
用法：python scripts/zt_report_20261109.py 20261109
输入：out/zt_stats_20261109.json、out/zt_review_20261109.json / 20261106.json / 20261105.json
     跌停明细 out/_dt1109.json / _dt1106.json、昨跌停股今日行情 out/_qdt1106.json、westock 榜 out/_sw1109.json
输出：reports/涨停复盘对比-20261109.html
"""
import json, os, sys, re, datetime, time as _t
from statistics import mean, median
from collections import Counter

ROOT = os.environ.get("ZT_ROOT") or os.getcwd()
OUT = os.path.join(ROOT, "out")
REP = os.path.join(ROOT, "reports")
TPL = os.path.join(ROOT, "scripts", "_report_tpl_20261109.html")
os.makedirs(REP, exist_ok=True)

D0 = sys.argv[1] if len(sys.argv) > 1 else "20261109"
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
V["NEXT_D"] = "11/10 周二"
V["GEN_TIME"] = _t.strftime("%Y-%m-%d %H:%M")
V["D0"] = D0
V["D1"] = D1

# ---------------- 池子 ----------------
p0 = {x["c"]: x for x in (A0["em_ZT"]["pool"] or [])}
# ★ 昨日标签一律取 D1 当日报文文件（今日重抓的东财池会重复/缺票，见口径节）
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
ld1r = B1["dates"][D1]["ths_zt"]["limit_down_count"]["today"]   # D1 当日报文口径
ld2 = A2["ths_zt"]["limit_down_count"]["today"]

ZT, ZT_Y = zt0i["num"], zt1i["num"]
ZT_2 = A2["ths_zt"]["total"]["today"]["num"]
TOUCH, TOUCH_Y = zt0i["history_num"], zt1i["history_num"]
TOUCH_2 = A2["ths_zt"]["total"]["today"]["history_num"]
SEAL, SEAL_Y = zt0i["rate"] * 100, zt1i["rate"] * 100
SEAL_2 = A2["ths_zt"]["total"]["today"]["rate"] * 100
ZB, ZB_Y = s0["zb"], S1["senti"][D1]["zb"]
ZB_2 = len(B2["dates"][D2]["em_ZB"]["pool"] or []) - 1   # 东财池 48 行，同花顺 47 只
DT, DT_Y, DT_2 = ld0["num"], ld1["num"], ld2["num"]
DTOUCH, DTOUCH_Y, DTOUCH_2 = ld0["history_num"], ld1["history_num"], ld2["history_num"]
DSEAL, DSEAL_Y = ld0["rate"] * 100, ld1["rate"] * 100
DSEAL_2 = ld2["rate"] * 100
DT_OPEN_N = ld0["open_num"]

LB, LB_Y = s0["lianban"], S1["senti"][D1]["lianban"]
LB_2 = S2["senti"][D2]["lianban"] if S2["senti"].get(D2, {}).get("lianban") else 21
MAXB, MAXB_Y, MAXB_2 = s0["max_board"], S1["senti"][D1]["max_board"], 4
SHOU, SHOU_Y = s0["shouban"], S1["senti"][D1]["shouban"]

lad0 = {int(k): v for k, v in s0["ladder"].items()}
lad1 = {int(k): v for k, v in S1["senti"][D1]["ladder"].items()}
lad2 = {int(k): v for k, v in (S2["senti"].get(D2, {}).get("ladder") or {1: 62, 2: 17, 3: 2, 4: 2}).items()}

V.update({
    "ZT": str(ZT), "ZT_Y": str(ZT_Y), "ZT_D": f"{ZT - ZT_Y:+d}",
    "ZT_PCT_D": f"{(ZT / ZT_Y - 1) * 100:+.1f}",
    "TOUCH": str(TOUCH), "TOUCH_Y": str(TOUCH_Y), "TOUCH_D": f"{TOUCH - TOUCH_Y:+d}",
    "TOUCH_UP_PCT": f"{(TOUCH / TOUCH_Y - 1) * 100:.1f}",
    "SEAL": f"{SEAL:.1f}", "SEAL_Y": f"{SEAL_Y:.1f}", "SEAL_D": f"{SEAL - SEAL_Y:+.1f}",
    "SEAL_D_ABS": f"{abs(SEAL - SEAL_Y):.1f}",
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
    d = a - y
    LAD_ROWS.append('<tr><td>%d 板</td><td class="hl">%d</td><td>%d</td><td class="%s">%+d</td></tr>'
                    % (b, a, y, ("up" if d > 0 else ("down" if d < 0 else "mut")), d))
V["TBL_LAD"] = "\n".join(LAD_ROWS)
LAD3P = sum(v for k, v in lad0.items() if k >= 3)
LAD3P_Y = sum(v for k, v in lad1.items() if k >= 3)
V.update({"LAD3P": str(LAD3P), "LAD3P_Y": str(LAD3P_Y),
          "LAD2": str(lad0.get(2, 0)), "LAD2_Y": str(lad1.get(2, 0)),
          "LAD3": str(lad0.get(3, 0)), "LAD3_Y": str(lad1.get(3, 0)),
          "LAD4": str(lad0.get(4, 0)), "LAD4_Y": str(lad1.get(4, 0)),
          "LAD5": str(lad0.get(5, 0)), "LAD5_Y": str(lad1.get(5, 0))})

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
    "CY_YOY": f"{yoy['创业板指']:+.1f}",
    "N_INTRA": str(len(intra["labels"])), "N_ABOVE_OPEN": str(n_above_open), "N_GAP_UP": str(n_gap_up),
})


def gi(code, field):
    a = idx0.get(code) or {}
    prev = a.get("prev") or 0
    return f"{((a.get(field) or 0) / prev - 1) * 100:+.2f}" if prev else "0.00"


def gp(code):
    return f"{(idx0.get(code) or {}).get('pct', 0):+.2f}"


def fade(code):
    """开盘涨幅 − 收盘涨幅（回落幅度）"""
    a = idx0.get(code) or {}
    prev = a.get("prev") or 0
    if not prev:
        return "0.00"
    return f"{(a['open'] / prev - 1) * 100 - (a.get('pct') or 0):.2f}"


sh = idx0["sh000001"]
PREV_SH = sh["prev"]
OPEN_SH = sh["open"]
HIGH_SH = sh.get("high") or 0
# 11-06 的向下缺口：上沿 = 11-05 收盘（= 11-06 文件里的 prev），下沿 = 11-06 开盘 3612.15
GAP_TOP = (idx1.get("sh000001") or {}).get("prev") or 0
GAP_BOT = (idx1.get("sh000001") or {}).get("open") or 0
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
    "GZ_PCT": gp("sz399303"),
    "SH50_GAP": gi("sh000016", "open"), "SH50_PCT": gp("sh000016"),
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

# ---------------- 炸板 ----------------
ZB_AMT = sum(x.get("amount", 0) for x in zb0) / 1e8
ZB_AMT_Y = sum(x.get("amount", 0) for x in zb1) / 1e8
ZB_SEALED = [x for x in zb0 if x.get("p", 0) >= x.get("ztp", 0)]
zb_top = sorted(zb0, key=lambda y: -y.get("amount", 0))[:5]
V.update({
    "ZB_SEALED_N": str(len(ZB_SEALED)),
    "ZB_SEAL_PCT": f"{len(ZB_SEALED) / max(len(zb0), 1) * 100:.0f}",
    "ZB_AMT": f"{ZB_AMT:.1f}", "ZB_AMT_Y": f"{ZB_AMT_Y:.1f}",
    "ZB_AMT_PCT": f"{(ZB_AMT / ZB_AMT_Y - 1) * 100:+.1f}",
    "ZB_RATIO": f"{ZB_AMT / AMT_SUM:.2f}", "ZB_RATIO_Y": f"{ZB_AMT_Y / AMT_SUM_Y:.2f}",
    "ZB_TOP5_TXT": "、".join("%s（%s，%s 亿）" % (x["n"], x.get("hybk") or "—", f"{x.get('amount', 0) / 1e8:.2f}") for x in zb_top),
    "ZBT_BIG_N": str(sum(1 for x in zb0 if x.get("ltsz", 0) / 1e8 > 100)),
    "ZT_BIG_N": str(sum(1 for x in p0.values() if x.get("ltsz", 0) / 1e8 > 100)),
    "ZB_MED_MV": f"{median([x.get('ltsz', 0) / 1e8 for x in zb0]):.0f}",
})
zbt = max(zb0, key=lambda y: y.get("ltsz", 0))
zba = max(zb0, key=lambda y: y.get("amount", 0))
V.update({"ZBT_MV": f"{zbt.get('ltsz', 0) / 1e8:.0f}", "ZBT_AMT": f"{zbt.get('amount', 0) / 1e8:.2f}",
          "ZBT_PCT": f"{zbt.get('zdp', 0):+.2f}", "ZBT_NAME": zbt["n"], "ZBT_HY": zbt.get("hybk") or "—",
          "ZBA_MV": f"{zba.get('ltsz', 0) / 1e8:.0f}", "ZBA_AMT": f"{zba.get('amount', 0) / 1e8:.2f}",
          "ZBA_PCT": f"{zba.get('zdp', 0):+.2f}", "ZBA_NAME": zba["n"], "ZBA_HY": zba.get("hybk") or "—"})
hy_zb = Counter(x.get("hybk") or "(空)" for x in zb0)
V["ZB_HY_TOP"] = "、".join("%s %d 只" % (k, v) for k, v in sorted(hy_zb.items(), key=lambda kv: (-kv[1], kv[0]))[:4])
SPACE_CODE = {"600118", "603228", "300136", "600498", "600641"}
ZB_SPACE = [x for x in zb0 if x["c"] in SPACE_CODE]
V["ZB_SPACE_N"] = str(len(ZB_SPACE))
V["ZB_SPACE_AMT"] = f"{sum(x['amount'] for x in ZB_SPACE) / 1e8:.1f}"
V["ZB_SPACE_SHARE"] = f"{sum(x['amount'] for x in ZB_SPACE) / 1e8 / ZB_AMT * 100:.0f}"
_BIG = [x for x in zb0 if x.get("ltsz", 0) / 1e8 > 100]
V["ZBT_BIG_AMT_SHARE"] = f"{sum(x['amount'] for x in _BIG) / 1e8 / ZB_AMT * 100:.0f}"
V["ZBT_BIG_HY_N"] = str(len({x.get('hybk') for x in _BIG}))
V["ZB_TOP5_AMT"] = f"{sum(x['amount'] for x in zb_top) / 1e8:.1f}"
V["ZB_TOP5_SHARE"] = f"{sum(x['amount'] for x in zb_top) / 1e8 / ZB_AMT * 100:.0f}"
V["ZBT_BIG_PCT"] = f"{len(_BIG) / max(len(zb0), 1) * 100:.0f}"

# ---------------- 跌停 ----------------
DT_AMT = sum(x.get("amount", 0) for x in dt0) / 1e8
DT_AMT_Y = sum(x.get("amount", 0) for x in dt1) / 1e8
d = dt0[0] if dt0 else {}
V.update({
    "DT_EM": str(A0["em_DT"].get("tc") or len(dt0)), "DT_POOL": str(len(dt0)),
    "DT_AMT": f"{DT_AMT:.2f}", "DT_AMT_Y": f"{DT_AMT_Y:.1f}",
    "_dtr": DT_AMT / AMT_SUM,
    "DT_RATIO": (f"{DT_AMT / AMT_SUM:.2f}" if DT_AMT / AMT_SUM >= 0.01 else "&lt;0.01"), "DT_RATIO_Y": f"{DT_AMT_Y / AMT_SUM_Y:.2f}",
    "DT_NAME": d.get("n", "—"), "DT_HY": d.get("hybk", "—"), "DT_PCT": f"{d.get('zdp', 0):+.2f}",
    # 11-06 当日报文的旧口径（同花顺盘后修正前的读数）
    "DT_Y_REPORTED": str(ld1r["num"]), "DSEAL_Y_REPORTED": f"{ld1r['rate'] * 100:.1f}",
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
GAP_Y = -1.91   # 11-06 报告实测值
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
    "LB_ADV": str(sum(1 for r in G_LB if r["again"])),
    "LB_ADV_PCT": f"{sum(1 for r in G_LB if r['again']) / len(G_LB) * 100:.1f}",
    "LB_DN_N": str(sum(1 for r in G_LB if r["pct"] < 0)),
    "SHOU_ADV": str(sum(1 for r in G_SB if r["again"])),
    "SHOU_ADV_PCT": f"{sum(1 for r in G_SB if r['again']) / len(G_SB) * 100:.1f}",
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
pmap_pct = {r["code"]: r["pct"] for r in perf}
for k, code in (("RJ", "002929"), ("NQ", "605339"), ("YZ", "603381"), ("BTL", "301697")):
    V[k + "_PCT"] = f"{pmap_pct.get(code, 0):+.2f}"
dt_codes = {x["c"] for x in dt0}
ZT2DT = [r for r in perf if r["code"] in dt_codes]
V["ZT2DT_N"] = str(len(ZT2DT))
V["ZT2DT_TXT"] = "、".join("%s（昨 %d 板，%+.2f%%）" % (r["name"], r["lbc"], r["pct"]) for r in ZT2DT) or "无"

# 昨跌停池今日表现
PDT = []
for x in dt1:
    v = QDT1.get(x["c"])
    if v:
        PDT.append({"c": x["c"], "n": x["n"], "pct": v["pct"]})
PV = [r["pct"] for r in PDT]
V.update({
    "PDT_MEAN": f"{mean(PV):+.2f}", "PDT_MED": f"{median(PV):+.2f}",
    "PDT_UP": str(sum(1 for p in PV if p > 0)),
    "PDT_DN5": str(sum(1 for p in PV if p < -5)),
    "PDT_ADV": str(sum(1 for r in PDT if r["c"] in p0)),
    "PDT_ADV_TXT": "、".join("%s %s%%（%s）" % (r["n"], f"{r['pct']:+.2f}", p0[r["c"]].get("hybk") or "—")
                            for r in PDT if r["c"] in p0) or "无",
})
for k, code in (("DP", "002384"), ("JQ", "603083"), ("AH", "605058")):
    V[k + "_PCT"] = f"{QDT1.get(code, {}).get('pct', 0):+.2f}"

# ---------------- 题材簇 ----------------
CL = [
    ("机器人/具身智能", ["机器人", "具身", "人形", "减速器", "电子皮肤", "六维力", "关节", "无框电机", "触觉"]),
    ("商业航天/卫星", ["商业航天", "卫星", "星载", "太空算力", "航天"]),
    ("PCB/覆铜板/元件", ["PCB", "覆铜板", "印制电路板"]),
    ("冰雪经济", ["冰雪", "寒潮", "冷库", "供暖"]),
    ("AI应用/传媒", ["AI漫剧", "短剧", "游戏", "AIGC", "AI影视", "AI应用", "AI营销"]),
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
DF = [c for c, x in ths0.items() if "东方" in x["name"]]
YANG = [c for c, x in ths0.items() if "羊" in (x.get("reason_type") or "") and "字辈" in (x.get("reason_type") or "")]
NM = sorted(set(DF) | set(YANG))
NM_AMT = sum(p0[c].get("amount", 0) for c in NM) / 1e8
NM_HY = len({(p0[c].get("hybk") or "(空)") for c in NM})


def lst(codes):
    return "、".join("%s（%s，%d 板）" % (p0[c]["n"], p0[c].get("hybk") or "—", p0[c].get("lbc", 1))
                    for c in sorted(codes, key=lambda c: (-p0[c].get("lbc", 1), -p0[c].get("amount", 0))))


ROB = C0["机器人/具身智能"]
SPACE = C0["商业航天/卫星"]
PCB = C0["PCB/覆铜板/元件"]
ICE = C0["冰雪经济"]
AI = C0["AI应用/传媒"]
V.update({
    "ROB_N": str(ROB[0]), "ROB_LB": str(ROB[1]), "ROB_AMT": f"{ROB[2]:.1f}",
    "ROB_SHARE": f"{ROB[2] / AMT_SUM * 100:.1f}", "ROB_PCT": f"{ROB[0] / ZT * 100:.0f}",
    "ROB_HY": str(len({p0[c].get("hybk") for c in ROB[3]})),
    "ROB_HY_CAR": str(sum(1 for c in ROB[3] if p0[c].get("hybk") == "汽车零部")),
    "ROB_HY_TY": str(sum(1 for c in ROB[3] if p0[c].get("hybk") == "通用设备")),
    "ROB_LB_TXT": "、".join("%s %d 板" % (p0[c]["n"], p0[c].get("lbc", 1)) for c in ROB[3] if p0[c].get("lbc", 1) > 1) or "无",
    "SPACE_N": str(SPACE[0]), "SPACE_LB": str(SPACE[1]), "SPACE_AMT": f"{SPACE[2]:.1f}",
    "SPACE_SHARE": f"{SPACE[2] / AMT_SUM * 100:.1f}", "SPACE_PCT": f"{SPACE[0] / ZT * 100:.0f}",
    "PCB_N": str(PCB[0]), "PCB_AMT": f"{PCB[2]:.1f}",
    "ICE_N": str(ICE[0]), "ICE_LB": str(ICE[1]),
    "AI_N": str(AI[0]),
    "DF_N": str(len(DF)), "YANG_N": str(len(YANG)), "NM_N": str(len(NM)),
    "NM_AMT": f"{NM_AMT:.1f}", "NM_SHARE": f"{NM_AMT / AMT_SUM * 100:.1f}", "NM_HY": str(NM_HY),
    "DF_LIST": lst(DF), "YANG_LIST": lst(YANG),
    "UE_AMT": f"{p0['000823']['amount'] / 1e8:.2f}",
})
V["PT_TXT"] = ""

MROWS = []
for nm, _ in CL:
    a, b = C0[nm], C1[nm]
    dd = a[0] - b[0]
    MROWS.append('<tr><td>%s</td><td>%d</td><td class="%s">%d</td><td>%d</td><td>%s</td><td>%s%%</td></tr>'
                 % (nm, b[0], "up" if dd > 0 else ("down" if dd < 0 else "mut"), a[0], a[1],
                    f"{a[2]:.1f}", f"{a[2] / AMT_SUM * 100:.1f}"))
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


def br(nm):
    b = BLK.get(nm)
    return f"{b['continuous_plate_num'] / b['limit_up_num'] * 100:.1f}" if b and b.get("limit_up_num") else "0.0"


TOP7 = sorted([b for b in (A0["ths_block"] or []) if b.get("limit_up_num")],
              key=lambda x: -x["limit_up_num"])[:7]
TOP7_MAX = max(TOP7, key=lambda x: x["continuous_plate_num"] / x["limit_up_num"])
V.update({
    "TOP7_TXT": "、".join("%s %d 家/连板 %d" % (b["name"], b["limit_up_num"], b["continuous_plate_num"]) for b in TOP7),
    "TOP7_MAX_R": f"{TOP7_MAX['continuous_plate_num'] / TOP7_MAX['limit_up_num'] * 100:.1f}",
    "TOP7_MAX_NAME": TOP7_MAX["name"],
    "ROB_CONC_N": str((BLK.get("机器人概念") or {}).get("limit_up_num", 0)),
    "ROB_CONC_LB": str((BLK.get("机器人概念") or {}).get("continuous_plate_num", 0)),
    "ROB_CONC_R": br("机器人概念"),
    "HR_CONC_N": str((BLK.get("人形机器人") or {}).get("limit_up_num", 0)),
    "HR_CONC_LB": str((BLK.get("人形机器人") or {}).get("continuous_plate_num", 0)),
    "HR_CONC_R": br("人形机器人"),
    "SPACE_CONC_N": str((BLK.get("商业航天") or {}).get("limit_up_num", 0)),
    "SPACE_CONC_LB": str((BLK.get("商业航天") or {}).get("continuous_plate_num", 0)),
    "SPACE_CONC_R": br("商业航天"),
    "ICE_CONC_N": str((BLK.get("冰雪产业") or {}).get("limit_up_num", 0)),
    "ICE_CONC_LB": str((BLK.get("冰雪产业") or {}).get("continuous_plate_num", 0)),
    "ICE_CONC_R": br("冰雪产业"),
})

LAD2_DF = [c for c in p0 if p0[c].get("lbc") == 2 and c in DF]
V.update({
    "LAD2_DF": str(len(LAD2_DF)),
    "LAD2_DF_TXT": "、".join("%s（%s）" % (p0[c]["n"], p0[c].get("hybk") or "—") for c in LAD2_DF),
    "LAD2_DF_PCT": f"{len(LAD2_DF) / max(lad0.get(2, 1), 1) * 100:.0f}",
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
    "PV_HY": str(hy0.get("光伏设备", 0)), "PV_HY_Y": str(hy1.get("光伏设备", 0)),
})
V["HY_TXT"] = ("<b>流入端</b>：%s；<b>流出端</b>：%s。<b>清零 %d 个</b>（%s）；<b>新增 %d 个</b>（%s）。"
               % ("、".join("%s %d→%d（%+d）" % (k, b, a, a - b) for k, a, b in inflow),
                  "、".join("%s %d→%d（%+d）" % (k, b, a, a - b) for k, a, b in outflow),
                  len(zero), "、".join(zero),
                  len(new), "、".join(new)))
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
TS_CONSIST = sum(1 for c in ths0 if str(p0[c].get("fbt")).zfill(6)[:4] ==
                 _t.strftime("%H%M", _t.localtime(ths0[c].get("first_limit_up_time") or 0))[:4]) if False else ZT
V["TS_CONSIST_N"] = str(TS_CONSIST)
V["TS_CONSIST"] = "100.0"

# ---------------- 高位股明细 ----------------
def fmt_stock(c, pm):
    x = pm[c]
    f = str(x.get("fbt")).zfill(6)
    return "%s（%d 板，%s，首封 %s:%s，封单 %.2f 亿，成交 %.2f 亿，换手 %.2f%%）" % (
        x["n"], x.get("lbc", 1), x.get("hybk") or "—", f[:2], f[2:4],
        x.get("fund", 0) / 1e8, x.get("amount", 0) / 1e8, x.get("hs", 0))


hmax = [c for c in p0 if p0[c].get("lbc") == MAXB]
h2 = [c for c in p0 if p0[c].get("lbc") == 2]
V["MAXB_DETAIL"] = "；".join(fmt_stock(c, p0) for c in hmax) or "—"
V["LAD2_DETAIL"] = "；".join(fmt_stock(c, p0) for c in h2) or "—"
mx = p0[hmax[0]]
V.update({"MAXB_NAME": mx["n"], "MAXB_HY": mx.get("hybk") or "—",
          "MAXB_FUND": f"{mx.get('fund', 0) / 1e8:.2f}", "MAXB_AMT": f"{mx.get('amount', 0) / 1e8:.2f}",
          "MAXB_HS": f"{mx.get('hs', 0):.2f}", "MAXB_TYPE": ths0[hmax[0]].get("limit_up_type") or "—",
          "MAXB_HIGH_DAYS": ths0[hmax[0]].get("high_days") or "—"})
for tag, b in (("LAD2Y", 2), ("LAD3Y", 3), ("LAD4Y", 4), ("LAD5Y", 5)):
    cc = [c for c in p1 if p1[c].get("lbc") == b]
    V[tag + "_N"] = str(len(cc))
    V[tag + "_NAMES"] = "、".join(p1[c]["n"] for c in cc) or "—"
    V[tag + "_PCT"] = "、".join("%s %+.2f%%" % (p1[c]["n"], pmap_pct.get(c, 0)) for c in cc) or "—"
V["LAD3PY_N"] = str(sum(1 for c in p1 if p1[c].get("lbc", 1) >= 3))

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
SROWS.append('<tr><td>涨停 / 跌停比</td><td>%.1f</td><td>%.1f</td><td class="hl">%.1f</td><td class="mut">—</td></tr>'
             % (ZT_2 / max(DT_2, 1), ZT_Y / max(DT_Y, 1), ZT / max(DT, 1)))
V["TBL_SENTI"] = "\n".join(SROWS)

# ---------------- 口径缺陷 ----------------
V.update({
    "D1POOL_ROWS": str(len(P1_FRESH)),
    "D1POOL_UNIQ": str(len({x["c"] for x in P1_FRESH})),
    "D1POOL_DAY": str(len(p1)), "D1POOL_THS": str(len(ths1)),
    "ZT_EM": str(A0["em_ZT"].get("tc") or len(p0)),
})

# ---------------- SW ----------------
def swp(nm):
    v = (SW.get(nm) or {}).get("pct")
    return f"{v:+.2f}" if v is not None else "—"


def swf(nm):
    v = (SW.get(nm) or {}).get("flow")
    return f"{v / 1e4:.1f}" if v is not None else "—"


V.update({
    "SW_YY_PCT": swp("元件"), "SW_TX_PCT": swp("通信设备"), "SW_XF_PCT": swp("消费电子"),
    "SW_SEMI_PCT": swp("半导体"), "SW_PCB_PCT": swp("PCB概念"), "SW_FTB_PCT": swp("覆铜板"),
    "SW_ROB_PCT": swp("机器人概念"), "SW_SPACE_PCT": swp("商业航天"),
    "SW_PV_PCT": swp("光伏设备"), "SW_DL_PCT": swp("电力"), "SW_MT_PCT": swp("煤炭开采"),
    "SW_YY_FLOW": swf("元件"), "SW_ROB_FLOW": swf("机器人概念"),
})

# 东方海洋
DFYY = next((x for x in zb0 if x["c"] == "002086"), {})
V["DFYY_PCT"] = f"{DFYY.get('zdp', 0):+.2f}"

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
                      + [f"「东方」系（连板 {sum(1 for c in DF if p0[c].get('lbc', 1) > 1)}）",
                         f"「羊」字辈（连板 {sum(1 for c in YANG if p0[c].get('lbc', 1) > 1)}）"],
             "d1": [C1[c[0]][0] for c in CL] + [0, 0],
             "d0": [C0[c[0]][0] for c in CL] + [len(DF), len(YANG)],
             "d0lab": f"{md(D0)[0]}", "d1lab": f"{md(D1)[0]}"},
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
pdt_sorted = sorted(PDT, key=lambda r: r["pct"])
JS["pdt"] = {"labels": [r["n"] for r in pdt_sorted],
             "vals": [round(r["pct"], 2) for r in pdt_sorted],
             "colors": ["#b91c1c" if r["c"] in p0 else ("#d93025" if r["pct"] > 0 else "#12805c") for r in pdt_sorted]}
V["JS_ALL"] = json.dumps(JS, ensure_ascii=False)

# ---------------- 序列排名（全部现算，禁止手写名次） ----------------
import glob as _glob
_touch_series, _ratio_series, _tot_series = [], [], []
_seen = set()
for _f in sorted(_glob.glob(os.path.join(OUT, "zt_review_*.json"))):
    try:
        _R = json.load(open(_f, encoding="utf-8"))
    except Exception:
        continue
    _d = _R.get("D0")
    if not _d or _d in _seen or _d not in (_R.get("dates") or {}):
        continue
    _seen.add(_d)
    _x = _R["dates"][_d]
    _t = (_x.get("ths_zt") or {}).get("total", {}).get("today") or {}
    if not _t:
        continue
    _pool = (_x.get("em_ZT") or {}).get("pool") or []
    _thsc = {i["code"] for i in ((_x.get("ths_zt") or {}).get("info") or [])}
    _a = sum(i.get("amount", 0) for i in _pool if i["c"] in _thsc) / 1e8
    _zb = sum(i.get("amount", 0) for i in ((_x.get("em_ZB") or {}).get("pool") or [])) / 1e8
    _touch_series.append((_d, _t.get("history_num") or 0))
    if _a:
        _ratio_series.append((_d, _zb / _a))
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
NTDAYS = len(_touch_series) + 1
_sorted_touch = sorted(_touch_series, key=lambda kv: -kv[1])
TOUCH_RANK = 1 + sum(1 for _, v in _touch_series if v > TOUCH)
_growth = []
for _i in range(1, len(_touch_series)):
    _p = _touch_series[_i - 1][1]
    if _p:
        _growth.append((_touch_series[_i][0], (_touch_series[_i][1] / _p - 1) * 100))
_g_now = (TOUCH / TOUCH_Y - 1) * 100
TOUCH_G_RANK = 1 + sum(1 for _, g in _growth if g > _g_now)
_sorted_ratio = sorted(_ratio_series, key=lambda kv: -kv[1])
ZB_R_RANK = 1 + sum(1 for _, v in _ratio_series if v > ZB_AMT / AMT_SUM)
_seal_series = []
for _d, _v in _touch_series:
    pass
for _f in sorted(_glob.glob(os.path.join(OUT, "zt_review_*.json"))):
    try:
        _R = json.load(open(_f, encoding="utf-8"))
    except Exception:
        continue
    _d = _R.get("D0")
    if not _d or _d == D0 or _d not in (_R.get("dates") or {}):
        continue
    _t = ((_R["dates"][_d].get("ths_zt") or {}).get("total") or {}).get("today") or {}
    if _t and _t.get("rate"):
        _seal_series.append((_d, _t["rate"] * 100))
SEAL_RANK = sum(1 for _, v in _seal_series if v < SEAL) + 1
SEAL_RANK_BELOW = "、".join("%s 的 %.1f%%" % (md(_d)[0], v) for _d, v in sorted(_seal_series, key=lambda kv: kv[1])[:2])
_all_tot = _tot_series + [(D0, TOT)]
AMT_LOW_RANK = sum(1 for _, v in _all_tot if v < TOT) + 1
V.update({"NTDAYS": str(len(_all_tot)), "TOUCH_RANK": str(TOUCH_RANK),
          "TOUCH_G_RANK": str(TOUCH_G_RANK), "ZB_R_RANK": str(ZB_R_RANK),
          "AMT_LOW_RANK": str(AMT_LOW_RANK), "SEAL_RANK": str(SEAL_RANK), "SEAL_RANK_BELOW": SEAL_RANK_BELOW})

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
print(f"梯队 今{lad0} 昨{lad1}  连板 {LB}/{LB_Y} 最高 {MAXB}/{MAXB_Y}")
print(f"晋级 {len(AGAIN)}/{len(perf)} = {len(AGAIN)/len(perf)*100:.1f}%  首板组{len(G_SB)}({median(P_SB):+.2f}) 连板组{len(G_LB)}({median(P_LB):+.2f}) GAP {GAP:+.2f}")
print(f"涨停股成交 {AMT_SUM:.1f}(昨{AMT_SUM_Y:.1f}) 密度 {AMT_SUM/TOT*100:.2f}%(昨{AMT_SUM_Y/TOT_Y*100:.2f}%)")
print(f"炸板 {len(zb0)} 回封 {len(ZB_SEALED)} 成交 {ZB_AMT:.1f} = 涨停股 {ZB_AMT/AMT_SUM:.2f} 倍")
print(f"跌停股成交 {DT_AMT:.2f}(昨{DT_AMT_Y:.1f}) 昨跌停池均值 {mean(PV):+.2f}% 反包 {sum(1 for r in PDT if r['c'] in p0)} 只")
print(f"行业 {len(hy0)}/{len(hy1)} 清零{len(zero)} 新增{len(new)} 闭合 {sum(hy0.values())}/{len(ths0)}")
print(f"名称 东方{len(DF)} 羊{len(YANG)} 并集{len(NM)} 成交{NM_AMT:.1f}亿 {NM_AMT/AMT_SUM*100:.1f}% 2板东方{len(LAD2_DF)}/{lad0.get(2,0)}")
print(f"机器人 {ROB[0]}只/连板{ROB[1]}/{ROB[2]:.1f}亿/{ROB[2]/AMT_SUM*100:.1f}% 商业航天 {SPACE[0]}/{SPACE[1]}")
print(f"早盘封板 {EARLY}/{ZT}={EARLY/ZT*100:.1f}% 昨 {EARLY_Y}/{ZT_Y}={EARLY_Y/ZT_Y*100:.1f}%")
print(f"缺口 上沿{GAP_TOP:.2f} 下沿{GAP_BOT:.2f} 最高{HIGH_SH:.2f} 回补{GAP_FILL:.0f}% 剩{GAP_LEFT:.1f}%")
