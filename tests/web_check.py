# -*- coding: utf-8 -*-
"""PC 管理端静态检查：构建产物、依赖、路由完整性、角色守卫、配置唯一来源、禁用项。

运行方式：
  cd health-management-system/tests
  python web_check.py
"""
import io
import json
import os
import re
import sys

TESTS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(TESTS, ".."))
WEB = os.path.join(ROOT, "management-web")
SRC = os.path.join(WEB, "src")

OUT = []


def add(name, ok, detail=""):
    OUT.append({"name": name, "status": "PASS" if ok else "FAIL",
                "detail": "" if ok else str(detail)[:400]})
    print("[%s] %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "  => " + str(detail)[:300]))


def read(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def walk_src(exts=(".vue", ".js")):
    for base, dirs, files in os.walk(SRC):
        dirs[:] = [d for d in dirs if d not in ("node_modules", "dist")]
        for f in files:
            if f.endswith(exts):
                yield os.path.join(base, f)


print("=" * 78)
print("PC 管理端静态检查  WEB =", WEB)
print("=" * 78)

# ---------- 1. 依赖 ----------
pkg = json.loads(read(os.path.join(WEB, "package.json")))
deps = dict(pkg.get("dependencies", {}))
deps.update(pkg.get("devDependencies", {}))
need_deps = ["vue", "vue-router", "element-plus", "axios", "echarts", "vite", "@vitejs/plugin-vue"]
lack_dep = [d for d in need_deps if d not in deps]
add("技术栈依赖齐备（Vue3/Vite/ElementPlus/VueRouter/Axios/ECharts）", not lack_dep, lack_dep)
add("node_modules 已安装", os.path.isdir(os.path.join(WEB, "node_modules")), "未安装")

# ---------- 2. 构建产物 ----------
dist = os.path.join(WEB, "dist")
add("vite build 产物 dist/ 存在", os.path.isdir(dist), dist)
if os.path.isdir(dist):
    idx = os.path.join(dist, "index.html")
    add("dist/index.html 存在", os.path.exists(idx), idx)
    assets = os.path.join(dist, "assets")
    files = os.listdir(assets) if os.path.isdir(assets) else []
    js = [f for f in files if f.endswith(".js")]
    css = [f for f in files if f.endswith(".css")]
    add("dist/assets 含 %d 个 JS 与 %d 个 CSS 产物" % (len(js), len(css)),
        len(js) >= 20 and len(css) >= 1, "js=%d css=%d" % (len(js), len(css)))
    # 每个角色页面都应被拆分为独立 chunk
    names = " ".join(files)
    role_chunks = {
        "医生页面": all(n in names for n in ("Dashboard", "Patients", "Health", "Trends", "Advice", "Notices", "Records")),
        "教练页面": all(n in names for n in ("Students", "Sports", "Goals", "Training")),
        "管理员页面": all(n in names for n in ("Users", "Doctors", "Coaches", "Audit", "Relations",
                                                "HealthData", "Plans", "DoctorBusiness", "CoachBusiness",
                                                "Content", "System")),
    }
    lack_chunk = [k for k, v in role_chunks.items() if not v]
    add("三种角色的页面均被独立打包为路由 chunk", not lack_chunk, lack_chunk)

# ---------- 3. 路由完整性（需求八十四 明确列出的路由） ----------
REQUIRED_ROUTES = {
    "doctor": ["/doctor/login", "/doctor/register", "/doctor/dashboard", "/doctor/patients",
               "/doctor/health", "/doctor/trends", "/doctor/advice", "/doctor/notices",
               "/doctor/records", "/doctor/profile"],
    "coach": ["/coach/login", "/coach/register", "/coach/dashboard", "/coach/students",
              "/coach/sports", "/coach/goals", "/coach/training", "/coach/advice",
              "/coach/profile"],
    "admin": ["/admin/login", "/admin/dashboard", "/admin/users", "/admin/doctors",
              "/admin/coaches", "/admin/audit", "/admin/relations", "/admin/health-data",
              "/admin/plans", "/admin/doctor-business", "/admin/coach-business",
              "/admin/content", "/admin/system"],
}
router_text = {}
for role in REQUIRED_ROUTES:
    router_text[role] = read(os.path.join(SRC, "router", role + ".js"))

for role, paths in REQUIRED_ROUTES.items():
    text = router_text[role]
    miss = []
    for p in paths:
        leaf = p.split("/")[-1]
        # 子路由写成相对 path: 'xxx'，登录页写成完整 path: '/role/login'
        if ("path: '%s'" % leaf) not in text and ("path: '/%s/%s'" % (role, leaf)) not in text:
            miss.append(p)
    add("%s 端 %d 条路由全部定义" % ({"doctor": "医生", "coach": "教练", "admin": "管理员"}[role],
                                     len(paths)), not miss, miss)

# 所有懒加载视图文件真实存在
bad_views = []
for p in walk_src((".js",)):
    for m in re.finditer(r"import\(\s*'(@/[^']+\.vue)'\s*\)", read(p)):
        rel = m.group(1)[2:]
        if not os.path.exists(os.path.join(SRC, rel)):
            bad_views.append("%s -> %s" % (os.path.relpath(p, SRC), m.group(1)))
add("全部路由懒加载视图文件均存在", not bad_views, bad_views[:8])

# ---------- 4. 路由守卫 ----------
rt = read(os.path.join(SRC, "router", "index.js"))
add("存在全局前置守卫 beforeEach", "beforeEach" in rt, "")
add("守卫校验角色自己的 Token（isLogin(role)）", "isLogin(role)" in rt, "")
add("角色不匹配/未登录 → 跳转该角色登录页",
    "ROLE_META[role].loginPath" in rt and "redirect" in rt, "")
add("后端 401 → 清除对应角色 Token 并跳回其登录页",
    "setUnauthorizedHandler" in rt and "clearAuth(role)" in rt, "")
add("已登录访问登录页 → 直接进入该角色工作台", "ROLE_META[role].homePath" in rt, "")

# ---------- 5. 管理员 12 个一级模块且不新增 ----------
admin_router = router_text["admin"]
menus = re.findall(r"\{\s*path:\s*'(/admin/[^']+)',\s*title:\s*'([^']+)'", admin_router)
add("管理员左侧导航固定 12 个一级模块", len(menus) == 12, [m[1] for m in menus])
expect_titles = ["01 系统首页", "02 普通用户管理", "03 医生管理", "04 健身教练管理",
                 "05 账号审核中心", "06 角色关系管理", "07 健康数据中心", "08 健康计划管理",
                 "09 医生业务监管", "10 健身业务监管", "11 内容运营管理", "12 系统管理"]
add("12 个一级模块名称与顺序与需求一致", [m[1] for m in menus] == expect_titles,
    [m[1] for m in menus])

# ---------- 6. 三角色 Dashboard / 菜单 / 布局彼此独立 ----------
shells = {
    "doctor": os.path.join(SRC, "views", "doctor", "DoctorShell.vue"),
    "coach": os.path.join(SRC, "views", "coach", "CoachShell.vue"),
    "admin": os.path.join(SRC, "views", "admin", "AdminShell.vue"),
}
missing_shell = [k for k, v in shells.items() if not os.path.exists(v)]
add("三种角色各自拥有独立 Shell（布局/菜单/主题）", not missing_shell, missing_shell)
menu_sets = {}
for role in shells:
    t = router_text[role]
    menu_sets[role] = sorted(set(re.findall(r"title:\s*'([^']+)'", t)) - set(["XX"]))
add("医生 / 教练 / 管理员 菜单集合互不相同",
    len({json.dumps(v, ensure_ascii=False) for v in menu_sets.values()}) == 3,
    {k: len(v) for k, v in menu_sets.items()})

# ---------- 7. 接口地址唯一来源 ----------
# 设计约定：
#   utils/config.js  = 全项目唯一 API 地址来源（读取 VITE_API_BASE_URL，并以相对 /api 兜底）
#   .env.production  = 生产同源相对路径 /api（由同源 Web Server 反向代理到 Flask:8080）
#   .env.development = 开发走 Vite 代理 /api -> VITE_PROXY_TARGET:8080（避免跨域与硬编码 IP）
cfg_src = read(os.path.join(SRC, "utils", "config.js"))
env_dev = read(os.path.join(WEB, ".env.development"))
add("utils/config.js 读取 VITE_API_BASE_URL 并以相对 /api 兜底（不含硬编码 IP）",
    "import.meta.env.VITE_API_BASE_URL" in cfg_src
    and "'/api'" in cfg_src and "192.168." not in cfg_src, "")
prod = read(os.path.join(WEB, ".env.production"))
add(".env.production 使用同源相对路径 /api（不含硬编码 IP）",
    "VITE_API_BASE_URL=/api" in prod and "192.168." not in prod, prod.strip()[:120])
add(".env.development 走代理且代理目标为 8080",
    "VITE_API_BASE_URL=/api" in env_dev and "VITE_PROXY_TARGET=http://127.0.0.1:8080" in env_dev,
    env_dev.strip()[:160])
vite_cfg = read(os.path.join(WEB, "vite.config.js"))
add("vite 代理 /api 与 /static 到后端 8080",
    "'/api'" in vite_cfg and "'/static'" in vite_cfg and "proxyTarget" in vite_cfg, "")
add("Axios 的 baseURL 取自 utils/config.js（未在页面中硬编码）",
    "API_BASE_URL" in read(os.path.join(SRC, "api", "request.js")), "")
ip_hits = []
for p in walk_src():
    rel = os.path.relpath(p, SRC)
    if rel in (os.path.join("utils", "config.js"),):
        continue
    for m in re.finditer(r"https?://\d+\.\d+\.\d+\.\d+", read(p)):
        ip_hits.append("%s -> %s" % (rel, m.group(0)))
add("除 utils/config.js 外无硬编码 IP", not ip_hits, ip_hits[:8])

# ---------- 8. 禁用项 ----------
banned = ["TODO", "此处省略", "后续自行实现", "根据实际情况补充"]
hits = []
for p in walk_src():
    text = read(p)
    for token in banned:
        if token in text:
            hits.append("%s -> %s" % (os.path.relpath(p, SRC), token))
add("无 TODO / 省略 / 未实现标记", not hits, hits[:8])

port_hits = []
for base, dirs, files in os.walk(WEB):
    dirs[:] = [d for d in dirs if d not in ("node_modules", "dist", ".git")]
    for f in files:
        if not f.endswith((".js", ".vue", ".json", ".env", ".development", ".production", ".html", ".css")):
            continue
        p = os.path.join(base, f)
        text = read(p)
        for token in (":5000", ":5001", "port=5000", "port=5001", "PORT=5000", "PORT=5001"):
            if token in text:
                port_hits.append("%s -> %s" % (os.path.relpath(p, WEB), token))
add("PC 端无 5000/5001 端口", not port_hits, port_hits[:5])

mock_hits = []
for p in walk_src():
    t = read(p)
    if re.search(r"(mockData|fakeData|MOCK_|__mock__)", t, re.I):
        mock_hits.append(os.path.relpath(p, SRC))
add("PC 端无 Mock 假数据标识", not mock_hits, mock_hits[:8])

# ---------- 9. Axios 统一封装 ----------
req = read(os.path.join(SRC, "api", "request.js"))
add("Axios 统一封装：baseURL 来自 utils/config.js（唯一来源）",
    "API_BASE_URL" in req and "from '@/utils/config'" in req, "")
add("Axios 请求拦截器自动携带角色 Token", "Authorization" in req and "Bearer" in req, "")
add("Axios 响应拦截器按角色处理 401", "401" in req and "setUnauthorizedHandler" in req, "")
add("统一解析 {code,msg,data} 契约", "code" in req and "msg" in req and "data" in req, "")
add("三角色各自独立的请求实例（Token 不串用）",
    all(k in req for k in ("doctorRequest", "coachRequest", "adminRequest")), "")

passed = len([x for x in OUT if x["status"] == "PASS"])
failed = [x for x in OUT if x["status"] == "FAIL"]
print("\n" + "=" * 78)
print("PC 端静态检查汇总：共 %d 项，PASS %d 项，FAIL %d 项" % (len(OUT), passed, len(failed)))
print("=" * 78)
if failed:
    for x in failed:
        print("FAIL", x["name"], "=>", x["detail"])

with io.open(os.path.join(TESTS, "web_check_result.json"), "w", encoding="utf-8") as fh:
    json.dump({"total": len(OUT), "pass": passed, "fail": len(failed), "items": OUT},
              fh, ensure_ascii=False, indent=2)
print("明细已写入：", os.path.join(TESTS, "web_check_result.json"))
sys.exit(0 if not failed else 1)
