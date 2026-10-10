# -*- coding: utf-8 -*-
"""存量事项② · Secret 泄露扫描（只输出命中数量，绝不打印 Secret 本体）。

口径：
  OLD = 轮换前的开发占位值（本文件以「分段拼接」构造，避免扫描器自身成为残留载体）
  NEW = 运行时从 backend/.env 读取（仅驻留内存）

覆盖：backend / management-web(src,public,dist,工程根) / miniapp / tests / docs
"""
import io
import json
import os
import sys

BASE = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system'

# 旧值分段拼接 —— 源码中不存在连续完整值
OLD = ('phs-v3.2-' 'final-local-dev-' 'secret-' 'please-replace-in-production')
OLD_PREFIX = ('phs-v3.2-' 'final-local-dev-secret')

SKIP_DIRS = {'.venv', 'node_modules', 'dist', '__pycache__', '.git', '.idea',
             '.vscode', 'unpackage', '.pytest_cache'}
SKIP_EXT = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.ico', '.woff', '.woff2',
            '.ttf', '.eot', '.mp4', '.zip', '.pyc', '.pdf', '.map', '.svg'}


def read_env_secret():
    p = os.path.join(BASE, 'backend', '.env')
    for line in io.open(p, encoding='utf-8'):
        s = line.strip()
        if s.startswith('JWT_SECRET='):
            return s.split('=', 1)[1].strip()
    return ''


def iter_files(roots, keep_dist=False):
    for root in roots:
        base = os.path.join(BASE, root)
        if os.path.isfile(base):
            yield base
            continue
        if not os.path.isdir(base):
            continue
        for r, ds, fs in os.walk(base):
            ds[:] = [d for d in ds if d not in SKIP_DIRS or (keep_dist and d == 'dist')]
            for f in fs:
                if os.path.splitext(f)[1].lower() in SKIP_EXT:
                    continue
                yield os.path.join(r, f)


def rel(p):
    return os.path.relpath(p, BASE).replace('\\', '/')


def count(needle, roots, exclude=(), keep_dist=False):
    n, hits = 0, {}
    for p in iter_files(roots, keep_dist=keep_dist):
        rp = rel(p)
        if any(rp == e or rp.startswith(e) for e in exclude):
            continue
        try:
            txt = io.open(p, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        c = txt.count(needle)
        if c:
            n += c
            hits[rp] = c
    return n, hits


def count_any(needles, roots, exclude=(), keep_dist=False):
    n, hits = 0, {}
    for p in iter_files(roots, keep_dist=keep_dist):
        rp = rel(p)
        if any(rp == e or rp.startswith(e) for e in exclude):
            continue
        try:
            txt = io.open(p, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        for nd in needles:
            c = txt.count(nd)
            if c:
                n += c
                hits[rp] = hits.get(rp, 0) + c
    return n, hits


def main():
    NEW = read_env_secret()
    assert NEW, 'backend/.env 未读到 JWT_SECRET'
    print('== 扫描基准（只报长度，不报值） ==')
    print('  OLD_SECRET_LENGTH =', len(OLD))
    print('  NEW_SECRET_LENGTH =', len(NEW))
    print('  NEW_FULL_IN_ENV   = %d' % io.open(os.path.join(BASE, 'backend', '.env'),
                                              encoding='utf-8').read().count(NEW))
    print()

    ALL = ['backend', 'management-web/src', 'management-web/public', 'miniapp', 'tests', 'docs']
    r = {}

    n, h = count(OLD, ALL)
    r['OLD_FULL_ANYWHERE'] = {'count': n, 'files': h}
    print('1) 旧 Secret 完整值全项目命中 =', n, h if n else '')

    n, h = count(OLD, ALL, exclude=('backend/.env',))
    r['OLD_FULL_OUTSIDE_ENV'] = {'count': n, 'files': h}
    print('   其中 backend/.env 之外命中 =', n, h if n else '')

    n, h = count(NEW, ALL, exclude=('backend/.env',))
    r['NEW_FULL_OUTSIDE_ENV'] = {'count': n, 'files': h}
    print('2) 新 Secret 完整值 backend/.env 之外命中 =', n, h if n else '')

    n, h = count(OLD_PREFIX, ALL)
    r['OLD_PREFIX_ANYWHERE'] = {'count': n, 'files': h}
    print('3) 旧 Secret 前缀(含截断提及)命中 =', n, h if n else '')

    n, h = count_any(['JWT_SECRET', 'jwt_secret', 'JwtSecret', 'jwtSecret'],
                     ['management-web'], exclude=('management-web/node_modules',))
    r['FRONTEND_JWT_SECRET_TOKEN'] = {'count': n, 'files': h}
    print('4) management-web 内 JWT_SECRET 字样命中 =', n, h if n else '')

    n, h = count_any(['JWT_SECRET', 'jwt_secret', 'JwtSecret', 'jwtSecret'], ['miniapp'])
    r['MINIAPP_JWT_SECRET_TOKEN'] = {'count': n, 'files': h}
    print('5) miniapp 内 JWT_SECRET 字样命中 =', n, h if n else '')

    dist = os.path.join(BASE, 'management-web', 'dist')
    if os.path.isdir(dist):
        n, h = count_any([NEW, OLD, 'JWT_SECRET', 'jwt_secret'], ['management-web/dist'],
                         keep_dist=True)
        r['DIST_SECRET_HIT'] = {'count': n, 'files': h}
        print('6) dist 内 Secret/JWT_SECRET 命中 =', n, h if n else '')
    else:
        r['DIST_SECRET_HIT'] = {'count': 0, 'files': {}, 'note': 'dist 不存在'}
        print('6) dist 不存在 -> 命中 0')

    n, h = count(NEW, ['docs', 'tests', 'backend'], exclude=('backend/.env',))
    r['LOGROPORT_NEW_SECRET'] = {'count': n, 'files': h}
    print('7) docs/tests/backend 内新 Secret 完整值命中（.env 除外）=', n, h if n else '')

    out = os.path.join(BASE, 'tests', 'security', '_out', 'JWT_LEAK_SCAN.json')
    with io.open(out, 'w', encoding='utf-8') as f:
        f.write(json.dumps(r, ensure_ascii=False, indent=2))
    print('\nwritten ->', out)

    ok = (r['OLD_FULL_OUTSIDE_ENV']['count'] == 0 and r['OLD_FULL_ANYWHERE']['count'] == 0
          and r['NEW_FULL_OUTSIDE_ENV']['count'] == 0
          and r['FRONTEND_JWT_SECRET_TOKEN']['count'] == 0
          and r['MINIAPP_JWT_SECRET_TOKEN']['count'] == 0
          and r['DIST_SECRET_HIT']['count'] == 0
          and r['LOGROPORT_NEW_SECRET']['count'] == 0)
    print('LEAK_SCAN_ALL_ZERO =', 'YES' if ok else 'NO')
    return 0 if ok else 5


if __name__ == '__main__':
    sys.exit(main())
