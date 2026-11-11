# -*- coding: utf-8 -*-
"""三日序列 + 炸板回封历史 + 涨停类型/20cm 对比"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load(p):
    with open(os.path.join(ROOT, "out", p), encoding="utf-8") as f:
        return json.load(f)

print("=" * 78)
print("三日情绪序列（各自文件的 today 字段）")
print("=" * 78)
for d in ("20261106", "20261109", "20261110", "20261111"):
    try:
        B = load(f"zt_review_{d}.json")
    except FileNotFoundError:
        print(d, "无文件"); continue
    t = B["dates"][d]["ths_zt"]
    tot, ld = t["total"]["today"], t["limit_down_count"]["today"]
    zb = B["dates"][d]["em_ZB"]["pool"] or []
    back = [z for z in zb if z["p"] >= z["ztp"] - 1e-6]
    pool = B["dates"][d]["em_ZT"]["pool"]
    yz = [z for z in pool if z["c"].startswith(("30", "68"))]
    a = sum(z.get("amount") or 0 for z in pool)
    print(f"{d} 涨停{tot['num']:>3} 触及{tot['history_num']:>3} 封板率{tot['rate']*100:>5.1f}% "
          f"炸板{len(zb):>2} 回封{len(back):>2} | 跌停{ld['num']:>2} 触及{ld['history_num']:>2} "
          f"| 成交{a/1e8:>7.1f}亿 20cm{len(yz):>2}只")

print()
print("=" * 78)
print("涨停类型对比（一字/T字/换手）")
print("=" * 78)
for d in ("20261110", "20261111"):
    info = load(f"zt_review_{d}.json")["dates"][d]["ths_zt"]["info"]
    import collections
    c = collections.Counter(i.get("limit_up_type") for i in info)
    print(d, dict(c), "合计", len(info))

print()
print("=" * 78)
print("今日炸板池 首封时间分布 / 昨日")
print("=" * 78)
for d in ("20261110", "20261111"):
    zb = load(f"zt_review_{d}.json")["dates"][d]["em_ZB"]["pool"]
    import collections
    c = collections.Counter()
    for z in zb:
        fb = z.get("fbt")
        if not fb: c["未知"] += 1; continue
        s = str(int(fb)).zfill(6); h = int(s[:2])
        c["09:25前"] += 1 if h == 9 and int(s[2:4]) <= 25 else 0
        if h < 11 or (h == 11 and int(s[2:4]) <= 30):
            if not (h == 9 and int(s[2:4]) <= 25): c["上午"] += 1
        elif h == 11 or h == 13 or (h == 14 and int(s[2:4]) <= 30): c["午后"] += 1
        else: c["尾盘"] += 1
    print(d, dict(c))
