# -*- coding: utf-8 -*-
import glob
import io
import os
import re

BASE = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system'

# 1) dist 内 API base（生产应使用相对 /api 与 /static/upload/）
DIST = os.path.join(BASE, 'management-web', 'dist', 'assets')
hit = set()
for p in glob.glob(os.path.join(DIST, '*.js')):
    t = io.open(p, encoding='utf-8', errors='replace').read()
    for m in re.finditer(r'["\'](/api|/static/upload/)["\']', t):
        hit.add((os.path.basename(p), m.group(1)))
print('dist API/STATIC 相对引用 =', sorted(hit))

# 2) miniapp 网络配置入口唯一性
mp = os.path.join(BASE, 'miniapp')
cfg_path = os.path.join(mp, 'common', 'config.js')
cfg = io.open(cfg_path, encoding='utf-8').read()
print('miniapp/common/config.js 含 192.168.2.219 次数 =', cfg.count('192.168.2.219'))
hits = []
for r, ds, fs in os.walk(mp):
    ds[:] = [d for d in ds if d not in ('node_modules', 'unpackage', '.git')]
    for f in fs:
        if not f.endswith(('.js', '.vue', '.json', '.ts', '.wxml', '.wxss')):
            continue
        p = os.path.join(r, f)
        if os.path.abspath(p) == os.path.abspath(cfg_path):
            continue
        t = io.open(p, encoding='utf-8', errors='replace').read()
        if re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?\b', t):
            hits.append(os.path.relpath(p, mp).replace('\\', '/'))
print('miniapp 其它文件出现 IP 字面量 =', hits if hits else 'NONE')

# 3) PC 管理端路由 / 一级模块
src = os.path.join(BASE, 'management-web', 'src')
routers = sorted(glob.glob(os.path.join(src, 'router', '*')))
menu = sorted(glob.glob(os.path.join(src, '**', '*menu*'), recursive=True))
print('router 目录项 =', [os.path.basename(x) for x in routers])
for p in routers:
    if not p.endswith('.js'):
        continue
    t = io.open(p, encoding='utf-8', errors='replace').read()
    paths = re.findall(r"path:\s*['\"]([^'\"]+)", t)
    recs = re.findall(r"name:\s*['\"]([^'\"]+)", t)
    print('  %-18s routes=%d names=%d' % (os.path.basename(p), len(paths), len(recs)))
print('menu 相关文件 =', [os.path.relpath(x, src).replace('\\', '/') for x in menu])
