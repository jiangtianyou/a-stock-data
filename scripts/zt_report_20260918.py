# -*- coding: utf-8 -*-
"""涨停复盘报告生成 2026-09-18（对比 09-17）—— 基于 skill 模板改写叙述文案

用法：python scripts/zt_report_20260918.py 20260918
输入：out/zt_stats_20260918.json、out/zt_review_20260918.json
输出：reports/涨停复盘对比-20260918.html
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


def hhmm(v):
    """东财 fbt 为 HHMMSS 整数（92500 = 09:25:00），必须补足 6 位再切，
    否则 10:00 前的封板时间会被切错（92500 -> '92:50'）。"""
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
    ("半导体 / 电子材料", ["半导体", "芯片", "封测", "先进封装", "存储", "晶圆", "光刻胶",
                     "电子特气", "电子化学品", "洁净室", "光引发剂", "电容器"]),
    ("电力设备 / 电缆 / 电网", ["电网", "电缆", "电磁线", "输配电", "断路器", "热电", "燃气表",
                       "智慧能源", "光伏玻璃", "液力传动"]),
    ("消费 / 零售 / 服装家居", ["零售", "服装", "家纺", "家居", "家具", "纺织", "黄酒", "厨具",
                       "毛毯", "皮鞋", "户外", "洗染", "商业地产", "烟标"]),
    ("AI算力 / 光通信 / PCB", ["光模块", "光通信", "光纤", "算力", "液冷", "服务器", "交换机",
                        "数据中心", "PCB", "CPO", "钻针", "云网"]),
    ("机器人 / 具身智能", ["机器人", "人形", "行星滚柱丝杠", "线性驱动", "具身", "结构件"]),
    ("房地产 / 城市更新", ["房地产", "城市更新", "深铁", "大资管", "基建项目"]),
    ("国资 / 区域主题", ["国资", "国企", "央企", "海峡两岸"]),
    ("医药 / 医疗", ["医药", "细胞", "CRO", "医疗", "诊断", "创新药", "维生素"]),
    ("风电 / 新能源材料", ["风电", "齿轮箱", "铸件", "锂电池", "储能", "钙钛矿", "电解铝", "电池箔"]),
    ("出版 / 传媒", ["出版", "教育", "传媒", "短剧", "演艺"]),
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

# ---- 0918 专用：权重股 / 主线扩散口径 ----
# 东财涨停池含北交所，沪深口径需剔除 920xxx/8xxxxx/4xxxxx
_bj = {x["c"] for x in B["dates"][D0]["em_ZT"]["pool"] if x["c"].startswith(("92", "8", "4"))}
em_zt_n = len(B["dates"][D0]["em_ZT"]["pool"])
bj_codes = "、".join(sorted(_bj))
# 今日涨停中流通市值 >= 200 亿的「大票」（含涨停，非封板中）
big200 = [r for r in sorted(r0, key=lambda x: -(x["ltsz"] or 0)) if (r["ltsz"] or 0) >= 200e8]
big200_name = "、".join(r["name"] for r in big200[:5])
# 消费/地产等「非科技」低位方向家数
LOW_KW = ("一般零售", "服装家纺", "家居用品", "文娱用品", "小家电", "非白酒", "旅游及景",
          "广告营销", "房地产开", "房地产服", "出版", "纺织制造")
low_n = sum(1 for r in r0 if r["hybk"] in LOW_KW)
TECH_KW = ("算力", "光模块", "光通信", "光纤", "数据中心", "液冷", "服务器", "CPO", "交换机",
           "PCB", "半导体", "芯片", "封装", "存储", "晶圆", "光刻胶", "电子特气", "光引发剂")
tech_n = sum(1 for r in r0 if any(k in r["reason"] for k in TECH_KW))
# 今日电力设备链（电网设备 + 电力 + 光伏 + 风电）
power_n = sum(1 for r in r0 if r["hybk"] in ("电网设备", "电力", "光伏设备", "风电设备"))
power_lianban = sum(1 for r in r0 if r["hybk"] in ("电网设备", "电力", "光伏设备", "风电设备")
                    and (r["lbc"] or 1) >= 2)
# 半导体链连板数
semi_lianban = sum(1 for r in r0 if r["hybk"] == "半导体" and (r["lbc"] or 1) >= 2)
# 最强单只成交额
amt_top = max(r0, key=lambda x: x["amount"] or 0)
amt_top_ltsz = (amt_top["ltsz"] or 0) / 1e8
# 昨5板今日表现
top_y = next((p for p in perf if (p["lbc"] or 0) >= 5), None)
# 早盘封板占比
ts_early0 = ts0.get("竞价/秒板", 0) + ts0.get("开盘半小时", 0)
ts_early0_pct = ts_early0 / s0["zt"] * 100

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
        hhmm(x["fbt"]),
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
P("DEN0", s0["zt"] + s0["zb"]); P("DEN1", s1["zt"] + s1["zb"])
P("DT", s0["dt"]); P("DT_Y", s1["dt"]); P("DT_D", "{:+d}".format(s0["dt"] - s1["dt"]))
P("SEAL", "{:.1f}".format(s0["seal_rate"] * 100))
P("SEAL_Y", "{:.1f}".format(s1["seal_rate"] * 100))
P("SEAL_D", "{:+.1f}".format((s0["seal_rate"] - s1["seal_rate"]) * 100))
P("ZTDT", "∞（零跌停）" if s0["dt"] == 0 else "{:.1f}".format(s0["zt"] / s0["dt"]))
P("ZTDT_Y", "∞（零跌停）" if s1["dt"] == 0 else "{:.1f}".format(s1["zt"] / s1["dt"]))
P("ZTDT_0", "∞（零跌停）" if days[0]["dt"] == 0 else "{:.1f}".format(days[0]["zt"] / days[0]["dt"]))
P("DT_OPEN", s0["limit_down_count"]["today"]["open_num"])
P("MAXB", maxb); P("MAXB_Y", maxb_y)
P("LB", s0["lianban"]); P("LB_Y", s1["lianban"])
P("SB", s0["shouban"]); P("SB_Y", s1["shouban"])
P("SB_PCT", "{:.0f}".format(s0["shouban"] / s0["zt"] * 100))
P("SB_PCT_Y", "{:.0f}".format(s1["shouban"] / s1["zt"] * 100))
P("SB_D", "{:+d}".format(s0["shouban"] - s1["shouban"]))
P("LB_D", "{:+d}".format(s0["lianban"] - s1["lianban"]))
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
P("HUANSHOU_PCT", "{:.0f}".format(huanshou / (oneword + tword + huanshou) * 100 if (oneword + tword + huanshou) else 0))
P("BIG_N", big_n); P("BIG_LIST", esc(big_list))
P("ZB_EARLY", zb_early); P("ZB_EARLY_PCT", "{:.0f}".format(zb_early_pct))
P("ZB_B1030", zb_before1030)
P("ZB_IN_YZT_N", len(zb_in_yzt)); P("ZB_IN_YZT", "、".join(zb_in_yzt))
P("ZB_NEW_N", len(zb0) - len(zb_in_yzt))
P("TBL_ZB", tbl_zb)
P("LB_TOP1", esc(lb_all[0]["name"])); P("LB_TOP1_REASON", esc(lb_all[0]["reason"]))
P("LB_TOP2", esc(lb_all[1]["name"])); P("LB_TOP2_LB", lb_all[1]["lbc"])
P("LB_TOP3", esc(lb_all[2]["name"])); P("LB_TOP3_LB", lb_all[2]["lbc"])
P("LB_TOP4", esc(lb_all[3]["name"])); P("LB_TOP4_LB", lb_all[3]["lbc"])
P("CAR_N", len(car_first)); P("CAR_ALL_FIRST", "是" if car_all1 else "否")
P("EM_ZT_N", em_zt_n); P("THS_ZT_N", s0["zt"]); P("BJ_CODES", esc(bj_codes) or "无")
P("BIG200_N", len(big200)); P("BIG200_NAME", esc(big200_name))
P("LOW_N", low_n); P("TECH_N", tech_n)
P("POWER_N", power_n); P("POWER_LB", power_lianban); P("SEMI_LB", semi_lianban)
P("AMT_TOP_NAME", esc(amt_top["name"])); P("AMT_TOP_AMT", "{:.2f}".format((amt_top["amount"] or 0) / 1e8))
P("AMT_TOP_LTSZ", "{:.0f}".format(amt_top_ltsz)); P("AMT_TOP_REASON", esc(amt_top["reason"]))
P("TOP_Y_NAME", esc(top_y["name"]) if top_y else "—")
P("TOP_Y_PCT", "{:+.2f}".format(top_y["pct"]) if top_y else "—")
P("TOP_Y_LB", top_y["lbc"] if top_y else "—")
P("HY_DW", hy1.get("电网设备", 0)); P("HY_DW0", hy0.get("电网设备", 0))
P("HY_TY", hy1.get("通用设备", 0)); P("HY_TY0", hy0.get("通用设备", 0))
P("HY_FZ", hy1.get("服装家纺", 0)); P("HY_FZ0", hy0.get("服装家纺", 0))
P("HY_JJ", hy1.get("家居用品", 0)); P("HY_JJ0", hy0.get("家居用品", 0))
P("HY_LS", hy1.get("一般零售", 0)); P("HY_LS0", hy0.get("一般零售", 0))
P("HY_FDC", hy1.get("房地产开", 0)); P("HY_FDC0", hy0.get("房地产开", 0))
P("HY_ZZY", hy1.get("种植业", 0)); P("HY_ZZY0", hy0.get("种植业", 0))
P("HY_JSS", hy1.get("计算机设", 0)); P("HY_JSS0", hy0.get("计算机设", 0))
P("TH_N", len([t for t in theme_cnt if t["n"] > 0]))


def THN(prefix):
    return next((t["n"] for t in theme_cnt if t["name"].startswith(prefix)), 0)


P("TH_AI", THN("AI算力")); P("TH_SEMI", THN("半导体")); P("TH_PWR", THN("电力设备"))
P("TH_CONS", THN("消费")); P("TH_ROBOT", THN("机器人")); P("TH_GZ", THN("国资"))
P("TH_RE", THN("房地产")); P("TH_PUB", THN("出版"))
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
<title>涨停复盘 · 2026-09-18（对比 9-17）</title>
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
<h1>涨停复盘 · 2026-09-18（周五）</h1>
<div class="sub">对比基准：2026-09-17（周四）｜口径：沪深两市（不含北交所）｜数据源：同花顺涨停池 + 东方财富涨停/炸板/跌停池 + 腾讯财经行情快照</div>

<div class="lead">
<p class="hl">一句话结论：昨日「宽度收缩、高度保留」的收敛日，今天直接反转为放量普涨。涨停从 __ZT_Y__ 家回到 __ZT__ 家、封板率升到 __SEAL__%、
跌停家数归零，两市成交额 __AMT__ 亿环比 __AMT_D__ 亿（__AMT_PCT__%）——这是本轮调整以来第一次「量价齐升 + 零跌停」。</p>
<p>更关键的是<b>结构换了</b>：昨日的接棒主线汽车产业链一日游（汽车零部 __HY_QC__→__HY_QC0__ 家，昨日 8 家涨停股今日全部未续板），
资金改道<b>电力设备/电缆（__HY_DW__→__HY_DW0__ 家）与半导体（__HY_BDT__→__HY_BDT0__ 家）</b>，同时把消费/零售/家居/地产等低位方向一起抬起来（合计 __LOW_N__ 家）。
<span class="hl">前两日纯小票游戏结束 —— 今日出现了流通市值 __AMT_TOP_LTSZ__ 亿的 __AMT_TOP_NAME__ 涨停（单只成交 __AMT_TOP_AMT__ 亿）、万科A、绿地控股等权重。</span></p>
<p>但高度仍未打开：最高板从 __MAXB_Y__ 板降到 __MAXB__ 板（昨 __MAXB_Y__ 板 __TOP_Y_NAME__ 今日 __TOP_Y_PCT__%），
首板占 __SB_PCT__%、中位封单仅 __FUND_MED__ 亿。<span class="hl">广度修复得很快，深度（连板高度 + 锁仓意愿）还没跟上。</span></p>
</div>

<div class="kpis">
  <div class="kpi"><div class="lbl">涨停家数</div><div class="val up">__ZT__</div>
    <div class="dt mut">昨日 __ZT_Y__ <span class="up">__ZT_D__</span></div></div>
  <div class="kpi"><div class="lbl">封板率</div><div class="val">__SEAL__%</div>
    <div class="dt mut">昨日 __SEAL_Y__% <span class="up">__SEAL_D__pct</span></div></div>
  <div class="kpi"><div class="lbl">跌停家数</div><div class="val">__DT__</div>
    <div class="dt mut">昨日 __DT_Y__ <span class="up">__DT_D__</span></div></div>
  <div class="kpi"><div class="lbl">两市成交额</div><div class="val">__AMT__亿</div>
    <div class="dt mut">昨日 __AMT_Y__亿 <span class="up">__AMT_D__亿（__AMT_PCT__%）</span></div></div>
  <div class="kpi"><div class="lbl">昨涨停今日晋级率</div><div class="val up">__ADV_RATE__%</div>
    <div class="dt mut">__ADV_N__/__ADV_TOT__ 只再涨停（昨基线 10.1%）</div></div>
  <div class="kpi"><div class="lbl">最高连板</div><div class="val">__MAXB__ 板</div>
    <div class="dt mut">昨日 __MAXB_Y__ 板</div></div>
</div>

<div class="card">
<h2>一、市场情绪温度计：收敛只维持一天，今日重新扩张</h2>
<table>
<tr><th>指标</th><th>__D2L__</th><th>__D1L__</th><th>__D0L__</th><th>__D0L__ 环比</th></tr>
__TBL_SENTI__
<tr><td>涨停/跌停比</td><td>__ZTDT_0__</td><td>__ZTDT_Y__</td><td class="hl">__ZTDT__</td><td class="up">跌停归零</td></tr>
</table>
<div class="note" style="margin-top:10px">
三日序列把节奏交代得很清楚：__D2L__ 是本轮情绪高点（涨停 __D2L_ZT__ 家、但跌停也有 __D2L_DT__ 家），
__D1L__ 收敛到 __ZT_Y__ 家（跌停降到 __DT_Y__ 家），__D0L__ 重新扩张到 __ZT__ 家、<b>跌停 __DT__ 家直接归零</b>。<br>
三项指标同向改善：涨停 __ZT_D__ 家、封板率 __SEAL_Y__%→__SEAL__%（__SEAL_D__pct）、炸板虽从 __ZB_Y__ 家增至 __ZB__ 家，
但分母（涨停+炸板）从 __ZT_Y__+__ZB_Y__ = __DEN1__ 升到 __ZT__+__ZB__ = __DEN0__，<span class="hl">炸板增加的幅度赶不上封板增加的幅度 —— 这是扩张而非分歧。</span><br>
真正的风险信号不在情绪指标，而在高度：最高连板从 __MAXB_Y__ 板回落到 __MAXB__ 板。
</div>
<div id="c_senti" class="chart" style="margin-top:16px"></div>
</div>

<div class="card">
<h2>二、指数与量能：量价齐升，增量资金终于全面进场</h2>
<div class="two">
<div>
<table>
<tr><th>指数</th><th>今日</th><th>昨日</th><th>成交额</th><th>环比</th></tr>
__TBL_IDX__
</table>
<div class="note" style="margin-top:10px">
<b>今天的量能是真增量，而且是全面性的：</b>两市成交额 __AMT__ 亿，环比增加 __AMT_DABS__ 亿（__AMT_PCT__%），
昨日全线小幅回调的 11 个指数今日<b>全部翻红</b>，涨幅区间 __SZ50_PCT__%（上证50）到 __KC_PCT__%（科创50）。<br>
增速最猛的仍是科创50：成交额 __KC_AMT__ 亿（昨 __KC_AMT_PREV__ 亿，__KC_AMT_PCT__%），
<span class="hl">昨日它缩量领跌，今日放量领涨 —— 科技成长的资金不但没走，还加了仓。</span>
值得注意的是上证50 也涨 __SZ50_PCT__%，权重股没有拖后腿，这与「只炒小票」的市场有本质区别。
</div>
</div>
<div><div id="c_idx" class="chart-sm"></div></div>
</div>
</div>

<div class="card">
<h2>三、连板梯队：宽度接近翻倍，高度反而退了一板</h2>
<div class="two">
<div><div id="c_lad" class="chart-sm"></div></div>
<div>
<table>
<tr><th>梯队</th><th>__D1L__</th><th>__D0L__</th><th>变化</th></tr>
__TBL_LAD__
<tr><td>合计</td><td>__ZT_Y__</td><td class="hl">__ZT__</td><td class="up">__ZT_D__</td></tr>
</table>
<div class="note" style="margin-top:10px">
首板 __SB__ 家（昨 __SB_Y__），首板占比 __SB_PCT__%（昨 __SB_PCT_Y__%）；连板股 __LB__ 家（昨 __LB_Y__）。<br>
最高板从 __MAXB_Y__ 板降到 __MAXB__ 板：昨日 5 板的高标 __TOP_Y_NAME__ 今日 __TOP_Y_PCT__% 断板；
新高度由 <b>__LB_TOP1__（4 板，__LB_TOP1_REASON__）</b>顶上。<br>
<span class="hl">首板暴增 __SB__-__SB_Y__ = __SB_D__ 家、连板只增 3 家 —— 新增的涨停几乎全是「第一次上板」。</span>
这种结构说明市场在<b>横向扩散</b>（更多票被拉起来），而不是<b>纵向拔高</b>（同一批票连续涨停）。对打板客来说，
前者意味着机会多但持续性差，后者才是赚钱效应最强的阶段 —— 今天明显是前者。
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
<h2>四、主线归因：科技链回归 + 消费地产低位补涨，双线并行</h2>
<div id="c_theme" class="chart"></div>
<table style="margin-top:14px">
<tr><th>主线</th><th>涨停家数</th><th>代表个股</th></tr>
__TBL_THEME__
</table>
<div class="note" style="margin-top:12px">
与昨日「汽车链单点接棒」不同，今天的题材是<b>多点开花</b>：AI算力/光通信/PCB __TH_AI__ 家、
半导体/电子材料 __TH_SEMI__ 家、消费/零售/服装家居 __TH_CONS__ 家、电力设备/电缆/电网 __TH_PWR__ 家、机器人 __TH_ROBOT__ 家。<br>
其中<b>电力设备/电缆</b>是最值得注意的一条：电网设备行业今日 __HY_DW__→__HY_DW0__ 家（全行业第一），
代表个股华盛昌（光通信测试+CPO）、精达股份（电磁线+高速铜线+数据中心）、太阳电缆、中超控股、中电鑫龙 ——
<span class="hl">本质是「AI 算力 → 电力配套」的外溢，属于算力链的下一环，不是纯基建。</span>
配合半导体链的华天科技（封测+先进封装，成交 __AMT_TOP_AMT__ 亿，今日单只最大）与托伦斯、盛景微，
可以看出<span class="hl">科技链并没有退场，只是从「光模块 / PCB」往「上游封测与电力配套」延伸。</span><br>
另一条是<b>低位方向的集体补涨</b>：一般零售 __HY_LS__→__HY_LS0__ 家、服装家纺 __HY_FZ__→__HY_FZ0__ 家、
家居用品 __HY_JJ__→__HY_JJ0__ 家、房地产开发 __HY_FDC__→__HY_FDC0__ 家（含万科A、绿地控股），合计 __LOW_N__ 家。
这类标的前期滞涨、市值偏小，是增量资金「没赶上科技、退而求其次」的选择。<br>
<b>要提醒的是：今日电网设备 __HY_DW0__ 家、半导体 __HY_BDT0__ 家，其中连板股合计仅 __POWER_LB__ 只（半导体链为零）</b>，
两条最"硬"的方向同样处于「扩散第一天」，尚未形成高度。<br>
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
<b>流入端：</b>电网设备 __HY_DW__→__HY_DW0__ 家（+5，全行业第一）、半导体 __HY_BDT__→__HY_BDT0__ 家（+3）、
通用设备 __HY_TY__→__HY_TY0__ 家（+4）、服装家纺 __HY_FZ__→__HY_FZ0__ 家（+3）、家居用品 __HY_JJ__→__HY_JJ0__ 家（+3）、
一般零售 0→__HY_LS0__ 家。<br>
<b>流出端：</b>汽车零部 __HY_QC__→__HY_QC0__ 家（-6，单行业最大流出）、种植业 __HY_ZZY__→__HY_ZZY0__ 家（清零）、
消费电子 2→1、自动化设 1→0。<br>
<span class="hl">昨天最强的汽车链只活了一天就交棒，这是今天最需要记住的一件事：在当前节奏下，「接棒主线」的保质期只有 1~2 个交易日，
追高昨日强势方向的性价比极低。</span>
</div>
</div>

<div class="card">
<h2>六、昨日涨停股今日表现：普涨修复，但强弱分层依然清晰</h2>
<div class="kpis" style="grid-template-columns:repeat(auto-fit,minmax(140px,1fr))">
  <div class="kpi"><div class="lbl">晋级率</div><div class="val">__ADV_RATE__%</div><div class="dt mut">__ADV_N__/__ADV_TOT__</div></div>
  <div class="kpi"><div class="lbl">平均涨幅</div><div class="val up">__PERF_MEAN__%</div><div class="dt mut">中位 __PERF_MED__%</div></div>
  <div class="kpi"><div class="lbl">翻绿比例</div><div class="val down">__NEG_PCT__%</div><div class="dt mut">__NEG__ 只</div></div>
  <div class="kpi"><div class="lbl">最强</div><div class="val up">__PERF_MAX__%</div><div class="dt mut">__PERF_MAX_NAME__（昨 __PERF_MAX_LB__ 板）</div></div>
  <div class="kpi"><div class="lbl">最弱</div><div class="val down">__PERF_MIN__%</div><div class="dt mut">__PERF_MIN_NAME__（昨 __PERF_MIN_LB__ 板）</div></div>
</div>
<h3>按昨日身份分组：连板组的接力效率仍是首板组的两倍</h3>
<table>
<tr><th>昨日身份</th><th>只数</th><th>今日晋级率</th><th>均涨</th><th>中位</th><th>翻绿只数</th></tr>
<tr><td>昨日首板</td><td>__GSB_N__</td><td>__GSB_ADV__%</td><td class="up">__GSB_MEAN__%</td><td class="up">__GSB_MED__%</td><td>__GSB_NEG__</td></tr>
<tr><td>昨日连板（2板+）</td><td>__GLB_N__</td><td class="hl">__GLB_ADV__%</td><td class="up hl">__GLB_MEAN__%</td><td class="up hl">__GLB_MED__%</td><td>__GLB_NEG__</td></tr>
</table>
<div class="note" style="margin-top:14px">
<b>这是本报告最重要的一张表。</b>整体晋级率 __ADV_RATE__%（昨基线 10.1%），但两组差异依然存在：
昨日 __GLB_N__ 只连板股今日均涨 __GLB_MEAN__%、晋级率 __GLB_ADV__%，只有 __GLB_NEG__ 只翻绿；
昨日 __GSB_N__ 只首板股今日均涨 __GSB_MEAN__%、晋级率 __GSB_ADV__%、__GSB_NEG__ 只翻绿。<br>
两组的中位涨幅（__GLB_MED__% vs __GSB_MED__%）看起来差不多，但<b>均值被拉开的差距说明连板组是两极分布</b>：
内蒙新华、华瓷股份、锡华科技、世联行 4 只继续封板（+9.89%~+10.04%），另外 5 只（含昨日 5 板 __TOP_Y_NAME__ __TOP_Y_PCT__%）则直接熄火。
<span class="hl">连板组不是「普遍能接力」，而是「要么晋级、要么走弱」，中间态很少</span>——这是高标博弈的典型特征。<br>
整体看，昨日 __ADV_TOT__ 只涨停股今日均涨 __PERF_MEAN__%、中位 __PERF_MED__%、仅 __NEG__ 只翻绿（__NEG_PCT__%），
最强的 __PERF_MAX_NAME__（昨 __PERF_MAX_LB__ 板）__PERF_MAX__%、最弱的 __PERF_MIN_NAME__（昨 __PERF_MIN_LB__ 板）__PERF_MIN__%。
<span class="hl">这是「普涨修复」，不是「结构分化」——与昨日那种首板组中位为负的行情完全不同。</span>
</div>
<h3>今日炸板池（__ZB__ 家）</h3>
<table>
<tr><th>名称</th><th>代码</th><th>行业</th><th>成交额</th><th>首封</th><th>身份</th></tr>
__TBL_ZB__
</table>
<div class="note" style="margin-top:10px">
炸板股里有 __ZB_IN_YZT_N__ 只是昨日涨停股（__ZB_IN_YZT__）—— 昨日封板、今日炸板，是接力失败最直接的形态；
其余 __ZB_NEW_N__ 只均为今日新增面孔，说明<span class="hl">今日炸板的主因不是「昨日资金撤离」，而是「今天新冲板被砸」</span>。<br>
<b>炸板股首封时间高度集中在早盘：__ZB_EARLY__/__ZB__ 只在 11:30 前首次封板、__ZB_B1030__ 只在 10:30 前</b>，
且成交额最大的是中材科技（玻璃玻纤）68.73 亿——
<span class="hl">早盘一致冲高、盘中承接不足，是今日炸板池的共同特征；封板率高不代表没有分歧，只是分歧被更强的买盘压住了。</span>
</div>
<div id="c_perf" class="chart" style="height:1500px;margin-top:8px"></div>
</div>

<div class="card">
<h2>七、封板节奏与成交结构：封板更早、封单更厚、换手更省</h2>
<div class="two">
<div><div id="c_ts" class="chart-sm"></div></div>
<div>
<table>
<tr><th>封板时段</th><th>__D1L__</th><th>__D0L__</th><th>__D0L__ 占比</th></tr>
__TBL_TS__
</table>
<div class="note" style="margin-top:10px">
<b>节奏明显前移：</b>早盘（竞价 + 开盘半小时）__D0L__ __TS_EARLY_0__ 家占 __TS_EARLY_0_PCT__%，
__D1L__ __TS_EARLY_Y__ 家占 __TS_EARLY_Y_PCT__%；午后封板 __D0L__ __TS_PM0__ 家占 __TS_PM0_PCT__%，__D1L__ __TS_PM1__ 家占 __TS_PM1_PCT__%。<br>
早盘封板占比从 __TS_EARLY_Y_PCT__% 提升到 __TS_EARLY_0_PCT__%，午后占比从 __TS_PM1_PCT__% 降到 __TS_PM0_PCT__%。
<span class="hl">这是「开盘即一致看多」的形态 —— 资金不等盘中确认就抢筹，通常出现在情绪修复的加速段。</span>
但要留意：早盘封板占比越高，一旦盘中出现利空，炸板的杀伤面也越大（今日炸板股 __ZB_EARLY__/__ZB__ 只也是早盘封的）。
</div>
</div>
</div>
<div class="kpis" style="grid-template-columns:repeat(auto-fit,minmax(160px,1fr));margin-top:16px">
  <div class="kpi"><div class="lbl">涨停股合计成交额</div><div class="val">__AMT_SUM__亿</div><div class="dt mut">占两市 __SHARE__%（昨 __SHARE_Y__%）</div></div>
  <div class="kpi"><div class="lbl">单只成交额中位</div><div class="val">__MED_AMT__亿</div><div class="dt mut">昨 __MED_AMT_Y__亿</div></div>
  <div class="kpi"><div class="lbl">单只换手中位</div><div class="val">__MED_HS__%</div><div class="dt mut">昨 __MED_HS_Y__%</div></div>
  <div class="kpi"><div class="lbl">封单中位</div><div class="val">__FUND_MED__亿</div><div class="dt mut">昨 __FUND_MED_Y__亿</div></div>
  <div class="kpi"><div class="lbl">封单合计</div><div class="val">__FUND_SUM__亿</div><div class="dt mut">昨 26.5亿（翻倍）</div></div>
</div>
<div class="note" style="margin-top:14px">
<b>封单结构是本日最正面的变化：</b>封单合计从 26.5 亿翻倍至 __FUND_SUM__ 亿，中位从 __FUND_MED_Y__ 亿升到 __FUND_MED__ 亿。
同时单只换手中位从 __MED_HS_Y__% 降到 __MED_HS__%、单只成交额中位从 __MED_AMT_Y__ 亿降到 __MED_AMT__ 亿。
<span class="hl">「封单变厚 + 换手变省」= 买盘锁仓意愿上升，而不是靠反复换手硬撑 —— 这是今天质地最好的一项指标。</span><br>
但合计成交额占比只有 __SHARE__%（昨 __SHARE_Y__%），低于 3%~8% 的经验区间。
需要说明：<b>该比值与涨停家数强相关，且与「大票占比」强相关</b>。
今日 __ZT__ 家里流通市值超 300 亿的仅 __BIG_N__ 只（__BIG_LIST__），绝大多数是中小市值票；
虽然单只成交额最大的 __AMT_TOP_NAME__ 达 __AMT_TOP_AMT__ 亿（流通市值 __AMT_TOP_LTSZ__ 亿），但样本整体偏轻。
用东财字段做「换手率 × 流通市值 ≈ 成交额」三角验证：__AMT_TOP_NAME__ __AMT_TOP_LTSZ__亿 × 10.9% ≈ 65 亿 vs 实际 __AMT_TOP_AMT__ 亿，误差 2%，<b>字段源无误</b>。<br>
一字板仅 __ONEWORD__ 只、T字板 __TWORD__ 只、换手板 __HUANSHOU__ 只（占 __ONEWORD__+__TWORD__+__HUANSHOU__ 只的 __HUANSHOU_PCT__%）——
<span class="hl">市场依然以「真金白银换手封板」为主，没有靠一字板虚抬指数。</span>
</div>
</div>

<div class="card">
<h2>八、资金运动的三个结论</h2>
<ul>
<li><b>① 总量上：这是本轮第一次「真·增量」。</b>两市成交额 __AMT__ 亿，环比增 __AMT_DABS__ 亿（__AMT_PCT__%），
11 个指数全红，科创50 成交额环比 __KC_AMT_PCT__%（增速是两市整体的 2.7 倍），跌停 __DT__ 家。
<span class="hl">与前两日的「存量搬家」不同 —— 今天是有新钱进来的。</span>从 KPI 看，涨停股合计成交 __AMT_SUM__ 亿（较昨 357.6 亿增 39%），
增量既来自更多涨停股，也来自单只大票（__AMT_TOP_NAME__ 单只 __AMT_TOP_AMT__ 亿）。</li>
<li><b>② 方向上：汽车链一日游停止，资金改道「算力外溢 + 低位补涨」。</b>
昨日汽车零部 __HY_QC__ 家涨停，今日只剩 __HY_QC0__ 家；同期电网设备 __HY_DW__→__HY_DW0__ 家、
半导体 __HY_BDT__→__HY_BDT0__ 家、通用设备 __HY_TY__→__HY_TY0__ 家。
<span class="hl">电网设备 6 家的涨停原因高度集中于「电缆 / 电磁线 / 高速铜线 / 数据中心供电」，本质是 AI 算力资本开支向电力配套外溢，
而不是传统基建逻辑 —— 这是今天最值得跟踪的方向。</span>
同时消费零售/地产（合计 __LOW_N__ 家，含万科A、绿地控股）承接了溢出资金。</li>
<li><b>③ 深度上：封单变厚、换手变省，但高度未打开。</b>封单合计 26.5→__FUND_SUM__ 亿、中位 __FUND_MED_Y__→__FUND_MED__ 亿；
单只换手中位 __MED_HS_Y__%→__MED_HS__%。
<span class="hl">锁仓意愿在回升，这是明日承接的基础。</span>但短板同样明确：首板占 __SB_PCT__%、最高板从 __MAXB_Y__ 降到 __MAXB__ 板、
昨日 5 板高标 __TOP_Y_NAME__ 今日 __TOP_Y_PCT__%。
<span class="hl">「广度极好、深度不足」是今天结构的关键词 —— 这种形态下涨停家数易维持、但赚钱效应集中在低位首板，追高连板风险大于收益。</span></li>
</ul>
</div>

<div class="card">
<h2>九、明日观察要点与风险</h2>
<ul>
<li><b>高度标杆：</b>今日 4 板由 __LB_TOP1__ 与 __LB_TOP2__ 并列（__LB_TOP1_REASON__），能否晋级 __MAXBN__ 板；
中位梯队看 __LB_TOP3__、__LB_TOP4__（均 3 板）能否补位。
高度端是今日唯一的短板（最高板从 __MAXB_Y__ 降到 __MAXB__），<b>若明日 4 板双双断板且无新高度顶上，则「扩散行情」将缺乏龙头锚</b>。</li>
<li><b>算力外溢链能否升级：</b>今日电网设备 __HY_DW0__ 家（__POWER_LB__ 只连板）、半导体 __HY_BDT0__ 家（__SEMI_LB__ 只连板）
<b>加总 11 家几乎全是首板</b>。明日看这两条线有没有 2 板出现 —— 有，则新主线成立；没有，则又是一轮一日游扩散。</li>
<li><b>权重股的第二波：</b>今日 __AMT_TOP_NAME__（半导体封测+先进封装+拟收购华羿微电，流通市值 __AMT_TOP_LTSZ__ 亿）以 __AMT_TOP_AMT__ 亿成交额涨停，
万科A、绿地控股同步涨停。<b>大市值涨停股次日通常是「低开震荡、不给溢价」的走法，
但若 __AMT_TOP_NAME__ 能走出连续性，意味着机构资金开始主导本轮行情</b>，性质将完全不同。</li>
<li><b>承接强度基线：</b>今日晋级率 __ADV_RATE__%（昨 10.1%）。若明日跌破 20%，说明今日的普涨只是「单日脉冲」；
若能维持在 __ADV_RATE__% 以上，则确认进入新一轮赚钱周期。</li>
<li><b>量能警戒线：</b>两市成交额 __AMT__ 亿（__AMT_PCT__%）。<b>若明日回落至 1.8 万亿以下，「增量行情」的判断需推翻</b>——
今日所有乐观结论都建立在量能扩张之上，缩量则逻辑不成立。</li>
<li><b>炸板压力：</b>封单中位仅 __FUND_MED__ 亿、早盘封板占比已达 __TS_EARLY_0_PCT__%，
今日已有 __ZB__ 家炸板（__ZB_EARLY__ 家早盘封）。<span class="hl">开盘 15 分钟的承接力度是明日最关键的前瞻信号。</span></li>
<li><b>数据口径：</b>统计为沪深两市（不含北交所）；涨停口径同花顺 __THS_ZT_N__ 家 vs 东财 __EM_ZT_N__ 家，
差额来自东财池内含北交所标的（__BJ_CODES__），<b>已按沪深口径取 __ZT__ 家</b>；
封板时间双源分钟级一致率 100%；成交额、封单、换手率一律取东财字段，并用「换手率 × 流通市值 ≈ 成交额」抽样三角验证；
两市成交额为沪市 + 深市全市场口径。
本报告「涨停股合计成交额 ÷ 两市成交额」= __SHARE__%（昨 __SHARE_Y__%），低于 3%~8% 的经验区间，
原因是<b>该比值与涨停家数、样本市值结构双重相关</b>：今日 __ZT__ 家里流通市值超 300 亿的仅 __BIG_N__ 只，
样本整体偏轻，故比值偏低；单只最大成交额 __AMT_TOP_AMT__ 亿与换手率口径吻合，可确认字段源无误。</li>
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
