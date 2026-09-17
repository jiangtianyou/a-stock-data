# -*- coding: utf-8 -*-
"""
培育钻石板块核心TOP3分析报告生成
输入：out/dia_daily.json, out/dia_analysis.json, out/dia_fin.json
输出：reports/培育钻石板块核心TOP3分析-20260917.html
"""
import json, os, sys, re, statistics, math

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")

D = json.load(open(os.path.join(OUT, "dia_daily.json"), encoding="utf-8"))
A = json.load(open(os.path.join(OUT, "dia_analysis.json"), encoding="utf-8"))
F = json.load(open(os.path.join(OUT, "dia_fin.json"), encoding="utf-8"))

daily = D["daily"]
ST = A["stocks"]
IDX = A["index"]
QUOTE = D["quote"]
INC = F["income"]

CORE3 = ["sz301071", "sh600172", "sz300179"]
C3NAME = {"sz301071": "力量钻石", "sh600172": "黄河旋风", "sz300179": "四方达"}

ASOF = daily["sh000300"]["rows"][-1]["date"]


def normdate(r):
    d0 = r["date"]
    return f"{d0[:4]}-{d0[4:6]}-{d0[6:]}" if (len(d0) == 8 and "-" not in d0) else d0


for sym, v in daily.items():
    for r in v["rows"]:
        r["date"] = normdate(r)
    v["rows"].sort(key=lambda x: x["date"])


def closes(sym):
    return {r["date"]: r["close"] for r in daily[sym]["rows"]}


def amts(sym):
    return {r["date"]: (r.get("amt") or 0) for r in daily[sym]["rows"]}


def cn(x, nd=2, plus=False):
    if x is None:
        return "--"
    s = f"{x:+.{nd}f}" if plus else f"{x:.{nd}f}"
    return s


def cls(x):
    return "up" if (x or 0) >= 0 else "down"


# ── 归一化净值序列（基期 2025-12-31 = 100）──────────────────────────
AXIS = [r["date"] for r in daily["sh000300"]["rows"] if r["date"] >= "2025-12-31"]
SERIES = {}
for sym in CORE3 + ["bk_885937", "sh000300"]:
    m = closes(sym)
    base = None
    vals = []
    for d in AXIS:
        if d in m:
            if base is None:
                base = m[d]
            vals.append(round(m[d] / base * 100, 2))
        else:
            vals.append(None)
    SERIES[sym] = vals

# ── 全样本 YTD 排序 ───────────────────────────────────────────────
RANK = sorted([(k, v) for k, v in ST.items() if not k.startswith(("sh000", "sz399"))],
              key=lambda x: -(x[1]["ytd_ret"] or -999))

# ── 三阶段 ────────────────────────────────────────────────────────
STAGE = {}
for sym in CORE3:
    s = ST[sym]
    STAGE[C3NAME[sym]] = [round(s["seg_h1"] or 0, 1), round(s["seg_jul_aug"] or 0, 1),
                          round(s["seg_sep"] or 0, 1)]

# ── 基本面 ────────────────────────────────────────────────────────
BAL = {  # 资产负债率 %，来源 westock finance --type balance（2026-06-30）
    "sz301071": 19.51, "sh600172": 94.64, "sz300179": 40.29,
    "sz000519": 43.34, "sh688028": 16.02, "sz002046": 42.0,
}
CF = {"sz301071": 2.068, "sh600172": 0.982, "sz300179": 0.635}  # 经营现金流 亿元


def inc(sym):
    for r in INC.get(sym, []):
        if r.get("EndDate") == "2026-06-30":
            return r
    return {}


def gv(r, k):
    try:
        return float(r.get(k))
    except Exception:
        return None


def cut_yoy(sym):
    """半年报口径扣非净利同比（westock 的 NPParentCompanyCutYOY_Q 是单季值，不可直接用）"""
    rows = INC.get(sym, [])
    cur = next((r for r in rows if r.get("EndDate") == "2026-06-30"), None)
    pre = next((r for r in rows if r.get("EndDate") == "2025-06-30"), None)
    a, b = gv(cur, "NPDeductNonRecurringPL"), gv(pre, "NPDeductNonRecurringPL")
    return None if (not a or not b) else (a / b - 1) * 100


CORE_INC = {s: inc(s) for s in CORE3}

# ── 生成 HTML 片段 ────────────────────────────────────────────────
def np_yoy_txt(r):
    """归母净利同比：亏损状态下用「收窄/扩大」表述，避免误读为增长"""
    np_v, yoy = gv(r, "NPParentCompanyOwners"), gv(r, "NPParentCompanyYOY")
    if np_v is not None and np_v < 0:
        w = "收窄" if (yoy or 0) > 0 else "扩大"
        return f"亏损同比{w} {abs(yoy or 0):.1f}%", "g"
    return f"同比 {(yoy or 0):+.1f}%", ("r" if (yoy or 0) >= 0 else "g")


cards = []
tags = {"sz301071": ("tag-blue", "业绩唯一兑现"), "sh600172": ("tag-red", "产业化标签最硬·财务最险"),
        "sz300179": ("tag-purple", "弹性第1·估值最贵")}
for sym in CORE3:
    s = ST[sym]
    t, lab = tags[sym]
    r = CORE_INC[sym]
    yoy_txt, yoy_cls = np_yoy_txt(r)
    np_v = gv(r, "NPParentCompanyOwners") or 0
    cards.append(f"""    <div class="card">
      <div class="name">{s['name']} ({sym[2:]}) <span class="tag {t}">{lab}</span></div>
      <div class="big {cls(s['ytd_ret'])}">{cn(s['ytd_ret'],1,True)}%</div>
      <div class="meta">
        最新：<b>{cn(s['close'])} 元</b>（YTD 高点 {cn(s['hi'])} / 距高点 <b class="{cls(s['from_hi'])}">{cn(s['from_hi'],1,True)}%</b>）<br>
        市值 <b>{cn(s['mktcap'],0)} 亿</b> | PE(TTM) {cn(s['pe'],1)} | PB {cn(s['pb'],2)}<br>
        H1 <span class="{cls(s['seg_h1'])}">{cn(s['seg_h1'],1,True)}%</span>
        → 7-8月 <span class="{cls(s['seg_jul_aug'])}">{cn(s['seg_jul_aug'],1,True)}%</span>
        → 9月 <span class="{cls(s['seg_sep'])}">{cn(s['seg_sep'],1,True)}%</span><br>
        2026H1 归母 <b class="{'r' if np_v>=0 else 'g'}">{np_v/1e8:+.2f} 亿</b>（<span class="{yoy_cls}">{yoy_txt}</span>）<br>
        YTD 最大回撤 <b class="down">{cn(abs(s['mdd']),1)}%</b> | 近5日日均额 {cn(s['amt5']/1e8)} 亿
      </div>
    </div>""")

rows_all = []
for sym, s in RANK:
    rows_all.append(
        f"      <tr><td><b>{s['name']}</b></td><td>{sym[2:]}</td>"
        f"<td class='{cls(s['ytd_ret'])}'><b>{cn(s['ytd_ret'],1,True)}%</b></td>"
        f"<td class='{cls(s['seg_jul_aug'])}'>{cn(s['seg_jul_aug'],1,True)}%</td>"
        f"<td class='{cls(s['seg_sep'])}'>{cn(s['seg_sep'],1,True)}%</td>"
        f"<td>{cn(s['mktcap'],0)}</td><td>{cn(s['pe'],1)}</td><td>{cn(s['pb'],2)}</td>"
        f"<td class='down'>{cn(s['mdd'],1)}%</td>"
        f"<td class='{cls(s['from_hi'])}'>{cn(s['from_hi'],1,True)}%</td>"
        f"<td>{cn(s['amt_ratio'],2)}</td></tr>")

rows_core = []
for sym in CORE3:
    s = ST[sym]
    r = CORE_INC[sym]
    rows_core.append(
        f"      <tr><td><b>{s['name']}</b></td><td>{sym[2:]}</td>"
        f"<td class='up'><b>{cn(s['ytd_ret'],1,True)}%</b></td>"
        f"<td class='{cls(s['seg_h1'])}'>{cn(s['seg_h1'],1,True)}%</td>"
        f"<td class='{cls(s['seg_jul_aug'])}'>{cn(s['seg_jul_aug'],1,True)}%</td>"
        f"<td class='{cls(s['seg_sep'])}'>{cn(s['seg_sep'],1,True)}%</td>"
        f"<td>{cn(s['close'])}</td><td><b>{cn(s['mktcap'],0)}</b></td>"
        f"<td>{cn(s['pe'],1)}</td><td>{cn(s['pb'],2)}</td>"
        f"<td>{cn(s['hi'])}<br><span class='muted'>{s['hi_date'][5:]}</span></td>"
        f"<td class='{cls(s['from_hi'])}'><b>{cn(s['from_hi'],1,True)}%</b></td>"
        f"<td class='down'>{cn(s['mdd'],1)}%<br><span class='muted'>{s['mdd_peak'][5:]}→{s['mdd_trough'][5:]}</span></td>"
        f"<td>{cn(s['amt5']/1e8)}<span class='muted'> / {cn(s['amt_ytd']/1e8)}</span></td>"
        f"<td>{cn(s['turn'],1)}%</td></tr>")

rows_fin = []
for sym in CORE3:
    s, r = ST[sym], CORE_INC[sym]
    yoy_txt, yoy_cls = np_yoy_txt(r)
    np_v = gv(r, "NPParentCompanyOwners") or 0
    rows_fin.append(
        f"      <tr><td><b>{s['name']}</b></td>"
        f"<td>{cn(gv(r,'OperatingRevenue')/1e8 if gv(r,'OperatingRevenue') else None)}</td>"
        f"<td class='{cls(gv(r,'TORGrowRate'))}'>{(gv(r,'TORGrowRate') or 0):+.2f}%</td>"
        f"<td class='{'r' if np_v>=0 else 'g'}'><b>{np_v/1e8:+.2f}</b></td>"
        f"<td class='{yoy_cls}'>{yoy_txt}</td>"
        f"<td>{cn(gv(r,'GrossIncomeRatio'))}%</td>"
        f"<td>{cn(BAL.get(sym))}%</td>"
        f"<td>{(CF.get(sym) or 0):+.2f}</td>"
        f"<td>{(gv(r,'ROEWeighted') or 0):+.2f}%</td></tr>")

# 阶段柱状图
stage_names = list(STAGE.keys())
stage_series = [
    ("2026上半年（1-6月）", [STAGE[n][0] for n in stage_names], "#dc2626"),
    ("7-8月深调", [STAGE[n][1] for n in stage_names], "#16a34a"),
    ("9月以来", [STAGE[n][2] for n in stage_names], "#2563eb"),
]

# 成交额对比
amt_names = [ST[n]["name"] for n in ["sz301071", "sh600172", "sz300179", "sz002046", "sh688028", "bj920725"]]
amt_a = [round(ST[n]["amt5"] / 1e8, 2) for n in ["sz301071", "sh600172", "sz300179", "sz002046", "sh688028", "bj920725"]]
amt_b = [round(ST[n]["amt_ytd"] / 1e8, 2) for n in ["sz301071", "sh600172", "sz300179", "sz002046", "sh688028", "bj920725"]]

# 排名条形图
bar = [(s["name"], round(s["ytd_ret"], 1)) for _, s in RANK]

# ── 关键结论数字（用于正文占位符）────────────────────────────────
K = {}
K["CORE_YTD_MIN"] = cn(ST["sz301071"]["ytd_ret"], 1, True)
K["CORE_YTD_MAX"] = cn(ST["sz300179"]["ytd_ret"], 1, True)
K["JUL_AUG_WORST"] = cn(ST["sz300179"]["seg_jul_aug"], 1, True)
K["JUL_AUG_BEST"] = cn(ST["sh600172"]["seg_jul_aug"], 1, True)
K["MDD_MIN"] = cn(abs(ST["sh600172"]["mdd"]), 1)
K["MDD_MAX"] = cn(abs(ST["sz300179"]["mdd"]), 1)
K["HS300_YTD"] = cn(IDX["sh000300"]["ytd_ret"], 1, True)
K["HS300_SEP"] = cn(IDX["sh000300"]["seg_sep"], 1, True)
K["CYB_YTD"] = cn(IDX["sz399006"]["ytd_ret"], 1, True)
K["CYB_MDD"] = cn(abs(IDX["sz399006"]["mdd"]), 1)
K["SEC_SEP"] = cn(IDX["bk_885937"]["seg_sep"], 1, True)
K["SEC_20D"] = cn(IDX["bk_885937"]["ret_20d"], 1, True)
K["SEC_MDD"] = cn(IDX["bk_885937"]["mdd"], 1)
K["SEC_HI_DATE"] = IDX["bk_885937"]["hi_date"]
K["LD_YTD"] = cn(ST["sz301071"]["ytd_ret"], 1, True)
K["LD_FROMHI"] = cn(ST["sz301071"]["from_hi"], 1, True)
K["LD_PE"] = cn(ST["sz301071"]["pe"], 1)
K["LD_PB"] = cn(ST["sz301071"]["pb"], 2)
K["LD_REV_G"] = f"{(gv(CORE_INC['sz301071'],'TORGrowRate') or 0):.2f}"
K["LD_NP_G"] = f"{(gv(CORE_INC['sz301071'],'NPParentCompanyYOY') or 0):.2f}"
K["LD_CUT_G"] = f"{(cut_yoy('sz301071') or 0):.2f}"
K["LD_GM"] = cn(gv(CORE_INC["sz301071"], "GrossIncomeRatio"))
K["LD_REV"] = f"{(gv(CORE_INC['sz301071'],'OperatingRevenue') or 0)/1e8:.2f}"
K["LD_BAL"] = cn(BAL["sz301071"])
K["ZBJ_FLOW20"] = cn(abs(float(F["flow"]["sz000519"]["MainNetFlow20D"]))/1e8, 2)
K["HH_YTD"] = cn(ST["sh600172"]["ytd_ret"], 1, True)
K["HH_FROMHI"] = cn(ST["sh600172"]["from_hi"], 1, True)
K["HH_PB"] = cn(ST["sh600172"]["pb"], 1)
K["HH_BAL"] = cn(BAL["sh600172"])
K["HH_LOSS"] = f"{(gv(CORE_INC['sh600172'],'NPParentCompanyOwners') or 0)/1e8:.2f}"
K["HH_REV"] = f"{(gv(CORE_INC['sh600172'],'OperatingRevenue') or 0)/1e8:.2f}"
K["HH_REV_G"] = f"{(gv(CORE_INC['sh600172'],'TORGrowRate') or 0):.2f}"
K["HH_AMT"] = cn(ST["sh600172"]["amt5"] / 1e8)
K["HH_MDD"] = cn(ST["sh600172"]["mdd"], 1)
K["SF_YTD"] = cn(ST["sz300179"]["ytd_ret"], 1, True)
K["SF_H1"] = cn(ST["sz300179"]["seg_h1"], 1, True)
K["SF_FROMHI"] = cn(ST["sz300179"]["from_hi"], 1, True)
K["SF_PE"] = cn(ST["sz300179"]["pe"], 1)
K["SF_PB"] = cn(ST["sz300179"]["pb"], 2)
K["SF_REV"] = f"{(gv(CORE_INC['sz300179'],'OperatingRevenue') or 0)/1e8:.2f}"
K["SF_REV_G"] = f"{(gv(CORE_INC['sz300179'],'TORGrowRate') or 0):.2f}"
K["SF_NP"] = f"{(gv(CORE_INC['sz300179'],'NPParentCompanyOwners') or 0)/1e8:.2f}"
K["SF_NP_G"] = f"{(gv(CORE_INC['sz300179'],'NPParentCompanyYOY') or 0):.1f}"
K["SF_GM"] = cn(gv(CORE_INC["sz300179"], "GrossIncomeRatio"))
K["ZBJ_YTD"] = cn(ST["sz000519"]["ytd_ret"], 1, True)
K["CM_BEST"] = cn(RANK[0][1]["ytd_ret"], 1, True)
K["CM_BEST_NM"] = RANK[0][1]["name"]
K["CONS_LOSS"] = cn(ST["sz002345"]["ytd_ret"], 1, True)
K["CONS_LOSS_NM"] = "潮宏基"
K["SEP_LEAD"] = cn(ST["bj920725"]["seg_sep"], 1, True)
K["SEP_LEAD_NM"] = "惠丰钻石"
K["ASOF"] = ASOF
K["N_STOCK"] = str(len(RANK))

TPL = open(os.path.join(BASE, "scripts", "_dia_tpl.html"), encoding="utf-8").read()

REP = {
    "__CARDS__": "\n".join(cards),
    "__ROWS_ALL__": "\n".join(rows_all),
    "__ROWS_CORE__": "\n".join(rows_core),
    "__ROWS_FIN__": "\n".join(rows_fin),
    "__AXIS__": json.dumps(AXIS),
    "__S_LD__": json.dumps(SERIES["sz301071"]),
    "__S_HH__": json.dumps(SERIES["sh600172"]),
    "__S_SF__": json.dumps(SERIES["sz300179"]),
    "__S_SEC__": json.dumps(SERIES["bk_885937"]),
    "__S_HS__": json.dumps(SERIES["sh000300"]),
    "__BAR__": json.dumps(bar, ensure_ascii=False),
    "__STAGE_NAMES__": json.dumps(stage_names, ensure_ascii=False),
    "__STAGE_SERIES__": json.dumps(
        [{"name": n, "data": d, "color": c} for n, d, c in stage_series], ensure_ascii=False),
    "__AMT_NAMES__": json.dumps(amt_names, ensure_ascii=False),
    "__AMT_A__": json.dumps(amt_a),
    "__AMT_B__": json.dumps(amt_b),
    "__N_STOCK__": str(len(RANK)),
}
for k, v in K.items():
    REP[f"__{k}__"] = str(v)

html = TPL
for k, v in REP.items():
    html = html.replace(k, v)

left = re.findall(r"__[A-Z_0-9]+__", html)
assert not left, f"未替换占位符: {set(left)}"

os.makedirs(os.path.join(BASE, "reports"), exist_ok=True)
p = os.path.join(BASE, "reports", f"培育钻石板块核心TOP3分析-{ASOF.replace('-','')}.html")
with open(p, "w", encoding="utf-8") as f:
    f.write(html)
print("saved", p)
print("sample K:", {k: K[k] for k in list(K)[:8]})
