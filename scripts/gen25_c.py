import json, os

BASE = r"D:\Desktop\Playground\a-stock-data"
d = json.load(open(os.path.join(BASE, "out", "final2025.json"), encoding="utf-8"))
a = json.load(open(os.path.join(BASE, "out", "attribution2025.json"), encoding="utf-8"))
M = d["metrics"]; S = d["stats"]; sm = a["summary"]
port = M["组合(等权买入持有)"]; idx = M["科创芯片指数"]

P = []
P.append(f"""
<h2>六、结论：2025 的「赢」说明了什么</h2>
<div class="concl">
<p><b>结论一：2025 组合 +62.04% 微胜指数 +61.33%，但这是「高 Beta 撞大牛市」的结果，不是选股能力。</b>
组合 Beta 1.25、年化波动 51.01%（指数 36.11%）、上行捕获 117.1%、下行捕获 118.7%。在一个指数单边上涨 +61% 的年份，任何高 Beta 组合都会自然输出正超额——<b>这不是 alpha，是被市场 beta 抬上去的</b>。证据是风险调整后指标全面落后：夏普 1.19 &lt; 指数 1.67，Calmar 2.59 &lt; 3.19，最大回撤 -24.06% &gt; 指数 -19.30%。<b>承担更高的波动和回撤，换来几乎相同的收益，本质是亏的。</b></p>

<p><b>结论二：全年「胜利」高度依赖一个单月、一只单票，脆弱到极点。</b>
按时间拆：8 月单月超额 +26.69pct，剔除 8 月后组合全年仅 <b>+0.07%</b>、指数 +19.29%，反而跑输 19.22pct——<b>一年的胜负系于一个月</b>。
按个股拆：寒武纪 +106.25%（超额 +44.92pct）独力撑起组合，中芯 +29.81%（-31.52pct）、海光 +50.07%（-11.26pct）双双拖累——<b>组合的命运系于一只票</b>。
这种「单月 + 单票」的双重集中，意味着 2025 的跑赢几乎不可复制：8 月那波寒武纪 +110.59% 的暴涨是特定催化（业绩超预期 + AI 算力情绪顶点）下的产物，一旦催化消失（如 2026 年），高 Beta 立刻反向。</p>

<p><b>结论三：2025 年组合也没有抓住指数真正的 alpha，只是「输得没 2026 那么惨」。</b>
前 20 大等权 2025 YTD <b>+117.61%</b>，组合三只等权仅 +62.04%，其余 17 只等权 <b>+127.42%</b>，差距 -65.37pct。真正的涨幅王是光芯片（仕佳光子 +451.93%、源杰科技 +382.16%）、晶圆代工华虹（+132.13%）、设备（睿创 +115.87%、拓荆 +115.37%）。组合三只里只有寒武纪挤进前 10。<b>换句话说：如果 2025 年买的是指数其余 17 只，收益是 +127%，不是 +62%。</b></p>

<p><b>结论四（最关键）：2025 与 2026 是同一个故事的两面，组合的结构性缺陷从未改变。</b>
把两年放一起看：2025 的强势二线（源杰、华峰测控、华海清科、盛科通信、普冉）到 2026 年继续强势（排名分别 ↑1/↑7/↑15/↑11/↑11）；而组合三只，中芯国际<b>连续两年倒数第 1</b>、海光从第 17 滑到第 19、寒武纪从第 7 滑到第 18。
<b>这说明组合押注的「确定性龙头」逻辑，在 2025-2026 这两年是系统性失效的</b>：市场奖励「业绩变化率与预期差」，而龙头恰恰是预期最充分、边际变化最小的一类。2025 年靠牛市 beta + 寒武纪单点爆发勉强遮住了这个缺陷，2026 年 beta 退潮，缺陷立刻暴露为 -35pct 的惨败。<b>2026 的失败不是意外，是 2025 就已埋下的必然。</b></p>

<p><b>结论五：中芯国际是最值得单独警惕的一只。</b>
2025 +29.81%（前 20 大倒数第 1）、2026 YTD -7.13%（仍倒数第 1），<b>连续两年垫底</b>。而同为晶圆制造的华虹宏力 2025 +132.13%、2026 +95.35%，连续两年大幅领先中芯约 100pct。问题不在「晶圆制造」环节，而在中芯国际自身：A 股 PE(TTM) 109x、对 H 股溢价 +116%、自由流通比例仅约 23%，<b>高估值 + 筹码结构 + 预期透支</b>共同压制了它的相对表现。它是组合里「确定性龙头」逻辑破产最彻底的样本。</p>
</div>

<h3>两年合并视角：如果一直持有这个组合</h3>
<table>
<tr><th>区间</th><th class="n">组合(等权)</th><th class="n">科创芯片指数</th><th class="n">超额</th><th>说明</th></tr>
<tr><td>2025 全年</td><td class="n up">+62.04%</td><td class="n up">+61.33%</td><td class="n up">+0.71pct</td><td>高Beta撞牛市，靠8月+寒武纪险胜</td></tr>
<tr><td>2026 YTD（至9/14）</td><td class="n up">+2.37%</td><td class="n up">+37.84%</td><td class="n down">-35.47pct</td><td>beta退潮，结构性缺陷暴露</td></tr>
<tr class="star"><td><b>两年累计（2024末→2026/9/14）</b></td><td class="n up"><b>+65.88%</b></td><td class="n up"><b>+122.38%</b></td><td class="n down"><b>-56.50pct</b></td><td>合并看，组合大幅跑输指数</td></tr>
</table>
<div class="note">两年累计 = (1+2025收益)×(1+2026收益)-1，组合 1.6204×1.0237=1.6588（+65.88%），指数 1.6133×1.3784=2.2238（+122.38%）。<b>2025 年那点微弱领先，在 2026 年被彻底抹平并反超</b>——把时间拉长到两年，组合跑输指数 56.50pct（几何超额 -25.41%），「险胜一年」掩盖不了「整体失败」的本质。来源：腾讯/通达信日K前复权，自行计算。</div>

<h3>反事实情景（2025）：如果换一种配置</h3>
<table>
<tr><th>情景</th><th>构成</th><th class="n">2025 YTD</th><th class="n">vs 指数超额</th></tr>
<tr class="star"><td><b>实际持有</b></td><td>中芯+寒武+海光 等权买入持有</td><td class="n up"><b>+62.04%</b></td><td class="n up">+0.71pct</td></tr>
<tr><td>实际持有（每日再平衡）</td><td>同上，每日拉回 1/3</td><td class="n up">+66.13%</td><td class="n up">+4.80pct</td></tr>
<tr><td>基准</td><td>科创芯片指数 000685</td><td class="n up">+61.33%</td><td class="n">—</td></tr>
<tr><td>反事实 A</td><td>其余 17 只前 20 大等权</td><td class="n up">+127.42%</td><td class="n up">+66.09pct</td></tr>
<tr><td>反事实 B</td><td>前 20 大等权</td><td class="n up">+117.61%</td><td class="n up">+56.28pct</td></tr>
<tr><td>反事实 C</td><td>仅光芯片/存储 5 只等权</td><td class="n up">+213.00%</td><td class="n up">+151.67pct</td></tr>
</table>
<div class="note">反事实为等权口径回溯测算（未计交易成本与调仓约束），仅说明「选股方向」的影响量级，不构成可复制业绩。反事实 C 由光芯片(仕佳+451.93%/源杰+382.16%/盛科+68.68%)+存储(佰维+85.53%/普冉+76.61%)等权算术平均得到。来源：腾讯日K前复权，自行计算。</div>

<h2>七、数据与方法附录</h2>
<div class="fact" style="font-size:12.5px">
<b>数据源与口径</b><br>
① 行情：腾讯日K（web.ifzq.gtimg.cn，前复权 qfq，覆盖 2024-11-01 → 2026-01-20），基准日取 <b>2024-12-31 收盘</b>，终点取 <b>2025-12-31 收盘</b>，共 <b>244 个交易日</b>。<br>
② 交叉校验：通达信日K（前复权）锚点比对——2025-12-31 中芯国际收盘 122.83、科创芯片指数收盘 2613.41，腾讯与通达信<b>完全一致</b>。通达信对 000685 的历史深度不足（startxh=175/410 返回空），故 2025 全年序列以腾讯 qfq 为准，端点已校验。<br>
③ 指数权重：通达信 F9 成分股权重（2026-09-14 快照）。前 20 大合计 78.17%。<br>
④ 停牌处理：个股按「沿用前一交易日收盘」asof 映射到指数主日历，符合买入持有的真实持有体验（中芯 237 交易日、海光 233、寒武 243，差异为停牌/数据缺口，已对齐到 244 主日历）。<br>
⑤ YTD 为<b>价格涨幅口径</b>，未含分红再投资。三只股息率均极低，指数为价格指数，口径可比。<br><br>
<b>指标计算方法</b>（与 2026 报告完全一致，便于跨年对照）<br>
· 归一化收益：norm[i] = close[i]/close[base] - 1。年化收益：(1+tot)^(244/n) - 1。年化波动：日收益标准差 × √244。<br>
· 最大回撤：在净值序列上计算 max[(1+min_{{j≤i}})/(1+norm[i]) - 1]。夏普：(年化收益 - 1.5%) / 年化波动（无风险利率取 1.5%，2025 口径）。Calmar：年化收益 / |最大回撤|。<br>
· 捕获率：上行 = 指数上涨日组合日均涨幅 / 指数日均涨幅；下行同理。Beta/相关/跟踪误差基于日收益序列，TE = std(组合-指数日收益) × √244。<br>
· 超额：算术 = 组合YTD - 指数YTD；几何 = (1+组合)/(1+指数) - 1。<br>
· 「剔除 8 月」对比：用<b>日收益序列</b>剔除 2025-08 全部交易日后重新连乘，而非从月度表中删除 8 月（后者会错误跳过 7月末→9月末的整段，已避免）。<br><br>
<b>归因方法学</b><br>
与前报一致：指数为自由流通市值加权 + 权重上限 + 半年调仓，当前权重 × YTD 会因权重漂移虚高，历史流通股本不可得。故结构归因一律采用<b>等权口径（算术平均）</b>。已校验：组合三只等权 +62.04% == 买入持有实际 +62.04%。<br>
<b>子板块等权用算术平均而非连乘</b>——连乘会因复利把多只高涨幅股票乘出 +8812% 的荒谬值（开发中已发现并修正），等权买入持有的正确口径是算术平均。<br><br>
<b>一致性校验清单（全部通过，0 处偏差）</b><br>
· 月度收益连乘 == 累计收益（组合 +62.04%、指数 +61.33%/+61.35%，差 &lt;0.05 为四舍五入）。<br>
· 等权分解 (1/3)Σ个股 == 组合实际 +62.04%。<br>
· 相关性矩阵对角线 == 1.000。<br>
· 回撤序列终点 == metrics 中的 mdd。<br>
· 跨年日期比较统一用 YYYY-MM-DD 全日期；窗口收益用净值比值 norm[i1]/norm[i0]。
</div>

<div class="risk">
<b>风险提示</b><br>
1. 本报告为<b>历史数据回溯</b>，所有反事实情景均为等权口径测算，未计交易成本、冲击成本、流动性约束与调仓限制，不可视为可复制业绩，不构成对未来收益的预测。<br>
2. 2025 是 A 股半导体的单边大牛市（指数 +61.33%），组合的「微胜」高度依赖牛市 beta 与寒武纪 8 月单点爆发，<b>不具可持续性</b>——2026 YTD 已验证这一点（跑输 35.47pct）。<br>
3. 三只标的当前 PE(TTM) 分别为 109.4x / 141.8x / 144.7x（2026-09-14），处于极高估值区间；中芯 A 股对 H 股溢价 +116.1%，寒武纪存货占总资产 45.32%，海光经营现金流转负，均存在估值消化与基本面恶化风险。<br>
4. 半导体板块波动率年化 36%-70%，2025 组合最大回撤 -24.06%、指数 -19.30%，2026 更深；高弹性与高回撤是同一枚硬币的两面。<br>
5. 本报告<b>不构成任何投资建议</b>，所有个股陈述均为对已公开数据的整理与计算，不含买卖推荐。投资决策请自行判断并咨询持牌专业机构。
</div>

<div class="dis">
报告生成时间：2026-09-14 | 数据区间：2024-12-31 收盘 → 2025-12-31 收盘（244 个交易日）<br>
数据源：腾讯日K（前复权 qfq）、通达信 MCP（锚点交叉校验 / F9 成分股权重）、公司定期报告<br>
计算与制图：Python 标准库自行计算 + ECharts 5 | 所有指标均可由 out/final2025.json、out/attribution2025.json 复现<br>
本报告为《三剑客 2026 YTD 复盘》的前传，两份报告口径一致、可对照阅读。本报告由 WorkBuddy 生成，仅供研究学习使用，不构成投资建议。
</div>
</div>
""")

# ---- ECharts JS ----
J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
dates = d["full_dates"]; port_s = d["port_bh"]; idx_s = d["idx"]
exn = d["exn"]; exan = d["exan"]
ddp = d["dd_port"]; ddi = d["dd_idx"]; ddz = d["688981"]["dd"]; ddh = d["688256"]["dd"]; ddg = d["688041"]["dd"]
zx = d["688981"]["norm"]; hw = d["688256"]["norm"]; hg = d["688041"]["norm"]
rows = a["rank"]
rk_name = [r["name"] + ("★" if r["in_port"] else "") for r in rows]
rk_ytd = [r["ytd"] for r in rows]
rk_w = [r["weight"] for r in rows]
rk_port = [r["in_port"] for r in rows]
cross = [[r["ytd"], r["ytd26"], r["name"] + ("★" if r["in_port"] else ""), 1 if r["in_port"] else 0] for r in rows if r["ytd26"] is not None]

js = f"""
<script>
function sw(gid,cid,tid,k){{
  var g=document.getElementById(gid);var bs=g.getElementsByTagName('button');
  for(var i=0;i<bs.length;i++)bs[i].className=(i===k)?'on':'';
  var panes=[cid,tid,tid+'2'];
  for(var i=0;i<panes.length;i++){{var el=document.getElementById(panes[i]);if(el)el.style.display=(i===k)?'':'none';}}
  if(k===0&&window._charts&&window._charts[cid])window._charts[cid].resize();
}}
window._charts=window._charts||{{}};
var AX={{axisLine:{{lineStyle:{{color:'#d5d9e0'}}}},axisLabel:{{color:'#6b7280',fontSize:11}},splitLine:{{lineStyle:{{color:'#eef0f3'}}}}}};
var TIP={{trigger:'axis',backgroundColor:'rgba(255,255,255,.97)',borderColor:'#e0e3e8',borderWidth:1,textStyle:{{color:'#2b2f36',fontSize:12}},extraCssText:'box-shadow:0 4px 16px rgba(0,0,0,.10);border-radius:8px;'}};
function mk(id,opt){{var el=document.getElementById(id);if(!el)return;var c=echarts.init(el);c.setOption(opt);window._charts[id]=c;}}
window.addEventListener('resize',function(){{for(var k in window._charts)window._charts[k].resize();}});
var DATES={J(dates)};
var PORT={J(port_s)},IDX={J(idx_s)},EXN={J(exn)},EXA={J(exan)};
var ZX={J(zx)},HW={J(hw)},HG={J(hg)};
var DDP={J(ddp)},DDI={J(ddi)},DDZ={J(ddz)},DDH={J(ddh)},DDG={J(ddg)};
var RK_NAME={J(rk_name)},RK_YTD={J(rk_ytd)},RK_W={J(rk_w)},RK_PORT={J(rk_port)};
var CROSS={J(cross)};
var UP='#d0342c',DN='#1e8e4e',BLUE='#2c6bd0';

mk('c_walk',{{
  tooltip:Object.assign({{}},TIP,{{axisPointer:{{type:'cross',label:{{backgroundColor:'#5a616c'}}}},
    formatter:function(ps){{var s='<b>'+ps[0].axisValue+'</b><br/>';ps.sort(function(a,b){{return b.value-a.value;}});
      ps.forEach(function(p){{var c=p.value>=0?UP:DN;s+=p.marker+p.seriesName+': <b style="color:'+c+'">'+(p.value>=0?'+':'')+p.value.toFixed(2)+'%</b><br/>';}});return s;}}}}),
  legend:{{data:['等权组合','科创芯片指数','中芯国际','寒武纪','海光信息'],top:4,textStyle:{{color:'#4a505a',fontSize:12}}}},
  grid:{{left:58,right:26,top:44,bottom:64}},
  xAxis:Object.assign({{type:'category',data:DATES,boundaryGap:false,axisLabel:{{color:'#6b7280',fontSize:11,interval:15,formatter:function(v){{return v.slice(2);}}}}}},{{axisLine:AX.axisLine,splitLine:{{show:false}}}}),
  yAxis:Object.assign({{type:'value',name:'YTD 涨幅 %',nameTextStyle:{{color:'#8a919c',fontSize:11}},axisLabel:{{color:'#6b7280',fontSize:11,formatter:'{{value}}%'}}}},{{axisLine:AX.axisLine,splitLine:AX.splitLine}}),
  dataZoom:[{{type:'inside'}},{{type:'slider',height:18,bottom:14,borderColor:'#d5d9e0',fillerColor:'rgba(192,57,43,.10)',handleStyle:{{color:'#c0392b'}},textStyle:{{color:'#8a919c',fontSize:10}}}}],
  series:[
    {{name:'科创芯片指数',type:'line',data:IDX,symbol:'none',lineStyle:{{width:3,color:BLUE}},itemStyle:{{color:BLUE}},z:6,
      areaStyle:{{color:new echarts.graphic.LinearGradient(0,0,0,1,[{{offset:0,color:'rgba(44,107,208,.16)'}},{{offset:1,color:'rgba(44,107,208,0)'}}])}},
      markPoint:{{data:[{{type:'max',name:'峰值'}}],symbolSize:46,label:{{fontSize:10,formatter:function(p){{return p.value.toFixed(0)+'%';}}}},itemStyle:{{color:BLUE}}}}}},
    {{name:'等权组合',type:'line',data:PORT,symbol:'none',lineStyle:{{width:3,color:'#c0392b'}},itemStyle:{{color:'#c0392b'}},z:7,
      markPoint:{{data:[{{type:'max',name:'峰值'}}],symbolSize:46,label:{{fontSize:10,formatter:function(p){{return p.value.toFixed(0)+'%';}}}},itemStyle:{{color:'#c0392b'}}}},
      markLine:{{silent:true,symbol:'none',lineStyle:{{color:'#c0c4cc',type:'dashed'}},data:[{{yAxis:0}}],label:{{show:false}}}}}},
    {{name:'中芯国际',type:'line',data:ZX,symbol:'none',lineStyle:{{width:1.4,color:'#8a919c',type:'dotted'}},itemStyle:{{color:'#8a919c'}},z:3}},
    {{name:'寒武纪',type:'line',data:HW,symbol:'none',lineStyle:{{width:1.4,color:'#e08a1e',type:'dotted'}},itemStyle:{{color:'#e08a1e'}},z:3}},
    {{name:'海光信息',type:'line',data:HG,symbol:'none',lineStyle:{{width:1.4,color:'#7b5cd6',type:'dotted'}},itemStyle:{{color:'#7b5cd6'}},z:3}}
  ]
}});

mk('c_dd',{{
  tooltip:Object.assign({{}},TIP,{{axisPointer:{{type:'cross',label:{{backgroundColor:'#5a616c'}}}},
    formatter:function(ps){{var s='<b>'+ps[0].axisValue+'</b><br/>';ps.sort(function(a,b){{return b.value-a.value;}});
      ps.forEach(function(p){{s+=p.marker+p.seriesName+': <b style="color:'+DN+'">'+p.value.toFixed(2)+'%</b><br/>';}});return s;}}}}),
  legend:{{data:['等权组合','科创芯片指数','中芯国际','寒武纪','海光信息'],top:4,textStyle:{{color:'#4a505a',fontSize:12}}}},
  grid:{{left:58,right:26,top:44,bottom:64}},
  xAxis:Object.assign({{type:'category',data:DATES,boundaryGap:false,axisLabel:{{color:'#6b7280',fontSize:11,interval:15,formatter:function(v){{return v.slice(2);}}}}}},{{axisLine:AX.axisLine,splitLine:{{show:false}}}}),
  yAxis:Object.assign({{type:'value',name:'距峰值回撤 %',nameTextStyle:{{color:'#8a919c',fontSize:11}},max:0,axisLabel:{{color:'#6b7280',fontSize:11,formatter:'{{value}}%'}}}},{{axisLine:AX.axisLine,splitLine:AX.splitLine}}),
  dataZoom:[{{type:'inside'}},{{type:'slider',height:18,bottom:14,borderColor:'#d5d9e0',fillerColor:'rgba(30,142,78,.10)',handleStyle:{{color:'#1e8e4e'}},textStyle:{{color:'#8a919c',fontSize:10}}}}],
  series:[
    {{name:'等权组合',type:'line',data:DDP,symbol:'none',lineStyle:{{width:2.6,color:'#c0392b'}},itemStyle:{{color:'#c0392b'}},z:7,areaStyle:{{color:'rgba(192,57,43,.10)'}},
      markPoint:{{data:[{{type:'min',name:'最深'}}],symbolSize:48,label:{{fontSize:10,formatter:function(p){{return p.value.toFixed(1)+'%';}}}},itemStyle:{{color:'#c0392b'}}}}}},
    {{name:'科创芯片指数',type:'line',data:DDI,symbol:'none',lineStyle:{{width:2.6,color:BLUE}},itemStyle:{{color:BLUE}},z:6,areaStyle:{{color:'rgba(44,107,208,.08)'}},
      markPoint:{{data:[{{type:'min',name:'最深'}}],symbolSize:48,label:{{fontSize:10,formatter:function(p){{return p.value.toFixed(1)+'%';}}}},itemStyle:{{color:BLUE}}}}}},
    {{name:'中芯国际',type:'line',data:DDZ,symbol:'none',lineStyle:{{width:1.2,color:'#8a919c',type:'dotted'}},itemStyle:{{color:'#8a919c'}},z:3}},
    {{name:'寒武纪',type:'line',data:DDH,symbol:'none',lineStyle:{{width:1.2,color:'#e08a1e',type:'dotted'}},itemStyle:{{color:'#e08a1e'}},z:3}},
    {{name:'海光信息',type:'line',data:DDG,symbol:'none',lineStyle:{{width:1.2,color:'#7b5cd6',type:'dotted'}},itemStyle:{{color:'#7b5cd6'}},z:3}}
  ]
}});

var rkNames=RK_NAME.slice().reverse(),rkYtd=RK_YTD.slice().reverse(),rkPort=RK_PORT.slice().reverse(),rkW=RK_W.slice().reverse();
mk('c_rank',{{
  tooltip:Object.assign({{}},TIP,{{trigger:'item',formatter:function(p){{var i=p.dataIndex;
    return '<b>'+rkNames[i]+'</b><br/>2025 YTD: <b style="color:'+(rkYtd[i]>=0?UP:DN)+'">'+(rkYtd[i]>=0?'+':'')+rkYtd[i].toFixed(2)+'%</b><br/>指数权重: '+rkW[i].toFixed(3)+'%'+(rkPort[i]?'<br/><b style="color:#c0392b">★ 本组合持仓</b>':'');}}}}),
  grid:{{left:96,right:84,top:34,bottom:36}},
  xAxis:Object.assign({{type:'value',name:'2025 YTD %',nameTextStyle:{{color:'#8a919c',fontSize:11}},axisLabel:{{color:'#6b7280',fontSize:11,formatter:'{{value}}%'}}}},{{axisLine:AX.axisLine,splitLine:AX.splitLine}}),
  yAxis:Object.assign({{type:'category',data:rkNames,axisLabel:{{color:'#4a505a',fontSize:11.5}}}},{{axisLine:AX.axisLine,splitLine:{{show:false}}}}),
  series:[{{type:'bar',data:rkYtd.map(function(v,i){{return {{value:v,itemStyle:{{color:rkPort[i]?'#c0392b':(v>=0?'#e8a0a0':'#9fd3b4'),borderRadius:[0,3,3,0]}}}};}}),barWidth:'62%',
    label:{{show:true,position:'right',fontSize:10.5,color:'#4a505a',formatter:function(p){{return (p.value>=0?'+':'')+p.value.toFixed(1)+'%';}}}},
    markLine:{{silent:true,symbol:'none',lineStyle:{{color:BLUE,type:'dashed',width:1.6}},data:[{{xAxis:61.33,label:{{formatter:'指数 +61.33%',color:BLUE,fontSize:11,position:'insideEndTop'}}}}]}}}}]
}});

mk('c_cross',{{
  tooltip:Object.assign({{}},TIP,{{trigger:'item',formatter:function(p){{var v=p.value;
    return '<b>'+v[2]+'</b><br/>2025 YTD: <b style="color:'+(v[0]>=0?UP:DN)+'">'+(v[0]>=0?'+':'')+v[0].toFixed(2)+'%</b><br/>2026 YTD: <b style="color:'+(v[1]>=0?UP:DN)+'">'+(v[1]>=0?'+':'')+v[1].toFixed(2)+'%</b>';}}}}),
  grid:{{left:64,right:40,top:40,bottom:56}},
  xAxis:Object.assign({{type:'value',name:'2025 YTD %',nameLocation:'middle',nameGap:30,nameTextStyle:{{color:'#8a919c',fontSize:12}},axisLabel:{{color:'#6b7280',fontSize:11,formatter:'{{value}}%'}}}},{{axisLine:AX.axisLine,splitLine:AX.splitLine}}),
  yAxis:Object.assign({{type:'value',name:'2026 YTD %',nameTextStyle:{{color:'#8a919c',fontSize:12}},axisLabel:{{color:'#6b7280',fontSize:11,formatter:'{{value}}%'}}}},{{axisLine:AX.axisLine,splitLine:AX.splitLine}}),
  series:[{{type:'scatter',data:CROSS,symbolSize:function(v){{return v[3]?16:11;}},
    itemStyle:{{color:function(p){{return p.value[3]?'#c0392b':'#9fb3d1';}},opacity:0.85,borderColor:p=>p.value[3]?'#8b1a10':'#6b88b0',borderWidth:1}},
    label:{{show:true,position:'top',fontSize:9.5,color:'#5a616c',formatter:function(p){{return p.value[2];}}}},
    markLine:{{silent:true,symbol:'none',lineStyle:{{color:'#c0c4cc',type:'dashed'}},data:[{{yAxis:0}},{{xAxis:0}}],label:{{show:false}}}}}}]
}});
</script>
</body>
</html>
"""
P.append(js)

open(os.path.join(BASE, "out", "frag25_c.html"), "w", encoding="utf-8").write("".join(P))
print("frag25_c.html written, bytes:", len("".join(P).encode("utf-8")))
