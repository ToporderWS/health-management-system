# -*- coding: utf-8 -*-
"""修正 tests/web_check.py 中因「地址统一」而陈旧的断言口径。

原断言写死了旧地址（http://192.168.1.4:8080/api），在产品配置改为同源相对路径后必然 FAIL。
改为语义不变式：仍要求「唯一来源 + VITE_API_BASE_URL + 相对 /api 兜底」，但不再要求具体 IP。

逐条锚点断言命中数 == 1，任一未命中 ⇒ 整批不改。
用法：python _patch_webcheck.py [--apply]
"""

import io
import json
import os
import sys

P = r"C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system\tests\web_check.py"

PAIRS = [
    # 1) 注释：唯一来源说明
    ("#   utils/config.js  = 全项目唯一 API 地址来源（读取 VITE_API_BASE_URL，并以 8080 地址兜底）",
     "#   utils/config.js  = 全项目唯一 API 地址来源（读取 VITE_API_BASE_URL，并以相对 /api 兜底）"),
    # 2) 注释：生产配置说明
    ("#   .env.production  = 生产固定 http://192.168.1.4:8080/api（需求约定）",
     "#   .env.production  = 生产同源相对路径 /api（由同源 Web Server 反向代理到 Flask:8080）"),
    # 3) 断言描述
    ('add("utils/config.js 读取 VITE_API_BASE_URL 并以 8080 地址兜底",',
     'add("utils/config.js 读取 VITE_API_BASE_URL 并以相对 /api 兜底（不含硬编码 IP）",'),
    # 4) 断言条件
    ('    and "http://192.168.1.4:8080/api" in cfg_src, "")',
     '    and "\'/api\'" in cfg_src and "192.168." not in cfg_src, "")'),
    # 5) 断言描述
    ('add(".env.production 固定 API 基础地址为 http://192.168.1.4:8080/api",',
     'add(".env.production 使用同源相对路径 /api（不含硬编码 IP）",'),
    # 6) 断言条件
    ('    "VITE_API_BASE_URL=http://192.168.1.4:8080/api" in prod, prod.strip()[:120])',
     '    "VITE_API_BASE_URL=/api" in prod and "192.168." not in prod, prod.strip()[:120])'),
]


def main():
    apply = "--apply" in sys.argv
    txt = open(P, "rb").read().decode("utf-8")

    problems = []
    plan = []
    for old, new in PAIRS:
        c = txt.count(old)
        if c != 1:
            problems.append({"hits": c, "anchor": old[:90]})
        plan.append((old, new, c))

    if problems:
        print("ABORT: 锚点未全部命中（!=1），整批不修改")
        for x in problems:
            print("   [X] hits=%d : %s" % (x["hits"], x["anchor"]))
        return 1

    for old, new, _ in plan:
        txt = txt.replace(old, new, 1)

    if apply:
        tmp = P + ".tmp_patch"
        open(tmp, "wb").write(txt.encode("utf-8"))
        os.replace(tmp, P)

    print("MODE = %s ; 锚点 6/6 命中" % ("APPLY" if apply else "DRY-RUN"))
    for old, new, c in plan:
        print("   [%d] %s" % (c, new[:95]))
    print("new_bytes =", len(txt.encode("utf-8")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
