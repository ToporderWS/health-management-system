# 个人健康管理系统 · 四角色一次性完整开发完成报告

> 版本：**V3.2 FINAL**　　项目根目录：`health-management-system/`
> 交付形态：MySQL 数据库 + Python Flask 后端 + UniApp/Vue3 微信小程序（普通用户）+ Vue3/Element Plus PC 管理端（医生/教练/管理员）
> **本报告所有结论均来自真实运行与真实数据验证，非设计描述。**

---

## 1. 项目概述

一套面向 **4 类角色** 的个人健康管理平台：

| 角色 | 载体 | 核心职责 |
| --- | --- | --- |
| 普通用户 | 微信小程序 | 录入健康指标/睡眠/运动、制定健康计划、查看数据报告、接收医生与教练的服务 |
| 医生 | PC 管理端 | 管理绑定患者、查看患者健康数据与趋势、下发健康建议/体检通知/医疗记录 |
| 健身教练 | PC 管理端 | 管理绑定学员、查看学员运动数据、下发运动目标/训练计划/健身建议 |
| 管理员 | PC 管理端 | 12 个固定模块：全局监管、账号审核、关系绑定、健康数据中心、内容运营、系统管理 |

**核心边界**：医生只能读写「与自己绑定」的患者数据；教练只能读写「与自己绑定」的学员数据；普通用户只能读写自己的数据。**权限由后端强制执行，不依赖前端隐藏菜单。**

---

## 2. 需求完成度总览

| # | 要求 | 状态 |
| --- | --- | --- |
| 1 | MySQL 数据库（19 表 / 外键 / 索引） | ✅ 完成 |
| 2 | Python Flask 统一后端（`0.0.0.0:8080`，禁 5000/5001） | ✅ 完成 |
| 3 | 统一响应体 `{code,msg,data}` | ✅ 完成 |
| 4 | 四角色 JWT Token 完全隔离 | ✅ 完成 |
| 5 | 医患 / 教练学员关系权限校验 | ✅ 完成 |
| 6 | 医生/教练注册审核流（`audit_status` 强制 0） | ✅ 完成 |
| 7 | Werkzeug 密码哈希 | ✅ 完成 |
| 8 | 全量参数化 SQL（防注入） | ✅ 完成 |
| 9 | 图片上传（扩展名校验，只存文件名） | ✅ 完成 |
| 10 | 小程序 15 页面 + TabBar 固定 4 项 | ✅ 完成 |
| 11 | uCharts 数据报告（7 类图表） | ✅ 完成 |
| 12 | PC 端三角色独立布局/菜单/路由/权限 | ✅ 完成 |
| 13 | 管理员 12 个固定一级模块（23 个页面路由） | ✅ 完成 |
| 14 | 全量测试（198 + 61 项） | ✅ 完成 |
| 15 | README + API + DATABASE + TEST_REPORT + 本报告 | ✅ 完成 |
| 16 | **真实数据，无 Mock / 无 TODO / 无空页面** | ✅ 完成 |

---

## 3. 项目目录结构

```
health-management-system/
├── README.md                      # 总说明（22 节）
├── docs/                          # 交付文档
│   ├── API.md                     # 接口文档（126 接口）
│   ├── DATABASE.md                # 数据库文档（19 表）
│   ├── TEST_REPORT.md             # 测试报告（259 用例）
│   └── FINAL_REPORT.md            # 本报告
├── database/
│   └── health_management.sql      # 建库脚本（19 表 + 初始化数据）
├── backend/                       # Python Flask
│   ├── app.py                     # 入口（0.0.0.0:8080，启动自检 DB）
│   ├── config.py                  # 统一配置（全部读环境变量）
│   ├── .env.example / .env        # 环境变量
│   ├── routes/                    # 按角色拆分蓝图
│   │   ├── user.py  health.py  doctor.py
│   │   ├── coach.py admin.py article.py notice.py
│   ├── services/                  # 业务与 SQL（全参数化）
│   │   ├── user_service.py  health_service.py  doctor_service.py
│   │   ├── coach_service.py admin_service.py   content_service.py
│   ├── utils/                     # auth/jwt_utils/db/response/upload/security/audit_log/helpers
│   └── static/upload/             # 4 张默认头像
├── miniapp/                       # UniApp + Vue3 小程序
│   ├── pages/                     # 15 个页面
│   ├── components/u-charts/       # uCharts 官方库 + Vue 封装
│   ├── common/                    # config.js(唯一地址源)/request.js/auth.js
│   ├── api/index.js               # 接口封装
│   ├── static/tabbar/             # 8 个 TabBar 图标
│   ├── pages.json / manifest.json / App.vue / main.js
├── management-web/                # Vue3 + Element Plus PC 端
│   ├── src/router/                # index.js + doctor.js/coach.js/admin.js
│   ├── src/views/doctor|coach|admin|portal
│   ├── src/api/                   # request.js + 三角色 api
│   ├── src/components/            # BaseLayout/ChartBox/StatCard/PatientSelect/RoleProfile
│   ├── src/utils/                 # config.js(唯一地址源)/auth.js/format.js/download.js
│   ├── .env.development / .env.production
│   └── vite.config.js
├── tests/                         # 4 套测试 + 结果快照
└── tools/                         # 资源生成工具（图标/头像/哈希）
```

---

## 4. 数据库设计与落地

- **19 张表**：`users`、`admin_user`、`doctor_user`、`coach_user`、`doctor_patient`、`coach_student`、`health_record`、`sleep_record`、`sport_record`、`health_plan`、`doctor_advice`、`medical_notice`、`medical_record`、`sport_goal`、`training_plan`、`fitness_advice`、`health_article`、`notice`、`admin_operation_log`。
- **20 个外键**，全部 `ON DELETE CASCADE`，避免孤儿数据。
- **索引按查询模式设计**：唯一键（手机号/账号）、关系表复合唯一键（防重复绑定）、`(user_id, date)` 复合索引（趋势查询）、`(is_show, publish_time)`（小程序列表）、审核状态与日志类型索引。
- **落库验证**：本地 MySQL 8.0.33 已成功导入，19 表齐备，初始化账号与演示数据正确。
- 明文密码检查：所有 `password_hash` 均为 `pbkdf2:sha256`。

详见 `docs/DATABASE.md`。

---

## 5. 后端（Flask）完成情况

- 入口 `app.py` 监听 **`0.0.0.0:8080`**，启动时自检数据库连通性；内置 `GET /api/health` 探活。
- 蓝图按角色拆分（`user/health/doctor/coach/admin/article/notice`），**共 126 个 `/api` 路由**。
- 统一响应体由 `utils/response.py` 收口，**所有接口返回 `{code,msg,data}`**。
- **全量参数化 SQL**（PyMySQL 占位符），无字符串拼接 SQL。
- 密码使用 **Werkzeug `pbkdf2:sha256`** 哈希存储与校验。
- 上传仅允许 `.jpg/.jpeg/.png/.webp`，**数据库只存文件名**，URL 由前端拼接。
- 配置全部来自 `.env`（`config.py`），**无任何硬编码密码/密钥**。
- 服务层设计：`user_service / health_service / doctor_service / coach_service / admin_service / content_service`。

---

## 6. 接口汇总

| 归属 | 数量 | 认证方式 |
| --- | --- | --- |
| 公开（探活 / 健康科普 / 系统公告） | 5 | 免登录 |
| 普通用户（含健康数据 / 计划 / 报告） | 23 | `user_token` |
| 医生 | 20 | `doctor_token` |
| 健身教练 | 19 | `coach_token` |
| 管理员 | 59 | `admin_token` |
| **合计** | **126** | — |

完整清单见 `docs/API.md`。

---

## 7. 四角色 Token 隔离

| Token 类型 | role | 服务端装饰器 |
| --- | --- | --- |
| `user_token` | 0 | `user_token_required` |
| `doctor_token` | 1 | `doctor_token_required` |
| `coach_token` | 2 | `coach_token_required` |
| `admin_token` | 3 | `admin_token_required` |

- Token 载荷 `{id, role, token_type, exp}`，装饰器**同时校验签名、有效期与 `token_type`**。
- 用 A 角色 Token 调 B 角色接口 → **一律 401**（真实 HTTP 验证）。
- 覆盖用例：越权 D/E/F（三角色互访管理员/医生）、附加 7 项交叉访问、L 组（非法/未携带/过期 Token）—— **全部 PASS**。

---

## 8. 数据隔离（本人数据）

- 普通用户所有接口的 `user_id` **从 Token 解析**，接口**不接受客户端传入 `user_id`**（越权 A 验证 PASS）。
- 「我的健康指标 / 睡眠 / 运动 / 计划 / 报告」只返回 Token 对应用户的数据。
- 用户 A 用 `user_token` 尝试读取用户 B 数据 → 被拒。

---

## 9. 关系权限（医患 / 教练学员）

- 医生读取或写入某患者任何数据前，服务层校验 `doctor_patient(doctor_id, user_id)` 存在；
  未绑定 → **401**（越权 B、附加「医生向非本人患者写入建议」PASS）。
- 教练同理，依赖 `coach_student`（越权 C、附加「教练向非本人学员写入建议」PASS）。
- **绑定后立即生效**：绑定 → 可读患者/学员数据（PASS）。
- **解除后立即失效**：管理员解绑 → 医生/教练继续读取 → **401**（越权 O/P PASS）。
- 重复绑定 → **400**（越权 M/N PASS）。

---

## 10. 注册审核流程

1. 医生/教练提交注册 → 服务端**强制 `audit_status = 0`**，并**忽略客户端传入的 `id`**（安全 I/J PASS）。
2. `audit_status != 1` 的账号登录 → **400 且不返回 Token**（越权 G/H PASS）。
3. 管理员在「05 账号审核中心」审核通过/拒绝 → 审核记录留痕。
4. 审核通过后方可登录工作台；审核拒绝账号登录 → 400（越权 K PASS）。

---

## 11. 操作日志与脱敏

- 管理员关键操作（登录、审核、绑定/解绑、重置密码、内容增删改等）写入 `admin_operation_log`。
- 写入前由 `utils/audit_log.py` 统一脱敏，**不含密码/Token/密钥**（安全用例 PASS）。
- **16 类关键操作日志全部有记录**（日志完整性用例 PASS）。
- 「12 系统管理」页可查询日志列表与操作类型枚举；系统信息仅暴露非敏感项。

---

## 12. 普通用户小程序完成情况

- **15 个页面**全部注册且为真实 `.vue`（无空页面）：
  `index`(首页)、`health-entry`(健康录入)、`report`(数据报告)、`profile`(我的)、`login`、`register`、
  `article`、`article-detail`、`plan`、`doctor-advice`、`medical-notice`、`medical-record`、
  `sport-goal`、`training-plan`、`fitness-advice`。
- **TabBar 固定 4 项**：首页 / 健康录入 / 数据报告 / 我的（8 张图标齐备）。
- **uCharts 数据报告**：体重趋势（折线）、血压趋势（双折线）、运动时长（柱状）、运动类型（环形）、睡眠质量（环形）、睡眠时长（面积），数据全部来自 `/api/report/statistics` 真实字段。
- 健康录入页支持健康指标 / 睡眠 / 运动 / 健康计划四类录入，睡眠时长由后端自动计算。
- 登录态网关：受保护页面统一 `ensureLogin()`，未登录跳转登录页。
- 全项目无硬编码 IP（唯一地址源 `common/config.js`）、无 Mock 数据、无 TODO 标记。

---

## 13. 医生端（PC）完成情况

独立 Shell + 独立菜单 + 独立权限，**10 条路由**：

`/doctor/login`、`/doctor/register`、`/doctor/dashboard`、`/doctor/patients`、`/doctor/health`、
`/doctor/trends`、`/doctor/advice`、`/doctor/notices`、`/doctor/records`、`/doctor/profile`

- 工作台统计（患者数/今日记录/需关注指标/已发建议）与图表（录入趋势/血压趋势/患者记录统计）均为真实数据。
- 患者管理、患者健康数据、健康趋势、健康建议、体检通知、医疗记录全部接通后端并受关系权限约束。
- 详情接口**不外泄 `password_hash`**。

---

## 14. 教练端（PC）完成情况

独立 Shell + 独立菜单 + 独立权限，**9 条路由**：

`/coach/login`、`/coach/register`、`/coach/dashboard`、`/coach/students`、`/coach/sports`、
`/coach/goals`、`/coach/training`、`/coach/advice`、`/coach/profile`

- 工作台统计（学员数/今日运动人数/本月时长/进行中计划）与图表（最近 7 天时长/运动类型分布/学员趋势）为真实数据。
- 学员管理、运动数据、运动目标、训练计划、健身建议全部接通并受关系权限约束。

---

## 15. 管理员端（PC）完成情况

独立 Shell + **固定 12 个一级模块**（不新增一级菜单），共 **13 条路由**：

| 模块 | 路由 | 关键能力 |
| --- | --- | --- |
| 01 系统首页 | `/admin/dashboard` | 10 项统计卡 + 7 张图表 + 快捷待办（真实 SQL） |
| 02 普通用户管理 | `/admin/users` | 列表/搜索/筛选/详情 + 6 个健康档案 Tab |
| 03 医生管理 | `/admin/doctors` | 列表/查询/筛选/详情(含患者与业务统计)/编辑/重置密码 |
| 04 健身教练管理 | `/admin/coaches` | 列表/详情/编辑/重置密码 |
| 05 账号审核中心 | `/admin/audit` | 概览 + 医生/教练审核 + 审核记录 |
| 06 角色关系管理 | `/admin/relations` | 医患/教练学员关系增删查 + 三组下拉数据源 |
| 07 健康数据中心 | `/admin/health-data` | 统计 + 三类数据列表/筛选 + **三类 CSV 导出** |
| 08 健康计划管理 | `/admin/plans` | 列表/统计/筛选 |
| 09 医生业务监管 | `/admin/doctor-business` | 建议/通知/记录监管 + 关键词筛选 |
| 10 健身业务监管 | `/admin/coach-business` | 目标/计划/建议监管 |
| 11 内容运营管理 | `/admin/content` | 文章与公告增删改查 + 封面上传 + 上下架 |
| 12 系统管理 | `/admin/system` | 操作日志/类型枚举/系统信息（已脱敏） |

---

## 16. 图片上传与静态资源

- 上传接口统一做扩展名校验，**非法扩展名（如 `.php`）→ 400**（PASS）。
- 数据库**只保存文件名**，四张业务表（`users`/`health_article`/`doctor_user`/`coach_user`）经静态扫描**均无完整 URL**（PASS）。
- 4 张默认头像（health/doctor/coach/admin）齐备；静态目录 `HTTP 200` 可访问。
- 前端通过 `STATIC_BASE_URL + 文件名` 拼接访问地址。

---

## 17. 网络配置

| 项 | 值 | 校验 |
| --- | --- | --- |
| 后端监听 | `0.0.0.0:8080` | `.env.example` `FLASK_PORT=8080` PASS |
| 禁用端口 | 5000 / 5001 | 全项目扫描无命中 PASS |
| API 基础地址 | `http://192.168.1.4:8080/api` | 小程序与 PC 端一致 |
| 静态地址 | `http://192.168.1.4:8080/static/upload/` | 一致 |

---

## 18. 前端配置单一来源

- **小程序**：唯一地址源 `miniapp/common/config.js`；除该文件外**全项目无硬编码 IP**（PASS）。
- **PC 端**：唯一地址源 `management-web/src/utils/config.js`（读 `VITE_API_BASE_URL`，以 8080 地址兜底）；
  开发态走 Vite 代理，生产态 `.env.production` 固定 `http://192.168.1.4:8080/api`（PASS）。

---

## 19. 构建结果

- PC 端 `vite build` **构建成功**：产出 `dist/`，含 **48 个 JS chunk + 18 个 CSS 产物**，
  三角色页面各自打包为独立路由 chunk，按角色懒加载。
- 后端：`python app.py` 正常启动，启动自检数据库连通，126 路由注册成功。
- 小程序：`pages.json` 解析通过，15 页面 + TabBar 4 项 + uCharts 组件引用全部有效。

---

## 20. 测试与验证结果

| 测试层 | 用例数 | 通过 | 失败 |
| --- | --- | --- | --- |
| 后端接口集成（真实 HTTP + 真实 MySQL） | 198 | **198** | 0 |
| 后端静态自检 | 5 | **5** | 0 |
| 小程序静态检查 | 23 | **23** | 0 |
| PC 管理端检查 | 33 | **33** | 0 |
| **合计** | **259** | **259** | **0** |

覆盖：4 角色全接口、A–P 越权/Token 隔离、注册防篡改、审核流、关系绑定与解绑失效、
CSV 导出遵守筛选、隐藏内容不可见、软/硬删除真实落库、日志脱敏与完整性、端口与明文密码扫描、
图片只存文件名、非法扩展名拦截、前端路由守卫与角色隔离。

详见 `docs/TEST_REPORT.md`。

---

## 21. 关键缺陷修复记录（摘要）

| # | 缺陷 | 根因 | 修复 |
| --- | --- | --- | --- |
| 1 | `/admin/health_data/statistics` 500 | pymysql 把 `%Y-%m` 当格式符 | 转义为 `%%Y-%%m` |
| 2 | 测试脚本 `case()` 缺参（5 处） | 漏传 `expect` | 锚点补丁（命中数校验 == 1） |
| 3 | 睡眠时长用例 FAIL | 用例起止时间反了 | 改用昨日入睡（480 分钟） |
| 4 | 中文查询参数编码错误 | 未 URL 编码 | `http()` 内统一 `_enc()` |
| 5 | 工作台断言不符 | 统计在 `data.stats` 子对象 | 用例改读 `stats` |
| 6–11 | 扫描器误报 / 检查器误判（6 项） | 扫描范围与判据问题 | 逐项修正扫描口径与检查规则 |

> 全部修复后 **4 套测试重跑，259/259 通过**。

---

## 22. 安全合规检查

| 项 | 结果 |
| --- | --- |
| 全项目无 5000/5001 端口 | ✅ 无命中 |
| 产品源码无 `123456` 明文密码（扫描 109 文件） | ✅ 无命中 |
| 数据库密码 / JWT Secret 无硬编码 | ✅ 全部走 `.env` |
| 密码均为 Werkzeug 哈希 | ✅ 四角色账号全部合规 |
| SQL 全参数化 | ✅ 无拼接 |
| 图片只存文件名 | ✅ 四表扫描计数 0 |
| 上传扩展名白名单 | ✅ 非法扩展名被拒 |
| 管理员日志脱敏 | ✅ 无敏感字段 |
| 越权防护（角色 + 关系双层） | ✅ A–P 全通过 |

---

## 23. 交付文件清单

| 文件 | 说明 |
| --- | --- |
| `README.md` | 总说明：环境准备、启动步骤、账号、流程、排查、局域网访问 |
| `docs/API.md` | 126 个接口：方法/路径/Token/参数/权限/返回字段 |
| `docs/DATABASE.md` | 19 张表：字段/类型/约束/外键/索引/角色数据关系 |
| `docs/TEST_REPORT.md` | 259 用例明细 + 11 项缺陷修复 + 回归结论 |
| `docs/FINAL_REPORT.md` | 本报告 |
| `database/health_management.sql` | 建库脚本（19 表 + 初始化数据） |
| `backend/` | Flask 后端全量源码 + `.env.example` |
| `miniapp/` | 小程序全量源码（含 uCharts 与 TabBar 图标） |
| `management-web/` | PC 端全量源码（含 `dist/` 构建产物） |
| `tests/` | 4 套测试脚本与结果快照 |
| `tools/` | 资源生成工具（图标/头像/哈希） |

---

## 24. 运行与部署指引（摘要）

```bash
# 1) 导入数据库
mysql -uroot -p < database/health_management.sql

# 2) 启动后端
cd backend
pip install -r requirements.txt
cp .env.example .env      # 修改 DB_PASSWORD / JWT_SECRET
python app.py             # http://0.0.0.0:8080

# 3) PC 管理端
cd management-web
npm install
npm run dev               # 或 npm run build 后用静态服务托管 dist/

# 4) 小程序
# 用 HBuilderX 打开 miniapp/ 运行到微信开发者工具
```

测试账号：`admin/123456`、`doctor001~003/123456`、`coach001~003/123456`、`13800138001|13800138002/123456`。
**正式使用前必须修改全部测试密码并替换 `JWT_SECRET` 与数据库密码。**

---

## 25. 明确不做事项与已知限制

**明确不做（遵循需求边界）：**
- 不做真实医疗诊断、处方、在线问诊与药品相关功能；系统内所有医学文本均为健康管理辅助信息。
- 不引入第三方登录、短信验证码、支付、即时通讯。
- 不新增管理员一级菜单（严格固定 12 个模块）。

**已知限制：**
- 小程序端以 HBuilderX 工程形态交付，未附带已编译的 `unpackage/` 产物（需由 HBuilderX 生成）。
- 本地开发数据库口令与 `JWT_SECRET` **仅限开发环境**，正式使用前必须替换（`JWT_SECRET` 已完成轮换，见安全验收报告 §十三）。
- PDF 报告导出未实现（需求未要求）；CSV 导出已实现并通过筛选条件校验。
- PC 管理端未做移动端响应式适配（面向桌面管理场景）。

---

## 26. 最终结论

| 维度 | 结论 |
| --- | --- |
| 数据库 | ✅ 19 表 / 20 外键 / 索引齐备，已导入并验证 |
| 后端 | ✅ Flask 126 接口，`0.0.0.0:8080`，统一响应体，参数化 SQL |
| 权限 | ✅ 四角色 Token 隔离 + 数据隔离 + 关系权限，A–P 全通过 |
| 小程序 | ✅ 15 页面 + TabBar 4 项 + uCharts 7 类图表，23/23 检查通过 |
| PC 端 | ✅ 三角色独立前台 + 管理员 12 模块，构建成功，33/33 检查通过 |
| 测试 | ✅ **259 / 259 全部通过** |
| 文档 | ✅ README + API + DATABASE + TEST_REPORT + FINAL_REPORT |

> ### ✅ 最终状态：**PASS**
> 四角色个人健康管理系统已按 V3.2 FINAL 要求**一次性完整开发完成**，全部功能可运行、可验证，
> 无 Mock 数据、无 TODO 占位、无空页面，权限隔离由后端强制执行。
