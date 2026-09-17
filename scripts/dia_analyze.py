# -*- coding: utf-8 -*-
"""
培育钻石板块分析：区间收益 / 回撤 / 量能 / 阶段节奏 / 资金
输出 out/dia_analysis.json
"""
import json, os, sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")

D = json.load(open(os.path.join(OUT, "dia_daily.json"), encoding="utf-8"))
FIN = json.load(open(os.path.join(OUT, "dia_fin.json"), encoding="utf-8"))
daily, quote = D["daily"], D["quote"]

YTD0 = "2025-12-31"
SEP = "2026-09-01"


def seq(sym):
    return daily[sym]["rows"]


def close_on_or_before(rows, d):
    hit = None
    for r in rows:
        if r["date"] <= d:
            hit = r
    return hit


def pct(a, b):
    return (a / b - 1) * 100 if b else None


def max_drawdown(rows):
    peak, pk_at, mdd, mdd_at, pk_before = None, None, 0.0, None, None
    for r in rows:
        c = r["close"]
        if peak is None or c > peak:
            peak, pk_at = c, r["date"]
        dd = c / peak - 1
        if dd < mdd:
            mdd, mdd_at, pk_before = dd, r["date"], pk_at
    return mdd * 100, pk_before, mdd_at


def stats(sym):
    rows = seq(sym)
    for r in rows:
        d0 = r["date"]
        if len(d0) == 8 and "-" not in d0:      # 同花顺板块指数日期为 YYYYMMDD
            r["date"] = f"{d0[:4]}-{d0[4:6]}-{d0[6:]}"
        if not r.get("amt"):                    # 板块指数无成交额字段，补 0 以复用同一套指标
            r["amt"] = 0.0
    rows.sort(key=lambda x: x["date"])
    last = rows[-1]
    base = close_on_or_before(rows, YTD0)
    ytd_rows = [r for r in rows if r["date"] > YTD0]
    hi = max(ytd_rows, key=lambda r: r["close"])
    lo = min(ytd_rows, key=lambda r: r["close"])

    def ret_from(d):
        b = close_on_or_before(rows, d)
        return pct(last["close"], b["close"]) if b else None

    def seg(a, b):
        ra = close_on_or_before(rows, a)
        rb = close_on_or_before(rows, b)
        return pct(rb["close"], ra["close"]) if ra and rb else None

    amt5 = sum(r["amt"] for r in rows[-5:]) / 5
    amt20 = sum(r["amt"] for r in rows[-20:]) / 20
    amt_ytd = sum(r["amt"] for r in ytd_rows) / max(len(ytd_rows), 1)
    amt_pre = sum(r["amt"] for r in ytd_rows[:60]) / 60

    mdd, pk, tk = max_drawdown(ytd_rows)
    q = quote.get(sym, {})

    def qn(k):
        try:
            return float(q.get(k))
        except Exception:
            return None

    return {
        "name": daily[sym]["name"],
        "close": last["close"],
        "ytd_ret": pct(last["close"], base["close"]) if base else None,
        "ret_5d": ret_from("2026-09-10"),
        "ret_20d": ret_from("2026-08-19"),
        "seg_h1": seg(YTD0, "2026-06-30"),
        "seg_jul_aug": seg("2026-06-30", "2026-08-31"),
        "seg_sep": seg("2026-08-31", last["date"]),
        "hi": hi["close"], "hi_date": hi["date"],
        "lo": lo["close"], "lo_date": lo["date"],
        "from_hi": pct(last["close"], hi["close"]),
        "from_lo": pct(last["close"], lo["close"]),
        "mdd": mdd, "mdd_peak": pk, "mdd_trough": tk,
        "amt5": amt5, "amt20": amt20, "amt_ytd": amt_ytd, "amt_pre60": amt_pre,
        "amt_ratio": amt5 / amt_ytd if amt_ytd else None,
        "mktcap": qn("total_market_cap"), "pe": qn("pe_ratio"), "pb": qn("pb_ratio"),
        "turn": qn("turnover_rate"), "chg_ytd_wd": qn("chg_ytd"),
        "high52": qn("high_52week"), "low52": qn("low_52week"),
        "n": len(rows), "first_date": rows[0]["date"],
    }


POOL = list(daily.keys())
CORE3 = ["sz301071", "sh600172", "sz300179"]
ENGINE = {k: v for k, v in FIN["names"].items()}

res = {}
for sym in POOL:
    if sym in ("bk_885937",) or sym.startswith(("sh000", "sz399")):
        continue
    try:
        res[sym] = stats(sym)
    except Exception as e:
        print(f"ERR {sym}: {e}")

# 指数/板块
idx = {}
for sym in ["sh000300", "sz399006", "sh000001"]:
    if sym in daily:
        s = stats(sym)
        idx[sym] = s
if "bk_885937" in daily:
    idx["bk_885937"] = stats("bk_885937")

print("=" * 108)
print("【全样本行情】截至 2026-09-17（盘中）  单位：%，量能：亿元")
print("=" * 108)
print(f"{'名称':<9}{'收盘':>8}{'YTD%':>9}{'H1%':>9}{'7-8月%':>9}{'9月%':>9}"
      f"{'20日%':>9}{'最大回撤%':>10}{'距高点%':>9}{'量能比':>8}{'市值亿':>9}")
for sym, s in sorted(res.items(), key=lambda x: -(x[1]["ytd_ret"] or -999)):
    print(f"{s['name']:<9}{s['close']:>8.2f}{s['ytd_ret']:>9.1f}"
          f"{(s['seg_h1'] or 0):>9.1f}{(s['seg_jul_aug'] or 0):>9.1f}{(s['seg_sep'] or 0):>9.1f}"
          f"{(s['ret_20d'] or 0):>9.1f}{s['mdd']:>10.1f}{(s['from_hi'] or 0):>9.1f}"
          f"{(s['amt_ratio'] or 0):>8.2f}{(s['mktcap'] or 0):>9.1f}")

print("\n【基准】")
for sym, s in idx.items():
    y = f"{s['ytd_ret']:+.1f}%" if s["ytd_ret"] is not None else "n/a(区间起点晚)"
    print(f"{s['name']:<10}{s['close']:>10.2f}  YTD={y}  "
          f"9月={s['seg_sep']:+.1f}%  20日={s['ret_20d']:+.1f}%  最大回撤={s['mdd']:.1f}%  "
          f"高点日 {s['hi_date']}")

print("\n" + "=" * 108)
print("【核心 TOP3 明细】")
print("=" * 108)
for sym in CORE3:
    s = res[sym]
    print(f"\n{s['name']} ({sym})")
    print(f"  收盘 {s['close']}  市值 {s['mktcap']}亿  PE {s['pe']}  PB {s['pb']}  换手 {s['turn']}%")
    print(f"  YTD {s['ytd_ret']:+.1f}%  |  H1 {s['seg_h1']:+.1f}%  |  7-8月 {s['seg_jul_aug']:+.1f}%  "
          f"|  9月 {s['seg_sep']:+.1f}%")
    print(f"  20日 {s['ret_20d']:+.1f}%  5日 {s['ret_5d']:+.1f}%")
    print(f"  YTD高 {s['hi']} ({s['hi_date']})  低 {s['lo']} ({s['lo_date']})  距高点 {s['from_hi']:+.1f}%  "
          f"自低点 {s['from_lo']:+.1f}%")
    print(f"  最大回撤 {s['mdd']:.1f}%  ({s['mdd_peak']} → {s['mdd_trough']})")
    print(f"  日均额: 近5日 {s['amt5']/1e8:.2f}亿  近20日 {s['amt20']/1e8:.2f}亿  "
          f"YTD {s['amt_ytd']/1e8:.2f}亿  量能比 {s['amt_ratio']:.2f}")

json.dump({"stocks": res, "index": idx, "core3": CORE3,
           "asof": daily["sh000300"]["rows"][-1]["date"]},
          open(os.path.join(OUT, "dia_analysis.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\nsaved out/dia_analysis.json")
