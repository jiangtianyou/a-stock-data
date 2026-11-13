# -*- coding: utf-8 -*-
"""20261113 复盘附加分析：指数环比 / 概念板块榜 / 主线聚类 / 市值结构 / 行业迁移 / 炸板回封 / 跌停池归并 / 池交集"""
import json, statistics, collections, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D0, D1, D2 = "20261113", "20261112", "20261111"

def load(p):
    with open(os.path.join(ROOT, "out", p), encoding="utf-8") as f:
        return json.load(f)

B, B1, B2 = load(f"zt_review_{D0}.json"), load(f"zt_review_{D1}.json"), load(f"zt_review_{D2}.json")
S, S1 = load(f"zt_stats_{D0}.json"), load(f"zt_stats_{D1}.json")
d0, d1, d2 = B["dates"][D0], B["dates"][D1], B2["dates"][D2]
ALLD = {**B2["dates"], **B1["dates"], **B["dates"]}
p0, p1, p2 = d0["em_ZT"]["pool"], d1["em_ZT"]["pool"], d2["em_ZT"]["pool"]
th0 = {i["code"]: i for i in d0["ths_zt"]["info"]}
th1 = {i["code"]: i for i in d1["ths_zt"]["info"]}
y = {v["code"]: v for v in B["yesterday_zt_today"].values()}
c0set, c1set, c2set = {z["c"] for z in p0}, {z["c"] for z in p1}, {z["c"] for z in p2}

print("=" * 78)
print("【一】情绪四指标三日序列")
print("=" * 78)
for d in (D0, D1, D2):
    r = ALLD[d]
    t = (r["ths_zt"].get("total") or {}).get("today") or {}
    ld = (r["ths_zt"].get("limit_down_count") or {}).get("today") or {}
    zbc = (r["em_ZB"] or {}).get("tc")
    print(f"  {d}: 涨停 {t.get('num')} 触及 {t.get('history_num')} 炸板 {zbc} 封板率 {t.get('rate',0)*100:.1f}% "
          f"| 跌停 {ld.get('num')} 触及跌停 {ld.get('history_num')} 封死率 {ld.get('rate',0)*100:.1f}% 被买回 {ld.get('open_num')}")

print("\n" + "=" * 78)
print("【二】11 指数：涨跌幅 + 成交额环比（今日 vs 昨日）")
print("=" * 78)
i0, i1 = B["indexes"], B1["indexes"]
rows = []
for k, v in i0.items():
    a1 = (i1.get(k) or {}).get("amount_wan") or 0
    a0 = v.get("amount_wan") or 0
    d = (a0 / a1 - 1) * 100 if a1 else None
    rows.append((v.get("name") or k, k, v.get("pct"), v.get("price"), v.get("open"), v.get("high"), v.get("low"), a0 / 1e4, a1 / 1e4, d))
for nm, k, pct, px, op, hi, lo, a0, a1, d in sorted(rows, key=lambda r: -(r[9] or 0)):
    gap = (op / px - 1) * 100 if px and op else 0
    pos = (px / hi - 1) * 100 if hi else 0
    below = "收于开下" if op and px < op else "收于开上"
    print(f"  {nm:<8} {pct:>+6.2f}%  额 {a0:>8.1f}亿 (昨{a1:>8.1f}亿 {d:>+6.1f}%)  开{gap:>+5.2f}%  距高{pos:>+5.2f}%  {below}")
n_up = sum(1 for r in rows if (r[2] or 0) > 0)
n_amt_up = sum(1 for r in rows if (r[9] or 0) > 0)
n_below = sum(1 for r in rows if r[4] and r[3] and r[3] < r[4])
print(f"  >> N_UP={n_up}/{len(rows)}  AMT_UP={n_amt_up}/{len(rows)}  N_BELOW_OPEN={n_below}")

print("\n" + "=" * 78)
print("【三】概念板块榜（同花顺 ths_block）今日 vs 昨日：连板占比")
print("=" * 78)
def blocks(d, label, topn=14):
    bl = d.get("ths_block") or []
    print(f"--- {label}（共 {len(bl)} 条）---")
    for b in bl[:topn]:
        n = b.get("limit_up_num") or 0
        cont = b.get("continuous_plate_num") or 0
        print(f"  {str(b.get('name')):<14} 涨停{n:>3}  连板{cont:>3} ({cont/n*100 if n else 0:>5.1f}%)  高标 {b.get('high')}")
blocks(d0, "今日 " + D0)
print()
blocks(d1, "昨日 " + D1, 8)

print("\n" + "=" * 78)
print("【四】主线聚类（reason_type 关键词）+ 连板数 + 离散度 + 成交占比")
print("=" * 78)
KW = {
    "机器人/具身智能": ["机器人", "具身智能", "减速器", "丝杠", "关节", "电子皮肤", "灵巧手", "谐波", "滚珠"],
    "AI应用/影视短剧": ["AI漫剧", "短剧", "AI影视", "AI游戏", "游戏", "IP", "影视", "剧集", "传媒", "AI应用", "电影院线", "院线"],
    "算力/数据中心": ["算力", "数据中心", "液冷", "服务器", "交换机", "HBM", "智算"],
    "光刻胶/电子化学品": ["光刻胶", "电子化学品", "合成树脂"],
    "半导体/芯片": ["存储芯片", "半导体", "芯片测试", "半导体设备", "GPU"],
    "汽车零部件": ["汽车零部件", "汽车管路", "变速器", "曲轴", "车辆齿轮", "汽车洗涤"],
    "光伏/玻璃": ["光伏", "玻璃基板", "光伏玻璃", "玻璃基封装"],
    "东方系": ["“东方系”", "“东方”"],
    "“羊”字辈": ["“羊”字辈"],
    "海洋经济/养殖": ["海洋", "水产", "海参", "渔业", "鱼粉", "生猪"],
    "零售/百货": ["百货", "零售", "免税"],
    "燃气/供热": ["燃气", "天然气", "LNG", "供热"],
    "冰雪/旅游": ["冰雪", "旅游"],
}
def agg(pool, th, label):
    tot_a = sum(z.get("amount") or 0 for z in pool)
    tot_f = sum(z.get("fund") or 0 for z in pool)
    print(f"--- {label}（涨停 {len(pool)} 只，成交 {tot_a/1e8:.1f}亿，封单 {tot_f/1e8:.2f}亿）---")
    for name, kws in KW.items():
        hit = [z for z in pool if any(k in (th.get(z["c"], {}).get("reason_type") or "") for k in kws)]
        if not hit:
            continue
        a = sum(z.get("amount") or 0 for z in hit)
        f = sum(z.get("fund") or 0 for z in hit)
        lb = sum(1 for z in hit if (z.get("lbc") or 0) >= 2)
        hy = len({z.get("hybk") for z in hit})
        print(f"  {name:<16} {len(hit):>2} 只 连板{lb:>2} ({lb/len(hit)*100:>4.1f}%) 离散{hy:>2} "
              f"成交{a/1e8:>7.1f}亿({a/tot_a*100:>4.1f}%) 封单{f/1e8:>5.2f}亿({f/tot_f*100 if tot_f else 0:>4.1f}%) "
              f"| " + " ".join(f"{z['n']}" for z in sorted(hit, key=lambda x: -(x.get('lbc') or 0))[:12]))
agg(p0, th0, "今日 " + D0)
print()
agg(p1, th1, "昨日 " + D1)

print("\n" + "=" * 78)
print("【五】市值分层")
print("=" * 78)
def capdist(pool, label):
    bins = [(0, 3e9, "<30亿"), (3e9, 5e9, "30-50亿"), (5e9, 1e10, "50-100亿"),
            (1e10, 3e10, "100-300亿"), (3e10, 9e18, ">300亿")]
    print(f"{label}: n={len(pool)} 合计成交 {sum(z.get('amount') or 0 for z in pool)/1e8:.1f}亿")
    for lo, hi, nm in bins:
        s = [z for z in pool if lo <= (z.get("ltsz") or 0) < hi]
        print(f"   {nm:<10} {len(s):>2} 只 ({len(s)/len(pool)*100:>4.1f}%)  成交 {sum(z.get('amount') or 0 for z in s)/1e8:>7.1f}亿")
capdist(p0, "今日")
capdist(p1, "昨日")

print("\n" + "=" * 78)
print("【六】行业迁移（含代码交集 / 轮换率）")
print("=" * 78)
h0, h1 = collections.defaultdict(set), collections.defaultdict(set)
for z in p0: h0[z.get("hybk")].add(z["c"])
for z in p1: h1[z.get("hybk")].add(z["c"])
mv = [(k, len(h0.get(k, set())), len(h1.get(k, set()))) for k in set(h0) | set(h1)]
mv.sort(key=lambda t: -((t[1] + t[2]) + abs(t[1] - t[2]) * 2))
for k, a, b in mv[:20]:
    inter = len(h0.get(k, set()) & h1.get(k, set()))
    print(f"  {str(k):<8} 今 {a:>2} 昨 {b:>2} Δ{a-b:>+3}  留存 {inter} 只  轮换率 {(1-inter/a)*100 if a else 0:>5.1f}%")
print(f"  行业数 今 {len([k for k in h0 if k and h0[k]])} 昨 {len([k for k in h1 if k and h1[k]])}")
print(f"  清零 {len([k for k in h1 if h1[k] and not h0.get(k)])}: {sorted(str(k) for k in h1 if h1[k] and not h0.get(k))}")
print(f"  新增 {len([k for k in h0 if h0[k] and not h1.get(k)])}: {sorted(str(k) for k in h0 if h0[k] and not h1.get(k))}")

print("\n" + "=" * 78)
print("【七】炸板池：回封判定（收盘价 >= 涨停价）+ 市值结构")
print("=" * 78)
zb = (d0["em_ZB"] or {}).get("pool") or []
print(f"炸板池 {len(zb)} 只（同花顺 {len(d0['ths_zb'].get('info') or [])} / 东财 tc={(d0['em_ZB'] or {}).get('tc')}）")
back = [z for z in zb if (z.get("p") or 0) >= (z.get("ztp") or 1e9)]
print(f"回封 {len(back)} 只: " + ", ".join(f"{z['n']}({z['c']}) {z.get('zdp')}%" for z in back))
for z in sorted(zb, key=lambda x: -(x.get("amount") or 0))[:14]:
    print(f"  {z['c']} {z['n']:<6} {str(z.get('hybk')):<6} 收{z.get('zdp'):>+7.2f}% 涨停价{z.get('ztp')} 现价{z.get('p')} "
          f"成交{(z.get('amount') or 0)/1e8:>6.2f}亿 流通{(z.get('ltsz') or 0)/1e8:>7.1f}亿 开板{z.get('zbc')}次")
print(f"  炸板池流通>100亿: {sum(1 for z in zb if (z.get('ltsz') or 0) > 1e10)} 只；中位流通 {statistics.median([z.get('ltsz') or 0 for z in zb])/1e8:.1f}亿")
print(f"  炸板池合计成交 {sum(z.get('amount') or 0 for z in zb)/1e8:.1f}亿")

print("\n" + "=" * 78)
print("【八】跌停池（重点）")
print("=" * 78)
dt = (d0["em_DT"] or {}).get("pool") or []
ld = d0["ths_zt"]["limit_down_count"]["today"]
print(f"同花顺汇总 跌停 {ld['num']} 触及 {ld['history_num']} 封死率 {ld['rate']*100:.1f}% 被买回 {ld['open_num']}")
print(f"东财池 {len(dt)} 只 tc={(d0['em_DT'] or {}).get('tc')}")
print(f"  东财池代码: {sorted({z['c'] for z in dt})}")
for z in sorted(dt, key=lambda x: -(x.get("amount") or 0)):
    print(f"  {z['c']} {z['n']:<6} {str(z.get('hybk')):<6} 收{z.get('zdp'):>+7.2f}% 成交{(z.get('amount') or 0)/1e8:>6.2f}亿 流通{(z.get('ltsz') or 0)/1e8:>7.1f}亿 开板{z.get('zbc')}次")
ztamt = sum(z.get("amount") or 0 for z in p0)
dtamt = sum(z.get("amount") or 0 for z in dt)
print(f"  跌停股成交 {dtamt/1e8:.1f}亿 = 涨停股 {ztamt/1e8:.1f}亿 的 {dtamt/ztamt if ztamt else 0:.2f} 倍")
hyc = collections.Counter(str(z.get('hybk')) for z in dt)
print(f"  跌停池行业 {len(hyc)} 个: {hyc.most_common()}")
print(f"  流通>100亿: {sum(1 for z in dt if (z.get('ltsz') or 0) > 1e10)} 只")
print(f"  北交所代码(920xxx): {sorted(c for c in {z['c'] for z in dt} if c.startswith('920'))}")
print(f"  昨涨停→今跌停: {sorted(c1set & {z['c'] for z in dt})}")
prevdt = (d1["em_DT"] or {}).get("pool") or []
print(f"  今日涨停∩昨日跌停池: 昨跌停 {len(prevdt)} 只 → {sorted(c0set & {z['c'] for z in prevdt})}")
print(f"  今日跌停∩昨日涨停池 只数: {len(c1set & {z['c'] for z in dt})}/{len(c1set)} = {len(c1set & {z['c'] for z in dt})/len(c1set)*100:.1f}%")

print("\n" + "=" * 78)
print("【九】昨涨停股分线表现（37 只）")
print("=" * 78)
for name, kws in KW.items():
    hit = [z for z in p1 if any(k in (th1.get(z["c"], {}).get("reason_type") or "") for k in kws)]
    chg = [y[z["c"]]["pct"] for z in hit if z["c"] in y and y[z["c"]].get("pct") is not None]
    if not chg:
        continue
    lim = sum(1 for z in hit if z["c"] in c0set)
    print(f"  {name:<16} n={len(hit):>2} 均{statistics.mean(chg):>+6.2f}% 中位{statistics.median(chg):>+6.2f}% "
          f"上涨{sum(1 for c in chg if c>0)}只 跌{sum(1 for c in chg if c<0)}只 晋级{lim}只")

print("\n" + "=" * 78)
print("【十】今日涨停股明细（按连板数、成交额）")
print("=" * 78)
for z in sorted(p0, key=lambda x: (-(x.get("lbc") or 0), -(x.get("amount") or 0))):
    rt = (th0.get(z["c"], {}).get("reason_type") or "")[:40]
    print(f"  {z.get('lbc')}板 {z['c']} {z['n']:<6} {str(z.get('hybk')):<6} 额{(z.get('amount') or 0)/1e8:>6.2f}亿 "
          f"流通{(z.get('ltsz') or 0)/1e8:>7.1f}亿 封单{(z.get('fund') or 0)/1e8:>5.2f}亿 开板{z.get('zbc')} | {rt}")

print("\n" + "=" * 78)
print("【十一】GAP 与两日对照")
print("=" * 78)
for tag, s in (("今日 " + D0, S), ("昨日 " + D1, S1)):
    perf = s["perf"]
    print(f"  {tag}: {json.dumps({k: perf[k] for k in perf if k in ('first','cont','all')}, ensure_ascii=False)[:500]}")
print("  GAP 定义 = 首板组中位 − 连板组中位")

print("\n" + "=" * 78)
print("【十二】昨日跌停池（5 只）今日表现")
print("=" * 78)
for z in prevdt:
    v = y.get(z["c"]) or {}
    print(f"  {z['c']} {z['n']:<6} {str(z.get('hybk')):<6} 昨收{z.get('zdp'):>+7.2f}% 今{v.get('pct')}")
print("\n  -- 昨日涨停池中今日跌幅>=9.8% 的 --")
for z in p1:
    v = y.get(z["c"]) or {}
    if v.get("pct") is not None and v["pct"] <= -9.8:
        print(f"  {z['c']} {z['n']:<6} 昨{z.get('lbc')}板 {str(z.get('hybk')):<6} 今{v.get('pct'):>+7.2f}%")
