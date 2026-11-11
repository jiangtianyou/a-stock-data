# -*- coding: utf-8 -*-
"""20261111 附加分析 v3：昨日涨停股分线表现 / 东方系链条 / 昨日连板股 / 今日成交前列"""
import json, statistics, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D0, D1 = "20261111", "20261110"
def load(p):
    with open(os.path.join(ROOT, "out", p), encoding="utf-8") as f:
        return json.load(f)
B, B1 = load(f"zt_review_{D0}.json"), load(f"zt_review_{D1}.json")
d0, d1 = B["dates"][D0], B["dates"][D1]
p0, p1 = d0["em_ZT"]["pool"], d1["em_ZT"]["pool"]
th0 = {i["code"]: i for i in d0["ths_zt"]["info"]}
th1 = {i["code"]: i for i in d1["ths_zt"]["info"]}
hy0 = {z["c"]: z.get("hybk") for z in p0}
y = {v["code"]: v for v in B["yesterday_zt_today"].values()}

KW = {
    "光模块/CPO/光通信": ["光模块", "CPO", "光通信", "光纤", "光芯片", "空芯光纤", "MPO", "光模块胶", "铜缆", "6G"],
    "PCB/覆铜板/元件": ["PCB", "覆铜板", "PCB材料"],
    "算力/数据中心/液冷": ["算力", "数据中心", "液冷", "服务器", "交换机", "HBM"],
    "机器人/具身智能": ["机器人", "具身智能", "减速器", "丝杠", "关节", "电子皮肤", "灵巧手"],
    "AI应用/传媒": ["AI漫剧", "短剧", "AI影视", "AI游戏", "游戏", "IP", "影视", "剧集", "传媒", "AI应用"],
}
print("=" * 70)
print("【昨日涨停股分线表现】样本 93")
print("=" * 70)
for name, kws in KW.items():
    hit = [z for z in p1 if any(k in (th1.get(z["c"], {}).get("reason_type") or "") for k in kws)]
    chg = [y[z["c"]]["pct"] for z in hit if z["c"] in y]
    if not chg:
        continue
    adv = sum(1 for c in chg if c > 0)
    lim = sum(1 for z in hit if z["c"] in y and y[z["c"]]["pct"] >= 9.9)
    print(f"  {name:<18} n={len(hit):>2} 均{statistics.mean(chg):>+6.2f}% 中位{statistics.median(chg):>+6.2f}% "
          f"上涨{adv}只 跌{len(chg)-adv}只 涨停{lim}只")

print("\n" + "=" * 70)
print("【东方系完整链条】")
print("=" * 70)
for c, i in th0.items():
    if "东方" in i.get("name", "") or "东方" in (i.get("reason_type") or ""):
        z = next((x for x in p0 if x["c"] == c), None)
        print(f"  {c} {i['name']:<6} {hy0.get(c):<6} 连板{z['lbc'] if z else 0} {i.get('high_days')} "
              f"封单{(i.get('order_amount') or 0)/1e8:.2f}亿 换手{i.get('turnover_rate')}% 额{(z.get('amount') or 0)/1e8:.2f}亿")
print("  --- 未涨停的东方系（昨涨停今日未涨停）---")
for c, i in th1.items():
    if ("东方" in i.get("name", "") or "东方" in (i.get("reason_type") or "")) and c not in {z["c"] for z in p0}:
        r = y.get(c)
        print(f"  {c} {i['name']:<6} 昨{i.get('high_days')} 今{r['pct'] if r else '?'}%")

print("\n" + "=" * 70)
print("【昨日连板股（lbc>=2）今日表现】共", sum(1 for z in p1 if (z.get("lbc") or 0) >= 2), "只")
print("=" * 70)
for z in sorted(p1, key=lambda x: -(x.get("lbc") or 0)):
    if (z.get("lbc") or 0) < 2:
        continue
    r = y.get(z["c"], {})
    st = "晋级" if z["c"] in {x["c"] for x in p0} else ""
    print(f"  昨{z['lbc']}板 {z['c']} {z['n']:<6} {str(z.get('hybk')):<6} 今{r.get('pct'):>+6.2f}% {st}")

print("\n" + "=" * 70)
print("【今日涨停股成交额 TOP18】")
print("=" * 70)
for z in sorted(p0, key=lambda x: -(x.get("amount") or 0))[:18]:
    rt = (th0.get(z["c"], {}).get("reason_type") or "")[:34]
    print(f"  {z['c']} {z['n']:<6} {str(z.get('hybk')):<6} 成交{z['amount']/1e8:>7.2f}亿 流通{(z.get('ltsz') or 0)/1e8:>7.1f}亿 "
          f"换手{z.get('hs'):>5.1f}% 连板{z.get('lbc')} 封单{(z.get('fund') or 0)/1e8:>5.2f}亿 | {rt}")

print("\n" + "=" * 70)
print("【封板时段：今日 vs 昨日（14:30 分界）】")
print("=" * 70)
def slot(t):
    t = int(t); h, m = t // 10000, (t // 100) % 100
    if h == 9 and m <= 25: return "竞价/秒板"
    if (h == 9 and m > 25) or (h == 10 and m == 0): return "开盘半小时"
    if (h == 9) or (h == 10) or (h == 11 and m <= 30): return "开盘半小时" if h == 9 and m >= 30 else "上午盘中"
    if h == 11 or (h == 13) or (h == 14 and m <= 30): return "午后盘中"
    return "尾盘"
import collections
for lbl, pool in (("今日", p0), ("昨日", p1)):
    for name, kws in KW.items():
        hit = [z for z in pool if any(k in (th0 if lbl == "今日" else th1).get(z["c"], {}).get("reason_type", "") for k in kws)]
    c = collections.Counter()
    for z in pool:
        fb = z.get("fbt")
        if not fb: c["未知"] += 1; continue
        s = str(int(fb)).zfill(6); h, m = int(s[:2]), int(s[2:4])
        if h == 9 and m <= 25: c["竞价/秒板"] += 1
        elif h < 11 or (h == 11 and m <= 30): c["开盘半小时" if (h == 9 or (h == 10 and m < 30)) else "上午盘中"] += 1
        elif h < 14 or (h == 14 and m <= 30): c["午后盘中"] += 1
        else: c["尾盘"] += 1
    print(f"  {lbl}: {dict(c)}")
