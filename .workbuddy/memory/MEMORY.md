# a-stock-data 项目长期笔记

> 详细接口/口径细节已下沉到 skill（见文末「已封装 skill」），此处只留跨任务通用的经验与结论。

## 数据源

### 可用通道（按用途）
| 用途 | 通道 | 要点 |
|---|---|---|
| 全收益指数（唯一） | 中证官网 `csindex.com.cn/csindex-home/perf/index-perf?indexCode={code}&startDate=&endDate=` | 一次取全历史；**全收益只返回 close 无 open**（跳空分解只能用价格指数）；连续请求会 403 或返回空 data，间隔 2s + 失败退避 60s 可恢复。全收益代码 = `H`+价格代码后 5 位（000922→H00922）；例外：红利低波 H30269→H20269、红利低波100 930955→H20955；399xxx 官网无数据 |
| 指数/个股月线日线全历史 | 腾讯 `web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={sym},month\|day,起始,结束,count,qfq` | 字段序 **开-收-高-低-量**；日线须分段（6 年/段、count=1700，段区间 1990/1997/2003/2009/2015/2021）；9 指数×6 段≈60~90s 0 失败 |
| 轻量月线（短历史） | `data.gtimg.cn/flashdata/hushen/monthly/{sym}.js` | 日期为 6 位 YYMMDD 需补世纪，行尾带 `\` 续行 |
| 板块/概念日线（最全） | 同花顺 `d.10jqka.com.cn/v6/line/bk_{code}/01/last.js` | 行业 881101~881175（~87 个）；概念有效区间 **885450~886400**（~362 个，<885450 → 404）；实测无限流、0.01~0.3s；约 140 个交易日 |
| 代码/名称核验 | `qt.gtimg.cn/q=sh000001,...` | **GBK**，`~` 分隔，f2=名称 |
| 板块列表（仅名称） | 新浪 `money.finance.sina.com.cn/q/view/newFLJK.php?param=class\|industry` | 概念 175 / 行业 84；**`CN_MarketData.getKLineData` 对板块返回 null，拿不到历史** |

| 板块/个股行情·财务·资金（**板块分析首选**） | westock CLI `C:/Users/Administrator/.local/bin/westock.exe` | 板块定位 `search <kw> --type sector` → 成分股 `sector constituent pt02231435`；K线 `kline <sym> --limit 300`（覆盖一年+）；财务 `finance <sym> --type income\|balance\|cashflow`；资金 `fund flow a,b,c`（支持批量）。**字段坑见「脚本与工程约定」** |

### 失效 / 限流
- 东财 `push2his`（历史 K 线）与 `push2`（clist）**IP 级限流，全域名同时封**（含 1./7./82. 数字前缀镜像），表现为连接被 RST、0.06s 即失败。
- 被限后 `push2delay` 的 clist 仍可用，但 **f24/f25 不是可靠涨跌幅字段**（实测与 K 线严重不符），**不可用于排序**；clist 每页上限 100，`fid=f3` 只返回"当日涨幅前 N"，会漏弱势板块。
- 通达信 MCP 有**调用配额**，耗尽返回 `unauthorized / quota is below 10`；批量拉指数前先确认。

### 已验证指数代码
- 宽基：sh000001 上证 / sz399001 深成 / sh000300 沪深300 / sh000905 中证500 / sh000852 中证1000 / sz399006 创业板指 / sh000688 科创50 / sh000016 上证50 / sh000922 中证红利 / sh000015 上证红利
- 全指一级行业 sh000986~000995；中证800行业 sh000928~000937
- 主题：sz399997 白酒 / sz399998 煤炭 / sz399986 银行 / sz399975 证券 / sz399967 军工 / sz399989 医疗 / sz399808 新能 / sz399976 CS新能车 / sz399971 传媒 / sh000827 环保 / sh000978 医药100 / sh000819 有色

## 脚本与工程约定

- **两段式**：先抓取落盘 `out/*.json`，再分析/出报告，避免长任务丢进度。
- 长时抓取：域名轮换 + 指数退避重试 + **逐品种增量打印**（不要 `| tail -N`，会缓冲到结束）。
- 网络脚本统一绕过代理（`ProxyHandler({})` / `Session.trust_env=False`）。
- **抓取脚本必须「全部成功才覆盖落盘文件」**（写 `.tmp` 再 `os.replace`）；限流/空返回会让重跑把好数据覆盖成空（已踩坑）。
- `{it['name']:it for it in items}` 类字典推导会因同名键互相覆盖（价格/全收益序列同名），须按类别分开存。
- **排序 tie-break 必须完整**：`sorted(set(...), key=计数)` 时同分项先后取决于 `set()` 迭代顺序，而 str 哈希**每进程随机化** → 同一份数据两次跑出的榜单不一样。补全为 `(..., -今值, -昨值, 名称)` 之类才可复现。
- **同一文件的多个 Edit 不要在同一条消息里并行提交**（会相互覆盖，实测 4 个只生效 1 个）；批量改配置类脚本用「一次性补丁脚本 + `assert a in s`」。
- 本机 Git Bash 下 grep/sed 处理 UTF-8 中文常失效 → 改用 Read 工具或 python 读文件。
- **依赖归属**：`pandas/numpy` 在 managed venv（`~/.workbuddy/binaries/python/envs/default/Scripts/python.exe`）；**`playwright` 只在系统 python 3.11**（`C:/Users/Administrator/AppData/Local/Programs/Python/Python311/python.exe`），venv 里跑 `_shot.py` 会 ModuleNotFoundError。
- **westock 字段坑**：`finance --type income` 中所有 `_Q` 后缀字段（`NPParentCompanyCutYOY_Q`、`NPParentCompanyYOY_Q`、`TORGrowRate_Q`、`OperatingRevenueGrowRate_Q`）都是**单季**同比；累计口径只有 `NPParentCompanyYOY`（归母）/`TORGrowRate`（营收）可直接用，**扣非累计同比必须自算**（本期 vs 去年同期 `NPDeductNonRecurringPL`）——力量钻石 2026H1 扣非累计 +1249.33%，而 `_Q` 字段给 +12839%（Q2 单季），差 10 倍。另外**亏损公司 `NPParentCompanyYOY` 为正 = 亏损收窄**，渲染成红色「+25.7%」会被误读为增长。
- **同花顺板块指数 `bk_885xxx` 日期格式为 `YYYYMMDD`**（8 位无横线），与 westock 的 `YYYY-MM-DD` 混入同一套指标计算前必须归一化。
- **同名不同型的字段最易埋 bug**：东财涨停/炸板池的 `fbt` 是 **HHMMSS 整数**（`92500`=09:25:00），切分前必须 `zfill(6)`，否则 10:00 前渲染成 `92:50`；而 `r0`（同花顺来源）的 `fbt` 已是 `"09:30:09"` 字符串。**字段名相同不等于类型/格式相同，跨源拼接前先 `type()` 确认。**
- **东财涨停池含北交所**：`em_ZT.tc` 会多出 `920xxx` 标的（09-18 东财 78 vs 同花顺 77），报告须显式声明「已按沪深口径」取数，不要静默取其一。
- 早期落盘的板块 JSON（`out/ths_concept_all.json`）`name` 字段是**双重转义字面量**（`'\u57f9\u80b2\u94bb\u77f3'`），用中文做 `in` 匹配会全部失败；改用 `chr()` 码点构造关键词或 `unicode_escape` 还原。
- **同名 key 的残留赋值会静默覆盖正确值**（`K["ZBJ_FLOW20"]` 被后面一行旧的 `*0` 赋值覆盖成 0）。改生成脚本后必须重新截图核对关键数字，不能只看占位符无残留。

## 报告规范

- 浅底深字、结论先行（首屏 lead + KPI 卡）、ECharts 5（`cdn.jsdelivr.net/npm/echarts@5`）、**红涨绿跌**。
- **正文数字一律由数据推导 + `__占位符__` + `.replace()` 注入，禁止手写**；收尾 `re.findall(r"__[A-Z_0-9]+__", html)` 确认无残留。
- **不要用 f-string 生成含 CSS/JS 的 HTML**（花括号转义地狱），用占位符替换。
- ECharts 横向条形图**类目 >25 时**容器高 ≈ 类目数×21px 且 `axisLabel.interval:0`，否则标签跳显错位。
- 双 Y 轴图图例用 `top:3,left:'center'`，**不要 `right:8`**（会与右侧轴名重叠，渲染成"胜率%率"）；`grid.top≥52` 做垂直分离。
- 瀑布图不能用 `data:[[起,止]]`，须「透明占位 stack + 数值 stack」。
- 交付前：`_check_js.py <html>`（`node --check` 提取的内联 JS）+ `_shot.py <html> <scrollY...>`（Playwright 截图自检，用系统 3.11）。
- **ECharts 本地托管 + CDN 兜底**（2026-09-20 起）：`assets/echarts.min.js`（1.0MB，来自 jsdelivr）；页面写
  `<script src="../assets/echarts.min.js"></script>` + `if(typeof echarts==='undefined'){document.write(CDN)}`。
  起因：jsdelivr 在 Playwright 侧频繁 `ERR_CONNECTION_RESET`，导致自检时 7 个图表容器 `canvas=0` + `PAGEERROR: echarts is not defined`，
  而 `curl` 同一时刻能通 —— **「截图自检报 canvas=0」先怀疑 CDN，不要先改图表配置**。
- **ECharts 类目轴首项在底部**：排名类热力图 / 条形图的数组**必须先反转**再喂给 `yAxis.data`，
  否则「合计最大的行业」会渲染在最下方（用户从上往下读会先看到最弱的）。

## 结论沉淀

- **红利指数季节性**：6 月是 A 股最强负季节性（7 个红利指数全负，价格口径 -4.01%、胜率 30.9%、t≈-3.2，包揽 81 指数负季节性第 1/2 名）。其中约 **1.33% 是除息机械扣减**（6+7 月占全年分红 73.5%）——**评估红利真实回报必须用全收益指数**，价格指数每年 6-7 月少算约 2.7pp。剩余弱势主因是风格轮动（6 月成长 +3.01% vs 红利 -2.80%）。正季节性（2/7/12 月）2015 年后基本消失，仅 6 月坏效应保留约 40%。

## 样本口径铁律（季节性 / 事件研究）

- **1991-1992 上证处于无涨跌停 / T+0 极端期**（1 月均值 28%、std 173%），月度统计起点取 **1997-01 或 2000-01**，否则均值失真。
- 小样本 + 极端值必看**中位数**（如 2024 年节前 10 日 +22.8% 会把均值拉偏）。
- **双基准分解（剥离首日跳空）**：算「事件后 N 日」同时给 `close(T+N)/close(T-1)`（含跳空）与 `close(T+N)/close(T+1)`（剔除首日），差额 = 首日贡献。A 股国庆节后 5 日中首日贡献 ≈85%。
- **用「环境档」替代「日历标签」**：季节性按**市场状态**切分才有解释力，已验证变量=**当年 1-8 月累计涨幅**（强势 >+10% / 震荡 ±10% / 弱势 <-10%）；10 月胜率随档位单调下降（88.9%/30.8%/28.6%）。
- **培育钻石（2026「叙事重构」标本，2026-09-17）**：市场从「珠宝周期股」重定价为「AI 算力散热材料股」。核心 TOP3 = 力量钻石(301071) / 黄河旋风(600172) / 四方达(300179)。**核心结论：涨的是预期，赚的是现状**——2026H1 板块利润改善来自工业金刚石涨价 + 培育钻石价格企稳，散热业务公司自述「尚未对主营业务及收入产生影响」（方正证券口径 2026 年 AI 芯片渗透率仅 1%）。结构是「上半年主升 +161%~+301% → 7-8 月深调 -14%~-37%（YTD 最大回撤 49%~54%）→ 9 月二波」，**只看 YTD 涨幅会严重误判当前位置**。板块内分层残酷：材料端普涨，消费/渠道端（潮宏基 -27%、豫园 -11%、中国黄金 -6%）YTD 下跌、9 月仍在跌。中兵红箭反差最大：市值最大、YTD -16.6% 垫底、20 日主力净流出 3 亿，且公司自述「业绩回暖与散热概念关联不大」。

## 自建等权指数（板块复盘）— 模板见 PCB 板块 8 月复盘

- 脚本链：`pcb_fetch.py` → `pcb_analyze.py` / `pcb_extra.py` → `pcb_report.py` → `reports/PCB板块8月以来走势复盘-20260915.html`。
- **致命坑**：`cur *= (1+avg_ret(d))` 之后再 `vals[base_d]=100`，会把**基期当日涨幅重复计入**（本次多算 5.2%，+49.22% 被放大成 +56.96%）。正确写法：遇基期日 `vals[base_d]=100.0; continue`，不累乘。**任何自建指数先断言「首日收益为 0」**。
- 最大回撤须记录**回撤当时的峰值日**（`pk_at`），不能用全局 peak 日（指数持续新高时会输出时间倒序）。
- 四件套指标：①区间涨幅 + 区间最高/最低（附距高点）②日成交额与指数的**背离**（缩量新高是重要信号）③全板块同向日 & 单日 |涨跌|≥5% 异动计数（区分 β 主导 vs 个股 Alpha）④「前期跌幅 × 本期涨幅」散点 + 回归斜率（区分超跌反弹 vs 基本面驱动）。
- 样本池分层并**显式声明等权口径与商业市值加权指数不可比**，样本遗漏写进口径说明。

## 可复用脚本链

- 季节性（81 品种月线）：`seasonality_fetch_tx2.py` → `seasonality_analyze.py` → `seasonality_report.py`
- 日历效应（9 指数日线）：`oct_fetch_daily.py` → `oct_analyze.py` / `oct_extra.py` → `oct_report.py`
- 渲染自检：`scripts/_shot.py <html相对路径> [滚动位置...]`、`scripts/_check_js.py <html>`
- **板块核心标的分析（泛化模板）**：`dia_fetch.py`（westock kline/quote + 同花顺板块指数 + 基准）→ `dia_fin.py`（利润表 6 期 + 资金流）→ `dia_analyze.py`（YTD / 分阶段 / 最大回撤 / 量能比）→ `dia_report.py` + `_dia_tpl.html`（占位符替换出 HTML）。换板块只需改 `POOL` 名单与板块指数代码。已在培育钻石板块跑通（2026-09-17）。
- **涨停周报（周末/非交易日替代交付）**：`zt_week_analyze.py <start> <end>` → `zt_week_report.py <start> <end>` → `reports/涨停周报-{start}至{end}.html`。
  输入是**多份** `out/zt_review_D0.json`，按日期自动合并（同日多份优先 D0 份），所以只要历史上跑过 zt_fetch 的日期都能进周报；
  缺口日期补跑一次 zt_fetch 即可。**晋级率用「前一日涨停池代码集合 ∩ 当日涨停池集合」计算，不依赖行情快照**，
  实测与逐日报告的快照口径完全一致（9/16=37.5%、9/17=10.1%、9/18=25.5%）——这是唯一能跨历史日期批量复算晋级率的方法。

## 已封装 skill

- **`a-share-limit-up-review`**（**项目级**，`.workbuddy/skills/` 下）：涨停复盘（今日 vs 昨日 + 资金运动）。
  `SKILL.md`（流程/八维度/自检/回归基线）+ `references/{data-sources,pitfalls}.md` + `scripts/`（fetch/analyze/report_template + `_check_js.py`/`_shot.py`）。
  脚本数据根目录 = `ZT_ROOT` 或 **CWD**（不是脚本所在目录），从项目根调用才落 `<项目>/out/`。
- **`a-share-market-turnover`**（用户级）：两市成交额 / 地量分析。
