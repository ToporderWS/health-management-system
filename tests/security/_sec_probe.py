# -*- coding: utf-8 -*-
"""环境探针：后端 8080 / MySQL 是否在线。"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _sec_lib import get, q1  # noqa: E402

out = {}
try:
    hc = get('/health')
    out['health_status'] = hc.get('status')
    out['health_json'] = hc.get('json')
except Exception as e:
    out['health_err'] = '%s: %s' % (type(e).__name__, e)

try:
    row = q1('SELECT DATABASE() AS db, VERSION() AS ver, NOW() AS now')
    out['db'] = row
    out['users_total'] = q1('SELECT COUNT(*) AS n FROM users')['n']
    out['doctors_total'] = q1('SELECT COUNT(*) AS n FROM doctor_user')['n']
    out['coaches_total'] = q1('SELECT COUNT(*) AS n FROM coach_user')['n']
except Exception as e:
    out['db_err'] = '%s: %s' % (type(e).__name__, e)

print(json.dumps(out, ensure_ascii=False, indent=1, default=str))
