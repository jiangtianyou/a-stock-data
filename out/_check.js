
var C_RED='#d93025', C_GRN='#12805c', C_BLU='#2563eb';
var AX={axisLine:{lineStyle:{color:'#d1d5db'}},axisLabel:{color:'#6b7280'},splitLine:{lineStyle:{color:'#f1f3f5'}}};
function mk(id,opt){var e=echarts.init(document.getElementById(id));e.setOption(opt);window.addEventListener('resize',function(){e.resize()});}

mk('c_senti',{
  tooltip:{trigger:'axis'},legend:{top:3,left:'center',textStyle:{color:'#6b7280'}},
  grid:{left:56,right:66,top:52,bottom:32},
  xAxis:Object.assign({type:'category',data:["9/14", "9/15", "9/16"]},AX),
  yAxis:[Object.assign({type:'value',name:'家数'},AX),
         Object.assign({type:'value',name:'封板率%',min:0,max:100},AX)],
  series:[
    {name:'涨停家数',type:'bar',data:[55, 32, 89],itemStyle:{color:C_RED},barWidth:26,
     label:{show:true,position:'top',color:C_RED,fontWeight:600}},
    {name:'炸板家数',type:'bar',data:[30, 24, 11],itemStyle:{color:'#f0a04b'},barWidth:26,
     label:{show:true,position:'top',color:'#b26a1e'}},
    {name:'跌停家数',type:'bar',data:[16, 27, 4],itemStyle:{color:C_GRN},barWidth:26,
     label:{show:true,position:'top',color:C_GRN}},
    {name:'封板率',type:'line',yAxisIndex:1,smooth:true,symbolSize:8,data:[64.7, 57.1, 89.0],
     itemStyle:{color:C_BLU},lineStyle:{width:3},label:{show:true,position:'bottom',color:C_BLU,formatter:'{c}%'}}
  ]
});

mk('c_idx',{
  tooltip:{trigger:'axis',valueFormatter:function(v){return v+'%'}},
  grid:{left:76,right:52,top:16,bottom:24},
  xAxis:Object.assign({type:'value',axisLabel:{formatter:'{value}%'}},AX),
  yAxis:Object.assign({type:'category',data:["上证50", "北证50", "沪深300", "中证500", "国证2000", "中证1000", "科创50", "创业板指", "深证成指", "上证指数"]},AX),
  series:[{type:'bar',data:[0.67, 1.15, 0.68, 1.61, 2.04, 2.01, 4.14, 1.96, 1.26, 0.71],barWidth:14,
    itemStyle:{color:function(p){return p.value>=0?C_RED:C_GRN}},
    label:{show:true,position:'right',color:'#6b7280',fontSize:11,formatter:'{c}%'}}]
});

mk('c_lad',{
  tooltip:{trigger:'axis'},legend:{top:3,left:'center',textStyle:{color:'#6b7280'}},
  grid:{left:46,right:20,top:52,bottom:28},
  xAxis:Object.assign({type:'category',data:["1板", "2板", "3板", "4板", "5板", "6板"]},AX),
  yAxis:Object.assign({type:'value'},AX),
  series:[
    {name:'9/15',type:'bar',data:[25, 3, 2, 1, 1, 0],itemStyle:{color:'#cbd5e1'},barWidth:18},
    {name:'9/16',type:'bar',data:[77, 9, 1, 1, 0, 1],itemStyle:{color:C_RED},barWidth:18,
     label:{show:true,position:'top',color:'#9ca3af',fontSize:11}}
  ]
});

mk('c_theme',{
  tooltip:{trigger:'axis'},
  grid:{left:124,right:70,top:16,bottom:24},
  xAxis:Object.assign({type:'value'},AX),
  yAxis:Object.assign({type:'category',data:["电力 / 电网", "风电 / 海洋能源", "机器人 / 具身智能", "固态电池 / 锂电", "液冷 / 散热", "PCB / 覆铜板", "消费 / 家居食品", "国资 / 区域主题", "半导体 / 存储", "AI算力 / 光通信"]},AX),
  series:[{type:'bar',data:[2, 3, 4, 4, 4, 9, 10, 10, 16, 27],itemStyle:{color:C_BLU},barWidth:15,
    label:{show:true,position:'right',color:'#374151',fontWeight:600,formatter:'{c} 家'}}]
});

mk('c_hy',{
  tooltip:{trigger:'axis'},legend:{top:3,left:'center',textStyle:{color:'#6b7280'}},
  grid:{left:100,right:56,top:52,bottom:24},
  xAxis:Object.assign({type:'value'},AX),
  yAxis:Object.assign({type:'category',data:["照明设备", "电网设备", "风电设备", "自动化设", "消费电子", "专用设备", "通用设备", "非白酒", "汽车零部", "其他电子", "家居用品", "电力", "包装印刷", "化学制品", "元件", "塑料", "半导体", "通信设备"]},AX),
  series:[
    {name:'9/15',type:'bar',data:[0, 1, 4, 2, 0, 0, 1, 1, 1, 0, 2, 3, 1, 0, 2, 2, 2, 1],itemStyle:{color:'#cbd5e1'},barWidth:11},
    {name:'9/16',type:'bar',data:[2, 2, 1, 2, 3, 3, 3, 3, 3, 4, 3, 3, 4, 5, 4, 4, 5, 6],itemStyle:{color:C_RED},barWidth:11}
  ]
});

mk('c_perf',{
  tooltip:{trigger:'axis',valueFormatter:function(v){return v+'%'}},
  grid:{left:100,right:56,top:16,bottom:28},
  xAxis:Object.assign({type:'value',axisLabel:{formatter:'{value}%'}},AX),
  yAxis:Object.assign({type:'category',data:["中新赛克", "启明信息", "新中港", "汉王科技", "宏盛股份", "欧克科技", "大金重工", "天龙股份", "中闽能源", "天顺风能", "国邦医药", "大为股份", "诺德股份", "吉鑫科技", "双星新材", "华正新材", "金龙羽", "上海洗霸", "浙江众成", "和顺石油", "华瓷股份", "德尔未来", "通鼎互联", "澳弘电子", "闽东电力", "英联股份", "北自科技", "中晶科技", "会稽山", "西陇科学", "锡华科技", "博汇科技"],axisLabel:{color:'#6b7280',fontSize:10,interval:0}},AX),
  series:[{type:'bar',data:[-9.98, -5.12, -3.98, -3.31, -1.27, -1.02, -0.71, -0.36, -0.16, 0.13, 0.17, 0.31, 0.49, 0.77, 0.91, 0.96, 1.15, 1.78, 2.41, 3.72, 9.98, 9.99, 9.99, 10.0, 10.0, 10.01, 10.01, 10.01, 10.02, 10.02, 10.02, 20.01],barWidth:9,
    itemStyle:{color:function(p){return p.value>=0?C_RED:C_GRN}},
    label:{show:true,position:'right',fontSize:10,color:'#9ca3af',
      formatter:function(p){return p.value.toFixed(1)}}}]
});

mk('c_ts',{
  tooltip:{trigger:'axis'},legend:{top:3,left:'center',textStyle:{color:'#6b7280'}},
  grid:{left:50,right:20,top:52,bottom:28},
  xAxis:Object.assign({type:'category',data:["竞价/秒板", "开盘半小时", "上午盘中", "午后盘中", "尾盘"]},AX),
  yAxis:Object.assign({type:'value'},AX),
  series:[
    {name:'9/15',type:'bar',data:[1, 17, 11, 2, 1],itemStyle:{color:'#cbd5e1'},barWidth:24},
    {name:'9/16',type:'bar',data:[2, 28, 34, 24, 1],itemStyle:{color:C_RED},barWidth:24}
  ]
});
