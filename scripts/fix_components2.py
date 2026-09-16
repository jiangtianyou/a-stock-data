import json, urllib.request, ssl, time

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
      "Referer": "https://gu.qq.com/"}
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=ctx))

def tencent_kline(code):
    url = (f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?"
           f"param=sh{code},day,2025-11-20,2026-09-15,320,qfq")
    for t in range(4):
        try:
            with opener.open(urllib.request.Request(url, headers=UA), timeout=25) as r:
                d = json.loads(r.read().decode("utf-8"))
            node = d["data"]["sh" + code]
            ks = node.get("qfqday") or node.get("day")
            if ks:
                out = []
                for k in ks:
                    out.append((k[0].replace("-", ""), float(k[2]), float(k[3]), float(k[4]), float(k[1])))
                return out
        except Exception as e:
            err = e
        time.sleep(1.5)
    print("  FAIL", code, err); return []

MISS = [("688361", "中科飞测", 2.889), ("688525", "佰维存储", 2.862), ("688002", "睿创微纳", 2.240),
        ("688037", "芯源微", 1.922), ("688313", "仕佳光子", 1.609), ("688702", "盛科通信", 1.545),
        ("688766", "普冉股份", 1.385)]

rows = json.load(open("out/components.json", encoding="utf-8"))
have = {r["code"] for r in rows}

# 用中芯国际做腾讯 vs 通达信口径校验（688981 通达信基准 122.83）
print("=== 口径校验：腾讯qfq vs 通达信前复权（688981 中芯国际）===")
kv = tencent_kline("688981")
if kv:
    b = [r for r in kv if r[0] <= "20251231"][-1]
    print("  腾讯: 基准%s@%.2f 现价%.2f YTD=%+.2f%%  | 通达信: 基准122.83 现价114.17 YTD=-7.02%%" % (
        b[0], b[1], kv[-1][1], (kv[-1][1]/b[1]-1)*100))
    # 校验 688012
    kv2 = tencent_kline("688012")
    if kv2:
        b2 = [r for r in kv2 if r[0] <= "20251231"][-1]
        print("  688012 中微公司 腾讯: 基准%s@%.2f 现价%.2f YTD=%+.2f%%（东财口径 12-31 缺数据，原记 +77.70%%）" % (
            b2[0], b2[1], kv2[-1][1], (kv2[-1][1]/b2[1]-1)*100))

print("\n=== 补齐 7 只（腾讯 qfq）===")
for code, name, w in MISS:
    if code in have: continue
    kk = tencent_kline(code)
    if not kk: continue
    base = [r for r in kk if r[0] <= "20251231"]
    if not base: print("NOBASE", code, name); continue
    b, cur = base[-1], kk[-1]
    seg = [r for r in kk if r[0] >= "20260101"]
    ytd = (cur[1]/b[1]-1)*100
    hi = max(r[2] for r in seg); lo = min(r[3] for r in seg)
    rows.append(dict(code=code, name=name, weight=w, base_date=b[0], base_close=b[1],
                     cur_date=cur[0], cur_close=cur[1], ytd=round(ytd,2),
                     contrib=round(w*ytd/100,3), hi=hi, hi_date=[r[0] for r in seg if r[2]==hi][0],
                     lo=lo, lo_date=[r[0] for r in seg if r[3]==lo][0], off_hi=round((cur[1]/hi-1)*100,2)))
    print("  %-8s %-8s w=%5.3f%% base=%s@%.2f -> %s@%.2f YTD=%+8.2f%% 贡献=%+7.3fpct" % (
        code, name, w, b[0], b[1], cur[0], cur[1], ytd, rows[-1]["contrib"]))
    time.sleep(0.8)

# 修正 688012 基准（东财 12 月数据断档）
kv2 = tencent_kline("688012")
if kv2:
    b2 = [r for r in kv2 if r[0] <= "20251231"][-1]
    seg = [r for r in kv2 if r[0] >= "20260101"]
    for r in rows:
        if r["code"] == "688012" and r["base_date"] != b2[0]:
            ytd = (kv2[-1][1]/b2[1]-1)*100
            print("\n修正 688012 中微公司: %s@%.2f -> YTD %+.2f%% (原 %.2f%%)" % (b2[0], b2[1], ytd, r["ytd"]))
            r.update(base_date=b2[0], base_close=b2[1], cur_close=kv2[-1][1], ytd=round(ytd,2),
                     contrib=round(r["weight"]*ytd/100,3), hi=max(x[2] for x in seg),
                     lo=min(x[3] for x in seg), off_hi=round((kv2[-1][1]/max(x[2] for x in seg)-1)*100,2))

rows.sort(key=lambda x: -x["weight"])
json.dump(rows, open("out/components.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

TOP3 = {"688981", "688256", "688041"}
o = [r for r in rows if r["code"] in TOP3]; x = [r for r in rows if r["code"] not in TOP3]
IDX_YTD = 38.04
print("\n" + "="*78)
print("归因汇总：覆盖 %d/20 只成分，权重 %.2f%%（指数剩余 %.2f%% 由第21-50名小权重股构成）" % (
    len(rows), sum(r["weight"] for r in rows), 100-sum(r["weight"] for r in rows)))
print("="*78)
print("指数 YTD(通达信口径) : %+.2f pct" % IDX_YTD)
print("前20大加权贡献合计   : %+.2f pct  (占指数涨幅 %.0f%%)" % (
    sum(r["contrib"] for r in rows), sum(r["contrib"] for r in rows)/IDX_YTD*100))
print("★组合三只(24.18%%权重): 贡献 %+.2f pct | 加权YTD %+.2f%%" % (
    sum(r["contrib"] for r in o), sum(r["ytd"]*r["weight"] for r in o)/sum(r["weight"] for r in o)))
print("  其余%d只(%.2f%%权重): 贡献 %+.2f pct | 加权YTD %+.2f%%" % (
    len(x), sum(r["weight"] for r in x), sum(r["contrib"] for r in x),
    sum(r["ytd"]*r["weight"] for r in x)/sum(r["weight"] for r in x)))
print("\n--- 前20大成分 YTD 排行 ---")
for i, r in enumerate(sorted(rows, key=lambda y: -y["ytd"]), 1):
    tag = " ★组合" if r["code"] in TOP3 else ""
    print("  %2d. %-8s w=%5.3f%% YTD=%+8.2f%% 贡献=%+7.3fpct 距高点%+7.2f%%%s" % (
        i, r["name"], r["weight"], r["ytd"], r["contrib"], r["off_hi"], tag))

GROUPS = [("半导体设备/材料", {"688012","688072","688120","688361","688037","688200","688082","688019"}),
          ("光芯片/光通信", {"688498","688313","688702"}),
          ("存储芯片", {"688525","688766"}),
          ("算力芯片设计", {"688256","688041","688008","688521"}),
          ("晶圆制造", {"688981","688347"}),
          ("军工电子/其他", {"688002"})]
print("\n--- 子板块加权YTD ---")
for label, s in GROUPS:
    g = [r for r in rows if r["code"] in s]
    if g:
        wsum = sum(r["weight"] for r in g)
        print("  %-16s 权重%6.2f%% 加权YTD %+8.2f%% 贡献 %+7.2fpct" % (
            label, wsum, sum(r["ytd"]*r["weight"] for r in g)/wsum, sum(r["contrib"] for r in g)))
json.dump(dict(rows=rows), open("out/components_final.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
