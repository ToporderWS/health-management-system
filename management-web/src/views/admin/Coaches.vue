<template>
  <div class="hms-page">
    <div class="hms-card">
      <div class="hms-card__title"><span>健身教练管理</span></div>

      <div class="hms-filter hms-mb-12">
        <el-input v-model="query.coach_name" placeholder="教练账号" clearable style="width: 150px" @keyup.enter="search" />
        <el-input v-model="query.real_name" placeholder="姓名" clearable style="width: 140px" @keyup.enter="search" />
        <el-input v-model="query.phone" placeholder="手机号" clearable style="width: 150px" @keyup.enter="search" />
        <el-input v-model="query.specialty" placeholder="专业方向" clearable style="width: 150px" @keyup.enter="search" />
        <el-select v-model="query.audit_status" placeholder="审核状态" clearable style="width: 140px">
          <el-option v-for="(v, k) in AUDIT_STATUS" :key="k" :label="v.text" :value="Number(k)" />
        </el-select>
        <el-button type="primary" @click="search">查询</el-button>
        <el-button @click="reset">重置</el-button>
      </div>

      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="coach_name" label="教练账号" width="130" />
        <el-table-column prop="real_name" label="姓名" width="110" />
        <el-table-column prop="gender" label="性别" width="70" />
        <el-table-column prop="phone" label="手机号" width="140" />
        <el-table-column prop="specialty" label="专业方向" min-width="130" />
        <el-table-column prop="student_count" label="负责学员数" width="110" />
        <el-table-column label="审核状态" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="auditType(row.audit_status)">{{ auditText(row.audit_status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="注册时间" width="180" />
        <el-table-column label="操作" width="210" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">详情</el-button>
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="warning" @click="openReset(row)">重置密码</el-button>
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

    <el-drawer v-model="detailVisible" :title="`教练详情 · ${detail.real_name || ''}`" size="62%">
      <div v-loading="detailLoading">
        <el-descriptions :column="3" border class="hms-mb-12">
          <el-descriptions-item label="教练账号">{{ detail.coach_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="姓名">{{ detail.real_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="性别">{{ detail.gender || '-' }}</el-descriptions-item>
          <el-descriptions-item label="手机号">{{ detail.phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="专业方向">{{ detail.specialty || '-' }}</el-descriptions-item>
          <el-descriptions-item label="审核状态">
            <el-tag size="small" :type="auditType(detail.audit_status)">{{ auditText(detail.audit_status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="负责学员数">{{ detail.student_count ?? 0 }}</el-descriptions-item>
          <el-descriptions-item label="运动目标数">{{ detail.business?.goal_count ?? 0 }}</el-descriptions-item>
          <el-descriptions-item label="训练计划数">{{ detail.business?.plan_count ?? 0 }}</el-descriptions-item>
          <el-descriptions-item label="健身建议数">{{ detail.business?.advice_count ?? 0 }}</el-descriptions-item>
          <el-descriptions-item label="注册时间">{{ detail.created_at || '-' }}</el-descriptions-item>
        </el-descriptions>

        <div class="hms-card__title"><span>负责学员列表</span></div>
        <el-table :data="detail.students || []" size="small" stripe>
          <el-table-column prop="nickname" label="学员" min-width="140" />
          <el-table-column prop="phone" label="手机号" width="140" />
          <el-table-column prop="gender" label="性别" width="80" />
          <el-table-column prop="age" label="年龄" width="80" />
        </el-table>
      </div>
    </el-drawer>

    <el-dialog v-model="editVisible" title="编辑教练基础资料" width="480px">
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="90px">
        <el-form-item label="姓名" prop="real_name">
          <el-input v-model="editForm.real_name" />
        </el-form-item>
        <el-form-item label="性别" prop="gender">
          <el-select v-model="editForm.gender" style="width: 100%">
            <el-option label="男" value="男" />
            <el-option label="女" value="女" />
          </el-select>
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="editForm.phone" />
        </el-form-item>
        <el-form-item label="专业方向" prop="specialty">
          <el-input v-model="editForm.specialty" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="resetVisible" title="重置教练登录密码" width="440px">
      <el-alert
        type="warning"
        :closable="false"
        show-icon
        title="重置后原密码立即失效，请将新密码线下告知教练本人。此操作会写入管理员操作日志。"
        class="hms-mb-12"
      />
      <el-form ref="resetFormRef" :model="resetForm" :rules="resetRules" label-width="90px">
        <el-form-item label="教练账号">
          <el-input :model-value="resetForm.coach_name" disabled />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="resetForm.new_password" type="password" show-password placeholder="不少于 6 位" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitReset">确定重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { adminApi } from '@/api/admin'
import { AUDIT_STATUS, auditText, auditType } from '@/utils/format'

const loading = ref(false)
const saving = ref(false)
const detailLoading = ref(false)
const list = ref([])
const total = ref(0)
const query = reactive({
  coach_name: '',
  real_name: '',
  phone: '',
  specialty: '',
  audit_status: '',
  page: 1,
  page_size: 10,
})

const detailVisible = ref(false)
const detail = ref({})

const editVisible = ref(false)
const editFormRef = ref(null)
const editForm = reactive({ id: '', real_name: '', gender: '', phone: '', specialty: '' })
const editRules = {
  real_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [{ pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' }],
}

const resetVisible = ref(false)
const resetFormRef = ref(null)
const resetForm = reactive({ id: '', coach_name: '', new_password: '' })
const resetRules = {
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 位', trigger: 'blur' },
  ],
}

async function load() {
  loading.value = true
  try {
    const { data } = await adminApi.coachList(query)
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
  Object.assign(query, { coach_name: '', real_name: '', phone: '', specialty: '', audit_status: '', page: 1 })
  load()
}

async function openDetail(row) {
  detailVisible.value = true
  detailLoading.value = true
  try {
    const { data } = await adminApi.coachDetail(row.id)
    detail.value = data
  } catch (e) {
    detail.value = {}
  } finally {
    detailLoading.value = false
  }
}

function openEdit(row) {
  Object.assign(editForm, {
    id: row.id,
    real_name: row.real_name || '',
    gender: row.gender || '',
    phone: row.phone || '',
    specialty: row.specialty || '',
  })
  editVisible.value = true
}

async function submitEdit() {
  const valid = await editFormRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const { msg } = await adminApi.coachUpdate({ ...editForm })
    ElMessage.success(msg || '教练资料更新成功')
    editVisible.value = false
    load()
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    saving.value = false
  }
}

function openReset(row) {
  Object.assign(resetForm, { id: row.id, coach_name: row.coach_name, new_password: '' })
  resetVisible.value = true
}

async function submitReset() {
  const valid = await resetFormRef.value.validate().catch(() => false)
  if (!valid) return
  await ElMessageBox.confirm(
    `确定要重置教练【${resetForm.coach_name}】的登录密码吗？重置后原密码立即失效。`,
    '二次确认',
    { type: 'warning', confirmButtonText: '确定重置' }
  ).catch(() => Promise.reject(new Error('cancel')))
  saving.value = true
  try {
    const { msg } = await adminApi.coachResetPwd({ id: resetForm.id, new_password: resetForm.new_password })
    ElMessage.success(msg || '密码重置成功')
    resetVisible.value = false
  } catch (e) {
    /* 拦截器已提示 / 用户取消 */
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
