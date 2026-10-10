# -*- coding: utf-8 -*-
"""健康数据路由：健康指标 / 睡眠 / 运动 / 健康计划 / 数据报告。

全部接口均要求 user_token，且数据归属一律取 Token 中的 user_id。
"""
from flask import Blueprint

from services import health_service
from utils.auth import current_user_id, user_token_required
from utils.helpers import get_arg, get_json, get_page, page_result, parse_date, to_int
from utils.response import param_error, success

health_bp = Blueprint("health", __name__, url_prefix="/api")


# =========================== 健康指标 ===========================
@health_bp.post("/health_record/add")
@user_token_required
def health_record_add():
    ok, msg, data = health_service.add_health_record(current_user_id(), get_json())
    return success(data, msg) if ok else param_error(msg)


@health_bp.get("/health_record/my_list")
@user_token_required
def health_record_my_list():
    page, size, _ = get_page()
    total, rows = health_service.list_health_record(
        current_user_id(), page=page, page_size=size,
        start_date=parse_date(get_arg("start_date")),
        end_date=parse_date(get_arg("end_date")),
    )
    return success(page_result(rows, total, page, size), "操作成功")


# =========================== 睡眠 ===========================
@health_bp.post("/sleep_record/add")
@user_token_required
def sleep_record_add():
    ok, msg, data = health_service.add_sleep_record(current_user_id(), get_json())
    return success(data, msg) if ok else param_error(msg)


@health_bp.get("/sleep_record/my_list")
@user_token_required
def sleep_record_my_list():
    page, size, _ = get_page()
    total, rows = health_service.list_sleep_record(
        current_user_id(), page=page, page_size=size,
        start_date=parse_date(get_arg("start_date")),
        end_date=parse_date(get_arg("end_date")),
    )
    return success(page_result(rows, total, page, size), "操作成功")


# =========================== 运动 ===========================
@health_bp.post("/sport_record/add")
@user_token_required
def sport_record_add():
    ok, msg, data = health_service.add_sport_record(current_user_id(), get_json())
    return success(data, msg) if ok else param_error(msg)


@health_bp.get("/sport_record/my_list")
@user_token_required
def sport_record_my_list():
    page, size, _ = get_page()
    total, rows = health_service.list_sport_record(
        current_user_id(), page=page, page_size=size,
        start_date=parse_date(get_arg("start_date")),
        end_date=parse_date(get_arg("end_date")),
        sport_type=get_arg("sport_type"),
    )
    return success(page_result(rows, total, page, size), "操作成功")


# =========================== 健康计划 ===========================
@health_bp.post("/health_plan/add")
@user_token_required
def health_plan_add():
    ok, msg, data = health_service.add_health_plan(current_user_id(), get_json())
    return success(data, msg) if ok else param_error(msg)


@health_bp.get("/health_plan/my_list")
@user_token_required
def health_plan_my_list():
    page, size, _ = get_page()
    total, rows = health_service.list_health_plan(
        current_user_id(), page=page, page_size=size,
        plan_status=get_arg("plan_status"),
    )
    return success(page_result(rows, total, page, size), "操作成功")


@health_bp.post("/health_plan/update_status")
@user_token_required
def health_plan_update_status():
    body = get_json()
    ok, msg, data = health_service.update_plan_status(
        current_user_id(), to_int(body.get("id")), body.get("plan_status"))
    return success(data, msg) if ok else param_error(msg)


# =========================== 数据报告 ===========================
@health_bp.get("/report/statistics")
@user_token_required
def report_statistics():
    """
    数据报告：最近 30 天体重 / 血压 / 运动 / 睡眠趋势 + 健康计划 + 首页今日概览 + 健康预警。
    """
    days = to_int(get_arg("days"), 30) or 30
    uid = current_user_id()
    data = health_service.report_statistics(uid, days=days)
    data["overview"] = health_service.today_overview(uid)
    return success(data, "操作成功")
