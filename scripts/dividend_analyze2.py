# -*- coding: utf-8 -*-
"""
红利指数季节性研究 - 统计分析 v2
输入: out/dividend_raw.json (含 open/close 日线)
输出: out/div2.json

分析框架
--------
红利指数的"季节性"必须拆成三层, 否则会把除息当成亏损:

  ① 除息机械效应(伪季节性)
     6-7月是 A 股年报分红实施高峰, 除息日指数点位直接扣减
     证据 A: 全收益指数 - 价格指数 = 当月分红贡献, 集中在 5/6/7 月
     证据 B: 隔夜跳空(open_t/close_{t-1}-1) 在 6-7 月相对沪深300显著为负,
             而日内收益为正 -> 除息低开 + 当日填权
  ② 市场共性(大盘在跌, 与红利无关): 用沪深300全收益剥离
  ③ 真实相对强弱: 剩余部分

样本: 2005-02 ~ 2026-08 (月度); 日线 2005-01 ~ 2026-09-14
"""
import sys, os, json
import numpy as np
import pandas as pd
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")

START_M = "2005-01"       # 月度面板起点(基日次月起算收益)
START_D = "2005-01-01"    # 日线起点
CUR_YM = "2026-09"        # 不完整的当前月
RED = ["中证红利", "上证红利", "300红利", "国企红利", "央企红利", "红利低波", "红利低波100"]
BENCH_TR = "沪深300"


def load():
    with open(os.path.join(OUT, "dividend_raw.json"), encoding="utf-8") as f:
        return json.load(f)["items"]


def daily_df(rows):
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["d"], format="%Y%m%d")
    df = df.dropna(subset=["c"]).sort_values("date").reset_index(drop=True)
    df["o"] = pd.to_numeric(df["o"], errors="coerce")
    df["c"] = pd.to_numeric(df["c"], errors="coerce")
    return df


def month_close(df):
    d = df[df["date"] < pd.Timestamp("2026-09-01")]
    s = d.groupby(d["date"].dt.to_period("M"))["c"].last()
    return s[s.index >= pd.Period(START_M, "M")]


def stats_by_month(r):
    """r: 月收益 Series -> 12 行统计"""
    r = r.dropna()
    d = pd.DataFrame({"r": r.values, "month": r.index.month, "year": r.index.year})
    d["r_dm"] = d["r"] - d.groupby("year")["r"].transform("mean")
    rows = []
    for m in range(1, 13):
        x = d[d["month"] == m]
        n = len(x)
        if n < 5:
            continue
        sd, sdm = x["r"].std(), x["r_dm"].std()
        rows.append({
            "month": m, "n": int(n),
            "mean": float(x["r"].mean()) * 100,
            "median": float(x["r"].median()) * 100,
            "win": float((x["r"] > 0).mean()) * 100,
            "std": float(sd) * 100,
            "min": float(x["r"].min()) * 100, "max": float(x["r"].max()) * 100,
            "pos": int((x["r"] > 0).sum()), "neg": int((x["r"] <= 0).sum()),
            "mean_dm": float(x["r_dm"].mean()) * 100,
            "t": float(x["r_dm"].mean() / (sdm / np.sqrt(n))) if sdm > 0 else 0.0,
        })
    return pd.DataFrame(rows)


def main():
    items = load()
    daily, daily_tr, px, tr, meta = {}, {}, {}, {}, {}
    for it in items:
        df = daily_df(it["rows"])
        if it["kind"] == "px":
            daily[it["name"]] = df
        else:
            daily_tr[it["name"]] = df
        s = month_close(df)
        if len(s) < 60:
            continue
        (px if it["kind"] == "px" else tr)[it["name"]] = s
        meta[it["name"]] = {"group": it["group"], "code": it["code"]}

    PX, TR = pd.DataFrame(px), pd.DataFrame(tr)
    # 逐列收益, 保留 NaN(不因个别品种缺失而丢整月)
    RPX = PX.pct_change(fill_method=None)
    RTR = TR.pct_change(fill_method=None)
    RPX = RPX[RPX.index >= pd.Period(START_M, "M") + 1]
    RTR = RTR[RTR.index >= pd.Period(START_M, "M") + 1]
    DIV = RTR - RPX                       # 分红贡献

    print("=" * 100)
    print(f"样本: 月度 {RPX.index.min()} ~ {RPX.index.max()} ({len(RPX)} 个月) | "
          f"品种 {list(PX.columns)}")
    print("=" * 100)

    res = {"sample": {"monthly": f"{RPX.index.min()} ~ {RPX.index.max()}",
                      "n_months": int(len(RPX)), "n_items": int(PX.shape[1])}}

    # ---------- 1. 分红贡献的月份分布(全样本 + 分段) ----------
    print("\n【1】红利族 分红贡献(全收益-价格) 的月份分布  [单位 %]")
    segs = [("全样本", 2005, 2026), ("2006-2014", 2006, 2014),
            ("2015-2023", 2015, 2023), ("2024-2026", 2024, 2026)]
    res["div_by_month"] = {}
    hdr = f"{'月':>3}" + "".join(f"{s[0]:>13}" for s in segs)
    print(hdr)
    tot_all = None
    for m in range(1, 13):
        line = f"{m:>3}"
        for tag, lo, hi in segs:
            vals = []
            for n in RED:
                s = DIV[n].dropna()
                s = s[(s.index.month == m) & (s.index.year >= lo) & (s.index.year <= hi)]
                if len(s):
                    vals.append(s.mean() * 100)
            v = float(np.mean(vals)) if vals else 0.0
            line += f"{v:>13.3f}"
            res["div_by_month"].setdefault(tag, {})[str(m)] = round(v, 3)
        print(line)
    for tag, lo, hi in segs:
        t = sum(res["div_by_month"][tag].values())
        res["div_by_month"][tag]["annual"] = round(t, 3)
        print(f"  {tag} 全年合计 {t:.2f}%  6+7月占比 "
              f"{(res['div_by_month'][tag]['6']+res['div_by_month'][tag]['7'])/t*100:.1f}%")

    print("\n--- 各红利指数 年化分红率(全样本) ---")
    res["div_rate"] = {}
    for n in RED:
        s = DIV[n].dropna()
        ann = s.mean() * 12 * 100
        bym = s.groupby(s.index.month).mean() * 100
        res["div_rate"][n] = {"annual": round(float(ann), 2),
                              "jul_share": round(float((bym.get(6, 0) + bym.get(7, 0)) / bym.sum() * 100), 1)}
        print(f"  {n:<12} 年化 {ann:>5.2f}%   6+7月占全年分红 {res['div_rate'][n]['jul_share']:>5.1f}%")

    # ---------- 2. 价格 vs 全收益 的 12 月效应(红利族平均) ----------
    print("\n【2】红利族平均 12 月效应: 价格口径 vs 全收益口径")
    rows = []
    for m in range(1, 13):
        a = RPX[RED]; b = RTR[RED]
        am = float(np.nanmean(a[a.index.month == m].values)) * 100
        bm = float(np.nanmean(b[b.index.month == m].values)) * 100
        aw = float(np.nanmean((a[a.index.month == m] > 0).values)) * 100
        bw = float(np.nanmean((b[b.index.month == m] > 0).values)) * 100
        dv = res["div_by_month"]["全样本"][str(m)]
        rows.append({"month": m, "px": round(am, 2), "tr": round(bm, 2),
                     "div": round(dv, 3), "px_win": round(aw, 1), "tr_win": round(bw, 1)})
    t2 = pd.DataFrame(rows)
    print(f"{'月':>3}{'价格%':>9}{'全收益%':>10}{'分红%':>9}{'除息贡献占比':>13}{'价格胜率%':>10}{'全收益胜率%':>12}")
    for _, x in t2.iterrows():
        sh = (x["div"] / abs(x["px"]) * 100) if x["px"] < 0 else float("nan")
        print(f"{int(x['month']):>3}{x['px']:>9.2f}{x['tr']:>10.2f}{x['div']:>9.3f}"
              f"{(f'{sh:.0f}%' if x['px']<0 else '-'):>13}{x['px_win']:>10.1f}{x['tr_win']:>12.1f}")
    res["red_avg"] = t2.to_dict("records")

    # ---------- 3. 相对基准超额 ----------
    print("\n【3】红利族相对沪深300全收益 的超额(剔市场共性)")
    mk = RTR[BENCH_TR]
    rows = []
    for m in range(1, 13):
        ex = []
        for n in RED:
            s = RTR[n].dropna()
            e = (s - mk.reindex(s.index)).dropna()
            x = e[e.index.month == m]
            if len(x):
                ex.append(x.mean() * 100)
        rows.append({"month": m, "ex": round(float(np.mean(ex)), 2)})
    t3 = pd.DataFrame(rows)
    res["excess"] = t3.to_dict("records")
    print("  " + "  ".join(f"{int(r['month'])}月{r['ex']:+.2f}%" for _, r in t3.iterrows()))

    # ---------- 4. 6 月分解 ----------
    print("\n【4】6 月收益分解 (红利族平均, 全样本)")
    j = 6
    px6 = float(np.nanmean(RPX[RED][RPX.index.month == j].values)) * 100
    tr6 = float(np.nanmean(RTR[RED][RTR.index.month == j].values)) * 100
    mk6 = float(mk[mk.index.month == j].mean()) * 100
    mk_all = float(mk.mean()) * 100
    div6 = res["div_by_month"]["全样本"]["6"]
    res["decomp_jun"] = {
        "px": round(px6, 2), "tr": round(tr6, 2), "div": round(div6, 2),
        "bench_tr": round(mk6, 2), "bench_all": round(mk_all, 2),
        "excess": round(tr6 - mk6, 2), "bench_excess": round(mk6 - mk_all, 2)}
    print(f"  价格口径 6 月: {px6:+.2f}%")
    print(f"    = 全收益口径 {tr6:+.2f}%  -  分红 {div6:+.2f}%")
    print(f"  全收益 6 月 vs 沪深300全收益 6 月({mk6:+.2f}%) -> 超额 {tr6-mk6:+.2f}%")
    print(f"  沪深300 6 月({mk6:+.2f}%) vs 全年月度均值({mk_all:+.2f}%) -> 市场共性 {mk6-mk_all:+.2f}%")

    # ---------- 5. 隔夜跳空 vs 日内收益(除息直接证据) ----------
    print("\n【5】隔夜跳空检验: open_t/close_{t-1}-1 vs 日内 close_t/open_t-1")
    print("     除息会让指数在除息日'低开', 故红利相对沪深300 的隔夜差 = 除息强度")
    bench = daily[BENCH_TR].set_index("date")
    ob = bench["o"] / bench["c"].shift(1) - 1
    ib = bench["c"] / bench["o"] - 1
    on_rows, in_rows = [], []
    for m in range(1, 13):
        onv, inv = [], []
        for n in RED:
            d = daily[n].set_index("date")
            o = d["o"] / d["c"].shift(1) - 1
            i = d["c"] / d["o"] - 1
            df = pd.DataFrame({"on": o, "in": i, "bon": ob, "bin": ib}).dropna()
            df = df[df.index >= pd.Timestamp(START_D)]
            x = df[df.index.month == m]
            if len(x) > 200:
                onv.append((x["on"] - x["bon"]).mean() * 100 * 21)   # 月化(约21个交易日)
                inv.append((x["in"] - x["bin"]).mean() * 100 * 21)
        on_rows.append({"month": m,
                        "on": round(float(np.mean(onv)), 2) if onv else 0.0,
                        "in": round(float(np.mean(inv)), 2) if inv else 0.0})
    t5 = pd.DataFrame(on_rows)
    res["gap"] = t5.to_dict("records")
    print(f"{'月':>3}{'隔夜超额(月化)%':>17}{'日内超额(月化)%':>17}{'合计%':>9}")
    for _, x in t5.iterrows():
        print(f"{int(x['month']):>3}{x['on']:>17.2f}{x['in']:>17.2f}{x['on']+x['in']:>9.2f}")
    jun = t5[t5["month"] == 6].iloc[0]
    print(f"\n  * 6月: 隔夜超额 {jun['on']:+.2f}% 日内超额 {jun['in']:+.2f}%"
          f"  -> 除息低开后当日被'填权'买回")

    # ---------- 6. 各指数独立检验(价格口径 12 月) ----------
    print("\n【6】各红利指数 价格口径 12 月效应速览")
    res["items"] = {}
    for n in list(PX.columns):
        if n not in RPX.columns:
            continue
        t = stats_by_month(RPX[n])
        tt = stats_by_month(RTR[n]) if n in RTR.columns else None
        dz = DIV[n].groupby(DIV[n].index.month).mean() * 100
        t["div"] = t["month"].map(dz).round(3)
        res["items"][n] = {"group": meta[n]["group"], "px": t.round(3).to_dict("records"),
                           "tr": (tt.round(3).to_dict("records") if tt is not None else None)}
        if n in RED:
            s = " | ".join(f"{int(r['month'])}月{r['mean']:+.1f}({r['win']:.0f}%)" for _, r in t.iterrows())
            print(f"  {n:<10} {s}")

    # ---------- 7. 逐年 6 月 & 分红 ----------
    print("\n【7】中证红利 逐年 6 月 & 分红贡献")
    yr = []
    for y in sorted(set(RPX.index.year)):
        p = RPX["中证红利"][(RPX.index.year == y) & (RPX.index.month == 6)]
        t_ = RTR["中证红利"][(RTR.index.year == y) & (RTR.index.month == 6)]
        if len(p) and len(t_):
            yr.append({"year": int(y), "px": round(float(p.iloc[0]) * 100, 2),
                       "tr": round(float(t_.iloc[0]) * 100, 2),
                       "div": round(float(t_.iloc[0] - p.iloc[0]) * 100, 2)})
    yd = pd.DataFrame(yr)
    res["jun_yearly"] = yd.to_dict("records")
    print("  " + " ".join(f"{int(r['year'])}:{r['px']:+.0f}/{r['div']:.1f}" for _, r in yd.iterrows()))
    print("  (格式: 年份:6月价格收益%/当月分红%)")
    n_neg = int((yd["px"] < 0).sum())
    print(f"  6月价格下跌年数 {n_neg}/{len(yd)} ({n_neg/len(yd)*100:.0f}%), "
          f"其中分红>1%的年份 {int((yd[yd['px']<0]['div']>1).sum())} 年")

    # ---------- 8. 分红落袋的日历分布(日度, 按旬) ----------
    print("\n【8】分红落袋的日历分布(日度全收益-价格, 按旬累计, 单位 %)")
    ddiv = {}
    for n in RED:
        if n in daily and n in daily_tr:
            a = daily[n].set_index("date")["c"]
            b = daily_tr[n].set_index("date")["c"]
            s = (b.pct_change(fill_method=None) - a.pct_change(fill_method=None)).dropna()
            s = s[s.index >= pd.Timestamp(START_D)]
            ddiv[n] = s

    def xun_of(day):
        return 1 if day <= 10 else (2 if day <= 20 else 3)

    cell = {}
    for m in range(1, 13):
        for k in (1, 2, 3):
            per_year = []
            yrs = sorted({d.year for s in ddiv.values() for d in s.index if d.month == m})
            for y in yrs:
                vs = []
                for n, s in ddiv.items():
                    x = s[(s.index.year == y) & (s.index.month == m) &
                          (s.index.day.map(xun_of) == k)]
                    if len(x):
                        vs.append(float(x.sum()) * 100)
                if vs:
                    per_year.append(np.mean(vs))
            cell[(m, k)] = float(np.mean(per_year)) if per_year else 0.0
    res["div_by_xun"] = {f"{m}-{k}": round(v, 3) for (m, k), v in cell.items()}
    print(f"{'月':>3}{'上旬(1-10)':>13}{'中旬(11-20)':>14}{'下旬(21-末)':>14}{'月合计':>10}")
    for m in range(1, 13):
        a, b, c = cell[(m, 1)], cell[(m, 2)], cell[(m, 3)]
        print(f"{m:>3}{a:>13.3f}{b:>14.3f}{c:>14.3f}{a+b+c:>10.3f}")
    top = sorted(cell.items(), key=lambda kv: -kv[1])[:6]
    print("  除息最密集的时段: " + ", ".join(f"{m}月{'上中下'[k-1]}旬 {v:.2f}%" for (m, k), v in top))

    # ---------- 9. 6月内路径(旬) ----------
    print("\n【9】6 月内路径: 各旬收益(价格 vs 全收益)")
    rows9 = []
    for k in (1, 2, 3):
        pv, tv = [], []
        for n in RED:
            a = daily[n].set_index("date")["c"].pct_change(fill_method=None).dropna()
            b = daily_tr[n].set_index("date")["c"].pct_change(fill_method=None).dropna()
            for s, box in ((a, pv), (b, tv)):
                x = s[(s.index.month == 6) & (s.index.day.map(xun_of) == k)]
                yrs = sorted(set(x.index.year))
                per = [float((1 + x[x.index.year == y]).prod() - 1) * 100 for y in yrs
                       if len(x[x.index.year == y]) > 0]
                if per:
                    box.append(np.mean(per))
        rows9.append({"xun": k, "px": round(float(np.mean(pv)), 2), "tr": round(float(np.mean(tv)), 2)})
    res["jun_path"] = rows9
    print(f"{'旬':>8}{'价格%':>10}{'全收益%':>11}{'差(分红)%':>11}")
    for r in rows9:
        print(f"{'上中下'[r['xun']-1]+'旬':>8}{r['px']:>10.2f}{r['tr']:>11.2f}{r['tr']-r['px']:>11.2f}")

    with open(os.path.join(OUT, "div2.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, default=float)
    print("\n-> out/div2.json")


if __name__ == "__main__":
    main()
