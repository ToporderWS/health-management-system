# -*- coding: utf-8 -*-
"""定位验收失败根因：密码眼睛按钮的真实 DOM 类名 / 表单结构 / 资源 404 来源 / 焦点状态。"""
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _verify_anim import BASE, CHROME, HOOK, WS, free_port, navigate, start_dev_server  # noqa: E402


def main():
    dev, _, reused = start_dev_server()
    cdp = free_port()
    profile = tempfile.mkdtemp(prefix='hms-probe-')
    chrome = subprocess.Popen([
        CHROME, '--headless=new', '--no-first-run', '--no-default-browser-check',
        '--disable-extensions', '--disable-background-networking', '--disable-sync', '--mute-audio',
        '--window-size=1440,900', '--user-data-dir=' + profile,
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
        ws.call('Page.enable'); ws.call('Runtime.enable'); ws.call('Network.enable')
        ws.call('Page.addScriptToEvaluateOnNewDocument', {'source': HOOK})
        ws.call('Emulation.setDeviceMetricsOverride',
                {'width': 1440, 'height': 900, 'deviceScaleFactor': 1, 'mobile': False})
        navigate(ws, BASE + '/coach/login')

        print('=== 密码项 outerHTML ===')
        print(ws.evaluate('(function(){var i=document.querySelectorAll(".lp__form .el-form-item");'
                          'return i.length>1 ? i[1].outerHTML : "NO ITEM 2";})()')[:1800])

        print('\n=== .lp__form 下出现的全部 class（去重） ===')
        print(ws.evaluate('(function(){var s=new Set();'
                          'document.querySelectorAll(".lp__form *").forEach(function(e){'
                          'if(e.classList) e.classList.forEach(function(c){s.add(c)})});'
                          'return Array.from(s).sort().join(", ")})()'))

        print('\n=== 常见眼睛按钮选择器命中数 ===')
        for sel in ['.el-input__password', '.el-input__suffix', '.el-input__suffix .el-icon',
                    '.el-input__suffix-inner .el-icon', '.lp__form input']:
            print('  %-40s -> %s' % (sel, ws.evaluate(
                'document.querySelectorAll(%s).length' % json.dumps(sel))))

        print('\n=== 资源请求（非 200） ===')
        ws.events = []
        navigate(ws, BASE + '/admin/login')
        time.sleep(1.2)
        seen = {}
        for ev in ws.events:
            if ev.get('method') == 'Network.responseReceived':
                r = ev['params']['response']
                if r.get('status', 0) != 200:
                    seen[r['url']] = r['status']
        print(json.dumps(seen, ensure_ascii=False, indent=1) or '{}')
        print('\n=== performance 资源里含 favicon 的条目 ===')
        print(ws.evaluate("JSON.stringify(performance.getEntriesByType('resource')"
                          ".map(function(e){return e.name}).filter(function(n){return /favicon|\.ico/.test(n)}))"))
        print('\n=== document 里的 favicon link ===')
        print(ws.evaluate("JSON.stringify(Array.prototype.map.call("
                          "document.querySelectorAll('link[rel*=icon]'),function(e){return e.getAttribute('href')}))"))
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
