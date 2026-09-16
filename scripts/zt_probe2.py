import urllib.request, json, ssl, time

ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=ctx))
opener.addheaders = [("User-Agent","Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0 Safari/537.36"),
                     ("Referer","https://quote.eastmoney.com/")]
UT = "7eea3edcaed734bea9cbfc24409ed989"

url = f"https://push2ex.eastmoney.com/getTopicZTPool?ut={UT}&dpt=wz.ztzt&Pageindex=0&pagesize=300&sort=fbt%3Aasc&date=20260916&_={int(time.time()*1000)}"
with opener.open(urllib.request.Request(url), timeout=20) as r:
    d = json.loads(r.read().decode("utf-8","ignore"))

print("top keys:", list(d.keys()))
print("data keys:", list(d["data"].keys()))
p = d["data"]["pool"]
print("count:", len(p))
print("--- sample 1 ---")
print(json.dumps(p[0], ensure_ascii=False, indent=1))
print("--- sample 2 ---")
print(json.dumps(p[35], ensure_ascii=False, indent=1))
