<template>
  <div class="hms-page">
    <div class="hms-card">
      <div class="hms-card__title">
        <span>内容运营管理</span>
        <el-button type="primary" @click="openDialog()">
          <el-icon><Plus /></el-icon>&nbsp;{{ activeTab === 'article' ? '新增文章' : '新增公告' }}
        </el-button>
      </div>

      <el-tabs v-model="activeTab" @tab-change="search">
        <el-tab-pane label="健康科普" name="article" />
        <el-tab-pane label="系统公告" name="notice" />
      </el-tabs>

      <div class="hms-filter hms-mb-12">
        <el-input
          v-model="query.keyword"
          :placeholder="activeTab === 'article' ? '标题 / 作者' : '标题 / 内容'"
          clearable
          style="width: 240px"
          @keyup.enter="search"
        />
        <el-select v-model="query.is_show" placeholder="显示状态" clearable style="width: 140px">
          <el-option label="显示" :value="1" />
          <el-option label="隐藏" :value="0" />
        </el-select>
        <el-button type="primary" @click="search">查询</el-button>
        <el-button @click="reset">重置</el-button>
      </div>

      <!-- 健康科普 -->
      <el-table v-if="activeTab === 'article'" :data="list" v-loading="loading" stripe>
        <el-table-column label="封面" width="90">
          <template #default="{ row }">
            <img class="cover" :src="resolveFileUrl(row.cover_img)" alt="cover" />
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="220" />
        <el-table-column prop="author" label="作者" width="120" />
        <el-table-column prop="publish_time" label="发布时间" width="180" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.is_show ? 'success' : 'info'">
              {{ row.is_show ? '显示' : '隐藏' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="230" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)">详情</el-button>
            <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
            <el-button link :type="row.is_show ? 'warning' : 'success'" @click="toggleShow(row)">
              {{ row.is_show ? '隐藏' : '显示' }}
            </el-button>
            <el-button link type="danger" @click="doDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 系统公告 -->
      <el-table v-else :data="list" v-loading="loading" stripe>
        <el-table-column prop="title" label="标题" min-width="240" />
        <el-table-column prop="content" label="内容" min-width="300" show-overflow-tooltip />
        <el-table-column prop="publish_time" label="发布时间" width="180" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.is_show ? 'success' : 'info'">
              {{ row.is_show ? '显示' : '隐藏' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
            <el-button link :type="row.is_show ? 'warning' : 'success'" @click="toggleShow(row)">
              {{ row.is_show ? '隐藏' : '显示' }}
            </el-button>
            <el-button link type="danger" @click="doDelete(row)">删除</el-button>
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

    <!-- 新增 / 编辑 -->
    <el-dialog
      v-model="dialogVisible"
      :title="`${form.id ? '编辑' : '新增'}${activeTab === 'article' ? '健康科普文章' : '系统公告'}`"
      width="680px"
      top="6vh"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" maxlength="200" show-word-limit placeholder="请输入标题" />
        </el-form-item>

        <el-form-item v-if="activeTab === 'article'" label="封面">
          <div class="cover-upload">
            <img v-if="form.cover_img" class="cover cover--lg" :src="resolveFileUrl(form.cover_img)" alt="cover" />
            <el-upload
              :show-file-list="false"
              :http-request="doUploadCover"
              :before-upload="beforeUpload"
              accept=".jpg,.jpeg,.png,.webp"
            >
              <el-button :loading="uploading">
                <el-icon><Upload /></el-icon>&nbsp;上传封面
              </el-button>
            </el-upload>
            <span class="hms-muted">支持 jpg / jpeg / png / webp，数据库仅保存文件名</span>
          </div>
        </el-form-item>

        <el-form-item v-if="activeTab === 'article'" label="作者" prop="author">
          <el-input v-model="form.author" maxlength="50" placeholder="默认：健康编辑部" />
        </el-form-item>

        <el-form-item label="发布时间" prop="publish_time">
          <el-date-picker
            v-model="form.publish_time"
            type="datetime"
            value-format="YYYY-MM-DD HH:mm:ss"
            placeholder="不填则使用当前时间"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="显示状态" prop="is_show">
          <el-radio-group v-model="form.is_show">
            <el-radio :value="1">显示</el-radio>
            <el-radio :value="0">隐藏</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="正文" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="9" placeholder="请输入正文内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 文章详情 -->
    <el-drawer v-model="detailVisible" :title="detail.title || '文章详情'" size="52%">
      <div v-loading="detailLoading">
        <div class="hms-muted hms-mb-12">
          作者：{{ detail.author || '-' }} &nbsp;|&nbsp; 发布时间：{{ detail.publish_time || '-' }}
        </div>
        <img v-if="detail.cover_img" class="detail-cover" :src="resolveFileUrl(detail.cover_img)" alt="cover" />
        <p class="detail-content">{{ detail.content }}</p>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { adminApi } from '@/api/admin'
import { resolveFileUrl } from '@/utils/config'

const activeTab = ref('article')
const loading = ref(false)
const saving = ref(false)
const uploading = ref(false)
const list = ref([])
const total = ref(0)
const query = reactive({ keyword: '', is_show: '', page: 1, page_size: 10 })

const dialogVisible = ref(false)
const formRef = ref(null)
const emptyForm = {
  id: '',
  title: '',
  cover_img: '',
  author: '健康编辑部',
  content: '',
  publish_time: '',
  is_show: 1,
}
const form = reactive({ ...emptyForm })

const detailVisible = ref(false)
const detailLoading = ref(false)
const detail = ref({})

const rules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入正文内容', trigger: 'blur' }],
}

async function load() {
  loading.value = true
  try {
    const api = activeTab.value === 'article' ? adminApi.articleList : adminApi.noticeList
    const { data } = await api(query)
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
  Object.assign(query, { keyword: '', is_show: '', page: 1 })
  load()
}

function openDialog(row) {
  Object.assign(form, emptyForm)
  if (row) {
    Object.assign(form, {
      id: row.id,
      title: row.title,
      cover_img: row.cover_img || '',
      author: row.author || '健康编辑部',
      content: row.content,
      publish_time: row.publish_time,
      is_show: row.is_show,
    })
  }
  dialogVisible.value = true
}

function beforeUpload(file) {
  const ext = (file.name.split('.').pop() || '').toLowerCase()
  if (!['jpg', 'jpeg', 'png', 'webp'].includes(ext)) {
    ElMessage.error('仅支持 jpg / jpeg / png / webp 格式图片')
    return false
  }
  return true
}

async function doUploadCover(options) {
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', options.file)
    const { data } = await adminApi.uploadCover(formData)
    form.cover_img = data.cover_img
    ElMessage.success('封面上传成功')
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    uploading.value = false
  }
}

async function submit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const api = activeTab.value === 'article' ? adminApi.articleSave : adminApi.noticeSave
    const { msg } = await api({ ...form })
    ElMessage.success(msg || '保存成功')
    dialogVisible.value = false
    search()
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    saving.value = false
  }
}

async function toggleShow(row) {
  try {
    const api = activeTab.value === 'article' ? adminApi.articleSave : adminApi.noticeSave
    const { msg } = await api({ ...row, is_show: row.is_show ? 0 : 1 })
    ElMessage.success(msg || '状态已更新')
    load()
  } catch (e) {
    /* 拦截器已提示 */
  }
}

async function doDelete(row) {
  const label = activeTab.value === 'article' ? '文章' : '公告'
  await ElMessageBox.confirm(`确定要删除${label}【${row.title}】吗？删除后不可恢复。`, '删除确认', {
    type: 'warning',
    confirmButtonText: '确定删除',
  }).catch(() => Promise.reject(new Error('cancel')))

  try {
    const api = activeTab.value === 'article' ? adminApi.articleDel : adminApi.noticeDel
    const { msg } = await api(row.id)
    ElMessage.success(msg || '删除成功')
    load()
  } catch (e) {
    /* 拦截器已提示 / 用户取消 */
  }
}

async function openDetail(row) {
  detailVisible.value = true
  detailLoading.value = true
  try {
    const { data } = await adminApi.articleDetail(row.id)
    detail.value = data
  } catch (e) {
    detail.value = {}
  } finally {
    detailLoading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.cover {
  width: 56px;
  height: 40px;
  border-radius: 6px;
  object-fit: cover;
  background: #eef2f7;
}

.cover--lg {
  width: 120px;
  height: 76px;
}

.cover-upload {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.detail-cover {
  width: 100%;
  max-height: 260px;
  object-fit: cover;
  border-radius: 10px;
  margin-bottom: 16px;
}

.detail-content {
  white-space: pre-wrap;
  line-height: 1.9;
  color: #3d4d63;
  font-size: 14px;
}
</style>
