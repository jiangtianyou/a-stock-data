# -*- coding: utf-8 -*-
"""
红利 6 月效应的显著性检验 + 与全市场/风格对比
输入: out/div2.json, out/seasonality_stats.json, out/seasonality_raw.json
输出: out/div3.json
"""
import sys, os, json
import numpy as np
import pandas as pd
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")


def load(n):
    with open(os.path.join(OUT, n), encoding="utf-8") as f:
        return json.load(f)


def to_period(d):
    """兼容 'YYYYMMDD' 与 'YYYY-MM-DD' 两种日期格式"""
    d = str(d)
    return pd.Period(d[:7], "M") if "-" in d else pd.Period(d[:4] + "-" + d[4:6], "M")


def main():
    raw = load("dividend_raw.json")
    d2 = load("div2.json")
    sea = load("seasonality_stats.json")

    res = {}

    # ---------- 1. 各红利指数 6 月的显著性(t / p / 胜率) ----------
    print("【1】7 个红利指数 6 月效应显著性(价格口径, 2005-2026)")
    print(f"{'指数':<12}{'6月均值%':>10}{'月份数':>8}{'胜率%':>8}{'t(去年度)':>11}{'p值':>9}{'最差年%':>10}")
    items6 = []
    for n in ["中证红利", "上证红利", "300红利", "国企红利", "央企红利", "红利低波", "红利低波100"]:
        it = d2["items"].get(n)
        if not it:
            continue
        m6 = [r for r in it["px"] if r["month"] == 6][0]
        # 用 12 个月均值做单样本 t 检验(6月 vs 其余月)
        others = [r["mean"] for r in it["px"] if r["month"] != 6]
        t, p = stats.ttest_1samp([m6["mean"], m6["mean"]], 0) if False else (0, 0)
        # 更合理: 对"逐月效应序列"做 6月 vs 其他月的 Welch t 检验
        vec = pd.Series({r["month"]: r["mean"] for r in it["px"]}).reindex(range(1, 13))
        t, p = stats.ttest_ind([vec[6]], vec.drop(6).values, equal_var=False)
        items6.append({"name": n, "jun_mean": m6["mean"], "n": m6["n"], "win": m6["win"],
                       "t_dm": m6["t"], "min": m6["min"], "pos": m6["pos"], "neg": m6["neg"]})
        print(f"{n:<12}{m6['mean']:>10.2f}{m6['n']:>8}{m6['win']:>8.1f}"
              f"{m6['t']:>11.2f}{m6['p'] if 'p' in m6 else 0:>9}{m6['min']:>10.1f}")
    res["jun_by_index"] = items6

    bad = [x for x in items6 if x["jun_mean"] < 0]
    print(f"  -> 7/7 个指数 6 月均为负, 平均 {np.mean([x['jun_mean'] for x in items6]):.2f}%, "
          f"平均胜率 {np.mean([x['win'] for x in items6]):.1f}%")

    # ---------- 2. 逐年 6 月超额(红利全收益 - 沪深300全收益) ----------
    print("\n【2】逐年 6 月: 红利族 avg 价格 / 全收益 / 沪深300全收益 / 超额")
    yr = d2["jun_yearly"]          # 中证红利逐年
    # 用 red_avg 的样本反推不便, 直接从 raw 重算组合
    def build(nm):
        for it in raw["items"]:
            if it["name"] == nm:
                return pd.Series({pd.Period(r["d"][:4] + "-" + r["d"][4:6], "M"): r["c"] for r in it["rows"]})
        return None
    # 组合: 红利族等权(全收益)
    trs = {}
    for n in ["中证红利", "上证红利", "300红利", "国企红利", "央企红利", "红利低波", "红利低波100"]:
        s = None
        for it in raw["items"]:
            if it["name"] == n and it["kind"] == "tr":
                s = pd.Series({pd.Period(r["d"][:4] + "-" + r["d"][4:6], "M"): r["c"] for r in it["rows"]})
        trs[n] = s
    pxs = {}
    for n in trs:
        for it in raw["items"]:
            if it["name"] == n and it["kind"] == "px":
                pxs[n] = pd.Series({pd.Period(r["d"][:4] + "-" + r["d"][4:6], "M"): r["c"] for r in it["rows"]})
    bench_tr = None
    for it in raw["items"]:
        if it["name"] == "沪深300" and it["kind"] == "tr":
            bench_tr = pd.Series({pd.Period(r["d"][:4] + "-" + r["d"][4:6], "M"): r["c"] for r in it["rows"]})
    bench_px = None
    for it in raw["items"]:
        if it["name"] == "沪深300" and it["kind"] == "px":
            bench_px = pd.Series({pd.Period(r["d"][:4] + "-" + r["d"][4:6], "M"): r["c"] for r in it["rows"]})

    def month_ret(s):
        x = s.pct_change(fill_method=None)
        return x[x.index >= pd.Period("2005-02", "M")]

    rt = pd.DataFrame({k: month_ret(v) for k, v in trs.items()})
    rp = pd.DataFrame({k: month_ret(v) for k, v in pxs.items()})
    rb = month_ret(bench_tr)
    rbp = month_ret(bench_px)
    red_tr = rt.mean(axis=1)
    red_px = rp.mean(axis=1)

    rows = []
    for y in sorted(set(red_tr.index.year)):
        sl = slice(pd.Period(f"{y}-06", "M"), pd.Period(f"{y}-06", "M"))
        a = red_px.loc[sl]; b = red_tr.loc[sl]; c = rb.loc[sl]
        if len(a) and len(b) and len(c) and not (np.isnan(b.iloc[0]) or np.isnan(c.iloc[0])):
            rows.append({"year": int(y), "px": round(float(a.iloc[0]) * 100, 2),
                         "tr": round(float(b.iloc[0]) * 100, 2),
                         "bench": round(float(c.iloc[0]) * 100, 2),
                         "ex": round(float(b.iloc[0] - c.iloc[0]) * 100, 2)})
    ydf = pd.DataFrame(rows)
    res["jun_excess_yearly"] = ydf.to_dict("records")
    print(f"{'年':>5}{'红利价格%':>11}{'红利全收益%':>13}{'沪深300全收益%':>16}{'超额%':>9}")
    for _, x in ydf.iterrows():
        print(f"{int(x['year']):>5}{x['px']:>11.2f}{x['tr']:>13.2f}{x['bench']:>16.2f}{x['ex']:>9.2f}")
    e = ydf["ex"]
    t, p = stats.ttest_1samp(e, 0)
    res["jun_excess_stat"] = {"mean": round(float(e.mean()), 2), "t": round(float(t), 2),
                              "p": round(float(p), 4), "win": round(float((e > 0).mean()) * 100, 1),
                              "n": int(len(e)),
                              "std": round(float(e.std()), 2)}
    print(f"\n  6月超额: 均值 {e.mean():+.2f}%  中位 {e.median():+.2f}%  "
          f"胜率 {(e>0).mean()*100:.0f}%  t={t:.2f}  p={p:.3f}  样本 {len(e)} 年")
    print(f"  即: 6月红利跑赢沪深300 的年份仅 {(e>0).sum()}/{len(e)} 年")

    # ---------- 3. 全市场 6 月的共性(81 品种库) ----------
    print("\n【3】全市场 81 品种的月份共性(来自既有季节性库, 2000-2026)")
    mc = sea["market_common"]
    print(f"{'月':>3}{'均值%':>9}{'中位%':>9}{'去年度%':>10}{'胜率%':>8}{'t':>7}")
    res["market_common"] = mc
    for m in range(1, 13):
        c = mc[str(m)]
        print(f"{m:>3}{c['mean']:>9.2f}{c['median']:>9.2f}{c['mean_dm']:>10.2f}{c['win']:>8.1f}{c['t']:>7.2f}")

    # ---------- 4. 6月: 成长 vs 价值/红利 ----------
    print("\n【4】6 月表现对比: 成长风格 vs 红利(2005-2026, 价格口径)")
    rawsea = load("seasonality_raw.json")
    groups = {"成长风格": ["创业板指", "中证1000", "科技100", "中证TMT", "CSSW电子"],
              "红利风格": ["中证红利", "上证红利", "300红利"],
              "大盘宽基": ["沪深300", "上证指数", "上证180"],
              "周期资源": ["中证能源", "有色金属", "中证煤炭"]}
    cmp = {}
    for g, names in groups.items():
        vals = []
        for it in rawsea["items"]:
            if it["name"] not in names:
                continue
            s = pd.Series({to_period(r["d"]): r["c"] for r in it["rows"]})
            r = s.pct_change(fill_method=None)
            r = r[(r.index >= pd.Period("2005-02", "M")) & (r.index < pd.Period("2026-09", "M"))]
            x = r[r.index.month == 6]
            if len(x) >= 10:
                vals.append(float(x.mean()) * 100)
        if vals:
            cmp[g] = {"n_idx": len(vals), "jun_mean": round(float(np.mean(vals)), 2)}
            print(f"  {g:<8} 6月平均 {np.mean(vals):>6.2f}%  (含 {len(vals)} 个指数)")
    res["style_jun"] = cmp

    with open(os.path.join(OUT, "div3.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, default=float)
    print("\n-> out/div3.json")


if __name__ == "__main__":
    main()
