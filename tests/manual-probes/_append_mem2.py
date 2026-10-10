# -*- coding: utf-8 -*-
"""向工作记忆 2026-10-01.md 追加"PC 端三登录页 UI 重构"章节，并回读校验关键串。"""
import io
import os

MEM = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\.workbuddy\memory\2026-10-01.md'

NOTE = """

## 2026-10-01（续）PC 端三登录页 UI 重构 —— /admin/login、/doctor/login、/coach/login

**范围（严格）**：只改 3 个登录页的 `<template>` + `<style>`；`<script setup>` 一字未动。
- 改：`src/views/{admin,doctor,coach}/Login.vue`
- 新增：`src/assets/login-portal.css`、`src/assets/images/login/{admin,doctor,coach}-login-illustration.webp`（1536×950，82~104KB）
- 未动：`api/*`、`utils/*`、`router/*`、`views/*/Register.vue`、`assets/login.css`、`assets/styles.css`、`views/portal/IdentitySelect.vue`

**版式**：`.lp > .lp__art`（绝对定位插画，`mask-image` 向右淡出）+ `.lp__inner`（`.lp__brand` 品牌 + `.lp__main` 两列）
→ 左 `.lp__copy`（2 行短标题 + 3 个功能小项）/ 右 `.lp__card`（403px、圆角 22px、white/0.9、
`backdrop-filter: blur(16px) saturate(135%)`）。输入/按钮高 50px，主按钮主题渐变 + 箭头图标。
主题变量 `.lp--admin` / `.lp--doctor` / `.lp--coach` = `#6d4ae0` / `#0fa98e` / `#1e6fff`。
管理员无注册入口；医生/教练保留「申请注册」真实跳转。

**踩坑（已修）**
1. `.lp` 初版 `grid-template-rows: auto minmax(0,1fr)` → 卡片无法垂直居中；改 `grid-template-rows: 1fr`
   单行 + `.lp__main` 同样 1fr + `align-items: center` 才真正居中（实测中心 y 与视口中线差 ≤46px）。
2. 插画初版构图压到文案 / 人物被裁 → 重生成提示词（人物+场景占右半、左侧留白、全身可见）。
3. ImageGen 右下角带「AI生成」水印 → `_prep_illustrations.py` 裁掉后保留 950px 高再转 webp。

**验收**：`_verify_login.py` **89/89 PASS**（104s），覆盖需求 22 项。
- 三档分辨率 1366×768 / 1440×900 / 1920×1080 均 `scrollWidth == clientWidth`，卡片与文案不重叠；
- admin / doctor001 / coach001 真登录 HTTP 200 + 跳转 `/xxx/dashboard` + Token 落地；
- doctor003 / coach003 待审核被拦 HTTP 400「账号正在审核中」+ 停留登录页 + 无 Token；
- 15 个业务文件 mtime 零改动、src 改动集合 == 期望集合、`<script setup>` 原业务语句齐全；
- `npm run build` EXIT=0，`built in 24.67s` / 2287 modules，产物含 3 张插画 + `Login-*.css` 7.01kB。

**新增脚手架结论（已回写 skill `vite-spa-headless-cdp-verify` 坑 9 / 坑 10）**
- `Input.dispatchMouseEvent` 在 `--headless=new` 下会**间歇性丢事件**：按钮矩形正确、
  `elementFromPoint` 命中按钮、`hasFocus()=true`、无滚动，但 click 计数 0。它**不是单调退化**（同一脚本重跑可能全过）。
  判据 = 按钮上装捕获型 click 计数器（`0` = 注入问题；`>=1` = 业务问题）；
  修法 = 真鼠标 → 强制产帧重试 → DOM `el.click()` 兜底，并把实际路径记进 `CLICKLOG` 如实报告。
  本轮 89 项里 5 次提交登录**全部真鼠标**（未用到兜底）。
- 负向用例（待审核 → 后端故意返回 400）会让 Chrome 记 `Failed to load resource: ... 400 (BAD REQUEST)`；
  「Console 0 红色错误」断言必须**按端点 + 状态码白名单放行**，否则会被自己的负向用例打成 FAIL。
"""


def main():
    raw = open(MEM, 'rb').read()
    txt = raw.decode('utf-8')
    if 'PC 端三登录页 UI 重构' in txt:
        print('SKIP: 章节已存在，未重复追加')
        return 0
    nl = '\r\n' if '\r\n' in txt else '\n'
    body = NOTE.replace('\n', nl).lstrip(nl)
    with io.open(MEM, 'a', encoding='utf-8', newline='') as f:
        f.write(nl + nl + body)

    back = open(MEM, 'rb').read().decode('utf-8')
    marks = ['PC 端三登录页 UI 重构', 'login-portal.css', '89/89 PASS',
             '间歇性丢事件', 'CLICKLOG', 'built in 24.67s', 'login-illustration.webp']
    for m in marks:
        print('  %-26s x%d' % (m, back.count(m)))
    print('BYTES %d -> %d' % (len(raw), len(back.encode('utf-8'))))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
