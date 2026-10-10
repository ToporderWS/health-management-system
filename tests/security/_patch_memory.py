# -*- coding: utf-8 -*-
"""更新项目 MEMORY.md：标记存量①②①已解决 + 冻结 API 地址约定。

3 处改动，逐条断言命中数 == 1，任一未命中 ⇒ 整个文件不改。
用法：python _patch_memory.py [--apply]
"""
import os
import sys

P = r"C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\.workbuddy\memory\MEMORY.md"

A_OLD = "  构建用 `node node_modules/vite/bin/vite.js build`（`management-web/` 下，约 27s）。"
A_NEW = ("  构建用 `node node_modules/vite/bin/vite.js build`（`management-web/` 下，约 27s）。\n"
         "- **API 地址约定（2026-10-01 冻结，存量事项① 处置结果）**：PC 端走**同源相对路径** —— "
         "dev `VITE_API_BASE_URL=/api` + Vite proxy；prod `VITE_API_BASE_URL=/api`、"
         "`VITE_STATIC_BASE_URL=/static/upload/`，由同源 Nginx 反代 `/api`、`/static` → Flask:8080。"
         "**PC 端任何位置不得再出现 `192.168.x.x`**。小程序保留唯一 LAN 入口 `miniapp/common/config.js`"
         "（换 Wi-Fi 只改该文件 L5/L8）。Flask 保持 `0.0.0.0:8080`。")

B_OLD = "1. `management-web/` 根目录残留 37 项历史验证脚手架（含明文口令 `123456`），最小修复=搬到 `tests/manual-probes/`；"
B_NEW = ("1. ~~`management-web/` 根目录残留 37 项历史验证脚手架（含明文口令 `123456`）~~ ✅ **已解决**"
         "（2026-10-01 19:00，已迁至 `tests/manual-probes/`）；遗留建议：在 `management-web/` 补 `.gitignore` 防复发；")

C_OLD = "3. 地址不一致：miniapp `common/config.js` = `192.168.2.219:8080`，而 `backend/config.py` 与 `management-web/.env.production` 兜底 `192.168.1.4:8080`；"
C_NEW = ("3. ~~地址不一致：miniapp `common/config.js` = `192.168.2.219:8080`，而 `backend/config.py` 与 "
         "`management-web/.env.production` 兜底 `192.168.1.4:8080`~~ ✅ **已解决**（2026-10-01 19:40，存量事项①）："
         "PC 端统一为同源相对路径（`.env.production` + `src/utils/config.js` 兜底 + `backend/config.py`/`.env`/`.env.example`），"
         "**PC 端 0 处 `192.168.x.x`**；miniapp 保留 `192.168.2.219:8080`（真机调试必需）；")

PAIRS = [(A_OLD, A_NEW), (B_OLD, B_NEW), (C_OLD, C_NEW)]


def main():
    apply = "--apply" in sys.argv
    txt = open(P, "rb").read().decode("utf-8")
    eol = "\r\n" if "\r\n" in txt else "\n"

    problems = []
    for i, (o, n) in enumerate(PAIRS, 1):
        c = txt.count(o)
        if c != 1:
            problems.append((i, c, o[:80]))
    if problems:
        print("ABORT: 锚点未全部命中（!=1），整个文件不改")
        for i, c, o in problems:
            print("   [X] #%d hits=%d : %s" % (i, c, o))
        return 1

    for o, n in PAIRS:
        txt = txt.replace(o, n, 1)

    # 插入文本统一为文件自身行尾
    if eol == "\r\n":
        txt = txt.replace("\r\n", "\n").replace("\n", eol)

    if apply:
        tmp = P + ".tmp_patch"
        open(tmp, "wb").write(txt.encode("utf-8"))
        os.replace(tmp, P)

    print("MODE = %s ; 锚点 3/3 命中 ; eol=%s" % ("APPLY" if apply else "DRY-RUN", "CRLF" if eol == "\r\n" else "LF"))
    print("chars = %d" % len(txt))
    for k in ["API 地址约定（2026-10-01 冻结", "已解决**（2026-10-01 19:00", "已解决**（2026-10-01 19:40"]:
        print("   含 '%s' ? %s" % (k, k in txt))
    return 0


if __name__ == "__main__":
    sys.exit(main())
