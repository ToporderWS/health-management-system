<template>
  <view class="hm-page plan">
    <!-- 新建计划 -->
    <view class="hm-card">
      <view class="hm-card__title">
        <text class="hm-title-text">新建健康计划</text>
        <text class="plan__toggle" @tap="formVisible = !formVisible">{{ formVisible ? '收起' : '展开' }}</text>
      </view>

      <template v-if="formVisible">
        <view class="hm-field">
          <text class="hm-field__label">计划标题</text>
          <input class="hm-field__input" maxlength="100" placeholder="如 每日减脂计划" placeholder-class="ph"
            :value="form.plan_title" @input="form.plan_title = $event.detail.value" />
        </view>
        <picker mode="date" :value="form.plan_start" @change="form.plan_start = $event.detail.value">
          <view class="hm-field">
            <text class="hm-field__label">开始日期</text>
            <text class="hm-field__input">{{ form.plan_start }}</text>
          </view>
        </picker>
        <picker mode="date" :value="form.plan_end" @change="form.plan_end = $event.detail.value">
          <view class="hm-field">
            <text class="hm-field__label">结束日期</text>
            <text class="hm-field__input">{{ form.plan_end }}</text>
          </view>
        </picker>
        <view class="plan__textarea-wrap">
          <text class="plan__textarea-label">计划内容</text>
          <textarea class="plan__textarea" maxlength="1000" placeholder="请填写计划的具体内容" placeholder-class="ph"
            :value="form.plan_content" @input="form.plan_content = $event.detail.value" />
        </view>
        <view class="hm-btn" :class="{ 'hm-btn--disabled': submitting }" @tap="submit">
          {{ submitting ? '提交中...' : '创建计划' }}
        </view>
      </template>
    </view>

    <!-- 状态筛选 -->
    <view class="plan__filter">
      <view
        v-for="f in filters"
        :key="String(f.value)"
        class="plan__filter-item"
        :class="{ 'plan__filter-item--active': status === f.value }"
        @tap="switchStatus(f.value)"
      >{{ f.label }}</view>
    </view>

    <!-- 计划列表（真实数据库数据） -->
    <view class="hm-card">
      <view class="hm-card__title">
        <text class="hm-title-text">我的健康计划</text>
        <text class="plan__toggle" @tap="load">刷新</text>
      </view>

      <view v-if="loading" class="hm-empty">加载中...</view>
      <view v-else-if="!list.length" class="hm-empty">暂无健康计划</view>
      <view v-for="item in list" v-else :key="item.id" class="hm-item">
        <view class="hm-item__row">
          <text class="hm-item__title">{{ item.plan_title }}</text>
          <text
            class="hm-tag"
            :class="{ 'hm-tag--gray': item.plan_status !== 0, 'hm-tag--orange': item.plan_status === 2 }"
          >{{ item.plan_status_text }}</text>
        </view>
        <view class="hm-item__row">
          <text class="hm-item__meta">{{ item.plan_start }} ~ {{ item.plan_end }}</text>
        </view>
        <view class="hm-item__content">{{ item.plan_content }}</view>
        <view class="plan__actions">
          <text
            v-for="a in actions"
            :key="a.value"
            class="plan__action"
            :class="{ 'plan__action--active': item.plan_status === a.value }"
            @tap="updateStatus(item, a.value)"
          >{{ a.label }}</text>
        </view>
      </view>

      <view v-if="hasMore" class="plan__more" @tap="loadMore">
        {{ loadingMore ? '加载中...' : '加载更多' }}
      </view>
    </view>

    <view class="hm-tip plan__foot">
      计划状态：0 = 进行中，1 = 已完成，2 = 已放弃。
    </view>
  </view>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { onLoad, onReachBottom, onPullDownRefresh } from '@dcloudio/uni-app'

import { api } from '@/api/index'
import { ensureLogin, isLogin } from '@/common/auth'

const formVisible = ref(true)
const submitting = ref(false)
const loading = ref(false)
const loadingMore = ref(false)
const list = ref([])
const page = ref(1)
const pageSize = 10
const hasMore = ref(false)
const status = ref('')

const filters = [
  { label: '全部', value: '' },
  { label: '进行中', value: 0 },
  { label: '已完成', value: 1 },
  { label: '已放弃', value: 2 },
]

const actions = [
  { label: '进行中', value: 0 },
  { label: '已完成', value: 1 },
  { label: '已放弃', value: 2 },
]

function today() {
  const d = new Date()
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}

const form = reactive({
  plan_title: '',
  plan_content: '',
  plan_start: today(),
  plan_end: today(),
})

function switchStatus(value) {
  status.value = value
  load()
}

async function fetchPage(reset) {
  if (!isLogin()) {
    list.value = []
    hasMore.value = false
    return
  }
  const target = reset ? 1 : page.value + 1
  if (reset) loading.value = true
  else loadingMore.value = true
  try {
    const res = await api.healthPlanList({
      page: target,
      page_size: pageSize,
      plan_status: status.value === '' ? undefined : status.value,
    })
    const rows = (res.data && res.data.list) || []
    const total = (res.data && res.data.total) || 0
    list.value = reset ? rows : list.value.concat(rows)
    page.value = target
    hasMore.value = list.value.length < total
  } catch (e) {
    if (reset) list.value = []
    hasMore.value = false
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function load() {
  fetchPage(true)
}

function loadMore() {
  if (!hasMore.value || loadingMore.value) return
  fetchPage(false)
}

async function submit() {
  if (submitting.value) return
  if (!form.plan_title.trim()) return uni.showToast({ title: '请填写计划标题', icon: 'none' })
  if (!form.plan_content.trim()) return uni.showToast({ title: '请填写计划内容', icon: 'none' })
  if (form.plan_end < form.plan_start) {
    return uni.showToast({ title: '结束日期不能早于开始日期', icon: 'none' })
  }
  if (!ensureLogin()) return

  submitting.value = true
  try {
    const res = await api.addHealthPlan({ ...form })
    uni.showToast({ title: res.msg || '创建成功', icon: 'success' })
    form.plan_title = ''
    form.plan_content = ''
    load()
  } catch (e) {
    /* 忽略 */
  } finally {
    submitting.value = false
  }
}

async function updateStatus(item, value) {
  if (item.plan_status === value) return
  try {
    const res = await api.updatePlanStatus({ id: item.id, plan_status: value })
    uni.showToast({ title: res.msg || '状态已更新', icon: 'success' })
    load()
  } catch (e) {
    /* 忽略 */
  }
}

onLoad(() => {
  load()
})

onPullDownRefresh(async () => {
  await fetchPage(true)
  uni.stopPullDownRefresh()
})

onReachBottom(() => {
  loadMore()
})
</script>

<style scoped>
.plan__toggle {
  font-size: 24rpx;
  color: #2e7d32;
  font-weight: 400;
}

.plan__textarea-wrap {
  padding: 22rpx 0 0;
}

.plan__textarea-label {
  display: block;
  color: #5c6b7a;
  font-size: 28rpx;
  margin-bottom: 14rpx;
}

.plan__textarea {
  width: 100%;
  min-height: 200rpx;
  background: #f7fbf7;
  border-radius: 16rpx;
  padding: 20rpx;
  box-sizing: border-box;
  font-size: 27rpx;
  color: #1f2d3d;
}

.plan__filter {
  display: flex;
  margin-bottom: 24rpx;
}

.plan__filter-item {
  flex: 1;
  text-align: center;
  padding: 16rpx 0;
  font-size: 26rpx;
  color: #7a8b9a;
  background: #ffffff;
  border-radius: 36rpx;
  margin-right: 14rpx;
  box-shadow: 0 4rpx 14rpx rgba(46, 125, 50, 0.05);
}

.plan__filter-item:last-child {
  margin-right: 0;
}

.plan__filter-item--active {
  background: #2e7d32;
  color: #ffffff;
  font-weight: 600;
}

.plan__actions {
  display: flex;
  margin-top: 20rpx;
}

.plan__action {
  padding: 8rpx 20rpx;
  margin-right: 14rpx;
  border-radius: 30rpx;
  font-size: 24rpx;
  color: #7a8b9a;
  background: #f1f6f1;
}

.plan__action--active {
  background: #2e7d32;
  color: #ffffff;
}

.plan__more {
  text-align: center;
  padding: 22rpx 0 4rpx;
  color: #2e7d32;
  font-size: 27rpx;
}

.plan__foot {
  padding: 0 8rpx 20rpx;
}

.ph {
  color: #b6c2cd;
}
</style>
