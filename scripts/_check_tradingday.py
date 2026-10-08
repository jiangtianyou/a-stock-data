# -*- coding: utf-8 -*-
"""交易日判定：四源交叉验证（判据见 skill/pitfalls；第一判据=同花顺 trade_status）"""
import json, sys, urllib.request

D = sys.argv[1] if len(sys.argv) > 1 else "20261007"

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def get(url, enc="utf-8", timeout=25):
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    req = urllib.request.Request(url, headers=UA)
    with op.open(req, timeout=timeout) as r:
        return r.read().decode(enc, "ignore")


print("== 交易日判定 %s ==" % D)

# 源1：同花顺涨停池 带 date
try:
    u1 = ("https://data.10jqka.com.cn/dataapi/limit_up/limit_up_pool"
          "?page=1&limit=200&field=199112,10,9001,330323,330324,330325,9002,330329,133971,133970,1968584,3475914,9003&filter=HS,GEM2STAR&order_field=330324&order_type=0&date=" + D)
    j1 = json.loads(get(u1))
    data = j1.get("data") or {}
    ts = data.get("trade_status")
    print("[1] ths 带date=%s -> total=%s trade_status=%s" % (
        D, (data.get("page") or {}).get("total"), ts))
except Exception as e:
    print("[1] ths 带date=%s -> ERR %r" % (D, e))

# 源2：同花顺涨停池 不带 date
try:
    u2 = ("https://data.10jqka.com.cn/dataapi/limit_up/limit_up_pool"
          "?page=1&limit=5&field=199112,10,9001&filter=HS,GEM2STAR&order_field=330324&order_type=0")
    j2 = json.loads(get(u2))
    d2 = j2.get("data") or {}
    print("[2] ths 不带date -> date=%s total=%s" % (
        d2.get("date"), (d2.get("page") or {}).get("total")))
except Exception as e:
    print("[2] ths 不带date -> ERR %r" % (e,))

# 源3：腾讯日线
try:
    u3 = ("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
          "?param=sh000001,day,,,6,qfq")
    j3 = json.loads(get(u3))
    rows = j3["data"]["sh000001"].get("day") or j3["data"]["sh000001"].get("qfqday")
    print("[3] 腾讯日线 末3根 ->", [r[0] for r in rows[-3:]])
except Exception as e:
    print("[3] 腾讯日线 -> ERR %r" % (e,))

# 源4：腾讯分时
try:
    u4 = "https://web.ifzq.gtimg.cn/appstock/app/minute/query?code=sh000001"
    j4 = json.loads(get(u4))
    d4 = j4["data"]["sh000001"]["data"]
    print("[4] 腾讯分时 -> date=%s 点数=%d 末点=%s" % (
        d4.get("date"), len(d4.get("data", [])),
        (d4.get("data") or [["", ""]])[-1][0]))
except Exception as e:
    print("[4] 腾讯分时 -> ERR %r" % (e,))
