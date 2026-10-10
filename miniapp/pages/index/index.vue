<template>
  <view class="hm-page home">
    <!-- 顶部渐变头 -->
    <view class="home__header">
      <view class="home__hello">个人健康管理 · 守护你的身体状态</view>
      <view v-if="isLogin" class="home__user">
        <image class="home__avatar" :src="avatarUrl" mode="aspectFill" />
        <text class="home__nickname">当前用户：{{ userInfo.nickname || '健康用户' }}</text>
      </view>
      <view v-else class="home__user">
        <text class="home__nickname">未登录 · 可查看公告与健康科普</text>
        <text class="home__login-btn" @tap="goLogin">去登录</text>
      </view>

      <!-- 公告滚动栏 -->
      <view v-if="notices.length" class="home__notice" @tap="goNoticeList">
        <text class="home__notice-label">公告</text>
        <swiper
          class="home__notice-swiper"
          :vertical="true"
          :autoplay="true"
          :interval="3500"
          :circular="true"
          :display-multiple-items="1"
        >
          <swiper-item v-for="item in notices" :key="item.id">
            <text class="home__notice-text">{{ item.title }}</text>
          </swiper-item>
        </swiper>
      </view>
    </view>

    <!-- 今日健康概览 -->
    <view class="hm-card">
      <view class="hm-card__title">
        <text class="hm-title-text">今日健康概览</text>
        <text class="hm-item__meta">{{ overview.today_date || '' }}</text>
      </view>

      <view v-if="!isLogin" class="hm-empty">登录后查看今日体重、血压与睡眠数据</view>
      <view v-else class="overview">
        <view class="overview__item">
          <view class="overview__value">
            {{ today.weight !== null ? today.weight : '--' }}
            <text class="overview__unit">kg</text>
          </view>
          <view class="overview__label">今日体重</view>
        </view>
        <view class="overview__item">
          <view class="overview__value">
            {{ today.blood_pressure_high !== null ? today.blood_pressure_high : '--'
            }}<text class="overview__unit">/</text>{{
              today.blood_pressure_low !== null ? today.blood_pressure_low : '--'
            }}
            <text class="overview__unit">mmHg</text>
          </view>
          <view class="overview__label">今日血压</view>
        </view>
        <view class="overview__item">
          <view class="overview__value">
            {{ sleepHours }}
            <text class="overview__unit">h</text>
          </view>
          <view class="overview__label">最近一次睡眠</view>
        </view>
      </view>
    </view>

    <!-- 健康预警（仅提醒，不做诊断） -->
    <view v-if="isLogin && overview.alert && overview.alert.has_alert" class="hm-card">
      <view class="hm-card__title"><text class="hm-title-text">健康提醒</text></view>
      <view class="hm-alert">
        <text>{{ alertTip }}</text>
      </view>
      <view v-if="overview.alert.items && overview.alert.items.length" class="alert-items">
        <text v-for="(item, idx) in overview.alert.items" :key="idx" class="alert-item">· {{ item }}</text>
      </view>
      <view class="hm-tip" style="margin-top: 14rpx">
        本提示仅为健康提醒，系统不会自动诊断疾病、不会生成处方或推荐药物。
      </view>
    </view>

    <!-- 快捷功能 -->
    <view class="hm-card">
      <view class="hm-card__title"><text class="hm-title-text">快捷功能</text></view>
      <view class="quick">
        <view v-for="item in quickItems" :key="item.key" class="quick__item" @tap="handleQuick(item)">
          <view class="quick__icon" :style="{ background: item.bg }">
            <text class="quick__icon-text">{{ item.icon }}</text>
          </view>
          <text class="quick__label">{{ item.label }}</text>
        </view>
      </view>
    </view>

    <!-- 健康科普推荐 -->
    <view class="hm-card">
      <view class="hm-card__title">
        <text class="hm-title-text">健康科普</text>
        <text class="hm-link" @tap="goArticleList">更多 ›</text>
      </view>
      <view v-if="!articles.length" class="hm-empty">暂无文章</view>
      <view
        v-for="item in articles"
        :key="item.id"
        class="article-row"
        @tap="goArticleDetail(item.id)"
      >
        <image class="article-row__cover" :src="imgSrc(item.cover_img)" mode="aspectFill" />
        <view class="article-row__body">
          <text class="article-row__title">{{ item.title }}</text>
          <text class="article-row__meta">{{ item.publish_time }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'

import { api } from '@/api/index'
import { ensureLogin, getUserInfo, isLogin as checkLogin } from '@/common/auth'
import { imgSrc } from '@/common/image'

const isLogin = ref(false)
const userInfo = ref({})
const notices = ref([])
const articles = ref([])
const overview = ref({ today: {}, last: {}, alert: {} })

const avatarUrl = computed(() => imgSrc(userInfo.value.avatar) || '/static/tabbar/profile-active.png')
const today = computed(() => overview.value.today || {})
const sleepHours = computed(() => {
  const minutes = overview.value.last?.sleep_duration
  if (!minutes) return '--'
  return (minutes / 60).toFixed(1)
})
const alertTip = computed(
  () =>
    (overview.value.alert && overview.value.alert.tips && overview.value.alert.tips[0]) ||
    '检测到部分健康指标可能超出常见参考范围，请注意关注身体状态；如持续异常，请咨询专业医疗人员。'
)

/** 快捷功能：私人数据功能需要登录 */
const quickItems = [
  { key: 'health', label: '健康记录', icon: '记', bg: 'linear-gradient(135deg,#2E7D32,#66BB6A)', url: '/pages/health-entry/index?tab=health', needLogin: true },
  { key: 'sleep', label: '睡眠记录', icon: '眠', bg: 'linear-gradient(135deg,#3F51B5,#7986CB)', url: '/pages/health-entry/index?tab=sleep', needLogin: true },
  { key: 'sport', label: '运动记录', icon: '动', bg: 'linear-gradient(135deg,#F5872A,#FFB74D)', url: '/pages/health-entry/index?tab=sport', needLogin: true },
  { key: 'plan', label: '健康计划', icon: '划', bg: 'linear-gradient(135deg,#00897B,#4DB6AC)', url: '/pages/plan/index', needLogin: true },
  { key: 'article', label: '健康科普', icon: '科', bg: 'linear-gradient(135deg,#7A5AF8,#A98BFF)', url: '/pages/article/index', needLogin: false },
  { key: 'advice', label: '医生建议', icon: '医', bg: 'linear-gradient(135deg,#0F9D8C,#2BC4AE)', url: '/pages/doctor-advice/index', needLogin: true },
  { key: 'notice', label: '体检通知', icon: '检', bg: 'linear-gradient(135deg,#0288D1,#4FC3F7)', url: '/pages/medical-notice/index', needLogin: true },
  { key: 'fitness', label: '健身建议', icon: '健', bg: 'linear-gradient(135deg,#C2185B,#F06292)', url: '/pages/fitness-advice/index', needLogin: true },
  { key: 'training', label: '训练计划', icon: '练', bg: 'linear-gradient(135deg,#455A64,#90A4AE)', url: '/pages/training-plan/index', needLogin: true },
]

function handleQuick(item) {
  if (item.needLogin && !checkLogin()) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    setTimeout(() => uni.navigateTo({ url: '/pages/login/index' }), 600)
    return
  }
  // 「健康录入」是 TabBar 页面，必须用 switchTab 跳转；目标子 Tab 通过本地标记传递
  if (item.url.indexOf('/pages/health-entry/index') === 0) {
    const tab = (item.url.split('tab=')[1] || 'health')
    uni.setStorageSync('health_entry_tab', tab)
    uni.switchTab({ url: '/pages/health-entry/index' })
    return
  }
  uni.navigateTo({ url: item.url })
}

function goLogin() {
  uni.navigateTo({ url: '/pages/login/index' })
}

function goNoticeList() {
  uni.navigateTo({ url: '/pages/article/index?tab=notice' })
}

function goArticleList() {
  uni.navigateTo({ url: '/pages/article/index' })
}

function goArticleDetail(id) {
  uni.navigateTo({ url: `/pages/article-detail/index?id=${id}` })
}

async function loadPublic() {
  try {
    const res = await api.noticeList({ page: 1, page_size: 10 })
    notices.value = res.data.list || []
  } catch (e) {
    notices.value = []
  }
  try {
    const res = await api.articleList({ page: 1, page_size: 3 })
    articles.value = res.data.list || []
  } catch (e) {
    articles.value = []
  }
}

async function loadPrivate() {
  try {
    const info = await api.userInfo()
    userInfo.value = info.data
  } catch (e) {
    /* 401 由请求层统一处理 */
  }
  try {
    const res = await api.reportStatistics(30)
    overview.value = res.data.overview || overview.value
  } catch (e) {
    /* 忽略 */
  }
}

onShow(() => {
  isLogin.value = checkLogin()
  if (isLogin.value) {
    userInfo.value = getUserInfo() || {}
    loadPrivate()
  } else {
    userInfo.value = {}
    overview.value = { today: {}, last: {}, alert: {} }
  }
  loadPublic()
})

onPullDownRefresh(async () => {
  await loadPublic()
  if (checkLogin()) {
    isLogin.value = true
    await loadPrivate()
  }
  uni.stopPullDownRefresh()
})
</script>

<style scoped>
.home {
  padding-top: 0;
}

/* 首页卡片标题更紧凑（仅作用于首页，不改全局 .hm-card__title 规则） */
.home .hm-card__title {
  margin-bottom: 16rpx;
}

.home__header {
  margin: -24rpx -24rpx 20rpx;
  padding: 26rpx 30rpx 22rpx;
  background: linear-gradient(140deg, #2e7d32 0%, #4caf50 55%, #81c784 100%);
  border-bottom-left-radius: 32rpx;
  border-bottom-right-radius: 32rpx;
}

.home__hello {
  color: #ffffff;
  font-size: 32rpx;
  font-weight: 600;
  letter-spacing: 1rpx;
}

.home__user {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 14rpx;
}

.home__avatar {
  width: 52rpx;
  height: 52rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.4);
}

.home__nickname {
  flex: 1;
  margin-left: 16rpx;
  color: rgba(255, 255, 255, 0.92);
  font-size: 26rpx;
}

.home__login-btn {
  color: #ffffff;
  font-size: 26rpx;
  padding: 8rpx 26rpx;
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.24);
}

.home__notice {
  display: flex;
  align-items: center;
  margin-top: 16rpx;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 18rpx;
  padding: 12rpx 18rpx;
  height: 58rpx;
}

.home__notice-label {
  color: #ffffff;
  font-size: 24rpx;
  padding: 2rpx 14rpx;
  border-radius: 10rpx;
  background: rgba(255, 255, 255, 0.28);
  margin-right: 16rpx;
  flex-shrink: 0;
}

.home__notice-swiper {
  flex: 1;
  height: 40rpx;
}

.home__notice-text {
  color: rgba(255, 255, 255, 0.96);
  font-size: 25rpx;
  line-height: 40rpx;
}

.overview {
  display: flex;
  justify-content: space-between;
}

.overview__item {
  flex: 1;
  text-align: center;
}

.overview__value {
  font-size: 34rpx;
  font-weight: 700;
  color: #2e7d32;
  line-height: 1.3;
}

.overview__unit {
  font-size: 22rpx;
  font-weight: 400;
  color: #8a99a8;
  margin: 0 2rpx;
}

.overview__label {
  font-size: 24rpx;
  color: #8a99a8;
  margin-top: 8rpx;
}

.alert-items {
  margin-top: 14rpx;
}

.alert-item {
  display: block;
  font-size: 25rpx;
  color: #8a6d1a;
  line-height: 1.8;
}

.quick {
  display: flex;
  flex-wrap: wrap;
}

.quick__item {
  width: 33.333%;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 18rpx 0;
}

.quick__icon {
  width: 88rpx;
  height: 88rpx;
  border-radius: 26rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6rpx 14rpx rgba(46, 125, 50, 0.16);
}

.quick__icon-text {
  color: #ffffff;
  font-size: 32rpx;
  font-weight: 600;
}

.quick__label {
  margin-top: 12rpx;
  font-size: 24rpx;
  color: #4a5a6a;
}

.hm-link {
  font-size: 24rpx;
  color: #2e7d32;
}

.article-row {
  display: flex;
  align-items: center;
  padding: 18rpx 0;
  border-bottom: 1rpx solid #eef4ef;
}

.article-row:last-child {
  border-bottom: none;
}

.article-row__cover {
  width: 140rpx;
  height: 96rpx;
  border-radius: 16rpx;
  background: #e8f5e9;
  flex-shrink: 0;
}

.article-row__body {
  flex: 1;
  margin-left: 20rpx;
  overflow: hidden;
}

.article-row__title {
  display: block;
  font-size: 28rpx;
  color: #1f2d3d;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.article-row__meta {
  display: block;
  margin-top: 10rpx;
  font-size: 23rpx;
  color: #9aa8b5;
}
</style>
