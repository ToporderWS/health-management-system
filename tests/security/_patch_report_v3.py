# -*- coding: utf-8 -*-
"""锚点式回写 FINAL_SECURITY_ACCEPTANCE_REPORT.md（第 3 版：存量事项① 处置）。

3 处改动，逐条断言命中数 == 1，任一未命中 ⇒ 整个文件不改。
用法：python _patch_report_v3.py [--apply]
"""
import io
import os
import sys

P = r"C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system\docs\FINAL_SECURITY_ACCEPTANCE_REPORT.md"

OLD3 = "| 3 | `miniapp/common/config.js` 局域网地址为 `192.168.2.219:8080`，而 `backend/config.py` 与 `management-web/.env.production` 兜底为 `192.168.1.4:8080` | 两端地址不一致，更换网络环境时**必有一端不可达**；建议统一为单一来源或按环境注入（**本轮未改动**） |"
NEW3 = "| 3 | ~~PC 端与小程序端 API 地址不一致（PC 兜底 `192.168.1.4:8080` / 小程序 `192.168.2.219:8080`）~~ | ✅ **已处置**（2026-10-01 19:40，见 §十二）。PC 端统一为**同源相对路径**（`/api`、`/static/upload/`），彻底移除开发 LAN IP；小程序保留唯一 LAN 配置入口（真机调试必需） |"

OLD_S = "7. **判定 FINAL_SECURITY_ACCEPTANCE = PASS**（安全验收转绿）。**本判定不构成项目最终封板**；§八 中 2 项存量事项仍待单独授权处置。"
NEW_S = ("7. **判定 FINAL_SECURITY_ACCEPTANCE = PASS**（安全验收转绿）。**本判定不构成项目最终封板**；"
         "§八 中「`JWT_SECRET` 占位值」「历届测试残留数据」2 项存量事项仍待单独授权处置。\n"
         "8. **存量事项①「API 地址 / LAN IP 配置统一」已于 2026-10-01 19:40 处置完成**"
         "（同源相对路径方案，5 文件 / 11 行，未触碰任何业务逻辑与数据）。处置与复验记录见 §十二；"
         "`STORAGE_ITEM_01_API_ADDRESS = PASS`。")

OLD_TAIL = "*报告第 1 版：2026-10-01 18:21 · 第 2 版（DEF-01 修复后复验）：2026-10-01 19:30*"

SEC12 = """## 十二、存量事项① 处置记录：API 地址 / LAN IP 配置统一（第 3 版）

**处置时间**：2026-10-01 19:38 – 19:46 ｜ **部署方案**：PC 端**同源部署**（相对路径，不写死任何开发 LAN IP）

### 12.1 问题与目标

原状态：PC 端生产配置与代码兜底写死 `http://192.168.1.4:8080`，而小程序端为 `192.168.2.219:8080`，两端不一致；更换网络环境时必有一端不可达。目标：PC 端彻底摆脱 LAN IP（相对路径 + 同源反向代理），小程序端保留唯一 LAN 配置入口（真机调试必需）。**Flask 保持 `0.0.0.0:8080`，CORS 与 `/static/upload` 均未改动。**

> 说明：**PC 开发环境此前已是目标形态**（`.env.development` 的 `VITE_API_BASE_URL=/api` + `vite.config.js` 的 `/api` `/static` 代理到 `127.0.0.1:8080`），本不需改动；本轮实际处理的是**生产配置与代码兜底值**。

### 12.2 实际修改（5 文件 / 11 行）

| # | 文件 | 行 | 改动前 | 改动后 |
|---|---|---|---|---|
| 1 | `management-web/.env.production` | 1 | `# 生产环境：固定后端地址（需求约定 API 基础地址）` | `# 生产环境：同源部署，API 与静态资源使用相对路径（由同源 Web Server 反向代理转发到 Flask:8080）` |
| 2 | `management-web/.env.production` | 2 | `VITE_API_BASE_URL=http://192.168.1.4:8080/api` | `VITE_API_BASE_URL=/api` |
| 3 | `management-web/.env.production` | 3 | `VITE_STATIC_BASE_URL=http://192.168.1.4:8080/static/upload/` | `VITE_STATIC_BASE_URL=/static/upload/` |
| 4 | `management-web/src/utils/config.js` | 6 | `import.meta.env.VITE_API_BASE_URL \\|\\| 'http://192.168.1.4:8080/api'` | `import.meta.env.VITE_API_BASE_URL \\|\\| '/api'` |
| 5 | `management-web/src/utils/config.js` | 9 | `import.meta.env.VITE_STATIC_BASE_URL \\|\\| 'http://192.168.1.4:8080/static/upload/'` | `import.meta.env.VITE_STATIC_BASE_URL \\|\\| '/static/upload/'` |
| 6 | `backend/config.py` | 41 | `_get("API_BASE_URL", "http://192.168.1.4:8080/api")` | `_get("API_BASE_URL", "/api")` |
| 7 | `backend/config.py` | 42 | `_get("STATIC_BASE_URL", "http://192.168.1.4:8080/static/upload/")` | `_get("STATIC_BASE_URL", "/static/upload/")` |
| 8-9 | `backend/.env` | 25-26 | LAN 绝对地址 | `/api`、`/static/upload/` |
| 10-11 | `backend/.env.example` | 29-30 | LAN 绝对地址 | `/api`、`/static/upload/` |

**未改动（严格按授权边界）**：`miniapp/` 全部文件（含 `miniapp/common/config.js`）、`management-web/.env.development`、`management-web/vite.config.js`、`management-web/src/api/request.js`、Flask HOST/PORT、CORS、数据库结构、`JWT_SECRET`、任何业务接口 / Vue 页面 / 鉴权逻辑。

> 影响面说明：`backend/config.py` 的 `API_BASE_URL` / `STATIC_BASE_URL` 当前仅用于「`/` 根路由回显」（`app.py:62`）与「管理员系统信息回显」（`admin_service.py:1273`）；`utils/upload.py::build_static_url()` 引用 `STATIC_BASE_URL` 但**全项目零调用（死代码）**。故改相对路径对业务功能**零影响**。

### 12.3 残留扫描（产品源码口径，排除 `docs/` 与 `*.log`）

| 范围 | `192.168.1.4` | `192.168.2.219` | `:5000` / `:5001` |
|---|---:|---:|---:|
| `management-web/`（含 `src`、`.env.*`） | **0** | 0 | **0** |
| `backend/` | **0** | 0 | **0** |
| `miniapp/`（**允许保留**） | 0 | 2（`config.js` L5/L8，为当前真实 LAN IP） | 0 |
| `management-web/dist/`（构建产物，65 个非二进制文件） | **0** | **0** | **0** |

**构建产物已注入相对路径**：`dist/assets/index-*.js` 内为 `const Fce="/api",Kce="/static/upload/"`；全库**无任何绝对 `http(s)://.../api` 残留**。

### 12.4 处置后回归

| 回归项 | 结果 |
|---|---|
| `backend_selfcheck.py` | **5/5 PASS**（126 条 `/api` 路由） |
| `miniapp_check.py` | **23/23 PASS** |
| `web_check.py` | **33/33 PASS** |
| `api_test.py` | **198/198 PASS** |
| `vite build`（production） | **PASS**（2287 modules / 22.24s / exit 0） |

> `web_check.py` 原 2 条断言写死了旧地址（`http://192.168.1.4:8080/api`），地址统一后必然 FAIL。已按**语义不变式**修正为「唯一来源 + `VITE_API_BASE_URL` + 相对 `/api` 兜底 + 不含硬编码 IP」。**属测试脚本口径修正，未改动任何产品代码。**

### 12.5 数据保护

| 项 | 结果 |
|---|---|
| 本轮临时数据新增 | **19 行**（2 用户 + 3 医生 + 2 教练 + 12 业务/绑定行） |
| 本轮临时数据清理 | **19 行**（白名单 id + 命名/手机号唯一标识 + 三重守卫） |
| **本轮临时数据残留** | **0** |
| 历届残留（30 行） | 原样保留（未授权，未动） |
| 产品源码非授权修改 | **0**（19:38 后产品工程 mtime 扫描：仅授权的 5 个配置文件） |
| 数据库结构修改 | **0**（无 DDL） |
| 小周数据（`user_id=13`） | **INTACT** |
| doctor002 绑定 | **INTACT**（`doctor_patient`: doctor_id=2 / user_id=13） |
| coach001 绑定 | **INTACT**（`coach_student`: coach_id=1 / user_id=13） |

> `admin_operation_log` 243 → 264（+21），系本轮测试触发审核动作的系统审计留痕；其来源未逐行核实，按「禁止清理无法确认来源的数据」原则**保留未动**。

### 12.6 判定

```
STORAGE_ITEM_01_API_ADDRESS = PASS
```

**同源部署落地要点（供正式部署参考）**：正式发布时由同源 Web Server / Nginx 反向代理 —— `/api` → `Flask:8080`、`/static` → `Flask:8080`；生产包使用相对路径，不再依赖任何固定 LAN IP。注意：直接以 `file://` 打开 `dist/index.html` 时 API 不可用属正常现象，正式生产包须由 HTTP Web Server 提供。

---

*报告第 1 版：2026-10-01 18:21 · 第 2 版（DEF-01 修复后复验）：2026-10-01 19:30 · 第 3 版（存量事项① 处置）：2026-10-01 19:46*"""

PAIRS = [(OLD3, NEW3), (OLD_S, NEW_S), (OLD_TAIL, SEC12)]


def main():
    apply = "--apply" in sys.argv
    txt = open(P, "rb").read().decode("utf-8")
    before = len(txt.encode("utf-8"))

    problems = []
    for i, (o, n) in enumerate(PAIRS, 1):
        c = txt.count(o)
        if c != 1:
            problems.append((i, c, o[:90]))
    if problems:
        print("ABORT: 锚点未全部命中（!=1），整个文件不改")
        for i, c, o in problems:
            print("   [X] #%d hits=%d : %s" % (i, c, o))
        return 1

    for o, n in PAIRS:
        txt = txt.replace(o, n, 1)

    if apply:
        tmp = P + ".tmp_patch"
        open(tmp, "wb").write(txt.encode("utf-8"))
        os.replace(tmp, P)

    after = len(txt.encode("utf-8"))
    print("MODE = %s ; 锚点 3/3 命中" % ("APPLY" if apply else "DRY-RUN"))
    print("bytes: %d -> %d  (delta %+d)" % (before, after, after - before))
    print("lines: %d -> %d" % (txt.count("\n") + 1, txt.count("\n") + 1))
    # 复核关键串
    for k in ["STORAGE_ITEM_01_API_ADDRESS = PASS", "## 十二、存量事项① 处置记录",
              "已处置**（2026-10-01 19:40", "第 3 版（存量事项① 处置）"]:
        print("   含 '%s' ? %s" % (k[:34], k in txt))
    return 0


if __name__ == "__main__":
    sys.exit(main())
