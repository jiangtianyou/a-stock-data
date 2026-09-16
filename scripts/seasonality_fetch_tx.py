# -*- coding: utf-8 -*-
"""
A股季节性研究 - 数据抓取(腾讯财经通道)
说明: 东财 push2his 在本机被限流, 改用腾讯 web.ifzq.gtimg.cn 月线接口
      param={sym},month,1990-01-01,2026-12-31,600,qfq
输出: out/seasonality_raw.json  (与 analyze 脚本约定一致)
"""
import sys, os, json, time, random
import requests

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")

S = requests.Session()
S.trust_env = False
S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
                  "Referer": "https://gu.qq.com/"})

# ---- 品种池: (代码, 名称, 分组) ----
POOL = [
    # ===== 宽基 =====
    ("sh000001", "上证指数", "宽基"), ("sz399001", "深证成指", "宽基"),
    ("sh000300", "沪深300", "宽基"), ("sh000905", "中证500", "宽基"),
    ("sh000852", "中证1000", "宽基"), ("sz399006", "创业板指", "宽基"),
    ("sh000688", "科创50", "宽基"), ("sh000016", "上证50", "宽基"),
    ("sz399005", "中小100", "宽基"), ("sh000010", "上证180", "宽基"),
    ("sh000009", "上证380", "宽基"), ("sh000903", "中证A100", "宽基"),
    ("sz399102", "创业板综", "宽基"), ("sh000985", "中证全指", "宽基"),
    ("sh000979", "大宗商品", "宽基"),
    # ===== 红利/风格 =====
    ("sh000922", "中证红利", "风格"), ("sh000015", "上证红利", "风格"),
    ("sh000821", "300红利", "风格"), ("sh000968", "300周期", "风格"),
    ("sh000958", "创业成长", "风格"), ("sh000912", "300成长", "风格"),
    # ===== 中证全指一级行业 =====
    ("sh000986", "全指能源", "行业"), ("sh000987", "全指材料", "行业"),
    ("sh000988", "全指工业", "行业"), ("sh000989", "全指可选", "行业"),
    ("sh000990", "全指消费", "行业"), ("sh000991", "全指医药", "行业"),
    ("sh000992", "全指金融", "行业"), ("sh000993", "全指信息", "行业"),
    ("sh000994", "全指通信", "行业"), ("sh000995", "全指公用", "行业"),
    # ===== 中证800行业 =====
    ("sh000928", "中证能源", "行业"), ("sh000929", "800材料", "行业"),
    ("sh000930", "800工业", "行业"), ("sh000931", "800可选", "行业"),
    ("sh000932", "中证消费", "行业"), ("sh000933", "中证医药", "行业"),
    ("sh000934", "中证金融", "行业"), ("sh000935", "中证信息", "行业"),
    ("sh000936", "800通信", "行业"), ("sh000937", "800公用", "行业"),
    # ===== 细分行业 =====
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
    # ===== 主题 =====
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


def get(url, params, min_interval=0.55, retries=4):
    for i in range(retries):
        w = min_interval - (time.time() - _last[0])
        if w > 0:
            time.sleep(w + random.uniform(0.05, 0.2))
        try:
            _last[0] = time.time()
            r = S.get(url, params=params, timeout=20)
            if r.status_code == 200 and r.text.strip():
                return r.json()
        except Exception as e:
            if i == retries - 1:
                print("  失败:", type(e).__name__)
        time.sleep(0.8 * (2 ** i))
    return None


def fetch_monthly(sym):
    r = get("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get",
            {"param": f"{sym},month,1990-01-01,2026-12-31,600,qfq"})
    if not r:
        return None
    d = (r.get("data") or {}).get(sym) or {}
    kl = d.get("qfqmonth") or d.get("month") or []
    if not kl:
        return None
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
    res, fail = [], []
    for i, (sym, name, grp) in enumerate(POOL, 1):
        rows = fetch_monthly(sym)
        if rows and len(rows) >= 60:
            res.append({"secid": sym, "name": name, "group": grp,
                        "em_code": sym, "em_name": name, "rows": rows})
            print(f"  [{i:>2}/{len(POOL)}] {name:<10} {len(rows):>4}根  {rows[0]['d']} -> {rows[-1]['d']}")
        else:
            fail.append(name)
            print(f"  [{i:>2}/{len(POOL)}] {name:<10} 数据不足")

    out = {"fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
           "source": "tencent web.ifzq.gtimg.cn (month, qfq)",
           "count": len(res), "items": res}
    with open(os.path.join(OUT, "seasonality_raw.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print(f"\n完成: 成功 {len(res)} / 失败 {len(fail)} {fail if fail else ''}")


if __name__ == "__main__":
    main()
