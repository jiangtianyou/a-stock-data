# -*- coding: utf-8 -*-
"""
红利指数季节性研究 - 统计分析
输入: out/dividend_raw.json
输出: out/dividend_stats.json

核心方法
--------
价格指数 r_px 与全收益指数 r_tr 在同一基日同一起点(1000), 月度收益之差即为
当月"分红落袋"贡献:  div = r_tr - r_px

由此把季节性拆成两块:
  伪季节性(除息机械效应): 分红集中月份, 价格指数被除息压低, 但持有人并未亏钱
  真季节性(风格/资金):   全收益口径下仍然存在的月度偏离

三层口径:
  L1 mean     原始月均收益
  L2 mean_dm  去年度效应(减当年12个月均值)
  L3 mean_re  去市场共性(减当月全样本横截面中位数)
"""
import sys, os, json
import numpy as np
import pandas as pd
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")

START = "2005-01"          # 首个完整月收益起点
CUR_YM = "2026-09"         # 当前不完整月, 剔除


def load():
    with open(os.path.join(OUT, "dividend_raw.json"), encoding="utf-8") as f:
        return json.load(f)["items"]


def to_monthly(rows):
    """日线 -> 月末收盘价(月度 PeriodIndex); 日期格式 YYYYMMDD"""
    df = pd.DataFrame(rows)
    df["ym"] = df["d"].str[:4] + "-" + df["d"].str[4:6]
    g = df.groupby("ym")["c"].last()
    g.index = pd.PeriodIndex(g.index, freq="M")
    return g.sort_index()


def build(items):
    px, tr, meta = {}, {}, {}
    for it in items:
        s = to_monthly(it["rows"])
        s = s[(s.index >= pd.Period(START, "M")) & (s.index < pd.Period(CUR_YM, "M"))]
        if len(s) < 60:
            continue
        key = it["name"]
        (px if it["kind"] == "px" else tr)[key] = s
        meta[key] = {"group": it["group"], "code": it["code"],
                     "n": int(len(s)), "start": str(s.index.min()), "end": str(s.index.max())}
    return (pd.DataFrame(px), pd.DataFrame(tr), meta)


def wr(s):
    a, b = s.quantile(0.02), s.quantile(0.98)
    return s.clip(a, b)


def monthly_table(r, mkt=None):
    """单个品种的12个月统计; r: 月收益 Series"""
    r = r.dropna()
    d = pd.DataFrame({"r": r.values, "month": r.index.month, "year": r.index.year})
    d["r_dm"] = d["r"] - d.groupby("year")["r"].transform("mean")
    if mkt is not None:
        mk = mkt.reindex(r.index)
        d["rel"] = (r - mk).values
    rows = []
    for m in range(1, 13):
        x = d[d["month"] == m]
        n = len(x)
        if n < 5:
            continue
        sd = x["r"].std()
        sdm = x["r_dm"].std()
        row = {"month": m, "n": int(n),
               "mean": float(x["r"].mean()) * 100,
               "median": float(x["r"].median()) * 100,
               "win": float((x["r"] > 0).mean()) * 100,
               "std": float(sd) * 100,
               "min": float(x["r"].min()) * 100,
               "max": float(x["r"].max()) * 100,
               "pos_years": int((x["r"] > 0).sum()),
               "neg_years": int((x["r"] <= 0).sum()),
               "mean_dm": float(x["r_dm"].mean()) * 100,
               "t": float(x["r_dm"].mean() / (sdm / np.sqrt(n))) if sdm > 0 else 0.0}
        if "rel" in x:
            sdr = x["rel"].std()
            row["mean_re"] = float(x["rel"].mean()) * 100
            row["t_re"] = float(x["rel"].mean() / (sdr / np.sqrt(n))) if sdr > 0 else 0.0
        rows.append(row)
    F, p = 0.0, 1.0
    groups = [d.loc[d["month"] == m, "r"].values for m in range(1, 13)]
    groups = [g for g in groups if len(g) >= 5]
    if len(groups) >= 3:
        F, p = stats.f_oneway(*groups)
    return pd.DataFrame(rows), {"F": float(F), "p": float(p)}


def fmt(df_tbl, name):
    s = f"\n--- {name} ---\n"
    s += f"{'月':>3}{'均值%':>8}{'中位%':>8}{'去年度%':>9}{'去共性%':>9}{'胜率%':>7}{'涨/跌':>8}{'t':>7}{'最差%':>8}{'最好%':>8}\n"
    for _, x in df_tbl.iterrows():
        s += (f"{int(x['month']):>3}{x['mean']:>8.2f}{x['median']:>8.2f}{x['mean_dm']:>9.2f}"
              f"{x.get('mean_re', float('nan')):>9.2f}{x['win']:>7.1f}"
              f"{str(x['pos_years'])+'/'+str(x['neg_years']):>8}{x['t']:>7.2f}"
              f"{x['min']:>8.1f}{x['max']:>8.1f}\n")
    return s


def main():
    items = load()
    px, tr, meta = build(items)
    names = [n for n in px.columns if n in tr.columns]
    print(f"价格/全收益配对品种 {len(names)} 个 | 区间 {px.index.min()} ~ {px.index.max()}"
          f" | 月数 {len(px)}")
    print("品种:", ", ".join(names))

    rpx = px.pct_change().dropna()
    rtr = tr.pct_change().dropna()

    div = rtr - rpx          # 分红贡献(简单差, 单位: 小数)
    red = [n for n in names if meta[n]["group"] in ("红利", "红利低波")]
    bench = [n for n in names if meta[n]["group"] == "基准"]
    allnames = names
    mkt = rpx[allnames].median(axis=1)     # 市场共性基准(横截面中位数)

    out = {"sample": {"range": f"{rpx.index.min()} ~ {rpx.index.max()}",
                      "n_months": int(len(rpx)), "n_pairs": len(names)},
           "meta": meta, "items": {}, "div_by_month": {}, "div_detail": {}}

    # ============ 1. 分红贡献的月份分布(全体红利平均) ============
    print("\n" + "=" * 96)
    print("【核心】红利族 分红贡献(全收益 - 价格) 的月份分布   单位: %")
    print("=" * 96)
    dd = div[red]
    rows = []
    for m in range(1, 13):
        x = dd[dd.index.month == m]
        rows.append({"month": m, "n": int(len(x)),
                     "mean": float(x.mean().mean()) * 100,
                     "median": float(x.median().median()) * 100,
                     "share": float(x.mean().mean() / dd.mean().mean()) * 100})
    ddf = pd.DataFrame(rows)
    tot = ddf["mean"].sum()
    print(f"{'月':>3}{'分红贡献%':>11}{'占全年比重%':>13}{'样本年':>8}")
    for _, x in ddf.iterrows():
        print(f"{int(x['month']):>3}{x['mean']:>11.3f}{x['mean']/tot*100:>13.1f}{x['n']:>8}")
    print(f"{'合计':>3}{tot:>11.3f}{100.0:>13.1f}")
    out["div_by_month"] = ddf.to_dict("records")
    out["div_annual_total"] = tot

    # 每个红利指数各自的年度分红率与集中月
    print("\n--- 各红利指数: 年化分红率 / 分红最集中月 ---")
    for n in red:
        s = div[n].dropna()
        yrs = s.index.year.nunique()
        ann = (s.mean() * 12) * 100
        bym = s.groupby(s.index.month).sum() / yrs * 100
        top2 = bym.sort_values(ascending=False).head(2)
        out["div_detail"][n] = {"annual_div_pct": round(ann, 2),
                                "by_month": {str(k): round(v, 3) for k, v in bym.items()},
                                "top_months": {str(k): round(v, 3) for k, v in top2.items()}}
        print(f"{n:<12} 年化分红 {ann:>5.2f}%   集中月: "
              + ", ".join(f"{k}月 {v:.2f}%" for k, v in top2.items()))

    # ============ 2. 逐品种 12 月季节性(价格 & 全收益) ============
    for n in names:
        tpx, st_px = monthly_table(rpx[n], mkt)
        ttr, st_tr = monthly_table(rtr[n], mkt)
        # 分红贡献并入
        dz = div[n].groupby(div[n].index.month).mean() * 100
        tpx["div"] = tpx["month"].map(dz).round(3)
        ttr["div"] = ttr["month"].map(dz).round(3)
        out["items"][n] = {
            "group": meta[n]["group"], "code": meta[n]["code"],
            "px": {"months": tpx.round(3).to_dict("records"), "F": round(st_px["F"], 2), "p": round(st_px["p"], 4)},
            "tr": {"months": ttr.round(3).to_dict("records"), "F": round(st_tr["F"], 2), "p": round(st_tr["p"], 4)},
        }
        if n in red:
            print(fmt(tpx, f"{n} [价格指数]"))
            print(fmt(ttr, f"{n} [全收益指数]"))

    # ============ 3. 红利族平均: 价格 vs 全收益 对比 ============
    print("\n" + "=" * 96)
    print("【核心】红利族平均 12 月效应: 价格口径 vs 全收益口径")
    print("=" * 96)
    cmp_rows = []
    for m in range(1, 13):
        a = rpx[red]; b = rtr[red]
        am = a[a.index.month == m].mean().mean() * 100
        bm = b[b.index.month == m].mean().mean() * 100
        aw = (a[a.index.month == m] > 0).mean().mean() * 100
        bw = (b[b.index.month == m] > 0).mean().mean() * 100
        dv = ddf.loc[ddf["month"] == m, "mean"].iloc[0]
        cmp_rows.append({"month": m, "px_mean": round(am, 2), "tr_mean": round(bm, 2),
                         "div": round(dv, 3), "diff": round(bm - am, 2),
                         "px_win": round(aw, 1), "tr_win": round(bw, 1)})
    cdf = pd.DataFrame(cmp_rows)
    print(f"{'月':>3}{'价格均%':>9}{'全收益均%':>10}{'差(分红)%':>10}{'价格胜率%':>10}{'全收益胜率%':>11}")
    for _, x in cdf.iterrows():
        print(f"{int(x['month']):>3}{x['px_mean']:>9.2f}{x['tr_mean']:>10.2f}"
              f"{x['div']:>10.3f}{x['px_win']:>10.1f}{x['tr_win']:>11.1f}")
    out["red_avg"] = cdf.to_dict("records")

    # ============ 4. 相对基准的超额(去市场共性) ============
    print("\n" + "=" * 96)
    print("【核心】红利族相对全市场超额(去市场共性), 按价格/全收益口径")
    print("=" * 96)
    rows = []
    for m in range(1, 13):
        e_px, e_tr = [], []
        for n in red:
            s = rpx[n].dropna(); mk = mkt.reindex(s.index)
            x = (s - mk)[s.index.month == m]; e_px.append(x.mean() * 100)
            # 全收益口径的全市场基准用价格指数会偏, 改用全收益基准中位数
            mkt_tr = rtr[bench].median(axis=1)
            s2 = rtr[n].dropna(); mk2 = mkt_tr.reindex(s2.index)
            x2 = (s2 - mk2)[s2.index.month == m]; e_tr.append(x2.mean() * 100)
        rows.append({"month": m, "ex_px": round(float(np.mean(e_px)), 2),
                     "ex_tr": round(float(np.mean(e_tr)), 2)})
    edf = pd.DataFrame(rows)
    print(f"{'月':>3}{'超额(价格)%':>13}{'超额(全收益)%':>15}")
    for _, x in edf.iterrows():
        print(f"{int(x['month']):>3}{x['ex_px']:>13.2f}{x['ex_tr']:>15.2f}")
    out["red_excess"] = edf.to_dict("records")

    # ============ 5. 分段稳健性(中证红利) ============
    print("\n" + "=" * 96)
    print("【稳健性】中证红利 各月平均(价格口径) 分段对比")
    print("=" * 96)
    segs = [("2005-2014", 2005, 2014), ("2015-2026", 2015, 2026)]
    seg_rows = []
    for n in ["中证红利", "上证红利"]:
        s = rpx[n].dropna()
        row = {"name": n}
        for tag, lo, hi in segs:
            x = s[(s.index.year >= lo) & (s.index.year <= hi)]
            row[tag] = round(float(x.mean()) * 100 * 12, 2)   # 年化
            for m in [1, 6, 7, 12]:
                row[f"{tag}_{m}"] = round(float(x[x.index.month == m].mean()) * 100, 2)
        seg_rows.append(row)
    for r in seg_rows:
        print(f"{r['name']}: 年化 {r['2005-2014']}%({segs[0][0]}) -> {r['2015-2026']}%")
        for tag, _, _ in segs:
            print(f"    {tag}: 1月 {r[tag+'_1']:>6.2f}%  6月 {r[tag+'_6']:>6.2f}%  "
                  f"7月 {r[tag+'_7']:>6.2f}%  12月 {r[tag+'_12']:>6.2f}%")
    out["segments"] = seg_rows

    # ============ 6. 逐年 6 月 / 12 月表现 ============
    print("\n" + "=" * 96)
    print("【明细】中证红利 6月(价格) vs 6月(全收益) vs 12月 逐年")
    print("=" * 96)
    yr_rows = []
    for y in sorted(set(rpx.index.year)):
        r = {}
        for m in [6, 7]:
            p = rpx["中证红利"][(rpx.index.year == y) & (rpx.index.month == m)]
            t = rtr["中证红利"][(rtr.index.year == y) & (rtr.index.month == m)]
            if len(p):
                r[f"px{m}"] = round(float(p.iloc[0]) * 100, 2)
                r[f"tr{m}"] = round(float(t.iloc[0]) * 100, 2)
                r[f"div{m}"] = round(float(t.iloc[0] - p.iloc[0]) * 100, 2)
        if r:
            yr_rows.append({"year": y, **r})
    ydf = pd.DataFrame(yr_rows)
    print(f"{'年':>5}{'6月价格%':>10}{'6月全收益%':>12}{'6月分红%':>10}{'7月价格%':>10}{'7月分红%':>10}")
    for _, x in ydf.iterrows():
        print(f"{int(x['year']):>5}{x.get('px6',float('nan')):>10.2f}{x.get('tr6',float('nan')):>12.2f}"
              f"{x.get('div6',float('nan')):>10.2f}{x.get('px7',float('nan')):>10.2f}"
              f"{x.get('div7',float('nan')):>10.2f}")
    out["yearly_67"] = ydf.to_dict("records")

    with open(os.path.join(OUT, "dividend_stats.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, default=float)
    print("\n-> out/dividend_stats.json")


if __name__ == "__main__":
    main()
