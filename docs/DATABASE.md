# 个人健康管理系统 · 数据库设计文档

> 版本：V3.2 FINAL　　数据库：MySQL 8.0.33　　库名：`health_management`
> 字符集：`utf8mb4` / `utf8mb4_general_ci`　　建库脚本：`database/health_management.sql`
> **19 张表 · 20 个外键 · 按角色与查询模式建索引**
> 封板校验（2026-10-01）：19 张表在线、结构指纹与基线一致、无 DDL 变更、无孤儿记录、临时数据残留 0。

---

## 一、表清单总览

| # | 表名 | 中文含义 | 归属角色 | 关键约束 |
| --- | --- | --- | --- | --- |
| 1 | `users` | 普通用户 | 普通用户 | `phone` 唯一 |
| 2 | `admin_user` | 管理员 | 管理员 | `admin_name` 唯一 |
| 3 | `doctor_user` | 医生 | 医生 | `doctor_name` 唯一；`audit_status` |
| 4 | `coach_user` | 健身教练 | 健身教练 | `coach_name` 唯一；`audit_status` |
| 5 | `doctor_patient` | 医患关系 | 关系表 | `(doctor_id,user_id)` 唯一 |
| 6 | `coach_student` | 教练学员关系 | 关系表 | `(coach_id,user_id)` 唯一 |
| 7 | `health_record` | 健康指标记录 | 普通用户 | FK → `users` |
| 8 | `sleep_record` | 睡眠记录 | 普通用户 | FK → `users` |
| 9 | `sport_record` | 运动记录 | 普通用户 | FK → `users` |
| 10 | `health_plan` | 健康计划 | 普通用户 | FK → `users` |
| 11 | `doctor_advice` | 医生健康建议 | 医生业务 | FK → `doctor_user`、`users` |
| 12 | `medical_notice` | 体检通知 | 医生业务 | FK → `doctor_user`、`users` |
| 13 | `medical_record` | 医疗记录 | 医生业务 | FK → `doctor_user`、`users` |
| 14 | `sport_goal` | 运动目标 | 教练业务 | FK → `coach_user`、`users` |
| 15 | `training_plan` | 训练计划 | 教练业务 | FK → `coach_user`、`users` |
| 16 | `fitness_advice` | 健身建议 | 教练业务 | FK → `coach_user`、`users` |
| 17 | `health_article` | 健康科普文章 | 内容运营 | `is_show` |
| 18 | `notice` | 系统公告 | 内容运营 | `is_show` |
| 19 | `admin_operation_log` | 管理员操作日志 | 系统管理 | 已脱敏 |

---

## 二、四角色账号表

### 2.1 `users` — 普通用户

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | INT | PK, AUTO_INCREMENT | 用户 ID |
| `phone` | VARCHAR(20) | NOT NULL, UNIQUE | 手机号（登录账号） |
| `password_hash` | VARCHAR(255) | NOT NULL | Werkzeug 安全哈希（`pbkdf2:sha256`） |
| `nickname` | VARCHAR(50) | DEFAULT NULL | 昵称 |
| `avatar` | VARCHAR(255) | DEFAULT `'default_health.jpg'` | 头像**文件名** |
| `gender` | VARCHAR(10) | DEFAULT NULL | 性别 |
| `age` | INT | DEFAULT NULL | 年龄 |
| `height` | DECIMAL(5,1) | DEFAULT NULL | 身高(cm) |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

索引：`UNIQUE uk_users_phone(phone)`、`KEY idx_users_created_at(created_at)`

### 2.2 `admin_user` — 管理员

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | INT | PK, AUTO_INCREMENT | 管理员 ID |
| `admin_name` | VARCHAR(50) | NOT NULL, UNIQUE | 管理员账号 |
| `password_hash` | VARCHAR(255) | NOT NULL | Werkzeug 哈希 |
| `real_name` | VARCHAR(50) | DEFAULT NULL | 真实姓名 |
| `avatar` | VARCHAR(255) | DEFAULT `'default_admin.jpg'` | 头像文件名 |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

索引：`UNIQUE uk_admin_name(admin_name)`

### 2.3 `doctor_user` — 医生

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | INT | PK, AUTO_INCREMENT | 医生 ID |
| `doctor_name` | VARCHAR(50) | NOT NULL, UNIQUE | 医生账号 |
| `password_hash` | VARCHAR(255) | NOT NULL | Werkzeug 哈希 |
| `real_name` | VARCHAR(50) | DEFAULT NULL | 真实姓名 |
| `gender` | VARCHAR(10) | DEFAULT NULL | 性别 |
| `phone` | VARCHAR(20) | DEFAULT NULL | 手机号 |
| `specialty` | VARCHAR(100) | DEFAULT NULL | 专业方向 |
| `avatar` | VARCHAR(255) | DEFAULT `'default_doctor.jpg'` | 头像文件名 |
| `audit_status` | TINYINT(1) | DEFAULT 0 | **0 待审核 / 1 通过 / 2 拒绝** |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

索引：`UNIQUE uk_doctor_name(doctor_name)`、`KEY idx_doc_audit(audit_status)`、`KEY idx_doc_created(created_at)`

### 2.4 `coach_user` — 健身教练

字段结构与 `doctor_user` 一致（`coach_name`、`specialty`、`audit_status` 等），索引为
`UNIQUE uk_coach_name(coach_name)`、`KEY idx_coach_audit(audit_status)`、`KEY idx_coach_created(created_at)`。

---

## 三、关系表（权限校验的唯一依据）

### 3.1 `doctor_patient` — 医患关系

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | INT | PK, AUTO_INCREMENT | — |
| `doctor_id` | INT | NOT NULL, FK → `doctor_user.id` (ON DELETE CASCADE) | 医生 ID |
| `user_id` | INT | NOT NULL, FK → `users.id` (ON DELETE CASCADE) | 患者 ID |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 绑定时间 |

索引：**`UNIQUE uk_dp_relation(doctor_id, user_id)`**（防重复绑定）、`KEY idx_dp_user(user_id)`

### 3.2 `coach_student` — 教练学员关系

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | INT | PK, AUTO_INCREMENT | — |
| `coach_id` | INT | NOT NULL, FK → `coach_user.id` (ON DELETE CASCADE) | 教练 ID |
| `user_id` | INT | NOT NULL, FK → `users.id` (ON DELETE CASCADE) | 学员 ID |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 绑定时间 |

索引：**`UNIQUE uk_cs_relation(coach_id, user_id)`**、`KEY idx_cs_user(user_id)`

> 医生 / 教练每次读取或写入某个用户的数据前，服务层都会先查这两张表；
> 不存在绑定记录 → 直接返回 401，关系被管理员解除后也立即失效。

---

## 四、普通用户健康数据表

### 4.1 `health_record` — 健康指标

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | INT PK AI | — |
| `user_id` | INT NOT NULL, FK → `users.id` CASCADE | 所属用户 |
| `record_date` | DATE NOT NULL | 记录日期 |
| `weight` | DECIMAL(5,1) | 体重(kg) |
| `blood_pressure_high` | INT | 收缩压（高压） |
| `blood_pressure_low` | INT | 舒张压（低压） |
| `heart_rate` | INT | 心率 |
| `blood_sugar` | DECIMAL(4,1) | 血糖 |
| `created_at` | DATETIME | 创建时间 |

索引：`KEY idx_hr_user_date(user_id, record_date)`、`KEY idx_hr_created(created_at)`

### 4.2 `sleep_record` — 睡眠记录

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | INT PK AI | — |
| `user_id` | INT NOT NULL, FK → `users.id` CASCADE | 所属用户 |
| `sleep_date` | DATE NOT NULL | 睡眠日期 |
| `sleep_start` | DATETIME | 入睡时间 |
| `sleep_end` | DATETIME | 起床时间 |
| `sleep_duration` | INT | **睡眠时长(分钟，后端自动计算)** |
| `sleep_quality` | VARCHAR(20) | `很好 / 一般 / 较差`（后端强校验） |
| `created_at` | DATETIME | 创建时间 |

索引：`KEY idx_sr_user_date(user_id, sleep_date)`、`KEY idx_sr_created(created_at)`

### 4.3 `sport_record` — 运动记录

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | INT PK AI | — |
| `user_id` | INT NOT NULL, FK → `users.id` CASCADE | 所属用户 |
| `sport_date` | DATE NOT NULL | 运动日期 |
| `sport_type` | VARCHAR(50) | 运动类型 |
| `sport_duration` | INT | 运动时长(分钟) |
| `calorie` | INT | 消耗卡路里 |
| `remark` | VARCHAR(200) | 备注 |
| `created_at` | DATETIME | 创建时间 |

索引：`KEY idx_spr_user_date(user_id, sport_date)`、`KEY idx_spr_created(created_at)`

### 4.4 `health_plan` — 健康计划

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | INT PK AI | — |
| `user_id` | INT NOT NULL, FK → `users.id` CASCADE | 所属用户 |
| `plan_title` | VARCHAR(100) | 计划标题 |
| `plan_content` | TEXT | 计划内容 |
| `plan_start` / `plan_end` | DATE | 起止日期 |
| `plan_status` | TINYINT(1) | **0 进行中 / 1 已完成 / 2 已放弃** |
| `created_at` | DATETIME | 创建时间 |

索引：`KEY idx_hp_user(user_id)`、`KEY idx_hp_status(plan_status)`

---

## 五、医生业务表

### 5.1 `doctor_advice` — 健康建议

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | INT PK AI | — |
| `doctor_id` | INT NOT NULL, FK → `doctor_user.id` CASCADE | 医生 |
| `user_id` | INT NOT NULL, FK → `users.id` CASCADE | 患者 |
| `advice_content` | TEXT | 建议内容 |
| `created_at` | DATETIME | 创建时间 |

索引：`KEY idx_da_doctor(doctor_id)`、`KEY idx_da_user(user_id)`

### 5.2 `medical_notice` — 体检通知

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | INT PK AI | — |
| `doctor_id` | INT NOT NULL, FK → `doctor_user.id` CASCADE | 医生 |
| `user_id` | INT NOT NULL, FK → `users.id` CASCADE | 患者 |
| `notice_title` | VARCHAR(200) | 通知标题 |
| `notice_content` | TEXT | 通知内容 |
| `check_date` | DATETIME | 检查时间 |
| `created_at` | DATETIME | 创建时间 |

索引：`KEY idx_mn_doctor(doctor_id)`、`KEY idx_mn_user(user_id)`

### 5.3 `medical_record` — 医疗记录

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | INT PK AI | — |
| `doctor_id` | INT NOT NULL, FK → `doctor_user.id` CASCADE | 医生 |
| `user_id` | INT NOT NULL, FK → `users.id` CASCADE | 患者 |
| `record_title` | VARCHAR(200) | 记录标题 |
| `record_content` | TEXT | 记录内容 |
| `record_date` | DATE | 记录日期 |
| `created_at` | DATETIME | 创建时间 |

索引：`KEY idx_mr_doctor(doctor_id)`、`KEY idx_mr_user(user_id)`

---

## 六、教练业务表

### 6.1 `sport_goal` — 运动目标

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | INT PK AI | — |
| `coach_id` | INT NOT NULL, FK → `coach_user.id` CASCADE | 教练 |
| `user_id` | INT NOT NULL, FK → `users.id` CASCADE | 学员 |
| `goal_title` | VARCHAR(100) | 目标标题 |
| `goal_content` | TEXT | 目标内容 |
| `start_date` / `end_date` | DATE | 起止日期 |
| `goal_status` | TINYINT(1) | **0 进行中 / 1 已完成 / 2 已结束** |
| `created_at` | DATETIME | 创建时间 |

索引：`KEY idx_sg_coach(coach_id)`、`KEY idx_sg_user(user_id)`

### 6.2 `training_plan` — 训练计划

结构与 `sport_goal` 对称：`plan_title`、`plan_content`、`start_date`、`end_date`、`plan_status`（0/1/2）。
索引：`KEY idx_tp_coach(coach_id)`、`KEY idx_tp_user(user_id)`

### 6.3 `fitness_advice` — 健身建议

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | INT PK AI | — |
| `coach_id` | INT NOT NULL, FK → `coach_user.id` CASCADE | 教练 |
| `user_id` | INT NOT NULL, FK → `users.id` CASCADE | 学员 |
| `advice_content` | TEXT | 建议内容 |
| `created_at` | DATETIME | 创建时间 |

索引：`KEY idx_fa_coach(coach_id)`、`KEY idx_fa_user(user_id)`

---

## 七、内容运营与系统管理表

### 7.1 `health_article` — 健康科普文章

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | INT PK AI | — |
| `title` | VARCHAR(200) | 标题 |
| `cover_img` | VARCHAR(255) | 封面**文件名**（非完整 URL） |
| `content` | TEXT | 正文 |
| `author` | VARCHAR(50) | 作者 |
| `is_show` | TINYINT(1) | **1 显示 / 0 隐藏** |
| `publish_time` | DATETIME | 发布时间 |
| `created_at` | DATETIME | 创建时间 |

索引：`KEY idx_art_show_time(is_show, publish_time)`（小程序端按「可见 + 时间」查询）

### 7.2 `notice` — 系统公告

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | INT PK AI | — |
| `title` | VARCHAR(200) | 公告标题 |
| `content` | TEXT | 公告内容 |
| `publish_time` | DATETIME | 发布时间 |
| `is_show` | TINYINT(1) | 1 显示 / 0 隐藏 |
| `created_at` | DATETIME | 创建时间 |

索引：`KEY idx_notice_show_time(is_show, publish_time)`

### 7.3 `admin_operation_log` — 管理员操作日志

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | INT PK AI | — |
| `admin_id` | INT NOT NULL | 操作管理员 |
| `operation_type` | VARCHAR(50) | 操作类型（共 16 类，如登录、审核、绑定、重置密码…） |
| `operation_content` | VARCHAR(500) | 操作内容（**已脱敏**，不含密码/Token/密钥） |
| `target_type` | VARCHAR(50) | 目标类型 |
| `target_id` | INT | 目标 ID |
| `created_at` | DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP | 操作时间 |

索引：`KEY idx_log_admin(admin_id)`、`KEY idx_log_type(operation_type)`、`KEY idx_log_created(created_at)`

> 该表用于 12 模块的「系统管理」页与审计；写入前由 `utils/audit_log.py` 统一脱敏。

---

## 八、外键关系（20 条）

所有外键均为 `ON DELETE CASCADE`，删除用户/医生/教练时自动清理其业务数据，避免孤儿行。

```
health_record.user_id      → users.id
sleep_record.user_id       → users.id
sport_record.user_id       → users.id
health_plan.user_id        → users.id

doctor_patient.doctor_id   → doctor_user.id
doctor_patient.user_id     → users.id
doctor_advice.doctor_id    → doctor_user.id
doctor_advice.user_id      → users.id
medical_notice.doctor_id   → doctor_user.id
medical_notice.user_id     → users.id
medical_record.doctor_id   → doctor_user.id
medical_record.user_id     → users.id

coach_student.coach_id     → coach_user.id
coach_student.user_id      → users.id
sport_goal.coach_id        → coach_user.id
sport_goal.user_id         → users.id
training_plan.coach_id     → coach_user.id
training_plan.user_id      → users.id
fitness_advice.coach_id    → coach_user.id
fitness_advice.user_id     → users.id
```

---

## 九、四角色数据关系图

```
                      ┌──────────────┐
                      │  admin_user  │  管理员：全局监管、审核、绑定关系、
                      └──────┬───────┘  内容运营、操作日志
                             │ 写日志
                             ▼
                   admin_operation_log

        ┌─────────────┐   doctor_patient   ┌─────────────┐
        │ doctor_user │◄───────(绑定)──────►│    users    │
        └──────┬──────┘  UNIQUE(doc,user)   └──────┬──────┘
               │ 产出                              │ 归属
               ▼                                   │
   doctor_advice / medical_notice / medical_record  │
                                                    │
        ┌─────────────┐   coach_student            │
        │ coach_user  │◄───────(绑定)──────────────┤
        └──────┬──────┘  UNIQUE(coach,user)        │
               │ 产出                              │
               ▼                                   ▼
   sport_goal / training_plan / fitness_advice   health_record / sleep_record
                                                 sport_record  / health_plan
```

- **普通用户**：只读写自己的健康数据，且只能读取与自己绑定的医生/教练产出。
- **医生**：只读写与自己绑定的患者数据（依赖 `doctor_patient`）。
- **健身教练**：只读写与自己绑定的学员数据（依赖 `coach_student`）。
- **管理员**：跨角色只读监管 + 关系绑定/审核/内容运营，操作留痕。

---

## 十、初始化数据（`health_management.sql` 内置）

| 表 | 初始行 | 说明 |
| --- | --- | --- |
| `admin_user` | 1 | `admin` / `123456`（Werkzeug 哈希存储） |
| `doctor_user` | 3 | doctor001/002 已通过，doctor003 待审核 |
| `coach_user` | 3 | coach001/002 已通过，coach003 待审核 |
| `users` | 2 | 13800138001（小林同学）、13800138002（阿may） |
| `doctor_patient` | 1 | 演示绑定 |
| `coach_student` | 1 | 演示绑定 |
| 其余业务表 | 各 1 | 少量演示数据，保证各页面首屏非空 |

> 所有 `password_hash` 均为 Werkzeug `pbkdf2:sha256` 哈希，**无任何明文密码**（已由测试用例校验）。
> 正式使用前必须修改全部测试密码并替换 `JWT_SECRET`。
