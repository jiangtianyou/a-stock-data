# -*- coding: utf-8 -*-
"""抖音评论提及标的 —— 9月表现分析"""
import json, os, sys
from collections import OrderedDict

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "out")

with open(os.path.join(OUT, "dy_kline.json"), encoding="utf-8") as f:
    K = json.load(f)


def series(sym):
    rows = K[sym]["rows"]
    out = []
    for r in rows:
        out.append({
            "d": r[0], "o": float(r[1]), "c": float(r[2]),
            "h": float(r[3]), "l": float(r[4]), "v": float(r[5]),
        })
    return out


def sep_window(rows):
    """返回 9 月行 + 基准行（9月首个交易日的前一交易日）"""
    idx = next(i for i, r in enumerate(rows) if r["d"] >= "2026-09-01")
    if idx == 0:
        raise ValueError("no base bar")
    return rows[idx:], rows[idx - 1]


BENCH = {"sh000001": "上证指数", "sz399001": "深证成指", "sz399006": "创业板指",
         "sh000688": "科创50", "sh000852": "中证1000"}

idx_cmp = {}
for sym in BENCH:
    rs, base = sep_window(series(sym))
    idx_cmp[sym] = {
        "name": BENCH[sym],
        "sep_ret": rs[-1]["c"] / base["c"] - 1,
        "sep_days": len(rs),
        "first": rs[0]["d"], "last": rs[-1]["d"],
    }

sh_ret = idx_cmp["sh000001"]["sep_ret"]


def max_dd(seq):
    peak = seq[0]; mdd = 0.0; pk_at = seq[0]
    for v in seq:
        if v > peak:
            peak = v
        dd = v / peak - 1
        if dd < mdd:
            mdd = dd
    return mdd


res = []
for sym, node in K.items():
    if sym in BENCH or sym == "bj899050":
        continue
    rows = series(sym)
    rs, base = sep_window(rows)
    if len(rs) < 5:
        continue
    c0 = base["c"]
    closes = [r["c"] for r in rs]
    highs = [r["h"] for r in rs]
    lows = [r["l"] for r in rs]
    ret = closes[-1] / c0 - 1
    hi, lo = max(highs), min(lows)
    limit_pct = 0.19 if sym[2:5] in ("300", "301", "688", "689") else 0.098
    zt = 0
    for i, r in enumerate(rs):
        prev = c0 if i == 0 else rs[i - 1]["c"]
        if r["c"] / prev - 1 >= limit_pct and r["h"] == r["c"]:
            zt += 1
    # 成交额（元）：volume 单位=手，估算用 close*volume*100
    amt_sep = sum(r["c"] * r["v"] * 100 for r in rs)
    amt_sep_d = amt_sep / len(rs) / 1e8 if rs else 0
    # 8 月同期（基准日前 20 个交易日）
    prev_rows = rows[max(0, rows.index(base) - 20):rows.index(base)]
    amt_aug_d = (sum(r["c"] * r["v"] * 100 for r in prev_rows) / len(prev_rows) / 1e8) if prev_rows else 0
    res.append(OrderedDict([
        ("name", node["name"]), ("sym", sym),
        ("base_d", base["d"]), ("base_c", round(c0, 3)),
        ("last_d", rs[-1]["d"]), ("last_c", round(closes[-1], 3)),
        ("ret", ret),
        ("excess", ret - sh_ret),
        ("hi", hi), ("lo", lo),
        ("ret_if_peak", hi / c0 - 1),
        ("dd_from_peak", closes[-1] / hi - 1),
        ("mdd", max_dd(closes)),
        ("zt", zt),
        ("amp_sep", round(amt_sep_d, 2)), ("amp_aug", round(amt_aug_d, 2)),
        ("amp_chg", (amt_sep_d / amt_aug_d - 1) if amt_aug_d else None),
        ("ndays", len(rs)),
    ]))

res.sort(key=lambda x: -x["ret"])
with open(os.path.join(OUT, "dy_perf.json"), "w", encoding="utf-8") as f:
    json.dump({"indexes": idx_cmp, "stocks": res}, f, ensure_ascii=False, indent=1)

print("== 指数 9 月表现 (%s ~ %s) ==" % (idx_cmp["sh000001"]["first"], idx_cmp["sh000001"]["last"]))
for s, v in idx_cmp.items():
    print("  %-8s %+7.2f%%" % (v["name"], v["sep_ret"] * 100))
print("基准日: %s  个股交易日数: %d" % (res[0]["base_d"], res[0]["ndays"]))
print()
print("%-9s %8s %8s %8s %8s %7s %6s %6s %8s" %
      ("名称", "9月涨幅", "超额", "距峰值", "最大回撤", "最高涨", "涨停", "量比", "9月末价"))
for r in res:
    print("%-9s %+7.2f%% %+7.2f%% %7.2f%% %8.2f%% %+7.1f%% %5d次 %5.2f %8.2f" % (
        r["name"], r["ret"] * 100, r["excess"] * 100, r["dd_from_peak"] * 100,
        r["mdd"] * 100, r["ret_if_peak"] * 100, r["zt"],
        (r["amp_chg"] or 0), r["last_c"]))
