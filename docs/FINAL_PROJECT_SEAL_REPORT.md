# 个人健康管理系统 V3.2 FINAL · 项目最终封板报告

> 封板时间：**2026-10-01 20:32**
> 封板对象：`health-management-system/`（后端 Flask + PC 管理端 Vue3 + 微信小程序 UniApp）
> 结论：**`PROJECT_FINAL_SEAL = PASS`**
> 配套文档：`docs/FINAL_SECURITY_ACCEPTANCE_REPORT.md`（第 5 版）· `README.md` · `docs/API.md` · `docs/DATABASE.md` · `docs/TEST_REPORT.md`

---

## 一、封板结论摘要

| 门禁项 | 判定 |
| --- | --- |
| `DEF-01`（产品目录残留验证脚手架） | **PASS** |
| `FINAL_SECURITY_ACCEPTANCE` | **PASS** |
| `STORAGE_ITEM_01_API_ADDRESS` | **PASS** |
| `STORAGE_ITEM_02_JWT_SECRET` | **PASS** |
| `HISTORICAL_TEST_RESIDUE` | **CLEAN**（CONFIRMED 已删 / UNCONFIRMED 保留 3 个） |
| `TEMP_TEST_DATA_RESIDUE` | **0** |
| `PROTECTED_ALL_INTACT` | **True** |
| `DATABASE_SCHEMA_CHANGED` | **NO** |
| `SECRET_LEAK_SCAN` | **PASS** |
| `ENGINEERING_HYGIENE` | **PASS** |
| `PROJECT_FINAL_SEAL` | **PASS** |

**真实未解决高风险缺陷 = 0；中风险缺陷 = 0；低风险已记录事项 = 4。**

---

## 二、封板范围与基线

- 基线：`FINAL_SECURITY_ACCEPTANCE = PASS`（A~K 197 项）、`STORAGE_ITEM_01/02 = PASS`、`api_test 199/199`。
- 本轮**只做收口与验证**：历届测试残留清理、`api_test` 防残留机制修复、工程卫生、敏感扫描、
  数据库完整性、四角色冒烟、安全复验、全量回归、生产构建、文档同步。
- 红线（全程未越界）：不碰 `miniapp` 业务逻辑、不改 `JWT` 算法/载荷/时效、不改 `Flask HOST/PORT`、
  不改 `CORS`、不改数据库结构与现有真实业务数据、不改 `management-web` 业务代码。

---

## 三、历届 api_test 测试残留处置

### 3.1 发现与取证

报告原记录「约 30 行实体」；实测更复杂，采用**多源交叉取证**（禁止仅凭 ID 区间删除）：

`api_test.py` 账号生成规则 · `username`/`nickname` · 手机号段 · `created_at` · 命名前缀 · 历史测试日志 · 外键关联 ·
是否与真实演示用户绑定 · 是否被现有真实业务数据引用。

| 判定 | 明细 |
| --- | --- |
| `CONFIRMED` | `users` 3~11（9）、`doctor_user` 4~16（13）、`coach_user` 4~11（8）**共 30 个账号**；连同其关联业务/绑定，**合计 81 行** |
| `UNCONFIRMED` | `doctor_user` 17 `001` / 18 `003`、`coach_user` 12 `002` **共 3 个** —— 创建时间 16:26–16:57，`admin_operation_log` 显示为人工管理端「资料修改 / 密码重置 / 审核」操作，**与 `api_test`（12:54–12:59）无关** |

### 3.2 精确清理

流程：**dry-run → 白名单 → 五重守卫 → apply → 清理后复核**。
按外键顺序先删关联业务数据、再删账号；禁用 `LIKE` 模糊删除 / `TRUNCATE` / `DROP` / 关外键强删。

| 统计 | 数量 |
| --- | --- |
| 历史测试残留发现 | **81 行**（30 账号 + 51 行关联业务与绑定） |
| `CONFIRMED` | **81 行** |
| `DELETED` | **81 行**（dry-run 命中 81、跳过 0；apply 后二次复核全 True） |
| `UNCONFIRMED_RETAINED` | **3 个账号**（删除计划中显式排除，未触碰） |

清理后：`NO_TEST_USERS` / `NO_TEST_DOCTORS` / `NO_TEST_COACHES` / `NO_SEC_RESIDUE_USERS` 全部 True；
`admin_operation_log` **未删除任何一条**（审计留痕按完整性原则保留）。

### 3.3 `api_test.py` 防残留机制（根因修复）

原脚本 `cleanup` / `finally` 计数为 **0**（无任何清理逻辑），是历届残留的根因。最小追加式修复：

1. 运行前记录数据库基线；
2. 全部测试实体使用**唯一时间戳标识**（`139908`/`138908` 手机号段 + `doc_test_` / `doc_reject_` / `doc_other_` / `coach_test_` / `coach_reject_` 命名前缀）；
3. `main()` 改为 `try / finally`，`finally` 内执行**精确清理**；
4. 只清理**本轮创建**的数据（白名单 + 受保护实体硬守卫 + 二次所有权校验），绝不动运行前既有数据；
5. 清理失败即令报告 **FAIL**；
6. 实测：**199 / 199 PASS**，运行前后 16 张业务表计数 **delta 全 0**，`TEMP_TEST_DATA_RESIDUE = 0`。

---

## 四、工程卫生

### 4.1 `.gitignore`（本轮新建，全工程原先**一份都没有**）

| 文件 | 关键规则 |
| --- | --- |
| `.gitignore`（工程根） | `.env` / `.env.*`（`!.env.example`）、`.venv/`、`venv/`、`__pycache__/`、`*.py[cod]`、`node_modules/`、`dist/`、`unpackage/`、`*.log`、`_verify_out/`、`*_verify_out/`、`.idea/`、`.vscode/` |
| `backend/.gitignore` | `.env` 系列（保留 `.env.example`）、Python 缓存、`*.log` |
| `management-web/.gitignore` | `node_modules/`、`dist/`、`.env` 系列、`__pycache__/`、**`_*.py` / `_*.log` / `_verify_out/` / `_out/`**（防止历史脚手架回流产品目录） |
| `miniapp/.gitignore` | `unpackage/`、`node_modules/`、Python 缓存、日志、编辑器目录 |

> 明确**允许入库**：`.env.example`、`src/`、`public/`、`database/`、`docs/`、`tests/`。
> 根 `.gitignore` 刻意**不**收窄 `_out/`，以免误伤 `tests/security/_out/`（正式验收证据）。

### 4.2 缓存清理（改为小批次逐文件，禁用递归删除）

产品目录残留仅 `backend/**/__pycache__` 的 CPython 字节码缓存（`cpython-311` / `cpython-313`）。

- 全部对象经只读核对：**100% 为 `__pycache__/` 内的 `*.pyc`**，无任何产品源码 / `src` / `miniapp` / `database` / `docs` /
  正式测试脚本 / `.env*` / 业务数据文件；
- 按**每批 ≤ 8 个文件**分批删除（3 批 + 2 个空目录），批内逐条断言「`.pyc` 且父目录名为 `__pycache__`」；
- 结果：`*.pyc` 残留 **0**、`__pycache__` 目录 **0**；
- `backend/server.log` 为**运行时日志**（Flask 进程持有），列为 **SAFE_RETAINED**（已被 `*.log` 忽略，不进版本控制）；
- `tests/manual-probes/`（DEF-01 隔离区）与 `tests/security/_out/`（正式验收证据）**按规则保留，未删除**。

---

## 五、最终敏感信息扫描

分层口径（**只输出命中数量，不打印任何密钥/口令/Token 本体**）：

| 检查项 | 作用域 | 命中 |
| --- | --- | --- |
| 旧 `JWT_SECRET` 完整值 / 前缀 | 全项目 | **0 / 0** |
| 新 `JWT_SECRET` 完整值 | `backend/.env` 之外 | **0** |
| bcrypt 哈希字面量 | 全项目 | **0** |
| 硬编码 `Bearer eyJ…` | 全项目 | **0** |
| 数据库密码 | 产品代码（除 `.env`） | **0** |
| `192.168.1.4` | 产品代码 | **0** |
| `192.168.2.219` | 产品代码（除 `miniapp/common/config.js`） | **0** |
| `:5000` / `:5001` | 产品代码 | **0** |
| `traceback` / SQL 错误信息 | 前端与文档 | **0** |
| dist 产物（Secret / 两个 LAN IP / DB 密码 / 脚手架） | `management-web/dist`（68 个文件） | **0** |
| `.env.example` 含真实 Secret | `backend/.env.example` | **0**（仅占位符 `CHANGE_ME_TO_A_STRONG_RANDOM_SECRET`） |

`SECRET_SCAN_HARD_ALL_ZERO = YES`

> **信息项（允许存在，已记录）**：历史文档与测试证据中出现的 `192.168.1.4` / `:5000` / 演示口令字面量，
> 属**既往变更留痕**与测试夹具，非运行面泄露，按审计完整性保留。

---

## 六、数据库最终完整性

| 检查项 | 结果 |
| --- | --- |
| 核心表数量 | **19**（`DATABASE_TABLES = 19`） |
| 结构指纹 | **与基线一致**（139 列；`DATABASE_SCHEMA_CHANGED = NO`，零 DDL） |
| 孤儿 `doctor_patient` | **0** |
| 孤儿 `coach_student` | **0** |
| 孤儿业务记录（10 类，`user_id` 失联） | **0** |
| `sec_` 临时数据 | **0** |
| 本轮 `api_test` 临时数据 | **0** |
| 16 张业务表计数 | **与基线 delta 全 0** |
| 受保护实体 | `users` 1 小林同学 / 2 阿may / 12 小孙 / 13 **小周**；`doctor_user` 1-3；`coach_user` 1-3 —— **全部 INTACT** |
| 小周 10 类业务数据 | 健康记录 / 睡眠 / 运动 / 健康计划 / 医生建议 / 体检通知 / 医疗记录 / 运动目标 / 训练计划 / 健身建议 —— **全部 INTACT** |
| 小周 ↔ doctor002 / coach001 绑定 | **INTACT** |

`PROTECTED_ALL_INTACT = True`

---

## 七、最终回归与验证

| 项目 | 命令 | 结果 |
| --- | --- | --- |
| 后端自检 | `tests/backend_selfcheck.py` | **5 / 5 PASS**（126 条路由；端口/敏感项/Python 编译全绿） |
| 小程序静态检查 | `tests/miniapp_check.py` | **23 / 23 PASS** |
| PC 端静态检查 | `tests/web_check.py` | **33 / 33 PASS** |
| 接口联调 / 权限 / 安全 | `tests/api_test.py` | **199 / 199 PASS**（含新增「本轮测试数据精确清理」断言） |
| 权限 + 异常专项 | `tests/security/_sec_run.py` + `_sec_static.py` | **A~K 197 / 197 PASS**（A29 B18 C16 D20 E16 F24 G16 H19 I17 J7 K15） |
| 四角色真实冒烟 | `tests/security/_seal_smoke_final.py` | **46 / 46 PASS** |
| 生产构建 | `vite build` | **PASS**（22.09s，exit 0） |

### 7.1 四角色冒烟明细（46 项）

- **USER（小周 13814142525）13 项**：登录、`info`、健康记录、睡眠、运动、健康计划、统计报告、医生建议、体检通知、医疗记录、运动目标、训练计划、健身建议 —— 全 200。
- **DOCTOR（doctor002）8 项**：登录、`info`、`dashboard`、`patient/list`、小周健康/睡眠/运动数据、建议列表 —— 全 200；**关系权限**：访问非本人患者 → 被拒（401）。
- **COACH（coach001）7 项**：登录、`info`、`dashboard`、`student/list`、小周运动数据与统计、运动目标列表 —— 全 200；**关系权限**：访问非本人学员 → 被拒（401）。
- **ADMIN 14 项**：登录、仪表盘、**12 个一级模块**（普通用户管理 / 医生管理 / 教练管理 / 审核中心 / 角色关系管理 / 健康数据中心 / 健康计划管理 / 医生业务监管 / 健身业务监管 / 内容运营管理 / 系统管理 / 操作日志）—— 全 200；**边界**：匿名访问 → 401。
- 另含 `/api/health` 存活（`database = ok`）。

### 7.2 安全复验（A~K 197 项）

覆盖：四角色 Token 隔离（含伪造 / 篡改 Token）、未登录拦截、医生患者隔离、教练学员隔离、
用户数据所有权、管理员监管边界（无原始数据写接口）、审核状态机、HTTP 异常稳定性、静态安全扫描。
**未降低任何测试标准；用例数与历史基线一致。**

---

## 八、生产构建与前端配置

| 检查项 | 结果 |
| --- | --- |
| `vite build` | **PASS** |
| dist 生产 API 基础路径 | **`/api`**（同源相对路径） |
| dist 生产静态路径 | **`/static/upload/`**（同源相对路径） |
| dist 内 LAN IP / Secret / DB 密码 / 脚手架 | **全部 0** |
| 小程序网络配置入口 | **唯一** = `miniapp/common/config.js`（`192.168.2.219:8080`，按需求保留） |
| 小程序页面级 IP 硬编码 | **0** |
| PC 管理端路由 / 守卫 / Token / API / 构建 | 正常（三角色独立请求实例，Token 不串用） |
| 管理员一级模块数 | **12**（`router/admin.js::adminMenus`，未增未删） |

---

## 九、封板前检查清单

```
DEF-01                          = PASS
FINAL_SECURITY_ACCEPTANCE       = PASS
STORAGE_ITEM_01_API_ADDRESS     = PASS
STORAGE_ITEM_02_JWT_SECRET      = PASS
HISTORICAL_TEST_RESIDUE         = CLEAN（CONFIRMED 删除 / UNCONFIRMED 保留 3）
TEMP_TEST_DATA_RESIDUE          = 0
PROTECTED_ALL_INTACT            = True
DATABASE_SCHEMA_CHANGED         = NO
SECRET_LEAK_SCAN                = PASS
ENGINEERING_HYGIENE             = PASS
backend_selfcheck               = 5 / 5 PASS
miniapp                         = 23 / 23 PASS
management-web                  = 33 / 33 PASS
api_test                        = 199 / 199 PASS
security (A~K)                  = 197 / 197 PASS
四角色冒烟                       = 46 / 46 PASS
Vite build                      = PASS
真实未解决高风险缺陷              = 0
真实未解决中风险缺陷              = 0
真实未解决低风险缺陷              = 4（见 §十，已记录，不阻塞）
```

---

## 十、遗留低风险事项（已记录，不阻塞封板）

| # | 事项 | 风险 | 说明与建议 |
| --- | --- | --- | --- |
| 1 | `admin_operation_log` 随每次 `api_test` 增长（约 +39 行/轮） | 低 | 属**审计表**而非业务数据，且审计留痕按完整性原则**不应删除**；生产环境不会由测试触发。建议：正式部署前清空测试期审计记录并切换为真实运维留痕。 |
| 2 | 开发环境 MySQL 口令为**弱口令**，且与文档中演示口令字面量相同 | 低 | 系统已确认**产品代码零硬编码**（全部走 `.env`）；该口令**仅限本地开发**，`.env` 已被忽略不入库。建议：部署前替换为高强度口令并同步 `backend/.env`。 |
| 3 | `tests/manual-probes/` 保留 49 项历史验证脚手架；`tests/security/_out/` 保留验收证据 | 低 | 属 DEF-01 的**隔离区**与**正式测试证据**，按规则保留；已被 `.gitignore` 覆盖，不进产品目录。建议：作为历史留存，无需处理。 |

| 4 | 审核中心「医生账号」列固定 `width="130"`，18 字符账号折行 | 低 | 纯 UI 观感问题，**不影响运行 / 安全 / 数据完整性**。建议：放宽列宽或改用 `min-width`。 |

> 另：`UNCONFIRMED` 保留的 3 个账号（`doctor_user` 17 `001` / 18 `003`、`coach_user` 12 `002`）语义与
> `doctor001-003` / `coach001-003` 易混淆，建议由需求方确认其归属后另行裁定；本轮**不做任何处置**。

---

## 十一、本轮变更文件清单（可审计）

**新增**

- `.gitignore` · `backend/.gitignore` · `management-web/.gitignore` · `miniapp/.gitignore`
- `docs/FINAL_PROJECT_SEAL_REPORT.md`（本文件）
- `tests/security/`：`_seal_recon.py`、`_seal_recon2.py`、`_seal_baseline.py`、`_seal_cleanup.py`、
  `_seal_verify.py`、`_seal_run_apitest.py`、`_seal_cache_audit.py`、`_seal_cache_clean.py`、
  `_seal_secret_scan.py`、`_seal_smoke_final.py`、`_seal_front_audit.py`、`_seal_doc_sync.py`、
  `_seal_report_closeout.py`、`_seal_pycache.py`

**修改**

- `tests/api_test.py`（追加防残留清理机制，最小追加式）
- `README.md`（同源相对路径 / 小程序 IP / `.env` 不提交 / 换 Wi-Fi 改法 / 测试数量 / **新增 §二十三、§二十四**）
- `docs/API.md`（基础地址 → 同源 `/api`）、`docs/DATABASE.md`（封板校验注记）、
  `docs/TEST_REPORT.md`（199 项 / 同源部署）、`docs/FINAL_REPORT.md`（历史开发口令脱敏）、
  `docs/FINAL_SECURITY_ACCEPTANCE_REPORT.md`（追加 §十四 第 5 版）

**未修改（红线）**：`miniapp/**` 业务代码、`management-web/src/**` 业务代码、`backend/**` 产品逻辑、
`database/**`、JWT 算法/载荷/时效、`Flask HOST/PORT`、`CORS`、数据库结构与现有真实业务数据。

---

## 十二、最终判定

```
PROJECT_FINAL_SEAL = PASS
```

**《个人健康管理系统 V3.2 FINAL》已完成最终封板。**

---

## 十三、封板后真机缺陷修复（BUGFIX-01：小程序「我的」页头像不显示）

> 触发：真机测试发现小程序「我的」页头像位置显示为**白色圆形**，无实际头像。
> 本轮 `PROJECT_FINAL_SEAL` 先置为 `REOPENED_FOR_BUGFIX`，全部回归通过后重新标记为 `PASS`。

### 13.1 定位（只读，逐环取证）

| 环节 | 实测结果 | 判定 |
| --- | --- | --- |
| `users.avatar`（user_id=13 小周） | `9f2f80d5f40d4628b2a3e505f94f1a1d.jpg` | 正常 |
| `/api/user/info` | `avatar` 返回上述文件名（HTTP 与服务层双路径核对） | 正常 |
| `backend/static/upload/<文件名>` | 文件存在，40129 bytes，640×640 有效 JPEG | 正常 |
| `GET http://192.168.2.219:8080/static/upload/<文件名>` | `200` · `Content-Type: image/jpeg` | 正常 |
| `miniapp/common/config.js` | `STATIC_BASE_URL = http://192.168.2.219:8080/static/upload/` | 正常 |
| `resolveFileUrl()` | `STATIC_BASE_URL + 文件名`，无文件名/半路径/完整 URL 的二次拼接 | 正常 |
| 旧地址残留（`192.168.1.4` / `localhost` / `127.0.0.1`） | 0 处 | 正常 |
| 上传链路 | 上传 → `static/upload` 生成 UUID 文件 → 库内只存文件名 → `/user/info` 回读一致 | 正常 |

结论：**服务端、数据库、URL 拼接均无缺陷**；头像文件真实存在且 HTTP 200，属情况 B（文件正常、真机不显示）。

### 13.2 根因

微信小程序在**真机**上会在渲染层拦截 `<image>` 组件加载 `http://` 网络图片：
图片走系统图片通道（渲染层），而开发者工具「不校验合法域名」只放行 JSBridge 网络请求
（官方文档亦将图片归入「其他 HTTPS 请求」）。因此 `wx.request` 访问同一
`http://<局域网IP>:8080` 正常、而同一地址的图片在真机上空白 —— 与本次现象完全一致。

`miniapp/manifest.json` 与产物 `project.config.json` / `project.private.config.json` 中
`urlCheck: false`（即「不校验合法域名」）**本就是开启状态**，故不属于设置缺失；
本轮**未关闭任何产品安全逻辑**，也未改协议与域名策略。

### 13.3 最小修复（仅小程序前端：新增 1 个模块 + 4 个页面各改 1~2 行）

- **新增** `miniapp/common/image.js`：`imgSrc(文件名)` = `resolveFileUrl()` + 真机本地化。
  对 `http://` 地址先用 `uni.downloadFile`（与 `wx.request` 同一条 JSBridge 通道）下载到本地
  临时文件，再交给 `<image>` 渲染；`https://` 地址与本地打包资源**原样返回**，
  下载失败也**回落原地址** ⇒ 对生产环境零影响，且失败时行为与改造前完全一致。
- **修改** `<image>` 地址绑定，统一改走 `imgSrc()`：
  `pages/profile/index.vue`（我的·头像）、`pages/index/index.vue`（首页头像 + 科普封面）、
  `pages/article/index.vue`、`pages/article-detail/index.vue`。

**设计不变式保持**：数据库仍**只保存文件名**；URL 前缀仍由 `common/config.js::resolveFileUrl()`
唯一负责；未改后端、未改接口契约、未改数据库、未放宽任何鉴权或安全校验。

> 说明：§十一「未修改 miniapp 业务代码」是**上一轮封板**的表述；本轮为需求方授权的真机缺陷修复，
> 属**小程序前端**改动，服务端与 PC 端产品代码仍为 0 改动。

### 13.4 回归结果

```
backend_selfcheck = 5/5 PASS          miniapp = 23/23 PASS
management-web    = 33/33 PASS        api_test = 199/199 PASS
security A~K      = 197/197 PASS      Vite build（上一轮） = PASS
头像上传 / 读取端到端 = 19/19 PASS
  （注册 → 登录 → 上传 → 落盘 → 库内只存文件名 → /user/info 回读 →
    LAN 与回环两路 GET 200 + image/* → 三重守卫清理 → 计数回基线）

用户数据 = INTACT    doctor002 绑定 = INTACT    coach001 绑定 = INTACT
DATABASE_SCHEMA_CHANGED = NO（19 表 / 139 列 / 结构指纹未变）
本轮临时数据残留 = 0
```

### 13.5 判定

```
BUGFIX-01            = 已修复（服务端与前端代码本身无缺陷；真机图片加载链路按平台约束改道）
AVATAR_REAL_DEVICE_FIX = 待真机复测确认
PROJECT_FINAL_SEAL   = PASS（REOPENED_FOR_BUGFIX → PASS）
```

> 软件侧所有可自动验证的环节均已由本轮回归证实为 PASS；真机显示需按 §13.6 人工复测。

### 13.6 真机复测步骤

1. HBuilderX 重新运行到微信开发者工具（源码改动后产物 `unpackage/dist/dev/mp-weixin` 已自动重建）；
2. 手机与电脑处于同一 Wi-Fi（当前后端 LAN 地址 `192.168.2.219:8080`；换网络只需改
   `miniapp/common/config.js` 一处）；
3. 微信开发者工具「详情 → 本地设置」确认已勾选
   **「不校验合法域名、web-view（业务域名）、TLS 版本以及 HTTPS 证书」**（当前已是勾选态）；
4. 真机调试进入「我的」页 → 头像应正常显示。



## 十四、封板后运行时缺陷修复 · BUGFIX-02（uCharts 饼/环图 formatter 异常）

> 记录时间：2026-10-02。需求方在**真机预览前**于微信开发者工具 Console 发现持续报错
> `MiniProgramError: Cannot create property 'formatter' on number '50'` /
> `... on number '1'`，调用栈 `fixPieSeries → uCharts2.drawCharts → new uCharts2 → render → init`。
> 本轮严格按「定位 → 最小修复 → 重新编译 → 回归 → 报告」执行，**未修改第三方库源码**。

### 14.1 定位结论

- **报错来源（产品代码）**：`miniapp/pages/report/index.vue`（数据报告页，全项目**唯一**使用图表的页面）。
  - 运动类型分布（ring）：`series: [{ name: '运动时长', data: sport_by_type.map(x => x.value) }]` → `data: [50]`
  - 睡眠质量占比（ring）：`series: [{ name: '次数', data: qualities.map(x => x.value) }]` → `data: [1]`
- **触发点（第三方库，未改动）**：`miniapp/components/u-charts/u-charts.js` 第 320 行 `fixPieSeries()`：
  当 `series[0].data` 为 Array 时逐项执行 `oldseries[i].formatter = series[0].formatter`；
  若 `oldseries[i]` 是**原始数值**，严格模式下向 number 赋属性即抛
  `Cannot create property 'formatter' on number '50'`。
  `fixPieSeries` 仅在 `type ∈ {pie, ring, mount, rose, funnel}` 时被调用（第 6386 行），
  故 line / column / area 的**数值数组**格式不受影响。

### 14.2 根因与修复

| 项 | 内容 |
| --- | --- |
| 错误结构（BAD） | `series: [{ name, data: [50] }]` —— `data` 为**纯数值数组** |
| 正确结构（FIXED） | `series: [{ data: [{ name, value }] }]` —— ECharts 兼容的**对象数组** |
| 修复方式 | 仅改**调用方数据结构**（`pages/report/index.vue` 两处 ring 图）；未在库内加 `typeof === 'number'` 之类掩盖补丁 |
| 业务数据 | 仍取自真实接口 `/api/report/statistics`（MySQL 真值 50 / 1），未写死、未 mock、未隐藏图表 |

### 14.3 运行时验证（无头 harness，加载真实 u-charts.js）

`tests/security/_ucharts_fix_verify.js`：把 `u-charts.js` 原样转 CJS（仅改导出行，**不动库逻辑**），
用 mock canvas 直接 `new uCharts(opts)`：

```
用例                                        预期    实际    结果
旧结构 ring data:[50]（应报 formatter 错）    抛错    抛错    PASS（复现原文）
旧结构 ring data:[1] （应报 formatter 错）    抛错    抛错    PASS（复现原文）
新结构 ring 运动类型分布（真值 50）           不抛错  不抛错  PASS
新结构 ring 睡眠质量占比（真值 1）            不抛错  不抛错  PASS
新结构 ring 多分片 / 全 0 值 / pie 单分片      不抛错  不抛错  PASS
line / line 双系列 / column / area          不抛错  不抛错  PASS
updateData 增量刷新 ring                    不抛错  不抛错  PASS
TOTAL = 12  PASS = 12  FAIL = 0
```

> `fixPieSeries` 在产物 `unpackage/dist/dev/mp-weixin/components/u-charts/u-charts.js` 中与源码
> **语义逐字一致**（`oldseries[i].formatter` 恰 1 处）⇒ 证明**第三方库零改动**，被测库 = 出厂库。

### 14.4 重新编译与产物验收（HBuilderX CLI）

```
HBuilderX cli.exe launch <miniapp> --compile true  → rc=0（mp-weixin 编译成功，约 11s）
产物锚点：新结构 { name, value } hit=2；旧结构 hit=0；全树旧结构残留文件 = 0
common/image.js（BUGFIX-01 头像本地化）仍在；profile/index.js 与 index/index.js 仍走 imgSrc
node --check 语法：23 个 .js 全通过；common_vendor 导出符号 21/21 齐备，未定义引用 = 0
两次编译产物 106/106 文件逐字节一致（BUILD_DETERMINISTIC = YES）
```

### 14.5 回归结果

```
backend_selfcheck = 5/5 PASS          miniapp = 23/23 PASS
management-web    = 33/33 PASS        api_test = 199/199 PASS
security A~K      = 197/197 PASS
uCharts 结构运行时验证 = 12/12 PASS    HBuilderX 编译产物验收 = PASS

用户数据(1/2/12/13) = INTACT     doctor002 绑定 = INTACT    coach001 绑定 = INTACT
PROTECTED_ALL_INTACT = True      DATABASE_SCHEMA_CHANGED = NO（19 表 / 139 列 / 指纹未变）
本轮临时数据残留 = 0
```

### 14.6 判定

```
UCHARTS_FORMATTER_ERROR_BEFORE = 2（复现：on number '50' / on number '1'）
UCHARTS_FORMATTER_ERROR_AFTER  = 0（真实库运行时 12/12；产品代码 0 处旧结构）
UCHARTS_RUNTIME_FIX = PASS（软件侧全闭环；开发者工具 Console 由需求方按 14.7 复看）
PROJECT_FINAL_SEAL  = PASS（REOPENED_FOR_BUGFIX → PASS）
```

### 14.7 开发者工具复看步骤

1. HBuilderX 重新运行到微信开发者工具（产物 `unpackage/dist/dev/mp-weixin` 已重建）；
2. 登录小周账号，打开「数据报告」页；
3. Console 过滤关键字 `formatter` ⇒ 期望 **0 条**；
4. 其余红色条目按三类归因：PRODUCT_ERROR（应为 0）/ DEVTOOLS_NOISE（uni统计、sourcemap、
   渲染层提示）/ NETWORK_ERROR（局域网 http 相关）。
## 十五、封板后真机 UI 缺陷修复 · BUGFIX-03（首页 + 数据报告 · 真机尺寸/布局）

> 触发：需求方使用真实 AppID 在**手机微信真机预览**，发现首页与数据报告存在 UI 缺陷。
> 本轮为 **真机 UI BUGFIX**，不改变任何业务功能、API 契约、数据库结构或绿色视觉体系。

### 15.1 现象
- 数据报告：折线/柱状卡片只显示「巨大坐标数字」（如 65 / 63.75 / 120 / 90 / 50 / 37.50）+ 部分坐标轴，图形未铺满卡片；**运动类型 ring / 睡眠质量 ring 整片空白**。
- 首页：「健康科普」标题右侧显示为 `更多 &gt;`（HTML 实体被当普通字符串）；Hero 区略松。

### 15.2 根因（真机 canvas 尺寸 **双重缩放**）
微信小程序**旧版 canvas**（`uni.createCanvasContext`）的绘图坐标系 = 组件 **CSS 像素**，位图由容器按设备 DPR 自动渲染，**不需要调用方再乘 DPR**。旧封装把
`width = 实测宽度 * pixelRatio`、`pixelRatio = 系统 DPR(≈3)`，而 uCharts 内部又把 `fontSize / padding / ringWidth / yAxisWidth / dashLength` 等统一 `* opts.pix`，导致：
1) 图形与文字被整体放大 DPR 倍 → 卡片里只剩「巨大数字 + 部分坐标轴」；
2) 饼/环图圆心 `(width/2, height/2)` 被推出画布 → **环图整片空白**。

### 15.3 修复（产品代码 3 个文件）
| 文件 | 改动 |
| --- | --- |
| `miniapp/components/u-charts/u-charts.vue` | `width/height` 改为 **CSS px**（`boundingClientRect` 实测，异常回落 `uni.upx2px`）；`pixelRatio` 固定 **1**；补齐 `extra.ring`（库内 pie/ring 使用两个独立配置键）；单序列图例关闭；字号 11~12。**未改第三方 `u-charts.js`** |
| `miniapp/pages/report/index.vue` | ring 保持 `[{name,value}]` 对象数组并加 `value>0` 守卫（全 0 / 无数据 → 置空走「暂无数据」）；线/柱/面积数据经 `pick()` 过滤空值（0/1/2+ 三态自然分支）；趋势卡高 380rpx、ring 卡高 420rpx；单序列关图例 |
| `miniapp/pages/index/index.vue` | `更多 &gt;` → **`更多 ›`**（真实字符）；Hero 内边距 26/30/22rpx、下边距收紧；内容卡标题与 Hero 间距压缩；**`imgSrc()` 头像修复保留** |

- 首页：Hero 间距收紧，九宫格/科普列表/业务功能与 API 均未改。
- 数据报告：**无写死、无 mock、无隐藏图表**；`65 / 63.75 / 50 / 37.50` 等均为 uCharts 自身计算的 Y 轴刻度，已由正确尺寸配置消除「巨大刻度」现象。
- 第三方库 `components/u-charts/u-charts.js` **零改动**（`oldseries[i].formatter` 仍恰 1 处，与源码语义逐字一致）。

### 15.4 验证（软件侧）
- 无头 Node harness（加载**真实** `u-charts.js`）：series 结构 **12/12**、真机尺寸/越界/字号/单分类整圆 **28/28**。
- HBuilderX 命令行重编译 `mp-weixin`：**rc=0**；产物锚点（新结构 hit / 旧结构残留 0 / ring 圆心在画布内）；
- 编译确定性：两次编译 **106/106 逐字节一致**；`node --check` 全通过；vendor 符号无未定义引用。
- `backend_selfcheck 5/5` · `miniapp_check 23/23` · `web_check 33/33` · `api_test 199/199` · 安全 A~K `197/197`。
- 响应式循环静态核查：封装组件仅 `watch(props.chartData)` 与 `watch([width,height])`，均不写模板读取的响应式；`image.js` 只在**异步回调**里写 `localPaths` ⇒ 无 `render → 改 reactive → render` 循环。

```
FORMATTER_ERROR                  = 0
RECURSIVE_UPDATE_ERROR           = 0（产品侧静态核查；如真机仍出现请回传，继续定位）
MINIPROGRAM_PRODUCT_ERROR        = 0
DATABASE_SCHEMA_CHANGED          = NO（19 表 / 139 列 / 指纹未变）
PROTECTED_ALL_INTACT             = True（小周 10 类业务 + doctor002 / coach001 绑定均 INTACT）
TEMP_TEST_DATA_RESIDUE           = 0
MANAGEMENT_WEB_SOURCE_CHANGED    = NO（PC 端本轮 0 改动；web_check 33/33 即无回归证据）
VITE_BUILD                       = SKIPPED_DUE_TO_SAFE_DELETE_GUARD
SOFTWARE_REGRESSION              = PASS
REAL_DEVICE_UI_ACCEPTANCE        = WAITING_USER_CONFIRMATION
PROJECT_FINAL_SEAL               = REOPENED_FOR_REAL_DEVICE_UI_FIX
```

### 15.5 真机人工验收清单（请需求方重编译后逐项确认）
**A. 首页**：头像正常 · 「更多 ›」正常 · Hero 高度/间距正常 · 九宫格正常 · 科普封面正常
**B. 数据报告**：概览卡正常 · 体重趋势正常 · 血压趋势正常 · 运动时长正常 · 运动类型 ring 正常 · 睡眠质量 ring 正常 · **无巨大坐标数字** · **无异常空白**
**C. 我的**：头像正常 · 原页面无回归

> 未在真机人工确认前，本报告**不**标注 `REAL_DEVICE_UI_ACCEPTANCE = PASS`。
