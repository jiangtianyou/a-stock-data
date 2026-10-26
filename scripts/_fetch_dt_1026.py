import json, time, ssl, urllib.request, os, sys

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
UT = "7eea3edcaed734bea9cbfc24409ed989"
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
OP = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=ctx))


def get(url, referer="https://quote.eastmoney.com/"):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer})
    return OP.open(req, timeout=20).read().decode("utf-8", "replace")


def pool(date, kind, sort):
    url = ("https://push2ex.eastmoney.com/getTopic" + kind + "Pool?ut=" + UT + "&dpt=wz.ztzt"
           "&Pageindex=0&pagesize=300&sort=" + sort + "&date=" + date + "&_=" + str(int(time.time() * 1000)))
    t = get(url)
    d = json.loads(t)
    data = d.get("data") or {}
    return {"tc": data.get("tc"), "pool": data.get("pool") or []}


for D in sys.argv[1:]:
    for kind, sort in (("DT", "fund%3Aasc"), ("ZB", "fbt%3Aasc")):
        r = pool(D, kind, sort)
        p = "out/_%s%s.json" % (kind.lower(), D[4:])
        json.dump(r, open(p, "w", encoding="utf-8"), ensure_ascii=False)
        print(D, kind, "tc=", r["tc"], "pool=", len(r["pool"]), "->", p)
    time.sleep(1.5)
