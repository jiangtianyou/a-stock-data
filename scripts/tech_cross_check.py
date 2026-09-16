# -*- coding: utf-8 -*-
"""
双通道交叉验证:
 A) 同花顺行业板块日线 -> 8月以来区间涨幅
 B) 东财 push2delay clist -> 全市场板块 60日涨幅(初筛)
输出: out/ths_industry_perf.json, out/em_clist_60d.json
"""
import sys, os, re, json, time, random
import requests

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")

S = requests.Session()
S.trust_env = False
S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
                  "Referer": "http://q.10jqka.com.cn/"})

# ---------- A) 同花顺 ----------
THS = [
    ("bk_881121", "半导体"), ("bk_881122", "光学光电子"), ("bk_881123", "其他电子"),
    ("bk_881124", "消费电子"), ("bk_881129", "通信设备"), ("bk_881130", "计算机设备"),
    ("bk_881162", "通信服务"), ("bk_881163", "计算机应用"), ("bk_881164", "文化传媒"),
    ("bk_881166", "军工装备"), ("bk_881171", "自动化设备"), ("bk_881172", "电子化学品"),
    ("bk_881117", "通用设备"), ("bk_881118", "专用设备"), ("bk_881119", "仪器仪表"),
]


def ths_perf(code):
    try:
        r = S.get(f"http://d.10jqka.com.cn/v6/line/{code}/01/last.js", timeout=10)
        m = re.search(r'(\{.*\})', r.text, re.S)
        if not m:
            return None
        d = json.loads(m.group(1))
        rows = []
        for seg in d.get("data", "").split(";"):
            p = seg.split(",")
            if len(p) < 5:
                continue
            try:
                rows.append({"d": p[0], "o": float(p[1]), "h": float(p[2]),
                             "l": float(p[3]), "c": float(p[4])})
            except Exception:
                continue
        base_row = None
        for x in rows:
            if x["d"] <= "20260731":
                base_row = x
        if not base_row or len(rows) < 5:
            return None
        seq = [x for x in rows if x["d"] >= base_row["d"]]
        last = seq[-1]
        lo = min(seq, key=lambda x: x["c"])
        hi = max(seq, key=lambda x: x["h"])
        return {"name": d.get("name"), "base_date": base_row["d"], "base": base_row["c"],
                "last_date": last["d"], "last": last["c"],
                "ret": last["c"] / base_row["c"] - 1,
                "low_date": lo["d"], "rd": last["c"] / lo["c"] - 1,
                "hi_date": hi["d"], "hi": hi["h"], "n": len(seq)}
    except Exception as e:
        print("  ERR", code, type(e).__name__)
        return None


print("=== A) 同花顺行业板块 (2026-07-31 -> 2026-09-15) ===")
ths_res = []
for code, nm in THS:
    st = ths_perf(code)
    if st:
        st["code"] = code
        ths_res.append(st)
        print(f"  {st['name']:<10} {st['ret']*100:>+7.2f}%  低点{st['low_date']} 反弹{st['rd']*100:>+6.2f}%  最高{st['hi_date']}")
    time.sleep(0.25)
ths_res.sort(key=lambda x: -x["ret"])
json.dump({"range": "2026-07-31 -> 2026-09-15", "source": "ths industry index",
           "items": ths_res}, open(os.path.join(OUT, "ths_industry_perf.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ---------- B) 东财 push2delay clist ----------
print("\n=== B) 东财全市场板块 60日涨幅 (push2delay) ===")
out = []
for fs, tag in [("m:90+t:2", "行业"), ("m:90+t:3", "概念")]:
    for pn in range(1, 8):
        try:
            r = S.get("https://push2delay.eastmoney.com/api/qt/clist/get",
                      params={"pn": pn, "pz": 100, "po": 1, "np": 1, "fltt": 2, "invt": 2,
                              "fid": "f3", "fs": fs, "fields": "f12,f14,f3,f24,f25"},
                      timeout=10)
            diff = ((r.json().get("data") or {}).get("diff")) or []
        except Exception as e:
            print("  ERR", tag, pn, type(e).__name__)
            break
        if not diff:
            break
        for d in diff:
            d["_t"] = tag
            out.append(d)
        time.sleep(0.3)
        if len(diff) < 100:
            break
print(f"  共 {len(out)} 个板块")
json.dump(out, open(os.path.join(OUT, "em_clist_60d.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# 打印科技相关按60日涨幅排序
KW = ["半导体", "芯片", "光", "通信", "电子", "算力", "AI", "人工智能", "存储", "PCB",
      "元件", "面板", "软件", "计算机", "传媒", "游戏", "机器人", "服务器", "数据中心",
      "消费电子", "光学", "MLCC", "封装", "光刻", "HBM", "CPO", "液冷", "铜缆", "光模块"]
EX = ["昨日", "涨停", "连板", "打板", "破净", "转债", "次新", "融资融券", "预盈", "预亏",
      "高送转", "股权转让", "举牌", "同花顺", "机构重仓", "基金重仓"]
cand = [d for d in out if d.get("f14") and not any(e in d["f14"] for e in EX)
        and any(k in d["f14"] for k in KW)]
cand.sort(key=lambda x: -(x.get("f24") or -999))
print("\n  --- 按 60 日涨幅排序的科技类板块 TOP25 ---")
for d in cand[:25]:
    print(f"  [{d['_t']}] {d['f14']:<18} 60日{d.get('f24')}%  当日{d.get('f3')}%")
