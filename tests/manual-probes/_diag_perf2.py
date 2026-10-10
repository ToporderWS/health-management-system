# -*- coding: utf-8 -*-
"""
定位"每帧 1 次样式重算"来自哪一组动画（成对隔离，区分单层失效与"每帧 1 趟"模型）。
GPU 后端，8s 窗口。若某组关掉后 dStyle 塌到 0 => 该组存在未上合成层的动画。
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

BG = '.portal__bg{animation:none !important}'
MT = '.portal__bg::before,.portal__bg::after{animation:none !important}'
PSEUDO = '.portal__bg::before{animation:none !important}'
ALL = ('.portal__bg,.portal__bg-photo,.portal__bg::before,.portal__bg::after,'
       '.portal__cloud,.portal__sun,.portal__shine{animation:none !important}')
SKY = '.portal__cloud,.portal__sun{animation:none !important}'
SHINE = '.portal__shine{animation:none !important}'
NOBG = BG + MT          # 关掉 背景呼吸 + 山景  -> 只剩 云/阳光/湖面
NOCLOUD = SKY + SHINE   # 关掉 云/阳光/湖面      -> 只剩 背景呼吸 + 山景

CONFIGS = [
    ('A 全部 ON（基线）', ''),
    ('J 只留 云+阳光+湖面（关背景+山景）', NOBG),
    ('K 只留 背景+山景（关云/阳光/湖面）', NOCLOUD),
    ('L 只关 山景两层', MT),
    ('M 只关 背景呼吸', BG),
    ('N 只关 湖面微光', SHINE),
    ('H 全部关闭', ALL),
]
W = 8.0


def run(ws, label, css):
    ws.evaluate("(function(){var o=document.getElementById('cfg'); if(o) o.remove();"
                "var s=document.createElement('style'); s.id='cfg'; s.textContent=%s;"
                "document.head.appendChild(s); return true;})()" % json.dumps(css))
    time.sleep(0.9)
    ws.evaluate('window.__frames=0')
    m0 = {m['name']: m['value'] for m in ws.call('Performance.getMetrics')['result']['metrics']}
    t0 = time.time()
    while time.time() - t0 < W:
        ws.shot(None)
        time.sleep(1.0)
    el = time.time() - t0
    m1 = {m['name']: m['value'] for m in ws.call('Performance.getMetrics')['result']['metrics']}
    frames = ws.evaluate('window.__frames||0')
    d = {'label': label, 'fps': round(frames / el, 1), 'dStyle': int(m1.get('RecalcStyleCount', 0) - m0.get('RecalcStyleCount', 0)),
         'dLayout': int(m1.get('LayoutCount', 0) - m0.get('LayoutCount', 0)),
         'perFrame': round((m1.get('RecalcStyleCount', 0) - m0.get('RecalcStyleCount', 0)) / max(frames, 1), 2),
         'styleMs': round((m1.get('RecalcStyleDuration', 0) - m0.get('RecalcStyleDuration', 0)) * 1000, 1)}
    print('   %-34s fps=%-7s dStyle=%-6s perFrame=%-5s dLayout=%-3s styleMs=%s'
          % (d['label'], d['fps'], d['dStyle'], d['perFrame'], d['dLayout'], d['styleMs']), flush=True)
    return d


def main():
    dev, _ = start_dev_server()
    cdp = free_port()
    profile = tempfile.mkdtemp(prefix='hms-p2-')
    chrome = subprocess.Popen([
        CHROME, '--headless=new', '--no-first-run', '--no-default-browser-check',
        '--disable-extensions', '--disable-background-networking', '--disable-sync', '--mute-audio',
        '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
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
        ws.call('Page.enable'); ws.call('Runtime.enable'); ws.call('Performance.enable')
        ws.call('Page.addScriptToEvaluateOnNewDocument', {'source': HOOK})
        ws.call('Emulation.setDeviceMetricsOverride',
                {'width': 1366, 'height': 768, 'deviceScaleFactor': 1, 'mobile': False})
        navigate(ws, BASE + '/')
        rows = [run(ws, l, c) for l, c in CONFIGS]
        base = rows[0]['dStyle']
        print('\n=== 判读（perFrame = 每帧样式重算次数）===', flush=True)
        for r in rows:
            print('   %-34s perFrame=%s' % (r['label'], r['perFrame']), flush=True)
        z = [r['label'] for r in rows if r['dStyle'] == 0 or (base and r['dStyle'] <= base * 0.1)]
        print('关掉后每帧样式重算基本消失的组合: %s' % (z or '无（说明是"有动画即每帧一趟"的整体行为）'), flush=True)
        with open(os.path.join(ART, 'diag_perf2.json'), 'w', encoding='utf-8') as f:
            json.dump({'rows': rows}, f, ensure_ascii=False, indent=2)
        return 0
    finally:
        try:
            if ws:
                ws.sock.close()
        except Exception:
            pass
        for p in (chrome, dev):
            try:
                p.terminate(); p.wait(timeout=10)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass


if __name__ == '__main__':
    sys.exit(main())
