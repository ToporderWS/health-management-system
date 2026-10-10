<template>
  <view class="hm-page service">
    <view v-if="!logged" class="hm-card">
      <view class="hm-empty">登录后可查看健身教练为你制定的运动目标</view>
      <view class="hm-btn" @tap="goLogin">前往登录</view>
    </view>

    <template v-else>
      <view class="hm-card">
        <view class="hm-card__title">
          <text class="hm-title-text">运动目标</text>
          <text class="service__refresh" @tap="load">刷新</text>
        </view>

        <view v-if="loading" class="hm-empty">加载中...</view>
        <view v-else-if="!list.length" class="hm-empty">暂无运动目标</view>
        <view v-for="item in list" v-else :key="item.id" class="hm-item">
          <view class="hm-item__row">
            <text class="hm-item__title">{{ item.goal_title }}</text>
            <text
              class="hm-tag"
              :class="{ 'hm-tag--gray': item.goal_status !== 0 }"
            >{{ statusText(item.goal_status) }}</text>
          </view>
          <view class="hm-item__row">
            <text class="hm-item__meta">{{ (item.start_date || '').slice(0, 10) }} ~ {{ (item.end_date || '').slice(0, 10) }}</text>
          </view>
          <view class="hm-item__content">{{ item.goal_content }}</view>
          <view class="hm-item__row service__from">
            <text class="hm-item__meta">教练：{{ item.coach_name || '健身教练' }} · {{ item.specialty || '综合' }}</text>
          </view>
        </view>
      </view>

      <view class="hm-tip service__foot">
        运动目标状态：0 = 进行中，1 = 已完成，2 = 已结束。
      </view>
    </template>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'

import { api } from '@/api/index'
import { isLogin } from '@/common/auth'
import { SPORT_STATUS_TEXT } from '@/common/config'

const logged = ref(false)
const loading = ref(false)
const list = ref([])

function statusText(status) {
  return SPORT_STATUS_TEXT[status] || '未知'
}

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
    const res = await api.sportGoal()
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
