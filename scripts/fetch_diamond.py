# -*- coding: utf-8 -*-
import requests, json, sys

sys.stdout.reconfigure(encoding="utf-8")

s = requests.Session()
s.trust_env = False
s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"})

# 1. 获取 BK1023 培育钻石板块成份股列表
url = "https://push2.eastmoney.com/api/qt/clist/get"
params = {
    "pn": 1,
    "pz": 100,
    "po": 1,
    "np": 1,
    "fltt": 2,
    "invt": 2,
    "fid": "f20", # 按总市值排序
    "fs": "b:BK1023",
    "fields": "f12,f14,f2,f3,f4,f5,f6,f7,f8,f9,f10,f20,f21"
}

r = s.get(url, params=params, timeout=10)
data = r.json().get("data", {})
stocks = data.get("diff", [])

print(f"板块成份股总数: {len(stocks)}")
for idx, item in enumerate(stocks):
    code = item.get("f12")
    name = item.get("f14")
    price = item.get("f2")
    chg = item.get("f3")
    total_val = item.get("f20", 0) / 1e8 if item.get("f20") else 0 # 亿元
    print(f"{idx+1}. {code} {name}: 现价={price}, 今日涨跌幅={chg}%, 总市值={total_val:.2f}亿")

# 2. 获取前几名以及核心标的的近一个月K线数据
# 核心标的比如：中兵红箭、力量钻石、黄河旋风、四方达、惠丰钻石
