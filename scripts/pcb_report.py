# -*- coding: utf-8 -*-
"""PCB 板块 8 月以来走势复盘 - 生成 HTML 报告"""
import sys, os, json
sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")
REP = os.path.join(BASE, "reports")

st = json.load(open(os.path.join(OUT, "pcb_stats.json"), encoding="utf-8"))
ex = json.load(open(os.path.join(OUT, "pcb_extra.json"), encoding="utf-8"))

DATES = [d[5:] for d in st["axis"]]
EQ = st["eq_all"]
B = st["bench"]
AMT = [a["amt"] for a in st["amt"]]
STOCKS = st["stocks"]
DAILY = st["daily"]


def j(o):
    return json.dumps(o, ensure_ascii=False)


# 散点: [7月涨幅, 8月以来涨幅, 名称, 组]
sc = [[round(r["ret_jul"], 1), round(r["ret"], 1), r["name"], r["group"]]
      for r in STOCKS if r["ret_jul"] is not None]

# 涨幅条形(按8月以来排序)
bar = [{"n": r["name"], "v": round(r["ret"], 1), "g": r["group"], "j": round(r["ret_jul"], 1)}
       for r in sorted(STOCKS, key=lambda x: x["ret"])]

segs = ex["segs"]
seg_mat = [[round(v, 1) if v is not None else None for v in r["segs"]] for r in ex["stocks"]]
seg_names = [r["n"] for r in sorted(ex["stocks"], key=lambda x: -(x["r8"] or -999))]
seg_sorted = [r for r in sorted(ex["stocks"], key=lambda x: -(x["r8"] or -999))]
seg_mat = [[round(v, 1) if v is not None else None for v in r["segs"]] for r in seg_sorted]

max_amt = max(AMT)
avg6, avg7, avg8, avg9 = (ex["vol"]["2026-06"][1], ex["vol"]["2026-07"][1],
                          ex["vol"]["2026-08"][1], ex["vol"]["2026-09"][1])

# ===== 关键数字: 全部由数据推导, 不手写 =====
N_TOT = st["meta"]["n_pcb"]
_AX, _EQ = st["axis"], st["eq_all"]
EQ_LAST = _EQ[-1]
EQ_RET = EQ_LAST - 100.0


def seg_eq(d0, d1):
    return (_EQ[_AX.index(d1)] / _EQ[_AX.index(d0)] - 1) * 100


SEG1 = seg_eq("2026-07-31", "2026-08-18")
SEG2 = seg_eq("2026-08-18", "2026-08-24")
SEG3 = seg_eq("2026-08-24", "2026-09-15")
SEG_RALLY = seg_eq("2026-08-03", "2026-08-07")
AUG_M = _EQ[_AX.index("2026-08-31")] - 100.0
SEP_M = (_EQ[-1] / _EQ[_AX.index("2026-08-31")] - 1) * 100

_peak, _mdd, _pk, _lo, _pk_at = _EQ[0], 0.0, _AX[0], _AX[0], _AX[0]
for _v, _d in zip(_EQ, _AX):
    if _v > _peak:
        _peak, _pk = _v, _d
    _dd = _v / _peak - 1
    if _dd < _mdd:
        _mdd, _lo, _pk_at = _dd, _d, _pk
MDD, MDD_FROM, MDD_TO = _mdd * 100, _pk_at[5:], _lo[5:]
N_BIG = len([d for d in DAILY if abs(d["eq_chg"]) >= 5])
N_UP = len([d for d in DAILY if d["up"] >= N_TOT])
N_DN = len([d for d in DAILY if d["dn"] >= N_TOT])
# 7月个股跌幅中位数(6/30->7/31)
_j7 = sorted(r["ret_jul"] for r in STOCKS if r["ret_jul"] is not None)
MED_JUL = _j7[len(_j7) // 2]
EXCESS = EQ_RET - (-3.01)

print(f"[report] 指数 {EQ_LAST:.2f} (+{EQ_RET:.2f}%) | 三段 {SEG1:+.2f}/{SEG2:+.2f}/{SEG3:+.2f} | "
      f"MDD {MDD:.2f}% | 异动{N_BIG} 全涨{N_UP} 全跌{N_DN} | 8月{AUG_M:+.2f}% 9月{SEP_M:+.2f}%")


def cls(v):
    return "up" if v > 0 else ("down" if v < 0 else "")


def f2(v, sign=True):
    if v is None:
        return "-"
    return f"{v:+.2f}%" if sign else f"{v:.2f}%"


# ===== 表格行 =====
seg_head = "".join(f"<th>{s}</th>" for s in segs)
seg_rows = ""
for r, m in zip(seg_sorted, seg_mat):
    cells = "".join(
        f'<td class="{cls(v)}">{v:+.1f}%</td>' if v is not None else "<td>-</td>" for v in m)
    seg_rows += f'<tr><td><b>{r["n"]}</b></td>{cells}<td class="{cls(r["r8"])}"><b>{f2(r["r8"])}</b></td></tr>'

daily_rows = ""
N_TOT = st["meta"]["n_pcb"]
for d in DAILY:
    eq_c = cls(d["eq_chg"])
    hs_c = cls(d["hs300_chg"] or 0)
    nb = ""
    if abs(d["eq_chg"]) >= 5:
        nb = '<span class="tag tag-red">异动</span>'
    elif d["dn"] >= N_TOT:
        nb = '<span class="tag tag-gray">全跌</span>'
    elif d["up"] >= N_TOT:
        nb = '<span class="tag tag-red">全涨</span>'
    daily_rows += (f'<tr><td>{d["d"][5:]}</td><td class="{eq_c}">{f2(d["eq_chg"])}</td>'
                   f'<td class="{hs_c}">{f2(d["hs300_chg"])}</td><td>{d["amt"]:.0f}</td>'
                   f'<td>{d["up"]}/{d["dn"]}</td><td>{d["best"][0]} <span class="{cls(d["best"][1])}">{d["best"][1]:+.1f}%</span></td>'
                   f'<td>{d["worst"][0]} <span class="{cls(d["worst"][1])}">{d["worst"][1]:+.1f}%</span></td><td>{nb}</td></tr>')

top10 = STOCKS[:10]
bot10 = STOCKS[-10:]
def stock_rows(rows):
    s = ""
    for r in rows:
        s += (f'<tr><td>{r["name"]}</td><td class="muted">{r["group"]}</td>'
              f'<td class="up"><b>{f2(r["ret"])}</b></td>'
              f'<td class="{cls(r["ret_jul"])}">{f2(r["ret_jul"])}</td>'
              f'<td class="muted">{r["hi_d"][5:]}</td>'
              f'<td class="down">{f2(r["ret_jul"]) if False else f2_static(r["cur_from_hi"])}</td></tr>')
    return s


def f2_static(v):
    return f"{v:+.2f}%"


def stock_rows2(rows):
    s = ""
    for r in rows:
        s += (f'<tr><td>{r["name"]}</td><td class="muted">{r["group"]}</td>'
              f'<td class="up"><b>{r["ret"]:+.1f}%</b></td>'
              f'<td class="{cls(r["ret_jul"])}">{r["ret_jul"]:+.1f}%</td>'
              f'<td class="muted">{r["hi_d"][5:]}</td>'
              f'<td class="down">{r["cur_from_hi"]:+.1f}%</td></tr>')
    return s


TPL = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PCB板块8月以来走势复盘（2026-08-03 ~ 2026-09-15）</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:"PingFang SC","Microsoft YaHei",sans-serif; background:#f7f8fa; color:#2b2f36; line-height:1.65; }
  .wrap { max-width:1080px; margin:0 auto; padding:28px 20px 60px; }
  h1 { font-size:26px; margin-bottom:6px; }
  .sub { color:#8a919c; font-size:13px; margin-bottom:24px; }
  h2 { font-size:19px; margin:36px 0 14px; padding-left:10px; border-left:4px solid #c0392b; }
  h3 { font-size:15px; margin:20px 0 8px; color:#3a4048; }
  .tldr { background:#fff; border:1px solid #e8eaee; border-radius:10px; padding:20px 22px; margin-bottom:8px; box-shadow:0 1px 3px rgba(0,0,0,.04); }
  .tldr li { margin:7px 0 7px 18px; font-size:14px; }
  .cards { display:flex; gap:14px; flex-wrap:wrap; margin:18px 0; }
  .card { flex:1; min-width:200px; background:#fff; border:1px solid #e8eaee; border-radius:10px; padding:16px 18px; box-shadow:0 1px 3px rgba(0,0,0,.04); }
  .card .name { font-size:13px; color:#5a616c; }
  .card .big { font-size:29px; font-weight:700; margin:2px 0; }
  .up { color:#d0342c; } .down { color:#1e8e4e; } .muted { color:#8a919c; font-size:12.5px; }
  .card .meta { font-size:12.5px; color:#8a919c; }
  table { width:100%; border-collapse:collapse; background:#fff; font-size:13px; border:1px solid #e8eaee; border-radius:8px; overflow:hidden; }
  th { background:#f0f2f5; padding:8px 10px; text-align:left; font-weight:600; color:#4a505a; white-space:nowrap; font-size:12.5px; }
  td { padding:7px 10px; border-top:1px solid #eef0f3; }
  tr:hover td { background:#fafbfc; }
  .chart { width:100%; height:400px; background:#fff; border:1px solid #e8eaee; border-radius:10px; padding:10px; box-shadow:0 1px 3px rgba(0,0,0,.04); }
  .note { font-size:12px; color:#9aa1ab; margin-top:8px; }
  .tag { display:inline-block; font-size:11px; padding:1px 7px; border-radius:10px; margin-right:4px; vertical-align:1px; }
  .tag-red { background:#fdeceb; color:#c0392b; } .tag-gray { background:#f0f2f5; color:#5a616c; }
  .risk { background:#fff8e6; border:1px solid #f0e0b0; border-radius:10px; padding:14px 18px; margin-top:14px; font-size:13.5px; }
  .risk b { color:#a07000; }
  .src { font-size:12px; color:#9aa1ab; margin-top:6px; }
  .conclusion { background:#fff; border:1px solid #e8eaee; border-left:4px solid #c0392b; border-radius:8px; padding:16px 20px; margin-top:14px; font-size:14px; }
  .conclusion p { margin:8px 0; }
  .kv { display:flex; gap:10px; flex-wrap:wrap; margin:10px 0; }
  .kv div { background:#fff; border:1px solid #e8eaee; border-radius:8px; padding:10px 14px; font-size:13px; }
  .kv b { font-size:17px; display:block; margin-top:2px; }
  .two { display:flex; gap:16px; flex-wrap:wrap; }
  .two > div { flex:1; min-width:320px; }
</style>
</head>
<body>
<div class="wrap">
<h1>PCB 板块 8 月以来走势复盘</h1>
<div class="sub">区间：2026-08-03 ~ 2026-09-15（基准日 2026-07-31 收盘）｜样本：34 只 PCB 产业链 A 股（PCB 制造 26 + 覆铜板 4 + 设备耗材 4）｜行情：腾讯财经日 K 前复权，板块指数为等权合成｜消息面：公开媒体与券商转述（可信度已分级标注）</div>

<div class="tldr">
<b>TL;DR 结论先行</b>
<ul>
<li><b>板块等权指数 8 月以来 __EQ_RET__%</b>（100 → __EQ_LAST__），其中 8 月单月 <b>+__AUG_M__%</b>、9 月上半月 <b>+__SEP_M__%</b>；同期沪深300 <span class="down">-3.01%</span>、创业板指 <span class="down">-2.87%</span>，超额收益约 <b>+__EXCESS__pct</b>——但这是 <b>7 月板块普跌 __MED_JUL__% 之后的 V 型修复</b>，不是新增趋势的起点。</li>
<li><b>三段式节奏</b>：① 8/3-8/18 反弹（+__SEG1__%，其中 8/4-8/7 四个交易日 <b>+__SEG_RALLY__%</b>）→ ② 8/19-8/24 两次全板块级急跌（__SEG2__%，两天均 34/34 全线下跌）→ ③ 8/25-9/15 缩量新高（+__SEG3__%，9/15 收于区间最高）。</li>
<li><b>四个走势特征</b>：高 β 高波动（年化波动率 58.7%，单日 |涨跌| ≥5% 的板块级波动出现 <b>__N_BIG__ 次</b>）、涨跌高度同步（__N_UP__ 天 34/34 全涨、__N_DN__ 天 34/34 全跌，个股趋势让位于板块 β）、缩量修复（8 月日均成交额仅 6 月高点的 65%，9 月指数创新高时量能最低）、内部极致分化（首尾涨幅相差 <b>127pct</b>）。</li>
<li><b>分化有明确规律</b>：7 月跌幅与 8 月涨幅显著负相关（<b>r = -0.41</b>，回归斜率 -1.17）；强度排序为 <b>覆铜板/上游材料 &gt; 二三线 PCB &gt; 一线 AI 龙头 &gt; 苹果链 FPC 与部分设备</b>。领涨的科翔股份、华正新材、迅捷兴，恰是 7 月跌幅最大的品种。</li>
<li><b>归因（事实 vs 演绎要分开）</b>：7 月暴跌 = 交易拥挤 + 融资盘踩踏 + 海外传闻扰动 + 全球科技股共振（技术与资金面因素为主，行业基本面未恶化）；8 月反转 = 覆铜板/电子布<b>连续实物涨价</b> + 中报业绩兑现 + AI 订单能见度；9 月新高 = 建滔第八轮涨价预期 + 松下/南亚塑胶 9/1 提价 + 英伟达 Vera Rubin 确认进客户数据中心。</li>
<li><b>最关键的一条隐忧</b>：本轮上涨是<b>缩量修复</b>——涨幅收复了 7 月失地，但量能从未回到 6 月水平，且 9 月创新高时成交额反而创区间新低，价量背离说明增量资金有限，行情更依赖涨价催化与情绪，而非资金面扩张。</li>
</ul>
</div>

<h2>一、核心数据速览</h2>
<div class="cards">
  <div class="card">
    <div class="name">PCB 等权板块指数（7/31 = 100）</div>
    <div class="big up">__EQ_LAST__</div>
    <div class="meta">8 月以来 <b class="up">+__EQ_RET__%</b>｜9/15 收于区间最高点｜最大回撤 __MDD__%（__MDD_FROM__→__MDD_TO__）</div>
  </div>
  <div class="card">
    <div class="name">同期沪深300</div>
    <div class="big down">-3.01%</div>
    <div class="meta">创业板指 -2.87%｜中证全指通信 +6.17%｜中证半导体 +3.28%</div>
  </div>
  <div class="card">
    <div class="name">板块年化波动率</div>
    <div class="big">58.7%</div>
    <div class="meta">沪深300 同期约 15%~18%｜β 粗略估算 2~3 倍</div>
  </div>
  <div class="card">
    <div class="name">个股首尾涨幅差</div>
    <div class="big">127pct</div>
    <div class="meta">最高 科翔股份 +133.9%｜最低 东山精密 +6.6%</div>
  </div>
</div>
<div class="src">来源：腾讯财经 web.ifzq.gtimg.cn 日 K（前复权），等权指数为 34 只样本日收益率算术平均后累乘，自行计算。等权口径下小市值弹性标的权重被放大，与市值加权指数（如通达信 PCB 概念指数）数值不可直接比较。</div>

<h2>二、走势全貌：指数与基准对比</h2>
<div id="c_main" class="chart" style="height:440px"></div>
<div class="note">板块指数 8 月首个交易日（8/3）小幅下跌 -1.53%，随后 8/4-8/7 四个交易日暴涨 <b class="up">+28.9%</b>，一举收复 7 月失地的约七成；8/19 单日 <b class="down">-8.19%</b> 抹去前期约 8% 涨幅；此后板块与大盘走势完全脱钩——9 月沪深300 连续走弱（9/15 收 -0.67%），PCB 反而连续 6 个交易日收阳并创新高。</div>
<div class="src">来源：腾讯财经日 K 前复权，自行合成。基准均以 2026-07-31 收盘归一化为 100。</div>

<h2>三、特征一：V 型反转，起点是 7 月的极端超跌</h2>
<p style="font-size:14px">8 月的涨幅必须放在 7 月的跌幅里看。7 月单月，34 只样本中有 33 只下跌，跌幅中位数约 <b class="down">__MED_JUL__%</b>，天承科技、金安国纪、四会富仕、博敏电子、科翔股份、华正新材 6 只跌超 50%——这是典型的<b>板块级踩踏</b>，而非个股基本面分化。</p>
<table>
<tr><th>7 月跌幅最大（前 8）</th><th>7 月跌幅</th><th>8 月以来涨幅</th><th>7 月跌幅最小（前 8）</th><th>7 月跌幅</th><th>8 月以来涨幅</th></tr>
__REBOUND_ROWS__
</table>
<div class="note">"7 月跌得最狠的，8 月涨得最多"——这条规律几乎贯穿全表。量化验证见第六节散点图。</div>
<div class="src">来源：行情数据自算；7 月区间取 2026-06-30 收盘至 2026-07-31 收盘。</div>

<h2>四、特征二：高 β 高波动，日内涨跌高度同步</h2>
<div class="kv">
  <div>单日板块级异动（|涨跌| ≥ 5%）<b class="up">__N_BIG__ 次</b></div>
  <div>全板块同向日（34/34）<b>__N_UP__+__N_DN__ = __N_SAME__ 次</b>（全涨 __N_UP__ / 全跌 __N_DN__）</div>
  <div>8/19 单日跌幅<b class="down">-8.19%</b></div>
  <div>同期沪深300 单日最大跌幅<b class="down">-2.90%</b></div>
</div>
<p style="font-size:14px">板块内部个股趋势几乎被 β 抹平：8/19、8/24 两天 34 只样本<b>无一上涨</b>；8/4、8/7、8/12、8/27、9/7 五天<b>无一显著下跌</b>。这说明 8 月以来的行情是<b>整体资金驱动的板块行情</b>，而非个股 Alpha 驱动的结构性行情——交易上"选板块重于选个股"的特征非常明显。</p>
<div class="src">来源：日度收益率自算，阈值 0.01%。</div>

<h2>五、走势时间轴：关键节点拆解</h2>
<table>
<tr><th>日期</th><th>板块指数涨跌</th><th>沪深300</th><th>成交额(亿)</th><th>涨/跌家数</th><th>最强</th><th>最弱</th><th>节点</th></tr>
__DAILY_ROWS__
</table>
<div class="note">成交额为估算值（成交量 × 当日均价），仅用于内部横向比较，非交易所口径。8/19、8/24 两天板块跌幅分别为 -8.19%、-3.60%，且均为全板块下跌，与沪深300 当日 -2.90%、-1.21% 同步——属于大盘系统性调整日板块以更高 β 放大跌幅。</div>
<div class="src">来源：行情数据自算。"节点"标签为按涨跌幅与涨跌家数自动标记。</div>

<h3>三段式节奏归纳</h3>
<table>
<tr><th>阶段</th><th>区间</th><th>板块涨幅</th><th>特征</th></tr>
<tr><td><b>① 反弹修复</b></td><td>8/3 - 8/18</td><td class="up">+__SEG1__%</td><td>8/3 首日小跌 -1.53%，8/4-8/7 四日暴涨 +__SEG_RALLY__%，多日 34/34 全涨；覆铜板与超跌小票领涨，中报预告与涨价函密集落地</td></tr>
<tr><td><b>② 急跌洗盘</b></td><td>8/19 - 8/24</td><td class="down">__SEG2__%</td><td>两次全板块下跌（34/34）；跟随大盘系统性调整，高 β 放大跌幅；此前强势股（胜宏、鼎泰、大族）开始跑输</td></tr>
<tr><td><b>③ 缩量新高</b></td><td>8/25 - 9/15</td><td class="up">+__SEG3__%</td><td>慢涨、低波动、缩量；9/7 单日 +7.81% 全板块上涨；超跌低位股持续新高，AI 一线龙头与苹果链持续落后</td></tr>
</table>

<h2>六、特征三：缩量修复，价量背离</h2>
<div id="c_amt" class="chart" style="height:360px"></div>
<div class="note">板块日均成交额：6 月 <b>128.3 亿</b> → 7 月 92.0 亿 → 8 月 <b>83.5 亿</b> → 9 月 <b>78.8 亿</b>（成交量口径：8049.6 → 5900.1 → 5835.5 → 6154.6 万手）。<b>9 月指数创区间新高，日均成交额却是全区间最低</b>。价格收复了 7 月失地，但量能仅恢复到 6 月高点的 61%~65%。</div>
<p style="font-size:14px">缩量上涨有两种解释，需要同时保留：<b>偏多解释</b>——7 月恐慌抛售已完成筹码换手，套牢盘减少、抛压轻，少量买盘即可推升；<b>偏空解释</b>——增量资金并未回流，行情靠涨价催化与情绪维持，一旦催化断档，缺乏承接资金。区分二者的观察指标是：成交额能否重回 6 月水平（120 亿以上），以及上涨日的量价配合度。</p>
<div class="src">来源：成交量取自腾讯财经日 K；成交额 = 成交量 × (最高+最低+收盘)/3，为估算值，因前复权价格调整可能与真实成交额有偏差，仅作趋势比较。</div>

<h2>七、特征四：内部极致分化（最重要的结构特征）</h2>
<div id="c_scatter" class="chart" style="height:420px"></div>
<div class="note">横轴为 7 月涨跌幅，纵轴为 8 月以来涨跌幅。散点呈现明显的<b>负斜率</b>：<b>r = -0.41，回归斜率 -1.17（7 月每多跌 1%，8 月平均多涨 1.17%）</b>。绿点（覆铜板/材料）整体位于左上——7 月跌得多、8 月涨得多；蓝点（PCB 制造）分布最散；橙点（设备）居中；最右下方的是苹果链与部分一线龙头。</div>

<h3>涨幅两端对照</h3>
<div class="two">
<div>
<table>
<tr><th>8 月以来涨幅 TOP 10</th><th>板块</th><th>8月以来</th><th>7 月</th><th>高点</th><th>距高点</th></tr>
__TOP10_ROWS__
</table>
</div>
<div>
<table>
<tr><th>8 月以来涨幅 BOTTOM 10</th><th>板块</th><th>8月以来</th><th>7 月</th><th>高点</th><th>距高点</th></tr>
__BOT10_ROWS__
</table>
</div>
</div>
<div class="src">"高点"= 8 月以来最高价出现日，"距高点"= 9/15 收盘相对该高点的涨跌幅。来源：行情数据自算。</div>

<h3>分阶段涨幅矩阵（%）</h3>
<div style="overflow-x:auto">
<table style="font-size:12.5px">
<tr><th>标的</th>__SEG_HEAD__<th>8月以来</th></tr>
__SEG_ROWS__
</table>
</div>
<div class="note">按 8 月以来涨幅降序排列。观察规律：① 8/3-8/7 首轮反弹中，涨幅与 7 月跌幅高度相关（科翔 +54.6%、胜宏 +47.2%、中富 +41.7%）；② 8/19-8/24 急跌中，几乎所有标的同步下跌且幅度接近（-5.7% ~ -16.6%），印证 β 主导；③ 9/7-9/15 最后一轮，分化重新出现——超声电子 +64.9%、崇达技术 +48.9%、华正新材 +48.7% 继续加速，而胜宏科技仅 +3.0%、大族数控 +1.6%，前期强势股已明显掉队。</div>

<h2>八、原因分析</h2>

<h3>8.1 为什么 7 月会暴跌（这是理解 8 月的前提）</h3>
<table>
<tr><th>因素</th><th>具体内容</th><th>属性</th></tr>
<tr><td><b>交易拥挤度</b></td><td>7 月初 TMT 板块成交占比超过 45%；热门股成交占全市场比重 7/14 创 2020 年以来新高 28%；上半年 PCB 算力赛道整体涨幅近 100%，部分标的涨 300%-500%</td><td>资金面 / 硬数据</td></tr>
<tr><td><b>杠杆资金踩踏</b></td><td>7 月 A 股融资余额连续 13 个交易日缩水，较 6 月末高点累计减少约 2231 亿元，PCB 及电子板块是融资净卖出重灾区；7/17 部分融资盘触发追保</td><td>资金面 / 硬数据</td></tr>
<tr><td><b>海外消息扰动</b></td><td>① 有半导体研究机构称英伟达 Kyber NVL144 机架因 PCB 中板瓶颈可能延迟至 2028（黄仁勋 7/15 已否认 Vera Rubin 延期）；② 三星、SK 海力士 7 月初向下游基板供应商提出下半年降价要求；③ 市场传闻部分 PCB 龙头因质量问题丢失大客户订单（后续澄清）</td><td>传闻 / 需谨慎对待</td></tr>
<tr><td><b>全球科技股共振</b></td><td>韩国股市因散户杠杆踩踏进入技术性熊市，三星电子、SK 海力士跌超 25%；费城半导体指数回调近两成；美债利率反弹压制成长股估值；港股建滔集团较 6 月高点近乎腰斩</td><td>外围 / 硬数据</td></tr>
<tr><td><b>中报"利好出尽"</b></td><td>上半年股价已大幅透支业绩预期，高预增中报落地反而成为兑现由头（多家公司中报预增 50%-543%，但股价已提前反映）</td><td>市场行为</td></tr>
</table>
<div class="src">来源：今日头条《半年报预增最高543%的PCB板块，为何成7月跌幅重灾区》（2026-07，自媒体，含具体资金数据但未给出原始出处）、中国经营报数字报（2026-07-27，传统媒体，含格上基金/西南财大研究员访谈）、腾讯新闻《PCB行业日报》（2026-07-18，媒体汇编）、长桥证券（2026-07，券商内容平台）。<b>上述为媒体转述口径，非交易所或公司公告原文，引用需谨慎。</b>可交叉验证的硬数据：融资余额变化、指数涨跌幅、公司中报数字。</div>
<div class="risk"><b>要点：</b>7 月的下跌中，<b>基本面并未恶化</b>——同期多家公司披露的中报预增幅度在 50%-130% 区间（沪电股份预增 68%-78%、生益科技 117%-131%、深南电路 54%-69%）。价格下跌的驱动是拥挤度、杠杆与情绪，而非盈利。这一点是 8 月能快速反转的根本原因。</div>

<h3>8.2 为什么 8 月能迅速反转（四条可直接验证的驱动）</h3>
<table>
<tr><th>驱动</th><th>关键事实</th><th>可信度</th></tr>
<tr><td><b>① 上游连续实物涨价</b></td><td>建滔积层板年内第 7 份涨价函（8 月底）：全厚度 FR-4 统一涨 10%，PP 半固化片按规格涨 10%-20%，仅 FR-4 按复利计年内累计涨幅超 100%；松下机电自 9/1 起对普通多层板 CCL 及 PP 涨价 30%；南亚塑胶 9/1 起 CCL 及 PP 涨 20%-25%；中国巨石 9 月电子布厚布涨 15%、薄布涨 20%，电子布 8 月单月涨约 20%、9 月再涨 15%-20%</td><td>高（多家公司/媒体独立报道，涨函可追溯）</td></tr>
<tr><td><b>② 中报业绩兑现</b></td><td>沪电股份 H1 营收 136.89 亿 / +61.17%，归母净利 29.23 亿，数据通信 PCB 收入 113.3 亿 / +73.46%，32 层以上产品同比 +190.83%；深南电路 H1 营收 152.96 亿 / +46.33%，净利 22.51 亿 / +65.55%；生益科技 H1 营收 190.26 亿 / +50%，净利 32.87 亿；胜宏科技 H1 营收 116.29 亿 / +28.77%，净利 28.57 亿 / +33.30%；鹏鼎控股 H1 营收 172.17 亿 / +5.14%，净利 12.84 亿</td><td>中高（媒体转述中报，建议核对公告原文）</td></tr>
<tr><td><b>③ AI 订单能见度</b></td><td>头部厂商高端 PCB 订单排至 2026Q4，部分客户锁单至 2027 年年中；北美 PCB 7 月订单同比 +60%、出货 +14.5%；高盛 8/6 大幅上调 AI 服务器 PCB 市场预测（2027 年 375 亿美元 → 2028 年 840 亿美元，2026-2028 CAGR 约 148%）</td><td>中（卖方与行业协会口径，转述）</td></tr>
<tr><td><b>④ 估值回落到低位后资金回流</b></td><td>7 月板块估值回落至历史低位区间后，7/28 起中长线资金逢低布局，7/29 元件板块获全天主力资金净流入 18.92 亿元，居全行业首位</td><td>中（媒体引述资金数据）</td></tr>
</table>
<div class="src">来源：新华财经（2026-09-14）、中国经济新闻网（2026-09-09）、腾讯新闻（2026-09-14）、顶尖财经网（2026-08-17）、今日头条（自媒体，2026-08）；券商观点转引自东北证券、浙商证券、国盛证券、招商证券、高盛。分析师预测为卖方观点，非既成事实。</div>

<h3>8.3 为什么领涨的是"覆铜板 + 二三线"，而不是 AI 一线龙头？</h3>
<div class="conclusion">
<p><b>这是本轮行情最需要解释的结构特征。</b>8 月以来涨幅前 10 中，8 只属于二三线 PCB（科翔股份、迅捷兴、崇达技术、奥士康、超声电子、博敏电子、四会富仕、强达电路），2 只属于覆铜板（华正新材、金安国纪）；而 AI 算力最核心的沪电股份（+21.3%）、胜宏科技（+18.7%）反而排名靠后。</p>
<p><b>四条可能解释（按证据强度排序）：</b></p>
<p>① <b>弹性的数学来源——超跌反弹的β不对称</b>（证据最强）。7 月跌 50% 的股票反弹 50% 只回到原点，而 7 月只跌 20% 的股票反弹空间天然更小。数据验证：回归斜率 -1.17，即 7 月多跌 1% 对应 8 月多涨 1.17%。这解释了大部分涨幅差异。</p>
<p>② <b>涨价传导链条的受益顺序</b>（证据较强）。本轮涨价源头在电子布/铜箔 → CCL → PCB。覆铜板企业的涨价可即时落地、毛利弹性直接体现（生益科技 H1 净利预增 117%-131% 即为印证）；二三线 PCB 因成本占比高、前期利润率被压缩更狠，一旦能提价，业绩弹性反而大于高端占比高的一线厂。崇达技术 9/9 公告"对线路板产品实施结构性提价"、金禄电子披露 Q2 订单均价环比 +21.77%，是该逻辑的落地证据。</p>
<p>③ <b>筹码结构与资金偏好</b>（证据中等）。7 月机构在龙头上演"净卖出+北向抄底"（7/20 东山精密机构席位净卖出 5.13 亿、同日深股通净买入 6.48 亿），说明一线龙头机构持仓集中、上方套牢盘重、反弹时面临解套抛压；而 LOW 位小票筹码更干净，游资与散户资金更容易推动。</p>
<p>④ <b>比价效应与题材扩散</b>（证据较弱，偏演绎）。当龙头估值已高企、涨幅已消化，资金转向"同题材、低位置、小市值"的品种做补涨，是 A 股题材行情的常见路径。9/14 涨停的满坤科技、中京电子、澳弘电子等多为此类。</p>
</div>
<div class="risk"><b>反向提示：</b>不要把"低位补涨"直接等同于"更好的机会"。① 二三线厂商的高端 AI 板占比低，涨价传导的持续性依赖成本能否继续向下游转嫁——若上游电子布价格回落或行业扩产放量，弹性品种的业绩基础最脆弱；② 一线龙头 7 月跌幅小，本身反映了更强的盈利韧性与机构定价；③ 从"距高点"一列看，胜宏科技 -21.4%、鼎泰高科 -17.3%、大族数控 -18.5%、东山精密 -16.8% 已明显走弱，而超跌小票仍在创新高——这种结构若持续，往往意味着行情进入"补涨尾声"而非"主升延续"。</div>

<h3>8.4 为什么 8/19、8/24 出现全板块急跌？</h3>
<p style="font-size:14px">两天的共同特征：板块跌幅（-8.19%、-3.60%）显著大于沪深300（-2.90%、-1.21%），且 34 只样本无一上涨。这符合<b>高 β 板块在系统性调整日放大跌幅</b>的典型模式，而非板块自身出现利空。可验证的观察是：这两天传媒、电子等同期高位板块同步下跌，而银行、电力等低估值板块相对抗跌，是市场层面的风格再平衡。<b>本次检索未找到 8/19 当日明确的事件性利空，此处不做强行归因。</b></p>

<h3>8.5 为什么 9 月能继续创新高？</h3>
<p style="font-size:14px">9 月的催化比 8 月更"实"：<b>①</b> 涨价从预期走向落地并向 PCB 端传导——建滔 8 月底第 7 轮涨函后，花旗预期 10 月初可能启动第 8 轮；松下、南亚塑胶 9/1 正式执行新价；中国巨石 9 月执行电子布新价。<b>②</b> 需求从预期走向交付——英伟达 Vera Rubin 已确认进入客户数据中心（微软确认首批生产型 Rubin 到货、AWS 收到 Vera CPU 与 Rubin GPU），单卡 PCB 价值量从 GB 系列的约 400 美元提升到 800 美元以上；谷歌 V8、AMD Helios 等三季度陆续出货。<b>③</b> 中报落地后，涨价对 Q3 业绩的贡献成为新的预期锚（浙商证券：涨价效果自 2026Q3 起逐步体现）。</p>
<div class="src">来源：新华财经（2026-09-14）、中国经济新闻网（2026-09-09）、腾讯新闻《PCB板块多股涨停》（2026-09-14）。均为媒体转述券商观点与产业链访谈，非公司公告。</div>

<h2>九、风险提示与后续观察指标</h2>
<div class="risk">
<b>主要风险：</b>
<ol style="margin:8px 0 0 20px; font-size:13.5px">
<li><b>价量背离未修复</b>：9 月指数创新高但成交额为区间最低，缩量上涨的持续性依赖催化不断档。</li>
<li><b>涨价逻辑的反身性</b>：涨价越猛，下游（PCB 厂、终端）的成本压力越大，若 AI 服务器出货节奏或客户接受度低于预期，涨价链条可能阶段性中断；东北证券的判断是"涨价至少延续至 2027 年"，这是<b>卖方预测而非既成事实</b>。</li>
<li><b>结构脆弱</b>：领涨品种集中在小市值超跌股与高位覆铜板，一旦市场风险偏好下降，回撤幅度会显著大于指数。</li>
<li><b>筹码松动信号已出现</b>：胜宏科技、鼎泰高科、大族数控、东山精密、中富电路、芯碁微装等 8 月中旬即见顶，当前距高点 -13% ~ -21%。</li>
<li><b>供给端反噬风险</b>：2026 年行业资本开支同比增速超 180%，头部企业史上最大规模扩产；高端 PCB 产线建设周期 1-2 年，若 2027-2028 年集中投产，供需格局可能逆转。</li>
<li><b>外围共振风险</b>：7 月的下跌已证明本板块对全球科技股情绪、美债利率、韩股/费半走势高度敏感。</li>
</ol>
</div>
<table>
<tr><th>观察指标</th><th>当前状态</th><th>转向信号</th></tr>
<tr><td>板块日均成交额</td><td>9 月 78.8 亿（区间最低）</td><td>重回 120 亿以上 = 增量资金入场；持续低于 70 亿 = 情绪退潮</td></tr>
<tr><td>CCL/电子布涨价函</td><td>建滔年内 7 轮，花旗预期 10 月初第 8 轮</td><td>涨价停发或幅度收窄 = 逻辑证伪起点</td></tr>
<tr><td>涨幅结构</td><td>超跌小票领涨、一线龙头滞后</td><td>若一线龙头开始补涨接力 = 行情延续；若小票继续脱离基本面加速 = 尾声特征</td></tr>
<tr><td>8 月中旬见顶股</td><td>胜宏、鼎泰、大族、东山距高点 -13% ~ -21%</td><td>若这批股票企稳回升 = 主力资金回流核心资产</td></tr>
<tr><td>Q3 业绩与涨价落地</td><td>尚未披露</td><td>提价能否真正体现在 Q3 毛利率 = 验证涨价传导是否成立</td></tr>
</table>

<h2>十、数据口径与来源说明</h2>
<table>
<tr><th>项目</th><th>说明</th></tr>
<tr><td>行情数据</td><td>腾讯财经 web.ifzq.gtimg.cn 日 K 前复权（fqkline/day/qfq），抓取时间 2026-09-15 收盘后；区间 2026-04-01 ~ 2026-09-15。东财 push2his 接口在本机被限流故未采用。</td></tr>
<tr><td>板块指数</td><td>34 只样本日收益率算术平均后累乘，基期 2026-07-31 = 100。<b>等权口径</b>，与市值加权的商业板块指数（如通达信 PCB 概念、WIND PCB 指数）数值不可直接比较，但趋势方向一致。</td></tr>
<tr><td>样本构成</td><td>PCB 制造 26 只：沪电股份、胜宏科技、深南电路、东山精密、景旺电子、鹏鼎控股、兴森科技、世运电路、广合科技、博敏电子、崇达技术、中富电路、四会富仕、奥士康、依顿电子、超声电子、方正科技、天津普林、弘信电子、生益电子、明阳电路、科翔股份、金百泽、强达电路、协和电子、迅捷兴；覆铜板 4 只：生益科技、南亚新材、华正新材、金安国纪；设备耗材 4 只：大族数控、芯碁微装、鼎泰高科、天承科技。样本为自行圈定，未使用官方成分股名单，可能存在遗漏（如则成电子、澳弘电子、满坤科技、中京电子等 9 月活跃个股未纳入）。</td></tr>
<tr><td>成交额</td><td>估算值 = 成交量 × (最高+最低+收盘)/3，非交易所披露口径，仅用于内部趋势比较。</td></tr>
<tr><td>消息面来源分级</td><td><b>高可信</b>：新华财经、中国经济新闻网、中国经营报等传统媒体，及可追溯的涨价函/中报数字。<b>中等</b>：券商研报转述（高盛、东北、浙商、国盛、招商）、行业协会数据。<b>需谨慎</b>：今日头条等自媒体，含具体资金流水数字但未标注原始出处；市场传闻（如 Kyber 延期、龙头丢单）部分已被否认或澄清。</td></tr>
<tr><td>未使用工具</td><td>本报告未获取到 Wind/通达信官方板块指数，未使用付费终端数据；板块构件与统计均基于公开行情自算，可复现（脚本 scripts/pcb_fetch.py、pcb_analyze.py、pcb_extra.py）。</td></tr>
</table>

<div class="sub" style="margin-top:30px">免责声明：以上内容基于公开数据和量化分析，仅供参考，不构成投资建议。文中涉及的板块涨跌、结构分化与原因推演包含对市场行为的归因假设，部分消息来源为媒体转述而非一手公告，请自行核实。市场有风险，投资需谨慎。过往表现不预示未来收益。</div>
</div>

<script>
var DATES=__DATES__;
var EQ=__EQ__;
var HS=__HS__;
var CY=__CY__;
var TX=__TX__;
var AMT=__AMT__;
var SC=__SC__;
var SEGNAMES=__SEGNAMES__;
var SEGMAT=__SEGMAT__;
var SEGS=__SEGS__;
var MAXAMT=__MAXAMT__;

var c=echarts.init(document.getElementById('c_main'));
c.setOption({
  tooltip:{trigger:'axis',valueFormatter:function(v){return (v===null||v===undefined)?'-':(+v).toFixed(2);}},
  legend:{data:['PCB等权(34只)','沪深300','创业板指','中证全指通信'],top:6},
  grid:{left:56,right:24,top:44,bottom:52},
  xAxis:{type:'category',data:DATES,axisLabel:{interval:3}},
  yAxis:{type:'value',name:'指数(7/31=100)',scale:true},
  dataZoom:[{type:'inside'},{type:'slider',height:16,bottom:8}],
  series:[
    {name:'PCB等权(34只)',type:'line',data:EQ,showSymbol:false,smooth:false,
     lineStyle:{width:2.6,color:'#d0342c'},itemStyle:{color:'#d0342c'},
     areaStyle:{color:'rgba(208,52,44,0.08)'},
     markPoint:{data:[
       {name:'反弹起点',coord:['08-03',EQ[1]],value:'8/3',itemStyle:{color:'#d0342c'},symbolSize:40,label:{fontSize:10}},
       {name:'急跌',coord:['08-19',EQ[DATES.indexOf('08-19')]],value:'8/19',itemStyle:{color:'#1e8e4e'},symbolSize:40,label:{fontSize:10}}
     ]}},
    {name:'沪深300',type:'line',data:HS,showSymbol:false,lineStyle:{width:1.6,color:'#8a919c'}},
    {name:'创业板指',type:'line',data:CY,showSymbol:false,lineStyle:{width:1.6,color:'#2c6bd0'}},
    {name:'中证全指通信',type:'line',data:TX,showSymbol:false,lineStyle:{width:1.6,color:'#c99a2e'}}
  ]
});

var c2=echarts.init(document.getElementById('c_amt'));
c2.setOption({
  tooltip:{trigger:'axis'},
  legend:{data:['板块日成交额(亿,左)','PCB等权指数(右)'],top:6},
  grid:{left:60,right:60,top:44,bottom:52},
  xAxis:{type:'category',data:DATES,axisLabel:{interval:3}},
  yAxis:[{type:'value',name:'成交额(亿)'},{type:'value',name:'指数',scale:true}],
  dataZoom:[{type:'inside'},{type:'slider',height:16,bottom:8}],
  series:[
    {name:'板块日成交额(亿,左)',type:'bar',data:AMT,itemStyle:{color:'#c9cdd4'}},
    {name:'PCB等权指数(右)',type:'line',yAxisIndex:1,data:EQ,showSymbol:false,lineStyle:{width:2.2,color:'#d0342c'},itemStyle:{color:'#d0342c'}}
  ]
});

var c3=echarts.init(document.getElementById('c_scatter'));
var GC={'PCB制造':'#2c6bd0','覆铜板':'#1e8e4e','PCB设备':'#c99a2e'};
var byG={};
SC.forEach(function(p){ (byG[p[3]]=byG[p[3]]||[]).push([p[0],p[1],p[2]]); });
var sers=[], i=0;
Object.keys(byG).forEach(function(g){
  sers.push({name:g,type:'scatter',data:byG[g].map(function(p){return [p[0],p[1]];}),
    symbolSize:11,itemStyle:{color:GC[g],opacity:0.85},
    label:{show:true,formatter:function(pp){return byG[g][pp.dataIndex][2];},position:'right',fontSize:9.5,color:'#6b7280'},
    markLine:i===0?{silent:true,symbol:'none',lineStyle:{type:'dashed',color:'#c9a0a0'},
      data:[[{coord:[0,0],symbol:'none'},{coord:[0,120]}]]}:undefined});
  i++;
});
sers.push({name:'回归线',type:'line',data:[[-60,5.2-1.166*-60],[0,5.2]],showSymbol:false,
  lineStyle:{width:1.6,type:'dashed',color:'#d0342c'},tooltip:{show:false}});
c3.setOption({
  tooltip:{trigger:'item',formatter:function(p){if(p.seriesName==='回归线')return '';
    var n=SC[0];return p.seriesName+'<br>x(7月) '+p.data[0]+'%<br>y(8月以来) '+p.data[1]+'%';}},
  legend:{data:['PCB制造','覆铜板','PCB设备','回归线'],top:6},
  grid:{left:60,right:60,top:44,bottom:48},
  xAxis:{type:'value',name:'7月涨跌幅(%)',axisLabel:{formatter:'{value}%'}},
  yAxis:{type:'value',name:'8月以来涨跌幅(%)',axisLabel:{formatter:'{value}%'}},
  series:sers
});

window.addEventListener('resize',function(){c.resize();c2.resize();c3.resize();});
</script>
</body>
</html>
"""


def f2v(v):
    return f"{v:+.1f}%"


def cls2(v):
    return "up" if v > 0 else "down"


# 反弹对照表(7月最惨8只 vs 7月最抗跌8只)
rows_sorted_jul = sorted([r for r in STOCKS if r["ret_jul"] is not None], key=lambda x: x["ret_jul"])
worst8 = rows_sorted_jul[:8]
best8 = rows_sorted_jul[-8:][::-1]
rb = ""
for a, b in zip(worst8, best8):
    rb += (f'<tr><td>{a["name"]}</td><td class="down">{f2v(a["ret_jul"])}</td>'
           f'<td class="up">{f2v(a["ret"])}</td>'
           f'<td>{b["name"]}</td><td class="down">{f2v(b["ret_jul"])}</td>'
           f'<td class="up">{f2v(b["ret"])}</td></tr>')

html = (TPL
        .replace("__REBOUND_ROWS__", rb)
        .replace("__DAILY_ROWS__", daily_rows)
        .replace("__TOP10_ROWS__", stock_rows2(top10))
        .replace("__BOT10_ROWS__", stock_rows2(bot10))
        .replace("__SEG_HEAD__", seg_head)
        .replace("__SEG_ROWS__", seg_rows)
        .replace("__EQ_LAST__", f"{EQ_LAST:.2f}")
        .replace("__EQ_RET__", f"{EQ_RET:.2f}")
        .replace("__AUG_M__", f"{AUG_M:.2f}")
        .replace("__SEP_M__", f"{SEP_M:.2f}")
        .replace("__EXCESS__", f"{EXCESS:.0f}")
        .replace("__MED_JUL__", f"{MED_JUL:.1f}")
        .replace("__SEG_RALLY__", f"{SEG_RALLY:.2f}")
        .replace("__SEG1__", f"{SEG1:.2f}")
        .replace("__SEG2__", f"{SEG2:.2f}")
        .replace("__SEG3__", f"{SEG3:.2f}")
        .replace("__MDD_FROM__", MDD_FROM)
        .replace("__MDD_TO__", MDD_TO)
        .replace("__MDD__", f"{MDD:.2f}")
        .replace("__N_BIG__", str(N_BIG))
        .replace("__N_UP__", str(N_UP))
        .replace("__N_DN__", str(N_DN))
        .replace("__N_SAME__", str(N_UP + N_DN))
        .replace("__DATES__", j(DATES))
        .replace("__EQ__", j(EQ))
        .replace("__HS__", j(B["沪深300"]))
        .replace("__CY__", j(B["创业板指"]))
        .replace("__TX__", j(B["中证全指通信"]))
        .replace("__AMT__", j(AMT))
        .replace("__SC__", j(sc))
        .replace("__SEGNAMES__", j(seg_names))
        .replace("__SEGMAT__", j(seg_mat))
        .replace("__SEGS__", j(segs))
        .replace("__MAXAMT__", str(max_amt)))

os.makedirs(REP, exist_ok=True)
fn = "PCB板块8月以来走势复盘-20260915.html"
p = os.path.join(REP, fn)
with open(p, "w", encoding="utf-8") as f:
    f.write(html)
print(f"[saved] {p}  ({len(html)} bytes)")
