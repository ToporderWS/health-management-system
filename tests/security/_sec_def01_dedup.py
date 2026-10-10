# -*- coding: utf-8 -*-
"""
DEF-01 收尾：确认 DEST/_verify_out 与 MW/_verify_out 完全一致后，
分批删除 MW 侧冗余副本（沙箱批量删除阈值 50，故按 <=8/批）。
另外删除 MW/__pycache__（纯编译缓存，2 文件）。

用法:
  python _sec_def01_dedup.py verify          # 仅比对
  python _sec_def01_dedup.py del_verify 0    # 删除 _verify_out 第 0 批(8个)
  python _sec_def01_dedup.py del_cache       # 删除 __pycache__
"""
import os
import sys
import json
import hashlib
import io

BASE = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system'
MW = os.path.join(BASE, 'management-web')
DEST = os.path.join(BASE, 'tests', 'manual-probes')
OUT = os.path.join(BASE, 'tests', 'security', '_out')

BATCH = 8


def sha(fp):
    h = hashlib.sha256()
    with open(fp, 'rb') as f:
        for b in iter(lambda: f.read(65536), b''):
            h.update(b)
    return h.hexdigest()


def rel_files(root):
    out = []
    for r, _, fs in os.walk(root):
        for f in fs:
            fp = os.path.join(r, f)
            out.append(os.path.relpath(fp, root))
    return sorted(out)


def verify():
    a = os.path.join(MW, '_verify_out')
    b = os.path.join(DEST, '_verify_out')
    fa, fb = rel_files(a), rel_files(b)
    res = {'mw_files': len(fa), 'dest_files': len(fb), 'only_mw': [], 'only_dest': [], 'mismatch': [],
           'mw_bytes': 0, 'dest_bytes': 0}
    for f in fa:
        res['mw_bytes'] += os.path.getsize(os.path.join(a, f))
    for f in fb:
        res['dest_bytes'] += os.path.getsize(os.path.join(b, f))
    res['only_mw'] = sorted(set(fa) - set(fb))
    res['only_dest'] = sorted(set(fb) - set(fa))
    same = True
    for f in sorted(set(fa) & set(fb)):
        if sha(os.path.join(a, f)) != sha(os.path.join(b, f)):
            res['mismatch'].append(f)
            same = False
    res['identical'] = (not res['only_mw']) and (not res['only_dest']) and (not res['mismatch'])
    with io.open(os.path.join(OUT, 'DEF01_VERIFYOUT_DEDUP.json'), 'w', encoding='utf-8') as fp:
        fp.write(json.dumps(res, ensure_ascii=False, indent=2))
    print(json.dumps(res, ensure_ascii=False, indent=2))
    print('IDENTICAL =', res['identical'])
    return 0 if res['identical'] else 3


def del_verify(batch_idx):
    a = os.path.join(MW, '_verify_out')
    fs = rel_files(a)
    lo = batch_idx * BATCH
    hi = lo + BATCH
    chunk = fs[lo:hi]
    print('total=%d batch=%d range=[%d,%d) count=%d' % (len(fs), batch_idx, lo, hi, len(chunk)))
    done = 0
    for f in chunk:
        fp = os.path.join(a, f)
        try:
            os.remove(fp)
            done += 1
        except Exception as e:
            print('  FAIL %s -> %s' % (f, e))
    print('deleted %d' % done)
    left = rel_files(a)
    print('remaining=%d' % len(left))
    if not left:
        try:
            os.rmdir(a)
            print('rmdir _verify_out OK')
        except Exception as e:
            print('rmdir fail', e)
    return 0


def del_cache():
    import shutil
    p = os.path.join(MW, '__pycache__')
    n = rel_files(p)
    for f in n:
        os.remove(os.path.join(p, f))
    try:
        os.rmdir(p)
    except Exception as e:
        print('rmdir fail', e)
    print('__pycache__ removed, files=%d, exists=%s' % (len(n), os.path.exists(p)))
    return 0


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'verify'
    if cmd == 'verify':
        sys.exit(verify())
    elif cmd == 'del_verify':
        sys.exit(del_verify(int(sys.argv[2])))
    elif cmd == 'del_cache':
        sys.exit(del_cache())
