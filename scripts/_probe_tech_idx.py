# -*- coding: utf-8 -*-
"""探测科技板块指数在腾讯通道的可用性"""
import requests

s = requests.Session()
s.trust_env = False
s.headers.update({"User-Agent": "Mozilla/5.0 Chrome/120", "Referer": "https://gu.qq.com/"})

CAND = [
    # 中证主题(试探 sh/sz 前缀)
    "sh930713", "sz930713", "sh931071", "sh931461", "sh931079", "sh930601",
    "sh930651", "sh931160", "sh930851", "sh930850", "sh931144", "sh930790",
    "sh931187", "sh931380", "sh931087", "sh931406", "sh931066", "sh931167",
    "shH30184", "shh30184", "shH30318",
    # 交易所挂牌(大概率可用)
    "sh000998", "sh000993", "sh000994", "sh000935", "sh000936", "sz399811",
    "sz399608", "sz399970", "sz399996", "sz399967", "sz399959", "sz399973",
    "sz399971", "sz399803", "sh000688", "sh000300",
]

r = s.get("https://qt.gtimg.cn/q=" + ",".join(CAND), timeout=20)
r.encoding = "gbk"
ok, bad = [], []
for line in r.text.strip().split(";"):
    line = line.strip()
    if not line or "=" not in line:
        continue
    key = line.split("=")[0].replace("v_", "")
    val = line.split("=", 1)[1].strip('"')
    parts = val.split("~")
    if len(parts) > 3 and parts[1]:
        ok.append((key, parts[1], parts[3]))
    else:
        bad.append(key)

print("=== 有效 ===")
for k, n, p in ok:
    print(f"  {k:<12} {n:<16} {p}")
print("\n=== 无效 ===")
print("  " + ", ".join(bad))
