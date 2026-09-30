# -*- coding: utf-8 -*-
"""涨停复盘报告 20260930 vs 20260929（国庆长假前最后一个交易日 / 高低切换 / 权重护盘·科技杀跌）

用法：python zt_report_20260930.py 20260930
输入：out/zt_stats_20260930.json、out/zt_review_20260930.json、out/zt_review_20260929.json
     昨日跌停池明细 out/_dt0929.json、今日跌停池明细 out/_dt0930.json（东财 getTopicDTPool，sort=fund:asc）
     昨日跌停股今日行情：腾讯快照 qt.gtimg.cn（脚本内实时抓取）
输出：reports/涨停复盘对比-20260930.html
"""
import json, os, sys, collections, html, re, urllib.request
from statistics import mean, median

ROOT = os.environ.get("ZT_ROOT") or os.getcwd()
OUT = os.path.join(ROOT, "out")
REP = os.path.join(ROOT, "reports")
os.makedirs(REP, exist_ok=True)

D0 = sys.argv[1] if len(sys.argv) > 1 else "20260930"
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
DSEAL0 = B["dates"][D0]["ths_zt"]["limit_down_count"]["today"]["rate"] * 100
DSEAL1 = B["dates"][D1]["ths_zt"]["limit_down_count"]["today"]["rate"] * 100
DTOUCH2 = 77  # 09-28 触及跌停家数（09-29 报告已核）

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
    ("医药：创新药 / CRO / 疫苗", ["创新药", "CRO", "疫苗", "单抗", "细胞", "血液制品", "抗感染", "肿瘤", "基因检测", "测序", "医药"]),
    ("机器人 / 精密零部件", ["机器人", "具身", "减速器", "轴承", "线性驱动", "关节"]),
    ("固态电池 / 锂电链", ["固态电池", "钠离子电池", "锂电", "复合集流体", "铝塑膜", "电池"]),
    ("PCB / 覆铜板 / 元件链", ["PCB", "覆铜板", "HDI", "封装基板", "高频通讯", "AI服务器电源"]),
    ("染料 / 化工涨价", ["染料", "颜料", "吡啶", "中间体", "精细化", "光刻胶"]),
    ("地产 / 物业", ["房地产开发", "物业管理", "房地产", "代建", "旧改"]),
    ("传媒出版 / AI应用", ["出版", "漫剧", "短剧", "传媒", "AI应用", "数字阅读", "财经新媒体"]),
    ("电力 / 绿电", ["绿色电力", "风电", "热电", "光伏", "储能", "供热"]),
    ("农业 / 食品饮料", ["种业", "转基因", "乳业", "乳品", "白酒", "黄酒", "益生菌", "乳酸菌"]),
]
theme_cnt = []
for nm, kws in THEMES:
    hit = [r for r in r0 if any(k in (r["reason"] or "") for k in kws)]
    lb = sum(1 for r in hit if (r["lbc"] or 1) >= 2)
    theme_cnt.append({"name": nm, "n": len(hit), "lb": lb,
                      "stocks": [r["name"] + "(" + str(r["lbc"] or 1) + "板)" for r in
                                 sorted(hit, key=lambda x: (-(x["lbc"] or 0), -(x["fund"] or 0)))][:8]})
theme_cnt.sort(key=lambda x: (-x["n"], x["name"]))
_th = {t["name"]: t for t in theme_cnt}

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
GAP = m_l - m_s

# 昨涨停 -> 今跌停
DT_TD = json.load(open(os.path.join(OUT, f"_dt{D0[4:]}.json"), encoding="utf-8"))["data"]["pool"]
DT_YD = json.load(open(os.path.join(OUT, f"_dt{D1[4:]}.json"), encoding="utf-8"))["data"]["pool"]
r1_set = {x["code"] for x in r1}
dt_from_zt = [x for x in DT_TD if x["c"] in r1_set]
perf_dt = [p for p in perf if p["pct"] is not None and p["pct"] <= -9.8]
dt_amt_td = sum(x.get("amount", 0) for x in DT_TD) / 1e8
dt_amt_yd = sum(x.get("amount", 0) for x in DT_YD) / 1e8

# 昨日跌停池今日表现（腾讯实时快照）
_syms = []
for c in DT_YD:
    p = "bj" if c["c"].startswith(("43", "83", "87", "92")) else ("sh" if c["c"].startswith(("6", "5", "9")) else "sz")
    _syms.append(p + c["c"])
_px = {}
try:
    _o = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    _raw = _o.open("https://qt.gtimg.cn/q=" + ",".join(_syms), timeout=20).read().decode("gbk", "ignore")
    for _l in _raw.strip().split(";"):
        if "=" not in _l:
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

# ================= 七、封板节奏与成交结构 =================
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

zbpool = (B["dates"][D0].get("em_ZB") or {}).get("pool") or []


def is_limit(z):
    th = 19.8 if z["c"].startswith(("30", "68")) else 9.8
    return z["zdp"] >= th


zb_sealed = [z for z in zbpool if is_limit(z)]
zb_open = [z for z in zbpool if not is_limit(z)]
tbl_zb = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td class='{4}'>{5:+.2f}%</td><td>{6:.2f}亿</td><td>{7:.0f}亿</td></tr>".format(
        esc(z["n"]), z["c"], hhmm(z["fbt"]), esc(z["hybk"]), "up" if z["zdp"] >= 0 else "down",
        z["zdp"], z["amount"] / 1e8, z["ltsz"] / 1e8)
    for z in sorted(zb_open, key=lambda x: x["fbt"]))
zb_big = [z for z in zbpool if z["ltsz"] >= 1e10]

tbl_lianban = "".join(
    "<tr><td>{0}板</td><td>{1}</td><td class='hl'>{2}</td><td>{3}</td><td>{4:.2f}亿</td><td>{5:.2f}亿</td><td>{6:.1f}%</td>"
    "<td>{7}</td><td style='text-align:left;color:#4b5563'>{8}</td></tr>".format(
        r["lbc"], r["code"], esc(r["name"]), (r["fbt"][:5] if r["fbt"] else "—"),
        (r["fund"] or 0) / 1e8, (r["amount"] or 0) / 1e8, (r["turnover"] or 0), esc(r["hybk"]), esc(r["reason"]))
    for r in lb_all)
tbl_hua = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td>{2}板</td><td>{3}</td><td style='text-align:left;color:#4b5563'>{4}</td></tr>".format(
        esc(x["name"]), x["code"], (x["lbc"] or 1), esc(x["hybk"]), esc(x["reason"]))
    for x in hua)
tbl_dt_td = "".join(
    "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3:.2f}亿</td><td>{4:.0f}亿</td></tr>".format(
        x["c"], esc(x["n"]), esc(x["hybk"]), x["amount"] / 1e8, x["ltsz"] / 1e8)
    for x in sorted(DT_TD, key=lambda x: -x["amount"]))
tbl_dt_from_zt = "".join(
    "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3:.2f}亿</td><td>{4:.0f}亿</td></tr>".format(
        x["c"], esc(x["n"]), esc(x["hybk"]), x["amount"] / 1e8, x["ltsz"] / 1e8)
    for x in sorted(dt_from_zt, key=lambda x: -x["amount"]))
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
        ("{:.1f}".format(days[2][k] - days[1][k]) if isinstance(days[2][k], float) else "{:+d}".format(days[2][k] - days[1][k])))
    for lab, k in [("涨停家数", "zt"), ("炸板家数", "zb"), ("封板率(%)", "seal"), ("跌停家数", "dt")])

tbl_lad = "".join(
    "<tr><td>{0} 板</td><td>{1}</td><td class='hl'>{2}</td><td class='{3}'>{4:+d}</td></tr>".format(
        i, lad1.get(i, 0), lad0.get(i, 0),
        "up" if lad0.get(i, 0) - lad1.get(i, 0) > 0 else ("down" if lad0.get(i, 0) - lad1.get(i, 0) < 0 else "mut"),
        lad0.get(i, 0) - lad1.get(i, 0))
    for i in range(lad_max, 0, -1))

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
P("D0_FULL", f"{D0[:4]}-{D0[4:6]}-{D0[6:]}")
P("ZT", s0["zt"]); P("ZT_Y", s1["zt"]); P("ZT_D", "{:+d}".format(s0["zt"] - s1["zt"]))
P("ZB", s0["zb"]); P("ZB_Y", s1["zb"]); P("ZB_D", "{:+d}".format(s0["zb"] - s1["zb"]))
P("DT", s0["dt"]); P("DT_Y", s1["dt"]); P("DT_D", "{:+d}".format(s0["dt"] - s1["dt"]))
P("SEAL", "{:.1f}".format(s0["seal_rate"] * 100))
P("SEAL_Y", "{:.1f}".format(s1["seal_rate"] * 100))
P("SEAL_D", "{:+.1f}".format((s0["seal_rate"] - s1["seal_rate"]) * 100))
P("TOUCH", TOUCH0); P("TOUCH_Y", TOUCH1); P("TOUCH_D", "{:+d}".format(TOUCH0 - TOUCH1))
P("DTOUCH", DTOUCH0); P("DTOUCH_Y", DTOUCH1); P("DTOUCH_D", "{:+d}".format(DTOUCH0 - DTOUCH1))
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
P("KC_PCT", "{:+.2f}".format(ixr.get("科创50", {}).get("pct", 0)))
P("SH50_PCT", "{:+.2f}".format(ixr.get("上证50", {}).get("pct", 0)))
P("HS300_PCT", "{:+.2f}".format(ixr.get("沪深300", {}).get("pct", 0)))
P("GZ2000_PCT", "{:+.2f}".format(ixr.get("国证2000", {}).get("pct", 0)))
P("ZZ1000_PCT", "{:+.2f}".format(ixr.get("中证1000", {}).get("pct", 0)))
P("SH_PCT", "{:+.2f}".format(ixr.get("上证指数", {}).get("pct", 0)))
P("KC_AMT", "{:,.0f}".format(ixr.get("科创50", {}).get("amt", 0)))
P("SH50_AMT", "{:,.0f}".format(ixr.get("上证50", {}).get("amt", 0)))
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
P("FUND_SUM", "{:.1f}".format(fund_sum)); P("FUND_SUM_Y", "{:.1f}".format(fund_sum1))
P("FUND_SUM_PCT", "{:+.1f}".format((fund_sum / fund_sum1 - 1) * 100 if fund_sum1 else 0))
P("FUND_MED", "{:.2f}".format(fund_med)); P("FUND_MED_Y", "{:.2f}".format(fund_med1))
P("FUND_MED_PCT", "{:+.1f}".format((fund_med / fund_med1 - 1) * 100 if fund_med1 else 0))
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
P("HY_YWFW", hy1.get("医疗服务", 0)); P("HY_YWFW0", hy0.get("医疗服务", 0))
P("HY_SWZP", hy1.get("生物制品", 0)); P("HY_SWZP0", hy0.get("生物制品", 0))
P("HY_HXZY", hy1.get("化学制药", 0)); P("HY_HXZY0", hy0.get("化学制药", 0))
P("HY_TYSB", hy1.get("通用设备", 0)); P("HY_TYSB0", hy0.get("通用设备", 0))
P("HY_ZDHS", hy1.get("自动化设", 0)); P("HY_ZDHS0", hy0.get("自动化设", 0))
P("HY_HXZP", hy1.get("化学制品", 0)); P("HY_HXZP0", hy0.get("化学制品", 0))
P("HY_DC", hy1.get("电池", 0)); P("HY_DC0", hy0.get("电池", 0))
P("HY_QCLB", hy1.get("汽车零部", 0)); P("HY_QCLB0", hy0.get("汽车零部", 0))
P("HY_CB", hy1.get("出版", 0)); P("HY_CB0", hy0.get("出版", 0))
P("DT_YD_N", s1["dt"]); P("DT_TD_N", s0["dt"])
P("DT_AMT_YD", "{:.0f}".format(dt_amt_yd)); P("DT_AMT_TD", "{:.1f}".format(dt_amt_td))
P("DT_FROM_ZT_N", len(dt_from_zt))
P("DT_FROM_ZT_NAMES", "、".join(esc(x["n"]) for x in dt_from_zt))
P("PERF_DT_N", len(perf_dt))
P("REL_N", len(rel)); P("REL_MEAN", "{:+.2f}".format(rel_mean)); P("REL_MED", "{:+.2f}".format(rel_med))
P("REL_UP", rel_up); P("REL_LIM", rel_lim)
P("ZB_N", s0["zb"]); P("ZB_OPEN_N", len(zb_open)); P("ZB_SEALED_N", len(zb_sealed))
P("ZB_BIG_N", len(zb_big))
P("ZB_BIG_MAX", "{:.0f}".format(max(z["ltsz"] for z in zbpool) / 1e8) if zbpool else "—")
P("TS_EARLY_Y", ts1.get("竞价/秒板", 0) + ts1.get("开盘半小时", 0))
P("TS_EARLY_Y_PCT", "{:.0f}".format((ts1.get("竞价/秒板", 0) + ts1.get("开盘半小时", 0)) / s1["zt"] * 100))
P("TS_EARLY_0", ts0.get("竞价/秒板", 0) + ts0.get("开盘半小时", 0))
P("TS_EARLY_0_PCT", "{:.0f}".format((ts0.get("竞价/秒板", 0) + ts0.get("开盘半小时", 0)) / s0["zt"] * 100))
P("TS_AM_0", ts0.get("上午盘中", 0)); P("TS_AM_1", ts1.get("上午盘中", 0))
P("TS_PM0", ts0.get("午后盘中", 0)); P("TS_PM1", ts1.get("午后盘中", 0))
P("TBL_SENTI", tbl_senti); P("TBL_LAD", tbl_lad); P("TBL_LIANBAN", tbl_lianban)
P("TBL_HY", tbl_hy); P("TBL_TS", tbl_ts); P("TBL_THEME", tbl_theme); P("TBL_IDX", tbl_idx)
P("TBL_STYLE", tbl_style); P("TBL_REL", tbl_rel); P("TBL_DT_TD", tbl_dt_td)
P("TBL_DT_FROM_ZT", tbl_dt_from_zt); P("TBL_HUA", tbl_hua)
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
P("JS_REL_NAME", json.dumps([x["n"] for x in sorted(rel, key=lambda x: -x["pct"])][::-1], ensure_ascii=False))
P("JS_REL_PCT", json.dumps([round(x["pct"], 2) for x in sorted(rel, key=lambda x: -x["pct"])][::-1]))
P("JS_STYLE_NAME", json.dumps([x["name"] for x in STYLE_SORTED][::-1], ensure_ascii=False))
P("JS_STYLE_PCT", json.dumps([round(x["pct"], 2) for x in STYLE_SORTED][::-1]))

# 北交所差额自检
em0 = set(x["c"] for x in B["dates"][D0]["em_ZT"]["pool"])
ths0 = set(x["code"] for x in (B["dates"][D0]["ths_zt"].get("info") or []))
diff = sorted(em0 - ths0)
assert all(c.startswith("92") for c in diff), f"北交所差额自检失败: {diff}"
if diff:
    V["__REL_DIFF_NOTE__"] = "东财池 %d 只 vs 同花顺 %d 只，差额 %d 只为北交所（%s），已按沪深口径取 %d 只" % (
        len(em0), len(ths0), len(diff), "/".join(diff), len(ths0))
else:
    V["__REL_DIFF_NOTE__"] = "东财池与同花顺家数一致（%d 只），差额 0" % len(em0)

V["__AMT_TOP_LEAD__"] = "成交额第一的 " + esc(amt_top[0]["name"]) + "（" + "{:.2f}".format((amt_top[0]["amount"] or 0) / 1e8) + " 亿）"
P("TH_MED_N", _th["医药：创新药 / CRO / 疫苗"]["n"]); P("TH_MED_LB", _th["医药：创新药 / CRO / 疫苗"]["lb"])
P("TH_ROBOT_N", _th["机器人 / 精密零部件"]["n"]); P("TH_ROBOT_LB", _th["机器人 / 精密零部件"]["lb"])
P("TH_SOLID_N", _th["固态电池 / 锂电链"]["n"]); P("TH_SOLID_LB", _th["固态电池 / 锂电链"]["lb"])
P("TH_PWR_N", _th["电力 / 绿电"]["n"]); P("TH_FB_N", _th["农业 / 食品饮料"]["n"])

HTML = open(os.path.join(ROOT, "scripts", "_report_tpl_20260930.html"), encoding="utf-8").read()
for k, v in V.items():
    HTML = HTML.replace(k, v)

fp = os.path.join(REP, f"涨停复盘对比-{D0}.html")
with open(fp, "w", encoding="utf-8") as f:
    f.write(HTML)
left = re.findall(r"__[A-Z_0-9]+__", HTML)
print("saved ->", fp, len(HTML) // 1024, "KB")
print("placeholder residue:", sorted(set(left)))
print("北交所差额自检: em=%d ths=%d diff=%s OK" % (len(em0), len(ths0), diff))
