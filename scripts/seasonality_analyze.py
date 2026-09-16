# -*- coding: utf-8 -*-
"""
A股季节性研究 - 统计分析 v2
输入: out/seasonality_raw.json
输出: out/seasonality_stats.json

方法
----
样本: 2000-01 起 (避开 1990s 无涨跌停/T+0 的极端期), 剔除当前不完整月
收益: 月末收盘价环比

三层口径, 逐层剥离干扰:
  L1 mean   : 原始月度收益均值      -> 含年度整体涨跌 + 市场共性
  L2 mean_dm: 去年度效应(减该年均值) -> 剥离牛熊整体涨跌
  L3 mean_re: 去市场共性(减当月横截面中位数) -> 剥离"这个月大盘整体在涨"
  mean_w    : 对品种收益序列做 winsorize(2%/98%) 后再按月平均 -> 抗极端月

季节性强度:
  F   : 单因素方差分析(因子=月份)的 F 值
  amp : 12个月效应的标准差 (季节性振幅)
  主排序用 t_w (winsorize 后, 去年度效应的 t 值) — 兼顾收益幅度与稳定性
"""
import sys, os, json
import numpy as np
import pandas as pd
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")

START = "2000-01"     # 样本起点
MIN_N = 10            # 单月最少样本年数
RANK_MIN_N = 12       # 进入主排名的最低样本年数


def load():
    with open(os.path.join(OUT, "seasonality_raw.json"), encoding="utf-8") as f:
        return json.load(f)


def build_panel(raw):
    cur_ym = pd.Timestamp.today().strftime("%Y-%m")
    series, meta = {}, {}
    for it in raw["items"]:
        df = pd.DataFrame(it["rows"])
        df["ym"] = df["d"].str[:7]
        df = df[(df["ym"] < cur_ym) & (df["ym"] >= START)]
        if len(df) < MIN_N * 6:
            continue
        df = df.sort_values("d").reset_index(drop=True)
        df["ret"] = df["c"].pct_change()
        df = df.dropna(subset=["ret"])
        if len(df) < MIN_N * 6:
            continue
        series[it["name"]] = pd.Series(df["ret"].values, index=df["ym"].values, name=it["name"])
        meta[it["name"]] = {"group": it["group"], "secid": it["secid"],
                            "start": df["ym"].iloc[0], "end": df["ym"].iloc[-1],
                            "n_months": int(len(df))}
    panel = pd.DataFrame(series)
    panel.index = pd.PeriodIndex(panel.index, freq="M")
    return panel, meta


def winsorize(s, lo=0.02, hi=0.98):
    a, b = s.quantile(lo), s.quantile(hi)
    return s.clip(a, b)


def analyze():
    raw = load()
    panel, meta = build_panel(raw)
    pw = panel.apply(winsorize)
    print("品种数: %d | 月份数: %d | 区间: %s -> %s"
          % (panel.shape[1], panel.shape[0], panel.index.min(), panel.index.max()))

    idx = panel.index
    months, years = idx.month, idx.year
    mkt = panel.median(axis=1)                      # 市场共性(横截面中位数)
    mkt_w = pw.median(axis=1)

    # ============ 全市场共性月份效应 ============
    mdf = pd.DataFrame({"ret": mkt.values, "ret_w": mkt_w.values, "month": months, "year": years})
    mdf["ret_dm"] = mdf["ret_w"] - mdf.groupby("year")["ret_w"].transform("mean")
    common = {}
    for m in range(1, 13):
        s = mdf[mdf["month"] == m]
        sdm = s["ret_dm"]
        common[str(m)] = {
            "n": int(len(s)),
            "mean": round(float(s["ret"].mean()) * 100, 2),
            "mean_w": round(float(s["ret_w"].mean()) * 100, 2),
            "median": round(float(s["ret"].median()) * 100, 2),
            "mean_dm": round(float(sdm.mean()) * 100, 2),
            "std": round(float(s["ret"].std()) * 100, 2),
            "win": round(float((s["ret"] > 0).mean()) * 100, 1),
            "t": round(float(sdm.mean() / (sdm.std() / np.sqrt(len(s)))), 2) if sdm.std() > 0 else 0.0,
        }

    items = []
    for name in panel.columns:
        s, sw = panel[name].dropna(), pw[name].reindex(panel[name].dropna().index)
        if len(s) < MIN_N * 6:
            continue
        rel = s - mkt.reindex(s.index)
        d = pd.DataFrame({"ret": s.values, "ret_w": sw.values, "rel": rel.values,
                          "month": s.index.month, "year": s.index.year})
        d["ret_dm"] = d["ret_w"] - d.groupby("year")["ret_w"].transform("mean")

        rows = []
        for m in range(1, 13):
            x = d[d["month"] == m]
            n = len(x)
            if n < 5:
                continue
            sd, sdm, sdr = x["ret"].std(), x["ret_dm"].std(), x["rel"].std()
            rows.append({
                "month": m, "n": int(n),
                "mean": round(float(x["ret"].mean()) * 100, 2),
                "mean_w": round(float(x["ret_w"].mean()) * 100, 2),
                "median": round(float(x["ret"].median()) * 100, 2),
                "std": round(float(sd) * 100, 2),
                "win": round(float((x["ret"] > 0).mean()) * 100, 1),
                "t": round(float(x["ret"].mean() / (sd / np.sqrt(n))), 2) if sd > 0 else 0.0,
                "mean_dm": round(float(x["ret_dm"].mean()) * 100, 2),
                "t_dm": round(float(x["ret_dm"].mean() / (sdm / np.sqrt(n))), 2) if sdm > 0 else 0.0,
                "mean_re": round(float(x["rel"].mean()) * 100, 2),
                "t_re": round(float(x["rel"].mean() / (sdr / np.sqrt(n))), 2) if sdr > 0 else 0.0,
                "min": round(float(x["ret"].min()) * 100, 1),
                "max": round(float(x["ret"].max()) * 100, 1),
            })
        if len(rows) < 12:
            continue
        md = pd.DataFrame(rows)

        groups = [d.loc[d["month"] == m, "ret_dm"].values for m in range(1, 13)]
        groups = [g for g in groups if len(g) >= 5]
        F, p = stats.f_oneway(*groups)

        b = md.loc[md["t_dm"].idxmax()]     # 最强月(按稳健t)
        w = md.loc[md["t_dm"].idxmin()]     # 最弱月
        b_raw = md.loc[md["mean"].idxmax()]

        # 稳健性: 两段
        seg = {}
        for tag, lo, hi in [("seg1", 2000, 2012), ("seg2", 2013, 2025)]:
            sub = d[(d["year"] >= lo) & (d["year"] <= hi)]
            x = sub[sub["month"] == int(b["month"])]
            seg[tag] = round(float(x["ret_dm"].mean()) * 100, 2) if len(x) >= 5 else None
        stable = (seg["seg1"] is not None and seg["seg2"] is not None and
                  ((seg["seg1"] > 0 and seg["seg2"] > 0) or (seg["seg1"] < 0 and seg["seg2"] < 0)))

        items.append({
            "name": name, **meta[name],
            "F": round(float(F), 2), "p": round(float(p), 4), "amp": round(float(md["mean_dm"].std()), 2),
            "best_month": int(b["month"]), "best_t": float(b["t_dm"]),
            "best_mean_dm": float(b["mean_dm"]), "best_mean": float(b["mean"]),
            "best_median": float(b["median"]), "best_win": float(b["win"]),
            "best_n": int(b["n"]), "best_min": float(b["min"]), "best_max": float(b["max"]),
            "best_mean_re": float(b["mean_re"]), "best_t_re": float(b["t_re"]),
            "worst_month": int(w["month"]), "worst_t": float(w["t_dm"]),
            "worst_mean_dm": float(w["mean_dm"]), "worst_mean": float(w["mean"]),
            "worst_median": float(w["median"]), "worst_win": float(w["win"]), "worst_n": int(w["n"]),
            "raw_best_month": int(b_raw["month"]), "raw_best_mean": float(b_raw["mean"]),
            "seg1": seg["seg1"], "seg2": seg["seg2"], "stable": bool(stable),
            "months": rows,
        })

    def rk(cands, key, rev=True):
        return sorted(cands, key=lambda x: x[key], reverse=rev)

    strong = [x for x in items if x["best_n"] >= RANK_MIN_N]

    # 最强月分布: 有多少品种把某个月选为最强月
    dist = {}
    for x in items:
        dist[str(x["best_month"])] = dist.get(str(x["best_month"]), 0) + 1
    # 2月效应在大/小盘上的分层
    def feb_rank(groups):
        out = []
        for x in items:
            if x["group"] not in groups:
                continue
            f = [m for m in x["months"] if m["month"] == 2]
            if not f or f[0]["n"] < RANK_MIN_N:
                continue
            f = f[0]
            out.append({"name": x["name"], "group": x["group"], "n": f["n"],
                        "mean": f["mean"], "mean_dm": f["mean_dm"], "mean_re": f["mean_re"],
                        "median": f["median"], "win": f["win"], "t_dm": f["t_dm"], "t_re": f["t_re"],
                        "min": f["min"], "max": f["max"]})
        return sorted(out, key=lambda z: z["t_dm"], reverse=True)

    res = {
        "fetched_at": raw["fetched_at"], "start": START,
        "sample": {"period": f"{panel.index.min()} ~ {panel.index.max()}",
                   "n_items": int(panel.shape[1]), "n_months": int(panel.shape[0])},
        "market_common": common,
        "items": items,
        "month_dist": dist,
        "feb_all": feb_rank({"宽基", "风格", "行业", "细分", "主题"}),
        "rank_pos": [x["name"] for x in rk(strong, "best_t")[:25]],
        "rank_neg": [x["name"] for x in rk(strong, "worst_t", False)[:25]],
        "rank_F": [x["name"] for x in rk(strong, "F")[:25]],
        "rank_by_group": {g: [x["name"] for x in rk([i for i in strong if i["group"] == g], "best_t")[:8]]
                          for g in sorted({i["group"] for i in strong})},
    }
    with open(os.path.join(OUT, "seasonality_stats.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False)

    # ---------- 速览 ----------
    print("\n=== 全市场共性月份效应 (横截面中位数, 去年度效应) ===")
    print(f"{'月份':<6}{'均值%':>8}{'中位%':>8}{'去年度%':>9}{'胜率%':>8}{'t':>7}{'样本':>6}")
    for m in range(1, 13):
        c = common[str(m)]
        print(f"{m:>2}月  {c['mean']:>8.2f}{c['median']:>8.2f}{c['mean_dm']:>9.2f}{c['win']:>8.1f}{c['t']:>7.2f}{c['n']:>6}")

    print("\n=== 季节性最强 TOP20 (按稳健 t 值) ===")
    print(f"{'品种':<12}{'组':<5}{'月':>4}{'去年度%':>9}{'去共性%':>9}{'原始%':>8}{'中位%':>8}{'胜率%':>7}{'t':>6}{'年数':>5}")
    for x in rk(strong, "best_t")[:20]:
        print(f"{x['name']:<12}{x['group']:<5}{x['best_month']:>3}月{x['best_mean_dm']:>9.2f}{x['best_mean_re']:>9.2f}"
              f"{x['best_mean']:>8.2f}{x['best_median']:>8.2f}{x['best_win']:>7.1f}{x['best_t']:>6.2f}{x['best_n']:>5}")

    print("\n=== 最强月分布 (多少个品种把该月选为最强月) ===")
    for m in range(1, 13):
        c = dist.get(str(m), 0)
        print(f"  {m:>2}月 : {'█' * c} {c}")

    print("\n=== 2月效应横截面 (样本>=12年, 按 t 值) ===")
    print(f"{'品种':<12}{'组':<5}{'年数':>5}{'去年度%':>9}{'去共性%':>9}{'中位%':>8}{'胜率%':>7}{'t':>6}{'最差年%':>8}")
    for x in res["feb_all"][:22]:
        print(f"{x['name']:<12}{x['group']:<5}{x['n']:>5}{x['mean_dm']:>9.2f}{x['mean_re']:>9.2f}"
              f"{x['median']:>8.2f}{x['win']:>7.1f}{x['t_dm']:>6.2f}{x['min']:>8.1f}")

    print("\n=== 最强负季节性 TOP15 (最差月) ===")
    for x in rk(strong, "worst_t", False)[:15]:
        print(f"{x['name']:<12}{x['group']:<5}{x['worst_month']:>3}月{x['worst_mean_dm']:>8.2f}{x['worst_mean']:>8.2f}"
              f"{x['worst_median']:>8.2f}{x['worst_win']:>7.1f}{x['worst_t']:>6.2f}{x['worst_n']:>5}")

    print("\n=== 季节性强度 TOP15 (按月份效应 F 值) ===")
    for x in rk(strong, "F")[:15]:
        print(f"{x['name']:<12}{x['group']:<5}F={x['F']:>5.2f} p={x['p']:>6.3f} 振幅={x['amp']:>6.2f}%  "
              f"最强月={x['best_month']:>2}月 样本={x['best_n']}")

    print("\n-> out/seasonality_stats.json")


if __name__ == "__main__":
    analyze()
