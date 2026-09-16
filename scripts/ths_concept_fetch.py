# -*- coding: utf-8 -*-
"""
枚举同花顺概念板块(885500-886600)，计算 2026-07-31 -> 2026-09-15 区间表现
输出: out/ths_concept_perf.json
"""
import sys, os, re, json, time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
      "Referer": "http://q.10jqka.com.cn/"}


def fetch(code):
    s = requests.Session()
    s.trust_env = False
    s.headers.update(UA)
    for a in range(3):
        try:
            r = s.get(f"http://d.10jqka.com.cn/v6/line/bk_{code}/01/last.js", timeout=12)
            if r.status_code == 200 and '"name"' in r.text:
                m = re.search(r"\((\{.*\})\)", r.text.strip(), re.S)
                if m:
                    return code, json.loads(m.group(1))
        except Exception:
            pass
        time.sleep(0.4 * (a + 1))
    return code, None


def calc(d):
    rows = []
    for seg in (d.get("data") or "").split(";"):
        p = seg.split(",")
        if len(p) < 5:
            continue
        try:
            rows.append({"d": p[0], "o": float(p[1]), "h": float(p[2]),
                         "l": float(p[3]), "c": float(p[4])})
        except Exception:
            continue
    base_row = None
    for x in rows:
        if x["d"] <= "20260731":
            base_row = x
    if not base_row or len(rows) < 6:
        return None
    seq = [x for x in rows if x["d"] >= base_row["d"]]
    last = seq[-1]
    lo = min(seq, key=lambda x: x["c"])
    hi = max(seq, key=lambda x: x["h"])
    return {"base_date": base_row["d"], "base": base_row["c"],
            "last_date": last["d"], "last": last["c"],
            "ret": last["c"] / base_row["c"] - 1,
            "low_date": lo["d"], "low": lo["c"], "rd": last["c"] / lo["c"] - 1,
            "hi_date": hi["d"], "hi": hi["h"],
            "seq": [[x["d"], round(x["c"], 2)] for x in seq],
            "n": len(seq)}


def main():
    codes = list(range(885450, 886600))
    res, fail = [], 0
    done = 0
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(fetch, c): c for c in codes}
        for f in as_completed(futs):
            done += 1
            code, d = f.result()
            if d and d.get("name"):
                st = calc(d)
                if st:
                    st["code"] = f"bk_{code}"
                    st["name"] = d["name"]
                    res.append(st)
            else:
                fail += 1
            if done % 100 == 0:
                print(f"  进度 {done}/{len(codes)}  有效 {len(res)}  空 {fail}", flush=True)
                json.dump(res, open(os.path.join(OUT, "_tmp_ths_concept.json"), "w", encoding="utf-8"),
                          ensure_ascii=False)

    res.sort(key=lambda x: -x["ret"])
    json.dump({"range": "2026-07-31 -> 2026-09-15", "source": "ths concept index (bk_885xxx)",
               "count": len(res), "items": res},
              open(os.path.join(OUT, "ths_concept_perf.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\n完成: 有效 {len(res)} 个概念板块")

    KW = ["半导体", "芯片", "光", "通信", "电子", "算力", "AI", "人工智能", "存储", "PCB",
          "元件", "面板", "软件", "计算机", "传媒", "游戏", "机器人", "服务器", "数据中心",
          "消费电子", "光学", "MLCC", "封装", "光刻", "HBM", "CPO", "液冷", "铜缆",
          "液冷", "GPU", "CPU", "传感器", "智能驾驶", "卫星", "军工", "5G", "6G", "虚拟",
          "元宇宙", "信创", "国产软件", "大数据", "云", "数字经济", "鸿蒙", "量子", "脑机",
          "无人机", "低空", "激光", "显示", "折叠", "穿戴", "HBM", "先进封装"]
    EX = ["ST", "次新", "融资", "转债"]
    tech = [x for x in res if any(k in x["name"] for k in KW) and not any(e in x["name"] for e in EX)]
    print(f"\n=== 同花顺概念板块 科技类 TOP35 (7/31->9/15) ===")
    for i, x in enumerate(tech[:35], 1):
        print(f"{i:>3}. {x['name']:<16}{x['ret']*100:>+8.2f}%  低点{x['low_date']} 反弹{x['rd']*100:>+7.2f}%")
    json.dump(tech, open(os.path.join(OUT, "ths_concept_tech.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
