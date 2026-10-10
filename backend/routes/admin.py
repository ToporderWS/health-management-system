# -*- coding: utf-8 -*-
"""管理员路由。

管理员为监管角色：可审核/编辑医生教练资料/重置密码/管理关系/内容运营，
并可查看全部业务数据；不提供任何篡改用户原始健康数据或冒充医生发建议的接口。
"""
import csv
import io

from flask import Blueprint, Response, request

from services import admin_service, content_service
from utils.auth import admin_token_required, current_admin_id
from utils.helpers import get_arg, get_json, get_page, page_result, to_int
from utils.response import param_error, success
from utils.upload import save_upload_file

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def _paging():
    return get_page()


def _int_arg(name):
    return to_int(get_arg(name))


# =========================== 登录 / 基础 ===========================
@admin_bp.post("/login")
def login():
    """管理员登录（管理员账号由数据库初始化，不提供注册接口）。"""
    body = get_json()
    ok, msg, data = admin_service.login(body.get("admin_name"), body.get("password"))
    return success(data, msg) if ok else param_error(msg)


@admin_bp.get("/info")
@admin_token_required
def info():
    ok, msg, data = admin_service.get_info(current_admin_id())
    return success(data, msg) if ok else param_error(msg)


@admin_bp.get("/dashboard")
@admin_token_required
def dashboard():
    """01 系统首页：全部为真实 SQL 统计。"""
    return success(admin_service.dashboard(), "操作成功")


# =========================== 02 普通用户管理 ===========================
@admin_bp.get("/user/list")
@admin_token_required
def user_list():
    page, size, _ = _paging()
    total, rows = admin_service.user_list(
        page=page, page_size=size,
        nickname=get_arg("nickname"), phone=get_arg("phone"), gender=get_arg("gender"),
        start_date=get_arg("start_date"), end_date=get_arg("end_date"))
    return success(page_result(rows, total, page, size), "操作成功")


@admin_bp.get("/user/detail")
@admin_token_required
def user_detail():
    user_id = _int_arg("id") or _int_arg("user_id")
    if not user_id:
        return param_error("缺少用户 id")
    row = admin_service.user_detail(user_id)
    if not row:
        return param_error("用户不存在")
    return success(row, "操作成功")


@admin_bp.get("/user/health_data")
@admin_token_required
def user_health_data():
    """用户健康档案数据（只读），data_type: health / sleep / sport / plan。"""
    user_id = _int_arg("user_id") or _int_arg("id")
    if not user_id:
        return param_error("缺少用户 id")
    page, size, _ = _paging()
    total, rows = admin_service.user_health_data(
        user_id, get_arg("data_type", "health"), page=page, page_size=size,
        start_date=get_arg("start_date"), end_date=get_arg("end_date"),
        sport_type=get_arg("sport_type"))
    return success(page_result(rows, total, page, size), "操作成功")


@admin_bp.get("/user/doctor_service")
@admin_token_required
def user_doctor_service():
    user_id = _int_arg("user_id")
    if not user_id:
        return param_error("缺少用户 id")
    return success(admin_service.user_doctor_service(user_id), "操作成功")


@admin_bp.get("/user/coach_service")
@admin_token_required
def user_coach_service():
    user_id = _int_arg("user_id")
    if not user_id:
        return param_error("缺少用户 id")
    return success(admin_service.user_coach_service(user_id), "操作成功")


# =========================== 03 医生管理 ===========================
@admin_bp.get("/doctor/list")
@admin_token_required
def doctor_list():
    page, size, _ = _paging()
    total, rows = admin_service.doctor_list(
        page=page, page_size=size,
        doctor_name=get_arg("doctor_name"), real_name=get_arg("real_name"),
        phone=get_arg("phone"), specialty=get_arg("specialty"),
        audit_status=get_arg("audit_status"))
    return success(page_result(rows, total, page, size), "操作成功")


@admin_bp.get("/doctor/detail")
@admin_token_required
def doctor_detail():
    doctor_id = _int_arg("id") or _int_arg("doctor_id")
    if not doctor_id:
        return param_error("缺少医生 id")
    row = admin_service.doctor_detail(doctor_id)
    if not row:
        return param_error("医生不存在")
    return success(row, "操作成功")


@admin_bp.post("/doctor/update")
@admin_token_required
def doctor_update():
    body = get_json()
    doctor_id = to_int(body.get("id") or body.get("doctor_id"))
    if not doctor_id:
        return param_error("缺少医生 id")
    ok, msg, _ = admin_service.doctor_update(current_admin_id(), doctor_id, body)
    return success(None, msg) if ok else param_error(msg)


@admin_bp.post("/doctor/reset_pwd")
@admin_token_required
def doctor_reset_pwd():
    body = get_json()
    doctor_id = to_int(body.get("id") or body.get("doctor_id"))
    if not doctor_id:
        return param_error("缺少医生 id")
    ok, msg, _ = admin_service.doctor_reset_pwd(
        current_admin_id(), doctor_id, body.get("new_password"))
    return success(None, msg) if ok else param_error(msg)


@admin_bp.post("/doctor/audit")
@admin_token_required
def doctor_audit():
    """审核医生：audit_status 1 通过 / 2 拒绝。"""
    body = get_json()
    doctor_id = to_int(body.get("id") or body.get("doctor_id"))
    if not doctor_id:
        return param_error("缺少医生 id")
    ok, msg, _ = admin_service.doctor_audit(
        current_admin_id(), doctor_id, body.get("audit_status"))
    return success(None, msg) if ok else param_error(msg)


# =========================== 04 健身教练管理 ===========================
@admin_bp.get("/coach/list")
@admin_token_required
def coach_list():
    page, size, _ = _paging()
    total, rows = admin_service.coach_list(
        page=page, page_size=size,
        coach_name=get_arg("coach_name"), real_name=get_arg("real_name"),
        phone=get_arg("phone"), specialty=get_arg("specialty"),
        audit_status=get_arg("audit_status"))
    return success(page_result(rows, total, page, size), "操作成功")


@admin_bp.get("/coach/detail")
@admin_token_required
def coach_detail():
    coach_id = _int_arg("id") or _int_arg("coach_id")
    if not coach_id:
        return param_error("缺少教练 id")
    row = admin_service.coach_detail(coach_id)
    if not row:
        return param_error("健身教练不存在")
    return success(row, "操作成功")


@admin_bp.post("/coach/update")
@admin_token_required
def coach_update():
    body = get_json()
    coach_id = to_int(body.get("id") or body.get("coach_id"))
    if not coach_id:
        return param_error("缺少教练 id")
    ok, msg, _ = admin_service.coach_update(current_admin_id(), coach_id, body)
    return success(None, msg) if ok else param_error(msg)


@admin_bp.post("/coach/reset_pwd")
@admin_token_required
def coach_reset_pwd():
    body = get_json()
    coach_id = to_int(body.get("id") or body.get("coach_id"))
    if not coach_id:
        return param_error("缺少教练 id")
    ok, msg, _ = admin_service.coach_reset_pwd(
        current_admin_id(), coach_id, body.get("new_password"))
    return success(None, msg) if ok else param_error(msg)


@admin_bp.post("/coach/audit")
@admin_token_required
def coach_audit():
    body = get_json()
    coach_id = to_int(body.get("id") or body.get("coach_id"))
    if not coach_id:
        return param_error("缺少教练 id")
    ok, msg, _ = admin_service.coach_audit(
        current_admin_id(), coach_id, body.get("audit_status"))
    return success(None, msg) if ok else param_error(msg)


# =========================== 05 账号审核中心 ===========================
@admin_bp.get("/audit/overview")
@admin_token_required
def audit_overview():
    return success(admin_service.audit_overview(), "操作成功")


@admin_bp.get("/audit/record_list")
@admin_token_required
def audit_record_list():
    page, size, _ = _paging()
    total, rows = admin_service.audit_record_list(
        page=page, page_size=size, audit_type=get_arg("audit_type"),
        keyword=get_arg("keyword"), start_date=get_arg("start_date"),
        end_date=get_arg("end_date"))
    return success(page_result(rows, total, page, size), "操作成功")


# =========================== 06 角色关系管理 ===========================
@admin_bp.get("/doctor/patient/list")
@admin_token_required
def doctor_patient_list():
    page, size, _ = _paging()
    total, rows = admin_service.doctor_patient_list(
        page=page, page_size=size, doctor_id=get_arg("doctor_id"),
        user_keyword=get_arg("user_keyword"))
    return success(page_result(rows, total, page, size), "操作成功")


@admin_bp.post("/doctor/bind_patient")
@admin_token_required
def bind_patient():
    body = get_json()
    ok, msg, _ = admin_service.bind_doctor_patient(
        current_admin_id(), body.get("doctor_id"), body.get("user_id"))
    return success(None, msg) if ok else param_error(msg)


@admin_bp.post("/doctor/unbind_patient")
@admin_token_required
def unbind_patient():
    body = get_json()
    ok, msg, _ = admin_service.unbind_doctor_patient(
        current_admin_id(), body.get("doctor_id"), body.get("user_id"))
    return success(None, msg) if ok else param_error(msg)


@admin_bp.get("/coach/student/list")
@admin_token_required
def coach_student_list():
    page, size, _ = _paging()
    total, rows = admin_service.coach_student_list(
        page=page, page_size=size, coach_id=get_arg("coach_id"),
        user_keyword=get_arg("user_keyword"))
    return success(page_result(rows, total, page, size), "操作成功")


@admin_bp.post("/coach/bind_student")
@admin_token_required
def bind_student():
    body = get_json()
    ok, msg, _ = admin_service.bind_coach_student(
        current_admin_id(), body.get("coach_id"), body.get("user_id"))
    return success(None, msg) if ok else param_error(msg)


@admin_bp.post("/coach/unbind_student")
@admin_token_required
def unbind_student():
    body = get_json()
    ok, msg, _ = admin_service.unbind_coach_student(
        current_admin_id(), body.get("coach_id"), body.get("user_id"))
    return success(None, msg) if ok else param_error(msg)


# ---------- 下拉筛选数据源（仅非敏感简要信息） ----------
@admin_bp.get("/common/users")
@admin_token_required
def common_users():
    return success(admin_service.simple_users(get_arg("keyword")), "操作成功")


@admin_bp.get("/common/doctors")
@admin_token_required
def common_doctors():
    return success(admin_service.simple_doctors(), "操作成功")


@admin_bp.get("/common/coaches")
@admin_token_required
def common_coaches():
    return success(admin_service.simple_coaches(), "操作成功")


# =========================== 07 健康数据中心 ===========================
@admin_bp.get("/health_data/statistics")
@admin_token_required
def health_data_statistics():
    data = admin_service.health_data_statistics()
    data["charts"] = admin_service.health_data_charts()
    return success(data, "操作成功")


@admin_bp.get("/health_record/list")
@admin_token_required
def health_record_list():
    page, size, _ = _paging()
    total, rows = admin_service.health_record_list(
        page=page, page_size=size, keyword=get_arg("keyword"),
        user_id=get_arg("user_id"), start_date=get_arg("start_date"),
        end_date=get_arg("end_date"))
    return success(page_result(rows, total, page, size), "操作成功")


@admin_bp.get("/sleep_record/list")
@admin_token_required
def sleep_record_list():
    page, size, _ = _paging()
    total, rows = admin_service.sleep_record_list(
        page=page, page_size=size, keyword=get_arg("keyword"),
        user_id=get_arg("user_id"), start_date=get_arg("start_date"),
        end_date=get_arg("end_date"))
    return success(page_result(rows, total, page, size), "操作成功")


@admin_bp.get("/sport_record/list")
@admin_token_required
def sport_record_list():
    page, size, _ = _paging()
    total, rows = admin_service.sport_record_list(
        page=page, page_size=size, keyword=get_arg("keyword"),
        user_id=get_arg("user_id"), sport_type=get_arg("sport_type"),
        start_date=get_arg("start_date"), end_date=get_arg("end_date"))
    return success(page_result(rows, total, page, size), "操作成功")


# ---------------- CSV 导出（严格遵循当前筛选条件） ----------------
def _csv_response(header, rows, filename):
    """生成带 UTF-8 BOM 的 CSV 响应，Excel 可直接打开且中文不乱码。"""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(header)
    for r in rows:
        writer.writerow(r)
    content = "\ufeff" + buf.getvalue()
    return Response(
        content,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=%s" % filename},
    )


@admin_bp.get("/health_record/export")
@admin_token_required
def health_record_export():
    _, _, _ = get_page()
    total, rows = admin_service.health_record_list(
        page=1, page_size=100000, keyword=get_arg("keyword"),
        user_id=get_arg("user_id"), start_date=get_arg("start_date"),
        end_date=get_arg("end_date"))
    data = [[
        r["id"], r.get("nickname") or "", r.get("phone") or "", r["record_date"],
        r["weight"], r["blood_pressure_high"], r["blood_pressure_low"],
        r["heart_rate"], r["blood_sugar"], r["created_at"],
    ] for r in rows]
    return _csv_response(
        ["ID", "用户昵称", "手机号", "记录日期", "体重(kg)", "收缩压", "舒张压", "心率", "血糖", "录入时间"],
        data, "health_record.csv")


@admin_bp.get("/sleep_record/export")
@admin_token_required
def sleep_record_export():
    total, rows = admin_service.sleep_record_list(
        page=1, page_size=100000, keyword=get_arg("keyword"),
        user_id=get_arg("user_id"), start_date=get_arg("start_date"),
        end_date=get_arg("end_date"))
    data = [[
        r["id"], r.get("nickname") or "", r.get("phone") or "", r["sleep_date"],
        r["sleep_start"], r["sleep_end"], r["sleep_duration"], r["sleep_quality"],
        r["created_at"],
    ] for r in rows]
    return _csv_response(
        ["ID", "用户昵称", "手机号", "睡眠日期", "入睡时间", "起床时间", "时长(分钟)", "睡眠质量", "录入时间"],
        data, "sleep_record.csv")


@admin_bp.get("/sport_record/export")
@admin_token_required
def sport_record_export():
    total, rows = admin_service.sport_record_list(
        page=1, page_size=100000, keyword=get_arg("keyword"),
        user_id=get_arg("user_id"), sport_type=get_arg("sport_type"),
        start_date=get_arg("start_date"), end_date=get_arg("end_date"))
    data = [[
        r["id"], r.get("nickname") or "", r.get("phone") or "", r["sport_date"],
        r["sport_type"], r["sport_duration"], r["calorie"], r.get("remark") or "",
        r["created_at"],
    ] for r in rows]
    return _csv_response(
        ["ID", "用户昵称", "手机号", "运动日期", "运动类型", "时长(分钟)", "卡路里", "备注", "录入时间"],
        data, "sport_record.csv")


# =========================== 08 健康计划管理 ===========================
@admin_bp.get("/health_plan/list")
@admin_token_required
def health_plan_list():
    page, size, _ = _paging()
    total, rows = admin_service.health_plan_list(
        page=page, page_size=size, keyword=get_arg("keyword"),
        user_id=get_arg("user_id"), plan_status=get_arg("plan_status"),
        start_date=get_arg("start_date"), end_date=get_arg("end_date"))
    return success(page_result(rows, total, page, size), "操作成功")


@admin_bp.get("/health_plan/stats")
@admin_token_required
def health_plan_stats():
    return success(admin_service.health_plan_stats(), "操作成功")


# =========================== 09 医生业务监管 ===========================
@admin_bp.get("/doctor_advice/list")
@admin_token_required
def doctor_advice_list():
    page, size, _ = _paging()
    total, rows = admin_service.doctor_advice_list(
        page=page, page_size=size, doctor_id=get_arg("doctor_id"),
        user_id=get_arg("user_id"), keyword=get_arg("keyword"),
        start_date=get_arg("start_date"), end_date=get_arg("end_date"))
    return success(page_result(rows, total, page, size), "操作成功")


@admin_bp.get("/medical_notice/list")
@admin_token_required
def medical_notice_list():
    page, size, _ = _paging()
    total, rows = admin_service.medical_notice_list(
        page=page, page_size=size, doctor_id=get_arg("doctor_id"),
        user_id=get_arg("user_id"), keyword=get_arg("keyword"),
        start_date=get_arg("start_date"), end_date=get_arg("end_date"))
    return success(page_result(rows, total, page, size), "操作成功")


@admin_bp.get("/medical_record/list")
@admin_token_required
def medical_record_list():
    page, size, _ = _paging()
    total, rows = admin_service.medical_record_list(
        page=page, page_size=size, doctor_id=get_arg("doctor_id"),
        user_id=get_arg("user_id"), keyword=get_arg("keyword"),
        start_date=get_arg("start_date"), end_date=get_arg("end_date"))
    return success(page_result(rows, total, page, size), "操作成功")


# =========================== 10 健身业务监管 ===========================
@admin_bp.get("/sport_goal/list")
@admin_token_required
def sport_goal_list():
    page, size, _ = _paging()
    total, rows = admin_service.sport_goal_list(
        page=page, page_size=size, coach_id=get_arg("coach_id"),
        user_id=get_arg("user_id"), goal_status=get_arg("goal_status"),
        keyword=get_arg("keyword"), start_date=get_arg("start_date"),
        end_date=get_arg("end_date"))
    return success(page_result(rows, total, page, size), "操作成功")


@admin_bp.get("/training_plan/list")
@admin_token_required
def training_plan_list():
    page, size, _ = _paging()
    total, rows = admin_service.training_plan_list(
        page=page, page_size=size, coach_id=get_arg("coach_id"),
        user_id=get_arg("user_id"), plan_status=get_arg("plan_status"),
        keyword=get_arg("keyword"), start_date=get_arg("start_date"),
        end_date=get_arg("end_date"))
    return success(page_result(rows, total, page, size), "操作成功")


@admin_bp.get("/fitness_advice/list")
@admin_token_required
def fitness_advice_list():
    page, size, _ = _paging()
    total, rows = admin_service.fitness_advice_list(
        page=page, page_size=size, coach_id=get_arg("coach_id"),
        user_id=get_arg("user_id"), keyword=get_arg("keyword"),
        start_date=get_arg("start_date"), end_date=get_arg("end_date"))
    return success(page_result(rows, total, page, size), "操作成功")


# =========================== 11 内容运营管理 ===========================
# ---- 健康科普 ----
@admin_bp.get("/article/list")
@admin_token_required
def article_list():
    page, size, _ = _paging()
    total, rows = content_service.list_article(
        page=page, page_size=size, keyword=get_arg("keyword"),
        is_show=get_arg("is_show"), admin=True)
    return success(page_result(rows, total, page, size), "操作成功")


@admin_bp.get("/article/detail")
@admin_token_required
def article_detail():
    article_id = _int_arg("id")
    if not article_id:
        return param_error("缺少文章 id")
    row = content_service.article_detail(article_id, admin=True)
    if not row:
        return param_error("文章不存在")
    return success(row, "操作成功")


@admin_bp.post("/article/save")
@admin_token_required
def article_save():
    body = get_json()
    is_new = not to_int(body.get("id"))
    ok, msg, data = content_service.save_article(body)
    if ok:
        from utils.audit_log import write_admin_log
        write_admin_log(current_admin_id(),
                        "文章新增" if is_new else "文章编辑",
                        "%s：%s" % ("新增" if is_new else "编辑", body.get("title")),
                        "health_article", data.get("id") if data else None)
    return success(data, msg) if ok else param_error(msg)


@admin_bp.post("/article/del")
@admin_token_required
def article_del():
    body = get_json()
    article_id = to_int(body.get("id"))
    if not article_id:
        return param_error("缺少文章 id")
    ok, msg, data = content_service.delete_article(article_id)
    if ok:
        from utils.audit_log import write_admin_log
        write_admin_log(current_admin_id(), "文章删除",
                        "删除文章：%s" % (data or {}).get("title", ""), "health_article", article_id)
    return success(None, msg) if ok else param_error(msg)


@admin_bp.post("/article/upload_cover")
@admin_token_required
def article_upload_cover():
    file = request.files.get("file") or request.files.get("cover")
    filename, err = save_upload_file(file)
    if err:
        return param_error(err)
    return success({"cover_img": filename}, "封面上传成功")


# ---- 系统公告 ----
@admin_bp.get("/notice/list")
@admin_token_required
def notice_list():
    page, size, _ = _paging()
    total, rows = content_service.list_notice(
        page=page, page_size=size, keyword=get_arg("keyword"),
        is_show=get_arg("is_show"), admin=True)
    return success(page_result(rows, total, page, size), "操作成功")


@admin_bp.get("/notice/detail")
@admin_token_required
def notice_detail():
    notice_id = _int_arg("id")
    if not notice_id:
        return param_error("缺少公告 id")
    row = content_service.notice_detail(notice_id, admin=True)
    if not row:
        return param_error("公告不存在")
    return success(row, "操作成功")


@admin_bp.post("/notice/save")
@admin_token_required
def notice_save():
    body = get_json()
    is_new = not to_int(body.get("id"))
    ok, msg, data = content_service.save_notice(body)
    if ok:
        from utils.audit_log import write_admin_log
        write_admin_log(current_admin_id(),
                        "公告新增" if is_new else "公告编辑",
                        "%s：%s" % ("新增" if is_new else "编辑", body.get("title")),
                        "notice", data.get("id") if data else None)
    return success(data, msg) if ok else param_error(msg)


@admin_bp.post("/notice/del")
@admin_token_required
def notice_del():
    body = get_json()
    notice_id = to_int(body.get("id"))
    if not notice_id:
        return param_error("缺少公告 id")
    ok, msg, data = content_service.delete_notice(notice_id)
    if ok:
        from utils.audit_log import write_admin_log
        write_admin_log(current_admin_id(), "公告删除",
                        "删除公告：%s" % (data or {}).get("title", ""), "notice", notice_id)
    return success(None, msg) if ok else param_error(msg)


# =========================== 12 系统管理 ===========================
@admin_bp.get("/operation_log/list")
@admin_token_required
def operation_log_list():
    """操作日志只读。"""
    page, size, _ = _paging()
    total, rows = admin_service.operation_log_list(
        page=page, page_size=size, admin_id=get_arg("admin_id"),
        operation_type=get_arg("operation_type"), keyword=get_arg("keyword"),
        start_date=get_arg("start_date"), end_date=get_arg("end_date"))
    return success(page_result(rows, total, page, size), "操作成功")


@admin_bp.get("/operation_log/types")
@admin_token_required
def operation_log_types():
    return success(admin_service.operation_types(), "操作成功")


@admin_bp.get("/system/info")
@admin_token_required
def system_info():
    """系统信息：只展示非敏感信息。"""
    return success(admin_service.system_info(), "操作成功")


@admin_bp.post("/upload_avatar")
@admin_token_required
def upload_avatar():
    file = request.files.get("file") or request.files.get("avatar")
    filename, err = save_upload_file(file)
    if err:
        return param_error(err)
    ok, msg, data = admin_service.update_avatar(current_admin_id(), filename)
    return success(data, msg) if ok else param_error(msg)


@admin_bp.post("/update_pwd")
@admin_token_required
def update_pwd():
    body = get_json()
    ok, msg, _ = admin_service.update_password(
        current_admin_id(), body.get("old_password"), body.get("new_password"))
    return success(None, msg) if ok else param_error(msg)


@admin_bp.post("/logout")
@admin_token_required
def logout():
    return success(None, "已退出登录")
