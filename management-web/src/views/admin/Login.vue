<template>
  <div class="lp lp--admin">
    <div class="lp__art" aria-hidden="true"></div>

    <div class="lp__inner">
      <header class="lp__brand">
        <div class="lp__brand-logo">
          <el-icon><Setting /></el-icon>
        </div>
        <div>
          <div class="lp__brand-name">个人健康管理系统</div>
          <div class="lp__brand-sub">管理后台 · Admin Console</div>
        </div>
      </header>

      <div class="lp__main">
        <div class="lp__copy">
          <h1 class="lp__slogan">
            <span>全域监管</span>
            <span>让健康管理更高效</span>
          </h1>
          <ul class="lp__features">
            <li class="lp__feature">
              <span class="lp__feature-icon"><el-icon><TrendCharts /></el-icon></span>
              <span class="lp__feature-label">数据统计</span>
            </li>
            <li class="lp__feature">
              <span class="lp__feature-icon"><el-icon><UserFilled /></el-icon></span>
              <span class="lp__feature-label">用户管理</span>
            </li>
            <li class="lp__feature">
              <span class="lp__feature-icon"><el-icon><Tools /></el-icon></span>
              <span class="lp__feature-label">系统配置</span>
            </li>
          </ul>
        </div>

        <section class="lp__card">
          <div class="lp__card-head">
            <div class="lp__card-icon">
              <el-icon><Setting /></el-icon>
            </div>
            <div>
              <div class="lp__card-title">管理员登录</div>
              <div class="lp__card-sub">Admin Console</div>
            </div>
          </div>

          <el-form ref="formRef" :model="form" :rules="rules" class="lp__form" @keyup.enter="submit">
            <el-form-item prop="admin_name">
              <el-input v-model="form.admin_name" size="large" placeholder="请输入管理员账号" clearable>
                <template #prefix><el-icon><Avatar /></el-icon></template>
              </el-input>
            </el-form-item>
            <el-form-item prop="password">
              <el-input v-model="form.password" size="large" type="password" placeholder="请输入密码" show-password>
                <template #prefix><el-icon><Lock /></el-icon></template>
              </el-input>
            </el-form-item>

            <el-button type="primary" size="large" class="lp__btn" :loading="loading" @click="submit">
              登录<el-icon><ArrowRight /></el-icon>
            </el-button>

            <div class="lp__foot">
              <el-button link class="lp__link--back" @click="router.push('/')">返回身份选择</el-button>
            </div>

            <div class="lp__note">管理员账号由数据库初始化，不提供注册。</div>
          </el-form>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { adminApi } from '@/api/admin'
import { ROLE } from '@/utils/config'
import { setAuth } from '@/utils/auth'

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const formRef = ref(null)
const form = reactive({ admin_name: '', password: '' })

const rules = {
  admin_name: [{ required: true, message: '请输入管理员账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function submit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    const { data } = await adminApi.login({ ...form })
    setAuth(ROLE.ADMIN, data.token, data.admin_info)
    ElMessage.success('登录成功')
    const redirect = route.query.redirect
    router.replace(typeof redirect === 'string' && redirect.startsWith('/admin') ? redirect : '/admin/dashboard')
  } catch (e) {
    /* 错误提示由拦截器处理 */
  } finally {
    loading.value = false
  }
}
</script>

<style>
@import '@/assets/login-portal.css';
</style>
