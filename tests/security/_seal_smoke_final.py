# -*- coding: utf-8 -*-
"""最终封板 · 四角色真实冒烟（只读为主，不做任何写操作）。

USER / DOCTOR / COACH / ADMIN 按清单逐项验证；关系权限做“非本人关系应被拒”的反向验证。
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _sec_lib import OUT, get, post, q  # noqa: E402

CASES = []
ADMIN_CRED = ('admin', '123456')


def rec(name, ok, detail=''):
    CASES.append({'name': name, 'ok': bool(ok), 'detail': str(detail)[:200]})


def login(path, body):
    r = post(path, body=body)
    tok = r['data'].get('token') if isinstance(r.get('data'), dict) else None
    return r, tok


def main():
    # ---------------- 依赖数据 ----------------
    d2_patients = [r['user_id'] for r in q('SELECT user_id FROM doctor_patient WHERE doctor_id=2')]
    c1_students = [r['user_id'] for r in q('SELECT user_id FROM coach_student WHERE coach_id=1')]
    all_users = [r['id'] for r in q('SELECT id FROM users ORDER BY id')]
    np_for_doc = next((u for u in all_users if u not in d2_patients), None)
    np_for_coach = next((u for u in all_users if u not in c1_students), None)

    hc = get('/health')
    rec('后端 /api/health 存活', hc.get('status') == 200
        and (hc.get('json') or {}).get('database') == 'ok', hc.get('json'))

    # ================= USER =================
    print('== USER（小周 user13）==')
    r, utok = login('/user/login', {'phone': '13814142525', 'password': '123456'})
    rec('USER 登录', bool(utok), r.get('msg'))
    if utok:
        for path, name in [
            ('/user/info', 'info'),
            ('/health_record/my_list?page=1&page_size=5', '健康记录'),
            ('/sleep_record/my_list?page=1&page_size=5', '睡眠记录'),
            ('/sport_record/my_list?page=1&page_size=5', '运动记录'),
            ('/health_plan/my_list?page=1&page_size=5', '健康计划'),
            ('/report/statistics', '统计报告'),
            ('/user/doctor_advice', '医生建议'),
            ('/user/medical_notice', '体检通知'),
            ('/user/medical_record', '医疗记录'),
            ('/user/sport_goal', '运动目标'),
            ('/user/training_plan', '训练计划'),
            ('/user/fitness_advice', '健身建议'),
        ]:
            rr = get(path, token=utok)
            rec('USER %s' % name, rr.get('status') == 200, rr.get('msg'))

    # ================= DOCTOR =================
    print('== DOCTOR（doctor002）==')
    r, dtok = login('/doctor/login', {'doctor_name': 'doctor002', 'password': '123456'})
    rec('DOCTOR 登录', bool(dtok), r.get('msg'))
    if dtok:
        for path, name in [
            ('/doctor/info', 'info'),
            ('/doctor/dashboard', 'dashboard'),
            ('/doctor/patient/list?page=1&page_size=5', 'patient/list'),
            ('/doctor/patient/health_data?user_id=13', '小周健康数据'),
            ('/doctor/patient/sleep_data?user_id=13', '小周睡眠数据'),
            ('/doctor/patient/sport_data?user_id=13', '小周运动数据'),
            ('/doctor/advice/list?page=1&page_size=5', '医生建议列表'),
        ]:
            rr = get(path, token=dtok)
            rec('DOCTOR %s' % name, rr.get('status') == 200, rr.get('msg'))
        if np_for_doc:
            rr = get('/doctor/patient/health_data?user_id=%d' % np_for_doc, token=dtok)
            rec('DOCTOR 关系权限：非本人患者(user%d) 被拒' % np_for_doc,
                rr.get('status') in (401, 400), rr.get('status'))

    # ================= COACH =================
    print('== COACH（coach001）==')
    r, ctok = login('/coach/login', {'coach_name': 'coach001', 'password': '123456'})
    rec('COACH 登录', bool(ctok), r.get('msg'))
    if ctok:
        for path, name in [
            ('/coach/info', 'info'),
            ('/coach/dashboard', 'dashboard'),
            ('/coach/student/list?page=1&page_size=5', 'student/list'),
            ('/coach/student/sport_data?user_id=13', '小周运动数据'),
            ('/coach/student/statistics?user_id=13', '小周运动统计'),
            ('/coach/sport_goal/list?page=1&page_size=5', '运动目标列表'),
        ]:
            rr = get(path, token=ctok)
            rec('COACH %s' % name, rr.get('status') == 200, rr.get('msg'))
        if np_for_coach:
            rr = get('/coach/student/sport_data?user_id=%d' % np_for_coach, token=ctok)
            rec('COACH 关系权限：非本人学员(user%d) 被拒' % np_for_coach,
                rr.get('status') in (401, 400), rr.get('status'))

    # ================= ADMIN（12 个一级模块） =================
    print('== ADMIN ==')
    r, atok = login('/admin/login', {'admin_name': 'admin', 'password': '123456'})
    rec('ADMIN 登录', bool(atok), r.get('msg'))
    if atok:
        for path, name in [
            ('/admin/dashboard', '首页/仪表盘'),
            ('/admin/user/list?page=1&page_size=5', '1 普通用户管理'),
            ('/admin/doctor/list?page=1&page_size=5', '2 医生管理'),
            ('/admin/coach/list?page=1&page_size=5', '3 教练管理'),
            ('/admin/audit/overview', '4 审核中心'),
            ('/admin/doctor/patient/list?page=1&page_size=5', '5 关系管理'),
            ('/admin/health_record/list?page=1&page_size=5', '6 健康数据'),
            ('/admin/health_plan/list?page=1&page_size=5', '7 健康计划'),
            ('/admin/doctor_advice/list?page=1&page_size=5', '8 医生业务'),
            ('/admin/fitness_advice/list?page=1&page_size=5', '9 教练业务'),
            ('/admin/article/list?page=1&page_size=5', '10 内容运营'),
            ('/admin/system/info', '11 系统管理'),
            ('/admin/operation_log/list?page=1&page_size=5', '12 操作日志'),
        ]:
            rr = get(path, token=atok)
            rec('ADMIN %s' % name, rr.get('status') == 200, rr.get('msg'))
        # 匿名/越权
        rr = get('/admin/user/list?page=1&page_size=5')
        rec('ADMIN 边界：匿名访问被拒', rr.get('status') == 401, rr.get('status'))

    # ---------------- 汇总 ----------------
    n_pass = sum(1 for x in CASES if x['ok'])
    for x in CASES:
        print('[%s] %s%s' % ('PASS' if x['ok'] else 'FAIL', x['name'],
                             '' if x['ok'] else '  => ' + x['detail']))
    print('---- 四角色冒烟：%d/%d PASS' % (n_pass, len(CASES)))

    with io.open(os.path.join(OUT, 'SEAL_SMOKE.json'), 'w', encoding='utf-8') as f:
        json.dump({'pass': n_pass, 'total': len(CASES), 'cases': CASES},
                  f, ensure_ascii=False, indent=1)
    return 0 if n_pass == len(CASES) else 7


if __name__ == '__main__':
    sys.exit(main())
