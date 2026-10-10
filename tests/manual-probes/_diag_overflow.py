# -*- coding: utf-8 -*-
"""
只读取证：长跑期间内容漂移的根因。

假设 H：背景层 scale(1->1.015) 的**变换溢出**被计入文档可滚动溢出区，
        使 scrollHeight 越过视口高度 -> 出现垂直滚动条 -> clientWidth 变窄 ->
        内容整体横移半个滚动条宽度；scale 回落时滚动条消失 -> 再移回来。
        这正好解释 3 个 FAIL（12 个元素同时漂移、CLS 0.0168）。

判据：动画 ON 时 scrollHeight 峰值 > 视口高度且 clientWidth 跳变；
      动画 OFF（同一次会话内注入 !important 覆盖）后两者都稳定。
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _verify_anim import (ART, BASE, CHROME, HOOK, WS, free_port, navigate,  # noqa: E402
                          start_dev_server)

import subprocess  # noqa: E402
import tempfile  # noqa: E402
import urllib.request  # noqa: E402

PROBE = """
(function(){
  var de=document.documentElement, p=document.querySelector('.portal'), bg=document.querySelector('.portal__bg');
  return {
    cw: de.clientWidth,
    ih: window.innerHeight,
    dsh: de.scrollHeight,
    bsh: document.body.scrollHeight,
    portalH: Math.round(p.getBoundingClientRect().height),
    portalSW: p.scrollHeight,
    over: de.scrollHeight - window.innerHeight,
    vscroll: de.scrollHeight > window.innerHeight,
    bgTf: getComputedStyle(bg).transform.slice(0, 26)
  };
})()
"""


def sample(ws, label, seconds, step=2.0):
    out = []
    dl = time.time() + seconds
    while time.time() < dl:
        ws.shot(None)
        out.append(ws.evaluate(PROBE))
        time.sleep(step)
    cws = sorted(set(o['cw'] for o in out))
    overs = [o['over'] for o in out]
    print('\n== %s ==' % label, flush=True)
    for o in out:
        print('   %s' % json.dumps(o), flush=True)
    print('   --> clientWidth 取值集合 = %s' % cws, flush=True)
    print('   --> scrollHeight-innerHeight: min=%s max=%s; 出现垂直滚动条=%s'
          % (min(overs), max(overs), any(o['vscroll'] for o in out)), flush=True)
    return cws, overs


def main():
    dev, _ = start_dev_server()
    cdp = free_port()
    profile = tempfile.mkdtemp(prefix='hms-diag-')
    chrome = subprocess.Popen([
        CHROME, '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
        '--disable-extensions', '--disable-background-networking', '--disable-sync', '--mute-audio',
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
        ws.call('Page.addScriptToEvaluateOnNewDocument', {'source': HOOK})
        ws.call('Emulation.setDeviceMetricsOverride',
                {'width': 1366, 'height': 768, 'deviceScaleFactor': 1, 'mobile': False})
        navigate(ws, BASE + '/')

        print('### A. 动画开启（现状）', flush=True)
        a_cw, a_over = sample(ws, 'A 动画 ON', 34, 2.0)

        ws.evaluate("""(function(){
          var s=document.createElement('style'); s.id='diag-off';
          s.textContent='.portal__bg,.portal__bg-photo,.portal__bg::before,.portal__bg::after,'
            +'.portal__cloud,.portal__sun,.portal__shine{animation:none !important}';
          document.head.appendChild(s); return true;})()""")
        time.sleep(1.0)
        print('\n### B. 已注入 animation:none 覆盖（排除 scale 溢出）', flush=True)
        b_cw, b_over = sample(ws, 'B 动画 OFF', 12, 2.0)

        ws.evaluate("document.getElementById('diag-off').remove()")
        time.sleep(1.0)
        print('\n### C. 移除覆盖后恢复', flush=True)
        c_cw, c_over = sample(ws, 'C 恢复动画', 10, 2.0)

        print('\n================ 结论 ================', flush=True)
        print('A 动画ON : clientWidth=%s  over:max=%s' % (a_cw, max(a_over)), flush=True)
        print('B 动画OFF: clientWidth=%s  over:max=%s' % (b_cw, max(b_over)), flush=True)
        print('C 恢复   : clientWidth=%s  over:max=%s' % (c_cw, max(c_over)), flush=True)
        verdict = (len(a_cw) > 1 and max(a_over) > 0 and len(b_cw) == 1 and max(b_over) <= 0)
        print('=> H 假设%s' % ('成立：背景 scale 的变换溢出导致滚动条闪烁 + 内容横移'
                              if verdict else '不成立，需另找根因'), flush=True)
        out = {'A': {'cw': a_cw, 'over': a_over}, 'B': {'cw': b_cw, 'over': b_over},
               'C': {'cw': c_cw, 'over': c_over}, 'verdict': bool(verdict)}
        with open(os.path.join(ART, 'diag_overflow.json'), 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
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
