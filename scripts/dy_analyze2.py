# -*- coding: utf-8 -*-
"""抖音评论标的 —— 频次 × 9月表现 交叉分析"""
import json, os, sys
from collections import OrderedDict

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "out")

# 评论提及频次（来自 SQL LIKE 精确统计，含主评论+回复文本）
FREQ = {
    "莲花控股": 241, "百合花": 50, "远东股份": 37, "紫光股份": 29, "中国巨石": 26,
    "湖南白银": 8, "白银有色": 10, "亨通光电": 24, "百花医药": 24, "西部矿业": 23,
    "青山纸业": 21,
    "紫金矿业": 20, "浪潮信息": 18, "杭电股份": 17, "星网锐捷": 15, "平潭发展": 15,
    "贵州茅台": 14, "金螳螂": 14, "西藏矿业": 14, "沃特股份": 13, "盛达资源": 13,
    "协鑫能科": 13, "太极实业": 13, "药明康德": 12, "特变电工": 12, "江西铜业": 12,
    "金风科技": 12, "中科曙光": 11, "哈药股份": 11, "英维克": 10, "风华高科": 10,
    "我爱我家": 10, "立讯精密": 10, "上海洗霸": 10, "利通电子": 10, "京东方A": 10,
    "德明利": 9, "恒瑞医药": 9, "长飞光纤": 9, "阳光电源": 9, "楚天龙": 9,
    "宗申动力": 9, "九安医疗": 8, "盈新发展": 8, "歌尔股份": 8, "红星发展": 8,
    "中钨高新": 7, "赤天化": 7, "中国长城": 7, "长电科技": 7, "工业富联": 7,
    "牧原股份": 7, "国瓷材料": 7, "金牛化工": 7, "红四方": 7, "高争民爆": 7,
    "东山精密": 7, "兆易创新": 6, "三安光电": 6, "步步高": 6, "新赛股份": 6,
    "敦煌种业": 6, "TCL科技": 6, "欧菲光": 6, "天娱数科": 6,
    "深科技": 5, "光迅科技": 5, "永鼎股份": 5, "招金黄金": 5, "铜陵有色": 5,
    "艾艾精工": 5, "胜宏科技": 5, "工商银行": 5, "蓝色光标": 5,
    "先导智能": 4, "通富微电": 4, "高能环境": 4, "巨化股份": 4, "多氟多": 4,
    "雅克科技": 4, "隆平高科": 4, "领益智造": 4, "长盈精密": 4, "拓维信息": 4,
    "巨人网络": 4, "海南橡胶": 4, "神农种业": 4, "金健米业": 4, "中国中免": 4,
    "西安饮食": 4, "剑桥科技": 4,
    "中国船舶": 3, "烽火通信": 3, "生益科技": 3, "南大光电": 3, "麦格米特": 3,
    "天齐锂业": 3, "大北农": 3, "水晶光电": 3,
    "中天科技": 2, "天孚通信": 2, "山东黄金": 2, "兴业银锡": 2, "赣锋锂业": 2,
    "融捷股份": 2, "中文在线": 2, "遥望科技": 2, "若羽臣": 2,
    "北方稀土": 1,
}

# 板块归属（评论语境下的热词分组）
SECTOR = OrderedDict([
    ("算力·国产服务器", ["浪潮信息", "中科曙光", "紫光股份", "工业富联", "拓维信息",
                    "星网锐捷", "利通电子", "协鑫能科"]),
    ("光通信·光纤", ["亨通光电", "中天科技", "长飞光纤", "光迅科技", "永鼎股份",
                  "剑桥科技", "天孚通信", "烽火通信"]),
    ("PCB·覆铜板·材料", ["中国巨石", "国瓷材料", "沃特股份", "风华高科", "生益科技",
                     "雅克科技", "南大光电"]),
    ("存储", ["兆易创新", "德明利", "深科技"]),
    ("半导体·封测", ["三安光电", "通富微电", "长电科技"]),
    ("液冷·散热", ["英维克", "麦格米特"]),
    ("有色·铜", ["江西铜业", "紫金矿业", "西部矿业", "铜陵有色"]),
    ("贵金属·白银黄金", ["山东黄金", "湖南白银", "白银有色", "盛达资源", "兴业银锡"]),
    ("小金属·钨稀土", ["中钨高新", "北方稀土"]),
    ("化工·材料", ["巨化股份", "多氟多", "金牛化工", "红星发展", "红四方", "赤天化"]),
    ("锂电·锂矿", ["赣锋锂业", "天齐锂业", "融捷股份", "西藏矿业"]),
    ("农业·种业", ["敦煌种业", "隆平高科", "大北农", "新赛股份", "海南橡胶", "牧原股份"]),
    ("医药·创新药", ["药明康德", "恒瑞医药", "哈药股份", "百花医药", "九安医疗"]),
    ("AI应用·传媒", ["蓝色光标", "中文在线", "遥望科技", "天娱数科", "若羽臣"]),
    ("消费电子·面板", ["京东方A", "立讯精密", "歌尔股份", "长盈精密", "水晶光电", "欧菲光"]),
    ("地产链·家居", ["我爱我家", "金螳螂"]),
    ("电力设备·新能源", ["特变电工", "金风科技", "宗申动力", "阳光电源", "先导智能"]),
    ("消费·白马", ["贵州茅台", "中国中免"]),
    ("军工·船舶", ["中国船舶"]),
])

with open(os.path.join(OUT, "dy_perf.json"), encoding="utf-8") as f:
    PERF = json.load(f)
P = {r["name"]: r for r in PERF["stocks"]}
IDX = PERF["indexes"]
SH = IDX["sh000001"]["sep_ret"]


def ret(name):
    r = P.get(name)
    return r["ret"] if r else None


rows = []
for name, fr in FREQ.items():
    r = P.get(name)
    if not r:
        continue
    rows.append({"name": name, "freq": fr, "ret": r["ret"], "excess": r["excess"],
                 "mdd": r["mdd"], "dd_peak": r["dd_from_peak"], "hi_ret": r["ret_if_peak"],
                 "zt": r["zt"], "amp_chg": r["amp_chg"], "last_c": r["last_c"],
                 "sym": r["sym"]})
rows.sort(key=lambda x: -x["freq"])


def band_stats(lo, hi):
    g = [r for r in rows if lo <= r["freq"] <= hi]
    if not g:
        return None
    n = len(g)
    return {"n": n, "avg": sum(r["ret"] for r in g) / n,
            "med": sorted(r["ret"] for r in g)[n // 2],
            "win": sum(1 for r in g if r["ret"] > 0) / n,
            "names": [r["name"] for r in g]}


bands = OrderedDict([
    ("≥30 次（超级热门）", band_stats(30, 999)),
    ("15–29 次（高热度）", band_stats(15, 29)),
    ("7–14 次（中热度）", band_stats(7, 14)),
    ("<7 次（低热度）", band_stats(0, 6)),
])

# Spearman 秩相关（频次 vs 收益）
def spearman(xs, ys):
    def rank(v):
        s = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(s):
            j = i
            while j + 1 < len(s) and v[s[j + 1]] == v[s[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[s[k]] = avg
            i = j + 1
        return r
    rx, ry = rank(xs), rank(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    cov = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    vx = sum((a - mx) ** 2 for a in rx) ** 0.5
    vy = sum((a - my) ** 2 for a in ry) ** 0.5
    return cov / (vx * vy) if vx and vy else 0


rho = spearman([r["freq"] for r in rows], [r["ret"] for r in rows])

sector_rows = []
for sec, members in SECTOR.items():
    vals = [(m, ret(m)) for m in members if ret(m) is not None]
    if not vals:
        continue
    avg = sum(v for _, v in vals) / len(vals)
    fsum = sum(FREQ.get(m, 0) for m, _ in vals)
    win = sum(1 for _, v in vals if v > 0)
    sector_rows.append({"sector": sec, "n": len(vals), "avg": avg,
                        "freq": fsum, "win": win,
                        "members": [{"name": m, "ret": v, "freq": FREQ.get(m, 0)} for m, v in
                                    sorted(vals, key=lambda x: -x[1])]})
sector_rows.sort(key=lambda x: -x["avg"])

out = {"rows": rows, "bands": bands, "rho": rho, "sectors": sector_rows,
       "indexes": IDX, "sh_ret": SH,
       "freq_total": sum(FREQ.values())}
with open(os.path.join(OUT, "dy_cross.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("样本标的数 =", len(rows), " 频次合计 =", sum(FREQ.values()))
print("Spearman(频次, 9月收益) = %.3f" % rho)
print("\n== 分档 ==")
for k, v in bands.items():
    if v:
        print("  %-18s n=%2d  均值 %+7.2f%%  中位 %+7.2f%%  正收益占比 %5.1f%%" %
              (k, v["n"], v["avg"] * 100, v["med"] * 100, v["win"] * 100))
print("\n== 板块（按 9 月等权收益排序） ==")
for s in sector_rows:
    print("  %-16s n=%d  等权 %+7.2f%%  提及合计 %4d  上涨 %d/%d" %
          (s["sector"], s["n"], s["avg"] * 100, s["freq"], s["win"], s["n"]))
print("\n== 热度 Top15 ==")
for r in rows[:15]:
    print("  %-9s %4d次  9月 %+7.2f%%  超额 %+7.2f%%  距峰 %7.2f%%  涨停%d次" %
          (r["name"], r["freq"], r["ret"] * 100, r["excess"] * 100,
           r["dd_peak"] * 100, r["zt"]))
print("\n== 9 月上涨的标的（全部，按收益） ==")
for r in sorted(rows, key=lambda x: -x["ret"]):
    if r["ret"] > 0:
        print("  %-9s %4d次  9月 %+7.2f%%" % (r["name"], r["freq"], r["ret"] * 100))
