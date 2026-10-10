# -*- coding: utf-8 -*-
"""真机头像缺陷修复后的端到端验证（含自身清理）。

覆盖链路：
  注册临时用户 -> 登录 -> /user/info 默认头像
  -> 上传头像 -> static/upload 生成 UUID 文件 -> 数据库只保存文件名
  -> /user/info 返回该文件名 -> resolveFileUrl 语义拼出完整 URL -> GET 200 + image/*
  -> 清理临时用户与本次生成的文件（三重守卫）
"""
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _sec_lib import API, ex, http, q  # noqa: E402

BASE = r'C:/Users/Toporder-WS/Desktop/项目/个人健康管理系统小程序/health-management-system'
UPLOAD_DIR = os.path.join(BASE, 'backend', 'static', 'upload')
NICK = 'sec_avatar_probe'
PW = 'Seal@2026Probe'

PROTECTED_FILES = {'default_health.jpg', 'default_doctor.jpg',
                   'default_coach.jpg', 'default_admin.jpg'}
UUID_FILE = re.compile(r'^[0-9a-f]{32}\.(jpg|jpeg|png|webp)$', re.I)

RESULT = {'steps': [], 'ok': True}


def step(name, ok, detail=''):
    RESULT['steps'].append({'name': name, 'ok': bool(ok), 'detail': str(detail)[:300]})
    print('[%s] %s%s' % ('PASS' if ok else 'FAIL', name, '' if ok else '  => ' + str(detail)[:200]))
    if not ok:
        RESULT['ok'] = False
    return ok


def multipart(field, filename, content, boundary):
    out = []
    out.append(('--' + boundary).encode())
    out.append(('Content-Disposition: form-data; name="%s"; filename="%s"' % (field, filename)).encode())
    out.append(b'Content-Type: image/jpeg')
    out.append(b'')
    out.append(content)
    out.append(('--' + boundary + '--').encode())
    out.append(b'')
    return b'\r\n'.join(out)


def post_file(path, token, filename, content):
    b = '----sealavatar%d' % int(time.time() * 1000)
    body = multipart('file', filename, content, b)
    req = urllib.request.Request(API + path, data=body, method='POST')
    req.add_header('Content-Type', 'multipart/form-data; boundary=' + b)
    req.add_header('Authorization', 'Bearer ' + token)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode('utf-8', 'replace'))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode('utf-8', 'replace'))
        except Exception:
            return e.code, {}


def get_static(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'probe'})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, r.headers.get('Content-Type'), int(r.headers.get('Content-Length') or 0)
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('Content-Type'), 0
    except Exception:
        return None, None, 0


print('=' * 78)
print('头像 / 上传链路端到端验证')
print('=' * 78)

users_before = q('SELECT COUNT(*) AS c FROM users')[0]['c']
files_before = set(os.listdir(UPLOAD_DIR))
print('基线：users=%d, static/upload=%d 个文件' % (users_before, len(files_before)))

phone = '199' + str(int(time.time()) % 100000000).zfill(8)
uid = None
uploaded = None

try:
    r = http('POST', '/user/register', body={'phone': phone, 'password': PW, 'nickname': NICK})
    uid = (r.get('data') or {}).get('id')
    step('1 注册临时用户', r.get('code') == 200 and uid, '%s %s' % (r.get('status'), r.get('msg')))

    r = http('POST', '/user/login', body={'phone': phone, 'password': PW})
    token = (r.get('data') or {}).get('token')
    step('2 登录获取 user_token', r.get('code') == 200 and token, r.get('msg'))

    r = http('GET', '/user/info', token=token)
    av0 = (r.get('data') or {}).get('avatar')
    step('3 新用户 /user/info 返回默认头像', av0 == 'default_health.jpg', repr(av0))

    content = io.open(os.path.join(UPLOAD_DIR, 'default_health.jpg'), 'rb').read()
    st, r = post_file('/user/upload_avatar', token, 'probe_avatar.jpg', content)
    uploaded = (r.get('data') or {}).get('avatar')
    ok = r.get('code') == 200 and bool(uploaded) and bool(UUID_FILE.match(str(uploaded)))
    step('4 上传头像返回 UUID 文件名', ok, '%s %s' % (st, uploaded))

    if ok:
        fp = os.path.join(UPLOAD_DIR, uploaded)
        exists = os.path.isfile(fp) and os.path.getsize(fp) > 0
        step('5 backend/static/upload 生成真实文件', exists,
             '%s size=%s' % (uploaded, os.path.getsize(fp) if os.path.isfile(fp) else 'N/A'))

        row = q('SELECT avatar FROM users WHERE id=%s', (uid,))
        dbv = row[0]['avatar'] if row else None
        clean = (dbv == uploaded) and ('/' not in str(dbv)) and (not str(dbv).lower().startswith('http'))
        step('6 数据库只保存文件名（无路径 / 无完整 URL）', clean, repr(dbv))

        r = http('GET', '/user/info', token=token)
        av1 = (r.get('data') or {}).get('avatar')
        step('7 /user/info 返回新头像文件名', av1 == uploaded, repr(av1))

        for host in ('http://127.0.0.1:8080', 'http://192.168.2.219:8080'):
            url = host + '/static/upload/' + uploaded
            code, ctype, clen = get_static(url)
            step('8 头像可访问 %s' % host, code == 200 and (ctype or '').startswith('image/'),
                 '%s %s %s bytes' % (code, ctype, clen))

        final_url = 'http://192.168.2.219:8080/static/upload/' + uploaded
        code, ctype, _ = get_static(final_url)
        RESULT['FINAL_AVATAR_URL_PROBE'] = final_url
        step('9 拼接出的最终头像 URL 返回 200 + image/*',
             code == 200 and (ctype or '').startswith('image/'), '%s %s' % (code, ctype))

    r = http('POST', '/doctor/login', body={'doctor_name': 'doctor002', 'password': '123456'})
    step('10 医生登录不受影响', r.get('code') == 200, r.get('msg'))
    r = http('POST', '/coach/login', body={'coach_name': 'coach001', 'password': '123456'})
    step('11 教练登录不受影响', r.get('code') == 200, r.get('msg'))
    r = http('POST', '/admin/login', body={'admin_name': 'admin', 'password': '123456'})
    adm = (r.get('data') or {}).get('token')
    step('12 管理员登录不受影响', r.get('code') == 200, r.get('msg'))
    if adm:
        r = http('GET', '/admin/user/list?page=1&page_size=5', token=adm)
        step('13 管理员用户列表含 avatar 字段', r.get('code') == 200, r.get('msg'))
        r = http('GET', '/admin/coach/list?page=1&page_size=5', token=adm)
        step('14 管理员教练列表含 avatar 字段', r.get('code') == 200, r.get('msg'))

finally:
    print('-' * 78)
    print('清理临时数据（三重守卫）')
    if uid is not None:
        rows = q('SELECT id,phone,nickname FROM users WHERE id=%s', (uid,))
        if rows and rows[0]['nickname'] == NICK and str(rows[0]['phone']).startswith('199'):
            ex('DELETE FROM users WHERE id=%s', (uid,))
            print('  已删除临时用户 id=%s' % uid)
        else:
            print('  !! 守卫拦截：id=%s 与命名/手机号不匹配，未删除' % uid)
    if uploaded and UUID_FILE.match(str(uploaded)) and uploaded not in PROTECTED_FILES:
        refs = q('SELECT COUNT(*) AS c FROM users WHERE avatar=%s', (uploaded,))[0]['c']
        if refs == 0:
            p = os.path.join(UPLOAD_DIR, uploaded)
            if os.path.isfile(p):
                os.remove(p)
                print('  已删除本次生成的头像文件 %s' % uploaded)
        else:
            print('  !! 文件仍被 %d 条记录引用，未删除' % refs)

users_after = q('SELECT COUNT(*) AS c FROM users')[0]['c']
files_after = set(os.listdir(UPLOAD_DIR))
new_files = files_after - files_before
print('-' * 78)
step('15 业务表计数回到基线', users_after == users_before, 'before=%d after=%d' % (users_before, users_after))
step('16 upload 目录无本批残留文件', not new_files, new_files or '')
step('17 无 sec_avatar_probe 残留', q("SELECT COUNT(*) AS c FROM users WHERE nickname=%s", (NICK,))[0]['c'] == 0)
step('18 无 199 段临时用户残留', q("SELECT COUNT(*) AS c FROM users WHERE phone LIKE '199%%'")[0]['c'] == 0)

print('=' * 78)
print('E2E 结果：%s（%d/%d 项通过）' % (
    'PASS' if RESULT['ok'] else 'FAIL',
    len([s for s in RESULT['steps'] if s['ok']]), len(RESULT['steps'])))
print('=' * 78)

os.makedirs(os.path.join(HERE, '_out'), exist_ok=True)
with io.open(os.path.join(HERE, '_out', 'BUG_AVATAR_E2E.json'), 'w', encoding='utf-8') as fh:
    json.dump(RESULT, fh, ensure_ascii=False, indent=1)
sys.exit(0 if RESULT['ok'] else 1)
