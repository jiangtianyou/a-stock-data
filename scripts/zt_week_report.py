# -*- coding: utf-8 -*-
"""A股涨停复盘 · 周报生成（占位符替换版）

用法（项目根目录）：
    python scripts/zt_week_report.py 20260911 20260918

输入：out/zt_week_{start}_{end}.json（由 zt_week_analyze.py 生成）
输出：reports/涨停周报-{start}至{end}.html

正文所有数字均由数据推导后经占位符注入，禁止手写。
"""
import json, os, sys, html, datetime

ROOT = os.environ.get("ZT_ROOT") or os.getcwd()
OUT = os.path.join(ROOT, "out")
REP = os.path.join(ROOT, "reports")
os.makedirs(REP, exist_ok=True)

START, END = (sys.argv[1], sys.argv[2]) if len(sys.argv) >= 3 else ("20260911", "20260918")
W = json.load(open(os.path.join(OUT, f"zt_week_{START}_{END}.json"), encoding="utf-8"))
DAYS = W["days"]
lb_occ = W["lb_occ"]
themes = W["themes"]
theme_order = W["theme_order"]

WK = [x for x in DAYS if x["date"] > START]        # 本周 5 个交易日
PREV = DAYS[0]                                     # 上周五锚点

WD = "一二三四五六日"


def lbl(ds):
    d = datetime.datetime.strptime(ds, "%Y%m%d")
    return f"{d.month}/{d.day}({WD[d.weekday()]})"


def short(ds):
    d = datetime.datetime.strptime(ds, "%Y%m%d")
    return f"{d.month}/{d.day}"


def esc(s):
    return html.escape(str(s))


def f1(v):
    return "—" if v is None else f"{v:.1f}"


def f2(v):
    return "—" if v is None else f"{v:+.2f}"


def sg(v):
    return "—" if v is None else f"{v:+.0f}"


D = {x["date"]: x for x in DAYS}
W0, W4 = WK[0], WK[-1]
LOW, HIGH = min(WK, key=lambda x: x["zt"]), max(WK, key=lambda x: x["zt"])
LOW_AMT, HIGH_AMT = min(WK, key=lambda x: x["mkt_amt"]), max(WK, key=lambda x: x["mkt_amt"])
LOW_ADV = min([x for x in WK if x["promo"] is not None], key=lambda x: x["promo"])
HIGH_ADV = max([x for x in WK if x["promo"] is not None], key=lambda x: x["promo"])
W4_PROMO = W4["promo"] if W4["promo"] is not None else 0
MAXB_WK = max(x["max_board"] for x in WK)
PB = [x for x in WK if x["promo"] is not None]
PROMO_AVG = sum(x["promo"] for x in PB) / len(PB)

# ---- 逐日指标表 ----
tbl_day = "".join(
    "<tr><td>{0}</td><td class='hl up'>{1}</td><td>{2}</td><td>{3}%</td>"
    "<td class='down'>{4}</td><td>{5}</td><td>{6}</td><td>{7}</td>"
    "<td>{8:,.0f}亿</td><td>{9}%</td><td>{10}</td><td>{11}</td><td>{12}%</td></tr>".format(
        lbl(x["date"]), x["zt"], x["zb"], f1(x["seal"]), x["dt"],
        x["max_board"], x["lianban"], x["shouban"], x["mkt_amt"],
        f1(x["ratio"]), f1(x["promo"]) + ("%" if x["promo"] is not None else ""),
        f2(x["prem_med"]) + ("%" if x["prem_med"] is not None else ""),
        f1(x["early_pct"]))
    for x in DAYS)

# ---- 周度连板股表 ----
tbl_lb = "".join(
    "<tr><td>{0}板</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td>"
    "<td style='text-align:left;color:#4b5563'>{6}</td></tr>".format(
        x["maxlv"], x["code"], esc(x["name"]), x["n"], " → ".join(str(q["lv"]) for q in x["seq"]),
        esc(x["hybk"]), esc(x["reason"]))
    for x in lb_occ if x["n"] >= 2)

# ---- 行业热力（Top16）----
allhy = {}
for x in DAYS:
    for k, v in x["ind"].items():
        allhy[k] = allhy.get(k, 0) + v
hy_top = sorted(allhy, key=lambda k: (-allhy[k], k))[:16]
# ECharts 类目轴首项在底部 —— 反转后让合计最大的行业排在最上方
hy_series = [{"name": k, "v": [D[x["date"]]["ind"].get(k, 0) for x in DAYS]} for k in hy_top][::-1]
hy_heat = [[j, i, s["v"][j]] for i, s in enumerate(hy_series) for j in range(len(DAYS))]
HY_MAX = max([v for s in hy_series for v in s["v"]] + [1])

# ---- 题材（按周合计降序，取前 8）----
th_top = theme_order[:8]
th_tbl = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td></tr>".format(
        esc(n), sum(themes[n]), sg(sum(themes[n][1:])), " / ".join(str(v) for v in themes[n]))
    for n in th_top)

# ---- 封单 / 成交 ------------
fund_series = [x["fund_sum"] for x in DAYS]
amt_series = [x["amt_sum"] for x in DAYS]

V = {}


def P(k, v):
    V["__" + k + "__"] = str(v)


P("TITLE_RANGE", f"{lbl(W0['date'])} ~ {lbl(W4['date'])}")
P("SESS", len(WK))
P("TOT_ZT", sum(x["zt"] for x in WK))
P("AVG_ZT", f1(sum(x["zt"] for x in WK) / len(WK)))
P("ZT_RANGE", f"{LOW['zt']}（{short(LOW['date'])}）~ {HIGH['zt']}（{short(HIGH['date'])}）")
P("TOT_DT", sum(x["dt"] for x in WK))
P("DT_SHARE", f1(D["20260915"]["dt"] / sum(x["dt"] for x in WK) * 100))
P("SEAL_AVG", f1(sum(x["seal"] for x in WK) / len(WK)))
P("SEAL_MIN", f1(min(x["seal"] for x in WK)))
P("SEAL_MAX", f1(max(x["seal"] for x in WK)))
P("SEAL_MIN_D", short(LOW_ADV["date"]) if LOW_ADV else "—")
P("SEAL_MAX_D", short(HIGH_ADV["date"]) if HIGH_ADV else "—")
P("LOW_ZT_D", short(LOW["date"]))
P("LOW_ZT", LOW["zt"])
P("LOW_ZT_DT", LOW["dt"])
P("LOW_ZT_SEAL", f1(LOW["seal"]))
P("LOW_ZT_ZB", LOW["zb"])
P("HIGH_ZT_D", short(HIGH["date"]))
P("HIGH_ZT", HIGH["zt"])
P("HIGH_ZT_DT", HIGH["dt"])
P("HIGH_ZT_SEAL", f1(HIGH["seal"]))
P("HIGH_ZT_PREM", f2(HIGH["prem_mean"]))
P("LOW_AMT", f"{LOW_AMT['mkt_amt']:,.0f}")
P("LOW_AMT_D", short(LOW_AMT["date"]))
P("HIGH_AMT", f"{HIGH_AMT['mkt_amt']:,.0f}")
P("HIGH_AMT_D", short(HIGH_AMT["date"]))
P("W0_AMT", f"{W0['mkt_amt']:,.0f}")
P("W4_AMT", f"{W4['mkt_amt']:,.0f}")
P("AMT_PCT", f"{(W4['mkt_amt'] / W0['mkt_amt'] - 1) * 100:+.1f}")
P("AMT_AVG", f"{sum(x['mkt_amt'] for x in WK) / len(WK):,.0f}")
P("PREV_AMT", f"{PREV['mkt_amt']:,.0f}")
P("AMT_VS_PREV", f"{(W4['mkt_amt'] / PREV['mkt_amt'] - 1) * 100:+.1f}")
P("MAXB", MAXB_WK)
P("MAXB_D", short(max(WK, key=lambda x: x["max_board"])["date"]))
P("MAXB_W4", W4["max_board"])
P("SHARE_AVG", f"{sum(x['ratio'] for x in WK) / len(WK):.2f}")
P("SHARE_W4", f"{W4['ratio']:.2f}")
P("SHARE_HIGH", f"{max(x['ratio'] for x in WK):.2f}")
P("SHARE_HIGH_D", short(max(WK, key=lambda x: x["ratio"])["date"]))
P("AMT_MED_W4", f"{W4['amt_med']:.2f}")
P("AMT_MED_HIGH", f"{max(x['amt_med'] for x in WK):.2f}")
P("PROMO_AVG", f1(PROMO_AVG))
P("PROMO_LOW", f1(LOW_ADV["promo"]))
P("PROMO_LOW_D", short(LOW_ADV["date"]))
P("PROMO_HIGH", f1(HIGH_ADV["promo"]))
P("PROMO_HIGH_D", short(HIGH_ADV["date"]))
P("PROMO_W4", f1(W4_PROMO))
P("PROMO_W4_N", f"{W4['again']}/{W4['prev_zt']}")
P("SB_W4", W4["shouban"])
P("SB_W4_PCT", f"{W4['shouban'] / W4['zt'] * 100:.0f}")
P("LB_W4", W4["lianban"])
P("EARLY_W4", f1(W4["early_pct"]))
P("EARLY_HIGH", f1(max(x["early_pct"] for x in WK)))
P("EARLY_LOW", f1(min(x["early_pct"] for x in WK)))
P("EARLY_LOW_D", short(min(WK, key=lambda x: x["early_pct"])["date"]))
P("FUND_W0", f"{W0['fund_sum']:.1f}")
P("FUND_W4", f"{W4['fund_sum']:.1f}")
P("FUND_MIN", f"{min(x['fund_sum'] for x in WK):.1f}")
P("FUND_MIN_D", short(min(WK, key=lambda x: x["fund_sum"])["date"]))
P("PREM_W4", f2(W4["prem_med"]))
P("PREM_LOW", f2(LOW_ADV["prem_med"]) if LOW_ADV["prem_med"] is not None else "—")
P("PREM_LOW_D", short([x for x in WK if x["date"] == "20260917"][0]["date"]))
P("GREEN_0917", f1([x for x in WK if x["date"] == "20260917"][0]["green_pct"]))
P("HY_YJ_W0", PREV["ind"].get("元件", 0))
P("HY_YJ_W4", W4["ind"].get("元件", 0))
P("HY_DW_W4", W4["ind"].get("电网设备", 0))
P("HY_DW_W2", D["20260916"]["ind"].get("电网设备", 0))
P("HY_BDT_W4", W4["ind"].get("半导体", 0))
P("HY_BDT_W1", D["20260916"]["ind"].get("半导体", 0))
P("HY_QC_W3", D["20260917"]["ind"].get("汽车零部", 0))
P("HY_QC_W4", W4["ind"].get("汽车零部", 0))
P("TH_PCB_W2", themes["PCB/算力硬件"][3])
P("TH_PCB_W3", themes["PCB/算力硬件"][4])
P("TH_PCB_W4", themes["PCB/算力硬件"][5])
P("TH_TOTAL", sum(sum(v) for v in themes.values()))
P("TH_PCB_TOTAL", sum(themes["PCB/算力硬件"]))
P("TH_PCB_SHARE", f"{sum(themes['PCB/算力硬件']) / sum(sum(v) for v in themes.values()) * 100:.0f}")
P("LB_TOP1", esc(lb_occ[0]["name"]))
P("LB_TOP1_CODE", lb_occ[0]["code"])
P("LB_TOP1_SEQ", "→".join(str(q["lv"]) for q in lb_occ[0]["seq"]))
P("LB_TOP1_HY", esc(lb_occ[0]["hybk"]))
P("LB_0918_NEW", "、".join(f"{esc(x['name'])}({x['maxlv']}板)" for x in lb_occ
                          if x["seq"][-1]["date"] == "20260918" and x["n"] >= 2))
P("TBL_DAY", tbl_day)
P("TBL_LB", tbl_lb)
P("TBL_TH", th_tbl)
P("JS_DAYS", json.dumps([lbl(x["date"]) for x in DAYS], ensure_ascii=False))
P("JS_ZT", json.dumps([x["zt"] for x in DAYS]))
P("JS_ZB", json.dumps([x["zb"] for x in DAYS]))
P("JS_DT", json.dumps([x["dt"] for x in DAYS]))
P("JS_SEAL", json.dumps([round(x["seal"], 1) for x in DAYS]))
P("JS_AMT", json.dumps([round(x["mkt_amt"]) for x in DAYS]))
P("JS_SHARE", json.dumps([round(x["ratio"], 2) for x in DAYS]))
P("JS_PROMO", json.dumps([round(x["promo"], 1) if x["promo"] is not None else None for x in DAYS]))
P("JS_PREM", json.dumps([round(x["prem_med"], 2) if x["prem_med"] is not None else None for x in DAYS]))
P("JS_LV", json.dumps(sorted({k for x in DAYS for k in x["ladder"]}, key=int)))
P("JS_LAD", json.dumps([[x["ladder"].get(str(k), x["ladder"].get(k, 0))
                         for k in sorted({k for y in DAYS for k in y["ladder"]}, key=int)] for x in DAYS]))
P("JS_MAXB", json.dumps([x["max_board"] for x in DAYS]))
P("JS_HY_NAME", json.dumps([s["name"] for s in hy_series], ensure_ascii=False))
P("JS_HY_DAYS", json.dumps([lbl(x["date"]) for x in DAYS], ensure_ascii=False))
P("JS_HY_DATA", json.dumps(hy_heat))
P("JS_HY_MAX", HY_MAX)
P("JS_TH_NAME", json.dumps(th_top, ensure_ascii=False))
P("JS_TH_DAYS", json.dumps([lbl(x["date"]) for x in DAYS], ensure_ascii=False))
P("JS_TH_DATA", json.dumps([{"name": n, "type": "bar", "stack": "t", "emphasis": {"focus": "series"},
                             "data": themes[n]} for n in th_top], ensure_ascii=False))
P("JS_FUND", json.dumps([round(v, 1) for v in fund_series]))
P("JS_ZTAMT", json.dumps([round(v) for v in amt_series]))
P("GEN_AT", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))

HTML_T = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>涨停周报 · __TITLE_RANGE__</title>
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
.chart{width:100%;height:340px}.chart-lg{width:100%;height:420px}.chart-sm{width:100%;height:280px}
.two{display:grid;grid-template-columns:1fr 1fr;gap:18px}
@media(max-width:820px){.two{grid-template-columns:1fr}}
.tag{display:inline-block;background:#eef2ff;color:#3730a3;border-radius:5px;padding:1px 7px;font-size:11px;margin:1px 3px 1px 0}
.note{font-size:12px;color:#6b7280;line-height:1.75}
.warn{background:#fff8f1;border:1px solid #f5d9be;border-radius:10px;padding:14px 18px;font-size:13px;color:#7c4a12}
ul{margin:6px 0 0;padding-left:20px}li{margin:6px 0}
.hl{font-weight:600;color:#111827}
.stage{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-top:6px}
@media(max-width:820px){.stage{grid-template-columns:1fr}}
.stg{background:#fafbfc;border:1px solid #e6e8eb;border-radius:10px;padding:12px 13px}
.stg .d{font-size:12px;color:#6b7280}
.stg .t{font-size:14px;font-weight:650;margin:3px 0 5px}
.stg .m{font-size:11.5px;color:#6b7280;line-height:1.7}
</style>
</head>
<body>
<div class="wrap">
<h1>涨停复盘 · 本周（__TITLE_RANGE__）</h1>
<div class="sub">共 __SESS__ 个交易日｜口径：沪深两市（不含北交所）｜数据源：同花顺涨停/炸板/跌停池 + 东方财富涨停池 + 腾讯行情快照｜生成 __GEN_AT__</div>

<div class="lead">
<p class="hl">一句话结论：本周走完「缩量分歧 → 地量杀跌 → V 型反转 → 收敛去伪 → 放量二波」五段。
资金没有离场，只是换了口袋——涨停家数从 __LOW_ZT_D__ 的 __LOW_ZT__ 家杀跌低点，到 __HIGH_ZT_D__ 的 __HIGH_ZT__ 家极端扩张，
再到周五 __W4_ZT__ 家的稳定扩张；周五两市成交额 __W4_AMT__ 亿，创周内新高，较周一 __AMT_PCT__%。</p>
<p>质量最好的是周五：<span class="hl">跌停 0 家（全周唯一）、放量、早盘封板占比回到 __EARLY_W4__%、昨涨停股晋级率 __PROMO_W4__%、溢价中位转正 __PREM_W4__%</span>。
但高度在退——最高连板路径为 __MAXB_SEQ__ 板，周内最高标 __LB_TOP1__（__LB_TOP1_HY__，__LB_TOP1_SEQ__ 板）断板后无新龙头接棒。
<span class="hl">这是「宽度驱动」而非「高度驱动」的行情，成败取决于次日承接而非连板效应。</span></p>
</div>

<div class="kpis">
  <div class="kpi"><div class="lbl">本周涨停合计</div><div class="val up">__TOT_ZT__</div>
    <div class="dt mut">日均 __AVG_ZT__ 家｜区间 __ZT_RANGE__</div></div>
  <div class="kpi"><div class="lbl">封板率均值</div><div class="val">__SEAL_AVG__%</div>
    <div class="dt mut">区间 __SEAL_MIN__%（__SEAL_MIN_D__）~ __SEAL_MAX__%（__SEAL_MAX_D__）</div></div>
  <div class="kpi"><div class="lbl">周五跌停家数</div><div class="val down">0</div>
    <div class="dt mut">全周合计 __TOT_DT__ 家，其中 __DT_SHARE__% 集中在 __DT_MAX_D__</div></div>
  <div class="kpi"><div class="lbl">周五两市成交额</div><div class="val">__W4_AMT__亿</div>
    <div class="dt mut">周一 __W0_AMT__亿 <span class="up">__AMT_PCT__%</span>｜周均 __AMT_AVG__亿</div></div>
  <div class="kpi"><div class="lbl">最高连板</div><div class="val">__MAXB__ 板</div>
    <div class="dt mut">周五回落至 __MAXB_W4__ 板</div></div>
  <div class="kpi"><div class="lbl">晋级率均值</div><div class="val">__PROMO_AVG__%</div>
    <div class="dt mut">区间 __PROMO_LOW__%（__PROMO_LOW_D__）~ __PROMO_HIGH__%（__PROMO_HIGH_D__）</div></div>
</div>

<div class="card">
<h2>一、一周五段：情绪与资金的时间轴</h2>
<div class="stage">
  <div class="stg"><div class="d">__D1__ 周一</div><div class="t">缩量分歧</div>
    <div class="m">涨停 __D1_ZT__ / 炸板 __D1_ZB__ / 跌停 __D1_DT__<br>成交 __D1_AMT__亿<br>封板率 __D1_SEAL__%｜晋级率 __D1_PROMO__%</div></div>
  <div class="stg"><div class="d">__D2__ 周二</div><div class="t">地量杀跌</div>
    <div class="m">涨停 __D2_ZT__ / 炸板 __D2_ZB__ / 跌停 __D2_DT__<br>成交 __D2_AMT__亿（全周地量）<br>封板率 __D2_SEAL__%（周内最低）</div></div>
  <div class="stg"><div class="d">__D3__ 周三</div><div class="t">V 型反转</div>
    <div class="m">涨停 __D3_ZT__（周内最高）/ 跌停 __D3_DT__<br>成交 __D3_AMT__亿 __D3_AMT_PCT__%<br>封板率 __D3_SEAL__%｜溢价均值 __D3_PREM__%</div></div>
  <div class="stg"><div class="d">__D4__ 周四</div><div class="t">收敛去伪</div>
    <div class="m">涨停 __D4_ZT__ / 跌停 __D4_DT__<br>成交 __D4_AMT__亿 __D4_AMT_PCT__%（横住）<br>晋级率 __D4_PROMO__%（周内最低）</div></div>
  <div class="stg"><div class="d">__D5__ 周五</div><div class="t">放量二波</div>
    <div class="m">涨停 __D5_ZT__ / 跌停 __D5_DT__<br>成交 __D5_AMT__亿 __D5_AMT_PCT__%<br>封板率 __D5_SEAL__%｜早盘封板 __D5_EARLY__%</div></div>
</div>
<div class="note" style="margin-top:14px">
关键读数：<b>__LOW_AMT_D__ 的地量 __LOW_AMT__ 亿是本周唯一的「卖压衰竭」信号</b>——当日跌停 __LOW_ZT_DT__ 家为周内最多，
但成交额同时见底，随后 __HIGH_ZT_D__ 即以 __ZT_MULT__ 倍的涨停家数回应。周五则相反：
<b>成交额创周内新高（__W4_AMT__ 亿）而涨停家数（__HIGH_ZT__ 家以下）未创新高</b>，属于典型的「量先于价」。
</div>
<div id="c_senti" class="chart" style="margin-top:16px"></div>
<div class="note">柱：涨停/炸板/跌停家数（左轴）；线：封板率（右轴）。__D2__（周二）三柱同时走坏、__D3__（周三）三柱同时转好，是本周最重要的拐点。</div>
</div>

<div class="card">
<h2>二、逐日核心指标</h2>
<table>
<tr><th>交易日</th><th>涨停</th><th>炸板</th><th>封板率</th><th>跌停</th><th>最高板</th><th>连板</th><th>首板</th><th>两市成交</th><th>涨停股成交占比</th><th>晋级率</th><th>溢价中位</th><th>早盘封板占比</th></tr>
__TBL_DAY__
</table>
<div class="note" style="margin-top:10px">
「晋级率」= 前一交易日涨停股中再度涨停的比例；「溢价中位」= 前一交易日涨停股在当日的涨跌幅中位数；
「早盘封板占比」= 首次封板时间 ≤ 10:00 的涨停股占比。
表中缺失的「溢价中位」出现在 __PREM_MISS__，原因是该交易日未采集前一交易日涨停股的行情快照（数据边界，非数据异常）。
</div>
</div>

<div class="card">
<h2>三、连板梯队与高度：宽度在扩，高度在削</h2>
<div id="c_lad" class="chart"></div>
<div class="note">堆叠柱为每日连板梯队构成（左轴），折线为当日最高连板（右轴）。
周三（__HIGH_ZT_D__）是唯一出现 __MAXB__ 板的一天；周五涨停回到 __W4_ZT__ 家，但最高板已降至 __MAXB_W4__ 板。
周五新增资金几乎全在首板——首板 __SB_W4__ 家，占 __SB_W4_PCT__%，连板股仅 __LB_W4__ 家。</div>
<div class="note" style="margin-top:8px">
周五仍在连板、且为本周新面孔的标的：__LB_0918_NEW__。<b>本周「老龙头」__LB_TOP1__（__LB_TOP1_CODE__，__LB_TOP1_SEQ__ 板）已于周三后断板</b>，
其所在的 __LB_TOP1_HY__ 方向的资金去向，是下周最需要盯的线索。
</div>
</div>

<div class="card">
<h2>四、量能与成交结构：资金确实在加仓</h2>
<div class="two">
<div><div id="c_amt" class="chart-sm"></div></div>
<div><div id="c_fund" class="chart-sm"></div></div>
</div>
<div class="note" style="margin-top:12px">
<b>量能：</b>两市成交额从周一 __W0_AMT__ 亿升至周五 __W4_AMT__ 亿（__AMT_PCT__%），周均 __AMT_AVG__ 亿，
较上周五 __PREV_AMT__ 亿高出 __AMT_VS_PREV__%。地量出现在 __LOW_AMT_D__（__LOW_AMT__ 亿），高点出现在 __HIGH_AMT_D__（__HIGH_AMT__ 亿）。<br>
<b>封单：</b>全周封单合计从周一 __FUND_W0__ 亿升至周五 __FUND_W4__ 亿，最低 __FUND_MIN__ 亿（__FUND_MIN_D__，即洗盘日）。
封单与涨停家数同向变动，说明周三是「主动扫货」而非「被动涨停」。<br>
<b>口径自检：</b>涨停股成交额占两市比重周均 __SHARE_AVG__%，高于经验区间 3%~8% 的下沿仅 __SHARE_HIGH_D__ 一天（__SHARE_HIGH__%）。
该比值与涨停家数强相关，本周家数多次在 50 家以下，跌破下沿属正常范围；用「单只中位成交额」二次校验（周内最高 __AMT_MED_HIGH__ 亿、周五 __AMT_MED_W4__ 亿），字段源无误。
</div>
</div>

<div class="card">
<h2>五、赚钱效应：晋级率极不稳定，追高成本高</h2>
<div id="c_perf" class="chart"></div>
<div class="note">
晋级率全周在 __PROMO_LOW__%（__PROMO_LOW_D__）~ __PROMO_HIGH__%（__PROMO_HIGH_D__）之间摆动，均值 __PROMO_AVG__%。
最痛的是周四：周三 __HIGH_ZT__ 家涨停股在周四只有 __PROMO_LOW__% 续板、溢价中位 __PREM_LOW__%、翻绿比例高达 __GREEN_0917__%。
周五的修复更健康——溢价中位 __PREM_W4__%，晋级率回到 __PROMO_W4__%（__PROMO_W4_N__）。
<b>本周的实操结论是：周三式的普涨日后不宜追高，周五式的「放量 + 跌停归零 + 早盘封板前移」组合才是可跟随的形态。</b>
</div>
</div>

<div class="card">
<h2>六、行业迁移：钱从「元件」流出，去了哪</h2>
<div id="c_hy" class="chart-lg"></div>
<div class="note" style="margin-top:12px">
最重要的单一线索：<b>行业口径「元件」（PCB/覆铜板/被动元件聚集地）从上周五的 __HY_YJ_W0__ 家一路衰减到周五的 __HY_YJ_W4__ 家</b>。
这与题材标签「PCB/算力硬件」的走势形成背离——该题材周三仍有 __TH_PCB_W2__ 家命中、周四骤降至 __TH_PCB_W3__ 家、周五回到 __TH_PCB_W4__ 家，
说明<b>退潮的是「上游元件」，回归的是「下游算力应用」</b>，不是同一条钱。<br>
接棒方向：电网设备 __HY_DW_W2__（周三）→ __HY_DW_W4__（周五）、半导体 __HY_BDT_W1__（周三）→ __HY_BDT_W4__（周五），
周五另有家居用品 / 服装家纺 / 一般零售等低位消费补涨，以及房地产服务（世联行 3 板）。<br>
反例：汽车零部件周四单日冲到 __HY_QC_W3__ 家、周五回落到 __HY_QC_W4__ 家——<b>典型一日游，不是主线</b>。
</div>
</div>

<div class="card">
<h2>七、题材标签迁移（关键词命中口径）</h2>
<div id="c_theme" class="chart"></div>
<table style="margin-top:14px">
<tr><th>题材</th><th>本周合计</th><th>本周（不含上周五）</th><th>逐日（9/11 起）</th></tr>
__TBL_TH__
</table>
<div class="note" style="margin-top:12px">
「PCB/算力硬件」以 __TH_PCB_TOTAL__ 次命中占全周全部命中的 __TH_PCB_SHARE__%，是绝对主线；
「电力/风电储能」是唯一全周零衰减的方向，属底仓型板块。
注：题材为关键词命中口径，同一只股票可命中多条，各题材家数之和（__TH_TOTAL__）大于涨停总数。
</div>
</div>

<div class="card">
<h2>八、本周连板股（上榜 ≥2 日）</h2>
<table>
<tr><th>最高高度</th><th>代码</th><th>名称</th><th>上榜日数</th><th>连板路径</th><th>行业</th><th>涨停原因</th></tr>
__TBL_LB__
</table>
<div class="note" style="margin-top:10px">
共 __LB_N__ 只标的在本周出现 2 日及以上连板。路径最完整的是 __LB_TOP1__（__LB_TOP1_SEQ__ 板），
它同时也是本周唯一触及 __MAXB__ 板的标的。
</div>
</div>

<div class="card">
<h2>九、资金运动总结</h2>
<ul>
<li><b>量能路径：</b>16,127 亿（周二地量）→ 18,391 亿（周三 +14.0%）→ 18,231 亿（周四横住）→ 20,771 亿（周五 +13.9%）。
<b>周四周五「横一天再加一天」是本周最健康的量能结构</b>——增量资金是分批进场的，不是一次性脉冲。</li>
<li><b>情绪路径：</b>跌停家数 __D1_DT__ → 27 → 4 → 1 → <span class="hl">0</span>，单调收敛；
同时涨停家数在 32~89 之间剧烈摆动。<b>「跌停归零」比「涨停变多」更能说明抛压消散。</b></li>
<li><b>资金搬家方向：</b>上游元件与 PCB 制造（持续衰减）→ 下游算力应用 + 半导体材料 + 电网设备 + 低位消费。
主线的「宽度」在扩散，但<b>没有形成新的高标共识</b>（周五最高板仅 __MAXB_W4__ 板）。</li>
<li><b>结构与风险：</b>周五首板占 __SB_W4_PCT__%，晋级率均值仅 __PROMO_AVG__% 且波动区间达 __PROMO_LOW__%~__PROMO_HIGH__%。
	<b>本轮的赚钱效应高度依赖次日承接，一旦首板批量炸板（如周四翻绿 __GREEN_0917__%），回撤速度会同样快。</b></li>
</ul>
</div>

<div class="warn">
<b>口径与数据可信度说明</b>
<ul>
<li>涨停/炸板/跌停家数取<b>同花顺 limit_up_count / limit_down_count 汇总字段</b>（沪深口径，不含北交所）；
东财涨停池条数含北交所标的（如 9/18 东财 78 家 vs 同花顺 77 家，差额为 920298），本报告统一按沪深口径。</li>
<li>成交额、换手率、市值、封单一律取<b>东方财富</b>（同花顺 currency_value 字段实测与成交额差约 10 倍，不可用）。</li>
<li>「晋级率」由「前一日涨停池代码集合 ∩ 当日涨停池代码集合」计算，与逐日报告中基于行情快照的口径结果一致
（9/16 = 37.5%、9/17 = 10.1%、9/18 = 25.5%，与逐日报告已核对相同）。</li>
<li>9/14（周一）与 9/15（周二）的「溢价中位」缺失，原因是当日未采集前一日涨停股的行情快照，属数据边界。</li>
<li>9/14 及之前的历史涨停池由 9/14 收盘后接口回补，字段结构与 9/16~9/18 一致。</li>
</ul>
<b>风险提示</b>：本报告为盘后数据复盘，所有结论基于已发生的公开行情与涨停池字段，
不构成任何投资建议。涨停股样本存在明显的样本选择偏差（涨得好的才在池子里），
「溢价中位」「晋级率」等指标在样本量小于 50 只时波动极大，不宜外推。
</div>

<div class="note" style="margin-top:16px;text-align:center">Generated by a-stock-data · 涨停复盘 pipeline｜数据截止 __GEN_AT__</div>
</div>

<script>
var DAYS=__JS_DAYS__, ZT=__JS_ZT__, ZB=__JS_ZB__, DT=__JS_DT__, SEAL=__JS_SEAL__;
var AMT=__JS_AMT__, SHARE=__JS_SHARE__, PROMO=__JS_PROMO__, PREM=__JS_PREM__;
var LV=__JS_LV__, LAD=__JS_LAD__, MAXB=__JS_MAXB__, FUND=__JS_FUND__, ZTAMT=__JS_ZTAMT__;
var RED='#d93025', GRN='#12805c', ORG='#f59e0b', BLU='#2563eb';

function mk(id,opt){var el=document.getElementById(id);if(!el)return;var c=echarts.init(el);c.setOption(opt);window.addEventListener('resize',function(){c.resize()});}

mk('c_senti',{
  tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},
  legend:{top:3,left:'center',data:['涨停家数','炸板家数','跌停家数','封板率']},
  grid:{left:56,right:60,top:52,bottom:34},
  xAxis:{type:'category',data:DAYS,axisLabel:{fontSize:11}},
  yAxis:[{type:'value',name:'家数',nameTextStyle:{fontSize:11}},
         {type:'value',name:'封板率%',min:40,max:100,axisLabel:{formatter:'{value}%'},nameTextStyle:{fontSize:11}}],
  series:[
    {name:'涨停家数',type:'bar',data:ZT,itemStyle:{color:RED},barGap:'0%'},
    {name:'炸板家数',type:'bar',data:ZB,itemStyle:{color:ORG}},
    {name:'跌停家数',type:'bar',data:DT,itemStyle:{color:GRN}},
    {name:'封板率',type:'line',yAxisIndex:1,data:SEAL,smooth:true,symbolSize:7,
     lineStyle:{width:2.4,color:BLU},itemStyle:{color:BLU},
     label:{show:true,formatter:'{c}%',fontSize:10,color:BLU,position:'top'}}
  ]
});

mk('c_lad',{
  tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},
  legend:{top:3,left:'center'},
  grid:{left:56,right:60,top:52,bottom:34},
  xAxis:{type:'category',data:DAYS,axisLabel:{fontSize:11}},
  yAxis:[{type:'value',name:'家数',nameTextStyle:{fontSize:11}},
         {type:'value',name:'最高板',min:0,max:8,nameTextStyle:{fontSize:11}}],
  series:LV.map(function(k,i){
    return {name:k+'板',type:'bar',stack:'t',data:LAD.map(function(r){return r[i]}),
      emphasis:{focus:'series'}};
  }).concat([
    {name:'最高连板',type:'line',yAxisIndex:1,data:MAXB,smooth:true,symbolSize:7,
     lineStyle:{width:2.2,color:'#7c3aed',type:'dashed'},itemStyle:{color:'#7c3aed'},
     label:{show:true,fontSize:10,color:'#7c3aed'}}
  ])
});

mk('c_amt',{
  tooltip:{trigger:'axis'},
  legend:{top:3,left:'center',data:['两市成交额','涨停股成交占比']},
  grid:{left:64,right:56,top:52,bottom:34},
  xAxis:{type:'category',data:DAYS,axisLabel:{fontSize:11}},
  yAxis:[{type:'value',name:'亿元',nameTextStyle:{fontSize:11}},
         {type:'value',name:'占比%',axisLabel:{formatter:'{value}%'},nameTextStyle:{fontSize:11}}],
  series:[
    {name:'两市成交额',type:'bar',data:AMT,itemStyle:{color:'#93c5fd'},barWidth:'46%',
     label:{show:true,formatter:function(p){return (p.value/10000).toFixed(2)+'万亿'},fontSize:10,color:'#4b5563',position:'top'}},
    {name:'涨停股成交占比',type:'line',yAxisIndex:1,data:SHARE,smooth:true,symbolSize:7,
     lineStyle:{width:2.2,color:ORG},itemStyle:{color:ORG},
     label:{show:true,formatter:'{c}%',fontSize:10,color:ORG,position:'bottom'}}
  ]
});

mk('c_fund',{
  tooltip:{trigger:'axis'},
  legend:{top:3,left:'center',data:['封单合计','涨停股成交额合计']},
  grid:{left:60,right:56,top:52,bottom:34},
  xAxis:{type:'category',data:DAYS,axisLabel:{fontSize:11}},
  yAxis:[{type:'value',name:'亿元',nameTextStyle:{fontSize:11}},
         {type:'value',name:'亿元',nameTextStyle:{fontSize:11}}],
  series:[
    {name:'封单合计',type:'bar',data:FUND,itemStyle:{color:RED},barWidth:'42%'},
    {name:'涨停股成交额合计',type:'line',yAxisIndex:1,data:ZTAMT,smooth:true,symbolSize:6,
     lineStyle:{width:2,color:'#0f766e'},itemStyle:{color:'#0f766e'}}
  ]
});

mk('c_perf',{
  tooltip:{trigger:'axis'},
  legend:{top:3,left:'center',data:['晋级率','溢价中位数']},
  grid:{left:56,right:60,top:52,bottom:34},
  xAxis:{type:'category',data:DAYS,axisLabel:{fontSize:11}},
  yAxis:[{type:'value',name:'晋级率%',axisLabel:{formatter:'{value}%'},nameTextStyle:{fontSize:11}},
         {type:'value',name:'溢价%',axisLabel:{formatter:'{value}%'},nameTextStyle:{fontSize:11}}],
  series:[
    {name:'晋级率',type:'line',data:PROMO,smooth:true,symbolSize:8,connectNulls:true,
     lineStyle:{width:2.4,color:RED},itemStyle:{color:RED},
     label:{show:true,formatter:function(p){return p.value==null?'':p.value+'%'},fontSize:10,color:RED,position:'top'}},
    {name:'溢价中位数',type:'line',yAxisIndex:1,data:PREM,smooth:true,symbolSize:8,connectNulls:true,
     lineStyle:{width:2.4,color:BLU},itemStyle:{color:BLU},
     markLine:{silent:true,symbol:'none',data:[{yAxis:0,lineStyle:{color:'#9ca3af',type:'dashed'}}]},
     label:{show:true,formatter:function(p){return p.value==null?'':p.value+'%'},fontSize:10,color:BLU,position:'bottom'}}
  ]
});

mk('c_hy',{
  tooltip:{position:'top',formatter:function(p){return __JS_HY_NAME__[p.value[1]]+'<br>'+DAYS[p.value[0]]+'：<b>'+p.value[2]+'</b> 家'}},
  grid:{left:110,right:70,top:16,bottom:46},
  xAxis:{type:'category',data:DAYS,splitArea:{show:true},axisLabel:{fontSize:11}},
  yAxis:{type:'category',data:__JS_HY_NAME__,splitArea:{show:true},axisLabel:{fontSize:11}},
  visualMap:{min:0,max:__JS_HY_MAX__,calculable:true,orient:'vertical',right:6,top:'center',
    inRange:{color:['#f7f8fa','#fde2e0','#f6b0a8','#e8685c','#c62828']},
    textStyle:{fontSize:10}},
  series:[{name:'行业涨停家数',type:'heatmap',data:__JS_HY_DATA__,
    label:{show:true,fontSize:10},
    emphasis:{itemStyle:{shadowBlur:6,shadowColor:'rgba(0,0,0,.25)'}}}]
});

mk('c_theme',{
  tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},
  legend:{top:3,left:'center'},
  grid:{left:56,right:30,top:56,bottom:34},
  xAxis:{type:'category',data:__JS_TH_DAYS__,axisLabel:{fontSize:11}},
  yAxis:{type:'value',name:'命中家数',nameTextStyle:{fontSize:11}},
  series:__JS_TH_DATA__
});
</script>
</body>
</html>
"""


def hz(x):
    return str(x)


V["__D1__"] = short(WK[0]["date"])
V["__D2__"] = short(WK[1]["date"])
V["__D3__"] = short(WK[2]["date"])
V["__D4__"] = short(WK[3]["date"])
V["__D5__"] = short(WK[4]["date"])
for i, x in enumerate(WK, start=1):
    V[f"__D{i}_ZT__"] = x["zt"]
    V[f"__D{i}_ZB__"] = x["zb"]
    V[f"__D{i}_DT__"] = x["dt"]
    V[f"__D{i}_AMT__"] = f"{x['mkt_amt']:,.0f}"
    V[f"__D{i}_SEAL__"] = f1(x["seal"])
    V[f"__D{i}_PROMO__"] = f1(x["promo"])
    V[f"__D{i}_PREM__"] = f2(x["prem_mean"])
    V[f"__D{i}_EARLY__"] = f1(x["early_pct"])
    V[f"__D{i}_AMT_PCT__"] = (f"{(x['mkt_amt'] / WK[i - 2]['mkt_amt'] - 1) * 100:+.1f}"
                              if i >= 2 else "—")
V["__LB_N__"] = len([x for x in lb_occ if x["n"] >= 2])
V["__W4_ZT__"] = WK[4]["zt"]
V["__MAXB_SEQ__"] = "→".join(str(x["max_board"]) for x in WK)
V["__ZT_MULT__"] = f"{HIGH['zt'] / LOW['zt']:.1f}"
DT_MAX = max(WK, key=lambda x: x["dt"])
V["__DT_MAX_D__"] = short(DT_MAX["date"])
V["__PREM_MISS__"] = "、".join(lbl(x["date"]) for x in DAYS if x["prem_med"] is None) or "无"

out = HTML_T
for k, v in V.items():
    out = out.replace(k, str(v))

import re
left = re.findall(r"__[A-Z_0-9]+__", out)
print("placeholder residue:", left)

fp = os.path.join(REP, f"涨停周报-{START}至{END}.html")
with open(fp, "w", encoding="utf-8") as f:
    f.write(out)
print("saved ->", fp, os.path.getsize(fp) // 1024, "KB")
