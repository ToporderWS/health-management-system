# -*- coding: utf-8 -*-
"""
量化"轻动态背景"的**可见强度**：同一页面、同一视口，按时间序列截图，
逐像素求 |Δ|（只统计纯背景区域），回答两件事：
  1) 太弱 -> 察觉不到（需求要求"观察几秒后察觉云在慢慢移动"）；
  2) 太强 -> 抢眼（需求要求"强度 2~3 分 / 不得明显抢眼"）。
判读参考：背景区 mean|Δ| 约 1~12 视为"克制但可察觉"；<1 基本无感；>20 偏抢眼。
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _verify_anim import ART, BASE, CHROME, HOOK, WS, free_port, navigate, start_dev_server  # noqa: E402
from PIL import Image, ImageChops, ImageStat  # noqa: E402

FRAMES = [0, 6, 12, 20]
BG_REGIONS = {
    'sky-upper':   (420, 8, 1000, 70),
    'sky-sunzone': (980, 20, 1290, 120),
    'left-blank':  (10, 300, 92, 430),
    'right-blank': (1280, 300, 1362, 430),
    'water-band':  (430, 575, 930, 625),
    'far-band':    (60, 645, 1230, 700),
}


def main():
    dev, _, reused = start_dev_server()
    print('dev server: %s' % ('复用已有实例' if reused else '本脚本自起'), flush=True)
    cdp = free_port()
    profile = tempfile.mkdtemp(prefix='hms-vis-')
    chrome = subprocess.Popen([
        CHROME, '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
        '--disable-extensions', '--disable-background-networking', '--disable-sync', '--mute-audio',
        '--window-size=1366,768', '--user-data-dir=' + profile,
        '--remote-debugging-port=%d' % cdp, 'about:blank'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ws = None
    try:
        target, dl = None, time.time() + 45
        while time.time() < dl:
            try:
                with urllib.request.urlopen('http://127.0.0.1:%d/json/list' % cdp, timeout=2) as r:
                    pages = [t for t in json.loads(r.read().decode()) if t.get('type') == 'page']
                if pages:
                    target = pages[0]
                    break
            except Exception:
                pass
            time.sleep(0.4)
        ws = WS(target['webSocketDebuggerUrl'])
        ws.call('Page.enable'); ws.call('Runtime.enable')
        ws.call('Page.addScriptToEvaluateOnNewDocument', {'source': HOOK})
        ws.call('Emulation.setDeviceMetricsOverride',
                {'width': 1366, 'height': 768, 'deviceScaleFactor': 1, 'mobile': False})
        navigate(ws, BASE + '/')

        paths, t0 = [], time.time()
        for sec in FRAMES:
            while time.time() - t0 < sec:
                ws.shot(None)
                time.sleep(1.0)
            p = os.path.join(ART, '_visframe_%02d.png' % sec)
            ws.shot(p)
            paths.append((sec, p))
            print('   captured +%2ds' % sec, flush=True)

        base = Image.open(paths[0][1]).convert('RGB')
        print('\n%-14s | %-11s | %-11s | %s' % ('region', 'mean|d| +6s', 'mean|d| +12s', 'peak(0..255)'))
        print('-' * 70)
        worst = 0.0
        for k, box in BG_REGIONS.items():
            means, peaks = [], []
            for _, p in paths[1:]:
                diff = ImageChops.difference(base.crop(box), Image.open(p).convert('RGB').crop(box)).convert('L')
                means.append(ImageStat.Stat(diff).mean[0])
                peaks.append(diff.getextrema()[1])
            worst = max(worst, max(means))
            print('%-14s | %11.2f | %11.2f | %d' % (k, means[0], means[1], max(peaks)))
        print('\n背景区最大 mean|Δ| = %.2f  =>  %s' % (
            worst,
            '基本无感（需加强）' if worst < 1 else
            ('克制但可察觉（推荐区间）' if worst <= 12 else '偏抢眼（需减弱）')), flush=True)
        print('（另附：+20s 帧已落盘 _visframe_20.png 供肉眼复核）', flush=True)
        return 0
    finally:
        try:
            if ws:
                ws.sock.close()
        except Exception:
            pass
        for p in (chrome, None if reused else dev):
            if p is None:
                continue
            try:
                p.terminate(); p.wait(timeout=10)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass


if __name__ == '__main__':
    sys.exit(main())
