<template>
  <div class="hms-page">
    <div class="hms-card">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="操作日志" name="log" />
        <el-tab-pane label="管理员个人中心" name="profile" />
        <el-tab-pane label="系统信息" name="info" />
      </el-tabs>

      <!-- 操作日志（只读） -->
      <template v-if="activeTab === 'log'">
        <div class="hms-filter hms-mb-12">
          <el-select v-model="query.operation_type" placeholder="操作类型" clearable filterable style="width: 190px">
            <el-option v-for="t in types" :key="t" :label="t" :value="t" />
          </el-select>
          <el-input v-model="query.keyword" placeholder="操作内容关键词" clearable style="width: 210px" @keyup.enter="search" />
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

        <el-table :data="logs" v-loading="loading" stripe>
          <el-table-column prop="admin_name" label="管理员" width="110" />
          <el-table-column prop="operation_type" label="操作类型" width="150" />
          <el-table-column prop="operation_content" label="操作内容" min-width="380" />
          <el-table-column prop="target_type" label="目标类型" width="140" />
          <el-table-column label="目标ID" width="90">
            <template #default="{ row }">{{ row.target_id ?? '-' }}</template>
          </el-table-column>
          <el-table-column prop="created_at" label="操作时间" width="180" />
        </el-table>

        <div class="hms-pagination">
          <el-pagination
            v-model:current-page="query.page"
            v-model:page-size="query.page_size"
            :total="total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @current-change="loadLogs"
            @size-change="search"
          />
        </div>
      </template>

      <!-- 管理员个人中心 -->
      <template v-else-if="activeTab === 'profile'">
        <div class="hms-grid-2">
          <div>
            <div class="avatar-box">
              <img class="big-avatar" :src="avatarUrl" alt="avatar" />
              <div>
                <el-upload
                  :show-file-list="false"
                  :http-request="doUploadAvatar"
                  :before-upload="beforeUpload"
                  accept=".jpg,.jpeg,.png,.webp"
                >
                  <el-button type="primary" :loading="uploading">
                    <el-icon><Upload /></el-icon>&nbsp;上传头像
                  </el-button>
                </el-upload>
                <div class="hms-muted" style="margin-top: 8px">支持 jpg / jpeg / png / webp</div>
              </div>
            </div>

            <el-descriptions :column="1" border class="hms-mb-12">
              <el-descriptions-item label="账号">{{ info.admin_name || '-' }}</el-descriptions-item>
              <el-descriptions-item label="真实姓名">{{ info.real_name || '-' }}</el-descriptions-item>
              <el-descriptions-item label="创建时间">{{ info.created_at || '-' }}</el-descriptions-item>
            </el-descriptions>

            <el-button type="primary" @click="openPwd">修改密码</el-button>
            <el-button type="danger" plain @click="logout">退出登录</el-button>
          </div>

          <div>
            <div class="hms-card__title"><span>权限说明</span></div>
            <el-alert type="info" :closable="false" show-icon title="管理员权限边界">
              <div style="line-height: 1.9">
                · 可审核医生 / 教练注册申请，可编辑其基础资料、重置其密码<br />
                · 可管理医患关系与教练学员关系（绑定 / 解除）<br />
                · 可查看全部用户健康数据与业务数据（只读监管）<br />
                · <b>不可篡改普通用户原始健康数据</b><br />
                · <b>不可冒充医生发布健康建议或医疗记录</b><br />
                · 关键操作全部写入操作日志，日志已脱敏且只读
              </div>
            </el-alert>
          </div>
        </div>
      </template>

      <!-- 系统信息 -->
      <template v-else>
        <el-descriptions :column="2" border v-loading="infoLoading">
          <el-descriptions-item label="系统名称">{{ sys.system_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="版本">{{ sys.version || '-' }}</el-descriptions-item>
          <el-descriptions-item label="后端">{{ sys.backend || '-' }}</el-descriptions-item>
          <el-descriptions-item label="数据库">{{ sys.database || '-' }}</el-descriptions-item>
          <el-descriptions-item label="PC 端">{{ sys.frontend || '-' }}</el-descriptions-item>
          <el-descriptions-item label="小程序端">{{ sys.miniapp || '-' }}</el-descriptions-item>
          <el-descriptions-item label="服务端口">{{ sys.port || '-' }}</el-descriptions-item>
          <el-descriptions-item label="API 基础地址">{{ sys.api_base_url || '-' }}</el-descriptions-item>
        </el-descriptions>

        <el-alert
          type="success"
          :closable="false"
          show-icon
          style="margin-top: 16px"
          title="本页仅展示非敏感信息，数据库密码 / JWT Secret / Token / 服务器敏感配置均不在展示范围内。"
        />
      </template>
    </div>

    <el-dialog v-model="pwdVisible" title="修改管理员密码" width="420px">
      <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-width="90px">
        <el-form-item label="原密码" prop="old_password">
          <el-input v-model="pwdForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="pwdForm.new_password" type="password" show-password placeholder="不少于 6 位" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm">
          <el-input v-model="pwdForm.confirm" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdVisible = false">取消</el-button>
        <el-button type="primary" :loading="pwdLoading" @click="submitPwd">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import { adminApi } from '@/api/admin'
import { ROLE_META, resolveFileUrl } from '@/utils/config'
import { clearAuth, getUserInfo, setUserInfo } from '@/utils/auth'

const route = useRoute()
const router = useRouter()

const activeTab = ref('log')
const loading = ref(false)
const infoLoading = ref(false)
const uploading = ref(false)
const logs = ref([])
const total = ref(0)
const types = ref([])
const dateRange = ref([])
const info = ref({})
const sys = ref({})
const query = reactive({ operation_type: '', keyword: '', page: 1, page_size: 10 })

const avatarUrl = computed(() => resolveFileUrl(info.value.avatar))

async function loadLogs() {
  loading.value = true
  try {
    const { data } = await adminApi.operationLogList({
      ...query,
      start_date: dateRange.value?.[0],
      end_date: dateRange.value?.[1],
    })
    logs.value = data.list || []
    total.value = data.total || 0
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

async function loadTypes() {
  try {
    types.value = (await adminApi.operationLogTypes()).data || []
  } catch (e) {
    types.value = []
  }
}

async function loadInfo() {
  infoLoading.value = true
  try {
    info.value = (await adminApi.info()).data || {}
    setUserInfo('admin', info.value)
  } catch (e) {
    info.value = getUserInfo('admin') || {}
  }
  try {
    sys.value = (await adminApi.systemInfo()).data || {}
  } catch (e) {
    sys.value = {}
  } finally {
    infoLoading.value = false
  }
}

function search() {
  query.page = 1
  loadLogs()
}

function reset() {
  Object.assign(query, { operation_type: '', keyword: '', page: 1 })
  dateRange.value = []
  loadLogs()
}

function beforeUpload(file) {
  const ext = (file.name.split('.').pop() || '').toLowerCase()
  if (!['jpg', 'jpeg', 'png', 'webp'].includes(ext)) {
    ElMessage.error('仅支持 jpg / jpeg / png / webp 格式图片')
    return false
  }
  return true
}

async function doUploadAvatar(options) {
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', options.file)
    const { data } = await adminApi.uploadAvatar(formData)
    info.value.avatar = data.avatar
    setUserInfo('admin', { ...(getUserInfo('admin') || {}), avatar: data.avatar })
    ElMessage.success('头像更新成功')
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    uploading.value = false
  }
}

const pwdVisible = ref(false)
const pwdLoading = ref(false)
const pwdFormRef = ref(null)
const pwdForm = reactive({ old_password: '', new_password: '', confirm: '' })
const pwdRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 位', trigger: 'blur' },
  ],
  confirm: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (rule, value, cb) =>
        value === pwdForm.new_password ? cb() : cb(new Error('两次输入的密码不一致')),
      trigger: 'blur',
    },
  ],
}

function openPwd() {
  Object.assign(pwdForm, { old_password: '', new_password: '', confirm: '' })
  pwdVisible.value = true
}

async function submitPwd() {
  const valid = await pwdFormRef.value.validate().catch(() => false)
  if (!valid) return
  pwdLoading.value = true
  try {
    await adminApi.updatePwd({
      old_password: pwdForm.old_password,
      new_password: pwdForm.new_password,
    })
    ElMessage.success('密码修改成功，请重新登录')
    pwdVisible.value = false
    clearAuth('admin')
    router.replace(ROLE_META.admin.loginPath)
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    pwdLoading.value = false
  }
}

function logout() {
  ElMessageBox.confirm('确定要退出登录吗？', '退出确认', { type: 'warning' })
    .then(async () => {
      try {
        await adminApi.logout()
      } catch (e) {
        /* 忽略 */
      }
      clearAuth('admin')
      ElMessage.success('已退出登录')
      router.replace(ROLE_META.admin.loginPath)
    })
    .catch(() => {})
}

onMounted(() => {
  const tab = route.query.tab
  activeTab.value = ['log', 'profile', 'info'].includes(tab) ? tab : 'log'
  loadTypes()
  loadLogs()
  loadInfo()
})
</script>

<style scoped>
.avatar-box {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.big-avatar {
  width: 88px;
  height: 88px;
  border-radius: 50%;
  object-fit: cover;
  background: #eef2f7;
  border: 3px solid #fff;
  box-shadow: 0 4px 14px rgba(24, 45, 82, 0.14);
}
</style>
