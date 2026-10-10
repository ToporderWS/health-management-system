# -*- coding: utf-8 -*-
"""普通用户路由。全部「我的数据」接口以 user_token 解析出的 user_id 为准。"""
from flask import Blueprint, request

from services import user_service
from utils.auth import current_user_id, user_token_required
from utils.helpers import get_arg, get_json
from utils.response import param_error, success
from utils.upload import save_upload_file

user_bp = Blueprint("user", __name__, url_prefix="/api/user")


@user_bp.post("/register")
def register():
    """普通用户自主注册，注册成功后可直接登录。"""
    ok, msg, data = user_service.register(get_json())
    return success(data, msg) if ok else param_error(msg)


@user_bp.post("/login")
def login():
    """普通用户登录，返回 user_token。"""
    body = get_json()
    ok, msg, data = user_service.login(body.get("phone"), body.get("password"))
    return success(data, msg) if ok else param_error(msg)


@user_bp.get("/info")
@user_token_required
def info():
    ok, msg, data = user_service.get_info(current_user_id())
    return success(data, msg) if ok else param_error(msg)


@user_bp.post("/update_info")
@user_token_required
def update_info():
    ok, msg, data = user_service.update_info(current_user_id(), get_json())
    return success(data, msg) if ok else param_error(msg)


@user_bp.post("/update_pwd")
@user_token_required
def update_pwd():
    body = get_json()
    ok, msg, _ = user_service.update_password(
        current_user_id(), body.get("old_password"), body.get("new_password"))
    return success(None, msg) if ok else param_error(msg)


@user_bp.post("/upload_avatar")
@user_token_required
def upload_avatar():
    """上传头像：数据库只保存文件名。"""
    file = request.files.get("file") or request.files.get("avatar")
    filename, err = save_upload_file(file)
    if err:
        return param_error(err)
    ok, msg, data = user_service.update_avatar(current_user_id(), filename)
    return success(data, msg) if ok else param_error(msg)


@user_bp.post("/logout")
@user_token_required
def logout():
    """
    退出登录：JWT 为无状态 Token，服务端不维护会话，
    客户端负责清除 user_token 与本地用户缓存。
    """
    return success(None, "已退出登录")


# ---------------- 医生服务（只读本人数据） ----------------
@user_bp.get("/doctor_advice")
@user_token_required
def doctor_advice():
    return success(user_service.my_doctor_advice(current_user_id()), "操作成功")


@user_bp.get("/medical_notice")
@user_token_required
def medical_notice():
    return success(user_service.my_medical_notice(current_user_id()), "操作成功")


@user_bp.get("/medical_record")
@user_token_required
def medical_record():
    return success(user_service.my_medical_record(current_user_id()), "操作成功")


# ---------------- 健身服务（只读本人数据） ----------------
@user_bp.get("/sport_goal")
@user_token_required
def sport_goal():
    return success(user_service.my_sport_goal(current_user_id()), "操作成功")


@user_bp.get("/training_plan")
@user_token_required
def training_plan():
    return success(user_service.my_training_plan(current_user_id()), "操作成功")


@user_bp.get("/fitness_advice")
@user_token_required
def fitness_advice():
    return success(user_service.my_fitness_advice(current_user_id()), "操作成功")
