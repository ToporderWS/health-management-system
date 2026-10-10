# -*- coding: utf-8 -*-
"""只读核对：产品目录中的缓存/临时产物候选（不删除任何内容）。"""
import fnmatch
import io
import os

BASE = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system'
SKIP = {'node_modules', '.venv', 'venv', '.git', 'unpackage', 'dist', '__pycache__'}
# 只读扫描：把 __pycache__ 单独处理，不放进 SKIP
SKIP_NO_PYC = {'node_modules', '.venv', 'venv', '.git', 'unpackage', 'dist'}
PATTERNS = ['_probe*', '_verify*', '_shot*', '_diag*', '_patch*', '_tune*',
            '*.log', '*.pyc', '*.pyo', '*.tmp', '*.bak', '*~', '*.orig']
OUT = []


def p(s=''):
    OUT.append(str(s))


def main():
    candidates = []      # (relpath, kind, size)
    for root in ['backend', 'management-web', 'miniapp', 'tests', 'database', 'docs', '.']:
        base = os.path.join(BASE, root)
        if not os.path.isdir(base):
            continue
        for r, ds, fs in os.walk(base):
            rel_r = os.path.relpath(r, BASE).replace('\\', '/')
            # 不深入 node_modules/.venv/dist/unpackage
            ds[:] = [d for d in ds if d not in SKIP_NO_PYC]
            for f in fs:
                rel = (rel_r + '/' + f).lstrip('./')
                if any(fnmatch.fnmatch(f, pat) for pat in PATTERNS):
                    if f.endswith(('.pyc', '.pyo')):
                        kind = 'PYC'
                    elif f.endswith('.log'):
                        kind = 'LOG'
                    else:
                        kind = 'OTHER'
                    try:
                        sz = os.path.getsize(os.path.join(r, f))
                    except Exception:
                        sz = -1
                    candidates.append((rel, kind, sz))
    candidates.sort()

    # ---- 缓存目录（__pycache__ / _verify_out / _out 等） ----
    cache_dirs = []
    for root in ['backend', 'management-web', 'miniapp', 'tests']:
        base = os.path.join(BASE, root)
        if not os.path.isdir(base):
            continue
        for r, ds, fs in os.walk(base):
            ds[:] = [d for d in ds if d not in SKIP_NO_PYC]
            b = os.path.basename(r)
            if b == '__pycache__' or b.endswith('_verify_out') or b == '_verify_out' or b == '_out':
                n_pyc = len([x for x in fs if x.lower().endswith(('.pyc', '.pyo'))])
                n_other = len(fs) - n_pyc
                cache_dirs.append((os.path.relpath(r, BASE).replace('\\', '/'), len(fs), n_pyc, n_other))
    cache_dirs.sort()

    p('=== A. 缓存目录清单 ===')
    for d, n, npyc, nother in cache_dirs:
        p('   %-46s files=%-4d pyc=%-4d non_pyc=%d' % (d, n, npyc, nother))
    p('   cache_dirs_total = %d' % len(cache_dirs))
    p()

    p('=== B. 散落缓存/临时文件候选 ===')
    kinds = {}
    for rel, kind, sz in candidates:
        kinds[kind] = kinds.get(kind, 0) + 1
        p('   [%-5s] %-60s %d B' % (kind, rel, sz))
    p('   by_kind = %s' % kinds)
    p()

    p('=== C. 禁列校验（任何命中即需保留） ===')
    forbid_prefix = ['backend/routes/', 'backend/services/',
                     'management-web/src/', 'miniapp/', 'database/', 'docs/']
    bad = []
    for rel, kind, sz in candidates:
        # .pyc 在 __pycache__ 内属于缓存；其它位置才可疑
        if rel.split('/')[-2:-1] == ['__pycache__']:
            continue
        if any(rel.startswith(pp) for pp in forbid_prefix):
            bad.append(rel)
    p('   product_src_hits = %d %s' % (len(bad), bad if bad else ''))
    for key in ['FINAL_PROJECT_SEAL_REPORT', '.env.example', '.env']:
        hit = [rel for rel, _, _ in candidates if key in rel]
        p('   %-28s hits=%d %s' % (key, len(hit), hit if hit else ''))
    p()

    p('=== D. 各候选是否可证明为缓存/临时 ===')
    for rel, kind, sz in candidates:
        seg = rel.split('/')
        is_pyc_in_cache = len(seg) >= 2 and seg[-2] == '__pycache__' and kind == 'PYC'
        is_log = kind == 'LOG'
        verdict = 'CACHE_OK' if is_pyc_in_cache else ('LOG_RUNTIME' if is_log else 'NEEDS_REVIEW')
        p('   %-14s %s' % (verdict, rel))

    txt = '\n'.join(OUT)
    out = os.path.join(BASE, 'tests', 'security', '_out', '_seal_cache_audit.txt')
    with io.open(out, 'w', encoding='utf-8') as f:
        f.write(txt)
    print(txt)


if __name__ == '__main__':
    main()
