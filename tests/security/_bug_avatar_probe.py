"""只读探针：确认 /api/user/info 的 avatar 字段（服务层直调，无需口令）。"""
import sys, os, io, json

BASE = r'C:/Users/Toporder-WS/Desktop/项目/个人健康管理系统小程序/health-management-system'
sys.path.insert(0, os.path.join(BASE, 'backend'))
os.chdir(os.path.join(BASE, 'backend'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _sec_lib import q

def p(s=''):
    print(s, flush=True)

import services.user_service as us

ok, msg, data = us.get_info(13)
p('user_service.get_info(13) -> ok=%s msg=%s' % (ok, msg))
p('  payload = %s' % json.dumps(data, ensure_ascii=False, default=str))
p('  avatar  = %r' % (data or {}).get('avatar'))

p()
p('== 三张 UUID 文件与数据库引用关系 ==')
files = sorted(os.listdir(os.path.join(BASE, 'backend', 'static', 'upload')))
for f in files:
    refs = []
    for t, col in (('users', 'avatar'), ('doctor_user', 'avatar'),
                   ('coach_user', 'avatar'), ('admin_user', 'avatar'),
                   ('health_article', 'cover_img')):
        try:
            n = q('SELECT COUNT(*) AS c FROM `%s` WHERE `%s`=%%s' % (t, col), (f,))[0]['c']
        except Exception as e:
            n = -1
        if n:
            refs.append('%s.%s=%d' % (t, col, n))
    p('  %-42s refs=%s' % (f, refs or 'ORPHAN'))

p()
p('== 小周 user13 ==')
p('  %s' % (q('SELECT id,nickname,phone,avatar FROM users WHERE id=13'),))
