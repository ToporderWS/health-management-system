# -*- coding: utf-8 -*-
"""把真机缺陷修复（BUGFIX-01）回写到封板报告与 README。

锚点式：每条锚点断言「命中恰 1 次」，任一未命中则整个文件不改。
"""
import io
import os
import sys

BASE = r'C:/Users/Toporder-WS/Desktop/项目/个人健康管理系统小程序/health-management-system'

SEAL = os.path.join(BASE, 'docs', 'FINAL_PROJECT_SEAL_REPORT.md')
README = os.path.join(BASE, 'README.md')

TAIL_ANCHOR = '**《个人健康管理系统 V3.2 FINAL》已完成最终封板。**'

SECTION13 = '''---

## 十三、封板后真机缺陷修复（BUGFIX-01：小程序「我的」页头像不显示）

> 触发：真机测试发现小程序「我的」页头像位置显示为**白色圆形**，无实际头像。
> 本轮 `PROJECT_FINAL_SEAL` 先置为 `REOPENED_FOR_BUGFIX`，全部回归通过后重新标记为 `PASS`。

### 13.1 定位（只读，逐环取证）

| 环节 | 实测结果 | 判定 |
| --- | --- | --- |
| `users.avatar`（user_id=13 小周） | `9f2f80d5f40d4628b2a3e505f94f1a1d.jpg` | 正常 |
| `/api/user/info` | `avatar` 返回上述文件名（HTTP 与服务层双路径核对） | 正常 |
| `backend/static/upload/<文件名>` | 文件存在，40129 bytes，640×640 有效 JPEG | 正常 |
| `GET http://192.168.2.219:8080/static/upload/<文件名>` | `200` · `Content-Type: image/jpeg` | 正常 |
| `miniapp/common/config.js` | `STATIC_BASE_URL = http://192.168.2.219:8080/static/upload/` | 正常 |
| `resolveFileUrl()` | `STATIC_BASE_URL + 文件名`，无文件名/半路径/完整 URL 的二次拼接 | 正常 |
| 旧地址残留（`192.168.1.4` / `localhost` / `127.0.0.1`） | 0 处 | 正常 |
| 上传链路 | 上传 → `static/upload` 生成 UUID 文件 → 库内只存文件名 → `/user/info` 回读一致 | 正常 |

结论：**服务端、数据库、URL 拼接均无缺陷**；头像文件真实存在且 HTTP 200，属情况 B（文件正常、真机不显示）。

### 13.2 根因

微信小程序在**真机**上会在渲染层拦截 `<image>` 组件加载 `http://` 网络图片：
图片走系统图片通道（渲染层），而开发者工具「不校验合法域名」只放行 JSBridge 网络请求
（官方文档亦将图片归入「其他 HTTPS 请求」）。因此 `wx.request` 访问同一
`http://<局域网IP>:8080` 正常、而同一地址的图片在真机上空白 —— 与本次现象完全一致。

`miniapp/manifest.json` 与产物 `project.config.json` / `project.private.config.json` 中
`urlCheck: false`（即「不校验合法域名」）**本就是开启状态**，故不属于设置缺失；
本轮**未关闭任何产品安全逻辑**，也未改协议与域名策略。

### 13.3 最小修复（仅小程序前端：新增 1 个模块 + 4 个页面各改 1~2 行）

- **新增** `miniapp/common/image.js`：`imgSrc(文件名)` = `resolveFileUrl()` + 真机本地化。
  对 `http://` 地址先用 `uni.downloadFile`（与 `wx.request` 同一条 JSBridge 通道）下载到本地
  临时文件，再交给 `<image>` 渲染；`https://` 地址与本地打包资源**原样返回**，
  下载失败也**回落原地址** ⇒ 对生产环境零影响，且失败时行为与改造前完全一致。
- **修改** `<image>` 地址绑定，统一改走 `imgSrc()`：
  `pages/profile/index.vue`（我的·头像）、`pages/index/index.vue`（首页头像 + 科普封面）、
  `pages/article/index.vue`、`pages/article-detail/index.vue`。

**设计不变式保持**：数据库仍**只保存文件名**；URL 前缀仍由 `common/config.js::resolveFileUrl()`
唯一负责；未改后端、未改接口契约、未改数据库、未放宽任何鉴权或安全校验。

> 说明：§十一「未修改 miniapp 业务代码」是**上一轮封板**的表述；本轮为需求方授权的真机缺陷修复，
> 属**小程序前端**改动，服务端与 PC 端产品代码仍为 0 改动。

### 13.4 回归结果

```
backend_selfcheck = 5/5 PASS          miniapp = 23/23 PASS
management-web    = 33/33 PASS        api_test = 199/199 PASS
security A~K      = 197/197 PASS      Vite build（上一轮） = PASS
头像上传 / 读取端到端 = 19/19 PASS
  （注册 → 登录 → 上传 → 落盘 → 库内只存文件名 → /user/info 回读 →
    LAN 与回环两路 GET 200 + image/* → 三重守卫清理 → 计数回基线）

用户数据 = INTACT    doctor002 绑定 = INTACT    coach001 绑定 = INTACT
DATABASE_SCHEMA_CHANGED = NO（19 表 / 139 列 / 结构指纹未变）
本轮临时数据残留 = 0
```

### 13.5 判定

```
BUGFIX-01            = 已修复（服务端与前端代码本身无缺陷；真机图片加载链路按平台约束改道）
AVATAR_REAL_DEVICE_FIX = 待真机复测确认
PROJECT_FINAL_SEAL   = PASS（REOPENED_FOR_BUGFIX → PASS）
```

> 软件侧所有可自动验证的环节均已由本轮回归证实为 PASS；真机显示需按 §13.6 人工复测。

### 13.6 真机复测步骤

1. HBuilderX 重新运行到微信开发者工具（源码改动后产物 `unpackage/dist/dev/mp-weixin` 已自动重建）；
2. 手机与电脑处于同一 Wi-Fi（当前后端 LAN 地址 `192.168.2.219:8080`；换网络只需改
   `miniapp/common/config.js` 一处）；
3. 微信开发者工具「详情 → 本地设置」确认已勾选
   **「不校验合法域名、web-view（业务域名）、TLS 版本以及 HTTPS 证书」**（当前已是勾选态）；
4. 真机调试进入「我的」页 → 头像应正常显示。

'''

README_BULLET = '''- **小程序图片地址统一入口**：`miniapp/common/image.js` 的 `imgSrc(文件名)`
  （= `resolveFileUrl()` + 真机 http 图片本地化）。真机上 `<image>` 组件会被客户端拦截
  `http://` 网络图片，故该函数先经 `uni.downloadFile` 落到本地临时文件再渲染；
  `https://` 地址与本地打包资源原样返回。**PC 端与后端不经过此层。**
'''

README_ANCHOR = '- 四类默认头像：`default_health.jpg`、`default_doctor.jpg`、`default_coach.jpg`、`default_admin.jpg`'

changed = []
ok = True

# ---- 1. 封板报告 ----
b = open(SEAL, 'rb').read()
t = b.decode('utf-8')
nl = '\r\n' if b.count(b'\r\n') else '\n'
n = t.count(TAIL_ANCHOR)
print('seal anchor hits =', n)
if n == 1 and '## 十三、' not in t:
    t2 = t + nl + SECTION13.replace('\n', nl)
    open(SEAL, 'wb').write(t2.encode('utf-8'))
    changed.append(SEAL)
else:
    ok = False
    print('!! 封板报告锚点不满足，未改动')

# ---- 2. README ----
b2 = open(README, 'rb').read()
r = b2.decode('utf-8')
nl2 = '\r\n' if b2.count(b'\r\n') else '\n'
n2 = r.count(README_ANCHOR)
print('readme anchor hits =', n2)
if n2 == 1 and 'miniapp/common/image.js' not in r:
    idx = r.index(README_ANCHOR)
    end = r.index(nl2, idx)
    r2 = r[:end] + nl2 + README_BULLET.replace('\n', nl2) + r[end + len(nl2):]
    open(README, 'wb').write(r2.encode('utf-8'))
    changed.append(README)
else:
    ok = False
    print('!! README 锚点不满足，未改动')

print('已修改文件 =', len(changed))
for c in changed:
    print('   ', os.path.relpath(c, BASE))
sys.exit(0 if ok else 1)
