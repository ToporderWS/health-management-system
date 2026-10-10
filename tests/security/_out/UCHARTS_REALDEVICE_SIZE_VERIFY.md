# uCharts 真机 canvas 尺寸回归验证（无头 Node harness）

模拟设备：1080×2400 / DPR=3 / 逻辑宽 360px；
650rpx=312px · 380rpx=182px · 420rpx=201px

| 用例 | 结果 | 明细 |
| --- | --- | --- |
| 复现-旧配置 ring 圆心越界（画布 312×182） | PASS | center=(468,230) r=188 maxAbs=656 |
| 复现-旧配置字号被放大到 DPR 倍（maxFont > 20） | PASS | maxFont=36 |
| 修复-体重趋势(line/1点) 可见绘制坐标不越界 | PASS | maxAbs=300 bound=312x182 texts=7 |
| 修复-字号为 CSS px（maxFont 11~14） | PASS | maxFont=12 |
| 修复-ring 圆心在画布内且半径合理 | PASS | center=(156,77) r=63 bound=312x201 |
| 修复-单分类 ring(球类=50) 画满 2π | PASS | sweep=6.2832 |
| 修复-单分类 ring(一般=1) 画满 2π | PASS | sweep=6.2832 |
| 不抛错且已绘制-体重趋势 line 1 点 | PASS | texts=7 arcs=1 |
| 不抛错且已绘制-体重趋势 line 2 点 | PASS | texts=8 arcs=2 |
| 不抛错且已绘制-血压趋势 line 1 点双序列 | PASS | texts=8 arcs=2 |
| 不抛错且已绘制-运动时长 column 1 点 | PASS | texts=7 arcs=4 |
| 不抛错且已绘制-运动时长 column 3 点 | PASS | texts=9 arcs=12 |
| 不抛错且已绘制-运动类型 ring 1 分类 | PASS | texts=1 arcs=3 |
| 不抛错且已绘制-运动类型 ring 3 分类 | PASS | texts=3 arcs=7 |
| 不抛错且已绘制-睡眠质量 ring 1 分类 | PASS | texts=1 arcs=3 |
| 不抛错且已绘制-睡眠时长 area 1 点 | PASS | texts=7 arcs=1 |
| 哨兵-旧结构数值数组仍报 formatter 错误 | PASS | EXCEPTION: Cannot create property 'formatter' on number '50' |
| 修复-updateData 增量刷新 ring 不抛错 | PASS | ok |
| 源码-u-charts.vue 不再把 width/height 乘 pixelRatio | PASS | - |
| 源码-u-charts.vue pixelRatio 固定为 1 | PASS | - |
| 源码-u-charts.vue 使用实测尺寸/upx2px 换算（不把 rpx 当 px） | PASS | - |
| 源码-u-charts.vue 显式给出 extra.ring 配置 | PASS | - |
| 源码-u-charts.js 未被修改（第三方库零改动） | PASS | - |
| 源码-report 页保留对象数组 ring 结构 | PASS | - |
| 源码-report 页 ring 已加 value>0 守卫 | PASS | - |
| 源码-report 页线图已过滤空值（0/1/2+ 分支） | PASS | - |
| 源码-report 页单序列图例关闭 | PASS | - |
| 源码-report 页 ring 卡片高度已下调至 420rpx | PASS | - |

TOTAL = 28  PASS = 28  FAIL = 0