# -*- coding: utf-8 -*-
"""小程序（mp-weixin）重新编译 + 产物一致性验收。

六步协议：PRE 快照 -> 命令行编译 -> POST 快照 -> 差异归因 -> 内容锚点 -> 源码零漂移。
不使用管道（避免回显被吞）；所有输出自行落盘到 tests/security/_out/。
"""
import hashlib
import os
import subprocess
import sys
import time

BASE = r'C:/Users/Toporder-WS/Desktop/项目/个人健康管理系统小程序/health-management-system'
MINI = os.path.join(BASE, 'miniapp')
DIST = os.path.join(MINI, 'unpackage', 'dist')
OUT = os.path.join(BASE, 'tests', 'security', '_out')
CLI = r'C:/Users/Toporder-WS/Downloads/HBuilderX.5.24.2026081301/HBuilderX/cli.exe'
os.makedirs(OUT, exist_ok=True)

LOG = []


def p(*a):
    s = ' '.join(str(x) for x in a)
    LOG.append(s)
    print(s)


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 16), b''):
            h.update(chunk)
    return h.hexdigest()


def snap_dir(root, rel_prefix=''):
    out = {}
    for r, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != '.git']
        for fn in files:
            fp = os.path.join(r, fn)
            rel = os.path.relpath(fp, root).replace('\\', '/')
            out[rel_prefix + rel] = {
                'size': os.path.getsize(fp),
                'sha256': sha256(fp),
                'mtime': int(os.path.getmtime(fp)),
            }
    return out


SRC_FILES = [
    'miniapp/pages/report/index.vue',
    'miniapp/pages/profile/index.vue',
    'miniapp/pages/index/index.vue',
    'miniapp/pages/article/index.vue',
    'miniapp/pages/article-detail/index.vue',
    'miniapp/common/image.js',
    'miniapp/common/config.js',
    'miniapp/components/u-charts/u-charts.js',
    'miniapp/components/u-charts/u-charts.vue',
    'miniapp/pages.json',
    'miniapp/manifest.json',
    'miniapp/App.vue',
    'miniapp/main.js',
    'miniapp/api/index.js',
]

p('=== 1. PRE 基线 ===')
pre_src = {}
for rel in SRC_FILES:
    fp = os.path.join(BASE, rel)
    if os.path.exists(fp):
        pre_src[rel] = {'sha256': sha256(fp), 'size': os.path.getsize(fp)}
p('  源码文件数 =', len(pre_src))
pre_dist = snap_dir(DIST)
p('  dist 文件数 =', len(pre_dist))

p('')
p('=== 2. 命令行重新编译（HBuilderX cli.exe launch mp-weixin --compile true） ===')
t0 = time.time()
proc = subprocess.run(
    [CLI, 'launch', 'mp-weixin', '--project', MINI, '--compile', 'true'],
    cwd=os.path.dirname(CLI), capture_output=True, timeout=600,
)
dt = time.time() - t0
build_out = (proc.stdout or b'').decode('utf-8', 'replace')
build_err = (proc.stderr or b'').decode('utf-8', 'replace')
p('  rc =', proc.returncode, ' elapsed = %.1fs' % dt)
open(os.path.join(OUT, '_ucharts_build_stdout.txt'), 'w', encoding='utf-8').write(build_out)
open(os.path.join(OUT, '_ucharts_build_stderr.txt'), 'w', encoding='utf-8').write(build_err)
p('  stdout 尾部：')
for line in [x for x in build_out.strip().splitlines() if x.strip()][-12:]:
    p('    ' + line)
if build_err.strip():
    p('  stderr：')
    for line in build_err.strip().splitlines()[-8:]:
        p('    ' + line)

p('')
p('=== 3. POST 快照 + 差异归因 ===')
post_src = {}
for rel in SRC_FILES:
    fp = os.path.join(BASE, rel)
    if os.path.exists(fp):
        post_src[rel] = {'sha256': sha256(fp), 'size': os.path.getsize(fp)}
post_dist = snap_dir(DIST)

added = sorted(set(post_dist) - set(pre_dist))
removed = sorted(set(pre_dist) - set(post_dist))
changed, unchanged = [], 0
for k in sorted(set(pre_dist) & set(post_dist)):
    if pre_dist[k]['sha256'] != post_dist[k]['sha256']:
        changed.append((k, post_dist[k]['size'] - pre_dist[k]['size']))
    else:
        unchanged += 1
p('  added =', len(added), ' removed =', len(removed), ' changed =', len(changed), ' unchanged =', unchanged)
p('  关键入口存在性：')
for rel in ['dev/mp-weixin/app.js', 'dev/mp-weixin/app.json', 'dev/mp-weixin/app.wxss',
            'dev/mp-weixin/common/vendor.js', 'dev/mp-weixin/common/image.js',
            'dev/mp-weixin/pages/report/index.js', 'dev/mp-weixin/pages/report/index.wxml']:
    fp = os.path.join(DIST, rel)
    p('    %-42s exists=%s size=%s' % (rel, os.path.exists(fp), os.path.getsize(fp) if os.path.exists(fp) else '-'))
if len(changed) <= 25:
    for k, d in changed:
        p('    changed: %-58s delta=%+d B' % (k, d))
else:
    p('    (changed 明细 >25 项，见下方聚合)')
    tot = sum(d for _, d in changed)
    p('    changed 总字节差 =%+d' % tot)
    for k, d in sorted(changed, key=lambda x: -abs(x[1]))[:12]:
        p('    changed: %-58s delta=%+d B' % (k, d))

p('')
p('=== 4. 源码零漂移 ===')
drift = [rel for rel in pre_src if pre_src[rel]['sha256'] != post_src.get(rel, {}).get('sha256')]
p('  SOURCE_DRIFT =', drift if drift else 'NONE')

p('')
p('=== 5. 产物内容锚点 ===')
rp = os.path.join(DIST, 'dev', 'mp-weixin', 'pages', 'report', 'index.js')
t = open(rp, 'rb').read().decode('utf-8', 'replace')
NEW_ANCHORS = [
    'const sportTypes = d.sport_by_type || []',
    'const qualities = d.sleep_quality || []',
    '{ name: x.name, value: Number(x.value) || 0 }',
]
BAD_ANCHORS = [
    'series: [{ name: "运动时长", data: (d.sport_by_type || []).map((x) => x.value) }]',
    'series: [{ name: "次数", data: qualities.map((x) => x.value) }]',
]
for a in NEW_ANCHORS:
    p('  [应有] %-62s hit=%d' % (a[:60], t.count(a)))
for a in BAD_ANCHORS:
    p('  [应无] %-62s hit=%d' % (a[:60], t.count(a)))

# 全树扫描：旧结构残留（整个 dist 目录）
bad_scan = 0
for r, dirs, files in os.walk(DIST):
    for fn in files:
        if fn.endswith(('.js', '.json', '.wxml', '.wxss', '.map')):
            fp = os.path.join(r, fn)
            try:
                c = open(fp, 'rb').read().decode('utf-8', 'replace')
            except Exception:
                continue
            if 'data: (d.sport_by_type || []).map((x) => x.value)' in c:
                bad_scan += 1
                p('  !! 旧结构残留:', os.path.relpath(fp, DIST))
p('  全树旧结构残留文件数 =', bad_scan)

# 头像修复未被回滚
ip = os.path.join(DIST, 'dev', 'mp-weixin', 'common', 'image.js')
ii = open(ip, 'rb').read().decode('utf-8', 'replace') if os.path.exists(ip) else ''
p('  image.js（头像本地化）存在 =', os.path.exists(ip), ' 含 downloadFile =', 'downloadFile' in ii, ' 含 imgSrc =', 'imgSrc' in ii)
for rel in ['dev/mp-weixin/pages/profile/index.js', 'dev/mp-weixin/pages/index/index.js']:
    c = open(os.path.join(DIST, rel), 'rb').read().decode('utf-8', 'replace')
    p('  %s 走 imgSrc = %s' % (rel, 'imgSrc' in c))

report = '\n'.join(LOG)
open(os.path.join(OUT, 'UCHARTS_BUILD_VERIFY.md'), 'w', encoding='utf-8').write(report)
print('\n[落盘] tests/security/_out/UCHARTS_BUILD_VERIFY.md')
