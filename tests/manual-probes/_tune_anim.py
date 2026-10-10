# -*- coding: utf-8 -*-
"""
调低轻动态装饰层强度（视觉纠偏）。

原因：1366x768 实拍显示，云/阳光/湖面三层叠加的等效白度太高
      （云层峰值 ≈0.5x0.98=0.49、阳光核心 ≈0.72x0.62=0.45），
      把原有蓝天/山体/湖面/森林的观感糊掉，违反"云层不得明显抢眼、强度 2~3 分"。
做法：只下调 opacity 与渐变 alpha，不动任何几何、时长、关键帧结构、层级与布局。
      目标等效白度：云 ≈0.22、阳光核心 ≈0.14、湖面 ≈0.075（均约为原值 1/2~1/3）。
"""
import os
import sys

P = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system\management-web\src\views\portal\IdentitySelect.vue'

PATCHES = [
    # ---- 云层 1 ----
    ("""  top: 4%;
  height: 19%;
  opacity: 0.5;
  background-size: 26% 100%;
  background-image:
    radial-gradient(closest-side at 16% 64%, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 33% 45%, rgba(255, 255, 255, 0.98), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 50% 62%, rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 70% 74%, rgba(255, 255, 255, 0.66), rgba(255, 255, 255, 0) 100%);""",
     """  top: 4%;
  height: 19%;
  opacity: 0.3;
  background-size: 26% 100%;
  background-image:
    radial-gradient(closest-side at 16% 64%, rgba(255, 255, 255, 0.7), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 33% 45%, rgba(255, 255, 255, 0.76), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 50% 62%, rgba(255, 255, 255, 0.62), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 70% 74%, rgba(255, 255, 255, 0.44), rgba(255, 255, 255, 0) 100%);"""),

    # ---- 云层 2 ----
    ("""  top: 15%;
  height: 16%;
  opacity: 0.34;
  background-size: 34% 100%;
  background-image:
    radial-gradient(closest-side at 22% 58%, rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 45% 40%, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 68% 66%, rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0) 100%);""",
     """  top: 15%;
  height: 16%;
  opacity: 0.2;
  background-size: 34% 100%;
  background-image:
    radial-gradient(closest-side at 22% 58%, rgba(255, 255, 255, 0.6), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 45% 40%, rgba(255, 255, 255, 0.66), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 68% 66%, rgba(255, 255, 255, 0.5), rgba(255, 255, 255, 0) 100%);"""),

    # ---- 云层 3 ----
    ("""  top: 26%;
  height: 13%;
  opacity: 0.26;
  background-size: 20.5% 100%;
  background-image:
    radial-gradient(closest-side at 30% 52%, rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 62% 68%, rgba(255, 255, 255, 0.76), rgba(255, 255, 255, 0) 100%);""",
     """  top: 26%;
  height: 13%;
  opacity: 0.15;
  background-size: 20.5% 100%;
  background-image:
    radial-gradient(closest-side at 30% 52%, rgba(255, 255, 255, 0.58), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 62% 68%, rgba(255, 255, 255, 0.44), rgba(255, 255, 255, 0) 100%);"""),

    # ---- 阳光呼吸 ----
    ("""  background: radial-gradient(
    closest-side at 64% 20%,
    rgba(255, 251, 228, 0.72) 0%,
    rgba(255, 249, 216, 0.38) 40%,
    rgba(255, 247, 212, 0) 76%
  );""",
     """  background: radial-gradient(
    closest-side at 64% 20%,
    rgba(255, 251, 228, 0.4) 0%,
    rgba(255, 249, 216, 0.19) 40%,
    rgba(255, 247, 212, 0) 76%
  );"""),

    ("""@keyframes portal-sun-breathe {
  0%, 100% { transform: scale(1); opacity: 0.62; }
  50% { transform: scale(1.03); opacity: 0.84; }
}""",
     """@keyframes portal-sun-breathe {
  0%, 100% { transform: scale(1); opacity: 0.34; }
  50% { transform: scale(1.03); opacity: 0.5; }
}"""),

    # ---- 湖面微光 ----
    ("""  opacity: 0.38;
  background-repeat: repeat-x;
  background-size: 22% 100%;
  background-image:
    radial-gradient(closest-side at 24% 56%, rgba(255, 255, 255, 0.52), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 58% 42%, rgba(255, 255, 255, 0.4), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 86% 64%, rgba(255, 254, 244, 0.32), rgba(255, 254, 244, 0) 100%);""",
     """  opacity: 0.22;
  background-repeat: repeat-x;
  background-size: 22% 100%;
  background-image:
    radial-gradient(closest-side at 24% 56%, rgba(255, 255, 255, 0.34), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 58% 42%, rgba(255, 255, 255, 0.26), rgba(255, 255, 255, 0) 100%),
    radial-gradient(closest-side at 86% 64%, rgba(255, 254, 244, 0.2), rgba(255, 254, 244, 0) 100%);"""),
]


def main():
    raw = open(P, 'rb').read()
    src = raw.decode('utf-8')
    if src.count('\r\n') not in (0, src.count('\n')):
        print('FATAL: 行尾混合')
        return 2
    norm = src.replace('\r\n', '\n')
    for i, (old, new) in enumerate(PATCHES, 1):
        n = norm.count(old)
        print('patch %d hits=%d' % (i, n))
        if n != 1:
            print('FATAL: patch %d 命中 %d 次 => 未写盘' % (i, n))
            return 2
        norm = norm.replace(old, new, 1)

    checks = {
        '几何/时长未变（58s）': norm.count('portal-cloud-drift-a 58s') == 1,
        '几何/时长未变（76s）': norm.count('portal-cloud-drift-b 76s') == 1,
        '几何/时长未变（67s）': norm.count('portal-cloud-drift-c 67s') == 1,
        '几何/时长未变（11s）': norm.count('portal-sun-breathe 11s') == 1,
        '几何/时长未变（23s）': norm.count('portal-shine-flow 23s') == 1,
        'keyframes 数=8': norm.count('@keyframes ') == 8,
        '动画声明数=9': norm.count('\n  animation: ') == 9,
        '括号配平': norm.count('{') == norm.count('}'),
        '等高云层几何未动（19%/16%/13%）':
            all(x in norm for x in ('height: 19%;', 'height: 16%;', 'height: 13%;')),
        '平铺周期未动（26%/34%/20.5%/22%）':
            all(x in norm for x in ('background-size: 26% 100%;', 'background-size: 34% 100%;',
                                    'background-size: 20.5% 100%;', 'background-size: 22% 100%;')),
    }
    for k, v in checks.items():
        print('self-check %-30s %s' % (k, 'OK' if v else 'FAIL'))
    if not all(checks.values()):
        print('FATAL: 自检未通过 => 未写盘')
        return 2
    with open(P, 'wb') as f:
        f.write(norm.encode('utf-8'))
    print('OK: 强度下调已落盘，字节 %d -> %d' % (len(raw), os.path.getsize(P)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
