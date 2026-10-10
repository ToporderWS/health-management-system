## 一、分专项汇总

| 专项 | 名称 | 用例数 | PASS | FAIL | 结论 |
|---|---|---:|---:|---:|---|
| A | A 四角色 Token 越权隔离 | 29 | 29 | 0 | PASS |
| B | B 医生-患者数据隔离 | 18 | 18 | 0 | PASS |
| C | C 教练-学员数据隔离 | 16 | 16 | 0 | PASS |
| D | D 注册审核状态机 | 20 | 20 | 0 | PASS |
| E | E 注册异常场景 | 16 | 16 | 0 | PASS |
| F | F 登录异常场景 | 24 | 24 | 0 | PASS |
| G | G 数据所有权（越权读写他人数据） | 16 | 16 | 0 | PASS |
| H | H 管理员监管权限边界 | 19 | 19 | 0 | PASS |
| I | I 操作日志 | 17 | 17 | 0 | PASS |
| J | J HTTP / 异常稳定性 | 7 | 7 | 0 | PASS |
| K | K 静态安全扫描 | 15 | 15 | 0 | PASS |
| **合计** | — | **197** | **197** | **0** | **ALL PASS** |

## 二、逐条明细

### A. A 四角色 Token 越权隔离（29/29 PASS）

| 编号 | 角色 | 目标 | 期望 | HTTP | code | 结果 |
|---|---|---|---|---:|---:|---|
| A-01 user Token -> user API | user | /user/info | HTTP 200（合法自身接口） | 200 | 200 | PASS |
| A-02 user Token -> doctor API（越权） | user | /doctor/patient/list | HTTP 401（跨角色必须拒绝） | 401 | 401 | PASS |
| A-03 user Token -> coach API（越权） | user | /coach/student/list | HTTP 401（跨角色必须拒绝） | 401 | 401 | PASS |
| A-04 user Token -> admin API（越权） | user | /admin/user/list | HTTP 401（跨角色必须拒绝） | 401 | 401 | PASS |
| A-05 doctor Token -> user API（越权） | doctor | /user/info | HTTP 401（跨角色必须拒绝） | 401 | 401 | PASS |
| A-06 doctor Token -> doctor API | doctor | /doctor/patient/list | HTTP 200（合法自身接口） | 200 | 200 | PASS |
| A-07 doctor Token -> coach API（越权） | doctor | /coach/student/list | HTTP 401（跨角色必须拒绝） | 401 | 401 | PASS |
| A-08 doctor Token -> admin API（越权） | doctor | /admin/user/list | HTTP 401（跨角色必须拒绝） | 401 | 401 | PASS |
| A-09 coach Token -> user API（越权） | coach | /user/info | HTTP 401（跨角色必须拒绝） | 401 | 401 | PASS |
| A-10 coach Token -> doctor API（越权） | coach | /doctor/patient/list | HTTP 401（跨角色必须拒绝） | 401 | 401 | PASS |
| A-11 coach Token -> coach API | coach | /coach/student/list | HTTP 200（合法自身接口） | 200 | 200 | PASS |
| A-12 coach Token -> admin API（越权） | coach | /admin/user/list | HTTP 401（跨角色必须拒绝） | 401 | 401 | PASS |
| A-13 admin Token -> user API（越权） | admin | /user/info | HTTP 401（跨角色必须拒绝） | 401 | 401 | PASS |
| A-14 admin Token -> doctor API（越权） | admin | /doctor/patient/list | HTTP 401（跨角色必须拒绝） | 401 | 401 | PASS |
| A-15 admin Token -> coach API（越权） | admin | /coach/student/list | HTTP 401（跨角色必须拒绝） | 401 | 401 | PASS |
| A-16 admin Token -> admin API | admin | /admin/user/list | HTTP 200（合法自身接口） | 200 | 200 | PASS |
| A-17 无 Token -> user API | none | /user/info | HTTP 401（未登录必须拒绝） | 401 | 401 | PASS |
| A-18 无 Token -> doctor API | none | /doctor/patient/list | HTTP 401（未登录必须拒绝） | 401 | 401 | PASS |
| A-19 无 Token -> coach API | none | /coach/student/list | HTTP 401（未登录必须拒绝） | 401 | 401 | PASS |
| A-20 无 Token -> admin API | none | /admin/user/list | HTTP 401（未登录必须拒绝） | 401 | 401 | PASS |
| A-21 伪造 Token(错误密钥) -> user API | forged | /user/info | HTTP 401（签名校验必须拒绝） | 401 | 401 | PASS |
| A-22 伪造 Token(错误密钥) -> doctor API | forged | /doctor/patient/list | HTTP 401（签名校验必须拒绝） | 401 | 401 | PASS |
| A-23 伪造 Token(错误密钥) -> coach API | forged | /coach/student/list | HTTP 401（签名校验必须拒绝） | 401 | 401 | PASS |
| A-24 伪造 Token(错误密钥) -> admin API | forged | /admin/user/list | HTTP 401（签名校验必须拒绝） | 401 | 401 | PASS |
| A-25 损坏 Token -> user API | broken | /user/info | HTTP 401（篡改必须拒绝） | 401 | 401 | PASS |
| A-26 损坏 Token -> doctor API | broken | /doctor/patient/list | HTTP 401（篡改必须拒绝） | 401 | 401 | PASS |
| A-27 损坏 Token -> coach API | broken | /coach/student/list | HTTP 401（篡改必须拒绝） | 401 | 401 | PASS |
| A-28 损坏 Token -> admin API | broken | /admin/user/list | HTTP 401（篡改必须拒绝） | 401 | 401 | PASS |
| A-29 医生 Token 无 Bearer 前缀 -> 管理员 API | doctor | /admin/user/list | HTTP 401 | 401 | 401 | PASS |

### B. B 医生-患者数据隔离（18/18 PASS）

| 编号 | 角色 | 目标 | 期望 | HTTP | code | 结果 |
|---|---|---|---|---:|---:|---|
| B-a 患者列表包含自己的患者 user=23 | 医生A | /doctor/patient/list | 列表含 user_id=23 | 200 | 200 | PASS |
| B-a 患者列表不含他人患者 user=24 | 医生A | /doctor/patient/list | 列表不含 user_id=24 | 200 | 200 | PASS |
| B-b 患者列表包含自己的患者 user=24 | 医生B | /doctor/patient/list | 列表含 user_id=24 | 200 | 200 | PASS |
| B-b 患者列表不含他人患者 user=23 | 医生B | /doctor/patient/list | 列表不含 user_id=23 | 200 | 200 | PASS |
| B-越权-01 医生A 直构 user_id=B 读患者详情 | doctor(A) | /doctor/patient/detail?user_id=B | HTTP 401（无医患关系必须拒绝） | 401 | 401 | PASS |
| B-越权-02 医生A 直构 user_id=B 读健康指标 | doctor(A) | /doctor/patient/health_data?user_id=B | HTTP 401（无医患关系必须拒绝） | 401 | 401 | PASS |
| B-越权-03 医生A 直构 user_id=B 读睡眠数据 | doctor(A) | /doctor/patient/sleep_data?user_id=B | HTTP 401（无医患关系必须拒绝） | 401 | 401 | PASS |
| B-越权-04 医生A 直构 user_id=B 读运动数据 | doctor(A) | /doctor/patient/sport_data?user_id=B | HTTP 401（无医患关系必须拒绝） | 401 | 401 | PASS |
| B-越权-05 医生A 直构 user_id=B 读健康计划 | doctor(A) | /doctor/patient/plan_data?user_id=B | HTTP 401（无医患关系必须拒绝） | 401 | 401 | PASS |
| B-越权-06 医生A 直构 user_id=B 读健康趋势 | doctor(A) | /doctor/patient/trend?user_id=B | HTTP 401（无医患关系必须拒绝） | 401 | 401 | PASS |
| B-正例-01 医生A 读自己患者健康指标 | doctor(A) | health_data?user_id=A | HTTP 200 | 200 | 200 | PASS |
| B-正例-02 医生A 确实读到患者A的健康记录 | doctor(A) | health_data | total>0 | 200 | 200 | PASS |
| B-越权-07 医生A 越权写患者B的健康建议 | doctor(A) | /doctor/advice/save | HTTP 400（关系校验拒绝） | 400 | 400 | PASS |
| B-越权-08 医生A 越权写患者B的体检通知 | doctor(A) | /doctor/medical_notice/save | HTTP 400（关系校验拒绝） | 400 | 400 | PASS |
| B-越权-09 医生A 越权写患者B的医疗记录 | doctor(A) | /doctor/medical_record/save | HTTP 400（关系校验拒绝） | 400 | 400 | PASS |
| B-DB-doctor_advice 医生A 对患者B 的doctor_advice写入为 0 条 | DB | doctor_advice WHERE doctor_id=A AND user_id=B | count=0 | 400 | 400 | PASS |
| B-DB-medical_notice 医生A 对患者B 的medical_notice写入为 0 条 | DB | medical_notice WHERE doctor_id=A AND user_id=B | count=0 | 400 | 400 | PASS |
| B-DB-medical_record 医生A 对患者B 的medical_record写入为 0 条 | DB | medical_record WHERE doctor_id=A AND user_id=B | count=0 | 400 | 400 | PASS |

### C. C 教练-学员数据隔离（16/16 PASS）

| 编号 | 角色 | 目标 | 期望 | HTTP | code | 结果 |
|---|---|---|---|---:|---:|---|
| C-a 学员列表包含自己的学员 user=23 | 教练A | /coach/student/list | 含 user_id=23 | 200 | 200 | PASS |
| C-a 学员列表不含他人学员 user=24 | 教练A | /coach/student/list | 不含 user_id=24 | 200 | 200 | PASS |
| C-b 学员列表包含自己的学员 user=24 | 教练B | /coach/student/list | 含 user_id=24 | 200 | 200 | PASS |
| C-b 学员列表不含他人学员 user=23 | 教练B | /coach/student/list | 不含 user_id=23 | 200 | 200 | PASS |
| C-越权-01 教练A 直构 user_id=B 读学员详情 | coach(A) | /coach/student/detail?user_id=B | HTTP 401（无师生关系必须拒绝） | 401 | 401 | PASS |
| C-越权-02 教练A 直构 user_id=B 读学员运动数据 | coach(A) | /coach/student/sport_data?user_id=B | HTTP 401（无师生关系必须拒绝） | 401 | 401 | PASS |
| C-越权-03 教练A 直构 user_id=B 读学员运动统计 | coach(A) | /coach/student/statistics?user_id=B | HTTP 401（无师生关系必须拒绝） | 401 | 401 | PASS |
| C-正例-01 教练A 读自己学员运动数据 | coach(A) | sport_data?user_id=A | HTTP 200 | 200 | 200 | PASS |
| C-越权-04 教练A 越权写学员B的运动目标 | coach(A) | /coach/sport_goal/save | HTTP 400（关系校验拒绝） | 400 | 400 | PASS |
| C-越权-05 教练A 越权写学员B的训练计划 | coach(A) | /coach/training_plan/save | HTTP 400（关系校验拒绝） | 400 | 400 | PASS |
| C-越权-06 教练A 越权写学员B的健身建议 | coach(A) | /coach/fitness_advice/save | HTTP 400（关系校验拒绝） | 400 | 400 | PASS |
| C-越权-07 教练A 改教练B 的运动目标(id=13) | coach(A) | /coach/sport_goal/update_status | HTTP 400（目标不属于自己） | 400 | 400 | PASS |
| C-越权-08 教练A 改教练B 的训练计划(id=14) | coach(A) | /coach/training_plan/update_status | HTTP 400（计划不属于自己） | 400 | 400 | PASS |
| C-DB-sport_goal 教练A 对学员B 的写入为 0 条 | DB | sport_goal | count=0 | 400 | 400 | PASS |
| C-DB-training_plan 教练A 对学员B 的写入为 0 条 | DB | training_plan | count=0 | 400 | 400 | PASS |
| C-DB-fitness_advice 教练A 对学员B 的写入为 0 条 | DB | fitness_advice | count=0 | 400 | 400 | PASS |

### D. D 注册审核状态机（20/20 PASS）

| 编号 | 角色 | 目标 | 期望 | HTTP | code | 结果 |
|---|---|---|---|---:|---:|---|
| D-01 新注册医生 audit_status 强制为 0 | doctor | /doctor/register | audit_status=0 | 200 | 200 | PASS |
| D-02 新注册教练 audit_status 强制为 0 | coach | /coach/register | audit_status=0 | 200 | 200 | PASS |
| D-03 医生注册恶意提交 audit_status=1 仍存 0 | doctor | /doctor/register | DB audit_status=0 | 200 | 200 | PASS |
| D-04 医生注册忽略客户端 id（未被覆盖为 1） | doctor | /doctor/register | id 为自增新值 | 200 | 200 | PASS |
| D-05 医生注册忽略客户端 created_at | doctor | /doctor/register | created_at 为 NOW() | 200 | 200 | PASS |
| D-06 audit_status=0 医生不允许登录 | doctor | /doctor/login | HTTP 400 待审核拦截 | 400 | 400 | PASS |
| D-07 audit_status=0 教练不允许登录 | coach | /coach/login | HTTP 400 待审核拦截 | 400 | 400 | PASS |
| D-08 管理员可把待审核(0)医生改为审核拒绝(2) | admin | /admin/doctor/audit | DB audit_status=2 | 200 | 200 | PASS |
| D-09 audit_status=2 医生不允许登录 | doctor | /doctor/login | HTTP 400 拒绝登录 | 400 | 400 | PASS |
| D-10 audit_status=2 教练不允许登录 | coach | /coach/login | HTTP 400 拒绝登录 | 400 | 400 | PASS |
| D-11 审核不可逆：拒绝(2)后不得再改为通过(1) | admin | /admin/doctor/audit | HTTP 400 该申请已完成审核，无需重复操作 | 400 | 400 | PASS |
| D-12 拒绝后状态保持 2（未被改写） | DB | doctor_user | audit_status=2 | 400 | 400 | PASS |
| D-13 新注册医生初始 audit_status=0 | doctor | /doctor/register | audit_status=0 | 200 | 200 | PASS |
| D-14 待审核(0) -> 审核通过(1) 允许 | admin | /admin/doctor/audit | HTTP 200（0->1 合法） | 200 | 200 | PASS |
| D-15 审核通过(1)后医生可登录 | doctor | /doctor/login | HTTP 200 | 200 | 200 | PASS |
| D-16 医生登录返回非空 token | doctor | /doctor/login | token 非空 | 200 | 200 | PASS |
| D-17 待审核(0) -> 审核通过(1) 教练允许 | admin | /admin/coach/audit | HTTP 200（0->1 合法） | 200 | 200 | PASS |
| D-18 审核通过(1)后教练可登录 | coach | /coach/login | HTTP 200 | 200 | 200 | PASS |
| D-19 教练登录返回非空 token | coach | /coach/login | token 非空 | 200 | 200 | PASS |
| D-20 已审核通过(1)的申请不可重复审核 | admin | /admin/doctor/audit | HTTP 400 该申请已完成审核，无需重复操作 | 400 | 400 | PASS |

### E. E 注册异常场景（16/16 PASS）

| 编号 | 角色 | 目标 | 期望 | HTTP | code | 结果 |
|---|---|---|---|---:|---:|---|
| E-01 普通用户重复手机号注册 | anon | /user/register | HTTP 400 该手机号已注册 | 400 | 400 | PASS |
| E-02 医生重复 doctor_name 注册 | anon | /doctor/register | HTTP 400 账号已注册 | 400 | 400 | PASS |
| E-03 教练重复 coach_name 注册 | anon | /coach/register | HTTP 400 账号已注册 | 400 | 400 | PASS |
| E-04 普通用户空手机号注册 | anon | /user/register | HTTP 400 手机号校验 | 400 | 400 | PASS |
| E-05 普通用户空密码注册 | anon | /user/register | HTTP 400 密码校验 | 400 | 400 | PASS |
| E-06 普通用户空昵称注册 | anon | /user/register | HTTP 400 昵称校验 | 400 | 400 | PASS |
| E-07 非法手机号注册 | anon | /user/register | HTTP 400 手机号格式 | 400 | 400 | PASS |
| E-08 非法性别取值注册 | anon | /user/register | HTTP 400 性别取值不合法 | 400 | 400 | PASS |
| E-09 密码长度不足注册 | anon | /user/register | HTTP 400 密码长度 | 400 | 400 | PASS |
| E-10 users 表不存在 confirm_password 列 | DB | SHOW COLUMNS FROM users | 无该列 | 400 | 400 | PASS |
| E-11 doctor_user 表不存在 confirm_password 列 | DB | SHOW COLUMNS FROM doctor_user | 无该列 | 400 | 400 | PASS |
| E-12 coach_user 表不存在 confirm_password 列 | DB | SHOW COLUMNS FROM coach_user | 无该列 | 400 | 400 | PASS |
| E-13 普通用户注册忽略恶意 id=99999 | anon | /user/register | 自增新 id | 200 | 200 | PASS |
| E-14 普通用户注册忽略恶意 created_at | anon | /user/register | created_at=NOW() | 200 | 200 | PASS |
| E-15 users 表无 role 字段（结构上无法提权） | DB | SHOW COLUMNS FROM users | 无 role 列 | 200 | 200 | PASS |
| E-16 users 表无 audit_status 字段 | DB | SHOW COLUMNS FROM users | 无 audit_status 列 | 200 | 200 | PASS |

### F. F 登录异常场景（24/24 PASS）

| 编号 | 角色 | 目标 | 期望 | HTTP | code | 结果 |
|---|---|---|---|---:|---:|---|
| F-01 user 正确账号+错误密码 | user | /user/login | HTTP 400 登录失败 | 400 | 400 | PASS |
| F-01* user 错误密码响应无敏感信息泄露 | user | /user/login | 无 password_hash/JWT/SQL/traceback | 400 | 400 | PASS |
| F-02 doctor 正确账号+错误密码 | doctor | /doctor/login | HTTP 400 登录失败 | 400 | 400 | PASS |
| F-02* doctor 错误密码响应无敏感信息泄露 | doctor | /doctor/login | 无 password_hash/JWT/SQL/traceback | 400 | 400 | PASS |
| F-03 coach 正确账号+错误密码 | coach | /coach/login | HTTP 400 登录失败 | 400 | 400 | PASS |
| F-03* coach 错误密码响应无敏感信息泄露 | coach | /coach/login | 无 password_hash/JWT/SQL/traceback | 400 | 400 | PASS |
| F-04 admin 正确账号+错误密码 | admin | /admin/login | HTTP 400 登录失败 | 400 | 400 | PASS |
| F-04* admin 错误密码响应无敏感信息泄露 | admin | /admin/login | 无 password_hash/JWT/SQL/traceback | 400 | 400 | PASS |
| F-05 user 不存在账号 | user | /user/login | HTTP 400 登录失败 | 400 | 400 | PASS |
| F-06 doctor 不存在账号 | doctor | /doctor/login | HTTP 400 登录失败 | 400 | 400 | PASS |
| F-07 coach 不存在账号 | coach | /coach/login | HTTP 400 登录失败 | 400 | 400 | PASS |
| F-08 admin 不存在账号 | admin | /admin/login | HTTP 400 登录失败 | 400 | 400 | PASS |
| F-09 user 空账号 | user | /user/login | HTTP 400 登录失败 | 400 | 400 | PASS |
| F-10 doctor 空账号 | doctor | /doctor/login | HTTP 400 登录失败 | 400 | 400 | PASS |
| F-11 coach 空账号 | coach | /coach/login | HTTP 400 登录失败 | 400 | 400 | PASS |
| F-12 admin 空账号 | admin | /admin/login | HTTP 400 登录失败 | 400 | 400 | PASS |
| F-13 user 空密码 | user | /user/login | HTTP 400 登录失败 | 400 | 400 | PASS |
| F-14 doctor 空密码 | doctor | /doctor/login | HTTP 400 登录失败 | 400 | 400 | PASS |
| F-15 coach 空密码 | coach | /coach/login | HTTP 400 登录失败 | 400 | 400 | PASS |
| F-16 admin 空密码 | admin | /admin/login | HTTP 400 登录失败 | 400 | 400 | PASS |
| F-17 未审核医生登录 | doctor | /doctor/login | HTTP 400 待审核拦截 | 400 | 400 | PASS |
| F-17* 未审核登录响应无敏感信息 | doctor | /doctor/login | 无敏感信息 | 400 | 400 | PASS |
| F-18 审核拒绝医生登录 | doctor | /doctor/login | HTTP 400 拒绝登录 | 400 | 400 | PASS |
| F-19 审核拒绝教练登录 | coach | /coach/login | HTTP 400 拒绝登录 | 400 | 400 | PASS |

### G. G 数据所有权（越权读写他人数据）（16/16 PASS）

| 编号 | 角色 | 目标 | 期望 | HTTP | code | 结果 |
|---|---|---|---|---:|---:|---|
| G-my_list 用户A 篡改 user_id=B 读取「健康指标」 | user(A) | /health_record/my_list?user_id=B | 不返回用户B的数据（user_id 一律取自 Token） | 200 | 200 | PASS |
| G-my_list 用户A 篡改 user_id=B 读取「睡眠记录」 | user(A) | /sleep_record/my_list?user_id=B | 不返回用户B的数据（user_id 一律取自 Token） | 200 | 200 | PASS |
| G-my_list 用户A 篡改 user_id=B 读取「运动记录」 | user(A) | /sport_record/my_list?user_id=B | 不返回用户B的数据（user_id 一律取自 Token） | 200 | 200 | PASS |
| G-my_list 用户A 篡改 user_id=B 读取「健康计划」 | user(A) | /health_plan/my_list?user_id=B | 不返回用户B的数据（user_id 一律取自 Token） | 200 | 200 | PASS |
| G-statistics 用户A 篡改 user_id=B 读取「数据报告」 | user(A) | /report/statistics?user_id=B | 不返回用户B的数据（user_id 一律取自 Token） | 200 | 200 | PASS |
| G-doctor_advice 用户A 篡改 user_id=B 读取「医生建议」 | user(A) | /user/doctor_advice?user_id=B | 不返回用户B的数据（user_id 一律取自 Token） | 200 | 200 | PASS |
| G-medical_notice 用户A 篡改 user_id=B 读取「体检通知」 | user(A) | /user/medical_notice?user_id=B | 不返回用户B的数据（user_id 一律取自 Token） | 200 | 200 | PASS |
| G-medical_record 用户A 篡改 user_id=B 读取「医疗记录」 | user(A) | /user/medical_record?user_id=B | 不返回用户B的数据（user_id 一律取自 Token） | 200 | 200 | PASS |
| G-sport_goal 用户A 篡改 user_id=B 读取「运动目标」 | user(A) | /user/sport_goal?user_id=B | 不返回用户B的数据（user_id 一律取自 Token） | 200 | 200 | PASS |
| G-training_plan 用户A 篡改 user_id=B 读取「训练计划」 | user(A) | /user/training_plan?user_id=B | 不返回用户B的数据（user_id 一律取自 Token） | 200 | 200 | PASS |
| G-fitness_advice 用户A 篡改 user_id=B 读取「健身建议」 | user(A) | /user/fitness_advice?user_id=B | 不返回用户B的数据（user_id 一律取自 Token） | 200 | 200 | PASS |
| G-写-01 用户A 提交 user_id=B 新增健康记录 | user(A) | /health_record/add | HTTP 200（接口忽略客户端 user_id） | 200 | 200 | PASS |
| G-写-02 新增记录归属用户A（而非B） | DB | health_record | user_id=23（A） | 200 | 200 | PASS |
| G-写-03 用户A 附 user_id=B 创建计划仍归属用户A | DB | health_plan | user_id=A | 200 | 200 | PASS |
| G-写-04 用户A 改用户B 的计划状态(id=20) | user(A) | /health_plan/update_status | HTTP 400（计划不属于自己） | 400 | 400 | PASS |
| G-写-05 用户B 的计划状态未被篡改 | DB | health_plan | plan_status=0 | 400 | 400 | PASS |

### H. H 管理员监管权限边界（19/19 PASS）

| 编号 | 角色 | 目标 | 期望 | HTTP | code | 结果 |
|---|---|---|---|---:|---:|---|
| H-list 管理员监管查看「原始健康指标」 | admin | /admin/health_record/list | HTTP 200（监管只读） | 200 | 200 | PASS |
| H-list 管理员监管查看「睡眠记录」 | admin | /admin/sleep_record/list | HTTP 200（监管只读） | 200 | 200 | PASS |
| H-list 管理员监管查看「运动记录」 | admin | /admin/sport_record/list | HTTP 200（监管只读） | 200 | 200 | PASS |
| H-list 管理员监管查看「用户健康计划」 | admin | /admin/health_plan/list | HTTP 200（监管只读） | 200 | 200 | PASS |
| H-list 管理员监管查看「医生健康建议」 | admin | /admin/doctor_advice/list | HTTP 200（监管只读） | 200 | 200 | PASS |
| H-list 管理员监管查看「体检通知」 | admin | /admin/medical_notice/list | HTTP 200（监管只读） | 200 | 200 | PASS |
| H-list 管理员监管查看「医疗记录」 | admin | /admin/medical_record/list | HTTP 200（监管只读） | 200 | 200 | PASS |
| H-list 管理员监管查看「教练运动目标」 | admin | /admin/sport_goal/list | HTTP 200（监管只读） | 200 | 200 | PASS |
| H-list 管理员监管查看「训练计划」 | admin | /admin/training_plan/list | HTTP 200（监管只读） | 200 | 200 | PASS |
| H-list 管理员监管查看「健身建议」 | admin | /admin/fitness_advice/list | HTTP 200（监管只读） | 200 | 200 | PASS |
| H-越权-01 管理员 Token 冒充业务角色写医生健康建议 | admin | /doctor/advice/save | HTTP 401（Token 类型不匹配） | 401 | 401 | PASS |
| H-越权-02 管理员 Token 冒充业务角色写体检通知 | admin | /doctor/medical_notice/save | HTTP 401（Token 类型不匹配） | 401 | 401 | PASS |
| H-越权-03 管理员 Token 冒充业务角色写医疗记录 | admin | /doctor/medical_record/save | HTTP 401（Token 类型不匹配） | 401 | 401 | PASS |
| H-越权-04 管理员 Token 冒充业务角色写运动目标 | admin | /coach/sport_goal/save | HTTP 401（Token 类型不匹配） | 401 | 401 | PASS |
| H-越权-05 管理员 Token 冒充业务角色写训练计划 | admin | /coach/training_plan/save | HTTP 401（Token 类型不匹配） | 401 | 401 | PASS |
| H-越权-06 管理员 Token 冒充业务角色写健身建议 | admin | /coach/fitness_advice/save | HTTP 401（Token 类型不匹配） | 401 | 401 | PASS |
| H-越权-07 管理员 Token 写用户健康记录 | admin | /health_record/add | HTTP 401（无此权限） | 401 | 401 | PASS |
| H-越权-08 管理员 Token 写用户健康计划 | admin | /health_plan/add | HTTP 401（无此权限） | 401 | 401 | PASS |
| H-静态-01 管理员路由中不存在健康/专业业务写入接口 | static | routes/admin.py | 无任何用户原始数据写接口 | 401 | 401 | PASS |

### I. I 操作日志（17/17 PASS）

| 编号 | 角色 | 目标 | 期望 | HTTP | code | 结果 |
|---|---|---|---|---:|---:|---|
| I-01 管理员解除医患关系（删除前先确认存在） | admin | /admin/doctor/unbind_patient | HTTP 200 | 200 | 200 | PASS |
| I-02 管理员恢复医患绑定（消除测试副作用） | admin | /admin/doctor/bind_patient | HTTP 200 | 200 | 200 | PASS |
| I-03 管理员解除教练学员关系 | admin | /admin/coach/unbind_student | HTTP 200 | 200 | 200 | PASS |
| I-04 管理员恢复教练学员绑定（消除测试副作用） | admin | /admin/coach/bind_student | HTTP 200 | 200 | 200 | PASS |
| I-05 管理员重置医生登录密码 | admin | /admin/doctor/reset_pwd | HTTP 200 | 200 | 200 | PASS |
| I-06 管理员重置教练登录密码 | admin | /admin/coach/reset_pwd | HTTP 200 | 200 | 200 | PASS |
| I-07 密码重置后医生仍可用原口令登录 | doctor | /doctor/login | HTTP 200 | 200 | 200 | PASS |
| I-日志 存在「医生审核通过」审计记录 | DB | admin_operation_log | admin_operation_log 含该 operation_type | 200 | 200 | PASS |
| I-日志 存在「教练审核通过」审计记录 | DB | admin_operation_log | admin_operation_log 含该 operation_type | 200 | 200 | PASS |
| I-日志 存在「医患绑定」审计记录 | DB | admin_operation_log | admin_operation_log 含该 operation_type | 200 | 200 | PASS |
| I-日志 存在「医患解绑」审计记录 | DB | admin_operation_log | admin_operation_log 含该 operation_type | 200 | 200 | PASS |
| I-日志 存在「教练学员绑定」审计记录 | DB | admin_operation_log | admin_operation_log 含该 operation_type | 200 | 200 | PASS |
| I-日志 存在「教练学员解绑」审计记录 | DB | admin_operation_log | admin_operation_log 含该 operation_type | 200 | 200 | PASS |
| I-日志 存在「医生密码重置」审计记录 | DB | admin_operation_log | admin_operation_log 含该 operation_type | 200 | 200 | PASS |
| I-日志 存在「教练密码重置」审计记录 | DB | admin_operation_log | admin_operation_log 含该 operation_type | 200 | 200 | PASS |
| I-08 操作日志不含明文密码/哈希/JWT/Secret/DB密码 | DB | admin_operation_log | 无敏感信息 | 200 | 200 | PASS |
| I-09 操作日志不含 password_hash 字样 | DB | admin_operation_log | 无 password_hash | 200 | 200 | PASS |

### J. J HTTP / 异常稳定性（7/7 PASS）

| 编号 | 角色 | 目标 | 期望 | HTTP | code | 结果 |
|---|---|---|---|---:|---:|---|
| J-01 全部请求未出现 HTTP 500 | all | REQUESTS | 0 个 500 |  |  | PASS |
| J-02 无连接层异常（后端进程全程存活） | all | REQUESTS | 0 个连接错误 |  |  | PASS |
| J-03 所有响应均为统一 {code,msg,data} 契约（无 HTML 错误页） | all | REQUESTS | 无裸文本/HTML 响应 |  |  | PASS |
| J-04 全部响应无敏感信息泄露（traceback/SQL/哈希/密钥；登录下发 token 除外） | all | REQUESTS | 无泄露 |  |  | PASS |
| J-05 经历全部异常请求后后端仍存活 | anon | /api/health | HTTP 200（service+database 均 ok） | 200 | 200 | PASS |
| J-06 /api/health 报告数据库连通 | anon | /api/health | database=ok | 200 | 200 | PASS |
| J-07 不存在接口返回统一契约而非 HTML 404 | anon | /no_such_api_sec_test | HTTP 400 + {code,msg,data} | 400 | 400 | PASS |

### K. K 静态安全扫描（15/15 PASS）

| 编号 | 角色 | 目标 | 期望 | HTTP | code | 结果 |
|---|---|---|---|---:|---:|---|
| K-01 源码中不存在 :5000 端口硬编码 | static | :5000 | 0 处命中 |  |  | PASS |
| K-02 源码中不存在 :5001 端口硬编码 | static | :5001 | 0 处命中 |  |  | PASS |
| K-03 前端源码不存在 password_hash | static | frontend | 0 处命中 |  |  | PASS |
| K-04 前端源码不含 JWT Secret / JWT_SECRET | static | frontend | 0 处命中 |  |  | PASS |
| K-05 前端源码不含数据库连接配置 | static | frontend | 0 处命中 |  |  | PASS |
| K-06 前端源码不含硬编码 token / 口令字面量 | static | frontend | 0 处命中 |  |  | PASS |
| K-07 前端代码中不含硬编码角色/审核绕过 | static | frontend | 0 处命中（中文文案行不计） |  |  | PASS |
| K-08 后端 auth.py 同时具备 Token 类型隔离与关系校验 | static | backend/utils/auth.py | token_type 隔离 + doctor_has_patient + coach_has_student |  |  | PASS |
| K-09 前端存在路由守卫（展示层过滤，非唯一防线） | static | management-web/src/router | 存在 beforeEach 守卫 |  |  | PASS |
| K-10 源码中无 TODO/FIXME/XXX 遗留标记 | static | all | 0 处命中 |  |  | PASS |
| K-11 源码中无 mock/桩数据替代核心业务 | static | all | 0 处命中 |  |  | PASS |
| K-12 前端 Token key 与角色映射一一对应（无串用） | static | src/utils/auth.js | 四类 key 与 ROLE 映射正确 |  |  | PASS |
| K-13 后端 TOKEN_ROLE_MAP 显式定义四类映射 | static | backend/config.py | 存在 TOKEN_ROLE_MAP 且含四类 |  |  | PASS |
| K-14 管理端工程内不含 .env 密钥泄露 | static | management-web | 0 处命中 |  |  | PASS |
| K-15 后端路由/服务未发现写死中文数据的假接口 | static | backend | 0 处命中 |  |  | PASS |
