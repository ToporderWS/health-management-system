<template>
  <view class="hm-page">
    <view class="hm-card">
      <view class="hm-card__title"><text class="hm-title-text">注册新账号</text></view>

      <view class="hm-field">
        <text class="hm-field__label">昵称</text>
        <input
          class="hm-field__input"
          maxlength="20"
          :value="form.nickname"
          placeholder="请输入昵称"
          placeholder-class="ph"
          @input="onInput('nickname', $event)"
        />
      </view>

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
          placeholder="不少于 6 位"
          placeholder-class="ph"
          @input="onInput('password', $event)"
        />
        <text class="pwd-toggle" @tap="showPwd = !showPwd">{{ showPwd ? '隐藏' : '显示' }}</text>
      </view>

      <view class="hm-field">
        <text class="hm-field__label">性别</text>
        <view class="gender">
          <text
            v-for="item in genderOptions"
            :key="item"
            class="gender__item"
            :class="{ 'gender__item--active': form.gender === item }"
            @tap="form.gender = item"
          >
            {{ item }}
          </text>
        </view>
      </view>

      <view class="hm-field">
        <text class="hm-field__label">年龄</text>
        <input
          class="hm-field__input"
          type="number"
          maxlength="3"
          :value="form.age"
          placeholder="请输入年龄"
          placeholder-class="ph"
          @input="onInput('age', $event)"
        />
        <text class="hm-field__unit">岁</text>
      </view>

      <view class="hm-field">
        <text class="hm-field__label">身高</text>
        <input
          class="hm-field__input"
          type="digit"
          maxlength="6"
          :value="form.height"
          placeholder="请输入身高"
          placeholder-class="ph"
          @input="onInput('height', $event)"
        />
        <text class="hm-field__unit">cm</text>
      </view>

      <view class="hm-btn" :class="{ 'hm-btn--disabled': loading }" @tap="submit">
        {{ loading ? '提交中...' : '注 册' }}
      </view>

      <view class="hm-btn hm-btn--plain" @tap="backLogin">返回登录</view>
    </view>

    <view class="hm-tip">
      注册成功后可直接登录。健康数据全部保存在服务器数据库中，请放心使用。
    </view>
  </view>
</template>

<script setup>
import { reactive, ref } from 'vue'

import { api } from '@/api/index'

const loading = ref(false)
const showPwd = ref(false)
const genderOptions = ['男', '女', '保密']

const form = reactive({
  nickname: '',
  phone: '',
  password: '',
  gender: '男',
  age: '',
  height: '',
})

function onInput(key, e) {
  form[key] = e.detail.value
}

function backLogin() {
  uni.navigateBack()
}

function validate() {
  if (!form.nickname || form.nickname.trim().length === 0) {
    uni.showToast({ title: '请输入昵称', icon: 'none' })
    return false
  }
  if (form.nickname.trim().length > 20) {
    uni.showToast({ title: '昵称不能超过 20 个字', icon: 'none' })
    return false
  }
  if (!/^1[3-9]\d{9}$/.test(form.phone)) {
    uni.showToast({ title: '请输入正确的手机号', icon: 'none' })
    return false
  }
  if (!form.password || form.password.length < 6) {
    uni.showToast({ title: '密码长度不能少于 6 位', icon: 'none' })
    return false
  }
  const age = Number(form.age)
  if (!age || age < 1 || age > 120) {
    uni.showToast({ title: '年龄需在 1~120 之间', icon: 'none' })
    return false
  }
  const height = Number(form.height)
  if (!height || height < 50 || height > 250) {
    uni.showToast({ title: '身高需在 50~250cm 之间', icon: 'none' })
    return false
  }
  return true
}

async function submit() {
  if (loading.value) return
  if (!validate()) return
  loading.value = true
  try {
    await api.register({
      nickname: form.nickname.trim(),
      phone: form.phone,
      password: form.password,
      gender: form.gender,
      age: Number(form.age),
      height: Number(form.height),
    })
    uni.showToast({ title: '注册成功，请登录', icon: 'success' })
    setTimeout(() => {
      uni.redirectTo({ url: '/pages/login/index' })
    }, 900)
  } catch (e) {
    /* 错误提示由请求层统一处理 */
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.ph {
  color: #b6c2cd;
}

.pwd-toggle {
  font-size: 25rpx;
  color: #2e7d32;
  margin-left: 16rpx;
}

.gender {
  flex: 1;
  display: flex;
  justify-content: flex-end;
}

.gender__item {
  padding: 8rpx 28rpx;
  margin-left: 16rpx;
  border-radius: 30rpx;
  font-size: 26rpx;
  color: #7a8b9a;
  background: #f2f7f3;
}

.gender__item--active {
  color: #ffffff;
  background: linear-gradient(135deg, #2e7d32 0%, #66bb6a 100%);
}
</style>
