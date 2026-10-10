# -*- coding: utf-8 -*-
"""修正 _verify_anim.py 的 6 处缺陷（锚点各命中恰 1 次，任一未命中则不写盘）。"""
import os
import sys

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_verify_anim.py')

PATCHES = [
    # 1) dev server 启动失败时先杀掉子进程，避免占用 5173 的孤儿 node
    ("""        if p.poll() is not None:
            raise RuntimeError('vite dev server exited early (code %s)' % p.returncode)
        time.sleep(0.6)
    raise RuntimeError('vite dev server not ready in 120s')""",
     """        if p.poll() is not None:
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
    raise RuntimeError('vite dev server not ready in 120s')"""),

    # 2) ANIM_JS 增加 .portal__bg 的 backgroundImage（用于校验 CSS 风景渐变仍在）
    ("""    veilBg: cs(q('.portal__bg-veil')).backgroundImage.slice(0, 60),""",
     """    bgImage: cs(bg).backgroundImage.slice(0, 80),
    veilBg: cs(q('.portal__bg-veil')).backgroundImage.slice(0, 60),"""),

    # 3) 层级契约断言：.portal__cards 无 z-index（computed 为 auto），改为只比 fx / main
    ("""        case('层级契约成立：装饰层 z-index(2) < 内容层 z-index(3)',
             info['fxZ'] == '2' and info['wrapperZ'] == '3' and info['cardsZ'] == '3',
             'fx=%s wrapper=%s cards=%s' % (info['fxZ'], info['wrapperZ'], info['cardsZ']))""",
     """        case('层级契约成立：装饰层 z-index(2) < 内容层 z-index(3)',
             info['fxZ'] == '2' and info['wrapperZ'] == '3',
             'fx=%s main=%s (cards computed=%s)' % (info['fxZ'], info['wrapperZ'], info['cardsZ']))"""),

    # 4) "原有 CSS 风景保留"：原写法 `or True` 恒真（假断言），改为真实断言
    ("""        case('原有 CSS 风景保留（.portal__bg 渐变 + 远/近山 clip-path 均在）',
             'gradient' in info['bg']['name'] or True,
             'bgBeforeClip=%s bgAfterClip=%s' % (info['bgBeforeClip'][:24], info['bgAfterClip'][:24]))""",
     """        case('原有 CSS 风景保留（.portal__bg 风景渐变仍在）',
             'gradient' in info['bgImage'], info['bgImage'])
        case('原有山体剪影保留（远山 / 近景 clip-path 均仍在）',
             info['bgBeforeClip'] not in ('none', 'MISSING') and info['bgAfterClip'] not in ('none', 'MISSING'),
             'far=%s near=%s' % (info['bgBeforeClip'][:30], info['bgAfterClip'][:30]))"""),

    # 5) 清理 getAnimations 取证里多余的空函数
    ("""        ct = ws.evaluate(\"\"\"
        (function(){
          function t(sel,pe){ var el=document.querySelector(sel); var a=el.getAnimations(pe?{subtree:false}:undefined);
            var x = (pe ? getComputedStyle(el,pe) : null);
            return null; }
          var el=document.querySelector('.portal__cloud--1');
          var list=el.getAnimations().map(function(an){return {n:an.animationName,ct:Math.round(an.currentTime||0),st:an.playState};});
          return list;
        })()
        \"\"\")""",
     """        ct = ws.evaluate(\"\"\"
        (function(){
          var el = document.querySelector('.portal__cloud--1');
          return el.getAnimations().map(function(an){
            return {n: an.animationName, ct: Math.round(an.currentTime || 0), st: an.playState};
          });
        })()
        \"\"\")"""),

    # 6) 纯 CSS 检查：显式编码读取，且顺带核对无第三方动画库依赖
    ("""        case('实现方式为纯 CSS（无 JS 动画、无第三方动画库）',
             'requestAnimationFrame' not in open(
                 os.path.join(MW, 'src', 'views', 'portal', 'IdentitySelect.vue'),
                 'rb').read().decode('utf-8', 'replace'))""",
     """        src_txt = open(os.path.join(MW, 'src', 'views', 'portal', 'IdentitySelect.vue'),
                       'rb').read().decode('utf-8', 'replace')
        case('实现方式为纯 CSS（.vue 内无任何 JS 动画代码）',
             'requestAnimationFrame' not in src_txt and 'setInterval' not in src_txt)"""),
]


def main():
    raw = open(P, 'rb').read()
    src = raw.decode('utf-8')
    if src.count('\r\n') not in (0, src.count('\n')):
        print('FATAL: 行尾混合')
        return 2
    norm = src.replace('\r\n', '\n')
    for i, (old, new) in enumerate(PATCHES, 1):
        n = norm.count(old)
        print('patch %d hits=%d' % (i, n))
        if n != 1:
            print('FATAL: patch %d 锚点命中 %d 次 => 未写盘' % (i, n))
            return 2
        norm = norm.replace(old, new, 1)
    # 语法自检
    try:
        compile(norm, P, 'exec')
    except SyntaxError as e:
        print('FATAL: 语法错误', e)
        return 2
    with open(P, 'wb') as f:
        f.write(norm.encode('utf-8'))
    print('OK: 6 处修正已落盘，字节 %d -> %d' % (len(raw), os.path.getsize(P)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
