import json

rows = json.load(open("out/components_final.json", encoding="utf-8"))["rows"]
IDX_YTD, IDX_NOW, IDX_HI = 38.04, 3607.588623, 5660.68
IDX_BASE = IDX_NOW / (1 + IDX_YTD/100)
TOP3 = {"688981", "688256", "688041"}

# 口径说明：科创芯片指数为「自由流通市值加权 + 单只权重上限」，年初真实权重无法从公开接口可靠还原，
# 故贡献一律采用【当前权重口径】，并标注其为近似（会因权重漂移高估涨幅大者的贡献）。
for r in rows:
    r["contrib_now"] = round(r["weight"] * r["ytd"] / 100, 3)   # 当前权重 × YTD
    r["mcap_yi"] = None
o = [r for r in rows if r["code"] in TOP3]
x = [r for r in rows if r["code"] not in TOP3]

c_top3 = sum(r["contrib_now"] for r in o)
c_rest = sum(r["contrib_now"] for r in x)
w_top3 = sum(r["weight"] for r in o)
w_rest = sum(r["weight"] for r in x)
wavg_top3 = c_top3 / (w_top3/100) / 100
wavg_rest = c_rest / (w_rest/100) / 100

print("=== 口径校验 ===")
print("指数 YTD %+.2f%% | 基准点 %.2f (2025-12-31) -> 现点 %.2f (2026-09-14盘中)" % (IDX_YTD, IDX_BASE, IDX_NOW))
print("指数 52周高 %.2f (2026-07-01) | 现价距高点 %+.2f%% | 52周低 2200.89" % (IDX_HI, (IDX_NOW/IDX_HI-1)*100))
print("前20大成分当前权重合计 %.2f%%，其余30只 %.2f%%" % (sum(r["weight"] for r in rows), 100-sum(r["weight"] for r in rows)))
print("前20大当前权重口径贡献合计 %+.2f pct（vs 指数实际 %+.2f pct，差 %+.2f pct 为权重漂移+未覆盖成分影响）" % (
    c_top3+c_rest, IDX_YTD, c_top3+c_rest-IDX_YTD))

print("\n=== ★本组合三只（当前权重口径）===")
print("%-10s %8s %8s %10s %10s %9s" % ("标的", "指数权重", "权重排名", "YTD", "贡献(近似)", "距年内高点"))
for i, r in enumerate(sorted(rows, key=lambda y: -y["weight"]), 1):
    r["rank_w"] = i
for r in sorted(o, key=lambda y: -y["weight"]):
    print("%-10s %7.3f%% %8d %+9.2f%% %+9.2fpct %+8.2f%%" % (
        r["name"], r["weight"], r["rank_w"], r["ytd"], r["contrib_now"], r["off_hi"]))
print("%-10s %7.3f%% %8s %+9.2f%% %+9.2fpct" % (
    "合计/加权", w_top3, "-", wavg_top3, c_top3))
print("其余17只前20大 %7.3f%% %8s %+9.2f%% %+9.2fpct" % (w_rest, "-", wavg_rest, c_rest))

# 反事实组合：若持有其余17只（按当前权重归一）
print("\n=== 反事实对照 ===")
print("若年初等权买入其余17只前20大：YTD %+.2f%%（简单平均）" % (sum(r["ytd"] for r in x)/len(x)))
print("若年初按当前权重买入其余17只：YTD %+.2f%%" % wavg_rest)
print("若年初等权买入本组合三只：YTD %+.2f%%" % (sum(r["ytd"] for r in o)/3))
print("差额：本组合 vs 其余17只等权 = %+.2f pct" % (sum(r["ytd"] for r in o)/3 - sum(r["ytd"] for r in x)/len(x)))

GROUPS = [("半导体设备/材料", {"688012","688072","688120","688361","688037","688200","688082","688019"}),
          ("光芯片/光通信", {"688498","688313","688702"}),
          ("存储芯片", {"688525","688766"}),
          ("算力芯片设计", {"688256","688041","688008","688521"}),
          ("晶圆制造", {"688981","688347"}),
          ("军工电子", {"688002"})]
print("\n=== 子板块归因（当前权重口径）===")
grp_out = []
for label, s in GROUPS:
    g = [r for r in rows if r["code"] in s]
    wn = sum(r["weight"] for r in g); con = sum(r["contrib_now"] for r in g)
    wavg = con/(wn/100)/100 if wn else 0
    grp_out.append(dict(name=label, w_now=round(wn,3), contrib=round(con,3), wavg_ytd=round(wavg,2),
                        n=len(g), members=[dict(name=r["name"], code=r["code"], ytd=r["ytd"],
                                                w=round(r["weight"],3), contrib=round(r["contrib_now"],3),
                                                off_hi=r["off_hi"]) for r in sorted(g, key=lambda y:-y["ytd"])]))
    print("  %-14s 权重%6.2f%% 加权YTD%+8.2f%% 贡献%+7.2fpct (%d只)" % (label, wn, wavg, con, len(g)))

print("\n=== 前20大 YTD 排行 ===")
rank_out = []
for i, r in enumerate(sorted(rows, key=lambda y: -y["ytd"]), 1):
    rank_out.append(dict(rank=i, name=r["name"], code=r["code"], weight=round(r["weight"],3),
                         ytd=r["ytd"], contrib=r["contrib_now"], off_hi=r["off_hi"],
                         in_portfolio=r["code"] in TOP3, group=next(
                             (g[0] for g in GROUPS if r["code"] in g[1]), "其他")))
    print("  %2d. %-8s w=%6.3f%% YTD=%+8.2f%% 贡献=%+7.2fpct 距高点%+7.2f%% %s" % (
        i, r["name"], r["weight"], r["ytd"], r["contrib_now"], r["off_hi"], "★组合" if r["code"] in TOP3 else ""))

json.dump(dict(rank=rank_out, groups=grp_out,
               summary=dict(idx_ytd=IDX_YTD, idx_base=round(IDX_BASE,2), idx_now=round(IDX_NOW,2),
                            idx_hi=IDX_HI, off_hi=round((IDX_NOW/IDX_HI-1)*100,2), idx_lo52=2200.89,
                            w20=round(sum(r["weight"] for r in rows),2),
                            c20=round(c_top3+c_rest,2),
                            top3_w=round(w_top3,3), top3_con=round(c_top3,3), top3_wavg=round(wavg_top3,2),
                            rest17_w=round(w_rest,3), rest17_con=round(c_rest,3), rest17_wavg=round(wavg_rest,2),
                            rest17_eq=round(sum(r["ytd"] for r in x)/len(x),2),
                            top3_eq=round(sum(r["ytd"] for r in o)/3,2),
                            gap=round(sum(r["ytd"] for r in o)/3 - sum(r["ytd"] for r in x)/len(x),2))),
          open("out/attribution.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nsaved out/attribution.json")
