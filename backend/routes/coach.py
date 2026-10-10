# -*- coding: utf-8 -*-
"""健身教练路由。所有学员数据接口都会做教练学员关系校验，未绑定一律 401。"""
from flask import Blueprint, request

from services import coach_service
from utils.auth import coach_token_required, current_coach_id
from utils.helpers import (
    get_arg,
    get_json,
    get_page,
    page_result,
    parse_date,
    to_int,
)
from utils.response import param_error, success, unauthorized
from utils.upload import save_upload_file

coach_bp = Blueprint("coach", __name__, url_prefix="/api/coach")

MSG_NO_RELATION = "无权访问该学员数据（未建立教练学员关系）"


# =========================== 注册 / 登录 ===========================
@coach_bp.post("/register")
def register():
    """教练自主申请注册，audit_status 强制为 0。"""
    ok, msg, data = coach_service.register(get_json())
    return success(data, msg) if ok else param_error(msg)


@coach_bp.post("/login")
def login():
    """教练登录：仅 audit_status=1 可签发 coach_token。"""
    body = get_json()
    ok, msg, data = coach_service.login(body.get("coach_name"), body.get("password"))
    return success(data, msg) if ok else param_error(msg)


@coach_bp.get("/info")
@coach_token_required
def info():
    ok, msg, data = coach_service.get_info(current_coach_id())
    return success(data, msg) if ok else param_error(msg)


@coach_bp.get("/dashboard")
@coach_token_required
def dashboard():
    return success(coach_service.dashboard(current_coach_id()), "操作成功")


# =========================== 学员管理 ===========================
@coach_bp.get("/student/list")
@coach_token_required
def student_list():
    page, size, _ = get_page()
    total, rows = coach_service.student_list(
        current_coach_id(), page=page, page_size=size, keyword=get_arg("keyword"))
    return success(page_result(rows, total, page, size), "操作成功")


@coach_bp.get("/student/detail")
@coach_token_required
def student_detail():
    user_id = to_int(get_arg("user_id"))
    if not user_id:
        return param_error("缺少学员 user_id")
    row = coach_service.get_student(current_coach_id(), user_id)
    if not row:
        return unauthorized(MSG_NO_RELATION)
    return success(row, "操作成功")


@coach_bp.get("/student/sport_data")
@coach_token_required
def student_sport_data():
    """学员运动原始数据（只读），支持筛选与分页。"""
    page, size, _ = get_page()
    user_id = to_int(get_arg("user_id"))
    if not user_id:
        return param_error("请选择学员")
    total, rows = coach_service.student_sport_data(
        current_coach_id(), user_id, page=page, page_size=size,
        start_date=parse_date(get_arg("start_date")),
        end_date=parse_date(get_arg("end_date")),
        sport_type=get_arg("sport_type"),
    )
    if total is None:
        return unauthorized(MSG_NO_RELATION)
    return success(page_result(rows, total, page, size), "操作成功")


@coach_bp.get("/student/statistics")
@coach_token_required
def student_statistics():
    user_id = to_int(get_arg("user_id"))
    if not user_id:
        return param_error("请选择学员")
    days = to_int(get_arg("days"), 30) or 30
    data = coach_service.student_sport_statistics(current_coach_id(), user_id, days=days)
    if data is None:
        return unauthorized(MSG_NO_RELATION)
    return success(data, "操作成功")


# =========================== 运动目标 ===========================
@coach_bp.get("/sport_goal/list")
@coach_token_required
def sport_goal_list():
    page, size, _ = get_page()
    total, rows = coach_service.list_sport_goal(
        current_coach_id(), page=page, page_size=size,
        user_id=get_arg("user_id"), goal_status=get_arg("goal_status"),
        keyword=get_arg("keyword"))
    return success(page_result(rows, total, page, size), "操作成功")


@coach_bp.post("/sport_goal/save")
@coach_token_required
def sport_goal_save():
    ok, msg, data = coach_service.save_sport_goal(current_coach_id(), get_json())
    return success(data, msg) if ok else param_error(msg)


@coach_bp.post("/sport_goal/update_status")
@coach_token_required
def sport_goal_update_status():
    body = get_json()
    ok, msg, data = coach_service.update_goal_status(
        current_coach_id(), to_int(body.get("id")), body.get("goal_status"))
    return success(data, msg) if ok else param_error(msg)


# =========================== 训练计划 ===========================
@coach_bp.get("/training_plan/list")
@coach_token_required
def training_plan_list():
    page, size, _ = get_page()
    total, rows = coach_service.list_training_plan(
        current_coach_id(), page=page, page_size=size,
        user_id=get_arg("user_id"), plan_status=get_arg("plan_status"),
        keyword=get_arg("keyword"))
    return success(page_result(rows, total, page, size), "操作成功")


@coach_bp.post("/training_plan/save")
@coach_token_required
def training_plan_save():
    ok, msg, data = coach_service.save_training_plan(current_coach_id(), get_json())
    return success(data, msg) if ok else param_error(msg)


@coach_bp.post("/training_plan/update_status")
@coach_token_required
def training_plan_update_status():
    body = get_json()
    ok, msg, data = coach_service.update_plan_status(
        current_coach_id(), to_int(body.get("id")), body.get("plan_status"))
    return success(data, msg) if ok else param_error(msg)


# =========================== 健身建议 ===========================
@coach_bp.get("/fitness_advice/list")
@coach_token_required
def fitness_advice_list():
    page, size, _ = get_page()
    total, rows = coach_service.list_fitness_advice(
        current_coach_id(), page=page, page_size=size,
        user_id=get_arg("user_id"), keyword=get_arg("keyword"))
    return success(page_result(rows, total, page, size), "操作成功")


@coach_bp.post("/fitness_advice/save")
@coach_token_required
def fitness_advice_save():
    body = get_json()
    ok, msg, data = coach_service.save_fitness_advice(
        current_coach_id(), body.get("user_id"), body.get("advice_content"))
    return success(data, msg) if ok else param_error(msg)


# =========================== 个人中心 ===========================
@coach_bp.post("/upload_avatar")
@coach_token_required
def upload_avatar():
    file = request.files.get("file") or request.files.get("avatar")
    filename, err = save_upload_file(file)
    if err:
        return param_error(err)
    ok, msg, data = coach_service.update_avatar(current_coach_id(), filename)
    return success(data, msg) if ok else param_error(msg)


@coach_bp.post("/update_pwd")
@coach_token_required
def update_pwd():
    body = get_json()
    ok, msg, _ = coach_service.update_password(
        current_coach_id(), body.get("old_password"), body.get("new_password"))
    return success(None, msg) if ok else param_error(msg)


@coach_bp.post("/logout")
@coach_token_required
def logout():
    return success(None, "已退出登录")
