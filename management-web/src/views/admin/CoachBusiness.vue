<template>
  <div class="hms-page">
    <div class="hms-card">
      <div class="hms-card__title">
        <span>健身业务监管</span>
        <span class="hms-muted">监管只读：管理员不得代教练创建或修改运动目标与训练计划</span>
      </div>

      <el-tabs v-model="activeTab" @tab-change="search">
        <el-tab-pane label="运动目标" name="goal" />
        <el-tab-pane label="训练计划" name="plan" />
        <el-tab-pane label="健身建议" name="advice" />
      </el-tabs>

      <div class="hms-filter hms-mb-12">
        <el-select v-model="query.coach_id" placeholder="按教练筛选" clearable filterable style="width: 210px">
          <el-option
            v-for="c in coaches"
            :key="c.id"
            :label="`${c.real_name || '-'}（${c.coach_name}）`"
            :value="c.id"
          />
        </el-select>
        <el-select v-model="query.user_id" placeholder="按学员筛选" clearable filterable style="width: 210px">
          <el-option v-for="u in users" :key="u.id" :label="`${u.nickname}（${u.phone}）`" :value="u.id" />
        </el-select>
        <el-select v-if="activeTab !== 'advice'" v-model="query.status" placeholder="状态" clearable style="width: 140px">
          <el-option v-for="(v, k) in SPORT_STATUS" :key="k" :label="v.text" :value="Number(k)" />
        </el-select>
        <el-input v-model="query.keyword" placeholder="关键词" clearable style="width: 170px" @keyup.enter="search" />
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 240px"
        />
        <el-button type="primary" @click="search">查询</el-button>
        <el-button @click="reset">重置</el-button>
      </div>

      <el-table v-if="activeTab === 'goal'" :data="list" v-loading="loading" stripe>
        <el-table-column prop="coach_real_name" label="教练" width="110" />
        <el-table-column label="学员" width="150">
          <template #default="{ row }">{{ row.nickname || '-' }}（{{ row.phone || '-' }}）</template>
        </el-table-column>
        <el-table-column prop="goal_title" label="目标标题" min-width="160" />
        <el-table-column prop="goal_content" label="目标内容" min-width="240" show-overflow-tooltip />
        <el-table-column prop="start_date" label="开始" width="120" />
        <el-table-column prop="end_date" label="结束" width="120" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="SPORT_STATUS[row.goal_status]?.type">
              {{ SPORT_STATUS[row.goal_status]?.text }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <el-table v-else-if="activeTab === 'plan'" :data="list" v-loading="loading" stripe>
        <el-table-column prop="coach_real_name" label="教练" width="110" />
        <el-table-column label="学员" width="150">
          <template #default="{ row }">{{ row.nickname || '-' }}（{{ row.phone || '-' }}）</template>
        </el-table-column>
        <el-table-column prop="plan_title" label="计划标题" min-width="160" />
        <el-table-column prop="plan_content" label="计划内容" min-width="240" show-overflow-tooltip />
        <el-table-column prop="start_date" label="开始" width="120" />
        <el-table-column prop="end_date" label="结束" width="120" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="SPORT_STATUS[row.plan_status]?.type">
              {{ SPORT_STATUS[row.plan_status]?.text }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <el-table v-else :data="list" v-loading="loading" stripe>
        <el-table-column prop="coach_real_name" label="教练" width="110" />
        <el-table-column label="学员" width="150">
          <template #default="{ row }">{{ row.nickname || '-' }}（{{ row.phone || '-' }}）</template>
        </el-table-column>
        <el-table-column prop="advice_content" label="健身建议内容" min-width="360" />
        <el-table-column prop="created_at" label="发送时间" width="180" />
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

import { adminApi } from '@/api/admin'
import { SPORT_STATUS } from '@/utils/format'

const activeTab = ref('goal')
const loading = ref(false)
const list = ref([])
const total = ref(0)
const coaches = ref([])
const users = ref([])
const dateRange = ref([])
const query = reactive({ coach_id: '', user_id: '', status: '', keyword: '', page: 1, page_size: 10 })

async function loadOptions() {
  try {
    coaches.value = (await adminApi.commonCoaches()).data || []
    users.value = (await adminApi.commonUsers()).data || []
  } catch (e) {
    /* 拦截器已提示 */
  }
}

async function load() {
  loading.value = true
  try {
    const base = {
      coach_id: query.coach_id,
      user_id: query.user_id,
      keyword: query.keyword,
      start_date: dateRange.value?.[0],
      end_date: dateRange.value?.[1],
      page: query.page,
      page_size: query.page_size,
    }
    let res
    if (activeTab.value === 'goal') {
      res = await adminApi.sportGoalList({ ...base, goal_status: query.status })
    } else if (activeTab.value === 'plan') {
      res = await adminApi.trainingPlanList({ ...base, plan_status: query.status })
    } else {
      res = await adminApi.fitnessAdviceList(base)
    }
    list.value = res.data.list || []
    total.value = res.data.total || 0
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

function search() {
  query.page = 1
  load()
}

function reset() {
  Object.assign(query, { coach_id: '', user_id: '', status: '', keyword: '', page: 1 })
  dateRange.value = []
  load()
}

onMounted(() => {
  loadOptions()
  load()
})
</script>
