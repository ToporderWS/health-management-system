=== A. 编译 #2 前快照 ===
  files = 106

=== B. 第二次命令行编译 ===
  rc = 0  elapsed = 9.4s
    14:13:48.719 正在编译中...
    14:13:48.745 编译会生成大量临时文件，杀毒软件监控时会影响编译速度，并造成CPU升高。推荐把项目目录添加到杀毒软件的监控排除名单中。[添加] [帮助]
    14:13:50.344 [33m​已开启 uni统计 2.0​[39m
    14:13:55.691 项目 miniapp 编译成功。 前端运行日志，请另行在小程序开发工具的控制台查看。如需在 HBuilderX 查看日志输出，可开启运行日志回显，详情：https://uniapp.dcloud.net.cn/tutorial/run/mp-log.html
    14:13:55.713 ready in 8531ms.
    14:13:55.718 [31m已停止运行...[39m

=== C. 逐字节一致性 ===
  一致 = 106 / 106
  不一致 = NONE
  BUILD_DETERMINISM = PASS

=== D. 产物体积差异归因（sourceMappingURL / 内联 sourcemap / uni 统计标记） ===
  common/vendor.js                           size=351754   sourceMappingURL=0  longComment(>200)=0
  pages/report/index.js                      size=7667     sourceMappingURL=0  longComment(>200)=0
  components/u-charts/u-charts.js            size=295413   sourceMappingURL=0  longComment(>200)=0
  dist/.sourcemap 文件数 = 0
  说明：dev 构建的 sourcemap 走独立目录；上面统计的产物内 sourceMappingURL 计数即"是否内联"。