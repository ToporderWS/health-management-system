# -*- coding: utf-8 -*-
"""安全追加本轮工作记忆：先回退上一次被 bash 反引号展开破坏的追加，再写正确正文。
（本机陷阱：python -c "..." 里的反引号 / $ 会被 bash 命令替换 → 静默损坏。）"""
import os

P = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\.workbuddy\memory\2026-10-01.md'
MARK = '## PC 端身份选择首页「CSS 轻动态背景」'

BODY = '''## PC 端身份选择首页「CSS 轻动态背景」（IdentitySelect.vue）

**范围**：仍只改 management-web/src/views/portal/IdentitySelect.vue 一个产品文件（16344 -> 23583 B）。
后端 / MySQL / API / JWT / 权限 / router / identities / enter(item) / ROLE_META / 医生·教练·管理员页面 / 小程序 全未触碰。
**零 JS**：装饰层是纯 template 的 5 个 span + scoped CSS keyframes，无 rAF、无第三方动画库、无新增 npm 依赖。

### 新增 9 条动画（8 组 keyframes）
- 云层 A/B/C —— .portal__cloud--1/2/3 —— 58s / 76s / 67s —— background repeat-x 位移，linear infinite
- 阳光呼吸 —— .portal__sun —— 11s —— scale 1→1.03 + opacity 弱呼吸，ease-in-out
- 湖面微光 —— .portal__shine —— 23s —— mask-image 渐隐 + linear 位移
- 整体微呼吸 —— .portal__bg / .portal__bg-photo —— 42s —— scale 1→1.015
- 远山景深 —— .portal__bg::before —— 38s —— translate 极小
- 近景景深 —— .portal__bg::after —— 31s —— translate 极小

层级契约：bg(0) < bg-photo(1) < veil(2) < fx(2，DOM 在 veil 之后) < 内容(3)；
装饰层及其 6 个子元素全部 pointer-events:none；fx 层 aria-hidden=true + overflow:hidden。

### 关键真实缺陷与修法（★ 可复用）
1. **满视口 transform:scale() 计入文档可滚动溢出** ⇒ 背景呼吸把 scrollHeight 顶高 6px ⇒ 出现纵向滚动条
   ⇒ clientWidth 在 1366/1351 之间跳 ⇒ **全部内容横移 7.5px（CLS）**。
   _diag_overflow.py 做 A/B/C 实证（动画 ON：over 0→6、clientWidth={1351,1366}；注入 animation:none 后 over=0、clientWidth={1366}）。
   **修法：.portal 由 overflow-x:clip 改为 overflow:clip（双轴）** ⇒ CLS=0、clientWidth 恒 1366、fps 不变。
2. **RecalcStyleCount 每帧 +1 是 Chrome 固有行为，不是缺陷**：_diag_perf.py / _diag_perf2.py 证明只要任意 CSS 动画在跑就 ~1 recalc/帧
   （7 种层组合 fps 143.6~144.2、dLayout 恒 0）。断言须写「≤1 次/帧」，不要写「≈0」。
3. **无头 Chrome 下 CSS 动画时间线只在"产帧"时推进**：采样 getComputedStyle().transform 前必须 Page.captureScreenshot 强制产帧，
   否则 transform 永远不变，会误判"动画没跑"。
4. 性能口径要用 **GPU vs 软件渲染对照**（--disable-gpu）：GPU 143fps / 软件 19fps，
   WebGL UNMASKED_RENDERER_WEBGL = Intel UHD Graphics 证实真机走 GPU。

### 验证结果（真实 Chrome + CDP，_verify_anim.py）
**64 PASS / 0 FAIL（101s）**：三入口真实鼠标点击分别跳 /doctor/login、/coach/login、/admin/login；
1366x768 / 1440x900 / 1920x1080 均无横向滚动；1366x620 与 1366x520 无裁剪；
prefers-reduced-motion:reduce 下 7 个动画全 none 且静态视觉仍在，取消后恢复；
60s 长跑 dLayout=0、dStyle=1.00/帧、longtasks=0、CLS=0.000000、clientWidth 恒 1366、Console 0 新增错误。

### 强度量化（_measure_anim_delta.py，Pillow 逐像素时间序列）
纯背景区最大 mean|Δ| = 3.28（山景带 3.22 / 湖面带 1.18 / 阳光区 0.89 / 云层 0.25~0.44）
=> 落在「克制但可察觉」推荐区间（1~12）；_cmp_pixels.py 静态侵入亮度差 ≤3.0。

### 构建
npm run build（须追加 --script-shell=cmd.exe，本机 npm 默认 shell 解析到缺失的 bash）
**EXIT=0 / built in 23.39s / 2287 modules transformed**；
产物 dist/assets/IdentitySelect-BddK09gW.css（12151 B）内含全部 6 组 keyframes + prefers-reduced-motion；
JS chunk IdentitySelect-NoAiWj_I.js 仅 4936 B（佐证页面无 JS 动画）。

### 资产
产品：仅 management-web/src/views/portal/IdentitySelect.vue
验证脚本（临时，均在 management-web/）：_verify_anim.py（主，64 项）、_measure_anim_delta.py、_cmp_pixels.py、
_diag_overflow.py、_diag_perf.py、_diag_perf2.py、_diag_fps.py、_run_build2.py、_tune_anim.py、_patch_anim.py + 4 个 _fix_*.py。
截图证据：management-web/_verify_out/identity-select-anim-1366x768.png、identity-select-anim-1920x1080.png、_visframe_00/06/12/20.png。
'''


def main():
    raw = open(P, 'rb').read()
    orig_len = len(raw)
    mb = MARK.encode('utf-8')
    idx = raw.find(mb)
    if idx > 0:
        # 回退到标题前，并吃掉多余空行
        cut = idx
        while cut > 0 and raw[cut - 1:cut] in (b'\n', b'\r'):
            cut -= 1
        raw = raw[:cut]
        print('detected previous (broken) append at byte %d, rolled back to %d' % (idx, cut))
    else:
        print('no previous append marker found; file len = %d' % orig_len)

    crlf = raw.count(b'\r\n') > 0
    nl = b'\r\n' if crlf else b'\n'
    out = raw + nl + nl + BODY.strip().encode('utf-8') + nl
    with open(P, 'wb') as f:
        f.write(out)
    print('eol = %s' % ('CRLF' if crlf else 'LF'))
    print('written bytes = %d' % len(out))

    # 自校验：关键串必须存在且仅一次
    t = open(P, 'rb').read().decode('utf-8')
    for kw in ['mean|Δ| = 3.28', 'overflow:clip（双轴）', 'IdentitySelect-BddK09gW.css',
               '64 PASS / 0 FAIL', 'enter(item)', 'ROLE_META']:
        print('  check %-32s -> %d' % (kw, t.count(kw)))
    print('  heading count -> %d' % t.count(MARK))


if __name__ == '__main__':
    main()
