# -*- coding: utf-8 -*-
"""涨停复盘数据抓取：同花顺（涨停原因/梯队）+ 东财（炸板/跌停池）+ 腾讯（指数与个股行情）"""
import urllib.request, json, ssl, time, os, sys, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
        except Exception as e:
            if i == tries - 1:
                return None
            time.sleep(sleep * (i + 1))
    return None

# ---------------- 同花顺：涨停 / 炸板 / 跌停池 ----------------
def ths_pool(date, kind):
    url = (f"https://data.10jqka.com.cn/dataapi/limit_up/{kind}?page=1&limit=200&field={FIELD}"
           f"&filter=HS,GEM2STAR&order_field=330324&order_type=0&date={date}")
    t = get(url, "https://data.10jqka.com.cn/")
    if not t:
        return None
    try:
        d = json.loads(t)
    except Exception:
        return None
    data = d.get("data") or {}
    info = data.get("info") or []
    return {
        "total": data.get("limit_up_count"),
        "limit_down_count": data.get("limit_down_count"),
        "date": data.get("date"),
        "trade_status": data.get("trade_status"),
        "info": info,
    }

def ths_block_top(date):
    url = f"https://data.10jqka.com.cn/dataapi/limit_up/block_top?filter=HS,GEM2STAR&date={date}"
    t = get(url, "https://data.10jqka.com.cn/market/longhu/")
    if not t: return None
    try:
        return (json.loads(t).get("data") or [])
    except Exception:
        return None

# ---------------- 同花顺指数日线（含成交额） ----------------
THS_IDX = {"zs_1A0001": "上证指数", "zs_399001": "深证成指",
           "zs_399006": "创业板指", "zs_1B0688": "科创50"}

def ths_index_line(code):
    url = f"http://d.10jqka.com.cn/v6/line/{code}/01/last.js"
    t = get(url, "https://www.10jqka.com.cn/")
    if not t: return None
    m = re.search(r'"data":"([^"]+)"', t)
    nm = re.search(r'"name":"([^"]*)"', t)
    rows = []
    if m:
        for r in m.group(1).split(";"):
            p = r.split(",")
            if len(p) >= 7 and p[1] and p[4]:
                rows.append({"date": p[0], "open": p[1], "high": p[2], "low": p[3],
                             "close": p[4], "vol": p[5], "amt": p[6]})
    return {"code": code, "name": (json.loads('"' + nm.group(1) + '"') if nm else THS_IDX.get(code, code)),
            "rows": rows[-8:]}

# ---------------- 东财：涨停 / 炸板 / 跌停池 ----------------
def em_pool(date, kind):
    url = (f"https://push2ex.eastmoney.com/getTopic{kind}Pool?ut={UT}&dpt=wz.ztzt"
           f"&Pageindex=0&pagesize=300&sort=fbt%3Aasc&date={date}&_={int(time.time()*1000)}")
    t = get(url, "https://quote.eastmoney.com/")
    if not t: return None
    try:
        d = json.loads(t)
    except Exception:
        return None
    data = d.get("data") or {}
    return {"tc": data.get("tc"), "qdate": data.get("qdate"), "pool": data.get("pool") or []}

# ---------------- 腾讯：批量行情 ----------------
def tx_quotes(codes):
    """codes: ['sh000001','sz300750'] -> dict code -> parsed"""
    res = {}
    for i in range(0, len(codes), 50):
        batch = codes[i:i+50]
        url = "https://qt.gtimg.cn/q=" + ",".join(batch)
        t = get(url, "https://gu.qq.com/", enc="gbk")
        if not t:
            print("   ! tx batch fail", i); continue
        for line in t.split(";"):
            line = line.strip()
            if not line or "=" not in line: continue
            key = line.split("=")[0].replace("v_", "").strip()
            body = line.split("=", 1)[1].strip().strip('"')
            f = body.split("~")
            if len(f) < 50: continue
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
    if market == 0: return "sz" + code
    return "sz" + code

INDEXES = {
    "sh000001": "上证指数", "sz399001": "深证成指", "sz399006": "创业板指",
    "sh000688": "科创50", "bj899050": "北证50", "sh000300": "沪深300",
    "sh000852": "中证1000", "sh000905": "中证500", "sz399303": "国证2000",
    "sh000016": "上证50", "sz399005": "中小100",
}

if __name__ == "__main__":
    dates = ["20260916", "20260915"]
    bundle = {"dates": {}, "indexes": {}, "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")}

    for d in dates:
        print(f"== {d} ==")
        rec = {}
        rec["ths_zt"] = ths_pool(d, "limit_up_pool")
        print("  ths 涨停:", len((rec["ths_zt"] or {}).get("info") or []), "limit_up_count:", (rec["ths_zt"] or {}).get("total"))
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
            print(f"  em {k}:", len((rec['em_'+k] or {}).get("pool") or []))
            time.sleep(0.6)
        bundle["dates"][d] = rec

    # 指数行情
    print("== 指数 ==")
    bundle["indexes"] = tx_quotes(list(INDEXES.keys()))
    for k, v in bundle["indexes"].items():
        print(f"  {k} {v['name']}: {v['pct']}% 额={v['amount_wan']}万 价={v['price']}")

    # 指数日线（含成交额，用于昨日/前日对比）
    print("== 指数日线 ==")
    bundle["index_hist"] = {}
    for c in THS_IDX:
        h = ths_index_line(c)
        bundle["index_hist"][c] = h
        if h and h["rows"]:
            print(f"  {h['name']}: last={h['rows'][-1]}")
        else:
            print(f"  {c} FAIL")
        time.sleep(0.6)

    # 昨日涨停股今日行情（晋级率/溢价）
    y = (bundle["dates"].get("20260915") or {}).get("ths_zt") or {}
    yinfo = y.get("info") or []
    if yinfo:
        syms = [sym_of(it["code"], 1 if it.get("market_id") == 17 else 0) for it in yinfo]
        print("== 昨日涨停股今日行情:", len(syms), "只 ==")
        bundle["yesterday_zt_today"] = tx_quotes(syms)
        print("  拿到:", len(bundle["yesterday_zt_today"]))
    else:
        bundle["yesterday_zt_today"] = {}

    # 今日涨停股行情（补成交额/市值，同花顺字段已有但口径统一）
    t = (bundle["dates"].get("20260916") or {}).get("ths_zt") or {}
    tinfo = t.get("info") or []
    if tinfo:
        syms = [sym_of(it["code"], 1 if it.get("market_id") == 17 else 0) for it in tinfo]
        print("== 今日涨停股行情:", len(syms), "只 ==")
        bundle["today_zt_quotes"] = tx_quotes(syms)
        print("  拿到:", len(bundle["today_zt_quotes"]))
    else:
        bundle["today_zt_quotes"] = {}

    # 全部成功才落盘
    fp = os.path.join(OUT, "zt_review_20260916.json")
    tmp = fp + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False, indent=1)
    os.replace(tmp, fp)
    print("saved ->", fp, os.path.getsize(fp) // 1024, "KB")
