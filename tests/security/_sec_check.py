# -*- coding: utf-8 -*-
"""核查测试数据是否就绪（只读）。"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _sec_lib import OUT, q  # noqa: E402

with io.open(os.path.join(OUT, 'sec_ids.json'), encoding='utf-8') as f:
    IDS = json.load(f)

uA, uB = IDS['users']['a'], IDS['users']['b']
dA, dB = IDS['doctors']['a'], IDS['doctors']['b']
cA, cB = IDS['coaches']['a'], IDS['coaches']['b']

print('ids: userA=%s userB=%s doctorA=%s doctorB=%s coachA=%s coachB=%s' % (uA, uB, dA, dB, cA, cB))

print('\n-- 用户侧数据 --')
for tbl, uid, tag in [('health_record', uA, 'A'), ('sleep_record', uA, 'A'),
                      ('sport_record', uA, 'A'), ('health_plan', uA, 'A'),
                      ('health_record', uB, 'B'), ('sleep_record', uB, 'B'),
                      ('sport_record', uB, 'B'), ('health_plan', uB, 'B')]:
    r = q('SELECT COUNT(*) AS c FROM %s WHERE user_id=%%s' % tbl, (uid,))
    print('  %-14s user_%s(%s) = %s' % (tbl, tag, uid, r[0]['c']))

print('\n-- 医生侧数据 --')
for tbl in ('doctor_advice', 'medical_notice', 'medical_record'):
    for did, tag in ((dA, 'A'), (dB, 'B')):
        r = q('SELECT COUNT(*) AS c FROM %s WHERE doctor_id=%%s' % tbl, (did,))
        print('  %-15s doctor_%s(%s) = %s' % (tbl, tag, did, r[0]['c']))

print('\n-- 教练侧数据 --')
for tbl in ('sport_goal', 'training_plan', 'fitness_advice'):
    for cid, tag in ((cA, 'A'), (cB, 'B')):
        r = q('SELECT COUNT(*) AS c FROM %s WHERE coach_id=%%s' % tbl, (cid,))
        print('  %-15s coach_%s(%s) = %s' % (tbl, tag, cid, r[0]['c']))

print('\n-- 绑定关系 --')
for tbl, col, pid, uid, tag in [('doctor_patient', 'doctor_id', dA, uA, 'doctorA-userA'),
                                ('doctor_patient', 'doctor_id', dB, uB, 'doctorB-userB'),
                                ('coach_student', 'coach_id', cA, uA, 'coachA-userA'),
                                ('coach_student', 'coach_id', cB, uB, 'coachB-userB')]:
    r = q('SELECT COUNT(*) AS c FROM %s WHERE %s=%%s AND user_id=%%s' % (tbl, col), (pid, uid))
    print('  %-18s = %s' % (tag, r[0]['c']))

print('\n-- 审核状态 --')
for tbl, pk, name in (('doctor_user', 'doctor_name', 'sec_doctor_a'),
                      ('doctor_user', 'doctor_name', 'sec_doctor_b'),
                      ('coach_user', 'coach_name', 'sec_coach_a'),
                      ('coach_user', 'coach_name', 'sec_coach_b')):
    r = q('SELECT id, audit_status FROM %s WHERE %s=%%s' % (tbl, pk), (name,))
    print('  %-16s %s' % (name, r[0] if r else '缺失'))

print('\n-- 既有数据健康度（必须未受影响） --')
print('  users 总数 = %s' % q('SELECT COUNT(*) AS c FROM users')[0]['c'])
print('  doctor_user 总数 = %s' % q('SELECT COUNT(*) AS c FROM doctor_user')[0]['c'])
print('  coach_user 总数 = %s' % q('SELECT COUNT(*) AS c FROM coach_user')[0]['c'])
