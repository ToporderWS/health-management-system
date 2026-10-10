# -*- coding: utf-8 -*-
"""精确诊断：① 密码"眼睛"按钮的真实类名与位置；② 点击「登录」后页面的真实反应。"""
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _verify_anim import BASE, CHROME, HOOK, WS, free_port, navigate, start_dev_server  # noqa: E402

KEYS = ['hms_doctor_token', 'hms_doctor_info', 'hms_coach_token',
        'hms_coach_info', 'hms_admin_token', 'hms_admin_info']


def click_pt(ws, x, y):
    ws.call('Input.dispatchMouseEvent', {'type': 'mouseMoved', 'x': x, 'y': y, 'button': 'none'})
    ws.call('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1})
    ws.call('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1})


def rect(ws, sel, idx=0):
    return ws.evaluate(
        '(function(){var l=document.querySelectorAll(%s);var e=l[%d];if(!e)return null;'
        'var r=e.getBoundingClientRect();'
        'return {x:r.left+r.width/2,y:r.top+r.height/2,w:Math.round(r.width),h:Math.round(r.height),'
        'cls:e.className.toString(),tag:e.tagName};})()' % (json.dumps(sel), idx))


def fill(ws, idx, text):
    r = rect(ws, '.lp__form input', idx)
    if not r:
        print('  !! input %d not found' % idx)
        return
    click_pt(ws, r['x'], r['y'])
    ws.evaluate('document.querySelectorAll(".lp__form input")[%d].focus()' % idx)
    ws.call('Input.insertText', {'text': text})


def main():
    dev, _, reused = start_dev_server()
    cdp = free_port()
    profile = tempfile.mkdtemp(prefix='hms-p3-')
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

        navigate(ws, BASE + '/')
        ws.evaluate("[%s].forEach(function(k){localStorage.removeItem(k)})"
                    % ",".join(json.dumps(k) for k in KEYS))
        navigate(ws, BASE + '/coach/login')
        time.sleep(1.2)

        print('=== 输入前：suffix 内 el-icon 清单 ===')
        print(ws.evaluate(
            'JSON.stringify(Array.prototype.map.call('
            'document.querySelectorAll(".lp__form .el-input__suffix .el-icon"),'
            'function(e,i){return {i:i, cls:e.className.toString(),'
            'text:(e.innerText||"").slice(0,10), html:e.outerHTML.slice(0,120)}}),null,1)'))

        fill(ws, 0, 'coach001')
        fill(ws, 1, '123456')
        print('\n=== 输入后：值 ===')
        print(ws.evaluate('JSON.stringify(Array.prototype.map.call('
                          'document.querySelectorAll(".lp__form input"),function(e){return e.value}))'))

        print('\n=== 输入后：suffix 内 el-icon 清单（含父链） ===')
        print(ws.evaluate(
            'JSON.stringify(Array.prototype.map.call('
            'document.querySelectorAll(".lp__form .el-input__suffix .el-icon"),'
            'function(e,i){var p=e.parentElement;'
            'return {i:i, cls:e.className.toString(),'
            ' parentCls:p?p.className.toString():"", '
            ' itemIndex:Array.prototype.indexOf.call('
            '   document.querySelectorAll(".lp__form .el-form-item"),'
            '   e.closest(".el-form-item"))}}),null,1)'))

        print('\n=== 密码项 suffix 区域 HTML ===')
        print(ws.evaluate(
            '(function(){var h=document.querySelectorAll(".lp__form .el-form-item")[1];'
            'if(!h) return "NO ITEM2"; var s=h.querySelector(".el-input__suffix");'
            'return s? s.outerHTML : "NO SUFFIX";})()')[:900])

        # 真实点击"眼睛"（定位到密码项内的第一个 el-icon）
        eye = rect(ws, '.lp__form .el-form-item:nth-of-type(2) .el-input__suffix .el-icon', 0)
        print('\n=== 密码项眼睛 rect = %s ===' % json.dumps(eye, ensure_ascii=False))
        if eye:
            click_pt(ws, eye['x'], eye['y'])
            time.sleep(0.5)
            print('点击后密码 input type = %s' % ws.evaluate(
                'document.querySelectorAll(".lp__form input")[1].getAttribute("type")'))
            click_pt(ws, eye['x'], eye['y'])
            time.sleep(0.5)
            print('再点一次 type = %s' % ws.evaluate(
                'document.querySelectorAll(".lp__form input")[1].getAttribute("type")'))

        # 点击登录按钮，观察真实反应
        btn = rect(ws, '.lp__btn')
        print('\n=== 登录按钮 rect = %s ===' % json.dumps(btn, ensure_ascii=False))
        print('按钮中心 elementFromPoint = %s' % ws.evaluate(
            '(function(){var b=document.querySelector(".lp__btn");var r=b.getBoundingClientRect();'
            'var e=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);'
            'return e? e.tagName+"."+e.className.toString() : "null";})()'))
        print('点击前值 = %s' % ws.evaluate('JSON.stringify(Array.prototype.map.call('
                                          'document.querySelectorAll(".lp__form input"),function(e){return e.value}))'))
        ws.events = []
        click_pt(ws, btn['x'], btn['y'])
        for i in range(14):
            time.sleep(0.25)
            msgs = ws.evaluate('JSON.stringify(Array.prototype.map.call('
                               'document.querySelectorAll(".el-message"),function(e){return e.innerText.trim()}))')
            path = ws.evaluate('location.pathname')
            if msgs != '[]':
                print('  +%.2fs msg=%s path=%s' % (0.25 * (i + 1), msgs, path))
            if path != '/coach/login':
                print('  +%.2fs 已跳转 -> %s' % (0.25 * (i + 1), path))
                break
        print('最终 path = %s' % ws.evaluate('location.pathname'))
        print('最终 token = %s' % ws.evaluate('localStorage.getItem("hms_coach_token")'))
        print('最终 values = %s' % ws.evaluate('JSON.stringify(Array.prototype.map.call('
                                              'document.querySelectorAll(".lp__form input"),function(e){return e.value}))'))
        print('\n=== 本段 /api/ 响应 ===')
        for ev in ws.events:
            if ev.get('method') == 'Network.responseReceived':
                r = ev['params']['response']
                if '/api/' in r['url']:
                    print('  %s  HTTP %s' % (r['url'].split('/api/', 1)[1][:70], r.get('status')))
        print('\n=== 页面错误 ===')
        print(ws.evaluate('JSON.stringify(window.__errs||[])'))
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
