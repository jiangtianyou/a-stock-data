import json, urllib.request, ssl, time, re

rows = json.load(open("out/components_final.json", encoding="utf-8"))["rows"]
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=ctx))

codes = [r["code"] for r in rows] + ["000685", "000688"]
q = ",".join("sh" + c for c in codes)
url = f"https://qt.gtimg.cn/q={q}"
now = {}
for t in range(4):
    try:
        with opener.open(urllib.request.Request(url, headers=UA), timeout=25) as resp:
            txt = resp.read().decode("gbk", errors="ignore")
        for m in re.finditer(r'v_sh(\d{6})="([^"]*)"', txt):
            f = m.group(2).split("~")
            if len(f) > 4:
                now[m.group(1)] = dict(price=float(f[3]), pct=float(f[32]) if f[32] else 0.0,
                                       date=f[30][:8], name=f[1])
        break
    except Exception as e:
        err = e; time.sleep(2)
print("拿到 %d 个实时快照 | 数据时间 %s" % (len(now), list(now.values())[0]["date"] if now else "?"))

# 指数
IDX = now["000685"]; KC50 = now["000688"]
print("科创芯片 000685 收盘 %.2f (%+.2f%%) | 科创50 000688 收盘 %.2f (%+.2f%%)" % (
    IDX["price"], IDX["pct"], KC50["price"], KC50["pct"]))

# 成分股：用已有基准价(20251231前复权) + 9-14收盘价
for r in rows:
    r["cur_close_0914"] = now[r["code"]]["price"]
    r["ytd_final"] = round((r["cur_close_0914"] / r["base_close"] - 1) * 100, 2)
    r["contrib_final"] = round(r["weight"] * r["ytd_final"] / 100, 3)
    r["pct_today"] = now[r["code"]]["pct"]
    print("  %-8s 基准%s@%.2f -> 9/14收 %.2f (%+.2f%%今日) YTD=%+8.2f%% (原%+8.2f%%)" % (
        r["name"], r["base_date"], r["base_close"], r["cur_close_0914"], r["pct_today"],
        r["ytd_final"], r["ytd"]))

IDX_BASE = 3607.588623 / 1.3804   # 盘中反推的基准，需改用真实收盘基准
# 从通达信落盘文件读指数真实基准价
D = r"C:\Users\Administrator\.workbuddy\projects\d-Desktop-Playground-a-stock-data\f4800af3-610a-497f-a9b6-fb135319d10e\tool-results"
raw = open(D + r"\mcp-tdx-connector-tdx_kline-1789368485688-da60c7.txt", encoding="utf-8", errors="ignore").read()
obj, _ = json.JSONDecoder().raw_decode(raw[raw.find("{"):])
irows = {x["Data"]: float(x["Close"]) for x in obj["Rows"]}
IDX_BASE_CLOSE = irows["20251231"]
IDX_YTD_FINAL = round((IDX["price"] / IDX_BASE_CLOSE - 1) * 100, 2)
KC50_BASE = None
print("\n指数基准(2025-12-31收盘) %.2f -> 9/14收盘 %.2f | YTD %+.2f%%（原盘中口径 +38.04%%）" % (
    IDX_BASE_CLOSE, IDX["price"], IDX_YTD_FINAL))

TOP3 = {"688981", "688256", "688041"}
o = [r for r in rows if r["code"] in TOP3]; x = [r for r in rows if r["code"] not in TOP3]
print("\n=== 最终口径（9-14收盘）===")
for r in o:
    print("  %-8s w=%6.3f%% YTD=%+8.2f%% 距高点=%+7.2f%%" % (r["name"], r["weight"], r["ytd_final"],
          (r["cur_close_0914"]/r["hi"]-1)*100))
    r["off_hi_final"] = round((r["cur_close_0914"]/r["hi"]-1)*100, 2)
print("  组合等权YTD %+.2f%% | 指数 %+.2f%% | 超额 %+.2f pct" % (
    sum(r["ytd_final"] for r in o)/3, IDX_YTD_FINAL, sum(r["ytd_final"] for r in o)/3 - IDX_YTD_FINAL))
print("  其余17只等权YTD %+.2f%%" % (sum(r["ytd_final"] for r in x)/len(x)))

for r in rows:
    r["off_hi_final"] = round((r["cur_close_0914"]/r["hi"]-1)*100, 2)
json.dump(dict(rows=rows, idx=dict(base=IDX_BASE_CLOSE, close=IDX["price"], ytd=IDX_YTD_FINAL,
                                   pct_today=IDX["pct"], hi=5660.68, lo52=2200.89),
               kc50=dict(close=KC50["price"], pct_today=KC50["pct"])),
          open("out/components_close.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nsaved out/components_close.json")
