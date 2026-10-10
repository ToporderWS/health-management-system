# -*- coding: utf-8 -*-
"""密码安全：统一使用 Werkzeug 安全哈希，禁止明文存储与明文比较。"""
from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password):
    """生成安全哈希（默认 pbkdf2:sha256）。"""
    return generate_password_hash(str(password))


def verify_password(password_hash, password):
    """校验明文密码与哈希是否匹配，异常一并视为不匹配。"""
    if not password_hash or password is None:
        return False
    try:
        return check_password_hash(password_hash, str(password))
    except Exception:  # noqa: BLE001  哈希格式异常时不应导致 500
        return False


def check_password_strength(password, min_len=6):
    """
    密码强度基础校验：长度 >= 6。
    :return: (ok, message)
    """
    if not password:
        return False, "密码不能为空"
    if len(str(password)) < min_len:
        return False, "密码长度不能少于 %d 位" % min_len
    return True, ""
