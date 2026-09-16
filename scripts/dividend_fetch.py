# -*- coding: utf-8 -*-
"""
红利指数季节性研究 - 数据抓取
数据源: 中证指数官网日线接口 (价格指数 + 全收益指数配对)
输出: out/dividend_raw.json

设计要点
--------
红利指数的月度收益统计必须区分两种口径:
  价格指数 (000922)  : 除息日价格直接扣减, 分红不落袋 -> 6-7月分红季被"机械压低"
  全收益指数 (H00922): 分红按除息日再投资, 反映真实持有回报
两者的月度差 = 当月分红收益率(近似), 是识别"伪季节性"的关键证据
"""
import sys, os, json, time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")

START, END = "20041231", "20260914"

# (显示名, 价格代码, 全收益代码, 分组)
PAIRS = [
    ("中证红利",     "000922", "H00922", "红利"),
    ("上证红利",     "000015", "H00015", "红利"),
    ("300红利",      "000821", "H00821", "红利"),
    ("国企红利",     "000824", "H00824", "红利"),
    ("央企红利",     "000825", "H00825", "红利"),
    ("红利低波",     "H30269", "H20269", "红利低波"),
    ("红利低波100",  "930955", "H20955", "红利低波"),
    ("沪深300",      "000300", "H00300", "基准"),
    ("中证500",      "000905", "H00905", "基准"),
    ("中证1000",     "000852", "H00852", "基准"),
    ("上证指数",     "000001", "H00001", "基准"),
    ("上证50",       "000016", "H00016", "基准"),
]

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
      "Referer": "https://www.csindex.com.cn/"}


def fetch(code, start=START, end=END, retry=4):
    url = ("https://www.csindex.com.cn/csindex-home/perf/index-perf"
           f"?indexCode={code}&startDate={start}&endDate={end}")
    for i in range(retry):
        try:
            req = urllib.request.Request(url, headers=UA)
            r = json.loads(urllib.request.urlopen(req, timeout=45).read().decode("utf-8", "ignore"))
            d = r.get("data") or []
            if d:
                return [{"d": x["tradeDate"], "o": x.get("open"), "c": x["close"]}
                        for x in d if x.get("close")]
        except Exception as e:
            if i == retry - 1:
                print(f"      ! {code} 失败 {type(e).__name__}: {e}")
        time.sleep(0.8 * (i + 1))
    return []


def main():
    items = []
    for name, pcode, tcode, group in PAIRS:
        for kind, code in (("px", pcode), ("tr", tcode)):
            rows = fetch(code)
            tag = "价格" if kind == "px" else "全收益"
            if not rows:
                print(f"[{group}] {name} {tag} ({code}) -> 无数据")
                continue
            items.append({"name": name, "group": group, "kind": kind, "code": code,
                          "rows": rows})
            print(f"[{group}] {name} {tag:<3} ({code:<7}) {len(rows):>5}条  "
                  f"{rows[0]['d']} -> {rows[-1]['d']}  {rows[0]['c']:.2f} -> {rows[-1]['c']:.2f}")
        time.sleep(0.4)

    res = {"fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
           "source": "csindex.com.cn / csindex-home/perf/index-perf",
           "count": len(items), "items": items}
    with open(os.path.join(OUT, "dividend_raw.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False)
    print(f"\n-> out/dividend_raw.json  ({len(items)} 个序列)")


if __name__ == "__main__":
    main()
