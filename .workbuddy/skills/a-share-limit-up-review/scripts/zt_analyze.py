# -*- coding: utf-8 -*-
"""A股涨停复盘 · 分析（情绪温度计 / 连板梯队 / 题材归因 / 晋级率 / 资金运动）

用法：
    python zt_analyze.py                          # 默认今日 / 上一交易日
    python zt_analyze.py 20260916 20260915 20260914   # D0 今日 / D1 昨日 / D2 前日

输入：out/zt_review_{D0}.json（由 zt_fetch.py 生成）
输出：out/zt_stats_{D0}.json（供 zt_report_*.py 消费）+ 控制台全量明细
"""
import json, os, sys, re, datetime, collections
from statistics import mean, median

# 数据根目录：优先环境变量 ZT_ROOT，否则取当前工作目录（须与 zt_fetch.py 一致）
ROOT = os.environ.get("ZT_ROOT") or os.getcwd()
OUT = os.path.join(ROOT, "out")


def prev_weekday(ds):
    d = datetime.datetime.strptime(ds, "%Y%m%d").date() - datetime.timedelta(days=1)
    while d.weekday() >= 5:
        d -= datetime.timedelta(days=1)
    return d.strftime("%Y%m%d")


def resolve_dates(argv):
    if len(argv) >= 3:
        return argv[0], argv[1], argv[2]
    if len(argv) == 2:
        return argv[0], argv[1], prev_weekday(argv[1])
    if len(argv) == 1:
        return argv[0], prev_weekday(argv[0]), prev_weekday(prev_weekday(argv[0]))
    d0 = datetime.date.today().strftime("%Y%m%d")
    d1 = prev_weekday(d0)
    return d0, d1, prev_weekday(d1)


D0, D1, D2 = resolve_dates(sys.argv[1:])
B = json.load(open(os.path.join(OUT, f"zt_review_{D0}.json"), encoding="utf-8"))
D = B["dates"]


def ts2hhmm(ts):
    """同花顺 first_limit_up_time 为 unix 秒（东八区）"""
    try:
        ts = int(ts)
    except Exception:
        return None
    t = datetime.datetime.fromtimestamp(ts, datetime.timezone(datetime.timedelta(hours=8)))
    return t.strftime("%H:%M:%S")


def em_time(v):
    """东财 fbt: 92500 -> 09:25:00"""
    try:
        s = str(int(v)).zfill(6)
        return f"{s[0:2]}:{s[2:4]}:{s[4:6]}"
    except Exception:
        return None


def build(date):
    """合并同花顺(原因/梯队) + 东财(封单/行业) 的涨停明细"""
    rec = D.get(date) or {}
    ths = ((rec.get("ths_zt") or {}).get("info")) or []
    em = ((rec.get("em_ZT") or {}).get("pool")) or []
    emmap = {it["c"]: it for it in em}
    rows = []
    for it in ths:
        c = it["code"]
        e = emmap.get(c, {})
        rows.append({
            "code": c,
            "name": it.get("name"),
            "reason": it.get("reason_type") or "",
            "high_days": it.get("high_days") or "",
            "lbc": e.get("lbc"),
            # 封板时间以东财为准（HHMMSS），同花顺时间戳作交叉校验
            "fbt": em_time(e.get("fbt")),
            "fbt_ths": ts2hhmm(it.get("first_limit_up_time")),
            "lbt": em_time(e.get("lbt")),
            "open_num": it.get("open_num"),
            # 成交额/换手/市值/封单一律取东财（已用 换手率×流通市值=成交额 三角校验）
            "fund": e.get("fund"),
            "amount": e.get("amount"),
            "turnover": e.get("hs"),
            "change": it.get("change_rate"),
            "ltsz": e.get("ltsz"),
            "tshare": e.get("tshare"),
            "hybk": e.get("hybk") or "",
            "limit_up_type": it.get("limit_up_type") or "",
            "is_again": it.get("is_again_limit"),
        })
    return rows


def ladder(rows):
    """连板梯队：东财 lbc 为主，缺失回退同花顺 high_days 文本"""
    def lv(r):
        if r["lbc"]:
            return int(r["lbc"])
        s = r["high_days"]
        m = re.match(r"^(\d+)连板$", s)
        if m:
            return int(m.group(1))
        m = re.match(r"^(\d+)天(\d+)板$", s)
        if m:
            return int(m.group(2))
        return 1
    return collections.Counter(lv(r) for r in rows)


def timeslot(hhmm):
    if not hhmm:
        return "未知"
    try:
        v = int(hhmm[:5].replace(":", ""))
    except Exception:
        return "未知"
    if v <= 925:
        return "竞价/秒板"
    if v <= 1000:
        return "开盘半小时"
    if v <= 1130:
        return "上午盘中"
    if v <= 1430:
        return "午后盘中"
    if v <= 1500:
        return "尾盘"
    return "未知"


print("=" * 70)
print(f"【一】情绪温度计  今日={D0} 昨日={D1} 前日={D2}")
print("=" * 70)
senti = {}
for d, tag in [(D0, "今日"), (D1, "昨日"), (D2, "前日")]:
    rec = D.get(d) or {}
    ths = rec.get("ths_zt") or {}
    lud = ths.get("total") or {}
    y = (lud.get("yesterday") or {})
    info = ths.get("info") or []
    zb = len(((rec.get("ths_zb") or {}).get("info")) or [])
    ldc = ths.get("limit_down_count") or {}
    dt = ((ldc.get("today") or {}).get("num")) or 0
    dt_y = ((ldc.get("yesterday") or {}).get("num")) or 0
    zt_y = (lud.get("yesterday") or {}).get("num") or 0
    zb_y = (lud.get("yesterday") or {}).get("open_num") or 0
    rows = build(d) if d in (D0, D1) else []
    lad = ladder(rows) if rows else {}
    senti[d] = {
        "zt": len(info), "zb": zb, "dt": dt,
        "zt_prev": zt_y, "zb_prev": zb_y, "dt_prev": dt_y,
        "seal_rate": (len(info) / (len(info) + zb)) if (len(info) + zb) else None,
        "ladder": dict(lad),
        "max_board": max(lad) if lad else None,
        "lianban": sum(v for k, v in lad.items() if k >= 2) if lad else None,
        "shouban": lad.get(1, 0) if lad else None,
        "yest": y, "limit_down_count": ldc,
    }
    print(f"\n[{tag} {d}]  涨停={len(info)}  炸板={zb}  "
          f"封板率={(len(info)/(len(info)+zb)*100 if (len(info)+zb) else 0):.1f}%  跌停={dt}")
    print(f"   前一交易日: 涨停={zt_y} 炸板={zb_y} 跌停={dt_y}")
    print(f"   涨停统计字段: {json.dumps(lud, ensure_ascii=False)}")
    print(f"   跌停统计字段: {json.dumps(ldc, ensure_ascii=False)[:200]}")
    if lad:
        print("   梯队:", dict(sorted(lad.items())))

print()
print("=" * 70)
print("【二】指数表现（今日 vs 昨日）")
print("=" * 70)
idx = B.get("indexes") or {}
h = B.get("index_hist") or {}


def hist_row(code, date):
    for x in ((h.get(code) or {}).get("rows") or []):
        if x["date"] == date:
            return x
    return None


pairs = [("sh000001", "zs_1A0001", "上证指数"), ("sz399001", "zs_399001", "深证成指"),
         ("sz399006", "zs_399006", "创业板指"), ("sh000688", "zs_1B0688", "科创50")]
tot = {"today": 0.0, "prev": 0.0}
idx_cmp = {}
for sym, hcode, nm in pairs:
    v = idx.get(sym) or {}
    cur_amt = (v.get("amount_wan") or 0) / 10000.0
    y = hist_row(hcode, D1)
    y2 = hist_row(hcode, D2)
    y_amt = float(y["amt"]) / 1e8 if y and y.get("amt") else None
    y_pct = None
    if y and y2 and float(y2["close"]):
        y_pct = (float(y["close"]) / float(y2["close"]) - 1) * 100
    idx_cmp[nm] = {"today_pct": v.get("pct"), "prev_pct": y_pct,
                   "today_amt": cur_amt, "prev_amt": y_amt}
    print(f"  {nm:<8} 今收{v.get('price'):<10} 今{v.get('pct'):>6.2f}%  昨{(y_pct or 0):>6.2f}%  "
          f"成交额 今{cur_amt:>8.1f}亿 / 昨{(y_amt or 0):>8.1f}亿")
    if nm in ("上证指数", "深证成指"):
        tot["today"] += cur_amt
        tot["prev"] += y_amt or 0
print(f"  >> 沪深两市合计成交额: 今日 {tot['today']:.0f}亿  昨日 {tot['prev']:.0f}亿  "
      f"增量 {tot['today']-tot['prev']:+.0f}亿 ({(tot['today']/tot['prev']-1)*100:+.1f}%)")
print("  其他指数（今日）:")
for k, v in idx.items():
    if v["name"] in ("上证指数", "深证成指", "创业板指", "科创50"):
        continue
    print(f"    {v['name']:<8} {v['pct']:>6.2f}%")

print()
print("=" * 70)
print("【三】连板梯队明细（今日）")
print("=" * 70)
r0 = build(D0)
r1 = build(D1)
for r in sorted(r0, key=lambda x: -(x["lbc"] or 0)):
    if (r["lbc"] or 1) >= 2:
        print(f"  {r['lbc']}板 {r['code']} {r['name']:<8} {r['fbt']} "
              f"封单{(r['fund'] or 0)/1e8:.2f}亿 额{(r['amount'] or 0)/1e8:.2f}亿 "
              f"[{r['high_days']}] {r['hybk']} | {r['reason']}")

print()
print("=" * 70)
print("【四】今日涨停题材归因（原始 reason_type 去重；一只票可命中多条线）")
print("=" * 70)
reasons = collections.Counter(r["reason"] for r in r0)
for k, v in reasons.most_common(100):
    print(f"  {v:>2}  {k}")

print()
print("=" * 70)
print("【五】东财行业分布 今日 vs 昨日")
print("=" * 70)
hy0 = collections.Counter(r["hybk"] for r in r0)
hy1 = collections.Counter(r["hybk"] for r in r1)
# tie-break 必须完整：只用加权计数排序时同分项先后取决于 set() 迭代顺序（str 哈希随机化），
# 会导致同一份数据两次输出顺序不同
allhy = sorted(set(list(hy0) + list(hy1)),
               key=lambda k: (-(hy0.get(k, 0) + hy1.get(k, 0)), -hy0.get(k, 0), -hy1.get(k, 0), k))
for k in allhy[:40]:
    print(f"  {k:<14} 今日{hy0.get(k,0):>3}  昨日{hy1.get(k,0):>3}")

print()
print("=" * 70)
print("【六】今日涨停封板时间分布")
print("=" * 70)
ts0 = collections.Counter(timeslot(r["fbt"]) for r in r0)
ts1 = collections.Counter(timeslot(r["fbt"]) for r in r1)
for k in ["竞价/秒板", "开盘半小时", "上午盘中", "午后盘中", "尾盘", "未知"]:
    print(f"  {k:<10} 今日{ts0.get(k,0):>3}  昨日{ts1.get(k,0):>3}")

print()
print("=" * 70)
print("【七】昨日涨停股今日表现（晋级率 / 溢价）")
print("=" * 70)
q = B.get("yesterday_zt_today") or {}


def sym_of(code):
    if code.startswith(("60", "68", "5", "11", "9")): return "sh" + code
    if code.startswith(("43", "83", "87", "92")): return "bj" + code
    return "sz" + code


yest_names = {r["code"]: (r["name"], r["lbc"] or 1, r["hybk"], r["reason"]) for r in r1}
today_zt_set = {r["code"] for r in r0}
rows_perf = []
for c in [r["code"] for r in r1]:
    v = q.get(sym_of(c))
    if not v:
        continue
    rows_perf.append({"code": c, "name": yest_names[c][0], "lbc": yest_names[c][1],
                      "hybk": yest_names[c][2], "reason": yest_names[c][3],
                      "pct": v["pct"], "price": v["price"], "amount": v["amount_wan"],
                      "again": c in today_zt_set})
pcts = [r["pct"] for r in rows_perf if r["pct"] is not None]
again = [r for r in rows_perf if r["again"]]
print(f"  样本: {len(rows_perf)} 只")
print(f"  晋级(今日再涨停): {len(again)} 只 -> 晋级率 {len(again)/max(len(rows_perf),1)*100:.1f}%")
print(f"  今日涨幅 均值 {mean(pcts):.2f}%  中位 {median(pcts):.2f}%  最大 {max(pcts):.2f}%  最小 {min(pcts):.2f}%")
print(f"  翻绿(跌): {sum(1 for p in pcts if p < 0)} 只  ({sum(1 for p in pcts if p<0)/len(pcts)*100:.1f}%)")
print(f"  跌超5%: {sum(1 for p in pcts if p < -5)} 只")
grp = collections.defaultdict(list)
for r in rows_perf:
    grp["昨日首板" if r["lbc"] == 1 else "昨日连板"].append(r)
print("  分组对比:")
for k in ["昨日首板", "昨日连板"]:
    g = grp.get(k) or []
    if not g:
        continue
    gp = [x["pct"] for x in g if x["pct"] is not None]
    ga = sum(1 for x in g if x["again"])
    print(f"   {k}: n={len(g)}  晋级率{ga/len(g)*100:.1f}%  均涨{mean(gp):+.2f}%  "
          f"中位{median(gp):+.2f}%  翻绿{sum(1 for p in gp if p < 0)}只")

print("\n  明细:")
for r in sorted(rows_perf, key=lambda x: -(x["pct"] or -99)):
    flag = "★晋级" if r["again"] else "     "
    print(f"   {flag} {r['code']} {r['name']:<8} 昨{r['lbc']}板 今{r['pct']:>7.2f}%  {r['hybk']:<10} {r['reason'][:30]}")

print()
print("=" * 70)
print("【八】今日涨停股成交额结构")
print("=" * 70)
amts = [r["amount"] for r in r0 if r["amount"]]
funds = [r["fund"] for r in r0 if r["fund"]]
print(f"  涨停股合计成交额: {sum(amts)/1e8:.1f}亿  均值 {mean(amts)/1e8:.2f}亿  中位 {median(amts)/1e8:.2f}亿")
print(f"  封单合计: {sum(funds)/1e8:.1f}亿  均值 {mean(funds)/1e8:.2f}亿  中位 {median(funds)/1e8:.2f}亿")
print(f"  一字板: {sum(1 for r in r0 if '一字' in r['limit_up_type'])}  "
      f"T字板: {sum(1 for r in r0 if 'T字' in r['limit_up_type'])}  "
      f"换手板: {sum(1 for r in r0 if '换手' in r['limit_up_type'])}")
print(f"  校验: 涨停股合计成交额 / 两市成交额({tot['today']:.0f}亿) = {sum(amts)/1e8/tot['today']*100:.1f}%")

print()
print("=" * 70)
print("【九】封板时间一致性校验（东财 fbt vs 同花顺时间戳）")
print("=" * 70)
same = sum(1 for r in r0 if r["fbt"] and r["fbt_ths"] and r["fbt"][:5] == r["fbt_ths"][:5])
have = sum(1 for r in r0 if r["fbt"] and r["fbt_ths"])
print(f"  可比样本 {have} 只，分钟级一致 {same} 只 ({same/max(have,1)*100:.0f}%)")

fp = os.path.join(OUT, f"zt_stats_{D0}.json")
tmp = fp + ".tmp"
with open(tmp, "w", encoding="utf-8") as f:
    json.dump({"D0": D0, "D1": D1, "D2": D2,
               "senti": senti, "hy0": dict(hy0), "hy1": dict(hy1),
               "idx_cmp": idx_cmp, "tot": tot, "reasons": dict(reasons.most_common(100)),
               "perf": rows_perf, "r0": r0, "r1": r1,
               "timeslot": {"today": dict(ts0), "yesterday": dict(ts1)}},
              f, ensure_ascii=False, indent=1)
os.replace(tmp, fp)
print(f"\nsaved -> out/zt_stats_{D0}.json")
