# -*- coding: utf-8 -*-
"""A股涨停复盘 · 周度聚合分析（多交易日）

用法（项目根目录）：
    python scripts/zt_week_analyze.py 20260911 20260918

输入：out/zt_review_{D0}.json（多份，由 skill 的 zt_fetch.py 生成）
输出：out/zt_week_{start}_{end}.json + 控制台明细
"""
import json, os, re, sys, collections, datetime
from statistics import mean, median

ROOT = os.environ.get("ZT_ROOT") or os.getcwd()
OUT = os.path.join(ROOT, "out")

START, END = (sys.argv[1], sys.argv[2]) if len(sys.argv) >= 3 else ("20260911", "20260918")

# 载入所有可用的 fetch 快照，按日期建立「日 -> 记录」映射（同日多份时优先 D0 份）
BUNDLES = {}
for fn in sorted(os.listdir(OUT)):
    m = re.match(r"^zt_review_(\d{8})\.json$", fn)
    if not m:
        continue
    try:
        b = json.load(open(os.path.join(OUT, fn), encoding="utf-8"))
    except Exception:
        continue
    BUNDLES[m.group(1)] = b

DAY = {}          # date -> rec
for d0, b in BUNDLES.items():
    for d, rec in (b.get("dates") or {}).items():
        if d == d0 or d not in DAY:
            DAY[d] = rec

# 指数日线（成交额）合并
HIST = {}
for d0, b in BUNDLES.items():
    for code, v in (b.get("index_hist") or {}).items():
        if not v:
            continue
        slot = HIST.setdefault(code, {"name": v.get("name"), "rows": {}})
        for r in v.get("rows") or []:
            slot["rows"][r["date"]] = r

DATES = sorted(d for d in DAY if START <= d <= END)
if not DATES:
    print("!! 区间内无数据"); sys.exit(1)


def em_time(v):
    try:
        s = str(int(v)).zfill(6)
        return f"{s[0:2]}:{s[2:4]}:{s[4:6]}"
    except Exception:
        return None


def build(date):
    rec = DAY.get(date) or {}
    ths = ((rec.get("ths_zt") or {}).get("info")) or []
    em = ((rec.get("em_ZT") or {}).get("pool")) or []
    emmap = {it["c"]: it for it in em}
    rows = []
    for it in ths:
        c = it["code"]
        e = emmap.get(c, {})
        rows.append({
            "code": c, "name": it.get("name"), "reason": it.get("reason_type") or "",
            "high_days": it.get("high_days") or "", "lbc": e.get("lbc"),
            "fbt": em_time(e.get("fbt")), "fund": e.get("fund"), "amount": e.get("amount"),
            "turnover": e.get("hs"), "ltsz": e.get("ltsz"),
            "hybk": e.get("hybk") or "", "limit_up_type": it.get("limit_up_type") or "",
            "change": it.get("change_rate"),
        })
    return rows


def level(r):
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


def amt_of(date, code):
    r = ((HIST.get(code) or {}).get("rows") or {}).get(date)
    return float(r["amt"]) / 1e8 if r and r.get("amt") else None


def prev_date(d):
    i = DATES.index(d)
    return DATES[i - 1] if i > 0 else None


# ---------------- 逐日指标 ----------------
days = []
for d in DATES:
    rec = DAY.get(d) or {}
    ths = rec.get("ths_zt") or {}
    lud = ths.get("total") or {}
    info = ths.get("info") or []
    zb = len(((rec.get("ths_zb") or {}).get("info")) or [])
    ldc = ths.get("limit_down_count") or {}
    dt = ((ldc.get("today") or {}).get("num")) or 0
    # 沪深口径：同花顺 limit_up_count（em 涨停池含北交所，仅作梯队/封单来源）
    zt = (lud.get("today") or {}).get("num") or len(info)
    rows = build(d)
    lad = collections.Counter(level(r) for r in rows)
    amts = [r["amount"] for r in rows if r["amount"]]
    funds = [r["fund"] for r in rows if r["fund"]]
    sh_amt = amt_of(d, "zs_1A0001"); sz_amt = amt_of(d, "zs_399001")
    tot_amt = (sh_amt or 0) + (sz_amt or 0)
    early = sum(1 for r in rows if r["fbt"] and r["fbt"][:5] <= "10:00")

    # 晋级率：集合交集（不依赖行情快照），D-1 涨停池 ∩ D 涨停池
    pd = prev_date(d)
    rate = None; n_prev = None; n_again = None
    if pd:
        a = {r["code"] for r in build(pd)}
        b = {r["code"] for r in rows}
        n_prev = len(a); n_again = len(a & b)
        rate = n_again / n_prev * 100 if n_prev else None

    # 溢价：来自 D0=d 的快照（yesterday_zt_today = D-1 涨停股在 d 日的行情）
    prem = None; prem_med = None; green = None
    snap = (BUNDLES.get(d) or {}).get("yesterday_zt_today") or {}
    pcts = [v["pct"] for v in snap.values() if v.get("pct") is not None]
    if pcts:
        prem = mean(pcts); prem_med = median(pcts)
        green = sum(1 for p in pcts if p < 0) / len(pcts) * 100

    days.append({
        "date": d, "zt": zt, "zb": zb, "dt": dt,
        "seal": (zt / (zt + zb) * 100) if (zt + zb) else None,
        "ladder": dict(lad), "max_board": max(lad) if lad else None,
        "lianban": sum(v for k, v in lad.items() if k >= 2),
        "shouban": lad.get(1, 0),
        "fund_sum": sum(funds) / 1e8 if funds else None,
        "fund_med": median(funds) / 1e8 if funds else None,
        "amt_sum": sum(amts) / 1e8 if amts else None,
        "amt_med": median(amts) / 1e8 if amts else None,
        "amt_max": max(amts) / 1e8 if amts else None,
        "mkt_amt": tot_amt, "sh_amt": sh_amt, "sz_amt": sz_amt,
        "ratio": (sum(amts) / 1e8 / tot_amt * 100) if (amts and tot_amt) else None,
        "early": early, "early_pct": early / zt * 100 if zt else None,
        "promo": rate, "prev_zt": n_prev, "again": n_again,
        "prem_mean": prem, "prem_med": prem_med, "green_pct": green,
        "hy": dict(collections.Counter(r["hybk"] for r in rows).most_common(20)),
        "reasons": collections.Counter(r["reason"] for r in rows).most_common(40),
        "ind": collections.Counter(r["hybk"] for r in rows),
        "rsn": collections.Counter(r["reason"] for r in rows),
    })

print("=" * 96)
print(f"【周度】 {START} ~ {END}")
print("=" * 96)
hdr = f"{'日期':<10}{'涨停':>5}{'炸板':>5}{'封板率':>8}{'跌停':>5}{'最高板':>7}{'连板':>5}{'首板':>5}{'两市成交':>10}{'占比':>7}{'晋级率':>8}{'溢价中位':>9}"
print(hdr)
for x in days:
    print(f"{x['date']:<10}{x['zt']:>5}{x['zb']:>5}"
          f"{(x['seal'] or 0):>7.1f}%{x['dt']:>5}{x['max_board'] or 0:>7}{x['lianban'] or 0:>5}"
          f"{x['shouban'] or 0:>5}{x['mkt_amt']:>9.0f}亿{(x['ratio'] or 0):>6.1f}%"
          f"{(x['promo'] if x['promo'] is not None else float('nan')):>7.1f}%"
          f"{(x['prem_med'] if x['prem_med'] is not None else float('nan')):>8.2f}%")

wk = [x for x in days if x["date"] > "20260911"]
print()
print(f"本周({len(wk)}日) 涨停合计 {sum(x['zt'] for x in wk)}  日均 {mean([x['zt'] for x in wk]):.1f}  "
      f"区间 {min(x['zt'] for x in wk)}~{max(x['zt'] for x in wk)}")
print(f"封板率 均值 {mean([x['seal'] for x in wk]):.1f}%  区间 {min(x['seal'] for x in wk):.1f}~{max(x['seal'] for x in wk):.1f}%")
print(f"跌停合计 {sum(x['dt'] for x in wk)}")
print(f"两市成交额 周一起 {wk[0]['mkt_amt']:.0f}亿 -> 周五 {wk[-1]['mkt_amt']:.0f}亿  "
      f"({(wk[-1]['mkt_amt']/wk[0]['mkt_amt']-1)*100:+.1f}%)  周均 {mean([x['mkt_amt'] for x in wk]):.0f}亿")
print(f"涨停股成交占比 均值 {mean([x['ratio'] for x in wk]):.2f}%")
print(f"封单合计 周一起 {wk[0]['fund_sum']:.1f}亿 -> 周五 {wk[-1]['fund_sum']:.1f}亿")
print(f"早盘封板占比: " + "  ".join(f"{x['date'][4:]}:{x['early_pct']:.0f}%" for x in wk))

print()
print("=" * 96)
print("【连板梯队逐日】")
print("=" * 96)
alllv = sorted({k for x in days for k in x["ladder"]})
print("日期      " + "".join(f"{str(k)+'板':>7}" for k in alllv) + "   合计")
for x in days:
    print(f"{x['date']:<10}" + "".join(f"{x['ladder'].get(k,0):>7}" for k in alllv)
          + f"{x['zt']:>7}")

print()
print("=" * 96)
print("【行业热度迁移（Top，东财 hybk）】")
print("=" * 96)
allhy = sorted({k for x in days for k in x["ind"]})
rank = sorted(allhy, key=lambda k: (-sum(x["ind"].get(k, 0) for x in days), k))
print(f"{'行业':<14}" + "".join(f"{x['date'][4:]:>7}" for x in days) + f"{'合计':>7}")
for k in rank[:28]:
    tot = sum(x["ind"].get(k, 0) for x in days)
    print(f"{k:<14}" + "".join(f"{x['ind'].get(k,0):>7}" for x in days) + f"{tot:>7}")

print()
print("=" * 96)
print("【涨停原因原始串（逐日 Top12）】")
print("=" * 96)
for x in days:
    print(f"\n-- {x['date']} --")
    for r, n in x["reasons"][:12]:
        print(f"   {n:>2}  {r}")

print()
print("=" * 96)
print("【周度 Top 连板股（按出现天数）】")
print("=" * 96)
occ = collections.defaultdict(list)
for x in days:
    for r in build(x["date"]):
        lv = level(r)
        if lv >= 2:
            occ[(r["code"], r["name"])].append((x["date"], lv, r["hybk"], r["reason"]))
lb_occ = []
for (c, n), v in sorted(occ.items(), key=lambda kv: (-len(kv[1]), -max(q[1] for q in kv[1]), kv[0][0])):
    lb_occ.append({"code": c, "name": n, "n": len(v), "maxlv": max(q[1] for q in v),
                   "hybk": v[-1][2], "reason": v[-1][3],
                   "seq": [{"date": q[0], "lv": q[1]} for q in v]})
    if len(v) >= 2:
        print(f"  {c} {n:<8} 上榜{len(v)}日  " +
              " | ".join(f"{q[0][4:]} {q[1]}板" for q in v) + f"   {v[-1][2]} {v[-1][3][:26]}")

print()
print("=" * 96)
print("【题材标签迁移（关键词命中；一只票可命中多条，家数之和 > 涨停总数）】")
print("=" * 96)
THEMES = [
    ("PCB/算力硬件", ["PCB", "HDI", "覆铜板", "铜箔", "钻针", "刀具", "光模块", "CPO", "光通信",
                   "数据中心", "交换机", "服务器", "液冷", "散热", "算力", "ABF", "电子材料",
                   "电磁线", "高速铜线", "连接器", "光纤", "存储", "通信"]),
    ("半导体", ["半导体", "芯片", "硅片", "晶圆", "封装", "半导体IP", "钽", "MLCC", "模拟"]),
    ("电力/风电储能", ["风电", "海上风电", "抽水蓄能", "储能", "电网", "特高压", "电力", "热电",
                    "清洁能源", "核聚变", "光伏", "锂电"]),
    ("机器人/汽车", ["机器人", "丝杠", "减速器", "汽车", "零部件"]),
    ("消费/地产/传媒", ["食品", "家居", "零售", "服装", "家纺", "旅游", "出版", "文化", "教育",
                    "房地产", "LED", "照明", "烟草", "造纸", "包装", "文旅", "景区"]),
    ("医药", ["医药", "创新药", "医疗", "中成药", "脑机", "保健品", "营养"]),
    ("军工/安全", ["军工", "航天", "网络安全", "AI安全", "低空"]),
    ("有色化工/资源", ["有色", "化工", "化学", "煤", "焦炭", "锂", "盐", "油运", "航运", "粮食", "水泥", "玻璃"]),
    ("国资重组", ["国资", "重组", "划转", "吸收合并", "预重整", "协议转让", "资产注入"]),
]
theme_series = {}
for name, kws in THEMES:
    row = []
    for d in DATES:
        rec = DAY.get(d) or {}
        info = ((rec.get("ths_zt") or {}).get("info")) or []
        n = sum(1 for it in info if any(k in (it.get("reason_type") or "") for k in kws))
        row.append(n)
    theme_series[name] = row
print(f"{'题材':<16}" + "".join(f"{d[4:]:>7}" for d in DATES) + f"{'合计':>7}")
for name, row in sorted(theme_series.items(), key=lambda kv: -sum(kv[1])):
    print(f"{name:<16}" + "".join(f"{v:>7}" for v in row) + f"{sum(row):>7}")

fp = os.path.join(OUT, f"zt_week_{START}_{END}.json")
tmp = fp + ".tmp"
with open(tmp, "w", encoding="utf-8") as f:
    json.dump({"start": START, "end": END, "days": days, "lb_occ": lb_occ,
               "themes": theme_series, "theme_order": sorted(theme_series, key=lambda k: -sum(theme_series[k]))},
              f, ensure_ascii=False, indent=1)
os.replace(tmp, fp)
print(f"\nsaved -> out/zt_week_{START}_{END}.json")
