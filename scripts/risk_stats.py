import json, math, statistics as st

P = json.load(open("out/portfolio.json", encoding="utf-8"))
dates = P["dates"]; n = len(dates)
STK = ["688981", "688256", "688041"]
NM = {"688981": "中芯国际", "688256": "寒武纪", "688041": "海光信息"}

def rets(series_pct):
    """series_pct 是累计涨幅% -> 日收益"""
    v = [1 + x/100 for x in series_pct]
    return [v[i]/v[i-1]-1 for i in range(1, len(v))]

rp = rets(P["port_bh"])       # 组合买入持有
ri = rets(P["idx"])           # 指数
assert len(rp) == len(ri) == n-1

# --- 上行/下行捕获率 ---
up_i = [i for i, r in enumerate(ri) if r > 0]
dn_i = [i for i, r in enumerate(ri) if r < 0]
up_cap = (sum(rp[i] for i in up_i)/len(up_i)) / (sum(ri[i] for i in up_i)/len(up_i))
dn_cap = (sum(rp[i] for i in dn_i)/len(dn_i)) / (sum(ri[i] for i in dn_i)/len(dn_i))
print("=== 捕获率分析（组合买入持有 vs 科创芯片指数）===")
print("指数上涨日 %d 天：指数日均 %+.3f%%，组合日均 %+.3f%% -> 上行捕获率 %.1f%%" % (
    len(up_i), sum(ri[i] for i in up_i)/len(up_i)*100, sum(rp[i] for i in up_i)/len(up_i)*100, up_cap*100))
print("指数下跌日 %d 天：指数日均 %+.3f%%，组合日均 %+.3f%% -> 下行捕获率 %.1f%%" % (
    len(dn_i), sum(ri[i] for i in dn_i)/len(dn_i)*100, sum(rp[i] for i in dn_i)/len(dn_i)*100, dn_cap*100))
print("捕获率差（上行-下行）: %+.1f pct  %s" % (
    (up_cap-dn_cap)*100, "-> 涨时跟不上、跌时抗不住，双重不利" if up_cap < 1 and dn_cap > 0.95 else ""))

# 大涨/大跌日细分
big_up = [i for i, r in enumerate(ri) if r > 0.03]
big_dn = [i for i, r in enumerate(ri) if r < -0.03]
print("\n指数单日>+3%%共%d天：指数累计%+.2f%%，组合累计%+.2f%%（差额%+.2f pct）" % (
    len(big_up), (math.prod(1+ri[i] for i in big_up)-1)*100, (math.prod(1+rp[i] for i in big_up)-1)*100,
    ((math.prod(1+rp[i] for i in big_up))-math.prod(1+ri[i] for i in big_up))*100))
print("指数单日<-3%%共%d天：指数累计%+.2f%%，组合累计%+.2f%%（差额%+.2f pct）" % (
    len(big_dn), (math.prod(1+ri[i] for i in big_dn)-1)*100, (math.prod(1+rp[i] for i in big_dn)-1)*100,
    ((math.prod(1+rp[i] for i in big_dn))-math.prod(1+ri[i] for i in big_dn))*100))

# --- 相关性矩阵 ---
def corr(a, b):
    ma, mb = sum(a)/len(a), sum(b)/len(b)
    cov = sum((x-ma)*(y-mb) for x, y in zip(a,b))/(len(a)-1)
    return cov/(st.stdev(a)*st.stdev(b))   # 同用样本标准差，保证对角线=1
rk = {NM[k]: rets(P[k]["norm"]) for k in STK}
print("\n=== 日收益相关性矩阵 ===")
print("%-10s %8s %8s %8s %8s" % ("", "中芯", "寒武", "海光", "指数"))
for a in ["中芯国际", "寒武纪", "海光信息"]:
    print("%-10s %8.3f %8.3f %8.3f %8.3f" % (a, corr(rk[a], rk["中芯国际"]), corr(rk[a], rk["寒武纪"]),
          corr(rk[a], rk["海光信息"]), corr(rk[a], ri)))
print("组合内部平均相关: %.3f（分散化几乎无效）" % (
    (corr(rk["中芯国际"], rk["寒武纪"]) + corr(rk["中芯国际"], rk["海光信息"]) + corr(rk["寒武纪"], rk["海光信息"]))/3))

# --- 各标的对组合的贡献分解 ---
print("\n=== 组合收益分解（等权买入持有，期初各1/3资金，不调整）===")
tot_p = P["port_bh"][-1]
contrib_out = {}
for k in STK:
    c = (1/3) * P[k]["norm"][-1]          # 等权买入持有：组合收益 = (1/3)Σ各标的收益（精确）
    contrib_out[NM[k]] = round(c, 2)
    print("  %-8s 自身YTD %+7.2f%% -> 对组合贡献 %+7.2f pct（相当于组合总收益的 %+.0f%%）" % (
        NM[k], P[k]["norm"][-1], c, c/(tot_p)*100))
print("  合计校验: %+.2f pct vs 组合实际 %+.2f%% ✓" % (sum(contrib_out.values()), tot_p))
print("  指数 %+.2f%% -> 组合跑输 %+.2f pct" % (P["idx"][-1], tot_p - P["idx"][-1]))
# 反事实：若三只换成指数前20大其余17只等权
A = json.load(open("out/attribution.json", encoding="utf-8"))
print("  反事实：若改为持有指数其余17只前20大等权 -> YTD %+.2f%%，差额 %+.2f pct" % (
    A["summary"]["eq_rest17"], A["summary"]["eq_rest17"] - tot_p))

# --- 阶段分解：跑输集中在哪几个月 ---
mo = P["monthly"]
print("\n=== 月度超额（组合 - 指数）===")
months = [m for m in mo["科创芯片指数"].keys() if m != "202512"]
mo_out = []
for m in months:
    d = mo["组合(买入持有)"][m] - mo["科创芯片指数"][m]
    mo_out.append(dict(month=m[:4]+"-"+m[4:], port=round(mo["组合(买入持有)"][m],2),
                       idx=round(mo["科创芯片指数"][m],2), ex=round(d,2),
                       zx=round(mo["中芯国际"][m],2), hw=round(mo["寒武纪"][m],2), hg=round(mo["海光信息"][m],2)))
    bar = "#" * int(abs(d)/3) if abs(d) > 0.5 else ""
    print("  %-9s 组合%+7.2f%% 指数%+7.2f%% 超额%+8.2f pct %s%s" % (
        m[:4]+"-"+m[4:]+("*" if m == months[-1] else ""), mo["组合(买入持有)"][m], mo["科创芯片指数"][m], d,
        bar, " <- 跑赢" if d > 0 else ""))
print("  跑赢月份: %d/%d（%s）" % (sum(1 for x in mo_out if x["ex"]>0), len(mo_out),
      "/".join(x["month"] for x in mo_out if x["ex"]>0)))

# --- 关键窗口 ---
fd = P["full_dates"]   # "YYYY-MM-DD"，避免跨年字符串比较错误
def seg(norm, d0, d1):
    i0 = fd.index(d0); i1 = fd.index(d1)
    return ((1+norm[i1]/100)/(1+norm[i0]/100)-1)*100
print("\n=== 关键窗口表现（区间累计）===")
WINS = [("2026-01-05", "2026-01-30", "1月"), ("2026-04-01", "2026-04-30", "4月"),
        ("2026-06-01", "2026-06-30", "6月"), ("2026-07-01", "2026-07-31", "7月"),
        ("2026-08-03", "2026-08-31", "8月"), ("2026-09-01", "2026-09-14", "9月至今"),
        ("2025-12-31", "2026-07-09", "年初→组合峰值"), ("2026-07-09", "2026-09-14", "组合峰值→现价")]
win_out = []
for d0, d1, label in WINS:
    d0x = next((d for d in fd if d >= d0), None)
    d1x = next((d for d in reversed(fd) if d <= d1), None)
    if not d0x or not d1x or d0x >= d1x:
        print("  %-14s 跳过（区间无效 %s~%s）" % (label, d0, d1)); continue
    vals = [seg(P["port_bh"], d0x, d1x), seg(P["idx"], d0x, d1x)]
    for k in STK: vals.append(seg(P[k]["norm"], d0x, d1x))
    win_out.append(dict(label=label, d0=d0x, d1=d1x, port=round(vals[0],2), idx=round(vals[1],2),
                        ex=round(vals[0]-vals[1],2), zx=round(vals[2],2), hw=round(vals[3],2), hg=round(vals[4],2)))
    print("  %-14s(%s~%s) 组合%+7.2f%% 指数%+7.2f%% 超额%+7.2f | 中芯%+7.2f%% 寒武%+7.2f%% 海光%+7.2f%%" % (
        label, d0x, d1x, vals[0], vals[1], vals[0]-vals[1], vals[2], vals[3], vals[4]))

# --- 峰值回撤结构 ---
print("\n=== 峰值与回撤 ===")
pk_out = {}
for key, label in [("port_bh", "组合"), ("idx", "科创芯片指数")] + [(k, NM[k]) for k in STK]:
    norm = P[key] if isinstance(P[key], list) else P[key]["norm"]
    peak = max(norm); pi = norm.index(peak)
    after = norm[pi:]
    trough_after = min(after); ti = pi + after.index(trough_after)
    dd_pct = ((1+trough_after/100)/(1+peak/100)-1)*100
    cur_dd = ((1+norm[-1]/100)/(1+peak/100)-1)*100
    pk_out[label] = dict(peak=round(peak,2), peak_date=fd[pi], trough=round(trough_after,2),
                         trough_date=fd[ti], dd=round(dd_pct,2), cur=round(norm[-1],2),
                         cur_dd=round(cur_dd,2))
    print("  %-8s YTD峰值 %+8.2f%% (%s) -> 其后谷底 %+8.2f%% (%s) 回撤 %6.2f%% | 现价 %+8.2f%% 距峰值 %+7.2f%%" % (
        label, peak, fd[pi], trough_after, fd[ti], dd_pct, norm[-1], cur_dd))

# --- AH 溢价 ---
HKD_CNY = 0.86325  # 2026-09-14 央行授权中国外汇交易中心人民币中间价（官方口径）
a_price, h_price = 114.14, 61.15
prem = a_price / (h_price * HKD_CNY) - 1
print("\n=== 中芯国际 AH 溢价（A股688981 / H股00981）===")
print("A股 %.2f 元(CNY) | H股 %.2f 元(HKD) | 按 %.4f 汇率折 %.2f 元(CNY)" % (
    a_price, h_price, HKD_CNY, h_price*HKD_CNY))
print("AH溢价率 %+.1f%%  A股PE(TTM) 109.4x | H股PE(TTM) 66.6x" % (prem*100))

# --- 科创50 对照 ---
kc50 = (1528.26611/1344.199951 - 1) * 100
print("\n=== 指数横向对照 ===")
print("科创芯片(000685) YTD %+7.2f%% | 科创50(000688) YTD %+7.2f%% -> 科创芯片跑赢 %+.2f pct" % (
    P["idx"][-1], kc50, P["idx"][-1]-kc50))

json.dump(dict(up_cap=round(up_cap*100,1), dn_cap=round(dn_cap*100,1),
               up_days=len(up_i), dn_days=len(dn_i),
               up_idx_avg=round(sum(ri[i] for i in up_i)/len(up_i)*100,3),
               up_p_avg=round(sum(rp[i] for i in up_i)/len(up_i)*100,3),
               dn_idx_avg=round(sum(ri[i] for i in dn_i)/len(dn_i)*100,3),
               dn_p_avg=round(sum(rp[i] for i in dn_i)/len(dn_i)*100,3),
               big_up_n=len(big_up), big_up_idx=round((math.prod(1+ri[i] for i in big_up)-1)*100,2),
               big_up_p=round((math.prod(1+rp[i] for i in big_up)-1)*100,2),
               big_dn_n=len(big_dn), big_dn_idx=round((math.prod(1+ri[i] for i in big_dn)-1)*100,2),
               big_dn_p=round((math.prod(1+rp[i] for i in big_dn)-1)*100,2),
               corr={"中芯-寒武": round(corr(rk["中芯国际"], rk["寒武纪"]),3),
                     "中芯-海光": round(corr(rk["中芯国际"], rk["海光信息"]),3),
                     "寒武-海光": round(corr(rk["寒武纪"], rk["海光信息"]),3),
                     "组合-指数": round(corr(rp, ri),3),
                     "中芯-指数": round(corr(rk["中芯国际"], ri),3),
                     "寒武-指数": round(corr(rk["寒武纪"], ri),3),
                     "海光-指数": round(corr(rk["海光信息"], ri),3),
                     "内部平均": round((corr(rk["中芯国际"],rk["寒武纪"])+corr(rk["中芯国际"],rk["海光信息"])+corr(rk["寒武纪"],rk["海光信息"]))/3,3)},
               contrib=contrib_out, windows=win_out, monthly=mo_out, peaks=pk_out,
               ah_prem=round(prem*100,1), hkd_cny=HKD_CNY, kc50_ytd=round(kc50,2),
               metrics=P["metrics"], stats=P["stats"]),
          open("out/risk_stats.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nsaved out/risk_stats.json")
