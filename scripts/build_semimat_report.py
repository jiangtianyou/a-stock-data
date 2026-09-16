# -*- coding: utf-8 -*-
import json, os

with open("out/semimat_stats.json", encoding="utf-8") as f:
    stats_data = json.load(f)

stats = stats_data["stats"]
norm = stats_data["norm"]
corr = stats_data["corr"]
dates = norm["彤程新材"]["dates"]

html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>半导体材料四强8月以来走势复盘与对比分析（2026-08-01 ~ 2026-09-16）</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif; background:#f7f8fa; color:#2b2f36; line-height:1.65; }}
  .wrap {{ max-width:1100px; margin:0 auto; padding:28px 20px 60px; }}
  h1 {{ font-size:26px; margin-bottom:6px; color:#1e242c; }}
  .sub {{ color:#8a919c; font-size:13px; margin-bottom:24px; }}
  h2 {{ font-size:19px; margin:36px 0 14px; padding-left:10px; border-left:4px solid #3b82f6; color:#1f2937; }}
  h3 {{ font-size:15px; margin:20px 0 8px; color:#374151; }}
  .tldr {{ background:#fff; border:1px solid #e8eaee; border-radius:10px; padding:20px 22px; margin-bottom:12px; box-shadow:0 1px 3px rgba(0,0,0,.04); }}
  .tldr li {{ margin:7px 0 7px 18px; font-size:14px; }}
  .cards {{ display:flex; gap:14px; flex-wrap:wrap; margin:18px 0; }}
  .card {{ flex:1; min-width:230px; background:#fff; border:1px solid #e8eaee; border-radius:10px; padding:16px 18px; box-shadow:0 1px 3px rgba(0,0,0,.04); position:relative; }}
  .card .name {{ font-size:14px; color:#6b7280; font-weight:500; }}
  .card .big {{ font-size:28px; font-weight:700; margin:4px 0; }}
  .up {{ color:#dc2626; }} .down {{ color:#16a34a; }} .muted {{ color:#9ca3af; font-size:12.5px; }}
  .card .meta {{ font-size:12.5px; color:#6b7280; line-height:1.5; }}
  table {{ width:100%; border-collapse:collapse; background:#fff; font-size:13.5px; border:1px solid #e8eaee; border-radius:8px; overflow:hidden; margin:14px 0; }}
  th {{ background:#f3f4f6; padding:10px 12px; text-align:left; font-weight:600; color:#374151; white-space:nowrap; }}
  td {{ padding:9px 12px; border-top:1px solid #f3f4f6; }}
  tr:hover td {{ background:#f9fafb; }}
  .chart {{ width:100%; height:450px; background:#fff; border:1px solid #e8eaee; border-radius:10px; padding:12px; box-shadow:0 1px 3px rgba(0,0,0,.04); margin-bottom:16px; }}
  .tag {{ display:inline-block; font-size:11px; padding:2px 8px; border-radius:12px; margin-right:4px; vertical-align:1px; font-weight:500; }}
  .tag-blue {{ background:#eff6ff; color:#2563eb; }}
  .tag-purple {{ background:#f5f3ff; color:#7c3aed; }}
  .tag-red {{ background:#fef2f2; color:#dc2626; }}
  .tag-gray {{ background:#f3f4f6; color:#4b5563; }}
  .analysis-box {{ background:#fff; border:1px solid #e5e7eb; border-radius:10px; padding:18px 20px; margin:16px 0; }}
  .analysis-box h4 {{ font-size:15px; margin-bottom:8px; color:#111827; }}
  .highlight {{ color:#2563eb; font-weight:600; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>半导体材料四强 8 月以来走势复盘与对比分析</h1>
  <div class="sub">标的：彤程新材(603650)、有研新材(600206)、雅克科技(002409)、江丰电子(300666) | 基准：科创50(000688) | 数据区间：2026-08-01 ~ 2026-09-16</div>

  <div class="tldr">
    <b>TL;DR 核心结论</b>
    <ul>
      <li><b>跑赢基准，全员超额</b>：8月以来四只材料标的全线跑赢科创50指数（同期科创50 <span class="down">-1.21%</span>），区间收益排名：<b>有研新材(+46.07%) &gt; 彤程新材(+27.90%) &gt; 江丰电子(+24.29%) &gt; 雅克科技(+2.47%)</b>。</li>
      <li><b>三阶段步调高度一致</b>：① <b>8.03-8.18 强力共振上攻</b>（雅克8/17见顶，其余三股及指数8/18-8/19见顶）；② <b>8.19-9.04 获利盘退潮深幅回踩</b>（四股全部在 <b>9月4日同日见底</b>，回撤19%~23%）；③ <b>9.05-9.16 逻辑与资金分化</b>。</li>
      <li><b>9月分化新格局</b>：<b>彤程新材</b>量能维持96%，走出独立新高主升形态，距前高仅 <b>-1.79%</b>；<b>有研新材</b>9/16放量涨停，高弹性题材与情绪龙头属性尽显；<b>江丰电子与雅克科技</b>日收益相关度高达 <b>0.921</b>，跟随机构白马稳步修复。</li>
    </ul>
  </div>

  <h2>一、核心区间指标对比看板</h2>
  <div class="cards">
    <div class="card">
      <div class="name">彤程新材 (603650) <span class="tag tag-blue">光刻胶龙头·形态最强</span></div>
      <div class="big up">+27.90%</div>
      <div class="meta">
        最新：<b>69.31 元</b> (距前高 -1.79%)<br>
        8月：+16.26% | 9月：+10.02%<br>
        区间最大回撤：<b>-19.00%</b> (抗跌韧性第1)<br>
        相对科创50超额：<b>+29.11%</b>
      </div>
    </div>
    <div class="card">
      <div class="name">有研新材 (600206) <span class="tag tag-red">靶材/固态·弹性第1</span></div>
      <div class="big up">+46.07%</div>
      <div class="meta">
        最新：<b>51.63 元</b> (今日涨停)<br>
        8月：+46.32% | 9月：-0.17%<br>
        区间最大回撤：<b>-23.13%</b> (波动第1)<br>
        相对科创50超额：<b>+47.28%</b>
      </div>
    </div>
    <div class="card">
      <div class="name">江丰电子 (300666) <span class="tag tag-purple">超高纯靶材+零部件</span></div>
      <div class="big up">+24.29%</div>
      <div class="meta">
        最新：<b>252.83 元</b> (距前高 -9.15%)<br>
        8月：+19.99% | 9月：+3.58%<br>
        区间最大回撤：<b>-20.88%</b><br>
        相对科创50超额：<b>+25.50%</b>
      </div>
    </div>
    <div class="card">
      <div class="name">雅克科技 (002409) <span class="tag tag-gray">前驱体/特气·相对滞涨</span></div>
      <div class="big up">+2.47%</div>
      <div class="meta">
        最新：<b>137.11 元</b> (距前高 -13.77%)<br>
        8月：+6.41% | 9月：-3.69%<br>
        区间最大回撤：<b>-20.37%</b><br>
        相对科创50超额：<b>+3.68%</b>
      </div>
    </div>
  </div>

  <h2>二、区间归一化走势对比 (基期 2026-07-31 = 100)</h2>
  <div id="chart-norm" class="chart"></div>

  <h2>三、全维度统计对比表</h2>
  <table>
    <thead>
      <tr>
        <th>标的</th>
        <th>细分赛道定位</th>
        <th>区间涨跌幅</th>
        <th>8月单月</th>
        <th>9月至今</th>
        <th>区间高点(日期)</th>
        <th>距高点回撤</th>
        <th>最大回撤区间</th>
        <th>日收益波动率</th>
        <th>9月/8月量比</th>
        <th>相对科创50超额</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><b>彤程新材</b></td>
        <td>光刻胶/特种树脂</td>
        <td class="up"><b>+27.90%</b></td>
        <td class="up">+16.26%</td>
        <td class="up"><b>+10.02%</b></td>
        <td>70.57 (08-18)</td>
        <td><b>-1.79%</b></td>
        <td>-19.00% (08/18→09/04)</td>
        <td>3.92%</td>
        <td><b>0.96</b> (量能充沛)</td>
        <td class="up">+29.11%</td>
      </tr>
      <tr>
        <td><b>有研新材</b></td>
        <td>靶材/稀土/固态电池</td>
        <td class="up"><b>+46.07%</b></td>
        <td class="up"><b>+46.32%</b></td>
        <td>-0.17%</td>
        <td>58.83 (08-19)</td>
        <td>-12.23%</td>
        <td>-23.13% (08/19→09/04)</td>
        <td>5.07%</td>
        <td>0.62</td>
        <td class="up"><b>+47.28%</b></td>
      </tr>
      <tr>
        <td><b>江丰电子</b></td>
        <td>高纯靶材/半导体零部件</td>
        <td class="up"><b>+24.29%</b></td>
        <td class="up">+19.99%</td>
        <td class="up">+3.58%</td>
        <td>278.28 (08-18)</td>
        <td>-9.15%</td>
        <td>-20.88% (08/18→09/04)</td>
        <td>4.99%</td>
        <td>0.60</td>
        <td class="up">+25.50%</td>
      </tr>
      <tr>
        <td><b>雅克科技</b></td>
        <td>前驱体/特气/球硅</td>
        <td class="up"><b>+2.47%</b></td>
        <td class="up">+6.41%</td>
        <td class="down">-3.69%</td>
        <td>159.01 (08-17)</td>
        <td>-13.77%</td>
        <td>-20.37% (08/17→09/04)</td>
        <td>4.28%</td>
        <td>0.57</td>
        <td class="up">+3.68%</td>
      </tr>
      <tr style="background:#fafafa;">
        <td><b>科创50</b></td>
        <td>板块基准</td>
        <td class="down">-1.21%</td>
        <td class="up">+2.96%</td>
        <td class="down">-4.05%</td>
        <td>1790.87 (08-18)</td>
        <td>-9.75%</td>
        <td>-14.66% (08/18→09/14)</td>
        <td>2.56%</td>
        <td>0.69</td>
        <td>--</td>
      </tr>
    </tbody>
  </table>

  <h2>四、两两收益率相关系数矩阵</h2>
  <table>
    <thead>
      <tr>
        <th>标的组合</th>
        <th>相关系数 (r)</th>
        <th>协同效应与同动性解读</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><b>雅克科技 vs 江丰电子</b></td>
        <td><b class="highlight">0.921</b></td>
        <td><b>高度绑定</b>：典型的半导体材料机构核心重仓股，走势与海外半导体/存储产业链强相关</td>
      </tr>
      <tr>
        <td><b>江丰电子 vs 有研新材</b></td>
        <td><b>0.767</b></td>
        <td><b>靶材双雄</b>：同处超高纯金属溅射靶材赛道，享受靶材国产化与产线稼动率红利</td>
      </tr>
      <tr>
        <td><b>彤程新材 vs 江丰电子</b></td>
        <td><b>0.768</b></td>
        <td>半导体材料先进制程突破主线，走势协同良好</td>
      </tr>
      <tr>
        <td><b>彤程新材 vs 雅克科技</b></td>
        <td><b>0.723</b></td>
        <td>前驱体与光刻胶均为晶圆制造核心化学品耗材</td>
      </tr>
      <tr>
        <td><b>彤程新材 vs 有研新材</b></td>
        <td><b>0.717</b></td>
        <td>各自龙头的独立催化较多（光刻胶独立趋势 vs 题材情绪博弈）</td>
      </tr>
      <tr>
        <td><b>有研新材 vs 雅克科技</b></td>
        <td><b>0.707</b></td>
        <td>风格差异明显，有研偏游资情绪弹性，雅克偏机构白马</td>
      </tr>
    </tbody>
  </table>

  <h2>五、走势复盘：三阶段节奏演进与归因</h2>
  
  <div class="analysis-box">
    <h4>阶段一（8月3日 ~ 8月18/19日）：政策与产业共振，全线主升浪</h4>
    <p><b>现象</b>：8月初探底后，半导体自主可控情绪引爆，四股全面暴涨，期间<b>有研新材自低点飙升 +77.7%</b>，江丰电子 +50.4%，彤程新材 +39.0%，雅克科技 +31.5%。四股先后于 8/17~8/19 冲顶。</p>
    <p><b>催化</b>：先进制程扩产预期提升，半导体材料作为国产替代“卡脖子”攻坚环节，迎来资金集中配置；有研新材叠加了央企资产整合与前沿新材料溢价，资金进攻欲望最强烈。</p>
  </div>

  <div class="analysis-box">
    <h4>阶段二（8月19日 ~ 9月4日）：高位分歧兑现，同日见底回踩</h4>
    <p><b>现象</b>：获利盘了结叠加科技大盘震荡调整，四只个股进入深幅回调，回撤幅度均在 19%~23% 之间。神奇的是，<b>四只股票全部在 9月4日 同日触及波段最低点</b>。</p>
    <p><b>特征</b>：彤程新材表现出最强抗跌性（最大回撤 -19.00% 为个股最低），而有研新材（-23.13%）由于前期获利盘过于丰厚，回撤最为剧烈。</p>
  </div>

  <div class="analysis-box">
    <h4>阶段三（9月5日 ~ 9月16日）：分化加剧，龙头新高与题材爆发</h4>
    <p><b>现象</b>：见底后各奔前程：</p>
    <ul style="margin-left:20px; font-size:13.5px; line-height:1.7;">
      <li><b>彤程新材（最强趋势龙）</b>：9月逆势上涨 +10.02%，日均成交量维持在8月的 96%，资金承接极佳，9月16日收于 69.31 元，距离前期天花板仅 -1.79%，展现出“领涨先锋”姿态。</li>
      <li><b>有研新材（最强弹性题材）</b>：9月4日探底后经过平台蓄势，9月16日放量涨停，单日涨幅 9.99%，直接抹平9月前期回调，显示超强的情绪召集力。</li>
      <li><b>江丰电子（机构成长标的）</b>：跟随大盘企稳温和上行，距高点 -9.15%，走势中规中矩。</li>
      <li><b>雅克科技（相对滞涨）</b>：9月量能萎缩至8月的 57%，资金流向光刻胶及高弹性题材，雅克作为大市值白马短期缺乏增量催化，在四强中涨幅居后。</li>
    </ul>
  </div>

  <h2>六、四强业务壁垒与驱动力对比</h2>
  <table>
    <thead>
      <tr>
        <th>标的</th>
        <th>核心壁垒与业务看点</th>
        <th>市场驱动力与催化剂</th>
        <th>盘面风格与资金属性</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><b>彤程新材</b></td>
        <td>国内光刻胶领军者，北京科华KrF/ArF光刻胶批量供货，北旭电子面板光刻胶市占高</td>
        <td>国产光刻胶导入验证加速，先进制程扩产关键材料刚需，基本面与技术突破共振</td>
        <td><b>机构与趋势资金深度锁仓</b>，走势呈独立多头趋势，承接盘极其充沛</td>
      </tr>
      <tr>
        <td><b>有研新材</b></td>
        <td>稀土永磁+铜铝钛钽高纯溅射靶材（有研亿金）+红外材料，央企平台背景</td>
        <td>超高纯金属材料自主可控，固态电池材料想象空间，国企改革与并购重组预期</td>
        <td><b>高β游资与活跃资金最爱</b>，爆发力强、波动大、换手充分</td>
      </tr>
      <tr>
        <td><b>江丰电子</b></td>
        <td>超高纯溅射靶材全球第一梯队，第二曲线半导体零部件（精密金属部件）高增</td>
        <td>先进制程晶圆厂扩产带动的靶材消耗增长，零部件国产替代打开天花板</td>
        <td><b>成长型机构重仓股</b>，创业板20cm弹性，波段节奏鲜明</td>
      </tr>
      <tr>
        <td><b>雅克科技</b></td>
        <td>High-k前驱体全球前列，供应海力士/三星/长存等，电子特气与球硅包装齐备</td>
        <td>存储大厂HBM产能扩张拉动前驱体需求，先进封装材料需求放量</td>
        <td><b>白马蓝筹属性较强</b>，基本面确定性高但短期受量能抑制，弹性偏低</td>
      </tr>
    </tbody>
  </table>
</div>

<script>
  const dates = {json.dumps(dates)};
  const chart = echarts.init(document.getElementById('chart-norm'));
  const option = {{
    title: {{ text: '8月以来归一化净值走势（2026-07-31 = 100）', left: 'center', top: 5, textStyle: {{ fontSize: 14, color: '#374151' }} }},
    tooltip: {{
      trigger: 'axis',
      formatter: function(params) {{
        let s = params[0].axisValue + '<br/>';
        params.forEach(p => {{
          s += p.marker + ' ' + p.seriesName + ': <b>' + p.value + '</b><br/>';
        }});
        return s;
      }}
    }},
    legend: {{ data: ['彤程新材', '有研新材', '雅克科技', '江丰电子', '科创50'], top: 30 }},
    grid: {{ left: '4%', right: '4%', bottom: '8%', top: '16%', containLabel: true }},
    xAxis: {{
      type: 'category',
      data: dates,
      axisLabel: {{
        formatter: function(v) {{ return v.substring(5); }}
      }}
    }},
    yAxis: {{
      type: 'value',
      scale: true,
      splitLine: {{ lineStyle: {{ stroke: '#f3f4f6', type: 'dashed' }} }}
    }},
    series: [
      {{ name: '彤程新材', type: 'line', data: {json.dumps(norm["彤程新材"]["vals"])}, smooth: true, lineStyle: {{ width: 3, color: '#2563eb' }}, itemStyle: {{ color: '#2563eb' }} }},
      {{ name: '有研新材', type: 'line', data: {json.dumps(norm["有研新材"]["vals"])}, smooth: true, lineStyle: {{ width: 2.5, color: '#dc2626' }}, itemStyle: {{ color: '#dc2626' }} }},
      {{ name: '雅克科技', type: 'line', data: {json.dumps(norm["雅克科技"]["vals"])}, smooth: true, lineStyle: {{ width: 2, color: '#9ca3af' }}, itemStyle: {{ color: '#9ca3af' }} }},
      {{ name: '江丰电子', type: 'line', data: {json.dumps(norm["江丰电子"]["vals"])}, smooth: true, lineStyle: {{ width: 2.5, color: '#7c3aed' }}, itemStyle: {{ color: '#7c3aed' }} }},
      {{ name: '科创50', type: 'line', data: {json.dumps(norm["科创50"]["vals"])}, smooth: true, lineStyle: {{ width: 1.5, type: 'dashed', color: '#6b7280' }}, itemStyle: {{ color: '#6b7280' }} }}
    ]
  }};
  chart.setOption(option);
  window.addEventListener('resize', () => chart.resize());
</script>
</body>
</html>
"""

os.makedirs("reports", exist_ok=True)
with open("reports/半导体材料四强8月以来走势复盘-20260916.html", "w", encoding="utf-8") as f:
    f.write(html_content)
print("saved reports/半导体材料四强8月以来走势复盘-20260916.html")
