# -*- coding: utf-8 -*-
"""生成《半导体材料四股 8月以来走势复盘对比》HTML 研报（浅底深字 / 结论先行 / ECharts / 红涨绿跌）"""
import json, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open("out/semimat_stats.json", encoding="utf-8") as f:
    S = json.load(f)
with open("out/semimat_daily.json", encoding="utf-8") as f:
    D = json.load(f)

stats, norm, corr = S["stats"], S["norm"], S["corr"]
NAMES = ["彤程新材", "有研新材", "雅克科技", "江丰电子"]
CUT = "2026-09-15"

def pct(x, digits=2):
    return f"{x*100:+.{digits}f}%"

# ---- 分段涨跌幅（按周旬切分，与周度表一致）----
SEGS = [("08-01~08-07 主升", "2026-07-31", "2026-08-07"),
        ("08-08~08-28 高位回落", "2026-08-07", "2026-08-28"),
        ("08-29~09-07 探底", "2026-08-28", "2026-09-07"),
        ("09-08~09-15 分化修复", "2026-09-07", "2026-09-15")]
seg_ret = {}
for nm in NAMES + ["科创50"]:
    rows = [r for r in D[nm]["rows"] if r["date"] <= CUT]
    dm = {r["date"]: r["close"] for r in rows}
    seg_ret[nm] = [dm[e]/dm[s]-1 for _, s, e in SEGS]

# ---- 变量替换值 ----
v = {}
for nm in NAMES:
    st = stats[nm]
    v[f"{nm}_total"] = pct(st["total_pct"])
    v[f"{nm}_aug"] = pct(st["aug_pct"])
    v[f"{nm}_sep"] = pct(st["sep_pct"])
    v[f"{nm}_mdd"] = f"{st['mdd']*100:.1f}%"
    v[f"{nm}_mdd_span"] = f"{st['mdd_from'][5:]} → {st['mdd_to'][5:]}"
    v[f"{nm}_hi"] = f"{st['hi']:.2f}"
    v[f"{nm}_hi_at"] = st["hi_at"][5:]
    v[f"{nm}_hi_off"] = pct(st["hi_off"])
    v[f"{nm}_lo_at"] = st["lo_at"][5:]
    v[f"{nm}_last"] = f"{st['last_close']:.2f}"
    v[f"{nm}_volr"] = f"{st['vol_sep']/st['vol_aug']:.2f}"
    v[f"{nm}_excess"] = f"{st['excess_vs_kc50']:+.1f}pp"
    v[f"{nm}_upratio"] = f"{st['up_days']}/{st['n_days']}"

st50 = stats["科创50"]
v["kc50_total"] = pct(st50["total_pct"])
v["kc50_mdd"] = f"{st50['mdd']*100:.1f}%"

# 单日异动（前文已验算，写死关键日期数据来自 D）
def top_moves(nm, k=3, sign=1):
    rows = [r for r in D[nm]["rows"] if r["date"] <= CUT]
    rets = sorted([(rows[i]["close"]/rows[i-1]["close"]-1, rows[i]["date"]) for i in range(1, len(rows))])
    return rets if sign > 0 else rets[:k], rets[-k:]

picks = {
    "tc_0909": "+10.0%（涨停）", "tc_0805": "+8.0%", "yj_0819": "-10.0%",
    "jf_0819": "-9.2%", "jf_0907": "+8.7%", "yj_0827": "+6.4%",
}
v["tc_reb"] = "+35.3%"   # 低点以来反弹（前文验算）
v["yj_reb"] = "+10.1%"
v["jf_reb"] = "+32.3%"
v["yj_0908"] = "-2.7%"

# ---- 归一化曲线数据 ----
dates_all = norm["科创50"]["dates"]
chart1_series = []
for nm in NAMES + ["科创50"]:
    n = norm[nm]
    m = dict(zip(n["dates"], n["vals"]))
    chart1_series.append({"name": nm, "data": [m.get(d) for d in dates_all]})

chart2 = {"segs": [s[0] for s in SEGS],
          "names": NAMES + ["科创50"],
          "data": [[round(seg_ret[nm][i]*100, 2) for nm in chart2_names] for i, nm2 in enumerate([])] if False else
                  {nm: [round(x*100, 2) for x in seg_ret[nm]] for nm in NAMES + ["科创50"]}}

chart3 = {nm: [round(stats[nm]["total_pct"]*100, 2), round(stats[nm]["hi_off"]*100, 2)] for nm in NAMES}
chart4 = {nm: round(stats[nm]["vol_sep"]/stats[nm]["vol_aug"], 3) for nm in NAMES}
corr_tbl = {}
for k, val in corr.items():
    a, b_ = k.split("|")
    corr_tbl.setdefault(a, {})[b_] = val
    corr_tbl.setdefault(b_, {})[a] = val

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>半导体材料四股 8月以来走势复盘对比</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
:root{--bg:#f7f8fa;--card:#ffffff;--ink:#1f2329;--sub:#646a73;--line:#e5e6eb;--red:#d64541;--green:#0f9d58;--accent:#2456d6;}
*{margin:0;padding:0;box-sizing:border-box;}
body{background:var(--bg);color:var(--ink);font-family:"Microsoft YaHei","PingFang SC",sans-serif;font-size:14px;line-height:1.7;padding:28px 16px;}
.wrap{max-width:1080px;margin:0 auto;}
h1{font-size:22px;margin-bottom:4px;}
.meta{color:var(--sub);font-size:12px;margin-bottom:18px;}
h2{font-size:17px;margin:26px 0 12px;padding-left:10px;border-left:4px solid var(--accent);}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin-bottom:14px;}
.concl{display:flex;flex-direction:column;gap:10px;}
.concl .item{display:flex;gap:10px;align-items:flex-start;}
.concl .no{flex:0 0 22px;height:22px;border-radius:50%;background:var(--accent);color:#fff;font-size:12px;display:flex;align-items:center;justify-content:center;margin-top:3px;}
table{width:100%;border-collapse:collapse;font-size:13px;background:var(--card);}
th,td{border:1px solid var(--line);padding:7px 9px;text-align:center;white-space:nowrap;}
th{background:#f0f2f5;font-weight:600;}
td.l{text-align:left;}
.up{color:var(--red);font-weight:600;}
.dn{color:var(--green);font-weight:600;}
.chart{width:100%;height:420px;}
.note{color:var(--sub);font-size:12px;margin-top:8px;}
.risk{background:#fff8e6;border:1px solid #f0d98c;border-radius:10px;padding:14px 18px;font-size:13px;}
.pos{display:inline-block;background:#fdeceb;color:var(--red);border-radius:4px;padding:0 6px;font-weight:600;}
.neg{display:inline-block;background:#e8f6ef;color:var(--green);border-radius:4px;padding:0 6px;font-weight:600;}
</style>
</head>
<body>
<div class="wrap">
<h1>半导体材料四股 8月以来走势复盘对比</h1>
<div class="meta">样本：彤程新材(603650) / 有研新材(600206) / 雅克科技(002409) / 江丰电子(300666)，基准：科创50(000688) ｜ 区间：2026-08-01 ～ 2026-09-15（前复权日线，量能为成交量）｜ 数据源：腾讯财经行情接口 ｜ 生成：2026-09-16</div>

<h2>一、核心结论（先看这个）</h2>
<div class="card concl">
  <div class="item"><div class="no">1</div><div><b>同涨同跌，板块 β 主导。</b>四股日收益两两相关系数 0.71～0.92（雅克↔江丰 0.92 最高），节奏完全同步：8 月第一周集体主升（单周 +23%～+45%），08-17～08-19 集体见顶，09-04 前后集体见底（早于科创50 的 09-14）。个股差异主要体现在<b>幅度</b>而非方向。</div></div>
  <div class="item"><div class="no">2</div><div><b>全部大幅跑赢基准。</b>区间涨幅：有研新材 <span class="pos">__有研新材_total__</span> &gt; 彤程新材 <span class="pos">__彤程新材_total__</span> &gt; 江丰电子 <span class="pos">__江丰电子_total__</span> &gt; 雅克科技 <span class="neg">__雅克科技_total__</span>；同期科创50 <span class="neg">__kc50_total__</span>，四股超额 <b>+4.7pp ～ +37.9pp</b>。</div></div>
  <div class="item"><div class="no">3</div><div><b>涨幅榜 ≠ 当前最强，9 月分化修复才是关键。</b>有研 8 月一周暴涨 +45.4%、三度涨停，但顶部回撤 <b>__有研新材_mdd__</b>，9 月仅 __有研新材_sep__、距高点仍 -20.2%，高位滞涨；<b>彤程是修复段最强</b>：9 月 __彤程新材_sep__（09-09 涨停），距高点仅 __彤程新材_hi_off__、基本收复失地，且 9 月量能保持（量比 __彤程新材_volr__，其余三只 0.55～0.61），反弹质量最好。</div></div>
  <div class="item"><div class="no">4</div><div><b>雅克明显掉队。</b>区间持平（__雅克科技_total__），08-19 单日 -10% 重挫后始终未缓过来：9 月 __雅克科技_sep__、距高点 __雅克科技_hi_off__、低点以来仅反弹 __yj_reb__（其余三只 +32%～+35%），量能萎缩最明显（量比 __雅克科技_volr__）。同一板块、0.92 的高相关，走出完全不同的结果——<b>回撤后的修复能力才是当前的区分点</b>。</div></div>
  <div class="item"><div class="no">5</div><div><b>量价背离信号：</b>四股 9 月成交量较 8 月全面萎缩（量比 0.55～0.92），彤程的修复有量能配合最健康；有研/江丰/雅克的 9 月反弹属于缩量修复，若后续放量跟不上，距高点 12%～20% 的套牢区压力不好消化。</div></div>
</div>

<h2>二、归一化走势对比（2026-07-31 = 100）</h2>
<div class="card"><div id="c1" class="chart"></div>
<div class="note">彤程新材 8 月初急跌 -6.3% 后 V 型拉起；有研新材斜率最陡但 8 月中旬后一路高位震荡回落；雅克科技 8/17 见顶后重心持续下移。</div></div>

<h2>三、分段涨跌幅（四个阶段 × 五标的）</h2>
<div class="card"><div id="c2" class="chart"></div>
<div class="note">阶段划分依据实际节奏：8 月上旬主升 → 8 月中下旬自高点回落 → 8 月末～9 月初探底 → 9 月中旬分化修复。红=涨、绿=跌。</div></div>

<h2>四、关键指标总表</h2>
<div class="card" style="overflow-x:auto;">
<table>
<tr><th>标的</th><th>最新收盘<br>(09-15)</th><th>区间涨幅</th><th>8月</th><th>9月以来</th><th>区间高点(日期)</th><th>现价距高点</th><th>最大回撤<br>(峰值→谷)</th><th>9月量/8月量</th><th>超额<br>vs科创50</th><th>上涨天数</th></tr>
__TABLE_ROWS__
<tr><td>科创50(基准)</td><td>—</td><td class="dn">__kc50_total__</td><td class="up">+2.96%</td><td class="dn">-7.86%</td><td>1790.87(08-18)</td><td class="dn">-13.34%</td><td class="dn">-14.7%</td><td>0.68</td><td>—</td><td>—</td></tr>
</table>
<div class="note">最大回撤按区间内「峰值收盘→其后最低收盘」计算；上涨天数为 8月以来有涨跌的交易日中收涨天数。</div>
</div>

<h2>五、区间涨幅 vs 现价距高点</h2>
<div class="card"><div id="c3" class="chart" style="height:340px;"></div>
<div class="note">「区间涨幅」看这轮谁涨得多，「现价距高点」看谁离前高最近（彤程 -2.65% 最接近修复完成；有研 -20.2% 仍深陷回撤）。</div></div>

<h2>六、量能对比（9 月日均量 / 8 月日均量）</h2>
<div class="card"><div id="c4" class="chart" style="height:340px;"></div>
<div class="note">量比 &lt;1 = 9 月成交萎缩。彤程 0.92 接近持平（修复有量），有研 0.61 / 江丰 0.57 / 雅克 0.55 明显缩量。</div></div>

<h2>六、两两日收益相关性</h2>
<div class="card" style="overflow-x:auto;">
<table>
<tr><th></th><th>彤程新材</th><th>有研新材</th><th>雅克科技</th><th>江丰电子</th></tr>
__CORR_ROWS__
</table>
<div class="note">基于 2026-08-01～09-15 日收益率（n≈32）。板块整体 β 主导，雅克↔江丰 0.92 为最高——两者同为设备/材料链直接标的，联动最强。</div>
</div>

<h2>八、逐股一句话复盘</h2>
<div class="card" style="font-size:13.5px;">
<p><b>彤程新材（光刻胶）：</b>8 月初急跌后 V 型反转，第一周 +27.1% 冲至 70.57（08-18 见顶），随后三周震荡回落，09-04 见底后 9 月修复段 +12.7%（09-09 涨停 +10%），当前 69.31 距前高仅 2.65%，<b>唯一一个量价配合修复、逼近前高的标的</b>。</p><br>
<p><b>有研新材（靶材/稀土材料）：</b>本轮弹性之王——8 月第一周 +45.4%、三个交易日涨停（08-05/07/17），但过快拉升透支空间，08-19 见顶 58.83 后最大回撤 -23.1%，9 月几乎横盘（-9.2% 后基本走平），<b>高位滞涨，等待新催化消化套牢盘</b>。</p><br>
<p><b>雅克科技（前驱体/电子特气）：</b>唯一区间收平的标的。第一周 +23.1% 不算弱，但 08-19 单日 -10% 是四股中最重的单日打击，此后重心持续下移，9 月继续 -6.5%、缩量最明显，<b>明显的掉队者，反弹节奏与量能均未恢复</b>。</p><br>
<p><b>江丰电子（靶材）：</b>第一周 +36.5% 弹性仅次于有研，08-19 单日 -9.2% 回撤，09-04 见底后 09-07 大涨 +8.7% 领先修复，低点以来 +32.3%，当前距高点 -12.1%，<b>修复进度次于彤程、明显好于有研/雅克</b>。</p>
</div>

<div class="risk">
<b>口径与风险提示：</b>① 样本仅 4 只个股 + 1 个基准，不构成板块全貌；② 价格为前复权口径，量能为成交量（手）而非成交额；③ 数据截至 2026-09-15 收盘（个股），科创50 截至 09-16；④ 本报告为历史行情复盘，所有"强/弱"判断均基于已发生的价格与量能，不预测未来，不构成投资建议；⑤ 8 月涨幅含极端单日（涨停/跌停），历史弹性不代表后续可持续。
</div>
</div>

<script>
var RED="#d64541", GREEN="#0f9d58", INK="#1f2329", SUB="#646a73", LINE="#e5e6eb";
var FONT={fontFamily:'"Microsoft YaHei","PingFang SC",sans-serif'};
var dates=__DATES__;
var norm=__NORM__;
var segData=__SEG__;
var volr=__VOLR__;

function baseAxis(){return{axisLine:{lineStyle:{color:LINE}},axisLabel:{color:SUB},splitLine:{lineStyle:{color:LINE}}};}

// 图1 归一化
var colors={"彤程新材":"#2456d6","有研新材":"#d64541","雅克科技":"#e69b00","江丰电子":"#7b3ff2","科创50":"#9aa0a6"};
var c1=echarts.init(document.getElementById("c1"));
c1.setOption({color:Object.values(colors),textStyle:FONT,
 tooltip:{trigger:"axis",valueFormatter:v=>v&&v.toFixed? v.toFixed(1):v},
 legend:{top:3,left:"center",textStyle:{color:INK}},
 grid:{top:52,left:56,right:24,bottom:56},
 xAxis:Object.assign({type:"category",data:dates,boundaryGap:false,axisLabel:{color:SUB,formatter:v=>v.slice(5)}},baseAxis()),
 yAxis:Object.assign({type:"value",scale:true,axisLabel:{color:SUB,formatter:v=>v}},baseAxis()),
 dataZoom:[{type:"inside"},{type:"slider",bottom:8,height:18}],
 series:norm.map(function(s){return{name:s.name,type:"line",data:s.data,symbol:"none",lineStyle:{width:s.name==="科创50"?1.5:2.5,type:s.name==="科创50"?"dashed":"solid"}};})
});

// 图2 分段
var segNames=Object.keys(segData);
var segSeries=segNames.map(function(nm,i){return{name:nm,type:"bar",data:segData[nm],
 itemStyle:{color:function(p){return p.value>=0?RED:GREEN;}}};});
var c2=echarts.init(document.getElementById("c2"));
c2.setOption({textStyle:FONT,
 tooltip:{trigger:"axis",valueFormatter:v=>v.toFixed(1)+"%"},
 legend:{top:3,left:"center",textStyle:{color:INK}},
 grid:{top:52,left:56,right:24,bottom:40},
 xAxis:Object.assign({type:"category",data:__SEG_LABELS__,axisLabel:{color:SUB,interval:0}},baseAxis()),
 yAxis:Object.assign({type:"value",axisLabel:{color:SUB,formatter:"{value}%"}},baseAxis()),
 series:segSeries
});

// 图3 距高点 & 区间涨幅（横向）
var c3=echarts.init(document.getElementById("c3"));
var stockNames=["彤程新材","有研新材","雅克科技","江丰电子"];
c3.setOption({textStyle:FONT,
 tooltip:{},
 legend:{top:3,left:"center",textStyle:{color:INK}},
 grid:{top:52,left:90,right:40,bottom:30},
 xAxis:Object.assign({type:"value",axisLabel:{color:SUB,formatter:"{value}%"}},baseAxis()),
 yAxis:{type:"category",data:stockNames.slice().reverse(),axisLabel:{color:INK}},
 series:[
  {name:"区间涨幅",type:"bar",data:stockNames.slice().reverse().map(function(nm){return{value:segTotal[nm],itemStyle:{color:segTotal[nm]>=0?RED:GREEN}};})},
  {name:"现价距高点",type:"bar",data:stockNames.slice().reverse().map(function(nm){return{value:hiOff[nm],itemStyle:{color:hiOff[nm]>=0?RED:GREEN,opacity:0.55}};})}
 ]
});

// 图4 量比
var c4=echarts.init(document.getElementById("c4"));
c4.setOption({textStyle:FONT,
 tooltip:{valueFormatter:v=>v.toFixed(2)},
 grid:{top:30,left:56,right:24,bottom:34},
 xAxis:Object.assign({type:"category",data:stockNames,axisLabel:{color:INK}},baseAxis()),
 yAxis:Object.assign({type:"value",min:0,max:1.1,axisLabel:{color:SUB}},baseAxis()),
 series:[{type:"bar",barWidth:52,data:stockNames.map(function(nm){return{value:volr[nm],itemStyle:{color:volr[nm]>=0.85?RED:"#f0a05a"}};}),
  label:{show:true,position:"top",color:INK,formatter:p=>p.value.toFixed(2)},
  markLine:{symbol:"none",lineStyle:{color:SUB,type:"dashed"},label:{formatter:"1.0 = 持平",color:SUB},data:[{yAxis:1}]}}]
});

window.addEventListener("resize",function(){c1.resize();c2.resize();c3.resize();c4.resize();});
</script>
</body>
</html>
"""

# ---- 表格行 ----
def table_rows():
    trs = []
    for nm in NAMES:
        st = stats[nm]
        def cls(x):
            return "up" if x >= 0 else "dn"
        trs.append(
            f"<tr><td><b>{nm}</b></td><td>{v[nm+'_last']}</td>"
            f"<td class='{cls(st['total_pct'])}'>{v[nm+'_total']}</td>"
            f"<td class='{cls(st['aug_pct'])}'>{v[nm+'_aug']}</td>"
            f"<td class='{cls(st['sep_pct'])}'>{v[nm+'_sep']}</td>"
            f"<td>{v[nm+'_hi']}({v[nm+'_hi_at']})</td>"
            f"<td class='{cls(st['hi_off'])}'>{v[nm+'_hi_off']}</td>"
            f"<td class='dn'>{v[nm+'_mdd']}<br><span style='font-size:11px;color:#646a73'>{v[nm+'_mdd_span']}</span></td>"
            f"<td>{v[nm+'_volr']}</td>"
            f"<td class='up'>{v[nm+'_excess']}</td>"
            f"<td>{v[nm+'_upratio']}</td></tr>")
    return "\n".join(trs)

def corr_rows():
    trs = []
    for a in NAMES:
        tds = f"<tr><td><b>{a}</b></td>"
        for b_ in NAMES:
            if a == b_:
                tds += "<td>—</td>"
            else:
                val = corr_tbl[a][b_]
                shade = "#fdeceb" if val >= 0.8 else ("#fdf1ee" if val >= 0.7 else "#fff")
                tds += f"<td style='background:{shade}'>{val:.2f}</td>"
        trs.append(tds + "</tr>")
    return "\n".join(trs)

seg_labels = [s[0] for s in SEGS]
repl = {
    "__DATES__": json.dumps(dates_all, ensure_ascii=False),
    "__NORM__": json.dumps(chart1_series, ensure_ascii=False),
    "__SEG__": json.dumps({nm: [round(x*100, 2) for x in seg_ret[nm]] for nm in NAMES + ["科创50"]}, ensure_ascii=False),
    "__SEG_LABELS__": json.dumps(seg_labels, ensure_ascii=False),
    "__VOLR__": json.dumps(chart4, ensure_ascii=False),
    "__TABLE_ROWS__": table_rows(),
    "__CORR_ROWS__": corr_rows(),
    "__SEG_TOTAL__": json.dumps({nm: round(stats[nm]["total_pct"]*100, 2) for nm in NAMES}, ensure_ascii=False),
    "__HIOFF__": json.dumps({nm: round(stats[nm]["hi_off"]*100, 2) for nm in NAMES}, ensure_ascii=False),
}
html = html.replace("var segTotal;", "var segTotal=__SEG_TOTAL__;").replace("var hiOff;", "var hiOff=__HIOFF__;")
for k, val in repl.items():
    html = html.replace(k, val)
for k, val in v.items():
    html = html.replace("__" + k + "__", val)

out = "reports/半导体材料四股8月以来复盘对比-20260916.html"
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print("saved", out)
