# -*- coding: utf-8 -*-
"""取证：管理员「05 账号审核中心」的审核入口与二次确认框。

只读原则：本脚本会点开「通过」的二次确认弹框用于截图，但**绝不点击"确定"**，
不会向后端提交任何审核请求，数据库 audit_status 保持原样。
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

API = 'http://127.0.0.1:8080'
ADMIN = ('admin', '123456')
SIZE = (1440, 900)


def _req(url, body=None, token=None):
    hdr = {'Content-Type': 'application/json'}
    if token:
        hdr['Authorization'] = 'Bearer ' + token
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=hdr)
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            return r.status, json.loads(r.read().decode('utf-8'))
    except Exception as e:
        raw = getattr(e, 'read', lambda: b'')()
        try:
            return getattr(e, 'code', 'ERR'), json.loads(raw.decode('utf-8', 'replace'))
        except Exception:
            return getattr(e, 'code', 'ERR'), {'raw': raw.decode('utf-8', 'replace')}


def api_facts():
    """纯 API 取证：审核概览 + 待审核名单（不进浏览器，零副作用）。"""
    s, d = _req(API + '/api/admin/login', {'admin_name': ADMIN[0], 'password': ADMIN[1]})
    if s != 200:
        print('登录失败', s, d, flush=True)
        return None, None, None
    token = d['data']['token']
    info = d['data']['admin_info']

    _, ov = _req(API + '/api/admin/audit/overview', token=token)
    print('审核概览:', json.dumps(ov.get('data'), ensure_ascii=False), flush=True)

    _, dl = _req(API + '/api/admin/doctor/list?page=1&page_size=10&audit_status=0', token=token)
    rows = (dl.get('data') or {}).get('list') or []
    print('待审核医生 %d 条:' % len(rows), flush=True)
    for r in rows:
        print('   id=%-6s %-16s %-8s %s' % (r.get('id'), r.get('doctor_name'),
                                            r.get('real_name'), r.get('audit_status_text')), flush=True)

    _, cl = _req(API + '/api/admin/coach/list?page=1&page_size=10&audit_status=0', token=token)
    crows = (cl.get('data') or {}).get('list') or []
    print('待审核教练 %d 条:' % len(crows), flush=True)
    for r in crows:
        print('   id=%-6s %-16s %-8s %s' % (r.get('id'), r.get('coach_name'),
                                            r.get('real_name'), r.get('audit_status_text')), flush=True)
    return token, info, rows


def main():
    token, info, pending = api_facts()
    if not token:
        return 1

    dev, _, reused = start_dev_server()
    cdp = free_port()
    profile = tempfile.mkdtemp(prefix='hms-audit-')
    chrome = subprocess.Popen([
        CHROME, '--headless=new', '--no-first-run', '--no-default-browser-check',
        '--disable-extensions', '--disable-background-networking', '--disable-sync', '--mute-audio',
        '--window-size=%d,%d' % SIZE, '--user-data-dir=' + profile,
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
                {'width': SIZE[0], 'height': SIZE[1], 'deviceScaleFactor': 1, 'mobile': False})

        # 1) 先进同源页，写入管理员登录态（localStorage）
        navigate(ws, BASE + '/admin/login')
        time.sleep(1.0)
        ws.evaluate('localStorage.setItem("hms_admin_token",%s);'
                    'localStorage.setItem("hms_admin_info",%s);'
                    % (json.dumps(token), json.dumps(json.dumps(info, ensure_ascii=False))))

        # 2) 打开「05 账号审核中心」
        navigate(ws, BASE + '/admin/audit')
        time.sleep(1.8)
        cur = ws.evaluate('location.pathname')
        print('当前路由:', cur, flush=True)
        out1 = os.path.join(ART, 'admin-audit-list-%dx%d.png' % SIZE)
        ws.shot(out1)
        print('  截图 ->', os.path.basename(out1), flush=True)

        # 3) 记录操作列按钮的可点/禁用状态（证明"只有待审核可操作"）
        stat = ws.evaluate('''(function(){
          var rows=[].slice.call(document.querySelectorAll('.el-table__body tbody tr'));
          return JSON.stringify(rows.slice(0,12).map(function(tr){
            var st=(tr.querySelector('.el-tag')||{}).textContent||'';
            var btns=[].slice.call(tr.querySelectorAll('.el-button')).map(function(b){
              return b.textContent.trim()+'='+(b.classList.contains('is-disabled')?'禁用':'可点');
            });
            return st.trim()+' | '+btns.join(' ');
          }));})()''')
        print('行状态/按钮:', flush=True)
        for line in json.loads(stat):
            print('   ', line, flush=True)

        # 4) 点开「通过」的二次确认框，仅截图，绝不点确定
        hit = ws.evaluate('''(function(){
          var bs=[].slice.call(document.querySelectorAll('.el-table__body .el-button'))
                    .filter(function(b){return b.textContent.trim()==='通过'
                      && !b.classList.contains('is-disabled');});
          if(!bs.length) return 'NO_ENABLED_PASS_BUTTON';
          bs[0].click(); return 'OPENED';})()''')
        print('二次确认框:', hit, flush=True)
        if hit == 'OPENED':
            time.sleep(1.0)
            out2 = os.path.join(ART, 'admin-audit-confirm-%dx%d.png' % SIZE)
            ws.shot(out2)
            print('  截图 ->', os.path.basename(out2), flush=True)
            # 关闭弹框（点右上角 ×，绝不点确定/取消以外的危险项）
            ws.evaluate('(function(){var b=document.querySelector(".el-message-box__headerbtn");'
                        'if(b)b.click();return !!b;})()')
            time.sleep(0.5)
            left = ws.evaluate('document.querySelectorAll(".el-message-box").length')
            print('  弹框已关闭(剩余 .el-message-box=%s)' % left, flush=True)
            # 复核：数据库/接口侧待审核数量未变
            _, ov2 = _req(API + '/api/admin/audit/overview', token=token)
            print('  复核审核概览(应未变):', json.dumps(ov2.get('data'), ensure_ascii=False), flush=True)
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
