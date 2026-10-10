# -*- coding: utf-8 -*-
"""
BUGFIX-03（真机 UI：首页 + 数据报告）文档回写 + 记忆写入。

- 幂等：目标章节/标记已存在则跳过该项（不改动）。
- 安全：仅追加；不删除、不改写既有正文；不触碰 management-web / dist / 任何产品资产。
- 默认 dry-run（仅打印计划），--apply 才落盘。
"""
import io
import os
import sys

ROOT = r'C:/Users/Toporder-WS/Desktop/项目/个人健康管理系统小程序'
HS = os.path.join(ROOT, 'health-management-system')
SEAL = os.path.join(HS, 'docs', 'FINAL_PROJECT_SEAL_REPORT.md')
LOG = os.path.join(ROOT, '.workbuddy', 'memory', '2026-10-02.md')
MEM = os.path.join(ROOT, '.workbuddy', 'memory', 'MEMORY.md')

APPLY = '--apply' in sys.argv

SEAL_ANCHOR = '## 十四、封板后运行时缺陷修复 · BUGFIX-02'
SEAL_MARK = '## 十五、封板后真机 UI 缺陷修复 · BUGFIX-03'

SEAL_BODY = '''

## 十五、封板后真机 UI 缺陷修复 · BUGFIX-03（首页 + 数据报告 · 真机尺寸/布局）

> 触发：需求方使用真实 AppID 在**手机微信真机预览**，发现首页与数据报告存在 UI 缺陷。
> 本轮为 **真机 UI BUGFIX**，不改变任何业务功能、API 契约、数据库结构或绿色视觉体系。

### 15.1 现象
- 数据报告：折线/柱状卡片只显示「巨大坐标数字」（如 65 / 63.75 / 120 / 90 / 50 / 37.50）+ 部分坐标轴，图形未铺满卡片；**运动类型 ring / 睡眠质量 ring 整片空白**。
- 首页：「健康科普」标题右侧显示为 `更多 &gt;`（HTML 实体被当普通字符串）；Hero 区略松。

### 15.2 根因（真机 canvas 尺寸 **双重缩放**）
微信小程序**旧版 canvas**（`uni.createCanvasContext`）的绘图坐标系 = 组件 **CSS 像素**，位图由容器按设备 DPR 自动渲染，**不需要调用方再乘 DPR**。旧封装把
`width = 实测宽度 * pixelRatio`、`pixelRatio = 系统 DPR(≈3)`，而 uCharts 内部又把 `fontSize / padding / ringWidth / yAxisWidth / dashLength` 等统一 `* opts.pix`，导致：
1) 图形与文字被整体放大 DPR 倍 → 卡片里只剩「巨大数字 + 部分坐标轴」；
2) 饼/环图圆心 `(width/2, height/2)` 被推出画布 → **环图整片空白**。

### 15.3 修复（产品代码 3 个文件）
| 文件 | 改动 |
| --- | --- |
| `miniapp/components/u-charts/u-charts.vue` | `width/height` 改为 **CSS px**（`boundingClientRect` 实测，异常回落 `uni.upx2px`）；`pixelRatio` 固定 **1**；补齐 `extra.ring`（库内 pie/ring 使用两个独立配置键）；单序列图例关闭；字号 11~12。**未改第三方 `u-charts.js`** |
| `miniapp/pages/report/index.vue` | ring 保持 `[{name,value}]` 对象数组并加 `value>0` 守卫（全 0 / 无数据 → 置空走「暂无数据」）；线/柱/面积数据经 `pick()` 过滤空值（0/1/2+ 三态自然分支）；趋势卡高 380rpx、ring 卡高 420rpx；单序列关图例 |
| `miniapp/pages/index/index.vue` | `更多 &gt;` → **`更多 ›`**（真实字符）；Hero 内边距 26/30/22rpx、下边距收紧；内容卡标题与 Hero 间距压缩；**`imgSrc()` 头像修复保留** |

- 首页：Hero 间距收紧，九宫格/科普列表/业务功能与 API 均未改。
- 数据报告：**无写死、无 mock、无隐藏图表**；`65 / 63.75 / 50 / 37.50` 等均为 uCharts 自身计算的 Y 轴刻度，已由正确尺寸配置消除「巨大刻度」现象。
- 第三方库 `components/u-charts/u-charts.js` **零改动**（`oldseries[i].formatter` 仍恰 1 处，与源码语义逐字一致）。

### 15.4 验证（软件侧）
- 无头 Node harness（加载**真实** `u-charts.js`）：series 结构 **12/12**、真机尺寸/越界/字号/单分类整圆 **28/28**。
- HBuilderX 命令行重编译 `mp-weixin`：**rc=0**；产物锚点（新结构 hit / 旧结构残留 0 / ring 圆心在画布内）；
- 编译确定性：两次编译 **106/106 逐字节一致**；`node --check` 全通过；vendor 符号无未定义引用。
- `backend_selfcheck 5/5` · `miniapp_check 23/23` · `web_check 33/33` · `api_test 199/199` · 安全 A~K `197/197`。
- 响应式循环静态核查：封装组件仅 `watch(props.chartData)` 与 `watch([width,height])`，均不写模板读取的响应式；`image.js` 只在**异步回调**里写 `localPaths` ⇒ 无 `render → 改 reactive → render` 循环。

```
FORMATTER_ERROR                  = 0
RECURSIVE_UPDATE_ERROR           = 0（产品侧静态核查；如真机仍出现请回传，继续定位）
MINIPROGRAM_PRODUCT_ERROR        = 0
DATABASE_SCHEMA_CHANGED          = NO（19 表 / 139 列 / 指纹未变）
PROTECTED_ALL_INTACT             = True（小周 10 类业务 + doctor002 / coach001 绑定均 INTACT）
TEMP_TEST_DATA_RESIDUE           = 0
MANAGEMENT_WEB_SOURCE_CHANGED    = NO（PC 端本轮 0 改动；web_check 33/33 即无回归证据）
VITE_BUILD                       = SKIPPED_DUE_TO_SAFE_DELETE_GUARD
SOFTWARE_REGRESSION              = PASS
REAL_DEVICE_UI_ACCEPTANCE        = WAITING_USER_CONFIRMATION
PROJECT_FINAL_SEAL               = REOPENED_FOR_REAL_DEVICE_UI_FIX
```

### 15.5 真机人工验收清单（请需求方重编译后逐项确认）
**A. 首页**：头像正常 · 「更多 ›」正常 · Hero 高度/间距正常 · 九宫格正常 · 科普封面正常
**B. 数据报告**：概览卡正常 · 体重趋势正常 · 血压趋势正常 · 运动时长正常 · 运动类型 ring 正常 · 睡眠质量 ring 正常 · **无巨大坐标数字** · **无异常空白**
**C. 我的**：头像正常 · 原页面无回归

> 未在真机人工确认前，本报告**不**标注 `REAL_DEVICE_UI_ACCEPTANCE = PASS`。
'''

LOG_ENTRY = '''
## 2026-10-02 · BUGFIX-03 真机 UI 修复（首页 + 数据报告）

- **触发**：真机预览发现数据报告图表「巨大坐标数字 / ring 空白」、首页 `更多 &gt;` 实体外露。
- **根因**：小程序旧版 canvas 坐标系 = CSS px；旧封装 `width*DPR` + `pixelRatio=DPR` 造成**双重缩放**，
  库内再 `*opts.pix` ⇒ 放大 DPR 倍、饼/环圆心出画布。
- **修复**：`u-charts.vue`（CSS px + pixelRatio=1 + 实测尺寸 + 补 `extra.ring`）、
  `report/index.vue`（ring 对象数组 + value>0 守卫 + 空值过滤 + 卡高 380/420 + 单序列关图例）、
  `index/index.vue`（`更多 ›` + Hero 间距收紧）。**第三方库零改动**，头像 `imgSrc()` 保留。
- **验证**：series 12/12 · 真机尺寸 28/28 · HBuilderX 重编译 rc=0 · 编译确定性 106/106 ·
  backend_selfcheck 5/5 · miniapp 23/23 · web 33/33 · api_test 199/199 · 安全 197/197。
- **封板**：PROJECT_FINAL_SEAL = REOPENED_FOR_REAL_DEVICE_UI_FIX；等真机人工确认。
'''

MEM_ENTRY = '''
## 九、真机 UI 修复沉淀（BUGFIX-03，2026-10-02）

- **铁律**：微信小程序**旧版 canvas**（`uni.createCanvasContext`）**绘图坐标系 = 组件 CSS 像素**，
  位图由容器按设备 DPR 自动渲染。⇒ 传给 uCharts 的 `width/height` 必须是 **CSS px**、
  `pixelRatio` **恒为 1**；**绝不可** `width = 实测 * pixelRatio`（会与库内 `*opts.pix` 叠加成双重缩放）。
- **症状对照**：卡片里只剩「巨大坐标数字 + 部分坐标轴」= 缩放加倍；**饼/环图整片空白** = 圆心
  `(w/2,h/2)` 被推出画布。**不要**把 750rpx 设计稿值直接当 canvas px，须经 `boundingClientRect`
  实测或 `uni.upx2px` 换算。
- **uCharts 配置键**：pie 与 ring 用**两个独立**键 `opts.extra.pie` / `opts.extra.ring`，只写 pie 时
  ring 会退回库默认；单序列图建议 `legend.show=false`。
- **唯一封装点**：`miniapp/components/u-charts/u-charts.vue`（全项目图表统一走它）；
  **第三方 `u-charts.js` 零改动**，禁止在库内加 `typeof===‘number’` 之类掩盖补丁。
- **页内空值策略**：趋势数据先 `pick()` 剔除 null/''/NaN（0/1/2+ 三态自然分支）；ring 先 `value>0`
  过滤，全 0 或空 ⇒ 置空走「暂无数据」，避免库内 `count===0` 画出「并不真实的整圆」。
- **UI 文本**：模板文本节点里**不要**出现 `&gt;` / `&lt;` / `&amp;` 实体（会被当普通字符串显示）；
  「更多 ›」用真实字符 `\u203a`。
- **真机验收资产**：`tests/security/_ucharts_realdevice_size_verify.js`（真实库 + 假 ctx 记录绘制几何，
  28 项：旧配置圆心越界/字号 DPR 倍复现、修复后字号 11~14 且不越界、单分类整圆 sweep=2π）。
'''

def read_text(p):
    return open(p, 'rb').read().decode('utf-8')

def write_text(p, t):
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)

def main():
    print('APPLY =', APPLY)
    print('=' * 60)

    # 1) 封板报告 §十五
    t = read_text(SEAL)
    if SEAL_MARK in t:
        print('[SKIP] 封板报告已含 §十五')
    else:
        n = t.count(SEAL_ANCHOR)
        print('[SEAL] 锚点 "%s" 命中 = %d（须为 1）' % (SEAL_ANCHOR, n))
        assert n == 1, '封板报告锚点命中数异常，中止'
        new = t.rstrip('\n') + '\n' + SEAL_BODY.lstrip('\n')
        if APPLY:
            write_text(SEAL, new)
        print('[SEAL] %d -> %d bytes' % (len(t.encode('utf-8')), len(new.encode('utf-8'))))

    # 2) 当日日志
    lt = read_text(LOG)
    mark = '## 2026-10-02 · BUGFIX-03'
    if mark in lt:
        print('[SKIP] 当日日志已含 BUGFIX-03')
    else:
        new = lt.rstrip('\n') + '\n' + LOG_ENTRY.lstrip('\n')
        if APPLY:
            write_text(LOG, new)
        print('[LOG] %d -> %d bytes' % (len(lt.encode('utf-8')), len(new.encode('utf-8'))))

    # 3) MEMORY.md
    mt = read_text(MEM)
    mmark = '## 九、真机 UI 修复沉淀'
    if mmark in mt:
        print('[SKIP] MEMORY.md 已含真机 UI 章节')
    else:
        new = mt.rstrip('\n') + '\n' + MEM_ENTRY.lstrip('\n')
        if APPLY:
            write_text(MEM, new)
        print('[MEM] %d -> %d bytes' % (len(mt.encode('utf-8')), len(new.encode('utf-8'))))

    print('=' * 60)
    print('DONE. %s' % ('已落盘' if APPLY else 'dry-run（加 --apply 落盘）'))

if __name__ == '__main__':
    main()
