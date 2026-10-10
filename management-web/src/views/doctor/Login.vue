<template>
  <div class="lp lp--doctor">
    <div class="lp__art" aria-hidden="true"></div>

    <div class="lp__inner">
      <header class="lp__brand">
        <div class="lp__brand-logo">
          <el-icon><FirstAidKit /></el-icon>
        </div>
        <div>
          <div class="lp__brand-name">个人健康管理系统</div>
          <div class="lp__brand-sub">医生工作台 · Doctor Console</div>
        </div>
      </header>

      <div class="lp__main">
        <div class="lp__copy">
          <h1 class="lp__slogan">
            <span>守护患者健康</span>
            <span>让医疗更有温度</span>
          </h1>
          <ul class="lp__features">
            <li class="lp__feature">
              <span class="lp__feature-icon"><el-icon><User /></el-icon></span>
              <span class="lp__feature-label">患者管理</span>
            </li>
            <li class="lp__feature">
              <span class="lp__feature-icon"><el-icon><Notebook /></el-icon></span>
              <span class="lp__feature-label">健康档案</span>
            </li>
            <li class="lp__feature">
              <span class="lp__feature-icon"><el-icon><ChatLineSquare /></el-icon></span>
              <span class="lp__feature-label">诊疗建议</span>
            </li>
          </ul>
        </div>

        <section class="lp__card">
          <div class="lp__card-head">
            <div class="lp__card-icon">
              <el-icon><FirstAidKit /></el-icon>
            </div>
            <div>
              <div class="lp__card-title">医生登录</div>
              <div class="lp__card-sub">Doctor Console</div>
            </div>
          </div>

          <el-form ref="formRef" :model="form" :rules="rules" class="lp__form" @keyup.enter="submit">
            <el-form-item prop="doctor_name">
              <el-input v-model="form.doctor_name" size="large" placeholder="请输入医生账号" clearable>
                <template #prefix><el-icon><User /></el-icon></template>
              </el-input>
            </el-form-item>
            <el-form-item prop="password">
              <el-input
                v-model="form.password"
                size="large"
                type="password"
                placeholder="请输入密码"
                show-password
              >
                <template #prefix><el-icon><Lock /></el-icon></template>
              </el-input>
            </el-form-item>

            <el-button type="primary" size="large" class="lp__btn" :loading="loading" @click="submit">
              登录<el-icon><ArrowRight /></el-icon>
            </el-button>

            <div class="lp__foot">
              <el-button link class="lp__link--reg" @click="router.push('/doctor/register')">申请注册</el-button>
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

import { doctorApi } from '@/api/doctor'
import { ROLE } from '@/utils/config'
import { setAuth } from '@/utils/auth'

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const formRef = ref(null)
const form = reactive({ doctor_name: '', password: '' })

const rules = {
  doctor_name: [{ required: true, message: '请输入医生账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function submit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    const { data } = await doctorApi.login({ ...form })
    setAuth(ROLE.DOCTOR, data.token, data.doctor_info)
    ElMessage.success('登录成功')
    const redirect = route.query.redirect
    router.replace(typeof redirect === 'string' && redirect.startsWith('/doctor') ? redirect : '/doctor/dashboard')
  } catch (e) {
    /* 待审核 / 审核拒绝 / 密码错误的提示均由拦截器统一弹出 */
  } finally {
    loading.value = false
  }
}
</script>

<style>
@import '@/assets/login-portal.css';
</style>
