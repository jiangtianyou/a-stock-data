# -*- coding: utf-8 -*-
"""
拉取东财全部行业/概念板块列表，筛选"大科技"相关板块
输出: out/tech_sector_list.json
"""
import sys, os, json, time, random
import requests

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")

S = requests.Session()
S.trust_env = False
S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
                  "Referer": "https://quote.eastmoney.com/"})

HOSTS = ["push2.eastmoney.com", "push2delay.eastmoney.com"]


def clist(fs, pz=100):
    out = []
    for pn in range(1, 9):
        params = {"pn": pn, "pz": pz, "po": 1, "np": 1, "fltt": 2, "invt": 2,
                  "fid": "f3", "fs": fs, "fields": "f12,f14,f3,f104,f105,f106"}
        got = False
        for h in HOSTS:
            try:
                r = S.get(f"https://{h}/api/qt/clist/get", params=params, timeout=15)
                if r.status_code == 200:
                    j = r.json()
                    diff = (j.get("data") or {}).get("diff") or []
                    if diff:
                        out.extend(diff)
                        got = True
                        break
            except Exception:
                continue
        if not got:
            break
        time.sleep(0.35 + random.uniform(0, 0.15))
        if len(diff) < pz:
            break
    return out


def main():
    boards = {}
    # t:2 行业板块, t:3 概念板块
    for fs, tag in [("m:90+t:2", "行业"), ("m:90+t:3", "概念")]:
        rows = clist(fs)
        print(f"{tag}板块: {len(rows)} 个")
        for d in rows:
            code, name = d.get("f12"), d.get("f14")
            if code and name:
                boards[code] = {"code": code, "name": name, "type": tag,
                                "chg_today": d.get("f3")}
        time.sleep(0.4)

    # ---- 大科技关键词筛选 ----
    KW = ["半导体", "芯片", "集成电路", "晶圆", "封装", "光刻", "存储", "HBM", "IC",
          "PCB", "覆铜板", "光模块", "光通信", "CPO", "算力", "数据中心", "液冷",
          "服务器", "IDC", "人工智能", "大模型", "AIGC", "AI", "机器人", "减速器",
          "伺服", "消费电子", "面板", "LED", "折叠屏", "光学", "摄像", "MLCC",
          "被动元件", "元件", "软件", "信创", "操作系统", "数据库", "云计算", "大数据",
          "国资云", "网络安全", "数字经济", "数字货币", "区块链", "游戏", "传媒",
          "影视", "虚拟现实", "MR", "元宇宙", "智能驾驶", "汽车电子", "激光雷达",
          "卫星", "北斗", "6G", "5G", "通信", "电子", "光电", "工业母机", "3D打印",
          "传感器", "机器视觉", "无人机", "低空", "第三代半导体", "GPU", "CPU",
          "智能穿戴", "智能音箱", "智能家居", "量子", "脑机", "虚拟电厂", "边缘计算",
          "PaaS", "SaaS", "操作系统", "鸿蒙"]
    EX = ["昨日", "涨停", "连板", "打板", "破净", "转债", "次新", "融资融券", "同花顺",
          "机构重仓", "基金重仓", "预盈预增", "预亏预减", "高送转", "股权转让", "举牌"]

    tech = []
    for b in boards.values():
        n = b["name"]
        if any(e in n for e in EX):
            continue
        if any(k in n for k in KW):
            tech.append(b)

    out = {"fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
           "total_boards": len(boards), "tech_count": len(tech),
           "all": list(boards.values()), "tech": tech}
    with open(os.path.join(OUT, "tech_sector_list.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"总板块 {len(boards)}，筛出科技类 {len(tech)}")
    for t in tech:
        print(f"  {t['code']} {t['name']}")


if __name__ == "__main__":
    main()
