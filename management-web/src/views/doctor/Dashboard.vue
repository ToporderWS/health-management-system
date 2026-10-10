<template>
  <div class="hms-page">
    <!-- 统计卡 -->
    <div class="hms-stat-grid">
      <StatCard label="负责患者数" :value="stats.patient_count" icon="User" :gradient="grad.green" />
      <StatCard label="今日患者健康记录数" :value="stats.today_record_count" icon="DataLine" :gradient="grad.blue" />
      <StatCard label="需关注健康指标" :value="stats.attention_count" icon="Warning" :gradient="grad.orange" />
      <StatCard label="已发送健康建议" :value="stats.advice_count" icon="ChatDotRound" :gradient="grad.purple" />
      <StatCard label="已发送体检通知" :value="stats.notice_count" icon="Bell" :gradient="grad.cyan" />
      <StatCard label="已创建医疗记录" :value="stats.record_count" icon="Notebook" :gradient="grad.teal" />
    </div>

    <div class="hms-grid-2">
      <div class="hms-card">
        <div class="hms-card__title"><span>患者健康数据录入趋势（最近 7 天）</span></div>
        <ChartBox :option="recordTrendOption" :height="260" />
      </div>
      <div class="hms-card">
        <div class="hms-card__title"><span>患者血压趋势（最近 30 天日均值）</span></div>
        <ChartBox :option="bpTrendOption" :height="260" />
      </div>
      <div class="hms-card">
        <div class="hms-card__title"><span>患者健康记录统计（Top 10）</span></div>
        <ChartBox :option="patientStatOption" :height="260" />
      </div>
      <div class="hms-card">
        <div class="hms-card__title">
          <span>最近患者列表</span>
          <el-button link type="primary" @click="router.push('/doctor/patients')">查看全部</el-button>
        </div>
        <el-table :data="patients" size="small" height="240" v-loading="loading">
          <el-table-column label="患者" min-width="140">
            <template #default="{ row }">
              <div class="cell-user">
                <img class="hms-avatar" :src="resolveFileUrl(row.avatar)" alt="avatar" />
                <span>{{ row.nickname }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="gender" label="性别" width="70" />
          <el-table-column prop="age" label="年龄" width="70" />
          <el-table-column label="操作" width="90">
            <template #default="{ row }">
              <el-button link type="primary" @click="goPatient(row)">查看</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import ChartBox from '@/components/ChartBox.vue'
import StatCard from '@/components/StatCard.vue'
import { doctorApi } from '@/api/doctor'
import { resolveFileUrl } from '@/utils/config'

const router = useRouter()
const loading = ref(false)
const stats = ref({
  patient_count: 0,
  today_record_count: 0,
  attention_count: 0,
  advice_count: 0,
  notice_count: 0,
  record_count: 0,
})
const recordTrend = ref([])
const bpTrend = ref([])
const patientStats = ref([])
const patients = ref([])

const grad = {
  green: 'linear-gradient(135deg, #0F9D8C 0%, #2BC4AE 100%)',
  blue: 'linear-gradient(135deg, #2F6BFF 0%, #5E9BFF 100%)',
  orange: 'linear-gradient(135deg, #F5872A 0%, #FFAE5C 100%)',
  purple: 'linear-gradient(135deg, #7A5AF8 0%, #A98BFF 100%)',
  cyan: 'linear-gradient(135deg, #17A2B8 0%, #4FD1E0 100%)',
  teal: 'linear-gradient(135deg, #0B7A6D 0%, #25A99A 100%)',
}

const recordTrendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 40, right: 16, top: 24, bottom: 30 },
  xAxis: {
    type: 'category',
    data: recordTrend.value.map((i) => i.date.slice(5)),
    axisLine: { lineStyle: { color: '#dfe6ef' } },
    axisLabel: { color: '#8794a8' },
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: '#f0f3f8' } },
    axisLabel: { color: '#8794a8' },
  },
  series: [
    {
      name: '健康记录数',
      type: 'bar',
      barWidth: 18,
      data: recordTrend.value.map((i) => i.value),
      itemStyle: { borderRadius: [5, 5, 0, 0], color: '#0F9D8C' },
    },
  ],
}))

const bpTrendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['收缩压', '舒张压'], right: 0, textStyle: { color: '#6b7a90' } },
  grid: { left: 40, right: 16, top: 34, bottom: 30 },
  xAxis: {
    type: 'category',
    data: bpTrend.value.map((i) => i.date.slice(5)),
    axisLine: { lineStyle: { color: '#dfe6ef' } },
    axisLabel: { color: '#8794a8' },
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: '#f0f3f8' } },
    axisLabel: { color: '#8794a8' },
  },
  series: [
    {
      name: '收缩压',
      type: 'line',
      smooth: true,
      data: bpTrend.value.map((i) => i.high),
      itemStyle: { color: '#E4572E' },
      areaStyle: { color: 'rgba(228,87,46,0.08)' },
    },
    {
      name: '舒张压',
      type: 'line',
      smooth: true,
      data: bpTrend.value.map((i) => i.low),
      itemStyle: { color: '#2F6BFF' },
      areaStyle: { color: 'rgba(47,107,255,0.08)' },
    },
  ],
}))

const patientStatOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 60, right: 20, top: 20, bottom: 30 },
  xAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: '#f0f3f8' } },
    axisLabel: { color: '#8794a8' },
  },
  yAxis: {
    type: 'category',
    data: patientStats.value.map((i) => i.nickname).reverse(),
    axisLine: { lineStyle: { color: '#dfe6ef' } },
    axisLabel: { color: '#8794a8' },
  },
  series: [
    {
      name: '健康记录数',
      type: 'bar',
      barWidth: 14,
      data: patientStats.value.map((i) => i.value).reverse(),
      itemStyle: { borderRadius: [0, 5, 5, 0], color: '#5B8FF9' },
    },
  ],
}))

function goPatient(row) {
  router.push({ path: '/doctor/health', query: { user_id: row.id } })
}

async function load() {
  loading.value = true
  try {
    const { data } = await doctorApi.dashboard()
    stats.value = data.stats || stats.value
    recordTrend.value = data.record_trend || []
    bpTrend.value = data.bp_trend || []
    patientStats.value = data.patient_record_stats || []
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
  try {
    const { data } = await doctorApi.patientList({ page: 1, page_size: 5 })
    patients.value = data.list || []
  } catch (e) {
    /* 拦截器已提示 */
  }
}

onMounted(load)
</script>

<style scoped>
.cell-user {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
