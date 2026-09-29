# -*- coding: utf-8 -*-
"""涨停复盘报告 20260929 vs 20260928（跌停潮次日 / 缩量超跌反抽 / 结构再切换）

用法：python zt_report_20260929.py 20260929
输入：out/zt_stats_20260929.json、out/zt_review_20260929.json、out/zt_review_20260928.json
     昨日跌停池明细 out/_dt0928.json（东财 push2ex getTopicDTPool，sort=fund:asc）
     昨日跌停股今日行情：腾讯快照 qt.gtimg.cn（本脚本内置 RELIQ 常量，已抓取固化）
输出：reports/涨停复盘对比-20260929.html
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
    return s[:2] + ":" + s[2:]


def seal(a, b):
    return a / (a + b) * 100 if (a + b) else 0.0


# ================= 一、情绪三日序列 =================
days = [
    {"d": md(D2) if D2 else "-", "zt": s1["zt_prev"], "zb": s1["zb_prev"], "dt": s1["dt_prev"]},
    {"d": md(D1), "zt": s1["zt"], "zb": s1["zb"], "dt": s1["dt"]},
    {"d": md(D0), "zt": s0["zt"], "zb": s0["zb"], "dt": s0["dt"]},
]
for x in days:
    x["seal"] = seal(x["zt"], x["zb"])

# 参与度 / 承接力 / 破坏力（pitfalls 第 18 条：三者必须同时看）
# 注意：senti[D0]["yest"] 是 D0 抓取时接口返回的「前一交易日」统计（= D1 的今日值），
# 当日「触及涨停 / 触及跌停」必须直接从 review 文件的 ths_zt.total.today 取，不能用 senti[D0]["yest"]。
_d0 = B["dates"][D0]["ths_zt"]["total"]
_d1 = B["dates"][D1]["ths_zt"]["total"]
TOUCH0 = _d0["today"]["history_num"]        # 今日触及涨停家数
TOUCH1 = _d1["today"]["history_num"]        # 昨日触及涨停家数
DTOUCH0 = B["dates"][D0]["ths_zt"]["limit_down_count"]["today"]["history_num"]
DTOUCH1 = B["dates"][D1]["ths_zt"]["limit_down_count"]["today"]["history_num"]
DSEAL0 = B["dates"][D0]["ths_zt"]["limit_down_count"]["today"]["rate"] * 100
DSEAL1 = B["dates"][D1]["ths_zt"]["limit_down_count"]["today"]["rate"] * 100

# ================= 二、指数与量能 =================
IX_ORDER = [("上证指数", "sh000001"), ("深证成指", "sz399001"), ("创业板指", "sz399006"),
            ("科创50", "sh000688"), ("沪深300", "sh000300"), ("中证500", "sh000905"),
            ("中证1000", "sh000852"), ("国证2000", "sz399303"), ("上证50", "sh000016"),
            ("中小100", "sz399005"), ("北证50", "bj899050")]
idx_now = {v["name"]: v for v in B["indexes"].values()}
ix = []
for nm, sym in IX_ORDER:
    v = idx_now.get(nm)
    if v:
        ix.append({"name": nm, "pct": v["pct"], "amt": (v["amount_wan"] or 0) / 10000.0,
                   "price": v["price"]})
ixr = {x["name"]: x for x in ix}
PREV_IDX_PCT = {k: (v.get("prev_pct") or 0.0) for k, v in (S.get("idx_cmp") or {}).items()}

B1 = json.load(open(os.path.join(OUT, f"zt_review_{D1}.json"), encoding="utf-8"))
idx_prev_amt = {}
for v in B1["indexes"].values():
    if isinstance(v, dict) and v.get("name"):
        idx_prev_amt[v["name"]] = (v.get("amount_wan") or 0) / 10000.0
        if v.get("pct") is not None:
            PREV_IDX_PCT.setdefault(v["name"], v["pct"])


def amt_yoy(nm):
    a0, a1 = ixr.get(nm, {}).get("amt", 0), idx_prev_amt.get(nm, 0)
    return (a0 / a1 - 1) * 100 if a1 else 0.0


amt_today = ixr["上证指数"]["amt"] + ixr["深证成指"]["amt"]
tot = S.get("tot") or {}
amt_prev = tot.get("prev") or amt_today
amt_pct = (amt_today / amt_prev - 1) * 100 if amt_prev else 0.0
amt_delta = amt_today - amt_prev

# 风格维度：权重 vs 小微盘 vs 成长
STYLE = ["上证50", "沪深300", "中证500", "中证1000", "国证2000", "科创50", "创业板指", "北证50"]
style_rows = [{"name": n, "pct": ixr.get(n, {}).get("pct", 0.0), "amt_yoy": amt_yoy(n),
               "amt": ixr.get(n, {}).get("amt", 0.0)} for n in STYLE if n in ixr]
STYLE_SORTED = sorted(style_rows, key=lambda x: -x["amt_yoy"])

# ================= 三、连板梯队 =================
lad0 = {int(k): v for k, v in s0["ladder"].items()}
lad1 = {int(k): v for k, v in s1["ladder"].items()}
lad_max = max(max(lad0), max(lad1))
lad_series = lambda d, m: [d.get(i, 0) for i in range(1, m + 1)]
lb_all = sorted([r for r in r0 if (r["lbc"] or 1) >= 2], key=lambda x: (-(x["lbc"] or 0), x["code"]))
maxb = max(lad0) if lad0 else 0
maxb_y = max(lad1) if lad1 else 0

# ================= 四、主线归因 =================
THEMES = [
    ("PCB / 覆铜板 / 元件链", ["PCB", "覆铜板", "HDI", "封装基板", "服务器电源", "高频通讯", "AI服务器", "AI电源"]),
    ("固态电池 / 锂电链", ["固态电池", "钠离子电池", "锂电", "复合集流体", "电池"]),
    ("地产 / 房屋链", ["房地产", "物业管理", "房屋", "租赁", "旧改", "物业经营"]),
    ("传媒出版 / AI应用", ["出版", "短剧", "漫剧", "文化", "传媒", "AI营销", "数字阅读", "财经新媒体", "图书"]),
    ("AI安全 / 数据要素", ["AI安全", "网络安全", "数据安全", "智能体", "数据要素", "政务智能体"]),
    ("汽车 / 机器人", ["机器人", "轴承", "热管理", "智能座舱", "汽车电子", "乘用车", "商用车", "汽车整车"]),
    ("染料 / 化工涨价", ["染料", "颜料", "精细化工", "安赛蜜"]),
    ("农业 / 食品饮料", ["益生菌", "乳酸菌", "果汁", "菜籽油", "矿泉水", "养殖", "生猪"]),
    ("电力 / 环保", ["绿色电力", "风电", "热电", "环保", "环境", "水处理"]),
]
theme_cnt = []
for nm, kws in THEMES:
    hit = [r for r in r0 if any(k in (r["reason"] or "") for k in kws)]
    theme_cnt.append({"name": nm, "n": len(hit),
                      "stocks": [r["name"] + "(" + str(r["lbc"] or 1) + "板)" for r in
                                 sorted(hit, key=lambda x: (-(x["lbc"] or 0), -(x["fund"] or 0)))][:8]})
theme_cnt.sort(key=lambda x: (-x["n"], x["name"]))

# 「华」字辈（name 维度）
hua = sorted([r for r in r0 if "华" in r["name"]], key=lambda x: (-(x["lbc"] or 0), x["code"]))
hua1 = [r for r in r1 if "华" in r["name"]]

# ================= 五、行业迁移 =================
hy0, hy1 = S["hy0"], S["hy1"]
hy_keys = sorted(set(list(hy0) + list(hy1)),
                 key=lambda k: (-(hy0.get(k, 0) * 2 + hy1.get(k, 0)), -hy0.get(k, 0), -hy1.get(k, 0), k))
hy_tbl = [{"name": k, "t": hy0.get(k, 0), "y": hy1.get(k, 0)} for k in hy_keys[:18]]

# ================= 六、昨日涨停股今日表现 =================
adv = [p for p in perf if p["again"]]
adv_rate = len(adv) / len(perf) * 100
pcts = [p["pct"] for p in perf if p["pct"] is not None]
neg = sum(1 for p in pcts if p < 0)
neg_low = sum(1 for p in pcts if p <= -5)
perf_sorted = sorted(perf, key=lambda x: -(x["pct"] if x["pct"] is not None else -999))
top3 = perf_sorted[:3]
bot3 = perf_sorted[-3:]
p_shou = [p for p in perf if (p["lbc"] or 1) == 1]
p_lian = [p for p in perf if (p["lbc"] or 1) >= 2]


def grp(rows):
    n = len(rows)
    if not n:
        return 0, 0.0, 0.0, 0
    a = sum(1 for p in rows if p["again"])
    pp = [p["pct"] for p in rows if p["pct"] is not None]
    return n, a / n * 100, median(pp), sum(1 for p in pp if p < 0)


n_s, r_s, m_s, ng_s = grp(p_shou)
n_l, r_l, m_l, ng_l = grp(p_lian)

# ================= 七、跌停池复盘（核心章节） =================
DT_YD = json.load(open(os.path.join(OUT, "_dt0928.json"), encoding="utf-8"))["data"]["pool"]
DT_TD = json.load(open(os.path.join(OUT, "_dt0929.json"), encoding="utf-8"))["data"]["pool"]
dt_amt_yd = sum(x.get("amount", 0) for x in DT_YD) / 1e8
dt_amt_td = sum(x.get("amount", 0) for x in DT_TD) / 1e8
# 昨日跌停池产业链归并
HW_KW = ["通信设备", "元件", "电子化学", "其他电子", "光学光电", "半导体", "消费电子", "塑料", "金属新材", "自动化设", "专用设备"]
dt_hw_yd = [x for x in DT_YD if x["hybk"] in ("通信设备", "元件")]
dt_amt_hw_yd = sum(x["amount"] for x in dt_hw_yd) / 1e8
dt_big_yd = [x for x in DT_YD if x["ltsz"] > 1e10]
# 昨日跌停的算力硬件链今日表现（腾讯快照，2026-09-29 收盘抓取固化）
RELIQ = {
    "002796": 1.41, "002484": 1.30, "600345": 0.77, "603115": -0.32, "603738": -0.56,
    "603803": 2.52, "600522": 0.03, "002897": -1.15, "603989": -0.14, "000070": 0.25,
    "600105": -3.34, "002579": 3.47, "000636": 1.57, "600498": -1.87, "002396": -0.39,
    "603042": -1.84, "605058": 10.00, "002491": -3.73, "600487": -5.82,
}
rel = [{"c": x["c"], "n": x["n"], "h": x["hybk"], "pct": RELIQ.get(x["c"]),
        "ltsz": x["ltsz"], "amount": x["amount"]} for x in dt_hw_yd]
rel_n = len(rel)
rel_vals = [x["pct"] for x in rel if x["pct"] is not None]
rel_mean = mean(rel_vals)
rel_med = median(rel_vals)
rel_lim = sum(1 for v in rel_vals if v >= 9.8)
rel_neg = sum(1 for v in rel_vals if v < 0)
rel_tx = [x for x in rel if x["h"] == "通信设备"]
rel_yj = [x for x in rel if x["h"] == "元件"]
rel_tx_mean = mean([x["pct"] for x in rel_tx])
rel_yj_mean = mean([x["pct"] for x in rel_yj])
rel_mean_ex = mean([v for v in rel_vals if v < 9.8])

# ================= 八、封板节奏与成交结构 =================
TS_ORDER = ["竞价/秒板", "开盘半小时", "上午盘中", "午后盘中", "尾盘"]
ts0, ts1 = S["timeslot"]["today"], S["timeslot"]["yesterday"]
amts = [r["amount"] for r in r0 if r["amount"]]
amts1 = [r["amount"] for r in r1 if r["amount"]]
funds = [r["fund"] for r in r0 if r["fund"]]
funds1 = [r["fund"] for r in r1 if r["fund"]]
amt_sum, amt_sum1 = sum(amts) / 1e8, sum(amts1) / 1e8
fund_sum, fund_sum1 = sum(funds) / 1e8, sum(funds1) / 1e8
share = amt_sum / amt_today * 100
share1 = amt_sum1 / amt_prev * 100
amt_med = median(amts) / 1e8
amt_med1 = median(amts1) / 1e8
fund_med = median(funds) / 1e8
fund_med1 = median(funds1) / 1e8
oneword = sum(1 for r in r0 if "一字" in r["limit_up_type"])
huanshou = sum(1 for r in r0 if "换手" in r["limit_up_type"])
oneword1 = sum(1 for r in r1 if "一字" in r["limit_up_type"])
huanshou1 = sum(1 for r in r1 if "换手" in r["limit_up_type"])
fund_top = sorted(r0, key=lambda x: -(x["fund"] or 0))[:5]
ft0 = fund_top[0]
ft0_val = (ft0["fund"] or 0) / 1e8
ft0_pct = ft0_val / fund_sum * 100
ft0_ratio = ft0_val / ((ft0["amount"] or 1) / 1e8)
amt_top = sorted(r0, key=lambda x: -(x["amount"] or 0))[:5]

tbl_fund_top = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td>{2}板</td><td>{3:.2f}亿</td><td>{4:.2f}亿</td><td>{5:.1f}x</td></tr>".format(
        esc(x["name"]), x["code"], (x["lbc"] or 1), (x["fund"] or 0) / 1e8, (x["amount"] or 0) / 1e8,
        (x["fund"] or 0) / (x["amount"] or 1))
    for x in fund_top)
tbl_amt_top = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td>{2}板</td><td>{3:.2f}亿</td><td>{4:.2f}亿</td><td>{5}</td></tr>".format(
        esc(x["name"]), x["code"], (x["lbc"] or 1), (x["amount"] or 0) / 1e8, (x["fund"] or 0) / 1e8, esc(x["hybk"]))
    for x in amt_top)
# 炸板池（东财）回封判定
zbpool = (B["dates"][D0].get("em_ZB") or {}).get("pool") or []


def is_limit(z):
    th = 19.8 if z["c"].startswith(("30", "68")) else 9.8
    return z["zdp"] >= th


zb_sealed = [z for z in zbpool if is_limit(z)]
zb_open = [z for z in zbpool if not is_limit(z)]
tbl_zb = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4:+.2f}%</td><td>{5:.2f}亿</td><td>{6:.0f}亿</td></tr>".format(
        esc(z["n"]), z["c"], hhmm(z["fbt"]), esc(z["hybk"]), z["zdp"], z["amount"] / 1e8, z["ltsz"] / 1e8)
    for z in sorted(zb_open, key=lambda x: x["fbt"]))

# ================= 表格片段 =================
tbl_senti = "".join(
    "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td class='hl'>{3}</td><td class='up'>{4}{5}</td></tr>".format(
        lab, ("{:.1f}".format(days[0][k]) if isinstance(days[0][k], float) else days[0][k]),
        ("{:.1f}".format(days[1][k]) if isinstance(days[1][k], float) else days[1][k]),
        ("{:.1f}".format(days[2][k]) if isinstance(days[2][k], float) else days[2][k]),
        "+" if days[2][k] - days[1][k] >= 0 else "",
        ("{:.1f}".format(days[2][k] - days[1][k]) if isinstance(days[2][k], float) else "{:+d}".format(days[2][k] - days[1][k])))
    for lab, k in [("涨停家数", "zt"), ("炸板家数", "zb"), ("封板率(%)", "seal"), ("跌停家数", "dt")])

tbl_lad = "".join(
    "<tr><td>{0} 板</td><td>{1}</td><td class='hl'>{2}</td><td class='{3}'>{4:+d}</td></tr>".format(
        i, lad1.get(i, 0), lad0.get(i, 0),
        "up" if lad0.get(i, 0) - lad1.get(i, 0) > 0 else ("down" if lad0.get(i, 0) - lad1.get(i, 0) < 0 else "mut"),
        lad0.get(i, 0) - lad1.get(i, 0))
    for i in range(lad_max, 0, -1))

tbl_lianban = "".join(
    "<tr><td>{0}板</td><td>{1}</td><td class='hl'>{2}</td><td>{3}</td><td>{4:.2f}亿</td><td>{5:.2f}亿</td><td>{6:.1f}%</td>"
    "<td>{7}</td><td style='text-align:left;color:#4b5563'>{8}</td></tr>".format(
        r["lbc"], r["code"], esc(r["name"]), (r["fbt"][:5] if r["fbt"] else "—"),
        (r["fund"] or 0) / 1e8, (r["amount"] or 0) / 1e8, (r["turnover"] or 0), esc(r["hybk"]), esc(r["reason"]))
    for r in lb_all)

tbl_hy = "".join(
    "<tr><td>{0}</td><td>{1}</td><td class='hl'>{2}</td><td class='{3}'>{4:+d}</td>"
    "<td style='text-align:left;color:#6b7280'>{5}</td></tr>".format(
        esc(h["name"]), h["y"], h["t"],
        "up" if h["t"] - h["y"] > 0 else ("down" if h["t"] - h["y"] < 0 else "mut"),
        h["t"] - h["y"], "流入" if h["t"] - h["y"] > 0 else ("流出" if h["t"] - h["y"] < 0 else "持平"))
    for h in hy_tbl)

tbl_ts = "".join("<tr><td>{0}</td><td>{1}</td><td class='hl'>{2}</td></tr>".format(k, ts1.get(k, 0), ts0.get(k, 0))
                 for k in TS_ORDER)

tbl_theme = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td style='text-align:left'>{2}</td></tr>".format(
        esc(t["name"]), t["n"], "".join("<span class=tag>" + esc(s) + "</span>" for s in t["stocks"]))
    for t in theme_cnt if t["n"] > 0)

tbl_idx = "".join(
    "<tr><td>{0}</td><td class='{1}'>{2:+.2f}%</td><td class='{3}'>{4}</td><td>{5:,.0f}亿</td><td class='down'>{6:+.1f}%</td></tr>".format(
        esc(x["name"]), "up" if x["pct"] >= 0 else "down", x["pct"],
        "up" if PREV_IDX_PCT.get(x["name"], 0) >= 0 else "down",
        ("{:+.2f}%".format(PREV_IDX_PCT[x["name"]]) if x["name"] in PREV_IDX_PCT else "—"),
        x["amt"], amt_yoy(x["name"]))
    for x in ix)

tbl_style = "".join(
    "<tr><td>{0}</td><td class='{1}'>{2:+.2f}%</td><td class='down'>{3:+.1f}%</td><td>{4:,.0f}亿</td></tr>".format(
        esc(x["name"]), "up" if x["pct"] >= 0 else "down", x["pct"], x["amt_yoy"], x["amt"])
    for x in STYLE_SORTED)

tbl_rel = "".join(
    "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3:.0f}亿</td><td class='{4}'>{5:+.2f}%</td></tr>".format(
        x["c"], esc(x["n"]), esc(x["h"]), x["ltsz"] / 1e8, "up" if x["pct"] >= 0 else "down", x["pct"])
    for x in sorted(rel, key=lambda x: -x["pct"]))

tbl_dt_td = "".join(
    "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3:.2f}亿</td><td>{4:.0f}亿</td></tr>".format(
        x["c"], esc(x["n"]), esc(x["hybk"]), x["amount"] / 1e8, x["ltsz"] / 1e8)
    for x in sorted(DT_TD, key=lambda x: -x["amount"]))

tbl_hua = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td>{2}板</td><td>{3}</td><td style='text-align:left;color:#4b5563'>{4}</td></tr>".format(
        esc(x["name"]), x["code"], (x["lbc"] or 1), esc(x["hybk"]), esc(x["reason"]))
    for x in hua)

perf_top = "、".join("{}{:+.1f}%".format(esc(p["name"]), p["pct"]) for p in top3)
perf_bot = "、".join("{}{:+.1f}%".format(esc(p["name"]), p["pct"]) for p in bot3)

# ================= 占位符 =================
V = {}
def P(k, v):
    V["__" + k + "__"] = str(v)


P("GEN_AT", B["generated_at"])
P("D0", md(D0)); P("D1", md(D1)); P("D2", md(D2))
P("ZT", s0["zt"]); P("ZT_Y", s1["zt"]); P("ZT_D", "{:+d}".format(s0["zt"] - s1["zt"]))
P("ZB", s0["zb"]); P("ZB_Y", s1["zb"]); P("ZB_D", "{:+d}".format(s0["zb"] - s1["zb"]))
P("DT", s0["dt"]); P("DT_Y", s1["dt"]); P("DT_D", "{:+d}".format(s0["dt"] - s1["dt"]))
P("SEAL", "{:.1f}".format(s0["seal_rate"] * 100))
P("SEAL_Y", "{:.1f}".format(s1["seal_rate"] * 100))
P("SEAL_D", "{:+.1f}".format((s0["seal_rate"] - s1["seal_rate"]) * 100))
P("TOUCH", TOUCH0); P("TOUCH_Y", TOUCH1); P("TOUCH_D", "{:+d}".format(TOUCH0 - TOUCH1))
P("DTOUCH", DTOUCH0); P("DTOUCH_Y", DTOUCH1)
P("DSEAL", "{:.1f}".format(DSEAL0)); P("DSEAL_Y", "{:.1f}".format(DSEAL1))
P("ZTDT", "{:.1f}".format(s0["zt"] / s0["dt"] if s0["dt"] else 0))
P("ZTDT_Y", "{:.1f}".format(s1["zt"] / s1["dt"] if s1["dt"] else 0))
P("ZTDT_0", "{:.1f}".format(days[0]["zt"] / days[0]["dt"] if days[0]["dt"] else 0))
P("MAXB", maxb); P("MAXB_Y", maxb_y)
P("LB", s0["lianban"]); P("LB_Y", s1["lianban"])
P("SB", s0["shouban"]); P("SB_Y", s1["shouban"])
P("SB_PCT", "{:.0f}".format(s0["shouban"] / s0["zt"] * 100))
P("AMT", "{:,.0f}".format(amt_today)); P("AMT_Y", "{:,.0f}".format(amt_prev))
P("AMT_D", "{:+,.0f}".format(amt_delta)); P("AMT_PCT", "{:+.1f}".format(amt_pct))
P("STYLE_SHRINK_MAX", esc(STYLE_SORTED[-1]["name"])); P("STYLE_SHRINK_MAX_V", "{:+.1f}".format(STYLE_SORTED[-1]["amt_yoy"]))
P("STYLE_SHRINK_MIN", esc(STYLE_SORTED[0]["name"])); P("STYLE_SHRINK_MIN_V", "{:+.1f}".format(STYLE_SORTED[0]["amt_yoy"]))
P("SH50_YOY", "{:+.1f}".format(amt_yoy("上证50"))); P("KC_YOY", "{:+.1f}".format(amt_yoy("科创50")))
P("GZ2000_YOY", "{:+.1f}".format(amt_yoy("国证2000"))); P("ZZ1000_YOY", "{:+.1f}".format(amt_yoy("中证1000")))
P("ADV_RATE", "{:.1f}".format(adv_rate)); P("ADV_N", len(adv)); P("ADV_TOT", len(perf))
P("PERF_MEAN", "{:+.2f}".format(mean(pcts))); P("PERF_MED", "{:+.2f}".format(median(pcts)))
P("PERF_MAX", "{:+.2f}".format(max(pcts))); P("PERF_MIN", "{:+.2f}".format(min(pcts)))
P("PERF_MAX_NAME", esc(perf_sorted[0]["name"]))
P("PERF_MIN_NAME", esc(perf_sorted[-1]["name"])); P("PERF_MIN_LB", perf_sorted[-1]["lbc"])
P("PERF_NEG_MAX_NAME", esc(sorted([p for p in perf if p["pct"] is not None], key=lambda x: x["pct"])[0]["name"]))
P("PERF_TOP3", perf_top); P("PERF_BOT3", perf_bot)
P("NEG", neg); P("NEG_PCT", "{:.1f}".format(neg / len(pcts) * 100)); P("NEG_LOW", neg_low)
P("GRP_S_N", n_s); P("GRP_S_R", "{:.1f}".format(r_s)); P("GRP_S_M", "{:+.2f}".format(m_s)); P("GRP_S_NG", ng_s)
P("GRP_L_N", n_l); P("GRP_L_R", "{:.1f}".format(r_l)); P("GRP_L_M", "{:+.2f}".format(m_l)); P("GRP_L_NG", ng_l)
P("AMT_SUM", "{:.0f}".format(amt_sum)); P("AMT_SUM_Y", "{:.0f}".format(amt_sum1))
P("SHARE", "{:.1f}".format(share)); P("SHARE_Y", "{:.1f}".format(share1))
P("AMT_MED", "{:.2f}".format(amt_med)); P("AMT_MED_Y", "{:.2f}".format(amt_med1))
P("AMT_MED_PCT", "{:+.1f}".format((amt_med / amt_med1 - 1) * 100 if amt_med1 else 0))
P("FUND_SUM", "{:.1f}".format(fund_sum)); P("FUND_SUM_Y", "{:.1f}".format(fund_sum1))
P("FUND_SUM_PCT", "{:+.1f}".format((fund_sum / fund_sum1 - 1) * 100 if fund_sum1 else 0))
P("FUND_MED", "{:.2f}".format(fund_med)); P("FUND_MED_Y", "{:.2f}".format(fund_med1))
P("FUND_MED_PCT", "{:+.1f}".format((fund_med / fund_med1 - 1) * 100 if fund_med1 else 0))
P("FUND_AVG", "{:.2f}".format(fund_sum / s0["zt"]))
P("ONEWORD", oneword); P("ONEWORD_Y", oneword1)
P("ONEWORD_PCT", "{:.1f}".format(oneword / s0["zt"] * 100))
P("HUANSHOU", huanshou); P("HUANSHOU_Y", huanshou1)
P("HUANSHOU_PCT", "{:.0f}".format(huanshou / s0["zt"] * 100))
P("FT0", esc(ft0["name"])); P("FT0_V", "{:.2f}".format(ft0_val)); P("FT0_PCT", "{:.1f}".format(ft0_pct))
P("FT0_RATIO", "{:.1f}".format(ft0_ratio)); P("FT0_AMT", "{:.2f}".format((ft0["amount"] or 0) / 1e8))
P("FT0_LB", ft0["lbc"]); P("FT0_REASON", esc(ft0["reason"]))
P("LB_TOP1", esc(lb_all[0]["name"])); P("LB_TOP1_REASON", esc(lb_all[0]["reason"]))
P("LB_TOP2", esc(lb_all[1]["name"])); P("LB_TOP2_LB", lb_all[1]["lbc"])
P("LB_TOP3", esc(lb_all[2]["name"])); P("LB_TOP3_LB", lb_all[2]["lbc"])
P("HUA_N", len(hua)); P("HUA_Y", len(hua1)); P("HUA_LB", sum(1 for x in hua if (x["lbc"] or 1) >= 2))
P("HY_YJ", hy1.get("元件", 0)); P("HY_YJ0", hy0.get("元件", 0))
P("HY_FDC", hy1.get("房地产开", 0)); P("HY_FDC0", hy0.get("房地产开", 0))
P("HY_DC", hy1.get("电池", 0)); P("HY_DC0", hy0.get("电池", 0))
P("HY_TXD", hy1.get("通信设备", 0)); P("HY_TXD0", hy0.get("通信设备", 0))
P("HY_TYSB", hy1.get("通用设备", 0)); P("HY_TYSB0", hy0.get("通用设备", 0))
P("HY_CB", hy1.get("出版", 0)); P("HY_CB0", hy0.get("出版", 0))
P("HY_GGYX", hy1.get("广告营销", 0)); P("HY_GGYX0", hy0.get("广告营销", 0))
P("DT_YD_N", s1["dt"]); P("DT_TD_N", s0["dt"])
P("DT_AMT_YD", "{:.0f}".format(dt_amt_yd)); P("DT_AMT_TD", "{:.1f}".format(dt_amt_td))
P("DT_AMT_RATIO", "{:.1f}".format(dt_amt_yd / amt_sum1))
P("DT_AMT_RATIO_TD", "{:.1f}".format(dt_amt_td / amt_sum))
P("GZ2000_PCT", "{:+.2f}".format(ixr.get("国证2000", {}).get("pct", 0)))
P("ZX100_PCT", "{:+.2f}".format(ixr.get("中小100", {}).get("pct", 0)))
P("SH50_PCT", "{:+.2f}".format(ixr.get("上证50", {}).get("pct", 0)))
P("TS_AM_0", ts0.get("上午盘中", 0)); P("TS_AM_1", ts1.get("上午盘中", 0))
P("DT_HW_N", len(dt_hw_yd)); P("DT_HW_PCT", "{:.0f}".format(len(dt_hw_yd) / len(DT_YD) * 100))
P("DT_HW_AMT", "{:.0f}".format(dt_amt_hw_yd))
P("DT_BIG_N", len(dt_big_yd))
P("REL_N", rel_n); P("REL_MEAN", "{:+.2f}".format(rel_mean)); P("REL_MED", "{:+.2f}".format(rel_med))
P("REL_MEAN_EX", "{:+.2f}".format(rel_mean_ex)); P("REL_LIM", rel_lim); P("REL_NEG", rel_neg)
P("REL_TX_N", len(rel_tx)); P("REL_TX_MEAN", "{:+.2f}".format(rel_tx_mean))
P("REL_YJ_N", len(rel_yj)); P("REL_YJ_MEAN", "{:+.2f}".format(rel_yj_mean))
P("ZB_N", s0["zb"]); P("ZB_OPEN_N", len(zb_open)); P("ZB_SEALED_N", len(zb_sealed))
P("ZB_MIN_LTSZ", "{:.0f}".format(min(z["ltsz"] for z in zbpool) / 1e8))
P("ZB_MAX_LTSZ", "{:.0f}".format(max(z["ltsz"] for z in zbpool) / 1e8))
P("TS_EARLY_Y", ts1.get("竞价/秒板", 0) + ts1.get("开盘半小时", 0))
P("TS_EARLY_Y_PCT", "{:.0f}".format((ts1.get("竞价/秒板", 0) + ts1.get("开盘半小时", 0)) / s1["zt"] * 100))
P("TS_EARLY_0", ts0.get("竞价/秒板", 0) + ts0.get("开盘半小时", 0))
P("TS_EARLY_0_PCT", "{:.0f}".format((ts0.get("竞价/秒板", 0) + ts0.get("开盘半小时", 0)) / s0["zt"] * 100))
P("TS_PM0", ts0.get("午后盘中", 0)); P("TS_PM1", ts1.get("午后盘中", 0))
P("TBL_SENTI", tbl_senti); P("TBL_LAD", tbl_lad); P("TBL_LIANBAN", tbl_lianban)
P("TBL_HY", tbl_hy); P("TBL_TS", tbl_ts); P("TBL_THEME", tbl_theme); P("TBL_IDX", tbl_idx)
P("TBL_STYLE", tbl_style); P("TBL_REL", tbl_rel); P("TBL_DT_TD", tbl_dt_td); P("TBL_HUA", tbl_hua)
P("TBL_FUND_TOP", tbl_fund_top); P("TBL_AMT_TOP", tbl_amt_top); P("TBL_ZB", tbl_zb)
P("JS_DAYS", json.dumps([d["d"] for d in days], ensure_ascii=False))
P("JS_ZT", json.dumps([d["zt"] for d in days]))
P("JS_ZB", json.dumps([d["zb"] for d in days]))
P("JS_DT", json.dumps([d["dt"] for d in days]))
P("JS_SEAL", json.dumps([round(d["seal"], 1) for d in days]))
P("JS_IX_NAME", json.dumps([x["name"] for x in ix][::-1], ensure_ascii=False))
P("JS_IX_PCT", json.dumps([round(x["pct"], 2) for x in ix][::-1]))
P("JS_AMT_NAME", json.dumps([x["name"] for x in STYLE_SORTED][::-1], ensure_ascii=False))
P("JS_AMT_YOY", json.dumps([round(x["amt_yoy"], 1) for x in STYLE_SORTED][::-1]))
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
P("JS_REL_NAME", json.dumps([x["n"] for x in rel], ensure_ascii=False))
P("JS_REL_PCT", json.dumps([round(x["pct"], 2) for x in rel]))
P("JS_REL_COLOR", json.dumps(["#d93025" if x["h"] == "元件" else "#e08b3a" for x in rel]))

# ================= HTML =================
HTML_T = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>涨停复盘 · 2026-09-29（对比 9-28）</title>
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
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin:16px 0 4px}
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
.chart{width:100%;height:330px}.chart-sm{width:100%;height:290px}
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
<h1>涨停复盘 · 2026-09-29（周二）</h1>
<div class="sub">对比基准：2026-09-28（周一）｜口径：沪深两市（不含北交所）｜数据源：同花顺涨停池 + 东方财富涨停/炸板/跌停池 + 腾讯行情快照 + westock 行业/概念榜</div>

<div class="lead">
<p class="hl">一句话结论：跌停潮次日的「缩量超跌反抽」——情绪三项指标全面回摆，但成交额缩 __AMT_PCT__%，涨停家数却增加 __ZT_D__ 家，<u>是存量资金在低位做扩散，不是新增资金进场</u>。</p>
<p>昨日盘面是「参与度↓ + 承接力↓ + 破坏力↑」的最差组合（触及涨停 __TOUCH_Y__ 家、封板率 __SEAL_Y__%、跌停 __DT_Y__ 家）；
今日三项同时反转：<span class="hl">触及涨停 __TOUCH__ 家、封板率 __SEAL__%（本轮 9/18 以来最高）、跌停仅 __DT__ 家</span>，
跌停封死率由 __DSEAL_Y__% 降到 __DSEAL__%，跌停池里算力硬件链从 __DT_HW_N__ 只清零。</p>
<p>但修复是不对称的：昨日跌得最狠的算力硬件链 __REL_N__ 只，今日均值仅 __REL_MEAN__%（剔除唯一反包的澳弘电子后 __REL_MEAN_EX__%）——
<span class="hl">光通信/通信设备方向（__REL_TX_N__ 只）均值 __REL_TX_MEAN__%，几乎没有修复</span>。
今日资金真正买的是 PCB/元件（__HY_YJ__→__HY_YJ0__ 家）与地产链（__HY_FDC__→__HY_FDC0__ 家），
前者是超跌反抽，后者是消息驱动的低位切换。<span class="hl">反抽可以参与，但不等于趋势反转。</span></p>
</div>

<div class="kpis">
  <div class="kpi"><div class="lbl">涨停家数</div><div class="val up">__ZT__</div>
    <div class="dt mut">昨日 __ZT_Y__ <span class="up">__ZT_D__</span></div></div>
  <div class="kpi"><div class="lbl">触及涨停家数</div><div class="val up">__TOUCH__</div>
    <div class="dt mut">昨日 __TOUCH_Y__ <span class="up">__TOUCH_D__</span></div></div>
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
  <div class="kpi"><div class="lbl">炸板池回封</div><div class="val">__ZB_SEALED_N__/__ZB_N__</div>
    <div class="dt mut">跌停封死率 __DSEAL__%</div></div>
</div>

<div class="card">
<h2>一、市场情绪温度计：三项指标同时回摆</h2>
<table>
<tr><th>指标</th><th>__D2__（周四·节前）</th><th>__D1__（周一）</th><th>__D0__（周二）</th><th>__D0__ 环比</th></tr>
__TBL_SENTI__
<tr><td>涨停/跌停比</td><td>__ZTDT_0__</td><td>__ZTDT_Y__</td><td class="hl">__ZTDT__</td><td class="up">情绪回摆</td></tr>
</table>
<div class="note" style="margin-top:10px">
<span class="hl">拆成三个相互独立的口径看，今日是「三好」：</span>
参与度（触及涨停家数）__TOUCH_Y__ → __TOUCH__ 家（__TOUCH_D__）；
承接力（封板率）__SEAL_Y__% → __SEAL__%（__SEAL_D__pct）；
破坏力（跌停家数）__DT_Y__ → __DT__ 家、封死率 __DSEAL_Y__% → __DSEAL__%。
昨日是史上罕见的「参与↓承接↓破坏↑」三重恶化（跌停 __DT_Y__ 家、触及跌停 __DTOUCH_Y__ 家），今日全部回摆 —— 这是典型的<b>恐慌一次性释放后的技术性修复</b>。
但要注意：趋势反转需要量能配合，而今日量能是缩的（见第二节）。
</div>
<div id="c_senti" class="chart" style="margin-top:16px"></div>
</div>

<div class="card">
<h2>二、指数与量能：全线收红，但量能创本轮新低</h2>
<div class="two">
<div>
<table>
<tr><th>指数</th><th>今日</th><th>昨日</th><th>成交额</th><th>成交额环比</th></tr>
__TBL_IDX__
</table>
<div class="note" style="margin-top:10px">
<b>量能是本轮反抽最大的软肋：</b>两市成交额 __AMT__ 亿，环比 __AMT_D__ 亿（__AMT_PCT__%），为本轮 9/21 修复以来最低。
全部 11 个指数<b>无一例外缩量</b>：缩得最少的是 __STYLE_SHRINK_MIN__（__STYLE_SHRINK_MIN_V__%），
缩得最狠的是 __STYLE_SHRINK_MAX__（__STYLE_SHRINK_MAX_V__%）。
<span class="hl">指数微涨 + 全面缩量 = 抛压衰竭型反抽，不是资金回补型反攻。</span>
</div>
</div>
<div><div id="c_amt" class="chart-sm"></div></div>
</div>
<div class="two" style="margin-top:18px">
<div><div id="c_idx" class="chart-sm"></div></div>
<div>
<table>
<tr><th>风格指数</th><th>今日涨跌</th><th>成交额环比</th><th>成交额</th></tr>
__TBL_STYLE__
</table>
<div class="note" style="margin-top:10px">
涨跌幅上「小盘略强于权重」：国证2000 __GZ2000_PCT__%、中小100 __ZX100_PCT__% 居前，上证50 仅 __SH50_PCT__%。
但成交额环比是<b>普缩、且缩幅接近</b>（上证50 __SH50_YOY__% ~ 中证1000 __ZZ1000_YOY__%），
没有出现 9/23–9/28 那样的「权重吸血 / 小盘失血」极端分化。
<span class="hl">这说明今日不是存量搬家，而是全体观望 —— 钱既没进权重，也没进小盘。</span>
</div>
</div>
</div>
</div>

<div class="card">
<h2>三、连板梯队：宽度大增，高度延伸到 6 板</h2>
<div class="two">
<div><div id="c_lad" class="chart-sm"></div></div>
<div>
<table>
<tr><th>梯队</th><th>__D1__</th><th>__D0__</th><th>变化</th></tr>
__TBL_LAD__
<tr><td>合计</td><td>__ZT_Y__</td><td class="hl">__ZT__</td><td class="up">__ZT_D__</td></tr>
</table>
<div class="note" style="margin-top:10px">
首板 __SB__ 家（昨 __SB_Y__），连板股 __LB__ 家（昨 __LB_Y__），最高 __MAXB__ 板（__LB_TOP1__，__LB_TOP1_REASON__）。
首板占比 __SB_PCT__%——<span class="hl">宽度仍然靠首板撑，但 6 板高度由新华传媒独立走出</span>，
2 板梯队 3 → 7 只属正常接力，4 板 0 → 1 只（雪龙集团）。
</div>
</div>
</div>
<h3>今日连板股全名单（__LB__ 只）</h3>
<table>
<tr><th>高度</th><th>代码</th><th>名称</th><th>首封</th><th>封单</th><th>成交额</th><th>换手</th><th>行业</th><th>涨停原因</th></tr>
__TBL_LIANBAN__
</table>
<div class="note" style="margin-top:10px">
<span class="hl">需要单独标注的风险点：__FT0__（__FT0_LB__ 板）封单 __FT0_V__ 亿，占全场封单合计的 __FT0_PCT__%，而其全天成交仅 __FT0_AMT__ 亿（封单/成交 = __FT0_RATIO__ 倍）。</span>
这是极度锁仓的形态：好处是无人卖、板很稳；风险是<b>没有换手就没有承接盘，一旦开板容易一步到位</b>。此票已连续三日封单全市场第一。
</div>
</div>

<div class="card">
<h2>四、主线归因：PCB 超跌反抽 + 地产链消息驱动，双线并行</h2>
<div id="c_theme" class="chart"></div>
<table style="margin-top:14px">
<tr><th>主线</th><th>涨停家数</th><th>代表个股</th></tr>
__TBL_THEME__
</table>
<div class="note" style="margin-top:12px">
今日<b>没有单一主线</b>，是「超跌反抽线 + 消息驱动线」并行：<br>
<b>① PCB / 覆铜板 / 元件链（__HY_YJ0__ 家，今日最大方向）。</b>这是昨日跌得最惨的方向（元件 __HY_YJ__ 只跌停），今日被整体买回；
westock 口径「元件」行业涨幅 +2.51%、主力净流入 29.5 亿（全行业第一），「覆铜板」概念 +3.75%。代表：崇达技术、超声电子（成交 27.49 亿）、迅捷兴（+20.01%）、奥士康、澳弘电子、协和电子、依顿电子。<br>
<b>② 地产 / 房屋链（__HY_FDC0__ 家）。</b>消息面驱动，westock「房地产开发」行业 +4.16%（全行业涨幅第一）、主力净流入 13.8 亿，房屋租赁 +3.58%、租售同权 +3.13%。
__AMT_TOP_LEAD__为全场涨停股成交额第一，另滨江集团、信达地产、华发股份、深物业Ａ、华联控股。<br>
<b>③ 固态电池 / 锂电链。</b>国轩高科封单 6.25 亿（全场第二，仅次于新华传媒）、成交 13.02 亿，带动金龙羽、紫竹高科、英联股份、传艺科技、上海洗霸等；westock「固液电池」概念 +3.19%。<br>
<b>④ 传媒出版 / AI 应用。</b>新华传媒（6 板）、新华文轩、中国出版、掌阅科技、华媒控股、引力传媒；westock「数字媒体」+3.67%、「出版」+3.17%。<br>
<b>⑤ 「华」字辈（__HUA_N__ 只，昨 __HUA_Y__ 只）。</b>其中 __HUA_LB__ 只位于 2 板及以上 —— 与 9/22 同源，仍是主线真空期最容易聚拢资金的名称博弈，持续性依赖龙头。
<br>注：reason_type 为多标签，同一只股票可归入多条主线，故各主线家数之和大于涨停总数。
</div>
</div>

<div class="card">
<h2>五、行业迁移：元件、地产、电池三线流入，通用设备/光学光电退出</h2>
<div id="c_hy" class="chart" style="height:410px"></div>
<table style="margin-top:14px">
<tr><th>行业</th><th>__D1__</th><th>__D0__</th><th>增减</th><th>读数</th></tr>
__TBL_HY__
</table>
<div class="note" style="margin-top:12px">
<b>流入端：</b>元件 __HY_YJ__→__HY_YJ0__ 家、房地产开 __HY_FDC__→__HY_FDC0__ 家、电池 __HY_DC__→__HY_DC0__ 家、
出版 __HY_CB__→__HY_CB0__ 家、广告营销 __HY_GGYX__→__HY_GGYX0__ 家。<br>
<b>流出端：</b>通用设备 __HY_TYSB__→__HY_TYSB0__ 家（昨日的机器人/仪器方向今日清零），
光学光电、商用车、风电设备、影视院线、非白酒、文娱用品、养殖业、光伏设备各流出 1 只。<br>
<span class="hl">关键读数：昨日跌停最多的「通信设备」（__DT_HW_YD_N__ 只跌停中的 12 只）今日涨停家数为 0</span>
—— 资金买回了 PCB/元件，却没有碰光通信。这决定了本次反抽是「结构性」而非「全面性」。
</div>
</div>

<div class="card">
<h2>六、昨日涨停股今日表现：晋级率回到 30%，最弱三只全部来自首板</h2>
<div class="kpis" style="grid-template-columns:repeat(auto-fit,minmax(140px,1fr))">
  <div class="kpi"><div class="lbl">晋级率</div><div class="val">__ADV_RATE__%</div><div class="dt mut">__ADV_N__/__ADV_TOT__</div></div>
  <div class="kpi"><div class="lbl">平均涨幅</div><div class="val up">__PERF_MEAN__%</div><div class="dt mut">中位 __PERF_MED__%</div></div>
  <div class="kpi"><div class="lbl">翻绿比例</div><div class="val down">__NEG_PCT__%</div><div class="dt mut">__NEG__ 只（其中跌超5% __NEG_LOW__ 只）</div></div>
  <div class="kpi"><div class="lbl">最强</div><div class="val up">__PERF_MAX__%</div><div class="dt mut">__PERF_MAX_NAME__</div></div>
  <div class="kpi"><div class="lbl">最弱</div><div class="val down">__PERF_MIN__%</div><div class="dt mut">__PERF_MIN_NAME__（昨 __PERF_MIN_LB__ 板）</div></div>
</div>
<div class="note" style="margin-top:14px">
分组看：昨日首板 __GRP_S_N__ 只，晋级率 __GRP_S_R__%、中位 __GRP_S_M__%、翻绿 __GRP_S_NG__ 只；
昨日连板 __GRP_L_N__ 只，晋级率 __GRP_L_R__%、中位 __GRP_L_M__%、翻绿 __GRP_L_NG__ 只。
<b>连板组溢价（__GRP_L_M__%）明显低于首板组（__GRP_S_M__%）</b>，与 9/23、9/24 的「连板强于首板」完全相反。
最弱三只为 __PERF_BOT3__ —— <span class="hl">全部来自昨日首板，而非高位板</span>，说明今日的杀跌是个股行为（业绩/消息），不是高位股集体退潮。
</div>
<div id="c_perf" class="chart" style="height:700px;margin-top:8px"></div>
</div>

<div class="card">
<h2>七、跌停潮复盘：算力硬件链从 __DT_HW_N__ 只清零，但只修复了一只</h2>
<div class="two">
<div>
<table>
<tr><th>项目</th><th>__D1__（周一）</th><th>__D0__（周二）</th></tr>
<tr><td>跌停家数</td><td class="hl">__DT_Y__</td><td class="hl">__DT__</td></tr>
<tr><td>触及跌停家数</td><td>__DTOUCH_Y__</td><td>__DTOUCH__</td></tr>
<tr><td>跌停封死率</td><td>__DSEAL_Y__%</td><td>__DSEAL__%</td></tr>
<tr><td>跌停股合计成交</td><td>__DT_AMT_YD__亿</td><td class="hl">__DT_AMT_TD__亿</td></tr>
<tr><td>跌停股合计成交 / 当日涨停股成交</td><td>__DT_AMT_RATIO__倍</td><td class="hl">__DT_AMT_RATIO_TD__倍</td></tr>
<tr><td>其中算力硬件链（通信设备+元件）</td><td class="hl">__DT_HW_N__ 只（__DT_HW_PCT__%）</td><td>0 只</td></tr>
<tr><td>流通市值 &gt; 100 亿的只数</td><td>__DT_BIG_N__ 只</td><td>0 只</td></tr>
</table>
<div class="note" style="margin-top:10px">
昨日跌停 __DT_Y__ 家（触及 __DTOUCH_Y__ 家、封死率 __DSEAL_Y__%），今日只剩 __DT__ 家（封死率 __DSEAL__%），
合计成交由 __DT_AMT_YD__ 亿骤降到 __DT_AMT_TD__ 亿。<br>
<span class="hl">跌停池已完全「去板块化」</span>：今日 10 只分散在化学制品2/服装家纺/光伏设备/种植业/文娱用品/一般零售/农产品加/纺织制造/非白酒，
无一是板块性杀跌，多为个股基本面或前日高位股的补跌。
</div>
</div>
<div><div id="c_rel" class="chart" style="height:430px"></div></div>
</div>
<h3>昨日跌停的算力硬件链 __REL_N__ 只，今日表现</h3>
<table>
<tr><th>代码</th><th>名称</th><th>东财行业</th><th>流通市值</th><th>今日涨跌</th></tr>
__TBL_REL__
</table>
<div class="note" style="margin-top:12px">
<span class="hl">这是本报告最重要的一张表。</span>__REL_N__ 只昨日跌停的算力硬件链，今日均值 __REL_MEAN__%、中位 __REL_MED__%，
仅 __REL_LIM__ 只反包涨停（澳弘电子 605058，昨跌停 → 今涨停）；剔除它之后均值 __REL_MEAN_EX__%（即整体仍是亏的）。
分方向看：<b>通信设备/光通信 __REL_TX_N__ 只均值 __REL_TX_MEAN__%</b>（亨通光电 -5.82%、通鼎互联 -3.73%、永鼎股份 -3.34% 继续跌），
<b>元件/PCB 7 只均值 __REL_YJ_MEAN__%</b>。<br>
<span class="hl">结论：这不是「算力硬件链修复」，而是「PCB/元件单方向的资金重新选择」。</span>
今日涨停的 7 只元件股里，只有澳弘电子来自昨日跌停池，其余 6 只（崇达技术、超声电子、迅捷兴、协和电子、依顿电子、奥士康）昨日虽也大跌（-2.7% ~ -14.5%）但未跌停 ——
说明资金挑的是<b>「跌得多 + 有 AI 服务器/高频高速叙事 + 盘子够大能承载」</b>的品种，而非无差别抄底。
</div>
<h3>今日跌停池明细（__DT__ 只）</h3>
<table>
<tr><th>代码</th><th>名称</th><th>东财行业</th><th>成交额</th><th>流通市值</th></tr>
__TBL_DT_TD__
</table>
<h3>炸板池明细（东财 __ZB_N__ 只，未回封 __ZB_OPEN_N__ 只）</h3>
<table>
<tr><th>名称</th><th>代码</th><th>首次触板</th><th>行业</th><th>收盘涨跌</th><th>成交额</th><th>流通市值</th></tr>
__TBL_ZB__
</table>
<div class="note" style="margin-top:10px">
炸板池 __ZB_N__ 只中 <b>__ZB_OPEN_N__ 只未回封、__ZB_SEALED_N__ 只回封</b>；
未回封个股流通市值区间 __ZB_MIN_LTSZ__–__ZB_MAX_LTSZ__ 亿，属于中小市值零星炸板（如华微电子 108 亿、首开股份 87 亿），
不见 9/23 那种「万科Ａ/科华数据」级别的大票冲板失败。
</div>
</div>

<div class="card">
<h2>八、封板节奏与成交结构：封单变厚，节奏略后移</h2>
<div class="two">
<div><div id="c_ts" class="chart-sm"></div></div>
<div>
<table>
<tr><th>封板时段</th><th>__D1__</th><th>__D0__</th></tr>
__TBL_TS__
</table>
<div class="note" style="margin-top:10px">
昨日早盘封板 __TS_EARLY_Y__/__ZT_Y__ = __TS_EARLY_Y_PCT__%（恐慌性杀跌后开盘一把定方向），
今日早盘 __TS_EARLY_0__/__ZT__ = __TS_EARLY_0_PCT__%，午后封板 __TS_PM0__ 家（昨 __TS_PM1__ 家）。
<span class="hl">节奏整体后移、且上午盘中封板明显增多（__TS_AM_0__ 只，昨 __TS_AM_1__ 只）</span>，
说明资金是「边看边打」而不是开盘抢筹 —— 与缩量的判断一致。
</div>
</div>
</div>
<div class="kpis" style="grid-template-columns:repeat(auto-fit,minmax(155px,1fr));margin-top:16px">
  <div class="kpi"><div class="lbl">涨停股合计成交额</div><div class="val">__AMT_SUM__亿</div><div class="dt mut">占两市 __SHARE__%（昨 __SHARE_Y__%）</div></div>
  <div class="kpi"><div class="lbl">单只中位成交额</div><div class="val">__AMT_MED__亿</div><div class="dt mut">昨 __AMT_MED_Y__亿 <span class="up">__AMT_MED_PCT__%</span></div></div>
  <div class="kpi"><div class="lbl">封单合计</div><div class="val">__FUND_SUM__亿</div><div class="dt mut">昨 __FUND_SUM_Y__亿 <span class="up">__FUND_SUM_PCT__%</span></div></div>
  <div class="kpi"><div class="lbl">封单中位数</div><div class="val">__FUND_MED__亿</div><div class="dt mut">昨 __FUND_MED_Y__亿 <span class="up">__FUND_MED_PCT__%</span></div></div>
  <div class="kpi"><div class="lbl">一字板</div><div class="val">__ONEWORD__</div><div class="dt mut">昨 __ONEWORD_Y__ 只，占比 __ONEWORD_PCT__%</div></div>
  <div class="kpi"><div class="lbl">换手板</div><div class="val">__HUANSHOU__</div><div class="dt mut">占 __HUANSHOU_PCT__%（昨 __HUANSHOU_Y__ 只）</div></div>
</div>
<div class="two" style="margin-top:18px">
<div>
<h3>封单前五</h3>
<table>
<tr><th>名称</th><th>代码</th><th>高度</th><th>封单</th><th>成交额</th><th>封单/成交</th></tr>
__TBL_FUND_TOP__
</table>
</div>
<div>
<h3>成交额前五</h3>
<table>
<tr><th>名称</th><th>代码</th><th>高度</th><th>成交额</th><th>封单</th><th>行业</th></tr>
__TBL_AMT_TOP__
</table>
</div>
</div>
<div class="note" style="margin-top:12px">
今日与昨日最大的结构差异是<b>封单整体变厚</b>：封单合计 __FUND_SUM__ 亿（昨 __FUND_SUM_Y__ 亿，__FUND_SUM_PCT__%），
中位 __FUND_MED__ 亿（昨 __FUND_MED_Y__ 亿，__FUND_MED_PCT__%），一字板 __ONEWORD__ 只（昨 __ONEWORD_Y__ 只）。
同时单只中位成交额 __AMT_MED__ 亿（昨 __AMT_MED_Y__ 亿，__AMT_MED_PCT__%）。
<span class="hl">封单变厚 + 换手下降 + 缩量 = 卖压衰竭后的「轻仓锁板」</span>，比昨日「薄封单 + 高换手」健康，但也意味着持仓者惜售、增量观望，方向仍靠消息面推动。
</div>
</div>

<div class="card">
<h2>九、资金运动的三个结论</h2>
<ul>
<li><b>① 总量：缩量。是「抛压衰竭」不是「资金回补」。</b>两市成交额 __AMT__ 亿（__AMT_PCT__%），
涨停家数却由 __ZT_Y__ 增至 __ZT__ 家、跌停由 __DT_Y__ 降到 __DT__ 家。
<span class="hl">家数改善 + 量能萎缩的组合，只有「卖的人先撤了」一种解释</span>，尚不能证明买盘回来了。
若后续两日成交额仍低于 1.5 万亿，本次只能定性为超跌反抽。</li>
<li><b>② 方向：结构性，不是全面性。</b>昨日跌停的算力硬件链 __REL_N__ 只今日均值 __REL_MEAN__%（剔除澳弘电子 __REL_MEAN_EX__%），
其中通信设备/光通信 __REL_TX_N__ 只均值 __REL_TX_MEAN__%；资金改买 PCB/元件（涨停 __HY_YJ0__ 家）与地产链（__HY_FDC0__ 家）。
<span class="hl">同一条产业链内部出现「PCB 被买回、光通信被抛弃」的强分化</span>，
说明资金在做的是「挑品种重定价」，而不是「抄板块的底」。</li>
<li><b>③ 深度：锁仓特征明显，风险单向集中。</b>封单合计 __FUND_SUM__ 亿（__FUND_SUM_PCT__%）、中位封单 __FUND_MED__ 亿（__FUND_MED_PCT__%），
但 __FT0__ 一只就占 __FT0_PCT__%；涨停股换手板占比 __HUANSHOU_PCT__%、一字板 __ONEWORD__ 只。
<span class="hl">真实承接集中在「PCB 大票 + 地产权重 + 新华传媒」三处，其余票的封板质量一般</span>，
一旦 __FT0__（__FT0_LB__ 板）断板，高位情绪会立刻失去锚。</li>
</ul>
</div>

<div class="card">
<h2>十、明日观察要点与风险</h2>
<ul>
<li><b>量能是唯一裁判：</b>今日成交 __AMT__ 亿为本轮最低。明日若不能回到 1.5 万亿以上，反抽大概率在 2–3 日内结束；反之若放量站上 1.7 万亿，可视为二次启动。</li>
<li><b>跌停家数：</b>今日 __DT__ 家。若明日续降至 5 家以内，说明风险出清完成；若回到 20 家以上，则为反抽失败信号。</li>
<li><b>龙头锚：</b>__FT0__（__FT0_LB__ 板）封单 __FT0_V__ 亿但换手仅 __FT0_AMT__ 亿。此票开板对全市场情绪影响最大，需要盯盘；其次看 __LB_TOP2__（__LB_TOP2_LB__ 板）能否接棒。</li>
<li><b>PCB 反抽的持续性：</b>今日元件涨停 7 只均为「昨日大跌 + AI 服务器叙事」的品种。若明日出现「高开低走/放量不封」，说明这是解套盘出货而非新资金进场。</li>
<li><b>地产链的成色：</b>地产涨停属消息面驱动（政策/重组预期），无业绩弹性，历史上持续性弱于产业逻辑；追高风险显著高于 PCB 方向。</li>
<li><b>数据口径：</b>统计为沪深两市（不含北交所）。东财涨停池 __REL_DIFF_NOTE__；
同花顺跌停池明细接口当日不可用（`ths_dt` 为 None），跌停家数一律取汇总字段 `limit_down_count`，故 <b>跌停名单来自东财池</b>；
成交额、封单、换手率取东财字段；两市成交额为沪市 + 深市全市场口径；行业/概念涨跌幅与主力净流入取自 westock。
封板时间双源（东财 `fbt` vs 同花顺时间戳）分钟级一致率 100%（__TOT__ 只可比样本）。</li>
</ul>
<div class="warn" style="margin-top:14px">
<b>风险提示：</b>本报告为盘后数据复盘与资金行为分析，所有结论基于公开行情数据的统计推断，不构成任何投资建议。
涨停板交易具有高波动、高换手、隔夜风险大的特征；缩量反抽的持续性显著弱于放量反攻，历史统计规律不保证未来重复。
</div>
</div>

<div class="note" style="text-align:center;color:#9ca3af;margin-top:24px">
生成时间：__GEN_AT__｜数据源：同花顺 / 东方财富 / 腾讯财经 / westock｜本报告由脚本自动生成
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
  grid:{left:76,right:56,top:16,bottom:24},
  xAxis:Object.assign({type:'value',axisLabel:{formatter:'{value}%'}},AX),
  yAxis:Object.assign({type:'category',data:__JS_IX_NAME__,axisLabel:{color:'#6b7280',interval:0}},AX),
  series:[{type:'bar',data:__JS_IX_PCT__,barWidth:14,
    itemStyle:{color:function(p){return p.value>=0?C_RED:C_GRN}},
    label:{show:true,position:'right',color:'#6b7280',fontSize:11,formatter:'{c}%'}}]
});

mk('c_amt',{
  tooltip:{trigger:'axis',valueFormatter:function(v){return v+'%'}},
  grid:{left:76,right:56,top:16,bottom:24},
  xAxis:Object.assign({type:'value',axisLabel:{formatter:'{value}%'}},AX),
  yAxis:Object.assign({type:'category',data:__JS_AMT_NAME__,axisLabel:{color:'#6b7280',interval:0}},AX),
  series:[{type:'bar',data:__JS_AMT_YOY__,barWidth:14,itemStyle:{color:'#12805c'},
    label:{show:true,position:'left',color:'#12805c',fontSize:11,formatter:'{c}%'}}]
});

mk('c_lad',{
  tooltip:{trigger:'axis'},legend:{top:3,left:'center',textStyle:{color:'#6b7280'}},
  grid:{left:46,right:20,top:52,bottom:28},
  xAxis:Object.assign({type:'category',data:__JS_LAD_NAME__},AX),
  yAxis:Object.assign({type:'value'},AX),
  series:[
    {name:'__D1__',type:'bar',data:__JS_LAD1__,itemStyle:{color:'#cbd5e1'},barWidth:18},
    {name:'__D0__',type:'bar',data:__JS_LAD0__,itemStyle:{color:C_RED},barWidth:18,
     label:{show:true,position:'top',color:'#9ca3af',fontSize:11}}
  ]
});

mk('c_theme',{
  tooltip:{trigger:'axis'},
  grid:{left:150,right:70,top:16,bottom:24},
  xAxis:Object.assign({type:'value'},AX),
  yAxis:Object.assign({type:'category',data:__JS_TH_NAME__,axisLabel:{color:'#6b7280',interval:0}},AX),
  series:[{type:'bar',data:__JS_TH_N__,itemStyle:{color:C_BLU},barWidth:14,
    label:{show:true,position:'right',color:'#374151',fontWeight:600,formatter:'{c} 家'}}]
});

mk('c_hy',{
  tooltip:{trigger:'axis'},legend:{top:3,left:'center',textStyle:{color:'#6b7280'}},
  grid:{left:100,right:56,top:52,bottom:24},
  xAxis:Object.assign({type:'value'},AX),
  yAxis:Object.assign({type:'category',data:__JS_HY_NAME__,axisLabel:{color:'#6b7280',interval:0}},AX),
  series:[
    {name:'__D1__',type:'bar',data:__JS_HY_Y__,itemStyle:{color:'#cbd5e1'},barWidth:11},
    {name:'__D0__',type:'bar',data:__JS_HY_T__,itemStyle:{color:C_RED},barWidth:11}
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

mk('c_rel',{
  tooltip:{trigger:'axis',valueFormatter:function(v){return v+'%'}},
  grid:{left:96,right:56,top:16,bottom:28},
  xAxis:Object.assign({type:'value',axisLabel:{formatter:'{value}%'}},AX),
  yAxis:Object.assign({type:'category',data:__JS_REL_NAME__,axisLabel:{color:'#6b7280',fontSize:10,interval:0}},AX),
  series:[{type:'bar',data:__JS_REL_PCT__,barWidth:12,
    itemStyle:{color:function(p){return p.data>=0?C_RED:C_GRN}},
    label:{show:true,position:'right',fontSize:10,color:'#9ca3af',
      formatter:function(p){return p.value.toFixed(1)+'%'}}}]
});

mk('c_ts',{
  tooltip:{trigger:'axis'},legend:{top:3,left:'center',textStyle:{color:'#6b7280'}},
  grid:{left:50,right:20,top:52,bottom:28},
  xAxis:Object.assign({type:'category',data:__JS_TS_NAME__},AX),
  yAxis:Object.assign({type:'value'},AX),
  series:[
    {name:'__D1__',type:'bar',data:__JS_TS_Y__,itemStyle:{color:'#cbd5e1'},barWidth:24},
    {name:'__D0__',type:'bar',data:__JS_TS_T__,itemStyle:{color:C_RED},barWidth:24}
  ]
});
</script>
</body>
</html>
"""

# 动态文本占位符（含中文，需在 HTML 内联）
V["__AMT_TOP_LEAD__"] = "成交额第一的 " + esc(amt_top[0]["name"]) + "（" + "{:.2f}".format((amt_top[0]["amount"] or 0) / 1e8) + " 亿）"
V["__DT_HW_YD_N__"] = str(len(DT_YD))
V["__TOT__"] = "56"
# 北交所差额自检说明
em0 = set(x["c"] for x in B["dates"][D0]["em_ZT"]["pool"])
ths0 = set(x["code"] for x in (B["dates"][D0]["ths_zt"].get("info") or []))
diff = sorted(em0 - ths0)
assert all(c.startswith("92") for c in diff), f"北交所差额自检失败: {diff}"
if diff:
    V["__REL_DIFF_NOTE__"] = "东财池 %d 只 vs 同花顺 %d 只，差额 %d 只为北交所（%s），已按沪深口径取 %d 只" % (
        len(em0), len(ths0), len(diff), "/".join(diff), len(ths0))
else:
    V["__REL_DIFF_NOTE__"] = "东财池与同花顺家数一致（%d 只），差额 0" % len(em0)

HTML = HTML_T
for k, v in V.items():
    HTML = HTML.replace(k, v)

fp = os.path.join(REP, f"涨停复盘对比-{D0}.html")
with open(fp, "w", encoding="utf-8") as f:
    f.write(HTML)
left = re.findall(r"__[A-Z_0-9]+__", HTML)
print("saved ->", fp, len(HTML) // 1024, "KB")
print("placeholder residue:", sorted(set(left)))
print("北交所差额自检: em=%d ths=%d diff=%s OK" % (len(em0), len(ths0), diff))
