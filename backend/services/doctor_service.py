# -*- coding: utf-8 -*-
"""医生业务：注册 / 审核校验 / 工作台 / 患者 / 健康数据 / 建议 / 通知 / 医疗记录。

权限铁律：医生读取或写入任何患者数据前，必须同时满足
  ① doctor_token 有效（由路由装饰器保证）
  ② doctor_patient 中存在 (doctor_id=当前医生, user_id=目标用户) 关系
"""
import datetime

from utils import db
from utils.auth import doctor_patient_ids
from utils.helpers import (
    fmt_date,
    fmt_datetime,
    is_valid_phone,
    parse_date,
    to_int,
    to_str,
)
from utils.jwt_utils import gen_doctor_token
from utils.response import MSG_AUDIT_PENDING, MSG_AUDIT_REJECTED
from utils.security import check_password_strength, hash_password, verify_password

DEFAULT_AVATAR = "default_doctor.jpg"

AUDIT_TEXT = {0: "待审核", 1: "审核通过", 2: "审核拒绝"}


# =========================== 注册 / 登录 ===========================
def register(data):
    """
    医生自主申请注册。
    强制 audit_status = 0；客户端提交的 id / role / audit_status / created_at 一律忽略。
    """
    doctor_name = to_str(data.get("doctor_name"))
    password = to_str(data.get("password"))
    confirm = to_str(data.get("confirm_password"))
    real_name = to_str(data.get("real_name"))
    gender = to_str(data.get("gender"))
    phone = to_str(data.get("phone"))
    specialty = to_str(data.get("specialty"))

    if not doctor_name:
        return False, "医生账号不能为空", None
    if len(doctor_name) < 3 or len(doctor_name) > 50:
        return False, "医生账号长度需在 3~50 位之间", None
    ok, msg = check_password_strength(password)
    if not ok:
        return False, msg, None
    if confirm is not None and confirm != password:
        return False, "两次输入的密码不一致", None
    if not real_name:
        return False, "真实姓名不能为空", None
    if gender and gender not in ("男", "女"):
        return False, "性别取值不合法", None
    if phone and not is_valid_phone(phone):
        return False, "手机号格式不正确", None
    if specialty and len(specialty) > 100:
        return False, "专业方向不能超过 100 字", None

    exists = db.query_one("SELECT id FROM doctor_user WHERE doctor_name=%s", (doctor_name,))
    if exists:
        return False, "该医生账号已被注册", None
    if phone:
        same_phone = db.query_one("SELECT id FROM doctor_user WHERE phone=%s", (phone,))
        if same_phone:
            return False, "该手机号已被其他医生账号使用", None

    # audit_status 强制为 0，不接受客户端传值
    new_id = db.insert(
        """INSERT INTO doctor_user
           (doctor_name, password_hash, real_name, gender, phone, specialty, avatar,
            audit_status, created_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s, 0, NOW())""",
        (doctor_name, hash_password(password), real_name, gender, phone, specialty, DEFAULT_AVATAR),
    )
    return True, "注册申请已提交，请等待管理员审核。", {"id": new_id, "audit_status": 0}


def login(doctor_name, password):
    doctor_name = to_str(doctor_name)
    if not doctor_name or not password:
        return False, "请输入医生账号和密码", None

    row = db.query_one("SELECT * FROM doctor_user WHERE doctor_name=%s", (doctor_name,))
    if not row or not verify_password(row["password_hash"], password):
        return False, "账号或密码错误", None

    audit_status = row["audit_status"]
    if audit_status == 0:
        # 待审核：拒绝生成 Token
        return False, MSG_AUDIT_PENDING, None
    if audit_status == 2:
        return False, MSG_AUDIT_REJECTED, None
    if audit_status != 1:
        return False, "账号状态异常，请联系管理员", None

    token = gen_doctor_token(row["id"])
    return True, "登录成功", {"token": token, "doctor_info": _public_doctor(row)}


def _public_doctor(row):
    return {
        "id": row["id"],
        "doctor_name": row["doctor_name"],
        "real_name": row["real_name"],
        "gender": row["gender"],
        "phone": row["phone"],
        "specialty": row["specialty"],
        "avatar": row["avatar"] or DEFAULT_AVATAR,
        "audit_status": row["audit_status"],
        "audit_status_text": AUDIT_TEXT.get(row["audit_status"], "未知"),
        "created_at": fmt_datetime(row["created_at"]),
    }


def get_info(doctor_id):
    row = db.query_one("SELECT * FROM doctor_user WHERE id=%s", (doctor_id,))
    if not row:
        return False, "医生账号不存在", None
    return True, "操作成功", _public_doctor(row)


def update_password(doctor_id, old_pwd, new_pwd):
    if not old_pwd or not new_pwd:
        return False, "请填写原密码与新密码", None
    ok, msg = check_password_strength(new_pwd)
    if not ok:
        return False, msg, None
    row = db.query_one("SELECT password_hash FROM doctor_user WHERE id=%s", (doctor_id,))
    if not row or not verify_password(row["password_hash"], old_pwd):
        return False, "原密码不正确", None
    if old_pwd == new_pwd:
        return False, "新密码不能与原密码相同", None
    db.execute("UPDATE doctor_user SET password_hash=%s WHERE id=%s",
               (hash_password(new_pwd), doctor_id))
    return True, "密码修改成功", None


def update_avatar(doctor_id, filename):
    db.execute("UPDATE doctor_user SET avatar=%s WHERE id=%s", (filename, doctor_id))
    return True, "头像更新成功", {"avatar": filename}


# =========================== 工作台 ===========================
def dashboard(doctor_id):
    patient_ids = doctor_patient_ids(doctor_id)
    patient_count = len(patient_ids)
    today = datetime.date.today()

    if patient_ids:
        placeholders = ",".join(["%s"] * len(patient_ids))
        today_record_count = db.query_scalar(
            "SELECT COUNT(*) AS c FROM health_record WHERE user_id IN (%s) AND record_date=%%s"
            % placeholders,
            tuple(patient_ids) + (today,),
        )
        advice_count = db.query_scalar(
            "SELECT COUNT(*) AS c FROM doctor_advice WHERE doctor_id=%s", (doctor_id,)
        )
        notice_count = db.query_scalar(
            "SELECT COUNT(*) AS c FROM medical_notice WHERE doctor_id=%s", (doctor_id,)
        )
        record_count = db.query_scalar(
            "SELECT COUNT(*) AS c FROM medical_record WHERE doctor_id=%s", (doctor_id,)
        )
        # 需关注健康指标数量：患者在最近 7 天内存在超出常见参考范围的记录条数
        attention_count = db.query_scalar(
            """SELECT COUNT(*) AS c FROM health_record
               WHERE user_id IN (%s) AND record_date >= %%s
                 AND (blood_pressure_high >= 140 OR blood_pressure_low >= 90
                      OR heart_rate > 100 OR heart_rate < 60
                      OR blood_sugar >= 6.1 OR blood_sugar < 3.9)""" % placeholders,
            tuple(patient_ids) + (today - datetime.timedelta(days=6),),
        )
        # 患者健康数据录入趋势（最近 7 天）
        trend_rows = db.query_all(
            """SELECT record_date, COUNT(*) AS c FROM health_record
               WHERE user_id IN (%s) AND record_date >= %%s
               GROUP BY record_date ORDER BY record_date ASC""" % placeholders,
            tuple(patient_ids) + (today - datetime.timedelta(days=6),),
        )
        # 患者血压趋势（最近 30 天日均值）
        bp_rows = db.query_all(
            """SELECT record_date,
                      ROUND(AVG(blood_pressure_high),0) AS high,
                      ROUND(AVG(blood_pressure_low),0) AS low
               FROM health_record
               WHERE user_id IN (%s) AND record_date >= %%s
               GROUP BY record_date ORDER BY record_date ASC""" % placeholders,
            tuple(patient_ids) + (today - datetime.timedelta(days=29),),
        )
        # 患者健康记录统计（按患者汇总）
        per_patient = db.query_all(
            """SELECT u.id AS user_id, u.nickname, COUNT(h.id) AS record_count
               FROM doctor_patient dp
               JOIN users u ON u.id = dp.user_id
               LEFT JOIN health_record h ON h.user_id = u.id
               WHERE dp.doctor_id=%s
               GROUP BY u.id, u.nickname ORDER BY record_count DESC LIMIT 10""",
            (doctor_id,),
        )
    else:
        today_record_count = advice_count = notice_count = record_count = attention_count = 0
        trend_rows, bp_rows, per_patient = [], [], []

    # 补齐最近 7 天日期（无数据补 0）
    trend_map = {fmt_date(r["record_date"]): int(r["c"]) for r in trend_rows}
    record_trend = []
    for i in range(6, -1, -1):
        d = fmt_date(today - datetime.timedelta(days=i))
        record_trend.append({"date": d, "value": trend_map.get(d, 0)})

    bp_trend = [
        {"date": fmt_date(r["record_date"]), "high": int(r["high"] or 0), "low": int(r["low"] or 0)}
        for r in bp_rows
    ]

    return {
        "stats": {
            "patient_count": patient_count,
            "today_record_count": int(today_record_count),
            "attention_count": int(attention_count),
            "advice_count": int(advice_count),
            "notice_count": int(notice_count),
            "record_count": int(record_count),
        },
        "record_trend": record_trend,
        "bp_trend": bp_trend,
        "patient_record_stats": [
            {"user_id": r["user_id"], "nickname": r["nickname"], "value": int(r["record_count"])}
            for r in per_patient
        ],
    }


# =========================== 患者管理 ===========================
def patient_list(doctor_id, page=1, page_size=10, keyword=None):
    """医生只能查看 doctor_patient 中属于自己的患者。"""
    where = ["dp.doctor_id=%s"]
    args = [doctor_id]
    if keyword:
        where.append("(u.nickname LIKE %s OR u.phone LIKE %s)")
        like = "%" + keyword + "%"
        args.extend([like, like])
    cond = " AND ".join(where)

    total = db.query_scalar(
        "SELECT COUNT(*) AS c FROM doctor_patient dp JOIN users u ON u.id=dp.user_id WHERE " + cond,
        tuple(args),
    )
    rows = db.query_all(
        """SELECT u.id, u.nickname, u.phone, u.gender, u.age, u.height, u.avatar,
                  dp.created_at AS relation_time
           FROM doctor_patient dp JOIN users u ON u.id=dp.user_id
           WHERE %s ORDER BY dp.id DESC LIMIT %%s OFFSET %%s""" % cond,
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for r in rows:
        r["height"] = float(r["height"]) if r["height"] is not None else None
        r["relation_time"] = fmt_datetime(r["relation_time"])
    return total, rows


def get_patient(doctor_id, user_id):
    """获取单个患者基础资料（带关系校验）。"""
    row = db.query_one(
        """SELECT u.id, u.nickname, u.phone, u.gender, u.age, u.height, u.avatar, u.created_at
           FROM doctor_patient dp JOIN users u ON u.id=dp.user_id
           WHERE dp.doctor_id=%s AND dp.user_id=%s""",
        (doctor_id, user_id),
    )
    if not row:
        return None
    row["height"] = float(row["height"]) if row["height"] is not None else None
    row["created_at"] = fmt_datetime(row["created_at"])
    return row


# =========================== 患者健康数据（只读） ===========================
def patient_health_data(doctor_id, user_id, page=1, page_size=10,
                        start_date=None, end_date=None):
    """
    读取患者健康指标数据（只读）。
    未绑定则返回 (None, None) 由路由层判定 401。
    """
    if not db.query_one(
        "SELECT id FROM doctor_patient WHERE doctor_id=%s AND user_id=%s", (doctor_id, user_id)
    ):
        return None, None
    from services import health_service
    return health_service.list_health_record(
        user_id, page=page, page_size=page_size,
        start_date=start_date, end_date=end_date,
    )


def patient_sleep_data(doctor_id, user_id, page=1, page_size=10):
    if not db.query_one(
        "SELECT id FROM doctor_patient WHERE doctor_id=%s AND user_id=%s", (doctor_id, user_id)
    ):
        return None, None
    from services import health_service
    return health_service.list_sleep_record(user_id, page=page, page_size=page_size)


def patient_sport_data(doctor_id, user_id, page=1, page_size=10):
    if not db.query_one(
        "SELECT id FROM doctor_patient WHERE doctor_id=%s AND user_id=%s", (doctor_id, user_id)
    ):
        return None, None
    from services import health_service
    return health_service.list_sport_record(user_id, page=page, page_size=page_size)


def patient_plan_data(doctor_id, user_id, page=1, page_size=10):
    if not db.query_one(
        "SELECT id FROM doctor_patient WHERE doctor_id=%s AND user_id=%s", (doctor_id, user_id)
    ):
        return None, None
    from services import health_service
    return health_service.list_health_plan(user_id, page=page, page_size=page_size)


def patient_health_trend(doctor_id, user_id, days=30):
    """患者健康趋势（体重 / 血压）。"""
    if not db.query_one(
        "SELECT id FROM doctor_patient WHERE doctor_id=%s AND user_id=%s", (doctor_id, user_id)
    ):
        return None
    from services import health_service
    return health_service.report_statistics(user_id, days=days)


# =========================== 健康建议 ===========================
def list_advice(doctor_id, page=1, page_size=10, user_id=None, keyword=None):
    where = ["a.doctor_id=%s"]
    args = [doctor_id]
    if user_id:
        where.append("a.user_id=%s")
        args.append(to_int(user_id))
    if keyword:
        where.append("a.advice_content LIKE %s")
        args.append("%" + keyword + "%")
    cond = " AND ".join(where)

    total = db.query_scalar("SELECT COUNT(*) AS c FROM doctor_advice a WHERE " + cond, tuple(args))
    rows = db.query_all(
        """SELECT a.*, u.nickname, u.phone FROM doctor_advice a
           LEFT JOIN users u ON u.id=a.user_id
           WHERE %s ORDER BY a.created_at DESC, a.id DESC LIMIT %%s OFFSET %%s""" % cond,
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for r in rows:
        r["created_at"] = fmt_datetime(r["created_at"])
    return total, rows


def save_advice(doctor_id, user_id, content):
    user_id = to_int(user_id)
    content = to_str(content)
    if not user_id:
        return False, "请选择患者", None
    if not content:
        return False, "健康建议内容不能为空", None
    if len(content) > 2000:
        return False, "健康建议内容不能超过 2000 字", None
    # 只能给自己的患者发送建议
    if not db.query_one(
        "SELECT id FROM doctor_patient WHERE doctor_id=%s AND user_id=%s", (doctor_id, user_id)
    ):
        return False, "该用户不是您的负责患者，无权发送建议", None

    new_id = db.insert(
        """INSERT INTO doctor_advice (doctor_id, user_id, advice_content, created_at)
           VALUES (%s, %s, %s, NOW())""",
        (doctor_id, user_id, content),
    )
    return True, "健康建议已发送", {"id": new_id}


# =========================== 体检通知 ===========================
def list_medical_notice(doctor_id, page=1, page_size=10, user_id=None, keyword=None):
    where = ["n.doctor_id=%s"]
    args = [doctor_id]
    if user_id:
        where.append("n.user_id=%s")
        args.append(to_int(user_id))
    if keyword:
        where.append("(n.notice_title LIKE %s OR n.notice_content LIKE %s)")
        like = "%" + keyword + "%"
        args.extend([like, like])
    cond = " AND ".join(where)

    total = db.query_scalar("SELECT COUNT(*) AS c FROM medical_notice n WHERE " + cond, tuple(args))
    rows = db.query_all(
        """SELECT n.*, u.nickname, u.phone FROM medical_notice n
           LEFT JOIN users u ON u.id=n.user_id
           WHERE %s ORDER BY n.created_at DESC, n.id DESC LIMIT %%s OFFSET %%s""" % cond,
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for r in rows:
        r["check_date"] = fmt_datetime(r["check_date"])
        r["created_at"] = fmt_datetime(r["created_at"])
    return total, rows


def save_medical_notice(doctor_id, data):
    user_id = to_int(data.get("user_id"))
    title = to_str(data.get("notice_title"))
    content = to_str(data.get("notice_content"))
    check_date = data.get("check_date")
    from utils.helpers import parse_datetime
    check_date = parse_datetime(check_date)

    if not user_id:
        return False, "请选择患者", None
    if not title:
        return False, "通知标题不能为空", None
    if len(title) > 200:
        return False, "通知标题不能超过 200 字", None
    if not content:
        return False, "通知内容不能为空", None
    if not check_date:
        return False, "请选择检查时间", None
    if not db.query_one(
        "SELECT id FROM doctor_patient WHERE doctor_id=%s AND user_id=%s", (doctor_id, user_id)
    ):
        return False, "该用户不是您的负责患者，无权发送通知", None

    new_id = db.insert(
        """INSERT INTO medical_notice
           (doctor_id, user_id, notice_title, notice_content, check_date, created_at)
           VALUES (%s, %s, %s, %s, %s, NOW())""",
        (doctor_id, user_id, title, content, check_date),
    )
    return True, "体检通知已发送", {"id": new_id}


# =========================== 医疗记录 ===========================
def list_medical_record(doctor_id, page=1, page_size=10, user_id=None, keyword=None):
    where = ["m.doctor_id=%s"]
    args = [doctor_id]
    if user_id:
        where.append("m.user_id=%s")
        args.append(to_int(user_id))
    if keyword:
        where.append("(m.record_title LIKE %s OR m.record_content LIKE %s)")
        like = "%" + keyword + "%"
        args.extend([like, like])
    cond = " AND ".join(where)

    total = db.query_scalar("SELECT COUNT(*) AS c FROM medical_record m WHERE " + cond, tuple(args))
    rows = db.query_all(
        """SELECT m.*, u.nickname, u.phone FROM medical_record m
           LEFT JOIN users u ON u.id=m.user_id
           WHERE %s ORDER BY m.record_date DESC, m.id DESC LIMIT %%s OFFSET %%s""" % cond,
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for r in rows:
        r["record_date"] = fmt_datetime(r["record_date"])
        r["created_at"] = fmt_datetime(r["created_at"])
    return total, rows


def save_medical_record(doctor_id, data):
    user_id = to_int(data.get("user_id"))
    title = to_str(data.get("record_title"))
    content = to_str(data.get("record_content"))
    record_date = parse_date(data.get("record_date")) or datetime.date.today()

    if not user_id:
        return False, "请选择患者", None
    if not title:
        return False, "记录标题不能为空", None
    if len(title) > 200:
        return False, "记录标题不能超过 200 字", None
    if not content:
        return False, "记录内容不能为空", None
    if not db.query_one(
        "SELECT id FROM doctor_patient WHERE doctor_id=%s AND user_id=%s", (doctor_id, user_id)
    ):
        return False, "该用户不是您的负责患者，无权创建记录", None

    new_id = db.insert(
        """INSERT INTO medical_record
           (doctor_id, user_id, record_title, record_content, record_date, created_at)
           VALUES (%s, %s, %s, %s, %s, NOW())""",
        (doctor_id, user_id, title, content, record_date),
    )
    return True, "医疗记录已保存", {"id": new_id}
