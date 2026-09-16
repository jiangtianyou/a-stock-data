import json, os, math, statistics as st

D = r"C:\Users\Administrator\.workbuddy\projects\d-Desktop-Playground-a-stock-data\f4800af3-610a-497f-a9b6-fb135319d10e\tool-results"
FILES = {
    "688981": "mcp-tdx-connector-tdx_kline-1789368452656-d2cc6d.txt",
    "688256": "mcp-tdx-connector-tdx_kline-1789368471326-8b9b18.txt",
    "688041": "mcp-tdx-connector-tdx_kline-1789368486947-8379df.txt",
    "000685": "mcp-tdx-connector-tdx_kline-1789368485688-da60c7.txt",
}
NAMES = {"688981": "中芯国际", "688256": "寒武纪", "688041": "海光信息", "000685": "科创芯片指数"}

def parse(path):
    raw = open(path, encoding="utf-8", errors="ignore").read()
    i = raw.find("{")
    obj, _ = json.JSONDecoder().raw_decode(raw[i:])
    return [(r["Data"], float(r["Close"]), float(r["High"]), float(r["Low"]), float(r["Amount"])) for r in obj["Rows"]]

series = {}
for code, fn in FILES.items():
    rows = parse(os.path.join(D, fn))
    series[code] = {d: (c, h, l, a) for d, c, h, l, a in rows}
    series[code + "_list"] = rows

# 统一交易日历（以指数为准）
cal = [r[0] for r in series["000685_list"]]
cal = [d for d in cal if d >= "20251231"]
BASE = cal[0]
print("基准日:", BASE, " 结束日:", cal[-1], " 交易日数:", len(cal))

STK = ["688981", "688256", "688041"]
close = {k: [series[k][d][0] for d in cal] for k in STK + ["000685"]}
base = {k: close[k][0] for k in close}

# --- 组合：等权买入持有（期初各 1/3 资金）---
W = 1.0 / 3
port_bh = []
for i in range(len(cal)):
    v = sum(W * (close[k][i] / base[k]) for k in STK)   # 归一化净值
    port_bh.append(v)
# 组合：等权每日再平衡（日均收益算术平均）
rets = {k: [close[k][i] / close[k][i-1] - 1 for i in range(1, len(cal))] for k in STK + ["000685"]}
port_dr = [1.0]
for i in range(len(rets["688981"])):
    r = sum(W * rets[k][i] for k in STK)
    port_dr.append(port_dr[-1] * (1 + r))
idx_norm = [c / base["000685"] for c in close["000685"]]

def metrics(norm, label, rf=0.015):
    n = len(norm)
    tot = norm[-1] / norm[0] - 1
    yrs = (n - 1) / 244.0
    cagr = (norm[-1] / norm[0]) ** (1 / yrs) - 1
    r = [norm[i] / norm[i-1] - 1 for i in range(1, n)]
    vol = st.pstdev(r) * math.sqrt(244)
    peak = norm[0]; mdd = 0; mdd_i = 0; peak_i = 0
    dd = []
    for i, v in enumerate(norm):
        if v > peak: peak = v; peak_i = i
        d = v / peak - 1
        dd.append(d)
        if d < mdd: mdd = d; mdd_i = i
    sharpe = (cagr - rf) / vol if vol else 0
    calmar = cagr / abs(mdd) if mdd else 0
    up = sum(1 for x in r if x > 0)
    return dict(label=label, tot=tot*100, cagr=cagr*100, vol=vol*100, mdd=mdd*100,
                mdd_date=cal[mdd_i], peak_date=cal[peak_i], sharpe=sharpe, calmar=calmar,
                up=up, down=len(r)-up, win=up/len(r)*100, dd=dd, rets=r, best=max(r)*100, worst=min(r)*100)

M = {}
M["组合(买入持有)"] = metrics(port_bh, "组合(买入持有)")
M["组合(每日再平衡)"] = metrics(port_dr, "组合(每日再平衡)")
M["科创芯片指数"] = metrics(idx_norm, "科创芯片指数")
for k in STK:
    M[NAMES[k]] = metrics([c / base[k] for c in close[k]], NAMES[k])

print("\n%-16s %9s %9s %8s %9s %7s %7s %6s %6s" % ("标的", "YTD%", "年化%", "波动%", "最大回撤%", "夏普", "Calmar", "胜日", "最佳/最差日%"))
for name, m in M.items():
    print("%-16s %9.2f %9.2f %8.2f %9.2f %7.2f %7.2f %5.1f%% %6.2f/%6.2f" % (
        name, m["tot"], m["cagr"], m["vol"], m["mdd"], m["sharpe"], m["calmar"], m["win"], m["best"], m["worst"]))
    if name in ("组合(买入持有)", "科创芯片指数") or name in [NAMES[k] for k in STK]:
        print("        峰值日 %s -> 谷底日 %s  涨日%d/跌日%d" % (m["peak_date"], m["mdd_date"], m["up"], m["down"]))

# --- 相关性 / Beta / 超额 ---
def corr(a, b):
    ma, mb = sum(a)/len(a), sum(b)/len(b)
    cov = sum((x-ma)*(y-mb) for x, y in zip(a, b)) / (len(a)-1)
    return cov / (st.pstdev(a) * st.pstdev(b))
def beta(y, x):
    mx, my = sum(x)/len(x), sum(y)/len(y)
    cov = sum((a-mx)*(b-my) for a, b in zip(x, y)) / (len(x)-1)
    return cov / st.pvariance(x)

ir = M["组合(买入持有)"]["rets"]
ix = M["科创芯片指数"]["rets"]
ex = [a-b for a, b in zip(ir, ix)]
te = st.pstdev(ex) * math.sqrt(244)
print("\n--- 组合(买入持有) vs 科创芯片指数 ---")
print("YTD超额: %.2f pct | 相关系数: %.3f | Beta: %.3f | 跟踪误差(年化): %.2f pct" % (
    M["组合(买入持有)"]["tot"] - M["科创芯片指数"]["tot"], corr(ir, ix), beta(ir, ix), te*100))
print("日超额胜率: %.1f%% (%d/%d)" % (sum(1 for e in ex if e > 0)/len(ex)*100, sum(1 for e in ex if e > 0), len(ex)))
# 超额收益净值
exn = [1.0]
for e in ex: exn.append(exn[-1]*(1+e))
print("超额净值(几何累计): %+.2f pct" % ((exn[-1]-1)*100))

for k in STK:
    print("  %s vs 指数: corr=%.3f beta=%.3f 超额=%.2f pct" % (
        NAMES[k], corr(M[NAMES[k]]["rets"], ix), beta(M[NAMES[k]]["rets"], ix),
        M[NAMES[k]]["tot"] - M["科创芯片指数"]["tot"]))

# --- 月度收益 ---
months = sorted(set(d[:6] for d in cal))
def monthly(norm):
    out = {}
    prev = None
    for mth in months:
        idxs = [i for i, d in enumerate(cal) if d[:6] == mth]
        first_i = idxs[0]
        p0 = norm[prev] if prev is not None else norm[first_i - 1] if first_i > 0 else norm[0]
        p1 = norm[idxs[-1]]
        out[mth] = (p1 / p0 - 1) * 100
        prev = idxs[-1]
    return out
mo = {name: monthly([v] if False else norm) for name, norm in []}
norms = {"组合(买入持有)": port_bh, "科创芯片指数": idx_norm}
for k in STK: norms[NAMES[k]] = [c / base[k] for c in close[k]]
mo = {n: monthly(v) for n, v in norms.items()}
print("\n--- 月度收益(%) ---")
print("%-8s %10s %10s %10s %10s %12s" % ("月份", "中芯国际", "寒武纪", "海光信息", "科创芯片", "组合(买持)"))
for mth in months:
    tag = mth[:4] + "-" + mth[4:] + ("*" if mth == months[-1] else "")
    print("%-8s %10.2f %10.2f %10.2f %10.2f %12.2f" % (tag,
        mo["中芯国际"][mth], mo["寒武纪"][mth], mo["海光信息"][mth], mo["科创芯片指数"][mth], mo["组合(买入持有)"][mth]))

# --- 权重漂移 ---
print("\n--- 组合权重漂移（买入持有，期初等权1/3）---")
w0 = {k: W * (close[k][0]/base[k]) for k in STK}
wt = {k: W * (close[k][-1]/base[k]) for k in STK}
tot0, tot1 = sum(w0.values()), sum(wt.values())
for k in STK:
    print("  %s: 期初 %.1f%% -> 期末 %.1f%% (价格 %s -> %s)" % (
        NAMES[k], w0[k]/tot0*100, wt[k]/tot1*100, close[k][0], close[k][-1]))

# --- 区间/高点分析 ---
print("\n--- YTD 高点/低点 ---")
for k in STK + ["000685"]:
    highs = [series[k][d][1] for d in cal]
    lows = [series[k][d][2] for d in cal]
    hi = max(highs); hid = cal[highs.index(hi)]
    lo = min(lows); lod = cal[lows.index(lo)]
    cur = close[k][-1]
    print("  %-8s 年内最高 %10.2f (%s) 最低 %10.2f (%s) 现价 %10.2f 距高点 %6.2f%%" % (
        NAMES[k], hi, hid, lo, lod, cur, (cur/hi-1)*100))

# --- 导出 JSON 供 HTML 用 ---
dates = [d[4:6] + "-" + d[6:] for d in cal]
full_dates = [d[:4] + "-" + d[4:6] + "-" + d[6:] for d in cal]
out = dict(
    dates=dates, full_dates=full_dates, base_date=BASE, end_date=cal[-1],
    port_bh=[round((v-1)*100, 2) for v in port_bh],
    port_dr=[round((v-1)*100, 2) for v in port_dr],
    idx=[round((v-1)*100, 2) for v in idx_norm],
    exn=[round((v-1)*100, 2) for v in exn],
    dd_port=[round(d*100, 2) for d in M["组合(买入持有)"]["dd"]],
    dd_idx=[round(d*100, 2) for d in M["科创芯片指数"]["dd"]],
    **{k: dict(norm=[round((c/base[k]-1)*100, 2) for c in close[k]],
               dd=[round(d*100, 2) for d in M[NAMES[k]]["dd"]],
               close=[round(c, 2) for c in close[k]],
               amount=[round(series[k][d][3]/1e8, 1) for d in cal]) for k in STK},
    idx_close=[round(c, 2) for c in close["000685"]],
    monthly={n: {m: round(v, 2) for m, v in d.items()} for n, d in mo.items()},
    metrics={n: {kk: (round(vv, 4) if isinstance(vv, float) else vv)
                 for kk, vv in m.items() if kk not in ("dd", "rets")} for n, m in M.items()},
    stats=dict(corr=round(corr(ir, ix), 4), beta=round(beta(ir, ix), 4),
               te=round(te*100, 2), ex_tot=round(M["组合(买入持有)"]["tot"]-M["科创芯片指数"]["tot"], 2),
               ex_geo=round((exn[-1]-1)*100, 2),
               ex_win=round(sum(1 for e in ex if e > 0)/len(ex)*100, 1),
               per_corr={NAMES[k]: round(corr(M[NAMES[k]]["rets"], ix), 4) for k in STK},
               per_beta={NAMES[k]: round(beta(M[NAMES[k]]["rets"], ix), 4) for k in STK},
               weights_end={NAMES[k]: round(wt[k]/tot1*100, 2) for k in STK}),
)
os.makedirs("out", exist_ok=True)
json.dump(out, open("out/portfolio.json", "w", encoding="utf-8"), ensure_ascii=False)
print("\nsaved out/portfolio.json")
