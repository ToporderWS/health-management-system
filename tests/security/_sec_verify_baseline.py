# -*- coding: utf-8 -*-
"""
复验前基线快照 / 复验后复核（只读）。
  python _sec_verify_baseline.py snapshot   -> 写 _out/VERIFY_BEFORE.json
  python _sec_verify_baseline.py verify     -> 与基线比对，输出 INTACT/CHANGED
"""
import os
import sys
import json
import io

BASE = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system'
OUT = os.path.join(BASE, 'tests', 'security', '_out')
SNAP = os.path.join(OUT, 'VERIFY_BEFORE.json')

TABLES = ['users', 'doctor_user', 'coach_user', 'doctor_patient', 'coach_student',
          'health_record', 'sleep_record', 'sport_record', 'health_plan',
          'doctor_advice', 'medical_notice', 'medical_record',
          'sport_goal', 'training_plan', 'fitness_advice', 'admin_operation_log']


def conn():
    import pymysql
    return pymysql.connect(host='127.0.0.1', port=3306, user='root',
                           password='123456', database='health_management',
                           charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)


def take():
    c = conn()
    cur = c.cursor()
    d = {'ts': __import__('time').strftime('%Y-%m-%d %H:%M:%S'), 'counts': {}, 'protected': {}}
    for t in TABLES:
        try:
            cur.execute('SELECT COUNT(*) AS n FROM `%s`' % t)
            d['counts'][t] = cur.fetchone()['n']
        except Exception as e:
            d['counts'][t] = 'ERR:%s' % e
    # 受保护实体
    cur.execute('SELECT id,phone,nickname FROM users WHERE id IN (1,2,12,13)')
    d['protected']['users'] = cur.fetchall()
    cur.execute("SELECT id,doctor_name,audit_status FROM doctor_user WHERE doctor_name IN ('doctor001','doctor002','doctor003')")
    d['protected']['doctors'] = cur.fetchall()
    cur.execute("SELECT id,coach_name,audit_status FROM coach_user WHERE coach_name IN ('coach001','coach002','coach003')")
    d['protected']['coaches'] = cur.fetchall()
    # 小周绑定
    cur.execute('SELECT doctor_id,user_id FROM doctor_patient WHERE user_id=13')
    d['protected']['xiaozhou_doctors'] = cur.fetchall()
    cur.execute('SELECT coach_id,user_id FROM coach_student WHERE user_id=13')
    d['protected']['xiaozhou_coaches'] = cur.fetchall()
    # 小周业务数据行数
    biz = {}
    for t in ['health_record', 'sleep_record', 'sport_record', 'health_plan',
              'doctor_advice', 'medical_notice', 'medical_record',
              'sport_goal', 'training_plan', 'fitness_advice']:
        try:
            cur.execute('SELECT COUNT(*) AS n FROM `%s` WHERE user_id=13' % t)
            biz[t] = cur.fetchone()['n']
        except Exception as e:
            biz[t] = 'ERR:%s' % e
    d['protected']['xiaozhou_biz'] = biz
    # sec_ / api 测试残留
    cur.execute("SELECT COUNT(*) AS n FROM users WHERE nickname LIKE 'sec%' OR phone LIKE '1990000%'")
    d['residual'] = {'sec_users': cur.fetchone()['n']}
    cur.execute("SELECT COUNT(*) AS n FROM doctor_user WHERE doctor_name LIKE 'sec%'")
    d['residual']['sec_doctors'] = cur.fetchone()['n']
    cur.execute("SELECT COUNT(*) AS n FROM coach_user WHERE coach_name LIKE 'sec%'")
    d['residual']['sec_coaches'] = cur.fetchone()['n']
    c.close()
    return d


def snapshot():
    d = take()
    os.makedirs(OUT, exist_ok=True)
    with io.open(SNAP, 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, ensure_ascii=False, indent=2))
    print(json.dumps(d, ensure_ascii=False, indent=2))
    return 0


def verify():
    before = json.load(io.open(SNAP, encoding='utf-8'))
    after = take()
    report = {'before_ts': before['ts'], 'after_ts': after['ts'],
              'count_delta': {}, 'protected_check': {}, 'residual_after': after['residual'],
              'all_intact': True}
    for t in before['counts']:
        b, a = before['counts'][t], after['counts'][t]
        if b != a:
            report['count_delta'][t] = {'before': b, 'after': a, 'delta': (a - b) if isinstance(a, int) and isinstance(b, int) else 'n/a'}
    for k in before['protected']:
        ok = before['protected'][k] == after['protected'][k]
        report['protected_check'][k] = {'intact': ok,
                                        'before': before['protected'][k],
                                        'after': after['protected'][k]}
        if not ok:
            report['all_intact'] = False
    with io.open(os.path.join(OUT, 'VERIFY_AFTER.json'), 'w', encoding='utf-8') as f:
        f.write(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print()
    print('PROTECTED_ALL_INTACT =', report['all_intact'])
    return 0 if report['all_intact'] else 4


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'snapshot'
    sys.exit(snapshot() if cmd == 'snapshot' else verify())
