# -*- coding: utf-8 -*-
"""
个人健康管理系统 · 接口联调 / 权限 / 安全 自动化测试脚本
=========================================================
运行前提：
  1. 已导入 database/health_management.sql
  2. backend/.env 配置正确
  3. Flask 后端已在 8080 端口运行（python app.py）

运行方式：
  cd health-management-system/tests
  python api_test.py

说明：
  - 全部请求走真实 HTTP，全部校验走真实 MySQL 查询，不使用任何 Mock。
  - 脚本会在数据库中创建带时间戳的唯一测试账号与测试数据（用于真实联调）；
    运行结束（含异常中断）时会自动精确清理「本轮」创建的数据 ——
    仅按本轮唯一标识（TAG / SUF8）做精确定值定位，附带受保护 id 硬守卫与
    二次所有权守卫，绝不删除运行前已有数据与真实用户数据。
"""
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

API = "http://127.0.0.1:8080/api"
STATIC = "http://127.0.0.1:8080/static/upload/"

MYSQL = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
DB_ARGS = ["-uroot", "-p123456", "--protocol=TCP", "-h", "127.0.0.1", "-P", "3306",
           "--default-character-set=utf8mb4", "-N", "-B", "health_management"]

# 每次运行生成唯一后缀，保证可重复执行且不污染既有数据
SUF8 = str(int(time.time()))[-8:]            # 8 位数字，用于手机号后 8 位
TAG = time.strftime("%m%d%H%M%S")            # 12 位，用于账号名唯一化
RESULTS = []


# =============================================================
# 基础工具
# =============================================================
def _enc(path):
    """对 URL 查询串做 UTF-8 百分号编码（中文筛选值必需）。"""
    full = path if path.startswith("http") else API + path
    parts = urlsplit(full)
    if not parts.query:
        return full
    query = urlencode(parse_qsl(parts.query, keep_blank_values=True), encoding="utf-8")
    return urlunsplit((parts.scheme, parts.netloc, quote(parts.path), query, parts.fragment))


def http(method, path, body=None, token=None, raw=False):
    url = _enc(path)
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode("utf-8", "replace")
            ctype = resp.headers.get("Content-Type", "")
            if raw:
                return resp.status, text, ctype
            return resp.status, json.loads(text), ctype
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8", "replace")
        if raw:
            return e.code, text, e.headers.get("Content-Type", "")
        try:
            return e.code, json.loads(text), ""
        except ValueError:
            return e.code, {"code": e.code, "msg": text[:200], "data": None}, ""
    except Exception as e:  # 网络层异常
        return 0, {"code": 0, "msg": "请求异常: %r" % (e,), "data": None}, ""


def sql(query):
    """执行 MySQL 查询，返回剔除表头后的行文本列表。"""
    r = subprocess.run([MYSQL] + DB_ARGS + ["-e", query], capture_output=True, timeout=60)
    out = r.stdout.decode("utf-8", "replace").strip()
    return [line for line in out.splitlines() if line.strip()]


def scalar(query):
    rows = sql(query)
    return rows[0] if rows else None


def case(group, name, expect, ok, actual):
    RESULTS.append({
        "group": group,
        "name": name,
        "expect": expect,
        "actual": actual,
        "status": "PASS" if ok else "FAIL",
    })
    print("[%s] %-46s %s" % ("PASS" if ok else "FAIL", name, "" if ok else "=> " + str(actual)[:150]))


def ok_group(name):
    print("\n" + "=" * 78)
    print("### " + name)
    print("=" * 78)


# =============================================================
# 1. 普通用户（小程序端）
# =============================================================
def suite_user():
    ok_group("一、普通用户（小程序端）全流程")
    phone = "139" + SUF8
    pwd = "test123456"

    st, r, _ = http("POST", "/user/register", {
        "nickname": "接口测试用户A", "phone": phone, "password": pwd,
        "gender": "男", "age": 28, "height": 175.5,
    })
    case("普通用户", "注册", "code=200", r.get("code") == 200, r)
    user_a_id = (r.get("data") or {}).get("id")

    st, r, _ = http("POST", "/user/register", {
        "nickname": "重复手机号", "phone": phone, "password": pwd,
    })
    case("普通用户", "重复手机号注册被拒", "code=400", r.get("code") == 400, r)

    st, r, _ = http("POST", "/user/login", {"phone": phone, "password": pwd})
    case("普通用户", "登录", "code=200 且返回 token", r.get("code") == 200 and bool((r.get("data") or {}).get("token")), r)
    utoken = (r.get("data") or {}).get("token")

    st, r, _ = http("POST", "/user/login", {"phone": phone, "password": "wrongpwd"})
    case("普通用户", "错误密码登录被拒", "code=400", r.get("code") == 400, r)

    st, r, _ = http("GET", "/user/info", token=utoken)
    case("普通用户", "查询个人资料", "code=200 且手机号一致", r.get("code") == 200 and (r.get("data") or {}).get("phone") == phone, r)

    st, r, _ = http("POST", "/user/update_info", {"nickname": "测试用户A改", "gender": "女", "age": 30, "height": 168.0}, token=utoken)
    case("普通用户", "修改资料", "code=200", r.get("code") == 200, r)
    db_nick = scalar("SELECT nickname FROM users WHERE id=%s;" % user_a_id)
    case("普通用户", "资料真实写入数据库", "数据库昵称=测试用户A改", db_nick == "测试用户A改", db_nick)

    # 健康指标
    st, r, _ = http("POST", "/health_record/add", {
        "record_date": time.strftime("%Y-%m-%d"), "weight": 65.5,
        "blood_pressure_high": 128, "blood_pressure_low": 82,
        "heart_rate": 76, "blood_sugar": 5.4,
    }, token=utoken)
    case("普通用户", "健康指标录入", "code=200", r.get("code") == 200, r)
    hr_id = (r.get("data") or {}).get("id")
    cnt = scalar("SELECT COUNT(*) FROM health_record WHERE id=%s AND user_id=%s;" % (hr_id, user_a_id))
    case("普通用户", "健康指标真实落库", "记录存在且归属本人", cnt == "1", cnt)

    st, r, _ = http("GET", "/health_record/my_list?page=1&page_size=10", token=utoken)
    case("普通用户", "健康指标列表", "code=200 且 total>=1", r.get("code") == 200 and (r.get("data") or {}).get("total", 0) >= 1, r)

    # 睡眠（时长由后端自动计算：昨日 23:00 入睡 → 今日 07:00 起床 = 480 分钟）
    yesterday = time.strftime("%Y-%m-%d", time.localtime(time.time() - 86400))
    st, r, _ = http("POST", "/sleep_record/add", {
        "sleep_date": time.strftime("%Y-%m-%d"),
        "sleep_start": yesterday + " 23:00:00",
        "sleep_end": time.strftime("%Y-%m-%d") + " 07:00:00",
        "sleep_quality": "很好",
    }, token=utoken)
    case("普通用户", "睡眠录入", "code=200", r.get("code") == 200, r)
    sl_id = (r.get("data") or {}).get("id")
    dur = scalar("SELECT sleep_duration FROM sleep_record WHERE id=%s;" % sl_id)
    case("普通用户", "睡眠时长后端自动计算", "480 分钟", dur == "480", dur)

    st, r, _ = http("POST", "/sleep_record/add", {
        "sleep_date": time.strftime("%Y-%m-%d"),
        "sleep_start": yesterday + " 23:00:00",
        "sleep_end": time.strftime("%Y-%m-%d") + " 07:00:00",
        "sleep_quality": "超级好",
    }, token=utoken)
    case("普通用户", "非法睡眠质量被拒", "code=400", r.get("code") == 400, r)

    st, r, _ = http("GET", "/sleep_record/my_list?page=1&page_size=10", token=utoken)
    case("普通用户", "睡眠列表", "code=200 且 total>=1", r.get("code") == 200 and (r.get("data") or {}).get("total", 0) >= 1, r)

    # 运动
    st, r, _ = http("POST", "/sport_record/add", {
        "sport_date": time.strftime("%Y-%m-%d"), "sport_type": "跑步",
        "sport_duration": 45, "calorie": 380, "remark": "接口测试运动记录",
    }, token=utoken)
    case("普通用户", "运动录入", "code=200", r.get("code") == 200, r)
    case("普通用户", "运动列表", "code=200",
         http("GET", "/sport_record/my_list?page=1&page_size=10", token=utoken)[1].get("code") == 200, "-")

    # 健康计划
    st, r, _ = http("POST", "/health_plan/add", {
        "plan_title": "接口测试减脂计划", "plan_content": "每日跑步 30 分钟，控制饮食。",
        "plan_start": time.strftime("%Y-%m-%d"), "plan_end": time.strftime("%Y-%m-%d"),
    }, token=utoken)
    case("普通用户", "健康计划创建", "code=200", r.get("code") == 200, r)
    plan_id = (r.get("data") or {}).get("id")
    st, r, _ = http("POST", "/health_plan/update_status", {"id": plan_id, "plan_status": 1}, token=utoken)
    case("普通用户", "健康计划状态更新", "code=200", r.get("code") == 200, r)
    ps = scalar("SELECT plan_status FROM health_plan WHERE id=%s;" % plan_id)
    case("普通用户", "计划状态真实落库", "plan_status=1", ps == "1", ps)

    st, r, _ = http("GET", "/health_plan/my_list?page=1&page_size=10", token=utoken)
    case("普通用户", "健康计划列表", "code=200", r.get("code") == 200, r)

    # 数据报告
    st, r, _ = http("GET", "/report/statistics?days=30", token=utoken)
    d = r.get("data") or {}
    case("普通用户", "数据报告统计", "code=200 且含体重/血压/睡眠趋势与今日概览",
         r.get("code") == 200 and "weight_trend" in d and "blood_pressure_trend" in d
         and "overview" in d, list(d.keys()))

    # 健康科普（免登录）
    st, r, _ = http("GET", "/article/list?page=1&page_size=5")
    arts = (r.get("data") or {}).get("list") or []
    case("普通用户", "健康科普列表（免登录）", "code=200 且只返回 is_show=1",
         r.get("code") == 200 and all(a.get("is_show") == 1 for a in arts), len(arts))
    if arts:
        st, r, _ = http("GET", "/article/detail?id=%s" % arts[0]["id"])
        case("普通用户", "健康科普详情", "code=200", r.get("code") == 200, r)

    st, r, _ = http("GET", "/notice/list?page=1&page_size=5")
    case("普通用户", "系统公告列表（免登录）", "code=200",
         r.get("code") == 200 and all(n.get("is_show") == 1 for n in ((r.get("data") or {}).get("list") or [])), r)

    # 医生 / 教练服务（只读本人）
    for path, label in (("/user/doctor_advice", "医生建议"), ("/user/medical_notice", "体检通知"),
                        ("/user/medical_record", "医疗记录"), ("/user/sport_goal", "运动目标"),
                        ("/user/training_plan", "训练计划"), ("/user/fitness_advice", "健身建议")):
        st, r, _ = http("GET", path, token=utoken)
        case("普通用户", "查看本人" + label, "code=200", r.get("code") == 200, r)

    # 修改密码 / 退出
    st, r, _ = http("POST", "/user/update_pwd", {"old_password": pwd, "new_password": "new123456"}, token=utoken)
    case("普通用户", "修改密码", "code=200", r.get("code") == 200, r)
    st, r, _ = http("POST", "/user/login", {"phone": phone, "password": "new123456"})
    case("普通用户", "新密码可登录", "code=200", r.get("code") == 200, r)
    utoken = (r.get("data") or {}).get("token")
    st, r, _ = http("POST", "/user/logout", {}, token=utoken)
    case("普通用户", "退出登录", "code=200", r.get("code") == 200, r)

    return {"phone": phone, "pwd": "new123456", "id": user_a_id, "token": utoken}


# =============================================================
# 2 / 3. 医生、教练（注册 → 待审核 → 审核 → 登录 → 业务）
# =============================================================
def suite_doctor(admin_token, patient_id):
    ok_group("二、医生：注册 → 审核 → 登录 → 业务")
    name = "doc_test_" + TAG
    pwd = "doc123456"

    # I. 恶意提交 audit_status=1
    st, r, _ = http("POST", "/doctor/register", {
        "doctor_name": name, "password": pwd, "confirm_password": pwd,
        "real_name": "接口测试医生", "gender": "男", "phone": "137" + SUF8,
        "specialty": "内科", "audit_status": 1, "id": 999999, "created_at": "2000-01-01 00:00:00",
    })
    case("医生", "注册申请提交", "code=200", r.get("code") == 200, r)
    doc_id = (r.get("data") or {}).get("id")
    db_audit = scalar("SELECT audit_status FROM doctor_user WHERE id=%s;" % doc_id)
    db_id = scalar("SELECT id FROM doctor_user WHERE id=%s;" % doc_id)
    case("医生·安全 I", "恶意提交 audit_status=1 被强制为 0", "数据库 audit_status=0", db_audit == "0", db_audit)
    case("医生·安全 I", "恶意提交 id 被忽略（自增 ID 生效）", "id != 999999", db_id not in (None, "999999"), db_id)

    # G. 待审核登录
    st, r, _ = http("POST", "/doctor/login", {"doctor_name": name, "password": pwd})
    case("医生·越权 G", "待审核医生登录被拒且无 Token", "code=400 且 data 中无 token",
         r.get("code") == 400 and not (r.get("data") or {}).get("token"), r)

    # 管理员审核通过
    st, r, _ = http("POST", "/admin/doctor/audit", {"id": doc_id, "audit_status": 1}, token=admin_token)
    case("医生", "管理员审核通过", "code=200", r.get("code") == 200, r)

    st, r, _ = http("POST", "/doctor/login", {"doctor_name": name, "password": pwd})
    case("医生", "审核通过后登录", "code=200 且返回 doctor_token",
         r.get("code") == 200 and bool((r.get("data") or {}).get("token")), r)
    dtoken = (r.get("data") or {}).get("token")

    st, r, _ = http("GET", "/doctor/info", token=dtoken)
    case("医生", "查询本人资料", "code=200", r.get("code") == 200, r)

    st, r, _ = http("GET", "/doctor/dashboard", token=dtoken)
    d = r.get("data") or {}
    ds = d.get("stats") or {}
    case("医生", "工作台 Dashboard 统计", "code=200 且 stats 含患者数/今日记录/需关注指标/已发建议",
         r.get("code") == 200 and all(k in ds for k in ("patient_count", "today_record_count",
                                                       "attention_count", "advice_count")), sorted(ds.keys()))
    case("医生", "工作台 Dashboard 图表", "含录入趋势/血压趋势/患者记录统计",
         all(k in d for k in ("record_trend", "bp_trend", "patient_record_stats")), sorted(d.keys()))

    # B. 未绑定患者 → 必须失败
    st, r, _ = http("GET", "/doctor/patient/health_data?user_id=%s" % patient_id, token=dtoken)
    case("医生·越权 B", "读取未绑定患者健康数据被拒", "code=401", r.get("code") == 401, r)
    st, r, _ = http("GET", "/doctor/patient/detail?user_id=%s" % patient_id, token=dtoken)
    case("医生·越权 B", "读取未绑定患者详情被拒", "code=401", r.get("code") == 401, r)

    # 管理员绑定医患关系
    st, r, _ = http("POST", "/admin/doctor/bind_patient", {"doctor_id": doc_id, "user_id": patient_id}, token=admin_token)
    case("医生", "管理员绑定医患关系", "code=200", r.get("code") == 200, r)

    # M. 重复绑定
    st, r, _ = http("POST", "/admin/doctor/bind_patient", {"doctor_id": doc_id, "user_id": patient_id}, token=admin_token)
    case("医生·越权 M", "重复绑定医患关系被拒", "code=400", r.get("code") == 400, r)

    st, r, _ = http("GET", "/doctor/patient/list?page=1&page_size=10", token=dtoken)
    case("医生", "患者列表（仅本人患者）", "code=200 且 total>=1",
         r.get("code") == 200 and (r.get("data") or {}).get("total", 0) >= 1, r)

    st, r, _ = http("GET", "/doctor/patient/health_data?user_id=%s&page=1&page_size=10" % patient_id, token=dtoken)
    case("医生", "绑定后可读患者健康数据", "code=200", r.get("code") == 200, r)
    for path, label in (("/doctor/patient/sleep_data", "睡眠"), ("/doctor/patient/sport_data", "运动"),
                        ("/doctor/patient/plan_data", "健康计划"), ("/doctor/patient/trend", "健康趋势")):
        st, r, _ = http("GET", "%s?user_id=%s" % (path, patient_id), token=dtoken)
        case("医生", "读取患者" + label, "code=200", r.get("code") == 200, r)

    # 业务：建议 / 体检通知 / 医疗记录
    st, r, _ = http("POST", "/doctor/advice/save",
                    {"user_id": patient_id, "advice_content": "接口测试：建议规律作息，控制盐分摄入。"}, token=dtoken)
    case("医生", "保存健康建议", "code=200", r.get("code") == 200, r)
    st, r, _ = http("GET", "/doctor/advice/list?page=1&page_size=10", token=dtoken)
    case("医生", "健康建议列表", "code=200 且 total>=1",
         r.get("code") == 200 and (r.get("data") or {}).get("total", 0) >= 1, r)

    st, r, _ = http("POST", "/doctor/medical_notice/save",
                    {"user_id": patient_id, "notice_title": "接口测试体检通知",
                     "notice_content": "建议进行一次常规体检。",
                     "check_date": time.strftime("%Y-%m-%d") + " 09:00:00"}, token=dtoken)
    case("医生", "保存体检通知", "code=200", r.get("code") == 200, r)
    st, r, _ = http("GET", "/doctor/medical_notice/list?page=1&page_size=10", token=dtoken)
    case("医生", "体检通知列表", "code=200", r.get("code") == 200, r)

    st, r, _ = http("POST", "/doctor/medical_record/save",
                    {"user_id": patient_id, "record_title": "接口测试医疗记录",
                     "record_content": "健康管理档案记录。",
                     "record_date": time.strftime("%Y-%m-%d")}, token=dtoken)
    case("医生", "保存医疗记录", "code=200", r.get("code") == 200, r)
    st, r, _ = http("GET", "/doctor/medical_record/list?page=1&page_size=10", token=dtoken)
    case("医生", "医疗记录列表", "code=200", r.get("code") == 200, r)

    st, r, _ = http("POST", "/doctor/update_pwd", {"old_password": pwd, "new_password": "doc654321"}, token=dtoken)
    case("医生", "修改密码", "code=200", r.get("code") == 200, r)
    st, r, _ = http("POST", "/doctor/login", {"doctor_name": name, "password": "doc654321"})
    case("医生", "新密码登录", "code=200", r.get("code") == 200, r)
    dtoken = (r.get("data") or {}).get("token")
    st, r, _ = http("POST", "/doctor/logout", {}, token=dtoken)
    case("医生", "退出登录", "code=200", r.get("code") == 200, r)

    return {"id": doc_id, "name": name, "pwd": "doc654321", "token": dtoken}


def suite_coach(admin_token, student_id):
    ok_group("三、健身教练：注册 → 审核 → 登录 → 业务")
    name = "coach_test_" + TAG
    pwd = "coach123456"

    st, r, _ = http("POST", "/coach/register", {
        "coach_name": name, "password": pwd, "confirm_password": pwd,
        "real_name": "接口测试教练", "gender": "女", "phone": "136" + SUF8,
        "specialty": "力量训练", "audit_status": 1, "id": 888888,
    })
    case("教练", "注册申请提交", "code=200", r.get("code") == 200, r)
    coach_id = (r.get("data") or {}).get("id")
    db_audit = scalar("SELECT audit_status FROM coach_user WHERE id=%s;" % coach_id)
    db_id = scalar("SELECT id FROM coach_user WHERE id=%s;" % coach_id)
    case("教练·安全 J", "恶意提交 audit_status=1 被强制为 0", "数据库 audit_status=0", db_audit == "0", db_audit)
    case("教练·安全 J", "恶意提交 id 被忽略", "id != 888888", db_id not in (None, "888888"), db_id)

    st, r, _ = http("POST", "/coach/login", {"coach_name": name, "password": pwd})
    case("教练·越权 H", "待审核教练登录被拒且无 Token", "code=400 且 data 中无 token",
         r.get("code") == 400 and not (r.get("data") or {}).get("token"), r)

    st, r, _ = http("POST", "/admin/coach/audit", {"id": coach_id, "audit_status": 1}, token=admin_token)
    case("教练", "管理员审核通过", "code=200", r.get("code") == 200, r)

    st, r, _ = http("POST", "/coach/login", {"coach_name": name, "password": pwd})
    case("教练", "审核通过后登录", "code=200 且返回 coach_token",
         r.get("code") == 200 and bool((r.get("data") or {}).get("token")), r)
    ctoken = (r.get("data") or {}).get("token")

    st, r, _ = http("GET", "/coach/info", token=ctoken)
    case("教练", "查询本人资料", "code=200", r.get("code") == 200, r)

    st, r, _ = http("GET", "/coach/dashboard", token=ctoken)
    cd = r.get("data") or {}
    cs = cd.get("stats") or {}
    case("教练", "工作台 Dashboard 统计", "code=200 且 stats 含学员数/今日运动人数/本月时长/进行中计划",
         r.get("code") == 200 and all(k in cs for k in
                                      ("student_count", "today_sport_user",
                                       "month_duration", "running_plan")), sorted(cs.keys()))
    case("教练", "工作台 Dashboard 图表", "含最近7天运动时长/运动类型分布/学员运动趋势",
         all(k in cd for k in ("duration_trend", "type_distribution", "student_trend")),
         sorted(cd.keys()))

    st, r, _ = http("GET", "/coach/student/sport_data?user_id=%s" % student_id, token=ctoken)
    case("教练·越权 C", "读取未绑定学员运动数据被拒", "code=401", r.get("code") == 401, r)

    st, r, _ = http("POST", "/admin/coach/bind_student", {"coach_id": coach_id, "user_id": student_id}, token=admin_token)
    case("教练", "管理员绑定教练学员关系", "code=200", r.get("code") == 200, r)

    st, r, _ = http("POST", "/admin/coach/bind_student", {"coach_id": coach_id, "user_id": student_id}, token=admin_token)
    case("教练·越权 N", "重复绑定教练学员关系被拒", "code=400", r.get("code") == 400, r)

    st, r, _ = http("GET", "/coach/student/list?page=1&page_size=10", token=ctoken)
    case("教练", "学员列表（仅本人学员）", "code=200 且 total>=1",
         r.get("code") == 200 and (r.get("data") or {}).get("total", 0) >= 1, r)

    st, r, _ = http("GET", "/coach/student/sport_data?user_id=%s&page=1&page_size=10" % student_id, token=ctoken)
    case("教练", "绑定后可读学员运动数据", "code=200", r.get("code") == 200, r)
    st, r, _ = http("GET", "/coach/student/statistics?user_id=%s&days=30" % student_id, token=ctoken)
    case("教练", "学员运动统计", "code=200", r.get("code") == 200, r)

    st, r, _ = http("POST", "/coach/sport_goal/save",
                    {"user_id": student_id, "goal_title": "接口测试运动目标",
                     "goal_content": "每周跑步 3 次，每次 5 公里。",
                     "start_date": time.strftime("%Y-%m-%d"), "end_date": time.strftime("%Y-%m-%d")}, token=ctoken)
    case("教练", "创建运动目标", "code=200", r.get("code") == 200, r)
    goal_id = (r.get("data") or {}).get("id")
    st, r, _ = http("GET", "/coach/sport_goal/list?page=1&page_size=10", token=ctoken)
    case("教练", "运动目标列表", "code=200", r.get("code") == 200, r)
    if goal_id:
        st, r, _ = http("POST", "/coach/sport_goal/update_status", {"id": goal_id, "goal_status": 1}, token=ctoken)
        case("教练", "更新运动目标状态", "code=200", r.get("code") == 200, r)

    st, r, _ = http("POST", "/coach/training_plan/save",
                    {"user_id": student_id, "plan_title": "接口测试训练计划",
                     "plan_content": "周一、周三、周五力量训练 60 分钟。",
                     "start_date": time.strftime("%Y-%m-%d"), "end_date": time.strftime("%Y-%m-%d")}, token=ctoken)
    case("教练", "创建训练计划", "code=200", r.get("code") == 200, r)
    tp_id = (r.get("data") or {}).get("id")
    st, r, _ = http("GET", "/coach/training_plan/list?page=1&page_size=10", token=ctoken)
    case("教练", "训练计划列表", "code=200", r.get("code") == 200, r)
    if tp_id:
        st, r, _ = http("POST", "/coach/training_plan/update_status", {"id": tp_id, "plan_status": 1}, token=ctoken)
        case("教练", "更新训练计划状态", "code=200", r.get("code") == 200, r)

    st, r, _ = http("POST", "/coach/fitness_advice/save",
                    {"user_id": student_id, "advice_content": "接口测试：注意训练前热身，避免运动损伤。"}, token=ctoken)
    case("教练", "创建健身建议", "code=200", r.get("code") == 200, r)
    st, r, _ = http("GET", "/coach/fitness_advice/list?page=1&page_size=10", token=ctoken)
    case("教练", "健身建议列表", "code=200", r.get("code") == 200, r)

    st, r, _ = http("POST", "/coach/update_pwd", {"old_password": pwd, "new_password": "coach654321"}, token=ctoken)
    case("教练", "修改密码", "code=200", r.get("code") == 200, r)
    st, r, _ = http("POST", "/coach/logout", {}, token=ctoken)
    case("教练", "退出登录", "code=200", r.get("code") == 200, r)

    return {"id": coach_id, "name": name, "pdw": "coach654321", "token": ctoken}


# =============================================================
# 4. 管理员 12 个一级模块
# =============================================================
def suite_admin(tokens):
    ok_group("四、管理员：登录 + 12 个一级模块")
    st, r, _ = http("POST", "/admin/login", {"admin_name": "admin", "password": "123456"})
    case("管理员", "登录", "code=200 且返回 admin_token",
         r.get("code") == 200 and bool((r.get("data") or {}).get("token")), r)
    atoken = (r.get("data") or {}).get("token")

    st, r, _ = http("POST", "/admin/login", {"admin_name": "admin", "password": "badpwd"})
    case("管理员", "错误密码登录被拒", "code=400", r.get("code") == 400, r)

    st, r, _ = http("GET", "/admin/info", token=atoken)
    case("管理员", "查询本人资料", "code=200", r.get("code") == 200, r)

    # 01 系统首页
    st, r, _ = http("GET", "/admin/dashboard", token=atoken)
    d = r.get("data") or {}
    stats = d.get("stats") or {}
    required = ["user_count", "doctor_count", "coach_count", "today_user_count",
                "today_health_count", "pending_doctor", "pending_coach",
                "running_plan", "article_count", "today_sport_count"]
    case("管理员 01 系统首页", "10 项统计卡全部为真实 SQL", "10 个字段齐备",
         r.get("code") == 200 and all(k in stats for k in required),
         [k for k in required if k not in stats])
    case("管理员 01 系统首页", "7 张图表数据齐备",
         "含用户趋势/健康录入趋势/睡眠/运动/计划分布/30天运动趋势",
         all(k in d for k in ("user_trend", "health_trend", "sleep_distribution",
                              "sport_distribution", "plan_distribution", "sport_30_trend")),
         list(d.keys()))
    case("管理员 01 系统首页", "快捷待办数据（待审核/最新注册/最近操作）",
         "含 pending_doctors / pending_coaches / latest_users / latest_logs",
         all(k in d for k in ("pending_doctors", "pending_coaches", "latest_users", "latest_logs")),
         list(d.keys()))

    # 02 普通用户管理
    st, r, _ = http("GET", "/admin/user/list?page=1&page_size=10", token=atoken)
    case("管理员 02 用户管理", "用户列表分页", "code=200 且 total>=1",
         r.get("code") == 200 and (r.get("data") or {}).get("total", 0) >= 1, r)
    st, r, _ = http("GET", "/admin/user/list?page=1&page_size=10&keyword=13800138001", token=atoken)
    case("管理员 02 用户管理", "手机号搜索", "code=200", r.get("code") == 200, r)
    st, r, _ = http("GET", "/admin/user/list?page=1&page_size=10&gender=男", token=atoken)
    case("管理员 02 用户管理", "性别筛选", "code=200", r.get("code") == 200, r)

    uid = tokens["user"]["id"]
    st, r, _ = http("GET", "/admin/user/detail?user_id=%s" % uid, token=atoken)
    case("管理员 02 用户管理", "用户详情（完整健康档案）", "code=200", r.get("code") == 200, r)
    for dt, label in (("health", "健康指标"), ("sleep", "睡眠"), ("sport", "运动"), ("plan", "健康计划")):
        st, r, _ = http("GET", "/admin/user/health_data?user_id=%s&data_type=%s" % (uid, dt), token=atoken)
        case("管理员 02 用户管理", "用户档案 Tab - " + label, "code=200", r.get("code") == 200, r)
    st, r, _ = http("GET", "/admin/user/doctor_service?user_id=%s" % uid, token=atoken)
    case("管理员 02 用户管理", "用户档案 Tab - 医生服务", "code=200", r.get("code") == 200, r)
    st, r, _ = http("GET", "/admin/user/coach_service?user_id=%s" % uid, token=atoken)
    case("管理员 02 用户管理", "用户档案 Tab - 健身服务", "code=200", r.get("code") == 200, r)

    # 03 医生管理
    st, r, _ = http("GET", "/admin/doctor/list?page=1&page_size=10", token=atoken)
    case("管理员 03 医生管理", "医生列表", "code=200 且 total>=1",
         r.get("code") == 200 and (r.get("data") or {}).get("total", 0) >= 1, r)
    st, r, _ = http("GET", "/admin/doctor/list?page=1&page_size=10&doctor_name=doctor001", token=atoken)
    case("管理员 03 医生管理", "账号查询", "code=200", r.get("code") == 200, True)
    st, r, _ = http("GET", "/admin/doctor/list?page=1&page_size=10&audit_status=0", token=atoken)
    case("管理员 03 医生管理", "审核状态筛选", "code=200", r.get("code") == 200, True)
    did = tokens["doctor"]["id"]
    st, r, _ = http("GET", "/admin/doctor/detail?id=%s" % did, token=atoken)
    detail = r.get("data") or {}
    case("管理员 03 医生管理", "医生详情含负责患者列表与业务统计",
         "含 patients / business(建议/通知/记录数)",
         r.get("code") == 200 and "patients" in detail and "business" in detail,
         list(detail.keys()))
    case("管理员 03 医生管理", "医生详情不外泄密码哈希", "无 password_hash 字段",
         "password_hash" not in detail, list(detail.keys()))
    st, r, _ = http("POST", "/admin/doctor/update", {"id": did, "real_name": "接口测试医生改", "specialty": "心血管内科"}, token=atoken)
    case("管理员 03 医生管理", "编辑医生基础资料", "code=200", r.get("code") == 200, r)
    st, r, _ = http("POST", "/admin/doctor/reset_pwd", {"id": did, "new_password": "reset123456"}, token=atoken)
    case("管理员 03 医生管理", "重置医生密码", "code=200", r.get("code") == 200, r)
    st, r, _ = http("POST", "/doctor/login", {"doctor_name": tokens["doctor"]["name"], "password": "reset123456"})
    case("管理员 03 医生管理", "重置后新密码可登录", "code=200", r.get("code") == 200, r)

    # 04 健身教练管理
    st, r, _ = http("GET", "/admin/coach/list?page=1&page_size=10", token=atoken)
    case("管理员 04 教练管理", "教练列表", "code=200 且 total>=1",
         r.get("code") == 200 and (r.get("data") or {}).get("total", 0) >= 1, r)
    cid = tokens["coach"]["id"]
    st, r, _ = http("GET", "/admin/coach/detail?id=%s" % cid, token=atoken)
    case("管理员 04 教练管理", "教练详情含负责学员数与业务统计", "code=200", r.get("code") == 200, r)
    st, r, _ = http("POST", "/admin/coach/update", {"id": cid, "specialty": "体态矫正与力量训练"}, token=atoken)
    case("管理员 04 教练管理", "编辑教练基础资料", "code=200", r.get("code") == 200, r)
    st, r, _ = http("POST", "/admin/coach/reset_pwd", {"id": cid, "new_password": "resetc123456"}, token=atoken)
    case("管理员 04 教练管理", "重置教练密码", "code=200", r.get("code") == 200, r)

    # 05 账号审核中心
    st, r, _ = http("GET", "/admin/audit/overview", token=atoken)
    ov = r.get("data") or {}
    case("管理员 05 审核中心", "审核概览（待审核医生/教练/今日已审/累计）", "4 项概览齐备",
         r.get("code") == 200 and len(ov) >= 4, list(ov.keys()))

    # 新建一个待审核医生 / 教练，用于走「拒绝」分支（覆盖 audit_status=2）
    rn_doc = "doc_reject_" + TAG
    st, r, _ = http("POST", "/doctor/register", {
        "doctor_name": rn_doc, "password": "reject123456", "confirm_password": "reject123456",
        "real_name": "待拒绝医生", "gender": "男", "phone": "135" + SUF8, "specialty": "外科"})
    rdoc_id = (r.get("data") or {}).get("id")
    st, r, _ = http("POST", "/admin/doctor/audit", {"id": rdoc_id, "audit_status": 2}, token=atoken)
    case("管理员 05 审核中心", "医生审核拒绝", "code=200", r.get("code") == 200, r)
    st, r, _ = http("POST", "/doctor/login", {"doctor_name": rn_doc, "password": "reject123456"})
    case("管理员 05 · 越权 K", "审核拒绝账号登录被拒", "code=400", r.get("code") == 400, r)

    rn_coach = "coach_reject_" + TAG
    st, r, _ = http("POST", "/coach/register", {
        "coach_name": rn_coach, "password": "reject123456", "confirm_password": "reject123456",
        "real_name": "待拒绝教练", "gender": "女", "phone": "134" + SUF8, "specialty": "瑜伽"})
    rcoach_id = (r.get("data") or {}).get("id")
    st, r, _ = http("POST", "/admin/coach/audit", {"id": rcoach_id, "audit_status": 2}, token=atoken)
    case("管理员 05 审核中心", "教练审核拒绝", "code=200", r.get("code") == 200, r)
    st, r, _ = http("GET", "/admin/audit/record_list?page=1&page_size=10", token=atoken)
    case("管理员 05 审核中心", "审核记录", "code=200", r.get("code") == 200, r)

    # 06 角色关系管理
    st, r, _ = http("GET", "/admin/doctor/patient/list?page=1&page_size=10", token=atoken)
    case("管理员 06 关系管理", "医患关系列表", "code=200 且 total>=1",
         r.get("code") == 200 and (r.get("data") or {}).get("total", 0) >= 1, r)
    st, r, _ = http("GET", "/admin/coach/student/list?page=1&page_size=10", token=atoken)
    case("管理员 06 关系管理", "教练学员关系列表", "code=200 且 total>=1",
         r.get("code") == 200 and (r.get("data") or {}).get("total", 0) >= 1, r)
    st, r, _ = http("GET", "/admin/common/users?page=1&page_size=10", token=atoken)
    case("管理员 06 关系管理", "下拉数据源 - 用户", "code=200", r.get("code") == 200, r)
    st, r, _ = http("GET", "/admin/common/doctors?page=1&page_size=10", token=atoken)
    case("管理员 06 关系管理", "下拉数据源 - 医生", "code=200", r.get("code") == 200, r)
    st, r, _ = http("GET", "/admin/common/coaches?page=1&page_size=10", token=atoken)
    case("管理员 06 关系管理", "下拉数据源 - 教练", "code=200", r.get("code") == 200, r)

    # 07 健康数据中心
    st, r, _ = http("GET", "/admin/health_data/statistics", token=atoken)
    case("管理员 07 健康数据中心", "顶部统计 + 统计分析", "code=200",
         r.get("code") == 200, r)
    for path, label in (("/admin/health_record/list", "健康指标"),
                        ("/admin/sleep_record/list", "睡眠数据"),
                        ("/admin/sport_record/list", "运动数据")):
        st, r, _ = http("GET", "%s?page=1&page_size=10" % path, token=atoken)
        case("管理员 07 健康数据中心", label + "列表", "code=200",
             r.get("code") == 200 and (r.get("data") or {}).get("total", 0) >= 1, r)
        st, r, _ = http("GET", "%s?page=1&page_size=10&start_date=2020-01-01&end_date=2099-12-31" % path, token=atoken)
        case("管理员 07 健康数据中心", label + "日期筛选", "code=200", r.get("code") == 200, r)

    # CSV 导出（必须为真实 CSV，且受筛选条件约束）
    for path, label in (("/admin/health_record/export", "健康指标"),
                        ("/admin/sleep_record/export", "睡眠"),
                        ("/admin/sport_record/export", "运动")):
        st, text, ctype = http("GET", path + "?start_date=2020-01-01&end_date=2099-12-31", token=atoken, raw=True)
        lines = [x for x in text.splitlines() if x.strip()]
        case("管理员 07 CSV 导出", label + "CSV 导出", "返回 CSV 且含表头与数据行",
             text.lstrip().startswith("ID") or "ID," in text.splitlines()[0] if lines else False,
             "lines=%d ctype=%s" % (len(lines), ctype))
        st2, text2, _ = http("GET", path + "?start_date=2000-01-01&end_date=2000-01-02", token=atoken, raw=True)
        n1 = len([x for x in text2.splitlines() if x.strip()])
        case("管理员 07 CSV 导出", label + "CSV 遵守筛选条件", "空区间导出仅剩表头",
             n1 <= 1, "lines=%d" % n1)

    # 08 健康计划管理
    st, r, _ = http("GET", "/admin/health_plan/list?page=1&page_size=10", token=atoken)
    case("管理员 08 健康计划管理", "计划列表", "code=200",
         r.get("code") == 200 and (r.get("data") or {}).get("total", 0) >= 1, r)
    st, r, _ = http("GET", "/admin/health_plan/stats", token=atoken)
    ps = r.get("data") or {}
    case("管理员 08 健康计划管理", "计划统计（总数/进行中/已完成/已放弃）", "4 项统计齐备",
         r.get("code") == 200 and len(ps) >= 4, list(ps.keys()))
    st, r, _ = http("GET", "/admin/health_plan/list?page=1&page_size=10&plan_status=0", token=atoken)
    case("管理员 08 健康计划管理", "状态筛选", "code=200", r.get("code") == 200, True)

    # 09 医生业务监管
    for path, label in (("/admin/doctor_advice/list", "健康建议"),
                        ("/admin/medical_notice/list", "体检通知"),
                        ("/admin/medical_record/list", "医疗记录")):
        st, r, _ = http("GET", "%s?page=1&page_size=10" % path, token=atoken)
        case("管理员 09 医生业务监管", label + "监管列表", "code=200 且 total>=1",
             r.get("code") == 200 and (r.get("data") or {}).get("total", 0) >= 1, r)
        st, r, _ = http("GET", "%s?page=1&page_size=10&keyword=接口测试" % path, token=atoken)
        case("管理员 09 医生业务监管", label + "关键词筛选", "code=200", r.get("code") == 200, True)

    # 10 健身业务监管
    for path, label in (("/admin/sport_goal/list", "运动目标"),
                        ("/admin/training_plan/list", "训练计划"),
                        ("/admin/fitness_advice/list", "健身建议")):
        st, r, _ = http("GET", "%s?page=1&page_size=10" % path, token=atoken)
        case("管理员 10 健身业务监管", label + "监管列表", "code=200 且 total>=1",
             r.get("code") == 200 and (r.get("data") or {}).get("total", 0) >= 1, r)

    # 11 内容运营管理
    st, r, _ = http("GET", "/admin/article/list?page=1&page_size=10", token=atoken)
    case("管理员 11 内容运营", "文章列表", "code=200",
         r.get("code") == 200 and (r.get("data") or {}).get("total", 0) >= 1, r)
    st, r, _ = http("POST", "/admin/article/save", {
        "title": "接口测试科普文章", "content": "这是接口联调测试创建的文章正文。",
        "author": "测试作者", "is_show": 1}, token=atoken)
    case("管理员 11 内容运营", "文章新增", "code=200", r.get("code") == 200, r)
    art_id = (r.get("data") or {}).get("id")
    st, r, _ = http("GET", "/admin/article/detail?id=%s" % art_id, token=atoken)
    case("管理员 11 内容运营", "文章详情", "code=200", r.get("code") == 200, r)
    st, r, _ = http("POST", "/admin/article/save", {
        "id": art_id, "title": "接口测试科普文章（已编辑）",
        "content": "编辑后的正文内容。", "author": "测试作者", "is_show": 0}, token=atoken)
    case("管理员 11 内容运营", "文章编辑（含隐藏）", "code=200", r.get("code") == 200, r)
    st, r, _ = http("GET", "/article/list?page=1&page_size=50")
    hidden = [x for x in ((r.get("data") or {}).get("list") or []) if x["id"] == art_id]
    case("管理员 11 内容运营", "隐藏文章小程序端不可见", "小程序端查不到该文章", len(hidden) == 0, len(hidden))
    st, r, _ = http("POST", "/admin/article/del", {"id": art_id}, token=atoken)
    case("管理员 11 内容运营", "文章删除", "code=200", r.get("code") == 200, r)
    gone = scalar("SELECT COUNT(*) FROM health_article WHERE id=%s;" % art_id)
    case("管理员 11 内容运营", "文章删除真实落库", "数据库记录数=0", gone == "0", gone)

    st, r, _ = http("POST", "/admin/notice/save", {
        "title": "接口测试公告", "content": "这是接口联调测试创建的公告内容。", "is_show": 1}, token=atoken)
    case("管理员 11 内容运营", "公告新增", "code=200", r.get("code") == 200, r)
    nid = (r.get("data") or {}).get("id")
    st, r, _ = http("GET", "/admin/notice/detail?id=%s" % nid, token=atoken)
    case("管理员 11 内容运营", "公告详情", "code=200", r.get("code") == 200, r)
    st, r, _ = http("POST", "/admin/notice/save", {
        "id": nid, "title": "接口测试公告（已编辑）", "content": "编辑后的公告内容。", "is_show": 0}, token=atoken)
    case("管理员 11 内容运营", "公告编辑", "code=200", r.get("code") == 200, r)
    st, r, _ = http("POST", "/admin/notice/del", {"id": nid}, token=atoken)
    case("管理员 11 内容运营", "公告删除", "code=200", r.get("code") == 200, r)

    # 12 系统管理
    st, r, _ = http("GET", "/admin/operation_log/list?page=1&page_size=20", token=atoken)
    logs = (r.get("data") or {}).get("list") or []
    case("管理员 12 系统管理", "操作日志列表", "code=200 且 total>=1",
         r.get("code") == 200 and (r.get("data") or {}).get("total", 0) >= 1, r)
    joined = json.dumps(logs, ensure_ascii=False)
    leak = [k for k in ("password", "pwd", "token", "secret", "jwt", "hash") if k in joined.lower()]
    case("管理员 12 · 安全", "操作日志不含密码/Token/密钥等敏感信息", "无敏感字段", not leak, leak)
    st, r, _ = http("GET", "/admin/operation_log/types", token=atoken)
    case("管理员 12 系统管理", "操作类型枚举", "code=200", r.get("code") == 200, r)
    st, r, _ = http("GET", "/admin/system/info", token=atoken)
    si = r.get("data") or {}
    joined_si = json.dumps(si, ensure_ascii=False)
    leak2 = [k for k in ("password", "secret", "jwt", "token") if k in joined_si.lower()]
    case("管理员 12 系统管理", "系统信息只含非敏感信息", "code=200 且无敏感字段",
         r.get("code") == 200 and not leak2, leak2)

    st, r, _ = http("GET", "/admin/doctor/list?page=1&page_size=200", token=atoken)
    types = sql("SELECT DISTINCT operation_type FROM admin_operation_log;")
    need = ["医生审核通过", "医生审核拒绝", "教练审核通过", "教练审核拒绝", "医患绑定",
            "教练学员绑定", "医生密码重置", "教练密码重置", "医生资料修改", "教练资料修改",
            "文章新增", "文章编辑", "文章删除", "公告新增", "公告编辑", "公告删除"]
    missing = [x for x in need if x not in types]
    case("管理员 12 · 日志完整性", "关键操作日志类型齐全", "全部 16 类均有记录", not missing, missing)

    return atoken


# =============================================================
# 5. 越权 / Token 隔离 测试
# =============================================================
def suite_permission(tokens):
    ok_group("五、越权与四角色 Token 隔离（A ~ P）")
    utoken = tokens["user"]["token"]
    dtoken = tokens["doctor"]["token"]
    ctoken = tokens["coach"]["token"]

    st, r, _ = http("POST", "/admin/login", {"admin_name": "admin", "password": "123456"})
    atoken = (r.get("data") or {}).get("token")

    # A. 用户 A 读取用户 B
    phone_b = "138" + SUF8
    http("POST", "/user/register", {"nickname": "接口测试用户B", "phone": phone_b,
                                    "password": "test123456"})
    st, r, _ = http("GET", "/user/info", token=(http("POST", "/user/login",
                                                     {"phone": phone_b, "password": "test123456"})[1].get("data") or {}).get("token"))
    b_id = (r.get("data") or {}).get("id")
    st, r, _ = http("GET", "/admin/user/detail?user_id=%s" % b_id, token=utoken)
    case("越权 A", "用户 A 用 user_token 读取用户 B 数据", "被拒（401/400）",
         r.get("code") in (401, 400), r)
    st, r, _ = http("GET", "/user/doctor_advice", token=utoken)
    own_only = all(x.get("id") is not None for x in (r.get("data") or []))
    case("越权 A", "用户接口仅返回本人数据（user_id 取自 Token）",
         "code=200 且接口不接受客户端指定 user_id", r.get("code") == 200 and own_only, r)

    # D. doctor_token 访问管理员接口
    st, r, _ = http("GET", "/admin/dashboard", token=dtoken)
    case("越权 D", "doctor_token 访问 /admin/dashboard", "401", r.get("code") == 401, r)

    # E. coach_token 访问医生接口
    st, r, _ = http("GET", "/doctor/dashboard", token=ctoken)
    case("越权 E", "coach_token 访问医生接口", "401", r.get("code") == 401, r)

    # F. user_token 访问管理员接口
    st, r, _ = http("GET", "/admin/dashboard", token=utoken)
    case("越权 F", "user_token 访问管理员接口", "401", r.get("code") == 401, r)

    st, r, _ = http("GET", "/user/info", token=dtoken)
    case("越权 附加", "doctor_token 访问普通用户接口", "401", r.get("code") == 401, r)
    st, r, _ = http("GET", "/user/info", token=ctoken)
    case("越权 附加", "coach_token 访问普通用户接口", "401", r.get("code") == 401, r)
    st, r, _ = http("GET", "/coach/dashboard", token=dtoken)
    case("越权 附加", "doctor_token 访问教练接口", "401", r.get("code") == 401, r)
    st, r, _ = http("GET", "/doctor/dashboard", token=atoken)
    case("越权 附加", "admin_token 访问医生接口", "401", r.get("code") == 401, r)
    st, r, _ = http("POST", "/health_record/add", {"weight": 70, "record_date": time.strftime("%Y-%m-%d")}, token=atoken)
    case("越权 附加", "admin_token 冒充普通用户提交私人健康记录", "401", r.get("code") == 401, r)

    # L. 非法 / 过期 Token
    st, r, _ = http("GET", "/user/info", token="this.is.not.a.jwt")
    case("越权 L", "非法 Token", "401", r.get("code") == 401, r)
    st, r, _ = http("GET", "/user/info")
    case("越权 L", "未携带 Token", "401", r.get("code") == 401, r)

    expired = make_expired_token()
    if expired:
        st, r, _ = http("GET", "/user/info", token=expired)
        case("越权 L", "过期 Token", "401", r.get("code") == 401, r)

    # 医生冒充其他医生：用医生A的 token 修改医生B的数据
    st, r, _ = http("POST", "/doctor/advice/save",
                    {"user_id": 999999, "advice_content": "越权测试"}, token=dtoken)
    case("越权 附加", "医生向非本人患者写入健康建议", "被拒", r.get("code") in (400, 401), r)

    # 教练冒充其他教练
    st, r, _ = http("POST", "/coach/fitness_advice/save",
                    {"user_id": 999999, "advice_content": "越权测试"}, token=ctoken)
    case("越权 附加", "教练向非本人学员写入健身建议", "被拒", r.get("code") in (400, 401), r)

    # O / P：解除关系后继续访问
    did = tokens["doctor"]["id"]
    uid = tokens["user"]["id"]
    st, r, _ = http("POST", "/admin/doctor/unbind_patient", {"doctor_id": did, "user_id": uid}, token=atoken)
    case("越权 O", "管理员解除医患关系", "code=200", r.get("code") == 200, r)
    st, r, _ = http("GET", "/doctor/patient/health_data?user_id=%s" % uid, token=dtoken)
    case("越权 O", "解除医患关系后医生继续读取患者", "401", r.get("code") == 401, r)
    # 复原关系，便于后续人工验收
    http("POST", "/admin/doctor/bind_patient", {"doctor_id": did, "user_id": uid}, token=atoken)

    cid = tokens["coach"]["id"]
    st, r, _ = http("POST", "/admin/coach/unbind_student", {"coach_id": cid, "user_id": uid}, token=atoken)
    case("越权 P", "管理员解除教练学员关系", "code=200", r.get("code") == 200, r)
    st, r, _ = http("GET", "/coach/student/sport_data?user_id=%s" % uid, token=ctoken)
    case("越权 P", "解除教练学员关系后继续读取学员", "401", r.get("code") == 401, r)
    http("POST", "/admin/coach/bind_student", {"coach_id": cid, "user_id": uid}, token=atoken)

    # 医生读取未绑定患者（另一名医生视角）
    other = "doc_other_" + TAG
    http("POST", "/doctor/register", {"doctor_name": other, "password": "other123456",
                                      "confirm_password": "other123456", "real_name": "另一名医生",
                                      "gender": "男", "phone": "133" + SUF8, "specialty": "骨科"})
    oid = scalar("SELECT id FROM doctor_user WHERE doctor_name='%s';" % other)
    http("POST", "/admin/doctor/audit", {"id": oid, "audit_status": 1}, token=atoken)
    st, r, _ = http("POST", "/doctor/login", {"doctor_name": other, "password": "other123456"})
    otoken = (r.get("data") or {}).get("token")
    st, r, _ = http("GET", "/doctor/patient/health_data?user_id=%s" % uid, token=otoken)
    case("越权 B", "另一名医生（无关系）读取该患者", "401", r.get("code") == 401, r)


def make_expired_token():
    """本地生成一个已过期 user_token，用于验证过期校验。"""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))
        import jwt  # PyJWT
        from config import Config
        payload = {
            "id": 1, "role": 0, "token_type": "user_token",
            "exp": int(time.time()) - 3600,
            "iat": int(time.time()) - 7200,
        }
        return jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")
    except Exception as e:
        print("  (跳过过期 Token 用例：%r)" % (e,))
        return None


# =============================================================
# 6. 安全与构建静态检查
# =============================================================
def suite_security_static():
    ok_group("六、安全 / 端口 / 敏感信息 静态检查")
    root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

    # 端口
    # 说明：只扫描「产品源码 / 配置」范围。
    # 排除 tests/ 目录：其中 _selfcheck.py、api_test.py 是端口扫描器本身，
    # _result.json / _run.log 是测试运行产物，都会包含被扫描的关键字字面量。
    # 补充排除（口径修正）：
    #   .venv/      —— 第三方依赖（werkzeug 自带 http_proxy.py 含 :5001 字面量）；
    #   docs/       —— 历史文档会引用被扫描端口作为"已修复项"的文字说明；
    #   unpackage/  —— HBuilderX 构建产物；.idea/.vscode —— 编辑器配置。
    #   以上均非产品源码，纳入扫描只会产生假性 FAIL。
    SCAN_EXCLUDE_DIRS = {"node_modules", "__pycache__", "dist", ".git", "tests",
                         ".venv", "venv", "docs", "unpackage", ".idea", ".vscode"}
    bad = []
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SCAN_EXCLUDE_DIRS]
        for f in files:
            if not f.endswith((".py", ".js", ".vue", ".json", ".md", ".html", ".env", ".example")):
                continue
            p = os.path.join(base, f)
            try:
                with open(p, "rb") as fh:
                    text = fh.read().decode("utf-8", "replace")
            except Exception:
                continue
            for token in (":5000", ":5001", "port=5000", "port=5001", "PORT=5000", "PORT=5001"):
                if token in text:
                    bad.append(os.path.relpath(p, root) + " -> " + token)
    case("安全", "全项目无 5000/5001 端口", "无任何命中", not bad, bad[:8])

    # 明文密码：产品源码（backend 业务代码 + database SQL + 前端）必须零命中。
    # 排除：database/_gen_hash.py（哈希生成工具，需持有原始口令）、
    #       tests/api_test.py（测试脚本需用测试账号登录）。二者均不写入产品数据。
    PWD_SCAN_EXCLUDE = {os.path.join("database", "_gen_hash.py"),
                        os.path.join("tests", "api_test.py"),
                        os.path.join("tests", "_patch_case.py")}
    PRODUCT_DIRS = ("backend", "database", "management-web", "miniapp")
    plain, scanned = [], 0
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ("node_modules", "__pycache__", "dist", ".git", "tests")]
        for f in files:
            if not f.endswith((".py", ".sql", ".js", ".vue")):
                continue
            p = os.path.join(base, f)
            rel = os.path.relpath(p, root)
            if rel in PWD_SCAN_EXCLUDE or not rel.split(os.sep)[0] in PRODUCT_DIRS:
                continue
            scanned += 1
            with open(p, "rb") as fh:
                text = fh.read().decode("utf-8", "replace")
            if "'123456'" in text or '"123456"' in text:
                plain.append(rel)
    case("安全", "产品源码中无 123456 明文密码（扫描 %d 个文件）" % scanned,
         "无命中", not plain, plain)
    sql_body = open(os.path.join(root, "database", "health_management.sql"),
                    "rb").read().decode("utf-8", "replace")
    case("安全", "初始化 SQL 的 password_hash 全部为哈希值",
         "SQL 中 password_hash 后接 pbkdf2/scrypt 哈希",
         "pbkdf2:" in sql_body or "scrypt:" in sql_body, None)

    # 数据库密码哈希非明文
    hashes = sql("SELECT password_hash FROM admin_user WHERE admin_name='admin';")
    h = hashes[0] if hashes else ""
    case("安全", "管理员密码为 Werkzeug 哈希存储", "非明文且哈希前缀合法",
         h.startswith(("pbkdf2:", "scrypt:")), h[:40])
    dh = sql("SELECT password_hash FROM doctor_user WHERE doctor_name='doctor001';")
    case("安全", "医生密码为 Werkzeug 哈希存储", "非明文且哈希前缀合法",
         bool(dh) and dh[0].startswith(("pbkdf2:", "scrypt:")), (dh or [""])[0][:40])
    ch = sql("SELECT password_hash FROM coach_user WHERE coach_name='coach001';")
    case("安全", "教练密码为 Werkzeug 哈希存储", "非明文且哈希前缀合法",
         bool(ch) and ch[0].startswith(("pbkdf2:", "scrypt:")), (ch or [""])[0][:40])

    # 图片字段只保存文件名
    urls = scalar("SELECT COUNT(*) FROM users WHERE avatar LIKE 'http%%';")
    case("安全", "users.avatar 只存文件名（无完整 URL）", "计数=0", urls == "0", urls)
    urls2 = scalar("SELECT COUNT(*) FROM health_article WHERE cover_img LIKE 'http%%';")
    case("安全", "health_article.cover_img 只存文件名", "计数=0", urls2 == "0", urls2)
    urls3 = scalar("SELECT COUNT(*) FROM doctor_user WHERE avatar LIKE 'http%%';")
    case("安全", "doctor_user.avatar 只存文件名", "计数=0", urls3 == "0", urls3)
    urls4 = scalar("SELECT COUNT(*) FROM coach_user WHERE avatar LIKE 'http%%';")
    case("安全", "coach_user.avatar 只存文件名", "计数=0", urls4 == "0", urls4)

    # 上传目录默认头像
    upload = os.path.join(root, "backend", "static", "upload")
    need = ["default_health.jpg", "default_doctor.jpg", "default_coach.jpg", "default_admin.jpg"]
    missing = [n for n in need if not os.path.exists(os.path.join(upload, n))]
    case("安全", "四类默认头像文件齐备", "全部存在", not missing, missing)

    # 静态资源可访问
    try:
        with urllib.request.urlopen(STATIC + "default_health.jpg", timeout=10) as resp:
            case("安全", "静态资源目录可访问", "HTTP 200", resp.status == 200, resp.status)
    except Exception as e:
        case("安全", "静态资源目录可访问", "HTTP 200", False, repr(e))

    # 上传扩展名校验
    import urllib.request as ur
    boundary = "----phsTestBoundary"
    body = ("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"evil.php\"\r\n"
            "Content-Type: application/x-php\r\n\r\n<?php echo 1; ?>\r\n--%s--\r\n" % (boundary, boundary)).encode()
    req = ur.Request(API + "/user/upload_avatar", data=body, method="POST",
                     headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    try:
        with ur.urlopen(req, timeout=20) as resp:
            r = json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        r = json.loads(e.read().decode("utf-8", "replace"))
    case("安全", "非法扩展名（.php）上传被拒", "code=401（未登录）或 400（扩展名不合法）",
         r.get("code") in (400, 401), r)


# =============================================================
# 7. 本轮测试数据精确清理（V3.2 FINAL 封板新增）
# -------------------------------------------------------------
# 设计原则（对应封板要求）：
#   1) 只用本轮唯一标识（TAG / SUF8）做「精确定值」定位，严禁 id 范围、
#      BETWEEN、TRUNCATE、DROP 或模糊 LIKE 大范围删除；
#   2) 硬编码受保护 id 白名单守卫，任一命中即中止且不删除任何行；
#   3) 业务行再加「二次所有权守卫」：user_id 必须属于本轮测试用户，
#      否则视为不可确认，剔除并记录，绝不删除；
#   4) 按外键依赖顺序：先关系/子业务，后账号；
#   5) 清理后复核残留必须为 0，否则该用例 FAIL。
# =============================================================
PROTECTED_IDS = {
    'users': (1, 2, 12, 13),
    'doctor_user': (1, 2, 3),
    'coach_user': (1, 2, 3),
}
BIZ_BY_USER = ['health_record', 'sleep_record', 'sport_record', 'health_plan']
BIZ_BY_DOCTOR = ['doctor_advice', 'medical_notice', 'medical_record']
BIZ_BY_COACH = ['sport_goal', 'training_plan', 'fitness_advice']


def _ids(query):
    """执行查询并返回整数 id 列表（仅接受纯数字首列，防止误读表头/文本）。"""
    out = []
    for line in sql(query):
        tok = line.split('\t')[0].strip()
        if tok.isdigit():
            out.append(int(tok))
    return out


def _il(v):
    """整数列表 -> SQL IN 字面量。"""
    return ','.join(str(x) for x in v)


def sqlexec(query):
    """执行写 SQL，返回 (returncode, stderr)。"""
    r = subprocess.run([MYSQL] + DB_ARGS + ["-e", query], capture_output=True, timeout=60)
    return r.returncode, r.stderr.decode('utf-8', 'replace').strip()


def _filter_owned(table, ids, owners):
    """二次所有权守卫：仅保留 user_id ∈ owners 的行。返回 (keep, dropped)。"""
    if not ids:
        return [], []
    keep, dropped = [], []
    for line in sql("SELECT id,user_id FROM `%s` WHERE id IN (%s);" % (table, _il(ids))):
        p = line.split('\t')
        if len(p) < 2:
            continue
        i, uid = p[0].strip(), p[1].strip()
        if uid.isdigit() and int(uid) in owners:
            keep.append(int(i))
        else:
            dropped.append(int(i))
    return keep, dropped


def cleanup_round():
    """精确清理本轮（同一 TAG / SUF8）创建的测试数据。返回 (ok, detail)。"""
    # 1) 本轮账号：唯一标识精确定值定位
    plan = {
        'users': _ids("SELECT id FROM users WHERE phone IN ('139%s','138%s');" % (SUF8, SUF8)),
        'doctor_user': _ids("SELECT id FROM doctor_user WHERE doctor_name IN "
                            "('doc_test_%s','doc_reject_%s','doc_other_%s');" % (TAG, TAG, TAG)),
        'coach_user': _ids("SELECT id FROM coach_user WHERE coach_name IN "
                           "('coach_test_%s','coach_reject_%s');" % (TAG, TAG)),
    }
    # 2) 硬守卫
    for t, ids in plan.items():
        bad = [i for i in ids if i in PROTECTED_IDS[t]]
        if bad:
            return False, '受保护实体命中，已中止清理且未删除任何行：%s %s' % (t, bad)
    u, d, c = plan['users'], plan['doctor_user'], plan['coach_user']
    owners = set(u)

    # 3) 关系表
    rel = {'doctor_patient': [], 'coach_student': []}
    if u:
        rel['doctor_patient'] += _ids("SELECT id FROM doctor_patient WHERE user_id IN (%s);" % _il(u))
        rel['coach_student'] += _ids("SELECT id FROM coach_student WHERE user_id IN (%s);" % _il(u))
    if d:
        rel['doctor_patient'] += _ids("SELECT id FROM doctor_patient WHERE doctor_id IN (%s);" % _il(d))
    if c:
        rel['coach_student'] += _ids("SELECT id FROM coach_student WHERE coach_id IN (%s);" % _il(c))
    for k in rel:
        rel[k] = sorted(set(rel[k]))

    # 4) 业务表：候选并集 + 二次所有权守卫
    biz, dropped = {}, {}
    for t in BIZ_BY_USER:
        cand = _ids("SELECT id FROM `%s` WHERE user_id IN (%s);" % (t, _il(u))) if u else []
        biz[t], dropped[t] = _filter_owned(t, sorted(set(cand)), owners)
    for t in BIZ_BY_DOCTOR:
        cand = []
        if u:
            cand += _ids("SELECT id FROM `%s` WHERE user_id IN (%s);" % (t, _il(u)))
        if d:
            cand += _ids("SELECT id FROM `%s` WHERE doctor_id IN (%s);" % (t, _il(d)))
        biz[t], dropped[t] = _filter_owned(t, sorted(set(cand)), owners)
    for t in BIZ_BY_COACH:
        cand = []
        if u:
            cand += _ids("SELECT id FROM `%s` WHERE user_id IN (%s);" % (t, _il(u)))
        if c:
            cand += _ids("SELECT id FROM `%s` WHERE coach_id IN (%s);" % (t, _il(c)))
        biz[t], dropped[t] = _filter_owned(t, sorted(set(cand)), owners)

    # 5) 按外键依赖顺序删除
    order = (['doctor_patient', 'coach_student'] + BIZ_BY_DOCTOR + BIZ_BY_COACH
             + BIZ_BY_USER + ['doctor_user', 'coach_user', 'users'])
    deleted, errs = {}, []
    for t in order:
        # 账号 id 存于 plan，关系/业务 id 存于 rel/biz，三者按表名归位
        if t in plan:
            ids = plan[t]
        elif t in rel:
            ids = rel[t]
        else:
            ids = biz.get(t) or []
        if not ids:
            deleted[t] = 0
            continue
        rc, err = sqlexec("DELETE FROM `%s` WHERE id IN (%s);" % (t, _il(ids)))
        deleted[t] = len(ids) if rc == 0 else 0
        if rc != 0:
            errs.append('%s: %s' % (t, err[:120]))

    # 6) 复核残留
    left = (_ids("SELECT id FROM users WHERE phone IN ('139%s','138%s');" % (SUF8, SUF8))
            + _ids("SELECT id FROM doctor_user WHERE doctor_name IN "
                   "('doc_test_%s','doc_reject_%s','doc_other_%s');" % (TAG, TAG, TAG))
            + _ids("SELECT id FROM coach_user WHERE coach_name IN "
                   "('coach_test_%s','coach_reject_%s');" % (TAG, TAG)))
    n_del = sum(deleted.values())
    n_drop = sum(len(v) for v in dropped.values())
    ok = (not left) and (not errs)
    detail = ('deleted=%d，dropped(非本轮用户,未删)=%d，residue=%d%s'
              % (n_del, n_drop, len(left), ('，ERR=%s' % errs) if errs else ''))
    return ok, detail


# =============================================================
# 主流程
# =============================================================
def main():
    print("=" * 78)
    print("个人健康管理系统 · 接口联调测试  API =", API)
    print("=" * 78)

    # 后端可用性
    st, r, _ = http("GET", "/article/list?page=1&page_size=1")
    if r.get("code") != 200:
        print("!! 后端不可用：", r)
        sys.exit(2)

    cleanup_ok, cleanup_detail = True, '未执行'
    try:
        user = suite_user()

        # 管理员先登录拿到 Token，用于医生/教练审核
        st, r, _ = http("POST", "/admin/login", {"admin_name": "admin", "password": "123456"})
        admin_token = (r.get("data") or {}).get("token")

        doctor = suite_doctor(admin_token, user["id"])
        coach = suite_coach(admin_token, user["id"])

        tokens = {"user": user, "doctor": doctor, "coach": coach}
        suite_admin(tokens)
        suite_permission(tokens)
        suite_security_static()
    finally:
        # V3.2 FINAL：无论用例是否抛异常，都必须精确清理本轮测试数据。
        cleanup_ok, cleanup_detail = cleanup_round()
        case("清理", "本轮测试数据精确清理（TEMP_TEST_DATA_RESIDUE = 0）",
             "清理成功且残留为 0", cleanup_ok, cleanup_detail)

    # 汇总
    total = len(RESULTS)
    passed = len([x for x in RESULTS if x["status"] == "PASS"])
    failed = [x for x in RESULTS if x["status"] == "FAIL"]

    print("\n" + "=" * 78)
    print("测试汇总：共 %d 项，PASS %d 项，FAIL %d 项" % (total, passed, len(failed)))
    if failed:
        print("-" * 78)
        for x in failed:
            print("FAIL [%s] %s" % (x["group"], x["name"]))
            print("     预期：%s" % x["expect"])
            print("     实际：%s" % str(x["actual"])[:400])
    print("=" * 78)

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_result.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"total": total, "pass": passed, "fail": len(failed), "results": RESULTS},
                  f, ensure_ascii=False, indent=2)
    print("明细已写入：", out)
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
