# -*- coding: utf-8 -*-
"""【已废弃的旧副本 —— 请勿直接维护】转发到项目级 skill 内的权威脚本。

历史问题：本文件曾是 zt_fetch.py 的副本，**日期硬编码**（D0,D1 = "20260916","20260915"），
忽略命令行参数 → 误用时会把结果静默写到错误日期的文件（2026-09-30 实测踩到）。
权威副本：.workbuddy/skills/a-share-limit-up-review/scripts/zt_fetch.py

现在本文件只做参数转发，保留入口以免破坏既有引用：
    python scripts/zt_fetch.py 20260930 20260929
等价于
    python .workbuddy/skills/a-share-limit-up-review/scripts/zt_fetch.py 20260930 20260929
"""
import os, runpy, sys

_TARGET = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".workbuddy", "skills", "a-share-limit-up-review", "scripts", "zt_fetch.py",
)
if not os.path.exists(_TARGET):
    sys.exit("权威脚本不存在: " + _TARGET)
sys.argv = [_TARGET] + sys.argv[1:]
runpy.run_path(_TARGET, run_name="__main__")
