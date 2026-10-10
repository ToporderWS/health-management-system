# -*- coding: utf-8 -*-
"""
MEMORY.md 注入截断规避 · 非破坏性三级拆分（v1）
- 归档当前逐字全文（byte-exact）
- 当前正文另存为 DETAIL
- MEMORY.md 重写为「判据+指针」索引（<=5000 chars）
不删除任何文件；仅新增 2 个文件 + 重写 MEMORY.md。
"""
import hashlib
import os
import shutil

MEMDIR = r'C:/Users/Toporder-WS/Desktop/项目/个人健康管理系统小程序/.workbuddy/memory'
MEM = os.path.join(MEMDIR, 'MEMORY.md')
ARC = os.path.join(MEMDIR, 'MEMORY-v1-full-archive-20261002.md')
DET = os.path.join(MEMDIR, 'MEMORY-DETAIL-v1.md')
CHAR_LIMIT = 5000

NEW_BODY = '''# 项目长期记忆 · 个人健康管理系统（V3.2 FINAL）

> 本文件为**判据 + 指针索引**（注入安全线 <=5000 字符）。
> 逐字全文/叙述 -> `MEMORY-DETAIL-v1.md`；本次压缩前逐字归档 -> `MEMORY-v1-full-archive-20261002.md`。
> 正本：`docs/FINAL_PROJECT_SEAL_REPORT.md`（§一~§十五）· `docs/` 安全验收报告（第 5 版 §十四）。

## 0. 当前断点（2026-10-02）
- **PROJECT_FINAL_SEAL = REOPENED_FOR_REAL_DEVICE_UI_FIX**。
- 已完成 BUGFIX-01（真机头像）/ 02（uCharts series）/ 03（真机 UI 尺寸 + 首页实体）。
- BUGFIX-03 软件侧全绿（见 §3）；`REAL_DEVICE_UI_ACCEPTANCE = WAITING_USER_CONFIRMATION`，等真机复看。
- PC 端本轮 0 改动；`VITE_BUILD = SKIPPED_DUE_TO_SAFE_DELETE_GUARD`（不得为跑 build 触发 dist 批量删除）。

## 1. 运行/测试环境（冻结）
- 后端 Flask `0.0.0.0:8080`，蓝图 `/api/user|doctor|coach|admin`；MySQL 8.0.33 库 `health_management`；**用户表名 `users`（复数）**。
- 安全/接口脚本（需 pymysql）**必须用项目 venv** `health-management-system/.venv/Scripts/python.exe`（py3.11+pymysql）；托管 py3.13 **无 pymysql**。
- Node：`C:/Users/Toporder-WS/.workbuddy/binaries/node/versions/22.22.2-3/node.exe`；PC 构建 `node node_modules/vite/bin/vite.js build`（`management-web/`）。
- 地址约定（冻结）：PC 端**同源相对路径**（`/api`、`/static/upload/`），**PC 端 0 处 `192.168.x.x`**；小程序唯一 LAN 入口 `miniapp/common/config.js`（换 Wi-Fi 只改它）。
- `/api/health` -> `{"code":200,"data":{"service":"ok","database":"ok","version":"V3.2 FINAL"}}`（`database` 在 `data` 内）。

## 2. 铁律索引（逐字全文 -> DETAIL）
- **A 测试数据**：临时实体一律 `sec_` 前缀 + `199********`；清理**精确 IN**，禁 `LIKE`；三重守卫（id 白名单+手机号前缀+命名关键字）；先 dry-run。
- **B 严禁触碰**：`users` 1小林/2阿may/12小孙/**13小周**；`doctor_user` 1-3；`coach_user` 1-3；**小周<->doctor002/coach001 绑定**。
- **C 权限模型**：JWT `token_type` 不符即 401；四角色 Token 不可互用；越权读 401/写 400；`admin.py` 全 GET 只读；`audit_status` 0待审(拒发Token)/1通过/2拒绝，审核一次性不可逆；统一 `{code,msg,data}` 且 HTTP==code。
- **D 小程序图片**：真机 `<image>` 拦截 `http://`；统一入口 `miniapp/common/image.js::imgSrc()`（=resolveFileUrl+http 本地化），**禁止**在 `<image>` 直接绑 `resolveFileUrl()`；DB 只存文件名。
- **E uCharts series**：pie/ring/mount/rose/funnel 的 `series[0].data` 必须 `[{name,value}]` 对象数组；line/column/area 才用数值数组；**禁改第三方 `u-charts.js`**。
- **F uCharts 真机尺寸**：旧版 canvas 坐标系 = **CSS px** => `width/height` 传 CSS px、`pixelRatio` **恒为 1**、用 `boundingClientRect`/`uni.upx2px` 换算；**绝不** `width*DPR`（与库内 `*opts.pix` 双重放大）。pie 与 ring 用**两个独立**键 `opts.extra.pie`/`.ring`。唯一封装 `miniapp/components/u-charts/u-charts.vue`。
- **G UI 文本**：模板文本节点禁出现 `&gt;`/`&lt;`/`&amp;`（会原样显示）；「更多 ›」用真实字符。
- **H 缓存清理**：`__pycache__` 分批逐文件（`_seal_cache_clean.py`，<=8/批），禁 `shutil.rmtree`；封板需在所有 Python 执行后做最后一轮。
- **I 工程卫生**：4 份 `.gitignore`（根/backend/management-web/miniapp）；根**刻意不收窄** `_out/`；`tests/manual-probes/` 与 `tests/security/_out/` 一律保留。
- **J 验证资产**：`tests/security/_out/UCHARTS_*.md`、`REALUI_BUILD_VERIFY.md`、`REALUI_BUILD_DETERMINISM.md`；无头 harness `_ucharts_fix_verify.js`(12)、`_ucharts_realdevice_size_verify.js`(28)。

## 3. 回归基线
`backend_selfcheck 5/5` · `miniapp_check 23/23` · `web_check 33/33` · `api_test 199/199` · 安全 A~K `197/197` · `DATABASE_SCHEMA_CHANGED=NO`（19 表/139 列指纹）· `PROTECTED_ALL_INTACT=True` · `TEMP_TEST_DATA_RESIDUE=0`。

## 4. 本地踩坑（全文 -> DETAIL §5）
- `HTTP_PROXY=http://127.0.0.1:65377`：Flask 挂了会返回 **502**（非 ConnectionRefused）-> 先查后端进程。
- `subprocess+DETACHED_PROCESS` 启的 Flask 会被沙箱回收；需常驻用 Bash `run_in_background=true`。
- `netstat -ano` LISTENING 行末字段才是 PID；`wmic` 已禁用。
- 遗留低风险 4 项（不阻塞）：admin_operation_log 每轮 +~39 行；开发 MySQL 弱口令；manual-probes/_out 保留；审核中心医生账号列宽 130 偏窄。
'''


def main():
    old_raw = open(MEM, 'rb').read()
    old_t = old_raw.decode('utf-8')
    print('old MEMORY.md bytes =', len(old_raw), 'chars =', len(old_t.replace('\r\n', '\n')))

    # 1) 归档（byte-exact）
    if os.path.exists(ARC):
        assert open(ARC, 'rb').read() == old_raw, 'ARC 已存在且与当前主文件不一致 -> ABORT'
        print('[ARC] 已存在且一致，跳过写入')
    else:
        shutil.copyfile(MEM, ARC)
        assert open(ARC, 'rb').read() == old_raw, 'ARC 逐字节复核失败'
        print('[ARC] 写入并逐字节复核通过')
    arc_sha = hashlib.sha256(open(ARC, 'rb').read()).hexdigest()
    print('archive  : %s bytes=%d sha256[:16]=%s' % (os.path.basename(ARC), os.path.getsize(ARC), arc_sha[:16]))

    # 2) DETAIL = 当前逐字正文
    if os.path.exists(DET):
        assert open(DET, 'rb').read() == old_raw, 'DETAIL 已存在且不一致 -> ABORT'
        print('[DET] 已存在且一致，跳过写入')
    else:
        with open(DET, 'wb') as f:
            f.write(old_raw)
        print('[DET] 写入并逐字节复核通过 =', open(DET, 'rb').read() == old_raw)
    det_sha = hashlib.sha256(open(DET, 'rb').read()).hexdigest()
    print('DETAIL   : %s bytes=%d sha256[:16]=%s' % (os.path.basename(DET), os.path.getsize(DET), det_sha[:16]))

    # 3) 新索引体
    body = NEW_BODY
    assert '\r\n' not in body, '新正文必须是纯 LF'
    nchars = len(body)
    print('new MEMORY.md chars(LF) =', nchars, '(limit %d)' % CHAR_LIMIT)
    assert nchars <= CHAR_LIMIT, '超字符上限 -> ABORT'
    new_raw = body.encode('utf-8')          # 本项目 MEMORY.md 为 LF，保持一致
    assert len(new_raw) < len(old_raw), '新文件必须更短'
    with open(MEM, 'wb') as f:
        f.write(new_raw)
    back = open(MEM, 'rb').read()
    assert back == new_raw, '读回逐字节复核失败'

    print('MEMORY.md: bytes %d -> %d ; chars %d -> %d' % (len(old_raw), len(new_raw), len(old_t.replace('\r\n', '\n')), len(body)))
    print('sha256[:16] =', hashlib.sha256(back).hexdigest()[:16])
    print('OK. 三个文件均就位（新增 2 + 重写 1，未删除任何文件）。')


if __name__ == '__main__':
    main()
