# -*- coding: utf-8 -*-
"""定位并裁掉生成模型在右下角打的「AI生成」水印，然后转成 webp 落地。

用法：
  python _prep_illustrations.py probe   # 输出底部区域放大预览，人工确认水印边界
  python _prep_illustrations.py build   # 按确认的裁剪行裁切 + 转 webp
"""
import os
import sys

from PIL import Image

DIR = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system\management-web\src\assets\images\login'
SRC = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system\management-web\_verify_out\illustration-raw'
PET = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system\management-web\_verify_out'

# (源文件, 目标文件名)
JOBS = [
    ('Wide_horizontal_semi_flat_vect_2026-10-01T07-38-27.png', 'admin-login-illustration.webp'),
    ('Wide_horizontal_semi_flat_vect_2026-10-01T07-31-01.png', 'doctor-login-illustration.webp'),
    ('Wide_horizontal_semi_flat_vect_2026-10-01T07-36-43.png', 'coach-login-illustration.webp'),
]

# 裁剪后保留的高度（像素）：水印上沿实测 y≈969，保留 950 可完整去除并留 19px 余量
KEEP_H = 950


def probe():
    os.makedirs(PET, exist_ok=True)
    for src, _dst in JOBS:
        im = Image.open(os.path.join(SRC, src)).convert('RGB')
        w, h = im.size
        # 数值检测：右下角区域里"低饱和 + 偏灰/偏暗"的文字像素，取其最小 y 作为水印上沿
        px = im.load()
        x0, y0 = int(w * 0.72), int(h * 0.90)
        rows = []
        for y in range(y0, h):
            cnt = 0
            for x in range(x0, w, 2):
                r, g, b = px[x, y]
                if max(r, g, b) - min(r, g, b) < 14 and (r + g + b) / 3 < 205:
                    cnt += 1
            if cnt >= 3:
                rows.append(y)
        top = min(rows) if rows else None
        print('%-46s %sx%s  水印疑云上沿 y = %s  (扫描区 y>=%d, x>=%d)' % (
            os.path.basename(src)[:44], w, h, top, y0, x0))
        band = im.crop((0, h - 140, w, h))
        band = band.resize((band.width * 2, band.height * 2), Image.LANCZOS)
        out = os.path.join(PET, '_wm_%s.png' % os.path.basename(src)[-12:-4])
        band.save(out)
        print('     bottom-band(2x) -> %s' % out)


def build():
    for src, dst in JOBS:
        p = os.path.join(SRC, src)
        im = Image.open(p).convert('RGB')
        w, h = im.size
        cut = im.crop((0, 0, w, min(KEEP_H, h)))
        out = os.path.join(DIR, dst)
        cut.save(out, 'WEBP', quality=90, method=6)
        print('%-34s %sx%s -> %s  %sx%s  %d B' % (
            src[:32], w, h, dst, cut.width, cut.height, os.path.getsize(out)))


if __name__ == '__main__':
    {'probe': probe, 'build': build}[sys.argv[1]]()
