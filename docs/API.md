# 个人健康管理系统 · API 接口文档

> 版本：V3.2 FINAL　　基础地址：`/api`（**生产同源相对路径**；小程序端为 `http://<局域网IP>:8080/api`）
> 接口总数：**126 个**（另有 `GET /api/health` 探活接口与静态资源路由）
> 统一响应体：`{ "code": 200, "msg": "xxx", "data": {...} }`

---

## 一、通用约定

### 1.1 统一响应体

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `code` | int | `200` 成功；`400` 业务错误（参数/账号/关系不合法）；`401` 未登录、Token 无效/过期、越权 |
| `msg` | string | 人类可读的提示文本，前端可直接 `Toast`/`Message` 展示 |
| `data` | object / array / null | 业务数据；失败时通常为 `null` |

### 1.2 认证方式

除「免登录接口」外，所有接口通过 **请求头** 携带对应角色的 Token：

```
Authorization: Bearer <token>
```

请求层会自动解析 Token 的 `token_type` 字段并与接口所需角色比对，**四角色 Token 完全隔离**：

| Token 类型（`token_type`） | `role` | 持有者 | 服务端装饰器 |
| --- | --- | --- | --- |
| `user_token` | 0 | 普通用户 | `user_token_required` |
| `doctor_token` | 1 | 医生 | `doctor_token_required` |
| `coach_token` | 2 | 健身教练 | `coach_token_required` |
| `admin_token` | 3 | 管理员 | `admin_token_required` |

Token 载荷：`{ id, role, token_type, exp }`，有效期默认 **72 小时**（`JWT_EXPIRE_HOURS`）。
用 A 角色的 Token 调 B 角色接口 → **一律 401**（服务端强制，非前端隐藏菜单）。

### 1.3 越权防护规则

1. **本人数据**：普通用户接口的 `user_id` 一律**从 Token 解析**，接口不接受客户端传入的 `user_id`。
2. **医患关系**：医生读取/写入某患者数据前，必须存在 `doctor_patient(doctor_id, user_id)` 绑定记录，否则 **401**。
3. **教练学员关系**：教练读取/写入某学员数据前，必须存在 `coach_student(coach_id, user_id)` 绑定记录，否则 **401**。
4. **注册字段防篡改**：医生/教练注册接口对 `audit_status` **强制置 0**、忽略客户端传入的 `id`。
5. **关系解除后立即失效**：管理员解除绑定后，医生/教练继续读取该用户 → **401**。
6. **待审核账号禁止登录**：`audit_status != 1` 的医生/教练登录 → **400 且不返回 Token**。

### 1.4 状态码语义

| code | 含义 | 典型场景 |
| --- | --- | --- |
| 200 | 成功 | 正常业务返回 |
| 400 | 业务校验失败 | 手机号重复、密码错误、待审核登录、重复绑定、非法枚举值（如睡眠质量）、非法扩展名上传 |
| 401 | 认证/授权失败 | 无 Token、非法 Token、过期 Token、角色不匹配、无医患/教练学员关系 |

---

## 二、免登录接口（公开）

| 方法 | 路径 | 说明 | 关键参数 |
| --- | --- | --- | --- |
| GET | `/api/health` | 服务探活 / 数据库连通性自检 | — |
| GET | `/api/article/list` | 健康科普列表（仅 `is_show=1`） | `page`、`pageSize`、`keyword` |
| GET | `/api/article/detail` | 健康科普详情 | `id` |
| GET | `/api/notice/list` | 系统公告列表（仅 `is_show=1`） | `page`、`pageSize` |
| GET | `/api/notice/detail` | 系统公告详情 | `id` |

> 隐藏（`is_show=0`）的文章/公告，小程序端列表与详情均不可见（已纳入测试用例）。

---

## 三、普通用户接口（13 个，`user_token_required`）

模块前缀：`/api/user/*`　　登录/注册为公开。

| 方法 | 路径 | 说明 | 需 Token | 关键参数 |
| --- | --- | --- | --- | --- |
| POST | `/api/user/register` | 用户注册 | 否 | `phone`、`password`、`nickname`、`gender`、`age`、`height` |
| POST | `/api/user/login` | 用户登录 | 否 | `phone`、`password` → 返回 `user_token` |
| POST | `/api/user/logout` | 退出登录 | 是 | — |
| GET | `/api/user/info` | 查询个人资料 | 是 | — |
| POST | `/api/user/update_info` | 修改个人资料 | 是 | `nickname`、`gender`、`age`、`height` |
| POST | `/api/user/update_pwd` | 修改密码 | 是 | `old_password`、`new_password` |
| POST | `/api/user/upload_avatar` | 上传头像 | 是 | `file`（multipart，仅 `.jpg/.jpeg/.png/.webp`） |
| GET | `/api/user/sport_goal` | 我的运动目标（教练下发） | 是 | — |
| GET | `/api/user/training_plan` | 我的训练计划（教练下发） | 是 | — |
| GET | `/api/user/fitness_advice` | 我的健身建议（教练下发） | 是 | — |
| GET | `/api/user/doctor_advice` | 我的医生建议 | 是 | — |
| GET | `/api/user/medical_notice` | 我的体检通知 | 是 | — |
| GET | `/api/user/medical_record` | 我的医疗记录 | 是 | — |

> 上述「我的 xxx」接口的 `user_id` 全部取自 Token，患者只能看到与自己绑定的医生/教练产出的数据。

### 3.1 健康数据录入（`/api/health_record`、`/api/sleep_record`、`/api/sport_record`）

| 方法 | 路径 | 说明 | 需 Token | 关键参数 |
| --- | --- | --- | --- | --- |
| POST | `/api/health_record/add` | 录入健康指标 | 是 | `record_date`、`weight`、`blood_pressure_high`、`blood_pressure_low`、`heart_rate`、`blood_sugar` |
| GET | `/api/health_record/my_list` | 健康指标列表 | 是 | `page`、`pageSize` |
| POST | `/api/sleep_record/add` | 录入睡眠 | 是 | `sleep_date`、`sleep_start`、`sleep_end`、`sleep_quality` |
| GET | `/api/sleep_record/my_list` | 睡眠列表 | 是 | `page`、`pageSize` |
| POST | `/api/sport_record/add` | 录入运动 | 是 | `sport_date`、`sport_type`、`sport_duration`、`calorie`、`remark` |
| GET | `/api/sport_record/my_list` | 运动列表 | 是 | `page`、`pageSize` |

- **睡眠时长由后端自动计算**（`sleep_end - sleep_start`，单位分钟），前端无需传 `sleep_duration`。
- `sleep_quality` 仅允许 `很好 / 一般 / 较差`，非法值 → **400**。

### 3.2 健康计划与数据报告

| 方法 | 路径 | 说明 | 需 Token | 关键参数 |
| --- | --- | --- | --- | --- |
| POST | `/api/health_plan/add` | 创建健康计划 | 是 | `plan_title`、`plan_content`、`plan_start`、`plan_end` |
| GET | `/api/health_plan/my_list` | 我的健康计划 | 是 | `page`、`pageSize` |
| POST | `/api/health_plan/update_status` | 更新计划状态 | 是 | `id`、`plan_status`（0 进行中 / 1 已完成 / 2 已放弃） |
| GET | `/api/report/statistics` | 数据报告聚合统计 | 是 | — |

`/api/report/statistics` 返回字段（供 uCharts 直接渲染）：

| 字段 | 说明 |
| --- | --- |
| `weight_trend` | 体重趋势（折线） |
| `blood_pressure_trend` | 血压趋势（高压/低压双折线） |
| `sport_daily` | 每日运动时长（柱状） |
| `sport_type` | 运动类型分布（环形） |
| `sleep_quality` | 睡眠质量分布（环形） |
| `sleep_duration` | 睡眠时长趋势（面积） |
| `plan_list` | 健康计划列表 |
| `summary` | 今日概览（体重/血压/运动/睡眠等） |

---

## 四、医生接口（20 个，`doctor_token_required`）

| 方法 | 路径 | 说明 | 需 Token | 关键参数 |
| --- | --- | --- | --- | --- |
| POST | `/api/doctor/register` | 医生注册申请 | 否 | `doctor_name`、`password`、`real_name`、`gender`、`phone`、`specialty`（`audit_status` 强制 0） |
| POST | `/api/doctor/login` | 医生登录 | 否 | `doctor_name`、`password` → 返回 `doctor_token`（待审核 → 400） |
| POST | `/api/doctor/logout` | 退出登录 | 是 | — |
| GET | `/api/doctor/info` | 本人资料 | 是 | — |
| POST | `/api/doctor/update_pwd` | 修改密码 | 是 | `old_password`、`new_password` |
| POST | `/api/doctor/upload_avatar` | 上传头像 | 是 | `file` |
| GET | `/api/doctor/dashboard` | 工作台统计 + 图表 | 是 | 返回 `stats`：`patient_count / today_record_count / attention_count / advice_count` |
| GET | `/api/doctor/patient/list` | 患者列表（仅本人患者） | 是 | `page`、`pageSize`、`keyword` |
| GET | `/api/doctor/patient/detail` | 患者详情 | 是 | `user_id`（须已绑定，否则 401） |
| GET | `/api/doctor/patient/health_data` | 患者健康指标 | 是 | `user_id` |
| GET | `/api/doctor/patient/sleep_data` | 患者睡眠数据 | 是 | `user_id` |
| GET | `/api/doctor/patient/sport_data` | 患者运动数据 | 是 | `user_id` |
| GET | `/api/doctor/patient/plan_data` | 患者健康计划 | 是 | `user_id` |
| GET | `/api/doctor/patient/trend` | 患者健康趋势 | 是 | `user_id` |
| GET | `/api/doctor/advice/list` | 健康建议列表 | 是 | `page`、`pageSize` |
| POST | `/api/doctor/advice/save` | 保存健康建议 | 是 | `user_id`、`advice_content`（须已绑定，否则 401） |
| GET | `/api/doctor/medical_notice/list` | 体检通知列表 | 是 | `page`、`pageSize` |
| POST | `/api/doctor/medical_notice/save` | 保存体检通知 | 是 | `user_id`、`notice_title`、`notice_content`、`check_date` |
| GET | `/api/doctor/medical_record/list` | 医疗记录列表 | 是 | `page`、`pageSize` |
| POST | `/api/doctor/medical_record/save` | 保存医疗记录 | 是 | `user_id`、`record_title`、`record_content`、`record_date` |

> 所有 `patient/*` 与 `*/save` 接口均执行 `doctor_patient` 关系校验；未绑定 → **401**（测试用例 越权 B / 附加 已覆盖）。

---

## 五、健身教练接口（19 个，`coach_token_required`）

| 方法 | 路径 | 说明 | 需 Token | 关键参数 |
| --- | --- | --- | --- | --- |
| POST | `/api/coach/register` | 教练注册申请 | 否 | `coach_name`、`password`、`real_name`、`gender`、`phone`、`specialty`（`audit_status` 强制 0） |
| POST | `/api/coach/login` | 教练登录 | 否 | `coach_name`、`password` → 返回 `coach_token`（待审核 → 400） |
| POST | `/api/coach/logout` | 退出登录 | 是 | — |
| GET | `/api/coach/info` | 本人资料 | 是 | — |
| POST | `/api/coach/update_pwd` | 修改密码 | 是 | `old_password`、`new_password` |
| POST | `/api/coach/upload_avatar` | 上传头像 | 是 | `file` |
| GET | `/api/coach/dashboard` | 工作台统计 + 图表 | 是 | 返回 `stats`：`student_count / today_sport_user / month_duration / running_plan` |
| GET | `/api/coach/student/list` | 学员列表（仅本人学员） | 是 | `page`、`pageSize`、`keyword` |
| GET | `/api/coach/student/detail` | 学员详情 | 是 | `user_id`（须已绑定，否则 401） |
| GET | `/api/coach/student/sport_data` | 学员运动数据 | 是 | `user_id` |
| GET | `/api/coach/student/statistics` | 学员运动统计 | 是 | `user_id` |
| GET | `/api/coach/sport_goal/list` | 运动目标列表 | 是 | `page`、`pageSize` |
| POST | `/api/coach/sport_goal/save` | 创建/更新运动目标 | 是 | `user_id`、`goal_title`、`goal_content`、`start_date`、`end_date` |
| POST | `/api/coach/sport_goal/update_status` | 更新目标状态 | 是 | `id`、`goal_status`（0/1/2） |
| GET | `/api/coach/training_plan/list` | 训练计划列表 | 是 | `page`、`pageSize` |
| POST | `/api/coach/training_plan/save` | 创建/更新训练计划 | 是 | `user_id`、`plan_title`、`plan_content`、`start_date`、`end_date` |
| POST | `/api/coach/training_plan/update_status` | 更新计划状态 | 是 | `id`、`plan_status`（0/1/2） |
| GET | `/api/coach/fitness_advice/list` | 健身建议列表 | 是 | `page`、`pageSize` |
| POST | `/api/coach/fitness_advice/save` | 保存健身建议 | 是 | `user_id`、`advice_content`（须已绑定，否则 401） |

> 所有 `student/*` 与 `*/save` 接口均执行 `coach_student` 关系校验；未绑定 → **401**（测试用例 越权 C / 附加 已覆盖）。

---

## 六、管理员接口（59 个，`admin_token_required`）

### 6.1 登录与个人信息

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/admin/login` | 管理员登录 → 返回 `admin_token` |
| POST | `/api/admin/logout` | 退出登录 |
| GET | `/api/admin/info` | 本人资料 |
| POST | `/api/admin/update_pwd` | 修改密码 |
| POST | `/api/admin/upload_avatar` | 上传头像 |

### 6.2 模块 01 · 系统首页

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/admin/dashboard` | 10 项统计卡 + 7 张图表 + 快捷待办（`pending_doctors / pending_coaches / latest_users / latest_logs`），全部为真实 SQL |

### 6.3 模块 02 · 普通用户管理

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/admin/user/list` | 用户列表（分页、手机号搜索、性别筛选） |
| GET | `/api/admin/user/detail` | 用户详情（完整健康档案） |
| GET | `/api/admin/user/health_data` | 档案 Tab · 健康指标 |
| GET | `/api/admin/sleep_record/list` | 档案 / 数据中心 · 睡眠列表 |
| GET | `/api/admin/sport_record/list` | 档案 / 数据中心 · 运动列表 |
| GET | `/api/admin/health_plan/list` | 档案 · 健康计划 |
| GET | `/api/admin/user/doctor_service` | 档案 Tab · 医生服务（建议/通知/记录） |
| GET | `/api/admin/user/coach_service` | 档案 Tab · 健身服务（目标/计划/建议） |

### 6.4 模块 03 / 04 · 医生 / 教练管理

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/admin/doctor/list` | 医生列表（账号查询、审核状态筛选） |
| GET | `/api/admin/doctor/detail` | 医生详情（含 `patients` 与 `business` 统计，**不外泄密码哈希**） |
| POST | `/api/admin/doctor/update` | 编辑医生基础资料 |
| POST | `/api/admin/doctor/reset_pwd` | 重置医生密码 |
| GET | `/api/admin/coach/list` | 教练列表 |
| GET | `/api/admin/coach/detail` | 教练详情（含负责学员数与业务统计） |
| POST | `/api/admin/coach/update` | 编辑教练基础资料 |
| POST | `/api/admin/coach/reset_pwd` | 重置教练密码 |

### 6.5 模块 05 · 账号审核中心

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/admin/audit/overview` | 概览：待审核医生 / 待审核教练 / 今日已审 / 累计 |
| POST | `/api/admin/doctor/audit` | 医生审核（通过 / 拒绝） |
| POST | `/api/admin/coach/audit` | 教练审核（通过 / 拒绝） |
| GET | `/api/admin/audit/record_list` | 审核记录 |

### 6.6 模块 06 · 角色关系管理

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/admin/doctor/patient/list` | 医患关系列表 |
| POST | `/api/admin/doctor/bind_patient` | 绑定医患关系（重复绑定 → 400） |
| POST | `/api/admin/doctor/unbind_patient` | 解除医患关系 |
| GET | `/api/admin/coach/student/list` | 教练学员关系列表 |
| POST | `/api/admin/coach/bind_student` | 绑定教练学员关系（重复绑定 → 400） |
| POST | `/api/admin/coach/unbind_student` | 解除教练学员关系 |
| GET | `/api/admin/common/users` | 下拉数据源 · 用户 |
| GET | `/api/admin/common/doctors` | 下拉数据源 · 医生 |
| GET | `/api/admin/common/coaches` | 下拉数据源 · 教练 |

### 6.7 模块 07 · 健康数据中心

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/admin/health_data/statistics` | 顶部统计 + 统计分析 |
| GET | `/api/admin/health_record/list` | 健康指标列表（支持日期筛选） |
| GET | `/api/admin/sleep_record/list` | 睡眠数据列表（支持日期筛选） |
| GET | `/api/admin/sport_record/list` | 运动数据列表（支持日期筛选） |
| GET | `/api/admin/health_record/export` | 健康指标 CSV 导出（遵守筛选条件） |
| GET | `/api/admin/sleep_record/export` | 睡眠 CSV 导出（遵守筛选条件） |
| GET | `/api/admin/sport_record/export` | 运动 CSV 导出（遵守筛选条件） |

### 6.8 模块 08 · 健康计划管理

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/admin/health_plan/list` | 计划列表（状态筛选） |
| GET | `/api/admin/health_plan/stats` | 计划统计（总数 / 进行中 / 已完成 / 已放弃） |

### 6.9 模块 09 · 医生业务监管

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/admin/doctor_advice/list` | 健康建议监管（关键词筛选） |
| GET | `/api/admin/medical_notice/list` | 体检通知监管（关键词筛选） |
| GET | `/api/admin/medical_record/list` | 医疗记录监管（关键词筛选） |

### 6.10 模块 10 · 健身业务监管

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/admin/sport_goal/list` | 运动目标监管 |
| GET | `/api/admin/training_plan/list` | 训练计划监管 |
| GET | `/api/admin/fitness_advice/list` | 健身建议监管 |

### 6.11 模块 11 · 内容运营管理

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/admin/article/list` | 文章列表 |
| GET | `/api/admin/article/detail` | 文章详情 |
| POST | `/api/admin/article/save` | 文章新增 / 编辑（含上下架 `is_show`） |
| POST | `/api/admin/article/del` | 文章删除 |
| POST | `/api/admin/article/upload_cover` | 上传文章封面 |
| GET | `/api/admin/notice/list` | 公告列表 |
| GET | `/api/admin/notice/detail` | 公告详情 |
| POST | `/api/admin/notice/save` | 公告新增 / 编辑 |
| POST | `/api/admin/notice/del` | 公告删除 |

### 6.12 模块 12 · 系统管理

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/admin/operation_log/list` | 操作日志列表（**不含密码/Token/密钥等敏感信息**） |
| GET | `/api/admin/operation_log/types` | 操作类型枚举 |
| GET | `/api/admin/system/info` | 系统信息（仅非敏感项：系统名/版本等） |

---

## 七、接口分布汇总

| 归属 | 数量 | 认证 |
| --- | --- | --- |
| 公开（探活 / 科普 / 公告） | 5 | 无 |
| 普通用户（含健康数据 / 计划 / 报告） | 23 | `user_token` |
| 医生 | 20 | `doctor_token` |
| 健身教练 | 19 | `coach_token` |
| 管理员 | 59 | `admin_token` |
| **合计 `/api` 接口** | **126** | — |

---

## 八、图片 URL 规则

- 数据库仅保存**文件名**（如 `default_doctor.jpg`、`a1b2c3.jpg`），**不保存完整 URL**（已由测试用例静态校验）。
- 前端拼接：`STATIC_BASE_URL + 文件名`，其中 `STATIC_BASE_URL = /static/upload/`（生产同源；小程序端为 `http://<局域网IP>:8080/static/upload/`）。
- 上传仅允许扩展名 `.jpg / .jpeg / .png / .webp`，非法扩展名（如 `.php`）→ 400。

---

## 九、医疗业务边界声明

本系统所有「医生建议 / 体检通知 / 医疗记录」均为**健康管理辅助信息**，不构成医疗诊断、处方或治疗意见；不得用于替代线下正规医疗机构就诊。
