# -*- coding: utf-8 -*-
"""健身教练业务：注册 / 审核校验 / 工作台 / 学员 / 运动数据 / 目标 / 训练计划 / 建议。

权限铁律：教练读取或写入任何学员数据前，必须同时满足
  ① coach_token 有效（由路由装饰器保证）
  ② coach_student 中存在 (coach_id=当前教练, user_id=目标用户) 关系
"""
import datetime

from utils import db
from utils.auth import coach_student_ids
from utils.helpers import (
    fmt_date,
    fmt_datetime,
    is_valid_phone,
    parse_date,
    to_int,
    to_str,
)
from utils.jwt_utils import gen_coach_token
from utils.response import MSG_AUDIT_PENDING, MSG_AUDIT_REJECTED
from utils.security import check_password_strength, hash_password, verify_password

DEFAULT_AVATAR = "default_coach.jpg"

AUDIT_TEXT = {0: "待审核", 1: "审核通过", 2: "审核拒绝"}
GOAL_STATUS_TEXT = {0: "进行中", 1: "已完成", 2: "已结束"}


# =========================== 注册 / 登录 ===========================
def register(data):
    """
    教练自主申请注册。
    强制 audit_status = 0；客户端提交的 id / role / audit_status / created_at 一律忽略。
    """
    coach_name = to_str(data.get("coach_name"))
    password = to_str(data.get("password"))
    confirm = to_str(data.get("confirm_password"))
    real_name = to_str(data.get("real_name"))
    gender = to_str(data.get("gender"))
    phone = to_str(data.get("phone"))
    specialty = to_str(data.get("specialty"))

    if not coach_name:
        return False, "教练账号不能为空", None
    if len(coach_name) < 3 or len(coach_name) > 50:
        return False, "教练账号长度需在 3~50 位之间", None
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

    exists = db.query_one("SELECT id FROM coach_user WHERE coach_name=%s", (coach_name,))
    if exists:
        return False, "该教练账号已被注册", None
    if phone:
        same_phone = db.query_one("SELECT id FROM coach_user WHERE phone=%s", (phone,))
        if same_phone:
            return False, "该手机号已被其他教练账号使用", None

    new_id = db.insert(
        """INSERT INTO coach_user
           (coach_name, password_hash, real_name, gender, phone, specialty, avatar,
            audit_status, created_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s, 0, NOW())""",
        (coach_name, hash_password(password), real_name, gender, phone, specialty, DEFAULT_AVATAR),
    )
    return True, "注册申请已提交，请等待管理员审核。", {"id": new_id, "audit_status": 0}


def login(coach_name, password):
    coach_name = to_str(coach_name)
    if not coach_name or not password:
        return False, "请输入教练账号和密码", None

    row = db.query_one("SELECT * FROM coach_user WHERE coach_name=%s", (coach_name,))
    if not row or not verify_password(row["password_hash"], password):
        return False, "账号或密码错误", None

    audit_status = row["audit_status"]
    if audit_status == 0:
        return False, MSG_AUDIT_PENDING, None
    if audit_status == 2:
        return False, MSG_AUDIT_REJECTED, None
    if audit_status != 1:
        return False, "账号状态异常，请联系管理员", None

    token = gen_coach_token(row["id"])
    return True, "登录成功", {"token": token, "coach_info": _public_coach(row)}


def _public_coach(row):
    return {
        "id": row["id"],
        "coach_name": row["coach_name"],
        "real_name": row["real_name"],
        "gender": row["gender"],
        "phone": row["phone"],
        "specialty": row["specialty"],
        "avatar": row["avatar"] or DEFAULT_AVATAR,
        "audit_status": row["audit_status"],
        "audit_status_text": AUDIT_TEXT.get(row["audit_status"], "未知"),
        "created_at": fmt_datetime(row["created_at"]),
    }


def get_info(coach_id):
    row = db.query_one("SELECT * FROM coach_user WHERE id=%s", (coach_id,))
    if not row:
        return False, "教练账号不存在", None
    return True, "操作成功", _public_coach(row)


def update_password(coach_id, old_pwd, new_pwd):
    if not old_pwd or not new_pwd:
        return False, "请填写原密码与新密码", None
    ok, msg = check_password_strength(new_pwd)
    if not ok:
        return False, msg, None
    row = db.query_one("SELECT password_hash FROM coach_user WHERE id=%s", (coach_id,))
    if not row or not verify_password(row["password_hash"], old_pwd):
        return False, "原密码不正确", None
    if old_pwd == new_pwd:
        return False, "新密码不能与原密码相同", None
    db.execute("UPDATE coach_user SET password_hash=%s WHERE id=%s",
               (hash_password(new_pwd), coach_id))
    return True, "密码修改成功", None


def update_avatar(coach_id, filename):
    db.execute("UPDATE coach_user SET avatar=%s WHERE id=%s", (filename, coach_id))
    return True, "头像更新成功", {"avatar": filename}


# =========================== 工作台 ===========================
def dashboard(coach_id):
    student_ids = coach_student_ids(coach_id)
    student_count = len(student_ids)
    today = datetime.date.today()
    month_start = today.replace(day=1)

    if student_ids:
        ph = ",".join(["%s"] * len(student_ids))
        # 今日运动人数（去重）
        today_sport_user = db.query_scalar(
            "SELECT COUNT(DISTINCT user_id) AS c FROM sport_record "
            "WHERE user_id IN (%s) AND sport_date=%%s" % ph,
            tuple(student_ids) + (today,),
        )
        # 本月运动总时长（分钟）
        month_duration = db.query_scalar(
            "SELECT COALESCE(SUM(sport_duration),0) AS c FROM sport_record "
            "WHERE user_id IN (%s) AND sport_date >= %%s" % ph,
            tuple(student_ids) + (month_start,),
        )
        running_plan = db.query_scalar(
            "SELECT COUNT(*) AS c FROM training_plan WHERE coach_id=%s AND plan_status=0",
            (coach_id,),
        )
        goal_count = db.query_scalar(
            "SELECT COUNT(*) AS c FROM sport_goal WHERE coach_id=%s", (coach_id,)
        )
        advice_count = db.query_scalar(
            "SELECT COUNT(*) AS c FROM fitness_advice WHERE coach_id=%s", (coach_id,)
        )
        # 最近 7 天运动时长
        daily_rows = db.query_all(
            """SELECT sport_date, COALESCE(SUM(sport_duration),0) AS duration
               FROM sport_record WHERE user_id IN (%s) AND sport_date >= %%s
               GROUP BY sport_date ORDER BY sport_date ASC""" % ph,
            tuple(student_ids) + (today - datetime.timedelta(days=6),),
        )
        # 本月运动类型分布
        type_rows = db.query_all(
            """SELECT sport_type, COALESCE(SUM(sport_duration),0) AS duration
               FROM sport_record WHERE user_id IN (%s) AND sport_date >= %%s
               GROUP BY sport_type ORDER BY duration DESC""" % ph,
            tuple(student_ids) + (month_start,),
        )
        # 学员运动趋势（按学员汇总本月时长）
        student_rows = db.query_all(
            """SELECT u.id AS user_id, u.nickname,
                      COALESCE(SUM(s.sport_duration),0) AS duration,
                      COALESCE(SUM(s.calorie),0) AS calorie
               FROM coach_student cs
               JOIN users u ON u.id = cs.user_id
               LEFT JOIN sport_record s ON s.user_id = u.id AND s.sport_date >= %s
               WHERE cs.coach_id=%s
               GROUP BY u.id, u.nickname ORDER BY duration DESC LIMIT 10""",
            (month_start, coach_id),
        )
    else:
        today_sport_user = month_duration = running_plan = goal_count = advice_count = 0
        daily_rows, type_rows, student_rows = [], [], []

    day_map = {fmt_date(r["sport_date"]): int(r["duration"] or 0) for r in daily_rows}
    duration_trend = []
    for i in range(6, -1, -1):
        d = fmt_date(today - datetime.timedelta(days=i))
        duration_trend.append({"date": d, "value": day_map.get(d, 0)})

    return {
        "stats": {
            "student_count": student_count,
            "today_sport_user": int(today_sport_user),
            "month_duration": int(month_duration),
            "running_plan": int(running_plan),
            "goal_count": int(goal_count),
            "advice_count": int(advice_count),
        },
        "duration_trend": duration_trend,
        "type_distribution": [
            {"name": r["sport_type"] or "其他", "value": int(r["duration"] or 0)}
            for r in type_rows
        ],
        "student_trend": [
            {
                "user_id": r["user_id"],
                "nickname": r["nickname"],
                "duration": int(r["duration"] or 0),
                "calorie": int(r["calorie"] or 0),
            }
            for r in student_rows
        ],
    }


# =========================== 学员管理 ===========================
def student_list(coach_id, page=1, page_size=10, keyword=None):
    where = ["cs.coach_id=%s"]
    args = [coach_id]
    if keyword:
        where.append("(u.nickname LIKE %s OR u.phone LIKE %s)")
        like = "%" + keyword + "%"
        args.extend([like, like])
    cond = " AND ".join(where)

    total = db.query_scalar(
        "SELECT COUNT(*) AS c FROM coach_student cs JOIN users u ON u.id=cs.user_id WHERE " + cond,
        tuple(args),
    )
    rows = db.query_all(
        """SELECT u.id, u.nickname, u.phone, u.gender, u.age, u.height, u.avatar,
                  cs.created_at AS relation_time
           FROM coach_student cs JOIN users u ON u.id=cs.user_id
           WHERE %s ORDER BY cs.id DESC LIMIT %%s OFFSET %%s""" % cond,
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    today = datetime.date.today()
    for r in rows:
        r["height"] = float(r["height"]) if r["height"] is not None else None
        r["relation_time"] = fmt_datetime(r["relation_time"])
        # 今日运动汇总
        agg = db.query_one(
            """SELECT COALESCE(SUM(sport_duration),0) AS duration,
                      COALESCE(SUM(calorie),0) AS calorie
               FROM sport_record WHERE user_id=%s AND sport_date=%s""",
            (r["id"], today),
        )
        r["today_duration"] = int((agg or {}).get("duration") or 0)
        r["today_calorie"] = int((agg or {}).get("calorie") or 0)
    return total, rows


def get_student(coach_id, user_id):
    row = db.query_one(
        """SELECT u.id, u.nickname, u.phone, u.gender, u.age, u.height, u.avatar, u.created_at
           FROM coach_student cs JOIN users u ON u.id=cs.user_id
           WHERE cs.coach_id=%s AND cs.user_id=%s""",
        (coach_id, user_id),
    )
    if not row:
        return None
    row["height"] = float(row["height"]) if row["height"] is not None else None
    row["created_at"] = fmt_datetime(row["created_at"])
    return row


# =========================== 学员运动数据（只读） ===========================
def student_sport_data(coach_id, user_id, page=1, page_size=10,
                       start_date=None, end_date=None, sport_type=None):
    if not db.query_one(
        "SELECT id FROM coach_student WHERE coach_id=%s AND user_id=%s", (coach_id, user_id)
    ):
        return None, None
    from services import health_service
    return health_service.list_sport_record(
        user_id, page=page, page_size=page_size,
        start_date=start_date, end_date=end_date, sport_type=sport_type,
    )


def student_sport_statistics(coach_id, user_id, days=30):
    """学员运动统计（图表用）。"""
    if not db.query_one(
        "SELECT id FROM coach_student WHERE coach_id=%s AND user_id=%s", (coach_id, user_id)
    ):
        return None
    from services import health_service
    return health_service.report_statistics(user_id, days=days)


# =========================== 运动目标 ===========================
def list_sport_goal(coach_id, page=1, page_size=10, user_id=None, goal_status=None, keyword=None):
    where = ["g.coach_id=%s"]
    args = [coach_id]
    if user_id:
        where.append("g.user_id=%s")
        args.append(to_int(user_id))
    if goal_status not in (None, ""):
        where.append("g.goal_status=%s")
        args.append(to_int(goal_status))
    if keyword:
        where.append("g.goal_title LIKE %s")
        args.append("%" + keyword + "%")
    cond = " AND ".join(where)

    total = db.query_scalar("SELECT COUNT(*) AS c FROM sport_goal g WHERE " + cond, tuple(args))
    rows = db.query_all(
        """SELECT g.*, u.nickname, u.phone FROM sport_goal g
           LEFT JOIN users u ON u.id=g.user_id
           WHERE %s ORDER BY g.created_at DESC, g.id DESC LIMIT %%s OFFSET %%s""" % cond,
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for r in rows:
        r["start_date"] = fmt_date(r["start_date"])
        r["end_date"] = fmt_date(r["end_date"])
        r["created_at"] = fmt_datetime(r["created_at"])
        r["goal_status_text"] = GOAL_STATUS_TEXT.get(r["goal_status"], "未知")
    return total, rows


def save_sport_goal(coach_id, data):
    """新增或更新运动目标。含 id 时为更新（只能更新自己的目标）。"""
    goal_id = to_int(data.get("id"))
    user_id = to_int(data.get("user_id"))
    title = to_str(data.get("goal_title"))
    content = to_str(data.get("goal_content"))
    start = parse_date(data.get("start_date"))
    end = parse_date(data.get("end_date"))
    status = to_int(data.get("goal_status"), 0)

    if not user_id:
        return False, "请选择学员", None
    if not title:
        return False, "目标标题不能为空", None
    if len(title) > 100:
        return False, "目标标题不能超过 100 字", None
    if not content:
        return False, "目标内容不能为空", None
    if not start or not end:
        return False, "请选择开始与结束日期", None
    if end < start:
        return False, "结束日期不能早于开始日期", None
    if status not in (0, 1, 2):
        return False, "状态取值不合法", None
    if not db.query_one(
        "SELECT id FROM coach_student WHERE coach_id=%s AND user_id=%s", (coach_id, user_id)
    ):
        return False, "该用户不是您的负责学员，无权操作", None

    if goal_id:
        owned = db.query_one(
            "SELECT id FROM sport_goal WHERE id=%s AND coach_id=%s", (goal_id, coach_id)
        )
        if not owned:
            return False, "目标不存在或无权操作", None
        db.execute(
            """UPDATE sport_goal SET user_id=%s, goal_title=%s, goal_content=%s,
                      start_date=%s, end_date=%s, goal_status=%s WHERE id=%s AND coach_id=%s""",
            (user_id, title, content, start, end, status, goal_id, coach_id),
        )
        return True, "运动目标更新成功", {"id": goal_id}

    new_id = db.insert(
        """INSERT INTO sport_goal
           (coach_id, user_id, goal_title, goal_content, start_date, end_date, goal_status, created_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())""",
        (coach_id, user_id, title, content, start, end, status),
    )
    return True, "运动目标创建成功", {"id": new_id}


def update_goal_status(coach_id, goal_id, status):
    status = to_int(status)
    if status not in (0, 1, 2):
        return False, "状态取值不合法", None
    owned = db.query_one(
        "SELECT id FROM sport_goal WHERE id=%s AND coach_id=%s", (goal_id, coach_id)
    )
    if not owned:
        return False, "目标不存在或无权操作", None
    db.execute("UPDATE sport_goal SET goal_status=%s WHERE id=%s AND coach_id=%s",
               (status, goal_id, coach_id))
    return True, "目标状态更新成功", {"goal_status": status}


# =========================== 训练计划 ===========================
def list_training_plan(coach_id, page=1, page_size=10, user_id=None, plan_status=None, keyword=None):
    where = ["p.coach_id=%s"]
    args = [coach_id]
    if user_id:
        where.append("p.user_id=%s")
        args.append(to_int(user_id))
    if plan_status not in (None, ""):
        where.append("p.plan_status=%s")
        args.append(to_int(plan_status))
    if keyword:
        where.append("p.plan_title LIKE %s")
        args.append("%" + keyword + "%")
    cond = " AND ".join(where)

    total = db.query_scalar("SELECT COUNT(*) AS c FROM training_plan p WHERE " + cond, tuple(args))
    rows = db.query_all(
        """SELECT p.*, u.nickname, u.phone FROM training_plan p
           LEFT JOIN users u ON u.id=p.user_id
           WHERE %s ORDER BY p.created_at DESC, p.id DESC LIMIT %%s OFFSET %%s""" % cond,
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for r in rows:
        r["start_date"] = fmt_date(r["start_date"])
        r["end_date"] = fmt_date(r["end_date"])
        r["created_at"] = fmt_datetime(r["created_at"])
        r["plan_status_text"] = GOAL_STATUS_TEXT.get(r["plan_status"], "未知")
    return total, rows


def save_training_plan(coach_id, data):
    plan_id = to_int(data.get("id"))
    user_id = to_int(data.get("user_id"))
    title = to_str(data.get("plan_title"))
    content = to_str(data.get("plan_content"))
    start = parse_date(data.get("start_date"))
    end = parse_date(data.get("end_date"))
    status = to_int(data.get("plan_status"), 0)

    if not user_id:
        return False, "请选择学员", None
    if not title:
        return False, "计划标题不能为空", None
    if len(title) > 100:
        return False, "计划标题不能超过 100 字", None
    if not content:
        return False, "计划内容不能为空", None
    if not start or not end:
        return False, "请选择开始与结束日期", None
    if end < start:
        return False, "结束日期不能早于开始日期", None
    if status not in (0, 1, 2):
        return False, "状态取值不合法", None
    if not db.query_one(
        "SELECT id FROM coach_student WHERE coach_id=%s AND user_id=%s", (coach_id, user_id)
    ):
        return False, "该用户不是您的负责学员，无权操作", None

    if plan_id:
        owned = db.query_one(
            "SELECT id FROM training_plan WHERE id=%s AND coach_id=%s", (plan_id, coach_id)
        )
        if not owned:
            return False, "训练计划不存在或无权操作", None
        db.execute(
            """UPDATE training_plan SET user_id=%s, plan_title=%s, plan_content=%s,
                      start_date=%s, end_date=%s, plan_status=%s WHERE id=%s AND coach_id=%s""",
            (user_id, title, content, start, end, status, plan_id, coach_id),
        )
        return True, "训练计划更新成功", {"id": plan_id}

    new_id = db.insert(
        """INSERT INTO training_plan
           (coach_id, user_id, plan_title, plan_content, start_date, end_date, plan_status, created_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())""",
        (coach_id, user_id, title, content, start, end, status),
    )
    return True, "训练计划创建成功", {"id": new_id}


def update_plan_status(coach_id, plan_id, status):
    status = to_int(status)
    if status not in (0, 1, 2):
        return False, "状态取值不合法", None
    owned = db.query_one(
        "SELECT id FROM training_plan WHERE id=%s AND coach_id=%s", (plan_id, coach_id)
    )
    if not owned:
        return False, "训练计划不存在或无权操作", None
    db.execute("UPDATE training_plan SET plan_status=%s WHERE id=%s AND coach_id=%s",
               (status, plan_id, coach_id))
    return True, "计划状态更新成功", {"plan_status": status}


# =========================== 健身建议 ===========================
def list_fitness_advice(coach_id, page=1, page_size=10, user_id=None, keyword=None):
    where = ["a.coach_id=%s"]
    args = [coach_id]
    if user_id:
        where.append("a.user_id=%s")
        args.append(to_int(user_id))
    if keyword:
        where.append("a.advice_content LIKE %s")
        args.append("%" + keyword + "%")
    cond = " AND ".join(where)

    total = db.query_scalar("SELECT COUNT(*) AS c FROM fitness_advice a WHERE " + cond, tuple(args))
    rows = db.query_all(
        """SELECT a.*, u.nickname, u.phone FROM fitness_advice a
           LEFT JOIN users u ON u.id=a.user_id
           WHERE %s ORDER BY a.created_at DESC, a.id DESC LIMIT %%s OFFSET %%s""" % cond,
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for r in rows:
        r["created_at"] = fmt_datetime(r["created_at"])
    return total, rows


def save_fitness_advice(coach_id, user_id, content):
    user_id = to_int(user_id)
    content = to_str(content)
    if not user_id:
        return False, "请选择学员", None
    if not content:
        return False, "健身建议内容不能为空", None
    if len(content) > 2000:
        return False, "健身建议内容不能超过 2000 字", None
    if not db.query_one(
        "SELECT id FROM coach_student WHERE coach_id=%s AND user_id=%s", (coach_id, user_id)
    ):
        return False, "该用户不是您的负责学员，无权发送建议", None

    new_id = db.insert(
        """INSERT INTO fitness_advice (coach_id, user_id, advice_content, created_at)
           VALUES (%s, %s, %s, NOW())""",
        (coach_id, user_id, content),
    )
    return True, "健身建议已发送", {"id": new_id}
