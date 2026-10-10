<template>
  <div class="hms-page">
    <div class="hms-card">
      <div class="hms-card__title">
        <span>患者列表</span>
        <span class="hms-muted">仅显示由管理员绑定给您负责的患者</span>
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
        <el-table-column label="患者" min-width="160">
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
        <el-table-column prop="relation_time" label="绑定时间" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">健康档案</el-button>
            <el-button link type="primary" @click="goHealth(row)">健康数据</el-button>
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

    <!-- 患者完整档案 -->
    <el-drawer v-model="drawerVisible" :title="`患者健康档案 · ${current.nickname || ''}`" size="72%">
      <el-descriptions :column="3" border size="small" class="hms-mb-12">
        <el-descriptions-item label="昵称">{{ current.nickname || '-' }}</el-descriptions-item>
        <el-descriptions-item label="手机号">{{ current.phone || '-' }}</el-descriptions-item>
        <el-descriptions-item label="性别">{{ current.gender || '-' }}</el-descriptions-item>
        <el-descriptions-item label="年龄">{{ current.age ?? '-' }}</el-descriptions-item>
        <el-descriptions-item label="身高(cm)">{{ current.height ?? '-' }}</el-descriptions-item>
        <el-descriptions-item label="注册时间">{{ current.created_at || '-' }}</el-descriptions-item>
      </el-descriptions>

      <el-tabs v-model="activeTab" @tab-change="loadTab">
        <el-tab-pane label="健康指标" name="health">
          <el-table :data="tab.health" size="small" v-loading="tabLoading" stripe>
            <el-table-column prop="record_date" label="日期" width="110" />
            <el-table-column prop="weight" label="体重(kg)" width="100" />
            <el-table-column prop="blood_pressure_high" label="收缩压" width="90" />
            <el-table-column prop="blood_pressure_low" label="舒张压" width="90" />
            <el-table-column prop="heart_rate" label="心率" width="80" />
            <el-table-column prop="blood_sugar" label="血糖" width="80" />
            <el-table-column prop="created_at" label="录入时间" min-width="160" />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="睡眠记录" name="sleep">
          <el-table :data="tab.sleep" size="small" v-loading="tabLoading" stripe>
            <el-table-column prop="sleep_date" label="日期" width="110" />
            <el-table-column prop="sleep_start" label="入睡" min-width="160" />
            <el-table-column prop="sleep_end" label="起床" min-width="160" />
            <el-table-column label="时长" width="130">
              <template #default="{ row }">{{ formatDuration(row.sleep_duration) }}</template>
            </el-table-column>
            <el-table-column prop="sleep_quality" label="质量" width="90" />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="运动记录" name="sport">
          <el-table :data="tab.sport" size="small" v-loading="tabLoading" stripe>
            <el-table-column prop="sport_date" label="日期" width="110" />
            <el-table-column prop="sport_type" label="运动类型" width="110" />
            <el-table-column prop="sport_duration" label="时长(分钟)" width="110" />
            <el-table-column prop="calorie" label="卡路里" width="90" />
            <el-table-column prop="remark" label="备注" min-width="160" />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="健康计划" name="plan">
          <el-table :data="tab.plan" size="small" v-loading="tabLoading" stripe>
            <el-table-column prop="plan_title" label="标题" min-width="150" />
            <el-table-column prop="plan_content" label="内容" min-width="200" show-overflow-tooltip />
            <el-table-column prop="plan_start" label="开始" width="110" />
            <el-table-column prop="plan_end" label="结束" width="110" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag size="small" :type="HEALTH_PLAN_STATUS[row.plan_status]?.type">
                  {{ HEALTH_PLAN_STATUS[row.plan_status]?.text }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="健康建议" name="advice">
          <el-table :data="tab.advice" size="small" v-loading="tabLoading" stripe>
            <el-table-column prop="created_at" label="时间" width="170" />
            <el-table-column prop="advice_content" label="建议内容" min-width="300" />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="体检通知" name="notice">
          <el-table :data="tab.notice" size="small" v-loading="tabLoading" stripe>
            <el-table-column prop="notice_title" label="标题" min-width="180" />
            <el-table-column prop="notice_content" label="内容" min-width="220" show-overflow-tooltip />
            <el-table-column prop="check_date" label="检查时间" width="170" />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="医疗记录" name="record">
          <el-table :data="tab.record" size="small" v-loading="tabLoading" stripe>
            <el-table-column prop="record_title" label="标题" min-width="180" />
            <el-table-column prop="record_content" label="内容" min-width="240" show-overflow-tooltip />
            <el-table-column prop="record_date" label="记录日期" width="120" />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-drawer>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { doctorApi } from '@/api/doctor'
import { resolveFileUrl } from '@/utils/config'
import { HEALTH_PLAN_STATUS, formatDuration, formatDate } from '@/utils/format'

const router = useRouter()
const loading = ref(false)
const tabLoading = ref(false)
const list = ref([])
const total = ref(0)
const query = reactive({ keyword: '', page: 1, page_size: 10 })

const drawerVisible = ref(false)
const current = ref({})
const activeTab = ref('health')
const tab = reactive({ health: [], sleep: [], sport: [], plan: [], advice: [], notice: [], record: [] })

async function load() {
  loading.value = true
  try {
    const { data } = await doctorApi.patientList(query)
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

function goHealth(row) {
  router.push({ path: '/doctor/health', query: { user_id: row.id } })
}

async function openDetail(row) {
  try {
    const { data } = await doctorApi.patientDetail(row.id)
    current.value = data
  } catch (e) {
    return
  }
  activeTab.value = 'health'
  drawerVisible.value = true
  await loadTab('health')
}

async function loadTab(name) {
  const userId = current.value.id
  if (!userId) return
  tabLoading.value = true
  const params = { user_id: userId, page: 1, page_size: 50 }
  try {
    if (name === 'health') tab.health = (await doctorApi.patientHealthData(params)).data.list || []
    else if (name === 'sleep') tab.sleep = (await doctorApi.patientSleepData(params)).data.list || []
    else if (name === 'sport') tab.sport = (await doctorApi.patientSportData(params)).data.list || []
    else if (name === 'plan') tab.plan = (await doctorApi.patientPlanData(params)).data.list || []
    else if (name === 'advice') tab.advice = (await doctorApi.adviceList(params)).data.list || []
    else if (name === 'notice') tab.notice = (await doctorApi.noticeList(params)).data.list || []
    else if (name === 'record') tab.record = (await doctorApi.recordList(params)).data.list || []
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    tabLoading.value = false
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
