# -*- coding: utf-8 -*-
"""产物语法与符号完整性校验（mp-weixin）。

1) 对 dist 下所有 .js 执行 `node --check`（语法必须全部通过）
2) 校验 pages/components/app 引用的 common_vendor.X 与 api/common 模块导出是否齐全
3) 统计导出符号数量，作为 vendor.js 未损坏的量化证据
"""
import os
import re
import subprocess
import sys

BASE = r'C:/Users/Toporder-WS/Desktop/项目/个人健康管理系统小程序/health-management-system'
DIST = os.path.join(BASE, 'miniapp', 'unpackage', 'dist', 'dev', 'mp-weixin')
OUT = os.path.join(BASE, 'tests', 'security', '_out', 'UCHARTS_DIST_SYMBOL_CHECK.md')
NODE = r'C:/Users/Toporder-WS/.workbuddy/binaries/node/versions/22.22.2-3/node.exe'

lines = []
def p(*a):
    s = ' '.join(str(x) for x in a)
    lines.append(s)
    print(s)

# ---- 1. 语法 ----
js_files = []
for r, d, f in os.walk(DIST):
    for fn in f:
        if fn.endswith('.js'):
            js_files.append(os.path.join(r, fn))
p('=== 1. 语法校验（node --check） ===')
p('  .js 文件数 =', len(js_files))
bad = []
for fp in js_files:
    r = subprocess.run([NODE, '--check', fp], capture_output=True)
    if r.returncode != 0:
        bad.append((os.path.relpath(fp, DIST), (r.stderr or b'').decode('utf-8', 'replace')[:200]))
p('  语法失败文件数 =', len(bad))
for k, m in bad:
    p('   !!', k, '->', m)

# ---- 2. 符号完整性 ----
p('')
p('=== 2. common_vendor 符号完整性 ===')
vt = open(os.path.join(DIST, 'common', 'vendor.js'), 'rb').read().decode('utf-8', 'replace')
defined = set(re.findall(r'exports\.([A-Za-z_$][\w$]*)\s*=', vt))
p('  vendor.js 导出符号数 =', len(defined))
p('  vendor.js 字节数 =', len(vt.encode('utf-8')))

used = set()
missing = {}
for fp in js_files:
    rel = os.path.relpath(fp, DIST).replace('\\', '/')
    t = open(fp, 'rb').read().decode('utf-8', 'replace')
    for m in re.finditer(r'common_vendor\.([A-Za-z_$][\w$]*)', t):
        name = m.group(1)
        used.add(name)
        if name not in defined:
            missing.setdefault(rel, set()).add(name)
p('  业务代码引用 common_vendor.X 去重后 =', len(used))
p('  未定义的引用 =', len(missing))
for k in sorted(missing):
    p('   !!', k, '->', sorted(missing[k]))

# 其它按模块自动生成的对象（例如 common_vendor.index / wx 等运行时注入）
p('')
p('=== 3. 各模块导出计数 ===')
for rel in ['api/index.js', 'common/auth.js', 'common/config.js', 'common/image.js', 'common/request.js']:
    fp = os.path.join(DIST, rel)
    t = open(fp, 'rb').read().decode('utf-8', 'replace')
    ex = re.findall(r'exports\.([A-Za-z_$][\w$]*)\s*=', t)
    p('  %-22s exports=%s' % (rel, ','.join(sorted(set(ex)))))

# ---- 4. 页面引用模块存在性 ----
p('')
p('=== 4. 页面/组件文件齐备 ===')
pages = sorted(os.listdir(os.path.join(DIST, 'pages')))
p('  页面目录数 =', len(pages))
missing_page = []
for pg in pages:
    d = os.path.join(DIST, 'pages', pg)
    for need in ['index.js', 'index.json', 'index.wxml']:
        if not os.path.exists(os.path.join(d, need)):
            missing_page.append('%s/%s' % (pg, need))
p('  缺失必需文件 =', len(missing_page))
for m in missing_page:
    p('   !!', m)

ok = (len(bad) == 0 and len(missing) == 0 and len(missing_page) == 0)
p('')
p('DIST_SYMBOL_CHECK = ' + ('PASS' if ok else 'FAIL'))

open(OUT, 'w', encoding='utf-8').write('\n'.join(lines))
print('\n[落盘]', OUT)
sys.exit(0 if ok else 1)
