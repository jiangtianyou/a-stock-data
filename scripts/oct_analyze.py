# -*- coding: utf-8 -*-
"""
9-10月行情专题 - 统计分析 v2
输入: out/oct_raw.json (日线)
输出: out/oct_stats.json

样本口径
--------
1991-01~1992 上证指数处于无涨跌停/T+0 的极端期(单月可涨 177%), 严重污染均值,
故:
  ALL    : 1991-01 起   —— 仅作参考, 标注含极端期
  MAIN   : 1997-01 起   —— 主口径 (1996-12-16 涨跌停制度实施后, 29年)
  MODERN : 2000-01 起   —— 现代市场对照
  RECENT : 2010-01 起   —— 近年对照

修正记录
--------
v1 条件概率把已百分化的 h["pre5"] 又乘 100, 导致 "26.59%" 量纲错误 -> v2 已修
"""
import sys, os, json
import numpy as np
import pandas as pd
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")
MAIN = "上证指数"
END_YM = "2026-08"                       # 2026-09 未完月, 剔除

W_PRE = [1, 3, 5, 10, 20]
W_POST = [1, 3, 5, 10, 20]
MAXW = 20


def build(rows):
    d = pd.DataFrame(rows)
    d["d"] = pd.to_datetime(d["d"])
    d = d.sort_values("d").reset_index(drop=True)
    d["ret"] = d["c"].pct_change()
    d["year"] = d["d"].dt.year
    d["month"] = d["d"].dt.month
    d["ym"] = d["d"].dt.strftime("%Y-%m")
    d["doy"] = d["d"].dt.day
    return d


def monthly_series(d):
    last = d.groupby("ym").last().reset_index()
    last["ret"] = last["c"].pct_change()
    last["year"] = last["ym"].str[:4].astype(int)
    last["month"] = last["ym"].str[5:7].astype(int)
    return last.dropna(subset=["ret"]).reset_index(drop=True)


def tstat(x):
    x = np.asarray(x, dtype=float)
    if len(x) < 3 or x.std(ddof=1) == 0:
        return 0.0, 1.0
    t, p = stats.ttest_1samp(x, 0.0)
    return float(t), float(p)


def desc(x, name):
    x = np.asarray(x, dtype=float)
    if len(x) == 0:
        return None
    t, p = tstat(x)
    return {
        "name": name, "n": int(len(x)),
        "mean": round(float(x.mean()) * 100, 2),
        "median": round(float(np.median(x)) * 100, 2),
        "std": round(float(x.std(ddof=1)) * 100, 2) if len(x) > 1 else 0.0,
        "win": round(float((x > 0).mean()) * 100, 1),
        "min": round(float(x.min()) * 100, 1),
        "max": round(float(x.max()) * 100, 1),
        "t": round(t, 2), "p": round(p, 4),
    }


def single_month(ms):
    dm = ms.copy()
    dm["ret_dm"] = dm["ret"] - dm.groupby("year")["ret"].transform("mean")
    out = {}
    for m in range(1, 13):
        s = dm[dm["month"] == m]
        if len(s) == 0:
            continue
        rec = desc(s["ret"].values, f"{m}月")
        rec["mean_dm"] = round(float(s["ret_dm"].mean()) * 100, 2)
        rec["t_dm"], rec["p_dm"] = [round(v, 4) for v in tstat(s["ret_dm"].values)]
        rec["years"] = [f"{int(y)}:{v*100:+.1f}" for y, v in zip(s["year"], s["ret"])]
        out[str(m)] = rec
    return out


def decade_split(ms, month, decades):
    s = ms[ms["month"] == month]
    res = {}
    for tag, lo, hi in decades:
        x = s[(s["year"] >= lo) & (s["year"] <= hi)]["ret"].values
        if len(x) >= 3:
            d = desc(x, tag)
            res[tag] = {"n": d["n"], "mean": d["mean"], "median": d["median"],
                        "win": d["win"], "std": d["std"]}
    return res


# ---------------------------------------------------------------- 长假
def find_holidays(d):
    res = []
    for y in sorted(set(d["year"])):
        oct_ = d[(d["year"] == y) & (d["month"] == 10)]
        sep = d[(d["year"] == y) & (d["month"] == 9)]
        if len(oct_) == 0 or len(sep) == 0:
            continue
        i_first = int(oct_.index[0])
        i_last = i_first - 1
        if i_last < 0:
            continue
        gap = (d.loc[i_first, "d"] - d.loc[i_last, "d"]).days
        if gap < 5:
            continue
        res.append((y, i_last, i_first, gap))
    return res


def holiday_effect(df, hol):
    """节前 N 日 / 节后 N 日累计收益; 节后以节前最后收盘为基准"""
    c = df["c"].values.astype(float)
    out, detail = {}, []
    pre = {n: [] for n in W_PRE}
    post = {n: [] for n in W_POST}
    post_b = {n: [] for n in W_POST}
    for (y, i0, i1, gap) in hol:
        if i0 - MAXW < 0 or i1 + MAXW >= len(c):
            continue
        row = {"year": y, "last_day": str(df.loc[i0, "d"].date()),
               "first_day": str(df.loc[i1, "d"].date()), "gap_days": gap}
        for n in W_PRE:
            r = c[i0] / c[i0 - n] - 1
            pre[n].append(r); row[f"pre{n}"] = round(r * 100, 2)
        for n in W_POST:
            r = c[i1 + n - 1] / c[i0] - 1
            post[n].append(r); row[f"post{n}"] = round(r * 100, 2)
            r2 = c[i1 + n - 1] / c[i1] - 1
            post_b[n].append(r2); row[f"post{n}b"] = round(r2 * 100, 2)
        detail.append(row)
    for n in W_PRE:
        out[f"pre{n}"] = desc(pre[n], f"节前{n}日")
    for n in W_POST:
        out[f"post{n}"] = desc(post[n], f"节后{n}日(基准=节前收盘)")
        out[f"post{n}b"] = desc(post_b[n], f"节后{n}日(基准=节后首日)")
    return out, detail


def volume_effect(df, hol):
    v = df["v"].values.astype(float)
    year_mean = df.groupby("year")["v"].mean().to_dict()
    pre_r, post_r, mid_r = [], [], []
    for (y, i0, i1, gap) in hol:
        ym_ = year_mean.get(y)
        if not ym_ or ym_ <= 0:
            continue
        if i0 - 5 < 0 or i1 + 25 >= len(v):
            continue
        pre_r.append(v[i0 - 4:i0 + 1].mean() / ym_ - 1)
        post_r.append(v[i1:i1 + 5].mean() / ym_ - 1)
        mid_r.append(v[i1 + 5:i1 + 25].mean() / ym_ - 1)
    return {"pre5_vs_year": round(float(np.mean(pre_r)) * 100, 1) if pre_r else None,
            "post5_vs_year": round(float(np.mean(post_r)) * 100, 1) if post_r else None,
            "post5to25_vs_year": round(float(np.mean(mid_r)) * 100, 1) if mid_r else None,
            "n": len(pre_r)}


def half_month(df, month):
    s = df[df["month"] == month]
    res = {}
    for tag, cond in [("上半月(1-15)", s["doy"] <= 15), ("下半月(16-末)", s["doy"] > 15)]:
        vals = []
        for y, g in s[cond].groupby("year"):
            g = g.sort_values("d")
            if len(g) < 5:
                continue
            vals.append(g["c"].iloc[-1] / g["c"].iloc[0] - 1)
        if vals:
            res[tag] = desc(vals, tag)
    return res


def main():
    raw = json.load(open(os.path.join(OUT, "oct_raw.json"), encoding="utf-8"))
    dfs = {it["name"]: build(it["rows"]) for it in raw["items"]}
    d = dfs[MAIN]
    ms_all = monthly_series(d)

    def sl(start):
        return ms_all[(ms_all["ym"] >= start) & (ms_all["ym"] <= END_YM)].reset_index(drop=True)

    ms_all_s, ms, ms00, ms10 = sl("1991-01"), sl("1997-01"), sl("2000-01"), sl("2010-01")
    DEC = [("1997-2009", 1997, 2009), ("2010-2019", 2010, 2019), ("2020-2026", 2020, 2026)]

    res = {"fetched_at": raw["fetched_at"], "main": MAIN,
           "sample": {"full": f"{d['d'].iloc[0].date()} ~ {d['d'].iloc[-1].date()}",
                      "n_days": int(len(d)),
                      "main_period": f"{ms['ym'].iloc[0]} ~ {ms['ym'].iloc[-1]}",
                      "main_years": int(ms["year"].nunique())}}

    res["single_month_all"] = single_month(ms_all_s)
    res["single_month"] = single_month(ms)
    res["single_month_2000"] = single_month(ms00)
    res["single_month_2010"] = single_month(ms10)
    res["decade"] = {f"{m}月": decade_split(ms, m, DEC) for m in (9, 10)}

    # ---- 长假 ----
    def hol_of(df):
        dd = df.reset_index(drop=True)
        h = find_holidays(dd)
        e, det = holiday_effect(dd, h)
        return e, det, dd

    heff, hdetail, d_all = hol_of(d)
    res["holiday"] = heff                 # 全历史
    res["holiday_detail"] = hdetail
    res["holiday_years"] = [{"year": y, "gap_days": g} for (y, _, _, g) in find_holidays(d_all)]
    for tag, st in [("holiday_2000", "2000-01-01"), ("holiday_2010", "2010-01-01")]:
        e, det, _ = hol_of(d[d["d"] >= st])
        res[tag] = e
        if tag == "holiday_2000":
            res["holiday_detail_2000"] = det
    # 节后的量能与月内结构用 2000 起样本
    d00 = d[d["d"] >= "2000-01-01"].reset_index(drop=True)
    res["volume"] = volume_effect(d00, find_holidays(d00))
    res["volume_all"] = volume_effect(d_all, find_holidays(d_all))

    # ---- 条件概率 (修正量纲) ----
    cond = {}
    pairs = []
    for y in sorted(set(ms["year"])):
        a = ms[(ms["year"] == y) & (ms["month"] == 9)]
        b = ms[(ms["year"] == y) & (ms["month"] == 10)]
        if len(a) and len(b):
            pairs.append((y, float(a["ret"].iloc[0]), float(b["ret"].iloc[0])))
    up9 = [b for (_, a, b) in pairs if a > 0]
    dn9 = [b for (_, a, b) in pairs if a <= 0]
    cond["n_pairs"] = len(pairs)
    cond["sep_up"] = {"n": len(up9), "oct_mean": round(float(np.mean(up9)) * 100, 2) if up9 else None,
                      "oct_win": round(float(np.mean([x > 0 for x in up9])) * 100, 1) if up9 else None}
    cond["sep_down"] = {"n": len(dn9), "oct_mean": round(float(np.mean(dn9)) * 100, 2) if dn9 else None,
                        "oct_win": round(float(np.mean([x > 0 for x in dn9])) * 100, 1) if dn9 else None}
    if pairs:
        cond["corr_sep_oct"] = round(float(np.corrcoef([a for _, a, _ in pairs],
                                                      [b for _, _, b in pairs])[0, 1]), 3)
    det00 = res["holiday_detail_2000"]
    pre5v = [h["pre5"] for h in det00]
    post5v = [h["post5"] for h in det00]
    dn = [p for p, q in zip(post5v, pre5v) if q < 0]
    up = [p for p, q in zip(post5v, pre5v) if q >= 0]
    cond["pre5_down"] = {"n": len(dn), "post5_mean": round(float(np.mean(dn)), 2) if dn else None,
                         "post5_win": round(float(np.mean([x > 0 for x in dn])) * 100, 1) if dn else None}
    cond["pre5_up"] = {"n": len(up), "post5_mean": round(float(np.mean(up)), 2) if up else None,
                       "post5_win": round(float(np.mean([x > 0 for x in up])) * 100, 1) if up else None}
    if pre5v:
        cond["corr_pre5_post5"] = round(float(np.corrcoef(pre5v, post5v)[0, 1]), 3)
    res["conditional"] = cond

    res["half_month"] = {"9月": half_month(d00, 9), "10月": half_month(d00, 10)}
    res["half_month_2010"] = {"9月": half_month(d[d["d"] >= "2010-01-01"].reset_index(drop=True), 9)}

    # ---- 年内高低点月份 ----
    hi, lo, n_year = {}, {}, 0
    for y, g in d.groupby("year"):
        g = g.sort_values("d")
        if y == 2026 or len(g) < 200:
            continue
        n_year += 1
        hm = int(g.loc[g["h"].idxmax(), "month"]); lm = int(g.loc[g["l"].idxmin(), "month"])
        hi[str(hm)] = hi.get(str(hm), 0) + 1
        lo[str(lm)] = lo.get(str(lm), 0) + 1
    res["year_high_month"] = hi
    res["year_low_month"] = lo
    res["n_full_year"] = n_year

    # ---- 各宽基 9/10月 ----
    cross = {}
    for n, dd in dfs.items():
        m = monthly_series(dd)
        m = m[(m["year"] >= 2000) & (m["ym"] <= END_YM)]
        if m["year"].nunique() < 8:
            continue
        e = {}
        for mo in (9, 10):
            s = m[m["month"] == mo]
            if len(s) < 5:
                continue
            dmx = s.copy()
            dmx["dm"] = dmx["ret"] - dmx.groupby("year")["ret"].transform("mean")
            e[f"{mo}月"] = {"n": int(len(s)), "mean": round(float(s["ret"].mean()) * 100, 2),
                            "median": round(float(s["ret"].median()) * 100, 2),
                            "mean_dm": round(float(dmx["dm"].mean()) * 100, 2),
                            "win": round(float((s["ret"] > 0).mean()) * 100, 1)}
        cross[n] = e
    res["cross_index"] = cross

    # ---- 年度明细 ----
    yd = []
    for y in sorted(set(ms["year"])):
        a = ms[(ms["year"] == y) & (ms["month"] == 9)]
        b = ms[(ms["year"] == y) & (ms["month"] == 10)]
        if len(a) and len(b):
            va, vb = float(a["ret"].iloc[0]), float(b["ret"].iloc[0])
            yd.append({"year": int(y), "sep": round(va * 100, 2), "oct": round(vb * 100, 2),
                       "sum": round((va + vb) * 100, 2)})
    res["yearly_detail"] = yd

    # ---- 极端年份 ----
    s9 = ms[ms["month"] == 9].sort_values("ret")
    s10 = ms[ms["month"] == 10].sort_values("ret")
    res["extreme_9"] = {"worst": [f"{int(y)} {v*100:+.1f}%" for y, v in zip(s9["year"].head(5), s9["ret"].head(5))],
                        "best": [f"{int(y)} {v*100:+.1f}%" for y, v in zip(s9["year"].tail(5)[::-1], s9["ret"].tail(5)[::-1])]}
    res["extreme_10"] = {"worst": [f"{int(y)} {v*100:+.1f}%" for y, v in zip(s10["year"].head(5), s10["ret"].head(5))],
                         "best": [f"{int(y)} {v*100:+.1f}%" for y, v in zip(s10["year"].tail(5)[::-1], s10["ret"].tail(5)[::-1])]}

    with open(os.path.join(OUT, "oct_stats.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False)

    # ================= 速览 =================
    print(f"主口径样本: {res['sample']['main_period']}  年数={res['sample']['main_years']}  标的={MAIN}")
    for tag, key in [("【主口径 1997起】", "single_month"), ("【2000起】", "single_month_2000"),
                     ("【2010起】", "single_month_2010"), ("【1991起 含极端期】", "single_month_all")]:
        print(f"\n=== 月度季节性 {tag} ===")
        print(f"{'月':<4}{'均值%':>9}{'中位%':>8}{'去年度%':>9}{'胜率%':>8}{'std%':>8}{'t':>7}{'n':>4}")
        for m in range(1, 13):
            c = res[key][str(m)]
            mark = " <==" if m in (9, 10) else ""
            print(f"{m:>2}月{c['mean']:>9.2f}{c['median']:>8.2f}{c['mean_dm']:>9.2f}"
                  f"{c['win']:>8.1f}{c['std']:>8.2f}{c['t_dm']:>7.2f}{c['n']:>4}{mark}")

    for tag, key in [("全历史", "holiday"), ("2000起", "holiday_2000"), ("2010起", "holiday_2010")]:
        print(f"\n=== 国庆长假效应 【{tag}】 ===")
        for k in ["pre1", "pre3", "pre5", "pre10", "pre20", "post1", "post3", "post5", "post10", "post20"]:
            v = res[key].get(k)
            if v:
                print(f"  {v['name']:<26} 均值{v['mean']:>7.2f}%  中位{v['median']:>7.2f}%  "
                      f"胜率{v['win']:>5.1f}%  t={v['t']:>5.2f}  n={v['n']}")

    print("\n=== 条件概率 (1997起) ===")
    print(f"  9月涨 -> 10月均值 {cond['sep_up']['oct_mean']}%  胜率 {cond['sep_up']['oct_win']}%  (n={cond['sep_up']['n']})")
    print(f"  9月跌 -> 10月均值 {cond['sep_down']['oct_mean']}%  胜率 {cond['sep_down']['oct_win']}%  (n={cond['sep_down']['n']})")
    print(f"  相关系数(9月,10月) = {cond.get('corr_sep_oct')}")
    print(f"  节前5日跌 -> 节后5日均值 {cond['pre5_down']['post5_mean']}%  胜率 {cond['pre5_down']['post5_win']}%  (n={cond['pre5_down']['n']})")
    print(f"  节前5日涨 -> 节后5日均值 {cond['pre5_up']['post5_mean']}%  胜率 {cond['pre5_up']['post5_win']}%  (n={cond['pre5_up']['n']})")
    print(f"  相关系数(节前5,节后5) = {cond.get('corr_pre5_post5')}")

    print("\n=== 月内结构 (2000起) ===")
    for mo in ("9月", "10月"):
        for k, v in res["half_month"][mo].items():
            print(f"  {mo} {k:<14} 均值{v['mean']:>7.2f}%  胜率{v['win']:>5.1f}%  n={v['n']}")

    print("\n=== 量能 相对当年日均量 (2000起) ===")
    print(" ", res["volume"])

    print(f"\n=== 年内最高点月份分布 (n={res['n_full_year']}年) ===")
    for m in range(1, 13):
        c = res["year_high_month"].get(str(m), 0)
        print(f"  {m:>2}月 {'█'*c} {c}")
    print(f"=== 年内最低点月份分布 ===")
    for m in range(1, 13):
        c = res["year_low_month"].get(str(m), 0)
        print(f"  {m:>2}月 {'█'*c} {c}")

    print("\n=== 各宽基 2000起 9/10月 ===")
    for n, e in res["cross_index"].items():
        s = e.get("9月", {}); o = e.get("10月", {})
        print(f"  {n:<8} 9月 mean{s.get('mean'):>7}/win{s.get('win'):>5} | 10月 mean{o.get('mean'):>7}/win{o.get('win'):>5}")

    print("\n-> out/oct_stats.json")


if __name__ == "__main__":
    main()
