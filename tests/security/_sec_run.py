# -*- coding: utf-8 -*-
"""A~H 专项验收：权限隔离 + 异常场景。

全部请求走真实 Flask API（127.0.0.1:8080）+ 真实 MySQL。
"""
import datetime
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _sec_lib import (OUT, Rec, get, post, q, q1, scan_sensitive)  # noqa: E402
from _sec_data import PWD                                          # noqa: E402

with io.open(os.path.join(OUT, 'sec_ids.json'), encoding='utf-8') as _f:
    IDS = json.load(_f)

U_A, U_B = IDS['users']['a'], IDS['users']['b']
D_A, D_B = IDS['doctors']['a'], IDS['doctors']['b']
C_A, C_B = IDS['coaches']['a'], IDS['coaches']['b']
ADMIN_ACC = IDS['admin']


# ---------------------------------------------------------------- token
def login_user(phone, pwd=PWD):
    r = post('/user/login', body={'phone': phone, 'password': pwd})
    return (r['data'] or {}).get('token') if r.get('status') == 200 else None


def login_pro(kind, name, pwd=PWD):
    r = post('/%s/login' % kind, body={'%s_name' % kind: name, 'password': pwd})
    return (r['data'] or {}).get('token') if r.get('status') == 200 else None


def login_admin():
    r = post('/admin/login', body={'admin_name': ADMIN_ACC, 'password': '123456'})
    return (r['data'] or {}).get('token') if r.get('status') == 200 else None


def row_uid(x):
    return x.get('user_id') or x.get('id')


# ================================================================= A
APIS = [('user', '/user/info'), ('doctor', '/doctor/patient/list'),
        ('coach', '/coach/student/list'), ('admin', '/admin/user/list')]


def test_A(out):
    r = Rec('A')
    toks = {
        'user': login_user('19900000001'),
        'doctor': login_pro('doctor', 'sec_doctor_a'),
        'coach': login_pro('coach', 'sec_coach_a'),
        'admin': login_admin(),
    }
    for k, v in toks.items():
        if not v:
            raise SystemExit('A 专项：%s token 获取失败' % k)

    n = 0
    for who, tok in toks.items():
        for target, path in APIS:
            n += 1
            resp = get(path, token=tok)
            legal = (who == target)
            cid = 'A-%02d %s Token -> %s API%s' % (n, who, target, '' if legal else '（越权）')
            if legal:
                r.expect_status(cid, who, path, resp, 200, expect='HTTP 200（合法自身接口）')
            else:
                r.expect_status(cid, who, path, resp, 401, expect='HTTP 401（跨角色必须拒绝）')

    # 无 Token
    for target, path in APIS:
        n += 1
        resp = get(path)
        r.expect_status('A-%02d 无 Token -> %s API' % (n, target), 'none', path, resp, 401,
                        expect='HTTP 401（未登录必须拒绝）')

    # 伪造 Token（错误密钥签名）
    import jwt as pyjwt
    now = datetime.datetime.utcnow()
    for target, path in APIS:
        n += 1
        fake = pyjwt.encode({'id': 1, 'role': 3, 'token_type': '%s_token' % target,
                             'iat': now, 'exp': now + datetime.timedelta(hours=1)},
                            'FORGED-WRONG-SECRET', algorithm='HS256')
        if isinstance(fake, bytes):
            fake = fake.decode()
        resp = get(path, raw_token=fake)
        r.expect_status('A-%02d 伪造 Token(错误密钥) -> %s API' % (n, target), 'forged', path,
                        resp, 401, expect='HTTP 401（签名校验必须拒绝）')

    # 损坏 Token（篡改真实 Token 尾部）
    real = toks['admin']
    broken = real[:-6] + ('aaaaaa' if not real.endswith('aaaaaa') else 'bbbbbb')
    for target, path in APIS:
        n += 1
        resp = get(path, raw_token=broken)
        r.expect_status('A-%02d 损坏 Token -> %s API' % (n, target), 'broken', path, resp, 401,
                        expect='HTTP 401（篡改必须拒绝）')

    # 交叉类型：用医生 token 但把 Authorization 写成非 Bearer 形态
    n += 1
    resp = get('/admin/user/list', headers={'Authorization': toks['doctor']})
    r.expect_status('A-%02d 医生 Token 无 Bearer 前缀 -> 管理员 API' % n, 'doctor',
                    '/admin/user/list', resp, 401, expect='HTTP 401')
    return r


# ================================================================= B
def test_B(out):
    r = Rec('B')
    tA = login_pro('doctor', 'sec_doctor_a')
    tB = login_pro('doctor', 'sec_doctor_b')

    for tag, tok, mine, other in (('医生A', tA, U_A, U_B), ('医生B', tB, U_B, U_A)):
        resp = get('/doctor/patient/list?page=1&page_size=50', token=tok)
        rows = ((resp.get('data') or {}).get('list') or [])
        uids = [row_uid(x) for x in rows]
        r.expect_true('B-%s 患者列表包含自己的患者 user=%s' % (tag[-1].lower(), mine), tag,
                      '/doctor/patient/list', mine in uids, resp,
                      expect='列表含 user_id=%s' % mine, note='uids=%s' % uids)
        r.expect_true('B-%s 患者列表不含他人患者 user=%s' % (tag[-1].lower(), other), tag,
                      '/doctor/patient/list', other not in uids, resp,
                      expect='列表不含 user_id=%s' % other, note='uids=%s' % uids)

    cases = [
        ('B-越权-01', '/doctor/patient/detail', 'GET', '患者详情'),
        ('B-越权-02', '/doctor/patient/health_data', 'GET', '健康指标'),
        ('B-越权-03', '/doctor/patient/sleep_data', 'GET', '睡眠数据'),
        ('B-越权-04', '/doctor/patient/sport_data', 'GET', '运动数据'),
        ('B-越权-05', '/doctor/patient/plan_data', 'GET', '健康计划'),
        ('B-越权-06', '/doctor/patient/trend', 'GET', '健康趋势'),
    ]
    for cid, path, _m, label in cases:
        resp = get('%s?user_id=%d' % (path, U_B), token=tA)
        r.expect_status('%s 医生A 直构 user_id=B 读%s' % (cid, label), 'doctor(A)', path + '?user_id=B',
                        resp, 401, expect='HTTP 401（无医患关系必须拒绝）')

    # 正例：自己的患者可读
    resp = get('/doctor/patient/health_data?user_id=%d' % U_A, token=tA)
    n = ((resp.get('data') or {}).get('total'))
    r.expect_status('B-正例-01 医生A 读自己患者健康指标', 'doctor(A)', 'health_data?user_id=A',
                    resp, 200, expect='HTTP 200')
    r.expect_true('B-正例-02 医生A 确实读到患者A的健康记录', 'doctor(A)', 'health_data',
                  bool(n), resp, expect='total>0', note='total=%s' % n)

    # 写越权
    writes = [
        ('B-越权-07', '/doctor/advice/save', {'user_id': U_B, 'advice_content': 'sec 越权写入尝试'}, '健康建议'),
        ('B-越权-08', '/doctor/medical_notice/save',
         {'user_id': U_B, 'notice_title': 'sec 越权', 'notice_content': 'sec 越权',
          'check_date': '2026-10-10 09:00:00'}, '体检通知'),
        ('B-越权-09', '/doctor/medical_record/save',
         {'user_id': U_B, 'record_title': 'sec 越权', 'record_content': 'sec 越权',
          'record_date': '2026-09-29'}, '医疗记录'),
    ]
    for cid, path, body, label in writes:
        resp = post(path, token=tA, body=body)
        r.expect_status('%s 医生A 越权写患者B的%s' % (cid, label), 'doctor(A)', path, resp, 400,
                        expect='HTTP 400（关系校验拒绝）')

    # DB 兜底：确认没有任何 A 医生给 B 用户写入的数据
    for tbl, col in (('doctor_advice', 'advice_content'), ('medical_notice', 'notice_title'),
                     ('medical_record', 'record_title')):
        row = q1('SELECT COUNT(*) AS c FROM %s WHERE doctor_id=%%s AND user_id=%%s' % tbl,
                 (D_A, U_B))
        r.expect_true('B-DB-%s 医生A 对患者B 的%s写入为 0 条' % (tbl, tbl), 'DB',
                      '%s WHERE doctor_id=A AND user_id=B' % tbl, (row or {}).get('c') == 0,
                      resp, expect='count=0', note='count=%s' % (row or {}).get('c'))
    return r


# ================================================================= C
def test_C(out):
    r = Rec('C')
    tA = login_pro('coach', 'sec_coach_a')
    tB = login_pro('coach', 'sec_coach_b')

    for tag, tok, mine, other in (('教练A', tA, U_A, U_B), ('教练B', tB, U_B, U_A)):
        resp = get('/coach/student/list?page=1&page_size=50', token=tok)
        rows = ((resp.get('data') or {}).get('list') or [])
        uids = [row_uid(x) for x in rows]
        r.expect_true('C-%s 学员列表包含自己的学员 user=%s' % (tag[-1].lower(), mine), tag,
                      '/coach/student/list', mine in uids, resp,
                      expect='含 user_id=%s' % mine, note='uids=%s' % uids)
        r.expect_true('C-%s 学员列表不含他人学员 user=%s' % (tag[-1].lower(), other), tag,
                      '/coach/student/list', other not in uids, resp,
                      expect='不含 user_id=%s' % other, note='uids=%s' % uids)

    for cid, path, label in (
            ('C-越权-01', '/coach/student/detail', '学员详情'),
            ('C-越权-02', '/coach/student/sport_data', '学员运动数据'),
            ('C-越权-03', '/coach/student/statistics', '学员运动统计')):
        resp = get('%s?user_id=%d' % (path, U_B), token=tA)
        r.expect_status('%s 教练A 直构 user_id=B 读%s' % (cid, label), 'coach(A)',
                        path + '?user_id=B', resp, 401, expect='HTTP 401（无师生关系必须拒绝）')

    resp = get('/coach/student/sport_data?user_id=%d' % U_A, token=tA)
    r.expect_status('C-正例-01 教练A 读自己学员运动数据', 'coach(A)', 'sport_data?user_id=A',
                    resp, 200, expect='HTTP 200')

    for cid, path, body, label in (
            ('C-越权-04', '/coach/sport_goal/save',
             {'user_id': U_B, 'goal_title': 'sec 越权', 'goal_content': 'sec 越权',
              'start_date': '2026-09-01', 'end_date': '2026-10-01', 'goal_status': 0}, '运动目标'),
            ('C-越权-05', '/coach/training_plan/save',
             {'user_id': U_B, 'plan_title': 'sec 越权', 'plan_content': 'sec 越权',
              'start_date': '2026-09-01', 'end_date': '2026-10-01', 'plan_status': 0}, '训练计划'),
            ('C-越权-06', '/coach/fitness_advice/save',
             {'user_id': U_B, 'advice_content': 'sec 越权'}, '健身建议')):
        resp = post(path, token=tA, body=body)
        r.expect_status('%s 教练A 越权写学员B的%s' % (cid, label), 'coach(A)', path, resp, 400,
                        expect='HTTP 400（关系校验拒绝）')

    # 按业务 id 越权：教练A 改教练B 的目标 / 计划
    g_b = q1('SELECT id FROM sport_goal WHERE coach_id=%s LIMIT 1', (C_B,))
    p_b = q1('SELECT id FROM training_plan WHERE coach_id=%s LIMIT 1', (C_B,))
    if g_b:
        resp = post('/coach/sport_goal/update_status', token=tA,
                    body={'id': g_b['id'], 'goal_status': 1})
        r.expect_status('C-越权-07 教练A 改教练B 的运动目标(id=%s)' % g_b['id'], 'coach(A)',
                        '/coach/sport_goal/update_status', resp, 400,
                        expect='HTTP 400（目标不属于自己）')
    if p_b:
        resp = post('/coach/training_plan/update_status', token=tA,
                    body={'id': p_b['id'], 'plan_status': 1})
        r.expect_status('C-越权-08 教练A 改教练B 的训练计划(id=%s)' % p_b['id'], 'coach(A)',
                        '/coach/training_plan/update_status', resp, 400,
                        expect='HTTP 400（计划不属于自己）')

    for tbl in ('sport_goal', 'training_plan', 'fitness_advice'):
        row = q1('SELECT COUNT(*) AS c FROM %s WHERE coach_id=%%s AND user_id=%%s' % tbl, (C_A, U_B))
        r.expect_true('C-DB-%s 教练A 对学员B 的写入为 0 条' % tbl, 'DB', tbl,
                      (row or {}).get('c') == 0, resp, expect='count=0',
                      note='count=%s' % (row or {}).get('c'))
    return r


# ================================================================= D
def test_D(out):
    r = Rec('D')
    adm = login_admin()

    # D-01 新注册医生：audit_status 必须为 0
    resp = post('/doctor/register', body={
        'doctor_name': 'sec_audit_doctor_pending', 'password': PWD, 'confirm_password': PWD,
        'real_name': '待审核医生', 'gender': '男', 'phone': '19900000301', 'specialty': '全科'})
    did = (resp.get('data') or {}).get('id')
    row = q1('SELECT audit_status FROM doctor_user WHERE id=%s', (did,)) if did else None
    r.expect_true('D-01 新注册医生 audit_status 强制为 0', 'doctor', '/doctor/register',
                  (row or {}).get('audit_status') == 0, resp, expect='audit_status=0',
                  note='实际=%s' % (row or {}).get('audit_status'))

    # D-02 新注册教练：audit_status 必须为 0
    resp = post('/coach/register', body={
        'coach_name': 'sec_audit_coach_pending', 'password': PWD, 'confirm_password': PWD,
        'real_name': '待审核教练', 'gender': '女', 'phone': '19900000303', 'specialty': '减脂'})
    cid = (resp.get('data') or {}).get('id')
    row = q1('SELECT audit_status FROM coach_user WHERE id=%s', (cid,)) if cid else None
    r.expect_true('D-02 新注册教练 audit_status 强制为 0', 'coach', '/coach/register',
                  (row or {}).get('audit_status') == 0, resp, expect='audit_status=0',
                  note='实际=%s' % (row or {}).get('audit_status'))

    # D-03 恶意提交 audit_status=1
    resp = post('/doctor/register', body={
        'doctor_name': 'sec_audit_doctor_evil', 'password': PWD, 'confirm_password': PWD,
        'real_name': '恶意医生', 'gender': '男', 'phone': '19900000302', 'specialty': '骨科',
        'audit_status': 1, 'id': 1, 'role': 3, 'created_at': '2000-01-01 00:00:00'})
    eid = (resp.get('data') or {}).get('id')
    row = q1('SELECT id, audit_status, created_at FROM doctor_user WHERE doctor_name=%s',
             ('sec_audit_doctor_evil',)) if eid else None
    r.expect_true('D-03 医生注册恶意提交 audit_status=1 仍存 0', 'doctor', '/doctor/register',
                  (row or {}).get('audit_status') == 0, resp, expect='DB audit_status=0',
                  note='实际=%s' % json.dumps(row, ensure_ascii=False, default=str))
    r.expect_true('D-04 医生注册忽略客户端 id（未被覆盖为 1）', 'doctor', '/doctor/register',
                  (row or {}).get('id') not in (None, 1), resp, expect='id 为自增新值',
                  note='id=%s' % (row or {}).get('id'))
    r.expect_true('D-05 医生注册忽略客户端 created_at', 'doctor', '/doctor/register',
                  str((row or {}).get('created_at', '')).startswith('2026'), resp,
                  expect='created_at 为 NOW()', note='created_at=%s' % (row or {}).get('created_at'))

    # D-06 audit_status=0 不允许登录
    resp = post('/doctor/login', body={'doctor_name': 'sec_audit_doctor_pending', 'password': PWD})
    r.expect_status('D-06 audit_status=0 医生不允许登录', 'doctor', '/doctor/login', resp, 400,
                    expect='HTTP 400 待审核拦截')
    resp = post('/coach/login', body={'coach_name': 'sec_audit_coach_pending', 'password': PWD})
    r.expect_status('D-07 audit_status=0 教练不允许登录', 'coach', '/coach/login', resp, 400,
                    expect='HTTP 400 待审核拦截')

    # D-08/09 审核改为 2（拒绝）后仍不允许登录
    resp_audit2 = post('/admin/doctor/audit', token=adm, body={'id': did, 'audit_status': 2})
    post('/admin/coach/audit', token=adm, body={'id': cid, 'audit_status': 2})
    row = q1('SELECT audit_status FROM doctor_user WHERE id=%s', (did,))
    r.expect_true('D-08 管理员可把待审核(0)医生改为审核拒绝(2)', 'admin',
                  '/admin/doctor/audit', (row or {}).get('audit_status') == 2, resp_audit2,
                  expect='DB audit_status=2', note='实际=%s' % (row or {}).get('audit_status'))
    resp = post('/doctor/login', body={'doctor_name': 'sec_audit_doctor_pending', 'password': PWD})
    r.expect_status('D-09 audit_status=2 医生不允许登录', 'doctor', '/doctor/login', resp, 400,
                    expect='HTTP 400 拒绝登录')
    resp = post('/coach/login', body={'coach_name': 'sec_audit_coach_pending', 'password': PWD})
    r.expect_status('D-10 audit_status=2 教练不允许登录', 'coach', '/coach/login', resp, 400,
                    expect='HTTP 400 拒绝登录')

    # D-11/12 审核不可逆：已非 0 的申请不得再次修改（产品设计约束，非缺陷）
    resp = post('/admin/doctor/audit', token=adm, body={'id': did, 'audit_status': 1})
    r.expect_status('D-11 审核不可逆：拒绝(2)后不得再改为通过(1)', 'admin',
                    '/admin/doctor/audit', resp, 400,
                    expect='HTTP 400 该申请已完成审核，无需重复操作')
    row = q1('SELECT audit_status FROM doctor_user WHERE id=%s', (did,))
    r.expect_true('D-12 拒绝后状态保持 2（未被改写）', 'DB', 'doctor_user',
                  (row or {}).get('audit_status') == 2, resp, expect='audit_status=2',
                  note='实际=%s' % (row or {}).get('audit_status'))

    # D-13~D-18 另建全新实体，验证 0 -> 1 审核通过后可登录
    resp = post('/doctor/register', body={
        'doctor_name': 'sec_audit_doctor_ok', 'password': PWD, 'confirm_password': PWD,
        'real_name': '可登录医生', 'gender': '男', 'phone': '19900000305', 'specialty': '全科'})
    did_ok = (resp.get('data') or {}).get('id') or (
        q1("SELECT id FROM doctor_user WHERE doctor_name='sec_audit_doctor_ok'") or {}).get('id')
    resp2 = post('/coach/register', body={
        'coach_name': 'sec_audit_coach_ok', 'password': PWD, 'confirm_password': PWD,
        'real_name': '可登录教练', 'gender': '女', 'phone': '19900000306', 'specialty': '减脂'})
    cid_ok = (resp2.get('data') or {}).get('id') or (
        q1("SELECT id FROM coach_user WHERE coach_name='sec_audit_coach_ok'") or {}).get('id')
    st = q1('SELECT audit_status FROM doctor_user WHERE id=%s', (did_ok,))
    r.expect_true('D-13 新注册医生初始 audit_status=0', 'doctor', '/doctor/register',
                  (st or {}).get('audit_status') == 0, resp, expect='audit_status=0',
                  note='id=%s 实际=%s' % (did_ok, (st or {}).get('audit_status')))

    ra = post('/admin/doctor/audit', token=adm, body={'id': did_ok, 'audit_status': 1})
    r.expect_status('D-14 待审核(0) -> 审核通过(1) 允许', 'admin', '/admin/doctor/audit',
                    ra, 200, expect='HTTP 200（0->1 合法）')
    resp = post('/doctor/login', body={'doctor_name': 'sec_audit_doctor_ok', 'password': PWD})
    r.expect_status('D-15 审核通过(1)后医生可登录', 'doctor', '/doctor/login', resp, 200,
                    expect='HTTP 200')
    r.expect_true('D-16 医生登录返回非空 token', 'doctor', '/doctor/login',
                  bool((resp.get('data') or {}).get('token')), resp, expect='token 非空')

    rc = post('/admin/coach/audit', token=adm, body={'id': cid_ok, 'audit_status': 1})
    r.expect_status('D-17 待审核(0) -> 审核通过(1) 教练允许', 'admin', '/admin/coach/audit',
                    rc, 200, expect='HTTP 200（0->1 合法）')
    resp = post('/coach/login', body={'coach_name': 'sec_audit_coach_ok', 'password': PWD})
    r.expect_status('D-18 审核通过(1)后教练可登录', 'coach', '/coach/login', resp, 200,
                    expect='HTTP 200')
    r.expect_true('D-19 教练登录返回非空 token', 'coach', '/coach/login',
                  bool((resp.get('data') or {}).get('token')), resp, expect='token 非空')

    # D-20 已审核通过(1)的申请同样不可重复审核
    resp = post('/admin/doctor/audit', token=adm, body={'id': did_ok, 'audit_status': 2})
    r.expect_status('D-20 已审核通过(1)的申请不可重复审核', 'admin', '/admin/doctor/audit',
                    resp, 400, expect='HTTP 400 该申请已完成审核，无需重复操作')
    return r


# ================================================================= E
def test_E(out):
    r = Rec('E')

    # E-01 普通用户重复手机号
    resp = post('/user/register', body={'phone': '19900000001', 'password': PWD,
                                        'nickname': 'sec_dup', 'gender': '男', 'age': 20,
                                        'height': 170})
    r.expect_status('E-01 普通用户重复手机号注册', 'anon', '/user/register', resp, 400,
                    expect='HTTP 400 该手机号已注册')

    # E-02 医生重复 doctor_name
    resp = post('/doctor/register', body={'doctor_name': 'sec_doctor_a', 'password': PWD,
                                          'confirm_password': PWD, 'real_name': '重复医生',
                                          'gender': '男', 'phone': '19900000901',
                                          'specialty': '全科'})
    r.expect_status('E-02 医生重复 doctor_name 注册', 'anon', '/doctor/register', resp, 400,
                    expect='HTTP 400 账号已注册')

    # E-03 教练重复 coach_name
    resp = post('/coach/register', body={'coach_name': 'sec_coach_a', 'password': PWD,
                                         'confirm_password': PWD, 'real_name': '重复教练',
                                         'gender': '女', 'phone': '19900000902',
                                         'specialty': '减脂'})
    r.expect_status('E-03 教练重复 coach_name 注册', 'anon', '/coach/register', resp, 400,
                    expect='HTTP 400 账号已注册')

    # E-04~E-06 空字段
    resp = post('/user/register', body={'phone': '', 'password': PWD, 'nickname': 'sec_x'})
    r.expect_status('E-04 普通用户空手机号注册', 'anon', '/user/register', resp, 400,
                    expect='HTTP 400 手机号校验')
    resp = post('/user/register', body={'phone': '19900000903', 'password': '', 'nickname': 'x'})
    r.expect_status('E-05 普通用户空密码注册', 'anon', '/user/register', resp, 400,
                    expect='HTTP 400 密码校验')
    resp = post('/user/register', body={'phone': '19900000904', 'password': PWD,
                                        'nickname': ''})
    r.expect_status('E-06 普通用户空昵称注册', 'anon', '/user/register', resp, 400,
                    expect='HTTP 400 昵称校验')

    # E-07 非法手机号
    resp = post('/user/register', body={'phone': '12345', 'password': PWD, 'nickname': 'sec_y'})
    r.expect_status('E-07 非法手机号注册', 'anon', '/user/register', resp, 400,
                    expect='HTTP 400 手机号格式')

    # E-08 非法性别
    resp = post('/user/register', body={'phone': '19900000905', 'password': PWD,
                                        'nickname': 'sec_z', 'gender': '外星人'})
    r.expect_status('E-08 非法性别取值注册', 'anon', '/user/register', resp, 400,
                    expect='HTTP 400 性别取值不合法')

    # E-09 密码过短
    resp = post('/user/register', body={'phone': '19900000906', 'password': '123',
                                        'nickname': 'sec_short'})
    r.expect_status('E-09 密码长度不足注册', 'anon', '/user/register', resp, 400,
                    expect='HTTP 400 密码长度')

    # E-10 confirm_password 不入库
    cols = q("SHOW COLUMNS FROM users")
    names = {c['Field'] for c in cols}
    r.expect_true('E-10 users 表不存在 confirm_password 列', 'DB', 'SHOW COLUMNS FROM users',
                  'confirm_password' not in names, resp, expect='无该列',
                  note='列=%s' % sorted(names))
    cols = q("SHOW COLUMNS FROM doctor_user")
    dn = {c['Field'] for c in cols}
    r.expect_true('E-11 doctor_user 表不存在 confirm_password 列', 'DB',
                  'SHOW COLUMNS FROM doctor_user', 'confirm_password' not in dn, resp,
                  expect='无该列', note='列=%s' % sorted(dn))
    cols = q("SHOW COLUMNS FROM coach_user")
    cn = {c['Field'] for c in cols}
    r.expect_true('E-12 coach_user 表不存在 confirm_password 列', 'DB',
                  'SHOW COLUMNS FROM coach_user', 'confirm_password' not in cn, resp,
                  expect='无该列', note='列=%s' % sorted(cn))

    # E-13 恶意角色字段：注册普通用户时提交 role=3
    resp = post('/user/register', body={'phone': '19900000003', 'password': PWD,
                                        'nickname': 'sec_user_dup', 'gender': '保密',
                                        'age': 22, 'height': 168, 'role': 3, 'id': 99999,
                                        'audit_status': 1, 'created_at': '2000-01-01'})
    uid = (resp.get('data') or {}).get('id')
    row = q1('SELECT id, phone, created_at FROM users WHERE phone=%s', ('19900000003',))
    r.expect_true('E-13 普通用户注册忽略恶意 id=99999', 'anon', '/user/register',
                  (row or {}).get('id') not in (None, 99999), resp, expect='自增新 id',
                  note='id=%s' % (row or {}).get('id'))
    r.expect_true('E-14 普通用户注册忽略恶意 created_at', 'anon', '/user/register',
                  str((row or {}).get('created_at', '')).startswith('2026'), resp,
                  expect='created_at=NOW()', note='created_at=%s' % (row or {}).get('created_at'))

    # E-15 users 表没有 role / audit_status 字段，从结构上排除提权
    r.expect_true('E-15 users 表无 role 字段（结构上无法提权）', 'DB', 'SHOW COLUMNS FROM users',
                  'role' not in names, resp, expect='无 role 列')
    r.expect_true('E-16 users 表无 audit_status 字段', 'DB', 'SHOW COLUMNS FROM users',
                  'audit_status' not in names, resp, expect='无 audit_status 列')
    return r


# ================================================================= F
def test_F(out):
    r = Rec('F')
    adm = login_admin()
    plan = [
        ('user', '/user/login', {'phone': '19900000001'}, '登录'),
        ('doctor', '/doctor/login', {'doctor_name': 'sec_doctor_a'}, '登录'),
        ('coach', '/coach/login', {'coach_name': 'sec_coach_a'}, '登录'),
        ('admin', '/admin/login', {'admin_name': ADMIN_ACC}, '登录'),
    ]
    n = 0
    for kind, path, base, _ in plan:
        n += 1
        resp = post(path, body=dict(base, password='wrong-password-999'))
        r.expect_status('F-%02d %s 正确账号+错误密码' % (n, kind), kind, path, resp, 400,
                        expect='HTTP 400 登录失败')
        hits = scan_sensitive(resp.get('raw', ''))
        r.expect_true('F-%02d* %s 错误密码响应无敏感信息泄露' % (n, kind), kind, path,
                      not hits, resp, expect='无 password_hash/JWT/SQL/traceback',
                      note='命中=%s' % hits)

    for kind, path, base, _ in plan:
        n += 1
        key = list(base.keys())[0]
        resp = post(path, body={key: 'no_such_account_99999', 'password': PWD})
        r.expect_status('F-%02d %s 不存在账号' % (n, kind), kind, path, resp, 400,
                        expect='HTTP 400 登录失败')

    for kind, path, base, _ in plan:
        n += 1
        key = list(base.keys())[0]
        resp = post(path, body={key: '', 'password': PWD})
        r.expect_status('F-%02d %s 空账号' % (n, kind), kind, path, resp, 400,
                        expect='HTTP 400 登录失败')

    for kind, path, base, _ in plan:
        n += 1
        resp = post(path, body=dict(base, password=''))
        r.expect_status('F-%02d %s 空密码' % (n, kind), kind, path, resp, 400,
                        expect='HTTP 400 登录失败')

    # 未审核 / 已拒绝 医生教练
    n += 1
    resp = post('/doctor/login', body={'doctor_name': 'sec_audit_doctor_evil', 'password': PWD})
    r.expect_status('F-%02d 未审核医生登录' % n, 'doctor', '/doctor/login', resp, 400,
                    expect='HTTP 400 待审核拦截')
    hits = scan_sensitive(resp.get('raw', ''))
    r.expect_true('F-%02d* 未审核登录响应无敏感信息' % n, 'doctor', '/doctor/login', not hits,
                  resp, expect='无敏感信息', note='命中=%s' % hits)

    # 审核拒绝场景：把 pending 医生改回 2 再测（复用 D 的实体）
    did = q1('SELECT id FROM doctor_user WHERE doctor_name=%s', ('sec_audit_doctor_pending',))
    cid = q1('SELECT id FROM coach_user WHERE coach_name=%s', ('sec_audit_coach_pending',))
    if did:
        post('/admin/doctor/audit', token=adm, body={'id': did['id'], 'audit_status': 2})
        n += 1
        resp = post('/doctor/login',
                    body={'doctor_name': 'sec_audit_doctor_pending', 'password': PWD})
        r.expect_status('F-%02d 审核拒绝医生登录' % n, 'doctor', '/doctor/login', resp, 400,
                        expect='HTTP 400 拒绝登录')
    if cid:
        post('/admin/coach/audit', token=adm, body={'id': cid['id'], 'audit_status': 2})
        n += 1
        resp = post('/coach/login',
                    body={'coach_name': 'sec_audit_coach_pending', 'password': PWD})
        r.expect_status('F-%02d 审核拒绝教练登录' % n, 'coach', '/coach/login', resp, 400,
                        expect='HTTP 400 拒绝登录')
    return r


# ================================================================= G
MY_APIS = [
    ('/health_record/my_list', '健康指标', True),
    ('/sleep_record/my_list', '睡眠记录', True),
    ('/sport_record/my_list', '运动记录', True),
    ('/health_plan/my_list', '健康计划', True),
    ('/report/statistics', '数据报告', False),
    ('/user/doctor_advice', '医生建议', False),
    ('/user/medical_notice', '体检通知', False),
    ('/user/medical_record', '医疗记录', False),
    ('/user/sport_goal', '运动目标', False),
    ('/user/training_plan', '训练计划', False),
    ('/user/fitness_advice', '健身建议', False),
]


def _walk_uid(obj, acc):
    """递归收集响应里出现的 user_id。"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == 'user_id' and isinstance(v, int):
                acc.add(v)
            else:
                _walk_uid(v, acc)
    elif isinstance(obj, list):
        for x in obj:
            _walk_uid(x, acc)
    return acc


def test_G(out):
    r = Rec('G')
    tA = login_user('19900000001')
    for path, label, has_rows in MY_APIS:
        resp = get('%s?user_id=%d&page=1&page_size=20' % (path, U_B), token=tA)
        ok_http = resp.get('status') == 200
        uids = _walk_uid(resp.get('data'), set())
        leaked = [u for u in uids if u == U_B]
        note = '响应中 user_id 集合=%s' % sorted(uids)
        r.expect_true('G-%s 用户A 篡改 user_id=B 读取「%s」' % (path.split('/')[-1], label),
                      'user(A)', path + '?user_id=B',
                      ok_http and not leaked, resp,
                      expect='不返回用户B的数据（user_id 一律取自 Token）', note=note)

    # 写操作：body 里塞 user_id=B，必须仍写入 A 名下
    resp = post('/health_record/add', token=tA, body={
        'user_id': U_B, 'record_date': '2026-09-30', 'weight': 71.2,
        'blood_pressure_high': 121, 'blood_pressure_low': 79, 'heart_rate': 71,
        'blood_sugar': 5.1})
    r.expect_status('G-写-01 用户A 提交 user_id=B 新增健康记录', 'user(A)', '/health_record/add',
                    resp, 200, expect='HTTP 200（接口忽略客户端 user_id）')
    row = q1('''SELECT user_id FROM health_record
                WHERE record_date='2026-09-30' AND weight=71.2 ORDER BY id DESC LIMIT 1''')
    r.expect_true('G-写-02 新增记录归属用户A（而非B）', 'DB', 'health_record', 
                  (row or {}).get('user_id') == U_A, resp,
                  expect='user_id=%s（A）' % U_A, note='实际=%s' % (row or {}).get('user_id'))

    # 用户 B 的记录数必须未因 A 的越权请求而增加
    resp = post('/health_plan/add', token=tA, body={
        'user_id': U_B, 'plan_title': 'sec_G 越权计划', 'plan_content': 'sec',
        'plan_start': '2026-09-01', 'plan_end': '2026-10-01'})
    row = q1("SELECT user_id FROM health_plan WHERE plan_title='sec_G 越权计划' ORDER BY id DESC LIMIT 1")
    r.expect_true('G-写-03 用户A 附 user_id=B 创建计划仍归属用户A', 'DB', 'health_plan',
                  (row or {}).get('user_id') == U_A, resp, expect='user_id=A',
                  note='实际=%s' % (row or {}).get('user_id'))

    # 越权修改：用户A 尝试改 B 的计划状态
    plan_b = q1('SELECT id FROM health_plan WHERE user_id=%s LIMIT 1', (U_B,))
    if plan_b:
        resp = post('/health_plan/update_status', token=tA,
                    body={'id': plan_b['id'], 'plan_status': 1})
        r.expect_status('G-写-04 用户A 改用户B 的计划状态(id=%s)' % plan_b['id'], 'user(A)',
                        '/health_plan/update_status', resp, 400,
                        expect='HTTP 400（计划不属于自己）')
        row = q1('SELECT plan_status FROM health_plan WHERE id=%s', (plan_b['id'],))
        r.expect_true('G-写-05 用户B 的计划状态未被篡改', 'DB', 'health_plan',
                      (row or {}).get('plan_status') == 0, resp, expect='plan_status=0',
                      note='实际=%s' % (row or {}).get('plan_status'))
    return r


# ================================================================= H
REG_READ = [
    ('/admin/health_record/list', '原始健康指标'),
    ('/admin/sleep_record/list', '睡眠记录'),
    ('/admin/sport_record/list', '运动记录'),
    ('/admin/health_plan/list', '用户健康计划'),
    ('/admin/doctor_advice/list', '医生健康建议'),
    ('/admin/medical_notice/list', '体检通知'),
    ('/admin/medical_record/list', '医疗记录'),
    ('/admin/sport_goal/list', '教练运动目标'),
    ('/admin/training_plan/list', '训练计划'),
    ('/admin/fitness_advice/list', '健身建议'),
]


def test_H(out):
    r = Rec('H')
    adm = login_admin()
    for path, label in REG_READ:
        resp = get('%s?page=1&page_size=5' % path, token=adm)
        r.expect_status('H-%s 管理员监管查看「%s」' % (path.split('/')[-1], label), 'admin',
                        path, resp, 200, expect='HTTP 200（监管只读）')

    # 管理员不得冒充医生/教练创建专业业务数据
    for cid, path, body, label in (
            ('H-越权-01', '/doctor/advice/save',
             {'user_id': U_A, 'advice_content': 'sec 管理员冒充医生'}, '医生健康建议'),
            ('H-越权-02', '/doctor/medical_notice/save',
             {'user_id': U_A, 'notice_title': 'sec', 'notice_content': 'sec',
              'check_date': '2026-10-10 09:00:00'}, '体检通知'),
            ('H-越权-03', '/doctor/medical_record/save',
             {'user_id': U_A, 'record_title': 'sec', 'record_content': 'sec',
              'record_date': '2026-09-29'}, '医疗记录'),
            ('H-越权-04', '/coach/sport_goal/save',
             {'user_id': U_A, 'goal_title': 'sec', 'goal_content': 'sec',
              'start_date': '2026-09-01', 'end_date': '2026-10-01', 'goal_status': 0}, '运动目标'),
            ('H-越权-05', '/coach/training_plan/save',
             {'user_id': U_A, 'plan_title': 'sec', 'plan_content': 'sec',
              'start_date': '2026-09-01', 'end_date': '2026-10-01', 'plan_status': 0}, '训练计划'),
            ('H-越权-06', '/coach/fitness_advice/save',
             {'user_id': U_A, 'advice_content': 'sec'}, '健身建议')):
        resp = post(path, token=adm, body=body)
        r.expect_status('%s 管理员 Token 冒充业务角色写%s' % (cid, label), 'admin', path, resp,
                        401, expect='HTTP 401（Token 类型不匹配）')

    # 管理员不得修改用户原始健康记录
    resp = post('/health_record/add', token=adm, body={
        'record_date': '2026-09-30', 'weight': 80, 'blood_pressure_high': 130,
        'blood_pressure_low': 85, 'heart_rate': 80, 'blood_sugar': 6.0})
    r.expect_status('H-越权-07 管理员 Token 写用户健康记录', 'admin', '/health_record/add',
                    resp, 401, expect='HTTP 401（无此权限）')
    resp = post('/health_plan/add', token=adm, body={
        'plan_title': 'sec', 'plan_content': 'sec',
        'plan_start': '2026-09-01', 'plan_end': '2026-10-01'})
    r.expect_status('H-越权-08 管理员 Token 写用户健康计划', 'admin', '/health_plan/add', resp,
                    401, expect='HTTP 401（无此权限）')

    # 管理员写接口白名单核对（静态）
    from _sec_lib import BACKEND
    src = io.open(os.path.join(BACKEND, 'routes', 'admin.py'), encoding='utf-8').read()
    banned = ['health_record/save', 'health_record/add', 'sleep_record/add', 'sport_record/add',
              'health_plan/add', 'doctor_advice/save', 'medical_record/save',
              'sport_goal/save', 'training_plan/save', 'fitness_advice/save']
    found = [b for b in banned if b in src]
    r.expect_true('H-静态-01 管理员路由中不存在健康/专业业务写入接口', 'static',
                  'routes/admin.py', not found, resp,
                  expect='无任何用户原始数据写接口', note='命中=%s' % found)
    return r


# ================================================================= I
def test_I(out):
    r = Rec('I')
    adm = login_admin()

    resp = post('/admin/doctor/unbind_patient', token=adm,
                body={'doctor_id': D_A, 'user_id': U_A})
    r.expect_status('I-01 管理员解除医患关系（删除前先确认存在）', 'admin',
                    '/admin/doctor/unbind_patient', resp, 200, expect='HTTP 200')
    resp = post('/admin/doctor/bind_patient', token=adm, body={'doctor_id': D_A, 'user_id': U_A})
    r.expect_status('I-02 管理员恢复医患绑定（消除测试副作用）', 'admin',
                    '/admin/doctor/bind_patient', resp, 200, expect='HTTP 200')

    resp = post('/admin/coach/unbind_student', token=adm, body={'coach_id': C_A, 'user_id': U_A})
    r.expect_status('I-03 管理员解除教练学员关系', 'admin', '/admin/coach/unbind_student',
                    resp, 200, expect='HTTP 200')
    resp = post('/admin/coach/bind_student', token=adm, body={'coach_id': C_A, 'user_id': U_A})
    r.expect_status('I-04 管理员恢复教练学员绑定（消除测试副作用）', 'admin',
                    '/admin/coach/bind_student', resp, 200, expect='HTTP 200')

    # 密码重置：重置为与当前相同口令，既产生审计日志又不改变实际状态
    resp = post('/admin/doctor/reset_pwd', token=adm, body={'id': D_B, 'new_password': PWD})
    r.expect_status('I-05 管理员重置医生登录密码', 'admin', '/admin/doctor/reset_pwd', resp, 200,
                    expect='HTTP 200')
    resp = post('/admin/coach/reset_pwd', token=adm, body={'id': C_B, 'new_password': PWD})
    r.expect_status('I-06 管理员重置教练登录密码', 'admin', '/admin/coach/reset_pwd', resp, 200,
                    expect='HTTP 200')

    # 复核：重置后原口令仍可登录（证明重置的是同一口令，未破坏测试数据）
    resp = post('/doctor/login', body={'doctor_name': 'sec_doctor_b', 'password': PWD})
    r.expect_status('I-07 密码重置后医生仍可用原口令登录', 'doctor', '/doctor/login', resp, 200,
                    expect='HTTP 200')

    logs = q('''SELECT operation_type, operation_content, target_type, target_id, created_at
                FROM admin_operation_log ORDER BY id DESC LIMIT 300''')
    types = {x['operation_type'] for x in logs}
    want = ['医生审核通过', '教练审核通过', '医患绑定', '医患解绑',
            '教练学员绑定', '教练学员解绑', '医生密码重置', '教练密码重置']
    for w in want:
        r.expect_true('I-日志 存在「%s」审计记录' % w, 'DB', 'admin_operation_log',
                      w in types, resp, expect='admin_operation_log 含该 operation_type',
                      note='已观测类型=%s' % sorted(types))

    blob = json.dumps(logs, ensure_ascii=False, default=str)
    hits = scan_sensitive(blob)
    r.expect_true('I-08 操作日志不含明文密码/哈希/JWT/Secret/DB密码', 'DB',
                  'admin_operation_log', not hits, resp, expect='无敏感信息',
                  note='命中=%s' % hits)
    r.expect_true('I-09 操作日志不含 password_hash 字样', 'DB', 'admin_operation_log',
                  'password_hash' not in blob, resp, expect='无 password_hash')
    return r


# ================================================================= J
def test_J(out):
    r = Rec('J')
    from _sec_lib import REQUESTS
    total = len(REQUESTS)

    n500 = [x for x in REQUESTS if x['status'] == 500]
    r.expect_true('J-01 全部请求未出现 HTTP 500', 'all', 'REQUESTS', not n500, None,
                  expect='0 个 500', note='总请求=%d，500=%d' % (total, len(n500)))

    nconn = [x for x in REQUESTS if x['status'] is None]
    r.expect_true('J-02 无连接层异常（后端进程全程存活）', 'all', 'REQUESTS', not nconn, None,
                  expect='0 个连接错误', note='连接错误=%d' % len(nconn))

    bad = []
    for x in REQUESTS:
        if x['status'] is None:
            continue
        try:
            j = json.loads(x['raw'])
            if not (isinstance(j, dict) and 'code' in j and 'msg' in j and 'data' in j):
                bad.append(x['path'])
        except Exception:
            bad.append(x['path'])
    r.expect_true('J-03 所有响应均为统一 {code,msg,data} 契约（无 HTML 错误页）', 'all',
                  'REQUESTS', not bad, None, expect='无裸文本/HTML 响应',
                  note='异常=%s' % bad[:5])

    leak = []
    for x in REQUESTS:
        # 登录成功响应按设计必须下发 JWT，不计为泄露
        if x['status'] == 200 and str(x['path']).endswith('/login'):
            continue
        h = scan_sensitive(x['raw'])
        if h:
            leak.append({'path': x['path'], 'status': x['status'], 'hits': h})
    r.expect_true('J-04 全部响应无敏感信息泄露（traceback/SQL/哈希/密钥；登录下发 token 除外）',
                  'all', 'REQUESTS', not leak, None, expect='无泄露',
                  note='泄露项=%s' % json.dumps(leak[:6], ensure_ascii=False))

    hc = get('/health')
    r.expect_status('J-05 经历全部异常请求后后端仍存活', 'anon', '/api/health', hc, 200,
                    expect='HTTP 200（service+database 均 ok）')
    r.expect_true('J-06 /api/health 报告数据库连通', 'anon', '/api/health',
                  (hc.get('json') or {}).get('database') == 'ok', hc,
                  expect='database=ok',
                  note='data=%s' % json.dumps(hc.get('json'), ensure_ascii=False))

    nf = get('/no_such_api_sec_test')
    ok_nf = nf.get('status') == 400 and isinstance(nf.get('json'), dict)
    r.expect_true('J-07 不存在接口返回统一契约而非 HTML 404', 'anon', '/no_such_api_sec_test',
                  ok_nf, nf, expect='HTTP 400 + {code,msg,data}',
                  note='msg=%s' % nf.get('msg'))
    return r


GROUPS = [('A', test_A), ('B', test_B), ('C', test_C), ('D', test_D),
          ('E', test_E), ('F', test_F), ('G', test_G), ('H', test_H),
          ('I', test_I), ('J', test_J)]


def main():
    only = sys.argv[1:] or None
    for name, fn in GROUPS:
        if only and name not in only:
            continue
        print('\n======== 专项 %s ========' % name, flush=True)
        rec = fn(None)
        rec.dump()


if __name__ == '__main__':
    main()
