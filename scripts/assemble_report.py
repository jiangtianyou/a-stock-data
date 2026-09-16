import json, io, os

BASE = r"D:\Desktop\Playground\a-stock-data"
d = json.load(open(os.path.join(BASE, "out", "final.json"), encoding="utf-8"))
a = json.load(open(os.path.join(BASE, "out", "attribution.json"), encoding="utf-8"))

dates = d["full_dates"]
port = d["port_bh"]
idx = d["idx"]
exn = d["exn"]
ddp = d["dd_port"]
ddi = d["dd_idx"]
zx = d["688981"]["norm"]
hw = d["688256"]["norm"]
hg = d["688041"]["norm"]
ddz = d["688981"]["dd"]
ddh = d["688256"]["dd"]
ddg = d["688041"]["dd"]

rank = a["rank"]
rk_name = [x["name"] + ("★" if x["in_portfolio"] else "") for x in rank]
rk_ytd = [x["ytd"] for x in rank]
rk_w = [x["weight"] for x in rank]
rk_port = [x["in_portfolio"] for x in rank]

J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))

js = []
js.append("""
<script>
function sw(gid, cid, tid, k){
  var g=document.getElementById(gid);
  var bs=g.getElementsByTagName('button');
  for(var i=0;i<bs.length;i++){ bs[i].className = (i===k)?'on':''; }
  var panes=[cid, tid, tid+'2'];
  for(var i=0;i<panes.length;i++){
    var el=document.getElementById(panes[i]);
    if(!el) continue;
    el.style.display = (i===k)?'':'none';
  }
  if(k===0 && window._charts && window._charts[cid]){ window._charts[cid].resize(); }
}
window._charts = window._charts || {};
var AX={axisLine:{lineStyle:{color:'#d5d9e0'}},axisLabel:{color:'#6b7280',fontSize:11},splitLine:{lineStyle:{color:'#eef0f3'}}};
var TIP={trigger:'axis',backgroundColor:'rgba(255,255,255,.97)',borderColor:'#e0e3e8',borderWidth:1,textStyle:{color:'#2b2f36',fontSize:12},extraCssText:'box-shadow:0 4px 16px rgba(0,0,0,.10);border-radius:8px;'};
function mk(id,opt){var el=document.getElementById(id);if(!el)return;var c=echarts.init(el);c.setOption(opt);window._charts[id]=c;}
window.addEventListener('resize',function(){for(var k in window._charts){window._charts[k].resize();}});
""")

js.append("var DATES=" + J(dates) + ";\n")
js.append("var PORT=" + J(port) + ", IDX=" + J(idx) + ", EXN=" + J(exn) + ";\n")
js.append("var ZX=" + J(zx) + ", HW=" + J(hw) + ", HG=" + J(hg) + ";\n")
js.append("var DDP=" + J(ddp) + ", DDI=" + J(ddi) + ", DDZ=" + J(ddz) + ", DDH=" + J(ddh) + ", DDG=" + J(ddg) + ";\n")
js.append("var RK_NAME=" + J(rk_name) + ", RK_YTD=" + J(rk_ytd) + ", RK_W=" + J(rk_w) + ", RK_PORT=" + J(rk_port) + ";\n")

js.append("""
var UP='#d0342c', DN='#1e8e4e', BLUE='#2c6bd0';

/* ---- 图1: YTD 归一化走势 ---- */
mk('c_walk',{
  tooltip:Object.assign({},TIP,{axisPointer:{type:'cross',label:{backgroundColor:'#5a616c'}},
    formatter:function(ps){
      var s='<b>'+ps[0].axisValue+'</b><br/>';
      ps.sort(function(a,b){return b.value-a.value;});
      ps.forEach(function(p){
        var c=p.value>=0?UP:DN;
        s+=p.marker+p.seriesName+': <b style="color:'+c+'">'+(p.value>=0?'+':'')+p.value.toFixed(2)+'%</b><br/>';
      });
      return s;
    }}),
  legend:{data:['等权组合','科创芯片指数','中芯国际','寒武纪','海光信息'],top:4,textStyle:{color:'#4a505a',fontSize:12}},
  grid:{left:58,right:26,top:44,bottom:64},
  xAxis:Object.assign({type:'category',data:DATES,boundaryGap:false,axisLabel:{color:'#6b7280',fontSize:11,interval:13,formatter:function(v){return v.slice(5);}}},{axisLine:AX.axisLine,splitLine:{show:false}}),
  yAxis:Object.assign({type:'value',name:'YTD 涨幅 %',nameTextStyle:{color:'#8a919c',fontSize:11},axisLabel:{color:'#6b7280',fontSize:11,formatter:'{value}%'}},{axisLine:AX.axisLine,splitLine:AX.splitLine}),
  dataZoom:[{type:'inside'},{type:'slider',height:18,bottom:14,borderColor:'#d5d9e0',fillerColor:'rgba(192,57,43,.10)',handleStyle:{color:'#c0392b'},textStyle:{color:'#8a919c',fontSize:10}}],
  series:[
    {name:'科创芯片指数',type:'line',data:IDX,symbol:'none',lineStyle:{width:3,color:BLUE},itemStyle:{color:BLUE},z:6,
      areaStyle:{color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(44,107,208,.16)'},{offset:1,color:'rgba(44,107,208,0)'}])},
      markPoint:{data:[{type:'max',name:'峰值'}],symbolSize:44,label:{fontSize:10,formatter:function(p){return p.value.toFixed(0)+'%';}},itemStyle:{color:BLUE}}},
    {name:'等权组合',type:'line',data:PORT,symbol:'none',lineStyle:{width:3,color:'#c0392b'},itemStyle:{color:'#c0392b'},z:7,
      markPoint:{data:[{type:'max',name:'峰值'}],symbolSize:44,label:{fontSize:10,formatter:function(p){return p.value.toFixed(0)+'%';}},itemStyle:{color:'#c0392b'}},
      markLine:{silent:true,symbol:'none',lineStyle:{color:'#c0c4cc',type:'dashed'},data:[{yAxis:0}],label:{show:false}}},
    {name:'中芯国际',type:'line',data:ZX,symbol:'none',lineStyle:{width:1.4,color:'#8a919c',type:'dotted'},itemStyle:{color:'#8a919c'},z:3},
    {name:'寒武纪',type:'line',data:HW,symbol:'none',lineStyle:{width:1.4,color:'#e08a1e',type:'dotted'},itemStyle:{color:'#e08a1e'},z:3},
    {name:'海光信息',type:'line',data:HG,symbol:'none',lineStyle:{width:1.4,color:'#7b5cd6',type:'dotted'},itemStyle:{color:'#7b5cd6'},z:3}
  ]
});

/* ---- 图2: 回撤 ---- */
mk('c_dd',{
  tooltip:Object.assign({},TIP,{axisPointer:{type:'cross',label:{backgroundColor:'#5a616c'}},
    formatter:function(ps){
      var s='<b>'+ps[0].axisValue+'</b><br/>';
      ps.sort(function(a,b){return b.value-a.value;});
      ps.forEach(function(p){ s+=p.marker+p.seriesName+': <b style="color:'+DN+'">'+p.value.toFixed(2)+'%</b><br/>'; });
      return s;
    }}),
  legend:{data:['等权组合','科创芯片指数','中芯国际','寒武纪','海光信息'],top:4,textStyle:{color:'#4a505a',fontSize:12}},
  grid:{left:58,right:26,top:44,bottom:64},
  xAxis:Object.assign({type:'category',data:DATES,boundaryGap:false,axisLabel:{color:'#6b7280',fontSize:11,interval:13,formatter:function(v){return v.slice(5);}}},{axisLine:AX.axisLine,splitLine:{show:false}}),
  yAxis:Object.assign({type:'value',name:'距YTD峰值回撤 %',nameTextStyle:{color:'#8a919c',fontSize:11},max:0,axisLabel:{color:'#6b7280',fontSize:11,formatter:'{value}%'}},{axisLine:AX.axisLine,splitLine:AX.splitLine}),
  dataZoom:[{type:'inside'},{type:'slider',height:18,bottom:14,borderColor:'#d5d9e0',fillerColor:'rgba(30,142,78,.10)',handleStyle:{color:'#1e8e4e'},textStyle:{color:'#8a919c',fontSize:10}}],
  series:[
    {name:'等权组合',type:'line',data:DDP,symbol:'none',lineStyle:{width:2.6,color:'#c0392b'},itemStyle:{color:'#c0392b'},z:7,
      areaStyle:{color:'rgba(192,57,43,.10)'},
      markPoint:{data:[{type:'min',name:'最深'}],symbolSize:46,label:{fontSize:10,formatter:function(p){return p.value.toFixed(1)+'%';}},itemStyle:{color:'#c0392b'}}},
    {name:'科创芯片指数',type:'line',data:DDI,symbol:'none',lineStyle:{width:2.6,color:BLUE},itemStyle:{color:BLUE},z:6,
      areaStyle:{color:'rgba(44,107,208,.08)'},
      markPoint:{data:[{type:'min',name:'最深'}],symbolSize:46,label:{fontSize:10,formatter:function(p){return p.value.toFixed(1)+'%';}},itemStyle:{color:BLUE}}},
    {name:'中芯国际',type:'line',data:DDZ,symbol:'none',lineStyle:{width:1.2,color:'#8a919c',type:'dotted'},itemStyle:{color:'#8a919c'},z:3},
    {name:'寒武纪',type:'line',data:DDH,symbol:'none',lineStyle:{width:1.2,color:'#e08a1e',type:'dotted'},itemStyle:{color:'#e08a1e'},z:3},
    {name:'海光信息',type:'line',data:DDG,symbol:'none',lineStyle:{width:1.2,color:'#7b5cd6',type:'dotted'},itemStyle:{color:'#7b5cd6'},z:3}
  ]
});

/* ---- 图3: 前20大成分股 YTD 排行 ---- */
var rkNames=RK_NAME.slice().reverse(), rkYtd=RK_YTD.slice().reverse(), rkPort=RK_PORT.slice().reverse(), rkW=RK_W.slice().reverse();
mk('c_rank',{
  tooltip:Object.assign({},TIP,{trigger:'item',
    formatter:function(p){
      var i=p.dataIndex;
      return '<b>'+rkNames[i]+'</b><br/>YTD: <b style="color:'+(rkYtd[i]>=0?UP:DN)+'">'+(rkYtd[i]>=0?'+':'')+rkYtd[i].toFixed(2)+'%</b><br/>指数权重: '+rkW[i].toFixed(3)+'%'+(rkPort[i]?'<br/><b style="color:#c0392b">★ 本组合持仓</b>':'');
    }}),
  grid:{left:96,right:78,top:34,bottom:36},
  xAxis:Object.assign({type:'value',name:'YTD %',nameTextStyle:{color:'#8a919c',fontSize:11},axisLabel:{color:'#6b7280',fontSize:11,formatter:'{value}%'}},{axisLine:AX.axisLine,splitLine:AX.splitLine}),
  yAxis:Object.assign({type:'category',data:rkNames,axisLabel:{color:'#4a505a',fontSize:11.5,formatter:function(v){return v;}}},{axisLine:AX.axisLine,splitLine:{show:false}}),
  series:[{
    type:'bar',data:rkYtd.map(function(v,i){return {value:v,itemStyle:{color:rkPort[i]?'#c0392b':(v>=0?'#e8a0a0':'#9fd3b4'),borderRadius:[0,3,3,0]}};}),
    barWidth:'62%',
    label:{show:true,position:'right',fontSize:10.5,color:'#4a505a',formatter:function(p){return (p.value>=0?'+':'')+p.value.toFixed(1)+'%';}},
    markLine:{silent:true,symbol:'none',lineStyle:{color:BLUE,type:'dashed',width:1.6},
      data:[{xAxis:37.84,label:{formatter:'指数 +37.84%',color:BLUE,fontSize:11,position:'insideEndTop'}}]}
  }]
});

/* ---- 图4: 累计超额收益（几何 + 算术双口径） ---- */
var EXA=PORT.map(function(v,i){return +(v-IDX[i]).toFixed(2);});
mk('c_ex',{
  tooltip:Object.assign({},TIP,{axisPointer:{type:'cross',label:{backgroundColor:'#5a616c'}},
    formatter:function(ps){
      var s='<b>'+ps[0].axisValue+'</b><br/>';
      ps.forEach(function(p){ s+=p.marker+p.seriesName+': <b style="color:'+(p.value>=0?UP:DN)+'">'+(p.value>=0?'+':'')+p.value.toFixed(2)+'%</b><br/>'; });
      return s;
    }}),
  legend:{data:['算术超额(组合-指数)','几何超额((1+组合)/(1+指数)-1)'],top:4,textStyle:{color:'#4a505a',fontSize:11.5}},
  grid:{left:58,right:26,top:44,bottom:64},
  xAxis:Object.assign({type:'category',data:DATES,boundaryGap:false,axisLabel:{color:'#6b7280',fontSize:11,interval:13,formatter:function(v){return v.slice(5);}}},{axisLine:AX.axisLine,splitLine:{show:false}}),
  yAxis:Object.assign({type:'value',name:'超额 %',nameTextStyle:{color:'#8a919c',fontSize:11},axisLabel:{color:'#6b7280',fontSize:11,formatter:'{value}%'}},{axisLine:AX.axisLine,splitLine:AX.splitLine}),
  dataZoom:[{type:'inside'},{type:'slider',height:18,bottom:14,borderColor:'#d5d9e0',fillerColor:'rgba(30,142,78,.10)',handleStyle:{color:'#1e8e4e'},textStyle:{color:'#8a919c',fontSize:10}}],
  series:[{
    name:'算术超额(组合-指数)',type:'line',data:EXA,symbol:'none',lineStyle:{width:2.4,color:'#e08a1e'},itemStyle:{color:'#e08a1e'},
    areaStyle:{color:'rgba(224,138,30,.10)'},
    markPoint:{data:[{type:'min',name:'最深'}],symbolSize:52,label:{fontSize:10,formatter:function(p){return p.value.toFixed(1);}},itemStyle:{color:'#e08a1e'}}
  },{
    name:'几何超额((1+组合)/(1+指数)-1)',type:'line',data:EXN,symbol:'none',lineStyle:{width:2.6,color:DN},itemStyle:{color:DN},
    markPoint:{data:[{type:'min',name:'最深'}],symbolSize:52,label:{fontSize:10,formatter:function(p){return p.value.toFixed(1)+'%';}},itemStyle:{color:DN}},
    markLine:{silent:true,symbol:'none',lineStyle:{color:'#c0c4cc',type:'dashed'},data:[{yAxis:0,label:{show:false}}]}
  }]
});
</script>
</body>
</html>
""")

out_js = "".join(js)
open(os.path.join(BASE, "scripts", "tpl_js.html"), "w", encoding="utf-8").write(out_js)

parts = []
for f in ["tpl_a.html", "tpl_b.html", "tpl_c.html", "tpl_d.html", "tpl_js.html"]:
    parts.append(open(os.path.join(BASE, "scripts", f), encoding="utf-8").read())
html = "".join(parts)

dest = os.path.join(BASE, "reports", "三剑客YTD复盘-中芯国际寒武纪海光信息vs科创芯片指数-20260914.html")
open(dest, "w", encoding="utf-8").write(html)
print("bytes:", len(html.encode("utf-8")))
print("dest:", dest)
