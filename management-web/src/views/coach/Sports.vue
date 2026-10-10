<template>
  <div class="hms-page">
    <div class="hms-card">
      <div class="hms-card__title">
        <span>学员运动数据（只读）</span>
        <span class="hms-muted">原始运动数据由学员自行录入，教练仅可查看</span>
      </div>

      <div class="hms-filter hms-mb-12">
        <PatientSelect v-model="query.user_id" role="coach" placeholder="选择学员" style="width: 220px" />
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 260px"
        />
        <el-select v-model="query.sport_type" placeholder="运动类型" clearable style="width: 140px">
          <el-option v-for="t in SPORT_TYPES" :key="t" :label="t" :value="t" />
        </el-select>
        <el-button type="primary" @click="search">查询</el-button>
        <el-button @click="reset">重置</el-button>
      </div>

      <el-empty v-if="!query.user_id" description="请先选择学员" />
      <template v-else>
        <el-table :data="list" v-loading="loading" stripe>
          <el-table-column prop="sport_date" label="日期" width="120" />
          <el-table-column prop="sport_type" label="运动类型" width="120" />
          <el-table-column prop="sport_duration" label="时长(分钟)" width="120" />
          <el-table-column prop="calorie" label="卡路里" width="100" />
          <el-table-column prop="remark" label="备注" min-width="180" />
          <el-table-column prop="created_at" label="录入时间" min-width="180" />
        </el-table>

        <div class="hms-pagination">
          <el-pagination
            v-model:current-page="query.page"
            v-model:page-size="query.page_size"
            :total="total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @current-change="load"
            @size-change="search"
          />
        </div>
      </template>
    </div>

    <template v-if="query.user_id">
      <div class="hms-stat-grid">
        <StatCard label="运动总时长(分钟)" :value="summary.total_sport_minutes || 0" icon="Stopwatch" :gradient="g.blue" />
        <StatCard label="消耗卡路里" :value="summary.total_calorie || 0" icon="Odometer" :gradient="g.orange" />
        <StatCard label="平均体重(kg)" :value="summary.avg_weight ?? '-'" icon="User" :gradient="g.purple" />
        <StatCard label="平均睡眠(分钟)" :value="summary.avg_sleep_minutes || 0" icon="Moon" :gradient="g.cyan" />
      </div>

      <div class="hms-grid-2">
        <div class="hms-card">
          <div class="hms-card__title"><span>运动时长趋势</span></div>
          <ChartBox :option="dayOption" :height="260" />
        </div>
        <div class="hms-card">
          <div class="hms-card__title"><span>运动类型分布</span></div>
          <ChartBox :option="typeOption" :height="260" />
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import ChartBox from '@/components/ChartBox.vue'
import PatientSelect from '@/components/PatientSelect.vue'
import StatCard from '@/components/StatCard.vue'
import { coachApi } from '@/api/coach'

const SPORT_TYPES = ['跑步', '快走', '骑行', '游泳', '瑜伽', '力量训练', '球类', '其他']

const route = useRoute()
const loading = ref(false)
const list = ref([])
const total = ref(0)
const dateRange = ref([])
const stats = ref({ summary: {}, sport_daily: [], sport_by_type: [] })

const query = reactive({ user_id: '', page: 1, page_size: 10, sport_type: '' })

const g = {
  blue: 'linear-gradient(135deg, #1E6FFF 0%, #4FA3FF 100%)',
  orange: 'linear-gradient(135deg, #F5872A 0%, #FFAE5C 100%)',
  purple: 'linear-gradient(135deg, #7A5AF8 0%, #A98BFF 100%)',
  cyan: 'linear-gradient(135deg, #17A2B8 0%, #4FD1E0 100%)',
}

const summary = computed(() => stats.value.summary || {})

const dayOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 46, right: 18, top: 24, bottom: 30 },
  xAxis: {
    type: 'category',
    data: (stats.value.sport_daily || []).map((i) => i.date.slice(5)),
    axisLine: { lineStyle: { color: '#dfe6ef' } },
    axisLabel: { color: '#8794a8' },
  },
  yAxis: { type: 'value', splitLine: { lineStyle: { color: '#f0f3f8' } }, axisLabel: { color: '#8794a8' } },
  series: [
    {
      name: '运动时长(分钟)',
      type: 'bar',
      barWidth: 16,
      data: (stats.value.sport_daily || []).map((i) => i.duration),
      itemStyle: { borderRadius: [5, 5, 0, 0], color: '#1E6FFF' },
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
      data: (stats.value.sport_by_type || []).map((i) => ({ name: i.name, value: i.value })),
    },
  ],
}))

async function load() {
  if (!query.user_id) {
    list.value = []
    total.value = 0
    return
  }
  loading.value = true
  try {
    const { data } = await coachApi.studentSportData({
      user_id: query.user_id,
      page: query.page,
      page_size: query.page_size,
      sport_type: query.sport_type,
      start_date: dateRange.value?.[0],
      end_date: dateRange.value?.[1],
    })
    list.value = data.list || []
    total.value = data.total || 0
  } catch (e) {
    list.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  if (!query.user_id) {
    stats.value = { summary: {}, sport_daily: [], sport_by_type: [] }
    return
  }
  try {
    const { data } = await coachApi.studentStatistics(query.user_id, 30)
    stats.value = data
  } catch (e) {
    stats.value = { summary: {}, sport_daily: [], sport_by_type: [] }
  }
}

function search() {
  query.page = 1
  load()
}

function reset() {
  dateRange.value = []
  query.sport_type = ''
  query.page = 1
  load()
}

watch(
  () => query.user_id,
  () => {
    search()
    loadStats()
  }
)

onMounted(() => {
  if (route.query.user_id) {
    query.user_id = Number(route.query.user_id)
  } else {
    load()
  }
})
</script>
