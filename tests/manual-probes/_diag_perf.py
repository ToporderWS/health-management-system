# -*- coding: utf-8 -*-
"""
只读取证：60s 长跑里 RecalcStyleCount +1341（≈1 次/帧）、LayoutCount +0 的成因定位。

方法：变量隔离 —— 在同一页面、同一会话内，用 !important 覆盖**逐个**关掉一层动画，
      固定 10s 窗口测 (ΔRecalcStyleCount, ΔLayoutCount, fps)，与"全部关闭"基线对照。
      若关掉某层后 Δ 塌到 ~0，该层即在主线程跑（未上合成层）。

判据：ΔRecalcStyleCount/10s ≈ 帧数 => 该层逐帧触发样式重算（主线程动画）。
      ΔLayoutCount 应恒为 0（无重排）。
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

CONFIGS = [
    ('A 全部动画 ON（现状）', ''),
    ('B 仅关 ① 云层漂移', '.portal__cloud{animation:none !important}'),
    ('C 仅关 ② 阳光呼吸', '.portal__sun{animation:none !important}'),
    ('D 仅关 ③ 湖面微光', '.portal__shine{animation:none !important}'),
    ('E 仅关 ⑤ 背景微呼吸', '.portal__bg{animation:none !important}'),
    ('F 仅关 ④ 远山景深', '.portal__bg::before{animation:none !important}'),
    ('G 仅关 ④ 近景景深', '.portal__bg::after{animation:none !important}'),
    ('H 全部关闭（基线）', ALL_OFF),
]

SET = """(function(){
  var old = document.getElementById('diag-cfg'); if (old) old.remove();
  if (!%s) return true;
  var s = document.createElement('style'); s.id = 'diag-cfg'; s.textContent = %s;
  document.head.appendChild(s); return true;})()"""

METRICS = "Performance.getMetrics"


def metrics(ws):
    return {m['name']: m['value'] for m in ws.call(METRICS)['result']['metrics']}


def run_cfg(ws, label, css, seconds=10.0):
    ws.evaluate(SET % (json.dumps(bool(css)), json.dumps(css)))
    time.sleep(1.2)
    ws.evaluate('window.__fps=0; window.__frames=0')
    m0 = metrics(ws)
    dl = time.time() + seconds
    while time.time() < dl:
        ws.shot(None)          # 强制产帧，保证动画时钟推进
        time.sleep(2.0)
    m1 = metrics(ws)
    fps = ws.evaluate('window.__fps||0')
    d = {
        'label': label,
        'dRecalcStyle': int(m1.get('RecalcStyleCount', 0) - m0.get('RecalcStyleCount', 0)),
        'dLayout': int(m1.get('LayoutCount', 0) - m0.get('LayoutCount', 0)),
        'dRecalcStyleDuration': round(m1.get('RecalcStyleDuration', 0) - m0.get('RecalcStyleDuration', 0), 4),
        'dLayoutDuration': round(m1.get('LayoutDuration', 0) - m0.get('LayoutDuration', 0), 4),
        'dTaskDuration': round(m1.get('TaskDuration', 0) - m0.get('TaskDuration', 0), 4),
        'dScriptDuration': round(m1.get('ScriptDuration', 0) - m0.get('ScriptDuration', 0), 4),
        'fps': fps,
    }
    print('   %-24s dStyle=%-6s dLayout=%-4s styleMs=%-8s taskMs=%-8s fps=%s'
          % (d['label'], d['dRecalcStyle'], d['dLayout'], d['dRecalcStyleDuration'],
             d['dTaskDuration'], d['fps']), flush=True)
    return d


def main():
    dev, _ = start_dev_server()
    cdp = free_port()
    profile = tempfile.mkdtemp(prefix='hms-perf-')
    chrome = subprocess.Popen([
        CHROME, '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
        '--disable-extensions', '--disable-background-networking', '--disable-sync', '--mute-audio',
        '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
        '--window-size=1366,768', '--user-data-dir=' + profile,
        '--remote-debugging-port=%d' % cdp, 'about:blank',
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
        ws.call('Performance.enable')
        ws.call('Page.addScriptToEvaluateOnNewDocument', {'source': HOOK})
        ws.call('Emulation.setDeviceMetricsOverride',
                {'width': 1366, 'height': 768, 'deviceScaleFactor': 1, 'mobile': False})
        navigate(ws, BASE + '/')

        print('### 逐层隔离（每档 10s 窗口，同页同会话）', flush=True)
        rows = []
        for label, css in CONFIGS:
            rows.append(run_cfg(ws, label, css))

        # 无动画静态页基线（验证 headless 的帧率天花板与副作用无关）
        navigate(ws, BASE + '/doctor/login')
        time.sleep(1.5)
        ws.evaluate('window.__fps=0; window.__frames=0')
        m0 = metrics(ws)
        dl = time.time() + 10
        while time.time() < dl:
            ws.shot(None); time.sleep(2.0)
        m1 = metrics(ws)
        base = {'label': 'I 静态页 /doctor/login（无动画）',
                'dRecalcStyle': int(m1.get('RecalcStyleCount', 0) - m0.get('RecalcStyleCount', 0)),
                'dLayout': int(m1.get('LayoutCount', 0) - m0.get('LayoutCount', 0)),
                'fps': ws.evaluate('window.__fps||0')}
        print('   %-24s dStyle=%-6s dLayout=%-4s fps=%s'
              % (base['label'], base['dRecalcStyle'], base['dLayout'], base['fps']), flush=True)

        on = rows[0]['dRecalcStyle']
        off = [r for r in rows if r['label'].startswith('H ')][0]['dRecalcStyle']
        culprits = [r['label'] for r in rows[1:7]
                    if on > 0 and r['dRecalcStyle'] <= max(3, on * 0.15)]
        print('\n================ 结论 ================', flush=True)
        print('全部 ON  dStyle/10s = %s' % on, flush=True)
        print('全部 OFF dStyle/10s = %s' % off, flush=True)
        print('静态页   dStyle/10s = %s  fps=%s（headless+软件渲染的帧率天花板参考值）'
              % (base['dRecalcStyle'], base['fps']), flush=True)
        print('单独关闭后 dStyle 塌到接近 0 的层（= 主线程逐帧样式重算的元凶）: %s' % (culprits or '无'), flush=True)
        with open(os.path.join(ART, 'diag_perf.json'), 'w', encoding='utf-8') as f:
            json.dump({'rows': rows, 'baseline': base, 'culprits': culprits}, f,
                      ensure_ascii=False, indent=2)
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
