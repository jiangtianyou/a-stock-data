import json, urllib.request, urllib.parse, ssl, time, os

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
HOSTS = ["push2his.eastmoney.com", "push2delay.eastmoney.com", "91.push2his.eastmoney.com"]

def kline(secid, beg="20251201", end="20260914", tries=4):
    last = None
    for t in range(tries):
        host = HOSTS[t % len(HOSTS)]
        url = (f"https://{host}/api/qt/stock/kline/get?" + urllib.parse.urlencode({
            "secid": secid, "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57",
            "klt": "101", "fqt": "1", "beg": beg, "end": end, "lmt": "300"}))
        try:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}),
                                                 urllib.request.HTTPSHandler(context=ctx))
            with opener.open(urllib.request.Request(url, headers=UA), timeout=25) as r:
                d = json.loads(r.read().decode("utf-8"))
            ks = (d.get("data") or {}).get("klines") or []
            if ks:
                out = []
                for line in ks:
                    p = line.split(",")
                    out.append((p[0].replace("-", ""), float(p[2]), float(p[3]), float(p[4]), float(p[5])))
                return out
            last = "empty"
        except Exception as e:
            last = str(e)
        time.sleep(2.0 + t * 1.5)
    print("   FAIL", secid, last)
    return []

MISSING = [("688347", "华虹宏力", 3.361), ("688120", "华海清科", 3.322), ("688361", "中科飞测", 2.889),
           ("688525", "佰维存储", 2.862), ("688002", "睿创微纳", 2.240), ("688037", "芯源微", 1.922),
           ("688313", "仕佳光子", 1.609), ("688702", "盛科通信", 1.545), ("688766", "普冉股份", 1.385)]

existing = json.load(open("out/components.json", encoding="utf-8"))
have = {r["code"] for r in existing}

# 先诊断 688012 十二月数据是否断档
print("=== 688012 中微公司 2025-12 K线完整性诊断 ===")
k = kline("1.688012", beg="20251201", end="20260110")
dec = [r for r in k if r[0] <= "20251231"]
for r in dec: print("   ", r[0], r[1])
print("   12月交易日数:", len(dec), "| 2025-12-31收盘:", dec[-1][1] if dec else None)

# 补齐缺失
print("\n=== 补齐缺失成分股 ===")
for code, name, w in MISSING:
    if code in have: continue
    kk = kline(f"1.{code}")
    if not kk: continue
    base = [r for r in kk if r[0] <= "20251231"]
    if not base:
        print("NOBASE", code, name); continue
    b, cur = base[-1], kk[-1]
    ytd = (cur[1] / b[1] - 1) * 100
    seg = [r for r in kk if r[0] >= "20260101"]
    hi = max(r[2] for r in seg); hid = [r[0] for r in seg if r[2] == hi][0]
    lo = min(r[3] for r in seg); lod = [r[0] for r in seg if r[3] == lo][0]
    existing.append(dict(code=code, name=name, weight=w, base_date=b[0], base_close=b[1],
                         cur_date=cur[0], cur_close=cur[1], ytd=round(ytd, 2),
                         contrib=round(w * ytd / 100, 3), hi=hi, hi_date=hid, lo=lo, lo_date=lod,
                         off_hi=round((cur[1]/hi-1)*100, 2)))
    print("  %-8s %-8s w=%5.3f%% base=%s@%.2f -> %.2f YTD=%+8.2f%% 贡献=%+7.3fpct" % (
        code, name, w, b[0], b[1], cur[1], ytd, existing[-1]["contrib"]))
    time.sleep(1.5)

# 修正 688012（若基准日不是 20251231）
for r in existing:
    if r["code"] == "688012" and dec and r["base_date"] != dec[-1][0]:
        kk = kline("1.688012")
        b2 = [x for x in kk if x[0] <= "20251231"][-1]
        cur = kk[-1]
        seg = [x for x in kk if x[0] >= "20260101"]
        hi = max(x[2] for x in seg); lo = min(x[3] for x in seg)
        ytd = (cur[1] / b2[1] - 1) * 100
        print("\n修正 688012: 原基准 %s@%.2f YTD=%.2f%% -> 新基准 %s@%.2f YTD=%.2f%%" % (
            r["base_date"], r["base_close"], r["ytd"], b2[0], b2[1], ytd))
        r.update(base_date=b2[0], base_close=b2[1], cur_close=cur[1], ytd=round(ytd, 2),
                 contrib=round(r["weight"] * ytd / 100, 3), hi=hi, lo=lo, off_hi=round((cur[1]/hi-1)*100, 2))

existing.sort(key=lambda x: -x["weight"])
json.dump(existing, open("out/components.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

TOP3 = {"688981", "688256", "688041"}
o = [r for r in existing if r["code"] in TOP3]
x = [r for r in existing if r["code"] not in TOP3]
print("\n=== 归因汇总（前%d大成分，权重合计%.2f%%）===" % (len(existing), sum(r["weight"] for r in existing)))
print("指数 YTD 实际涨幅: +38.04%（通达信口径, 20251231->20260914盘中）")
print("组合三只 权重%.2f%% 贡献%+.3fpct  加权YTD%+.2f%%" % (
    sum(r["weight"] for r in o), sum(r["contrib"] for r in o),
    sum(r["ytd"]*r["weight"] for r in o)/sum(r["weight"] for r in o)))
print("其余%d只 权重%.2f%% 贡献%+.3fpct  加权YTD%+.2f%%" % (
    len(x), sum(r["weight"] for r in x), sum(r["contrib"] for r in x),
    sum(r["ytd"]*r["weight"] for r in x)/sum(r["weight"] for r in x)))
print("\n--- 全部成分 YTD 排行 ---")
for r in sorted(existing, key=lambda y: -y["ytd"]):
    tag = "★本组合" if r["code"] in TOP3 else ""
    print("  %-8s w=%5.3f%% YTD=%+8.2f%% 贡献=%+7.3fpct %s" % (r["name"], r["weight"], r["ytd"], r["contrib"], tag))
# 板块分组
EQ = {"688012", "688072", "688120", "688361", "688037", "688200", "688082", "688019"}
MEM = {"688525", "688766"}
OPT = {"688498", "688313", "688702"}
for label, s in [("半导体设备+材料", EQ), ("存储芯片", MEM), ("光芯片/光模块", OPT), ("设计(算力CPU/GPU)", {"688256","688041","688008","688521"}), ("晶圆制造", {"688981","688347"})]:
    g = [r for r in existing if r["code"] in s]
    if g: print("  %-18s 权重%.2f%% 平均YTD%+7.2f%%" % (label, sum(r["weight"] for r in g), sum(r["ytd"] for r in g)/len(g)))
