# -*- coding: utf-8 -*-
"""让验证器如实报告 5173 上的 dev server 是"复用已有"还是"脚本自起"（原写法会默认是自己起的）。"""
import os
import sys

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_verify_anim.py')

OLD_FN = """def start_dev_server():
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
                return p, body
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
    raise RuntimeError('vite dev server not ready in 120s')"""

NEW_FN = """def start_dev_server():
    \"\"\"返回 (proc_or_None, html, reused)。

    先探测 5173 是否**已有**dev server 在跑（例如用户自己开着 `npm run dev`）：
      - 有 -> 直接复用，proc 返回 None（收尾不去 kill 别人的进程）；
      - 无 -> 自起一个（用 --strictPort 保证不会被静默换端口），失败则清理后抛错。
    归属必须如实上报，否则日志会谎称"脚本自起"。
    \"\"\"
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
    raise RuntimeError('vite dev server not ready in 120s')"""

OLD_CALL = """    dev, html = start_dev_server()
    case('脚手架：Vite dev server 在 127.0.0.1:5173 就绪并返回 index.html', 'id="app"' in html,
         '%.1fs' % (time.time() - t0))"""

NEW_CALL = """    dev, html, reused = start_dev_server()
    case('脚手架：127.0.0.1:5173 的 dev server 就绪并返回 index.html（来源：%s）'
         % ('复用已在运行的实例' if reused else '本脚本自起'),
         'id="app"' in html, '%.1fs' % (time.time() - t0))"""

OLD_FIN = """        for p in (chrome, dev):
            try:"""
NEW_FIN = """        for p in (chrome, dev):
            if p is None:      # 复用别人已在跑的 dev server 时不去 kill
                continue
            try:"""

PATCHES = [(OLD_FN, NEW_FN), (OLD_CALL, NEW_CALL), (OLD_FIN, NEW_FIN)]


def main():
    raw = open(P, 'rb').read()
    src = raw.decode('utf-8')
    norm = src.replace('\r\n', '\n')
    for i, (old, new) in enumerate(PATCHES, 1):
        n = norm.count(old)
        print('patch %d hits=%d' % (i, n))
        if n != 1:
            print('FATAL: patch %d 命中 %d 次 => 未写盘' % (i, n))
            return 2
        norm = norm.replace(old, new, 1)
    try:
        compile(norm, P, 'exec')
    except SyntaxError as e:
        print('FATAL: 语法错误', e)
        return 2
    with open(P, 'wb') as f:
        f.write(norm.encode('utf-8'))
    print('OK: 归属判定已修正，字节 %d -> %d' % (len(raw), os.path.getsize(P)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
