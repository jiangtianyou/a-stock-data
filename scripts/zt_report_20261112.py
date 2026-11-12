# -*- coding: utf-8 -*-
"""20261112 涨停复盘报告（对比 20261111）"""
import json, os, sys, collections, html, statistics

ROOT = os.environ.get("ZT_ROOT") or os.getcwd()
OUT = os.path.join(ROOT, "out"); REP = os.path.join(ROOT, "reports")
os.makedirs(REP, exist_ok=True)

D0, D1, D2 = "20261112", "20261111", "20261110"
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
def d0_(v): return "0" if v == 0 else ("%+d" % v)
def d1_(v): return "0" if abs(v) < 0.005 else ("%+.1f" % v)

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
    ix.append({"name": nm, "pct": a["pct"], "amt": amt, "amt_p": amt_p,
               "dpct": (amt / amt_p - 1) * 100 if amt_p else 0.0,
               "gap": (a["open"] / b_["price"] - 1) * 100 if b_ and b_.get("price") else 0.0,
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
zb_top = sorted(zb, key=lambda x: -(x.get("amount") or 0))[:10]

# ---- 跌停池 ----
dtp = [{"c": "603303", "n": "得邦照明", "hybk": "照明设备", "zdp": -10.00, "amount": 2.50, "ltsz": 120.1},
       {"c": "002695", "n": "煌上煌", "hybk": "休闲食品", "zdp": -9.96, "amount": 3.27, "ltsz": 50.4},
       {"c": "002779", "n": "中坚科技", "hybk": "专用设备", "zdp": -10.00, "amount": 10.57, "ltsz": 150.0},
       {"c": "601595", "n": "上海电影", "hybk": "影视院线", "zdp": -9.99, "amount": 19.52, "ltsz": 188.9},
       {"c": "605488", "n": "福莱新材", "hybk": "塑料", "zdp": -10.00, "amount": 30.01, "ltsz": 169.3}]
dt_amt = sum(z["amount"] for z in dtp)
dt_ratio = dt_amt / amt_sum
dt_from_zt = [z for z in dtp if z["c"] in c1set]

# ---- 主线聚类 ----
KW = [
    ("机器人 / 具身智能", ["机器人", "具身智能", "减速器", "丝杠", "关节", "电子皮肤", "灵巧手", "谐波", "滚珠"]),
    ("“东方系”名称博弈", ["“东方系”", "“东方”"]),
    ("“羊”字辈名称博弈", ["“羊”字辈"]),
    ("海洋经济 / 养殖", ["海洋", "水产", "海参", "渔业", "鱼粉"]),
    ("AI 应用 / 传媒", ["AI漫剧", "短剧", "AI影视", "AI游戏", "游戏", "IP", "影视", "剧集", "传媒", "AI应用"]),
    ("光伏 / 玻璃基板", ["光伏", "玻璃基板", "光伏玻璃"]),
    ("燃气 / 天然气", ["燃气", "天然气", "LNG", "供热"]),
    ("算力硬件（光模块∪PCB∪算力）", ["光模块", "CPO", "光通信", "光纤", "光芯片", "空芯光纤", "MPO", "铜缆", "6G",
                              "PCB", "覆铜板", "玻璃基", "算力", "数据中心", "液冷", "服务器", "交换机", "HBM"]),
    ("冰雪 / 旅游", ["冰雪", "旅游"]),
    ("半导体 / 存储", ["存储芯片", "半导体", "芯片测试", "半导体设备", "光刻胶"]),
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
                    "stocks": [z["n"] for z in sorted(hit, key=lambda x: -(x.get("lbc") or 0))][:10]})
    return out
TH0 = theme_rows(p0, th0); TH1 = theme_rows(p1, th1)
THM = {t["name"]: t for t in TH0}
THM1 = {t["name"]: t for t in TH1}
JSKW = "算力硬件（光模块∪PCB∪算力）"

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

# ---- 行业迁移 ----
hy0d, hy1d = S["hy0"], S["hy1"]
hy_keys = sorted(set(list(hy0d) + list(hy1d)),
                 key=lambda k: (-(hy0d.get(k, 0) * 2 + hy1d.get(k, 0)), -hy0d.get(k, 0), -hy1d.get(k, 0), k))
hy_tbl = [{"name": k, "t": hy0d.get(k, 0), "y": hy1d.get(k, 0)} for k in hy_keys[:16]]
h0s, h1s = collections.defaultdict(set), collections.defaultdict(set)
for z in p0: h0s[z.get("hybk")].add(z["c"])
for z in p1: h1s[z.get("hybk")].add(z["c"])
HY_N = len([k for k in h0s if k]); HY_N1 = len([k for k in h1s if k])
CLR = [k for k in h1s if h1s[k] and not h0s.get(k)]
NEW = [k for k in h0s if h0s[k] and not h1s.get(k)]

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
BIG1 = [z for z in p1 if (z.get("ltsz") or 0) > 3e10]
BIG1_PCT = [Y[z["c"]]["pct"] for z in BIG1 if z["c"] in Y and Y[z["c"]].get("pct") is not None]
BIG1_MED = statistics.median(BIG1_PCT) if BIG1_PCT else 0

# ---- 缺口 ----
GAP_UP, GAP_DN = 3689.91, 3612.15
SH_HIGH = B["indexes"]["sh000001"]["high"]; SH_CLOSE = B["indexes"]["sh000001"]["price"]
GAP_FILL = (SH_HIGH - GAP_UP)

# ================= 表格 =================
def _srow(lab, a, b, c, unit="", rev=False):
    """rev=True 表示反向指标（炸板/跌停/触及跌停/跌停封死率）：上升为负面 → 标绿。
    配色按语义、不按正负号——这是本刊铁律，曾因一刀切把「炸板 +12」标成红色。"""
    diff = c - b
    good = (diff < 0) if rev else (diff > 0)
    cls = "up" if good else ("down" if diff != 0 else "mut")
    if diff == 0: cls = "mut"
    txt = ("0" if abs(diff) < 0.005 else ("%+.1f" % diff)) if unit else ("%+d" % diff)
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
        d0_(lad0.get(i, 0) - lad1.get(i, 0)))
    for i in range(LADM, 0, -1))

lb_all = sorted([z for z in p0 if (z.get("lbc") or 0) >= 2], key=lambda x: (-(x.get("lbc") or 0), -(x.get("amount") or 0)))
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
        d0_(h["t"] - h["y"]),
        "流入" if h["t"] - h["y"] > 0 else ("流出" if h["t"] - h["y"] < 0 else "持平"))
    for h in hy_tbl)

tbl_ts = "".join(
    "<tr><td>{0}</td><td>{1}</td><td class='hl'>{2}</td><td class='{3}'>{4}</td></tr>".format(
        k, ts1.get(k, 0), ts0.get(k, 0),
        "up" if ts0.get(k, 0) - ts1.get(k, 0) > 0 else ("down" if ts0.get(k, 0) - ts1.get(k, 0) < 0 else "mut"),
        d0_(ts0.get(k, 0) - ts1.get(k, 0)))
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

tbl_dt = "".join(
    "<tr><td>{0}</td><td class='hl'>{1}</td><td>{2}</td><td class='down'>{3:+.2f}%</td><td>{4:.2f}亿</td>"
    "<td>{5:.1f}亿</td><td class='{6}'>{7}</td></tr>".format(
        z["c"], esc(z["n"]), esc(z["hybk"]), z["zdp"], z["amount"], z["ltsz"],
        "down" if z["c"] in c1set else "mut", "昨涨停" if z["c"] in c1set else "非昨涨停")
    for z in dtp)

tbl_perf = "".join(
    "<tr><td>{0}{1}</td><td>{2}</td><td>{3}</td><td class='{4}'>{5:+.2f}%</td><td>{6}{7}</td></tr>".format(
        "昨" + str(p["lbc"]) + "板" if (p["lbc"] or 0) >= 2 else "昨首板",
        "", esc(p["name"]), esc(p["hybk"]), "up" if p["pct"] >= 0 else "down", p["pct"],
        "", "")
    for p in sorted(perf, key=lambda x: -(x["pct"] if x["pct"] is not None else -999))[:8])

def ix_order_by_pct():
    return sorted(ix, key=lambda x: x["pct"])

# ================= 占位符 =================
V = {}
def P(k, v): V["__" + k + "__"] = str(v)

P("GEN_AT", B["generated_at"])
P("D0", md(D0)); P("D1", md(D1)); P("D2", md(D2))
P("ZT", ZT); P("ZT_Y", ZT1); P("ZT_D", d0_(ZT - ZT1)); P("ZT_PCT", "%.1f" % ((ZT / ZT1 - 1) * 100))
P("TOUCH", TOUCH); P("TOUCH_Y", TOUCH1); P("TOUCH_D", d0_(TOUCH - TOUCH1))
P("ZB", ZBC); P("ZB_Y", ZBC1); P("ZB_D", d0_(ZBC - ZBC1))
P("SEAL", "%.1f" % SEAL); P("SEAL_Y", "%.1f" % SEAL1); P("SEAL_D", "%.1f" % (SEAL - SEAL1))
P("DT", DT); P("DT_Y", DT1); P("DT_D", d0_(DT - DT1))
P("DT_T", DT_T); P("DT_T_Y", DT_T1); P("DT_R", "%.1f" % DT_R)
P("DT_OPEN", ld0["open_num"])
P("AMT", "{:,.0f}".format(AMT)); P("AMT_Y", "{:,.0f}".format(AMT1))
P("AMT_D", "{:+,.0f}".format(AMT - AMT1)); P("AMT_PCT", "%+.1f" % ((AMT / AMT1 - 1) * 100))
P("N_UP", N_UP); P("N_AMT_UP", N_AMT_UP); P("N_BELOW", N_BELOW); P("N_IX", len(ix))
P("KC_PCT", "%+.2f" % KC["pct"]); P("KC_AMT", "{:,.0f}".format(KC["amt"]))
P("KC_AMT_PREV", "{:,.0f}".format(KC["amt_p"])); P("KC_AMT_PCT", "%+.1f" % KC["dpct"])
P("KC_POS", "%.2f" % KC["pos"])
P("SZ50_PCT", "%+.2f" % SZ50["pct"]); P("SZ50_AMT_PCT", "%+.1f" % SZ50["dpct"])
P("CYB_PCT", "%+.2f" % CYB["pct"]); P("CYB_AMT_PCT", "%+.1f" % CYB["dpct"])
P("AMT_SUM", "%.1f" % amt_sum); P("AMT_SUM_Y", "%.1f" % amt_sum1)
P("AMT_SUM_PCT", "%+.1f" % ((amt_sum / amt_sum1 - 1) * 100))
P("SHARE", "%.2f" % SHARE); P("SHARE_Y", "%.2f" % SHARE1)
P("FUND_SUM", "%.2f" % fund_sum); P("FUND_SUM_Y", "%.2f" % fund_sum1)
P("FUND_SUM_PCT", "%+.1f" % ((fund_sum / fund_sum1 - 1) * 100))
P("FUND_MED", "%.2f" % fund_med); P("FUND_MED_Y", "%.2f" % fund_med1)
P("FUND_AVG", "%.2f" % (fund_sum / ZT))
P("AMT_MED", "%.2f" % amt_med); P("AMT_MED_Y", "%.2f" % amt_med1)
P("MAXB", MAXB); P("MAXB_Y", MAXB1)
P("LB", LB_N); P("LB_Y", LB_N1); P("SB", SB_N); P("SB_Y", SB_N1)
P("SB_PCT", "%.0f" % (SB_N / ZT * 100))
P("ADV_RATE", "%.1f" % (len(adv) / len(perf) * 100)); P("ADV_N", len(adv)); P("ADV_TOT", len(perf))
P("PERF_MEAN", "%+.2f" % statistics.mean(pcts)); P("PERF_MED", "%+.2f" % statistics.median(pcts))
P("NEG", neg); P("NEG_PCT", "%.1f" % (neg / len(perf) * 100)); P("NEG5", neg5)
P("F_N", len(first)); P("F_RATE", "%.1f" % f_rate); P("F_MED", "%+.2f" % f_med); P("F_MEAN", "%+.2f" % f_mean)
P("C_N", len(cont)); P("C_RATE", "%.1f" % c_rate); P("C_MED", "%+.2f" % c_med); P("C_MEAN", "%+.2f" % c_mean)
P("GAP", "%+.2f" % GAP); P("GAP_Y", "%+.2f" % GAP1); P("GAP_2", "%+.2f" % GAP2)
P("LIMDN_N", len(lim_dn))
P("LIMDN_LIST", "、".join(esc(p["name"]) for p in lim_dn))
P("ZB_BACK", len(zb_back)); P("ZB_N", len(zb)); P("ZB_AMT", "%.1f" % zb_amt)
P("ZB_RATIO", "%.2f" % zb_ratio); P("ZB_BIG", zb_big); P("ZB_HI", len(zb_hi))
P("DT_AMT", "%.1f" % dt_amt); P("DT_RATIO", "%.2f" % dt_ratio); P("DT_FROM_ZT", len(dt_from_zt))
P("DT_HY", len({z["hybk"] for z in dtp}))
P("TH_LB", THM.get(JSKW, {}).get("lb", 0)); P("TH_LB_Y", THM1.get(JSKW, {}).get("lb", 0))
P("TH_N", THM.get(JSKW, {}).get("n", 0)); P("TH_N_Y", THM1.get(JSKW, {}).get("n", 0))
P("TH_AMT", "%.1f" % THM.get(JSKW, {}).get("amt", 0)); P("TH_AMT_Y", "%.1f" % THM1.get(JSKW, {}).get("amt", 0))
P("TH_AMT_PCT", "%+.1f" % ((THM.get(JSKW, {}).get("amt", 1) / max(THM1.get(JSKW, {}).get("amt", 1), 0.01) - 1) * 100))
P("RB_N", THM.get("机器人 / 具身智能", {}).get("n", 0)); P("RB_N_Y", THM1.get("机器人 / 具身智能", {}).get("n", 0))
P("RB_LB", THM.get("机器人 / 具身智能", {}).get("lb", 0)); P("RB_LB_Y", THM1.get("机器人 / 具身智能", {}).get("lb", 0))
P("RB_AMT", "%.1f" % THM.get("机器人 / 具身智能", {}).get("amt", 0))
P("RB_AMT_Y", "%.1f" % THM1.get("机器人 / 具身智能", {}).get("amt", 0))
P("RB_PCT", "%+.1f" % ((THM.get("机器人 / 具身智能", {}).get("amt", 1) / max(THM1.get("机器人 / 具身智能", {}).get("amt", 1), 0.01) - 1) * 100))
P("DF_N", THM.get("“东方系”名称博弈", {}).get("n", 0)); P("DF_LB", THM.get("“东方系”名称博弈", {}).get("lb", 0))
P("DF_AMT", "%.1f" % THM.get("“东方系”名称博弈", {}).get("amt", 0))
P("DF_SHR", "%.1f" % THM.get("“东方系”名称博弈", {}).get("shr", 0))
P("DF_AMT_Y", "%.1f" % THM1.get("“东方系”名称博弈", {}).get("amt", 0))
P("YANG_N", THM.get("“羊”字辈名称博弈", {}).get("n", 0)); P("YANG_LB", THM.get("“羊”字辈名称博弈", {}).get("lb", 0))
P("YANG_AMT", "%.1f" % THM.get("“羊”字辈名称博弈", {}).get("amt", 0))
P("YANG_SHR", "%.1f" % THM.get("“羊”字辈名称博弈", {}).get("shr", 0))
P("FAKE_N", FAKE_N); P("BLK_N", len(blk))
P("TOP_BLK", esc(TOP_BLK["name"])); P("TOP_BLK_N", TOP_BLK["n"]); P("TOP_BLK_PCT", "%.1f" % TOP_BLK["pct"])
P("TOP_BLK_HY", TOP_BLK["hy"])
P("HY_N", HY_N); P("HY_N_Y", HY_N1)
P("CLR_N", len(CLR)); P("NEW_N", len(NEW))
P("CLR_LIST", "、".join(sorted(str(x) for x in CLR)))
P("NEW_LIST", "、".join(sorted(str(x) for x in NEW)))
P("TS_E0", TS_E0); P("TS_E1", TS_E1)
P("TS_E0_PCT", "%.0f" % (TS_E0 / ZT * 100)); P("TS_E1_PCT", "%.0f" % (TS_E1 / ZT1 * 100))
P("TS_PM0", ts0.get("午后盘中", 0)); P("TS_PM1", ts1.get("午后盘中", 0))
P("ONEWORD", oneword); P("ONEWORD_PCT", "%.1f" % (oneword / ZT * 100)); P("HUANSHOU", huanshou)
P("C20", c20)
P("BIG1_N", len(BIG1)); P("BIG1_MED", "%+.2f" % BIG1_MED)
P("BIG1_UP", sum(1 for p in BIG1_PCT if p > 0)); P("BIG1_N2", len(BIG1_PCT))
P("CAP0_BIG", CAP0[4]["n"]); P("CAP1_BIG", CAP1[4]["n"])
P("GAP_UP", "%.2f" % GAP_UP); P("GAP_FILL", "%.2f" % GAP_FILL); P("SH_HIGH", "%.2f" % SH_HIGH)
P("SH_CLOSE", "%.2f" % SH_CLOSE); P("GAP_BACK", "%.2f" % (GAP_UP - SH_CLOSE))
P("NEW_FACE", len(c0set - c1set)); P("NEW_FACE_PCT", "%.1f" % (len(c0set - c1set) / len(c0set) * 100))
P("FROM_Y", len(c0set & c1set))
P("TOP1", esc(lb_all[0]["n"])); P("TOP1_LB", lb_all[0]["lbc"])
P("TOP1_FBT", hhmm(lb_all[0]["fbt"])); P("TOP1_FUND", "%.2f" % ((lb_all[0].get("fund") or 0) / 1e8))
P("TOP2", esc(lb_all[1]["n"])); P("TOP2_LB", lb_all[1]["lbc"])
P("TOP2_FBT", hhmm(lb_all[1]["fbt"])); P("TOP2_ZBC", lb_all[1].get("zbc"))
P("TBL_SENTI", tbl_senti); P("TBL_LAD", tbl_lad); P("TBL_LB", tbl_lb)
P("TBL_BLK", tbl_blk); P("TBL_TH", tbl_th); P("TBL_HY", tbl_hy); P("TBL_TS", tbl_ts)
P("TBL_CAP", tbl_cap); P("TBL_ZB", tbl_zb); P("TBL_DT", tbl_dt)

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
P("JS_CHART_H", max(300, len(perf) * 21))

HTML_T = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>涨停复盘 · 2026-11-12（对比 11-11）</title>
<script src="../assets/echarts.min.js"></script>
<script>if(typeof echarts==='undefined'){document.write('<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"><\\/script>');}</script>
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
<h1>涨停复盘 · 2026-11-12（周四）</h1>
<div class="sub">对比基准：2026-11-11（周三）｜口径：沪深两市（不含北交所）｜数据源：同花顺涨停/炸板/跌停池 + 东方财富涨停/炸板/跌停池 + 行情快照</div>

<div class="lead">
<p class="hl">一句话结论：11-11 是「钱厚 × 面窄 × 塔矮」，今天一天之内把最后一层拆完了 —— 塔尖上去了（最高板 4→__MAXB__），面塌了（涨停 __ZT_Y__→__ZT__ 只），钱也换了地方（涨停股成交 __AMT_SUM_Y__→__AMT_SUM__ 亿，−__AMT_SUM_PCT_ABS__%）。</p>
<p>三项情绪指标同步恶化、无一处背离：参与度（触及涨停 __TOUCH_Y__→__TOUCH__）、承接力（封板率 __SEAL_Y__%→__SEAL__%，−__SEAL_D__pct）、破坏力（跌停 __DT_Y__→__DT__ 只）。
炸板 __ZB__ 只、<span class="hl">回封 0 只（连续第 3 个交易日）</span>；炸板池成交 __ZB_AMT__ 亿 = 涨停股成交的 __ZB_RATIO__ 倍（昨 0.12 倍）——<span class="hl">冲板失败的钱第一次超过封住的钱。</span></p>
<p>但钱没离开市场：两市成交 __AMT__ 亿（__AMT_PCT__%）、__N_AMT_UP__/__N_IX__ 个指数成交额环比全正，增量集中在权重与科技核心（科创50 成交额 __KC_AMT_PCT__%、上证50 __SZ50_AMT_PCT__%，两者是 __N_UP__/__N_IX__ 个收红指数里的全部）。
代价是 <span class="hl">__N_BELOW__/__N_IX__ 个指数收于开盘价下方</span>、科创50 盘中最高 +4.96% 却只收 __KC_PCT__%（距当日最高 __KC_POS__%）——<span class="hl">增量进去当天就被套。定性：高低切换 + 打板生态断裂，不是全面退潮。</span></p>
</div>

<div class="kpis">
  <div class="kpi"><div class="lbl">涨停家数</div><div class="val down">__ZT__</div>
    <div class="dt mut">昨日 __ZT_Y__ <span class="down">__ZT_D__（__ZT_PCT__%）</span></div></div>
  <div class="kpi"><div class="lbl">封板率</div><div class="val down">__SEAL__%</div>
    <div class="dt mut">昨日 __SEAL_Y__% <span class="down">−__SEAL_D__pct</span></div></div>
  <div class="kpi"><div class="lbl">炸板 / 回封</div><div class="val">__ZB__ / __ZB_BACK__</div>
    <div class="dt mut">昨日 __ZB_Y__ / 0</div></div>
  <div class="kpi"><div class="lbl">跌停家数</div><div class="val down">__DT__</div>
    <div class="dt mut">昨日 __DT_Y__ <span class="down">__DT_D__</span>　触及跌停 __DT_T__</div></div>
  <div class="kpi"><div class="lbl">两市成交额</div><div class="val up">__AMT__亿</div>
    <div class="dt mut">昨日 __AMT_Y__亿 <span class="up">__AMT_D__亿</span></div></div>
  <div class="kpi"><div class="lbl">涨停股合计成交</div><div class="val down">__AMT_SUM__亿</div>
    <div class="dt mut">昨 __AMT_SUM_Y__亿 <span class="down">__AMT_SUM_PCT__%</span></div></div>
  <div class="kpi"><div class="lbl">晋级率</div><div class="val down">__ADV_RATE__%</div>
    <div class="dt mut">__ADV_N__/__ADV_TOT__ 只再涨停</div></div>
  <div class="kpi"><div class="lbl">最高连板</div><div class="val up">__MAXB__ 板</div>
    <div class="dt mut">昨日 __MAXB_Y__ 板</div></div>
</div>

<div class="card">
<h2>一、情绪温度计：三项同步恶化，且这次不是「假改善」</h2>
<table>
<tr><th>指标</th><th>__D2__（周二）</th><th>__D1__（周三）</th><th>__D0__（周四）</th><th>环比</th></tr>
__TBL_SENTI__
</table>
<div class="note" style="margin-top:10px">
参与度（触及涨停 __TOUCH_Y__→__TOUCH__，−__TOUCH_D_ABS__）、承接力（封板率 −__SEAL_D__pct）、破坏力（跌停 0→__DT__、封死率 __DT_R__%）
三处同时转差、<span class="hl">无一处背离</span>。按本刊的情绪形态分类，这是「无差别全面退潮」——与 10-14 同型，
区别于 09-23（承接力退潮但参与度平）、09-24（双降缩量锁仓）、10-12（广度退潮但资金缩圈）这三类背离型。
</div>
<div class="note" style="margin-top:8px">
<span class="hl">本次封板率的下滑不是「分母收缩型假改善」的反面陷阱</span>：分子的分母同时塌（涨停 __ZT__ 只、触及 __TOUCH__ 只），
封板率 = __ZT__ ÷ __TOUCH__ = __SEAL__%，是真实的承接力读数，与 10-15 那次「分子没变、分母塌了造出 +23.7pct 假改善」正好相反。
</div>
<div id="c_senti" class="chart" style="margin-top:16px"></div>
</div>

<div class="card">
<h2>二、指数与量能：__N_AMT_UP__/__N_IX__ 个指数放量，__N_UP__/__N_IX__ 个收红</h2>
<div class="two">
<div>
<table>
<tr><th>指数</th><th>今日</th><th>成交额环比</th><th>较昨收开盘</th><th>收盘距当日最高</th><th>成交额</th></tr>
__TBL_IDX__
</table>
<div class="note" style="margin-top:10px">
两市成交 __AMT__ 亿（昨 __AMT1_PLACEHOLDER__ 亿，__AMT_D__ 亿 / __AMT_PCT__%），
<span class="hl">__N_AMT_UP__/__N_IX__ 个指数成交额环比为正，但只有 __N_UP__ 个收红</span>。
「全线放量 + 绝大多数下跌」只有一种解释：主动性卖出增加、承接盘被动接货（同 10-08 / 10-15 判据）。
</div>
</div>
<div><div id="c_idx" class="chart-sm" style="height:360px"></div></div>
</div>
<div class="note" style="margin-top:10px">
<b>放量的方向是分裂的，必须拆开读：</b>
科创50 放量 __KC_AMT_PCT__%（__KC_AMT_PREV__→__KC_AMT__ 亿）且收 __KC_PCT__%、上证50 放量 __SZ50_AMT_PCT__% 收 __SZ50_PCT__%，
这两个是唯一收红的方向；而创业板放量 __CYB_AMT_PCT__% 却跌 __CYB_PCT__%、国证2000 与中证1000 均跌近 2%。
<span class="hl">增量在权重与科技核心，失血在小微盘与题材端</span>——这是高低切换，不是总量扩张。
</div>
<div class="note" style="margin-top:8px">
<b>但切换的代价已经写在上影线里：</b>科创50 今日开 +0.16%、盘中最高 +4.96%、收 __KC_PCT__%，<span class="hl">距当日最高 __KC_POS__%</span>，
__N_BELOW__/__N_IX__ 个指数收于开盘价下方。冲进去的钱当天没有浮盈，明日一旦不接就是二次抛压。
</div>
</div>

<div class="card">
<h2>三、连板梯队：塔尖上移一档，塔基塌掉 60%</h2>
<div class="two">
<div><div id="c_lad" class="chart-sm"></div></div>
<div>
<table>
<tr><th>梯队</th><th>__D1__</th><th>__D0__</th><th>变化</th></tr>
__TBL_LAD__
<tr><td>合计</td><td>__ZT_Y__</td><td class="hl">__ZT__</td><td class="down">__ZT_D__</td></tr>
</table>
<div class="note" style="margin-top:10px">
首板 __SB__ 只（昨 __SB_Y__ 只，少 __SB_D_ABS__ 只）、连板股 __LB__ 只（昨 __LB_Y__）、最高 __MAXB__ 板（昨 __MAXB_Y__ 板）。
首板占比 __SB_PCT__%。<span class="hl">「高度上移」与「结构空心」同时成立</span>：塔尖从 4 板抬到 5 板，但 1–2 板的地基从 77 只塌到 31 只。
</div>
</div>
</div>
<h3>今日连板股全名单（__LB__ 只，昨日 __LB_Y__ 只）</h3>
<table>
<tr><th>高度</th><th>代码</th><th>名称</th><th>首封</th><th>封单</th><th>成交额</th><th>流通市值</th><th>行业</th><th>涨停原因</th></tr>
__TBL_LB__
</table>
<div class="note" style="margin-top:10px">
<b>5 板的两只质量差异极大：</b>__TOP1__（__TOP1_LB__ 板）首封 __TOP1_FBT__、<span class="hl">封单仅 __TOP1_FUND__ 亿</span>，是尾盘一波拉上去的；
__TOP2__（__TOP2_LB__ 板）09:30 即封但<span class="hl">全天开板 __TOP2_ZBC__ 次</span>。两只都属「东方系」名称博弈，
<b>没有一个涨停板的钱是靠产业叙事支撑的</b>——这与 10-23 机器人链 45 只同源叙事的结构完全不同型。
</div>
</div>

<div class="card">
<h2>四、主线归因：今日不存在主线（前 __BLK_N__ 名里 __FAKE_N__ 名是伪聚类）</h2>
<table>
<tr><th>概念板块（同花顺）</th><th>涨停</th><th>其中连板</th><th>连板占比</th><th>成分行业数</th><th>板块内最强标</th><th>判定</th></tr>
__TBL_BLK__
</table>
<div class="note" style="margin-top:10px">
判据只看一个比值：<b>连板占比 = 其中连板 ÷ 涨停家数</b>。榜首「__TOP_BLK__」__TOP_BLK_N__ 家 / 连板 __TOP_BLK_PCT__%，
比值本身不低，但<span class="hl">成分散落 __TOP_BLK_HY__ 个行业</span>——是靠「海外市场 / 海外基建 / 海外拓展」这类通用词捞起来的，
典型地域型泛标签，<b>须显式剔除</b>。前 {@BLK_N@} 名里 {@FAKE_N@} 名都是这个毛病（乡村振兴 8 家散落 8 行业、机器人概念 8 家散落 8 行业）。<br>
<b>口径提示：</b>「其中连板」是同花顺 <code>continuous_plate_num</code>，统计「连续/断续上榜」；
与东财 <code>lbc</code>（当日连续连板数）是两套口径，同一簇可能报出两个数
（例：一带一路按同花顺 7 只、按东财 lbc≥2 只有 5 只）。判断「主线是否长高」用前者（跨日可比），判断「今日封板梯队」用后者。
</div>
<div id="c_th" class="chart" style="height:340px;margin-top:14px"></div>
<h3>按涨停原因聚类的同源簇（含连板数与成交占比）</h3>
<table>
<tr><th>簇</th><th>家数</th><th>其中连板</th><th>行业离散度</th><th>成交额</th><th>占涨停股成交</th><th>代表个股</th></tr>
__TBL_TH__
</table>
<div class="note" style="margin-top:10px">
<b>唯一同源、且有高度的簇是「东方系」</b>：__DF_N__ 只全部在榜（大东方 5 板、日出东方 5 板、东方环宇 4 板、东方海洋首板），
其中 __DF_LB__ 只连板，合计成交 __DF_AMT__ 亿 = 涨停股成交的 __DF_SHR__%。
但它<span class="hl">只是名字相同，不是产业链</span>——四只分属一般零售 / 厨卫电器 / 燃气 / 农产品加工，
属于「主线真空期的名称博弈」，是本刊反复标注的脆弱结构（同 09-22「华字辈」、10-19「某字辈」）。
「羊」字辈 __YANG_N__ 只、成交 __YANG_AMT__ 亿（__YANG_SHR__%）但<span class="hl">连板 0 只</span>，比东方系更弱。<br>
另一个连板率 100% 的簇是「光伏 / 玻璃基板」3 只（日出东方 5 板、亚玛顿 4 板、金辰股份 2 板），
但三只叙事并不同源（热泵 / 复牌易主 / 光伏设备），<span class="hl">属关键词碰撞而非产业集群，不计为主线</span>（同 10-30「电力/绿电」型伪簇）。
</div>
<div class="note" style="margin-top:8px">
<b>昨日的两条真主线今日同时熄火：</b>
算力硬件链（光模块 ∪ PCB ∪ 算力）__TH_N_Y__ 只 / 连板 __TH_LB_Y__ 只 / 成交 __TH_AMT_Y__ 亿
→ <span class="hl">__TH_N__ 只 / 连板 __TH_LB__ 只 / 成交 __TH_AMT__ 亿（__TH_AMT_PCT__%）</span>；
机器人链 __RB_N_Y__ 只 / 连板 __RB_LB_Y__ 只 / 成交 __RB_AMT_Y__ 亿
→ __RB_N__ 只 / 连板 __RB_LB__ 只 / 成交 __RB_AMT__ 亿（__RB_PCT__%）。
两条链的家数都腰斩到不足三分之一，<b>成交额却跌得更狠（−98.9% / −82.1%）</b>——是钱走了，不是标的轮换。
</div>
</div>

<div class="card">
<h2>五、行业迁移：__CLR_N__ 个行业清零，新增全是零散小簇</h2>
<div id="c_hy" class="chart" style="height:420px"></div>
<table style="margin-top:14px">
<tr><th>行业</th><th>__D1__</th><th>__D0__</th><th>增减</th><th>读数</th></tr>
__TBL_HY__
</table>
<div class="note" style="margin-top:12px">
行业数 __HY_N_Y__ → __HY_N__，<b>清零 __CLR_N__ 个</b>：__CLR_LIST__。
<b>新增 __NEW_N__ 个行业，其中绝大多数只有 1 家</b>：__NEW_LIST__——「一只票占一个行业」，不构成方向。
流出前三：汽车零部 10→1、通用设备 8→1、通信设备 7→0、元件 5→1。
<span class="hl">做多的方向不是「换了行业」，而是「行业被打散了」。</span>
</div>
</div>

<div class="card">
<h2>六、昨日涨停股今日表现：晋级率 __ADV_RATE__%，首板组中位三日内首次反超</h2>
<div class="kpis" style="grid-template-columns:repeat(auto-fit,minmax(140px,1fr))">
  <div class="kpi"><div class="lbl">晋级率</div><div class="val down">__ADV_RATE__%</div><div class="dt mut">__ADV_N__/__ADV_TOT__</div></div>
  <div class="kpi"><div class="lbl">平均涨幅</div><div class="val down">__PERF_MEAN__%</div><div class="dt mut">中位 __PERF_MED__%</div></div>
  <div class="kpi"><div class="lbl">翻绿比例</div><div class="val down">__NEG_PCT__%</div><div class="dt mut">__NEG__ 只；跌超 5% 的 __NEG5__ 只</div></div>
  <div class="kpi"><div class="lbl">跌幅≥9.8%</div><div class="val down">__LIMDN_N__ 只</div><div class="dt mut">__LIMDN_LIST__</div></div>
  <div class="kpi"><div class="lbl">GAP（首板−连板中位）</div><div class="val up">__GAP__pct</div><div class="dt mut">昨 __GAP_Y__pct、前日 __GAP_2__pct</div></div>
</div>
<table style="margin-top:16px">
<tr><th>分组</th><th>样本</th><th>晋级率</th><th>均涨</th><th>中位</th></tr>
<tr><td>昨日首板</td><td>__F_N__</td><td>__F_RATE__%</td><td class="down">__F_MEAN__%</td><td class="down">__F_MED__%</td></tr>
<tr><td>昨日连板（≥2 板）</td><td>__C_N__</td><td class="up">__C_RATE__%</td><td class="down">__C_MEAN__%</td><td class="down">__C_MED__%</td></tr>
</table>
<div class="note" style="margin-top:12px">
<b>GAP 三日内首次翻正：__GAP_2__ → __GAP_Y__ → __GAP__pct。</b>
它的含义是<span class="hl">市场不再为「高度」付费，改为为「位置」付费</span>——
昨日连板组今日中位 __C_MED__% 反而比首板组 __F_MED__% 更差，尽管连板组晋级率（__C_RATE__%）是首板组（__F_RATE__%）的 4 倍。
这两个数不矛盾：<b>少数高位票活下来，多数高位票被清算</b>（昨涨停股里跌停级别的 __LIMDN_N__ 只全是 1–2 板的中位票）。
配套证据：今日 37 只里新面孔 __NEW_FACE__ 只（__NEW_FACE_PCT__%），昨日涨停股只贡献 __FROM_Y__ 只。
</div>
<div id="c_perf" class="chart" style="height:__JS_CHART_H__px;margin-top:8px"></div>
</div>

<div class="card">
<h2>七、封板节奏与成交结构：封单腰斩 78%，密度跌到 1.51%</h2>
<div class="two">
<div><div id="c_ts" class="chart-sm"></div></div>
<div>
<table>
<tr><th>封板时段</th><th>__D1__</th><th>__D0__</th><th>变化</th></tr>
__TBL_TS__
</table>
<div class="note" style="margin-top:10px">
早盘封板 __TS_E0__/__ZT__ = __TS_E0_PCT__%（昨 __TS_E1__/__ZT_Y__ = __TS_E1_PCT__%），节奏<span class="hl">前移 __TS_ADV__pct</span>；
午后仅 __TS_PM0__ 只（昨 __TS_PM1__ 只）。「早封早炸 + 午后无人接力」的组合同 10-12 / 10-14，是存量抢跑而非增量进场。
</div>
</div>
</div>
<div class="kpis" style="grid-template-columns:repeat(auto-fit,minmax(160px,1fr));margin-top:16px">
  <div class="kpi"><div class="lbl">涨停股合计成交</div><div class="val down">__AMT_SUM__亿</div><div class="dt mut">占两市 __SHARE__%（昨 __SHARE_Y__%）</div></div>
  <div class="kpi"><div class="lbl">封单合计</div><div class="val down">__FUND_SUM__亿</div><div class="dt mut">昨 __FUND_SUM_Y__亿（__FUND_SUM_PCT__%）</div></div>
  <div class="kpi"><div class="lbl">封单中位</div><div class="val">__FUND_MED__亿</div><div class="dt mut">昨 __FUND_MED_Y__亿</div></div>
  <div class="kpi"><div class="lbl">单只中位成交</div><div class="val">__AMT_MED__亿</div><div class="dt mut">昨 __AMT_MED_Y__亿</div></div>
  <div class="kpi"><div class="lbl">一字板 / 换手板</div><div class="val">__ONEWORD__ / __HUANSHOU__</div><div class="dt mut">20cm 标的 __C20__ 只</div></div>
</div>
<div class="note" style="margin-top:12px">
<b>吸金密度跌破 3%–8% 自检区间，且是全线抽水而非结构变化：</b>密度 __SHARE__%（昨 __SHARE_Y__%），
总额 −__AMT_SUM_PCT_ABS__% 与单只中位 −__AMT_MED_D__% <span class="hl">同向下滑</span>——不是「家数少了但单只更重」，
而是每一只都在失血。同型校验：封单合计 −__FUND_SUM_PCT_ABS__%、封单中位 __FUND_MED_Y__→__FUND_MED__ 亿，同步腰斩。
</div>
<div class="note" style="margin-top:8px">
<b>另一个结构性变化：今日 __ZT__ 只涨停里 <span class="hl">20cm 标的 0 只</span></b>——涨停池完全主板化。
而科创50 盘中曾冲 +4.96%，却没有一只科创板标的封住，说明冲高的是<b>权重半导体大票</b>（通富微电盘中触板、收 +5.36%、成交 94.20 亿，为炸板池最大）。
「大票冲板失败 → 小票才封得住」= 资金风险偏好下行，只敢在低流通盘里做高度。
</div>
</div>

<div class="card">
<h2>八、承接力与破坏力：炸板 35 只零回封，跌停端首次出现昨涨停股</h2>
<h3>炸板池：__ZB_N__ 只，回封 __ZB_BACK__ 只，合计成交 __ZB_AMT__ 亿</h3>
<table>
<tr><th>代码</th><th>名称</th><th>行业</th><th>收盘</th><th>成交额</th><th>流通市值</th><th>开板次数</th></tr>
__TBL_ZB__
</table>
<div class="note" style="margin-top:10px">
<b>三条硬信号：</b>
① <span class="hl">回封 0 只，连续第 3 个交易日</span>（按「收盘价 ≥ 涨停价」严格判定，未用涨幅阈值）；
② 炸板池成交 / 涨停股成交 = <span class="hl">__ZB_RATIO__ 倍</span>（昨 0.12 倍）——冲板失败的钱首次超过封住的钱，承接质量系统性逆转；
③ 池内流通 &gt;100 亿的 __ZB_BIG__ 只、中大盘云集（通富微电 733.8 亿 / 景旺电子 656.7 亿 / 剑桥科技 338.6 亿），
其中 __ZB_HI__ 只来自昨日涨停 → <b>高位票集中炸板，且炸完不再回头</b>。
</div>
<h3>跌停池：__DT__ 只（同花顺汇总），封死率 __DT_R__%，其中 __DT_FROM_ZT__ 只来自昨日涨停</h3>
<table>
<tr><th>代码</th><th>名称</th><th>行业</th><th>收盘</th><th>成交额</th><th>流通市值</th><th>来源</th></tr>
__TBL_DT__
</table>
<div class="note" style="margin-top:10px">
跌停股合计成交 __DT_AMT__ 亿 = 涨停股成交的 <span class="hl">__DT_RATIO__ 倍</span>（昨 0 只跌停，比值无意义）；
行业 __DT_HY__ 个各不相同 → <b>彻底去板块化，不是板块性杀跌</b>，而是高位个股的清算。
但破坏力的方向已经转向：<span class="hl">__DT_FROM_ZT__ 只（中坚科技、上海电影、福莱新材）全部是昨日的 1–2 板中位票</span>，
这是 11-11「零跌停」之后第一次出现「昨日打板、今日跌停」的负反馈（打板资金隔夜亏损面 3.6%）。
</div>
<h3>市值结构：&gt;300 亿档从 9 只归零</h3>
<table>
<tr><th>流通市值档</th><th>__D0__ 只数</th><th>__D1__ 只数</th><th>__D0__ 成交</th><th>__D1__ 成交</th></tr>
__TBL_CAP__
</table>
<div class="note" style="margin-top:10px">
最能说明问题的一行：<span class="hl">&gt;300 亿档 __CAP1_BIG__ 只 → __CAP0_BIG__ 只</span>。
昨日那 9 只今日中位涨幅 __BIG1_MED__%（__BIG1_UP__/__BIG1_N2__ 上涨）——<b>它们没跌，但也不再涨停</b>。
大票从「打板主力」退回「指数承接盘」，这是 11-11 观察点⑤的直接答案。
</div>
</div>

<div class="card">
<h2>九、资金运动总结：钱从哪儿来、到哪儿去</h2>
<div class="lead" style="border-left-color:#2563eb;margin:0 0 14px">
<p class="hl">一句话：钱没有离开市场，但从「打板」搬到了「权重与科技核心」，而且搬进去当天就被套。</p>
</div>
<h3>钱的来路（四处，全部是打板端）</h3>
<ul>
<li><b>① 算力硬件链 —— 最大流出源。</b>光模块/CPO 13→1 只、PCB/覆铜板 9→3 只、算力/液冷 10→1 只，
合计 __TH_N_Y__→__TH_N__ 只、成交 __TH_AMT_Y__→__TH_AMT__ 亿（<span class="hl">__TH_AMT_PCT__%</span>）。
昨日的「5.6 倍放量」在一日内全部退回，第四轮发作仍零接棒。</li>
<li><b>② 机器人链 —— 家数腰斩、成交跌得更狠。</b>__RB_N_Y__→__RB_N__ 只、__RB_AMT_Y__→__RB_AMT__ 亿（__RB_PCT__%）、
连板 __RB_LB_Y__→__RB_LB__ 只。连板占比反而从 26.7% 升到 40%，<span class="hl">但那是分母塌陷的机械结果，不是长高</span>。</li>
<li><b>③ 大票档 —— 归零。</b>&gt;300 亿档 9→0 只、成交 443.7→0 亿；100–300 亿档 17→2 只。</li>
<li><b>④ AI 应用 / 传媒 —— 塌到 2 只。</b>9→2 只（仅剩吉视传媒、北纬科技），成交 74.8→28.8 亿（−61.5%）。</li>
</ul>
<h3>钱的去向（两处，都不在打板端）</h3>
<ul>
<li><b>① 权重与科技核心。</b>科创50 成交额 __KC_AMT_PREV__→__KC_AMT__ 亿（__KC_AMT_PCT__%）收 __KC_PCT__%、
上证50 __SZ50_AMT_PCT__% 收 __SZ50_PCT__%。
<span class="hl">但科创50 盘中最高 +4.96%、收 +0.73%，距高 __KC_POS__%</span> —— 增量进来即被套，明日是验证窗口。</li>
<li><b>② 主板低流通盘名称博弈。</b>东方系 __DF_N__ 只（__DF_AMT__ 亿 / 占 __DF_SHR__%）、「羊」字辈 __YANG_N__ 只（__YANG_AMT__ 亿）。
涨停股流通市值中位从 51.2 亿降到 44.2 亿，<span class="hl">钱在往更小的票里躲</span>。</li>
</ul>
<h3>形式判据（三条，决定这次是切换还是溃败）</h3>
<div class="note">
① 成交额环比 __N_AMT_UP__/__N_IX__ 全正、收盘仅 __N_UP__/__N_IX__ 红、__N_BELOW__/__N_IX__ 收于开盘价下方
→ <b>放量 + 下跌 + 高开低走</b>，与 10-08 / 10-15 的派发型同构，<b>不写「资金回流」</b>；<br>
② 增量独独落在科创50 与上证50 两个「涨跌相反于大盘」的方向 → <b>高低切换成立</b>，市场没有系统性失血；<br>
③ 涨停股合计成交 −__AMT_SUM_PCT_ABS__%、封单 −__FUND_SUM_PCT_ABS__%、回封 0、密度 1.51%
→ <b>打板生态是断裂而不是降温</b>，这与「切换」不冲突：钱去了别处，只是不再回来。
</div>
<h3>上期（11-11）七条观察点复核</h3>
<table>
<tr><th>上期观察点</th><th>今日事实</th><th>结论</th></tr>
<tr><td>① 算力硬件链能否长出高标（≥3 只 2 板且连板占比过 30%）</td><td>该链 __TH_N_Y__→__TH_N__ 只、连板 __TH_LB_Y__→__TH_LB__ 只、成交 __TH_AMT__ 亿</td><td class="down">证伪，第四轮零接棒</td></tr>
<tr><td>② 回封是否破零（≥3 只）</td><td>炸板 __ZB__ 只、回封 __ZB_BACK__ 只</td><td class="down">未破零，连续第 3 日</td></tr>
<tr><td>③ 4 板层能否脱离名称依赖</td><td>昨 4 板 2 只（均为东方系）→ 全部晋级 5 板；今日 4 板 2 只 = 东方环宇（东方系）+ <b>亚玛顿（复牌+控制权变更，一字板）</b></td><td class="mut">塔尖仍靠名称，4 板层出现 1 只非名称类</td></tr>
<tr><td>④ 上证缺口上沿 __GAP_UP__ 能否补掉</td><td>今日最高 __SH_HIGH__（超上沿 __GAP_FILL__ 点），收 __SH_CLOSE__（回落 __GAP_BACK__ 点）</td><td class="down">补掉但没站住，压力位确认</td></tr>
<tr><td>⑤ 量能能否延续（≥1.6 万亿且密度 ≥4%）</td><td>成交 __AMT__ 亿（达标），密度 1.51%（远低于 4%）</td><td class="mut">量能达标、<b>密度失守</b></td></tr>
<tr><td>⑥ &gt;300 亿档 9 只次日溢价</td><td>该 9 只今日中位 __BIG1_MED__%（__BIG1_UP__/__BIG1_N2__ 上涨），无一只涨停</td><td class="up">中位为正，机构建仓未证伪</td></tr>
<tr><td>⑦ 机器人链连板占比能否守住 25%</td><td>__RB_N__ 只 / 连板 __RB_LB__ 只 = 40%（家数 __RB_N_Y__→__RB_N__）</td><td class="mut">占比守住，但家数崩了 2/3</td></tr>
</table>
</div>

<div class="card">
<h2>十、明日 11/13 周五 观察点：六条，每条带阈值</h2>
<ul>
<li><b>① 5 板东方系 2 只能否上 6 板（第一优先）。</b>__TOP1__ 是 __TOP1_FBT__ 尾盘封、封单仅 __TOP1_FUND__ 亿；__TOP2__ 全天开板 __TOP2_ZBC__ 次。
<span class="hl">两只都上 6 板</span> ⇒ 名称博弈还能延续一天、情绪有支点；<b>断一只</b> ⇒ 最高板回落到 4 板、塔尖归零（对照 10-13 最高板 10→3）。</li>
<li><b>② 封板率能否修复（第二优先，阈值 65% / 45%）。</b>今日 __SEAL__%（本轮低位）。<span class="hl">回到 65% 以上</span> ⇒ 今日只是单日换手冲击；
<b>跌破 45%</b> ⇒ 37 只是本轮顶部，退潮确认。判断时必须并读涨停家数绝对值，防止分母收缩造假改善。</li>
<li><b>③ 回封是否破零（连续 3 日 0）。</b><span class="hl">≥3 只回封</span> ⇒ 承接资金回来；仍 0–1 只 ⇒ 「打开即当日不封」的惯性已经固化成制度性缺陷。</li>
<li><b>④ 科创50 放量 __KC_AMT_PCT__% 能否守住。</b>今日冲高 +4.96% 收 __KC_PCT__%、距高 __KC_POS__%。
<span class="hl">次日收红且成交额不低于 1,000 亿</span> ⇒ 权重承接真实、指数级行情成立；<b>跌回 1,300 点下方且缩量</b> ⇒ 今日放量是换手式出货。</li>
<li><b>⑤ 跌停端是否扩散。</b>今日 __DT__ 只（含 __DT_FROM_ZT__ 只昨涨停股）。<span class="hl">≥8 只</span> ⇒ 拉高派发开始、高位票要系统性清算；
<b>回到 0–2 只</b> ⇒ 今日这 4 只只是个股事件、非系统性派发。</li>
<li><b>⑥ 密度能否回到 3%（吸金真伪的唯一裁判）。</b>今日 1.51%（涨停股 291.3 亿 / 两市 19,321 亿）。
<span class="hl">回到 3% 以上</span> ⇒ 打板资金回场；<b>连续第二日低于 2%</b> ⇒ 涨停板不再是资金主战场，本刊的涨停框架应降权使用、改看指数与板块轮动。</li>
</ul>
<div class="note" style="margin-top:8px">
判定顺序固定：先看①（高度能否延续）→ 再看②③（承接质量）→ 最后看⑥（量能裁判）。
只看涨停家数会得出「今日腰斩、明天抄底」，只看最高板会得出「5 板新高、情绪转强」——<b>两者都错。今日是「塔尖上移 + 塔基塌陷 + 钱换场地」的三重分裂</b>。
</div>
</div>

<div class="card">
<h2>十一、数据口径与风险提示</h2>
<div class="note">
<b>家数</b>：同花顺涨停池沪深口径 __ZT__ 家；东财涨停池 __ZT__ 只，<span class="hl">两源完全一致（差额 0，今日涨停池内无北交所标的）</span>。<br>
<b>跌停</b>：同花顺汇总 __DT__ 家（触及 __DT_T__、封死率 __DT_R__%、被买回 __DT_OPEN__ 只）；东财池 5 只，
差额 1 只<b>无法归因</b>（得邦照明 603303 / 煌上煌 002695 均为沪深代码，既非北交所、也非池空）。
按本刊口径，<b>家数取同花顺汇总 4 家</b>，明细表按东财池原样列出 5 只并标注。<br>
<b>成交额 / 封单 / 流通市值 / 连板数（lbc）</b>：一律取东财 <code>em_ZT.pool</code> 字段；
同花顺 <code>currency_value</code> 不是成交额（实测差约 10 倍），仅用于 <code>reason_type</code>、<code>high_days</code>、<code>limit_up_type</code> 与汇总家数。<br>
<b>「触及涨停 / 封板率」</b>：取 <code>ths_zt.total.today</code> 的 <code>history_num</code> / <code>rate</code>；
三日序列表中 __D2__ 的跌停/触及跌停取自 __D1__ 文件的 <code>yesterday</code> 字段，不由 __D0__ 文件推算。<br>
<b>吸金密度</b>：涨停股合计成交 ÷ 两市成交。今日 __SHARE__% 跌破 3%–8% 自检区间，已用「单只中位成交 __AMT_MED_Y__→__AMT_MED__ 亿」
与「封单中位 __FUND_MED_Y__→__FUND_MED__ 亿」双向交叉验证 ⇒ <b>字段无误，是全线抽水</b>。<br>
<b>炸板回封</b>：严格按「收盘价 ≥ 涨停价」判定；今日 __ZB_N__ 只炸板中 __ZB_BACK__ 只满足，故回封记 0，未使用涨幅阈值（20cm 标的会被误判）。<br>
<b>跨日对比</b>：「昨日」一类数字全部从 <code>zt_stats_20261111.json</code> / <code>zt_review_20261111.json</code> 现算，
不继承 11-11 报告内的手写结论。昨日涨停股合计成交按东财 85 只口径复算为 __AMT_SUM_Y__ 亿，
与 11-11 报告的同花顺 84 只口径 927.7 亿相差 3.8 亿（北交所 920157 宇特光电），已在两处口径中分别声明。<br>
<b>封板时间双源一致率</b>：__ZT__/__ZT__ = 100%（东财 <code>fbt</code> vs 同花顺时间戳，分钟级）。
</div>
<div class="warn" style="margin-top:14px">
<b>风险提示：</b>本报告为盘后数据复盘与资金行为分析，所有结论基于公开行情数据的统计推断，<b>不构成任何投资建议</b>。
涨停板交易具有高波动、高换手、隔夜风险大的特征，历史统计规律不保证未来重复。
今日出现的「名称博弈」（东方系 / 羊字辈）在历史样本中普遍具备一日游与集体断板的特征，风险显著高于产业叙事型主线。
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
  grid:{left:150,right:70,top:16,bottom:24},
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

V["__AMT1_PLACEHOLDER__"] = "{:,.0f}".format(AMT1)
V["__AMT_SUM_PCT_ABS__"] = "%.1f" % abs((amt_sum / amt_sum1 - 1) * 100)
V["__AMT_MED_D__"] = "%.1f" % abs((amt_med / amt_med1 - 1) * 100)
V["__FUND_SUM_PCT_ABS__"] = "%.1f" % abs((fund_sum / fund_sum1 - 1) * 100)
V["__TOUCH_D_ABS__"] = str(abs(TOUCH - TOUCH1))
V["__SB_D_ABS__"] = str(abs(SB_N - SB_N1))
V["__TS_ADV__"] = "%.0f" % (TS_E0 / ZT * 100 - TS_E1 / ZT1 * 100)

HTML = HTML_T
for k, v in V.items():
    HTML = HTML.replace(k, v)
HTML = HTML.replace("{@BLK_N@}", str(len(blk))).replace("{@FAKE_N@}", str(FAKE_N))

fp = os.path.join(REP, "涨停复盘对比-%s.html" % D0)
with open(fp, "w", encoding="utf-8") as f:
    f.write(HTML)
import re
left = re.findall(r"__[A-Z_0-9]+__", HTML)
print("saved ->", fp, len(HTML) // 1024, "KB")
print("placeholder residue:", sorted(set(left)))
