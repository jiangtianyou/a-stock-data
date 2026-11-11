# -*- coding: utf-8 -*-
"""20261111 复盘附加分析 v2：主线归因（东财 hybk 口径）/ 链对比 / 市值结构 / 行业迁移"""
import json, statistics, collections, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D0, D1 = "20261111", "20261110"

def load(p):
    with open(os.path.join(ROOT, "out", p), encoding="utf-8") as f:
        return json.load(f)

B, B1 = load(f"zt_review_{D0}.json"), load(f"zt_review_{D1}.json")
d0, d1 = B["dates"][D0], B["dates"][D1]
p0, p1 = d0["em_ZT"]["pool"], d1["em_ZT"]["pool"]
th0, th1 = {i["code"]: i for i in d0["ths_zt"]["info"]}, {i["code"]: i for i in d1["ths_zt"]["info"]}
hy0 = {z["c"]: z.get("hybk") for z in p0}
hy1 = {z["c"]: z.get("hybk") for z in p1}

KW = {
    "光模块/CPO/光通信": ["光模块", "CPO", "光通信", "光纤", "光芯片", "空芯光纤", "MPO", "光模块胶", "铜缆", "6G"],
    "PCB/覆铜板/元件": ["PCB", "覆铜板", "PCB材料"],
    "算力/数据中心/液冷": ["算力", "数据中心", "液冷", "服务器", "交换机", "HBM"],
    "机器人/具身智能": ["机器人", "具身智能", "减速器", "丝杠", "关节", "电子皮肤", "灵巧手"],
    "AI应用/传媒": ["AI漫剧", "短剧", "AI影视", "AI游戏", "游戏", "IP", "影视", "剧集", "传媒", "AI应用"],
    "半导体/存储": ["存储芯片", "半导体", "芯片测试", "半导体设备"],
}

def agg(pool, th, label):
    print(f"\n--- {label}（涨停 {len(pool)} 只，成交 {sum(z['amount'] for z in pool)/1e8:.1f}亿）---")
    tot_a = sum(z.get("amount") or 0 for z in pool)
    tot_f = sum(z.get("fund") or 0 for z in pool)
    for name, kws in KW.items():
        hit = [z for z in pool if any(k in (th.get(z["c"], {}).get("reason_type") or "") for k in kws)]
        if not hit:
            print(f"  {name:<18} 0 只")
            continue
        a = sum(z.get("amount") or 0 for z in hit)
        f = sum(z.get("fund") or 0 for z in hit)
        lb = sum(1 for z in hit if (z.get("lbc") or 0) >= 2)
        hy = len({z.get("hybk") for z in hit})
        caps = [z.get("ltsz") or 0 for z in hit]
        big = sum(1 for c in caps if c > 1e10)
        print(f"  {name:<18} {len(hit):>2} 只 连板{lb:>2} ({lb/len(hit)*100:>4.1f}%) 离散度{hy:>2} "
              f"成交{a/1e8:>7.1f}亿({a/tot_a*100:>4.1f}%) 封单{f/1e8:>5.1f}亿({f/tot_f*100:>4.1f}%) "
              f"流通>100亿 {big} 只 中位流通 {statistics.median(caps)/1e8:>6.1f}亿")
    union = {z["c"] for name, kws in KW.items() for z in pool
             if any(k in (th.get(z["c"], {}).get("reason_type") or "") for k in kws)}
    print(f"  [任一命中并集] {len(union)} 只")

agg(p0, th0, "今日 " + D0)
agg(p1, th1, "昨日 " + D1)

print("\n" + "=" * 70)
print("【市值结构】涨停股流通市值分层")
print("=" * 70)
def capdist(pool, label):
    bins = [(0, 3e9, "<30亿"), (3e9, 5e9, "30-50亿"), (5e9, 1e10, "50-100亿"),
            (1e10, 3e10, "100-300亿"), (3e10, 9e18, ">300亿")]
    print(f"{label}: n={len(pool)}")
    for lo, hi, nm in bins:
        s = [z for z in pool if lo <= (z.get("ltsz") or 0) < hi]
        print(f"   {nm:<10} {len(s):>2} 只 ({len(s)/len(pool)*100:>4.1f}%)  成交 {sum(z.get('amount') or 0 for z in s)/1e8:>7.1f}亿")
capdist(p0, "今日")
capdist(p1, "昨日")

print("\n" + "=" * 70)
print("【行业迁移 v2】含代码交集（东财 hybk 口径）")
print("=" * 70)
c0 = collections.defaultdict(set); c1 = collections.defaultdict(set)
for z in p0: c0[z.get("hybk")].add(z["c"])
for z in p1: c1[z.get("hybk")].add(z["c"])
keys = set(c0) | set(c1)
mv = [(k, len(c0.get(k, set())), len(c1.get(k, set()))) for k in keys]
mv.sort(key=lambda t: -((t[1] + t[2]) + abs(t[1] - t[2]) * 2))
for k, a, b in mv[:16]:
    inter = len(c0.get(k, set()) & c1.get(k, set()))
    print(f"  {str(k):<8} 今 {a:>2} 昨 {b:>2}  Δ{a-b:>+3}  留存 {inter} 只  轮换率 {(1-inter/a)*100 if a else 0:>5.1f}%")
print(f"行业数 今 {len([k for k in c0 if k and c0[k]])} 昨 {len([k for k in c1 if k and c1[k]])}")
print(f"清零 {len([k for k in c1 if c1[k] and not c0.get(k)])}: {sorted([str(k) for k in c1 if c1[k] and not c0.get(k)])}")
print(f"新增 {len([k for k in c0 if c0[k] and not c1.get(k)])}: {sorted([str(k) for k in c0 if c0[k] and not c1.get(k)])}")

print("\n" + "=" * 70)
print("【昨涨停今日表现 · 分线】")
print("=" * 70)
y = B["yesterday_zt_today"]
print("样本", len(y))
for name, kws in KW.items():
    hit = [r for r in y if any(k in (r.get("reason") or r.get("reason_type") or "") for k in kws)]
    if not hit:
        continue
    chg = [r["pct"] for r in hit if r.get("pct") is not None]
    if not chg:
        continue
    greens = sum(1 for c in chg if c < 0)
    print(f"  {name:<18} n={len(hit):>2} 均{statistics.mean(chg):>+6.2f}% 中位{statistics.median(chg):>+6.2f}% 翻绿{greens}只")
print("\n字段样例:", json.dumps(y[0], ensure_ascii=False))

print("\n" + "=" * 70)
print("【东方系完整链条（含未涨停的东方新能）】")
print("=" * 70)
for c, i in th0.items():
    if "东方" in i.get("name", "") or "东方" in (i.get("reason_type") or ""):
        print(f"  {c} {i['name']:<6} {hy0.get(c)}  连板{next((z['lbc'] for z in p0 if z['c']==c),0)} {i.get('high_days')} "
              f"封单{(i.get('order_amount') or 0)/1e8:.2f}亿 换手{i.get('turnover_rate')}%")

print("\n" + "=" * 70)
print("【昨日连板股 20 只今日表现】")
print("=" * 70)
for z in p1:
    if (z.get("lbc") or 0) >= 2:
        r = next((x for x in y if x.get("code") == z["c"]), None)
        print(f"  昨{z['lbc']}板 {z['c']} {z['n']:<6} {z.get('hybk'):<6} 今{(r or {}).get('pct')}%  "
              f"{(th1.get(z['c'],{}).get('reason_type') or '')[:40]}")

print("\n" + "=" * 70)
print("【今日前排成交额 TOP15 涨停股】")
print("=" * 70)
for z in sorted(p0, key=lambda x: -(x.get("amount") or 0))[:15]:
    print(f"  {z['c']} {z['n']:<6} {z.get('hybk'):<6} 成交{z['amount']/1e8:>7.2f}亿 流通{(z.get('ltsz') or 0)/1e8:>7.1f}亿 "
          f"换手{z.get('hs'):>5.1f}% 连板{z.get('lbc')} 封单{(z.get('fund') or 0)/1e8:>5.2f}亿 炸{z.get('zbc')}")
