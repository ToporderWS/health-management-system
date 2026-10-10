# -*- coding: utf-8 -*-
"""生成四类默认头像（default_health / default_doctor / default_coach / default_admin）。
统一输出到 backend/static/upload/，数据库只保存文件名。

运行方式：python tools/gen_default_avatars.py
"""
import os

from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "backend", "static", "upload")
os.makedirs(OUT, exist_ok=True)

SPECS = [
    ("default_health.jpg", (46, 125, 50), (102, 187, 106), "健"),
    ("default_doctor.jpg", (0, 121, 107), (77, 182, 172), "医"),
    ("default_coach.jpg", (21, 101, 192), (66, 165, 245), "教"),
    ("default_admin.jpg", (26, 35, 126), (92, 107, 192), "管"),
]


def font(size):
    for path in (r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msyh.ttc",
                 r"C:\Windows\Fonts\simhei.ttf"):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def make(name, c1, c2, ch):
    size = 400
    img = Image.new("RGB", (size, size), c1)
    d = ImageDraw.Draw(img)
    # 对角渐变背景
    for y in range(size):
        r = int(c1[0] + (c2[0] - c1[0]) * y / size)
        g = int(c1[1] + (c2[1] - c1[1]) * y / size)
        b = int(c1[2] + (c2[2] - c1[2]) * y / size)
        d.line([(0, y), (size, y)], fill=(r, g, b))
    # 头像剪影：头部 + 肩部
    d.ellipse([140, 70, 260, 190], fill=(255, 255, 255))
    d.ellipse([90, 205, 310, 470], fill=(255, 255, 255))
    # 中心字符
    f = font(80)
    box = d.textbbox((0, 0), ch, font=f)
    w, h = box[2] - box[0], box[3] - box[1]
    d.text(((size - w) / 2 - box[0], (size - h) / 2 - box[1] - 6), ch, font=f, fill=c1)
    path = os.path.join(OUT, name)
    img.save(path, "JPEG", quality=90)
    print("OK", path, os.path.getsize(path), "bytes")


for spec in SPECS:
    make(*spec)
