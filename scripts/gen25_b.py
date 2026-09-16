import json, os

BASE = r"D:\Desktop\Playground\a-stock-data"
d = json.load(open(os.path.join(BASE, "out", "final2025.json"), encoding="utf-8"))
a = json.load(open(os.path.join(BASE, "out", "attribution2025.json"), encoding="utf-8"))
M = d["metrics"]; S = d["stats"]; mo = d["monthly"]; months = d["months"]
rows = a["rank"]; groups = a["groups"]; sm = a["summary"]

def up(v): return "up" if v >= 0 else "down"
def sg(v, unit="%"): return ('+' if v >= 0 else '') + f"{v:.2f}" + unit

P = []
P.append(f"""
<h2>四、为什么只赢 0.71pct？—— 2025 指数成分归因</h2>
<div class="fact">
<b>和 2026 一样，2025 年组合也没有抓住指数真正的 alpha。</b>组合三只仍是指数第 2、3、4 大权重股（合计 24.18%），但在前 20 大成分股的 2025 YTD 排名中：
寒武纪第 <b>7</b>（+106.25%）、海光信息第 <b>17</b>（+50.07%）、中芯国际第 <b>20</b>（+29.81%，连续两年倒数第1）。
前 20 大等权 2025 YTD 高达 <b>+{sm['eq_all20']:.2f}%</b>，而组合三只等权仅 +{sm['eq_top3']:.2f}%，其余 17 只等权 <b>+{sm['eq_rest17']:.2f}%</b>，差距 <b>{sm['gap_top3']:.2f}pct</b>。
组合 2025 年之所以还能微幅跑赢指数，纯粹是因为<b>指数本身被中芯、海光两只大权重拖累了</b>（指数是市值加权，前 20 大占 78%，但中芯/海光在指数里的高权重稀释了二线的爆发），而不是组合选股有多好。
</div>
<div class="toggle" id="tg2">
  <button class="on" onclick="sw('tg2','c_rank','t_rank',0)">前20大 2025 YTD 排行</button><button onclick="sw('tg2','c_rank','t_rank',1)">子板块归因</button><button onclick="sw('tg2','c_rank','t_rank',2)">明细表</button>
</div>
<div id="c_rank" class="chart tall"></div>
<div id="t_rank" style="display:none">
<h3>子板块等权 2025 YTD（前 20 大成分股分组）</h3>
<table>
<tr><th>子板块</th><th class="n">只数</th><th class="n">指数权重合计</th><th class="n">等权 YTD</th><th>代表标的</th></tr>""")
for g in groups:
    star = ' class="star"' if g["in_port"] else ""
    mem = sorted(g["members"], key=lambda x: -x["ytd"])
    rep = " / ".join(f'{m["name"]} {m["ytd"]:+.2f}%' for m in mem[:4])
    tag = " ←含组合" if g["in_port"] else ""
    P.append(f'<tr{star}><td><b>{g["name"]}</b>{tag}</td><td class="n">{g["n"]}</td><td class="n">{g["w"]:.2f}%</td>'
             f'<td class="n {up(g["eq_ytd"])}"><b>{g["eq_ytd"]:+.2f}%</b></td><td>{rep}</td></tr>')
P.append(f"""<tr><td>前20大整体</td><td class="n">20</td><td class="n">78.17%</td><td class="n up">+{sm['eq_all20']:.2f}%</td><td>等权口径</td></tr>
<tr><td><b>★本组合三只</b></td><td class="n">3</td><td class="n">24.18%</td><td class="n up"><b>+{sm['eq_top3']:.2f}%</b></td><td>等权口径</td></tr>
<tr><td>其余 17 只前 20 大</td><td class="n">17</td><td class="n">53.99%</td><td class="n up"><b>+{sm['eq_rest17']:.2f}%</b></td><td>反事实：若持有它们，超额 <b class="up">{sm['eq_rest17']-sm['eq_top3']:+.2f}pct</b></td></tr>
</table>
<div class="note">
等权口径（算术平均）消除权重漂移干扰，可精确比较，与组合买入持有 +62.04% 自洽。子板块按通达信三级行业人工归组。
<b>2025 年的 alpha 在光芯片（等权 +300.92%）和算力设计中的芯原股份（+161.24%）</b>，组合三只里只有寒武纪跟上了节奏。
注意：<b>同为晶圆制造，华虹宏力 2025 +132.13% vs 中芯国际 +29.81%，相差 102pct</b>——和 2026 年如出一辙，中芯国际连续两年大幅跑输同环节的华虹。
</div>
</div>
<div id="t_rank2" style="display:none">
<h3>科创芯片指数前 20 大成分股 2025 YTD 明细</h3>
<table>
<tr><th class="n">2025排名</th><th>证券简称</th><th>代码</th><th class="n">指数权重</th><th class="n">2025 YTD</th><th class="n">距25年高点</th><th class="n">2026 YTD</th><th class="n">2026排名</th><th>子板块</th></tr>""")
for r in rows:
    star = ' class="star"' if r["in_port"] else ""
    nm = r["name"] + (" ★" if r["in_port"] else "")
    y26 = f'{r["ytd26"]:+.2f}%' if r["ytd26"] is not None else "—"
    r26 = r["rank26"] if r["rank26"] else "—"
    P.append(f'<tr{star}><td class="n">{r["rank"]}</td><td>{nm}</td><td>{r["code"]}</td><td class="n">{r["weight"]:.3f}%</td>'
             f'<td class="n {up(r["ytd"])}">{r["ytd"]:+.2f}%</td><td class="n down">{r["off_hi"]:+.2f}%</td>'
             f'<td class="n {up(r["ytd26"]) if r["ytd26"] else ""}">{y26}</td><td class="n">{r26}</td><td>{r["grp"]}</td></tr>')
P.append(f"""</table>
<div class="note">
权重为通达信 F9 成分股权重（2026-09-14 快照）；2025 YTD 以 2024-12-31 前复权收盘为基准、2025-12-31 收盘为终点；2026 YTD 截至 2026-09-14。
前 20 大合计权重 78.17%。「距25年高点」= 2025-12-31 收盘相对 2025 年内最高价的回撤。
</div>
</div>

<h2>五、跨年对照：2025 的赢家，2026 还在赢吗？</h2>
<div class="warn">
<b>这是把两年放在一起看才能发现的最重要规律。</b>
2025 年涨幅榜前列的二线股（光芯片、设备、晶圆代工里的非中芯标的），到 2026 年<b>继续</b>占据涨幅榜前列；而组合三只里，除了寒武纪从第 7 滑到第 18，中芯国际<b>连续两年倒数第 1</b>、海光信息从第 17 滑到第 19。
<b>市场奖励的从来不是「龙头地位」或「市值权重」，而是「业绩变化率与预期差」。</b>组合押注的是「确定性龙头」，但 2025-2026 这两年，确定性龙头恰恰是预期最充分、边际变化最小的一类。
</div>
<div id="c_cross" class="chart tall"></div>
<div class="note">散点图：横轴 2025 YTD、纵轴 2026 YTD，每个点是一只前 20 大成分股，红色为组合三只。<b>右上角（两年都强）的是源杰、华峰测控、华海清科、盛科通信等二线</b>；<b>左下角（两年都弱）的恰是中芯国际</b>。寒武纪从右上滑向左上（2025 强、2026 转弱）。这张图直观说明：组合的失败不是 2026 年的偶然，而是 2025 年就已注定的结构问题。来源：腾讯日K前复权，自行计算。</div>

<h3>排名迁移明细（2025 → 2026）</h3>
<table>
<tr><th>证券简称</th><th class="n">2025 YTD</th><th class="n">2025排名</th><th class="n">2026 YTD</th><th class="n">2026排名</th><th class="n">排名变化</th><th>趋势</th></tr>""")
# 按 2026 排名升序展示迁移
rows_by26 = sorted([r for r in rows if r["rank26"]], key=lambda x: x["rank26"])
for r in rows_by26:
    delta = r["rank"] - r["rank26"]   # 正=上升(排名数字变小)
    if delta > 0: arrow, cls, txt = f"↑{delta}", "up", "走强"
    elif delta < 0: arrow, cls, txt = f"↓{-delta}", "down", "走弱"
    else: arrow, cls, txt = "→", "", "持平"
    star = ' class="star"' if r["in_port"] else ""
    nm = r["name"] + (" ★" if r["in_port"] else "")
    P.append(f'<tr{star}><td>{nm}</td><td class="n {up(r["ytd"])}">{r["ytd"]:+.2f}%</td><td class="n">{r["rank"]}</td>'
             f'<td class="n {up(r["ytd26"])}">{r["ytd26"]:+.2f}%</td><td class="n">{r["rank26"]}</td>'
             f'<td class="n {cls}"><b>{arrow}</b></td><td>{txt}</td></tr>')
P.append("""</table>
<div class="note">排名变化 = 2025排名 - 2026排名，正数（↑）表示 2026 相对走强、排名上升。<b>上升最多的是华海清科（↑15）、普冉股份（↑11）、盛科通信（↑11）、中科飞测（↑8）、华峰测控（↑7）、中微公司（↑7）</b>——全是设备/材料/光芯片/存储二线；<b>下降最多的是芯原股份（↓13）、仕佳光子（↓12）、寒武纪（↓11）</b>。组合三只中，寒武纪大幅走弱、海光小幅走弱、中芯国际原地垫底。来源：腾讯日K前复权，自行计算。</div>
""")

open(os.path.join(BASE, "out", "frag25_b.html"), "w", encoding="utf-8").write("".join(P))
print("frag25_b.html written, bytes:", len("".join(P).encode("utf-8")))
