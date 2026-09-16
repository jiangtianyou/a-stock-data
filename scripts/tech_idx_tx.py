# -*- coding: utf-8 -*-
"""
腾讯通道: 交易所挂牌科技指数 8月以来表现
口径: 2026-07-31 收盘 -> 2026-09-15 收盘
输出: out/tech_idx_tx.json
"""
import sys, os, json, time, random
import requests

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")

S = requests.Session()
S.trust_env = False
S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
                  "Referer": "https://gu.qq.com/"})

POOL = [
    ("sh000998", "中证TMT", "综合"),
    ("sh000993", "全指信息", "综合"),
    ("sh000994", "全指通信", "综合"),
    ("sh000935", "中证信息", "综合"),
    ("sh000936", "800通信", "综合"),
    ("sz399811", "CSSW电子", "综合"),
    ("sz399608", "科技100", "综合"),
    ("sz399970", "移动互联", "综合"),
    ("sz399996", "智能家居", "综合"),
    ("sz399803", "工业4.0", "综合"),
    ("sz399971", "中证传媒", "传媒"),
    ("sz399967", "中证军工", "军工"),
    ("sh000688", "科创50", "基准"),
    ("sz399006", "创业板指", "基准"),
    ("sh000300", "沪深300", "基准"),
    ("sh000001", "上证指数", "基准"),
]

_last = [0.0]


def get(url, params, min_interval=0.5, retries=4):
    for i in range(retries):
        w = min_interval - (time.time() - _last[0])
        if w > 0:
            time.sleep(w + random.uniform(0.05, 0.2))
        try:
            _last[0] = time.time()
            r = S.get(url, params=params, timeout=20)
            if r.status_code == 200 and r.text.strip():
                return r.json()
        except Exception:
            pass
        time.sleep(0.8 * (2 ** i))
    return None


def fetch_day(sym):
    r = get("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get",
            {"param": f"{sym},day,2026-07-25,2026-09-15,60,qfq"})
    if not r:
        return None
    d = (r.get("data") or {}).get(sym) or {}
    kl = d.get("qfqday") or d.get("day") or []
    rows = []
    for k in kl:
        try:
            rows.append({"d": k[0], "o": float(k[1]), "c": float(k[2]),
                         "h": float(k[3]), "l": float(k[4])})
        except Exception:
            continue
    return rows or None


def calc(rows):
    if not rows or len(rows) < 3:
        return None
    base_row = None
    for r in rows:
        if r["d"] <= "2026-07-31":
            base_row = r
    if not base_row:
        return None
    base = base_row["c"]
    last = rows[-1]["c"]
    seq = [r for r in rows if r["d"] >= base_row["d"]]
    lo = min(seq, key=lambda x: x["c"])
    return {"base_date": base_row["d"], "base": round(base, 2),
            "last_date": rows[-1]["d"], "last": round(last, 2),
            "ret": last / base - 1,
            "low_date": lo["d"], "low": round(lo["c"], 2),
            "rebound_from_low": last / lo["c"] - 1,
            "days": len(seq)}


def main():
    res, fail = [], []
    for i, (sym, name, grp) in enumerate(POOL, 1):
        rows = fetch_day(sym)
        st = calc(rows)
        if st:
            st.update({"code": sym, "name": name, "group": grp})
            res.append(st)
            print(f"[{i:>2}/{len(POOL)}] {name:<10} {st['ret']*100:>+7.2f}%  低点{st['low_date']}→反弹{st['rebound_from_low']*100:>+6.2f}%")
        else:
            fail.append(name)
            print(f"[{i:>2}/{len(POOL)}] {name:<10} 失败")
    json.dump({"fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
               "source": "tencent fqkline (day, qfq)",
               "range": "2026-07-31 -> 2026-09-15",
               "items": res, "fail": fail},
              open(os.path.join(OUT, "tech_idx_tx.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\n完成 {len(res)}/{len(POOL)} 失败:{fail}")


if __name__ == "__main__":
    main()
