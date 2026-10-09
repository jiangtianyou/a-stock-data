# -*- coding: utf-8 -*-
"""生成《抖音评论区"9月翻倍股"提名盘后复盘》HTML"""
import json, os, re, sys, time
sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "out")
REP = os.path.join(ROOT, "reports")

cross = json.load(open(os.path.join(OUT, "dy_cross.json"), encoding="utf-8"))
perf = json.load(open(os.path.join(OUT, "dy_perf.json"), encoding="utf-8"))
kl = json.load(open(os.path.join(OUT, "dy_kline.json"), encoding="utf-8"))

rows = cross["rows"]
idx = cross["indexes"]
N = len(rows)
UP = [r for r in rows if r["ret"] > 0]
UP.sort(key=lambda x: -x["ret"])

tone = {
    "我爱我家": "被反复当作“地产翻倍”的调侃对象，也有人认真给出“地产超预期政策、盘子小”的理由",
    "平潭发展": "“下个月台湾要回来了”“因为业绩亏损”——典型的玩笑式提名",
    "中国船舶": "零星提及：“造船厂上下游的订单爆满，应该要起势”；也有人回“不如松发股份”",
    "敦煌种业": "“敦煌种业 绝对翻倍 已经挣啦百分之二十啦”",
    "高能环境": "“高能是我入市买的第一支股票，是个好公司，比较稳”",
    "药明康德": "被批评为“卖铲子的”、被拿来与恒瑞比较，属争议票",
    "上海洗霸": "“硫化物研发有中科院背景、体量小易炒作”——少数派逻辑",
    "先导智能": "仅被零星提及（“应该是先导”）",
    "剑桥科技": "光模块阵营中被问“还有救吗”，此前曾被当作“剑桥大学”调侃",
    "遥望科技": "零星提名（“遥望科技！！！”），属无人讨论的冷门票",
    "恒瑞医药": "被讽“已经沦落为杂毛”，多空分歧极大",
    "牧原股份": "“周期反转”“猪周期加小市值”",
}
for r in UP:
    r["tone"] = tone.get(r["name"], "")

lm = kl["sh600186"]["rows"]
lm = [x for x in lm if x[0] >= "2026-09-01"]
base_lh = next(x for x in kl["sh600186"]["rows"] if x[0] == "2026-08-31")
b = float(base_lh[2])
lh_hi = max(float(x[3]) for x in lm)
lh_last = float(lm[-1][2])
lh_hi_d = max(lm, key=lambda x: float(x[3]))[0]

data = {
    "top": [{"name": r["name"], "sym": r["sym"], "freq": r["freq"], "ret": r["ret"],
             "excess": r["excess"], "hi_ret": r["hi_ret"], "dd_peak": r["dd_peak"],
             "mdd": r["mdd"], "zt": r["zt"]} for r in rows[:20]],
    "scatter": [[r["freq"], round(r["ret"] * 100, 2), r["name"]] for r in rows],
    "bands": [{"name": k, "avg": v["avg"], "win": v["win"], "n": v["n"]}
              for k, v in cross["bands"].items() if v],
    "sectors": cross["sectors"],
    "winners": UP,
    "peak": [{"name": r["name"], "hi": r["hi_ret"], "ret": r["ret"]} for r in rows[:15]],
    "lianhua": {
        "dates": [x[0][5:] for x in lm],
        "closes": [float(x[2]) for x in lm],
        "pct": [round((float(x[2]) / b - 1) * 100, 2) for x in lm],
    },
    "senti": [
        ["翻倍（话题本身）", 263, "#2f6fed"],
        ["科技", 161, "#2f6fed"],
        ["消费", 59, "#2f6fed"],
        ["有色", 57, "#2f6fed"],
        ["铜", 52, "#5b6470"],
        ["被套/套牢/套住", 52, "#149e5c"],
        ["算力", 39, "#2f6fed"],
        ["液冷", 37, "#2f6fed"],
        ["黄金", 35, "#5b6470"],
        ["粮食/农业", 30, "#2f6fed"],
        ["满仓/全仓/梭哈", 27, "#149e5c"],
        ["化工", 26, "#5b6470"],
        ["光通信/光纤", 21, "#5b6470"],
        ["半导体", 21, "#5b6470"],
        ["消费电子", 21, "#5b6470"],
        ["量化（狙击）", 21, "#d9342b"],
        ["券商", 18, "#5b6470"],
        ["电力/电网", 18, "#5b6470"],
        ["月线死叉/MACD", 17, "#d9342b"],
        ["机器人", 17, "#5b6470"],
        ["锂电/锂矿", 16, "#5b6470"],
        ["存储", 16, "#5b6470"],
        ["军工", 15, "#5b6470"],
        ["美联储/加息", 14, "#d9342b"],
        ["C浪", 12, "#d9342b"],
    ],
}

bA = cross["bands"]["≥30 次（超级热门）"]
bD = cross["bands"]["<7 次（低热度）"]
sec = {s["sector"]: s for s in cross["sectors"]}
order = [s["sector"] for s in cross["sectors"]]


def rank_of(name):
    return order.index(name) + 1


peak15 = data["peak"]
peak_avg = sum(x["hi"] for x in peak15) / len(peak15)
last_avg = sum(x["ret"] for x in peak15) / len(peak15)

pct = lambda v: ("+" if v >= 0 else "") + "%.2f%%" % (v * 100)

mono = " → ".join("%s %.2f%%" % (k.split("（")[0], v["avg"] * 100)
                 for k, v in cross["bands"].items() if v)

rep = {
    "__GEN_TIME__": time.strftime("%Y-%m-%d %H:%M"),
    "__DATA_JSON__": json.dumps(data, ensure_ascii=False, separators=(",", ":")),
    "__N_STOCK__": str(N),
    "__N_UP__": str(len(UP)),
    "__WIN_RATE__": "%.1f" % (len(UP) / N * 100),
    "__BAND_A_AVG__": pct(bA["avg"]),
    "__BAND_A_EX__": pct(bA["avg"] - cross["sh_ret"]),
    "__BAND_D_N__": str(bD["n"]),
    "__BAND_D_AVG__": pct(bD["avg"]),
    "__BAND_D_WIN__": "%.0f%%" % (bD["win"] * 100),
    "__RHO__": "%.3f" % cross["rho"],
    "__BAND_MONO__": mono,
    "__SEC_AS_N__": str(sec["算力·国产服务器"]["n"]),
    "__SEC_AS_F__": str(sec["算力·国产服务器"]["freq"]),
    "__SEC_AS_AVG__": pct(sec["算力·国产服务器"]["avg"]),
    "__SEC_AS_WIN__": str(sec["算力·国产服务器"]["win"]),
    "__SEC_LC_AVG__": pct(sec["液冷·散热"]["avg"]),
    "__SEC_PM_AVG__": pct(sec["贵金属·白银黄金"]["avg"]),
    "__SEC_LI_AVG__": pct(sec["锂电·锂矿"]["avg"]),
    "__SEC_RANK_AS__": "第 %d / %d、第 %d、第 %d" % (
        rank_of("算力·国产服务器"), len(order), rank_of("PCB·覆铜板·材料"), rank_of("医药·创新药")),
    "__BEST1__": pct(UP[0]["ret"]),
    "__BEST2__": pct(UP[1]["ret"]),
    "__N_UP_LT10__": str(sum(1 for r in UP if r["freq"] < 10)),
    "__PEAK_AVG__": pct(peak_avg),
    "__LAST_AVG__": pct(last_avg),
    "__GIVEBACK__": "%.1f" % ((peak_avg - last_avg) * 100),
    "__LH_HI__": "%.2f 元（%s）" % (lh_hi, lh_hi_d[5:]),
    "__LH_LAST__": "%.2f 元" % lh_last,
    "__LH_RET__": pct(lh_last / b - 1),
}

tpl = open(os.path.join(REP, "_dy_tpl.html"), encoding="utf-8").read()
html = tpl
for k, v in rep.items():
    html = html.replace(k, v)

left = re.findall(r"__[A-Z_0-9]+__", html)
assert not left, "未替换占位符: %s" % set(left)

dst = os.path.join(REP, "抖音评论标的九月复盘-20260930.html")
open(dst, "w", encoding="utf-8").write(html)
print("OK ->", dst, len(html), "chars")
print("样本", N, "上涨", len(UP), "胜率 %.1f%%" % (len(UP) / N * 100))
print("rho", rep["__RHO__"], "|", rep["__BAND_MONO__"])
print("Top15 最高均值", rep["__PEAK_AVG__"], "月末均值", rep["__LAST_AVG__"], "回吐", rep["__GIVEBACK__"], "pct")
print("莲花: 最高", rep["__LH_HI__"], "末", rep["__LH_LAST__"], rep["__LH_RET__"])
