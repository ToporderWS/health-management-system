<template>
  <div class="hms-page">
    <div class="hms-card">
      <div class="hms-card__title">
        <span>学员列表</span>
        <span class="hms-muted">仅显示由管理员绑定给您负责的学员</span>
      </div>

      <div class="hms-filter hms-mb-12">
        <el-input
          v-model="query.keyword"
          placeholder="搜索昵称 / 手机号"
          clearable
          style="width: 240px"
          @keyup.enter="search"
        />
        <el-button type="primary" @click="search">查询</el-button>
        <el-button @click="reset">重置</el-button>
      </div>

      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column label="学员" min-width="160">
          <template #default="{ row }">
            <div class="cell-user">
              <img class="hms-avatar" :src="resolveFileUrl(row.avatar)" alt="avatar" />
              <span>{{ row.nickname }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="手机号" width="140" />
        <el-table-column prop="gender" label="性别" width="80" />
        <el-table-column prop="age" label="年龄" width="80" />
        <el-table-column label="身高(cm)" width="100">
          <template #default="{ row }">{{ row.height ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="今日运动(分钟)" width="140">
          <template #default="{ row }">{{ row.today_duration }}</template>
        </el-table-column>
        <el-table-column label="今日卡路里" width="120">
          <template #default="{ row }">{{ row.today_calorie }}</template>
        </el-table-column>
        <el-table-column prop="relation_time" label="绑定时间" width="180" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">详情</el-button>
            <el-button link type="primary" @click="goSports(row)">运动数据</el-button>
          </template>
        </el-table-column>
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

    <el-drawer v-model="drawerVisible" :title="`学员详情 · ${current.nickname || ''}`" size="70%">
      <el-descriptions :column="3" border size="small" class="hms-mb-12">
        <el-descriptions-item label="昵称">{{ current.nickname || '-' }}</el-descriptions-item>
        <el-descriptions-item label="手机号">{{ current.phone || '-' }}</el-descriptions-item>
        <el-descriptions-item label="性别">{{ current.gender || '-' }}</el-descriptions-item>
        <el-descriptions-item label="年龄">{{ current.age ?? '-' }}</el-descriptions-item>
        <el-descriptions-item label="身高(cm)">{{ current.height ?? '-' }}</el-descriptions-item>
        <el-descriptions-item label="注册时间">{{ current.created_at || '-' }}</el-descriptions-item>
      </el-descriptions>

      <el-tabs v-model="activeTab" @tab-change="loadTab">
        <el-tab-pane label="运动数据" name="sport">
          <el-table :data="tab.sport" size="small" v-loading="tabLoading" stripe>
            <el-table-column prop="sport_date" label="日期" width="120" />
            <el-table-column prop="sport_type" label="运动类型" width="120" />
            <el-table-column prop="sport_duration" label="时长(分钟)" width="120" />
            <el-table-column prop="calorie" label="卡路里" width="100" />
            <el-table-column prop="remark" label="备注" min-width="160" />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="运动目标" name="goal">
          <el-table :data="tab.goal" size="small" v-loading="tabLoading" stripe>
            <el-table-column prop="goal_title" label="目标标题" min-width="160" />
            <el-table-column prop="goal_content" label="内容" min-width="220" show-overflow-tooltip />
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
        </el-tab-pane>

        <el-tab-pane label="训练计划" name="plan">
          <el-table :data="tab.plan" size="small" v-loading="tabLoading" stripe>
            <el-table-column prop="plan_title" label="计划标题" min-width="160" />
            <el-table-column prop="plan_content" label="内容" min-width="220" show-overflow-tooltip />
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
        </el-tab-pane>

        <el-tab-pane label="健身建议" name="advice">
          <el-table :data="tab.advice" size="small" v-loading="tabLoading" stripe>
            <el-table-column prop="created_at" label="时间" width="180" />
            <el-table-column prop="advice_content" label="建议内容" min-width="320" />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-drawer>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { coachApi } from '@/api/coach'
import { resolveFileUrl } from '@/utils/config'
import { SPORT_STATUS } from '@/utils/format'

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const tabLoading = ref(false)
const list = ref([])
const total = ref(0)
const query = reactive({ keyword: '', page: 1, page_size: 10 })

const drawerVisible = ref(false)
const current = ref({})
const activeTab = ref('sport')
const tab = reactive({ sport: [], goal: [], plan: [], advice: [] })

async function load() {
  loading.value = true
  try {
    const { data } = await coachApi.studentList(query)
    list.value = data.list || []
    total.value = data.total || 0
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
  query.keyword = ''
  query.page = 1
  load()
}

function goSports(row) {
  router.push({ path: '/coach/sports', query: { user_id: row.id } })
}

async function openDetail(row) {
  try {
    const { data } = await coachApi.studentDetail(row.id)
    current.value = data
  } catch (e) {
    return
  }
  activeTab.value = 'sport'
  drawerVisible.value = true
  await loadTab('sport')
}

async function loadTab(name) {
  const userId = current.value.id
  if (!userId) return
  tabLoading.value = true
  const params = { user_id: userId, page: 1, page_size: 50 }
  try {
    if (name === 'sport') tab.sport = (await coachApi.studentSportData(params)).data.list || []
    else if (name === 'goal') tab.goal = (await coachApi.goalList(params)).data.list || []
    else if (name === 'plan') tab.plan = (await coachApi.planList(params)).data.list || []
    else if (name === 'advice') tab.advice = (await coachApi.adviceList(params)).data.list || []
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    tabLoading.value = false
  }
}

onMounted(() => {
  load()
  if (route.query.user_id) {
    openDetail({ id: Number(route.query.user_id) })
  }
})
</script>

<style scoped>
.cell-user {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
