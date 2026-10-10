# -*- coding: utf-8 -*-
"""健康数据业务：健康指标 / 睡眠 / 运动 / 健康计划 / 报告统计 / 健康预警。

所有函数第一个参数均为 user_id（由调用方从 Token 或关系校验结果得出）。
"""
import datetime

from utils import db
from utils.helpers import fmt_date, fmt_datetime, parse_date, to_int, to_str

SLEEP_QUALITY_OPTIONS = ("很好", "一般", "较差")


# =========================================================
# 健康指标
# =========================================================
def add_health_record(user_id, data):
    record_date = parse_date(data.get("record_date")) or datetime.date.today()
    weight = data.get("weight")
    high = to_int(data.get("blood_pressure_high"))
    low = to_int(data.get("blood_pressure_low"))
    heart = to_int(data.get("heart_rate"))
    sugar = data.get("blood_sugar")

    if weight in (None, ""):
        return False, "体重不能为空", None
    try:
        weight = round(float(weight), 1)
    except (TypeError, ValueError):
        return False, "体重格式不正确", None
    if weight < 10 or weight > 300:
        return False, "体重需在 10~300kg 之间", None

    for name, val in (("收缩压", high), ("舒张压", low), ("心率", heart)):
        if val is None:
            return False, "%s不能为空" % name, None
    if high < 50 or high > 300:
        return False, "收缩压数值超出合理范围", None
    if low < 30 or low > 200:
        return False, "舒张压数值超出合理范围", None
    if low >= high:
        return False, "舒张压应小于收缩压", None
    if heart < 30 or heart > 220:
        return False, "心率需在 30~220 之间", None

    try:
        sugar = round(float(sugar), 1)
    except (TypeError, ValueError):
        return False, "血糖格式不正确", None
    if sugar < 1 or sugar > 40:
        return False, "血糖数值超出合理范围", None

    rid = db.insert(
        """INSERT INTO health_record
           (user_id, record_date, weight, blood_pressure_high, blood_pressure_low,
            heart_rate, blood_sugar, created_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())""",
        (user_id, record_date, weight, high, low, heart, sugar),
    )
    return True, "健康指标记录成功", {"id": rid}


def list_health_record(user_id, page=1, page_size=10, start_date=None, end_date=None,
                       order="desc"):
    where = ["user_id=%s"]
    args = [user_id]
    if start_date:
        where.append("record_date >= %s")
        args.append(start_date)
    if end_date:
        where.append("record_date <= %s")
        args.append(end_date)
    cond = " AND ".join(where)
    order_sql = "DESC" if order == "desc" else "ASC"

    total = db.query_scalar("SELECT COUNT(*) AS c FROM health_record WHERE " + cond, tuple(args))
    rows = db.query_all(
        "SELECT * FROM health_record WHERE %s ORDER BY record_date %s, id %s LIMIT %%s OFFSET %%s"
        % (cond, order_sql, order_sql),
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for r in rows:
        r["record_date"] = fmt_date(r["record_date"])
        r["weight"] = float(r["weight"]) if r["weight"] is not None else None
        r["blood_sugar"] = float(r["blood_sugar"]) if r["blood_sugar"] is not None else None
        r["created_at"] = fmt_datetime(r["created_at"])
    return total, rows


# =========================================================
# 睡眠
# =========================================================
def add_sleep_record(user_id, data):
    sleep_date = parse_date(data.get("sleep_date")) or datetime.date.today()
    from utils.helpers import parse_datetime
    start = parse_datetime(data.get("sleep_start"))
    end = parse_datetime(data.get("sleep_end"))
    quality = to_str(data.get("sleep_quality"))

    if not start or not end:
        return False, "请填写完整的入睡与起床时间", None
    if end <= start:
        return False, "起床时间必须晚于入睡时间", None
    if quality not in SLEEP_QUALITY_OPTIONS:
        return False, "睡眠质量只能选择：很好 / 一般 / 较差", None

    # 睡眠时长由后端根据 sleep_end - sleep_start 自动计算（分钟）
    duration = int((end - start).total_seconds() // 60)
    if duration <= 0 or duration > 24 * 60:
        return False, "睡眠时长不合理，请检查时间", None

    rid = db.insert(
        """INSERT INTO sleep_record
           (user_id, sleep_date, sleep_start, sleep_end, sleep_duration, sleep_quality, created_at)
           VALUES (%s, %s, %s, %s, %s, %s, NOW())""",
        (user_id, sleep_date, start, end, duration, quality),
    )
    return True, "睡眠记录成功", {"id": rid, "sleep_duration": duration}


def list_sleep_record(user_id, page=1, page_size=10, start_date=None, end_date=None):
    where = ["user_id=%s"]
    args = [user_id]
    if start_date:
        where.append("sleep_date >= %s")
        args.append(start_date)
    if end_date:
        where.append("sleep_date <= %s")
        args.append(end_date)
    cond = " AND ".join(where)

    total = db.query_scalar("SELECT COUNT(*) AS c FROM sleep_record WHERE " + cond, tuple(args))
    rows = db.query_all(
        "SELECT * FROM sleep_record WHERE %s ORDER BY sleep_date DESC, id DESC LIMIT %%s OFFSET %%s" % cond,
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for r in rows:
        r["sleep_date"] = fmt_date(r["sleep_date"])
        r["sleep_start"] = fmt_datetime(r["sleep_start"])
        r["sleep_end"] = fmt_datetime(r["sleep_end"])
        r["created_at"] = fmt_datetime(r["created_at"])
    return total, rows


# =========================================================
# 运动
# =========================================================
SPORT_TYPES = ("跑步", "快走", "骑行", "游泳", "瑜伽", "力量训练", "球类", "其他")


def add_sport_record(user_id, data):
    sport_date = parse_date(data.get("sport_date")) or datetime.date.today()
    sport_type = to_str(data.get("sport_type"))
    duration = to_int(data.get("sport_duration"))
    calorie = to_int(data.get("calorie"))
    remark = to_str(data.get("remark"))

    if not sport_type:
        return False, "请选择运动类型", None
    if duration is None or duration <= 0:
        return False, "运动时长必须大于 0", None
    if duration > 24 * 60:
        return False, "运动时长不合理", None
    if calorie is None or calorie < 0:
        return False, "消耗卡路里不能为空且不能为负数", None
    if remark and len(remark) > 200:
        return False, "备注不能超过 200 字", None

    rid = db.insert(
        """INSERT INTO sport_record
           (user_id, sport_date, sport_type, sport_duration, calorie, remark, created_at)
           VALUES (%s, %s, %s, %s, %s, %s, NOW())""",
        (user_id, sport_date, sport_type, duration, calorie, remark),
    )
    return True, "运动记录成功", {"id": rid}


def list_sport_record(user_id, page=1, page_size=10, start_date=None, end_date=None,
                      sport_type=None, order="desc"):
    where = ["user_id=%s"]
    args = [user_id]
    if start_date:
        where.append("sport_date >= %s")
        args.append(start_date)
    if end_date:
        where.append("sport_date <= %s")
        args.append(end_date)
    if sport_type:
        where.append("sport_type = %s")
        args.append(sport_type)
    cond = " AND ".join(where)
    order_sql = "DESC" if order == "desc" else "ASC"

    total = db.query_scalar("SELECT COUNT(*) AS c FROM sport_record WHERE " + cond, tuple(args))
    rows = db.query_all(
        "SELECT * FROM sport_record WHERE %s ORDER BY sport_date %s, id %s LIMIT %%s OFFSET %%s"
        % (cond, order_sql, order_sql),
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for r in rows:
        r["sport_date"] = fmt_date(r["sport_date"])
        r["created_at"] = fmt_datetime(r["created_at"])
    return total, rows


# =========================================================
# 健康计划
# =========================================================
PLAN_STATUS_TEXT = {0: "进行中", 1: "已完成", 2: "已放弃"}


def add_health_plan(user_id, data):
    title = to_str(data.get("plan_title"))
    content = to_str(data.get("plan_content"))
    start = parse_date(data.get("plan_start"))
    end = parse_date(data.get("plan_end"))

    if not title:
        return False, "计划标题不能为空", None
    if len(title) > 100:
        return False, "计划标题不能超过 100 字", None
    if not content:
        return False, "计划内容不能为空", None
    if not start or not end:
        return False, "请选择计划开始与结束日期", None
    if end < start:
        return False, "结束日期不能早于开始日期", None

    pid = db.insert(
        """INSERT INTO health_plan
           (user_id, plan_title, plan_content, plan_start, plan_end, plan_status, created_at)
           VALUES (%s, %s, %s, %s, %s, 0, NOW())""",
        (user_id, title, content, start, end),
    )
    return True, "健康计划创建成功", {"id": pid}


def list_health_plan(user_id, page=1, page_size=10, plan_status=None):
    where = ["user_id=%s"]
    args = [user_id]
    if plan_status not in (None, ""):
        where.append("plan_status=%s")
        args.append(to_int(plan_status))
    cond = " AND ".join(where)

    total = db.query_scalar("SELECT COUNT(*) AS c FROM health_plan WHERE " + cond, tuple(args))
    rows = db.query_all(
        "SELECT * FROM health_plan WHERE %s ORDER BY id DESC LIMIT %%s OFFSET %%s" % cond,
        tuple(args) + (page_size, (page - 1) * page_size),
    )
    for r in rows:
        r["plan_start"] = fmt_date(r["plan_start"])
        r["plan_end"] = fmt_date(r["plan_end"])
        r["created_at"] = fmt_datetime(r["created_at"])
        r["plan_status_text"] = PLAN_STATUS_TEXT.get(r["plan_status"], "未知")
    return total, rows


def update_plan_status(user_id, plan_id, status):
    status = to_int(status)
    if status not in (0, 1, 2):
        return False, "计划状态参数不合法", None
    # 同时校验归属，防止修改他人计划
    row = db.query_one("SELECT id FROM health_plan WHERE id=%s AND user_id=%s",
                       (plan_id, user_id))
    if not row:
        return False, "计划不存在或无权操作", None
    db.execute("UPDATE health_plan SET plan_status=%s WHERE id=%s AND user_id=%s",
               (status, plan_id, user_id))
    return True, "计划状态更新成功", {"plan_status": status}


# =========================================================
# 报告统计（最近 30 天）
# =========================================================
def report_statistics(user_id, days=30):
    since = (datetime.date.today() - datetime.timedelta(days=days - 1))

    # 体重趋势
    weight_rows = db.query_all(
        """SELECT record_date, weight FROM health_record
           WHERE user_id=%s AND record_date >= %s AND weight IS NOT NULL
           ORDER BY record_date ASC""",
        (user_id, since),
    )
    weight_trend = [
        {"date": fmt_date(r["record_date"]), "weight": float(r["weight"])}
        for r in weight_rows
    ]

    # 血压趋势
    bp_rows = db.query_all(
        """SELECT record_date, blood_pressure_high AS high, blood_pressure_low AS low
           FROM health_record
           WHERE user_id=%s AND record_date >= %s
           ORDER BY record_date ASC""",
        (user_id, since),
    )
    bp_trend = [
        {"date": fmt_date(r["record_date"]), "high": r["high"], "low": r["low"]}
        for r in bp_rows
    ]

    # 月度运动时长（按运动类型汇总）
    sport_type_rows = db.query_all(
        """SELECT sport_type, SUM(sport_duration) AS total_duration, SUM(calorie) AS total_calorie
           FROM sport_record
           WHERE user_id=%s AND sport_date >= %s
           GROUP BY sport_type ORDER BY total_duration DESC""",
        (user_id, since),
    )
    sport_by_type = [
        {
            "name": r["sport_type"] or "其他",
            "value": int(r["total_duration"] or 0),
            "calorie": int(r["total_calorie"] or 0),
        }
        for r in sport_type_rows
    ]

    # 月度运动总时长（按日期）
    sport_day_rows = db.query_all(
        """SELECT sport_date, SUM(sport_duration) AS total_duration
           FROM sport_record WHERE user_id=%s AND sport_date >= %s
           GROUP BY sport_date ORDER BY sport_date ASC""",
        (user_id, since),
    )
    sport_daily = [
        {"date": fmt_date(r["sport_date"]), "duration": int(r["total_duration"] or 0)}
        for r in sport_day_rows
    ]

    # 睡眠质量占比
    sleep_rows = db.query_all(
        """SELECT sleep_quality, COUNT(*) AS c FROM sleep_record
           WHERE user_id=%s AND sleep_date >= %s GROUP BY sleep_quality""",
        (user_id, since),
    )
    sleep_quality = [
        {"name": r["sleep_quality"] or "未填写", "value": int(r["c"])} for r in sleep_rows
    ]

    # 睡眠时长趋势
    sleep_trend_rows = db.query_all(
        """SELECT sleep_date, sleep_duration FROM sleep_record
           WHERE user_id=%s AND sleep_date >= %s ORDER BY sleep_date ASC""",
        (user_id, since),
    )
    sleep_trend = [
        {"date": fmt_date(r["sleep_date"]), "duration": int(r["sleep_duration"] or 0)}
        for r in sleep_trend_rows
    ]

    # 健康计划列表
    _, plans = list_health_plan(user_id, page=1, page_size=50)

    # 汇总
    avg_weight = None
    if weight_trend:
        avg_weight = round(sum(x["weight"] for x in weight_trend) / len(weight_trend), 1)
    total_sport_minutes = sum(x["duration"] for x in sport_daily)
    total_calorie = sum(x["calorie"] for x in sport_by_type)
    avg_sleep = None
    if sleep_trend:
        avg_sleep = int(sum(x["duration"] for x in sleep_trend) / len(sleep_trend))

    return {
        "days": days,
        "summary": {
            "avg_weight": avg_weight,
            "total_sport_minutes": total_sport_minutes,
            "total_calorie": total_calorie,
            "avg_sleep_minutes": avg_sleep,
            "record_count": len(bp_trend),
        },
        "weight_trend": weight_trend,
        "blood_pressure_trend": bp_trend,
        "sport_by_type": sport_by_type,
        "sport_daily": sport_daily,
        "sleep_quality": sleep_quality,
        "sleep_trend": sleep_trend,
        "plan_list": plans,
    }


# =========================================================
# 首页今日概览 + 健康预警
# =========================================================
def today_overview(user_id):
    today = datetime.date.today()
    latest = db.query_one(
        """SELECT record_date, weight, blood_pressure_high, blood_pressure_low, heart_rate, blood_sugar
           FROM health_record WHERE user_id=%s ORDER BY record_date DESC, id DESC LIMIT 1""",
        (user_id,),
    )
    today_record = db.query_one(
        """SELECT weight, blood_pressure_high, blood_pressure_low, heart_rate, blood_sugar
           FROM health_record WHERE user_id=%s AND record_date=%s ORDER BY id DESC LIMIT 1""",
        (user_id, today),
    )
    last_sleep = db.query_one(
        """SELECT sleep_date, sleep_duration, sleep_quality FROM sleep_record
           WHERE user_id=%s ORDER BY sleep_date DESC, id DESC LIMIT 1""",
        (user_id,),
    )
    today_sport = db.query_one(
        """SELECT SUM(sport_duration) AS duration, SUM(calorie) AS calorie
           FROM sport_record WHERE user_id=%s AND sport_date=%s""",
        (user_id, today),
    )
    plan_count = db.query_scalar(
        "SELECT COUNT(*) AS c FROM health_plan WHERE user_id=%s AND plan_status=0", (user_id,)
    )

    def _f(row, key):
        if not row or row.get(key) is None:
            return None
        try:
            return float(row[key])
        except (TypeError, ValueError):
            return row[key]

    return {
        "today_date": fmt_date(today),
        "today": {
            "weight": _f(today_record, "weight"),
            "blood_pressure_high": today_record["blood_pressure_high"] if today_record else None,
            "blood_pressure_low": today_record["blood_pressure_low"] if today_record else None,
            "heart_rate": today_record["heart_rate"] if today_record else None,
            "blood_sugar": _f(today_record, "blood_sugar"),
            "sport_duration": int((today_sport or {}).get("duration") or 0),
            "calorie": int((today_sport or {}).get("calorie") or 0),
        },
        "last": {
            "weight": _f(latest, "weight"),
            "blood_pressure_high": latest["blood_pressure_high"] if latest else None,
            "blood_pressure_low": latest["blood_pressure_low"] if latest else None,
            "heart_rate": latest["heart_rate"] if latest else None,
            "blood_sugar": _f(latest, "blood_sugar"),
            "record_date": fmt_date(latest["record_date"]) if latest else None,
            "sleep_duration": int(last_sleep["sleep_duration"]) if last_sleep and last_sleep["sleep_duration"] else None,
            "sleep_quality": last_sleep["sleep_quality"] if last_sleep else None,
            "sleep_date": fmt_date(last_sleep["sleep_date"]) if last_sleep else None,
        },
        "running_plan_count": int(plan_count),
        "alert": health_alert(latest),
    }


def health_alert(latest):
    """
    健康预警：基于最近一次健康指标做**提醒**，不做疾病诊断。

    绝对禁止：自动诊断疾病、生成处方、推荐药物、给出确诊结论。
    """
    if not latest:
        return {"has_alert": False, "items": [], "tips": []}

    items = []
    high = latest.get("blood_pressure_high")
    low = latest.get("blood_pressure_low")
    heart = latest.get("heart_rate")
    sugar = latest.get("blood_sugar")
    weight = latest.get("weight")

    if high is not None and low is not None:
        if high >= 140 or low >= 90:
            items.append("血压读数偏高")
        elif high < 90 or low < 60:
            items.append("血压读数偏低")
    if heart is not None and (heart > 100 or heart < 60):
        items.append("心率读数有待关注")
    if sugar is not None:
        sugar = float(sugar)
        if sugar >= 6.1 or sugar < 3.9:
            items.append("血糖读数有待关注")
    if weight is not None and float(weight) <= 0:
        items.append("体重数据异常")

    tips = []
    if items:
        tips = [
            "检测到部分健康指标可能超出常见参考范围，请注意关注身体状态；如持续异常，请咨询专业医疗人员。",
            "建议在安静休息状态下多次测量，避免单次读数造成的误判。",
            "保持规律作息、均衡饮食与适度运动有助于维持指标平稳。",
        ]
    return {"has_alert": bool(items), "items": items, "tips": tips}
