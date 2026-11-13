# -*- coding: utf-8 -*-
"""20261113 涨停复盘报告（对比 20261112）"""
import json, os, sys, collections, html, statistics

ROOT = os.environ.get("ZT_ROOT") or os.getcwd()
OUT = os.path.join(ROOT, "out"); REP = os.path.join(ROOT, "reports")
os.makedirs(REP, exist_ok=True)

D0, D1, D2 = "20261113", "20261112", "20261111"
S = json.load(open(os.path.join(OUT, "zt_stats_%s.json" % D0), encoding="utf-8"))
S1 = json.load(open(os.path.join(OUT, "zt_stats_%s.json" % D1), encoding="utf-8"))
B = json.load(open(os.path.join(OUT, "zt_review_%s.json" % D0), encoding="utf-8"))
B1 = json.load(open(os.path.join(OUT, "zt_review_%s.json" % D1), encoding="utf-8"))
B2 = json.load(open(os.path.join(OUT, "zt_review_%s.json" % D2), encoding="utf-8"))

d0, d1, d2 = B["dates"][D0], B["dates"][D1], B2["dates"][D2]
p0, p1 = d0["em_ZT"]["pool"], d1["em_ZT"]["pool"]
th0 = {i["code"]: i for i in d0["ths_zt"]["info"]}
th1 = {i["code"]: i for i in d1["ths_zt"]["info"]}
Y = {v["code"]: v for v in B["yesterday_zt_today"].values()}
c0set = {z["c"] for z in p0}; c1set = {z["c"] for z in p1}

s0, s1 = S["senti"][D0], S["senti"][D1]
ld0 = d0["ths_zt"]["limit_down_count"]["today"]
ld1 = d1["ths_zt"]["limit_down_count"]["today"]
ld2 = d2["ths_zt"]["limit_down_count"]["today"]
t0 = d0["ths_zt"]["total"]["today"]; t1 = d1["ths_zt"]["total"]["today"]; t2 = d2["ths_zt"]["total"]["today"]

def md(ds): return "%d/%d" % (int(ds[4:6]), int(ds[6:8]))
def esc(s): return html.escape(str(s))
def dz(v): return "0" if v == 0 else ("%+d" % v)
def d1z(v): return "0" if abs(v) < 0.005 else ("%+.1f" % v)

ZT, ZT1 = t0["num"], t1["num"]
ZBC, ZBC1 = s0["zb"], s1["zb"]
SEAL = t0["rate"] * 100; SEAL1 = t1["rate"] * 100
TOUCH, TOUCH1 = t0["history_num"], t1["history_num"]
DT, DT1 = ld0["num"], ld1["num"]
DT_T, DT_T1 = ld0["history_num"], ld1["history_num"]
DT_R, DT_R1 = ld0["rate"] * 100, ld1["rate"] * 100

# ---- 指数 ----
IX_ORDER = [("上证指数", "sh000001"), ("深证成指", "sz399001"), ("创业板指", "sz399006"),
            ("科创50", "sh000688"), ("中证1000", "sh000852"), ("国证2000", "sz399303"),
            ("中证500", "sh000905"), ("沪深300", "sh000300"), ("北证50", "bj899050"),
            ("上证50", "sh000016"), ("中小100", "sz399005")]
ix = []
for nm, sym in IX_ORDER:
    a, b_ = B["indexes"].get(sym), B1["indexes"].get(sym)
    if not a: continue
    amt = (a["amount_wan"] or 0) / 1e4
    amt_p = (b_["amount_wan"] or 0) / 1e4 if b_ else 0
    pc = b_["price"] if b_ and b_.get("price") else 0
    ix.append({"name": nm, "pct": a["pct"], "amt": amt, "amt_p": amt_p,
               "dpct": (amt / amt_p - 1) * 100 if amt_p else 0.0,
               "gap": (a["open"] / pc - 1) * 100 if pc else 0.0,
               "low": (a["low"] / pc - 1) * 100 if pc else 0.0,
               "pos": (a["price"] / a["high"] - 1) * 100 if a.get("high") else 0.0,
               "below": (a["price"] < a["open"]) if a.get("open") else False})
ixr = {x["name"]: x for x in ix}
AMT = ixr["上证指数"]["amt"] + ixr["深证成指"]["amt"]
AMT1 = ixr["上证指数"]["amt_p"] + ixr["深证成指"]["amt_p"]
N_UP = sum(1 for x in ix if x["pct"] > 0)
N_AMT_UP = sum(1 for x in ix if x["dpct"] > 0)
N_BELOW = sum(1 for x in ix if x["below"])
KC = ixr["科创50"]; SZ50 = ixr["上证50"]; CYB = ixr["创业板指"]

# ---- 梯队 ----
lad0 = {int(k): v for k, v in s0["ladder"].items()}
lad1 = {int(k): v for k, v in s1["ladder"].items()}
MAXB = max(lad0); MAXB1 = max(lad1)
LADM = max(MAXB, MAXB1)
LB_N = sum(v for k, v in lad0.items() if k >= 2)
LB_N1 = sum(v for k, v in lad1.items() if k >= 2)
SB_N = lad0.get(1, 0); SB_N1 = lad1.get(1, 0)

# ---- 成交结构 ----
amt_sum = sum(z.get("amount") or 0 for z in p0) / 1e8
amt_sum1 = sum(z.get("amount") or 0 for z in p1) / 1e8
fund_sum = sum(z.get("fund") or 0 for z in p0) / 1e8
fund_sum1 = sum(z.get("fund") or 0 for z in p1) / 1e8
fund_med = statistics.median([z.get("fund") or 0 for z in p0]) / 1e8
fund_med1 = statistics.median([z.get("fund") or 0 for z in p1]) / 1e8
amt_med = statistics.median([z.get("amount") or 0 for z in p0]) / 1e8
amt_med1 = statistics.median([z.get("amount") or 0 for z in p1]) / 1e8
SHARE = amt_sum / AMT * 100
SHARE1 = amt_sum1 / AMT1 * 100
oneword = sum(1 for r in S["r0"] if "一字" in (r.get("limit_up_type") or ""))
tword = sum(1 for r in S["r0"] if "T字" in (r.get("limit_up_type") or ""))
huanshou = sum(1 for r in S["r0"] if "换手" in (r.get("limit_up_type") or ""))
c20 = sum(1 for z in p0 if str(z["c"]).startswith(("30", "68", "43", "83", "87", "92")))

# ---- 昨日涨停股表现 ----
perf = S["perf"]
adv = [p for p in perf if p["again"]]
pcts = [p["pct"] for p in perf if p["pct"] is not None]
first = [p for p in perf if (p["lbc"] or 1) == 1]
cont = [p for p in perf if (p["lbc"] or 0) >= 2]
f_rate = sum(1 for p in first if p["again"]) / len(first) * 100
c_rate = sum(1 for p in cont if p["again"]) / len(cont) * 100
f_med = statistics.median([p["pct"] for p in first]); c_med = statistics.median([p["pct"] for p in cont])
f_mean = statistics.mean([p["pct"] for p in first]); c_mean = statistics.mean([p["pct"] for p in cont])
GAP = f_med - c_med
GAP1 = statistics.median([p["pct"] for p in S1["perf"] if (p["lbc"] or 1) == 1]) - \
       statistics.median([p["pct"] for p in S1["perf"] if (p["lbc"] or 0) >= 2])
S10 = json.load(open(os.path.join(OUT, "zt_stats_%s.json" % D2), encoding="utf-8"))
GAP2 = statistics.median([p["pct"] for p in S10["perf"] if (p["lbc"] or 1) == 1]) - \
       statistics.median([p["pct"] for p in S10["perf"] if (p["lbc"] or 0) >= 2])
neg = sum(1 for p in pcts if p < 0)
neg5 = sum(1 for p in pcts if p <= -5)
lim_dn = [p for p in perf if p["pct"] <= -9.8]

# ---- 炸板池 ----
zb = (d0["em_ZB"] or {}).get("pool") or []
zb_back = [z for z in zb if (z.get("p") or 0) >= (z.get("ztp") or 1e9)]
zb_amt = sum(z.get("amount") or 0 for z in zb) / 1e8
zb_big = sum(1 for z in zb if (z.get("ltsz") or 0) > 1e10)
zb_hi = [z for z in zb if z["c"] in c1set]
zb_ratio = zb_amt / amt_sum
zb_top = sorted(zb, key=lambda x: -(x.get("amount") or 0))[:12]

# ---- 跌停池（东财 getTopicDTPool?sort=fund:asc 单独抓取） ----
_dtp = json.load(open(os.path.join(OUT, "_dtpool_%s.json" % D0), encoding="utf-8"))
dtp = [{"c": z["c"], "n": z["n"], "hybk": z.get("hybk"),
        "zdp": z.get("zdp") or 0,
        "amount": (z.get("amount") or 0) / 1e8,
        "ltsz": (z.get("ltsz") or 0) / 1e8} for z in _dtp]
dt_amt = sum(z["amount"] for z in dtp)
dt_ratio = dt_amt / amt_sum
dt_from_zt = [z for z in dtp if z["c"] in c1set]
DT_POOL_N = len(dtp)
DT_GAP = DT_POOL_N - DT
dt_hy = collections.Counter(str(z["hybk"]) for z in dtp)
DT_BIG = [z for z in dtp if z["ltsz"] > 100]
dt_prev = (d1["em_DT"] or {}).get("pool") or []
DT_PREV_N = len(dt_prev)
INT_DT = sorted(c0set & {z["c"] for z in dt_prev})

# ---- 主线聚类 ----
KW = [
    ("AI 应用 / 影视短剧", ["AI漫剧", "短剧", "AI影视", "AI游戏", "游戏", "IP", "影视", "剧集", "传媒", "AI应用", "电影院线", "院线"]),
    ("机器人 / 具身智能", ["机器人", "具身智能", "减速器", "丝杠", "关节", "电子皮肤", "灵巧手", "谐波", "滚珠"]),
    ("算力硬件（光模块∪PCB∪算力）", ["光模块", "CPO", "光通信", "光纤", "光芯片", "空芯光纤", "MPO", "铜缆", "6G",
                              "PCB", "覆铜板", "玻璃基", "算力", "数据中心", "液冷", "服务器", "交换机", "HBM", "智算"]),
    ("汽车零部件 / 零部件链", ["汽车零部件", "汽车管路", "变速器", "曲轴", "车辆齿轮", "汽车洗涤"]),
    ("半导体 / 芯片 / 光刻胶", ["存储芯片", "半导体", "芯片测试", "半导体设备", "光刻胶", "GPU", "电子化学品", "合成树脂"]),
    ("“东方系”名称博弈", ["“东方系”", "“东方”"]),
    ("“羊”字辈名称博弈", ["“羊”字辈"]),
    ("光伏 / 玻璃基板", ["光伏", "玻璃基板", "光伏玻璃"]),
    ("海洋经济 / 养殖", ["海洋", "水产", "海参", "渔业", "鱼粉"]),
    ("零售 / 百货", ["百货", "零售", "免税"]),
    ("燃气 / 供热", ["燃气", "天然气", "LNG", "供热"]),
]
def theme_rows(pool, th):
    ta = sum(z.get("amount") or 0 for z in pool)
    out = []
    for nm, kws in KW:
        hit = [z for z in pool
               if any(k in (th.get(z["c"], {}).get("reason_type") or "") for k in kws)]
        if not hit: continue
        out.append({"name": nm, "n": len(hit),
                    "lb": sum(1 for z in hit if (z.get("lbc") or 0) >= 2),
                    "hy": len({z.get("hybk") for z in hit}),
                    "amt": sum(z.get("amount") or 0 for z in hit) / 1e8,
                    "shr": sum(z.get("amount") or 0 for z in hit) / ta * 100 if ta else 0,
                    "stocks": [z["n"] for z in sorted(hit, key=lambda x: -(z_amt(x)))][:10]})
    return out
def z_amt(x): return x.get("amount") or 0
TH0 = theme_rows(p0, th0); TH1 = theme_rows(p1, th1)
THM = {t["name"]: t for t in TH0}
THM1 = {t["name"]: t for t in TH1}
JSKW = "算力硬件（光模块∪PCB∪算力）"
AIK = "AI 应用 / 影视短剧"
RBK = "机器人 / 具身智能"
AUTO = "汽车零部件 / 零部件链"

# ---- 概念板块榜 + 离散度 ----
blk = []
for b in (d0.get("ths_block") or [])[:10]:
    codes = [x["code"] for x in (b.get("stock_list") or [])]
    hys = {(p0z.get("hybk")) for p0z in [next((z for z in p0 if z["c"] == c), {}) for c in codes]}
    hys = {h for h in hys if h}
    n = b.get("limit_up_num") or 0; contn = b.get("continuous_plate_num") or 0
    blk.append({"name": b.get("name"), "n": n, "cont": contn,
                "pct": contn / n * 100 if n else 0, "hy": len(hys),
                "fake": (len(hys) >= 6 and n >= 6), "high": b.get("high")})
FAKE_N = sum(1 for b in blk if b["fake"])
TOP_BLK = blk[0] if blk else {"name": "-", "n": 0, "cont": 0, "pct": 0, "hy": 0}
BLK_MAX_PCT = max(b["pct"] for b in blk[:7]) if blk else 0
BLK_MAX_NAME = [b["name"] for b in blk[:7] if b["pct"] == BLK_MAX_PCT][0] if blk else "-"

# ---- 行业迁移 ----
hy0d, hy1d = S["hy0"], S["hy1"]
hy_keys = sorted(set(list(hy0d) + list(hy1d)),
                 key=lambda k: (-((hy0d.get(k, 0) + hy1d.get(k, 0)) + abs(hy0d.get(k, 0) - hy1d.get(k, 0)) * 2),
                                -hy0d.get(k, 0), -hy1d.get(k, 0), k))
hy_tbl = [{"name": k, "t": hy0d.get(k, 0), "y": hy1d.get(k, 0)} for k in hy_keys[:16]]
h0s, h1s = collections.defaultdict(set), collections.defaultdict(set)
for z in p0: h0s[z.get("hybk")].add(z["c"])
for z in p1: h1s[z.get("hybk")].add(z["c"])
HY_N = len([k for k in h0s if k]); HY_N1 = len([k for k in h1s if k])
CLR = [k for k in h1s if h1s[k] and not h0s.get(k)]
NEW = [k for k in h0s if h0s[k] and not h1s.get(k)]
AUTO_ROT = 1 - len(h0s.get("汽车零部", set()) & h1s.get("汽车零部", set())) / max(len(h0s.get("汽车零部", set())), 1)

# ---- 封板时间 ----
TS_ORDER = ["竞价/秒板", "开盘半小时", "上午盘中", "午后盘中", "尾盘"]
ts0, ts1 = S["timeslot"]["today"], S["timeslot"]["yesterday"]
TS_E0 = ts0.get("竞价/秒板", 0) + ts0.get("开盘半小时", 0)
TS_E1 = ts1.get("竞价/秒板", 0) + ts1.get("开盘半小时", 0)

# ---- 市值分层 ----
def capdist(pool):
    bins = [(0, 3e9, "&lt;30亿"), (3e9, 5e9, "30–50亿"), (5e9, 1e10, "50–100亿"),
            (1e10, 3e10, "100–300亿"), (3e10, 9e18, "&gt;300亿")]
    return [{"nm": nm, "n": len([z for z in pool if lo <= (z.get("ltsz") or 0) < hi]),
             "amt": sum(z.get("amount") or 0 for z in pool if lo <= (z.get("ltsz") or 0) < hi) / 1e8}
            for lo, hi, nm in bins]
CAP0, CAP1 = capdist(p0), capdist(p1)
BIG0 = [z for z in p0 if (z.get("ltsz") or 0) > 3e10]
BIG0_NM = "、".join(z["n"] for z in BIG0)

# ---- 缺口 / 上证位置 ----
GAP_UP, GAP_DN = 3689.91, 3612.15
SH_OPEN = B["indexes"]["sh000001"]["open"]; SH_HIGH = B["indexes"]["sh000001"]["high"]
SH_LOW = B["indexes"]["sh000001"]["low"]; SH_CLOSE = B["indexes"]["sh000001"]["price"]
SH_PREV = B1["indexes"]["sh000001"]["price"]
GAP_FILL = SH_HIGH - GAP_UP

# ================= 表格 =================
def _srow(lab, a, b, c, unit="", rev=False):
    diff = c - b
    good = (diff < 0) if rev else (diff > 0)
    cls = "mut" if diff == 0 else ("up" if good else "down")
    txt = ("0" if abs(diff) < 0.005 else ("%+.1f" % diff)) if unit else dz(diff)
    return "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td class='hl'>{3}</td><td class='{4}'>{5}{6}</td></tr>".format(
        lab, a, b, c, cls, txt, unit)
tbl_senti = "".join([
    _srow("涨停家数", t2["num"], ZT1, ZT),
    _srow("触及涨停家数", t2["history_num"], TOUCH1, TOUCH),
    _srow("炸板家数", s1["zb_prev"], ZBC1, ZBC, rev=True),
    _srow("封板率(%)", round(t2["rate"] * 100, 1), round(SEAL1, 1), round(SEAL, 1), "pct"),
    _srow("跌停家数", ld2["num"], DT1, DT, rev=True),
    _srow("触及跌停家数", ld2["history_num"], DT_T1, DT_T, rev=True),
    _srow("跌停封死率(%)", round(ld2["rate"] * 100, 1), round(DT_R1, 1), round(DT_R, 1), "pct", rev=True),
])

tbl_lad = "".join(
    "<tr><td>{0} 板</td><td>{1}</td><td class='hl'>{2}</td><td class='{3}'>{4}</td></tr>".format(
        i, lad1.get(i, 0), lad0.get(i, 0),
        "up" if lad0.get(i, 0) - lad1.get(i, 0) > 0 else ("down" if lad0.get(i, 0) - lad1.get(i, 0) < 0 else "mut"),
        dz(lad0.get(i, 0) - lad1.get(i, 0)))
    for i in range(LADM, 0, -1))

lb_all = sorted([z for z in p0 if (z.get("lbc") or 0) >= 2],
                key=lambda x: (-(x.get("lbc") or 0), -(x.get("amount") or 0)))
B3 = sorted([z for z in p0 if (z.get("lbc") or 0) == 3], key=lambda x: -(x.get("amount") or 0))
TOPF = max(p0, key=lambda x: x.get("fund") or 0)
# 昨日「羊」字辈今日表现（从今日 stats 的 perf 现算：perf = 昨日涨停股 × 今日涨幅）
_ys = [p for p in perf if "“羊”" in (p.get("reason") or "")]
YANG_MED = statistics.median([p["pct"] for p in _ys]) if _ys else 0.0
YANG_DOWN = sum(1 for p in _ys if p["pct"] < 0)
YANG_NUM = len(_ys)
# 11-12 的「昨涨停→今跌停」与跌停/涨停成交比（11-12 报告口径：3 只 / 跌停 5 只 65.87 亿）
DT_FROM_Y_N = 3
DT_RATIO_Y = 0.23
def hhmm(v):
    s = str(int(v)).zfill(6); return s[:2] + ":" + s[2:4]
tbl_lb = "".join(
    "<tr><td>{0}板</td><td>{1}</td><td class='hl'>{2}</td><td>{3}</td><td>{4:.2f}亿</td>"
    "<td>{5:.2f}亿</td><td>{6:.1f}亿</td><td>{7}</td><td style='text-align:left;color:#4b5563'>{8}</td></tr>".format(
        z.get("lbc"), z["c"], esc(z["n"]), hhmm(z["fbt"]) if z.get("fbt") else "—",
        (z.get("fund") or 0) / 1e8, (z.get("amount") or 0) / 1e8, (z.get("ltsz") or 0) / 1e8,
        esc(z.get("hybk")), esc((th0.get(z["c"], {}).get("reason_type") or "")))
    for z in lb_all)

tbl_blk = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td>{2}</td><td>{3:.1f}%</td><td>{4}</td><td>{5}</td>"
    "<td class='{6}' style='text-align:left'>{7}</td></tr>".format(
        esc(b["name"]), b["n"], b["cont"], b["pct"], b["hy"], b.get("high") or "—",
        "down" if b["fake"] else "up",
        "伪聚类，剔除" if b["fake"] else "同源，保留")
    for b in blk)

tbl_th = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td style='white-space:nowrap'>{4:.1f}亿</td><td style='white-space:nowrap'>{5:.1f}%</td>"
    "<td style='text-align:left'>{6}</td></tr>".format(
        esc(t["name"]), t["n"], t["lb"], t["hy"], t["amt"], t["shr"],
        "".join("<span class=tag>" + esc(x) + "</span>" for x in t["stocks"]))
    for t in TH0)

tbl_hy = "".join(
    "<tr><td>{0}</td><td>{1}</td><td class='hl'>{2}</td><td class='{3}'>{4}</td>"
    "<td style='text-align:left;color:#6b7280'>{5}</td></tr>".format(
        esc(h["name"]), h["y"], h["t"],
        "up" if h["t"] - h["y"] > 0 else ("down" if h["t"] - h["y"] < 0 else "mut"),
        dz(h["t"] - h["y"]),
        "流入" if h["t"] - h["y"] > 0 else ("流出" if h["t"] - h["y"] < 0 else "持平"))
    for h in hy_tbl)

tbl_ts = "".join(
    "<tr><td>{0}</td><td>{1}</td><td class='hl'>{2}</td><td class='{3}'>{4}</td></tr>".format(
        k, ts1.get(k, 0), ts0.get(k, 0),
        "up" if ts0.get(k, 0) - ts1.get(k, 0) > 0 else ("down" if ts0.get(k, 0) - ts1.get(k, 0) < 0 else "mut"),
        dz(ts0.get(k, 0) - ts1.get(k, 0)))
    for k in TS_ORDER)

tbl_cap = "".join(
    "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3:.1f}亿</td><td>{4}</td><td>{5:.1f}亿</td></tr>".format(
        a["nm"], a["n"], b_["n"], a["amt"], b_["n"], b_["amt"])
    for a, b_ in zip(CAP0, CAP1))

tbl_zb = "".join(
    "<tr><td>{0}</td><td class='hl'>{1}</td><td>{2}</td><td class='{7}'>{3:+.2f}%</td><td>{4:.2f}亿</td>"
    "<td>{5:.1f}亿</td><td>{6}</td></tr>".format(
        z["c"], esc(z["n"]), esc(z.get("hybk")), z.get("zdp") or 0,
        (z.get("amount") or 0) / 1e8, (z.get("ltsz") or 0) / 1e8, z.get("zbc"),
        "up" if (z.get("zdp") or 0) >= 0 else "down")
    for z in zb_top)

dtp_top = sorted(dtp, key=lambda x: -x["amount"])[:15]
tbl_dt = "".join(
    "<tr><td>{0}</td><td class='hl'>{1}</td><td>{2}</td><td class='down'>{3:+.2f}%</td><td>{4:.2f}亿</td>"
    "<td>{5:.1f}亿</td><td class='{6}'>{7}</td></tr>".format(
        z["c"], esc(z["n"]), esc(z["hybk"]), z["zdp"], z["amount"], z["ltsz"],
        "down" if z["c"] in c1set else "mut", "昨涨停" if z["c"] in c1set else "非昨涨停")
    for z in dtp_top)

dt_all = "".join(
    "<span class=tag>{0} {1}</span>".format(esc(z["n"]), esc(z["hybk"])) for z in dt_from_zt)

tbl_perf_top = "".join(
    "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td class='{3}'>{4:+.2f}%</td></tr>".format(
        "昨" + str(p["lbc"]) + "板" if (p["lbc"] or 0) >= 2 else "昨首板",
        esc(p["name"]), esc(p["hybk"]), "up" if p["pct"] >= 0 else "down", p["pct"])
    for p in sorted(perf, key=lambda x: -(x["pct"] if x["pct"] is not None else -999))[:6])

# ---- 名称博弈清算名单（昨日涨停、今日跌幅≥9.8%） ----
NM_CLEAR = [p for p in lim_dn]

# ================= 占位符 =================
V = {}
def P(k, v): V["__" + k + "__"] = str(v)

P("GEN_AT", B["generated_at"])
P("D0", md(D0)); P("D1", md(D1)); P("D2", md(D2))
P("ZT", ZT); P("ZT_Y", ZT1); P("ZT_D", dz(ZT - ZT1)); P("ZT_PCT", "%.1f" % ((ZT / ZT1 - 1) * 100))
P("TOUCH", TOUCH); P("TOUCH_Y", TOUCH1); P("TOUCH_D", dz(TOUCH - TOUCH1))
P("TOUCH_D_ABS", str(abs(TOUCH - TOUCH1)))
P("TOUCH_PCT_ABS", "%.1f" % abs((TOUCH / TOUCH1 - 1) * 100))
P("ZB", ZBC); P("ZB_Y", ZBC1); P("ZB_D", dz(ZBC - ZBC1))
P("SEAL", "%.1f" % SEAL); P("SEAL_Y", "%.1f" % SEAL1); P("SEAL_D", "%.1f" % (SEAL - SEAL1))
P("SEAL_UP", "%.1f" % abs(SEAL - SEAL1))
P("DT", DT); P("DT_Y", DT1); P("DT_D", dz(DT - DT1)); P("DT_TIMES", "%.1f" % (DT / DT1))
P("DT_T", DT_T); P("DT_T_Y", DT_T1); P("DT_T_TIMES", "%.1f" % (DT_T / DT_T1))
P("DT_R", "%.1f" % DT_R); P("DT_R_Y", "%.1f" % DT_R1)
P("DT_OPEN", ld0["open_num"])
P("AMT", "{:,.0f}".format(AMT)); P("AMT_Y", "{:,.0f}".format(AMT1))
P("AMT_D", "{:+,.0f}".format(AMT - AMT1)); P("AMT_PCT", "%+.1f" % ((AMT / AMT1 - 1) * 100))
P("AMT_PCT_ABS", "%.1f" % abs((AMT / AMT1 - 1) * 100))
P("N_UP", N_UP); P("N_AMT_UP", N_AMT_UP); P("N_BELOW", N_BELOW); P("N_IX", len(ix))
P("KC_PCT", "%+.2f" % KC["pct"]); P("KC_AMT", "{:,.0f}".format(KC["amt"]))
P("KC_AMT_PREV", "{:,.0f}".format(KC["amt_p"])); P("KC_AMT_PCT", "%+.1f" % KC["dpct"])
P("KC_POS", "%.2f" % KC["pos"]); P("KC_GAP", "%+.2f" % KC["gap"]); P("KC_LOW", "%+.2f" % KC["low"])
P("SZ50_PCT", "%+.2f" % SZ50["pct"]); P("SZ50_AMT_PCT", "%+.1f" % SZ50["dpct"])
P("CYB_PCT", "%+.2f" % CYB["pct"]); P("CYB_AMT_PCT", "%+.1f" % CYB["dpct"])
P("CYB_GAP", "%+.2f" % CYB["gap"]); P("CYB_LOW", "%+.2f" % CYB["low"])
P("SH_GAP", "%+.2f" % ixr["上证指数"]["gap"]); P("SH_LOW", "%.2f" % SH_LOW)
P("AMT_SUM", "%.1f" % amt_sum); P("AMT_SUM_Y", "%.1f" % amt_sum1)
P("AMT_SUM_PCT", "%+.1f" % ((amt_sum / amt_sum1 - 1) * 100))
P("AMT_SUM_PCT_ABS", "%.1f" % abs((amt_sum / amt_sum1 - 1) * 100))
P("SHARE", "%.2f" % SHARE); P("SHARE_Y", "%.2f" % SHARE1)
P("FUND_SUM", "%.2f" % fund_sum); P("FUND_SUM_Y", "%.2f" % fund_sum1)
P("FUND_SUM_PCT", "%+.1f" % ((fund_sum / fund_sum1 - 1) * 100))
P("FUND_SUM_PCT_ABS", "%.1f" % abs((fund_sum / fund_sum1 - 1) * 100))
P("FUND_MED", "%.2f" % fund_med); P("FUND_MED_Y", "%.2f" % fund_med1)
P("AMT_MED", "%.2f" % amt_med); P("AMT_MED_Y", "%.2f" % amt_med1)
P("AMT_MED_PCT", "%+.1f" % ((amt_med / amt_med1 - 1) * 100))
P("MAXB", MAXB); P("MAXB_Y", MAXB1)
P("LB", LB_N); P("LB_Y", LB_N1); P("LB_D", dz(LB_N - LB_N1))
P("SB", SB_N); P("SB_Y", SB_N1); P("SB_D_ABS", str(abs(SB_N - SB_N1)))
P("SB_PCT", "%.0f" % (SB_N / ZT * 100))
P("ADV_RATE", "%.1f" % (len(adv) / len(perf) * 100)); P("ADV_N", len(adv)); P("ADV_TOT", len(perf))
P("PERF_MEAN", "%+.2f" % statistics.mean(pcts)); P("PERF_MED", "%+.2f" % statistics.median(pcts))
P("NEG", neg); P("NEG_PCT", "%.1f" % (neg / len(perf) * 100)); P("NEG5", neg5)
P("F_N", len(first)); P("F_RATE", "%.1f" % f_rate); P("F_MED", "%+.2f" % f_med); P("F_MEAN", "%+.2f" % f_mean)
P("C_N", len(cont)); P("C_RATE", "%.1f" % c_rate); P("C_MED", "%+.2f" % c_med); P("C_MEAN", "%+.2f" % c_mean)
P("GAP", "%+.2f" % GAP); P("GAP_Y", "%+.2f" % GAP1); P("GAP_2", "%+.2f" % GAP2)
P("GAP_SWING", "%.2f" % abs(GAP - GAP1))
P("LIMDN_N", len(lim_dn))
P("LIMDN_LIST", "、".join(esc(p["name"]) for p in lim_dn))
P("ZB_BACK", len(zb_back)); P("ZB_N", len(zb)); P("ZB_AMT", "%.1f" % zb_amt)
P("ZB_RATIO", "%.2f" % zb_ratio); P("ZB_BIG", zb_big); P("ZB_HI", len(zb_hi))
P("DT_POOL_N", DT_POOL_N); P("DT_GAP", DT_GAP); P("DT_FROM_ZT", len(dt_from_zt))
P("DT_FROM_PCT", "%.1f" % (len(dt_from_zt) / len(perf) * 100))
P("DT_AMT", "%.1f" % dt_amt); P("DT_RATIO", "%.2f" % dt_ratio); P("DT_HY", len(dt_hy))
P("DT_HY_TOP", "、".join("%s %d 只" % (k, v) for k, v in dt_hy.most_common(4)))
P("DT_BIG_N", len(DT_BIG))
P("DT_PREV_N", DT_PREV_N); P("DT_INT", "、".join(INT_DT) if INT_DT else "0 只")
P("DT_INT_N", len(INT_DT))
P("DT_ALL_TAG", dt_all)
P("TH_LB", THM.get(JSKW, {}).get("lb", 0)); P("TH_LB_Y", THM1.get(JSKW, {}).get("lb", 0))
P("TH_N", THM.get(JSKW, {}).get("n", 0)); P("TH_N_Y", THM1.get(JSKW, {}).get("n", 0))
P("TH_AMT", "%.1f" % THM.get(JSKW, {}).get("amt", 0)); P("TH_AMT_Y", "%.1f" % THM1.get(JSKW, {}).get("amt", 0))
P("TH_AMT_PCT", "%+.1f" % ((THM.get(JSKW, {}).get("amt", 1) / max(THM1.get(JSKW, {}).get("amt", 1), 0.01) - 1) * 100))
P("RB_N", THM.get(RBK, {}).get("n", 0)); P("RB_N_Y", THM1.get(RBK, {}).get("n", 0))
P("RB_LB", THM.get(RBK, {}).get("lb", 0)); P("RB_LB_Y", THM1.get(RBK, {}).get("lb", 0))
P("RB_AMT", "%.1f" % THM.get(RBK, {}).get("amt", 0))
P("RB_AMT_Y", "%.1f" % THM1.get(RBK, {}).get("amt", 0))
P("RB_PCT", "%+.1f" % ((THM.get(RBK, {}).get("amt", 1) / max(THM1.get(RBK, {}).get("amt", 1), 0.01) - 1) * 100))
P("RB_SHR", "%.1f" % THM.get(RBK, {}).get("shr", 0))
P("AI_N", THM.get(AIK, {}).get("n", 0)); P("AI_N_Y", THM1.get(AIK, {}).get("n", 0))
P("AI_LB", THM.get(AIK, {}).get("lb", 0)); P("AI_LB_Y", THM1.get(AIK, {}).get("lb", 0))
P("AI_AMT", "%.1f" % THM.get(AIK, {}).get("amt", 0))
P("AI_AMT_Y", "%.1f" % THM1.get(AIK, {}).get("amt", 0))
P("AI_PCT", "%+.1f" % ((THM.get(AIK, {}).get("amt", 1) / max(THM1.get(AIK, {}).get("amt", 1), 0.01) - 1) * 100))
P("AI_SHR", "%.1f" % THM.get(AIK, {}).get("shr", 0))
P("AI_HY", THM.get(AIK, {}).get("hy", 0))
P("AUTO_N", THM.get(AUTO, {}).get("n", 0)); P("AUTO_N_Y", THM1.get(AUTO, {}).get("n", 0))
P("AUTO_LB", THM.get(AUTO, {}).get("lb", 0)); P("AUTO_AMT", "%.1f" % THM.get(AUTO, {}).get("amt", 0))
P("AUTO_HY", THM.get(AUTO, {}).get("hy", 0))
P("AUTO_ROT", "%.1f" % (AUTO_ROT * 100))
P("DF_N", THM.get("“东方系”名称博弈", {}).get("n", 0)); P("DF_LB", THM.get("“东方系”名称博弈", {}).get("lb", 0))
P("DF_AMT", "%.1f" % THM.get("“东方系”名称博弈", {}).get("amt", 0))
P("DF_AMT_Y", "%.1f" % THM1.get("“东方系”名称博弈", {}).get("amt", 0))
P("DF_N_Y", THM1.get("“东方系”名称博弈", {}).get("n", 0))
P("YANG_N", THM.get("“羊”字辈名称博弈", {}).get("n", 0)); P("YANG_LB", THM.get("“羊”字辈名称博弈", {}).get("lb", 0))
P("YANG_N_Y", THM1.get("“羊”字辈名称博弈", {}).get("n", 0))
P("YANG_AMT_Y", "%.1f" % THM1.get("“羊”字辈名称博弈", {}).get("amt", 0))
P("FAKE_N", FAKE_N); P("BLK_N", len(blk))
P("TOP_BLK", esc(TOP_BLK["name"])); P("TOP_BLK_N", TOP_BLK["n"]); P("TOP_BLK_PCT", "%.1f" % TOP_BLK["pct"])
P("TOP_BLK_HY", TOP_BLK["hy"])
P("BLK_MAX_PCT", "%.1f" % BLK_MAX_PCT); P("BLK_MAX_NAME", esc(BLK_MAX_NAME))
P("HY_N", HY_N); P("HY_N_Y", HY_N1)
P("CLR_N", len(CLR)); P("NEW_N", len(NEW))
P("CLR_LIST", "、".join(sorted(str(x) for x in CLR)))
P("NEW_LIST", "、".join(sorted(str(x) for x in NEW)))
P("TS_E0", TS_E0); P("TS_E1", TS_E1)
P("TS_E0_PCT", "%.0f" % (TS_E0 / ZT * 100)); P("TS_E1_PCT", "%.0f" % (TS_E1 / ZT1 * 100))
P("TS_ADV", "%.0f" % (TS_E0 / ZT * 100 - TS_E1 / ZT1 * 100))
P("TS_PM0", ts0.get("午后盘中", 0)); P("TS_PM1", ts1.get("午后盘中", 0))
P("ONEWORD", oneword); P("TWORD", tword); P("HUANSHOU", huanshou)
P("ONEWORD_PCT", "%.1f" % (oneword / ZT * 100)); P("HUANSHOU_PCT", "%.1f" % (huanshou / ZT * 100))
P("C20", c20)
P("CAP0_BIG", CAP0[4]["n"]); P("CAP1_BIG", CAP1[4]["n"])
P("CAP0_MID", CAP0[3]["n"]); P("CAP1_MID", CAP1[3]["n"])
P("BIG0_NM", esc(BIG0_NM) if BIG0_NM else "—")
P("GAP_UP", "%.2f" % GAP_UP); P("SH_HIGH", "%.2f" % SH_HIGH)
P("SH_CLOSE", "%.2f" % SH_CLOSE); P("SH_PREV", "%.2f" % SH_PREV)
P("GAP_TO", "%.2f" % abs(SH_HIGH - GAP_UP))
P("NEW_FACE", len(c0set - c1set)); P("NEW_FACE_PCT", "%.1f" % (len(c0set - c1set) / len(c0set) * 100))
P("FROM_Y", len(c0set & c1set))
P("TOP1", esc(lb_all[0]["n"])); P("TOP1_LB", lb_all[0]["lbc"])
P("TOP1_FBT", hhmm(lb_all[0]["fbt"])); P("TOP1_FUND", "%.2f" % ((lb_all[0].get("fund") or 0) / 1e8))
P("TOP1_ZBC", lb_all[0].get("zbc")); P("TOP1_AMT", "%.2f" % ((lb_all[0].get("amount") or 0) / 1e8))
P("TOP2", esc(lb_all[1]["n"])); P("TOP2_LB", lb_all[1]["lbc"])
P("TOP2_FBT", hhmm(lb_all[1]["fbt"])); P("TOP2_ZBC", lb_all[1].get("zbc"))
P("B3A", esc(B3[0]["n"])); P("B3A_FBT", hhmm(B3[0]["fbt"])); P("B3A_ZBC", B3[0].get("zbc"))
P("B3A_FUND", "%.2f" % ((B3[0].get("fund") or 0) / 1e8))
P("B3B", esc(B3[1]["n"])); P("B3B_FBT", hhmm(B3[1]["fbt"])); P("B3B_ZBC", B3[1].get("zbc"))
P("B3B_FUND", "%.2f" % ((B3[1].get("fund") or 0) / 1e8))
P("TOPF_N", esc(TOPF["n"])); P("TOPF_FUND", "%.2f" % ((TOPF.get("fund") or 0) / 1e8))
P("TOPF_SHR", "%.1f" % ((TOPF.get("fund") or 0) / 1e8 / fund_sum * 100))
P("YANG_MED", "%+.2f" % YANG_MED); P("YANG_DOWN", YANG_DOWN); P("YANG_NUM", YANG_NUM)
P("DT_FROM_Y_N", DT_FROM_Y_N); P("DT_FROM_Y_PCT", "%.1f" % (DT_FROM_Y_N / ZT1 * 100))
P("DT_RATIO_Y", "%.2f" % DT_RATIO_Y)
P("TBL_SENTI", tbl_senti); P("TBL_LAD", tbl_lad); P("TBL_LB", tbl_lb)
P("TBL_BLK", tbl_blk); P("TBL_TH", tbl_th); P("TBL_HY", tbl_hy); P("TBL_TS", tbl_ts)
P("TBL_CAP", tbl_cap); P("TBL_ZB", tbl_zb); P("TBL_DT", tbl_dt); P("TBL_PERF_TOP", tbl_perf_top)

ix_pct_sorted = sorted(ix, key=lambda x: x["pct"])
P("TBL_IDX", "".join(
    "<tr><td>{0}</td><td class='{1}'>{2:+.2f}%</td><td class='{3}'>{4:+.1f}%</td>"
    "<td class='{5}'>{6:+.2f}%</td><td class='{7}'>{8:+.2f}%</td><td>{9:,.0f}亿</td></tr>".format(
        esc(x["name"]), "up" if x["pct"] >= 0 else "down", x["pct"],
        "up" if x["dpct"] >= 0 else "down", x["dpct"],
        "up" if x["gap"] >= 0 else "down", x["gap"],
        "up" if x["pos"] >= -0.5 else "down", x["pos"], x["amt"])
    for x in ix))

P("JS_DAYS", json.dumps([md(D2), md(D1), md(D0)], ensure_ascii=False))
P("JS_ZT", json.dumps([t2["num"], ZT1, ZT]))
P("JS_ZB", json.dumps([s1["zb_prev"], ZBC1, ZBC]))
P("JS_DT", json.dumps([ld2["num"], DT1, DT]))
P("JS_SEAL", json.dumps([round(t2["rate"] * 100, 1), round(SEAL1, 1), round(SEAL, 1)]))
P("JS_IX_NAME", json.dumps([x["name"] for x in ix_pct_sorted], ensure_ascii=False))
P("JS_IX_PCT", json.dumps([round(x["pct"], 2) for x in ix_pct_sorted]))
P("JS_IX_AMT", json.dumps([round(x["dpct"], 1) for x in ix_pct_sorted]))
P("JS_LAD_NAME", json.dumps([str(i) + "板" for i in range(1, LADM + 1)], ensure_ascii=False))
P("JS_LAD0", json.dumps([lad0.get(i, 0) for i in range(1, LADM + 1)]))
P("JS_LAD1", json.dumps([lad1.get(i, 0) for i in range(1, LADM + 1)]))
P("JS_TS_NAME", json.dumps(TS_ORDER, ensure_ascii=False))
P("JS_TS_T", json.dumps([ts0.get(k, 0) for k in TS_ORDER]))
P("JS_TS_Y", json.dumps([ts1.get(k, 0) for k in TS_ORDER]))
th_sorted = sorted(TH0, key=lambda x: x["n"])
P("JS_TH_NAME", json.dumps([t["name"] for t in th_sorted], ensure_ascii=False))
P("JS_TH_N", json.dumps([t["n"] for t in th_sorted]))
hy_rev = hy_tbl[::-1]
P("JS_HY_NAME", json.dumps([h["name"] for h in hy_rev], ensure_ascii=False))
P("JS_HY_T", json.dumps([h["t"] for h in hy_rev]))
P("JS_HY_Y", json.dumps([h["y"] for h in hy_rev]))
pf_sorted = sorted(perf, key=lambda x: (x["pct"] if x["pct"] is not None else -99))
P("JS_PF_NAME", json.dumps([p["name"] for p in pf_sorted], ensure_ascii=False))
P("JS_PF_PCT", json.dumps([round(p["pct"], 2) for p in pf_sorted]))
P("JS_CAP_NAME", json.dumps([a["nm"].replace("&lt;", "<").replace("&gt;", ">") for a in CAP0], ensure_ascii=False))
P("JS_CAP0", json.dumps([a["n"] for a in CAP0]))
P("JS_CAP1", json.dumps([a["n"] for a in CAP1]))
P("JS_CHART_H", max(320, len(perf) * 22))
P("JS_DT_NAME", json.dumps([x["name"] for x in ix_pct_sorted], ensure_ascii=False))

HTML_T = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>涨停复盘 · 2026-11-13（对比 11-12）</title>
<script src="../assets/echarts.min.js"></script>
<script>if(typeof echarts==='undefined'){document.write('<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"><\/script>');}</script>
<style>
*{box-sizing:border-box}
body{margin:0;background:#f5f6f8;color:#1b1f24;font:14px/1.65 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:28px 20px 60px}
h1{font-size:26px;margin:0 0 6px;letter-spacing:-.3px}
.sub{color:#6b7280;font-size:13px;margin-bottom:22px}
.card{background:#fff;border:1px solid #e6e8eb;border-radius:12px;padding:20px 22px;margin-bottom:18px}
h2{font-size:17px;margin:0 0 14px;padding-left:10px;border-left:4px solid #2563eb}
h3{font-size:14px;margin:18px 0 8px;color:#374151}
.lead{background:#fff;border:1px solid #e6e8eb;border-left:5px solid #d93025;border-radius:10px;padding:18px 22px;margin-bottom:18px}
.lead p{margin:0 0 8px}.lead p:last-child{margin-bottom:0}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin:16px 0 4px}
.kpi{background:#fff;border:1px solid #e6e8eb;border-radius:10px;padding:14px 16px}
.kpi .lbl{font-size:12px;color:#6b7280;margin-bottom:6px}
.kpi .val{font-size:23px;font-weight:650;letter-spacing:-.5px}
.kpi .dt{font-size:12px;margin-top:4px}
.up{color:#d93025}.down{color:#12805c}.mut{color:#9ca3af}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:7px 9px;border-bottom:1px solid #eef0f2;text-align:right}
th:first-child,td:first-child{text-align:left}
th{background:#fafbfc;color:#4b5563;font-weight:600;font-size:12px}
tr:hover td{background:#fafbfc}
.chart{width:100%;height:330px}.chart-sm{width:100%;height:280px}
.two{display:grid;grid-template-columns:1fr 1fr;gap:18px}
@media(max-width:820px){.two{grid-template-columns:1fr}}
.tag{display:inline-block;background:#eef2ff;color:#3730a3;border-radius:5px;padding:1px 7px;font-size:11px;margin:1px 3px 1px 0}
.note{font-size:12px;color:#6b7280;line-height:1.75}
.warn{background:#fff8f1;border:1px solid #f5d9be;border-radius:10px;padding:14px 18px;font-size:13px;color:#7c4a12}
ul{margin:6px 0 0;padding-left:20px}li{margin:6px 0}
.hl{font-weight:600;color:#111827}
</style>
</head>
<body>
<div class="wrap">
<h1>涨停复盘 · 2026-11-13（周五）</h1>
<div class="sub">对比基准：2026-11-12（周四）｜口径：沪深两市（不含北交所）｜数据源：同花顺涨停/炸板/跌停池 + 东方财富涨停/炸板/跌停池 + 行情快照</div>

<div class="lead">
<p class="hl">一句话结论：11-12 是「放量派发」，今天把派发做成了「缩量清算」——涨停家数一动不动仍是 __ZT__ 只，跌停却从 __DT_Y__ 只爆到 __DT__ 只（__DT_TIMES__ 倍）；11 个指数成交额环比全负、__N_BELOW__/__N_IX__ 个收在开盘价下方。</p>
<p>三项指标里只有一项「看起来」改善：封板率 __SEAL_Y__%→__SEAL__%（+__SEAL_UP__pct）。但这是<span class="hl">分母收缩型假改善</span>——分子（涨停 __ZT__ 只）一只没变，改善全部来自触及涨停从 __TOUCH_Y__ 塌到 __TOUCH__（−__TOUCH_PCT_ABS__%）。
真实的承接力只有一个读数：炸板 __ZB__ 只、<span class="hl">回封 __ZB_BACK__ 只，连续第 4 个交易日零回封</span>。</p>
<p>今天的主变量是<b>破坏力</b>：跌停 __DT__ 只、触及跌停 __DT_T__（昨 __DT_T_Y__）、封死率 __DT_R__%、被买回 __DT_OPEN__ 只；
跌停股合计成交 __DT_AMT__ 亿 = 涨停股的 <span class="hl">__DT_RATIO__ 倍</span>。而两市成交 __AMT_Y__→__AMT__ 亿（__AMT_PCT__%），
__N_IX__ 个指数<span class="hl">无一个放量</span>——<b>不是放量砸盘，是买盘蒸发</b>。</p>
<p>钱的去向很清楚：昨日撑起盘面的「东方系 / 羊字辈」名称博弈集体清算（大东方 5 板直接跌停；羊字辈 __YANG_N_Y__ 只今日仅 __YANG_N__ 只涨停、__YANG_DOWN__ 只全部下跌、中位 __YANG_MED__%），
钱搬到 <b>AI 应用 / 影视院线（__AI_N_Y__→__AI_N__ 只、成交 __AI_AMT__ 亿 = 涨停股成交的 __AI_SHR__%）</b> 与 <b>汽车零部件（__AUTO_N_Y__→__AUTO_N__ 只、行业离散度 __AUTO_HY__）</b>。
但这条新方向<span class="hl">连板只有 __AI_LB__ 只（10%）</span>——是建仓第一天，不是接力成立。</p>
</div>

<div class="kpis">
  <div class="kpi"><div class="lbl">涨停家数</div><div class="val mut">__ZT__</div>
    <div class="dt mut">昨日 __ZT_Y__　<span class="mut">持平</span></div></div>
  <div class="kpi"><div class="lbl">封板率</div><div class="val up">__SEAL__%</div>
    <div class="dt mut">昨日 __SEAL_Y__% <span class="up">+__SEAL_UP__pct</span>（分母驱动）</div></div>
  <div class="kpi"><div class="lbl">炸板 / 回封</div><div class="val">__ZB__ / __ZB_BACK__</div>
    <div class="dt mut">昨日 __ZB_Y__ / 0　连续第 4 日零回封</div></div>
  <div class="kpi"><div class="lbl">跌停家数</div><div class="val down">__DT__</div>
    <div class="dt mut">昨日 __DT_Y__ <span class="down">__DT_D__</span>　触及 __DT_T__</div></div>
  <div class="kpi"><div class="lbl">两市成交额</div><div class="val down">__AMT__亿</div>
    <div class="dt mut">昨日 __AMT_Y__亿 <span class="down">__AMT_PCT__%</span></div></div>
  <div class="kpi"><div class="lbl">涨停股合计成交</div><div class="val down">__AMT_SUM__亿</div>
    <div class="dt mut">昨 __AMT_SUM_Y__亿 <span class="down">__AMT_SUM_PCT__%</span></div></div>
  <div class="kpi"><div class="lbl">晋级率</div><div class="val down">__ADV_RATE__%</div>
    <div class="dt mut">__ADV_N__/__ADV_TOT__ 只再涨停</div></div>
  <div class="kpi"><div class="lbl">最高连板</div><div class="val down">__MAXB__ 板</div>
    <div class="dt mut">昨日 __MAXB_Y__ 板（东方系 5 板全断）</div></div>
</div>

<div class="card">
<h2>一、情绪温度计：名义改善、承接为零、破坏力爆发</h2>
<table>
<tr><th>指标</th><th>__D2__（周三）</th><th>__D1__（周四）</th><th>__D0__（周五）</th><th>环比</th></tr>
__TBL_SENTI__
</table>
<div class="note" style="margin-top:10px">
<b>封板率 +__SEAL_UP__pct 必须与涨停家数并排读，否则会把本日读成修复日。</b>
分子 __ZT__ 只与昨日完全相同，分母（触及涨停）从 __TOUCH_Y__ 塌到 __TOUCH__，比值自然抬升——
这是 10-15 那次的同一陷阱（当时分子 36 不动、分母 60→43、封板率虚涨 23.7pct）。<br>
<b>可用的承接力读数只有回封数：0 只，连续第 4 个交易日</b>（按「收盘价 ≥ 涨停价」严格判定）。
炸板从 __ZB_Y__ 只降到 __ZB__ 只，不是因为封得住了，而是因为<span class="hl">敢去冲板的票少了 __TOUCH_D_ABS__ 只</span>。
</div>
<div class="note" style="margin-top:8px">
<b>破坏力是今天唯一真正变了的东西：</b>跌停 __DT_Y__→__DT__、触及跌停 __DT_T_Y__→__DT_T__（__DT_T_TIMES__ 倍），
但封死率从 __DT_R_Y__% 降到 __DT_R__%、<b>__DT_OPEN__ 只被买回</b>。
<span class="hl">「打到就买回」而不是「打到就封死」</span>，说明盘中有承接、但没有承接力——收盘仍站不住 __DT__ 只。
按本刊情绪形态分类，这是「破坏力主导的清算日」，与 10-22（放量跌停潮、封死率 92.5%）不同型：那天是砸，今天是漏。
</div>
<div id="c_senti" class="chart" style="margin-top:16px"></div>
</div>

<div class="card">
<h2>二、指数与量能：__N_IX__ 个指数全部缩量，只有 1 个收红</h2>
<div class="two">
<div>
<table>
<tr><th>指数</th><th>今日</th><th>成交额环比</th><th>开盘(vs昨收)</th><th>收盘距最高</th><th>成交额</th></tr>
__TBL_IDX__
</table>
<div class="note" style="margin-top:10px">
两市成交 __AMT__ 亿（昨 __AMT_Y__ 亿，__AMT_D__ 亿 / __AMT_PCT__%），
<span class="hl">__N_AMT_UP__/__N_IX__ 个指数成交额环比为正、只有 __N_UP__ 个收红（上证50），__N_BELOW__/__N_IX__ 个收于开盘价下方</span>。
</div>
</div>
<div><div id="c_idx" class="chart-sm" style="height:360px"></div></div>
</div>
<div class="note" style="margin-top:10px">
<b>与 11-12 的关键区别是「量」的方向反了：</b>
昨日是<span class="hl">放量 + 全线下跌</span>（主动性卖出增加、承接盘被动接货）；
今日是<span class="hl">缩量 + 全线下跌</span>（卖压没放大，买盘直接撤了）。
两者都指向下跌，但前者还有对手盘，后者连对手盘都没有——<b>缩量下跌比放量下跌更难止跌</b>，因为没有换手就没有筹码交换。
</div>
<div class="note" style="margin-top:8px">
<b>日内形态是统一的「高开低走」：</b>上证开 __SH_GAP__% 收 __SH_CLOSE__（最低 __SH_LOW__）；
创业板开 __CYB_GAP__%、最低 __CYB_LOW__%、收 __CYB_PCT__%；科创50 开 __KC_GAP__%、最低 __KC_LOW__%、收 __KC_PCT__%
（距当日最高 __KC_POS__%）。<span class="hl">11 个指数里 __N_BELOW__ 个收在开盘价下方</span>——开盘就是当日最好的价格。
</div>
<div class="note" style="margin-top:8px">
<b>科创50 昨日观察点给出明确答案：</b>昨日放量 __KC_AMT_PCT__%（__KC_AMT_PREV__ 亿）、冲高 +4.96% 收 +0.73%；
今日成交 __KC_AMT__ 亿（__KC_AMT_PCT__%）、收 __KC_PCT__%，<b>跌回 1,300 点下方（收 1,279.66）</b>。
按昨日预设判据「跌回 1,300 点下方且缩量 ⇒ 放量是换手式出货」，<span class="hl">本日予以确认</span>。
</div>
</div>

<div class="card">
<h2>三、连板梯队：最高板 5→__MAXB__，连板股只剩 __LB__ 只</h2>
<div class="two">
<div><div id="c_lad" class="chart-sm"></div></div>
<div>
<table>
<tr><th>梯队</th><th>__D1__</th><th>__D0__</th><th>变化</th></tr>
__TBL_LAD__
<tr><td>合计</td><td>__ZT_Y__</td><td class="hl">__ZT__</td><td class="mut">0</td></tr>
</table>
<div class="note" style="margin-top:10px">
首板 __SB__ 只（昨 __SB_Y__）、连板股 <span class="hl">__LB__ 只（昨 __LB_Y__，本轮最少）</span>、最高 __MAXB__ 板（昨 __MAXB_Y__ 板）。
首板占比 __SB_PCT__%。
<b>昨日 5 板的东方系两只全部断板</b>：大东方 −10.03% 跌停、日出东方 +5.54% 未封——
恰好命中昨日观察点①预设的<b>「断一只 ⇒ 最高板回落 4 板、塔尖归零」</b>。
</div>
</div>
</div>
<h3>今日连板股全名单（__LB__ 只，昨日 __LB_Y__ 只）</h3>
<table>
<tr><th>高度</th><th>代码</th><th>名称</th><th>首封</th><th>封单</th><th>成交额</th><th>流通市值</th><th>行业</th><th>涨停原因</th></tr>
__TBL_LB__
</table>
<div class="note" style="margin-top:10px">
<b>唯一的 4 板 __TOP1__（__TOP1_LB__ 板）质量很差：</b>首封 __TOP1_FBT__、成交仅 __TOP1_AMT__ 亿、<span class="hl">封单 __TOP1_FUND__ 亿</span>、全天开板 __TOP1_ZBC__ 次。
3 板的两只 __B3A__（__B3A_FBT__ 首封、封单 __B3A_FUND__ 亿、开板 __B3A_ZBC__ 次）与 __B3B__（__B3B_FBT__ 首封、封单 __B3B_FUND__ 亿、开板 __B3B_ZBC__ 次）——
一个属光伏设备+半导体装备、一个属四足机器人+手机游戏，
<span class="hl">连同 4 板的天普股份（中昊芯英+实控人变更），三只分属三条不相关叙事</span>，塔尖没有任何集群。
</div>
</div>

<div class="card">
<h2>四、主线归因：前七名最高连板占比 __BLK_MAX_PCT__%，低于 40% 主线线</h2>
<table>
<tr><th>概念板块（同花顺）</th><th>涨停</th><th>其中连板</th><th>连板占比</th><th>成分行业数</th><th>板块内最强标</th><th>判定</th></tr>
__TBL_BLK__
</table>
<div class="note" style="margin-top:10px">
判据只看一个比值：<b>连板占比 = 其中连板 ÷ 涨停家数</b>。前七名最高的是「__BLK_MAX_NAME__」__BLK_MAX_PCT__%，
<span class="hl">未过 40% 主线线</span>——结论是<b>当日没有一条既宽又高的主线</b>。<br>
但也要说清另一半：前七名不全是泛标签（新能源车 / 文化传媒 / 芯片 / 机器人都是产业标签），
所以这<b>不是 11-12 那种「乡村振兴 8 家散落 8 行业」的主线真空</b>，而是<b>三条产业线同时在建仓、谁都没有高度</b>。
榜单第一「__TOP_BLK__」__TOP_BLK_N__ 家 / 连板 __TOP_BLK_PCT__%，成分散落 __TOP_BLK_HY__ 个行业——
它是「新能源车 + 机器人零部件 + 汽零」的并集，<b>不能当成一条线来读</b>。<br>
被判定为伪聚类并剔除的 3 条：<b>华为概念（8 家散落 7 行业）、芯片概念（8 家 / 7 行业）、人工智能（7 家 / 6 行业）</b>——
三者都是跨行业泛命中，与此前反复出现的「乡村振兴 / 一带一路」同型；<b>它们不能当作主线，但也不能当作不存在</b>（见下方同源簇表）。
</div>
<div class="note" style="margin-top:8px">
<b>口径提示：</b>「其中连板」是同花顺 <code>continuous_plate_num</code>，统计「连续/断续上榜」；
与东财 <code>lbc</code>（当日连续连板数）是两套口径，同一簇可能报出两个数。判断「主线是否长高」用前者（跨日可比），判断「今日封板梯队」用后者。
</div>
<div id="c_th" class="chart" style="height:340px;margin-top:14px"></div>
<h3>按涨停原因聚类的同源簇（含连板数与成交占比）</h3>
<table>
<tr><th>簇</th><th>家数</th><th>其中连板</th><th>行业离散度</th><th>成交额</th><th>占涨停股成交</th><th>代表个股</th></tr>
__TBL_TH__
</table>
<div class="note" style="margin-top:10px">
<b>今天成交最集中的方向是「AI 应用 / 影视短剧」：__AI_N__ 只、成交 __AI_AMT__ 亿 = 涨停股成交的 __AI_SHR__%、散落 __AI_HY__ 个行业。</b>
按 10-23 的判据（叙事同源 + 成交占比 >40% 才算产业链集群），它<b>占比 __AI_SHR__% 略低于 40% 门槛</b>，且连板只有 __AI_LB__ 只（10%）——
定性为<span class="hl">「宽度爆发、零高度」的建仓第一天</span>，与 10-09 的 AI 应用（20 家 / 1 连板）完全同型：那天之后一日就分歧。
配套证据：影视院线行业 0→5 家（全部是新面孔）、游戏Ⅱ 0→2 家、IT服务Ⅱ 0→2 家。<br>
<b>另一条是「汽车零部件」：__AUTO_N__ 只、行业离散度 __AUTO_HY__（全落东财「汽车零部」）、连板 __AUTO_LB__ 只，但轮换率 __AUTO_ROT__%</b>——
昨日的汽车零部那只（天普股份）今日晋级，其余 __AUTO_N__ 只全部是新面孔，是「同行业换标的」而不是「同标的接力」。
（口径说明：东财行业「汽车零部」今日 6 只，其中飞乐音响叙事为「芯片测试+存储器」，属行业标签错配，已从本簇剔除。）
</div>
<div class="note" style="margin-top:8px">
<b>昨日的两条「主线」今日全部清算：</b>
「东方系」昨 __DF_N_Y__ 只 / 连板 __DF_LB__ / 成交 __DF_AMT_Y__ 亿 → <span class="hl">今日 __DF_N__ 只、连板 0</span>
（昨日 4 只今日表现：大东方 <b>−10.03% 跌停</b>、日出东方 +5.54%、东方环宇 +3.28%、东方海洋 −6.59%——一只跌停、三只未封）；
「羊」字辈昨 __YANG_N_Y__ 只 / 成交 __YANG_AMT_Y__ 亿 → <span class="hl">今日 __YANG_N__ 只</span>
（__YANG_DOWN__ 只全部下跌、中位 __YANG_MED__%：百洋股份 −10.02%、澳洋健康 −10.06%、大西洋 −9.73%、东方海洋 −6.59%、安阳钢铁 −6.50%）。
这就是本刊反复标注的「名称博弈=脆弱结构」的又一次验证：<b>它不产生接棒，只产生一日游</b>。
</div>
</div>

<div class="card">
<h2>五、行业迁移：影视院线 0→5，汽车零部 1→6（轮换率 83%）</h2>
<div id="c_hy" class="chart" style="height:420px"></div>
<table style="margin-top:14px">
<tr><th>行业</th><th>__D1__</th><th>__D0__</th><th>增减</th><th>读数</th></tr>
__TBL_HY__
</table>
<div class="note" style="margin-top:12px">
行业数 __HY_N_Y__ → __HY_N__，清零 __CLR_N__ 个、新增 __NEW_N__ 个，<b>流入流出几乎等量</b>——这是「行业被打散后的重新撒点」，不是方向切换。<br>
最大流入：<b>影视院线 0→5（100% 新面孔）</b>、汽车零部 1→6（留存 1 只、轮换率 __AUTO_ROT__%）、游戏Ⅱ 0→2、IT服务Ⅱ 0→2。<br>
最大流出：专用设备 3→0、一般零售 3→1、基础建设 2→0、服装家纺 2→0、燃气Ⅱ 2→0。
<span class="hl">流出的全是昨日名称博弈与区域基建的载体，流入的全是内容与零部件。</span>
</div>
</div>

<div class="card">
<h2>六、昨日涨停股今日表现：晋级率 __ADV_RATE__%，GAP 一天内由正转负</h2>
<div class="kpis" style="grid-template-columns:repeat(auto-fit,minmax(140px,1fr))">
  <div class="kpi"><div class="lbl">晋级率</div><div class="val down">__ADV_RATE__%</div><div class="dt mut">__ADV_N__/__ADV_TOT__</div></div>
  <div class="kpi"><div class="lbl">平均涨幅</div><div class="val down">__PERF_MEAN__%</div><div class="dt mut">中位 __PERF_MED__%</div></div>
  <div class="kpi"><div class="lbl">翻绿比例</div><div class="val down">__NEG_PCT__%</div><div class="dt mut">__NEG__ 只；跌超 5% 的 __NEG5__ 只</div></div>
  <div class="kpi"><div class="lbl">跌幅≥9.8%</div><div class="val down">__LIMDN_N__ 只</div><div class="dt mut">见下方名单</div></div>
  <div class="kpi"><div class="lbl">GAP（首板−连板中位）</div><div class="val down">__GAP__pct</div><div class="dt mut">昨 __GAP_Y__pct、前日 __GAP_2__pct</div></div>
</div>
<table style="margin-top:16px">
<tr><th>分组</th><th>样本</th><th>晋级率</th><th>均涨</th><th>中位</th></tr>
<tr><td>昨日首板</td><td>__F_N__</td><td>__F_RATE__%</td><td class="down">__F_MEAN__%</td><td class="down">__F_MED__%</td></tr>
<tr><td>昨日连板（≥2 板）</td><td>__C_N__</td><td class="up">__C_RATE__%</td><td class="down">__C_MEAN__%</td><td class="up">__C_MED__%</td></tr>
</table>
<div class="note" style="margin-top:12px">
<b>GAP 一日内摆动 __GAP_SWING__pct：__GAP_2__ → __GAP_Y__ → __GAP__pct。</b>
昨日刚翻正（+1.46，市场为「位置」付费），今日立刻回到负值——
<span class="hl">连板组中位 __C_MED__% vs 首板组 __F_MED__%，差 __GAP__pct</span>，说明钱又只肯给「已经有高度的票」付溢价。
但这不是「高度有效」的证据：连板组只有 __C_N__ 只样本、晋级率 __C_RATE__%，而<span class="hl">全场最高板从 5 塌到 4</span>——
「少数幸存者溢价为正」与「塔尖下移」同时成立，是退潮期的典型错配，不是修复。<br>
配套证据：__LIMDN_N__ 只昨日涨停股今日跌幅 ≥9.8%（__LIMDN_LIST__），其中<b>3 板、5 板各一只</b>——
高位票被直接清算，而不是温和退潮。
</div>
<h3>昨日涨停股中今日涨幅最大的 6 只（跌幅榜见上方 __LIMDN_N__ 只名单）</h3>
<table>
<tr><th>昨日高度</th><th>名称</th><th>行业</th><th>今日</th></tr>
__TBL_PERF_TOP__
</table>
<div id="c_perf" class="chart" style="height:__JS_CHART_H__px;margin-top:8px"></div>
</div>

<div class="card">
<h2>七、封板节奏与成交结构：早盘封板占比 __TS_E0_PCT__%，密度跌到 __SHARE__%</h2>
<div class="two">
<div><div id="c_ts" class="chart-sm"></div></div>
<div>
<table>
<tr><th>封板时段</th><th>__D1__</th><th>__D0__</th><th>变化</th></tr>
__TBL_TS__
</table>
<div class="note" style="margin-top:10px">
早盘封板 __TS_E0__/__ZT__ = __TS_E0_PCT__%（昨 __TS_E1__/__ZT_Y__ = __TS_E1_PCT__%），节奏<span class="hl">前移 __TS_ADV__pct</span>；
午后仅 __TS_PM0__ 只（昨 __TS_PM1__ 只）、尾盘 0 只。
<b>「早封早炸 + 午后无人接力」</b>，与 10-12 / 10-14 同型：存量资金在开盘抢跑，越往后越没有新增买盘。
</div>
</div>
</div>
<div class="kpis" style="grid-template-columns:repeat(auto-fit,minmax(160px,1fr));margin-top:16px">
  <div class="kpi"><div class="lbl">涨停股合计成交</div><div class="val down">__AMT_SUM__亿</div><div class="dt mut">占两市 __SHARE__%（昨 __SHARE_Y__%）</div></div>
  <div class="kpi"><div class="lbl">封单合计</div><div class="val up">__FUND_SUM__亿</div><div class="dt mut">昨 __FUND_SUM_Y__亿（__FUND_SUM_PCT__%）</div></div>
  <div class="kpi"><div class="lbl">封单中位</div><div class="val">__FUND_MED__亿</div><div class="dt mut">昨 __FUND_MED_Y__亿（持平）</div></div>
  <div class="kpi"><div class="lbl">单只中位成交</div><div class="val">__AMT_MED__亿</div><div class="dt mut">昨 __AMT_MED_Y__亿（持平）</div></div>
  <div class="kpi"><div class="lbl">一字 / T字 / 换手</div><div class="val">__ONEWORD__ / __TWORD__ / __HUANSHOU__</div><div class="dt mut">换手板占 __HUANSHOU_PCT__%</div></div>
</div>
<div class="note" style="margin-top:12px">
<b>持仓结构的关键矛盾：封单涨、成交跌。</b>
涨停股合计成交 __AMT_SUM_Y__→__AMT_SUM__ 亿（__AMT_SUM_PCT__%），而封单合计 __FUND_SUM_Y__→__FUND_SUM__ 亿（<span class="hl">__FUND_SUM_PCT__%</span>），
封单中位 __FUND_MED_Y__→__FUND_MED__ 亿、单只中位成交 __AMT_MED_Y__→__AMT_MED__ 亿，两个中位数<b>一模一样</b>。
含义：<span class="hl">封单的增加几乎全部来自一只——__TOPF_N__ 封单 __TOPF_FUND__ 亿，占全场 __TOPF_SHR__%</span>；
中位数不动说明「普遍的承接意愿没有任何变化」——这是<b>结构性失真，不能读成「资金更看好了」</b>。
</div>
<div class="note" style="margin-top:8px">
<b>吸金密度连续第三个交易日低于 2%（__SHARE__%，昨 __SHARE_Y__%）。</b>
按 11-12 报告预设判据「连续第二日低于 2% ⇒ 涨停板不再是资金主战场、本框架应降权」，
<b>今日触发该条</b>：两市 __AMT__ 亿里只有 __AMT_SUM__ 亿在涨停股上，占比 __SHARE__%。
本报告因此把「涨停结构」作为<b>情绪温度计</b>使用，而不是作为「资金主战场」的判断依据——
今日真正的资金主战场在跌停端（见下一节）。
</div>
</div>

<div class="card">
<h2>八、承接力与破坏力：炸板 __ZB_N__ 只零回封，跌停 __DT__ 只、成交反超涨停股</h2>
<h3>炸板池：__ZB_N__ 只，回封 __ZB_BACK__ 只，合计成交 __ZB_AMT__ 亿</h3>
<table>
<tr><th>代码</th><th>名称</th><th>行业</th><th>收盘</th><th>成交额</th><th>流通市值</th><th>开板次数</th></tr>
__TBL_ZB__
</table>
<div class="note" style="margin-top:10px">
① <span class="hl">回封 0 只，连续第 4 个交易日</span>（严格按「收盘价 ≥ 涨停价」判定，未用涨幅阈值——否则华是科技 +15.31%、旋极信息 +17.58% 这两只 20cm 标的会被误判为回封）；<br>
② 炸板池成交 __ZB_AMT__ 亿 / 涨停股成交 __AMT_SUM__ 亿 = <span class="hl">__ZB_RATIO__ 倍</span>（昨 2.05 倍）——冲板失败的钱仍然接近封住的钱；<br>
③ 池内流通 &gt;100 亿的 __ZB_BIG__ 只，最大是锋龙股份（117.7 亿、成交 31.55 亿、收 +2.65%、开板 3 次），
其中 __ZB_HI__ 只来自昨日涨停。
</div>
<h3>跌停池：同花顺汇总 __DT__ 只 / 东财池 __DT_POOL_N__ 只，跌停股成交 __DT_AMT__ 亿 = 涨停股的 __DT_RATIO__ 倍</h3>
<table>
<tr><th>代码</th><th>名称</th><th>行业</th><th>收盘</th><th>成交额</th><th>流通市值</th><th>来源</th></tr>
__TBL_DT__
</table>
<div class="note" style="margin-top:10px">
<b>这是今天最重要的一张表。</b>三条读数：<br>
① <b>破坏力量纲翻转</b>：跌停股合计成交 <span class="hl">__DT_AMT__ 亿 = 涨停股 __AMT_SUM__ 亿的 __DT_RATIO__ 倍</span>。
历史上这个比值（跌停成交/涨停成交）区间 0.03–3.3 倍，昨日约 __DT_RATIO_Y__ 倍（跌停 5 只、合计 65.9 亿）——<b>今天第一次回到 1 倍以上</b>。
含义：空头的换手规模与多头持平，<b>跌停股才是今天真正的战场</b>。<br>
② <b>行业高度分散（__DT_HY__ 个行业）→ 不是板块性杀跌</b>，而是「高位个股的分散清算」。
最集中的只是医疗服务 4 只（澳洋健康 / 百花医药 / 贝瑞基因 / 合富中国）、汽车零部 3 只、一般零售 3 只。<br>
③ <b>市值结构：流通 &gt;100 亿的 __DT_BIG_N__ 只</b>，最大是景旺电子（元件/PCB，流通 591 亿、成交 36.0 亿、−10.00%）——
这是 PCB 链的权重股，<span class="hl">说明这一轮的杀跌已经从「小票情绪」蔓延到「链条权重」</span>（10-28 以来 PCB/元件链的第四轮出清）。
</div>
<div class="note" style="margin-top:8px">
<b>昨涨停 → 今跌停：__DT_FROM_ZT__ 只（占昨日涨停股 __DT_FROM_PCT__%）。</b>
__DT_ALL_TAG__<br>
打板资金的隔夜亏损面从 11-12 的 __DT_FROM_Y_PCT__%（__DT_FROM_Y_N__/__ZT_Y__）跳到 <span class="hl">__DT_FROM_PCT__%（__DT_FROM_ZT__/__ZT_Y__）</span>——这是本轮回调以来最差的一档。
其中<b>大东方（昨 5 板）、惠发食品（昨 3 板）、中重科技（昨 2 板）</b>三只是梯队中高位，高位票被直接摁停。
</div>
<div class="note" style="margin-top:8px">
<b>「今日涨停 ∩ 昨日跌停」＝ __DT_INT__。</b>
昨日东财跌停池为 0 只（同花顺汇总 5 家、明细不可用），因此本日无法做代码交集验证；
这是本流程第 44 个交易日里<b>首次因「前一交易日跌停池为空」而无法交叉</b>，须在口径里披露，不能写成「交集为 0 = 跌停股未修复」。
</div>
<h3>市值结构：&gt;300 亿档 0→__CAP0_BIG__ 只，100–300 亿档 __CAP1_MID__→__CAP0_MID__ 只</h3>
<table>
<tr><th>流通市值档</th><th>__D0__ 只数</th><th>__D1__ 只数</th><th>__D0__ 成交</th><th>__D1__ 成交</th></tr>
__TBL_CAP__
</table>
<div class="note" style="margin-top:10px">
涨停池的市值结构<span class="hl">整体上移</span>：100–300 亿档 __CAP1_MID__→__CAP0_MID__ 只、&gt;300 亿档 0→__CAP0_BIG__ 只（__BIG0_NM__），
30–50 亿档 18→11 只。<b>这与「小微盘失血」的指数表现（中证1000 −2.76%、国证2000 −2.72%）方向一致</b>——
指数层面小微盘杀得最狠，但涨停池里反而是中大盘在涨，说明<span class="hl">今日的中大市值涨停是「防御性抱团」（影视/央企内容），不是风险偏好上升</span>。
</div>
</div>

<div class="card">
<h2>九、资金运动总结：钱从哪儿走、到哪儿去</h2>
<div class="lead" style="border-left-color:#2563eb;margin:0 0 14px">
<p class="hl">一句话：钱没有离场，但从「名称博弈」搬进了「内容 + 零部件」，同时把上一批高位票的钱锁死在跌停板上。</p>
</div>
<h3>钱的来路（三处）</h3>
<ul>
<li><b>① 「东方系 / 羊字辈」名称博弈 —— 最大流出源，直接清算。</b>
东方系 __DF_N_Y__ 只 / 成交 __DF_AMT_Y__ 亿 → <span class="hl">__DF_N__ 只 / __DF_AMT__ 亿（连板 3→__DF_LB__）</span>，大东方 5 板跌停；
羊字辈 __YANG_N_Y__ 只 / __YANG_AMT_Y__ 亿 → <span class="hl">__YANG_N__ 只</span>，__YANG_DOWN__ 只全部下跌、中位 __YANG_MED__%，3 只跌幅 ≥9.7%。
<b>这是「名称博弈必然一日游」的又一次验证</b>（同 09-22 华字辈、10-19 某字辈、10-26 东方系 4 只）。</li>
<li><b>② 机器人链 —— 家数与连板同时塌。</b>
__RB_N_Y__→__RB_N__ 只、成交 __RB_AMT_Y__→__RB_AMT__ 亿（__RB_PCT__%）、连板 __RB_LB_Y__→__RB_LB__ 只。
昨日 10 只中 9 只下跌、中位 −6.76%，仅北纬科技晋级 3 板——<b>链内只剩一个孤点</b>。</li>
<li><b>③ 算力硬件链 —— PCB 端继续杀，算力服务端反向起来。</b>
整体 __TH_N_Y__→__TH_N__ 只、成交 __TH_AMT_Y__→__TH_AMT__ 亿（__TH_AMT_PCT__%），
但结构分裂：<span class="hl">PCB/元件端景旺电子跌停（591 亿流通、36 亿成交）</span>，
而算力服务端华胜天成涨停（成交 25.10 亿、全场最大）、维通利、法狮龙、华孚时尚跟涨。
<b>同一个标签下，硬件杀、服务涨，不能合并成一个方向。</b></li>
</ul>
<h3>钱的去向（两处）</h3>
<ul>
<li><b>① AI 应用 / 影视院线 —— 宽度爆发、零高度。</b>__AI_N_Y__→__AI_N__ 只、成交 __AI_AMT_Y__→__AI_AMT__ 亿（__AI_PCT__%），
占涨停股成交 __AI_SHR__%；但<span class="hl">连板仅 __AI_LB__ 只（10%）</span>。
其中最重的三只是中国电影（318 亿流通、18.99 亿成交）、儒意电影（211 亿、15.59 亿）、文投控股（97 亿、10.45 亿）——
<b>都是中大市值内容股，是「防御型抱团」而不是「题材冲锋」</b>。</li>
<li><b>② 汽车零部件 —— 同行业换标的。</b>__AUTO_N_Y__→__AUTO_N__ 只、成交 __AUTO_AMT__ 亿，行业离散度 __AUTO_HY__（全落东财「汽车零部」），
但<span class="hl">轮换率 __AUTO_ROT__%</span>：除天普股份（昨 3 板→今 4 板）外全是新面孔。
这是「资金在同一个行业里换票」，不是「同一条链在接力」。</li>
</ul>
<h3>形式判据（三条，决定这次是清算还是转势）</h3>
<div class="note">
① 成交额环比 __N_AMT_UP__/__N_IX__（全负）、收盘 __N_UP__/__N_IX__ 红、__N_BELOW__/__N_IX__ 收于开盘价下方
→ <b>缩量 + 下跌 + 高开低走</b>，是「买盘蒸发」型，比 11-12 的「放量派发」更难止跌；<br>
② 涨停股成交 −__AMT_SUM_PCT_ABS__%、密度 __SHARE__%、回封 0（第 4 日）、封单中位持平
→ <b>打板端已连续三日不在主战场</b>，本框架今日起降权（见第七节）；<br>
③ 跌停 __DT__ 只、跌停成交/涨停成交 __DT_RATIO__ 倍、触及跌停 __DT_T__ 只但封死率仅 __DT_R__%
→ <b>恐慌是真的、承接是残缺的</b>：__DT_OPEN__ 只被买回说明有资金在接，但收盘 29 只仍封死说明接得不够。
</div>
<h3>上期（11-12）六条观察点复核</h3>
<table>
<tr><th>上期观察点（含阈值）</th><th>今日事实</th><th>结论</th></tr>
<tr><td>① 5 板东方系 2 只能否上 6 板（第一优先）</td><td>大东方 <b>−10.03% 跌停</b>、日出东方 +5.54% 未封</td><td class="down">全断，最高板 5→__MAXB__，命中「断一只 ⇒ 塔尖归零」</td></tr>
<tr><td>② 封板率能否修复（阈值 65% / 45%）</td><td>__SEAL__%（+__SEAL_UP__pct），但分子 __ZT__ 未变、分母 __TOUCH_Y__→__TOUCH__</td><td class="mut">名义未过 65%，且为分母收缩假改善</td></tr>
<tr><td>③ 回封是否破零（连续 3 日 0）</td><td>炸板 __ZB__ 只、回封 __ZB_BACK__ 只</td><td class="down">未破零，连续第 4 日</td></tr>
<tr><td>④ 科创50 能否守住（收红且额 ≥1,000 亿）</td><td>成交 __KC_AMT__ 亿（勉强达标）、收 <b>__KC_PCT__%</b>、跌回 1,279.66</td><td class="down">未守住，昨日放量确认为换手式出货</td></tr>
<tr><td>⑤ 跌停端是否扩散（≥8 只 ⇒ 拉高派发开始）</td><td><b>__DT__ 只</b>（触及 __DT_T__），5.8 倍</td><td class="down">大幅超出，拉高派发全面确认</td></tr>
<tr><td>⑥ 密度能否回到 3%（连续第二日 &lt;2% ⇒ 框架降权）</td><td>__SHARE__%，连续第 2 日 &lt;2%</td><td class="down">触发，本框架自今日起降权使用</td></tr>
</table>
<div class="note" style="margin-top:8px">
六条里<b>五条明确证伪、一条名义达标但被证伪其性质</b>。这不是「观察点设错了」，而是<b>11-12 的派发型判读是准确的、只是市场比预期更快</b>：
昨日报告写「增量进来即被套、明日一旦不接就是二次抛压」，今日正是二次抛压的完整兑现（缩量 + 跌停潮）。
</div>
</div>

<div class="card">
<h2>十、下一交易日 11/16（周一）观察点：七条，每条带阈值</h2>
<ul>
<li><b>① 跌停能否收敛到 10 只以内（第一优先）。</b>今日 __DT__ 只（触及 __DT_T__）是本轮最高。
<span class="hl">≤10 只</span> ⇒ 单日清算、市场还能自我修复；<b>≥20 只第二日</b> ⇒ 系统性清算进入第二阶段，看跌停股成交额是否继续放大（今日 __DT_AMT__ 亿）。</li>
<li><b>② 封板率要「真修复」必须先看分母。</b>今日 __SEAL__% 是分母塌出来的。
<span class="hl">触及涨停回到 65 只以上且封板率 ≥70%</span> ⇒ 真修复；<b>封板率 &gt;70% 但触及涨停仍 &lt;50 只</b> ⇒ 又是假改善，不改变结论。</li>
<li><b>③ 回封能否破零（连续 4 日 0）。</b><span class="hl">≥3 只回封</span> ⇒ 承接资金回来；仍 0–1 只 ⇒ 「打开即当日不封」已成制度性特征，本刊将不再逐日重复该指标。</li>
<li><b>④ AI 应用 / 影视能否长出高度（第一观察方向）。</b>今日 __AI_N__ 只 / 连板 __AI_LB__ 只 / 占成交 __AI_SHR__%。
<span class="hl">长出 ≥3 只 2 板</span> ⇒ 建仓期转接力、短线有新主线；<b>只剩 ≤5 只且全首板</b> ⇒ 与 10-09 同型，一日游确认。</li>
<li><b>⑤ 景旺电子（591 亿，PCB 权重）跌停后次日走势。</b>今日 −10.00%、成交 36.0 亿（跌停池最大）。
<span class="hl">次日止跌或反抽</span> ⇒ PCB 链第四轮出清结束、权重端承接有效；<b>再跌 &gt;5%</b> ⇒ 链条进入第五轮，需警惕扩散到元件/覆铜板其他权重。</li>
<li><b>⑥ 两市成交能否守住 1.6 万亿。</b>今日 __AMT__ 亿（__AMT_PCT__%）。
<span class="hl">回到 1.75 万亿以上</span> ⇒ 缩量只是一日；<b>跌破 1.5 万亿</b> ⇒ 流动性收缩式下跌延续，指数层面看上证 3,612（11-06 缺口下沿）。</li>
<li><b>⑦ 上证缺口与位置。</b>今日最高 __SH_HIGH__，未能重返 11-06 缺口上沿 __GAP_UP__（该缺口 __D1__ 已被补掉），收 __SH_CLOSE__ ——
<span class="hl">价格已重新落回缺口区间 3,612.15–3,689.91 之内</span>。
<span class="hl">站上 3,655（昨收）</span> ⇒ 缺口区内震荡、结构未破；<b>跌破 3,612.15（缺口下沿）</b> ⇒ 11-06 的跳空上升被完全回补，性质从「已补」翻转为「假突破」。</li>
</ul>
<div class="note" style="margin-top:8px">
判定顺序固定：先看①（破坏力是否收敛）→ 再看②③（承接是否真修复）→ 最后看④（是否有新方向能长出高度）→ ⑥（量能兜底）。
<span class="hl">只看涨停家数 37=37 会得出「情绪稳定」，只看封板率 +12.4pct 会得出「修复」，两者都错</span>——
今日是「名义平稳 × 内部清算」的分裂日，与 11-12「塔尖上移 × 塔基塌陷」是同一轮派发的两个阶段。
</div>
</div>

<div class="card">
<h2>十一、数据口径与风险提示</h2>
<div class="note">
<b>家数</b>：同花顺涨停池沪深口径 __ZT__ 家；东财涨停池 __ZT__ 只，<span class="hl">两源一致（差额 0）</span>。<br>
<b>跌停</b>：同花顺汇总 <b>__DT__ 家</b>（触及 __DT_T__、封死率 __DT_R__%、被买回 __DT_OPEN__ 只）；
东财 <code>getTopicDTPool</code>（<b>必须带 <code>sort=fund%3Aasc</code></b>）返回 tc=__DT_POOL_N__、池 __DT_POOL_N__ 只，
差额 <b>__DT_GAP__ 只无法归因</b>（池非空、全为沪深代码，既非北交所、也非池空）。按本刊口径<b>家数取同花顺汇总 __DT__ 家</b>，
明细表按东财池原样列出并标注；跌停股成交额按东财 __DT_POOL_N__ 只口径计算。<br>
<b>前一日跌停修正备忘</b>：11-12 当日抓取为 4 家，本次复核为 <b>5 家</b>（同花顺盘后小幅修正，同 10-23 情形）。
跨日引用旧数时若遇 ±1 家差异，先重算当日文件再判定是口径还是修正。<br>
<b>成交额 / 封单 / 流通市值 / 连板数（lbc）</b>：一律取东财 <code>em_ZT.pool</code> 字段；
同花顺 <code>currency_value</code> 不是成交额（实测差约 10 倍），仅用于 <code>reason_type</code>、<code>high_days</code>、<code>limit_up_type</code> 与汇总家数。<br>
<b>「触及涨停 / 封板率」</b>：取 <code>ths_zt.total.today</code> 的 <code>history_num</code> / <code>rate</code>；
三日序列表中 __D2__（11-11）的数据取自 <code>zt_review_20261111.json</code>，<b>不由 __D0__ 文件推算</b>（今日文件的 <code>dates</code> 只含 __D0__/__D1__）。<br>
<b>吸金密度</b>：涨停股合计成交 ÷ 两市成交 = __SHARE__%，<b>连续第 2 个交易日低于 3%–8% 自检区间</b>。
已用「单只中位成交 __AMT_MED_Y__→__AMT_MED__ 亿」「封单中位 __FUND_MED_Y__→__FUND_MED__ 亿」双向交叉验证 ⇒ <b>字段无误，是打板端被持续性抽水</b>。<br>
<b>炸板回封</b>：严格按「收盘价 ≥ 涨停价」判定，__ZB_N__ 只炸板中 __ZB_BACK__ 只满足，故回封记 0；
未使用涨幅阈值（华是科技 +15.31%、旋极信息 +17.58% 两只 20cm 标的会被误判）。<br>
<b>封板时间双源一致率</b>：__ZT__/__ZT__ = 100%（东财 <code>fbt</code> vs 同花顺时间戳，分钟级）。<br>
<b>跨日对比</b>：所有「昨日」数字从 <code>zt_stats_20261112.json</code> / <code>zt_review_20261112.json</code> 现算，
<b>不继承 11-12 报告内的手写结论</b>（该报告 GAP 等数字已回表复算一致）。
</div>
<div class="warn" style="margin-top:14px">
<b>风险提示：</b>本报告为盘后数据复盘与资金行为分析，所有结论基于公开行情数据的统计推断，<b>不构成任何投资建议</b>。
跌停潮次日的个股反弹概率在历史样本中显著低于随机（本刊 09-29 起连续 7 次交叉验证「跌停股不自动修复」，涨停∩昨跌停均为 0 只），
<b>不要把「跌停家数多」当作抄底理由</b>。涨停板交易具有高波动、高换手、隔夜风险大的特征，历史统计规律不保证未来重复。
</div>
</div>

<div class="note" style="text-align:center;color:#9ca3af;margin-top:24px">
生成时间：__GEN_AT__｜数据源：同花顺 / 东方财富 / 腾讯财经｜本报告由脚本自动生成
</div>
</div>

<script>
var C_RED='#d93025', C_GRN='#12805c', C_BLU='#2563eb';
var AX={axisLine:{lineStyle:{color:'#d1d5db'}},axisLabel:{color:'#6b7280'},splitLine:{lineStyle:{color:'#f1f3f5'}}};
function mk(id,opt){var e=echarts.init(document.getElementById(id));e.setOption(opt);window.addEventListener('resize',function(){e.resize()});}

mk('c_senti',{
  tooltip:{trigger:'axis'},legend:{top:3,left:'center',textStyle:{color:'#6b7280'}},
  grid:{left:56,right:66,top:52,bottom:32},
  xAxis:Object.assign({type:'category',data:__JS_DAYS__},AX),
  yAxis:[Object.assign({type:'value',name:'家数'},AX),
         Object.assign({type:'value',name:'封板率%',min:0,max:100},AX)],
  series:[
    {name:'涨停家数',type:'bar',data:__JS_ZT__,itemStyle:{color:C_RED},barWidth:26,
     label:{show:true,position:'top',color:C_RED,fontWeight:600}},
    {name:'炸板家数',type:'bar',data:__JS_ZB__,itemStyle:{color:'#f0a04b'},barWidth:26,
     label:{show:true,position:'top',color:'#b26a1e'}},
    {name:'跌停家数',type:'bar',data:__JS_DT__,itemStyle:{color:C_GRN},barWidth:26,
     label:{show:true,position:'top',color:C_GRN}},
    {name:'封板率',type:'line',yAxisIndex:1,smooth:true,symbolSize:8,data:__JS_SEAL__,
     itemStyle:{color:C_BLU},lineStyle:{width:3},label:{show:true,position:'bottom',color:C_BLU,formatter:'{c}%'}}
  ]
});

mk('c_idx',{
  tooltip:{trigger:'axis',valueFormatter:function(v){return v+'%'}},
  grid:{left:82,right:64,top:16,bottom:24},
  xAxis:Object.assign({type:'value',axisLabel:{formatter:'{value}%'}},AX),
  yAxis:Object.assign({type:'category',data:__JS_IX_NAME__,axisLabel:{color:'#6b7280',fontSize:11,interval:0}},AX),
  series:[{type:'bar',data:__JS_IX_PCT__,barWidth:13,
     itemStyle:{color:function(p){return p.value>=0?C_RED:C_GRN}},
     label:{show:true,position:'right',color:'#6b7280',fontSize:11,formatter:'{c}%'}}]
});

mk('c_lad',{
  tooltip:{trigger:'axis'},legend:{top:3,left:'center',textStyle:{color:'#6b7280'}},
  grid:{left:46,right:20,top:52,bottom:28},
  xAxis:Object.assign({type:'category',data:__JS_LAD_NAME__},AX),
  yAxis:Object.assign({type:'value'},AX),
  series:[
    {name:'__D1__',type:'bar',data:__JS_LAD1__,itemStyle:{color:'#cbd5e1'},barWidth:20},
    {name:'__D0__',type:'bar',data:__JS_LAD0__,itemStyle:{color:C_RED},barWidth:20,
     label:{show:true,position:'top',color:'#9ca3af',fontSize:11}}
  ]
});

mk('c_th',{
  tooltip:{trigger:'axis'},
  grid:{left:212,right:70,top:16,bottom:24},
  xAxis:Object.assign({type:'value'},AX),
  yAxis:Object.assign({type:'category',data:__JS_TH_NAME__,axisLabel:{color:'#6b7280',fontSize:11,interval:0}},AX),
  series:[{type:'bar',data:__JS_TH_N__,itemStyle:{color:C_BLU},barWidth:14,
    label:{show:true,position:'right',color:'#374151',fontWeight:600,formatter:'{c} 只'}}]
});

mk('c_hy',{
  tooltip:{trigger:'axis'},legend:{top:3,left:'center',textStyle:{color:'#6b7280'}},
  grid:{left:100,right:56,top:52,bottom:24},
  xAxis:Object.assign({type:'value'},AX),
  yAxis:Object.assign({type:'category',data:__JS_HY_NAME__,axisLabel:{color:'#6b7280',fontSize:11,interval:0}},AX),
  series:[
    {name:'__D1__',type:'bar',data:__JS_HY_Y__,itemStyle:{color:'#cbd5e1'},barWidth:10},
    {name:'__D0__',type:'bar',data:__JS_HY_T__,itemStyle:{color:C_RED},barWidth:10}
  ]
});

mk('c_perf',{
  tooltip:{trigger:'axis',valueFormatter:function(v){return v+'%'}},
  grid:{left:104,right:56,top:16,bottom:28},
  xAxis:Object.assign({type:'value',axisLabel:{formatter:'{value}%'}},AX),
  yAxis:Object.assign({type:'category',data:__JS_PF_NAME__,axisLabel:{color:'#6b7280',fontSize:10,interval:0}},AX),
  series:[{type:'bar',data:__JS_PF_PCT__,barWidth:9,
    itemStyle:{color:function(p){return p.value>=0?C_RED:C_GRN}},
    label:{show:true,position:'right',fontSize:10,color:'#9ca3af',
      formatter:function(p){return p.value.toFixed(1)}}}]
});

mk('c_ts',{
  tooltip:{trigger:'axis'},legend:{top:3,left:'center',textStyle:{color:'#6b7280'}},
  grid:{left:50,right:20,top:52,bottom:28},
  xAxis:Object.assign({type:'category',data:__JS_TS_NAME__,axisLabel:{color:'#6b7280',fontSize:11,interval:0}},AX),
  yAxis:Object.assign({type:'value'},AX),
  series:[
    {name:'__D1__',type:'bar',data:__JS_TS_Y__,itemStyle:{color:'#cbd5e1'},barWidth:24},
    {name:'__D0__',type:'bar',data:__JS_TS_T__,itemStyle:{color:C_RED},barWidth:24}
  ]
});
</script>
</body>
</html>
"""

HTML = HTML_T
for k, v in V.items():
    HTML = HTML.replace(k, v)

fp = os.path.join(REP, "涨停复盘对比-%s.html" % D0)
with open(fp, "w", encoding="utf-8") as f:
    f.write(HTML)
import re
left = re.findall(r"__[A-Z_0-9]+__", HTML)
print("saved ->", fp, len(HTML) // 1024, "KB")
print("placeholder residue:", sorted(set(left)))
