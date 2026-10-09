# -*- coding: utf-8 -*-
"""抖音评论提及标的 —— 9月表现行情抓取（腾讯日线，前复权）"""
import json, os, sys, time, urllib.request, urllib.error

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "out")

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

POOL = [
    ("莲花控股", "sh600186"),
    ("百合花", "sh603823"),
    ("百花医药", "sh600721"),
    ("远东股份", "sh600869"),
    ("紫光股份", "sz000938"),
    ("中国巨石", "sh600176"),
    ("亨通光电", "sh600487"),
    ("西部矿业", "sh601168"),
    ("青山纸业", "sh600103"),
    ("紫金矿业", "sh601899"),
    ("浪潮信息", "sz000977"),
    ("杭电股份", "sh603618"),
    ("星网锐捷", "sz002396"),
    ("平潭发展", "sz000592"),
    ("贵州茅台", "sh600519"),
    ("英维克", "sz002837"),
    ("中科曙光", "sh603019"),
    ("九安医疗", "sz002432"),
    ("药明康德", "sh603259"),
    ("兆易创新", "sh603986"),
    ("德明利", "sz001309"),
    ("我爱我家", "sz000560"),
    ("沃特股份", "sz002886"),
    ("上海洗霸", "sh603200"),
    ("江西铜业", "sh600362"),
    ("湖南白银", "sz002716"),
    ("白银有色", "sh601212"),
    ("太极实业", "sh600667"),
    ("立讯精密", "sz002475"),
    ("京东方A", "sz000725"),
    ("阳光电源", "sz300274"),
    ("中钨高新", "sz000657"),
    ("金螳螂", "sz002081"),
    ("特变电工", "sh600089"),
    ("中国中免", "sh601888"),
    ("盈新发展", "sz000620"),
    ("赤天化", "sh600227"),
    ("牧原股份", "sz002714"),
    ("国瓷材料", "sz300285"),
    ("长盈精密", "sz300115"),
    ("歌尔股份", "sz002241"),
    ("风华高科", "sz000636"),
    ("先导智能", "sz300450"),
    ("赣锋锂业", "sz002460"),
    ("天齐锂业", "sz002466"),
    ("多氟多", "sz002407"),
    ("巨化股份", "sh600160"),
    ("红星发展", "sh600367"),
    ("金牛化工", "sh600722"),
    ("红四方", "sh603395"),
    ("三安光电", "sh600703"),
    ("光迅科技", "sz002281"),
    ("长飞光纤", "sh601869"),
    ("中天科技", "sh600522"),
    ("永鼎股份", "sh600105"),
    ("利通电子", "sh603629"),
    ("山子高科", "sz000981"),
    ("剑桥科技", "sh603083"),
    ("麦格米特", "sz002851"),
    ("盛达资源", "sz000603"),
    ("兴业银锡", "sz000426"),
    ("山东黄金", "sh600547"),
    ("中国长城", "sz000066"),
    ("深科技", "sz000021"),
    ("长电科技", "sh600584"),
    ("通富微电", "sz002156"),
    ("工业富联", "sh601138"),
    ("协鑫能科", "sz002015"),
    ("高能环境", "sh603588"),
    ("南大光电", "sz300346"),
    ("雅克科技", "sz002409"),
    ("大北农", "sz002385"),
    ("新赛股份", "sh600540"),
    ("敦煌种业", "sh600354"),
    ("隆平高科", "sz000998"),
    ("海南橡胶", "sh601118"),
    ("恒瑞医药", "sh600276"),
    ("哈药股份", "sh600664"),
    ("中国船舶", "sh600150"),
    ("金风科技", "sz002202"),
    ("宗申动力", "sz001696"),
    ("诺德股份", "sh600110"),
    ("融捷股份", "sz002192"),
    ("西藏矿业", "sz000762"),
    ("若羽臣", "sz003010"),
    ("遥望科技", "sz002291"),
    ("天娱数科", "sz002354"),
    ("蓝色光标", "sz300058"),
    ("中文在线", "sz300364"),
    ("拓维信息", "sz002261"),
]

BENCH = [
    ("上证指数", "sh000001"),
    ("深证成指", "sz399001"),
    ("创业板指", "sz399006"),
    ("科创50", "sh000688"),
    ("中证1000", "sh000852"),
    ("北证50", "bj899050"),
]


def fetch(sym, start="", end="", n=120):
    # 不传日期区间：带区间参数时盘后最新一根会缺失
    url = ("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
           "?param=%s,day,,,%d,qfq" % (sym, n))
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=UA)
            raw = _opener.open(req, timeout=20).read().decode("utf-8", "ignore")
            js = json.loads(raw)
            node = js.get("data", {}).get(sym, {})
            rows = node.get("qfqday") or node.get("day") or []
            if rows:
                return rows
        except Exception as e:
            print("  ! %s attempt%d %s" % (sym, attempt, e))
        time.sleep(1.2 + attempt * 1.5)
    return []


def main():
    res = {}
    for name, sym in POOL + BENCH:
        rows = fetch(sym)
        if not rows:
            print("MISS %s %s" % (name, sym))
            continue
        res[sym] = {"name": name, "rows": rows}
        print("OK   %-8s %-10s %d bars  %s -> %s" %
              (name, sym, len(rows), rows[0][0], rows[-1][0]))
        time.sleep(0.25)

    dst = os.path.join(OUT, "dy_kline.json")
    tmp = dst + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, dst)
    print("saved ->", dst, "items=", len(res))


if __name__ == "__main__":
    main()
