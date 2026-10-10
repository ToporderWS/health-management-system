# -*- coding: utf-8 -*-
"""最终封板 · api_test.py 清理机制验证（运行前→运行→运行后）。"""
import io
import os
import sys
import json
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _sec_lib import q, q1, PROJECT      # noqa: E402

OUT = os.path.join(PROJECT, 'tests', 'security', '_out')
PY = os.path.join(PROJECT, '.venv', 'Scripts', 'python.exe')
TESTS = os.path.join(PROJECT, 'tests')

BIZ = ['health_record', 'sleep_record', 'sport_record', 'health_plan',
       'doctor_advice', 'medical_notice', 'medical_record',
       'sport_goal', 'training_plan', 'fitness_advice']
ACC = ['users', 'doctor_user', 'coach_user', 'doctor_patient', 'coach_student']


def snap():
    d = {}
    for t in ACC + BIZ + ['admin_operation_log']:
        d[t] = q1('SELECT COUNT(*) AS n FROM `%s`' % t)['n']
    d['_protected'] = {
        'users': q('SELECT id,nickname,phone FROM users WHERE id IN (1,2,12,13) ORDER BY id'),
        'dp_13': q('SELECT doctor_id,user_id FROM doctor_patient WHERE user_id=13'),
        'cs_13': q('SELECT coach_id,user_id FROM coach_student WHERE user_id=13'),
        'biz13': {t: [r['id'] for r in q('SELECT id FROM `%s` WHERE user_id=13 ORDER BY id' % t)] for t in BIZ},
    }
    return d


def main():
    before = snap()
    print('== BEFORE ==')
    for t in ACC + BIZ:
        print('  %-18s %s' % (t, before[t]))

    r = subprocess.run([PY, 'api_test.py'], cwd=TESTS, capture_output=True, timeout=1800)
    out = r.stdout.decode('utf-8', 'replace')
    err = r.stderr.decode('utf-8', 'replace')
    with io.open(os.path.join(OUT, '_seal_apitest_run.txt'), 'w', encoding='utf-8') as f:
        f.write(out + '\n\n---- STDERR ----\n' + err)
    print('\n== api_test 结果行 ==')
    for line in out.splitlines():
        if '测试汇总' in line or line.startswith('FAIL ['):
            print('  ', line)
    print('  exit code =', r.returncode)

    after = snap()
    print('\n== AFTER vs BEFORE ==')
    same = True
    for t in ACC + BIZ:
        d = after[t] - before[t]
        flag = '' if d == 0 else '   <-- DELTA'
        if d:
            same = False
        print('  %-18s before=%-4s after=%-4s delta=%s%s' % (t, before[t], after[t], d, flag))
    print('  %-18s before=%-4s after=%-4s (+%s 审计留痕，允许)' % (
        'admin_operation_log', before['admin_operation_log'], after['admin_operation_log'],
        after['admin_operation_log'] - before['admin_operation_log']))

    prot_ok = (after['_protected'] == before['_protected'])
    print('\n  PROTECTED_INTACT =', prot_ok)
    print('  BUSINESS_COUNT_RESTORED =', same)
    res = {'before': before, 'after': after, 'business_restored': same,
           'protected_intact': prot_ok, 'exit_code': r.returncode}
    with io.open(os.path.join(OUT, 'SEAL_APITEST_VERIFY.json'), 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=str)
    return 0 if (same and prot_ok) else 4


if __name__ == '__main__':
    sys.exit(main())
