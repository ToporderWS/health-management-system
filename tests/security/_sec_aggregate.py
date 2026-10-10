# -*- coding: utf-8 -*-
"""把 sec_A..sec_K 的结果 JSON 聚合成 Markdown 明细（用于最终报告）。"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '_out')

TITLES = {
    'A': 'A 四角色 Token 越权隔离',
    'B': 'B 医生-患者数据隔离',
    'C': 'C 教练-学员数据隔离',
    'D': 'D 注册审核状态机',
    'E': 'E 注册异常场景',
    'F': 'F 登录异常场景',
    'G': 'G 数据所有权（越权读写他人数据）',
    'H': 'H 管理员监管权限边界',
    'I': 'I 操作日志',
    'J': 'J HTTP / 异常稳定性',
    'K': 'K 静态安全扫描',
}


def esc(s):
    if s is None:
        return ''
    return str(s).replace('|', '\\|').replace('\n', ' ').strip()


def main():
    lines = []
    grand = 0
    grand_pass = 0
    # 汇总表
    lines.append('## 一、分专项汇总\n')
    lines.append('| 专项 | 名称 | 用例数 | PASS | FAIL | 结论 |')
    lines.append('|---|---|---:|---:|---:|---|')
    detail = []
    for g in 'ABCDEFGHIJK':
        p = os.path.join(OUT, 'sec_%s.json' % g)
        cases = json.load(io.open(p, encoding='utf-8')) if os.path.exists(p) else []
        n = len(cases)
        ps = sum(1 for c in cases if c.get('passed'))
        fl = n - ps
        grand += n
        grand_pass += ps
        lines.append('| %s | %s | %d | %d | %d | %s |' % (
            g, TITLES[g], n, ps, fl, 'PASS' if fl == 0 else 'FAIL'))
        detail.append((g, cases))
    lines.append('| **合计** | — | **%d** | **%d** | **%d** | **%s** |' % (
        grand, grand_pass, grand - grand_pass,
        'ALL PASS' if grand == grand_pass else 'HAS FAIL'))
    lines.append('')

    # 明细
    lines.append('## 二、逐条明细\n')
    for g, cases in detail:
        lines.append('### %s. %s（%d/%d PASS）\n' % (
            g, TITLES[g], sum(1 for c in cases if c.get('passed')), len(cases)))
        lines.append('| 编号 | 角色 | 目标 | 期望 | HTTP | code | 结果 |')
        lines.append('|---|---|---|---|---:|---:|---|')
        for c in cases:
            lines.append('| %s | %s | %s | %s | %s | %s | %s |' % (
                esc(c.get('id')), esc(c.get('role')), esc(c.get('goal')),
                esc(c.get('expect')), esc(c.get('http')), esc(c.get('code')),
                'PASS' if c.get('passed') else '**FAIL**'))
        fails = [c for c in cases if not c.get('passed')]
        if fails:
            lines.append('')
            lines.append('失败项说明：')
            for c in fails:
                lines.append('- `%s`：实际 msg=%s；备注=%s' % (
                    esc(c.get('id')), esc(c.get('msg')), esc(c.get('note'))))
        lines.append('')

    txt = '\n'.join(lines)
    dst = os.path.join(OUT, 'SEC_DETAIL.md')
    io.open(dst, 'w', encoding='utf-8').write(txt)
    sys.stdout.write('written %s (%d bytes); TOTAL %d/%d PASS\n' % (
        dst, len(txt.encode('utf-8')), grand_pass, grand))


if __name__ == '__main__':
    main()
