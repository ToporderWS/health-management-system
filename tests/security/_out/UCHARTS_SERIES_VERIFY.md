# uCharts 饼/环图 series 结构回归验证（无头 Node harness）

| 用例 | 预期 | 实际 | 结果 | 异常信息 |
| --- | --- | --- | --- | --- |
| 旧结构 ring: series=[{name,data:[50]}]（应报 formatter 错误） | 抛错 | 抛错 | PASS | Cannot create property 'formatter' on number '50' |
| 旧结构 ring: series=[{name,data:[1]}]（应报 formatter 错误） | 抛错 | 抛错 | PASS | Cannot create property 'formatter' on number '1' |
| 新结构 ring 运动类型分布（真实数据 50） | 不抛错 | 不抛错 | PASS | - |
| 新结构 ring 睡眠质量占比（真实数据 1） | 不抛错 | 不抛错 | PASS | - |
| 新结构 ring 多分片（3 段） | 不抛错 | 不抛错 | PASS | - |
| 新结构 ring 全 0 值（count=0 分支） | 不抛错 | 不抛错 | PASS | - |
| 新结构 pie 单分片 | 不抛错 | 不抛错 | PASS | - |
| line（体重趋势） | 不抛错 | 不抛错 | PASS | - |
| line（血压双系列） | 不抛错 | 不抛错 | PASS | - |
| column（运动时长按天） | 不抛错 | 不抛错 | PASS | - |
| area（睡眠时长趋势） | 不抛错 | 不抛错 | PASS | - |
| updateData 增量刷新 ring | 不抛错 | 不抛错 | PASS | - |

TOTAL = 12  PASS = 12  FAIL = 0