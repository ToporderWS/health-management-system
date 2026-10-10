# -*- coding: utf-8 -*-
"""存量事项① 最小修改：API 地址 / LAN IP 配置统一（同源相对路径方案）。

规则：
  - 逐条锚点断言「命中数 == 1」，任一条未命中 ⇒ 整批不修改（fail-closed）；
  - 按字节读写，保留原始行尾（CRLF/LF）不变；
  - 只改这 5 个文件的指定行，不做任何其它改动。

用法：
  python _patch_addr_fix.py           # dry-run（只校验 + 预览）
  python _patch_addr_fix.py --apply   # 实际落盘
"""

import io
import json
import os
import sys

BASE = r"C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system"

# (相对路径, [(锚点, 替换文本), ...])
EDITS = [
    ("management-web/.env.production", [
        ("# 生产环境：固定后端地址（需求约定 API 基础地址）",
         "# 生产环境：同源部署，API 与静态资源使用相对路径（由同源 Web Server 反向代理转发到 Flask:8080）"),
        ("VITE_API_BASE_URL=http://192.168.1.4:8080/api",
         "VITE_API_BASE_URL=/api"),
        ("VITE_STATIC_BASE_URL=http://192.168.1.4:8080/static/upload/",
         "VITE_STATIC_BASE_URL=/static/upload/"),
    ]),
    ("management-web/src/utils/config.js", [
        ("import.meta.env.VITE_API_BASE_URL || 'http://192.168.1.4:8080/api'",
         "import.meta.env.VITE_API_BASE_URL || '/api'"),
        ("import.meta.env.VITE_STATIC_BASE_URL || 'http://192.168.1.4:8080/static/upload/'",
         "import.meta.env.VITE_STATIC_BASE_URL || '/static/upload/'"),
    ]),
    ("backend/config.py", [
        ('_get("API_BASE_URL", "http://192.168.1.4:8080/api")',
         '_get("API_BASE_URL", "/api")'),
        ('_get("STATIC_BASE_URL", "http://192.168.1.4:8080/static/upload/")',
         '_get("STATIC_BASE_URL", "/static/upload/")'),
    ]),
    ("backend/.env", [
        ("API_BASE_URL=http://192.168.1.4:8080/api",
         "API_BASE_URL=/api"),
        ("STATIC_BASE_URL=http://192.168.1.4:8080/static/upload/",
         "STATIC_BASE_URL=/static/upload/"),
    ]),
    ("backend/.env.example", [
        ("API_BASE_URL=http://192.168.1.4:8080/api",
         "API_BASE_URL=/api"),
        ("STATIC_BASE_URL=http://192.168.1.4:8080/static/upload/",
         "STATIC_BASE_URL=/static/upload/"),
    ]),
]


def load(p):
    return open(p, "rb").read().decode("utf-8")


def main():
    apply = "--apply" in sys.argv
    report = {"apply": apply, "files": [], "problems": [], "total_changed_lines": 0}

    # ---- 阶段 1：全量校验（fail-closed）----
    loaded = []
    for rel, pairs in EDITS:
        p = os.path.join(BASE, rel.replace("/", os.sep))
        if not os.path.isfile(p):
            report["problems"].append({"file": rel, "issue": "FILE_NOT_FOUND"})
            continue
        txt = load(p)
        hits = []
        for old, new in pairs:
            c = txt.count(old)
            hits.append({"anchor": old, "hits": c, "new": new})
            if c != 1:
                report["problems"].append(
                    {"file": rel, "issue": "ANCHOR_HITS_%d" % c, "anchor": old[:80]})
        loaded.append({"rel": rel, "path": p, "txt": txt, "hits": hits,
                       "crlf": "\r\n" in txt})

    if report["problems"]:
        print("=" * 64)
        print("ABORT: 锚点未全部命中（命中数 != 1），整批不修改")
        for x in report["problems"]:
            print("   [X] %s : %s : %s" % (x["file"], x["issue"], x.get("anchor", "")))
        print("=" * 64)
        json.dump(report, io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                               "_out", "ADDR_FIX_REPORT.json"),
                                  "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        return 1

    # ---- 阶段 2：应用 ----
    for item in loaded:
        txt = item["txt"]
        for h in item["hits"]:
            txt = txt.replace(h["anchor"], h["new"], 1)
        item["after"] = txt
        report["total_changed_lines"] += len(item["hits"])

        if apply:
            tmp = item["path"] + ".tmp_patch"
            open(tmp, "wb").write(txt.encode("utf-8"))
            os.replace(tmp, item["path"])

        report["files"].append({
            "file": item["rel"],
            "eol": "CRLF" if item["crlf"] else "LF",
            "changed_lines": len(item["hits"]),
            "before_bytes": len(item["txt"].encode("utf-8")),
            "after_bytes": len(txt.encode("utf-8")),
            "pairs": [{"old": h["anchor"], "new": h["new"], "hits": h["hits"]}
                      for h in item["hits"]],
        })

    # ---- 输出 ----
    print("=" * 64)
    print("MODE = %s" % ("APPLY" if apply else "DRY-RUN"))
    print("锚点校验：全部命中 (命中数 == 1)  OK")
    print("-" * 64)
    for f in report["files"]:
        print("[%s] %s  (%s, %d 行)" % ("APPLIED" if apply else "DRYRUN",
                                        f["file"], f["eol"], f["changed_lines"]))
        for pr in f["pairs"]:
            print("     - %s" % pr["old"][:88])
            print("     + %s" % pr["new"][:88])
    print("-" * 64)
    print("受影响文件 = %d ; 改动行数合计 = %d" % (len(report["files"]),
                                                 report["total_changed_lines"]))
    print("=" * 64)

    # 预览改后全文（仅前 2 个关键文件）
    for item in loaded:
        if item["rel"] in ("management-web/.env.production", "management-web/src/utils/config.js"):
            print("---- 改后预览: %s ----" % item["rel"])
            print("\n".join(item["after"].splitlines()[:12]))
            print()

    outp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_out", "ADDR_FIX_REPORT.json")
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    json.dump(report, io.open(outp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("报告已写入: %s" % outp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
