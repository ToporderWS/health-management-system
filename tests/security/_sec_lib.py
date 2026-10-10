# -*- coding: utf-8 -*-
"""权限隔离 + 异常场景专项验收 · 公共库。

约束：
- 只读测试优先；必要的写操作全部落在 sec_ 前缀的临时数据上；
- HTTP 一律走真实 127.0.0.1:8080 的 Flask API；
- DB 取证走真实 MySQL（health_management）。
"""
import io
import json
import os
import time
import urllib.error
import urllib.request

import pymysql

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.abspath(os.path.join(HERE, '..', '..'))          # health-management-system
BACKEND = os.path.join(PROJECT, 'backend')
OUT = os.path.join(HERE, '_out')

API = 'http://127.0.0.1:8080/api'


def _load_env():
    p = os.path.join(BACKEND, '.env')
    d = {}
    if os.path.exists(p):
        for line in io.open(p, encoding='utf-8'):
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            d[k.strip()] = v.strip()
    return d


_ENV = _load_env()
DB_CFG = dict(
    host=_ENV.get('DB_HOST', '127.0.0.1'),
    port=int(_ENV.get('DB_PORT', '3306')),
    user=_ENV.get('DB_USER', 'root'),
    password=_ENV.get('DB_PASSWORD', ''),
    database=_ENV.get('DB_NAME', 'health_management'),
    charset=_ENV.get('DB_CHARSET', 'utf8mb4'),
    autocommit=True,
)

# ---------------------------------------------------------------- HTTP
REQUESTS = []   # 全量请求留痕（用于报告与 J 专项扫描）


def http(method, path, token=None, body=None, raw_token=None, headers=None, timeout=20):
    """发起真实 HTTP 请求。返回 dict(status, code, msg, data, raw, ms)。"""
    url = path if path.startswith('http') else API + path
    hdr = {'Content-Type': 'application/json'}
    tok = raw_token if raw_token is not None else token
    if tok:
        hdr['Authorization'] = 'Bearer ' + tok
    if headers:
        hdr.update(headers)
    data = json.dumps(body, ensure_ascii=False).encode('utf-8') if body is not None else None
    req = urllib.request.Request(url, data=data, headers=hdr, method=method)
    t0 = time.time()
    status, raw = None, ''
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            status = r.status
            raw = r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        status = e.code
        raw = e.read().decode('utf-8', 'replace')
    except Exception as e:                                   # 连接层异常
        status = None
        raw = 'CONN_ERROR: %s: %s' % (type(e).__name__, e)
    ms = int((time.time() - t0) * 1000)

    code = msg = None
    data_obj = None
    try:
        j = json.loads(raw)
        if isinstance(j, dict):
            code, msg, data_obj = j.get('code'), j.get('msg'), j.get('data')
    except Exception:
        pass
    rec = {'method': method, 'path': path, 'status': status, 'code': code,
           'msg': msg, 'raw': raw[:4000], 'ms': ms,
           'token_kind': ('none' if not tok else ('raw:' + tok[:12] + '…' if raw_token is not None else tok[:12] + '…'))}
    REQUESTS.append(rec)
    return {'status': status, 'code': code, 'msg': msg, 'data': data_obj,
            'raw': raw, 'ms': ms, 'json': (data_obj if data_obj is not None else None)}


def get(path, **kw):
    return http('GET', path, **kw)


def post(path, **kw):
    return http('POST', path, **kw)


# ---------------------------------------------------------------- DB
def conn():
    return pymysql.connect(cursorclass=pymysql.cursors.DictCursor, **DB_CFG)


def q(sql, args=()):
    c = conn()
    try:
        with c.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchall()
    finally:
        c.close()


def q1(sql, args=()):
    r = q(sql, args)
    return r[0] if r else None


def ex(sql, args=()):
    """执行写 SQL（仅用于测试数据准备/清理）。返回影响行数。"""
    c = conn()
    try:
        with c.cursor() as cur:
            n = cur.execute(sql, args)
            return n
    finally:
        c.close()


# ---------------------------------------------------------------- 结果收集
SEV_ORDER = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1, '': 0}


class Rec(object):
    """验收结果收集器。"""

    def __init__(self, group):
        self.group = group
        self.cases = []
        self.t0 = time.time()

    def add(self, cid, role, goal, expect, resp, passed, note='', db='', severity=''):
        case = {
            'id': cid, 'group': self.group, 'role': role, 'goal': goal,
            'expect': expect,
            'http': resp.get('status') if resp else None,
            'code': resp.get('code') if resp else None,
            'msg': resp.get('msg') if resp else None,
            'passed': bool(passed), 'note': note, 'db': db, 'severity': severity if not passed else '',
        }
        self.cases.append(case)
        flag = 'PASS' if passed else 'FAIL'
        print('[%s] %-46s http=%-4s code=%-4s %s' % (
            flag, cid, case['http'], case['code'], (case['msg'] or '')[:46]), flush=True)
        return case

    def ok(self, cid, role, goal, resp, expect='被拒绝', note='', db=''):
        """断言：请求被拒绝（HTTP 非 2xx，且 code 为 400/401/403）。"""
        p = resp.get('status') in (400, 401, 403) or resp.get('code') in (400, 401, 403)
        return self.add(cid, role, goal, expect, resp, p, note, db)

    def expect_status(self, cid, role, goal, resp, want, expect='', note='', db=''):
        p = resp.get('status') == want
        return self.add(cid, role, goal, expect or ('HTTP %s' % want), resp, p, note, db)

    def expect_true(self, cid, role, goal, cond, resp, expect='', note='', db=''):
        return self.add(cid, role, goal, expect, resp, bool(cond), note, db)

    def counts(self):
        p = sum(1 for c in self.cases if c['passed'])
        return p, len(self.cases) - p

    def dump(self):
        os.makedirs(OUT, exist_ok=True)
        path = os.path.join(OUT, 'sec_%s.json' % self.group)
        with io.open(path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(self.cases, ensure_ascii=False, indent=1))
        p, f_ = self.counts()
        print('---- %s: %d/%d PASS, %d FAIL (%.0fs) -> %s' % (
            self.group, p, len(self.cases), f_, time.time() - self.t0, path), flush=True)
        return path


# ---------------------------------------------------------------- 登录便捷封装
def login(path, body, token_field='token'):
    r = post(path, body=body)
    tok = None
    if isinstance(r.get('data'), dict):
        tok = r['data'].get(token_field)
    return r, tok


# ---------------------------------------------------------------- 敏感信息扫描
SENSITIVE_PATTERNS = [
    ('password_hash', r'password_hash'),
    ('明文 password 字段', r'"password"\s*:'),
    ('JWT Secret 值', r'phs-v3\.2-final-local-dev-secret'),
    ('DB 密码值', r'123456'),
    ('Python traceback', r'Traceback \(most recent call last\)'),
    ('Flask 调试页', r'Werkzeug Debugger'),
    ('SQL 语句泄露', r'(SELECT |INSERT INTO|UPDATE |DELETE FROM)'),
    ('MySQL 报错', r'(pymysql|MySQLdb|1064|1146|1364|1045)'),
    ('列名泄露', r'(Unknown column|Table .* doesn\'t exist)'),
    ('JWT 原文段', r'eyJ[A-Za-z0-9_\-]{12,}'),
    ('文件路径泄露', r'[A-Za-z]:\\\\'),
    ('venv 路径', r'\.venv|site-packages'),
]

# 追加：当前运行 Secret 由 backend/.env 动态读取（仅驻留内存、不落盘明文），
# 使响应泄露检测在 Secret 轮换后依然有效（原写死旧值特征已随轮换失效）。
if _ENV.get('JWT_SECRET'):
    import re as _re                                                  # noqa: E402
    SENSITIVE_PATTERNS.append(('JWT Secret 值(当前运行)', _re.escape(_ENV['JWT_SECRET'])))


def scan_sensitive(text):
    """返回命中的敏感模式名列表。"""
    import re
    hits = []
    if not text:
        return hits
    for name, pat in SENSITIVE_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            hits.append(name)
    return hits


def summary(resp):
    return '%s / %s' % (resp.get('status'), (resp.get('msg') or resp.get('raw') or '')[:80])
