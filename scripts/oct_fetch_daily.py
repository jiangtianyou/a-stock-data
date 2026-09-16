# -*- coding: utf-8 -*-
"""
9-10月行情专题 - 日线抓取
通道: 腾讯 web.ifzq.gtimg.cn  (东财 push2his 在本机被限流)
参数: param={sym},day,{start},{end},1700,qfq  分段拉全历史
字段: [日期, 开, 收, 高, 低, 量]  <-- 注意是 开-收-高-低
输出: out/oct_raw.json
"""
import sys, os, json, time, random
import requests

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")

S = requests.Session()
S.trust_env = False
S.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://gu.qq.com/",
})

POOL = [
    ("sh000001", "上证指数", "宽基"),
    ("sz399001", "深证成指", "宽基"),
    ("sh000300", "沪深300", "宽基"),
    ("sh000905", "中证500", "宽基"),
    ("sh000852", "中证1000", "宽基"),
    ("sz399006", "创业板指", "宽基"),
    ("sh000985", "中证全指", "宽基"),
    ("sh000016", "上证50", "宽基"),
    ("sh000922", "中证红利", "风格"),
]

SEGS = [(1990, 1996), (1997, 2002), (2003, 2008), (2009, 2014), (2015, 2020), (2021, 2026)]

_last = [0.0]


def get(params, retries=4):
    for i in range(retries):
        w = 0.5 - (time.time() - _last[0])
        if w > 0:
            time.sleep(w + random.uniform(0.05, 0.2))
        try:
            _last[0] = time.time()
            r = S.get("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get",
                      params=params, timeout=20)
            if r.status_code == 200 and r.text.strip():
                return r.json()
        except Exception as e:
            if i == retries - 1:
                print("    网络失败:", type(e).__name__)
        time.sleep(0.8 * (2 ** i))
    return None


def fetch_daily(sym):
    acc = {}
    for y0, y1 in SEGS:
        r = get({"param": f"{sym},day,{y0}-01-01,{y1}-12-31,1700,qfq"})
        if not r:
            continue
        d = (r.get("data") or {}).get(sym) or {}
        kl = d.get("qfqday") or d.get("day") or []
        for k in kl:
            try:
                acc[k[0]] = {"d": k[0], "o": float(k[1]), "c": float(k[2]),
                             "h": float(k[3]), "l": float(k[4]), "v": float(k[5])}
            except Exception:
                continue
        time.sleep(0.15)
    rows = [acc[k] for k in sorted(acc)]
    return rows or None


def main():
    os.makedirs(OUT, exist_ok=True)
    res, fail = [], []
    for i, (sym, name, grp) in enumerate(POOL, 1):
        rows = fetch_daily(sym)
        if rows and len(rows) >= 500:
            res.append({"secid": sym, "name": name, "group": grp, "rows": rows})
            print(f"  [{i:>2}/{len(POOL)}] {name:<8} {len(rows):>5}根  {rows[0]['d']} -> {rows[-1]['d']}")
        else:
            fail.append(name)
            print(f"  [{i:>2}/{len(POOL)}] {name:<8} 数据不足")

    out = {"fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
           "source": "tencent web.ifzq.gtimg.cn (day, qfq)",
           "count": len(res), "items": res}
    with open(os.path.join(OUT, "oct_raw.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print(f"\n完成: 成功 {len(res)} / 失败 {len(fail)} {fail if fail else ''}")


if __name__ == "__main__":
    main()
