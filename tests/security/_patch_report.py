# -*- coding: utf-8 -*-
"""对报告做锚点式数值更正（每条锚点断言命中恰 1 次，任一未命中则整文件不改）。"""
import io
import sys

P = (r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system'
     r'\docs\FINAL_SECURITY_ACCEPTANCE_REPORT.md')

EDITS = [
    # 1) J 专项请求总数
    ('累计 **428 条真实请求**（A~J 全量留痕）复核：',
     '累计 **152 条真实请求**（A~J 同进程全量留痕）复核：'),
    # 2) 证据索引里的请求数
    ('| `tests/security/_out/_rerun_all2.txt` | A~J 全量执行日志（同进程累积 428 条请求） |',
     '| `tests/security/_out/_rerun_all2.txt` | A~J 全量执行日志（同进程累积 152 条请求） |'),
    # 3) sec_ 业务数据行数
    ('| 业务数据 | 健康记录 / 睡眠 / 运动 / 健康计划 / 医嘱 / 体检通知 / 医疗记录 / 运动目标 / 训练计划 / 健身建议 | 26 行 |',
     '| 业务数据 | 健康记录 / 睡眠 / 运动 / 健康计划 / 医嘱 / 体检通知 / 医疗记录 / 运动目标 / 训练计划 / 健身建议 | 24 行（含 G 专项越权写入验证产生的 2 行） |'),
    # 4) 清理结果里的行数
    ('- **阶段 1（`sec_` 实体）**：删除 3 用户 / 5 医生 / 4 教练 + 26 行业务数据，全部成功；',
     '- **阶段 1（`sec_` 实体）**：删除 3 用户 / 5 医生 / 4 教练 + 24 行业务数据 + 4 组绑定关系，全部成功；'),
]

raw = open(P, 'rb').read()
text = raw.decode('utf-8')
crlf = '\r\n' in text

problems = []
for i, (old, new) in enumerate(EDITS, 1):
    n = text.count(old)
    if n != 1:
        problems.append('EDIT#%d 锚点命中 %d 次（应为 1）：%s' % (i, n, old[:60]))

if problems:
    print('!! 未命中，整文件不改：')
    for p in problems:
        print('   ', p)
    sys.exit(1)

for old, new in EDITS:
    text = text.replace(old, new, 1)

open(P, 'wb').write(text.encode('utf-8'))
print('OK：%d 处更正已写入（行尾 %s）' % (len(EDITS), 'CRLF' if crlf else 'LF'))
