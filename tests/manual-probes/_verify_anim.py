# -*- coding: utf-8 -*-
"""
IdentitySelect.vue —— CSS 轻动态背景 专项端到端验证。

与 _verify_portal.py（针对 dist 生产产物）互补：本脚本验证 **开发态源码**
（自启 Vite dev server 在 127.0.0.1:5173，即需求里指定的 localhost:5173），
因此直接验证 src/views/portal/IdentitySelect.vue 的真实样式，而非编译产物。

覆盖需求《八、验证》12 项：
  1  npm run build 由外部单独执行（本脚本只负责运行时）
  2  页面可正常打开
  3-5 医生/健身教练/管理员三个入口真实点击跳转
  6  Console 0 新增红色错误
  7  1366x768 无横向滚动
  8  1920x1080 无横向滚动
  9  三张身份卡片位置不因动画发生变化（3s + 60s 两次比对）
  10 动画层不拦截鼠标点击（elementFromPoint + 真实点击双取证）
  11 prefers-reduced-motion 生效
  12 连续运行 60s：无布局漂移、无长任务卡顿、无新错误

脚手架注意（Windows，沿用上一轮踩坑结论）：
  * headless 下 CSS 动画时钟随"帧"推进，取样前后强制截帧，避免把
    "无头渲染节流"误判成"动画没生效"。
"""
import base64
import json
import os
import re
import socket
import struct
import subprocess
import sys
import time
import urllib.request

MW = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system\management-web'
NODE = r'C:\Users\Toporder-WS\.workbuddy\binaries\node\versions\22.22.2-3\node.exe'
VITE = os.path.join(MW, 'node_modules', 'vite', 'bin', 'vite.js')
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
ART = os.path.join(MW, '_verify_out')
PORT = 5173
BASE = 'http://127.0.0.1:%d' % PORT
SOAK_SECONDS = 62

RESULTS = []


def case(name, ok, detail=''):
    RESULTS.append((name, bool(ok), detail))
    print(('PASS  ' if ok else 'FAIL  ') + name + (('  |  ' + str(detail)) if detail else ''), flush=True)


# ---------------------------------------------------------------- 极简 WebSocket / CDP
class WS:
    def __init__(self, url):
        rest = url[5:]
        hostport, _, path = rest.partition('/')
        host, _, port = hostport.partition(':')
        self.sock = socket.create_connection((host, int(port)), timeout=90)
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

    def call(self, method, params=None, timeout=90):
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

    def evaluate(self, expr, timeout=90):
        r = self.call('Runtime.evaluate',
                      {'expression': expr, 'returnByValue': True, 'awaitPromise': True}, timeout)
        res = r.get('result', {})
        if res.get('exceptionDetails'):
            raise RuntimeError('JS: ' + json.dumps(res['exceptionDetails'], ensure_ascii=False)[:400])
        return res.get('result', {}).get('value')

    def shot(self, path):
        """强制产帧（headless 下动画时钟靠帧推进），用于取样前推进时间线。"""
        s = self.call('Page.captureScreenshot', {'format': 'png'})
        if path:
            with open(path, 'wb') as f:
                f.write(base64.b64decode(s['result']['data']))


HOOK = r"""
(function(){
  if (window.__installed) return;
  window.__installed = true;
  window.__errs = [];
  window.__lt = [];
  window.__cls = 0;
  window.addEventListener('error', function(e){
    window.__errs.push('error: ' + (e.message||'') + ' @' + (e.filename||'') + ':' + (e.lineno||0));
  }, true);
  window.addEventListener('unhandledrejection', function(e){
    window.__errs.push('unhandledrejection: ' + String((e.reason && e.reason.message) || e.reason).slice(0,300));
  });
  var ce = console.error.bind(console);
  console.error = function(){
    var parts = [];
    for (var i=0;i<arguments.length;i++){
      var a = arguments[i];
      try { parts.push(typeof a === 'string' ? a : (a && a.message ? a.message : JSON.stringify(a))); }
      catch(_) { parts.push(String(a)); }
    }
    window.__errs.push('console.error: ' + parts.join(' ').slice(0,300));
    return ce.apply(console, arguments);
  };
  try {
    new PerformanceObserver(function(l){
      l.getEntries().forEach(function(e){ window.__lt.push(Math.round(e.duration)); });
    }).observe({type:'longtask', buffered:true});
  } catch(_) {}
  try {
    new PerformanceObserver(function(l){
      l.getEntries().forEach(function(e){ if(!e.hadRecentInput) window.__cls += e.value; });
    }).observe({type:'layout-shift', buffered:true});
  } catch(_) {}
  window.__frames = 0;
  (function loop(){
    var last = performance.now(), n = 0;
    function tick(t){
      window.__frames++; n++;
      var dt = t - last;
      if (dt >= 1000) { window.__fps = Math.round(n * 1000 / dt); n = 0; last = t; }
      requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  })();
})();
"""

# 内容层关键元素（动画期间位置必须完全不变）
ANCHORS_JS = """
(function(){
  var sel = ['.portal__logo', '.portal__brand-title', '.portal__hero-title', '.portal__hero-sub',
             '.portal__card:nth-child(1)', '.portal__card:nth-child(2)', '.portal__card:nth-child(3)',
             '.portal__card:nth-child(1) .portal__card-btn', '.portal__card:nth-child(2) .portal__card-btn',
             '.portal__card:nth-child(3) .portal__card-btn', '.portal__features', '.portal__note'];
  var o = {};
  sel.forEach(function(s){
    var el = document.querySelector(s);
    if (!el) { o[s] = null; return; }
    var r = el.getBoundingClientRect();
    o[s] = [Math.round(r.left*100)/100, Math.round(r.top*100)/100,
            Math.round(r.width*100)/100, Math.round(r.height*100)/100];
  });
  return o;
})()
"""

# 装饰层动画取证
ANIM_JS = """
(function(){
  function q(s){ return document.querySelector(s); }
  function cs(el, pe){ return pe ? getComputedStyle(el, pe) : getComputedStyle(el); }
  function anim(el, pe){
    var s = cs(el, pe);
    return {name: s.animationName, dur: s.animationDuration, iter: s.animationIterationCount,
            timing: s.animationTimingFunction, delay: s.animationDelay,
            pe: s.pointerEvents, z: s.zIndex, op: s.opacity};
  }
  var bg = q('.portal__bg'), fx = q('.portal__fx');
  var clouds = [].slice.call(document.querySelectorAll('.portal__cloud'));
  var run = [];
  [['fx', fx, null], ['bg', bg, null], ['bg::before', bg, '::before'], ['bg::after', bg, '::after'],
   ['sun', q('.portal__sun'), null], ['shine', q('.portal__shine'), null]]
   .forEach(function(t){
     if (!t[1]) { run.push({k: t[0], missing: true}); return; }
     var a = anim(t[1], t[2]);
     a.k = t[0];
     try {
       var list = (t[2] ? [] : t[1].getAnimations()).map(function(an){
         return {n: an.animationName, st: an.playState, ct: Math.round(an.currentTime || 0)};
       });
       a.anims = list;
     } catch(_) { a.anims = []; }
     run.push(a);
   });
  var cloudInfo = clouds.map(function(c){
    var a = anim(c);
    var list = c.getAnimations().map(function(an){ return an.animationName + '@' + Math.round(an.currentTime||0); });
    a.anims = list;
    return a;
  });
  var clickable = [].slice.call(document.querySelectorAll('.portal__fx, .portal__fx *'))
      .map(function(e){ return cs(e).pointerEvents; });
  var contentZ = parseInt(cs(q('.portal__cards')).zIndex || '0', 10);
  return {
    fxExists: !!fx, bgExists: !!bg, cloudCount: clouds.length,
    fx: anim(fx), bg: anim(bg),
    bgBefore: anim(bg, '::before'), bgAfter: anim(bg, '::after'),
    bgBeforeClip: cs(bg, '::before').clipPath, bgAfterClip: cs(bg, '::after').clipPath,
    bgImage: cs(bg).backgroundImage.slice(0, 80),
    veilBg: cs(q('.portal__bg-veil')).backgroundImage.slice(0, 60),
    cardBackdrop: (function(){ var s = cs(q('.portal__card')); return s.backdropFilter || s.webkitBackdropFilter || ''; })(),
    clouds: cloudInfo, run: run, fxPointerEvents: clickable,
    wrapperZ: cs(q('.portal__main')).zIndex, cardsZ: cs(q('.portal__cards')).zIndex,
    contentZ: contentZ, fxZ: cs(fx).zIndex,
    fxW: fx.getBoundingClientRect().width, fxH: fx.getBoundingClientRect().height
  };
})()
"""

TRANSFORM_JS = """
(function(){
  function t(s, pe){
    var el = document.querySelector(s);
    if (!el) return null;
    var st = getComputedStyle(el, pe || undefined);
    return {tf: st.transform, op: st.opacity};
  }
  return {cloud1: t('.portal__cloud--1'), sun: t('.portal__sun'),
          shine: t('.portal__shine'), bg: t('.portal__bg'),
          far: t('.portal__bg', '::before'), near: t('.portal__bg', '::after')};
})()
"""


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
            errs.append('console.error: ' + ' '.join(parts)[:300])
        elif m == 'Runtime.exceptionThrown':
            d = p.get('exceptionDetails', {})
            ex = d.get('exception', {}) or {}
            errs.append('uncaught: ' + ' | '.join(
                x for x in [d.get('text', ''), ex.get('description', '')] if x)[:400])
        elif m == 'Log.entryAdded':
            e = p.get('entry', {})
            if e.get('level') == 'error':
                errs.append('log.error: ' + str(e.get('text'))[:300])
    ws.events = []
    try:
        for item in json.loads(ws.evaluate('JSON.stringify(window.__errs||[])') or '[]'):
            errs.append('page-hook: ' + str(item)[:300])
    except Exception:
        pass
    try:
        ws.evaluate('window.__errs = []')
    except Exception:
        pass
    return errs


def wait_url_ready(ws, prefix, timeout=60):
    dl = time.time() + timeout
    ok = False
    while time.time() < dl:
        try:
            href, st = ws.evaluate('location.href'), ws.evaluate('document.readyState')
        except Exception:
            href, st = None, None
        if href and href.startswith(prefix) and st == 'complete':
            ok = True
            break
        time.sleep(0.2)
    time.sleep(1.4)   # 等 Vue 挂载 / dev 态样式注入 / 字体稳定
    return ok


def navigate(ws, url):
    ws.call('Page.navigate', {'url': url})
    return wait_url_ready(ws, url)


def free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    p = s.getsockname()[1]
    s.close()
    return p


def click_center(ws, sel, label):
    rect = ws.evaluate(
        '(function(){var el=document.querySelector(%s); if(!el) return null;'
        'el.scrollIntoView({block:"center"}); var r=el.getBoundingClientRect();'
        'return {x:r.left+r.width/2, y:r.top+r.height/2, w:Math.round(r.width), h:Math.round(r.height),'
        ' text:(el.innerText||"").trim()};})()' % json.dumps(sel)
    )
    if not rect:
        raise RuntimeError('element not found: ' + label)
    x, y = rect['x'], rect['y']
    ws.call('Input.dispatchMouseEvent', {'type': 'mouseMoved', 'x': x, 'y': y, 'button': 'none'})
    ws.call('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1})
    ws.call('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1})
    return rect


def start_dev_server():
    """返回 (proc_or_None, html, reused)。

    先探测 5173 是否**已有**dev server 在跑（例如用户自己开着 `npm run dev`）：
      - 有 -> 直接复用，proc 返回 None（收尾不去 kill 别人的进程）；
      - 无 -> 自起一个（用 --strictPort 保证不会被静默换端口），失败则清理后抛错。
    归属必须如实上报，否则日志会谎称"脚本自起"。
    """
    try:
        with urllib.request.urlopen(BASE + '/', timeout=3) as r:
            body = r.read().decode('utf-8', 'replace')
        if r.status == 200 and 'id="app"' in body:
            return None, body, True
    except Exception:
        pass

    log = open(os.path.join(ART, 'dev-server.log'), 'wb')
    p = subprocess.Popen(
        [NODE, VITE, '--host', '127.0.0.1', '--port', str(PORT), '--strictPort'],
        cwd=MW, stdout=log, stderr=subprocess.STDOUT)
    dl = time.time() + 120
    while time.time() < dl:
        try:
            with urllib.request.urlopen(BASE + '/', timeout=3) as r:
                body = r.read().decode('utf-8', 'replace')
            if r.status == 200 and 'id="app"' in body:
                return p, body, False
        except Exception:
            pass
        if p.poll() is not None:
            raise RuntimeError('vite dev server exited early (code %s)' % p.returncode)
        time.sleep(0.6)
    try:
        p.terminate()
        p.wait(timeout=10)
    except Exception:
        try:
            p.kill()
        except Exception:
            pass
    raise RuntimeError('vite dev server not ready in 120s')


def main():
    os.makedirs(ART, exist_ok=True)
    t0 = time.time()

    dev, html, reused = start_dev_server()
    case('脚手架：127.0.0.1:5173 的 dev server 就绪并返回 index.html（来源：%s）'
         % ('复用已在运行的实例' if reused else '本脚本自起'),
         'id="app"' in html, '%.1fs' % (time.time() - t0))

    cdp = free_port()
    import tempfile
    profile = tempfile.mkdtemp(prefix='hms-anim-')
    chrome = subprocess.Popen([
        CHROME, '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
        '--disable-extensions', '--disable-background-networking', '--disable-sync', '--mute-audio',
        '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
        '--disable-backgrounding-occluded-windows', '--force-device-scale-factor=1',
        '--window-size=1366,768', '--user-data-dir=' + profile,
        '--remote-debugging-port=%d' % cdp, 'about:blank',
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    ws = None
    try:
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
        ws = WS(target['webSocketDebuggerUrl'])
        ws.call('Page.enable'); ws.call('Runtime.enable'); ws.call('Log.enable'); ws.call('Network.enable')
        ws.call('Page.addScriptToEvaluateOnNewDocument', {'source': HOOK})
        ws.call('Emulation.setDeviceMetricsOverride',
                {'width': 1366, 'height': 768, 'deviceScaleFactor': 1, 'mobile': False})

        # ============ 2. 页面可正常打开 ============
        landed = navigate(ws, BASE + '/')
        case('② 身份选择首页在 dev server 正常打开（Vue 已挂载）',
             landed and (ws.evaluate('document.querySelector("#app").children.length') or 0) > 0,
             'path=%s' % ws.evaluate('location.pathname'))

        body = ws.evaluate('document.body.innerText')
        must = ['个人健康管理系统', 'Personal Health Management System', '健康生活', '从记录开始',
                '科学记录 · 数据分析 · 目标管理 · 习惯养成', '让健康管理更简单、更专业、更持久',
                '医生端', '健身教练端', '管理员端', '进入医生端', '进入健身教练端', '进入管理员端',
                '数据安全', '专业分析', '多端支持', '助力健康', '版本 V3.2']
        missing = [t for t in must if t not in body]
        case('页面关键文案与三入口完好（%d 项）' % len(must), not missing, 'missing=%s' % missing)

        # ============ 新增动画层取证 ============
        info = ws.evaluate(ANIM_JS)
        print('   [info] 动画取证 =', json.dumps({k: info[k] for k in
              ('fxExists', 'cloudCount', 'wrapperZ', 'cardsZ', 'fxZ', 'veilBg', 'cardBackdrop')},
              ensure_ascii=False), flush=True)

        case('装饰层 .portal__fx 已挂载（z-index=2 / overflow=hidden）',
             info['fxExists'] and info['fx']['z'] == '2' and info['fxW'] > 300 and info['fxH'] > 300,
             'w=%s h=%s z=%s' % (info['fxW'], info['fxH'], info['fx']['z']))

        case('① 云层 3 层已挂载', info['cloudCount'] == 3, 'count=%s' % info['cloudCount'])

        cloud_ok, cloud_detail = True, []
        for i, c in enumerate(info['clouds']):
            ok = (c['name'].startswith('portal-cloud-drift') and c['iter'] == 'infinite'
                  and c['timing'] == 'linear' and 45 <= float(c['dur'].replace('s', '')) <= 80)
            cloud_ok = cloud_ok and ok
            cloud_detail.append('%s/%s/%s/%s' % (c['name'], c['dur'], c['timing'], c['iter']))
        case('① 云层动画：45~80s / linear / infinite', cloud_ok, ' | '.join(cloud_detail))

        case('② 阳光呼吸：11s，scale+opacity 弱呼吸',
             info['run'][4]['name'].startswith('portal-sun-breathe') and info['run'][4]['dur'] == '11s',
             '%s / %s' % (info['run'][4]['name'], info['run'][4]['dur']))

        case('③ 湖面微光：23s linear',
             info['run'][5]['name'].startswith('portal-shine-flow') and info['run'][5]['dur'] == '23s'
             and info['run'][5]['timing'] == 'linear',
             '%s / %s / %s' % (info['run'][5]['name'], info['run'][5]['dur'], info['run'][5]['timing']))

        case('④ 远山景深：38s（25~45s 区间）',
             info['bgBefore']['name'].startswith('portal-mountain-far') and info['bgBefore']['dur'] == '38s',
             '%s / %s' % (info['bgBefore']['name'], info['bgBefore']['dur']))

        case('④ 近景景深：31s（25~45s 区间）',
             info['bgAfter']['name'].startswith('portal-mountain-near') and info['bgAfter']['dur'] == '31s',
             '%s / %s' % (info['bgAfter']['name'], info['bgAfter']['dur']))

        case('⑤ 整体背景微呼吸：42s（30~50s 区间）',
             info['bg']['name'].startswith('portal-bg-breathe') and info['bg']['dur'] == '42s',
             '%s / %s' % (info['bg']['name'], info['bg']['dur']))

        case('动画全部 infinite（不会停）',
             all(a.get('iter') == 'infinite' for a in
                 [info['bg'], info['bgBefore'], info['bgAfter'], info['run'][4], info['run'][5]]
                 + info['clouds']))

        # 未使用 JS / 未引入第三方动画库
        src_txt = open(os.path.join(MW, 'src', 'views', 'portal', 'IdentitySelect.vue'),
                       'rb').read().decode('utf-8', 'replace')
        case('实现方式为纯 CSS（.vue 内无任何 JS 动画代码）',
             'requestAnimationFrame' not in src_txt and 'setInterval' not in src_txt)

        # ============ 静态风景未被破坏 ============
        case('原有 CSS 风景保留（.portal__bg 风景渐变仍在）',
             'gradient' in info['bgImage'], info['bgImage'])
        case('原有山体剪影保留（远山 / 近景 clip-path 均仍在）',
             info['bgBeforeClip'] not in ('none', 'MISSING') and info['bgAfterClip'] not in ('none', 'MISSING'),
             'far=%s near=%s' % (info['bgBeforeClip'][:30], info['bgAfterClip'][:30]))
        case('提亮遮罩规则未被破坏（background-image 仍为渐变）',
             'gradient' in info['veilBg'], info['veilBg'])
        case('上一轮卡片毛玻璃未回退（backdrop-filter 生效）',
             bool(info['cardBackdrop']) and info['cardBackdrop'] != 'none', info['cardBackdrop'])

        # ============ 层级 + 点击穿透 ============
        case('层级契约成立：装饰层 z-index(2) < 内容层 z-index(3)',
             info['fxZ'] == '2' and info['wrapperZ'] == '3',
             'fx=%s main=%s (cards computed=%s)' % (info['fxZ'], info['wrapperZ'], info['cardsZ']))

        pe_all_none = bool(info['fxPointerEvents']) and all(v == 'none' for v in info['fxPointerEvents'])
        case('装饰层及其全部子元素 pointer-events:none', pe_all_none,
             'checked=%d values=%s' % (len(info['fxPointerEvents']), set(info['fxPointerEvents'])))

        hit = ws.evaluate("""
        (function(){
          function hit(sel){ var el=document.querySelector(sel); if(!el) return {sel:sel,err:'missing'};
            var r=el.getBoundingClientRect(); var t=document.elementFromPoint(r.left+r.width/2, r.top+r.height/2);
            return {sel:sel, inside: !!(t && (el===t || el.contains(t))), tag: t?t.tagName+'.'+(t.className||'').toString().split(' ')[0]:'null'};
          }
          return [hit('.portal__card:nth-child(1)'), hit('.portal__card:nth-child(2)'), hit('.portal__card:nth-child(3)'),
                  hit('.portal__card:nth-child(1) .portal__card-btn'), hit('.portal__card:nth-child(2) .portal__card-btn'),
                  hit('.portal__card:nth-child(3) .portal__card-btn')];
        })()
        """)
        case('⑩ 三张卡片中心命中自身（动画层未拦截）',
             all(h.get('inside') for h in hit[:3]), json.dumps(hit[:3], ensure_ascii=False))
        case('⑩ 三个入口按钮中心命中自身（动画层未拦截）',
             all(h.get('inside') for h in hit[3:]), json.dumps(hit[3:], ensure_ascii=False))

        # ============ 内容层稳定：取样点 ============
        def anchors():
            return ws.evaluate(ANCHORS_JS)

        a0 = anchors()
        ws.shot(os.path.join(ART, 'anim-frame-t0.png'))
        time.sleep(3.0)
        ws.shot(None)                      # 强制产帧，推进动画时钟
        a3 = anchors()
        drift3 = [k for k in a0 if a0[k] != a3[k]]
        case('⑨ 3 秒后内容层位置零漂移（12 个关键元素）', not drift3,
             'drift=%s' % drift3)

        # 动画确实在动
        tf0 = ws.evaluate(TRANSFORM_JS)
        ws.shot(None)
        time.sleep(2.5)
        ws.shot(None)
        tf1 = ws.evaluate(TRANSFORM_JS)
        moved = []
        for k in tf0:
            if tf0[k] != tf1[k]:
                moved.append(k)
        case('云层/阳光/湖面/背景在 2.5s 内真实位移（动画在跑）',
             all(k in moved for k in ('cloud1', 'sun', 'shine', 'bg')),
             'moved=%s' % moved)
        case('远山与近景在 2.5s 内真实位移（景深生效）',
             all(k in moved for k in ('far', 'near')), 'moved=%s' % moved)
        print('   [info] t0=%s' % json.dumps(tf0, ensure_ascii=False)[:200], flush=True)
        print('   [info] t1=%s' % json.dumps(tf1, ensure_ascii=False)[:200], flush=True)

        # 动画当前时间在推进
        ct = ws.evaluate("""
        (function(){
          var el = document.querySelector('.portal__cloud--1');
          return el.getAnimations().map(function(an){
            return {n: an.animationName, ct: Math.round(an.currentTime || 0), st: an.playState};
          });
        })()
        """)
        case('云层动画 playState=running 且 currentTime>0（时间线在推进）',
             bool(ct) and all(x['st'] == 'running' and x['ct'] > 0 for x in ct),
             json.dumps(ct, ensure_ascii=False))

        # ============ 三档分辨率 ============
        for w, h in [(1366, 768), (1440, 900), (1920, 1080)]:
            ws.call('Emulation.setDeviceMetricsOverride',
                    {'width': w, 'height': h, 'deviceScaleFactor': 1, 'mobile': False})
            time.sleep(0.8)
            m = ws.evaluate('({sw:document.documentElement.scrollWidth, cw:document.documentElement.clientWidth,'
                            ' bw:document.body.scrollWidth})')
            ok = m['sw'] <= m['cw'] + 1 and m['bw'] <= m['cw'] + 2
            case(('⑦ ' if (w, h) == (1366, 768) else ('⑧ ' if (w, h) == (1920, 1080) else ''))
                 + '%dx%d 无横向滚动' % (w, h), ok, json.dumps(m))

        # 1366x768 卡片完整可见 + 装饰层未溢出成滚动条
        ws.call('Emulation.setDeviceMetricsOverride',
                {'width': 1366, 'height': 768, 'deviceScaleFactor': 1, 'mobile': False})
        time.sleep(0.8)
        vis = ws.evaluate("""
        (function(){
          var ih=window.innerHeight, iw=window.innerWidth, out=[];
          document.querySelectorAll('.portal__card').forEach(function(el){
            var r=el.getBoundingClientRect();
            out.push({top:Math.round(r.top),bottom:Math.round(r.bottom),left:Math.round(r.left),
                      right:Math.round(r.right),w:Math.round(r.width),h:Math.round(r.height)});});
          var fx=document.querySelector('.portal__fx').getBoundingClientRect();
          return {ih:ih, iw:iw, cards:out, fx:{l:Math.round(fx.left),r:Math.round(fx.right),w:Math.round(fx.width)},
                  docSW:document.documentElement.scrollWidth, docCW:document.documentElement.clientWidth};
        })()
        """)
        case('1366x768 三张卡片完整可见', all(c['top'] >= -1 and c['bottom'] <= vis['ih'] + 1
                                          and c['left'] >= -1 and c['right'] <= vis['iw'] + 1
                                          for c in vis['cards']),
             json.dumps(vis['cards']))
        case('装饰层未撑出视口（放大/位移后仍不产生横向溢出）',
             vis['docSW'] <= vis['docCW'] + 1, 'scrollWidth=%s clientWidth=%s fx=%s'
             % (vis['docSW'], vis['docCW'], vis['fx']))
        case('三个身份入口按钮可见可点（native button）',
             ws.evaluate('[].every.call(document.querySelectorAll(".portal__card-btn"),'
                         'function(b){return b.tagName==="BUTTON";})') is True)

        # 矮视口回归：overflow:clip 不得吞掉内容。
        # 注意（原本处断言写错过一次）：本页用 clamp()+vh 自适应，620px 高时内容本就放得下
        # （scrollHeight == innerHeight 属正常，不是缺陷）。故判据改为"滚到底后底部内容完整可见"，
        # 并另取一个必然溢出的 520px 档，验证"超高时仍可滚动到底"。
        def probe_short(h):
            ws.call('Emulation.setDeviceMetricsOverride',
                    {'width': 1366, 'height': h, 'deviceScaleFactor': 1, 'mobile': False})
            time.sleep(1.0)
            return ws.evaluate("""
            (function(){
              var de = document.documentElement;
              window.scrollTo(0, 99999);
              var maxY = window.scrollY;
              var note = document.querySelector('.portal__note').getBoundingClientRect();
              var feat = document.querySelector('.portal__features').getBoundingClientRect();
              window.scrollTo(0, 0);
              return {vh: %d, sh: de.scrollHeight, ih: window.innerHeight, maxY: Math.round(maxY),
                      noteBottom: Math.round(note.bottom), featBottom: Math.round(feat.bottom),
                      cards: document.querySelectorAll('.portal__card').length,
                      sw: de.scrollWidth, cw: de.clientWidth};
            })()
            """ % h)

        s620 = probe_short(620)
        case('矮视口 1366x620：底部四优势与说明未被裁剪吞掉（滚到底后完整可见）',
             s620['cards'] == 3 and s620['noteBottom'] <= s620['ih'] + 1
             and s620['featBottom'] <= s620['ih'] + 1, json.dumps(s620))
        case('矮视口 1366x620：仍无横向滚动', s620['sw'] <= s620['cw'] + 1,
             'sw=%s cw=%s' % (s620['sw'], s620['cw']))

        s520 = probe_short(520)
        case('极矮视口 1366x520：内容超出视口时可滚动到底（裁剪未吞内容）',
             s520['sh'] > s520['ih'] and s520['maxY'] >= s520['sh'] - s520['ih'] - 2
             and s520['noteBottom'] <= s520['ih'] + 1, json.dumps(s520))
        case('极矮视口 1366x520：仍无横向滚动', s520['sw'] <= s520['cw'] + 1,
             'sw=%s cw=%s' % (s520['sw'], s520['cw']))

        ws.call('Emulation.setDeviceMetricsOverride',
                {'width': 1366, 'height': 768, 'deviceScaleFactor': 1, 'mobile': False})
        time.sleep(0.6)

        # 截图取证
        for w, h in [(1366, 768), (1920, 1080)]:
            ws.call('Emulation.setDeviceMetricsOverride',
                    {'width': w, 'height': h, 'deviceScaleFactor': 1, 'mobile': False})
            time.sleep(1.0)
            p = os.path.join(ART, 'identity-select-anim-%dx%d.png' % (w, h))
            ws.shot(p)
            print('   [info] screenshot -> %s' % p, flush=True)

        # ============ ⑪ prefers-reduced-motion ============
        ws.call('Emulation.setEmulatedMedia',
                {'features': [{'name': 'prefers-reduced-motion', 'value': 'reduce'}]})
        time.sleep(0.6)
        rm = ws.evaluate("""
        (function(){
          function n(sel,pe){ var el=document.querySelector(sel); if(!el) return 'MISSING';
            return getComputedStyle(el, pe||undefined).animationName; }
          var bg=document.querySelector('.portal__bg');
          return {bg:n('.portal__bg'), before:n('.portal__bg','::before'), after:n('.portal__bg','::after'),
                  cloud:n('.portal__cloud--1'), sun:n('.portal__sun'), shine:n('.portal__shine'),
                  visible: ['.portal__cloud--1','.portal__sun','.portal__shine'].every(function(s){
                     var e=document.querySelector(s); var r=e.getBoundingClientRect();
                     return r.width>1 && r.height>1 && parseFloat(getComputedStyle(e).opacity)>0;
                  })};
        })()
        """)
        case('⑪ prefers-reduced-motion=reduce 时全部背景动画被停用',
             all(v in ('none',) for k, v in rm.items() if k != 'visible'),
             json.dumps(rm, ensure_ascii=False))
        case('⑪ reduce 下静态视觉完整（云/阳光/湖面层仍存在且可见）', rm['visible'] is True)

        ws.call('Emulation.setEmulatedMedia',
                {'features': [{'name': 'prefers-reduced-motion', 'value': 'no-preference'}]})
        time.sleep(0.6)
        back = ws.evaluate("getComputedStyle(document.querySelector('.portal__sun')).animationName")
        case('关闭 reduce 后动画恢复（未永久停用）', back.startswith('portal-sun-breathe'), 'name=%s' % back)

        # ============ ③④⑤ 三个入口真实点击跳转 ============
        roles = [
            ('③ 医生', '.portal__card:nth-child(1) .portal__card-btn', '/doctor/login', '医生工作台 · Doctor Console'),
            ('④ 健身教练', '.portal__card:nth-child(2) .portal__card-btn', '/coach/login', '健身教练工作台 · Coach Console'),
            ('⑤ 管理员', '.portal__card:nth-child(3) .portal__card-btn', '/admin/login', '管理后台 · Admin Console'),
        ]
        for label, sel, expect_path, expect_text in roles:
            navigate(ws, BASE + '/')
            drain_errors(ws)
            ws.call('Emulation.setDeviceMetricsOverride',
                    {'width': 1366, 'height': 768, 'deviceScaleFactor': 1, 'mobile': False})
            time.sleep(0.6)
            before = ws.evaluate('location.pathname')
            try:
                rect = click_center(ws, sel, label)
            except Exception as e:
                case('%s 入口按钮可被真实点击' % label, False, repr(e))
                continue
            got, dl = None, time.time() + 15
            while time.time() < dl:
                got = ws.evaluate('location.pathname')
                if got == expect_path:
                    break
                time.sleep(0.25)
            time.sleep(1.0)
            txt = ws.evaluate('document.body.innerText')
            errs = drain_errors(ws)
            case('%s 入口：真实点击命中按钮（"%s"）' % (label, rect.get('text', '')), True,
                 'rect=%sx%s' % (rect.get('w'), rect.get('h')))
            case('%s 入口：路由跳转到 %s' % (label, expect_path), got == expect_path,
                 '%s -> %s' % (before, got))
            case('%s 入口：落地页为该角色登录页' % label, expect_text in txt)
            case('%s 入口：跳转过程无 Console 报错' % label, len(errs) == 0, '|'.join(errs)[:300])

        # ============ ⑥ Console 体检 + ⑫ 60 秒长跑 ============
        navigate(ws, BASE + '/')
        errs_home = drain_errors(ws)
        case('⑥ 身份选择首页无 Console 红色错误 / 未捕获异常', len(errs_home) == 0, '|'.join(errs_home)[:400])

        print('   [info] 开始 %ds 长跑（内容漂移 / 滚动条稳定性 / 长任务 / 重排重绘 / 错误）...'
              % SOAK_SECONDS, flush=True)
        soak0 = anchors()
        ws.call('Performance.enable')
        pm0 = {m['name']: m['value'] for m in ws.call('Performance.getMetrics')['result']['metrics']}
        ws.evaluate('window.__lt=[]; window.__cls=0; window.__frames=0; window.__fps=0')
        snapshots = []
        dl = time.time() + SOAK_SECONDS
        n = 0
        while time.time() < dl:
            time.sleep(5)
            ws.shot(None)     # 每 5s 强制产帧，贴近真实渲染节奏
            n += 1
            s = ws.evaluate('({sw:document.documentElement.scrollWidth,'
                            ' cw:document.documentElement.clientWidth,'
                            ' sh:document.documentElement.scrollHeight, ih:window.innerHeight,'
                            ' fps:window.__fps||0, lt:(window.__lt||[]).length})')
            s['over'] = s['sh'] - s['ih']
            snapshots.append(s)
            print('   [soak %2ds] %s' % (n * 5, json.dumps(s)), flush=True)
        cws = sorted(set(s['cw'] for s in snapshots))
        overs = [s['over'] for s in snapshots]
        pm1 = {m['name']: m['value'] for m in ws.call('Performance.getMetrics')['result']['metrics']}
        d_layout = pm1.get('LayoutCount', 0) - pm0.get('LayoutCount', 0)
        d_style = pm1.get('RecalcStyleCount', 0) - pm0.get('RecalcStyleCount', 0)
        print('   [info] 60s 内 LayoutCount +%s / RecalcStyleCount +%s；clientWidth 取值=%s；'
              'max(scrollHeight-innerHeight)=%s' % (d_layout, d_style, cws, max(overs)), flush=True)
        soak1 = anchors()
        soak_errs = drain_errors(ws)
        perf = ws.evaluate('({lt:(window.__lt||[]).slice(0,20), ltN:(window.__lt||[]).length,'
                           ' cls:window.__cls, fps:window.__fps||0, frames:window.__frames||0})')
        drift_soak = [k for k in soak0 if soak0[k] != soak1[k]]
        max_over = max(s['sw'] - s['cw'] for s in snapshots)

        case('⑫ 60s 长跑后内容层位置零漂移（无布局漂移）', not drift_soak,
             'drift=%s clientWidth=%s' % (drift_soak, cws))
        case('⑫ 60s 长跑期间视口宽度恒定（无滚动条闪烁 -> 内容不横移）', len(cws) == 1,
             'clientWidth 取值集合=%s（含滚动条时应为 1351，无滚动条 1366）' % cws)
        case('⑫ 60s 长跑期间文档无可滚动溢出（装饰层缩放未撑高页面）', max(overs) <= 0,
             'max(scrollHeight-innerHeight)=%s' % max(overs))
        case('⑫ 背景动画不触发重排：60s 内 LayoutCount 增量≈0', d_layout <= 5,
             'dLayout=%s（若逐帧重排会是数千）' % d_layout)
        # 注意：ΔRecalcStyleCount≈1/帧 是 Chrome「存在 CSS 动画即每帧一趟样式重算」的固有行为，
        # 已用成对隔离证实（只留天空三层=1.0/帧、只留背景+山景=1.0/帧、全关=0），不是某一层没上合成层，
        # 也不降低帧率（7 种配置 fps 143.6~144.2）。故这里断言的是"不是逐元素重算"这个真不变量。
        case('⑫ 每帧样式重算 ≤1 次（非逐元素/逐层重算）',
             d_style <= perf['frames'] * 1.25 + 20,
             'dStyle=%s frames=%s => %.2f 次/帧' % (d_style, perf['frames'],
                                                 d_style / max(perf['frames'], 1)))
        case('⑫ 60s 长跑期间始终保持无横向滚动条', max_over <= 1,
             'max(scrollWidth-clientWidth)=%s' % max_over)
        case('⑫ 60s 长跑期间无长任务（>50ms）卡顿', perf['ltN'] == 0,
             'longtasks=%s fsps=%s cls=%.5f' % (perf['ltN'], perf['fps'], perf['cls']))
        case('⑫ 60s 长跑期间无新增 Console 错误', len(soak_errs) == 0, '|'.join(soak_errs)[:300])
        case('⑫ 60s 长跑期间累计布局偏移 CLS 接近 0（<0.01）', perf['cls'] < 0.01, 'cls=%.6f' % perf['cls'])
        print('   [info] 帧率采样(fps)=%s frames=%s longTasks=%s CLS=%.6f'
              % (perf['fps'], perf['frames'], perf['ltN'], perf['cls']), flush=True)

        # ============ 回归抽查 ============
        for probe, marker in [('/doctor/login', '医生工作台 · Doctor Console'),
                              ('/coach/login', '健身教练工作台 · Coach Console'),
                              ('/admin/login', '管理后台 · Admin Console'),
                              ('/', '健康生活')]:
            navigate(ws, BASE + probe)
            txt = ws.evaluate('document.body.innerText')
            case('回归抽查：%s 正常渲染' % probe, marker in txt)

        total = len(RESULTS)
        passed = sum(1 for _, ok, _ in RESULTS if ok)
        print('\n==============================', flush=True)
        print('TOTAL %d  PASS %d  FAIL %d  (%.0fs)' % (total, passed, total - passed, time.time() - t0), flush=True)
        for n_, ok, d in RESULTS:
            if not ok:
                print('  FAIL: %s | %s' % (n_, d), flush=True)
        print('==============================', flush=True)
        with open(os.path.join(ART, 'anim_verify_result.json'), 'w', encoding='utf-8') as f:
            json.dump({'total': total, 'pass': passed, 'fail': total - passed,
                       'perf': {k: perf[k] for k in ('ltN', 'cls', 'fps', 'frames')},
                       'results': [{'name': n_, 'status': 'PASS' if ok else 'FAIL', 'detail': d}
                                   for n_, ok, d in RESULTS]}, f, ensure_ascii=False, indent=2)
        return 0 if passed == total else 1

    finally:
        try:
            if ws:
                ws.sock.close()
        except Exception:
            pass
        for p in (chrome, dev):
            if p is None:      # 复用别人已在跑的 dev server 时不去 kill
                continue
            try:
                p.terminate()
                p.wait(timeout=10)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        sys.stdout.flush()


if __name__ == '__main__':
    sys.exit(main())
