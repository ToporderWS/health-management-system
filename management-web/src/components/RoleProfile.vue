<template>
  <div class="hms-page">
    <div class="hms-grid-2">
      <div class="hms-card">
        <div class="hms-card__title"><span>个人资料</span></div>

        <div class="profile__avatar-box">
          <img class="profile__avatar" :src="avatarUrl" alt="avatar" />
          <div class="profile__avatar-actions">
            <el-upload
              :show-file-list="false"
              :http-request="doUpload"
              :before-upload="beforeUpload"
              accept=".jpg,.jpeg,.png,.webp"
            >
              <el-button type="primary" :loading="uploading">
                <el-icon><Upload /></el-icon>&nbsp;上传头像
              </el-button>
            </el-upload>
            <div class="hms-muted">支持 jpg / jpeg / png / webp，文件名由后端以 UUID 重命名</div>
          </div>
        </div>

        <el-descriptions :column="1" border class="hms-mb-12">
          <el-descriptions-item label="账号">{{ info.username || '-' }}</el-descriptions-item>
          <el-descriptions-item label="姓名">{{ info.real_name || info.nickname || '-' }}</el-descriptions-item>
          <el-descriptions-item v-if="role !== 'admin'" label="性别">{{ info.gender || '-' }}</el-descriptions-item>
          <el-descriptions-item v-if="role !== 'admin'" label="手机号">{{ info.phone || '-' }}</el-descriptions-item>
          <el-descriptions-item v-if="role !== 'admin'" label="专业方向">{{ info.specialty || '-' }}</el-descriptions-item>
          <el-descriptions-item v-if="role === 'admin'" label="创建时间">{{ info.created_at || '-' }}</el-descriptions-item>
          <el-descriptions-item v-if="role !== 'admin'" label="审核状态">
            <el-tag size="small" :type="auditType(info.audit_status)">{{ auditText(info.audit_status) }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <el-button :loading="pwdLoading" @click="openPwd">修改密码</el-button>
        <el-button type="danger" plain @click="logout">退出登录</el-button>
      </div>

      <div class="hms-card">
        <div class="hms-card__title"><span>工作台信息</span></div>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="所属端">{{ meta.label }}工作台</el-descriptions-item>
          <el-descriptions-item label="系统">{{ meta.portalTitle }}</el-descriptions-item>
          <el-descriptions-item label="角色">{{ meta.label }}</el-descriptions-item>
          <el-descriptions-item label="权限说明">{{ permissionText }}</el-descriptions-item>
        </el-descriptions>

        <el-alert
          v-if="role !== 'admin'"
          class="hms-mb-12"
          style="margin-top: 16px"
          type="info"
          :closable="false"
          show-icon
          title="数据权限说明"
          :description="roleDescription"
        />
      </div>
    </div>

    <el-dialog v-model="pwdVisible" title="修改密码" width="420px">
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
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import { adminApi } from '@/api/admin'
import { coachApi } from '@/api/coach'
import { doctorApi } from '@/api/doctor'
import { ROLE, ROLE_META, resolveFileUrl } from '@/utils/config'
import { authState, clearAuth, getUserInfo, setAuth, setUserInfo, getToken } from '@/utils/auth'
import { auditText, auditType } from '@/utils/format'

const props = defineProps({
  role: { type: String, required: true },
})

const router = useRouter()
const uploading = ref(false)
const info = ref({})

const apiMap = { [ROLE.DOCTOR]: doctorApi, [ROLE.COACH]: coachApi, [ROLE.ADMIN]: adminApi }
const api = computed(() => apiMap[props.role])
const meta = computed(() => ROLE_META[props.role])
const avatarUrl = computed(() => resolveFileUrl(info.value.avatar))

const permissionText = computed(
  () =>
    ({
      [ROLE.DOCTOR]: '仅可访问本人负责患者的数据',
      [ROLE.COACH]: '仅可访问本人负责学员的数据',
      [ROLE.ADMIN]: '全域监管，不可篡改用户原始健康数据、不可冒充医生发布建议',
    })[props.role]
)

const roleDescription = computed(
  () =>
    ({
      [ROLE.DOCTOR]:
        '读取任何患者数据前，后端会校验 doctor_patient 中是否存在该医患关系；未绑定一律返回 401。',
      [ROLE.COACH]:
        '读取任何学员数据前，后端会校验 coach_student 中是否存在该教练学员关系；未绑定一律返回 401。',
    })[props.role]
)

async function loadInfo() {
  try {
    const { data } = await api.value.info()
    info.value = data
    setUserInfo(props.role, data)
  } catch (e) {
    info.value = getUserInfo(props.role) || {}
  }
  // 统一账号字段名，便于模板展示
  info.value = {
    ...info.value,
    username: info.value.doctor_name || info.value.coach_name || info.value.admin_name || '',
  }
}

function beforeUpload(file) {
  const ext = (file.name.split('.').pop() || '').toLowerCase()
  if (!['jpg', 'jpeg', 'png', 'webp'].includes(ext)) {
    ElMessage.error('仅支持 jpg / jpeg / png / webp 格式图片')
    return false
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过 10MB')
    return false
  }
  return true
}

async function doUpload(options) {
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', options.file)
    const { data } = await api.value.uploadAvatar(formData)
    info.value.avatar = data.avatar
    setUserInfo(props.role, { ...(getUserInfo(props.role) || {}), avatar: data.avatar })
    ElMessage.success('头像更新成功')
  } catch (e) {
    /* 拦截器已提示 */
  } finally {
    uploading.value = false
  }
}

// ---------------- 修改密码 ----------------
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
    await api.value.updatePwd({
      old_password: pwdForm.old_password,
      new_password: pwdForm.new_password,
    })
    ElMessage.success('密码修改成功，请重新登录')
    pwdVisible.value = false
    clearAuth(props.role)
    router.replace(meta.value.loginPath)
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
        await api.value.logout()
      } catch (e) {
        /* 忽略 */
      }
      clearAuth(props.role)
      ElMessage.success('已退出登录')
      router.replace(meta.value.loginPath)
    })
    .catch(() => {})
}

onMounted(loadInfo)
</script>

<style scoped>
.profile__avatar-box {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.profile__avatar {
  width: 88px;
  height: 88px;
  border-radius: 50%;
  object-fit: cover;
  background: #eef2f7;
  border: 3px solid #fff;
  box-shadow: 0 4px 14px rgba(24, 45, 82, 0.14);
}

.profile__avatar-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>
