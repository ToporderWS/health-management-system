# -*- coding: utf-8 -*-
"""更新技能 sandbox-bulk-delete-quota-vs-test-teardown：补「缓存清理」变体与分批口径修正。"""
import os
import sys

P = r'C:\Users\Toporder-WS\.workbuddy\skills\sandbox-bulk-delete-quota-vs-test-teardown\SKILL.md'

NEW_SECTION = """## 变体：清理 `__pycache__` / 构建缓存（本工程实测）

要把仓库内缓存清到 **0** 时，同样受这条上限约束，且多**两个新坑**：

1. **删目录 = 按内层文件计数。** `shutil.rmtree('backend/utils/__pycache__')`（内含 9 个 `.pyc`）
   在沙箱看来是 **10 项**删除；几个目录一叠加就顶过 50 —— 实测"累计 53 > 阈值 50"被拒。
   ⇒ **先逐条删文件（`os.remove`），再删空目录**。
2. **缓存会再生。** 任何「应用导入」型测试（本工程 `tests/backend_selfcheck.py` 会 `import` Flask app）
   都会重新生成 `backend/**/__pycache__`（实测清 0 后又长出 26 个 `.pyc`）。
   ⇒ **必须在全部 Python 执行结束之后**再做最后一轮扫描 + 清理；扫描用**不会 import 产品代码**的解释器
   （本工程用托管 py3.13），否则越扫越多。

正确姿势（可复用脚本：`tests/security/_seal_cache_clean.py`）：

- `del <rel_file> ...`：**每批 ≤ 8**；守卫 = 后缀必须 `.pyc/.pyo` **且**父目录名必须 `__pycache__`，
  任一不合格 → **整批中止、一个都不删**（fail-closed）；
- `rmdir <rel_dir> ...`：**仅删空目录**（非空即拒）；
- **批次间重新枚举目标**，不要拿上一批的清单硬套；
- 先做**只读核对**并回答"是否命中产品源码 / `src` / `miniapp` / `database` / `docs` / 正式测试脚本 / `.env*` / 业务数据"，
  命中数必须全为 0 才动手。

判定：`*.pyc` 残留 0 **且** `__pycache__` 目录 0 才算清干净。
`backend/server.log` 这类**运行时日志**属 **SAFE_RETAINED**（被进程持有 + 已被 `*.log` 忽略），不要强行删。

"""

OLD_SECTION_ANCHOR = "## 收尾纪律"

BAD_NEW = ("- ❌ 「分批 ≤10 就能规避」——**当同轮累计总量 > 50 时不能**（累计口径）；"
           "若总量本身就 < 50（例：清 26 个 `.pyc`），按「逐文件 ≤ 8/批」分批是能正常跑完的 —— "
           "关键看**项数**（删目录要算内层文件），不是批次数。")
BAD_OLD = "- ❌ 「分批 ≤10 就能规避」——不能，累计口径。"

DESC_ADD = " Also covers the __pycache__/build-cache variant: deleting a directory counts its inner files, and caches REGENERATE after app-import tests, so the final sweep must run after all Python execution."


def main():
    with open(P, 'rb') as f:
        txt = f.read().decode('utf-8')

    checks = [(txt.count(OLD_SECTION_ANCHOR), 1, 'NEW_SECTION anchor'),
              (txt.count(BAD_OLD), 1, 'BAD_OLD anchor'),
              (txt.count(DESC_ADD), 0, 'desc not yet added')]
    ok = True
    for n, want, name in checks:
        if n != want:
            print('  %-22s count=%d want=%d -> ABORT' % (name, n, want))
            ok = False
    if not ok:
        print('SKILL_CLOSE 未命中 -> 整文件不改')
        return 3

    txt = txt.replace(OLD_SECTION_ANCHOR, NEW_SECTION + OLD_SECTION_ANCHOR, 1)
    txt = txt.replace(BAD_OLD, BAD_NEW, 1)
    # 描述补一句（插在 `agent_created: true` 前）
    lines = txt.split('\n')
    for i, l in enumerate(lines):
        if l.startswith('agent_created:'):
            lines[i - 1] = lines[i - 1].rstrip() + DESC_ADD
            break
    txt = '\n'.join(lines)

    with open(P, 'wb') as f:
        f.write(txt.encode('utf-8'))
    print('SKILL 已更新, chars =', len(txt))
    return 0


if __name__ == '__main__':
    sys.exit(main())
