=== 1. PRE 基线 ===
  源码文件数 = 14
  dist 文件数 = 106

=== 2. 命令行重新编译（HBuilderX cli.exe launch mp-weixin --compile true） ===
  rc = 0  elapsed = 10.4s
  stdout 尾部：
    14:13:05.108 HBuilderX Version: 5.24
    14:13:05.178 项目 miniapp 开始编译
    14:13:07.927 请注意运行模式下，因日志输出、sourcemap 以及未压缩源码等原因，性能和包体积，均不及发行模式。若要正式发布，请点击发行菜单或使用 cli 发布命令进行发布
    14:13:07.932 编译器版本：5.24（vue3）
    14:13:07.937 正在编译中...
    14:13:07.943 编译会生成大量临时文件，杀毒软件监控时会影响编译速度，并造成CPU升高。推荐把项目目录添加到杀毒软件的监控排除名单中。[添加] [帮助]
    14:13:10.039 [33m​已开启 uni统计 2.0​[39m
    14:13:15.189 项目 miniapp 编译成功。 前端运行日志，请另行在小程序开发工具的控制台查看。如需在 HBuilderX 查看日志输出，可开启运行日志回显，详情：https://uniapp.dcloud.net.cn/tutorial/run/mp-log.html
    14:13:15.208 ready in 9114ms.
    14:13:15.216 [31m已停止运行...[39m

=== 3. POST 快照 + 差异归因 ===
  added = 0  removed = 0  changed = 24  unchanged = 82
  被改动的产物（本批应只有我们改过的页面/组件）：
    changed: dev/mp-weixin/api/index.js                                 delta=-65 B
    changed: dev/mp-weixin/app.js                                       delta=-168 B
    changed: dev/mp-weixin/common/auth.js                               delta=-67 B
    changed: dev/mp-weixin/common/config.js                             delta=-69 B
    changed: dev/mp-weixin/common/image.js                              delta=-68 B
    changed: dev/mp-weixin/common/request.js                            delta=-70 B
    changed: dev/mp-weixin/common/vendor.js                             delta=-17859 B
    changed: dev/mp-weixin/components/u-charts/u-charts.js              delta=-279 B
    changed: dev/mp-weixin/pages/article-detail/index.js                delta=-85 B
    changed: dev/mp-weixin/pages/article/index.js                       delta=-78 B
    changed: dev/mp-weixin/pages/doctor-advice/index.js                 delta=-84 B
    changed: dev/mp-weixin/pages/fitness-advice/index.js                delta=-85 B
    changed: dev/mp-weixin/pages/health-entry/index.js                  delta=-83 B
    changed: dev/mp-weixin/pages/index/index.js                         delta=-76 B
    changed: dev/mp-weixin/pages/login/index.js                         delta=-76 B
    changed: dev/mp-weixin/pages/medical-notice/index.js                delta=-85 B
    changed: dev/mp-weixin/pages/medical-record/index.js                delta=-85 B
    changed: dev/mp-weixin/pages/plan/index.js                          delta=-75 B
    changed: dev/mp-weixin/pages/profile/index.js                       delta=-78 B
    changed: dev/mp-weixin/pages/register/index.js                      delta=-79 B
    changed: dev/mp-weixin/pages/report/index.js                        delta=-77 B
    changed: dev/mp-weixin/pages/sport-goal/index.js                    delta=-81 B
    changed: dev/mp-weixin/pages/training-plan/index.js                 delta=-84 B
    changed: dev/mp-weixin/project.config.json                          delta=-68 B

=== 4. 源码零漂移 ===
  SOURCE_DRIFT = NONE

=== 5. 产物内容锚点 ===
  -- 数据报告页（对象数组 ring / 空值过滤 / 图例） --
    [应有] Number(x.value) > 0                                      hit=2
    [应有] { name: x.name, value: Number(x.value) || 0 }            hit=2
    [应有] const wRows = pick(d.weight_trend                        hit=1
    [应有] const bpRows = pick                                      hit=1
    [应有] const sRows = pick                                       hit=1
    [应有] const stRows = pick                                      hit=1
    [应无] data: (d.sport_by_type || []).map((x) => x.value)        hit=0
    [应无] data: (d.sleep_quality || []).map((x) => x.value)        hit=0
    [应无] data: (d.weight_trend || []).map((x) => x.weight)        hit=0
    [应无] 全树旧 ring 结构残留 = 0
  -- uCharts 组件（真机尺寸：CSS px + pixelRatio 1） --
    [应有] boundingClientRect                                       hit=1
    [应有] uni.upx2px                                               hit=0
    [应有] pixelRatio                                               hit=5
    [应无] cWidth * pixelRatio          hit=0
    [应无] cHeight * pixelRatio         hit=0
    第三方库 u-charts.js 未被修改（oldseries[i].formatter 恰 1 处）= 1
  -- 首页（HTML 实体「更多 ›」/ Hero 间距） --
    [应有] › (更多 ›)              hit=1  |  原 “更多 &gt;” 残留 = 0
    [应有] 26rpx 30rpx 22rpx                                        hit=1
    [应有] font-size: 32rpx                                         hit=2
    [应有] margin-top: 14rpx                                        hit=2
    [应有] font-size: 34rpx                                         hit=1
  -- 头像修复未被回滚 --
    image.js 存在=True 含 downloadFile=True 含 imgSrc=True
    dev/mp-weixin/pages/profile/index.js         走 imgSrc = True
    dev/mp-weixin/pages/index/index.js           走 imgSrc = True
    dev/mp-weixin/pages/index/index.wxml         wxml 含 imgSrc = False
    dev/mp-weixin/pages/article/index.wxml       wxml 含 imgSrc = False

  -- 关键入口存在性 --
    dev/mp-weixin/app.js                             exists=True size=1014
    dev/mp-weixin/app.json                           exists=True size=1763
    dev/mp-weixin/common/vendor.js                   exists=True size=351754
    dev/mp-weixin/common/image.js                    exists=True size=1116
    dev/mp-weixin/components/u-charts/u-charts.js    exists=True size=295413