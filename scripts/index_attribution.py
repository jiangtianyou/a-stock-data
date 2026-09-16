import json, urllib.request, urllib.parse, ssl, time

# 科创芯片指数(000685)成分股权重（通达信 F9, 2026-09-14）
COMP = [
    ("688012", "中微公司", 8.738, 1), ("688981", "中芯国际", 8.444, 1),
    ("688256", "寒武纪", 8.134, 1), ("688041", "海光信息", 7.602, 1),
    ("688008", "澜起科技", 7.566, 1), ("688498", "源杰科技", 4.917, 1),
    ("688072", "拓荆科技", 4.320, 1), ("688347", "华虹宏力", 3.361, 1),
    ("688120", "华海清科", 3.322, 1), ("688361", "中科飞测", 2.889, 1),
    ("688525", "佰维存储", 2.862, 1), ("688521", "芯原股份", 2.713, 1),
    ("688002", "睿创微纳", 2.240, 1), ("688037", "芯源微", 1.922, 1),
    ("688200", "华峰测控", 1.791, 1), ("688313", "仕佳光子", 1.609, 1),
    ("688702", "盛科通信", 1.545, 1), ("688082", "盛美上海", 1.407, 1),
    ("688019", "安集科技", 1.401, 1), ("688766", "普冉股份", 1.385, 1),
]

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE

def kline(secid, beg="20251218", end="20260914"):
    """东财日K，fqt=1 前复权"""
    url = ("https://push2his.eastmoney.com/api/qt/stock/kline/get?"
           + urllib.parse.urlencode({
               "secid": secid, "fields1": "f1,f2,f3,f4,f5,f6",
               "fields2": "f51,f52,f53,f54,f55,f56,f57",
               "klt": "101", "fqt": "1", "beg": beg, "end": end, "lmt": "200"}))
    req = urllib.request.Request(url, headers=UA)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}),
                                         urllib.request.HTTPSHandler(context=ctx))
    with opener.open(req, timeout=20) as r:
        d = json.loads(r.read().decode("utf-8"))
    ks = (d.get("data") or {}).get("klines") or []
    out = []
    for line in ks:
        p = line.split(",")
        out.append((p[0].replace("-", ""), float(p[2]), float(p[3]), float(p[4]), float(p[5])))
    return out

rows = []
for code, name, w, mkt in COMP:
    secid = f"{mkt}.{code}"
    try:
        k = kline(secid)
    except Exception as e:
        print("ERR", code, name, e); continue
    if not k:
        print("EMPTY", code, name); continue
    # 基准 = 2025-12-31（2025 最后一个交易日）
    base = [r for r in k if r[0] <= "20251231"]
    if not base:
        print("NOBASE", code, name, k[0][0]); continue
    b = base[-1]
    cur = k[-1]
    ytd = (cur[1] / b[1] - 1) * 100
    hi = max(r[2] for r in k if r[0] >= "20260101"); hid = [r[0] for r in k if r[0] >= "20260101" and r[2] == hi][0]
    lo = min(r[3] for r in k if r[0] >= "20260101"); lod = [r[0] for r in k if r[0] >= "20260101" and r[3] == lo][0]
    rows.append(dict(code=code, name=name, weight=w, base_date=b[0], base_close=b[1],
                     cur_date=cur[0], cur_close=cur[1], ytd=round(ytd, 2),
                     contrib=round(w * ytd / 100, 3), hi=hi, hi_date=hid, lo=lo, lo_date=lod,
                     off_hi=round((cur[1]/hi-1)*100, 2)))
    print("%-8s %-8s w=%5.3f%% base=%s@%.2f -> %s@%.2f YTD=%+8.2f%% 贡献=%+7.3fpct 距高点%+7.2f%%" % (
        code, name, w, b[0], b[1], cur[0], cur[1], ytd, rows[-1]["contrib"], rows[-1]["off_hi"]))
    time.sleep(0.4)

json.dump(rows, open("out/components.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
tot_w = sum(r["weight"] for r in rows)
tot_c = sum(r["contrib"] for r in rows)
print("\n前20大成分权重合计 %.3f%%，加权贡献合计 %+.3f pct（约占指数YTD涨幅的 %.0f%%）" % (
    tot_w, tot_c, tot_c / 38.04 * 100))
TOP3 = [r for r in rows if r["code"] in ("688981", "688256", "688041")]
print("本组合三只（中芯/寒武/海光）权重合计 %.3f%%，贡献 %+.3f pct" % (
    sum(r["weight"] for r in TOP3), sum(r["contrib"] for r in TOP3)))
OTH = [r for r in rows if r not in TOP3]
print("其余17只权重合计 %.3f%%，贡献 %+.3f pct，平均YTD %+.2f%%" % (
    sum(r["weight"] for r in OTH), sum(r["contrib"] for r in OTH),
    sum(r["ytd"]*r["weight"] for r in OTH)/sum(r["weight"] for r in OTH)))
print("\n--- 其余权重股 YTD 排行 ---")
for r in sorted(OTH, key=lambda x: -x["ytd"]):
    print("  %-8s w=%5.3f%% YTD=%+8.2f%% 贡献=%+7.3fpct" % (r["name"], r["weight"], r["ytd"], r["contrib"]))
