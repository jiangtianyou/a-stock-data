
const RED='#d0342c', GREEN='#1e8e4e', BLUE='#2c6bd0', ORANGE='#e08b1a', GRAY='#8a919c';
const M=["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"];
const grid={left:55,right:55,top:50,bottom:40};
const tt={trigger:'axis',axisPointer:{type:'shadow'}};

// 图1 价格 vs 全收益 + 分红
echarts.init(document.getElementById('c1')).setOption({
  tooltip:tt,
  legend:{data:['价格指数月均','全收益指数月均','分红贡献(右轴)'],top:6},
  grid:{left:55,right:60,top:52,bottom:40},
  xAxis:{type:'category',data:M},
  yAxis:[{type:'value',name:'收益 %',axisLabel:{formatter:'{value}%'}},
         {type:'value',name:'分红 %',min:0,max:1.6,interval:0.4,axisLabel:{formatter:'{value}%'}}],
  series:[
    {name:'价格指数月均',type:'bar',data:[1.12, 3.34, 1.06, 2.92, 0.62, -4.01, 2.29, -1.04, 1.25, -0.48, 2.44, 3.42],itemStyle:{color:RED},barGap:'0%'},
    {name:'全收益指数月均',type:'bar',data:[1.3, 3.36, 1.07, 3.03, 1.06, -2.68, 3.61, -0.87, 1.35, -0.44, 2.46, 3.44],itemStyle:{color:BLUE}},
    {name:'分红贡献(右轴)',type:'line',yAxisIndex:1,data:[0.034, 0.016, 0.01, 0.116, 0.434, 1.329, 1.322, 0.169, 0.099, 0.039, 0.02, 0.018],smooth:true,symbolSize:6,
      itemStyle:{color:ORANGE},lineStyle:{width:2.5},
      label:{show:true,fontSize:11,color:ORANGE,formatter:function(p){return p.value>=0.3?p.value.toFixed(2):'';}}}
  ]
});

// 图2 分红月份分布
echarts.init(document.getElementById('c2')).setOption({
  tooltip:tt, grid:grid,
  xAxis:{type:'category',data:M},
  yAxis:{type:'value',name:'分红贡献 %',axisLabel:{formatter:'{value}%'}},
  series:[{type:'bar',data:[0.034, 0.016, 0.01, 0.116, 0.434, 1.329, 1.322, 0.169, 0.099, 0.039, 0.02, 0.018],itemStyle:{color:function(p){return p.value>0.5?'#d0342c':(p.value>0.15?'#e08b1a':'#c9cfd8');}},
    label:{show:true,position:'top',fontSize:11,formatter:function(p){return p.value>=0.3?p.value.toFixed(2):''}}}]
});

// 图3 6月瀑布
echarts.init(document.getElementById('c3')).setOption({
  tooltip:{trigger:'axis',axisPointer:{type:'shadow'},formatter:function(ps){
    const i=ps[0].dataIndex;
    const txt=['市场共性(沪深300全收益6月)','红利相对弱势','除息机械扣减','= 6月价格口径收益'];
    const v=[-0.41,-2.27,-1.33,-4.01];
    return txt[i]+'<br/><b>'+v[i].toFixed(2)+'%</b>';}},
  grid:{left:60,right:40,top:40,bottom:56},
  xAxis:{type:'category',data:['市场共性\n(沪深300)','红利相对弱势','除息机械扣减','= 6月价格口径'],
         axisLabel:{fontSize:12,lineHeight:16}},
  yAxis:{type:'value',name:'贡献 %',min:-4.6,max:0.2,axisLabel:{formatter:'{value}%'}},
  series:[
    {name:'占位',type:'bar',stack:'wf',silent:true,itemStyle:{color:'transparent'},data:[0,-0.41,-2.68,0]},
    {name:'贡献',type:'bar',stack:'wf',barWidth:48,data:[
      {value:-0.41,itemStyle:{color:RED},label:{show:true,position:'bottom',fontSize:12,formatter:'-0.41%'}},
      {value:-2.27,itemStyle:{color:RED},label:{show:true,position:'bottom',fontSize:12,formatter:'-2.27%'}},
      {value:-1.33,itemStyle:{color:ORANGE},label:{show:true,position:'bottom',fontSize:12,formatter:'-1.33%'}},
      {value:-4.01,itemStyle:{color:'#7a8593'},label:{show:true,position:'bottom',fontSize:12,fontWeight:'bold',formatter:'-4.01%'}}]}
  ]
});

// 图4 逐年6月
echarts.init(document.getElementById('c4')).setOption({
  tooltip:tt,
  legend:{data:['红利族全收益6月','沪深300全收益6月','红利超额(右轴)'],top:6},
  grid:{left:55,right:60,top:52,bottom:50},
  xAxis:{type:'category',data:["2005", "2006", "2007", "2008", "2009", "2010", "2011", "2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026"],axisLabel:{rotate:45}},
  yAxis:[{type:'value',name:'收益 %',axisLabel:{formatter:'{value}%'}},
         {type:'value',name:'超额 %',axisLabel:{formatter:'{value}%'}}],
  series:[
    {name:'红利族全收益6月',type:'bar',data:[2.91, 2.58, -11.66, -25.11, 8.09, -8.35, 0.65, -5.0, -14.29, 1.59, -0.7, 0.38, 4.59, -6.72, 0.86, 2.88, -0.61, 1.76, -0.88, -2.95, 1.64, -9.02],itemStyle:{color:BLUE}},
    {name:'沪深300全收益6月',type:'line',data:[2.66, 2.9, -3.87, -22.34, 15.3, -7.32, 2.23, -5.55, -14.65, 1.31, -7.24, 0.15, 5.59, -6.99, 6.06, 8.48, -1.48, 10.43, 2.13, -2.52, 3.31, 2.32],smooth:true,
      itemStyle:{color:ORANGE},symbolSize:6},
    {name:'红利超额(右轴)',type:'scatter',yAxisIndex:1,data:[0.25, -0.33, -7.78, -2.76, -7.21, -1.04, -1.58, 0.55, 0.36, 0.28, 6.54, 0.23, -1.0, 0.27, -5.19, -5.6, 0.86, -8.67, -3.0, -0.43, -1.68, -11.34],
      itemStyle:{color:GRAY} ,symbolSize:9}
  ]
});
