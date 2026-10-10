# -*- coding: utf-8 -*-
"""编译确定性实验：连续两次 `cli launch mp-weixin --compile true`，比对产物哈希。

若两次产物逐字节一致 => CLI 编译是确定性的，前一阶段 PRE(GUI 运行) → POST(CLI 编译)
的字节差属于「构建模式差异」（HBuilderX GUI 运行会写 sourceMappingURL 尾注等），
而不是随机/损坏。
"""
import hashlib
import os
import subprocess

BASE = r'C:/Users/Toporder-WS/Desktop/项目/个人健康管理系统小程序/health-management-system'
MINI = os.path.join(BASE, 'miniapp')
DIST = os.path.join(MINI, 'unpackage', 'dist')
OUT = os.path.join(BASE, 'tests', 'security', '_out')
CLI = r'C:/Users/Toporder-WS/Downloads/HBuilderX.5.24.2026081301/HBuilderX/cli.exe'


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 16), b''):
            h.update(c)
    return h.hexdigest()


def snap():
    d = {}
    for r, dd, ff in os.walk(DIST):
        for fn in ff:
            fp = os.path.join(r, fn)
            d[os.path.relpath(fp, DIST).replace('\\', '/')] = (os.path.getsize(fp), sha(fp))
    return d


a = snap()
print('run1 快照文件数 =', len(a))

p = subprocess.run([CLI, 'launch', 'mp-weixin', '--project', MINI, '--compile', 'true'],
                   cwd=os.path.dirname(CLI), capture_output=True, timeout=600)
out = (p.stdout or b'').decode('utf-8', 'replace')
print('rc =', p.returncode)
for line in [x for x in out.strip().splitlines() if x.strip()][-4:]:
    print('   ', line)
open(os.path.join(OUT, '_ucharts_build2_stdout.txt'), 'w', encoding='utf-8').write(out)

b = snap()
print('run2 快照文件数 =', len(b))

same = [k for k in a if k in b and a[k] == b[k]]
diff = [k for k in a if k in b and a[k] != b[k]]
only_a = sorted(set(a) - set(b))
only_b = sorted(set(b) - set(a))
print('相同 =', len(same), ' 不同 =', len(diff), ' 仅run1 =', len(only_a), ' 仅run2 =', len(only_b))
for k in diff:
    print('   DIFF', k, a[k][0], '->', b[k][0])

det = (len(diff) == 0 and len(only_a) == 0 and len(only_b) == 0)
print('BUILD_DETERMINISTIC =', 'YES' if det else 'NO')
open(os.path.join(OUT, 'UCHARTS_BUILD_DETERMINISM.md'), 'w', encoding='utf-8').write(
    'run1 files=%d\nrun2 files=%d\nidentical=%d\ndiff=%d\nBUILD_DETERMINISTIC=%s\n'
    % (len(a), len(b), len(same), len(diff), 'YES' if det else 'NO'))
