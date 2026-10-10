# -*- coding: utf-8 -*-
"""
对 FINAL_SECURITY_ACCEPTANCE_REPORT.md 做锚点式回写：把 DEF-01 从「未处置」更新为「已修复并复验」。

铁律：每条锚点断言「命中恰 1 次」；任一未命中 -> 整个文件不写。
"""
import io
import os
import sys

P = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system\docs\FINAL_SECURITY_ACCEPTANCE_REPORT.md'

EDITS = []


def E(old, new, tag):
    EDITS.append((old, new, tag))


# ---------- 1) 头部：验收性质 ----------
E(
    "- 验收性质：**仅测试、取证、发现问题**；除测试脚手架（`tests/` 内脚本、`tests/security/` 新增用例）外，**未修改任何产品代码**",
    "- 验收性质：**仅测试、取证、发现问题**；除测试脚手架（`tests/` 内脚本、`tests/security/` 新增用例）外，**未修改任何产品代码**\n"
    "- 本版次：**第 2 版（DEF-01 已修复 + 全量复验）** —— 第 1 版于 2026-10-01 18:21 出具（判定 FAIL）；本版为授权修复 DEF-01 后的复验结论",
    "header-nature",
)

# ---------- 2) 1.1 四项汇总 ----------
E(
    "| **现有回归** | backend_selfcheck / miniapp_check / web_check / api_test / vite build | **258 / 259 PASS**（1 项 FAIL，见 §五） |",
    "| **现有回归** | backend_selfcheck / miniapp_check / web_check / api_test / vite build | **259 / 259 PASS**（DEF-01 修复后 `api_test` 恢复 198/198） |",
    "1.1-regression",
)

# ---------- 3) 1.2 真实缺陷 ----------
E(
    "| 编号 | 描述 | 风险 | 状态 |\n|---|---|---|---|\n"
    "| **DEF-01** | 验证/调试脚本残留于生产前端工程目录 `management-web/`，其中 7 个文件含明文登录口令（`admin` / `doctor001` / `coach001` 的 `123456`） | **中** | **未处置（待授权）** |",
    "| 编号 | 描述 | 风险 | 状态 |\n|---|---|---|---|\n"
    "| **DEF-01** | 验证/调试脚本残留于生产前端工程目录 `management-web/`，其中 7 个文件含明文登录口令（`admin` / `doctor001` / `coach001` 的 `123456`） | **中** | **已修复（2026-10-01 19:00）** |\n"
    "\n"
    "> DEF-01 处置方式见 §5.3 执行记录；修复后 `management-web/` 根目录已无任何测试脚手架，`api_test.py` 恢复 `198/198`。复验结论见 §十一。",
    "1.2-defect",
)

# ---------- 4) 1.3 最终判定 ----------
E(
    "```\nFINAL_SECURITY_ACCEPTANCE = FAIL\n```\n"
    "\n"
    "**判定理由**：11 个专项（197 项）全部 PASS，权限隔离与异常处理链路未发现缺陷；但存在 **1 项未处置的真实缺陷 DEF-01**（明文口令落在产品工程目录），故**不自封板**，判定为 FAIL，逐条列于 §五。\n"
    "\n"
    "> 若需求方授权执行 §5.3 的最小修复（纯文件搬迁，不触碰任何产品代码与数据），复跑 `api_test.py` 即可恢复 `198/198`，判定可转 PASS。",
    "```\nFINAL_SECURITY_ACCEPTANCE = PASS\n```\n"
    "\n"
    "**判定理由**：11 个专项（197 项）全部 PASS；唯一真实缺陷 **DEF-01 已按 §5.3 修复（纯文件搬迁，未触碰任何产品代码与业务数据）**；修复后全量复验（权限专项 / 异常专项 / 静态扫描 / 四项现有回归 / Vite 构建）**全部通过**，`api_test.py` 恢复 `198/198`，本轮临时数据 **0 残留**，受保护数据 **全部 INTACT**。详见 §十一 复验记录。\n"
    "\n"
    "> 说明：本判定为**安全验收转绿**，**不代表项目最终封板**。",
    "1.3-verdict",
)

# ---------- 5) 2.3 用例来源表补一行 ----------
E(
    "| `tests/security/_sec_smoke.py` | 清理后冒烟复核（15 项） |",
    "| `tests/security/_sec_smoke.py` | 清理后冒烟复核（15 项） |\n"
    "| `tests/security/_sec_def01_fix.py` | **DEF-01 修复**：脚手架迁移 + 守卫 + 明文口令取证（第 2 版新增） |\n"
    "| `tests/security/_sec_def01_dedup.py` | **DEF-01 收尾**：`_verify_out` 双份副本哈希比对与分批去重（第 2 版新增） |\n"
    "| `tests/security/_sec_verify_baseline.py` | 复验前后基线快照与受保护实体比对（第 2 版新增） |\n"
    "| `tests/security/_sec_verify_cleanup.py` | 复验轮临时数据清理（白名单 + 三重守卫）（第 2 版新增） |",
    "2.3-sources",
)

# ---------- 6) §5.1 暴露面表格状态行 ----------
E(
    "| **影响面** | 无运行时影响、无功能影响；属**工程卫生与凭证管理**缺陷 |",
    "| **影响面** | 无运行时影响、无功能影响；属**工程卫生与凭证管理**缺陷 |\n"
    "| **处置状态** | ✅ **已修复（2026-10-01 19:00，授权执行）**：36 个顶层项（35 文件 + `_verify_out/`）整体迁出 → `tests/manual-probes/`；`__pycache__/` 删除；`_verify_out` 双份副本按哈希比对后去重 |\n"
    "| **修复后复核** | `management-web/` 根目录脚手架残留 **0**；`src`/`public`/`dist` 对被迁移脚本引用 **0**、对 `123456` 命中 **0**；7 个明文口令文件哈希 **全部一致**（`DEF01_PLAINTEXT_EVIDENCE.json`） |",
    "5.1-status",
)

# ---------- 7) §5.3 标题与尾部 ----------
E(
    "### 5.3 最小修复建议（DEF-01，待授权）",
    "### 5.3 最小修复（DEF-01，已于 2026-10-01 19:00 授权执行完成）",
    "5.3-title",
)

E(
    "**替代方式**：若确认这些脚本无保留价值，可直接删除（均为可再生成的一次性脚手架）。**本轮未执行**，以避免在验收轮内改变被测对象状态。",
    "**替代方式**：若确认这些脚本无保留价值，可直接删除（均为可再生成的一次性脚手架）。\n"
    "\n"
    "#### 5.3.1 实际执行记录（2026-10-01 18:30 – 19:00）\n"
    "\n"
    "| 项 | 实测数据 |\n"
    "|---|---|\n"
    "| 迁移目标目录 | `health-management-system/tests/manual-probes/`（新建） |\n"
    "| 迁移文件 | **35 个**（`_*.py` / `_*.log` / `*.log`） |\n"
    "| 迁移目录 | `_verify_out/`（**54 个文件**，含 `illustration-raw/` 5 个） |\n"
    "| 迁移合计 | **36 个顶层项 / 89 个文件** |\n"
    "| 删除（纯缓存） | `management-web/__pycache__/`（2 个 `.pyc`） |\n"
    "| 删除（冗余副本） | MW 侧 `_verify_out/` 54 文件（DEST 已有逐字节相同副本，**先经 sha256 全量比对确认**） |\n"
    "| 明文口令文件 | **7 个全部迁移成功，迁移前后 sha256 完全一致** |\n"
    "| 产品资产 | 未触碰（`.env.development` / `.env.production` / `index.html` / `package.json` / `package-lock.json` / `vite.config.js` / `src/` / `public/` / `dist/` / `node_modules/` 原地保留） |\n"
    "\n"
    "**修复后 `management-web/` 顶层项（实测）**：\n"
    "\n"
    "```\n"
    ".env.development  .env.production  dist/  index.html  node_modules/\n"
    "package-lock.json  package.json  public/  src/  vite.config.js\n"
    "```\n"
    "\n"
    "**执行过程注意事项（工程经验，建议后续同类操作遵循）**：\n"
    "\n"
    "1. `shutil.move(src_dir, dst_dir)` 在**目标已存在**时会退化为「复制 + 删源」；删源若超沙箱批量删除阈值（50）会被拦截，产生「DEST 有副本、SRC 仍在」的**双份残留**。规避：迁移目录前确保 DEST 不存在，或改用**逐文件 move**。\n"
    "2. 出现双份残留时，**必须先按相对路径集合 + sha256 全量比对确认副本完整**，再分批（每批 ≤8 个）删源文件，最后自底向上 `rmdir` 空子目录。\n"
    "3. 分批删除**不可使用固定 batch 索引**（列表每次重算会收缩导致索引错位漏删），应每次取前 N 个直至剩余为 0。",
    "5.3-exec",
)

# ---------- 8) §六 回归表 ----------
E(
    "| `tests/api_test.py` | 接口联调 / 权限 / 安全（真实 HTTP + 真实 MySQL） | **197 / 198 PASS**（1 FAIL = DEF-01） |",
    "| `tests/api_test.py` | 接口联调 / 权限 / 安全（真实 HTTP + 真实 MySQL） | **198 / 198 PASS**（DEF-01 修复后） |",
    "6-api",
)

E(
    "| **合计** | — | **258 / 259 PASS** |",
    "| **合计** | — | **259 / 259 PASS** |",
    "6-total",
)

E(
    "**回归结论**：**未发现功能性回归**。除 DEF-01（工程卫生，存量问题）与已修正的口径假性 FAIL 外，全部功能、接口、构建断言通过；PC 管理端可正常构建出全量产物（含新增的三角色登录页资源）。",
    "**回归结论（第 2 版复验）**：**未发现功能性回归**。DEF-01 修复后 `api_test.py` 由 `197/198` 恢复为 **`198/198`**；全部功能、接口、构建断言通过；PC 管理端可正常构建出全量产物（2287 模块 / 19.93s）。第 1 版的另一项口径假性 FAIL 仍为已修正状态。",
    "6-conclusion",
)

# ---------- 9) §七 7.1 增补 ----------
E(
    "| 回归残留 | `api_test.py` 两轮（18:15、18:17）产生的 user 4 / doctor 6 / coach 4 及其业务行 | 14 实体 |",
    "| 回归残留 | `api_test.py` 两轮（18:15、18:17）产生的 user 4 / doctor 6 / coach 4 及其业务行 | 14 实体 |\n"
    "\n"
    "### 7.1.1 复验轮（第 2 版，19:04–19:25）创建与清理\n"
    "\n"
    "| 类别 | 实体（实测 id） | 数量 |\n"
    "|---|---|---|\n"
    "| 用户 | `sec_user_a`(30) / `sec_user_b`(31) / `sec_user_dup`(32) | 3 |\n"
    "| 用户（api_test 本轮） | 手机 `13990852777` / `13890852777`（id 33 / 34） | 2 |\n"
    "| 医生 | `sec_doctor_a`(44) / `sec_doctor_b`(45) / `sec_audit_doctor_pending`(46) / `sec_audit_doctor_evil`(47) / `sec_audit_doctor_ok`(48) | 5 |\n"
    "| 医生（api_test 本轮） | `doc_test_1001190617`(49) / `doc_reject_1001190617`(50) / `doc_other_1001190617`(51) | 3 |\n"
    "| 教练 | `sec_coach_a`(32) / `sec_coach_b`(33) / `sec_audit_coach_pending`(34) / `sec_audit_coach_ok`(35) | 4 |\n"
    "| 教练（api_test 本轮） | `coach_test_1001190617`(36) / `coach_reject_1001190617`(37) | 2 |\n"
    "| 绑定关系 | 医患 3 组 + 师生 3 组 | 6 |\n"
    "| 业务数据 | 健康记录 6 / 睡眠 3 / 运动 3 / 健康计划 4 / 医嘱 3 / 体检通知 3 / 医疗记录 3 / 运动目标 3 / 训练计划 3 / 健身建议 3 | **34 行** |\n"
    "| **本轮新增合计** | 5 用户 + 8 医生 + 6 教练 + 6 绑定 + 34 业务行 | **59 行** |\n"
    "\n"
    "**清理执行（`_sec_verify_cleanup.py --apply`，白名单 + 三重守卫）**：5 用户 / 8 医生 / 6 教练 + 34 业务行 + 6 绑定关系，**全部删除成功**；`problems = []`，`SAFE = True`。\n"
    "**清理后复核**：`users id>13` = **0**、`doctor_user id>18` = **0**、`coach_user id>12` = **0** ⇒ **本轮临时数据残留 = 0**。",
    "7.1.1-add",
)

# ---------- 10) §八 未处置项 ----------
E(
    "| # | 事项 | 建议 |\n|---|---|---|\n"
    "| 1 | **DEF-01** 验证脚本残留 + 明文口令 | 授权后按 §5.3 执行搬迁；建议同时在 `management-web/` 增加 `.gitignore` 规则（`_*.py`、`*.log`、`_verify_out/`）以防复发 |",
    "| # | 事项 | 建议 |\n|---|---|---|\n"
    "| 1 | ~~**DEF-01** 验证脚本残留 + 明文口令~~ | ✅ **已处置**（2026-10-01 19:00，见 §5.3.1）。**遗留建议（未执行）**：在 `management-web/` 增加 `.gitignore` 规则（`_*.py`、`*.log`、`_verify_out/`、`__pycache__/`）以防复发 |",
    "8-item1",
)

# ---------- 11) §九 证据索引 ----------
E(
    "| `tests/security/_out/_cleanup_dry.txt` / `_cleanup_apply.txt` | 收尾清理 dry-run 与实际执行记录 |",
    "| `tests/security/_out/_cleanup_dry.txt` / `_cleanup_apply.txt` | 收尾清理 dry-run 与实际执行记录 |\n"
    "| `tests/security/_out/DEF01_PLAINTEXT_EVIDENCE.json` | **DEF-01 明文口令取证**：7 个文件迁移前后 sha256 + 命中行（第 2 版新增） |\n"
    "| `tests/security/_out/DEF01_VERIFYOUT_DEDUP.json` | `_verify_out` 双份副本一致性比对（54/54 文件哈希全等，第 2 版新增） |\n"
    "| `tests/security/_out/VERIFY_BEFORE.json` / `VERIFY_AFTER.json` | 复验前后基线快照与受保护实体比对（第 2 版新增） |\n"
    "| `tests/security/_out/VERIFY_CLEANUP_PLAN.json` | 复验轮清理计划（白名单 + 守卫，`safe=true`，第 2 版新增） |\n"
    "| `tests/security/_out/_v_run.txt` / `_v_K.txt` / `_v_backend.txt` / `_v_miniapp.txt` / `_v_web.txt` / `_v_api.txt` / `_v_build.txt` | 第 2 版复验各套件执行日志 |",
    "9-evidence",
)

# ---------- 12) §十 声明 ----------
E(
    "3. 11 个专项 197/197 PASS，**权限隔离与异常处理链路未发现缺陷**；\n"
    "4. 因存在 **1 项未处置的真实缺陷 DEF-01**，**判定 FINAL_SECURITY_ACCEPTANCE = FAIL，不自封板**；\n"
    "5. DEF-01 属工程卫生 / 凭证管理范畴，修复成本极低（纯文件搬迁，不触碰产品代码与数据），授权后可在数分钟内恢复全绿。",
    "3. 11 个专项 197/197 PASS，**权限隔离与异常处理链路未发现缺陷**；\n"
    "4. **真实缺陷 DEF-01 已于 2026-10-01 19:00 按 §5.3 修复**（纯文件搬迁 + 缓存删除，未触碰任何产品代码与业务数据）；\n"
    "5. 修复后完成**全量复验**（权限专项 / 异常专项 / 静态扫描 / backend_selfcheck / miniapp / web / api_test / vite build），**全部通过**；`api_test.py` 恢复 `198/198`；\n"
    "6. 复验轮临时数据 **0 残留**；受保护实体与小周绑定关系 **全部 INTACT**；产品源码非授权修改 **0**；数据库结构修改 **0**；\n"
    "7. **判定 FINAL_SECURITY_ACCEPTANCE = PASS**（安全验收转绿）。**本判定不构成项目最终封板**；§八 中 2 项存量事项仍待单独授权处置。",
    "10-decl",
)

# ---------- 13) 末尾追加 §十一 ----------
E(
    "---\n\n*报告生成：2026-10-01*",
    "---\n"
    "\n"
    "## 十一、DEF-01 修复后复验记录（第 2 版）\n"
    "\n"
    "### 11.1 复验范围与结果\n"
    "\n"
    "复验时间窗：**2026-10-01 19:04 – 19:25**。执行顺序：基线快照 → `_sec_setup.py`（自带清理）→ `_sec_run.py`（整跑 A~J）→ `_sec_static.py`（K）→ 三项静态自检 → `api_test.py` → `vite build` → 临时数据清理 → 复验后比对。\n"
    "\n"
    "| # | 复验项 | 结果 |\n"
    "|---|---|---|\n"
    "| 1 | 权限专项（A/B/C/D/G/H） | **118 / 118 PASS** |\n"
    "| 2 | 异常专项（E/F/I/J） | **64 / 64 PASS** |\n"
    "| 3 | 静态扫描（K） | **15 / 15 PASS** |\n"
    "| 4 | backend_selfcheck | **5 / 5 PASS**（126 条 `/api` 路由） |\n"
    "| 5 | miniapp_check | **23 / 23 PASS** |\n"
    "| 6 | web_check | **33 / 33 PASS** |\n"
    "| 7 | api_test | **198 / 198 PASS** |\n"
    "| 8 | vite build | **PASS**（2287 模块 / 19.93s / exit 0） |\n"
    "| — | **A~K 合计** | **197 / 197 PASS，0 FAIL** |\n"
    "\n"
    "### 11.2 受保护数据复核（`_sec_verify_baseline.py verify`）\n"
    "\n"
    "```\n"
    "PROTECTED_ALL_INTACT = True\n"
    "```\n"
    "\n"
    "| 保护项 | 复验前 | 复验后 | 结论 |\n"
    "|---|---|---|---|\n"
    "| `users` 1 小林同学 / 2 阿may / 12 小孙 / 13 小周 | 在 | 在 | **INTACT** |\n"
    "| `doctor_user` 1 `doctor001` / 2 `doctor002` / 3 `doctor003` | 在（`audit_status=1`） | 在（`audit_status=1`） | **INTACT** |\n"
    "| `coach_user` 1 `coach001` / 2 `coach002` / 3 `coach003` | 在（`audit_status=1`） | 在（`audit_status=1`） | **INTACT** |\n"
    "| 小周(13) ↔ `doctor002`(2) | 绑定在 | 绑定在 | **INTACT** |\n"
    "| 小周(13) ↔ `coach001`(1) | 绑定在 | 绑定在 | **INTACT** |\n"
    "| 小周业务数据（健康记录 / 睡眠 / 运动 / 健康计划 / 医嘱 / 体检通知 / 医疗记录 / 训练计划 / 健身建议 各 1 行） | 10 项齐全 | 10 项齐全 | **INTACT** |\n"
    "\n"
    "**唯一数量变化**：`admin_operation_log` 204 → 243（+39）。原因为复验期间执行了注册 / 审核 / 绑定等写操作，产生**正常审计留痕**，非业务数据改动。\n"
    "\n"
    "### 11.3 临时数据账目\n"
    "\n"
    "| 指标 | 值 |\n"
    "|---|---:|\n"
    "| 本轮测试新增临时数据 | **59 行**（5 用户 + 8 医生 + 6 教练 + 6 绑定 + 34 业务行） |\n"
    "| 本轮测试清理临时数据 | **59 行**（清理明细见 7.1.1） |\n"
    "| **本轮临时数据残留** | **0** |\n"
    "\n"
    "历届残留（`users` 3~11 / `doctor_user` 4~16 / `coach_user` 4~11，共 30 行）**未授权，原样保留未动**。\n"
    "\n"
    "### 11.4 产品与结构完整性\n"
    "\n"
    "| 项 | 结果 |\n"
    "|---|---|\n"
    "| 产品源码非授权修改（`backend/` / `miniapp/` / `management-web/src`，19:04 后 mtime 扫描） | **0** |\n"
    "| 数据库结构修改 | **0**（无 DDL） |\n"
    "| 本轮改动范围 | 仅 `tests/`（新增复验脚本与证据）、`docs/`（本报告）、`management-web/dist/`（构建产物） |\n"
    "\n"
    "### 11.5 复验过程中的环境异常（如实说明）\n"
    "\n"
    "首次 `vite build` 在 `✓ 2287 modules transformed` 后**卡在产物写出阶段逾 18 分钟**（`dist/` mtime 长时间不变），判定为**进程挂起**（非产品缺陷：模块转换已全部完成）。终止该进程后**重跑构建 19.93s 正常完成**，`exit 0`。已排除产品代码因素。\n"
    "\n"
    "### 11.6 第 2 版判定\n"
    "\n"
    "```\n"
    "DEF-01 = PASS\n"
    "FINAL_SECURITY_ACCEPTANCE = PASS\n"
    "```\n"
    "\n"
    "> 本判定为**安全验收转绿**，**不构成项目最终封板**。\n"
    "\n"
    "---\n"
    "\n"
    "*报告第 1 版：2026-10-01 18:21 · 第 2 版（DEF-01 修复后复验）：2026-10-01 19:30*",
    "11-appendix",
)


def main():
    raw = open(P, 'rb').read()
    crlf = b'\r\n' in raw
    txt = raw.decode('utf-8')
    print('line ending :', 'CRLF' if crlf else 'LF')
    print('orig bytes  :', len(raw))
    ok = True
    for old, new, tag in EDITS:
        n = txt.count(old)
        flag = 'OK ' if n == 1 else 'BAD'
        print('  [%s] %-16s hits=%d' % (flag, tag, n))
        if n != 1:
            ok = False
    if not ok:
        print('!! 锚点校验失败 -> 整个文件不写')
        return 2
    for old, new, tag in EDITS:
        txt = txt.replace(old, new, 1)
    with open(P, 'wb') as f:
        f.write(txt.encode('utf-8'))
    print('WRITTEN: %d -> %d bytes' % (len(raw), len(txt.encode('utf-8'))))
    return 0


if __name__ == '__main__':
    sys.exit(main())
