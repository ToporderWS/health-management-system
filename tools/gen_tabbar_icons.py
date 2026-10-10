# -*- coding: utf-8 -*-
"""生成小程序 TabBar 图标（PNG，81x81，未选中灰 / 选中绿色）。

运行方式：python tools/gen_tabbar_icons.py
输出目录：miniapp/static/tabbar/
"""
import os

from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "miniapp", "static", "tabbar")
os.makedirs(OUT, exist_ok=True)

GRAY = (154, 168, 181, 255)
GREEN = (46, 125, 50, 255)
SIZE = 81
W = 5


def new_canvas():
    return Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))


def draw_home(d, c):
    d.line([(40, 12), (13, 38), (13, 68), (67, 68), (67, 38), (40, 12)], fill=c, width=W, joint="curve")
    d.line([(32, 68), (32, 50), (48, 50), (48, 68)], fill=c, width=W)


def draw_entry(d, c):
    d.rounded_rectangle([(13, 13), (68, 68)], radius=13, outline=c, width=W)
    d.line([(26, 40), (55, 40)], fill=c, width=W)
    d.line([(40, 26), (40, 55)], fill=c, width=W)


def draw_report(d, c):
    d.line([(12, 69), (69, 69)], fill=c, width=W)
    d.rectangle([(19, 48), (28, 69)], fill=c)
    d.rectangle([(36, 34), (45, 69)], fill=c)
    d.rectangle([(53, 20), (62, 69)], fill=c)


def draw_profile(d, c):
    d.ellipse([(29, 12), (52, 35)], outline=c, width=W)
    d.arc([(16, 38), (65, 87)], start=180, end=360, fill=c, width=W)


ICONS = {
    "home": draw_home,
    "entry": draw_entry,
    "report": draw_report,
    "profile": draw_profile,
}


def build():
    created = []
    for name, painter in ICONS.items():
        for suffix, color in (("", GRAY), ("-active", GREEN)):
            img = new_canvas()
            painter(ImageDraw.Draw(img), color)
            path = os.path.join(OUT, "%s%s.png" % (name, suffix))
            img.save(path)
            created.append(os.path.basename(path))
    return created


if __name__ == "__main__":
    files = build()
    print("生成图标 %d 个: %s" % (len(files), ", ".join(files)))
    for f in files:
        p = os.path.join(OUT, f)
        print("  %s  %d bytes" % (f, os.path.getsize(p)))
