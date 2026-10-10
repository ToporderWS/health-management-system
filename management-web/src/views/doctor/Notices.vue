<template>
  <div class="hms-page">
    <div class="hms-card">
      <div class="hms-card__title">
        <span>体检通知</span>
        <el-button type="primary" @click="openDialog">
          <el-icon><Plus /></el-icon>&nbsp;发送体检通知
        </el-button>
      </div>

      <div class="hms-filter hms-mb-12">
        <PatientSelect v-model="query.user_id" role="doctor" placeholder="按患者筛选" style="width: 220px" />
        <el-input v-model="query.keyword" placeholder="搜索标题 / 内容" clearable style="width: 220px" @keyup.enter="search" />
        <el-button type="primary" @click="search">查询</el-button>
        <el-button @click="reset">重置</el-button>
      </div>

      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="notice_title" label="通知标题" min-width="180" />
        <el-table-column label="患者" width="150">
          <template #default="{ row }">{{ row.nickname || '-' }}（{{ row.phone || '-' }}）</template>
        </el-table-column>
        <el-table-column prop="notice_content" label="通知内容" min-width="280" show-overflow-tooltip />
        <el-table-column prop="check_date" label="检查时间" width="180" />
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

    <el-dialog v-model="dialogVisible" title="发送体检通知" width="560px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="选择患者" prop="user_id">
          <PatientSelect v-model="form.user_id" role="doctor" placeholder="请选择您的患者" />
        </el-form-item>
        <el-form-item label="通知标题" prop="notice_title">
          <el-input v-model="form.notice_title" maxlength="200" placeholder="如：年度心血管专项体检通知" />
        </el-form-item>
        <el-form-item label="检查时间" prop="check_date">
          <el-date-picker
            v-model="form.check_date"
            type="datetime"
            value-format="YYYY-MM-DD HH:mm:ss"
            placeholder="选择建议检查时间"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="通知内容" prop="notice_content">
          <el-input v-model="form.notice_content" type="textarea" :rows="5" placeholder="请填写体检通知内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">保存并发送</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import PatientSelect from '@/components/PatientSelect.vue'
import { doctorApi } from '@/api/doctor'

const loading = ref(false)
const saving = ref(false)
const list = ref([])
const total = ref(0)
const query = reactive({ user_id: '', keyword: '', page: 1, page_size: 10 })

const dialogVisible = ref(false)
const formRef = ref(null)
const form = reactive({ user_id: '', notice_title: '', notice_content: '', check_date: '' })
const rules = {
  user_id: [{ required: true, message: '请选择患者', trigger: 'change' }],
  notice_title: [{ required: true, message: '请输入通知标题', trigger: 'blur' }],
  check_date: [{ required: true, message: '请选择检查时间', trigger: 'change' }],
  notice_content: [{ required: true, message: '请输入通知内容', trigger: 'blur' }],
}

async function load() {
  loading.value = true
  try {
    const { data } = await doctorApi.noticeList(query)
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
  query.user_id = ''
  query.keyword = ''
  query.page = 1
  load()
}

function openDialog() {
  Object.assign(form, { user_id: '', notice_title: '', notice_content: '', check_date: '' })
  dialogVisible.value = true
}

async function submit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const { msg } = await doctorApi.noticeSave({ ...form })
    ElMessage.success(msg || '体检通知已发送')
    dialogVisible.value = false
    search()
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
