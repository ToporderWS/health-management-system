# -*- coding: utf-8 -*-
"""JWT 工具：四角色 Token 签发与解析。

Token 载荷至少包含：id / role / token_type / exp
token_type 取值：user_token | doctor_token | coach_token | admin_token
"""
import datetime

import jwt

from config import Config, ROLE_ADMIN, ROLE_COACH, ROLE_DOCTOR, ROLE_USER, TOKEN_ROLE_MAP


def generate_token(uid, role, token_type):
    """
    签发 Token。

    :param uid: 账号主键 ID
    :param role: 角色 0用户 1医生 2教练 3管理员
    :param token_type: user_token / doctor_token / coach_token / admin_token
    :raises ValueError: role 与 token_type 不匹配时抛出，防止跨角色签发
    """
    if TOKEN_ROLE_MAP.get(token_type) != role:
        raise ValueError("角色与 token_type 不匹配")
    now = datetime.datetime.utcnow()
    payload = {
        "id": int(uid),
        "role": int(role),
        "token_type": token_type,
        "iat": now,
        "exp": now + datetime.timedelta(hours=Config.JWT_EXPIRE_HOURS),
    }
    token = jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")
    # PyJWT 2.x 返回 str；1.x 返回 bytes，此处兼容处理
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def decode_token(token):
    """
    解析 Token，返回 payload；失败返回 None（不区分过期/非法，调用方统一按 401 处理）。
    """
    if not token:
        return None
    try:
        return jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
    except Exception:  # noqa: BLE001  ExpiredSignatureError / InvalidTokenError 等
        return None


# 便捷签发函数（业务代码推荐使用，避免手写 token_type 字符串出错）
def gen_user_token(uid):
    return generate_token(uid, ROLE_USER, "user_token")


def gen_doctor_token(uid):
    return generate_token(uid, ROLE_DOCTOR, "doctor_token")


def gen_coach_token(uid):
    return generate_token(uid, ROLE_COACH, "coach_token")


def gen_admin_token(uid):
    return generate_token(uid, ROLE_ADMIN, "admin_token")
