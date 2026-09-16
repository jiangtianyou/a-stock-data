import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch2025 import tencent, BASE

# 当前前20大成分股（2026-09-14 权重快照）+ 指数
COMPS = [
    ("688012", "中微公司", 8.738), ("688981", "中芯国际", 8.444), ("688256", "寒武纪", 8.134),
    ("688041", "海光信息", 7.602), ("688008", "澜起科技", 7.566), ("688072", "拓荆科技", 4.320),
    ("688498", "源杰科技", 4.917), ("688347", "华虹宏力", 3.361), ("688120", "华海清科", 3.322),
    ("688361", "中科飞测", 2.889), ("688525", "佰维存储", 2.862), ("688521", "芯原股份", 2.713),
    ("688002", "睿创微纳", 2.240), ("688037", "芯源微", 1.922), ("688200", "华峰测控", 1.791),
    ("688313", "仕佳光子", 1.609), ("688702", "盛科通信", 1.545), ("688082", "盛美上海", 1.407),
    ("688019", "安集科技", 1.401), ("688766", "普冉股份", 1.385),
]
IDX = ("000685", "科创芯片指数", 100.0)

out = {}
todo = [IDX] + COMPS
for code, name, w in todo:
    ks = tencent(code)
    if not ks:
        print("FAIL", code, name); continue
    rows = []
    for r in ks:
        d = r[0].replace("-", "")
        rows.append(dict(d=d, o=float(r[1]), c=float(r[2]), h=float(r[3]), l=float(r[4]),
                         amt=float(r[5]) if len(r) > 5 and r[5] else 0.0))
    out[code] = dict(name=name, weight=w, rows=rows)
    d24 = [x for x in rows if x["d"] <= "20241231"]
    seg = [x for x in rows if "20250101" <= x["d"] <= "20251231"]
    b = d24[-1]["c"]; e = seg[-1]["c"]
    hi = max(x["h"] for x in seg); lo = min(x["l"] for x in seg)
    print("%-8s %-6s 基准%s@%.2f -> 2025末%.2f  YTD25=%+8.2f%%  hi=%.2f lo=%.2f 交易日=%d" % (
        code, name, d24[-1]["d"], b, e, (e/b-1)*100, hi, lo, len(seg)))
    time.sleep(0.7)

json.dump(out, open(os.path.join(BASE, "out", "k2025_all.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("\nsaved out/k2025_all.json  codes:", len(out))
