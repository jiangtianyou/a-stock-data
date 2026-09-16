# -*- coding: utf-8 -*-
"""一次性修补 oct_report.py 中的 ECharts 配置（避免多次并行 Edit 相互覆盖）"""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "oct_report.py")
s = open(P, encoding="utf-8").read()

reps = [
    # 图例统一居中
    ("legend:{data:['平均收益','胜率'],right:8,top:4,",
     "legend:{data:['平均收益','胜率'],top:3,left:'center',"),
    ("legend:{data:['平均收益','中位数','胜率'],right:8,top:4,",
     "legend:{data:['平均收益','中位数','胜率'],top:3,left:'center',"),
    ("legend:{data:['9月均值','10月均值','10月胜率'],right:8,top:4,",
     "legend:{data:['9月均值','10月均值','10月胜率'],top:3,left:'center',"),
    ("legend:{data:['年内最低点','年内最高点'],right:8,top:4,",
     "legend:{data:['年内最低点','年内最高点'],top:3,left:'center',"),
    # 绘图区下移, 与图例垂直分离
    ("grid:{left:52,right:56,top:38,bottom:30},", "grid:{left:52,right:56,top:52,bottom:30},"),
    ("grid:{left:52,right:56,top:38,bottom:46},", "grid:{left:52,right:56,top:52,bottom:46},"),
    ("grid:{left:52,right:56,top:38,bottom:32},", "grid:{left:52,right:56,top:52,bottom:32},"),
    ("grid:{left:46,right:20,top:38,bottom:30},", "grid:{left:46,right:20,top:52,bottom:30},"),
    # 图1: 高亮 9-10 月区间
    ("borderRadius:[3,3,0,0]}})),barWidth:'52%',",
     "borderRadius:[3,3,0,0]}})),barWidth:'52%',\n"
     "        markArea:{silent:true,itemStyle:{color:'rgba(43,92,255,.055)'},"
     "data:[[{xAxis:'9月'},{xAxis:'10月'}]]},"),
    # 图3: 折线置于柱子上层, 避免标签被遮挡
    ("{name:'10月胜率',type:'line',yAxisIndex:1,data:win,smooth:false,symbolSize:7,",
     "{name:'10月胜率',type:'line',yAxisIndex:1,data:win,smooth:false,symbolSize:7,z:10,"),
]

fail = 0
for a, b in reps:
    if a in s:
        s = s.replace(a, b, 1)
        print("  OK  ", a[:56])
    else:
        print("  MISS", a[:56])
        fail += 1

open(P, "w", encoding="utf-8").write(s)
print("\n未匹配数:", fail)
