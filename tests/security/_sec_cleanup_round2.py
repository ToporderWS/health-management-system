# -*- coding: utf-8 -*-
"""存量事项① 复验轮 · 本轮临时数据清理。

严格限定为「本轮 api_test.py 明确创建」的数据：
  users      35(测试用户A改/13990854876)、36(接口测试用户B/13890854876)
  doctor_user 52 doc_test_1001194116、53 doc_reject_1001194116、54 doc_other_1001194116
  coach_user  38 coach_test_1001194116、39 coach_reject_1001194116
  绑定        doctor_patient(52,35)、coach_student(38,35)
  业务行      上述 user_id / doctor_id / coach_id 关联行

守卫（任一不匹配 ⇒ 整批中止，一个都不删）：
  1) id 必须在显式白名单内
  2) 命名必须命中唯一标识断言 / 正则
  3) 受保护实体（小周 13 / users 1,2,12 / doctor001-003 / coach001-003）绝不在清单

严禁：LIKE 模糊删除；触碰历届残留（users 3~11 / doctor_user 4~16 / coach_user 4~11）；
      清理 admin_operation_log（来源未核实）；修改数据库结构。

用法：python _sec_cleanup_round2.py [--apply]
"""
import io
import json
import os
import re
import sys

BASE = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system'
OUT = os.path.join(BASE, 'tests', 'security', '_out')

WL_USERS = {
    35: ('测试用户A改', '13990854876'),
    36: ('接口测试用户B', '13890854876'),
}
WL_DOCTORS = {
    52: 'doc_test_1001194116',
    53: 'doc_reject_1001194116',
    54: 'doc_other_1001194116',
}
WL_COACHES = {
    38: 'coach_test_1001194116',
    39: 'coach_reject_1001194116',
}

RE_USER_PHONE = re.compile(r'^13[89]90854876$')
RE_DOCTOR = re.compile(r'^doc_(test|reject|other)_\d{8,12}$')
RE_COACH = re.compile(r'^coach_(test|reject)_\d{8,12}$')

PROTECT_USERS = {1, 2, 12, 13}
PROTECT_DOCTORS = {1, 2, 3}
PROTECT_COACHES = {1, 2, 3}

CHILD_BY_USER = ['health_record', 'sleep_record', 'sport_record', 'health_plan',
                 'doctor_advice', 'medical_notice', 'medical_record',
                 'sport_goal', 'training_plan', 'fitness_advice',
                 'doctor_patient', 'coach_student']
BY_DOCTOR = [('doctor_advice', 'doctor_id'), ('medical_notice', 'doctor_id'),
             ('medical_record', 'doctor_id')]
BY_COACH = [('sport_goal', 'coach_id'), ('training_plan', 'coach_id'),
            ('fitness_advice', 'coach_id')]


def conn():
    import pymysql
    return pymysql.connect(host='127.0.0.1', port=3306, user='root',
                           password='123456', database='health_management',
                           charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)


def plan():
    problems = []
    c = conn()
    cur = c.cursor()

    ids_u = ','.join(map(str, WL_USERS))
    cur.execute('SELECT id,phone,nickname FROM users WHERE id IN (%s)' % ids_u)
    rows = {r['id']: r for r in cur.fetchall()}
    for uid, (name, phone) in WL_USERS.items():
        if uid not in rows:
            problems.append('users id=%d 不存在（清单要求存在）' % uid)
            continue
        r = rows[uid]
        if r['phone'] != phone:
            problems.append('users id=%d 手机号不匹配: %s != %s' % (uid, r['phone'], phone))
        if r['nickname'] != name:
            problems.append('users id=%d 昵称不匹配: %s != %s' % (uid, r['nickname'], name))
        if not RE_USER_PHONE.match(str(r['phone'])):
            problems.append('users id=%d 手机号未命中唯一标识正则' % uid)

    ids_d = ','.join(map(str, WL_DOCTORS))
    cur.execute('SELECT id,doctor_name FROM doctor_user WHERE id IN (%s)' % ids_d)
    d = {r['id']: r['doctor_name'] for r in cur.fetchall()}
    for did, dn in WL_DOCTORS.items():
        if did not in d:
            problems.append('doctor_user id=%d 不存在' % did)
        elif d[did] != dn:
            problems.append('doctor_user id=%d 名称不匹配: %s != %s' % (did, d[did], dn))
        elif not RE_DOCTOR.match(str(d[did])):
            problems.append('doctor_user id=%d 名称未命中唯一标识正则' % did)

    ids_c = ','.join(map(str, WL_COACHES))
    cur.execute('SELECT id,coach_name FROM coach_user WHERE id IN (%s)' % ids_c)
    k = {r['id']: r['coach_name'] for r in cur.fetchall()}
    for cid, cn in WL_COACHES.items():
        if cid not in k:
            problems.append('coach_user id=%d 不存在' % cid)
        elif k[cid] != cn:
            problems.append('coach_user id=%d 名称不匹配: %s != %s' % (cid, k[cid], cn))
        elif not RE_COACH.match(str(k[cid])):
            problems.append('coach_user id=%d 名称未命中唯一标识正则' % cid)

    for s, nm in [(set(WL_USERS) & PROTECT_USERS, 'users'),
                  (set(WL_DOCTORS) & PROTECT_DOCTORS, 'doctor_user'),
                  (set(WL_COACHES) & PROTECT_COACHES, 'coach_user')]:
        if s:
            problems.append('!! 受保护实体落入删除清单: %s %s' % (nm, s))

    child = {}
    for t in CHILD_BY_USER:
        cur.execute('SELECT COUNT(*) AS n FROM `%s` WHERE user_id IN (%s)' % (t, ids_u))
        child[t + '(by user_id)'] = cur.fetchone()['n']
    for t, col in BY_DOCTOR:
        cur.execute('SELECT COUNT(*) AS n FROM `%s` WHERE %s IN (%s)' % (t, col, ids_d))
        child['%s(by %s)' % (t, col)] = cur.fetchone()['n']
    for t, col in BY_COACH:
        cur.execute('SELECT COUNT(*) AS n FROM `%s` WHERE %s IN (%s)' % (t, col, ids_c))
        child['%s(by %s)' % (t, col)] = cur.fetchone()['n']

    c.close()
    return {'users': sorted(WL_USERS), 'doctors': sorted(WL_DOCTORS),
            'coaches': sorted(WL_COACHES), 'child_rows': child,
            'problems': problems, 'safe': not problems}


def do_delete():
    p = plan()
    if not p['safe']:
        print('!! 守卫失败，整批中止（一个都不删）：')
        for x in p['problems']:
            print('   ', x)
        return 2
    c = conn()
    cur = c.cursor()
    ids_u = ','.join(map(str, WL_USERS))
    ids_d = ','.join(map(str, WL_DOCTORS))
    ids_c = ','.join(map(str, WL_COACHES))
    log = {}
    for t in CHILD_BY_USER:
        cur.execute('DELETE FROM `%s` WHERE user_id IN (%s)' % (t, ids_u))
        log['%s(by user_id)' % t] = cur.rowcount
    for t, col in BY_DOCTOR:
        cur.execute('DELETE FROM `%s` WHERE %s IN (%s)' % (t, col, ids_d))
        log['%s(by %s)' % (t, col)] = cur.rowcount
    for t, col in BY_COACH:
        cur.execute('DELETE FROM `%s` WHERE %s IN (%s)' % (t, col, ids_c))
        log['%s(by %s)' % (t, col)] = cur.rowcount
    cur.execute('DELETE FROM users WHERE id IN (%s)' % ids_u)
    log['users'] = cur.rowcount
    cur.execute('DELETE FROM doctor_user WHERE id IN (%s)' % ids_d)
    log['doctor_user'] = cur.rowcount
    cur.execute('DELETE FROM coach_user WHERE id IN (%s)' % ids_c)
    log['coach_user'] = cur.rowcount
    c.commit()
    c.close()
    tot = sum(v for v in log.values() if isinstance(v, int))
    print('== 清理执行明细 ==')
    for kk in sorted(log):
        print('   %-28s %d' % (kk, log[kk]))
    print('   %-28s %d' % ('合计删除行数', tot))
    return 0


if __name__ == '__main__':
    if '--apply' in sys.argv:
        sys.exit(do_delete())
    p = plan()
    print(json.dumps(p, ensure_ascii=False, indent=2))
    os.makedirs(OUT, exist_ok=True)
    with io.open(os.path.join(OUT, 'ROUND2_CLEANUP_PLAN.json'), 'w', encoding='utf-8') as f:
        f.write(json.dumps(p, ensure_ascii=False, indent=2))
    print()
    print('SAFE =', p['safe'])
