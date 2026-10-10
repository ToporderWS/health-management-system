# -*- coding: utf-8 -*-
"""封板报告口径修正：低风险已记录事项 3 -> 4（补记审核中心「医生账号」列宽）。"""
import io
import os
import sys

BASE = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system'
P = os.path.join(BASE, 'docs', 'FINAL_PROJECT_SEAL_REPORT.md')

PAIRS = [
    ("**真实未解决高风险缺陷 = 0；中风险缺陷 = 0；低风险已记录事项 = 3。**",
     "**真实未解决高风险缺陷 = 0；中风险缺陷 = 0；低风险已记录事项 = 4。**"),
    ("真实未解决低风险缺陷              = 3（见 §十，已记录，不阻塞）",
     "真实未解决低风险缺陷              = 4（见 §十，已记录，不阻塞）"),
    ("> 另：`UNCONFIRMED` 保留的 3 个账号",
     "| 4 | 审核中心「医生账号」列固定 `width=\"130\"`，18 字符账号折行 | 低 | 纯 UI 观感问题，**不影响运行 / 安全 / 数据完整性**。建议：放宽列宽或改用 `min-width`。 |\n\n> 另：`UNCONFIRMED` 保留的 3 个账号"),
]


def main():
    txt = open(P, 'rb').read().decode('utf-8')
    for i, (a, b) in enumerate(PAIRS, 1):
        n = txt.count(a)
        print('  anchor#%d count=%d %s' % (i, n, 'OK' if n == 1 else 'ABORT'))
        if n != 1:
            print('未命中 -> 整文件不改')
            return 3
    for a, b in PAIRS:
        txt = txt.replace(a, b, 1)
    with open(P, 'wb') as f:
        f.write(txt.encode('utf-8'))
    print('FINAL_PROJECT_SEAL_REPORT.md 已更新')
    return 0


if __name__ == '__main__':
    sys.exit(main())
