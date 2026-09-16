import json, os

BASE = r"D:\Desktop\Playground\a-stock-data"
RAW = json.load(open(os.path.join(BASE, "out", "k2025_all.json"), encoding="utf-8"))
# 2026 YTD（来自已完成的 attribution.json，腾讯qfq口径）
a26 = json.load(open(os.path.join(BASE, "out", "attribution.json"), encoding="utf-8"))
ytd26 = {x["code"]: x["ytd"] for x in a26["rank"]}
rank26 = {x["code"]: x["rank"] for x in a26["rank"]}
off26 = {x["code"]: x["off_hi"] for x in a26["rank"]}

GROUPS = {
    "半导体设备/材料": {"688012","688072","688120","688361","688037","688200","688082","688019"},
    "光芯片/光通信": {"688498","688313","688702"},
    "存储芯片": {"688525","688766"},
    "算力芯片设计": {"688256","688041","688008","688521"},
    "晶圆制造": {"688981","688347"},
    "军工电子": {"688002"},
}
PORT3 = {"688981","688256","688041"}
def grp(code):
    for g,s in GROUPS.items():
        if code in s: return g
    return "其他"

rows = []
for code, obj in RAW.items():
    if code == "000685": continue
    rs = obj["rows"]
    d24 = [x for x in rs if x["d"] <= "20241231"]
    seg = [x for x in rs if "20250101" <= x["d"] <= "20251231"]
    b = d24[-1]["c"]; e = seg[-1]["c"]
    hi = max(x["h"] for x in seg); lo = min(x["l"] for x in seg)
    ytd = (e/b-1)*100
    rows.append(dict(code=code, name=obj["name"], weight=obj["weight"], grp=grp(code),
        in_port=code in PORT3, base_close=round(b,2), end_close=round(e,2),
        ytd=round(ytd,2), hi=round(hi,2), lo=round(lo,2),
        off_hi=round((e/hi-1)*100,2), ytd26=ytd26.get(code), rank26=rank26.get(code), off26=off26.get(code)))

rows.sort(key=lambda x:-x["ytd"])
for i,r in enumerate(rows,1): r["rank"]=i

# 子板块等权 2025（等权买入持有 = 算术平均，与前报口径一致；连乘会因复利虚高）
groups=[]
for g,s in GROUPS.items():
    mem=[r for r in rows if r["code"] in s]
    if not mem: continue
    eq_ytd=sum(r["ytd"] for r in mem)/len(mem)
    groups.append(dict(name=g,n=len(mem),w=round(sum(r["weight"] for r in mem),3),
        eq_ytd=round(eq_ytd,2),in_port=(g in ("算力芯片设计","晶圆制造")),
        members=[dict(name=r["name"],ytd=r["ytd"]) for r in mem]))
groups.sort(key=lambda x:-x["eq_ytd"])

eq20=sum(r["ytd"] for r in rows)/len(rows)
top3=[r for r in rows if r["in_port"]]; rest17=[r for r in rows if not r["in_port"]]
eq3=sum(r["ytd"] for r in top3)/len(top3)
eq17=sum(r["ytd"] for r in rest17)/len(rest17)
IDX25=61.33
summary=dict(idx25=IDX25,eq_all20=round(eq20,2),eq_top3=round(eq3,2),eq_rest17=round(eq17,2),
    gap_top3=round(eq3-eq17,2),top3_w=round(sum(r["weight"] for r in top3),3))

out=dict(rank=rows,groups=groups,summary=summary)
json.dump(out,open(os.path.join(BASE,"out","attribution2025.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)

print("=== 2025年前20大成分股 YTD 排行（腾讯qfq）===")
for r in rows:
    tag=" ★组合" if r["in_port"] else ""
    print("%2d. %-6s %-6s w=%5.3f%% 2025=%+8.2f%% | 2026YTD=%+8.2f%%(第%s) 距25高%+6.2f%%%s"%(
        r["rank"],r["name"],r["grp"][:4],r["weight"],r["ytd"],
        r["ytd26"] if r["ytd26"] is not None else 0, r["rank26"], r["off_hi"], tag))
print("\n=== 2025 子板块等权 YTD ===")
for g in groups:
    print("  %-14s n=%d w=%6.2f%% 等权YTD %+8.2f%%%s"%(g["name"],g["n"],g["w"],g["eq_ytd"]," ←含组合" if g["in_port"] else ""))
print("\n=== 归因汇总 2025 ===")
print("  指数 +%.2f%% | 前20大等权 +%.2f%% | 组合三只等权 +%.2f%% | 其余17只等权 +%.2f%% | gap %+.2fpct"%(
    IDX25,eq20,eq3,eq17,eq3-eq17))
print("  组合权重合计 %.2f%%"%summary["top3_w"])

# 跨年对照：2025排名 vs 2026排名
print("\n=== 跨年排名变化（前20大，2025 rank -> 2026 rank）===")
for r in sorted(rows,key=lambda x:x["rank"]):
    d=(r["rank26"]-r["rank"]) if r["rank26"] else None
    arrow="↑%d"%(-d) if d and d<0 else ("↓%d"%d if d and d>0 else "→")
    print("  %-6s 2025第%2d(%+7.2f%%) -> 2026第%s(%+7.2f%%) %s%s"%(
        r["name"],r["rank"],r["ytd"],r["rank26"],r["ytd26"],arrow," ★" if r["in_port"] else ""))
print("\nsaved out/attribution2025.json")
