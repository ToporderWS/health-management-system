# -*- coding: utf-8 -*-
"""最终封板 · 文档同步（锚点式回写；每条锚点断言命中恰 1 次，任一未命中该文件整体不改）。

不改写历史报告中的既往记录（如 FINAL_SECURITY_ACCEPTANCE_REPORT 的 §十二 变更留痕），
仅同步「活文档」（README / API / DATABASE / TEST_REPORT）并追加封板新章节。
"""
import io
import os
import sys

BASE = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system'

README_NEW_SECTIONS = """

---

## 二十三、JWT_SECRET 配置与安全约定

- **算法 / 载荷 / 时效未改**：HS256、四角色 `token_type` 隔离、有效期 `JWT_EXPIRE_HOURS=72`。
- **密钥只经环境变量进入后端**：`backend/.env` → `config.py` → `utils/jwt_utils.py`；产品源码**无硬编码**。
- **生成方式**（不要用固定串 / 项目名+日期 / `123456` / UUID）：

```bash
python -c "import secrets;print(secrets.token_urlsafe(64))"
```

  将输出写入 `backend/.env` 的 `JWT_SECRET`（≥32 bytes 熵，推荐 64 bytes）。
- **安全失败策略**：`JWT_SECRET` 缺失或仍为占位值时，**后端启动阶段直接报配置错误**，不会回落到固定默认密钥。
- **`.env` 不提交版本控制**：`backend/.env`、`management-web/.env.*` 均被 `.gitignore` 忽略；
  仓库内只保留 **`.env.example`** 占位模板（`JWT_SECRET=CHANGE_ME_TO_A_STRONG_RANDOM_SECRET`）。
- **轮换影响**：更换 `JWT_SECRET` 后旧 Token 全部失效——这是**正确的安全行为**，四角色需重新登录；
  系统**不保留旧密钥、不实现双密钥、不降低校验**。

---

## 二十四、最终验收结果（V3.2 FINAL 封板）

| 项目 | 结果 |
| --- | --- |
| 后端自检 `backend_selfcheck.py` | **5 / 5 PASS**（126 条路由） |
| 小程序静态检查 `miniapp_check.py` | **23 / 23 PASS** |
| PC 端静态检查 `web_check.py` | **33 / 33 PASS** |
| 接口联调 `api_test.py` | **199 / 199 PASS** |
| 权限 + 异常专项 A~K | **197 / 197 PASS** |
| 四角色真实冒烟 | **46 / 46 PASS** |
| Vite 生产构建（同源 `/api`） | **PASS** |
| Secret 泄露扫描（旧/新 JWT Secret、DB 密码、Bearer、dist） | **命中 0** |
| 数据库完整性 | 19 表 · 结构指纹未变 · 无孤儿 · 临时数据残留 0 |
| 受保护数据（小林同学 / 阿may / 小孙 / 小周 + doctor001-003 + coach001-003 及绑定） | **INTACT** |

**结论**：`PROJECT_FINAL_SEAL = PASS`。完整记录见 **`docs/FINAL_PROJECT_SEAL_REPORT.md`**。
"""

WIFI_SECTION = """
### 换 Wi-Fi / 换网络后如何修改小程序 IP

1. `ipconfig` 查到本机新的 IPv4 地址（形如 `192.168.x.y`）；
2. 编辑 **`miniapp/common/config.js`**（全项目**唯一**网络配置入口），把 `API_BASE_URL` /
   `STATIC_BASE_URL` 的 IP 换成新值，**端口保持 `8080`**；
3. 重新运行小程序即可；**PC 端无需修改**——开发态走 Vite 代理，生产态走同源相对路径 `/api`。

> 除 `miniapp/common/config.js` 外，任何页面都**不得**再出现 IP 字面量（已静态扫描确认 = 0）。
"""


def patch_file(path, pairs, append=None):
    """pairs: [(anchor, replacement), ...]；任一 anchor 命中数 != 1 -> 该文件整体不改。"""
    full = os.path.join(BASE, path)
    txt = open(full, 'rb').read().decode('utf-8')
    orig = txt
    report = []
    for i, (a, b) in enumerate(pairs, 1):
        n = txt.count(a)
        report.append('  [%s] anchor#%d count=%d' % ('OK' if n == 1 else 'ABORT', i, n))
        if n != 1:
            print('%s : 锚点未命中，整文件未修改' % path)
            print('\n'.join(report))
            return False
    for a, b in pairs:
        txt = txt.replace(a, b, 1)
    if append:
        if not txt.endswith('\n'):
            txt += '\n'
        txt += append
    with open(full, 'wb') as f:
        f.write(txt.encode('utf-8'))
    print('%s : 已更新（%d 处锚点 + %s）chars %d -> %d'
          % (path, len(pairs), 'append' if append else 'no-append', len(orig), len(txt)))
    print('\n'.join(report))
    return True


def main():
    ok = True

    # ---------------- README.md ----------------
    ok &= patch_file('README.md', [
        # 1) .env 关键项：同源相对路径
        ("API_BASE_URL=http://192.168.1.4:8080/api\n"
         "STATIC_BASE_URL=http://192.168.1.4:8080/static/upload/",
         "API_BASE_URL=/api                     # 生产同源相对路径（Web Server 反代到 Flask:8080）\n"
         "STATIC_BASE_URL=/static/upload/       # 生产同源相对路径"),
        # 2) .env 不提交
        ("`.env` 关键项：",
         "`.env` 含真实密钥，已被 `.gitignore` 忽略、**绝不提交版本控制**；仓库内仅保留 `.env.example` 占位模板。`.env` 关键项："),
        # 3) 生产部署要点：同源方案
        ("- 生产环境 API 地址在 `.env.production` 中固定为 `http://192.168.1.4:8080/api`。",
         "- 生产采用**同源部署**：`.env.production` 中 `VITE_API_BASE_URL=/api`、`VITE_STATIC_BASE_URL=/static/upload/`，\n"
         "  由 Web Server（Nginx 等）把 `/api`、`/static/upload/` 反向代理到 Flask `127.0.0.1:8080`。"),
        # 4) 小程序 IP
        ("export const API_BASE_URL = 'http://192.168.1.4:8080/api'\n"
         "export const STATIC_BASE_URL = 'http://192.168.1.4:8080/static/upload/'",
         "export const API_BASE_URL = 'http://192.168.2.219:8080/api'\n"
         "export const STATIC_BASE_URL = 'http://192.168.2.219:8080/static/upload/'"),
        # 5) API 配置表
        ("| PC 端 | `management-web/src/utils/config.js` | 读取 `VITE_API_BASE_URL`，兜底 `http://192.168.1.4:8080/api` |\n"
         "| PC 端（开发） | `management-web/.env.development` | `/api` + Vite 代理 |\n"
         "| PC 端（生产） | `management-web/.env.production` | `http://192.168.1.4:8080/api` |",
         "| PC 端 | `management-web/src/utils/config.js` | 读取 `VITE_API_BASE_URL`，兜底 `/api` |\n"
         "| PC 端（开发） | `management-web/.env.development` | `/api` + Vite 代理（无需改 IP） |\n"
         "| PC 端（生产） | `management-web/.env.production` | `/api` + `/static/upload/`（**同源**，由 Web Server 反代） |"),
        # 6) 测试数量
        ("python api_test.py              # 接口/权限/安全：198 项（需后端已启动）",
         "python api_test.py              # 接口/权限/安全：199 项（需后端已启动）"),
        # 7) api_test 自动清理说明
        ("> `api_test.py` 会在数据库中创建带时间戳的测试账号与测试数据用于真实联调，不会删除任何既有数据。",
         "> `api_test.py` 会创建**带唯一时间戳标识**的测试账号与测试数据用于真实联调，并在 `finally` 中\n"
         "> **精确清理本轮创建的数据**（白名单 + 守卫，绝不模糊删除、绝不动既有数据）；运行前后业务表计数一致，残留恒为 0。"),
        # 8) 局域网排查：IP 指向
        ("   - `192.168.1.4` 是否为本机真实 IP（若路由器分配的是 `192.168.x.y`，需同步修改前端配置）。",
         "   - `miniapp/common/config.js` 内的 IP 是否为本机**当前**真实 IP（换网络后需同步修改）。"),
        # 9) 换 Wi-Fi 小节
        ("5. 小程序真机预览时，手机必须与电脑在同一局域网，且手机可访问该 IP。",
         "5. 小程序真机预览时，手机必须与电脑在同一局域网，且手机可访问该 IP。\n" + WIFI_SECTION),
    ], append=README_NEW_SECTIONS)

    # ---------------- docs/API.md ----------------
    ok &= patch_file('docs/API.md', [
        ("> 版本：V3.2 FINAL　　基础地址：`http://192.168.1.4:8080/api`",
         "> 版本：V3.2 FINAL　　基础地址：`/api`（**生产同源相对路径**；小程序端为 `http://<局域网IP>:8080/api`）"),
        ("- 前端拼接：`STATIC_BASE_URL + 文件名`，其中 `STATIC_BASE_URL = http://192.168.1.4:8080/static/upload/`。",
         "- 前端拼接：`STATIC_BASE_URL + 文件名`，其中 `STATIC_BASE_URL = /static/upload/`（生产同源；小程序端为 `http://<局域网IP>:8080/static/upload/`）。"),
    ])

    # ---------------- docs/DATABASE.md ----------------
    ok &= patch_file('docs/DATABASE.md', [
        ("> **19 张表 · 20 个外键 · 按角色与查询模式建索引**",
         "> **19 张表 · 20 个外键 · 按角色与查询模式建索引**\n"
         "> 封板校验（2026-10-01）：19 张表在线、结构指纹与基线一致、无 DDL 变更、无孤儿记录、临时数据残留 0。"),
    ])

    # ---------------- docs/TEST_REPORT.md ----------------
    ok &= patch_file('docs/TEST_REPORT.md', [
        ("| 后端接口集成测试 `api_test.py` | 198 | 198 | 0 | ✅ PASS |",
         "| 后端接口集成测试 `api_test.py` | 199 | 199 | 0 | ✅ PASS |"),
        ("## 三、后端接口测试（198 / 198 PASS）",
         "## 三、后端接口测试（199 / 199 PASS）"),
        ("| `.env.production` 固定 API 基础地址为 `http://192.168.1.4:8080/api` | PASS |",
         "| `.env.production` 使用同源相对路径 `VITE_API_BASE_URL=/api`（Web Server 反代到 Flask:8080） | PASS |"),
    ])

    print()
    print('DOC_SYNC_OK =', ok)
    return 0 if ok else 3


if __name__ == '__main__':
    sys.exit(main())
