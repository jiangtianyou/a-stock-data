import sys
import os
import time
import random
import urllib.parse
import requests
import pandas as pd
from collections import Counter
from datetime import date as _date, timedelta
from playwright.sync_api import sync_playwright

# 添加 notify 脚本的路径
sys.path.append("D:/Desktop/Playground/dydown/scripts")
try:
    import notify
except ImportError:
    notify = None
    print("Warning: notify module not found at D:/Desktop/Playground/dydown/scripts")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"

EM_SESSION = requests.Session()
EM_SESSION.trust_env = False
EM_SESSION.headers.update({"User-Agent": UA})
EM_MIN_INTERVAL = 1.2
_em_last_call = [0.0]

class EastMoneyPlaywright:
    """
    东财 Playwright 统一防封请求客户端：
    - 启动 Headless 浏览器规避 TLS 指纹与动态 JS 风控。
    - 显式通过 direct:// 禁用代理避免连接错误，支持 with 语句复用浏览器。
    """
    def __init__(self, headless: bool = True):
        self.playwright = None
        self.browser = None
        self.page = None
        self.headless = headless
        self.last_call_time = 0.0
        self.min_interval = 1.0

    def __enter__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless, 
            args=['--no-sandbox', '--no-proxy-server']
        )
        context = self.browser.new_context(user_agent=UA)
        self.page = context.new_page()
        # 预加载东财域名生成 cookie
        self.page.goto("https://data.eastmoney.com/")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def get(self, url: str, params: dict | None = None) -> str | dict:
        """安全节流并在浏览器 context 下发起请求，避开 CORS 限制"""
        wait = self.min_interval - (time.time() - self.last_call_time)
        if wait > 0:
            time.sleep(wait + random.uniform(0.1, 0.3))
        
        url_full = f"{url}?{urllib.parse.urlencode(params)}" if params else url
        try:
            response = self.page.request.get(url_full)
            try:
                return response.json()
            except Exception:
                return response.text()
        finally:
            self.last_call_time = time.time()

def em_get(url: str, params: dict | None = None, headers: dict | None = None, timeout: int = 15, max_retries: int = 3, **kwargs):
    """东财统一请求入口 (requests 兜底版，带重试及忽略代理)"""
    for attempt in range(max_retries):
        wait = EM_MIN_INTERVAL - (time.time() - _em_last_call[0])
        if wait > 0:
            time.sleep(wait + random.uniform(0.1, 0.5))
        try:
            _em_last_call[0] = time.time()
            r = EM_SESSION.get(url, params=params, headers=headers, timeout=timeout, **kwargs)
            if r.status_code == 200:
                return r
            print(f"Request failed with status code {r.status_code}, retrying ({attempt + 1}/{max_retries})...")
        except Exception as e:
            print(f"Request error: {e}, retrying ({attempt + 1}/{max_retries})...")
            if attempt == max_retries - 1:
                raise e

def _get_industry_ranking_from_sina() -> list[dict]:
    """新浪财经板块行情接口作为容灾备用源"""
    url = "http://money.finance.sina.com.cn/q/view/newSinaHy.php"
    try:
        print("Fetching industry ranking from Sina Finance as fallback...")
        r = em_get(url, timeout=10)
        if not r:
            return []
        content = r.content.decode('gbk', errors='ignore')
        start = content.find('{')
        end = content.rfind('}') + 1
        if start == -1 or end == 0:
            return []
        
        import json
        data = json.loads(content[start:end])
        results = []
        for key, val in data.items():
            parts = val.split(',')
            if len(parts) < 13:
                continue
            
            try:
                change_pct = float(parts[5])
                leader_change = float(parts[11])
            except ValueError:
                change_pct = 0.0
                leader_change = 0.0
                
            results.append({
                "name": parts[1],
                "change_pct": change_pct,
                "code": parts[0],
                "up_count": int(parts[2]) if parts[2].isdigit() else 0,
                "down_count": 0,
                "leader": parts[8].replace("sh", "").replace("sz", ""),
                "leader_name": parts[12],
                "leader_change": leader_change,
            })
        
        results.sort(key=lambda x: x["change_pct"], reverse=True)
        for i, item in enumerate(results):
            item["rank"] = i + 1
        return results
    except Exception as e:
        print(f"Fallback to Sina Finance API failed: {e}")
        return []

def get_industry_ranking(client: EastMoneyPlaywright = None) -> list[dict]:
    """东财全行业板块涨跌幅排名"""
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {"pn": 1, "pz": 100, "po": 1, "np": 1, "fltt": 2, "invt": 2,
              "fs": "m:90+t:2", "fields": "f2,f3,f4,f12,f13,f14,f104,f105,f128,f136,f140,f141,f207"}
    res_json = None
    if client:
        try:
            res_json = client.get(url, params=params)
        except Exception as e:
            print(f"Playwright request failed: {e}, falling back to requests...")
    
    if not res_json:
        try:
            r = em_get(url, params=params, timeout=15)
            res_json = r.json()
        except Exception as e:
            print(f"Fallback requests failed too: {e}")
            
    if not res_json or not isinstance(res_json, dict):
        return _get_industry_ranking_from_sina()
        
    try:
        items = res_json.get("data", {}).get("diff", [])
        if not items:
            return _get_industry_ranking_from_sina()
        return [{
            "rank": i+1, "name": item.get("f14", ""), "change_pct": item.get("f3", 0),
            "code": item.get("f12", ""), "up_count": item.get("f104", 0),
            "down_count": item.get("f105", 0), "leader": item.get("f140", ""),
            "leader_name": item.get("f128", ""),
            "leader_change": item.get("f136", 0),
        } for i, item in enumerate(items)]
    except Exception as e:
        print(f"Error parsing industry ranking: {e}")
        return _get_industry_ranking_from_sina()

def get_hot_reasons(client: EastMoneyPlaywright = None, trade_date: str = None) -> pd.DataFrame:
    """同花顺当日强势股 + 题材标签 (从东财补充获取涨幅数据)"""
    if trade_date is None:
        trade_date = _date.today().strftime("%Y-%m-%d")
    url = f"http://zx.10jqka.com.cn/event/api/getharden/date/{trade_date}/orderby/date/orderway/desc/charset/GBK/"
    try:
        r = EM_SESSION.get(url, timeout=10)
        rows = r.json().get("data") or []
    except Exception as e:
        print(f"Error getting hot reasons for {trade_date}: {e}")
        rows = []
        
    df = pd.DataFrame(rows)
    if df.empty:
        return df
        
    # 提取代码并去东财获取涨跌幅
    codes = df["code"].tolist()
    secids = [f"1.{c}" if c.startswith('6') or c.startswith('9') else f"0.{c}" for c in codes]
            
    # 批量获取行情
    stock_map = {}
    batch_size = 50
    for i in range(0, len(secids), batch_size):
        batch_secids = secids[i:i+batch_size]
        secids_str = ",".join(batch_secids)
        res_json = None
        if client:
            try:
                res_json = client.get(
                    "https://push2.eastmoney.com/api/qt/ulist.np/get",
                    params={"fltt": 2, "fields": "f2,f3,f12", "secids": secids_str}
                )
            except Exception as e:
                print(f"Playwright batch quotes failed: {e}, falling back to requests...")
        
        if not res_json:
            try:
                r_east = em_get(
                    "https://push2.eastmoney.com/api/qt/ulist.np/get",
                    params={"fltt": 2, "fields": "f2,f3,f12", "secids": secids_str},
                    timeout=10
                )
                res_json = r_east.json()
            except Exception as e:
                print(f"Fallback batch quotes failed: {e}")
                
        if res_json and isinstance(res_json, dict):
            try:
                data_east = res_json.get("data", {}).get("diff", [])
                for item in data_east:
                    stock_map[item.get("f12")] = {"zhangfu": item.get("f3"), "close": item.get("f2")}
            except Exception as e:
                print(f"Error parsing batch quotes: {e}")
            
    for row in rows:
        code = row.get("code")
        row["zhangfu"] = stock_map[code]["zhangfu"] if code in stock_map else None
        row["close"] = stock_map[code]["close"] if code in stock_map else None
            
    df = pd.DataFrame(rows)
    df = df.rename(columns={"name": "名称", "code": "代码", "reason": "题材归因",
                            "close": "收盘价", "zhangfu": "涨幅%", "huanshou": "换手率%", "ddejingliang": "大单净量"})
    return df

def get_theme_heat(df_hot: pd.DataFrame) -> list[tuple]:
    """统计题材标签高频分布，识别市场主线"""
    if df_hot.empty or "题材归因" not in df_hot.columns:
        return []
    all_tags = []
    for r in df_hot["题材归因"].dropna():
        for t in str(r).split("+"):
            t = t.strip()
            if t:
                all_tags.append(t)
    return Counter(all_tags).most_common(15)

def analyze_and_notify():
    # 启用 Playwright 客户端
    with EastMoneyPlaywright() as client:
        # 1. 查找有同花顺强势股数据的最近交易日
        today_str = _date.today().strftime("%Y-%m-%d")
        df_hot = pd.DataFrame()
        actual_date = today_str
        
        # 尝试最近7天
        for i in range(7):
            check_date = (_date.today() - timedelta(days=i)).strftime("%Y-%m-%d")
            print(f"Checking data for {check_date}...")
            df_temp = get_hot_reasons(client, check_date)
            if not df_temp.empty:
                df_hot = df_temp
                actual_date = check_date
                print(f"Found valid data for date: {actual_date}, count: {len(df_hot)}")
                break
                
        if df_hot.empty:
            print("Error: Could not find any valid stock data in the last 7 days.")
            # 回退使用今天的空数据继续
            
        # 2. 获取行业板块排名
        sectors = get_industry_ranking(client)
        top_sectors = [s for s in sectors if s["change_pct"] > 0][:10]
        
        # 3. 统计题材热度
        themes = get_theme_heat(df_hot)
        
        # 4. 组装 Markdown 报告
        md_lines = []
        md_lines.append(f"# 今日强势板块与题材分析报告")
        md_lines.append(f"**数据统计日期**: {actual_date} (今日: {today_str})")
        md_lines.append("")
        
        # 行业板块部分
        md_lines.append(f"## 📊 TOP 10 强势行业板块")
        if top_sectors:
            for s in top_sectors:
                leader_str = f" | 领涨: **{s['leader_name']} ({s['leader']})** (<font color=\"warning\">{s['leader_change']:+.2f}%</font>)" if s.get("leader") else ""
                stats_str = f"涨{s['up_count']}家/跌{s['down_count']}家" if s['down_count'] > 0 else f"共{s['up_count']}家"
                md_lines.append(f"- **{s['name']}** (<font color=\"warning\">{s['change_pct']:+.2f}%</font>) {stats_str}{leader_str}")
        else:
            md_lines.append("暂无上涨的行业板块数据")
        md_lines.append("")
        
        # 题材热度部分
        md_lines.append(f"## 🔥 当日题材热度 TOP 15")
        if themes:
            for tag, cnt in themes:
                md_lines.append(f"- **{tag}**: {cnt} 次")
        else:
            md_lines.append("暂无题材热度统计数据")
        md_lines.append("")
        
        # 强势股前20部分
        md_lines.append(f"## 🚀 同花顺当日强势股 (前12)")
        if not df_hot.empty:
            hot_stocks = df_hot.to_dict("records")
            for s in hot_stocks[:12]:
                zf = s.get('涨幅%')
                zf_str = f" (<font color=\"warning\">{zf:+.2f}%</font>)" if zf is not None else ""
                md_lines.append(f"- **{s.get('名称','')}** ({s.get('代码','')}){zf_str} | 题材: {s.get('题材归因','')}")
        else:
            md_lines.append("暂无强势股数据")
            
        content = "\n".join(md_lines)
        
        # # 企微字数超限截断 (安全阈值 4000 字节)
        # content_bytes = content.encode('utf-8')
        # if len(content_bytes) > 4000:
        #     print(f"Warning: content length {len(content_bytes)} bytes exceeds limit. Truncating...")
        #     content = content_bytes[:3900].decode('utf-8', 'ignore') + "\n\n*(部分内容因字数超限已截断)*"
            
        # # 5. 调用 notify 进行通知
        # if notify:
        #     print("Sending notification via notify.py...")
        #     try:
        #         res = notify.send_markdown(content)
        #         print(f"Notification result: {res}")
        #     except Exception as e:
        #         print(f"Error sending notification: {e}")
        # else:
        #     print("Error: notify module is not available, printing output instead:")
        #     print(content)

if __name__ == "__main__":
    analyze_and_notify()
