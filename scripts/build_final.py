import json, os, math, statistics as st

D = r"C:\Users\Administrator\.workbuddy\projects\d-Desktop-Playground-a-stock-data\f4800af3-610a-497f-a9b6-fb135319d10e\tool-results"
FILES = {
    "688981": "mcp-tdx-connector-tdx_kline-1789368452656-d2cc6d.txt",
    "688256": "mcp-tdx-connector-tdx_kline-1789368471326-8b9b18.txt",
    "688041": "mcp-tdx-connector-tdx_kline-1789368486947-8379df.txt",
    "000685": "mcp-tdx-connector-tdx_kline-1789368485688-da60c7.txt",
}
NM = {"688981": "中芯国际", "688256": "寒武纪", "688041": "海光信息", "000685": "科创芯片指数"}
STK = ["688981", "688256", "688041"]

# 9-14 官方收盘价（腾讯快照，15:00 后）
CLOSE_0914 = {"688981": 114.07, "688256": 1040.00, "688041": 223.69, "000685": 3602.31}

def parse(fn):
    raw = open(os.path.join(D, fn), encoding="utf-8", errors="ignore").read()
    obj, _ = json.JSONDecoder().raw_decode(raw[raw.find("{"):])
    return [(r["Data"], float(r["Close"]), float(r["High"]), float(r["Low"]), float(r["Amount"])) for r in obj["Rows"]]

raw = {k: parse(v) for k, v in FILES.items()}
# 用收盘价覆盖最后一根（原为盘中 14:46 数据）
for k in raw:
    if raw[k][-1][0] == "20260914":
        d, _, h, l, a = raw[k][-1]
        raw[k][-1] = (d, CLOSE_0914[k], h, l, a)

cal = [r[0] for r in raw["000685"]]
cal = [d for d in cal if d >= "20251231"]
idxmap = {k: {r[0]: r for r in raw[k]} for k in raw}
close = {k: [idxmap[k][d][1] for d in cal] for k in NM}
base = {k: close[k][0] for k in close}
dates = [d[4:6] + "-" + d[6:] for d in cal]
fd = [d[:4] + "-" + d[4:6] + "-" + d[6:] for d in cal]
n = len(cal)
print("基准 %s -> 结束 %s | 交易日 %d | 收盘价口径" % (cal[0], cal[-1], n))

W = 1/3
port_bh = [sum(W * close[k][i]/base[k] for k in STK) for i in range(n)]
rets = {k: [close[k][i]/close[k][i-1]-1 for i in range(1, n)] for k in NM}
port_dr = [1.0]
for i in range(n-1):
    port_dr.append(port_dr[-1] * (1 + sum(W*rets[k][i] for k in STK)))
idx_norm = [c/base["000685"] for c in close["000685"]]

def dd_series(norm):
    peak = norm[0]; out = []
    for v in norm:
        if v > peak: peak = v
        out.append((v/peak - 1) * 100)
    return out

def metrics(norm, label, rf=0.015):
    m = len(norm)
    tot = norm[-1]/norm[0] - 1
    cagr = (norm[-1]/norm[0]) ** (244.0/(m-1)) - 1
    r = [norm[i]/norm[i-1]-1 for i in range(1, m)]
    vol = st.stdev(r) * math.sqrt(244)
    dd = dd_series(norm)
    mdd = min(dd); mi = dd.index(mdd)
    peak = max(norm); pi = norm.index(peak)
    sharpe = (cagr - rf)/vol
    calmar = (cagr*100)/abs(mdd) if mdd else 0     # 两者同为百分数口径
    up = sum(1 for x in r if x > 0)
    return dict(label=label, tot=round(tot*100,2), cagr=round(cagr*100,2), vol=round(vol*100,2),
                mdd=round(mdd,2), mdd_date=fd[mi], peak=round((peak-1)*100,2), peak_date=fd[pi],
                sharpe=round(sharpe,2), calmar=round(calmar,2), win=round(up/len(r)*100,1),
                up_days=up, dn_days=len(r)-up, best=round(max(r)*100,2), worst=round(min(r)*100,2),
                dd=[round(x,2) for x in dd], ann_vol=round(vol*100,2))

M = {"组合(等权买入持有)": metrics(port_bh, "组合(等权买入持有)"),
     "组合(等权每日再平衡)": metrics(port_dr, "组合(等权每日再平衡)"),
     "科创芯片指数": metrics(idx_norm, "科创芯片指数")}
for k in STK: M[NM[k]] = metrics([c/base[k] for c in close[k]], NM[k])

print("\n%-22s %9s %9s %8s %9s %7s %7s %7s" % ("标的", "YTD%", "年化%", "年化波动%", "最大回撤%", "夏普", "Calmar", "日胜率"))
for name, m in M.items():
    print("%-22s %9.2f %9.2f %8.2f %9.2f %7.2f %7.2f %6.1f%%" % (
        name, m["tot"], m["cagr"], m["vol"], m["mdd"], m["sharpe"], m["calmar"], m["win"]))

def corr(a, b):
    ma, mb = sum(a)/len(a), sum(b)/len(b)
    cov = sum((x-ma)*(y-mb) for x, y in zip(a,b))/(len(a)-1)
    return cov/(st.stdev(a)*st.stdev(b))
def beta(y, x):
    mx, my = sum(x)/len(x), sum(y)/len(y)
    cov = sum((a-mx)*(b-my) for a, b in zip(x,y))/(len(x)-1)
    return cov/st.variance(x)

rp = [port_bh[i]/port_bh[i-1]-1 for i in range(1, n)]
ri = rets["000685"]
ex = [a-b for a, b in zip(rp, ri)]
te = st.stdev(ex)*math.sqrt(244)
exn = [1.0]
for e in ex: exn.append(exn[-1]*(1+e))
up_i = [i for i,r in enumerate(ri) if r > 0]; dn_i = [i for i,r in enumerate(ri) if r < 0]
up_cap = (sum(rp[i] for i in up_i)/len(up_i))/(sum(ri[i] for i in up_i)/len(up_i))
dn_cap = (sum(rp[i] for i in dn_i)/len(dn_i))/(sum(ri[i] for i in dn_i)/len(dn_i))
big_up = [i for i,r in enumerate(ri) if r > 0.03]; big_dn = [i for i,r in enumerate(ri) if r < -0.03]

rk = {NM[k]: rets[k] for k in STK}
CM = [[round(corr(rk[a], rk[b]),3) for b in ["中芯国际","寒武纪","海光信息"]] + [round(corr(rk[a], ri),3)]
      for a in ["中芯国际","寒武纪","海光信息"]]
CM.append([round(corr(ri, rk[a]),3) for a in ["中芯国际","寒武纪","海光信息"]] + [1.0])

# 月度
months = sorted(set(d[:6] for d in cal))
def monthly(norm):
    out = {}; prev = None
    for m in months:
        ii = [i for i, d in enumerate(cal) if d[:6] == m]
        p0 = norm[prev] if prev is not None else (norm[ii[0]-1] if ii[0] > 0 else norm[0])
        out[m] = round((norm[ii[-1]]/p0 - 1)*100, 2); prev = ii[-1]
    return out
norms = {"port": port_bh, "idx": idx_norm, **{NM[k]: [c/base[k] for c in close[k]] for k in STK}}
mo = {k: monthly(v) for k, v in norms.items()}

print("\n=== 相对指数（等权买入持有）===")
print("超额(算术) %+.2f pct | 超额(几何) %+.2f pct | 相关 %.3f | Beta %.3f | 跟踪误差 %.2f%%" % (
    M["组合(等权买入持有)"]["tot"] - M["科创芯片指数"]["tot"], (exn[-1]-1)*100,
    corr(rp, ri), beta(rp, ri), te*100))
print("日超额胜率 %.1f%% (%d/%d) | 上行捕获 %.1f%% | 下行捕获 %.1f%%" % (
    sum(1 for e in ex if e>0)/len(ex)*100, sum(1 for e in ex if e>0), len(ex), up_cap*100, dn_cap*100))
print("指数>+3%%的%d天: 指数累计%+.2f%% 组合%+.2f%% | 指数<-3%%的%d天: 指数%+.2f%% 组合%+.2f%%" % (
    len(big_up), (math.prod(1+ri[i] for i in big_up)-1)*100, (math.prod(1+rp[i] for i in big_up)-1)*100,
    len(big_dn), (math.prod(1+ri[i] for i in big_dn)-1)*100, (math.prod(1+rp[i] for i in big_dn)-1)*100))
for k in STK:
    print("  %-8s vs 指数: corr=%.3f beta=%.3f 超额=%+.2fpct" % (NM[k], corr(rk[NM[k]], ri),
          beta(rk[NM[k]], ri), M[NM[k]]["tot"] - M["科创芯片指数"]["tot"]))

# 窗口 = 自然月（首末交易日），起点自动含上月末收盘 -> 与月度收益表严格一致
# 注意：norms 是「净值」序列（1.0 基准），直接用比值，不能再 +1
def seg(norm, d0, d1, incl=True):
    i0 = fd.index(d0)
    i1 = fd.index(d1)
    if incl and i0 > 0: i0 -= 1        # 含起点当日涨跌
    return round((norm[i1]/norm[i0] - 1)*100, 2)
MB = []
for m in months:
    if m == "202512": continue
    ii = [i for i, d in enumerate(cal) if d[:6] == m]
    MB.append((fd[ii[0]], fd[ii[-1]], m[:4]+"-"+m[4:]+("*" if m == months[-1] else "")))
MB += [(fd[0], M["组合(等权买入持有)"]["peak_date"], "年初→组合峰值", False),
       (M["组合(等权买入持有)"]["peak_date"], fd[-1], "组合峰值→今", False),
       (fd[0], M["科创芯片指数"]["peak_date"], "年初→指数峰值", False),
       (M["科创芯片指数"]["peak_date"], fd[-1], "指数峰值→今", False)]
win = []
for item in MB:
    d0, d1, label = item[0], item[1], item[2]
    incl = item[3] if len(item) > 3 else True
    win.append(dict(label=label, d0=d0, d1=d1, port=seg(port_bh,d0,d1,incl), idx=seg(idx_norm,d0,d1,incl),
                    zx=seg(norms[NM["688981"]],d0,d1,incl), hw=seg(norms[NM["688256"]],d0,d1,incl),
                    hg=seg(norms[NM["688041"]],d0,d1,incl)))
    win[-1]["ex"] = round(win[-1]["port"] - win[-1]["idx"], 2)

# 一致性校验：窗口收益 vs 月度收益表
print("\n=== 一致性校验（窗口 vs 月度表）===")
mlist = [m for m in months if m != "202512"]
bad = 0
for i, mkey in enumerate(mlist):
    w = win[i]
    pairs = [("port", "组合"), ("idx", "指数"), ("zx", "中芯"), ("hw", "寒武"), ("hg", "海光")]
    src = {"port": "port", "idx": "idx", "zx": "中芯国际", "hw": "寒武纪", "hg": "海光信息"}
    for key, tag in pairs:
        a = w[key]; b = mo[src[key]][mkey]
        if abs(a - b) > 0.02:
            print("  x %s %s 窗口%+.2f%% vs 月度%+.2f%%" % (w["label"], tag, a, b)); bad += 1
print("  月度窗口 vs 月度表: %s (%d 处偏差)" % ("OK 全部一致" if bad == 0 else "FAIL", bad))
# 月度连乘 = 累计
ch_port = (math.prod(1 + mo["port"][m]/100 for m in months) - 1) * 100
ch_idx = (math.prod(1 + mo["idx"][m]/100 for m in months) - 1) * 100
print("  组合月度连乘 %+.2f%% vs 累计 %+.2f%% | 指数月度连乘 %+.2f%% vs 累计 %+.2f%% -> %s" % (
    ch_port, M["组合(等权买入持有)"]["tot"], ch_idx, M["科创芯片指数"]["tot"],
    "OK" if abs(ch_port - M["组合(等权买入持有)"]["tot"]) < 0.05 and abs(ch_idx - M["科创芯片指数"]["tot"]) < 0.05 else "FAIL"))
# 组合等权分解自洽
decomp = sum((1/3) * M[NM[k]]["tot"] for k in STK)
print("  等权分解 (1/3)Σ个股YTD = %+.2f%% vs 组合实际 %+.2f%% -> %s" % (
    decomp, M["组合(等权买入持有)"]["tot"],
    "OK" if abs(decomp - M["组合(等权买入持有)"]["tot"]) < 0.02 else "FAIL"))
print("\n=== 关键窗口 ===")
for w in win:
    print("  %-14s 组合%+7.2f%% 指数%+7.2f%% 超额%+7.2f | 中芯%+7.2f%% 寒武%+7.2f%% 海光%+7.2f%%" % (
        w["label"], w["port"], w["idx"], w["ex"], w["zx"], w["hw"], w["hg"]))

# 权重漂移
w0 = {k: W for k in STK}
wt = {k: W*(close[k][-1]/base[k]) for k in STK}
tt = sum(wt.values())
print("\n=== 权重漂移（买入持有）===")
for k in STK:
    print("  %-8s 期初 %.1f%% -> 期末 %.1f%% (%.2f -> %.2f 元)" % (NM[k], w0[k]*100, wt[k]/tt*100, close[k][0], close[k][-1]))

# 成交额（活跃度）
amt = {k: [round(idxmap[k][d][4]/1e8, 2) for d in cal] for k in NM}
print("\n=== 日均成交额（亿元）===")
for k in STK + ["000685"]:
    print("  %-8s 全期日均 %7.1f | 4-6月日均 %7.1f | 9月日均 %7.1f" % (
        NM[k], sum(amt[k])/n,
        sum(a for d,a in zip(cal, amt[k]) if "20260401"<=d<="20260630")/len([d for d in cal if "20260401"<=d<="20260630"]),
        sum(a for d,a in zip(cal, amt[k]) if d>="20260901")/len([d for d in cal if d>="20260901"])))

out = dict(
    dates=dates, full_dates=fd, base_date=cal[0], end_date=cal[-1], n=n,
    port_bh=[round((v-1)*100,2) for v in port_bh],
    port_dr=[round((v-1)*100,2) for v in port_dr],
    idx=[round((v-1)*100,2) for v in idx_norm],
    exn=[round((v-1)*100,2) for v in exn],
    dd_port=M["组合(等权买入持有)"]["dd"], dd_idx=M["科创芯片指数"]["dd"],
    **{k: dict(norm=[round((c/base[k]-1)*100,2) for c in close[k]], dd=M[NM[k]]["dd"],
               close=[round(c,2) for c in close[k]], amount=amt[k],
               base_close=round(base[k],2), last_close=round(close[k][-1],2),
               hi=round(max(idxmap[k][d][2] for d in cal),2),
               hi_date=fd[[idxmap[k][d][2] for d in cal].index(max(idxmap[k][d][2] for d in cal))],
               lo=round(min(idxmap[k][d][3] for d in cal),2),
               lo_date=fd[[idxmap[k][d][3] for d in cal].index(min(idxmap[k][d][3] for d in cal))]) for k in STK},
    idx_close=[round(c,2) for c in close["000685"]], idx_amount=amt["000685"],
    metrics={k: {kk: vv for kk, vv in v.items() if kk != "dd"} for k, v in M.items()},
    monthly={k: v for k, v in mo.items()}, windows=win, corr_matrix=CM,
    stats=dict(corr=round(corr(rp,ri),3), beta=round(beta(rp,ri),3), te=round(te*100,2),
               ex_arith=round(M["组合(等权买入持有)"]["tot"]-M["科创芯片指数"]["tot"],2),
               ex_geo=round((exn[-1]-1)*100,2),
               ex_win=round(sum(1 for e in ex if e>0)/len(ex)*100,1),
               up_cap=round(up_cap*100,1), dn_cap=round(dn_cap*100,1),
               up_days=len(up_i), dn_days=len(dn_i),
               big_up_n=len(big_up), big_up_idx=round((math.prod(1+ri[i] for i in big_up)-1)*100,2),
               big_up_p=round((math.prod(1+rp[i] for i in big_up)-1)*100,2),
               big_dn_n=len(big_dn), big_dn_idx=round((math.prod(1+ri[i] for i in big_dn)-1)*100,2),
               big_dn_p=round((math.prod(1+rp[i] for i in big_dn)-1)*100,2),
               per_corr={NM[k]: round(corr(rk[NM[k]],ri),3) for k in STK},
               per_beta={NM[k]: round(beta(rk[NM[k]],ri),3) for k in STK},
               per_ex={NM[k]: round(M[NM[k]]["tot"]-M["科创芯片指数"]["tot"],2) for k in STK},
               weights_end={NM[k]: round(wt[k]/tt*100,2) for k in STK},
               avg_amt={NM[k]: round(sum(amt[k])/n,1) for k in STK},
               idx_avg_amt=round(sum(amt["000685"])/n,1)),
)
json.dump(out, open("out/final.json","w",encoding="utf-8"), ensure_ascii=False)
print("\nsaved out/final.json (%d 个交易日)" % n)
