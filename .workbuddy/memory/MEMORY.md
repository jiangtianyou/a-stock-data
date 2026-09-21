# a-stock-data 项目长期笔记

> 接口/口径细节已下沉到 skill（见文末），此处只留跨任务通用经验与结论。

## 数据源（可用通道）

| 用途 | 通道 | 要点 |
|---|---|---|
| 全收益指数（唯一） | 中证官网 `csindex.com.cn/csindex-home/perf/index-perf?indexCode={code}` | 一次取全历史；**全收益只返回 close 无 open**（跳空分解只能用价格指数）；连发会 403/空，间隔 2s+退避 60s 可恢复。全收益码=`H`+价格码后5位；例外 红利低波 H30269→H20269、红利低波100 930955→H20955；399xxx 官网无数据 |
| 指数/个股月线日线 | 腾讯 `web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={sym},month\|day,...` | 字段序 **开-收-高-低-量**；日线须分段（6年/段、count=1700，区间 1990/1997/2003/2009/2015/2021） |
| 轻量月线 | `data.gtimg.cn/flashdata/hushen/monthly/{sym}.js` | 日期 6 位 YYMMDD 需补世纪，行尾带 `\` 续行 |
| 板块/概念日线（最全） | 同花顺 `d.10jqka.com.cn/v6/line/bk_{code}/01/last.js` | 行业 881101~881175；概念有效区 **885450~886400**（<885450→404）；无限流 0.01~0.3s；约 140 交易日 |
| 代码/名称核验 | `qt.gtimg.cn/q=sh000001,...` | **GBK**，`~` 分隔，f2=名称 |
| 板块列表（仅名称） | 新浪 `newFLJK.php?param=class\|industry` | 概念 175/行业 84；拿不到历史 |
| 行情·财务·资金（板块分析首选） | westock CLI `C:/Users/Administrator/.local/bin/westock.exe` | `search <kw> --type sector` → `sector constituent <id>`；`kline <sym> --limit 300`；`finance <sym> --type income\|balance\|cashflow`；`fund flow a,b,c` |

**失效/限流**：东财 `push2his`+`push2`（clist）**IP 级全域名封锁**（RST，0.06s 即失败）；`push2delay` 的 clist 可用但 **f24/f25 涨跌幅不可信**，clist 每页 100 且 `fid=f3` 会漏弱势板块。通达信 MCP 有配额。

**已验证指数**：宽基 sh000001 上证 / sz399001 深成 / sh000300 / sh000905 / sh000852 / sz399006 创业板 / sh000688 科创50 / sh000016 上证50 / sh000922 中证红利 / sh000015 上证红利；全指一级行业 sh000986~000995；中证800行业 sh000928~000937；主题 sz399997 白酒 / sz399998 煤炭 / sz399986 银行 / sz399975 证券 / sz399967 军工 / sz399989 医疗 / sz399808 新能 / sz399976 新能车 / sz399971 传媒 / sh000827 环保 / sh000978 医药100 / sh000819 有色。

## 脚本与工程约定

- **两段式**：先抓取落盘 `out/*.json`，再分析/出报告。长时抓取用域名轮换+指数退避+**逐品种增量打印**（不要 `| tail -N`，会缓冲到结束）。
- 网络脚本统一绕过代理（`ProxyHandler({})` / `Session.trust_env=False`）。
- **抓取脚本必须「全部成功才覆盖落盘」**（写 `.tmp` 再 `os.replace`）；否则重跑会把好数据覆盖成空。
- **盘后复跑的幂等比对只比四个核心键**：`D0` / `D1` / `today_zt_quotes` / `yesterday_zt_today`。
  `generated_at`、`dates`、`indexes`（市值尾数抖动）、`index_hist`（**指数日线盘后会把「当日行」移出返回窗口**，
  09-21 实测 16:11 含当日、16:34 起不含）都会产生假差异，纳入比对会误判成数据变化而白跑全流程。
  当日成交额一律取实时快照 `indexes[sym].amount_wan`，**禁止用 `index_hist[code].rows[-1]` 当当日**。
- **排序 tie-break 必须完整**：`sorted(set(...))` 同分项受 str 哈希随机化影响 → 同一数据两次跑出不同榜单。补 `(计数, -今值, -昨值, 名称)`。
- **同一文件的多个 Edit 不要并行提交**（实测 4 个只生效 1 个）；批量改脚本用「一次性补丁 + `assert a in s`」。
- Git Bash 下 grep/sed 处理 UTF-8 中文常失效 → 用 Read 工具或 python。
- **依赖归属**：`pandas/numpy` 在 managed venv（`~/.workbuddy/binaries/python/envs/default/Scripts/python.exe`）；**`playwright` 只在系统 python 3.11**（`.../Python311/python.exe`），venv 跑 `_shot.py` 会 ModuleNotFoundError。
- **westock 字段坑**：`finance --type income` 的 `_Q` 后缀字段（`NPParentCompanyYOY_Q`/`TORGrowRate_Q` 等）全是**单季**同比；累计口径只有 `NPParentCompanyYOY`/`TORGrowRate`；**扣非累计同比必须自算**（力量钻石 2026H1 扣非累计 +1249%，`_Q` 给 +12839%，差 10 倍）。**亏损公司 `NPParentCompanyYOY` 为正 = 亏损收窄**，渲染成红色会被误读为增长。
- **同名不同型的字段最易埋 bug**：东财涨停/炸板池 `fbt` 是 **HHMMSS 整数**（`92500`），切分前须 `zfill(6)`，否则 10:00 前渲染成 `92:50`；而 `r0`（同花顺源）的 `fbt` 已是 `"09:30:09"` 字符串。**跨源拼接前先 `type()` 确认。**
- **东财涨停池含北交所**：`em_ZT.tc` 多出 `920xxx`（09-18 东财 78 vs 同花顺 77；09-21 东财 103 vs 同花顺 101，差额 920478/920427），报告须显式声明「按沪深口径」。
- **同花顺跌停池明细接口会 404**（`dataapi/limit_up/limit_down_pool`，09-21 实测 404，`ths_dt` 为 None）；跌停家数只能取汇总字段 `limit_down_count`，报告须声明明细不可用。
- **`zt_fetch.resolve_dates` 只取前 2 个参数** → `zt_review_{D0}.json` 只含 D0/D1。但 `zt_analyze.py` 的三日序列仍正确，因为 `days[0]` 用的是 `senti[D1]["zt_prev"]`（D1 记录自带的「前一交易日」汇总值），不需要 D2 自己的 senti，**不必为此补抓 D2**。
- 同花顺板块指数 `bk_885xxx` 日期为 **`YYYYMMDD`**（8 位无横线），混入计算前须归一化。
- 早期落盘 `out/ths_concept_all.json` 的 `name` 是**双重转义字面量**，中文 `in` 匹配全失败 → 用 `chr()` 码点或 `unicode_escape` 还原。
- **同名 key 的残留赋值会静默覆盖正确值**（`K["ZBJ_FLOW20"]` 被后面 `*0` 覆盖成 0）。改生成脚本后必须重新截图核对关键数字，不能只看占位符无残留。

## 报告规范

- 浅底深字、结论先行（首屏 lead + KPI 卡）、ECharts 5、**红涨绿跌**。
- **正文数字一律由数据推导 + `__占位符__` + `.replace()` 注入，禁止手写**；收尾 `re.findall(r"__[A-Z_0-9]+__", html)` 确认无残留。
- **不要用 f-string 生成含 CSS/JS 的 HTML**，用占位符替换。
- ECharts 横向条形图**类目 >25** 时容器高 ≈ 类目数×21px 且 `axisLabel.interval:0`。
- 双 Y 轴图图例用 `top:3,left:'center'`，**不要 `right:8`**（会与右轴名重叠）；`grid.top≥52`。
- 瀑布图不能 `data:[[起,止]]`，须「透明占位 stack + 数值 stack」。
- 交付前：`_check_js.py <html>` + `_shot.py <html> <scrollY...>`（用系统 3.11）。
- **ECharts 本地托管 + CDN 兜底**：`assets/echarts.min.js` + 页面 `<script src="../assets/echarts.min.js">` + `if(typeof echarts==='undefined'){document.write(CDN)}`。起因 jsdelivr 在 Playwright 侧间歇 `ERR_CONNECTION_RESET` → `canvas=0`+`echarts is not defined`，而 curl 同时刻能通 —— **「截图自检报 canvas=0」先怀疑 CDN**。
- **ECharts 类目轴首项在底部**：排名类热力图/条形图数组**必须先反转**再喂 `yAxis.data`。

## 结论沉淀

- **红利指数季节性**：6 月是 A 股最强负季节性（7 个红利指数全负，价格口径 -4.01%、胜率 30.9%、t≈-3.2）。其中约 **1.33% 是除息机械扣减**（6+7 月占全年分红 73.5%）——**评估红利真实回报必须用全收益指数**，价格指数每年 6-7 月少算约 2.7pp。剩余弱势主因风格轮动（6 月成长 +3.01% vs 红利 -2.80%）。正季节性（2/7/12 月）2015 年后基本消失。
- **培育钻石（2026「叙事重构」标本，2026-09-17）**：市场从「珠宝周期股」重定价为「AI 算力散热材料股」。TOP3=力量钻石(301071)/黄河旋风(600172)/四方达(300179)。**核心：涨的是预期，赚的是现状**——2026H1 利润改善来自工业金刚石涨价+培育钻石价格企稳，散热业务公司自述「尚未对收入产生影响」。结构「上半年主升 +161%~+301% → 7-8 月深调 -14%~-37% → 9 月二波」，**只看 YTD 会误判位置**。分层残酷：材料端普涨，消费/渠道端（潮宏基 -27%、豫园 -11%）YTD 跌。中兵红箭市值最大、YTD -16.6% 垫底、20 日主力净流出 3 亿，且自述「业绩回暖与散热概念关联不大」。

## 自建等权指数 / 板块复盘（模板见 PCB 8 月复盘）

- 脚本链：`pcb_fetch.py` → `pcb_analyze.py`/`pcb_extra.py` → `pcb_report.py`。
- **致命坑**：`cur *= (1+avg_ret(d))` 后再 `vals[base_d]=100` 会把**基期当日涨幅重复计入**。正确：遇基期日 `vals[base_d]=100.0; continue`。**任何自建指数先断言「首日收益为 0」**。
- 最大回撤须记录**回撤当时的峰值日**（`pk_at`），不能用全局 peak 日。
- 四件套：①区间涨幅+区间最高/最低（附距高点）②日成交额与指数的**背离**（缩量新高是重要信号）③全板块同向日 & 单日 |涨跌|≥5% 异动计数（区分 β vs Alpha）④「前期跌幅 × 本期涨幅」散点+回归斜率。
- 样本池分层并**显式声明等权口径与市值加权指数不可比**。

## 样本口径铁律（季节性 / 事件研究）

- **1991-1992 上证处于无涨跌停/T+0 极端期**（1 月均值 28%、std 173%），月度统计起点取 **1997-01 或 2000-01**。
- 小样本+极端值必看**中位数**。
- **双基准分解（剥离跳空）**：同时给 `close(T+N)/close(T-1)`（含跳空）与 `close(T+N)/close(T+1)`（剔除首日），差额=首日贡献。国庆节后 5 日首日贡献 ≈85%。
- **用「环境档」替代「日历标签」**：按**当年 1-8 月累计涨幅**切分（强势 >+10%/震荡 ±10%/弱势 <-10%），10 月胜率随档位单调下降（88.9%/30.8%/28.6%）。

## 可复用脚本链

- 季节性（81 品种月线）：`seasonality_fetch_tx2.py` → `seasonality_analyze.py` → `seasonality_report.py`
- 日历效应（9 指数日线）：`oct_fetch_daily.py` → `oct_analyze.py`/`oct_extra.py` → `oct_report.py`
- 渲染自检：`scripts/_shot.py`、`scripts/_check_js.py`
- **板块核心标的分析（泛化模板）**：`dia_fetch.py`（westock kline/quote + 同花顺板块指数 + 基准）→ `dia_fin.py` → `dia_analyze.py`（YTD/分阶段/最大回撤/量能比）→ `dia_report.py` + `_dia_tpl.html`。换板块只改 `POOL` 与板块指数代码。
- **涨停周报（周末/非交易日替代交付）**：`zt_week_analyze.py <start> <end>` → `zt_week_report.py` → `reports/涨停周报-{start}至{end}.html`。输入是**多份** `out/zt_review_D0.json` 自动合并；**晋级率用「前一日涨停池代码集合 ∩ 当日涨停池集合」**，不依赖行情快照，可跨历史日期批量复算（实测与逐日报告口径一致）。

## 已封装 skill

- **`a-share-limit-up-review`**（**项目级**`.workbuddy/skills/`）：涨停复盘（今日 vs 昨日 + 资金运动）。`SKILL.md` + `references/{data-sources,pitfalls}.md` + `scripts/`（fetch/analyze/report_template + `_check_js.py`/`_shot.py`）。**数据根目录 = `ZT_ROOT` 或 CWD**（不是脚本目录），须从项目根调用才落 `<项目>/out/`。
- **`a-share-market-turnover`**（用户级）：两市成交额 / 地量分析。
