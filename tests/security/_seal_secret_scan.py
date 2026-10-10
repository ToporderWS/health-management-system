# -*- coding: utf-8 -*-
"""最终敏感信息扫描（只输出命中数量，绝不打印任何密钥/口令/Token 本体）。

分层口径：
  硬性要求（必须 0）—— 产品运行面：
    A. 旧 JWT Secret 完整值 / 前缀（全项目）
    B. 新 JWT Secret 完整值（backend/.env 之外）
    C. bcrypt 哈希字面量、硬编码 Bearer Token
    D. 产品代码内 DB 密码 / 192.168.1.4 / 192.168.2.219 / :5000 / :5001
    E. dist 产物内 Secret / JWT_SECRET / 两个 LAN IP / DB 密码 / 脚手架
    F. traceback / SQL 错误信息（前端与文档）
  信息项（允许存在，仅记录）—— 历史文档 / 测试证据 / 运行时日志
"""
import io
import json
import os
import re
import sys

BASE = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system'

OLD = ('phs-v3.2-' 'final-local-dev-' 'secret-' 'please-replace-in-production')
OLD_PREFIX = ('phs-v3.2-' 'final-local-dev-secret')

SKIP_DIRS = {'.venv', 'node_modules', '.git', '.idea', '.vscode', 'unpackage',
             '.pytest_cache'}
SKIP_EXT = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.ico', '.woff', '.woff2',
            '.ttf', '.eot', '.mp4', '.zip', '.pyc', '.pdf', '.map', '.svg'}

# 产品运行面（代码/配置）：不含 tests、docs、日志
PROD = ['backend', 'management-web/src', 'management-web/public', 'miniapp']
PROD_EXCLUDE = ('backend/.env', 'backend/server.log')


def read_env():
    d = {}
    p = os.path.join(BASE, 'backend', '.env')
    for line in io.open(p, encoding='utf-8'):
        s = line.strip()
        if s and not s.startswith('#') and '=' in s:
            k, v = s.split('=', 1)
            d[k.strip()] = v.strip()
    return d


def iter_files(roots, include_dist=False):
    for root in roots:
        base = os.path.join(BASE, root)
        if os.path.isfile(base):
            yield base
            continue
        if not os.path.isdir(base):
            continue
        for r, ds, fs in os.walk(base):
            ds[:] = [d for d in ds if d not in SKIP_DIRS or (include_dist and d == 'dist')]
            for f in fs:
                if os.path.splitext(f)[1].lower() in SKIP_EXT:
                    continue
                yield os.path.join(r, f)


def rel(p):
    return os.path.relpath(p, BASE).replace('\\', '/')


def scan(roots, needles=None, regex=None, exclude=(), include_dist=False):
    n, hits = 0, {}
    rx = re.compile(regex) if regex else None
    for p in iter_files(roots, include_dist=include_dist):
        rp = rel(p)
        if any(rp == e or rp.startswith(e) for e in exclude):
            continue
        try:
            txt = io.open(p, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        c = 0
        if needles:
            for nd in needles:
                if nd:
                    c += txt.count(nd)
        if rx:
            c += len(rx.findall(txt))
        if c:
            n += c
            hits[rp] = hits.get(rp, 0) + c
    return {'count': n, 'files': hits}


def main():
    env = read_env()
    NEW = env.get('JWT_SECRET', '')
    DB_PW = env.get('DB_PASSWORD', '')
    assert NEW, 'backend/.env 未读到 JWT_SECRET'
    print('== 基准（只报长度） ==')
    print('  OLD_LEN=%d  NEW_LEN=%d  DB_PW_LEN=%d' % (len(OLD), len(NEW), len(DB_PW)))
    print()

    ALL = ['backend', 'management-web/src', 'management-web/public', 'miniapp',
           'tests', 'docs', 'database']
    r = {}

    print('--- 硬性要求（须为 0） ---')
    for key, kw in [
        ('A_OLD_FULL', dict(roots=ALL, needles=[OLD])),
        ('A2_OLD_PREFIX', dict(roots=ALL, needles=[OLD_PREFIX])),
        ('B_NEW_OUTSIDE_ENV', dict(roots=ALL, needles=[NEW], exclude=('backend/.env',))),
        ('C_BCRYPT', dict(roots=ALL, regex=r'\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}')),
        ('C2_BEARER', dict(roots=ALL, regex=r'Bearer\s+eyJ[A-Za-z0-9_\-]{10,}')),
        ('D_DB_PW_PROD', dict(roots=PROD, needles=[DB_PW] if DB_PW else [], exclude=PROD_EXCLUDE)),
        ('D2_LAN1_4_PROD', dict(roots=PROD, needles=['192.168.1.4'], exclude=PROD_EXCLUDE)),
        ('D3_LAN2_219_PROD', dict(roots=PROD, needles=['192.168.2.219'],
                                  exclude=PROD_EXCLUDE + ('miniapp/common/config.js',))),
        ('D4_PORT_PROD', dict(roots=PROD, needles=[':5000', ':5001'], exclude=PROD_EXCLUDE)),
        ('F_TRACEBACK', dict(roots=['management-web/src', 'management-web/public', 'miniapp'],
                             needles=['Traceback (most recent call last)'])),
        ('F2_SQLERR', dict(roots=['management-web/src', 'management-web/public', 'miniapp'],
                           regex=r'(You have an error in your SQL syntax|pymysql\.err|OperationalError)')),
    ]:
        r[key] = scan(**kw)
        print('  %-18s count=%-5d %s' % (key, r[key]['count'],
                                         list(r[key]['files'])[:6] if r[key]['count'] else ''))

    dist = os.path.join(BASE, 'management-web', 'dist')
    if os.path.isdir(dist):
        r['E_DIST'] = scan(['management-web/dist'],
                           needles=[NEW, OLD, 'JWT_SECRET', 'jwt_secret', DB_PW,
                                    '192.168.1.4', '192.168.2.219'],
                           include_dist=True)
        print('  %-18s count=%-5d %s' % ('E_DIST', r['E_DIST']['count'],
                                         list(r['E_DIST']['files'])[:6] if r['E_DIST']['count'] else ''))
    else:
        r['E_DIST'] = {'count': 0, 'files': {}, 'note': 'dist 不存在'}
        print('  E_DIST             count=0    (dist 不存在)')

    print()
    print('--- 信息项（允许存在：历史文档 / 测试证据 / 运行时日志） ---')
    for key, kw in [
        ('INFO_DB_PW_DOCS', dict(roots=['docs'], needles=[DB_PW] if DB_PW else [])),
        ('INFO_DB_PW_TESTS', dict(roots=['tests'], needles=[DB_PW] if DB_PW else [])),
        ('INFO_LAN1_4_OTHER', dict(roots=['tests', 'docs'], needles=['192.168.1.4'])),
        ('INFO_PORT_OTHER', dict(roots=['tests', 'docs'], needles=[':5000', ':5001'])),
    ]:
        r[key] = scan(**kw)
        print('  %-18s count=%-5d files=%d' % (key, r[key]['count'], len(r[key]['files'])))

    # .env.example 占位符校验
    ex = os.path.join(BASE, 'backend', '.env.example')
    ex_txt = io.open(ex, encoding='utf-8').read()
    ex_secret_line = [l.strip() for l in ex_txt.splitlines() if l.strip().startswith('JWT_SECRET=')]
    ex_val = ex_secret_line[0].split('=', 1)[1] if ex_secret_line else ''
    r['ENV_EXAMPLE_REAL_SECRET'] = {
        'count': (1 if (NEW and NEW in ex_txt) else 0),
        'value_is_placeholder': ex_val == 'CHANGE_ME_TO_A_STRONG_RANDOM_SECRET',
        'line': ex_secret_line[0] if ex_secret_line else '(missing)',
    }
    print()
    print('  .env.example JWT_SECRET 行 =', r['ENV_EXAMPLE_REAL_SECRET']['line'])
    print('  含真实新 Secret =', r['ENV_EXAMPLE_REAL_SECRET']['count'])

    out = os.path.join(BASE, 'tests', 'security', '_out', 'SEAL_SECRET_SCAN.json')
    with io.open(out, 'w', encoding='utf-8') as f:
        f.write(json.dumps(r, ensure_ascii=False, indent=2))

    hard = ['A_OLD_FULL', 'A2_OLD_PREFIX', 'B_NEW_OUTSIDE_ENV', 'C_BCRYPT', 'C2_BEARER',
            'D_DB_PW_PROD', 'D2_LAN1_4_PROD', 'D3_LAN2_219_PROD', 'D4_PORT_PROD',
            'E_DIST', 'F_TRACEBACK', 'F2_SQLERR', 'ENV_EXAMPLE_REAL_SECRET']
    ok = all(r[k]['count'] == 0 for k in hard)
    print()
    print('SECRET_SCAN_HARD_ALL_ZERO =', 'YES' if ok else 'NO')
    print('written ->', out)
    return 0 if ok else 5


if __name__ == '__main__':
    sys.exit(main())
