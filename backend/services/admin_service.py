# -*- coding: utf-8 -*-
"""管理员业务：登录 / 系统首页 / 用户 / 医生 / 教练 / 审核 / 关系 / 数据监管 / 内容 / 系统。

管理员为监管角色：
- 可编辑医生、教练基础资料，可重置其密码（均写操作日志）
- 禁止篡改普通用户原始健康数据（本模块不提供任何用户健康数据写接口）
- 禁止冒充医生发布专业建议（本模块不提供医生业务写接口）
"""
import datetime

from utils import db
from utils.audit_log import write_admin_log
from utils.helpers import fmt_date, fmt_datetime, to_int, to_str
from utils.jwt_utils import gen_admin_token
from utils.security import check_password_strength, hash_password, verify_password

DEFAULT_AVATAR = "default_admin.jpg"
AUDIT_TEXT = {0: "待审核", 1: "审核通过", 2: "审核拒绝"}
GOAL_STATUS_TEXT = {0: "进行中", 1: "已完成", 2: "已结束"}
PLAN_STATUS_TEXT = {0: "进行中", 1: "已完成", 2: "已放弃"}


# =========================== 登录 / 资料 ===========================
def login(admin_name, password):
    admin_name = to_str(admin_name)
    if not admin_name or not password:
        return False, "请输入管理员账号和密码", None
    row = db.query_one("SELECT * FROM admin_user WHERE admin_name=%s", (admin_name,))
    if not row or not verify_password(row["password_hash"], password):
        return False, "账号或密码错误", None

    token = gen_admin_token(row["id"])
    return True, "登录成功", {"token": token, "admin_info": _public_admin(row)}


def _public_admin(row):
    return {
        "id": row["id"],
        "admin_name": row["admin_name"],
        "real_name": row["real_name"],
        "avatar": row["avatar"] or DEFAULT_AVATAR,
        "created_at": fmt_datetime(row["created_at"]),
    }


def get_info(admin_id):
    row = db.query_one("SELECT * FROM admin_user WHERE id=%s", (admin_id,))
    if not row:
        return False, "管理员不存在", None
    return True, "操作成功", _public_admin(row)


def update_password(admin_id, old_pwd, new_pwd):
    if not old_pwd or not new_pwd:
        return False, "请填写原密码与新密码", None
    ok, msg = check_password_strength(new_pwd)
    if not ok:
        return False, msg, None
    row = db.query_one("SELECT password_hash FROM admin_user WHERE id=%s", (admin_id,))
    if not row or not verify_password(row["password_hash"], old_pwd):
        return False, "原密码不正确", None
    if old_pwd == new_pwd:
        return False, "新密码不能与原密码相同", None
    db.execute("UPDATE admin_user SET password_hash=%s WHERE id=%s",
               (hash_password(new_pwd), admin_id))
    return True, "密码修改成功", None


def update_avatar(admin_id, filename):
    db.execute("UPDATE admin_user SET avatar=%s WHERE id=%s", (filename, admin_id))
    return True, "头像更新成功", {"avatar": filename}


# =========================== 01 系统首页 ===========================
def dashboard():
    today = datetime.date.today()
    week_ago = today - datetime.timedelta(days=6)

    stats = {
        "user_count": int(db.query_scalar("SELECT COUNT(*) AS c FROM users")),
        "doctor_count": int(db.query_scalar("SELECT COUNT(*) AS c FROM doctor_user")),
        "coach_count": int(db.query_scalar("SELECT COUNT(*) AS c FROM coach_user")),
        "today_user_count": int(db.query_scalar(
            "SELECT COUNT(*) AS c FROM users WHERE DATE(created_at)=%s", (today,))),
        "today_health_count": int(db.query_scalar(
            "SELECT COUNT(*) AS c FROM health_record WHERE record_date=%s", (today,))),
        "pending_doctor": int(db.query_scalar(
            "SELECT COUNT(*) AS c FROM doctor_user WHERE audit_status=0")),
        "pending_coach": int(db.query_scalar(
            "SELECT COUNT(*) AS c FROM coach_user WHERE audit_status=0")),
        "running_plan": int(db.query_scalar(
            "SELECT COUNT(*) AS c FROM health_plan WHERE plan_status=0")),
        "article_count": int(db.query_scalar("SELECT COUNT(*) AS c FROM health_article")),
        "today_sport_count": int(db.query_scalar(
            "SELECT COUNT(*) AS c FROM sport_record WHERE sport_date=%s", (today,))),
    }

    # ---- 图表：最近 7 天新增用户 ----
    u_rows = db.query_all(
        "SELECT DATE(created_at) AS d, COUNT(*) AS c FROM users "
        "WHERE DATE(created_at) >= %s GROUP BY DATE(created_at)", (week_ago,))
    u_map = {fmt_date(r["d"]): int(r["c"]) for r in u_rows}
    user_trend = [
        {"date": fmt_date(today - datetime.timedelta(days=i)),
         "value": u_map.get(fmt_date(today - datetime.timedelta(days=i)), 0)}
        for i in range(6, -1, -1)
    ]

    # ---- 图表：最近 7 天健康数据录入（健康指标 / 睡眠 / 运动） ----
    h_rows = db.query_all(
        "SELECT record_date AS d, COUNT(*) AS c FROM health_record "
        "WHERE record_date >= %s GROUP BY record_date", (week_ago,))
    s_rows = db.query_all(
        "SELECT sleep_date AS d, COUNT(*) AS c FROM sleep_record "
        "WHERE sleep_date >= %s GROUP BY sleep_date", (week_ago,))
    sp_rows = db.query_all(
        "SELECT sport_date AS d, COUNT(*) AS c FROM sport_record "
        "WHERE sport_date >= %s GROUP BY sport_date", (week_ago,))
    h_map = {fmt_date(r["d"]): int(r["c"]) for r in h_rows}
    s_map = {fmt_date(r["d"]): int(r["c"]) for r in s_rows}
    sp_map = {fmt_date(r["d"]): int(r["c"]) for r in sp_rows}
    health_trend = []
    for i in range(6, -1, -1):
        d = fmt_date(today - datetime.timedelta(days=i))
        health_trend.append({
            "date": d,
            "health": h_map.get(d, 0),
            "sleep": s_map.get(d, 0),
            "sport": sp_map.get(d, 0),
        })

    # ---- 图表：睡眠质量分布 ----
    sleep_dist = db.query_all(
        "SELECT sleep_quality AS name, COUNT(*) AS value FROM sleep_record "
        "GROUP BY sleep_quality")
    sleep_distribution = [
        {"name": r["name"] or "未填写", "value": int(r["value"])} for r in sleep_dist]

    # ---- 图表：运动类型分布 ----
    type_dist = db.query_all(
        "SELECT sport_type AS name, COALESCE(SUM(sport_duration),0) AS value, "
        "COUNT(*) AS cnt FROM sport_record GROUP BY sport_type ORDER BY value DESC")
    sport_distribution = [
        {"name": r["name"] or "其他", "value": int(r["value"]), "count": int(r["cnt"])}
        for r in type_dist]

    # ---- 图表：健康计划状态分布 ----
    plan_dist = db.query_all(
        "SELECT plan_status AS s, COUNT(*) AS c FROM health_plan GROUP BY plan_status")
    plan_map = {int(r["s"]): int(r["c"]) for r in plan_dist}
    plan_distribution = [
        {"name": PLAN_STATUS_TEXT[i], "value": plan_map.get(i, 0)} for i in (0, 1, 2)
    ]

    # ---- 图表：最近 30 天运动时长趋势 ----
    month_ago = today - datetime.timedelta(days=29)
    sport_day = db.query_all(
        "SELECT sport_date AS d, COALESCE(SUM(sport_duration),0) AS c FROM sport_record "
        "WHERE sport_date >= %s GROUP BY sport_date ORDER BY sport_date ASC", (month_ago,))
    sd_map = {fmt_date(r["d"]): int(r["c"]) for r in sport_day}
    sport_30_trend = [
        {"date": fmt_date(month_ago + datetime.timedelta(days=i)),
         "value": sd_map.get(fmt_date(month_ago + datetime.timedelta(days=i)), 0)}
        for i in range(30)
    ]

    # ---- 快捷待办 ----
    pending_doctors = db.query_all(
        """SELECT id, doctor_name, real_name, gender, phone, specialty, created_at
           FROM doctor_user WHERE audit_status=0 ORDER BY created_at DESC LIMIT 5""")
    for r in pending_doctors:
        r["created_at"] = fmt_datetime(r["created_at"])

    pending_coaches = db.query_all(
        """SELECT id, coach_name, real_name, gender, phone, specialty, created_at
           FROM coach_user WHERE audit_status=0 ORDER BY created_at DESC LIMIT 5""")
    for r in pending_coaches:
        r["created_at"] = fmt_datetime(r["created_at"])

    latest_users = db.query_all(
        """SELECT id, nickname, phone, gender, avatar, created_at
           FROM users ORDER BY id DESC LIMIT 5""")
    for r in latest_users:
        r["created_at"] = fmt_datetime(r["created_at"])

    latest_logs = db.query_all(
        """SELECT l.id, l.operation_type, l.operation_content, l.target_type,
                  l.target_id, l.created_at, a.admin_name
           FROM admin_operation_log l
           LEFT JOIN admin_user a ON a.id = l.admin_id
           ORDER BY l.id DESC LIMIT 8""")
    for r in latest_logs:
        r["created_at"] = fmt_datetime(r["created_at"])

    return {
        "stats": stats,
        "user_trend": user_trend,
        "health_trend": health_trend,
        "sleep_distribution": sleep_distribution,
        "sport_distribution": sport_distribution,
        "plan_distribution": plan_distribution,
        "sport_30_trend": sport_30_trend,
        "pending_doctors": pending_doctors,
        "pending_coaches": pending_coaches,
        "latest_users": latest_users,
        "latest_logs": latest_logs,
    }


# =========================== 02 普通用户管理 ===========================
def user_list(page=1, page_size=10, nickname=None, phone=None, gender=None,
              start_date=None, end_date=None):
    where, args = [], []
    if nickname:
        where.append("nickname LIKE %s")
        args.append("%" + nickname + "%")
    if phone:
        where.append("phone LIKE %s")
        args.append("%" + phone + "%")
    if gender:
        where.append("gender=%s")
        args.append(gender)
    if start_date:
        where.append("DATE(created_at) >= %s")
        args.append(start_date)
    if end_date:
        where.append("DATE(created_at) <= %s")
        args.append(end_date)
    cond = (" WHERE " + " AND ".join(where)) if where else ""

    total = db.query_scalar("SELECT COUNT(*) AS c FROM users" + cond, tuple(args))
    rows = db.query_all(
        "SELECT id, phone, nickname, avatar, gender, age, height, created_at FROM users"
        + cond + " ORDER BY id DESC LIMIT %s OFFSET %s",
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for r in rows:
        r["height"] = float(r["height"]) if r["height"] is not None else None
        r["created_at"] = fmt_datetime(r["created_at"])
        # 关联负责医生 / 教练数量
        r["doctor_count"] = int(db.query_scalar(
            "SELECT COUNT(*) AS c FROM doctor_patient WHERE user_id=%s", (r["id"],)))
        r["coach_count"] = int(db.query_scalar(
            "SELECT COUNT(*) AS c FROM coach_student WHERE user_id=%s", (r["id"],)))
    return total, rows


def user_detail(user_id):
    """用户完整健康档案（只读）。管理员禁止修改用户原始健康数据。"""
    row = db.query_one(
        "SELECT id, phone, nickname, avatar, gender, age, height, created_at "
        "FROM users WHERE id=%s", (user_id,))
    if not row:
        return None
    row["height"] = float(row["height"]) if row["height"] is not None else None
    row["created_at"] = fmt_datetime(row["created_at"])

    # 负责医生
    doctors = db.query_all(
        """SELECT d.id, d.doctor_name, d.real_name, d.specialty, d.phone
           FROM doctor_patient dp JOIN doctor_user d ON d.id = dp.doctor_id
           WHERE dp.user_id=%s""", (user_id,))
    # 负责教练
    coaches = db.query_all(
        """SELECT c.id, c.coach_name, c.real_name, c.specialty, c.phone
           FROM coach_student cs JOIN coach_user c ON c.id = cs.coach_id
           WHERE cs.user_id=%s""", (user_id,))

    heatlh_total = int(db.query_scalar(
        "SELECT COUNT(*) AS c FROM health_record WHERE user_id=%s", (user_id,)))
    sleep_total = int(db.query_scalar(
        "SELECT COUNT(*) AS c FROM sleep_record WHERE user_id=%s", (user_id,)))
    sport_total = int(db.query_scalar(
        "SELECT COUNT(*) AS c FROM sport_record WHERE user_id=%s", (user_id,)))
    plan_total = int(db.query_scalar(
        "SELECT COUNT(*) AS c FROM health_plan WHERE user_id=%s", (user_id,)))

    row["doctors"] = doctors
    row["coaches"] = coaches
    row["counts"] = {
        "health_record": heatlh_total,
        "sleep_record": sleep_total,
        "sport_record": sport_total,
        "health_plan": plan_total,
    }
    return row


def user_health_data(user_id, data_type, page=1, page_size=10,
                     start_date=None, end_date=None, sport_type=None):
    """按 Tab 读取用户健康档案数据（只读）。"""
    from services import health_service
    if data_type == "health":
        return health_service.list_health_record(user_id, page, page_size, start_date, end_date)
    if data_type == "sleep":
        return health_service.list_sleep_record(user_id, page, page_size, start_date, end_date)
    if data_type == "sport":
        return health_service.list_sport_record(user_id, page, page_size, start_date, end_date, sport_type)
    if data_type == "plan":
        return health_service.list_health_plan(user_id, page, page_size)
    return 0, []


def user_doctor_service(user_id):
    from services import user_service
    detail = user_detail(user_id) or {}
    return {
        "doctors": detail.get("doctors", []),
        "advice": user_service.my_doctor_advice(user_id),
        "medical_notice": user_service.my_medical_notice(user_id),
        "medical_record": user_service.my_medical_record(user_id),
    }


def user_coach_service(user_id):
    from services import user_service
    detail = user_detail(user_id) or {}
    return {
        "coaches": detail.get("coaches", []),
        "sport_goal": user_service.my_sport_goal(user_id),
        "training_plan": user_service.my_training_plan(user_id),
        "fitness_advice": user_service.my_fitness_advice(user_id),
    }


# =========================== 03 医生管理 ===========================
def doctor_list(page=1, page_size=10, doctor_name=None, real_name=None, phone=None,
                specialty=None, audit_status=None):
    where, args = [], []
    if doctor_name:
        where.append("doctor_name LIKE %s")
        args.append("%" + doctor_name + "%")
    if real_name:
        where.append("real_name LIKE %s")
        args.append("%" + real_name + "%")
    if phone:
        where.append("phone LIKE %s")
        args.append("%" + phone + "%")
    if specialty:
        where.append("specialty LIKE %s")
        args.append("%" + specialty + "%")
    if audit_status not in (None, ""):
        where.append("audit_status=%s")
        args.append(to_int(audit_status))
    cond = (" WHERE " + " AND ".join(where)) if where else ""

    total = db.query_scalar("SELECT COUNT(*) AS c FROM doctor_user" + cond, tuple(args))
    rows = db.query_all(
        """SELECT id, doctor_name, real_name, gender, phone, specialty, avatar,
                  audit_status, created_at FROM doctor_user""" + cond +
        " ORDER BY id DESC LIMIT %s OFFSET %s",
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for r in rows:
        r["audit_status_text"] = AUDIT_TEXT.get(r["audit_status"], "未知")
        r["created_at"] = fmt_datetime(r["created_at"])
        r["patient_count"] = int(db.query_scalar(
            "SELECT COUNT(*) AS c FROM doctor_patient WHERE doctor_id=%s", (r["id"],)))
    return total, rows


def doctor_detail(doctor_id):
    row = db.query_one("SELECT * FROM doctor_user WHERE id=%s", (doctor_id,))
    if not row:
        return None
    row.pop("password_hash", None)  # 绝不外泄密码哈希
    row["audit_status_text"] = AUDIT_TEXT.get(row["audit_status"], "未知")
    row["created_at"] = fmt_datetime(row["created_at"])
    row["patient_count"] = int(db.query_scalar(
        "SELECT COUNT(*) AS c FROM doctor_patient WHERE doctor_id=%s", (doctor_id,)))
    row["patients"] = db.query_all(
        """SELECT u.id, u.nickname, u.phone, u.gender, u.age, u.avatar
           FROM doctor_patient dp JOIN users u ON u.id=dp.user_id
           WHERE dp.doctor_id=%s ORDER BY dp.id DESC""", (doctor_id,))
    row["business"] = {
        "advice_count": int(db.query_scalar(
            "SELECT COUNT(*) AS c FROM doctor_advice WHERE doctor_id=%s", (doctor_id,))),
        "notice_count": int(db.query_scalar(
            "SELECT COUNT(*) AS c FROM medical_notice WHERE doctor_id=%s", (doctor_id,))),
        "record_count": int(db.query_scalar(
            "SELECT COUNT(*) AS c FROM medical_record WHERE doctor_id=%s", (doctor_id,))),
    }
    return row


def doctor_update(admin_id, doctor_id, data):
    row = db.query_one("SELECT * FROM doctor_user WHERE id=%s", (doctor_id,))
    if not row:
        return False, "医生不存在", None

    fields, args, changed = [], [], []
    mapping = {
        "real_name": "姓名", "gender": "性别", "phone": "手机号", "specialty": "专业方向",
    }
    for key, label in mapping.items():
        value = to_str(data.get(key))
        if value is not None:
            fields.append("%s=%%s" % key)
            args.append(value)
            changed.append("%s=%s" % (label, value))
    if not fields:
        return False, "没有需要更新的内容", None

    args.append(doctor_id)
    db.execute("UPDATE doctor_user SET %s WHERE id=%%s" % ", ".join(fields), tuple(args))
    # 记录资料修改日志（不含任何敏感字段）
    write_admin_log(admin_id, "医生资料修改",
                    "修改医生[%s]资料：%s" % (row["doctor_name"], "，".join(changed)),
                    "doctor", doctor_id)
    return True, "医生资料更新成功", None


def doctor_reset_pwd(admin_id, doctor_id, new_pwd):
    ok, msg = check_password_strength(new_pwd)
    if not ok:
        return False, msg, None
    row = db.query_one("SELECT doctor_name FROM doctor_user WHERE id=%s", (doctor_id,))
    if not row:
        return False, "医生不存在", None
    db.execute("UPDATE doctor_user SET password_hash=%s WHERE id=%s",
               (hash_password(new_pwd), doctor_id))
    # 日志只记录"已重置"，绝不记录密码明文或哈希
    write_admin_log(admin_id, "医生密码重置",
                    "重置医生[%s]登录密码" % row["doctor_name"], "doctor", doctor_id)
    return True, "密码重置成功", None


def doctor_audit(admin_id, doctor_id, audit_status):
    """审核医生：1 通过 / 2 拒绝。"""
    audit_status = to_int(audit_status)
    if audit_status not in (1, 2):
        return False, "审核状态参数不合法", None
    row = db.query_one(
        "SELECT doctor_name, real_name, audit_status FROM doctor_user WHERE id=%s", (doctor_id,))
    if not row:
        return False, "医生不存在", None
    if row["audit_status"] != 0:
        return False, "该申请已完成审核，无需重复操作", None

    db.execute("UPDATE doctor_user SET audit_status=%s WHERE id=%s", (audit_status, doctor_id))
    op = "医生审核通过" if audit_status == 1 else "医生审核拒绝"
    write_admin_log(admin_id, op,
                    "%s：医生[%s]（%s）" % (op, row["doctor_name"], row["real_name"] or "-"),
                    "doctor", doctor_id)
    return True, "审核%s" % ("通过" if audit_status == 1 else "已拒绝"), None


# =========================== 04 健身教练管理 ===========================
def coach_list(page=1, page_size=10, coach_name=None, real_name=None, phone=None,
               specialty=None, audit_status=None):
    where, args = [], []
    if coach_name:
        where.append("coach_name LIKE %s")
        args.append("%" + coach_name + "%")
    if real_name:
        where.append("real_name LIKE %s")
        args.append("%" + real_name + "%")
    if phone:
        where.append("phone LIKE %s")
        args.append("%" + phone + "%")
    if specialty:
        where.append("specialty LIKE %s")
        args.append("%" + specialty + "%")
    if audit_status not in (None, ""):
        where.append("audit_status=%s")
        args.append(to_int(audit_status))
    cond = (" WHERE " + " AND ".join(where)) if where else ""

    total = db.query_scalar("SELECT COUNT(*) AS c FROM coach_user" + cond, tuple(args))
    rows = db.query_all(
        """SELECT id, coach_name, real_name, gender, phone, specialty, avatar,
                  audit_status, created_at FROM coach_user""" + cond +
        " ORDER BY id DESC LIMIT %s OFFSET %s",
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for r in rows:
        r["audit_status_text"] = AUDIT_TEXT.get(r["audit_status"], "未知")
        r["created_at"] = fmt_datetime(r["created_at"])
        r["student_count"] = int(db.query_scalar(
            "SELECT COUNT(*) AS c FROM coach_student WHERE coach_id=%s", (r["id"],)))
    return total, rows


def coach_detail(coach_id):
    row = db.query_one("SELECT * FROM coach_user WHERE id=%s", (coach_id,))
    if not row:
        return None
    row.pop("password_hash", None)
    row["audit_status_text"] = AUDIT_TEXT.get(row["audit_status"], "未知")
    row["created_at"] = fmt_datetime(row["created_at"])
    row["student_count"] = int(db.query_scalar(
        "SELECT COUNT(*) AS c FROM coach_student WHERE coach_id=%s", (coach_id,)))
    row["students"] = db.query_all(
        """SELECT u.id, u.nickname, u.phone, u.gender, u.age, u.avatar
           FROM coach_student cs JOIN users u ON u.id=cs.user_id
           WHERE cs.coach_id=%s ORDER BY cs.id DESC""", (coach_id,))
    row["business"] = {
        "goal_count": int(db.query_scalar(
            "SELECT COUNT(*) AS c FROM sport_goal WHERE coach_id=%s", (coach_id,))),
        "plan_count": int(db.query_scalar(
            "SELECT COUNT(*) AS c FROM training_plan WHERE coach_id=%s", (coach_id,))),
        "advice_count": int(db.query_scalar(
            "SELECT COUNT(*) AS c FROM fitness_advice WHERE coach_id=%s", (coach_id,))),
    }
    return row


def coach_update(admin_id, coach_id, data):
    row = db.query_one("SELECT * FROM coach_user WHERE id=%s", (coach_id,))
    if not row:
        return False, "健身教练不存在", None

    fields, args, changed = [], [], []
    mapping = {
        "real_name": "姓名", "gender": "性别", "phone": "手机号", "specialty": "专业方向",
    }
    for key, label in mapping.items():
        value = to_str(data.get(key))
        if value is not None:
            fields.append("%s=%%s" % key)
            args.append(value)
            changed.append("%s=%s" % (label, value))
    if not fields:
        return False, "没有需要更新的内容", None

    args.append(coach_id)
    db.execute("UPDATE coach_user SET %s WHERE id=%%s" % ", ".join(fields), tuple(args))
    write_admin_log(admin_id, "教练资料修改",
                    "修改教练[%s]资料：%s" % (row["coach_name"], "，".join(changed)),
                    "coach", coach_id)
    return True, "教练资料更新成功", None


def coach_reset_pwd(admin_id, coach_id, new_pwd):
    ok, msg = check_password_strength(new_pwd)
    if not ok:
        return False, msg, None
    row = db.query_one("SELECT coach_name FROM coach_user WHERE id=%s", (coach_id,))
    if not row:
        return False, "健身教练不存在", None
    db.execute("UPDATE coach_user SET password_hash=%s WHERE id=%s",
               (hash_password(new_pwd), coach_id))
    write_admin_log(admin_id, "教练密码重置",
                    "重置教练[%s]登录密码" % row["coach_name"], "coach", coach_id)
    return True, "密码重置成功", None


def coach_audit(admin_id, coach_id, audit_status):
    audit_status = to_int(audit_status)
    if audit_status not in (1, 2):
        return False, "审核状态参数不合法", None
    row = db.query_one(
        "SELECT coach_name, real_name, audit_status FROM coach_user WHERE id=%s", (coach_id,))
    if not row:
        return False, "健身教练不存在", None
    if row["audit_status"] != 0:
        return False, "该申请已完成审核，无需重复操作", None

    db.execute("UPDATE coach_user SET audit_status=%s WHERE id=%s", (audit_status, coach_id))
    op = "教练审核通过" if audit_status == 1 else "教练审核拒绝"
    write_admin_log(admin_id, op,
                    "%s：教练[%s]（%s）" % (op, row["coach_name"], row["real_name"] or "-"),
                    "coach", coach_id)
    return True, "审核%s" % ("通过" if audit_status == 1 else "已拒绝"), None


# =========================== 05 账号审核中心 ===========================
def audit_overview():
    today = datetime.date.today()
    return {
        "pending_doctor": int(db.query_scalar(
            "SELECT COUNT(*) AS c FROM doctor_user WHERE audit_status=0")),
        "pending_coach": int(db.query_scalar(
            "SELECT COUNT(*) AS c FROM coach_user WHERE audit_status=0")),
        "today_audited": int(db.query_scalar(
            """SELECT COUNT(*) AS c FROM admin_operation_log
               WHERE operation_type IN ('医生审核通过','医生审核拒绝','教练审核通过','教练审核拒绝')
                 AND DATE(created_at)=%s""", (today,))),
        "total_apply": int(
            db.query_scalar("SELECT COUNT(*) AS c FROM doctor_user")
            + db.query_scalar("SELECT COUNT(*) AS c FROM coach_user")
        ),
    }


def audit_record_list(page=1, page_size=10, audit_type=None, keyword=None,
                      start_date=None, end_date=None):
    """审核记录（来自管理员操作日志）。"""
    where = ["operation_type IN ('医生审核通过','医生审核拒绝','教练审核通过','教练审核拒绝')"]
    args = []
    if audit_type == "doctor":
        where.append("operation_type LIKE '医生%'")
    elif audit_type == "coach":
        where.append("operation_type LIKE '教练%'")
    if keyword:
        where.append("operation_content LIKE %s")
        args.append("%" + keyword + "%")
    if start_date:
        where.append("DATE(created_at) >= %s")
        args.append(start_date)
    if end_date:
        where.append("DATE(created_at) <= %s")
        args.append(end_date)
    cond = " WHERE " + " AND ".join(where)

    total = db.query_scalar("SELECT COUNT(*) AS c FROM admin_operation_log" + cond, tuple(args))
    rows = db.query_all(
        """SELECT l.*, a.admin_name FROM admin_operation_log l
           LEFT JOIN admin_user a ON a.id=l.admin_id""" + cond +
        " ORDER BY l.id DESC LIMIT %s OFFSET %s",
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for r in rows:
        r["created_at"] = fmt_datetime(r["created_at"])
    return total, rows


# =========================== 06 角色关系管理 ===========================
def doctor_patient_list(page=1, page_size=10, doctor_id=None, user_keyword=None):
    where, args = [], []
    if doctor_id:
        where.append("dp.doctor_id=%s")
        args.append(to_int(doctor_id))
    if user_keyword:
        where.append("(u.nickname LIKE %s OR u.phone LIKE %s)")
        args.extend(["%" + user_keyword + "%", "%" + user_keyword + "%"])
    cond = (" WHERE " + " AND ".join(where)) if where else ""

    total = db.query_scalar(
        "SELECT COUNT(*) AS c FROM doctor_patient dp JOIN users u ON u.id=dp.user_id" + cond,
        tuple(args))
    rows = db.query_all(
        """SELECT dp.id, dp.doctor_id, dp.user_id, dp.created_at,
                  d.doctor_name, d.real_name AS doctor_real_name, d.specialty,
                  u.nickname, u.phone, u.gender, u.age, u.avatar
           FROM doctor_patient dp
           JOIN doctor_user d ON d.id = dp.doctor_id
           JOIN users u ON u.id = dp.user_id""" + cond +
        " ORDER BY dp.id DESC LIMIT %s OFFSET %s",
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for r in rows:
        r["created_at"] = fmt_datetime(r["created_at"])
    return total, rows


def bind_doctor_patient(admin_id, doctor_id, user_id):
    doctor_id, user_id = to_int(doctor_id), to_int(user_id)
    if not doctor_id or not user_id:
        return False, "请选择医生与患者", None
    doctor = db.query_one("SELECT doctor_name, audit_status FROM doctor_user WHERE id=%s", (doctor_id,))
    if not doctor:
        return False, "医生不存在", None
    if doctor["audit_status"] != 1:
        return False, "该医生账号未通过审核，不能建立医患关系", None
    user = db.query_one("SELECT nickname FROM users WHERE id=%s", (user_id,))
    if not user:
        return False, "用户不存在", None
    # 防重复绑定（数据库唯一约束 + 应用层预校验）
    exists = db.query_one(
        "SELECT id FROM doctor_patient WHERE doctor_id=%s AND user_id=%s", (doctor_id, user_id))
    if exists:
        return False, "该医患关系已存在，请勿重复绑定", None

    db.execute("INSERT INTO doctor_patient (doctor_id, user_id, created_at) VALUES (%s, %s, NOW())",
               (doctor_id, user_id))
    write_admin_log(admin_id, "医患绑定",
                    "绑定医患关系：医生[%s] <-> 患者[%s]" % (doctor["doctor_name"], user["nickname"]),
                    "doctor_patient", doctor_id)
    return True, "医患关系绑定成功", None


def unbind_doctor_patient(admin_id, doctor_id, user_id):
    doctor_id, user_id = to_int(doctor_id), to_int(user_id)
    row = db.query_one(
        """SELECT dp.id, d.doctor_name, u.nickname FROM doctor_patient dp
           JOIN doctor_user d ON d.id=dp.doctor_id JOIN users u ON u.id=dp.user_id
           WHERE dp.doctor_id=%s AND dp.user_id=%s""", (doctor_id, user_id))
    if not row:
        return False, "该医患关系不存在", None
    db.execute("DELETE FROM doctor_patient WHERE doctor_id=%s AND user_id=%s", (doctor_id, user_id))
    write_admin_log(admin_id, "医患解绑",
                    "解除医患关系：医生[%s] <-> 患者[%s]" % (row["doctor_name"], row["nickname"]),
                    "doctor_patient", doctor_id)
    return True, "医患关系已解除", None


def coach_student_list(page=1, page_size=10, coach_id=None, user_keyword=None):
    where, args = [], []
    if coach_id:
        where.append("cs.coach_id=%s")
        args.append(to_int(coach_id))
    if user_keyword:
        where.append("(u.nickname LIKE %s OR u.phone LIKE %s)")
        args.extend(["%" + user_keyword + "%", "%" + user_keyword + "%"])
    cond = (" WHERE " + " AND ".join(where)) if where else ""

    total = db.query_scalar(
        "SELECT COUNT(*) AS c FROM coach_student cs JOIN users u ON u.id=cs.user_id" + cond,
        tuple(args))
    rows = db.query_all(
        """SELECT cs.id, cs.coach_id, cs.user_id, cs.created_at,
                  c.coach_name, c.real_name AS coach_real_name, c.specialty,
                  u.nickname, u.phone, u.gender, u.age, u.avatar
           FROM coach_student cs
           JOIN coach_user c ON c.id = cs.coach_id
           JOIN users u ON u.id = cs.user_id""" + cond +
        " ORDER BY cs.id DESC LIMIT %s OFFSET %s",
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for r in rows:
        r["created_at"] = fmt_datetime(r["created_at"])
    return total, rows


def bind_coach_student(admin_id, coach_id, user_id):
    coach_id, user_id = to_int(coach_id), to_int(user_id)
    if not coach_id or not user_id:
        return False, "请选择教练与学员", None
    coach = db.query_one("SELECT coach_name, audit_status FROM coach_user WHERE id=%s", (coach_id,))
    if not coach:
        return False, "健身教练不存在", None
    if coach["audit_status"] != 1:
        return False, "该教练账号未通过审核，不能建立教练学员关系", None
    user = db.query_one("SELECT nickname FROM users WHERE id=%s", (user_id,))
    if not user:
        return False, "用户不存在", None
    exists = db.query_one(
        "SELECT id FROM coach_student WHERE coach_id=%s AND user_id=%s", (coach_id, user_id))
    if exists:
        return False, "该教练学员关系已存在，请勿重复绑定", None

    db.execute("INSERT INTO coach_student (coach_id, user_id, created_at) VALUES (%s, %s, NOW())",
               (coach_id, user_id))
    write_admin_log(admin_id, "教练学员绑定",
                    "绑定教练学员关系：教练[%s] <-> 学员[%s]" % (coach["coach_name"], user["nickname"]),
                    "coach_student", coach_id)
    return True, "教练学员关系绑定成功", None


def unbind_coach_student(admin_id, coach_id, user_id):
    coach_id, user_id = to_int(coach_id), to_int(user_id)
    row = db.query_one(
        """SELECT cs.id, c.coach_name, u.nickname FROM coach_student cs
           JOIN coach_user c ON c.id=cs.coach_id JOIN users u ON u.id=cs.user_id
           WHERE cs.coach_id=%s AND cs.user_id=%s""", (coach_id, user_id))
    if not row:
        return False, "该教练学员关系不存在", None
    db.execute("DELETE FROM coach_student WHERE coach_id=%s AND user_id=%s", (coach_id, user_id))
    write_admin_log(admin_id, "教练学员解绑",
                    "解除教练学员关系：教练[%s] <-> 学员[%s]" % (row["coach_name"], row["nickname"]),
                    "coach_student", coach_id)
    return True, "教练学员关系已解除", None


# ---------- 通用筛选：从 users 表取非敏感简要信息（供下拉筛选） ----------
def simple_users(keyword=None, limit=200):
    where, args = [], []
    if keyword:
        where.append("(nickname LIKE %s OR phone LIKE %s)")
        args.extend(["%" + keyword + "%", "%" + keyword + "%"])
    cond = (" WHERE " + " AND ".join(where)) if where else ""
    return db.query_all(
        "SELECT id, nickname, phone FROM users" + cond + " ORDER BY id DESC LIMIT %s",
        tuple(args) + (limit,))


def simple_doctors():
    return db.query_all(
        "SELECT id, doctor_name, real_name, specialty FROM doctor_user WHERE audit_status=1 "
        "ORDER BY id ASC")


def simple_coaches():
    return db.query_all(
        "SELECT id, coach_name, real_name, specialty FROM coach_user WHERE audit_status=1 "
        "ORDER BY id ASC")


# =========================== 07 健康数据中心 ===========================
def health_data_statistics():
    today = datetime.date.today()
    week_ago = today - datetime.timedelta(days=6)
    return {
        "health_total": int(db.query_scalar("SELECT COUNT(*) AS c FROM health_record")),
        "sleep_total": int(db.query_scalar("SELECT COUNT(*) AS c FROM sleep_record")),
        "sport_total": int(db.query_scalar("SELECT COUNT(*) AS c FROM sport_record")),
        "today_total": int(
            db.query_scalar("SELECT COUNT(*) AS c FROM health_record WHERE record_date=%s", (today,))
            + db.query_scalar("SELECT COUNT(*) AS c FROM sleep_record WHERE sleep_date=%s", (today,))
            + db.query_scalar("SELECT COUNT(*) AS c FROM sport_record WHERE sport_date=%s", (today,))
        ),
        "week_ago": fmt_date(week_ago),
    }


def health_data_charts():
    today = datetime.date.today()
    week_ago = today - datetime.timedelta(days=6)
    month_ago = today - datetime.timedelta(days=29)

    h_rows = db.query_all(
        "SELECT record_date AS d, COUNT(*) AS c FROM health_record WHERE record_date >= %s "
        "GROUP BY record_date", (week_ago,))
    h_map = {fmt_date(r["d"]): int(r["c"]) for r in h_rows}
    trend = [
        {"date": fmt_date(today - datetime.timedelta(days=i)),
         "value": h_map.get(fmt_date(today - datetime.timedelta(days=i)), 0)}
        for i in range(6, -1, -1)
    ]

    sleep_dist = db.query_all(
        "SELECT sleep_quality AS name, COUNT(*) AS value FROM sleep_record GROUP BY sleep_quality")
    sport_dist = db.query_all(
        "SELECT sport_type AS name, COALESCE(SUM(sport_duration),0) AS value FROM sport_record "
        "GROUP BY sport_type ORDER BY value DESC")
    # 注意：该 SQL 使用参数化查询（%s），DATE_FORMAT 中的 % 必须写成 %% 转义，
    # 否则 pymysql 会把它当作格式符直接抛 ValueError。
    month_rows = db.query_all(
        "SELECT DATE_FORMAT(sport_date,'%%Y-%%m') AS m, COALESCE(SUM(sport_duration),0) AS v "
        "FROM sport_record WHERE sport_date >= %s GROUP BY m ORDER BY m ASC", (month_ago,))

    return {
        "record_trend": trend,
        "sleep_distribution": [{"name": r["name"] or "未填写", "value": int(r["value"])} for r in sleep_dist],
        "sport_distribution": [{"name": r["name"] or "其他", "value": int(r["value"])} for r in sport_dist],
        "month_duration": [{"name": r["m"], "value": int(r["v"])} for r in month_rows],
    }


def health_record_list(page=1, page_size=10, keyword=None, user_id=None,
                       start_date=None, end_date=None):
    where, args = [], []
    if user_id:
        where.append("h.user_id=%s")
        args.append(to_int(user_id))
    if keyword:
        where.append("(u.nickname LIKE %s OR u.phone LIKE %s)")
        args.extend(["%" + keyword + "%", "%" + keyword + "%"])
    if start_date:
        where.append("h.record_date >= %s")
        args.append(start_date)
    if end_date:
        where.append("h.record_date <= %s")
        args.append(end_date)
    cond = (" WHERE " + " AND ".join(where)) if where else ""

    total = db.query_scalar(
        "SELECT COUNT(*) AS c FROM health_record h LEFT JOIN users u ON u.id=h.user_id" + cond,
        tuple(args))
    rows = db.query_all(
        """SELECT h.*, u.nickname, u.phone FROM health_record h
           LEFT JOIN users u ON u.id=h.user_id""" + cond +
        " ORDER BY h.record_date DESC, h.id DESC LIMIT %s OFFSET %s",
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for r in rows:
        r["record_date"] = fmt_date(r["record_date"])
        r["created_at"] = fmt_datetime(r["created_at"])
        r["weight"] = float(r["weight"]) if r["weight"] is not None else None
        r["blood_sugar"] = float(r["blood_sugar"]) if r["blood_sugar"] is not None else None
    return total, rows


def sleep_record_list(page=1, page_size=10, keyword=None, user_id=None,
                      start_date=None, end_date=None):
    where, args = [], []
    if user_id:
        where.append("s.user_id=%s")
        args.append(to_int(user_id))
    if keyword:
        where.append("(u.nickname LIKE %s OR u.phone LIKE %s)")
        args.extend(["%" + keyword + "%", "%" + keyword + "%"])
    if start_date:
        where.append("s.sleep_date >= %s")
        args.append(start_date)
    if end_date:
        where.append("s.sleep_date <= %s")
        args.append(end_date)
    cond = (" WHERE " + " AND ".join(where)) if where else ""

    total = db.query_scalar(
        "SELECT COUNT(*) AS c FROM sleep_record s LEFT JOIN users u ON u.id=s.user_id" + cond,
        tuple(args))
    rows = db.query_all(
        """SELECT s.*, u.nickname, u.phone FROM sleep_record s
           LEFT JOIN users u ON u.id=s.user_id""" + cond +
        " ORDER BY s.sleep_date DESC, s.id DESC LIMIT %s OFFSET %s",
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for r in rows:
        r["sleep_date"] = fmt_date(r["sleep_date"])
        r["sleep_start"] = fmt_datetime(r["sleep_start"])
        r["sleep_end"] = fmt_datetime(r["sleep_end"])
        r["created_at"] = fmt_datetime(r["created_at"])
    return total, rows


def sport_record_list(page=1, page_size=10, keyword=None, user_id=None, sport_type=None,
                      start_date=None, end_date=None):
    where, args = [], []
    if user_id:
        where.append("s.user_id=%s")
        args.append(to_int(user_id))
    if keyword:
        where.append("(u.nickname LIKE %s OR u.phone LIKE %s)")
        args.extend(["%" + keyword + "%", "%" + keyword + "%"])
    if sport_type:
        where.append("s.sport_type=%s")
        args.append(sport_type)
    if start_date:
        where.append("s.sport_date >= %s")
        args.append(start_date)
    if end_date:
        where.append("s.sport_date <= %s")
        args.append(end_date)
    cond = (" WHERE " + " AND ".join(where)) if where else ""

    total = db.query_scalar(
        "SELECT COUNT(*) AS c FROM sport_record s LEFT JOIN users u ON u.id=s.user_id" + cond,
        tuple(args))
    rows = db.query_all(
        """SELECT s.*, u.nickname, u.phone FROM sport_record s
           LEFT JOIN users u ON u.id=s.user_id""" + cond +
        " ORDER BY s.sport_date DESC, s.id DESC LIMIT %s OFFSET %s",
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for r in rows:
        r["sport_date"] = fmt_date(r["sport_date"])
        r["created_at"] = fmt_datetime(r["created_at"])
    return total, rows


# =========================== 08 健康计划管理 ===========================
def health_plan_list(page=1, page_size=10, keyword=None, user_id=None, plan_status=None,
                     start_date=None, end_date=None):
    where, args = [], []
    if user_id:
        where.append("p.user_id=%s")
        args.append(to_int(user_id))
    if keyword:
        where.append("(u.nickname LIKE %s OR u.phone LIKE %s OR p.plan_title LIKE %s)")
        args.extend(["%" + keyword + "%", "%" + keyword + "%", "%" + keyword + "%"])
    if plan_status not in (None, ""):
        where.append("p.plan_status=%s")
        args.append(to_int(plan_status))
    if start_date:
        where.append("p.plan_start >= %s")
        args.append(start_date)
    if end_date:
        where.append("p.plan_start <= %s")
        args.append(end_date)
    cond = (" WHERE " + " AND ".join(where)) if where else ""

    total = db.query_scalar(
        "SELECT COUNT(*) AS c FROM health_plan p LEFT JOIN users u ON u.id=p.user_id" + cond,
        tuple(args))
    rows = db.query_all(
        """SELECT p.*, u.nickname, u.phone FROM health_plan p
           LEFT JOIN users u ON u.id=p.user_id""" + cond +
        " ORDER BY p.id DESC LIMIT %s OFFSET %s",
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for r in rows:
        r["plan_start"] = fmt_date(r["plan_start"])
        r["plan_end"] = fmt_date(r["plan_end"])
        r["created_at"] = fmt_datetime(r["created_at"])
        r["plan_status_text"] = PLAN_STATUS_TEXT.get(r["plan_status"], "未知")
    return total, rows


def health_plan_stats():
    rows = db.query_all("SELECT plan_status AS s, COUNT(*) AS c FROM health_plan GROUP BY plan_status")
    m = {int(r["s"]): int(r["c"]) for r in rows}
    return {
        "total": sum(m.values()),
        "running": m.get(0, 0),
        "finished": m.get(1, 0),
        "abandoned": m.get(2, 0),
    }


# =========================== 09 医生业务监管 ===========================
def doctor_advice_list(page=1, page_size=10, doctor_id=None, user_id=None,
                       keyword=None, start_date=None, end_date=None):
    where, args = [], []
    if doctor_id:
        where.append("a.doctor_id=%s")
        args.append(to_int(doctor_id))
    if user_id:
        where.append("a.user_id=%s")
        args.append(to_int(user_id))
    if keyword:
        where.append("a.advice_content LIKE %s")
        args.append("%" + keyword + "%")
    if start_date:
        where.append("DATE(a.created_at) >= %s")
        args.append(start_date)
    if end_date:
        where.append("DATE(a.created_at) <= %s")
        args.append(end_date)
    cond = (" WHERE " + " AND ".join(where)) if where else ""

    total = db.query_scalar(
        "SELECT COUNT(*) AS c FROM doctor_advice a LEFT JOIN users u ON u.id=a.user_id" + cond,
        tuple(args))
    rows = db.query_all(
        """SELECT a.*, d.doctor_name, d.real_name AS doctor_real_name, d.specialty,
                  u.nickname, u.phone
           FROM doctor_advice a
           LEFT JOIN doctor_user d ON d.id=a.doctor_id
           LEFT JOIN users u ON u.id=a.user_id""" + cond +
        " ORDER BY a.created_at DESC, a.id DESC LIMIT %s OFFSET %s",
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for r in rows:
        r["created_at"] = fmt_datetime(r["created_at"])
    return total, rows


def medical_notice_list(page=1, page_size=10, doctor_id=None, user_id=None,
                        keyword=None, start_date=None, end_date=None):
    where, args = [], []
    if doctor_id:
        where.append("n.doctor_id=%s")
        args.append(to_int(doctor_id))
    if user_id:
        where.append("n.user_id=%s")
        args.append(to_int(user_id))
    if keyword:
        where.append("(n.notice_title LIKE %s OR n.notice_content LIKE %s)")
        args.extend(["%" + keyword + "%", "%" + keyword + "%"])
    if start_date:
        where.append("DATE(n.created_at) >= %s")
        args.append(start_date)
    if end_date:
        where.append("DATE(n.created_at) <= %s")
        args.append(end_date)
    cond = (" WHERE " + " AND ".join(where)) if where else ""

    total = db.query_scalar(
        "SELECT COUNT(*) AS c FROM medical_notice n LEFT JOIN users u ON u.id=n.user_id" + cond,
        tuple(args))
    rows = db.query_all(
        """SELECT n.*, d.doctor_name, d.real_name AS doctor_real_name, u.nickname, u.phone
           FROM medical_notice n
           LEFT JOIN doctor_user d ON d.id=n.doctor_id
           LEFT JOIN users u ON u.id=n.user_id""" + cond +
        " ORDER BY n.created_at DESC, n.id DESC LIMIT %s OFFSET %s",
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for r in rows:
        r["check_date"] = fmt_datetime(r["check_date"])
        r["created_at"] = fmt_datetime(r["created_at"])
    return total, rows


def medical_record_list(page=1, page_size=10, doctor_id=None, user_id=None,
                        keyword=None, start_date=None, end_date=None):
    where, args = [], []
    if doctor_id:
        where.append("m.doctor_id=%s")
        args.append(to_int(doctor_id))
    if user_id:
        where.append("m.user_id=%s")
        args.append(to_int(user_id))
    if keyword:
        where.append("(m.record_title LIKE %s OR m.record_content LIKE %s)")
        args.extend(["%" + keyword + "%", "%" + keyword + "%"])
    if start_date:
        where.append("m.record_date >= %s")
        args.append(start_date)
    if end_date:
        where.append("m.record_date <= %s")
        args.append(end_date)
    cond = (" WHERE " + " AND ".join(where)) if where else ""

    total = db.query_scalar(
        "SELECT COUNT(*) AS c FROM medical_record m LEFT JOIN users u ON u.id=m.user_id" + cond,
        tuple(args))
    rows = db.query_all(
        """SELECT m.*, d.doctor_name, d.real_name AS doctor_real_name, u.nickname, u.phone
           FROM medical_record m
           LEFT JOIN doctor_user d ON d.id=m.doctor_id
           LEFT JOIN users u ON u.id=m.user_id""" + cond +
        " ORDER BY m.record_date DESC, m.id DESC LIMIT %s OFFSET %s",
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for r in rows:
        r["record_date"] = fmt_date(r["record_date"])
        r["created_at"] = fmt_datetime(r["created_at"])
    return total, rows


# =========================== 10 健身业务监管 ===========================
def sport_goal_list(page=1, page_size=10, coach_id=None, user_id=None, goal_status=None,
                    keyword=None, start_date=None, end_date=None):
    where, args = [], []
    if coach_id:
        where.append("g.coach_id=%s")
        args.append(to_int(coach_id))
    if user_id:
        where.append("g.user_id=%s")
        args.append(to_int(user_id))
    if goal_status not in (None, ""):
        where.append("g.goal_status=%s")
        args.append(to_int(goal_status))
    if keyword:
        where.append("(g.goal_title LIKE %s OR g.goal_content LIKE %s)")
        args.extend(["%" + keyword + "%", "%" + keyword + "%"])
    if start_date:
        where.append("g.start_date >= %s")
        args.append(start_date)
    if end_date:
        where.append("g.start_date <= %s")
        args.append(end_date)
    cond = (" WHERE " + " AND ".join(where)) if where else ""

    total = db.query_scalar(
        "SELECT COUNT(*) AS c FROM sport_goal g LEFT JOIN users u ON u.id=g.user_id" + cond,
        tuple(args))
    rows = db.query_all(
        """SELECT g.*, c.coach_name, c.real_name AS coach_real_name, u.nickname, u.phone
           FROM sport_goal g
           LEFT JOIN coach_user c ON c.id=g.coach_id
           LEFT JOIN users u ON u.id=g.user_id""" + cond +
        " ORDER BY g.id DESC LIMIT %s OFFSET %s",
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for r in rows:
        r["start_date"] = fmt_date(r["start_date"])
        r["end_date"] = fmt_date(r["end_date"])
        r["created_at"] = fmt_datetime(r["created_at"])
        r["goal_status_text"] = GOAL_STATUS_TEXT.get(r["goal_status"], "未知")
    return total, rows


def training_plan_list(page=1, page_size=10, coach_id=None, user_id=None, plan_status=None,
                       keyword=None, start_date=None, end_date=None):
    where, args = [], []
    if coach_id:
        where.append("p.coach_id=%s")
        args.append(to_int(coach_id))
    if user_id:
        where.append("p.user_id=%s")
        args.append(to_int(user_id))
    if plan_status not in (None, ""):
        where.append("p.plan_status=%s")
        args.append(to_int(plan_status))
    if keyword:
        where.append("(p.plan_title LIKE %s OR p.plan_content LIKE %s)")
        args.extend(["%" + keyword + "%", "%" + keyword + "%"])
    if start_date:
        where.append("p.start_date >= %s")
        args.append(start_date)
    if end_date:
        where.append("p.start_date <= %s")
        args.append(end_date)
    cond = (" WHERE " + " AND ".join(where)) if where else ""

    total = db.query_scalar(
        "SELECT COUNT(*) AS c FROM training_plan p LEFT JOIN users u ON u.id=p.user_id" + cond,
        tuple(args))
    rows = db.query_all(
        """SELECT p.*, c.coach_name, c.real_name AS coach_real_name, u.nickname, u.phone
           FROM training_plan p
           LEFT JOIN coach_user c ON c.id=p.coach_id
           LEFT JOIN users u ON u.id=p.user_id""" + cond +
        " ORDER BY p.id DESC LIMIT %s OFFSET %s",
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for r in rows:
        r["start_date"] = fmt_date(r["start_date"])
        r["end_date"] = fmt_date(r["end_date"])
        r["created_at"] = fmt_datetime(r["created_at"])
        r["plan_status_text"] = GOAL_STATUS_TEXT.get(r["plan_status"], "未知")
    return total, rows


def fitness_advice_list(page=1, page_size=10, coach_id=None, user_id=None,
                        keyword=None, start_date=None, end_date=None):
    where, args = [], []
    if coach_id:
        where.append("a.coach_id=%s")
        args.append(to_int(coach_id))
    if user_id:
        where.append("a.user_id=%s")
        args.append(to_int(user_id))
    if keyword:
        where.append("a.advice_content LIKE %s")
        args.append("%" + keyword + "%")
    if start_date:
        where.append("DATE(a.created_at) >= %s")
        args.append(start_date)
    if end_date:
        where.append("DATE(a.created_at) <= %s")
        args.append(end_date)
    cond = (" WHERE " + " AND ".join(where)) if where else ""

    total = db.query_scalar(
        "SELECT COUNT(*) AS c FROM fitness_advice a LEFT JOIN users u ON u.id=a.user_id" + cond,
        tuple(args))
    rows = db.query_all(
        """SELECT a.*, c.coach_name, c.real_name AS coach_real_name, u.nickname, u.phone
           FROM fitness_advice a
           LEFT JOIN coach_user c ON c.id=a.coach_id
           LEFT JOIN users u ON u.id=a.user_id""" + cond +
        " ORDER BY a.created_at DESC, a.id DESC LIMIT %s OFFSET %s",
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for r in rows:
        r["created_at"] = fmt_datetime(r["created_at"])
    return total, rows


# =========================== 12 系统管理 ===========================
def operation_log_list(page=1, page_size=10, admin_id=None, operation_type=None,
                       keyword=None, start_date=None, end_date=None):
    where, args = [], []
    if admin_id:
        where.append("l.admin_id=%s")
        args.append(to_int(admin_id))
    if operation_type:
        where.append("l.operation_type=%s")
        args.append(operation_type)
    if keyword:
        where.append("l.operation_content LIKE %s")
        args.append("%" + keyword + "%")
    if start_date:
        where.append("DATE(l.created_at) >= %s")
        args.append(start_date)
    if end_date:
        where.append("DATE(l.created_at) <= %s")
        args.append(end_date)
    cond = (" WHERE " + " AND ".join(where)) if where else ""

    total = db.query_scalar("SELECT COUNT(*) AS c FROM admin_operation_log l" + cond, tuple(args))
    rows = db.query_all(
        """SELECT l.*, a.admin_name, a.real_name AS admin_real_name
           FROM admin_operation_log l
           LEFT JOIN admin_user a ON a.id=l.admin_id""" + cond +
        " ORDER BY l.id DESC LIMIT %s OFFSET %s",
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for r in rows:
        r["created_at"] = fmt_datetime(r["created_at"])
    return total, rows


def operation_types():
    rows = db.query_all("SELECT DISTINCT operation_type FROM admin_operation_log ORDER BY operation_type")
    return [r["operation_type"] for r in rows]


def system_info():
    """系统信息：只展示非敏感信息。"""
    from config import Config
    import flask
    db_version = "未知"
    try:
        row = db.query_one("SELECT VERSION() AS v")
        db_version = row["v"] if row else "未知"
    except Exception:  # noqa: BLE001
        pass
    return {
        "system_name": Config.SYSTEM_NAME,
        "version": Config.SYSTEM_VERSION,
        "backend": "Python 3 + Flask %s" % flask.__version__,
        "frontend": "Vue3 + Vite + Element Plus + ECharts",
        "miniapp": "UniApp + Vue3 + uCharts",
        "database": "MySQL %s" % db_version,
        "port": Config.PORT,
        "api_base_url": Config.API_BASE_URL,
    }
