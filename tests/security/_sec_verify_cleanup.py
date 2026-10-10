# -*- coding: utf-8 -*-
"""
复验轮临时数据清理（白名单 / 唯一标识 / 三重守卫）。

清理范围（严格限定为「本轮复验明确创建」的数据）：
  1) sec_ 前缀实体（_sec_setup.py 创建）：users 30/31/32、doctor 44~48、coach 32~35
  2) api_test.py 本轮创建（时间戳后缀唯一标识 1001190617）：users 33/34、doctor 49/50/51、coach 36/37

守卫（任一不匹配 -> 整批中止）：
  - id 必须在显式白名单内
  - 命名必须命中预期前缀/后缀
  - 受保护实体（小周 13 / doctor001-003 / coach001-003 / users 1,2,12）绝不在清单内

严禁：
  - 使用 LIKE 模糊删除
  - 触碰历届残留（users 3~11、doctor_user 4~16、coach_user 4~11）
  - 修改数据库结构
"""
import os
import sys
import json
import io

BASE = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system'
OUT = os.path.join(BASE, 'tests', 'security', '_out')

# ---- 白名单（id -> 必须匹配的命名断言）----
WL_USERS = {
    30: ('sec_user_a', '19900000001'),
    31: ('sec_user_b', '19900000002'),
    32: ('sec_user_dup', '19900000003'),
    33: (None, '13990852777'),   # api_test 本轮
    34: (None, '13890852777'),
}
WL_DOCTORS = {
    44: 'sec_doctor_a', 45: 'sec_doctor_b',
    46: 'sec_audit_doctor_pending', 47: 'sec_audit_doctor_evil', 48: 'sec_audit_doctor_ok',
    49: 'doc_test_1001190617', 50: 'doc_reject_1001190617', 51: 'doc_other_1001190617',
}
WL_COACHES = {
    32: 'sec_coach_a', 33: 'sec_coach_b',
    34: 'sec_audit_coach_pending', 35: 'sec_audit_coach_ok',
    36: 'coach_test_1001190617', 37: 'coach_reject_1001190617',
}

# 受保护 id（绝不允许出现在删除清单）
PROTECT_USERS = {1, 2, 12, 13}
PROTECT_DOCTORS = {1, 2, 3}
PROTECT_COACHES = {1, 2, 3}

# 子表（按 user_id 关联）
CHILD_TABLES = ['health_record', 'sleep_record', 'sport_record', 'health_plan',
                'doctor_advice', 'medical_notice', 'medical_record',
                'sport_goal', 'training_plan', 'fitness_advice']


def conn():
    import pymysql
    return pymysql.connect(host='127.0.0.1', port=3306, user='root',
                           password='123456', database='health_management',
                           charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)


def plan():
    problems = []
    c = conn()
    cur = c.cursor()

    # 1) 校验 users 白名单
    cur.execute('SELECT id,phone,nickname FROM users WHERE id IN (%s)' % ','.join(map(str, WL_USERS)))
    rows = {r['id']: r for r in cur.fetchall()}
    for uid, (name, phone) in WL_USERS.items():
        if uid not in rows:
            problems.append('users id=%d 不存在（清单要求存在）' % uid)
            continue
        r = rows[uid]
        if phone and r['phone'] != phone:
            problems.append('users id=%d 手机号不匹配: %s != %s' % (uid, r['phone'], phone))
        if name and r['nickname'] != name:
            problems.append('users id=%d 昵称不匹配: %s != %s' % (uid, r['nickname'], name))

    # 2) 校验 doctor
    cur.execute('SELECT id,doctor_name FROM doctor_user WHERE id IN (%s)' % ','.join(map(str, WL_DOCTORS)))
    d = {r['id']: r['doctor_name'] for r in cur.fetchall()}
    for did, dn in WL_DOCTORS.items():
        if did not in d:
            problems.append('doctor_user id=%d 不存在' % did)
        elif d[did] != dn:
            problems.append('doctor_user id=%d 名称不匹配: %s != %s' % (did, d[did], dn))

    # 3) 校验 coach
    cur.execute('SELECT id,coach_name FROM coach_user WHERE id IN (%s)' % ','.join(map(str, WL_COACHES)))
    k = {r['id']: r['coach_name'] for r in cur.fetchall()}
    for cid, cn in WL_COACHES.items():
        if cid not in k:
            problems.append('coach_user id=%d 不存在' % cid)
        elif k[cid] != cn:
            problems.append('coach_user id=%d 名称不匹配: %s != %s' % (cid, k[cid], cn))

    # 4) 受保护实体不得落入清单
    for s, pset, nm in [(set(WL_USERS) & PROTECT_USERS, PROTECT_USERS, 'users'),
                        (set(WL_DOCTORS) & PROTECT_DOCTORS, PROTECT_DOCTORS, 'doctor_user'),
                        (set(WL_COACHES) & PROTECT_COACHES, PROTECT_COACHES, 'coach_user')]:
        if s:
            problems.append('!! 受保护实体落入删除清单: %s %s' % (nm, s))

    # 5) 统计将删除的子表行
    child_rows = {}
    for t in CHILD_TABLES:
        cur.execute('SELECT COUNT(*) AS n FROM `%s` WHERE user_id IN (%s)' % (t, ','.join(map(str, WL_USERS))))
        n = cur.fetchone()['n']
        if n:
            child_rows[t] = n
    cur.execute('SELECT COUNT(*) AS n FROM doctor_patient WHERE user_id IN (%s)' % ','.join(map(str, WL_USERS)))
    child_rows['doctor_patient'] = cur.fetchone()['n']
    cur.execute('SELECT COUNT(*) AS n FROM coach_student WHERE user_id IN (%s)' % ','.join(map(str, WL_USERS)))
    child_rows['coach_student'] = cur.fetchone()['n']

    # 6) 医生/教练侧可能挂的业务行（doctor_advice.doctor_id / medical_* doctor_id）
    extra = {}
    for t, col in [('doctor_advice', 'doctor_id'), ('medical_notice', 'doctor_id'), ('medical_record', 'doctor_id')]:
        try:
            cur.execute('SELECT COUNT(*) AS n FROM `%s` WHERE %s IN (%s)' % (t, col, ','.join(map(str, WL_DOCTORS))))
            extra['%s.%s' % (t, col)] = cur.fetchone()['n']
        except Exception as e:
            extra['%s.%s' % (t, col)] = 'ERR:%s' % e
    c.close()

    p = {'users': sorted(WL_USERS), 'doctors': sorted(WL_DOCTORS), 'coaches': sorted(WL_COACHES),
         'child_rows_by_user_id': child_rows, 'doctor_side_rows': extra, 'problems': problems,
         'safe': not problems}
    return p


def do_delete():
    p = plan()
    if not p['safe']:
        print('!! 守卫失败，整批中止：')
        for x in p['problems']:
            print('   ', x)
        return 2
    c = conn()
    cur = c.cursor()
    log = []
    uids = ','.join(map(str, WL_USERS))
    dids = ','.join(map(str, WL_DOCTORS))
    cids = ','.join(map(str, WL_COACHES))
    # 子表
    for t in CHILD_TABLES:
        cur.execute('DELETE FROM `%s` WHERE user_id IN (%s)' % (t, uids))
        log.append('%s: %d' % (t, cur.rowcount))
    cur.execute('DELETE FROM doctor_patient WHERE user_id IN (%s)' % uids)
    log.append('doctor_patient: %d' % cur.rowcount)
    cur.execute('DELETE FROM coach_student WHERE user_id IN (%s)' % uids)
    log.append('coach_student: %d' % cur.rowcount)
    # 医生侧
    for t, col in [('doctor_advice', 'doctor_id'), ('medical_notice', 'doctor_id'), ('medical_record', 'doctor_id')]:
        try:
            cur.execute('DELETE FROM `%s` WHERE %s IN (%s)' % (t, col, dids))
            log.append('%s(by %s): %d' % (t, col, cur.rowcount))
        except Exception as e:
            log.append('%s(by %s): ERR %s' % (t, col, e))
    # 父表
    cur.execute('DELETE FROM users WHERE id IN (%s)' % uids)
    log.append('users: %d' % cur.rowcount)
    cur.execute('DELETE FROM doctor_user WHERE id IN (%s)' % dids)
    log.append('doctor_user: %d' % cur.rowcount)
    cur.execute('DELETE FROM coach_user WHERE id IN (%s)' % cids)
    log.append('coach_user: %d' % cur.rowcount)
    c.commit()
    c.close()
    print('== 清理执行明细 ==')
    for l in log:
        print('   ', l)
    return 0


if __name__ == '__main__':
    if '--apply' in sys.argv:
        sys.exit(do_delete())
    p = plan()
    print(json.dumps(p, ensure_ascii=False, indent=2))
    with io.open(os.path.join(OUT, 'VERIFY_CLEANUP_PLAN.json'), 'w', encoding='utf-8') as f:
        f.write(json.dumps(p, ensure_ascii=False, indent=2))
    print()
    print('SAFE =', p['safe'])
