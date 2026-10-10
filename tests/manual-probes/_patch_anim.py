# -*- coding: utf-8 -*-
"""
IdentitySelect.vue —— 追加 CSS 轻动态背景（纯追加，非破坏性）。

安全策略（对齐工程纪律）：
  1. 读原始字节 -> 解码，先判定行尾；行尾混合则整体中止（避免整文件 diff 爆炸）。
  2. 三个锚点必须各命中恰好 1 次；任一未命中 => 不写盘，打印诊断后退出。
  3. 只做「锚点 + 追加」，不删除、不重写任何既有声明。
  4. 写盘前做括号配平与关键标记自检。
"""
import io
import os
import sys

P = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system\management-web\src\views\portal\IdentitySelect.vue'

# ----------------------------------------------------------------- 追加内容
INS_TEMPLATE = '''
    <!-- 轻动态背景装饰层（纯 CSS：云层漂移 / 阳光呼吸 / 湖面微光）；全层 pointer-events:none，不拦截点击 -->
    <div class="portal__fx" aria-hidden="true">
      <span class="portal__cloud portal__cloud--1"></span>
      <span class="portal__cloud portal__cloud--2"></span>
      <span class="portal__cloud portal__cloud--3"></span>
      <span class="portal__sun"></span>
      <span class="portal__shine"></span>
    </div>
'''

INS_CSS_FX = '''
/* ================= 轻动态背景（纯 CSS 合成层动画，无 JS / 无第三方库） =================
   层级契约（自下而上，越靠后越上）：
     .portal__bg(0) < .portal__bg-photo(1) < .portal__bg-veil(2) < .portal__fx(2，DOM 在 veil 之后) < 内容(3)
     装饰层全部 pointer-events:none，绝不拦截身份卡片与三个入口按钮的点击；
     内容层（header / main）不参与任何动画，动画前后位置完全一致。
   实现原则：只动 transform / opacity（合成层完成，不触发重排重绘），不新增 DOM 动画库、不用 JS。
   强度约 2~3 分（满 10 分）：第一眼先看到标题与三个身份入口，观察数秒后才察觉背景在动。 */

/* ---- 装饰层容器 ---- */
.portal__fx {
  position: absolute;
  inset: 0;
  z-index: 2;
  overflow: hidden;
  pointer-events: none;
}

/* ---- ① 云层缓慢漂移：3 层半透明浮云，58s / 76s / 67s，linear infinite ----
   每层元素宽 200% + background-repeat:repeat-x 平铺；位移量恰好等于一个平铺周期
   （background-size-x × 200%），所以循环点完全无缝，不会出现"跳一下"。 */
.portal__cloud {
  position: absolute;
  left: 0;
  width: 200%;
  pointer-events: none;
  background-repeat: repeat-x;
  will-change: transform;
}

.portal__cloud--1 {
  top: 4%;
  height: 19%;
  opacity: 0.5;
  background-size: 26% 100%;
  background-image:
    radial-gradient(closest-side at 16% 64%, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 33% 45%, rgba(255, 255, 255, 0.98), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 50% 62%, rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 70% 74%, rgba(255, 255, 255, 0.66), rgba(255, 255, 255, 0) 100%);
  animation: portal-cloud-drift-a 58s linear infinite;
}

.portal__cloud--2 {
  top: 15%;
  height: 16%;
  opacity: 0.34;
  background-size: 34% 100%;
  background-image:
    radial-gradient(closest-side at 22% 58%, rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 45% 40%, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 68% 66%, rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0) 100%);
  animation: portal-cloud-drift-b 76s linear infinite;
  animation-delay: -24s;
}

.portal__cloud--3 {
  top: 26%;
  height: 13%;
  opacity: 0.26;
  background-size: 20.5% 100%;
  background-image:
    radial-gradient(closest-side at 30% 52%, rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 62% 68%, rgba(255, 255, 255, 0.76), rgba(255, 255, 255, 0) 100%);
  animation: portal-cloud-drift-c 67s linear infinite;
  animation-delay: -47s;
}

@keyframes portal-cloud-drift-a {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(-26%, 0, 0); }
}

@keyframes portal-cloud-drift-b {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(-34%, 0, 0); }
}

@keyframes portal-cloud-drift-c {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(-20.5%, 0, 0); }
}

/* ---- ② 阳光呼吸：右上自然光晕，scale 1 -> 1.03，11s（很弱，不是灯闪） ---- */
.portal__sun {
  position: absolute;
  top: 0;
  right: 0;
  width: 58%;
  height: 62%;
  pointer-events: none;
  transform-origin: 64% 20%;
  background: radial-gradient(
    closest-side at 64% 20%,
    rgba(255, 251, 228, 0.72) 0%,
    rgba(255, 249, 216, 0.38) 40%,
    rgba(255, 247, 212, 0) 76%
  );
  animation: portal-sun-breathe 11s ease-in-out infinite;
  will-change: transform, opacity;
}

@keyframes portal-sun-breathe {
  0%, 100% { transform: scale(1); opacity: 0.62; }
  50% { transform: scale(1.03); opacity: 0.84; }
}

/* ---- ③ 湖面微光：中下部水面极淡反光缓慢横移，23s，上下用 mask 化开（不是波浪、不闪烁） ---- */
.portal__shine {
  position: absolute;
  left: 0;
  bottom: 22%;
  width: 200%;
  height: 22%;
  pointer-events: none;
  opacity: 0.38;
  background-repeat: repeat-x;
  background-size: 22% 100%;
  background-image:
    radial-gradient(closest-side at 24% 56%, rgba(255, 255, 255, 0.52), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 58% 42%, rgba(255, 255, 255, 0.4), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 86% 64%, rgba(255, 254, 244, 0.32), rgba(255, 254, 244, 0) 100%);
  -webkit-mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0) 0%, #000 34%, #000 66%, rgba(0, 0, 0, 0) 100%);
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0) 0%, #000 34%, #000 66%, rgba(0, 0, 0, 0) 100%);
  animation: portal-shine-flow 23s linear infinite;
  will-change: transform;
}

@keyframes portal-shine-flow {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(-22%, 0, 0); }
}

/* ---- ④ 山景景深 + ⑤ 整体微呼吸 ----
   在既有 CSS 风景之上追加动画，不修改原有风光规则的任何声明。
   远山 / 近山林线的位移严格控制在 ±4px、±2px 以内；整体缩放恒 >= 1（1 -> 1.015），
   因此缩放过程中背景始终铺满视口、边缘不会露白，也不会产生横向滚动条。 */
.portal__bg {
  animation: portal-bg-breathe 42s ease-in-out infinite;
  will-change: transform;
}

.portal__bg-photo {
  animation: portal-bg-breathe 42s ease-in-out infinite;
}

.portal__bg::before {
  animation: portal-mountain-far 38s ease-in-out infinite;
  will-change: transform;
}

.portal__bg::after {
  animation: portal-mountain-near 31s ease-in-out infinite;
  will-change: transform;
}

@keyframes portal-bg-breathe {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.015); }
}

@keyframes portal-mountain-far {
  0%, 100% { transform: translate3d(-3px, 1px, 0); }
  50% { transform: translate3d(3px, -1.5px, 0); }
}

@keyframes portal-mountain-near {
  0%, 100% { transform: translate3d(-4px, -2px, 0); }
  50% { transform: translate3d(4px, 2px, 0); }
}
'''

INS_CSS_REDUCED = '''
/* ================= 无障碍：系统开启"减少动态效果"时，停用全部背景动画（静态视觉完整保留） ================= */
@media (prefers-reduced-motion: reduce) {
  .portal__bg,
  .portal__bg-photo,
  .portal__bg::before,
  .portal__bg::after,
  .portal__cloud,
  .portal__sun,
  .portal__shine {
    animation: none !important;
    will-change: auto;
  }
}
'''


def main():
    if not os.path.exists(P):
        print('FATAL: file not found', P)
        return 2
    raw = open(P, 'rb').read()
    src = raw.decode('utf-8')
    lf, crlf = src.count('\n'), src.count('\r\n')
    print('origin bytes :', len(raw))
    print('lines        :', lf, ' CRLF:', crlf)
    if crlf not in (0, lf):
        print('FATAL: 行尾混合，为免整文件 diff 中止')
        return 2
    eol = '\r\n' if crlf else '\n'
    norm = src.replace('\r\n', '\n')
    print('eol          :', repr(eol))

    A = '    <div class="portal__bg-veil" aria-hidden="true"></div>'
    B = ('radial-gradient(78% 44% at 50% 2%, rgba(255, 255, 255, 0.38), rgba(255, 255, 255, 0) 66%);\n'
         '}\n\n'
         '/* ================= 顶部 ================= */')
    C = ('@media (max-height: 700px) {\n'
         '  .portal__main {\n'
         '    justify-content: flex-start;\n'
         '  }\n'
         '}\n'
         '</style>')

    anchors = [('A/模板-veil 之后', A), ('B/CSS-veil 规则之后', B), ('C/CSS-文件末尾', C)]
    bad = []
    for name, a in anchors:
        # 幂等：已打过补丁则直接退出
        n = norm.count(a)
        print('anchor %-22s hits=%d' % (name, n))
        if n != 1:
            bad.append(name)
    if bad:
        print('FATAL: 锚点未命中恰 1 次:', bad, '=> 未写盘')
        return 2

    # ---- 纯追加 ----
    norm = norm.replace(A, A + INS_TEMPLATE, 1)
    norm = norm.replace(B, INS_CSS_FX + '\n' + B, 1)
    norm = norm.replace(C, INS_CSS_REDUCED + '\n' + C, 1)

    # ---- 自检 ----
    checks = {
        '装饰层容器': '.portal__fx {' in norm,
        '云层 3 个 span': norm.count('portal__cloud portal__cloud--') == 3,
        '阳光层': '.portal__sun {' in norm,
        '湖面层': '.portal__shine {' in norm,
        'reduced-motion': 'prefers-reduced-motion: reduce' in norm,
        'keyframes 数=8': norm.count('@keyframes ') == 8,
        'target=_blank 未引入': 'target=' not in norm,
    }
    for k, v in checks.items():
        print('self-check %-16s %s' % (k, 'OK' if v else 'FAIL'))
    if not all(checks.values()):
        print('FATAL: 自检未通过 => 未写盘')
        return 2

    brace = norm.count('{') - norm.count('}')
    print('brace balance:', brace)
    if brace != 0:
        print('FATAL: 括号不配平 => 未写盘')
        return 2

    out = norm.replace('\n', eol) if eol == '\r\n' else norm
    assert out.encode('utf-8') != raw, 'no change?'
    with open(P, 'wb') as f:
        f.write(out.encode('utf-8'))
    print('written bytes:', os.path.getsize(P), '(+%d)' % (os.path.getsize(P) - len(raw)))
    print('OK: 补丁已一次性落盘')
    return 0


if __name__ == '__main__':
    sys.exit(main())
