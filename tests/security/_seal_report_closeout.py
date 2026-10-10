# -*- coding: utf-8 -*-
"""最终封板 · 报告收口：
  1) docs/FINAL_REPORT.md —— 脱敏历史报告中的开发用 MySQL 口令字面量；
  2) docs/FINAL_SECURITY_ACCEPTANCE_REPORT.md —— 追加 §十四（第 5 版）并更新版本脚注。
锚点未命中恰 1 次则该文件整体不改。
"""
import io
import os
import sys

BASE = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system'

SEC14 = """## 十四、最终封板记录（第 5 版）

本轮在存量事项②（`JWT_SECRET` 轮换）通过后，一次性完成**历届测试残留精确清理 → `api_test` 防残留机制修复 → 工程卫生 → Secret 扫描 → 数据库完整性 → 四角色冒烟 → A~K 安全复验 → 全量回归 → 生产构建 → 文档同步**，并给出项目最终封板判定。

### 14.1 历届测试残留处置（§八 第 2 项闭环）

`users` 3~11 / `doctor_user` 4~16 / `coach_user` 4~11 等**共 30 个账号 + 51 行关联数据（合计 81 行）**，经多源交叉取证（`api_test.py` 账号生成规则、`username`/`nickname`、手机号段、`created_at`、命名前缀、外键关联、是否与真实实体绑定）逐条判定：

| 判定 | 数量 | 处置 |
|---|---|---|
| `TEST_RESIDUE_CONFIDENCE = CONFIRMED` | 30 个账号（81 行含关联业务/绑定） | **已精确删除**（dry-run → 白名单 → 五重守卫 → apply → 复核） |
| `UNCONFIRMED` | 3 个（`doctor_user` 17 `001` / 18 `003`、`coach_user` 12 `002`） | **保留**（创建时间 16:26–16:57，带人工管理端「资料修改 / 密码重置 / 审核」审计痕迹，与 `api_test` 无关） |

`admin_operation_log` 未删除任何记录（审计留痕按完整性原则保留）。

### 14.2 `api_test.py` 防残留机制（根因修复）

原 `api_test.py` 无任何清理逻辑（`cleanup` / `finally` 计数为 0），是历届残留的**根因**。已做**最小追加式修复**：

- 运行前记录基线；所有测试实体使用**唯一时间戳标识**（`139908`/`138908` 手机号段、`doc_test_`/`doc_reject_`/`doc_other_`/`coach_test_`/`coach_reject_` 命名前缀）；
- `main()` 改为 `try / finally`，`finally` 中执行**精确清理**（白名单 + 受保护实体硬守卫 + 二次所有权校验）；
- 只清理**本轮创建**的数据，绝不触碰运行前既有数据；清理失败即令测试报告 **FAIL**；
- 用例数由 198 增至 **199**（新增「本轮测试数据精确清理」断言），运行前后业务表计数 delta 全 0。

### 14.3 最终结果

| 项目 | 结果 |
|---|---|
| 历史测试残留（显式扫描） | **CLEAN**（CONFIRMED 全部删除、UNCONFIRMED 保留 3 个） |
| 本轮临时数据残留 | **0** |
| `backend_selfcheck.py` | **5 / 5 PASS** |
| `miniapp_check.py` | **23 / 23 PASS** |
| `web_check.py` | **33 / 33 PASS** |
| `api_test.py` | **199 / 199 PASS** |
| 权限 + 异常专项 A~K | **197 / 197 PASS** |
| 四角色真实冒烟 | **46 / 46 PASS** |
| `vite build`（production） | **PASS**（22.09s） |
| Secret 泄露扫描（含 dist） | **命中 0** |
| 数据库完整性 / 结构变更 | 19 表 · 指纹未变 · **DATABASE_SCHEMA_CHANGED = NO** |
| 受保护实体（含小周 10 类业务数据与两条绑定） | **PROTECTED_ALL_INTACT = True** |
| 工程卫生（`.gitignore` + 缓存清理） | **PASS**（4 份 `.gitignore`；`*.pyc` 缓存残留 0） |

```
DEF-01 = PASS
FINAL_SECURITY_ACCEPTANCE = PASS
STORAGE_ITEM_01_API_ADDRESS = PASS
STORAGE_ITEM_02_JWT_SECRET = PASS
PROJECT_FINAL_SEAL = PASS
```

> 完整封板正本见 **`docs/FINAL_PROJECT_SEAL_REPORT.md`**。
"""


def patch(path, pairs):
    full = os.path.join(BASE, path)
    txt = open(full, 'rb').read().decode('utf-8')
    for a, b in pairs:
        if txt.count(a) != 1:
            print('%s : 锚点命中 %d != 1，整文件未改' % (path, txt.count(a)))
            return False
    for a, b in pairs:
        txt = txt.replace(a, b, 1)
    with open(full, 'wb') as f:
        f.write(txt.encode('utf-8'))
    print('%s : 已更新（%d 处）' % (path, len(pairs)))
    return True


def main():
    import datetime
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    ok = True

    ok &= patch('docs/FINAL_REPORT.md', [
        ("- 本地开发使用 MySQL `root/123456` 与示例 `JWT_SECRET`，**仅限开发环境**，上线必须替换。",
         "- 本地开发数据库口令与 `JWT_SECRET` **仅限开发环境**，正式使用前必须替换（`JWT_SECRET` 已完成轮换，见安全验收报告 §十三）。"),
    ])

    ok &= patch('docs/FINAL_SECURITY_ACCEPTANCE_REPORT.md', [
        ("*报告第 1 版：2026-10-01 18:21 · 第 2 版（DEF-01 修复后复验）：2026-10-01 19:30 · 第 3 版（存量事项① 处置）：2026-10-01 19:46 · 第 4 版（存量事项② JWT_SECRET 轮换）：2026-10-01 20:15*",
         SEC14 + "\n---\n*报告第 1 版：2026-10-01 18:21 · 第 2 版（DEF-01 修复后复验）：2026-10-01 19:30 · 第 3 版（存量事项① 处置）：2026-10-01 19:46 · 第 4 版（存量事项② JWT_SECRET 轮换）：2026-10-01 20:15 · 第 5 版（历届残留清理 + 最终封板）：%s*" % now),
    ])

    print('REPORT_CLOSEOUT_OK =', ok)
    return 0 if ok else 3


if __name__ == '__main__':
    sys.exit(main())
