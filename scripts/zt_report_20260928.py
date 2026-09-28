# -*- coding: utf-8 -*-
"""涨停复盘报告 20260928 vs 20260924（中秋假期后首个交易日 / 放量杀跌 / 算力硬件链跌停潮）

用法：python zt_report_20260928.py 20260928
输入：out/zt_stats_20260928.json、out/zt_review_20260928.json
     跌停池明细：东财 push2ex getTopicDTPool（sort=fund:asc，默认 sort=fbt 时 pool 为空）
     行业/概念涨跌幅榜：westock CLI `sector ranking`（申万二级 + 概念），已固化为下方 SECTOR_IND / CONCEPT_BOT 常量
输出：reports/涨停复盘对比-20260928.html
"""
import json, os, sys, collections, html, re, urllib.request
from statistics import mean, median

ROOT = os.environ.get("ZT_ROOT") or os.getcwd()
OUT = os.path.join(ROOT, "out")
REP = os.path.join(ROOT, "reports")
os.makedirs(REP, exist_ok=True)

S = json.load(open(os.path.join(OUT, f"zt_stats_{sys.argv[1]}.json"), encoding="utf-8"))
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


def seal(a, b):
    return a / (a + b) * 100 if (a + b) else 0.0


# ---- 三日情绪 ----
days = [
    {"d": md(D2) if D2 else "-", "zt": s1["zt_prev"], "zb": s1["zb_prev"], "dt": s1["dt_prev"]},
    {"d": md(D1), "zt": s1["zt"], "zb": s1["zb"], "dt": s1["dt"]},
    {"d": md(D0), "zt": s0["zt"], "zb": s0["zb"], "dt": s0["dt"]},
]
for x in days:
    x["seal"] = seal(x["zt"], x["zb"])
    x["touch"] = x["zt"] + x["zb"]

# ---- 指数 ----
IX_ORDER = [("上证指数", "sh000001"), ("深证成指", "sz399001"), ("创业板指", "sz399006"),
            ("科创50", "sh000688"), ("中小100", "sz399005"), ("沪深300", "sh000300"),
            ("中证500", "sh000905"), ("中证1000", "sh000852"), ("国证2000", "sz399303"),
            ("上证50", "sh000016"), ("北证50", "bj899050")]
idx_now = {v["name"]: v for v in B["indexes"].values()}
ix = []
for nm, sym in IX_ORDER:
    v = idx_now.get(nm)
    if v:
        ix.append({"name": nm, "pct": v["pct"], "amt": (v["amount_wan"] or 0) / 10000.0,
                   "price": v["price"]})
ixr = {x["name"]: x for x in ix}
PREV_IDX_PCT = {k: (v.get("prev_pct") or 0.0) for k, v in (S.get("idx_cmp") or {}).items()}

amt_today = ixr["上证指数"]["amt"] + ixr["深证成指"]["amt"]
tot = S.get("tot") or {}
amt_prev = tot.get("prev") or amt_today
amt_pct = (amt_today / amt_prev - 1) * 100 if amt_prev else 0.0
kc = ixr.get("科创50", {})
kc_prev_amt = (S.get("idx_cmp") or {}).get("科创50", {}).get("prev_amt") or kc.get("amt", 1)
kc_amt_pct = (kc.get("amt", 0) / kc_prev_amt - 1) * 100 if kc_prev_amt else 0.0
pct_delta = {k: v["pct"] - PREV_IDX_PCT.get(k, 0) for k, v in ixr.items()}

# 昨日全指数成交额（读上一交易日 review 文件，用于风格量能对比）
B1 = None
_p1 = os.path.join(OUT, f"zt_review_{D1}.json")
if os.path.exists(_p1):
    B1 = json.load(open(_p1, encoding="utf-8"))
idx_prev_amt = {}
if B1:
    for v in B1["indexes"].values():
        if isinstance(v, dict) and v.get("name"):
            idx_prev_amt[v["name"]] = (v.get("amount_wan") or 0) / 10000.0
            if v.get("pct") is not None:
                PREV_IDX_PCT.setdefault(v["name"], v["pct"])


def amt_yoy(nm):
    a0, a1 = ixr.get(nm, {}).get("amt", 0), idx_prev_amt.get(nm, 0)
    return (a0 / a1 - 1) * 100 if a1 else 0.0


# 开盘缺口 与 距当日最高回落（用实时快照 open/high/prev/price，对 index_hist 窗口滑动免疫）
def gap_pct(nm):
    v = idx_now.get(nm)
    return (v["open"] / v["prev"] - 1) * 100 if v and v.get("prev") else 0.0


def draw_pct(nm):
    v = idx_now.get(nm)
    return abs((v["price"] / v["high"] - 1) * 100) if v and v.get("high") else 0.0


# ---- 行业迁移 ----
hy0, hy1 = S["hy0"], S["hy1"]
hy_keys = sorted(set(list(hy0) + list(hy1)),
                 key=lambda k: (-(hy0.get(k, 0) * 2 + hy1.get(k, 0)), -hy0.get(k, 0), -hy1.get(k, 0), k))
hy_tbl = [{"name": k, "t": hy0.get(k, 0), "y": hy1.get(k, 0)} for k in hy_keys[:18]]
N_HY0, N_HY1 = len(hy0), len(hy1)
TOP_HY0 = max(hy0.values()) if hy0 else 0
TOP_HY1 = max(hy1.values()) if hy1 else 0
TOP_HY0_NAME = sorted([k for k, v in hy0.items() if v == TOP_HY0])[0]
TOP_HY1_NAME = sorted([k for k, v in hy1.items() if v == TOP_HY1])[0]

# ---- 连板梯队 ----
lad0 = {int(k): v for k, v in s0["ladder"].items()}
lad1 = {int(k): v for k, v in s1["ladder"].items()}
lad_max = max(max(lad0), max(lad1))
lad_series = lambda d, m: [d.get(i, 0) for i in range(1, m + 1)]

# ---- 封板时间 ----
TS_ORDER = ["竞价/秒板", "开盘半小时", "上午盘中", "午后盘中", "尾盘"]
ts0, ts1 = S["timeslot"]["today"], S["timeslot"]["yesterday"]

# ---- 晋级/溢价 ----
adv = [p for p in perf if p["again"]]
adv_rate = len(adv) / len(perf) * 100
pcts = [p["pct"] for p in perf if p["pct"] is not None]
neg = sum(1 for p in pcts if p < 0)
perf_sorted = sorted(perf, key=lambda x: -(x["pct"] if x["pct"] is not None else -999))
top3 = perf_sorted[:3]
bot3 = perf_sorted[-3:]
p_shou = [p for p in perf if (p["lbc"] or 1) == 1]
p_lian = [p for p in perf if (p["lbc"] or 1) >= 2]


def grp(rows):
    n = len(rows)
    if not n:
        return 0, 0.0, 0.0
    a = sum(1 for p in rows if p["again"])
    pp = [p["pct"] for p in rows if p["pct"] is not None]
    return n, a / n * 100, median(pp)


n_s, r_s, m_s = grp(p_shou)
n_l, r_l, m_l = grp(p_lian)
neg_low = sum(1 for p in pcts if p <= -5)

# ---- 成交额结构 ----
amts = [r["amount"] for r in r0 if r["amount"]]
amts1 = [r["amount"] for r in r1 if r["amount"]]
funds = [r["fund"] for r in r0 if r["fund"]]
funds1 = [r["fund"] for r in r1 if r["fund"]]
amt_sum, amt_sum1 = sum(amts) / 1e8, sum(amts1) / 1e8
fund_sum, fund_sum1 = sum(funds) / 1e8, sum(funds1) / 1e8
share = amt_sum / amt_today * 100
share1 = amt_sum1 / amt_prev * 100
amt_med = median(amts) / 1e8
amt_med1 = median(amts1) / 1e8
oneword = sum(1 for r in r0 if "一字" in r["limit_up_type"])
huanshou = sum(1 for r in r0 if "换手" in r["limit_up_type"])
oneword1 = sum(1 for r in r1 if "一字" in r["limit_up_type"])
huanshou1 = sum(1 for r in r1 if "换手" in r["limit_up_type"])
fund_top = sorted(r0, key=lambda x: -(x["fund"] or 0))[:3]
fund_top1 = sum((x["fund"] or 0) for x in fund_top) / 1e8
fund_ex = fund_sum - fund_top1
fund_top_name = fund_top[0]["name"]
fund_top_val = (fund_top[0]["fund"] or 0) / 1e8
fund_top_pct = fund_top_val / fund_sum * 100
fund_top_ratio = fund_top_val / ((fund_top[0]["amount"] or 1) / 1e8)
fund_top_lb = fund_top[0]["lbc"]
fund_top_reason = fund_top[0]["reason"]
fund_top1_share = len([x for x in fund_top if x["code"] == fund_top[0]["code"]])  # 占位，保持结构一致

# ---- 「华」字辈（name 维度，不走 reason 关键词）----
hua = sorted([r for r in r0 if "华" in r["name"]], key=lambda x: (-(x["lbc"] or 0), x["code"]))
hua_lb = [r for r in hua if (r["lbc"] or 1) >= 2]
lb_all = sorted([r for r in r0 if (r["lbc"] or 1) >= 2], key=lambda x: (-(x["lbc"] or 0), x["code"]))
hua_lb_pct = len(hua_lb) / len(lb_all) * 100 if lb_all else 0.0
hua1 = [r for r in r1 if "华" in r["name"]]
_hua1_lb = sum(1 for r in hua1 if (r["lbc"] or 1) >= 2)

# ---- 机器人/零部件集群 ----
ROBOT_KW = ["机器人", "具身", "人形", "减速器", "轴承", "丝杠", "执行器"]
robot = sorted([r for r in r0 if any(k in (r["reason"] or "") for k in ROBOT_KW)],
               key=lambda x: (-(x["lbc"] or 0), -(x["fund"] or 0)))
robot_n = len(robot)
robot_fund = sum((r["fund"] or 0) for r in robot) / 1e8

# ---- 汽车整车/商用车集群（本日唯一"申万行业收涨 + 涨停"的方向）----
AUTO_KW = ["尊界", "华为合作", "整车", "商用车", "A0车型", "玛莎拉蒂"]
auto = sorted([r for r in r0 if any(k in (r["reason"] or "") for k in AUTO_KW)],
              key=lambda x: (-(x["amount"] or 0)))
auto_n = len(auto)
auto_fund = sum((r["fund"] or 0) for r in auto) / 1e8
auto_amt = sum((r["amount"] or 0) for r in auto) / 1e8

# ---- 黄金/贵金属（用户关注度高的杀跌方向，单列为注） ----
gold = [r for r in r0 if (r["hybk"] or "") == "贵金属"]

# ---- 炸板池结构（东财 em_ZB）：区分「回封」与「未回封」----
_zbpool = (B["dates"][D0].get("em_ZB") or {}).get("pool") or []


def _is_limit(z):
    """按收盘涨幅判断是否收在涨停（创业板/科创板阈值 19.8%）"""
    thr = 19.8 if (z["c"].startswith("30") or z["c"].startswith("688")) else 9.8
    return (z.get("zdp") or 0) >= thr


zb_pool = sorted([z for z in _zbpool if not _is_limit(z)], key=lambda x: -(x.get("ltsz") or 0))
zb_sealed = sorted([z for z in _zbpool if _is_limit(z)], key=lambda x: -(x.get("ltsz") or 0))
zb_top = zb_pool[:4]
zb_today = [z for z in zb_pool if ((z.get("fbt") or 0) <= 113000)]
_zb_h = len(zb_pool) - len(zb_today)
_zb_early = len([z for z in zb_pool if ((z.get("fbt") or 0) <= 100000)])
# 炸板池最早/最晚首触
_zb_fbt = sorted(int(z.get("fbt") or 0) for z in zb_pool)
ZB_FBT_MIN = hhmm(_zb_fbt[0]) if _zb_fbt else "—"
ZB_FBT_MAX = hhmm(_zb_fbt[-1]) if _zb_fbt else "—"

# ---- 跌停池明细（东财 push2ex，必须 sort=fund:asc，默认 sort 返回空 pool） ----
DT_URL = ("https://push2ex.eastmoney.com/getTopicDTPool"
          "?ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&Pageindex=0&pagesize=300"
          "&sort=fund%3Aasc&date=" + D0)
_dt_pool = []
try:
    _op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    _raw = _op.open(DT_URL, timeout=25).read().decode("utf-8")
    _dt_pool = ((json.loads(_raw) or {}).get("data") or {}).get("pool") or []
except Exception as _e:
    print("warn: 跌停池明细抓取失败", _e)

DT_N = len(_dt_pool)
DT_AMT = sum(x.get("amount") or 0 for x in _dt_pool) / 1e8
# 电子/算力硬件链（关键词口径，非标准行业分类；口径已在报告中声明）
DT_CHAIN_HY = {"通信设备", "元件", "其他电子", "电子化学", "消费电子", "自动化设", "塑料", "金属新材"}
dt_chain = sorted([x for x in _dt_pool if (x.get("hybk") or "") in DT_CHAIN_HY],
                  key=lambda z: -(z.get("amount") or 0))
DT_CHAIN_N = len(dt_chain)
DT_CHAIN_PCT = DT_CHAIN_N / DT_N * 100 if DT_N else 0
DT_CHAIN_LB_N = len([x for x in dt_chain if (x.get("thyk") or "") == "通信设备"])  # 兼容字段
_dt_hy_cnt = collections.Counter(x.get("hybk") or "—" for x in _dt_pool)
dt_hy_top = _dt_hy_cnt.most_common(12)
_dt_big = sorted(_dt_pool, key=lambda z: -(z.get("ltsz") or 0))[:10]
_dt_chain_amt = sum(x.get("amount") or 0 for x in dt_chain) / 1e8


def _dt_fmt(rows):
    return "".join(
        "<tr><td class='hl'>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td class='down'>{4:+.2f}%</td>"
        "<td>{5}</td></tr>".format(
            esc(z.get("n")), z.get("c"), esc(z.get("hybk") or "—"),
            "{:.0f}亿".format((z.get("ltsz") or 0) / 1e8), z.get("zdp") or 0,
            "{:.2f}亿".format((z.get("amount") or 0) / 1e8))
        for z in rows)


tbl_dt_big = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td class='down'>{4:+.2f}%</td>"
    "<td>{5}</td><td>{6}</td></tr>".format(
        esc(z.get("n")), z.get("c"), esc(z.get("hybk") or "—"),
        "{:.0f}亿".format((z.get("ltsz") or 0) / 1e8), z.get("zdp") or 0,
        "{:.2f}亿".format((z.get("amount") or 0) / 1e8), hhmm(z.get("lbt") or 0))
    for z in _dt_big)

tbl_dt_chain = _dt_fmt(dt_chain)

# ---- 行业/概念涨跌幅榜（来源：westock CLI `sector ranking`，2026-09-28 收盘）----
SECTOR_IND = [["商用车", 3.34], ["养殖业", 2.03], ["非白酒", 1.73], ["小家电", 1.15], ["炼化及贸易", 0.99],
              ["电力", 0.18], ["国有大型银行Ⅱ", 0.13], ["煤炭开采", 0.12], ["食品加工", 0.11], ["中药Ⅱ", 0.09],
              ["饲料", 0.04], ["饮料乳品", 0.01], ["休闲食品", -0.02], ["白酒Ⅱ", -0.04], ["生物制品", -0.07],
              ["股份制银行Ⅱ", -0.11], ["铁路公路", -0.11], ["医药商业", -0.2], ["动物保健Ⅱ", -0.21], ["燃气Ⅱ", -0.24],
              ["航运港口", -0.26], ["渔业", -0.29], ["农商行Ⅱ", -0.33], ["油服工程", -0.34], ["医疗器械", -0.34],
              ["个护用品", -0.44], ["风电设备", -0.46], ["化学制药", -0.5], ["互联网电商", -0.53], ["白色家电", -0.54],
              ["城商行Ⅱ", -0.57], ["乘用车", -0.58], ["航空机场", -0.59], ["房地产服务", -0.59], ["物流", -0.62],
              ["航海装备Ⅱ", -0.67], ["轨交设备Ⅱ", -0.68], ["医疗服务", -0.72], ["多元金融", -1.12], ["影视院线", -1.17],
              ["房地产开发", -1.21], ["酒店餐饮", -1.22], ["普钢", -1.22], ["一般零售", -1.27], ["汽车服务", -1.27],
              ["基础建设", -1.29], ["造纸", -1.32], ["水泥", -1.35], ["电机Ⅱ", -1.39], ["厨卫电器", -1.41],
              ["特钢Ⅱ", -1.46], ["通信服务", -1.5], ["焦炭Ⅱ", -1.59], ["文娱用品", -1.59], ["房屋建设Ⅱ", -1.62],
              ["保险Ⅱ", -1.62], ["工程机械", -1.62], ["化学原料", -1.63], ["摩托车及其他", -1.64], ["服装家纺", -1.7],
              ["贸易Ⅱ", -1.8], ["旅游及景区", -1.87], ["证券Ⅱ", -1.89], ["汽车零部件", -1.9], ["黑色家电", -2.08],
              ["航空装备Ⅱ", -2.1], ["农化制品", -2.11], ["软件开发", -2.12], ["化学纤维", -2.12], ["环境治理", -2.17],
              ["饰品", -2.17], ["化妆品", -2.26], ["家居用品", -2.27], ["电池", -2.29], ["化学制品", -2.35],
              ["电网设备", -2.39], ["纺织制造", -2.4], ["电视广播Ⅱ", -2.46], ["包装印刷", -2.46], ["装修建材", -2.48],
              ["广告营销", -2.53], ["数字媒体", -2.59], ["光伏设备", -2.6], ["出版", -2.67], ["调味发酵品Ⅱ", -2.68],
              ["家电零部件Ⅱ", -2.7], ["冶钢原料", -2.74], ["综合Ⅱ", -2.76], ["计算机设备", -2.76], ["工业金属", -2.78],
              ["IT服务Ⅱ", -2.8], ["农产品加工", -2.88], ["游戏Ⅱ", -2.93], ["专业工程", -3.04], ["专业连锁Ⅱ", -3.05],
              ["地面兵装Ⅱ", -3.1], ["照明设备Ⅱ", -3.1], ["光学光电子", -3.1], ["航天装备Ⅱ", -3.15], ["专业服务", -3.2],
              ["装修装饰Ⅱ", -3.28], ["工程咨询服务Ⅱ", -3.34], ["专用设备", -3.71], ["通用设备", -3.74], ["环保设备Ⅱ", -3.75],
              ["教育", -3.91], ["种植业", -3.96], ["军工电子Ⅱ", -4.23], ["金属新材料", -4.35], ["能源金属", -4.43],
              ["半导体", -4.58], ["消费电子", -4.65], ["小金属", -4.66], ["其他电源设备Ⅱ", -4.75], ["自动化设备", -4.98],
              ["橡胶", -5.38], ["电子化学品Ⅱ", -5.49], ["塑料", -5.76], ["其他电子Ⅱ", -6.05], ["贵金属", -6.12],
              ["元件", -6.8], ["玻璃玻纤", -6.93], ["通信设备", -8.21], ["非金属材料Ⅱ", -8.34]]

CONCEPT_BOT = [["矢量网络分析仪VNA", -9.66], ["光芯片", -7.34], ["电子树脂", -7.17], ["陶瓷基板", -6.89],
               ["电子布", -6.84], ["MLCC", -6.72], ["光通信", -6.65], ["共封装光模块(CPO)", -6.63],
               ["F5G", -6.54], ["光纤概念", -6.53], ["谷歌概念", -6.37], ["被动元件概念", -6.27]]

SEC_N = len(SECTOR_IND)
SEC_UP = len([x for x in SECTOR_IND if x[1] > 0])
SEC_DN = len([x for x in SECTOR_IND if x[1] < 0])
SEC_FLAT = SEC_N - SEC_UP - SEC_DN
# 榜单展示：涨幅前 8 + 跌幅前 12
SEC_SHOW = SECTOR_IND[:8] + SECTOR_IND[-12:]

tbl_sec = "".join(
    "<tr><td>{0}</td><td class='{1}'>{2:+.2f}%</td><td>{3}</td></tr>".format(
        esc(nm), "up" if v >= 0 else "down", v,
        "↑" if v >= 0 else "↓") for nm, v in SEC_SHOW)

tbl_con = "".join(
    "<tr><td>{0}</td><td class='down'>{1:+.2f}%</td></tr>".format(esc(nm), v) for nm, v in CONCEPT_BOT)

# ---- 主线归因（多标签，家数之和 > 总数）----
THEMES = [
    ("机器人/精密零部件", ["机器人", "具身", "人形", "减速器", "轴承", "丝杠", "执行器", "3D打印"]),
    ("汽车整车/商用车", ["整车", "商用车", "尊界", "华为合作", "A0车型", "玛莎拉蒂", "变速器", "热管理"]),
    ("AI算力/电子硬件", ["算力", "PCB", "服务器", "光通信", "光模块", "数据中心", "交换机", "液冷",
                         "端侧AI", "存储", "半导体", "消费电子", "芯片", "光刻", "先进封装", "显示",
                         "覆铜板", "HDI", "MiniLED", "AIDC", "MLCC", "离子注入", "铜箔", "LED",
                         "测试", "仪器", "测量", "光电", "TGV", "微棱镜"]),
    ("海峡两岸/福建", ["海峡两岸", "福建", "平潭", "厦门", "漳州"]),
    ("出版传媒/文化整合", ["出版", "传媒", "图书", "文化", "影视", "数字内容", "短剧", "广告", "营销",
                           "数字教育", "游戏", "AI电影", "院线"]),
    ("医药医疗", ["创新药", "医药", "医疗", "中药", "体外诊断", "CRO", "脑机", "细胞", "抗感染",
                  "肿瘤", "口腔", "康复", "阿尔茨海默", "基因", "医疗器械", "精麻", "抗生素",
                  "流感", "合成生物", "腹膜透析", "药材", "脱敏", "过敏", "食欲素", "药"]),
    ("国资/股权变更", ["国资", "央企", "国企", "控制权", "股权转让", "股份转让", "控股", "资产重组",
                       "复牌", "借壳", "入主", "划转", "拟收购", "收购", "重组"]),
    ("消费零售/农业", ["零售", "百货", "家居", "家具", "服装", "家纺", "食品", "黄酒", "白酒", "珠宝",
                       "乳品", "纺织", "羽绒", "养殖", "猪", "粮油", "皮鞋", "皮革", "卫浴", "智能马桶",
                       "按摩椅", "大消费", "功能糖", "种业", "玉米", "转基因", "夹克", "小家电", "菜籽油",
                       "跨境电商", "矿泉水", "饮用水", "黄酒", "农"]),
    ("化工材料/资源", ["化学", "新材料", "锆", "锶", "玻纤", "聚酯", "薄膜", "染料", "铝", "锂", "钢丝绳",
                       "贵金属", "铜箔", "陶瓷", "钼", "锑", "锡", "稀贵", "危废", "煤炭", "铬", "水泥",
                       "焦炭", "磷化铟", "TDI", "SOFC", "四氯化硅", "硅烷", "电子化学品", "氯代吡啶"]),
    ("地产链", ["房地产", "城市更新", "物业", "房产经纪", "旧改", "装修", "深圳旧改"]),
    ("电力电网/能源", ["电力", "电网", "热电", "电缆", "风电", "光伏", "储能", "输电", "天然气", "LNG",
                       "燃气", "核电", "燃气轮机", "变压器", "清洁能源", "绿色电力", "智慧运维"]),
    ("低空经济/商业航天", ["低空", "商业航天", "无人机", "车路云", "卫星", "电磁", "索具", "深海系泊"]),
    ("网络安全/信创", ["网络安全", "数据安全", "AI安全", "车联网", "数字风洞", "网络靶场", "信创"]),
    ("基建/交运", ["基建", "基础建设", "路桥", "港口", "物流", "铁路", "扣件", "航运"]),
]
theme_cnt = []
for nm, kws in THEMES:
    hit = [r for r in r0 if any(k in (r["reason"] or "") for k in kws)]
    theme_cnt.append({"name": nm, "n": len(hit),
                      "stocks": [r["name"] + "(" + str(r["lbc"] or 1) + "板)" for r in
                                 sorted(hit, key=lambda x: (-(x["lbc"] or 0), -(x["amount"] or 0)))][:8]})
theme_cnt.sort(key=lambda x: (-x["n"], x["name"]))
med_theme = theme_cnt[0]

maxb = max(lad0) if lad0 else 0
maxb_y = max(lad1) if lad1 else 0

# ================= 表格片段 =================
tbl_lad = "".join(
    "<tr><td>{0} 板</td><td>{1}</td><td class='hl'>{2}</td><td class='{3}'>{4:+d}</td></tr>".format(
        i, lad1.get(i, 0), lad0.get(i, 0),
        "up" if lad0.get(i, 0) - lad1.get(i, 0) > 0 else ("down" if lad0.get(i, 0) - lad1.get(i, 0) < 0 else "mut"),
        lad0.get(i, 0) - lad1.get(i, 0))
    for i in range(lad_max, 0, -1))

tbl_lianban = "".join(
    "<tr><td>{0}板</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td><td>{6:.1f}%</td>"
    "<td>{7}</td><td style='text-align:left;color:#4b5563'>{8}</td></tr>".format(
        r["lbc"], r["code"], esc(r["name"]), (r["fbt"][:5] if r["fbt"] else "—"),
        "{:.2f}亿".format((r["fund"] or 0) / 1e8), "{:.2f}亿".format((r["amount"] or 0) / 1e8),
        (r["turnover"] or 0), esc(r["hybk"]), esc(r["reason"]))
    for r in lb_all)

tbl_hua = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td></tr>".format(
        esc(r["name"]), r["code"], r["lbc"], esc(r["hybk"]),
        "{:.2f}亿".format((r["amount"] or 0) / 1e8),
        ("是" if any(k in (r["reason"] or "") for k in ["国资", "央企", "国企", "重组", "收购", "控股", "变更", "划转"]) else "—"))
    for r in hua)

tbl_robot = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td>"
    "<td>{5}</td><td style='text-align:left;color:#4b5563'>{6}</td></tr>".format(
        esc(r["name"]), r["code"], (r["lbc"] if (r["lbc"] or 0) >= 2 else "首板"), esc(r["hybk"]),
        "{:.2f}亿".format((r["fund"] or 0) / 1e8), "{:.2f}亿".format((r["amount"] or 0) / 1e8),
        esc(r["reason"]))
    for r in robot)

tbl_auto = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td>"
    "<td>{5}</td><td style='text-align:left;color:#4b5563'>{6}</td></tr>".format(
        esc(r["name"]), r["code"], (r["lbc"] if (r["lbc"] or 0) >= 2 else "首板"), esc(r["hybk"]),
        "{:.2f}亿".format((r["fund"] or 0) / 1e8), "{:.2f}亿".format((r["amount"] or 0) / 1e8),
        esc(r["reason"]))
    for r in auto)

tbl_hy = "".join(
    "<tr><td>{0}</td><td>{1}</td><td class='hl'>{2}</td><td class='{3}'>{4:+d}</td>"
    "<td style='text-align:left;color:#6b7280'>{5}</td></tr>".format(
        esc(h["name"]), h["y"], h["t"],
        "up" if h["t"] - h["y"] > 0 else ("down" if h["t"] - h["y"] < 0 else "mut"),
        h["t"] - h["y"], "流入" if h["t"] - h["y"] > 0 else ("流出" if h["t"] - h["y"] < 0 else "持平"))
    for h in hy_tbl)

tbl_ts = "".join(
    "<tr><td>{0}</td><td>{1}</td><td class='hl'>{2}</td></tr>".format(k, ts1.get(k, 0), ts0.get(k, 0))
    for k in TS_ORDER)

tbl_theme = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td style='text-align:left'>{2}</td></tr>".format(
        esc(t["name"]), t["n"], "".join("<span class=tag>" + esc(s) + "</span>" for s in t["stocks"]))
    for t in theme_cnt if t["n"] > 0)

tbl_zb = "".join(
    "<tr><td class='hl'>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td></tr>".format(
        esc(z["n"]), z["c"], esc(z.get("hybk", "")), "{:.0f}亿".format((z.get("ltsz") or 0) / 1e8),
        "{:+.2f}%".format(z.get("zdp") or 0), hhmm(z.get("fbt") or 0))
    for z in zb_top)

tbl_idx = "".join(
    "<tr><td>{0}</td><td class='{1}'>{2:+.2f}%</td><td class='{3}'>{4}</td><td>{5}</td></tr>".format(
        esc(x["name"]), "up" if x["pct"] >= 0 else "down", x["pct"],
        "up" if PREV_IDX_PCT.get(x["name"], 0) >= 0 else "down",
        ("{:+.2f}%".format(PREV_IDX_PCT[x["name"]]) if x["name"] in PREV_IDX_PCT else "—"),
        "{:,.0f}亿".format(x["amt"]))
    for x in ix)

tbl_sty = "".join(
    "<tr><td>{0}</td><td class='hl'>{1}</td><td>{2}</td><td class='{3}'>{4}</td></tr>".format(
        esc(nm), "{:+.2f}".format(ixr.get(nm, {}).get("pct", 0.0)),
        ("{:+.2f}".format(PREV_IDX_PCT[nm]) if nm in PREV_IDX_PCT else "—"),
        "up" if amt_yoy(nm) >= 0 else "down", "{:+.1f}%".format(amt_yoy(nm)))
    for nm, _s in [("科创50", "sh000688"), ("沪深300", "sh000300"), ("上证50", "sh000016"),
                   ("中小100", "sz399005"), ("中证500", "sh000905"), ("创业板指", "sz399006"),
                   ("中证1000", "sh000852"), ("国证2000", "sz399303"), ("北证50", "bj899050")])

tbl_dthy = "".join(
    "<tr><td>{0}</td><td class='hl'>{1}</td><td>{2}</td></tr>".format(
        esc(k), v, "算力硬件链" if k in DT_CHAIN_HY else "—") for k, v in dt_hy_top)


def fmtv(v):
    return "{:.1f}".format(v) if isinstance(v, float) else str(v)


def fmtd(v):
    return ("{:+.1f}" if isinstance(v, float) else "{:+d}").format(v)


tbl_senti = "".join(
    "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td class='hl'>{3}</td><td class='{4}'>{5}</td></tr>".format(
        lab, fmtv(days[0][k]), fmtv(days[1][k]), fmtv(days[2][k]),
        "up" if days[2][k] - days[1][k] > 0 else ("down" if days[2][k] - days[1][k] < 0 else "mut"),
        fmtd(days[2][k] - days[1][k]))
    for lab, k in [("涨停家数", "zt"), ("炸板家数", "zb"), ("封板率(%)", "seal"), ("跌停家数", "dt"),
                   ("触及涨停家数", "touch")])

perf_top = "、".join("{}{:+.1f}%".format(esc(p["name"]), p["pct"]) for p in top3)
perf_bot = "、".join("{}{:+.1f}%".format(esc(p["name"]), p["pct"]) for p in bot3)

# ================= 占位符 =================
V = {}


def P(k, v):
    V["__" + k + "__"] = str(v)


P("GEN_AT", B["generated_at"])
P("ZT", s0["zt"]); P("ZT_Y", s1["zt"]); P("ZT_D", "{:+d}".format(s0["zt"] - s1["zt"]))
P("ZT_PCT_D", "{:+.1f}".format((s0["zt"] / s1["zt"] - 1) * 100))
P("ZB", s0["zb"]); P("ZB_Y", s1["zb"]); P("ZB_D", "{:+d}".format(s0["zb"] - s1["zb"]))
P("ZB_PCT_D", "{:+.0f}".format((s0["zb"] / s1["zb"] - 1) * 100))
P("DT", s0["dt"]); P("DT_Y", s1["dt"]); P("DT_D", "{:+d}".format(s0["dt"] - s1["dt"]))
P("DT_MULT", "{:.1f}".format(s0["dt"] / s1["dt"] if s1["dt"] else 0))
P("SEAL", "{:.1f}".format(s0["seal_rate"] * 100))
P("SEAL_Y", "{:.1f}".format(s1["seal_rate"] * 100))
P("SEAL_D", "{:+.1f}".format((s0["seal_rate"] - s1["seal_rate"]) * 100))
P("TOUCH", s0["zt"] + s0["zb"]); P("TOUCH_Y", s1["zt"] + s1["zb"])
P("TOUCH_D", "{:+d}".format((s0["zt"] + s0["zb"]) - (s1["zt"] + s1["zb"])))
P("TOUCH_PCT_D", "{:+.0f}".format(((s0["zt"] + s0["zb"]) / (s1["zt"] + s1["zb"]) - 1) * 100))
P("ZTDT", "{:.2f}".format(s0["zt"] / s0["dt"] if s0["dt"] else 0))
P("ZTDT_Y", "{:.1f}".format(s1["zt"] / s1["dt"] if s1["dt"] else 0))
P("ZTDT_0", ("{:.1f}".format(days[0]["zt"] / days[0]["dt"]) if days[0]["dt"] else "—（跌停0家）"))
P("DT_OPEN", s0["limit_down_count"]["today"]["open_num"])
P("DT_TOUCH", s0["limit_down_count"]["today"]["history_num"])
P("DT_TOUCH_Y", s0["limit_down_count"]["yesterday"]["history_num"])
P("DT_OPEN_Y", s0["limit_down_count"]["yesterday"]["open_num"])
P("DT_LOCK", "{:.0f}".format(s0["limit_down_count"]["today"]["rate"] * 100))
P("DT_LOCK_Y", "{:.0f}".format(s1["limit_down_count"]["today"]["rate"] * 100))
P("MAXB", maxb); P("MAXB_Y", maxb_y)
P("LB", s0["lianban"]); P("LB_Y", s1["lianban"])
P("SB", s0["shouban"]); P("SB_Y", s1["shouban"])
P("SB_PCT", "{:.0f}".format(s0["shouban"] / s0["zt"] * 100))
P("SB_PCT_Y", "{:.0f}".format(s1["shouban"] / s1["zt"] * 100))
P("AMT", "{:,.0f}".format(amt_today)); P("AMT_Y", "{:,.0f}".format(amt_prev))
P("AMT_D", "{:+,.0f}".format(amt_today - amt_prev)); P("AMT_PCT", "{:+.1f}".format(amt_pct))
P("KC_PCT", "{:+.2f}".format(kc.get("pct", 0)))
P("KC_AMT", "{:,.0f}".format(kc.get("amt", 0)))
P("KC_AMT_PCT", "{:+.1f}".format(kc_amt_pct))
P("KC_AMT_PREV", "{:,.0f}".format(kc_prev_amt))
P("KC_GAP", "{:+.2f}".format(gap_pct("科创50")))
P("KC_DRAW", "{:.2f}".format(draw_pct("科创50")))
for _nm, _k in [("上证指数", "SH"), ("深证成指", "SZ"), ("创业板指", "CY"), ("上证50", "SZ50")]:
    P(_k + "_GAP", "{:+.2f}".format(gap_pct(_nm)))
    P(_k + "_DRAW", "{:.2f}".format(draw_pct(_nm)))
    P(_k + "_PCT2", "{:+.2f}".format(ixr.get(_nm, {}).get("pct", 0)))
P("SZ50_AMT_PCT", "{:+.1f}".format(amt_yoy("上证50")))
P("HS300_AMT_PCT", "{:+.1f}".format(amt_yoy("沪深300")))
P("ZZ500_AMT_PCT", "{:+.1f}".format(amt_yoy("中证500")))
P("ZZ1000_AMT_PCT", "{:+.1f}".format(amt_yoy("中证1000")))
P("GZ2000_AMT_PCT", "{:+.1f}".format(amt_yoy("国证2000")))
P("CYB_AMT_PCT", "{:+.1f}".format(amt_yoy("创业板指")))
P("ZXX_AMT_PCT", "{:+.1f}".format(amt_yoy("中小100")))
P("BJ50_AMT_PCT", "{:+.1f}".format(amt_yoy("北证50")))
P("ADV_RATE", "{:.1f}".format(adv_rate)); P("ADV_N", len(adv)); P("ADV_TOT", len(perf))
P("PERF_MEAN", "{:+.2f}".format(mean(pcts))); P("PERF_MED", "{:+.2f}".format(median(pcts)))
P("PERF_MAX", "{:+.2f}".format(max(pcts))); P("PERF_MIN", "{:+.2f}".format(min(pcts)))
P("PERF_MAX_NAME", esc(perf_sorted[0]["name"]))
P("PERF_MIN_NAME", esc(perf_sorted[-1]["name"]))
P("PERF_MIN_LB", perf_sorted[-1]["lbc"])
P("PERF_TOP3", perf_top); P("PERF_BOT3", perf_bot)
P("NEG", neg); P("NEG_PCT", "{:.1f}".format(neg / len(pcts) * 100))
P("NEG_LOW", neg_low)
P("AMT_SUM", "{:.0f}".format(amt_sum)); P("SHARE", "{:.1f}".format(share))
P("AMT_SUM_Y", "{:.0f}".format(amt_sum1)); P("SHARE_Y", "{:.1f}".format(share1))
P("AMT_SUM_PCT_D", "{:+.0f}".format((amt_sum / amt_sum1 - 1) * 100))
P("AMT_MED", "{:.2f}".format(amt_med)); P("AMT_MED_Y", "{:.2f}".format(amt_med1))
P("AMT_MED_PCT_D", "{:+.0f}".format((amt_med / amt_med1 - 1) * 100))
P("FUND_SUM", "{:.1f}".format(fund_sum)); P("FUND_SUM_Y", "{:.1f}".format(fund_sum1))
P("FUND_MED", "{:.2f}".format(median(funds) / 1e8))
P("FUND_MED_Y", "{:.2f}".format(median(funds1) / 1e8))
P("FUND_AVG", "{:.2f}".format(fund_sum / s0["zt"]))
P("FUND_AVG_Y", "{:.2f}".format(fund_sum1 / s1["zt"]))
P("ONEWORD", oneword); P("ONEWORD_Y", oneword1); P("ONEWORD_PCT", "{:.1f}".format(oneword / s0["zt"] * 100))
P("HUANSHOU", huanshou); P("HUANSHOU_Y", huanshou1)
P("HUANSHOU_PCT", "{:.0f}".format(huanshou / s0["zt"] * 100))
P("FUND_TOP_NAME", esc(fund_top_name))
P("FUND_TOP_VAL", "{:.1f}".format(fund_top_val))
P("FUND_TOP_PCT", "{:.1f}".format(fund_top_pct))
P("FUND_TOP_RATIO", "{:.0f}".format(fund_top_ratio))
P("FUND_TOP_AMT", "{:.2f}".format((fund_top[0]["amount"] or 0) / 1e8))
P("FUND_TOP_LB", fund_top_lb)
P("FUND_TOP_REASON", esc(fund_top_reason))
P("FUND_TOP3_VAL", "{:.1f}".format(fund_top1))
fund_top_y = sorted(r1, key=lambda x: -(x["fund"] or 0))[:1]
P("FUND_TOP_Y_NAME", esc(fund_top_y[0]["name"]) if fund_top_y else "—")
P("FUND_TOP_Y_VAL", "{:.1f}".format((fund_top_y[0]["fund"] or 0) / 1e8) if fund_top_y else "0")
P("FUND_TOP_Y_AMT", "{:.2f}".format((fund_top_y[0]["amount"] or 0) / 1e8) if fund_top_y else "0")
P("FUND_EX", "{:.1f}".format(fund_ex))
P("LB_TOP1", esc(lb_all[0]["name"])); P("LB_TOP1_REASON", esc(lb_all[0]["reason"]))
P("LB_TOP1_FUND", "{:.2f}".format((lb_all[0]["fund"] or 0) / 1e8))
P("LB_TOP1_AMT", "{:.2f}".format((lb_all[0]["amount"] or 0) / 1e8))
P("LB_TOP2", esc(lb_all[1]["name"])); P("LB_TOP2_LB", lb_all[1]["lbc"])
P("LB_TOP3", esc(lb_all[2]["name"])); P("LB_TOP3_LB", lb_all[2]["lbc"])
P("LB_LIST", "、".join("{0}（{1}板）".format(esc(r["name"]), r["lbc"]) for r in lb_all))
P("HUA_N", len(hua)); P("HUA_PCT", "{:.1f}".format(len(hua) / s0["zt"] * 100))
P("HUA_N_Y", len(hua1))
P("HUA_LB_N", len(hua_lb)); P("HUA_LB_PCT", "{:.0f}".format(hua_lb_pct))
P("HUA_LB_RATIO", "{:.0f}".format(len(hua_lb) / len(hua) * 100) if hua else "0")
P("HUA_LB_RATIO_Y", "{:.0f}".format(_hua1_lb / len(hua1) * 100) if hua1 else "0")
P("HUA_LIST", "、".join(r["name"] for r in hua))
P("INSTR_N", len([r for r in r0 if any(k in (r["reason"] or "") for k in ["仪器", "测量", "质谱", "网络分析", "VNA"])]))
P("STR_N", len([r for r in r0 if any(k in (r["reason"] or "") for k in ["海峡两岸", "福建", "平潭", "厦门", "漳州"])]))
P("ROBOT_N", robot_n); P("ROBOT_FUND", "{:.2f}".format(robot_fund))
P("ROBOT_LB_N", sum(1 for r in robot if (r["lbc"] or 0) >= 2))
P("ROBOT_LIST", "、".join(r["name"] for r in robot))
P("AUTO_N", auto_n); P("AUTO_FUND", "{:.2f}".format(auto_fund)); P("AUTO_AMT", "{:.1f}".format(auto_amt))
P("AUTO_LIST", "、".join(r["name"] for r in auto))
P("GOLD_N", len(gold))
P("ZB_POOL_N", len(_zbpool))
P("ZB_SEALED_N", len(zb_sealed))
P("ZB_SEALED_NAME", esc(zb_sealed[0]["n"]) if zb_sealed else "—")
P("ZB_TOP1", esc(zb_top[0]["n"])); P("ZB_TOP1_V", "{:.0f}".format((zb_top[0]["ltsz"] or 0) / 1e8))
P("ZB_TOP1_AMT", "{:.2f}".format((zb_top[0].get("amount") or 0) / 1e8))
P("ZB_TOP2", esc(zb_top[1]["n"])); P("ZB_TOP2_V", "{:.0f}".format((zb_top[1]["ltsz"] or 0) / 1e8))
P("ZB_TOP3", esc(zb_top[2]["n"])); P("ZB_TOP3_V", "{:.0f}".format((zb_top[2]["ltsz"] or 0) / 1e8))
P("ZB_TOP4", esc(zb_top[3]["n"])); P("ZB_TOP4_V", "{:.0f}".format((zb_top[3]["ltsz"] or 0) / 1e8))
P("ZB_FBT_MIN", ZB_FBT_MIN); P("ZB_FBT_MAX", ZB_FBT_MAX)
P("MEDTHEME", esc(med_theme["name"])); P("MEDTHEME_N", med_theme["n"])
P("MEDTHEME_PCT", "{:.1f}".format(med_theme["n"] / s0["zt"] * 100))
P("ADV_S_N", n_s); P("ADV_S_RATE", "{:.1f}".format(r_s)); P("ADV_S_MED", "{:+.2f}".format(m_s))
P("ADV_L_N", n_l); P("ADV_L_RATE", "{:.1f}".format(r_l)); P("ADV_L_MED", "{:+.2f}".format(m_l))
P("ADV_GAP", "{:.2f}".format(m_l - m_s))
P("TH_AI_N", next(t["n"] for t in theme_cnt if t["name"].startswith("AI算力")))
P("TH_AUTO_N", next(t["n"] for t in theme_cnt if t["name"].startswith("汽车整车")))
P("TH_CB_N", next(t["n"] for t in theme_cnt if t["name"].startswith("出版")))
P("TH_STR_N", next(t["n"] for t in theme_cnt if t["name"].startswith("海峡两岸")))
P("TH_ROBOT_N", next(t["n"] for t in theme_cnt if t["name"].startswith("机器人")))
P("TH_GZ_N", next(t["n"] for t in theme_cnt if t["name"].startswith("国资")))
P("TH_MED_N", next(t["n"] for t in theme_cnt if t["name"].startswith("医药")))
P("TH_NET_N", next(t["n"] for t in theme_cnt if t["name"].startswith("网络安全")))
P("ZT_D2", days[0]["zt"]); P("SEAL_D2", "{:.1f}".format(days[0]["seal"]))
P("SHARE_HY0", "{:.1f}".format(TOP_HY0 / s0["zt"] * 100))
P("SHARE_HY1", "{:.1f}".format(TOP_HY1 / s1["zt"] * 100))
P("N_HY0", N_HY0); P("N_HY1", N_HY1)
P("TOP_HY0", esc(TOP_HY0_NAME)); P("TOP_HY1", esc(TOP_HY1_NAME))
P("TOP_HY0_N", TOP_HY0); P("TOP_HY1_N", TOP_HY1)
_amt_top = sorted(r0, key=lambda x: -(x["amount"] or 0))[:3]
P("AMT_TOP1", esc(_amt_top[0]["name"])); P("AMT_TOP1_V", "{:.1f}".format((_amt_top[0]["amount"] or 0) / 1e8))
P("AMT_TOP2", esc(_amt_top[1]["name"])); P("AMT_TOP2_V", "{:.1f}".format((_amt_top[1]["amount"] or 0) / 1e8))
P("AMT_TOP3", esc(_amt_top[2]["name"])); P("AMT_TOP3_V", "{:.1f}".format((_amt_top[2]["amount"] or 0) / 1e8))
for _b in (2, 3, 4, 5, 6):
    P("LAD{}_T".format(_b), lad0.get(_b, 0)); P("LAD{}_Y".format(_b), lad1.get(_b, 0))
P("LAD3P_Y", sum(lad1.get(i, 0) for i in (3, 4, 5, 6)))
P("LAD3P_T", sum(lad0.get(i, 0) for i in (3, 4, 5, 6)))
P("HILB_Y", sum(lad1.get(i, 0) for i in (4, 5, 6)))
# 行业
for nm, key in [("化学制药", "YIYAO"), ("医疗服务", "MEDSVC"), ("医疗器械", "MEDDEV"),
                ("半导体", "BDT"), ("电网设备", "DW"), ("房地产开", "FDCK"),
                ("房地产服", "FDCF"), ("化学制品", "HXP"), ("出版", "CB"),
                ("家居用品", "JJYP"), ("广告营销", "GGYX"), ("元件", "YJ"),
                ("一般零售", "LS"), ("服装家纺", "FZJZ"), ("专用设备", "ZYSB"),
                ("通用设备", "TYSB"), ("消费电子", "XFDZ"), ("计算机设", "JSJSB"),
                ("软件开发", "RJKF"), ("塑料", "SL"), ("环境治理", "HJZL"), ("家电零部", "JD"),
                ("光学光电", "GXGD"), ("IT服务Ⅱ", "IT2"), ("水泥", "SN"), ("军工电子", "JG"),
                ("林业Ⅱ", "LY"), ("汽车零部", "QC"), ("电视广播", "DSGB"), ("其他家电", "QTJD"),
                ("纺织制造", "FZZZ"), ("光伏设备", "GFSB"), ("工程机械", "GCJX"),
                ("农化制品", "NH"), ("焦炭Ⅱ", "JT"), ("养殖业", "YZY"), ("文娱用品", "WY"),
                ("小家电", "XDJ"), ("光学光电", "GX2"), ("电池", "DC"), ("非白酒", "FBJ"),
                ("商用车", "SYC"), ("农产品加", "NCP"), ("化学原料", "HXL"), ("影视院线", "YSYX"),
                ("互联网电", "HLWD"), ("电力", "DL")]:
    P("HY_" + key, hy0.get(nm, 0)); P("HY_" + key + "_Y", hy1.get(nm, 0))
P("IX_SZ50_PCT", "{:+.2f}".format(ixr.get("上证50", {}).get("pct", 0)))
P("IX_GZ2000_PCT", "{:+.2f}".format(ixr.get("国证2000", {}).get("pct", 0)))
P("IX_ZZ1000_PCT", "{:+.2f}".format(ixr.get("中证1000", {}).get("pct", 0)))
P("IX_CYB_PCT", "{:+.2f}".format(ixr.get("创业板指", {}).get("pct", 0)))
P("IX_ZZ500_PCT", "{:+.2f}".format(ixr.get("中证500", {}).get("pct", 0)))
P("IX_HS300_PCT", "{:+.2f}".format(ixr.get("沪深300", {}).get("pct", 0)))
P("IX_ZXX100_PCT", "{:+.2f}".format(ixr.get("中小100", {}).get("pct", 0)))
P("IX_BJ50_PCT", "{:+.2f}".format(ixr.get("北证50", {}).get("pct", 0)))
P("ZTDT_Y_DISP", "—" if not s1["dt"] else "{:.1f}".format(s1["zt"] / s1["dt"]))
P("TS_EARLY", ts0.get("竞价/秒板", 0) + ts0.get("开盘半小时", 0))
P("TS_EARLY_PCT", "{:.0f}".format((ts0.get("竞价/秒板", 0) + ts0.get("开盘半小时", 0)) / s0["zt"] * 100))
P("TS_EARLY_Y", ts1.get("竞价/秒板", 0) + ts1.get("开盘半小时", 0))
P("TS_EARLY_Y_PCT", "{:.0f}".format((ts1.get("竞价/秒板", 0) + ts1.get("开盘半小时", 0)) / s1["zt"] * 100))
P("TS_PM0", ts0.get("午后盘中", 0)); P("TS_PM1", ts1.get("午后盘中", 0))
P("TS_PM_PCT", "{:.0f}".format(ts0.get("午后盘中", 0) / s0["zt"] * 100))
P("TS_PM_Y_PCT", "{:.0f}".format(ts1.get("午后盘中", 0) / s1["zt"] * 100))
P("TS_AUC", ts0.get("竞价/秒板", 0)); P("TS_AUC_Y", ts1.get("竞价/秒板", 0))
# 跌停池
P("DT_N", DT_N); P("DT_AMT", "{:.0f}".format(DT_AMT))
P("DT_AMT_RATIO", "{:.1f}".format(DT_AMT / amt_sum if amt_sum else 0))
P("DT_AMT_SHARE", "{:.1f}".format(DT_AMT / amt_today * 100))
P("DT_CHAIN_N", DT_CHAIN_N); P("DT_CHAIN_PCT", "{:.0f}".format(DT_CHAIN_PCT))
P("DT_CHAIN_AMT", "{:.0f}".format(_dt_chain_amt))
P("DT_CHAIN_TOPN", "、".join(esc(x.get("n")) for x in dt_chain[:6]))
P("DT_BIG_N", len([x for x in _dt_pool if (x.get("ltsz") or 0) >= 1e10]))
P("DT_BIG_AMT", "{:.0f}".format(sum((x.get("amount") or 0) for x in _dt_pool if (x.get("ltsz") or 0) >= 1e10) / 1e8))
P("DT_HY_N", len(_dt_hy_cnt))
# 行业榜
P("SEC_N", SEC_N); P("SEC_UP", SEC_UP); P("SEC_DN", SEC_DN); P("SEC_FLAT", SEC_FLAT)
P("SEC_TOP1", esc(SECTOR_IND[0][0])); P("SEC_TOP1_V", "{:+.2f}".format(SECTOR_IND[0][1]))
P("SEC_TOP2", esc(SECTOR_IND[1][0])); P("SEC_TOP2_V", "{:+.2f}".format(SECTOR_IND[1][1]))
P("SEC_TOP3", esc(SECTOR_IND[2][0])); P("SEC_TOP3_V", "{:+.2f}".format(SECTOR_IND[2][1]))
P("SEC_TOP4", esc(SECTOR_IND[3][0])); P("SEC_TOP4_V", "{:+.2f}".format(SECTOR_IND[3][1]))
P("SEC_TOP5", esc(SECTOR_IND[4][0])); P("SEC_TOP5_V", "{:+.2f}".format(SECTOR_IND[4][1]))
P("SEC_BOT1", esc(SECTOR_IND[-1][0])); P("SEC_BOT1_V", "{:+.2f}".format(SECTOR_IND[-1][1]))
P("SEC_BOT2", esc(SECTOR_IND[-2][0])); P("SEC_BOT2_V", "{:+.2f}".format(SECTOR_IND[-2][1]))
P("SEC_BOT3", esc(SECTOR_IND[-3][0])); P("SEC_BOT3_V", "{:+.2f}".format(SECTOR_IND[-3][1]))
P("SEC_BOT4", esc(SECTOR_IND[-4][0])); P("SEC_BOT4_V", "{:+.2f}".format(SECTOR_IND[-4][1]))
P("SEC_BOT5", esc(SECTOR_IND[-5][0])); P("SEC_BOT5_V", "{:+.2f}".format(SECTOR_IND[-5][1]))
P("SEC_BOT6", esc(SECTOR_IND[-6][0])); P("SEC_BOT6_V", "{:+.2f}".format(SECTOR_IND[-6][1]))
P("SEC_NM_PCT", "{:.1f}".format(SECTOR_IND[-1][1] / SECTOR_IND[0][1] * 100) if False else "—")
P("CON_BOT1", esc(CONCEPT_BOT[0][0])); P("CON_BOT1_V", "{:+.2f}".format(CONCEPT_BOT[0][1]))
P("CON_BOT2", esc(CONCEPT_BOT[1][0])); P("CON_BOT2_V", "{:+.2f}".format(CONCEPT_BOT[1][1]))
P("CON_BOT3", esc(CONCEPT_BOT[2][0])); P("CON_BOT3_V", "{:+.2f}".format(CONCEPT_BOT[2][1]))
P("CON_BOT4", esc(CONCEPT_BOT[3][0])); P("CON_BOT4_V", "{:+.2f}".format(CONCEPT_BOT[3][1]))
P("CON_BOT5", esc(CONCEPT_BOT[4][0])); P("CON_BOT5_V", "{:+.2f}".format(CONCEPT_BOT[4][1]))
P("CON_BOT6", esc(CONCEPT_BOT[5][0])); P("CON_BOT6_V", "{:+.2f}".format(CONCEPT_BOT[5][1]))
P("CON_BOT7", esc(CONCEPT_BOT[6][0])); P("CON_BOT7_V", "{:+.2f}".format(CONCEPT_BOT[6][1]))
P("CON_BOT8", esc(CONCEPT_BOT[7][0])); P("CON_BOT8_V", "{:+.2f}".format(CONCEPT_BOT[7][1]))
P("SEC_BOT7", esc(SECTOR_IND[-7][0])); P("SEC_BOT7_V", "{:+.2f}".format(SECTOR_IND[-7][1]))
P("SEC_BOT8", esc(SECTOR_IND[-8][0])); P("SEC_BOT8_V", "{:+.2f}".format(SECTOR_IND[-8][1]))
P("MKT_DN5P", 350 + 449)
# 全市场分布（westock changedist）
P("MKT_UP", 898); P("MKT_DN", 4554); P("MKT_FLAT", 117)
P("MKT_DN_PCT", "{:.1f}".format(4554 / (898 + 4554 + 117) * 100))
P("MKT_UP7", 48); P("MKT_DN7", 350)
P("MKT_DN5", 449); P("MKT_DN2", 1784)
P("TBL_SENTI", tbl_senti); P("TBL_LAD", tbl_lad); P("TBL_LIANBAN", tbl_lianban)
P("TBL_HY", tbl_hy); P("TBL_TS", tbl_ts); P("TBL_THEME", tbl_theme); P("TBL_IDX", tbl_idx)
P("TBL_HUA", tbl_hua); P("TBL_ZB", tbl_zb); P("TBL_STY", tbl_sty)
P("TBL_ROBOT", tbl_robot); P("TBL_AUTO", tbl_auto)
P("TBL_DT_BIG", tbl_dt_big); P("TBL_DT_CHAIN", tbl_dt_chain); P("TBL_DT_HY", tbl_dthy)
P("TBL_SEC", tbl_sec); P("TBL_CON", tbl_con)
P("JS_DAYS", json.dumps([d["d"] for d in days], ensure_ascii=False))
P("JS_ZT", json.dumps([d["zt"] for d in days]))
P("JS_ZB", json.dumps([d["zb"] for d in days]))
P("JS_DT", json.dumps([d["dt"] for d in days]))
P("JS_SEAL", json.dumps([round(d["seal"], 1) for d in days]))
P("JS_IX_NAME", json.dumps([x["name"] for x in ix][::-1], ensure_ascii=False))
P("JS_IX_PCT", json.dumps([round(x["pct"], 2) for x in ix][::-1]))
P("JS_LAD_NAME", json.dumps([str(i) + "板" for i in range(1, lad_max + 1)], ensure_ascii=False))
P("JS_LAD0", json.dumps(lad_series(lad0, lad_max)))
P("JS_LAD1", json.dumps(lad_series(lad1, lad_max)))
_th_pos = [t for t in theme_cnt if t["n"] > 0]
P("JS_TH_NAME", json.dumps([t["name"] for t in _th_pos][::-1], ensure_ascii=False))
P("JS_TH_N", json.dumps([t["n"] for t in _th_pos][::-1]))
P("JS_HY_NAME", json.dumps([h["name"] for h in hy_tbl][::-1], ensure_ascii=False))
P("JS_HY_T", json.dumps([h["t"] for h in hy_tbl][::-1]))
P("JS_HY_Y", json.dumps([h["y"] for h in hy_tbl][::-1]))
P("JS_PF_NAME", json.dumps([p["name"] for p in perf_sorted][::-1], ensure_ascii=False))
P("JS_PF_PCT", json.dumps([round(p["pct"], 2) for p in perf_sorted][::-1]))
P("JS_TS_NAME", json.dumps(TS_ORDER, ensure_ascii=False))
P("JS_TS_T", json.dumps([ts0.get(k, 0) for k in TS_ORDER]))
P("JS_TS_Y", json.dumps([ts1.get(k, 0) for k in TS_ORDER]))
P("JS_DTHY_NAME", json.dumps([k for k, _v in dt_hy_top][::-1], ensure_ascii=False))
P("JS_DTHY_N", json.dumps([v for _k, v in dt_hy_top][::-1]))
P("JS_SEC_NAME", json.dumps([nm for nm, _v in SEC_SHOW][::-1], ensure_ascii=False))
P("JS_SEC_V", json.dumps([v for _nm, v in SEC_SHOW][::-1]))
P("L_D1", md(D1)); P("L_D0", md(D0)); P("L_D2", md(D2))

# ================= HTML =================
HTML_T = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>涨停复盘 · 2026-09-28（对比 9-24）</title>
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
.lead{background:#fff;border:1px solid #e6e8eb;border-left:5px solid #12805c;border-radius:10px;padding:18px 22px;margin-bottom:18px}
.lead p{margin:0 0 8px}.lead p:last-child{margin-bottom:0}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:12px;margin:16px 0 4px}
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
.chart{width:100%;height:330px}.chart-sm{width:100%;height:270px}
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
<h1>涨停复盘 · 2026-09-28（周一）</h1>
<div class="sub">对比基准：2026-09-24（周四）｜中间跨中秋节假期（9/25–9/27 休市）｜口径：沪深两市（不含北交所）｜数据源：同花顺涨停池 + 东方财富涨停/炸板/跌停池 + 行情快照 + WeStock 行业榜</div>

<div class="lead">
<p class="hl">一句话结论：从"缩量阴跌"切换到"放量杀跌"——涨停腰斩到 __ZT__ 家、跌停暴增 __DT_MULT__ 倍到 __DT__ 家，两市成交额逆势放大 __AMT_PCT__%，全部指数重挫（创业板 __CY_PCT2__%、科创50 __KC_PCT__%）；
跌停池 __DT_N__ 只里有 __DT_CHAIN_N__ 只（__DT_CHAIN_PCT__%）属于<b>光通信 / PCB / 被动元件这条算力硬件链</b>，这是一次高位拥挤赛道的集中减仓，而不是普跌中的均匀失血。</p>
<p>指数端：上证 __SH_PCT2__%、深成 __SZ_PCT2__%、创业板 __CY_PCT2__%、科创50 __KC_PCT__%、北证50 __IX_BJ50_PCT__%，
<span class="hl">全部指数低开且全天无反抽</span>（缺口 __SH_GAP__%~__KC_GAP__%，收盘距当日最高 __SH_DRAW__%~__CY_DRAW__%）。
全市场 __MKT_UP__ 只上涨、__MKT_DN__ 只下跌（__MKT_DN_PCT__% 下跌）、跌超 7% 的 __MKT_DN7__ 只——<b>这是一次全市场级别的风险偏好收缩</b>。</p>
<p>量能端出现本轮最关键的转折：两市成交额 __AMT__ 亿，<span class="hl">环比 __AMT_D__ 亿 / __AMT_PCT__%（由缩量转为放量），而指数跌幅比昨日扩大 1.2~1.9 倍</span>。
9/24 那天的组合是「缩量 + 下跌」（没人接），今天的组合是「<b>放量 + 下跌</b>」（有人在卖）——
<b>这是本日与前一交易日最本质的区别</b>，也是把"收缩式锁仓"直接推翻的信号。</p>
<p>打板端同步塌陷：涨停 __ZT_Y__→__ZT__（__ZT_PCT_D__%）、封板率 __SEAL_Y__%→__SEAL__%（__SEAL_D__pct）、
触及涨停家数 __TOUCH_Y__→__TOUCH__（__TOUCH_PCT_D__%）——<span class="hl">参与度与承接力同时下降，与 9/24「参与降、承接升」的背离形态完全相反</span>。
昨日涨停股今日晋级率 __ADV_RATE__%（昨 25.5%），中位 __PERF_MED__%，翻绿 __NEG__ 只（__NEG_PCT__%）、跌超 5% 的 __NEG_LOW__ 只——
<b>打板资金的单日亏损幅度是本轮 9/16 以来最严重的一天</b>。</p>
<p>资金去向：主力净流出集中在<b>通信设备、半导体、元件、消费电子</b>（CPO 概念单日净流出规模居前），
唯一上涨的行业只有 __SEC_TOP1__（__SEC_TOP1_V__%）、__SEC_TOP2__（__SEC_TOP2_V__%）、__SEC_TOP3__（__SEC_TOP3_V__%）等 __SEC_UP__ 个低位方向；__SEC_N__ 个申万二级行业里有 __SEC_DN__ 个下跌。
涨停结构上，唯一同时具备"产业叙事 + 连板梯队"的是<b>机器人/精密零部件（__ROBOT_N__ 只）</b>，新增方向是<b>汽车整车/商用车（__AUTO_N__ 只，合计成交 __AUTO_AMT__ 亿）</b>；
而「华」字辈由 __HUA_N_Y__ 只塌到 __HUA_N__ 只——<b>9/22 以来靠名称博弈撑起来的最后一块情绪，今天正式瓦解</b>。</p>
</div>

<div class="kpis">
  <div class="kpi"><div class="lbl">涨停家数</div><div class="val mut">__ZT__</div>
    <div class="dt mut">昨日 __ZT_Y__ <span class="down">__ZT_D__</span>（__ZT_PCT_D__%）</div></div>
  <div class="kpi"><div class="lbl">跌停家数</div><div class="val down">__DT__</div>
    <div class="dt mut">昨日 __DT_Y__ <span class="down">__DT_D__</span>（__DT_MULT__ 倍）</div></div>
  <div class="kpi"><div class="lbl">封板率</div><div class="val down">__SEAL__%</div>
    <div class="dt mut">昨日 __SEAL_Y__% <span class="down">__SEAL_D__pct</span></div></div>
  <div class="kpi"><div class="lbl">两市成交额</div><div class="val up">__AMT__亿</div>
    <div class="dt mut">昨日 __AMT_Y__亿 <span class="up">__AMT_D__亿（__AMT_PCT__%）</span></div></div>
  <div class="kpi"><div class="lbl">昨涨停今日晋级率</div><div class="val down">__ADV_RATE__%</div>
    <div class="dt mut">__ADV_N__/__ADV_TOT__ 只再涨停（昨 25.5%）</div></div>
  <div class="kpi"><div class="lbl">最高连板</div><div class="val up">__MAXB__ 板</div>
    <div class="dt mut">昨日 __MAXB_Y__ 板（__LB_TOP1__，4 板→5 板）</div></div>
</div>

<div class="card">
<h2>一、市场情绪温度计：跌停 5 倍于昨日，参与度与承接力首次同向下滑</h2>
<table>
<tr><th>指标</th><th>__L_D2__（周三）</th><th>__L_D1__（周四）</th><th>__L_D0__（周一）</th><th>__L_D0__ 环比</th></tr>
__TBL_SENTI__
<tr><td>涨停/跌停比</td><td>__ZTDT_0__</td><td>__ZTDT_Y_DISP__</td><td class="down">__ZTDT__</td><td class="down">崩塌</td></tr>
<tr><td>跌停封死率(%)</td><td>__DT_LOCK_D2__</td><td>__DT_LOCK_Y__</td><td class="hl">__DT_LOCK__</td><td class="down">—</td></tr>
<tr><td>触及跌停家数</td><td>__DT_TOUCH_D2__</td><td>__DT_TOUCH_Y__</td><td class="hl">__DT_TOUCH__</td><td class="down">__DT_TOUCH_D__</td></tr>
</table>
<div class="note" style="margin-top:10px">
注：__L_D2__ 与 __L_D1__ 两列取自本次抓取的前一交易日存档（同花顺汇总字段）；该字段在盘后仍会极小幅度刷新，
与当日盘后即时抓取的值可能有 ±1 家的差异（例如 9/24 跌停家数当日记录为 10 家、本次存档为 11 家），<b>不影响方向性结论</b>。<br>
三日序列变成「退潮（__L_D1__ 涨停 __ZT_Y__ 家、封板率 __SEAL_Y__%）→ <b>杀跌（__L_D0__ 涨停 __ZT__ 家、跌停 __DT__ 家）</b>」。
按本流程的判读规则，<span class="hl">「封板率与跌停数同时恶化」是退潮加速的确认信号</span>——今日两项同时反向（封板率 __SEAL_D__pct、跌停由 __DT_Y__ 增到 __DT__、跌停封死率 __DT_LOCK_Y__%→__DT_LOCK__%），
且<span class="hl">参与度同步下滑</span>（触及涨停 __TOUCH_Y__→__TOUCH__，__TOUCH_PCT_D__%）。<br>
<b>这一点必须与 9/24 对照着读：</b>9/24 是"参与度 ↓ 而承接力 ↑"（收缩式锁仓），今日是"<b>参与度 ↓ 且承接力 ↓</b>"——
前者是资金收手、后者是资金出逃。<b>两者方向一致但性质完全不同，绝不能因为"封板率仍在 __SEAL__% 附近"就认为形态没变</b>。<br>
最强的量化冲突在跌停端：<span class="hl">跌停 __DT__ 家（昨日 __DT_Y__ 家的 __DT_MULT__ 倍）、触及跌停 __DT_TOUCH__ 家、封死率 __DT_LOCK__%，三项均为本轮 9/16 以来最高</span>。
而涨停/跌停比从 __ZTDT_Y_DISP__ 直接掉到 __ZTDT__，<b>跌破 1 是本轮首次</b>——即"跌停家数超过涨停家数"。
</div>
<div id="c_senti" class="chart" style="margin-top:16px"></div>
</div>

<div class="card">
<h2>二、指数与量能：逆势放量 __AMT_PCT__%，是"卖盘涌出"而非"买盘回归"</h2>
<div class="two">
<div>
<table>
<tr><th>指数</th><th>今日</th><th>昨日</th><th>成交额</th></tr>
__TBL_IDX__
</table>
<div class="note" style="margin-top:10px">
两市成交额 __AMT__ 亿（环比 __AMT_D__ 亿、__AMT_PCT__%），<span class="hl">结束连续两日缩量，重新回到 9/22 的 21356 亿下方但明显高于 9/24 的 16534 亿</span>。
更关键的是<b>放量的分布</b>——按各指数成交额环比排序：
</div>
<table style="margin-top:8px">
<tr><th>市值/风格</th><th>今日涨跌%</th><th>昨日涨跌%</th><th>成交额环比</th></tr>
__TBL_STY__
</table>
<div class="note" style="margin-top:8px">
<span class="hl">放量的方向恰恰是跌幅居前的方向</span>：科创50 成交额环比 __KC_AMT_PCT__%（跌幅 __KC_PCT__%）、沪深300 __HS300_AMT_PCT__%（__IX_HS300_PCT__%）、
中小100 __ZXX_AMT_PCT__%（__IX_ZXX100_PCT__%）、中证500 __ZZ500_AMT_PCT__%（__IX_ZZ500_PCT__%）、上证50 __SZ50_AMT_PCT__%（__IX_SZ50_PCT__%）。<br>
反之缩量的是国证2000 __GZ2000_AMT_PCT__%（__IX_GZ2000_PCT__%）与北证50 __BJ50_AMT_PCT__%（__IX_BJ50_PCT__%）。
<b>"放量 + 下跌"和"缩量 + 下跌"是两种完全不同的市场</b>：前者是卖方主动出货、后者是买方消失。
今日大市值与科技成长两头放量下跌，说明<b>减仓来自持仓最重的资金</b>，而不是流向了小微盘。
</div>
</div>
<div><div id="c_idx" class="chart-sm"></div>
<div class="note" style="margin-top:8px">
上证低开 __SH_GAP__% 收 __SH_PCT2__%（距当日最高 __SH_DRAW__%），深成低开 __SZ_GAP__% 收 __SZ_PCT2__%（距最高 __SZ_DRAW__%），
创业板指低开 __CY_GAP__% 收 __CY_PCT2__%（距最高 __CY_DRAW__%），科创50 低开 __KC_GAP__% 收 __KC_PCT__%（距最高 __KC_DRAW__%）。
<span class="hl">四类指数全部低开低走、全天没有一次有效反抽</span>，与 9/24 形态一致但跌幅放大 1.2~1.9 倍。
</div>
</div>
</div>
<h3>全市场涨跌分布：__MKT_DN_PCT__% 个股下跌，跌超 7% 的 __MKT_DN7__ 只</h3>
<table style="margin-top:8px">
<tr><th>区间</th><th>家数</th><th>区间</th><th>家数</th></tr>
<tr><td>涨停</td><td class="up">35</td><td>跌停</td><td class="down">60</td></tr>
<tr><td>涨超 7%</td><td class="up">13</td><td>跌超 7%</td><td class="down">350</td></tr>
<tr><td>涨 7%~5%</td><td class="up">35</td><td>跌 7%~5%</td><td class="down">449</td></tr>
<tr><td>涨 5%~2%</td><td class="up">165</td><td>跌 5%~2%</td><td class="down">1784</td></tr>
<tr><td>涨 2%~0%</td><td class="up">650</td><td>跌 2%~0%</td><td class="down">1911</td></tr>
<tr><td>平盘</td><td class="mut">117</td><td>停牌</td><td class="mut">12</td></tr>
</table>
<div class="note" style="margin-top:8px">
口径：全市场（含北交所、含 ST）涨跌分布，来源 WeStock `changedist`。该口径下涨停 35 家 / 跌停 60 家，
与沪深涨停池口径（__ZT__ / __DT__）相差 2 / 4 家，差额无法归因到具体标的，<b>本报告正文一律采用沪深池口径</b>。
分布形态是典型的<b>恐慌长尾</b>：跌 5% 以上的合计 __MKT_DN5P__ 家（跌 5%~7% __MKT_DN5__ 家 + 跌超 7% __MKT_DN7__ 家），而涨 5% 以上的仅 48 家，<b>比例接近 17:1</b>。
</div>
<h3>炸板池结构：__ZB_POOL_N__ 只炸板、__ZB_SEALED_N__ 只回封，全部在 __ZB_FBT_MAX__ 前触板</h3>
<table style="margin-top:8px">
<tr><th>炸板池个股（流通市值 TOP4）</th><th>代码</th><th>行业</th><th>流通市值</th><th>收盘涨幅</th><th>首触时间</th></tr>
__TBL_ZB__
</table>
<div class="note" style="margin-top:8px">
__ZB_POOL_N__ 只炸板股中 __ZB_SEALED_N__ 只回封；首触时间区间为 <span class="hl">__ZB_FBT_MIN__ – __ZB_FBT_MAX__</span>，
<b>即全部 11 只都在早盘 23 分钟内冲板、之后无一回封</b>——这是"早盘情绪冲高、随后全天走坏"的教科书形态。<br>
未回封阵营里流通市值最大的是 __ZB_TOP1__（__ZB_TOP1_V__ 亿，成交 __ZB_TOP1_AMT__ 亿）、__ZB_TOP2__（__ZB_TOP2_V__ 亿）、__ZB_TOP3__（__ZB_TOP3_V__ 亿）、__ZB_TOP4__（__ZB_TOP4_V__ 亿）。
其中<span class="hl">彩虹股份（流通 380 亿以上，成交 37.70 亿）收 +9.38%、距涨停价仅差 0.06 元未封住</span>，
是"面板/显示链在系统性杀跌中最后抵抗失败"的直接样本，也是本日炸板池里最具指标意义的一只。
</div>
</div>

<div class="card">
<h2>三、跌停池 __DT_N__ 只：__DT_CHAIN_N__ 只（__DT_CHAIN_PCT__%）来自算力硬件链，这才是今日的主要矛盾</h2>
<div class="two">
<div><div id="c_dthy" class="chart-sm" style="height:330px"></div></div>
<div>
<table>
<tr><th>跌停池行业分布</th><th>家数</th><th>归类</th></tr>
__TBL_DT_HY__
</table>
<div class="note" style="margin-top:8px">
跌停池 __DT_N__ 只、覆盖 __DT_HY_N__ 个东财行业；<span class="hl">通信设备 __DT_HY_CS__ 家 + 元件 __DT_HY_YJ__ 家，两个行业就占了 __DT_HY_CS_YJ__ 只（__DT_HY_CS_YJ2__%）</span>。
跨行业归并后（口径见下方说明），<b>电子/算力硬件链合计 __DT_CHAIN_N__ 只</b>。
</div>
</div>
</div>
<h3>跌停池流通市值 TOP10</h3>
<table>
<tr><th>名称</th><th>代码</th><th>东财行业</th><th>流通市值</th><th>收盘涨幅</th><th>成交额</th><th>最后封板</th></tr>
__TBL_DT_BIG__
</table>
<div class="note" style="margin-top:8px">
<span class="hl">跌停池合计成交 __DT_AMT__ 亿，是今日涨停股合计成交（__AMT_SUM__ 亿）的 __DT_AMT_RATIO__ 倍，占两市成交额 __DT_AMT_SHARE__%</span>。
流通市值超过 100 亿的跌停股有 __DT_BIG_N__ 只、合计成交 __DT_BIG_AMT__ 亿——
<b>这不是"小票补跌"，而是大市值核心资产在主动减仓</b>。名单里可以看到：
亨通光电（1488 亿）、中天科技（1069 亿）、山东黄金（946 亿）、华工科技（931 亿）、风华高科（579 亿）、永鼎股份（560 亿）、
烽火通信（470 亿）、江海股份（428 亿）、星网锐捷（250 亿）等，<b>全部是本轮 AI 算力/光通信主线的核心持仓</b>。</p>
</div>
<h3>算力硬件链跌停明细（__DT_CHAIN_N__ 只）</h3>
<table>
<tr><th>名称</th><th>代码</th><th>东财行业</th><th>流通市值</th><th>收盘涨幅</th><th>成交额</th></tr>
__TBL_DT_CHAIN__
</table>
<div class="note" style="margin-top:8px">
口径说明：本表按东财行业标签归并「通信设备 / 元件 / 其他电子 / 电子化学品 / 消费电子 / 自动化设备 / 塑料 / 金属新材料」八类，
属<b>关键词口径而非标准行业分类</b>（「塑料」下为东材科技、圣泉集团等电子材料，「金属新材料」下为江南新材 PCB 铜球，「自动化设备」下为华工科技、科瑞技术），
因此报告同时披露原始行业分布表，读者可自行复核。
板块层面可以交叉验证：<span class="hl">申万二级「通信设备」收 __SEC_BOT2_V__%（行业跌幅第二、主流行业中第一）、「元件」__SEC_BOT4_V__%（跌幅第四）、
概念板块「光芯片」__CON_BOT2_V__%、「光通信」__CON_BOT7_V__%、「CPO」__CON_BOT8_V__%、「MLCC」__CON_BOT6_V__%</span>——
行业、概念、跌停池三条独立口径同时指向同一条链，归因是稳固的。
</div>
<div class="warn" style="margin-top:12px">
<b>消息面（媒体转述，非本报告结论依据）：</b>多家财经媒体同日报道称，本轮光通信/CPO 杀跌主要来自"海外政策提案（限制中国光模块进入部分联邦安全系统）+ 龙头定增带来的摊薄与扩产担忧 + 节前高位兑现"三重共振，
并强调<b>该法案目前仍属提案阶段、限制范围限于国家安全系统</b>，机构普遍表述为"情绪与资金层面扰动，产业景气逻辑未变"。
上述内容为媒体与机构观点转述，本报告<b>不将其作为涨跌原因的证实</b>，仅作为"为什么拥挤度高的赛道会被优先减仓"的背景参考；具体以交易所公告与公司披露为准。
</div>
<h3>贵金属同步杀跌（补充观察）</h3>
<div class="note">
申万二级「贵金属」收 __SEC_BOT5_V__%，为跌幅第五；<b>山东黄金（946 亿）收于跌停、湖南黄金 -4.31%</b>。
在算力链之外，黄金股是今日第二条显著放量下跌的方向（贵金属行业换手率 2.74%，行业小幅缩量但龙头跌幅较大）。
</div>
</div>

<div class="card">
<h2>四、连板梯队：4 板断层、首板占比 __SB_PCT__%，高度只剩一只 5 板的 __LB_TOP1__</h2>
<div class="two">
<div><div id="c_lad" class="chart-sm"></div></div>
<div>
<table>
<tr><th>梯队</th><th>__L_D1__</th><th>__L_D0__</th><th>变化</th></tr>
__TBL_LAD__
<tr><td>合计</td><td>__ZT_Y__</td><td class="hl">__ZT__</td><td class="mut">__ZT_D__</td></tr>
</table>
<div class="note" style="margin-top:10px">
三处结构性变化：① 首板 __SB_Y__→__SB__ 家（占比 __SB_PCT_Y__%→<span class="hl">__SB_PCT__%</span>）；
② <b>2 板由 __LAD2_Y__ 只塌成 __LAD2_T__ 只</b>、3 板由 __LAD3_Y__ 只变成 __LAD3_T__ 只，<b>4 板直接断层（__LAD4_Y__→__LAD4_T__）</b>；
③ 最高板 __MAXB_Y__ → __MAXB__ 板（__LB_TOP1__，昨 4 板→今 5 板）——但<span class="hl">这只是单点，3 板以上合计由 __LAD3P_Y__ 家降到 __LAD3P_T__ 家</span>。
<b>昨日 4 板以上的 __HILB_Y__ 只（新华文轩 5 板、奥佳华/泰慕士/新华传媒 各 4 板）今日只有一只晋级</b>：
新华传媒 5 板、奥佳华 +2.04%、<b>泰慕士 -10.00% 跌停、新华文轩 -8.99%</b>——
"高位股集体断板"是今日跌停家数暴增在个股层面的直接映射。
</div>
</div>
</div>
<h3>今日连板股全名单（2 板及以上，__LB__ 只）</h3>
<table>
<tr><th>高度</th><th>代码</th><th>名称</th><th>首封</th><th>封单</th><th>成交额</th><th>换手</th><th>行业</th><th>涨停原因</th></tr>
__TBL_LIANBAN__
</table>
<div class="note" style="margin-top:8px">
7 只连板股按叙事分成两组，且分得很干净：
<span class="hl">① 机器人零部件 4 只</span>——襄阳轴承（2 板）、大业股份（2 板）、雪龙集团（3 板）、吉鑫科技（2 板，风电轴承）；
<span class="hl">② 其余 3 只各说各的</span>——新华传媒（5 板，出版/资产重组）、福建水泥（3 板，海峡两岸/福建国资）、金辰股份（3 板，半导体装备+光伏设备）。
<b>唯一成规模的接力方向是机器人零部件</b>，其余都是孤立标的。
</div>
</div>

<div class="card">
<h2>五、主线归因：机器人零部件（__ROBOT_N__ 只）是唯一有产业逻辑的方向，汽车整车（__AUTO_N__ 只）是新增的低位接力位</h2>
<div id="c_theme" class="chart" style="height:380px"></div>
<table style="margin-top:14px">
<tr><th>题材</th><th>涨停家数</th><th>代表个股</th></tr>
__TBL_THEME__
</table>
<div class="note" style="margin-top:12px">
多标签口径下家数最多的三条是 __TH_TOP1__（__TH_TOP1_N__ 家）、__TH_TOP2__（__TH_TOP2_N__ 家）、__TH_TOP3__（__TH_TOP3_N__ 家）；
<b>但家数排序在这里依然无效</b>——国资/股权变更是横切标签（几乎每只涨停都带"国资/重组"关键词）、
AI算力/电子硬件口径过宽且今日该方向<b>恰恰是跌停重灾区</b>（涨停里只剩五方光电、中新赛克、永信至诚、启明信息等零散票）。
<span class="hl">今日真正成立的只有三条线</span>：<br>
① <b>机器人/精密零部件（__TH_ROBOT_N__ 家，合计封单 __ROBOT_FUND__ 亿）</b>——唯一有产业叙事且有连板梯队的方向；
② <b>汽车整车/商用车（__TH_AUTO_N__ 家）</b>——申万二级「商用车」是全场唯一涨幅超 3% 的行业（__SEC_TOP1_V__%），有"行业级"而非"个股级"的支撑；
③ <b>低位消费/农业（__SEC_TOP2__ __SEC_TOP2_V__%、__SEC_TOP3__ __SEC_TOP3_V__%、__SEC_TOP4__ __SEC_TOP4_V__%）</b>——防御性补涨，非主线。
</div>
<h3>机器人/精密零部件集群（__ROBOT_N__ 只，合计封单 __ROBOT_FUND__ 亿，其中连板 __ROBOT_LB_N__ 只）</h3>
<table>
<tr><th>名称</th><th>代码</th><th>连板</th><th>东财行业</th><th>封单</th><th>成交额</th><th>涨停原因</th></tr>
__TBL_ROBOT__
</table>
<div class="note" style="margin-top:8px">
按 reason 关键词（机器人 / 具身 / 人形 / 轴承 / 减速器 / 丝杠 / 执行器）命中 __ROBOT_N__ 家。
其中<span class="hl">吉鑫科技（风电铸件+风电轴承，属风电设备行业）、九阳股份（机器人+太空科技+厨房小家电，属小家电行业）为关键词碰撞</span>，
剔除后<b>严格口径只剩 __ROBOT_CORE_N__ 只</b>：<b>轴承/传动</b>襄阳轴承（机器人轴承+汽车轴承）、大业股份（人形机器人+胎圈钢丝）；<b>本体/集成</b>泰尔股份（工业机器人+激光装备）。
若把"间接投资宇树科技"的雪龙集团（3 板，东财行业为汽车零部）一并计入，该方向的实际承接标的是 __ROBOT_WIDE_N__ 只。
注意：<b>最强势的洛轴股份（301699）今日 +14.46%、成交 8.68 亿，但收盘未涨停（未进入涨停池）</b>，
它同时带"航空轴承+机器人轴承+风电轴承+次新股"四重叙事，是这条线的情绪指标股——<b>指标股不涨停，说明这条线今天是"抗跌"而非"进攻"</b>。
这也是本集群 __ROBOT_N__ 只里只有 __ROBOT_LB_N__ 只连板的原因。
</div>
<h3>汽车整车/商用车集群（__AUTO_N__ 只，合计成交 __AUTO_AMT__ 亿、封单 __AUTO_FUND__ 亿）</h3>
<table>
<tr><th>名称</th><th>代码</th><th>连板</th><th>东财行业</th><th>封单</th><th>成交额</th><th>涨停原因</th></tr>
__TBL_AUTO__
</table>
<div class="note" style="margin-top:8px">
<span class="hl">江淮汽车（__AMT_TOP1__，成交 __AMT_TOP1_V__ 亿）是今日成交额最大的涨停股</span>，也是全场唯一"大市值 + 大成交 + 涨停"的组合，
叙事为"尊界+华为合作+玛莎拉蒂合作传闻"；搭配众泰汽车（汽车整车+A0 车型）构成整车方向。<b>口径提示：本集群按 reason 关键词命中，其中雪龙集团（商用车热管理）与机器人集群重叠、属关键词碰撞，剔除后纯整车标的为 __AUTO_CORE_N__ 只。</b>
行业层面交叉验证：<b>申万二级「商用车」__SEC_TOP1_V__%（全场第一）、「乘用车」-0.58%（远好于大盘）</b>，
是"行业级"证据，而非单只票的脉冲。<b>但需注意其持续性依赖华为合作类事件的进一步落地，属事件驱动而非资金主线。</b>
</div>
<h3>「华」字辈与新华系：由 __HUA_N_Y__ 只塌到 __HUA_N__ 只，名称博弈正式瓦解</h3>
<table>
<tr><th>名称</th><th>代码</th><th>连板</th><th>行业</th><th>成交额</th><th>reason 含国资/重组关键词</th></tr>
__TBL_HUA__
</table>
<div class="note" style="margin-top:10px">
<span class="hl">数量由 __HUA_N_Y__ 只塌到 __HUA_N__ 只（__HUA_LIST__），是 9/22 以来最彻底的一次瓦解</span>：
昨日涨停的「华」字辈中，<b>内蒙新华（昨 1 板）今日跌停 -10.02%、华英农业 -6.61%、华神科技 -5.56%、华茂股份 +0.39% 炸板</b>。
但同一时间龙头却被锁得更死：<span class="hl">__FUND_TOP_NAME__（__FUND_TOP_LB__ 板）封单 __FUND_TOP_VAL__ 亿、占全部涨停股封单的 __FUND_TOP_PCT__%</span>，
而当日成交额仅 __FUND_TOP_AMT__ 亿（封单/成交 ≈ __FUND_TOP_RATIO__ 倍），首封时间 09:25（竞价一字）。
<b>这是"分母崩塌、龙头锁死"的极端结构</b>：整条线的情绪载体已经消失，只剩一只缩量一字板在硬撑。
昨日封单第一同样是它（__FUND_TOP_Y_NAME__，__FUND_TOP_Y_VAL__ 亿，成交 __FUND_TOP_Y_AMT__ 亿），
封单从 __FUND_TOP_Y_VAL__ 亿加到 __FUND_TOP_VAL__ 亿、占比从约 32% 升到 __FUND_TOP_PCT__%——
<b>资金的集中度在提高，而不是在扩散</b>。这种结构的脆弱性是非线性的：不开口看不出问题，一开口就是急跌，且会同步冲击出版行业（今日 __HY_CB__ 家）。<br>
注：reason_type 为多标签，同一只股票可归入多条主线，故各主线家数之和大于涨停总数（__ZT__）。
</div>
</div>

<div class="card">
<h2>六、行业迁移与行业涨跌幅：__SEC_N__ 个申万二级行业仅 __SEC_UP__ 个上涨，资金无处分流</h2>
<div id="c_sec" class="chart" style="height:480px"></div>
<div class="two" style="margin-top:16px">
<div>
<table>
<tr><th>申万二级涨幅前 8 与跌幅前 12</th><th>涨跌%</th><th></th></tr>
__TBL_SEC__
</table>
</div>
<div>
<table>
<tr><th>跌幅前 12 概念板块</th><th>涨跌%</th></tr>
__TBL_CON__
</table>
</div>
</div>
<div class="note" style="margin-top:12px">
<b>行业面（收盘涨跌幅）：</b>__SEC_N__ 个申万二级行业中仅 <span class="hl">__SEC_UP__ 个上涨（__SEC_TOP1__ __SEC_TOP1_V__%、__SEC_TOP2__ __SEC_TOP2_V__%、__SEC_TOP3__ __SEC_TOP3_V__%、__SEC_TOP4__ __SEC_TOP4_V__%、__SEC_TOP5__ __SEC_TOP5_V__%）</span>，
其余 __SEC_DN__ 个全部下跌。跌幅榜前五：<span class="hl">__SEC_BOT1__ __SEC_BOT1_V__%、__SEC_BOT2__ __SEC_BOT2_V__%、__SEC_BOT3__ __SEC_BOT3_V__%、__SEC_BOT4__ __SEC_BOT4_V__%、__SEC_BOT5__ __SEC_BOT5_V__%</span>，
第六至第八为 __SEC_BOT6__ __SEC_BOT6_V__%、__SEC_BOT7__ __SEC_BOT7_V__%、__SEC_BOT8__ __SEC_BOT8_V__%。<br>
<b>关键读数：上涨的 __SEC_UP__ 个行业全部是"低位 + 小体量"方向（商用车 67 亿成交、养殖 57 亿、非白酒 53 亿、小家电 27 亿；涨幅居前的五个行业合计仅 296 亿、占两市 __SEC_UP_TURN_SHARE__%），
而跌幅榜前列全部是"高位 + 大体量"方向（通信设备 1310 亿、元件 __SEC_YJ_TURN__ 亿、半导体 __SEC_BDT_TURN__ 亿、消费电子 __SEC_XFDZ_TURN__ 亿）。</b>
这不是"资金从 A 板块搬到 B 板块"，而是<b>资金从市场整体撤出后，只在少数低位小方向上留下零星痕迹</b>——
上涨行业的合计成交额不到下跌行业总量的十分之一，<b>没有承接能力</b>。这也是今日"跌停 56 家而涨停仅 33 家"的行业级解释。<br>
<b>概念面：</b>跌幅前 12 里 11 条属于光通信/PCB/被动元件链（__CON_BOT1__ __CON_BOT1_V__%、__CON_BOT2__ __CON_BOT2_V__%、__CON_BOT3__ __CON_BOT3_V__%、
__CON_BOT4__ __CON_BOT4_V__%、__CON_BOT7__ __CON_BOT7_V__%、__CON_BOT8__ __CON_BOT8_V__%），
与跌停池的行业归因完全一致，属于<b>三个独立口径的交叉验证</b>。
</div>
<h3>涨停股的东财行业迁移（家数口径）</h3>
<div id="c_hy" class="chart" style="height:410px"></div>
<table style="margin-top:14px">
<tr><th>行业</th><th>__L_D1__</th><th>__L_D0__</th><th>增减</th><th>读数</th></tr>
__TBL_HY__
</table>
<div class="note" style="margin-top:12px">
<b>流出端：</b>通用设备 __HY_TYSB_Y__→__HY_TYSB__ 家、汽车零部 __HY_QC_Y__→__HY_QC__ 家、出版 __HY_CB_Y__→__HY_CB__ 家、
医疗服务 __HY_MEDSVC_Y__→__HY_MEDSVC__ 家、半导体 __HY_BDT_Y__→__HY_BDT__ 家、军工电子 __HY_JG_Y__→__HY_JG__ 家、广告营销 __HY_GGYX_Y__→__HY_GGYX__ 家，
以及林业 __HY_LY_Y__→__HY_LY__ 家（福建系退潮）。<br>
<b>流入端（均为零散单点，不构成集群）：</b>化学制药 __HY_YIYAO_Y__→__HY_YIYAO__ 家（丽珠集团、津药药业）、
电网设备 __HY_DW_Y__→__HY_DW__ 家（昨日三星电气今日跌停）、电力 __HY_DL_Y__→__HY_DL__ 家（浙江新能、新筑股份，实为绿电）、光学光电 __HY_GXGD_Y__→__HY_GXGD__ 家（深华发Ａ、五方光电）、
软件开发 __HY_RJKF_Y__→__HY_RJKF__ 家（国新健康、永信至诚）、化学制品 __HY_HXP_Y__→__HY_HXP__ 家（醋化股份、宏柏新材）。<br>
<span class="hl">行业集中度继续失效：今日 __ZT__ 只涨停分散在 __N_HY0__ 个东财行业，最大集群「__TOP_HY0__」各 __TOP_HY0_N__ 只、占 __SHARE_HY0__%</span>
（昨日 __ZT_Y__ 只分散在 __N_HY1__ 个行业，最大集群「__TOP_HY1__」__TOP_HY1_N__ 只占 __SHARE_HY1__%）。
<b>__N_HY0__ 个行业、最大集群仅 __SHARE_HY0__%——在跌停潮里，"行业分布"这个维度已经完全无法用来定位主线</b>，
只能靠 reason 关键词聚类。<br>
<b>注意「通用设备」__HY_TYSB_Y__→__HY_TYSB__ 家继续减少，与本报告上一期（9/24）的发现一致：该标签下是多个不同叙事的混装
（今日为泰尔股份、巨力索具、大业股份——机器人/激光/索具三条线），家数变化不具解释力。</b>
</div>
</div>

<div class="card">
<h2>七、昨日涨停股今日表现：晋级率 __ADV_RATE__%，中位 __PERF_MED__%，跌超 5% 的 __NEG_LOW__ 只</h2>
<div class="kpis" style="grid-template-columns:repeat(auto-fit,minmax(140px,1fr))">
  <div class="kpi"><div class="lbl">晋级率</div><div class="val down">__ADV_RATE__%</div><div class="dt mut">__ADV_N__/__ADV_TOT__（昨 25.5%）</div></div>
  <div class="kpi"><div class="lbl">平均涨幅</div><div class="val down">__PERF_MEAN__%</div><div class="dt mut">中位 __PERF_MED__%</div></div>
  <div class="kpi"><div class="lbl">翻绿比例</div><div class="val down">__NEG_PCT__%</div><div class="dt mut">__NEG__ 只（跌超5% 共 __NEG_LOW__ 只）</div></div>
  <div class="kpi"><div class="lbl">最强</div><div class="val up">__PERF_MAX__%</div><div class="dt mut">__PERF_MAX_NAME__（未涨停）</div></div>
  <div class="kpi"><div class="lbl">最弱</div><div class="val down">__PERF_MIN__%</div><div class="dt mut">__PERF_MIN_NAME__（昨 __PERF_MIN_LB__ 板）</div></div>
</div>
<div class="note" style="margin-top:14px">
昨日 __ADV_TOT__ 只涨停股今日平均 __PERF_MEAN__%、中位 __PERF_MED__%，晋级 __ADV_N__ 只（__ADV_RATE__%），翻绿 __NEG__ 只（__NEG_PCT__%）、跌超 5% 的 __NEG_LOW__ 只。
分层看：<b>昨日首板 n=__ADV_S_N__ 晋级率 __ADV_S_RATE__%、中位 __ADV_S_MED__%；昨日连板 n=__ADV_L_N__ 晋级率 __ADV_L_RATE__%、中位 __ADV_L_MED__%</b>。<br>
<span class="hl">连板组中位为正连续第四个交易日成立（9/22 +2.77%、9/23 +1.25%、9/24 +1.50%、今日 __ADV_L_MED__%），但强度降到最低；首板组中位 -3.75%，是 9/23（-2.62%）以来最差</span>，
两组差距 __ADV_GAP__ 个百分点。含义是：<b>"买确认"仍略优于"买扩散"，但在系统性杀跌里两者的绝对收益均为负</b>——
连板组中位 __ADV_L_MED__% 与首板组中位 __ADV_S_MED__% 的差别，只是"少亏"与"多亏"。<br>
最弱三只 <b>__PERF_BOT3__</b>，<span class="hl">其中泰慕士为昨日 4 板、内蒙新华与华脉科技均收于跌停</span>；
最强三只 <b>__PERF_TOP3__</b>，其中洛轴股份 +14.46% 收涨但<b>未涨停</b>。
<b>最强榜里出现"未涨停"的股票，本身就是当日情绪不足的直接证据</b>——说明资金宁愿在个别标的里做多，也不愿去打板。
</div>
<div id="c_perf" class="chart" style="height:900px;margin-top:8px"></div>
</div>

<div class="card">
<h2>八、封板节奏与成交结构：早盘封板 __TS_EARLY_PCT__%、一字板仅 __ONEWORD__ 只、封单中位继续变薄</h2>
<div class="two">
<div><div id="c_ts" class="chart-sm"></div></div>
<div>
<table>
<tr><th>封板时段</th><th>__L_D1__</th><th>__L_D0__</th></tr>
__TBL_TS__
</table>
<div class="note" style="margin-top:10px">
早盘封板（竞价 + 开盘半小时）__TS_EARLY__ 只，占比 <span class="hl">__TS_EARLY_PCT__%</span>（昨 __TS_EARLY_Y_PCT__%）；
竞价封板仅 __TS_AUC__ 只（昨 __TS_AUC_Y__ 只），午后 __TS_PM0__ 只、尾盘 __TS_TOP__ 只。
<b>节奏与昨日接近，但含义不同：昨日是"早盘定局后不再参与"，今日是"早盘冲高后被系统性杀跌压住"</b>——
两者的差别在炸板池里看得很清楚（11 只炸板全部在 09:47 前触板、之后无一回封）。
</div>
</div>
</div>
<div class="kpis" style="grid-template-columns:repeat(auto-fit,minmax(160px,1fr));margin-top:16px">
  <div class="kpi"><div class="lbl">涨停股合计成交额</div><div class="val down">__AMT_SUM__亿</div><div class="dt mut">占两市 __SHARE__%（昨 __SHARE_Y__%）</div></div>
  <div class="kpi"><div class="lbl">封单合计</div><div class="val down">__FUND_SUM__亿</div><div class="dt mut">昨 __FUND_SUM_Y__亿</div></div>
  <div class="kpi"><div class="lbl">封单中位数</div><div class="val down">__FUND_MED__亿</div><div class="dt mut">昨 __FUND_MED_Y__亿</div></div>
  <div class="kpi"><div class="lbl">一字板 / 换手板</div><div class="val">__ONEWORD__ / __HUANSHOU__</div><div class="dt mut">换手板占 __HUANSHOU_PCT__%</div></div>
</div>
<div class="note" style="margin-top:14px">
涨停股合计成交 __AMT_SUM__ 亿（昨 __AMT_SUM_Y__ 亿，__AMT_SUM_PCT_D__%），占两市 __SHARE__%（昨 __SHARE_Y__%）——<b>低于 3%~8% 常规区间，但这是家数腰斩所致</b>。
用单只中位成交额二次校验：__AMT_MED__ 亿（昨 __AMT_MED_Y__ 亿，__AMT_MED_PCT_D__%）→ 与家数收缩同步，<b>字段源无误</b>。<br>
<span class="hl">封单端是今日更值得关注的一处：封单合计由 __FUND_SUM_Y__ 亿降到 __FUND_SUM__ 亿，封单中位数由 __FUND_MED_Y__ 亿降到 __FUND_MED__ 亿</span>
（9/24 曾出现"合计降、中位升"，今日是<b>两者同降</b>）。
其中 __FUND_TOP_NAME__ 一只占 __FUND_TOP_VAL__ 亿（__FUND_TOP_PCT__%），剔除它之后其余 32 只平均封单仅 __FUND_EX_AVG__ 亿——
<b>"锁仓"保护伞已经收窄到一只票上，市场的整体封板厚度在下降</b>。<br>
换手结构：一字板仅 __ONEWORD__ 只、T字板 2 只、换手板 __HUANSHOU__ 只（占 __HUANSHOU_PCT__%）。
<b>换手板占绝大多数 = 参与者的持仓成本集中在今日，明天大概率是"当日买、当日亏"的延续</b>，而非筹码沉淀。
</div>
</div>

<div class="card">
<h2>九、资金运动的三个结论</h2>
<ul>
<li><b>① 总量：从"缩量阴跌"切换到"放量杀跌"，性质已变。</b>
两市成交额 __AMT__ 亿（__AMT_D__ 亿、__AMT_PCT__%），同时涨停 __ZT_Y__→__ZT__、跌停 __DT_Y__→__DT__（__DT_MULT__ 倍）。
<span class="hl">"成交额放大 + 跌幅扩大 + 跌停家数暴增"三者同向，只能解释为卖盘主动出逃</span>（9/24 的"缩量 + 跌停两位数"是买盘缺席，两者危害机制不同）。
全市场 __MKT_DN__ 只下跌、跌超 7% 的 __MKT_DN7__ 只，也印证了这不是结构性调整而是系统性收缩。</li>
<li><b>② 方向：钱从"算力硬件链"单向夺门而出，进入的方向不构成承接。</b>
跌停池 __DT_N__ 只里 __DT_CHAIN_N__ 只是电子/算力硬件链（__DT_CHAIN_PCT__%），
行业面「通信设备」__SEC_BOT2_V__%、「元件」__SEC_BOT6_V__% 位居跌幅前列，
概念面「光芯片」「光通信」「CPO」「MLCC」全线跌 6%+，
<b>三条独立口径一致指向同一条链</b>。资金并非搬去了某个新主线：上涨的行业只有 __SEC_UP__ 个，
且都是商用车/养殖/非白酒/小家电这类小体量低位方向，<span class="hl">合计成交额不足下跌方向的十分之一</span>。
<b>更值得警惕的是"放量下跌"集中在科创50（__KC_AMT_PCT__%）、沪深300（__HS300_AMT_PCT__%）这类持仓最重的方向</b>——
减仓来自本来持有最多筹码的资金，而不是小微盘的补跌。</li>
<li><b>③ 结构：参与度与承接力同向下滑、打板亏损扩大、"华"字辈瓦解——9/22 以来的情绪载体全部失效。</b>
触及涨停 __TOUCH_Y__→__TOUCH__（__TOUCH_PCT_D__%）、封板率 __SEAL_Y__%→__SEAL__%、炸板 11 只 0 只回封、
晋级率 __ADV_RATE__%（昨 25.5%）、昨日涨停股中位 __PERF_MED__%（跌超 5% 的 __NEG_LOW__ 只）、
封单中位数 __FUND_MED_Y__→__FUND_MED__ 亿（变薄）。
<span class="hl">此前报告的"收缩式锁仓"结论今日被推翻：那天靠的是"减少出手"，今天则是"出手也会亏、且封不住"</span>。
高度端只剩 __LB_TOP1__ 一只 5 板（封单 __FUND_TOP_VAL__ 亿、成交 __FUND_TOP_AMT__ 亿 的缩量一字），
4 板断层、3 板以上合计由 __LAD3P_Y__ 家降到 __LAD3P_T__ 家——
<b>"剩一只高位票 + 腰部断层 + 底部大面积跌停"是本轮 9/16 以来最差的梯队结构</b>。</li>
</ul>
</div>

<div class="card">
<h2>十、明日观察要点与风险</h2>
<ul>
<li><b>第一优先：跌停家数能否收敛。</b>今日跌停 __DT__ 家（触及 __DT_TOUCH__ 家、封死率 __DT_LOCK__%），是本轮首次两位数暴增。
<span class="hl">若明日跌停家数收敛到 15 家以内且触及跌停同步下降，说明今日是"节前一日性恐慌"；若继续高于 30 家，则进入被动去杠杆阶段</span>，
此时任何"涨停家数回升"都不应解读为情绪修复。</li>
<li><b>第二优先：算力硬件链的跌停股能否出现"打开 + 放量承接"。</b>核心观察名单（流通市值从大到小）：
亨通光电（1488 亿）、中天科技（1069 亿）、华工科技（931 亿）、风华高科（579 亿）、永烽火通信（470 亿）、江海股份（428 亿）。
<b>判据不是"是否反弹"，而是"跌停打开时有没有量"</b>——今日这 27 只合计成交 __DT_CHAIN_AMT__ 亿，属于"放量跌停"，
说明解套盘在承接；若明日缩量继续跌停，则是流动性危机的典型特征。</li>
<li><b>机器人零部件能否成为真正的接力主线：</b>__ROBOT_N__ 只、连板 __ROBOT_LB_N__ 只（雪龙集团 3 板；襄阳轴承/大业股份/吉鑫科技 2 板）。
关键在于指标股 <b>洛轴股份（今日 +14.46%、成交 8.68 亿、换手 36.9%，未涨停）</b>——
<span class="hl">这只票若能在次日涨停，这条线才具备"高度 + 龙头"的组合；若继续冲高不封板，则本轮机器人板块只是大盘下跌中的抗跌品种</span>。</li>
<li><b>汽车整车/商用车的延续性：</b>江淮汽车（成交 __AMT_TOP1_V__ 亿）是全场唯一的大市值大成交涨停股，行业面「商用车」__SEC_TOP1_V__%。
<b>但这一方向依赖"尊界/华为合作"类事件的进一步落地</b>，且"玛莎拉蒂合作"目前仍属传闻性质，需以公司公告为准，不宜按已落地定价。</li>
<li><b>新华传媒的缩量一字是最大的一处非线性风险：</b>__FUND_TOP_LB__ 板、封单 __FUND_TOP_VAL__ 亿（占全部封单 __FUND_TOP_PCT__%）、成交仅 __FUND_TOP_AMT__ 亿（封单/成交 __FUND_TOP_RATIO__ 倍）、首封 09:25。
<span class="hl">这种结构的破法只有一种：某一天放量开板</span>。届时不仅该股回撤剧烈，还会同步冲击出版行业（今日 __HY_CB__ 家）与残余的「华」字辈情绪。
<b>它是今日唯一"看起来最安全、实际最脆弱"的持仓</b>。</li>
<li><b>贵金属（黄金股）需单独跟踪：</b>申万二级「贵金属」__SEC_BOT5_V__%，山东黄金（946 亿）收跌停、湖南黄金 -4.31%。
<b>黄金股在"算力链杀跌 + 风险偏好收缩"的当天反而大跌，说明本次是全球性的实际利率/美元定价变化，而非单纯的风险事件避险</b>，
本条仅为观察提示，具体驱动需结合外盘贵金属价格与美债利率核实，不宜据单日表现下结论。</li>
<li><b>假期因素：</b>今日为中秋假期后首个交易日，距离国庆长假仅剩 2 个交易日（9/29、9/30）。
<span class="hl">节前缩量避险与获利了结</span>是历史上 9 月下旬的常见特征，不宜将今日的单日杀跌简单外推为趋势性下行，也不宜把"节后资金回流"当作确定事件。</li>
<li><b>数据口径：</b>统计为沪深两市（不含北交所）。涨停家数：同花顺 __ZT__ 家、东财涨停池 tc=__ZT_D_EM__ 家，<span class="hl">差额 __ZT_EM_DIFF__ 只（今日涨停池内无北交所标的）</span>；
第三方全市场口径（WeStock，含北交所与 ST）为涨停 35 家 / 跌停 60 家，与沪深池口径差 2 / 4 家，<b>差额无法归因到具体标的</b>，正文一律采用沪深池口径。
跌停明细：<span class="hl">东财跌停池接口在默认排序下返回空 pool，改用 sort=fund:asc 后正常返回 __DT_N__ 只</span>（本轮新增的经验）；
同花顺跌停池明细接口本次返回 404（"url 不存在"），故跌停结构完全基于东财池。
封板时间双源分钟级一致率 100%（可比样本 __ZT__ 只）。
涨停股成交额、封单、换手率、连板数均取东财字段；两市成交额为沪市 + 深市全市场口径。<br>
另需披露：<b>今日无"收在涨停价但两源涨停池均不收录"的标的</b>（09-22 瑞芯微、09-24 三羊马为该现象的历史案例），故家数不存在口径歧义。
「算力硬件链」为<b>关键词归并口径</b>（通信设备 / 元件 / 其他电子 / 电子化学品 / 消费电子 / 自动化设备 / 塑料 / 金属新材料八类，
非标准行业分类），报告已同时披露原始行业分布表以便复核。</li>
<li><b>本报告与前一期结论的关系：</b>9/24 本报告的结论是「收缩式锁仓」（参与度 ↓ 而承接力 ↑，靠减少出手维持封板率）。
<span class="hl">今日该结论被直接推翻：封板率 83.6%→__SEAL__%、跌停 10→__DT__ 家、触及涨停 61→__TOUCH__ 家，参与度与承接力首次同向恶化</span>。
这再次验证了本流程的一条固定动作：<b>前一日的情绪结论必须用次日的"各指数成交额环比 + 跌停家数"复核</b>——
本次复核的结果是"缩量锁仓"并未演化为"缩量整理"，而是在假期积累的消息面冲击下直接转为放量出逃。</li>
</ul>
<div class="warn" style="margin-top:14px">
<b>风险提示：</b>本报告为盘后数据复盘与资金行为分析，所有结论基于公开行情数据的统计推断，不构成任何投资建议。
涨停板与跌停板交易均具有高波动、高换手、隔夜风险大的特征，历史统计规律不保证未来重复。
报告引用的"消息面"部分为财经媒体与机构观点转述，<b>不构成事实确认</b>，涉及政策与公司事项请以交易所公告、公司披露及主管部门文件为准。
</div>
</div>

<div class="note" style="text-align:center;color:#9ca3af;margin-top:24px">
生成时间：__GEN_AT__｜数据源：同花顺 / 东方财富 / 腾讯财经 / WeStock｜本报告由脚本自动生成
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
  grid:{left:76,right:52,top:16,bottom:24},
  xAxis:Object.assign({type:'value',axisLabel:{formatter:'{value}%'}},AX),
  yAxis:Object.assign({type:'category',data:__JS_IX_NAME__},AX),
  series:[{type:'bar',data:__JS_IX_PCT__,barWidth:14,
    itemStyle:{color:function(p){return p.value>=0?C_RED:C_GRN}},
    label:{show:true,position:'right',color:'#6b7280',fontSize:11,formatter:'{c}%'}}]
});

mk('c_dthy',{
  tooltip:{trigger:'axis'},
  grid:{left:84,right:52,top:14,bottom:22},
  xAxis:Object.assign({type:'value'},AX),
  yAxis:Object.assign({type:'category',data:__JS_DTHY_NAME__},AX),
  series:[{type:'bar',data:__JS_DTHY_N__,itemStyle:{color:C_GRN},barWidth:15,
    label:{show:true,position:'right',color:'#374151',fontWeight:600,formatter:'{c} 家'}}]
});

mk('c_lad',{
  tooltip:{trigger:'axis'},legend:{top:3,left:'center',textStyle:{color:'#6b7280'}},
  grid:{left:46,right:20,top:52,bottom:28},
  xAxis:Object.assign({type:'category',data:__JS_LAD_NAME__},AX),
  yAxis:Object.assign({type:'value'},AX),
  series:[
    {name:'__L_D1__',type:'bar',data:__JS_LAD1__,itemStyle:{color:'#cbd5e1'},barWidth:18},
    {name:'__L_D0__',type:'bar',data:__JS_LAD0__,itemStyle:{color:C_RED},barWidth:18,
     label:{show:true,position:'top',color:'#9ca3af',fontSize:11}}
  ]
});

mk('c_theme',{
  tooltip:{trigger:'axis'},
  grid:{left:138,right:70,top:16,bottom:24},
  xAxis:Object.assign({type:'value'},AX),
  yAxis:Object.assign({type:'category',data:__JS_TH_NAME__},AX),
  series:[{type:'bar',data:__JS_TH_N__,itemStyle:{color:C_BLU},barWidth:15,
    label:{show:true,position:'right',color:'#374151',fontWeight:600,formatter:'{c} 家'}}]
});

mk('c_sec',{
  tooltip:{trigger:'axis',valueFormatter:function(v){return v+'%'}},
  grid:{left:118,right:56,top:14,bottom:26},
  xAxis:Object.assign({type:'value',axisLabel:{formatter:'{value}%'}},AX),
  yAxis:Object.assign({type:'category',data:__JS_SEC_NAME__,axisLabel:{color:'#6b7280',fontSize:10,interval:0}},AX),
  series:[{type:'bar',data:__JS_SEC_V__,barWidth:13,
    itemStyle:{color:function(p){return p.value>=0?C_RED:C_GRN}},
    label:{show:true,position:'right',fontSize:10,color:'#9ca3af',
      formatter:function(p){return p.value.toFixed(2)}}}]
});

mk('c_hy',{
  tooltip:{trigger:'axis'},legend:{top:3,left:'center',textStyle:{color:'#6b7280'}},
  grid:{left:100,right:56,top:52,bottom:24},
  xAxis:Object.assign({type:'value'},AX),
  yAxis:Object.assign({type:'category',data:__JS_HY_NAME__},AX),
  series:[
    {name:'__L_D1__',type:'bar',data:__JS_HY_Y__,itemStyle:{color:'#cbd5e1'},barWidth:11},
    {name:'__L_D0__',type:'bar',data:__JS_HY_T__,itemStyle:{color:C_RED},barWidth:11}
  ]
});

mk('c_perf',{
  tooltip:{trigger:'axis',valueFormatter:function(v){return v+'%'}},
  grid:{left:100,right:56,top:16,bottom:28},
  xAxis:Object.assign({type:'value',axisLabel:{formatter:'{value}%'}},AX),
  yAxis:{type:'category',data:__JS_PF_NAME__,axisLine:{lineStyle:{color:'#d1d5db'}},
    axisLabel:{color:'#6b7280',fontSize:9,interval:0},splitLine:{show:false}},
  series:[{type:'bar',data:__JS_PF_PCT__,barWidth:9,
    itemStyle:{color:function(p){return p.value>=0?C_RED:C_GRN}},
    label:{show:true,position:'right',fontSize:10,color:'#9ca3af',
      formatter:function(p){return p.value.toFixed(1)}}}]
});

mk('c_ts',{
  tooltip:{trigger:'axis'},legend:{top:3,left:'center',textStyle:{color:'#6b7280'}},
  grid:{left:50,right:20,top:52,bottom:28},
  xAxis:Object.assign({type:'category',data:__JS_TS_NAME__},AX),
  yAxis:Object.assign({type:'value'},AX),
  series:[
    {name:'__L_D1__',type:'bar',data:__JS_TS_Y__,itemStyle:{color:'#cbd5e1'},barWidth:24},
    {name:'__L_D0__',type:'bar',data:__JS_TS_T__,itemStyle:{color:C_RED},barWidth:24}
  ]
});
</script>
</body>
</html>
"""
# ---- 东财与同花顺涨停池差额（北交所口径）----
_em_tc = (B["dates"][D0]["em_ZT"] or {}).get("tc") or 0
P("ZT_D_EM", _em_tc)
P("ZT_EM_DIFF", _em_tc - s0["zt"])
_em_codes = set(x["c"] for x in (B["dates"][D0]["em_ZT"] or {}).get("pool") or [])
_ths_codes = set(x["code"] for x in ((B["dates"][D0]["ths_zt"] or {}).get("info") or []))
_bj = sorted(_em_codes - _ths_codes)
assert all(c.startswith("92") for c in _bj), f"北交所差额断言失败: _bj={_bj}"
print("ths pool:", len(_ths_codes), "em tc:", _em_tc, "bj_diff:", _bj)

# ---- 跌停池差额 ----
_em_dt = (B["dates"][D0].get("em_DT") or {}).get("tc") or 0
P("DT_EM_T", _em_dt)
P("DT_EM_DIFF", _em_dt - s0["dt"])
print("em_DT tc:", _em_dt, "| ths dt:", s0["dt"], "| 明细池(实测):", DT_N)

# ---- 补充占位符 ----
P("DT_HY_CS", _dt_hy_cnt.get("通信设备", 0))
P("DT_HY_YJ", _dt_hy_cnt.get("元件", 0))
P("DT_HY_CS_YJ", _dt_hy_cnt.get("通信设备", 0) + _dt_hy_cnt.get("元件", 0))
P("DT_TOUCH_D", "{:+d}".format(s0["limit_down_count"]["today"]["history_num"] - s0["limit_down_count"]["yesterday"]["history_num"]))
P("DT_LOCK_D2", "{:.0f}".format(s1["limit_down_count"]["yesterday"]["rate"] * 100))
P("DT_TOUCH_D2", s1["limit_down_count"]["yesterday"]["history_num"])
_ROBOT_CORE = [r for r in robot if not any(k in (r["name"] or "") for k in ["吉鑫科技", "九阳股份"])]
P("ROBOT_CORE_N", len(_ROBOT_CORE))
P("ROBOT_WIDE_N", len(robot) - 1)
_AUTO_CORE = [r for r in auto if r["name"] != "雪龙集团"]
P("AUTO_CORE_N", len(_AUTO_CORE))
P("TH_TOP1", esc(theme_cnt[0]["name"])); P("TH_TOP1_N", theme_cnt[0]["n"])
P("TH_TOP2", esc(theme_cnt[1]["name"])); P("TH_TOP2_N", theme_cnt[1]["n"])
P("TH_TOP3", esc(theme_cnt[2]["name"])); P("TH_TOP3_N", theme_cnt[2]["n"])
P("DT_HY_CS_YJ2", "{:.0f}".format((_dt_hy_cnt.get("通信设备", 0) + _dt_hy_cnt.get("元件", 0)) / DT_N * 100) if DT_N else "0")
# 上涨行业合计成交额（WeStock turnover 字段单位为万元 → 亿）
_SEC_UP_TURN = 673876 + 571036 + 525443 + 267962 + 918053
P("SEC_UP_TURN", "{:.0f}".format(_SEC_UP_TURN / 1e4))
P("SEC_UP_TURN_SHARE", "{:.1f}".format(_SEC_UP_TURN / 1e4 / amt_today * 100))
P("SEC_YJ_TURN", "{:.0f}".format(9967975 / 1e4))
P("SEC_BDT_TURN", "{:.0f}".format(22722791 / 1e4))
P("SEC_XFDZ_TURN", "{:.0f}".format(4767947 / 1e4))
P("FUND_EX_AVG", "{:.2f}".format(fund_ex / max(s0["zt"] - 1, 1)))
P("TS_TOP", ts0.get("尾盘", 0))
_amt_top_lb = lb_all[0]["lbc"] if lb_all else 0
P("PERF_MIN_LB_CTX", "最高板" if not maxb_y else ("昨 %d 板" % maxb_y))

HTML = HTML_T
for k, v in V.items():
    HTML = HTML.replace(k, v)

fp = os.path.join(REP, f"涨停复盘对比-{D0}.html")
with open(fp, "w", encoding="utf-8") as f:
    f.write(HTML)
left = re.findall(r"__[A-Z_0-9]+__", HTML)
print("saved ->", fp, len(HTML) // 1024, "KB")
print("placeholder residue:", sorted(set(left)))
