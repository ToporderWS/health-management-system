# -*- coding: utf-8 -*-
"""最终封板 · 补充只读侦察 2：内容表残留 + 外键引用面 + 审计日志。"""
import io
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _sec_lib import q, q1, PROJECT      # noqa: E402

OUT = os.path.join(PROJECT, 'tests', 'security', '_out')
BUF = []


def p(*args):
    s = ' '.join(str(a) for a in args)
    BUF.append(s)
    print(s, flush=True)


def cols(t):
    return [r['COLUMN_NAME'] for r in q(
        """SELECT COLUMN_NAME FROM information_schema.COLUMNS
           WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s ORDER BY ORDINAL_POSITION""", (t,))]


def main():
    p('=' * 78)
    p('最终封板 · 补充只读侦察 2')
    p('=' * 78)

    # 1) 内容表
    for t in ('health_article', 'notice'):
        cs = cols(t)
        show = [x for x in ('id', 'title', 'is_show', 'created_at') if x in cs]
        rows = q('SELECT %s FROM `%s` ORDER BY id' % (','.join('`%s`' % x for x in show), t))
        p('\n## health_article/notice -> %s 共 %d 行 (列:%s)' % (t, len(rows), ','.join(show)))
        p('   全列:', ','.join(cs))
        for r in rows:
            p('   ', ' | '.join('%s=%s' % (k, r.get(k)) for k in show))

    # 2) 各表外键列清单
    p('\n## 各表含 *_id 的列')
    tabs = sorted(list(r.values())[0] for r in q('SHOW TABLES'))
    for t in tabs:
        idc = [c for c in cols(t) if c.endswith('_id')]
        if idc:
            p('   %-20s %s' % (t, ','.join(idc)))

    # 3) 测试实体被引用面（不删，仅统计）
    p('\n## 测试实体被引用统计')
    test_users = [r['id'] for r in q("SELECT id FROM users WHERE nickname IN ('测试用户A改','接口测试用户B')")]
    test_docs = [r['id'] for r in q("SELECT id FROM doctor_user WHERE doctor_name LIKE 'doc\\_%%'")]
    test_coaches = [r['id'] for r in q("SELECT id FROM coach_user WHERE coach_name LIKE 'coach\\_%%'")]
    p('   测试 users ids   =', test_users)
    p('   测试 doctor ids  =', test_docs)
    p('   测试 coach ids   =', test_coaches)

    def inlist(v):
        return ','.join(str(x) for x in v) or '0'

    sets = {'users': test_users, 'doctor_user': test_docs, 'coach_user': test_coaches}
    for t in tabs:
        cs = cols(t)
        parts = []
        for c in cs:
            if not c.endswith('_id') or c == 'id':
                continue
            for kind, ids in sets.items():
                try:
                    n = q1('SELECT COUNT(*) AS n FROM `%s` WHERE `%s` IN (%s)' % (t, c, inlist(ids)))['n']
                except Exception:
                    continue
                if n:
                    parts.append('%s~%s=%s' % (c, kind, n))
        if parts:
            p('   %-20s %s' % (t, '; '.join(parts)))

    # 4) admin_operation_log
    cs = cols('admin_operation_log')
    p('\n## admin_operation_log 列:', ','.join(cs))
    p('   总数 =', q1('SELECT COUNT(*) AS n FROM admin_operation_log')['n'])
    if 'target_id' in cs:
        p('   target_id 分布前 20:',
          ', '.join('%s=%s' % (r['target_id'], r['n']) for r in q(
              'SELECT target_id,COUNT(*) AS n FROM admin_operation_log GROUP BY target_id ORDER BY n DESC LIMIT 20')))

    # 5) 孤儿检测（只读）
    p('\n## 孤儿检测（只读）')
    orph_dp = q("""SELECT dp.doctor_id, dp.user_id FROM doctor_patient dp
                   LEFT JOIN doctor_user d ON d.id=dp.doctor_id
                   LEFT JOIN users u ON u.id=dp.user_id
                   WHERE d.id IS NULL OR u.id IS NULL""")
    p('   孤儿 doctor_patient =', len(orph_dp), orph_dp[:10])
    orph_cs = q("""SELECT cs.coach_id, cs.user_id FROM coach_student cs
                   LEFT JOIN coach_user c ON c.id=cs.coach_id
                   LEFT JOIN users u ON u.id=cs.user_id
                   WHERE c.id IS NULL OR u.id IS NULL""")
    p('   孤儿 coach_student =', len(orph_cs), orph_cs[:10])
    for t in ('health_record', 'sleep_record', 'sport_record', 'health_plan',
              'doctor_advice', 'medical_notice', 'medical_record',
              'sport_goal', 'training_plan', 'fitness_advice'):
        orph = q('SELECT COUNT(*) AS n FROM `%s` x LEFT JOIN users u ON u.id=x.user_id WHERE u.id IS NULL' % t)
        n = orph[0]['n'] if orph else 0
        if n:
            p('   孤儿 %s = %s' % (t, n))

    path = os.path.join(OUT, '_seal_recon2.txt')
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(BUF))
    print('\n>>> WRITTEN', path)


if __name__ == '__main__':
    main()
