<template>
  <div class="hms-page">
    <div class="hms-card">
      <div class="hms-card__title">
        <span>运动目标</span>
        <el-button type="primary" @click="openDialog()">
          <el-icon><Plus /></el-icon>&nbsp;创建运动目标
        </el-button>
      </div>

      <div class="hms-filter hms-mb-12">
        <PatientSelect v-model="query.user_id" role="coach" placeholder="按学员筛选" style="width: 200px" />
        <el-select v-model="query.goal_status" placeholder="状态" clearable style="width: 140px">
          <el-option v-for="(v, k) in SPORT_STATUS" :key="k" :label="v.text" :value="Number(k)" />
        </el-select>
        <el-input v-model="query.keyword" placeholder="搜索目标标题" clearable style="width: 200px" @keyup.enter="search" />
        <el-button type="primary" @click="search">查询</el-button>
        <el-button @click="reset">重置</el-button>
      </div>

      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column label="学员" width="150">
          <template #default="{ row }">{{ row.nickname || '-' }}</template>
        </el-table-column>
        <el-table-column prop="goal_title" label="目标标题" min-width="160" />
        <el-table-column prop="goal_content" label="目标内容" min-width="240" show-overflow-tooltip />
        <el-table-column prop="start_date" label="开始" width="120" />
        <el-table-column prop="end_date" label="结束" width="120" />
        <el-table-column label="状态" width="130">
          <template #default="{ row }">
            <el-select
              :model-value="row.goal_status"
              size="small"
              style="width: 104px"
              @change="(v) => changeStatus(row, v)"
            >
              <el-option v-for="(v, k) in SPORT_STATUS" :key="k" :label="v.text" :value="Number(k)" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
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

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑运动目标' : '创建运动目标'" width="600px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="学员" prop="user_id">
          <PatientSelect v-model="form.user_id" role="coach" placeholder="请选择您的学员" />
        </el-form-item>
        <el-form-item label="目标标题" prop="goal_title">
          <el-input v-model="form.goal_title" maxlength="100" placeholder="如：3 个月减脂 5kg" />
        </el-form-item>
        <el-form-item label="目标内容" prop="goal_content">
          <el-input v-model="form.goal_content" type="textarea" :rows="5" placeholder="请填写目标内容与执行要求" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="开始日期" prop="start_date">
              <el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束日期" prop="end_date">
              <el-date-picker v-model="form.end_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="状态" prop="goal_status">
          <el-select v-model="form.goal_status" style="width: 100%">
            <el-option v-for="(v, k) in SPORT_STATUS" :key="k" :label="v.text" :value="Number(k)" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import PatientSelect from '@/components/PatientSelect.vue'
import { coachApi } from '@/api/coach'
import { SPORT_STATUS } from '@/utils/format'

const loading = ref(false)
const saving = ref(false)
const list = ref([])
const total = ref(0)
const query = reactive({ user_id: '', goal_status: '', keyword: '', page: 1, page_size: 10 })

const dialogVisible = ref(false)
const formRef = ref(null)
const emptyForm = {
  id: '',
  user_id: '',
  goal_title: '',
  goal_content: '',
  start_date: '',
  end_date: '',
  goal_status: 0,
}
const form = reactive({ ...emptyForm })

const rules = {
  user_id: [{ required: true, message: '请选择学员', trigger: 'change' }],
  goal_title: [{ required: true, message: '请输入目标标题', trigger: 'blur' }],
  goal_content: [{ required: true, message: '请输入目标内容', trigger: 'blur' }],
  start_date: [{ required: true, message: '请选择开始日期', trigger: 'change' }],
  end_date: [{ required: true, message: '请选择结束日期', trigger: 'change' }],
}

async function load() {
  loading.value = true
  try {
    const { data } = await coachApi.goalList(query)
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
  Object.assign(query, { user_id: '', goal_status: '', keyword: '', page: 1 })
  load()
}

function openDialog(row) {
  Object.assign(form, emptyForm)
  if (row) {
    Object.assign(form, {
      id: row.id,
      user_id: row.user_id,
      goal_title: row.goal_title,
      goal_content: row.goal_content,
      start_date: row.start_date,
      end_date: row.end_date,
      goal_status: row.goal_status,
    })
  }
  dialogVisible.value = true
}

async function submit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  if (form.end_date < form.start_date) {
    ElMessage.warning('结束日期不能早于开始日期')
    return
  }
  saving.value = true
  try {
    const { msg } = await coachApi.goalSave({ ...form })
    ElMessage.success(msg || '保存成功')
    dialogVisible.value = false
    search()
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    saving.value = false
  }
}

async function changeStatus(row, status) {
  try {
    const { msg } = await coachApi.goalUpdateStatus({ id: row.id, goal_status: status })
    ElMessage.success(msg || '状态更新成功')
    load()
  } catch (e) {
    /* 拦截器已提示 */
  }
}

onMounted(load)
</script>
