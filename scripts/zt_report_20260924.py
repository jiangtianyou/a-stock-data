# -*- coding: utf-8 -*-
"""涨停复盘报告 20260924 vs 20260923（缩量普跌 / 收缩式锁仓 / 福建海峡两岸主线）

用法：python zt_report_20260924.py 20260924
输入：out/zt_stats_20260924.json、out/zt_review_20260924.json
输出：reports/涨停复盘对比-20260924.html
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

# ---- 海峡两岸/福建区域题材（本日唯一板块级主线）----
STR_KW = ["海峡两岸", "福建", "平潭", "厦门", "漳州"]
strait = sorted([r for r in r0 if any(k in (r["reason"] or "") for k in STR_KW)],
                key=lambda x: (-(x["lbc"] or 0), -(x["fund"] or 0)))
strait_n = len(strait)
strait_pct = strait_n / s0["zt"] * 100
strait_fund = sum((r["fund"] or 0) for r in strait) / 1e8

# ---- 机器人/零部件集群 ----
ROBOT_KW = ["机器人", "具身", "人形", "减速器", "轴承", "丝杠", "执行器"]
robot = sorted([r for r in r0 if any(k in (r["reason"] or "") for k in ROBOT_KW)],
               key=lambda x: (-(x["lbc"] or 0), -(x["fund"] or 0)))
robot_n = len(robot)
robot_fund = sum((r["fund"] or 0) for r in robot) / 1e8

# ---- 测量仪器/半导体测试集群（延续方向）----
INSTR_KW = ["仪器", "测量", "质谱", "网络分析", "VNA", "计量"]
instr = sorted([r for r in r0 if any(k in (r["reason"] or "") for k in INSTR_KW)],
               key=lambda x: -(x["amount"] or 0))
# 通用设备标签下的三个不同叙事（成分几乎全换，仅东方中科留存）
tysb0 = sorted([r for r in r0 if (r["hybk"] or "") == "通用设备"], key=lambda x: -(x["fund"] or 0))
tysb1 = sorted([r for r in r1 if (r["hybk"] or "") == "通用设备"], key=lambda x: -(x["fund"] or 0))
_tysb0c = set(r["code"] for r in tysb0)
_tysb1c = set(r["code"] for r in tysb1)
tysb_keep = [r for r in tysb0 if r["code"] in _tysb1c]

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
    ("海峡两岸/福建", ["海峡两岸", "福建", "平潭", "厦门", "漳州"]),
    ("机器人/精密零部件", ["机器人", "具身", "人形", "减速器", "轴承", "丝杠", "执行器", "3D打印"]),
    ("AI算力/电子硬件", ["算力", "PCB", "服务器", "光通信", "光模块", "数据中心", "交换机", "液冷",
                         "端侧AI", "存储", "半导体", "消费电子", "芯片", "光刻", "先进封装", "显示",
                         "覆铜板", "HDI", "MiniLED", "AIDC", "MLCC", "离子注入", "铜箔", "LED",
                         "测试", "仪器", "测量"]),
    ("测量仪器/半导体测试", ["仪器", "测量", "质谱", "网络分析", "VNA", "计量", "测试"]),
    ("出版传媒/文化整合", ["出版", "传媒", "图书", "文化", "影视", "数字内容", "短剧", "广告", "营销",
                           "数字教育", "游戏", "数据中心"]),
    ("医药医疗", ["创新药", "医药", "医疗", "中药", "体外诊断", "CRO", "脑机", "细胞", "抗感染",
                  "肿瘤", "口腔", "康复", "阿尔茨海默", "基因", "医疗器械", "精麻", "抗生素",
                  "流感", "合成生物", "腹膜透析", "药材", "脱敏", "过敏"]),
    ("国资/股权变更", ["国资", "央企", "国企", "控制权", "股权转让", "股份转让", "控股", "资产重组",
                       "复牌", "借壳", "入主", "划转", "拟收购", "收购"]),
    ("消费零售/家居", ["零售", "百货", "家居", "家具", "服装", "家纺", "食品", "黄酒", "白酒", "珠宝",
                       "乳品", "纺织", "羽绒", "养殖", "猪", "粮油", "皮鞋", "皮革", "卫浴", "智能马桶",
                       "按摩椅", "大消费", "功能糖", "种业", "玉米", "转基因", "夹克"]),
    ("化工材料/资源", ["化学", "新材料", "锆", "锶", "玻纤", "聚酯", "薄膜", "染料", "铝", "锂", "钢丝绳",
                       "贵金属", "铜箔", "陶瓷", "钼", "锑", "锡", "稀贵", "危废", "煤炭", "铬", "水泥",
                       "焦炭", "磷化铟", "TDI", "SOFC"]),
    ("地产链", ["房地产", "城市更新", "物业", "房产经纪", "旧改", "装修"]),
    ("电力电网/能源", ["电力", "电网", "热电", "电缆", "风电", "光伏", "储能", "输电", "天然气", "LNG",
                       "燃气", "核电", "燃气轮机", "变压器"]),
    ("低空经济", ["低空", "商业航天", "无人机", "车路云", "卫星", "电磁"]),
    ("基建/交运", ["基建", "基础建设", "路桥", "港口", "物流", "铁路", "扣件", "航运"]),
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

tbl_strait = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td>"
    "<td>{5}</td><td style='text-align:left;color:#4b5563'>{6}</td></tr>".format(
        esc(r["name"]), r["code"], (r["lbc"] if (r["lbc"] or 0) >= 2 else "首板"), esc(r["hybk"]),
        "{:.2f}亿".format((r["fund"] or 0) / 1e8), "{:.2f}亿".format((r["amount"] or 0) / 1e8),
        esc(r["reason"]))
    for r in strait)

tbl_robot = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td>"
    "<td>{5}</td><td style='text-align:left;color:#4b5563'>{6}</td></tr>".format(
        esc(r["name"]), r["code"], (r["lbc"] if (r["lbc"] or 0) >= 2 else "首板"), esc(r["hybk"]),
        "{:.2f}亿".format((r["fund"] or 0) / 1e8), "{:.2f}亿".format((r["amount"] or 0) / 1e8),
        esc(r["reason"]))
    for r in robot)

tbl_tysb = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td></tr>".format(
        esc(r["name"]), r["code"], ({1: "首板"}.get(r["lbc"], str(r["lbc"]) + " 板")),
        "{:.2f}亿".format((r["fund"] or 0) / 1e8), esc(r["reason"]))
    for r in tysb0)

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
P("TOUCH_PCT_D", "{:+.0f}".format(((s0["zt"] + s0["zb"]) / (s1["zt"] + s1["zb"]) - 1) * 100))
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
fund_top_y = sorted(r1, key=lambda x: -(x["fund"] or 0))[:1]
P("FUND_TOP_Y_NAME", esc(fund_top_y[0]["name"]) if fund_top_y else "—")
P("FUND_TOP_Y_VAL", "{:.1f}".format((fund_top_y[0]["fund"] or 0) / 1e8) if fund_top_y else "0")
P("FUND_TOP_Y_AMT", "{:.2f}".format((fund_top_y[0]["amount"] or 0) / 1e8) if fund_top_y else "0")
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
P("STR_N", strait_n); P("STR_PCT", "{:.0f}".format(strait_pct))
P("STR_FUND", "{:.2f}".format(strait_fund))
P("STR_LB_N", sum(1 for r in strait if (r["lbc"] or 0) >= 2))
P("STR_LIST", "、".join(r["name"] for r in strait))
P("ROBOT_N", robot_n); P("ROBOT_FUND", "{:.2f}".format(robot_fund))
P("ROBOT_LB_N", sum(1 for r in robot if (r["lbc"] or 0) >= 2))
P("ROBOT_LIST", "、".join(r["name"] for r in robot))
P("TYSB_KEEP_N", len(tysb_keep))
P("TYSB_KEEP", "、".join(r["name"] for r in tysb_keep))
P("TYSB_ROT", "{:.0f}".format(100 - len(tysb_keep) / len(tysb0) * 100) if tysb0 else "0")
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
P("TH_STR_N", next(t["n"] for t in theme_cnt if t["name"].startswith("海峡两岸")))
P("TH_ROBOT_N", next(t["n"] for t in theme_cnt if t["name"].startswith("机器人")))
P("TH_GZ_N", next(t["n"] for t in theme_cnt if t["name"].startswith("国资")))
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
                ("光学光电", "GXGD"), ("IT服务Ⅱ", "IT2"), ("水泥", "SN"), ("军工电子", "JG"),
                ("林业Ⅱ", "LY"), ("汽车零部", "QC"), ("电视广播", "DSGB"), ("其他家电", "QTJD"),
                ("纺织制造", "FZZZ"), ("光伏设备", "GFSB"), ("工程机械", "GCJX"),
                ("农化制品", "NH"), ("焦炭Ⅱ", "JT"), ("养殖业", "YZY")]:
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
P("TBL_STRAIT", tbl_strait); P("TBL_ROBOT", tbl_robot); P("TBL_TYSB", tbl_tysb)
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
<title>涨停复盘 · 2026-09-24（对比 9-23）</title>
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
<h1>涨停复盘 · 2026-09-24（周四）</h1>
<div class="sub">对比基准：2026-09-23（周三）｜口径：沪深两市（不含北交所）｜数据源：同花顺涨停池 + 东方财富涨停/炸板池 + 行情快照</div>

<div class="lead">
<p class="hl">一句话结论：缩量普跌中的"收缩式锁仓"——指数全线中阴、量能再缩 __AMT_PCT__%，但涨停家数持平、封板率由 __SEAL_Y__% 回到 __SEAL__%，资金把战线收缩到极少数低位小盘题材（福建/海峡两岸 + 机器人零部件）。</p>
<p>指数端是<b>低开低走、无抵抗下跌</b>：两市成交额 __AMT__ 亿（__AMT_D__ 亿、__AMT_PCT__%），连续第二日缩量并跌破 9/17 的 18231 亿水平；
全部指数收绿且跌幅较昨日（-0.4%~-0.6%）明显放大——上证 __SH_PCT2__%、深成 __SZ_PCT2__%、创业板 __CY_PCT2__%、科创50 __KC_PCT__%、北证50 __IX_BJ50_PCT__%。
所有指数<b>清一色低开</b>（缺口 __SH_GAP__%~__KC_GAP__%），收盘距当日最高回落 __SH_DRAW__%~__CY_DRAW__%，<span class="hl">开盘即接近全天最高、全天单边下行</span>（昨日为"高开低走"有诱多，今日连诱多都没有）。</p>
<p>打板端却相反：涨停 __ZT_Y__→__ZT__（持平）、炸板 __ZB_Y__→__ZB__（__ZB_PCT_D__%，腰斩）、封板率 __SEAL_Y__%→__SEAL__%（__SEAL_D__pct）、跌停 __DT_Y__→__DT__（封死率 __DT_LOCK__%，昨 __DT_LOCK_Y__%）。
<span class="hl">但"触及涨停家数"由 __TOUCH_Y__ 降到 __TOUCH__（__TOUCH_D__、__TOUCH_PCT_D__%）——愿意去冲板的力量明显减少，而冲上去的却更容易封住</span>。
这不是"资金回流"，而是<b>参与收缩 + 失败率下降</b>的组合。</p>
<p>结构与资金：今日按"叙事同源度"只归得出两条集群——<span class="hl">「福建/海峡两岸」__STR_N__ 只</span>（占全部涨停 __STR_PCT__%，横跨港口物流、工程机械、林业、水泥、电力、智慧城市、AI医疗）
与<span class="hl">「机器人/精密零部件」__ROBOT_N__ 只</span>（轴承、减速器、丝杠、具身智能）；
退潮端是昨日的中大盘科技硬件与地产链——元件 __HY_YJ_Y__→__HY_YJ__、消费电子 __HY_XFDZ_Y__→__HY_XFDZ__、医疗器械 __HY_MEDDEV_Y__→__HY_MEDDEV__、房地产服 __HY_FDCF_Y__→__HY_FDCF__ 全部清零。
成交额环比上<span class="hl">上证50 是唯一放量方向（__SZ50_AMT_PCT__%）且最抗跌（__IX_SZ50_PCT__%），中证1000 / 国证2000 缩幅最大（__ZZ1000_AMT_PCT__% / __GZ2000_AMT_PCT__%）</span>——
资金从题材小盘撤出、回到权重防御，与昨日"权重缩得最狠"完全反转。</p>
<p>昨涨停股今日晋级率 __ADV_RATE__%（昨 19.4%），分层：昨日首板组 __ADV_S_RATE__%（中位 __ADV_S_MED__%）、昨日连板组 __ADV_L_RATE__%（中位 __ADV_L_MED__%）；
最弱三只 __PERF_BOT3__ 全部来自昨天 3 板的高位股，<b>"中位梯队"是本日最大的失血点</b>。</p>
</div>

<div class="kpis">
  <div class="kpi"><div class="lbl">涨停家数</div><div class="val mut">__ZT__</div>
    <div class="dt mut">昨日 __ZT_Y__ <span class="mut">__ZT_D__（持平）</span></div></div>
  <div class="kpi"><div class="lbl">封板率</div><div class="val up">__SEAL__%</div>
    <div class="dt mut">昨日 __SEAL_Y__% <span class="up">__SEAL_D__pct</span></div></div>
  <div class="kpi"><div class="lbl">跌停家数</div><div class="val down">__DT__</div>
    <div class="dt mut">昨日 __DT_Y__ <span class="down">__DT_D__</span>（封死率 __DT_LOCK__%）</div></div>
  <div class="kpi"><div class="lbl">两市成交额</div><div class="val down">__AMT__亿</div>
    <div class="dt mut">昨日 __AMT_Y__亿 <span class="down">__AMT_D__亿</span></div></div>
  <div class="kpi"><div class="lbl">昨涨停今日晋级率</div><div class="val up">__ADV_RATE__%</div>
    <div class="dt mut">__ADV_N__/__ADV_TOT__ 只再涨停（昨 19.4%）</div></div>
  <div class="kpi"><div class="lbl">最高连板</div><div class="val up">__MAXB__ 板</div>
    <div class="dt mut">昨日 __MAXB_Y__ 板（__LB_TOP1__ 5 天 5 板）</div></div>
</div>

<div class="card">
<h2>一、市场情绪温度计：封板率与跌停数"同向改善"，但参与度没有回来</h2>
<table>
<tr><th>指标</th><th>__L_D2__（周二）</th><th>__L_D1__（周三）</th><th>__L_D0__（周四）</th><th>__L_D0__ 环比</th></tr>
__TBL_SENTI__
<tr><td>涨停/跌停比</td><td>__ZTDT_0__</td><td>__ZTDT_Y_DISP__</td><td class="hl">__ZTDT__</td><td class="up">回升</td></tr>
</table>
<div class="note" style="margin-top:10px">
三日序列是「分歧（__L_D2__ 涨停 __ZT_D2__ 家）→ 退潮（__L_D1__ __ZT_Y__ 家、封板率 __SEAL_D2__%→__SEAL_Y__%）→ 收缩锁仓（__L_D0__ __ZT__ 家、封板率回到 __SEAL__%）」。<br>
按本流程的判读规则，<span class="hl">「封板率与跌停家数同时反向」既是退潮确认信号，也是退潮暂停信号</span>——今日两项同时改善（封板率 __SEAL_D__pct、跌停 -2 家、跌停封死率 __DT_LOCK_Y__%→__DT_LOCK__%），
说明 9/23 那种"承接力塌陷"没有延续。<br>
但必须加一条否决条件：<span class="hl">参与度完全没有回来</span>。触及涨停家数由 __TOUCH_Y__ 降到 __TOUCH__（__TOUCH_D__、__TOUCH_PCT_D__%），是 9/18（触及 102 家）以来的最低值。
<b>所以今日的正确读法不是"资金回流"，而是"参与收缩 + 失败率下降"</b>：愿意冲板的钱少了，但冲上去的大部分能封住——
本报告将其定义为<b>收缩式锁仓</b>。这种形态对次日不利，因为它靠的是"减少出手"而不是"增加承接"。<br>
另一项佐证：涨停/跌停比回升到 __ZTDT__（__ZT__ ÷ __DT__），绝对水平仍远低于 9/21 的 50.5，<b>个股层面的风险释放尚未结束</b>。
</div>
<div id="c_senti" class="chart" style="margin-top:16px"></div>
</div>

<div class="card">
<h2>二、指数与量能：全线低开低走，量能再缩 __AMT_PCT__%，权重成唯一放量方向</h2>
<div class="two">
<div>
<table>
<tr><th>指数</th><th>今日</th><th>昨日</th><th>成交额</th></tr>
__TBL_IDX__
</table>
<div class="note" style="margin-top:10px">
两市成交额 __AMT__ 亿（环比 __AMT_D__ 亿、__AMT_PCT__%），<span class="hl">连续第二日缩量，跌破 9/17 的 18231 亿、回到 9/16 附近水平</span>。
更值得看的是<b>缩量的结构</b>——按各指数成交额环比排序：
</div>
<table style="margin-top:8px">
<tr><th>方向</th><th>今日涨跌%</th><th>昨日涨跌%</th><th>成交额环比</th></tr>
__TBL_STY__
</table>
<div class="note" style="margin-top:8px">
<span class="hl">上证50 是唯一成交额放量的方向（__SZ50_AMT_PCT__%）且最抗跌（__IX_SZ50_PCT__%）</span>；
沪深300（__HS300_AMT_PCT__%）、中证500（__ZZ500_AMT_PCT__%）基本持平；缩幅最大的是中证1000 __ZZ1000_AMT_PCT__%、国证2000 __GZ2000_AMT_PCT__% 与北证50 —— 都是小盘/题材属性。<br>
<b>这与昨日形成精确的镜像</b>：9/23 是"权重缩得最狠、小微盘缩幅最小"（权重先撤），今日反过来是"权重放量、小微盘缩得最狠"。
两日连起来看，资金路径是：<span class="hl">9/23 撤权重 → 9/24 撤题材小盘</span>，即<b>成长中盘（科创50 __KC_AMT_PCT__%、创业板指 __CYB_AMT_PCT__%）被两头抽走</b>，
而权重（上证50）成了唯一的避风港。今日风格因此是"大盘价值抗跌、小盘题材补跌"。
</div>
</div>
<div><div id="c_idx" class="chart-sm"></div>
<div class="note" style="margin-top:8px">
上证低开 __SH_GAP__% 收 __SH_PCT2__%（距当日最高 __SH_DRAW__%），深成低开 __SZ_GAP__% 收 __SZ_PCT2__%（距最高 __SZ_DRAW__%），
创业板指低开 __CY_GAP__% 收 __CY_PCT2__%（距最高 __CY_DRAW__%，为全部指数最大）；<b>科创50 低开 __KC_GAP__% 收 __KC_PCT__%</b>。
<span class="hl">全部指数低开且收盘都在全天最高点下方 1.1%~2.5%，全天没有任何一次有效反抽</span>——与昨日"高开低走"相比，今日缺少的第一个环节就是"高开"。
</div>
</div>
</div>
<h3>炸板池结构：__ZB_POOL_N__ 只炸板、__ZB_SEALED_N__ 只回封，中大盘科技硬件已不在池内</h3>
<table style="margin-top:8px">
<tr><th>炸板池个股（流通市值 TOP4）</th><th>代码</th><th>行业</th><th>流通市值</th><th>收盘涨幅</th><th>首触时间</th></tr>
__TBL_ZB__
</table>
<div class="note" style="margin-top:8px">
__ZB_POOL_N__ 只炸板股中 __ZB_SEALED_N__ 只回封（__ZB_SEALED_NAME__，收盘收于涨停价）。
未回封阵营里流通市值最大的是 __ZB_TOP1__（__ZB_TOP1_V__ 亿）、__ZB_TOP2__（__ZB_TOP2_V__ 亿）、__ZB_TOP3__（__ZB_TOP3_V__ 亿）——
<b>与前两日"炸板池塞满中大盘科技硬件"完全不同</b>：昨日炸板池 26 只里流通市值最大的包括先导基电（445 亿）、万科Ａ（381 亿）、
天山股份（280 亿）、科华数据（215 亿）、超声电子（162 亿），科技硬件与地产链各占一半；
今日 9 只未回封票中流通市值过百亿的只剩 <span class="hl">先导基电（__ZB_TOP1_V__ 亿）、__ZB_TOP2__（__ZB_TOP2_V__ 亿）、__ZB_TOP3__（__ZB_TOP3_V__ 亿）</span>，
其余 6 只全部在 50 亿以下。<b>炸板池的市值结构从"中大盘为主"变成"小票为主"，这才是炸板数从 26 降到 10 的真实原因</b>。
<span class="hl">这说明在指数连续下跌后，中大盘科技硬件已经"不再尝试冲板"</span>——炸板数从 26 降到 10，主因是<b>冲板总量减少</b>而非承接变强。
这也是"封板率回升不等于情绪修复"的直接证据。
</div>
</div>

<div class="card">
<h2>三、连板梯队：2 板由 3 只暴增到 8 只，3 板由 7 只塌成 1 只，"腰部"被整体换血</h2>
<div class="two">
<div><div id="c_lad" class="chart-sm"></div></div>
<div>
<table>
<tr><th>梯队</th><th>__L_D1__</th><th>__L_D0__</th><th>变化</th></tr>
__TBL_LAD__
<tr><td>合计</td><td>__ZT_Y__</td><td class="hl">__ZT__</td><td class="mut">__ZT_D__</td></tr>
</table>
<div class="note" style="margin-top:10px">
<span class="hl">最鲜明的两处变化</span>：① 首板 __SB_Y__→__SB__ 家（几乎不动）；
② <b>2 板由 __LAD2_Y__ 只暴增到 __LAD2_T__ 只</b>，同时 <b>3 板由 __LAD3_Y__ 只塌成 __LAD3_T__ 只</b>。<br>
这说明昨日那批"3 板中位梯队"（__LAD3_Y__ 只）今天几乎全部断板（最弱三只 __PERF_BOT3__ 都出自这里），
而资金把接力对象换成了昨日首板里晋级的 8 只新 2 板。<b>这是"中位梯队被整体换血"，不是高度打开。</b><br>
高度端：最高板由 __MAXB_Y__ 升到 __MAXB__（__LB_TOP1__，5 天 5 板），4 板由 __LAD4_Y__ 增到 __LAD4_T__ 只。
3 板以上合计 __LAD3P_Y__→__LAD3P_T__ 家，<b>总量反而减少</b>——所以"高度提升"只是单点现象（一只 5 板 + 三只 4 板），梯队整体是在"变矮变宽"。
</div>
</div>
</div>
<h3>今日连板股全名单（2 板及以上，__LB__ 只）</h3>
<table>
<tr><th>高度</th><th>代码</th><th>名称</th><th>首封</th><th>封单</th><th>成交额</th><th>换手</th><th>行业</th><th>涨停原因</th></tr>
__TBL_LIANBAN__
</table>
<div class="note" style="margin-top:8px">
8 只新 2 板里，<b>福建水泥（水泥）、康强电子（半导体封装材料）、集泰股份（液冷硅油）、上工申贝（机器人缝制）、东方中科（网络分析仪）、
金辰股份（半导体装备）、雪龙集团（新能源风扇）、华茂股份（纺织+矿业整合）</b>——行业极度分散，
唯一共同点是全部来自昨日首板且今日早盘封板（除福建水泥 14:24）。
<span class="hl">它们的价值在于揭示"接力资金的口味"：低价、小市值、有单点叙事，而不是产业链主线。</span>
</div>
</div>

<div class="card">
<h2>四、主线归因：「福建/海峡两岸」__STR_N__ 只叙事最同源，「机器人/精密零部件」__ROBOT_N__ 只有产业逻辑，国资 __TH_GZ_N__ 家只是横切标签</h2>
<div id="c_theme" class="chart"></div>
<table style="margin-top:14px">
<tr><th>主线</th><th>涨停家数</th><th>代表个股</th></tr>
__TBL_THEME__
</table>
<div class="note" style="margin-top:12px">
多标签口径下的排序（按命中家数）：国资/股权变更 __TH_GZ_N__ 家 &gt; AI算力/电子硬件与机器人/精密零部件各 __TH_AI_N__ / __TH_ROBOT_N__ 家 &gt; 海峡两岸/福建 __TH_STR_N__ 家。
<b>但家数排序在这里是无效的</b>：国资/股权变更是横切标签（今天几乎每只涨停都带国企改革/收购/重组关键词）、AI算力口径过宽且成分碎片化，
两者都不构成"同一驱动"。<span class="hl">按"叙事同源度"看，今日只有两条具备集群属性</span>：<br>
① <b>福建/海峡两岸（__TH_STR_N__ 家）</b>——这是近两周以来第一条同时满足"家数 ≥ 8、叙事同源、有连板梯队"的板块级主线，
但它与产业景气无关，是纯粹的<b>区域政策/事件驱动题材</b>；
② <b>机器人/精密零部件（__TH_ROBOT_N__ 家）</b>——唯一有真实产业叙事的方向（人形机器人量产预期下的轴承、减速器、丝杠）。
</div>
<h3>福建/海峡两岸集群（__STR_N__ 只，占今日涨停 __STR_PCT__%，合计封单 __STR_FUND__ 亿）</h3>
<table>
<tr><th>名称</th><th>代码</th><th>连板</th><th>东财行业</th><th>封单</th><th>成交额</th><th>涨停原因</th></tr>
__TBL_STRAIT__
</table>
<div class="note" style="margin-top:8px">
共同特征非常一致：<b>全部是福建本地股（厦门 / 漳州 / 平潭 / 福州），多带国资或"资产重组"关键词，小市值、低价、无业绩弹性</b>。
行业横跨港口物流（厦门港务）、工程机械（厦工股份）、林业（福建金森、平潭发展）、水泥（福建水泥）、
绿色电力（漳州发展）、智慧城市（海峡创新）、AI医疗（合富中国）、纺织服装（七匹狼）、AI营销（新华都）——
<span class="hl">唯一的共同点就是"地域"，这正是典型的题材真空期抱团特征</span>。
解读要点：地域题材的持续性取决于政策/事件催化能否落地，<b>在没有新增信息的情况下，第二天的溢价往往依赖首日封单厚度</b>；
本集群封单合计 __STR_FUND__ 亿，其中平潭发展一只占 3.57 亿（接近集群的四成），<b>分布极不均衡</b>，需警惕"单只锁仓、其余松散"的结构。
另可留意：集群里出现 3 只"福建国资"（福建水泥 / 漳州发展 / 福建金森）与 2 只"平潭系"（海峡创新 / 平潭发展），
说明资金在区域内部也是按"国资资产/对台平台"两个子标签分层，而不是无差别扫货。
</div>
<h3>机器人/精密零部件集群（__ROBOT_N__ 只，合计封单 __ROBOT_FUND__ 亿）</h3>
<table>
<tr><th>名称</th><th>代码</th><th>连板</th><th>东财行业</th><th>封单</th><th>成交额</th><th>涨停原因</th></tr>
__TBL_ROBOT__
</table>
<div class="note" style="margin-top:8px">
口径说明：本集群按 reason 关键词（机器人 / 具身 / 人形 / 轴承 / 减速器 / 丝杠）命中 __ROBOT_N__ 家，
其中<span class="hl">吉鑫科技（风电轴承）、七匹狼（男装 + 投资机器人）属关键词碰撞</span>，剔除后实际机器人零部件标的约 9 只——
<br>① <b>轴承</b>：洛轴股份（航空 + 机器人 + 风电轴承）、襄阳轴承（机器人 + 汽车轴承）、大业股份（胎圈钢丝）；
② <b>减速器 / 传动</b>：宁波东力、中马传动、长华集团；③ <b>本体 / 集成</b>：上工申贝（机器人缝制）、奥佳华（具身智能按摩椅）。
<br>__ROBOT_N__ 只中只有 __ROBOT_LB_N__ 只是连板（奥佳华 4 板、东方中科 / 上工申贝 2 板），其余全为首板，
且<span class="hl">除奥佳华（4 板，但主业是按摩椅 + 具身智能，并非轴承/减速器叙事）外，没有一只站上 3 板</span>——
轴承与减速器属于人形机器人产业链中"价值量低但弹性大"的环节，
这条线有产业逻辑支撑，缺点是<b>缺少同叙事的龙头</b>：全部中小市值、无一只带动板块成交放大（集群封单合计仅 __ROBOT_FUND__ 亿）。
</div>
<h3>「华」字辈：__HUA_N_Y__ 只 → __HUA_N__ 只，占比 __HUA_PCT__%，≥2 板比例 __HUA_LB_RATIO_Y__%→__HUA_LB_RATIO__%</h3>
<table>
<tr><th>名称</th><th>代码</th><th>连板</th><th>行业</th><th>reason 含国资/重组关键词</th></tr>
__TBL_HUA__
</table>
<div class="note" style="margin-top:10px">
数量几乎持平（__HUA_N_Y__→__HUA_N__ 只），但<span class="hl">内部结构在持续"去高度化"：≥2 板比例由 __HUA_LB_RATIO_Y__% 降到 __HUA_LB_RATIO__%</span>，
占全市场 2 板以上梯队（__LB__ 只）的 __HUA_LB_PCT__%。<br>
不过其中「新华系」反而强化：__XH_N__ 家（__XH_LIST__），出版行业 __HY_CB_Y__→__HY_CB__ 家，
其中 <span class="hl">__FUND_TOP_NAME__ 4 板、封单 __FUND_TOP_VAL__ 亿，而当日成交额仅 __FUND_TOP_AMT__ 亿（封单/成交 ≈ __FUND_TOP_RATIO__ 倍）</span>，
是今日最极致的缩量锁仓结构：<b>好处是抛压极小、坏处是一旦开口没有换手承接，回撤会被放大</b>。
更要注意<b>封单已经连续两日集中在同一只票</b>：昨日封单第一同样是 __FUND_TOP_Y_NAME__（__FUND_TOP_Y_VAL__ 亿），今日 __FUND_TOP_VAL__ 亿——
<span class="hl">这说明资金没有扩散、只是在这一只上继续加码，整条「华」字辈的高度则在往下走（≥2 板比例 __HUA_LB_RATIO_Y__%→__HUA_LB_RATIO__%）</span>。<br>
注：reason_type 为多标签，同一只股票可归入多条主线，故各主线家数之和大于涨停总数（__ZT__）。
</div>
</div>

<div class="card">
<h2>五、行业迁移：科技硬件与地产链同时清零，钱只去了"福建系"与"机器人零部件"</h2>
<div id="c_hy" class="chart" style="height:410px"></div>
<table style="margin-top:14px">
<tr><th>行业</th><th>__L_D1__</th><th>__L_D0__</th><th>增减</th><th>读数</th></tr>
__TBL_HY__
</table>
<div class="note" style="margin-top:12px">
<b>流出端（昨日的科技硬件与地产链同步退潮）：</b>元件 __HY_YJ_Y__→__HY_YJ__ 家、消费电子 __HY_XFDZ_Y__→__HY_XFDZ__ 家、
医疗器械 __HY_MEDDEV_Y__→__HY_MEDDEV__ 家、房地产服 __HY_FDCF_Y__→__HY_FDCF__ 家，<span class="hl">四个方向同时清零</span>；
半导体 __HY_BDT_Y__→__HY_BDT__ 家、专用设备 __HY_ZYSB_Y__→__HY_ZYSB__ 家同步减半。
其中元件的依顿电子（昨涨停今 -6.18%）与消费电子的安洁科技（-5.84%）、胜利精密（-5.41%）是昨日"跨界半导体"叙事的核心标的，
今日集体回落——<b>说明昨日那种"壳资源 + 资产注入"的脉冲没有持续性</b>。<br>
<b>流入端：</b>医疗服务 __HY_MEDSVC_Y__→__HY_MEDSVC__ 家（贝瑞基因 / 皓宸医疗 / 合富中国，三家均无联动叙事，属分散补涨）、
汽车零部 __HY_QC_Y__→__HY_QC__ 家（襄阳轴承 / 中马传动 / 长华集团，实为机器人零部件）、
林业Ⅱ __HY_LY_Y__→__HY_LY__ 家（福建金森 / 平潭发展，实为福建题材）、水泥 __HY_SN_Y__→__HY_SN__ 家（福建水泥 / 国统股份）、
服装家纺 __HY_FZJZ_Y__→__HY_FZJZ__ 家、广告营销 __HY_GGYX_Y__→__HY_GGYX__ 家、军工电子 __HY_JG_Y__→__HY_JG__ 家（商业航天双票）。<br>
<span class="hl">行业集中度：今日 __ZT__ 只涨停分散在 __N_HY0__ 个东财行业，最大集群「__TOP_HY0__」__TOP_HY0_N__ 只、仅占 __SHARE_HY0__%</span>
（昨日 __ZT_Y__ 只分散在 __N_HY1__ 个行业，最大集群「__TOP_HY1__」__TOP_HY1_N__ 只占 __SHARE_HY1__%）。
<b>32 个行业、最大集群只占 __SHARE_HY0__%——东财行业标签维度已经完全失效</b>，因为今日的两条主线（福建系、机器人零部件）恰恰是<b>跨行业</b>的：
真正的共同点在地域与产业链环节，而不在行业分类里。这是本报告坚持用"题材集群"而非"行业分布"做归因的原因。
</div>
<h3>标签陷阱：行业标签同为「通用设备」，两天的成分却几乎全换（轮换率 __TYSB_ROT__%）</h3>
<table style="margin-top:8px">
<tr><th>今日「通用设备」涨停股</th><th>代码</th><th>连板</th><th>封单</th><th>涨停原因</th></tr>
__TBL_TYSB__
</table>
<div class="note" style="margin-top:8px">
昨日「通用设备」__HY_TYSB_Y__ 家（优利德、普源精电、东方中科、莱伯泰科、威星智能、申科股份，共同叙事是"电子测量/科学仪器"），
今日「通用设备」__HY_TYSB__ 家，但<span class="hl">只有 __TYSB_KEEP_N__ 只（__TYSB_KEEP__）留存，轮换率 __TYSB_ROT__%</span>。
今日这 6 只其实是三个完全不同的叙事混装：仪器（电科思仪）、机器人零部件（大业股份、洛轴股份、宁波东力）、军工物流（昆船智能）。
<b>结论：看到"某行业涨停家数持平"不要直接读成"该行业延续"，必须先看成分是否被换掉。</b>
</div>
</div>

<div class="card">
<h2>六、昨日涨停股今日表现：晋级率 __ADV_RATE__%，连板组仍强、昨日 3 板的中位梯队是最大失血点</h2>
<div class="kpis" style="grid-template-columns:repeat(auto-fit,minmax(140px,1fr))">
  <div class="kpi"><div class="lbl">晋级率</div><div class="val up">__ADV_RATE__%</div><div class="dt mut">__ADV_N__/__ADV_TOT__（昨 19.4%）</div></div>
  <div class="kpi"><div class="lbl">平均涨幅</div><div class="val up">__PERF_MEAN__%</div><div class="dt mut">中位 __PERF_MED__%</div></div>
  <div class="kpi"><div class="lbl">翻绿比例</div><div class="val down">__NEG_PCT__%</div><div class="dt mut">__NEG__ 只（跌超5% 共 __NEG_LOW__ 只）</div></div>
  <div class="kpi"><div class="lbl">最强</div><div class="val up">__PERF_MAX__%</div><div class="dt mut">__PERF_MAX_NAME__</div></div>
  <div class="kpi"><div class="lbl">最弱</div><div class="val down">__PERF_MIN__%</div><div class="dt mut">__PERF_MIN_NAME__</div></div>
</div>
<div class="note" style="margin-top:14px">
昨日 __ADV_TOT__ 只涨停股今日平均 __PERF_MEAN__%、中位 __PERF_MED__%，晋级 __ADV_N__ 只（__ADV_RATE__%），翻绿 __NEG__ 只（__NEG_PCT__%）、跌超 5% 的 __NEG_LOW__ 只。
分层看：<b>昨日首板 n=__ADV_S_N__ 晋级率 __ADV_S_RATE__%、中位 __ADV_S_MED__%；昨日连板 n=__ADV_L_N__ 晋级率 __ADV_L_RATE__%、中位 __ADV_L_MED__%</b>。<br>
<span class="hl">连板组中位为正已连续第三个交易日成立（9/22 +2.77%、9/23 +1.25%、今日 __ADV_L_MED__%），而首板组中位在 -0.06% 上下反复（9/23 为 -2.62%）</span>，
两组差距 __ADV_GAP__ 个百分点，比 9/23 的 3.87pct 明显收窄。<b>"买确认赚钱、买扩散不赚钱"的结构仍在，但强度在减弱</b>——
一旦连板组中位也转负，就是本轮退潮的最后一环。<br>
最弱三只 __PERF_BOT3__，<span class="hl">全部来自昨日的 3 板梯队（房地产服务 / 房地产开发 / IT服务）</span>；
最强三只 __PERF_TOP3__ 来自昨天的 1~3 板（纺织制造 / 出版 / 电视广播）。
最弱名单里 3 板占 3 席，正是第三节"3 板梯队由 7 只塌成 1 只"在个股层面的直接映射。
</div>
<div id="c_perf" class="chart" style="height:700px;margin-top:8px"></div>
</div>

<div class="card">
<h2>七、封板节奏与成交结构：早盘封板占比 __TS_EARLY_PCT__%（昨 __TS_EARLY_Y_PCT__%），节奏大幅前移、午后基本停滞</h2>
<div class="two">
<div><div id="c_ts" class="chart-sm"></div></div>
<div>
<table>
<tr><th>封板时段</th><th>__L_D1__</th><th>__L_D0__</th></tr>
__TBL_TS__
</table>
<div class="note" style="margin-top:10px">
早盘封板（竞价 + 开盘半小时）占比由 __TS_EARLY_Y_PCT__%（__TS_EARLY_Y__/__ZT_Y__）升到 <span class="hl">__TS_EARLY_PCT__%（__TS_EARLY__/__ZT__）</span>，
而上午盘中（09:30–11:30 之后段）由 12 只降到 5 只、午后由 __TS_PM1__ 只降到 __TS_PM0__ 只。
<span class="hl">"早盘一次性定局、午后不再产生新板"是本日最典型的分时特征</span>，也解释了为什么炸板数会骤降：
资金在开盘半小时内就把仓位打满，之后不再参与博弈，市场自然没有"冲了又炸"的样本。
这与 9/24 指数低开低走的形态互为因果——<b>午后不接力，指数就只能单边走低</b>。
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
涨停股合计成交 __AMT_SUM__ 亿（昨 __AMT_SUM_Y__ 亿，环比 -15%），占两市 __SHARE__%（昨 __SHARE_Y__%），仍低于 3%~8% 常规区间；
用单只中位成交额二次校验：__AMT_MED__ 亿（昨 __AMT_MED_Y__ 亿）→ <b>字段源无误，比值低是家数与总量同步收缩的结果</b>。<br>
封单合计 __FUND_SUM__ 亿（昨 __FUND_SUM_Y__ 亿），其中 <span class="hl">__FUND_TOP_NAME__ 一只占 __FUND_TOP_VAL__ 亿、即全部封单的 __FUND_TOP_PCT__%</span>；
但封单中位数 __FUND_MED__ 亿<b>高于</b>昨日 __FUND_MED_Y__ 亿——剔除头部极端值后，普通涨停股的封单是变厚的。<br>
<span class="hl">把三个指标连起来读，才是本日最重要的资金结论：涨停股合计成交额 -15%、单只中位成交额 -15%、而封单中位数 +13%</span> ——
这是<b>"缩量锁仓"的教科书式组合</b>：成交在萎缩、但封单在变厚，说明筹码没有换手，只是被锁住了。
它短期看起来"封板率高、炸板少"，但<b>缺乏换手意味着一旦有人先跑，承接盘会很薄</b>（今日 __HUANSHOU__ 只换手板占 __HUANSHOU_PCT__%，一字板仅 __ONEWORD__ 只）。
</div>
</div>

<div class="card">
<h2>八、资金运动的三个结论</h2>
<ul>
<li><b>① 总量：连续第二日缩量，跌幅反而扩大——抛压来自"没人接"而不是"有人在卖"。</b>
两市成交额 __AMT__ 亿（__AMT_D__ 亿、__AMT_PCT__%），同时上证 __SH_PCT2__%、创业板指 __CY_PCT2__%、中小100 __IX_ZXX100_PCT__%。
<span class="hl">缩量与跌幅扩大同时出现，只能解释为买盘撤退而非卖盘涌出</span>（否则成交额应放大）。
所有指数低开低走、全天无反抽，进一步印证了"承接真空"。</li>
<li><b>② 方向：权重是唯一避风港，题材与成长两头被抽。</b>
成交额环比上，上证50 __SZ50_AMT_PCT__%（唯一放量）且 __IX_SZ50_PCT__% 最抗跌；中证1000 __ZZ1000_AMT_PCT__%、国证2000 __GZ2000_AMT_PCT__%、北证50 缩幅最大；
成长中盘（科创50 __KC_AMT_PCT__%、创业板指 __CYB_AMT_PCT__%）居中但跌幅最深。
<span class="hl">资金从"题材小盘 + 成长中盘"撤到"大盘价值"，这是一次典型的防御性再平衡</span>，而非新的进攻方向建立。
打板端的对应表现是：涨停全部集中在低价小市值（福建系 __STR_N__ 只 + 机器人零部件 __ROBOT_N__ 只），
<b>中大盘科技硬件今天连冲板的意愿都没有</b>（炸板池里只剩先导基电一只半导体大票）。</li>
<li><b>③ 结构：高度单点化、腰部换血、参与收缩。</b>
最高板升到 __MAXB__（__LB_TOP1__），但 3 板梯队由 __LAD3_Y__ 只塌成 __LAD3_T__ 只、2 板由 __LAD2_Y__ 只暴增到 __LAD2_T__ 只；
触及涨停家数 __TOUCH_Y__→__TOUCH__（__TOUCH_PCT_D__%）说明参与资金在减少；
封单中位数上升而成交额下降，说明留下的资金在<b>锁仓而非进攻</b>。
<span class="hl">"低位补涨 + 高度单点 + 缩量锁仓"三者叠加，通常对应指数的继续整理与题材的加速轮动，而不是新一轮上攻的起点</span>。</li>
</ul>
</div>

<div class="card">
<h2>九、明日观察要点与风险</h2>
<ul>
<li><b>三个阈值判断"收缩"是暂停还是延续：</b>今日封板率 __SEAL__% 是本轮 9/21 以来最高。若明日<b>涨停家数回到 65 家以上、封板率保持 78% 以上</b>，则今日是缩量整理；若
<b>涨停家数跌破 40 家、或触及涨停家数继续低于 55 家</b>，则"参与收缩"演变为持续性退潮（封板率再高也无意义，因为没有量）。</li>
<li><b>福建/海峡两岸 __STR_N__ 只能否走出第二日：</b>这是今日唯一成规模的主线，但全部为首板 + 1 只 2 板，<span class="hl">没有一只形成高度</span>。
地域题材的典型路径是"首日批量、次日分化留 2~3 只"。需要盯住的是封单最厚的 <b>平潭发展（__STR_FUND__ 亿中的主要部分）</b>与港口物流的厦门港务，
若明日这两只不能连板，则集群大概率一日游。</li>
<li><b>机器人零部件能否替代福建系成为新主线：</b>__ROBOT_N__ 只有产业逻辑（轴承 / 减速器 / 丝杠），连板 3 只（奥佳华 4 板、东方中科 / 上工申贝 2 板）、其余 __ROBOT_N__-3 只全为首板。
但<span class="hl">缺少真正同叙事的龙头</span>——最高的奥佳华主业是按摩椅 + 具身智能，与轴承/减速器并非同一条细分线。
<b>判断标准是次日是否出现 3 板以上的轴承/减速器标的</b>；若无，则归类为与昨日"测量仪器"同性质的单日脉冲。</li>
<li><b>高度标杆只有 __MAXB__ 板一只：</b>__LB_TOP1__（5 天 5 板，__LB_TOP1_REASON__）与三只 4 板（奥佳华 / 新华传媒 / 泰慕士）。
回顾本轮：华瓷股份 6 板 → 断板，内蒙新华 5 板 → 断板后今日反包（7 天 6 板）。<b>高位股的断板-反包循环说明资金仍在，但没有一只敢于持续做高度</b>。</li>
<li><b>「华」字辈与新华系的锁仓风险：</b>__FUND_TOP_NAME__ 连续两日封单第一（昨 __FUND_TOP_Y_VAL__ 亿、今 __FUND_TOP_VAL__ 亿），
封单/成交达 __FUND_TOP_RATIO__ 倍。这种结构的脆弱性是<b>非线性的</b>——不开口看不出问题，一开口就是急跌，且会同步冲击出版板块（今日 __HY_CB__ 家）与整个「华」字辈情绪。</li>
<li><b>跌停家数仍在两位数：</b>跌停 __DT__ 家、跌停触及 16 家（打开 __DT_OPEN__ 家）、封死率 __DT_LOCK__%。
<b>连续两日跌停触及 16 家，说明个股层面的风险释放尚未结束</b>，不宜把"封板率高"当作个股风险下降的信号。</li>
<li><b>北证50 的避险属性消退：</b>昨日北证50 是唯一上涨方向，今日 __IX_BJ50_PCT__% 且成交额环比 -12.9%（缩幅全市场最大）。
<span class="hl">昨日的背离一天就修复了，说明它不是资金流入信号</span>；北交所流动性风险显著高于沪深，不应作为情绪指标使用。</li>
<li><b>数据口径：</b>统计为沪深两市；东财涨停池 tc=__ZT_D_EM__ 家、同花顺 __ZT__ 家，<span class="hl">差额 __ZT_EM_DIFF__ 只为北交所标的（920748）</span>，本报告按沪深口径取 __ZT__ 家。
跌停家数两源不一致：同花顺汇总 __DT__ 家、东财 em_DT tc=__DT_EM_T__ 家且明细池返回空，<b>差额 __DT_EM_DIFF__ 只无法归因</b>，本报告采用同花顺汇总口径并声明此差异。
封板时间双源分钟级一致率 100%（可比样本 __ZT__ 只）。<br>
另有一条需披露的口径现象：东财炸板池 10 只中 <b>001317 三羊马收盘价等于涨停价（+10.01%）</b>，但同花顺与东财的涨停池<b>均未收录</b>它，
本报告因此仍按两源口径计为"涨停 __ZT__ 家 / 炸板 __ZB__ 家"。同类现象在 09-22（603893 瑞芯微收 +10.00%、同样仅出现在炸板池）已出现过，
<b>属数据源既有行为</b>（推测按"收盘是否有封单"筛选），不影响结构与资金结论。
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
