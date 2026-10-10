<template>
  <div class="layout" :style="themeVars">
    <!-- 左侧固定导航 -->
    <aside class="layout__aside" :class="{ 'is-collapse': collapsed }">
      <div class="layout__logo">
        <div class="layout__logo-mark">
          <el-icon><FirstAidKit /></el-icon>
        </div>
        <div v-show="!collapsed" class="layout__logo-text">
          <div class="layout__logo-title">个人健康管理系统</div>
          <div class="layout__logo-sub">{{ roleLabel }}工作台</div>
        </div>
      </div>

      <el-scrollbar class="layout__menu-wrap">
        <el-menu
          :default-active="activeMenu"
          :collapse="collapsed"
          :collapse-transition="false"
          background-color="transparent"
          text-color="rgba(255,255,255,0.72)"
          active-text-color="#ffffff"
          router
        >
          <el-menu-item v-for="item in menus" :key="item.path" :index="item.path">
            <el-icon><component :is="item.icon" /></el-icon>
            <template #title>{{ item.title }}</template>
          </el-menu-item>
        </el-menu>
      </el-scrollbar>
    </aside>

    <!-- 右侧主体 -->
    <div class="layout__main">
      <header class="layout__header">
        <div class="layout__header-left">
          <el-icon class="layout__collapse" @click="collapsed = !collapsed">
            <component :is="collapsed ? 'Expand' : 'Fold'" />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item>{{ roleLabel }}工作台</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <div class="layout__header-right">
          <el-tag :type="tagType" effect="light" round size="small">{{ roleLabel }}</el-tag>
          <el-dropdown @command="handleCommand">
            <div class="layout__user">
              <img class="hms-avatar" :src="avatarUrl" alt="avatar" />
              <span class="layout__user-name">{{ displayName }}</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="pwd">修改密码</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <main class="layout__content">
        <router-view />
      </main>
    </div>

    <!-- 修改密码 -->
    <el-dialog v-model="pwdVisible" title="修改密码" width="420px">
      <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-width="90px">
        <el-form-item label="原密码" prop="old_password">
          <el-input v-model="pwdForm.old_password" type="password" show-password placeholder="请输入原密码" />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="pwdForm.new_password" type="password" show-password placeholder="不少于 6 位" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm">
          <el-input v-model="pwdForm.confirm" type="password" show-password placeholder="请再次输入新密码" />
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
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import { adminApi } from '@/api/admin'
import { coachApi } from '@/api/coach'
import { doctorApi } from '@/api/doctor'
import { ROLE, ROLE_META, resolveFileUrl } from '@/utils/config'
import { authState, clearAuth, getUserInfo, setUserInfo } from '@/utils/auth'

const props = defineProps({
  role: { type: String, required: true },
  menus: { type: Array, required: true },
  profilePath: { type: String, required: true },
})

const route = useRoute()
const router = useRouter()
const collapsed = ref(false)

const meta = computed(() => ROLE_META[props.role])
const roleLabel = computed(() => meta.value.label)
const themeVars = computed(() => ({
  '--role-primary': meta.value.primary,
  '--role-primary-dark': meta.value.primaryDark,
  '--role-gradient': meta.value.gradient,
}))

const tagType = computed(
  () => ({ [ROLE.DOCTOR]: 'success', [ROLE.COACH]: 'primary', [ROLE.ADMIN]: 'danger' })[props.role]
)

const activeMenu = computed(() => route.path)
const currentTitle = computed(() => route.meta?.title || '')

const userInfo = computed(() => authState[props.role].info || getUserInfo(props.role) || {})
const displayName = computed(
  () => userInfo.value.real_name || userInfo.value.nickname || userInfo.value.admin_name || roleLabel.value
)
const avatarUrl = computed(() => resolveFileUrl(userInfo.value.avatar))

const apiMap = { [ROLE.DOCTOR]: doctorApi, [ROLE.COACH]: coachApi, [ROLE.ADMIN]: adminApi }
const currentApi = computed(() => apiMap[props.role])

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

function handleCommand(command) {
  if (command === 'profile') {
    router.push(props.profilePath)
  } else if (command === 'pwd') {
    pwdForm.old_password = ''
    pwdForm.new_password = ''
    pwdForm.confirm = ''
    pwdVisible.value = true
  } else if (command === 'logout') {
    confirmLogout()
  }
}

async function submitPwd() {
  const valid = await pwdFormRef.value.validate().catch(() => false)
  if (!valid) return
  pwdLoading.value = true
  try {
    await currentApi.value.updatePwd({
      old_password: pwdForm.old_password,
      new_password: pwdForm.new_password,
    })
    ElMessage.success('密码修改成功，请重新登录')
    pwdVisible.value = false
    clearAuth(props.role)
    router.replace(meta.value.loginPath)
  } catch (e) {
    /* 错误提示由拦截器统一处理 */
  } finally {
    pwdLoading.value = false
  }
}

function confirmLogout() {
  ElMessageBox.confirm('确定要退出登录吗？', '退出确认', {
    type: 'warning',
    confirmButtonText: '确定退出',
    cancelButtonText: '取消',
  })
    .then(async () => {
      try {
        await currentApi.value.logout()
      } catch (e) {
        /* 退出接口失败也要清理本地登录态 */
      }
      clearAuth(props.role)
      ElMessage.success('已退出登录')
      router.replace(meta.value.loginPath)
    })
    .catch(() => {})
}

/** 供子页面在更新个人资料后同步顶部显示 */
function syncUserInfo(patch) {
  setUserInfo(props.role, { ...userInfo.value, ...patch })
}
defineExpose({ syncUserInfo })
</script>

<style scoped>
.layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* ---------- 侧边栏 ---------- */
.layout__aside {
  width: 232px;
  flex-shrink: 0;
  background: var(--role-gradient);
  display: flex;
  flex-direction: column;
  transition: width 0.2s;
  overflow: hidden;
}

.layout__aside.is-collapse {
  width: 64px;
}

.layout__logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 14px;
  height: 64px;
  flex-shrink: 0;
}

.layout__logo-mark {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.18);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 20px;
  flex-shrink: 0;
}

.layout__logo-text {
  overflow: hidden;
  white-space: nowrap;
}

.layout__logo-title {
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.3;
}

.layout__logo-sub {
  color: rgba(255, 255, 255, 0.68);
  font-size: 12px;
  line-height: 1.4;
}

.layout__menu-wrap {
  flex: 1;
  overflow: hidden;
}

.layout__menu-wrap :deep(.el-menu) {
  border-right: none;
}

.layout__menu-wrap :deep(.el-menu-item) {
  height: 46px;
  line-height: 46px;
  margin: 2px 8px;
  border-radius: 10px;
  font-size: 13.5px;
}

.layout__menu-wrap :deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.1) !important;
  color: #fff !important;
}

.layout__menu-wrap :deep(.el-menu-item.is-active) {
  background: rgba(255, 255, 255, 0.2) !important;
  color: #fff !important;
  font-weight: 600;
}

/* ---------- 主体 ---------- */
.layout__main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.layout__header {
  height: 64px;
  flex-shrink: 0;
  background: #fff;
  border-bottom: 1px solid var(--hms-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.layout__header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.layout__collapse {
  font-size: 18px;
  cursor: pointer;
  color: var(--hms-text-sub);
}

.layout__collapse:hover {
  color: var(--role-primary);
}

.layout__header-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.layout__user {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
  outline: none;
}

.layout__user:hover {
  background: #f3f6fa;
}

.layout__user-name {
  font-size: 13.5px;
  color: var(--hms-text);
}

.layout__content {
  flex: 1;
  overflow: auto;
  padding: 18px 20px 28px;
  background: var(--hms-bg);
}
</style>
