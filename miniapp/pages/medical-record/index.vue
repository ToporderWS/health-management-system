<template>
  <view class="hm-page service">
    <view v-if="!logged" class="hm-card">
      <view class="hm-empty">登录后可查看医生为你建立的医疗记录</view>
      <view class="hm-btn" @tap="goLogin">前往登录</view>
    </view>

    <template v-else>
      <view class="hm-card">
        <view class="hm-card__title">
          <text class="hm-title-text">医疗记录</text>
          <text class="service__refresh" @tap="load">刷新</text>
        </view>

        <view v-if="loading" class="hm-empty">加载中...</view>
        <view v-else-if="!list.length" class="hm-empty">暂无医疗记录</view>
        <view v-for="item in list" v-else :key="item.id" class="hm-item">
          <view class="hm-item__row">
            <text class="hm-item__title">{{ item.record_title }}</text>
            <text class="hm-item__meta">{{ (item.record_date || '').slice(0, 10) }}</text>
          </view>
          <view class="hm-item__content">{{ item.record_content }}</view>
          <view class="hm-item__row service__from">
            <text class="hm-item__meta">记录医生：{{ item.doctor_name || '医生' }} · {{ item.specialty || '综合' }}</text>
          </view>
        </view>
      </view>

      <view class="hm-tip service__foot">
        医疗记录由医生人工填写，仅用于健康管理档案留存。
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
    const res = await api.medicalRecord()
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
