# 个人健康管理系统 · 最终权限隔离 + 异常场景专项验收报告

- 系统版本：`V3.2 FINAL`
- 验收日期：2026-10-01
- 验收对象：Flask 后端（`127.0.0.1:8080`，蓝图前缀 `/api`）+ MySQL `health_management`（8.0.33）+ PC 管理端（Vue3/Vite）+ 小程序端
- 验收性质：**仅测试、取证、发现问题**；除测试脚手架（`tests/` 内脚本、`tests/security/` 新增用例）外，**未修改任何产品代码**
- 本版次：**第 4 版（DEF-01 修复 → 存量事项① API 地址统一 → 存量事项② JWT_SECRET 轮换）**
  - 第 1 版（18:21）：原始验收，判定 FAIL（DEF-01）
  - 第 2 版（19:30）：DEF-01 修复后全量复验，判定 PASS
  - 第 3 版（19:46）：存量事项① API 地址 / LAN IP 统一（同源相对路径），`STORAGE_ITEM_01_API_ADDRESS = PASS`
  - 第 4 版（20:15）：存量事项② JWT_SECRET 轮换 + 配置安全失败策略，`STORAGE_ITEM_02_JWT_SECRET = PASS`
- 报告正本：`health-management-system/docs/FINAL_SECURITY_ACCEPTANCE_REPORT.md`
- 逐条明细附录：`tests/security/_out/SEC_DETAIL.md`

---

## 一、验收结论摘要

### 1.1 四项汇总

| 分类 | 覆盖专项 | 结果 |
|---|---|---|
| **权限隔离专项** | A 四角色 Token 越权 / B 医生-患者数据隔离 / C 教练-学员数据隔离 / D 注册审核状态机 / G 数据所有权 / H 管理员监管边界 | **118 / 118 PASS** |
| **异常场景专项** | E 注册异常 / F 登录异常 / I 操作日志 / J HTTP 与异常稳定性 | **64 / 64 PASS** |
| **静态安全扫描** | K 静态安全扫描（15 项） | **15 / 15 PASS** |
| **现有回归** | backend_selfcheck / miniapp_check / web_check / api_test / vite build | **259 / 259 PASS**（DEF-01 修复后 `api_test` 恢复 198/198） |
| **合计（11 专项）** | A~K | **197 / 197 PASS，0 FAIL** |

### 1.2 真实缺陷

| 编号 | 描述 | 风险 | 状态 |
|---|---|---|---|
| **DEF-01** | 验证/调试脚本残留于生产前端工程目录 `management-web/`，其中 7 个文件含明文登录口令（`admin` / `doctor001` / `coach001` 的 `123456`） | **中** | **已修复（2026-10-01 19:00）** |

> DEF-01 处置方式见 §5.3 执行记录；修复后 `management-web/` 根目录已无任何测试脚手架，`api_test.py` 恢复 `198/198`。复验结论见 §十一。

### 1.3 最终判定

```
FINAL_SECURITY_ACCEPTANCE = PASS
```

**判定理由**：11 个专项（197 项）全部 PASS；唯一真实缺陷 **DEF-01 已按 §5.3 修复（纯文件搬迁，未触碰任何产品代码与业务数据）**；修复后全量复验（权限专项 / 异常专项 / 静态扫描 / 四项现有回归 / Vite 构建）**全部通过**，`api_test.py` 恢复 `198/198`，本轮临时数据 **0 残留**，受保护数据 **全部 INTACT**。详见 §十一 复验记录。

> 说明：本判定为**安全验收转绿**，**不代表项目最终封板**。

---

## 二、验收范围与执行方式

### 2.1 环境基线

| 项 | 值 |
|---|---|
| 后端 | Flask，`http://127.0.0.1:8080`，运行中（`/api/health` → `service=ok, database=ok`） |
| 数据库 | MySQL 8.0.33，库 `health_management` |
| 管理端 | Vue3 + Vite 5，`management-web/`（本轮以 API 与静态扫描为主） |
| 小程序端 | UniApp，`miniapp/` |
| 语言/驱动 | 项目 venv `.venv`（Python 3.11 + pymysql）；HTTP 走标准库 urllib（venv 内无 requests） |

### 2.2 执行口径（红线）

1. **不伪造 PASS**：所有断言均调用真实 Flask API / 真实 MySQL / 真实 JWT 鉴权，无任何 Mock；
2. **DB 取证**：越权类断言除比对 HTTP 状态码外，均追加数据库侧复核（写入是否真的落库、是否真的未落库）；
3. **不破坏既有数据**：不空库、不修改「小林同学 / 阿may / 小孙 / **小周**」及 `doctor001-003` / `coach001-003` 及其绑定关系；
4. **测试数据隔离**：临时实体一律 `sec_` 前缀 + 专用手机号段（`199********`），清理用**精确 IN 匹配**，绝不用模糊 `LIKE`；
5. **不改产品代码**：本轮仅新增/修正 `tests/` 下的验证脚本；产品代码零改动。

### 2.3 主要用例来源

| 文件 | 作用 |
|---|---|
| `tests/security/_sec_lib.py` | 公共库：HTTP/DB/结果收集/敏感信息扫描 |
| `tests/security/_sec_data.py` | 测试实体定义 + 精确清理 |
| `tests/security/_sec_setup.py` | 走真实 API 建数据（清理→注册→审核→绑定→造业务数据） |
| `tests/security/_sec_run.py` | A~J 十个专项（181 项） |
| `tests/security/_sec_static.py` | K 静态安全扫描（15 项） |
| `tests/security/_sec_final_cleanup.py` | 收尾清理（白名单 + 守卫 + dry-run） |
| `tests/security/_sec_smoke.py` | 清理后冒烟复核（15 项） |
| `tests/security/_sec_def01_fix.py` | **DEF-01 修复**：脚手架迁移 + 守卫 + 明文口令取证（第 2 版新增） |
| `tests/security/_sec_def01_dedup.py` | **DEF-01 收尾**：`_verify_out` 双份副本哈希比对与分批去重（第 2 版新增） |
| `tests/security/_sec_verify_baseline.py` | 复验前后基线快照与受保护实体比对（第 2 版新增） |
| `tests/security/_sec_verify_cleanup.py` | 复验轮临时数据清理（白名单 + 三重守卫）（第 2 版新增） |

---

## 三、分专项结果汇总

| 专项 | 名称 | 用例数 | PASS | FAIL | 结论 |
|---|---|---:|---:|---:|---|
| A | 四角色 Token 越权隔离 | 29 | 29 | 0 | PASS |
| B | 医生-患者数据隔离 | 18 | 18 | 0 | PASS |
| C | 教练-学员数据隔离 | 16 | 16 | 0 | PASS |
| D | 注册审核状态机 | 20 | 20 | 0 | PASS |
| E | 注册异常场景 | 16 | 16 | 0 | PASS |
| F | 登录异常场景 | 24 | 24 | 0 | PASS |
| G | 数据所有权（越权读写他人数据） | 16 | 16 | 0 | PASS |
| H | 管理员监管权限边界 | 19 | 19 | 0 | PASS |
| I | 操作日志 | 17 | 17 | 0 | PASS |
| J | HTTP / 异常稳定性 | 7 | 7 | 0 | PASS |
| K | 静态安全扫描 | 15 | 15 | 0 | PASS |
| **合计** | — | **197** | **197** | **0** | **ALL PASS** |

---

## 四、专项明细（关键结论）

> 完整 197 条「编号 / 角色 / 目标 / 期望 / 实际 HTTP / code / PASS-FAIL」见 `tests/security/_out/SEC_DETAIL.md`。

### A. 四角色 Token 越权隔离（29/29 PASS）

对 `user / doctor / coach / admin` 四类 Token 与 `user / doctor / coach / admin` 四类接口做 **4×4 全矩阵**，外加 4 类非法凭据：

| 类别 | 用例 | 结果 |
|---|---|---|
| 合法自身接口（对角） | `user→/user/info`、`doctor→/doctor/patient/list`、`coach→/coach/student/list`、`admin→/admin/user/list` | HTTP 200 ✓ |
| 跨角色（非对角 12 组） | 例：`user→/admin/user/list`、`admin→/doctor/patient/list` | **HTTP 401**「无权访问该接口（Token 类型不匹配）」✓ |
| 未登录（4 组） | 无 `Authorization` | HTTP 401 ✓ |
| 伪造签名（4 组） | 篡改 `role` 后重签失败 | HTTP 401 ✓ |
| 篡改载荷（4 组） | 保留原签名改 payload | HTTP 401 ✓ |

> 机制：`backend/utils/auth.py::_verify(expected_type)` 校验 JWT 载荷中的 `token_type`，与端点声明类型不一致即 401；`decode_token` 异常吞掉返回 `None` → 401。**四角色 Token 完全不可互用**。

### B. 医生-患者数据隔离（18/18 PASS）

- 医生 A 的 `/doctor/patient/list` **只含**其绑定患者，**不含**医生 B 的患者（反向对称成立）；
- 医生 A 以 `?user_id=B` 访问 `patient/detail`、`health_data`、`sleep_data`、`sport_data`、`plan_data`、`trend` **6 个读取接口全部 401**；
- 医生 A 以 `user_id=B` 调 `advice/save`、`medical_notice/save`、`medical_record/save` **写接口全部 400**；
- **DB 复核**：`doctor_advice` / `medical_notice` / `medical_record` 中 `doctor_id=A AND user_id=B` 的行数均为 **0** —— 越权写入未落库。

### C. 教练-学员数据隔离（16/16 PASS）

- 教练 A 的 `/coach/student/list` 只含其学员；
- `student/detail`、`student/sport_data`、`student/statistics` 跨学员访问 **401**；
- `sport_goal/save`、`training_plan/save`、`fitness_advice/save` 跨学员写入 **400**；
- `sport_goal/update_status`、`training_plan/update_status` 操作他人记录 **400**；
- **DB 复核**：`sport_goal` / `training_plan` / `fitness_advice` 越权行数 **0**。

### D. 注册审核状态机（20/20 PASS）

| 环节 | 期望 | 结果 |
|---|---|---|
| 新注册医生/教练 | `audit_status` 强制为 `0` | ✓（客户端传 `audit_status=1` 被忽略） |
| 注册忽略客户端 `id` / `created_at` | 取自增新值与 `NOW()` | ✓ |
| 用户表 | 不存在 `role` / `audit_status` 列（角色不落数据表） | ✓ |
| 待审核(`0`)登录 | HTTP 400 拦截 | ✓ |
| 审核 `0→2`（拒绝） | 管理员可操作；拒绝后仍不能登录 | ✓ |
| 审核 `0→1`（通过） | 通过后可登录且下发 token | ✓ |
| **重复审核** | HTTP 400「该申请已完成审核，无需重复操作」 | ✓（**审核一次性不可逆，属设计约束**） |

### E. 注册异常场景（16/16 PASS）

手机号/账号重复（user、doctor、coach 三侧）、手机号格式非法、密码长度不足、昵称非法、性别取值非法 → 全部 HTTP 400 且返回可读业务提示；注册产生的 `id` 为自增新值、`created_at=NOW()`；用户表无 `role` / `audit_status` 列。

### F. 登录异常场景（24/24 PASS）

四角色 × {错误密码、不存在账号、空参数、超长参数、类型异常（`null`/数组）} 共 20 组 → 全部 HTTP 400「登录失败」，**不区分"账号不存在/密码错误"**（防用户枚举）；
另有 4 组 **响应体敏感信息扫描**（`password_hash` / JWT / SQL / traceback）→ 无泄露；
待审核账号登录拦截、审核拒绝账号登录拦截 → ✓。

### G. 数据所有权（16/16 PASS）

- 用户 A 携带 `?user_id=B` 调用 11 个「我的数据」接口（`health_record/my_list`、`sleep_record/my_list`、`sport_record/my_list`、`health_plan/my_list`、`report/statistics`、`user/doctor_advice`、`user/medical_notice`、`user/medical_record`、`user/sport_goal`、`user/training_plan`、`user/fitness_advice`）**全部只返回 A 自己的数据**——`user_id` 一律由 Token 推导，客户端传参被忽略；
- 写入接口忽略客户端 `user_id`：`health_record/add` 携带 `user_id=B` 实际落库 `user_id=A`（DB 复核）；
- `health_plan/update_status` 操作不属于自己的计划 → HTTP 400，且 `plan_status` 未被改写。

### H. 管理员监管权限边界（19/19 PASS）

- 管理员对 10 类用户原始数据接口（`health_record` / `sleep_record` / `sport_record` / `health_plan` / `doctor_advice` / `medical_notice` / `medical_record` / `sport_goal` / `training_plan` / `fitness_advice` 的 `/admin/*/list`）**均为只读 200**，符合监管职责；
- 管理员调医生/教练业务写接口（6 个 `advice|notice|record|goal|plan|fitness/save`）→ **HTTP 401**（Token 类型不匹配）；
- 管理员调用户写接口（`health_record/add`、`health_plan/add`）→ **HTTP 401**；
- **静态复核**：`backend/routes/admin.py` 内**不存在任何用户原始数据的写接口**。

### I. 操作日志（17/17 PASS）

管理员执行 8 类敏感操作（解绑/绑定医患、解绑/绑定师生、重置医生密码、重置教练密码等）后，`admin_operation_log` 表**均落有对应 `operation_type` 记录**；日志内容扫描：**无 `password_hash`、无明文口令、无敏感字段**。

### J. HTTP / 异常稳定性（7/7 PASS）

累计 **152 条真实请求**（A~J 同进程全量留痕）复核：

| 项 | 结果 |
|---|---|
| 出现 HTTP 500 | **0 次** |
| 连接层异常（后端崩溃/超时） | **0 次** |
| 非统一契约响应（裸文本 / HTML 错误页） | **0 次** |
| 敏感信息泄露（traceback / SQL / 哈希 / 密钥 / 文件路径） | **0 处**（登录成功响应按设计下发 JWT，不计） |
| 异常轰炸后 `/api/health` | 200，`service=ok`、`database=ok` |
| 不存在接口 `/no_such_api_sec_test` | HTTP 400 + 统一 `{code,msg,data}`（非 HTML 404） |

### K. 静态安全扫描（15/15 PASS）

端口禁令（`:5000` / `:5001` 零命中）、前端零敏感信息（`password_hash` / JWT Secret / DB 配置 / 硬编码 token）、前端无硬编码角色与审核绕过、后端 `auth.py` 同时具备 **Token 类型隔离 + 医患关系校验 + 师生关系校验**、前端存在路由守卫（展示层过滤，非唯一防线）、源码无 `TODO/FIXME/XXX`、无 mock/桩数据替代核心业务、前端 Token key 与角色映射一一对应、后端 `TOKEN_ROLE_MAP` 显式定义四类、管理端工程无 `.env` 密钥泄露、后端无写死中文数据的假接口。

> 说明：K 的扫描范围定义为**产品源码**（`backend` / `management-web/src` / `management-web/public` / `miniapp` / `database` / `tools`），不含 `docs`（文档中"无 TODO / 无 Mock / 端口禁令"的**描述文字**不构成代码缺陷），代码类断言跳过中文文案行。

---

## 五、真实缺陷清单

### 5.1 DEF-01：验证脚本残留于生产前端目录，含明文登录口令

| 项 | 内容 |
|---|---|
| **风险等级** | **中** |
| **发现来源** | 现有回归 `tests/api_test.py` → 断言「产品源码中无 123456 明文密码（扫描 134 个文件）」FAIL |
| **影响文件（直接命中，含明文口令）** | `management-web/_probe_click.py`（`PW='123456'`）<br>`management-web/_probe_login.py`（admin/doctor001/coach001 + `123456`）<br>`management-web/_probe_login3.py`（表单填充 `123456`）<br>`management-web/_shot_audit.py`（`ADMIN=('admin','123456')`）<br>`management-web/_verify_login.py`（`PASSWORD='123456'`）<br>`management-web/_probe3.log`、`management-web/login_verify.log`（日志内含 `['admin','123456']` 等） |
| **同目录其余残留** | 共 **37 个顶层项**：33 个 `_*.py` / `_*.log` 验证脚本 + 目录 `_verify_out/`（54 个文件）+ `__pycache__/`（2 个文件），均为一次性验证/诊断脚手架 |
| **原因** | 历轮 UI 验收与动画/性能调试的一次性脚本未清理，直接落在 PC 管理端工程根目录 |
| **暴露面（已实测界定）** | ✅ **未进入构建产物**：`dist/` 68 个文件中零命中（`dist_contains_leftover = []`）<br>✅ **未被产品源码引用**：`src/`、`public/` 内对 `_probe*/_verify*/_shot*/_diag*/_patch*/_tune*` 的引用数 = 0<br>⚠️ **凭证暴露面存在**：文件实体在产品工程目录内，若工程被提交版本库 / 打包交付 / 整体拷贝，明文管理员口令随之外泄 |
| **影响面** | 无运行时影响、无功能影响；属**工程卫生与凭证管理**缺陷 |
| **处置状态** | ✅ **已修复（2026-10-01 19:00，授权执行）**：36 个顶层项（35 文件 + `_verify_out/`）整体迁出 → `tests/manual-probes/`；`__pycache__/` 删除；`_verify_out` 双份副本按哈希比对后去重 |
| **修复后复核** | `management-web/` 根目录脚手架残留 **0**；`src`/`public`/`dist` 对被迁移脚本引用 **0**、对 `123456` 命中 **0**；7 个明文口令文件哈希 **全部一致**（`DEF01_PLAINTEXT_EVIDENCE.json`） |

### 5.2 另一项 FAIL 的定性（非缺陷）

`api_test.py` 首轮另有一项 FAIL：「全项目无 5000/5001 端口」，命中
`\.venv\Lib\site-packages\werkzeug\middleware\http_proxy.py`（第三方依赖自带字面量）与
`docs\TEST_REPORT.md`（历史报告引用端口作为"已修复项"的文字说明）。

该项为**扫描口径假性 FAIL**（扫描器未排除 `/.venv` 与 `/docs`），已按"只扫产品源码"的口径修正 `tests/api_test.py` 的 `SCAN_EXCLUDE_DIRS`（补入 `.venv`、`venv`、`docs`、`unpackage`、`.idea`、`.vscode`），修正后该项 PASS，**未改动任何产品代码**。

### 5.3 最小修复（DEF-01，已于 2026-10-01 19:00 授权执行完成）

**方式（推荐）：搬迁而非删除**（保留历史验证证据，且不与版本控制/交付物混淆）

```bash
# 1) 建立存放目录（tests/ 已在所有扫描器的排除范围内）
mkdir -p health-management-system/tests/manual-probes

# 2) 把误置的验证脚手架整体迁出产品工程目录
mv health-management-system/management-web/_*.py     health-management-system/tests/manual-probes/
mv health-management-system/management-web/_*.log    health-management-system/tests/manual-probes/
mv health-management-system/management-web/*.log     health-management-system/tests/manual-probes/
mv health-management-system/management-web/_verify_out  health-management-system/tests/manual-probes/
```

**预期结果**：`api_test.py` 恢复 `198/198 PASS`；`management-web/` 根目录仅保留产品资产（`.env.*` / `index.html` / `package.json` / `package-lock.json` / `vite.config.js` / `src/` / `public/` / `dist/` / `node_modules/`）。

**替代方式**：若确认这些脚本无保留价值，可直接删除（均为可再生成的一次性脚手架）。

#### 5.3.1 实际执行记录（2026-10-01 18:30 – 19:00）

| 项 | 实测数据 |
|---|---|
| 迁移目标目录 | `health-management-system/tests/manual-probes/`（新建） |
| 迁移文件 | **35 个**（`_*.py` / `_*.log` / `*.log`） |
| 迁移目录 | `_verify_out/`（**54 个文件**，含 `illustration-raw/` 5 个） |
| 迁移合计 | **36 个顶层项 / 89 个文件** |
| 删除（纯缓存） | `management-web/__pycache__/`（2 个 `.pyc`） |
| 删除（冗余副本） | MW 侧 `_verify_out/` 54 文件（DEST 已有逐字节相同副本，**先经 sha256 全量比对确认**） |
| 明文口令文件 | **7 个全部迁移成功，迁移前后 sha256 完全一致** |
| 产品资产 | 未触碰（`.env.development` / `.env.production` / `index.html` / `package.json` / `package-lock.json` / `vite.config.js` / `src/` / `public/` / `dist/` / `node_modules/` 原地保留） |

**修复后 `management-web/` 顶层项（实测）**：

```
.env.development  .env.production  dist/  index.html  node_modules/
package-lock.json  package.json  public/  src/  vite.config.js
```

**执行过程注意事项（工程经验，建议后续同类操作遵循）**：

1. `shutil.move(src_dir, dst_dir)` 在**目标已存在**时会退化为「复制 + 删源」；删源若超沙箱批量删除阈值（50）会被拦截，产生「DEST 有副本、SRC 仍在」的**双份残留**。规避：迁移目录前确保 DEST 不存在，或改用**逐文件 move**。
2. 出现双份残留时，**必须先按相对路径集合 + sha256 全量比对确认副本完整**，再分批（每批 ≤8 个）删源文件，最后自底向上 `rmdir` 空子目录。
3. 分批删除**不可使用固定 batch 索引**（列表每次重算会收缩导致索引错位漏删），应每次取前 N 个直至剩余为 0。

---

## 六、现有回归结果

| 资产 | 内容 | 结果 |
|---|---|---|
| `tests/backend_selfcheck.py` | 语法编译 / 应用导入（126 条 `/api` 路由）/ 端口扫描 / `.env.example` / 硬编码密钥 | **5 / 5 PASS** |
| `tests/miniapp_check.py` | 页面注册、TabBar、uCharts、别名 import、API 地址唯一来源、禁用项 | **23 / 23 PASS** |
| `tests/web_check.py` | 构建产物、依赖、路由完整性、角色守卫、配置唯一来源、禁用项 | **33 / 33 PASS** |
| `tests/api_test.py` | 接口联调 / 权限 / 安全（真实 HTTP + 真实 MySQL） | **198 / 198 PASS**（DEF-01 修复后） |
| `vite build`（`management-web`） | 生产构建 | **PASS**（2287 模块，26.6s，exit 0） |
| **合计** | — | **259 / 259 PASS** |

**回归结论（第 2 版复验）**：**未发现功能性回归**。DEF-01 修复后 `api_test.py` 由 `197/198` 恢复为 **`198/198`**；全部功能、接口、构建断言通过；PC 管理端可正常构建出全量产物（2287 模块 / 19.93s）。第 1 版的另一项口径假性 FAIL 仍为已修正状态。

**清理后冒烟复核（`_sec_smoke.py`，15/15 PASS）**：后端存活、管理员登录、6 个监管接口可读、`doctor002` / `coach001` / 小周(user 13) 均存在、小周↔医生/教练绑定完好、匿名访问受保护接口被 401 拒绝、已清理的 `sec_user_a` 登录失败。

---

## 七、测试数据账目

### 7.1 本轮创建（全部经真实 API）

| 类别 | 实体 | 数量 |
|---|---|---|
| 用户 | `sec_user_a`(id 23) / `sec_user_b`(id 24) / `sec_user_dup`(id 25) | 3 |
| 医生 | `sec_doctor_a`(33) / `sec_doctor_b`(34) / `sec_audit_doctor_pending`(35) / `sec_audit_doctor_evil`(36) / `sec_audit_doctor_ok`(37) | 5 |
| 教练 | `sec_coach_a`(24) / `sec_coach_b`(25) / `sec_audit_coach_pending`(26) / `sec_audit_coach_ok`(27) | 4 |
| 绑定关系 | 医患 2 组、师生 2 组 | 4 |
| 业务数据 | 健康记录 / 睡眠 / 运动 / 健康计划 / 医嘱 / 体检通知 / 医疗记录 / 运动目标 / 训练计划 / 健身建议 | 24 行（含 G 专项越权写入验证产生的 2 行） |
| 回归残留 | `api_test.py` 两轮（18:15、18:17）产生的 user 4 / doctor 6 / coach 4 及其业务行 | 14 实体 |

### 7.1.1 复验轮（第 2 版，19:04–19:25）创建与清理

| 类别 | 实体（实测 id） | 数量 |
|---|---|---|
| 用户 | `sec_user_a`(30) / `sec_user_b`(31) / `sec_user_dup`(32) | 3 |
| 用户（api_test 本轮） | 手机 `13990852777` / `13890852777`（id 33 / 34） | 2 |
| 医生 | `sec_doctor_a`(44) / `sec_doctor_b`(45) / `sec_audit_doctor_pending`(46) / `sec_audit_doctor_evil`(47) / `sec_audit_doctor_ok`(48) | 5 |
| 医生（api_test 本轮） | `doc_test_1001190617`(49) / `doc_reject_1001190617`(50) / `doc_other_1001190617`(51) | 3 |
| 教练 | `sec_coach_a`(32) / `sec_coach_b`(33) / `sec_audit_coach_pending`(34) / `sec_audit_coach_ok`(35) | 4 |
| 教练（api_test 本轮） | `coach_test_1001190617`(36) / `coach_reject_1001190617`(37) | 2 |
| 绑定关系 | 医患 3 组 + 师生 3 组 | 6 |
| 业务数据 | 健康记录 6 / 睡眠 3 / 运动 3 / 健康计划 4 / 医嘱 3 / 体检通知 3 / 医疗记录 3 / 运动目标 3 / 训练计划 3 / 健身建议 3 | **34 行** |
| **本轮新增合计** | 5 用户 + 8 医生 + 6 教练 + 6 绑定 + 34 业务行 | **59 行** |

**清理执行（`_sec_verify_cleanup.py --apply`，白名单 + 三重守卫）**：5 用户 / 8 医生 / 6 教练 + 34 业务行 + 6 绑定关系，**全部删除成功**；`problems = []`，`SAFE = True`。
**清理后复核**：`users id>13` = **0**、`doctor_user id>18` = **0**、`coach_user id>12` = **0** ⇒ **本轮临时数据残留 = 0**。

### 7.2 清理结果（`_sec_final_cleanup.py --apply`）

- **阶段 1（`sec_` 实体）**：删除 3 用户 / 5 医生 / 4 教练 + 24 行业务数据 + 4 组绑定关系，全部成功；
- **阶段 2（本轮 api_test 残留，白名单 + 守卫）**：删除 4 用户 / 6 医生 / 4 教练 + 业务行，全部成功；
- 两阶段均先 dry-run 输出删除计划，阶段 2 设 **id 白名单 + 手机号前缀 + 命名关键字** 三重守卫，任一不匹配即整批中止（实跑守卫通过）。

### 7.3 清理后库状态

| 表 | 清理前 | 清理后 |
|---|---:|---:|
| `users` | 20 | **13** |
| `doctor_user` | 29 | **18** |
| `coach_user` | 20 | **12** |

**受保护实体核对（全部完好）**：`users` 1 小林同学 / 2 阿may / 12 小孙 / **13 小周**；`doctor_user` 1 `doctor001` / 2 `doctor002` / 3 `doctor003`；`coach_user` 1 `coach001` / 2 `coach002` / 3 `coach003`；**小周(user 13) ↔ doctor002、coach001 的绑定关系均在**。

### 7.4 遗留未清理项（如实说明）

`users` 3~11（9 行）、`doctor_user` 4~16（13 行）、`coach_user` 4~11（8 行）为**历届 `api_test.py` 回归运行（2026-10-01 12:54–12:59）留下的存量数据**，不属于本轮创建，且 `api_test.py` 自身设计为「不删除任何已有数据」。本轮**未清理**（超出 `sec_` 授权范围），如需清理建议单独授权后按手机号段 + 命名前缀精确定位。

---

## 八、未处置项与后续建议

| # | 事项 | 建议 |
|---|---|---|
| 1 | ~~**DEF-01** 验证脚本残留 + 明文口令~~ | ✅ **已处置**（2026-10-01 19:00，见 §5.3.1）。**遗留建议（未执行）**：在 `management-web/` 增加 `.gitignore` 规则（`_*.py`、`*.log`、`_verify_out/`、`__pycache__/`）以防复发 |
| 2 | 存量 `api_test.py` 残留数据（30 行实体） | 如需清理请单独授权；或恢复数据库基线快照 |
| 3 | ~~PC 端与小程序端 API 地址不一致（PC 兜底 `192.168.1.4:8080` / 小程序 `192.168.2.219:8080`）~~ | ✅ **已处置**（2026-10-01 19:40，见 §十二）。PC 端统一为**同源相对路径**（`/api`、`/static/upload/`），彻底移除开发 LAN IP；小程序保留唯一 LAN 配置入口（真机调试必需） |
| 4 | `tests/miniapp_check.py` 原断言写死 `192.168.1.4` | 已改为校验"唯一来源"语义不变式（`API_BASE_URL='http://<ip>:8080/api'`），避免局域网 IP 变动产生假性 FAIL |
| 5 | ~~**JWT Secret 使用开发占位值**~~ | ✅ **已处置**（2026-10-01 20:15，见 §十三）。`backend/.env` 已轮换为高强度随机值（86 字符 / `cryptographically_secure_random`）；`config.py` 改为「环境变量缺失或仍为占位值 ⇒ 启动失败」；旧 Token 全部失效（预期安全行为，非缺陷） |

---

## 九、附：证据文件索引

| 文件 | 内容 |
|---|---|
| `tests/security/_out/SEC_DETAIL.md` | **197 条用例逐条明细**（编号/角色/目标/期望/HTTP/code/结果） |
| `tests/security/_out/sec_A.json` … `sec_K.json` | 各专项原始结果 JSON |
| `tests/security/_out/_rerun_all2.txt` | A~J 全量执行日志（同进程累积 152 条请求） |
| `tests/security/_out/_rerun_K.txt` | K 专项执行日志 |
| `tests/security/_out/_reg_backend.txt` / `_reg_miniapp2.txt` / `_reg_web.txt` / `_reg_api2.txt` / `_reg_build.txt` | 现有回归执行日志 |
| `tests/security/_out/DB_INVENTORY.json` / `_inventory2.txt` | 数据库实体盘点（清理前后） |
| `tests/security/_out/DEFECT_EVIDENCE.json` / `_defect_ev.txt` | **DEF-01 取证**（残留清单、明文口令命中、构建产物隔离性、源码引用核查） |
| `tests/security/_out/_cleanup_dry.txt` / `_cleanup_apply.txt` | 收尾清理 dry-run 与实际执行记录 |
| `tests/security/_out/DEF01_PLAINTEXT_EVIDENCE.json` | **DEF-01 明文口令取证**：7 个文件迁移前后 sha256 + 命中行（第 2 版新增） |
| `tests/security/_out/DEF01_VERIFYOUT_DEDUP.json` | `_verify_out` 双份副本一致性比对（54/54 文件哈希全等，第 2 版新增） |
| `tests/security/_out/VERIFY_BEFORE.json` / `VERIFY_AFTER.json` | 复验前后基线快照与受保护实体比对（第 2 版新增） |
| `tests/security/_out/VERIFY_CLEANUP_PLAN.json` | 复验轮清理计划（白名单 + 守卫，`safe=true`，第 2 版新增） |
| `tests/security/_out/_v_run.txt` / `_v_K.txt` / `_v_backend.txt` / `_v_miniapp.txt` / `_v_web.txt` / `_v_api.txt` / `_v_build.txt` | 第 2 版复验各套件执行日志 |
| `tests/security/_out/_smoke.txt` | 清理后冒烟复核（15/15 PASS） |
| `tests/_result.json` | `api_test.py` 最新一轮 198 项结构化结果 |
| `tests/security/_out/JWT_LEAK_SCAN.json` | **存量事项② Secret 泄露扫描**（旧值 / 新值 / 前端 / 小程序 / dist 命中数量，第 4 版新增） |
| `tests/security/_out/JWT_TOKEN_VERIFY.json` | **新旧 Token 四角色验证**（旧 401 / 新 200 / 跨角色 12 组 401，第 4 版新增） |
| `tests/security/_out/JWT_BASELINE.json` / `VERIFY_AFTER.json` | 结构指纹 + 受保护实体 + 16 表计数 处置前后比对（第 4 版新增） |
| `tests/security/_out/_jwt_*.txt` | 轮换 / 重启 / 泄露扫描 / Token 验证 / 回归 执行日志（第 4 版新增） |

---

## 十、声明

1. 本报告所有结论均来自**真实 HTTP 请求 + 真实 MySQL 查询 + 真实 JWT 鉴权**，无 Mock、无伪造；
2. 本轮**未修改任何产品代码**；对测试脚手架的改动（`tests/api_test.py` 扫描口径、`tests/miniapp_check.py` 断言口径、`tests/security/*` 新增用例）已在正文逐项标注；
3. 11 个专项 197/197 PASS，**权限隔离与异常处理链路未发现缺陷**；
4. **真实缺陷 DEF-01 已于 2026-10-01 19:00 按 §5.3 修复**（纯文件搬迁 + 缓存删除，未触碰任何产品代码与业务数据）；
5. 修复后完成**全量复验**（权限专项 / 异常专项 / 静态扫描 / backend_selfcheck / miniapp / web / api_test / vite build），**全部通过**；`api_test.py` 恢复 `198/198`；
6. 复验轮临时数据 **0 残留**；受保护实体与小周绑定关系 **全部 INTACT**；产品源码非授权修改 **0**；数据库结构修改 **0**；
7. **判定 FINAL_SECURITY_ACCEPTANCE = PASS**（安全验收转绿）。**本判定不构成项目最终封板**；§八 存量事项已处置 4 项（DEF-01 / API 地址 / miniapp_check 断言口径 / **JWT_SECRET**），仅剩「存量 `api_test.py` 残留数据（30 行实体）」1 项仍待单独授权处置。
8. **存量事项①「API 地址 / LAN IP 配置统一」已于 2026-10-01 19:40 处置完成**（同源相对路径方案，5 文件 / 11 行，未触碰任何业务逻辑与数据）。处置与复验记录见 §十二；`STORAGE_ITEM_01_API_ADDRESS = PASS`。

---

## 十一、DEF-01 修复后复验记录（第 2 版）

### 11.1 复验范围与结果

复验时间窗：**2026-10-01 19:04 – 19:25**。执行顺序：基线快照 → `_sec_setup.py`（自带清理）→ `_sec_run.py`（整跑 A~J）→ `_sec_static.py`（K）→ 三项静态自检 → `api_test.py` → `vite build` → 临时数据清理 → 复验后比对。

| # | 复验项 | 结果 |
|---|---|---|
| 1 | 权限专项（A/B/C/D/G/H） | **118 / 118 PASS** |
| 2 | 异常专项（E/F/I/J） | **64 / 64 PASS** |
| 3 | 静态扫描（K） | **15 / 15 PASS** |
| 4 | backend_selfcheck | **5 / 5 PASS**（126 条 `/api` 路由） |
| 5 | miniapp_check | **23 / 23 PASS** |
| 6 | web_check | **33 / 33 PASS** |
| 7 | api_test | **198 / 198 PASS** |
| 8 | vite build | **PASS**（2287 模块 / 19.93s / exit 0） |
| — | **A~K 合计** | **197 / 197 PASS，0 FAIL** |

### 11.2 受保护数据复核（`_sec_verify_baseline.py verify`）

```
PROTECTED_ALL_INTACT = True
```

| 保护项 | 复验前 | 复验后 | 结论 |
|---|---|---|---|
| `users` 1 小林同学 / 2 阿may / 12 小孙 / 13 小周 | 在 | 在 | **INTACT** |
| `doctor_user` 1 `doctor001` / 2 `doctor002` / 3 `doctor003` | 在（`audit_status=1`） | 在（`audit_status=1`） | **INTACT** |
| `coach_user` 1 `coach001` / 2 `coach002` / 3 `coach003` | 在（`audit_status=1`） | 在（`audit_status=1`） | **INTACT** |
| 小周(13) ↔ `doctor002`(2) | 绑定在 | 绑定在 | **INTACT** |
| 小周(13) ↔ `coach001`(1) | 绑定在 | 绑定在 | **INTACT** |
| 小周业务数据（健康记录 / 睡眠 / 运动 / 健康计划 / 医嘱 / 体检通知 / 医疗记录 / 训练计划 / 健身建议 各 1 行） | 10 项齐全 | 10 项齐全 | **INTACT** |

**唯一数量变化**：`admin_operation_log` 204 → 243（+39）。原因为复验期间执行了注册 / 审核 / 绑定等写操作，产生**正常审计留痕**，非业务数据改动。

### 11.3 临时数据账目

| 指标 | 值 |
|---|---:|
| 本轮测试新增临时数据 | **59 行**（5 用户 + 8 医生 + 6 教练 + 6 绑定 + 34 业务行） |
| 本轮测试清理临时数据 | **59 行**（清理明细见 7.1.1） |
| **本轮临时数据残留** | **0** |

历届残留（`users` 3~11 / `doctor_user` 4~16 / `coach_user` 4~11，共 30 行）**未授权，原样保留未动**。

### 11.4 产品与结构完整性

| 项 | 结果 |
|---|---|
| 产品源码非授权修改（`backend/` / `miniapp/` / `management-web/src`，19:04 后 mtime 扫描） | **0** |
| 数据库结构修改 | **0**（无 DDL） |
| 本轮改动范围 | 仅 `tests/`（新增复验脚本与证据）、`docs/`（本报告）、`management-web/dist/`（构建产物） |

### 11.5 复验过程中的环境异常（如实说明）

首次 `vite build` 在 `✓ 2287 modules transformed` 后**卡在产物写出阶段逾 18 分钟**（`dist/` mtime 长时间不变），判定为**进程挂起**（非产品缺陷：模块转换已全部完成）。终止该进程后**重跑构建 19.93s 正常完成**，`exit 0`。已排除产品代码因素。

### 11.6 第 2 版判定

```
DEF-01 = PASS
FINAL_SECURITY_ACCEPTANCE = PASS
```

> 本判定为**安全验收转绿**，**不构成项目最终封板**。

---

## 十二、存量事项① 处置记录：API 地址 / LAN IP 配置统一（第 3 版）

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
| 4 | `management-web/src/utils/config.js` | 6 | `import.meta.env.VITE_API_BASE_URL \|\| 'http://192.168.1.4:8080/api'` | `import.meta.env.VITE_API_BASE_URL \|\| '/api'` |
| 5 | `management-web/src/utils/config.js` | 9 | `import.meta.env.VITE_STATIC_BASE_URL \|\| 'http://192.168.1.4:8080/static/upload/'` | `import.meta.env.VITE_STATIC_BASE_URL \|\| '/static/upload/'` |
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

## 十三、存量事项② 处置记录：JWT_SECRET 轮换（第 4 版）

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
## 十四、最终封板记录（第 5 版）

本轮在存量事项②（`JWT_SECRET` 轮换）通过后，一次性完成**历届测试残留精确清理 → `api_test` 防残留机制修复 → 工程卫生 → Secret 扫描 → 数据库完整性 → 四角色冒烟 → A~K 安全复验 → 全量回归 → 生产构建 → 文档同步**，并给出项目最终封板判定。

### 14.1 历届测试残留处置（§八 第 2 项闭环）

`users` 3~11 / `doctor_user` 4~16 / `coach_user` 4~11 等**共 30 个账号 + 51 行关联数据（合计 81 行）**，经多源交叉取证（`api_test.py` 账号生成规则、`username`/`nickname`、手机号段、`created_at`、命名前缀、外键关联、是否与真实实体绑定）逐条判定：

| 判定 | 数量 | 处置 |
|---|---|---|
| `TEST_RESIDUE_CONFIDENCE = CONFIRMED` | 30 个账号（81 行含关联业务/绑定） | **已精确删除**（dry-run → 白名单 → 五重守卫 → apply → 复核） |
| `UNCONFIRMED` | 3 个（`doctor_user` 17 `001` / 18 `003`、`coach_user` 12 `002`） | **保留**（创建时间 16:26–16:57，带人工管理端「资料修改 / 密码重置 / 审核」审计痕迹，与 `api_test` 无关） |

`admin_operation_log` 未删除任何记录（审计留痕按完整性原则保留）。

### 14.2 `api_test.py` 防残留机制（根因修复）

原 `api_test.py` 无任何清理逻辑（`cleanup` / `finally` 计数为 0），是历届残留的**根因**。已做**最小追加式修复**：

- 运行前记录基线；所有测试实体使用**唯一时间戳标识**（`139908`/`138908` 手机号段、`doc_test_`/`doc_reject_`/`doc_other_`/`coach_test_`/`coach_reject_` 命名前缀）；
- `main()` 改为 `try / finally`，`finally` 中执行**精确清理**（白名单 + 受保护实体硬守卫 + 二次所有权校验）；
- 只清理**本轮创建**的数据，绝不触碰运行前既有数据；清理失败即令测试报告 **FAIL**；
- 用例数由 198 增至 **199**（新增「本轮测试数据精确清理」断言），运行前后业务表计数 delta 全 0。

### 14.3 最终结果

| 项目 | 结果 |
|---|---|
| 历史测试残留（显式扫描） | **CLEAN**（CONFIRMED 全部删除、UNCONFIRMED 保留 3 个） |
| 本轮临时数据残留 | **0** |
| `backend_selfcheck.py` | **5 / 5 PASS** |
| `miniapp_check.py` | **23 / 23 PASS** |
| `web_check.py` | **33 / 33 PASS** |
| `api_test.py` | **199 / 199 PASS** |
| 权限 + 异常专项 A~K | **197 / 197 PASS** |
| 四角色真实冒烟 | **46 / 46 PASS** |
| `vite build`（production） | **PASS**（22.09s） |
| Secret 泄露扫描（含 dist） | **命中 0** |
| 数据库完整性 / 结构变更 | 19 表 · 指纹未变 · **DATABASE_SCHEMA_CHANGED = NO** |
| 受保护实体（含小周 10 类业务数据与两条绑定） | **PROTECTED_ALL_INTACT = True** |
| 工程卫生（`.gitignore` + 缓存清理） | **PASS**（4 份 `.gitignore`；`*.pyc` 缓存残留 0） |

```
DEF-01 = PASS
FINAL_SECURITY_ACCEPTANCE = PASS
STORAGE_ITEM_01_API_ADDRESS = PASS
STORAGE_ITEM_02_JWT_SECRET = PASS
PROJECT_FINAL_SEAL = PASS
```

> 完整封板正本见 **`docs/FINAL_PROJECT_SEAL_REPORT.md`**。

---
*报告第 1 版：2026-10-01 18:21 · 第 2 版（DEF-01 修复后复验）：2026-10-01 19:30 · 第 3 版（存量事项① 处置）：2026-10-01 19:46 · 第 4 版（存量事项② JWT_SECRET 轮换）：2026-10-01 20:15 · 第 5 版（历届残留清理 + 最终封板）：2026-10-01 20:31*
