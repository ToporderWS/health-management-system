<template>
  <div class="hms-page">
    <div class="hms-card">
      <div class="hms-card__title"><span>患者健康趋势</span></div>
      <div class="hms-filter">
        <PatientSelect v-model="userId" role="doctor" placeholder="选择患者" style="width: 240px" />
        <el-select v-model="days" style="width: 140px">
          <el-option label="最近 30 天" :value="30" />
          <el-option label="最近 14 天" :value="14" />
          <el-option label="最近 7 天" :value="7" />
        </el-select>
        <el-button type="primary" :loading="loading" @click="load">查询</el-button>
      </div>
    </div>

    <el-empty v-if="!userId" description="请先选择患者，查看其真实健康趋势" />

    <template v-else>
      <div class="hms-stat-grid">
        <StatCard label="平均体重(kg)" :value="summary.avg_weight ?? '-'" icon="Odometer" :gradient="g.green" />
        <StatCard label="运动总时长(分钟)" :value="summary.total_sport_minutes || 0" icon="Stopwatch" :gradient="g.blue" />
        <StatCard label="平均睡眠(分钟)" :value="summary.avg_sleep_minutes || 0" icon="Moon" :gradient="g.purple" />
        <StatCard label="健康指标记录条数" :value="summary.record_count || 0" icon="DataLine" :gradient="g.orange" />
      </div>

      <div class="hms-grid-2">
        <div class="hms-card" v-loading="loading">
          <div class="hms-card__title"><span>体重趋势</span></div>
          <ChartBox :option="weightOption" :height="260" />
        </div>
        <div class="hms-card" v-loading="loading">
          <div class="hms-card__title"><span>血压趋势</span></div>
          <ChartBox :option="bpOption" :height="260" />
        </div>
        <div class="hms-card" v-loading="loading">
          <div class="hms-card__title"><span>睡眠时长趋势</span></div>
          <ChartBox :option="sleepOption" :height="260" />
        </div>
        <div class="hms-card" v-loading="loading">
          <div class="hms-card__title"><span>运动类型分布（分钟）</span></div>
          <ChartBox :option="sportOption" :height="260" />
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import ChartBox from '@/components/ChartBox.vue'
import PatientSelect from '@/components/PatientSelect.vue'
import StatCard from '@/components/StatCard.vue'
import { doctorApi } from '@/api/doctor'

const route = useRoute()
const userId = ref('')
const days = ref(30)
const loading = ref(false)
const summary = ref({})
const data = ref({ weight_trend: [], blood_pressure_trend: [], sleep_trend: [], sport_by_type: [] })

const g = {
  green: 'linear-gradient(135deg, #0F9D8C 0%, #2BC4AE 100%)',
  blue: 'linear-gradient(135deg, #2F6BFF 0%, #5E9BFF 100%)',
  purple: 'linear-gradient(135deg, #7A5AF8 0%, #A98BFF 100%)',
  orange: 'linear-gradient(135deg, #F5872A 0%, #FFAE5C 100%)',
}

const axisBase = {
  axisLine: { lineStyle: { color: '#dfe6ef' } },
  axisLabel: { color: '#8794a8' },
}

const weightOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 46, right: 18, top: 24, bottom: 30 },
  xAxis: { type: 'category', data: data.value.weight_trend.map((i) => i.date.slice(5)), ...axisBase },
  yAxis: { type: 'value', scale: true, splitLine: { lineStyle: { color: '#f0f3f8' } }, axisLabel: { color: '#8794a8' } },
  series: [
    {
      name: '体重(kg)',
      type: 'line',
      smooth: true,
      symbolSize: 6,
      data: data.value.weight_trend.map((i) => i.weight),
      itemStyle: { color: '#0F9D8C' },
      areaStyle: { color: 'rgba(15,157,140,0.12)' },
    },
  ],
}))

const bpOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['收缩压', '舒张压'], right: 0, textStyle: { color: '#6b7a90' } },
  grid: { left: 46, right: 18, top: 34, bottom: 30 },
  xAxis: { type: 'category', data: data.value.blood_pressure_trend.map((i) => i.date.slice(5)), ...axisBase },
  yAxis: { type: 'value', scale: true, splitLine: { lineStyle: { color: '#f0f3f8' } }, axisLabel: { color: '#8794a8' } },
  series: [
    { name: '收缩压', type: 'line', smooth: true, data: data.value.blood_pressure_trend.map((i) => i.high), itemStyle: { color: '#E4572E' } },
    { name: '舒张压', type: 'line', smooth: true, data: data.value.blood_pressure_trend.map((i) => i.low), itemStyle: { color: '#2F6BFF' } },
  ],
}))

const sleepOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 46, right: 18, top: 24, bottom: 30 },
  xAxis: { type: 'category', data: data.value.sleep_trend.map((i) => i.date.slice(5)), ...axisBase },
  yAxis: { type: 'value', splitLine: { lineStyle: { color: '#f0f3f8' } }, axisLabel: { color: '#8794a8' } },
  series: [
    {
      name: '睡眠(分钟)',
      type: 'bar',
      barWidth: 16,
      data: data.value.sleep_trend.map((i) => i.duration),
      itemStyle: { borderRadius: [5, 5, 0, 0], color: '#7A5AF8' },
    },
  ],
}))

const sportOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0, textStyle: { color: '#6b7a90' } },
  series: [
    {
      name: '运动时长(分钟)',
      type: 'pie',
      radius: ['42%', '68%'],
      center: ['50%', '44%'],
      itemStyle: { borderColor: '#fff', borderWidth: 2 },
      data: data.value.sport_by_type.map((i) => ({ name: i.name, value: i.value })),
    },
  ],
}))

async function load() {
  if (!userId.value) return
  loading.value = true
  try {
    const res = await doctorApi.patientTrend(userId.value, days.value)
    data.value = res.data
    summary.value = res.data.summary || {}
  } catch (e) {
    /* 未绑定关系会返回 401，由拦截器提示 */
  } finally {
    loading.value = false
  }
}

watch(() => queryKey(), load)
function queryKey() {
  return `${userId.value}-${days.value}`
}

onMounted(() => {
  if (route.query.user_id) {
    userId.value = Number(route.query.user_id)
  }
})
</script>
