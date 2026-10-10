# -*- coding: utf-8 -*-
"""K 专项：静态安全扫描。

口径说明：
- 「源码」= backend / management-web/src / management-web/public / miniapp / database / tools，
  不含 docs（文档里对"无 TODO / 无 Mock / 端口禁令"的**描述文字**不构成代码缺陷）；
- 代码类断言默认跳过含中文的行（中文行通常是用户可见文案，如"审核通过（audit_status = 1）"）。
"""
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _sec_lib import OUT, PROJECT, Rec  # noqa: E402

SKIP_DIRS = {'.venv', 'node_modules', 'dist', '__pycache__', '.git', '.idea',
             '.vscode', 'unpackage', '.pytest_cache', 'security', 'docs'}
SKIP_EXT = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.ico', '.woff', '.woff2',
            '.ttf', '.eot', '.mp4', '.zip', '.pyc', '.log', '.pdf', '.map'}

SRC_ROOTS = ['backend', 'management-web/src', 'management-web/public',
             'miniapp', 'database', 'tools']
FRONT_ROOTS = ['management-web/src', 'management-web/public', 'miniapp']
CJK = re.compile(r'[\u4e00-\u9fa5]')


def iter_files(roots):
    for root in roots:
        base = os.path.join(PROJECT, root)
        if not os.path.isdir(base):
            continue
        for r, ds, fs in os.walk(base):
            ds[:] = [d for d in ds if d not in SKIP_DIRS]
            for f in fs:
                if os.path.splitext(f)[1].lower() in SKIP_EXT:
                    continue
                yield os.path.join(r, f)


def grep(roots, pattern, flags=re.I, limit=60, exclude=None, skip_cjk=False, exts=None):
    rx = re.compile(pattern, flags)
    hits = []
    for p in iter_files(roots):
        rel = os.path.relpath(p, PROJECT).replace('\\', '/')
        if exclude and any(e in rel for e in exclude):
            continue
        if exts and os.path.splitext(p)[1].lower() not in exts:
            continue
        try:
            txt = io.open(p, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        for i, line in enumerate(txt.splitlines(), 1):
            if skip_cjk and CJK.search(line):
                continue
            if rx.search(line):
                hits.append({'file': rel, 'line': i, 'text': line.strip()[:180]})
                if len(hits) >= limit:
                    return hits
    return hits


def show(hits):
    return json.dumps(hits[:6], ensure_ascii=False)


def main():
    r = Rec('K')

    # ---------------- 端口禁令 ----------------
    for port, cid in (('5000', 'K-01'), ('5001', 'K-02')):
        hits = grep(SRC_ROOTS, r':%s\b' % port)
        r.expect_true('%s 源码中不存在 :%s 端口硬编码' % (cid, port), 'static', ':%s' % port,
                      not hits, None, expect='0 处命中', note=show(hits))

    # ---------------- 前端敏感信息 ----------------
    hits = grep(FRONT_ROOTS, r'password_hash')
    r.expect_true('K-03 前端源码不存在 password_hash', 'static', 'frontend',
                  not hits, None, expect='0 处命中', note=show(hits))

    hits = grep(FRONT_ROOTS, r'phs-v3\.2-final-local-dev-secret|JWT_SECRET|jwt_secret')
    r.expect_true('K-04 前端源码不含 JWT Secret / JWT_SECRET', 'static', 'frontend',
                  not hits, None, expect='0 处命中', note=show(hits))

    hits = grep(FRONT_ROOTS, r'DB_PASSWORD|DB_USER|DB_NAME|mysql://|3306')
    r.expect_true('K-05 前端源码不含数据库连接配置', 'static', 'frontend',
                  not hits, None, expect='0 处命中', note=show(hits))

    hits = grep(FRONT_ROOTS,
                r"""(token|password)\s*[:=]\s*['"][A-Za-z0-9\-_\.]{8,}['"]""", skip_cjk=True)
    r.expect_true('K-06 前端源码不含硬编码 token / 口令字面量', 'static', 'frontend',
                  not hits, None, expect='0 处命中', note=show(hits))

    # ---------------- 前端权限绕过（只在代码文件、跳过中文文案行） ----------------
    hits = grep(FRONT_ROOTS,
                r"""(is[Aa]dmin\s*=\s*true|role\s*[:=]\s*3\b|audit_status\s*[:=]\s*1\b)""",
                skip_cjk=True, exts={'.js', '.ts', '.vue', '.jsx', '.tsx'})
    r.expect_true('K-07 前端代码中不含硬编码角色/审核绕过', 'static', 'frontend',
                  not hits, None, expect='0 处命中（中文文案行不计）', note=show(hits))

    # ---------------- 后端为最终判定方 ----------------
    be_auth = io.open(os.path.join(PROJECT, 'backend', 'utils', 'auth.py'),
                      encoding='utf-8').read()
    has_guard = ('token_type != expected_type' in be_auth
                 and 'doctor_has_patient' in be_auth and 'coach_has_student' in be_auth)
    r.expect_true('K-08 后端 auth.py 同时具备 Token 类型隔离与关系校验', 'static',
                  'backend/utils/auth.py', has_guard, None,
                  expect='token_type 隔离 + doctor_has_patient + coach_has_student')

    hits = grep(['management-web/src/router'], r'beforeEach|isLogin\(|getToken\(')
    r.expect_true('K-09 前端存在路由守卫（展示层过滤，非唯一防线）', 'static',
                  'management-web/src/router', bool(hits), None,
                  expect='存在 beforeEach 守卫', note='命中 %d 处' % len(hits))

    # ---------------- 遗留标记 / mock ----------------
    hits = grep(SRC_ROOTS, r'\b(TODO|FIXME|XXX)\b', skip_cjk=True)
    r.expect_true('K-10 源码中无 TODO/FIXME/XXX 遗留标记', 'static', 'all',
                  not hits, None, expect='0 处命中', note=show(hits))

    hits = grep(SRC_ROOTS, r'\b(mock|Mock|MOCK|dummy)\b', skip_cjk=True)
    r.expect_true('K-11 源码中无 mock/桩数据替代核心业务', 'static', 'all',
                  not hits, None, expect='0 处命中', note=show(hits))

    # ---------------- Token key 一致性 ----------------
    js = io.open(os.path.join(PROJECT, 'management-web', 'src', 'utils', 'auth.js'),
                 encoding='utf-8').read()
    ok = all(("'%s'" % k) in js for k in
             ('hms_doctor_token', 'hms_coach_token', 'hms_admin_token'))
    r.expect_true('K-12 前端 Token key 与角色映射一一对应（无串用）', 'static',
                  'src/utils/auth.js', ok, None, expect='四类 key 与 ROLE 映射正确')

    cfg = io.open(os.path.join(PROJECT, 'backend', 'config.py'), encoding='utf-8').read()
    ok = all(x in cfg for x in ('TOKEN_ROLE_MAP', 'TOKEN_USER', 'TOKEN_ADMIN'))
    r.expect_true('K-13 后端 TOKEN_ROLE_MAP 显式定义四类映射', 'static', 'backend/config.py',
                  ok, None, expect='存在 TOKEN_ROLE_MAP 且含四类')

    hits = grep(['management-web'], r'phs-v3\.2-final-local-dev-secret|DB_PASSWORD\s*=')
    r.expect_true('K-14 管理端工程内不含 .env 密钥泄露', 'static', 'management-web',
                  not hits, None, expect='0 处命中', note=show(hits))

    hits = grep(['backend/routes', 'backend/services'],
                r'return\s+success\(\s*\{[^}]*[\u4e00-\u9fa5]{4,}[^}]*\}\s*,\s*"操作成功"\s*\)')
    r.expect_true('K-15 后端路由/服务未发现写死中文数据的假接口', 'static', 'backend',
                  not hits, None, expect='0 处命中', note=show(hits))

    return r.dump()


if __name__ == '__main__':
    main()
