-- =============================================================
-- 个人健康管理系统 · Personal Health Management System
-- 版本：V3.2 FINAL
-- 数据库：health_management   字符集：utf8mb4
-- 说明：本文件为数据库唯一初始化脚本，包含全部表结构与初始化测试账号
-- =============================================================

CREATE DATABASE IF NOT EXISTS `health_management`
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_general_ci;

USE `health_management`;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- -------------------------------------------------------------
-- 1. users 普通用户表（role = 0）
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
    `id`            INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    `phone`         VARCHAR(20)  NOT NULL COMMENT '手机号（登录账号）',
    `password_hash` VARCHAR(255) NOT NULL COMMENT 'Werkzeug 安全哈希密码',
    `nickname`      VARCHAR(50)  DEFAULT NULL COMMENT '昵称',
    `avatar`        VARCHAR(255) DEFAULT 'default_health.jpg' COMMENT '头像文件名',
    `gender`        VARCHAR(10)  DEFAULT NULL COMMENT '性别',
    `age`           INT          DEFAULT NULL COMMENT '年龄',
    `height`        DECIMAL(5,1) DEFAULT NULL COMMENT '身高(cm)',
    `created_at`    DATETIME     DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY `uk_users_phone` (`phone`),
    KEY `idx_users_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='普通用户表';

-- -------------------------------------------------------------
-- 2. admin_user 管理员表（role = 3，禁止公开注册）
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `admin_user`;
CREATE TABLE `admin_user` (
    `id`            INT AUTO_INCREMENT PRIMARY KEY COMMENT '管理员ID',
    `admin_name`    VARCHAR(50)  NOT NULL COMMENT '管理员账号',
    `password_hash` VARCHAR(255) NOT NULL COMMENT 'Werkzeug 安全哈希密码',
    `real_name`     VARCHAR(50)  DEFAULT NULL COMMENT '真实姓名',
    `avatar`        VARCHAR(255) DEFAULT 'default_admin.jpg' COMMENT '头像文件名',
    `created_at`    DATETIME     DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY `uk_admin_name` (`admin_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='管理员表';

-- -------------------------------------------------------------
-- 3. health_record 健康指标记录表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `health_record`;
CREATE TABLE `health_record` (
    `id`                  INT AUTO_INCREMENT PRIMARY KEY,
    `user_id`             INT          NOT NULL COMMENT '所属用户',
    `record_date`         DATE         NOT NULL COMMENT '记录日期',
    `weight`              DECIMAL(5,1) DEFAULT NULL COMMENT '体重(kg)',
    `blood_pressure_high` INT          DEFAULT NULL COMMENT '收缩压(高压)',
    `blood_pressure_low`  INT          DEFAULT NULL COMMENT '舒张压(低压)',
    `heart_rate`          INT          DEFAULT NULL COMMENT '心率',
    `blood_sugar`         DECIMAL(4,1) DEFAULT NULL COMMENT '血糖',
    `created_at`          DATETIME     DEFAULT CURRENT_TIMESTAMP,
    KEY `idx_hr_user_date` (`user_id`, `record_date`),
    KEY `idx_hr_created` (`created_at`),
    CONSTRAINT `fk_hr_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='健康指标记录表';

-- -------------------------------------------------------------
-- 4. sleep_record 睡眠记录表
--    sleep_duration 由后端根据 sleep_end - sleep_start 自动计算（分钟）
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `sleep_record`;
CREATE TABLE `sleep_record` (
    `id`             INT AUTO_INCREMENT PRIMARY KEY,
    `user_id`        INT         NOT NULL COMMENT '所属用户',
    `sleep_date`     DATE        NOT NULL COMMENT '睡眠日期',
    `sleep_start`    DATETIME    DEFAULT NULL COMMENT '入睡时间',
    `sleep_end`      DATETIME    DEFAULT NULL COMMENT '起床时间',
    `sleep_duration` INT         DEFAULT NULL COMMENT '睡眠时长(分钟,后端计算)',
    `sleep_quality`  VARCHAR(20) DEFAULT NULL COMMENT '睡眠质量:很好/一般/较差',
    `created_at`     DATETIME    DEFAULT CURRENT_TIMESTAMP,
    KEY `idx_sr_user_date` (`user_id`, `sleep_date`),
    KEY `idx_sr_created` (`created_at`),
    CONSTRAINT `fk_sr_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='睡眠记录表';

-- -------------------------------------------------------------
-- 5. sport_record 运动记录表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `sport_record`;
CREATE TABLE `sport_record` (
    `id`             INT AUTO_INCREMENT PRIMARY KEY,
    `user_id`        INT          NOT NULL COMMENT '所属用户',
    `sport_date`     DATE         NOT NULL COMMENT '运动日期',
    `sport_type`     VARCHAR(50)  DEFAULT NULL COMMENT '运动类型',
    `sport_duration` INT          DEFAULT NULL COMMENT '运动时长(分钟)',
    `calorie`        INT          DEFAULT NULL COMMENT '消耗卡路里',
    `remark`         VARCHAR(200) DEFAULT NULL COMMENT '备注',
    `created_at`     DATETIME     DEFAULT CURRENT_TIMESTAMP,
    KEY `idx_spr_user_date` (`user_id`, `sport_date`),
    KEY `idx_spr_created` (`created_at`),
    CONSTRAINT `fk_spr_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='运动记录表';

-- -------------------------------------------------------------
-- 6. health_plan 健康计划表
--    状态：0进行中 1已完成 2已放弃
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `health_plan`;
CREATE TABLE `health_plan` (
    `id`           INT AUTO_INCREMENT PRIMARY KEY,
    `user_id`      INT          NOT NULL COMMENT '所属用户',
    `plan_title`   VARCHAR(100) DEFAULT NULL COMMENT '计划标题',
    `plan_content` TEXT         COMMENT '计划内容',
    `plan_start`   DATE         DEFAULT NULL COMMENT '开始日期',
    `plan_end`     DATE         DEFAULT NULL COMMENT '结束日期',
    `plan_status`  TINYINT(1)   DEFAULT 0 COMMENT '0进行中 1已完成 2已放弃',
    `created_at`   DATETIME     DEFAULT CURRENT_TIMESTAMP,
    KEY `idx_hp_user` (`user_id`),
    KEY `idx_hp_status` (`plan_status`),
    CONSTRAINT `fk_hp_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='健康计划表';

-- -------------------------------------------------------------
-- 7. health_article 健康科普文章表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `health_article`;
CREATE TABLE `health_article` (
    `id`           INT AUTO_INCREMENT PRIMARY KEY,
    `title`        VARCHAR(200) DEFAULT NULL COMMENT '标题',
    `cover_img`    VARCHAR(255) DEFAULT NULL COMMENT '封面文件名',
    `content`      TEXT         COMMENT '正文',
    `author`       VARCHAR(50)  DEFAULT NULL COMMENT '作者',
    `is_show`      TINYINT(1)   DEFAULT 1 COMMENT '1显示 0隐藏',
    `publish_time` DATETIME     DEFAULT NULL COMMENT '发布时间',
    `created_at`   DATETIME     DEFAULT CURRENT_TIMESTAMP,
    KEY `idx_art_show_time` (`is_show`, `publish_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='健康科普文章表';

-- -------------------------------------------------------------
-- 8. notice 系统公告表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `notice`;
CREATE TABLE `notice` (
    `id`           INT AUTO_INCREMENT PRIMARY KEY,
    `title`        VARCHAR(200) DEFAULT NULL COMMENT '公告标题',
    `content`      TEXT         COMMENT '公告内容',
    `publish_time` DATETIME     DEFAULT NULL COMMENT '发布时间',
    `is_show`      TINYINT(1)   DEFAULT 1 COMMENT '1显示 0隐藏',
    `created_at`   DATETIME     DEFAULT CURRENT_TIMESTAMP,
    KEY `idx_notice_show_time` (`is_show`, `publish_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统公告表';

-- -------------------------------------------------------------
-- 9. doctor_user 医生表（role = 1）
--    audit_status：0待审核 1审核通过 2审核拒绝
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `doctor_user`;
CREATE TABLE `doctor_user` (
    `id`            INT AUTO_INCREMENT PRIMARY KEY,
    `doctor_name`   VARCHAR(50)  NOT NULL COMMENT '医生账号',
    `password_hash` VARCHAR(255) NOT NULL COMMENT 'Werkzeug 安全哈希密码',
    `real_name`     VARCHAR(50)  DEFAULT NULL COMMENT '真实姓名',
    `gender`        VARCHAR(10)  DEFAULT NULL COMMENT '性别',
    `phone`         VARCHAR(20)  DEFAULT NULL COMMENT '手机号',
    `specialty`     VARCHAR(100) DEFAULT NULL COMMENT '专业方向',
    `avatar`        VARCHAR(255) DEFAULT 'default_doctor.jpg' COMMENT '头像文件名',
    `audit_status`  TINYINT(1)   DEFAULT 0 COMMENT '0待审核 1通过 2拒绝',
    `created_at`    DATETIME     DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `uk_doctor_name` (`doctor_name`),
    KEY `idx_doc_audit` (`audit_status`),
    KEY `idx_doc_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='医生表';

-- -------------------------------------------------------------
-- 10. doctor_patient 医患关系表（doctor_id + user_id 唯一）
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `doctor_patient`;
CREATE TABLE `doctor_patient` (
    `id`         INT AUTO_INCREMENT PRIMARY KEY,
    `doctor_id`  INT      NOT NULL COMMENT '医生ID',
    `user_id`    INT      NOT NULL COMMENT '患者(普通用户)ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `uk_dp_relation` (`doctor_id`, `user_id`),
    KEY `idx_dp_user` (`user_id`),
    CONSTRAINT `fk_dp_doctor` FOREIGN KEY (`doctor_id`) REFERENCES `doctor_user` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_dp_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='医患关系表';

-- -------------------------------------------------------------
-- 11. doctor_advice 医生健康建议表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `doctor_advice`;
CREATE TABLE `doctor_advice` (
    `id`             INT AUTO_INCREMENT PRIMARY KEY,
    `doctor_id`      INT      NOT NULL COMMENT '医生ID',
    `user_id`        INT      NOT NULL COMMENT '患者ID',
    `advice_content` TEXT     COMMENT '建议内容',
    `created_at`     DATETIME DEFAULT CURRENT_TIMESTAMP,
    KEY `idx_da_doctor` (`doctor_id`),
    KEY `idx_da_user` (`user_id`),
    CONSTRAINT `fk_da_doctor` FOREIGN KEY (`doctor_id`) REFERENCES `doctor_user` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_da_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='医生健康建议表';

-- -------------------------------------------------------------
-- 12. medical_notice 体检通知表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `medical_notice`;
CREATE TABLE `medical_notice` (
    `id`             INT AUTO_INCREMENT PRIMARY KEY,
    `doctor_id`      INT          NOT NULL COMMENT '医生ID',
    `user_id`        INT          NOT NULL COMMENT '患者ID',
    `notice_title`   VARCHAR(200) DEFAULT NULL COMMENT '通知标题',
    `notice_content` TEXT         COMMENT '通知内容',
    `check_date`     DATETIME     DEFAULT NULL COMMENT '检查时间',
    `created_at`     DATETIME     DEFAULT CURRENT_TIMESTAMP,
    KEY `idx_mn_doctor` (`doctor_id`),
    KEY `idx_mn_user` (`user_id`),
    CONSTRAINT `fk_mn_doctor` FOREIGN KEY (`doctor_id`) REFERENCES `doctor_user` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_mn_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='体检通知表';

-- -------------------------------------------------------------
-- 13. medical_record 医疗记录表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `medical_record`;
CREATE TABLE `medical_record` (
    `id`             INT AUTO_INCREMENT PRIMARY KEY,
    `doctor_id`      INT          NOT NULL COMMENT '医生ID',
    `user_id`        INT          NOT NULL COMMENT '患者ID',
    `record_title`   VARCHAR(200) DEFAULT NULL COMMENT '记录标题',
    `record_content` TEXT         COMMENT '记录内容',
    `record_date`    DATE         DEFAULT NULL COMMENT '记录日期',
    `created_at`     DATETIME     DEFAULT CURRENT_TIMESTAMP,
    KEY `idx_mr_doctor` (`doctor_id`),
    KEY `idx_mr_user` (`user_id`),
    CONSTRAINT `fk_mr_doctor` FOREIGN KEY (`doctor_id`) REFERENCES `doctor_user` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_mr_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='医疗记录表';

-- -------------------------------------------------------------
-- 14. coach_user 健身教练表（role = 2）
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `coach_user`;
CREATE TABLE `coach_user` (
    `id`            INT AUTO_INCREMENT PRIMARY KEY,
    `coach_name`    VARCHAR(50)  NOT NULL COMMENT '教练账号',
    `password_hash` VARCHAR(255) NOT NULL COMMENT 'Werkzeug 安全哈希密码',
    `real_name`     VARCHAR(50)  DEFAULT NULL COMMENT '真实姓名',
    `gender`        VARCHAR(10)  DEFAULT NULL COMMENT '性别',
    `phone`         VARCHAR(20)  DEFAULT NULL COMMENT '手机号',
    `specialty`     VARCHAR(100) DEFAULT NULL COMMENT '专业方向',
    `avatar`        VARCHAR(255) DEFAULT 'default_coach.jpg' COMMENT '头像文件名',
    `audit_status`  TINYINT(1)   DEFAULT 0 COMMENT '0待审核 1通过 2拒绝',
    `created_at`    DATETIME     DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `uk_coach_name` (`coach_name`),
    KEY `idx_coach_audit` (`audit_status`),
    KEY `idx_coach_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='健身教练表';

-- -------------------------------------------------------------
-- 15. coach_student 教练学员关系表（coach_id + user_id 唯一）
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `coach_student`;
CREATE TABLE `coach_student` (
    `id`         INT AUTO_INCREMENT PRIMARY KEY,
    `coach_id`   INT      NOT NULL COMMENT '教练ID',
    `user_id`    INT      NOT NULL COMMENT '学员(普通用户)ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `uk_cs_relation` (`coach_id`, `user_id`),
    KEY `idx_cs_user` (`user_id`),
    CONSTRAINT `fk_cs_coach` FOREIGN KEY (`coach_id`) REFERENCES `coach_user` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_cs_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教练学员关系表';

-- -------------------------------------------------------------
-- 16. sport_goal 运动目标表  状态：0进行中 1已完成 2已结束
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `sport_goal`;
CREATE TABLE `sport_goal` (
    `id`           INT AUTO_INCREMENT PRIMARY KEY,
    `coach_id`     INT          NOT NULL COMMENT '教练ID',
    `user_id`      INT          NOT NULL COMMENT '学员ID',
    `goal_title`   VARCHAR(100) DEFAULT NULL COMMENT '目标标题',
    `goal_content` TEXT         COMMENT '目标内容',
    `start_date`   DATE         DEFAULT NULL,
    `end_date`     DATE         DEFAULT NULL,
    `goal_status`  TINYINT(1)   DEFAULT 0 COMMENT '0进行中 1已完成 2已结束',
    `created_at`   DATETIME     DEFAULT CURRENT_TIMESTAMP,
    KEY `idx_sg_coach` (`coach_id`),
    KEY `idx_sg_user` (`user_id`),
    CONSTRAINT `fk_sg_coach` FOREIGN KEY (`coach_id`) REFERENCES `coach_user` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_sg_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='运动目标表';

-- -------------------------------------------------------------
-- 17. training_plan 训练计划表  状态：0进行中 1已完成 2已结束
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `training_plan`;
CREATE TABLE `training_plan` (
    `id`           INT AUTO_INCREMENT PRIMARY KEY,
    `coach_id`     INT          NOT NULL COMMENT '教练ID',
    `user_id`      INT          NOT NULL COMMENT '学员ID',
    `plan_title`   VARCHAR(100) DEFAULT NULL COMMENT '计划标题',
    `plan_content` TEXT         COMMENT '计划内容',
    `start_date`   DATE         DEFAULT NULL,
    `end_date`     DATE         DEFAULT NULL,
    `plan_status`  TINYINT(1)   DEFAULT 0 COMMENT '0进行中 1已完成 2已结束',
    `created_at`   DATETIME     DEFAULT CURRENT_TIMESTAMP,
    KEY `idx_tp_coach` (`coach_id`),
    KEY `idx_tp_user` (`user_id`),
    CONSTRAINT `fk_tp_coach` FOREIGN KEY (`coach_id`) REFERENCES `coach_user` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_tp_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='训练计划表';

-- -------------------------------------------------------------
-- 18. fitness_advice 健身建议表
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `fitness_advice`;
CREATE TABLE `fitness_advice` (
    `id`             INT AUTO_INCREMENT PRIMARY KEY,
    `coach_id`       INT      NOT NULL COMMENT '教练ID',
    `user_id`        INT      NOT NULL COMMENT '学员ID',
    `advice_content` TEXT     COMMENT '建议内容',
    `created_at`     DATETIME DEFAULT CURRENT_TIMESTAMP,
    KEY `idx_fa_coach` (`coach_id`),
    KEY `idx_fa_user` (`user_id`),
    CONSTRAINT `fk_fa_coach` FOREIGN KEY (`coach_id`) REFERENCES `coach_user` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_fa_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='健身建议表';

-- -------------------------------------------------------------
-- 19. admin_operation_log 管理员操作日志表
--     禁止记录：明文密码 / 密码哈希 / Token / JWT Secret / 数据库密码
-- -------------------------------------------------------------
DROP TABLE IF EXISTS `admin_operation_log`;
CREATE TABLE `admin_operation_log` (
    `id`                  INT AUTO_INCREMENT PRIMARY KEY,
    `admin_id`            INT          NOT NULL COMMENT '管理员ID',
    `operation_type`      VARCHAR(50)  NOT NULL COMMENT '操作类型',
    `operation_content`   VARCHAR(500) NOT NULL COMMENT '操作内容(已脱敏)',
    `target_type`         VARCHAR(50)  DEFAULT NULL COMMENT '目标类型',
    `target_id`           INT          DEFAULT NULL COMMENT '目标ID',
    `created_at`          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY `idx_log_admin` (`admin_id`),
    KEY `idx_log_type` (`operation_type`),
    KEY `idx_log_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='管理员操作日志表';

SET FOREIGN_KEY_CHECKS = 1;

-- =============================================================
-- 初始化测试账号（全部密码为 123456，均为 Werkzeug 兼容安全哈希）
-- 正式使用前请修改测试密码
-- =============================================================

-- 管理员：admin / 123456
INSERT INTO `admin_user` (`admin_name`, `password_hash`, `real_name`, `avatar`, `created_at`) VALUES
('admin', 'pbkdf2:sha256:600000$cyFtvYVYb5aX8kAw$904ff860f97e0dac99e539acdde8bfc04a8392adb2bf1761cacf23d51e1bdff5', '系统管理员', 'default_admin.jpg', NOW());

-- 医生：doctor001 / 123456（已审核）；doctor002 / 123456（已审核）
--       doctor003 / 123456（待审核，用于审核流程演示）
INSERT INTO `doctor_user` (`doctor_name`, `password_hash`, `real_name`, `gender`, `phone`, `specialty`, `avatar`, `audit_status`, `created_at`) VALUES
('doctor001', 'pbkdf2:sha256:600000$KSdn81BChwtGxVix$cf3a754fcc556cba32e2673909c9054ad92558d95fa7abd54f6f2a74be3d840a', '张明远', '男', '13800000001', '心内科', 'default_doctor.jpg', 1, NOW()),
('doctor002', 'pbkdf2:sha256:600000$1w2jtCGde7uPh3qK$61fa3279534f138b8cf65e1d74d0e400ab3216125bda04b38a144605e75d7a9c', '李欣',   '女', '13800000002', '内分泌科', 'default_doctor.jpg', 1, NOW()),
('doctor003', 'pbkdf2:sha256:600000$KSdn81BChwtGxVix$cf3a754fcc556cba32e2673909c9054ad92558d95fa7abd54f6f2a74be3d840a', '王海涛', '男', '13800000003', '全科', 'default_doctor.jpg', 0, NOW());

-- 健身教练：coach001 / 123456（已审核）；coach002 / 123456（已审核）
--           coach003 / 123456（待审核，用于审核流程演示）
INSERT INTO `coach_user` (`coach_name`, `password_hash`, `real_name`, `gender`, `phone`, `specialty`, `avatar`, `audit_status`, `created_at`) VALUES
('coach001', 'pbkdf2:sha256:600000$5olPmYzyLBRvirff$3f117550add4d2816c4f5f02c11934a4686819cd7351ad37ed1b8b8c969c710c', '陈昊',   '男', '13900000001', '力量训练', 'default_coach.jpg', 1, NOW()),
('coach002', 'pbkdf2:sha256:600000$zDByRrGxmAsFpyOk$3e71523800a84fa7e6d3c54b89c10d0826f477ca7da6b8dc4b84ae1b376c12ff', '刘雨欣', '女', '13900000002', '普拉提',   'default_coach.jpg', 1, NOW()),
('coach003', 'pbkdf2:sha256:600000$5olPmYzyLBRvirff$3f117550add4d2816c4f5f02c11934a4686819cd7351ad37ed1b8b8c969c710c', '赵强',   '男', '13900000003', '体能训练', 'default_coach.jpg', 0, NOW());

-- 普通用户：13800138001 / 123456 ；13800138002 / 123456
INSERT INTO `users` (`phone`, `password_hash`, `nickname`, `avatar`, `gender`, `age`, `height`, `created_at`) VALUES
('13800138001', 'pbkdf2:sha256:600000$En28yrhsgy7hA6af$f0ae98b1ebaf05d795ca75ca7b8efbb50b3ce7aecda6f62ae8c7e866a08c30d4', '小林同学', 'default_health.jpg', '男', 26, 175.0, NOW()),
('13800138002', 'pbkdf2:sha256:600000$zvBZOMCdgiS5FmLX$f25d37681d9d725e1cf66b1eb26119c04761f9ef3e2226df403b36a10332a60f', '阿may',   'default_health.jpg', '女', 24, 163.0, NOW());

-- 初始医患关系：doctor001 -> user001 / user002
INSERT INTO `doctor_patient` (`doctor_id`, `user_id`, `created_at`) VALUES
(1, 1, NOW()),
(1, 2, NOW());
-- 初始教练学员关系：coach001 -> user001 / user002
INSERT INTO `coach_student` (`coach_id`, `user_id`, `created_at`) VALUES
(1, 1, NOW()),
(1, 2, NOW());

-- 健康科普文章（无需登录可见）
INSERT INTO `health_article` (`title`, `cover_img`, `content`, `author`, `is_show`, `publish_time`, `created_at`) VALUES
('每天喝多少水才健康？', 'default_health.jpg', '成年人每日饮水量建议在 1500~1700 毫升之间，具体需根据气温、运动量与个人体质调整。建议少量多次饮用，避免一次性大量饮水。运动后可适当补充含电解质的饮品。', '健康编辑部', 1, NOW(), NOW()),
('如何科学安排一周运动计划', 'default_health.jpg', '建议每周进行 150 分钟中等强度有氧运动，并搭配 2~3 次力量训练。有氧运动可选择快走、慢跑、游泳、骑行；力量训练可从自重训练开始逐步过渡到器械训练。注意运动前热身与运动后拉伸。', '健康编辑部', 1, NOW(), NOW()),
('优质睡眠的 7 个小习惯', 'default_health.jpg', '1) 固定作息时间；2) 睡前 1 小时远离电子屏幕；3) 卧室温度保持在 18~22 摄氏度；4) 避免午后摄入咖啡因；5) 睡前避免大量进食；6) 适度日间运动；7) 保持卧室安静黑暗。', '健康编辑部', 1, NOW(), NOW()),
('读懂体检报告里的血压数值', 'default_health.jpg', '血压通常以「收缩压/舒张压」表示，单位为 mmHg。一般成年人在安静状态下，收缩压低于 120、舒张压低于 80 属于理想范围。单次测量偏高并不等于异常，建议在平静状态下多次测量并咨询专业医疗人员。', '健康编辑部', 1, NOW(), NOW());

-- 系统公告
INSERT INTO `notice` (`title`, `content`, `publish_time`, `is_show`, `created_at`) VALUES
('系统上线公告', '个人健康管理系统 V3.2 正式上线，欢迎使用健康数据记录、趋势分析、医生建议与教练训练计划等功能。', NOW(), 1, NOW()),
('健康数据记录提醒', '建议每日固定时间记录体重、血压等健康指标，持续记录可获得更准确的趋势分析结果。', NOW(), 1, NOW()),
('关于医疗建议的说明', '本系统提供的健康建议均由医生人工填写，系统不会自动诊断疾病或推荐药物。如身体持续异常，请及时前往正规医疗机构就诊。', NOW(), 1, NOW());

-- 初始运动数据（便于教练 Dashboard 图表展示）
INSERT INTO `sport_record` (`user_id`, `sport_date`, `sport_type`, `sport_duration`, `calorie`, `remark`, `created_at`) VALUES
(1, CURDATE(), '跑步', 40, 320, '晨跑', NOW()),
(2, CURDATE(), '骑行', 60, 410, '通勤骑行', NOW()),
(1, DATE_SUB(CURDATE(), INTERVAL 1 DAY), '力量训练', 50, 280, '上肢训练', NOW()),
(2, DATE_SUB(CURDATE(), INTERVAL 1 DAY), '瑜伽', 45, 160, '睡前放松', NOW()),
(1, DATE_SUB(CURDATE(), INTERVAL 2 DAY), '游泳', 45, 380, '自由泳', NOW()),
(2, DATE_SUB(CURDATE(), INTERVAL 3 DAY), '跑步', 30, 240, '慢跑', NOW());

-- 初始健康指标数据
INSERT INTO `health_record` (`user_id`, `record_date`, `weight`, `blood_pressure_high`, `blood_pressure_low`, `heart_rate`, `blood_sugar`, `created_at`) VALUES
(1, CURDATE(), 68.5, 118, 76, 72, 5.4, NOW()),
(2, CURDATE(), 55.2, 110, 70, 78, 4.9, NOW()),
(1, DATE_SUB(CURDATE(), INTERVAL 2 DAY), 69.0, 122, 80, 75, 5.6, NOW()),
(2, DATE_SUB(CURDATE(), INTERVAL 3 DAY), 55.6, 112, 72, 76, 5.0, NOW());

-- 初始睡眠数据
INSERT INTO `sleep_record` (`user_id`, `sleep_date`, `sleep_start`, `sleep_end`, `sleep_duration`, `sleep_quality`, `created_at`) VALUES
(1, CURDATE(), DATE_SUB(NOW(), INTERVAL 8 HOUR), NOW(), 480, '很好', NOW()),
(2, CURDATE(), DATE_SUB(NOW(), INTERVAL 7 HOUR), NOW(), 420, '一般', NOW());

-- 初始健康计划
INSERT INTO `health_plan` (`user_id`, `plan_title`, `plan_content`, `plan_start`, `plan_end`, `plan_status`, `created_at`) VALUES
(1, '每日 8000 步挑战', '坚持每日步行 8000 步以上，配合睡前拉伸 10 分钟。', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 30 DAY), 0, NOW()),
(2, '早睡早起计划', '23:30 前入睡，7:00 起床，坚持 21 天养成作息习惯。', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 21 DAY), 0, NOW());

-- 初始医生业务数据
INSERT INTO `doctor_advice` (`doctor_id`, `user_id`, `advice_content`, `created_at`) VALUES
(1, 1, '近期血压平稳，建议保持低盐饮食，每日食盐摄入控制在 5g 以内，并保持每周 3 次以上有氧运动。', NOW());

INSERT INTO `medical_notice` (`doctor_id`, `user_id`, `notice_title`, `notice_content`, `check_date`, `created_at`) VALUES
(1, 1, '年度心血管专项体检通知', '建议进行一次血脂四项 + 心电图检查，检查当日请空腹前往。', DATE_ADD(NOW(), INTERVAL 7 DAY), NOW());

INSERT INTO `medical_record` (`doctor_id`, `user_id`, `record_title`, `record_content`, `record_date`, `created_at`) VALUES
(1, 1, '常规随访记录', '患者自述近期睡眠质量良好，无胸闷心悸。血压 118/76 mmHg，心率 72 次/分。建议继续保持当前运动与饮食方案，3 个月后复诊。', CURDATE(), NOW());

-- 初始教练业务数据
INSERT INTO `sport_goal` (`coach_id`, `user_id`, `goal_title`, `goal_content`, `start_date`, `end_date`, `goal_status`, `created_at`) VALUES
(1, 1, '3 个月减脂 5kg', '每周有氧 3 次 + 力量 2 次，控制每日热量缺口 300~500 kcal。', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 90 DAY), 0, NOW());

INSERT INTO `training_plan` (`coach_id`, `user_id`, `plan_title`, `plan_content`, `start_date`, `end_date`, `plan_status`, `created_at`) VALUES
(1, 1, '8 周力量提升计划', '周一/周四：上肢推拉；周二/周五：下肢；周三/周六：核心与有氧。每个训练日 60 分钟。', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 56 DAY), 0, NOW());

INSERT INTO `fitness_advice` (`coach_id`, `user_id`, `advice_content`, `created_at`) VALUES
(1, 1, '跑步时注意保持 170~180 步/分钟的步频，落地时前脚掌先着地，可有效降低膝关节压力。', NOW());
