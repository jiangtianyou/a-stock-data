# -*- coding: utf-8 -*-
"""
枚举同花顺概念板块(串行+正则提取), 计算 2026-07-31 -> 2026-09-15 区间表现
输出: out/ths_concept_all.json / out/ths_concept_tech.json
"""
import sys, os, re, json, time
import requests

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")

S = requests.Session()
S.trust_env = False
S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
                  "Referer": "http://q.10jqka.com.cn/"})

RE_NAME = re.compile(r'"name":"([^"]*)"')
RE_DATA = re.compile(r'"data":"([^"]*)"')


def fetch(code):
    for a in range(2):
        try:
            r = S.get(f"http://d.10jqka.com.cn/v6/line/bk_{code}/01/last.js", timeout=10)
            if r.status_code == 200 and len(r.text) > 500:
                mn = RE_NAME.search(r.text)
                md = RE_DATA.search(r.text)
                if mn and md:
                    return mn.group(1), md.group(1)
            return None, None
        except Exception:
            time.sleep(0.3)
    return None, None


def calc(datastr):
    rows = []
    for seg in datastr.split(";"):
        p = seg.split(",")
        if len(p) < 5:
            continue
        try:
            rows.append((p[0], float(p[1]), float(p[2]), float(p[3]), float(p[4])))
        except Exception:
            continue
    base = None
    for x in rows:
        if x[0] <= "20260731":
            base = x
    if not base or len(rows) < 6:
        return None
    seq = [x for x in rows if x[0] >= base[0]]
    last = seq[-1]
    lo = min(seq, key=lambda x: x[4])
    hi = max(seq, key=lambda x: x[2])
    return {"base_date": base[0], "base": base[4], "last_date": last[0], "last": last[4],
            "ret": last[4] / base[4] - 1, "low_date": lo[0], "low": lo[4],
            "rd": last[4] / lo[4] - 1, "hi_date": hi[0], "hi": hi[2],
            "seq": [[x[0], round(x[4], 2)] for x in seq], "n": len(seq)}


def main():
    res = []
    total = 0
    lo_c, hi_c = 885450, 886400
    for c in range(lo_c, hi_c):
        total += 1
        name, ds = fetch(c)
        if name and ds:
            st = calc(ds)
            if st:
                st["code"] = f"bk_{c}"
                st["name"] = name
                res.append(st)
        if total % 50 == 0:
            print(f"  进度 {total}/{hi_c-lo_c}  有效 {len(res)}", flush=True)
            json.dump(res, open(os.path.join(OUT, "_tmp_ths_concept.json"), "w", encoding="utf-8"), ensure_ascii=False)
        time.sleep(0.04)

    res.sort(key=lambda x: -x["ret"])
    json.dump({"range": "2026-07-31 -> 2026-09-15", "source": "ths concept index",
               "count": len(res), "items": res},
              open(os.path.join(OUT, "ths_concept_all.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\n完成: 有效 {len(res)} 个概念板块")

    KW = ["半导体", "芯片", "光", "通信", "电子", "算力", "AI", "人工智能", "存储", "PCB",
          "元件", "面板", "软件", "计算机", "传媒", "游戏", "机器人", "服务器", "数据中心",
          "消费电子", "光学", "MLCC", "封装", "光刻", "HBM", "CPO", "液冷", "铜缆", "GPU",
          "CPU", "传感器", "智能驾驶", "卫星", "军工", "5G", "6G", "虚拟", "元宇宙", "信创",
          "大数据", "云", "数字经济", "鸿蒙", "量子", "脑机", "无人机", "低空", "激光",
          "显示", "折叠", "穿戴", "覆铜", "电子布", "光模块", "先进封装", "第三代半导体"]
    EX = ["ST", "次新", "融资", "转债", "贬值", "升值"]
    tech = [x for x in res if any(k in x["name"] for k in KW) and not any(e in x["name"] for e in EX)]
    print(f"\n=== 同花顺概念板块 科技类 TOP40 (7/31->9/15) ===")
    for i, x in enumerate(tech[:40], 1):
        print(f"{i:>3}. {x['name']:<18}{x['ret']*100:>+8.2f}%  低点{x['low_date']} 反弹{x['rd']*100:>+7.2f}%")
    json.dump(tech, open(os.path.join(OUT, "ths_concept_tech.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
