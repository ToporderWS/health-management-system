# -*- coding: utf-8 -*-
"""
IdentitySelect.vue 端到端验证（真实 Chrome + CDP，仅用 Python 标准库）。

验证项：
  1. 身份选择首页可正常打开（关键文案齐全、卡片结构正确）
  2. 三个身份按钮真实路由跳转（医生/教练/管理员登录页）
  3. 浏览器 Console 无红色错误 / 无未捕获异常（双通道取证）
  4. 1366x768 / 1440x900 / 1920x1080 三档无横向滚动
  5. 1366x768 下三张身份卡片完整可见且尺寸统一
  6. 截图落盘（视觉取证）

脚手架注意（Windows）：
  Python mimetypes 在 Windows 上会把 .js 判成 text/plain，导致 <script type=module>
  因 MIME 校验被 Chrome 拒绝执行（页面白屏）。这是**测试装置缺陷、非产品缺陷**，
  通过强制 extensions_map 修正。
"""
import base64
import http.server
import json
import os
import re
import socket
import socketserver
import struct
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

DIST = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system\management-web\dist'
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
ARTIFACT_DIR = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system\management-web\_verify_out'

RESULTS = []


def case(name, ok, detail=''):
    RESULTS.append((name, bool(ok), detail))
    print(('PASS  ' if ok else 'FAIL  ') + name + (('  |  ' + str(detail)) if detail else ''), flush=True)


# ---------------------------------------------------------------- 静态服务（MIME 修正）
class SpaHandler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        '.html': 'text/html; charset=utf-8',
        '.js': 'text/javascript; charset=utf-8',
        '.mjs': 'text/javascript; charset=utf-8',
        '.css': 'text/css; charset=utf-8',
        '.json': 'application/json; charset=utf-8',
        '.svg': 'image/svg+xml',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.webp': 'image/webp',
        '.ico': 'image/x-icon',
        '.woff': 'font/woff',
        '.woff2': 'font/woff2',
        '.ttf': 'font/ttf',
        '.map': 'application/json; charset=utf-8',
    }

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=DIST, **kw)

    def do_GET(self):
        path = self.translate_path(self.path)
        if not os.path.exists(path) or os.path.isdir(path):
            self.path = '/index.html'   # SPA fallback（createWebHistory 需要）
        return super().do_GET()

    def handle_one_request(self):
        # Chrome 关闭连接会造成 ConnectionReset，属正常收尾，不打印回溯
        try:
            super().handle_one_request()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, OSError):
            self.close_connection = True

    def log_message(self, *a):
        pass


class QuietServer(socketserver.ThreadingTCPServer):
    """安静线程服务：忽略客户端中断造成的回溯。"""

    daemon_threads = True
    allow_reuse_address = True

    def handle_error(self, request, client_address):
        pass


def free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    p = s.getsockname()[1]
    s.close()
    return p


# ---------------------------------------------------------------- 极简 WebSocket 客户端
class WS:
    def __init__(self, url):
        rest = url[5:]
        hostport, _, path = rest.partition('/')
        host, _, port = hostport.partition(':')
        self.sock = socket.create_connection((host, int(port)), timeout=60)
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall((
            'GET /%s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n'
            'Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n' % (path, hostport, key)
        ).encode())
        buf = b''
        while b'\r\n\r\n' not in buf:
            c = self.sock.recv(4096)
            if not c:
                raise RuntimeError('handshake closed')
            buf += c
        if b'101' not in buf.split(b'\r\n')[0]:
            raise RuntimeError('handshake failed')
        self.buf = buf.split(b'\r\n\r\n', 1)[1]
        self.next_id = 1
        self.pending = {}
        self.events = []

    def _exact(self, n):
        while len(self.buf) < n:
            c = self.sock.recv(65536)
            if not c:
                raise RuntimeError('socket closed')
            self.buf += c
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def _send(self, payload, opcode=1):
        data = payload.encode()
        h = bytes([0x80 | opcode])
        n = len(data)
        if n < 126:
            h += bytes([0x80 | n])
        elif n < 65536:
            h += bytes([0x80 | 126]) + struct.pack('>H', n)
        else:
            h += bytes([0x80 | 127]) + struct.pack('>Q', n)
        m = os.urandom(4)
        self.sock.sendall(h + m + bytes(b ^ m[i % 4] for i, b in enumerate(data)))

    def _read_message(self):
        chunks = []
        while True:
            b1, b2 = self._exact(2)
            fin, op = b1 & 0x80, b1 & 0x0F
            ln = b2 & 0x7F
            if ln == 126:
                ln = struct.unpack('>H', self._exact(2))[0]
            elif ln == 127:
                ln = struct.unpack('>Q', self._exact(8))[0]
            data = self._exact(ln)
            if op == 0x9:
                self._send(data.decode('latin1'), opcode=0xA)
                continue
            if op == 0xA:
                continue
            if op == 0x8:
                raise RuntimeError('server closed ws')
            chunks.append(data)
            if fin:
                return b''.join(chunks).decode('utf-8', 'replace')

    def call(self, method, params=None, timeout=40):
        cid = self.next_id
        self.next_id += 1
        self._send(json.dumps({'id': cid, 'method': method, 'params': params or {}}))
        dl = time.time() + timeout
        while True:
            if cid in self.pending:
                return self.pending.pop(cid)
            if time.time() > dl:
                raise TimeoutError('timeout: ' + method)
            m = json.loads(self._read_message())
            if 'id' in m:
                if m['id'] == cid:
                    return m
                self.pending[m['id']] = m
            else:
                self.events.append(m)

    def evaluate(self, expr, timeout=40):
        r = self.call('Runtime.evaluate',
                      {'expression': expr, 'returnByValue': True, 'awaitPromise': True}, timeout)
        res = r.get('result', {})
        if res.get('exceptionDetails'):
            raise RuntimeError('JS exception: ' + json.dumps(res['exceptionDetails'], ensure_ascii=False)[:400])
        return res.get('result', {}).get('value')


# 在 document-start 注入错误收集钩子（每个新文档都执行）
ERROR_HOOK = r"""
(function(){
  if (window.__errsInstalled) return;
  window.__errsInstalled = true;
  window.__errs = [];
  window.addEventListener('error', function(e){
    window.__errs.push('error: ' + (e.message || '') + ' @' + (e.filename||'') + ':' + (e.lineno||0));
  }, true);
  window.addEventListener('unhandledrejection', function(e){
    var r = e.reason;
    var s = '';
    try { s = (r && r.stack) ? r.stack : JSON.stringify(r); } catch(_) { s = String(r); }
    window.__errs.push('unhandledrejection: ' + String(r && r.message || s).slice(0,400));
  });
  var ce = console.error.bind(console);
  console.error = function(){
    var parts = [];
    for (var i=0;i<arguments.length;i++){
      var a = arguments[i];
      try { parts.push(typeof a === 'string' ? a : (a && a.message ? a.message : JSON.stringify(a))); }
      catch(_) { parts.push(String(a)); }
    }
    window.__errs.push('console.error: ' + parts.join(' ').slice(0,400));
    return ce.apply(console, arguments);
  };
})();
"""


def wait_url_ready(ws, prefix, timeout=40):
    """等待落到目标 URL 且文档就绪（避免 readyState 竞态读到上一个文档）。"""
    dl = time.time() + timeout
    ok = False
    while time.time() < dl:
        try:
            href = ws.evaluate('location.href')
            st = ws.evaluate('document.readyState')
        except Exception:
            href, st = None, None
        if href and href.startswith(prefix) and st == 'complete':
            ok = True
            break
        time.sleep(0.2)
    time.sleep(1.1)   # 等 Vue 挂载 / 布局与字体稳定
    return ok


def navigate(ws, url):
    ws.call('Page.navigate', {'url': url})
    return wait_url_ready(ws, url)


def drain_errors(ws):
    errs = []
    for ev in ws.events:
        m = ev.get('method')
        p = ev.get('params') or {}
        if m == 'Runtime.consoleAPICalled' and p.get('type') == 'error':
            parts = []
            for a in p.get('args', []):
                if 'value' in a:
                    parts.append(str(a['value']))
                elif a.get('description'):
                    parts.append(str(a['description']))
            errs.append('console.error: ' + ' '.join(parts)[:400])
        elif m == 'Runtime.exceptionThrown':
            d = p.get('exceptionDetails', {})
            ex = d.get('exception', {}) or {}
            val = ex.get('value')
            extra = json.dumps(val, ensure_ascii=False) if isinstance(val, dict) else ''
            errs.append('uncaught: ' + ' | '.join(x for x in [d.get('text', ''), extra, ex.get('description', '')] if x)[:500])
        elif m == 'Log.entryAdded':
            e = p.get('entry', {})
            if e.get('level') == 'error':
                errs.append('log.error: ' + str(e.get('text'))[:400])
    ws.events = []
    # 页面内钩子收集到的错误
    try:
        hooked = ws.evaluate('JSON.stringify(window.__errs||[])')
        for item in json.loads(hooked or '[]'):
            errs.append('page-hook: ' + str(item)[:400])
    except Exception:
        pass
    try:
        ws.evaluate('window.__errs = []')
    except Exception:
        pass
    return errs


def click_center(ws, expr, label):
    rect = ws.evaluate(
        '(function(){var el=%s; if(!el) return null; el.scrollIntoView({block:"center"});'
        'var r=el.getBoundingClientRect();'
        'return {x:r.left+r.width/2, y:r.top+r.height/2, w:Math.round(r.width), h:Math.round(r.height), text:(el.innerText||"").trim()};})()' % expr
    )
    if not rect:
        raise RuntimeError('element not found: ' + label)
    x, y = rect['x'], rect['y']
    ws.call('Input.dispatchMouseEvent', {'type': 'mouseMoved', 'x': x, 'y': y, 'button': 'none'})
    ws.call('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1})
    ws.call('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1})
    return rect


def main():
    os.makedirs(ARTIFACT_DIR, exist_ok=True)

    port = free_port()
    httpd = QuietServer(('127.0.0.1', port), SpaHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = 'http://127.0.0.1:%d' % port
    print('static server: %s -> %s' % (base, DIST), flush=True)

    # 资源 MIME 前置核对（脚手架有效性闸门）
    html = urllib.request.urlopen(base + '/').read().decode('utf-8')
    js_ref = re.findall(r'src="(/assets/[^"]+\.js)"', html)
    mime_ok = True
    for ref in js_ref:
        resp = urllib.request.urlopen(base + ref)
        ct = resp.headers.get('Content-Type', '')
        if 'javascript' not in ct:
            mime_ok = False
    case('脚手架：静态 JS 以 text/javascript 提供（模块脚本可执行）', mime_ok, 'refs=%s' % js_ref)

    cdp = free_port()
    profile = tempfile.mkdtemp(prefix='hms-verify-')
    chrome = subprocess.Popen([
        CHROME, '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
        '--disable-extensions', '--disable-background-networking', '--disable-sync', '--mute-audio',
        '--window-size=1366,768', '--user-data-dir=' + profile,
        '--remote-debugging-port=%d' % cdp, 'about:blank',
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    ws = None
    try:
        target = None
        dl = time.time() + 40
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
        ws = WS(target['webSocketDebuggerUrl'])

        ws.call('Page.enable')
        ws.call('Runtime.enable')
        ws.call('Log.enable')
        ws.call('Network.enable')
        ws.call('Page.addScriptToEvaluateOnNewDocument', {'source': ERROR_HOOK})

        ws.call('Emulation.setDeviceMetricsOverride',
                {'width': 1366, 'height': 768, 'deviceScaleFactor': 1, 'mobile': False})

        # ================= 1. 首页可正常打开 =================
        landed = navigate(ws, base + '/')
        case('首页导航落地并完成加载', landed, 'location=%s' % ws.evaluate('location.pathname'))

        app_children = ws.evaluate('document.querySelector("#app").children.length')
        case('Vue 应用已挂载（#app 非空）', app_children > 0, '#app children=%s' % app_children)

        body = ws.evaluate('document.body.innerText')
        must = [
            '个人健康管理系统', 'Personal Health Management System',
            '健康生活', '从记录开始',
            '科学记录 · 数据分析 · 目标管理 · 习惯养成',
            '让健康管理更简单、更专业、更持久',
            '医生端', '健身教练端', '管理员端',
            '进入医生端', '进入健身教练端', '进入管理员端',
            '数据安全', '专业分析', '多端支持', '助力健康',
            '版本 V3.2', '关于我们', '帮助中心', '联系我们',
        ]
        missing = [t for t in must if t not in body]
        case('首页关键文案齐全（%d 项）' % len(must), not missing, 'missing=%s' % missing)

        cnt = ws.evaluate('document.querySelectorAll(".portal__card").length')
        case('身份卡片数量 = 3', cnt == 3, 'count=%s' % cnt)

        btn_texts = ws.evaluate(
            '[].map.call(document.querySelectorAll(".portal__card-btn"),'
            'function(b){return (b.innerText||"").trim();})'
        )
        case('三个入口按钮文案正确',
             btn_texts and len(btn_texts) == 3
             and '进入医生端' in btn_texts[0] and '进入健身教练端' in btn_texts[1] and '进入管理员端' in btn_texts[2],
             'buttons=%s' % btn_texts)

        btn_is_native = ws.evaluate(
            '[].every.call(document.querySelectorAll(".portal__card-btn"),function(b){return b.tagName==="BUTTON";})'
        )
        case('入口按钮为真实可点击元素（native button）', btn_is_native is True)

        accents = ws.evaluate(
            '[].map.call(document.querySelectorAll(".portal__card"),'
            'function(el){return getComputedStyle(el).getPropertyValue("--card-accent").trim();})'
        )
        case('三张卡片主题色互不相同（青绿/蓝/蓝紫）',
             isinstance(accents, list) and len(set(accents)) == 3, 'accents=%s' % accents)

        bf = ws.evaluate(
            '(function(){var el=document.querySelector(".portal__card");'
            'if(!el) return ""; var s=getComputedStyle(el);'
            'return s.backdropFilter||s.webkitBackdropFilter||"";})()'
        )
        case('卡片启用 backdrop-filter 毛玻璃', bool(bf) and bf != 'none', 'backdropFilter=%s' % bf)

        hover = ws.evaluate(
            '(function(){var el=document.querySelector(".portal__card"); if(!el) return null;'
            'var s=getComputedStyle(el);'
            'return {transition:s.transitionProperty, shadow:s.boxShadow, radius:s.borderRadius};})()'
        )
        case('卡片具备 hover 过渡 / 柔和阴影 / 统一圆角',
             bool(hover) and 'transform' in str(hover.get('transition', ''))
             and hover.get('shadow') not in (None, 'none')
             and hover.get('radius') not in (None, '0px'),
             json.dumps(hover, ensure_ascii=False))

        bg_layers = ws.evaluate(
            '(function(){var el=document.querySelector(".portal__bg"); if(!el) return null;'
            'var s=getComputedStyle(el);'
            'return {bgImage: s.backgroundImage.slice(0,120), isDark: s.backgroundColor};})()'
        )
        case('背景层存在（CSS 风景渐变兜底）', bool(bg_layers) and 'gradient' in str(bg_layers.get('bgImage', '')),
             json.dumps(bg_layers, ensure_ascii=False))

        has_photo = ws.evaluate('!!document.querySelector(".portal__bg-photo")')
        print('   [info] 是否已加载本地实景背景图 health-portal-bg: %s' % has_photo, flush=True)

        # ================= 2. 三档分辨率无横向滚动 =================
        for w, h in [(1366, 768), (1440, 900), (1920, 1080)]:
            ws.call('Emulation.setDeviceMetricsOverride',
                    {'width': w, 'height': h, 'deviceScaleFactor': 1, 'mobile': False})
            time.sleep(0.7)
            m = ws.evaluate(
                '({sw:document.documentElement.scrollWidth, cw:document.documentElement.clientWidth,'
                ' bw:document.body.scrollWidth, ih:window.innerHeight, iw:window.innerWidth})'
            )
            ok = m['sw'] <= m['cw'] + 1 and m['bw'] <= m['cw'] + 2
            case('%dx%d 无横向滚动' % (w, h), ok, json.dumps(m))

        # ================= 3. 1366x768 卡片完整可见 =================
        ws.call('Emulation.setDeviceMetricsOverride',
                {'width': 1366, 'height': 768, 'deviceScaleFactor': 1, 'mobile': False})
        time.sleep(0.7)
        vis = ws.evaluate(
            '(function(){var ih=window.innerHeight, iw=window.innerWidth, out=[];'
            'document.querySelectorAll(".portal__card").forEach(function(el){var r=el.getBoundingClientRect();'
            'out.push({top:Math.round(r.top),bottom:Math.round(r.bottom),left:Math.round(r.left),'
            'right:Math.round(r.right),w:Math.round(r.width),h:Math.round(r.height)});});'
            'return {ih:ih, iw:iw, cards:out};})()'
        )
        cards = vis['cards']
        fully = len(cards) == 3 and all(
            c['top'] >= -1 and c['bottom'] <= vis['ih'] + 1 and c['left'] >= -1 and c['right'] <= vis['iw'] + 1
            for c in cards)
        case('1366x768 三张卡片完整可见（无裁切）', fully, json.dumps(vis, ensure_ascii=False))
        case('三张卡片尺寸统一（等宽等高）',
             len(set(c['h'] for c in cards)) == 1 and len(set(c['w'] for c in cards)) == 1,
             'heights=%s widths=%s' % ([c['h'] for c in cards], [c['w'] for c in cards]))

        feat = ws.evaluate(
            '(function(){var e=document.querySelector(".portal__features"); if(!e) return null;'
            'var r=e.getBoundingClientRect(); return {bottom:Math.round(r.bottom), ih:window.innerHeight};})()'
        )
        case('1366x768 底部四优势区可见', bool(feat) and feat['bottom'] <= feat['ih'] + 1, json.dumps(feat))

        # 截图取证
        for w, h in [(1366, 768), (1920, 1080)]:
            ws.call('Emulation.setDeviceMetricsOverride',
                    {'width': w, 'height': h, 'deviceScaleFactor': 1, 'mobile': False})
            time.sleep(0.9)
            shot = ws.call('Page.captureScreenshot', {'format': 'png'})
            p = os.path.join(ARTIFACT_DIR, 'identity-select-%dx%d.png' % (w, h))
            with open(p, 'wb') as f:
                f.write(base64.b64decode(shot['result']['data']))
            print('   [info] screenshot -> %s' % p, flush=True)

        # ================= 4. 三个入口真实跳转 =================
        roles = [
            ('医生', '.portal__card:nth-child(1) .portal__card-btn', '/doctor/login', '医生工作台 · Doctor Console'),
            ('健身教练', '.portal__card:nth-child(2) .portal__card-btn', '/coach/login', '健身教练工作台 · Coach Console'),
            ('管理员', '.portal__card:nth-child(3) .portal__card-btn', '/admin/login', '管理后台 · Admin Console'),
        ]
        for label, sel, expect_path, expect_text in roles:
            navigate(ws, base + '/')
            drain_errors(ws)
            ws.call('Emulation.setDeviceMetricsOverride',
                    {'width': 1366, 'height': 768, 'deviceScaleFactor': 1, 'mobile': False})
            time.sleep(0.5)
            before = ws.evaluate('location.pathname')
            try:
                rect = click_center(ws, 'document.querySelector(%s)' % json.dumps(sel), label)
            except Exception as e:
                case('%s入口按钮可被真实点击' % label, False, repr(e))
                continue
            got, dl = None, time.time() + 12
            while time.time() < dl:
                got = ws.evaluate('location.pathname')
                if got == expect_path:
                    break
                time.sleep(0.25)
            time.sleep(0.9)
            page_text = ws.evaluate('document.body.innerText')
            errs = drain_errors(ws)

            case('%s入口：按钮真实点击命中（点击 "%s"）' % (label, rect.get('text', '')), True,
                 'rect=%sx%s' % (rect.get('w'), rect.get('h')))
            case('%s入口：路由真实跳转到 %s' % (label, expect_path), got == expect_path,
                 'from=%s -> %s' % (before, got))
            case('%s入口：落地页为该角色登录页' % label, expect_text in page_text,
                 'expect=%s found=%s' % (expect_text, expect_text in page_text))
            case('%s入口：跳转过程无 Console 报错' % label, len(errs) == 0, '|'.join(errs)[:400])

        # ================= 5. 首页 Console 体检 =================
        navigate(ws, base + '/')
        errs_home = drain_errors(ws)
        case('身份选择首页无 Console 红色错误 / 未捕获异常', len(errs_home) == 0, '|'.join(errs_home)[:600])

        # ================= 6. 其他页面未被破坏（抽查） =================
        for probe, marker in [('/doctor/login', '医生工作台 · Doctor Console'),
                              ('/coach/login', '健身教练工作台 · Coach Console'),
                              ('/admin/login', '管理后台 · Admin Console'),
                              ('/', '健康生活')]:
            navigate(ws, base + probe)
            txt = ws.evaluate('document.body.innerText')
            kids = ws.evaluate('document.querySelector("#app").children.length')
            case('回归抽查：%s 正常渲染' % probe, marker in txt, '#app children=%s' % kids)

        # ---------------- 汇总
        total = len(RESULTS)
        passed = sum(1 for _, ok, _ in RESULTS if ok)
        print('\n==============================', flush=True)
        print('TOTAL %d  PASS %d  FAIL %d' % (total, passed, total - passed), flush=True)
        for n, ok, d in RESULTS:
            if not ok:
                print('  FAIL: %s | %s' % (n, d), flush=True)
        print('==============================', flush=True)

        with open(os.path.join(ARTIFACT_DIR, 'verify_result.json'), 'w', encoding='utf-8') as f:
            json.dump({'total': total, 'pass': passed, 'fail': total - passed,
                       'results': [{'name': n, 'status': 'PASS' if ok else 'FAIL', 'detail': d}
                                   for n, ok, d in RESULTS]}, f, ensure_ascii=False, indent=2)
        return 0 if passed == total else 1

    finally:
        try:
            if ws:
                ws.sock.close()
        except Exception:
            pass
        try:
            chrome.terminate()
            chrome.wait(timeout=10)
        except Exception:
            try:
                chrome.kill()
            except Exception:
                pass
        try:
            httpd.shutdown()
            httpd.server_close()
        except Exception:
            pass
        sys.stdout.flush()


if __name__ == '__main__':
    sys.exit(main())
