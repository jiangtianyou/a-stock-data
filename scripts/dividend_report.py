# -*- coding: utf-8 -*-
"""
红利指数季节性 - HTML 研报生成
输入: out/div2.json, out/div3.json, out/seasonality_stats.json
输出: reports/dividend-index-seasonality.html
"""
import sys, os, json
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")
REP = os.path.join(BASE, "reports")
os.makedirs(REP, exist_ok=True)

d2 = json.load(open(os.path.join(OUT, "div2.json"), encoding="utf-8"))
d3 = json.load(open(os.path.join(OUT, "div3.json"), encoding="utf-8"))
sea = json.load(open(os.path.join(OUT, "seasonality_stats.json"), encoding="utf-8"))

S = d2["sample"]
red_avg = d2["red_avg"]
divm = d2["div_by_month"]
gap = d2["gap"]
jun_y = d3["jun_excess_yearly"]
jun_ex = d3["jun_excess_stat"]
style = d3["style_jun"]
seg = d2.get("segments") or []

MONTHS = [f"{m}月" for m in range(1, 13)]
px_v = [r["px"] for r in red_avg]
tr_v = [r["tr"] for r in red_avg]
dv_v = [r["div"] for r in red_avg]
px_win = [r["px_win"] for r in red_avg]
tr_win = [r["tr_win"] for r in red_avg]

# 分红旬度
xun = d2["div_by_xun"]
xun_month = [round(sum(xun[f"{m}-{k}"] for k in (1, 2, 3)), 3) for m in range(1, 13)]
# 分红月度(与正文一致的口径)
dv_month = [divm["全样本"][str(m)] for m in range(1, 13)]

# 分段(中证红利)硬编码来自 analyze 输出
SEG = {"中证红利": {"a": {"6": -5.94, "7": 5.46, "12": 6.64, "1": 2.79},
                    "b": {"6": -2.28, "7": 0.10, "12": 0.16, "1": -0.95}},
       "上证红利": {"a": {"6": -6.89, "7": 5.25, "12": 6.62, "1": 2.17},
                    "b": {"6": -1.93, "7": -0.07, "12": -0.08, "1": -0.88}}}

# 分红年代
divseg = divm
ann = {k: divseg[k]["annual"] for k in ["全样本", "2006-2014", "2015-2023", "2024-2026"]}
jul_share = {k: round((divseg[k]["6"] + divseg[k]["7"]) / divseg[k]["annual"] * 100, 1)
             for k in ann}

html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>A股红利指数的季节性 · 6月魔咒的真相</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:"PingFang SC","Microsoft YaHei",sans-serif; background:#f7f8fa; color:#2b2f36; line-height:1.65; }}
  .wrap {{ max-width:1180px; margin:0 auto; padding:28px 20px 60px; }}
  h1 {{ font-size:26px; margin-bottom:6px; }}
  .sub {{ color:#8a919c; font-size:13px; margin-bottom:22px; }}
  h2 {{ font-size:19px; margin:38px 0 14px; padding-left:10px; border-left:4px solid #c0392b; }}
  h3 {{ font-size:15px; margin:20px 0 8px; color:#3a4048; }}
  .tldr {{ background:#fff; border:1px solid #e8eaee; border-left:4px solid #c0392b; border-radius:10px; padding:20px 22px; box-shadow:0 1px 3px rgba(0,0,0,.04); }}
  .tldr li {{ margin:8px 0 8px 18px; font-size:14.5px; }}
  .tldr b {{ color:#c0392b; }}
  .cards {{ display:flex; gap:14px; flex-wrap:wrap; margin:18px 0; }}
  .card {{ flex:1; min-width:196px; background:#fff; border:1px solid #e8eaee; border-radius:10px; padding:15px 17px; box-shadow:0 1px 3px rgba(0,0,0,.04); }}
  .card .name {{ font-size:13px; color:#5a616c; }}
  .card .big {{ font-size:27px; font-weight:700; margin:3px 0; }}
  .card.win {{ border-top:3px solid #d0342c; }} .card.lose {{ border-top:3px solid #1e8e4e; }}
  .card .meta {{ font-size:12px; color:#8a919c; line-height:1.6; }}
  .up {{ color:#d0342c; font-weight:600; }} .down {{ color:#1e8e4e; font-weight:600; }}
  table {{ width:100%; border-collapse:collapse; background:#fff; font-size:13px; border:1px solid #e8eaee; border-radius:8px; overflow:hidden; }}
  th {{ background:#f0f2f5; padding:8px 10px; text-align:left; font-weight:600; color:#4a505a; white-space:nowrap; }}
  td {{ padding:7px 10px; border-top:1px solid #eef0f3; }}
  tr:hover td {{ background:#fafbfc; }}
  td.n, th.n {{ text-align:right; font-variant-numeric:tabular-nums; }}
  .chart {{ width:100%; height:420px; background:#fff; border:1px solid #e8eaee; border-radius:10px; padding:10px; box-shadow:0 1px 3px rgba(0,0,0,.04); }}
  .chart.tall {{ height:520px; }}
  .note {{ font-size:12px; color:#9aa1ab; margin-top:8px; line-height:1.65; }}
  .tag {{ display:inline-block; font-size:11.5px; padding:1px 8px; border-radius:10px; margin-right:5px; }}
  .tag-red {{ background:#fdeceb; color:#c0392b; }} .tag-green {{ background:#e8f6ee; color:#1e8e4e; }}
  .tag-blue {{ background:#eaf1fd; color:#2c6bd0; }} .tag-gray {{ background:#f0f2f5; color:#5a616c; }}
  .tag-amber {{ background:#fff5e0; color:#a07000; }}
  .risk {{ background:#fff8e6; border:1px solid #f0e0b0; border-radius:10px; padding:14px 18px; margin-top:14px; font-size:13.5px; line-height:1.8; }}
  .risk b {{ color:#a07000; }}
  .concl {{ background:#fff; border:1px solid #e8eaee; border-left:4px solid #c0392b; border-radius:8px; padding:16px 20px; margin-top:14px; font-size:14px; }}
  .concl p {{ margin:9px 0; }}
  .method {{ background:#f4f8ff; border:1px solid #d8e5fb; border-radius:10px; padding:14px 18px; margin-top:14px; font-size:13px; line-height:1.8; }}
  .method b {{ color:#2c6bd0; }}
  .why {{ background:#fff; border:1px solid #e8eaee; border-radius:10px; padding:16px 20px; margin-top:12px; }}
  .why .item {{ display:flex; gap:12px; padding:11px 0; border-bottom:1px dashed #eceef2; }}
  .why .item:last-child {{ border-bottom:none; }}
  .why .no {{ flex:0 0 26px; height:26px; border-radius:50%; background:#c0392b; color:#fff; font-size:13px; font-weight:700; display:flex; align-items:center; justify-content:center; }}
  .why .bd {{ flex:1; font-size:13.8px; }}
  .why .bd b {{ color:#c0392b; }}
  .kv {{ display:flex; gap:26px; flex-wrap:wrap; font-size:13px; color:#5a616c; margin:10px 0 4px; }}
  .kv span b {{ color:#2b2f36; }}
</style></head><body><div class="wrap">

<h1>A 股红利指数的季节性</h1>
<div class="sub">样本 {S['monthly']}（{S['n_months']} 个月，{S['n_items']} 条序列；7 个红利指数价格 + 全收益配对）
&nbsp;|&nbsp; 数据源：中证指数官网日线（价格指数 / 全收益指数）&nbsp;|&nbsp; 更新 2026-09-15</div>

<div class="tldr">
  <b style="font-size:15px">结论先行</b>
  <ol>
    <li><b>有，而且红利是 A 股季节性最强的品种之一。</b>7 个红利指数 6 月收益<b>全部为负</b>，平均 <b class="down">-4.01%</b>、胜率仅 <b>30.9%</b>；在全部 81 个指数里，
        「上证红利 6 月」（t=-3.20）与「中证红利 6 月」（t=-2.95）<b>包揽负季节性第 1、2 名</b>。作为对照，全市场 6 月平均仅 -1.00%（t=-0.91，不显著）。</li>
    <li><b>但「6 月亏 4%」有三分之一是账面假象。</b>6-7 月是 A 股年报分红实施高峰，这两年两个月拿走全年 <b>73.5%</b> 的分红；
       除息当天指数点位被机械扣减，价格指数因此每月少掉约 <b>1.33%</b>。换成<b>全收益指数</b>（分红再投资），6 月跌幅从 -4.01% 收窄到 <b>-2.68%</b>，胜率从 30.9% 回到 50.0%。</li>
    <li><b>扣掉除息后，剩下的才是真季节性 —— 主因是风格轮动。</b>历史上 6 月成长风格平均 <b class="up">+3.01%</b>、红利 <b class="down">-2.80%</b>，两者差 <b>5.8 个百分点</b>；
       6 月红利相对沪深 300 的超额为 <b>-2.19%</b>（22 年里只有 8 年跑赢，p=0.018），与半年末资金面收紧（6 月中旬最弱）叠加。</li>
    <li><b>正季节性集中在 2 月与 11-12 月，但 2015 年后大幅衰减。</b>2 月 +3.34%（胜率 76.6%）其实是全市场共性（全市场 2 月 +3.43%），红利并无超额；
       而 12 月从 2005-2014 的 +6.64% 降到 2015 年后的 +0.16%，7 月从 +5.46% 降到 +0.10%，<b>「好月份」基本消失，只剩 6 月的「坏月份」还在</b>。</li>
    <li><b>7 月是「填权月」。</b>6 月除息后 7 月接力：价格 +2.29%、全收益 +3.61%、相对沪深 300 超额 +1.60%，是全年最强的月份之一 —— 6 月跌、7 月涨是配对出现的。</li>
  </ol>
</div>

<div class="cards">
  <div class="card lose"><div class="name">6 月平均收益（价格口径）</div><div class="big down">-4.01%</div>
    <div class="meta">7 个红利指数全部为负<br>胜率 30.9%（22 年约 7 年上涨）</div></div>
  <div class="card win"><div class="name">其中属于「除息」的部分</div><div class="big">1.33%</div>
    <div class="meta">占 6 月跌幅的 33%<br>换成全收益口径跌幅仅 -2.68%</div></div>
  <div class="card lose"><div class="name">6 月相对沪深 300 超额</div><div class="big down">-2.19%</div>
    <div class="meta">跑赢年份仅 8/22<br>t=-2.57&nbsp;&nbsp;p=0.018</div></div>
  <div class="card win"><div class="name">7 月全收益 / 相对超额</div><div class="big up">+3.61%</div>
    <div class="meta">超额 +1.60%，填权月<br>全年次强月份</div></div>
</div>

<h2>一、红利族 12 个月的收益画像：价格口径 vs 全收益口径</h2>
<div class="chart tall" id="c1"></div>
<div class="note">红柱为价格指数月均收益，蓝柱为全收益指数月均收益，橙色折线为该月「分红落袋」贡献（全收益 − 价格，读右轴）。
<b>6 月是唯一收益为负的月份</b>：价格口径 -4.01%、全收益口径 -2.68%，两个口径差 1.33 个百分点即为当月除息；7 月两口径差距 1.32 个百分点（分红与填权同时发生）。
1-5 月、9-12 月两个口径几乎重合，说明这些月份的涨跌与分红无关。</div>

<h2>二、除息效应：6-7 月拿走了全年 73.5% 的分红</h2>
<div class="chart" id="c2"></div>
<div class="note">A 股上市公司年报分红多在 4-5 月股东大会通过、会后两个月内实施，因此除息高峰精确落在 <b>6 月中旬至 7 月中旬</b>。
按旬拆解，除息最密集的时段依次为：7 月中旬 0.58%、6 月下旬 0.56%、7 月上旬 0.50%、6 月中旬 0.49%（每月分红率）。
红利指数成分股年化分红率 3.4%-4.0%，远高于大盘，因此这个「除息坑」是红利独有的。</div>

<h3>分红制度的年代变化</h3>
<table>
  <thead><tr><th>样本区间</th><th class="n">全年分红率</th><th class="n">6+7 月占比</th><th class="n">1 月分红</th><th class="n">9 月分红</th><th class="n">10 月分红</th><th class="n">12 月分红</th><th>特征</th></tr></thead>
  <tbody>
    <tr><td>2006-2014</td><td class="n">2.70%</td><td class="n">71.7%</td><td class="n">0.003%</td><td class="n">0.069%</td><td class="n">0.001%</td><td class="n">0.001%</td><td>仅年报分红，高度集中在 6-7 月</td></tr>
    <tr><td>2015-2023</td><td class="n">4.17%</td><td class="n">78.4%</td><td class="n">0.000%</td><td class="n">0.093%</td><td class="n">0.044%</td><td class="n">0.006%</td><td>分红率抬升，集中度反而更高</td></tr>
    <tr><td>2024-2026</td><td class="n">4.77%</td><td class="n"><b>62.4%</b></td><td class="n"><b>0.229%</b></td><td class="n"><b>0.286%</b></td><td class="n"><b>0.202%</b></td><td class="n"><b>0.154%</b></td><td>中期分红铺开，集中度首次明显下降</td></tr>
  </tbody>
</table>
<div class="note">「新国九条」推动一年多次分红后，2024 年起 1/9/10/11/12 月开始出现非零分红，6+7 月占比从 78.4% 回落到 62.4%。
<b>这意味着未来「6 月除息砸坑」的力度大概率继续减弱。</b></div>

<h2>三、把 6 月的 -4.01% 拆开看</h2>
<div class="chart" id="c3"></div>
<div class="note">瀑布图：6 月价格口径 -4.01%，可拆成「市场共性 -0.41%（沪深 300 全收益 6 月自身收益）」+「红利相对弱势 -2.27%」+「除息机械扣减 -1.33%」。
<b>只有「相对弱势」才是真正的策略风险，除息部分对应的现金已经进入持有人账户。</b></div>

<h3>6 月内的节奏：中旬最弱</h3>
<table>
  <thead><tr><th>6 月时段</th><th class="n">价格口径</th><th class="n">全收益口径</th><th class="n">其中除息</th><th>说明</th></tr></thead>
  <tbody>
    <tr><td>上旬（1-10 日）</td><td class="n down">{d2['jun_path'][0]['px']:.2f}%</td><td class="n down">{d2['jun_path'][0]['tr']:.2f}%</td><td class="n">{d2['jun_path'][0]['tr']-d2['jun_path'][0]['px']:.2f}%</td><td>基本不跌，跌幅几乎全由除息构成</td></tr>
    <tr><td>中旬（11-20 日）</td><td class="n down">{d2['jun_path'][1]['px']:.2f}%</td><td class="n down">{d2['jun_path'][1]['tr']:.2f}%</td><td class="n">{d2['jun_path'][1]['tr']-d2['jun_path'][1]['px']:.2f}%</td><td><b>真实下跌的主体</b>，全收益口径跌 {d2['jun_path'][1]['tr']:.2f}%</td></tr>
    <tr><td>下旬（21-月末）</td><td class="n down">{d2['jun_path'][2]['px']:.2f}%</td><td class="n down">{d2['jun_path'][2]['tr']:.2f}%</td><td class="n">{d2['jun_path'][2]['tr']-d2['jun_path'][2]['px']:.2f}%</td><td>半年末资金面 + 除息继续</td></tr>
  </tbody>
</table>

<h2>四、为什么是 6 月？四个原因，按证据强度排序</h2>
<div class="why">
  <div class="item"><div class="no">1</div><div class="bd">
    <b>除息日历（机械效应，解释 1.33%）</b><br>
    A 股年报分红在 4-5 月股东大会审议，规定「会后两个月内」实施，于是除息日天然挤在 6 月中旬至 7 月中旬。
    红利指数成分股恰恰是全市场分红率最高的一批（年化 3.4%-4.0%），除息密度远高于大盘，价格指数被扣得最狠。
    <span class="tag tag-blue">证据：全收益−价格差 = 分红，6 月 1.33% / 7 月 1.32%，合计占全年 73.5%</span></div></div>
  <div class="item"><div class="no">2</div><div class="bd">
    <b>风格轮动：6 月是成长月（真实原因，贡献最大）</b><br>
    2005-2026 年 6 月，成长风格指数平均 <b class="up">+3.01%</b>（创业板指、中证 1000、科技100、中证TMT、CSSW电子），
    而红利风格 <b class="down">-2.80%</b>，剪刀差 5.8 个百分点；大盘宽基 -1.35%、周期资源 -2.17%（均为价格口径）。
    历史上 6 月超额大幅为负的年份（2009 -7.2%、2019 -5.2%、2020 -5.6%、2022 -8.7%）全部是成长/主题强势反弹的月份。
    <span class="tag tag-red">证据：6 月红利跑输沪深300 达 -2.19%，胜率仅 36%</span></div></div>
  <div class="item"><div class="no">3</div><div class="bd">
    <b>半年末资金面收紧（辅助）</b><br>
    6 月末银行体系面临 MPA 考核、季末缴税与跨半年资金备付，短端利率季节性上行。红利股具有类债属性、对无风险利率敏感，
    利率抬升阶段相对估值承压。数据上 6 月<b>中旬</b>跌幅最大（全收益 -1.73%），符合季度中段资金面开始收敛的节奏。
    <span class="tag tag-amber">证据：中旬弱于上旬与下旬；属方向性推论，未做利率回归</span></div></div>
  <div class="item"><div class="no">4</div><div class="bd">
    <b>分红税与除息前后的交易行为（辅助）</b><br>
    A 股股息红利税按持股期限差异化征收（1 个月以内 20%、1 个月至 1 年 10%、超过 1 年免征），除息前后存在避税与再投资的择时行为；
    分红现金到账后也不必然立刻回流红利板块，短期内形成需求真空。
    <span class="tag tag-gray">说明：机制存在，本文未做量化归因</span></div></div>
</div>

<h2>五、逐年验证：6 月的弱势是「系统性」还是「风格性」</h2>
<div class="chart tall" id="c4"></div>
<div class="note">蓝柱为红利族平均（全收益口径）6 月收益，橙线为沪深 300 全收益 6 月收益，灰点为红利超额。
22 年中红利跑赢沪深 300 的只有 8 年（36%），平均超额 -2.19%（p=0.018）。
注意 2015 年 6 月红利超额 <b>+6.54%</b>（股灾中红利抗跌）与 2022 年 <b>-8.67%</b>（新能源反弹中红利被抽血）构成镜像 ——
<b>6 月超额的符号，本质上是「这个 6 月是不是成长行情」的函数。</b></div>

<h2>六、正季节性是否存在，以及为什么「消失了」</h2>
<table>
  <thead><tr><th>指数</th><th class="n">区间</th><th class="n">1月</th><th class="n">6月</th><th class="n">7月</th><th class="n">12月</th><th class="n">年化</th></tr></thead>
  <tbody>
    <tr><td>中证红利</td><td class="n">2005-2014</td><td class="n up">+2.79%</td><td class="n down">-5.94%</td><td class="n up">+5.46%</td><td class="n up">+6.64%</td><td class="n">20.77%</td></tr>
    <tr><td>中证红利</td><td class="n">2015-2026</td><td class="n down">-0.95%</td><td class="n down">-2.28%</td><td class="n up">+0.10%</td><td class="n up">+0.16%</td><td class="n">6.20%</td></tr>
    <tr><td>上证红利</td><td class="n">2005-2014</td><td class="n up">+2.17%</td><td class="n down">-6.89%</td><td class="n up">+5.25%</td><td class="n up">+6.62%</td><td class="n">17.51%</td></tr>
    <tr><td>上证红利</td><td class="n">2015-2026</td><td class="n down">-0.88%</td><td class="n down">-1.93%</td><td class="n down">-0.07%</td><td class="n down">-0.08%</td><td class="n">4.28%</td></tr>
  </tbody>
</table>
<div class="note">价格口径月度收益。<b>一个不对称的现象：正效应（7 月、12 月）在 2015 年后基本归零，负效应（6 月）却保留了约 40%。</b>
前者对应 2005-2014 年银行地产周期股的高波动年代；后者由分红制度与半年末资金面支撑，更稳定，因此更值得当作日历规律对待。
另需注意 2 月：红利 2 月 +3.34%、胜率 76.6%，但全市场 2 月 +3.43%，<b>红利在 2 月并无超额（+0.73%），那是全市场的春季躁动而非红利特征。</b></div>

<h2>七、对交易的含义</h2>
<div class="concl">
  <p><b>1. 不要把 6 月的价格跌幅当亏损读。</b>若用价格指数评估红利策略，每年 6-7 月会被少算约 2.7 个百分点的收益。
     判断红利是否真的走坏，必须看<b>全收益口径</b>或 ETF 的复权净值。</p>
  <p><b>2. 6 月该关注的是超额，不是绝对收益。</b>6 月红利跌 4% 里只有约 2.3% 是「跑输市场」，其余是除息与大盘共性。
     真正需要预警的信号是：<b>成长风格在 6 月显著走强</b>时，红利相对弱势会放大（2022 年 -8.67%、2026 年 -11.34% 皆为实例）。</p>
  <p><b>3. 6 月末至 7 月是历史胜率较高的观察窗口。</b>除息把价格打低、分红陆续到账，7 月全收益 +3.61%、超额 +1.60%。
     但这一组合收益中的相当部分是「填权」，属于统计规律而非因果保证，样本 22 年，2015 年后 7 月超额已明显减弱。</p>
  <p><b>4. 除息效应本身在弱化。</b>2024 年起中期分红铺开，6+7 月分红占比从 78.4% 降至 62.4%。
     未来「6 月价格坑」会变浅，季节性策略若照搬历史幅度，容易高估收益。</p>
</div>

<div class="risk">
  <b>风险与局限</b><br>
  ① 本文为历史统计特征，不是对未来的预测；季节性存在样本内挖掘风险，22 年的样本量对月度效应而言并不充裕（整体 F 检验 p 值 0.096-0.124 仅边缘显著，单月 6 月检验 p&lt;0.01 才较稳健）。<br>
  ② 全收益指数假设分红在除息日按当日收盘价即时再投资，与个人实际（分红为现金、可能拖到账、需缴税）存在差异，因此真实到手回报会略低于全收益指数。<br>
  ③ 「风格轮动是主因」基于成长/红利指数 6 月收益的横向对比与个案印证，未做多因子正交分解，不能排除其他同期变量的解释力。<br>
  ④ 2026 年 6 月红利超额 -11.34% 为历史极值，含当年特定的市场结构变化，不应线性外推。<br>
  ⑤ 本文不构成任何投资建议。
</div>

<div class="method">
  <b>方法与数据</b><br>
  · <b>数据源</b>：中证指数有限公司官网日线接口（价格指数与全收益指数配对），覆盖 7 个红利指数（中证红利/上证红利/300红利/国企红利/央企红利/红利低波/红利低波100）+ 4 个基准，日线 2005-01-04 ~ 2026-09-14。<br>
  · <b>分红贡献</b>：同一基日、同一起点的全收益指数月度收益减价格指数月度收益，等于当月分红再投资贡献（近似分红率）。<br>
  · <b>三层口径</b>：①原始月度收益 ②去年度效应（减当年 12 个月均值）③相对沪深 300 全收益的超额。<br>
  · <b>显著性</b>：对 12 个月效应做单因素方差分析（F 检验），对单月（6 月）效应做 t 检验（去年度效应口径）；6 月超额对 0 做单样本 t 检验。<br>
  · <b>交叉验证</b>：全市场 81 个指数的月份共性来自同项目既有季节性库（2000-2026，价格口径月线）。<br>
  · 明细数据：<code>out/dividend_raw.json</code>（原始日线）、<code>out/div2.json</code>、<code>out/div3.json</code>；脚本：<code>scripts/dividend_fetch.py</code> / <code>dividend_analyze2.py</code> / <code>dividend_analyze3.py</code>。
</div>

<script>
const RED='#d0342c', GREEN='#1e8e4e', BLUE='#2c6bd0', ORANGE='#e08b1a', GRAY='#8a919c';
const M={json.dumps(MONTHS, ensure_ascii=False)};
const grid={{left:55,right:55,top:50,bottom:40}};
const tt={{trigger:'axis',axisPointer:{{type:'shadow'}}}};

// 图1 价格 vs 全收益 + 分红
echarts.init(document.getElementById('c1')).setOption({{
  tooltip:tt,
  legend:{{data:['价格指数月均','全收益指数月均','分红贡献(右轴)'],top:6}},
  grid:{{left:55,right:60,top:52,bottom:40}},
  xAxis:{{type:'category',data:M}},
  yAxis:[{{type:'value',name:'收益 %',axisLabel:{{formatter:'{{value}}%'}}}},
         {{type:'value',name:'分红 %',min:0,max:1.6,interval:0.4,axisLabel:{{formatter:'{{value}}%'}}}}],
  series:[
    {{name:'价格指数月均',type:'bar',data:{json.dumps(px_v)},itemStyle:{{color:RED}},barGap:'0%'}},
    {{name:'全收益指数月均',type:'bar',data:{json.dumps(tr_v)},itemStyle:{{color:BLUE}}}},
    {{name:'分红贡献(右轴)',type:'line',yAxisIndex:1,data:{json.dumps(dv_month)},smooth:true,symbolSize:6,
      itemStyle:{{color:ORANGE}},lineStyle:{{width:2.5}},
      label:{{show:true,fontSize:11,color:ORANGE,formatter:function(p){{return p.value>=0.3?p.value.toFixed(2):'';}}}}}}
  ]
}});

// 图2 分红月份分布
echarts.init(document.getElementById('c2')).setOption({{
  tooltip:tt, grid:grid,
  xAxis:{{type:'category',data:M}},
  yAxis:{{type:'value',name:'分红贡献 %',axisLabel:{{formatter:'{{value}}%'}}}},
  series:[{{type:'bar',data:{json.dumps(dv_month)},itemStyle:{{color:function_placeholder}},
    label:{{show:true,position:'top',fontSize:11,formatter:function(p){{return p.value>=0.3?p.value.toFixed(2):''}}}}}}]
}});

// 图3 6月瀑布
echarts.init(document.getElementById('c3')).setOption({{
  tooltip:{{trigger:'axis',axisPointer:{{type:'shadow'}},formatter:function(ps){{
    const i=ps[0].dataIndex;
    const txt=['市场共性(沪深300全收益6月)','红利相对弱势','除息机械扣减','= 6月价格口径收益'];
    const v=[-0.41,-2.27,-1.33,-4.01];
    return txt[i]+'<br/><b>'+v[i].toFixed(2)+'%</b>';}}}},
  grid:{{left:60,right:40,top:40,bottom:56}},
  xAxis:{{type:'category',data:['市场共性\\n(沪深300)','红利相对弱势','除息机械扣减','= 6月价格口径'],
         axisLabel:{{fontSize:12,lineHeight:16}}}},
  yAxis:{{type:'value',name:'贡献 %',min:-4.6,max:0.2,axisLabel:{{formatter:'{{value}}%'}}}},
  series:[
    {{name:'占位',type:'bar',stack:'wf',silent:true,itemStyle:{{color:'transparent'}},data:[0,-0.41,-2.68,0]}},
    {{name:'贡献',type:'bar',stack:'wf',barWidth:48,data:[
      {{value:-0.41,itemStyle:{{color:RED}},label:{{show:true,position:'bottom',fontSize:12,formatter:'-0.41%'}}}},
      {{value:-2.27,itemStyle:{{color:RED}},label:{{show:true,position:'bottom',fontSize:12,formatter:'-2.27%'}}}},
      {{value:-1.33,itemStyle:{{color:ORANGE}},label:{{show:true,position:'bottom',fontSize:12,formatter:'-1.33%'}}}},
      {{value:-4.01,itemStyle:{{color:'#7a8593'}},label:{{show:true,position:'bottom',fontSize:12,fontWeight:'bold',formatter:'-4.01%'}}}}]}}
  ]
}});

// 图4 逐年6月
echarts.init(document.getElementById('c4')).setOption({{
  tooltip:tt,
  legend:{{data:['红利族全收益6月','沪深300全收益6月','红利超额(右轴)'],top:6}},
  grid:{{left:55,right:60,top:52,bottom:50}},
  xAxis:{{type:'category',data:{json.dumps([str(r["year"]) for r in jun_y])},axisLabel:{{rotate:45}}}},
  yAxis:[{{type:'value',name:'收益 %',axisLabel:{{formatter:'{{value}}%'}}}},
         {{type:'value',name:'超额 %',axisLabel:{{formatter:'{{value}}%'}}}}],
  series:[
    {{name:'红利族全收益6月',type:'bar',data:{json.dumps([r["tr"] for r in jun_y])},itemStyle:{{color:BLUE}}}},
    {{name:'沪深300全收益6月',type:'line',data:{json.dumps([r["bench"] for r in jun_y])},smooth:true,
      itemStyle:{{color:ORANGE}},symbolSize:6}},
    {{name:'红利超额(右轴)',type:'scatter',yAxisIndex:1,data:{json.dumps([r["ex"] for r in jun_y])},
      itemStyle:{{color:R}} ,symbolSize:9}}
  ]
}});
</script>
</div></body></html>"""

# 图2 颜色回调 & 图4 颜色修正
html = html.replace("itemStyle:{color:function_placeholder}", "itemStyle:{color:function(p){return p.value>0.5?'#d0342c':(p.value>0.15?'#e08b1a':'#c9cfd8');}}")
html = html.replace("itemStyle:{color:R} ", "itemStyle:{color:GRAY} ")

path = os.path.join(REP, "dividend-index-seasonality.html")
with open(path, "w", encoding="utf-8") as f:
    f.write(html)
print("->", path, len(html), "字节")
