# -*- coding: utf-8 -*-
"""把 BUGFIX-02 的教训沉淀进两个既有 skill（锚点式，命中须恰为 1 次）。

- ucharts-config-key-and-canvas-probe：新增「第 4 类根因：饼/环图 series 结构」+「无头 Node harness」
- hbuilderx-cli-build-and-verify：新增「Windows 本机非交互调用实测补充」

用法： python _ucharts_skill_patch.py [--apply]
"""
import io
import os
import sys

SK = os.path.expanduser('~') + r'/.workbuddy/skills'
F1 = os.path.join(SK, 'ucharts-config-key-and-canvas-probe', 'SKILL.md')
F2 = os.path.join(SK, 'hbuilderx-cli-build-and-verify', 'SKILL.md')

# ----------------------------- Edits -----------------------------

E1_DESC_OLD = u'与「测量/绘制必须同源」原则。当出现「折线或双线整块空白/半渲染」'
E1_DESC_NEW = (u'与「测量/绘制必须同源」原则。另含第 4 类：饼/环图 series[0].data 传纯数值数组 ⇒ '
               u'库内 fixPieSeries 对 number 赋 formatter 抛 "Cannot create property \'formatter\' on number"；'
               u'附「转 CJS + mock canvas + new uCharts」无头 Node 复现/回归 harness。'
               u'当出现「折线或双线整块空白/半渲染」')

E1_TAIL_OLD = u'- **新增：真机 `captionPx` 类 rem→px 换算会静默失效**（逻辑层拿不到根字号）⇒ 依赖它的「自适应」逻辑在真机上从未执行；**别把真机上看变好的现象归功于一段没跑过的代码**。'

E1_TAIL_NEW = E1_TAIL_OLD + u"""

## 9. 第 4 类根因：饼/环图 series 结构（运行时抛错，不是"设了没效果"）

> 现象：Console 持续 `MiniProgramError: Cannot create property 'formatter' on number '50'`（或 `'1'`），
> 调用栈 `fixPieSeries → drawCharts → new uCharts → render → init`。**与配置键位无关，别去改 opts。**

**根因（读库源码，勿猜）**：`u-charts.js` 的 `fixPieSeries(series, opts, config)`：

```js
if (series.length > 0 && series[0].data.constructor.toString().indexOf('Array') > -1) {
  opts._pieSeries_ = series;
  let oldseries = series[0].data;
  for (var i = 0; i < oldseries.length; i++) {
    oldseries[i].formatter = series[0].formatter;   // ★ 对 number 赋属性 ⇒ 严格模式抛错
    oldseries[i].data = oldseries[i].value;
    pieSeriesArr.push(oldseries[i]);
  }
  opts.series = pieSeriesArr;
}
```

- 只要 `series[0].data` 是 **Array**（哪怕是 `[50]`），就会逐项写 `.formatter`；
  若元素是**原始数值** ⇒ `Cannot create property 'formatter' on number '50'`。
- **调用范围**：`if (type === 'pie' || type === 'ring' || type === 'mount' || type === 'rose' || type === 'funnel') series = fixPieSeries(...)`
  ⇒ **line / column / area 的「数值数组」是正确格式，不受影响**（别顺手改它们）。

**正确结构（ECharts 饼图兼容）**：

| | 结构 |
|---|---|
| BAD | `series: [{ name: '运动时长', data: [50] }]` —— `data` 是**纯数值数组** |
| FIXED | `series: [{ data: [{ name: '球类', value: 50 }] }]` —— `data` 是**对象数组** |

- 修复只改**调用方**（页面里的数据适配），**绝不在库内加 `if (typeof x === 'number')` 掩盖**。
- 不变量：`categories` 仍可作图例文本来源；业务值仍取真实接口，**不写死、不 mock、不隐藏图表**。

**扫描完整性**：一个页面修完还要全树扫一遍 `type="pie|ring|mount|rose|funnel"` 的全部使用点
（实例：全项目只有 1 个 report 页共 6 张图，其中仅 2 张 ring 需改）——只认组件属性 `type`，
别把 line/column/area 的数值数组误报成问题。

## 10. 无头 Node harness：不依赖浏览器/开发者工具复现与回归

适用于「小程序真机或开发者工具报错、但 CI 里跑不了 GUI」的场景。

1. 把第三方 `u-charts.js` **原样**读入，**只改最后一行** `export default uCharts;` → `module.exports = uCharts;`，
   写到临时文件（**不改库逻辑**）。
2. `require` 它，用 **mock canvas context**（`Proxy` 兜底：`measureText` 返回 `{width}`，其余方法 no-op）
   构造 `opts`，直接 `new uCharts(opts)`。
3. `baseOptions` 必须**复刻**封装组件里的默认值（`type/width/height/pixelRatio/fontSize/legend/xAxis/yAxis/extra` …），
   否则可能因缺键抛别的错、掩盖真因。
4. 用例覆盖：**旧结构断言抛错**（复现原文）＋ **新结构断言不抛错** ＋ 其它图型（line/column/area）回归 ＋ `updateData` 增量刷新。
5. 脚本自己**落盘**（`X.md` + `X.json`），**禁管道**；判定以落盘文件为准。

> 加固：把产物 `unpackage/dist/**/u-charts.js` 里的 `fixPieSeries` 函数体与源码逐字对比
> （允许格式化差异与 `config`→`config2` 重命名），可证明**第三方库零改动、被测库 = 出厂库**。
"""

E2_TAIL_OLD = u'- 若项目无法可靠命令行构建 → 明确输出 **`MANUAL_BUILD_REQUIRED = YES`**，并给出 HBuilderX 精确点击路径（打开哪个项目 → 哪个菜单 → 哪个目标 → 完成后哪个目录 mtime 会变），**不要伪造成功**。'

E2_TAIL_NEW = E2_TAIL_OLD + u"""

---

## 六、Windows 本机非交互调用（实测补充）

- 本机 Git Bash 缺 `head/tail/cat/grep` ⇒ `./cli.exe project list | head` 这类会**「左侧照跑、右侧不存在」**：
  回显为空但退出码 127，极易误判成「CLI 不可用」。**正解：不用管道**，把 stdout 落盘再读。
- 推荐用 **Python `subprocess`** 调用，并显式设 `cwd=<HBuilderX 安装目录>`：

```python
import subprocess, os
exe = r'<HBuilderX 安装目录>/cli.exe'
p = subprocess.run([exe, 'project', 'list'], cwd=os.path.dirname(exe),
                   capture_output=True, timeout=180)
print(p.returncode, (p.stdout or b'').decode('utf-8', 'replace'))
```

- 实测一次完整「改源码 → `launch mp-weixin --compile true` → 验收产物」约 **8–12 s**（日志 `ready in ~10s`）。
- 产物比对里常见的**整批小额负差**（每文件 -65~-85 B、`vendor.js` 约 -17.9 KB）正是 §三-3 的
  **尾注 / 统计注入差异**，**不是内容缺失**；要判定内容是否真的变了，只看**锚点字符串 hit 数**
  与**两次编译的确定性**（run1 vs run2 是否 106/106 逐字节一致 ⇒ `BUILD_DETERMINISTIC = YES`）。
"""


def apply_file(path, edits, apply_):
    raw = open(path, 'rb').read()
    text = raw.decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    print('== %s  (%d bytes, %s)' % (os.path.basename(os.path.dirname(path)), len(raw),
                                     'CRLF' if nl == '\r\n' else 'LF'))
    ok = True
    for i, (old, new) in enumerate(edits, 1):
        n = text.count(old)
        print('   edit%d 命中=%d  %s' % (i, n, 'OK' if n == 1 else '!! 中止'))
        if n != 1:
            ok = False
    if not ok:
        print('   -> 守卫未通过，本文件不改')
        return False
    for old, new in edits:
        text = text.replace(old, new.replace('\n', nl), 1)
    if apply_:
        with io.open(path, 'wb') as f:
            f.write(text.encode('utf-8'))
        print('   -> 已落盘，新字节数 %d (+%d)' % (len(text.encode('utf-8')),
                                              len(text.encode('utf-8')) - len(raw)))
    else:
        print('   -> [dry-run] 未落盘，预计 +%d 字节' % (len(text.encode('utf-8')) - len(raw)))
    return ok


def main():
    apply_ = '--apply' in sys.argv
    print('==== skill 沉淀 (%s) ====' % ('APPLY' if apply_ else 'DRY-RUN'))
    a = apply_file(F1, [(E1_DESC_OLD, E1_DESC_NEW), (E1_TAIL_OLD, E1_TAIL_NEW)], apply_)
    b = apply_file(F2, [(E2_TAIL_OLD, E2_TAIL_NEW)], apply_)
    print('汇总: ucharts=%s  hbuilderx=%s' % (a, b))
    return 0 if (a and b) else 1


if __name__ == '__main__':
    sys.exit(main())
