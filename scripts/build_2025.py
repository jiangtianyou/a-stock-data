import json, os, math, bisect, statistics as st

BASE = r"D:\Desktop\Playground\a-stock-data"
RAW = json.load(open(os.path.join(BASE, "out", "k2025_all.json"), encoding="utf-8"))

IDX = "000685"
STK = ["688981", "688256", "688041"]
NM = {"688981": "中芯国际", "688256": "寒武纪", "688041": "海光信息", "000685": "科创芯片指数"}
W = 1/3

# ---- 主日历 = 指数交易日（2024-12-31 基准 + 2025 全年）----
idx_rows = RAW[IDX]["rows"]
cal = [r["d"] for r in idx_rows if r["d"] <= "20251231"]      # 含 20241231
cal = [d for d in cal if d >= "20241231"]
fd = [d[:4]+"-"+d[4:6]+"-"+d[6:] for d in cal]
dates = [d[4:6]+"-"+d[6:] for d in cal]
n = len(cal)

# ---- 个股 asof 映射到主日历（停牌日沿用前收盘，符合买入持有真实体验）----
def series_asof(code, field="c"):
    rows = RAW[code]["rows"]
    ds = [r["d"] for r in rows]
    vals = [r[field] for r in rows]
    out = []
    for d in cal:
        i = bisect.bisect_right(ds, d) - 1
        out.append(vals[i] if i >= 0 else vals[0])
    return out

close = {IDX: series_asof(IDX)}
for k in STK: close[k] = series_asof(k)
base = {k: close[k][0] for k in close}

print("主日历 %s -> %s | 交易日 %d（含基准）| 收盘价口径(腾讯qfq)" % (cal[0], cal[-1], n))
for k in [IDX]+STK:
    print("  %-6s %-8s base %.2f -> end %.2f  YTD25 %+.2f%%" % (k, NM.get(k,''), base[k], close[k][-1], (close[k][-1]/base[k]-1)*100))

# ---- 组合净值 ----
port_bh = [sum(W*close[k][i]/base[k] for k in STK) for i in range(n)]
rets = {k: [close[k][i]/close[k][i-1]-1 for i in range(1, n)] for k in [IDX]+STK}
port_dr = [1.0]
for i in range(n-1):
    port_dr.append(port_dr[-1]*(1+sum(W*rets[k][i] for k in STK)))
idx_norm = [c/base[IDX] for c in close[IDX]]
norms = {"port": port_bh, "idx": idx_norm, **{NM[k]: [c/base[k] for c in close[k]] for k in STK}}

def dd_series(norm):
    peak = norm[0]; out = []
    for v in norm:
        if v > peak: peak = v
        out.append((v/peak-1)*100)
    return out

def metrics(norm, label, rf=0.015):
    m = len(norm)
    tot = norm[-1]/norm[0]-1
    cagr = (norm[-1]/norm[0])**(244.0/(m-1))-1
    r = [norm[i]/norm[i-1]-1 for i in range(1, m)]
    vol = st.stdev(r)*math.sqrt(244)
    dd = dd_series(norm); mdd = min(dd); mi = dd.index(mdd)
    peak = max(norm); pi = norm.index(peak)
    sharpe = (cagr-rf)/vol
    calmar = (cagr*100)/abs(mdd) if mdd else 0
    up = sum(1 for x in r if x > 0)
    return dict(label=label, tot=round(tot*100,2), cagr=round(cagr*100,2), vol=round(vol*100,2),
                mdd=round(mdd,2), mdd_date=fd[mi], peak=round((peak-1)*100,2), peak_date=fd[pi],
                sharpe=round(sharpe,2), calmar=round(calmar,2), win=round(up/len(r)*100,1),
                up_days=up, dn_days=len(r)-up, best=round(max(r)*100,2), worst=round(min(r)*100,2),
                dd=[round(x,2) for x in dd])

M = {"组合(等权买入持有)": metrics(port_bh, "组合(等权买入持有)"),
     "组合(等权每日再平衡)": metrics(port_dr, "组合(等权每日再平衡)"),
     "科创芯片指数": metrics(idx_norm, "科创芯片指数")}
for k in STK: M[NM[k]] = metrics([c/base[k] for c in close[k]], NM[k])

print("\n%-22s %9s %9s %8s %9s %7s %7s %7s" % ("标的","YTD25%","年化%","波动%","回撤%","夏普","Calmar","胜率"))
for nm, m in M.items():
    print("%-22s %9.2f %9.2f %8.2f %9.2f %7.2f %7.2f %6.1f%%" % (nm,m["tot"],m["cagr"],m["vol"],m["mdd"],m["sharpe"],m["calmar"],m["win"]))

def corr(a,b):
    ma,mb=sum(a)/len(a),sum(b)/len(b)
    cov=sum((x-ma)*(y-mb) for x,y in zip(a,b))/(len(a)-1)
    return cov/(st.stdev(a)*st.stdev(b))
def beta(y,x):
    mx,my=sum(x)/len(x),sum(y)/len(y)
    cov=sum((a-mx)*(b-my) for a,b in zip(x,y))/(len(x)-1)
    return cov/st.variance(x)

rp=[port_bh[i]/port_bh[i-1]-1 for i in range(1,n)]; ri=rets[IDX]
ex=[a-b for a,b in zip(rp,ri)]; te=st.stdev(ex)*math.sqrt(244)
exn=[1.0]
for e in ex: exn.append(exn[-1]*(1+e))
exa=[rp_i-ri_i for rp_i,ri_i in zip(rp,ri)]
exan=[0.0]; cum_p=1.0; cum_i=1.0
exan=[round(((port_bh[i]/idx_norm[i])-1)*100,2) for i in range(n)]  # 几何超额序列
up_i=[i for i,r in enumerate(ri) if r>0]; dn_i=[i for i,r in enumerate(ri) if r<0]
up_cap=(sum(rp[i] for i in up_i)/len(up_i))/(sum(ri[i] for i in up_i)/len(up_i))
dn_cap=(sum(rp[i] for i in dn_i)/len(dn_i))/(sum(ri[i] for i in dn_i)/len(dn_i))
big_up=[i for i,r in enumerate(ri) if r>0.03]; big_dn=[i for i,r in enumerate(ri) if r<-0.03]

rk={NM[k]:rets[k] for k in STK}
CM=[[round(corr(rk[a],rk[b]),3) for b in ["中芯国际","寒武纪","海光信息"]]+[round(corr(rk[a],ri),3)] for a in ["中芯国际","寒武纪","海光信息"]]
CM.append([round(corr(ri,rk[a]),3) for a in ["中芯国际","寒武纪","海光信息"]]+[1.0])

# 月度
months=sorted(set(d[:6] for d in cal if d>="20250101"))
def monthly(norm):
    out={}; prev=None
    for m in months:
        ii=[i for i,d in enumerate(cal) if d[:6]==m]
        p0=norm[prev] if prev is not None else norm[ii[0]-1]
        out[m]=round((norm[ii[-1]]/p0-1)*100,2); prev=ii[-1]
    return out
mo={k:monthly(v) for k,v in norms.items()}

print("\n=== 相对指数（2025全年）===")
print("超额(算术) %+.2fpct | 超额(几何) %+.2f%% | corr %.3f | Beta %.3f | TE %.2f%%" % (
    M["组合(等权买入持有)"]["tot"]-M["科创芯片指数"]["tot"], (exn[-1]-1)*100, corr(rp,ri), beta(rp,ri), te*100))
print("日超额胜率 %.1f%% | 上行捕获 %.1f%% | 下行捕获 %.1f%%" % (
    sum(1 for e in ex if e>0)/len(ex)*100, up_cap*100, dn_cap*100))
print("指数>+3%%的%d天: 指数%+.2f%% 组合%+.2f%% | <-3%%的%d天: 指数%+.2f%% 组合%+.2f%%" % (
    len(big_up),(math.prod(1+ri[i] for i in big_up)-1)*100,(math.prod(1+rp[i] for i in big_up)-1)*100,
    len(big_dn),(math.prod(1+ri[i] for i in big_dn)-1)*100,(math.prod(1+rp[i] for i in big_dn)-1)*100))
for k in STK:
    print("  %-8s vs指数 corr=%.3f beta=%.3f 超额=%+.2fpct" % (NM[k],corr(rk[NM[k]],ri),beta(rk[NM[k]],ri),M[NM[k]]["tot"]-M["科创芯片指数"]["tot"]))

# 月度超额（上涨月vs下跌月）
up_m=[m for m in months if mo["idx"][m]>0]; dn_m=[m for m in months if mo["idx"][m]<0]
print("\n指数上涨月 %s 超额合计 %+.2fpct" % (up_m, sum(mo["port"][m]-mo["idx"][m] for m in up_m)))
print("指数下跌月 %s 超额合计 %+.2fpct" % (dn_m, sum(mo["port"][m]-mo["idx"][m] for m in dn_m)))
print("\n=== 月度明细 ===")
for m in months:
    print("  %s 组合%+7.2f%% 指数%+7.2f%% 超额%+7.2f | 中芯%+7.2f 寒武%+7.2f 海光%+7.2f" % (
        m,mo["port"][m],mo["idx"][m],mo["port"][m]-mo["idx"][m],mo["中芯国际"][m],mo["寒武纪"][m],mo["海光信息"][m]))

# 关键窗口
def seg(norm,d0,d1,incl=True):
    i0=fd.index(d0); i1=fd.index(d1)
    if incl and i0>0: i0-=1
    return round((norm[i1]/norm[i0]-1)*100,2)
pk=M["组合(等权买入持有)"]["peak_date"]; ipk=M["科创芯片指数"]["peak_date"]
MB=[(fd[0],pk,"年初→组合峰值",False),(pk,fd[-1],"组合峰值→年末",False),
    (fd[0],ipk,"年初→指数峰值",False),(ipk,fd[-1],"指数峰值→年末",False)]
win=[]
for d0,d1,label,incl in MB:
    win.append(dict(label=label,d0=d0,d1=d1,port=seg(port_bh,d0,d1,incl),idx=seg(idx_norm,d0,d1,incl),
                    zx=seg(norms["中芯国际"],d0,d1,incl),hw=seg(norms["寒武纪"],d0,d1,incl),hg=seg(norms["海光信息"],d0,d1,incl)))
    win[-1]["ex"]=round(win[-1]["port"]-win[-1]["idx"],2)
print("\n=== 关键窗口 ===")
for w in win:
    print("  %-14s 组合%+8.2f%% 指数%+8.2f%% 超额%+7.2f | 中芯%+8.2f 寒武%+8.2f 海光%+8.2f" % (
        w["label"],w["port"],w["idx"],w["ex"],w["zx"],w["hw"],w["hg"]))

# 权重漂移
wt={k:W*(close[k][-1]/base[k]) for k in STK}; tt=sum(wt.values())
print("\n=== 权重漂移（买入持有，年初→年末）===")
for k in STK: print("  %-8s 33.3%% -> %.1f%%" % (NM[k], wt[k]/tt*100))

# 成交额
amt={k:[x/1e8 for x in series_asof(k,"amt")] for k in [IDX]+STK}

out=dict(dates=dates,full_dates=fd,base_date=cal[0],end_date=cal[-1],n=n,
    port_bh=[round((v-1)*100,2) for v in port_bh],
    port_dr=[round((v-1)*100,2) for v in port_dr],
    idx=[round((v-1)*100,2) for v in idx_norm],
    exn=[round((v-1)*100,2) for v in exn],
    exan=exan,
    dd_port=M["组合(等权买入持有)"]["dd"],dd_idx=M["科创芯片指数"]["dd"],
    **{k:dict(norm=[round((c/base[k]-1)*100,2) for c in close[k]],dd=M[NM[k]]["dd"],
        close=[round(c,2) for c in close[k]],amount=[round(a,2) for a in amt[k]],
        base_close=round(base[k],2),last_close=round(close[k][-1],2)) for k in STK},
    idx_close=[round(c,2) for c in close[IDX]],idx_amount=[round(a,2) for a in amt[IDX]],
    metrics={k:{kk:vv for kk,vv in v.items() if kk!="dd"} for k,v in M.items()},
    monthly={k:v for k,v in mo.items()},windows=win,corr_matrix=CM,months=months,
    stats=dict(corr=round(corr(rp,ri),3),beta=round(beta(rp,ri),3),te=round(te*100,2),
        ex_arith=round(M["组合(等权买入持有)"]["tot"]-M["科创芯片指数"]["tot"],2),
        ex_geo=round((exn[-1]-1)*100,2),ex_win=round(sum(1 for e in ex if e>0)/len(ex)*100,1),
        up_cap=round(up_cap*100,1),dn_cap=round(dn_cap*100,1),up_days=len(up_i),dn_days=len(dn_i),
        big_up_n=len(big_up),big_up_idx=round((math.prod(1+ri[i] for i in big_up)-1)*100,2),
        big_up_p=round((math.prod(1+rp[i] for i in big_up)-1)*100,2),
        big_dn_n=len(big_dn),big_dn_idx=round((math.prod(1+ri[i] for i in big_dn)-1)*100,2),
        big_dn_p=round((math.prod(1+rp[i] for i in big_dn)-1)*100,2),
        per_corr={NM[k]:round(corr(rk[NM[k]],ri),3) for k in STK},
        per_beta={NM[k]:round(beta(rk[NM[k]],ri),3) for k in STK},
        per_ex={NM[k]:round(M[NM[k]]["tot"]-M["科创芯片指数"]["tot"],2) for k in STK},
        weights_end={NM[k]:round(wt[k]/tt*100,2) for k in STK},
        up_m_ex=round(sum(mo["port"][m]-mo["idx"][m] for m in up_m),2),
        dn_m_ex=round(sum(mo["port"][m]-mo["idx"][m] for m in dn_m),2),
        avg_amt={NM[k]:round(sum(amt[k])/n,1) for k in STK},idx_avg_amt=round(sum(amt[IDX])/n,1)),
)

# ---- 一致性校验 ----
print("\n=== 一致性校验 ===")
ch_port=(math.prod(1+mo["port"][m]/100 for m in months)-1)*100
ch_idx=(math.prod(1+mo["idx"][m]/100 for m in months)-1)*100
ok1=abs(ch_port-M["组合(等权买入持有)"]["tot"])<0.05 and abs(ch_idx-M["科创芯片指数"]["tot"])<0.05
print("  月度连乘: 组合%+.2f vs累计%+.2f | 指数%+.2f vs累计%+.2f -> %s"%(ch_port,M["组合(等权买入持有)"]["tot"],ch_idx,M["科创芯片指数"]["tot"],"OK" if ok1 else "FAIL"))
decomp=sum((1/3)*M[NM[k]]["tot"] for k in STK)
ok2=abs(decomp-M["组合(等权买入持有)"]["tot"])<0.02
print("  等权分解 (1/3)Σ=%+.2f vs 组合实际=%+.2f -> %s"%(decomp,M["组合(等权买入持有)"]["tot"],"OK" if ok2 else "FAIL"))
print("  对角线:",[CM[i][i] for i in range(4)])
out["_check"]=dict(monthly_chain="OK" if ok1 else "FAIL",decomp="OK" if ok2 else "FAIL")
json.dump(out,open(os.path.join(BASE,"out","final2025.json"),"w",encoding="utf-8"),ensure_ascii=False)
print("\nsaved out/final2025.json (%d 交易日)"%n)
