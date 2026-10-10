# -*- coding: utf-8 -*-
"""封板收尾 · 记忆写入（项目 MEMORY.md 更新 + 当日日志追加）。"""
import io
import os
import sys

PROJ = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序'
MEM = os.path.join(PROJ, '.workbuddy', 'memory', 'MEMORY.md')
LOG = os.path.join(PROJ, '.workbuddy', 'memory', '2026-10-01.md')

MEM_PAIRS = [
    ("2. `api_test.py` 历届残留数据（users 3-11 / doctors 4-16 / coaches 4-11）；",
     "2. ~~`api_test.py` 历届残留数据（users 3-11 / doctors 4-16 / coaches 4-11）~~ ✅ **已解决**"
     "（2026-10-01 20:32，最终封板批）：31 个候选实体经多源交叉取证（命名规则/手机号/`created_at`/外键/审计日志），"
     "**CONFIRMED 30 个账号（含关联共 81 行）已精确删除**（dry-run→白名单→五重守卫→apply→复核，命中 81/跳过 0）；"
     "`doctor_user` 17 `001` / 18 `003`、`coach_user` 12 `002` 判定 **UNCONFIRMED 保留**（16:26–16:57 人工管理端"
     "「资料修改/密码重置/审核」痕迹，与 api_test 12:54–12:59 无关）；同时给 `api_test.py` 补了 `try/finally` "
     "精确清理机制（用例 198→**199**，运行前后业务表 delta 全 0）；"),
    ("5. 审核中心「医生账号」列 `width:130px` 偏窄，18 字符账号折行。",
     "5. 审核中心「医生账号」列 `width=\"130\"`（`views/admin/Audit.vue:30`）偏窄，18 字符账号折行 —— **仍开放**，"
     "已记入封板报告低风险项 #4（纯观感，不阻塞封板）。"),
]

MEM_APPEND = """
## 六、最终封板记录（2026-10-01 20:32 · PROJECT_FINAL_SEAL = PASS）

- **判定**：`DEF-01=PASS` / `FINAL_SECURITY_ACCEPTANCE=PASS` / `STORAGE_ITEM_01_API_ADDRESS=PASS` / `STORAGE_ITEM_02_JWT_SECRET=PASS` / **`PROJECT_FINAL_SEAL = PASS`**。正本：`docs/FINAL_PROJECT_SEAL_REPORT.md`（安全报告升至第 5 版 §十四）。
- **历届残留**：CONFIRMED 81 行已删、UNCONFIRMED 3 个保留、`TEMP_TEST_DATA_RESIDUE=0`；`admin_operation_log` 全程未删一条（审计留痕）。
- **回归**：backend_selfcheck **5/5** · miniapp **23/23** · web **33/33** · api_test **199/199** · 安全 A~K **197/197** · 四角色冒烟 **46/46** · vite build **PASS**(22.09s)。
- **数据**：`DATABASE_SCHEMA_CHANGED=NO`（19 表 / 139 列指纹未变）、`PROTECTED_ALL_INTACT=True`、16 张业务表 delta 全 0。

### 工程卫生铁律（本轮新增，后续必须遵守）

- **本工程原先一份 `.gitignore` 都没有**；现已建 4 份（根 / `backend` / `management-web` / `miniapp`）。
  根 `.gitignore` **刻意不收窄 `_out/`**，以免误伤 `tests/security/_out/`（正式验收证据）。
- **清理缓存必须小批次逐文件**：`__pycache__` 目录删除会被沙箱按**内层文件数**计入阈值（曾触发「累计 53 > 阈值 50」被拒）。
  正解 = `tests/security/_seal_cache_clean.py`（`del` 逐文件 ≤8/批、`rmdir` 仅删空目录；守卫：必须是 `.pyc`/`.pyo` 且父目录名为 `__pycache__`，任一不合格整批中止），**禁用 `shutil.rmtree`**。
- **缓存会再生**：`backend_selfcheck.py` 会「应用导入」⇒ 重新生成 `backend/**/__pycache__`；**封板前必须在所有 Python 执行完成后**做最后一轮扫描+清理（用托管 py3.13 扫，避免再次触发）。
- **运行时日志 `backend/server.log` 属 SAFE_RETAINED**（被 Flask 持有 + 已被 `*.log` 忽略），不删。
- **`tests/manual-probes/`（DEF-01 隔离区）与 `tests/security/_out/`（正式证据）一律保留**，不因「清洁工程」删除。

### 封板批新增测试资产（tests/security/，非产品代码）

`_seal_recon.py` / `_seal_recon2.py`（只读侦察）· `_seal_baseline.py` · `_seal_cleanup.py`（残留精确清理）·
`_seal_verify.py`（清理后复核）· `_seal_run_apitest.py`（防残留验证）· `_seal_cache_audit.py` / `_seal_cache_clean.py`（缓存核对与分批清理）·
`_seal_secret_scan.py`（分层敏感扫描，硬性项须全 0）· `_seal_smoke_final.py`（四角色 46 项冒烟）·
`_seal_front_audit.py` · `_seal_doc_sync.py` / `_seal_report_closeout.py` / `_seal_report_fixup.py`（文档锚点回写）。

### 遗留低风险（4 项，已记录不阻塞）

① `admin_operation_log` 随每轮 `api_test` +约 39 行（审计表，不可删）② 开发环境 MySQL 弱口令（仅本地，`.env` 不入库）
③ `tests/manual-probes/` 保留 49 项历史脚手架 + `tests/security/_out/` 证据（按规则保留）④ 审核中心「医生账号」列宽 130 偏窄。
"""

LOG_APPEND = """
## ★ 最终封板：PROJECT_FINAL_SEAL = PASS（2026-10-01 20:32）

- **缓存删除被沙箱拦截后的处置**：用户取消了一批累计 53 项的删除（阈值 50）。按要求改为**只读核对 + 小批次（≤8/批）逐文件**：产品目录缓存候选**全部为 `backend/**/__pycache__` 内的 `*.pyc`**，禁列（产品源码 / `src` / `miniapp` / `database` / `docs` / 正式测试脚本 / `FINAL_PROJECT_SEAL_REPORT` / `.env*` / 业务数据）**命中全为 0**；`backend/server.log` 记为 **SAFE_RETAINED**。分批清理后 `*.pyc` 残留 0；回归运行再生 26 个 `.pyc` 后再次 4 批清空。
- **历届残留闭环**：`_seal_cleanup.py` 精确删除 **81 行**（30 账号 + 51 关联），跳过 0；UNCONFIRMED 3 个（doctor 17/18、coach 12）保留。清理前后 `admin_operation_log` 一条未删。
- **api_test 防残留机制修复**：`api_test.py` 追加 `try/finally` 精确清理（唯一时间戳标识 + 保护白名单 + 二次所有权校验），实测 **199/199 PASS**、业务表 delta 全 0。
- **工程卫生**：新建 4 份 `.gitignore`（根/backend/management-web/miniapp），覆盖 `.env`/`.venv`/`node_modules`/`dist`/`unpackage`/`__pycache__`/`*.py[cod]`/`*.log`/`_verify_out`/`*_verify_out`/`.idea`/`.vscode`，并在 `management-web` 追加 `_*.py`/`_*.log`/`_verify_out/`/`_out/` 防历史脚手架回流。
- **敏感扫描（分层，硬性项须全 0）**：旧 Secret 0 · 新 Secret（`.env` 外）0 · bcrypt 0 · `Bearer eyJ…` 0 · 产品范围 DB 密码 0 · `192.168.1.4` 0 · `192.168.2.219`（除 `miniapp/common/config.js`）0 · `:5000/:5001` 0 · traceback/SQL 0 · **dist 68 文件全 0** ⇒ `SECRET_SCAN_HARD_ALL_ZERO = YES`。
- **数据库完整性**：19 表 / 指纹未变 / 无孤儿 / `sec_` 与 api_test 临时数据 0 / 小周 10 类业务 + 两条绑定 INTACT。
- **回归**：自检 5/5 · 小程序 23/23 · web 33/33 · api_test 199/199 · **A~K 197/197**（A29 B18 C16 D20 E16 F24 G16 H19 I17 J7 K15）· **四角色冒烟 46/46** · vite build PASS(22.09s)。admin 一级模块 **12 个**（`router/admin.js::adminMenus`）未增未减。
- **文档同步（锚点回写，每条断言命中恰 1 次）**：README（9 处 + 新增 §二十三/§二十四）、`docs/API.md`（2 处）、`docs/DATABASE.md`（1 处）、`docs/TEST_REPORT.md`（3 处）、`docs/FINAL_REPORT.md`（历史开发口令脱敏 1 处）、`docs/FINAL_SECURITY_ACCEPTANCE_REPORT.md`（追加 §十四 第 5 版）；**新建 `docs/FINAL_PROJECT_SEAL_REPORT.md`**。
- **判定**：`PROJECT_FINAL_SEAL = PASS`；未解决高/中风险 = 0，低风险已记录 = 4（见封板报告 §十）。**《个人健康管理系统 V3.2 FINAL》已完成最终封板。**
"""


def patch_memory():
    raw = open(MEM, 'rb').read().decode('utf-8')
    nl = '\r\n' if '\r\n' in raw else '\n'
    for i, (a, b) in enumerate(MEM_PAIRS, 1):
        n = raw.count(a)
        print('MEM anchor#%d count=%d %s' % (i, n, 'OK' if n == 1 else 'ABORT'))
        if n != 1:
            print('MEMORY.md 未命中 -> 整文件不改')
            return False
    for a, b in MEM_PAIRS:
        raw = raw.replace(a, b, 1)
    if not raw.endswith(nl):
        raw += nl
    raw += MEM_APPEND.replace('\n', nl)
    open(MEM, 'wb').write(raw.encode('utf-8'))
    print('MEMORY.md 已更新, chars =', len(raw))
    return True


def append_log():
    raw = open(LOG, 'rb').read().decode('utf-8')
    nl = '\r\n' if '\r\n' in raw else '\n'
    if not raw.endswith(nl):
        raw += nl
    raw += LOG_APPEND.replace('\n', nl)
    open(LOG, 'wb').write(raw.encode('utf-8'))
    print('2026-10-01.md 已追加, chars =', len(raw))
    return True


if __name__ == '__main__':
    ok = patch_memory()
    ok &= append_log()
    print('MEMORY_WRITE_OK =', ok)
    sys.exit(0 if ok else 3)
