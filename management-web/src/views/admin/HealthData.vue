<template>
  <div class="hms-page">
    <div class="hms-stat-grid">
      <StatCard label="健康指标记录总数" :value="stats.health_total" icon="DataLine" :gradient="g.blue" />
      <StatCard label="睡眠记录总数" :value="stats.sleep_total" icon="Moon" :gradient="g.purple" />
      <StatCard label="运动记录总数" :value="stats.sport_total" icon="Stopwatch" :gradient="g.orange" />
      <StatCard label="今日新增记录数" :value="stats.today_total" icon="Plus" :gradient="g.green" />
    </div>

    <div class="hms-card">
      <el-tabs v-model="activeTab" @tab-change="onTabChange">
        <el-tab-pane label="健康指标" name="health" />
        <el-tab-pane label="睡眠数据" name="sleep" />
        <el-tab-pane label="运动数据" name="sport" />
        <el-tab-pane label="统计分析" name="stat" />
      </el-tabs>

      <template v-if="activeTab !== 'stat'">
        <div class="hms-filter hms-mb-12">
          <el-input v-model="query.keyword" placeholder="昵称 / 手机号" clearable style="width: 190px" @keyup.enter="search" />
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            value-format="YYYY-MM-DD"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 250px"
          />
          <el-select v-if="activeTab === 'sport'" v-model="query.sport_type" placeholder="运动类型" clearable style="width: 140px">
            <el-option v-for="t in SPORT_TYPES" :key="t" :label="t" :value="t" />
          </el-select>
          <el-button type="primary" @click="search">查询</el-button>
          <el-button @click="reset">重置</el-button>
          <el-button type="success" plain :loading="exporting" @click="exportCsv">
            <el-icon><Download /></el-icon>&nbsp;导出 CSV
          </el-button>
        </div>

        <el-table v-if="activeTab === 'health'" :data="list" v-loading="loading" stripe>
          <el-table-column label="用户昵称" min-width="130">
            <template #default="{ row }">{{ row.nickname || '-' }}</template>
          </el-table-column>
          <el-table-column label="手机号" width="140">
            <template #default="{ row }">{{ row.phone || '-' }}</template>
          </el-table-column>
          <el-table-column prop="record_date" label="日期" width="120" />
          <el-table-column prop="weight" label="体重(kg)" width="100" />
          <el-table-column prop="blood_pressure_high" label="收缩压" width="90" />
          <el-table-column prop="blood_pressure_low" label="舒张压" width="90" />
          <el-table-column prop="heart_rate" label="心率" width="80" />
          <el-table-column prop="blood_sugar" label="血糖" width="80" />
          <el-table-column prop="created_at" label="录入时间" min-width="170" />
        </el-table>

        <el-table v-else-if="activeTab === 'sleep'" :data="list" v-loading="loading" stripe>
          <el-table-column label="用户昵称" min-width="130">
            <template #default="{ row }">{{ row.nickname || '-' }}</template>
          </el-table-column>
          <el-table-column label="手机号" width="140">
            <template #default="{ row }">{{ row.phone || '-' }}</template>
          </el-table-column>
          <el-table-column prop="sleep_date" label="日期" width="120" />
          <el-table-column prop="sleep_start" label="入睡" min-width="170" />
          <el-table-column prop="sleep_end" label="起床" min-width="170" />
          <el-table-column label="时长" width="130">
            <template #default="{ row }">{{ formatDuration(row.sleep_duration) }}</template>
          </el-table-column>
          <el-table-column prop="sleep_quality" label="质量" width="90" />
        </el-table>

        <el-table v-else :data="list" v-loading="loading" stripe>
          <el-table-column label="用户昵称" min-width="130">
            <template #default="{ row }">{{ row.nickname || '-' }}</template>
          </el-table-column>
          <el-table-column label="手机号" width="140">
            <template #default="{ row }">{{ row.phone || '-' }}</template>
          </el-table-column>
          <el-table-column prop="sport_date" label="日期" width="120" />
          <el-table-column prop="sport_type" label="运动类型" width="110" />
          <el-table-column prop="sport_duration" label="时长(分钟)" width="110" />
          <el-table-column prop="calorie" label="卡路里" width="90" />
          <el-table-column prop="remark" label="备注" min-width="160" />
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

      <template v-else>
        <div class="hms-grid-2" v-loading="statLoading">
          <div class="hms-card" style="box-shadow: none; margin-bottom: 0">
            <div class="hms-card__title"><span>健康数据录入趋势（最近 7 天）</span></div>
            <ChartBox :option="recordTrendOption" :height="250" />
          </div>
          <div class="hms-card" style="box-shadow: none; margin-bottom: 0">
            <div class="hms-card__title"><span>睡眠质量分布</span></div>
            <ChartBox :option="sleepOption" :height="250" />
          </div>
          <div class="hms-card" style="box-shadow: none; margin-bottom: 0">
            <div class="hms-card__title"><span>运动类型分布（时长分钟）</span></div>
            <ChartBox :option="sportOption" :height="250" />
          </div>
          <div class="hms-card" style="box-shadow: none; margin-bottom: 0">
            <div class="hms-card__title"><span>月度运动总时长</span></div>
            <ChartBox :option="monthOption" :height="250" />
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import ChartBox from '@/components/ChartBox.vue'
import StatCard from '@/components/StatCard.vue'
import { adminApi } from '@/api/admin'
import { saveBlobResponse } from '@/utils/download'
import { formatDuration } from '@/utils/format'

const SPORT_TYPES = ['跑步', '快走', '骑行', '游泳', '瑜伽', '力量训练', '球类', '其他']

const g = {
  blue: 'linear-gradient(135deg, #1B3A6B 0%, #2F5DA8 100%)',
  purple: 'linear-gradient(135deg, #7A5AF8 0%, #A98BFF 100%)',
  orange: 'linear-gradient(135deg, #F5872A 0%, #FFAE5C 100%)',
  green: 'linear-gradient(135deg, #0F9D8C 0%, #2BC4AE 100%)',
}

const activeTab = ref('health')
const loading = ref(false)
const statLoading = ref(false)
const exporting = ref(false)
const list = ref([])
const total = ref(0)
const dateRange = ref([])
const stats = ref({ health_total: 0, sleep_total: 0, sport_total: 0, today_total: 0 })
const charts = ref({ record_trend: [], sleep_distribution: [], sport_distribution: [], month_duration: [] })

const query = reactive({ keyword: '', sport_type: '', page: 1, page_size: 10 })

const axisBase = {
  axisLine: { lineStyle: { color: '#dfe6ef' } },
  axisLabel: { color: '#8794a8' },
}

const recordTrendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 46, right: 18, top: 24, bottom: 30 },
  xAxis: { type: 'category', data: (charts.value.record_trend || []).map((i) => i.date.slice(5)), ...axisBase },
  yAxis: { type: 'value', splitLine: { lineStyle: { color: '#f0f3f8' } }, axisLabel: { color: '#8794a8' } },
  series: [
    {
      name: '录入数',
      type: 'line',
      smooth: true,
      data: (charts.value.record_trend || []).map((i) => i.value),
      itemStyle: { color: '#2F5DA8' },
      areaStyle: { color: 'rgba(47,93,168,0.12)' },
    },
  ],
}))

const sleepOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0, textStyle: { color: '#6b7a90' } },
  series: [
    {
      type: 'pie',
      radius: ['42%', '68%'],
      center: ['50%', '44%'],
      itemStyle: { borderColor: '#fff', borderWidth: 2 },
      data: charts.value.sleep_distribution || [],
    },
  ],
}))

const sportOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0, textStyle: { color: '#6b7a90' } },
  series: [
    {
      type: 'pie',
      roseType: 'radius',
      radius: ['30%', '68%'],
      center: ['50%', '44%'],
      itemStyle: { borderColor: '#fff', borderWidth: 2 },
      data: charts.value.sport_distribution || [],
    },
  ],
}))

const monthOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 56, right: 18, top: 24, bottom: 30 },
  xAxis: { type: 'category', data: (charts.value.month_duration || []).map((i) => i.name), ...axisBase },
  yAxis: { type: 'value', splitLine: { lineStyle: { color: '#f0f3f8' } }, axisLabel: { color: '#8794a8' } },
  series: [
    {
      name: '运动时长(分钟)',
      type: 'bar',
      barWidth: 26,
      data: (charts.value.month_duration || []).map((i) => i.value),
      itemStyle: { borderRadius: [6, 6, 0, 0], color: '#F5872A' },
    },
  ],
}))

function currentQuery() {
  return {
    keyword: query.keyword,
    sport_type: activeTab.value === 'sport' ? query.sport_type : undefined,
    start_date: dateRange.value?.[0],
    end_date: dateRange.value?.[1],
  }
}

async function load() {
  if (activeTab.value === 'stat') return
  loading.value = true
  try {
    const params = { ...currentQuery(), page: query.page, page_size: query.page_size }
    let res
    if (activeTab.value === 'health') res = await adminApi.healthRecordList(params)
    else if (activeTab.value === 'sleep') res = await adminApi.sleepRecordList(params)
    else res = await adminApi.sportRecordList(params)
    list.value = res.data.list || []
    total.value = res.data.total || 0
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  statLoading.value = true
  try {
    const { data } = await adminApi.healthDataStatistics()
    stats.value = {
      health_total: data.health_total,
      sleep_total: data.sleep_total,
      sport_total: data.sport_total,
      today_total: data.today_total,
    }
    charts.value = data.charts || charts.value
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    statLoading.value = false
  }
}

function search() {
  query.page = 1
  load()
}

function reset() {
  query.keyword = ''
  query.sport_type = ''
  query.page = 1
  dateRange.value = []
  load()
}

function onTabChange() {
  if (activeTab.value === 'stat') loadStats()
  else search()
}

async function exportCsv() {
  exporting.value = true
  try {
    const params = currentQuery()
    let res
    if (activeTab.value === 'health') res = await adminApi.exportHealthRecord(params)
    else if (activeTab.value === 'sleep') res = await adminApi.exportSleepRecord(params)
    else res = await adminApi.exportSportRecord(params)
    saveBlobResponse(res, `${activeTab.value}_record.csv`)
    ElMessage.success('导出成功，内容与当前筛选条件一致')
  } catch (e) {
    ElMessage.error('导出失败，请稍后重试')
  } finally {
    exporting.value = false
  }
}

onMounted(() => {
  loadStats()
  load()
})
</script>
