---
name: a-stock-data
description: A股全栈数据工具包 — 覆盖行情(mootdx+腾讯+百度K线)、研报(东财+同花顺+iwencai)、信号(同花顺热点+北向+龙虎榜+解禁+行业)、资金面(融资融券+大宗交易+股东户数+分红+资金流分钟级+资金流120日)、新闻(东财个股+全球资讯)、公告(巨潮)七层数据源，内嵌全部调用代码，自包含零依赖外部文件。优先用通达信(mootdx)/腾讯(不封IP)，东财接口已内置限流防封。适用于个股估值、研报检索、题材归因、龙虎榜跟踪、解禁预警、行业轮动、融资融券跟踪、筹码分析、产业链调研、批量筛选等场景。
origin: custom
version: 3.2.1
---

# A股全栈数据工具包 V3.2.1

## 数据源优先级 & 东财防封

### 优先级原则：能用通达信/腾讯，就别用东财

| 优先级 | 数据源 | 协议 | 封 IP 风险 | 覆盖范围 |
|--------|--------|------|-----------|---------|
| **1（首选）** | **mootdx（通达信）** | TCP 7709 二进制 | **不封 IP** | K线、五档盘口、逐笔成交、财务快照、F10 |
| **2** | **腾讯财经** | HTTP GBK | **不封 IP** | 实时价、PE/PB/市值/换手率/涨跌停、指数、ETF |
| **3** | 新浪 / 巨潮 / 同花顺 | HTTP | 低 | 财报三表、公告、一致预期/热点 |
| **4（仅独有数据用）** | **东财 eastmoney** | HTTP | **高风控，极易封 IP** | 龙虎榜席位、全市场龙虎榜、限售解禁日历、融资融券、大宗交易、股东户数、分红、资金流向、个股新闻、全球资讯、研报列表/PDF |

> **防封铁律（调用东财时必须遵守）：**
> 1. **优先使用 Playwright**——东财 API 对普通 HTTP 库（如 requests）有极强的 TLS 指纹和行为风控，极易触发 `Connection aborted` (RemoteDisconnected) 错误。推荐使用 Playwright 启动 headless 浏览器，并在页面上下文发起 fetch 请求，实现无缝防封。
> 2. **共享/复用浏览器实例**——在批量或循环调用场景下，切忌重复启动/关闭 Playwright 浏览器，必须通过 context manager (`with`) 共享同一个客户端实例以极大提升速度并保持 Cookie 会话。
> 3. **串行调用 + 安全节流**——绝不对东财接口开多线程/协程并发请求。每次请求之间必须强制间隔 ≥ 1 秒。
> 4. **Requests 兜底/轻量备用**——对于偶尔的一次性单次请求，如不方便启动 Playwright，可使用 requests 兜底，但必须复用 `Session`、带正常 UA/Referer 并严格限流。

### When to Activate
- 用户要查 A 股个股估值（一致预期 / PE / PEG / PE消化）。
- 用户要拉实时行情（价格 / 五档盘口 / K线 / 涨跌停价）。
- 用户要搜研报（按主题 / 按标的 / 按行业 / 下载PDF）。
- 用户要看当日强势股、题材归因、概念热点、板块排名。
- 用户要看北向资金分钟级流向及自缓存历史。
- 用户要看个股资金流向（主力/散户/超大单/大单）、龙虎榜席位明细或全市场龙虎榜。
- 用户要看限售解禁、两融数据、大宗交易、股东户数变化或分红送转历史。
- 用户要查询个股新闻、7x24全球资讯或巨潮公告全文。
- 关键词：估值、一致预期、机构预测、市盈率、PEG、市值、研报、K线、盘口、公告、新闻、题材、热点、概念归因、北向资金、资金流向、主力、龙虎榜、解禁、限售、行业轮动、融资融券、大宗交易、股东户数、筹码集中、分红、指数、ETF。

### Prerequisites
```bash
pip install mootdx requests pandas stockstats playwright
playwright install chromium
```

| 依赖 | 用途 |
|------|------|
| mootdx | TCP行情+财务+F10（唯一非HTTP依赖） |
| playwright | 东方财富等高风控数据源防封请求（首选） |
| requests | 其他轻量 HTTP API 直连与兜底 |
| pandas | 数据处理+HTML表格解析 |
| stockstats | 技术指标计算（RSI/MACD/BOLL等） |

### 辅助代码与东财防封统一 Helper

```python
import time
import random
import base64
import urllib.parse
import requests
from playwright.sync_api import sync_playwright

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
DATACENTER_URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"

# 1. Playwright 防封客户端 (优先推荐)
class EastMoneyPlaywright:
    """
    东财 Playwright 统一防封请求客户端：
    - 启动 Headless 浏览器规避 TLS 指纹与动态 JS 风控。
    - 支持 with 语句以复用同一个浏览器实例进行批量请求，极大提高效率。
    """
    def __init__(self, headless: bool = True):
        self.playwright = None
        self.browser = None
        self.page = None
        self.headless = headless
        self.last_call_time = 0.0
        self.min_interval = 1.0  # 每次请求最小安全时间间隔

    def __enter__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        context = self.browser.new_context(user_agent=UA)
        self.page = context.new_page()
        # 初始化东财域名上下文，预加载以生成/保留合法 Cookie
        self.page.goto("https://data.eastmoney.com/")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def get(self, url: str, params: dict | None = None) -> str | dict:
        """安全节流，并在浏览器 context 下发起 fetch"""
        wait = self.min_interval - (time.time() - self.last_call_time)
        if wait > 0:
            time.sleep(wait + random.uniform(0.1, 0.3))
        
        url_full = f"{url}?{urllib.parse.urlencode(params)}" if params else url
        try:
            # 借用真实浏览器网络栈进行 fetch，返回 JSON 或 JSONP 原始文本
            js_code = """
            async (u) => {
                const response = await fetch(u);
                const text = await response.text();
                try {
                    return JSON.parse(text);
                } catch (e) {
                    return text;
                }
            }
            """
            return self.page.evaluate(js_code, url_full)
        finally:
            self.last_call_time = time.time()

    def get_bytes(self, url: str) -> bytes:
        """通过浏览器 fetch 下载二进制数据（如 PDF），避免 requests 下载触发风控阻断"""
        js_code = """
        async (u) => {
            const response = await fetch(u);
            const blob = await response.blob();
            return new Promise((resolve) => {
                const reader = new FileReader();
                reader.onloadend = () => resolve(reader.result.split(',')[1]);
                reader.readAsDataURL(blob);
            });
        }
        """
        b64_str = self.page.evaluate(js_code, url)
        return base64.b64decode(b64_str)

# 2. Requests 会话 (兜底/轻量备用)
EM_SESSION = requests.Session()
EM_SESSION.headers.update({"User-Agent": UA})
EM_MIN_INTERVAL = 1.2
_em_last_call = [0.0]

def em_get(url: str, params: dict | None = None, headers: dict | None = None, timeout: int = 15, **kwargs):
    """东财统一请求入口 (requests 兜底版)"""
    wait = EM_MIN_INTERVAL - (time.time() - _em_last_call[0])
    if wait > 0:
        time.sleep(wait + random.uniform(0.1, 0.5))
    try:
        return EM_SESSION.get(url, params=params, headers=headers, timeout=timeout, **kwargs)
    finally:
        _em_last_call[0] = time.time()

def get_prefix(code: str) -> str:
    """6位代码 → 市场前缀"""
    if code.startswith(("6", "9")):
        return "sh"
    elif code.startswith("8"):
        return "bj"
    else:
        return "sz"

def eastmoney_datacenter(report_name: str, columns: str = "ALL", filter_str: str = "", page_size: int = 50, sort_columns: str = "", sort_types: str = "-1", client: EastMoneyPlaywright | None = None) -> list[dict]:
    """东财数据中心统一查询 (支持传入 Playwright 客户端或使用 requests 兜底)"""
    params = {
        "reportName": report_name, "columns": columns,
        "filter": filter_str, "pageNumber": "1", "pageSize": str(page_size),
        "sortColumns": sort_columns, "sortTypes": sort_types,
        "source": "WEB", "client": "WEB",
    }
    if client:
        d = client.get(DATACENTER_URL, params=params)
    else:
        r = em_get(DATACENTER_URL, params=params, timeout=15)
        d = r.json()
        
    if d and isinstance(d, dict) and d.get("result") and d["result"].get("data"):
        return d["result"]["data"]
    return []
```

---

## Layer 1: 行情层（实时，不封IP）

### 1.1 mootdx — K线 + 五档盘口 + 逐笔成交 (TCP 7709)
```python
from mootdx.quotes import Quotes

client = Quotes.factory(market='std')

# K线数据 (category: 4=日线, 7=1分钟, 8=5分钟)
klines = client.bars(symbol='688017', category=4, offset=10)

# 实时报价 (含 price, open, bid1~bid5, ask1~ask5, vol, servertime等)
quotes = client.quotes(symbol=['688017', '300476'])

# 逐笔成交 (非交易时间返回空)
trades = client.transaction(symbol='688017', date='20260502')
```

### 1.2 腾讯财经 API — PE/PB/市值/换手率/涨跌停/指数/ETF
```python
import urllib.request

def tencent_quote(codes: list[str]) -> dict[str, dict]:
    """批量拉取腾讯财经实时行情。支持个股、指数(000001, 000300)、ETF(510050)"""
    prefixed = [f"{get_prefix(c)}{c}" for c in codes]
    url = "https://qt.gtimg.cn/q=" + ",".join(prefixed)
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0")
    resp = urllib.request.urlopen(req, timeout=10)
    data = resp.read().decode("gbk")

    result = {}
    for line in data.strip().split(";"):
        if not line.strip() or "=" not in line or '"' not in line:
            continue
        key = line.split("=")[0].split("_")[-1]
        vals = line.split('"')[1].split("~")
        if len(vals) < 53:
            continue
        code = key[2:]
        result[code] = {
            "name":         vals[1],
            "price":        float(vals[3]) if vals[3] else 0,
            "last_close":   float(vals[4]) if vals[4] else 0,
            "open":         float(vals[5]) if vals[5] else 0,
            "change_amt":   float(vals[31]) if vals[31] else 0,
            "change_pct":   float(vals[32]) if vals[32] else 0,
            "high":         float(vals[33]) if vals[33] else 0,
            "low":          float(vals[34]) if vals[34] else 0,
            "amount_wan":   float(vals[37]) if vals[37] else 0,
            "turnover_pct": float(vals[38]) if vals[38] else 0,
            "pe_ttm":       float(vals[39]) if vals[39] else 0,
            "amplitude_pct":float(vals[43]) if vals[43] else 0,
            "mcap_yi":      float(vals[44]) if vals[44] else 0,
            "float_mcap_yi":float(vals[45]) if vals[45] else 0,
            "pb":           float(vals[46]) if vals[46] else 0,
            "limit_up":     float(vals[47]) if vals[47] else 0,
            "limit_down":   float(vals[48]) if vals[48] else 0,
            "vol_ratio":    float(vals[49]) if vals[49] else 0,
            "pe_static":    float(vals[52]) if vals[52] else 0,
        }
    return result
```

#### 腾讯财经关键字段索引
- 索引 `3`: 当前价 | 索引 `4`: 昨收 | 索引 `38`: 换手率% | 索引 `39`: PE(TTM) | 索引 `44`: 总市值(亿) | 索引 `46`: PB(市净率) | 索引 `47`: 涨停价 | 索引 `48`: 跌停价 | 索引 `52`: PE(静)。

### 1.3 百度股市通 K线 — 带MA5/MA10/MA20
```python
import requests

def baidu_kline_with_ma(code: str, start_time: str = "") -> dict:
    """百度股市通K线 — 返回时自带 ma5/ma10/ma20 均价"""
    url = "https://finance.pae.baidu.com/selfselect/getstockquotation"
    params = {
        "all": "1", "isIndex": "false", "isBk": "false", "isBlock": "false",
        "isFutures": "false", "isStock": "true", "newFormat": "1",
        "group": "quotation_kline_ab", "finClientType": "pc",
        "code": code, "start_time": start_time, "ktype": "1",
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/vnd.finance-web.v1+json",
        "Origin": "https://gushitong.baidu.com",
        "Referer": "https://gushitong.baidu.com/",
    }
    r = requests.get(url, params=params, headers=headers, timeout=10)
    d = r.json()
    md = d.get("Result", {}).get("newMarketData", {})
    return {"keys": md.get("keys", []), "rows": md.get("marketData", "").split(";")}
```

---

## Layer 2: 研报层

### 2.1 东财研报 API — 研报列表 + PDF下载
```python
import requests
import re
from pathlib import Path

REPORT_API = "https://reportapi.eastmoney.com/report/list"
PDF_TPL = "https://pdf.dfcfw.com/pdf/H3_{info_code}_1.pdf"

def eastmoney_reports(code: str, max_pages: int = 5, client: EastMoneyPlaywright | None = None) -> list[dict]:
    """拉取指定股票的研报列表 (支持 Playwright/requests)"""
    all_records = []
    for page in range(1, max_pages + 1):
        params = {
            "industryCode": "*", "pageSize": "100", "industry": "*",
            "rating": "*", "ratingChange": "*",
            "beginTime": "2000-01-01", "endTime": "2030-01-01",
            "pageNo": str(page), "fields": "", "qType": "0",
            "orgCode": "", "code": code, "rcode": "",
            "p": str(page), "pageNum": str(page), "pageNumber": str(page),
        }
        if client:
            d = client.get(REPORT_API, params=params)
        else:
            r = em_get(REPORT_API, params=params, headers={"Referer": "https://data.eastmoney.com/"}, timeout=30)
            d = r.json()
        
        rows = d.get("data") if d else []
        if not rows:
            break
        all_records.extend(rows)
        if page >= (d.get("TotalPage", 1) if d else 1):
            break
    return all_records

def download_pdf(record: dict, target_dir: str = "./reports", client: EastMoneyPlaywright | None = None) -> str | None:
    """下载单份研报PDF，返回保存路径或None (支持 Playwright/requests)"""
    info_code = record.get("infoCode", "")
    if not info_code:
        return None
    date = (record.get("publishDate") or "")[:10]
    org = record.get("orgSName") or "未知"
    title = re.sub(r'[\\/:*?"<>|]', "_", record.get("title", ""))[:80]
    target = Path(target_dir) / f"{date}_{org}_{title}.pdf"
    if target.exists():
        return str(target)
    url = PDF_TPL.format(info_code=info_code)
    
    if client:
        try:
            content = client.get_bytes(url)
        except Exception:
            return None
    else:
        r = em_get(url, headers={"Referer": "https://data.eastmoney.com/"}, timeout=60)
        content = r.content if r.status_code == 200 else None
        
    if content and len(content) >= 1024:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return str(target)
    return None
```
- 研报 record 关键字段：`title`(标题), `publishDate`(发布日期), `orgSName`(机构), `infoCode`(用于拼PDF), `predictThisYearEps`, `predictNextYearEps`, `predictNextTwoYearEps`, `emRatingName`(评级)。

### 2.2 同花顺一致预期EPS（直连 basic.10jqka.com.cn）
```python
import requests
import pandas as pd
from io import StringIO

def ths_eps_forecast(code: str) -> pd.DataFrame:
    """同花顺机构一致预期EPS。均值即一致预期EPS。"""
    url = f"https://basic.10jqka.com.cn/new/{code}/worth.html"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Referer": "https://basic.10jqka.com.cn/",
    }
    r = requests.get(url, headers=headers, timeout=15)
    r.encoding = "gbk"
    dfs = pd.read_html(StringIO(r.text))
    for df in dfs:
        cols = [str(c) for c in df.columns]
        if any("每股收益" in c or "均值" in c for c in cols):
            return df
    return dfs[0] if dfs else pd.DataFrame()
```

### 2.3 iwencai — NL语义搜索研报（唯一能力，需 API Key）
```python
import os
import json
import secrets
import requests

IWENCAI_BASE = os.environ.get("IWENCAI_BASE_URL", "https://openapi.iwencai.com")
IWENCAI_KEY = os.environ.get("IWENCAI_API_KEY", "")

def _claw_headers() -> dict:
    return {
        "X-Claw-Call-Type": "normal",
        "X-Claw-Skill-Id": "report-search",
        "X-Claw-Skill-Version": "2.0.0",
        "X-Claw-Plugin-Id": "none",
        "X-Claw-Plugin-Version": "none",
        "X-Claw-Trace-Id": secrets.token_hex(32),
    }

def iwencai_search(query: str, channel: str = "report", size: int = 50) -> list[dict]:
    """iwencai 语义搜索。channel: 'report' / 'announcement' / 'news'"""
    headers = {"Authorization": f"Bearer {IWENCAI_KEY}", "Content-Type": "application/json", **_claw_headers()}
    payload = {"channels": [channel], "app_id": "AIME_SKILL", "query": query, "size": size}
    r = requests.post(f"{IWENCAI_BASE}/v1/comprehensive/search", json=payload, headers=headers, timeout=30)
    return r.json().get("data") or []
```

---

## Layer 3: 信号层

### 3.1 同花顺热点 — 当日强势股 + 题材归因 reason tags
```python
import requests
import pandas as pd

def ths_hot_reason(date: str = None) -> pd.DataFrame:
    """同花顺当日强势股题材归因。date格式 'YYYY-MM-DD'"""
    from datetime import date as _date
    if date is None:
        date = _date.today().strftime("%Y-%m-%d")
    url = f"http://zx.10jqka.com.cn/event/api/getharden/date/{date}/orderby/date/orderway/desc/charset/GBK/"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=10)
    rows = r.json().get("data") or []
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.rename(columns={
            "name": "名称", "code": "代码", "reason": "题材归因",
            "close": "收盘价", "zhangfu": "涨幅%", "huanshou": "换手率%",
            "ddejingliang": "大单净量"
        })
    return df
```

### 3.2 同花顺北向资金 — 实时分钟流向 + 本地自缓存历史
```python
import requests
import pandas as pd
from pathlib import Path

HSGT_HEADERS = {"User-Agent": "Mozilla/5.0", "Host": "data.hexin.cn", "Referer": "https://data.hexin.cn/"}

def hsgt_realtime() -> pd.DataFrame:
    """沪深股通当日实时分钟流向。返回累计净买入(亿元)"""
    url = "https://data.hexin.cn/market/hsgtApi/method/dayChart/"
    r = requests.get(url, headers=HSGT_HEADERS, timeout=10)
    d = r.json()
    times, hgt, sgt = d.get("time", []), d.get("hgt", []), d.get("sgt", [])
    n = len(times)
    return pd.DataFrame({
        "time": times,
        "hgt_yi": hgt[:n] + [None] * (n - len(hgt)),
        "sgt_yi": sgt[:n] + [None] * (n - len(sgt)),
    })

def _northbound_cache_path() -> Path:
    p = Path.home() / ".tradingagents" / "cache" / "northbound_daily.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def _save_northbound_snapshot(date: str, hgt: float, sgt: float):
    path = _northbound_cache_path()
    rows = {}
    if path.exists():
        for line in path.read_text().strip().split("\n")[1:]:
            parts = line.split(",")
            if len(parts) == 3: rows[parts[0]] = line
    rows[date] = f"{date},{hgt},{sgt}"
    with open(path, "w") as f:
        f.write("date,hgt,sgt\n")
        for d in sorted(rows.keys()): f.write(rows[d] + "\n")
```

### 3.3 百度股市通 — 概念板块归属
```python
import requests

def baidu_concept_blocks(code: str) -> dict:
    """概念板块归属。返回个股所属的行业、概念、地域"""
    url = f"https://finance.pae.baidu.com/api/getrelatedblock?code={code}&market=ab&typeCode=all&finClientType=pc"
    headers = {"Host": "finance.pae.baidu.com", "User-Agent": "Mozilla/5.0", "Accept": "application/vnd.finance-web.v1+json"}
    r = requests.get(url, headers=headers, timeout=10)
    d = r.json()
    if str(d.get("ResultCode", -1)) != "0":
        return {}
    result = {"industry": [], "concept": [], "region": [], "concept_tags": []}
    for block in d.get("Result", []):
        block_type = block.get("type", "")
        for item in block.get("list", []):
            entry = {"name": item.get("name", ""), "change_pct": item.get("increase", ""), "desc": item.get("desc", "")}
            if "行业" in block_type: result["industry"].append(entry)
            elif "概念" in block_type:
                result["concept"].append(entry)
                result["concept_tags"].append(entry["name"])
            elif "地域" in block_type: result["region"].append(entry)
    return result
```

### 3.4 东财 push2 — 个股资金流向（分钟级）
```python
def eastmoney_fund_flow_minute(code: str, client: EastMoneyPlaywright | None = None) -> list[dict]:
    """个股盘中实时分钟级资金流向 (主力/大单/中单/小单)。金额单位：元"""
    secid = f"1.{code}" if code.startswith("6") else f"0.{code}"
    url = "https://push2.eastmoney.com/api/qt/stock/fflow/kline/get"
    params = {"secid": secid, "klt": 1, "fields1": "f1,f2,f3,f7", "fields2": "f51,f52,f53,f54,f55,f56,f57"}
    if client:
        d = client.get(url, params=params)
    else:
        r = em_get(url, params=params, headers={"Referer": "https://quote.eastmoney.com/"}, timeout=10)
        d = r.json()
        
    rows = []
    if d and isinstance(d, dict):
        for line in d.get("data", {}).get("klines", []) or []:
            parts = line.split(",")
            if len(parts) >= 6:
                rows.append({
                    "time": parts[0], "main_net": float(parts[1]), "small_net": float(parts[2]),
                    "mid_net": float(parts[3]), "large_net": float(parts[4]), "super_net": float(parts[5]),
                })
    return rows
```

### 3.5 龙虎榜席位 — 上榜记录 + 买卖席位 TOP5 + 机构动向
```python
from datetime import datetime, timedelta

def dragon_tiger_board(code: str, trade_date: str, look_back: int = 30, client: EastMoneyPlaywright | None = None) -> dict:
    """龙虎榜个股数据汇总。"""
    start = datetime.strptime(trade_date, "%Y-%m-%d") - timedelta(days=look_back)
    start_str = start.strftime("%Y-%m-%d")
    
    # 1. 上榜记录
    records = []
    data = eastmoney_datacenter(
        "RPT_DAILYBILLBOARD_DETAILSNEW",
        filter_str=f"(TRADE_DATE>='{start_str}')(TRADE_DATE<='{trade_date}')(SECURITY_CODE=\"{code}\")",
        page_size=50, sort_columns="TRADE_DATE", sort_types="-1", client=client
    )
    for row in data:
        records.append({
            "date": str(row.get("TRADE_DATE", ""))[:10],
            "reason": row.get("EXPLANATION", ""),
            "net_buy": round((row.get("BILLBOARD_NET_AMT") or 0) / 10000, 1),
            "turnover": round(float(row.get("TURNOVERRATE") or 0), 2),
        })

    # 2. 最近一期席位明细
    seats = {"buy": [], "sell": []}
    institution = {"buy_amt": 0, "sell_amt": 0, "net_amt": 0}
    if records:
        latest_date = records[0]["date"]
        buy_data = eastmoney_datacenter("RPT_BILLBOARD_DAILYDETAILSBUY", filter_str=f"(TRADE_DATE='{latest_date}')(SECURITY_CODE=\"{code}\")", page_size=10, sort_columns="BUY", sort_types="-1", client=client)
        for row in buy_data[:5]:
            seats["buy"].append({"name": row.get("OPERATEDEPT_NAME", ""), "buy_amt": round((row.get("BUY") or 0) / 10000, 1), "sell_amt": round((row.get("SELL") or 0) / 10000, 1), "net": round((row.get("NET") or 0) / 10000, 1)})
        
        sell_data = eastmoney_datacenter("RPT_BILLBOARD_DAILYDETAILSSELL", filter_str=f"(TRADE_DATE='{latest_date}')(SECURITY_CODE=\"{code}\")", page_size=10, sort_columns="SELL", sort_types="-1", client=client)
        for row in sell_data[:5]:
            seats["sell"].append({"name": row.get("OPERATEDEPT_NAME", ""), "buy_amt": round((row.get("BUY") or 0) / 10000, 1), "sell_amt": round((row.get("SELL") or 0) / 10000, 1), "net": round((row.get("NET") or 0) / 10000, 1)})

        # 3. 机构席位买卖额汇总 (OPERATEDEPT_CODE="0" 代表机构专用席位)
        for detail_data, side in [(buy_data, "buy"), (sell_data, "sell")]:
            for row in detail_data:
                if str(row.get("OPERATEDEPT_CODE", "")) == "0":
                    amt = (row.get("BUY") or 0) if side == "buy" else (row.get("SELL") or 0)
                    if side == "buy": institution["buy_amt"] += amt
                    else: institution["sell_amt"] += amt
        institution["buy_amt"] = round(institution["buy_amt"] / 10000, 1)
        institution["sell_amt"] = round(institution["sell_amt"] / 10000, 1)
        institution["net_amt"] = round(institution["buy_amt"] - institution["sell_amt"], 1)

    return {"records": records, "seats": seats, "institution": institution}
```

### 3.6 限售解禁日历 — 历史解禁 + 未来 90 天待解禁
```python
from datetime import datetime, timedelta

def lockup_expiry(code: str, trade_date: str, forward_days: int = 90, client: EastMoneyPlaywright | None = None) -> dict:
    """限售股解禁日历"""
    # 历史解禁
    history_data = eastmoney_datacenter("RPT_LIFT_STAGE", filter_str=f'(SECURITY_CODE="{code}")', page_size=15, sort_columns="FREE_DATE", sort_types="-1", client=client)
    history = [{"date": str(row.get("FREE_DATE", ""))[:10], "type": row.get("LIMITED_STOCK_TYPE", ""), "shares": row.get("FREE_SHARES_NUM", 0), "ratio": row.get("FREE_RATIO", 0)} for row in history_data]

    # 未来解禁
    end_str = (datetime.strptime(trade_date, "%Y-%m-%d") + timedelta(days=forward_days)).strftime("%Y-%m-%d")
    upcoming_data = eastmoney_datacenter("RPT_LIFT_STAGE", filter_str=f'(SECURITY_CODE="{code}")(FREE_DATE>=\'{trade_date}\')(FREE_DATE<=\'{end_str}\')', page_size=20, sort_columns="FREE_DATE", sort_types="1", client=client)
    upcoming = [{"date": str(row.get("FREE_DATE", ""))[:10], "type": row.get("LIMITED_STOCK_TYPE", ""), "shares": row.get("FREE_SHARES_NUM", 0), "ratio": row.get("FREE_RATIO", 0)} for row in upcoming_data]

    return {"history": history, "upcoming": upcoming}
```

### 3.7 行业板块排名 (东财 clist)
```python
def industry_comparison(top_n: int = 20, client: EastMoneyPlaywright | None = None) -> dict:
    """行业板块涨跌幅排名，监控全行业轮动"""
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {"pn": "1", "pz": "100", "po": "1", "np": "1", "fltt": "2", "invt": "2", "fs": "m:90+t:2", "fields": "f2,f3,f4,f12,f13,f14,f104,f105,f128,f136,f140,f141,f207"}
    if client:
        d = client.get(url, params=params)
    else:
        r = em_get(url, params=params, headers={"User-Agent": UA}, timeout=15)
        d = r.json()
    items = d.get("data", {}).get("diff", []) if d else []
    rows = []
    for i, item in enumerate(items):
        rows.append({
            "rank": i + 1, "name": item.get("f14", ""), "change_pct": item.get("f3", 0), "code": item.get("f12", ""),
            "up_count": item.get("f104", 0), "down_count": item.get("f105", 0), "leader": item.get("f140", ""), "leader_change": item.get("f136", 0),
        })
    return {"top": rows[:top_n], "bottom": rows[-top_n:], "total": len(rows)}
```

### 3.8 全市场龙虎榜
```python
from datetime import datetime

def daily_dragon_tiger(trade_date: str = None, min_net_buy: float = None, client: EastMoneyPlaywright | None = None) -> dict:
    """全市场当日所有上榜股票汇总"""
    if trade_date is None:
        trade_date = datetime.now().strftime("%Y-%m-%d")
    data = eastmoney_datacenter("RPT_DAILYBILLBOARD_DETAILSNEW", filter_str=f"(TRADE_DATE>='{trade_date}')(TRADE_DATE<='{trade_date}')", page_size=500, sort_columns="BILLBOARD_NET_AMT", sort_types="-1", client=client)
    stocks = []
    for row in data:
        net_buy = (row.get("BILLBOARD_NET_AMT") or 0) / 10000
        if min_net_buy is not None and net_buy < min_net_buy: continue
        stocks.append({
            "code": row.get("SECURITY_CODE", ""), "name": row.get("SECURITY_NAME_ABBR", ""), "reason": row.get("EXPLANATION", ""),
            "close": row.get("CLOSE_PRICE") or 0, "change_pct": round(float(row.get("CHANGE_RATE") or 0), 2),
            "net_buy_wan": round(net_buy, 1), "buy_wan": round((row.get("BILLBOARD_BUY_AMT") or 0) / 10000, 1),
            "sell_wan": round((row.get("BILLBOARD_SELL_AMT") or 0) / 10000, 1), "turnover_pct": round(float(row.get("TURNOVERRATE") or 0), 2)
        })
    return {"date": trade_date, "total_records": len(stocks), "stocks": stocks}
```

### 3.9 信号层组合用法：题材热度 + 资金验证
```python
# 示例：拉取当日强势股，并统计高频题材标签以识别市场主线
df_hot = ths_hot_reason()
from collections import Counter
all_tags = [t.strip() for r in df_hot["题材归因"].dropna() for t in str(r).split("+") if t.strip()]
print("当日 TOP 10 题材热度:", Counter(all_tags).most_common(10))
```

---

## Layer 4: 资金面 / 筹码层

### 4.1 融资融券明细（日级）
```python
def margin_trading(code: str, page_size: int = 30, client: EastMoneyPlaywright | None = None) -> list[dict]:
    """融资融券明细。金额单位：元"""
    data = eastmoney_datacenter("RPTA_WEB_RZRQ_GGMX", filter_str=f'(SCODE="{code}")', page_size=page_size, sort_columns="DATE", sort_types="-1", client=client)
    return [{
        "date": str(row.get("DATE", ""))[:10],
        "rzye": row.get("RZYE", 0), "rzmre": row.get("RZMRE", 0), "rzche": row.get("RZCHE", 0),
        "rqye": row.get("RQYE", 0), "rqmcl": row.get("RQMCL", 0), "rqchl": row.get("RQCHL", 0), "rzrqye": row.get("RZRQYE", 0)
    } for row in data]
```

### 4.2 大宗交易记录
```python
def block_trade(code: str, page_size: int = 20, client: EastMoneyPlaywright | None = None) -> list[dict]:
    """大宗交易记录明细"""
    data = eastmoney_datacenter("RPT_DATA_BLOCKTRADE", filter_str=f'(SECURITY_CODE="{code}")', page_size=page_size, sort_columns="TRADE_DATE", sort_types="-1", client=client)
    rows = []
    for row in data:
        close, deal_price = row.get("CLOSE_PRICE") or 0, row.get("DEAL_PRICE") or 0
        premium = ((deal_price / close - 1) * 100) if close else 0
        rows.append({
            "date": str(row.get("TRADE_DATE", ""))[:10], "price": deal_price, "close": close, "premium_pct": round(premium, 2),
            "vol": row.get("DEAL_VOLUME", 0), "amount": row.get("DEAL_AMT", 0), "buyer": row.get("BUYER_NAME", ""), "seller": row.get("SELLER_NAME", "")
        })
    return rows
```

### 4.3 股东户数变化（季度级）
```python
def holder_num_change(code: str, page_size: int = 10, client: EastMoneyPlaywright | None = None) -> list[dict]:
    """股东户数环比变化，代表筹码集散度（持续减少 = 筹码集中）"""
    data = eastmoney_datacenter("RPT_HOLDERNUMLATEST", filter_str=f'(SECURITY_CODE="{code}")', page_size=page_size, sort_columns="END_DATE", sort_types="-1", client=client)
    return [{
        "date": str(row.get("END_DATE", ""))[:10], "holder_num": row.get("HOLDER_NUM", 0),
        "change_num": row.get("HOLDER_NUM_CHANGE", 0), "change_ratio": row.get("HOLDER_NUM_RATIO", 0), "avg_shares": row.get("AVG_FREE_SHARES", 0)
    } for row in data]
```

### 4.4 分红送转历史
```python
def dividend_history(code: str, page_size: int = 20, client: EastMoneyPlaywright | None = None) -> list[dict]:
    """分红送转历史。每股派息(税前)、每10股转增、每10股送股"""
    data = eastmoney_datacenter("RPT_SHAREBONUS_DET", filter_str=f'(SECURITY_CODE="{code}")', page_size=page_size, sort_columns="EX_DIVIDEND_DATE", sort_types="-1", client=client)
    return [{
        "date": str(row.get("EX_DIVIDEND_DATE", ""))[:10], "bonus_rmb": row.get("PRETAX_BONUS_RMB", 0),
        "transfer_ratio": row.get("TRANSFER_RATIO", 0), "bonus_ratio": row.get("BONUS_RATIO", 0), "plan": row.get("ASSIGN_PROGRESS", "")
    } for row in data]
```

### 4.5 个股主力资金流（120日，日级）
```python
def stock_fund_flow_120d(code: str, client: EastMoneyPlaywright | None = None) -> list[dict]:
    """个股主力/大单/中单/小单日级净流入历史（最近120天）。金额单位：元"""
    market_code = 1 if code.startswith("6") else 0
    url = "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get"
    params = {"secid": f"{market_code}.{code}", "fields1": "f1,f2,f3,f7", "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65", "lmt": "120"}
    if client:
        res = client.get(url, params=params)
    else:
        r = em_get(url, params=params, headers={"Referer": "https://quote.eastmoney.com/"}, timeout=15)
        res = r.json()
    d = res if res else {}
    rows = []
    for line in d.get("data", {}).get("klines", []) or []:
        parts = line.split(",")
        if len(parts) >= 7:
            rows.append({
                "date": parts[0],
                "main_net": float(parts[1]) if parts[1] != "-" else 0,
                "small_net": float(parts[2]) if parts[2] != "-" else 0,
                "mid_net": float(parts[3]) if parts[3] != "-" else 0,
                "large_net": float(parts[4]) if parts[4] != "-" else 0,
                "super_net": float(parts[5]) if parts[5] != "-" else 0,
            })
    return rows
```

---

## Layer 5: 新闻层

### 5.1 东财个股新闻（JSONP 接口）
```python
import re
import json

def eastmoney_stock_news(code: str, page_size: int = 20, client: EastMoneyPlaywright | None = None) -> list[dict]:
    """获取个股关联的新闻资讯列表"""
    cb = "jQuery_news"
    url = "https://search-api-web.eastmoney.com/search/jsonp"
    inner_params = json.dumps({
        "uid": "", "keyword": code, "type": ["cmsArticleWebOld"], "client": "web", "clientType": "web", "clientVersion": "curr",
        "param": {"cmsArticleWebOld": {"searchScope": "default", "sort": "default", "pageIndex": 1, "pageSize": page_size, "preTag": "", "postTag": ""}},
    }, separators=(',', ':'))
    if client:
        res = client.get(url, params={"cb": cb, "param": inner_params})
        text = res if isinstance(res, str) else json.dumps(res)
    else:
        r = em_get(url, params={"cb": cb, "param": inner_params}, headers={"Referer": "https://so.eastmoney.com/"}, timeout=15)
        text = r.text
    
    json_str = text[text.index("(") + 1 : text.rindex(")")]
    d = json.loads(json_str)
    
    rows = []
    articles = d.get("result", {}).get("cmsArticleWebOld", []) or []
    for a in articles:
        rows.append({
            "title": re.sub(r'<[^>]+>', '', a.get("title", "")),
            "content": re.sub(r'<[^>]+>', '', a.get("content", ""))[:200],
            "time": a.get("date", ""), "source": a.get("mediaName", ""), "url": a.get("url", ""),
        })
    return rows
```

### 5.2 东财全球资讯（7x24 滚动快讯）
```python
import uuid

def eastmoney_global_news(page_size: int = 50, client: EastMoneyPlaywright | None = None) -> list[dict]:
    """全市场7x24小时财经滚动快讯。替代下线的财联社。"""
    url = "https://np-weblist.eastmoney.com/comm/web/getFastNewsList"
    params = {"client": "web", "biz": "web_724", "fastColumn": "102", "sortEnd": "", "pageSize": str(page_size), "req_trace": str(uuid.uuid4())}
    if client:
        d = client.get(url, params=params)
    else:
        r = em_get(url, params=params, headers={"Referer": "https://kuaixun.eastmoney.com/"}, timeout=10)
        d = r.json()
    rows = []
    if d and isinstance(d, dict):
        for item in d.get("data", {}).get("fastNewsList", []) or []:
            rows.append({"title": item.get("title", ""), "summary": item.get("summary", "")[:200], "time": item.get("showTime", "")})
    return rows
```

---

## Layer 6: 基础数据层

### 6.1 mootdx 财务快照（季报快照）
```python
from mootdx.quotes import Quotes
client = Quotes.factory(market='std')
fin = client.finance(symbol='688017')
# 返回流通股本、总股本、EPS、ROE、净利润、主营收入等37个财务关键指标
```

### 6.2 mootdx F10 公司文本资料
```python
from mootdx.quotes import Quotes
client = Quotes.factory(market='std')
# 支持类别: 最新提示, 公司概况, 财务分析, 股东研究, 股本结构, 资本运作, 业内点评, 行业分析, 公司大事
text = client.F10(symbol='688017', name="公司概况")
```

### 6.3 东财个股基本面 (直连 push2)
```python
def eastmoney_stock_info(code: str, client: EastMoneyPlaywright | None = None) -> dict:
    """获取个股基础字段：行业归属、总股本、流通股、总市值、流通市值、上市日期等"""
    market_code = 1 if code.startswith("6") else 0
    url = "https://push2.eastmoney.com/api/qt/stock/get"
    params = {"fltt": "2", "invt": "2", "fields": "f57,f58,f84,f85,f127,f116,f117,f189,f43", "secid": f"{market_code}.{code}"}
    if client:
        res = client.get(url, params=params)
    else:
        r = em_get(url, params=params, headers={"User-Agent": UA}, timeout=10)
        res = r.json()
    d = res.get("data", {}) if res and isinstance(res, dict) else {}
    return {
        "code": d.get("f57", ""), "name": d.get("f58", ""), "industry": d.get("f127", ""),
        "total_shares": d.get("f84", 0), "float_shares": d.get("f85", 0),
        "mcap": d.get("f116", 0), "float_mcap": d.get("f117", 0), "list_date": str(d.get("f189", "")), "price": d.get("f43", 0),
    }
```

### 6.4 新浪财报三表（资产负债表/利润表/现金流量表）
```python
import requests

def sina_financial_report(code: str, report_type: str = "lrb", num: int = 8) -> list[dict]:
    """新浪财报三表。report_type: 'fzb'(资产负债表) / 'lrb'(利润表) / 'llb'(现金流量表)"""
    prefix = "sh" if code.startswith("6") else "sz"
    url = "https://quotes.sina.cn/cn/api/openapi.php/CompanyFinanceService.getFinanceReport2022"
    params = {"paperCode": f"{prefix}{code}", "source": report_type, "type": "0", "page": "1", "num": str(num)}
    r = requests.get(url, params=params, headers={"User-Agent": UA}, timeout=15)
    report_list = r.json().get("result", {}).get("data", {}).get("report_list", {}) or {}

    rows = []
    for period in sorted(report_list.keys(), reverse=True)[:num]:
        obj = report_list[period]
        rec = {"报告期": f"{period[:4]}-{period[4:6]}-{period[6:8]}"}
        for it in obj.get("data", []) or []:
            title = it.get("item_title", "")
            if not title or it.get("item_value") is None: continue
            rec[title] = it.get("item_value")
            tongbi = it.get("item_tongbi")
            if tongbi not in (None, ""): rec[title + "_同比"] = tongbi
        rows.append(rec)
    return rows
```

---

## Layer 7: 公告层

### 7.1 巨潮公告全文检索
```python
import requests
from datetime import datetime

def cninfo_announcements(code: str, page_size: int = 30) -> list[dict]:
    """从巨潮资讯获取公司最新的公告列表"""
    url = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
    org_id = f"gssh0{code}" if code.startswith("6") else (f"gsbj0{code}" if code.startswith(("8","4")) else f"gssz0{code}")
    payload = {"stock": f"{code},{org_id}", "tabName": "fulltext", "pageSize": str(page_size), "pageNum": "1", "isHLtitle": "true"}
    headers = {"User-Agent": UA, "Content-Type": "application/x-www-form-urlencoded", "Referer": "https://www.cninfo.com.cn/new/disclosure", "Origin": "https://www.cninfo.com.cn"}
    r = requests.post(url, data=payload, headers=headers, timeout=15)
    
    rows = []
    for item in r.json().get("announcements", []) or []:
        ts = item.get("announcementTime")
        date_str = datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d") if isinstance(ts, (int, float)) else str(ts)[:10]
        rows.append({
            "title": item.get("announcementTitle", ""), "type": item.get("announcementTypeName", ""), "date": date_str,
            "url": f"https://www.cninfo.com.cn/new/disclosure/detail?annoId={item.get('announcementId', '')}"
        })
    return rows
```

### 7.2 mootdx F10 公告摘要
```python
from mootdx.quotes import Quotes
client = Quotes.factory(market='std')
text = client.F10(symbol='688017', name='最新提示') # 包含公告/股东会决议/分红摘要
```

---

## 估值与分析核心公式

### 估值公式定义
```python
import math

def forward_pe(price: float, eps_forecast: float) -> float:
    """前向PE = 股价 / 未来年度一致预期EPS"""
    return price / eps_forecast if eps_forecast > 0 else float("inf")

def pe_digestion(current_pe: float, cagr: float, target_pe: float = 30) -> float:
    """PE消化年数：将当前PE通过CAGR消化到目标PE(默认30)所需的年限"""
    if current_pe <= target_pe: return 0.0
    return math.log(current_pe / target_pe) / math.log(1 + cagr) if cagr > 0 else float("inf")

def calc_peg(pe: float, cagr: float) -> float:
    """PEG = 前向PE / (CAGR * 100)。 <1便宜，1-1.5合理，>1.5偏贵"""
    return pe / (cagr * 100) if cagr > 0 else float("inf")
```

- 投资框架速查：
  1. **壁垒**：是否有深厚壁垒（行业龙头/技术优势/产能壁垒）。
  2. **增速**：一致预期复合增速 CAGR 是否大于 30%。
  3. **PE消化**：消化到 30x PE 合理水平所需的年数是否在 2 年内（合理），大于 4 年则偏贵。
  4. **PEG**：是否小于 1.5。

---

## 完整调研流程示例

### 流程 A: 单票完整估值与评级分析
```python
import math
import urllib.request
import pandas as pd

def full_valuation(code: str) -> dict:
    # 1. 腾讯实时行情拉取当前估值
    prefix = get_prefix(code)
    url = f"https://qt.gtimg.cn/q={prefix}{code}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    data = urllib.request.urlopen(req, timeout=10).read().decode("gbk")
    vals = data.split('"')[1].split("~")
    price, mcap, pe_ttm, pb = float(vals[3]), float(vals[44]), float(vals[39]) if vals[39] else 0, float(vals[46]) if vals[46] else 0

    # 2. 从同花顺获取一致预期
    df = ths_eps_forecast(code)
    eps_cur = eps_next = analyst_count = None
    if not df.empty and len(df.columns) >= 3:
        try:
            eps_cur = float(df.iloc[0].iloc[2]) if pd.notna(df.iloc[0].iloc[2]) else None
            analyst_count = int(df.iloc[0].iloc[1]) if pd.notna(df.iloc[0].iloc[1]) else 0
            eps_next = float(df.iloc[1].iloc[2]) if pd.notna(df.iloc[1].iloc[2]) else None
        except Exception: pass

    # 3. 核心估值计算
    pe_fwd = price / eps_cur if eps_cur else float("inf")
    cagr = (eps_next / eps_cur - 1) if (eps_cur and eps_next) else 0
    peg = pe_fwd / (cagr * 100) if cagr > 0 else float("inf")
    digest = math.log(pe_fwd / 30) / math.log(1 + cagr) if pe_fwd > 30 and cagr > 0 else 0

    return {
        "name": vals[1], "price": price, "mcap_yi": mcap, "pe_ttm": pe_ttm, "pb": pb,
        "pe_fwd": round(pe_fwd, 1) if eps_cur else None, "cagr_pct": round(cagr * 100, 0) if cagr else None,
        "peg": round(peg, 2) if peg != float("inf") else None, "digest_years": round(digest, 1), "analyst_count": analyst_count,
    }
```

### 流程 B: 多标的批量估值比对
```python
stocks = ["688017", "300308", "300476"]
for code in stocks:
    try:
        r = full_valuation(code)
        print(f"{r['name']}({code}): PE_fwd={r['pe_fwd']}x PEG={r['peg']} 消化={r['digest_years']}年 覆盖机构={r['analyst_count']}")
    except Exception as e:
        print(f"{code} 估值比对失败: {e}")
```

### 流程 C: 主题研报语义检索与提取 (Playwright 高效复用示例)
```python
# 1. 语义搜索特定题材的研报
articles = iwencai_search("人形机器人减速器 丝杠", channel="report", size=20)
# 2. 拿到关联股票后批量拉取东财细分研报 (使用 Playwright 共享浏览器会话以极大提升速度)
with EastMoneyPlaywright() as emp:
    for a in articles[:5]:
        stocks = a.get("stock_infos") or []
        for s in stocks:
            code = s.get("code")
            if code:
                reports = eastmoney_reports(code, max_pages=1, client=emp)
                print(f"股票 {code} 最新研报数: {len(reports)}")
```

### 流程 D: 个股360度资金/筹码与盘口画像 (Playwright 高效复用示例)
```python
code = "688017"

# 使用 with 语句，让所有东财接口复用同一个 Playwright 浏览器会话，规避 IP 封禁
with EastMoneyPlaywright() as emp:
    # 1. 查询基本面与板块概念归属
    info = eastmoney_stock_info(code, client=emp)
    blocks = baidu_concept_blocks(code)  # 百度接口不需要 Playwright
    print(f"{info['name']}({code}) 所属概念: {', '.join(blocks.get('concept_tags', [])[:10])}")
    
    # 2. 统计近20日主力累计资金流向
    flow_120 = stock_fund_flow_120d(code, client=emp)
    if flow_120:
        total_main = sum(d["main_net"] for d in flow_120[-20:])
        print(f"近20日主力净流入累计: {total_main/1e8:.2f} 亿元")
    
    # 3. 获取龙虎榜及解禁警示
    dtb = dragon_tiger_board(code, "2026-05-17", client=emp)
    lockup = lockup_expiry(code, "2026-05-17", client=emp)
    print(f"近30日龙虎榜次数: {len(dtb['records'])}，未来90天待解禁批次: {len(lockup['upcoming'])}")
    
    # 4. 股东户数与融资余额追踪
    holders = holder_num_change(code, client=emp)
    margin = margin_trading(code, page_size=5, client=emp)
    if holders: print(f"最新股东户数: {holders[0]['holder_num']}，环比变化: {holders[0]['change_ratio']}%")
    if margin: print(f"最新两融余额: {margin[0]['rzye']/1e8:.2f} 亿元")
```
