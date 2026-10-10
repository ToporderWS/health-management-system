# -*- coding: utf-8 -*-
"""真机 UI BUGFIX 轮：小程序（mp-weixin）重新编译 + 产物一致性验收。

协议：PRE 快照 -> HBuilderX 命令行编译 -> POST 快照 -> 差异归因 -> 源码零漂移 -> 内容锚点
（不使用管道；所有输出自行落盘到 tests/security/_out/）
"""
import hashlib
import os
import subprocess
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


def snap_dir(root):
    out = {}
    for r, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != '.git']
        for fn in files:
            fp = os.path.join(r, fn)
            rel = os.path.relpath(fp, root).replace('\\', '/')
            out[rel] = {'size': os.path.getsize(fp), 'sha256': sha256(fp)}
    return out


SRC_FILES = [
    'miniapp/pages/index/index.vue',
    'miniapp/pages/report/index.vue',
    'miniapp/pages/profile/index.vue',
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
pre_src = {rel: sha256(os.path.join(BASE, rel)) for rel in SRC_FILES if os.path.exists(os.path.join(BASE, rel))}
p('  源码文件数 =', len(pre_src))
pre_dist = snap_dir(DIST)
p('  dist 文件数 =', len(pre_dist))

p('')
p('=== 2. 命令行重新编译（HBuilderX cli.exe launch mp-weixin --compile true） ===')
t0 = time.time()
proc = subprocess.run(
    [CLI, 'launch', 'mp-weixin', '--project', MINI, '--compile', 'true'],
    cwd=os.path.dirname(CLI), capture_output=True, timeout=900,
)
dt = time.time() - t0
build_out = (proc.stdout or b'').decode('utf-8', 'replace')
build_err = (proc.stderr or b'').decode('utf-8', 'replace')
p('  rc =', proc.returncode, ' elapsed = %.1fs' % dt)
open(os.path.join(OUT, '_realui_build_stdout.txt'), 'w', encoding='utf-8').write(build_out)
open(os.path.join(OUT, '_realui_build_stderr.txt'), 'w', encoding='utf-8').write(build_err)
p('  stdout 尾部：')
for line in [x for x in build_out.strip().splitlines() if x.strip()][-10:]:
    p('    ' + line)
if build_err.strip():
    p('  stderr 尾部：')
    for line in build_err.strip().splitlines()[-8:]:
        p('    ' + line)

p('')
p('=== 3. POST 快照 + 差异归因 ===')
post_dist = snap_dir(DIST)
added = sorted(set(post_dist) - set(pre_dist))
removed = sorted(set(pre_dist) - set(post_dist))
changed = []
unchanged = 0
for k in sorted(set(pre_dist) & set(post_dist)):
    if pre_dist[k]['sha256'] != post_dist[k]['sha256']:
        changed.append((k, post_dist[k]['size'] - pre_dist[k]['size']))
    else:
        unchanged += 1
p('  added =', len(added), ' removed =', len(removed), ' changed =', len(changed), ' unchanged =', unchanged)
p('  被改动的产物（本批应只有我们改过的页面/组件）：')
for k, d in sorted(changed):
    p('    changed: %-58s delta=%+d B' % (k, d))
for k in added[:20]:
    p('    added  : %s' % k)

p('')
p('=== 4. 源码零漂移 ===')
post_src = {rel: sha256(os.path.join(BASE, rel)) for rel in SRC_FILES if os.path.exists(os.path.join(BASE, rel))}
drift = [rel for rel in pre_src if pre_src[rel] != post_src.get(rel)]
p('  SOURCE_DRIFT =', drift if drift else 'NONE')

p('')
p('=== 5. 产物内容锚点 ===')


def read(rel):
    fp = os.path.join(DIST, rel)
    return open(fp, 'rb').read().decode('utf-8', 'replace') if os.path.exists(fp) else ''


report_js = read('dev/mp-weixin/pages/report/index.js')
report_wxml = read('dev/mp-weixin/pages/report/index.wxml')
home_wxml = read('dev/mp-weixin/pages/index/index.wxml')
home_wxss = read('dev/mp-weixin/pages/index/index.wxss')
uc_js = read('dev/mp-weixin/components/u-charts/u-charts.js')
img_js = read('dev/mp-weixin/common/image.js')
uc_src = open(os.path.join(BASE, 'miniapp/components/u-charts/u-charts.js'), 'rb').read().decode('utf-8', 'replace')

p('  -- 数据报告页（对象数组 ring / 空值过滤 / 图例） --')
for a in ['Number(x.value) > 0', '{ name: x.name, value: Number(x.value) || 0 }',
          'const wRows = pick(d.weight_trend', 'const bpRows = pick', 'const sRows = pick', 'const stRows = pick']:
    p('    [应有] %-56s hit=%d' % (a[:54], report_js.count(a)))
for a in ['data: (d.sport_by_type || []).map((x) => x.value)', 'data: (d.sleep_quality || []).map((x) => x.value)',
          'data: (d.weight_trend || []).map((x) => x.weight)']:
    p('    [应无] %-56s hit=%d' % (a[:54], report_js.count(a)))
p('    [应无] 全树旧 ring 结构残留 = %d' % sum(
    1 for r, d, fs in os.walk(DIST) for fn in fs
    if fn.endswith(('.js', '.json', '.wxml'))
    and 'data: (d.sport_by_type || []).map((x) => x.value)' in open(os.path.join(r, fn), 'rb').read().decode('utf-8', 'replace')))

p('  -- uCharts 组件（真机尺寸：CSS px + pixelRatio 1） --')
for a in ['boundingClientRect', 'uni.upx2px', 'pixelRatio']:
    p('    [应有] %-56s hit=%d' % (a, uc_js.count(a)))
p('    [应无] cWidth * pixelRatio          hit=%d' % uc_js.count('cWidth * pixelRatio'))
p('    [应无] cHeight * pixelRatio         hit=%d' % uc_js.count('cHeight * pixelRatio'))
p('    第三方库 u-charts.js 未被修改（oldseries[i].formatter 恰 1 处）= %d' % uc_src.count('oldseries[i].formatter'))

p('  -- 首页（HTML 实体「更多 ›」/ Hero 间距） --')
p('    [应有] \u203a (更多 ›)              hit=%d  |  原 “更多 &gt;” 残留 = %d'
  % (home_wxml.count('\u203a'), home_wxml.count('&gt;') + home_wxml.count('更多 >')))
for a in ['26rpx 30rpx 22rpx', 'font-size: 32rpx', 'margin-top: 14rpx', 'font-size: 34rpx']:
    p('    [应有] %-56s hit=%d' % (a, home_wxss.count(a)))

p('  -- 头像修复未被回滚 --')
p('    image.js 存在=%s 含 downloadFile=%s 含 imgSrc=%s' % (bool(img_js), 'downloadFile' in img_js, 'imgSrc' in img_js))
for rel in ['dev/mp-weixin/pages/profile/index.js', 'dev/mp-weixin/pages/index/index.js']:
    p('    %-44s 走 imgSrc = %s' % (rel, 'imgSrc' in read(rel)))
for rel in ['dev/mp-weixin/pages/index/index.wxml', 'dev/mp-weixin/pages/article/index.wxml']:
    p('    %-44s wxml 含 imgSrc = %s' % (rel, 'imgSrc' in read(rel)))

p('')
p('  -- 关键入口存在性 --')
for rel in ['dev/mp-weixin/app.js', 'dev/mp-weixin/app.json', 'dev/mp-weixin/common/vendor.js',
            'dev/mp-weixin/common/image.js', 'dev/mp-weixin/components/u-charts/u-charts.js']:
    fp = os.path.join(DIST, rel)
    p('    %-48s exists=%s size=%s' % (rel, os.path.exists(fp), os.path.getsize(fp) if os.path.exists(fp) else '-'))

report = '\n'.join(LOG)
open(os.path.join(OUT, 'REALUI_BUILD_VERIFY.md'), 'w', encoding='utf-8').write(report)
print('\n[落盘] tests/security/_out/REALUI_BUILD_VERIFY.md')
