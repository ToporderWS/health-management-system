# -*- coding: utf-8 -*-
"""最终封板 · 删除前保护基线 + 残留身份判定（只读，不写数据库）。

产出：
  _out/SEAL_BASELINE.json   保护实体快照 + 19 表计数 + 结构指纹 + 残留白名单
  _out/SEAL_VERDICT.json    每条残留候选的 CONFIRMED / UNCONFIRMED + 证据
"""
import io
import os
import re
import sys
import json
import hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _sec_lib import q, q1, PROJECT      # noqa: E402

OUT = os.path.join(PROJECT, 'tests', 'security', '_out')
os.makedirs(OUT, exist_ok=True)

# ---------------- 受保护白名单（硬编码，任一命中即整批中止） ----------------
PROTECTED = {
    'users': [1, 2, 12, 13],
    'doctor_user': [1, 2, 3],
    'coach_user': [1, 2, 3],
    'admin_user': [1],
}
PROTECTED_NAMES = {
    'doctor_user': ['doctor001', 'doctor002', 'doctor003'],
    'coach_user': ['coach001', 'coach002', 'coach003'],
}

BIZ = ['health_record', 'sleep_record', 'sport_record', 'health_plan',
       'doctor_advice', 'medical_notice', 'medical_record',
       'sport_goal', 'training_plan', 'fitness_advice']

# api_test 运行窗口（历届残留创建时间）
WINDOW = ('2026-10-01 00:00:00', '2026-10-02 23:59:59')


def cols(t):
    return [r['COLUMN_NAME'] for r in q(
        """SELECT COLUMN_NAME FROM information_schema.COLUMNS
           WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s ORDER BY ORDINAL_POSITION""", (t,))]


def schema_fingerprint():
    tabs = sorted(list(r.values())[0] for r in q('SHOW TABLES'))
    rows = []
    for t in tabs:
        for c in q("""SELECT COLUMN_NAME,COLUMN_TYPE,IS_NULLABLE,COLUMN_KEY,COLUMN_DEFAULT,EXTRA
                      FROM information_schema.COLUMNS
                      WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s ORDER BY ORDINAL_POSITION""", (t,)):
            rows.append('%s.%s|%s|%s|%s|%s|%s' % (t, c['COLUMN_NAME'], c['COLUMN_TYPE'],
                                                  c['IS_NULLABLE'], c['COLUMN_KEY'],
                                                  c['COLUMN_DEFAULT'], c['EXTRA']))
    return tabs, rows, hashlib.sha256('\n'.join(sorted(rows)).encode('utf-8')).hexdigest()


def verdict():
    """逐条判定残留候选。多重独立证据交叉。"""
    out = {'confirmed': {}, 'unconfirmed': {}, 'evidence': []}

    # --- users ---
    u_rows = q('SELECT id,nickname,phone,gender,age,created_at FROM users ORDER BY id')
    conf_u, unconf_u = [], []
    for r in u_rows:
        i = r['id']
        if i in PROTECTED['users']:
            out['evidence'].append({'table': 'users', 'id': i, 'verdict': 'PROTECTED',
                                    'why': '硬编码受保护白名单'})
            continue
        nick_ok = r['nickname'] in ('测试用户A改', '接口测试用户B')
        phone_ok = bool(re.fullmatch(r'1(39|38)908\d{5}', r['phone'] or ''))
        name_ok = r['nickname'] in ('接口测试用户A', '测试用户A改', '接口测试用户B', '重复手机号')
        time_ok = WINDOW[0] <= str(r['created_at']) <= WINDOW[1]
        # 复刻 api_test 注册后 update_info 的年龄/性别
        profile_ok = (r['age'] == 30 and r['gender'] == '女') or (r['age'] is None and r['gender'] is None)
        ok = bool(nick_ok and phone_ok and time_ok)
        (conf_u if ok else unconf_u).append(r)
        out['evidence'].append({'table': 'users', 'id': i, 'nickname': r['nickname'],
                                'phone': r['phone'], 'created_at': str(r['created_at']),
                                'verdict': 'CONFIRMED' if ok else 'UNCONFIRMED',
                                'checks': {'nickname_match': nick_ok, 'phone_pattern': phone_ok,
                                           'created_in_apitest_window': time_ok,
                                           'profile_shape': profile_ok}})
    out['confirmed']['users'] = conf_u
    out['unconfirmed']['users'] = unconf_u

    # --- doctor_user ---
    d_rows = q('SELECT id,doctor_name,real_name,phone,audit_status,created_at FROM doctor_user ORDER BY id')
    conf_d, unconf_d = [], []
    for r in d_rows:
        i = r['id']
        if i in PROTECTED['doctor_user'] or r['doctor_name'] in PROTECTED_NAMES['doctor_user']:
            out['evidence'].append({'table': 'doctor_user', 'id': i, 'verdict': 'PROTECTED',
                                    'why': '硬编码受保护白名单/名称'})
            continue
        name_ok = bool(re.match(r'^doc_(test|reject|other)_\d{10}$', r['doctor_name'] or ''))
        real_ok = r['real_name'] in ('接口测试医生', '接口测试医生改', '待拒绝医生', '另一名医生')
        phone_ok = bool(re.fullmatch(r'1(37|35|33)908\d{5}', r['phone'] or ''))
        time_ok = WINDOW[0] <= str(r['created_at']) <= WINDOW[1]
        ok = bool(name_ok and phone_ok and time_ok)
        (conf_d if ok else unconf_d).append(r)
        out['evidence'].append({'table': 'doctor_user', 'id': i, 'doctor_name': r['doctor_name'],
                                'real_name': r['real_name'], 'phone': r['phone'],
                                'created_at': str(r['created_at']),
                                'verdict': 'CONFIRMED' if ok else 'UNCONFIRMED',
                                'checks': {'name_pattern': name_ok, 'real_name_match': real_ok,
                                           'phone_pattern': phone_ok, 'created_in_apitest_window': time_ok}})
    out['confirmed']['doctor_user'] = conf_d
    out['unconfirmed']['doctor_user'] = unconf_d

    # --- coach_user ---
    c_rows = q('SELECT id,coach_name,real_name,phone,audit_status,created_at FROM coach_user ORDER BY id')
    conf_c, unconf_c = [], []
    for r in c_rows:
        i = r['id']
        if i in PROTECTED['coach_user'] or r['coach_name'] in PROTECTED_NAMES['coach_user']:
            out['evidence'].append({'table': 'coach_user', 'id': i, 'verdict': 'PROTECTED',
                                    'why': '硬编码受保护白名单/名称'})
            continue
        name_ok = bool(re.match(r'^coach_(test|reject)_\d{10}$', r['coach_name'] or ''))
        real_ok = r['real_name'] in ('接口测试教练', '待拒绝教练')
        phone_ok = bool(re.fullmatch(r'1(36|34)908\d{5}', r['phone'] or ''))
        time_ok = WINDOW[0] <= str(r['created_at']) <= WINDOW[1]
        ok = bool(name_ok and phone_ok and time_ok)
        (conf_c if ok else unconf_c).append(r)
        out['evidence'].append({'table': 'coach_user', 'id': i, 'coach_name': r['coach_name'],
                                'real_name': r['real_name'], 'phone': r['phone'],
                                'created_at': str(r['created_at']),
                                'verdict': 'CONFIRMED' if ok else 'UNCONFIRMED',
                                'checks': {'name_pattern': name_ok, 'real_name_match': real_ok,
                                           'phone_pattern': phone_ok, 'created_in_apitest_window': time_ok}})
    out['confirmed']['coach_user'] = conf_c
    out['unconfirmed']['coach_user'] = unconf_c

    return out


def main():
    tabs, rows, fp = schema_fingerprint()
    base = {
        'ts': __import__('time').strftime('%Y-%m-%d %H:%M:%S'),
        'tables': tabs,
        'table_count': len(tabs),
        'schema_fingerprint': fp,
        'schema_columns': len(rows),
        'counts': {}, 'protected': {}, 'whitelist': {},
    }
    for t in tabs:
        base['counts'][t] = q1('SELECT COUNT(*) AS n FROM `%s`' % t)['n']

    base['protected'] = {
        'users': q('SELECT id,nickname,phone,gender,age FROM users WHERE id IN (1,2,12,13) ORDER BY id'),
        'doctors': q("SELECT id,doctor_name,real_name,audit_status FROM doctor_user WHERE doctor_name IN ('doctor001','doctor002','doctor003') ORDER BY id"),
        'coaches': q("SELECT id,coach_name,real_name,audit_status FROM coach_user WHERE coach_name IN ('coach001','coach002','coach003') ORDER BY id"),
        'xiaozhou_doctors': q('SELECT doctor_id,user_id FROM doctor_patient WHERE user_id=13'),
        'xiaozhou_coaches': q('SELECT coach_id,user_id FROM coach_student WHERE user_id=13'),
        'xiaozhou_biz': {},
    }
    for t in BIZ:
        base['protected']['xiaozhou_biz'][t] = q1('SELECT COUNT(*) AS n FROM `%s` WHERE user_id=13' % t)['n']
    # 小周业务数据逐行 id（用于删除后逐行校验）
    base['protected']['xiaozhou_biz_ids'] = {}
    for t in BIZ:
        base['protected']['xiaozhou_biz_ids'][t] = [r['id'] for r in
                                                    q('SELECT id FROM `%s` WHERE user_id=13 ORDER BY id' % t)]

    v = verdict()
    with io.open(os.path.join(OUT, 'SEAL_VERDICT.json'), 'w', encoding='utf-8') as f:
        json.dump(v, f, ensure_ascii=False, indent=1, default=str)

    base['whitelist'] = {
        'users': [r['id'] for r in v['confirmed']['users']],
        'doctor_user': [r['id'] for r in v['confirmed']['doctor_user']],
        'coach_user': [r['id'] for r in v['confirmed']['coach_user']],
    }
    base['unconfirmed_retained'] = {
        'users': [{'id': r['id'], 'name': r['nickname']} for r in v['unconfirmed']['users']],
        'doctor_user': [{'id': r['id'], 'name': r['doctor_name']} for r in v['unconfirmed']['doctor_user']],
        'coach_user': [{'id': r['id'], 'name': r['coach_name']} for r in v['unconfirmed']['coach_user']],
    }

    with io.open(os.path.join(OUT, 'SEAL_BASELINE.json'), 'w', encoding='utf-8') as f:
        json.dump(base, f, ensure_ascii=False, indent=1, default=str)

    print('== 保护基线 ==')
    print('  表数 =', base['table_count'], ' 列数 =', base['schema_columns'])
    print('  结构指纹 =', fp)
    print('  受保护 users =', [r['id'] for r in base['protected']['users']])
    print('  小周↔医生绑定 =', base['protected']['xiaozhou_doctors'])
    print('  小周↔教练绑定 =', base['protected']['xiaozhou_coaches'])
    print('  小周业务 =', base['protected']['xiaozhou_biz'])
    print()
    print('== 残留判定 ==')
    print('  CONFIRMED users   =', base['whitelist']['users'])
    print('  CONFIRMED doctor  =', base['whitelist']['doctor_user'])
    print('  CONFIRMED coach   =', base['whitelist']['coach_user'])
    print('  UNCONFIRMED       =', json.dumps(base['unconfirmed_retained'], ensure_ascii=False))


if __name__ == '__main__':
    main()
