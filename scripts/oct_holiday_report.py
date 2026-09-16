# -*- coding: utf-8 -*-
"""
A股国庆长假效应复盘 - 报告生成（独立链路，不与并行进程的 oct_report.py 冲突）
输入: out/oct_stats.json, out/oct_raw.json
输出: reports/国庆长假效应复盘-20260915.html
其他: out/_oct_holiday_report.js  (供 node --check 语法自检)
"""
import sys, os, json
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")
REP = os.path.join(BASE, "reports")
os.makedirs(REP, exist_ok=True)

stats = json.load(open(os.path.join(OUT, "oct_stats.json"), encoding="utf-8"))
raw = json.load(open(os.path.join(OUT, "oct_raw.json"), encoding="utf-8"))

CL = {}
for it in raw["items"]:
    s = pd.Series([r["c"] for r in it["rows"]],
                  index=[r["d"] for r in it["rows"]]).sort_index()
    CL[it["name"]] = s

SHc = CL["上证指数"]

# ---------------- 环境分档：按当年 1-8 月累计涨幅 ----------------
monthly_last = {}
for name, s in CL.items():
    ym = s.groupby(s.index.str[:7]).last()
    monthly_last[name] = ym


def pct(a, b):
    return None if not b else (a / b - 1) * 100


env_rows = []
for y in range(1997, 2026):
    try:
        base = monthly_last["上证指数"][f"{y-1}-12"]
        aug = monthly_last["上证指数"][f"{y}-08"]
        sep = pct(monthly_last["上证指数"][f"{y}-09"], aug)
        octv = pct(monthly_last["上证指数"][f"{y}-10"], monthly_last["上证指数"][f"{y}-09"])
        if sep is None or octv is None:
            continue
        ytd8 = pct(aug, base)
        tag = "强势(1-8月>+10%)" if ytd8 > 10 else ("弱势(1-8月<-10%)" if ytd8 < -10 else "震荡(-10%~+10%)")
        env_rows.append({"year": y, "ytd8": round(ytd8, 2), "sep": round(sep, 2),
                         "oct": round(octv, 2), "sum": round(sep + octv, 2), "env": tag})
    except KeyError:
        continue


def desc(vals):
    v = pd.Series([x for x in vals if x is not None], dtype=float)
    if len(v) == 0:
        return None
    return {"n": int(len(v)), "mean": round(float(v.mean()), 2),
            "median": round(float(v.median()), 2),
            "win": round(float((v > 0).mean()) * 100, 1)}


ENV_ORDER = ["强势(1-8月>+10%)", "震荡(-10%~+10%)", "弱势(1-8月<-10%)"]
env = {}
for tag in ENV_ORDER:
    sub = [r for r in env_rows if r["env"] == tag]
    if not sub:
        continue
    env[tag] = {"n": len(sub),
                "sep": desc([r["sep"] for r in sub]),
                "oct": desc([r["oct"] for r in sub]),
                "sum": desc([r["sum"] for r in sub])}

# 2026 定位
ytd8_26 = pct(monthly_last["上证指数"]["2026-08"], monthly_last["上证指数"]["2025-12"])
env_26 = ("强势(1-8月>+10%)" if ytd8_26 > 10
          else ("弱势(1-8月<-10%)" if ytd8_26 < -10 else "震荡(-10%~+10%)"))

# ---------------- 2026 各指数 9 月至今 ----------------
m2026 = []
for name, s in CL.items():
    try:
        aug = monthly_last[name]["2026-08"]
        last_d, last_c = s.index[-1], s.iloc[-1]
        m2026.append({"name": name, "last_d": last_d, "last": round(float(last_c), 2),
                      "aug31": round(float(aug), 2), "sep_mtd": round(pct(last_c, aug), 2)})
    except KeyError:
        continue
m2026.sort(key=lambda x: x["sep_mtd"])

SHdf = pd.DataFrame(next(i for i in raw["items"] if i["secid"] == "sh000001")["rows"])
SHdf = SHdf.sort_values("d").reset_index(drop=True)
last_row = SHdf.iloc[-1]
v5 = float(SHdf["v"].tail(5).mean())
v20 = float(SHdf["v"].iloc[-25:-5].mean())
recent = SHdf.tail(60)

WK_LBL = {"pre10": "节前10日", "pre5": "节前5日", "pre3": "节前3日", "pre1": "节前1日",
          "post1": "节后1日", "post3": "节后3日", "post5": "节后5日",
          "post10": "节后10日", "post20": "节后20日"}
WK_ORDER = ["pre10", "pre5", "pre3", "pre1", "post1", "post3", "post5", "post10", "post20"]

DATA = {
    "fetched_at": stats["fetched_at"],
    "win_lbl": WK_LBL, "win_order": WK_ORDER,
    "scopes": {"all": stats["holiday"], "y2000": stats["holiday_2000"], "y2010": stats["holiday_2010"]},
    "detail": stats["holiday_detail_2000"],
    "yearly": stats["yearly_detail"],
    "months": stats["single_month"],
    "volume": stats["volume"], "volume_all": stats["volume_all"],
    "half": stats["half_month"],
    "cond": stats["conditional"],
    "env": env, "env_order": ENV_ORDER, "env_rows": env_rows,
    "env_26": env_26, "ytd8_26": round(ytd8_26, 2),
    "m2026": m2026,
    "pos": {"today": last_row["d"], "close": round(float(last_row["c"]), 2),
            "sep_mtd": round(pct(last_row["c"], monthly_last["上证指数"]["2026-08"]), 2),
            "v_ratio": round(v5 / v20, 2), "v5": round(v5), "v20": round(v20)},
    "recent": {"dates": [d for d in recent["d"]],
               "close": [round(float(x), 2) for x in recent["c"]]},
}

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>A股国庆长假效应复盘：缩量、节前避险与"红十月"的失效</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:"PingFang SC","Microsoft YaHei",sans-serif; background:#f7f8fa; color:#2b2f36; line-height:1.65; }
  .wrap { max-width:1180px; margin:0 auto; padding:28px 20px 60px; }
  h1 { font-size:25px; margin-bottom:6px; }
  .sub { color:#8a919c; font-size:13px; margin-bottom:22px; }
  h2 { font-size:19px; margin:40px 0 14px; padding-left:10px; border-left:4px solid #c0392b; }
  h3 { font-size:15px; margin:22px 0 8px; color:#3a4048; }
  p { font-size:14px; margin:9px 0; }
  .tldr { background:#fff; border:1px solid #e8eaee; border-left:4px solid #c0392b; border-radius:10px; padding:20px 22px; box-shadow:0 1px 3px rgba(0,0,0,.04); }
  .tldr li { margin:10px 0 10px 18px; font-size:14.5px; }
  .tldr b { color:#c0392b; }
  .cards { display:flex; gap:14px; flex-wrap:wrap; margin:18px 0; }
  .card { flex:1; min-width:178px; background:#fff; border:1px solid #e8eaee; border-radius:10px; padding:14px 16px; box-shadow:0 1px 3px rgba(0,0,0,.04); }
  .card .name { font-size:12.5px; color:#5a616c; }
  .card .big { font-size:25px; font-weight:700; margin:3px 0; font-variant-numeric:tabular-nums; }
  .card .meta { font-size:11.5px; color:#8a919c; line-height:1.6; }
  .card.win { border-top:3px solid #d0342c; } .card.lose { border-top:3px solid #1e8e4e; }
  .card.neu { border-top:3px solid #8a919c; } .card.amb { border-top:3px solid #d9a300; }
  .up { color:#d0342c; font-weight:600; } .down { color:#1e8e4e; font-weight:600; } .flat { color:#8a919c; }
  table { width:100%; border-collapse:collapse; background:#fff; font-size:12.8px; border:1px solid #e8eaee; border-radius:8px; overflow:hidden; }
  th { background:#f0f2f5; padding:8px 9px; text-align:left; font-weight:600; color:#4a505a; white-space:nowrap; }
  td { padding:6px 9px; border-top:1px solid #eef0f3; }
  tr:hover td { background:#fafbfc; }
  td.n, th.n { text-align:right; font-variant-numeric:tabular-nums; }
  td.c, th.c { text-align:center; }
  .chart { width:100%; height:430px; background:#fff; border:1px solid #e8eaee; border-radius:10px; padding:8px; box-shadow:0 1px 3px rgba(0,0,0,.04); }
  .chart.tall { height:500px; }
  .note { font-size:12px; color:#9aa1ab; margin-top:8px; line-height:1.7; }
  .tag { display:inline-block; font-size:11.5px; padding:1px 8px; border-radius:10px; margin-right:5px; }
  .tag-red { background:#fdeceb; color:#c0392b; } .tag-green { background:#e8f6ee; color:#1e8e4e; }
  .tag-gray { background:#f0f2f5; color:#5a616c; } .tag-amber { background:#fff5e0; color:#a07000; }
  .tag-blue { background:#eaf1fd; color:#2c6bd0; }
  .risk { background:#fff8e6; border:1px solid #f0e0b0; border-radius:10px; padding:14px 18px; margin-top:14px; font-size:13.5px; line-height:1.85; }
  .risk b { color:#a07000; }
  .method { background:#f4f8ff; border:1px solid #d8e5fb; border-radius:10px; padding:14px 18px; margin-top:14px; font-size:13px; line-height:1.85; }
  .method b { color:#2c6bd0; }
  .dis { font-size:12px; color:#9aa1ab; margin-top:34px; line-height:1.75; border-top:1px solid #e8eaee; padding-top:14px; }
  .hl { background:#fff9e8; }
  .two { display:flex; gap:16px; flex-wrap:wrap; }
  .two > div { flex:1; min-width:320px; }
  code { background:#f0f2f5; padding:1px 5px; border-radius:4px; font-size:12px; }
</style>
</head>
<body>
<div class="wrap">

<h1>A股国庆长假效应复盘：缩量、节前避险与"红十月"的失效</h1>
<div class="sub">标的：上证指数为主，另用 8 个宽基 / 风格指数做横向校验 ｜ 数据：腾讯财经日线（前复权）｜ 样本区间 1990-12-19 ~ __TODAY__ ｜ 生成 __FETCH__</div>

<div class="tldr">
  <ul>
    <li><b>一句话：国庆长假效应是真的，但它是一个「节奏」现象，不是「方向」现象。</b>价格上最确定的东西——节前两周跌多涨少、节前最后一天偏红、节后首日跳空——全部集中在 <b>1~5 个交易日</b>的短窗口里；一旦拉长到月度口径，9 月（均值 +0.01%）与 10 月（-0.15%）在 12 个月里都排在中下游，<b>谈不上"金九"，也谈不上"红十月"</b>。</li>
    <li><b>唯一稳健的特征是缩量。</b>节前 5 日均量只有当年日均量的 <b>-15.8%</b>（2000 年起 26 年），全历史 -14.2%。这条在 9 个指数上方向完全一致，是整份复盘里最干净的结论。而节后并没有补偿性放量（-1.9%），<b>"节后资金回流"在量能上找不到证据</b>。</li>
    <li><b>节前两周"跌多涨少"，但均值会骗人。</b>节前 10 日：<b>中位数 -1.89%、胜率仅 34.6%</b>（2000 起），均值却只有 -0.05%——因为 2024 年节前 5 日 <b>+21.37%</b>、2008 年 +10.54% 这类右尾把均值拉平了。看均值会得出"节前无所谓"，看中位数才知道节前是偏弱的。</li>
    <li><b>节后"红包"存在，但统计上不显著，且几乎全在开市第一天。</b>2000 起节后 1 日均值 <b>+0.51%</b>、胜率 65.4%，但 <b>t 值只有 1.14（p=0.26）</b>。剔除首日跳空后，节后 5 日从 +0.60% 塌到 <b>+0.06%</b>，节后 10 日变成 <b>-0.65%</b>。<b>"持股过节"赚的是首日的情绪溢价，"节后再买"基本赚不到。</b></li>
    <li><b>真正有交易价值的是反向信号：节前越弱，节后越强。</b>节前 5 日下跌的年份（n=14），节后 5 日平均 <b>+1.52%</b>、胜率 <b>71.4%</b>；节前 5 日上涨的年份（n=12），节后 5 日平均 <b>-0.46%</b>、胜率 50%。相关系数 <b>-0.336</b>。这是全文唯一同时具备方向、幅度与胜率的可操作特征。</li>
    <li><b>"红十月"失效的真正原因不是时间，是「环境」——年内位置才是决定 10 月的关键变量。</b>按当年 1-8 月涨幅分档：<b>强势档（&gt;+10%）10 月均值 +3.20%、胜率 88.9%；震荡档 10 月均值 -0.15%、胜率仅 30.8%；弱势档（&lt;-10%）10 月均值 -4.44%、胜率 28.6%</b>。单调递进，比"哪一年"有解释力得多。<b>2026 年上证 1-8 月只涨 +0.44%，落在震荡档——该档 13 年里 10 月只有 4 次上涨。</b></li>
    <li><b>尾部风险厚且不对称。</b>10 月单月极值从 2008 年的 <b>-24.6%</b> 到 2010 年的 <b>+12.2%</b>（跨度 36.8 个百分点）；而 A 股休市 8~11 天，这期间外盘要交易 6~7 个交易日，政策与地缘事件全部落在无法调仓的持仓敞口上。<b>节前减仓的成本是确定的，不减仓的风险是不确定的。</b></li>
  </ul>
</div>

<h2>一、样本与方法</h2>
<div class="method">
  <b>窗口定义</b>：<code>T-1</code> = 节前最后一个交易日；<code>T+1</code> = 节后第一个交易日。<b>节前 N 日</b> = <code>close(T-1)/close(T-1-N)-1</code>；<b>节后 N 日</b> = <code>close(T+N)/close(T-1)-1</code>（含跳空缺口）。另有"基准 = 节后首日收盘"的 postNb 版本，用于剥离首日跳空。<br>
  <b>长假识别</b>：相邻交易日间隔 ≥ 5 个自然日、且跨 10 月 1 日的，判定为国庆长假，共识别到 <b>32 次</b>（1991–2025）。<br>
  <b>样本口径</b>：<span class="tag tag-gray">全历史 1991 起 n=32</span> 含 1996-12-16 涨跌停制度实施前的极端期（1991–1992 单月可涨 177%），仅作参考；<span class="tag tag-red">主口径 2000 起 n=26</span> 用于多数结论；<span class="tag tag-blue">近年 2010 起 n=16</span> 作对照。2026 年 10 月尚未发生，不计入统计。<br>
  <b>显著性</b>：单样本 t 检验（H₀：收益均值 = 0）。本报告对 p &gt; 0.05 的结果一律标注"不显著"，不做因果化表述。
</div>

<h2>二、结论一：缩量是唯一稳健的特征</h2>
<div class="cards">
  <div class="card lose"><div class="name">节前 5 日均量 / 当年日均量</div><div class="big down">-15.8%</div><div class="meta">2000 起 · 26 年 · 9 个指数方向一致</div></div>
  <div class="card lose"><div class="name">节前 5 日均量 / 当年日均量（全历史）</div><div class="big down">-14.2%</div><div class="meta">1991 起 · 32 年</div></div>
  <div class="card neu"><div class="name">节后 5 日均量 / 当年日均量</div><div class="big flat">-1.9%</div><div class="meta">量能回归常态，无放量</div></div>
  <div class="card neu"><div class="name">节后 6~25 日均量 / 当年日均量</div><div class="big flat">-1.5%</div><div class="meta">未见"资金大举回流"</div></div>
</div>
<p>节前缩量的幅度（-15.8%）远大于价格波动的幅度（节前 5 日中位数 -0.53%），说明<b>长假前主导市场的是"降低敞口"的行为，而不是"看空"的判断</b>——资金在降低仓位以规避休市期间的不确定性，而不是在定价一个下跌预期。这也解释了为什么价格上没有干净的下跌：卖压被同样不敢做多的买盘对冲掉了，最终表现为<b>缩量震荡</b>。而节后量能并未反弹（-1.9%），说明所谓"节后资金回流"更多是叙事而非事实。</p>

<h2>三、结论二：节前两周跌多涨少，但均值会骗人</h2>
<table>
  <thead><tr>
    <th>窗口</th>
    <th class="n">均值%<br><span style="font-weight:400;color:#8a919c">2000起</span></th>
    <th class="n">中位数%<br><span style="font-weight:400;color:#8a919c">2000起</span></th>
    <th class="n">胜率%<br><span style="font-weight:400;color:#8a919c">2000起</span></th>
    <th class="n">t 值</th><th class="n">p 值</th>
    <th class="n">均值%<br><span style="font-weight:400;color:#8a919c">全历史</span></th>
    <th class="n">中位数%<br><span style="font-weight:400;color:#8a919c">全历史</span></th>
    <th class="n">胜率%<br><span style="font-weight:400;color:#8a919c">全历史</span></th>
  </tr></thead>
  <tbody>__TBL_WINDOW__</tbody>
</table>
<div class="note">口径：上证指数。加粗行 = |t| ≥ 1.0 的窗口。全部窗口 p &gt; 0.05，即<b>无一显著</b>。</div>

<div class="chart" id="c_win"></div>
<div class="note">柱 = 均值收益（左轴）；折线 = 上涨概率（右轴）。注意"节前 10 日"的柱与折线严重背离——均值近 0 而胜率仅 34.6%，是典型的右偏分布。</div>

<h3>为什么说均值会骗人</h3>
<p>把 26 年的节前 5 日收益排一下：中位数 <b>-0.53%</b>、上涨年份 12/26（46.2%），但均值却是 <b>+0.82%</b>。差额几乎全部来自三个年份——<b>2024 年 +21.37%</b>（9/24 政策组合拳）、<b>2008 年 +10.54%</b>（9/19 印花税单边征收 + 汇金增持）、<b>2010 年 +2.59%</b>。换句话说：<b>节前行情有 46% 的概率下跌，但一旦上涨，幅度可以极大——政策底往往砸在长假前后。</b>这才是"节前避险"在数据上的真实形态：不是稳定下跌，而是<b>上涨靠事件、下跌靠惯性</b>的非对称分布。</p>

<h2>四、结论三：节后红包只在开市第一天</h2>
<p>节后窗口最容易被误读。用"基准 = 节前收盘"计算，节后 1/3/5 日看起来都不错；换一个基准就能看出问题：</p>
<table>
  <thead><tr>
    <th rowspan="2">窗口</th>
    <th colspan="4" class="c">基准 = 节前收盘（含跳空）</th>
    <th colspan="4" class="c">基准 = 节后首日收盘（剔除首日）</th>
  </tr><tr>
    <th class="n">均值%</th><th class="n">中位%</th><th class="n">胜率%</th><th class="n">t</th>
    <th class="n">均值%</th><th class="n">中位%</th><th class="n">胜率%</th><th class="n">t</th>
  </tr></thead>
  <tbody>__TBL_POST__</tbody>
</table>
<div class="note">口径：上证指数，2000 年起 26 年。右半区的窗口自节后首日收盘起算，衡量<b>首日之后</b>的续涨能力。</div>

<div class="two">
  <div>
    <h3>首日跳空贡献了多少</h3>
    <p>节后 5 日累计 <b>+0.60%</b>，其中节后首日贡献 <b>+0.51%</b>——<b>约 85% 的涨幅集中在开市第一天</b>。剔除首日后，节后 5 日只剩 <b>+0.06%</b>，节后 10 日更是 <b>-0.65%</b>。</p>
    <p>意味着：<b>想吃这个红包，就必须承担休市 8~11 天的全部不确定性</b>。而首日跳空本身并不便宜——2008 年节后首日 <b>-5.23%</b>、2018 年 <b>-3.72%</b>，一次就能吞掉 5~7 年的红包期望。</p>
  </div>
  <div>
    <h3>为什么首日之后会走弱</h3>
    <p>A 股收假后第 5~10 个交易日，正好落在 <b>三季报预告密集披露 + 9 月宏观数据落地</b>的窗口。节前被压制的利空在这时集中释放，而"假期情绪"已经消化完毕。数据上，10 月呈现<b>前强后弱</b>的月内结构：上半月（含节后首周）均值 <b>+0.16%</b>、胜率 57.7%；下半月均值 <b>-0.58%</b>、胜率 46.2%。</p>
  </div>
</div>

<h2>五、结论四：真正的信号是"节前弱 → 节后强"</h2>
<p>把所有窗口两两做相关性检验后，只有一组关系稳定且可用：<b>节前 5 日与节后 5 日负相关，系数 -0.336</b>。分组看更直观：</p>
<div class="cards">
  <div class="card win"><div class="name">节前 5 日下跌的年份 → 节后 5 日</div><div class="big up">+1.52%</div><div class="meta">胜率 71.4%（n=14）｜ 2000 起</div></div>
  <div class="card lose"><div class="name">节前 5 日上涨的年份 → 节后 5 日</div><div class="big down">-0.46%</div><div class="meta">胜率 50.0%（n=12）｜ 2000 起</div></div>
  <div class="card amb"><div class="name">9 月涨跌 → 10 月涨跌 相关系数</div><div class="big flat">0.03</div><div class="meta">≈ 零相关，9 月不预测 10 月</div></div>
</div>
<div class="chart tall" id="c_scatter"></div>
<div class="note">横轴 = 节前 5 日收益，纵轴 = 节后 5 日收益（均为 %，2000 年起 26 年）。虚线为最小二乘拟合线，斜率向下即负相关。左上角（节前大跌、节后大涨）的样本密度明显高于右下角。</div>

<p>这个负相关有两层解释。第一层是<b>均值回归</b>：节前的下跌如果由避险行为驱动（而非基本面恶化），那么假期结束、避险需求消退，价格自然回补。第二层是<b>政策时点</b>：历史上多次政策底都出现在长假前后（2008/9、2024/9），<b>节前杀跌本身可能是政策干预的前兆</b>。</p>
<p>反过来看，<b>"9 月跌则 10 月红"这个流传很广的说法，相关系数只有 0.03，等于没有</b>：9 月涨的年份 10 月均值 +1.23%（胜率 50.0%，n=14），9 月跌的年份 10 月均值 -1.44%（胜率 46.7%，n=15）——方向甚至是一致的（9 月跌则 10 月也偏弱），只是弱到不可用。</p>

<h2>六、结论五："红十月"失效的真正原因——环境，而不是年份</h2>
<p class="hl" style="padding:10px 12px;border-radius:8px;font-size:14px">这是本复盘里最有价值的一节。<b>"红十月"作为一个时间标签是无解释力的：它在 1997–2009 年不成立（均值 -1.69%、胜率 38.5%），只在 2010–2019 年成立（+2.52%、胜率 70%），2020 年后又反转（-1.25%、胜率 33.3%）。但如果我们换一个分类变量——把年份按<b>「当年 1-8 月的累计涨幅」</b>分成强势 / 震荡 / 弱势三档，10 月的表现立刻变得单调且有序：</p>
<table>
  <thead><tr>
    <th>环境档（按当年 1-8 月涨幅）</th><th class="n">n</th>
    <th class="n">9月均值%</th><th class="n">9月中位%</th><th class="n">9月胜率%</th>
    <th class="n">10月均值%</th><th class="n">10月中位%</th><th class="n">10月胜率%</th>
    <th class="n">9+10均值%</th><th class="n">9+10胜率%</th>
  </tr></thead>
  <tbody>__TBL_ENV__</tbody>
</table>
<div class="note">口径：上证指数，1997–2025 共 29 年。<b>强势</b> = 1-8 月累涨 &gt; +10%；<b>震荡</b> = -10% ~ +10%；<b>弱势</b> = &lt; -10%。</div>

<div class="chart" id="c_env"></div>
<div class="note">同一批年份、同一个 10 月，只是换了一个分类变量，10 月胜率就从 88.9% 单调降到 28.6%。<b>决定 10 月的不是"十月"这两个字，而是市场在 9 月底处于什么位置。</b></div>

<p>读法是清晰的：<b>年内已经走强的市场，10 月延续的概率极高（9 年里 8 次上涨）；年内走弱的市场，10 月继续下跌（7 年里 5 次下跌，均值 -4.44%，含 2008 年 -24.63%、2018 年 -7.75% 这样的加速下跌）。</b>机制上说得通——10 月是三季报验证期叠加年末流动性预期开始定价的时点，强势市场有盈利与资金的双重支撑，弱势市场则面临"业绩不及预期 + 机构年末保收益"的双杀。</p>
<p>而"红十月"在 2010 年代成立、在 2020 年代失效，恰好对应的是<b>环境档位分布的变化</b>：2010 年代后半段（2014/2015/2019）多次落入强势或高位震荡档；2020 年以来（2021 震荡、2022 弱势、2023 震荡、2024 震荡、2025 强势）则分散在震荡与弱势档，其中震荡档的 10 月胜率只有 30.8%。<b>用一个固定日历标签去套不同的市场环境，是季节性研究最典型的刻舟求剑。</b></p>

<h3>对照：9 / 10 月在 12 个月里的真实位置</h3>
<div class="chart" id="c_month"></div>
<div class="note">上证指数 1997 年起各月平均涨跌（%）。<b>真正强的月份是 2 月（+2.46%、胜率 73.3%、t=2.89，全表唯一统计显著）、4 月（+2.27%）、12 月（+1.79%）、3 月（+1.42%）、11 月（+1.08%）</b>；弱的月份是 8 月（-1.11%）、6 月（-0.41%）、10 月（-0.15%）。9 月均值 +0.01%、中位数 -0.30%、胜率 48.3%，基本"无色"。</div>
<p>换言之：<b>9-10 月既不是季节性的高地，也不是洼地，而是一段"过渡带"。</b>这也与年内高低点的分布吻合——34 个完整年度里，9 月只出现过 1 次年内最高点和 1 次最低点，10 月是 2 次和 3 次；年内低点最集中的月份是 <b>1 月（8 次）</b>、12 月与 2 月（各 4 次）。把长假当作方向性拐点的依据，在数据上找不到支持。</p>

<h2>七、横向校验：9 个指数的一致性与分歧</h2>
<table>
  <thead><tr><th>指数</th><th class="n">9 月均值%</th><th class="n">9 月中位%</th><th class="n">9 月胜率%</th><th class="n">10 月均值%</th><th class="n">10 月中位%</th><th class="n">10 月胜率%</th><th class="n">n</th></tr></thead>
  <tbody>__TBL_CROSS__</tbody>
</table>
<div class="note">口径：各指数 2000 年起、至 2026-08 的月度收益。中证1000 / 中证全指 / 中证500 可用样本不足 20 年，仅作方向参考。</div>
<p>跨指数看下来，<b>没有干净的"节后小盘更强"结论</b>：10 月创业板指 +1.49%（胜率 56.2%）、中证1000 +1.19%（但胜率仅 45.5%）、中证500 却是 -0.67%（胜率 42.1%）；大盘侧上证50 +0.11%（胜率 59.1%）、沪深300 +0.19%（胜率 57.1%）。看中位数则沪深300（+1.89%）与上证50（+1.73%）明显好于创业板指（+0.22%）。<b>样本小 + 方向分歧大，这个维度上不应下结论</b>——它的价值在于说明：长假效应是<b>全市场层面的风险偏好现象</b>，而不是某一类市值风格的特征。</p>

<h2>八、逐年明细：26 次长假的完整记录</h2>
<table>
  <thead><tr>
    <th class="c">年份</th><th class="c">节前最后交易日</th><th class="c">节后首日</th><th class="n">休市天</th>
    <th class="n">节前5日%</th><th class="n">节前1日%</th>
    <th class="n">节后1日%</th><th class="n">节后5日%</th><th class="n">节后10日%</th><th class="n">节后20日%</th>
  </tr></thead>
  <tbody>__TBL_DETAIL__</tbody>
</table>
<div class="note">口径：上证指数，2000 年起 26 次。<span class="hl">黄底</span> = 节后 20 日跌幅超过 5%。<b>2008 年（-24.63%）与 2018 年（-5.13%）是两次典型的"假期利空"</b>——前者撞上全球金融危机，后者撞上中美贸易摩擦升级与美股大跌。另可注意节后 5 日为负的 9 个年份里，有 6 个的节前 5 日是上涨的。</div>

<h2>九、2026 年当下：位置与时间表</h2>
<div class="cards">
  <div class="card amb"><div class="name">最新收盘（__TODAY__）</div><div class="big">__CLOSE__</div><div class="meta">上证指数</div></div>
  <div class="card lose"><div class="name">9 月至今</div><div class="big down">__SEPCHG__</div><div class="meta">相对 8/31 收盘</div></div>
  <div class="card amb"><div class="name">1-8 月累计涨幅 → 环境档</div><div class="big">__YTD8__</div><div class="meta">__ENV26__</div></div>
  <div class="card neu"><div class="name">节前 5 日均量 / 前 20 日均量</div><div class="big flat">__VRATIO__</div><div class="meta">缩量尚未出现（历史节前为 -15.8%）</div></div>
</div>

<h3>2026 年中秋 + 国庆放假安排（依据：国办发明电〔2025〕7 号，2025-11-04）</h3>
<table>
  <thead><tr><th class="c">日期</th><th class="c">星期</th><th class="c">A 股</th><th>说明</th></tr></thead>
  <tbody>
    <tr><td class="c">2026-09-25 ~ 09-27</td><td class="c">五 ~ 日</td><td class="c"><span class="tag tag-red">休市</span></td><td>中秋节放假 3 天（<b>9/25 周五单独休市</b>，与国庆不连休）</td></tr>
    <tr><td class="c">2026-09-28 ~ 09-30</td><td class="c">一 ~ 三</td><td class="c"><span class="tag tag-green">交易</span></td><td><b>9/30（周三）为节前最后一个交易日</b>；节前 10 日窗口 = 9/16 ~ 9/30</td></tr>
    <tr><td class="c">2026-10-01 ~ 10-07</td><td class="c">四 ~ 三</td><td class="c"><span class="tag tag-red">休市</span></td><td>国庆节放假调休 7 天</td></tr>
    <tr><td class="c">2026-10-08</td><td class="c">四</td><td class="c"><span class="tag tag-green">交易</span></td><td><b>节后首个交易日</b>；本周仅 10/8、10/9 两个交易日</td></tr>
    <tr><td class="c">2026-10-10</td><td class="c">六</td><td class="c"><span class="tag tag-gray">非交易日</span></td><td>调休上班日，但周六不交易</td></tr>
  </tbody>
</table>
<div class="note">休市期间（10/1–10/7）外盘约有 <b>6 个交易日</b>（美股 5 个、港股 4 个，港股通同步关闭），事件风险全部落在无法调仓的持仓敞口上。9/20（周日）虽为调休上班日，但不影响 A 股交易。</div>

<h3>2026 年 9 月各指数表现（截至 __TODAY__）</h3>
<table>
  <thead><tr><th>指数</th><th class="n">8/31 收盘</th><th class="n">最新收盘</th><th class="n">9 月至今%</th></tr></thead>
  <tbody>__TBL_M2026__</tbody>
</table>
<div class="note">9 月呈现<b>小盘 / 成长跌幅大于大盘</b>的格局：创业板指 -5.55%、中证500 -4.91%，而上证50 -3.08%、沪深300 -3.78%。这与"节前避险先杀高波动资产"的行为模式一致。</div>

<div class="chart" id="c_recent"></div>
<div class="note">上证指数近 60 个交易日收盘（截至 __TODAY__）。</div>

<h3>把统计套到 2026 上的推演（仅作参考，不构成任何建议）</h3>
<p><b>匹配之处</b>：9 月已跌 __SEPCHG__，处于"节前 20 日"窗口的后半段，方向上与历史上"节前偏弱"的样本一致。若剩余窗口继续走弱至节前 5 日收跌，则进入"节后 5 日 +1.52%、胜率 71.4%"的经验区间。<br>
<b>不匹配之处有三</b>：
① <b>缩量尚未出现</b>——节前 5 日量能 / 前 20 日量能 = __VRATIO__，而历史节前 5 日相对当年日均量为 -15.8%，说明避险行为还没发生或尚未体现到量能；
② <b>环境档位不利</b>——2026 年上证 1-8 月仅 __YTD8__，落在震荡档，该档 10 月胜率只有 30.8%（13 年仅 4 次上涨）、中位数为负。<b>这是与"持股过节等红包"最冲突的一条证据</b>；
③ <b>单年样本噪声极大</b>——26 年样本里节后 5 日的标准差约 3.5%，用 ±1.5% 的均值预测单一年份，信噪比极低；而历史 10 月极值跨度是 +12.2% 到 -24.6%。</p>

<h2>十、风险提示与局限</h2>
<div class="risk">
  <b>1. 样本量根本不足。</b>国庆长假一年只有一次，26 年样本对"节后 5 日 +0.60%"这种量级的效应来说过于稀薄——<b>本文所有窗口的 p 值都大于 0.05</b>，因此所有结论都不能称为"统计显著"，只能称为"经验倾向"。<br>
  <b>2. 均值受极端年份污染严重。</b>2024 年（节前 5 日 +21.37%）、2008 年（+10.54%）、2010 年（10 月 +12.17%）三个样本足以改变任何窗口的均值符号。本文关键结论均以<b>中位数 + 胜率</b>交叉验证，但不排除仍有未被识别的杠杆点。<br>
  <b>3. 环境分档是事后分类，存在前视偏差风险。</b>"1-8 月涨幅"在 9 月底是已知的，用于当期判断不构成前视；但用 29 年样本得到的档位胜率（如强势档 88.9%）本身是<b>样本内拟合</b>，且强势档只有 9 个样本。<b>它解释历史的能力，强于预测未来的能力。</b><br>
  <b>4. 制度的断层未处理。</b>1996-12-16 涨跌停制度、2005 年股权分置改革、2010 年股指期货、2016 年熔断与注册制、2019 年科创板、2023 年全面注册制——市场结构在 30 年里多次断裂。分年代 / 分环境拆解只能部分缓解，不能消除。<br>
  <b>5. 数据口径。</b>指数为价格指数、前复权，<b>不含分红再投资收益</b>，会系统性低估长期收益（对单月窗口影响很小，对年度口径的对比有影响）。成交量单位在不同指数间不统一，量能分析已按各指数自身的当年日均量做归一化。<br>
  <b>6. 这是统计描述，不是交易建议。</b>本报告不预测 2026 年 10 月涨跌。任何基于"历史胜率"的仓位决策都需要额外纳入：当前估值分位、盈利周期位置、政策周期、筹码结构、外盘状态、汇率与流动性——这些都不在本文的变量集内。<br>
  <b>7. 季节性规律会自我消解。</b>如果足够多的资金认同"节前跌、节后涨"，节前抛压会提前（削弱节前跌幅），节后买盘也会提前（削弱节后涨幅）。<b>季节性本身就是被套利掉的规律</b>——这可能是 2020 年后 10 月收益转负的原因之一，也意味着 2010 年代的经验不能线性外推。
</div>

<div class="dis">
  数据来源：腾讯财经日线接口（<code>web.ifzq.gtimg.cn</code>，前复权），抓取时间 __FETCH__，样本区间 1990-12-19 ~ __TODAY__。<br>
  节假日安排依据：国务院办公厅《关于 2026 年部分节假日安排的通知》（国办发明电〔2025〕7 号，2025-11-04 发布）。交易所具体休市安排以沪深交易所公告为准。<br>
  统计方法：单样本 t 检验；窗口收益按交易日计数；相关性为 Pearson 系数；环境分档按当年 1-8 月累计涨幅。<br>
  本报告为历史数据统计描述，不构成任何投资建议。历史规律不代表未来表现。
</div>

</div>
<script>
var D = __DATA__;
var RED = '#d0342c', GREEN = '#1e8e4e', GRAY = '#8a919c', AMBER = '#d9a300';

function fmt(v) { return (v > 0 ? '+' : '') + v.toFixed(2); }
function colorOf(v) { return v > 0 ? RED : (v < 0 ? GREEN : GRAY); }
function chart(id) {
  var c = echarts.init(document.getElementById(id));
  window.addEventListener('resize', function () { c.resize(); });
  return c;
}

/* 1. 窗口收益全景 */
(function () {
  var order = D.win_order, s2 = D.scopes.y2000, sA = D.scopes.all;
  var labs = order.map(function (k) { return D.win_lbl[k]; });
  var mean2 = order.map(function (k) { return s2[k] ? s2[k].mean : null; });
  var win2 = order.map(function (k) { return s2[k] ? s2[k].win : null; });
  var med2 = order.map(function (k) { return s2[k] ? s2[k].median : null; });
  var meanA = order.map(function (k) { return sA[k] ? sA[k].mean : null; });
  chart('c_win').setOption({
    title: { text: '节前 / 节后各窗口收益（上证指数，2000 年起）', left: 'center', top: 6, textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' },
      formatter: function (ps) {
        var i = ps[0].dataIndex, s = s2[order[i]];
        return labs[i] + '<br>均值 ' + fmt(s.mean) + '%　中位数 ' + fmt(s.median) + '%<br>胜率 ' + s.win + '%　t = ' + s.t + '　p = ' + s.p + '<br>n = ' + s.n;
      } },
    legend: { top: 32, data: ['均值(2000起)', '中位数(2000起)', '均值(全历史)', '胜率(2000起)'] },
    grid: { left: 64, right: 64, top: 78, bottom: 46 },
    xAxis: { type: 'category', data: labs, axisLabel: { fontSize: 11.5 } },
    yAxis: [
      { type: 'value', name: '收益 %', axisLabel: { formatter: '{value}%' }, splitLine: { lineStyle: { color: '#eef0f3' } } },
      { type: 'value', name: '胜率 %', min: 0, max: 100, axisLabel: { formatter: '{value}%' }, splitLine: { show: false } }
    ],
    series: [
      { name: '均值(2000起)', type: 'bar', barWidth: 26, data: mean2,
        itemStyle: { color: function (p) { return colorOf(p.value); } },
        label: { show: true, position: 'top', fontSize: 10.5, formatter: function (p) { return fmt(p.value) + '%'; } } },
      { name: '中位数(2000起)', type: 'bar', barWidth: 26, data: med2,
        itemStyle: { color: 'rgba(140,150,165,.35)' } },
      { name: '均值(全历史)', type: 'scatter', symbolSize: 9, data: meanA, itemStyle: { color: '#2c6bd0' } },
      { name: '胜率(2000起)', type: 'line', yAxisIndex: 1, data: win2, smooth: true,
        lineStyle: { width: 2, color: AMBER }, itemStyle: { color: AMBER }, symbolSize: 7 }
    ]
  });
})();

/* 2. 散点 节前5 vs 节后5 */
(function () {
  var pts = D.detail.map(function (h) { return [h.pre5, h.post5, h.year]; });
  var xs = pts.map(function (p) { return p[0]; }), ys = pts.map(function (p) { return p[1]; });
  var n = xs.length, mx = 0, my = 0, i, num = 0, den = 0;
  for (i = 0; i < n; i++) { mx += xs[i]; my += ys[i]; }
  mx /= n; my /= n;
  for (i = 0; i < n; i++) { num += (xs[i] - mx) * (ys[i] - my); den += (xs[i] - mx) * (xs[i] - mx); }
  var b = num / den, a = my - b * mx;
  var x0 = Math.min.apply(null, xs), x1 = Math.max.apply(null, xs);
  chart('c_scatter').setOption({
    title: { text: '节前 5 日 vs 节后 5 日（2000 年起 26 年，Pearson 相关系数 -0.336）', left: 'center', top: 6, textStyle: { fontSize: 14 } },
    tooltip: { formatter: function (p) { return p.data[2] + ' 年<br>节前 5 日 ' + fmt(p.data[0]) + '%<br>节后 5 日 ' + fmt(p.data[1]) + '%'; } },
    grid: { left: 68, right: 46, top: 58, bottom: 54 },
    xAxis: { type: 'value', name: '节前 5 日 %', nameLocation: 'middle', nameGap: 30,
      axisLabel: { formatter: '{value}%' }, splitLine: { lineStyle: { color: '#eef0f3' } } },
    yAxis: { type: 'value', name: '节后 5 日 %', nameGap: 22, axisLabel: { formatter: '{value}%' }, splitLine: { lineStyle: { color: '#eef0f3' } } },
    series: [{
      type: 'scatter', data: pts, symbolSize: 12,
      itemStyle: { color: function (p) { return colorOf(p.data[1]); }, opacity: .82 },
      label: { show: true, position: 'right', fontSize: 10, color: '#8a919c', formatter: function (p) { return p.data[2]; } },
      markLine: { silent: true, symbol: 'none', lineStyle: { color: '#c8cdd6', type: 'solid', width: 1 },
        data: [{ xAxis: 0 }, { yAxis: 0 }], label: { show: false } }
    }, {
      type: 'line', data: [[x0, a + b * x0], [x1, a + b * x1]], showSymbol: false,
      lineStyle: { color: '#2c6bd0', width: 2, type: 'dashed' }, silent: true
    }]
  });
})();

/* 3. 环境分档 */
(function () {
  var tags = D.env_order;
  var n9 = tags.map(function (t) { return D.env[t].sep.mean; });
  var n10 = tags.map(function (t) { return D.env[t].oct.mean; });
  var w10 = tags.map(function (t) { return D.env[t].oct.win; });
  var m10 = tags.map(function (t) { return D.env[t].oct.median; });
  var nn = tags.map(function (t) { return D.env[t].n; });
  chart('c_env').setOption({
    title: { text: '按「当年 1-8 月涨幅」分档后的 9 / 10 月表现（上证指数，1997–2025）', left: 'center', top: 6, textStyle: { fontSize: 13.5 } },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' },
      formatter: function (ps) {
        var i = ps[0].dataIndex;
        return tags[i] + '　n=' + nn[i] +
          '<br>9 月 均值 ' + fmt(n9[i]) + '%' +
          '<br>10 月 均值 ' + fmt(n10[i]) + '%　中位数 ' + fmt(m10[i]) + '%　胜率 ' + w10[i] + '%';
      } },
    legend: { top: 32, data: ['9 月均值', '10 月均值', '10 月中位数', '10 月胜率'] },
    grid: { left: 70, right: 70, top: 82, bottom: 66 },
    xAxis: { type: 'category', data: tags, axisLabel: { fontSize: 11.5, lineHeight: 16,
      formatter: function (v, i) { return v + '\n10月胜率 ' + w10[i] + '%'; } } },
    yAxis: [
      { type: 'value', name: '均值 %', axisLabel: { formatter: '{value}%' }, splitLine: { lineStyle: { color: '#eef0f3' } } },
      { type: 'value', name: '胜率 %', min: 0, max: 100, axisLabel: { formatter: '{value}%' }, splitLine: { show: false } }
    ],
    series: [
      { name: '9 月均值', type: 'bar', barWidth: 26, data: n9,
        itemStyle: { color: 'rgba(44,107,208,.55)' },
        label: { show: true, position: 'top', offset: [-21, 0], fontSize: 10.5, formatter: function (p) { return fmt(p.value) + '%'; } } },
      { name: '10 月均值', type: 'bar', barWidth: 26, data: n10,
        itemStyle: { color: function (p) { return colorOf(p.value); } },
        label: { show: true, position: 'top', offset: [21, 0], fontSize: 11, fontWeight: 'bold', formatter: function (p) { return fmt(p.value) + '%'; } } },
      { name: '10 月中位数', type: 'scatter', symbolSize: 11, data: m10, itemStyle: { color: '#3a4048' } },
      { name: '10 月胜率', type: 'line', yAxisIndex: 1, data: w10, smooth: true,
        lineStyle: { width: 2, color: AMBER }, itemStyle: { color: AMBER }, symbolSize: 8,
        label: { show: false },
        endLabel: { show: false } }
    ]
  });
})();

/* 4. 12 个月季节性 */
(function () {
  var labs = [], vs = [], med = [], win = [];
  for (var m = 1; m <= 12; m++) {
    var c = D.months[String(m)];
    labs.push(m + '月'); vs.push(c.mean); med.push(c.median); win.push(c.win);
  }
  chart('c_month').setOption({
    title: { text: '上证指数 12 个月平均涨跌（1997 年起，%）', left: 'center', top: 6, textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' },
      formatter: function (ps) {
        var i = ps[0].dataIndex, c = D.months[String(i + 1)];
        return labs[i] + '<br>均值 ' + fmt(c.mean) + '%　中位数 ' + fmt(c.median) + '%<br>胜率 ' + c.win + '%　t = ' + c.t + '　n = ' + c.n;
      } },
    legend: { top: 32, data: ['均值', '中位数', '胜率'] },
    grid: { left: 62, right: 62, top: 78, bottom: 44 },
    xAxis: { type: 'category', data: labs, axisLabel: { fontSize: 11.5 } },
    yAxis: [
      { type: 'value', name: '收益 %', axisLabel: { formatter: '{value}%' }, splitLine: { lineStyle: { color: '#eef0f3' } } },
      { type: 'value', name: '胜率 %', min: 0, max: 100, axisLabel: { formatter: '{value}%' }, splitLine: { show: false } }
    ],
    series: [
      { name: '均值', type: 'bar', barWidth: 22, data: vs,
        itemStyle: { color: function (p) { return (p.dataIndex === 8 || p.dataIndex === 9) ? colorOf(p.value) : 'rgba(150,160,175,.45)'; } },
        label: { show: true, position: 'top', fontSize: 10, formatter: function (p) { return fmt(p.value); } } },
      { name: '中位数', type: 'scatter', symbolSize: 8, data: med, itemStyle: { color: '#3a4048' } },
      { name: '胜率', type: 'line', yAxisIndex: 1, data: win, smooth: true,
        lineStyle: { width: 1.8, color: AMBER }, itemStyle: { color: AMBER }, symbolSize: 5 }
    ]
  });
})();

/* 5. 近 60 日 */
(function () {
  chart('c_recent').setOption({
    title: { text: '上证指数近 60 个交易日（截至 ' + D.pos.today + '）', left: 'center', top: 6, textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis', formatter: function (ps) { return ps[0].axisValue + '<br>收盘 ' + ps[0].data; } },
    grid: { left: 66, right: 40, top: 46, bottom: 46 },
    xAxis: { type: 'category', data: D.recent.dates, axisLabel: { fontSize: 10, interval: 9 } },
    yAxis: { type: 'value', scale: true, splitLine: { lineStyle: { color: '#eef0f3' } } },
    series: [{ type: 'line', data: D.recent.close, showSymbol: false, smooth: true,
      lineStyle: { color: '#2c6bd0', width: 2 }, areaStyle: { color: 'rgba(44,107,208,.08)' } }]
  });
})();
</script>
</body>
</html>
"""


def cls(v):
    if v is None:
        return "flat"
    if v > 0:
        return "up"
    if v < 0:
        return "down"
    return "flat"


def row_window(k):
    s2, sA = scopes_y2000[k], stats["holiday"][k]
    mark = ' style="font-weight:600;background:#fffdf5"' if abs(s2["t"]) >= 1.0 else ""
    return (f'<tr{mark}><td>{WK_LBL[k]}</td>'
            f'<td class="n {cls(s2["mean"])}">{s2["mean"]:+.2f}</td>'
            f'<td class="n {cls(s2["median"])}">{s2["median"]:+.2f}</td>'
            f'<td class="n">{s2["win"]:.1f}</td>'
            f'<td class="n">{s2["t"]:.2f}</td><td class="n">{s2["p"]:.3f}</td>'
            f'<td class="n {cls(sA["mean"])}">{sA["mean"]:+.2f}</td>'
            f'<td class="n {cls(sA["median"])}">{sA["median"]:+.2f}</td>'
            f'<td class="n">{sA["win"]:.1f}</td></tr>')


def row_post(n):
    a, b = scopes_y2000[f"post{n}"], scopes_y2000[f"post{n}b"]
    return (f'<tr><td>{WK_LBL[f"post{n}"]}</td>'
            f'<td class="n {cls(a["mean"])}">{a["mean"]:+.2f}</td>'
            f'<td class="n">{a["median"]:+.2f}</td><td class="n">{a["win"]:.1f}</td>'
            f'<td class="n">{a["t"]:.2f}</td>'
            f'<td class="n {cls(b["mean"])}">{b["mean"]:+.2f}</td>'
            f'<td class="n">{b["median"]:+.2f}</td><td class="n">{b["win"]:.1f}</td>'
            f'<td class="n">{b["t"]:.2f}</td></tr>')


def row_env(tag):
    e = env[tag]
    s, o, u = e["sep"], e["oct"], e["sum"]
    hi = tag == env_26
    mark = ' style="font-weight:600;background:#fffdf5"' if hi else ""
    tail = ' <span class="tag tag-red">← 2026 落此档</span>' if hi else ""
    return (f'<tr{mark}><td>{tag}{tail}</td><td class="n">{e["n"]}</td>'
            f'<td class="n {cls(s["mean"])}">{s["mean"]:+.2f}</td><td class="n {cls(s["median"])}">{s["median"]:+.2f}</td><td class="n">{s["win"]:.1f}</td>'
            f'<td class="n {cls(o["mean"])}">{o["mean"]:+.2f}</td><td class="n {cls(o["median"])}">{o["median"]:+.2f}</td><td class="n">{o["win"]:.1f}</td>'
            f'<td class="n {cls(u["mean"])}">{u["mean"]:+.2f}</td><td class="n">{u["win"]:.1f}</td></tr>')


CROSS_ORDER = ["上证指数", "上证50", "沪深300", "中证500", "中证1000", "中证全指",
               "创业板指", "深证成指", "中证红利"]


def row_cross(n):
    e = stats["cross_index"].get(n)
    if not e:
        return ""
    s, o = e.get("9月"), e.get("10月")
    if not s or not o:
        return ""
    return (f'<tr><td>{n}</td>'
            f'<td class="n {cls(s["mean"])}">{s["mean"]:+.2f}</td><td class="n">{s["median"]:+.2f}</td><td class="n">{s["win"]:.1f}</td>'
            f'<td class="n {cls(o["mean"])}">{o["mean"]:+.2f}</td><td class="n">{o["median"]:+.2f}</td><td class="n">{o["win"]:.1f}</td>'
            f'<td class="n">{s["n"]}</td></tr>')


def row_detail(h):
    hl = ' class="hl"' if h["post20"] < -5 else ""
    return (f'<tr{hl}><td class="c">{h["year"]}</td><td class="c">{h["last_day"]}</td><td class="c">{h["first_day"]}</td>'
            f'<td class="n">{h["gap_days"]}</td>'
            f'<td class="n {cls(h["pre5"])}">{h["pre5"]:+.2f}</td>'
            f'<td class="n {cls(h["pre1"])}">{h["pre1"]:+.2f}</td>'
            f'<td class="n {cls(h["post1"])}">{h["post1"]:+.2f}</td>'
            f'<td class="n {cls(h["post5"])}">{h["post5"]:+.2f}</td>'
            f'<td class="n {cls(h["post10"])}">{h["post10"]:+.2f}</td>'
            f'<td class="n {cls(h["post20"])}">{h["post20"]:+.2f}</td></tr>')


def row_m2026(r):
    return (f'<tr><td>{r["name"]}</td><td class="n">{r["aug31"]:.2f}</td>'
            f'<td class="n">{r["last"]:.2f}</td>'
            f'<td class="n {cls(r["sep_mtd"])}">{r["sep_mtd"]:+.2f}</td></tr>')


scopes_y2000 = stats["holiday_2000"]

html = HTML
html = html.replace("__DATA__", json.dumps(DATA, ensure_ascii=False))
html = html.replace("__FETCH__", stats["fetched_at"])
html = html.replace("__TODAY__", DATA["pos"]["today"])
html = html.replace("__CLOSE__", f'{DATA["pos"]["close"]:.2f}')
html = html.replace("__SEPCHG__", f'{DATA["pos"]["sep_mtd"]:+.2f}%')
html = html.replace("__YTD8__", f'{DATA["ytd8_26"]:+.2f}%')
html = html.replace("__ENV26__", f'环境档：{DATA["env_26"]}')
html = html.replace("__VRATIO__", f'{DATA["pos"]["v_ratio"]:.2f}')
html = html.replace("__TBL_WINDOW__", "\n".join(row_window(k) for k in WK_ORDER))
html = html.replace("__TBL_POST__", "\n".join(row_post(n) for n in [1, 3, 5, 10, 20]))
html = html.replace("__TBL_ENV__", "\n".join(row_env(t) for t in ENV_ORDER))
html = html.replace("__TBL_CROSS__", "\n".join(row_cross(n) for n in CROSS_ORDER))
html = html.replace("__TBL_DETAIL__", "\n".join(row_detail(h) for h in stats["holiday_detail_2000"]))
html = html.replace("__TBL_M2026__", "\n".join(row_m2026(r) for r in m2026))

outp = os.path.join(REP, "国庆长假效应复盘-20260915.html")
with open(outp, "w", encoding="utf-8") as f:
    f.write(html)
print("written:", outp)
print("chars:", len(html))
print("env buckets:", json.dumps(env, ensure_ascii=False))
print("2026 ytd8=%.2f%% -> %s" % (ytd8_26, env_26))
print("2026 sep_mtd 上证:", DATA["pos"]["sep_mtd"], " v_ratio:", DATA["pos"]["v_ratio"])

js = html.split("<script>")[-1].split("</script>")[0]
open(os.path.join(OUT, "_oct_holiday_report.js"), "w", encoding="utf-8").write(
    "var echarts={init:function(){return{setOption:function(){},resize:function(){}}}};\n"
    "var document={getElementById:function(){return null;}};\n"
    "var window={addEventListener:function(){}};\n" + js)
print("js chars:", len(js))
