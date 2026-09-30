# -*- coding: utf-8 -*-
"""【已废弃的旧副本 —— 请勿直接维护】转发到项目级 skill 内的权威脚本。

历史问题：本文件曾是 zt_analyze.py 的副本，**日期硬编码**（D0,D1,D2 = "20260916"...），
忽略命令行参数 → 误用时读到错误日期的 review 文件。
权威副本：.workbuddy/skills/a-share-limit-up-review/scripts/zt_analyze.py

现在本文件只做参数转发，保留入口以免破坏既有引用：
    python scripts/zt_analyze.py 20260930 20260929 20260928
"""
import os, runpy, sys

_TARGET = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".workbuddy", "skills", "a-share-limit-up-review", "scripts", "zt_analyze.py",
)
if not os.path.exists(_TARGET):
    sys.exit("权威脚本不存在: " + _TARGET)
sys.argv = [_TARGET] + sys.argv[1:]
runpy.run_path(_TARGET, run_name="__main__")
