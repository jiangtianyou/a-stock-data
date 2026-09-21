# 口径坑与工程踩坑

## 口径类（会导致结论错误，必读）

### 1. 同花顺 `currency_value` / `order_amount` 不是成交额 ⚠️ 最致命

实测某股 `currency_value` = 58.16 亿，但按「换手率 4.357% × 流通市值」反推只有约 5.8 亿，**差 10 倍**。
用它汇总会得出「涨停股合计成交 1.03 万亿 > 两市总成交 1.84 万亿」的荒谬结论。

→ 成交额、换手率、市值、封单**一律取东财字段**（`amount` / `hs` / `ltsz` / `fund`）。
→ 收尾自检：`涨停股合计成交额 ÷ 两市成交额` 应落在 **3%~8%**。
   注意该比值**与涨停家数强相关**，家数腰斩时会自然跌破 3%（实测 2026-09-17 仅 47 家 → 2.0%，
   而前一日 89 家 → 4.3%）。此时应改用**单只中位成交额**做交叉验证
   （同日中位 5.53 亿 vs 前日 3.88 亿，不降反升 → 字段源无误），并在报告口径说明中写明原因。

### 2. 家数不要数池子条数

- 跌停/炸板家数用 `limit_up_count` / `limit_down_count` 的**汇总字段**。
  实测 2026-09-16 跌停 4 家，而 `limit_down_pool` 返回 0 条。
- 涨停家数用 `len(info)` 与 `limit_up_count.today.num` 互相验证。

### 3. 排序 tie-break 必须完整，否则结果不可复现

`collections.Counter` + `set()` 排序时，同分项的先后取决于 `set()` 迭代顺序，
而 **Python 对 str 的哈希每进程随机化** → 同一份数据两次跑出的「行业 Top18」不一样。

```python
# 错：同分项顺序随机
sorted(set(hy0) | set(hy1), key=lambda k: -(hy0.get(k, 0) * 2 + hy1.get(k, 0)))
# 对：补全 tie-break
sorted(set(hy0) | set(hy1),
       key=lambda k: (-(hy0.get(k, 0) * 2 + hy1.get(k, 0)), -hy0.get(k, 0), -hy1.get(k, 0), k))
```

### 4. 涨跌幅字段的可靠源

- 腾讯 `qt.gtimg.cn` 的 f32 可靠。
- 东财 `push2delay` 的 clist `f24`/`f25` **不可靠**（实测「元件」60 日显示 -6.5%，实际 +41.8%），**不可用于排序**。

### 5. 「晋级率」的分组口径

昨日涨停股按**昨日连板数**分组（首板 / 连板），不要按今日连板数分组——
后者是本轮的结果而非前提，会让「首板晋级率」失真。

### 6. `x or 默认值` 会把「0」当成缺失值 ⚠️

报告模板里若用 `sorted(perf, key=lambda x: -(x["pct"] or -99))` 排序，
则 **涨跌幅恰为 0.00% 的个股（当日收平）会被当成缺失值排到最末尾**，
「最弱」标签就会指向一只平盘股而不是真正的最弱股。

实测 2026-09-17：`PERF_MIN` 取 `min(pcts)` 得 -8.09%（远望谷），
而同一次运行的 `PERF_MIN_NAME` 却是「浙江永强」（pct=0.0）——两个数字自相矛盾。
改用显式 None 判断：

```python
perf_sorted = sorted(perf, key=lambda x: -(x["pct"] if x["pct"] is not None else -999))
```

**通用规则**：凡是给数值字段设默认值，一律用 `if v is None` 而不是 `v or d`；
收尾时加一条自检 —— 「最弱股的名称与其涨跌幅是否对应同一个代码」。

### 7. 东财 `fbt` 是 HHMMSS 整数，切字符串前必须 `zfill(6)` ⚠️

炸板池（`em_ZB.pool`）里 `fbt` 是不带前导零的**整数**（`92500` = 09:25:00，`130052` = 13:00:52）。
若按 `str(int(v))[:2] + ":" + str(int(v))[2:4]` 格式化，
**10:00 之前的封板时间全部被切错**：`92500` → `92:50`、`95842` → `95:84`、`94045` → `94:04`。
因为 09:00 段的 HH 只有 1 位，`[:2]` 把 `H H` 的后一位和分针的第一位一起吃掉了。
`10:00` 之后恰好有 6 位，所以 bug 只在早盘时段显形，极易漏检。

```python
def hhmm(v):
    s = str(int(v)).zfill(6)      # 92500 -> '092500'
    return s[:2] + ":" + s[2:4]   # -> '09:25'
```

> 注意与 `r0`（涨停池，来自同花顺）区分：那里的 `fbt` 已经是 `"09:30:09"` 字符串，直接 `[:5]` 即可。
> 两个源的字段同名不同型，写模板时不要混用同一段格式化代码。

**自检**：报告出图后 `grep -o "[0-9][0-9]:[0-9][0-9]"` 取唯一值，
**不允许出现 `9x:xx`（90~99 点）或 `1x:xx` 中分钟 >59 的值**。

---

### 8. 东财涨停池与同花顺家数的差额，必须能全部归因到北交所

东财 `em_ZT.tc` 会比同花顺 `num` 多出 `920xxx` 的北交所标的：

| 日期 | 同花顺 | 东财 tc | 差额 | 归因 |
|---|---|---|---|---|
| 2026-09-18 | 77 | 78 | 1 | 920298 |
| 2026-09-21 | 101 | 103 | 2 | 920478 峆一药业、920427 华维设计 |

**处理规范**：报告统一按**沪深口径**（同花顺数）出数，并在「数据口径」里写明
「东财池 N 条，差额 M 只为北交所标的（列出代码），已剔除」。

**自检**：每次复盘都跑一次 `set(em_codes) - set(ths_codes)`，
若差额里出现沪深代码（`60/00/30/68` 开头）→ 说明字段错位或某一源漏数，必须排查，不要直接采用同花顺口径掩盖。

```python
r = B["dates"][D0]
diff = sorted({x["c"] for x in r["em_ZT"]["pool"]} - {x["code"] for x in r["ths_zt"]["info"]})
assert all(c.startswith("92") for c in diff), f"非北交所差额: {diff}"
```

---

### 9. 同花顺「跌停池」明细接口会 404，不能用它判断跌停家数

`dataapi/limit_up/limit_down_pool` 实测返回 **HTTP 404**（2026-09-21），`ths_dt` 落盘为 `None`；
东财侧 `em_DT` 会出现 `tc=2` 但 `pool=[]` 的自相矛盾状态。

**唯一可靠源是汇总字段** `ths_zt["limit_down_count"]["today"]["num"]`（与第 2 条同源）。

**处理规范**：明细拿不到时，报告写「跌停 N 家（同花顺汇总口径；明细池接口当日不可用，未列名单）」，
**不要**因为池子返回 0 条就写成「跌停 0 家」——这正是第 2 条踩过的坑。

---

### 10. 同花顺封单字段（`order_amount`）收盘 30 分钟内仍在刷新 ⚠️

**同一交易日的两次抓取，同花顺 `order_amount` / `order_volume` 会变**：

| 个股 | 15:31 抓取 | 16:11 抓取 | 倍数 |
|---|---|---|---|
| 我爱我家 000560 | 327 万 | 5,916 万 | 18× |
| 百通能源 001376 | 220 万 | 11,980 万 | 54× |
| 华森制药 002907 | 106 万 | 3,550 万 | 33× |
| 奥赛康 002755 | 13.3 万 | 271 万 | 20× |

同一时段内**家数、涨跌幅、封板时间、成交额都没变**，只有封单字段在变 →
说明同花顺封单是**延迟结算字段**，15:30 抓到的不是终值。

**处理规范**：
1. 封单口径**一律取东财 `fund`**（本流程已如此），不受此影响；
2. 若将来改用同花顺 `order_amount` 出「封单结构性结论」，
   **必须等 16:00 之后再抓**，否则会把「某只票封单只有几百万」当成事实写进报告；
3. 盘中/早于 16:00 的补跑，报告中「封单合计」类数字应标注时点。

**幂等自检（判断数据是否已稳定，可复用）**：

```python
def canon(o):                       # 排序归一化：列表按 code/c 排序后再比
    if isinstance(o, dict): return {k: canon(v) for k, v in sorted(o.items())}
    if isinstance(o, list):
        if o and isinstance(o[0], dict):
            key = "code" if "code" in o[0] else ("c" if "c" in o[0] else None)
            if key: return sorted((canon(x) for x in o), key=lambda x: str(x.get(key)))
        return [canon(x) for x in o]
    return o
# 两次抓取后：json.dumps(canon(a), sort_keys=True) == json.dumps(canon(b), sort_keys=True)
```

> **必须归一化后再比**：同一份数据两次抓取的**列表顺序本身不稳定**
> （`em_ZB` / `ths_block` 的首项会互换），直接 diff 会看到几十处「差异」，
> 全是排序抖动，容易误判成数据变化。

### 11. 指数日线（`index_hist`）盘后会把「当日行」移出返回窗口 ⚠️

**现象**：同一交易日盘后多次抓取，`index_hist[code].rows` 的**最后一行会变**。
2026-09-21 实测（`zs_1B0688` 科创50）：

| 抓取时刻 | rows 末两行 |
|---|---|
| 16:11 | … `20260918`, **`20260921`** ← 含当日 |
| 16:34 / 16:36 | … `20260917`, `20260918` ← **当日消失** |

16:11 之后当日行被移出窗口、稳定为「不含当日」，与代码无关，是接口侧行为。

**为什么不会污染报告**：本流程的当日成交额取自**实时快照** `indexes[sym].amount_wan`，
历史行只按**显式日期**查 D1/D2（`hist_row(hcode, D1)`），所以 `rows` 里有没有当日都无影响。

**必须遵守的两条**：
1. **禁止用 `index_hist[code]["rows"][-1]` 当作「当日」** —— 它在 16:30 后会静默回退到前一交易日，
   算出来的「今日成交额」会等于昨日值，且不报错。
2. **幂等复跑比对时，这四个键必须排除**：`generated_at`、`dates`（含 trade_status 等易变元数据）、
   `indexes`（`float_mv` / `total_mv` 尾数抖动）、`index_hist`（本条窗口滑动）。
   只比 **`D0` / `D1` / `today_zt_quotes` / `yesterday_zt_today`** —— 这四个一致即可判定「数据未变、报告可复用」。
   本次若把 `index_hist` 也纳入比对，会看到 8 行「差异」而误判为数据变化、白跑一遍完整流程。

```python
CORE_KEYS = ("D0", "D1", "today_zt_quotes", "yesterday_zt_today")   # 幂等判定只看这四个
same = all(json.dumps(canon(a[k]), ensure_ascii=False, sort_keys=True)
           == json.dumps(canon(b[k]), ensure_ascii=False, sort_keys=True) for k in CORE_KEYS)
```

---

## 工程类

### 落盘：全部成功才覆盖

限流/空返回会让重跑把已抓好的数据覆盖成空。统一写法：

```python
tmp = fp + ".tmp"
with open(tmp, "w", encoding="utf-8") as f: json.dump(bundle, f, ...)
os.replace(tmp, fp)      # 原子替换
```

### 字典推导会静默吞数据

`{it['name']: it for it in items}` 遇到同名键会互相覆盖。价格序列与全收益序列常同名，
必须按类别分开存（如 `data["price"]` / `data["tr"]`）。

### 长任务进度：不要用管道

`python x.py | tail -N` 会缓冲到进程结束才输出，看不到进度。
用 `> out/x.log 2>&1` 落盘，再读文件；或直接看 stdout。

### Windows 环境

- **编码**：跑脚本前设 `PYTHONIOENCODING=utf-8`；写日志文件时同理。腾讯接口单独要 `decode("gbk")`。
- **路径**：managed venv 的 python 在 `Scripts/python.exe`（**不是** `bin/python`）。
- **依赖归属**：`pandas/numpy` 在 managed venv；**`playwright` 只装在系统 python 3.11**
  （`C:/Users/Administrator/AppData/Local/Programs/Python/Python311/python.exe`），
  在 venv 里跑 `_shot.py` 会 `ModuleNotFoundError`。
- **grep/sed 处理 UTF-8 中文常失效**：改用 Read 工具或 python 读文件。
- `mkdir`/`cp` 等 gow 工具偶发路径异常：改用 python `os.makedirs` / `shutil.copy2`。

### 同一文件的多个 Edit 不要并行提交

实测 4 个 Edit 同批提交只生效 1 个（相互覆盖）。批量改配置类脚本时用
「一次性补丁脚本 + `assert old in s`」更稳。

---

## 报告生成类

- **不要用 f-string 生成含 CSS/JS 的 HTML**：`{` `}` 转义是地狱，`data:{json.dumps(x)}` 需写成
  `{json.dumps(x)}}}`（3 个右花括号）且极易漏。统一用 `__占位符__` + `str.replace`。
- 收尾必查占位符残留：`re.findall(r"__[A-Z_0-9]+__", html)` 必须为空。
- ECharts 横向条形图**类目 >25 时**容器高 ≈ 类目数 × 21px 且 `axisLabel.interval: 0`，
  否则标签跳显、与柱子视觉错位。
- 双 Y 轴图图例用 `top:3, left:'center'`，**不要 `right:8`**（会与右侧轴名重叠，渲染成「胜率%率」）。
- 瀑布图不能用 `data:[[起, 止]]`，须「透明占位 stack + 数值 stack」。
- **ECharts 用本地托管而非纯 CDN**（2026-09-20 踩坑）：jsdelivr 在 Playwright 侧会间歇性
  `ERR_CONNECTION_RESET`，表现为自检输出「7 个图表容器 `canvas=0`」+ `PAGEERROR: echarts is not defined`，
  而**同一时刻 `curl` 却能正常下载**——极具误导性，容易去改图表配置。
  正解：`<script src="../assets/echarts.min.js">`（已入库）＋ `if(typeof echarts==='undefined')` 时 `document.write` 回退 CDN。
  另：`cdn.bootcdn.net` / `cdn.staticfile.org` 的 `echarts/5.5.1` 路径实测 404，`lib.baomitu.com` 返回的是错误页，都不可用。
- **ECharts 类目轴首项在底部**：排名类热力图 / 条形图的数组**必须先反转**再传给 `yAxis.data`，
  否则「合计最大」的行业渲染在最下方。热力图 data 是 `[x下标, y下标, 值]`（x=日期、y=行业），别把两个下标写反。

---

## 通道限流

- 东财 `push2his`（历史 K 线）与 `push2`（clist）**IP 级限流，全域名同时封**
  （含 `1.` / `7.` / `82.` 数字前缀镜像），表现为连接被 RST、0.06s 即失败。
  被限后 `push2delay` 仍有响应，但只提供延迟行情。
- **`push2ex`（涨停池）不在限流范围内**，实测稳定。
- 通达信 MCP 有**调用配额**，耗尽返回 `MCP error -32603: Your usage quota has been reached`；
  本流程不依赖它，批量拉指数前也建议先确认配额。
