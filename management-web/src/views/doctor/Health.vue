<template>
  <div class="hms-page">
    <div class="hms-card">
      <div class="hms-card__title">
        <span>患者健康数据（只读）</span>
        <span class="hms-muted">原始数据由患者自行录入，医生仅可查看</span>
      </div>

      <div class="hms-filter hms-mb-12">
        <PatientSelect v-model="query.user_id" role="doctor" placeholder="选择患者" style="width: 220px" />
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 260px"
        />
        <el-select v-if="activeTab === 'sport'" v-model="query.sport_type" placeholder="运动类型" clearable style="width: 140px">
          <el-option v-for="t in SPORT_TYPES" :key="t" :label="t" :value="t" />
        </el-select>
        <el-button type="primary" @click="search">查询</el-button>
        <el-button @click="reset">重置</el-button>
      </div>

      <el-tabs v-model="activeTab" @tab-change="search">
        <el-tab-pane label="健康指标" name="health" />
        <el-tab-pane label="睡眠数据" name="sleep" />
        <el-tab-pane label="运动数据" name="sport" />
      </el-tabs>

      <el-empty v-if="!query.user_id" description="请先选择患者" />
      <template v-else>
        <el-table v-if="activeTab === 'health'" :data="list" v-loading="loading" stripe>
          <el-table-column prop="record_date" label="日期" width="120" />
          <el-table-column prop="weight" label="体重(kg)" width="110" />
          <el-table-column prop="blood_pressure_high" label="收缩压" width="100" />
          <el-table-column prop="blood_pressure_low" label="舒张压" width="100" />
          <el-table-column prop="heart_rate" label="心率" width="90" />
          <el-table-column prop="blood_sugar" label="血糖" width="90" />
          <el-table-column label="指标提示" width="120">
            <template #default="{ row }">
              <el-tag v-if="isAbnormal(row)" size="small" type="warning">请关注</el-tag>
              <el-tag v-else size="small" type="success">常规</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="录入时间" min-width="170" />
        </el-table>

        <el-table v-else-if="activeTab === 'sleep'" :data="list" v-loading="loading" stripe>
          <el-table-column prop="sleep_date" label="日期" width="120" />
          <el-table-column prop="sleep_start" label="入睡时间" min-width="170" />
          <el-table-column prop="sleep_end" label="起床时间" min-width="170" />
          <el-table-column label="睡眠时长" width="140">
            <template #default="{ row }">{{ formatDuration(row.sleep_duration) }}</template>
          </el-table-column>
          <el-table-column prop="sleep_quality" label="睡眠质量" width="110" />
        </el-table>

        <el-table v-else :data="list" v-loading="loading" stripe>
          <el-table-column prop="sport_date" label="日期" width="120" />
          <el-table-column prop="sport_type" label="运动类型" width="120" />
          <el-table-column prop="sport_duration" label="时长(分钟)" width="120" />
          <el-table-column prop="calorie" label="卡路里" width="100" />
          <el-table-column prop="remark" label="备注" min-width="180" />
          <el-table-column prop="created_at" label="录入时间" min-width="170" />
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
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import PatientSelect from '@/components/PatientSelect.vue'
import { doctorApi } from '@/api/doctor'
import { isAbnormal, formatDuration } from '@/utils/format'

const SPORT_TYPES = ['跑步', '快走', '骑行', '游泳', '瑜伽', '力量训练', '球类', '其他']

const route = useRoute()
const loading = ref(false)
const list = ref([])
const total = ref(0)
const activeTab = ref('health')
const dateRange = ref([])

const query = reactive({
  user_id: '',
  page: 1,
  page_size: 10,
  sport_type: '',
})

function buildParams() {
  return {
    user_id: query.user_id,
    page: query.page,
    page_size: query.page_size,
    sport_type: activeTab.value === 'sport' ? query.sport_type : undefined,
    start_date: dateRange.value?.[0],
    end_date: dateRange.value?.[1],
  }
}

async function load() {
  if (!query.user_id) {
    list.value = []
    total.value = 0
    return
  }
  loading.value = true
  try {
    const params = buildParams()
    let res
    if (activeTab.value === 'health') res = await doctorApi.patientHealthData(params)
    else if (activeTab.value === 'sleep') res = await doctorApi.patientSleepData(params)
    else res = await doctorApi.patientSportData(params)
    list.value = res.data.list || []
    total.value = res.data.total || 0
  } catch (e) {
    list.value = []
    total.value = 0
  } finally {
    loading.value = false
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

watch(() => query.user_id, search)

onMounted(() => {
  if (route.query.user_id) {
    query.user_id = Number(route.query.user_id)
  }
  load()
})
</script>
