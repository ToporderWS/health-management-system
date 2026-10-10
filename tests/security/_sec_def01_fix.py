# -*- coding: utf-8 -*-
"""
DEF-01 最小修复：把误置在 management-web/ 根目录的一次性验证脚手架
迁出产品工程目录 -> tests/manual-probes/，并删除纯 Python 编译缓存。

红线：
  * 仅操作显式白名单内的 35 个文件 + 2 个目录（_verify_out / __pycache__）。
  * 白名单外出现任何非产品项 -> 整批中止，一个都不动。
  * 产品资产（.env.* / index.html / package.json / package-lock.json /
    vite.config.js / src / public / dist / node_modules）绝不触碰。
  * 不触碰 src/ 内文件、不触碰数据库、不触碰 miniapp/backend。
"""
import os
import sys
import json
import hashlib
import shutil
import io

BASE = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system'
MW = os.path.join(BASE, 'management-web')
DEST = os.path.join(BASE, 'tests', 'manual-probes')
OUT = os.path.join(BASE, 'tests', 'security', '_out')

# ---- 产品资产白名单（必须原地保留，任何情况下不动）----
KEEP = {
    '.env.development', '.env.production',
    'index.html', 'package.json', 'package-lock.json', 'vite.config.js',
    'src', 'public', 'dist', 'node_modules',
}

# ---- 待迁移的一次性脚手架（顶层文件，名称必须完全一致）----
MOVE_FILES = [
    '_append_mem.py', '_append_mem2.py', '_append_mem3.py',
    '_build2.log',
    '_cmp_pixels.py',
    '_diag_fps.py', '_diag_overflow.py', '_diag_perf.py', '_diag_perf2.py',
    '_fix_anim_place.py', '_fix_verify.py', '_fix_verify2.py', '_fix_verify3.py',
    '_measure.log', '_measure_anim_delta.py', '_mem.log',
    '_patch_anim.py', '_patch_verify2.py', '_prep_illustrations.py',
    '_probe2.log', '_probe3.log',
    '_probe_click.py', '_probe_login.py', '_probe_login2.py', '_probe_login3.py',
    '_run_build2.py',
    '_shot_audit.py', '_shot_login.log', '_shot_login.py',
    '_tune_anim.py',
    '_verify_anim.py', '_verify_login.py', '_verify_portal.py',
    'anim_run4.log', 'login_verify.log',
]

# ---- 待迁移的目录（整体搬迁，保留验证证据）----
MOVE_DIRS = ['_verify_out']

# ---- 待删除的纯缓存目录（可再生成）----
DELETE_DIRS = ['__pycache__']

# ---- 含明文测试登录口令的 7 个文件（重点取证，必须在迁移清单内）----
PLAINTEXT = [
    '_probe_click.py', '_probe_login.py', '_probe_login3.py',
    '_shot_audit.py', '_verify_login.py', '_probe3.log', 'login_verify.log',
]


def sha256(fp):
    h = hashlib.sha256()
    with open(fp, 'rb') as f:
        for b in iter(lambda: f.read(65536), b''):
            h.update(b)
    return h.hexdigest()


def main():
    apply = '--apply' in sys.argv
    log = []
    log.append('MODE = %s' % ('APPLY' if apply else 'DRY-RUN'))
    log.append('SRC  = %s' % MW)
    log.append('DEST = %s' % DEST)
    log.append('')

    # ===== 0. 前置校验：确认白名单文件确实存在；确认白名单外无遗漏脚手架 =====
    missing = [f for f in MOVE_FILES if not os.path.isfile(os.path.join(MW, f))]
    log.append('[0] 清单文件缺失: %s' % (missing if missing else '无'))

    actual = set(os.listdir(MW))
    known_move = set(MOVE_FILES) | set(MOVE_DIRS) | set(DELETE_DIRS)
    unexpected = sorted(actual - KEEP - known_move)
    log.append('[0] 白名单外未识别顶层项: %s' % (unexpected if unexpected else '无'))
    if missing or unexpected:
        log.append('!! 守卫失败 -> 整批中止，不执行任何操作')
        print('\n'.join(log))
        return 2

    # ===== 1. 前置取证：7 个明文口令文件 sha256 + 命中行 =====
    log.append('')
    log.append('[1] 明文口令文件取证（迁移前）')
    ev = {}
    for f in PLAINTEXT:
        fp = os.path.join(MW, f)
        hits = []
        try:
            raw = open(fp, 'rb').read()
            txt = raw.decode('utf-8', 'replace')
            for i, line in enumerate(txt.splitlines(), 1):
                if '123456' in line:
                    hits.append({'line': i, 'text': line.strip()[:160]})
        except Exception as e:
            hits = [{'error': str(e)}]
        item = {'file': f, 'sha256': sha256(fp), 'size': os.path.getsize(fp), 'hits': hits}
        ev[f] = item
        log.append('  %-20s sha256=%s size=%d hit_lines=%d' % (f, item['sha256'][:16], item['size'], len(hits)))
    with io.open(os.path.join(OUT, 'DEF01_PLAINTEXT_EVIDENCE.json'), 'w', encoding='utf-8') as fp:
        fp.write(json.dumps(ev, ensure_ascii=False, indent=2))

    # ===== 2. 建立目标目录 =====
    log.append('')
    if apply:
        os.makedirs(DEST, exist_ok=True)
        log.append('[2] 目标目录已建立: %s' % DEST)
    else:
        log.append('[2] 将建立目标目录: %s' % DEST)

    # ===== 3. 迁移文件 =====
    log.append('')
    log.append('[3] 迁移文件 (%d 个)' % len(MOVE_FILES))
    moved, mfail = [], []
    for f in MOVE_FILES:
        src = os.path.join(MW, f)
        dst = os.path.join(DEST, f)
        if apply:
            try:
                if os.path.exists(dst):
                    os.remove(dst)
                shutil.move(src, dst)
                moved.append(f)
            except Exception as e:
                mfail.append((f, str(e)))
                log.append('    FAIL move %s -> %s' % (f, e))
        else:
            log.append('    (dry) move %s' % f)
    log.append('    迁移成功 %d / 失败 %d' % (len(moved) if apply else len(MOVE_FILES), len(mfail)))

    # ===== 4. 迁移目录 =====
    log.append('')
    log.append('[4] 迁移目录 (%d 个)' % len(MOVE_DIRS))
    for d in MOVE_DIRS:
        src = os.path.join(MW, d)
        dst = os.path.join(DEST, d)
        n = sum(len(fs) for _, _, fs in os.walk(src))
        if apply:
            try:
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.move(src, dst)
                log.append('    move %s (%d files) OK' % (d, n))
            except Exception as e:
                log.append('    FAIL move %s -> %s' % (d, e))
        else:
            log.append('    (dry) move %s (%d files)' % (d, n))

    # ===== 5. 删除纯缓存 =====
    log.append('')
    log.append('[5] 删除纯 Python 编译缓存 (%d 个)' % len(DELETE_DIRS))
    for d in DELETE_DIRS:
        src = os.path.join(MW, d)
        n = sum(len(fs) for _, _, fs in os.walk(src))
        if apply:
            try:
                shutil.rmtree(src)
                log.append('    rmtree %s (%d files) OK' % (d, n))
            except Exception as e:
                log.append('    FAIL rmtree %s -> %s' % (d, e))
        else:
            log.append('    (dry) rmtree %s (%d files)' % (d, n))

    # ===== 6. 后置校验 =====
    if apply:
        log.append('')
        log.append('[6] 后置校验')
        left = sorted(os.listdir(MW))
        log.append('    management-web 剩余顶层项: %s' % left)
        residual = [x for x in left if x.startswith('_') or x.endswith('.log')]
        log.append('    残留脚手架: %s' % (residual if residual else '无 ✓'))
        log.append('    __pycache__ 存在: %s' % os.path.exists(os.path.join(MW, '__pycache__')))
        log.append('    dest 顶层项数: %d' % len(os.listdir(DEST)))

    print('\n'.join(log))
    return 0


if __name__ == '__main__':
    sys.exit(main())
