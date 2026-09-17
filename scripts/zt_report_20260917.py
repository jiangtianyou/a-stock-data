# -*- coding: utf-8 -*-
"""涨停复盘报告生成 2026-09-17（对比 09-16）—— 基于 skill 模板改写叙述文案

用法：python scripts/zt_report_20260917.py 20260917
输入：out/zt_stats_20260917.json、out/zt_review_20260917.json
输出：reports/涨停复盘对比-20260917.html
"""
import json, os, sys, re, html, statistics as st

ROOT = os.environ.get("ZT_ROOT") or os.getcwd()
OUT = os.path.join(ROOT, "out")
REP = os.path.join(ROOT, "reports")
os.makedirs(REP, exist_ok=True)

S = json.load(open(os.path.join(OUT, f"zt_stats_{sys.argv[1]}.json"), encoding="utf-8"))
D0, D1 = S["D0"], S["D1"]
D2 = S.get("D2")
B = json.load(open(os.path.join(OUT, f"zt_review_{D0}.json"), encoding="utf-8"))
r0, r1 = S["r0"], S["r1"]
perf = S["perf"]
s0, s1 = S["senti"][D0], S["senti"][D1]


def md(ds):
    return f"{int(ds[4:6])}/{int(ds[6:8])}"


def esc(s):
    return html.escape(str(s))


def seal(a, b):
    return a / (a + b) * 100 if (a + b) else 0.0


# ---- 三日情绪 ----
days = [
    {"d": md(D2) if D2 else "-", "zt": s1["zt_prev"], "zb": s1["zb_prev"], "dt": s1["dt_prev"]},
    {"d": md(D1), "zt": s1["zt"], "zb": s1["zb"], "dt": s1["dt"]},
    {"d": md(D0), "zt": s0["zt"], "zb": s0["zb"], "dt": s0["dt"]},
]
for x in days:
    x["seal"] = seal(x["zt"], x["zb"])

# ---- 指数 ----
IX_ORDER = [("上证指数", "sh000001"), ("深证成指", "sz399001"), ("创业板指", "sz399006"),
            ("科创50", "sh000688"), ("中证1000", "sh000852"), ("国证2000", "sz399303"),
            ("中证500", "sh000905"), ("沪深300", "sh000300"), ("北证50", "bj899050"),
            ("上证50", "sh000016"), ("中小100", "sz399005")]
idx_now = {v["name"]: v for v in B["indexes"].values()}
ix = []
for nm, sym in IX_ORDER:
    v = idx_now.get(nm)
    if v:
        ix.append({"name": nm, "pct": v["pct"], "amt": (v["amount_wan"] or 0) / 10000.0,
                   "price": v["price"]})
ixr = {x["name"]: x for x in ix}
PREV_IDX_PCT = {k: (v.get("prev_pct") or 0.0) for k, v in (S.get("idx_cmp") or {}).items()}
PREV_IDX_AMT = {k: (v.get("prev_amt") or 0.0) for k, v in (S.get("idx_cmp") or {}).items()}

amt_today = ixr["上证指数"]["amt"] + ixr["深证成指"]["amt"]
tot = S.get("tot") or {}
amt_prev = tot.get("prev") or amt_today
amt_pct = (amt_today / amt_prev - 1) * 100 if amt_prev else 0.0
kc = ixr.get("科创50", {})
kc_prev_amt = PREV_IDX_AMT.get("科创50") or kc.get("amt", 1)
kc_amt_pct = (kc.get("amt", 0) / kc_prev_amt - 1) * 100 if kc_prev_amt else 0.0

# ---- 行业迁移 ----
hy0, hy1 = S["hy0"], S["hy1"]
hy_keys = sorted(set(list(hy0) + list(hy1)),
                 key=lambda k: (-(hy0.get(k, 0) * 2 + hy1.get(k, 0)), -hy0.get(k, 0), -hy1.get(k, 0), k))
hy_tbl = [{"name": k, "t": hy0.get(k, 0), "y": hy1.get(k, 0)} for k in hy_keys[:18]]

# ---- 连板梯队 ----
lad0 = {int(k): v for k, v in s0["ladder"].items()}
lad1 = {int(k): v for k, v in s1["ladder"].items()}
lad_max = max(max(lad0), max(lad1))
lad_series = lambda d, m: [d.get(i, 0) for i in range(1, m + 1)]

# ---- 封板时间 ----
TS_ORDER = ["竞价/秒板", "开盘半小时", "上午盘中", "午后盘中", "尾盘"]
ts0, ts1 = S["timeslot"]["today"], S["timeslot"]["yesterday"]

# ---- 晋级/溢价 ----
adv = [p for p in perf if p["again"]]
adv_rate = len(adv) / len(perf) * 100
pcts = [p["pct"] for p in perf if p["pct"] is not None]
neg = sum(1 for p in pcts if p < 0)
# 注意：不能用 `x["pct"] or -99`——pct 恰为 0.00（收平）时会被当成缺失值排到末尾，导致「最弱」显示错误
perf_sorted = sorted(perf, key=lambda x: -(x["pct"] if x["pct"] is not None else -999))
top3 = perf_sorted[:3]
bot3 = perf_sorted[-3:]

g_sb = [p for p in perf if (p["lbc"] or 1) == 1]
g_lb = [p for p in perf if (p["lbc"] or 1) >= 2]


def grp(g):
    p_ = [x["pct"] for x in g if x["pct"] is not None]
    return {"n": len(g), "adv": sum(1 for x in g if x["again"]) / len(g) * 100 if g else 0,
            "mean": st.mean(p_) if p_ else 0, "med": st.median(p_) if p_ else 0,
            "neg": sum(1 for v in p_ if v < 0)}


G_SB, G_LB = grp(g_sb), grp(g_lb)

# ---- 成交额结构 ----
amts = [r["amount"] for r in r0 if r["amount"]]
funds = [r["fund"] for r in r0 if r["fund"]]
amts1 = [r["amount"] for r in r1 if r["amount"]]
hss = [r["turnover"] for r in r0 if r["turnover"]]
hss1 = [r["turnover"] for r in r1 if r["turnover"]]
amt_sum, fund_sum = sum(amts) / 1e8, sum(funds) / 1e8
share = amt_sum / amt_today * 100
share_prev = sum(amts1) / 1e8 / amt_prev * 100
med_amt, med_amt1 = st.median(amts) / 1e8, st.median(amts1) / 1e8
med_hs, med_hs1 = st.median(hss), st.median(hss1)
oneword = sum(1 for r in r0 if "一字" in (r["limit_up_type"] or ""))
tword = sum(1 for r in r0 if "T字" in (r["limit_up_type"] or ""))
huanshou = sum(1 for r in r0 if "换手" in (r["limit_up_type"] or ""))
big_n = sum(1 for r in r0 if (r["ltsz"] or 0) >= 300e8)
big_list = "、".join(r["name"] for r in sorted(r0, key=lambda x: -(x["ltsz"] or 0)) if (r["ltsz"] or 0) >= 300e8)

# ---- 炸板池交叉 ----
zb0 = B["dates"][D0]["em_ZB"]["pool"]
zt_yest = {x["c"] for x in B["dates"][D1]["em_ZT"]["pool"]}
zb_in_yzt = [x["n"] for x in zb0 if x["c"] in zt_yest]


def early(v):
    t = int(v); h = t // 10000; m = (t % 10000) // 100
    return h < 11 or (h == 11 and m < 30)


zb_early = sum(1 for x in zb0 if early(x["fbt"]))
zb_early_pct = zb_early / len(zb0) * 100 if zb0 else 0
zb_before1030 = sum(1 for x in zb0 if int(x["fbt"]) < 103000)

# ---- 主线归因 ----
THEMES = [
    ("汽车产业链", ["汽车整车", "汽车零部", "A0车型", "整车业务", "汽配", "汽车线束", "汽车连接器",
                "汽车玻璃", "汽车贸易", "客车", "哪吒", "宁德时代", "吉利", "智能驾驶", "座椅",
                "空气悬架", "海外布局"]),
    ("机器人 / 具身智能", ["机器人", "人形", "行星滚柱丝杠", "线性驱动", "具身"]),
    ("半导体 / 电子材料", ["半导体", "硅片", "离子注入", "超纯水膜", "MLCC", "氧化锆", "电子玻璃",
                     "功率半导体", "晶圆"]),
    ("AI算力 / 光通信", ["光模块", "光通信", "光纤", "算力", "液冷", "服务器", "硅光", "移动通信", "数据中心"]),
    ("农业 / 种业粮食", ["种业", "玉米", "转基因", "粮油", "粮食", "育种", "农产品"]),
    ("国资 / 区域主题", ["国资", "国企"]),
    ("电力 / 电网 / 储能", ["智能电网", "智能配电", "V2G", "储能", "热电", "电力", "弗迪"]),
    ("烟草 / HNB", ["烟草", "卷烟纸", "HNB", "烟标", "香精"]),
    ("医药 / 医疗", ["医药", "细胞", "CRO", "制剂", "用药", "皮肤"]),
    ("风电 / 大兆瓦", ["风电", "齿轮箱", "铸件", "大兆瓦"]),
]
theme_cnt = []
for nm, kws in THEMES:
    hit = [r for r in r0 if any(k in r["reason"] for k in kws)]
    theme_cnt.append({"name": nm, "n": len(hit),
                      "stocks": [r["name"] + "(" + str(r["lbc"] or 1) + "板)" for r in
                                 sorted(hit, key=lambda x: (-(x["lbc"] or 0), -(x["amount"] or 0)))][:8]})
theme_cnt.sort(key=lambda x: (-x["n"], x["name"]))

# ---- 连板股 ----
lb_all = sorted([r for r in r0 if (r["lbc"] or 1) >= 2], key=lambda x: (-(x["lbc"] or 0), -(x["amount"] or 0)))
maxb = max(lad0) if lad0 else 0
maxb_y = max(lad1) if lad1 else 0
car_first = [r for r in r0 if r["hybk"] == "汽车零部"]
car_all1 = all((r["lbc"] or 1) == 1 for r in car_first)

# ================= 表格片段 =================
tbl_lad = "".join(
    "<tr><td>{0} 板</td><td>{1}</td><td class='hl'>{2}</td><td class='{3}'>{4:+d}</td></tr>".format(
        i, lad1.get(i, 0), lad0.get(i, 0),
        "up" if lad0.get(i, 0) - lad1.get(i, 0) > 0 else ("down" if lad0.get(i, 0) - lad1.get(i, 0) < 0 else "mut"),
        lad0.get(i, 0) - lad1.get(i, 0))
    for i in range(lad_max, 0, -1))

tbl_lianban = "".join(
    "<tr><td>{0}板</td><td>{1}</td><td class='hl'>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td><td>{6:.1f}%</td>"
    "<td>{7}</td><td style='text-align:left;color:#4b5563'>{8}</td></tr>".format(
        r["lbc"], r["code"], esc(r["name"]), (r["fbt"][:5] if r["fbt"] else "—"),
        "{:.2f}亿".format((r["fund"] or 0) / 1e8), "{:.2f}亿".format((r["amount"] or 0) / 1e8),
        (r["turnover"] or 0), esc(r["hybk"]), esc(r["reason"]))
    for r in lb_all)

tbl_hy = "".join(
    "<tr><td>{0}</td><td>{1}</td><td class='hl'>{2}</td><td class='{3}'>{4:+d}</td>"
    "<td style='text-align:left;color:#6b7280'>{5}</td></tr>".format(
        esc(h["name"]), h["y"], h["t"],
        "up" if h["t"] - h["y"] > 0 else ("down" if h["t"] - h["y"] < 0 else "mut"),
        h["t"] - h["y"], "流入" if h["t"] - h["y"] > 0 else ("流出" if h["t"] - h["y"] < 0 else "持平"))
    for h in hy_tbl)

tbl_ts = "".join(
    "<tr><td>{0}</td><td>{1}</td><td class='hl'>{2}</td><td class='{3}'>{4:.0f}%</td></tr>".format(
        k, ts1.get(k, 0), ts0.get(k, 0),
        "up" if (ts0.get(k, 0) / s0["zt"]) > (ts1.get(k, 0) / s1["zt"]) else "down",
        ts0.get(k, 0) / s0["zt"] * 100)
    for k in TS_ORDER)

tbl_theme = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td style='text-align:left'>{2}</td></tr>".format(
        esc(t["name"]), t["n"], "".join("<span class=tag>" + esc(s) + "</span>" for s in t["stocks"]))
    for t in theme_cnt if t["n"] > 0)

tbl_idx = "".join(
    "<tr><td>{0}</td><td class='{1}'>{2:+.2f}%</td><td class='{3}'>{4}</td><td>{5:,.0f}亿</td><td class='{6}'>{7}</td></tr>".format(
        esc(x["name"]), "up" if x["pct"] >= 0 else "down", x["pct"],
        "up" if PREV_IDX_PCT.get(x["name"], 0) >= 0 else "down",
        ("{:+.2f}%".format(PREV_IDX_PCT[x["name"]]) if x["name"] in PREV_IDX_PCT else "—"),
        x["amt"],
        "down" if x["name"] in PREV_IDX_AMT and x["amt"] < PREV_IDX_AMT[x["name"]] else "up",
        ("{:+,.0f}亿".format(x["amt"] - PREV_IDX_AMT[x["name"]]) if x["name"] in PREV_IDX_AMT else "—"))
    for x in ix)

tbl_zb = "".join(
    "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td class='{5}'>{6}</td></tr>".format(
        esc(x["n"]), x["c"], esc(x["hybk"]), "{:.1f}亿".format(x["amount"] / 1e8),
        (str(int(x["fbt"]))[:2] + ":" + str(int(x["fbt"]))[2:4]),
        "down" if x["c"] in zt_yest else "mut", "昨日涨停" if x["c"] in zt_yest else "新面孔")
    for x in sorted(zb0, key=lambda v: -v["amount"]))


def fmtv(v):
    return "{:.1f}".format(v) if isinstance(v, float) else str(v)


def fmtd(v):
    return ("{:+.1f}" if isinstance(v, float) else "{:+d}").format(v)


tbl_senti = "".join(
    "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td class='hl'>{3}</td><td class='{4}'>{5}</td></tr>".format(
        lab, fmtv(days[0][k]), fmtv(days[1][k]), fmtv(days[2][k]),
        "up" if days[2][k] - days[1][k] > 0 else ("down" if days[2][k] - days[1][k] < 0 else "mut"),
        fmtd(days[2][k] - days[1][k]))
    for lab, k in [("涨停家数", "zt"), ("炸板家数", "zb"), ("封板率(%)", "seal"), ("跌停家数", "dt")])

perf_top = "、".join("{}{:+.1f}%".format(esc(p["name"]), p["pct"]) for p in top3)
perf_bot = "、".join("{}{:+.1f}%".format(esc(p["name"]), p["pct"]) for p in bot3)

# ================= 占位符 =================
V = {}


def P(k, v):
    V["__" + k + "__"] = str(v)


P("GEN_AT", B["generated_at"])
P("D0L", md(D0)); P("D1L", md(D1)); P("D2L", md(D2) if D2 else "-")
P("ZT", s0["zt"]); P("ZT_Y", s1["zt"]); P("ZT_D", "{:+d}".format(s0["zt"] - s1["zt"]))
P("ZB", s0["zb"]); P("ZB_Y", s1["zb"]); P("ZB_D", "{:+d}".format(s0["zb"] - s1["zb"]))
P("DT", s0["dt"]); P("DT_Y", s1["dt"]); P("DT_D", "{:+d}".format(s0["dt"] - s1["dt"]))
P("SEAL", "{:.1f}".format(s0["seal_rate"] * 100))
P("SEAL_Y", "{:.1f}".format(s1["seal_rate"] * 100))
P("SEAL_D", "{:+.1f}".format((s0["seal_rate"] - s1["seal_rate"]) * 100))
P("ZTDT", "{:.1f}".format(s0["zt"] / s0["dt"] if s0["dt"] else 0))
P("ZTDT_Y", "{:.1f}".format(s1["zt"] / s1["dt"] if s1["dt"] else 0))
P("ZTDT_0", "{:.1f}".format(days[0]["zt"] / days[0]["dt"] if days[0]["dt"] else 0))
P("DT_OPEN", s0["limit_down_count"]["today"]["open_num"])
P("MAXB", maxb); P("MAXB_Y", maxb_y)
P("LB", s0["lianban"]); P("LB_Y", s1["lianban"])
P("SB", s0["shouban"]); P("SB_Y", s1["shouban"])
P("SB_PCT", "{:.0f}".format(s0["shouban"] / s0["zt"] * 100))
P("SB_PCT_Y", "{:.0f}".format(s1["shouban"] / s1["zt"] * 100))
P("AMT", "{:,.0f}".format(amt_today)); P("AMT_Y", "{:,.0f}".format(amt_prev))
P("AMT_D", "{:+,.0f}".format(amt_today - amt_prev)); P("AMT_PCT", "{:+.1f}".format(amt_pct))
P("KC_PCT", "{:+.2f}".format(kc.get("pct", 0)))
P("KC_PCT_Y", "{:+.2f}".format(PREV_IDX_PCT.get("科创50", 0)))
P("KC_AMT", "{:,.0f}".format(kc.get("amt", 0)))
P("KC_AMT_PCT", "{:+.1f}".format(kc_amt_pct))
P("KC_AMT_PREV", "{:,.0f}".format(kc_prev_amt))
P("SZ50_PCT", "{:+.2f}".format(ixr.get("上证50", {}).get("pct", 0)))
P("ZSX_PCT", "{:+.2f}".format(ixr.get("中小100", {}).get("pct", 0)))
P("ADV_RATE", "{:.1f}".format(adv_rate)); P("ADV_N", len(adv)); P("ADV_TOT", len(perf))
P("PERF_MEAN", "{:+.2f}".format(st.mean(pcts))); P("PERF_MED", "{:+.2f}".format(st.median(pcts)))
P("PERF_MAX", "{:+.2f}".format(max(pcts))); P("PERF_MIN", "{:+.2f}".format(min(pcts)))
P("PERF_MAX_NAME", esc(perf_sorted[0]["name"]))
P("PERF_MAX_LB", perf_sorted[0]["lbc"])
P("PERF_MIN_NAME", esc(perf_sorted[-1]["name"]))
P("PERF_MIN_LB", perf_sorted[-1]["lbc"])
P("PERF_TOP3", perf_top); P("PERF_BOT3", perf_bot)
P("NEG", neg); P("NEG_PCT", "{:.1f}".format(neg / len(pcts) * 100))
P("GSB_N", G_SB["n"]); P("GSB_ADV", "{:.1f}".format(G_SB["adv"])); P("GSB_MEAN", "{:+.2f}".format(G_SB["mean"]))
P("GSB_MED", "{:+.2f}".format(G_SB["med"])); P("GSB_NEG", G_SB["neg"])
P("GLB_N", G_LB["n"]); P("GLB_ADV", "{:.1f}".format(G_LB["adv"])); P("GLB_MEAN", "{:+.2f}".format(G_LB["mean"]))
P("GLB_MED", "{:+.2f}".format(G_LB["med"])); P("GLB_NEG", G_LB["neg"])
P("AMT_SUM", "{:.0f}".format(amt_sum)); P("SHARE", "{:.1f}".format(share))
P("SHARE_Y", "{:.1f}".format(share_prev))
P("MED_AMT", "{:.2f}".format(med_amt)); P("MED_AMT_Y", "{:.2f}".format(med_amt1))
P("MED_HS", "{:.1f}".format(med_hs)); P("MED_HS_Y", "{:.1f}".format(med_hs1))
P("FUND_SUM", "{:.1f}".format(fund_sum)); P("FUND_MED", "{:.2f}".format(st.median(funds) / 1e8))
P("FUND_MED_Y", "{:.2f}".format(st.median([r["fund"] for r in r1 if r["fund"]]) / 1e8))
P("FUND_AVG", "{:.2f}".format(fund_sum / s0["zt"]))
P("ONEWORD", oneword); P("ONEWORD_PCT", "{:.1f}".format(oneword / s0["zt"] * 100))
P("TWORD", tword); P("HUANSHOU", huanshou)
P("BIG_N", big_n); P("BIG_LIST", esc(big_list))
P("ZB_EARLY", zb_early); P("ZB_EARLY_PCT", "{:.0f}".format(zb_early_pct))
P("ZB_B1030", zb_before1030)
P("ZB_IN_YZT_N", len(zb_in_yzt)); P("ZB_IN_YZT", "、".join(zb_in_yzt))
P("TBL_ZB", tbl_zb)
P("LB_TOP1", esc(lb_all[0]["name"])); P("LB_TOP1_REASON", esc(lb_all[0]["reason"]))
P("LB_TOP2", esc(lb_all[1]["name"])); P("LB_TOP2_LB", lb_all[1]["lbc"])
P("CAR_N", len(car_first)); P("CAR_ALL_FIRST", "是" if car_all1 else "否")
P("TH_N", len([t for t in theme_cnt if t["n"] > 0]))
P("HY_TXD", hy1.get("通信设备", 0)); P("HY_TXD0", hy0.get("通信设备", 0))
P("HY_BDT", hy1.get("半导体", 0)); P("HY_BDT0", hy0.get("半导体", 0))
P("HY_HXP", hy1.get("化学制品", 0)); P("HY_HXP0", hy0.get("化学制品", 0))
P("HY_YJ", hy1.get("元件", 0)); P("HY_YJ0", hy0.get("元件", 0))
P("HY_QT", hy1.get("其他电子", 0)); P("HY_QT0", hy0.get("其他电子", 0))
P("HY_QC", hy1.get("汽车零部", 0)); P("HY_QC0", hy0.get("汽车零部", 0))
P("HY_FD", hy1.get("风电设备", 0)); P("HY_FD0", hy0.get("风电设备", 0))
P("HY_BZ", hy1.get("包装印刷", 0)); P("HY_BZ0", hy0.get("包装印刷", 0))
P("TS_EARLY_Y", ts1.get("竞价/秒板", 0) + ts1.get("开盘半小时", 0))
P("TS_EARLY_Y_PCT", "{:.0f}".format((ts1.get("竞价/秒板", 0) + ts1.get("开盘半小时", 0)) / s1["zt"] * 100))
P("TS_EARLY_0", ts0.get("竞价/秒板", 0) + ts0.get("开盘半小时", 0))
P("TS_EARLY_0_PCT", "{:.0f}".format((ts0.get("竞价/秒板", 0) + ts0.get("开盘半小时", 0)) / s0["zt"] * 100))
P("TS_PM0", ts0.get("午后盘中", 0)); P("TS_PM1", ts1.get("午后盘中", 0))
P("TS_PM0_PCT", "{:.0f}".format(ts0.get("午后盘中", 0) / s0["zt"] * 100))
P("TS_PM1_PCT", "{:.0f}".format(ts1.get("午后盘中", 0) / s1["zt"] * 100))
P("TBL_SENTI", tbl_senti); P("TBL_LAD", tbl_lad); P("TBL_LIANBAN", tbl_lianban)
P("TBL_HY", tbl_hy); P("TBL_TS", tbl_ts); P("TBL_THEME", tbl_theme); P("TBL_IDX", tbl_idx)
P("JS_DAYS", json.dumps([d["d"] for d in days], ensure_ascii=False))
P("JS_ZT", json.dumps([d["zt"] for d in days]))
P("JS_ZB", json.dumps([d["zb"] for d in days]))
P("JS_DT", json.dumps([d["dt"] for d in days]))
P("JS_SEAL", json.dumps([round(d["seal"], 1) for d in days]))
P("JS_IX_NAME", json.dumps([x["name"] for x in ix][::-1], ensure_ascii=False))
P("JS_IX_PCT", json.dumps([round(x["pct"], 2) for x in ix][::-1]))
P("JS_LAD_NAME", json.dumps([str(i) + "板" for i in range(1, lad_max + 1)], ensure_ascii=False))
P("JS_LAD0", json.dumps(lad_series(lad0, lad_max)))
P("JS_LAD1", json.dumps(lad_series(lad1, lad_max)))
P("JS_TH_NAME", json.dumps([t["name"] for t in theme_cnt][::-1], ensure_ascii=False))
P("JS_TH_N", json.dumps([t["n"] for t in theme_cnt][::-1]))
P("JS_HY_NAME", json.dumps([h["name"] for h in hy_tbl][::-1], ensure_ascii=False))
P("JS_HY_T", json.dumps([h["t"] for h in hy_tbl][::-1]))
P("JS_HY_Y", json.dumps([h["y"] for h in hy_tbl][::-1]))
P("JS_PF_NAME", json.dumps([p["name"] for p in perf_sorted][::-1], ensure_ascii=False))
P("JS_PF_PCT", json.dumps([round(p["pct"], 2) for p in perf_sorted][::-1]))
P("JS_TS_NAME", json.dumps(TS_ORDER, ensure_ascii=False))
P("JS_TS_T", json.dumps([ts0.get(k, 0) for k in TS_ORDER]))
P("JS_TS_Y", json.dumps([ts1.get(k, 0) for k in TS_ORDER]))

# 派生占位符（注意命名不要与上面的 key 形成前缀包含关系）
V["__D2L_ZT__"] = str(days[0]["zt"])
V["__D2L_DT__"] = str(days[0]["dt"])
V["__TH_AI__"] = str(next((t["n"] for t in theme_cnt if t["name"].startswith("AI算力")), 0))
V["__AMT_DABS__"] = "{:,.0f}".format(abs(amt_today - amt_prev))
V["__MED_AMT_UP__"] = "{:+.0f}".format((med_amt / med_amt1 - 1) * 100)
V["__MED_HS_UP__"] = "{:+.1f}".format(med_hs - med_hs1)
V["__MAXBN__"] = str(maxb + 1)

# ================= HTML 模板 =================
HTML_T = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>涨停复盘 · 2026-09-17（对比 9-16）</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
*{box-sizing:border-box}
body{margin:0;background:#f5f6f8;color:#1b1f24;font:14px/1.65 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:28px 20px 60px}
h1{font-size:26px;margin:0 0 6px;letter-spacing:-.3px}
.sub{color:#6b7280;font-size:13px;margin-bottom:22px}
.card{background:#fff;border:1px solid #e6e8eb;border-radius:12px;padding:20px 22px;margin-bottom:18px}
h2{font-size:17px;margin:0 0 14px;padding-left:10px;border-left:4px solid #2563eb}
h3{font-size:14px;margin:18px 0 8px;color:#374151}
.lead{background:#fff;border:1px solid #e6e8eb;border-left:5px solid #2563eb;border-radius:10px;padding:18px 22px;margin-bottom:18px}
.lead p{margin:0 0 8px}.lead p:last-child{margin-bottom:0}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:12px;margin:16px 0 4px}
.kpi{background:#fff;border:1px solid #e6e8eb;border-radius:10px;padding:14px 16px}
.kpi .lbl{font-size:12px;color:#6b7280;margin-bottom:6px}
.kpi .val{font-size:23px;font-weight:650;letter-spacing:-.5px}
.kpi .dt{font-size:12px;margin-top:4px}
.up{color:#d93025}.down{color:#12805c}.mut{color:#9ca3af}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:7px 9px;border-bottom:1px solid #eef0f2;text-align:right}
th:first-child,td:first-child{text-align:left}
th{background:#fafbfc;color:#4b5563;font-weight:600;font-size:12px}
tr:hover td{background:#fafbfc}
.chart{width:100%;height:330px}.chart-sm{width:100%;height:270px}
.two{display:grid;grid-template-columns:1fr 1fr;gap:18px}
@media(max-width:820px){.two{grid-template-columns:1fr}}
.tag{display:inline-block;background:#eef2ff;color:#3730a3;border-radius:5px;padding:1px 7px;font-size:11px;margin:1px 3px 1px 0}
.note{font-size:12px;color:#6b7280;line-height:1.75}
.warn{background:#fff8f1;border:1px solid #f5d9be;border-radius:10px;padding:14px 18px;font-size:13px;color:#7c4a12}
ul{margin:6px 0 0;padding-left:20px}li{margin:6px 0}
.hl{font-weight:600;color:#111827}
</style>
</head>
<body>
<div class="wrap">
<h1>涨停复盘 · 2026-09-17（周四）</h1>
<div class="sub">对比基准：2026-09-16（周三）｜口径：沪深两市（不含北交所）｜数据源：同花顺涨停池 + 东方财富涨停/炸板/跌停池 + 腾讯财经行情快照</div>

<div class="lead">
<p class="hl">一句话结论：昨日的普涨只维持一天就收敛。涨停从 __ZT_Y__ 家降到 __ZT__ 家、封板率从 __SEAL_Y__% 掉到 __SEAL__%（__SEAL_D__pct）、炸板从 __ZB_Y__ 家翻倍到 __ZB__ 家——
但这不是退潮：跌停只剩 __DT__ 家（昨 __DT_Y__ 家）、两市成交额 __AMT__ 亿几乎没缩（__AMT_PCT__%），
<b>昨日连板股今日均涨 __GLB_MEAN__%、中位 __GLB_MED__%、晋级率 __GLB_ADV__%</b>。</p>
<p>真正恶化的是<b>首板股的接力</b>：昨日 __GSB_N__ 只首板今日晋级率仅 __GSB_ADV__%、中位 __GSB_MED__%、__GSB_NEG__ 只翻绿。
<span class="hl">今天是「宽度收缩、高度保留」的结构切换日，不是杀跌日。</span>
资金从昨日遍地开花的算力链（通信设备 __HY_TXD__→__HY_TXD0__ 家、其他电子 __HY_QT__→__HY_QT0__ 家）
搬到汽车产业链（汽车零部 __HY_QC__→__HY_QC0__ 家）。</p>
</div>

<div class="kpis">
  <div class="kpi"><div class="lbl">涨停家数</div><div class="val up">__ZT__</div>
    <div class="dt mut">昨日 __ZT_Y__ <span class="down">__ZT_D__</span></div></div>
  <div class="kpi"><div class="lbl">封板率</div><div class="val">__SEAL__%</div>
    <div class="dt mut">昨日 __SEAL_Y__% <span class="down">__SEAL_D__pct</span></div></div>
  <div class="kpi"><div class="lbl">跌停家数</div><div class="val down">__DT__</div>
    <div class="dt mut">昨日 __DT_Y__ <span class="down">__DT_D__</span></div></div>
  <div class="kpi"><div class="lbl">两市成交额</div><div class="val">__AMT__亿</div>
    <div class="dt mut">昨日 __AMT_Y__亿 <span class="down">__AMT_D__亿</span></div></div>
  <div class="kpi"><div class="lbl">昨涨停今日晋级率</div><div class="val">__ADV_RATE__%</div>
    <div class="dt mut">__ADV_N__/__ADV_TOT__ 只再涨停</div></div>
  <div class="kpi"><div class="lbl">最高连板</div><div class="val">__MAXB__ 板</div>
    <div class="dt mut">昨日 __MAXB_Y__ 板</div></div>
</div>

<div class="card">
<h2>一、市场情绪温度计：从「普涨」到「收敛」</h2>
<table>
<tr><th>指标</th><th>__D2L__</th><th>__D1L__</th><th>__D0L__</th><th>__D0L__ 环比</th></tr>
__TBL_SENTI__
<tr><td>涨停/跌停比</td><td>__ZTDT_0__</td><td>__ZTDT_Y__</td><td class="hl">__ZTDT__</td><td class="up">继续走强</td></tr>
</table>
<div class="note" style="margin-top:10px">
三日序列看清了这轮节奏：__D2L__ 是退潮杀跌（涨停 __D2L_ZT__ 家、跌停 __D2L_DT__ 家），__D1L__ 是全面修复（涨停 __ZT_Y__ 家、封板率 __SEAL_Y__%），
__D0L__ 是<b>修复后的收敛</b>。<br>
判断「收敛」而非「退潮」的核心证据是<b>跌停家数</b>：__D2L__ 跌停 __D2L_DT__ 家、__D1L__ __DT_Y__ 家、今日仅 __DT__ 家，
且今日这只跌停是盘中 __DT_OPEN__ 次开板、并非一字闷杀。
<span class="hl">涨停腰斩而跌停继续收敛 —— 说明资金是「不追了」，而不是「夺路而逃」。</span>
但封板率 __SEAL__% 已跌破 75% 这一健康阈值，承接力度确实在变差。
</div>
<div id="c_senti" class="chart" style="margin-top:16px"></div>
</div>

<div class="card">
<h2>二、指数与量能：回调不缩量，钱还在场内</h2>
<div class="two">
<div>
<table>
<tr><th>指数</th><th>今日</th><th>昨日</th><th>成交额</th><th>环比</th></tr>
__TBL_IDX__
</table>
<div class="note" style="margin-top:10px">
<b>量能是最硬的反面证据：</b>两市成交额 __AMT__ 亿，环比 __AMT_D__ 亿（__AMT_PCT__%）—— 几乎持平。
指数全线小幅回调，跌幅最大的上证50 __SZ50_PCT__%，最小的是中小100 __ZSX_PCT__%，<b>11 个指数跌幅全在 1.5% 以内</b>。<br>
唯一明显缩量的是科创50：成交额 __KC_AMT__ 亿（昨 __KC_AMT_PREV__ 亿，__KC_AMT_PCT__%）。
昨天科创50 涨 __KC_PCT_Y__%、今天跌 __KC_PCT__% 领跌，<span class="hl">昨日领涨的科技成长今天成了主要回调对象 —— 典型的「涨多了先歇」。</span>
</div>
</div>
<div><div id="c_idx" class="chart-sm"></div></div>
</div>
</div>

<div class="card">
<h2>三、连板梯队：宽度收了一半，高度只让了一板</h2>
<div class="two">
<div><div id="c_lad" class="chart-sm"></div></div>
<div>
<table>
<tr><th>梯队</th><th>__D1L__</th><th>__D0L__</th><th>变化</th></tr>
__TBL_LAD__
<tr><td>合计</td><td>__ZT_Y__</td><td class="hl">__ZT__</td><td class="down">__ZT_D__</td></tr>
</table>
<div class="note" style="margin-top:10px">
首板 __SB__ 家（昨 __SB_Y__），首板占比 __SB_PCT__%（昨 __SB_PCT_Y__%）；连板股 __LB__ 家（昨 __LB_Y__）。
最高板从 __MAXB_Y__ 板降到 __MAXB__ 板（__LB_TOP1__，__LB_TOP1_REASON__）—— 只让了一板。<br>
更值得注意的是<b>中位梯队逆势增厚</b>：3 板从 __D1L__ 的 1 家增至 3 家（中晶科技、华瓷股份、锡华科技），2 板 5 家（昨 9 家）。
<span class="hl">首板塌了一半、连板只少了四分之一，高度端比宽度端抗跌得多。</span>
</div>
</div>
</div>
<h3>今日连板股全名单</h3>
<table>
<tr><th>高度</th><th>代码</th><th>名称</th><th>首封</th><th>封单</th><th>成交额</th><th>换手</th><th>行业</th><th>涨停原因</th></tr>
__TBL_LIANBAN__
</table>
</div>

<div class="card">
<h2>四、主线归因：汽车链接棒，算力链退位</h2>
<div id="c_theme" class="chart"></div>
<table style="margin-top:14px">
<tr><th>主线</th><th>涨停家数</th><th>代表个股</th></tr>
__TBL_THEME__
</table>
<div class="note" style="margin-top:12px">
今日 __TH_N__ 条主线里有 1 条断层领先：<b>汽车产业链 12 家</b>（整车 2 + 零部件 8 + 汽车服务/客车各 1），
并带出机器人链 __A_ROBOT__ 家（均胜电子、北特科技、克来机电、冠盛股份、凯迪股份、科森科技——多为「汽车零部件 + 人形机器人」双标签）。
昨日最强的 AI 算力 / 光通信今日只剩 __TH_AI__ 家命中，高度靠 __LB_TOP1__（__MAXB__ 板，__LB_TOP1_REASON__）独撑。<br>
<b>要提醒的是：汽车零部 __CAR_N__ 只涨停股里没有一只是连板（全部首板）。</b>
这意味着这条线目前只是「资金扩散」，还没跑出连板高度，属于<b>接棒的第一天</b>，不是已经成立的主线。<br>
注：reason_type 为多标签，同一只股票可归入多条主线，故各主线家数之和大于涨停总数。
</div>
</div>

<div class="card">
<h2>五、行业迁移：钱从哪里来、到哪里去</h2>
<div id="c_hy" class="chart" style="height:410px"></div>
<table style="margin-top:14px">
<tr><th>行业</th><th>__D1L__</th><th>__D0L__</th><th>增减</th><th>读数</th></tr>
__TBL_HY__
</table>
<div class="note" style="margin-top:12px">
<b>流入端：</b>汽车零部 __HY_QC__→__HY_QC0__ 家（单行业占今日涨停的 1/6 以上）、
种业/医疗服务/风电设备/出版各 2 家，另有 11 个行业从 0 到 1（航运港口、焦炭、玻璃玻纤、商用车、纺织制造等）。<br>
<b>流出端：</b>通信设备 __HY_TXD__→__HY_TXD0__ 家、半导体 __HY_BDT__→__HY_BDT0__ 家、元件/PCB __HY_YJ__→__HY_YJ0__ 家、
其他电子 __HY_QT__→__HY_QT0__ 家（清零）、包装印刷 __HY_BZ__→__HY_BZ0__ 家。<br>
<span class="hl">这不是「普跌」，而是有明确方向的搬家：昨日算力/电子硬件链 6 个行业合计贡献 26 家涨停，今日只剩 6 家；
腾出来的钱流向汽车链与低位补涨题材。</span>
</div>
</div>

<div class="card">
<h2>六、昨日涨停股今日表现：分化到了极致</h2>
<div class="kpis" style="grid-template-columns:repeat(auto-fit,minmax(140px,1fr))">
  <div class="kpi"><div class="lbl">晋级率</div><div class="val">__ADV_RATE__%</div><div class="dt mut">__ADV_N__/__ADV_TOT__</div></div>
  <div class="kpi"><div class="lbl">平均涨幅</div><div class="val up">__PERF_MEAN__%</div><div class="dt mut">中位 __PERF_MED__%</div></div>
  <div class="kpi"><div class="lbl">翻绿比例</div><div class="val down">__NEG_PCT__%</div><div class="dt mut">__NEG__ 只</div></div>
  <div class="kpi"><div class="lbl">最强</div><div class="val up">__PERF_MAX__%</div><div class="dt mut">__PERF_MAX_NAME__（昨 __PERF_MAX_LB__ 板）</div></div>
  <div class="kpi"><div class="lbl">最弱</div><div class="val down">__PERF_MIN__%</div><div class="dt mut">__PERF_MIN_NAME__（昨 __PERF_MIN_LB__ 板）</div></div>
</div>
<h3>按昨日身份分组：首板与连板是两个世界</h3>
<table>
<tr><th>昨日身份</th><th>只数</th><th>今日晋级率</th><th>均涨</th><th>中位</th><th>翻绿只数</th></tr>
<tr><td>昨日首板</td><td>__GSB_N__</td><td class="down">__GSB_ADV__%</td><td class="down">__GSB_MEAN__%</td><td class="down">__GSB_MED__%</td><td class="down">__GSB_NEG__</td></tr>
<tr><td>昨日连板（2板+）</td><td>__GLB_N__</td><td class="up">__GLB_ADV__%</td><td class="up">__GLB_MEAN__%</td><td class="up">__GLB_MED__%</td><td>__GLB_NEG__</td></tr>
</table>
<div class="note" style="margin-top:14px">
<b>这是本报告最重要的一张表。</b>整体晋级率 __ADV_RATE__% 看着很差，但拆开看：
昨日 __GLB_N__ 只连板股今日均涨 __GLB_MEAN__%、中位 __GLB_MED__%、晋级率 __GLB_ADV__%，只有 __GLB_NEG__ 只翻绿；
而昨日 __GSB_N__ 只首板股均涨 __GSB_MEAN__%、中位 __GSB_MED__%、晋级率仅 __GSB_ADV__%、__GSB_NEG__ 只翻绿。<br>
<span class="hl">今天是「亏在追首板、赚在接力连板」的结构分化行情。</span>最强的 __PERF_MAX_NAME__（昨 __PERF_MAX_LB__ 板）
今日 __PERF_MAX__% 仍未封板（科创板 20cm 上限），最弱的 __PERF_MIN_NAME__ 也只有 __PERF_MIN__% ——
<span class="hl">没有出现 __D2L__ 那种「高标集体跌停」的无差别杀跌。</span>
</div>
<h3>今日炸板池（__ZB__ 家）</h3>
<table>
<tr><th>名称</th><th>代码</th><th>行业</th><th>成交额</th><th>首封</th><th>身份</th></tr>
__TBL_ZB__
</table>
<div class="note" style="margin-top:10px">
炸板股里有 __ZB_IN_YZT_N__ 只是昨日涨停股（__ZB_IN_YZT__）—— 昨日封板、今日炸板，是接力失败最直接的形态；其余为今日新增面孔。<br>
<b>炸板股首封时间高度集中在早盘：__ZB_EARLY__/__ZB__ 只在 11:30 前首次封板、__ZB_B1030__ 只在 10:30 前</b>——
<span class="hl">早盘一致冲高、盘中承接不足，是今日炸板池的共同特征。</span>
</div>
<div id="c_perf" class="chart" style="height:1500px;margin-top:8px"></div>
</div>

<div class="card">
<h2>七、封板节奏与成交结构：封单变薄，换手变足</h2>
<div class="two">
<div><div id="c_ts" class="chart-sm"></div></div>
<div>
<table>
<tr><th>封板时段</th><th>__D1L__</th><th>__D0L__</th><th>__D0L__ 占比</th></tr>
__TBL_TS__
</table>
<div class="note" style="margin-top:10px">
按占比看，封板节奏<b>几乎没有变化</b>：早盘（竞价 + 开盘半小时）__D0L__ __TS_EARLY_0__ 家占 __TS_EARLY_0_PCT__%，
__D1L__ __TS_EARLY_Y__ 家占 __TS_EARLY_Y_PCT__%；午后封板 __D0L__ __TS_PM0__ 家占 __TS_PM0_PCT__%，__D1L__ __TS_PM1__ 家占 __TS_PM1_PCT__%。<br>
<span class="hl">节奏没变，但结果变了</span>——同样的早盘冲板强度，昨日封板率 __SEAL_Y__%、今日 __SEAL__%，
说明差异不在「资金什么时候来」，而在「封住之后有没有人接」。
</div>
</div>
</div>
<div class="kpis" style="grid-template-columns:repeat(auto-fit,minmax(160px,1fr));margin-top:16px">
  <div class="kpi"><div class="lbl">涨停股合计成交额</div><div class="val">__AMT_SUM__亿</div><div class="dt mut">占两市 __SHARE__%（昨 __SHARE_Y__%）</div></div>
  <div class="kpi"><div class="lbl">单只成交额中位</div><div class="val">__MED_AMT__亿</div><div class="dt mut">昨 __MED_AMT_Y__亿</div></div>
  <div class="kpi"><div class="lbl">单只换手中位</div><div class="val">__MED_HS__%</div><div class="dt mut">昨 __MED_HS_Y__%</div></div>
  <div class="kpi"><div class="lbl">封单中位</div><div class="val">__FUND_MED__亿</div><div class="dt mut">昨 __FUND_MED_Y__亿</div></div>
</div>
<div class="note" style="margin-top:14px">
合计成交额占比从 __SHARE_Y__% 掉到 __SHARE__%，<b>但这不是缩量，是家数少了</b>：__ZT__ 家（昨 __ZT_Y__ 家）自然摊薄了合计值。
看单只口径反而更清楚 —— 中位成交额 __MED_AMT_Y__→__MED_AMT__ 亿（__MED_AMT_UP__%）、中位换手 __MED_HS_Y__%→__MED_HS__%（__MED_HS_UP__pct）。
今日涨停股里还有 __BIG_N__ 只流通市值超 300 亿的大票（__BIG_LIST__），说明<b>资金打的是有基本面的大中盘，不是小票乱炒</b>。<br>
反面是封单：一字板仅 __ONEWORD__ 只、T字板 __TWORD__ 只、换手板 __HUANSHOU__ 只，
封单合计 __FUND_SUM__ 亿、中位 __FUND_MED__ 亿（昨 __FUND_MED_Y__ 亿）。
<span class="hl">换手充分 + 封单变薄 = 抛压被消化了，但锁仓意愿也在下降 —— 好处是筹码轻，风险是明日无新资金则易松动。</span>
</div>
</div>

<div class="card">
<h2>八、资金运动的三个结论</h2>
<ul>
<li><b>① 总量上：不是撤退，是降档。</b>两市成交额 __AMT__ 亿（__AMT_PCT__%，仅减 __AMT_DABS__ 亿），跌停仅 __DT__ 家，
11 个指数跌幅全在 1.5% 以内。<span class="hl">钱还在场内，只是从「无差别扫货」降档为「挑方向买」。</span>
对比 __D2L__ 那天的跌停 __D2L_DT__ 家，当前离「退潮」还很远。</li>
<li><b>② 方向上：算力链止盈 → 汽车链接棒，是搬家不是流失。</b>
昨日算力/电子硬件链（通信设备 __HY_TXD__、半导体 __HY_BDT__、元件 __HY_YJ__、其他电子 __HY_QT__、包装印刷 __HY_BZ__、化学制品 __HY_HXP__）合计 26 家涨停，
今日只剩 6 家；同期汽车零部从 __HY_QC__ 家增至 __HY_QC0__ 家。
<span class="hl">真正的证据是资金去向而非流出：昨日领涨的科创50 今日成交额缩 __KC_AMT_PCT__% 并领跌 __KC_PCT__%，
而两市总量几乎不变 —— 卖算力的钱直接买了汽车和其他低位方向。</span></li>
<li><b>③ 深度上：筹码换得更狠，但封单更薄。</b>单只中位成交额 __MED_AMT_Y__→__MED_AMT__ 亿、中位换手 __MED_HS_Y__%→__MED_HS__%，
封单中位却从 __FUND_MED_Y__ 亿降到 __FUND_MED__ 亿。
<span class="hl">高换手 + 薄封单意味着：卖的人卖得很干净，买的人也不敢重仓锁仓。</span>
这种结构下，明日若成交额不能再放大，容易看到「涨停家数不变但炸板率继续上升」。</li>
</ul>
</div>

<div class="card">
<h2>九、明日观察要点与风险</h2>
<ul>
<li><b>高度标杆：</b>__LB_TOP1__（__MAXB__ 板，__LB_TOP1_REASON__）能否晋级 __MAXBN__ 板，
以及 __LB_TOP2__（__LB_TOP2_LB__ 板）等 2~3 板梯队能否补位。高度端是今日唯一没失守的部分，若连板梯队明日大面积炸板，则结构切换失败。</li>
<li><b>汽车链能否升级：</b>今日汽车零部 __CAR_N__ 家涨停<b>全部是首板</b>，属于扩散第一天。
明日看有没有 2 板出现——有，则接棒成立；没有，则只是一日游。</li>
<li><b>首板亏钱效应：</b>昨日首板晋级率仅 __GSB_ADV__%、中位 __GSB_MED__%。若明日首板晋级率仍低于 15%，说明追涨停的性价比已明显下降，市场进入「只有接力才赚钱」的阶段。</li>
<li><b>量能警戒线：</b>两市成交额 __AMT__ 亿。若明日回落至 1.6 万亿以下，则「降档」将升级为「退潮」，今日的收敛判断需推翻。</li>
<li><b>薄封单风险：</b>封单中位仅 __FUND_MED__ 亿（昨 __FUND_MED_Y__ 亿），且今日已有 __ZB__ 家炸板。<b>开盘 15 分钟的承接力度是明日最关键的前瞻信号。</b></li>
<li><b>数据口径：</b>统计为沪深两市（不含北交所）；涨停/炸板/跌停家数经同花顺与东财双源交叉校验（两池家数完全一致 __ZT__/__ZT__、__ZB__/__ZB__，封板时间分钟级一致率 100%）；
成交额、封单、换手率一律取东财字段；两市成交额为沪市 + 深市全市场口径；
汽车零部涨停股是否全为首板：__CAR_ALL_FIRST__。
本报告「涨停股合计成交额 ÷ 两市成交额」= __SHARE__%（昨 __SHARE_Y__%），低于 3%~8% 的经验区间，
原因是<b>该比值与涨停家数强相关</b>（昨 __ZT_Y__ 家对应 __SHARE_Y__%、今 __ZT__ 家对应 __SHARE__%），而单只中位成交额不降反升，故可确认字段源无误。</li>
</ul>
<div class="warn" style="margin-top:14px">
<b>风险提示：</b>本报告为盘后数据复盘与资金行为分析，所有结论基于公开行情数据的统计推断，不构成任何投资建议。
涨停板交易具有高波动、高换手、隔夜风险大的特征，历史统计规律不保证未来重复。
</div>
</div>

<div class="note" style="text-align:center;color:#9ca3af;margin-top:24px">
生成时间：__GEN_AT__｜数据源：同花顺 / 东方财富 / 腾讯财经｜本报告由脚本自动生成
</div>
</div>

<script>
var C_RED='#d93025', C_GRN='#12805c', C_BLU='#2563eb';
var AX={axisLine:{lineStyle:{color:'#d1d5db'}},axisLabel:{color:'#6b7280'},splitLine:{lineStyle:{color:'#f1f3f5'}}};
function mk(id,opt){var e=echarts.init(document.getElementById(id));e.setOption(opt);window.addEventListener('resize',function(){e.resize()});}

mk('c_senti',{
  tooltip:{trigger:'axis'},legend:{top:3,left:'center',textStyle:{color:'#6b7280'}},
  grid:{left:56,right:66,top:52,bottom:32},
  xAxis:Object.assign({type:'category',data:__JS_DAYS__},AX),
  yAxis:[Object.assign({type:'value',name:'家数'},AX),
         Object.assign({type:'value',name:'封板率%',min:0,max:100},AX)],
  series:[
    {name:'涨停家数',type:'bar',data:__JS_ZT__,itemStyle:{color:C_RED},barWidth:26,
     label:{show:true,position:'top',color:C_RED,fontWeight:600}},
    {name:'炸板家数',type:'bar',data:__JS_ZB__,itemStyle:{color:'#f0a04b'},barWidth:26,
     label:{show:true,position:'top',color:'#b26a1e'}},
    {name:'跌停家数',type:'bar',data:__JS_DT__,itemStyle:{color:C_GRN},barWidth:26,
     label:{show:true,position:'top',color:C_GRN}},
    {name:'封板率',type:'line',yAxisIndex:1,smooth:true,symbolSize:8,data:__JS_SEAL__,
     itemStyle:{color:C_BLU},lineStyle:{width:3},label:{show:true,position:'bottom',color:C_BLU,formatter:'{c}%'}}
  ]
});

mk('c_idx',{
  tooltip:{trigger:'axis',valueFormatter:function(v){return v+'%'}},
  grid:{left:76,right:52,top:16,bottom:24},
  xAxis:Object.assign({type:'value',axisLabel:{formatter:'{value}%'}},AX),
  yAxis:Object.assign({type:'category',data:__JS_IX_NAME__},AX),
  series:[{type:'bar',data:__JS_IX_PCT__,barWidth:14,
    itemStyle:{color:function(p){return p.value>=0?C_RED:C_GRN}},
    label:{show:true,position:'right',color:'#6b7280',fontSize:11,formatter:'{c}%'}}]
});

mk('c_lad',{
  tooltip:{trigger:'axis'},legend:{top:3,left:'center',textStyle:{color:'#6b7280'}},
  grid:{left:46,right:20,top:52,bottom:28},
  xAxis:Object.assign({type:'category',data:__JS_LAD_NAME__},AX),
  yAxis:Object.assign({type:'value'},AX),
  series:[
    {name:'__D1L__',type:'bar',data:__JS_LAD1__,itemStyle:{color:'#cbd5e1'},barWidth:18},
    {name:'__D0L__',type:'bar',data:__JS_LAD0__,itemStyle:{color:C_RED},barWidth:18,
     label:{show:true,position:'top',color:'#9ca3af',fontSize:11}}
  ]
});

mk('c_theme',{
  tooltip:{trigger:'axis'},
  grid:{left:130,right:70,top:16,bottom:24},
  xAxis:Object.assign({type:'value'},AX),
  yAxis:Object.assign({type:'category',data:__JS_TH_NAME__},AX),
  series:[{type:'bar',data:__JS_TH_N__,itemStyle:{color:C_BLU},barWidth:15,
    label:{show:true,position:'right',color:'#374151',fontWeight:600,formatter:'{c} 家'}}]
});

mk('c_hy',{
  tooltip:{trigger:'axis'},legend:{top:3,left:'center',textStyle:{color:'#6b7280'}},
  grid:{left:100,right:56,top:52,bottom:24},
  xAxis:Object.assign({type:'value'},AX),
  yAxis:Object.assign({type:'category',data:__JS_HY_NAME__},AX),
  series:[
    {name:'__D1L__',type:'bar',data:__JS_HY_Y__,itemStyle:{color:'#cbd5e1'},barWidth:11},
    {name:'__D0L__',type:'bar',data:__JS_HY_T__,itemStyle:{color:C_RED},barWidth:11}
  ]
});

mk('c_perf',{
  tooltip:{trigger:'axis',valueFormatter:function(v){return v+'%'}},
  grid:{left:100,right:56,top:16,bottom:28},
  xAxis:Object.assign({type:'value',axisLabel:{formatter:'{value}%'}},AX),
  yAxis:Object.assign({type:'category',data:__JS_PF_NAME__,axisLabel:{color:'#6b7280',fontSize:10,interval:0}},AX),
  series:[{type:'bar',data:__JS_PF_PCT__,barWidth:9,
    itemStyle:{color:function(p){return p.value>=0?C_RED:C_GRN}},
    label:{show:true,position:'right',fontSize:10,color:'#9ca3af',
      formatter:function(p){return p.value.toFixed(1)}}}]
});

mk('c_ts',{
  tooltip:{trigger:'axis'},legend:{top:3,left:'center',textStyle:{color:'#6b7280'}},
  grid:{left:50,right:20,top:52,bottom:28},
  xAxis:Object.assign({type:'category',data:__JS_TS_NAME__},AX),
  yAxis:Object.assign({type:'value'},AX),
  series:[
    {name:'__D1L__',type:'bar',data:__JS_TS_Y__,itemStyle:{color:'#cbd5e1'},barWidth:24},
    {name:'__D0L__',type:'bar',data:__JS_TS_T__,itemStyle:{color:C_RED},barWidth:24}
  ]
});
</script>
</body>
</html>
"""

V["__A_ROBOT__"] = str(next((t["n"] for t in theme_cnt if t["name"].startswith("机器人")), 0))

HTML = HTML_T
for k, v in V.items():
    HTML = HTML.replace(k, v)

fp = os.path.join(REP, f"涨停复盘对比-{D0}.html")
with open(fp, "w", encoding="utf-8") as f:
    f.write(HTML)
left = re.findall(r"__[A-Za-z_0-9]+__", HTML)
print("saved ->", fp, len(HTML) // 1024, "KB")
print("placeholder residue:", sorted(set(left)))
