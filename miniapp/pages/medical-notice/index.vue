<template>
  <view class="hm-page service">
    <view v-if="!logged" class="hm-card">
      <view class="hm-empty">登录后可查看医生发送给你的体检通知</view>
      <view class="hm-btn" @tap="goLogin">前往登录</view>
    </view>

    <template v-else>
      <view class="hm-card">
        <view class="hm-card__title">
          <text class="hm-title-text">体检通知</text>
          <text class="service__refresh" @tap="load">刷新</text>
        </view>

        <view v-if="loading" class="hm-empty">加载中...</view>
        <view v-else-if="!list.length" class="hm-empty">暂无体检通知</view>
        <view v-for="item in list" v-else :key="item.id" class="hm-item">
          <view class="hm-item__row">
            <text class="hm-item__title">{{ item.notice_title }}</text>
          </view>
          <view class="hm-item__row">
            <text class="hm-tag">检查时间：{{ item.check_date || '--' }}</text>
          </view>
          <view class="hm-item__content">{{ item.notice_content }}</view>
          <view class="hm-item__row service__from">
            <text class="hm-item__meta">发送医生：{{ item.doctor_name || '医生' }} · {{ item.specialty || '综合' }}</text>
          </view>
        </view>
      </view>

      <view class="hm-tip service__foot">
        请按医生建议的检查时间前往正规医疗机构完成体检。
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
    const res = await api.medicalNotice()
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

.service__from {
  margin-top: 16rpx;
  justify-content: flex-end;
}

.service__foot {
  padding: 0 8rpx 20rpx;
}
</style>
