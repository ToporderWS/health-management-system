# -*- coding: utf-8 -*-
"""存量事项② · 新旧 Token 四角色验证。

  A) 旧 Secret 签发的 Token 调受保护接口 -> 期望 401（密钥已轮换，必然失效）
  B) 重新登录取得新 Token -> 调自身合法接口 -> 期望 200
  C) 跨角色隔离仍成立：新 Token 调他人角色接口 -> 期望 401

只输出判定与 HTTP 状态，不打印 Token 明文。
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _sec_lib import OUT, get, post  # noqa: E402

OLDTOK = os.path.join(OUT, '_jwt_old_tokens.json')

OWN_API = {
    'user': '/user/info',
    'doctor': '/doctor/patient/list',
    'coach': '/coach/student/list',
    'admin': '/admin/user/list',
}
NEW_LOGIN = {
    'user': ('/user/login', {'phone': '19900000001', 'password': 'sec123456'}),
    'doctor': ('/doctor/login', {'doctor_name': 'sec_doctor_a', 'password': 'sec123456'}),
    'coach': ('/coach/login', {'coach_name': 'sec_coach_a', 'password': 'sec123456'}),
    'admin': ('/admin/login', {'admin_name': 'admin', 'password': '123456'}),
}


def main():
    old = json.load(io.open(OLDTOK, encoding='utf-8'))
    res = {'old_token_401': {}, 'new_token_200': {}, 'new_login_status': {},
           'cross_role_401': {}, 'cross_role_detail': {}}

    print('== A) 旧 Token（旧 Secret 签发）应全部 401 ==')
    old_ok = 0
    for role in ('user', 'doctor', 'coach', 'admin'):
        r = get(OWN_API[role], token=old[role])
        ok = (r.get('status') == 401)
        res['old_token_401'][role] = r.get('status')
        old_ok += 1 if ok else 0
        print('   OLD %-7s -> %-24s http=%s code=%s %s'
              % (role, OWN_API[role], r.get('status'), r.get('code'), 'OK' if ok else '!!'))

    print('== B) 重新登录新 Token 应 200 ==')
    new = {}
    new_ok = 0
    for role in ('user', 'doctor', 'coach', 'admin'):
        path, body = NEW_LOGIN[role]
        r = post(path, body=body)
        tok = (r.get('data') or {}).get('token') if isinstance(r.get('data'), dict) else None
        new[role] = tok
        res['new_login_status'][role] = r.get('status')
        r2 = get(OWN_API[role], token=tok) if tok else {'status': None}
        ok = (r2.get('status') == 200)
        res['new_token_200'][role] = r2.get('status')
        new_ok += 1 if ok else 0
        print('   NEW %-7s login=%s -> %-24s http=%s %s'
              % (role, r.get('status'), OWN_API[role], r2.get('status'), 'OK' if ok else '!!'))

    print('== C) 跨角色隔离（新 Token 调他人角色接口）应 401 ==')
    cross_ok, cross_n = 0, 0
    for who, tok in new.items():
        if not tok:
            continue
        for target, path in OWN_API.items():
            if target == who:
                continue
            r = get(path, token=tok)
            cross_n += 1
            ok = (r.get('status') == 401)
            cross_ok += 1 if ok else 0
            res['cross_role_detail']['%s->%s' % (who, target)] = r.get('status')
    res['cross_role_401'] = {'pass': cross_ok, 'total': cross_n}
    print('   跨角色 %d/%d 返回 401' % (cross_ok, cross_n))

    summary = {
        'OLD_TOKEN_INVALIDATED': '%d/4' % old_ok,
        'NEW_TOKEN_VALIDATION': '%d/4' % new_ok,
        'CROSS_ROLE_ISOLATION': '%d/%d' % (cross_ok, cross_n),
        'ALL_PASS': (old_ok == 4 and new_ok == 4 and cross_ok == cross_n),
    }
    with io.open(os.path.join(OUT, 'JWT_TOKEN_VERIFY.json'), 'w', encoding='utf-8') as f:
        f.write(json.dumps({'summary': summary, 'detail': res}, ensure_ascii=False, indent=2))

    print()
    for k, v in summary.items():
        print('%s = %s' % (k, v))
    print()
    print('OLD_USER_TOKEN =', res['old_token_401']['user'])
    print('OLD_DOCTOR_TOKEN =', res['old_token_401']['doctor'])
    print('OLD_COACH_TOKEN =', res['old_token_401']['coach'])
    print('OLD_ADMIN_TOKEN =', res['old_token_401']['admin'])
    print('NEW_USER_TOKEN =', res['new_token_200']['user'])
    print('NEW_DOCTOR_TOKEN =', res['new_token_200']['doctor'])
    print('NEW_COACH_TOKEN =', res['new_token_200']['coach'])
    print('NEW_ADMIN_TOKEN =', res['new_token_200']['admin'])
    return 0 if summary['ALL_PASS'] else 6


if __name__ == '__main__':
    sys.exit(main())
