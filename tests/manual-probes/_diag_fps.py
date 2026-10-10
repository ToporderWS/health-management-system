# -*- coding: utf-8 -*-
"""
对照实验：动画 ON / OFF / 静态页，在 **软件合成(--disable-gpu)** 与 **GPU 合成** 两种
渲染后端下的帧率与主线程成本，用于回答"普通笔记本 Chrome 是否流畅"。

用法：python _diag_fps.py nogpu|gpu
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

ALL_OFF = ('.portal__bg,.portal__bg-photo,.portal__bg::before,.portal__bg::after,'
           '.portal__cloud,.portal__sun,.portal__shine{animation:none !important}')
WINDOW = 8.0


def run(ws, label, css, url_extra=''):
    ws.evaluate("(function(){var o=document.getElementById('cfg'); if(o) o.remove();"
                "var s=document.createElement('style'); s.id='cfg'; s.textContent=%s;"
                "document.head.appendChild(s); return true;})()" % json.dumps(css))
    time.sleep(1.0)
    ws.evaluate('window.__frames=0; window.__lt=[]')
    m0 = {m['name']: m['value'] for m in ws.call('Performance.getMetrics')['result']['metrics']}
    t0 = time.time()
    while time.time() - t0 < WINDOW:
        ws.shot(None)
        time.sleep(1.0)
    el = time.time() - t0
    m1 = {m['name']: m['value'] for m in ws.call('Performance.getMetrics')['result']['metrics']}
    frames = ws.evaluate('window.__frames||0')
    lt = ws.evaluate('(window.__lt||[]).length')
    row = {'label': label, 'fps': round(frames / el, 1), 'frames': frames,
           'dStyle': int(m1.get('RecalcStyleCount', 0) - m0.get('RecalcStyleCount', 0)),
           'dLayout': int(m1.get('LayoutCount', 0) - m0.get('LayoutCount', 0)),
           'styleMs': round((m1.get('RecalcStyleDuration', 0) - m0.get('RecalcStyleDuration', 0)) * 1000, 1),
           'taskMs': round((m1.get('TaskDuration', 0) - m0.get('TaskDuration', 0)) * 1000, 1),
           'longtasks': lt}
    print('   %-30s fps=%-6s frames=%-5s dStyle=%-5s dLayout=%-3s styleMs=%-7s taskMs=%-7s lt=%s'
          % (row['label'], row['fps'], row['frames'], row['dStyle'], row['dLayout'],
             row['styleMs'], row['taskMs'], row['longtasks']), flush=True)
    return row


def main():
    mode = (sys.argv[1] if len(sys.argv) > 1 else 'nogpu').lower()
    extra = [] if mode == 'gpu' else ['--disable-gpu']
    print('### 渲染后端 = %s %s' % (mode, extra or '(默认 GPU)'), flush=True)

    dev, _ = start_dev_server()
    cdp = free_port()
    profile = tempfile.mkdtemp(prefix='hms-fps-')
    chrome = subprocess.Popen([
        CHROME, '--headless=new', '--no-first-run', '--no-default-browser-check',
        '--disable-extensions', '--disable-background-networking', '--disable-sync', '--mute-audio',
        '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
        '--disable-backgrounding-occluded-windows',
        '--window-size=1366,768', '--user-data-dir=' + profile,
        '--remote-debugging-port=%d' % cdp, 'about:blank'] + extra,
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

        rows = []
        navigate(ws, BASE + '/')
        # 用 WebGL/GPU 可用性做一次客观判定，避免把"其实没用上 GPU"当成 GPU 结果
        gpu = ws.evaluate("""(function(){
          try { var c=document.createElement('canvas');
            var gl=c.getContext('webgl2')||c.getContext('webgl'); if(!gl) return 'no-webgl';
            var d=gl.getExtension('WEBGL_debug_renderer_info');
            return d ? String(gl.getParameter(d.UNMASKED_RENDERER_WEBGL)) : 'webgl-ok(unknown)';
          } catch(e){ return 'err:'+e.message; }})()""")
        print('   [info] WebGL renderer = %s' % gpu, flush=True)

        rows.append(run(ws, 'A 首页 · 全部动画 ON', ''))
        rows.append(run(ws, 'B 首页 · 全部动画 OFF', ALL_OFF))
        navigate(ws, BASE + '/doctor/login')
        time.sleep(1.2)
        rows.append(run(ws, 'C 静态页 /doctor/login', ''))

        on = rows[0]
        print('\n结论[%s]：动画 ON fps=%s（同页 OFF fps=%s；静态页 fps=%s）；'
              'ON 时 dLayout=%s、style 占比=%.2f%%、主线程任务占比=%.2f%%、长任务=%s'
              % (mode, on['fps'], rows[1]['fps'], rows[2]['fps'], on['dLayout'],
                 on['styleMs'] / (WINDOW * 1000) * 100, on['taskMs'] / (WINDOW * 1000) * 100,
                 on['longtasks']), flush=True)
        with open(os.path.join(ART, 'diag_fps_%s.json' % mode), 'w', encoding='utf-8') as f:
            json.dump({'mode': mode, 'webgl': gpu, 'rows': rows}, f, ensure_ascii=False, indent=2)
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
