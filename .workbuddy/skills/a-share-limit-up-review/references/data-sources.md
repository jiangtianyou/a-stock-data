# 数据源接口与字段全表

四个源，均为实测可用（2026-09）。

---

## 1. 同花顺 — 涨停 / 炸板 / 跌停池（唯一带「涨停原因」）

```
https://data.10jqka.com.cn/dataapi/limit_up/{kind}?page=1&limit=200
  &field=199112,10,9001,330323,330324,330325,9002,330329,133971,133970,1968584,3475914,9003,9004
  &filter=HS,GEM2STAR&order_field=330324&order_type=0&date=YYYYMMDD
```

- `kind`：`limit_up_pool` / `open_limit_pool` / `limit_down_pool`
- **`limit` 必须 ≤ 200，传 300 返回 0 条**
- **`Referer` 必须是 `https://data.10jqka.com.cn/`**；用 `/market/longhu/` 返回 0 条
- `field` 串固定，改动会导致字段错位

返回 `data` 下：

| 字段 | 含义 |
|---|---|
| `info[]` | 个股数组 |
| `info[].code` / `.name` | 代码 / 名称 |
| `info[].reason_type` | **涨停原因**，多标签以 `+` 连接 |
| `info[].high_days` | 梯队文本：`首板` / `2连板` / `3天2板` |
| `info[].limit_up_type` | `换手板` / `一字板` / `T字板` |
| `info[].first_limit_up_time` / `.last_limit_up_time` | 首次/最后封板时间（**unix 秒**，东八区） |
| `info[].open_num` | 炸板次数 |
| `info[].order_amount` | 封单额（**不要当成交额用**） |
| `info[].turnover_rate` / `.change_rate` | 换手率 / 涨跌幅 |
| `info[].is_again_limit` | 是否回封 |
| `info[].market_id` | `17` = 沪市，其余按代码前缀推断 |
| `limit_up_count` | `{today:{num,history_num,rate,open_num}, yesterday:{...}}` → **一次请求即得当日与前一交易日的涨停家数、炸板家数、封板率** |
| `limit_down_count` | 同结构 → 跌停家数与开板次数 |
| `date` / `trade_status` | 数据日期 / 交易状态 |

---

## 2. 东方财富 — 涨停 / 炸板 / 跌停池（连板数、封单、成交额、行业）

```
https://push2ex.eastmoney.com/getTopic{ZT|ZB|DT}Pool?ut=7eea3edcaed734bea9cbfc24409ed989
  &dpt=wz.ztzt&Pageindex=0&pagesize=300&sort=fbt%3Aasc&date=YYYYMMDD&_=<ms>
```

- `date` 可取历史交易日；`pagesize=300` 一次拉全（实测 89 只无需翻页）
- `push2ex` 域名实测**未被限流**

`data.pool[]` 字段：

| 字段 | 含义 |
|---|---|
| `c` / `m` / `n` | 代码 / 市场(0 深 1 沪) / 名称 |
| `p` | 价格 **×1000** |
| `zdp` | 涨跌幅 |
| `amount` | 成交额（元）← **成交额一律取这里** |
| `ltsz` / `tshare` | 流通市值 / 总市值（元） |
| `hs` | 换手率（%） |
| `lbc` | **连板数** |
| `fbt` | 首封时间，**HHMMSS 整数**（`92500` = 09:25:00） |
| `lbt` | 最后封板时间 |
| `fund` | 封单资金（元） |
| `zbc` | 炸板次数 |
| `hybk` | **行业板块** |
| `zttj{days,ct}` | 几天几板 |

与同花顺交叉校验：两池家数实测完全一致，封板时间分钟级一致率 100%。

---

## 3. 腾讯 — 批量行情与指数快照

```
https://qt.gtimg.cn/q=sh000001,sz300750,...
```

- **返回 GBK，必须 `decode("gbk")`**，否则中文名全部乱码
- 单批 ≤ 50 只；指数也可查（`sh000001` `sz399001` `sz399006` `sh000688` `bj899050`）

`~` 分隔字段索引：

| idx | 含义 | idx | 含义 |
|---|---|---|---|
| 1 | 名称 | 34 | 最低 |
| 2 | 代码 | 37 | **成交额（万元）** |
| 3 | 现价 | 38 | 换手率(%) |
| 4 | 昨收 | 39 | PE |
| 5 | 今开 | 43 | 振幅 |
| 31 | 涨跌额 | 44 | 流通市值 |
| 32 | **涨跌幅(%)** | 45 | 总市值 |
| 33 | 最高 | | |

---

## 4. 同花顺 — 指数日线（补历史成交额）

```
http://d.10jqka.com.cn/v6/line/{zs_1A0001|zs_399001|zs_399006|zs_1B0688}/01/last.js
```

- 正则取 `"data":"..."`，行格式 `日期,开,高,低,收,量,额`（额单位：元）
- **当日行不完整**（开高低与额为 0/空），只用于取历史
- 当日行情改用：`https://push2.eastmoney.com/api/qt/stock/get?secid=1.000001&fields=f43,f47,f48,f60,f170`
  （`f43` 现价×100、`f48` 成交额、`f170` 涨跌幅×100、`f60` 昨收）
- 实测锚点：2026-09-15 沪 7640 亿 + 深 8487 亿 = 16127 亿

---

## 代码 → 市场前缀

```python
def sym_of(code, market=None):
    if code.startswith(("60", "68", "5", "11", "9")):   return "sh" + code
    if code.startswith(("00", "30", "12", "15", "16", "18", "20")): return "sz" + code
    if code.startswith(("43", "83", "87", "92")):       return "bj" + code
    return "sh" + code if market == 1 else "sz" + code
```
