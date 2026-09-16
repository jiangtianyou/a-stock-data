# -*- coding: utf-8 -*-
"""
生成《8月以来大科技板块反弹复盘》研报
输出: reports/tech-rebound-2026-08.html
"""
import sys, os, json

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "out")
REP = os.path.join(BASE, "reports")
os.makedirs(REP, exist_ok=True)


def dec(s):
    try:
        return json.loads('"' + s + '"')
    except Exception:
        return s


def fmt_d(d):
    return f"{d[4:6]}-{d[6:8]}"


# ---------- 读数据 ----------
em = json.load(open(os.path.join(OUT, "_tmp_tech_perf.json"), encoding="utf-8"))["items"]
em.sort(key=lambda x: -x["ret"])

ths_all = json.load(open(os.path.join(OUT, "ths_concept_all.json"), encoding="utf-8"))["items"]
for x in ths_all:
    x["name"] = dec(x["name"])

ths_ind = json.load(open(os.path.join(OUT, "ths_industry_perf.json"), encoding="utf-8"))["items"]
leaders = json.load(open(os.path.join(OUT, "tech_leaders.json"), encoding="utf-8"))
tx = json.load(open(os.path.join(OUT, "tech_idx_tx.json"), encoding="utf-8"))["items"]

KW = ["半导体", "芯片", "光", "通信", "电子", "算力", "AI", "人工智能", "存储", "PCB",
      "元件", "面板", "软件", "计算机", "传媒", "游戏", "机器人", "服务器", "数据中心",
      "消费电子", "光学", "MLCC", "封装", "光刻", "HBM", "CPO", "液冷", "铜缆", "GPU",
      "CPU", "传感器", "智能驾驶", "卫星", "军工", "5G", "6G", "虚拟", "元宇宙", "信创",
      "大数据", "云", "数字经济", "鸿蒙", "量子", "脑机", "无人机", "低空", "激光",
      "显示", "折叠", "穿戴", "覆铜", "电子布", "光模块", "先进封装", "第三代半导体"]
EX = ["ST", "次新", "融资", "转债", "烟草", "电子烟"]
ths_tech = [x for x in ths_all if any(k in x["name"] for k in KW)
            and not any(e in x["name"] for e in EX)]
ths_tech.sort(key=lambda x: -x["ret"])

# ---------- 组装前端数据 ----------
em_top = [{"n": x["name"], "r": round(x["ret"] * 100, 2),
           "rd": round(x["rebound_from_low"] * 100, 2),
           "cat": ("光纤光缆" if "线缆" in x["name"] else
                   "PCB/元件" if x["name"] in ("元件", "被动元件", "电子") else
                   "光模块/通信设备" if "通信" in x["name"] else
                   "半导体链" if ("半导体" in x["name"] or "芯片" in x["name"] or "集成电路" in x["name"] or "电子化学品" in x["name"]) else
                   "消费电子/光学" if ("消费" in x["name"] or "光学" in x["name"] or "面板" in x["name"]) else "其他")}
          for x in em[:18]]

ths_top = [{"n": x["name"], "r": round(x["ret"] * 100, 2),
            "rd": round(x["rd"] * 100, 2)} for x in ths_tech[:18]]

ld_top = [{"n": x["name"], "r": round(x["ret"] * 100, 2), "g": x["group"],
           "low": fmt_d(x["low_date"])} for x in leaders]

# 走势对比: 同花顺概念 + 腾讯指数
TREND_SRC = ["共封装光学(CPO)", "光纤概念", "PCB概念", "铜缆高速连接", "F5G概念",
             "AI PC", "AIGC概念", "AI应用"]
trends = []
for nm in TREND_SRC:
    for x in ths_all:
        if x["name"] == nm:
            trends.append({"name": nm, "type": "概念板块",
                           "data": [[fmt_d(d), v] for d, v in x["seq"]]})
            break
for nm in ["科创50", "创业板指", "沪深300"]:
    for x in tx:
        if x["name"] == nm:
            for x2 in leaders:
                pass
            break
# 宽基用同花顺不可得 -> 用腾讯日线归一化(已存 ret 但无序列)，此处改用东财板块替代

ind_sel = [x for x in ths_ind if x["name"] in
           ("半导体", "通信设备", "电子化学品", "消费电子", "计算机应用", "文化传媒")]

json.dump({"em": em_top, "ths": ths_top, "leaders": ld_top, "trends": trends,
           "ind": ind_sel}, open(os.path.join(OUT, "tech_rebound_data.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

D = {"em": em_top, "ths": ths_top, "leaders": ld_top, "trends": trends,
     "ind": [{"n": x["name"], "r": round(x["ret"] * 100, 2)} for x in ind_sel]}

print("东财 TOP:", [(x["n"], x["r"]) for x in em_top[:6]])
print("同花顺概念 TOP:", [(x["n"], x["r"]) for x in ths_top[:6]])
print("龙头 TOP:", [(x["n"], x["r"]) for x in ld_top[:6]])
print("走势序列:", [x["name"] for x in trends])

# ---------- 生成 HTML ----------
DS = json.dumps(D, ensure_ascii=False)

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>8月以来大科技板块反弹复盘 | 2026.07.31 → 2026.09.15</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5"></script>
<style>
:root{--bg:#f7f8fa;--card:#fff;--ink:#1a1d24;--sub:#586172;--line:#e6e9ef;--up:#d5313a;--down:#0f9960;--acc:#2b6cb0}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
 font-family:-apple-system,"PingFang SC","Microsoft YaHei",Segoe UI,sans-serif;line-height:1.7}
.wrap{max-width:1180px;margin:0 auto;padding:28px 20px 64px}
header{border-bottom:2px solid var(--ink);padding-bottom:16px;margin-bottom:26px}
h1{font-size:27px;margin:0 0 8px;letter-spacing:-.4px}
.meta{color:var(--sub);font-size:13.5px}
h2{font-size:19px;margin:38px 0 14px;padding-left:11px;border-left:4px solid var(--acc)}
h3{font-size:16px;margin:24px 0 10px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:20px 22px;margin:14px 0;
 box-shadow:0 1px 3px rgba(16,24,40,.04)}
.lead{background:#fff;border:1px solid var(--line);border-left:5px solid var(--up);border-radius:10px;
 padding:18px 22px;margin:16px 0}
.lead b{color:var(--up)}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:18px 0}
.kpi{background:#fff;border:1px solid var(--line);border-radius:10px;padding:16px 18px}
.kpi .rk{font-size:12px;color:var(--sub);letter-spacing:1px}
.kpi .nm{font-size:19px;font-weight:700;margin:5px 0 3px}
.kpi .vl{font-size:25px;font-weight:700;color:var(--up);font-variant-numeric:tabular-nums}
.kpi .ds{font-size:12.5px;color:var(--sub);margin-top:5px}
table{width:100%;border-collapse:collapse;font-size:13.5px;margin:6px 0}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left}
th{background:#f1f3f7;font-weight:600;color:var(--sub);font-size:12.5px}
td.num{text-align:right;font-variant-numeric:tabular-nums;font-weight:600}
.up{color:var(--up)}.down{color:var(--down)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.chart{width:100%;height:430px}
.tag{display:inline-block;font-size:11.5px;padding:1px 8px;border-radius:20px;background:#eef2f7;color:#33415c;margin-right:6px}
ul{margin:8px 0;padding-left:22px}li{margin:5px 0}
.note{font-size:12.5px;color:var(--sub);background:#f1f3f7;border-radius:8px;padding:10px 14px;margin-top:10px}
.risk{border-left:5px solid #b7791f}
.tl{border-left:2px solid var(--line);margin:10px 0 0 8px;padding-left:18px}
.tl .it{margin-bottom:13px;position:relative}
.tl .it:before{content:'';position:absolute;left:-25px;top:8px;width:9px;height:9px;border-radius:50%;background:var(--acc)}
.tl .dt{font-weight:700;font-size:13.5px}
.tl .tx{font-size:13px;color:var(--sub)}
@media(max-width:860px){.kpis,.grid2{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>8月以来大科技板块反弹复盘</h1>
  <div class="meta">统计区间：<b>2026-07-31 收盘 → 2026-09-15 收盘</b>（8月以来）　·　口径：板块指数区间涨幅（前复权）　·　数据源：同花顺概念/行业板块指数、东方财富细分行业、腾讯财经指数</div>
</header>

<div class="lead">
  <b>一句话结论：</b>8月以来大科技的反弹高度集中在<b>AI算力"互联硬件"</b>——在两种独立的板块口径下，<b>光模块/CPO、光纤光缆、PCB/覆铜板</b>都同时占据涨幅前三；紧随其后的"铜缆高速连接"（+21.8%）与"F5G概念"（+21.4%）同属这条链。
  而同属"科技"的<b>软件与AI应用（AIGC概念 +2.6%、AI应用 +1.1%）、半导体龙头（中芯国际 −7.4%、北方华创 −7.1%）同期反而下跌</b>。
  这不是一轮普涨式科技反弹，而是一次由"<b>AI资本开支超预期 → 上游缺货涨价 → 中报业绩兑现</b>"共同驱动的高度结构性行情。
</div>

<div class="kpis">
  <div class="kpi"><div class="rk">TOP 1</div><div class="nm">光模块 / CPO</div><div class="vl">+24.3%</div>
    <div class="ds">同花顺"共封装光学(CPO)"；东财口径"通信网络设备及器件" +25.4%。龙头天孚通信 +50.5%、源杰科技 +54.3%</div></div>
  <div class="kpi"><div class="rk">TOP 2</div><div class="nm">光纤光缆</div><div class="vl">+22.8%</div>
    <div class="ds">同花顺"光纤概念"；东财口径"通信线缆及配套" +39.1%。龙头长盈通 +124.9%、太辰光 +70.5%、长飞光纤 +70.4%</div></div>
  <div class="kpi"><div class="rk">TOP 3</div><div class="nm">PCB / 覆铜板</div><div class="vl">+22.7%</div>
    <div class="ds">同花顺"PCB概念"；东财口径"元件" +41.8%。龙头金安国纪 +65.2%、南亚新材 +57.9%、生益科技 +42.2%</div></div>
</div>

<h2>一、板块涨幅排行</h2>
<div class="card">
  <div id="c_ths" class="chart"></div>
  <div class="note">口径：同花顺概念板块指数（362个概念板块中筛选科技类，按区间涨幅排序）。这是最细的公开板块口径，不含个股选择偏差。</div>
</div>
<div class="card">
  <div id="c_em" class="chart" style="height:470px"></div>
  <div class="note">口径：东方财富细分行业板块（受数据源限流影响，此处为已获取的25个科技细分行业样本）。用于与同花顺口径交叉验证。</div>
</div>

<h2>二、TOP 方向的走势对比</h2>
<div class="card">
  <div id="c_trend" class="chart" style="height:470px"></div>
  <div class="note">以 2026-07-31 收盘 = 100 归一化。两条清晰的裂口：<b>① 8 月中旬起硬件（CPO/光纤/PCB/铜缆）与软件-AI应用（AIGC/AI应用）持续分化</b>；<b>② 9/7 硬件方向集体二次加速</b>，而 AI 应用端几乎没有响应。</div>
</div>

<h2>三、龙头股表现印证"上游 &gt; 下游"</h2>
<div class="card">
  <div id="c_leader" class="chart" style="height:560px"></div>
  <div class="note">关键结构：<b>越靠近涨价与缺货环节，涨幅越大</b>。光纤预制棒/光器件（长盈通+124.9%、太辰光+70.5%）＞ 覆铜板/PCB（金安国纪+65.2%、南亚新材+57.9%）＞ 光模块整机（中际旭创 −4.2%、新易盛 +0.3%）＞ 半导体龙头（中芯国际 −7.4%、北方华创 −7.1%）。</div>
</div>

<h2>四、原因拆解：四条主线共振</h2>
<div class="grid2">
  <div class="card">
    <h3>① 产业端：AI资本开支超预期 → 上游缺货涨价</h3>
    <ul>
      <li><b>光通信</b>：8/14 英伟达宣布 Spectrum-X 硅光交换机（全球首款 200G/lane CPO 以太网交换机）<b>全面量产</b>；高盛将 2026-2028 年全球光模块出货量预测<b>上调 20%+</b>，1.6T 及以上超高速模块上调幅度更大。</li>
      <li><b>光纤光缆</b>：中国移动普缆招标重启，最高限价<b>上调 8.5%</b> 至约 71 亿元；7 月光纤光缆出口单价刷新年内新高；保偏光纤被视作 CPO 架构核心增量部件。</li>
      <li><b>PCB/覆铜板</b>：CCL 覆铜板年内<b>第七轮涨价</b>（8/28 建滔再涨，FR-4 累计复利涨幅突破 100%），电子布/铜箔主材紧缺，供需缺口预计延续至 2027 年。</li>
      <li><b>被动元件</b>：8/28 三星电机调涨 MLCC（消费级 X5R +25%~30%，AI 服务器用 X6S +10%~20%）；AI 服务器单柜用量翻倍。</li>
      <li><b>铜互联</b>：GB200 NVL72 等机柜级方案大量采用铜缆背板/DAC，"铜缆高速连接"板块 8 月以来 +21.8%，与光互联共同构成机柜内外的短距/长距互联方案。</li>
    </ul>
  </div>
  <div class="card">
    <h3>② 业绩端：中报集中兑现"算真账"</h3>
    <ul>
      <li>中际旭创 H1 营收 <b>+182.5%</b>、归母净利 <b>+241.7%</b></li>
      <li>新易盛 H1 净利 <b>+78%~103%</b>；天孚通信净利 +33.9%</li>
      <li>长飞光纤归母净利 <b>+888.9%</b>（29.25 亿元）</li>
      <li>亨通光电光通信业务营收 <b>+130%</b>，毛利率超 60%</li>
      <li>创业板 2026H1 营收 2.55 万亿、同比 <b>+22.3%</b></li>
    </ul>
    <div class="note">业绩兑现是本轮与"纯题材炒作"的关键区别——涨幅最大的环节同时是<b>订单能见度最长</b>（中际旭创/新易盛均已给出 2027 年订单指引）的环节。</div>
  </div>
  <div class="card">
    <h3>③ 政策与事件：密集催化</h3>
    <div class="tl">
      <div class="it"><div class="dt">8/14</div><div class="tx">英伟达 CPO 交换机全面量产</div></div>
      <div class="it"><div class="dt">8/27</div><div class="tx">英伟达财报超预期；1-7 月集成电路行业利润同比 <b>+18.5 倍</b></div></div>
      <div class="it"><div class="dt">9/4</div><div class="tx">OpenAI 发布 GPT-6 Astra（超十万张 GPU 训练）；工信部印发《人工智能中小企业创业支持计划》</div></div>
      <div class="it"><div class="dt">9/7</div><div class="tx">华为发布"逻辑折叠架构"自研芯片；工信部《信息通信行业"十五五"规划》提出 2030 年信息基础设施累计投资 3.8 万亿元、智能算力 9800 EFLOPS</div></div>
      <div class="it"><div class="dt">9/11</div><div class="tx">存储、半导体产业链多家公司披露重大资产重组，产业资本加速整合</div></div>
    </div>
  </div>
  <div class="card">
    <h3>④ 资金端：增量资金明确流向算力</h3>
    <ul>
      <li>9/4 首批创业板算力基础设施 ETF 发售，<b>部分产品一日售罄</b>。</li>
      <li>9/8-9/12 单周，光通信/CPO 方向主力资金净流入<b>超 176 亿元</b>，居全市场第一；中际旭创单周净流入 102 亿元。</li>
      <li>7 月创业板指回撤 23% 后，浮筹清洗较充分，两融与量化交易筹码回落至行情加速前水平，边际卖压减轻。</li>
      <li>资金从银行、煤炭等高股息防御方向撤出，回流超跌成长，形成<b>高低切换</b>。</li>
    </ul>
  </div>
</div>

<h2>五、三段式节奏：反弹不是一条直线</h2>
<div class="card">
  <table>
    <tr><th>阶段</th><th>区间</th><th>特征</th></tr>
    <tr><td><b>超跌修复</b></td><td>8/3 → 8/7</td><td>7月创业板指回撤 23% 后的技术性反弹。8/4 创业板指 +5.64%、科创综指 +4.77%；8/5 半导体 +5.34%、存储器 +5.61%，成交放大至 2.68 万亿。</td></tr>
    <tr><td><b>冲高见顶</b></td><td>8/11 → 8/21</td><td>多数板块在 <b>8/18</b> 前后摸到区间高点（半导体、光学光电子、电子化学品、被动元件低点均在 8/3、高点均在 8/18）。</td></tr>
    <tr><td><b>回调震荡</b></td><td>8/24 → 9/4</td><td>外围扰动 + 获利了结，板块普遍回吐，AIGC/AI应用等低点出现在 8/24。</td></tr>
    <tr><td><b>二次爆发</b></td><td>9/7 → 9/9</td><td>GPT-6 + 华为芯片 + 工信部政策三线共振，通信/电子涨停潮，CPO/PCB/存储/半导体设备集体爆发。通信设备高点出现在 <b>9/9</b>。</td></tr>
    <tr><td><b>高位回落</b></td><td>9/10 → 9/15</td><td>科创50 自 9/9 高点回落，半导体、半导体设备低点出现在 <b>9/14</b>；硬件方向仍在高位震荡。</td></tr>
  </table>
  <div class="note">值得注意的是：区间涨幅看起来亮眼，但<b>低点基本都在 8/3、高点在 8/18 或 9/9</b>——并非单边上行，追高与低吸的体验差异极大。</div>
</div>

<h2>六、与"宽基科技指数"的背离</h2>
<div class="card">
  <table>
    <tr><th>指数（宽口径）</th><th>8月以来涨幅</th><th>说明</th></tr>
    <tr><td>全指通信</td><td class="num up">+6.17%</td><td>宽口径中最强，印证硬件主线</td></tr>
    <tr><td>800通信</td><td class="num up">+5.00%</td><td></td></tr>
    <tr><td>中证军工</td><td class="num up">+4.53%</td><td>同期另一条独立主线</td></tr>
    <tr><td>CSSW电子</td><td class="num up">+3.28%</td><td></td></tr>
    <tr><td>全指信息</td><td class="num up">+0.65%</td><td>被软件/IT服务拖累</td></tr>
    <tr><td>中证TMT</td><td class="num down">-0.25%</td><td></td></tr>
    <tr><td>创业板指</td><td class="num down">-2.87%</td><td></td></tr>
    <tr><td>科创50</td><td class="num down">-5.13%</td><td>半导体权重高且龙头走弱</td></tr>
  </table>
  <div class="note"><b>看指数会严重低估这轮行情。</b>科创50 区间 −5.13%、创业板指 −2.87%，但光纤光缆龙头 +70%、覆铜板龙头 +65%。原因：这轮涨的是<b>上游中小市值弹性品种</b>，而宽基指数由半导体大市值权重股主导，后者同期是下跌的。</div>
</div>

<h2>七、风险提示</h2>
<div class="card risk">
  <ul>
    <li><b>拥挤度与高位波动</b>：光通信/CPO 单周主力净流入超 176 亿元，成交高度集中（中际旭创单日成交曾达 675 亿元），一旦资金退潮回撤幅度会显著放大。9/10 起部分方向已现回落。</li>
    <li><b>涨价逻辑的可持续性依赖 AI 资本开支</b>：覆铜板、MLCC、光纤的涨价本质上由 AI 服务器需求驱动，若海外云厂商资本开支不及预期，涨价链会最先承压。</li>
    <li><b>内部结构已明显分化</b>：光模块整机龙头（中际旭创 −4.2%）跑输上游器件（天孚通信 +50.5%），说明资金在产业链内部做"上移"，这种再平衡往往伴随剧烈轮动。</li>
    <li><b>外部扰动</b>：美股映射（费城半导体、存储股）是 A 股硬科技的重要外部情绪指引，美国加息预期与非农数据波动会直接传导。</li>
    <li><b>口径提醒</b>：本报告为<b>板块指数层面</b>的复盘，不同数据源板块分类与成分差异会导致涨幅数值不同（如"元件"含 PCB 与被动元件），结论的重心应放在<b>方向的排序</b>而非精确到小数点的数值。</li>
  </ul>
</div>

<div class="note" style="margin-top:26px">
数据说明：区间为 2026-07-31（7月最后一个交易日）收盘至 2026-09-15 收盘，均采用前复权口径。板块指数分别来自同花顺概念板块（362个，bk_ 指数）、同花顺行业板块、东方财富细分行业板块（BK 指数）、腾讯财经指数；个股为腾讯财经日线。部分数据源在抓取过程中出现限流，已在相应位置标注样本范围。本报告仅作数据复盘与归因，不构成任何投资建议。
</div>

</div>

<script>
const D = __DATA__;
const up = '#d5313a', down = '#0f9960', acc = '#2b6cb0';
const fmtPct = v => (v >= 0 ? '+' : '') + v.toFixed(2) + '%';
const cRed = '#d5313a';

function hbar(id, items, opt) {
  const el = document.getElementById(id);
  const ch = echarts.init(el);
  const data = items.slice().reverse();
  ch.setOption({
    grid: { left: 130, right: 90, top: 16, bottom: 34 },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' },
      formatter: p => p[0].name + '：' + fmtPct(p[0].value) + (p[1] ? '　自低点反弹 ' + fmtPct(p[1].value) : '') },
    xAxis: { type: 'value', axisLabel: { formatter: v => v + '%', color: '#586172' },
      splitLine: { lineStyle: { color: '#eef1f5' } } },
    yAxis: { type: 'category', data: data.map(x => x.n),
      axisLabel: { color: '#1a1d24', fontSize: 12 }, axisLine: { lineStyle: { color: '#dde2ea' } } },
    series: [{
      type: 'bar', data: data.map(x => x.r), barWidth: opt && opt.barWidth || '58%',
      itemStyle: { color: p => p.value >= 0 ? up : down, borderRadius: [0, 3, 3, 0] },
      label: { show: true, position: 'right', formatter: p => fmtPct(p.value),
        color: '#1a1d24', fontSize: 11.5, fontWeight: 600 }
    }]
  });
  window.addEventListener('resize', () => ch.resize());
  return ch;
}

hbar('c_ths', D.ths.map(x => ({ n: x.n, r: x.r })));
hbar('c_em', D.em.map(x => ({ n: x.n, r: x.r })), { barWidth: '62%' });

// 龙头股
(function () {
  const el = document.getElementById('c_leader');
  const ch = echarts.init(el);
  const data = D.leaders.slice().reverse();
  ch.setOption({
    grid: { left: 152, right: 100, top: 20, bottom: 34 },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' },
      formatter: p => p[0].name + '（' + data[p[0].dataIndex].g + '）<br/>8月以来：' + fmtPct(p[0].value) + '<br/>区间低点：' + data[p[0].dataIndex].low },
    xAxis: { type: 'value', axisLabel: { formatter: v => v + '%', color: '#586172' },
      splitLine: { lineStyle: { color: '#eef1f5' } } },
    yAxis: { type: 'category', data: data.map(x => x.n + ' · ' + x.g),
      axisLabel: { color: '#1a1d24', fontSize: 11.5 }, axisLine: { lineStyle: { color: '#dde2ea' } } },
    series: [{
      type: 'bar', data: data.map(x => x.r), barWidth: '62%',
      itemStyle: { color: p => p.value >= 0 ? up : down, borderRadius: [0, 3, 3, 0] },
      label: { show: true, position: 'right', formatter: p => fmtPct(p.value),
        color: '#1a1d24', fontSize: 11, fontWeight: 600 }
    }]
  });
  window.addEventListener('resize', () => ch.resize());
})();

// 走势对比
(function () {
  const el = document.getElementById('c_trend');
  const ch = echarts.init(el);
  const palette = ['#d5313a', '#e8743b', '#b7791f', '#2b6cb0', '#4c9be8', '#7b8794', '#a0aab8', '#0f9960'];
  const dates = D.trends.length ? D.trends[0].data.map(x => x[0]) : [];
  const series = D.trends.map((t, i) => ({
    name: t.name, type: 'line', showSymbol: false, smooth: true,
    lineStyle: { width: 2.2, color: palette[i % palette.length] },
    itemStyle: { color: palette[i % palette.length] },
    data: t.data.map(x => x[1])
  }));
  ch.setOption({
    grid: { left: 56, right: 130, top: 40, bottom: 46 },
    legend: { type: 'scroll', top: 4, textStyle: { color: '#33415c', fontSize: 12 } },
    tooltip: { trigger: 'axis', valueFormatter: v => (v >= 100 ? '+' : '') + (v - 100).toFixed(2) + '%' },
    xAxis: { type: 'category', data: dates, boundaryGap: false,
      axisLabel: { color: '#586172' }, axisLine: { lineStyle: { color: '#dde2ea' } } },
    yAxis: { type: 'value', min: 85, axisLabel: { color: '#586172', formatter: '{value}' },
      splitLine: { lineStyle: { color: '#eef1f5' } }, name: '7/31 = 100',
      nameTextStyle: { color: '#7b8794', fontSize: 11 } },
    series: series
  });
  window.addEventListener('resize', () => ch.resize());
})();
</script>
</body>
</html>
"""

html = HTML.replace("__DATA__", DS)
p = os.path.join(REP, "tech-rebound-2026-08.html")
open(p, "w", encoding="utf-8").write(html)
print(f"\n报告已生成: {p}  ({len(html)} 字节)")
