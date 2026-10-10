# -*- coding: utf-8 -*-
"""
修复 _patch_anim.py 的插入位置错误：
  上一次误用 replace(B, BLOCK + '\n' + B)，把动画段插进了 .portal__bg-veil 的
  background 声明内部（锚点 B 落在一条声明的中间）。

本脚本做两件事，均为"取出 + 移到正确位置"，不改动任何既有声明：
  1. 把误插在 veil 声明内部的动画段取出，改放到 veil 规则 `}` 之后。
  2. 把 reduced-motion 段从"max-height 媒体查询之前"移到文件末尾（`</style>` 之前）。
每一步都断言命中次数，任何异常立即中止且不写盘；写盘前校验 veil 规则字节级还原。
"""
import os
import sys

P = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system\management-web\src\views\portal\IdentitySelect.vue'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _patch_anim import INS_CSS_FX, INS_CSS_REDUCED  # noqa: E402  复用同一份文本

# veil 规则原始形态（修复后必须字节级存在）
VEIL_RULE = '''  background:
    linear-gradient(
      180deg,
      rgba(255, 255, 255, 0.4) 0%,
      rgba(255, 255, 255, 0.1) 26%,
      rgba(255, 255, 255, 0.04) 54%,
      rgba(255, 255, 255, 0.34) 100%
    ),
    radial-gradient(78% 44% at 50% 2%, rgba(255, 255, 255, 0.38), rgba(255, 255, 255, 0) 66%);
}'''

VEIL_TAIL = 'radial-gradient(78% 44% at 50% 2%, rgba(255, 255, 255, 0.38), rgba(255, 255, 255, 0) 66%);\n}\n'
TOP_COMMENT = '/* ================= 顶部 ================= */'
MAXH_BLOCK = ('@media (max-height: 700px) {\n'
              '  .portal__main {\n'
              '    justify-content: flex-start;\n'
              '  }\n'
              '}\n')


def main():
    raw = open(P, 'rb').read()
    src = raw.decode('utf-8')
    lf, crlf = src.count('\n'), src.count('\r\n')
    if crlf not in (0, lf):
        print('FATAL: 行尾混合')
        return 2
    eol = '\r\n' if crlf else '\n'
    norm = src.replace('\r\n', '\n')

    # ---------- 取证：当前误插形态 ----------
    mis = '),\n    \n' + INS_CSS_FX.strip('\n')[:40]
    print('misplaced marker present :', mis in norm)
    if mis not in norm:
        print('FATAL: 未检出预期的误插形态，中止（不做任何修改）')
        return 2

    n_fx = norm.count(INS_CSS_FX + '\n')
    n_red = norm.count(INS_CSS_REDUCED + '\n')
    print('fx block occurrences     :', n_fx)
    print('reduced block occurrences:', n_red)
    if (n_fx, n_red) != (1, 1):
        print('FATAL: 段落出现次数异常，中止')
        return 2

    # ---------- 1. 取出误插的动画段 ----------
    norm = norm.replace(INS_CSS_FX + '\n', '', 1)
    if VEIL_RULE not in norm:
        print('FATAL: 取出后 veil 规则未恢复原状，中止')
        return 2
    print('step1 veil rule restored : OK')

    # ---------- 1b. 放到 veil 规则之后 ----------
    if norm.count(VEIL_TAIL) != 1 or norm.count(TOP_COMMENT) != 1:
        print('FATAL: 目标锚点命中数异常，中止')
        return 2
    norm = norm.replace(VEIL_TAIL, VEIL_TAIL + '\n' + INS_CSS_FX.strip('\n') + '\n\n', 1)
    print('step1b fx moved after veil: OK')

    # ---------- 2. 取出 reduced-motion ----------
    norm = norm.replace(INS_CSS_REDUCED + '\n', '', 1)
    print('step2 reduced block pulled: OK')

    # ---------- 2b. 放到文件末尾（最后一个媒体查询之后、</style> 之前） ----------
    if norm.count(MAXH_BLOCK) != 1 or norm.count('}\n</style>') != 1:
        print('FATAL: 末尾锚点命中数异常，中止')
        return 2
    norm = norm.replace(MAXH_BLOCK, MAXH_BLOCK + '\n' + INS_CSS_REDUCED.strip('\n') + '\n', 1)
    print('step2b reduced block at end: OK')

    # ---------- 结构自检 ----------
    checks = {
        'veil 规则完整': VEIL_RULE in norm,
        'veil 之后紧跟动画段': VEIL_TAIL + '\n' + INS_CSS_FX.strip('\n') in norm,
        '顶部注释仍在': TOP_COMMENT in norm,
        'reduced 在 </style> 之前': norm.index('prefers-reduced-motion') > norm.index(MAXH_BLOCK)
                                    and norm.rindex('prefers-reduced-motion') < norm.index('</style>'),
        'keyframes 数=8': norm.count('@keyframes ') == 8,
        'fx 段唯一': norm.count(INS_CSS_FX.strip('\n')) == 1,
        'reduced 段唯一': norm.count(INS_CSS_REDUCED.strip('\n')) == 1,
        '残留 4 空格空行已消除': '),\n    \n' not in norm,
        '括号配平': norm.count('{') == norm.count('}'),
        '动画声明数=9': norm.count('\n  animation: ') == 9,
    }
    for k, v in checks.items():
        print('self-check %-26s %s' % (k, 'OK' if v else 'FAIL'))
    if not all(checks.values()):
        print('FATAL: 自检未通过 => 未写盘')
        return 2

    out = norm.replace('\n', eol) if eol == '\r\n' else norm
    with open(P, 'wb') as f:
        f.write(out.encode('utf-8'))
    print('written bytes: %d (was %d)' % (os.path.getsize(P), len(raw)))
    print('OK: 位置修复完成')
    return 0


if __name__ == '__main__':
    sys.exit(main())
