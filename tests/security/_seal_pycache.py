# -*- coding: utf-8 -*-
"""工程卫生 · __pycache__ 缓存清理（白名单 fail-closed）。

用法：
  python _seal_pycache.py dry <rel_dir> [rel_dir ...]
  python _seal_pycache.py apply <rel_dir> [rel_dir ...]

守卫：目录内**每一个**文件都必须是 .pyc/.pyo，否则整批中止、一个都不删。
"""
import io
import os
import sys
import shutil

BASE = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system'
ALLOW = ('.pyc', '.pyo')


def scan(rel):
    p = os.path.join(BASE, rel)
    if not os.path.isdir(p):
        return None, [], 0
    bad, cnt = [], 0
    for r, ds, fs in os.walk(p):
        for f in fs:
            cnt += 1
            if not f.lower().endswith(ALLOW):
                bad.append(os.path.relpath(os.path.join(r, f), BASE).replace('\\', '/'))
    return p, bad, cnt


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'dry'
    rels = sys.argv[2:]
    lines = []
    abort = False
    for rel in rels:
        p, bad, cnt = scan(rel)
        if p is None:
            lines.append('MISSING  %s' % rel)
            continue
        if bad:
            abort = True
            lines.append('ABORT    %s  非缓存文件: %s' % (rel, bad[:5]))
        else:
            lines.append('OK       %-40s files=%d' % (rel, cnt))
    lines.append('TOTAL_SCANNED_DIRS=%d  ABORT=%s' % (len(rels), abort))
    if abort:
        lines.append('>> 检测到非缓存文件，整批中止，未删除任何内容')
    elif mode == 'apply':
        for rel in rels:
            p, bad, cnt = scan(rel)
            if p is None:
                continue
            shutil.rmtree(p, ignore_errors=True)
            left = os.path.isdir(p)
            lines.append('DELETED  %-40s existed_after=%s' % (rel, left))
    out = os.path.join(BASE, 'tests', 'security', '_out', '_seal_pycache_%s.txt' % mode)
    with io.open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print('\n'.join(lines))
    return 1 if abort else 0


if __name__ == '__main__':
    sys.exit(main())
