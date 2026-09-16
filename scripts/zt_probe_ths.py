import urllib.request, json, ssl, time

ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=ctx))
opener.addheaders = [("User-Agent","Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0 Safari/537.36"),
                     ("Referer","https://data.10jqka.com.cn/")]

def get(url):
    with opener.open(urllib.request.Request(url), timeout=20) as r:
        return r.read().decode("utf-8","ignore")

u1 = ("https://data.10jqka.com.cn/dataapi/limit_up/limit_up_pool?page=1&limit=200"
      "&field=199112,10,9001,330323,330324,330325,9002,330329,133971,133970,1968584,3475914,9003,9004"
      "&filter=HS,GEM2STAR&order_field=330324&order_type=0&date=20260916")
try:
    t = get(u1)
    d = json.loads(t)
    print("THS LUP keys:", list(d.keys()), "status:", d.get("status_code"), d.get("status_msg"))
    dd = d.get("data") or {}
    print("data keys:", list(dd.keys()))
    info = dd.get("info") or []
    print("count:", len(info))
    if info:
        print(json.dumps(info[0], ensure_ascii=False, indent=1)[:2500])
except Exception as e:
    print("THS LUP ERR", repr(e))

time.sleep(1)
u2 = "https://data.10jqka.com.cn/dataapi/limit_up/block_top?filter=HS,GEM2STAR&date=20260916"
try:
    t = get(u2)
    d = json.loads(t)
    print("\nTHS BLOCK status:", d.get("status_code"))
    dd = d.get("data") or []
    print("blocks:", len(dd))
    if dd:
        print(json.dumps(dd[0], ensure_ascii=False)[:800])
except Exception as e:
    print("THS BLOCK ERR", repr(e))
