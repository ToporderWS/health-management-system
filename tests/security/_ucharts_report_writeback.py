# -*- coding: utf-8 -*-
"""BUGFIX-02（uCharts 饼/环图 formatter 异常）回写封板报告 §十四。

约束（沿用本工程锚点式回写铁律）：
  - 每条锚点必须**恰好命中 1 次**，任一不满足 ⇒ 整个文件不改（dry-run 打印原因）；
  - 保留原文件行尾（open('rb') 读取，按自身判定 \\r\\n / \\n）；
  - 默认 dry-run，需显式 --apply 才落盘。

用法： python _ucharts_report_writeback.py [--apply]
"""
import io
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPORT = os.path.join(BASE, 'docs', 'FINAL_PROJECT_SEAL_REPORT.md')

ANCHOR = u'4. 真机调试进入「我的」页 → 头像应正常显示。'

SECTION = u"""

## 十四、封板后运行时缺陷修复 · BUGFIX-02（uCharts 饼/环图 formatter 异常）

> 记录时间：2026-10-02。需求方在**真机预览前**于微信开发者工具 Console 发现持续报错
> `MiniProgramError: Cannot create property 'formatter' on number '50'` /
> `... on number '1'`，调用栈 `fixPieSeries → uCharts2.drawCharts → new uCharts2 → render → init`。
> 本轮严格按「定位 → 最小修复 → 重新编译 → 回归 → 报告」执行，**未修改第三方库源码**。

### 14.1 定位结论

- **报错来源（产品代码）**：`miniapp/pages/report/index.vue`（数据报告页，全项目**唯一**使用图表的页面）。
  - 运动类型分布（ring）：`series: [{ name: '运动时长', data: sport_by_type.map(x => x.value) }]` → `data: [50]`
  - 睡眠质量占比（ring）：`series: [{ name: '次数', data: qualities.map(x => x.value) }]` → `data: [1]`
- **触发点（第三方库，未改动）**：`miniapp/components/u-charts/u-charts.js` 第 320 行 `fixPieSeries()`：
  当 `series[0].data` 为 Array 时逐项执行 `oldseries[i].formatter = series[0].formatter`；
  若 `oldseries[i]` 是**原始数值**，严格模式下向 number 赋属性即抛
  `Cannot create property 'formatter' on number '50'`。
  `fixPieSeries` 仅在 `type ∈ {pie, ring, mount, rose, funnel}` 时被调用（第 6386 行），
  故 line / column / area 的**数值数组**格式不受影响。

### 14.2 根因与修复

| 项 | 内容 |
| --- | --- |
| 错误结构（BAD） | `series: [{ name, data: [50] }]` —— `data` 为**纯数值数组** |
| 正确结构（FIXED） | `series: [{ data: [{ name, value }] }]` —— ECharts 兼容的**对象数组** |
| 修复方式 | 仅改**调用方数据结构**（`pages/report/index.vue` 两处 ring 图）；未在库内加 `typeof === 'number'` 之类掩盖补丁 |
| 业务数据 | 仍取自真实接口 `/api/report/statistics`（MySQL 真值 50 / 1），未写死、未 mock、未隐藏图表 |

### 14.3 运行时验证（无头 harness，加载真实 u-charts.js）

`tests/security/_ucharts_fix_verify.js`：把 `u-charts.js` 原样转 CJS（仅改导出行，**不动库逻辑**），
用 mock canvas 直接 `new uCharts(opts)`：

```
用例                                        预期    实际    结果
旧结构 ring data:[50]（应报 formatter 错）    抛错    抛错    PASS（复现原文）
旧结构 ring data:[1] （应报 formatter 错）    抛错    抛错    PASS（复现原文）
新结构 ring 运动类型分布（真值 50）           不抛错  不抛错  PASS
新结构 ring 睡眠质量占比（真值 1）            不抛错  不抛错  PASS
新结构 ring 多分片 / 全 0 值 / pie 单分片      不抛错  不抛错  PASS
line / line 双系列 / column / area          不抛错  不抛错  PASS
updateData 增量刷新 ring                    不抛错  不抛错  PASS
TOTAL = 12  PASS = 12  FAIL = 0
```

> `fixPieSeries` 在产物 `unpackage/dist/dev/mp-weixin/components/u-charts/u-charts.js` 中与源码
> **语义逐字一致**（`oldseries[i].formatter` 恰 1 处）⇒ 证明**第三方库零改动**，被测库 = 出厂库。

### 14.4 重新编译与产物验收（HBuilderX CLI）

```
HBuilderX cli.exe launch <miniapp> --compile true  → rc=0（mp-weixin 编译成功，约 11s）
产物锚点：新结构 { name, value } hit=2；旧结构 hit=0；全树旧结构残留文件 = 0
common/image.js（BUGFIX-01 头像本地化）仍在；profile/index.js 与 index/index.js 仍走 imgSrc
node --check 语法：23 个 .js 全通过；common_vendor 导出符号 21/21 齐备，未定义引用 = 0
两次编译产物 106/106 文件逐字节一致（BUILD_DETERMINISTIC = YES）
```

### 14.5 回归结果

```
backend_selfcheck = 5/5 PASS          miniapp = 23/23 PASS
management-web    = 33/33 PASS        api_test = 199/199 PASS
security A~K      = 197/197 PASS
uCharts 结构运行时验证 = 12/12 PASS    HBuilderX 编译产物验收 = PASS

用户数据(1/2/12/13) = INTACT     doctor002 绑定 = INTACT    coach001 绑定 = INTACT
PROTECTED_ALL_INTACT = True      DATABASE_SCHEMA_CHANGED = NO（19 表 / 139 列 / 指纹未变）
本轮临时数据残留 = 0
```

### 14.6 判定

```
UCHARTS_FORMATTER_ERROR_BEFORE = 2（复现：on number '50' / on number '1'）
UCHARTS_FORMATTER_ERROR_AFTER  = 0（真实库运行时 12/12；产品代码 0 处旧结构）
UCHARTS_RUNTIME_FIX = PASS（软件侧全闭环；开发者工具 Console 由需求方按 14.7 复看）
PROJECT_FINAL_SEAL  = PASS（REOPENED_FOR_BUGFIX → PASS）
```

### 14.7 开发者工具复看步骤

1. HBuilderX 重新运行到微信开发者工具（产物 `unpackage/dist/dev/mp-weixin` 已重建）；
2. 登录小周账号，打开「数据报告」页；
3. Console 过滤关键字 `formatter` ⇒ 期望 **0 条**；
4. 其余红色条目按三类归因：PRODUCT_ERROR（应为 0）/ DEVTOOLS_NOISE（uni统计、sourcemap、
   渲染层提示）/ NETWORK_ERROR（局域网 http 相关）。
"""


def main():
    apply_ = '--apply' in sys.argv
    raw = open(REPORT, 'rb').read()
    text = raw.decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'

    print('==== BUGFIX-02 回写封板报告 (%s) ====' % ('APPLY' if apply_ else 'DRY-RUN'))
    print('目标文件 : %s' % REPORT)
    print('原字节数 : %d   行尾: %s' % (len(raw), 'CRLF' if nl == '\r\n' else 'LF'))

    hit = text.count(ANCHOR)
    print('锚点命中 : %d  （要求恰为 1）' % hit)
    print('已存在 §十四: %s' % ('## 十四' in text))

    if hit != 1 or '## 十四' in text:
        print('\n!! 守卫未通过，整份文件不改。')
        return 1

    body = SECTION.replace('\n', nl)
    new_text = text + body
    if not new_text.endswith(nl):
        new_text += nl

    print('新增字节 : +%d' % (len(new_text.encode('utf-8')) - len(raw)))
    if not apply_:
        print('\n[dry-run] 未落盘。加 --apply 执行。')
        return 0

    with io.open(REPORT, 'wb') as f:
        f.write(new_text.encode('utf-8'))
    print('\n已落盘。新字节数 : %d' % os.path.getsize(REPORT))
    return 0


if __name__ == '__main__':
    sys.exit(main())
