# -*- coding: utf-8 -*-
"""日线定位: 2024初 / 2016初 / 2018初 / 2022初 小盘股的暴跌区间"""
import sys, os, json, time
import requests
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
S = requests.Session()
S.trust_env = False
S.headers.update({"User-Agent": "Mozilla/5.0", "Referer": "https://gu.qq.com/"})

SYMS = {"sh000852": "中证1000", "sz399303": "国证2000", "sh000905": "中证500",
        "sh000300": "沪深300", "sh000001": "上证指数", "sz399006": "创业板指",
        "sh932000": "中证2000", "sz399001": "深证成指"}


def day(sym, a, b, n=400):
    try:
        r = S.get("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get",
                  params={"param": f"{sym},day,{a},{b},{n},qfq"}, timeout=20)
        j = r.json()
        d = (j.get("data") or {}).get(sym) or {}
        kl = d.get("qfqday") or d.get("day") or []
        out = []
        for k in kl:
            out.append({"d": k[0], "c": float(k[2])})
        return pd.Series([x["c"] for x in out], index=[x["d"] for x in out])
    except Exception as e:
        return None


def seg(name, sym, a, b, lo, hi):
    s = day(sym, a, b)
    if s is None or s.empty:
        print(f"  {name:<8} 无数据")
        return None
    s = s[(s.index >= lo) & (s.index <= hi)]
    if s.empty:
        return None
    peak_i = s.idxmax()
    trough_i = s.idxmin()
    # 区间内最大回撤
    roll = s.cummax()
    dd = ((s - roll) / roll)
    mdd_i = dd.idxmin()
    mdd = dd.min() * 100
    ret = (s.iloc[-1] / s.iloc[0] - 1) * 100
    print(f"  {name:<8} {s.index[0]}~{s.index[-1]}  区间 {ret:>+7.2f}%   最大回撤 {mdd:>+7.2f}%  "
          f"高点 {peak_i}  低点 {trough_i}({s.min():.0f})")
    return {"name": name, "ret": round(ret, 2), "mdd": round(mdd, 2),
            "peak": peak_i, "trough": trough_i, "low": round(float(s.min()), 2),
            "series": {k: round(float(v), 2) for k, v in s.items()}}


for tag, a, b, lo, hi in [
    ("2024年初 (1月2日-2月29日)", "2024-01-01", "2024-03-01", "2024-01-02", "2024-02-29"),
    ("2016年初 (1月4日-2月29日)", "2016-01-01", "2016-03-01", "2016-01-04", "2016-02-29"),
    ("2018年初 (1月2日-2月28日)", "2018-01-01", "2018-03-01", "2018-01-02", "2018-02-28"),
    ("2022年初 (1月4日-2月28日)", "2022-01-01", "2022-03-01", "2022-01-04", "2022-02-28"),
]:
    print(f"\n=== {tag} ===")
    for sym, nm in SYMS.items():
        seg(nm, sym, a, b, lo, hi)
        time.sleep(0.35)
