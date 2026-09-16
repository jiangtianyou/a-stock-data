# -*- coding: utf-8 -*-
"""
PCB 板块 8 月以来走势复盘 - 日线抓取
通道: 腾讯 web.ifzq.gtimg.cn (day, qfq)  —— 东财 push2his 本机限流
字段: [日期, 开, 收, 高, 低, 量(手)]   <-- 开-收-高-低
输出: out/pcb_raw.json
"""
import sys, os, json, time, random
import requests

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")

S = requests.Session()
S.trust_env = False
S.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://gu.qq.com/",
})

# (代码, 名称, 分类)
POOL = [
    # ---- PCB 制造 ----
    ("sz002463", "沪电股份", "PCB制造"),
    ("sz300476", "胜宏科技", "PCB制造"),
    ("sz002916", "深南电路", "PCB制造"),
    ("sz002384", "东山精密", "PCB制造"),
    ("sh603228", "景旺电子", "PCB制造"),
    ("sz002938", "鹏鼎控股", "PCB制造"),
    ("sz002436", "兴森科技", "PCB制造"),
    ("sh603920", "世运电路", "PCB制造"),
    ("sz001389", "广合科技", "PCB制造"),
    ("sh603936", "博敏电子", "PCB制造"),
    ("sz002815", "崇达技术", "PCB制造"),
    ("sz300814", "中富电路", "PCB制造"),
    ("sz300852", "四会富仕", "PCB制造"),
    ("sz002913", "奥士康",   "PCB制造"),
    ("sh603328", "依顿电子", "PCB制造"),
    ("sz000823", "超声电子", "PCB制造"),
    ("sh600601", "方正科技", "PCB制造"),
    ("sz002134", "天津普林", "PCB制造"),
    ("sz300657", "弘信电子", "PCB制造"),
    ("sh688183", "生益电子", "PCB制造"),
    ("sz300739", "明阳电路", "PCB制造"),
    ("sz300903", "科翔股份", "PCB制造"),
    ("sz301041", "金百泽",   "PCB制造"),
    ("sz301628", "强达电路", "PCB制造"),
    ("sh605258", "协和电子", "PCB制造"),
    ("sh688655", "迅捷兴",   "PCB制造"),
    # ---- 上游覆铜板/材料 ----
    ("sh600183", "生益科技", "覆铜板"),
    ("sh688519", "南亚新材", "覆铜板"),
    ("sh603186", "华正新材", "覆铜板"),
    ("sz002636", "金安国纪", "覆铜板"),
    # ---- 设备/耗材 ----
    ("sz301200", "大族数控", "PCB设备"),
    ("sh688630", "芯碁微装", "PCB设备"),
    ("sz301377", "鼎泰高科", "PCB设备"),
    ("sh688603", "天承科技", "PCB设备"),
    # ---- 基准 ----
    ("sh000001", "上证指数", "基准"),
    ("sh000300", "沪深300", "基准"),
    ("sz399006", "创业板指", "基准"),
    ("sh000985", "中证全指", "基准"),
    ("sh000993", "中证全指信息技术", "基准"),
    ("sh000994", "中证全指通信", "基准"),
    ("sz399811", "中证半导体", "基准"),
]

START, END = "2026-04-01", "2026-12-31"

_last = [0.0]


def get(params, retries=5):
    for i in range(retries):
        w = 0.35 - (time.time() - _last[0])
        if w > 0:
            time.sleep(w + random.uniform(0.03, 0.15))
        try:
            _last[0] = time.time()
            r = S.get("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get",
                      params=params, timeout=20)
            if r.status_code == 200 and r.text.strip():
                return r.json()
        except Exception:
            pass
        time.sleep(0.6 * (2 ** i))
    return None


def fetch_daily(sym):
    r = get({"param": f"{sym},day,{START},{END},600,qfq"})
    if not r:
        return None
    d = (r.get("data") or {}).get(sym) or {}
    kl = d.get("qfqday") or d.get("day") or []
    rows = []
    for k in kl:
        try:
            rows.append({"d": k[0], "o": float(k[1]), "c": float(k[2]),
                         "h": float(k[3]), "l": float(k[4]), "v": float(k[5])})
        except Exception:
            continue
    return rows or None


def main():
    os.makedirs(OUT, exist_ok=True)
    res, fail = [], []
    for i, (sym, name, grp) in enumerate(POOL, 1):
        rows = fetch_daily(sym)
        if rows and len(rows) >= 100:
            res.append({"secid": sym, "name": name, "group": grp, "rows": rows})
            print(f"  [{i:>2}/{len(POOL)}] {name:<10} {len(rows):>4}根  "
                  f"{rows[0]['d']} -> {rows[-1]['d']}  收{rows[-1]['c']}", flush=True)
        else:
            fail.append(name)
            print(f"  [{i:>2}/{len(POOL)}] {name:<10} 数据不足", flush=True)
        time.sleep(0.1)

    out = {"fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
           "source": "tencent web.ifzq.gtimg.cn (day, qfq)",
           "count": len(res), "items": res}
    with open(os.path.join(OUT, "pcb_raw.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print(f"\n完成: 成功 {len(res)} / 失败 {len(fail)} {fail if fail else ''}")


if __name__ == "__main__":
    main()
