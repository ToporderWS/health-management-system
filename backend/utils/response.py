# -*- coding: utf-8 -*-
"""统一响应契约。

成功：{"code": 200, "msg": "操作成功", "data": {}}
400 = 参数错误 / 业务错误 / 审核状态限制
401 = 未登录 / Token 无效 / Token 过期 / 角色错误 / 越权
500 = 服务器异常
"""
from flask import jsonify


def success(data=None, msg="操作成功", code=200):
    """成功响应。data 为空时统一返回 {}。"""
    return jsonify({
        "code": code,
        "msg": msg,
        "data": {} if data is None else data,
    }), code


def error(msg="操作失败", code=400, data=None):
    """失败响应。"""
    return jsonify({
        "code": code,
        "msg": msg,
        "data": {} if data is None else data,
    }), code


def param_error(msg="参数错误"):
    """参数/业务错误 -> 400。"""
    return error(msg, 400)


def unauthorized(msg="未登录或登录已失效"):
    """未登录 / Token 无效 / 角色错误 -> 401。"""
    return error(msg, 401)


def server_error(msg="服务器异常"):
    """服务器异常 -> 500。"""
    return error(msg, 500)


# 常用固定文案
MSG_AUDIT_PENDING = "账号正在审核中，请耐心等待"
MSG_AUDIT_REJECTED = "账号审核未通过，请联系管理员"
MSG_NOT_LOGIN = "请先登录"
