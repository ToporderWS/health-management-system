# -*- coding: utf-8 -*-
"""数据盘点：区分「原始业务数据 / 本轮 sec_ 测试数据 / api_test.py 回归数据」。"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _sec_lib import q  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_out')


def rows(sql, args=()):
    return q(sql, args)


def main():
    rep = {}
    rep['counts'] = {
        'users': rows('SELECT COUNT(*) n FROM users')[0]['n'],
        'doctor_user': rows('SELECT COUNT(*) n FROM doctor_user')[0]['n'],
        'coach_user': rows('SELECT COUNT(*) n FROM coach_user')[0]['n'],
    }
    rep['users'] = rows('SELECT id, phone, nickname, created_at FROM users ORDER BY id')
    rep['doctors'] = rows(
        'SELECT id, doctor_name, phone, real_name, audit_status, created_at '
        'FROM doctor_user ORDER BY id')
    rep['coaches'] = rows(
        'SELECT id, coach_name, phone, real_name, audit_status, created_at '
        'FROM coach_user ORDER BY id')
    rep['doctor_patient'] = rows(
        'SELECT doctor_id, user_id FROM doctor_patient ORDER BY doctor_id, user_id')
    rep['coach_student'] = rows(
        'SELECT coach_id, user_id FROM coach_student ORDER BY coach_id, user_id')

    txt = json.dumps(rep, ensure_ascii=False, indent=1, default=str)
    io.open(os.path.join(OUT, 'DB_INVENTORY.json'), 'w', encoding='utf-8').write(txt)

    print('== 行数 ==', json.dumps(rep['counts'], ensure_ascii=False))
    print('\n== users ==')
    for r in rep['users']:
        print('  id=%-4s phone=%-12s nickname=%-16s created=%s' % (
            r['id'], r['phone'], r['nickname'], r['created_at']))
    print('\n== doctor_user ==')
    for r in rep['doctors']:
        print('  id=%-4s name=%-22s phone=%-12s audit=%s real=%s created=%s' % (
            r['id'], r['doctor_name'], r['phone'], r['audit_status'],
            r['real_name'], r['created_at']))
    print('\n== coach_user ==')
    for r in rep['coaches']:
        print('  id=%-4s name=%-22s phone=%-12s audit=%s real=%s created=%s' % (
            r['id'], r['coach_name'], r['phone'], r['audit_status'],
            r['real_name'], r['created_at']))
    print('\n== doctor_patient ==')
    for r in rep['doctor_patient']:
        print('  doctor=%s -> user=%s' % (r['doctor_id'], r['user_id']))
    print('\n== coach_student ==')
    for r in rep['coach_student']:
        print('  coach=%s -> user=%s' % (r['coach_id'], r['user_id']))


if __name__ == '__main__':
    main()
