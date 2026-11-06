# -*- coding: utf-8 -*-
"""补抓 20261106 报告所需：今日跌停池 / 昨跌停股今日行情 / 个股流通市值 / westock 榜"""
import json, os, ssl, time, subprocess, urllib.request

ROOT = os.environ.get("ZT_ROOT") or os.getcwd()
OUT = os.path.join(ROOT, "out")
D0, D1 = "20261106", "20261105"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
UT = "7eea3edcaed734bea9cbfc24409ed989"
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
OP = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=ctx))


def get(url, referer, enc="utf-8"):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer})
    with OP.open(req, timeout=25) as r:
        return r.read().decode(enc, "ignore")


def dt_pool(date):
    url = ("https://push2ex.eastmoney.com/getTopicDTPool?ut=" + UT + "&dpt=wz.ztzt"
           "&Pageindex=0&pagesize=300&sort=fund%3Aasc&date=" + date + "&_=" + str(int(time.time() * 1000)))
    return json.loads(get(url, "https://quote.eastmoney.com/"))


def sym(code):
    if code.startswith(("60", "68", "5", "11", "9")):
        return "sh" + code
    if code.startswith(("00", "30", "12", "15", "16", "18", "20")):
        return "sz" + code
    return "bj" + code


def tx_quotes(codes):
    """返回 code -> {name,pct,amount(亿),float_mv(亿),total_mv(亿),turnover,price}"""
    res = {}
    for i in range(0, len(codes), 40):
        batch = codes[i:i + 40]
        t = get("https://qt.gtimg.cn/q=" + ",".join(batch), "https://gu.qq.com/", enc="gbk")
        for line in t.split(";"):
            line = line.strip()
            if not line or "=" not in line:
                continue
            body = line.split("=", 1)[1].strip().strip('"')
            f = body.split("~")
            if len(f) < 50:
                continue
            try:
                res[f[2]] = {"name": f[1], "price": float(f[3]), "pct": float(f[32]),
                             "amount": float(f[37]) / 10000.0,
                             "turnover": float(f[38]) if f[38] else 0.0,
                             "float_mv": float(f[44]) if f[44] else 0.0,
                             "total_mv": float(f[45]) if f[45] else 0.0,
                             "open": float(f[5]) if f[5] else 0.0,
                             "high": float(f[33]) if f[33] else 0.0,
                             "low": float(f[34]) if f[34] else 0.0}
            except Exception:
                continue
        time.sleep(0.3)
    return res


# 1) 今日跌停池
p0 = os.path.join(OUT, f"_dt{D0[4:]}.json")
d = dt_pool(D0)
json.dump(d, open(p0, "w", encoding="utf-8"), ensure_ascii=False)
print("dt", D0, "tc=", (d.get("data") or {}).get("tc"), "pool=", len((d.get("data") or {}).get("pool") or []))

# 2) 昨日跌停股今日行情
dt1 = json.load(open(os.path.join(OUT, f"_dt{D1[4:]}.json"), encoding="utf-8"))
p1 = (dt1.get("data") or {}).get("pool") or []
Q = tx_quotes([sym(x["c"]) for x in p1])
json.dump(Q, open(os.path.join(OUT, f"_qdt{D1[4:]}.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("qdt", D1, "pool=", len(p1), "got=", len(Q))

# 3) 今日涨停股流通市值（取腾讯 f44/f45）
R = json.load(open(os.path.join(OUT, f"zt_review_{D0}.json"), encoding="utf-8"))
zt_codes = [x["code"] for x in (R["yesterday_zt_today"] or [])] if False else None
pool = (R["dates"][D0]["em_ZT"] or {}).get("pool") or []
codes = [x["c"] for x in pool]
mq = tx_quotes([sym(c) for c in codes])
json.dump(mq, open(os.path.join(OUT, f"_mv{D0[4:]}.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("mv", D0, "zt pool=", len(codes), "got=", len(mq))

# 4) westock 行业/概念榜（今日主线候选：光伏/储能/华为/AI/算力/贵金属/电池）
_need = {"半导体", "元件", "光学光电", "电子化学", "其他电子", "消费电子", "通信设备", "软件开发",
         "IT服务Ⅱ", "自动化设", "专用设备", "通用设备", "贵金属", "小金属", "工业金属", "电池",
         "光伏设备", "风电设备", "电力", "汽车零部", "电网设备", "游戏Ⅱ", "出版", "影视院线",
         "数字媒体", "广告营销", "文化传媒", "医疗服务", "化学制药", "中药Ⅱ", "装修建材",
         "一般零售", "食品加工", "休闲食品", "白酒Ⅱ", "证券Ⅱ", "保险Ⅱ", "银行", "航运港口",
         "煤炭开采", "钢铁", "化学制品", "农牧饲渔", "房地产开发",
         "覆铜板", "PCB概念", "先进封装", "存储芯片", "光模块", "CPO", "人形机器人", "固态电池",
         "半导体设备", "第三代半导体", "AI算力", "算力概念", "黄金概念", "光伏概念", "储能",
         "锂电池概念", "华为概念", "人工智能", "AI应用", "商业航天", "可控核聚变"}
SW = {}
_wx = "C:/Users/Administrator/.local/bin/westock.exe"
for kind in ("industry", "concept"):
    r = subprocess.run([_wx, "sector", "ranking", "--kind", kind], capture_output=True, timeout=180)
    txt = r.stdout.decode("utf-8", errors="ignore")
    for line in txt.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        p = [q.strip() for q in s.strip("|").split("|")]
        if len(p) < 10 or p[1] in ("name", "---") or set(p[1]) <= set("-"):
            continue
        try:
            if p[1] in _need:
                SW[p[1]] = {"pct": float(p[2]), "flow": float(p[3]), "turnover": float(p[4]), "updown": p[8]}
        except Exception:
            continue
json.dump(SW, open(os.path.join(OUT, f"_sw{D0[4:]}.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("sw n=", len(SW))
for k, v in sorted(SW.items(), key=lambda kv: -kv[1]["pct"])[:18]:
    print("  ", k, v)
