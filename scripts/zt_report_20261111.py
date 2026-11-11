# -*- coding: utf-8 -*-
"""涨停复盘 20261111 vs 20261110 —— 钱厚面窄塔矮 · AI 算力硬件链中大票爆发
用法：python scripts/zt_report_20261111.py 20261111
"""
import json, os, sys, re, datetime, time as _t
from statistics import mean, median
from collections import Counter

ROOT = os.environ.get("ZT_ROOT") or os.getcwd()
OUT, REP = os.path.join(ROOT, "out"), os.path.join(ROOT, "reports")
TPL = os.path.join(ROOT, "scripts", "_report_tpl_20261111.html")
os.makedirs(REP, exist_ok=True)

D0 = sys.argv[1] if len(sys.argv) > 1 else "20261111"
S = json.load(open(os.path.join(OUT, f"zt_stats_{D0}.json"), encoding="utf-8"))
D0, D1, D2 = S["D0"], S["D1"], S["D2"]
B = json.load(open(os.path.join(OUT, f"zt_review_{D0}.json"), encoding="utf-8"))
B1 = json.load(open(os.path.join(OUT, f"zt_review_{D1}.json"), encoding="utf-8"))
B2 = json.load(open(os.path.join(OUT, f"zt_review_{D2}.json"), encoding="utf-8"))
A0, A1, A2 = B["dates"][D0], B["dates"][D1], B2["dates"][D2]

WEEK = {0: "一", 1: "二", 2: "三", 3: "四", 4: "五", 5: "六", 6: "日"}
def md(ds):
    d = datetime.date(int(ds[:4]), int(ds[4:6]), int(ds[6:8]))
    return f"{d.month}/{d.day:02d}", WEEK[d.weekday()]

V = {}
for tag, ds in [("D0", D0), ("D1", D1), ("D2", D2)]:
    lab, wk = md(ds)
    V[tag + "_LABEL"], V[tag + "_WEEK"] = lab, "周" + wk
    V[tag + "_FULL"] = f"{ds[:4]}-{ds[4:6]}-{ds[6:8]}"
V["D0"], V["D1"], V["D2"] = D0, D1, D2
V["NEXT_D"] = "11/12 周四"
V["GEN_TIME"] = _t.strftime("%Y-%m-%d %H:%M")

# ---------- 池子 ----------
p0 = {x["c"]: x for x in (A0["em_ZT"]["pool"] or [])}
p1 = {x["c"]: x for x in (B1["dates"][D1]["em_ZT"]["pool"] or [])}
p2 = {x["c"]: x for x in (B2["dates"][D2]["em_ZT"]["pool"] or [])}
th0 = {x["code"]: x for x in A0["ths_zt"]["info"]}
th1 = {x["code"]: x for x in A1["ths_zt"]["info"]}
zb0 = A0["em_ZB"]["pool"] or []
zb1 = B1["dates"][D1]["em_ZB"]["pool"] or []
zb2 = B2["dates"][D2]["em_ZB"]["pool"] or []

# 沪深口径（同花顺）为家数基准；成交额用同花顺名单内的东财字段求合计
def amt_of(pool, ths):
    return sum((pool[c].get("amount") or 0) for c in ths if c in pool) / 1e8
AMT_SUM, AMT_SUM_Y, AMT_SUM_2 = amt_of(p0, th0), amt_of(p1, th1), amt_of(p2, th2 := {x["code"]: x for x in A2["ths_zt"]["info"]})
FUND, FUND_Y = sum((p0[c].get("fund") or 0) for c in th0) / 1e8, sum((p1[c].get("fund") or 0) for c in th1) / 1e8
MED_AMT = median([p0[c]["amount"] for c in th0]) / 1e8
MED_AMT_Y = median([p1[c]["amount"] for c in th1]) / 1e8
FUND_MED = median([p0[c]["fund"] for c in th0]) / 1e8
FUND_MED_Y = median([p1[c]["fund"] for c in th1]) / 1e8

# ---------- 情绪 ----------
zt0, zt1, zt2 = (A0["ths_zt"]["total"]["today"], A1["ths_zt"]["total"]["today"],
                 A2["ths_zt"]["total"]["today"])
ld0, ld1, ld2 = (A0["ths_zt"]["limit_down_count"]["today"], A1["ths_zt"]["limit_down_count"]["today"],
                 A2["ths_zt"]["limit_down_count"]["today"])
ZT, ZT_Y, ZT_2 = zt0["num"], zt1["num"], zt2["num"]
TOUCH, TOUCH_Y, TOUCH_2 = zt0["history_num"], zt1["history_num"], zt2["history_num"]
SEAL, SEAL_Y, SEAL_2 = zt0["rate"] * 100, zt1["rate"] * 100, zt2["rate"] * 100
ZB, ZB_Y, ZB_2 = len(zb0), len(zb1), len(zb2)
ZB_SEALED = sum(1 for z in zb0 if z["p"] >= z["ztp"] - 1e-6)
ZB_SEALED_Y = sum(1 for z in zb1 if z["p"] >= z["ztp"] - 1e-6)
DT, DT_Y, DT_2 = ld0["num"], ld1["num"], ld2["num"]
DTOUCH, DTOUCH_Y, DTOUCH_2 = ld0["history_num"], ld1["history_num"], ld2["history_num"]
DSEAL, DSEAL_Y, DSEAL_2 = ld0["rate"] * 100, ld1["rate"] * 100, ld2["rate"] * 100
DT_OPEN_N = ld0["open_num"]

s0, s1, s2 = S["senti"][D0], S["senti"][D1], S["senti"][D2]
LB, LB_Y, LB_2 = s0["lianban"], s1["lianban"], s2["lianban"]
MAXB, MAXB_Y, MAXB_2 = s0["max_board"], s1["max_board"], s2["max_board"]
SHOU, SHOU_Y = s0["shouban"], s1["shouban"]
lad0 = {int(k): v for k, v in s0["ladder"].items()}
lad1 = {int(k): v for k, v in s1["ladder"].items()}
# D2 的 zt_stats 文件中 senti[D2] 为空（analyze 未落该日的分日统计），改为从原始池子现算
_th2 = {x["code"] for x in A2["ths_zt"]["info"]}
_l2 = [p2[c]["lbc"] for c in _th2 if c in p2 and (p2[c].get("lbc") or 0) >= 1]
lad2 = dict(Counter(_l2))
LB_2 = sum(1 for x in _l2 if x >= 2)
MAXB_2 = max(_l2) if _l2 else 0

# ---------- 指数 ----------
NAME = {"sh000001": "上证指数", "sz399001": "深证成指", "sz399006": "创业板指", "sh000688": "科创50",
        "bj899050": "北证50", "sh000300": "沪深300", "sh000852": "中证1000", "sh000905": "中证500",
        "sz399303": "国证2000", "sh000016": "上证50", "sz399005": "中小100"}
idx0, idx1 = B["indexes"], B1["indexes"]
AMT = (idx0["sh000001"]["amount_wan"] + idx0["sz399001"]["amount_wan"]) / 1e4
AMT_Y = (idx1["sh000001"]["amount_wan"] + idx1["sz399001"]["amount_wan"]) / 1e4
rows_idx, yoy = [], []
n_up = n_dn = n_amt_up = 0
n_below_open = 0
for k, nm in NAME.items():
    a, b = idx0.get(k) or {}, idx1.get(k) or {}
    if not a:
        continue
    p0v, p1v = a.get("pct") or 0, b.get("pct") or 0
    m0, m1 = a.get("amount_wan") or 0, b.get("amount_wan") or 0
    ch = (m0 / m1 - 1) * 100 if m1 else 0
    yoy.append((nm, ch, p0v))
    n_up += p0v > 0
    n_dn += p0v < 0
    n_amt_up += ch > 0
    n_below_open += int(a["price"] < a["open"])
    rows_idx.append('<tr><td>%s</td><td class="%s">%+.2f%%</td><td class="%s">%+.2f%%</td><td>%s</td><td class="%s">%+.1f%%</td>'
                    '<td class="%s">%+.2f%%</td></tr>'
                    % (nm, "up" if p0v > 0 else ("down" if p0v < 0 else "mut"), p0v,
                       "up" if p1v > 0 else ("down" if p1v < 0 else "mut"), p1v,
                       f"{m0 / 1e4:,.0f}", "up" if ch > 0 else "down", ch,
                       "up" if (a["price"] / a["prev"] - 1) * 100 > (a["open"] / a["prev"] - 1) * 100 else "down",
                       (a["price"] / a["open"] - 1) * 100))
yoy_s = sorted(yoy, key=lambda t: t[1])
V["TBL_IDX"] = "\n".join(rows_idx)
V.update({
    "N_UP": str(n_up), "N_DN": str(n_dn), "N_AMT_UP": str(n_amt_up), "N_IDX": str(len(yoy)),
    "N_BELOW_OPEN": str(n_below_open),
    "AMT": f"{AMT:,.0f}", "AMT_Y": f"{AMT_Y:,.0f}",
    "AMT_D": f"{(AMT - AMT_Y):+,.0f}", "AMT_PCT": f"{(AMT / AMT_Y - 1) * 100:+.1f}",
    "YOY_MAX_NAME": yoy_s[-1][0], "YOY_MAX": f"{yoy_s[-1][1]:+.1f}%",
    "YOY_MIN_NAME": yoy_s[0][0], "YOY_MIN": f"{yoy_s[0][1]:+.1f}%",
})
def pct_of(k):
    return (idx0[k]["amount_wan"] / idx1[k]["amount_wan"] - 1) * 100
V.update({
    "HS300_YOY": f"{pct_of('sh000300'):+.1f}", "KC_YOY": f"{pct_of('sh000688'):+.1f}",
    "CY_YOY": f"{pct_of('sz399006'):+.1f}", "ZZ_YOY": f"{pct_of('sh000852'):+.1f}",
    "SH50_YOY": f"{pct_of('sh000016'):+.1f}", "GZ_YOY": f"{pct_of('sz399303'):+.1f}",
    "SH_YOY": f"{pct_of('sh000001'):+.1f}",
})
for k, tag in [("sh000001", "SH"), ("sz399006", "CY"), ("sh000688", "KC"),
               ("sz399303", "GZ"), ("sh000016", "SH50")]:
    a = idx0[k]; prev = a["prev"]
    V[tag + "_GAP"] = f"{(a['open'] / prev - 1) * 100:+.2f}"
    V[tag + "_PCT"] = f"{a['pct']:+.2f}"
    V[tag + "_LOW"] = f"{(a['low'] / prev - 1) * 100:+.2f}"
    V[tag + "_HIGH"] = f"{(a['high'] / prev - 1) * 100:+.2f}"
    V[tag + "_FADE"] = f"{(a['price'] / a['high'] - 1) * 100:.2f}"

# ---------- 缺口 ----------
# 缺口（11-06 向下跳空）：上沿 = 11-05 收盘 = 11-06 快照的 prev；下沿 = 11-06 开盘
_GAPD = "20261106"
_BG = json.load(open(os.path.join(OUT, f"zt_review_{_GAPD}.json"), encoding="utf-8"))
g_hi = _BG["indexes"]["sh000001"]["prev"]
g_lo = _BG["indexes"]["sh000001"]["open"]
g_size = g_hi - g_lo
sh = idx0["sh000001"]
V.update({
    "GAP_HI": f"{g_hi:.2f}", "GAP_LO": f"{g_lo:.2f}", "GAP_SIZE": f"{g_size:.2f}",
    "GAP_HIGH_REST": f"{g_hi - sh['high']:.2f}",
    "GAP_CLOSE_REST": f"{g_hi - sh['price']:.2f}",
    "GAP_CLOSE_FILL": f"{(sh['price'] - g_lo) / g_size * 100:.1f}",
    "GAP_HIGH_FILL": f"{(sh['high'] - g_lo) / g_size * 100:.1f}",
    "GAP_CLOSE_PCT": f"{(g_hi - sh['price']) / g_size * 100:.1f}",
})

# ---------- 核心数值 ----------
V.update({
    "ZT": str(ZT), "ZT_Y": str(ZT_Y), "ZT_2": str(ZT_2),
    "ZT_D": f"{ZT - ZT_Y:+d}", "ZT_PCT_D": f"{(ZT / ZT_Y - 1) * 100:+.1f}",
    "TOUCH": str(TOUCH), "TOUCH_Y": str(TOUCH_Y), "TOUCH_2": str(TOUCH_2),
    "TOUCH_D": f"{TOUCH - TOUCH_Y:+d}", "TOUCH_PCT_D": f"{(TOUCH / TOUCH_Y - 1) * 100:+.1f}",
    "SEAL": f"{SEAL:.1f}", "SEAL_Y": f"{SEAL_Y:.1f}", "SEAL_2": f"{SEAL_2:.1f}",
    "SEAL_DP": f"{SEAL - SEAL_Y:+.1f}", "SEAL_D_ABS": f"{abs(SEAL - SEAL_Y):.1f}",
    "ZB": str(ZB), "ZB_Y": str(ZB_Y), "ZB_2": str(ZB_2),
    "ZB_EM": str(len(zb0)), "ZB_SEALED": str(ZB_SEALED), "ZB_SEALED_Y": str(ZB_SEALED_Y),
    "DT": str(DT), "DT_Y": str(DT_Y), "DT_2": str(DT_2), "DT_D": f"{DT - DT_Y:+d}",
    "DTOUCH": str(DTOUCH), "DTOUCH_Y": str(DTOUCH_Y), "DTOUCH_2": str(DTOUCH_2),
    "DTOUCH_D": f"{DTOUCH - DTOUCH_Y:+d}",
    "DSEAL": f"{DSEAL:.1f}", "DSEAL_Y": f"{DSEAL_Y:.1f}", "DSEAL_2": f"{DSEAL_2:.1f}",
    "DT_OPEN_N": str(DT_OPEN_N),
    "SEAL_FAIL": f"{round((TOUCH - ZT) / TOUCH * 100, 1):.1f}",
    "SEAL_FAIL_Y": f"{round((TOUCH_Y - ZT_Y) / TOUCH_Y * 100, 1):.1f}",
    "LB": str(LB), "LB_Y": str(LB_Y), "LB_2": str(LB_2), "LB_D": f"{LB - LB_Y:+d}",
    "LB_PCT": f"{LB / ZT * 100:.1f}", "LB_PCT_Y": f"{LB_Y / ZT_Y * 100:.1f}",
    "MAXB": str(MAXB), "MAXB_Y": str(MAXB_Y), "MAXB_2": str(MAXB_2),
    "MAXB_D": f"{MAXB - MAXB_Y:+d}",
    "SHOU": str(SHOU), "SHOU_Y": str(SHOU_Y),
    "SHOU_PCT": f"{SHOU / ZT * 100:.1f}", "SHOU_PCT_Y": f"{SHOU_Y / ZT_Y * 100:.1f}",
    "AMT_SUM": f"{AMT_SUM:.1f}", "AMT_SUM_Y": f"{AMT_SUM_Y:.1f}", "AMT_SUM_2": f"{AMT_SUM_2:.1f}",
    "AMT_SUM_PCT": f"{(AMT_SUM / AMT_SUM_Y - 1) * 100:+.1f}",
    "SHARE": f"{AMT_SUM / AMT * 100:.2f}", "SHARE_Y": f"{AMT_SUM_Y / AMT_Y * 100:.2f}",
    "FUND": f"{FUND:.1f}", "FUND_Y": f"{FUND_Y:.1f}", "FUND_PCT": f"{(FUND / FUND_Y - 1) * 100:+.1f}",
    "FUND_MED": f"{FUND_MED:.2f}", "FUND_MED_Y": f"{FUND_MED_Y:.2f}",
    "MED_AMT": f"{MED_AMT:.2f}", "MED_AMT_Y": f"{MED_AMT_Y:.2f}",
    "MED_AMT_PCT": f"{(MED_AMT / MED_AMT_Y - 1) * 100:+.1f}",
    "ZT_EM": str(len(p0)), "ZT_THS": str(len(th0)),
    "NTDAYS": str(len([f for f in os.listdir(OUT) if re.match(r"zt_stats_\d{8}\.json$", f)])),
})
em_only = [c for c in p0 if c not in th0]
V["BJ_CODE"] = "、".join(f"{c} {p0[c]['n']}" for c in em_only) or "无"
V["BJ_N"] = str(len(em_only))

# ---------- 梯队 ----------
LADMAX = max(max(lad0), max(lad1), max(lad2))
LAD_ROWS = []
for b in range(1, LADMAX + 1):
    a, y = lad0.get(b, 0), lad1.get(b, 0)
    dd = a - y
    LAD_ROWS.append('<tr><td>%d 板</td><td class="hl">%d</td><td>%d</td><td class="%s">%s</td></tr>'
                    % (b, a, y, "up" if dd > 0 else ("down" if dd < 0 else "mut"),
                       "0" if dd == 0 else "%+d" % dd))
V["TBL_LAD"] = "\n".join(LAD_ROWS)
V["LAD_VAC"] = "、".join("%d 板" % b for b in range(5, MAXB_Y + 1) if lad0.get(b, 0) == 0) or "无"
LAD3P, LAD3P_Y = sum(v for k, v in lad0.items() if k >= 3), sum(v for k, v in lad1.items() if k >= 3)
V.update({"LAD3P": str(LAD3P), "LAD3P_Y": str(LAD3P_Y),
          "LAD2": str(lad0.get(2, 0)), "LAD2_Y": str(lad1.get(2, 0)),
          "LAD3": str(lad0.get(3, 0)), "LAD3_Y": str(lad1.get(3, 0)),
          "LAD4": str(lad0.get(4, 0)), "LAD4_Y": str(lad1.get(4, 0)),
          "LAD7": str(lad0.get(7, 0)), "LAD7_Y": str(lad1.get(7, 0))})

# ---------- 分线 ----------
KW_HW = ["光模块", "CPO", "光通信", "光纤", "光芯片", "空芯光纤", "MPO", "光模块胶", "铜缆",
         "PCB", "覆铜板", "算力", "数据中心", "液冷", "服务器", "交换机", "HBM", "6G"]
KW_ROB = ["机器人", "具身智能", "减速器", "丝杠", "关节", "电子皮肤", "灵巧手"]
KW_MED = ["AI漫剧", "短剧", "AI影视", "AI游戏", "游戏", "IP", "影视", "剧集", "传媒", "AI应用"]

def chain(kws, pool, th):
    hit = [c for c in th if any(k in (th[c].get("reason_type") or "") for k in kws) and c in pool]
    return hit

def chain_stats(kws, pool, th, base_amt):
    hit = chain(kws, pool, th)
    a = sum((pool[c].get("amount") or 0) for c in hit) / 1e8
    f = sum((pool[c].get("fund") or 0) for c in hit) / 1e8
    lb = sum(1 for c in hit if (pool[c].get("lbc") or 0) >= 2)
    big = sum(1 for c in hit if (pool[c].get("ltsz") or 0) > 1e10)
    mvh = median([(pool[c].get("ltsz") or 0) for c in hit]) / 1e8
    return dict(n=len(hit), amt=a, fund=f, lb=lb, big=big, mv=mvh,
                share=a / base_amt * 100, fshare=f / FUND * 100, hy=len({pool[c].get("hybk") for c in hit}))

BASE0, BASE1 = AMT_SUM, AMT_SUM_Y
hw0, hw1 = chain_stats(KW_HW, p0, th0, BASE0), chain_stats(KW_HW, p1, th1, BASE1)
rb0, rb1 = chain_stats(KW_ROB, p0, th0, BASE0), chain_stats(KW_ROB, p1, th1, BASE1)
md0, md1 = chain_stats(KW_MED, p0, th0, BASE0), chain_stats(KW_MED, p1, th1, BASE1)
V.update({
    "AI_N": str(hw0["n"]), "AI_N_Y": str(hw1["n"]),
    "AI_AMT": f"{hw0['amt']:.1f}", "AI_AMT_Y": f"{hw1['amt']:.1f}",
    "AI_AMT_X": f"{hw0['amt'] / hw1['amt']:.1f}",
    "AI_SHARE": f"{hw0['share']:.1f}", "AI_SHARE_Y": f"{hw1['share']:.1f}",
    "AI_FSHARE": f"{hw0['fshare']:.1f}", "AI_FSHARE_Y": f"{hw1['fshare']:.1f}",
    "AI_LB": str(hw0["lb"]), "AI_LB_Y": str(hw1["lb"]),
    "AI_LB_PCT": f"{hw0['lb'] / hw0['n'] * 100:.1f}", "AI_LB_PCT_Y": f"{hw1['lb'] / hw1['n'] * 100:.1f}",
    "AI_BIG": str(hw0["big"]), "AI_BIG_Y": str(hw1["big"]),
    "AI_MV": f"{hw0['mv']:.0f}", "AI_MV_Y": f"{hw1['mv']:.0f}", "AI_HY": str(hw0["hy"]),
    "ROB_N": str(rb0["n"]), "ROB_N_Y": str(rb1["n"]),
    "ROB_AMT": f"{rb0['amt']:.1f}", "ROB_AMT_Y": f"{rb1['amt']:.1f}",
    "ROB_AMT_PCT": f"{(rb0['amt'] / rb1['amt'] - 1) * 100:+.1f}",
    "ROB_SHARE": f"{rb0['share']:.1f}", "ROB_SHARE_Y": f"{rb1['share']:.1f}",
    "ROB_LB": str(rb0["lb"]), "ROB_LB_Y": str(rb1["lb"]),
    "ROB_LB_PCT": f"{rb0['lb'] / rb0['n'] * 100:.1f}", "ROB_LB_PCT_Y": f"{rb1['lb'] / rb1['n'] * 100:.1f}",
    "ROB_HY": str(rb0["hy"]),
    "MEDIA_N": str(md0["n"]), "MEDIA_N_Y": str(md1["n"]),
    "MEDIA_AMT": f"{md0['amt']:.1f}", "MEDIA_AMT_Y": f"{md1['amt']:.1f}",
    "MEDIA_AMT_PCT": f"{(md0['amt'] / md1['amt'] - 1) * 100:+.1f}",
    "MEDIA_SHARE": f"{md0['share']:.1f}", "MEDIA_SHARE_Y": f"{md1['share']:.1f}",
    "MEDIA_LB": str(md0["lb"]), "MEDIA_LB_Y": str(md1["lb"]),
    "MEDIA_LB_PCT": f"{md0['lb'] / md0['n'] * 100:.1f}",
})

# ---------- 市值分层 ----------
BINS = [(0, 3e9, "&lt;30亿"), (3e9, 5e9, "30–50亿"), (5e9, 1e10, "50–100亿"),
        (1e10, 3e10, "100–300亿"), (3e10, 9e18, "&gt;300亿")]
mv_rows, mv_chart = [], {"cat": [], "a": [], "b": []}
for lo, hi, nm in BINS:
    s0_ = [p0[c] for c in th0 if lo <= (p0[c].get("ltsz") or 0) < hi]
    s1_ = [p1[c] for c in th1 if lo <= (p1[c].get("ltsz") or 0) < hi]
    a_amt, b_amt = sum(x["amount"] for x in s0_) / 1e8, sum(x["amount"] for x in s1_) / 1e8
    _dd = len(s0_) - len(s1_)
    mv_rows.append('<tr><td>%s</td><td class="hl">%d</td><td>%d</td><td class="%s">%s</td>'
                   '<td>%.1f</td><td>%.1f</td><td class="%s">%+.1f</td></tr>'
                   % (nm, len(s0_), len(s1_), "up" if _dd > 0 else ("down" if _dd < 0 else "mut"),
                      "0" if _dd == 0 else "%+d" % _dd, a_amt, b_amt,
                      "up" if a_amt > b_amt else "down", a_amt - b_amt))
    mv_chart["cat"].append(nm); mv_chart["a"].append(round(a_amt, 1)); mv_chart["b"].append(round(b_amt, 1))
V["TBL_MV"] = "\n".join(mv_rows)
big_a = sum(x["amount"] for x in p0.values() if (x.get("ltsz") or 0) > 3e10) / 1e8
big_b = sum(x["amount"] for x in p1.values() if (x.get("ltsz") or 0) > 3e10) / 1e8
V.update({
    "MV_B5": str(len([c for c in th0 if (p0[c].get("ltsz") or 0) > 3e10])),
    "MV_B5_Y": str(len([c for c in th1 if (p1[c].get("ltsz") or 0) > 3e10])),
    "BIG_AMT": f"{big_a:.1f}", "BIG_AMT_Y": f"{big_b:.1f}",
    "BIG_SHARE": f"{big_a / AMT_SUM * 100:.1f}",
    "BIG_SHARE_Y": f"{big_b / AMT_SUM_Y * 100:.1f}",
    "MV_SMALL": str(len([c for c in th0 if (p0[c].get("ltsz") or 0) < 1e10])),
    "MV_SMALL_PCT": f"{len([c for c in th0 if (p0[c].get('ltsz') or 0) < 1e10]) / len(th0) * 100:.1f}",
    "MV_SMALL_AMT_SHARE": f"{sum(x['amount'] for c, x in p0.items() if c in th0 and (x.get('ltsz') or 0) < 1e10) / 1e8 / AMT_SUM * 100:.1f}",
})

# ---------- 封板时段 ----------
ts_lab = ["竞价/秒板", "开盘半小时", "上午盘中", "午后盘中", "尾盘"]
def slot_of(t):
    if not t: return "未知"
    s = str(int(t)).zfill(6); mins = int(s[:2]) * 60 + int(s[2:4])
    if mins <= 9 * 60 + 25: return "竞价/秒板"
    if mins <= 10 * 60: return "开盘半小时"
    if mins <= 11 * 60 + 30: return "上午盘中"
    if mins <= 14 * 60 + 30: return "午后盘中"
    return "尾盘"
c_ts0, c_ts1 = Counter(slot_of(z.get("fbt")) for z in p0.values()), Counter(slot_of(z.get("fbt")) for z in p1.values())
ts_rows, ts_chart = [], {"cat": ts_lab, "a": [], "b": []}
for lab in ts_lab:
    a, b = c_ts0.get(lab, 0), c_ts1.get(lab, 0)
    dd = a - b
    ts_rows.append('<tr><td>%s</td><td class="hl">%d</td><td>%d</td><td class="%s">%s</td></tr>'
                   % (lab, a, b, "up" if dd > 0 else ("down" if dd < 0 else "mut"),
                      "0" if dd == 0 else "%+d" % dd))
    ts_chart["a"].append(a); ts_chart["b"].append(b)
V["TBL_TS"] = "\n".join(ts_rows)
EARLY0 = c_ts0.get("竞价/秒板", 0) + c_ts0.get("开盘半小时", 0)
EARLY1 = c_ts1.get("竞价/秒板", 0) + c_ts1.get("开盘半小时", 0)
V.update({
    "TS_JJ": str(c_ts0.get("竞价/秒板", 0)), "TS_JJ_Y": str(c_ts1.get("竞价/秒板", 0)),
    "TS_KP": str(c_ts0.get("开盘半小时", 0)), "TS_KP_Y": str(c_ts1.get("开盘半小时", 0)),
    "TS_SW": str(c_ts0.get("上午盘中", 0)), "TS_SW_Y": str(c_ts1.get("上午盘中", 0)),
    "TS_WH": str(c_ts0.get("午后盘中", 0)), "TS_WH_Y": str(c_ts1.get("午后盘中", 0)),
    "TS_WP": str(c_ts0.get("尾盘", 0)), "TS_WP_Y": str(c_ts1.get("尾盘", 0)),
    "TS_EARLY": str(EARLY0), "TS_EARLY_Y": str(EARLY1),
    "TS_EARLY_PCT": f"{EARLY0 / ZT * 100:.0f}", "TS_EARLY_PCT_Y": f"{EARLY1 / ZT_Y * 100:.0f}",
})
YIZI = Counter(x.get("limit_up_type") for x in th0.values())
YIZI_Y = Counter(x.get("limit_up_type") for x in th1.values())
V.update({
    "YIZI": str(YIZI.get("一字板", 0)), "YIZI_Y": str(YIZI_Y.get("一字板", 0)),
    "TZI": str(YIZI.get("T字板", 0)), "TZI_Y": str(YIZI_Y.get("T字板", 0)),
    "TURN": str(YIZI.get("换手板", 0)), "TURN_Y": str(YIZI_Y.get("换手板", 0)),
    "TURN_PCT": f"{YIZI.get('换手板', 0) / len(th0) * 100:.0f}",
})

# ---------- 昨日涨停今日表现 ----------
Y = {v["code"]: v for v in B["yesterday_zt_today"].values()}
perf = S["perf"]                      # list of dicts: code/name/lbc/hybk/reason/pct/again
chg = [x["pct"] for x in perf]
adv = [x for x in perf if x["again"]]
sb_ = [x for x in perf if x["lbc"] == 1]
lb_ = [x for x in perf if x["lbc"] >= 2]
V.update({
    "ADV_N": str(len(adv)), "ADV_TOT": str(len(perf)), "ADV_RATE": f"{len(adv) / len(perf) * 100:.1f}",
    "PERF_MEAN": f"{mean(chg):+.2f}", "PERF_MED": f"{median(chg):+.2f}",
    "PERF_MAX": f"{max(chg):+.2f}", "PERF_MIN": f"{min(chg):+.2f}",
    "PERF_DN_N": str(sum(1 for c in chg if c < 0)),
    "PERF_DN_PCT": f"{sum(1 for c in chg if c < 0) / len(chg) * 100:.1f}",
    "PERF_DN5_N": str(sum(1 for c in chg if c <= -5)),
    "SB_N": str(len(sb_)), "SB_MED": f"{median([x['pct'] for x in sb_]):+.2f}",
    "SB_ADV_PCT": f"{sum(1 for x in sb_ if x['again']) / len(sb_) * 100:.1f}",
    "LB_MED": f"{median([x['pct'] for x in lb_]):+.2f}",
    "LB_N": str(len(lb_)),
    "LB_ADV_PCT": f"{sum(1 for x in lb_ if x['again']) / len(lb_) * 100:.1f}",
    "GAP": f"{median([x['pct'] for x in sb_]) - median([x['pct'] for x in lb_]):+.2f}",
    "GAP_ABS": f"{abs(median([x['pct'] for x in sb_]) - median([x['pct'] for x in lb_])):.2f}",
})
# 昨日（11-10 对 11-09）的晋级率与 GAP，从 D1 的 stats 文件现算
_S1 = json.load(open(os.path.join(OUT, f"zt_stats_{D1}.json"), encoding="utf-8"))
_p1 = _S1["perf"]
_s1b = [x for x in _p1 if x["lbc"] == 1]
_l1b = [x for x in _p1 if x["lbc"] >= 2]
V.update({
    "ADV_RATE_Y": f"{sum(1 for x in _p1 if x['again']) / len(_p1) * 100:.1f}",
    "SB_N_Y": str(len(_s1b)), "LB_N_Y": str(len(_l1b)), "ADV_TOT_Y": str(len(_p1)),
    "GAP_Y": f"{median([x['pct'] for x in _s1b]) - median([x['pct'] for x in _l1b]):+.2f}",
    "GAP_Y_ABS": f"{abs(median([x['pct'] for x in _s1b]) - median([x['pct'] for x in _l1b])):.2f}",
    "SB_MED_Y": f"{median([x['pct'] for x in _s1b]):+.2f}",
    "LB_MED_Y": f"{median([x['pct'] for x in _l1b]):+.2f}",
    "SB_ADV_Y": f"{sum(1 for x in _s1b if x['again']) / len(_s1b) * 100:.1f}",
    "LB_ADV_Y": f"{sum(1 for x in _l1b if x['again']) / len(_l1b) * 100:.1f}",
})
# 最强最弱
srt = sorted([(x["pct"], x["name"], x["hybk"]) for x in perf], reverse=True)
V.update({
    "PERF_TOP_TXT": "、".join(f"{n} {v:+.2f}%" for v, n, _ in srt[:3]),
    "PERF_BOT_TXT": "、".join(f"{n} {v:+.2f}%" for v, n, _ in srt[-3:][::-1]),
})
# 分线表现
def line_perf(kws):
    hit = [x for x in perf if any(k in (x.get("reason") or "") for k in kws)]
    cs = [x["pct"] for x in hit]
    return len(cs), mean(cs), median(cs), sum(1 for x in cs if x >= 9.9)
lp_hw = line_perf(KW_HW); lp_rb = line_perf(KW_ROB); lp_md = line_perf(KW_MED)
V.update({
    "LPHW_N": str(lp_hw[0]), "LPHW_MEAN": f"{lp_hw[1]:+.2f}", "LPHW_MED": f"{lp_hw[2]:+.2f}", "LPHW_ZT": str(lp_hw[3]),
    "LPRB_N": str(lp_rb[0]), "LPRB_MEAN": f"{lp_rb[1]:+.2f}", "LPRB_MED": f"{lp_rb[2]:+.2f}", "LPRB_ZT": str(lp_rb[3]),
    "LPMD_N": str(lp_md[0]), "LPMD_MEAN": f"{lp_md[1]:+.2f}", "LPMD_MED": f"{lp_md[2]:+.2f}", "LPMD_ZT": str(lp_md[3]),
})

# ---------- 连板股 / 最高板 ----------
lb_pool = sorted([c for c in th0 if (p0[c].get("lbc") or 0) >= 2], key=lambda c: -(p0[c]["lbc"]))
TBL_LB = []
for c in lb_pool:
    x = p0[c]; i = th0[c]
    TBL_LB.append('<tr><td>%d 板</td><td>%s</td><td class="hl">%s</td><td>%s</td><td>%s</td><td>%.2f</td><td>%.2f</td></tr>'
                  % (x["lbc"], c, i["name"], x.get("hybk") or "—", i.get("high_days") or "—",
                     (x.get("fund") or 0) / 1e8, (x.get("amount") or 0) / 1e8))
V["TBL_LIANBAN"] = "\n".join(TBL_LB)
top4 = [c for c in lb_pool if p0[c]["lbc"] == 4]
V["MAXB_NAMES"] = "、".join(f"{th0[c]['name']}（{th0[c]['high_days']}）" for c in top4)
lad3_names = [f"{th0[c]['name']}" for c in lb_pool if p0[c]["lbc"] == 3]
V["LAD3_NAMES"] = "、".join(lad3_names)
df = [th0[c]["name"] for c in th0 if "东方" in th0[c]["name"]]
V["DF_N"] = str(len(df)); V["DF_LIST"] = "、".join(df)
df_amt = sum(p0[c]["amount"] for c in th0 if "东方" in th0[c]["name"]) / 1e8
V["DF_AMT"] = f"{df_amt:.1f}"; V["DF_SHARE"] = f"{df_amt / AMT_SUM * 100:.1f}"
V["DF_LAD"] = "、".join(f"{th0[c]['name']} {p0[c]['lbc']} 板" for c in lb_pool if "东方" in th0[c]["name"])
yang = [th0[c]["name"] for c in th0 if "字辈" in (th0[c].get("reason_type") or "")]
V["YANG_N"] = str(len(yang)); V["YANG_LIST"] = "、".join(yang) if yang else "无"

# 昨日连板 → 今日断板
lb1 = [c for c in th1 if (p1[c].get("lbc") or 0) >= 2]
lb1_adv = [c for c in lb1 if c in p0]
V.update({
    "LBY": str(len(lb1)), "LBY_ADV": str(len(lb1_adv)), "LBY_ADV_PCT": f"{len(lb1_adv) / len(lb1) * 100:.1f}",
    "LBY_FAIL": str(len(lb1) - len(lb1_adv)),
})
max7 = [c for c in lb1 if (p1[c].get("lbc") or 0) >= 5]
V["MAX7_TXT"] = "、".join(f"{th1[c]['name']}（{p1[c]['lbc']} 板→今 {Y[c]['pct']:+.2f}%）" for c in max7 if c in Y)

# ---------- 炸板池 ----------
zb_sorted = sorted(zb0, key=lambda z: -(z.get("amount") or 0))
TBL_ZB = []
for z in zb_sorted[:10]:
    t = str(int(z["fbt"])).zfill(6)
    TBL_ZB.append('<tr><td>%s</td><td class="hl">%s</td><td>%s</td><td class="down">%+.2f%%</td><td>%.2f</td><td>%s:%s</td></tr>'
                  % (z["c"], z["n"], z.get("hybk") or "—", z["zdp"], (z.get("amount") or 0) / 1e8, t[:2], t[2:4]))
V["TBL_ZB"] = "\n".join(TBL_ZB)
V["ZB_AMT"] = f"{sum((z.get('amount') or 0) for z in zb0) / 1e8:.1f}"
V["ZB_AMT_Y"] = f"{sum((z.get('amount') or 0) for z in zb1) / 1e8:.1f}"
V["ZB_RATIO"] = f"{sum((z.get('amount') or 0) for z in zb0) / 1e8 / AMT_SUM:.2f}"
V["ZB_RATIO_Y"] = f"{sum((z.get('amount') or 0) for z in zb1) / 1e8 / AMT_SUM_Y:.2f}"
V["ZBA_NAME"] = zb_sorted[0]["n"] if zb_sorted else "—"
V["ZBA_HY"] = zb_sorted[0].get("hybk") or "—" if zb_sorted else "—"
V["ZBA_AMT"] = f"{(zb_sorted[0].get('amount') or 0) / 1e8:.2f}" if zb_sorted else "0"
V["ZB_MV_MED"] = f"{median([z.get('ltsz') or 0 for z in zb0]) / 1e8:.0f}"
def _mins(t):
    s_ = str(int(t)).zfill(6)
    return int(s_[:2]) * 60 + int(s_[2:4])
V["ZB_MORNING"] = str(sum(1 for z in zb0 if (z.get("fbt") or 0) and _mins(z["fbt"]) <= 11 * 60 + 30))
V["ZB_AFTERNOON"] = str(sum(1 for z in zb0 if (z.get("fbt") or 0) and _mins(z["fbt"]) > 11 * 60 + 30))

# ---------- 概念板块榜 ----------
bl = A0["ths_block"] or []
bl1 = A1["ths_block"] or []
TBL_MAIN = []
for b in bl[:10]:
    r = b["continuous_plate_num"] / b["limit_up_num"] * 100 if b["limit_up_num"] else 0
    TBL_MAIN.append('<tr><td>%s</td><td class="hl">%d</td><td>%d</td><td class="%s">%.1f%%</td><td class="%s">%+.2f%%</td></tr>'
                    % (b["name"], b["limit_up_num"], b["continuous_plate_num"],
                       "up" if r >= 40 else "down", r,
                       "up" if b["change"] > 0 else "down", b["change"]))
V["TBL_MAIN"] = "\n".join(TBL_MAIN)
top_r = max((b["continuous_plate_num"] / b["limit_up_num"] * 100, b["name"]) for b in bl[:7] if b["limit_up_num"])
V["MAIN_MAX_R"] = f"{top_r[0]:.1f}"; V["MAIN_MAX_NAME"] = top_r[1]
V["MAIN_TOP1"] = bl[0]["name"] if bl else "—"
V["MAIN_TOP1_N"] = str(bl[0]["limit_up_num"]) if bl else "0"
V["MAIN_TOP1_LB"] = str(bl[0]["continuous_plate_num"]) if bl else "0"
# 芯片概念（连板占比最低的大簇）
chip = next((b for b in bl if b["name"] == "芯片概念"), None)
V["CHIP_N"] = str(chip["limit_up_num"]) if chip else "0"
V["CHIP_LB"] = str(chip["continuous_plate_num"]) if chip else "0"
V["CHIP_R"] = f"{chip['continuous_plate_num'] / chip['limit_up_num'] * 100:.1f}" if chip else "0"
# 行业迁移
c0 = {}
c1 = {}
for c in th0:
    c0.setdefault(p0[c].get("hybk"), set()).add(c)
for c in th1:
    c1.setdefault(p1[c].get("hybk"), set()).add(c)
mv = [(k, len(c0.get(k, ())), len(c1.get(k, ()))) for k in set(c0) | set(c1)]
mv.sort(key=lambda t: -((t[1] + t[2]) + abs(t[1] - t[2]) * 2))
TBL_HY = []
for k, a, b in mv[:12]:
    inter = len(c0.get(k, set()) & c1.get(k, set()))
    dd = a - b
    TBL_HY.append('<tr><td>%s</td><td class="hl">%d</td><td>%d</td><td class="%s">%+d</td><td>%d</td></tr>'
                  % (k or "—", a, b, "up" if dd > 0 else ("down" if dd < 0 else "mut"), dd, inter))
V["TBL_HY"] = "\n".join(TBL_HY)
_inc = sorted([(a - b, k, a) for k, a, b in mv if a - b > 0], reverse=True)[:3]
_dec = sorted([(b - a, k, a) for k, a, b in mv if b - a > 0], reverse=True)[:1]
V["HY_INC_TXT"] = "、".join(f"{k} +{d}" for d, k, _ in _inc)
V["HY_DEC_TXT"] = "、".join(f"{k} −{d}（清零）" for d, k, a in _dec if a == 0) or "无"
V["HY_N"] = str(len([k for k in c0 if k]))
V["HY_N_Y"] = str(len([k for k in c1 if k]))
V["HY_ZERO_N"] = str(len([k for k in c1 if c1[k] and not c0.get(k)]))
V["HY_NEW_N"] = str(len([k for k in c0 if c0[k] and not c1.get(k)]))
V["HY_YS0"] = "、".join(sorted(str(k) for k in c0 if c0[k] and not c1.get(k))[:6])
V["HY_GG0"] = "、".join(sorted(str(k) for k in c0 if c0[k] and not c1.get(k)))
V["HY_ZERO_LIST"] = "、".join(sorted(str(k) for k in c1 if c1[k] and not c0.get(k)))
V["HY_NEW_LIST"] = "、".join(sorted(str(k) for k in c0 if c0[k] and not c1.get(k)))

# ---------- 图表数据 ----------
V["JS_SENTI"] = json.dumps({
    "cat": [V["D2_LABEL"], V["D1_LABEL"], V["D0_LABEL"]],
    "zt": [ZT_2, ZT_Y, ZT], "zb": [ZB_2, ZB_Y, ZB],
    "dt": [DT_2, DT_Y, DT], "seal": [round(SEAL_2, 1), round(SEAL_Y, 1), round(SEAL, 1)],
}, ensure_ascii=False)
V["JS_AMT"] = json.dumps({"cat": [t[0] for t in yoy_s], "val": [round(t[1], 1) for t in yoy_s],
                          "pct": [round(t[2], 2) for t in yoy_s]}, ensure_ascii=False)
ic = ["sh000001", "sz399001", "sz399006", "sh000688", "sh000300", "sz399303", "sh000016"]
V["JS_INTRA"] = json.dumps({
    "cat": [NAME[k] for k in ic],
    "open": [round((idx0[k]["open"] / idx0[k]["prev"] - 1) * 100, 2) for k in ic],
    "low": [round((idx0[k]["low"] / idx0[k]["prev"] - 1) * 100, 2) for k in ic],
    "high": [round((idx0[k]["high"] / idx0[k]["prev"] - 1) * 100, 2) for k in ic],
    "close": [round(idx0[k]["pct"], 2) for k in ic],
}, ensure_ascii=False)
V["JS_LAD"] = json.dumps({"cat": [f"{b}板" for b in range(1, LADMAX + 1)],
                          "a": [lad0.get(b, 0) for b in range(1, LADMAX + 1)],
                          "b": [lad1.get(b, 0) for b in range(1, LADMAX + 1)]}, ensure_ascii=False)
V["JS_CHAIN"] = json.dumps({
    "cat": ["AI算力硬件", "机器人/具身", "AI应用/传媒"],
    "a": [round(hw0["amt"], 1), round(rb0["amt"], 1), round(md0["amt"], 1)],
    "b": [round(hw1["amt"], 1), round(rb1["amt"], 1), round(md1["amt"], 1)],
}, ensure_ascii=False)
V["JS_MV"] = json.dumps(mv_chart, ensure_ascii=False)
_ts_short = {"竞价/秒板": "竞价", "开盘半小时": "开盘30分", "上午盘中": "上午", "午后盘中": "午后", "尾盘": "尾盘"}
V["JS_TS"] = json.dumps({**ts_chart, "cat": [_ts_short[c] for c in ts_chart["cat"]]}, ensure_ascii=False)

# ---------- 情绪三日表 ----------
def r_(v, good):
    cls = "up" if good else "down"
    return '<td class="%s">%s</td>' % (cls, v)
def d_(dv, good_up):
    if dv == 0:
        return '<td class="mut">0</td>'
    cls = "up" if (dv > 0) == good_up else "down"
    return '<td class="%s">%+d</td>' % (cls, dv)
SENTI_ROWS = [
    ("涨停家数", str(ZT_2), str(ZT_Y), str(ZT), d_(ZT - ZT_Y, True)),
    ("触及涨停", str(TOUCH_2), str(TOUCH_Y), str(TOUCH), d_(TOUCH - TOUCH_Y, True)),
    ("封板率", f"{SEAL_2:.1f}%", f"{SEAL_Y:.1f}%", f"{SEAL:.1f}%",
     ('<td class="mut">0.0 pct</td>' if round(SEAL,1) == round(SEAL_Y,1) else
      '<td class="%s">%+.1f pct</td>' % ("up" if SEAL > SEAL_Y else "down", SEAL - SEAL_Y))),
    ("炸板家数", str(ZB_2), str(ZB_Y), str(ZB), d_(ZB - ZB_Y, False)),
    ("炸板回封", "—", str(ZB_SEALED_Y), str(ZB_SEALED), d_(ZB_SEALED - ZB_SEALED_Y, True)),
    ("跌停家数", str(DT_2), str(DT_Y), str(DT), d_(DT - DT_Y, False)),
    ("触及跌停", str(DTOUCH_2), str(DTOUCH_Y), str(DTOUCH), d_(DTOUCH - DTOUCH_Y, False)),
    ("跌停封死率", f"{DSEAL_2:.1f}%", f"{DSEAL_Y:.1f}%", f"{DSEAL:.1f}%",
     ('<td class="mut">0.0 pct</td>' if round(DSEAL,1) == round(DSEAL_Y,1) else
      '<td class="%s">%+.1f pct</td>' % ("up" if DSEAL < DSEAL_Y else "down", DSEAL - DSEAL_Y))),
    ("连板股家数", str(LB_2), str(LB_Y), str(LB), d_(LB - LB_Y, True)),
    ("最高连板", f"{MAXB_2} 板", f"{MAXB_Y} 板", f"{MAXB} 板", d_(MAXB - MAXB_Y, True)),
    ("两市成交额", "—", f"{AMT_Y:,.0f} 亿", f"{AMT:,.0f} 亿",
     '<td class="up">%+.1f%%</td>' % ((AMT / AMT_Y - 1) * 100)),
    ("涨停股合计成交", f"{AMT_SUM_2:.1f} 亿", f"{AMT_SUM_Y:.1f} 亿", f"{AMT_SUM:.1f} 亿",
     '<td class="up">%+.1f%%</td>' % ((AMT_SUM / AMT_SUM_Y - 1) * 100)),
]
V["TBL_SENTI"] = "\n".join(
    "<tr><td>%s</td><td>%s</td><td>%s</td><td class=\"hl\">%s</td>%s</tr>" % (a, b, c, d, e)
    for a, b, c, d, e in SENTI_ROWS)

# ---------- 派生文案用的现算串 ----------
_top7 = [(b["name"], b["continuous_plate_num"] / b["limit_up_num"] * 100) for b in bl[:7] if b["limit_up_num"]]
V["MAIN_TOP7_TXT"] = "、".join(f"{n} {r:.1f}%" for n, r in _top7)
_fades = sorted(abs((idx0[k]["price"] / idx0[k]["high"] - 1) * 100) for k in NAME if idx0.get(k))
V["FADE_RANGE"] = f"{_fades[0]:.2f}%~{_fades[-1]:.2f}%"
# 通信设备 / 汽车零部 的成分留存
def hy_txt(name):
    a, b = len(c0.get(name, ())), len(c1.get(name, ()))
    inter = len(c0.get(name, set()) & c1.get(name, set()))
    rr = (1 - inter / a) * 100 if a else 0
    return f"{name} {b}→{a} 只（成分留存 {inter} 只，轮换率 {rr:.0f}%）"
V["HY_CM_TXT"] = hy_txt("通信设备")
V["HY_CAR_TXT"] = hy_txt("汽车零部")
# 50–100 亿档
_s0 = [p0[c] for c in th0 if 5e9 <= (p0[c].get("ltsz") or 0) < 1e10]
_s1 = [p1[c] for c in th1 if 5e9 <= (p1[c].get("ltsz") or 0) < 1e10]
V["MV501_TXT"] = ("50–100 亿档从 %d 只降到 %d 只、成交 %.1f → %.1f 亿"
                  % (len(_s1), len(_s0), sum(x["amount"] for x in _s1) / 1e8, sum(x["amount"] for x in _s0) / 1e8))
# 链内低换手大票样例（按成交额取前三）
_hw_list = sorted(chain(KW_HW, p0, th0), key=lambda c: -(p0[c].get("amount") or 0))[:3]
V["LOW_TURN_TXT"] = "、".join(f"{th0[c]['name']} {p0[c]['hs']:.1f}%" for c in _hw_list)
# 断板最差三只（昨日连板中今日跌最多）
_worst = sorted([(Y[c]["pct"], th1[c]["name"]) for c in lb1 if c in Y])[:3]
V["LBY_WORST_TXT"] = "、".join(f"{n} {v:+.2f}%" for v, n in _worst)
_df_set = {c for c in th0 if "东方" in th0[c]["name"] or "东方" in (th0[c].get("reason_type") or "")}
V.update({
    "CH500_YOY": f"{pct_of('sh000905'):+.1f}",
    "SEAL_FAIL_D": f"{abs((TOUCH - ZT) / TOUCH * 100 - (TOUCH_Y - ZT_Y) / TOUCH_Y * 100):.1f}",
    "N_INTRA": "7",
    "ZT_D_ABS": str(abs(ZT - ZT_Y)),
    "DF_LAD4": str(sum(1 for c in _df_set if (p0[c].get("lbc") or 0) == 4)),
    "DF_LAD3": str(sum(1 for c in _df_set if (p0[c].get("lbc") or 0) == 3)),
    "HW_TOP_NAME": th0[_hw_list[0]]["name"] if _hw_list else "—",
    "HW_TOP_AMT": f"{(p0[_hw_list[0]].get('amount') or 0) / 1e8:.1f}" if _hw_list else "0",
})

# ---------- 封板率 ≥83% 的次日样本（现算） ----------
_rows = []
for _f in sorted(os.listdir(OUT)):
    _m = re.match(r"zt_stats_(\d{8})\.json$", _f)
    if not _m:
        continue
    _d = _m.group(1)
    _S = json.load(open(os.path.join(OUT, _f), encoding="utf-8"))
    _s = (_S.get("senti") or {}).get(_d) or {}
    if _s.get("seal_rate"):
        _rows.append((_d, _s["seal_rate"] * 100, _s["zt"]))
_hw = [(d, r, z, _rows[i + 1]) for i, (d, r, z) in enumerate(_rows) if r >= 83 and i + 1 < len(_rows)]
_deltas = [n[1] - r for _, r, _, n in _hw]
V.update({
    "HW_N": str(len(_hw)), "HW_DOWN": str(sum(1 for x in _deltas if x < 0)),
    "HW_MIN": f"{min(_deltas):+.1f}", "HW_MAX": f"{max(_deltas):+.1f}",
    "HW_MEAN": f"{sum(_deltas) / len(_deltas):+.1f}",
    "HW_TXT": "、".join(f"{d[4:6]}/{d[6:8]} {r:.1f}%→{n[1]:.1f}%" for d, r, _, n in _hw),
})

# ---------- 渲染 ----------
tpl = open(TPL, encoding="utf-8").read()
miss = []
def rep(m):
    k = m.group(1)
    if k in V:
        return str(V[k])
    miss.append(k)
    return m.group(0)
html = re.sub(r"__([A-Z_0-9]+)__", rep, tpl)
if miss:
    raise SystemExit("缺失占位符: %s" % sorted(set(miss)))
res = re.findall(r"__[A-Z_0-9]+__", html)
print("placeholder residue:", sorted(set(res)))
fn = f"涨停复盘对比-{D0}.html"
open(os.path.join(REP, fn), "w", encoding="utf-8").write(html)
print("saved ->", os.path.join(REP, fn), len(html), "bytes")
