<template>
  <view class="hm-page service">
    <view v-if="!logged" class="hm-card">
      <view class="hm-empty">登录后可查看健身教练为你填写的健身建议</view>
      <view class="hm-btn" @tap="goLogin">前往登录</view>
    </view>

    <template v-else>
      <view class="hm-card">
        <view class="hm-card__title">
          <text class="hm-title-text">健身建议</text>
          <text class="service__refresh" @tap="load">刷新</text>
        </view>

        <view v-if="loading" class="hm-empty">加载中...</view>
        <view v-else-if="!list.length" class="hm-empty">暂无健身建议</view>
        <view v-for="item in list" v-else :key="item.id" class="hm-item">
          <view class="hm-item__row">
            <text class="hm-item__title">{{ item.coach_name || '健身教练' }}</text>
            <text class="hm-item__meta">{{ item.created_at }}</text>
          </view>
          <view class="hm-item__row">
            <text class="hm-tag">{{ item.specialty || '综合' }}</text>
          </view>
          <view class="hm-item__content">{{ item.advice_content }}</view>
        </view>
      </view>

      <view class="hm-tip service__foot">
        健身建议由教练人工填写，运动前请评估自身身体状况，如有不适请停止训练。
      </view>
    </template>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'

import { api } from '@/api/index'
import { isLogin } from '@/common/auth'

const logged = ref(false)
const loading = ref(false)
const list = ref([])

function goLogin() {
  uni.navigateTo({ url: '/pages/login/index' })
}

async function load() {
  logged.value = isLogin()
  if (!logged.value) {
    list.value = []
    return
  }
  loading.value = true
  try {
    const res = await api.fitnessAdvice()
    list.value = res.data || []
  } catch (e) {
    list.value = []
  } finally {
    loading.value = false
  }
}

onShow(() => {
  load()
})

onPullDownRefresh(async () => {
  await load()
  uni.stopPullDownRefresh()
})
</script>

<style scoped>
.service__refresh {
  font-size: 24rpx;
  color: #2e7d32;
  font-weight: 400;
}

.service__foot {
  padding: 0 8rpx 20rpx;
}
</style>
