# -*- coding: utf-8 -*-
"""最终封板 · 清理后复核（只读）。与 SEAL_BASELINE.json 比对。"""
import io
import os
import re
import sys
import json
import hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _sec_lib import q, q1, PROJECT      # noqa: E402

OUT = os.path.join(PROJECT, 'tests', 'security', '_out')
BASE_F = os.path.join(OUT, 'SEAL_BASELINE.json')

BIZ = ['health_record', 'sleep_record', 'sport_record', 'health_plan',
       'doctor_advice', 'medical_notice', 'medical_record',
       'sport_goal', 'training_plan', 'fitness_advice']


def schema_fingerprint():
    tabs = sorted(list(r.values())[0] for r in q('SHOW TABLES'))
    rows = []
    for t in tabs:
        for c in q("""SELECT COLUMN_NAME,COLUMN_TYPE,IS_NULLABLE,COLUMN_KEY,COLUMN_DEFAULT,EXTRA
                      FROM information_schema.COLUMNS
                      WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s ORDER BY ORDINAL_POSITION""", (t,)):
            rows.append('%s.%s|%s|%s|%s|%s|%s' % (t, c['COLUMN_NAME'], c['COLUMN_TYPE'],
                                                  c['IS_NULLABLE'], c['COLUMN_KEY'],
                                                  c['COLUMN_DEFAULT'], c['EXTRA']))
    return tabs, rows, hashlib.sha256('\n'.join(sorted(rows)).encode('utf-8')).hexdigest()


def main():
    B = json.load(io.open(BASE_F, encoding='utf-8'))
    R = {'checks': {}, 'ok': True}

    def chk(k, v):
        R['checks'][k] = v
        if v is False:
            R['ok'] = False
        print('  %-42s %s' % (k, v))

    tabs, rows, fp = schema_fingerprint()
    print('== 结构 ==')
    chk('TABLE_COUNT_19', len(tabs) == B['table_count'] == 19)
    chk('COLUMN_COUNT_UNCHANGED', len(rows) == B['schema_columns'])
    chk('SCHEMA_FINGERPRINT_UNCHANGED', fp == B['schema_fingerprint'])

    print('== 受保护实体 ==')
    chk('USERS_1_2_12_13_INTACT',
        q('SELECT id,nickname,phone,gender,age FROM users WHERE id IN (1,2,12,13) ORDER BY id')
        == B['protected']['users'])
    chk('DOCTOR_001_002_003_INTACT',
        q("SELECT id,doctor_name,real_name,audit_status FROM doctor_user WHERE doctor_name IN ('doctor001','doctor002','doctor003') ORDER BY id")
        == B['protected']['doctors'])
    chk('COACH_001_002_003_INTACT',
        q("SELECT id,coach_name,real_name,audit_status FROM coach_user WHERE coach_name IN ('coach001','coach002','coach003') ORDER BY id")
        == B['protected']['coaches'])
    chk('XIAOZHOU_DOCTOR_BINDING_INTACT',
        q('SELECT doctor_id,user_id FROM doctor_patient WHERE user_id=13') == B['protected']['xiaozhou_doctors'])
    chk('XIAOZHOU_COACH_BINDING_INTACT',
        q('SELECT coach_id,user_id FROM coach_student WHERE user_id=13') == B['protected']['xiaozhou_coaches'])
    for t in BIZ:
        chk('XIAOZHOU_BIZ_%s_INTACT' % t,
            [r['id'] for r in q('SELECT id FROM `%s` WHERE user_id=13 ORDER BY id' % t)]
            == B['protected']['xiaozhou_biz_ids'][t])

    print('== 残留清除 ==')
    chk('NO_TEST_USERS', not q("SELECT id FROM users WHERE phone LIKE '139908%%' OR phone LIKE '138908%%' OR nickname IN ('测试用户A改','接口测试用户B')"))
    chk('NO_TEST_DOCTORS', not q("SELECT id FROM doctor_user WHERE doctor_name LIKE 'doc\\_%%'"))
    chk('NO_TEST_COACHES', not q("SELECT id FROM coach_user WHERE coach_name LIKE 'coach\\_%%'"))
    chk('NO_SEC_RESIDUE_USERS', not q("SELECT id FROM users WHERE nickname LIKE 'sec%%'"))
    chk('UNCONFIRMED_RETAINED_OK',
        [r['id'] for r in q("SELECT id FROM doctor_user WHERE doctor_name IN ('001','003') ORDER BY id")] == [17, 18]
        and [r['id'] for r in q("SELECT id FROM coach_user WHERE coach_name='002'")] == [12])

    print('== 孤儿 ==')
    chk('NO_ORPHAN_DOCTOR_PATIENT', not q("""SELECT dp.id FROM doctor_patient dp
        LEFT JOIN doctor_user d ON d.id=dp.doctor_id LEFT JOIN users u ON u.id=dp.user_id
        WHERE d.id IS NULL OR u.id IS NULL"""))
    chk('NO_ORPHAN_COACH_STUDENT', not q("""SELECT cs.id FROM coach_student cs
        LEFT JOIN coach_user c ON c.id=cs.coach_id LEFT JOIN users u ON u.id=cs.user_id
        WHERE c.id IS NULL OR u.id IS NULL"""))
    orph_biz = []
    for t in BIZ:
        r = q('SELECT x.id FROM `%s` x LEFT JOIN users u ON u.id=x.user_id WHERE u.id IS NULL LIMIT 1' % t)
        if r:
            orph_biz.append(t)
    chk('NO_ORPHAN_BIZ', not orph_biz)

    print('== 当前计数 ==')
    for t in sorted(list(r.values())[0] for r in q('SHOW TABLES')):
        n = q1('SELECT COUNT(*) AS n FROM `%s`' % t)['n']
        print('  %-20s %s' % (t, n))

    R['after_counts'] = {t: q1('SELECT COUNT(*) AS n FROM `%s`' % t)['n']
                         for t in sorted(list(r.values())[0] for r in q('SHOW TABLES'))}
    R['after_fingerprint'] = fp
    with io.open(os.path.join(OUT, 'SEAL_VERIFY_AFTER.json'), 'w', encoding='utf-8') as f:
        json.dump(R, f, ensure_ascii=False, indent=1, default=str)
    print()
    print('PROTECTED_ALL_INTACT =', R['ok'])
    return 0 if R['ok'] else 4


if __name__ == '__main__':
    sys.exit(main())
