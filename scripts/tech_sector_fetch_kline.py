# -*- coding: utf-8 -*-
"""
拉取科技板块 K 线，计算 2026-07-31(7月最后交易日) -> 2026-09-15 区间表现
输出: out/tech_sector_perf.json
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

HOSTS = ["7.push2his.eastmoney.com", "push2his.eastmoney.com",
         "82.push2his.eastmoney.com", "1.push2his.eastmoney.com"]
BEG, END = "20260731", "20260915"
_last = [0.0]


def get(url, params, min_interval=0.5, retries=4):
    for i in range(retries):
        w = min_interval - (time.time() - _last[0])
        if w > 0:
            time.sleep(w + random.uniform(0, 0.12))
        try:
            _last[0] = time.time()
            r = S.get(url, params=params, timeout=18)
            if r.status_code == 200 and r.text.strip():
                return r.json()
        except Exception:
            pass
        time.sleep(0.5 * (2 ** i))
    return None


def fetch_kline(secid):
    for h in HOSTS:
        j = get(f"https://{h}/api/qt/stock/kline/get",
                {"secid": secid, "fields1": "f1,f2,f3,f4,f5,f6",
                 "fields2": "f51,f52,f53,f54,f55,f56,f57,f59",
                 "klt": 101, "fqt": 1, "beg": BEG, "end": END, "lmt": 120})
        if not j:
            continue
        d = j.get("data") or {}
        kl = d.get("klines") or []
        if kl:
            rows = []
            for k in kl:
                p = k.split(",")
                try:
                    rows.append({"d": p[0], "o": float(p[1]), "c": float(p[2]),
                                 "h": float(p[3]), "l": float(p[4]),
                                 "amt": float(p[6]) if p[6] else 0.0})
                except Exception:
                    continue
            return d.get("name"), rows
    return None, None


def stats(rows):
    if not rows or len(rows) < 3:
        return None
    base = rows[0]["c"]          # 7/31 收盘
    last = rows[-1]["c"]         # 9/15 收盘
    ret = last / base - 1
    # 区间最低点(收盘口径)及之后反弹
    lo = min(rows, key=lambda x: x["c"])
    hi = max(rows, key=lambda x: x["h"])
    low_idx = rows.index(lo)
    # 最低点之前的高点 -> 最大回撤
    pre = rows[:low_idx + 1]
    peak_before = max(pre, key=lambda x: x["h"]) if pre else rows[0]
    dd = lo["c"] / peak_before["h"] - 1 if peak_before["h"] else 0
    rebound = last / lo["c"] - 1
    return {"base_date": rows[0]["d"], "base": round(base, 2),
            "last_date": rows[-1]["d"], "last": round(last, 2),
            "ret": ret, "low_date": lo["d"], "low": round(lo["c"], 2),
            "hi_date": hi["d"], "hi": round(hi["h"], 2),
            "dd": dd, "rebound_from_low": rebound,
            "days": len(rows),
            "amt_first": rows[0]["amt"], "amt_last": rows[-1]["amt"]}


def main():
    lst = json.load(open(os.path.join(OUT, "tech_sector_list.json"), encoding="utf-8"))
    boards = lst["tech"]
    # 去重（同名不同码保留一个）
    seen, uniq = set(), []
    for b in boards:
        if b["name"] in seen:
            continue
        seen.add(b["name"])
        uniq.append(b)

    bench = [("1.000300", "沪深300", "基准"), ("1.000688", "科创50", "基准"),
             ("0.399006", "创业板指", "基准"), ("1.000001", "上证指数", "基准")]

    res, fail = [], []
    todo = [(b["code"], b["name"], b["type"]) for b in uniq] + bench
    for i, (code, name, typ) in enumerate(todo, 1):
        secid = code if "." in code else f"90.{code}"
        nm, rows = fetch_kline(secid)
        st = stats(rows)
        if st:
            st.update({"code": code, "name": name, "type": typ})
            res.append(st)
            print(f"[{i:>3}/{len(todo)}] {name:<14} {st['ret']*100:>+7.2f}%  低点{st['low_date']}→反弹{st['rebound_from_low']*100:>+6.2f}%")
        else:
            fail.append(name)
            print(f"[{i:>3}/{len(todo)}] {name:<14} 失败")
        if i % 25 == 0:
            json.dump({"items": res, "fail": fail}, open(os.path.join(OUT, "_tmp_tech_perf.json"), "w", encoding="utf-8"), ensure_ascii=False)

    out = {"fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
           "range": f"{BEG} -> {END}", "source": "eastmoney kline",
           "count": len(res), "items": res, "fail": fail}
    json.dump(out, open(os.path.join(OUT, "tech_sector_perf.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n成功 {len(res)} / 失败 {len(fail)}  {fail if fail else ''}")


if __name__ == "__main__":
    main()
