# -*- coding: utf-8 -*-
"""重启 Flask：终止占用 8080 的旧进程 -> 以独立进程重新拉起 -> 轮询 /api/health。"""
import io
import os
import signal
import subprocess
import sys
import time
import urllib.request

BASE = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system'
BACKEND = os.path.join(BASE, 'backend')
PY = os.path.join(BASE, '.venv', 'Scripts', 'python.exe')

HEALTH = 'http://127.0.0.1:8080/api/health'


def listening_pids(port=8080):
    """netstat -ano 行形如: TCP 0.0.0.0:8080 0.0.0.0:0 LISTENING 8984"""
    out = subprocess.run('netstat -ano', shell=True, capture_output=True)
    txt = out.stdout.decode('utf-8', 'replace')
    pids = set()
    for line in txt.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[0].upper() == 'TCP' and parts[1].endswith(':%d' % port):
            if 'LISTENING' in parts:
                pids.add(parts[-1])
    return pids


def port_open(port=8080, host='127.0.0.1'):
    import socket
    s = socket.socket()
    s.settimeout(0.5)
    try:
        return s.connect_ex((host, port)) == 0
    finally:
        s.close()


def health():
    try:
        with urllib.request.urlopen(HEALTH, timeout=3) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except Exception as e:  # noqa: BLE001
        return None, '%s: %s' % (type(e).__name__, e)


def main():
    pids = listening_pids()
    print('OLD LISTENING PIDS =', sorted(pids))
    for pid in sorted(pids):
        r = subprocess.run('taskkill /PID %s /F' % pid, shell=True, capture_output=True)
        print('  taskkill %s -> rc=%s %s' % (pid, r.returncode,
                                             r.stdout.decode('utf-8', 'replace').strip()
                                             or r.stderr.decode('utf-8', 'replace').strip()))
    # 确认端口已释放
    for _ in range(30):
        if not port_open():
            break
        time.sleep(0.5)
    print('PORT 8080 FREE =', not port_open())
    if port_open():
        print('!! 端口仍被占用，终止流程')
        return 2

    logf = io.open(os.path.join(BACKEND, 'server.log'), 'ab')
    DETACHED_PROCESS = 0x00000008
    CREATE_NEW_PROCESS_GROUP = 0x00000200
    p = subprocess.Popen([PY, 'app.py'], cwd=BACKEND,
                         stdout=logf, stderr=logf, stdin=subprocess.DEVNULL,
                         creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)
    print('NEW FLASK PID =', p.pid)

    ok = False
    for i in range(60):
        time.sleep(0.5)
        st, body = health()
        if st == 200:
            print('HEALTH OK after %.1fs: %s %s' % ((i + 1) * 0.5, st, body))
            ok = True
            break
    if not ok:
        print('!! HEALTH FAILED:', health())
        tail = io.open(os.path.join(BACKEND, 'server.log'), encoding='utf-8',
                       errors='replace').read()[-1500:]
        print('--- server.log tail ---')
        print(tail)
        return 1
    print('LISTENING PIDS NOW =', sorted(listening_pids()))
    return 0


if __name__ == '__main__':
    sys.exit(main())
