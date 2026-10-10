<template>
  <div class="hms-page">
    <div class="hms-stat-grid">
      <StatCard label="计划总数" :value="stats.total" icon="List" :gradient="g.blue" />
      <StatCard label="进行中" :value="stats.running" icon="Loading" :gradient="g.orange" />
      <StatCard label="已完成" :value="stats.finished" icon="CircleCheck" :gradient="g.green" />
      <StatCard label="已放弃" :value="stats.abandoned" icon="CircleClose" :gradient="g.slate" />
    </div>

    <div class="hms-card">
      <div class="hms-card__title">
        <span>健康计划管理</span>
        <span class="hms-muted">管理员以监管为主，不修改用户计划内容</span>
      </div>

      <div class="hms-filter hms-mb-12">
        <el-input v-model="query.keyword" placeholder="用户昵称 / 手机号 / 计划标题" clearable style="width: 240px" @keyup.enter="search" />
        <el-select v-model="query.plan_status" placeholder="计划状态" clearable style="width: 140px">
          <el-option v-for="(v, k) in HEALTH_PLAN_STATUS" :key="k" :label="v.text" :value="Number(k)" />
        </el-select>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 250px"
        />
        <el-button type="primary" @click="search">查询</el-button>
        <el-button @click="reset">重置</el-button>
      </div>

      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column label="用户" min-width="140">
          <template #default="{ row }">{{ row.nickname || '-' }}（{{ row.phone || '-' }}）</template>
        </el-table-column>
        <el-table-column prop="plan_title" label="计划标题" min-width="160" />
        <el-table-column prop="plan_content" label="计划内容" min-width="240" show-overflow-tooltip />
        <el-table-column prop="plan_start" label="开始日期" width="120" />
        <el-table-column prop="plan_end" label="结束日期" width="120" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="HEALTH_PLAN_STATUS[row.plan_status]?.type">
              {{ HEALTH_PLAN_STATUS[row.plan_status]?.text }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
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
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'

import StatCard from '@/components/StatCard.vue'
import { adminApi } from '@/api/admin'
import { HEALTH_PLAN_STATUS } from '@/utils/format'

const g = {
  blue: 'linear-gradient(135deg, #1B3A6B 0%, #2F5DA8 100%)',
  orange: 'linear-gradient(135deg, #F5872A 0%, #FFAE5C 100%)',
  green: 'linear-gradient(135deg, #0F9D8C 0%, #2BC4AE 100%)',
  slate: 'linear-gradient(135deg, #5B6B85 0%, #8A9BB5 100%)',
}

const loading = ref(false)
const list = ref([])
const total = ref(0)
const dateRange = ref([])
const stats = ref({ total: 0, running: 0, finished: 0, abandoned: 0 })
const query = reactive({ keyword: '', plan_status: '', page: 1, page_size: 10 })

async function load() {
  loading.value = true
  try {
    const { data } = await adminApi.healthPlanList({
      ...query,
      start_date: dateRange.value?.[0],
      end_date: dateRange.value?.[1],
    })
    list.value = data.list || []
    total.value = data.total || 0
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  try {
    const { data } = await adminApi.healthPlanStats()
    stats.value = data
  } catch (e) {
    /* 拦截器已提示 */
  }
}

function search() {
  query.page = 1
  load()
}

function reset() {
  Object.assign(query, { keyword: '', plan_status: '', page: 1 })
  dateRange.value = []
  load()
}

onMounted(() => {
  loadStats()
  load()
})
</script>
