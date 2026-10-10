# -*- coding: utf-8 -*-
"""小程序端静态检查：页面注册、资源引用、import 解析、接口地址唯一来源、禁用项扫描。

运行方式：
  cd health-management-system/tests
  python miniapp_check.py
"""
import io
import json
import os
import re
import sys

TESTS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(TESTS, ".."))
APP = os.path.join(ROOT, "miniapp")

OUT = []


def add(name, ok, detail=""):
    OUT.append({
        "name": name,
        "status": "PASS" if ok else "FAIL",
        "detail": "" if ok else str(detail)[:400],
    })
    print("[%s] %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  => " + str(detail)[:300]))


def read(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def walk_vue():
    for base, dirs, files in os.walk(APP):
        dirs[:] = [d for d in dirs if d not in ("node_modules", "unpackage", "__pycache__")]
        for f in files:
            if f.endswith(".vue"):
                yield os.path.join(base, f)


print("=" * 78)
print("小程序端静态检查  APP =", APP)
print("=" * 78)

# ---------- 1. pages.json 结构 ----------
pages_json_path = os.path.join(APP, "pages.json")
add("pages.json 存在", os.path.exists(pages_json_path), pages_json_path)
cfg = json.loads(read(pages_json_path))
pages = [p["path"] for p in cfg.get("pages", [])]
add("pages.json 可解析且含 pages", len(pages) > 0, len(pages))

# ---------- 2. 每个页面都有真实 .vue 文件 ----------
missing_pages = [p for p in pages if not os.path.exists(os.path.join(APP, p + ".vue"))]
add("pages.json 注册的 %d 个页面均存在真实 .vue 文件" % len(pages), not missing_pages, missing_pages)

# 需求要求的最少页面
REQUIRED_PAGES = {
    "pages/index/index": "首页",
    "pages/login/index": "登录",
    "pages/register/index": "注册",
    "pages/health-entry/index": "健康录入",
    "pages/report/index": "数据报告",
    "pages/article/index": "健康科普列表",
    "pages/article-detail/index": "文章详情",
    "pages/doctor-advice/index": "医生建议",
    "pages/medical-notice/index": "体检通知",
    "pages/medical-record/index": "医疗记录",
    "pages/sport-goal/index": "运动目标",
    "pages/training-plan/index": "训练计划",
    "pages/fitness-advice/index": "健身建议",
    "pages/profile/index": "我的",
    "pages/plan/index": "健康计划",
}
lack = [v for k, v in REQUIRED_PAGES.items() if k not in pages]
add("需求要求的 %d 个页面全部已注册" % len(REQUIRED_PAGES), not lack, lack)

# ---------- 3. TabBar 固定四项 + 图标文件 ----------
tab = cfg.get("tabBar", {}).get("list", [])
tab_paths = [t["pagePath"] for t in tab]
want_tab = ["pages/index/index", "pages/health-entry/index", "pages/report/index", "pages/profile/index"]
add("TabBar 固定为 首页/健康录入/数据报告/我的", tab_paths == want_tab, tab_paths)
icons = []
for t in tab:
    icons.extend([t.get("iconPath", ""), t.get("selectedIconPath", "")])
missing_icons = [i for i in icons if i and not os.path.exists(os.path.join(APP, i))]
add("TabBar %d 个图标文件齐备" % len(icons), not missing_icons, missing_icons)

# ---------- 4. easycom 组件与 uCharts 库 ----------
uc_vue = os.path.join(APP, "components", "u-charts", "u-charts.vue")
uc_js = os.path.join(APP, "components", "u-charts", "u-charts.js")
add("uCharts 封装组件存在", os.path.exists(uc_vue), uc_vue)
add("uCharts 官方库存在", os.path.exists(uc_js) and os.path.getsize(uc_js) > 10000,
    os.path.getsize(uc_js) if os.path.exists(uc_js) else "缺失")
if os.path.exists(uc_js):
    lib = read(uc_js)
    add("uCharts 库为 ESM 默认导出", "export default uCharts" in lib, lib[-80:])

# 图表组件是否真的被数据报告页使用
report = read(os.path.join(APP, "pages", "report", "index.vue"))
add("数据报告页使用 <u-charts> 组件", "<u-charts" in report, "")
for kind in ("weight_trend", "blood_pressure_trend", "sport_daily", "sleep_quality", "plan_list"):
    if kind not in report:
        add("数据报告读取后端字段 %s" % kind, False, "字段缺失")
add("数据报告读取 5 类后端真实字段", all(
    k in report for k in ("weight_trend", "blood_pressure_trend", "sport_daily", "sleep_quality", "plan_list")))

# ---------- 5. 全部 @/ import 可解析 ----------
bad_imports = []
for p in walk_vue():
    text = read(p)
    for m in re.finditer(r'from\s+[\'"](@/[^\'"]+)[\'"]', text):
        target = m.group(1)[2:]
        cands = [os.path.join(APP, target), os.path.join(APP, target + ".js"),
                 os.path.join(APP, target + ".vue"), os.path.join(APP, target, "index.js")]
        if not any(os.path.exists(c) for c in cands):
            bad_imports.append("%s -> %s" % (os.path.relpath(p, APP), m.group(1)))
# 同时扫描 common/ 与 api/ 下的 js
for base, dirs, files in os.walk(APP):
    dirs[:] = [d for d in dirs if d not in ("node_modules", "unpackage", "__pycache__")]
    for f in files:
        if not f.endswith(".js"):
            continue
        p = os.path.join(base, f)
        for m in re.finditer(r'from\s+[\'"](@/[^\'"]+)[\'"]', read(p)):
            target = m.group(1)[2:]
            cands = [os.path.join(APP, target), os.path.join(APP, target + ".js"),
                     os.path.join(APP, target + ".vue"), os.path.join(APP, target, "index.js")]
            if not any(os.path.exists(c) for c in cands):
                bad_imports.append("%s -> %s" % (os.path.relpath(p, APP), m.group(1)))
add("全部 @/ 别名 import 均可解析", not bad_imports, bad_imports[:8])

# ---------- 6. API 地址唯一来源 ----------
# 口径：只校验「唯一来源」这一语义不变式（config.js 内声明了指向 :8080/api 的绝对地址），
# 不写死具体网段 —— 局域网 IP 随路由器分配变化，写死会产出假性 FAIL。
cfgjs = read(os.path.join(APP, "common", "config.js"))
_cfg_m = re.search(r"""API_BASE_URL\s*=\s*['"]https?://[\d.]+:8080/api['"]""", cfgjs)
add("API 基础地址在 common/config.js 中定义",
    bool(_cfg_m), "config.js 内含 API_BASE_URL='http://<ip>:8080/api'" if not _cfg_m else "")
ip_hits = []
for base, dirs, files in os.walk(APP):
    dirs[:] = [d for d in dirs if d not in ("node_modules", "unpackage", "__pycache__")]
    for f in files:
        if not f.endswith((".vue", ".js")):
            continue
        p = os.path.join(base, f)
        if os.path.relpath(p, APP) == os.path.join("common", "config.js"):
            continue
        text = read(p)
        for m in re.finditer(r'https?://\d+\.\d+\.\d+\.\d+', text):
            ip_hits.append("%s -> %s" % (os.path.relpath(p, APP), m.group(0)))
add("除 config.js 外无任何硬编码 IP 地址", not ip_hits, ip_hits[:8])

# ---------- 7. 页面跳转目标均已注册 ----------
bad_nav = []
registered = set("/" + p for p in pages)
for p in walk_vue():
    text = read(p)
    for m in re.finditer(r'url:\s*[\'"`](/pages/[^\'"`?]+)', text):
        u = m.group(1)
        if u not in registered:
            bad_nav.append("%s -> %s" % (os.path.relpath(p, APP), u))
add("所有 navigateTo/switchTab 目标均已注册", not bad_nav, bad_nav[:8])

# tabBar 页面禁止用 navigateTo（微信小程序限制）
tab_nav_bad = []
for p in walk_vue():
    text = read(p)
    for m in re.finditer(r'navigateTo\(\{\s*url:\s*[\'"`](/pages/(?:index|health-entry|report|profile)/index)', text):
        tab_nav_bad.append("%s -> %s" % (os.path.relpath(p, APP), m.group(1)))
add("TabBar 页面未被错误地使用 navigateTo 打开", not tab_nav_bad, tab_nav_bad[:5])

# ---------- 8. 禁用项扫描 ----------
banned = {
    "TODO": "TODO 占位",
    "此处省略": "省略标记",
    "后续自行实现": "未实现标记",
    "根据实际情况补充": "未实现标记",
}
hits = []
for p in list(walk_vue()) + [os.path.join(APP, a, b) for a, b in
                            (("common", "config.js"), ("common", "auth.js"),
                             ("common", "request.js"), ("api", "index.js"))]:
    if not os.path.exists(p):
        continue
    text = read(p)
    for token, label in banned.items():
        if token in text:
            hits.append("%s -> %s" % (os.path.relpath(p, APP), label))
add("无 TODO / 省略 / 未实现标记", not hits, hits[:8])

# 假数据 / Mock 扫描（业务页面不得内置固定假数据集）
mock_hits = []
for p in walk_vue():
    rel = os.path.relpath(p, APP)
    if rel.startswith(os.path.join("components", "")):
        continue
    text = read(p)
    if re.search(r'(mockData|fakeData|MOCK_|__mock__)', text, re.I):
        mock_hits.append(rel)
add("业务页面无 Mock 假数据标识", not mock_hits, mock_hits)

# 端口禁用
port_hits = []
for base, dirs, files in os.walk(APP):
    dirs[:] = [d for d in dirs if d not in ("node_modules", "unpackage", "__pycache__")]
    for f in files:
        if not f.endswith((".vue", ".js", ".json", ".md")):
            continue
        p = os.path.join(base, f)
        text = read(p)
        for token in (":5000", ":5001", "port=5000", "port=5001"):
            if token in text:
                port_hits.append("%s -> %s" % (os.path.relpath(p, APP), token))
add("小程序端无 5000/5001 端口", not port_hits, port_hits[:5])

# ---------- 9. 结构完整性 ----------
# 说明：App.vue 是 uni-app 根组件，惯例上无 <template>、使用 Options API 并承载全局样式，
# 因此单独按其自身规范校验；其余页面均为 <template> + <script setup> + scoped 样式。
struct_bad = []
for p in walk_vue():
    rel = os.path.relpath(p, APP)
    text = read(p)
    if rel == "App.vue":
        if "<style>" not in text:
            struct_bad.append("App.vue 缺少全局 <style>")
        if "onLaunch" not in text:
            struct_bad.append("App.vue 缺少生命周期 onLaunch")
        continue
    if "<template>" not in text or "</template>" not in text:
        struct_bad.append(rel + " 缺少 template")
    if "<script setup>" not in text:
        struct_bad.append(rel + " 缺少 <script setup>")
    if "<style scoped>" not in text:
        struct_bad.append(rel + " 缺少 scoped 样式")
add("全部页面 .vue 含 template / script setup / scoped 样式（App.vue 按根组件规范校验）",
    not struct_bad, struct_bad[:8])

# ---------- 10. 登录态与接口正确性 ----------
req = read(os.path.join(APP, "common", "request.js"))
add("请求层统一携带 Authorization: Bearer", "Bearer" in req, "")
add("请求层统一处理 401 → 清除登录态并跳登录", "handleUnauthorized" in req and "clearAuth" in req, "")
api_idx = read(os.path.join(APP, "api", "index.js"))
need_api = ["/user/register", "/user/login", "/user/info", "/health_record/add",
            "/sleep_record/add", "/sport_record/add", "/health_plan/add",
            "/report/statistics", "/article/list", "/notice/list",
            "/user/doctor_advice", "/user/medical_notice", "/user/medical_record",
            "/user/sport_goal", "/user/training_plan", "/user/fitness_advice"]
lack_api = [a for a in need_api if a not in api_idx]
add("小程序 API 层覆盖需求要求的 %d 个接口" % len(need_api), not lack_api, lack_api)

# ---------- 汇总 ----------
passed = len([x for x in OUT if x["status"] == "PASS"])
failed = [x for x in OUT if x["status"] == "FAIL"]
print("\n" + "=" * 78)
print("小程序静态检查汇总：共 %d 项，PASS %d 项，FAIL %d 项" % (len(OUT), passed, len(failed)))
print("=" * 78)
if failed:
    for x in failed:
        print("FAIL", x["name"], "=>", x["detail"])

with io.open(os.path.join(TESTS, "miniapp_check_result.json"), "w", encoding="utf-8") as fh:
    json.dump({"total": len(OUT), "pass": passed, "fail": len(failed), "items": OUT},
              fh, ensure_ascii=False, indent=2)
print("明细已写入：", os.path.join(TESTS, "miniapp_check_result.json"))
sys.exit(0 if not failed else 1)
