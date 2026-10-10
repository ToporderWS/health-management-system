# -*- coding: utf-8 -*-
"""存量事项② JWT_SECRET 轮换 · 轮换前准备 / 轮换后清理。

子命令：
  baseline   -> 记录 DB 结构签名 + 表计数 + 受保护实体 + 三表 id 集合（只读）
  tokens     -> 用「当前（旧）Secret」登录四角色，落盘旧 Token（供轮换后 401 验证）
  idsnap     -> 记录 users/doctor_user/coach_user 当前 id 集合（api_test 前调用）
  idclean    -> 与 idsnap 求差集 = 本轮新增行；三重守卫通过后精确删除（--apply 才真删）
  structdiff -> 与 baseline 比对 DB 结构签名，输出 STRUCTURE_CHANGED = 0/非0

安全红线：一切删除都基于「id 差集 + 命名/手机号正则 + 受保护实体三重守卫」，
          任一不匹配整批中止；不清理 admin_operation_log；不改数据库结构。
"""
import hashlib
import io
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _sec_lib import OUT, post, q, conn  # noqa: E402

TABLES = ['users', 'doctor_user', 'coach_user', 'doctor_patient', 'coach_student',
          'health_record', 'sleep_record', 'sport_record', 'health_plan',
          'doctor_advice', 'medical_notice', 'medical_record',
          'sport_goal', 'training_plan', 'fitness_advice', 'admin_operation_log']

PROTECT_USERS = {1, 2, 12, 13}
PROTECT_DOCTORS = {1, 2, 3}
PROTECT_COACHES = {1, 2, 3}

# 本轮 api_test 命名/手机号指纹（跨轮次唯一，但删除只认 id 差集 + 指纹双重确认）
RE_APT_USER = re.compile(r'^13[3-9]\d{8}$')
RE_APT_DOCTOR = re.compile(r'^doc_(test|reject|other)_\d{8,14}$')
RE_APT_COACH = re.compile(r'^coach_(test|reject)_\d{8,14}$')

BASE = os.path.join(OUT, 'JWT_BASELINE.json')
IDSNAP = os.path.join(OUT, 'JWT_ID_SNAP.json')
OLDTOK = os.path.join(OUT, '_jwt_old_tokens.json')

CHILD_BY_USER = ['health_record', 'sleep_record', 'sport_record', 'health_plan',
                 'doctor_advice', 'medical_notice', 'medical_record',
                 'sport_goal', 'training_plan', 'fitness_advice',
                 'doctor_patient', 'coach_student']
BY_DOCTOR = [('doctor_advice', 'doctor_id'), ('medical_notice', 'doctor_id'),
             ('medical_record', 'doctor_id'), ('doctor_patient', 'doctor_id')]
BY_COACH = [('sport_goal', 'coach_id'), ('training_plan', 'coach_id'),
            ('fitness_advice', 'coach_id'), ('coach_student', 'coach_id')]


def _structure_signature():
    """用 information_schema 固化 16 张表的列结构，生成 SHA-256 指纹。"""
    rows = q("""SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY,
                       COLUMN_DEFAULT, EXTRA, ORDINAL_POSITION
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA='health_management'
                ORDER BY TABLE_NAME, ORDINAL_POSITION""")
    blob = json.dumps([{k: (str(v) if v is not None else None) for k, v in r.items()}
                       for r in rows], ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(blob.encode('utf-8')).hexdigest(), len(rows)


def _idsets():
    return {
        'users': sorted(r['id'] for r in q('SELECT id FROM users')),
        'doctor_user': sorted(r['id'] for r in q('SELECT id FROM doctor_user')),
        'coach_user': sorted(r['id'] for r in q('SELECT id FROM coach_user')),
    }


def _counts():
    out = {}
    for t in TABLES:
        try:
            out[t] = q('SELECT COUNT(*) AS n FROM `%s`' % t)[0]['n']
        except Exception as e:  # noqa: BLE001
            out[t] = 'ERR:%s' % e
    return out


def _protected():
    d = {}
    d['users'] = q('SELECT id,phone,nickname FROM users WHERE id IN (1,2,12,13)')
    d['doctors'] = q("SELECT id,doctor_name,audit_status FROM doctor_user "
                     "WHERE doctor_name IN ('doctor001','doctor002','doctor003')")
    d['coaches'] = q("SELECT id,coach_name,audit_status FROM coach_user "
                     "WHERE coach_name IN ('coach001','coach002','coach003')")
    d['xiaozhou_doctors'] = q('SELECT doctor_id,user_id FROM doctor_patient WHERE user_id=13')
    d['xiaozhou_coaches'] = q('SELECT coach_id,user_id FROM coach_student WHERE user_id=13')
    biz = {}
    for t in ['health_record', 'sleep_record', 'sport_record', 'health_plan',
              'doctor_advice', 'medical_notice', 'medical_record',
              'sport_goal', 'training_plan', 'fitness_advice']:
        biz[t] = q('SELECT COUNT(*) AS n FROM `%s` WHERE user_id=13' % t)[0]['n']
    d['xiaozhou_biz'] = biz
    return d


def cmd_baseline():
    sig, ncol = _structure_signature()
    data = {
        'ts': time.strftime('%Y-%m-%d %H:%M:%S'),
        'structure_sha256': sig,
        'structure_columns': ncol,
        'counts': _counts(),
        'idsets': _idsets(),
        'protected': _protected(),
        'autoincrement': {t: (q("SELECT AUTO_INCREMENT AS a FROM information_schema.TABLES "
                                "WHERE TABLE_SCHEMA='health_management' AND TABLE_NAME=%s", (t,))
                              or [{}])[0].get('a') for t in
                          ('users', 'doctor_user', 'coach_user')},
    }
    with io.open(BASE, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2, default=str))
    print('baseline written -> %s' % BASE)
    print('structure_sha256 =', sig, '(%d columns)' % ncol)
    print('counts =', json.dumps(data['counts'], ensure_ascii=False))
    print('idsets =', json.dumps({k: len(v) for k, v in data['idsets'].items()}))
    return 0


def cmd_tokens():
    plan = [
        ('user', '/user/login', {'phone': '19900000001', 'password': 'sec123456'}),
        ('doctor', '/doctor/login', {'doctor_name': 'sec_doctor_a', 'password': 'sec123456'}),
        ('coach', '/coach/login', {'coach_name': 'sec_coach_a', 'password': 'sec123456'}),
        ('admin', '/admin/login', {'admin_name': 'admin', 'password': '123456'}),
    ]
    toks = {}
    for kind, path, body in plan:
        r = post(path, body=body)
        tok = (r.get('data') or {}).get('token') if isinstance(r.get('data'), dict) else None
        toks[kind] = tok
        print('  %-7s http=%s token=%s' % (kind, r.get('status'),
                                           ('len=%d' % len(tok)) if tok else 'NONE'))
    if not all(toks.values()):
        print('!! 旧 Token 捕获失败，缺失:', [k for k, v in toks.items() if not v])
        return 3
    with io.open(OLDTOK, 'w', encoding='utf-8') as f:
        f.write(json.dumps(toks, ensure_ascii=False))
    print('old tokens saved -> %s (%d roles)' % (OLDTOK, len(toks)))
    return 0


def cmd_idsnap():
    data = _idsets()
    with io.open(IDSNAP, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2))
    print('idsnap =', json.dumps({k: len(v) for k, v in data.items()}))
    return 0


def cmd_structdiff():
    b = json.load(io.open(BASE, encoding='utf-8'))
    sig, ncol = _structure_signature()
    same_sig = (sig == b['structure_sha256'])
    same_cols = (ncol == b['structure_columns'])
    print('structure_sha256 now =', sig)
    print('structure columns now =', ncol)
    print('STRUCTURE_UNCHANGED =', 'YES' if (same_sig and same_cols) else 'NO')
    changed = 0 if (same_sig and same_cols) else 1
    print('DB_STRUCTURE_MODIFIED =', changed)
    return 0


def _diff_plan():
    snap = json.load(io.open(IDSNAP, encoding='utf-8'))
    now = _idsets()
    users = sorted(set(now['users']) - set(snap['users']))
    doctors = sorted(set(now['doctor_user']) - set(snap['doctor_user']))
    coaches = sorted(set(now['coach_user']) - set(snap['coach_user']))

    problems = []
    for uid in users:
        if uid in PROTECT_USERS:
            problems.append('!! 受保护 users id=%d 落入差集' % uid)
    for did in doctors:
        if did in PROTECT_DOCTORS:
            problems.append('!! 受保护 doctor_user id=%d 落入差集' % did)
    for cid in coaches:
        if cid in PROTECT_COACHES:
            problems.append('!! 受保护 coach_user id=%d 落入差集' % cid)

    detail = {}
    for uid in users:
        r = (q('SELECT id,phone,nickname FROM users WHERE id=%s', (uid,)) or [None])[0]
        detail['user:%d' % uid] = r
        if r and not RE_APT_USER.match(str(r['phone'])):
            problems.append('users id=%d 手机号未命中 api_test 指纹: %s' % (uid, r['phone']))
    for did in doctors:
        r = (q('SELECT id,doctor_name FROM doctor_user WHERE id=%s', (did,)) or [None])[0]
        detail['doctor:%d' % did] = r
        if r and not RE_APT_DOCTOR.match(str(r['doctor_name'])):
            problems.append('doctor_user id=%d 名称未命中 api_test 指纹: %s'
                            % (did, r['doctor_name']))
    for cid in coaches:
        r = (q('SELECT id,coach_name FROM coach_user WHERE id=%s', (cid,)) or [None])[0]
        detail['coach:%d' % cid] = r
        if r and not RE_APT_COACH.match(str(r['coach_name'])):
            problems.append('coach_user id=%d 名称未命中 api_test 指纹: %s'
                            % (cid, r['coach_name']))

    return {'users': users, 'doctors': doctors, 'coaches': coaches,
            'detail': detail, 'problems': problems, 'safe': not problems}


def cmd_idclean():
    p = _diff_plan()
    print(json.dumps(p, ensure_ascii=False, indent=2, default=str))
    if '--apply' not in sys.argv:
        print('\n[dry-run] SAFE =', p['safe'])
        return 0
    if not p['safe']:
        print('\n!! 守卫失败，整批中止（一个都不删）')
        return 2
    if not (p['users'] or p['doctors'] or p['coaches']):
        print('\n本轮无新增行，无需清理')
        return 0
    c = conn()
    cur = c.cursor()
    log = {}
    ids_u = ','.join(map(str, p['users'])) or 'NULL'
    ids_d = ','.join(map(str, p['doctors'])) or 'NULL'
    ids_c = ','.join(map(str, p['coaches'])) or 'NULL'
    for t in CHILD_BY_USER:
        cur.execute('DELETE FROM `%s` WHERE user_id IN (%s)' % (t, ids_u))
        log['%s(user_id)' % t] = cur.rowcount
    for t, col in BY_DOCTOR:
        cur.execute('DELETE FROM `%s` WHERE %s IN (%s)' % (t, col, ids_d))
        log['%s(%s)' % (t, col)] = cur.rowcount
    for t, col in BY_COACH:
        cur.execute('DELETE FROM `%s` WHERE %s IN (%s)' % (t, col, ids_c))
        log['%s(%s)' % (t, col)] = cur.rowcount
    cur.execute('DELETE FROM users WHERE id IN (%s)' % ids_u)
    log['users'] = cur.rowcount
    cur.execute('DELETE FROM doctor_user WHERE id IN (%s)' % ids_d)
    log['doctor_user'] = cur.rowcount
    cur.execute('DELETE FROM coach_user WHERE id IN (%s)' % ids_c)
    log['coach_user'] = cur.rowcount
    c.commit()
    c.close()
    print('\n== 清理执行明细 ==')
    for k in sorted(log):
        if log[k]:
            print('   %-30s %d' % (k, log[k]))
    print('   %-30s %d' % ('合计删除行数', sum(v for v in log.values() if isinstance(v, int))))
    return 0


CMDS = {'baseline': cmd_baseline, 'tokens': cmd_tokens, 'idsnap': cmd_idsnap,
        'idclean': cmd_idclean, 'structdiff': cmd_structdiff}

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'baseline'
    sys.exit(CMDS[cmd]())
