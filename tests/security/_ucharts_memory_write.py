# -*- coding: utf-8 -*-
"""记录 BUGFIX-02：写当日日志 + MEMORY.md 增补 §八。默认 dry-run。

用法： python _ucharts_memory_write.py [--apply]
"""
import io
import os
import sys

MEM = r'C:/Users/Toporder-WS/Desktop/项目/个人健康管理系统小程序/.workbuddy/memory'
LOG = os.path.join(MEM, '2026-10-02.md')
CUR = os.path.join(MEM, 'MEMORY.md')

LOG_TEXT = u"""# 2026-10-02 工作日志

## BUGFIX-02 · uCharts 饼/环图 `formatter` 运行时异常（真机预览前）

- **现象**：微信开发者工具 Console 持续 `MiniProgramError: Cannot create property 'formatter' on number '50'` / `'1'`，
  栈 `fixPieSeries → drawCharts → new uCharts → render → init`。
- **定位**：报错源 = `miniapp/pages/report/index.vue`（全项目唯一图表页）：ring 图 `series[0].data` 传了纯数值数组；
  触发点 = 第三方库 `components/u-charts/u-charts.js` L320 `fixPieSeries()` 对 number 赋 `.formatter`
  （该函数仅对 pie/ring/mount/rose/funnel 调用，L6386）。
- **最小修复**：只改调用方数据结构 → `series: [{ data: [{ name, value }] }]`（2 处 ring）；**未改第三方库**；
  业务值仍取真实接口，未写死 / 未 mock / 未隐藏图表。
- **重新编译**：HBuilderX `cli.exe launch mp-weixin --compile true` rc=0（~11s）；产物锚点：新结构 hit=2、旧结构 hit=0、
  全树旧残留 0；`common/image.js` 与 `imgSrc`（BUGFIX-01）仍在 ⇒ 未回滚头像修复。
- **运行时验证**：`tests/security/_ucharts_fix_verify.js` **12/12**（旧结构复现两条原文错误 / 新结构 0 抛错 /
  line·column·area 回归 / updateData 增量）；产物内 `fixPieSeries` 与源码语义逐字一致 ⇒ **第三方库零改动**。
- **回归（本轮实测）**：backend_selfcheck **5/5** · miniapp **23/23** · web **33/33** · api_test **199/199** ·
  安全 A~K **197/197** · `_seal_verify` 全 True（`PROTECTED_ALL_INTACT=True`、19 表 / 139 列 / 指纹不变、残留 0）。
- **收尾清理**：`_sec_final_cleanup.py --apply` 删除 sec_ 临时实体（users 7→4、doctor_user 10→5、coach_user 8→4），
  小周 ↔ doctor002 / coach001 绑定完好。
- **文档回写**：`docs/FINAL_PROJECT_SEAL_REPORT.md` 追加 **§十四**（锚点命中恰 1：19982→25042 B）。
- **skill 沉淀**：`ucharts-config-key-and-canvas-probe` 增 §9 / §10（饼环 series 结构 + 无头 Node harness）；
  `hbuilderx-cli-build-and-verify` 增 §六（Windows 非交互调用：禁管道、Python subprocess、尾注负差判读）。
- **判定**：`UCHARTS_FORMATTER_ERROR_BEFORE=2 / AFTER=0`；`UCHARTS_RUNTIME_FIX=PASS`；
  `PROJECT_FINAL_SEAL = PASS`（REOPENED_FOR_BUGFIX → PASS）。
- **待需求方人工**：微信开发者工具重开「数据报告」页 → Console 过滤 `formatter` 应为 **0 条**。
"""

CUR_ANCHOR = u'_bug_final_verify.py`（最终只读复核）。'

CUR_APPEND = u"""

## 八、uCharts 饼/环图 series 结构（BUGFIX-02 沉淀，2026-10-02）

- **铁律**：uCharts v2.5.0 的 **pie / ring / mount / rose / funnel**，`series[0].data` 必须是
  **对象数组** `[{ name, value }]`；传**纯数值数组**（如 `[50]`）会让库内 `fixPieSeries`
  执行 `oldseries[i].formatter = ...` ⇒ `MiniProgramError: Cannot create property 'formatter' on number '50'`。
  `fixPieSeries` 仅对上述 5 种 type 调用 ⇒ **line / column / area 用数值数组才是正确格式，别顺手改**。
- **唯一使用点**：全项目图表**只在** `miniapp/pages/report/index.vue`（共 6 张，其中 ring 2 张需对象数组）。
- **禁改第三方库**：不得在 `components/u-charts/u-charts.js` 内加 `typeof === 'number'` 掩盖；只改调用方数据结构。
- **无头验证资产**：`tests/security/_ucharts_fix_verify.js`（结构 12/12）· `_ucharts_build_verify.py`
  （HBuilderX 重编译 + 产物锚点，旧结构残留 0）· `_ucharts_dist_symbol_check.py`（`node --check` + 符号完整性）·
  `_ucharts_build_determinism.py`（run1/run2 = 106/106 逐字节一致）。
- **文档**：封板报告追加 **§十四**；当日日志 `memory/2026-10-02.md`。
- **判定**：`UCHARTS_FORMATTER_ERROR_BEFORE=2 / AFTER=0`；`UCHARTS_RUNTIME_FIX=PASS`；
  `PROJECT_FINAL_SEAL = PASS`（REOPENED_FOR_BUGFIX → PASS）。
- **构建/打开路径**：HBuilderX `cli.exe` 在 `C:/Users/Toporder-WS/Downloads/HBuilderX.5.24.2026081301/HBuilderX`；
  微信开发者工具直接打开 `miniapp/unpackage/dist/dev/mp-weixin`（该目录含 `project.config.json`）。
- ⚠️ 本文件已超注入上限（约 12.5 KB），**建议尽快做「判据 + 指针」式精简拆分**。
"""


def main():
    apply_ = '--apply' in sys.argv
    print('==== 记忆写入 (%s) ====' % ('APPLY' if apply_ else 'DRY-RUN'))

    # 1) 当日日志（新建）
    print('== 日志 %s  已存在=%s' % (os.path.basename(LOG), os.path.exists(LOG)))
    if not apply_:
        print('   [dry-run] 将写入 %d 字节' % len(LOG_TEXT.encode('utf-8')))
    else:
        with io.open(LOG, 'wb') as f:
            f.write(LOG_TEXT.encode('utf-8'))
        print('   已写入 %d 字节' % os.path.getsize(LOG))

    # 2) MEMORY.md 追加 §八
    raw = open(CUR, 'rb').read()
    text = raw.decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    hit = text.count(CUR_ANCHOR)
    print('== MEMORY.md %d 字节 (%s)  锚点命中=%d  已有§八=%s'
          % (len(raw), 'CRLF' if nl == '\r\n' else 'LF', hit, '## 八' in text))
    if hit != 1 or u'## 八' in text:
        print('   !! 守卫未通过，MEMORY.md 不改')
        return 1
    new_text = text + CUR_APPEND.replace('\n', nl)
    if not new_text.endswith(nl):
        new_text += nl
    if not apply_:
        print('   [dry-run] 将追加 +%d 字节' % (len(new_text.encode('utf-8')) - len(raw)))
    else:
        with io.open(CUR, 'wb') as f:
            f.write(new_text.encode('utf-8'))
        print('   已追加，新字节数 %d' % os.path.getsize(CUR))
    return 0


if __name__ == '__main__':
    sys.exit(main())
