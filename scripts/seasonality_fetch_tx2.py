# -*- coding: utf-8 -*-
"""
A股季节性研究 - 数据抓取 v2
通道1: data.gtimg.cn/flashdata/hushen/monthly/{sym}.js  (轻量, 无限流, 无复权)
通道2: web.ifzq.gtimg.cn/appstock/app/fqkline/get (月线qfq, 全历史, 有限流)
策略: 两通道都尝试, 同一品种取历史起点更早/行数更多者
输出: out/seasonality_raw.json
"""
import sys, os, json, time, random, re
import requests

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")

S = requests.Session()
S.trust_env = False
S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
                  "Referer": "https://gu.qq.com/"})

POOL = [
    ("sh000001", "上证指数", "宽基"), ("sz399001", "深证成指", "宽基"),
    ("sh000300", "沪深300", "宽基"), ("sh000905", "中证500", "宽基"),
    ("sh000852", "中证1000", "宽基"), ("sz399006", "创业板指", "宽基"),
    ("sh000688", "科创50", "宽基"), ("sh000016", "上证50", "宽基"),
    ("sz399005", "中小100", "宽基"), ("sh000010", "上证180", "宽基"),
    ("sh000009", "上证380", "宽基"), ("sh000903", "中证A100", "宽基"),
    ("sz399102", "创业板综", "宽基"), ("sh000985", "中证全指", "宽基"),
    ("sh000979", "大宗商品", "宽基"),
    ("sh000922", "中证红利", "风格"), ("sh000015", "上证红利", "风格"),
    ("sh000821", "300红利", "风格"), ("sh000968", "300周期", "风格"),
    ("sh000958", "创业成长", "风格"), ("sh000912", "300成长", "风格"),
    ("sh000986", "全指能源", "行业"), ("sh000987", "全指材料", "行业"),
    ("sh000988", "全指工业", "行业"), ("sh000989", "全指可选", "行业"),
    ("sh000990", "全指消费", "行业"), ("sh000991", "全指医药", "行业"),
    ("sh000992", "全指金融", "行业"), ("sh000993", "全指信息", "行业"),
    ("sh000994", "全指通信", "行业"), ("sh000995", "全指公用", "行业"),
    ("sh000928", "中证能源", "行业"), ("sh000929", "800材料", "行业"),
    ("sh000930", "800工业", "行业"), ("sh000931", "800可选", "行业"),
    ("sh000932", "中证消费", "行业"), ("sh000933", "中证医药", "行业"),
    ("sh000934", "中证金融", "行业"), ("sh000935", "中证信息", "行业"),
    ("sh000936", "800通信", "行业"), ("sh000937", "800公用", "行业"),
    ("sh000807", "食品饮料", "细分"), ("sh000808", "医药生物", "细分"),
    ("sh000811", "细分有色", "细分"), ("sh000813", "细分化工", "细分"),
    ("sh000814", "细分医药", "细分"), ("sh000815", "细分食品", "细分"),
    ("sh000816", "细分地产", "细分"), ("sh000818", "细分金融", "细分"),
    ("sh000819", "有色金属", "细分"), ("sh000820", "煤炭指数", "细分"),
    ("sh000823", "800有色", "细分"), ("sh000949", "中证农业", "细分"),
    ("sh000977", "内地低碳", "细分"), ("sh000998", "中证TMT", "细分"),
    ("sz399231", "农林指数", "细分"), ("sz399441", "生物医药", "细分"),
    ("sz399608", "科技100", "细分"), ("sz399618", "深证医药", "细分"),
    ("sz399619", "深证金融", "细分"), ("sz399811", "CSSW电子", "细分"),
    ("sz399814", "大农业", "细分"),
    ("sz399997", "中证白酒", "主题"), ("sz399987", "中证酒", "主题"),
    ("sz399998", "中证煤炭", "主题"), ("sz399986", "中证银行", "主题"),
    ("sz399975", "证券公司", "主题"), ("sz399967", "中证军工", "主题"),
    ("sz399959", "军工指数", "主题"), ("sz399973", "中证国防", "主题"),
    ("sz399989", "中证医疗", "主题"), ("sz399808", "中证新能", "主题"),
    ("sz399976", "CS新能车", "主题"), ("sh000827", "中证环保", "主题"),
    ("sh000978", "医药100", "主题"), ("sz399971", "中证传媒", "主题"),
    ("sz399970", "移动互联", "主题"), ("sz399812", "养老产业", "主题"),
    ("sz399813", "中证国安", "主题"), ("sz399995", "基建工程", "主题"),
    ("sz399996", "智能家居", "主题"),
]

_last = [0.0]


def get(url, params=None, min_interval=0.8, retries=3):
    for i in range(retries):
        w = min_interval - (time.time() - _last[0])
        if w > 0:
            time.sleep(w + random.uniform(0.05, 0.25))
        try:
            _last[0] = time.time()
            r = S.get(url, params=params, timeout=20)
            if r.status_code == 200 and r.text.strip():
                return r
        except Exception:
            pass
        time.sleep(0.8 * (2 ** i))
    return None


def fetch_flash(sym):
    """通道1: flashdata 月线"""
    r = get(f"https://data.gtimg.cn/flashdata/hushen/monthly/{sym}.js", min_interval=0.35)
    if not r:
        return None
    r.encoding = "gbk"
    txt = r.text
    m = re.search(r'="(.*?)";', txt, re.S)
    body = m.group(1) if m else txt
    rows = []
    for line in body.split("\n"):
        p = line.strip().split()
        if len(p) < 6:
            continue
        d = p[0]
        if len(d) != 8 or not d.isdigit():
            continue
        try:
            # 格式: 日期 开 高 低 收 量
            rows.append({"d": f"{d[:4]}-{d[4:6]}-{d[6:]}", "o": float(p[1]),
                         "h": float(p[2]), "l": float(p[3]), "c": float(p[4])})
        except Exception:
            continue
    return rows or None


def fetch_fq(sym):
    """通道2: fqkline 月线(前复权)"""
    r = get("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get",
            {"param": f"{sym},month,1990-01-01,2026-12-31,600,qfq"}, min_interval=1.0)
    if not r:
        return None
    try:
        j = r.json()
    except Exception:
        return None
    d = (j.get("data") or {}).get(sym) or {}
    kl = d.get("qfqmonth") or d.get("month") or []
    rows = []
    for k in kl:
        try:
            rows.append({"d": k[0], "o": float(k[1]), "c": float(k[2]),
                         "h": float(k[3]), "l": float(k[4])})
        except Exception:
            continue
    return rows or None


def main():
    os.makedirs(OUT, exist_ok=True)
    res, notes = [], []
    for i, (sym, name, grp) in enumerate(POOL, 1):
        a = fetch_flash(sym)
        b = fetch_fq(sym)
        best, src = None, "-"
        for cand, tag in [(a, "flash"), (b, "fq")]:
            if cand and (best is None or len(cand) > len(best)):
                best, src = cand, tag
        if best and len(best) >= 48:
            best.sort(key=lambda x: x["d"])
            res.append({"secid": sym, "name": name, "group": grp,
                        "src": src, "rows": best})
            notes.append(f"  [{i:>2}/{len(POOL)}] {name:<10} {src:<6} {len(best):>4}根  {best[0]['d']} -> {best[-1]['d']}")
        else:
            notes.append(f"  [{i:>2}/{len(POOL)}] {name:<10} 无数据 (flash={len(a) if a else 0}, fq={len(b) if b else 0})")
        if i % 10 == 0:
            print("\n".join(notes[-10:]), flush=True)
    print("\n".join(notes[-(len(notes) % 10):]), flush=True)

    out = {"fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
           "source": "tencent flashdata + fqkline (monthly)",
           "count": len(res), "items": res}
    with open(os.path.join(OUT, "seasonality_raw.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print(f"\n完成: 成功 {len(res)}/{len(POOL)}")


if __name__ == "__main__":
    main()
