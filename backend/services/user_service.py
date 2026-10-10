# -*- coding: utf-8 -*-
"""普通用户业务：注册 / 登录 / 资料 / 密码 / 头像 / 医生服务 / 健身服务。

权限要点：所有「我的数据」查询一律以 user_token 解析出的 user_id 为准，
禁止接受客户端传入的 user_id，从根源上防止横向越权。
"""
from utils import db
from utils.helpers import fmt_datetime, is_valid_phone, to_float, to_int, to_str
from utils.jwt_utils import gen_user_token
from utils.security import check_password_strength, hash_password, verify_password

DEFAULT_AVATAR = "default_health.jpg"


# ---------------- 注册 / 登录 ----------------
def register(data):
    phone = to_str(data.get("phone"))
    password = to_str(data.get("password"))
    nickname = to_str(data.get("nickname"))
    gender = to_str(data.get("gender"))
    age = to_int(data.get("age"))
    height = to_float(data.get("height"))

    if not is_valid_phone(phone):
        return False, "请输入正确的手机号", None
    ok, msg = check_password_strength(password)
    if not ok:
        return False, msg, None
    if not nickname:
        return False, "昵称不能为空", None
    if gender and gender not in ("男", "女", "保密"):
        return False, "性别取值不合法", None
    if age is not None and (age < 1 or age > 120):
        return False, "年龄需在 1~120 之间", None
    if height is not None and (height < 50 or height > 250):
        return False, "身高需在 50~250cm 之间", None

    exists = db.query_one("SELECT id FROM users WHERE phone=%s", (phone,))
    if exists:
        return False, "该手机号已注册", None

    uid = db.insert(
        """INSERT INTO users (phone, password_hash, nickname, avatar, gender, age, height, created_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())""",
        (phone, hash_password(password), nickname, DEFAULT_AVATAR, gender, age, height),
    )
    # 普通用户自主注册后可直接登录
    return True, "注册成功", {"id": uid}


def login(phone, password):
    phone = to_str(phone)
    if not phone or not password:
        return False, "请输入手机号和密码", None
    user = db.query_one("SELECT * FROM users WHERE phone=%s", (phone,))
    if not user or not verify_password(user["password_hash"], password):
        return False, "手机号或密码错误", None

    token = gen_user_token(user["id"])
    return True, "登录成功", {
        "token": token,
        "user_info": _public_user(user),
    }


def _public_user(row):
    return {
        "id": row["id"],
        "phone": row["phone"],
        "nickname": row["nickname"],
        "avatar": row["avatar"] or DEFAULT_AVATAR,
        "gender": row["gender"],
        "age": row["age"],
        "height": float(row["height"]) if row["height"] is not None else None,
        "created_at": fmt_datetime(row["created_at"]),
    }


def get_info(user_id):
    row = db.query_one("SELECT * FROM users WHERE id=%s", (user_id,))
    if not row:
        return False, "用户不存在", None
    return True, "操作成功", _public_user(row)


def update_info(user_id, data):
    fields, args = [], []
    nickname = to_str(data.get("nickname"))
    gender = to_str(data.get("gender"))
    age = to_int(data.get("age"))
    height = to_float(data.get("height"))

    if nickname is not None:
        fields.append("nickname=%s")
        args.append(nickname)
    if gender is not None:
        if gender not in ("男", "女", "保密"):
            return False, "性别取值不合法", None
        fields.append("gender=%s")
        args.append(gender)
    if age is not None:
        if age < 1 or age > 120:
            return False, "年龄需在 1~120 之间", None
        fields.append("age=%s")
        args.append(age)
    if height is not None:
        if height < 50 or height > 250:
            return False, "身高需在 50~250cm 之间", None
        fields.append("height=%s")
        args.append(height)

    if not fields:
        return False, "没有需要更新的内容", None

    args.append(user_id)
    db.execute("UPDATE users SET %s WHERE id=%%s" % ", ".join(fields), tuple(args))
    return get_info(user_id)


def update_password(user_id, old_pwd, new_pwd):
    if not old_pwd or not new_pwd:
        return False, "请填写原密码与新密码", None
    ok, msg = check_password_strength(new_pwd)
    if not ok:
        return False, msg, None
    row = db.query_one("SELECT password_hash FROM users WHERE id=%s", (user_id,))
    if not row or not verify_password(row["password_hash"], old_pwd):
        return False, "原密码不正确", None
    if old_pwd == new_pwd:
        return False, "新密码不能与原密码相同", None
    db.execute("UPDATE users SET password_hash=%s WHERE id=%s",
               (hash_password(new_pwd), user_id))
    return True, "密码修改成功", None


def update_avatar(user_id, filename):
    db.execute("UPDATE users SET avatar=%s WHERE id=%s", (filename, user_id))
    return True, "头像更新成功", {"avatar": filename}


# ---------------- 医生服务（只读本人数据） ----------------
def my_doctor_advice(user_id):
    rows = db.query_all(
        """SELECT a.id, a.advice_content, a.created_at,
                  d.real_name AS doctor_name, d.specialty, d.avatar AS doctor_avatar
           FROM doctor_advice a
           LEFT JOIN doctor_user d ON d.id = a.doctor_id
           WHERE a.user_id=%s ORDER BY a.created_at DESC""",
        (user_id,),
    )
    for r in rows:
        r["created_at"] = fmt_datetime(r["created_at"])
    return rows


def my_medical_notice(user_id):
    rows = db.query_all(
        """SELECT n.id, n.notice_title, n.notice_content, n.check_date, n.created_at,
                  d.real_name AS doctor_name, d.specialty
           FROM medical_notice n
           LEFT JOIN doctor_user d ON d.id = n.doctor_id
           WHERE n.user_id=%s ORDER BY n.created_at DESC""",
        (user_id,),
    )
    for r in rows:
        r["check_date"] = fmt_datetime(r["check_date"])
        r["created_at"] = fmt_datetime(r["created_at"])
    return rows


def my_medical_record(user_id):
    rows = db.query_all(
        """SELECT m.id, m.record_title, m.record_content, m.record_date, m.created_at,
                  d.real_name AS doctor_name, d.specialty
           FROM medical_record m
           LEFT JOIN doctor_user d ON d.id = m.doctor_id
           WHERE m.user_id=%s ORDER BY m.record_date DESC, m.id DESC""",
        (user_id,),
    )
    for r in rows:
        r["record_date"] = fmt_datetime(r["record_date"])
        r["created_at"] = fmt_datetime(r["created_at"])
    return rows


# ---------------- 健身服务（只读本人数据） ----------------
def my_sport_goal(user_id):
    rows = db.query_all(
        """SELECT g.id, g.goal_title, g.goal_content, g.start_date, g.end_date,
                  g.goal_status, g.created_at, c.real_name AS coach_name, c.specialty
           FROM sport_goal g
           LEFT JOIN coach_user c ON c.id = g.coach_id
           WHERE g.user_id=%s ORDER BY g.created_at DESC""",
        (user_id,),
    )
    for r in rows:
        r["start_date"] = fmt_datetime(r["start_date"])
        r["end_date"] = fmt_datetime(r["end_date"])
        r["created_at"] = fmt_datetime(r["created_at"])
    return rows


def my_training_plan(user_id):
    rows = db.query_all(
        """SELECT p.id, p.plan_title, p.plan_content, p.start_date, p.end_date,
                  p.plan_status, p.created_at, c.real_name AS coach_name, c.specialty
           FROM training_plan p
           LEFT JOIN coach_user c ON c.id = p.coach_id
           WHERE p.user_id=%s ORDER BY p.created_at DESC""",
        (user_id,),
    )
    for r in rows:
        r["start_date"] = fmt_datetime(r["start_date"])
        r["end_date"] = fmt_datetime(r["end_date"])
        r["created_at"] = fmt_datetime(r["created_at"])
    return rows


def my_fitness_advice(user_id):
    rows = db.query_all(
        """SELECT a.id, a.advice_content, a.created_at,
                  c.real_name AS coach_name, c.specialty
           FROM fitness_advice a
           LEFT JOIN coach_user c ON c.id = a.coach_id
           WHERE a.user_id=%s ORDER BY a.created_at DESC""",
        (user_id,),
    )
    for r in rows:
        r["created_at"] = fmt_datetime(r["created_at"])
    return rows
