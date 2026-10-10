# -*- coding: utf-8 -*-
"""
根因探针：为什么 _verify_login.py 的 E/F 阶段 "真实鼠标点击" 到达登录按钮 0 次。

三个待验证假设：
  H1 平滑滚动漂移 —— click_center 里 scrollIntoView({block:'center'}) 若命中
     html{scroll-behavior:smooth}，矩形是在"滚动进行中"量的，等坐标发出去时
     页面已滚走 => 点空。
  H2 长会话退化 —— 同一 CDP 会话导航次数变多后 Input.dispatchMouseEvent 失效。
  H3 纯脚手架问题 —— DOM 级 el.click() 能正常跑通 login()（HTTP 200 + 跳转），
     说明产品功能正常，仅鼠标注入失效。

输出同时落盘 _verify_out/probe_click.txt（不依赖管道回显）。
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

MW = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system\management-web'
sys.path.insert(0, MW)

spec = importlib.util.spec_from_file_location('va', os.path.join(MW, '_verify_anim.py'))
va = importlib.util.module_from_spec(spec)
spec.loader.exec_module(va)

BASE = va.BASE
OUT = os.path.join(va.ART, 'probe_click.txt')
LINES = []


def log(*a):
    s = ' '.join(str(x) for x in a)
    LINES.append(s)
    print(s, flush=True)


ROLES = [('admin', '/admin/login', 'admin', '/admin/dashboard'),
         ('doctor', '/doctor/login', 'doctor001', '/doctor/dashboard'),
         ('coach', '/coach/login', 'coach001', '/coach/dashboard')]
PW = '123456'


def launch():
    cdp = va.free_port()
    profile = tempfile.mkdtemp(prefix='hms-click-')
    chrome = subprocess.Popen([
        va.CHROME, '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
        '--disable-extensions', '--disable-background-networking', '--disable-sync', '--mute-audio',
        '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
        '--disable-backgrounding-occluded-windows', '--force-device-scale-factor=1',
        '--window-size=1366,768', '--user-data-dir=' + profile,
        '--remote-debugging-port=%d' % cdp, 'about:blank',
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    target, dl = None, time.time() + 45
    while time.time() < dl:
        try:
            with urllib.request.urlopen('http://127.0.0.1:%d/json/list' % cdp, timeout=2) as r:
                ts = json.loads(r.read().decode())
            pages = [t for t in ts if t.get('type') == 'page']
            if pages:
                target = pages[0]
                break
        except Exception:
            pass
        time.sleep(0.4)
    if not target:
        raise RuntimeError('CDP not ready')
    ws = va.WS(target['webSocketDebuggerUrl'])
    ws.call('Page.enable'); ws.call('Runtime.enable')
    ws.call('Log.enable'); ws.call('Network.enable')
    ws.call('Page.addScriptToEvaluateOnNewDocument', {'source': va.HOOK})
    ws.call('Emulation.setDeviceMetricsOverride',
            {'width': 1366, 'height': 768, 'deviceScaleFactor': 1, 'mobile': False})
    return chrome, ws, cdp


def click_nth(ws, sel, idx=0):
    """与 _verify_login.click_nth 完全一致（带 scrollIntoView 的真实鼠标点击）。"""
    rect = ws.evaluate(
        '(function(){var l=document.querySelectorAll(%s); var el=l[%d]; if(!el) return null;'
        'el.scrollIntoView({block:"center"}); var r=el.getBoundingClientRect();'
        'return {x:r.left+r.width/2, y:r.top+r.height/2, w:Math.round(r.width), h:Math.round(r.height)};})()'
        % (json.dumps(sel), idx))
    if not rect or rect['w'] <= 0 or rect['h'] <= 0:
        return None
    x, y = rect['x'], rect['y']
    ws.call('Input.dispatchMouseEvent', {'type': 'mouseMoved', 'x': x, 'y': y, 'button': 'none'})
    ws.call('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': x, 'y': y,
                                         'button': 'left', 'buttons': 1, 'clickCount': 1})
    ws.call('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': x, 'y': y,
                                         'button': 'left', 'buttons': 0, 'clickCount': 1})
    return rect


def wait_path(ws, want, timeout=20):
    dl = time.time() + timeout
    while time.time() < dl:
        try:
            if ws.evaluate('location.pathname') == want:
                time.sleep(0.6)
                return True
        except Exception:
            pass
        time.sleep(0.25)
    return False


def wait_form(ws, timeout=12):
    dl = time.time() + timeout
    last = None
    while time.time() < dl:
        last = ws.evaluate(
            '(function(){var l=document.querySelectorAll(".lp__form input"); if(l.length<2) return null;'
            'var r0=l[0].getBoundingClientRect(), r1=l[1].getBoundingClientRect();'
            'return {n:l.length, h0:Math.round(r0.height), h1:Math.round(r1.height)};})()')
        if last and last['h0'] >= 30 and last['h1'] >= 30:
            return last
        time.sleep(0.15)
    return last


def fill(ws, key, account):
    """真实聚焦 + insertText（与 _verify_login.type_text 同机制）。"""
    for idx, txt in ((0, account), (1, PW)):
        for _ in range(3):
            click_nth(ws, '.lp__form input', idx)
            ws.evaluate('(function(){var i=document.querySelectorAll(".lp__form input");'
                        'if(i[%d]) i[%d].focus();})()' % (idx, idx))
            ws.call('Input.insertText', {'text': txt})
            got = ws.evaluate('(function(){var i=document.querySelectorAll(".lp__form input");'
                              'return i[%d]?i[%d].value:null;})()' % (idx, idx))
            if got == txt:
                break
            time.sleep(0.3)
    return ws.evaluate('JSON.stringify(Array.prototype.map.call('
                       'document.querySelectorAll(".lp__form input"),function(e){return e.value}))')


def env(ws, tag):
    d = ws.evaluate('''JSON.stringify({
      focus: document.hasFocus(), vis: document.visibilityState,
      ae: document.activeElement ? (document.activeElement.tagName + '.' + (document.activeElement.className||'')) : null,
      iw: innerWidth, ih: innerHeight,
      sy: Math.round(scrollY), sh: document.documentElement.scrollHeight,
      ch: document.documentElement.clientHeight,
      sb: getComputedStyle(document.documentElement).scrollBehavior})''')
    log('  [%s] env=%s' % (tag, d))
    return d


def scroll_drift(ws):
    """H1：量 scrollIntoView 前后的按钮矩形与 scrollY，看是否在滚。"""
    r = ws.evaluate('''(function(){
      var el=document.querySelector('.lp__btn');
      var y0=Math.round(scrollY), t0=Math.round(el.getBoundingClientRect().top);
      el.scrollIntoView({block:'center'});
      var a=el.getBoundingClientRect();
      return JSON.stringify({y_before:y0, t_before:t0, y_now:Math.round(scrollY),
                             t_now:Math.round(a.top), h:Math.round(a.height)});})()''')
    time.sleep(0.5)
    r2 = ws.evaluate('''(function(){var el=document.querySelector('.lp__btn');
      var a=el.getBoundingClientRect();
      return JSON.stringify({y_500ms:Math.round(scrollY), t_500ms:Math.round(a.top)});})()''')
    log('  scrollIntoView 前=%s' % r)
    log('  scrollIntoView +500ms=%s' % r2)
    return json.loads(r), json.loads(r2)


def mouse_click(ws, sel='.lp__btn', force_frame=False):
    """复刻 click_center，但把每一步矩形/命中元素都打出来。

    force_frame=True：在按下前先 Page.captureScreenshot 强制产一帧，
    用于验证"合成器休眠导致 input 注入失效"这一假设。
    """
    info = json.loads(ws.evaluate('''(function(){
      var el=document.querySelector(%s);
      if(!el) return JSON.stringify({err:'no-el'});
      el.scrollIntoView({block:"center"});
      var r=el.getBoundingClientRect();
      var x=r.left+r.width/2, y=r.top+r.height/2;
      var hit=document.elementFromPoint(x,y);
      return JSON.stringify({x:Math.round(x), y:Math.round(y),
        w:Math.round(r.width), h:Math.round(r.height),
        hit: hit ? hit.tagName+'.'+hit.className.toString() : null,
        y_now: Math.round(scrollY)});})()''' % json.dumps(sel)))
    if info.get('err'):
        return None
    x, y = info['x'], info['y']
    if force_frame:
        try:
            ws.call('Page.captureScreenshot', {'format': 'png'})
        except Exception:
            pass
    ws.call('Input.dispatchMouseEvent', {'type': 'mouseMoved', 'x': x, 'y': y, 'button': 'none'})
    if force_frame:
        try:
            ws.call('Page.captureScreenshot', {'format': 'png'})
        except Exception:
            pass
    ws.call('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': x, 'y': y,
                                         'button': 'left', 'buttons': 1, 'clickCount': 1})
    ws.call('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': x, 'y': y,
                                         'button': 'left', 'buttons': 0, 'clickCount': 1})
    time.sleep(0.5)
    return info


def arm(ws):
    ws.evaluate("window.__hit=0;(function(){var b=document.querySelector('.lp__btn');"
                "if(b){b.addEventListener('click',function(){window.__hit=(window.__hit||0)+1},true);}})()")


def dom_click(ws):
    return ws.evaluate('(function(){var b=document.querySelector(".lp__btn");'
                       'if(!b) return "no-btn"; b.click(); return "clicked";})()')


def api_tail(ws, n=6):
    out = []
    for ev in ws.events[-400:]:
        if ev.get('method') == 'Network.responseReceived':
            r = ev['params'].get('response') or {}
            if '/api/' in r.get('url', ''):
                out.append((r['url'].split('/api/', 1)[1], r.get('status')))
    return out[-n:]


def probe_role(ws, key, path, account, home, tag):
    log('---- %s (%s) ----' % (tag, path))
    va.navigate(ws, BASE + path)
    wf = wait_form(ws)
    log('  wait_form=%s' % wf)
    log('  fill vals=%s' % fill(ws, key, account))
    env(ws, tag)
    scroll_drift(ws)

    # 1) 真实鼠标点击
    arm(ws)
    mc = mouse_click(ws)
    log('  mouse_click rect=%s -> __hit=%s' % (mc, ws.evaluate('window.__hit||0')))
    ok1 = wait_path(ws, home, 12)
    log('  mouse_click 结果: 跳转=%s path=%s api=%s' % (ok1, ws.evaluate('location.pathname'), api_tail(ws)))

    if ok1:
        return 'mouse'

    # 2) 强制产帧后再试一次（验证合成器休眠假设）
    arm(ws)
    mc = mouse_click(ws, force_frame=True)
    log('  2nd mouse_click(+force_frame) rect=%s -> __hit=%s' % (mc, ws.evaluate('window.__hit||0')))
    ok2 = wait_path(ws, home, 12)
    log('  2nd mouse_click 结果: 跳转=%s path=%s api=%s' % (ok2, ws.evaluate('location.pathname'), api_tail(ws)))
    if ok2:
        return 'mouse-frame'

    # 3) DOM 级 el.click()
    arm(ws)
    log('  dom_click=%s' % dom_click(ws))
    time.sleep(0.3)
    log('  dom_click -> __hit=%s' % ws.evaluate('window.__hit||0'))
    ok3 = wait_path(ws, home, 15)
    log('  dom_click 结果: 跳转=%s path=%s api=%s' % (ok3, ws.evaluate('location.pathname'), api_tail(ws)))
    if ok3:
        return 'dom'
    return 'none'


def main():
    os.makedirs(va.ART, exist_ok=True)
    dev, html, reused = va.start_dev_server()
    log('dev server reused=%s ok=%s' % (reused, 'id="app"' in html))
    chrome, ws, cdp = launch()
    try:
        # 阶段 1：干净会话（导航 1 次）
        log('===== 阶段 1：干净会话 =====')
        for key, path, account, home in ROLES:
            r = probe_role(ws, key, path, account, home, 'fresh-' + key)
            log('  => 结论: %s' % r)
            ws.evaluate('localStorage.clear()')

        # 阶段 2：先做 24 次导航，模拟 _verify_login 的长会话
        log('===== 阶段 2：24 次导航后的长会话 =====')
        for i in range(24):
            va.navigate(ws, BASE + ROLES[i % 3][1])
        log('  已完成 24 次导航，ws.events 累计 %d 条' % len(ws.events))
        for key, path, account, home in ROLES:
            r = probe_role(ws, key, path, account, home, 'soak-' + key)
            log('  => 结论: %s' % r)
            ws.evaluate('localStorage.clear()')
    finally:
        try:
            chrome.kill()
        except Exception:
            pass
        if dev is not None:
            try:
                dev.kill()
            except Exception:
                pass

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(LINES))
    print('WROTE ' + OUT, flush=True)


if __name__ == '__main__':
    main()
