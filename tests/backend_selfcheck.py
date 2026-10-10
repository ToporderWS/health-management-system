# -*- coding: utf-8 -*-
"""后端静态自检：语法编译 + 应用导入 + 路由清单 + 端口/敏感项扫描。

说明：本文件属于「验证工具」，统一放在 tests/ 目录，
不放在 backend/ 产品源码目录内（它自身必须包含被扫描的关键字字面量）。
运行方式：
  cd health-management-system/tests
  python backend_selfcheck.py
"""
import compileall
import io
import os
import sys

TESTS = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.abspath(os.path.join(TESTS, "..", "backend"))
sys.path.insert(0, BACKEND)

out = []

# ---------- 1. 语法编译 ----------
ok = compileall.compile_dir(BACKEND, quiet=1, force=True)
out.append("=== 1. Python 语法编译: %s ===" % ("PASS" if ok else "FAIL"))

# ---------- 2. 导入应用 + 路由清单 ----------
try:
    from app import app  # noqa: E402
    rules = sorted(
        [(str(r.rule), ",".join(sorted(m for m in r.methods if m in ("GET", "POST", "PUT", "DELETE"))))
         for r in app.url_map.iter_rules() if str(r.rule).startswith("/api")],
        key=lambda x: x[0],
    )
    out.append("=== 2. 应用导入: PASS, /api 路由数 = %d ===" % len(rules))
    for rule, methods in rules:
        out.append("    %-45s %s" % (rule, methods))
except Exception as exc:  # noqa: BLE001
    import traceback
    out.append("=== 2. 应用导入: FAIL ===")
    out.append(traceback.format_exc())

# ---------- 3. 端口与敏感信息扫描 ----------
SELF = os.path.basename(os.path.abspath(__file__))
bad_ports, secrets = [], []
for root, dirs, files in os.walk(BACKEND):
    dirs[:] = [d for d in dirs if d not in ("__pycache__", "static")]
    for f in files:
        if not f.endswith(".py") or f == SELF:
            continue
        path = os.path.join(root, f)
        text = io.open(path, encoding="utf-8").read()
        # 逐行检查并跳过注释行（注释中的"禁止 5000"属文档说明，不是真实端口配置）
        for lineno, line in enumerate(text.splitlines(), 1):
            if line.strip().startswith("#"):
                continue
            for token in (":5000", ":5001", "port=5000", "port=5001"):
                if token in line:
                    bad_ports.append("%s:%d -> %s" % (os.path.relpath(path, BACKEND), lineno, token))
out.append("=== 3a. 端口扫描(禁止 5000/5001): %s ===" % ("PASS" if not bad_ports else "FAIL " + str(bad_ports)))

# ---------- 4. 确认 8080 配置 ----------
env_example = os.path.join(BACKEND, ".env.example")
text = io.open(env_example, encoding="utf-8").read()
out.append("=== 3b. .env.example FLASK_PORT=8080: %s ===" %
           ("PASS" if "FLASK_PORT=8080" in text else "FAIL"))

# ---------- 5. 敏感信息扫描（业务代码中禁止硬编码密码 / JWT Secret） ----------
sensitive = []
for root, dirs, files in os.walk(BACKEND):
    dirs[:] = [d for d in dirs if d not in ("__pycache__", "static")]
    for f in files:
        if not f.endswith(".py") or f == SELF:
            continue
        path = os.path.join(root, f)
        for lineno, line in enumerate(io.open(path, encoding="utf-8").read().splitlines(), 1):
            s = line.strip()
            if s.startswith("#"):
                continue
            for token in ("DB_PASSWORD=", "JWT_SECRET="):
                if token in s and "_get(" not in s and "os.environ" not in s and "os.getenv" not in s:
                    sensitive.append("%s:%d -> %s" % (os.path.relpath(path, BACKEND), lineno, token))
out.append("=== 3c. 硬编码数据库密码/JWT Secret: %s ===" %
           ("PASS" if not sensitive else "FAIL " + str(sensitive)))

result = "\n".join(out)
with io.open(os.path.join(TESTS, "backend_selfcheck.txt"), "w", encoding="utf-8") as fh:
    fh.write(result)
print(result)
