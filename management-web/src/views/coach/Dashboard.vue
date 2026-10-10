<template>
  <div class="hms-page">
    <div class="hms-stat-grid">
      <StatCard label="负责学员数量" :value="stats.student_count" icon="User" :gradient="grad.blue" />
      <StatCard label="今日运动人数" :value="stats.today_sport_user" icon="Basketball" :gradient="grad.cyan" />
      <StatCard label="本月运动总时长(分钟)" :value="stats.month_duration" icon="Stopwatch" :gradient="grad.purple" />
      <StatCard label="进行中训练计划" :value="stats.running_plan" icon="Calendar" :gradient="grad.orange" />
      <StatCard label="运动目标总数" :value="stats.goal_count" icon="Aim" :gradient="grad.green" />
      <StatCard label="已发送健身建议" :value="stats.advice_count" icon="ChatDotRound" :gradient="grad.indigo" />
    </div>

    <div class="hms-card">
      <div class="hms-card__title"><span>最近 7 天运动时长（分钟）</span></div>
      <ChartBox :option="durationOption" :height="280" />
    </div>

    <div class="hms-grid-2">
      <div class="hms-card">
        <div class="hms-card__title"><span>本月运动类型分布</span></div>
        <ChartBox :option="typeOption" :height="280" />
      </div>
      <div class="hms-card">
        <div class="hms-card__title"><span>学员运动趋势（本月时长 Top 10）</span></div>
        <ChartBox :option="studentOption" :height="280" />
      </div>
    </div>

    <div class="hms-card">
      <div class="hms-card__title">
        <span>学员运动明细</span>
        <el-button link type="primary" @click="router.push('/coach/students')">学员管理</el-button>
      </div>
      <el-table :data="studentTrend" v-loading="loading" size="small">
        <el-table-column prop="nickname" label="学员" min-width="150" />
        <el-table-column prop="duration" label="本月运动时长(分钟)" width="180" />
        <el-table-column prop="calorie" label="本月消耗卡路里" width="170" />
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import ChartBox from '@/components/ChartBox.vue'
import StatCard from '@/components/StatCard.vue'
import { coachApi } from '@/api/coach'

const router = useRouter()
const loading = ref(false)
const stats = ref({
  student_count: 0,
  today_sport_user: 0,
  month_duration: 0,
  running_plan: 0,
  goal_count: 0,
  advice_count: 0,
})
const durationTrend = ref([])
const typeDistribution = ref([])
const studentTrend = ref([])

const grad = {
  blue: 'linear-gradient(135deg, #1E6FFF 0%, #4FA3FF 100%)',
  cyan: 'linear-gradient(135deg, #17A2B8 0%, #4FD1E0 100%)',
  purple: 'linear-gradient(135deg, #7A5AF8 0%, #A98BFF 100%)',
  orange: 'linear-gradient(135deg, #F5872A 0%, #FFAE5C 100%)',
  green: 'linear-gradient(135deg, #0F9D8C 0%, #2BC4AE 100%)',
  indigo: 'linear-gradient(135deg, #3B5BDB 0%, #748FFC 100%)',
}

const axisBase = {
  axisLine: { lineStyle: { color: '#dfe6ef' } },
  axisLabel: { color: '#8794a8' },
}

const durationOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 46, right: 18, top: 24, bottom: 30 },
  xAxis: { type: 'category', data: durationTrend.value.map((i) => i.date.slice(5)), ...axisBase },
  yAxis: { type: 'value', splitLine: { lineStyle: { color: '#f0f3f8' } }, axisLabel: { color: '#8794a8' } },
  series: [
    {
      name: '运动时长(分钟)',
      type: 'bar',
      barWidth: 22,
      data: durationTrend.value.map((i) => i.value),
      itemStyle: { borderRadius: [6, 6, 0, 0], color: '#1E6FFF' },
    },
  ],
}))

const typeOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0, textStyle: { color: '#6b7a90' } },
  series: [
    {
      name: '运动时长(分钟)',
      type: 'pie',
      radius: ['40%', '66%'],
      center: ['50%', '44%'],
      itemStyle: { borderColor: '#fff', borderWidth: 2 },
      data: typeDistribution.value.map((i) => ({ name: i.name, value: i.value })),
    },
  ],
}))

const studentOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 70, right: 24, top: 20, bottom: 30 },
  xAxis: { type: 'value', splitLine: { lineStyle: { color: '#f0f3f8' } }, axisLabel: { color: '#8794a8' } },
  yAxis: {
    type: 'category',
    data: studentTrend.value.map((i) => i.nickname).reverse(),
    axisLine: { lineStyle: { color: '#dfe6ef' } },
    axisLabel: { color: '#8794a8' },
  },
  series: [
    {
      name: '运动时长(分钟)',
      type: 'bar',
      barWidth: 14,
      data: studentTrend.value.map((i) => i.duration).reverse(),
      itemStyle: { borderRadius: [0, 6, 6, 0], color: '#4FA3FF' },
    },
  ],
}))

async function load() {
  loading.value = true
  try {
    const { data } = await coachApi.dashboard()
    stats.value = data.stats || stats.value
    durationTrend.value = data.duration_trend || []
    typeDistribution.value = data.type_distribution || []
    studentTrend.value = data.student_trend || []
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
