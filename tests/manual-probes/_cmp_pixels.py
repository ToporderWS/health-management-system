# -*- coding: utf-8 -*-
"""分区像素量化：对比"加动效前"与"当前"两张 1366x768 截图，判断装饰层把底图洗白了多少。"""
from PIL import Image, ImageStat

D = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system\management-web\_verify_out'
OLD = D + r'\identity-select-1366x768.png'       # 动效前（上一轮生产产物验证）
NEW = D + r'\identity-select-anim-1366x768.png'  # 当前（含轻动态装饰层）

REGIONS = {
    'sky-upper   (y10-60)':    (420, 10, 1000, 60),
    'sky-sun     (y20-90)':    (1000, 20, 1290, 90),
    'band-top    (y300-345)':  (430, 300, 930, 345),
    'blank-left  (y300-420)':  (20, 300, 90, 420),
    'blank-right (y300-420)':  (1290, 300, 1360, 420),
    'water       (y580-620)':  (430, 580, 930, 620),
    'far-band    (y650-690)':  (100, 650, 1200, 690),
    'forest      (y700-755)':  (100, 700, 1200, 755),
}


def stat(img, box):
    r, g, b = ImageStat.Stat(img.crop(box)).mean
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    mx, mn = max(r, g, b), min(r, g, b)
    sat = 0.0 if mx == 0 else (mx - mn) / mx
    return r, g, b, lum, sat


def fmt(t):
    return '%3.0f,%3.0f,%3.0f  lum=%5.1f  sat=%.3f' % (t[0], t[1], t[2], t[3], t[4])


o = Image.open(OLD).convert('RGB')
n = Image.open(NEW).convert('RGB')
print('before size %s   after size %s' % (o.size, n.size))
print('%-24s | %-34s | %-34s | %s' % ('region', 'BEFORE', 'AFTER', 'dLum / dSat'))
print('-' * 118)
for k, box in REGIONS.items():
    a, b = stat(o, box), stat(n, box)
    print('%-24s | %-34s | %-34s | %+6.1f / %+.3f' % (k, fmt(a), fmt(b), b[3] - a[3], b[4] - a[4]))
