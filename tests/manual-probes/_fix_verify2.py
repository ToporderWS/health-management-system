# -*- coding: utf-8 -*-
"""修正 _verify_anim.py 的矮视口断言（原断言假设"必然溢出"，与自适应设计不符）。"""
import os
import sys

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_verify_anim.py')

OLD = '''        # 矮视口回归：overflow:clip 不得吞掉"内容超高时仍可滚动可达"
        ws.call('Emulation.setDeviceMetricsOverride',
                {'width': 1366, 'height': 620, 'deviceScaleFactor': 1, 'mobile': False})
        time.sleep(1.0)
        short = ws.evaluate("""
        (function(){
          var de = document.documentElement;
          window.scrollTo(0, 99999);
          var maxY = window.scrollY;
          window.scrollTo(0, 0);
          return {sh: de.scrollHeight, ih: window.innerHeight, maxY: Math.round(maxY),
                  sw: de.scrollWidth, cw: de.clientWidth,
                  cardsVisible: [].slice.call(document.querySelectorAll('.portal__card')).length};
        })()
        """)
        case('矮视口 1366x620：内容超高时页面仍可滚动到底（裁剪未吞内容）',
             short['sh'] > short['ih'] and short['maxY'] >= short['sh'] - short['ih'] - 2
             and short['cardsVisible'] == 3,
             json.dumps(short))
        case('矮视口 1366x620：仍无横向滚动', short['sw'] <= short['cw'] + 1,
             'sw=%s cw=%s' % (short['sw'], short['cw']))
        ws.call('Emulation.setDeviceMetricsOverride',
                {'width': 1366, 'height': 768, 'deviceScaleFactor': 1, 'mobile': False})
        time.sleep(0.6)
'''

NEW = '''        # 矮视口回归：overflow:clip 不得吞掉内容。
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
'''


def main():
    raw = open(P, 'rb').read()
    src = raw.decode('utf-8')
    norm = src.replace('\r\n', '\n')
    n = norm.count(OLD)
    print('anchor hits=%d' % n)
    if n != 1:
        print('FATAL: 锚点命中 %d 次 => 未写盘' % n)
        return 2
    norm = norm.replace(OLD, NEW, 1)
    try:
        compile(norm, P, 'exec')
    except SyntaxError as e:
        print('FATAL: 语法错误', e)
        return 2
    with open(P, 'wb') as f:
        f.write(norm.encode('utf-8'))
    print('OK: 矮视口断言已改写，字节 %d -> %d' % (len(raw), os.path.getsize(P)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
