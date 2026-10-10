# -*- coding: utf-8 -*-
"""给 _verify_anim.py 追加针对"装饰层溢出导致滚动条闪烁"的回归断言（锚点各恰 1 次）。"""
import os
import sys

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_verify_anim.py')

OLD_SOAK = """        print('   [info] 开始 %ds 长跑（含布局漂移 / 长任务 / 错误 / 帧率监控）...' % SOAK_SECONDS, flush=True)
        soak0 = anchors()
        ws.evaluate('window.__lt=[]; window.__cls=0; window.__frames=0; window.__fps=0')
        snapshots = []
        dl = time.time() + SOAK_SECONDS
        n = 0
        while time.time() < dl:
            time.sleep(5)
            ws.shot(None)     # 每 5s 强制产帧，贴近真实渲染节奏
            n += 1
            s = ws.evaluate('({sw:document.documentElement.scrollWidth, cw:document.documentElement.clientWidth,'
                            ' fps:window.__fps||0, lt:(window.__lt||[]).length})')
            snapshots.append(s)
            print('   [soak %2ds] %s' % (n * 5, json.dumps(s)), flush=True)"""

NEW_SOAK = """        print('   [info] 开始 %ds 长跑（内容漂移 / 滚动条稳定性 / 长任务 / 重排重绘 / 错误）...'
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
              'max(scrollHeight-innerHeight)=%s' % (d_layout, d_style, cws, max(overs)), flush=True)"""

OLD_CASES = """        case('⑫ 60s 长跑后内容层位置零漂移（无布局漂移）', not drift_soak, 'drift=%s' % drift_soak)"""

NEW_CASES = """        case('⑫ 60s 长跑后内容层位置零漂移（无布局漂移）', not drift_soak,
             'drift=%s clientWidth=%s' % (drift_soak, cws))
        case('⑫ 60s 长跑期间视口宽度恒定（无滚动条闪烁 -> 内容不横移）', len(cws) == 1,
             'clientWidth 取值集合=%s（含滚动条时应为 1351，无滚动条 1366）' % cws)
        case('⑫ 60s 长跑期间文档无可滚动溢出（装饰层缩放未撑高页面）', max(overs) <= 0,
             'max(scrollHeight-innerHeight)=%s' % max(overs))
        case('⑫ 背景动画只走合成层：60s 内 LayoutCount 增量≈0（不触发重排）', d_layout <= 5,
             'dLayout=%s（若逐帧重排会是数千）' % d_layout)
        case('⑫ 背景动画只走合成层：60s 内 RecalcStyleCount 增量≈0（不触发重算样式）', d_style <= 5,
             'dStyle=%s' % d_style)"""

OLD_SHOT = """        # 截图取证
        for w, h in [(1366, 768), (1920, 1080)]:"""

NEW_SHOT = """        # 矮视口回归：overflow:clip 不得吞掉"内容超高时仍可滚动可达"
        ws.call('Emulation.setDeviceMetricsOverride',
                {'width': 1366, 'height': 620, 'deviceScaleFactor': 1, 'mobile': False})
        time.sleep(1.0)
        short = ws.evaluate(\"\"\"
        (function(){
          var de = document.documentElement;
          window.scrollTo(0, 99999);
          var maxY = window.scrollY;
          window.scrollTo(0, 0);
          return {sh: de.scrollHeight, ih: window.innerHeight, maxY: Math.round(maxY),
                  sw: de.scrollWidth, cw: de.clientWidth,
                  cardsVisible: [].slice.call(document.querySelectorAll('.portal__card')).length};
        })()
        \"\"\")
        case('矮视口 1366x620：内容超高时页面仍可滚动到底（裁剪未吞内容）',
             short['sh'] > short['ih'] and short['maxY'] >= short['sh'] - short['ih'] - 2
             and short['cardsVisible'] == 3,
             json.dumps(short))
        case('矮视口 1366x620：仍无横向滚动', short['sw'] <= short['cw'] + 1,
             'sw=%s cw=%s' % (short['sw'], short['cw']))
        ws.call('Emulation.setDeviceMetricsOverride',
                {'width': 1366, 'height': 768, 'deviceScaleFactor': 1, 'mobile': False})
        time.sleep(0.6)

        # 截图取证
        for w, h in [(1366, 768), (1920, 1080)]:"""

PATCHES = [(OLD_SOAK, NEW_SOAK), (OLD_CASES, NEW_CASES), (OLD_SHOT, NEW_SHOT)]


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
            print('FATAL: patch %d 命中 %d 次 => 未写盘' % (i, n))
            return 2
        norm = norm.replace(old, new, 1)
    # 长跑前需要后置捕获 pm1：把 pm1 取点放在 soak1 之前
    old2 = """        soak1 = anchors()
        soak_errs = drain_errors(ws)"""
    if norm.count(old2) != 1:
        print('FATAL: soak1 锚点命中异常')
        return 2
    try:
        compile(norm, P, 'exec')
    except SyntaxError as e:
        print('FATAL: 语法错误', e)
        return 2
    with open(P, 'wb') as f:
        f.write(norm.encode('utf-8'))
    print('OK: 3 处补丁落盘，字节 %d -> %d' % (len(raw), os.path.getsize(P)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
