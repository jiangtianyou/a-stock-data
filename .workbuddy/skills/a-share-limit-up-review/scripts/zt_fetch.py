# -*- coding: utf-8 -*-
"""A股涨停复盘 · 数据抓取（今日 vs 昨日）

用法：
    python zt_fetch.py                 # 默认：今日 / 上一交易日（仅按周末回退，节假日需显式传入）
    python zt_fetch.py 20260916 20260915

三源交叉：
  同花顺 dataapi  -> 涨停池（唯一带 reason_type 涨停原因）、炸板池、跌停池、板块涨幅、指数日线
  东财 push2ex    -> 涨停/炸板/跌停池（连板数 lbc、封单 fund、成交额 amount、行业 hybk）
  腾讯 qt.gtimg   -> 指数与个股快照（成交额、换手、市值）

落盘：out/zt_review_{D0}.json（**全部成功才覆盖**，写 .tmp 再 os.replace）
"""
import urllib.request, json, ssl, time, os, sys, re, datetime

# 数据根目录：优先环境变量 ZT_ROOT，否则取当前工作目录
# （从项目根调用时，结果落 <项目>/out/，不会污染 skill 自身目录）
ROOT = os.environ.get("ZT_ROOT") or os.getcwd()
OUT = os.path.join(ROOT, "out")
os.makedirs(OUT, exist_ok=True)

ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=ctx))

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
UT = "7eea3edcaed734bea9cbfc24409ed989"
FIELD = "199112,10,9001,330323,330324,330325,9002,330329,133971,133970,1968584,3475914,9003,9004"

def get(url, referer, tries=3, sleep=1.2, enc="utf-8"):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer})
            with OPENER.open(req, timeout=20) as r:
                return r.read().decode(enc, "ignore")
        except Exception:
            if i == tries - 1:
                return None
            time.sleep(sleep * (i + 1))
    return None

# ---------------- 日期 ----------------
def prev_weekday(ds):
    """前一工作日（仅按周末回退；遇节假日必须显式传参）"""
    d = datetime.datetime.strptime(ds, "%Y%m%d").date() - datetime.timedelta(days=1)
    while d.weekday() >= 5:
        d -= datetime.timedelta(days=1)
    return d.strftime("%Y%m%d")

def resolve_dates(argv):
    if len(argv) >= 2:
        return argv[0], argv[1]
    if len(argv) == 1:
        return argv[0], prev_weekday(argv[0])
    d0 = datetime.date.today().strftime("%Y%m%d")
    return d0, prev_weekday(d0)

# ---------------- 同花顺：涨停 / 炸板 / 跌停池 ----------------
def ths_pool(date, kind):
    url = (f"https://data.10jqka.com.cn/dataapi/limit_up/{kind}?page=1&limit=200&field={FIELD}"
           f"&filter=HS,GEM2STAR&order_field=330324&order_type=0&date={date}")
    # Referer 必须是根路径；用 /market/longhu/ 会返回 0 条
    t = get(url, "https://data.10jqka.com.cn/")
    if not t:
        return None
    try:
        d = json.loads(t)
    except Exception:
        return None
    data = d.get("data") or {}
    return {
        # limit_up_count / limit_down_count 为 {today:{num,history_num,rate,open_num}, yesterday:{...}}
        "total": data.get("limit_up_count"),
        "limit_down_count": data.get("limit_down_count"),
        "date": data.get("date"),
        "trade_status": data.get("trade_status"),
        "info": data.get("info") or [],
    }

def ths_block_top(date):
    url = f"https://data.10jqka.com.cn/dataapi/limit_up/block_top?filter=HS,GEM2STAR&date={date}"
    t = get(url, "https://data.10jqka.com.cn/")
    if not t:
        return None
    try:
        return (json.loads(t).get("data") or [])
    except Exception:
        return None

# ---------------- 同花顺指数日线（含成交额，用于昨日/前日对比） ----------------
THS_IDX = {"zs_1A0001": "上证指数", "zs_399001": "深证成指",
           "zs_399006": "创业板指", "zs_1B0688": "科创50"}

def ths_index_line(code):
    url = f"http://d.10jqka.com.cn/v6/line/{code}/01/last.js"
    t = get(url, "https://www.10jqka.com.cn/")
    if not t:
        return None
    m = re.search(r'"data":"([^"]+)"', t)
    nm = re.search(r'"name":"([^"]*)"', t)
    rows = []
    if m:
        for r in m.group(1).split(";"):
            p = r.split(",")
            if len(p) >= 7 and p[1] and p[4]:
                rows.append({"date": p[0], "open": p[1], "high": p[2], "low": p[3],
                             "close": p[4], "vol": p[5], "amt": p[6]})
    return {"code": code,
            "name": (json.loads('"' + nm.group(1) + '"') if nm else THS_IDX.get(code, code)),
            "rows": rows[-8:]}

# ---------------- 东财：涨停 / 炸板 / 跌停池 ----------------
def em_pool(date, kind):
    url = (f"https://push2ex.eastmoney.com/getTopic{kind}Pool?ut={UT}&dpt=wz.ztzt"
           f"&Pageindex=0&pagesize=300&sort=fbt%3Aasc&date={date}&_={int(time.time()*1000)}")
    t = get(url, "https://quote.eastmoney.com/")
    if not t:
        return None
    try:
        d = json.loads(t)
    except Exception:
        return None
    data = d.get("data") or {}
    return {"tc": data.get("tc"), "qdate": data.get("qdate"), "pool": data.get("pool") or []}

# ---------------- 腾讯：批量行情 ----------------
def tx_quotes(codes):
    """codes: ['sh000001','sz300750'] -> {code: {...}}；返回 GBK，必须 decode('gbk')"""
    res = {}
    for i in range(0, len(codes), 50):
        batch = codes[i:i + 50]
        url = "https://qt.gtimg.cn/q=" + ",".join(batch)
        t = get(url, "https://gu.qq.com/", enc="gbk")
        if not t:
            print("   ! tx batch fail", i); continue
        for line in t.split(";"):
            line = line.strip()
            if not line or "=" not in line:
                continue
            key = line.split("=")[0].replace("v_", "").strip()
            body = line.split("=", 1)[1].strip().strip('"')
            f = body.split("~")
            if len(f) < 50:
                continue
            def fl(idx):
                try: return float(f[idx])
                except Exception: return None
            res[key] = {
                "name": f[1], "code": f[2], "price": fl(3), "prev": fl(4), "open": fl(5),
                "chg": fl(31), "pct": fl(32), "high": fl(33), "low": fl(34),
                "amount_wan": fl(37), "turnover": fl(38), "pe": fl(39),
                "amp": fl(43), "float_mv": fl(44), "total_mv": fl(45),
            }
        time.sleep(0.3)
    return res

def sym_of(code, market=None):
    if code.startswith(("60", "68", "5", "11", "9")):
        return "sh" + code
    if code.startswith(("00", "30", "12", "15", "16", "18", "20")):
        return "sz" + code
    if code.startswith(("43", "83", "87", "92")):
        return "bj" + code
    if market == 1: return "sh" + code
    return "sz" + code

INDEXES = {
    "sh000001": "上证指数", "sz399001": "深证成指", "sz399006": "创业板指",
    "sh000688": "科创50", "bj899050": "北证50", "sh000300": "沪深300",
    "sh000852": "中证1000", "sh000905": "中证500", "sz399303": "国证2000",
    "sh000016": "上证50", "sz399005": "中小100",
}

if __name__ == "__main__":
    D0, D1 = resolve_dates(sys.argv[1:])
    print(f"== 复盘 {D0} 对比 {D1} ==")
    bundle = {"D0": D0, "D1": D1, "dates": {}, "indexes": {},
              "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")}

    for d in [D0, D1]:
        print(f"== {d} ==")
        rec = {}
        rec["ths_zt"] = ths_pool(d, "limit_up_pool")
        print("  ths 涨停:", len((rec["ths_zt"] or {}).get("info") or []),
              "limit_up_count:", (rec["ths_zt"] or {}).get("total"))
        time.sleep(1.0)
        rec["ths_zb"] = ths_pool(d, "open_limit_pool")
        print("  ths 炸板:", len((rec["ths_zb"] or {}).get("info") or []))
        time.sleep(1.0)
        rec["ths_dt"] = ths_pool(d, "limit_down_pool")
        print("  ths 跌停:", len((rec["ths_dt"] or {}).get("info") or []))
        time.sleep(1.0)
        rec["ths_block"] = ths_block_top(d)
        print("  ths 板块:", len(rec["ths_block"] or []))
        time.sleep(1.0)
        for k in ["ZT", "ZB", "DT"]:
            rec["em_" + k] = em_pool(d, k)
            print(f"  em {k}:", len((rec["em_" + k] or {}).get("pool") or []))
            time.sleep(0.6)
        bundle["dates"][d] = rec

    print("== 指数快照 ==")
    bundle["indexes"] = tx_quotes(list(INDEXES.keys()))
    for k, v in bundle["indexes"].items():
        print(f"  {k} {v['name']}: {v['pct']}% 额={v['amount_wan']}万 价={v['price']}")

    print("== 指数日线（含成交额） ==")
    bundle["index_hist"] = {}
    for c in THS_IDX:
        h = ths_index_line(c)
        bundle["index_hist"][c] = h
        print(f"  {h['name']}: last={h['rows'][-1]}" if (h and h["rows"]) else f"  {c} FAIL")
        time.sleep(0.6)

    # 昨日涨停股今日行情（晋级率/溢价）
    y = (bundle["dates"].get(D1) or {}).get("ths_zt") or {}
    yinfo = y.get("info") or []
    if yinfo:
        syms = [sym_of(it["code"], 1 if it.get("market_id") == 17 else 0) for it in yinfo]
        print("== 昨日涨停股今日行情:", len(syms), "只 ==")
        bundle["yesterday_zt_today"] = tx_quotes(syms)
        print("  拿到:", len(bundle["yesterday_zt_today"]))
    else:
        bundle["yesterday_zt_today"] = {}

    # 今日涨停股行情
    t = (bundle["dates"].get(D0) or {}).get("ths_zt") or {}
    tinfo = t.get("info") or []
    if tinfo:
        syms = [sym_of(it["code"], 1 if it.get("market_id") == 17 else 0) for it in tinfo]
        print("== 今日涨停股行情:", len(syms), "只 ==")
        bundle["today_zt_quotes"] = tx_quotes(syms)
        print("  拿到:", len(bundle["today_zt_quotes"]))
    else:
        bundle["today_zt_quotes"] = {}

    # 落盘前校验：关键源为空则中止，避免用残缺数据覆盖上次的好数据
    problems = []
    for d in [D0, D1]:
        rec = bundle["dates"].get(d) or {}
        if not ((rec.get("ths_zt") or {}).get("info")):
            problems.append(f"{d} 同花顺涨停池为空（限流 / 非交易日 / Referer 错）")
        if not ((rec.get("em_ZT") or {}).get("pool")):
            problems.append(f"{d} 东财涨停池为空")
        if not ((rec.get("ths_zt") or {}).get("total")):
            problems.append(f"{d} limit_up_count 缺失，封板率无法计算")
    if not bundle["indexes"]:
        problems.append("指数快照为空（腾讯行情未取到）")
    if problems:
        print("!! 抓取不完整，已放弃落盘（保留已有文件）：")
        for p in problems:
            print("   -", p)
        sys.exit(1)

    fp = os.path.join(OUT, f"zt_review_{D0}.json")
    tmp = fp + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False, indent=1)
    os.replace(tmp, fp)   # 原子替换，防止写一半
    print("saved ->", fp, os.path.getsize(fp) // 1024, "KB")
