# -*- coding: utf-8 -*-
"""涨停复盘报告 20261020 vs 20261019（跌停潮退去 / 机器人链接棒：参与度回升、承接力不升反降）

用法：python zt_report_20261020.py 20261020
输入：out/zt_stats_20261020.json、out/zt_review_20261020.json、out/zt_stats_20261019.json
     跌停池明细 out/_dt1020.json、out/_dt1019.json（东财 getTopicDTPool，sort=fund:asc）
     昨日跌停股 / 出版链 / 电网设备 / 有色今日行情：腾讯快照 qt.gtimg.cn（脚本内实时抓取）
     各指数 10-19 成交额与涨跌幅：out/_idx_amt_1019.json（同花顺指数日线，显式按日期取）
输出：reports/涨停复盘对比-20261020.html
"""
import json, os, sys, html, re, urllib.request
from statistics import mean, median

ROOT = os.environ.get("ZT_ROOT") or os.getcwd()
OUT = os.path.join(ROOT, "out")
REP = os.path.join(ROOT, "reports")
os.makedirs(REP, exist_ok=True)

D0 = sys.argv[1] if len(sys.argv) > 1 else "20261020"
S = json.load(open(os.path.join(OUT, f"zt_stats_{D0}.json"), encoding="utf-8"))
D0, D1, D2 = S["D0"], S["D1"], S["D2"]
B = json.load(open(os.path.join(OUT, f"zt_review_{D0}.json"), encoding="utf-8"))
r0, r1 = S["r0"], S["r1"]
perf = S["perf"]
s0, s1 = S["senti"][D0], S["senti"][D1]


def md(ds):
    return f"{int(ds[4:6])}/{int(ds[6:8])}"


def esc(s):
    return html.escape(str(s))


def hhmm(v):
    s = str(int(v)).zfill(6)
    return s[:2] + ":" + s[2:4]


def pct_txt(v, nd=2):
    if v is not None and abs(v) < 0.005:
        return ("{:." + str(nd) + "f}").format(0.0)
    return ("{:+." + str(nd) + "f}").format(v)


# ================= 一、情绪 =================
_d0 = B["dates"][D0]["ths_zt"]["total"]
_d1 = B["dates"][D1]["ths_zt"]["total"]
TOUCH0, TOUCH1 = _d0["today"]["history_num"], _d1["today"]["history_num"]
_dc0 = B["dates"][D0]["ths_zt"]["limit_down_count"]["today"]
_dc1 = B["dates"][D1]["ths_zt"]["limit_down_count"]["today"]
DTOUCH0, DTOUCH1 = _dc0["history_num"], _dc1["history_num"]
DTOUCH_OPEN = _dc0["open_num"]
DSEAL0, DSEAL1 = _dc0["rate"] * 100, _dc1["rate"] * 100

days = [
    {"d": md(D2), "zt": s1["zt_prev"], "zb": s1["zb_prev"], "dt": s1["dt_prev"]},
    {"d": md(D1), "zt": s1["zt"], "zb": s1["zb"], "dt": s1["dt"]},
    {"d": md(D0), "zt": s0["zt"], "zb": s0["zb"], "dt": s0["dt"]},
]
for x in days:
    x["seal"] = x["zt"] / (x["zt"] + x["zb"]) * 100 if (x["zt"] + x["zb"]) else 0.0

# ================= 二、指数 =================
IX_ORDER = ["上证指数", "深证成指", "创业板指", "科创50", "沪深300", "中证500",
            "中证1000", "国证2000", "上证50", "中小100", "北证50"]
IX_PREV = json.load(open(os.path.join(OUT, "_idx_amt_1019.json"), encoding="utf-8"))
idx_now = {v["name"]: v for v in B["indexes"].values() if isinstance(v, dict) and v.get("name")}
ix = []
for nm in IX_ORDER:
    v = idx_now.get(nm) or {}
    a0 = (v.get("amount_wan") or 0) / 10000.0
    p1 = IX_PREV.get(nm, {}).get("amt16")
    a1 = (p1 / 1e8) if p1 else 0.0
    ix.append({"name": nm, "pct": v.get("pct") or 0.0, "amt": a0, "amt_y": a1,
               "prev_pct": IX_PREV.get(nm, {}).get("pct16"),
               "yoy": ((a0 / a1 - 1) * 100) if a1 else None})
ixr = {x["name"]: x for x in ix}
IX_A = [x for x in ix if x["yoy"] is not None]
N_SHRINK = sum(1 for x in IX_A if x["yoy"] < 0)
N_UP = sum(1 for x in ix if x["pct"] > 0)
N_DN = sum(1 for x in ix if x["pct"] < 0)
amt_today = ixr["上证指数"]["amt"] + ixr["深证成指"]["amt"]
amt_prev = (S.get("tot") or {}).get("prev") or amt_today
amt_pct = (amt_today / amt_prev - 1) * 100 if amt_prev else 0.0
amt_delta = amt_today - amt_prev
STYLE_SORTED = sorted(IX_A, key=lambda x: -x["yoy"])

# ================= 三、梯队 =================
lad0 = {int(k): v for k, v in s0["ladder"].items()}
lad1 = {int(k): v for k, v in s1["ladder"].items()}
lad_max = max(max(lad0), max(lad1))
maxb = max(lad0) if lad0 else 0
maxb_y = max(lad1) if lad1 else 0
lb_all = sorted([r for r in r0 if (r["lbc"] or 1) >= 2], key=lambda x: (-(x["lbc"] or 0), x["code"]))
LB_HIGH_NAMES = "、".join(esc(r["name"]) for r in lb_all if (r["lbc"] or 0) == maxb) or "—"
_y_top = sorted([r for r in r1 if (r["lbc"] or 0) == maxb_y], key=lambda x: x["code"])
LB_HIGH_NAMES_Y = "、".join(esc(r["name"]) for r in _y_top) or "—"
LAD2_NAMES = "、".join(esc(r["name"]) for r in lb_all if (r["lbc"] or 0) == 2) or "—"

# ================= 四、主线 =================
REASON = {x["code"]: (x.get("reason_type") or "") for x in (B["dates"][D0]["ths_zt"].get("info") or [])}


def reason_of(r):
    return r.get("reason") or REASON.get(r["code"], "")


LOWALT_KWS = ["飞行汽车", "低空经济", "eVTOL", "低空", "无人机", "通航"]
ROBOT_KWS = ["机器人", "具身", "减速器", "丝杠", "灵巧手", "伺服", "执行器", "精密传动"]
EDGE_KWS = ["端侧AI", "AI眼镜", "AI PC", "SoC", "无线芯片", "AIoT量产", "通信模组", "智能终端", "智能穿戴", "AI ISP"]
MIL_KWS = ["军工", "兵装", "军用", "弹药", "防务", "地面兵装", "航空装备", "光电", "军民"]
CALC_KWS = ["PCB", "覆铜板", "光通信", "算力", "服务器", "SSD", "存储", "半导体", "液冷", "光刻"]
MEDIA_KWS = ["出版", "传媒", "影视", "短剧", "漫剧", "IP", "图书", "院线", "数字阅读", "AI应用", "内容"]
MED_KWS = ["中药", "创新药", "医药", "医疗器械", "原料药", "制药", "医疗", "宠物药"]
CONS_KWS = ["家居", "小家电", "调味", "食品", "零售", "纺织", "白酒", "餐饮", "教育", "银发"]


def sel(kws):
    return [r for r in r0 if any(k in reason_of(r) for k in kws)]


lowalt_sel, robot_sel, edge_sel, mil_sel, calc_sel, media_sel, med_sel, cons_sel = (
    sel(LOWALT_KWS), sel(ROBOT_KWS), sel(EDGE_KWS), sel(MIL_KWS), sel(CALC_KWS), sel(MEDIA_KWS),
    sel(MED_KWS), sel(CONS_KWS))

blocks = sorted((B["dates"][D0].get("ths_block") or []), key=lambda x: -x["limit_up_num"])
blocks1 = sorted((B["dates"][D1].get("ths_block") or []), key=lambda x: -x["limit_up_num"])
b_top = blocks[:7]
_b1 = {b["name"]: b for b in blocks1}


def blk_nl(src, name):
    b = next((x for x in src if x["name"] == name), None)
    if not b:
        return (0, 0, 0.0)
    n = b["limit_up_num"]; l = b.get("continuous_plate_num", 0)
    return (n, l, l / n * 100 if n else 0.0)


QC_N, QC_LB, QC_R = blk_nl(blocks, "汽车零部件")
QC_N_Y, QC_LB_Y, QC_R_Y = blk_nl(blocks1, "汽车零部件")
DK_N, DK_LB, DK_R = blk_nl(blocks, "低空经济")
DK_N_Y, DK_LB_Y, DK_R_Y = blk_nl(blocks1, "低空经济")


def hy_stat(src, name):
    rows = [r for r in src if r["hybk"] == name]
    n = len(rows)
    l = sum(1 for r in rows if (r["lbc"] or 1) >= 2)
    return n, l, (l / n * 100 if n else 0.0)


def kw_stat(src, kws):
    rows = [r for r in src if any(k in (r.get("reason") or "") for k in kws)]
    n = len(rows)
    l = sum(1 for r in rows if (r["lbc"] or 1) >= 2)
    return n, l, (l / n * 100 if n else 0.0)


# 昨日两条主线的同口径对照：走「东财行业」与「涨停原因关键词」，不依赖板块榜前 20（跌出前 20 不等于 0 家）
QC_N, QC_LB, QC_R = hy_stat(r0, "汽车零部")
QC_N_Y, QC_LB_Y, QC_R_Y = hy_stat(r1, "汽车零部")
DK_N, DK_LB, DK_R = kw_stat(r0, LOWALT_KWS)
DK_N_Y, DK_LB_Y, DK_R_Y = kw_stat(r1, LOWALT_KWS)
RB_N, RB_LB, RB_R = blk_nl(blocks, "机器人概念")
RB_N_Y, RB_LB_Y, RB_R_Y = blk_nl(blocks1, "机器人概念")
RX_N, RX_LB, RX_R = blk_nl(blocks, "人形机器人")
RX_N_Y, RX_LB_Y, RX_R_Y = blk_nl(blocks1, "人形机器人")
UAV_N_Y, UAV_LB_Y = blk_nl(blocks1, "无人机")[0], blk_nl(blocks1, "无人机")[1]
EV_N_Y, EV_LB_Y = blk_nl(blocks1, "飞行汽车(eVTOL)")[0], blk_nl(blocks1, "飞行汽车(eVTOL)")[1]
NEW_N_Y, NEW_LB_Y = blk_nl(blocks1, "新能源汽车")[0], blk_nl(blocks1, "新能源汽车")[1]
CONC_TOP5_TXT = "、".join("%s（%d 家 / 连板 %d）" % (esc(b["name"]), b["limit_up_num"], b.get("continuous_plate_num", 0))
                       for b in b_top[:5])
CONC_TOP7_MAXLB = max((b.get("continuous_plate_num", 0) for b in b_top), default=0)
CONC_MAX_R = max((b.get("continuous_plate_num", 0) / b["limit_up_num"] * 100 for b in b_top if b["limit_up_num"]), default=0.0)
CONC_MAX_R_Y = max((b.get("continuous_plate_num", 0) / b["limit_up_num"] * 100 for b in blocks1[:7] if b["limit_up_num"]), default=0.0)

concept_rows = sorted(blocks[:12], key=lambda x: x["limit_up_num"])


# 行业离散度
def dispersion(name):
    b = next((x for x in blocks if x["name"] == name), None)
    if not b:
        return 0, []
    codes = [s["code"] for s in b["stock_list"]]
    hy = sorted({r["hybk"] for r in r0 if r["code"] in codes})
    return len(hy), hy


QC_DISP, QC_DISP_LIST = dispersion("汽车零部件")
DK_DISP, DK_DISP_LIST = dispersion("低空经济")
RB_DISP, RB_DISP_LIST = dispersion("机器人概念")

# 机器人链明细（涨停原因关键词口径，含「机器人/具身/减速器/丝杠/灵巧手/伺服/执行器/精密传动」）
ROB_SEL = sorted(robot_sel, key=lambda x: (-(x["lbc"] or 0), -(x["amount"] or 0)))
ROB_N = len(robot_sel)
ROB_LB = sum(1 for r in robot_sel if (r["lbc"] or 1) >= 2)
ROB_R = ROB_LB / ROB_N * 100 if ROB_N else 0.0
ROB_AMT = sum(r["amount"] or 0 for r in robot_sel) / 1e8
ROB_FUND = sum(r["fund"] or 0 for r in robot_sel) / 1e8
ROB_HY = sorted({r["hybk"] for r in robot_sel})
ROB_HY_N = len(ROB_HY)
ROB_MAXB = max((r["lbc"] or 1) for r in robot_sel) if robot_sel else 0
ROB_NO_LB_N = sum(1 for r in robot_sel if (r["lbc"] or 1) == 1)

TBL_ROB = "".join(
    "<tr><td>{0}</td><td class='hl'>{1}</td><td>{2}板</td><td>{3}</td><td>{4:.2f}亿</td><td>{5:.2f}亿</td>"
    "<td>{6}</td><td style='text-align:left;color:#4b5563'>{7}</td></tr>".format(
        r["code"], esc(r["name"]), (r["lbc"] or 1), (r["fbt"][:5] if r["fbt"] else "—"),
        (r["amount"] or 0) / 1e8, (r["fund"] or 0) / 1e8, esc(r["hybk"]), esc(reason_of(r)))
    for r in ROB_SEL)

# ================= 五、行业迁移 =================
hy0, hy1 = S["hy0"], S["hy1"]
hy_keys = sorted(set(list(hy0) + list(hy1)),
                 key=lambda k: (-((hy0.get(k, 0) + hy1.get(k, 0)) + abs(hy0.get(k, 0) - hy1.get(k, 0)) * 2),
                                -max(hy0.get(k, 0), hy1.get(k, 0)), k))
hy_tbl = [{"name": k, "t": hy0.get(k, 0), "y": hy1.get(k, 0)} for k in hy_keys[:18]]
HY_ZERO = sorted([k for k in hy1 if hy1.get(k, 0) > 0 and hy0.get(k, 0) == 0])
HY_ZERO_N = len(HY_ZERO)
HY_ZERO_NAMES = "、".join(HY_ZERO) or "无"
HY_UP_N = len([k for k in hy0 if hy0.get(k, 0) > 0 and hy0.get(k, 0) > hy1.get(k, 0)])

# ================= 六、昨日涨停股今日表现 =================
adv = [p for p in perf if p["again"]]
adv_rate = len(adv) / len(perf) * 100
pcts = [p["pct"] for p in perf if p["pct"] is not None]
neg = sum(1 for p in pcts if p < 0)
neg_low = sum(1 for p in pcts if p <= -5)
perf_sorted = sorted(perf, key=lambda x: -(x["pct"] if x["pct"] is not None else -999))
p_shou = [p for p in perf if (p["lbc"] or 1) == 1]
p_lian = [p for p in perf if (p["lbc"] or 1) >= 2]


def grp(rows):
    n = len(rows)
    if not n:
        return 0, 0.0, 0.0, 0
    a = sum(1 for p in rows if p["again"])
    pp = [p["pct"] for p in rows if p["pct"] is not None]
    return n, a / n * 100, median(pp), sum(1 for v in pp if v < 0)


n_s, r_s, m_s, ng_s = grp(p_shou)
n_l, r_l, m_l, ng_l = grp(p_lian)
GAP = m_s - m_l

_py = json.load(open(os.path.join(OUT, "zt_stats_%s.json" % D1), encoding="utf-8"))["perf"]
_gy_s = [p["pct"] for p in _py if (p["lbc"] or 1) == 1 and p["pct"] is not None]
_gy_l = [p["pct"] for p in _py if (p["lbc"] or 1) >= 2 and p["pct"] is not None]
m_s_y = median(_gy_s) if _gy_s else 0.0
m_l_y = median(_gy_l) if _gy_l else 0.0
GAP_Y = m_s_y - m_l_y
assert len(_gy_s) + len(_gy_l) == len(_py), "D1 分组计数不闭合"

PERF_BOT5 = "、".join("%s %s%%" % (esc(p["name"]), pct_txt(p["pct"])) for p in perf_sorted[-5:][::-1])
PERF_TOP5 = "、".join("%s %s%%" % (esc(p["name"]), pct_txt(p["pct"])) for p in perf_sorted[:5])

# ================= 七、跌停池 =================
DT_TD = json.load(open(os.path.join(OUT, f"_dt{D0[4:]}.json"), encoding="utf-8"))["data"]["pool"]
DT_YD = json.load(open(os.path.join(OUT, f"_dt{D1[4:]}.json"), encoding="utf-8"))["data"]["pool"]
r1_set = {x["code"] for x in r1}
r0_set = {x["code"] for x in r0}
dt1_set = {x["c"] for x in DT_YD}
dt_from_zt = [x for x in DT_TD if x["c"] in r1_set]
dt_cont = [x for x in DT_TD if x["c"] in dt1_set]
dt_amt_td = sum(x.get("amount", 0) for x in DT_TD) / 1e8
dt_amt_yd = sum(x.get("amount", 0) for x in DT_YD) / 1e8
DT_TC = len(DT_TD)
DT_DIFF = DT_TC - s0["dt"]
DT_TD_BIG_N = sum(1 for x in DT_TD if x.get("ltsz", 0) >= 1e10)
DT_HY_N = len({x.get("hybk") for x in DT_TD})
dt_top1 = max(DT_TD, key=lambda x: x.get("amount", 0))


def sym(c):
    return ("bj" if c.startswith(("43", "83", "87", "92")) else ("sh" if c.startswith(("6", "5", "9")) else "sz")) + c


def snap(codes):
    res = {}
    try:
        op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        u = "https://qt.gtimg.cn/q=" + ",".join(sym(c) for c in codes)
        raw = op.open(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=25).read().decode("gbk", "ignore")
        for l in raw.strip().split(";"):
            if '="' not in l:
                continue
            f = l.split('"')[1].split("~")
            if len(f) < 45:
                continue
            res[l.split("=")[0].strip().replace("v_", "")[2:]] = (
                float(f[32]) if f[32] else 0.0, f[1], float(f[44] or 0))
    except Exception:
        pass
    return res


_sp = snap([x["c"] for x in DT_YD])
rel = [{"c": x["c"], "n": x["n"], "h": x["hybk"], "pct": _sp.get(x["c"], (None,))[0]} for x in DT_YD]
rel_vals = [x["pct"] for x in rel if x["pct"] is not None]
rel_mean = mean(rel_vals) if rel_vals else 0.0
rel_med = median(rel_vals) if rel_vals else 0.0
rel_up = sum(1 for v in rel_vals if v > 0)
rel_lim = sum(1 for v in rel_vals if v >= 9.8)
_rel_top = sorted([x for x in rel if x["pct"] is not None], key=lambda x: -x["pct"])
REL_TOP_NAME = _rel_top[0]["n"] if _rel_top else "—"
REL_TOP_PCT = pct_txt(_rel_top[0]["pct"]) if _rel_top else "—"
INTER_N = len(r0_set & dt1_set)

# 出版 / 传媒链全景（东财行业「出版」+ 同源传媒标的，口径已在报告声明）
PUB = ["601811", "601999", "603999", "603096", "603230", "600825", "300364", "601801", "600373",
       "000719", "600551", "601098", "600757", "601019", "600229", "000607", "002181", "300788",
       "300413", "002400", "600088", "300291", "002238"]
_pub = snap(PUB)
pub_rows = [{"c": c, "n": v[1], "pct": v[0], "mv": v[2]} for c, v in _pub.items()]
pub_vals = [r["pct"] for r in pub_rows]
PUB_N = len(pub_rows)
PUB_DN = sum(1 for v in pub_vals if v < 0)
PUB_DT = sum(1 for v in pub_vals if v <= -9.8)
PUB_MEAN = mean(pub_vals) if pub_vals else 0.0
PUB_MED = median(pub_vals) if pub_vals else 0.0
TBL_PUB = "".join(
    "<tr><td>{0}</td><td class='hl'>{1}</td><td class='{2}'>{3}</td><td>{4:.0f}亿</td><td>{5}</td></tr>".format(
        r["c"], esc(r["n"]), "down" if r["pct"] < 0 else "up", pct_txt(r["pct"]) + "%", r["mv"],
        "<b class='hl'>跌停</b>" if r["pct"] <= -9.8 else ("昨涨停" if r["c"] in r1_set else "—"))
    for r in sorted(pub_rows, key=lambda x: x["pct"])[:12])

DT_HY_CNT = {}
for x in DT_TD:
    DT_HY_CNT[x.get("hybk") or "—"] = DT_HY_CNT.get(x.get("hybk") or "—", 0) + 1
DT_HY_TOP = sorted(DT_HY_CNT.items(), key=lambda z: (-z[1], z[0]))[:8]
DT_HY_TOP_TXT = "、".join("%s %d" % (k, v) for k, v in DT_HY_TOP)

# 板块级验证：电网设备（思源电气） / 有色（洛阳钼业）
GRID = ["002028", "600312", "000400", "600406", "600089", "601179", "600869", "600577",
        "300990", "600517", "002879", "002364"]
_grid = snap(GRID)
grid_rows = [{"c": c, "n": v[1], "pct": v[0], "mv": v[2]} for c, v in _grid.items()]
grid_vals = [r["pct"] for r in grid_rows]
GRID_N = len(grid_rows)
GRID_DN = sum(1 for v in grid_vals if v < 0)
GRID_DT = sum(1 for v in grid_vals if v <= -9.8)
GRID_MEAN = mean(grid_vals) if grid_vals else 0.0
TBL_GRID = "".join(
    "<tr><td>{0}</td><td class='hl'>{1}</td><td class='{2}'>{3}</td><td>{4:.0f}亿</td></tr>".format(
        r["c"], esc(r["n"]), "down" if r["pct"] < 0 else "up", pct_txt(r["pct"]) + "%", r["mv"])
    for r in sorted(grid_rows, key=lambda x: x["pct"])[:8])

MT = ["603993", "601899", "600362", "601168", "000630", "600111"]
_mt = snap(MT)
mt_rows = [{"n": v[1], "pct": v[0], "mv": v[2]} for v in _mt.values()]
mt_vals = [r["pct"] for r in mt_rows]
MT_N = len(mt_rows)
MT_DN = sum(1 for v in mt_vals if v < 0)
MT_MEAN = mean(mt_vals) if mt_vals else 0.0

# ================= 八、封板节奏与成交结构 =================
TS_ORDER = ["竞价/秒板", "开盘半小时", "上午盘中", "午后盘中", "尾盘"]
ts0, ts1 = S["timeslot"]["today"], S["timeslot"]["yesterday"]
amts = [r["amount"] for r in r0 if r["amount"]]
amts1 = [r["amount"] for r in r1 if r["amount"]]
funds = [r["fund"] for r in r0 if r["fund"]]
funds1 = [r["fund"] for r in r1 if r["fund"]]
amt_sum, amt_sum1 = sum(amts) / 1e8, sum(amts1) / 1e8
fund_sum, fund_sum1 = sum(funds) / 1e8, sum(funds1) / 1e8
share = amt_sum / amt_today * 100
share1 = amt_sum1 / amt_prev * 100
amt_med, amt_med1 = median(amts) / 1e8, median(amts1) / 1e8
fund_med, fund_med1 = median(funds) / 1e8, median(funds1) / 1e8
oneword = sum(1 for r in r0 if "一字" in (r["limit_up_type"] or ""))
huanshou = sum(1 for r in r0 if "换手" in (r["limit_up_type"] or ""))
oneword1 = sum(1 for r in r1 if "一字" in (r["limit_up_type"] or ""))
huanshou1 = sum(1 for r in r1 if "换手" in (r["limit_up_type"] or ""))
fund_top = sorted(r0, key=lambda x: -(x["fund"] or 0))[:5]
ft0 = fund_top[0]
ft0_val = (ft0["fund"] or 0) / 1e8
ft0_pct = ft0_val / fund_sum * 100
ft0_ratio = ft0_val / ((ft0["amount"] or 1) / 1e8)
amt_top = sorted(r0, key=lambda x: -(x["amount"] or 0))[:5]

zbpool = (B["dates"][D0].get("em_ZB") or {}).get("pool") or []
zbpool1 = (B["dates"][D1].get("em_ZB") or {}).get("pool") or []
zb_sealed = [z for z in zbpool if z["p"] >= z["ztp"]]
zb_open = [z for z in zbpool if z["p"] < z["ztp"]]
zb_sealed1 = [z for z in zbpool1 if z["p"] >= z["ztp"]]
zb_big = max(zbpool, key=lambda z: z.get("amount", 0)) if zbpool else None

tbl_fund_top = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td>{2}板</td><td>{3:.2f}亿</td><td>{4:.2f}亿</td><td>{5:.2f}x</td></tr>".format(
        esc(x["name"]), x["code"], (x["lbc"] or 1), (x["fund"] or 0) / 1e8, (x["amount"] or 0) / 1e8,
        (x["fund"] or 0) / (x["amount"] or 1))
    for x in fund_top)
tbl_amt_top = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td>{2}板</td><td>{3:.2f}亿</td><td>{4:.2f}亿</td><td>{5}</td></tr>".format(
        esc(x["name"]), x["code"], (x["lbc"] or 1), (x["amount"] or 0) / 1e8, (x["fund"] or 0) / 1e8, esc(x["hybk"]))
    for x in amt_top)
tbl_zb = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td class='{4}'>{5}</td><td>{6:.2f}亿</td><td>{7:.0f}亿</td></tr>".format(
        esc(z["n"]), z["c"], hhmm(z["fbt"]), esc(z["hybk"]), "up" if z["zdp"] >= 0 else "down",
        pct_txt(z["zdp"]) + "%", z["amount"] / 1e8, z["ltsz"] / 1e8)
    for z in sorted(zb_open, key=lambda x: -(x.get("amount", 0)))[:10])

tbl_lianban = "".join(
    "<tr><td>{0}板</td><td>{1}</td><td class='hl'>{2}</td><td>{3}</td><td>{4:.2f}亿</td><td>{5:.2f}亿</td><td>{6:.1f}%</td>"
    "<td>{7}</td><td style='text-align:left;color:#4b5563'>{8}</td></tr>".format(
        r["lbc"], r["code"], esc(r["name"]), (r["fbt"][:5] if r["fbt"] else "—"),
        (r["fund"] or 0) / 1e8, (r["amount"] or 0) / 1e8, (r["turnover"] or 0), esc(r["hybk"]), esc(reason_of(r)))
    for r in lb_all)


def dt_tag(x):
    tags = []
    if x["c"] in r1_set:
        tags.append("<b class='hl'>昨涨停→今跌停</b>")
    if x["c"] in dt1_set:
        tags.append("<b class='hl'>连续跌停</b>")
    if x.get("ltsz", 0) >= 1e10:
        tags.append("大市值")
    return "／".join(tags) if tags else "—"


tbl_dt_td = "".join(
    "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3:.2f}亿</td><td>{4:.0f}亿</td><td>{5}</td></tr>".format(
        x["c"], esc(x["n"]), esc(x["hybk"]), x["amount"] / 1e8, x["ltsz"] / 1e8, dt_tag(x))
    for x in sorted(DT_TD, key=lambda x: -x["amount"]))
tbl_rel = "".join(
    "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td class='{3}'>{4}</td></tr>".format(
        x["c"], esc(x["n"]), esc(x["h"]), "up" if x["pct"] >= 0 else "down", pct_txt(x["pct"]) + "%")
    for x in sorted(rel, key=lambda x: -(x["pct"] or -99)))

# ================= 表格片段 =================
SENTI_ROWS = [("涨停家数", "zt", True), ("炸板家数", "zb", False),
              ("封板率(%)", "seal", True), ("跌停家数", "dt", False)]


def _sp(v, isf):
    return "{:.1f}".format(v) if isf else "{:d}".format(v)


def _senti_cell(lab, k, good):
    a, b, c = days[0][k], days[1][k], days[2][k]
    isf = isinstance(c, float)
    d = c - b
    if d == 0:
        cls, txt = "mut", "0"
    else:
        cls = "up" if (d > 0) == good else "down"
        txt = ("+" if d > 0 else "−") + _sp(abs(d), isf)
    return "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td class='hl'>{3}</td><td class='{4}'>{5}</td></tr>".format(
        lab, _sp(a, isf), _sp(b, isf), _sp(c, isf), cls, txt)


tbl_senti = "".join(_senti_cell(*r) for r in SENTI_ROWS)
tbl_lad = "".join(
    "<tr><td>{0} 板</td><td>{1}</td><td class='hl'>{2}</td><td class='{3}'>{4}</td></tr>".format(
        i, lad1.get(i, 0), lad0.get(i, 0),
        "up" if lad0.get(i, 0) - lad1.get(i, 0) > 0 else ("down" if lad0.get(i, 0) - lad1.get(i, 0) < 0 else "mut"),
        "{:+d}".format(lad0.get(i, 0) - lad1.get(i, 0)))
    for i in range(lad_max, 0, -1))
tbl_hy = "".join(
    "<tr><td>{0}</td><td>{1}</td><td class='hl'>{2}</td><td class='{3}'>{4}</td></tr>".format(
        esc(h["name"]), h["y"], h["t"],
        "up" if h["t"] - h["y"] > 0 else ("down" if h["t"] - h["y"] < 0 else "mut"),
        ("+%d" % (h["t"] - h["y"])) if h["t"] - h["y"] > 0 else ("%d" % (h["t"] - h["y"]) if h["t"] - h["y"] < 0 else "0"))
    for h in hy_tbl)
tbl_ts = "".join("<tr><td>{0}</td><td>{1}</td><td class='hl'>{2}</td></tr>".format(k, ts1.get(k, 0), ts0.get(k, 0))
                 for k in TS_ORDER)
tbl_idx = "".join(
    "<tr><td>{0}</td><td class='{1}'>{2}</td><td class='{3}'>{4}</td><td>{5:,.0f}亿</td><td class='{6}'>{7}</td></tr>".format(
        esc(x["name"]), "up" if x["pct"] >= 0 else "down", pct_txt(x["pct"]) + "%",
        "up" if (x["prev_pct"] or 0) >= 0 else "down",
        (pct_txt(x["prev_pct"]) + "%") if x["prev_pct"] is not None else "—",
        x["amt"], "up" if (x["yoy"] or 0) >= 0 else "down",
        (pct_txt(x["yoy"], 1) + "%") if x["yoy"] is not None else "—")
    for x in ix)
tbl_style = "".join(
    "<tr><td>{0}</td><td class='{1}'>{2}</td><td class='{3}'>{4}</td><td>{5:,.0f}亿</td></tr>".format(
        esc(x["name"]), "up" if x["pct"] >= 0 else "down", pct_txt(x["pct"]) + "%",
        "up" if x["yoy"] >= 0 else "down", pct_txt(x["yoy"], 1) + "%", x["amt"])
    for x in STYLE_SORTED)
tbl_theme = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td>{2}</td><td style='text-align:left'>{3}</td></tr>".format(
        esc(nm), len(hit), sum(1 for r in hit if (r["lbc"] or 1) >= 2),
        "".join("<span class=tag>" + esc(r["name"]) + "(" + str(r["lbc"] or 1) + ")</span>"
                for r in sorted(hit, key=lambda x: (-(x["lbc"] or 0), -(x["fund"] or 0)))[:12]))
    for nm, hit in [("机器人 / 具身智能 / 精密传动", robot_sel), ("端侧 AI / AI 眼镜 / 模组", edge_sel),
                    ("算力 / PCB / 半导体", calc_sel), ("低空经济 / 飞行汽车", lowalt_sel),
                    ("医药 / 创新药 / 宠物药", med_sel), ("消费 / 家居 / 食品", cons_sel),
                    ("传媒 / 出版 / AI 内容", media_sel), ("军工 / 兵装", mil_sel)])
tbl_conc = "".join(
    "<tr><td>{0}</td><td class='hl'>{1}</td><td>{2}</td><td>{3:.0f}%</td><td>{4}</td></tr>".format(
        esc(b["name"]), b["limit_up_num"], b.get("continuous_plate_num", 0),
        b.get("continuous_plate_num", 0) / b["limit_up_num"] * 100 if b["limit_up_num"] else 0, esc(b.get("high") or "—"))
    for b in blocks[:12])

# ================= 占位符 =================
V = {}


def P(k, v):
    V["__" + k + "__"] = str(v)


P("GEN_AT", B.get("generated_at", ""))
P("D0", md(D0)); P("D1", md(D1)); P("D2", md(D2))
P("ZT", s0["zt"]); P("ZT_Y", s1["zt"]); P("ZT_D", "{:+d}".format(s0["zt"] - s1["zt"]))
P("ZB", s0["zb"]); P("ZB_Y", s1["zb"]); P("ZB_D", "{:+d}".format(s0["zb"] - s1["zb"]))
P("DT", s0["dt"]); P("DT_Y", s1["dt"]); P("DT_D", "{:+d}".format(s0["dt"] - s1["dt"]))
P("SEAL", "{:.1f}".format(s0["seal_rate"] * 100))
P("SEAL_Y", "{:.1f}".format(s1["seal_rate"] * 100))
P("SEAL_D", "{:+.1f}".format((s0["seal_rate"] - s1["seal_rate"]) * 100))
P("SEAL_D_ABS", "{:.1f}".format(abs((s0["seal_rate"] - s1["seal_rate"]) * 100)))
P("SEAL_FAIL", "{:.1f}".format((1 - s0["seal_rate"]) * 100))
P("SEAL_FAIL_Y", "{:.1f}".format((1 - s1["seal_rate"]) * 100))
P("TOUCH", TOUCH0); P("TOUCH_Y", TOUCH1); P("TOUCH_D", "{:+d}".format(TOUCH0 - TOUCH1))
P("TOUCH_D_ABS", "{:d}".format(abs(TOUCH0 - TOUCH1)))
P("TOUCH_PCT", "{:.0f}".format((TOUCH0 / TOUCH1 - 1) * 100))
P("DTOUCH", DTOUCH0); P("DTOUCH_Y", DTOUCH1); P("DTOUCH_D", "{:+d}".format(DTOUCH0 - DTOUCH1))
P("DTOUCH_OPEN", DTOUCH_OPEN)
P("DSEAL", "{:.1f}".format(DSEAL0)); P("DSEAL_Y", "{:.1f}".format(DSEAL1))
P("DSEAL_D", "{:+.1f}".format(DSEAL0 - DSEAL1))
P("ZTDT", "{:.1f}".format(s0["zt"] / s0["dt"] if s0["dt"] else 0))
P("ZTDT_Y", "{:.1f}".format(s1["zt"] / s1["dt"] if s1["dt"] else 0))
P("ZTDT_0", "{:.1f}".format(days[0]["zt"] / days[0]["dt"] if days[0]["dt"] else 0))
P("MAXB", maxb); P("MAXB_Y", maxb_y)
P("MAXB_NAMES", LB_HIGH_NAMES); P("MAXB_NAMES_Y", LB_HIGH_NAMES_Y)
P("LAD2", lad0.get(2, 0)); P("LAD2_Y", lad1.get(2, 0))
P("LAD2_D", "{:+d}".format(lad0.get(2, 0) - lad1.get(2, 0)))
P("LAD2_NAMES", LAD2_NAMES)
P("LAD3", lad0.get(3, 0)); P("LAD3_Y", lad1.get(3, 0))
P("LAD4", lad0.get(4, 0)); P("LAD4_Y", lad1.get(4, 0))
P("LADMAX_N", lad0.get(maxb, 0))
P("LB", s0["lianban"]); P("LB_Y", s1["lianban"])
P("SB", s0["shouban"]); P("SB_Y", s1["shouban"])
P("SB_PCT", "{:.0f}".format(s0["shouban"] / s0["zt"] * 100))
P("SB_PCT_Y", "{:.0f}".format(s1["shouban"] / s1["zt"] * 100))
P("AMT", "{:,.0f}".format(amt_today)); P("AMT_Y", "{:,.0f}".format(amt_prev))
P("AMT_D", "{:+,.0f}".format(amt_delta)); P("AMT_PCT", "{:+.1f}".format(amt_pct))
P("AMT_PCT_ABS", "{:.1f}".format(abs(amt_pct)))
P("N_SHRINK", N_SHRINK); P("IX_N", len(IX_A)); P("IX_ALL", len(ix))
P("N_UP", N_UP); P("N_DN", N_DN)
P("STYLE_TOP", esc(STYLE_SORTED[0]["name"])); P("STYLE_TOP_V", "{:+.1f}".format(STYLE_SORTED[0]["yoy"]))
P("STYLE_SHRINK_MAX", esc(STYLE_SORTED[-1]["name"])); P("STYLE_SHRINK_MAX_V", "{:+.1f}".format(STYLE_SORTED[-1]["yoy"]))
for nm, key in [("上证指数", "SH"), ("深证成指", "SZ"), ("创业板指", "CY"), ("科创50", "KC"),
                ("沪深300", "HS300"), ("中证500", "ZZ500"), ("中证1000", "ZZ1000"),
                ("国证2000", "GZ2000"), ("上证50", "SH50"), ("中小100", "ZS100"), ("北证50", "BZ50")]:
    _x = ixr.get(nm, {})
    P(key + "_PCT", pct_txt(_x.get("pct") or 0.0))
    P(key + "_YOY", pct_txt(_x.get("yoy") or 0.0, 1))
    P(key + "_AMT", "{:,.0f}".format(_x.get("amt") or 0))
P("AMT_UP_N", sum(1 for x in IX_A if x["yoy"] > 0))
P("HY_ALL_N", len([k for k, v in hy0.items() if v]))
P("HY_ZERO_N", HY_ZERO_N); P("HY_ZERO_NAMES", esc(HY_ZERO_NAMES)); P("HY_UP_N", HY_UP_N)
P("HY_QC", hy1.get("汽车零部", 0)); P("HY_QC0", hy0.get("汽车零部", 0))
P("HY_CB", hy1.get("出版", 0)); P("HY_CB0", hy0.get("出版", 0))
P("HY_ZYSB", hy1.get("专用设备", 0)); P("HY_ZYSB0", hy0.get("专用设备", 0))
P("HY_HKZB", hy1.get("航空装备", 0)); P("HY_HKZB0", hy0.get("航空装备", 0))
P("HY_SL", hy1.get("塑料", 0)); P("HY_SL0", hy0.get("塑料", 0))
P("HY_YJ", hy1.get("元件", 0)); P("HY_YJ0", hy0.get("元件", 0))
P("HY_JJ", hy1.get("家居用品", 0)); P("HY_JJ0", hy0.get("家居用品", 0))
P("HY_DL", hy1.get("电力", 0)); P("HY_DL0", hy0.get("电力", 0))
P("HY_TY", hy1.get("通用设备", 0)); P("HY_TY0", hy0.get("通用设备", 0))
P("HY_SN", hy1.get("水泥", 0)); P("HY_SN0", hy0.get("水泥", 0))
P("QC_N", QC_N); P("QC_LB", QC_LB); P("QC_R", "{:.0f}".format(QC_R))
P("QC_N_Y", QC_N_Y); P("QC_LB_Y", QC_LB_Y); P("QC_R_Y", "{:.0f}".format(QC_R_Y))
P("QC_DISP", QC_DISP); P("QC_DISP_LIST", esc("、".join(QC_DISP_LIST)))
P("DK_N", DK_N); P("DK_LB", DK_LB); P("DK_R", "{:.0f}".format(DK_R))
P("DK_N_Y", DK_N_Y); P("DK_LB_Y", DK_LB_Y); P("DK_R_Y", "{:.0f}".format(DK_R_Y))
P("DK_DISP", DK_DISP)
P("RB_N", RB_N); P("RB_LB", RB_LB); P("RB_R", "{:.0f}".format(RB_R))
P("RB_N_Y", RB_N_Y); P("RB_LB_Y", RB_LB_Y); P("RB_R_Y", "{:.0f}".format(RB_R_Y))
P("RB_DISP", RB_DISP); P("RX_N", RX_N); P("RX_LB", RX_LB); P("RX_R", "{:.0f}".format(RX_R))
P("RX_N_Y", RX_N_Y); P("RX_LB_Y", RX_LB_Y); P("RX_R_Y", "{:.0f}".format(RX_R_Y))
P("ROB_N", ROB_N); P("ROB_LB", ROB_LB); P("ROB_R", "{:.0f}".format(ROB_R))
P("ROB_N_SHARE", "{:.0f}".format(ROB_N / s0["zt"] * 100 if s0["zt"] else 0))
P("ROB_AMT", "{:.0f}".format(ROB_AMT)); P("ROB_FUND", "{:.1f}".format(ROB_FUND))
P("ROB_AMT_SHARE", "{:.0f}".format(ROB_AMT / amt_sum * 100 if amt_sum else 0))
P("ROB_FUND_SHARE", "{:.0f}".format(ROB_FUND / fund_sum * 100 if fund_sum else 0))
P("ROB_HY_N", ROB_HY_N); P("ROB_MAXB", ROB_MAXB); P("ROB_SB_N", ROB_NO_LB_N)
P("TBL_ROB", TBL_ROB)
P("UAV_N_Y", UAV_N_Y); P("UAV_LB_Y", UAV_LB_Y)
P("EV_N_Y", EV_N_Y); P("EV_LB_Y", EV_LB_Y)
P("NEW_N_Y", NEW_N_Y); P("NEW_LB_Y", NEW_LB_Y)
P("CONC_TOP5_TXT", CONC_TOP5_TXT); P("CONC_TOP7_MAXLB", CONC_TOP7_MAXLB)
P("CONC_TOP7_MAXR", "{:.0f}".format(CONC_MAX_R)); P("CONC_TOP7_MAXR_Y", "{:.0f}".format(CONC_MAX_R_Y))
P("TH_AUTO_N", len(lowalt_sel)); P("TH_AUTO_LB", sum(1 for r in lowalt_sel if (r["lbc"] or 1) >= 2))
P("TH_ROBOT_N", len(robot_sel)); P("TH_ROBOT_LB", sum(1 for r in robot_sel if (r["lbc"] or 1) >= 2))
P("TH_EDGE_N", len(edge_sel)); P("TH_EDGE_LB", sum(1 for r in edge_sel if (r["lbc"] or 1) >= 2))
P("TH_MIL_N", len(mil_sel)); P("TH_MIL_LB", sum(1 for r in mil_sel if (r["lbc"] or 1) >= 2))
P("TH_CALC_N", len(calc_sel)); P("TH_CALC_LB", sum(1 for r in calc_sel if (r["lbc"] or 1) >= 2))
P("TH_MEDIA_N", len(media_sel)); P("TH_MEDIA_LB", sum(1 for r in media_sel if (r["lbc"] or 1) >= 2))
P("TH_MED_N", len(med_sel)); P("TH_MED_LB", sum(1 for r in med_sel if (r["lbc"] or 1) >= 2))
P("TH_CONS_N", len(cons_sel)); P("TH_CONS_LB", sum(1 for r in cons_sel if (r["lbc"] or 1) >= 2))
P("ADV_RATE", "{:.1f}".format(adv_rate)); P("ADV_N", len(adv)); P("ADV_TOT", len(perf))
P("PERF_MEAN", pct_txt(mean(pcts))); P("PERF_MED", pct_txt(median(pcts)))
P("PERF_MAX", pct_txt(max(pcts))); P("PERF_MIN", pct_txt(min(pcts)))
P("PERF_TOP5", PERF_TOP5); P("PERF_BOT5", PERF_BOT5)
P("NEG", neg); P("NEG_PCT", "{:.0f}".format(neg / len(pcts) * 100)); P("NEG_LOW", neg_low)
P("GRP_S_N", n_s); P("GRP_S_R", "{:.1f}".format(r_s)); P("GRP_S_M", pct_txt(m_s)); P("GRP_S_NG", ng_s)
P("GRP_L_N", n_l); P("GRP_L_R", "{:.1f}".format(r_l)); P("GRP_L_M", pct_txt(m_l)); P("GRP_L_NG", ng_l)
P("GAP", "{:.2f}".format(GAP)); P("GAP_ABS", "{:.2f}".format(abs(GAP)))
P("GRP_S_M_Y", pct_txt(m_s_y)); P("GRP_L_M_Y", pct_txt(m_l_y)); P("GAP_Y", "{:.2f}".format(GAP_Y))
P("GAP_Y_ABS", "{:.2f}".format(abs(GAP_Y)))
P("AMT_SUM", "{:.0f}".format(amt_sum)); P("AMT_SUM_Y", "{:.0f}".format(amt_sum1))
P("AMT_SUM_PCT", "{:+.1f}".format((amt_sum / amt_sum1 - 1) * 100 if amt_sum1 else 0))
P("SHARE", "{:.1f}".format(share)); P("SHARE_Y", "{:.1f}".format(share1))
P("SHARE_D", "{:+.1f}".format(share - share1))
P("AMT_MED", "{:.2f}".format(amt_med)); P("AMT_MED_Y", "{:.2f}".format(amt_med1))
P("AMT_MED_PCT", "{:+.1f}".format((amt_med / amt_med1 - 1) * 100 if amt_med1 else 0))
P("AMT_MED_PCT_ABS", "{:.1f}".format(abs((amt_med / amt_med1 - 1) * 100 if amt_med1 else 0)))
P("FUND_SUM", "{:.1f}".format(fund_sum)); P("FUND_SUM_Y", "{:.1f}".format(fund_sum1))
P("FUND_SUM_PCT", "{:+.1f}".format((fund_sum / fund_sum1 - 1) * 100 if fund_sum1 else 0))
P("FUND_MED", "{:.2f}".format(fund_med)); P("FUND_MED_Y", "{:.2f}".format(fund_med1))
P("FUND_MED_PCT", "{:+.1f}".format((fund_med / fund_med1 - 1) * 100 if fund_med1 else 0))
P("ONEWORD", oneword); P("ONEWORD_Y", oneword1); P("HUANSHOU_Y", huanshou1)
P("HUANSHOU", huanshou); P("HUANSHOU_PCT", "{:.0f}".format(huanshou / s0["zt"] * 100))
P("FT0", esc(ft0["name"])); P("FT0_V", "{:.2f}".format(ft0_val)); P("FT0_PCT", "{:.1f}".format(ft0_pct))
P("FT0_RATIO", "{:.2f}".format(ft0_ratio)); P("FT0_AMT", "{:.2f}".format((ft0["amount"] or 0) / 1e8))
P("FT0_TURN", "{:.1f}".format(ft0["turnover"] or 0)); P("FT0_HY", esc(ft0["hybk"]))
P("DT_TC", DT_TC); P("DT_DIFF", abs(DT_DIFF)); P("DT_HY_N", DT_HY_N)
P("DT_AMT_TD", "{:.0f}".format(dt_amt_td)); P("DT_AMT_YD", "{:.0f}".format(dt_amt_yd))
P("DT_RATIO_TD", "{:.2f}".format(dt_amt_td / amt_sum if amt_sum else 0))
P("DT_RATIO_Y", "{:.2f}".format(dt_amt_yd / amt_sum1 if amt_sum1 else 0))
P("DT_BIG_N", DT_TD_BIG_N)
P("DT_PER_TD", "{:.1f}".format(dt_amt_td / len(DT_TD) if DT_TD else 0))
P("DT_PER_YD", "{:.1f}".format(dt_amt_yd / len(DT_YD) if DT_YD else 0))
_dt2 = sum(x.get("amount", 0) for x in sorted(DT_TD, key=lambda y: -y.get("amount", 0))[:2]) / 1e8
P("DT_TOP2_SHARE", "{:.0f}".format(_dt2 / dt_amt_td * 100 if dt_amt_td else 0))
P("DT_TOP1_NAME", esc(dt_top1["n"])); P("DT_TOP1_AMT", "{:.1f}".format(dt_top1["amount"] / 1e8))
P("DT_TOP1_MV", "{:.0f}".format(dt_top1["ltsz"] / 1e8)); P("DT_TOP1_HY", esc(dt_top1["hybk"]))
P("DT_FROM_ZT_N", len(dt_from_zt))
P("DT_FROM_ZT_NAMES", "、".join(esc(x["n"]) for x in dt_from_zt) or "无")
P("DT_CONT_N", len(dt_cont)); P("DT_CONT_NAMES", "、".join(esc(x["n"]) for x in dt_cont) or "无")
P("DT_HY_TOP", DT_HY_TOP_TXT)
P("REL_N", len(rel)); P("REL_MEAN", pct_txt(rel_mean)); P("REL_MED", pct_txt(rel_med))
P("REL_UP", rel_up); P("REL_LIM", rel_lim)
P("REL_TOP_NAME", esc(REL_TOP_NAME)); P("REL_TOP_PCT", REL_TOP_PCT)
P("INTER_N", INTER_N)
P("INTER_NAMES", "、".join(esc(r["name"]) for r in r0 if r["code"] in dt1_set) or "无")
P("PUB_BIG_DN", sum(1 for r in pub_rows if r["pct"] < 0 and r["mv"] >= 100))
P("PUB_N", PUB_N); P("PUB_DN", PUB_DN); P("PUB_DT", PUB_DT)
PUB4_AMT = sum(x["amount"] for x in DT_TD if x["hybk"] == "出版") / 1e8
P("PUB4_AMT", "{:.1f}".format(PUB4_AMT))
TOP5_SHARE = sum(x["amount"] for x in amt_top) / sum(amts) * 100
P("TOP5_SHARE", "{:.0f}".format(TOP5_SHARE))
P("FT0_SHARE", "{:.0f}".format((ft0["amount"] or 0) / sum(amts) * 100))
P("PUB_MEAN", pct_txt(PUB_MEAN)); P("PUB_MED", pct_txt(PUB_MED))
P("GRID_N", GRID_N); P("GRID_DN", GRID_DN); P("GRID_DT", GRID_DT); P("GRID_MEAN", pct_txt(GRID_MEAN))
P("TBL_GRID", TBL_GRID)
P("MT_N", MT_N); P("MT_DN", MT_DN); P("MT_MEAN", pct_txt(MT_MEAN))
P("ZB_N", s0["zb"]); P("ZB_POOL_N", len(zbpool)); P("ZB_POOL_N_Y", len(zbpool1))
P("ZB_SEALED_N", len(zb_sealed)); P("ZB_SEALED_N_Y", len(zb_sealed1))
P("ZB_OPEN_N", len(zb_open))
P("ZB_SEALED_NAMES", "、".join(esc(z["n"]) + " " + pct_txt(z["zdp"]) + "%" for z in zb_sealed) or "无")
P("ZB_SEALED_PCT", "{:.0f}".format(len(zb_sealed) / len(zbpool) * 100 if zbpool else 0))
P("ZB_MAX_NAME", esc(zb_big["n"]) if zb_big else "—")
P("ZB_MAX_AMT", "{:.2f}".format(zb_big["amount"] / 1e8) if zb_big else "—")
P("ZB_MAX_MV", "{:.0f}".format(zb_big["ltsz"] / 1e8) if zb_big else "—")
P("ZB_MAX_PCT", pct_txt(zb_big["zdp"]) if zb_big else "—")
P("ZB_MAX_HY", esc(zb_big["hybk"]) if zb_big else "—")
P("TS_EARLY_0", ts0.get("竞价/秒板", 0) + ts0.get("开盘半小时", 0))
P("TS_EARLY_Y", ts1.get("竞价/秒板", 0) + ts1.get("开盘半小时", 0))
P("TS_EARLY_0_PCT", "{:.0f}".format((ts0.get("竞价/秒板", 0) + ts0.get("开盘半小时", 0)) / s0["zt"] * 100))
P("TS_EARLY_Y_PCT", "{:.0f}".format((ts1.get("竞价/秒板", 0) + ts1.get("开盘半小时", 0)) / s1["zt"] * 100))
P("TS_PM0", ts0.get("午后盘中", 0)); P("TS_PM1", ts1.get("午后盘中", 0))
P("TS_PM0_PCT", "{:.0f}".format((ts0.get("午后盘中", 0) + ts0.get("尾盘", 0)) / s0["zt"] * 100))
P("TS_PM1_PCT", "{:.0f}".format((ts1.get("午后盘中", 0) + ts1.get("尾盘", 0)) / s1["zt"] * 100))
P("TS_KJ0", ts0.get("开盘半小时", 0)); P("TS_KJ1", ts1.get("开盘半小时", 0))
P("TS_JJ0", ts0.get("竞价/秒板", 0)); P("TS_JJ1", ts1.get("竞价/秒板", 0))
P("TBL_SENTI", tbl_senti); P("TBL_LAD", tbl_lad); P("TBL_LIANBAN", tbl_lianban)
P("TBL_HY", tbl_hy); P("TBL_TS", tbl_ts); P("TBL_THEME", tbl_theme); P("TBL_IDX", tbl_idx)
P("TBL_STYLE", tbl_style); P("TBL_REL", tbl_rel); P("TBL_DT_TD", tbl_dt_td)
P("TBL_FUND_TOP", tbl_fund_top); P("TBL_AMT_TOP", tbl_amt_top); P("TBL_ZB", tbl_zb)
P("TBL_CONC", tbl_conc); P("TBL_PUB", TBL_PUB)

# 北交所差额自检（涨停池）
em0 = set(x["c"] for x in B["dates"][D0]["em_ZT"]["pool"])
ths0 = set(x["code"] for x in (B["dates"][D0]["ths_zt"].get("info") or []))
diff = sorted(em0 - ths0)
assert all(c.startswith("92") for c in diff), f"北交所差额自检失败: {diff}"
if diff:
    V["__REL_DIFF_NOTE__"] = "东财涨停池 %d 只 vs 同花顺 %d 只，差额 %d 只为北交所（%s），已按沪深口径取 %d 只" % (
        len(em0), len(ths0), len(diff), "/".join(diff), len(ths0))
else:
    V["__REL_DIFF_NOTE__"] = "东财涨停池与同花顺家数一致（%d 只），差额 0" % len(em0)

P("JS_DAYS", json.dumps([d["d"] for d in days], ensure_ascii=False))
P("JS_ZT", json.dumps([d["zt"] for d in days]))
P("JS_ZB", json.dumps([d["zb"] for d in days]))
P("JS_DT", json.dumps([d["dt"] for d in days]))
P("JS_SEAL", json.dumps([round(d["seal"], 1) for d in days]))
P("JS_IX_NAME", json.dumps([x["name"] for x in sorted(ix, key=lambda y: y["pct"])], ensure_ascii=False))
P("JS_IX_PCT", json.dumps([round(x["pct"], 2) for x in sorted(ix, key=lambda y: y["pct"])]))
P("JS_AMT_NAME", json.dumps([x["name"] for x in STYLE_SORTED][::-1], ensure_ascii=False))
P("JS_AMT_YOY", json.dumps([round(x["yoy"], 1) for x in STYLE_SORTED][::-1]))
P("JS_LAD_NAME", json.dumps([str(i) + "板" for i in range(1, lad_max + 1)], ensure_ascii=False))
P("JS_LAD0", json.dumps([lad0.get(i, 0) for i in range(1, lad_max + 1)]))
P("JS_LAD1", json.dumps([lad1.get(i, 0) for i in range(1, lad_max + 1)]))
P("JS_CONC_NAME", json.dumps([b["name"] for b in concept_rows], ensure_ascii=False))
P("JS_CONC_N", json.dumps([b["limit_up_num"] for b in concept_rows]))
P("JS_CONC_LB", json.dumps([b.get("continuous_plate_num", 0) for b in concept_rows]))
P("JS_HY_NAME", json.dumps([h["name"] for h in hy_tbl][::-1], ensure_ascii=False))
P("JS_HY_T", json.dumps([h["t"] for h in hy_tbl][::-1]))
P("JS_HY_Y", json.dumps([h["y"] for h in hy_tbl][::-1]))
P("JS_PF_NAME", json.dumps([p["name"] for p in perf_sorted][::-1], ensure_ascii=False))
P("JS_PF_PCT", json.dumps([round(p["pct"], 2) for p in perf_sorted][::-1]))
P("JS_PF_H", len(perf_sorted) * 21 + 40)
P("JS_TS_NAME", json.dumps(TS_ORDER, ensure_ascii=False))
P("JS_TS_T", json.dumps([ts0.get(k, 0) for k in TS_ORDER]))
P("JS_TS_Y", json.dumps([ts1.get(k, 0) for k in TS_ORDER]))
_rs = sorted([x for x in rel if x["pct"] is not None], key=lambda x: x["pct"])
P("JS_REL_NAME", json.dumps([x["n"] for x in _rs], ensure_ascii=False))
P("JS_REL_PCT", json.dumps([round(x["pct"], 2) for x in _rs]))

HTML = open(os.path.join(ROOT, "scripts", "_report_tpl_20261020.html"), encoding="utf-8").read()
for k, v in V.items():
    HTML = HTML.replace(k, v)

fp = os.path.join(REP, f"涨停复盘对比-{D0}.html")
with open(fp, "w", encoding="utf-8") as f:
    f.write(HTML)
left = re.findall(r"__[A-Z_0-9]+__", HTML)
print("saved ->", fp, len(HTML) // 1024, "KB")
print("placeholder residue:", sorted(set(left)))
print("北交所差额自检: em=%d ths=%d diff=%s OK" % (len(em0), len(ths0), diff))
print("概念 top7:", [(b["name"], b["limit_up_num"], b.get("continuous_plate_num")) for b in b_top])
print("主题:", [(nm, len(hit), sum(1 for r in hit if (r["lbc"] or 1) >= 2))
                for nm, hit in [("robot", robot_sel), ("edge", edge_sel), ("lowalt", lowalt_sel),
                                ("calc", calc_sel), ("med", med_sel), ("cons", cons_sel),
                                ("media", media_sel), ("mil", mil_sel)]])
print("机器人簇: n=%d 连板=%d 成交%.1f亿(%.0f%%) 封单%.1f亿(%.0f%%) 离散度=%d 最高%d板"
      % (ROB_N, ROB_LB, ROB_AMT, ROB_AMT / amt_sum * 100, ROB_FUND, ROB_FUND / fund_sum * 100, ROB_HY_N, ROB_MAXB))
print("跌停行业:", DT_HY_TOP_TXT)
print("出版链:", PUB_N, "跌%d 跌停%d 均值%.2f%%" % (PUB_DN, PUB_DT, PUB_MEAN))
print("电网设备样本:", GRID_N, "跌%d 跌停%d 均值%.2f%%" % (GRID_DN, GRID_DT, GRID_MEAN))
print("关键:", dict(ZT=s0["zt"], TOUCH=TOUCH0, SEAL=round(s0["seal_rate"] * 100, 1), DT=s0["dt"],
                   AMT=round(amt_today), AMT_PCT=round(amt_pct, 1), SHARE=round(share, 1),
                   SHARE_Y=round(share1, 1), ADV=round(adv_rate, 1), GAP=round(GAP, 2),
                   DT_RATIO=round(dt_amt_td / amt_sum, 2), INTER=INTER_N,
                   ZB_SEALED=len(zb_sealed), ZB_POOL=len(zbpool), MAXB=(maxb, maxb_y)))
