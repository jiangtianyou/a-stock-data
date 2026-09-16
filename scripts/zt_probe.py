import urllib.request, json, ssl, time, os

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=ctx))
opener.addheaders = [
    ("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"),
    ("Referer", "https://quote.eastmoney.com/"),
]

UT = "7eea3edcaed734bea9cbfc24409ed989"

def get(url):
    req = urllib.request.Request(url)
    with opener.open(req, timeout=20) as r:
        return r.read().decode("utf-8", "ignore")

def pool(kind, date):
    # kind: ZT / ZB / DT
    url = (f"https://push2ex.eastmoney.com/getTopic{kind}Pool?ut={UT}&dpt=wz.ztzt"
           f"&Pageindex=0&pagesize=300&sort=fbt%3Aasc&date={date}&_={int(time.time()*1000)}")
    try:
        txt = get(url)
    except Exception as e:
        return {"err": repr(e)}
    try:
        return json.loads(txt)
    except Exception:
        return {"raw": txt[:300]}

for d in ["20260916", "20260915"]:
    for k in ["ZT", "ZB", "DT"]:
        r = pool(k, d)
        data = r.get("data") if isinstance(r, dict) else None
        if data:
            print(d, k, "total=", data.get("total"), "pages=", data.get("pages"), "len=", len(data.get("pool") or []))
        else:
            print(d, k, "NO DATA ->", json.dumps(r, ensure_ascii=False)[:200])
        time.sleep(0.5)
