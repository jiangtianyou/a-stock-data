# -*- coding: utf-8 -*-
"""
9-10月专题 - 补充分析
输入: out/oct_raw.json
输出: out/oct_extra.json

1. 牛熊环境分组 : 按「当年截至8月底累计涨幅」把年份分档, 看 9/10 月在各环境下的表现
2. 风格切换     : 国庆长假前后, 小盘成长 vs 大盘价值 的相对收益
3. 长假日历明细 : 节前1日 / 节后1日 / 节后3日 逐年结果 + 稳定性
4. 2026 当前位置
"""
import sys, os, json
import numpy as np
import pandas as pd
from scipy import stats

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")
END_YM = "2026-08"
MAIN = "上证指数"

GROWTH = ["创业板指", "中证1000", "中证500"]
VALUE = ["上证50", "中证红利", "沪深300"]


def build(rows):
    d = pd.DataFrame(rows)
    d["d"] = pd.to_datetime(d["d"])
    d = d.sort_values("d").reset_index(drop=True)
    d["year"] = d["d"].dt.year
    d["month"] = d["d"].dt.month
    d["ym"] = d["d"].dt.strftime("%Y-%m")
    return d


def monthly(d):
    last = d.groupby("ym").last().reset_index()
    last["ret"] = last["c"].pct_change()
    last["year"] = last["ym"].str[:4].astype(int)
    last["month"] = last["ym"].str[5:7].astype(int)
    return last.dropna(subset=["ret"]).reset_index(drop=True)


def close_at(df, dt):
    """df 中 <= dt 的最后一个收盘"""
    sub = df[df["d"] <= dt]
    return float(sub["c"].iloc[-1]) if len(sub) else None


def find_holidays(d):
    res = []
    for y in sorted(set(d["year"])):
        oct_ = d[(d["year"] == y) & (d["month"] == 10)]
        sep = d[(d["year"] == y) & (d["month"] == 9)]
        if len(oct_) == 0 or len(sep) == 0:
            continue
        i_first = int(oct_.index[0]); i_last = i_first - 1
        if i_last < 0:
            continue
        if (d.loc[i_first, "d"] - d.loc[i_last, "d"]).days < 5:
            continue
        res.append((y, i_last, i_first))
    return res


def main():
    raw = json.load(open(os.path.join(OUT, "oct_raw.json"), encoding="utf-8"))
    dfs = {it["name"]: build(it["rows"]) for it in raw["items"]}
    d = dfs[MAIN]
    ms = monthly(d)
    ms = ms[(ms["year"] >= 1997) & (ms["ym"] <= END_YM)].reset_index(drop=True)

    out = {"fetched_at": raw["fetched_at"]}

    # ---------------- 1 牛熊环境分组 ----------------
    env = {"强势(1-8月>10%)": [], "震荡(-10%~10%)": [], "弱势(<-10%)": []}
    rows = []
    for y in sorted(set(ms["year"])):
        ytd = ms[(ms["year"] == y) & (ms["month"] <= 8)]
        if len(ytd) < 8:
            continue
        cum = float((1 + ytd["ret"]).prod() - 1)
        a = ms[(ms["year"] == y) & (ms["month"] == 9)]
        b = ms[(ms["year"] == y) & (ms["month"] == 10)]
        if not len(a) or not len(b):
            continue
        sa, sb = float(a["ret"].iloc[0]), float(b["ret"].iloc[0])
        tag = "强势(1-8月>10%)" if cum > 0.10 else ("弱势(<-10%)" if cum < -0.10 else "震荡(-10%~10%)")
        env[tag].append((sa, sb))
        rows.append({"year": int(y), "ytd8": round(cum * 100, 1),
                     "sep": round(sa * 100, 2), "oct": round(sb * 100, 2),
                     "sum": round((sa + sb) * 100, 2), "env": tag})
    envout = {}
    for k, v in env.items():
        if not v:
            continue
        sa = np.array([x[0] for x in v]); sb = np.array([x[1] for x in v])
        ss = sa + sb
        envout[k] = {
            "n": len(v),
            "sep_mean": round(float(sa.mean()) * 100, 2), "sep_win": round(float((sa > 0).mean()) * 100, 1),
            "oct_mean": round(float(sb.mean()) * 100, 2), "oct_win": round(float((sb > 0).mean()) * 100, 1),
            "sum_mean": round(float(ss.mean()) * 100, 2), "sum_win": round(float((ss > 0).mean()) * 100, 1),
            "sum_median": round(float(np.median(ss)) * 100, 2),
        }
    out["env"] = envout
    out["env_rows"] = rows

    # ---------------- 2 风格切换 ----------------
    hol = find_holidays(d)
    st = {"pre5": [], "post5": [], "post20": []}
    st_detail = []
    for (y, i0, i1) in hol:
        if y < 2000 or i0 - 5 < 0 or i1 + 20 >= len(d):
            continue
        dt0 = d.loc[i0, "d"]; dt1 = d.loc[i1, "d"]
        g_pre, v_pre, g_post, v_post, g_p20, v_p20 = [], [], [], [], [], []
        for n in GROWTH:
            dd = dfs[n]
            c0 = close_at(dd, dt0); c1 = close_at(dd, dt1)
            pre = close_at(dd, d.loc[i0 - 5, "d"]); post = close_at(dd, d.loc[i1 + 4, "d"])
            p20 = close_at(dd, d.loc[i1 + 19, "d"])
            if None in (c0, c1, pre, post, p20):
                continue
            g_pre.append(c0 / pre - 1); g_post.append(post / c0 - 1); g_p20.append(p20 / c0 - 1)
        for n in VALUE:
            dd = dfs[n]
            c0 = close_at(dd, dt0); c1 = close_at(dd, dt1)
            pre = close_at(dd, d.loc[i0 - 5, "d"]); post = close_at(dd, d.loc[i1 + 4, "d"])
            p20 = close_at(dd, d.loc[i1 + 19, "d"])
            if None in (c0, c1, pre, post, p20):
                continue
            v_pre.append(c0 / pre - 1); v_post.append(post / c0 - 1); v_p20.append(p20 / c0 - 1)
        if not g_pre or not v_pre:
            continue
        a, b, c = np.mean(g_pre) - np.mean(v_pre), np.mean(g_post) - np.mean(v_post), np.mean(g_p20) - np.mean(v_p20)
        st["pre5"].append(a); st["post5"].append(b); st["post20"].append(c)
        st_detail.append({"year": y, "pre5_gs": round(float(a) * 100, 2),
                          "post5_gs": round(float(b) * 100, 2), "post20_gs": round(float(c) * 100, 2)})

    style = {}
    for k, v in st.items():
        v = np.array(v)
        if len(v) == 0:
            continue
        t, p = stats.ttest_1samp(v, 0.0) if len(v) > 2 else (0.0, 1.0)
        style[k] = {"n": len(v), "mean": round(float(v.mean()) * 100, 2),
                    "median": round(float(np.median(v)) * 100, 2),
                    "win": round(float((v > 0).mean()) * 100, 1),
                    "t": round(float(t), 2), "p": round(float(p), 4)}
    out["style"] = style
    out["style_detail"] = st_detail
    out["style_def"] = {"成长": GROWTH, "价值": VALUE}

    # ---------------- 3 长假逐年明细 (2000起) ----------------
    c = d["c"].values.astype(float)
    det = []
    for (y, i0, i1) in hol:
        if y < 2000 or i0 - 10 < 0 or i1 + 5 >= len(c):
            continue
        det.append({"year": y,
                    "pre10": round((c[i0] / c[i0 - 10] - 1) * 100, 2),
                    "pre1": round((c[i0] / c[i0 - 1] - 1) * 100, 2),
                    "post1": round((c[i1] / c[i0] - 1) * 100, 2),
                    "post3": round((c[i1 + 2] / c[i0] - 1) * 100, 2),
                    "post5": round((c[i1 + 4] / c[i0] - 1) * 100, 2)})
    out["holiday_yearly"] = det
    p1 = [x["post1"] for x in det]
    out["post1_stability"] = {"n": len(p1), "up_years": [x["year"] for x in det if x["post1"] > 0],
                              "dn_years": [x["year"] for x in det if x["post1"] <= 0]}

    # ---------------- 4 2026 当前位置 ----------------
    cur = {}
    for n, dd in dfs.items():
        last = dd.iloc[-1]
        ytd_start = dd[(dd["year"] == 2026) & (dd["month"] == 1)]
        base = float(ytd_start["c"].iloc[0]) / (1 + 0) if len(ytd_start) else None
        aug31 = close_at(dd, pd.Timestamp("2026-08-31"))
        jul31 = close_at(dd, pd.Timestamp("2026-07-31"))
        cur[n] = {"last_day": str(last["d"].date()), "last": round(float(last["c"]), 2),
                  "aug31": round(aug31, 2) if aug31 else None,
                  "sep_mtd": round((float(last["c"]) / aug31 - 1) * 100, 2) if aug31 else None,
                  "jul_mtd": round((aug31 / jul31 - 1) * 100, 2) if (aug31 and jul31) else None}
    out["current_2026"] = cur

    with open(os.path.join(OUT, "oct_extra.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)

    print("=== 1. 牛熊环境分组 (1997起, 按当年1-8月累计涨幅) ===")
    print(f"{'环境':<22}{'n':>4}{'9月均%':>9}{'9月胜%':>8}{'10月均%':>9}{'10月胜%':>9}{'9+10均%':>9}{'9+10胜%':>9}{'9+10中位':>10}")
    for k, v in envout.items():
        print(f"{k:<22}{v['n']:>4}{v['sep_mean']:>9.2f}{v['sep_win']:>8.1f}{v['oct_mean']:>9.2f}"
              f"{v['oct_win']:>9.1f}{v['sum_mean']:>9.2f}{v['sum_win']:>9.1f}{v['sum_median']:>10.2f}")

    print("\n=== 2. 风格切换: 成长(创业板/中证1000/中证500) - 价值(上证50/中证红利/沪深300) ===")
    print(f"{'窗口':<10}{'n':>4}{'均值%':>9}{'中位%':>9}{'成长占优%':>11}{'t':>7}{'p':>8}")
    for k, v in style.items():
        print(f"{k:<10}{v['n']:>4}{v['mean']:>9.2f}{v['median']:>9.2f}{v['win']:>11.1f}{v['t']:>7.2f}{v['p']:>8.3f}")

    print("\n=== 3. 国庆逐年明细 (2000起) ===")
    print(f"{'年':<6}{'节前10日':>10}{'节前1日':>9}{'节后1日':>9}{'节后3日':>9}{'节后5日':>9}")
    for x in det:
        print(f"{x['year']:<6}{x['pre10']:>10.2f}{x['pre1']:>9.2f}{x['post1']:>9.2f}{x['post3']:>9.2f}{x['post5']:>9.2f}")
    print(f"  节后1日上涨年份 {out['post1_stability']['up_years']}")
    print(f"  节后1日下跌年份 {out['post1_stability']['dn_years']}")

    print("\n=== 4. 2026 当前位置 ===")
    print(f"{'品种':<10}{'最新':>10}{'8/31':>10}{'9月MTD%':>10}{'8月%':>9}")
    for n, v in cur.items():
        print(f"{n:<10}{v['last']:>10.2f}{v['aug31']:>10.2f}{v['sep_mtd']:>10.2f}{v['jul_mtd']:>9.2f}")

    print("\n-> out/oct_extra.json")


if __name__ == "__main__":
    main()
