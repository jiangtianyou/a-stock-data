# -*- coding: utf-8 -*-
"""
2024 年小盘股行情复盘 - HTML 报告生成
输入: out/review2024_raw.json, out/review2024_stats.json
输出: reports/review-2024-smallcap.html
"""
import sys, os, json
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")
REP = os.path.join(BASE, "reports")
os.makedirs(REP, exist_ok=True)

raw = json.load(open(os.path.join(OUT, "review2024_raw.json"), encoding="utf-8"))
stats = json.load(open(os.path.join(OUT, "review2024_stats.json"), encoding="utf-8"))

CL = {}
VOL = {}
for it in raw["items"]:
    df = pd.DataFrame(it["rows"]).sort_values("d")
    CL[it["name"]] = pd.Series(df["c"].values, index=df["d"].values)
    VOL[it["name"]] = pd.Series(df["v"].values, index=df["d"].values)

MAIN = ["国证2000", "中证1000", "中证500", "沪深300", "上证50"]
dates = list(CL["国证2000"].index)
base = {n: CL[n].iloc[0] for n in MAIN}
series = [[n, [round(float(CL[n][d] / base[n] * 100), 2) for d in dates]] for n in MAIN]

EVENTS = [
    {"d": "2024-01-02", "t": "1/2 暴跌起点", "v": 100.0, "pos": "top"},
    {"d": "2024-02-05", "t": "2/5 见底 5347", "v": None, "pos": "bottom"},
    {"d": "2024-03-21", "t": "3/21 反弹高点", "v": None, "pos": "top"},
    {"d": "2024-09-18", "t": "9/18 二次探底", "v": None, "pos": "bottom"},
    {"d": "2024-10-08", "t": "10/8 情绪顶", "v": None, "pos": "top"},
]

# 成交量(按阶段均值, 相对2023H2)
vperiods = stats["vol_periods"]
vdata = {k: v for k, v in stats["vol"].items() if k in ["国证2000", "中证1000", "中证500", "沪深300"]}

DATA = {
    "dates": dates,
    "series": series,
    "events": EVENTS,
    "segs": stats["segs"],
    "seg_data": stats["seg_data"],
    "grad": stats["grad"],
    "vol_periods": vperiods,
    "vol": vdata,
    "order": stats["order"],
    "fetched_at": raw["fetched_at"],
}

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>2024 年小盘股行情复盘：从 -29% 踩踏到 +41% 修复</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:"PingFang SC","Microsoft YaHei",sans-serif; background:#f7f8fa; color:#2b2f36; line-height:1.65; }
  .wrap { max-width:1160px; margin:0 auto; padding:28px 20px 60px; }
  h1 { font-size:25px; margin-bottom:6px; }
  .sub { color:#8a919c; font-size:13px; margin-bottom:22px; }
  h2 { font-size:19px; margin:38px 0 14px; padding-left:10px; border-left:4px solid #c0392b; }
  h3 { font-size:15px; margin:20px 0 8px; color:#3a4048; }
  .tldr { background:#fff; border:1px solid #e8eaee; border-left:4px solid #c0392b; border-radius:10px; padding:20px 22px; box-shadow:0 1px 3px rgba(0,0,0,.04); }
  .tldr li { margin:8px 0 8px 18px; font-size:14.5px; }
  .tldr b { color:#c0392b; }
  .cards { display:flex; gap:14px; flex-wrap:wrap; margin:18px 0; }
  .card { flex:1; min-width:190px; background:#fff; border:1px solid #e8eaee; border-radius:10px; padding:15px 17px; box-shadow:0 1px 3px rgba(0,0,0,.04); }
  .card .name { font-size:13px; color:#5a616c; }
  .card .big { font-size:26px; font-weight:700; margin:3px 0; }
  .card .meta { font-size:12px; color:#8a919c; line-height:1.6; }
  .card.lose { border-top:3px solid #1e8e4e; } .card.win { border-top:3px solid #d0342c; }
  .up { color:#d0342c; font-weight:600; } .down { color:#1e8e4e; font-weight:600; }
  table { width:100%; border-collapse:collapse; background:#fff; font-size:13px; border:1px solid #e8eaee; border-radius:8px; overflow:hidden; }
  th { background:#f0f2f5; padding:8px 10px; text-align:left; font-weight:600; color:#4a505a; white-space:nowrap; }
  td { padding:7px 10px; border-top:1px solid #eef0f3; }
  tr:hover td { background:#fafbfc; }
  td.n, th.n { text-align:right; font-variant-numeric:tabular-nums; }
  .chart { width:100%; height:460px; background:#fff; border:1px solid #e8eaee; border-radius:10px; padding:10px; box-shadow:0 1px 3px rgba(0,0,0,.04); }
  .chart.tall { height:520px; }
  .note { font-size:12px; color:#9aa1ab; margin-top:8px; line-height:1.65; }
  .tag { display:inline-block; font-size:11.5px; padding:1px 8px; border-radius:10px; margin-right:5px; }
  .tag-red { background:#fdeceb; color:#c0392b; } .tag-green { background:#e8f6ee; color:#1e8e4e; }
  .tag-gray { background:#f0f2f5; color:#5a616c; } .tag-amber { background:#fff5e0; color:#a07000; }
  .tag-blue { background:#eaf1fd; color:#2c6bd0; }
  .risk { background:#fff8e6; border:1px solid #f0e0b0; border-radius:10px; padding:14px 18px; margin-top:14px; font-size:13.5px; line-height:1.8; }
  .risk b { color:#a07000; }
  .method { background:#f4f8ff; border:1px solid #d8e5fb; border-radius:10px; padding:14px 18px; margin-top:14px; font-size:13px; line-height:1.8; }
  .method b { color:#2c6bd0; }
  .timeline { background:#fff; border:1px solid #e8eaee; border-radius:10px; padding:6px 20px 14px; box-shadow:0 1px 3px rgba(0,0,0,.04); margin-top:14px; }
  .timeline .row { display:flex; gap:14px; padding:11px 0; border-bottom:1px dashed #eef0f3; font-size:13.5px; }
  .timeline .row:last-child { border-bottom:none; }
  .timeline .dt { flex:0 0 108px; color:#c0392b; font-weight:600; font-variant-numeric:tabular-nums; }
  .timeline .tx { flex:1; }
  .dis { font-size:12px; color:#9aa1ab; margin-top:34px; line-height:1.75; border-top:1px solid #e8eaee; padding-top:14px; }
  .hl { background:#fff9e8; }
</style>
</head>
<body>
<div class="wrap">

<h1>2024 年小盘股行情复盘</h1>
<div class="sub">样本区间 __RANGE__ ｜ 数据：腾讯财经日线（前复权）｜ 生成时间 __FETCHED__</div>

<div class="tldr">
  <ul>
    <li><b>一句话：这是一次纯粹的「小盘股结构性问题」，不是熊市普跌。</b>2024-01-02 至 02-05 的 23 个交易日里，国证2000 跌 <b>-29.29%</b>、中证1000 跌 <b>-26.67%</b>，而同期沪深300 只跌 <b>-6.10%</b>、上证50 只跌 <b>-4.06%</b>。小盘超额跌幅达 <b>-23.2 个百分点</b>。</li>
    <li><b>跌幅严格按市值排序，梯度极其干净：</b>国证2000 -29.3% ＞ 中证1000 -26.7% ＞ 中证500 -17.6% ＞ 深证成指 -15.3% ＞ 上证指数 -8.8% ＞ 沪深300 -6.1% ＞ 上证50 -4.1%。「越小跌越多」在这轮体现得比任何一次股灾都彻底。</li>
    <li><b>底部在 2024-02-05，次日即 V 型反转。</b>2/5 国证2000 单日 -7.52% 见底 5347 点，2/6 汇金宣布扩大 ETF 增持范围，当日中证1000 <b>+6.97%</b>。此后 30 个交易日国证2000 反弹 <b>+34.60%</b>。</li>
    <li><b>全年看，小盘股是输家。</b>2024 年国证2000 <b>-0.38%</b>、中证1000 +1.76%，而沪深300 <b>+16.20%</b>、上证50 +17.12%。小盘跑输大盘 <b>16 个百分点以上</b>。但从 2/5 底部持有到年末，国证2000 <b>+40.89%</b>，反而跑赢沪深300（+22.95%）。<b>同一段行情，取决于你在哪一天进场。</b></li>
    <li><b>流动性是真正的杀手。</b>暴跌末段（2/1-2/5）国证2000 成交量放大到基准的 116%，越跌越放量；而 8-9 月二次探底时萎缩到 80.7%——先恐慌抛售，后无人问津。真正的反转要等到 9/24 后的天量（国证2000 放大至 207%）。</li>
  </ul>
</div>

<h2>一、关键数据</h2>
<div class="cards">
  <div class="card lose">
    <div class="name">国证2000 · 暴跌期</div>
    <div class="big down">-29.29%</div>
    <div class="meta">2024/1/2 → 2/5<br>23 个交易日 · 低点 5347</div>
  </div>
  <div class="card lose">
    <div class="name">沪深300 · 同期</div>
    <div class="big down">-6.10%</div>
    <div class="meta">同为 23 个交易日<br>小盘超额 -23.2pct</div>
  </div>
  <div class="card win">
    <div class="name">国证2000 · 反弹期</div>
    <div class="big up">+34.60%</div>
    <div class="meta">2/5 → 3/21<br>30 个交易日</div>
  </div>
  <div class="card">
    <div class="name">国证2000 · 全年收益</div>
    <div class="big down">-0.38%</div>
    <div class="meta">跑输沪深300 达 16.6pct<br>但底部算起 +40.89%</div>
  </div>
</div>

<h2>二、全景走势：一年走出两轮完整周期</h2>
<p style="font-size:13.5px;color:#5a616c;margin-bottom:10px;">2023 年 6 月以来归一化走势（起点=100）。小盘股在 2024 年走出<b>双底结构</b>：2 月 5 日的第一只脚和 9 月中的第二只脚，中间靠 9/24 政策转向完成反转。</p>
<div id="c_main" class="chart tall"></div>
<div class="note">归一化起点为 2023-06-01。三条小盘线（国证2000／中证1000／中证500）与两条大盘线（沪深300／上证50）在暴跌期的剪刀差，直观呈现"结构性踩踏"。</div>

<h2>三、五个阶段拆解</h2>
<div id="c_seg" class="chart tall"></div>
<div class="note">按阶段看，小盘股在下跌段跌得最多（-29.3%），在反弹段涨得最多（+34.6%），在 9/24 后的爆发行情中弹性也最大（+41.1%）。<b>高波动本身就是小盘股的属性，问题只在于你能否扛过第一段。</b></div>

<h3>各阶段涨跌幅明细（%）</h3>
<table id="t_seg"></table>
<div class="note">阶段划分：前期=2023/6/1~2024/1/2；暴跌=2024/1/2~2/5；V反弹=2/5~3/21；二次探底=3/21~9/18；924暴涨=9/18~10/8；年末震荡=10/8~12/31。</div>

<h2>四、暴跌的市值梯度：越小跌越多，没有例外</h2>
<div id="c_grad" class="chart"></div>
<div class="note">统计口径：2024/1/2 收盘至各自区间最低收盘。低点日期：国证2000、中证1000、中证500、上证指数、深证成指均为 2/5；科创50、创业板指、沪深300、中证白酒为 2/2；上证50 为 1/17。</div>

<h2>五、时间线：23 个交易日发生了什么</h2>
<div class="timeline">
  <div class="row"><div class="dt">2024-01-02</div><div class="tx">中证1000 见阶段高点，暴跌起点。此时市场对"小微盘抱团"的拥挤度尚无警觉。</div></div>
  <div class="row"><div class="dt">2024-01-17</div><div class="tx">上证50 见低点（-4.06%），大盘股率先止跌；同日沪深300 单日 -2.18%。分化开始。</div></div>
  <div class="row"><div class="dt">2024-01-22</div><div class="tx">加速下跌：国证2000 <span class="down">-6.00%</span>、中证1000 -5.77%、中证500 -4.73%。雪球敲入与量化平仓的负反馈开始自我强化。</div></div>
  <div class="row"><div class="dt">2024-01-31</div><div class="tx">国证2000 再跌 -4.48%，1 月单月中证1000 累计 <span class="down">-18.72%</span>、国证2000 -19.8%。</div></div>
  <div class="row"><div class="dt">2024-02-02</div><div class="tx">科创50、创业板指、沪深300、中证白酒同日见最低点（沪深300 累计 -6.10%）。小盘股仍在下跌。</div></div>
  <div class="row hl"><div class="dt">2024-02-05</div><div class="tx"><b>恐慌顶点</b>：国证2000 单日 <span class="down">-7.52%</span>、中证1000 <span class="down">-6.16%</span>，双双收出本轮最低点（5347 / 4293）。成交量放大至基准的 116%~125%。</div></div>
  <div class="row hl"><div class="dt">2024-02-06</div><div class="tx"><b>V 型反转起点</b>：汇金公司公告扩大 ETF 增持范围，中证1000 当日 <span class="up">+6.97%</span>、国证2000 <span class="up">+5.16%</span>。中证500 更是 <span class="up">+7.75%</span>。</div></div>
  <div class="row"><div class="dt">2024-02-07~08</div><div class="tx">证监会主要负责人调整；2/8 国证2000 再涨 +6.11%。流动性危机解除，但情绪修复缓慢。</div></div>
  <div class="row"><div class="dt">2024-02-28</div><div class="tx">残余冲击：国证2000 <span class="down">-5.51%</span>、中证1000 -4.49%（量化业务收紧传闻扰动）。</div></div>
  <div class="row"><div class="dt">2024-03-21</div><div class="tx">反弹高点。自 2/5 起国证2000 <span class="up">+34.60%</span>、中证1000 +31.80%、沪深300 +11.89%。小盘弹性是大盘的 3 倍。</div></div>
  <div class="row"><div class="dt">2024-03-21~09-18</div><div class="tx">二次探底：国证2000 <span class="down">-23.88%</span>、中证1000 -22.25%。成交量萎缩到基准的 80.7%（国证2000）——<b>从恐慌抛售切换到无人问津</b>。中证500 与沪深300 的年内最低点出现在 9/13。</div></div>
  <div class="row hl"><div class="dt">2024-09-24</div><div class="tx"><b>政策转向</b>：一行一局一会联合发布会。9/30 国证2000 单日 <span class="up">+11.39%</span>（历史级涨幅），中证1000 <span class="up">+11.14%</span>。成交量放大至基准的 207%~317%。</div></div>
  <div class="row"><div class="dt">2024-10-08</div><div class="tx">情绪顶点。次日（10/9）即大幅回吐：国证2000 <span class="down">-8.38%</span>、中证1000 -7.65%、沪深300 -7.05%。</div></div>
  <div class="row"><div class="dt">2024-12-12</div><div class="tx">国证2000 创年内新高 8318 点，全年收益回到 -0.38%（收平）。</div></div>
</div>

<h2>六、成交量：流动性枯竭的三个阶段</h2>
<div id="c_vol" class="chart"></div>
<div class="note">以 2023 年 6-12 月日均成交量为基准 100%。关键差异：暴跌末段是<b>放量下跌</b>（国证2000 116%、沪深300 161%，后者对应国家队申赎大盘 ETF），二次探底是<b>缩量阴跌</b>（80.7%），924 才是<b>天量反转</b>（207%~317%）。</div>

<h2>七、全年收益对比：小盘输在哪里</h2>
<div id="c_year" class="chart"></div>
<div class="note">2024 全年（1/2~12/31）：以大盘蓝筹与高股息胜出，小盘股收平甚至下跌。<b>但若从 2/5 底部买入并持有到年末，排序完全颠倒</b>（国证2000 +40.89% vs 沪深300 +22.95%）。</div>

<h2>八、机制归因与不同之处</h2>
<div class="method">
  <p><b>1. 这轮的特殊性在于「下跌的不是市场，而是某一类股票」。</b>对比 2016 年初（熔断）与 2018 年初（美股 VIX 冲击），那两次沪深300 与小盘同步下跌，大盘跌幅甚至更大。2024 年初不同：沪深300 只跌 6.10%，上证50 只跌 4.06%，说明市场整体并未陷入系统性风险，是<b>小市值板块内部的流动性链条断裂</b>。</p>
  <p><b>2. 市场普遍归因的传导链</b>（以下为市场与媒体共识，非官方结论）：① 中证500／中证1000 相关雪球产品集中敲入，券商对冲盘被迫卖出期货与成分股；② 量化 DMA（多空收益互换）产品在下跌中被限制或降杠杆，需被动减仓；③ 微盘股策略拥挤度过高，流动性枯竭时买盘瞬间消失；④ 负反馈自我强化，形成"越跌越卖、越卖越跌"。转折点为 2/6 汇金公告扩大 ETF 增持范围。</p>
  <p><b>3. 数据上可验证的佐证。</b>① 跌幅严格按市值单调排序，是典型的"流动性折价"而非"基本面重估"；② 沪深300 在暴跌末段成交量放大到 161%，说明有大规模资金在场内承接大盘、但小盘无人接盘；③ 低点在 2/5 集中出现后，2/6 单日即出现 5%~7.75% 的报复性反弹，符合"流动性危机解除"而非"利空出尽"的特征。</p>
  <p><b>4. 后续的二次探底同样值得注意。</b>2 月的暴力反弹并未带来持续行情，3/21 至 9/18 小盘股再度下跌 23.88%，且是缩量阴跌。这说明流动性冲击留下的疤痕效应持续了半年以上，直到 9/24 政策转向才真正修复。</p>
</div>

<h2>九、可提炼的规律与风险提示</h2>
<div class="risk">
  <p><b>1. 暴跌的排序即风险的排序。</b>市值越小、量化与杠杆资金占比越高、流动性越薄，在负反馈中跌得越狠。这轮国证2000 -29.3% vs 上证50 -4.1%，差距 25 个百分点，是"同一市场、不同世界"的极端样本。</p>
  <p><b>2. 放量下跌与缩量阴跌含义不同。</b>2 月是放量恐慌（可能是危机尾声），8-9 月是缩量阴跌（震荡磨底）。真正的反转需要成交量级别的跃迁，而不是价格的止跌。</p>
  <p><b>3. 抄底小盘的赔率与代价都很高。</b>2/5 抄底到年末 +40.89%，但代价是在 23 个交易日里承受 -29% 的净值回撤，且需要精确踩在 2/5 那一天。事实上 2/5 当日国证2000 仍跌 7.52%，绝大多数买盘在当天被套。</p>
  <p><b>4. 本文为历史复盘研究，不构成任何投资建议。</b>所有数据来自公开行情接口，机制归因部分为市场共识整理，未经官方确认。历史规律不保证重演，任何据此进行的仓位决策需自行承担风险。</p>
</div>

<div class="dis">
  数据来源：腾讯财经日线（web.ifzq.gtimg.cn，前复权），区间 __RANGE__，抓取时间 __FETCHED__。<br>
  脚本：scripts/review2024_fetch.py（抓取）、scripts/review2024_analyze.py（分析）、scripts/review2024_report.py（本报告）。<br>
  注：本轮最惨烈的是"微盘股"（自由流通市值最小的数百只个股），其跌幅大于国证2000；因缺少可靠的微盘股指数历史数据，本报告以国证2000 作为小盘股的代表口径，实际极端跌幅应大于本文数值。
</div>

</div>
<script>
var D = __DATA__;

function ec(id){ return echarts.init(document.getElementById(id)); }
var RED='#d0342c', GREEN='#1e8e4e';
var COLORS = {'国证2000':'#c0392b','中证1000':'#e07b6a','中证500':'#d9a441','沪深300':'#2c6bd0','上证50':'#6b8fc9'};

(function(){
  var s = D.series.map(function(x){
    return { name:x[0], type:'line', data:x[1], showSymbol:false, smooth:false,
             lineStyle:{ width: x[0]==='国证2000'?2.6:1.8, color:COLORS[x[0]] },
             itemStyle:{ color:COLORS[x[0]] }, emphasis:{focus:'series'} };
  });
  s[0].markLine = { silent:true, symbol:'none',
      lineStyle:{ color:'#c3c8d0', type:'dashed', width:1 },
      label:{ formatter:function(p){ return p.name; }, fontSize:11, color:'#6b7380', rotate:0,
              position:'insideEndTop', distance:6 },
      data: D.events.map(function(e){ return { xAxis:e.d, name:e.t }; }) };
  ec('c_main').setOption({
    tooltip:{ trigger:'axis', valueFormatter:function(v){ return v==null?'-':v.toFixed(1); } },
    legend:{ top:6, itemWidth:14, textStyle:{fontSize:12} },
    grid:{ left:64, right:30, top:44, bottom:40 },
    xAxis:{ type:'category', data:D.dates, axisLabel:{ fontSize:10.5, interval:Math.floor(D.dates.length/10) }, axisTick:{show:false} },
    yAxis:{ type:'value', name:'基准=100', nameTextStyle:{fontSize:11}, splitLine:{lineStyle:{color:'#eef0f3'}} },
    series: s
  });
})();

(function(){
  var segs = D.segs.map(function(x){ return x[0]; });
  var names = ['国证2000','中证1000','中证500','沪深300','上证50'];
  var series = names.map(function(n){
    var row = D.seg_data[n]; if(!row) return null;
    return { name:n, type:'bar', data:row.segs,
      itemStyle:{ color:COLORS[n], borderRadius:[2,2,0,0] },
      barMaxWidth:20 };
  }).filter(Boolean);
  ec('c_seg').setOption({
    tooltip:{ trigger:'axis', valueFormatter:function(v){ return v==null?'-':(v>0?'+':'')+v+'%'; } },
    legend:{ top:6, itemWidth:14, textStyle:{fontSize:12} },
    grid:{ left:56, right:26, top:44, bottom:56 },
    xAxis:{ type:'category', data:segs, axisLabel:{ fontSize:11.5 }, axisTick:{show:false} },
    yAxis:{ type:'value', axisLabel:{formatter:'{value}%'}, splitLine:{lineStyle:{color:'#eef0f3'}} },
    series: series
  });
})();

(function(){
  var g = D.grad.slice().sort(function(a,b){ return a[2]-b[2]; });
  ec('c_grad').setOption({
    tooltip:{ trigger:'axis', axisPointer:{type:'shadow'},
      formatter:function(p){ var d=p[0]; return d.name+'<br>跌幅 <b>'+d.value+'%</b><br>低点 '+(g[d.dataIndex][3]||''); } },
    grid:{ left:96, right:70, top:20, bottom:36 },
    xAxis:{ type:'value', axisLabel:{formatter:'{value}%'}, splitLine:{lineStyle:{color:'#eef0f3'}} },
    yAxis:{ type:'category', data:g.map(function(x){return x[0];}), axisTick:{show:false}, axisLabel:{fontSize:12} },
    series:[{ type:'bar', data:g.map(function(x){ return {value:x[2],
        itemStyle:{ color: x[2]<=-25?'#1e8e4e':(x[2]<=-15?'#5aa87a':'#a8cfae'), borderRadius:[0,3,3,0] }};}),
      barMaxWidth:20,
      label:{ show:true, position:'right', formatter:function(p){ return p.value+'%'; }, fontSize:11, color:'#5a616c' } }]
  });
})();

(function(){
  var names = ['国证2000','中证1000','中证500','沪深300'];
  ec('c_vol').setOption({
    tooltip:{ trigger:'axis', valueFormatter:function(v){ return v+' (基准=100)'; } },
    legend:{ top:6, itemWidth:14, textStyle:{fontSize:12} },
    grid:{ left:56, right:26, top:44, bottom:56 },
    xAxis:{ type:'category', data:D.vol_periods, axisLabel:{ fontSize:10.5, interval:0, rotate:22 } },
    yAxis:{ type:'value', name:'相对成交量', splitLine:{lineStyle:{color:'#eef0f3'}} },
    series: names.map(function(n){
      return { name:n, type:'bar', data:D.vol[n], itemStyle:{color:COLORS[n], borderRadius:[2,2,0,0]}, barMaxWidth:20 };
    })
  });
})();

(function(){
  var names = ['国证2000','中证1000','中证500','深证成指','上证指数','沪深300','上证50','创业板指','科创50','证券公司','中证白酒'];
  var year = [], fromLow = [];
  names.forEach(function(n){
    var r = D.seg_data[n];
    year.push(r ? r.segs[6] : null);
    fromLow.push(r ? r.segs[7] : null);
  });
  ec('c_year').setOption({
    tooltip:{ trigger:'axis', valueFormatter:function(v){ return v==null?'-':(v>0?'+':'')+v+'%'; } },
    legend:{ top:6, itemWidth:14, textStyle:{fontSize:12} },
    grid:{ left:56, right:26, top:44, bottom:40 },
    xAxis:{ type:'category', data:names, axisLabel:{fontSize:11, interval:0, rotate:24}, axisTick:{show:false} },
    yAxis:{ type:'value', axisLabel:{formatter:'{value}%'}, splitLine:{lineStyle:{color:'#eef0f3'}} },
    series:[
      { name:'2024全年收益', type:'bar', data:year, barMaxWidth:20,
        itemStyle:{ borderRadius:[2,2,0,0], color:function(p){ return p.value>=0?RED:GREEN; } } },
      { name:'2/5底部持有至年末', type:'bar', data:fromLow, barMaxWidth:20,
        itemStyle:{ borderRadius:[2,2,0,0], color:'#8ab0e0' } }
    ]
  });
})();

function tbl(id, rows, cols){
  var h = '<thead><tr>' + cols.map(function(c){return '<th class="'+(c.n?'n':'')+'">'+c.t+'</th>';}).join('') + '</tr></thead><tbody>';
  rows.forEach(function(r){
    h += '<tr>' + cols.map(function(c){
      var v = c.f(r); return '<td class="'+(c.n?'n':'')+'">'+(v==null?'-':v)+'</td>';
    }).join('') + '</tr>';
  });
  document.getElementById(id).innerHTML = h + '</tbody>';
}
function sgn(v){ if(v==null) return '-'; var c = v>0?'up':(v<0?'down':''); return '<span class="'+c+'">'+(v>0?'+':'')+v.toFixed(2)+'%</span>'; }

tbl('t_seg', D.order.map(function(n){
  var r = D.seg_data[n] || {segs:[]};
  return { name:n, group:r.group, segs:r.segs };
}), [
  {t:'指数', f:function(r){return r.name;}},
  {t:'组', f:function(r){return '<span class="tag tag-gray">'+r.group+'</span>';}},
  {t:'前期', n:1, f:function(r){return sgn(r.segs[0]);}},
  {t:'暴跌', n:1, f:function(r){return sgn(r.segs[1]);}},
  {t:'V反弹', n:1, f:function(r){return sgn(r.segs[2]);}},
  {t:'二次探底', n:1, f:function(r){return sgn(r.segs[3]);}},
  {t:'924暴涨', n:1, f:function(r){return sgn(r.segs[4]);}},
  {t:'年末震荡', n:1, f:function(r){return sgn(r.segs[5]);}},
  {t:'2024全年', n:1, f:function(r){return sgn(r.segs[6]);}},
  {t:'底部至年末', n:1, f:function(r){return sgn(r.segs[7]);}}
]);
</script>
</body>
</html>
"""

html = (HTML
        .replace("__RANGE__", f"{raw['range'][0]} ~ {raw['range'][1]}")
        .replace("__FETCHED__", raw["fetched_at"])
        .replace("__DATA__", json.dumps(DATA, ensure_ascii=False)))

outp = os.path.join(REP, "review-2024-smallcap.html")
open(outp, "w", encoding="utf-8").write(html)
print("生成:", outp, len(html), "字节")

import re
js = re.findall(r"<script>(.*?)</script>", html, re.S)
if js:
    p = os.path.join(OUT, "_review2024_check.js")
    open(p, "w", encoding="utf-8").write(js[-1])
    print("JS 提取:", p)
