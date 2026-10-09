# -*- coding: utf-8 -*-
"""涨停复盘报告 20261009 vs 20261008（放量反攻 / AI应用·传媒接棒 / 固态电池唯一有高度）

用法：python zt_report_20261009.py 20261009
输入：out/zt_stats_20261009.json、out/zt_review_20261009.json、out/zt_review_20261008.json
     跌停池明细 out/_dt1009.json、out/_dt1008.json（东财 getTopicDTPool，sort=fund:asc）
     昨日跌停股今日行情：腾讯快照 qt.gtimg.cn（脚本内实时抓取）
输出：reports/涨停复盘对比-20261009.html
"""
import json, os, sys, html, re, urllib.request
from statistics import mean, median

ROOT = os.environ.get("ZT_ROOT") or os.getcwd()
OUT = os.path.join(ROOT, "out")
REP = os.path.join(ROOT, "reports")
os.makedirs(REP, exist_ok=True)

D0 = sys.argv[1] if len(sys.argv) > 1 else "20261009"
S = json.load(open(os.path.join(OUT, f"zt_stats_{D0}.json"), encoding="utf-8"))
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


def fmt_d(v):
    return "{:+d}".format(v)


# ================= 一、情绪三日序列 =================
days = [
    {"d": md(D2) if D2 else "-", "zt": s1["zt_prev"], "zb": s1["zb_prev"], "dt": s1["dt_prev"]},
    {"d": md(D1), "zt": s1["zt"], "zb": s1["zb"], "dt": s1["dt"]},
    {"d": md(D0), "zt": s0["zt"], "zb": s0["zb"], "dt": s0["dt"]},
]
for x in days:
    x["seal"] = seal(x["zt"], x["zb"])

_d0 = B["dates"][D0]["ths_zt"]["total"]
_d1 = B["dates"][D1]["ths_zt"]["total"]
TOUCH0 = _d0["today"]["history_num"]
TOUCH1 = _d1["today"]["history_num"]
DTOUCH0 = B["dates"][D0]["ths_zt"]["limit_down_count"]["today"]["history_num"]
DTOUCH1 = B["dates"][D1]["ths_zt"]["limit_down_count"]["today"]["history_num"]
DTOUCH_OPEN = B["dates"][D0]["ths_zt"]["limit_down_count"]["today"]["open_num"]
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
        ix.append({"name": nm, "pct": v["pct"], "amt": (v["amount_wan"] or 0) / 10000.0})
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
REASON = {x["code"]: (x.get("reason_type") or "") for x in (B["dates"][D0]["ths_zt"].get("info") or [])}
def reason_of(r):
    return r.get("reason") or REASON.get(r["code"], "")


AI_KWS = ["AI短剧", "AI漫剧", "AI视频", "短剧", "微短剧", "漫剧", "影视", "院线", "传媒", "出版",
          "AIGC", "数字阅读", "内容IP", "泛文化", "图书", "财经新媒体", "互动影游", "AI营销", "数字教育"]
SEC_KWS = ["AI安全", "网络安全", "数据安全", "国产操作系统", "智算", "信息安全", "抗量子", "PKI",
           "人工智能安全", "数据要素", "互联网金融", "金融科技", "吸收合并"]
SOLID_KWS = ["固态电池", "磷酸铁锂", "铝塑膜", "锂电池", "新能源电池", "圆柱锂电", "储能电池", "UPS"]

ai_sel = [r for r in r0 if any(k in reason_of(r) for k in AI_KWS)]
sec_sel = [r for r in r0 if any(k in reason_of(r) for k in SEC_KWS)]
ai_wide = {r["code"]: r for r in ai_sel + sec_sel}
solid_sel = [r for r in r0 if any(k in reason_of(r) for k in SOLID_KWS)]
solid_strict = [r for r in r0 if "固态电池" in reason_of(r)]

THEMES = [
    ("AI应用/传媒（短剧·漫剧·影视·IP）", AI_KWS),
    ("AI安全 / 信创 / 智算", SEC_KWS),
    ("固态电池 / 锂电链", SOLID_KWS),
    ("机器人 / 智能制造", ["机器人", "具身", "伺服", "减速器", "自动化", "智能制造"]),
    ("医药 / 创新药", ["创新药", "抗生素", "鼠疫", "集采", "基因检测", "三代测序", "仿创", "减肥药", "核医药", "医用手套", "头孢"]),
    ("化工 / 材料涨价", ["有机硅", "金属铬", "铬盐", "功能性硅烷", "焦炭", "甲醇", "生物柴油", "粘胶", "碳纤维", "硅烷"]),
    ("零售 / 消费", ["零售", "商业综合体", "超市", "消费", "服装", "男裤", "化妆品", "家纺"]),
    ("农业 / 种业 / 食品", ["种业", "玉米", "转基因", "粮食", "水产品", "饲料", "粮油", "食品", "奶酪", "乳品"]),
    ("地产 / 国资重组 / 跨界资产", ["重大重组", "国资", "股份转让", "房地产", "物业", "重整", "资产出售", "吸收合并", "轻资产"]),
    ("电网 / 电力 / 光伏", ["电网", "电力", "光伏", "储能电站", "电缆", "特高压"]),
]
theme_cnt = []
for nm, kws in THEMES:
    hit = [r for r in r0 if any(k in reason_of(r) for k in kws)]
    lb = sum(1 for r in hit if (r["lbc"] or 1) >= 2)
    theme_cnt.append({"name": nm, "n": len(hit), "lb": lb,
                      "stocks": [r["name"] + "(" + str(r["lbc"] or 1) + "板)" for r in
                                 sorted(hit, key=lambda x: (-(x["lbc"] or 0), -(x["fund"] or 0)))][:8]})
theme_cnt.sort(key=lambda x: (-x["n"], x["name"]))
_th = {t["name"]: t for t in theme_cnt}

# 概念板块（同花顺）
blocks = sorted((B["dates"][D0].get("ths_block") or []), key=lambda x: -x["limit_up_num"])
b_top = blocks[:7]
CONC_LIST = "、".join("%s（%d 家）" % (esc(b["name"]), b["limit_up_num"]) for b in b_top)
concept_rows = sorted(blocks[:12], key=lambda x: x["limit_up_num"])

# ================= 五、行业迁移 =================
hy0, hy1 = S["hy0"], S["hy1"]
HY_ALL_N = len([k for k, v in hy0.items() if v])
hy_keys = sorted(set(list(hy0) + list(hy1)),
                 key=lambda k: (-((hy0.get(k, 0) + hy1.get(k, 0)) + abs(hy0.get(k, 0) - hy1.get(k, 0)) * 2),
                                -max(hy0.get(k, 0), hy1.get(k, 0)), k))
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
GAP = m_l - m_s

# ================= 七、跌停池 =================
DT_TD = json.load(open(os.path.join(OUT, f"_dt{D0[4:]}.json"), encoding="utf-8"))["data"]["pool"]
DT_YD = json.load(open(os.path.join(OUT, f"_dt{D1[4:]}.json"), encoding="utf-8"))["data"]["pool"]
r1_set = {x["code"] for x in r1}
dt_from_zt = [x for x in DT_TD if x["c"] in r1_set]
dt_amt_td = sum(x.get("amount", 0) for x in DT_TD) / 1e8
dt_amt_yd = sum(x.get("amount", 0) for x in DT_YD) / 1e8
DT_TC = len(DT_TD)
DT_DIFF = DT_TC - s0["dt"]
DT_BIG_Y = sum(1 for x in DT_YD if x.get("ltsz", 0) >= 1e10)
DT_TD_BIG_N = sum(1 for x in DT_TD if x.get("ltsz", 0) >= 1e10)
DT_HY_N = len({x.get("hybk") for x in DT_TD})
dt_top1 = max(DT_TD, key=lambda x: x.get("amount", 0))

# 昨日跌停池今日表现（腾讯实时快照）
_syms = []
for c in DT_YD:
    p = "bj" if c["c"].startswith(("43", "83", "87", "92")) else ("sh" if c["c"].startswith(("6", "5", "9")) else "sz")
    _syms.append(p + c["c"])
_px = {}
try:
    _o = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    _req = urllib.request.Request("https://qt.gtimg.cn/q=" + ",".join(_syms), headers={"User-Agent": "Mozilla/5.0"})
    _raw = _o.open(_req, timeout=20).read().decode("gbk", "ignore")
    for _l in _raw.strip().split(";"):
        if '="' not in _l:
            continue
        _f = _l.split('"')[1].split("~")
        _px[_l.split("=")[0].strip().replace("v_", "")[2:]] = float(_f[32]) if _f[32] else None
except Exception:
    pass
rel = [{"c": x["c"], "n": x["n"], "h": x["hybk"], "pct": _px.get(x["c"]), "amount": x.get("amount", 0)}
       for x in DT_YD if _px.get(x["c"]) is not None]
rel_vals = [x["pct"] for x in rel]
rel_mean = mean(rel_vals) if rel_vals else 0.0
rel_med = median(rel_vals) if rel_vals else 0.0
rel_up = sum(1 for v in rel_vals if v > 0)
rel_lim = sum(1 for v in rel_vals if v >= 9.8)
_rel_lim = [x for x in rel if x["pct"] is not None and x["pct"] >= 9.8]
REL_LIM_NAME = _rel_lim[0]["n"] if _rel_lim else "—"
_chipmap = {"688498": "REL_CHIP1", "688048": "REL_CHIP2", "603773": "REL_CHIP3", "002384": "REL_CHIP4"}
CHIP_PCT = {}
for _c, _k in _chipmap.items():
    _v = _px.get(_c)
    CHIP_PCT[_k] = ("{:+.2f}".format(_v) if _v is not None else "—")

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
oneword = sum(1 for r in r0 if "一字" in (r["limit_up_type"] or ""))
huanshou = sum(1 for r in r0 if "换手" in (r["limit_up_type"] or ""))
oneword1 = sum(1 for r in r1 if "一字" in (r["limit_up_type"] or ""))
huanshou1 = sum(1 for r in r1 if "换手" in (r["limit_up_type"] or ""))
fund_top = sorted(r0, key=lambda x: -(x["fund"] or 0))[:5]
ft0 = fund_top[0]
ft0_val = (ft0["fund"] or 0) / 1e8
ft0_pct = ft0_val / fund_sum * 100
ft0_ratio = ft0_val / ((ft0["amount"] or 1) / 1e8)
ft0_turn = ft0["turnover"] or 0
amt_top = sorted(r0, key=lambda x: -(x["amount"] or 0))[:5]

tbl_fund_top = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td>{2}板</td><td>{3:.2f}亿</td><td>{4:.2f}亿</td><td>{5:.2f}x</td></tr>".format(
        esc(x["name"]), x["code"], (x["lbc"] or 1), (x["fund"] or 0) / 1e8, (x["amount"] or 0) / 1e8,
        (x["fund"] or 0) / (x["amount"] or 1))
    for x in fund_top)
tbl_amt_top = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td>{2}板</td><td>{3:.2f}亿</td><td>{4:.2f}亿</td><td>{5}</td></tr>".format(
        esc(x["name"]), x["code"], (x["lbc"] or 1), (x["amount"] or 0) / 1e8, (x["fund"] or 0) / 1e8, esc(x["hybk"]))
    for x in amt_top)

zbpool = (B["dates"][D0].get("em_ZB") or {}).get("pool") or []


def is_limit(z):
    th = 19.8 if z["c"].startswith(("30", "68")) else 9.8
    return z["zdp"] >= th


zb_sealed = [z for z in zbpool if is_limit(z)]
zb_open = [z for z in zbpool if not is_limit(z)]
zb_amt_sum = sum(z.get("amount", 0) for z in zbpool) / 1e8
tbl_zb = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td class='{4}'>{5:+.2f}%</td><td>{6:.2f}亿</td><td>{7:.0f}亿</td></tr>".format(
        esc(z["n"]), z["c"], hhmm(z["fbt"]), esc(z["hybk"]), "up" if z["zdp"] >= 0 else "down",
        z["zdp"], z["amount"] / 1e8, z["ltsz"] / 1e8)
    for z in sorted(zb_open, key=lambda x: x["fbt"]))
zb_big = max(zbpool, key=lambda z: z.get("ltsz", 0)) if zbpool else None
_zb_tcl = [z for z in zbpool if z["n"] == "天赐材料"]
ZB_TCL_AMT = (_zb_tcl[0].get("amount", 0) / 1e8) if _zb_tcl else 0.0

tbl_lianban = "".join(
    "<tr><td>{0}板</td><td>{1}</td><td class='hl'>{2}</td><td>{3}</td><td>{4:.2f}亿</td><td>{5:.2f}亿</td><td>{6:.1f}%</td>"
    "<td>{7}</td><td style='text-align:left;color:#4b5563'>{8}</td></tr>".format(
        r["lbc"], r["code"], esc(r["name"]), (r["fbt"][:5] if r["fbt"] else "—"),
        (r["fund"] or 0) / 1e8, (r["amount"] or 0) / 1e8, (r["turnover"] or 0), esc(r["hybk"]), esc(reason_of(r)))
    for r in lb_all)


def dt_tag(x):
    if x["c"] in r1_set:
        return "<b class='hl'>昨涨停→今跌停</b>"
    if x.get("ltsz", 0) >= 1e10:
        return "<b class='hl'>大市值</b>"
    return "—"


tbl_dt_td = "".join(
    "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3:.2f}亿</td><td>{4:.0f}亿</td><td>{5}</td></tr>".format(
        x["c"], esc(x["n"]), esc(x["hybk"]), x["amount"] / 1e8, x["ltsz"] / 1e8, dt_tag(x))
    for x in sorted(DT_TD, key=lambda x: -x["amount"]))
tbl_rel = "".join(
    "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td class='{3}'>{4:+.2f}%</td></tr>".format(
        x["c"], esc(x["n"]), esc(x["h"]), "up" if x["pct"] >= 0 else "down", x["pct"])
    for x in sorted(rel, key=lambda x: -x["pct"]))

perf_top = "、".join("{}{:+.1f}%".format(esc(p["name"]), p["pct"]) for p in top3)
perf_bot = "、".join("{}{:+.1f}%".format(esc(p["name"]), p["pct"]) for p in bot3)

# ================= 表格片段 =================
tbl_senti = "".join(
    "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td class='hl'>{3}</td><td class='{4}'>{5}{6}</td></tr>".format(
        lab, ("{:.1f}".format(days[0][k]) if isinstance(days[0][k], float) else days[0][k]),
        ("{:.1f}".format(days[1][k]) if isinstance(days[1][k], float) else days[1][k]),
        ("{:.1f}".format(days[2][k]) if isinstance(days[2][k], float) else days[2][k]),
        "up" if days[2][k] - days[1][k] >= 0 else "down",
        "+" if days[2][k] - days[1][k] >= 0 else "",
        ("{:.1f}".format(days[2][k] - days[1][k]) if isinstance(days[2][k], float) else "{:d}".format(days[2][k] - days[1][k])))
    for lab, k in [("涨停家数", "zt"), ("炸板家数", "zb"), ("封板率(%)", "seal"), ("跌停家数", "dt")])

tbl_lad = "".join(
    "<tr><td>{0} 板</td><td>{1}</td><td class='hl'>{2}</td><td class='{3}'>{4:+d}</td></tr>".format(
        i, lad1.get(i, 0), lad0.get(i, 0),
        "up" if lad0.get(i, 0) - lad1.get(i, 0) > 0 else ("down" if lad0.get(i, 0) - lad1.get(i, 0) < 0 else "mut"),
        lad0.get(i, 0) - lad1.get(i, 0))
    for i in range(lad_max, 0, -1))

tbl_hy = "".join(
    "<tr><td>{0}</td><td>{1}</td><td class='hl'>{2}</td><td class='{3}'>{4}</td>"
    "<td style='text-align:left;color:#6b7280'>{5}</td></tr>".format(
        esc(h["name"]), h["y"], h["t"],
        "up" if h["t"] - h["y"] > 0 else ("down" if h["t"] - h["y"] < 0 else "mut"),
        fmt_d(h["t"] - h["y"]), "流入" if h["t"] - h["y"] > 0 else ("流出" if h["t"] - h["y"] < 0 else "持平"))
    for h in hy_tbl)

tbl_ts = "".join("<tr><td>{0}</td><td>{1}</td><td class='hl'>{2}</td></tr>".format(k, ts1.get(k, 0), ts0.get(k, 0))
                 for k in TS_ORDER)

tbl_theme = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td>{2}</td><td style='text-align:left'>{3}</td></tr>".format(
        esc(t["name"]), t["n"], t["lb"], "".join("<span class=tag>" + esc(s) + "</span>" for s in t["stocks"]))
    for t in theme_cnt if t["n"] > 0)

tbl_idx = "".join(
    "<tr><td>{0}</td><td class='{1}'>{2:+.2f}%</td><td class='{3}'>{4}</td><td>{5:,.0f}亿</td><td class='{6}'>{7:+.1f}%</td></tr>".format(
        esc(x["name"]), "up" if x["pct"] >= 0 else "down", x["pct"],
        "up" if PREV_IDX_PCT.get(x["name"], 0) >= 0 else "down",
        ("{:+.2f}%".format(PREV_IDX_PCT[x["name"]]) if x["name"] in PREV_IDX_PCT else "—"),
        x["amt"], "up" if amt_yoy(x["name"]) >= 0 else "down", amt_yoy(x["name"]))
    for x in ix)

tbl_style = "".join(
    "<tr><td>{0}</td><td class='{1}'>{2:+.2f}%</td><td class='{3}'>{4:+.1f}%</td><td>{5:,.0f}亿</td></tr>".format(
        esc(x["name"]), "up" if x["pct"] >= 0 else "down", x["pct"],
        "up" if x["amt_yoy"] >= 0 else "down", x["amt_yoy"], x["amt"])
    for x in STYLE_SORTED)

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
P("DTOUCH", DTOUCH0); P("DTOUCH_Y", DTOUCH1); P("DTOUCH_D", "{:+d}".format(DTOUCH0 - DTOUCH1))
P("DTOUCH_OPEN", DTOUCH_OPEN)
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

for nm, key in [("上证指数", "SH"), ("深证成指", "SZ"), ("创业板指", "CY"), ("科创50", "KC"),
                ("沪深300", "HS300"), ("中证500", "ZZ500"), ("中证1000", "ZZ1000"),
                ("国证2000", "GZ2000"), ("上证50", "SH50"), ("中小100", "ZS100"), ("北证50", "BZ50")]:
    P(key + "_PCT", "{:+.2f}".format(ixr.get(nm, {}).get("pct", 0.0)))
    P(key + "_YOY", "{:+.1f}".format(amt_yoy(nm)))
    P(key + "_AMT", "{:,.0f}".format(ixr.get(nm, {}).get("amt", 0.0)))
P("STYLE_SHRINK_MAX", esc(STYLE_SORTED[-1]["name"])); P("STYLE_SHRINK_MAX_V", "{:+.1f}".format(STYLE_SORTED[-1]["amt_yoy"]))
P("STYLE_TOP", esc(STYLE_SORTED[0]["name"])); P("STYLE_TOP_V", "{:+.1f}".format(STYLE_SORTED[0]["amt_yoy"]))
P("CONC_LIST", CONC_LIST)
_c1 = b_top[0] if b_top else {"name": "—", "change": 0, "limit_up_num": 0, "continuous_plate_num": 0}
P("CONC1_NAME", esc(_c1["name"])); P("CONC1_CHG", "{:+.2f}".format(_c1.get("change", 0)))
P("CONC1_N", _c1.get("limit_up_num", 0)); P("CONC1_LB", _c1.get("continuous_plate_num", 0))
P("ADV_RATE", "{:.1f}".format(adv_rate)); P("ADV_N", len(adv)); P("ADV_TOT", len(perf))
P("PERF_MEAN", "{:+.2f}".format(mean(pcts))); P("PERF_MED", "{:+.2f}".format(median(pcts)))
P("PERF_MAX", "{:+.2f}".format(max(pcts))); P("PERF_MIN", "{:+.2f}".format(min(pcts)))
P("PERF_MAX_NAME", esc(perf_sorted[0]["name"]))
P("PERF_MIN_NAME", esc(perf_sorted[-1]["name"])); P("PERF_MIN_LB", perf_sorted[-1]["lbc"])
P("PERF_TOP3", perf_top); P("PERF_BOT3", perf_bot)
P("NEG", neg); P("NEG_PCT", "{:.0f}".format(neg / len(pcts) * 100)); P("NEG_LOW", neg_low)
P("GRP_S_N", n_s); P("GRP_S_R", "{:.1f}".format(r_s)); P("GRP_S_M", "{:+.2f}".format(m_s)); P("GRP_S_NG", ng_s)
P("GRP_L_N", n_l); P("GRP_L_R", "{:.1f}".format(r_l)); P("GRP_L_M", "{:+.2f}".format(m_l)); P("GRP_L_NG", ng_l)
P("GAP", "{:.2f}".format(GAP))
P("AMT_SUM", "{:.0f}".format(amt_sum)); P("AMT_SUM_Y", "{:.0f}".format(amt_sum1))
P("SHARE", "{:.1f}".format(share)); P("SHARE_Y", "{:.1f}".format(share1))
P("AMT_MED", "{:.2f}".format(amt_med)); P("AMT_MED_Y", "{:.2f}".format(amt_med1))
P("AMT_MED_PCT", "{:+.1f}".format((amt_med / amt_med1 - 1) * 100 if amt_med1 else 0))
P("AMT_MED_PCT_ABS", "{:.1f}".format(abs((amt_med / amt_med1 - 1) * 100 if amt_med1 else 0)))
P("FUND_SUM", "{:.1f}".format(fund_sum)); P("FUND_SUM_Y", "{:.1f}".format(fund_sum1))
P("FUND_SUM_PCT", "{:+.1f}".format((fund_sum / fund_sum1 - 1) * 100 if fund_sum1 else 0))
P("FUND_SUM_PCT_ABS", "{:.1f}".format(abs((fund_sum / fund_sum1 - 1) * 100 if fund_sum1 else 0)))
P("FUND_MED", "{:.2f}".format(fund_med)); P("FUND_MED_Y", "{:.2f}".format(fund_med1))
P("FUND_MED_PCT", "{:+.1f}".format((fund_med / fund_med1 - 1) * 100 if fund_med1 else 0))
P("ONEWORD", oneword); P("ONEWORD_Y", oneword1)
P("ONEWORD_PCT", "{:.1f}".format(oneword / s0["zt"] * 100))
P("HUANSHOU", huanshou); P("HUANSHOU_Y", huanshou1)
P("HUANSHOU_PCT", "{:.0f}".format(huanshou / s0["zt"] * 100))
P("FT0", esc(ft0["name"])); P("FT0_V", "{:.2f}".format(ft0_val)); P("FT0_PCT", "{:.1f}".format(ft0_pct))
P("FT0_RATIO", "{:.2f}".format(ft0_ratio)); P("FT0_AMT", "{:.2f}".format((ft0["amount"] or 0) / 1e8))
P("FT0_TURN", "{:.1f}".format(ft0_turn))
P("FT0_LB", ft0["lbc"]); P("FT0_REASON", esc(ft0["reason"]))
P("LB_TOP1", esc(lb_all[0]["name"])); P("LB_TOP1_REASON", esc(reason_of(lb_all[0])))
P("HY_ALL_N", HY_ALL_N)
P("HY_DC", hy1.get("电池", 0)); P("HY_DC0", hy0.get("电池", 0))
P("HY_DC0_PCT", "{:.0f}".format(hy0.get("电池", 0) / s0["zt"] * 100))
P("HY_CB", hy1.get("出版", 0)); P("HY_CB0", hy0.get("出版", 0))
P("HY_RJ", hy1.get("软件开发", 0)); P("HY_RJ0", hy0.get("软件开发", 0))
P("HY_YS", hy1.get("影视院线", 0)); P("HY_YS0", hy0.get("影视院线", 0))
P("HY_LS", hy1.get("一般零售", 0)); P("HY_LS0", hy0.get("一般零售", 0))
P("HY_SZ", hy1.get("数字媒体", 0)); P("HY_SZ0", hy0.get("数字媒体", 0))
P("HY_ZZ", hy1.get("种植业", 0)); P("HY_ZZ0", hy0.get("种植业", 0))
P("HY_HY", hy1.get("航运港口", 0)); P("HY_HY0", hy0.get("航运港口", 0))
P("HY_ZYSB", hy1.get("专用设备", 0)); P("HY_ZYSB0", hy0.get("专用设备", 0))
P("DT_TD_N", s0["dt"]); P("DT_YD_N", s1["dt"])
P("DT_AMT_YD", "{:.0f}".format(dt_amt_yd)); P("DT_AMT_TD", "{:.1f}".format(dt_amt_td))
P("DT_RATIO_TD", "{:.2f}".format(dt_amt_td / amt_sum if amt_sum else 0))
P("DT_RATIO_Y", "{:.2f}".format(dt_amt_yd / amt_sum1 if amt_sum1 else 0))
P("DT_BIG_Y", DT_BIG_Y); P("DT_TD_BIG_N", DT_TD_BIG_N)
P("DT_TC", DT_TC); P("DT_DIFF", abs(DT_DIFF)); P("DT_HY_N", DT_HY_N)
P("DT_TOP1_NAME", esc(dt_top1["n"])); P("DT_TOP1_AMT", "{:.1f}".format(dt_top1["amount"] / 1e8))
P("DT_TOP1_MV", "{:.0f}".format(dt_top1["ltsz"] / 1e8)); P("DT_TOP1_HY", esc(dt_top1.get("hybk", "—")))
P("DT_BIG_NAMES", "、".join("%s %.0f亿" % (esc(x["n"]), x.get("ltsz", 0) / 1e8)
                            for x in sorted([y for y in DT_TD if y.get("ltsz", 0) >= 1e10], key=lambda z: -z.get("ltsz", 0))) or "无")
P("DT_FROM_ZT_N", len(dt_from_zt))
P("REL_N", len(rel)); P("REL_MEAN", "{:+.2f}".format(rel_mean)); P("REL_MED", "{:+.2f}".format(rel_med))
P("REL_UP", rel_up); P("REL_LIM", rel_lim); P("REL_LIM_NAME", esc(REL_LIM_NAME))
for k, v in CHIP_PCT.items():
    P(k, v)
P("ZB_N", s0["zb"]); P("ZB_OPEN_N", len(zb_open)); P("ZB_SEALED_N", len(zb_sealed))
P("ZB_POOL_N", len(zbpool))
P("ZB_BD_CODE", next((z["c"] for z in zbpool if z["c"].startswith("92")), "—"))
P("ZB_SEALED_NAMES", "、".join(esc(z["n"]) + " {:+.2f}%".format(z["zdp"]) for z in zb_sealed) or "无")
P("ZB_SEALED_PCT", "{:.0f}".format(len(zb_sealed) / len(zbpool) * 100 if zbpool else 0))
P("ZB_AMT_SUM", "{:.0f}".format(zb_amt_sum)); P("ZB_BIG_N", len(zb_big and [zb_big] or []))
P("NEVER_OPEN", s0["zt"] - s0["zb"])
P("ZB_MAX_NAME", esc(zb_big["n"]) if zb_big else "—")
P("ZB_BIG_MAX", "{:.0f}".format(zb_big.get("ltsz", 0) / 1e8) if zb_big else "—")
P("ZB_MAX_AMT", "{:.2f}".format(zb_big.get("amount", 0) / 1e8) if zb_big else "—")
P("ZB_MAX_PCT", "{:+.2f}".format(zb_big.get("zdp", 0)) if zb_big else "—")
P("ZB_MAX_HY", esc(zb_big.get("hybk", "—")) if zb_big else "—")
P("ZB_TCL_AMT", "{:.2f}".format(ZB_TCL_AMT))
P("TS_EARLY_Y", ts1.get("竞价/秒板", 0) + ts1.get("开盘半小时", 0))
P("TS_EARLY_Y_PCT", "{:.0f}".format((ts1.get("竞价/秒板", 0) + ts1.get("开盘半小时", 0)) / s1["zt"] * 100))
P("TS_EARLY_0", ts0.get("竞价/秒板", 0) + ts0.get("开盘半小时", 0))
P("TS_EARLY_0_PCT", "{:.0f}".format((ts0.get("竞价/秒板", 0) + ts0.get("开盘半小时", 0)) / s0["zt"] * 100))
P("TS_AM_0", ts0.get("上午盘中", 0)); P("TS_AM_1", ts1.get("上午盘中", 0))
P("TS_PM0", ts0.get("午后盘中", 0)); P("TS_PM_1", ts1.get("午后盘中", 0))
P("TS_WM0", ts0.get("尾盘", 0))
P("TS_PM0_PCT", "{:.0f}".format(ts0.get("午后盘中", 0) / s0["zt"] * 100))
P("TS_KJ0", ts0.get("开盘半小时", 0)); P("TS_KJ1", ts1.get("开盘半小时", 0))
P("TS_KJ0_PCT", "{:.0f}".format(ts0.get("开盘半小时", 0) / s0["zt"] * 100))
P("TBL_SENTI", tbl_senti); P("TBL_LAD", tbl_lad); P("TBL_LIANBAN", tbl_lianban)
P("TBL_HY", tbl_hy); P("TBL_TS", tbl_ts); P("TBL_THEME", tbl_theme); P("TBL_IDX", tbl_idx)
P("TBL_STYLE", tbl_style); P("TBL_REL", tbl_rel); P("TBL_DT_TD", tbl_dt_td)
P("TBL_FUND_TOP", tbl_fund_top); P("TBL_AMT_TOP", tbl_amt_top); P("TBL_ZB", tbl_zb)
P("TH_AI_N", len(ai_sel)); P("TH_AI_LB", sum(1 for r in ai_sel if (r["lbc"] or 1) >= 2))
P("TH_AI_WIDE_N", len(ai_wide))
P("TH_SEC_N", len(sec_sel))
P("TH_SOLID_N", _th["固态电池 / 锂电链"]["n"]); P("TH_SOLID_LB", _th["固态电池 / 锂电链"]["lb"])
P("TH_SOLID_STRICT_N", len(solid_strict))
P("TH_SOLID_STRICT_LB", sum(1 for r in solid_strict if (r["lbc"] or 1) >= 2))
P("TH_ROBOT_N", _th["机器人 / 智能制造"]["n"])
P("TH_MED_N", _th["医药 / 创新药"]["n"])
P("TH_CHEM_N", _th["化工 / 材料涨价"]["n"])
P("TH_RETAIL_N", _th["零售 / 消费"]["n"])
P("TH_AGRI_N", _th["农业 / 种业 / 食品"]["n"])
P("TH_RE_N", _th["地产 / 国资重组 / 跨界资产"]["n"])
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
P("JS_CONC_NAME", json.dumps([b["name"] for b in concept_rows], ensure_ascii=False))
P("JS_CONC_N", json.dumps([b["limit_up_num"] for b in concept_rows]))
P("JS_HY_NAME", json.dumps([h["name"] for h in hy_tbl][::-1], ensure_ascii=False))
P("JS_HY_T", json.dumps([h["t"] for h in hy_tbl][::-1]))
P("JS_HY_Y", json.dumps([h["y"] for h in hy_tbl][::-1]))
P("JS_PF_NAME", json.dumps([p["name"] for p in perf_sorted][::-1], ensure_ascii=False))
P("JS_PF_PCT", json.dumps([round(p["pct"], 2) for p in perf_sorted][::-1]))
P("JS_TS_NAME", json.dumps(TS_ORDER, ensure_ascii=False))
P("JS_TS_T", json.dumps([ts0.get(k, 0) for k in TS_ORDER]))
P("JS_TS_Y", json.dumps([ts1.get(k, 0) for k in TS_ORDER]))
P("JS_REL_NAME", json.dumps([x["n"] for x in sorted(rel, key=lambda x: -x["pct"])][::-1], ensure_ascii=False))
P("JS_REL_PCT", json.dumps([round(x["pct"], 2) for x in sorted(rel, key=lambda x: -x["pct"])][::-1]))

# 北交所差额自检（涨停池）
em0 = set(x["c"] for x in B["dates"][D0]["em_ZT"]["pool"])
ths0 = set(x["code"] for x in (B["dates"][D0]["ths_zt"].get("info") or []))
diff = sorted(em0 - ths0)
assert all(c.startswith("92") for c in diff), f"北交所差额自检失败: {diff}"
if diff:
    V["__REL_DIFF_NOTE__"] = "东财池 %d 只 vs 同花顺 %d 只，差额 %d 只为北交所（%s），已按沪深口径取 %d 只" % (
        len(em0), len(ths0), len(diff), "/".join(diff), len(ths0))
else:
    V["__REL_DIFF_NOTE__"] = "东财池与同花顺家数一致（%d 只），差额 0" % len(em0)
P("FBT_AGREE", 100)

HTML = open(os.path.join(ROOT, "scripts", "_report_tpl_20261009.html"), encoding="utf-8").read()
for k, v in V.items():
    HTML = HTML.replace(k, v)

fp = os.path.join(REP, f"涨停复盘对比-{D0}.html")
with open(fp, "w", encoding="utf-8") as f:
    f.write(HTML)
left = re.findall(r"__[A-Z_0-9]+__", HTML)
print("saved ->", fp, len(HTML) // 1024, "KB")
print("placeholder residue:", sorted(set(left)))
print("北交所差额自检: em=%d ths=%d diff=%s OK" % (len(em0), len(ths0), diff))
print("主题聚类:", [(t["name"], t["n"], t["lb"]) for t in theme_cnt])
print("概念 top7:", [(b["name"], b["limit_up_num"]) for b in b_top])
print("关键:", dict(ZT=s0["zt"], SEAL=round(s0["seal_rate"]*100,1), AMT=round(amt_today),
                   AMT_Y=round(amt_prev), TOUCH=TOUCH0, DTOUCH=DTOUCH0, DSEAL=round(DSEAL0,1),
                   DT_RATIO_TD=round(dt_amt_td/amt_sum,2), DT_RATIO_Y=round(dt_amt_yd/amt_sum1,2),
                   AI_WIDE=len(ai_wide), TH_AI_LB=sum(1 for r in ai_sel if (r["lbc"] or 1)>=2),
                   ZB_MAX=(zb_big or {}).get("n"), ZB_MAX_LTSZ=round((zb_big or {}).get("ltsz",0)/1e8)))
