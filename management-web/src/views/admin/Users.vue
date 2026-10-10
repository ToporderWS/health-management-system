<template>
  <div class="hms-page">
    <div class="hms-card">
      <div class="hms-card__title">
        <span>普通用户管理</span>
        <span class="hms-muted">管理员以查看为主，禁止修改用户原始健康数据</span>
      </div>

      <div class="hms-filter hms-mb-12">
        <el-input v-model="query.nickname" placeholder="昵称" clearable style="width: 160px" @keyup.enter="search" />
        <el-input v-model="query.phone" placeholder="手机号" clearable style="width: 160px" @keyup.enter="search" />
        <el-select v-model="query.gender" placeholder="性别" clearable style="width: 110px">
          <el-option label="男" value="男" />
          <el-option label="女" value="女" />
          <el-option label="保密" value="保密" />
        </el-select>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          range-separator="至"
          start-placeholder="注册开始"
          end-placeholder="注册结束"
          style="width: 250px"
        />
        <el-button type="primary" @click="search">查询</el-button>
        <el-button @click="reset">重置</el-button>
      </div>

      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column label="用户" min-width="160">
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
        <el-table-column prop="doctor_count" label="负责医生数" width="110" />
        <el-table-column prop="coach_count" label="负责教练数" width="110" />
        <el-table-column prop="created_at" label="注册时间" width="180" />
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">健康档案</el-button>
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

    <!-- 用户完整健康档案 -->
    <el-drawer v-model="drawerVisible" :title="`用户健康档案 · ${detail.nickname || ''}`" size="76%">
      <el-tabs v-model="activeTab" @tab-change="loadTab">
        <el-tab-pane label="基本资料" name="base">
          <el-descriptions :column="3" border v-loading="tabLoading">
            <el-descriptions-item label="用户ID">{{ detail.id }}</el-descriptions-item>
            <el-descriptions-item label="昵称">{{ detail.nickname || '-' }}</el-descriptions-item>
            <el-descriptions-item label="手机号">{{ detail.phone || '-' }}</el-descriptions-item>
            <el-descriptions-item label="性别">{{ detail.gender || '-' }}</el-descriptions-item>
            <el-descriptions-item label="年龄">{{ detail.age ?? '-' }}</el-descriptions-item>
            <el-descriptions-item label="身高(cm)">{{ detail.height ?? '-' }}</el-descriptions-item>
            <el-descriptions-item label="注册时间">{{ detail.created_at || '-' }}</el-descriptions-item>
            <el-descriptions-item label="健康指标记录数">{{ detail.counts?.health_record ?? 0 }}</el-descriptions-item>
            <el-descriptions-item label="睡眠记录数">{{ detail.counts?.sleep_record ?? 0 }}</el-descriptions-item>
            <el-descriptions-item label="运动记录数">{{ detail.counts?.sport_record ?? 0 }}</el-descriptions-item>
            <el-descriptions-item label="健康计划数">{{ detail.counts?.health_plan ?? 0 }}</el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>

        <el-tab-pane label="健康指标" name="health">
          <el-table :data="tabData.health" size="small" v-loading="tabLoading" stripe>
            <el-table-column prop="record_date" label="日期" width="120" />
            <el-table-column prop="weight" label="体重(kg)" width="100" />
            <el-table-column prop="blood_pressure_high" label="收缩压" width="90" />
            <el-table-column prop="blood_pressure_low" label="舒张压" width="90" />
            <el-table-column prop="heart_rate" label="心率" width="80" />
            <el-table-column prop="blood_sugar" label="血糖" width="80" />
            <el-table-column prop="created_at" label="录入时间" min-width="170" />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="睡眠记录" name="sleep">
          <el-table :data="tabData.sleep" size="small" v-loading="tabLoading" stripe>
            <el-table-column prop="sleep_date" label="日期" width="120" />
            <el-table-column prop="sleep_start" label="入睡" min-width="170" />
            <el-table-column prop="sleep_end" label="起床" min-width="170" />
            <el-table-column label="时长" width="130">
              <template #default="{ row }">{{ formatDuration(row.sleep_duration) }}</template>
            </el-table-column>
            <el-table-column prop="sleep_quality" label="质量" width="90" />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="运动记录" name="sport">
          <el-table :data="tabData.sport" size="small" v-loading="tabLoading" stripe>
            <el-table-column prop="sport_date" label="日期" width="120" />
            <el-table-column prop="sport_type" label="类型" width="110" />
            <el-table-column prop="sport_duration" label="时长(分钟)" width="110" />
            <el-table-column prop="calorie" label="卡路里" width="90" />
            <el-table-column prop="remark" label="备注" min-width="160" />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="健康计划" name="plan">
          <el-table :data="tabData.plan" size="small" v-loading="tabLoading" stripe>
            <el-table-column prop="plan_title" label="标题" min-width="150" />
            <el-table-column prop="plan_content" label="内容" min-width="200" show-overflow-tooltip />
            <el-table-column prop="plan_start" label="开始" width="120" />
            <el-table-column prop="plan_end" label="结束" width="120" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag size="small" :type="HEALTH_PLAN_STATUS[row.plan_status]?.type">
                  {{ HEALTH_PLAN_STATUS[row.plan_status]?.text }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="医生服务" name="doctor">
          <div v-loading="tabLoading">
            <el-descriptions :column="2" border class="hms-mb-12" title="负责医生">
              <el-descriptions-item v-for="d in service.doctor.doctors" :key="d.id" :label="d.real_name">
                {{ d.doctor_name }} / {{ d.specialty || '-' }} / {{ d.phone || '-' }}
              </el-descriptions-item>
              <el-descriptions-item v-if="!service.doctor.doctors?.length" label="负责医生">暂无</el-descriptions-item>
            </el-descriptions>
            <div class="hms-card__title"><span>健康建议</span></div>
            <el-table :data="service.doctor.advice" size="small" stripe>
              <el-table-column prop="doctor_name" label="医生" width="120" />
              <el-table-column prop="created_at" label="时间" width="180" />
              <el-table-column prop="advice_content" label="内容" min-width="300" />
            </el-table>
            <div class="hms-card__title" style="margin-top: 16px"><span>体检通知</span></div>
            <el-table :data="service.doctor.medical_notice" size="small" stripe>
              <el-table-column prop="notice_title" label="标题" min-width="170" />
              <el-table-column prop="notice_content" label="内容" min-width="220" show-overflow-tooltip />
              <el-table-column prop="check_date" label="检查时间" width="170" />
            </el-table>
            <div class="hms-card__title" style="margin-top: 16px"><span>医疗记录</span></div>
            <el-table :data="service.doctor.medical_record" size="small" stripe>
              <el-table-column prop="record_title" label="标题" min-width="170" />
              <el-table-column prop="record_content" label="内容" min-width="240" show-overflow-tooltip />
              <el-table-column prop="record_date" label="记录日期" width="130" />
            </el-table>
          </div>
        </el-tab-pane>

        <el-tab-pane label="健身服务" name="coach">
          <div v-loading="tabLoading">
            <el-descriptions :column="2" border class="hms-mb-12" title="负责教练">
              <el-descriptions-item v-for="c in service.coach.coaches" :key="c.id" :label="c.real_name">
                {{ c.coach_name }} / {{ c.specialty || '-' }} / {{ c.phone || '-' }}
              </el-descriptions-item>
              <el-descriptions-item v-if="!service.coach.coaches?.length" label="负责教练">暂无</el-descriptions-item>
            </el-descriptions>
            <div class="hms-card__title"><span>运动目标</span></div>
            <el-table :data="service.coach.sport_goal" size="small" stripe>
              <el-table-column prop="goal_title" label="标题" min-width="150" />
              <el-table-column prop="goal_content" label="内容" min-width="200" show-overflow-tooltip />
              <el-table-column prop="start_date" label="开始" width="120" />
              <el-table-column prop="end_date" label="结束" width="120" />
            </el-table>
            <div class="hms-card__title" style="margin-top: 16px"><span>训练计划</span></div>
            <el-table :data="service.coach.training_plan" size="small" stripe>
              <el-table-column prop="plan_title" label="标题" min-width="150" />
              <el-table-column prop="plan_content" label="内容" min-width="200" show-overflow-tooltip />
              <el-table-column prop="start_date" label="开始" width="120" />
              <el-table-column prop="end_date" label="结束" width="120" />
            </el-table>
            <div class="hms-card__title" style="margin-top: 16px"><span>健身建议</span></div>
            <el-table :data="service.coach.fitness_advice" size="small" stripe>
              <el-table-column prop="coach_name" label="教练" width="120" />
              <el-table-column prop="created_at" label="时间" width="180" />
              <el-table-column prop="advice_content" label="内容" min-width="300" />
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-drawer>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'

import { adminApi } from '@/api/admin'
import { resolveFileUrl } from '@/utils/config'
import { HEALTH_PLAN_STATUS, formatDuration } from '@/utils/format'

const loading = ref(false)
const tabLoading = ref(false)
const list = ref([])
const total = ref(0)
const dateRange = ref([])
const query = reactive({ nickname: '', phone: '', gender: '', page: 1, page_size: 10 })

const drawerVisible = ref(false)
const detail = ref({})
const activeTab = ref('base')
const tabData = reactive({ health: [], sleep: [], sport: [], plan: [] })
const service = reactive({
  doctor: { doctors: [], advice: [], medical_notice: [], medical_record: [] },
  coach: { coaches: [], sport_goal: [], training_plan: [], fitness_advice: [] },
})

async function load() {
  loading.value = true
  try {
    const { data } = await adminApi.userList({
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

function search() {
  query.page = 1
  load()
}

function reset() {
  Object.assign(query, { nickname: '', phone: '', gender: '', page: 1 })
  dateRange.value = []
  load()
}

async function openDetail(row) {
  activeTab.value = 'base'
  drawerVisible.value = true
  tabLoading.value = true
  try {
    const { data } = await adminApi.userDetail(row.id)
    detail.value = data
  } catch (e) {
    detail.value = {}
  } finally {
    tabLoading.value = false
  }
}

async function loadTab(name) {
  const userId = detail.value.id
  if (!userId) return
  if (name === 'base') return
  tabLoading.value = true
  try {
    if (['health', 'sleep', 'sport', 'plan'].includes(name)) {
      const { data } = await adminApi.userHealthData({
        user_id: userId,
        data_type: name,
        page: 1,
        page_size: 100,
      })
      tabData[name] = data.list || []
    } else if (name === 'doctor') {
      const { data } = await adminApi.userDoctorService(userId)
      service.doctor = {
        doctors: data.doctors || [],
        advice: data.advice || [],
        medical_notice: data.medical_notice || [],
        medical_record: data.medical_record || [],
      }
    } else if (name === 'coach') {
      const { data } = await adminApi.userCoachService(userId)
      service.coach = {
        coaches: data.coaches || [],
        sport_goal: data.sport_goal || [],
        training_plan: data.training_plan || [],
        fitness_advice: data.fitness_advice || [],
      }
    }
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
