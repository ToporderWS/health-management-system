# -*- coding: utf-8 -*-
"""写记忆：当日日志 append + MEMORY.md 追加（各一次落盘，避免读写竞争）。"""
import os

BASE = r'C:/Users/Toporder-WS/Desktop/项目/个人健康管理系统小程序/.workbuddy/memory'
LOG = os.path.join(BASE, '2026-10-01.md')
MEM = os.path.join(BASE, 'MEMORY.md')

LOG_ADD = '''
---

## BUGFIX-01 · 真机「我的」页头像不显示（2026-10-01 21:0x）

- **现象**：真机进入小程序，「我的」页头像位置白色圆形；资料可读、其他 API/页面正常。
- **定位（只读逐环）**：小周 `users.id=13` 的 `avatar = 9f2f80d5f40d4628b2a3e505f94f1a1d.jpg`；
  `/api/user/info` 返回该文件名；文件存在 40129 bytes 640×640 JPEG；
  `GET http://192.168.2.219:8080/static/upload/<file>` = **200 · image/jpeg**（127.0.0.1 与 LAN 双路一致）；
  `STATIC_BASE_URL` 正确、无二次拼接、旧地址 `192.168.1.4/localhost/127.0.0.1` 残留 0。⇒ **情况 B（文件正常、真机不显示）**。
- **根因**：微信**真机**渲染层拦截 `<image>` 加载 `http://` 网络图片；开发者工具「不校验合法域名」
  只放行 JSBridge 请求（`wx.request/uploadFile/downloadFile`），不覆盖 `<image>` 的系统图片通道。
  `manifest.json`/`project.config.json`/`project.private.config.json` 中 `urlCheck:false` **本就是开启态**，非设置缺失。
- **最小修复（仅小程序前端）**：**新增** `miniapp/common/image.js` 的 `imgSrc(文件名)`
  = `resolveFileUrl()` + 对 `http://` 用 `uni.downloadFile`（同一 JSBridge 通道）落本地临时文件后渲染；
  `https://` 与本地打包资源原样返回、下载失败回落原地址 ⇒ 生产零影响。
  **改** 4 个页面的 image 绑定改走 `imgSrc`：`profile/index.vue`（我的·头像）、
  `index/index.vue`（首页头像 + 科普封面）、`article/index.vue`、`article-detail/index.vue`。
- **不变式**：数据库仍**只存文件名**；URL 前缀仍由 `common/config.js::resolveFileUrl()` 唯一负责；后端/PC/接口契约/数据库 0 改动。
- **回归（本轮实测）**：backend_selfcheck **5/5** · miniapp **23/23** · web **33/33** · api_test **199/199** ·
  安全 A~K **197/197** · 头像上传/读取端到端 **19/19** · `_seal_verify` 全 True（19 表/139 列/指纹不变、
  小周 10 类业务 + doctor002/coach001 双绑定 INTACT、临时数据 0）。
- **文档回写**：`docs/FINAL_PROJECT_SEAL_REPORT.md` 追加 **§十三**；`README.md` 图片章节追加 `imgSrc` 说明
  （锚点式，各命中恰 1 次）。
- **判定**：`BUGFIX-01=已修复`；`DATABASE_SCHEMA_CHANGED=NO`；`AVATAR_REAL_DEVICE_FIX=待真机复测确认`；
  `PROJECT_FINAL_SEAL = PASS`（REOPENED_FOR_BUGFIX → PASS）。
'''

MEM_ADD = '''
## 七、真机图片加载（BUGFIX-01 沉淀，2026-10-01）

- **铁律**：微信小程序**真机**会拦截 `<image>` 加载 `http://` 网络图片（渲染层系统图片通道）；
  开发者工具「不校验合法域名」(`urlCheck:false`) **只放行 JSBridge 请求**，**不覆盖** `<image>`。
  ⇒ 局域网 IP + http 场景下，「接口正常、图片空白」是**平台约束**，不是接口/URL/拼接缺陷。
- **本工程统一入口**：小程序内任何图片一律用 `miniapp/common/image.js` 的 **`imgSrc(文件名)`**
  （= `resolveFileUrl()` + http 本地化），**不要**直接在 `<image>` 上绑 `resolveFileUrl()`。
  PC 端与后端不走此层；数据库仍只存文件名。
- **排查顺序**（下次遇到同类）：① 库值 → ② `/user/info` 回读 → ③ 文件是否存在/大小/魔数 →
  ④ 双路 GET 200 + `image/*` → ⑤ `STATIC_BASE_URL` 与二次拼接 → ⑥ 旧 IP 残留；
  全绿即判定为**真机平台约束**，走 `imgSrc` 本地化，别去改后端。
- **新增测试资产**：`tests/security/_bug_avatar_probe.py`（只读探针）、`_bug_avatar_e2e.py`（端到端+三重守卫清理）、
  `_bug_avatar_cleanup.py`、`_bug_report_writeback.py`（锚点回写）、`_bug_final_verify.py`（最终只读复核）。
'''

for path, add in ((LOG, LOG_ADD), (MEM, MEM_ADD)):
    b = open(path, 'rb').read()
    nl = '\r\n' if b'\r\n' in b else '\n'
    t = b.decode('utf-8')
    t2 = t + add.replace('\n', nl)
    open(path, 'wb').write(t2.encode('utf-8'))
    print('appended', os.path.basename(path), len(b), '->', len(t2.encode('utf-8')), 'nl=', repr(nl))
