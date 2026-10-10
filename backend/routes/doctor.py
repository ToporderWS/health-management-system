# -*- coding: utf-8 -*-
"""医生路由。所有患者数据接口都会做医患关系校验，未绑定一律 401。"""
from flask import Blueprint, request

from services import doctor_service
from utils.auth import current_doctor_id, doctor_token_required
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

doctor_bp = Blueprint("doctor", __name__, url_prefix="/api/doctor")

MSG_NO_RELATION = "无权访问该患者数据（未建立医患关系）"


# =========================== 注册 / 登录 ===========================
@doctor_bp.post("/register")
def register():
    """医生自主申请注册，audit_status 强制为 0。"""
    ok, msg, data = doctor_service.register(get_json())
    return success(data, msg) if ok else param_error(msg)


@doctor_bp.post("/login")
def login():
    """医生登录：仅 audit_status=1 可签发 doctor_token。"""
    body = get_json()
    ok, msg, data = doctor_service.login(body.get("doctor_name"), body.get("password"))
    return success(data, msg) if ok else param_error(msg)


@doctor_bp.get("/info")
@doctor_token_required
def info():
    ok, msg, data = doctor_service.get_info(current_doctor_id())
    return success(data, msg) if ok else param_error(msg)


@doctor_bp.get("/dashboard")
@doctor_token_required
def dashboard():
    return success(doctor_service.dashboard(current_doctor_id()), "操作成功")


# =========================== 患者管理 ===========================
@doctor_bp.get("/patient/list")
@doctor_token_required
def patient_list():
    page, size, _ = get_page()
    total, rows = doctor_service.patient_list(
        current_doctor_id(), page=page, page_size=size, keyword=get_arg("keyword"))
    return success(page_result(rows, total, page, size), "操作成功")


@doctor_bp.get("/patient/detail")
@doctor_token_required
def patient_detail():
    user_id = to_int(get_arg("user_id"))
    if not user_id:
        return param_error("缺少患者 user_id")
    row = doctor_service.get_patient(current_doctor_id(), user_id)
    if not row:
        return unauthorized(MSG_NO_RELATION)
    return success(row, "操作成功")


@doctor_bp.get("/patient/health_data")
@doctor_token_required
def patient_health_data():
    """患者健康指标（只读），支持患者筛选 / 日期筛选 / 分页。"""
    page, size, _ = get_page()
    user_id = to_int(get_arg("user_id"))
    if not user_id:
        return param_error("请选择患者")
    total, rows = doctor_service.patient_health_data(
        current_doctor_id(), user_id, page=page, page_size=size,
        start_date=parse_date(get_arg("start_date")),
        end_date=parse_date(get_arg("end_date")),
    )
    if total is None:
        return unauthorized(MSG_NO_RELATION)
    return success(page_result(rows, total, page, size), "操作成功")


@doctor_bp.get("/patient/sleep_data")
@doctor_token_required
def patient_sleep_data():
    page, size, _ = get_page()
    user_id = to_int(get_arg("user_id"))
    if not user_id:
        return param_error("请选择患者")
    total, rows = doctor_service.patient_sleep_data(
        current_doctor_id(), user_id, page=page, page_size=size)
    if total is None:
        return unauthorized(MSG_NO_RELATION)
    return success(page_result(rows, total, page, size), "操作成功")


@doctor_bp.get("/patient/sport_data")
@doctor_token_required
def patient_sport_data():
    page, size, _ = get_page()
    user_id = to_int(get_arg("user_id"))
    if not user_id:
        return param_error("请选择患者")
    total, rows = doctor_service.patient_sport_data(
        current_doctor_id(), user_id, page=page, page_size=size)
    if total is None:
        return unauthorized(MSG_NO_RELATION)
    return success(page_result(rows, total, page, size), "操作成功")


@doctor_bp.get("/patient/plan_data")
@doctor_token_required
def patient_plan_data():
    page, size, _ = get_page()
    user_id = to_int(get_arg("user_id"))
    if not user_id:
        return param_error("请选择患者")
    total, rows = doctor_service.patient_plan_data(
        current_doctor_id(), user_id, page=page, page_size=size)
    if total is None:
        return unauthorized(MSG_NO_RELATION)
    return success(page_result(rows, total, page, size), "操作成功")


@doctor_bp.get("/patient/trend")
@doctor_token_required
def patient_trend():
    """患者健康趋势（体重 / 血压 / 睡眠 / 运动）。"""
    user_id = to_int(get_arg("user_id"))
    if not user_id:
        return param_error("请选择患者")
    days = to_int(get_arg("days"), 30) or 30
    data = doctor_service.patient_health_trend(current_doctor_id(), user_id, days=days)
    if data is None:
        return unauthorized(MSG_NO_RELATION)
    return success(data, "操作成功")


# =========================== 健康建议 ===========================
@doctor_bp.get("/advice/list")
@doctor_token_required
def advice_list():
    page, size, _ = get_page()
    total, rows = doctor_service.list_advice(
        current_doctor_id(), page=page, page_size=size,
        user_id=get_arg("user_id"), keyword=get_arg("keyword"))
    return success(page_result(rows, total, page, size), "操作成功")


@doctor_bp.post("/advice/save")
@doctor_token_required
def advice_save():
    body = get_json()
    ok, msg, data = doctor_service.save_advice(
        current_doctor_id(), body.get("user_id"), body.get("advice_content"))
    return success(data, msg) if ok else param_error(msg)


# =========================== 体检通知 ===========================
@doctor_bp.get("/medical_notice/list")
@doctor_token_required
def medical_notice_list():
    page, size, _ = get_page()
    total, rows = doctor_service.list_medical_notice(
        current_doctor_id(), page=page, page_size=size,
        user_id=get_arg("user_id"), keyword=get_arg("keyword"))
    return success(page_result(rows, total, page, size), "操作成功")


@doctor_bp.post("/medical_notice/save")
@doctor_token_required
def medical_notice_save():
    ok, msg, data = doctor_service.save_medical_notice(current_doctor_id(), get_json())
    return success(data, msg) if ok else param_error(msg)


# =========================== 医疗记录 ===========================
@doctor_bp.get("/medical_record/list")
@doctor_token_required
def medical_record_list():
    page, size, _ = get_page()
    total, rows = doctor_service.list_medical_record(
        current_doctor_id(), page=page, page_size=size,
        user_id=get_arg("user_id"), keyword=get_arg("keyword"))
    return success(page_result(rows, total, page, size), "操作成功")


@doctor_bp.post("/medical_record/save")
@doctor_token_required
def medical_record_save():
    ok, msg, data = doctor_service.save_medical_record(current_doctor_id(), get_json())
    return success(data, msg) if ok else param_error(msg)


# =========================== 个人中心 ===========================
@doctor_bp.post("/upload_avatar")
@doctor_token_required
def upload_avatar():
    file = request.files.get("file") or request.files.get("avatar")
    filename, err = save_upload_file(file)
    if err:
        return param_error(err)
    ok, msg, data = doctor_service.update_avatar(current_doctor_id(), filename)
    return success(data, msg) if ok else param_error(msg)


@doctor_bp.post("/update_pwd")
@doctor_token_required
def update_pwd():
    body = get_json()
    ok, msg, _ = doctor_service.update_password(
        current_doctor_id(), body.get("old_password"), body.get("new_password"))
    return success(None, msg) if ok else param_error(msg)


@doctor_bp.post("/logout")
@doctor_token_required
def logout():
    return success(None, "已退出登录")
