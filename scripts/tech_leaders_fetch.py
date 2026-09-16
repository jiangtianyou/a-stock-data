# -*- coding: utf-8 -*-
"""
整合 8月以来大科技板块反弹数据
输出: out/tech_rebound_data.json
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


def dec(s):
    try:
        return json.loads('"' + s + '"')
    except Exception:
        return s


# ---------- 龙头股 ----------
LEADERS = [
    ("sh601869", "长飞光纤", "光纤光缆"), ("sh600487", "亨通光电", "光纤光缆"),
    ("sh600522", "中天科技", "光纤光缆"), ("sz002491", "通鼎互联", "光纤光缆"),
    ("sz300570", "太辰光", "光纤光缆"), ("sh688143", "长盈通", "光纤光缆"),
    ("sz300308", "中际旭创", "光模块/CPO"), ("sz300502", "新易盛", "光模块/CPO"),
    ("sz300394", "天孚通信", "光模块/CPO"), ("sh688498", "源杰科技", "光芯片"),
    ("sz300476", "胜宏科技", "PCB/覆铜板"), ("sh600183", "生益科技", "PCB/覆铜板"),
    ("sz002636", "金安国纪", "PCB/覆铜板"), ("sh688519", "南亚新材", "PCB/覆铜板"),
    ("sz300408", "三环集团", "被动元件/MLCC"), ("sz000636", "风华高科", "被动元件/MLCC"),
    ("sz300285", "国瓷材料", "被动元件/MLCC"),
    ("sh688981", "中芯国际", "半导体"), ("sh688256", "寒武纪", "半导体"),
    ("sz002371", "北方华创", "半导体设备"),
]


def fetch_day(sym):
    for a in range(3):
        try:
            r = S.get("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get",
                      params={"param": f"{sym},day,2026-07-25,2026-09-15,60,qfq"}, timeout=20)
            if r.status_code == 200:
                d = (r.json().get("data") or {}).get(sym) or {}
                kl = d.get("qfqday") or d.get("day") or []
                rows = []
                for k in kl:
                    try:
                        rows.append({"d": k[0], "o": float(k[1]), "c": float(k[2]),
                                     "h": float(k[3]), "l": float(k[4])})
                    except Exception:
                        continue
                if rows:
                    return rows
        except Exception:
            pass
        time.sleep(0.6 * (a + 1))
    return None


def calc(rows):
    base = None
    for r in rows:
        if r["d"] <= "2026-07-31":
            base = r
    if not base:
        return None
    seq = [r for r in rows if r["d"] >= base["d"]]
    last = seq[-1]
    lo = min(seq, key=lambda x: x["c"])
    return {"ret": last["c"] / base["c"] - 1, "base": base["c"], "last": last["c"],
            "low_date": lo["d"], "rd": last["c"] / lo["c"] - 1,
            "high": max(x["h"] for x in seq),
            "seq": [[x["d"], round(x["c"] / base["c"] * 100, 2)] for x in seq]}


print("=== 龙头股 8月以来表现 ===")
leaders = []
for sym, name, grp in LEADERS:
    rows = fetch_day(sym)
    st = calc(rows) if rows else None
    if st:
        st.update({"name": name, "code": sym, "group": grp})
        leaders.append(st)
        print(f"  {name:<8}{st['ret']*100:>+8.2f}%  低点{st['low_date']} 反弹{st['rd']*100:>+7.2f}%")
    else:
        print(f"  {name:<8} 失败")
    time.sleep(0.4)

leaders.sort(key=lambda x: -x["ret"])
json.dump(leaders, open(os.path.join(OUT, "tech_leaders.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("已写出 out/tech_leaders.json")
