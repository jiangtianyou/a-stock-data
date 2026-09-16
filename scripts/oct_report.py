# -*- coding: utf-8 -*-
"""
9-10月行情专题 - 报告生成
输入: out/oct_stats.json, out/oct_extra.json
输出: reports/9-10月行情季节性复盘-20260915.html
风格: 浅底深字 / 结论先行 / ECharts / 红涨绿跌
"""
import sys, os, json

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")
REP = os.path.join(BASE, "reports")
TITLE = "A股9-10月行情季节性复盘"
SUB = "1991-2026 · 上证指数为主口径 · 数据截至2026-08（月度）/ 2026-09-15（日线）"

st = json.load(open(os.path.join(OUT, "oct_stats.json"), encoding="utf-8"))
ex = json.load(open(os.path.join(OUT, "oct_extra.json"), encoding="utf-8"))

sm = st["single_month"]           # 1997起
sm00 = st["single_month_2000"]
hol00 = st["holiday_2000"]        # 2000起长假
hol10 = st["holiday_2010"]
env = ex["env"]
cur = ex["current_2026"]

# ---------------- 数据准备 (给 JS) ----------------
months = [{"m": m, "mean": sm[str(m)]["mean"], "win": sm[str(m)]["win"],
           "median": sm[str(m)]["median"], "n": sm[str(m)]["n"]} for m in range(1, 13)]

yearly = st["yearly_detail"]      # 1997起

wins = []
for k, lab in [("pre1", "节前1日"), ("pre3", "节前3日"), ("pre5", "节前5日"),
               ("pre10", "节前10日"), ("pre20", "节前20日"),
               ("post1", "节后1日"), ("post3", "节后3日"), ("post5", "节后5日"),
               ("post10", "节后10日"), ("post20", "节后20日")]:
    v = hol00.get(k)
    if v:
        wins.append({"k": lab, "mean": v["mean"], "median": v["median"],
                     "win": v["win"], "n": v["n"], "t": v["t"]})
wins10 = []
for k, lab in [("pre5", "节前5日"), ("pre10", "节前10日"), ("post3", "节后3日"),
               ("post5", "节后5日"), ("post10", "节后10日"), ("post20", "节后20日")]:
    v = hol10.get(k)
    if v:
        wins10.append({"k": lab, "mean": v["mean"], "median": v["median"],
                       "win": v["win"], "n": v["n"], "t": v["t"]})

envdata = [{"k": k, **v} for k, v in env.items()]
hidist = [{"m": m, "v": st["year_high_month"].get(str(m), 0)} for m in range(1, 13)]
lodist = [{"m": m, "v": st["year_low_month"].get(str(m), 0)} for m in range(1, 13)]

DATA = {
    "months": months, "yearly": yearly, "wins": wins, "wins10": wins10,
    "env": envdata, "hi": hidist, "lo": lodist,
    "volume": st["volume"], "yearly9": st["extreme_9"], "yearly10": st["extreme_10"],
    "current": cur,
}

# ---------------- CSS ----------------
CSS = """
:root{--bg:#f5f6f8;--card:#fff;--ink:#1a1d21;--ink2:#4a5058;--ink3:#8b929c;
--line:#e3e6ea;--up:#d9363e;--dn:#1f9e5a;--accent:#2b5cff;--warn:#c8791a;}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;
font-size:14px;line-height:1.72;-webkit-font-smoothing:antialiased}
.wrap{max-width:1080px;margin:0 auto;padding:34px 22px 70px}
h1{font-size:27px;font-weight:700;letter-spacing:-.4px;margin-bottom:6px}
.sub{color:var(--ink3);font-size:12.5px;margin-bottom:26px}
h2{font-size:18px;font-weight:650;margin:40px 0 6px;padding-left:11px;border-left:3.5px solid var(--accent)}
h2 .en{font-size:11.5px;color:var(--ink3);font-weight:400;margin-left:8px;letter-spacing:.4px}
h3{font-size:14.5px;font-weight:600;margin:22px 0 8px;color:var(--ink)}
p{color:var(--ink2);margin:9px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:11px;padding:18px 20px;margin:14px 0}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:11px;margin:18px 0 6px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:13px 14px}
.kpi .lb{font-size:11.5px;color:var(--ink3);margin-bottom:5px;line-height:1.4}
.kpi .vl{font-size:21px;font-weight:680;letter-spacing:-.5px}
.kpi .nt{font-size:11px;color:var(--ink3);margin-top:3px}
.up{color:var(--up)}.dn{color:var(--dn)}.warn{color:var(--warn)}
table{width:100%;border-collapse:collapse;font-size:12.8px;margin:10px 0}
th{background:#eef1f5;color:var(--ink2);font-weight:600;text-align:right;padding:8px 9px;
border-bottom:1.5px solid var(--line);white-space:nowrap}
th:first-child{text-align:left}
td{padding:7px 9px;text-align:right;border-bottom:1px solid #f0f2f5;font-variant-numeric:tabular-nums}
td:first-child{text-align:left;font-weight:500}
tr.hl{background:#fff8ec}
tr.hl td{font-weight:640}
.tblnote{font-size:11.5px;color:var(--ink3);margin-top:6px}
.chart{width:100%;background:var(--card);border:1px solid var(--line);border-radius:11px;
padding:8px;margin:12px 0}
.cap{font-size:11.5px;color:var(--ink3);text-align:center;margin:-4px 0 14px}
ul{margin:8px 0 8px 20px;color:var(--ink2)}li{margin:5px 0}
.tag{display:inline-block;font-size:11px;padding:1.5px 7px;border-radius:4px;font-weight:600;
vertical-align:middle;margin-left:6px}
.t-ok{background:#e6f6ec;color:#1f7a45}.t-warn{background:#fdf0e0;color:#a8640f}
.t-no{background:#f0f2f5;color:#767d87}
.lead{background:linear-gradient(180deg,#fff 0%,#fbfcfe 100%);border:1px solid #dfe4ec;
border-left:4px solid var(--accent);border-radius:10px;padding:16px 19px;margin:16px 0}
.lead b{color:var(--ink)}
.risk{background:#fdf8f3;border:1px solid #f0e0cc;border-radius:10px;padding:15px 19px;margin:14px 0}
.risk h3{color:var(--warn);margin-top:0}
.two{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:820px){.kpis{grid-template-columns:repeat(2,1fr)}.two{grid-template-columns:1fr}}
.ft{margin-top:44px;padding-top:18px;border-top:1px solid var(--line);font-size:11.5px;color:var(--ink3)}
code{background:#eef1f5;padding:1px 5px;border-radius:3px;font-size:12px;
font-family:"SF Mono",Consolas,monospace}
"""

# ---------------- 表格生成 ----------------
rows_m = []
for m in range(1, 13):
    c = sm[str(m)]
    cls = ' class="hl"' if m in (9, 10) else ""
    rows_m.append(
        f"<tr{cls}><td>{m}月</td><td>{c['mean']:+.2f}%</td><td>{c['median']:+.2f}%</td>"
        f"<td class=\"{'up' if c['mean_dm']>0 else 'dn'}\">{c['mean_dm']:+.2f}%</td>"
        f"<td>{c['win']:.1f}%</td><td>{c['std']:.2f}%</td><td>{c['t_dm']:+.2f}</td><td>{c['n']}</td></tr>")
tbl_month = "\n".join(rows_m)

rows_w = []
for w in wins:
    cls = ' class="hl"' if w["k"] in ("节前1日", "节前10日", "节后3日", "节后20日") else ""
    rows_w.append(f"<tr{cls}><td>{w['k']}</td>"
                  f"<td class=\"{'up' if w['mean']>0 else 'dn'}\">{w['mean']:+.2f}%</td>"
                  f"<td class=\"{'up' if w['median']>0 else 'dn'}\">{w['median']:+.2f}%</td>"
                  f"<td>{w['win']:.1f}%</td><td>{w['t']:+.2f}</td><td>{w['n']}</td></tr>")
tbl_win = "\n".join(rows_w)

env_order = ["强势(1-8月>10%)", "震荡(-10%~10%)", "弱势(<-10%)"]
rows_e = []
for k in env_order:
    if k not in env:
        continue
    v = env[k]
    rows_e.append(f"<tr><td>{k}</td><td>{v['n']}</td>"
                  f"<td class=\"{'up' if v['sep_mean']>0 else 'dn'}\">{v['sep_mean']:+.2f}%</td>"
                  f"<td>{v['sep_win']:.1f}%</td>"
                  f"<td class=\"{'up' if v['oct_mean']>0 else 'dn'}\"><b>{v['oct_mean']:+.2f}%</b></td>"
                  f"<td><b>{v['oct_win']:.1f}%</b></td>"
                  f"<td class=\"{'up' if v['sum_mean']>0 else 'dn'}\">{v['sum_mean']:+.2f}%</td>"
                  f"<td>{v['sum_win']:.1f}%</td></tr>")
tbl_env = "\n".join(rows_e)

c = st["conditional"]
sep_u, sep_d = c["sep_up"], c["sep_down"]
p5d, p5u = c["pre5_down"], c["pre5_up"]

cur_rows = "".join(
    f'<tr><td>{n}</td><td>{v["last"]:.2f}</td><td>{v["aug31"]:.2f}</td>'
    f'<td class="{ "up" if v["sep_mtd"] > 0 else "dn"}"><b>{v["sep_mtd"]:+.2f}%</b></td>'
    f'<td class="{ "up" if v["jul_mtd"] > 0 else "dn"}">{v["jul_mtd"]:+.2f}%</td></tr>'
    for n, v in cur.items())

# 关键数字
k9, k10 = sm["9"], sm["10"]
m2 = sm["2"]

HTML_BODY = f"""
<div class="wrap">
<h1>{TITLE}</h1>
<div class="sub">{SUB}　|　数据源：腾讯财经日线/月线（前复权），上证指数为主口径</div>

<div class="lead">
<b>一句话结论：</b>A股 9-10 月<b>并不存在一个稳定的"月度方向规律"</b>——9月、10月 29 年里去年度效应后均值仅
{k9['mean_dm']:+.2f}% / {k10['mean_dm']:+.2f}%，胜率约 {k9['win']:.0f}% / {k10['win']:.0f}%，统计上都不显著。<br>
<b>真正稳定的是三件事：</b>① 国庆长假造成的<b>时间切分效应</b>（节前两周偏弱缩量、节前最后一日显著偏强、节后阶段性回暖）；
② 10月走势是<b>市场状态的放大器</b>——强势年里 10 月胜率 {env['强势(1-8月>10%)']['oct_win']:.0f}%，弱势年里只有 {env['弱势(<-10%)']['oct_win']:.0f}%；
③ 9月/10月是 A 股<b>季节性最弱的月份之一</b>，远不如 2 月（去年度效应 {m2['mean_dm']:+.2f}%、胜率 {m2['win']:.0f}%、t={m2['t_dm']:.2f}）。
</div>

<div class="kpis">
  <div class="kpi"><div class="lb">9月 去年度效应均值</div>
    <div class="vl {'up' if k9['mean_dm']>0 else 'dn'}">{k9['mean_dm']:+.2f}%</div>
    <div class="nt">胜率 {k9['win']:.1f}% · t={k9['t_dm']:+.2f} · {k9['n']}年</div></div>
  <div class="kpi"><div class="lb">10月 去年度效应均值</div>
    <div class="vl {'up' if k10['mean_dm']>0 else 'dn'}">{k10['mean_dm']:+.2f}%</div>
    <div class="nt">胜率 {k10['win']:.1f}% · t={k10['t_dm']:+.2f} · {k10['n']}年</div></div>
  <div class="kpi"><div class="lb">节前最后1日（2000起）</div>
    <div class="vl up">{hol00['pre1']['mean']:+.2f}%</div>
    <div class="nt">胜率 {hol00['pre1']['win']:.1f}% · <b>t={hol00['pre1']['t']:+.2f}</b> · 显著</div></div>
  <div class="kpi"><div class="lb">节前10日 中位数（2000起）</div>
    <div class="vl dn">{hol00['pre10']['median']:+.2f}%</div>
    <div class="nt">胜率仅 {hol00['pre10']['win']:.1f}% · 偏弱最稳</div></div>
</div>

<h2>一、先纠两个偏<span class="en">MYTH-BUSTING</span></h2>
<p>市场上关于 9-10 月有两句流行说法，<b>数据都不支持</b>：</p>
<ul>
<li><b>"金九银十"</b>——这是房地产与商品消费的说法，不是 A 股指数的规律。9月去年度效应均值
{k9['mean_dm']:+.2f}%，10月 {k10['mean_dm']:+.2f}%，都在 12 个月里排倒数。</li>
<li><b>"9月魔咒"</b>——源自美股（标普 9 月是全年唯一负收益月）。A股 9 月虽然略偏弱，但 t 值仅
{k9['t_dm']:+.2f}，<b>达不到任何常规显著性水平</b>，不能当成"必跌"来用。</li>
</ul>
<p>把样本按口径拆分，能看到一个更关键的事实：<b>9-10月的"弱势"主要来自 2010 年以前</b>。</p>

<table>
<thead><tr><th>口径</th><th>9月均值</th><th>9月胜率</th><th>10月均值</th><th>10月胜率</th></tr></thead>
<tbody>
<tr><td>1997起（主口径，29年）</td>
<td class="{ 'up' if sm['9']['mean']>0 else 'dn'}">{sm['9']['mean']:+.2f}%</td><td>{sm['9']['win']:.1f}%</td>
<td class="{ 'up' if sm['10']['mean']>0 else 'dn'}">{sm['10']['mean']:+.2f}%</td><td>{sm['10']['win']:.1f}%</td></tr>
<tr><td>2000起（26年）</td>
<td class="{ 'up' if sm00['9']['mean']>0 else 'dn'}">{sm00['9']['mean']:+.2f}%</td><td>{sm00['9']['win']:.1f}%</td>
<td class="{ 'up' if sm00['10']['mean']>0 else 'dn'}">{sm00['10']['mean']:+.2f}%</td><td>{sm00['10']['win']:.1f}%</td></tr>
<tr class="hl"><td>2010起（16年）</td>
<td class="up">{st['single_month_2010']['9']['mean']:+.2f}%</td><td>{st['single_month_2010']['9']['win']:.1f}%</td>
<td class="up">{st['single_month_2010']['10']['mean']:+.2f}%</td><td>{st['single_month_2010']['10']['win']:.1f}%</td></tr>
</tbody></table>
<div class="tblnote">结论：近 16 年 9 月、10 月均值双双转正、胜率升至 56%。所谓"9-10月偏弱"更像是
2000年代（多次熊市、股权分置改革前后）留下的印象，而不是可持续交易的规律。</div>

<div class="chart" id="c_month" style="height:330px"></div>
<div class="cap">图1　12个月份平均收益与胜率（上证指数，1997-2026，红柱为负收益按 A 股习惯反向着色）</div>

<table>
<thead><tr><th>月份</th><th>平均收益</th><th>中位数</th><th>去年度效应</th><th>胜率</th><th>标准差</th><th>t值</th><th>样本</th></tr></thead>
<tbody>
{tbl_month}
</tbody></table>
<div class="tblnote">主口径 1997-01~2026-08（涨跌停制度实施后），共 {st['sample']['main_years']} 年。
"去年度效应"= 当月收益 − 该年 12 个月平均收益，用于剥离牛熊整体涨跌。<b>t值 &gt; 2 才算统计显著</b>——
12 个月里只有 2 月（t={m2['t_dm']:+.2f}）越过了这条线。</div>

<h2>二、长假切分：9-10月真正的结构性特征<span class="en">THE HOLIDAY SPLIT</span></h2>
<p>10 月只有约 16 个交易日，而长假把行情切成<b>节前</b>与<b>节后</b>两个性质不同的阶段。这是 9-10 月最稳定、
也最容易被"单月统计"掩盖的规律。</p>

<div class="chart" id="c_win" style="height:340px"></div>
<div class="cap">图2　国庆长假前后各窗口累计收益（上证指数，2000年起 26 个样本；均值 vs 中位数）</div>

<table>
<thead><tr><th>窗口</th><th>平均收益</th><th>中位数</th><th>胜率</th><th>t值</th><th>样本</th></tr></thead>
<tbody>
{tbl_win}
</tbody></table>
<div class="tblnote">节后窗口以<b>节前最后收盘</b>为基准。高亮行为最有交易含义的四个窗口。</div>

<h3>三段式特征</h3>
<ul>
<li><b>① 节前两周：偏弱 + 缩量（最稳的一段）。</b>节前 10 日中位数 {hol00['pre10']['median']:+.2f}%，
胜率仅 <b>{hol00['pre10']['win']:.1f}%</b>——26 年里只有 9 年节前两周是涨的。
节前 5 日成交量相对当年日均量<b>萎缩 {abs(st['volume']['pre5_vs_year']):.1f}%</b>，节后 5 日仍低
{abs(st['volume']['post5_vs_year']):.1f}%，避险资金离场特征清晰。</li>
<li><b>② 节前最后一日：全样本唯一显著的窗口。</b>均值 {hol00['pre1']['mean']:+.2f}%，
胜率 <b>{hol00['pre1']['win']:.1f}%</b>，<b>t={hol00['pre1']['t']:+.2f}</b>。"节前红盘收官"在 2000 年后
的 26 年里出现 18 次。注意 1997-1999 口径下该效应不明显，是 2000 年后才稳定下来的。</li>
<li><b>③ 节后：短窗口偏强，且 2010 年后明显增强。</b>2010 起节后 3 日 {hol10['post3']['mean']:+.2f}%
（胜率 {hol10['post3']['win']:.1f}%，t={hol10['post3']['t']:+.2f}）、节后 5 日 {hol10['post5']['mean']:+.2f}%、
节后 20 日 <b>{hol10['post20']['mean']:+.2f}%（胜率 {hol10['post20']['win']:.1f}%，t={hol10['post20']['t']:+.2f}）</b>。</li>
</ul>
<p>但<b>不要把"节后"当成无脑做多的理由</b>：2000-2009 年节后 5 日均值为
{st['holiday']['post5']['mean']:+.2f}%（全历史口径），节后 1 日上涨年份 17 个、下跌年份 9 个，
下跌的 9 年（2001/2002/2005/2008/2011/2012/2018/2022/2023）<b>几乎全是熊市或弱市</b>。也就是说，
节后效应是"环境依赖"的，不是日历依赖的——直接引出下一节。</p>

<h2>三、真正的开关：市场环境<span class="en">REGIME, NOT CALENDAR</span></h2>
<p>把年份按<b>当年 1-8 月累计涨幅</b>分档，10 月的表现出现数量级差异：</p>

<table>
<thead><tr><th>环境（按1-8月涨幅）</th><th>样本年</th><th>9月均值</th><th>9月胜率</th>
<th>10月均值</th><th>10月胜率</th><th>9+10合计</th><th>合计胜率</th></tr></thead>
<tbody>
{tbl_env}
</tbody></table>
<div class="tblnote">1997-2026 共 29 个可分组年份（不含 2026）。</div>

<div class="chart" id="c_env" style="height:320px"></div>
<div class="cap">图3　不同市场环境下 10 月平均收益与胜率（柱=均值，折线=胜率）</div>

<ul>
<li><b>强势年（1-8月涨超10%）：</b>10 月均值 <b>{env['强势(1-8月>10%)']['oct_mean']:+.2f}%</b>、
胜率 <b>{env['强势(1-8月>10%)']['oct_win']:.1f}%</b>（9 年中 8 年上涨）——"红十月"确实存在于牛市里。</li>
<li><b>震荡年：</b>10 月均值 {env['震荡(-10%~10%)']['oct_mean']:+.2f}%、胜率仅
<b>{env['震荡(-10%~10%)']['oct_win']:.1f}%</b>，但 9 月是 {env['震荡(-10%~10%)']['sep_mean']:+.2f}%，
<b>9+10 合计 {env['震荡(-10%~10%)']['sum_mean']:+.2f}%、合计胜率 {env['震荡(-10%~10%)']['sum_win']:.1f}%</b>。</li>
<li><b>弱势年：</b>10 月均值 <b>{env['弱势(<-10%)']['oct_mean']:+.2f}%</b>、胜率
<b>{env['弱势(<-10%)']['oct_win']:.1f}%</b>（7 年中 5 年大跌）——熊市里的 10 月是"补跌月"。</li>
</ul>
<div class="lead">
<b>这才是可用的框架：</b>不要问"10 月涨还是跌"，要问"当前处于哪种环境"。<br>
牛市里 10 月是<b>延续上涨</b>（胜率 89%）；震荡市里 10 月单月容易收跌，但 9-10 月合计偏正；
熊市里 10 月是<b>放大跌幅</b>（均值 -4.44%）。环境判断的权重，远高于日历。
</div>

<h2>四、容易被误读的四个细节<span class="en">GOTCHAS</span></h2>
<div class="two">
<div class="card">
<h3>1. 极端值会骗人</h3>
<p>2024 年节前 10 日上证 <b>+22.80%</b>（"9·24"行情），单年就把节前 10 日的<b>均值</b>从负数拉到接近 0。
所以这张表必须看<b>中位数</b>：{hol00['pre10']['median']:+.2f}%。同理，2008 年节后 5 日 -12.78%
也会拉低均值。<b>小样本的季节性统计，中位数比均值可靠。</b></p>
</div>
<div class="card">
<h3>2. 节前跌 → 节后涨？</h3>
<p>2000 年起 26 个样本中，节前 5 日下跌的 {p5d['n']} 次里，节后 5 日均值
<b>{p5d['post5_mean']:+.2f}%</b>、胜率 <b>{p5d['post5_win']:.1f}%</b>；节前 5 日上涨的 {p5u['n']} 次里，
节后 5 日均值 {p5u['post5_mean']:+.2f}%、胜率 {p5u['post5_win']:.1f}%。相关系数
-0.336（弱负相关）。<b>方向上有"跷跷板"，但样本量太小（14/12），只能当参考不能当信号。</b></p>
</div>
<div class="card">
<h3>3. 风格切换不显著</h3>
<p>用创业板指/中证1000/中证500 为成长组，上证50/中证红利/沪深300 为价值组：节前 5 日成长-价值
{ex['style']['pre5']['mean']:+.2f}%、节后 5 日 {ex['style']['post5']['mean']:+.2f}%、节后 20 日
{ex['style']['post20']['mean']:+.2f}%，<b>p 值均 &gt; 0.6，统计上无法区分</b>。所谓"节前价值、节后成长"
在指数层面没有证据支持（个股层面另说）。</p>
</div>
<div class="card">
<h3>4. 9/10月不是年内低点高发期</h3>
<p>34 个完整年份里，年内最低点出现在 <b>1 月 8 次</b>、2月/12月各 4 次、10月 3 次，而 <b>9 月只有 1 次</b>。
最高点则均匀分布在 1/2/6/12 月。"9-10 月见底/见顶"缺乏统计支持。</p>
</div>
</div>

<div class="chart" id="c_dist" style="height:300px"></div>
<div class="cap">图4　年内最高点 / 最低点出现的月份分布（34 个完整年份，1991-2025）</div>

<h2>五、2026 年当前位置<span class="en">WHERE WE ARE</span></h2>
<p>以下为截至 <b>2026-09-15</b> 的实际数据（非预测）：</p>
<table>
<thead><tr><th>品种</th><th>最新收盘</th><th>8月末</th><th>9月至今</th><th>8月单月</th></tr></thead>
<tbody>
{cur_rows}
</tbody></table>
<div class="tblnote">上证指数 2026 年 1-8 月累计 <b>+0.44%</b>，属"震荡档"；年内最高 4258.86（5/14）、
最低 3741.11（7/20），9 月 15 日收 3864.28，距年内高点 -9.26%。</div>

<div class="card">
<h3>历史范式对照（震荡档，n=13）</h3>
<ul>
<li>9 月均值 <b>{env['震荡(-10%~10%)']['sep_mean']:+.2f}%</b>，胜率 {env['震荡(-10%~10%)']['sep_win']:.1f}% —— 震荡市 9 月反而偏强。</li>
<li>10 月均值 {env['震荡(-10%~10%)']['oct_mean']:+.2f}%，但<b>胜率仅 {env['震荡(-10%~10%)']['oct_win']:.1f}%</b>（13 年中只 4 年上涨）。</li>
<li>9+10 月合计均值 {env['震荡(-10%~10%)']['sum_mean']:+.2f}%，合计胜率 {env['震荡(-10%~10%)']['sum_win']:.1f}%，中位数 {env['震荡(-10%~10%)']['sum_median']:+.2f}%。</li>
</ul>
<p><b>但 2026 年的 9 月正在偏离这个范式</b>：9 月已过半，上证 {cur['上证指数']['sep_mtd']:+.2f}%、
创业板指 {cur['创业板指']['sep_mtd']:+.2f}%，全面回撤。历史条件概率上，
"9 月收跌"之后 10 月均值 {sep_d['oct_mean']:+.2f}%、胜率 {sep_d['oct_win']:.1f}%（n={sep_d['n']}）；
"9 月收涨"之后 10 月均值 {sep_u['oct_mean']:+.2f}%、胜率 {sep_u['oct_win']:.1f}%（n={sep_u['n']}）。
两点差异都不显著（相关系数仅 {c['corr_sep_oct']:+.2f}），<b>不足以据此推断 10 月方向</b>。</p>
</div>

<div class="risk">
<h3>风险提示与使用边界</h3>
<ul>
<li><b>样本量是全篇最大限制。</b>9/10 月每个统计口径只有 16-34 个观测，单看 9 月或 10 月，
任何结论都可能在 3-4 个异常年份上翻盘。请把本文当作"分布参考"，而不是"预测模型"。</li>
<li><b>2024 年是重大异常值。</b>"9·24"政策转向把当年节前 10 日拉出 +22.8%，任何含 2024 的均值都被系统性抬升。</li>
<li><b>政策窗口不可被季节性覆盖。</b>9 月底政治局会议、10 月四中全会/五年规划讨论、三季报密集披露，
都可能单点改写行情，其影响力大于任何日历规律。</li>
<li><b>本文全部为历史统计分析，不构成任何投资建议。</b>市场环境判断（强势/震荡/弱势）本身是主观变量，
用不同口径（是否换基准指数、是否用振幅而非涨幅）会得到不同的分组结果。</li>
<li>数据经腾讯财经接口获取并做前复权处理，月末收益按最后交易日收盘价环比计算；
2026-09 为未完月，已从月度统计中剔除。</li>
</ul>
</div>

<div class="ft">
{TITLE}　|　生成于 2026-09-15　|　样本：上证指数 1990-12-19 ~ 2026-09-15（8553 个交易日）
</div>
</div>
"""

HTML = ('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{TITLE}</title><style>{CSS}</style></head><body>')

JS_TMPL = r"""
const D = __DATA__;
const UP='#d9363e', DN='#1f9e5a', INK='#1a1d21', INK3='#8b929c', GRID='#eceff3';
function ucls(v){return v>=0?'#e8545c':'#28a866';}           // 浅底用稍亮色
function dcls(v){return v>0?UP:DN;}
const baseTip={backgroundColor:'rgba(255,255,255,.97)',borderColor:'#dfe4ec',borderWidth:1,
  textStyle:{color:INK,fontSize:12},extraCssText:'box-shadow:0 4px 14px rgba(0,0,0,.09);border-radius:7px;'};

// ---------- 图1 月份季节性 ----------
(function(){
  const el=document.getElementById('c_month'); if(!el)return;
  const ch=echarts.init(el);
  const x=D.months.map(d=>d.m+'月');
  const mean=D.months.map(d=>d.mean);
  const win=D.months.map(d=>d.win);
  const hl=[8,9];   // 索引 8=9月, 9=10月
  ch.setOption({
    tooltip:Object.assign({trigger:'axis',axisPointer:{type:'shadow'},
      formatter:p=>{const i=p[0].dataIndex,d=D.months[i];
        return d.m+'月<br/>平均收益 <b style="color:'+dcls(d.mean)+'">'+d.mean.toFixed(2)+'%</b>'
          +'<br/>中位数 '+d.median.toFixed(2)+'%<br/>胜率 '+d.win.toFixed(1)+'%<br/>样本 '+d.n+' 年';}},baseTip),
    legend:{data:['平均收益','胜率'],top:3,left:'center',textStyle:{color:INK3,fontSize:11},itemWidth:12,itemHeight:8},
    grid:{left:52,right:56,top:52,bottom:30},
    xAxis:{type:'category',data:x,axisLine:{lineStyle:{color:'#d8dde5'}},
      axisLabel:{color:INK3,fontSize:11.5},axisTick:{show:false}},
    yAxis:[
      {type:'value',name:'收益 %',nameTextStyle:{color:INK3,fontSize:10.5},
        splitLine:{lineStyle:{color:GRID}},axisLabel:{color:INK3,fontSize:11,formatter:'{value}'}},
      {type:'value',name:'胜率 %',min:30,max:85,nameTextStyle:{color:INK3,fontSize:10.5},
        splitLine:{show:false},axisLabel:{color:INK3,fontSize:11,formatter:'{value}%'}}
    ],
    series:[
      {name:'平均收益',type:'bar',data:mean.map((v,i)=>({value:v,
        itemStyle:{color:hl.includes(i)?dcls(v):(v>=0?'rgba(217,54,62,.42)':'rgba(31,158,90,.42)'),
        borderRadius:[3,3,0,0]}})),barWidth:'52%',
        markArea:{silent:true,itemStyle:{color:'rgba(43,92,255,.055)'},data:[[{xAxis:'9月'},{xAxis:'10月'}]]},
        label:{show:true,position:'top',fontSize:10.5,color:INK2_,formatter:p=>p.value.toFixed(2)}},
      {name:'胜率',type:'line',yAxisIndex:1,data:win,smooth:true,symbolSize:5,
        lineStyle:{color:'#2b5cff',width:2},itemStyle:{color:'#2b5cff'}}
    ]
  });
  window.addEventListener('resize',()=>ch.resize());
})();

// ---------- 图2 长假窗口 ----------
(function(){
  const el=document.getElementById('c_win'); if(!el)return;
  const ch=echarts.init(el);
  const x=D.wins.map(d=>d.k);
  const mean=D.wins.map(d=>d.mean);
  const med=D.wins.map(d=>d.median);
  const win=D.wins.map(d=>d.win);
  ch.setOption({
    tooltip:Object.assign({trigger:'axis',axisPointer:{type:'shadow'},
      formatter:p=>{const i=p[0].dataIndex,d=D.wins[i];
        return d.k+'<br/>平均 <b style="color:'+dcls(d.mean)+'">'+d.mean.toFixed(2)+'%</b>'
          +'<br/>中位数 '+d.median.toFixed(2)+'%<br/>胜率 '+d.win.toFixed(1)+'%'
          +'<br/>t='+d.t+' · n='+d.n;}},baseTip),
    legend:{data:['平均收益','中位数','胜率'],top:3,left:'center',textStyle:{color:INK3,fontSize:11},itemWidth:12,itemHeight:8},
    grid:{left:52,right:56,top:52,bottom:46},
    xAxis:{type:'category',data:x,axisLine:{lineStyle:{color:'#d8dde5'}},
      axisLabel:{color:INK3,fontSize:11,interval:0,rotate:0},axisTick:{show:false}},
    yAxis:[
      {type:'value',name:'收益 %',nameTextStyle:{color:INK3,fontSize:10.5},
        splitLine:{lineStyle:{color:GRID}},axisLabel:{color:INK3,fontSize:11}},
      {type:'value',name:'胜率 %',min:20,max:80,nameTextStyle:{color:INK3,fontSize:10.5},
        splitLine:{show:false},axisLabel:{color:INK3,fontSize:11,formatter:'{value}%'}}
    ],
    series:[
      {name:'平均收益',type:'bar',data:mean.map(v=>({value:v,itemStyle:{color:dcls(v),borderRadius:[3,3,0,0]}})),
        barWidth:'26%',barGap:'12%'},
      {name:'中位数',type:'bar',data:med.map(v=>({value:v,itemStyle:{color:v>=0?'rgba(217,54,62,.45)':'rgba(31,158,90,.45)',borderRadius:[3,3,0,0]}})),
        barWidth:'26%'},
      {name:'胜率',type:'line',yAxisIndex:1,data:win,smooth:true,symbolSize:5,
        lineStyle:{color:'#2b5cff',width:2},itemStyle:{color:'#2b5cff'},
        markLine:{silent:true,symbol:'none',data:[{yAxis:50,lineStyle:{color:'#c9cfd8',type:'dashed'}}]}}
    ]
  });
  window.addEventListener('resize',()=>ch.resize());
})();

// ---------- 图3 环境分组 ----------
(function(){
  const el=document.getElementById('c_env'); if(!el)return;
  const ch=echarts.init(el);
  const x=D.env.map(d=>d.k);
  const oct=D.env.map(d=>d.oct_mean);
  const sep=D.env.map(d=>d.sep_mean);
  const win=D.env.map(d=>d.oct_win);
  ch.setOption({
    tooltip:Object.assign({trigger:'axis',axisPointer:{type:'shadow'},
      formatter:p=>{const i=p[0].dataIndex,d=D.env[i];
        return d.k+'（'+d.n+'年）<br/>9月均值 <b>'+d.sep_mean.toFixed(2)+'%</b>'
          +'<br/>10月均值 <b style="color:'+dcls(d.oct_mean)+'">'+d.oct_mean.toFixed(2)+'%</b>'
          +'<br/>10月胜率 '+(d.oct_win).toFixed(1)+'%'
          +'<br/>9+10合计 '+d.sum_mean.toFixed(2)+'% · 胜率 '+d.sum_win.toFixed(1)+'%';}},baseTip),
    legend:{data:['9月均值','10月均值','10月胜率'],top:3,left:'center',textStyle:{color:INK3,fontSize:11},itemWidth:12,itemHeight:8},
    grid:{left:52,right:56,top:52,bottom:32},
    xAxis:{type:'category',data:x,axisLine:{lineStyle:{color:'#d8dde5'}},
      axisLabel:{color:INK2_,fontSize:11.5},axisTick:{show:false}},
    yAxis:[
      {type:'value',name:'收益 %',nameTextStyle:{color:INK3,fontSize:10.5},
        splitLine:{lineStyle:{color:GRID}},axisLabel:{color:INK3,fontSize:11}},
      {type:'value',name:'胜率 %',min:0,max:100,nameTextStyle:{color:INK3,fontSize:10.5},
        splitLine:{show:false},axisLabel:{color:INK3,fontSize:11,formatter:'{value}%'}}
    ],
    series:[
      {name:'9月均值',type:'bar',data:sep.map(v=>({value:v,itemStyle:{color:'rgba(139,146,156,.5)',borderRadius:[3,3,0,0]}})),barWidth:'24%'},
      {name:'10月均值',type:'bar',data:oct.map(v=>({value:v,itemStyle:{color:dcls(v),borderRadius:[3,3,0,0]}})),
        barWidth:'24%',label:{show:true,position:'top',fontSize:11,color:INK2_,formatter:p=>p.value.toFixed(2)}},
      {name:'10月胜率',type:'line',yAxisIndex:1,data:win,smooth:false,symbolSize:7,z:10,
        lineStyle:{color:'#2b5cff',width:2},itemStyle:{color:'#2b5cff'},
        label:{show:true,fontSize:11,color:'#2b5cff',formatter:p=>p.value.toFixed(0)+'%',
          backgroundColor:'rgba(255,255,255,.92)',padding:[1,4],borderRadius:3}}
    ]
  });
  window.addEventListener('resize',()=>ch.resize());
})();

// ---------- 图4 高低点分布 ----------
(function(){
  const el=document.getElementById('c_dist'); if(!el)return;
  const ch=echarts.init(el);
  const x=[...Array(12)].map((_,i)=>(i+1)+'月');
  ch.setOption({
    tooltip:Object.assign({trigger:'axis',axisPointer:{type:'shadow'}},baseTip),
    legend:{data:['年内最低点','年内最高点'],top:3,left:'center',textStyle:{color:INK3,fontSize:11},itemWidth:12,itemHeight:8},
    grid:{left:46,right:20,top:52,bottom:30},
    xAxis:{type:'category',data:x,axisLine:{lineStyle:{color:'#d8dde5'}},
      axisLabel:{color:INK3,fontSize:11.5},axisTick:{show:false}},
    yAxis:{type:'value',name:'年数',nameTextStyle:{color:INK3,fontSize:10.5},
      splitLine:{lineStyle:{color:GRID}},axisLabel:{color:INK3,fontSize:11}},
    series:[
      {name:'年内最低点',type:'bar',data:D.lo.map(d=>d.v),barWidth:'30%',
        itemStyle:{color:'#2b5cff',borderRadius:[3,3,0,0]},
        label:{show:true,position:'top',fontSize:10.5,color:INK3,formatter:p=>p.value||''}},
      {name:'年内最高点',type:'bar',data:D.hi.map(d=>d.v),barWidth:'30%',
        itemStyle:{color:'#e8a33d',borderRadius:[3,3,0,0]},
        label:{show:true,position:'top',fontSize:10.5,color:INK3,formatter:p=>p.value||''}}
    ]
  });
  window.addEventListener('resize',()=>ch.resize());
})();
"""
JS_TMPL = JS_TMPL.replace("INK2_", "'#4a5058'")
JS = JS_TMPL.replace("__DATA__", json.dumps(DATA, ensure_ascii=False))

# 修正 JS 里被替换的常量
JS = JS.replace("'#4a5058'", "'#4a5058'")

HTML_END = ('<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>'
            '<script>' + JS + '</script></body></html>')

body = HTML_BODY.replace("{A_TITLE_PLACEHOLDER}", TITLE)

html = HTML + body + HTML_END

os.makedirs(REP, exist_ok=True)
path = os.path.join(REP, "9-10月行情季节性复盘-20260915.html")
with open(path, "w", encoding="utf-8") as f:
    f.write(html)
print("->", path, len(html), "bytes")
