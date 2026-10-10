<template>
  <div class="hms-page">
    <div class="hms-card">
      <div class="hms-card__title">
        <span>医生业务监管</span>
        <span class="hms-muted">监管只读：管理员不得冒充医生发布专业建议或医疗记录</span>
      </div>

      <el-tabs v-model="activeTab" @tab-change="search">
        <el-tab-pane label="健康建议" name="advice" />
        <el-tab-pane label="体检通知" name="notice" />
        <el-tab-pane label="医疗记录" name="record" />
      </el-tabs>

      <div class="hms-filter hms-mb-12">
        <el-select v-model="query.doctor_id" placeholder="按医生筛选" clearable filterable style="width: 210px">
          <el-option
            v-for="d in doctors"
            :key="d.id"
            :label="`${d.real_name || '-'}（${d.doctor_name}）`"
            :value="d.id"
          />
        </el-select>
        <el-select v-model="query.user_id" placeholder="按患者筛选" clearable filterable style="width: 210px">
          <el-option
            v-for="u in users"
            :key="u.id"
            :label="`${u.nickname}（${u.phone}）`"
            :value="u.id"
          />
        </el-select>
        <el-input v-model="query.keyword" placeholder="关键词" clearable style="width: 180px" @keyup.enter="search" />
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

      <el-table v-if="activeTab === 'advice'" :data="list" v-loading="loading" stripe>
        <el-table-column prop="doctor_real_name" label="医生" width="110" />
        <el-table-column prop="doctor_name" label="医生账号" width="120" />
        <el-table-column label="患者" width="150">
          <template #default="{ row }">{{ row.nickname || '-' }}（{{ row.phone || '-' }}）</template>
        </el-table-column>
        <el-table-column prop="advice_content" label="健康建议内容" min-width="360" />
        <el-table-column prop="created_at" label="发送时间" width="180" />
      </el-table>

      <el-table v-else-if="activeTab === 'notice'" :data="list" v-loading="loading" stripe>
        <el-table-column prop="doctor_real_name" label="医生" width="110" />
        <el-table-column label="患者" width="150">
          <template #default="{ row }">{{ row.nickname || '-' }}（{{ row.phone || '-' }}）</template>
        </el-table-column>
        <el-table-column prop="notice_title" label="通知标题" min-width="170" />
        <el-table-column prop="notice_content" label="通知内容" min-width="240" show-overflow-tooltip />
        <el-table-column prop="check_date" label="检查时间" width="180" />
        <el-table-column prop="created_at" label="发送时间" width="180" />
      </el-table>

      <el-table v-else :data="list" v-loading="loading" stripe>
        <el-table-column prop="doctor_real_name" label="医生" width="110" />
        <el-table-column label="患者" width="150">
          <template #default="{ row }">{{ row.nickname || '-' }}（{{ row.phone || '-' }}）</template>
        </el-table-column>
        <el-table-column prop="record_title" label="记录标题" min-width="170" />
        <el-table-column prop="record_content" label="记录内容" min-width="260" show-overflow-tooltip />
        <el-table-column prop="record_date" label="记录日期" width="130" />
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

import { adminApi } from '@/api/admin'

const activeTab = ref('advice')
const loading = ref(false)
const list = ref([])
const total = ref(0)
const doctors = ref([])
const users = ref([])
const dateRange = ref([])
const query = reactive({ doctor_id: '', user_id: '', keyword: '', page: 1, page_size: 10 })

async function loadOptions() {
  try {
    doctors.value = (await adminApi.commonDoctors()).data || []
    users.value = (await adminApi.commonUsers()).data || []
  } catch (e) {
    /* 拦截器已提示 */
  }
}

async function load() {
  loading.value = true
  try {
    const params = {
      ...query,
      start_date: dateRange.value?.[0],
      end_date: dateRange.value?.[1],
    }
    let res
    if (activeTab.value === 'advice') res = await adminApi.doctorAdviceList(params)
    else if (activeTab.value === 'notice') res = await adminApi.medicalNoticeList(params)
    else res = await adminApi.medicalRecordList(params)
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
  Object.assign(query, { doctor_id: '', user_id: '', keyword: '', page: 1 })
  dateRange.value = []
  load()
}

onMounted(() => {
  loadOptions()
  load()
})
</script>
