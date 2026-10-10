# -*- coding: utf-8 -*-
"""BUGFIX-01 最终只读复核（只读，不写库、不改文件）。

用项目 venv (pymysql) 执行。输出落盘 _out/_bug_final_verify.txt。
"""
import os
import sys
import json
import urllib.request

BASE = r'C:/Users/Toporder-WS/Desktop/项目/个人健康管理系统小程序/health-management-system'
sys.path.insert(0, os.path.join(BASE, 'backend'))

OUT = []
def p(*a):
    s = ' '.join(str(x) for x in a)
    OUT.append(s)
    print(s)

# ---------- 1. DB 只读 ----------
try:
    import pymysql
    import config as cfgmod
    cfg = cfgmod.Config
    conn = pymysql.connect(
        host=cfg.DB_HOST, port=cfg.DB_PORT, user=cfg.DB_USER,
        password=cfg.DB_PASSWORD, database=cfg.DB_NAME,
        charset=cfg.DB_CHARSET, cursorclass=pymysql.cursors.DictCursor,
    )
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE id=13")
    u13 = cur.fetchone()
    p('USER13 =', json.dumps({k: str(v) for k, v in (u13 or {}).items()}, ensure_ascii=False))

    cur.execute("SELECT COUNT(*) AS c FROM users")
    users_cnt = cur.fetchone()['c']
    p('USERS_COUNT =', users_cnt)

    # 绑定关系
    for t in ['doctor_patient', 'coach_student']:
        try:
            cur.execute("SELECT * FROM %s WHERE user_id=13" % t)
            rows = [{k: str(v) for k, v in r.items()} for r in cur.fetchall()]
            p('BIND_%s_13 = %s' % (t, json.dumps(rows, ensure_ascii=False)))
        except Exception as e:
            p('BIND_%s_13 = N/A(%s)' % (t, str(e)[:50]))

    # 小周 10 类业务数据计数（存在则统计）
    for t in ['health_record', 'diet_record', 'exercise_record', 'weight_record', 'body_data',
              'health_goal', 'reminder', 'consultation', 'message', 'article_collect']:
        try:
            cur.execute("SELECT COUNT(*) AS c FROM %s WHERE user_id=13" % t)
            p('BIZ_%s_13 = %s' % (t, cur.fetchone()['c']))
        except Exception as e:
            p('BIZ_%s_13 = N/A(%s)' % (t, str(e)[:40]))

    # schema
    cur.execute("SELECT COUNT(*) AS c FROM information_schema.tables WHERE table_schema=%s", (cfg.DB_NAME,))
    tbls = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) AS c FROM information_schema.columns WHERE table_schema=%s", (cfg.DB_NAME,))
    cols = cur.fetchone()['c']
    p('SCHEMA_TABLES =', tbls, 'COLUMNS =', cols)
    cur.execute("SELECT table_name AS t FROM information_schema.tables WHERE table_schema=%s ORDER BY table_name", (cfg.DB_NAME,))
    p('TABLE_LIST =', json.dumps([r['t'] for r in cur.fetchall()], ensure_ascii=False))

    # 默认头像引用计数
    cur.execute("SELECT COUNT(*) AS c FROM users WHERE avatar LIKE 'default_%'")
    p('DEFAULT_AVATAR_USERS =', cur.fetchone()['c'])
    cur.execute("SELECT DISTINCT avatar FROM users WHERE avatar IS NOT NULL AND avatar<>''")
    p('DISTINCT_AVATARS =', json.dumps([r['avatar'] for r in cur.fetchall()], ensure_ascii=False))

    conn.close()
    DB_OK = True
except Exception as e:
    p('DB_ERROR =', repr(e))
    DB_OK = False

# ---------- 2. 头像文件 ----------
AV = '9f2f80d5f40d4628b2a3e505f94f1a1d.jpg'
fp = os.path.join(BASE, 'backend', 'static', 'upload', AV)
if os.path.isfile(fp):
    sz = os.path.getsize(fp)
    head = open(fp, 'rb').read(4)
    p('AVATAR_FILE = EXISTS size=%d jpeg=%s' % (sz, head[:2] == b'\xff\xd8'))
else:
    p('AVATAR_FILE = MISSING')

# ---------- 3. HTTP 双路 ----------
for host in ['127.0.0.1', '192.168.2.219']:
    url = 'http://%s:8080/static/upload/%s' % (host, AV)
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=6) as r:
            body = r.read()
            p('HTTP[%s] = status=%s ct=%s bytes=%d' % (host, r.status, r.headers.get('Content-Type'), len(body)))
    except Exception as e:
        p('HTTP[%s] = ERROR %r' % (host, e))

outdir = os.path.join(BASE, 'tests', 'security', '_out')
os.makedirs(outdir, exist_ok=True)
open(os.path.join(outdir, '_bug_final_verify.txt'), 'w', encoding='utf-8').write('\n'.join(OUT))
