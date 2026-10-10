# -*- coding: utf-8 -*-
"""工程卫生 · 缓存小批次逐文件清理（每批 <=8，禁用递归删除）。

用法：
  python _seal_cache_clean.py del <rel_file> [rel_file ...]   # 最多 8 个
  python _seal_cache_clean.py rmdir <rel_dir> [rel_dir ...]   # 仅删除空目录，最多 8 个

守卫（fail-closed，任一不满足整批中止、一个都不删）：
  del   : 必须是 .pyc/.pyo，且父目录名必须为 __pycache__
  rmdir : 目录必须为空
"""
import io
import os
import sys

BASE = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system'
LIMIT = 8
OUT = os.path.join(BASE, 'tests', 'security', '_out')


def log(lines):
    txt = '\n'.join(lines)
    os.makedirs(OUT, exist_ok=True)
    with io.open(os.path.join(OUT, '_seal_cache_clean.txt'), 'a', encoding='utf-8') as f:
        f.write(txt + '\n')
    print(txt)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'del'
    rels = sys.argv[2:]
    if not rels:
        log(['NO_TARGET'])
        return 1
    if len(rels) > LIMIT:
        log(['ABORT_BATCH_TOO_LARGE n=%d > %d' % (len(rels), LIMIT)])
        return 1

    lines = ['---- %s batch n=%d ----' % (mode, len(rels))]
    plans = []
    abort = False
    for rel in rels:
        p = os.path.join(BASE, rel.replace('/', os.sep))
        if mode == 'del':
            ok = os.path.isfile(p) and rel.lower().endswith(('.pyc', '.pyo')) \
                and os.path.basename(os.path.dirname(p)) == '__pycache__'
            why = '' if ok else 'NOT_PYC_IN_PYCACHE'
            lines.append('  %-6s %s %s' % ('CHECK' if ok else 'REJECT', rel, why))
            if ok:
                plans.append(p)
            else:
                abort = True
        else:  # rmdir
            ok = os.path.isdir(p) and not os.listdir(p)
            why = '' if ok else ('NOT_DIR' if not os.path.isdir(p) else 'NOT_EMPTY')
            lines.append('  %-6s %s %s' % ('CHECK' if ok else 'REJECT', rel, why))
            if ok and os.path.isdir(p):
                plans.append(p)
            else:
                abort = True

    if abort:
        lines.append('>> GUARD_ABORT：存在不合格目标，整批未执行')
        log(lines)
        return 1

    done = 0
    for p in plans:
        try:
            if mode == 'del':
                os.remove(p)
            else:
                os.rmdir(p)
            done += 1
            lines.append('  OK  %s' % os.path.relpath(p, BASE).replace('\\', '/'))
        except Exception as e:
            lines.append('  ERR %s -> %s: %s' % (os.path.relpath(p, BASE).replace('\\', '/'),
                                                 type(e).__name__, e))
    lines.append('>> DELETED=%d / %d' % (done, len(plans)))
    log(lines)
    return 0 if done == len(plans) else 1


if __name__ == '__main__':
    sys.exit(main())
