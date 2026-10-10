# -*- coding: utf-8 -*-
"""存量事项② · JWT_SECRET 轮换（不打印任何 Secret 值）。

动作：
  1) backend/.env          : JWT_SECRET 行替换为 secrets.token_urlsafe(64) 生成值
  2) backend/.env.example  : 真实值不得出现，仅保留安全占位符

守卫：锚点「JWT_SECRET=」在 .env 中必须恰好命中 1 行，否则整批中止，不写任何文件。
输出：仅统计量（ROTATED / LENGTH / SOURCE / 行数），不含 Secret 本体。
"""
import io
import os
import re
import secrets
import sys

BASE = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system'
ENV = os.path.join(BASE, 'backend', '.env')
ENV_EX = os.path.join(BASE, 'backend', '.env.example')
PLACEHOLDER = 'CHANGE_ME_TO_A_STRONG_RANDOM_SECRET'


def rd(p):
    with open(p, 'rb') as f:
        return f.read().decode('utf-8')


def wr(p, s):
    with open(p, 'wb') as f:
        f.write(s.encode('utf-8'))


def nl(s):
    return '\r\n' if '\r\n' in s else '\n'


env = rd(ENV)
eol = nl(env)
rx = re.compile(r'^[ \t]*JWT_SECRET=.*$', re.M)
hits = rx.findall(env)
print('ANCHOR .env  JWT_SECRET= lines =', len(hits))
if len(hits) != 1:
    print('!! 锚点命中数 != 1，整批中止（不改任何文件）')
    sys.exit(2)

old_line = hits[0]
old_val = old_line.split('=', 1)[1].strip()
print('OLD_JWT_SECRET_LENGTH =', len(old_val))

new_secret = secrets.token_urlsafe(64)          # 64 bytes 熵 -> 86 字符 URL-safe
assert len(new_secret) >= 32, 'secret too short'
new_line = 'JWT_SECRET=' + new_secret

env2 = env.replace(old_line, new_line, 1)
wr(ENV, env2)

# ---- .env.example：只允许安全占位符 ----
ex = rd(ENV_EX)
ex_eol = nl(ex)
rx2 = re.compile(r'^[ \t]*JWT_SECRET=.*$', re.M)
hits2 = rx2.findall(ex)
print('ANCHOR .env.example  JWT_SECRET= lines =', len(hits2))
if len(hits2) != 1:
    print('!! .env.example 锚点命中数 != 1，中止（.env 已写，需人工复核）')
    sys.exit(3)
old_ex_line = hits2[0]
ex2 = ex.replace(old_ex_line, 'JWT_SECRET=' + PLACEHOLDER, 1)
wr(ENV_EX, ex2)

# ---- 复核 ----
chk = rd(ENV)
cur = rx.search(chk).group(0).split('=', 1)[1].strip()
chk_ex = rd(ENV_EX)
cur_ex = rx2.search(chk_ex).group(0).split('=', 1)[1].strip()

print('JWT_SECRET_ROTATED = YES')
print('JWT_SECRET_LENGTH =', len(cur))
print('JWT_SECRET_SOURCE = cryptographically_secure_random')
print('ENV_SECRET_MATCHES_GENERATED =', cur == new_secret)
print('.env.example_JWT_SECRET =', cur_ex)
print('.env.example_CONTAINS_REAL_SECRET =', (cur_ex == cur))
print('REAL_SECRET_IN_EXAMPLE =', 1 if cur_ex == cur else 0)
print('EOL .env =', repr(eol), ' .env.example =', repr(ex_eol))
