<template>
  <div ref="chartRef" :style="{ width: '100%', height: height + 'px' }"></div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  option: { type: Object, default: () => ({}) },
  height: { type: Number, default: 280 },
})

const chartRef = ref(null)
let chart = null

function render() {
  if (!chartRef.value) return
  if (!chart) {
    chart = echarts.init(chartRef.value)
  }
  chart.setOption(props.option || {}, true)
}

function handleResize() {
  chart && chart.resize()
}

onMounted(async () => {
  await nextTick()
  render()
  window.addEventListener('resize', handleResize)
})

watch(
  () => props.option,
  async () => {
    await nextTick()
    render()
  },
  { deep: true }
)

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (chart) {
    chart.dispose()
    chart = null
  }
})
</script>
