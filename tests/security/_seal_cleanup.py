# -*- coding: utf-8 -*-
"""最终封板 · 历届测试残留精确清理。

用法：
  python _seal_cleanup.py plan     # 只读 dry-run，打印将删除的每一行
  python _seal_cleanup.py apply    # 备份后执行删除

五重守卫（任一不满足 ⇒ 该行跳过并计入 UNCONFIRMED）：
  G1 待删 id 必须在 SEAL_BASELINE.json 的 whitelist 内
  G2 待删 id 不得命中硬编码受保护白名单
  G3 账号行特征必须仍匹配 api_test 判定规则（防基线后数据被改）
  G4 业务行/关系行必须「user_id ∈ test_users」（测试数据必属测试用户）
  G5 若 user_id ∉ test_users 但 doctor_id/coach_id ∈ 测试集 ⇒ 标 UNCONFIRMED，绝不删

只删本脚本判定为 CONFIRMED 的行；admin_operation_log 一律不动。
"""
import io
import os
import re
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _sec_lib import q, q1, conn, PROJECT      # noqa: E402

OUT = os.path.join(PROJECT, 'tests', 'security', '_out')
BASE_F = os.path.join(OUT, 'SEAL_BASELINE.json')

PROTECTED = {'users': [1, 2, 12, 13], 'doctor_user': [1, 2, 3], 'coach_user': [1, 2, 3]}
PROTECTED_NAMES = {
    'doctor_user': ['doctor001', 'doctor002', 'doctor003'],
    'coach_user': ['coach001', 'coach002', 'coach003'],
}
WINDOW = ('2026-10-01 00:00:00', '2026-10-02 23:59:59')

# 删除顺序：先关系 → 再带外键的业务 → 再纯 user 业务 → 最后账号
ORDER_BIZ_FK = [('doctor_advice', 'doctor_id'), ('medical_notice', 'doctor_id'),
                ('medical_record', 'doctor_id'), ('sport_goal', 'coach_id'),
                ('training_plan', 'coach_id'), ('fitness_advice', 'coach_id')]
ORDER_BIZ_U = ['health_record', 'sleep_record', 'sport_record', 'health_plan']
ORDER_REL = ['doctor_patient', 'coach_student']
ORDER_ACC = ['doctor_user', 'coach_user', 'users']


def load_base():
    return json.load(io.open(BASE_F, encoding='utf-8'))


def check_account_row(table, r):
    """G2/G3：账号行是否仍满足判定规则。"""
    if r['id'] in PROTECTED.get(table, []):
        return False, 'G2_HITS_PROTECTED_WHITELIST'
    name = r.get('doctor_name') or r.get('coach_name') or r.get('nickname') or ''
    if table == 'doctor_user':
        if name in PROTECTED_NAMES['doctor_user']:
            return False, 'G2_HITS_PROTECTED_NAME'
        if not re.match(r'^doc_(test|reject|other)_\d{10}$', name):
            return False, 'G3_NAME_PATTERN_CHANGED'
        if not re.fullmatch(r'1(37|35|33)908\d{5}', r.get('phone') or ''):
            return False, 'G3_PHONE_PATTERN_CHANGED'
    elif table == 'coach_user':
        if name in PROTECTED_NAMES['coach_user']:
            return False, 'G2_HITS_PROTECTED_NAME'
        if not re.match(r'^coach_(test|reject)_\d{10}$', name):
            return False, 'G3_NAME_PATTERN_CHANGED'
        if not re.fullmatch(r'1(36|34)908\d{5}', r.get('phone') or ''):
            return False, 'G3_PHONE_PATTERN_CHANGED'
    elif table == 'users':
        if not re.fullmatch(r'1(39|38)908\d{5}', r.get('phone') or ''):
            return False, 'G3_PHONE_PATTERN_CHANGED'
        if name not in ('测试用户A改', '接口测试用户B'):
            return False, 'G3_NICKNAME_CHANGED'
    if not (WINDOW[0] <= str(r.get('created_at')) <= WINDOW[1]):
        return False, 'G3_CREATED_OUTSIDE_WINDOW'
    return True, ''


def build_plan():
    B = load_base()
    wl_u = set(B['whitelist']['users'])
    wl_d = set(B['whitelist']['doctor_user'])
    wl_c = set(B['whitelist']['coach_user'])
    plan = {'delete': {}, 'skipped': []}

    # ---- 账号 ----
    wl_map = {'users': wl_u, 'doctor_user': wl_d, 'coach_user': wl_c}
    acc_rows = {}
    for t, namecol in (('users', 'nickname'), ('doctor_user', 'doctor_name'), ('coach_user', 'coach_name')):
        rows = q('SELECT * FROM `%s` ORDER BY id' % t)
        keep = []
        for r in rows:
            if r['id'] not in wl_map[t]:
                continue
            ok, why = check_account_row(t, r)
            if ok:
                keep.append(r['id'])
            else:
                plan['skipped'].append({'table': t, 'id': r['id'], 'why': why})
        acc_rows[t] = keep
        plan['delete'][t] = keep

    # ---- 关系表 ----
    for t in ORDER_REL:
        pk = 'doctor_id' if t == 'doctor_patient' else 'coach_id'
        pkset = wl_d if t == 'doctor_patient' else wl_c
        rows = q('SELECT * FROM `%s`' % t)
        ids = []
        for r in rows:
            uid, pid = r['user_id'], r[pk]
            if uid in PROTECTED['users'] or pid in PROTECTED.get('doctor_user' if pk == 'doctor_id' else 'coach_user', []):
                continue                                  # 保护关系（含小周）
            if uid in wl_u and pid in pkset:
                ids.append(r['id'])
            elif pid in pkset and uid not in wl_u:
                plan['skipped'].append({'table': t, 'id': r['id'], 'why': 'G5_OWNER_NOT_TEST_USER',
                                        'user_id': uid, 'pid': pid})
        plan['delete'][t] = ids

    # ---- 业务表 ----
    for t, fk in ORDER_BIZ_FK + [(x, None) for x in ORDER_BIZ_U]:
        rows = q('SELECT * FROM `%s`' % t)
        ids = []
        for r in rows:
            uid = r.get('user_id')
            if uid in PROTECTED['users']:
                continue                                  # 小周/小林/阿may/小孙 一律保护
            if uid in wl_u:
                ids.append(r['id'])
            else:
                fkv = r.get(fk) if fk else None
                if fk and fkv in (wl_d if fk == 'doctor_id' else wl_c):
                    plan['skipped'].append({'table': t, 'id': r['id'], 'why': 'G5_OWNER_NOT_TEST_USER',
                                            'user_id': uid, fk: fkv})
        plan['delete'][t] = ids
    return plan, B


def ordered():
    return ORDER_REL + [x[0] for x in ORDER_BIZ_FK] + ORDER_BIZ_U + ORDER_ACC


def cmd_plan():
    plan, B = build_plan()
    print('=' * 78)
    print('DRY-RUN 删除计划（只读）')
    print('=' * 78)
    total = 0
    for t in ordered():
        ids = plan['delete'].get(t) or []
        total += len(ids)
        print('  %-18s 将删 %3d 行  ids=%s' % (t, len(ids), ids[:40]))
    print('-' * 78)
    print('  合计 =', total, '行')
    print('  跳过(UNCONFIRMED) =', len(plan['skipped']))
    for s in plan['skipped']:
        print('     ', s)
    with io.open(os.path.join(OUT, 'SEAL_DELETE_PLAN.json'), 'w', encoding='utf-8') as f:
        json.dump({'plan': plan['delete'], 'skipped': plan['skipped'], 'total': total},
                  f, ensure_ascii=False, indent=1, default=str)
    return total


def cmd_apply():
    plan, B = build_plan()
    # G1 二次校验：所有 id 必须来自白名单
    wl = {'users': set(B['whitelist']['users']), 'doctor_user': set(B['whitelist']['doctor_user']),
          'coach_user': set(B['whitelist']['coach_user'])}
    for t in ('users', 'doctor_user', 'coach_user'):
        bad = [i for i in plan['delete'][t] if i not in wl[t]]
        if bad:
            print('!! G1 FAILED', t, bad)
            return 1
    # 备份（剥离敏感列，避免 password_hash 落盘）
    SENSITIVE_COLS = {'password_hash', 'password', 'token'}
    backup = {}
    c = conn()
    try:
        with c.cursor() as cur:
            for t in ordered():
                ids = plan['delete'].get(t) or []
                if not ids:
                    backup[t] = []
                    continue
                cur.execute('SELECT * FROM `%s` WHERE id IN (%s)' % (t, ','.join(str(i) for i in ids)))
                backup[t] = [{k: v for k, v in row.items() if k not in SENSITIVE_COLS}
                             for row in cur.fetchall()]
    finally:
        c.close()
    with io.open(os.path.join(OUT, 'SEAL_DELETED_BACKUP.json'), 'w', encoding='utf-8') as f:
        json.dump(backup, f, ensure_ascii=False, indent=1, default=str)
    print('BACKUP rows:', {k: len(v) for k, v in backup.items()})

    # ---- 保护断言（删除前最后一道闸）：计划内任何行不得触碰受保护实体 ----
    viol = []
    for t, rows in backup.items():
        for r in rows:
            if t in PROTECTED and r.get('id') in PROTECTED[t]:
                viol.append({t: r.get('id'), 'why': 'ACCOUNT_ID_PROTECTED'})
            if r.get('user_id') in PROTECTED['users']:
                viol.append({t: r.get('id'), 'user_id': r.get('user_id'), 'why': 'USER_PROTECTED'})
            if r.get('doctor_id') in PROTECTED['doctor_user']:
                viol.append({t: r.get('id'), 'doctor_id': r.get('doctor_id'), 'why': 'DOCTOR_PROTECTED'})
            if r.get('coach_id') in PROTECTED['coach_user']:
                viol.append({t: r.get('id'), 'coach_id': r.get('coach_id'), 'why': 'COACH_PROTECTED'})
    if viol:
        print('!! PROTECTED ASSERTION FAILED，整批中止，未删除任何行：')
        for v in viol:
            print('   ', v)
        return 1
    print('PROTECTED_ASSERTION = OK（计划内 0 行触碰受保护实体）')

    # 执行删除
    c = conn()
    done = {}
    try:
        with c.cursor() as cur:
            for t in ordered():
                ids = plan['delete'].get(t) or []
                if not ids:
                    done[t] = 0
                    continue
                n = cur.execute('DELETE FROM `%s` WHERE id IN (%s)' % (t, ','.join(str(i) for i in ids)))
                done[t] = n
                print('   DELETED %-18s %d' % (t, n))
    finally:
        c.close()
    with io.open(os.path.join(OUT, 'SEAL_DELETE_RESULT.json'), 'w', encoding='utf-8') as f:
        json.dump({'deleted': done, 'skipped': plan['skipped'],
                   'total': sum(done.values())}, f, ensure_ascii=False, indent=1, default=str)
    print('TOTAL DELETED =', sum(done.values()))
    return 0


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'plan'
    if cmd == 'apply':
        sys.exit(cmd_apply())
    cmd_plan()
    sys.exit(0)
