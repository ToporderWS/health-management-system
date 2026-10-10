<template>
  <div class="lp lp--coach">
    <div class="lp__art" aria-hidden="true"></div>

    <div class="lp__inner">
      <header class="lp__brand">
        <div class="lp__brand-logo">
          <el-icon><Basketball /></el-icon>
        </div>
        <div>
          <div class="lp__brand-name">个人健康管理系统</div>
          <div class="lp__brand-sub">健身教练工作台 · Coach Console</div>
        </div>
      </header>

      <div class="lp__main">
        <div class="lp__copy">
          <h1 class="lp__slogan">
            <span>科学训练</span>
            <span>成就更好的自己</span>
          </h1>
          <ul class="lp__features">
            <li class="lp__feature">
              <span class="lp__feature-icon"><el-icon><Calendar /></el-icon></span>
              <span class="lp__feature-label">训练计划</span>
            </li>
            <li class="lp__feature">
              <span class="lp__feature-icon"><el-icon><DataAnalysis /></el-icon></span>
              <span class="lp__feature-label">学员数据</span>
            </li>
            <li class="lp__feature">
              <span class="lp__feature-icon"><el-icon><Aim /></el-icon></span>
              <span class="lp__feature-label">目标管理</span>
            </li>
          </ul>
        </div>

        <section class="lp__card">
          <div class="lp__card-head">
            <div class="lp__card-icon">
              <el-icon><Basketball /></el-icon>
            </div>
            <div>
              <div class="lp__card-title">健身教练登录</div>
              <div class="lp__card-sub">Coach Console</div>
            </div>
          </div>

          <el-form ref="formRef" :model="form" :rules="rules" class="lp__form" @keyup.enter="submit">
            <el-form-item prop="coach_name">
              <el-input v-model="form.coach_name" size="large" placeholder="请输入教练账号" clearable>
                <template #prefix><el-icon><User /></el-icon></template>
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
              <el-button link class="lp__link--reg" @click="router.push('/coach/register')">申请注册</el-button>
              <el-button link class="lp__link--back" @click="router.push('/')">返回身份选择</el-button>
            </div>

            <div class="lp__note">注册后需等待管理员审核，审核通过（audit_status = 1）方可登录。</div>
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

import { coachApi } from '@/api/coach'
import { ROLE } from '@/utils/config'
import { setAuth } from '@/utils/auth'

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const formRef = ref(null)
const form = reactive({ coach_name: '', password: '' })

const rules = {
  coach_name: [{ required: true, message: '请输入教练账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function submit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    const { data } = await coachApi.login({ ...form })
    setAuth(ROLE.COACH, data.token, data.coach_info)
    ElMessage.success('登录成功')
    const redirect = route.query.redirect
    router.replace(typeof redirect === 'string' && redirect.startsWith('/coach') ? redirect : '/coach/dashboard')
  } catch (e) {
    /* 提示由拦截器统一处理 */
  } finally {
    loading.value = false
  }
}
</script>

<style>
@import '@/assets/login-portal.css';
</style>
