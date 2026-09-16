import json, glob, os, sys

D = r"C:\Users\Administrator\.workbuddy\projects\d-Desktop-Playground-a-stock-data\f4800af3-610a-497f-a9b6-fb135319d10e\tool-results"

FILES = {
    "688981": "mcp-tdx-connector-tdx_kline-1789368452656-d2cc6d.txt",
    "688256": "mcp-tdx-connector-tdx_kline-1789368471326-8b9b18.txt",
    "688041": "mcp-tdx-connector-tdx_kline-1789368486947-8379df.txt",
    "000685": "mcp-tdx-connector-tdx_kline-1789368485688-da60c7.txt",
}

def parse(path):
    raw = open(path, encoding="utf-8", errors="ignore").read()
    i = raw.find("{")
    obj, _ = json.JSONDecoder().raw_decode(raw[i:])
    rows = obj["Rows"]
    out = []
    for r in rows:
        out.append({
            "date": r["Data"],
            "open": float(r["Open"]),
            "high": float(r["High"]),
            "low": float(r["Low"]),
            "close": float(r["Close"]),
            "amount": float(r["Amount"]),
        })
    return obj.get("AttachInfo", {}).get("Name", "?"), out

for code, fn in FILES.items():
    p = os.path.join(D, fn)
    if not os.path.exists(p):
        print(code, "MISSING", fn); continue
    name, rows = parse(p)
    print(f"{code} {name}: n={len(rows)} first={rows[0]['date']} last={rows[-1]['date']} firstclose={rows[0]['close']} lastclose={rows[-1]['close']}")
