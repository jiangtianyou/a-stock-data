# -*- coding: utf-8 -*-
"""
培育钻石板块数据抓取
- 成分股日线（westock kline，limit 300，覆盖 2025-06 ~ 2026-09-17）
- 实时行情快照（westock quote，板块全样本）
- 同花顺培育钻石板块指数 bk_885937
- 市场基准：沪深300 / 创业板指
落盘 out/dia_daily.json（全部成功才覆盖）
"""
import subprocess, json, os, sys, re, time, ssl
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

WESTOCK = "C:/Users/Administrator/.local/bin/westock.exe"
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")

# 板块全样本（聚源产业概念-培育钻石 17 只 + 同花顺口径补充）
POOL = {
    # ---- 材料/制造端（核心）----
    "sz301071": "力量钻石",
    "sh600172": "黄河旋风",
    "sz300179": "四方达",
    "sz000519": "中兵红箭",
    "sz002046": "国机精工",
    "bj920725": "惠丰钻石",
    "sh688028": "沃尔德",
    "sz002171": "楚江新材",
    # ---- 设备/加工端 ----
    "sz300316": "晶盛机电",
    "sz301021": "英诺激光",
    "sh688103": "国力电子",
    # ---- 消费/渠道端 ----
    "sz002345": "潮宏基",
    "sh600916": "中国黄金",
    "sh600655": "豫园股份",
    # ---- 跨界/概念 ----
    "sh605580": "恒盛能源",
    "sh603661": "恒林股份",
    "sh603389": "亚振家居",
}

BENCH = {
    "sh000300": "沪深300",
    "sz399006": "创业板指",
    "sh000001": "上证指数",
}

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def run(args, retry=3):
    for i in range(retry):
        try:
            p = subprocess.run([WESTOCK] + args, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=120)
            if p.returncode == 0 and p.stdout and p.stdout.strip():
                return p.stdout
            print(f"    retry {i+1}: rc={p.returncode} err={(p.stderr or '')[:120]}")
        except Exception as e:
            print(f"    retry {i+1}: {e}")
        time.sleep(2 * (i + 1))
    return None


def md_rows(txt):
    """把 markdown 表格解析成 [[cells], ...]，跳过表头与分隔行"""
    rows = []
    for line in txt.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if set("".join(cells)) <= set("-: "):
            continue
        rows.append(cells)
    return rows[1:] if rows else []   # 去表头


def f(x, d=None):
    try:
        return float(x)
    except Exception:
        return d


def fetch_kline(sym):
    txt = run(["kline", sym, "--period", "day", "--limit", "300"])
    if not txt:
        return None
    rows = md_rows(txt)
    out = []
    for r in rows:
        if len(r) < 9 or not re.match(r"^\d{4}-\d{2}-\d{2}$", r[0]):
            continue
        out.append({"date": r[0], "open": f(r[1]), "close": f(r[2]), "high": f(r[3]),
                    "low": f(r[4]), "vol": f(r[5]), "amt": f(r[6]),
                    "turn": f(r[7]), "pct": f(r[8])})
    out.sort(key=lambda x: x["date"])
    return out or None


def fetch_quote(syms):
    txt = run(["quote", ",".join(syms)])
    if not txt:
        return None
    rows = md_rows(txt)
    hdr = None
    raw = run(["quote", ",".join(syms)])
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("| code "):
            hdr = [c.strip() for c in line.strip("|").split("|")]
            break
    if not hdr:
        return None
    res = {}
    for r in rows:
        if len(r) != len(hdr):
            continue
        d = dict(zip(hdr, r))
        if d.get("code") in syms:
            res[d["code"]] = d
    return res


def fetch_ths_sector(code):
    url = f"http://d.10jqka.com.cn/v6/line/bk_{code}/01/last.js"
    hdr = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
           "Referer": "http://q.10jqka.com.cn/"}
    for i in range(4):
        try:
            req = urllib.request.Request(url, headers=hdr)
            raw = urllib.request.urlopen(req, context=ctx, timeout=15).read().decode("utf-8", "replace")
            m = re.search(r"\((\{.*\})\)", raw.strip(), re.S)
            if m:
                return json.loads(m.group(1))
        except Exception as e:
            print(f"    ths retry {i+1}: {e}")
        time.sleep(1.5 * (i + 1))
    return None


def main():
    daily = {}
    ok = True

    print("=== 1. 成分股 + 基准 日线 ===")
    for sym, name in list(POOL.items()) + list(BENCH.items()):
        rows = fetch_kline(sym)
        if not rows:
            print(f"  FAIL {name} {sym}")
            ok = False
            continue
        daily[sym] = {"name": name, "rows": rows}
        print(f"  OK {name:<8} {sym:<10} {len(rows)} bars  {rows[0]['date']} ~ {rows[-1]['date']}  "
              f"last={rows[-1]['close']}")

    print("\n=== 2. 板块指数 bk_885937 ===")
    sec = fetch_ths_sector("885937")
    if sec:
        parsed = []
        for seg in (sec.get("data") or "").split(";"):
            p = seg.split(",")
            if len(p) < 5:
                continue
            parsed.append({"date": p[0], "open": f(p[1]), "high": f(p[2]),
                           "low": f(p[3]), "close": f(p[4])})
        daily["bk_885937"] = {"name": sec.get("name", "培育钻石"), "rows": parsed}
        print(f"  OK 同花顺{sec.get('name')} {len(parsed)} bars  "
              f"{parsed[0]['date']} ~ {parsed[-1]['date']}  last={parsed[-1]['close']}")
    else:
        print("  FAIL 同花顺板块指数（不阻断，可用等权自建替代）")

    print("\n=== 3. 实时行情快照 ===")
    q = fetch_quote(list(POOL.keys()))
    if not q:
        print("  FAIL quote")
        ok = False
    else:
        print(f"  OK {len(q)} 只")

    if not ok:
        print("\n!! 存在失败项，不覆盖落盘文件")
        sys.exit(1)

    tmp = os.path.join(OUT, "_dia_daily.tmp.json")
    with open(tmp, "w", encoding="utf-8") as fp:
        json.dump({"fetch_date": time.strftime("%Y-%m-%d"), "daily": daily, "quote": q},
                  fp, ensure_ascii=False)
    os.replace(tmp, os.path.join(OUT, "dia_daily.json"))
    print(f"\nsaved out/dia_daily.json  ({len(daily)} 序列)")


if __name__ == "__main__":
    main()
