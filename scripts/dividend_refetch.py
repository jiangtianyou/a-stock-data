# -*- coding: utf-8 -*-
"""
红利指数数据补抓(限流恢复后自动重试)
- 请求间隔 2s, 遇 403/空数据 -> 退避 60s 再整体重试, 最多 25 分钟
- 全部成功才覆盖 out/dividend_raw.json (避免半成品覆盖)
"""
import sys, os, json, time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")
START, END = "20041231", "20260914"

PAIRS = [
    ("中证红利", "000922", "H00922", "红利"),
    ("上证红利", "000015", "H00015", "红利"),
    ("300红利", "000821", "H00821", "红利"),
    ("国企红利", "000824", "H00824", "红利"),
    ("央企红利", "000825", "H00825", "红利"),
    ("红利低波", "H30269", "H20269", "红利低波"),
    ("红利低波100", "930955", "H20955", "红利低波"),
    ("沪深300", "000300", "H00300", "基准"),
    ("中证500", "000905", "H00905", "基准"),
    ("中证1000", "000852", "H00852", "基准"),
    ("上证指数", "000001", None, "基准"),
]

UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]


def fetch(code, ua, retry=3):
    url = ("https://www.csindex.com.cn/csindex-home/perf/index-perf"
           f"?indexCode={code}&startDate={START}&endDate={END}")
    for i in range(retry):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": ua, "Referer": "https://www.csindex.com.cn/",
                "Accept": "application/json, text/plain, */*"})
            r = json.loads(urllib.request.urlopen(req, timeout=45).read().decode("utf-8", "ignore"))
            d = r.get("data") or []
            if d:
                return [{"d": x["tradeDate"], "o": x.get("open"), "c": x["close"]}
                        for x in d if x.get("close")]
            return []          # 200 但空 -> 限流
        except Exception:
            time.sleep(3 * (i + 1))
    return []


def attempt():
    items, ok = [], True
    for k, (name, pcode, tcode, group) in enumerate(PAIRS):
        for kind, code in (("px", pcode), ("tr", tcode)):
            if code is None:
                continue
            rows = fetch(code, UAS[k % len(UAS)])
            if not rows:
                print(f"  限流中: {name} {'价格' if kind=='px' else '全收益'} ({code})")
                ok = False
            else:
                items.append({"name": name, "group": group, "kind": kind, "code": code, "rows": rows})
                print(f"  OK {name:<10}{'价格' if kind=='px' else '全收益':<4}{len(rows):>5}条")
            time.sleep(2)
    return items, ok


def main():
    t0 = time.time()
    for rnd in range(1, 26):
        print(f"\n[第 {rnd} 轮] {time.strftime('%H:%M:%S')}  已耗时 {(time.time()-t0)/60:.1f} 分钟")
        items, ok = attempt()
        if ok and len(items) >= 20:
            res = {"fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "source": "csindex.com.cn / csindex-home/perf/index-perf",
                   "count": len(items), "items": items}
            with open(os.path.join(OUT, "dividend_raw.json"), "w", encoding="utf-8") as f:
                json.dump(res, f, ensure_ascii=False)
            print(f"\n完成 -> out/dividend_raw.json ({len(items)} 序列)")
            return
        print(f"  本轮失败, 等待 60s 重试")
        time.sleep(60)
    print("25 轮仍未成功, 放弃")


if __name__ == "__main__":
    main()
