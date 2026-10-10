<template>
  <view class="hm-page login">
    <view class="login__brand">
      <view class="login__logo">健</view>
      <view class="login__title">个人健康管理系统</view>
      <view class="login__sub">记录健康数据 · 查看健康趋势</view>
    </view>

    <view class="hm-card">
      <view class="hm-card__title"><text class="hm-title-text">账号登录</text></view>

      <view class="hm-field">
        <text class="hm-field__label">手机号</text>
        <input
          class="hm-field__input"
          type="number"
          maxlength="11"
          :value="form.phone"
          placeholder="请输入 11 位手机号"
          placeholder-class="ph"
          @input="onInput('phone', $event)"
        />
      </view>

      <view class="hm-field">
        <text class="hm-field__label">密码</text>
        <input
          class="hm-field__input"
          :password="!showPwd"
          :value="form.password"
          placeholder="请输入密码"
          placeholder-class="ph"
          @input="onInput('password', $event)"
        />
        <text class="pwd-toggle" @tap="showPwd = !showPwd">{{ showPwd ? '隐藏' : '显示' }}</text>
      </view>

      <view class="hm-btn" :class="{ 'hm-btn--disabled': loading }" @tap="submit">
        {{ loading ? '登录中...' : '登 录' }}
      </view>

      <view class="login__actions">
        <text class="login__link" @tap="goRegister">还没有账号？立即注册</text>
        <text class="login__link login__link--gray" @tap="backHome">返回首页</text>
      </view>
    </view>

    <view class="hm-tip login__tip">
      登录后可记录健康指标、睡眠与运动数据，查看健康趋势，并接收医生健康建议与教练训练计划。
    </view>
  </view>
</template>

<script setup>
import { reactive, ref } from 'vue'

import { api } from '@/api/index'
import { setAuth } from '@/common/auth'

const loading = ref(false)
const showPwd = ref(false)
const form = reactive({ phone: '', password: '' })

function onInput(key, e) {
  form[key] = e.detail.value
}

function goRegister() {
  uni.navigateTo({ url: '/pages/register/index' })
}

function backHome() {
  uni.switchTab({ url: '/pages/index/index' })
}

async function submit() {
  if (loading.value) return
  if (!/^1[3-9]\d{9}$/.test(form.phone)) {
    uni.showToast({ title: '请输入正确的手机号', icon: 'none' })
    return
  }
  if (!form.password || form.password.length < 6) {
    uni.showToast({ title: '密码长度不能少于 6 位', icon: 'none' })
    return
  }
  loading.value = true
  try {
    const res = await api.login({ phone: form.phone, password: form.password })
    setAuth(res.data.token, res.data.user_info)
    uni.showToast({ title: '登录成功', icon: 'success' })
    setTimeout(() => {
      uni.switchTab({ url: '/pages/index/index' })
    }, 800)
  } catch (e) {
    /* 错误提示由请求层统一处理 */
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login__brand {
  text-align: center;
  padding: 60rpx 0 40rpx;
}

.login__logo {
  width: 128rpx;
  height: 128rpx;
  margin: 0 auto 24rpx;
  border-radius: 36rpx;
  background: linear-gradient(135deg, #2e7d32 0%, #66bb6a 100%);
  color: #ffffff;
  font-size: 56rpx;
  font-weight: 700;
  line-height: 128rpx;
  box-shadow: 0 12rpx 28rpx rgba(46, 125, 50, 0.28);
}

.login__title {
  font-size: 38rpx;
  font-weight: 700;
  color: #1f2d3d;
}

.login__sub {
  margin-top: 12rpx;
  font-size: 25rpx;
  color: #8a99a8;
}

.ph {
  color: #b6c2cd;
}

.pwd-toggle {
  font-size: 25rpx;
  color: #2e7d32;
  margin-left: 16rpx;
}

.login__actions {
  display: flex;
  justify-content: space-between;
  margin-top: 28rpx;
}

.login__link {
  font-size: 25rpx;
  color: #2e7d32;
}

.login__link--gray {
  color: #8a99a8;
}

.login__tip {
  margin-top: 10rpx;
  padding: 0 8rpx;
}
</style>
