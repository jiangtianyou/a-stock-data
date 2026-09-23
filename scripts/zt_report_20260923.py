# -*- coding: utf-8 -*-
"""涨停复盘报告 20260923 vs 20260922（缩量退潮 / 高位全断 / 承接力塌陷）

用法：python zt_report_20260923.py 20260923
输入：out/zt_stats_20260923.json、out/zt_review_20260923.json
输出：reports/涨停复盘对比-20260923.html
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
    x["touch"] = x["zt"] + x["zb"]

# ---- 指数 ----
IX_ORDER = [("上证指数", "sh000001"), ("深证成指", "sz399001"), ("创业板指", "sz399006"),
            ("科创50", "sh000688"), ("中小100", "sz399005"), ("沪深300", "sh000300"),
            ("中证500", "sh000905"), ("中证1000", "sh000852"), ("国证2000", "sz399303"),
            ("上证50", "sh000016"), ("北证50", "bj899050")]
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
pct_delta = {k: v["pct"] - PREV_IDX_PCT.get(k, 0) for k, v in ixr.items()}

# 昨日全指数成交额（读上一交易日 review 文件，用于风格量能对比）
B1 = None
_p1 = os.path.join(OUT, f"zt_review_{D1}.json")
if os.path.exists(_p1):
    B1 = json.load(open(_p1, encoding="utf-8"))
idx_prev_amt = {}
if B1:
    for v in B1["indexes"].values():
        if isinstance(v, dict) and v.get("name"):
            idx_prev_amt[v["name"]] = (v.get("amount_wan") or 0) / 10000.0
            if v.get("pct") is not None:
                PREV_IDX_PCT.setdefault(v["name"], v["pct"])


def amt_yoy(nm):
    a0, a1 = ixr.get(nm, {}).get("amt", 0), idx_prev_amt.get(nm, 0)
    return (a0 / a1 - 1) * 100 if a1 else 0.0


# 开盘缺口 与 距当日最高回落（用实时快照 open/high/prev/price，对 index_hist 窗口滑动免疫）
def gap_pct(nm):
    v = idx_now.get(nm)
    return (v["open"] / v["prev"] - 1) * 100 if v and v.get("prev") else 0.0


def draw_pct(nm):
    v = idx_now.get(nm)
    return abs((v["price"] / v["high"] - 1) * 100) if v and v.get("high") else 0.0


# ---- 行业迁移 ----
hy0, hy1 = S["hy0"], S["hy1"]
hy_keys = sorted(set(list(hy0) + list(hy1)),
                 key=lambda k: (-(hy0.get(k, 0) * 2 + hy1.get(k, 0)), -hy0.get(k, 0), -hy1.get(k, 0), k))
hy_tbl = [{"name": k, "t": hy0.get(k, 0), "y": hy1.get(k, 0)} for k in hy_keys[:18]]
N_HY0, N_HY1 = len(hy0), len(hy1)
TOP_HY0 = max(hy0.values()) if hy0 else 0
TOP_HY1 = max(hy1.values()) if hy1 else 0
TOP_HY0_NAME = sorted([k for k, v in hy0.items() if v == TOP_HY0])[0]
TOP_HY1_NAME = sorted([k for k, v in hy1.items() if v == TOP_HY1])[0]

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
neg_low = sum(1 for p in pcts if p <= -5)

# ---- 成交额结构 ----
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
oneword = sum(1 for r in r0 if "一字" in r["limit_up_type"])
huanshou = sum(1 for r in r0 if "换手" in r["limit_up_type"])
oneword1 = sum(1 for r in r1 if "一字" in r["limit_up_type"])
huanshou1 = sum(1 for r in r1 if "换手" in r["limit_up_type"])
fund_top = sorted(r0, key=lambda x: -(x["fund"] or 0))[:3]
fund_top1 = sum((x["fund"] or 0) for x in fund_top) / 1e8
fund_ex = fund_sum - fund_top1
fund_top_name = fund_top[0]["name"]
fund_top_val = (fund_top[0]["fund"] or 0) / 1e8
fund_top_pct = fund_top_val / fund_sum * 100
fund_top_ratio = fund_top_val / ((fund_top[0]["amount"] or 1) / 1e8)

# ---- 「华」字辈（name 维度，不走 reason 关键词）----
hua = sorted([r for r in r0 if "华" in r["name"]], key=lambda x: (-(x["lbc"] or 0), x["code"]))
hua_lb = [r for r in hua if (r["lbc"] or 1) >= 2]
lb_all = sorted([r for r in r0 if (r["lbc"] or 1) >= 2], key=lambda x: (-(x["lbc"] or 0), x["code"]))
hua_lb_pct = len(hua_lb) / len(lb_all) * 100 if lb_all else 0.0
hua1 = [r for r in r1 if "华" in r["name"]]

# ---- 测量仪器/半导体测试集群（本日新增方向）----
INSTR_KW = ["仪器", "测量", "质谱", "网络分析", "VNA", "计量"]
instr = sorted([r for r in r0 if any(k in (r["reason"] or "") for k in INSTR_KW)],
               key=lambda x: -(x["amount"] or 0))

# ---- 炸板池结构（东财 em_ZB）：区分「回封」与「未回封」----
_zbpool = (B["dates"][D0].get("em_ZB") or {}).get("pool") or []


def _is_limit(z):
    """按收盘涨幅判断是否收在涨停（创业板/科创板阈值 19.8%）"""
    thr = 19.8 if (z["c"].startswith("30") or z["c"].startswith("688")) else 9.8
    return (z.get("zdp") or 0) >= thr


zb_pool = sorted([z for z in _zbpool if not _is_limit(z)], key=lambda x: -(x.get("ltsz") or 0))
zb_sealed = sorted([z for z in _zbpool if _is_limit(z)], key=lambda x: -(x.get("ltsz") or 0))
zb_top = zb_pool[:4]
zb_today = [z for z in zb_pool if ((z.get("fbt") or 0) <= 113000)]
_zb_h = len(zb_pool) - len(zb_today)
_zb_early = len([z for z in zb_pool if ((z.get("fbt") or 0) <= 100000)])

# ---- 主线归因（多标签，家数之和 > 总数）----
THEMES = [
    ("AI算力/电子硬件", ["算力", "PCB", "服务器", "光通信", "光模块", "数据中心", "交换机", "液冷",
                         "端侧AI", "存储", "半导体", "消费电子", "芯片", "光刻", "先进封装", "显示",
                         "覆铜板", "HDI", "MiniLED", "AIDC", "MLCC", "离子注入", "铜箔", "LED"]),
    ("测量仪器/半导体测试", ["仪器", "测量", "质谱", "网络分析", "VNA", "计量", "测试", "检测"]),
    ("出版传媒/文化整合", ["出版", "传媒", "图书", "文化", "影视", "数字内容", "短剧", "广告", "营销",
                           "数字教育", "游戏", "数据中心"]),
    ("医药医疗", ["创新药", "医药", "医疗", "中药", "体外诊断", "CRO", "脑机", "细胞", "抗感染",
                  "肿瘤", "口腔", "康复", "阿尔茨海默", "基因", "医疗器械", "精麻", "抗生素",
                  "流感", "合成生物", "腹膜透析", "药材", "脱敏", "过敏"]),
    ("国资/股权变更", ["国资", "央企", "国企", "控制权", "股权转让", "股份转让", "控股", "资产重组",
                       "复牌", "借壳", "入主", "划转", "拟收购", "收购"]),
    ("消费零售/家居", ["零售", "百货", "家居", "家具", "服装", "家纺", "食品", "黄酒", "白酒", "珠宝",
                       "乳品", "纺织", "羽绒", "养殖", "猪", "粮油", "皮鞋", "皮革", "卫浴", "智能马桶",
                       "按摩椅", "大消费", "功能糖", "种业", "玉米", "转基因"]),
    ("化工材料/资源", ["化学", "新材料", "锆", "锶", "玻纤", "聚酯", "薄膜", "染料", "铝", "锂", "钢丝绳",
                       "贵金属", "铜箔", "陶瓷", "钼", "锑", "锡", "稀贵", "危废", "煤炭", "铬", "水泥",
                       "TDI", "SOFC"]),
    ("地产链", ["房地产", "城市更新", "物业", "房产经纪", "旧改", "装修"]),
    ("机器人/智造", ["机器人", "具身", "人形", "3D打印", "精密", "执行器", "智能装备", "智能电控",
                     "电梯", "焊接", "轴承"]),
    ("电力电网/能源", ["电力", "电网", "热电", "电缆", "风电", "光伏", "储能", "输电", "天然气", "LNG",
                       "燃气", "核电", "燃气轮机"]),
    ("低空经济", ["低空", "商业航天", "无人机", "车路云", "卫星"]),
]
theme_cnt = []
for nm, kws in THEMES:
    hit = [r for r in r0 if any(k in (r["reason"] or "") for k in kws)]
    theme_cnt.append({"name": nm, "n": len(hit),
                      "stocks": [r["name"] + "(" + str(r["lbc"] or 1) + "板)" for r in
                                 sorted(hit, key=lambda x: (-(x["lbc"] or 0), -(x["amount"] or 0)))][:8]})
theme_cnt.sort(key=lambda x: (-x["n"], x["name"]))
med_theme = theme_cnt[0]

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
    "<tr><td>{0}板</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td><td>{6:.1f}%</td>"
    "<td>{7}</td><td style='text-align:left;color:#4b5563'>{8}</td></tr>".format(
        r["lbc"], r["code"], esc(r["name"]), (r["fbt"][:5] if r["fbt"] else "—"),
        "{:.2f}亿".format((r["fund"] or 0) / 1e8), "{:.2f}亿".format((r["amount"] or 0) / 1e8),
        (r["turnover"] or 0), esc(r["hybk"]), esc(r["reason"]))
    for r in lb_all)

tbl_hua = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td style='text-align:left;color:#4b5563'>{4}</td></tr>".format(
        esc(r["name"]), r["code"], r["lbc"], esc(r["hybk"]),
        ("是" if any(k in (r["reason"] or "") for k in ["国资", "央企", "国企", "重组", "收购", "控股", "变更", "划转"]) else "—"))
    for r in hua)

tbl_instr = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td>"
    "<td style='text-align:left;color:#4b5563'>{5}</td></tr>".format(
        esc(r["name"]), r["code"], r["lbc"], esc(r["hybk"]),
        "{:.2f}亿".format((r["amount"] or 0) / 1e8), esc(r["reason"]))
    for r in instr)

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

tbl_zb = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td></tr>".format(
        esc(z["n"]), z["c"], esc(z.get("hybk", "")), "{:.0f}亿".format((z.get("ltsz") or 0) / 1e8),
        "{:+.2f}%".format(z.get("zdp") or 0), hhmm(z.get("fbt") or 0))
    for z in zb_top)

tbl_idx = "".join(
    "<tr><td>{0}</td><td class='{1}'>{2:+.2f}%</td><td class='{3}'>{4}</td><td>{5}</td></tr>".format(
        esc(x["name"]), "up" if x["pct"] >= 0 else "down", x["pct"],
        "up" if PREV_IDX_PCT.get(x["name"], 0) >= 0 else "down",
        ("{:+.2f}%".format(PREV_IDX_PCT[x["name"]]) if x["name"] in PREV_IDX_PCT else "—"),
        "{:,.0f}亿".format(x["amt"]))
    for x in ix)

tbl_sty = "".join(
    "<tr><td>{0}</td><td class='hl'>{1}</td><td>{2}</td><td class='{3}'>{4}</td></tr>".format(
        esc(nm), "{:+.2f}".format(ixr.get(nm, {}).get("pct", 0.0)),
        ("{:+.2f}".format(PREV_IDX_PCT[nm]) if nm in PREV_IDX_PCT else "—"),
        "up" if amt_yoy(nm) >= 0 else "down", "{:+.1f}%".format(amt_yoy(nm)))
    for nm, _s in [("科创50", "sh000688"), ("上证50", "sh000016"), ("沪深300", "sh000300"),
                   ("中小100", "sz399005"), ("中证500", "sh000905"), ("创业板指", "sz399006"),
                   ("中证1000", "sh000852"), ("国证2000", "sz399303")])


def fmtv(v):
    return "{:.1f}".format(v) if isinstance(v, float) else str(v)


def fmtd(v):
    return ("{:+.1f}" if isinstance(v, float) else "{:+d}").format(v)


tbl_senti = "".join(
    "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td class='hl'>{3}</td><td class='{4}'>{5}</td></tr>".format(
        lab, fmtv(days[0][k]), fmtv(days[1][k]), fmtv(days[2][k]),
        "down" if days[2][k] - days[1][k] < 0 else "up", fmtd(days[2][k] - days[1][k]))
    for lab, k in [("涨停家数", "zt"), ("炸板家数", "zb"), ("封板率(%)", "seal"), ("跌停家数", "dt"),
                   ("触及涨停家数", "touch")])

perf_top = "、".join("{}{:+.1f}%".format(esc(p["name"]), p["pct"]) for p in top3)
perf_bot = "、".join("{}{:+.1f}%".format(esc(p["name"]), p["pct"]) for p in bot3)

# ================= 占位符 =================
V = {}


def P(k, v):
    V["__" + k + "__"] = str(v)


P("GEN_AT", B["generated_at"])
P("ZT", s0["zt"]); P("ZT_Y", s1["zt"]); P("ZT_D", "{:+d}".format(s0["zt"] - s1["zt"]))
P("ZT_PCT_D", "{:+.1f}".format((s0["zt"] / s1["zt"] - 1) * 100))
P("ZB", s0["zb"]); P("ZB_Y", s1["zb"]); P("ZB_D", "{:+d}".format(s0["zb"] - s1["zb"]))
P("ZB_PCT_D", "{:+.0f}".format((s0["zb"] / s1["zb"] - 1) * 100))
P("DT", s0["dt"]); P("DT_Y", s1["dt"]); P("DT_D", "{:+d}".format(s0["dt"] - s1["dt"]))
P("SEAL", "{:.1f}".format(s0["seal_rate"] * 100))
P("SEAL_Y", "{:.1f}".format(s1["seal_rate"] * 100))
P("SEAL_D", "{:+.1f}".format((s0["seal_rate"] - s1["seal_rate"]) * 100))
P("TOUCH", s0["zt"] + s0["zb"]); P("TOUCH_Y", s1["zt"] + s1["zb"])
P("TOUCH_D", "{:+d}".format((s0["zt"] + s0["zb"]) - (s1["zt"] + s1["zb"])))
P("ZTDT", "{:.1f}".format(s0["zt"] / s0["dt"] if s0["dt"] else 0))
P("ZTDT_Y", "{:.1f}".format(s1["zt"] / s1["dt"] if s1["dt"] else 0))
P("ZTDT_0", ("{:.1f}".format(days[0]["zt"] / days[0]["dt"]) if days[0]["dt"] else "—（跌停0家）"))
P("DT_OPEN", s0["limit_down_count"]["today"]["open_num"])
P("DT_LOCK", "{:.0f}".format(s0["limit_down_count"]["today"]["rate"] * 100))
P("DT_LOCK_Y", "{:.0f}".format(s1["limit_down_count"]["today"]["rate"] * 100))
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
P("KC_GAP", "{:+.2f}".format(gap_pct("科创50")))
P("KC_DRAW", "{:.2f}".format(draw_pct("科创50")))
for _nm, _k in [("上证指数", "SH"), ("深证成指", "SZ"), ("创业板指", "CY"), ("上证50", "SZ50")]:
    P(_k + "_GAP", "{:+.2f}".format(gap_pct(_nm)))
    P(_k + "_DRAW", "{:.2f}".format(draw_pct(_nm)))
    P(_k + "_PCT2", "{:+.2f}".format(ixr.get(_nm, {}).get("pct", 0)))
P("SZ50_AMT_PCT", "{:+.1f}".format(amt_yoy("上证50")))
P("HS300_AMT_PCT", "{:+.1f}".format(amt_yoy("沪深300")))
P("ZZ500_AMT_PCT", "{:+.1f}".format(amt_yoy("中证500")))
P("ZZ1000_AMT_PCT", "{:+.1f}".format(amt_yoy("中证1000")))
P("GZ2000_AMT_PCT", "{:+.1f}".format(amt_yoy("国证2000")))
P("CYB_AMT_PCT", "{:+.1f}".format(amt_yoy("创业板指")))
P("ADV_RATE", "{:.1f}".format(adv_rate)); P("ADV_N", len(adv)); P("ADV_TOT", len(perf))
P("PERF_MEAN", "{:+.2f}".format(mean(pcts))); P("PERF_MED", "{:+.2f}".format(median(pcts)))
P("PERF_MAX", "{:+.2f}".format(max(pcts))); P("PERF_MIN", "{:+.2f}".format(min(pcts)))
P("PERF_MAX_NAME", esc(perf_sorted[0]["name"]))
P("PERF_MIN_NAME", esc(perf_sorted[-1]["name"]))
P("PERF_MIN_LB", perf_sorted[-1]["lbc"])
P("PERF_TOP3", perf_top); P("PERF_BOT3", perf_bot)
P("NEG", neg); P("NEG_PCT", "{:.1f}".format(neg / len(pcts) * 100))
P("NEG_LOW", neg_low)
P("AMT_SUM", "{:.0f}".format(amt_sum)); P("SHARE", "{:.1f}".format(share))
P("AMT_SUM_Y", "{:.0f}".format(amt_sum1)); P("SHARE_Y", "{:.1f}".format(share1))
P("AMT_MED", "{:.2f}".format(amt_med)); P("AMT_MED_Y", "{:.2f}".format(amt_med1))
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
P("FUND_TOP_RATIO", "{:.0f}".format(fund_top_ratio))
P("FUND_TOP_AMT", "{:.2f}".format((fund_top[0]["amount"] or 0) / 1e8))
P("FUND_TOP3_VAL", "{:.1f}".format(fund_top1))
P("FUND_EX", "{:.1f}".format(fund_ex))
P("LB_TOP1", esc(lb_all[0]["name"])); P("LB_TOP1_REASON", esc(lb_all[0]["reason"]))
P("LB_TOP2", esc(lb_all[1]["name"])); P("LB_TOP2_LB", lb_all[1]["lbc"])
P("HUA_N", len(hua)); P("HUA_PCT", "{:.1f}".format(len(hua) / s0["zt"] * 100))
P("HUA_N_Y", len(hua1))
P("HUA_LB_N", len(hua_lb)); P("HUA_LB_PCT", "{:.0f}".format(hua_lb_pct))
P("HUA_LB_RATIO", "{:.0f}".format(len(hua_lb) / len(hua) * 100))
P("HUA_LB_RATIO_Y", "{:.0f}".format(sum(1 for r in hua1 if (r["lbc"] or 1) >= 2) / len(hua1) * 100) if hua1 else "0")
# 「新华系」：名称含"新华"且行业为出版/文化
_xh = [r for r in hua if "新华" in r["name"] and ("出版" in (r["hybk"] or "") or "文化" in (r["reason"] or ""))]
P("XH_N", len(_xh))
P("XH_LIST", "、".join(r["name"] + "（" + str(r["lbc"]) + " 板）" for r in _xh))
P("INSTR_N", len(instr))
P("INSTR_LIST", "、".join(r["name"] for r in instr))
P("ZB_POOL_N", len(_zbpool))
P("ZB_SEALED_N", len(zb_sealed))
P("ZB_SEALED_NAME", esc(zb_sealed[0]["n"]) if zb_sealed else "—")
P("ZB_SEALED_V", "{:.0f}".format((zb_sealed[0]["ltsz"] or 0) / 1e8) if zb_sealed else "0")
P("ZB_AM", len(zb_today)); P("ZB_PM", _zb_h); P("ZB_EARLY", _zb_early)
P("ZB_TOP1", esc(zb_top[0]["n"])); P("ZB_TOP1_V", "{:.0f}".format((zb_top[0]["ltsz"] or 0) / 1e8))
P("ZB_TOP2", esc(zb_top[1]["n"])); P("ZB_TOP2_V", "{:.0f}".format((zb_top[1]["ltsz"] or 0) / 1e8))
P("ZB_TOP3", esc(zb_top[2]["n"])); P("ZB_TOP3_V", "{:.0f}".format((zb_top[2]["ltsz"] or 0) / 1e8))
P("MEDTHEME", esc(med_theme["name"])); P("MEDTHEME_N", med_theme["n"])
P("MEDTHEME_PCT", "{:.1f}".format(med_theme["n"] / s0["zt"] * 100))
P("ADV_S_N", n_s); P("ADV_S_RATE", "{:.1f}".format(r_s)); P("ADV_S_MED", "{:+.2f}".format(m_s))
P("ADV_L_N", n_l); P("ADV_L_RATE", "{:.1f}".format(r_l)); P("ADV_L_MED", "{:+.2f}".format(m_l))
P("ADV_GAP", "{:.2f}".format(m_l - m_s))
P("TH_AI_N", next(t["n"] for t in theme_cnt if t["name"].startswith("AI算力")))
P("TH_INSTR_N", next(t["n"] for t in theme_cnt if t["name"].startswith("测量仪器")))
P("TH_CB_N", next(t["n"] for t in theme_cnt if t["name"].startswith("出版")))
P("ZT_D2", days[0]["zt"]); P("SEAL_D2", "{:.1f}".format(days[0]["seal"]))
P("SHARE_HY0", "{:.1f}".format(TOP_HY0 / s0["zt"] * 100))
P("SHARE_HY1", "{:.1f}".format(TOP_HY1 / s1["zt"] * 100))
P("N_HY0", N_HY0); P("N_HY1", N_HY1)
P("TOP_HY0", esc(TOP_HY0_NAME)); P("TOP_HY1", esc(TOP_HY1_NAME))
P("TOP_HY0_N", TOP_HY0); P("TOP_HY1_N", TOP_HY1)
_amt_top = sorted(r0, key=lambda x: -(x["amount"] or 0))[:3]
P("AMT_TOP1", esc(_amt_top[0]["name"])); P("AMT_TOP1_V", "{:.1f}".format((_amt_top[0]["amount"] or 0) / 1e8))
P("AMT_TOP2", esc(_amt_top[1]["name"])); P("AMT_TOP2_V", "{:.1f}".format((_amt_top[1]["amount"] or 0) / 1e8))
P("AMT_TOP3", esc(_amt_top[2]["name"])); P("AMT_TOP3_V", "{:.1f}".format((_amt_top[2]["amount"] or 0) / 1e8))
for _b in (2, 3, 4, 5, 6):
    P("LAD{}_T".format(_b), lad0.get(_b, 0)); P("LAD{}_Y".format(_b), lad1.get(_b, 0))
P("LAD3P_Y", sum(lad1.get(i, 0) for i in (3, 4, 5, 6)))
P("LAD3P_T", sum(lad0.get(i, 0) for i in (3, 4, 5, 6)))
P("HILB_Y", sum(lad1.get(i, 0) for i in (4, 5, 6)))
# 行业
for nm, key in [("化学制药", "YIYAO"), ("医疗服务", "MEDSVC"), ("医疗器械", "MEDDEV"),
                ("半导体", "BDT"), ("电网设备", "DW"), ("房地产开", "FDCK"),
                ("房地产服", "FDCF"), ("化学制品", "HXP"), ("出版", "CB"),
                ("家居用品", "JJYP"), ("广告营销", "GGYX"), ("元件", "YJ"),
                ("一般零售", "LS"), ("服装家纺", "FZJZ"), ("专用设备", "ZYSB"),
                ("通用设备", "TYSB"), ("消费电子", "XFDZ"), ("计算机设", "JSJSB"),
                ("软件开发", "RJKF"), ("塑料", "SL"), ("环境治理", "HJZL"), ("家电零部", "JD"),
                ("光学光电", "GXGD"), ("IT服务Ⅱ", "IT2")]:
    P("HY_" + key, hy0.get(nm, 0)); P("HY_" + key + "_Y", hy1.get(nm, 0))
P("IX_SZ50_PCT", "{:+.2f}".format(ixr.get("上证50", {}).get("pct", 0)))
P("IX_GZ2000_PCT", "{:+.2f}".format(ixr.get("国证2000", {}).get("pct", 0)))
P("IX_ZZ1000_PCT", "{:+.2f}".format(ixr.get("中证1000", {}).get("pct", 0)))
P("IX_CYB_PCT", "{:+.2f}".format(ixr.get("创业板指", {}).get("pct", 0)))
P("IX_ZZ500_PCT", "{:+.2f}".format(ixr.get("中证500", {}).get("pct", 0)))
P("IX_HS300_PCT", "{:+.2f}".format(ixr.get("沪深300", {}).get("pct", 0)))
P("IX_ZXX100_PCT", "{:+.2f}".format(ixr.get("中小100", {}).get("pct", 0)))
P("IX_BJ50_PCT", "{:+.2f}".format(ixr.get("北证50", {}).get("pct", 0)))
P("ZTDT_Y_DISP", "—" if not s1["dt"] else "{:.1f}".format(s1["zt"] / s1["dt"]))
P("TS_EARLY", ts0.get("竞价/秒板", 0) + ts0.get("开盘半小时", 0))
P("TS_EARLY_PCT", "{:.0f}".format((ts0.get("竞价/秒板", 0) + ts0.get("开盘半小时", 0)) / s0["zt"] * 100))
P("TS_EARLY_Y", ts1.get("竞价/秒板", 0) + ts1.get("开盘半小时", 0))
P("TS_EARLY_Y_PCT", "{:.0f}".format((ts1.get("竞价/秒板", 0) + ts1.get("开盘半小时", 0)) / s1["zt"] * 100))
P("TS_PM0", ts0.get("午后盘中", 0)); P("TS_PM1", ts1.get("午后盘中", 0))
P("TS_PM_PCT", "{:.0f}".format(ts0.get("午后盘中", 0) / s0["zt"] * 100))
P("TS_PM_Y_PCT", "{:.0f}".format(ts1.get("午后盘中", 0) / s1["zt"] * 100))
P("TBL_SENTI", tbl_senti); P("TBL_LAD", tbl_lad); P("TBL_LIANBAN", tbl_lianban)
P("TBL_HY", tbl_hy); P("TBL_TS", tbl_ts); P("TBL_THEME", tbl_theme); P("TBL_IDX", tbl_idx)
P("TBL_HUA", tbl_hua); P("TBL_ZB", tbl_zb); P("TBL_INSTR", tbl_instr); P("TBL_STY", tbl_sty)
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
<title>涨停复盘 · 2026-09-23（对比 9-22）</title>
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
.lead{background:#fff;border:1px solid #e6e8eb;border-left:5px solid #12805c;border-radius:10px;padding:18px 22px;margin-bottom:18px}
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
<h1>涨停复盘 · 2026-09-23（周三）</h1>
<div class="sub">对比基准：2026-09-22（周二）｜口径：沪深两市（不含北交所）｜数据源：同花顺涨停池 + 东方财富涨停/炸板池 + 行情快照</div>

<div class="lead">
<p class="hl">一句话结论：缩量退潮日——量价齐跌 + 高位股全军覆没 + 承接力塌陷。</p>
<p>两市成交额 __AMT__ 亿（__AMT_D__ 亿、__AMT_PCT__%），除北证50（__IX_BJ50_PCT__%）外<span class="hl">全部指数收绿</span>；
涨停家数 __ZT_Y__→__ZT__（__ZT_D__）、炸板 __ZB_Y__→__ZB__（__ZB_D__）、封板率 __SEAL_Y__%→__SEAL__%（__SEAL_D__pct，本轮回调以来最低）、
跌停 __DT_Y__→__DT__（__DT_D__，封死率 __DT_LOCK__%）。
<span class="hl">昨日 6 板华瓷股份（今 +6.95%）、5 板内蒙新华（今 +2.94%）、4 板南华生物（今 +5.37%）全部断板</span>，最高板由 __MAXB_Y__ 板降到 __MAXB__ 板。</p>
<p><span class="hl">但这不是"参与度"的退潮，而是"承接力"的退潮</span>：触及涨停家数 __TOUCH_Y__→__TOUCH__（__TOUCH_D__，几乎持平），
封住率却从 __SEAL_Y__% 掉到 __SEAL__%；炸板池 __ZB_POOL_N__ 只中 <span class="hl">__ZB_SEALED_N__ 只回封</span>，且 __ZB_AM__ 只集中在上午被砸。
昨涨停股今日晋级率 __ADV_RATE__%，其中昨日首板组仅 __ADV_S_RATE__%（中位 __ADV_S_MED__%），翻绿 __NEG__ 只（__NEG_PCT__%）。</p>
<p>资金端：昨日"增量是配置盘"的最强证据是权重放量（科创50 成交 +27.2%、上证50 +17.8%），
今日这两个方向<span class="hl">缩得最狠（科创50 __KC_AMT_PCT__%、上证50 __SZ50_AMT_PCT__%）</span>，
而小微盘缩幅最小（国证2000 __GZ2000_AMT_PCT__%、中证1000 __ZZ1000_AMT_PCT__%）——昨天的结论今天被反向验证。
涨停行业里出现唯一的新集群<span class="hl">「通用设备」0→__HY_TYSB__ 家</span>，其中 __INSTR_N__ 只是电子测量/科学仪器（__INSTR_LIST__），
共性叙事是"光通信测试 / 半导体检测"。「华」字辈由 __HUA_N_Y__ 只衰减到 __HUA_N__ 只。</p>
</div>

<div class="kpis">
  <div class="kpi"><div class="lbl">涨停家数</div><div class="val down">__ZT__</div>
    <div class="dt mut">昨日 __ZT_Y__ <span class="down">__ZT_D__</span></div></div>
  <div class="kpi"><div class="lbl">封板率</div><div class="val down">__SEAL__%</div>
    <div class="dt mut">昨日 __SEAL_Y__% <span class="down">__SEAL_D__pct</span></div></div>
  <div class="kpi"><div class="lbl">跌停家数</div><div class="val down">__DT__</div>
    <div class="dt mut">昨日 __DT_Y__ <span class="down">__DT_D__</span>（封死率 __DT_LOCK__%）</div></div>
  <div class="kpi"><div class="lbl">两市成交额</div><div class="val down">__AMT__亿</div>
    <div class="dt mut">昨日 __AMT_Y__亿 <span class="down">__AMT_D__亿</span></div></div>
  <div class="kpi"><div class="lbl">昨涨停今日晋级率</div><div class="val down">__ADV_RATE__%</div>
    <div class="dt mut">__ADV_N__/__ADV_TOT__ 只再涨停</div></div>
  <div class="kpi"><div class="lbl">最高连板</div><div class="val down">__MAXB__ 板</div>
    <div class="dt mut">昨日 __MAXB_Y__ 板（昨高板全断）</div></div>
</div>

<div class="card">
<h2>一、市场情绪温度计：封板率与跌停数同时反向，退潮确认</h2>
<table>
<tr><th>指标</th><th>__L_D2__（周一）</th><th>__L_D1__（周二）</th><th>__L_D0__（周三）</th><th>__L_D0__ 环比</th></tr>
__TBL_SENTI__
<tr><td>涨停/跌停比</td><td>__ZTDT_0__</td><td>__ZTDT_Y_DISP__</td><td class="hl">__ZTDT__</td><td class="down">快速回落</td></tr>
</table>
<div class="note" style="margin-top:10px">
三日序列走完一个完整的「扩张（__L_D1__ 前的 __L_D2__ 涨停 __ZT_D2__ 家）→ 分歧（__L_D1__ __ZT_Y__ 家）→ 退潮（__L_D0__ __ZT__ 家）」。
按本流程的判读规则，<span class="hl">「封板率与跌停家数同时反向」是退潮拐点的确认信号</span>——
今日封板率 __SEAL_Y__%→__SEAL__%（__SEAL_D__pct）、跌停 __DT_Y__→__DT__ 家，两项同时恶化，退潮方向已确认。<br>
但要区分退潮的"形态"：跌停 __DT__ 家（__L_D0__）远低于 9/15 的 27 家，<span class="hl">本轮不是靠跌停潮完成的，而是靠"封不住"完成的</span>——
涨停/跌停比仍为 __ZTDT__（__ZT__ ÷ __DT__），说明是<b>缩量阴跌型退潮</b>，而非恐慌式杀跌。
这种形态下指数跌幅有限（最大跌幅的中小100 也只有 __IX_ZXX100_PCT__%），但对打板资金极不友好。
</div>
<div id="c_senti" class="chart" style="margin-top:16px"></div>
</div>

<div class="card">
<h2>二、指数与量能：缩量 17.4%，昨天进得最猛的权重今天缩得最狠</h2>
<div class="two">
<div>
<table>
<tr><th>指数</th><th>今日</th><th>昨日</th><th>成交额</th></tr>
__TBL_IDX__
</table>
<div class="note" style="margin-top:10px">
两市成交额 __AMT__ 亿（环比 __AMT_D__ 亿、__AMT_PCT__%），<span class="hl">跌破 9/18 的 20771 亿，回到 9/17 的水平</span>。
更值得看的是<b>缩量的结构</b>——按各指数成交额环比排序：
</div>
<table style="margin-top:8px">
<tr><th>方向</th><th>今日涨跌%</th><th>昨日涨跌%</th><th>成交额环比</th></tr>
__TBL_STY__
</table>
<div class="note" style="margin-top:8px">
<span class="hl">昨日进场最猛的两个方向（科创50 成交 +27.2%、上证50 +17.8%），今日缩幅最大（__KC_AMT_PCT__%、__SZ50_AMT_PCT__%）</span>；
而缩幅最小的恰好是昨日最平的小微盘（国证2000 __GZ2000_AMT_PCT__%、中证1000 __ZZ1000_AMT_PCT__%）。
<b>这说明昨天的放量不是"新增配置盘入场"，而是场内资金的一次短线搬家</b>——搬进权重、第二天就搬走。
今日风格因此完全反转：昨日权重涨、小微盘平；今日全线跌，但小微盘最抗跌（国证2000 __IX_GZ2000_PCT__%、中证1000 __IX_ZZ1000_PCT__%）
而大盘领跌（中小100 __IX_ZXX100_PCT__%、沪深300 __IX_HS300_PCT__%、创业板指 __IX_CYB_PCT__%）。
唯一的例外是<b>北证50 __IX_BJ50_PCT__%</b>，成交额环比 +0.3%，是全市场唯一没有缩量的方向。
</div>
</div>
<div><div id="c_idx" class="chart-sm"></div>
<div class="note" style="margin-top:8px">
上证平开（__SH_GAP__%）收 __SH_PCT2__%（距当日最高 __SH_DRAW__%），深成高开 __SZ_GAP__% 收 __SZ_PCT2__%（距最高 __SZ_DRAW__%），
创业板指高开 __CY_GAP__% 收 __CY_PCT2__%、<span class="hl">开盘价即全天最高价</span>；科创50 高开 __KC_GAP__% 收 __KC_PCT__%（距最高 __KC_DRAW__%）。
</div>
</div>
</div>
<h3>炸板池结构：__ZB_POOL_N__ 只炸板、__ZB_SEALED_N__ 只回封，市值最大的都是科技硬件</h3>
<table style="margin-top:8px">
<tr><th>炸板池个股（流通市值 TOP4）</th><th>代码</th><th>行业</th><th>流通市值</th><th>收盘涨幅</th><th>首触时间</th></tr>
__TBL_ZB__
</table>
<div class="note" style="margin-top:8px">
__ZB_POOL_N__ 只炸板股中仅 __ZB_SEALED_N__ 只回封（昨日为 18 只中 1 只回封）；
未回封阵营里流通市值最大的是 __ZB_TOP1__（__ZB_TOP1_V__ 亿）、__ZB_TOP2__（__ZB_TOP2_V__ 亿）、__ZB_TOP3__（__ZB_TOP3_V__ 亿），
全部是中大盘科技硬件。<span class="hl">"大票冲高回落 + 小票封不住"同时出现，是本日最重要的资金面特征</span>，
也是指数跌幅不大、但打板体验极差的直接原因。
</div>
</div>

<div class="card">
<h2>三、连板梯队：首板不动、中位塌陷、高位全断</h2>
<div class="two">
<div><div id="c_lad" class="chart-sm"></div></div>
<div>
<table>
<tr><th>梯队</th><th>__L_D1__</th><th>__L_D0__</th><th>变化</th></tr>
__TBL_LAD__
<tr><td>合计</td><td>__ZT_Y__</td><td class="hl">__ZT__</td><td class="down">__ZT_D__</td></tr>
</table>
<div class="note" style="margin-top:10px">
<span class="hl">三项对比最有信息量</span>：① 首板 __SB_Y__→__SB__ 家，几乎不动；
② 2 板 __LAD2_Y__→__LAD2_T__ 家，<b>塌陷</b>；③ 3 板以上由 __LAD3_Y__+__LAD4_Y__+__LAD5_Y__+__LAD6_Y__ 共 __LAD3P_Y__ 家增到 __LAD3_T__+__LAD4_T__ 共 __LAD3P_T__ 家，<b>反而变厚</b>。<br>
梯队形状从昨日的"金字塔（首板 __SB_Y__ 独大 + 2 板 __LAD2_Y__ 的厚腰）"变成今日的"<span class="hl">漏斗（首板 __SB__ 独大 + 2 板只剩 __LAD2_T__ 的断崖 + 3-4 板 __LAD3_T__+__LAD4_T__ 家）</span>"。<br>
含金量解读：昨日 2 板 __LAD2_Y__ 家是"中位补涨梯队"，今日只有 __LAD3_T__ 家晋级到 3 板、其余全部回落；
而昨日 4/5/6 板的高位股（__HILB_Y__ 家）<span class="hl">一只都没有续板</span>。资金在做的事是：
<b>放弃 2 板试错、集中到 3 板以上的"已确认标的"抱团</b>——赚钱效应进一步变窄。
</div>
</div>
</div>
<h3>今日连板股全名单（2 板及以上，__LB__ 只）</h3>
<table>
<tr><th>高度</th><th>代码</th><th>名称</th><th>首封</th><th>封单</th><th>成交额</th><th>换手</th><th>行业</th><th>涨停原因</th></tr>
__TBL_LIANBAN__
</table>
</div>

<div class="card">
<h2>四、主线归因：唯一新方向是"测量仪器"，「华」字辈明显衰减</h2>
<div id="c_theme" class="chart"></div>
<table style="margin-top:14px">
<tr><th>主线</th><th>涨停家数</th><th>代表个股</th></tr>
__TBL_THEME__
</table>
<div class="note" style="margin-top:12px">
多标签口径下命中最多的是 AI算力/电子硬件 __TH_AI_N__ 家，但该口径宽（含 PCB/铜箔/消费电子/显示等），不构成单一主线。
今日唯一有<b>共同产业叙事</b>的新集群是「测量仪器/半导体测试」：<span class="hl">__INSTR_N__ 只涨停股同属电子测量与科学仪器</span>，
叙事高度一致（光通信测试 / 半导体检测 / 实验仪器）。这与 AI 算力链的下游延伸有关：光模块与先进封装的测试环节需要 VNA、质谱等设备。
</div>
<h3>测量仪器/半导体测试集群（__INSTR_N__ 只）</h3>
<table>
<tr><th>名称</th><th>代码</th><th>连板</th><th>行业</th><th>成交额</th><th>涨停原因</th></tr>
__TBL_INSTR__
</table>
<div class="note" style="margin-top:8px">
全部为首板、且成交额普遍很小（除个别），属于典型的<b>冷门方向单日脉冲</b>，没有业绩弹性支撑（多为"测试/检测"概念延伸）。
注意：东财行业把它们归入「通用设备」，若只看行业标签会误判为"通用设备行情"。
</div>
<h3>「华」字辈：由 __HUA_N_Y__ 只衰减到 __HUA_N__ 只，≥2 板占比 __HUA_LB_RATIO_Y__%→__HUA_LB_RATIO__%</h3>
<table>
<tr><th>名称</th><th>代码</th><th>连板</th><th>行业</th><th>reason 含国资/重组关键词</th></tr>
__TBL_HUA__
</table>
<div class="note" style="margin-top:10px">
昨日 __HUA_N_Y__ 只含"华"字标的<span class="hl">100% 位于 2 板及以上</span>，今日 __HUA_N__ 只中只剩 __HUA_LB_N__ 只（__HUA_LB_RATIO__%）在 2 板以上，
占全市场 2 板以上梯队（__LB__ 只）的 __HUA_LB_PCT__%。<b>衰减方向明确了：名称博弈的接力资金在减少。</b><br>
其中的"新华系"由 3 家减到 __XH_N__ 家（__XH_LIST__），出版行业 __HY_CB_Y__→__HY_CB__ 家。
需要特别标注 __FUND_TOP_NAME__：3 板、封单 __FUND_TOP_VAL__ 亿，而当日成交额仅 __FUND_TOP_AMT__ 亿（封单/成交 ≈ __FUND_TOP_RATIO__ 倍），
<span class="hl">属于极致的缩量锁仓结构——一旦开口，缺少换手承接，波动会被放大</span>。<br>
注：reason_type 为多标签，同一只股票可归入多条主线，故各主线家数之和大于涨停总数（__ZT__）。
</div>
</div>

<div class="card">
<h2>五、行业迁移：家居/医药/广告同步清零，钱只去了"通用设备"</h2>
<div id="c_hy" class="chart" style="height:410px"></div>
<table style="margin-top:14px">
<tr><th>行业</th><th>__L_D1__</th><th>__L_D0__</th><th>增减</th><th>读数</th></tr>
__TBL_HY__
</table>
<div class="note" style="margin-top:12px">
<b>流出端（昨日方向集体退潮）：</b>家居用品 __HY_JJYP_Y__→__HY_JJYP__ 家（昨日最大集群直接归零）、
广告营销 __HY_GGYX_Y__→__HY_GGYX__ 家、化学制药 __HY_YIYAO_Y__→__HY_YIYAO__ 家、医疗服务 __HY_MEDSVC_Y__→__HY_MEDSVC__ 家、
塑料 __HY_SL_Y__→__HY_SL__ 家、环境治理 __HY_HJZL_Y__→__HY_HJZL__ 家、计算机设备 __HY_JSJSB_Y__→__HY_JSJSB__ 家、
软件开发 __HY_RJKF_Y__→__HY_RJKF__ 家、家电零部件 __HY_JD_Y__→__HY_JD__ 家。<span class="hl">昨日 9 个方向今日全部清零</span>。<br>
<b>流入端：</b>通用设备 __HY_TYSB_Y__→__HY_TYSB__ 家（唯一显著增量）、半导体 __HY_BDT_Y__→__HY_BDT__ 家、消费电子 __HY_XFDZ_Y__→__HY_XFDZ__ 家，
其余 1 家以下的分散方向（水泥 / 电池 / 玻璃玻纤 / 工业金属 / 化学原料 / 照明设备 / 光伏设备 / 军工电子 / 农产品加工 / 种植业 / 汽车服务 / 专业服务）
合计 12 家，全部是单只脉冲，<b>不构成方向</b>。<br>
<span class="hl">行业集中度：今日 __ZT__ 只涨停分散在 __N_HY0__ 个东财行业，最大集群「__TOP_HY0__」__TOP_HY0_N__ 只、仅占 __SHARE_HY0__%</span>
（昨日 __ZT_Y__ 只分散在 __N_HY1__ 个行业，最大集群「__TOP_HY1__」__TOP_HY1_N__ 只占 __SHARE_HY1__%）。
集中度微弱回升，但没有任何方向超过 12% —— <b>这是"没有主线"的量化定义</b>。
</div>
</div>

<div class="card">
<h2>六、昨日涨停股今日表现：晋级率 __ADV_RATE__%，首板组只剩 __ADV_S_RATE__%</h2>
<div class="kpis" style="grid-template-columns:repeat(auto-fit,minmax(140px,1fr))">
  <div class="kpi"><div class="lbl">晋级率</div><div class="val down">__ADV_RATE__%</div><div class="dt mut">__ADV_N__/__ADV_TOT__</div></div>
  <div class="kpi"><div class="lbl">平均涨幅</div><div class="val down">__PERF_MEAN__%</div><div class="dt mut">中位 __PERF_MED__%</div></div>
  <div class="kpi"><div class="lbl">翻绿比例</div><div class="val down">__NEG_PCT__%</div><div class="dt mut">__NEG__ 只（跌超5% 共 __NEG_LOW__ 只）</div></div>
  <div class="kpi"><div class="lbl">最强</div><div class="val up">__PERF_MAX__%</div><div class="dt mut">__PERF_MAX_NAME__</div></div>
  <div class="kpi"><div class="lbl">最弱</div><div class="val down">__PERF_MIN__%</div><div class="dt mut">__PERF_MIN_NAME__</div></div>
</div>
<div class="note" style="margin-top:14px">
昨日 __ADV_TOT__ 只涨停股今日平均 __PERF_MEAN__%、中位 __PERF_MED__%，晋级 __ADV_N__ 只（__ADV_RATE__%），翻绿 __NEG__ 只（__NEG_PCT__%）、跌超 5% 的 __NEG_LOW__ 只。
分层看：<b>昨日首板 n=__ADV_S_N__ 晋级率 __ADV_S_RATE__%、中位 __ADV_S_MED__%；昨日连板 n=__ADV_L_N__ 晋级率 __ADV_L_RATE__%、中位 __ADV_L_MED__%</b>。<br>
<span class="hl">这是连续第二个交易日「首板组中位为负、连板组中位为正」，且两组差距扩大到 __ADV_GAP__ 个百分点（本轮最大）</span>——
昨日买扩散（首板）的资金今天几乎全部亏损，买确认（连板）的资金仍在赚钱。
<b>"买扩散亏钱、买确认赚钱"这一结构连续两日成立，是本轮由扩张转向退潮最稳定的量化证据。</b><br>
最弱三只为 __PERF_BOT3__，全部来自昨日的连板梯队（医药 / 传媒 / 物流方向的补涨标的）；
最强三只 __PERF_TOP3__ 同样来自昨日 2 板及以上的连板梯队（房地产服务 / 房地产开发 / 电视广播方向）。
</div>
<div id="c_perf" class="chart" style="height:700px;margin-top:8px"></div>
</div>

<div class="card">
<h2>七、封板节奏与成交结构：节奏后移、封单集中度继续上升</h2>
<div class="two">
<div><div id="c_ts" class="chart-sm"></div></div>
<div>
<table>
<tr><th>封板时段</th><th>__L_D1__</th><th>__L_D0__</th></tr>
__TBL_TS__
</table>
<div class="note" style="margin-top:10px">
早盘封板（竞价 + 开盘半小时）占比从 __TS_EARLY_Y_PCT__%（__TS_EARLY_Y__/__ZT_Y__）降到 __TS_EARLY_PCT__%（__TS_EARLY__/__ZT__），
午后封板 __TS_PM1__→__TS_PM0__ 家（占今日 __TS_PM_PCT__%，为近期最高）。
<span class="hl">节奏后移与炸板结构完全对应：__ZB_POOL_N__ 只炸板股中 __ZB_AM__ 只的首次触板时间在上午、仅 __ZB_PM__ 只在下午，其中 __ZB_EARLY__ 只集中在 09:30–10:00 的半小时内</span>，
说明早盘一致性冲高失败后，资金在午后重新逐波承接。
<b>与昨日"节奏大幅前移（61%）"恰好相反</b>——昨日的早盘抢一致性，今天被证明是分歧的起点而非趋势的起点。
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
涨停股合计成交 __AMT_SUM__ 亿（昨 __AMT_SUM_Y__ 亿），占两市 __SHARE__%（昨 __SHARE_Y__%），仍低于 3%~8% 常规区间；
用单只中位成交额二次校验：__AMT_MED__ 亿（昨 __AMT_MED_Y__ 亿）→ <b>字段源无误，比值低是家数与总量同步收缩的结果</b>。<br>
封单合计 __FUND_SUM__ 亿（昨 __FUND_SUM_Y__ 亿），<span class="hl">__FUND_TOP_NAME__ 一只占 __FUND_TOP_VAL__ 亿、即全部封单的 __FUND_TOP_PCT__%</span>；
但封单中位数 __FUND_MED__ 亿<b>反而高于</b>昨日 __FUND_MED_Y__ 亿——剔除头部极端值后，普通涨停股的封单其实是变厚的。
换手板 __HUANSHOU__ 只占 __HUANSHOU_PCT__%、一字板仅 __ONEWORD__ 只，说明封板主要靠盘中承接而非一字锁仓，
这也解释了为什么在承接力下降时封板率会跌得这么快。
</div>
</div>

<div class="card">
<h2>八、资金运动的三个结论</h2>
<ul>
<li><b>① 总量：缩量 __AMT_PCT__%，且是"权重先撤"。</b>两市成交额 __AMT__ 亿（__AMT_D__ 亿、__AMT_PCT__%），
其中科创50 __KC_AMT_PCT__%、上证50 __SZ50_AMT_PCT__%、沪深300 __HS300_AMT_PCT__%，而国证2000 仅 __GZ2000_AMT_PCT__%、中证1000 __ZZ1000_AMT_PCT__%。
<span class="hl">昨日放量最猛的权重今天缩量最猛，证明昨日的增量是场内短线搬家而非新增配置资金</span>——这是对昨日报告核心结论的直接证伪。</li>
<li><b>② 方向：昨日 9 个方向同步清零，钱只去了"测量仪器"。</b>
家居用品 __HY_JJYP_Y__→__HY_JJYP__、广告营销 __HY_GGYX_Y__→__HY_GGYX__、化学制药 __HY_YIYAO_Y__→__HY_YIYAO__、医疗服务 __HY_MEDSVC_Y__→__HY_MEDSVC__、
塑料 __HY_SL_Y__→__HY_SL__、环境治理 __HY_HJZL_Y__→__HY_HJZL__、计算机设备 __HY_JSJSB_Y__→__HY_JSJSB__、软件开发 __HY_RJKF_Y__→__HY_RJKF__、家电零部件 __HY_JD_Y__→__HY_JD__；
接棒的只有电子测量/科学仪器 __INSTR_N__ 只（冷门、小市值、无业绩弹性）与半导体 __HY_BDT_Y__→__HY_BDT__。
<span class="hl">资金没有找到新的产业主线，只是在做"从热到冷"的低位游击</span>。</li>
<li><b>③ 深度：参与度未退，承接力退了。</b>触及涨停家数 __TOUCH_Y__→__TOUCH__（__TOUCH_D__）说明<b>资金意愿仍在</b>；
但封板率 __SEAL_D__pct、炸板 __ZB__ 只中 __ZB_SEALED_N__ 只回封、跌停 __DT__ 只（封死率 __DT_LOCK__%）说明<b>承接力显著下降</b>。
结构上钱在"3 板以上"打桩（3 板以上 __LAD3P_Y__→__LAD3P_T__ 家）、在"2 板"被弃（__LAD2_Y__→__LAD2_T__）。
<span class="hl">这种"意愿在、承接弱"的组合，通常对应指数的缩量整理与个股的快速轮动，而非趋势性下跌</span>，
但打板胜率会持续被压制。</li>
</ul>
</div>

<div class="card">
<h2>九、明日观察要点与风险</h2>
<ul>
<li><b>退潮确认/证伪的三个阈值：</b>今日封板率 __SEAL__% 已跌破 9/17 收敛日的 70.1%，是本轮新低。若明日<b>封板率继续低于 70%、跌停家数超过 10 家、量能低于 1.8 万亿</b>，则退潮延续；
若<b>封板率回到 75% 以上且涨停家数回到 70 家以上</b>，今日只是缩量洗盘（形态上会更像 9/17 的"收敛去伪"而非 9/15 的"地量杀跌"）。</li>
<li><b>高度标杆只剩 __MAXB__ 板：</b>__LB_TOP1__（__MAXB__ 板，__LB_TOP1_REASON__）与 __LB_TOP2__（__LB_TOP2_LB__ 板）是当前最高高度。
本轮前两个高度标杆（华瓷股份 6 板、内蒙新华 5 板）均在次日断板，<span class="hl">4 板能否续板直接决定"抱团高度"逻辑是否还成立</span>。
第二梯队是 3 板的 __LAD3_T__ 只，其中 5 只属「华」字辈——同一名称族群的集中度仍然偏高。</li>
<li><b>「华」字辈衰减：</b>__HUA_N_Y__→__HUA_N__ 只，≥2 板占比 __HUA_LB_RATIO_Y__%→__HUA_LB_RATIO__%。
尤其 __FUND_TOP_NAME__（3 板，封单 __FUND_TOP_VAL__ 亿 vs 当日成交 __FUND_TOP_AMT__ 亿，比值约 __FUND_TOP_RATIO__ 倍）属极端锁仓，
<span class="hl">一旦开口缺少换手承接，波动会明显放大，并直接冲击「华」字辈整体情绪</span>。</li>
<li><b>测量仪器方向能否成线：</b>__INSTR_N__ 只同日涨停（__INSTR_LIST__）是今日唯一的产业叙事延展（光通信/先进封装测试环节）。
但它们全部为首板、市值小、叙事偏"测试/检测"概念延伸，<b>需观察次日是否有第二日跟风与梯队形成</b>；若无，则归类为单日脉冲。</li>
<li><b>大票能否止住回落：</b>炸板池流通市值 TOP3（__ZB_TOP1__ __ZB_TOP1_V__ 亿、__ZB_TOP2__ __ZB_TOP2_V__ 亿、__ZB_TOP3__ __ZB_TOP3_V__ 亿）
与昨日同源，均为中大盘科技硬件。<span class="hl">科技硬件冲高回落已连续两个交易日</span>，若明日继续，则"指数缩量整理 + 打板胜率下滑"会延续。</li>
<li><b>北证50 的背离：</b>__IX_BJ50_PCT__% 是全市场唯一上涨且唯一不缩量（+0.3%）的方向，与沪深两市全线缩量形成明显背离。
北交所标的的流动性风险显著高于沪深，<b>不建议把该指数作为情绪回暖的信号使用</b>。</li>
<li><b>数据口径：</b>统计为沪深两市；同花顺与东财涨停池家数一致（__ZT__ = __ZT__，<span class="hl">差额 0，今日涨停池内无北交所标的</span>）。
跌停家数两源不一致：同花顺汇总 __DT__ 家、东财 em_DT tc= 13 家，<b>差额 1 只无法归因</b>（东财跌停池明细返回空、同花顺跌停池接口当日 404），
报告采用同花顺汇总口径 __DT__ 家并声明此差异。封板时间双源分钟级一致率 100%（可比样本 __ZT__ 只）。
涨停股成交额、封单、换手率、连板数均取东财字段；两市成交额为沪市 + 深市全市场口径。</li>
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
  grid:{left:138,right:70,top:16,bottom:24},
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
# 未出现在涨停名单里的北交所标的（用于口径说明）
_em_codes = set(x["c"] for x in (B["dates"][D0]["em_ZT"] or {}).get("pool") or [])
_ths_codes = set(x["code"] for x in ((B["dates"][D0]["ths_zt"] or {}).get("info") or []))
_bj = sorted(_em_codes - _ths_codes)
assert all(c.startswith("92") for c in _bj), f"北交所差额断言失败: _bj={_bj}"
print("ths pool:", len(_ths_codes), "em tc:", _em_tc, "bj_diff:", _bj)
# 跌停池差额（明细池为空时的声明）
_em_dt = (B["dates"][D0].get("em_DT") or {}).get("tc") or 0
P("DT_EM_T", _em_dt)
P("DT_EM_DIFF", _em_dt - s0["dt"])
# 昨日高板（用于 lead 文案）
_y_top = max(lad1) if lad1 else 0
PERF_MIN_LB_CTX = "最高板" if not _y_top else ("昨 %d 板" % _y_top)
P("PERF_MIN_LB_CTX", PERF_MIN_LB_CTX)

HTML = HTML_T
for k, v in V.items():
    HTML = HTML.replace(k, v)

fp = os.path.join(REP, f"涨停复盘对比-{D0}.html")
with open(fp, "w", encoding="utf-8") as f:
    f.write(HTML)
left = re.findall(r"__[A-Z_0-9]+__", HTML)
print("saved ->", fp, len(HTML) // 1024, "KB")
print("placeholder residue:", sorted(set(left)))
