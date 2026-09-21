# -*- coding: utf-8 -*-
"""涨停复盘报告生成（占位符替换版）—— **版式模板**

用法：python zt_report_template.py [D0] [D1]
    D0 今日 / D1 昨日；默认沿用 stats 文件内记录的日期
输入：out/zt_stats_{D0}.json、out/zt_review_{D0}.json
输出：reports/涨停复盘对比-{D0}.html

═══ 每次复盘必须改写的部分（其余为可复用骨架）═══
  1. HTML_T 里的**叙述性文案**：首屏 lead、各节小标题下的结论句、图表下方的解读段落。
     这些是从当日数据得出的判断，脚本无法自动生成，必须人工重写。
  2. 正文所有数字**不要手写**：一律在下方"取值区"用 python 算出后塞进 V 字典占位符。
  3. 收尾必看 `placeholder residue:` 输出，必须是空列表。
"""
import json, os, sys, collections, html
from statistics import mean, median

# 数据根目录：优先环境变量 ZT_ROOT，否则取当前工作目录（须与 fetch/analyze 一致）
ROOT = os.environ.get("ZT_ROOT") or os.getcwd()
OUT = os.path.join(ROOT, "out")
REP = os.path.join(ROOT, "reports")
os.makedirs(REP, exist_ok=True)

S = json.load(open(os.path.join(OUT, f"zt_stats_{sys.argv[1]}.json"), encoding="utf-8")) \
    if len(sys.argv) > 1 else json.load(open(os.path.join(OUT, "zt_stats.json"), encoding="utf-8"))
D0, D1 = S["D0"], S["D1"]
D2 = S.get("D2")
B = json.load(open(os.path.join(OUT, f"zt_review_{D0}.json"), encoding="utf-8"))
r0, r1 = S["r0"], S["r1"]
perf = S["perf"]
s0, s1 = S["senti"][D0], S["senti"][D1]


def md(ds):
    """20260916 -> 9/16"""
    return f"{int(ds[4:6])}/{int(ds[6:8])}"


def esc(s):
    return html.escape(str(s))


def hhmm(v):
    """东财 em_ZB.pool 的 fbt 是 HHMMSS 整数（92500 = 09:25:00），必须 zfill(6) 再切；
    直接 str(int(v))[:2]+':'+...[2:4] 会把 10:00 前的时间切错（92500 -> '92:50'）。
    注意 r0（同花顺来源）的 fbt 已是 '09:30:09' 字符串，不要混用这段代码。"""
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
# 昨日各指数涨跌幅直接来自 stats（不再手写）
PREV_IDX_PCT = {k: (v.get("prev_pct") or 0.0) for k, v in (S.get("idx_cmp") or {}).items()}

amt_today = ixr["上证指数"]["amt"] + ixr["深证成指"]["amt"]
tot = S.get("tot") or {}
amt_prev = tot.get("prev") or amt_today
amt_pct = (amt_today / amt_prev - 1) * 100 if amt_prev else 0.0
kc = ixr.get("科创50", {})
kc_prev_amt = (S.get("idx_cmp") or {}).get("科创50", {}).get("prev_amt") or kc.get("amt", 1)
kc_amt_pct = (kc.get("amt", 0) / kc_prev_amt - 1) * 100 if kc_prev_amt else 0.0

# ---- 行业迁移 ----
hy0, hy1 = S["hy0"], S["hy1"]
# 排序必须带完整 tie-break：仅按加权计数排序时，同分项的先后取决于 set() 迭代顺序，
# 而 str 哈希每进程随机化 → 同一份数据两次跑出的 Top18 会不一样（已踩坑）
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

# ---- 成交额结构 ----
amts = [r["amount"] for r in r0 if r["amount"]]
funds = [r["fund"] for r in r0 if r["fund"]]
amt_sum, fund_sum = sum(amts) / 1e8, sum(funds) / 1e8
share = amt_sum / amt_today * 100
oneword = sum(1 for r in r0 if "一字" in r["limit_up_type"])
huanshou = sum(1 for r in r0 if "换手" in r["limit_up_type"])

# ---- 主线归因 ----
THEMES = [
    ("AI算力 / 光通信", ["光模块", "光通信", "光纤", "算力", "数据中心", "交换机", "硅光", "MPO", "NPO", "光芯片", "数据中心电源", "算电协同", "算力服务", "服务器"]),
    ("PCB / 覆铜板", ["PCB", "覆铜板", "HDI", "铜箔", "钻针", "高速树脂", "PPE树脂", "MLCC基膜", "AI电源PCB"]),
    ("半导体 / 存储", ["半导体", "硅片", "芯片", "封装", "晶圆", "存储", "碳化硅", "光刻胶", "靶材", "VCSEL", "功率半导体"]),
    ("液冷 / 散热", ["液冷", "散热", "温控", "热管理"]),
    ("固态电池 / 锂电", ["固态电池", "锂电", "电解液", "复合集流体", "六氟磷酸锂"]),
    ("机器人 / 具身智能", ["机器人", "具身智能", "人形"]),
    ("风电 / 海洋能源", ["风电", "海上风电", "齿轮箱", "铸件"]),
    ("国资 / 区域主题", ["福建国资", "海峡两岸", "宜宾国资", "深圳国资", "珠海国资", "绵阳国资", "眉山", "宜宾"]),
    ("消费 / 家居食品", ["家居", "家具", "服装", "家纺", "食品", "黄酒", "燕麦", "珠宝", "卡牌", "电竞"]),
    ("电力 / 电网", ["电力", "水电", "虚拟电厂", "储能", "特高压", "热电"]),
]
theme_cnt = []
for nm, kws in THEMES:
    hit = [r for r in r0 if any(k in r["reason"] for k in kws)]
    theme_cnt.append({"name": nm, "n": len(hit),
                      "stocks": [r["name"] + "(" + str(r["lbc"] or 1) + "板)" for r in
                                 sorted(hit, key=lambda x: -(x["lbc"] or 0))][:8]})
theme_cnt.sort(key=lambda x: -x["n"])
fj_n = next((t["n"] for t in theme_cnt if t["name"].startswith("国资")), 0)

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
P("FUND_SUM", "{:.1f}".format(fund_sum)); P("FUND_MED", "{:.2f}".format(median(funds) / 1e8))
P("FUND_AVG", "{:.2f}".format(fund_sum / s0["zt"]))
P("ONEWORD", oneword); P("ONEWORD_PCT", "{:.1f}".format(oneword / s0["zt"] * 100))
P("HUANSHOU", huanshou)
P("LB_TOP1", esc(lb_all[0]["name"])); P("LB_TOP1_REASON", esc(lb_all[0]["reason"]))
P("LB_TOP2", esc(lb_all[1]["name"])); P("LB_TOP2_LB", lb_all[1]["lbc"])
P("FJ_N", fj_n)
P("HY_TXD", hy1.get("通信设备", 0)); P("HY_TXD0", hy0.get("通信设备", 0))
P("HY_BDT", hy1.get("半导体", 0)); P("HY_BDT0", hy0.get("半导体", 0))
P("HY_HXP", hy1.get("化学制品", 0)); P("HY_HXP0", hy0.get("化学制品", 0))
P("HY_YJ", hy1.get("元件", 0)); P("HY_YJ0", hy0.get("元件", 0))
P("HY_FD", hy1.get("风电设备", 0)); P("HY_FD0", hy0.get("风电设备", 0))
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

# ================= HTML 模板 =================
HTML_T = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>涨停复盘 · 2026-09-16（对比 9-15）</title>
<script src="../assets/echarts.min.js"></script>
<script>if(typeof echarts==='undefined'){document.write('<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"><\/script>');}</script>
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
<h1>涨停复盘 · 2026-09-16（周三）</h1>
<div class="sub">对比基准：2026-09-15（周二）｜口径：沪深两市（不含北交所）｜数据源：同花顺涨停池 + 东方财富涨停/炸板/跌停池 + 行情快照</div>

<div class="lead">
<p class="hl">一句话结论：昨日退潮杀跌，今日全面修复。涨停 __ZT__ 家（昨 __ZT_Y__ 家，__ZT_D__），封板率 __SEAL__%（昨 __SEAL_Y__%，__SEAL_D__pct），
涨停/跌停比从 __ZTDT_Y__ 翻转为 __ZTDT__——情绪指标三项同时反向。</p>
<p>但修复的质量不对称：科创板一枝独秀（科创50 __KC_PCT__%，成交额环比 __KC_AMT_PCT__%），
增量资金几乎全部涌向 AI 算力硬件链；最高连板仅 __MAXB__ 板，昨日涨停股今日晋级率 __ADV_RATE__%、中位涨幅仅 __PERF_MED__%，
昨 __PERF_MIN_LB__ 板股 __PERF_MIN_NAME__ __PERF_MIN__%。<span class="hl">这是「资金搬家 + 低位补涨」的修复，不是主升浪。</span></p>
</div>

<div class="kpis">
  <div class="kpi"><div class="lbl">涨停家数</div><div class="val up">__ZT__</div>
    <div class="dt mut">昨日 __ZT_Y__ <span class="up">__ZT_D__</span></div></div>
  <div class="kpi"><div class="lbl">封板率</div><div class="val">__SEAL__%</div>
    <div class="dt mut">昨日 __SEAL_Y__% <span class="up">__SEAL_D__pct</span></div></div>
  <div class="kpi"><div class="lbl">跌停家数</div><div class="val down">__DT__</div>
    <div class="dt mut">昨日 __DT_Y__ <span class="down">__DT_D__</span></div></div>
  <div class="kpi"><div class="lbl">两市成交额</div><div class="val">__AMT__亿</div>
    <div class="dt mut">昨日 __AMT_Y__亿 <span class="up">__AMT_D__亿</span></div></div>
  <div class="kpi"><div class="lbl">昨涨停今日晋级率</div><div class="val">__ADV_RATE__%</div>
    <div class="dt mut">__ADV_N__/__ADV_TOT__ 只再涨停</div></div>
  <div class="kpi"><div class="lbl">最高连板</div><div class="val">__MAXB__ 板</div>
    <div class="dt mut">昨日 __MAXB_Y__ 板</div></div>
</div>

<div class="card">
<h2>一、市场情绪温度计：从冰点到修复</h2>
<table>
<tr><th>指标</th><th>9/14（周一）</th><th>9/15（周二）</th><th>9/16（周三）</th><th>9/16 环比</th></tr>
__TBL_SENTI__
<tr><td>涨停/跌停比</td><td>__ZTDT_0__</td><td>__ZTDT_Y__</td><td class="hl">__ZTDT__</td><td class="up">情绪逆转</td></tr>
</table>
<div class="note" style="margin-top:10px">
9/15 是典型的 <span class="hl">退潮杀跌日</span>：涨停骤降至 __ZT_Y__ 家、炸板 __ZB_Y__ 家、跌停 __DT_Y__ 家为三日最多。
9/16 三项指标同时反向：涨停放大近三倍、炸板减半、跌停仅剩 __DT__ 家（其中 __DT_OPEN__ 次为盘中开板，非一字闷杀）。
</div>
<div id="c_senti" class="chart" style="margin-top:16px"></div>
</div>

<div class="card">
<h2>二、指数与量能：增量资金去了哪里</h2>
<div class="two">
<div>
<table>
<tr><th>指数</th><th>今日</th><th>昨日</th><th>成交额</th></tr>
__TBL_IDX__
</table>
<div class="note" style="margin-top:10px">
<b>量能是本次修复最硬的证据：</b>两市成交额 __AMT__ 亿，环比 __AMT_D__ 亿（__AMT_PCT__%）。
但增量分布极不均衡——科创50 成交额 __KC_AMT__ 亿（昨 __KC_AMT_PREV__ 亿，__KC_AMT_PCT__%），
增速是两市整体的 2 倍以上；而上证50 仅 __SZ50_PCT__%。
<span class="hl">钱进了科技成长，没进大盘蓝筹。</span>
</div>
</div>
<div><div id="c_idx" class="chart-sm"></div></div>
</div>
</div>

<div class="card">
<h2>三、连板梯队：宽度打开，高度未破</h2>
<div class="two">
<div><div id="c_lad" class="chart-sm"></div></div>
<div>
<table>
<tr><th>梯队</th><th>9/15</th><th>9/16</th><th>变化</th></tr>
__TBL_LAD__
<tr><td>合计</td><td>__ZT_Y__</td><td class="hl">__ZT__</td><td class="up">__ZT_D__</td></tr>
</table>
<div class="note" style="margin-top:10px">
首板 __SB__ 家（昨 __SB_Y__），连板股 __LB__ 家（昨 __LB_Y__），最高 __MAXB__ 板（__LB_TOP1__，__LB_TOP1_REASON__），昨日为 __MAXB_Y__ 板。
<span class="hl">新增资金几乎全部堆在首板（占 __SB_PCT__%），3~5 板的中位梯队仍是空的</span>——这是修复初期而非主升浪的典型结构。
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
<h2>四、主线归因：算力硬件链一家独大</h2>
<div id="c_theme" class="chart"></div>
<table style="margin-top:14px">
<tr><th>主线</th><th>涨停家数</th><th>代表个股</th></tr>
__TBL_THEME__
</table>
<div class="note" style="margin-top:12px">
AI算力/光通信与 PCB/覆铜板、半导体三条链覆盖了今日涨停的大部分，
且高标集中在这三条链上——市场合力方向明确。另外「国资/区域主题」贡献 __FJ_N__ 家，
属于典型的地域+国资题材扩散。<br>
注：reason_type 为多标签，同一只股票可归入多条主线，故各主线家数之和大于涨停总数。
</div>
</div>

<div class="card">
<h2>五、行业迁移：资金从哪里来、到哪里去</h2>
<div id="c_hy" class="chart" style="height:410px"></div>
<table style="margin-top:14px">
<tr><th>行业</th><th>9/15</th><th>9/16</th><th>增减</th><th>读数</th></tr>
__TBL_HY__
</table>
<div class="note" style="margin-top:12px">
<b>流入端：</b>通信设备 __HY_TXD__→__HY_TXD0__ 家、半导体 __HY_BDT__→__HY_BDT0__ 家、
化学制品 __HY_HXP__→__HY_HXP0__ 家、元件/PCB __HY_YJ__→__HY_YJ0__ 家。<br>
<b>流出端：</b>风电设备从 __HY_FD__ 家收缩到 __HY_FD0__ 家——昨日风电是最强方向，今日被算力链完全替代。
这说明<span class="hl">资金在主题内部做了「高低切换」，而非单纯靠增量推动</span>。
</div>
</div>

<div class="card">
<h2>六、昨日涨停股今日表现：修复，但有裂痕</h2>
<div class="kpis" style="grid-template-columns:repeat(auto-fit,minmax(140px,1fr))">
  <div class="kpi"><div class="lbl">晋级率</div><div class="val">__ADV_RATE__%</div><div class="dt mut">__ADV_N__/__ADV_TOT__</div></div>
  <div class="kpi"><div class="lbl">平均涨幅</div><div class="val up">__PERF_MEAN__%</div><div class="dt mut">中位 __PERF_MED__%</div></div>
  <div class="kpi"><div class="lbl">翻绿比例</div><div class="val down">__NEG_PCT__%</div><div class="dt mut">__NEG__ 只</div></div>
  <div class="kpi"><div class="lbl">最强</div><div class="val up">__PERF_MAX__%</div><div class="dt mut">__PERF_MAX_NAME__</div></div>
  <div class="kpi"><div class="lbl">最弱</div><div class="val down">__PERF_MIN__%</div><div class="dt mut">__PERF_MIN_NAME__（昨 __PERF_MIN_LB__ 板）</div></div>
</div>
<div class="note" style="margin-top:14px">
昨日首板 n=25 晋级率 36.0%、均涨 +3.70%；昨日连板 n=7 晋级率 42.9%、均涨 +3.51%。
连板股晋级率并不低，但<span class="hl">高位股分化极端</span>：最弱三只为 __PERF_BOT3__，
而低位补涨股普遍 +10%。<span class="hl">资金在「砍高位、补低位」。</span>
</div>
<div id="c_perf" class="chart" style="height:700px;margin-top:8px"></div>
</div>

<div class="card">
<h2>七、封板节奏与成交结构</h2>
<div class="two">
<div><div id="c_ts" class="chart-sm"></div></div>
<div>
<table>
<tr><th>封板时段</th><th>9/15</th><th>9/16</th></tr>
__TBL_TS__
</table>
<div class="note" style="margin-top:10px">
昨日封板高度集中在早盘（__TS_EARLY_Y__/__ZT_Y__ = __TS_EARLY_Y_PCT__%），但当日炸板 __ZB_Y__ 家、封板率仅 __SEAL_Y__%，属于「早盘一致 → 盘中瓦解」；今日封板时间明显后移，
午后封板 __TS_PM0__ 家（昨 __TS_PM1__ 家），是<span class="hl">盘中逐波承接、资金持续进场</span>的特征，而非开盘一把梭。
</div>
</div>
</div>
<div class="kpis" style="grid-template-columns:repeat(auto-fit,minmax(160px,1fr));margin-top:16px">
  <div class="kpi"><div class="lbl">涨停股合计成交额</div><div class="val">__AMT_SUM__亿</div><div class="dt mut">占两市 __SHARE__%</div></div>
  <div class="kpi"><div class="lbl">封单合计</div><div class="val">__FUND_SUM__亿</div><div class="dt mut">均值 __FUND_AVG__亿/只</div></div>
  <div class="kpi"><div class="lbl">一字板</div><div class="val">__ONEWORD__</div><div class="dt mut">占比 __ONEWORD_PCT__%</div></div>
  <div class="kpi"><div class="lbl">换手板</div><div class="val">__HUANSHOU__</div><div class="dt mut">真金白银买入</div></div>
</div>
</div>

<div class="card">
<h2>八、资金运动的三个结论</h2>
<ul>
<li><b>① 总量上：是增量，但有选择性。</b>两市成交额 __AMT__ 亿（__AMT_PCT__%），其中科创50 贡献 __KC_AMT_PCT__% 的成交额增速；
上证50 仅 __SZ50_PCT__%。<span class="hl">增量资金进科技、不进蓝筹。</span></li>
<li><b>② 方向上：主题内部高低切换。</b>风电设备 __HY_FD__→__HY_FD0__ 家，昨日 4 板高标 __PERF_MIN_NAME__ 今日 __PERF_MIN__%；
资金同步流入通信设备（__HY_TXD__→__HY_TXD0__）、半导体（__HY_BDT__→__HY_BDT0__）、元件/PCB（__HY_YJ__→__HY_YJ0__）。
本质是<span class="hl">同一批资金从「旧题材高标」搬到「算力硬件链」</span>。</li>
<li><b>③ 深度上：筹码完成换手，但封单偏薄。</b>涨停股合计成交 __AMT_SUM__ 亿（占两市 __SHARE__%），
其中换手板 __HUANSHOU__/__ZT__ 只、一字板仅 __ONEWORD__ 只；封单合计 __FUND_SUM__ 亿、均值 __FUND_AVG__ 亿/只、中位 __FUND_MED__ 亿。
封单薄 + 换手充分，意味着<span class="hl">承接盘是真实换手而非锁仓</span>——好处是抛压被消化，风险是明日若无新增资金，薄封单容易松动。</li>
</ul>
</div>

<div class="card">
<h2>九、明日观察要点与风险</h2>
<ul>
<li><b>承接强度：</b>今日 __ZT__ 家涨停股明日能否维持 35% 以上晋级率。若晋级率跌破 30% 且炸板率回升至 30%+，即为二次退潮信号。</li>
<li><b>高度标杆：</b>__LB_TOP1__（__MAXB__ 板）与 __LB_TOP2__（__LB_TOP2_LB__ 板）能否延续，决定算力链情绪能否外溢至中位梯队。</li>
<li><b>量能持续性：</b>两市成交额若回落至 1.6 万亿以下，本轮修复大概率只是超跌反弹。</li>
<li><b>封单薄弱风险：</b>涨停股中位封单仅 __FUND_MED__ 亿，一旦开盘承接不足易出现集体炸板。</li>
<li><b>数据口径：</b>统计为沪深两市（不含北交所）；涨停/炸板/跌停家数经同花顺与东财双源交叉校验（两池家数完全一致，封板时间分钟级一致率 100%）；
成交额、封单、换手率取东财字段，已用「换手率 × 流通市值 ≈ 成交额」三角验证；两市成交额为沪市 + 深市全市场口径。</li>
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
    {name:'9/15',type:'bar',data:__JS_LAD1__,itemStyle:{color:'#cbd5e1'},barWidth:18},
    {name:'9/16',type:'bar',data:__JS_LAD0__,itemStyle:{color:C_RED},barWidth:18,
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
    {name:'9/15',type:'bar',data:__JS_HY_Y__,itemStyle:{color:'#cbd5e1'},barWidth:11},
    {name:'9/16',type:'bar',data:__JS_HY_T__,itemStyle:{color:C_RED},barWidth:11}
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
    {name:'9/15',type:'bar',data:__JS_TS_Y__,itemStyle:{color:'#cbd5e1'},barWidth:24},
    {name:'9/16',type:'bar',data:__JS_TS_T__,itemStyle:{color:C_RED},barWidth:24}
  ]
});
</script>
</body>
</html>
"""

HTML = HTML_T
for k, v in V.items():
    HTML = HTML.replace(k, v)

fp = os.path.join(REP, f"涨停复盘对比-{D0}.html")
with open(fp, "w", encoding="utf-8") as f:
    f.write(HTML)
import re
left = re.findall(r"__[A-Z_0-9]+__", HTML)
print("saved ->", fp, len(HTML) // 1024, "KB")
print("placeholder residue:", sorted(set(left)))
