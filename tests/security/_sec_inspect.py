# -*- coding: utf-8 -*-
import json, os, sys

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_out')

def main():
    lines = []
    for g in 'ABCDEFGHIJK':
        p = os.path.join(OUT, 'sec_%s.json' % g)
        if not os.path.exists(p):
            lines.append('%s MISSING' % g)
            continue
        try:
            j = json.load(open(p, encoding='utf-8'))
        except Exception as e:
            lines.append('%s READERR %s' % (g, e))
            continue
        if isinstance(j, list):
            total = len(j)
            def is_ok(c):
                if not isinstance(c, dict):
                    return False
                for k in ('passed', 'ok', 'pass'):
                    if k in c:
                        return bool(c[k])
                return str(c.get('status', '')).upper().startswith('PASS')
            fails = [c for c in j if not is_ok(c)]
            lines.append('%s list total=%d passed=%d fails=%d mtime=%s' % (
                g, total, total - len(fails), len(fails), round(os.path.getmtime(p))))
            for c in fails:
                lines.append('      FAIL: %s' % json.dumps(c, ensure_ascii=False)[:500])
        elif isinstance(j, dict):
            lines.append('%s dict keys=%s mtime=%s' % (g, list(j.keys()), round(os.path.getmtime(p))))
            lines.append('    %s' % json.dumps(j, ensure_ascii=False)[:800])
    txt = '\n'.join(lines)
    open(os.path.join(OUT, '_inspect.txt'), 'w', encoding='utf-8').write(txt)
    sys.stdout.write(txt + '\n')

if __name__ == '__main__':
    main()
