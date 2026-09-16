# -*- coding: utf-8 -*-
"""
A股季节性研究 - HTML 研报生成
输入: out/seasonality_stats.json, out/seasonality_raw.json
输出: reports/a-share-seasonality.html
"""
import sys, os, json
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")
REP = os.path.join(BASE, "reports")
os.makedirs(REP, exist_ok=True)

stats = json.load(open(os.path.join(OUT, "seasonality_stats.json"), encoding="utf-8"))
raw = json.load(open(os.path.join(OUT, "seasonality_raw.json"), encoding="utf-8"))
cur = pd.Timestamp.today().strftime("%Y-%m")

# ---------- 重建面板 (算逐年明细) ----------
panel = {}
for it in raw["items"]:
    df = pd.DataFrame(it["rows"])
    df = df[(df["d"].str[:7] < cur) & (df["d"].str[:7] >= "2000-01")]
    if len(df) < 60:
        continue
    df = df.sort_values("d").reset_index(drop=True)
    df["ret"] = df["c"].pct_change()
    panel[it["name"]] = pd.Series(df["ret"].values, index=pd.PeriodIndex(df["d"].str[:7], freq="M"))
P = pd.DataFrame(panel)


def month_series(name, month):
    if name not in P:
        return {}
    s = P[name].dropna()
    s = s[s.index.month == month]
    return {int(p.year): round(float(v) * 100, 2) for p, v in s.items()}


def yoy(name, month):
    d = month_series(name, month)
    ys = sorted(d)
    return {"years": ys, "vals": [d[y] for y in ys]}


# ---------- 热力图数据 (全部品种, 呈现全貌) ----------
# 排序: 样本充足(>=12年)的优先, 组内按最强月 t 值降序
items_sorted = sorted(stats["items"],
                      key=lambda x: (x["best_n"] >= 12, x["best_t"]), reverse=True)
names = [x["name"] for x in items_sorted]
heat = []
for yi, x in enumerate(items_sorted):
    mm = {m["month"]: m for m in x["months"]}
    for mi in range(1, 13):
        v = mm.get(mi, {}).get("mean_dm")
        heat.append([mi - 1, yi, round(v, 2) if v is not None else None])

# 榜单只保留单月样本 >= 12 年的品种, 避免小样本噪音占据榜首
STRONG = [x for x in stats["items"] if x["best_n"] >= 12 and x["worst_n"] >= 12]

common = stats["market_common"]
c_mean = [common[str(m)]["mean"] for m in range(1, 13)]
c_med = [common[str(m)]["median"] for m in range(1, 13)]
c_dm = [common[str(m)]["mean_dm"] for m in range(1, 13)]
c_win = [common[str(m)]["win"] for m in range(1, 13)]

idx500 = P["中证500"].dropna() if "中证500" in P else None
m500 = {}
if idx500 is not None:
    for m in range(1, 13):
        x = idx500[idx500.index.month == m]
        m500[m] = {"mean": round(float(x.mean()) * 100, 2), "med": round(float(x.median()) * 100, 2),
                   "win": round(float((x > 0).mean()) * 100, 1), "min": round(float(x.min()) * 100, 1),
                   "max": round(float(x.max()) * 100, 1), "n": int(len(x))}

feb500 = yoy("中证500", 2)
jun_hl = yoy("上证红利", 6)
jun_zzhl = yoy("中证红利", 6)

# 各年2月横截面
feb_panel = P[P.index.month == 2]
feb_breadth = []
for y in sorted({p.year for p in feb_panel.index}):
    r = feb_panel[feb_panel.index.year == y]
    if r.empty:
        continue
    v = r.iloc[0].dropna()
    if len(v) < 10:
        continue
    feb_breadth.append({"y": y, "up": int((v > 0).sum()), "n": int(len(v)),
                        "pct": round(float((v > 0).mean()) * 100, 1),
                        "med": round(float(v.median()) * 100, 2)})

# 2月横截面表
feb_table = stats["feb_all"][:24]

DATA = {
    "sample": stats["sample"], "start": stats["start"],
    "fetched_at": stats["fetched_at"],
    "names": names, "heat": heat,
    "common": {"mean": c_mean, "median": c_med, "dm": c_dm, "win": c_win,
               "t": [common[str(m)]["t"] for m in range(1, 13)],
               "n": [common[str(m)]["n"] for m in range(1, 13)]},
    "m500": {str(k): v for k, v in m500.items()},
    "feb500": feb500, "jun_hl": jun_hl, "jun_zzhl": jun_zzhl,
    "feb_breadth": feb_breadth,
    "month_dist": stats["month_dist"],
    "rank_pos": sorted(STRONG, key=lambda x: x["best_t"], reverse=True)[:22],
    "rank_neg": sorted(STRONG, key=lambda x: x["worst_t"])[:15],
    "rank_F": sorted(STRONG, key=lambda x: x["F"], reverse=True)[:12],
    "feb_table": feb_table,
}

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>A股季节性研究：哪个品种的季节性最强</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:"PingFang SC","Microsoft YaHei",sans-serif; background:#f7f8fa; color:#2b2f36; line-height:1.65; }
  .wrap { max-width:1180px; margin:0 auto; padding:28px 20px 60px; }
  h1 { font-size:26px; margin-bottom:6px; }
  .sub { color:#8a919c; font-size:13px; margin-bottom:22px; }
  h2 { font-size:19px; margin:38px 0 14px; padding-left:10px; border-left:4px solid #c0392b; }
  h3 { font-size:15px; margin:20px 0 8px; color:#3a4048; }
  .tldr { background:#fff; border:1px solid #e8eaee; border-left:4px solid #c0392b; border-radius:10px; padding:20px 22px; box-shadow:0 1px 3px rgba(0,0,0,.04); }
  .tldr li { margin:8px 0 8px 18px; font-size:14.5px; }
  .tldr b { color:#c0392b; }
  .cards { display:flex; gap:14px; flex-wrap:wrap; margin:18px 0; }
  .card { flex:1; min-width:196px; background:#fff; border:1px solid #e8eaee; border-radius:10px; padding:15px 17px; box-shadow:0 1px 3px rgba(0,0,0,.04); }
  .card .name { font-size:13px; color:#5a616c; }
  .card .big { font-size:27px; font-weight:700; margin:3px 0; }
  .card.win { border-top:3px solid #d0342c; } .card.lose { border-top:3px solid #1e8e4e; }
  .card .meta { font-size:12px; color:#8a919c; line-height:1.6; }
  .up { color:#d0342c; font-weight:600; } .down { color:#1e8e4e; font-weight:600; }
  table { width:100%; border-collapse:collapse; background:#fff; font-size:13px; border:1px solid #e8eaee; border-radius:8px; overflow:hidden; }
  th { background:#f0f2f5; padding:8px 10px; text-align:left; font-weight:600; color:#4a505a; white-space:nowrap; }
  td { padding:7px 10px; border-top:1px solid #eef0f3; }
  tr:hover td { background:#fafbfc; }
  td.n, th.n { text-align:right; font-variant-numeric:tabular-nums; }
  .chart { width:100%; height:420px; background:#fff; border:1px solid #e8eaee; border-radius:10px; padding:10px; box-shadow:0 1px 3px rgba(0,0,0,.04); }
  .chart.tall { height:560px; }
  .chart.xtall { height:1500px; }
  .note { font-size:12px; color:#9aa1ab; margin-top:8px; line-height:1.65; }
  .tag { display:inline-block; font-size:11.5px; padding:1px 8px; border-radius:10px; margin-right:5px; }
  .tag-red { background:#fdeceb; color:#c0392b; } .tag-green { background:#e8f6ee; color:#1e8e4e; }
  .tag-blue { background:#eaf1fd; color:#2c6bd0; } .tag-gray { background:#f0f2f5; color:#5a616c; }
  .tag-amber { background:#fff5e0; color:#a07000; }
  .risk { background:#fff8e6; border:1px solid #f0e0b0; border-radius:10px; padding:14px 18px; margin-top:14px; font-size:13.5px; line-height:1.8; }
  .risk b { color:#a07000; }
  .concl { background:#fff; border:1px solid #e8eaee; border-left:4px solid #c0392b; border-radius:8px; padding:16px 20px; margin-top:14px; font-size:14px; }
  .concl p { margin:9px 0; }
  .method { background:#f4f8ff; border:1px solid #d8e5fb; border-radius:10px; padding:14px 18px; margin-top:14px; font-size:13px; line-height:1.8; }
  .method b { color:#2c6bd0; }
  .grid2 { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
  @media (max-width:880px){ .grid2 { grid-template-columns:1fr; } }
  .dis { font-size:12px; color:#9aa1ab; margin-top:34px; line-height:1.75; border-top:1px solid #e8eaee; padding-top:14px; }
  .hl { background:#fff9e8; }
</style>
</head>
<body>
<div class="wrap">

<h1>A股季节性研究：哪个品种的季节性最强</h1>
<div class="sub">样本 __PERIOD__ ｜ __NITEM__ 个指数品种（宽基/风格/行业/细分/主题）｜ __NMON__ 个月度观测 ｜ 数据来源：腾讯财经月线（前复权）｜ 生成时间 __FETCHED__</div>

<div class="tldr">
  <ul>
    <li><b>结论一：A股季节性最强的月份是 2 月，且这不是"某个品种"的特性，而是横截面级别的共识。</b>81 个品种中有 <b>52 个</b>把 2 月选为自己的最强月份，2 月的全市场平均收益 +3.43%、上涨胜率 77.8%，远高于其他 11 个月。</li>
    <li><b>结论二：季节性最强的单一品种是「中证500」的 2 月。</b>20 年样本里 18 年上涨（胜率 90%），平均收益 <b>+6.17%</b>，<b>最差年份仅 -2.7%</b>，t 值 3.86 —— 高收益、高胜率、极低尾部风险，这在全样本里是独一档的风险收益结构。</li>
    <li><b>结论三：季节性的本质是「2 月做小盘成长、12 月做大盘蓝筹」的风格切换。</b>剔除市场共性后，2 月小盘成长仍比市场多涨 2%~3.8%（中证信息 +3.27、中证TMT +3.76、全指信息 +3.70），而上证指数、红利类在 2 月反而弱于市场。</li>
    <li><b>结论四：最强的「负面季节性」是 6 月的红利与公用事业。</b>上证红利 6 月 22 年只有 8 年上涨，平均 <b>-3.70%</b>，t 值 -3.20，是全样本最稳定的单月负向信号。</li>
    <li><b>结论五：2 月效应会被「系统性风险年」打断，不是必赢。</b>2016、2018、2020 三年 2 月全市场上涨品种占比仅 15%~49%；且收益高度右偏——2019 年 2 月中位数 +17.9%、2024 年 +11.1%，少数年份贡献了大部分收益。</li>
  </ul>
</div>

<h2>一、核心数据</h2>
<div class="cards">
  <div class="card win">
    <div class="name">中证500 · 2月</div>
    <div class="big up">+6.17%</div>
    <div class="meta">20年18涨 · 胜率90%<br>最差年仅 -2.7% · t=3.86</div>
  </div>
  <div class="card win">
    <div class="name">中证1000 · 2月</div>
    <div class="big up">+5.31%</div>
    <div class="meta">12年10涨 · 胜率83.3%<br>2016年以来仍 +4.96%</div>
  </div>
  <div class="card lose">
    <div class="name">上证红利 · 6月</div>
    <div class="big down">-3.70%</div>
    <div class="meta">22年8涨 · 胜率36.4%<br>t=-3.20 · 最稳定负向信号</div>
  </div>
  <div class="card">
    <div class="name">全市场 · 2月（共性）</div>
    <div class="big up">+3.43%</div>
    <div class="meta">胜率77.8% · 27个样本年<br>最强月份共识 52/81</div>
  </div>
</div>

<h2>二、全市场共性月度效应</h2>
<p style="font-size:13.5px;color:#5a616c;margin-bottom:10px;">取全部品种每月收益的横截面中位数作为"市场"，再剔除年度整体涨跌效应（去年度均值）。A股的月度规律非常集中：<b>2 月一枝独秀</b>，6、8、10 月偏弱。</p>
<div id="c_common" class="chart"></div>
<div class="note">左轴：月度收益（%）；红色为正值、绿色为负值。柱上标注该月平均收益与上涨胜率。"去年度效应"= 当月收益减去该年 12 个月的平均收益，用于剥离牛熊整体涨跌。</div>

<h2>三、最强月分布：52/81 指向 2 月</h2>
<div id="c_dist" class="chart" style="height:320px;"></div>
<div class="note">统计口径：对每个品种，用"去年度效应 + winsorize 抗极值"后的 t 值选出最强月份，再统计多少个品种落在每个月。</div>

<h2>四、季节性强度全景（品种 × 月份热力图）</h2>
<p style="font-size:13.5px;color:#5a616c;margin-bottom:10px;">横轴为 12 个月份，纵轴为 81 个品种（按最强月 t 值降序）。颜色为该品种在该月的<b>去年度效应超额收益</b>：红=强于自身年度均值，绿=弱于自身年度均值。可以看到一条贯穿全图的"红柱"落在 2 月。</p>
<div id="c_heat" class="chart xtall"></div>
<div class="note">注意：纵轴越靠上的品种样本年数未必越多；红利类等品种样本 18~22 年，多数行业/主题指数样本 12~17 年（2012 年后成立）。</div>

<h2>五、单一品种画像：中证500 的十二个月</h2>
<div class="grid2">
  <div><div id="c_m500" class="chart"></div></div>
  <div><div id="c_m500win" class="chart"></div></div>
</div>
<div class="note">中证500 的季节性结构在整个样本里最"干净"：2 月胜率 90%、最小值仅 -2.7%；而 1 月、3 月、4 月、6 月、10 月胜率均不足 48%。</div>

<h2>六、2月效应逐年检验（是否还有效）</h2>
<div id="c_feb" class="chart tall"></div>
<div class="note">柱：中证500 当月收益（%），红涨绿跌。折线：当年 2 月全市场上涨品种占比（%）。<b>失效年份集中在 2016（熔断）、2018（贸易战）、2020（疫情）、2021（核心资产瓦解）</b>，均为系统性风险年。2026 年 2 月中证500 +3.4%，规律仍成立。</div>

<h3>各年 2 月横截面广度</h3>
<table id="t_breadth"></table>

<h2>七、榜单</h2>
<h3>正季节性 TOP22（按稳健 t 值）</h3>
<table id="t_pos"></table>
<div class="note">"去年度%"=剔除年度涨跌后的月度超额；"去共性%"=再剔除当月全市场横截面中位数后的超额，代表真正的品种特质季节性。</div>

<h3>负季节性 TOP15（最差月）</h3>
<table id="t_neg"></table>

<h3>季节性强度 TOP12（按月份效应 F 值）</h3>
<table id="t_F"></table>
<div class="note">F 值为单因素方差分析（因子=月份）统计量，衡量 12 个月效应整体是否显著。注意：F 值对波动率小的品种有利（同样的绝对收益，噪音小则 F 高），因此公用事业类排名靠前，但其绝对收益幅度很小。</div>

<h2>八、6月红利效应专项</h2>
<div class="grid2">
  <div><div id="c_junhl" class="chart"></div></div>
  <div><div id="c_junzz" class="chart"></div></div>
</div>
<div class="note">上证红利（左）22 年 6 月中仅 8 年上涨；中证红利（右）18 年 6 月中仅 6 年上涨。2008 年（-26.8%/-9.4%）、2013 年（-15.8%/-16.5%）是极端年。2026 年 6 月上证红利 -10.3%、中证红利 -10.0%。</div>

<h2>九、方法论与局限</h2>
<div class="method">
  <p><b>1. 样本</b>：__NITEM__ 个指数品种，区间 __PERIOD__。起点取 2000-01，规避 1990s 无涨跌停 / T+0 / 极小市值阶段的极端波动（上证指数 1992 年单月涨幅曾超 170%，会严重污染均值）。</p>
  <p><b>2. 三层收益口径</b>：① 原始月度收益；② 去年度效应（减该年 12 个月均值）——剥离牛熊整体涨跌；③ 去市场共性（减当月横截面中位数）——剥离"这个月大盘整体在涨"。<b>只有第 ③ 层才是真正的"品种特质季节性"。</b></p>
  <p><b>3. 抗极值</b>：对每个品种的月度收益序列做 winsorize（2%/98% 截尾），避免单一极端月主导结论。</p>
  <p><b>4. 显著性</b>：报告 t 值基于去年度效应序列。需注意多重检验问题——81 品种 × 12 月共 972 次检验，纯随机也会有约 49 个"显著"结果，因此<b>单个品种的 t=2.5 不足为凭；真正的证据是横截面一致性（52/81 指向 2 月）</b>。</p>
  <p><b>5. 未处理的问题</b>：① 春节在 1 月下旬至 2 月中旬浮动，"2 月效应"很可能是"春节前后效应"的日历投影，未做春节日期对齐；② 未考虑交易成本与冲击成本；③ 样本内含有 2005-2007、2014-2015、2019、2024 等多轮牛市，牛市中所有月份都易上涨，去年度效应只能部分修正。</p>
</div>

<h2>十、风险提示</h2>
<div class="risk">
  <p><b>季节性不是因果规律，而是历史统计特征。</b>它的成立依赖市场参与者结构、资金面节律（如年初信贷投放、机构考核周期）和投资者行为的重复性，这些条件一旦改变，规律即失效。</p>
  <p><b>1. 规律已被广泛认知。</b>2 月效应、春季躁动是市场共识，共识本身会带来提前抢跑与提前结束（例如行情提前到 1 月启动、或 2 月即见顶），历史上 2016/2018/2020 三年该效应完全失效。</p>
  <p><b>2. 收益高度右偏。</b>中证500 的 2 月平均收益 +6.17%、中位数 +4.49%，但 2019 年单年 +20.3%、2024 年 +13.8%，少数年份贡献了主要收益。剔除这两个年份后均值显著下降。</p>
  <p><b>3. 小样本 + 数据挖掘。</b>多数行业/主题指数样本仅 12~17 年，每月 12~17 个观测，统计功效有限。榜单前 22 名中 15 个是 2 月，虽然一致性很高，但仍无法排除数据挖掘偏差。</p>
  <p><b>4. 本文为历史统计研究，不构成任何投资建议。</b>任何基于季节性的仓位决策都需结合当期宏观、流动性与估值位置独立判断，并自行承担风险。</p>
</div>

<div class="dis">
  数据来源：腾讯财经月线（web.ifzq.gtimg.cn / data.gtimg.cn，前复权），抓取时间 __FETCHED__。<br>
  品种池：宽基 15 / 风格 6 / 行业 20 / 细分 18 / 主题 19（部分指数因数据不足被剔除）。<br>
  统计脚本：scripts/seasonality_fetch_tx2.py（抓取）、scripts/seasonality_analyze.py（统计）、scripts/seasonality_report.py（本报告）。<br>
  本文所有收益均为指数层面价格收益，不含分红再投资以外的处理；指数历史不代表未来表现。
</div>

</div>
<script>
var D = __DATA__;

function ec(id) { return echarts.init(document.getElementById(id)); }
var RED = '#d0342c', GREEN = '#1e8e4e', GREY = '#8a919c';
var MON = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月'];

// 1. 全市场共性
(function(){
  var o = {
    tooltip: { trigger:'axis', valueFormatter:function(v){return v+'%';} },
    grid: { left:56, right:30, top:40, bottom:34 },
    xAxis: { type:'category', data:MON, axisTick:{show:false} },
    yAxis: { type:'value', name:'月度收益(%)', axisLabel:{formatter:'{value}%'}, splitLine:{lineStyle:{color:'#eef0f3'}} },
    series: [
      { name:'原始均值', type:'bar', data:D.common.mean, barWidth:'42%',
        itemStyle:{ color:function(p){ return p.value>=0 ? RED : GREEN; }, borderRadius:[3,3,0,0] },
        label:{ show:true, position:'top', formatter:function(p){return p.value+'%';}, fontSize:11, color:'#5a616c' },
        markLine:{ silent:true, symbol:'none', lineStyle:{color:'#c9ced6', type:'dashed'},
                   data:[{yAxis:0}], label:{show:false} } },
      { name:'去年度效应', type:'line', data:D.common.dm, smooth:true, symbolSize:7,
        lineStyle:{ width:2, color:'#2c6bd0' }, itemStyle:{ color:'#2c6bd0' } }
    ],
    legend:{ top:6, right:10, itemWidth:14, textStyle:{fontSize:12} }
  };
  // 胜率注记
  var rich = D.common.win;
  o.graphic = [{ type:'text', left:'center', top:14,
                 style:{ text:'柱内为原始均值，蓝线为去年度效应；2月胜率 '+rich[1]+'%',
                         fill:'#9aa1ab', fontSize:12 } }];
  ec('c_common').setOption(o);
})();

// 2. 最强月分布
(function(){
  var md = D.month_dist, arr = [];
  for (var m=1;m<=12;m++){ arr.push(md[String(m)]||0); }
  ec('c_dist').setOption({
    tooltip:{ trigger:'axis', valueFormatter:function(v){return v+' 个品种';} },
    grid:{ left:50, right:30, top:30, bottom:34 },
    xAxis:{ type:'category', data:MON, axisTick:{show:false} },
    yAxis:{ type:'value', name:'品种数', splitLine:{lineStyle:{color:'#eef0f3'}} },
    series:[{ type:'bar', data:arr.map(function(v,i){ return {value:v,
        itemStyle:{ color: i===1 ? RED : (v>=5 ? '#e39a94' : '#cfd4db'), borderRadius:[3,3,0,0] }};}),
      barWidth:'52%',
      label:{ show:true, position:'top', fontSize:12, fontWeight:'bold', color:'#5a616c' } }]
  });
})();

// 3. 热力图
(function(){
  var data = D.heat.filter(function(d){ return d[2] !== null; });
  ec('c_heat').setOption({
    tooltip:{ position:'top',
      formatter:function(p){ return D.names[p.value[1]] + ' · ' + MON[p.value[0]] + '<br><b>' + p.value[2] + '%</b>'; } },
    grid:{ left:96, right:60, top:14, bottom:74 },
    xAxis:{ type:'category', data:MON, splitArea:{show:true}, axisLabel:{fontSize:12} },
    yAxis:{ type:'category', data:D.names, splitArea:{show:true}, axisLabel:{fontSize:10.5} },
    visualMap:{ min:-4, max:4, calculable:true, orient:'horizontal', left:'center', bottom:8,
      text:['强于自身年度均值','弱于自身年度均值'], textStyle:{fontSize:11},
      inRange:{ color:['#1e8e4e','#9fd4b4','#f7f8fa','#f0a9a3','#d0342c'] } },
    series:[{ name:'月度超额', type:'heatmap', data:data,
      label:{ show:false }, emphasis:{ itemStyle:{ borderColor:'#333', borderWidth:1 } },
      progressive: 2000 }]
  });
})();

// 4. 中证500 十二个月
(function(){
  var m = D.m500, mean=[], med=[], win=[];
  for (var i=1;i<=12;i++){ var v=m[String(i)]||{}; mean.push(v.mean); med.push(v.med); win.push(v.win); }
  ec('c_m500').setOption({
    title:{ text:'中证500 各月平均/中位收益', left:'center', top:6, textStyle:{fontSize:13} },
    tooltip:{ trigger:'axis', valueFormatter:function(v){return v+'%';} },
    grid:{ left:52, right:22, top:52, bottom:30 },
    xAxis:{ type:'category', data:MON, axisTick:{show:false}, axisLabel:{fontSize:11} },
    yAxis:{ type:'value', axisLabel:{formatter:'{value}%'}, splitLine:{lineStyle:{color:'#eef0f3'}} },
    legend:{ top:26, itemWidth:14, textStyle:{fontSize:11} },
    series:[
      { name:'平均', type:'bar', data:mean, barWidth:'36%',
        itemStyle:{ borderRadius:[3,3,0,0],
          color:function(p){ return p.value>=0?RED:GREEN; } } },
      { name:'中位', type:'line', data:med, smooth:true, symbolSize:6,
        lineStyle:{color:'#2c6bd0', width:2}, itemStyle:{color:'#2c6bd0'} }
    ]
  });
  ec('c_m500win').setOption({
    title:{ text:'中证500 各月上涨胜率', left:'center', top:6, textStyle:{fontSize:13} },
    tooltip:{ trigger:'axis', valueFormatter:function(v){return v+'%';} },
    grid:{ left:52, right:46, top:52, bottom:30 },
    xAxis:{ type:'category', data:MON, axisTick:{show:false}, axisLabel:{fontSize:11} },
    yAxis:{ type:'value', max:100, axisLabel:{formatter:'{value}%'}, splitLine:{lineStyle:{color:'#eef0f3'}} },
    series:[{ type:'bar', data:win.map(function(v,i){ return {value:v,
        itemStyle:{ color: i===1 ? RED : '#9aa1ab', borderRadius:[3,3,0,0] }};}),
      barWidth:'52%',
      label:{ show:true, position:'top', formatter:'{c}%', fontSize:10, color:'#5a616c' },
      markLine:{ silent:true, symbol:'none', lineStyle:{color:'#c9ced6', type:'dashed'},
                 data:[{yAxis:50, label:{formatter:'50%'}}] } }]
  });
})();

// 5. 2月逐年
(function(){
  var f = D.feb500, b = D.feb_breadth;
  var bymap = {}; b.forEach(function(x){ bymap[x.y]=x; });
  var labels = f.years.map(String);
  var pct = f.years.map(function(y){ return bymap[y] ? bymap[y].pct : null; });
  ec('c_feb').setOption({
    tooltip:{ trigger:'axis' },
    grid:{ left:56, right:64, top:34, bottom:44 },
    legend:{ top:6, itemWidth:14, textStyle:{fontSize:12} },
    xAxis:{ type:'category', data:labels, axisTick:{show:false}, axisLabel:{fontSize:11} },
    yAxis:[
      { type:'value', name:'中证500收益(%)', axisLabel:{formatter:'{value}%'}, splitLine:{lineStyle:{color:'#eef0f3'}} },
      { type:'value', name:'上涨占比(%)', min:0, max:100, axisLabel:{formatter:'{value}%'}, splitLine:{show:false} }
    ],
    series:[
      { name:'中证500 2月收益', type:'bar', data:f.vals, barWidth:'54%',
        itemStyle:{ borderRadius:[3,3,0,0], color:function(p){ return p.value>=0?RED:GREEN; } },
        label:{ show:true, position:'top', formatter:'{c}%', fontSize:9.5, color:'#5a616c' } },
      { name:'全市场2月上涨占比', type:'line', yAxisIndex:1, data:pct, smooth:true, symbolSize:6,
        lineStyle:{ color:'#2c6bd0', width:2 }, itemStyle:{ color:'#2c6bd0' },
        connectNulls:true }
    ]
  });
})();

// 6. 6月红利
function junChart(id, name, d, title){
  ec(id).setOption({
    title:{ text:title, left:'center', top:6, textStyle:{fontSize:13} },
    tooltip:{ trigger:'axis', valueFormatter:function(v){return v+'%';} },
    grid:{ left:56, right:22, top:52, bottom:34 },
    xAxis:{ type:'category', data:d.years.map(String), axisTick:{show:false}, axisLabel:{fontSize:10.5} },
    yAxis:{ type:'value', axisLabel:{formatter:'{value}%'}, splitLine:{lineStyle:{color:'#eef0f3'}} },
    series:[{ type:'bar', data:d.vals, barWidth:'54%',
      itemStyle:{ borderRadius:[3,3,0,0], color:function(p){ return p.value>=0?RED:GREEN; } } }]
  });
}
junChart('c_junhl','上证红利', D.jun_hl, '上证红利 6月收益（22年）');
junChart('c_junzz','中证红利', D.jun_zzhl, '中证红利 6月收益（18年）');

// 7. 表格
function tbl(id, rows, cols){
  var h = '<thead><tr>' + cols.map(function(c){ return '<th class="'+(c.n?'n':'')+'">'+c.t+'</th>'; }).join('') + '</tr></thead><tbody>';
  rows.forEach(function(r){
    h += '<tr'+(r.__hl?' class="hl"':'')+'>' + cols.map(function(c){
      var v = c.f(r);
      return '<td class="'+(c.n?'n':'')+'">'+ (v===null||v===undefined?'-':v) +'</td>';
    }).join('') + '</tr>';
  });
  document.getElementById(id).innerHTML = h + '</tbody>';
}
function sgn(v){ if(v===null||v===undefined) return '-';
  var c = v>0?'up':(v<0?'down':''); var t = (v>0?'+':'')+v.toFixed(2)+'%'; return '<span class="'+c+'">'+t+'</span>'; }

tbl('t_pos', D.rank_pos, [
  {t:'品种', f:function(r){return r.name;}},
  {t:'组', f:function(r){return '<span class="tag tag-gray">'+r.group+'</span>';}},
  {t:'最强月', n:1, f:function(r){return r.best_month+'月';}},
  {t:'去年度效应', n:1, f:function(r){return sgn(r.best_mean_dm);}},
  {t:'去市场共性', n:1, f:function(r){return sgn(r.best_mean_re);}},
  {t:'原始均值', n:1, f:function(r){return sgn(r.best_mean);}},
  {t:'中位数', n:1, f:function(r){return sgn(r.best_median);}},
  {t:'胜率', n:1, f:function(r){return r.best_win+'%';}},
  {t:'t值', n:1, f:function(r){return r.best_t.toFixed(2);}},
  {t:'样本年', n:1, f:function(r){return r.best_n;}},
  {t:'最差年', n:1, f:function(r){return sgn(r.best_min);}}
]);

tbl('t_neg', D.rank_neg, [
  {t:'品种', f:function(r){return r.name;}},
  {t:'组', f:function(r){return '<span class="tag tag-gray">'+r.group+'</span>';}},
  {t:'最差月', n:1, f:function(r){return r.worst_month+'月';}},
  {t:'去年度效应', n:1, f:function(r){return sgn(r.worst_mean_dm);}},
  {t:'原始均值', n:1, f:function(r){return sgn(r.worst_mean);}},
  {t:'中位数', n:1, f:function(r){return sgn(r.worst_median);}},
  {t:'胜率', n:1, f:function(r){return r.worst_win+'%';}},
  {t:'t值', n:1, f:function(r){return r.worst_t.toFixed(2);}},
  {t:'样本年', n:1, f:function(r){return r.worst_n;}}
]);

tbl('t_F', D.rank_F, [
  {t:'品种', f:function(r){return r.name;}},
  {t:'组', f:function(r){return '<span class="tag tag-gray">'+r.group+'</span>';}},
  {t:'F值', n:1, f:function(r){return r.F.toFixed(2);}},
  {t:'p值', n:1, f:function(r){return r.p.toFixed(3);}},
  {t:'季节性振幅', n:1, f:function(r){return r.amp.toFixed(2)+'%';}},
  {t:'最强月', n:1, f:function(r){return r.best_month+'月';}},
  {t:'样本年', n:1, f:function(r){return r.best_n;}}
]);

tbl('t_breadth', D.feb_breadth, [
  {t:'年份', n:1, f:function(r){return r.y;}},
  {t:'上涨/总数', n:1, f:function(r){return r.up+' / '+r.n;}},
  {t:'上涨占比', n:1, f:function(r){
      var c = r.pct>=70?'up':(r.pct<=40?'down':''); return '<span class="'+c+'">'+r.pct+'%</span>';}},
  {t:'横截面中位数', n:1, f:function(r){return sgn(r.med);}}
]);
</script>
</body>
</html>
"""

html = (HTML
        .replace("__PERIOD__", stats["sample"]["period"])
        .replace("__NITEM__", str(stats["sample"]["n_items"]))
        .replace("__NMON__", str(stats["sample"]["n_months"]))
        .replace("__FETCHED__", stats["fetched_at"])
        .replace("__DATA__", json.dumps(DATA, ensure_ascii=False)))

outp = os.path.join(REP, "a-share-seasonality.html")
with open(outp, "w", encoding="utf-8") as f:
    f.write(html)
print("生成:", outp, len(html), "字节")

# 提取 JS 供 node --check
import re
js = re.findall(r"<script>(.*?)</script>", html, re.S)
if js:
    p = os.path.join(OUT, "_season_check.js")
    open(p, "w", encoding="utf-8").write(js[-1])
    print("JS 提取:", p)
