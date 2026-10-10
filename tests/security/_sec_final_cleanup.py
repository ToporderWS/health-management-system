# -*- coding: utf-8 -*-
"""收尾清理：删除本轮验收产生的临时数据。

两类目标：
  (1) sec_ 前缀实体 —— 本轮权限/异常专项自建（_sec_data.targets 精确匹配）；
  (2) api_test.py 本轮回归残留 —— 18:15 / 18:17 两轮，id 白名单 + 手机号/名称守卫。

安全约束：
  - 只用精确 IN 匹配，绝不用 LIKE 模糊匹配；
  - 每个候选行必须先通过守卫校验，任一不匹配则整批中止（一个都不删）；
  - 不动「小林同学/阿may/小孙/小周」与 doctor001-003 / coach001-003 及其绑定关系；
  - 默认 dry-run，需显式 --apply 才执行。

用法： python _sec_final_cleanup.py [--apply]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _sec_data import cleanup as sec_cleanup          # noqa: E402
from _sec_lib import q, ex                            # noqa: E402

# ---- api_test.py 本轮残留：显式 id 白名单（已由盘点核实） ----
API_USERS = [26, 27, 28, 29]
API_DOCTORS = [38, 39, 40, 41, 42, 43]
API_COACHES = [28, 29, 30, 31]

# 期望特征（守卫用）：手机号前缀 + 昵称/名称关键字
USER_PHONE_PREFIX = ('139', '138')
USER_NICK_KEYS = ('测试用户A', '接口测试用户B')
DOC_NAME_PREFIX = ('doc_test_', 'doc_reject_', 'doc_other_')
COACH_NAME_PREFIX = ('coach_test_', 'coach_reject_')

# 严禁触碰的既有实体（出现即中止）
PROTECTED_USER_IDS = {1, 2, 12, 13}
PROTECTED_DOCTOR_IDS = {1, 2, 3}
PROTECTED_COACH_IDS = {1, 2, 3}


def _ph(n):
    return ','.join(['%s'] * n)


def guard():
    """返回 (ok, 问题列表)。任何问题 ⇒ 整批中止。"""
    problems = []

    us = q('SELECT id, phone, nickname FROM users WHERE id IN (%s)' % _ph(len(API_USERS)),
           API_USERS)
    for r in us:
        if r['id'] in PROTECTED_USER_IDS:
            problems.append('users id=%s 属受保护实体' % r['id'])
        if not str(r['phone']).startswith(USER_PHONE_PREFIX):
            problems.append('users id=%s phone=%s 前缀异常' % (r['id'], r['phone']))
        if not any(k in (r['nickname'] or '') for k in USER_NICK_KEYS):
            problems.append('users id=%s nickname=%s 非 api_test 命名' % (r['id'], r['nickname']))

    ds = q('SELECT id, doctor_name FROM doctor_user WHERE id IN (%s)'
           % _ph(len(API_DOCTORS)), API_DOCTORS)
    for r in ds:
        if r['id'] in PROTECTED_DOCTOR_IDS:
            problems.append('doctor_user id=%s 属受保护实体' % r['id'])
        if not str(r['doctor_name']).startswith(DOC_NAME_PREFIX):
            problems.append('doctor_user id=%s name=%s 非 api_test 命名'
                            % (r['id'], r['doctor_name']))

    cs = q('SELECT id, coach_name FROM coach_user WHERE id IN (%s)'
           % _ph(len(API_COACHES)), API_COACHES)
    for r in cs:
        if r['id'] in PROTECTED_COACH_IDS:
            problems.append('coach_user id=%s 属受保护实体' % r['id'])
        if not str(r['coach_name']).startswith(COACH_NAME_PREFIX):
            problems.append('coach_user id=%s name=%s 非 api_test 命名'
                            % (r['id'], r['coach_name']))
    return not problems, problems


def api_plan():
    """生成 api_test 残留的删除计划（子表 -> 父表）。"""
    plan = []
    if API_USERS:
        ph = _ph(len(API_USERS))
        for tbl in ('health_record', 'sleep_record', 'sport_record', 'health_plan',
                    'doctor_advice', 'medical_notice', 'medical_record',
                    'sport_goal', 'training_plan', 'fitness_advice'):
            plan.append((tbl, 'DELETE FROM %s WHERE user_id IN (%s)' % (tbl, ph), API_USERS))
        plan.append(('doctor_patient',
                     'DELETE FROM doctor_patient WHERE user_id IN (%s)' % ph, API_USERS))
        plan.append(('coach_student',
                     'DELETE FROM coach_student WHERE user_id IN (%s)' % ph, API_USERS))
    if API_DOCTORS:
        ph = _ph(len(API_DOCTORS))
        for tbl in ('doctor_advice', 'medical_notice', 'medical_record'):
            plan.append((tbl, 'DELETE FROM %s WHERE doctor_id IN (%s)' % (tbl, ph), API_DOCTORS))
        plan.append(('doctor_patient',
                     'DELETE FROM doctor_patient WHERE doctor_id IN (%s)' % ph, API_DOCTORS))
        plan.append(('doctor_user',
                     'DELETE FROM doctor_user WHERE id IN (%s)' % ph, API_DOCTORS))
    if API_COACHES:
        ph = _ph(len(API_COACHES))
        for tbl in ('sport_goal', 'training_plan', 'fitness_advice'):
            plan.append((tbl, 'DELETE FROM %s WHERE coach_id IN (%s)' % (tbl, ph), API_COACHES))
        plan.append(('coach_student',
                     'DELETE FROM coach_student WHERE coach_id IN (%s)' % ph, API_COACHES))
        plan.append(('coach_user',
                     'DELETE FROM coach_user WHERE id IN (%s)' % ph, API_COACHES))
    if API_USERS:
        plan.append(('users', 'DELETE FROM users WHERE id IN (%s)' % _ph(len(API_USERS)),
                     API_USERS))
    return plan


def main():
    apply_ = '--apply' in sys.argv
    print('################ 收尾清理 (%s) ################' % ('实际执行' if apply_ else 'DRY-RUN'))

    print('\n########## 阶段 1：sec_ 前缀实体 ##########')
    if apply_:
        sec_cleanup(dry_run=False)
    else:
        sec_cleanup(dry_run=True)

    print('\n########## 阶段 2：api_test.py 本轮残留 ##########')
    print('  目标: users=%s doctors=%s coaches=%s' % (API_USERS, API_DOCTORS, API_COACHES))
    ok, problems = guard()
    if not ok:
        print('  !! 守卫未通过，整批中止，未删除任何 api_test 数据：')
        for p in problems:
            print('     - %s' % p)
    else:
        print('  守卫通过（id 白名单 + 手机号前缀 + 命名关键字 全部匹配）')
        plan = api_plan()
        if not apply_:
            for table, sql, _a in plan:
                print('  [dry-run] %s' % sql)
        else:
            counts = {}
            for table, sql, args in plan:
                n = ex(sql, args)
                counts[table] = counts.get(table, 0) + n
            print('  已删除: %s' % counts)

    print('\n########## 清理后剩余实体 ##########')
    print('  users      : %s' % q('SELECT COUNT(*) n FROM users')[0]['n'])
    print('  doctor_user: %s' % q('SELECT COUNT(*) n FROM doctor_user')[0]['n'])
    print('  coach_user : %s' % q('SELECT COUNT(*) n FROM coach_user')[0]['n'])
    print('  受保护实体抽查:')
    for uid in sorted(PROTECTED_USER_IDS):
        r = q('SELECT id, nickname FROM users WHERE id=%s', (uid,))
        print('    users id=%s -> %s' % (uid, (r[0]['nickname'] if r else '已不存在!!')))
    for did in sorted(PROTECTED_DOCTOR_IDS):
        r = q('SELECT id, doctor_name FROM doctor_user WHERE id=%s', (did,))
        print('    doctor id=%s -> %s' % (did, (r[0]['doctor_name'] if r else '已不存在!!')))
    for cid in sorted(PROTECTED_COACH_IDS):
        r = q('SELECT id, coach_name FROM coach_user WHERE id=%s', (cid,))
        print('    coach id=%s -> %s' % (cid, (r[0]['coach_name'] if r else '已不存在!!')))
    print('  小周(user 13) 绑定: doctor_patient=%s coach_student=%s' % (
        q('SELECT doctor_id FROM doctor_patient WHERE user_id=13'),
        q('SELECT coach_id FROM coach_student WHERE user_id=13')))


if __name__ == '__main__':
    main()
