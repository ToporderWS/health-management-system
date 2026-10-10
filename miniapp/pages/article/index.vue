<template>
  <view class="hm-page article">
    <!-- 顶部 Tab -->
    <view class="article__tabs">
      <view
        class="article__tab"
        :class="{ 'article__tab--active': tab === 'article' }"
        @tap="switchTab('article')"
      >健康科普</view>
      <view
        class="article__tab"
        :class="{ 'article__tab--active': tab === 'notice' }"
        @tap="switchTab('notice')"
      >系统公告</view>
    </view>

    <!-- 搜索 -->
    <view class="article__search">
      <input
        class="article__search-input"
        :value="keyword"
        placeholder="搜索标题 / 作者"
        placeholder-class="ph"
        confirm-type="search"
        @input="keyword = $event.detail.value"
        @confirm="reload"
      />
      <text class="article__search-btn" @tap="reload">搜索</text>
    </view>

    <!-- 健康科普列表 -->
    <template v-if="tab === 'article'">
      <view v-if="loading" class="hm-empty">加载中...</view>
      <view v-else-if="!list.length" class="hm-empty">暂无健康科普文章</view>
      <view
        v-for="item in list"
        v-else
        :key="item.id"
        class="hm-card article__item"
        @tap="goDetail(item.id)"
      >
        <image
          v-if="item.cover_img"
          class="article__cover"
          :src="imgSrc(item.cover_img)"
          mode="aspectFill"
        />
        <view v-else class="article__cover article__cover--empty">健康科普</view>
        <view class="article__body">
          <text class="article__title">{{ item.title }}</text>
          <view class="article__meta">
            <text class="hm-tag">作者：{{ item.author || '健康编辑部' }}</text>
            <text class="hm-item__meta">{{ item.publish_time }}</text>
          </view>
        </view>
      </view>
    </template>

    <!-- 系统公告列表 -->
    <template v-else>
      <view v-if="loading" class="hm-empty">加载中...</view>
      <view v-else-if="!list.length" class="hm-empty">暂无系统公告</view>
      <view v-for="item in list" v-else :key="item.id" class="hm-card article__notice">
        <view class="article__notice-title">{{ item.title }}</view>
        <view class="article__notice-time">{{ item.publish_time }}</view>
        <view class="article__notice-content">{{ item.content }}</view>
      </view>
    </template>

    <!-- 分页 -->
    <view v-if="list.length && hasMore" class="article__more" @tap="loadMore">
      {{ loadingMore ? '加载中...' : '加载更多' }}
    </view>
    <view v-else-if="list.length" class="article__no-more">— 已经到底了 —</view>

    <view class="hm-tip article__foot">
      健康科普与系统公告无需登录即可查看。
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad, onPullDownRefresh, onReachBottom } from '@dcloudio/uni-app'

import { api } from '@/api/index'
import { imgSrc } from '@/common/image'

const tab = ref('article')
const keyword = ref('')
const list = ref([])
const page = ref(1)
const pageSize = 10
const hasMore = ref(false)
const loading = ref(false)
const loadingMore = ref(false)

function switchTab(key) {
  if (tab.value === key) return
  tab.value = key
  reload()
}

async function fetchPage(reset) {
  const target = reset ? 1 : page.value + 1
  if (reset) loading.value = true
  else loadingMore.value = true
  try {
    const res =
      tab.value === 'article'
        ? await api.articleList({ page: target, page_size: pageSize, keyword: keyword.value || undefined })
        : await api.noticeList({ page: target, page_size: pageSize, keyword: keyword.value || undefined })
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

function reload() {
  fetchPage(true)
}

function loadMore() {
  if (!hasMore.value || loadingMore.value) return
  fetchPage(false)
}

function goDetail(id) {
  uni.navigateTo({ url: `/pages/article-detail/index?id=${id}` })
}

onLoad((options) => {
  if (options && options.tab === 'notice') tab.value = 'notice'
  reload()
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
.article__tabs {
  display: flex;
  background: #ffffff;
  border-radius: 44rpx;
  padding: 8rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 4rpx 16rpx rgba(46, 125, 50, 0.06);
}

.article__tab {
  flex: 1;
  text-align: center;
  padding: 18rpx 0;
  font-size: 28rpx;
  color: #7a8b9a;
  border-radius: 36rpx;
}

.article__tab--active {
  background: linear-gradient(135deg, #2e7d32 0%, #66bb6a 100%);
  color: #ffffff;
  font-weight: 600;
  box-shadow: 0 6rpx 14rpx rgba(46, 125, 50, 0.22);
}

.article__search {
  display: flex;
  align-items: center;
  background: #ffffff;
  border-radius: 44rpx;
  padding: 8rpx 8rpx 8rpx 30rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 4rpx 16rpx rgba(46, 125, 50, 0.06);
}

.article__search-input {
  flex: 1;
  font-size: 27rpx;
  color: #1f2d3d;
}

.article__search-btn {
  padding: 14rpx 30rpx;
  border-radius: 34rpx;
  background: linear-gradient(135deg, #2e7d32, #66bb6a);
  color: #ffffff;
  font-size: 26rpx;
}

.article__item {
  display: flex;
  align-items: center;
  padding: 20rpx;
}

.article__cover {
  width: 180rpx;
  height: 130rpx;
  border-radius: 16rpx;
  flex-shrink: 0;
  background: #e8f5e9;
}

.article__cover--empty {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #2e7d32;
  font-size: 24rpx;
}

.article__body {
  flex: 1;
  margin-left: 20rpx;
  min-width: 0;
}

.article__title {
  font-size: 29rpx;
  font-weight: 600;
  color: #1f2d3d;
  line-height: 1.5;
}

.article__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 18rpx;
}

.article__notice-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #1f2d3d;
}

.article__notice-time {
  font-size: 23rpx;
  color: #8a99a8;
  margin: 10rpx 0 14rpx;
}

.article__notice-content {
  font-size: 27rpx;
  color: #4a5a6a;
  line-height: 1.75;
  word-break: break-all;
}

.article__more {
  text-align: center;
  padding: 26rpx 0;
  color: #2e7d32;
  font-size: 27rpx;
}

.article__no-more {
  text-align: center;
  padding: 26rpx 0;
  color: #a8b5bf;
  font-size: 24rpx;
}

.article__foot {
  padding: 0 8rpx 20rpx;
}

.ph {
  color: #b6c2cd;
}
</style>
