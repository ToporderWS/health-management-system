# -*- coding: utf-8 -*-
"""最终封板 · 只读侦察（不写任何数据）。

输出：
  1. 全部表清单 + 各表列结构指纹
  2. users / doctor_user / coach_user / admin_user 全量行
  3. doctor_patient / coach_student 全量关系
  4. 业务表按 user_id 聚合计数
  5. 历届 api_test 残留候选（按命名/手机号特征）
"""
import io
import os
import sys
import json
import hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _sec_lib import q, q1, PROJECT      # noqa: E402

OUT = os.path.join(PROJECT, 'tests', 'security', '_out')
os.makedirs(OUT, exist_ok=True)

BUF = []


def p(*args):
    s = ' '.join(str(a) for a in args)
    BUF.append(s)
    print(s, flush=True)


def dump(name):
    path = os.path.join(OUT, name)
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(BUF))
    print('\n>>> WRITTEN', path, len('\n'.join(BUF)), 'chars')


def cols(table):
    return q("""SELECT COLUMN_NAME,COLUMN_TYPE,IS_NULLABLE,COLUMN_KEY,COLUMN_DEFAULT
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s
                ORDER BY ORDINAL_POSITION""", (table,))


def main():
    p('=' * 78)
    p('最终封板 · 只读侦察  @', __import__('time').strftime('%Y-%m-%d %H:%M:%S'))
    p('=' * 78)

    # ---------- 1. 表清单 ----------
    tabs = sorted(list(r.values())[0] for r in q('SHOW TABLES'))
    p('\n## 1. 数据库表清单（共 %d 张）' % len(tabs))
    for t in tabs:
        p('   -', t)

    # ---------- 2. 结构指纹 ----------
    sig_rows = []
    for t in tabs:
        cs = cols(t)
        for c in cs:
            sig_rows.append('%s.%s|%s|%s|%s' % (
                t, c['COLUMN_NAME'], c['COLUMN_TYPE'], c['IS_NULLABLE'], c['COLUMN_KEY']))
    sig = hashlib.sha256('\n'.join(sorted(sig_rows)).encode('utf-8')).hexdigest()
    p('\n## 2. 结构指纹 SHOW: cols=%d  fingerprint=%s' % (len(sig_rows), sig))
    with io.open(os.path.join(OUT, 'SEAL_SCHEMA_FINGERPRINT.json'), 'w', encoding='utf-8') as f:
        json.dump({'tables': tabs, 'columns': sig_rows, 'fingerprint': sig,
                   'count': len(sig_rows)}, f, ensure_ascii=False, indent=1)

    # ---------- 3. 账号表全量 ----------
    for t, namecol in (('users', 'nickname'), ('doctor_user', 'doctor_name'),
                       ('coach_user', 'coach_name'), ('admin_user', 'admin_name')):
        cs = [c['COLUMN_NAME'] for c in cols(t)]
        show = [x for x in ('id', namecol, 'real_name', 'phone', 'gender', 'age',
                            'audit_status', 'created_at') if x in cs]
        rows = q('SELECT %s FROM `%s` ORDER BY id' % (','.join('`%s`' % x for x in show), t))
        p('\n## 3. %s  共 %d 行  (列: %s)' % (t, len(rows), ','.join(show)))
        for r in rows:
            p('   ', ' | '.join('%s=%s' % (k, r.get(k)) for k in show))

    # ---------- 4. 关系表 ----------
    for t, a, b in (('doctor_patient', 'doctor_id', 'user_id'),
                    ('coach_student', 'coach_id', 'user_id')):
        rows = q('SELECT %s,%s FROM `%s` ORDER BY %s,%s' % (a, b, t, a, b))
        p('\n## 4. %s  共 %d 行' % (t, len(rows)))
        for r in rows:
            p('   ', '%s=%s -> %s=%s' % (a, r[a], b, r[b]))

    # ---------- 5. 业务表按 user_id 聚合 ----------
    p('\n## 5. 业务表计数 + 按 user_id 聚合')
    biz = ['health_record', 'sleep_record', 'sport_record', 'health_plan',
           'doctor_advice', 'medical_notice', 'medical_record',
           'sport_goal', 'training_plan', 'fitness_advice']
    for t in biz:
        cs = [c['COLUMN_NAME'] for c in cols(t)]
        n = q1('SELECT COUNT(*) AS n FROM `%s`' % t)['n']
        p('   %-16s total=%s' % (t, n))
        if 'user_id' in cs:
            rows = q('SELECT user_id, COUNT(*) AS n FROM `%s` GROUP BY user_id ORDER BY user_id' % t)
            p('        by user_id:', ', '.join('u%s=%s' % (r['user_id'], r['n']) for r in rows) or '(空)')

    # ---------- 6. 历届残留候选 ----------
    p('\n## 6. 历届 api_test 残留候选（命名/手机号特征）')
    cands = {}
    cands['users_3_11'] = q("SELECT id,nickname,phone,created_at FROM users WHERE id BETWEEN 3 AND 11 ORDER BY id")
    cands['doctors_4_16'] = q("SELECT id,doctor_name,real_name,phone,audit_status,created_at FROM doctor_user WHERE id BETWEEN 4 AND 16 ORDER BY id")
    cands['coaches_4_11'] = q("SELECT id,coach_name,real_name,phone,audit_status,created_at FROM coach_user WHERE id BETWEEN 4 AND 11 ORDER BY id")
    for k, rows in cands.items():
        p('\n   [%s] %d 行' % (k, len(rows)))
        for r in rows:
            p('      ', ' | '.join('%s=%s' % (kk, vv) for kk, vv in r.items()))

    # 全库命名特征扫描
    p('\n## 6b. 全库按「测试命名特征」扫描')
    pat_doc = q("SELECT id,doctor_name,created_at FROM doctor_user WHERE doctor_name LIKE 'doc\\_%%' OR doctor_name LIKE 'sec%%' ORDER BY id")
    p('   doctor_user 命中 doc_/sec_: %d' % len(pat_doc))
    for r in pat_doc:
        p('      ', r['id'], r['doctor_name'], r['created_at'])
    pat_co = q("SELECT id,coach_name,created_at FROM coach_user WHERE coach_name LIKE 'coach\\_%%' OR coach_name LIKE 'sec%%' ORDER BY id")
    p('   coach_user 命中 coach_/sec_: %d' % len(pat_co))
    for r in pat_co:
        p('      ', r['id'], r['coach_name'], r['created_at'])
    pat_us = q("SELECT id,nickname,phone,created_at FROM users WHERE phone LIKE '139%%' OR phone LIKE '137%%' OR phone LIKE '136%%' OR phone LIKE '133%%' OR nickname LIKE 'sec%%' ORDER BY id")
    p('   users 命中测试手机号段/命名: %d' % len(pat_us))
    for r in pat_us:
        p('      ', r['id'], r['nickname'], r['phone'], r['created_at'])

    dump('_seal_recon.txt')


if __name__ == '__main__':
    main()
