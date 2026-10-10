# -*- coding: utf-8 -*-
"""只读探针：确认 Flask 后端可用 + 捞出三个角色的可登录 / 待审核账号，供后续真机登录验收使用。"""
import json
import urllib.request

BASE = 'http://127.0.0.1:8080/api'


def post(path, payload):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.status, json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')
    except Exception as e:
        return None, repr(e)


def main():
    print('=== 后端连通性 / 三角色登录探测（密码统一 123456）===')
    cases = [
        ('管理员', '/admin/login', {'admin_name': 'admin', 'password': '123456'}),
        ('医生', '/doctor/login', {'doctor_name': 'doctor001', 'password': '123456'}),
        ('教练', '/coach/login', {'coach_name': 'coach001', 'password': '123456'}),
    ]
    for label, path, payload in cases:
        code, resp = post(path, payload)
        if isinstance(resp, dict):
            print('  %-6s %-16s HTTP=%s code=%s msg=%s' % (label, path, code, resp.get('code'), resp.get('msg')))
        else:
            print('  %-6s %-16s HTTP=%s resp=%s' % (label, path, code, resp))

    print('\n=== 候选账号扫描（找"待审核"拦截样本）===')
    for i in range(1, 5):
        for role, path, key in (('doctor', '/doctor/login', 'doctor_name'),
                                ('coach', '/coach/login', 'coach_name')):
            name = '%s%03d' % (role, i)
            code, resp = post(path, {key: name, 'password': '123456'})
            msg = resp.get('msg') if isinstance(resp, dict) else str(resp)[:60]
            c = resp.get('code') if isinstance(resp, dict) else '?'
            print('  %-10s HTTP=%s code=%s msg=%s' % (name, code, c, msg))


if __name__ == '__main__':
    main()
