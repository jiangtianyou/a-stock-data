# -*- coding: utf-8 -*-
"""涨停复盘报告 20260921 vs 20260918（放量扩张→缩量扩散 / 医药链接棒）

用法：python zt_report_20260921.py 20260921
输入：out/zt_stats_20260921.json、out/zt_review_20260921.json
输出：reports/涨停复盘对比-20260921.html
"""
import json, os, sys, collections, html, re
from statistics import mean, median

ROOT = os.environ.get("ZT_ROOT") or os.getcwd()
OUT = os.path.join(ROOT, "out")
REP = os.path.join(ROOT, "reports")
os.makedirs(REP, exist_ok=True)

S = json.load(open(os.path.join(OUT, f"zt_stats_{sys.argv[1]}.json"), encoding="utf-8"))
D0, D1, D2 = S["D0"], S["D1"], S["D2"]
B = json.load(open(os.path.join(OUT, f"zt_review_{D0}.json"), encoding="utf-8"))
r0, r1 = S["r0"], S["r1"]
perf = S["perf"]
s0, s1 = S["senti"][D0], S["senti"][D1]


def md(ds):
    return f"{int(ds[4:6])}/{int(ds[6:8])}"


def esc(s):
    return html.escape(str(s))


def hhmm(v):
    s = str(int(v)).zfill(6)
    return s[:2] + ":" + s[2:4]


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
            ("上证50", "sh000016")]
idx_now = {v["name"]: v for v in B["indexes"].values()}
ix = []
for nm, sym in IX_ORDER:
    v = idx_now.get(nm)
    if v:
        ix.append({"name": nm, "pct": v["pct"], "amt": (v["amount_wan"] or 0) / 10000.0,
                   "price": v["price"]})
ixr = {x["name"]: x for x in ix}
PREV_IDX_PCT = {k: (v.get("prev_pct") or 0.0) for k, v in (S.get("idx_cmp") or {}).items()}

amt_today = ixr["上证指数"]["amt"] + ixr["深证成指"]["amt"]
tot = S.get("tot") or {}
amt_prev = tot.get("prev") or amt_today
amt_pct = (amt_today / amt_prev - 1) * 100 if amt_prev else 0.0
kc = ixr.get("科创50", {})
kc_prev_amt = (S.get("idx_cmp") or {}).get("科创50", {}).get("prev_amt") or kc.get("amt", 1)
kc_amt_pct = (kc.get("amt", 0) / kc_prev_amt - 1) * 100 if kc_prev_amt else 0.0
# 指数涨跌幅两日差（用于风格判断）
pct_delta = {k: v["pct"] - PREV_IDX_PCT.get(k, 0) for k, v in ixr.items()}

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
perf_sorted = sorted(perf, key=lambda x: -(x["pct"] if x["pct"] is not None else -999))
top3 = perf_sorted[:3]
bot3 = perf_sorted[-3:]
# 分层
p_shou = [p for p in perf if (p["lbc"] or 1) == 1]
p_lian = [p for p in perf if (p["lbc"] or 1) >= 2]


def grp(rows):
    n = len(rows)
    if not n:
        return 0, 0.0, 0.0
    a = sum(1 for p in rows if p["again"])
    pp = [p["pct"] for p in rows if p["pct"] is not None]
    return n, a / n * 100, median(pp)


n_s, r_s, m_s = grp(p_shou)
n_l, r_l, m_l = grp(p_lian)

# ---- 成交额结构 ----
amts = [r["amount"] for r in r0 if r["amount"]]
amts1 = [r["amount"] for r in r1 if r["amount"]]
funds = [r["fund"] for r in r0 if r["fund"]]
funds1 = [r["fund"] for r in r1 if r["fund"]]
amt_sum, amt_sum1 = sum(amts) / 1e8, sum(amts1) / 1e8
fund_sum, fund_sum1 = sum(funds) / 1e8, sum(funds1) / 1e8
share = amt_sum / amt_today * 100
share1 = amt_sum1 / amt_prev * 100
oneword = sum(1 for r in r0 if "一字" in r["limit_up_type"])
huanshou = sum(1 for r in r0 if "换手" in r["limit_up_type"])
oneword1 = sum(1 for r in r1 if "一字" in r["limit_up_type"])
huanshou1 = sum(1 for r in r1 if "换手" in r["limit_up_type"])
# 封单集中度：最大单只
fund_top = sorted(r0, key=lambda x: -(x["fund"] or 0))[:3]
fund_top1 = sum((x["fund"] or 0) for x in fund_top) / 1e8
fund_ex = fund_sum - fund_top1  # 剔除前三后
fund_top_name = fund_top[0]["name"]
fund_top_val = (fund_top[0]["fund"] or 0) / 1e8
fund_top_pct = fund_top_val / fund_sum * 100

# ---- 主线归因（多标签，家数之和 > 总数）----
THEMES = [
    ("医药医疗", ["创新药", "医药", "医疗", "中药", "体外诊断", "CRO", "脑机", "细胞", "抗感染",
                  "肿瘤", "口腔", "康复", "阿尔茨海默", "基因", "医疗器械", "精麻", "抗生素",
                  "流感", "合成生物"]),
    ("AI算力/电子硬件", ["算力", "PCB", "服务器", "光通信", "光模块", "数据中心", "交换机", "液冷",
                         "端侧AI", "存储芯片", "半导体", "消费电子", "芯片", "光刻", "先进封装", "显示面板"]),
    ("国资/股权变更", ["国资", "央企", "国企", "控制权", "股权转让", "股份转让", "控股变更",
                       "资产重组", "复牌", "借壳", "入主", "划转"]),
    ("消费零售", ["零售", "百货", "家居", "家具", "服装", "家纺", "食品", "黄酒", "白酒", "珠宝",
                  "旅游", "纺织", "羽绒", "养殖", "猪", "粮油", "皮鞋", "皮革", "户外", "餐厨"]),
    ("化工材料", ["化学", "新材料", "锆", "锶", "玻纤", "聚酯", "薄膜", "染料", "偏光片", "铝",
                  "锂", "钢丝绳", "贵金属", "铜箔", "海绵锆"]),
    ("地产链", ["房地产", "城市更新", "物业", "房产经纪", "旧改", "装修"]),
    ("机器人/智造", ["机器人", "具身智能", "人形", "3D打印", "精密金属", "执行器"]),
    ("出版传媒", ["出版", "传媒", "教育", "游戏", "文化", "影视", "数字内容"]),
    ("电力电网", ["电力", "电网", "热电", "电缆", "风电", "光伏", "储能", "输电"]),
]
theme_cnt = []
for nm, kws in THEMES:
    hit = [r for r in r0 if any(k in (r["reason"] or "") for k in kws)]
    theme_cnt.append({"name": nm, "n": len(hit),
                      "stocks": [r["name"] + "(" + str(r["lbc"] or 1) + "板)" for r in
                                 sorted(hit, key=lambda x: (-(x["lbc"] or 0), -(x["amount"] or 0)))][:8]})
theme_cnt.sort(key=lambda x: -x["n"])
med_theme = theme_cnt[0]

# ---- 连板股 ----
lb_all = sorted([r for r in r0 if (r["lbc"] or 1) >= 2], key=lambda x: -(x["lbc"] or 0))
maxb = max(lad0) if lad0 else 0
maxb_y = max(lad1) if lad1 else 0

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
    "<tr><td>{0}</td><td>{1}</td><td class='hl'>{2}</td></tr>".format(k, ts1.get(k, 0), ts0.get(k, 0))
    for k in TS_ORDER)

tbl_theme = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td style='text-align:left'>{2}</td></tr>".format(
        esc(t["name"]), t["n"], "".join("<span class=tag>" + esc(s) + "</span>" for s in t["stocks"]))
    for t in theme_cnt if t["n"] > 0)

tbl_idx = "".join(
    "<tr><td>{0}</td><td class='{1}'>{2:+.2f}%</td><td class='{3}'>{4}</td><td>{5:,.0f}亿</td></tr>".format(
        esc(x["name"]), "up" if x["pct"] >= 0 else "down", x["pct"],
        "up" if PREV_IDX_PCT.get(x["name"], 0) >= 0 else "down",
        ("{:+.2f}%".format(PREV_IDX_PCT[x["name"]]) if x["name"] in PREV_IDX_PCT else "—"),
        x["amt"])
    for x in ix)


def fmtv(v):
    return "{:.1f}".format(v) if isinstance(v, float) else str(v)


def fmtd(v):
    return ("{:+.1f}" if isinstance(v, float) else "{:+d}").format(v)


tbl_senti = "".join(
    "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td class='hl'>{3}</td><td class='up'>{4}</td></tr>".format(
        lab, fmtv(days[0][k]), fmtv(days[1][k]), fmtv(days[2][k]), fmtd(days[2][k] - days[1][k]))
    for lab, k in [("涨停家数", "zt"), ("炸板家数", "zb"), ("封板率(%)", "seal"), ("跌停家数", "dt")])

perf_top = "、".join("{}{:+.1f}%".format(esc(p["name"]), p["pct"]) for p in top3)
perf_bot = "、".join("{}{:+.1f}%".format(esc(p["name"]), p["pct"]) for p in bot3)

# ================= 占位符 =================
V = {}


def P(k, v):
    V["__" + k + "__"] = str(v)


P("GEN_AT", B["generated_at"])
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
P("AMT", "{:,.0f}".format(amt_today)); P("AMT_Y", "{:,.0f}".format(amt_prev))
P("AMT_D", "{:+,.0f}".format(amt_today - amt_prev)); P("AMT_PCT", "{:+.1f}".format(amt_pct))
P("KC_PCT", "{:+.2f}".format(kc.get("pct", 0)))
P("KC_AMT", "{:,.0f}".format(kc.get("amt", 0)))
P("KC_AMT_PCT", "{:+.1f}".format(kc_amt_pct))
P("KC_AMT_PREV", "{:,.0f}".format(kc_prev_amt))
P("SZ50_PCT", "{:+.2f}".format(ixr.get("上证50", {}).get("pct", 0)))
P("ADV_RATE", "{:.1f}".format(adv_rate)); P("ADV_N", len(adv)); P("ADV_TOT", len(perf))
P("PERF_MEAN", "{:+.2f}".format(mean(pcts))); P("PERF_MED", "{:+.2f}".format(median(pcts)))
P("PERF_MAX", "{:+.2f}".format(max(pcts))); P("PERF_MIN", "{:+.2f}".format(min(pcts)))
P("PERF_MAX_NAME", esc(perf_sorted[0]["name"]))
P("PERF_MIN_NAME", esc(perf_sorted[-1]["name"]))
P("PERF_MIN_LB", perf_sorted[-1]["lbc"])
P("PERF_TOP3", perf_top); P("PERF_BOT3", perf_bot)
P("NEG", neg); P("NEG_PCT", "{:.1f}".format(neg / len(pcts) * 100))
P("AMT_SUM", "{:.0f}".format(amt_sum)); P("SHARE", "{:.1f}".format(share))
P("AMT_SUM_Y", "{:.0f}".format(amt_sum1)); P("SHARE_Y", "{:.1f}".format(share1))
P("FUND_SUM", "{:.1f}".format(fund_sum)); P("FUND_SUM_Y", "{:.1f}".format(fund_sum1))
P("FUND_MED", "{:.2f}".format(median(funds) / 1e8))
P("FUND_MED_Y", "{:.2f}".format(median(funds1) / 1e8))
P("FUND_AVG", "{:.2f}".format(fund_sum / s0["zt"]))
P("ONEWORD", oneword); P("ONEWORD_Y", oneword1); P("ONEWORD_PCT", "{:.1f}".format(oneword / s0["zt"] * 100))
P("HUANSHOU", huanshou); P("HUANSHOU_Y", huanshou1)
P("HUANSHOU_PCT", "{:.0f}".format(huanshou / s0["zt"] * 100))
P("FUND_TOP_NAME", esc(fund_top[0]["name"]))
P("FUND_TOP_VAL", "{:.1f}".format(fund_top_val))
P("FUND_TOP_PCT", "{:.1f}".format(fund_top_pct))
P("FUND_TOP3_VAL", "{:.1f}".format(fund_top1))
P("FUND_EX", "{:.1f}".format(fund_ex))
P("LB_TOP1", esc(lb_all[0]["name"])); P("LB_TOP1_REASON", esc(lb_all[0]["reason"]))
P("LB_TOP2", esc(lb_all[1]["name"])); P("LB_TOP2_LB", lb_all[1]["lbc"])
P("MEDTHEME", esc(med_theme["name"])); P("MEDTHEME_N", med_theme["n"])
P("MEDTHEME_PCT", "{:.1f}".format(med_theme["n"] / s0["zt"] * 100))
P("ADV_S_N", n_s); P("ADV_S_RATE", "{:.1f}".format(r_s)); P("ADV_S_MED", "{:+.2f}".format(m_s))
P("ADV_L_N", n_l); P("ADV_L_RATE", "{:.1f}".format(r_l)); P("ADV_L_MED", "{:+.2f}".format(m_l))
P("TH_AI_N", next(t["n"] for t in theme_cnt if t["name"].startswith("AI算力")))
P("ZT_D2", days[0]["zt"])
_amt_top = sorted(r0, key=lambda x: -(x["amount"] or 0))[:3]
P("AMT_TOP1", esc(_amt_top[0]["name"])); P("AMT_TOP1_V", "{:.1f}".format((_amt_top[0]["amount"] or 0) / 1e8))
P("AMT_TOP2", esc(_amt_top[1]["name"])); P("AMT_TOP2_V", "{:.1f}".format((_amt_top[1]["amount"] or 0) / 1e8))
P("AMT_TOP3", esc(_amt_top[2]["name"])); P("AMT_TOP3_V", "{:.1f}".format((_amt_top[2]["amount"] or 0) / 1e8))
for _b in (2, 3, 4, 5):
    P("LAD{}_T".format(_b), lad0.get(_b, 0)); P("LAD{}_Y".format(_b), lad1.get(_b, 0))
_med_top = sorted([r for r in r0 if any(k in (r["reason"] or "") for k in
                   ["创新药", "医药", "医疗", "中药", "体外诊断", "CRO", "脑机", "细胞", "抗感染",
                    "肿瘤", "口腔", "康复", "基因", "医疗器械", "精麻", "抗生素", "流感"])],
                  key=lambda x: -(x["lbc"] or 0))
P("MED_TOP_NAME", esc(_med_top[0]["name"])); P("MED_TOP_LB", _med_top[0]["lbc"])
# 行业
for nm, key in [("化学制药", "YIYAO"), ("医疗服务", "MEDSVC"), ("医疗器械", "MEDDEV"),
                ("半导体", "BDT"), ("电网设备", "DW"), ("房地产开", "FDCK"),
                ("房地产服", "FDCF"), ("化学制品", "HXP"), ("出版", "CB")]:
    P("HY_" + key, hy0.get(nm, 0)); P("HY_" + key + "_Y", hy1.get(nm, 0))
# 指数风格差
P("IX_SZ50_D", "{:+.2f}".format(pct_delta.get("上证50", 0)))
P("IX_KC_D", "{:+.2f}".format(pct_delta.get("科创50", 0)))
P("IX_GZ2000_PCT", "{:+.2f}".format(ixr.get("国证2000", {}).get("pct", 0)))
P("IX_ZZ1000_PCT", "{:+.2f}".format(ixr.get("中证1000", {}).get("pct", 0)))
P("IX_CYB_PCT", "{:+.2f}".format(ixr.get("创业板指", {}).get("pct", 0)))
P("ZTDT_Y_DISP", "—" if not s1["dt"] else "{:.1f}".format(s1["zt"] / s1["dt"]))
P("TS_EARLY", ts0.get("竞价/秒板", 0) + ts0.get("开盘半小时", 0))
P("TS_EARLY_PCT", "{:.0f}".format((ts0.get("竞价/秒板", 0) + ts0.get("开盘半小时", 0)) / s0["zt"] * 100))
P("TS_EARLY_Y", ts1.get("竞价/秒板", 0) + ts1.get("开盘半小时", 0))
P("TS_EARLY_Y_PCT", "{:.0f}".format((ts1.get("竞价/秒板", 0) + ts1.get("开盘半小时", 0)) / s1["zt"] * 100))
P("TS_PM0", ts0.get("午后盘中", 0)); P("TS_PM1", ts1.get("午后盘中", 0))
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
P("L_D1", md(D1)); P("L_D0", md(D0)); P("L_D2", md(D2))

# ================= HTML =================
HTML_T = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>涨停复盘 · 2026-09-21（对比 9-18）</title>
<script src="../assets/echarts.min.js"></script>
<script>if(typeof echarts==='undefined'){document.write('<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"><\\/script>');}</script>
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
<h1>涨停复盘 · 2026-09-21（周一）</h1>
<div class="sub">对比基准：2026-09-18（周五）｜口径：沪深两市（不含北交所）｜数据源：同花顺涨停池 + 东方财富涨停/炸板池 + 行情快照</div>

<div class="lead">
<p class="hl">一句话结论：情绪继续升温，但不是靠增量——涨停 __ZT__ 家（昨 __ZT_Y__ 家，__ZT_D__）、封板率 __SEAL__%（昨 __SEAL_Y__%，__SEAL_D__pct），
而两市成交额反而环比 __AMT_PCT__%。家数扩张来自存量资金向低位扩散，不是新钱进场。</p>
<p>风格出现明显换挡：成长权重减速（科创50 __KC_PCT__%，前一日 __KC_AMT_PREV__ 亿成交今缩至 __KC_AMT__ 亿），
小微盘与低位补涨接棒（国证2000 __IX_GZ2000_PCT__%、中证1000 __IX_ZZ1000_PCT__%，均跑赢创业板指 __IX_CYB_PCT__%）。
板块层面是<span class="hl">「科技硬件退潮、医药链集体爆发」</span>——医药医疗 __MEDTHEME_N__ 家（占涨停 __MEDTHEME_PCT__%），
而半导体 __HY_BDT_Y__→__HY_BDT__ 家、电网设备 __HY_DW_Y__→__HY_DW__ 家。
梯队高度由 __MAXB_Y__ 板升到 __MAXB__ 板（__LB_TOP1__），昨涨停股晋级率 __ADV_RATE__%（连板组 __ADV_L_RATE__%、首板组 __ADV_S_RATE__%）。
<span class="hl">赚钱效应集中在少数高标，首板承接只能算及格。</span></p>
</div>

<div class="kpis">
  <div class="kpi"><div class="lbl">涨停家数</div><div class="val up">__ZT__</div>
    <div class="dt mut">昨日 __ZT_Y__ <span class="up">__ZT_D__</span></div></div>
  <div class="kpi"><div class="lbl">封板率</div><div class="val">__SEAL__%</div>
    <div class="dt mut">昨日 __SEAL_Y__% <span class="up">__SEAL_D__pct</span></div></div>
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
<h2>一、市场情绪温度计：连续第二日修复，但斜率放缓</h2>
<table>
<tr><th>指标</th><th>__L_D2__（周四）</th><th>__L_D1__（周五）</th><th>__L_D0__（周一）</th><th>__L_D0__ 环比</th></tr>
__TBL_SENTI__
<tr><td>涨停/跌停比</td><td>__ZTDT_0__</td><td>__ZTDT_Y_DISP__</td><td class="hl">__ZTDT__</td><td class="up">高位维持</td></tr>
</table>
<div class="note" style="margin-top:10px">
三日序列读下来是「收敛（__L_D2__ 涨停 __ZT_D2__ 家）→ 放量扩张（__L_D1__）→ 缩量扩散（__L_D0__）」。
今日涨停 __ZT__ 家、封板率 __SEAL__% 均为阶段新高，炸板 __ZB__ 家与前日持平（__ZB_Y__ 家），
说明<span class="hl">封板质量在改善而非靠分时反复纠缠</span>；但跌停由 __DT_Y__ 家回升到 __DT__ 家，是本轮修复以来第一个负向边际变化。
</div>
<div id="c_senti" class="chart" style="margin-top:16px"></div>
</div>

<div class="card">
<h2>二、指数与量能：没有增量，风格从「大成长」切向「小微盘」</h2>
<div class="two">
<div>
<table>
<tr><th>指数</th><th>今日</th><th>昨日</th><th>成交额</th></tr>
__TBL_IDX__
</table>
<div class="note" style="margin-top:10px">
<b>量能是本次判断的关键：</b>两市成交额 __AMT__ 亿，环比 __AMT_D__ 亿（__AMT_PCT__%）——<span class="hl">在涨停家数增加 __ZT_D__ 家的同时成交额是缩的</span>，
这直接说明扩张来自存量腾挪而非增量资金。结构上更清楚：科创50 成交额从 __KC_AMT_PREV__ 亿降到 __KC_AMT__ 亿（__KC_AMT_PCT__%），
而国证2000、中证1000 涨幅领先、上证50 也涨 __SZ50_PCT__%——<span class="hl">资金从高波动的成长硬件撤出，向中低位与权重两头分流。</span>
</div>
</div>
<div><div id="c_idx" class="chart-sm"></div></div>
</div>
</div>

<div class="card">
<h2>三、连板梯队：高度打开到 __MAXB__ 板，中位梯队同步填充</h2>
<div class="two">
<div><div id="c_lad" class="chart-sm"></div></div>
<div>
<table>
<tr><th>梯队</th><th>__L_D1__</th><th>__L_D0__</th><th>变化</th></tr>
__TBL_LAD__
<tr><td>合计</td><td>__ZT_Y__</td><td class="hl">__ZT__</td><td class="up">__ZT_D__</td></tr>
</table>
<div class="note" style="margin-top:10px">
首板 __SB__ 家（昨 __SB_Y__），连板股 __LB__ 家（昨 __LB_Y__），最高 __MAXB__ 板（__LB_TOP1__，__LB_TOP1_REASON__），昨日为 __MAXB_Y__ 板。
<span class="hl">与 __L_D1__ 那次「首板独大、中位空档」不同，今日 2/3/5 板三个档位同时增加（2板 __LAD2_Y__→__LAD2_T__、3板 __LAD3_Y__→__LAD3_T__、5板 __LAD5_Y__→__LAD5_T__）</span>，
梯队是「纺锤形填充」而非金字塔尖独苗——这是可持续性更好的结构，但也意味着高位股的分歧点被推后。
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
<h2>四、主线归因：医药链一日接棒，科技硬件退居次席</h2>
<div id="c_theme" class="chart"></div>
<table style="margin-top:14px">
<tr><th>主线</th><th>涨停家数</th><th>代表个股</th></tr>
__TBL_THEME__
</table>
<div class="note" style="margin-top:12px">
今日最拥挤方向是<span class="hl">医药医疗 __MEDTHEME_N__ 家</span>（创新药 / 化学制药 / 医疗器械 / 中药 / 体外诊断几乎全链条开花），
对应东财行业「化学制药 __HY_YIYAO_Y__→__HY_YIYAO__ 家、医疗服务 __HY_MEDSVC_Y__→__HY_MEDSVC__ 家、医疗器械 __HY_MEDDEV_Y__→__HY_MEDDEV__ 家」。
这是典型的<span class="hl">低位防御 + 政策/业绩预期</span>的双重驱动，特征是没有 3 板以上高标（最高仅 __MED_TOP_NAME__ __MED_TOP_LB__ 板），
说明资金在做「广度」而非「高度」，需要警惕一日游。<br>
AI算力/电子硬件仍占 __TH_AI_N__ 家上下（多标签口径），但内部分化：成设备件退潮，材料与 PCB 上游仍有大额资金
（__AMT_TOP1__ __AMT_TOP1_V__ 亿、__AMT_TOP2__ __AMT_TOP2_V__ 亿、__AMT_TOP3__ __AMT_TOP3_V__ 亿）。<br>
注：reason_type 为多标签，同一只股票可归入多条主线，故各主线家数之和大于涨停总数（__ZT__）。
</div>
</div>

<div class="card">
<h2>五、行业迁移：钱从哪里来、到哪里去</h2>
<div id="c_hy" class="chart" style="height:410px"></div>
<table style="margin-top:14px">
<tr><th>行业</th><th>__L_D1__</th><th>__L_D0__</th><th>增减</th><th>读数</th></tr>
__TBL_HY__
</table>
<div class="note" style="margin-top:12px">
<b>流入端：</b>化学制药 __HY_YIYAO_Y__→__HY_YIYAO__ 家、医疗服务 __HY_MEDSVC_Y__→__HY_MEDSVC__ 家、医疗器械 __HY_MEDDEV_Y__→__HY_MEDDEV__ 家、
房地产开 __HY_FDCK_Y__→__HY_FDCK__ 家、房地产服 __HY_FDCF_Y__→__HY_FDCF__ 家。<br>
<b>流出端：</b>电网设备从 __HY_DW_Y__ 家塌到 __HY_DW__ 家、半导体 __HY_BDT_Y__→__HY_BDT__ 家、化学制品 __HY_HXP_Y__→__HY_HXP__ 家。
<span class="hl">__L_D1__ 的主线（电网设备 + 半导体）在今日几乎被清空，资金整体搬到医药与地产链</span>——注意这不是"高低切换"，
而是<span class="hl">"跨板块换赛道"</span>：昨日领涨方向是电子制造，今日领涨方向是医药，两者几乎无重叠。
</div>
</div>

<div class="card">
<h2>六、昨日涨停股今日表现：连板溢价极高，首板只能算及格</h2>
<div class="kpis" style="grid-template-columns:repeat(auto-fit,minmax(140px,1fr))">
  <div class="kpi"><div class="lbl">晋级率</div><div class="val">__ADV_RATE__%</div><div class="dt mut">__ADV_N__/__ADV_TOT__</div></div>
  <div class="kpi"><div class="lbl">平均涨幅</div><div class="val up">__PERF_MEAN__%</div><div class="dt mut">中位 __PERF_MED__%</div></div>
  <div class="kpi"><div class="lbl">翻绿比例</div><div class="val down">__NEG_PCT__%</div><div class="dt mut">__NEG__ 只</div></div>
  <div class="kpi"><div class="lbl">最强</div><div class="val up">__PERF_MAX__%</div><div class="dt mut">__PERF_MAX_NAME__</div></div>
  <div class="kpi"><div class="lbl">最弱</div><div class="val down">__PERF_MIN__%</div><div class="dt mut">__PERF_MIN_NAME__（昨 __PERF_MIN_LB__ 板）</div></div>
</div>
<div class="note" style="margin-top:14px">
分层看分化极大：<b>昨日首板 n=__ADV_S_N__ 晋级率 __ADV_S_RATE__%、中位 __ADV_S_MED__%；昨日连板 n=__ADV_L_N__ 晋级率 __ADV_L_RATE__%、中位 __ADV_L_MED__%</b>。
连板组中位接近涨停、晋级率三分之二，说明<span class="hl">高标接力意愿很强</span>；
但首板组中位仅 __ADV_S_MED__%、翻绿 __NEG__ 只（__NEG_PCT__%），<span class="hl">昨日首板买入者今日大概率赚不到钱</span>。
最弱三只为 __PERF_BOT3__——集中在前期最强的电网设备与算力硬件，正是今日被切换掉的方向。
</div>
<div id="c_perf" class="chart" style="height:700px;margin-top:8px"></div>
</div>

<div class="card">
<h2>七、封板节奏与成交结构：节奏后移，封单在变薄</h2>
<div class="two">
<div><div id="c_ts" class="chart-sm"></div></div>
<div>
<table>
<tr><th>封板时段</th><th>__L_D1__</th><th>__L_D0__</th></tr>
__TBL_TS__
</table>
<div class="note" style="margin-top:10px">
早盘封板占比从 __TS_EARLY_Y_PCT__%（__TS_EARLY_Y__/__ZT_Y__）回落到 __TS_EARLY_PCT__%（__TS_EARLY__/__ZT__），
午后封板 __TS_PM1__→__TS_PM0__ 家。<span class="hl">节奏温和后移，配合封板率上升到 __SEAL__%</span>，
说明不是开盘一把梭的脉冲，而是盘中不断有新资金接力——量能是缩的，但接力的广度在扩大。
</div>
</div>
</div>
<div class="kpis" style="grid-template-columns:repeat(auto-fit,minmax(160px,1fr));margin-top:16px">
  <div class="kpi"><div class="lbl">涨停股合计成交额</div><div class="val">__AMT_SUM__亿</div><div class="dt mut">占两市 __SHARE__%（昨 __SHARE_Y__%）</div></div>
  <div class="kpi"><div class="lbl">封单合计</div><div class="val">__FUND_SUM__亿</div><div class="dt mut">昨 __FUND_SUM_Y__亿</div></div>
  <div class="kpi"><div class="lbl">封单中位数</div><div class="val">__FUND_MED__亿</div><div class="dt mut">昨 __FUND_MED_Y__亿</div></div>
  <div class="kpi"><div class="lbl">一字板 / 换手板</div><div class="val">__ONEWORD__ / __HUANSHOU__</div><div class="dt mut">换手板占 __HUANSHOU_PCT__%</div></div>
</div>
<div class="note" style="margin-top:14px">
封单合计从 __FUND_SUM_Y__ 亿跳到 __FUND_SUM__ 亿，但<span class="hl">其中 __FUND_TOP_NAME__ 一只就占 __FUND_TOP_VAL__ 亿（__FUND_TOP_PCT__%）</span>，
前三只合计 __FUND_TOP3_VAL__ 亿，剔除后只剩 __FUND_EX__ 亿。更能反映整体的是<b>中位数</b>：__FUND_MED__ 亿，反而低于昨日 __FUND_MED_Y__ 亿。
结论是<span class="hl">"少数票被死死锁仓，多数票封单偏薄"</span>——这类结构对次日开盘承接最敏感。
</div>
</div>

<div class="card">
<h2>八、资金运动的三个结论</h2>
<ul>
<li><b>① 总量：不是增量，是存量扩散。</b>涨停家数 __ZT_Y__→__ZT__（__ZT_D__），而两市成交额 __AMT__ 亿（__AMT_PCT__%，__AMT_D__ 亿）。
<span class="hl">家数增加与成交额下降同时出现，只有一种解释：现有资金从"少数大票"分散到"更多小票"</span>——
佐证是科创50 成交额 __KC_AMT_PCT__%，而涨停股合计成交占两市比重反而从 __SHARE_Y__% 升到 __SHARE__%。</li>
<li><b>② 方向：跨赛道搬家，不是板块内高低切。</b>昨日主线电网设备 __HY_DW_Y__→__HY_DW__ 家、半导体 __HY_BDT_Y__→__HY_BDT__ 家几乎被清空，
资金整体流向医药链（化学制药 __HY_YIYAO_Y__→__HY_YIYAO__、医疗服务 __HY_MEDSVC_Y__→__HY_MEDSVC__、医疗器械 __HY_MEDDEV_Y__→__HY_MEDDEV__）
与地产链（房地产开 __HY_FDCK_Y__→__HY_FDCK__、房地产服 __HY_FDCF_Y__→__HY_FDCF__）。
<span class="hl">昨日的强势方向今日直接变成最弱（__PERF_BOT3__ 均为原电网设备/算力硬件标），这是资金偏短线、不愿过夜的信号</span>。</li>
<li><b>③ 深度：高标锁仓、首板快换手。</b>连板组晋级率 __ADV_L_RATE__%、中位 __ADV_L_MED__%，而首板组晋级率仅 __ADV_S_RATE__%、中位 __ADV_S_MED__%；
封单中位降到 __FUND_MED__ 亿、换手板占 __HUANSHOU_PCT__%。<span class="hl">钱在少数高标上打桩，在首板上做日内博弈</span>，
这种结构下"涨停家数"这个总量指标的解释力是下降的，应重点看连板梯队的存续。</li>
</ul>
</div>

<div class="card">
<h2>九、明日观察要点与风险</h2>
<ul>
<li><b>退潮触发条件：</b>封板率已到 __SEAL__% 的高位，若明日回落到 70% 以下、同时炸板数升破 30 家，即为情绪见顶的第一确认；跌停家数已从 __DT_Y__ 升到 __DT__，需盯是否继续扩大。</li>
<li><b>高度标杆：</b>__LB_TOP1__（__MAXB__ 板，__LB_TOP1_REASON__）与 __LB_TOP2__（__LB_TOP2_LB__ 板）能否延续。__LB_TOP2_LB__ 板档位有 __LAD4_T__ 家、3 板档位有 __LAD3_T__ 家，是明日的接力池，也是分歧最大的一档。</li>
<li><b>医药链的持续性：</b>__MEDTHEME_N__ 家集体涨停且最高只有 3 板，是"广度行情"而非"高度行情"。若明日出现缩量一字板或大面积炸板，大概率验证一日游。</li>
<li><b>量能回补：</b>本轮上涨建立在成交额 __AMT_PCT__ 的基础上。若明日成交额仍不能回到 2.1 万亿上方，则涨停家数的高位难以维持。</li>
<li><b>封单薄弱风险：</b>剔除 __FUND_TOP_NAME__ 后封单合计仅 __FUND_EX__ 亿、中位 __FUND_MED__ 亿，一旦开盘承接不足易出现集体炸板。</li>
<li><b>数据口径：</b>统计为沪深两市（同花顺口径 __ZT__ 家）；东财涨停池 __ZT_D_EM__ 条，差额 __ZT_EM_DIFF__ 只为北交所标的（920478 峆一药业、920427 华维设计），已按沪深口径剔除。
跌停家数取同花顺汇总字段 __DT__ 家（跌停池明细接口当日返回空，故未列名单）。两市成交额为沪市 + 深市全市场口径。
封板时间双源分钟级一致率 100%（101/101）。</li>
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
    {name:'__L_D1__',type:'bar',data:__JS_LAD1__,itemStyle:{color:'#cbd5e1'},barWidth:18},
    {name:'__L_D0__',type:'bar',data:__JS_LAD0__,itemStyle:{color:C_RED},barWidth:18,
     label:{show:true,position:'top',color:'#9ca3af',fontSize:11}}
  ]
});

mk('c_theme',{
  tooltip:{trigger:'axis'},
  grid:{left:124,right:70,top:16,bottom:24},
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
    {name:'__L_D1__',type:'bar',data:__JS_HY_Y__,itemStyle:{color:'#cbd5e1'},barWidth:11},
    {name:'__L_D0__',type:'bar',data:__JS_HY_T__,itemStyle:{color:C_RED},barWidth:11}
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
    {name:'__L_D1__',type:'bar',data:__JS_TS_Y__,itemStyle:{color:'#cbd5e1'},barWidth:24},
    {name:'__L_D0__',type:'bar',data:__JS_TS_T__,itemStyle:{color:C_RED},barWidth:24}
  ]
});
</script>
</body>
</html>
"""

# 东财与同花顺涨停池差额（北交所口径）
_em_tc = (B["dates"][D0]["em_ZT"] or {}).get("tc") or 0
P("ZT_D_EM", _em_tc)
P("ZT_EM_DIFF", _em_tc - s0["zt"])

HTML = HTML_T
for k, v in V.items():
    HTML = HTML.replace(k, v)

fp = os.path.join(REP, f"涨停复盘对比-{D0}.html")
with open(fp, "w", encoding="utf-8") as f:
    f.write(HTML)
left = re.findall(r"__[A-Z_0-9]+__", HTML)
print("saved ->", fp, len(HTML) // 1024, "KB")
print("placeholder residue:", sorted(set(left)))
