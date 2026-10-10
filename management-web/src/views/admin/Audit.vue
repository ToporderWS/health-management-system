<template>
  <div class="hms-page">
    <div class="hms-stat-grid">
      <StatCard label="待审核医生" :value="overview.pending_doctor" icon="FirstAidKit" :gradient="g.orange" />
      <StatCard label="待审核教练" :value="overview.pending_coach" icon="Basketball" :gradient="g.blue" />
      <StatCard label="今日已审核" :value="overview.today_audited" icon="Checked" :gradient="g.green" />
      <StatCard label="累计审核申请" :value="overview.total_apply" icon="Document" :gradient="g.slate" />
    </div>

    <div class="hms-card">
      <el-tabs v-model="activeTab" @tab-change="onTabChange">
        <el-tab-pane label="医生审核" name="doctor" />
        <el-tab-pane label="健身教练审核" name="coach" />
        <el-tab-pane label="审核记录" name="record" />
      </el-tabs>

      <!-- 医生审核 -->
      <template v-if="activeTab === 'doctor'">
        <div class="hms-filter hms-mb-12">
          <el-input v-model="doctorQuery.doctor_name" placeholder="医生账号" clearable style="width: 160px" @keyup.enter="search" />
          <el-input v-model="doctorQuery.real_name" placeholder="姓名" clearable style="width: 140px" @keyup.enter="search" />
          <el-select v-model="doctorQuery.audit_status" placeholder="审核状态" clearable style="width: 140px">
            <el-option v-for="(v, k) in AUDIT_STATUS" :key="k" :label="v.text" :value="Number(k)" />
          </el-select>
          <el-button type="primary" @click="search">查询</el-button>
          <el-button @click="resetDoctor">重置</el-button>
        </div>

        <el-table :data="doctorList" v-loading="loading" stripe>
          <el-table-column prop="doctor_name" label="医生账号" width="130" />
          <el-table-column prop="real_name" label="真实姓名" width="110" />
          <el-table-column prop="gender" label="性别" width="70" />
          <el-table-column prop="phone" label="手机号" width="140" />
          <el-table-column prop="specialty" label="专业方向" min-width="130" />
          <el-table-column prop="created_at" label="申请时间" width="180" />
          <el-table-column label="状态" width="110">
            <template #default="{ row }">
              <el-tag size="small" :type="auditType(row.audit_status)">{{ auditText(row.audit_status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="230" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openDetail('doctor', row)">查看</el-button>
              <el-button link type="success" :disabled="row.audit_status !== 0" @click="doAudit('doctor', row, 1)">通过</el-button>
              <el-button link type="danger" :disabled="row.audit_status !== 0" @click="doAudit('doctor', row, 2)">拒绝</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="hms-pagination">
          <el-pagination
            v-model:current-page="doctorQuery.page"
            v-model:page-size="doctorQuery.page_size"
            :total="doctorTotal"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @current-change="loadDoctors"
            @size-change="searchDoctor"
          />
        </div>
      </template>

      <!-- 教练审核 -->
      <template v-else-if="activeTab === 'coach'">
        <div class="hms-filter hms-mb-12">
          <el-input v-model="coachQuery.coach_name" placeholder="教练账号" clearable style="width: 160px" @keyup.enter="search" />
          <el-input v-model="coachQuery.real_name" placeholder="姓名" clearable style="width: 140px" @keyup.enter="search" />
          <el-select v-model="coachQuery.audit_status" placeholder="审核状态" clearable style="width: 140px">
            <el-option v-for="(v, k) in AUDIT_STATUS" :key="k" :label="v.text" :value="Number(k)" />
          </el-select>
          <el-button type="primary" @click="search">查询</el-button>
          <el-button @click="resetCoach">重置</el-button>
        </div>

        <el-table :data="coachList" v-loading="loading" stripe>
          <el-table-column prop="coach_name" label="教练账号" width="130" />
          <el-table-column prop="real_name" label="真实姓名" width="110" />
          <el-table-column prop="gender" label="性别" width="70" />
          <el-table-column prop="phone" label="手机号" width="140" />
          <el-table-column prop="specialty" label="专业方向" min-width="130" />
          <el-table-column prop="created_at" label="申请时间" width="180" />
          <el-table-column label="状态" width="110">
            <template #default="{ row }">
              <el-tag size="small" :type="auditType(row.audit_status)">{{ auditText(row.audit_status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="230" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openDetail('coach', row)">查看</el-button>
              <el-button link type="success" :disabled="row.audit_status !== 0" @click="doAudit('coach', row, 1)">通过</el-button>
              <el-button link type="danger" :disabled="row.audit_status !== 0" @click="doAudit('coach', row, 2)">拒绝</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="hms-pagination">
          <el-pagination
            v-model:current-page="coachQuery.page"
            v-model:page-size="coachQuery.page_size"
            :total="coachTotal"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @current-change="loadCoaches"
            @size-change="searchCoach"
          />
        </div>
      </template>

      <!-- 审核记录 -->
      <template v-else>
        <div class="hms-filter hms-mb-12">
          <el-select v-model="recordQuery.audit_type" placeholder="审核类型" clearable style="width: 150px">
            <el-option label="医生审核" value="doctor" />
            <el-option label="教练审核" value="coach" />
          </el-select>
          <el-input v-model="recordQuery.keyword" placeholder="关键词" clearable style="width: 200px" @keyup.enter="search" />
          <el-date-picker
            v-model="recordDateRange"
            type="daterange"
            value-format="YYYY-MM-DD"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 250px"
          />
          <el-button type="primary" @click="search">查询</el-button>
          <el-button @click="resetRecord">重置</el-button>
        </div>

        <el-table :data="recordList" v-loading="loading" stripe>
          <el-table-column prop="admin_name" label="管理员" width="110" />
          <el-table-column prop="operation_type" label="审核结果" width="140" />
          <el-table-column prop="operation_content" label="审核内容" min-width="320" />
          <el-table-column prop="created_at" label="审核时间" width="180" />
        </el-table>

        <div class="hms-pagination">
          <el-pagination
            v-model:current-page="recordQuery.page"
            v-model:page-size="recordQuery.page_size"
            :total="recordTotal"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @current-change="loadRecords"
            @size-change="searchRecord"
          />
        </div>
      </template>
    </div>

    <!-- 申请资料详情 -->
    <el-drawer v-model="detailVisible" :title="`申请资料 · ${detail.real_name || ''}`" size="46%">
      <el-descriptions :column="1" border v-loading="detailLoading">
        <el-descriptions-item :label="detailType === 'doctor' ? '医生账号' : '教练账号'">
          {{ detail.doctor_name || detail.coach_name || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="真实姓名">{{ detail.real_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="性别">{{ detail.gender || '-' }}</el-descriptions-item>
        <el-descriptions-item label="手机号">{{ detail.phone || '-' }}</el-descriptions-item>
        <el-descriptions-item label="专业方向">{{ detail.specialty || '-' }}</el-descriptions-item>
        <el-descriptions-item label="审核状态">
          <el-tag size="small" :type="auditType(detail.audit_status)">{{ auditText(detail.audit_status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="申请时间">{{ detail.created_at || '-' }}</el-descriptions-item>
      </el-descriptions>
      <div style="margin-top: 16px">
        <el-button
          type="success"
          :disabled="detail.audit_status !== 0"
          @click="doAudit(detailType, detail, 1)"
        >
          审核通过
        </el-button>
        <el-button
          type="danger"
          :disabled="detail.audit_status !== 0"
          @click="doAudit(detailType, detail, 2)"
        >
          审核拒绝
        </el-button>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import StatCard from '@/components/StatCard.vue'
import { adminApi } from '@/api/admin'
import { AUDIT_STATUS, auditText, auditType } from '@/utils/format'

const g = {
  orange: 'linear-gradient(135deg, #F5872A 0%, #FFAE5C 100%)',
  blue: 'linear-gradient(135deg, #1B3A6B 0%, #2F5DA8 100%)',
  green: 'linear-gradient(135deg, #0F9D8C 0%, #2BC4AE 100%)',
  slate: 'linear-gradient(135deg, #5B6B85 0%, #8A9BB5 100%)',
}

const activeTab = ref('doctor')
const loading = ref(false)
const overview = ref({ pending_doctor: 0, pending_coach: 0, today_audited: 0, total_apply: 0 })

const doctorList = ref([])
const doctorTotal = ref(0)
const doctorQuery = reactive({ doctor_name: '', real_name: '', audit_status: 0, page: 1, page_size: 10 })

const coachList = ref([])
const coachTotal = ref(0)
const coachQuery = reactive({ coach_name: '', real_name: '', audit_status: 0, page: 1, page_size: 10 })

const recordList = ref([])
const recordTotal = ref(0)
const recordDateRange = ref([])
const recordQuery = reactive({ audit_type: '', keyword: '', page: 1, page_size: 10 })

const detailVisible = ref(false)
const detailLoading = ref(false)
const detail = ref({})
const detailType = ref('doctor')

async function loadOverview() {
  try {
    const { data } = await adminApi.auditOverview()
    overview.value = data
  } catch (e) {
    /* 拦截器已提示 */
  }
}

async function loadDoctors() {
  loading.value = true
  try {
    const { data } = await adminApi.doctorList(doctorQuery)
    doctorList.value = data.list || []
    doctorTotal.value = data.total || 0
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

async function loadCoaches() {
  loading.value = true
  try {
    const { data } = await adminApi.coachList(coachQuery)
    coachList.value = data.list || []
    coachTotal.value = data.total || 0
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

async function loadRecords() {
  loading.value = true
  try {
    const { data } = await adminApi.auditRecordList({
      ...recordQuery,
      start_date: recordDateRange.value?.[0],
      end_date: recordDateRange.value?.[1],
    })
    recordList.value = data.list || []
    recordTotal.value = data.total || 0
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

function onTabChange(name) {
  if (name === 'doctor') loadDoctors()
  else if (name === 'coach') loadCoaches()
  else loadRecords()
}

function search() {
  if (activeTab.value === 'doctor') searchDoctor()
  else if (activeTab.value === 'coach') searchCoach()
  else searchRecord()
}

function searchDoctor() {
  doctorQuery.page = 1
  loadDoctors()
}
function searchCoach() {
  coachQuery.page = 1
  loadCoaches()
}
function searchRecord() {
  recordQuery.page = 1
  loadRecords()
}

function resetDoctor() {
  Object.assign(doctorQuery, { doctor_name: '', real_name: '', audit_status: '', page: 1 })
  loadDoctors()
}
function resetCoach() {
  Object.assign(coachQuery, { coach_name: '', real_name: '', audit_status: '', page: 1 })
  loadCoaches()
}
function resetRecord() {
  Object.assign(recordQuery, { audit_type: '', keyword: '', page: 1 })
  recordDateRange.value = []
  loadRecords()
}

async function openDetail(type, row) {
  detailType.value = type
  detailVisible.value = true
  detailLoading.value = true
  try {
    const api = type === 'doctor' ? adminApi.doctorDetail : adminApi.coachDetail
    const { data } = await api(row.id)
    detail.value = data
  } catch (e) {
    detail.value = {}
  } finally {
    detailLoading.value = false
  }
}

async function doAudit(type, row, status) {
  const name = type === 'doctor' ? row.doctor_name : row.coach_name
  const label = type === 'doctor' ? '医生' : '健身教练'
  const action = status === 1 ? '通过' : '拒绝'
  await ElMessageBox.confirm(
    `确定要${action}${label}【${name}】的注册申请吗？${status === 1 ? '通过后该账号即可登录工作台。' : '拒绝后该账号将无法登录。'}`,
    '二次确认',
    { type: 'warning', confirmButtonText: `确定${action}` }
  ).catch(() => Promise.reject(new Error('cancel')))

  try {
    const fn = type === 'doctor' ? adminApi.doctorAudit : adminApi.coachAudit
    const { msg } = await fn({ id: row.id, audit_status: status })
    ElMessage.success(msg || `审核${action}成功`)
    detailVisible.value = false
    await loadOverview()
    if (type === 'doctor') loadDoctors()
    else loadCoaches()
  } catch (e) {
    /* 拦截器已提示 / 用户取消 */
  }
}

onMounted(() => {
  loadOverview()
  loadDoctors()
})
</script>
