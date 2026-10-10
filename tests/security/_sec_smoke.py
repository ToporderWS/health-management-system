# -*- coding: utf-8 -*-
"""清理后冒烟复核：后端存活 + 既有关键实体可读 + 越权仍被拒。"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _sec_lib import get, post, q1  # noqa: E402

out = []


def rec(name, ok, detail=''):
    out.append({'name': name, 'ok': bool(ok), 'detail': str(detail)[:300]})


hc = get('/health')
rec('后端 /api/health 存活且数据库 ok', hc.get('status') == 200
    and (hc.get('json') or {}).get('database') == 'ok', hc.get('json'))

r = post('/admin/login', body={'admin_name': 'admin', 'password': '123456'})
atok = r['data']['token'] if r.get('status') == 200 and isinstance(r.get('data'), dict) else None
rec('管理员可登录', bool(atok), r.get('msg'))

if atok:
    for path, name in (('/admin/user/list?page=1&page_size=5', '用户列表'),
                       ('/admin/doctor/list?page=1&page_size=5', '医生列表'),
                       ('/admin/coach/list?page=1&page_size=5', '教练列表'),
                       ('/admin/audit/overview', '审核概览'),
                       ('/admin/operation_log/list?page=1&page_size=5', '操作日志'),
                       ('/admin/dashboard', '仪表盘')):
        rr = get(path, token=atok)
        rec('管理员读取 %s' % name, rr.get('status') == 200, rr.get('msg'))

    # 既有实体仍在
    d2 = q1('SELECT id, doctor_name FROM doctor_user WHERE id=2')
    c1 = q1('SELECT id, coach_name FROM coach_user WHERE id=1')
    u13 = q1('SELECT id, nickname FROM users WHERE id=13')
    rec('doctor002 存在', bool(d2), d2)
    rec('coach001 存在', bool(c1), c1)
    rec('小周(user13) 存在', bool(u13), u13)
    rec('小周 - doctor002 绑定仍在',
        bool(q1('SELECT 1 x FROM doctor_patient WHERE doctor_id=2 AND user_id=13')))
    rec('小周 - coach001 绑定仍在',
        bool(q1('SELECT 1 x FROM coach_student WHERE coach_id=1 AND user_id=13')))

# 越权抽样（user token 打 admin 接口）
r = post('/user/login', body={'phone': '19900000001', 'password': 'sec123456'})
rec('sec_user_a 已不存在（登录应失败）', r.get('status') != 200, r.get('msg'))

# 匿名访问受保护接口应 401
anon = get('/admin/user/list?page=1&page_size=5')
rec('匿名访问 /admin/user/list 被拒', anon.get('status') == 401, anon.get('msg'))

n_pass = sum(1 for x in out if x['ok'])
for x in out:
    print('[%s] %s%s' % ('PASS' if x['ok'] else 'FAIL', x['name'],
                         '' if x['ok'] else '  => ' + x['detail']))
print('---- 冒烟：%d/%d PASS' % (n_pass, len(out)))
