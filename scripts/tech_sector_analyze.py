# -*- coding: utf-8 -*-
"""
科技板块 8月以来表现分析
口径: 2026-07-31(7月最后交易日)收盘 -> 2026-09-15 收盘
输出: out/tech_sector_stats.json
"""
import sys, os, json
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")

# 板块名称 -> 大类
CATS = [
    ("半导体/芯片链", ["半导体", "芯片", "集成电路", "晶圆", "封装", "光刻", "存储", "HBM",
                    "IC", "电子化学品", "MLCC", "被动元件", "元件", "第四代半导体", "第三代半导体",
                    "电子纸"]),
    ("AI算力链", ["CPO", "光通信", "光模块", "液冷", "算力", "数据中心", "IDC", "服务器",
                "人工智能", "AIGC", "多模态", "AI应用", "AI语料", "AI智能体", "智谱", "大模型",
                "AI手机", "AIPC", "AI眼镜", "AI制药"]),
    ("通信网络", ["通信", "5G", "6G", "F5G", "卫星", "光纤"]),
    ("消费电子/元器件", ["消费电子", "智能穿戴", "面板", "OLED", "LED", "光学", "CCM",
                   "AIPC", "柔性屏", "屏下摄像", "电子纸", "3D摄像头", "电子后视镜",
                   "智能家居", "PCB", "覆铜板", "品牌消费电子", "汽车电子"]),
    ("计算机/软件", ["软件", "信创", "网络安全", "云计算", "大数据", "数字经济", "国资云",
                 "区块链", "数字货币", "边缘计算", "鸿蒙", "量子科技", "时空大数据", "计算机"]),
    ("传媒/游戏", ["游戏", "传媒", "影视", "电子竞技", "虚拟现实", "元宇宙", "短剧"]),
    ("机器人/智造", ["机器人", "减速器", "机器视觉", "工业母机", "3D打印", "传感器",
                 "智能驾驶", "激光雷达", "低空经济", "无人机", "人形"]),
    ("军工电子", ["军工电子", "军工"]),
    ("电子(综合)", ["电子"]),
]


def cat_of(name):
    for c, kws in CATS:
        for k in kws:
            if k in name:
                return c
    return "其他科技"


def main():
    p = os.path.join(OUT, "tech_sector_perf.json")
    data = json.load(open(p, encoding="utf-8"))
    items = [x for x in data["items"] if x.get("type") != "基准"]
    bench = [x for x in data["items"] if x.get("type") == "基准"]

    for it in items:
        it["cat"] = cat_of(it["name"])

    # 去重：同名保留
    items.sort(key=lambda x: -x["ret"])

    print("=" * 78)
    print(f"科创板块区间表现  {data['range']}  共{len(items)}个")
    print("=" * 78)
    print(f"{'排名':<4}{'板块':<18}{'涨幅':>9}{'反弹(自低点)':>13}{'最大回撤':>10}  {'低点日期':<12}")
    for i, x in enumerate(items[:40], 1):
        print(f"{i:<4}{x['name']:<18}{x['ret']*100:>+8.2f}%{x['rebound_from_low']*100:>+12.2f}%"
              f"{x['dd']*100:>+9.2f}%  {x['low_date']}")

    print("\n--- 基准 ---")
    for b in bench:
        print(f"  {b['name']:<10}{b['ret']*100:>+8.2f}%   低点{b['low_date']} → 反弹{b['rebound_from_low']*100:+.2f}%")

    # 分类均值
    print("\n--- 各细分方向均值 ---")
    g = defaultdict(list)
    for x in items:
        g[x["cat"]].append(x["ret"])
    for c, v in sorted(g.items(), key=lambda kv: -sum(kv[1]) / len(kv[1])):
        print(f"  {c:<16} n={len(v):<4} 均值 {sum(v)/len(v)*100:>+7.2f}%  最高 {max(v)*100:>+7.2f}%")

    json.dump({"range": data["range"], "fetched_at": data["fetched_at"],
               "items": items, "bench": bench,
               "cat_avg": {c: {"n": len(v), "avg": sum(v) / len(v), "max": max(v)} for c, v in g.items()}},
              open(os.path.join(OUT, "tech_sector_stats.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\n已写出 out/tech_sector_stats.json")


if __name__ == "__main__":
    main()
