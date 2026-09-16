# -*- coding: utf-8 -*-
"""补漏: 对缺失品种多轮重试(两通道交替)"""
import sys, os, json, time, random, re
import requests

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")
S = requests.Session()
S.trust_env = False
S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
                  "Referer": "https://gu.qq.com/"})

with open(os.path.join(OUT, "seasonality_raw.json"), encoding="utf-8") as f:
    raw = json.load(f)
have = {it["secid"]: it for it in raw["items"]}

MISS = [("sh000001", "上证指数", "宽基"), ("sz399001", "深证成指", "宽基"),
        ("sh000852", "中证1000", "宽基"), ("sh000903", "中证A100", "宽基"),
        ("sh000985", "中证全指", "宽基"), ("sh000968", "300周期", "风格"),
        ("sh000994", "全指通信", "行业"), ("sh000995", "全指公用", "行业"),
        ("sh000933", "中证医药", "行业"), ("sh000935", "中证信息", "行业"),
        ("sh000820", "煤炭指数", "细分"), ("sz399619", "深证金融", "细分"),
        ("sz399811", "CSSW电子", "细分"), ("sz399973", "中证国防", "主题"),
        ("sz399808", "中证新能", "主题"), ("sh000827", "中证环保", "主题")]
todo = [(c, n, g) for c, n, g in MISS if c not in have]


def flash(sym, verbose=False):
    try:
        r = S.get(f"https://data.gtimg.cn/flashdata/hushen/monthly/{sym}.js", timeout=15)
        if verbose:
            print("      flash status=%s len=%s head=%r" % (r.status_code, len(r.text), r.text[:90]))
        if r.status_code != 200 or not r.text.strip():
            return None
        r.encoding = "gbk"
        txt = r.text
        body = txt
        m = re.search(r'monthly_data\s*=\s*"(.*?)"\s*;', txt, re.S)
        if m:
            body = m.group(1)
        rows = []
        for line in body.replace("\\\n", "\n").split("\n"):
            p = line.strip().rstrip("\\").strip().split()
            if len(p) < 5:
                continue
            d = p[0]
            if len(d) != 8 or not d.isdigit():
                continue
            try:
                rows.append({"d": f"{d[:4]}-{d[4:6]}-{d[6:]}", "o": float(p[1]),
                             "h": float(p[2]), "l": float(p[3]), "c": float(p[4])})
            except Exception:
                continue
        return rows or None
    except Exception as e:
        if verbose:
            print("      flash ERR", type(e).__name__)
        return None


def fq(sym):
    try:
        r = S.get("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get",
                  params={"param": f"{sym},month,1990-01-01,2026-12-31,600,qfq"}, timeout=20)
        j = r.json()
        d = (j.get("data") or {}).get(sym) or {}
        kl = d.get("qfqmonth") or d.get("month") or []
        rows = []
        for k in kl:
            try:
                rows.append({"d": k[0], "o": float(k[1]), "c": float(k[2]),
                             "h": float(k[3]), "l": float(k[4])})
            except Exception:
                continue
        return rows or None
    except Exception:
        return None


def main():
    print("待补 %d 个" % len(todo), flush=True)
    pending = list(todo)
    for rnd in range(1, 7):
        left = []
        print(f"\n--- 第 {rnd} 轮 (剩余 {len(pending)}) ---", flush=True)
        for sym, name, grp in pending:
            a = flash(sym, verbose=(rnd == 1))
            time.sleep(random.uniform(0.4, 0.8))
            b = fq(sym)
            best = max([x for x in (a, b) if x], key=len, default=None)
            if best and len(best) >= 48:
                best.sort(key=lambda x: x["d"])
                have[sym] = {"secid": sym, "name": name, "group": grp,
                             "src": "flash" if best is a else "fq", "rows": best}
                print(f"  OK {name:<10} {len(best):>4}根 {best[0]['d']} -> {best[-1]['d']}", flush=True)
            else:
                left.append((sym, name, grp))
            time.sleep(random.uniform(0.5, 1.0))
        pending = left
        if not pending:
            break
        time.sleep(4 * rnd)

    items = list(have.values())
    items.sort(key=lambda x: (x["group"], x["name"]))
    raw["items"] = items
    raw["count"] = len(items)
    raw["fetched_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(os.path.join(OUT, "seasonality_raw.json"), "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False)
    print(f"\n合计 {len(items)} 个品种; 仍缺: {[t[1] for t in pending]}")


if __name__ == "__main__":
    main()
