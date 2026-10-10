=== 1. PRE 基线 ===
  源码文件数 = 14
  dist 文件数 = 106

=== 2. 命令行重新编译（HBuilderX cli.exe launch mp-weixin --compile true） ===
  rc = 0  elapsed = 11.7s
  stdout 尾部：
    13:14:04.519 HBuilderX Version: 5.24
    13:14:04.572 项目 miniapp 开始编译
    13:14:07.570 请注意运行模式下，因日志输出、sourcemap 以及未压缩源码等原因，性能和包体积，均不及发行模式。若要正式发布，请点击发行菜单或使用 cli 发布命令进行发布
    13:14:07.592 编译器版本：5.24（vue3）
    13:14:07.620 正在编译中...
    13:14:07.637 编译会生成大量临时文件，杀毒软件监控时会影响编译速度，并造成CPU升高。推荐把项目目录添加到杀毒软件的监控排除名单中。[添加] [帮助]
    13:14:10.216 [33m​已开启 uni统计 2.0​[39m
    13:14:15.862 项目 miniapp 编译成功。 前端运行日志，请另行在小程序开发工具的控制台查看。如需在 HBuilderX 查看日志输出，可开启运行日志回显，详情：https://uniapp.dcloud.net.cn/tutorial/run/mp-log.html
    13:14:15.873 ready in 10483ms.
    13:14:15.881 [31m已停止运行...[39m

=== 3. POST 快照 + 差异归因 ===
  added = 0  removed = 0  changed = 23  unchanged = 83
  关键入口存在性：
    dev/mp-weixin/app.js                       exists=True size=1014
    dev/mp-weixin/app.json                     exists=True size=1763
    dev/mp-weixin/app.wxss                     exists=True size=3765
    dev/mp-weixin/common/vendor.js             exists=True size=351754
    dev/mp-weixin/common/image.js              exists=True size=988
    dev/mp-weixin/pages/report/index.js        exists=True size=6939
    dev/mp-weixin/pages/report/index.wxml      exists=True size=4620
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

=== 4. 源码零漂移 ===
  SOURCE_DRIFT = NONE

=== 5. 产物内容锚点 ===
  [应有] const sportTypes = d.sport_by_type || []                       hit=1
  [应有] const qualities = d.sleep_quality || []                        hit=1
  [应有] { name: x.name, value: Number(x.value) || 0 }                  hit=2
  [应无] series: [{ name: "运动时长", data: (d.sport_by_type || []).map((   hit=0
  [应无] series: [{ name: "次数", data: qualities.map((x) => x.value) }   hit=0
  全树旧结构残留文件数 = 0
  image.js（头像本地化）存在 = True  含 downloadFile = True  含 imgSrc = True
  dev/mp-weixin/pages/profile/index.js 走 imgSrc = True
  dev/mp-weixin/pages/index/index.js 走 imgSrc = True