# -*- coding: utf-8 -*-
"""PCB 代表性个股图谱 - 生成 HTML"""
import sys, os, json
sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")
REP = os.path.join(BASE, "reports")

st = json.load(open(os.path.join(OUT, "pcb_stocks_stats.json"), encoding="utf-8"))
S = st["stocks"]
BYN = {r["name"]: r for r in S}

# 2026 中报(净利同比) —— 公开披露/媒体报道口径
FIN = {
    "沪电股份": ("+73.7%", "29.23 亿", "正式"),
    "深南电路": ("+65.6%", "22.51 亿", "正式"),
    "生益科技": ("+117~131%", "-", "预告"),
    "生益电子": ("+104~114%", "10.82~11.37 亿", "预告"),
    "广合科技": ("+85~95%", "9.1~9.6 亿", "预告"),
    "嘉立创":   ("+73.5%", "10.30 亿", "正式"),
    "胜宏科技": ("+33.3%", "28.57 亿", "正式"),
    "景旺电子": ("-", "6.02 亿", "正式"),
    "鹏鼎控股": ("-", "12.84 亿", "正式"),
    "华正新材": ("+305.3%", "1.73 亿", "正式"),
    "奥士康":   ("-57.8%", "0.83 亿", "正式"),
    "崇达技术": ("-31.3%", "1.52 亿", "正式"),
    "超声电子": ("-1.2%", "1.13 亿", "正式"),
    "博敏电子": ("转亏", "-0.51 亿", "正式"),
    "满坤科技": ("同比下滑", "0.44 亿", "正式"),
    "威尔高":   ("-", "0.44 亿", "正式"),
    "澳弘电子": ("-", "0.66 亿", "正式"),
    "逸豪新材": ("亏损", "-", "正式"),
    "中京电子": ("亏损", "-", "正式"),
    "科翔股份": ("亏损", "-", "正式"),
    "迅捷兴":   ("亏损", "-", "正式"),
}
# 区间内高点日期(见顶信号)
WINNERS_9 = ["满坤科技", "超声电子", "崇达技术", "澳弘电子", "迅捷兴", "华正新材", "四会富仕", "中京电子"]
LAGGARDS_9 = ["大族数控", "东山精密", "胜宏科技", "鹏鼎控股", "鼎泰高科", "生益电子", "天承科技",
              "生益科技", "芯碁微装", "弘信电子"]

ROLE = [
    ("A｜算力核心资产", "A", "#d0342c",
     ["沪电股份", "深南电路", "胜宏科技", "广合科技", "生益电子", "嘉立创"]),
    ("B｜覆铜板 / 上游材料", "B", "#e08a2e",
     ["生益科技", "南亚新材", "华正新材", "金安国纪", "逸豪新材"]),
    ("C｜PCB 设备与耗材", "C", "#2c6bd0",
     ["大族数控", "芯碁微装", "鼎泰高科", "天承科技"]),
    ("D｜消费电子 / 苹果链", "D", "#1e8e4e",
     ["鹏鼎控股", "东山精密", "弘信电子"]),
    ("E｜二线弹性制造", "E", "#8a5bd0",
     ["科翔股份", "迅捷兴", "崇达技术", "奥士康", "超声电子", "博敏电子", "四会富仕", "金禄电子",
      "中京电子", "强达电路", "明阳电路", "天津普林", "依顿电子", "世运电路", "景旺电子", "兴森科技",
      "中富电路", "协和电子", "金百泽", "方正科技", "澳弘电子", "满坤科技", "威尔高"]),
]
ROLEMAP = {}
for rn, rc, cc, names in ROLE:
    for n in names:
        ROLEMAP[n] = (rc, cc)
missing = [n for n in BYN if n not in ROLEMAP]
assert not missing, f"未归类: {missing}"


def role_of(n):
    for rn, rc, cc, names in ROLE:
        if n in names:
            return rn, rc, cc
    return "?", "?", "#999"


TIER_CN = {"① 大市值(≥800亿)": "≥800 亿", "② 中大市值(300-800亿)": "300–800 亿",
           "③ 中市值(100-300亿)": "100–300 亿", "④ 小市值(<100亿)": "<100 亿"}


def fm(v, d=1, unit=""):
    return "—" if v is None else f"{v:.{d}f}{unit}"


def cl(v):
    if v is None:
        return ""
    return "up" if v > 0 else ("down" if v < 0 else "")


# ---------- 表格: 全景 ----------
rows_all = ""
for r in S:
    rn, rc, cc = role_of(r["name"])
    fin = FIN.get(r["name"], ("—", "—", ""))
    fin_txt = fin[0] if fin[0] != "-" else "—"
    fin_cls = "down" if ("-" in fin[0] or "亏损" in fin[0] or "转亏" in fin[0]) else ("up" if "%" in fin[0] else "")
    star = ' <span class="tag tag-red">9月接力</span>' if r["name"] in WINNERS_9 else (
        ' <span class="tag tag-gray">9月掉队</span>' if r["name"] in LAGGARDS_9 else "")
    rows_all += (f'<tr><td><b>{r["name"]}</b>{star}</td><td class="muted">{r["code"]}</td>'
                 f'<td><span style="color:{cc}">■</span> {rc.split("｜")[0]}</td>'
                 f'<td class="up"><b>{fm(r["ret"],1,"%")}</b></td>'
                 f'<td class="{cl(r["ret_jul"])}">{fm(r["ret_jul"],1,"%")}</td>'
                 f'<td class="{cl(r["ret_sep"])}">{fm(r["ret_sep"],1,"%")}</td>'
                 f'<td class="down">{fm(r["from_hi"],1,"%")}</td>'
                 f'<td>{fm(r["mv"],0)}</td><td class="{fin_cls}">{fin_txt}</td>'
                 f'<td>{fm(r["turnover"],2,"%")}</td><td>{fm(r["vr"],2)}</td></tr>')

# ---------- 图表数据 ----------
scat_role = {}
for r in S:
    if r["new_stock"]:
        continue
    rn, rc, cc = role_of(r["name"])
    scat_role.setdefault(rc, {"color": cc, "data": []})
    scat_role[rc]["data"].append([r["mv"] or 0, round(r["ret"], 1), round(r["turnover"] or 0, 2), r["name"]])

turn_data = sorted([[round(r["turnover"] or 0, 2), round(r["ret"], 1), r["name"]] for r in S],
                   key=lambda x: -x[1])

sep_mix = [{"n": r["name"], "a": round(r["ret_aug"] or 0, 1), "s": round(r["ret_sep"] or 0, 1)}
           for r in sorted([y for y in S if not y["new_stock"]],
                           key=lambda x: -(x["ret_sep"] if x["ret_sep"] is not None else -99))]

# 分层汇总
tiers = [("≥800 亿", []), ("300–800 亿", []), ("100–300 亿", []), ("<100 亿", [])]
_tmap = {"≥800 亿": 0, "300–800 亿": 1, "100–300 亿": 2, "<100 亿": 3}
for r in S:
    k = TIER_CN[r["tier"]]
    tiers[_tmap[k]][1].append(r)


def med(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else 0


tier_rows = ""
for name, g in tiers:
    if not g:
        continue
    tier_rows += (f'<tr><td><b>{name}</b></td><td>{len(g)}</td>'
                  f'<td class="up"><b>+{med([x["ret"] for x in g]):.1f}%</b></td>'
                  f'<td class="down">{med([x["mdd"] for x in g]):.1f}%</td>'
                  f'<td>{med([x["turnover"] or 0 for x in g]):.2f}%</td>'
                  f'<td>{med([x["mv"] or 0 for x in g]):.0f} 亿</td></tr>')

# ---------- 个股卡片 ----------
CARDS = [
    ("沪电股份", "002463", "A", "算力 PCB 业绩标杆 · 但涨幅倒数第 6",
     ["2026H1 营收 136.89 亿（+61.17%）、归母净利 29.23 亿（+73.72%）；32 层以上产品同比 +190.83%，PCB 毛利率 40.52%，1.6T 交换机产品已批量出货",
      "8 月以来仅 +21.3%，市值 2421 亿，日均换手 2.13%，9 月 +0.7% —— 业绩最扎实、股价最迟钝",
      "7 月跌幅 -28.5%，在样本中属「跌得少」一档，超跌反弹空间天然受限；机构持仓集中，反弹面临解套抛压"],
     "业绩确定性最高、估值 PE 47.8 为算力链中偏低；但已被机构充分定价，不具备超跌弹性的爆发力。适合作为板块景气的「锚」，不适合做弹性。"),
    ("华正新材", "603186", "B", "唯一「业绩 + 股价」双高标的",
     ["2026H1 营收 29.6 亿（+41.28%）、归母净利 1.73 亿（+305.28%），Q2 单季净利 1.42 亿（+485%）、毛利率升至 18.72%（环比 +6.7pct）",
      "8 月以来 +133.0% 排名第 2，9 月仍 +37.8%，且 9/15 收盘即区间最高点（距高点 0%）",
      "逻辑最直接：CCL 连续七轮涨价即时进表，公司自述「覆铜板行业结构性上行、量价齐升」"],
     "本轮最强的一条逻辑链——涨价→毛利→利润，且已验证到报表。但 PE(TTM) 96.9、PB 16.0，估值已高；后续取决于第八轮涨价能否落地。"),
    ("崇达技术", "002815", "E", "超跌 + 提价落地 · 但业绩仍在恶化",
     ["8 月以来 +94.3%，9 月 +46.8%（继续加速），9 月量能为 8 月的 3.07 倍，日均换手 14.48%",
      "2026H1 营收 43.30 亿（+22.55%）但归母净利仅 1.52 亿（-31.30%）；珠海二厂投产爬坡，上半年收入 13.28 亿却净利 -754 万",
      "9/9 发布异动公告：因覆铜板、铜、金盐等原材料加速上涨，对线路板产品实施结构性提价"],
     "典型的「预期先行」：股价买的是提价后 Q3/Q4 的盈利拐点，而 H1 报表仍在恶化（财务费用 +129%、资产减值 5877 万）。提价能否传导到利润，是 Q3 报表需要验证的核心。"),
    ("超声电子", "000823", "E", "9 月最活跃 · 换手率全样本第一",
     ["8 月以来 +89.7%，9 月 +51.1%（排名第 2），9/15 单日换手率 40.42%，为 41 只样本最高",
      "2026H1 营收 33.51 亿（+10.04%）、归母净利 1.13 亿（-1.17%），毛利率 16.32%",
      "市值仅 142 亿，PE 64.3、PB 2.55（PB 在样本中偏低）"],
     "40% 的单日换手意味着筹码在一个交易日内几乎全部易手——这是典型的短线资金主导品种，波动会非常剧烈。低 PB + 小市值 + 涨价预期是资金选它的理由，但基本面并未跟上。"),
    ("胜宏科技", "300476", "A", "曾经的弹性龙头 · 已掉队 -21.4%",
     ["2026H1 营收 116.29 亿（+28.77%）、归母净利 28.57 亿（+33.30%）；高多层/高阶 HDI 排单延续至 2027 年，ASIC 算力 PCB 已量产",
      "8 月以来仅 +18.7%，且 8/13 即见顶，当前距高点 -21.4%，9 月 -7.0% —— 样本中「距高点」最深之一",
      "9 月量能仅为 8 月的 0.49 倍，缩量下跌"],
     "基本面没问题（净利 +33%、PE 44.2 不算贵），但它是 6 月行情的旧核心，7 月跌 -41.7% 后未能重新获得资金关注。缩量阴跌 + 高位套牢盘，是「旧龙头」的典型形态。"),
    ("满坤科技", "301132", "E", "9 月接力冠军 · 量能放大 2.57 倍",
     ["8 月以来 +124.5%，其中 9 月 +57.7% 为全样本第一；市值仅 92 亿，9/15 换手 22.57%",
      "9 月日均成交额为 8 月的 2.57 倍 —— 资金是 9 月才大举进入的",
      "2026H1 归母净利 4398 万（Q2 单季 2586 万），对比 2025 Q2 的 3505 万，实际同比是下滑的"],
     "「低位 + 小市值 + 涨价预期」的组合，与业绩无关。它的启动时点（9 月）比板块晚一个月，属于补涨链末端——这类品种通常在行情后段最活跃，也最先失去承接。"),
    ("科翔股份", "300903", "E", "涨幅冠军 · 但公司是亏损的",
     ["8 月以来 +133.9% 排名第 1，7 月跌 -51.9%（样本第 5 惨），「超跌反弹」弹性最大",
      "PE(TTM) -190（亏损），PB 26.27（全样本最高之一），市值 476 亿",
      "9 月 +17.4%，涨势已明显放缓"],
     "PB 26 倍的亏损股，是本轮行情「不看业绩、只看位置」的极端样本。涨幅与基本面完全脱钩，一旦风险偏好回落，这类品种的回撤也会最剧烈（7 月已演示过一次 -51.9%）。"),
    ("生益科技", "600183", "B", "CCL 真龙头 · 估值已到 PB 19.7",
     ["2026H1 营收 190.26 亿（+50%）、归母净利 32.87 亿；覆铜板及粘结片营收 123.57 亿（+47.74%）；中报预告增幅 117%~131%",
      "市值 3650 亿（全样本最大），8 月以来 +42.2%，但 9 月 -2.1% 走弱，日均换手仅 3.37%",
      "PE 70.3、PB 19.73 —— PB 处于自身历史极高位"],
     "覆铜板涨价的「确定性受益」，但市值太大、估值太高，缺乏弹性。9 月资金从大市值材料股流向小市值 PCB，是典型的「同逻辑换标的」。"),
    ("鼎泰高科", "301377", "C", "设备端的见顶样本 · 距高点 -17.3%",
     ["8 月以来仅 +14.9%，8/18 见顶后一路走弱，距高点 -17.3%，9 月 -4.2%，量能萎缩至 8 月的 0.57 倍",
      "PE 179.1、PB 54.63 —— 全样本估值最高",
      "同组的大族数控距高点 -18.5%（9 月 -7.7%）、芯碁微装 -13.2%，设备板块整体从 8 月中旬起被资金抛弃"],
     "设备是「扩产受益」的远端逻辑，兑现最慢。当行情从「产业逻辑」切换到「价格上涨的即期弹性」时，设备是最先被卖出的位置——高估值则放大了这一过程。"),
    ("鹏鼎控股", "002938", "D", "苹果链代表 · 本轮最弱主线",
     ["8 月以来仅 +9.0%，9 月 -4.8%，距高点 -14.7%，日均换手 0.70%（样本最低档）",
      "2026H1 营收 172.17 亿（+5.14%）、归母净利 12.84 亿；AI 服务器 PCB 收入接近 10 亿、光模块超 6 亿，但占比仍小",
      "拟募资不超过 96 亿元投 AI 服务器与高速光模块 HDI 项目"],
     "营收体量最大但增速最低（+5.14%），主业是消费电子 FPC。虽然正在切 AI，但市场给的是「消费电子估值」。它与东山精密（8 月以来 +6.6%，样本垫底）共同说明：没有 AI 叙事的 PCB 这轮基本没参与。"),
]

cards_html = ""
for name, code, grp, subtitle, bullets, judge in CARDS:
    r = BYN.get(name, {})
    fin = FIN.get(name, ("—", "—", ""))
    cards_html += f"""
<div class="scard">
  <div class="sc-head">
    <div><span class="sc-name">{name}</span> <span class="sc-code">{code}</span>
      <span class="tag tag-gray">{grp}</span></div>
    <div class="sc-sub">{subtitle}</div>
  </div>
  <div class="sc-nums">
    <div><span>8月以来</span><b class="up">{fm(r.get('ret'),1,'%')}</b></div>
    <div><span>7月</span><b class="{cl(r.get('ret_jul'))}">{fm(r.get('ret_jul'),1,'%')}</b></div>
    <div><span>9月</span><b class="{cl(r.get('ret_sep'))}">{fm(r.get('ret_sep'),1,'%')}</b></div>
    <div><span>距高点</span><b class="down">{fm(r.get('from_hi'),1,'%')}</b></div>
    <div><span>总市值</span><b>{fm(r.get('mv'),0)}亿</b></div>
    <div><span>PE / PB</span><b>{fm(r.get('pe'),1)} / {fm(r.get('pb'),2)}</b></div>
    <div><span>换手</span><b>{fm(r.get('turnover'),2,'%')}</b></div>
    <div><span>中报净利同比</span><b>{fin[0]}</b></div>
  </div>
  <ul class="sc-ul">{''.join(f'<li>{b}</li>' for b in bullets)}</ul>
  <div class="sc-judge"><b>定位判断｜</b>{judge}</div>
</div>"""

TPL = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PCB 板块代表性个股图谱与深度分析（2026-09-15）</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:"PingFang SC","Microsoft YaHei",sans-serif; background:#f7f8fa; color:#2b2f36; line-height:1.65; }
  .wrap { max-width:1080px; margin:0 auto; padding:28px 20px 60px; }
  h1 { font-size:26px; margin-bottom:6px; }
  .sub { color:#8a919c; font-size:13px; margin-bottom:24px; }
  h2 { font-size:19px; margin:36px 0 14px; padding-left:10px; border-left:4px solid #c0392b; }
  h3 { font-size:15px; margin:22px 0 10px; color:#3a4048; }
  .tldr { background:#fff; border:1px solid #e8eaee; border-radius:10px; padding:20px 22px; margin-bottom:8px; box-shadow:0 1px 3px rgba(0,0,0,.04); }
  .tldr li { margin:7px 0 7px 18px; font-size:14px; }
  table { width:100%; border-collapse:collapse; background:#fff; font-size:13px; border:1px solid #e8eaee; border-radius:8px; overflow:hidden; }
  th { background:#f0f2f5; padding:8px 10px; text-align:left; font-weight:600; color:#4a505a; white-space:nowrap; font-size:12.5px; }
  td { padding:7px 10px; border-top:1px solid #eef0f3; }
  tr:hover td { background:#fafbfc; }
  .up { color:#d0342c; } .down { color:#1e8e4e; } .muted { color:#8a919c; font-size:12.5px; }
  .chart { width:100%; height:420px; background:#fff; border:1px solid #e8eaee; border-radius:10px; padding:10px; box-shadow:0 1px 3px rgba(0,0,0,.04); }
  .note { font-size:12px; color:#9aa1ab; margin-top:8px; }
  .tag { display:inline-block; font-size:11px; padding:1px 7px; border-radius:10px; margin-right:4px; vertical-align:1px; }
  .tag-red { background:#fdeceb; color:#c0392b; } .tag-gray { background:#f0f2f5; color:#5a616c; }
  .src { font-size:12px; color:#9aa1ab; margin-top:6px; }
  .risk { background:#fff8e6; border:1px solid #f0e0b0; border-radius:10px; padding:14px 18px; margin-top:14px; font-size:13.5px; }
  .risk b { color:#a07000; }
  .conclusion { background:#fff; border:1px solid #e8eaee; border-left:4px solid #c0392b; border-radius:8px; padding:16px 20px; margin-top:14px; font-size:14px; }
  .conclusion p { margin:8px 0; }
  .scard { background:#fff; border:1px solid #e8eaee; border-radius:10px; padding:16px 20px; margin-bottom:14px; box-shadow:0 1px 3px rgba(0,0,0,.04); }
  .sc-head { border-bottom:1px solid #eef0f3; padding-bottom:8px; margin-bottom:10px; }
  .sc-name { font-size:17px; font-weight:700; }
  .sc-code { color:#8a919c; font-size:12.5px; margin-right:6px; }
  .sc-sub { color:#c0392b; font-size:13px; margin-top:3px; font-weight:600; }
  .sc-nums { display:flex; gap:8px; flex-wrap:wrap; margin:10px 0 12px; }
  .sc-nums > div { background:#fafbfc; border:1px solid #eef0f3; border-radius:7px; padding:6px 12px; min-width:92px; }
  .sc-nums span { display:block; font-size:11.5px; color:#8a919c; }
  .sc-nums b { font-size:15px; }
  .sc-ul { margin:6px 0 10px 18px; }
  .sc-ul li { font-size:13.5px; margin:5px 0; }
  .sc-judge { background:#fafbfc; border-radius:7px; padding:10px 14px; font-size:13.5px; border-left:3px solid #c0392b; }
  .sc-judge b { color:#c0392b; }
  .kpi { display:flex; gap:12px; flex-wrap:wrap; margin:16px 0; }
  .kpi > div { flex:1; min-width:170px; background:#fff; border:1px solid #e8eaee; border-radius:10px; padding:14px 16px; }
  .kpi .lb { font-size:12.5px; color:#5a616c; }
  .kpi .vl { font-size:24px; font-weight:700; margin:3px 0; }
  .kpi .ft { font-size:12px; color:#8a919c; }
</style>
</head>
<body>
<div class="wrap">
<h1>PCB 板块代表性个股图谱与深度分析</h1>
<div class="sub">样本 41 只 A 股 PCB 产业链（含 9 月新活跃品种 7 只：满坤科技、澳弘电子、威尔高、中京电子、金禄电子、逸豪新材、嘉立创）｜数据截至 2026-09-15 收盘｜行情：腾讯财经日 K 前复权；估值/市值/换手：通达信快照（2026-09-15）；中报：公司公告及主流财经媒体</div>

<div class="tldr">
<b>TL;DR 核心发现</b>
<ul>
<li><b>这轮行情最大的特征是「业绩与股价背离」。</b>涨幅前 10 名中，<b>6 只</b>2026 中报净利同比下滑或亏损（科翔股份、迅捷兴、博敏电子、中京电子为亏损；崇达技术 −31.3%、奥士康 −57.8%）；而业绩最强的算力核心资产——沪电股份（净利 +73.7%）、深南电路（+65.6%）、广合科技（+85~95%）、生益电子（+104~114%）——涨幅全部落在 <b>20%~33%</b>，排在样本后 1/3。</li>
<li><b>唯一「业绩 + 股价」双高的是覆铜板链</b>：华正新材净利 +305.3%、股价 +133.0%，且 9 月仍在加速（+37.8%，收盘即区间最高）。逻辑最直接也最硬：CCL 年内七轮涨价即时进报表。</li>
<li><b>市值与弹性严格负相关</b>：≥800 亿组中位涨幅 +20.5%、中位换手 2.92%；100–300 亿组 +74.1%、换手 8.86%；&lt;100 亿组 +68.0%、换手 13.08%。市值越小，涨得越多、换手越高、回撤也越大（小市值中位回撤 −25.1%）。</li>
<li><b>9 月出现明显的「接力换手」</b>：旧核心掉队——大族数控 −7.7%、东山精密 −7.7%、胜宏科技 −7.0%、鹏鼎控股 −4.8%、鼎泰高科 −4.2%；新面孔接力——满坤科技 +57.7%、超声电子 +51.1%、崇达技术 +46.8%、澳弘电子 +41.9%。接力品种的共同点是<b>小市值 + 9 月量能骤增</b>（澳弘 3.45 倍、崇达 3.07 倍、超声 2.69 倍、满坤 2.57 倍）。</li>
<li><b>设备与消费电子是两条被抛弃的主线</b>：设备（鼎泰高科距高点 −17.3%、大族数控 −18.5%）逻辑兑现最慢、估值最高（鼎泰 PB 54.6）；苹果链（鹏鼎 +9.0%、东山精密 +6.6%）缺乏 AI 叙事，本轮基本没参与。</li>
<li><b>交易含义</b>：本轮的定价锚是「① 超跌修复空间 ② 涨价向 PCB 端传导的预期」，<b>不是已兑现的业绩</b>。这意味着——跟踪的重点应从「谁的中报好」切换到「谁的提价能落进 Q3 报表」和「资金还在不在低位小票里」。</li>
</ul>
</div>

<h2>一、四个量化观察</h2>
<div class="kpi">
  <div><div class="lb">涨幅前 10 中业绩下滑/亏损</div><div class="vl up">6 / 10</div><div class="ft">科翔、迅捷兴、博敏为亏损；崇达 −31.3%、奥士康 −57.8%、超声 −1.2%</div></div>
  <div><div class="lb">市值分层中位涨幅差</div><div class="vl">53.6pct</div><div class="ft">≥800 亿 +20.5% vs 100–300 亿 +74.1%</div></div>
  <div><div class="lb">9 月换手率最高</div><div class="vl">40.4%</div><div class="ft">超声电子（单一交易日筹码几乎全部易手）</div></div>
  <div><div class="lb">强弱分化（首尾）</div><div class="vl">__SPREAD__pct</div><div class="ft">威尔高 +142.0% vs 东山精密 +6.6%</div></div>
</div>

<h3>1.1 市值分层：越小越猛，回撤也越深</h3>
<table>
<tr><th>市值分层</th><th>只数</th><th>中位涨幅（8 月以来）</th><th>中位最大回撤</th><th>中位换手率</th><th>中位市值</th></tr>
__TIER_ROWS__
</table>
<div class="note">涨幅随市值总体单调递减，但 <b>&lt;100 亿组（中位 +68.0%）反而略低于 100–300 亿组（+74.1%）</b>——原因是该组内包含天津普林、协和电子、金百泽等涨幅集中在 +30%~+55% 的品种，分布更分散。<b>但小市值组的两项「代价」仍然最高</b>：中位最大回撤 −25.1%（是大市值组 −15.9% 的 1.6 倍）、中位换手 13.08%。弹性来自市值小，风险也来自市值小。</div>
<div class="src">来源：行情数据自算；市值与换手为 2026-09-15 快照。中位数为组内中位数，未加权。</div>

<h3>1.2 市值 × 涨幅散点（颜色 = 角色）</h3>
<div id="c_scat" class="chart" style="height:460px"></div>
<div class="note">横轴市值取对数。左侧密集区（&lt;200 亿）是本轮涨幅的主战场，右侧（&gt;2000 亿）的红点在 +10%~+45% 区间被明显压低。<b>「大市值 = 低弹性」这条规律在 PCB 板块 8 月以来几乎无例外</b>；唯一偏离的是胜宏科技（2222 亿却只有 +18.7%）与东山精密（3349 亿、+6.6%）。</div>

<h3>1.3 换手率 × 涨幅：高换手全部集中在二三线</h3>
<div id="c_turn" class="chart" style="height:420px"></div>
<div class="note">换手率 &gt;10% 的 9 只全部是二三线制造（超声电子 40.4%、中京电子 35.2%、满坤科技 22.6%、博敏电子 18.9%、强达电路 16.9%）；而算力核心资产的换手率普遍在 1%~4%（深南电路 1.14%、鹏鼎控股 0.70%、大族数控 0.58%）。<b>换手率的差距，本质上是「谁在定价」的差距</b>：低换手 = 机构锁仓定价，高换手 = 短线资金反复博弈。</div>

<h2>二、九月的接力与掉队</h2>
<div id="c_sep" class="chart" style="height:460px"></div>
<div class="note">按 9 月涨幅排序，绿柱为 9 月下跌（掉队），红柱为 9 月上涨（接力）。<b>一个清晰的分界线</b>：8 月上旬领涨的算力/设备龙头（胜宏、大族、鼎泰、生益电子、天承）在 9 月集体转负；而 8 月中下旬启动的低位小票在 9 月继续加速。这说明资金在板块内部完成了一次<b>从「旧核心」向「低位补涨」的迁移</b>，而非板块整体退潮。</div>

<h2>三、全景图谱（41 只，按 8 月以来涨幅排序）</h2>
<div style="overflow-x:auto">
<table style="font-size:12.5px">
<tr><th>名称</th><th>代码</th><th>角色</th><th>8月以来</th><th>7月</th><th>9月</th><th>距高点</th><th>市值亿</th><th>2026中报净利同比</th><th>换手</th><th>9月/8月量能</th></tr>
__ROWS_ALL__
</table>
</div>
<div class="note">「9月接力 / 掉队」标签按 9 月涨幅与量能变化人工标记。「距高点」为 9/15 收盘相对 8 月以来最高价的涨跌幅。嘉立创为 2026-08-04 上市新股，「8 月以来」为上市以来涨幅，与其余标的不同口径。</div>
<div class="src">来源：行情数据自算（腾讯财经前复权）；市值/PE/PB/换手为 2026-09-15 通达信快照；中报数据来自公司公告及电子工程专辑、中国证券报、证券时报、上海证券报等媒体汇总。表格中「—」表示未见公开同比口径。</div>

<h2>四、五类角色拆解</h2>
<table>
<tr><th>角色</th><th>代表标的</th><th>本轮表现</th><th>资金性质</th><th>核心矛盾</th></tr>
<tr><td><b style="color:#d0342c">A｜算力核心资产</b></td><td>沪电股份、深南电路、胜宏科技、广合科技、生益电子、嘉立创</td><td class="up">+18.7% ~ +33.2%</td><td>机构锁仓，换手 1%~4%</td><td>业绩最好、涨得最少；旧筹码未出清</td></tr>
<tr><td><b style="color:#e08a2e">B｜覆铜板/材料</b></td><td>华正新材、生益科技、南亚新材、金安国纪、逸豪新材</td><td class="up">+42.2% ~ +133.0%</td><td>机构 + 游资混合</td><td>涨价直接进表（逻辑最硬），但 PB 已到历史高位</td></tr>
<tr><td><b style="color:#2c6bd0">C｜设备与耗材</b></td><td>鼎泰高科、大族数控、芯碁微装、天承科技</td><td class="up">+10.9% ~ +39.2%</td><td>资金持续流出</td><td>兑现最慢 + 估值最高，8 月中旬即见顶</td></tr>
<tr><td><b style="color:#1e8e4e">D｜消费电子/苹果链</b></td><td>鹏鼎控股、东山精密、弘信电子</td><td class="up">+6.6% ~ +16.0%</td><td>机构低换手</td><td>没有 AI 叙事，增速最低（鹏鼎营收 +5.1%）</td></tr>
<tr><td><b style="color:#8a5bd0">E｜二线弹性制造</b></td><td>科翔股份、迅捷兴、崇达技术、奥士康、超声电子、满坤科技等 23 只</td><td class="up">+16.0% ~ +142.0%</td><td>游资/短线主导，换手 4%~40%</td><td>业绩普遍下滑或亏损，纯位置 + 涨价预期驱动</td></tr>
</table>

<h2>五、十只有代表性的个股</h2>
__CARDS__

<h2>六、结论与风险</h2>
<div class="conclusion">
<p><b>如果只记一件事：本轮 PCB 行情的定价锚不是业绩，而是「位置」与「涨价传导预期」。</b>三条证据：① 涨幅前 10 中 6 只业绩下滑或亏损；② 业绩最强的算力核心资产涨幅排在后 1/3；③ 唯一「双高」的覆铜板链，恰好是涨价最直接受益、且能即时进表的环节。这反过来给出一个可操作的观察点：<b>当提价从 CCL 传导到 PCB 制造商的 Q3 报表时（10 月底三季报），真正的分化才会出现</b>——届时能证明「提价落进利润」的二线厂，与只有概念的低位股会被市场重新定价。</p>
<p><b>结构上，当前处于「旧核心退潮、低位补涨接力」的中后段。</b>判断依据：① 8 月中旬见顶的那批（胜宏、大族、鼎泰、东山、中富、芯碁）至今未收复，缩量阴跌；② 9 月接力的是市值最小、换手最高的一档（满坤、澳弘、超声），这类品种是行情后段的典型特征；③ 板块整体仍处缩量（9 月成交额为区间最低），缺乏增量资金。</p>
</div>
<div class="risk">
<b>风险提示：</b>
<ol style="margin:8px 0 0 20px; font-size:13.5px">
<li><b>估值与业绩的背离终会收敛。</b>科翔股份 PB 26.3、迅捷兴 PE 为负、鼎泰高科 PB 54.6、生益科技 PB 19.7 —— 高 PB 叠加业绩下滑的组合，在风险偏好回落时缺乏估值保护。</li>
<li><b>提价能否落到利润仍是未验证的假设。</b>崇达技术是最典型的样本：H1 净利 −31.3%（财务费用 +129%、资产减值 5877 万、珠海二厂净利 −754 万），公司 9/9 才公告结构性提价。这类「预期先行」的标的，Q3 报表是硬验证。</li>
<li><b>小市值高换手品种的流动性风险。</b>超声电子单日换手 40.4%、中京电子 35.2%，意味着筹码极不稳定；一旦资金撤离，缺乏承接。</li>
<li><b>板块整体缩量。</b>9 月日均成交额为区间最低，行情依赖涨价催化与情绪延续。</li>
<li><b>供给端远期压力。</b>2026 年行业资本开支同比增速超 180%，2027–2028 年集中投产后供需格局可能逆转。</li>
<li><b>数据口径提示。</b>本报告样本为自行圈定的 41 只，未使用官方成分股名单；等权与市值加权口径的结果会不同；中报同比数据来自公开披露与媒体汇总，部分为业绩预告区间，请以公司公告为准。</li>
</ol>
</div>

<div class="sub" style="margin-top:30px">免责声明：以上内容基于公开数据和量化分析，仅供参考，不构成投资建议。文中个股仅作为行情结构性分析样本，不构成任何买卖推荐。市场有风险，投资需谨慎。过往表现不预示未来收益。</div>
</div>

<script>
var SCAT=__SCAT__;
var TURN=__TURN__;
var SEP=__SEP__;

var c1=echarts.init(document.getElementById('c_scat'));
var sers=[];
Object.keys(SCAT).forEach(function(k){
  sers.push({name:k,type:'scatter',
    data:SCAT[k].data.map(function(p){return [p[0],p[1],p[2],p[3]];}),
    symbolSize:function(v){return Math.max(8,Math.min(30,4+Math.sqrt(v[2])*3));},
    itemStyle:{color:SCAT[k].color,opacity:0.82},
    label:{show:true,fontSize:9,color:'#5a616c',position:'top',
      formatter:function(p){return (p.value[0]<700||p.value[1]>70)?p.value[3]:'';}},
    labelLayout:{hideOverlap:true}
  });
});
c1.setOption({
  tooltip:{formatter:function(p){return p.value[3]+'<br>市值 '+p.value[0]+' 亿<br>8月以来 '+(p.value[1]>0?'+':'')+p.value[1]+'%<br>换手 '+p.value[2]+'%';}},
  legend:{data:Object.keys(SCAT),top:6,itemWidth:10,itemHeight:10},
  grid:{left:64,right:30,top:52,bottom:52},
  xAxis:{type:'log',name:'总市值(亿,对数)',min:20,max:5000},
  yAxis:{type:'value',name:'8月以来涨幅(%)',axisLabel:{formatter:'{value}%'}},
  series:sers
});

var c2=echarts.init(document.getElementById('c_turn'));
c2.setOption({
  tooltip:{trigger:'item',formatter:function(p){return p.value[2]+'<br>换手 '+p.value[0]+'%<br>8月以来 '+(p.value[1]>0?'+':'')+p.value[1]+'%';}},
  grid:{left:64,right:30,top:34,bottom:52},
  xAxis:{type:'value',name:'9/15 换手率(%)',axisLabel:{formatter:'{value}%'}},
  yAxis:{type:'value',name:'8月以来涨幅(%)',axisLabel:{formatter:'{value}%'}},
  series:[{type:'scatter',data:TURN,symbolSize:11,
    itemStyle:{color:function(p){return p.value[1]>50?'#d0342c':(p.value[1]>25?'#e08a2e':'#8a919c');},opacity:0.85},
    label:{show:true,fontSize:9.5,color:'#5a616c',position:'right',
      formatter:function(p){return p.value[0]>6?p.value[2]:'';}},
    labelLayout:{hideOverlap:true}}]
});

var c3=echarts.init(document.getElementById('c_sep'));
c3.setOption({
  tooltip:{trigger:'axis',axisPointer:{type:'shadow'}},
  legend:{data:['8月','9月'],top:6},
  grid:{left:56,right:26,top:48,bottom:110},
  xAxis:{type:'category',data:SEP.map(function(x){return x.n;}),axisLabel:{rotate:60,fontSize:10,interval:0}},
  yAxis:{type:'value',name:'月度涨幅(%)',axisLabel:{formatter:'{value}%'}},
  series:[
    {name:'8月',type:'bar',data:SEP.map(function(x){return x.a;}),itemStyle:{color:'#c9cdd4'}},
    {name:'9月',type:'bar',data:SEP.map(function(x){return x.s;}),
      itemStyle:{color:function(p){return p.value>=0?'#d0342c':'#1e8e4e';}}}
  ]
});

window.addEventListener('resize',function(){c1.resize();c2.resize();c3.resize();});
</script>
</body>
</html>
"""

html = (TPL
        .replace("__SPREAD__", f"{BYN['威尔高']['ret'] - BYN['东山精密']['ret']:.1f}")
        .replace("__TIER_ROWS__", tier_rows)
        .replace("__ROWS_ALL__", rows_all)
        .replace("__CARDS__", cards_html)
        .replace("__SCAT__", json.dumps(scat_role, ensure_ascii=False))
        .replace("__TURN__", json.dumps(turn_data, ensure_ascii=False))
        .replace("__SEP__", json.dumps(sep_mix, ensure_ascii=False)))

os.makedirs(REP, exist_ok=True)
p = os.path.join(REP, "PCB代表性个股图谱-20260915.html")
open(p, "w", encoding="utf-8").write(html)
print(f"[saved] {p} ({len(html)} bytes)")
print(f"样本 {len(S)} 只 | 角色 {len(ROLE)} 类 | 卡片 {len(CARDS)} 只")
