import json, os, re

BASE = r"D:\Desktop\Playground\a-stock-data"
d = json.load(open(os.path.join(BASE, "out", "final2025.json"), encoding="utf-8"))
a = json.load(open(os.path.join(BASE, "out", "attribution2025.json"), encoding="utf-8"))
M = d["metrics"]; S = d["stats"]; mo = d["monthly"]; months = d["months"]

# 复用 2026 报告的 <style>
tpl_a = open(os.path.join(BASE, "scripts", "tpl_a.html"), encoding="utf-8").read()
STYLE = tpl_a[tpl_a.index("<style>"):tpl_a.index("</style>") + len("</style>")]

def up(v): return "up" if v >= 0 else "down"
def sg(v, unit="%"): return ('+' if v >= 0 else '') + f"{v:.2f}" + unit

port = M["组合(等权买入持有)"]; idx = M["科创芯片指数"]
zx = M["中芯国际"]; hw = M["寒武纪"]; hg = M["海光信息"]
raw = json.load(open(os.path.join(BASE, "out", "k2025_all.json"), encoding="utf-8"))
def hilo(code):
    seg = [x for x in raw[code]["rows"] if "20250101" <= x["d"] <= "20251231"]
    hi = max(seg, key=lambda x: x["h"]); lo = min(seg, key=lambda x: x["l"])
    return hi["h"], hi["d"], lo["l"], lo["d"]
H = {k: hilo(k) for k in ["000685", "688981", "688256", "688041"]}

P = []
P.append(f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>国产算力三剑客组合 2025 全年复盘：中芯国际+寒武纪+海光信息 vs 科创芯片指数</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
{STYLE}
</head>
<body>
<div class="wrap">
<h1>国产算力「三剑客」组合 2025 全年复盘</h1>
<div class="sub">
组合：中芯国际(688981) + 寒武纪(688256) + 海光信息(688041)，等权各 1/3 |
基准：科创芯片指数(000685) |
区间：2024-12-31 收盘 → 2025-12-31 收盘（244 个交易日）|
行情：腾讯日K前复权（与通达信锚点交叉校验一致）| 本报告为 2026 YTD 复盘的前传
</div>

<div class="tldr">
<b>TL;DR 结论先行 —— 2025 是「赢」的一年，但赢得侥幸且埋雷</b>
<ul>
<li><b>组合 2025 全年 +62.04%，科创芯片指数 +61.33%，微幅跑赢 0.71pct（几何超额 +3.43%）。</b>这与 2026 YTD 跑输 35.47pct 形成 180° 反转——同样三只票、同一个指数，去年险胜、今年惨败。</li>
<li><b>「赢」完全靠 8 月单月。</b>8 月组合 +61.94%、指数 +35.24%，单月超额 +26.69pct；剔除 8 月后，组合全年仅 <b>+0.07%</b>，指数 <b>+19.29%</b>，反而跑输 19.22pct。<b>一个月的暴力拉升撑起了全年的「胜利」。</b></li>
<li><b>「赢」也完全靠寒武纪一只。</b>寒武纪 +106.25%（超额 +44.92pct）以一己之力拉动组合；中芯 +29.81%（跑输指数 -31.52pct）、海光 +50.07%（-11.26pct）都是拖累。若寒武纪不爆发，组合 2025 大幅跑输。</li>
<li><b>风险调整后其实更差。</b>组合夏普 <b>1.19</b> &lt; 指数 1.67，Calmar 2.59 &lt; 3.19，最大回撤 -24.06% &gt; 指数 -19.30%，年化波动 51.01% 远高于指数 36.11%。<b>Beta 高达 1.25</b>——这不是「选股 alpha」，是「加杠杆式的高 Beta 暴露」在牛市里的自然结果。</li>
<li><b>上行捕获 117.1% / 下行捕获 118.7%</b>：涨得多也跌得多，典型高 Beta 放大器。2025 是单边上行的大牛市（指数 +61%），放大器自然输出正超额；<b>2026 风向一变，同一个放大器立刻反噬</b>——两年的结果是同一枚硬币的两面。</li>
<li><b>2025 年真正的 alpha 也不在组合身上。</b>前 20 大等权 YTD <b>+117.61%</b>，组合三只等权仅 +62.04%，其余 17 只等权 <b>+127.42%</b>，差距 -65.37pct。涨幅王是光芯片（仕佳光子 +451.93%、源杰科技 +382.16%）、晶圆代工（华虹 +132.13%）、设备（睿创 +115.87%、拓荆 +115.37%）。</li>
<li><b>跨年铁证：2025 的强势二线，2026 继续强势；组合三只从「权重龙头」沦为「掉队者」。</b>源杰 2025 第2→2026 第1、华峰测控 2025 第10→第3、华海清科 2025 第19→第4、盛科通信 2025 第16→第5；而寒武纪 2025 第7→2026 第18、中芯国际连续两年倒数第1。<b>市场奖励的从来不是「龙头地位」，是「业绩变化率与预期差」。</b></li>
</ul>
</div>

<h2>一、组合与基准：2025 全年核心数据</h2>
<div class="cards">
  <div class="card win">
    <div class="name">等权组合（买入持有）</div>
    <div class="big up">+{port['tot']:.2f}%</div>
    <div class="meta">期初各投 1/3 不调整 | 年化 +{port['cagr']:.2f}% | 年化波动 {port['vol']:.2f}%<br>最大回撤 <b class="down">{port['mdd']:.2f}%</b>（{port['mdd_date'][5:]}）| 夏普 <b>{port['sharpe']:.2f}</b> | Calmar {port['calmar']:.2f} | 日胜率 {port['win']:.1f}%</div>
  </div>
  <div class="card bench">
    <div class="name">科创芯片指数 000685</div>
    <div class="big up">+{idx['tot']:.2f}%</div>
    <div class="meta">1619.93 → 2613.41 点 | 年化 +{idx['cagr']:.2f}% | 年化波动 {idx['vol']:.2f}%<br>最大回撤 <b class="down">{idx['mdd']:.2f}%</b>（{idx['mdd_date'][5:]}）| 夏普 <b>{idx['sharpe']:.2f}</b> | Calmar {idx['calmar']:.2f} | 日胜率 {idx['win']:.1f}%</div>
  </div>
  <div class="card win">
    <div class="name">超额收益</div>
    <div class="big up">+{S['ex_arith']:.2f}<span style="font-size:16px">pct</span></div>
    <div class="meta">算术超额（组合 - 指数）| 几何超额 <b class="up">+{S['ex_geo']:.2f}%</b><br>日超额胜率 {S['ex_win']:.1f}% | 跟踪误差 {S['te']:.2f}% | Beta {S['beta']:.2f}</div>
  </div>
</div>

<div class="cards">
  <div class="card lose">
    <div class="name">中芯国际 688981 <span class="tag tag-blue">指数权重第2</span></div>
    <div class="big up">+{zx['tot']:.2f}%</div>
    <div class="meta">94.62 → 122.83 元 | 权重 8.444%<br>年内高 {H['688981'][0]:.2f}（{H['688981'][1][4:6]}/{H['688981'][1][6:]}）距高 -19.72% | 年内低 {H['688981'][2]:.2f}（4/7）<br>波动 {zx['vol']:.2f}% | 回撤 {zx['mdd']:.2f}% | 夏普 {zx['sharpe']:.2f} | 跑输指数 <b class="down">{S['per_ex']['中芯国际']:+.2f}pct</b></div>
  </div>
  <div class="card win">
    <div class="name">寒武纪 688256 <span class="tag tag-blue">指数权重第3</span></div>
    <div class="big up">+{hw['tot']:.2f}%</div>
    <div class="meta">440.60 → 908.76 元 | 权重 8.134%<br>年内高 {H['688256'][0]:.2f}（8/28）距高 -15.07% | 年内低 {H['688256'][2]:.2f}（7/10）<br>波动 {hw['vol']:.2f}% | 回撤 {hw['mdd']:.2f}% | 夏普 {hw['sharpe']:.2f} | 跑赢指数 <b class="up">{S['per_ex']['寒武纪']:+.2f}pct</b></div>
  </div>
  <div class="card win">
    <div class="name">海光信息 688041 <span class="tag tag-blue">指数权重第4</span></div>
    <div class="big up">+{hg['tot']:.2f}%</div>
    <div class="meta">149.38 → 224.17 元 | 权重 7.602%<br>年内高 {H['688041'][0]:.2f}（9/25）距高 -19.29% | 年内低 {H['688041'][2]:.2f}（1/27）<br>波动 {hg['vol']:.2f}% | 回撤 {hg['mdd']:.2f}% | 夏普 {hg['sharpe']:.2f} | 跑输指数 <b class="down">{S['per_ex']['海光信息']:+.2f}pct</b></div>
  </div>
</div>
<div class="src">
来源：腾讯日K（前复权 qfq，覆盖 2024-11-01→2026-01-20），基准取 2024-12-31 收盘、终点取 2025-12-31 收盘，共 244 个交易日。
口径已与通达信交叉校验：2025-12-31 中芯收盘 122.83、指数收盘 2613.41，两源完全一致。
个股停牌日按「沿用前一交易日收盘」映射到指数主日历，符合买入持有的真实持有体验。
YTD 为价格涨幅口径，未含分红再投——三只股息率均极低，指数为价格指数，口径可比。
一致性校验全部通过：月度收益连乘 = 累计收益；等权分解 (1/3)Σ个股 = 组合实际 +62.04%；相关性矩阵对角线 = 1.000。
</div>

<div class="fact">
<b>组合口径说明（两种构建方式）：</b><br>
① <b>等权买入持有</b>（期初各投 1/3，之后不调整）：全年 <b>+62.04%</b>，最大回撤 -24.06%，夏普 1.19。这是「买了就不动」的真实体验。<br>
② <b>等权每日再平衡</b>（每天拉回 1/3）：全年 <b>+66.13%</b>，最大回撤 -23.50%，夏普 1.30。再平衡多出 4.09pct，来自高波动下的「再平衡溢价」。<br>
③ 期末权重已漂移至：中芯 26.7% / 寒武 <b>42.4%</b> / 海光 30.9%——<b>涨最多的寒武纪被动加仓到 42.4%</b>，组合的命运因此被单只票深度绑定。本报告除特别说明外均以口径 ① 为准。
</div>
""")

# ---- Section 2: 走势图 + 月度表 ----
P.append(f"""
<h2>二、2025 全年走势对比（归一化 = 0%）</h2>
<div class="toggle" id="tg1">
  <button class="on" onclick="sw('tg1','c_walk','t_walk',0)">走势图</button><button onclick="sw('tg1','c_walk','t_walk',1)">月度明细表</button>
</div>
<div id="c_walk" class="chart"></div>
<div id="t_walk" style="display:none">
<table>
<tr><th>月份</th><th class="n">组合(等权)</th><th class="n">科创芯片指数</th><th class="n">超额</th><th class="n">中芯国际</th><th class="n">寒武纪</th><th class="n">海光信息</th><th>阶段特征</th></tr>""")

NOTES = {
 "202501": "开年急跌，组合（高Beta）跌幅远超指数，超额 -6.86pct",
 "202502": "DeepSeek 行情点燃国产算力，寒武 +28.65%、海光 +25.08% 领涨",
 "202503": "全板块回调，组合再次放大下跌",
 "202504": "关税冲击后深蹲反弹，4/7 见年内最低（指数 1463.70）",
 "202505": "缩量调整，组合继续跑输",
 "202506": "指数小胜，组合微幅落后",
 "202507": "全球科技去杠杆前夜，7/10 组合触及年内最大回撤 -24.06%",
 "202508": "<b>全年胜负手</b>：寒武单月 +110.59%、组合 +61.94% vs 指数 +35.24%，单月超额 +26.70pct，几乎贡献全年全部超额",
 "202509": "指数续涨 +17.75%，组合仅 +8.40%（寒武 -11.23% 高位回调），超额 -9.35pct",
 "202510": "10/9 指数见收盘峰值 3071.05，组合 10/27 见峰值 +80.99%",
 "202511": "高位震荡回落，组合微跌",
 "202512": "年末小幅修复，组合 +3.90% 略输指数 +4.06%",
}
for m in months:
    pv = mo["port"][m]; iv = mo["idx"][m]; ev = round(pv - iv, 2)
    star = ' class="star"' if m == "202508" else ""
    P.append(f'<tr{star}><td>{m[:4]}-{m[4:]}</td>'
             f'<td class="n {up(pv)}">{sg(pv)}</td><td class="n {up(iv)}">{sg(iv)}</td>'
             f'<td class="n {up(ev)}">{ev:+.2f}</td>'
             f'<td class="n {up(mo["中芯国际"][m])}">{sg(mo["中芯国际"][m])}</td>'
             f'<td class="n {up(mo["寒武纪"][m])}">{sg(mo["寒武纪"][m])}</td>'
             f'<td class="n {up(mo["海光信息"][m])}">{sg(mo["海光信息"][m])}</td>'
             f'<td>{NOTES[m]}</td></tr>')
P.append(f"""</table>
<div class="note">月度涨幅按各月首末交易日收盘环比计算（前复权），「超额」为算术口径。组合 12 个月中仅 <b>5 个月</b>跑赢指数（2/4/7/8/10 月），且其中 4 个月是「跌得稍少」或小幅领先——<b>唯一一次决定性的主动超额来自 8 月（+26.70pct）</b>。其余 11 个月超额合计 <b class="down">-16.62pct</b>。来源：腾讯日K，自行计算。</div>
</div>

<h2>三、回撤结构与风险特征：高 Beta 的双刃剑</h2>
<div id="c_dd" class="chart"></div>
<div class="note">
收盘价距滚动峰值的回撤。组合最大回撤 <b class="down">-24.06%</b>（年初→7/10 谷底），指数 <b class="down">-19.30%</b>（年初→4/7 谷底）。
<b>组合回撤比指数深 4.76pct</b>，且谷底出现在 7/10（晚于指数的 4/7），说明组合在年中那波全球科技去杠杆中受伤更重。
个股回撤：中芯 -22.17%、寒武 -34.30%、海光 -26.21%——寒武纪波动最剧烈（年化波动 70.43%）。
组合内部日收益相关性均值 <b>0.616</b>，三只同属国产算力链，等权配置几乎没有分散化效果。
来源：腾讯日K前复权，自行计算。
</div>

<div class="grid2">
<div>
<h3>日收益相关性矩阵</h3>
<table class="kv">
<tr><th></th><th class="n">中芯</th><th class="n">寒武</th><th class="n">海光</th><th class="n">指数</th></tr>""")
cm = d["corr_matrix"]; nmrow = ["中芯国际", "寒武纪", "海光信息", "科创芯片指数"]
lbl = ["中芯", "寒武", "海光", "指数"]
for i in range(4):
    cells = "".join(f'<td class="n">{cm[i][j]:.3f}</td>' for j in range(4))
    bold = ' style="font-weight:700"' if i == 3 else ""
    P.append(f'<tr{bold}><td>{nmrow[i]}</td>{cells}</tr>')
P.append(f"""</table>
<div class="note">内部平均相关 0.616（中芯-寒武 0.595、中芯-海光 0.591、寒武-海光 0.762）。三只对指数相关 0.810/0.741/0.785。本质仍是<b>单一高 Beta 行业因子暴露</b>，不是真正的多标的分散组合。</div>
</div>
<div>
<h3>捕获率与风险收益结构</h3>
<table class="kv">
<tr><th>指标</th><th class="n">数值</th><th>解读</th></tr>
<tr><td>上行捕获率</td><td class="n up"><b>{S['up_cap']:.1f}%</b></td><td>指数上涨日组合涨得更多（高Beta放大）</td></tr>
<tr><td>下行捕获率</td><td class="n down"><b>{S['dn_cap']:.1f}%</b></td><td>指数下跌日组合也跌得更多</td></tr>
<tr><td>Beta</td><td class="n"><b>{S['beta']:.2f}</b></td><td>典型高Beta，指数1%→组合约1.25%</td></tr>
<tr><td>相关系数</td><td class="n">{S['corr']:.3f}</td><td>方向高度贴合指数</td></tr>
<tr><td>跟踪误差(年化)</td><td class="n"><b>{S['te']:.2f}%</b></td><td>偏离幅度极大（与2026的25.82%几乎相同）</td></tr>
<tr><td>夏普比率</td><td class="n down"><b>{port['sharpe']:.2f}</b> &lt; 指数{idx['sharpe']:.2f}</td><td>单位风险收益不如指数</td></tr>
<tr><td>指数涨日({S['up_days']}天)日均</td><td class="n">组合放大上涨</td><td>—</td></tr>
<tr><td>指数&gt;+3%({S['big_up_n']}天)</td><td class="n">指数{S['big_up_idx']:+.2f}% / 组合{S['big_up_p']:+.2f}%</td><td class="up">大涨日跑赢 {S['big_up_p']-S['big_up_idx']:+.2f}pct</td></tr>
<tr><td>指数&lt;-3%({S['big_dn_n']}天)</td><td class="n">指数{S['big_dn_idx']:+.2f}% / 组合{S['big_dn_p']:+.2f}%</td><td class="down">大跌日多跌 {S['big_dn_p']-S['big_dn_idx']:+.2f}pct</td></tr>
</table>
<div class="note"><b>「Beta 1.25 + 上下行捕获都 &gt;117%」= 高 Beta 放大器</b>。在 2025 单边牛市中它放大收益、贡献正超额；但放大器不分方向，2026 年市场转弱时它同样放大亏损——这正是 2026 跑输 35pct 的结构根源。来源：日收益序列自行计算。</div>
</div>
</div>
""")

open(os.path.join(BASE, "out", "frag25_a.html"), "w", encoding="utf-8").write("".join(P))
print("frag25_a.html written, bytes:", len("".join(P).encode("utf-8")))
