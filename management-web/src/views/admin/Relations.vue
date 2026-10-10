<template>
  <div class="hms-page">
    <div class="hms-card">
      <el-tabs v-model="activeTab" @tab-change="onTabChange">
        <el-tab-pane label="医患关系" name="doctor" />
        <el-tab-pane label="教练学员关系" name="coach" />
      </el-tabs>

      <div class="hms-filter hms-mb-12">
        <el-select
          v-model="query.owner_id"
          :placeholder="activeTab === 'doctor' ? '按医生筛选' : '按教练筛选'"
          clearable
          filterable
          style="width: 220px"
        >
          <el-option
            v-for="item in owners"
            :key="item.id"
            :label="`${item.real_name || item.doctor_name || item.coach_name}（${item.doctor_name || item.coach_name}）`"
            :value="item.id"
          />
        </el-select>
        <el-input
          v-model="query.user_keyword"
          :placeholder="activeTab === 'doctor' ? '患者昵称 / 手机号' : '学员昵称 / 手机号'"
          clearable
          style="width: 220px"
          @keyup.enter="search"
        />
        <el-button type="primary" @click="search">查询</el-button>
        <el-button @click="reset">重置</el-button>
        <el-button type="success" @click="openBind">
          <el-icon><Plus /></el-icon>&nbsp;{{ activeTab === 'doctor' ? '绑定医患关系' : '绑定教练学员关系' }}
        </el-button>
      </div>

      <!-- 医患关系 -->
      <el-table v-if="activeTab === 'doctor'" :data="list" v-loading="loading" stripe>
        <el-table-column prop="doctor_real_name" label="医生姓名" width="120" />
        <el-table-column prop="doctor_name" label="医生账号" width="130" />
        <el-table-column prop="specialty" label="专业方向" width="130" />
        <el-table-column prop="nickname" label="患者昵称" width="140" />
        <el-table-column prop="phone" label="患者手机号" width="140" />
        <el-table-column prop="gender" label="性别" width="80" />
        <el-table-column prop="created_at" label="绑定时间" width="180" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="danger" @click="doUnbind(row)">解除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 教练学员关系 -->
      <el-table v-else :data="list" v-loading="loading" stripe>
        <el-table-column prop="coach_real_name" label="教练姓名" width="120" />
        <el-table-column prop="coach_name" label="教练账号" width="130" />
        <el-table-column prop="specialty" label="专业方向" width="130" />
        <el-table-column prop="nickname" label="学员昵称" width="140" />
        <el-table-column prop="phone" label="学员手机号" width="140" />
        <el-table-column prop="gender" label="性别" width="80" />
        <el-table-column prop="created_at" label="绑定时间" width="180" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="danger" @click="doUnbind(row)">解除</el-button>
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

    <!-- 绑定关系 -->
    <el-dialog
      v-model="bindVisible"
      :title="activeTab === 'doctor' ? '绑定医患关系' : '绑定教练学员关系'"
      width="480px"
    >
      <el-alert
        type="info"
        :closable="false"
        show-icon
        title="仅审核通过的医生 / 教练可建立关系；重复绑定会被数据库唯一约束与业务校验拒绝。"
        class="hms-mb-12"
      />
      <el-form ref="bindFormRef" :model="bindForm" :rules="bindRules" label-width="90px">
        <el-form-item :label="activeTab === 'doctor' ? '医生' : '教练'" prop="owner_id">
          <el-select v-model="bindForm.owner_id" filterable placeholder="请选择（仅显示已审核通过）" style="width: 100%">
            <el-option
              v-for="item in owners"
              :key="item.id"
              :label="`${item.real_name || item.doctor_name || item.coach_name}（${item.doctor_name || item.coach_name}）`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="activeTab === 'doctor' ? '患者' : '学员'" prop="user_id">
          <el-select v-model="bindForm.user_id" filterable placeholder="请选择用户" style="width: 100%">
            <el-option
              v-for="item in users"
              :key="item.id"
              :label="`${item.nickname}（${item.phone}）`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="bindVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitBind">确定绑定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { adminApi } from '@/api/admin'

const activeTab = ref('doctor')
const loading = ref(false)
const saving = ref(false)
const list = ref([])
const total = ref(0)
const owners = ref([])
const users = ref([])

const query = reactive({ owner_id: '', user_keyword: '', page: 1, page_size: 10 })

const bindVisible = ref(false)
const bindFormRef = ref(null)
const bindForm = reactive({ owner_id: '', user_id: '' })
const bindRules = {
  owner_id: [{ required: true, message: '请选择', trigger: 'change' }],
  user_id: [{ required: true, message: '请选择用户', trigger: 'change' }],
}

async function loadOwners() {
  try {
    const { data } = activeTab.value === 'doctor' ? await adminApi.commonDoctors() : await adminApi.commonCoaches()
    owners.value = data || []
  } catch (e) {
    owners.value = []
  }
}

async function loadUsers() {
  try {
    const { data } = await adminApi.commonUsers()
    users.value = data || []
  } catch (e) {
    users.value = []
  }
}

async function load() {
  loading.value = true
  try {
    const params = {
      page: query.page,
      page_size: query.page_size,
      user_keyword: query.user_keyword,
    }
    let res
    if (activeTab.value === 'doctor') {
      params.doctor_id = query.owner_id
      res = await adminApi.doctorPatientList(params)
    } else {
      params.coach_id = query.owner_id
      res = await adminApi.coachStudentList(params)
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
  query.owner_id = ''
  query.user_keyword = ''
  query.page = 1
  load()
}

function onTabChange() {
  query.owner_id = ''
  query.page = 1
  loadOwners()
  load()
}

function openBind() {
  bindForm.owner_id = ''
  bindForm.user_id = ''
  bindVisible.value = true
}

async function submitBind() {
  const valid = await bindFormRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const payload =
      activeTab.value === 'doctor'
        ? { doctor_id: bindForm.owner_id, user_id: bindForm.user_id }
        : { coach_id: bindForm.owner_id, user_id: bindForm.user_id }
    const fn = activeTab.value === 'doctor' ? adminApi.bindPatient : adminApi.bindStudent
    const { msg } = await fn(payload)
    ElMessage.success(msg || '绑定成功')
    bindVisible.value = false
    search()
  } catch (e) {
    /* 重复绑定 / 未审核 等错误由拦截器提示 */
  } finally {
    saving.value = false
  }
}

async function doUnbind(row) {
  const ownerName =
    activeTab.value === 'doctor' ? row.doctor_real_name || row.doctor_name : row.coach_real_name || row.coach_name
  await ElMessageBox.confirm(
    `确定要解除【${ownerName}】与【${row.nickname}】的${
      activeTab.value === 'doctor' ? '医患' : '教练学员'
    }关系吗？解除后该${activeTab.value === 'doctor' ? '医生' : '教练'}将无法再读取此用户数据。`,
    '二次确认',
    { type: 'warning', confirmButtonText: '确定解除' }
  ).catch(() => Promise.reject(new Error('cancel')))

  try {
    const payload =
      activeTab.value === 'doctor'
        ? { doctor_id: row.doctor_id, user_id: row.user_id }
        : { coach_id: row.coach_id, user_id: row.user_id }
    const fn = activeTab.value === 'doctor' ? adminApi.unbindPatient : adminApi.unbindStudent
    const { msg } = await fn(payload)
    ElMessage.success(msg || '关系已解除')
    load()
  } catch (e) {
    /* 拦截器已提示 / 用户取消 */
  }
}

onMounted(() => {
  loadOwners()
  loadUsers()
  load()
})
</script>
