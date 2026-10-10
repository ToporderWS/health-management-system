# -*- coding: utf-8 -*-
"""快速视觉取证：三个登录页在三档分辨率下截图，供人工/多模态复核布局。"""
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _verify_anim import ART, BASE, CHROME, HOOK, WS, free_port, navigate, start_dev_server  # noqa: E402

PAGES = [('admin', '/admin/login'), ('doctor', '/doctor/login'), ('coach', '/coach/login')]
SIZES = [(1920, 1080), (1440, 900), (1366, 768)]


def main():
    dev, _, reused = start_dev_server()
    print('dev server: %s' % ('复用已有实例' if reused else '本脚本自起'), flush=True)
    cdp = free_port()
    profile = tempfile.mkdtemp(prefix='hms-shot-')
    chrome = subprocess.Popen([
        CHROME, '--headless=new', '--no-first-run', '--no-default-browser-check',
        '--disable-extensions', '--disable-background-networking', '--disable-sync', '--mute-audio',
        '--window-size=1920,1080', '--user-data-dir=' + profile,
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

        for w, h in SIZES:
            ws.call('Emulation.setDeviceMetricsOverride',
                    {'width': w, 'height': h, 'deviceScaleFactor': 1, 'mobile': False})
            for name, path in PAGES:
                navigate(ws, BASE + path)
                time.sleep(0.9)
                out = os.path.join(ART, 'login-%s-%dx%d.png' % (name, w, h))
                ws.shot(out)
                print('  shot %s %dx%d -> %s' % (name, w, h, os.path.basename(out)), flush=True)
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
