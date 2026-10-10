<template>
  <view class="hm-page service">
    <view v-if="!logged" class="hm-card">
      <view class="hm-empty">登录后可查看医生为你填写的健康建议</view>
      <view class="hm-btn" @tap="goLogin">前往登录</view>
    </view>

    <template v-else>
      <view class="hm-card">
        <view class="hm-card__title">
          <text class="hm-title-text">医生健康建议</text>
          <text class="service__refresh" @tap="load">刷新</text>
        </view>

        <view v-if="loading" class="hm-empty">加载中...</view>
        <view v-else-if="!list.length" class="hm-empty">暂无医生健康建议</view>
        <view v-for="item in list" v-else :key="item.id" class="hm-item">
          <view class="hm-item__row">
            <text class="hm-item__title">{{ item.doctor_name || '医生' }}</text>
            <text class="hm-item__meta">{{ item.created_at }}</text>
          </view>
          <view class="hm-item__row">
            <text class="hm-tag">{{ item.specialty || '综合' }}</text>
          </view>
          <view class="hm-item__content">{{ item.advice_content }}</view>
        </view>
      </view>

      <view class="hm-tip service__foot">
        健康建议由医生人工填写，仅作健康管理参考，不作为疾病诊断依据。
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
    const res = await api.doctorAdvice()
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
