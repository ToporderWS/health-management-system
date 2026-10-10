<template>
  <div class="login login--coach">
    <div class="login__panel login__panel--wide">
      <div class="login__brand">
        <div class="login__logo">
          <el-icon><Basketball /></el-icon>
        </div>
        <div>
          <div class="login__brand-title">健身教练注册申请</div>
          <div class="login__brand-sub">提交后需等待管理员审核</div>
        </div>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="92px">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="教练账号" prop="coach_name">
              <el-input v-model="form.coach_name" placeholder="3~50 位" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="真实姓名" prop="real_name">
              <el-input v-model="form.real_name" placeholder="请输入真实姓名" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="密码" prop="password">
              <el-input v-model="form.password" type="password" show-password placeholder="不少于 6 位" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="确认密码" prop="confirm_password">
              <el-input v-model="form.confirm_password" type="password" show-password placeholder="请再次输入" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="性别" prop="gender">
              <el-select v-model="form.gender" placeholder="请选择性别" style="width: 100%">
                <el-option label="男" value="男" />
                <el-option label="女" value="女" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="手机号" prop="phone">
              <el-input v-model="form.phone" placeholder="11 位手机号" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="专业方向" prop="specialty">
              <el-input v-model="form.specialty" placeholder="如：力量训练 / 普拉提 / 体能训练" clearable />
            </el-form-item>
          </el-col>
        </el-row>

        <el-alert
          type="info"
          :closable="false"
          show-icon
          title="注册后 audit_status 固定为「待审核」，通过管理员审核后方可登录工作台。"
          class="hms-mb-12"
        />

        <div class="login__actions">
          <el-button style="width: 160px" @click="router.push('/coach/login')">返回登录</el-button>
          <el-button type="primary" style="width: 200px" :loading="loading" @click="submit">
            提交注册申请
          </el-button>
          <el-button link @click="router.push('/')">身份选择</el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'

import { coachApi } from '@/api/coach'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  coach_name: '',
  password: '',
  confirm_password: '',
  real_name: '',
  gender: '',
  phone: '',
  specialty: '',
})

const rules = {
  coach_name: [
    { required: true, message: '请输入教练账号', trigger: 'blur' },
    { min: 3, max: 50, message: '账号长度需在 3~50 位之间', trigger: 'blur' },
  ],
  real_name: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (rule, value, cb) =>
        value === form.password ? cb() : cb(new Error('两次输入的密码不一致')),
      trigger: 'blur',
    },
  ],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' },
  ],
  specialty: [{ required: true, message: '请输入专业方向', trigger: 'blur' }],
}

async function submit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    const { msg } = await coachApi.register({ ...form })
    await ElMessageBox.alert(msg || '注册申请已提交，请等待管理员审核。', '提交成功', {
      confirmButtonText: '返回登录',
      type: 'success',
    })
    router.replace('/coach/login')
  } catch (e) {
    /* 错误提示由拦截器处理 */
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
@import '@/assets/login.css';
</style>
