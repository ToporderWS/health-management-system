# -*- coding: utf-8 -*-
"""存量事项② · 报告回写（锚点式，命中数必须 == 1，任一未命中则整批不改）。

注意：涉及旧 Secret 截断前缀的锚点一律用「正则」表达，避免脚本自身成为旧值残留载体。
"""
import io
import re
import sys

REPORT = (r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system'
          r'\docs\FINAL_SECURITY_ACCEPTANCE_REPORT.md')

SEC13 = '''## 十三、存量事项② 处置记录：JWT_SECRET 轮换（第 4 版）

**处置时间**：2026-10-01 20:00 – 20:15 ｜ **授权边界**：只处理 JWT_SECRET；不处理历届 30 行残留；不最终封板

### 13.1 处置前只读确认

| 项 | 结论 |
|---|---|
| `JWT_SECRET` 来源 | **仅经环境变量进入后端**：`backend/.env` → `config.py::_get("JWT_SECRET", ...)` → `utils/jwt_utils.py`（`HS256` 签发 / 校验） |
| 产品源码硬编码真实 Secret | **0**（轮换前 `config.py` 仅有通用占位默认值，非真实密钥） |
| 前端 / 小程序 | `management-web`、`miniapp` 内 `JWT_SECRET` 命中 **0** |

> 结论：无需「立即停止并报告」的中断条件，可继续处置。

### 13.2 实际修改（3 文件）

| # | 文件 | 改动 |
|---|---|---|
| 1 | `backend/.env` | `JWT_SECRET` 由开发占位值轮换为新随机值（`secrets.token_urlsafe(64)` ⇒ **86 字符**） |
| 2 | `backend/config.py` | **安全失败策略**：`JWT_SECRET` 必须由环境变量提供；**缺失或仍为占位值 ⇒ 启动阶段抛 `RuntimeError`**，不再回落代码内固定默认密钥（+7 行 / −1 行） |
| 3 | `backend/.env.example` | 仅保留安全占位符 `JWT_SECRET=CHANGE_ME_TO_A_STRONG_RANDOM_SECRET`，**不含任何真实值** |

> **未改动**：JWT 算法（`HS256`）、Token 载荷结构、`token_type`、`TOKEN_ROLE_MAP`、四角色鉴权规则、医患 / 师生关系校验、Token 有效期（72h）、密码哈希逻辑、Flask HOST/PORT、CORS、API 地址配置、数据库结构与业务数据、历届 30 行残留。
> **Secret 值管理**：本轮全程**未在任何回复 / 报告 / 日志 / JSON 证据 / 控制台输出中记录 Secret 本体**，仅记录长度与来源。

### 13.3 泄露扫描（只报命中数量，不记录 Secret 值）

| # | 检查项 | 命中 |
|---|---|---:|
| 1 | 旧 Secret 完整值（全项目，含 `backend/.env`） | **0** |
| 2 | 新 Secret 完整值（`backend/.env` 之外） | **0** |
| 3 | `management-web/` 内 `JWT_SECRET` 字样 | **0** |
| 4 | `miniapp/` 内 `JWT_SECRET` 字样 | **0** |
| 5 | `management-web/dist/`（构建产物）内 Secret / `JWT_SECRET` | **0** |
| 6 | `docs/` / `tests/` / `backend/`（除 `.env`）内新 Secret 完整值 | **0** |

### 13.4 新旧 Token 验证（四角色）

| 角色 | 旧 Token → 自身受保护接口 | 新登录 Token → 自身合法接口 |
|---|---|---|
| user | **401** | **200** |
| doctor | **401** | **200** |
| coach | **401** | **200** |
| admin | **401** | **200** |

**跨角色隔离**：新 Token 调其他角色接口 **12 / 12 返回 401**。

> 旧 Secret 签发的 Token 全部失效属**正确的安全行为**（非缺陷）；四角色需重新登录获取新 Token。**未保留旧 Secret、未实现双 Secret、未降低校验强度。**

### 13.5 处置后回归

| 回归项 | 结果 |
|---|---|
| `backend_selfcheck.py` | **5 / 5 PASS** |
| `miniapp_check.py` | **23 / 23 PASS** |
| `web_check.py` | **33 / 33 PASS** |
| `api_test.py` | **198 / 198 PASS** |
| 权限 + 异常专项（A~J） | **182 / 182 PASS**（其中 A「四角色 Token 越权隔离」**29 / 29**） |
| 静态安全扫描（K） | **15 / 15 PASS** |
| `vite build`（production） | **PASS**（exit 0，22.07s） |

### 13.6 数据保护

| 项 | 结果 |
|---|---|
| 本轮临时数据新增 | **59 行**（`sec_` 3 用户 + 5 医生 + 4 教练及其业务/绑定 40 行；`api_test` 2 用户 + 3 医生 + 2 教练及其业务/绑定 19 行） |
| 本轮临时数据清理 | **59 行全部清理**（`sec_` 沿用既有精确清理；`api_test` 新增「id 差集 + 命名/手机号正则 + 受保护实体」三重守卫脚本，任一不匹配整批中止） |
| **本轮临时数据残留** | **0** |
| 历届残留（30 行：`users` 3~11 / `doctor_user` 4~16 / `coach_user` 4~11） | **原样保留（未授权，未动）** |
| 小周数据（`user_id=13`，10 项业务数据） | **INTACT** |
| doctor002 绑定（`doctor_patient` doctor_id=2 / user_id=13） | **INTACT** |
| coach001 绑定（`coach_student` coach_id=1 / user_id=13） | **INTACT** |
| 数据库结构修改 | **0**（`information_schema.COLUMNS` 指纹 `e66d8cbd…`，139 列，处置前后一致） |
| 16 张业务表计数 | **delta 全 0** |

> `admin_operation_log` 264 → 303（**+39**），系本轮审核 / 绑定 / 解绑 / 密码重置等测试动作产生的**系统审计留痕**（非业务数据）；按审计完整性原则**保留未动**。
> 附带测试资产改进（非产品代码）：`tests/security/_sec_lib.py` **新增 3 行** —— 动态从 `backend/.env` 读取**当前** Secret 加入响应敏感模式（仅驻留内存、不落盘明文），使原写死旧值特征的响应泄露检测在轮换后依然有效。

### 13.7 判定

```
JWT_SECRET_ROTATED        = YES
JWT_SECRET_STRENGTH       = PASS
OLD_TOKEN_INVALIDATED     = PASS
NEW_TOKEN_VALIDATION      = PASS
SECRET_LEAK_SCAN          = PASS
STORAGE_ITEM_02_JWT_SECRET = PASS
```

> 存量事项③「历届 30 行测试残留」**本轮未处理**（超出本次授权边界）。本判定**不构成项目最终封板**。

---
'''

NEW_EVIDENCE = '''| `tests/security/_out/JWT_LEAK_SCAN.json` | **存量事项② Secret 泄露扫描**（旧值 / 新值 / 前端 / 小程序 / dist 命中数量，第 4 版新增） |
| `tests/security/_out/JWT_TOKEN_VERIFY.json` | **新旧 Token 四角色验证**（旧 401 / 新 200 / 跨角色 12 组 401，第 4 版新增） |
| `tests/security/_out/JWT_BASELINE.json` / `VERIFY_AFTER.json` | 结构指纹 + 受保护实体 + 16 表计数 处置前后比对（第 4 版新增） |
| `tests/security/_out/_jwt_*.txt` | 轮换 / 重启 / 泄露扫描 / Token 验证 / 回归 执行日志（第 4 版新增） |'''


def main():
    raw = open(REPORT, 'rb').read().decode('utf-8')
    eol = '\r\n' if '\r\n' in raw else '\n'
    text = raw

    edits = []

    def sub_literal(name, old, new):
        n = text.count(old)
        edits.append((name, n))
        if n != 1:
            return None
        return text.replace(old, new, 1)

    def sub_regex(name, pattern, new):
        rx = re.compile(pattern, re.M)
        found = rx.findall(text)
        edits.append((name, len(found)))
        if len(found) != 1:
            return None
        return rx.sub(lambda m: new, text, count=1)

    # 1) 头部版次
    t = sub_regex(
        'HEADER_VERSION',
        r'^- 本版次：.*$',
        ('- 本版次：**第 4 版（DEF-01 修复 → 存量事项① API 地址统一 → 存量事项② JWT_SECRET 轮换）**' + eol
         + '  - 第 1 版（18:21）：原始验收，判定 FAIL（DEF-01）' + eol
         + '  - 第 2 版（19:30）：DEF-01 修复后全量复验，判定 PASS' + eol
         + '  - 第 3 版（19:46）：存量事项① API 地址 / LAN IP 统一（同源相对路径），`STORAGE_ITEM_01_API_ADDRESS = PASS`' + eol
         + '  - 第 4 版（20:15）：存量事项② JWT_SECRET 轮换 + 配置安全失败策略，`STORAGE_ITEM_02_JWT_SECRET = PASS`'))
    if t is None:
        return fail(edits)
    text = t

    # 2) §八 第 5 行（旧 Secret 截断前缀所在行）—— 用正则，避免脚本自身残留该前缀
    t = sub_regex(
        'SECTION8_ITEM5',
        r'^\| 5 \| JWT Secret 使用开发占位值 \|.*$',
        ('| 5 | ~~**JWT Secret 使用开发占位值**~~ | ✅ **已处置**（2026-10-01 20:15，见 §十三）。'
         '`backend/.env` 已轮换为高强度随机值（86 字符 / `cryptographically_secure_random`）；'
         '`config.py` 改为「环境变量缺失或仍为占位值 ⇒ 启动失败」；'
         '旧 Token 全部失效（预期安全行为，非缺陷） |'))
    if t is None:
        return fail(edits)
    text = t

    # 3) §十 声明第 7 条
    t = sub_literal(
        'SECTION10_ITEM7',
        '7. **判定 FINAL_SECURITY_ACCEPTANCE = PASS**（安全验收转绿）。**本判定不构成项目最终封板**；'
        '§八 中「`JWT_SECRET` 占位值」「历届测试残留数据」2 项存量事项仍待单独授权处置。',
        '7. **判定 FINAL_SECURITY_ACCEPTANCE = PASS**（安全验收转绿）。**本判定不构成项目最终封板**；'
        '§八 存量事项已处置 4 项（DEF-01 / API 地址 / miniapp_check 断言口径 / **JWT_SECRET**），'
        '仅剩「存量 `api_test.py` 残留数据（30 行实体）」1 项仍待单独授权处置。')
    if t is None:
        return fail(edits)
    text = t

    # 4) §九 证据索引追加
    t = sub_literal(
        'SECTION9_EVIDENCE',
        '| `tests/_result.json` | `api_test.py` 最新一轮 198 项结构化结果 |',
        '| `tests/_result.json` | `api_test.py` 最新一轮 198 项结构化结果 |' + eol + NEW_EVIDENCE)
    if t is None:
        return fail(edits)
    text = t

    # 5) 追加 §十三 + footer
    t = sub_regex(
        'FOOTER_SECTION13',
        r'^\*报告第 1 版：.*$',
        SEC13.replace('\n', eol)
        + '*报告第 1 版：2026-10-01 18:21 · 第 2 版（DEF-01 修复后复验）：2026-10-01 19:30 · '
          '第 3 版（存量事项① 处置）：2026-10-01 19:46 · '
          '第 4 版（存量事项② JWT_SECRET 轮换）：2026-10-01 20:15*')
    if t is None:
        return fail(edits)
    text = t

    open(REPORT, 'wb').write(text.encode('utf-8'))
    print('== 锚点命中数 ==')
    for n, c in edits:
        print('   %-22s %d' % (n, c))
    print('REPORT_PATCHED = OK')
    return 0


def fail(edits):
    print('!! 锚点未全部命中（必须恰 == 1），整批中止，未写任何内容：')
    for n, c in edits:
        print('   %-22s %d' % (n, c))
    return 2


if __name__ == '__main__':
    sys.exit(main())
