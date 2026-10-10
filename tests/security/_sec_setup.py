# -*- coding: utf-8 -*-
"""专项验收 · 测试数据准备。

全部通过真实 Flask API 创建（注册 / 审核 / 绑定 / 业务写入），
只使用 sec_ 前缀实体，不触碰任何既有数据。
产出：tests/security/_out/sec_ids.json
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _sec_lib import OUT, post, q1                                  # noqa: E402
from _sec_data import (COACH_NAMES, DOCTOR_NAMES, PWD, SEC_COACHES,  # noqa: E402
                       SEC_DOCTORS, SEC_USERS, cleanup)

ADMIN = ('admin', '123456')


def _ids(resp):
    d = resp.get('data')
    return d.get('id') if isinstance(d, dict) else None


def admin_token():
    r = post('/admin/login', body={'admin_name': ADMIN[0], 'password': ADMIN[1]})
    if r.get('status') != 200:
        raise SystemExit('管理员登录失败: %s %s' % (r.get('status'), r.get('msg')))
    return r['data']['token']


def reg_user(nick, phone, gender, age, height):
    r = post('/user/register', body={'phone': phone, 'password': PWD, 'nickname': nick,
                                     'gender': gender, 'age': age, 'height': height})
    uid = _ids(r)
    if uid is None:
        row = q1('SELECT id FROM users WHERE phone=%s', (phone,))
        uid = row['id'] if row else None
    print('  user  %-14s id=%-5s http=%s %s' % (nick, uid, r.get('status'), r.get('msg')), flush=True)
    return uid


def reg_pro(kind, name, phone, real, gender, specialty):
    r = post('/%s/register' % kind,
             body={'%s_name' % kind: name, 'password': PWD, 'confirm_password': PWD,
                   'real_name': real, 'gender': gender, 'phone': phone, 'specialty': specialty})
    pid = _ids(r)
    if pid is None:
        row = q1('SELECT id FROM %s_user WHERE %s_name=%%s' % (kind, kind), (name,))
        pid = row['id'] if row else None
    print('  %-5s %-14s id=%-5s http=%s %s' % (kind, name, pid, r.get('status'), r.get('msg')), flush=True)
    return pid


def approve(kind, pid, tok):
    r = post('/admin/%s/audit' % kind, token=tok, body={'id': pid, 'audit_status': 1})
    print('  audit %-5s id=%-5s http=%s %s' % (kind, pid, r.get('status'), r.get('msg')), flush=True)
    return r


def bind(kind, pid, uid, tok):
    path = '/admin/doctor/bind_patient' if kind == 'doctor' else '/admin/coach/bind_student'
    key = 'doctor_id' if kind == 'doctor' else 'coach_id'
    r = post(path, token=tok, body={key: pid, 'user_id': uid})
    print('  bind  %-5s %s-%s http=%s %s' % (kind, pid, uid, r.get('status'), r.get('msg')), flush=True)
    return r


def user_token(phone):
    r = post('/user/login', body={'phone': phone, 'password': PWD})
    return r['data']['token'] if r.get('status') == 200 else None


def pro_token(kind, name):
    r = post('/%s/login' % kind, body={'%s_name' % kind: name, 'password': PWD})
    return r['data']['token'] if r.get('status') == 200 else None


def seed_user(uid, tok, tag):
    """给用户造健康数据（走真实 API）。"""
    post('/health_record/add', token=tok, body={
        'record_date': '2026-09-28', 'weight': 70.5 if tag == 'A' else 55.2,
        'blood_pressure_high': 122, 'blood_pressure_low': 80,
        'heart_rate': 72, 'blood_sugar': 5.2})
    post('/health_record/add', token=tok, body={
        'record_date': '2026-09-29', 'weight': 70.1 if tag == 'A' else 55.0,
        'blood_pressure_high': 118, 'blood_pressure_low': 78,
        'heart_rate': 70, 'blood_sugar': 5.0})
    post('/sleep_record/add', token=tok, body={
        'sleep_date': '2026-09-29', 'sleep_start': '2026-09-28 23:00:00',
        'sleep_end': '2026-09-29 07:00:00', 'sleep_quality': '很好'})
    post('/sport_record/add', token=tok, body={
        'sport_date': '2026-09-29', 'sport_type': '跑步', 'sport_duration': 40,
        'calorie': 320, 'remark': 'sec_%s 测试数据' % tag})
    post('/health_plan/add', token=tok, body={
        'plan_title': 'sec_%s 健康计划' % tag, 'plan_content': 'sec 测试计划内容',
        'plan_start': '2026-09-01', 'plan_end': '2026-10-01'})


def seed_doctor(did, uid, tok, tag):
    post('/doctor/advice/save', token=tok,
         body={'user_id': uid, 'advice_content': 'sec_%s 医生健康建议' % tag})
    post('/doctor/medical_notice/save', token=tok, body={
        'user_id': uid, 'notice_title': 'sec_%s 体检通知' % tag,
        'notice_content': 'sec_%s 通知内容' % tag, 'check_date': '2026-10-10 09:00:00'})
    post('/doctor/medical_record/save', token=tok, body={
        'user_id': uid, 'record_title': 'sec_%s 医疗记录' % tag,
        'record_content': 'sec_%s 记录内容' % tag, 'record_date': '2026-09-29'})


def seed_coach(cid, uid, tok, tag):
    post('/coach/sport_goal/save', token=tok, body={
        'user_id': uid, 'goal_title': 'sec_%s 运动目标' % tag,
        'goal_content': 'sec_%s 目标内容' % tag,
        'start_date': '2026-09-01', 'end_date': '2026-10-01', 'goal_status': 0})
    post('/coach/training_plan/save', token=tok, body={
        'user_id': uid, 'plan_title': 'sec_%s 训练计划' % tag,
        'plan_content': 'sec_%s 计划内容' % tag,
        'start_date': '2026-09-01', 'end_date': '2026-10-01', 'plan_status': 0})
    post('/coach/fitness_advice/save', token=tok,
         body={'user_id': uid, 'advice_content': 'sec_%s 健身建议' % tag})


def main():
    print('== 0. 清理历史 sec 测试数据（保证干净起点） ==', flush=True)
    cleanup(dry_run=False)

    tok = admin_token()
    print('== 1. 注册测试用户 ==', flush=True)
    users = {nick: reg_user(nick, phone, g, a, h) for nick, phone, g, a, h in SEC_USERS}
    uA, uB = users['sec_user_a'], users['sec_user_b']

    print('== 2. 注册测试医生/教练 ==', flush=True)
    doctors = {n: reg_pro('doctor', n, p, r, g, s) for n, p, r, g, s in SEC_DOCTORS}
    coaches = {n: reg_pro('coach', n, p, r, g, s) for n, p, r, g, s in SEC_COACHES}
    dA, dB = doctors['sec_doctor_a'], doctors['sec_doctor_b']
    cA, cB = coaches['sec_coach_a'], coaches['sec_coach_b']

    print('== 3. 管理员审核通过 ==', flush=True)
    for pid in (dA, dB):
        approve('doctor', pid, tok)
    for pid in (cA, cB):
        approve('coach', pid, tok)

    print('== 4. 建立绑定关系 ==', flush=True)
    bind('doctor', dA, uA, tok)
    bind('doctor', dB, uB, tok)
    bind('coach', cA, uA, tok)
    bind('coach', cB, uB, tok)

    print('== 5. 造业务数据 ==', flush=True)
    tA = user_token('19900000001')
    tB = user_token('19900000002')
    seed_user(uA, tA, 'A')
    seed_user(uB, tB, 'B')
    dtA = pro_token('doctor', 'sec_doctor_a')
    dtB = pro_token('doctor', 'sec_doctor_b')
    ctA = pro_token('coach', 'sec_coach_a')
    ctB = pro_token('coach', 'sec_coach_b')
    seed_doctor(dA, uA, dtA, 'A')
    seed_doctor(dB, uB, dtB, 'B')
    seed_coach(cA, uA, ctA, 'A')
    seed_coach(cB, uB, ctB, 'B')

    ids = {
        'created_at': '2026-10-01',
        'pwd': PWD,
        'users': {'a': uA, 'b': uB},
        'doctors': {'a': dA, 'b': dB},
        'coaches': {'a': cA, 'b': cB},
        'admin': ADMIN[0],
    }
    os.makedirs(OUT, exist_ok=True)
    with io.open(os.path.join(OUT, 'sec_ids.json'), 'w', encoding='utf-8') as f:
        f.write(json.dumps(ids, ensure_ascii=False, indent=1))
    print('\n== 准备完成 ==')
    print(json.dumps(ids, ensure_ascii=False, indent=1))
    return ids


if __name__ == '__main__':
    main()
