# -*- coding: utf-8 -*-
"""项目配置：统一从环境变量 / .env 读取，禁止在代码中硬编码密码。"""
import os

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 优先加载同目录 .env，其次 .env.example（便于开箱启动）
_env_file = os.path.join(BASE_DIR, ".env")
if os.path.exists(_env_file):
    load_dotenv(_env_file)
else:
    load_dotenv(os.path.join(BASE_DIR, ".env.example"))


def _get(key, default=""):
    value = os.environ.get(key, default)
    return value if value not in (None, "") else default


class Config(object):
    # ---------------- 服务 ----------------
    HOST = _get("FLASK_HOST", "0.0.0.0")
    PORT = int(_get("FLASK_PORT", "8080"))
    DEBUG = _get("FLASK_DEBUG", "False").lower() in ("1", "true", "yes")

    # ---------------- 数据库 ----------------
    DB_HOST = _get("DB_HOST", "127.0.0.1")
    DB_PORT = int(_get("DB_PORT", "3306"))
    DB_USER = _get("DB_USER", "root")
    DB_PASSWORD = _get("DB_PASSWORD", "")
    DB_NAME = _get("DB_NAME", "health_management")
    DB_CHARSET = _get("DB_CHARSET", "utf8mb4")

    # ---------------- JWT ----------------
    # 安全失败策略：JWT_SECRET 必须由环境变量（backend/.env）提供。
    # 缺失或仍为占位值 => 启动阶段直接报配置错误，绝不回落到代码内固定默认密钥。
    JWT_SECRET = _get("JWT_SECRET", "")
    if not JWT_SECRET or JWT_SECRET in (
            "please-change-this-jwt-secret-in-production",
            "CHANGE_ME_TO_A_STRONG_RANDOM_SECRET"):
        raise RuntimeError(
            "配置错误：环境变量 JWT_SECRET 未设置或仍为占位值，"
            "请在 backend/.env 中配置高强度随机密钥后重启服务。")
    JWT_EXPIRE_HOURS = int(_get("JWT_EXPIRE_HOURS", "72"))

    # ---------------- 地址 ----------------
    API_BASE_URL = _get("API_BASE_URL", "/api")
    STATIC_BASE_URL = _get("STATIC_BASE_URL", "/static/upload/")

    # ---------------- 上传 ----------------
    UPLOAD_DIR = os.path.join(BASE_DIR, "static", "upload")
    ALLOWED_EXT = {"jpg", "jpeg", "png", "webp"}
    MAX_CONTENT_LENGTH = int(_get("MAX_CONTENT_LENGTH_MB", "10")) * 1024 * 1024

    # ---------------- 业务约束 ----------------
    # sleep_quality 只允许的取值
    SLEEP_QUALITY_OPTIONS = ("很好", "一般", "较差")

    # 系统版本（用于系统信息展示，禁止暴露敏感配置）
    SYSTEM_NAME = "个人健康管理系统"
    SYSTEM_VERSION = "V3.2 FINAL"


# JWT token 类型 -> 角色映射（四角色 Token 完全隔离）
ROLE_USER = 0
ROLE_DOCTOR = 1
ROLE_COACH = 2
ROLE_ADMIN = 3

TOKEN_USER = "user_token"
TOKEN_DOCTOR = "doctor_token"
TOKEN_COACH = "coach_token"
TOKEN_ADMIN = "admin_token"

TOKEN_ROLE_MAP = {
    TOKEN_USER: ROLE_USER,
    TOKEN_DOCTOR: ROLE_DOCTOR,
    TOKEN_COACH: ROLE_COACH,
    TOKEN_ADMIN: ROLE_ADMIN,
}
