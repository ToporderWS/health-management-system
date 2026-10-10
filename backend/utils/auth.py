# -*- coding: utf-8 -*-
"""鉴权层：四角色 Token 完全隔离 + 医患/教练学员关系校验。

后端为权限最终判定方，前端隐藏菜单不作为权限依据。
"""
import functools

from flask import g, request

from utils import db
from utils.jwt_utils import decode_token
from utils.response import unauthorized

_TOKEN_KEY_MAP = {
    "user_token": "current_user_id",
    "doctor_token": "current_doctor_id",
    "coach_token": "current_coach_id",
    "admin_token": "current_admin_id",
}


def _extract_token():
    """从 Authorization: Bearer {token} 请求头中提取 Token。"""
    auth = request.headers.get("Authorization", "") or ""
    if auth.startswith("Bearer "):
        return auth[7:].strip()
    # 兼容未带 Bearer 前缀的写法
    if auth and "." in auth:
        return auth.strip()
    return ""


def _verify(expected_type):
    """
    校验 Token 类型并与期望角色比对。
    返回 (payload, error_response)；校验通过时 error_response 为 None。
    """
    token = _extract_token()
    if not token:
        return None, unauthorized("未登录，请先登录")

    payload = decode_token(token)
    if not payload:
        return None, unauthorized("登录状态已失效，请重新登录")

    token_type = payload.get("token_type")
    if token_type != expected_type:
        # 角色错误 / 跨 Token 使用 -> 401
        return None, unauthorized("无权访问该接口（Token 类型不匹配）")

    if payload.get("id") is None:
        return None, unauthorized("登录状态异常，请重新登录")

    return payload, None


def _make_decorator(expected_type):
    """生成指定 token_type 的鉴权装饰器。"""

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            payload, err = _verify(expected_type)
            if err:
                return err
            # 注入当前登录身份，业务层统一从 g 取值，禁止信任客户端传参的 id
            setattr(g, _TOKEN_KEY_MAP[expected_type], int(payload["id"]))
            setattr(g, "current_role", int(payload.get("role", -1)))
            setattr(g, "current_token_type", expected_type)
            return fn(*args, **kwargs)

        return wrapper

    return decorator


# ---------------- 四角色鉴权装饰器 ----------------
user_token_required = _make_decorator("user_token")
doctor_token_required = _make_decorator("doctor_token")
coach_token_required = _make_decorator("coach_token")
admin_token_required = _make_decorator("admin_token")


# ---------------- 角色 ID 快捷读取 ----------------
def current_user_id():
    """当前登录普通用户 ID（仅 user_token_required 装饰的接口内有效）。"""
    return getattr(g, "current_user_id", None)


def current_doctor_id():
    return getattr(g, "current_doctor_id", None)


def current_coach_id():
    return getattr(g, "current_coach_id", None)


def current_admin_id():
    return getattr(g, "current_admin_id", None)


# ---------------- 关系权限校验 ----------------
def doctor_has_patient(doctor_id, user_id):
    """医生是否负责该患者（存在 doctor_patient 关系）。"""
    row = db.query_one(
        "SELECT id FROM doctor_patient WHERE doctor_id=%s AND user_id=%s LIMIT 1",
        (doctor_id, user_id),
    )
    return bool(row)


def coach_has_student(coach_id, user_id):
    """教练是否负责该学员（存在 coach_student 关系）。"""
    row = db.query_one(
        "SELECT id FROM coach_student WHERE coach_id=%s AND user_id=%s LIMIT 1",
        (coach_id, user_id),
    )
    return bool(row)


def doctor_patient_ids(doctor_id):
    """医生负责的全部患者 ID 列表。"""
    rows = db.query_all(
        "SELECT user_id FROM doctor_patient WHERE doctor_id=%s", (doctor_id,)
    )
    return [r["user_id"] for r in rows]


def coach_student_ids(coach_id):
    """教练负责的全部学员 ID 列表。"""
    rows = db.query_all(
        "SELECT user_id FROM coach_student WHERE coach_id=%s", (coach_id,)
    )
    return [r["user_id"] for r in rows]
