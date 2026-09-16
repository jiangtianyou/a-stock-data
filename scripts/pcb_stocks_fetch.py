# -*- coding: utf-8 -*-
"""PCB 代表性个股 - 扩充样本行情 + 实时基本面(市值/PE/PB/换手)"""
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

# 9 月活跃 / 媒体点名但此前未纳入的品种
NEW = [
    ("sh605058", "澳弘电子", "PCB制造"),
    ("sz301132", "满坤科技", "PCB制造"),
    ("sz002579", "中京电子", "PCB制造"),
    ("sz001232", "嘉立创",   "PCB制造"),
    ("sz301282", "金禄电子", "PCB制造"),
    ("sz301176", "逸豪新材", "覆铜板"),
    ("sz301251", "威尔高",   "PCB制造"),
]

# 全样本（含上一轮 34 只）用于抓实时基本面
ALL = NEW + [
    ("sz002463", "沪电股份"), ("sz300476", "胜宏科技"), ("sz002916", "深南电路"),
    ("sz002384", "东山精密"), ("sh603228", "景旺电子"), ("sz002938", "鹏鼎控股"),
    ("sz002436", "兴森科技"), ("sh603920", "世运电路"), ("sz001389", "广合科技"),
    ("sh603936", "博敏电子"), ("sz002815", "崇达技术"), ("sz300814", "中富电路"),
    ("sz300852", "四会富仕"), ("sz002913", "奥士康"),   ("sh603328", "依顿电子"),
    ("sz000823", "超声电子"), ("sh600601", "方正科技"), ("sz002134", "天津普林"),
    ("sz300657", "弘信电子"), ("sh688183", "生益电子"), ("sz300739", "明阳电路"),
    ("sz300903", "科翔股份"), ("sz301041", "金百泽"),   ("sz301628", "强达电路"),
    ("sh605258", "协和电子"), ("sh688655", "迅捷兴"),   ("sh600183", "生益科技"),
    ("sh688519", "南亚新材"), ("sh603186", "华正新材"), ("sz002636", "金安国纪"),
    ("sz301200", "大族数控"), ("sh688630", "芯碁微装"), ("sz301377", "鼎泰高科"),
    ("sh688603", "天承科技"),
]

# ---------- 1) 实时基本面 ----------
print("== 实时快照 (qt.gtimg.cn) ==")
codes = ",".join(s for s, *_ in ALL)
r = S.get("https://qt.gtimg.cn/q=" + codes, timeout=20)
r.encoding = "gbk"
snap = {}
sample_printed = False
for line in r.text.strip().split("\n"):
    if "=" not in line:
        continue
    body = line.split("=", 1)[1].strip().strip('";')
    f = body.split("~")
    if len(f) < 45:
        continue
    code = f[2]
    d = {
        "name": f[1], "price": f[3], "chg_pct": f[32],
        "turnover": f[38], "pe": f[39], "amp": f[43],
        "float_mv": f[44], "total_mv": f[45], "pb": f[46],
        "vol_ratio": f[49] if len(f) > 49 else "",
    }
    snap[code] = d
    if not sample_printed:
        print("  字段样例:", {i: v for i, v in enumerate(f[:50]) if i in (1, 2, 3, 32, 38, 39, 43, 44, 45, 46, 49)})
        sample_printed = True

print(f"  快照 {len(snap)} 条")

# ---------- 2) 新增品种日线 ----------
print("\n== 新增品种日线 ==")
_last = [0.0]


def get(params, retries=5):
    for i in range(retries):
        w = 0.35 - (time.time() - _last[0])
        if w > 0:
            time.sleep(w + random.uniform(0.03, 0.15))
        try:
            _last[0] = time.time()
            rr = S.get("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get", params=params, timeout=20)
            if rr.status_code == 200 and rr.text.strip():
                return rr.json()
        except Exception:
            pass
        time.sleep(0.6 * (2 ** i))
    return None


def fetch_daily(sym):
    rr = get({"param": f"{sym},day,2026-06-01,2026-12-31,300,qfq"})
    if not rr:
        return None
    d = (rr.get("data") or {}).get(sym) or {}
    kl = d.get("qfqday") or d.get("day") or []
    out = []
    for k in kl:
        try:
            out.append({"d": k[0], "o": float(k[1]), "c": float(k[2]),
                        "h": float(k[3]), "l": float(k[4]), "v": float(k[5])})
        except Exception:
            continue
    return out or None


new_rows, fail = [], []
for sym, name, grp in NEW:
    rows = fetch_daily(sym)
    if rows and len(rows) >= 18:
        new_rows.append({"secid": sym, "name": name, "group": grp, "rows": rows})
        print(f"  {name:<10} {len(rows):>4}根 {rows[0]['d']} -> {rows[-1]['d']} 收{rows[-1]['c']}", flush=True)
    else:
        fail.append(name)
        print(f"  {name:<10} 数据不足", flush=True)

json.dump({"fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"), "items": new_rows},
          open(os.path.join(OUT, "pcb_new_raw.json"), "w", encoding="utf-8"), ensure_ascii=False)
json.dump({"fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"), "snap": snap, "fail": fail},
          open(os.path.join(OUT, "pcb_snap.json"), "w", encoding="utf-8"), ensure_ascii=False)

print(f"\n完成: 新增 {len(new_rows)} / 失败 {fail if fail else '无'}")
for c, d in list(snap.items())[:6]:
    print(f"  {d['name']:<8} 价{d['price']:>8} 总市值{d['total_mv']:>10}亿 PE{d['pe']:>8} PB{d['pb']:>6} 换手{d['turnover']}%")
