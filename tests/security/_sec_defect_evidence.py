# -*- coding: utf-8 -*-
"""缺陷取证：management-web 根目录残留验证脚本清点 + 构建产物隔离性核查。"""
import io
import json
import os
import re
import sys

WEB = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system\management-web'
OUT = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system\tests\security\_out'

rep = {}

# 1. 根目录残留清点（顶层以 _ 开头，或 *.log）
extras = []
for f in sorted(os.listdir(WEB)):
    p = os.path.join(WEB, f)
    if os.path.isdir(p):
        if f.startswith('_'):
            n = sum(len(fs) for _r, _d, fs in os.walk(p))
            extras.append({'name': f, 'type': 'dir', 'files': n})
        continue
    if f.startswith('_') or f.endswith('.log'):
        extras.append({'name': f, 'type': 'file', 'size': os.path.getsize(p)})
rep['leftovers'] = extras
rep['leftover_count'] = len(extras)

# 2. 含明文 admin 口令的文件（精确取证：admin_name/admin + 123456）
pat = re.compile(r'123456')
hits = []
for e in extras:
    if e['type'] != 'file':
        continue
    p = os.path.join(WEB, e['name'])
    try:
        txt = io.open(p, encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    lines = [ln.strip()[:160] for ln in txt.splitlines() if pat.search(ln)]
    if lines:
        hits.append({'file': e['name'], 'n_lines': len(lines), 'sample': lines[:4]})
rep['plaintext_pwd_files'] = hits

# 3. 构建产物是否包含这些脚本
dist = os.path.join(WEB, 'dist')
dist_all = []
if os.path.isdir(dist):
    for r, _d, fs in os.walk(dist):
        for f in fs:
            dist_all.append(os.path.relpath(os.path.join(r, f), dist))
rep['dist_file_count'] = len(dist_all)
rep['dist_contains_leftover'] = [x for x in dist_all
                                 if '_probe' in x or '_verify' in x or '_shot' in x
                                 or '_diag' in x or '_patch' in x or '_tune' in x]

# 4. 是否被 src / package.json / index.html 引用
refs = []
for sub in ('src', 'public'):
    base = os.path.join(WEB, sub)
    for r, _d, fs in os.walk(base):
        for f in fs:
            if not f.endswith(('.js', '.vue', '.ts', '.html', '.css', '.json')):
                continue
            p = os.path.join(r, f)
            try:
                txt = io.open(p, encoding='utf-8', errors='replace').read()
            except Exception:
                continue
            for m in re.finditer(r'_probe\w*|_verify\w*|_shot\w*|_diag\w*|_patch\w*|_tune\w*', txt):
                refs.append({'file': os.path.relpath(p, WEB), 'token': m.group(0)})
rep['referenced_by_src'] = refs

txt = json.dumps(rep, ensure_ascii=False, indent=1)
io.open(os.path.join(OUT, 'DEFECT_EVIDENCE.json'), 'w', encoding='utf-8').write(txt)
print(txt)
