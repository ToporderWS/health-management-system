# -*- coding: utf-8 -*-
"""
存量① 只读审计：全项目 API 地址扫描。
只读。不修改任何文件。
"""
import os
import re
import io
import json

BASE = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system'
OUT = os.path.join(BASE, 'tests', 'security', '_out')

ROOTS = ['backend', 'miniapp', 'management-web', 'database', 'docs']

# 排除：第三方依赖 / 构建产物 / 缓存 / 虚拟环境
EXCL_DIR = {'node_modules', 'dist', 'unpackage', '.venv', 'venv', '__pycache__',
            '.git', '.idea', '.vscode', '.hbuilderx', 'build', 'illustration-raw'}
EXCL_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.woff', '.woff2',
            '.ttf', '.eot', '.mp4', '.zip', '.jar', '.exe', '.dll', '.so',
            '.pyc', '.map', '.psd', '.svg'}
MAXSIZE = 2 * 1024 * 1024

PATTERNS = [
    ('LAN_IP',      re.compile(r'192\.168\.\d{1,3}\.\d{1,3}')),
    ('LOCALHOST',   re.compile(r'\blocalhost\b')),
    ('LOOPBACK',    re.compile(r'127\.0\.0\.1')),
    ('PORT_8080',   re.compile(r':8080\b')),
    ('PORT_5000',   re.compile(r':500[01]\b')),
    ('API_BASE_URL', re.compile(r'API_BASE_URL')),
    ('STATIC_BASE_URL', re.compile(r'STATIC_BASE_URL')),
    ('baseURL',     re.compile(r'baseURL')),
    ('VITE_',       re.compile(r'VITE_[A-Z_]+')),
    ('proxy',       re.compile(r'\bproxy\b|changeOrigin')),
    ('STATIC_UPLOAD', re.compile(r'/static/upload')),
]


def iter_files():
    for root in ROOTS:
        rp = os.path.join(BASE, root)
        if not os.path.isdir(rp):
            continue
        for r, ds, fs in os.walk(rp):
            ds[:] = [d for d in ds if d not in EXCL_DIR]
            for f in fs:
                ext = os.path.splitext(f)[1].lower()
                if ext in EXCL_EXT:
                    continue
                fp = os.path.join(r, f)
                try:
                    if os.path.getsize(fp) > MAXSIZE:
                        continue
                except OSError:
                    continue
                yield root, fp


def main():
    hits = []
    scanned = 0
    for root, fp in iter_files():
        try:
            txt = open(fp, 'rb').read().decode('utf-8', 'replace')
        except OSError:
            continue
        scanned += 1
        rel = os.path.relpath(fp, BASE).replace(os.sep, '/')
        for i, line in enumerate(txt.splitlines(), 1):
            for tag, pat in PATTERNS:
                for m in pat.finditer(line):
                    hits.append({
                        'root': root, 'file': rel, 'line': i, 'tag': tag,
                        'value': m.group(0),
                        'text': line.strip()[:200],
                    })
    # 去重（同一行同 tag 同值只留一条）
    seen = set()
    uniq = []
    for h in hits:
        k = (h['file'], h['line'], h['tag'], h['value'])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(h)

    # 汇总
    by_root = {}
    by_tag = {}
    for h in uniq:
        by_root[h['root']] = by_root.get(h['root'], 0) + 1
        by_tag[h['tag']] = by_tag.get(h['tag'], 0) + 1

    res = {'scanned_files': scanned, 'total_hits': len(uniq),
           'by_root': by_root, 'by_tag': by_tag, 'hits': uniq}
    os.makedirs(OUT, exist_ok=True)
    with io.open(os.path.join(OUT, 'ADDR_AUDIT.json'), 'w', encoding='utf-8') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2))

    print('scanned_files =', scanned)
    print('total_hits    =', len(uniq))
    print('by_root       =', by_root)
    print('by_tag        =', by_tag)
    print()
    print('===== 逐项 =====')
    for h in uniq:
        print('%-16s %-18s %s:%d  | %s' % (h['root'], h['tag'], h['file'], h['line'], h['text'][:150]))

    # ---- 产品源码口径（排除 docs / database）----
    print()
    print('===== 产品源码口径统计（排除 docs/）=====')
    prod = [h for h in uniq if h['root'] != 'docs']
    for tag in ['LAN_IP', 'LOCALHOST', 'LOOPBACK', 'PORT_5000']:
        n = len([h for h in prod if h['tag'] == tag])
        files = sorted(set(h['file'] for h in prod if h['tag'] == tag))
        print('  %-12s 命中 %d 处 / 文件: %s' % (tag, n, files))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
