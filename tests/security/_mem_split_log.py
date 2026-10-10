# -*- coding: utf-8 -*-
"""向当日日志追加「MEMORY.md 拆分留痕」一条（幂等）。"""
import os

LOG = r'C:/Users/Toporder-WS/Desktop/项目/个人健康管理系统小程序/.workbuddy/memory/2026-10-02.md'
MARK = '### MEMORY.md 注入安全拆分（v1）'

ENTRY = '''
### MEMORY.md 注入安全拆分（v1）

- **触发**：MEMORY.md 达 14 805 bytes / 9 516 chars，超出注入安全线，注入时被截尾（会话开局丢判据）。
- **动作**（非破坏，未删除任何文件）：
  - 归档（byte-exact）`MEMORY-v1-full-archive-20261002.md`（14 805 B，sha256[:16]=a1f60a06b8a03ad6）
  - 正文另存 `MEMORY-DETAIL-v1.md`（同 14 805 B，同指纹）
  - `MEMORY.md` 重写为「判据 + 指针」索引：9 516 -> 3 281 chars（4 603 B，sha256[:16]=66ecccf4f0a81db4）
- **脚本**：`tests/security/_mem_split_v1.py`（含 ARC/DETAIL 逐字节复核 + 字符上限硬断言 + 读回复核）。
'''

def main():
    t = open(LOG, 'rb').read().decode('utf-8')
    if MARK in t:
        print('[SKIP] 已含拆分留痕')
        return
    with open(LOG, 'wb') as f:
        f.write((t.rstrip('\n') + '\n' + ENTRY.lstrip('\n')).encode('utf-8'))
    print('[LOG] 已追加；新大小 =', os.path.getsize(LOG), 'bytes')

if __name__ == '__main__':
    main()
