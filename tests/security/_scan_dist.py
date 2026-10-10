# -*- coding: utf-8 -*-
"""扫描 management-web/dist 生产产物：
  - 是否残留 192.168.x.x / :8080 等开发 LAN 地址
  - 是否已注入相对路径 /api 与 /static/upload/
"""
import io
import json
import os
import re

DIST = r"C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system\management-web\dist"
BIN_EXT = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".woff",
           ".woff2", ".ttf", ".eot", ".map", ".svg")

out = {"dist": DIST, "files_scanned": 0, "lan_ip": {}, "port": {},
       "rel_api": [], "rel_static": [], "api_abs_url": []}

texts = {}
for r, _, fs in os.walk(DIST):
    for f in fs:
        fp = os.path.join(r, f)
        rel = os.path.relpath(fp, DIST).replace(os.sep, "/")
        if f.lower().endswith(BIN_EXT):
            continue
        try:
            t = open(fp, "rb").read().decode("utf-8", "replace")
        except Exception:
            continue
        out["files_scanned"] += 1
        texts[rel] = t

for tok in ("192.168.1.4", "192.168.2.219", "192.168."):
    hits = []
    for rel, t in texts.items():
        c = t.count(tok)
        if c:
            hits.append({"file": rel, "count": c})
    out["lan_ip"][tok] = hits

for tok in (":8080", ":5000", ":5001"):
    hits = []
    for rel, t in texts.items():
        c = t.count(tok)
        if c:
            hits.append({"file": rel, "count": c})
    out["port"][tok] = hits

# 相对路径注入证据
rel_api_pat = re.compile(r"""["'](/api)["']""")
rel_static_pat = re.compile(r"""["'](/static/upload/)["']""")
abs_api_pat = re.compile(r"""https?://[^"'\s]{0,60}?/api""")
for rel, t in texts.items():
    n1 = len(rel_api_pat.findall(t))
    if n1:
        out["rel_api"].append({"file": rel, "count": n1})
    n2 = len(rel_static_pat.findall(t))
    if n2:
        out["rel_static"].append({"file": rel, "count": n2})
    for m in set(abs_api_pat.findall(t)):
        out["api_abs_url"].append({"file": rel, "url": m[:120]})

print("=" * 66)
print("dist 文件扫描数（非二进制）= %d" % out["files_scanned"])
print("-" * 66)
print("[LAN IP 残留]")
for tok, hits in out["lan_ip"].items():
    tot = sum(h["count"] for h in hits)
    print("   %-16s = %d 处 %s" % (tok, tot, [h["file"] for h in hits][:6]))
print("[端口残留]")
for tok, hits in out["port"].items():
    tot = sum(h["count"] for h in hits)
    print("   %-8s = %d 处 %s" % (tok, tot, [h["file"] for h in hits][:6]))
print("[相对路径注入]")
print("   \"/api\"           命中文件: %s" % out["rel_api"])
print("   \"/static/upload/\" 命中文件: %s" % out["rel_static"])
print("[绝对 http(s)://.../api 残留]")
if out["api_abs_url"]:
    for x in out["api_abs_url"]:
        print("   %s -> %s" % (x["file"], x["url"]))
else:
    print("   无")
print("=" * 66)

# 抽样上下文
print("---- 相对路径上下文抽样 ----")
for rel, t in texts.items():
    if not rel.endswith(".js"):
        continue
    for m in re.finditer(r"""["']/api["']""", t):
        s = max(0, m.start() - 70)
        print("  [%s] ...%s..." % (rel, t[s:m.end() + 40].replace("\n", " ")))
        break
    for m in re.finditer(r"""["']/static/upload/["']""", t):
        s = max(0, m.start() - 70)
        print("  [%s] ...%s..." % (rel, t[s:m.end() + 40].replace("\n", " ")))
        break

p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_out", "DIST_SCAN.json")
json.dump(out, io.open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("已写入 %s" % p)
