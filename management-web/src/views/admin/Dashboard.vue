<template>
  <div class="hms-page">
    <!-- 统计卡 -->
    <div class="hms-stat-grid">
      <StatCard label="普通用户总数" :value="stats.user_count" icon="User" :gradient="grad.blue" />
      <StatCard label="医生总数" :value="stats.doctor_count" icon="FirstAidKit" :gradient="grad.green" />
      <StatCard label="健身教练总数" :value="stats.coach_count" icon="Basketball" :gradient="grad.cyan" />
      <StatCard label="今日新增用户" :value="stats.today_user_count" icon="Plus" :gradient="grad.purple" />
      <StatCard label="今日新增健康记录" :value="stats.today_health_count" icon="DataLine" :gradient="grad.indigo" />
      <StatCard label="待审核医生" :value="stats.pending_doctor" icon="Warning" :gradient="grad.orange" />
      <StatCard label="待审核教练" :value="stats.pending_coach" icon="Warning" :gradient="grad.red" />
      <StatCard label="进行中健康计划" :value="stats.running_plan" icon="List" :gradient="grad.teal" />
      <StatCard label="健康科普文章" :value="stats.article_count" icon="Document" :gradient="grad.slate" />
      <StatCard label="今日运动记录" :value="stats.today_sport_count" icon="Stopwatch" :gradient="grad.lime" />
    </div>

    <!-- 快捷待办 -->
    <div class="hms-grid-2">
      <div class="hms-card">
        <div class="hms-card__title">
          <span>待审核医生</span>
          <el-button link type="primary" @click="router.push('/admin/audit')">进入审核中心</el-button>
        </div>
        <el-table :data="pendingDoctors" size="small" v-loading="loading" empty-text="暂无待审核医生">
          <el-table-column prop="doctor_name" label="账号" width="120" />
          <el-table-column prop="real_name" label="姓名" width="100" />
          <el-table-column prop="specialty" label="专业方向" min-width="120" />
          <el-table-column prop="created_at" label="申请时间" width="170" />
        </el-table>
      </div>

      <div class="hms-card">
        <div class="hms-card__title">
          <span>待审核教练</span>
          <el-button link type="primary" @click="router.push('/admin/audit')">进入审核中心</el-button>
        </div>
        <el-table :data="pendingCoaches" size="small" v-loading="loading" empty-text="暂无待审核教练">
          <el-table-column prop="coach_name" label="账号" width="120" />
          <el-table-column prop="real_name" label="姓名" width="100" />
          <el-table-column prop="specialty" label="专业方向" min-width="120" />
          <el-table-column prop="created_at" label="申请时间" width="170" />
        </el-table>
      </div>

      <div class="hms-card">
        <div class="hms-card__title">
          <span>最新注册用户</span>
          <el-button link type="primary" @click="router.push('/admin/users')">用户管理</el-button>
        </div>
        <el-table :data="latestUsers" size="small" v-loading="loading" empty-text="暂无数据">
          <el-table-column label="用户" min-width="140">
            <template #default="{ row }">
              <div class="cell-user">
                <img class="hms-avatar" :src="resolveFileUrl(row.avatar)" alt="avatar" />
                <span>{{ row.nickname }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="phone" label="手机号" width="130" />
          <el-table-column prop="gender" label="性别" width="70" />
          <el-table-column prop="created_at" label="注册时间" width="170" />
        </el-table>
      </div>

      <div class="hms-card">
        <div class="hms-card__title">
          <span>最近系统操作</span>
          <el-button link type="primary" @click="router.push('/admin/system')">系统管理</el-button>
        </div>
        <el-table :data="latestLogs" size="small" v-loading="loading" empty-text="暂无操作日志">
          <el-table-column prop="admin_name" label="管理员" width="100" />
          <el-table-column prop="operation_type" label="操作类型" width="130" />
          <el-table-column prop="operation_content" label="操作内容" min-width="220" show-overflow-tooltip />
          <el-table-column prop="created_at" label="时间" width="170" />
        </el-table>
      </div>
    </div>

    <!-- 图表 -->
    <div class="hms-grid-2">
      <div class="hms-card">
        <div class="hms-card__title"><span>最近 7 天新增用户趋势</span></div>
        <ChartBox :option="userTrendOption" :height="260" />
      </div>
      <div class="hms-card">
        <div class="hms-card__title"><span>最近 7 天健康数据录入趋势</span></div>
        <ChartBox :option="healthTrendOption" :height="260" />
      </div>
      <div class="hms-card">
        <div class="hms-card__title"><span>睡眠质量分布</span></div>
        <ChartBox :option="sleepOption" :height="260" />
      </div>
      <div class="hms-card">
        <div class="hms-card__title"><span>运动类型分布（时长分钟）</span></div>
        <ChartBox :option="sportOption" :height="260" />
      </div>
      <div class="hms-card">
        <div class="hms-card__title"><span>健康计划状态分布</span></div>
        <ChartBox :option="planOption" :height="260" />
      </div>
      <div class="hms-card">
        <div class="hms-card__title"><span>最近 30 天运动时长趋势</span></div>
        <ChartBox :option="sport30Option" :height="260" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import ChartBox from '@/components/ChartBox.vue'
import StatCard from '@/components/StatCard.vue'
import { adminApi } from '@/api/admin'
import { resolveFileUrl } from '@/utils/config'

const router = useRouter()
const loading = ref(false)

const stats = ref({
  user_count: 0,
  doctor_count: 0,
  coach_count: 0,
  today_user_count: 0,
  today_health_count: 0,
  pending_doctor: 0,
  pending_coach: 0,
  running_plan: 0,
  article_count: 0,
  today_sport_count: 0,
})
const userTrend = ref([])
const healthTrend = ref([])
const sleepDist = ref([])
const sportDist = ref([])
const planDist = ref([])
const sport30 = ref([])
const pendingDoctors = ref([])
const pendingCoaches = ref([])
const latestUsers = ref([])
const latestLogs = ref([])

const grad = {
  blue: 'linear-gradient(135deg, #1B3A6B 0%, #2F5DA8 100%)',
  green: 'linear-gradient(135deg, #0F9D8C 0%, #2BC4AE 100%)',
  cyan: 'linear-gradient(135deg, #17A2B8 0%, #4FD1E0 100%)',
  purple: 'linear-gradient(135deg, #7A5AF8 0%, #A98BFF 100%)',
  indigo: 'linear-gradient(135deg, #3B5BDB 0%, #748FFC 100%)',
  orange: 'linear-gradient(135deg, #F5872A 0%, #FFAE5C 100%)',
  red: 'linear-gradient(135deg, #E4572E 0%, #FF8A65 100%)',
  teal: 'linear-gradient(135deg, #0B7A6D 0%, #25A99A 100%)',
  slate: 'linear-gradient(135deg, #5B6B85 0%, #8A9BB5 100%)',
  lime: 'linear-gradient(135deg, #5C940D 0%, #94C748 100%)',
}

const axisBase = {
  axisLine: { lineStyle: { color: '#dfe6ef' } },
  axisLabel: { color: '#8794a8' },
}
const gridBase = { left: 46, right: 18, top: 24, bottom: 30 }

const userTrendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: gridBase,
  xAxis: { type: 'category', data: userTrend.value.map((i) => i.date.slice(5)), ...axisBase },
  yAxis: { type: 'value', splitLine: { lineStyle: { color: '#f0f3f8' } }, axisLabel: { color: '#8794a8' } },
  series: [
    {
      name: '新增用户',
      type: 'line',
      smooth: true,
      symbolSize: 7,
      data: userTrend.value.map((i) => i.value),
      itemStyle: { color: '#1B3A6B' },
      areaStyle: { color: 'rgba(27,58,107,0.12)' },
    },
  ],
}))

const healthTrendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['健康指标', '睡眠记录', '运动记录'], right: 0, textStyle: { color: '#6b7a90' } },
  grid: { ...gridBase, top: 34 },
  xAxis: { type: 'category', data: healthTrend.value.map((i) => i.date.slice(5)), ...axisBase },
  yAxis: { type: 'value', splitLine: { lineStyle: { color: '#f0f3f8' } }, axisLabel: { color: '#8794a8' } },
  series: [
    { name: '健康指标', type: 'bar', barWidth: 10, data: healthTrend.value.map((i) => i.health), itemStyle: { color: '#2F5DA8', borderRadius: [4, 4, 0, 0] } },
    { name: '睡眠记录', type: 'bar', barWidth: 10, data: healthTrend.value.map((i) => i.sleep), itemStyle: { color: '#17A2B8', borderRadius: [4, 4, 0, 0] } },
    { name: '运动记录', type: 'bar', barWidth: 10, data: healthTrend.value.map((i) => i.sport), itemStyle: { color: '#F5872A', borderRadius: [4, 4, 0, 0] } },
  ],
}))

const sleepOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0, textStyle: { color: '#6b7a90' } },
  series: [
    {
      name: '睡眠质量',
      type: 'pie',
      radius: ['40%', '66%'],
      center: ['50%', '44%'],
      itemStyle: { borderColor: '#fff', borderWidth: 2 },
      data: sleepDist.value,
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
      roseType: 'radius',
      radius: ['30%', '68%'],
      center: ['50%', '44%'],
      itemStyle: { borderColor: '#fff', borderWidth: 2 },
      data: sportDist.value,
    },
  ],
}))

const planOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0, textStyle: { color: '#6b7a90' } },
  series: [
    {
      name: '健康计划',
      type: 'pie',
      radius: ['46%', '68%'],
      center: ['50%', '44%'],
      label: { formatter: '{b}\n{c}' },
      itemStyle: { borderColor: '#fff', borderWidth: 2 },
      data: planDist.value,
    },
  ],
}))

const sport30Option = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: gridBase,
  xAxis: {
    type: 'category',
    data: sport30.value.map((i) => i.date.slice(5)),
    axisLine: { lineStyle: { color: '#dfe6ef' } },
    axisLabel: { color: '#8794a8', interval: 4 },
  },
  yAxis: { type: 'value', splitLine: { lineStyle: { color: '#f0f3f8' } }, axisLabel: { color: '#8794a8' } },
  series: [
    {
      name: '运动时长(分钟)',
      type: 'bar',
      barWidth: 8,
      data: sport30.value.map((i) => i.value),
      itemStyle: { borderRadius: [3, 3, 0, 0], color: '#3B5BDB' },
    },
  ],
}))

async function load() {
  loading.value = true
  try {
    const { data } = await adminApi.dashboard()
    stats.value = data.stats || stats.value
    userTrend.value = data.user_trend || []
    healthTrend.value = data.health_trend || []
    sleepDist.value = data.sleep_distribution || []
    sportDist.value = data.sport_distribution || []
    planDist.value = data.plan_distribution || []
    sport30.value = data.sport_30_trend || []
    pendingDoctors.value = data.pending_doctors || []
    pendingCoaches.value = data.pending_coaches || []
    latestUsers.value = data.latest_users || []
    latestLogs.value = data.latest_logs || []
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
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
