# -*- coding: utf-8 -*-
"""真实执行 `npm run build`（本机 npm 默认 script-shell 解析到不存在的 bash，故显式 --script-shell=cmd.exe）。"""
import os
import subprocess
import sys

MW = r'C:\Users\Toporder-WS\Desktop\项目\个人健康管理系统小程序\health-management-system\management-web'
NODE = r'C:\Users\Toporder-WS\.workbuddy\binaries\node\versions\22.22.2-3\node.exe'
LOG = os.path.join(MW, '_verify_out', 'npm_build.log')

CANDIDATES = [
    r'E:\node.js\node_modules\npm\bin\npm-cli.js',
    r'E:\node.js\npm\node_modules\npm\bin\npm-cli.js',
    r'C:\Program Files\nodejs\node_modules\npm\bin\npm-cli.js',
    r'C:\Users\Toporder-WS\AppData\Roaming\npm\node_modules\npm\bin\npm-cli.js',
]


def find_npm():
    for c in CANDIDATES:
        if os.path.exists(c):
            return c
    # 兜底：在 node 安装目录里搜一层
    for base in (r'E:\node.js', r'C:\Program Files\nodejs'):
        for root, dirs, files in os.walk(base):
            if root.count(os.sep) - base.count(os.sep) > 4:
                dirs[:] = []
                continue
            if 'npm-cli.js' in files and os.sep + 'npm' + os.sep in root + os.sep:
                return os.path.join(root, 'npm-cli.js')
    return None


def main():
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    npm = find_npm()
    print('npm-cli.js =', npm)
    if not npm:
        print('FATAL: 未找到 npm-cli.js')
        return 2
    cmd = [NODE, npm, 'run', 'build', '--script-shell=cmd.exe']
    print('cmd =', ' '.join(cmd))
    with open(LOG, 'wb') as f:
        p = subprocess.run(cmd, cwd=MW, stdout=f, stderr=subprocess.STDOUT)
    txt = open(LOG, 'rb').read().decode('utf-8', 'replace')
    print('EXIT =', p.returncode)
    print('BUILT =', 'built in' in txt)
    import re
    m = re.findall(r'(IdentitySelect-[A-Za-z0-9_]+\.(?:css|js))\s+([\d.,]+\skB)', txt)
    for a, b in m:
        print('   %s  %s' % (a, b))
    m2 = re.search(r'✓ \d+ modules transformed', txt) or re.search(r'(\d+) modules transformed', txt)
    print('modules:', m2.group(0) if m2 else '?')
    print('--- tail ---')
    print('\n'.join(txt.strip().splitlines()[-6:]))
    return 0 if (p.returncode == 0 and 'built in' in txt) else 1


if __name__ == '__main__':
    sys.exit(main())
