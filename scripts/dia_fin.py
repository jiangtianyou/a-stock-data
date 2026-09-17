# -*- coding: utf-8 -*-
"""
培育钻石板块 财务 + 资金流 抓取
- finance --type income：近 6 期利润表
- fund flow：个股主力资金净流入（当日/5日/10日/20日）
落盘 out/dia_fin.json
"""
import subprocess, json, os, sys, time, re

sys.stdout.reconfigure(encoding="utf-8")
WESTOCK = "C:/Users/Administrator/.local/bin/westock.exe"
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")

CORE = ["sz301071", "sh600172", "sz300179", "sz000519",
        "sz002046", "bj920725", "sh688028", "sz300316"]
NAME = {"sz301071": "力量钻石", "sh600172": "黄河旋风", "sz300179": "四方达",
        "sz000519": "中兵红箭", "sz002046": "国机精工", "bj920725": "惠丰钻石",
        "sh688028": "沃尔德", "sz300316": "晶盛机电"}


def run(args, retry=3):
    for i in range(retry):
        try:
            p = subprocess.run([WESTOCK] + args, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=120)
            if p.returncode == 0 and p.stdout and p.stdout.strip():
                return p.stdout
            print(f"    retry {i+1}: rc={p.returncode} {(p.stderr or '')[:100]}")
        except Exception as e:
            print(f"    retry {i+1}: {e}")
        time.sleep(2 * (i + 1))
    return None


def md_tables(txt):
    """返回 [(header, [row,...]), ...]"""
    tables, hdr, rows = [], None, []
    for line in txt.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            if hdr and rows:
                tables.append((hdr, rows))
            hdr, rows = None, []
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if set("".join(cells)) <= set("-: "):
            continue
        if hdr is None:
            hdr = cells
        else:
            rows.append(cells)
    if hdr and rows:
        tables.append((hdr, rows))
    return tables


def num(x):
    try:
        return float(x)
    except Exception:
        return None


def fetch_income(sym, limit=6):
    txt = run(["finance", sym, "--type", "income", "--limit", str(limit)])
    if not txt:
        return None
    tabs = md_tables(txt)
    if not tabs:
        return None
    hdr, rows = tabs[0]
    out = []
    for r in rows:
        if len(r) != len(hdr):
            continue
        d = dict(zip(hdr, r))
        out.append(d)
    return out


def fetch_flow(syms):
    txt = run(["fund", "flow", ",".join(syms)])
    if not txt:
        return None
    tabs = md_tables(txt)
    if not tabs:
        return None
    hdr, rows = tabs[0]
    res = {}
    for r in rows:
        if len(r) != len(hdr):
            continue
        d = dict(zip(hdr, r))
        res[d.get("code")] = d
    return res


def main():
    fin, flow = {}, {}
    ok = True

    print("=== 利润表（近 6 期）===")
    for sym in CORE:
        rows = fetch_income(sym)
        if not rows:
            print(f"  FAIL {NAME[sym]} {sym}")
            ok = False
            continue
        fin[sym] = rows
        r0 = rows[0]
        print(f"  OK {NAME[sym]:<8} {r0.get('EndDate')}  营收={num(r0.get('OperatingRevenue'))}  "
              f"归母={num(r0.get('NPParentCompanyOwners'))}  毛利率={r0.get('GrossIncomeRatio')}")

    print("\n=== 主力资金流 ===")
    f = fetch_flow(CORE)
    if not f:
        print("  FAIL")
        ok = False
    else:
        flow = f
        for sym in CORE:
            d = flow.get(sym)
            if d:
                print(f"  OK {NAME[sym]:<8} 当日={num(d.get('MainNetFlow'))}  "
                      f"5日={num(d.get('MainNetFlow5D'))}  10日={num(d.get('MainNetFlow10D'))}  "
                      f"20日={num(d.get('MainNetFlow20D'))}")

    if not ok:
        print("\n!! 存在失败项，不覆盖")
        sys.exit(1)

    tmp = os.path.join(OUT, "_dia_fin.tmp.json")
    with open(tmp, "w", encoding="utf-8") as fp:
        json.dump({"income": fin, "flow": flow, "names": NAME}, fp, ensure_ascii=False)
    os.replace(tmp, os.path.join(OUT, "dia_fin.json"))
    print("\nsaved out/dia_fin.json")


if __name__ == "__main__":
    main()
