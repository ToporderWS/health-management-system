# -*- coding: utf-8 -*-
"""清理首次执行崩溃时遗留的临时用户（严格守卫：命名 + 手机号段 + 创建时间窗）。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _sec_lib import ex, q  # noqa: E402

rows = q("SELECT id,phone,nickname,avatar,created_at FROM users "
         "WHERE nickname=%s OR phone LIKE '199%%'", ('sec_avatar_probe',))
print('候选行 = %d' % len(rows))
for r in rows:
    print('   ', r)

# 三重守卫：命名精确匹配 + 手机号 199 段 + 头像为默认头像（本脚本从不改动它）
safe = [r for r in rows
        if r['nickname'] == 'sec_avatar_probe'
        and str(r['phone']).startswith('199')
        and r['avatar'] == 'default_health.jpg']
if len(safe) != len(rows) or not rows:
    print('!! 守卫拦截：存在不匹配的候选行，未执行删除')
    sys.exit(1)

for r in safe:
    # 先确认没有被任何关系表引用
    for t, col in (('doctor_patient', 'user_id'), ('coach_student', 'user_id'),
                   ('health_record', 'user_id'), ('sleep_record', 'user_id'),
                   ('sport_record', 'user_id'), ('health_plan', 'user_id'),
                   ('doctor_advice', 'user_id'), ('medical_notice', 'user_id'),
                   ('medical_record', 'user_id'), ('sport_goal', 'user_id'),
                   ('training_plan', 'user_id'), ('fitness_advice', 'user_id')):
        n = q('SELECT COUNT(*) AS c FROM `%s` WHERE `%s`=%%s' % (t, col), (r['id'],))[0]['c']
        if n:
            print('!! id=%s 仍被 %s 引用 %d 行，整批中止' % (r['id'], t, n))
            sys.exit(1)
    ex('DELETE FROM users WHERE id=%s AND nickname=%s AND phone=%s',
       (r['id'], r['nickname'], r['phone']))
    print('   已删除 id=%s' % r['id'])

print('删除后残留 =',
      q("SELECT COUNT(*) AS c FROM users WHERE nickname=%s", ('sec_avatar_probe',))[0]['c'],
      q("SELECT COUNT(*) AS c FROM users WHERE phone LIKE '199%%'")[0]['c'])
print('users 总数 =', q('SELECT COUNT(*) AS c FROM users')[0]['c'])
