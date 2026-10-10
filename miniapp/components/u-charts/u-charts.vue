<template>
  <view class="ucharts">
    <canvas
      class="ucharts__canvas"
      :id="canvasId"
      :canvas-id="canvasId"
      :style="canvasStyle"
      @touchstart="onTouch"
    ></canvas>
  </view>
</template>

<script setup>
/**
 * uCharts 原生组件封装（uni-app 非 npm 工程手动引入方式）
 * - 底层为官方 uCharts 2.5.0（components/u-charts/u-charts.js，**未做任何修改**）
 * - 统一处理 rpx→px 换算、canvas 实测尺寸、数据更新与点击提示
 * - 图表数据全部来自后端真实接口，组件内不做任何数据造假
 *
 * ⚠️ 真机尺寸铁律（2026-10-02 真机 UI 缺陷修复沉淀，务必保留）
 *
 * 微信小程序【旧版 canvas】（uni.createCanvasContext 创建的）：
 *   1) 绘图**坐标系 = 组件的 CSS 像素尺寸**（不是设备物理像素）；
 *   2) 位图由容器按设备 DPR 自动渲染，**不需要**调用方手动放大。
 * 因此传给 uCharts 的 width/height 必须是 **CSS px**，且 pixelRatio 必须恒为 1。
 *
 * 旧写法（错误）：width = cWidth * pixelRatio、pixelRatio = 系统 DPR
 *   → 库内还会把 fontSize / padding / ringWidth / yAxisWidth / dashLength 等再 * opts.pix，
 *     图形被整体放大 DPR 倍（真机现象：卡片里只剩「巨大坐标数字 + 部分坐标轴」）；
 *   → 饼/环图圆心 (width/2, height/2) 被推到画布外 ⇒ 整个环图区域为空白。
 *
 * 另：严禁把 750rpx 设计稿数值直接当 canvas px 使用，必须经 uni.upx2px / 实测尺寸换算。
 */
import { computed, getCurrentInstance, onMounted, watch, ref } from 'vue'

import uCharts from './u-charts.js'

const props = defineProps({
  // 唯一 canvas 标识；同一页面多个图表必须各不相同
  chartId: { type: String, default: '' },
  // line / column / area / pie / ring
  type: { type: String, default: 'line' },
  // { categories: [], series: [{ name, data }] }
  chartData: { type: Object, default: () => ({ categories: [], series: [] }) },
  // uCharts 额外配置（会与默认配置合并）
  opts: { type: Object, default: () => ({}) },
  // 画布尺寸（rpx），默认适配 750rpx 页面内的卡片宽度
  width: { type: Number, default: 650 },
  height: { type: Number, default: 420 },
  // 数值单位，用于点击提示文案
  unit: { type: String, default: '' },
})

const instance = getCurrentInstance()
const canvasId = ref(props.chartId || 'uc_' + Math.random().toString(36).slice(2, 9))

let chart = null
let ctx = null
let cWidth = 0
let cHeight = 0
// 旧版 canvas：绘图坐标系就是 CSS px，固定 1（详见文件头「真机尺寸铁律」）
const pixelRatio = 1

const canvasStyle = computed(() => `width:${props.width}rpx;height:${props.height}rpx;`)

/** 主题色板：与小程序主色 #2E7D32 / #66BB6A 保持一致 */
const PALETTE = ['#2E7D32', '#66BB6A', '#43A047', '#81C784', '#A5D6A7', '#1B5E20', '#C8E6C9', '#FFB300']

function baseOptions() {
  const isPie = props.type === 'pie' || props.type === 'ring'
  const common = {
    $this: instance.proxy,
    canvasId: canvasId.value,
    type: props.type,
    context: ctx,
    // ⚠️ CSS px（不是设备像素），与 pixelRatio:1 配套，勿改
    width: cWidth,
    height: cHeight,
    pixelRatio,
    fontSize: 12,
    fontColor: '#4A5A6A',
    background: '#FFFFFF',
    animation: true,
    timing: 'easeOut',
    duration: 600,
    color: PALETTE,
    // [上, 右, 下, 左]，单位与坐标系一致（px）
    padding: isPie ? [6, 6, 6, 6] : [18, 12, 6, 6],
    rotate: false,
    errorMessage: '暂无数据',
    dataLabel: false,
    dataPointShape: true,
    enableScroll: false,
    legend: {
      show: true,
      position: 'bottom',
      float: 'center',
      fontSize: 11,
      lineHeight: 18,
      itemGap: 12,
      padding: 3,
      margin: 2,
    },
    xAxis: {
      disableGrid: true,
      fontSize: 11,
      fontColor: '#8A99A8',
      itemCount: 6,
      scrollShow: false,
      axisLine: false,
      axisLineColor: '#DCE6DC',
      labelCount: 6,
    },
    yAxis: {
      gridType: 'dash',
      dashLength: 3,
      gridColor: '#E6F0E7',
      splitNumber: 4,
      fontSize: 11,
      fontColor: '#8A99A8',
      data: [{ min: 0 }],
    },
    extra: {
      line: { type: 'curve', width: 2, activeType: 'hollow' },
      area: { type: 'curve', opacity: 0.22, addLine: true, width: 2 },
      column: { type: 'group', width: 22, barBorderCircle: true, seriesGap: 2, barBorderWidth: 0 },
      // 注意：库内 pie 与 ring 使用**两个独立**的配置键（opts.extra.pie / opts.extra.ring），
      // 只写 pie 时 ring 会退回库默认值，因此两者都要显式给出。
      pie: {
        activeOpacity: 0.6,
        activeRadius: 8,
        offsetAngle: 0,
        labelWidth: 15,
        ringWidth: 32,
        border: true,
        borderWidth: 2,
        borderColor: '#FFFFFF',
        centerColor: '#FFFFFF',
      },
      ring: {
        activeOpacity: 0.6,
        activeRadius: 8,
        offsetAngle: 0,
        labelWidth: 15,
        ringWidth: 32,
        border: true,
        borderWidth: 2,
        borderColor: '#FFFFFF',
        centerColor: '#FFFFFF',
      },
      tooltip: { showBox: true, bgColor: '#1F2D3D', bgOpacity: 0.86, fontSize: 11, fontColor: '#FFFFFF' },
    },
  }
  // 深度合并调用方传入的配置（简单对象足够）
  return merge(common, props.opts || {})
}

function merge(base, extra) {
  const out = Array.isArray(base) ? base.slice() : Object.assign({}, base)
  Object.keys(extra || {}).forEach((k) => {
    const bv = out[k]
    const ev = extra[k]
    if (bv && ev && typeof bv === 'object' && typeof ev === 'object' && !Array.isArray(bv) && !Array.isArray(ev)) {
      out[k] = merge(bv, ev)
    } else {
      out[k] = ev
    }
  })
  return out
}

function hasData(data) {
  if (!data || !data.categories || !data.categories.length) return false
  return Array.isArray(data.series) && data.series.length > 0
}

/** 首次绘制 */
function render() {
  const data = props.chartData || {}
  if (!hasData(data)) {
    // 无数据时清空画布，避免残留上一次图形
    if (ctx) ctx.clearRect(0, 0, cWidth, cHeight)
    if (ctx && typeof ctx.draw === 'function') ctx.draw()
    chart = null
    return
  }
  chart = new uCharts(
    merge(baseOptions(), {
      categories: data.categories,
      series: data.series,
    })
  )
}

/** 数据更新：复用实例，避免闪烁 */
function update() {
  const data = props.chartData || {}
  if (!chart) {
    render()
    return
  }
  if (!hasData(data)) {
    render()
    return
  }
  chart.updateData({ categories: data.categories, series: data.series })
}

function onTouch(e) {
  if (!chart) return
  try {
    chart.touchLegend(e, { animation: false })
    chart.showToolTip(e, {
      format: (item, category) =>
        `${category}：${item.name} ${item.data}${props.unit || ''}`,
    })
  } catch (err) {
    /* 触摸提示失败不影响图形本身 */
  }
}

/**
 * 取得 canvas 的**实测 CSS 尺寸**（px）。
 * 优先用 boundingClientRect 取真实布局尺寸；任何异常/取不到时回落 uni.upx2px(rpx)。
 * 两条路径都返回 CSS px，绝不返回 rpx 原值，也绝不乘 DPR。
 */
function resolveSize(cb) {
  let settled = false
  const finish = (w, h) => {
    if (settled) return
    settled = true
    if (w > 0 && h > 0) {
      cWidth = Math.floor(w)
      cHeight = Math.floor(h)
    } else {
      cWidth = Math.floor(uni.upx2px(props.width))
      cHeight = Math.floor(uni.upx2px(props.height))
    }
    cb()
  }
  try {
    uni
      .createSelectorQuery()
      .in(instance.proxy)
      .select('#' + canvasId.value)
      .boundingClientRect((rect) => {
        if (rect && rect.width && rect.height) finish(rect.width, rect.height)
        else finish(0, 0)
      })
      .exec()
  } catch (e) {
    finish(0, 0)
    return
  }
  // 兜底：极端情况下选择器不回调，也不能让图表一直不画
  setTimeout(() => finish(0, 0), 150)
}

function init() {
  resolveSize(() => {
    ctx = uni.createCanvasContext(canvasId.value, instance.proxy)
    render()
  })
}

onMounted(() => {
  // 等待 canvas 节点渲染完成后再测量并绘制
  setTimeout(init, 60)
})

watch(
  () => props.chartData,
  () => {
    if (!ctx) return
    update()
  },
  { deep: true }
)

watch(
  () => [props.width, props.height],
  () => {
    if (!ctx) return
    cWidth = Math.floor(uni.upx2px(props.width))
    cHeight = Math.floor(uni.upx2px(props.height))
    render()
  }
)
</script>

<style scoped>
.ucharts {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
}

.ucharts__canvas {
  display: block;
}
</style>
