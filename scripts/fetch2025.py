import json, urllib.request, ssl, time, os

BASE = r"D:\Desktop\Playground\a-stock-data"
RAW = os.path.join(BASE, "out", "raw2025")
os.makedirs(RAW, exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
      "Referer": "https://gu.qq.com/"}
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=ctx))

def tencent(code, start="2024-11-01", end="2026-01-20", cnt=320):
    url = (f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?"
           f"param=sh{code},day,{start},{end},{cnt},qfq")
    last = None
    for t in range(4):
        try:
            with opener.open(urllib.request.Request(url, headers=UA), timeout=30) as r:
                d = json.loads(r.read().decode("utf-8"))
            node = d["data"]["sh" + code]
            ks = node.get("qfqday") or node.get("day")
            if ks:
                return ks
            last = "empty"
        except Exception as e:
            last = repr(e)
        time.sleep(1.5)
    print("  FAIL", code, last)
    return []

if __name__ == "__main__":
    ks = tencent("688981")
    print("rows:", len(ks))
    print("first:", ks[0])
    print("rowlen:", len(ks[0]))
    print("last:", ks[-1])
    print("second-last:", ks[-2])
    # 找 2024-12-31 与 2025-12-31
    dd = {r[0]: r for r in ks}
    for k in ["2024-12-31", "2025-12-31", "2026-01-02"]:
        print(k, dd.get(k))
