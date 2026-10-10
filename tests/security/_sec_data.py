# -*- coding: utf-8 -*-
"""专项验收 · 测试数据定义与安全清理。

安全红线：
- 只操作 sec_ 前缀 / 指定测试手机号的数据；全部使用精确 IN 匹配，绝不用模糊 LIKE 误伤；
- 绝不动「小周」「doctor001 / coach001 / doctor003 / coach003」等既有数据；
- 清理按「子表 -> 父表」顺序执行。
"""
from _sec_lib import ex, q

# ---------------- 测试实体标识（全部带 sec 前缀） ----------------
PWD = 'sec123456'

SEC_USERS = [
    ('sec_user_a', '19900000001', '男', 30, 175.0),
    ('sec_user_b', '19900000002', '女', 28, 165.0),
]
SEC_DOCTORS = [
    ('sec_doctor_a', '19900000101', '测试医生A', '男', '全科'),
    ('sec_doctor_b', '19900000102', '测试医生B', '女', '骨科'),
]
SEC_COACHES = [
    ('sec_coach_a', '19900000201', '测试教练A', '男', '增肌'),
    ('sec_coach_b', '19900000202', '测试教练B', '女', '减脂'),
]

# D/E 专项临时实体（独立，避免与 B/C 互相干扰）
SEC_EXTRA = {
    'doctor_pending': ('sec_audit_doctor_pending', '19900000301'),
    'doctor_evil': ('sec_audit_doctor_evil', '19900000302'),
    'coach_pending': ('sec_audit_coach_pending', '19900000303'),
    'coach_evil': ('sec_audit_coach_evil', '19900000304'),
    'doctor_ok': ('sec_audit_doctor_ok', '19900000305'),
    'coach_ok': ('sec_audit_coach_ok', '19900000306'),
    'user_dup': ('sec_user_dup', '19900000003'),
}

USER_PHONES = tuple(p for _, p, _, _, _ in SEC_USERS) + tuple(
    v[1] for v in SEC_EXTRA.values())
DOCTOR_NAMES = tuple(n for n, _, _, _, _ in SEC_DOCTORS) + tuple(
    v[0] for k, v in SEC_EXTRA.items() if k.startswith('doctor'))
COACH_NAMES = tuple(n for n, _, _, _, _ in SEC_COACHES) + tuple(
    v[0] for k, v in SEC_EXTRA.items() if k.startswith('coach'))


def _ph(n):
    return ','.join(['%s'] * n)


def targets():
    """返回本轮测试实体的 id 集合（只认 sec 前缀 + 专用手机号/账号名）。"""
    t = {}
    t['users'] = [r['id'] for r in q(
        'SELECT id FROM users WHERE phone IN (%s)' % _ph(len(USER_PHONES)), USER_PHONES)]
    t['doctors'] = [r['id'] for r in q(
        'SELECT id FROM doctor_user WHERE doctor_name IN (%s)' % _ph(len(DOCTOR_NAMES)),
        DOCTOR_NAMES)]
    t['coaches'] = [r['id'] for r in q(
        'SELECT id FROM coach_user WHERE coach_name IN (%s)' % _ph(len(COACH_NAMES)),
        COACH_NAMES)]
    return t


def describe():
    t = targets()
    return '\n'.join('%s: %s' % (k, v or '（无）') for k, v in t.items())


def cleanup(dry_run=True):
    """删除本轮测试产生的全部业务数据。dry_run=True 只打印计划不删除。"""
    t = targets()
    uids, dids, cids = t['users'], t['doctors'], t['coaches']
    if not (uids or dids or cids):
        print('无需清理：未发现 sec_ 测试实体')
        return {}

    plan = []

    def add(table, sql, args):
        plan.append((table, sql, args))

    if uids:
        ph = _ph(len(uids))
        for tbl in ('health_record', 'sleep_record', 'sport_record', 'health_plan',
                    'doctor_advice', 'medical_notice', 'medical_record',
                    'sport_goal', 'training_plan', 'fitness_advice'):
            add(tbl, 'DELETE FROM %s WHERE user_id IN (%s)' % (tbl, ph), uids)
        add('doctor_patient', 'DELETE FROM doctor_patient WHERE user_id IN (%s)' % ph, uids)
        add('coach_student', 'DELETE FROM coach_student WHERE user_id IN (%s)' % ph, uids)
    if dids:
        ph = _ph(len(dids))
        for tbl in ('doctor_advice', 'medical_notice', 'medical_record'):
            add(tbl, 'DELETE FROM %s WHERE doctor_id IN (%s)' % (tbl, ph), dids)
        add('doctor_patient', 'DELETE FROM doctor_patient WHERE doctor_id IN (%s)' % ph, dids)
        add('doctor_user', 'DELETE FROM doctor_user WHERE id IN (%s)' % ph, dids)
    if cids:
        ph = _ph(len(cids))
        for tbl in ('sport_goal', 'training_plan', 'fitness_advice'):
            add(tbl, 'DELETE FROM %s WHERE coach_id IN (%s)' % (tbl, ph), cids)
        add('coach_student', 'DELETE FROM coach_student WHERE coach_id IN (%s)' % ph, cids)
        add('coach_user', 'DELETE FROM coach_user WHERE id IN (%s)' % ph, cids)
    if uids:
        add('users', 'DELETE FROM users WHERE id IN (%s)' % _ph(len(uids)), uids)

    print('  目标实体: users=%s doctors=%s coaches=%s' % (uids, dids, cids), flush=True)
    if dry_run:
        for table, sql, _a in plan:
            print('  [dry-run] %s' % sql, flush=True)
        return {}
    counts = {}
    for table, sql, args in plan:
        for _ in range(1):
            pass
        n = ex(sql, args)
        counts[table] = counts.get(table, 0) + n
    print('  已删除: %s' % counts, flush=True)
    return counts


if __name__ == '__main__':
    import sys
    apply_ = '--apply' in sys.argv
    print('== 当前 sec 测试实体 ==')
    print(describe())
    print('== 清理 (%s) ==' % ('实际执行' if apply_ else 'dry-run'))
    cleanup(dry_run=not apply_)
