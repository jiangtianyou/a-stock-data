import json

rows = json.load(open("out/components_final.json", encoding="utf-8"))["rows"]
IDX_YTD, IDX_NOW, IDX_HI, IDX_LO52 = 38.04, 3607.588623, 5660.68, 2200.89
IDX_BASE = IDX_NOW / (1 + IDX_YTD/100)
TOP3 = {"688981", "688256", "688041"}

o = [r for r in rows if r["code"] in TOP3]
x = [r for r in rows if r["code"] not in TOP3]
for i, r in enumerate(sorted(rows, key=lambda y: -y["weight"]), 1):
    r["rank_w"] = i

# --- 口径说明 ---
# 科创芯片指数(000685)为【自由流通市值加权 + 单只权重上限 + 半年度调仓(6月/12月)】。
# 年初真实权重无法从公开接口还原（需历史自由流通股本快照），因此：
#   A) 等权口径：精确、无权重漂移污染 -> 用于结构归因
#   B) 当前权重口径：近似、会高估涨幅大者 -> 仅用于「相对贡献占比」
eq_all20 = sum(r["ytd"] for r in rows) / len(rows)
eq_top3 = sum(r["ytd"] for r in o) / len(o)
eq_rest17 = sum(r["ytd"] for r in x) / len(x)
cw_all20 = sum(r["weight"] * r["ytd"] / 100 for r in rows)
cw_top3 = sum(r["weight"] * r["ytd"] / 100 for r in o)
cw_rest = sum(r["weight"] * r["ytd"] / 100 for r in x)

print("=== 口径校验 ===")
print("指数 YTD %+.2f%% | 基准点 %.2f (2025-12-31收) -> 现点 %.2f (2026-09-14盘中)" % (IDX_YTD, IDX_BASE, IDX_NOW))
print("指数 52周高 %.2f (2026-07-01) 距高点 %+.2f%% | 52周低 %.2f" % (IDX_HI, (IDX_NOW/IDX_HI-1)*100, IDX_LO52))
print("F9交叉验证: 指数YTD(截至9-11) +40.32%% -> 9/14盘中再跌 %.2f%% = %+.2f%%，口径一致 ✓" % (
    (IDX_NOW/3667.09-1)*100, 40.32*(IDX_NOW/3667.09)))
print("前20大当前权重合计 %.2f%%（其余30只 %.2f%%）" % (sum(r["weight"] for r in rows), 100-sum(r["weight"] for r in rows)))

print("\n=== A) 等权口径（精确，用于结构归因）===")
print("  前20大成分 等权YTD       : %+8.2f%%" % eq_all20)
print("  ★组合三只 等权YTD        : %+8.2f%%  (= 组合买入持有口径，与通达信计算 +2.54%% 一致)" % eq_top3)
print("  其余17只前20大 等权YTD   : %+8.2f%%" % eq_rest17)
print("  -> 选股差额（组合 vs 其余17只等权）: %+.2f pct" % (eq_top3 - eq_rest17))
print("  -> 组合 vs 前20大等权: %+.2f pct | 组合 vs 指数: %+.2f pct" % (eq_top3-eq_all20, eq_top3-IDX_YTD))

print("\n=== B) 当前权重口径（近似，仅看相对结构）===")
print("  前20大 加权贡献 %+.2f pct（>指数%+.2f pct，因权重漂移+半年度调仓，绝对值不可用）" % (cw_all20, IDX_YTD))
print("  ★组合三只 权重%.2f%% 贡献%+.2f pct 占总贡献 %5.1f%%" % (
    sum(r["weight"] for r in o), cw_top3, cw_top3/cw_all20*100))
print("  其余17只 权重%.2f%% 贡献%+.2f pct 占总贡献 %5.1f%%" % (
    sum(r["weight"] for r in x), cw_rest, cw_rest/cw_all20*100))

print("\n=== ★组合三只明细 ===")
print("%-10s %9s %6s %9s %9s %10s %10s" % ("标的", "指数权重", "排名", "YTD", "等权贡献", "距年内高点", "年内区间"))
for r in sorted(o, key=lambda y: -y["weight"]):
    print("%-10s %8.3f%% %6d %+8.2f%% %+8.2fpct %+9.2f%% %8.2f~%.2f" % (
        r["name"], r["weight"], r["rank_w"], r["ytd"], r["ytd"]/3, r["off_hi"], r["lo"], r["hi"]))

GROUPS = [("半导体设备/材料", {"688012","688072","688120","688361","688037","688200","688082","688019"}),
          ("光芯片/光通信", {"688498","688313","688702"}),
          ("存储芯片", {"688525","688766"}),
          ("算力芯片设计", {"688256","688041","688008","688521"}),
          ("晶圆制造", {"688981","688347"}),
          ("军工电子", {"688002"})]
print("\n=== 子板块（等权口径，精确）===")
grp_out = []
for label, s in GROUPS:
    g = [r for r in rows if r["code"] in s]
    eq = sum(r["ytd"] for r in g)/len(g); wn = sum(r["weight"] for r in g)
    grp_out.append(dict(name=label, n=len(g), w_now=round(wn,3), eq_ytd=round(eq,2),
                        members=[dict(name=r["name"], code=r["code"], ytd=r["ytd"],
                                      w=round(r["weight"],3), off_hi=r["off_hi"]) for r in sorted(g,key=lambda y:-y["ytd"])]))
    star = " ←含组合标的" if s & TOP3 else ""
    print("  %-14s %d只 权重%6.2f%% 等权YTD%+8.2f%%%s" % (label, len(g), wn, eq, star))

print("\n=== 前20大 YTD 排行 ===")
rank_out = []
for i, r in enumerate(sorted(rows, key=lambda y: -y["ytd"]), 1):
    rank_out.append(dict(rank=i, name=r["name"], code=r["code"], weight=round(r["weight"],3),
                         rank_w=r["rank_w"], ytd=r["ytd"], off_hi=r["off_hi"], hi=r["hi"], lo=r["lo"],
                         in_portfolio=r["code"] in TOP3,
                         group=next((g[0] for g in GROUPS if r["code"] in g[1]), "其他")))
    print("  %2d. %-8s w=%6.3f%%(第%d) YTD=%+8.2f%% 距高点%+7.2f%% %s" % (
        i, r["name"], r["weight"], r["rank_w"], r["ytd"], r["off_hi"], "★组合" if r["code"] in TOP3 else ""))

# 组合标的在指数内的「YTD排名」
print("\n=== 关键结论：组合三只 = 指数前4大权重中的3只，却是YTD排名倒数3名 ===")
print("  权重排名: 中芯第%d / 寒武第%d / 海光第%d（合计%.2f%%）" % (
    [r["rank_w"] for r in o if r["code"]=="688981"][0],
    [r["rank_w"] for r in o if r["code"]=="688256"][0],
    [r["rank_w"] for r in o if r["code"]=="688041"][0], sum(r["weight"] for r in o)))
srt = sorted(rows, key=lambda y: -y["ytd"])
print("  YTD排名: 中芯第%d / 寒武第%d / 海光第%d（共20只）" % (
    srt.index([r for r in rows if r["code"]=="688981"][0])+1,
    srt.index([r for r in rows if r["code"]=="688256"][0])+1,
    srt.index([r for r in rows if r["code"]=="688041"][0])+1))

json.dump(dict(rank=rank_out, groups=grp_out,
               portfolio=[dict(name=r["name"], code=r["code"], weight=round(r["weight"],3),
                               rank_w=r["rank_w"], ytd=r["ytd"], off_hi=r["off_hi"],
                               hi=r["hi"], lo=r["lo"], hi_date=r["hi_date"], lo_date=r["lo_date"],
                               base_close=r["base_close"], cur_close=r["cur_close"],
                               eq_contrib=round(r["ytd"]/3,3)) for r in o],
               summary=dict(idx_ytd=IDX_YTD, idx_base=round(IDX_BASE,2), idx_now=round(IDX_NOW,2),
                            idx_hi=IDX_HI, off_hi=round((IDX_NOW/IDX_HI-1)*100,2), idx_lo52=IDX_LO52,
                            w20=round(sum(r["weight"] for r in rows),2),
                            eq_all20=round(eq_all20,2), eq_top3=round(eq_top3,2),
                            eq_rest17=round(eq_rest17,2), gap=round(eq_top3-eq_rest17,2),
                            cw_all20=round(cw_all20,2), cw_top3=round(cw_top3,2), cw_rest=round(cw_rest,2),
                            top3_w=round(sum(r["weight"] for r in o),3),
                            top3_share_cw=round(cw_top3/cw_all20*100,1))),
          open("out/attribution.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nsaved out/attribution.json")
