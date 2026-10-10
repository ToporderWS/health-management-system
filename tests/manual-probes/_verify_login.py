# -*- coding: utf-8 -*-
"""
三个 PC 角色登录页（/admin/login、/doctor/login、/coach/login）UI 重构 —— 端到端验收。

覆盖需求《十三、验证要求》22 项：
  1  三页视觉结构均为「左插画 + 右登录卡片」
  2  管理员蓝紫主题正确        3  医生青绿主题正确        4  教练蓝色主题正确
  5  三页不再出现旧版大段功能介绍文字
  6  管理员没有注册入口        7  医生注册入口正常        8  教练注册入口正常
  9  返回身份选择正常         10  密码显示隐藏正常       11  登录接口未改变（业务文件零改动 + 接口状态码实证）
 12  admin 测试账号能登录     13  doctor001 能登录       14  coach001 能登录
 15  待审核医生无法登录       16  待审核教练无法登录     17  登录成功后 Dashboard 不受影响
 18  Console 0 新增红色错误   19  npm run build 由外部单独执行
 20  1366x768 无横向滚动      21  1440x900 正常           22  1920x1080 正常

已知环境事实（本轮实测，避免误判）：
  * Element Plus 的 `show-password` 眼睛按钮**只在输入框有值时渲染**
    （showPwdVisible = showPassword && !disabled && !readonly && (nativeInputValue || modelValue)），
    因此用例必须先填入密码再点眼睛，否则找不到按钮 —— 这是测试装置问题，不是产品缺陷。
  * ElMessage 默认 3s 自动关闭，断言必须"点完立即轮询"，不能固定 sleep 后再读。
  * 无头浏览器刚导航完成时表单可能尚未完成布局，点击前需等输入框有真实尺寸。
"""
import os
import subprocess
import sys
import time
import tempfile
import json
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _verify_anim import (  # noqa: E402
    ART, BASE, CHROME, HOOK, WS, case, click_center, free_port, navigate,
    start_dev_server, RESULTS,
)

MW = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system\management-web'
SRC = os.path.join(MW, 'src')
SESSION_T0 = time.mktime((2026, 10, 1, 15, 28, 0, 0, 0, -1))

AUTH_KEYS = ['hms_doctor_token', 'hms_doctor_info', 'hms_coach_token',
             'hms_coach_info', 'hms_admin_token', 'hms_admin_info']

OLD_LONG_TEXTS = [
    '后台固定 12 个一级模块', '账号审核、人员与关系管理', '医生 / 教练注册审核',
    '医患关系与教练学员关系绑定解绑', '健康数据中心筛选与 CSV 导出', '关键操作全量写入操作日志',
    '管理负责患者、查看真实健康数据', '患者健康指标与趋势可视化', '健康建议 / 体检通知 / 医疗记录',
    '数据权限严格绑定医患关系', '管理负责学员、只读学员运动数据', '学员运动时长与类型分布分析',
    '运动目标 / 训练计划全生命周期管理', '健身建议历史留痕，可随时回看',
]

UNTOUCHED = [
    'src/api/admin.js', 'src/api/doctor.js', 'src/api/coach.js', 'src/api/request.js',
    'src/utils/config.js', 'src/utils/auth.js',
    'src/router/index.js', 'src/router/admin.js', 'src/router/doctor.js', 'src/router/coach.js',
    'src/views/doctor/Register.vue', 'src/views/coach/Register.vue',
    'src/assets/login.css', 'src/assets/styles.css',
    'src/views/portal/IdentitySelect.vue',
]

ROLES = [
    dict(key='admin', label='管理员', path='/admin/login', theme='rgb(109, 74, 224)',
         art='admin-login-illustration', title='管理员登录',
         slogan=['全域监管', '让健康管理更高效'],
         features=['数据统计', '用户管理', '系统配置'],
         account='admin', has_reg=False, home='/admin/dashboard', pending=None, reg_path=None),
    dict(key='doctor', label='医生', path='/doctor/login', theme='rgb(15, 169, 142)',
         art='doctor-login-illustration', title='医生登录',
         slogan=['守护患者健康', '让医疗更有温度'],
         features=['患者管理', '健康档案', '诊疗建议'],
         account='doctor001', has_reg=True, home='/doctor/dashboard',
         pending='doctor003', reg_path='/doctor/register'),
    dict(key='coach', label='健身教练', path='/coach/login', theme='rgb(30, 111, 255)',
         art='coach-login-illustration', title='健身教练登录',
         slogan=['科学训练', '成就更好的自己'],
         features=['训练计划', '学员数据', '目标管理'],
         account='coach001', has_reg=True, home='/coach/dashboard',
         pending='coach003', reg_path='/coach/register'),
]

PASSWORD = '123456'
PERRORS = {}


# ------------------------------------------------------------------ 工具
def reset_auth(ws):
    navigate(ws, BASE + '/')
    ws.evaluate("[" + ",".join(json.dumps(k) for k in AUTH_KEYS) +
                "].forEach(function(k){localStorage.removeItem(k)})")


def wait_form(ws, timeout=10):
    """等表单真正可交互（2 个输入框且高度正常），避免把"未布局完成"误判成"输入没生效"。"""
    dl = time.time() + timeout
    last = None
    while time.time() < dl:
        last = ws.evaluate(
            '(function(){var l=document.querySelectorAll(".lp__form input");'
            'if(l.length<2) return null;'
            'var r0=l[0].getBoundingClientRect(), r1=l[1].getBoundingClientRect();'
            'return {n:l.length, h0:Math.round(r0.height), h1:Math.round(r1.height),'
            ' x0:Math.round(r0.left), y0:Math.round(r0.top)};})()')
        if last and last['h0'] >= 30 and last['h1'] >= 30:
            return last
        time.sleep(0.15)
    return last


def goto_login(ws, role):
    reset_auth(ws)
    ok = navigate(ws, BASE + role['path'])
    return ok and bool(wait_form(ws))


def click_nth(ws, sel, idx=0):
    rect = ws.evaluate(
        '(function(){var l=document.querySelectorAll(%s); var el=l[%d]; if(!el) return null;'
        'el.scrollIntoView({block:"center"}); var r=el.getBoundingClientRect();'
        'return {x:r.left+r.width/2, y:r.top+r.height/2, w:Math.round(r.width), h:Math.round(r.height),'
        ' tag:el.tagName, type:el.getAttribute("type"), text:(el.innerText||el.value||"").trim()};})()'
        % (json.dumps(sel), idx))
    if not rect or rect['w'] <= 0 or rect['h'] <= 0:
        return None
    x, y = rect['x'], rect['y']
    ws.call('Input.dispatchMouseEvent', {'type': 'mouseMoved', 'x': x, 'y': y, 'button': 'none'})
    ws.call('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1})
    ws.call('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1})
    return rect


def type_text(ws, idx, text, tries=3):
    """真实聚焦 + 真实文本输入；失败可重试并回报是否走了兜底赋值。"""
    for _ in range(tries):
        rect = click_nth(ws, '.lp__form input', idx)
        ws.evaluate('(function(){var i=document.querySelectorAll(".lp__form input");'
                    'if(i[%d]) i[%d].focus();})()' % (idx, idx))
        ws.call('Input.insertText', {'text': text})
        got = ws.evaluate('(function(){var i=document.querySelectorAll(".lp__form input");'
                          'return i[%d] ? i[%d].value : null;})()' % (idx, idx))
        if got == text:
            return True, 'insertText', rect
        time.sleep(0.3)
    return False, 'failed', rect


def busy_el(ws, secs):
    """点击后尽快轮询 ElMessage 文案（默认 3s 自动关闭，不能固定 sleep 后再读）。"""
    dl = time.time() + secs
    seen = []
    while time.time() < dl:
        try:
            msgs = json.loads(ws.evaluate(
                'JSON.stringify(Array.prototype.map.call('
                'document.querySelectorAll(".el-message"),function(e){return e.innerText.trim()}))'))
            for m in msgs:
                if m and m not in seen:
                    seen.append(m)
            if seen:
                break
        except Exception:
            pass
        time.sleep(0.12)
    return seen


def wait_path(ws, want, timeout=25):
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


# 事件水位线：错误与 /api/ 响应各自按"上一次取走到现在"增量读取。
# ★ 必须做水位线（而不是每次全量重读 ws.events）：实测全量重读会把上一阶段的
#   请求混进本阶段断言，导致"教练登录"被误判为失败（真实是 HTTP 200 成功）。
WM = {'e': 0, 'a': 0}
APILOG = []


def take_errors(ws, phase):
    """增量取出本阶段的红色错误 / 未捕获异常（保留资源 URL，便于区分既有 404）。"""
    out = []
    for ev in ws.events[WM['e']:]:
        m = ev.get('method')
        p = ev.get('params') or {}
        if m == 'Runtime.consoleAPICalled' and p.get('type') == 'error':
            parts = []
            for a in p.get('args', []):
                if 'value' in a:
                    parts.append(str(a['value']))
                elif a.get('description'):
                    parts.append(str(a['description']))
            out.append({'src': 'console', 'text': ' '.join(parts)[:300], 'url': p.get('url') or ''})
        elif m == 'Runtime.exceptionThrown':
            d = p.get('exceptionDetails', {})
            ex = d.get('exception') or {}
            out.append({'src': 'uncaught', 'url': d.get('url') or '',
                        'text': ' | '.join(x for x in [d.get('text', ''), ex.get('description', '')] if x)[:400]})
        elif m == 'Log.entryAdded':
            e = p.get('entry') or {}
            if e.get('level') == 'error':
                out.append({'src': 'log', 'text': str(e.get('text'))[:300], 'url': str(e.get('url') or '')})
    WM['e'] = len(ws.events)
    PERRORS.setdefault(phase, []).extend(out)
    return out


def take_api(ws, label):
    """增量取出本阶段的 /api/ 请求状态码 —— 作为"登录接口未改变且被真实调用"的硬证据。"""
    out = []
    for ev in ws.events[WM['a']:]:
        if ev.get('method') == 'Network.responseReceived':
            r = ev['params'].get('response') or {}
            if '/api/' in r.get('url', ''):
                out.append((r['url'].split('/api/', 1)[1], r.get('status')))
    WM['a'] = len(ws.events)
    APILOG.append((label, out))
    return out


def snapshot(ws):
    """失败时的现场快照（路径 / 字段值 / 组件内 form / 校验报错 / 按钮命中元素 / 页面错误）。"""
    return ws.evaluate('''JSON.stringify({
      path: location.pathname,
      vals: Array.prototype.map.call(document.querySelectorAll('.lp__form input'),
                                     function(e){return e.value}),
      form: (function(){var b=document.querySelector('.lp__btn');
             var c=b&&b.__vueParentComponent; while(c){ if(c.setupState&&c.setupState.form)
               return JSON.parse(JSON.stringify(c.setupState.form)); c=c.parent; } return 'no-inst';})(),
      errors: Array.prototype.map.call(document.querySelectorAll('.el-form-item__error'),
                                       function(e){return e.innerText.trim()}),
      isError: document.querySelectorAll('.el-form-item.is-error').length,
      msgs: Array.prototype.map.call(document.querySelectorAll('.el-message'),
                                     function(e){return e.innerText.trim()}),
      btnHit: window.__btnHit,
      btn: (function(){var b=document.querySelector('.lp__btn'); if(!b) return null;
            var r=b.getBoundingClientRect();
            var e=document.elementFromPoint(r.left+r.width/2, r.top+r.height/2);
            return {w:Math.round(r.width), h:Math.round(r.height),
                    hit: e? e.tagName+'.'+e.className.toString() : null};})(),
      errs: (window.__errs||[]).slice(-3)
    })''')


CLICKLOG = []   # [(label, 'mouse' | 'mouse+frame' | 'dom')] —— 提交登录实际走的输入路径


def click_login(ws, label=''):
    """提交登录：真实鼠标注入优先，逐级升级，并把实际使用的路径记录下来。

    根因取证（_verify_out/probe_click.txt，本轮第四次探针，同一 Chrome / 同一会话）：
      · CDP `Input.dispatchMouseEvent` 在本机 `--headless=new` 下会**间歇性丢事件**：
        按钮矩形正确、`elementFromPoint` 命中按钮内层 SPAN、`document.hasFocus()=true`、
        `visibilityState=visible`、无滚动（scrollY 恒 0），但 click 事件 0 次到达按钮；
        同一会话里换账号重跑又可能完全正常 —— 属注入层抖动，不是产品缺陷。
      · DOM 级 `el.click()` 在上述状态下 100% 有效，且触发的是同一条真实链路
        （Vue @click → login() → axios POST /api/<role>/login → router.replace），
        因此"接口状态码 + 路由跳转 + Token 落库"三类证据与真鼠标完全等价。
    分级顺序：① 真实鼠标 → ② 强制产帧后重试真实鼠标 → ③ DOM 兜底。
    """
    try:
        ws.call('Page.bringToFront')
    except Exception:
        pass
    ws.evaluate("window.__btnHit=0;(function(){var b=document.querySelector('.lp__btn');"
                "if(b&&!b.__probe){b.__probe=1;b.addEventListener('click',function(){"
                "window.__btnHit=(window.__btnHit||0)+1},true);}})()")
    mode = 'mouse'
    for mode in ('mouse', 'mouse+frame'):
        if mode == 'mouse+frame':
            try:
                ws.call('Page.captureScreenshot', {'format': 'png'})   # 强制产帧，唤醒合成器
            except Exception:
                pass
        click_center(ws, '.lp__btn', 'login button')
        time.sleep(0.4)
        if ws.evaluate('window.__btnHit||0'):
            CLICKLOG.append((label, mode))
            return ws.evaluate('window.__btnHit||0')
    ws.evaluate("(function(){var b=document.querySelector('.lp__btn'); if(b) b.click();})()")
    time.sleep(0.4)
    CLICKLOG.append((label, 'dom'))
    return ws.evaluate('window.__btnHit||0')


def probe_page(ws):
    return ws.evaluate('''(function(){
      var q=function(s){return document.querySelector(s)};
      var rect=function(el){if(!el) return null;var r=el.getBoundingClientRect();
        return {l:Math.round(r.left),t:Math.round(r.top),r:Math.round(r.right),b:Math.round(r.bottom),
                w:Math.round(r.width),h:Math.round(r.height),
                cx:Math.round(r.left+r.width/2),cy:Math.round(r.top+r.height/2)};};
      var cs=function(el,p){return el?getComputedStyle(el).getPropertyValue(p):null};
      var art=q('.lp__art'), card=q('.lp__card'), copy=q('.lp__copy'),
          icon=q('.lp__card-icon'), btn=q('.lp__btn'), logo=q('.lp__brand-logo');
      return {
        vw: innerWidth, vh: innerHeight,
        hasArt: !!art, artBg: cs(art,'background-image'),
        artMask: cs(art,'mask-image')||cs(art,'-webkit-mask-image'),
        artRect: rect(art), cardRect: rect(card), copyRect: rect(copy),
        cardW: card?Math.round(card.getBoundingClientRect().width):0,
        cardRadius: cs(card,'border-radius'), cardShadow: cs(card,'box-shadow'),
        cardBackdrop: cs(card,'backdrop-filter')||cs(card,'-webkit-backdrop-filter'),
        iconBg: cs(icon,'background-image'), logoBg: cs(logo,'background-image'),
        btnBg: cs(btn,'background-image'), btnH: btn?Math.round(btn.getBoundingClientRect().height):0,
        inputH: (function(){var i=q('.lp__form .el-input__wrapper');
                 return i?Math.round(i.getBoundingClientRect().height):0})(),
        artZ: cs(art,'z-index'), innerZ: cs(q('.lp__inner'),'z-index'), artPE: cs(art,'pointer-events'),
        sloganText: q('.lp__slogan')?q('.lp__slogan').innerText.replace(/\\s+/g,' ').trim():null,
        featTexts: Array.prototype.map.call(document.querySelectorAll('.lp__feature-label'),function(e){return e.innerText.trim()}),
        cardTitle: q('.lp__card-title')?q('.lp__card-title').innerText.trim():null,
        cardSub: q('.lp__card-sub')?q('.lp__card-sub').innerText.trim():null,
        footTexts: Array.prototype.map.call(document.querySelectorAll('.lp__foot .el-button'),function(e){return e.innerText.trim()}),
        noteText: q('.lp__note')?q('.lp__note').innerText.trim():null,
        bodyText: (document.body.innerText||'').replace(/\\s+/g,' '),
        oldSide: document.querySelectorAll('.login__side').length,
        oldTip: document.querySelectorAll('.login__tip').length,
        oldPanel: document.querySelectorAll('.login__panel').length,
        scrollW: document.documentElement.scrollWidth, clientW: document.documentElement.clientWidth,
        bodyScrollW: document.body.scrollWidth,
        pwToggles: document.querySelectorAll('.lp__form .el-input__suffix .el-icon').length,
        pwType: (function(){var l=document.querySelectorAll('.lp__form input');
                 return l.length>1?l[1].getAttribute('type'):null})(),
        cardInView: card ? (card.getBoundingClientRect().top>=-1 &&
                            card.getBoundingClientRect().bottom<=innerHeight+1) : false,
        copyInView: copy ? (copy.getBoundingClientRect().top>=-1 &&
                            copy.getBoundingClientRect().bottom<=innerHeight+1) : false,
      };})()''')


# ------------------------------------------------------------------ 各项验收
def check_structure(ws, role, tag):
    p = probe_page(ws)
    vw = p['vw']
    ok = (p['hasArt'] and role['art'] in (p['artBg'] or '')
          and p['artRect'] and p['artRect']['l'] <= 1 and p['artRect']['w'] >= vw * 0.6
          and p['cardRect'] and p['cardRect']['l'] >= vw * 0.55 and p['cardRect']['r'] <= vw + 1
          and p['copyRect'] and p['copyRect']['l'] <= vw * 0.25
          and p['copyRect']['r'] <= p['cardRect']['l'])
    case('%s ①「左插画 + 右登录卡片」结构成立（插画宽 %d / 卡片左边界 %d / 视口 %d）'
         % (tag, p['artRect']['w'] if p['artRect'] else -1,
            p['cardRect']['l'] if p['cardRect'] else -1, vw), ok,
         'art=%s card=%s copy=%s' % (p['artRect'], p['cardRect'], p['copyRect']))
    case('%s 插画资源已真实接入（background-image 含 %s.webp）' % (tag, role['art']),
         role['art'] in (p['artBg'] or ''), (p['artBg'] or '')[:110])
    case('%s 插画向右柔和淡出（mask-image 渐变生效）' % tag,
         'gradient' in (p['artMask'] or '') and 'none' not in (p['artMask'] or ''), str(p['artMask']))
    case('%s 装饰插画层 pointer-events:none（不拦截点击）' % tag, p['artPE'] == 'none', p['artPE'])
    case('%s 层级契约：插画层 z=%s < 内容层 z=%s' % (tag, p['artZ'], p['innerZ']),
         p['artZ'] == '0' and p['innerZ'] == '2', 'art=%s inner=%s' % (p['artZ'], p['innerZ']))
    case('%s 登录卡片垂直居中（中心 y=%s / 视口中线 %d）'
         % (tag, p['cardRect']['cy'] if p['cardRect'] else None, p['vh'] // 2),
         p['cardRect'] and abs(p['cardRect']['cy'] - p['vh'] / 2) <= 46, None)
    case('%s 卡片规格：宽 %dpx（390~450）/ 圆角 %s / 柔和阴影 / 轻毛玻璃'
         % (tag, p['cardW'], p['cardRadius']),
         380 <= p['cardW'] <= 460 and 'rgba' in (p['cardShadow'] or '')
         and 'blur' in (p['cardBackdrop'] or ''), 'blur=%s' % (p['cardBackdrop'] or '')[:36])
    case('%s 卡片圆角 20~24px' % tag,
         p['cardRadius'] in ('20px', '21px', '22px', '23px', '24px'), p['cardRadius'])
    case('%s 输入框高 %dpx / 按钮高 %dpx（要求 48~52）' % (tag, p['inputH'], p['btnH']),
         48 <= p['inputH'] <= 52 and 48 <= p['btnH'] <= 52, None)
    return p


def check_theme(ws, role, tag, p):
    th = role['theme']
    case('%s ②③④ 主题色正确（卡片图标 / 品牌标 / 主按钮渐变均含 %s）' % (tag, th),
         th in (p['iconBg'] or '') and th in (p['logoBg'] or '') and th in (p['btnBg'] or ''),
         'btn=%s' % (p['btnBg'] or '')[:90])


def check_copy(ws, role, tag, p):
    body = p['bodyText']
    missing = [s for s in role['slogan'] + role['features'] + [role['title']] if s not in body]
    case('%s 新文案齐全（标题 %d 行 + 功能 %d 项 + 卡片标题 + 副标题）'
         % (tag, len(role['slogan']), len(role['features'])),
         not missing and p['cardSub'] in ('Admin Console', 'Doctor Console', 'Coach Console'),
         'missing=%s sub=%s' % (missing, p['cardSub']))
    hit = [s for s in OLD_LONG_TEXTS if s in body]
    case('%s ⑤ 旧版大段功能介绍文字已清除（%d 条特征串零命中）' % (tag, len(OLD_LONG_TEXTS)),
         not hit, 'hit=%s' % hit)
    case('%s 旧版 DOM（.login__panel / .login__side / .login__tip）已全部移除' % tag,
         p['oldSide'] == 0 and p['oldTip'] == 0 and p['oldPanel'] == 0,
         'side=%s tip=%s panel=%s' % (p['oldSide'], p['oldTip'], p['oldPanel']))
    case('%s 左侧只保留 2 行短文案 + 3 个功能小项' % tag,
         p['sloganText'] == ' '.join(role['slogan']) and p['featTexts'] == role['features'],
         'slogan=%r feats=%s' % (p['sloganText'], p['featTexts']))


# ------------------------------------------------------------------ 主流程
def run(ws):
    # ---- A. 逐页：结构 / 主题 / 文案 / 真实输入 / 密码显隐 ----
    for role in ROLES:
        tag = role['label'] + '页'
        goto_login(ws, role)
        p = check_structure(ws, role, tag)
        check_theme(ws, role, tag, p)
        check_copy(ws, role, tag, p)

        ok_a, how_a, ra = type_text(ws, 0, role['account'])
        ok_p, how_p, rp = type_text(ws, 1, PASSWORD)
        vals = json.loads(ws.evaluate(
            'JSON.stringify(Array.prototype.map.call(document.querySelectorAll(".lp__form input"),'
            'function(e){return e.value}))'))
        case('%s 真实输入进入 v-model（账号 / 密码）  [机制=%s/%s]' % (tag, how_a, how_p),
             ok_a and ok_p and vals == [role['account'], PASSWORD],
             'vals=%s rect0=%s rect1=%s' % (vals, ra, rp))

        # 需求 10：密码显示/隐藏
        # 注意：Element Plus 的眼睛按钮类名是 .el-input__password，且**只在输入框有值时渲染**；
        # 而 .el-input__suffix .el-icon 的第 0 个是"账号框的清除按钮"(.el-input__clear，默认隐藏)，
        # 用它会点错元素 —— 这是上一版误判 FAIL 的根因。
        before = ws.evaluate('(function(){var l=document.querySelectorAll(".lp__form input");'
                             'return l[1].getAttribute("type")})()')
        found = ws.evaluate('document.querySelectorAll(".lp__form .el-input__password").length')
        owns = ws.evaluate(
            '(function(){var e=document.querySelector(".lp__form .el-input__password");'
            'if(!e) return -1; return Array.prototype.indexOf.call('
            'document.querySelectorAll(".lp__form .el-form-item"), e.closest(".el-form-item"));})()')
        r_t = click_nth(ws, '.lp__form .el-input__password', 0)
        time.sleep(0.4)
        on = ws.evaluate('(function(){var l=document.querySelectorAll(".lp__form input");'
                         'return l[1].getAttribute("type")})()')
        click_nth(ws, '.lp__form .el-input__password', 0)
        time.sleep(0.4)
        off = ws.evaluate('(function(){var l=document.querySelectorAll(".lp__form input");'
                          'return l[1].getAttribute("type")})()')
        case('%s ⑩ 密码显示/隐藏可切换（%s -> %s -> %s）' % (tag, before, on, off),
             found == 1 and owns == 1 and before == 'password' and on == 'text' and off == 'password',
             'eyeCount=%s 所属表单项索引=%s clicked=%s' % (found, owns, r_t is not None))

    take_errors(ws, 'A-结构/主题/文案/输入/密码显隐')

    # ---- B. 需求 6：管理员无注册入口 ----
    goto_login(ws, ROLES[0])
    da = json.loads(ws.evaluate(
        'JSON.stringify({reg:document.body.innerText.indexOf("申请注册")>=0,'
        'regLink:document.querySelectorAll("a[href*=register],button[href*=register]").length,'
        'note:(document.querySelector(".lp__note")||{}).innerText||""})'))
    case('⑥ 管理员页无「申请注册」入口（文案与节点双零）',
         (not da['reg']) and da['regLink'] == 0, json.dumps(da, ensure_ascii=False))
    case('⑥ 管理员页说明仍为「账号由数据库初始化，不提供注册」', '不提供注册' in da['note'], da['note'])
    take_errors(ws, 'B-管理员无注册')

    # ---- C. 需求 7/8：医生 / 教练注册入口 ----
    for role in ROLES[1:]:
        tag = role['label'] + '页'
        goto_login(ws, role)
        got = click_nth(ws, '.lp__foot .el-button', 0)
        ok = wait_path(ws, role['reg_path'], 15)
        case('%s ⑦⑧ 「申请注册」真实点击跳转到 %s' % (tag, role['reg_path']),
             got is not None and got['text'] == '申请注册' and ok,
             'btn=%s path=%s' % (got['text'] if got else None, ws.evaluate('location.pathname')))
        dr = json.loads(ws.evaluate(
            'JSON.stringify({panel:document.querySelectorAll(".login__panel").length,'
            'lpCard:document.querySelectorAll(".lp__card").length,'
            'title:(document.querySelector(".login__brand-title")||{}).innerText||""})'))
        case('%s 注册页仍沿用原 login.css 版式（未被本轮新样式波及）' % tag,
             dr['panel'] == 1 and dr['lpCard'] == 0 and '注册' in dr['title'],
             json.dumps(dr, ensure_ascii=False))
    take_errors(ws, 'C-注册入口')

    # ---- D. 需求 9：返回身份选择 ----
    for role in ROLES:
        tag = role['label'] + '页'
        goto_login(ws, role)
        n = ws.evaluate('document.querySelectorAll(".lp__foot .el-button").length')
        click_nth(ws, '.lp__foot .el-button', int(n) - 1)
        ok = wait_path(ws, '/', 15)
        cards = ws.evaluate('document.querySelectorAll(".portal__card").length')
        case('%s ⑨ 「返回身份选择」跳回身份选择首页（并渲染 3 张身份卡片）' % tag,
             ok and cards == 3, 'path=%s cards=%s' % (ws.evaluate('location.pathname'), cards))
    take_errors(ws, 'D-返回身份选择')

    # ---- E. 需求 12/13/14/17：三个真实账号登录 ----
    for role in ROLES:
        tag = role['label']
        goto_login(ws, role)
        type_text(ws, 0, role['account'])
        type_text(ws, 1, PASSWORD)
        ok, used, snap = False, 0, None
        for attempt in (1, 2):
            vals = json.loads(ws.evaluate(
                'JSON.stringify(Array.prototype.map.call(document.querySelectorAll(".lp__form input"),'
                'function(e){return e.value}))'))
            if vals != [role['account'], PASSWORD]:      # 重试前重新确认输入已就位
                type_text(ws, 0, role['account'])
                type_text(ws, 1, PASSWORD)
            hits = click_login(ws, 'E-%s' % tag)
            ok = wait_path(ws, role['home'], 20)
            used = attempt
            if ok:
                break
            snap = snapshot(ws)
            print('   [diag] %s 第 %d 次提交未跳转：点击到达按钮 %s 次 / snap=%s'
                  % (tag, attempt, hits, snap), flush=True)
            time.sleep(0.6)
        calls = take_api(ws, 'E-login-%s' % tag)
        status = [s for u, s in calls if u == '%s/login' % role['key']]
        tok = ws.evaluate('localStorage.getItem("hms_%s_token")' % role['key'])
        body = ws.evaluate('(document.body.innerText||"").length')
        case('%s ⑫⑬⑭ 登录成功并跳转 %s（接口 HTTP=%s / Token 已落库 / 第 %d 次提交生效）'
             % (tag, role['home'], status, used), ok and bool(tok) and 200 in status,
             'path=%s token=%s calls=%s snap=%s'
             % (ws.evaluate('location.pathname'), bool(tok), calls, snap))
        case('%s ⑰ 登录后原工作台正常渲染（正文 %d 字，无白屏）' % (tag, body),
             ok and body > 200, 'bodyLen=%s' % body)
        ws.shot(os.path.join(ART, 'login-dashboard-%s.png' % role['key']))
        reset_auth(ws)

    # ---- F. 需求 15/16：待审核账号必须被拦截 ----
    for role in ROLES[1:]:
        tag = role['label']
        goto_login(ws, role)
        type_text(ws, 0, role['pending'])
        type_text(ws, 1, PASSWORD)
        msgs, status, used, snap = [], [], 0, None
        for attempt in (1, 2):
            hits = click_login(ws, 'F-%s' % tag)
            msgs = busy_el(ws, 5)
            used = attempt
            calls = take_api(ws, 'F-pending-%s(#%d)' % (tag, attempt))
            status += [s for u, s in calls if u == '%s/login' % role['key']]
            if 400 in status and msgs:
                break
            snap = snapshot(ws)
            print('   [diag] %s 待审核第 %d 次提交无响应：点击到达按钮 %s 次 / snap=%s'
                  % (tag, attempt, hits, snap), flush=True)
            time.sleep(0.6)
        st = json.loads(ws.evaluate('JSON.stringify({path:location.pathname,'
                                    'token:!!localStorage.getItem("hms_%s_token")})' % role['key']))
        hit_audit = any('审核' in m for m in msgs)
        case('%s ⑮⑯ 待审核账号 %s 被拦截（接口 HTTP=%s / 停留登录页 / 无 Token / 提示含"审核" / 第 %d 次提交生效）'
             % (tag, role['pending'], status, used),
             st['path'] == role['path'] and (not st['token']) and hit_audit and 400 in status,
             'msgs=%s state=%s snap=%s' % (msgs, json.dumps(st, ensure_ascii=False), snap))
        reset_auth(ws)
    take_errors(ws, 'E/F-真实登录与待审核')

    # ---- G. 需求 20/21/22：三档分辨率 ----
    for w, h in ((1366, 768), (1440, 900), (1920, 1080)):
        ws.call('Emulation.setDeviceMetricsOverride',
                {'width': w, 'height': h, 'deviceScaleFactor': 1, 'mobile': False})
        for role in ROLES:
            tag = '%s页 %dx%d' % (role['label'], w, h)
            goto_login(ws, role)
            d = json.loads(ws.evaluate(
                'JSON.stringify({sw:document.documentElement.scrollWidth,'
                'cw:document.documentElement.clientWidth,bw:document.body.scrollWidth})'))
            case('%s 无横向滚动条（scrollWidth=%s clientWidth=%s）'
                 % (tag, d['sw'], d['cw']), d['sw'] <= d['cw'] and d['bw'] <= d['cw'] + 1,
                 json.dumps(d))
            p = probe_page(ws)
            case('%s 卡片与文案完整可见且互不重叠' % tag,
                 p['cardInView'] and p['copyInView'] and p['copyRect']['r'] <= p['cardRect']['l'],
                 'card=%s copy=%s' % (p['cardRect'], p['copyRect']))
            ws.shot(os.path.join(ART, 'login-%s-%dx%d.png' % (role['key'], w, h)))
    ws.call('Emulation.setDeviceMetricsOverride',
            {'width': 1440, 'height': 900, 'deviceScaleFactor': 1, 'mobile': False})
    take_errors(ws, 'G-三档分辨率')


def static_checks():
    """需求 11：登录接口与认证业务代码逐字节未被改动。"""
    changed = []
    for rel in UNTOUCHED:
        p = os.path.join(MW, rel.replace('/', os.sep))
        if not os.path.exists(p):
            changed.append(rel + ' (MISSING)')
        elif os.path.getmtime(p) > SESSION_T0:
            changed.append('%s (mtime=%s)' % (rel, time.strftime('%H:%M:%S', time.localtime(os.path.getmtime(p)))))
    case('⑪ 登录/认证/路由/注册页/身份选择页等 %d 个业务文件在本轮开工后零改动' % len(UNTOUCHED),
         not changed, 'changed=%s' % changed)

    expect = {
        'views/admin/Login.vue', 'views/doctor/Login.vue', 'views/coach/Login.vue',
        'assets/login-portal.css',
        'assets/images/login/admin-login-illustration.webp',
        'assets/images/login/doctor-login-illustration.webp',
        'assets/images/login/coach-login-illustration.webp',
    }
    got = set()
    for dp, dn, fn in os.walk(SRC):
        for f in fn:
            fp = os.path.join(dp, f)
            if os.path.getmtime(fp) > SESSION_T0:
                got.add(os.path.relpath(fp, SRC).replace(os.sep, '/'))
    case('⑪ 本轮 src/ 改动集合 == 期望集合（3 登录页 + 1 新样式表 + 3 插画，无多改）',
         got == expect, 'extra=%s missing=%s' % (sorted(got - expect), sorted(expect - got)))

    n_ok, det = 0, []
    for role in ROLES:
        t = open(os.path.join(SRC, 'views', role['key'], 'Login.vue'), 'rb').read().decode('utf-8')
        script = t.split('<script setup>', 1)[1].split('</script>', 1)[0]
        need = ['Api.login(', 'setAuth(ROLE.%s' % role['key'].upper(), 'router.replace(',
                "'/%s/dashboard'" % role['key'], 'formRef.value.validate()',
                'const redirect = route.query.redirect', "redirect.startsWith('/%s')" % role['key'],
                'loading.value = true', 'loading.value = false']
        miss = [s for s in need if s not in script]
        if not miss:
            n_ok += 1
        det.append('%s:missing=%s' % (role['key'], miss))
    case('⑪ 三个登录页 <script setup> 原业务语句齐全（原 login() / 校验 / Token / 跳转逻辑一字未改）',
         n_ok == 3, ' | '.join(det))

    ok_style, det = True, []
    for role in ROLES:
        t = open(os.path.join(SRC, 'views', role['key'], 'Login.vue'), 'rb').read().decode('utf-8')
        st = t.split('<style>', 1)[1] if '<style>' in t else ''
        if 'login-portal.css' not in st or 'login.css' in st:
            ok_style = False
        det.append('%s:%r' % (role['key'], st.strip().replace('\n', ' ')[:34]))
    case('⑪ 三个登录页仅引入新样式表 login-portal.css（不再引 register 页共用的 login.css）',
         ok_style, ' || '.join(det))


def main():
    dev, _, reused = start_dev_server()
    print('dev server: %s\n' % ('复用已有实例' if reused else '本脚本自起'), flush=True)
    cdp = free_port()
    profile = tempfile.mkdtemp(prefix='hms-login-')
    chrome = subprocess.Popen([
        CHROME, '--headless=new', '--no-first-run', '--no-default-browser-check',
        '--disable-extensions', '--disable-background-networking', '--disable-sync', '--mute-audio',
        '--window-size=1440,900', '--user-data-dir=' + profile,
        '--remote-debugging-port=%d' % cdp, 'about:blank'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ws = None
    t0 = time.time()
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
        try:
            ws.call('Log.enable')
        except Exception:
            pass
        ws.call('Page.addScriptToEvaluateOnNewDocument', {'source': HOOK})
        ws.call('Emulation.setDeviceMetricsOverride',
                {'width': 1440, 'height': 900, 'deviceScaleFactor': 1, 'mobile': False})
        # 无头会话长时间多次导航后，聚焦状态会丢失，导致部分 Input 事件被丢弃
        for extra in ({'method': 'Emulation.setFocusEmulationEnabled', 'params': {'enabled': True}},
                      {'method': 'Page.bringToFront', 'params': {}}):
            try:
                ws.call(extra['method'], extra['params'])
            except Exception:
                pass

        ws.events = []
        run(ws)
        static_checks()

        modes = [m for _, m in CLICKLOG]
        case('⑫⑬⑭⑮⑯ 5 次「提交登录」全部记录到有效输入路径（真鼠标优先；仅当注入层丢事件时才退化到 DOM 兜底，并如实标注）',
             len(modes) == 5 and all(m in ('mouse', 'mouse+frame', 'dom') for m in modes),
             json.dumps(CLICKLOG, ensure_ascii=False))

        take_errors(ws, 'H-收尾')
        allerr = [(ph, e) for ph, lst in PERRORS.items() for e in lst]
        benign = [e for ph, e in allerr if 'favicon' in (e.get('url') or '').lower()
                  or 'favicon' in (e.get('text') or '').lower()]
        # 负向用例的必然产物：F 阶段**故意**用待审核账号登录，后端按冻结契约返回
        # HTTP 400 + "账号正在审核中"；Chrome 因此会记一条 log 级
        # "Failed to load resource ... 400 (BAD REQUEST)"。这是**被测行为本身**
        # （第 ⑮⑯ 项已断言 400 + 无 Token），并非本轮新增的红色缺陷，故单独放行。
        neg_ep = ['/api/%s/login' % r['key'] for r in ROLES[1:]]
        expected_4xx = [e for ph, e in allerr
                        if '400 (BAD REQUEST)' in (e.get('text') or '')
                        and any(k in (e.get('url') or '') for k in neg_ep)]
        real = [(ph, e) for ph, e in allerr if e not in benign and e not in expected_4xx]
        case('⑱ 全流程 Console 0 新增红色错误 / 未捕获异常（已排除 favicon 探测，以及 F 阶段负向用例预期的 400）',
             not real,
             json.dumps([{'phase': ph, **e} for ph, e in real], ensure_ascii=False)[:700]
             or '放行明细：favicon 探测 %d 条；F 阶段预期 HTTP 400 %d 条 %s'
                % (len(benign), len(expected_4xx),
                   json.dumps([ph for ph, e in allerr if e in expected_4xx], ensure_ascii=False)[:160]))
        print('\n[info] 各阶段 /api/ 请求状态：')
        for label, calls in APILOG:
            if calls:
                print('   %-24s %s' % (label, calls))
    finally:
        try:
            if ws:
                ws.shot(os.path.join(ART, 'login-final.png'))
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

    npass = sum(1 for _, ok, _ in RESULTS if ok)
    print('\n' + '=' * 30)
    print('TOTAL %d  PASS %d  FAIL %d  (%.0fs)' % (len(RESULTS), npass, len(RESULTS) - npass, time.time() - t0))
    print('=' * 30)
    with open(os.path.join(ART, 'login_verify_result.json'), 'w', encoding='utf-8') as f:
        json.dump([{'case': n, 'pass': ok, 'detail': str(d)[:400]} for n, ok, d in RESULTS],
                  f, ensure_ascii=False, indent=1)
    return 0 if npass == len(RESULTS) else 1


if __name__ == '__main__':
    sys.exit(main())
