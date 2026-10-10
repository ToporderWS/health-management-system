# -*- coding: utf-8 -*-
"""编译确定性验证：连续两次编译，逐字节比较 dist 产物；并归因与上一批的差异。"""
import hashlib
import os
import re
import subprocess
import time

BASE = r'C:/Users/Toporder-WS/Desktop/项目/个人健康管理系统小程序/health-management-system'
MINI = os.path.join(BASE, 'miniapp')
DIST = os.path.join(MINI, 'unpackage', 'dist')
OUT = os.path.join(BASE, 'tests', 'security', '_out')
CLI = r'C:/Users/Toporder-WS/Downloads/HBuilderX.5.24.2026081301/HBuilderX/cli.exe'

LOG = []


def p(*a):
    s = ' '.join(str(x) for x in a)
    LOG.append(s)
    print(s)


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for c in iter(lambda: f.read(1 << 16), b''):
            h.update(c)
    return h.hexdigest()


def snap():
    out = {}
    for r, dirs, files in os.walk(DIST):
        dirs[:] = [d for d in dirs if d != '.git']
        for fn in files:
            fp = os.path.join(r, fn)
            out[os.path.relpath(fp, DIST).replace('\\', '/')] = sha256(fp)
    return out


p('=== A. 编译 #2 前快照 ===')
s1 = snap()
p('  files =', len(s1))

p('')
p('=== B. 第二次命令行编译 ===')
t0 = time.time()
proc = subprocess.run([CLI, 'launch', 'mp-weixin', '--project', MINI, '--compile', 'true'],
                      cwd=os.path.dirname(CLI), capture_output=True, timeout=900)
p('  rc =', proc.returncode, ' elapsed = %.1fs' % (time.time() - t0))
out = (proc.stdout or b'').decode('utf-8', 'replace')
for line in [x for x in out.strip().splitlines() if x.strip()][-6:]:
    p('    ' + line)

p('')
p('=== C. 逐字节一致性 ===')
s2 = snap()
same = sum(1 for k in s1 if s1.get(k) == s2.get(k))
diff = sorted(k for k in set(s1) | set(s2) if s1.get(k) != s2.get(k))
p('  一致 = %d / %d' % (same, len(set(s1) | set(s2))))
p('  不一致 =', diff if diff else 'NONE')
p('  BUILD_DETERMINISM =', 'PASS' if not diff else 'FAIL')

p('')
p('=== D. 产物体积差异归因（sourceMappingURL / 内联 sourcemap / uni 统计标记） ===')
D = os.path.join(DIST, 'dev', 'mp-weixin')
for rel in ['common/vendor.js', 'pages/report/index.js', 'components/u-charts/u-charts.js']:
    fp = os.path.join(D, rel)
    t = open(fp, 'rb').read().decode('utf-8', 'replace')
    p('  %-42s size=%-8d sourceMappingURL=%d  longComment(>200)=%d' % (
        rel, len(t.encode('utf-8')), t.count('sourceMappingURL'),
        len([l for l in t.splitlines() if len(l) > 200 and l.lstrip().startswith('//')])))
sm = os.path.join(DIST, '.sourcemap')
n = sum(len(f) for _, _, f in os.walk(sm)) if os.path.isdir(sm) else 0
p('  dist/.sourcemap 文件数 =', n)
p('  说明：dev 构建的 sourcemap 走独立目录；上面统计的产物内 sourceMappingURL 计数即"是否内联"。')

rep = '\n'.join(LOG)
open(os.path.join(OUT, 'REALUI_BUILD_DETERMINISM.md'), 'w', encoding='utf-8').write(rep)
print('\n[落盘] tests/security/_out/REALUI_BUILD_DETERMINISM.md')
