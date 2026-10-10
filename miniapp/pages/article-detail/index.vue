<template>
  <view class="hm-page detail">
    <view v-if="loading" class="hm-empty">加载中...</view>
    <view v-else-if="!article" class="hm-empty">文章不存在或已下架</view>

    <template v-else>
      <view class="hm-card">
        <view class="detail__title">{{ article.title }}</view>
        <view class="detail__meta">
          <text class="hm-tag">作者：{{ article.author || '健康编辑部' }}</text>
          <text class="hm-item__meta">{{ article.publish_time }}</text>
        </view>
        <image
          v-if="article.cover_img"
          class="detail__cover"
          :src="imgSrc(article.cover_img)"
          mode="widthFix"
        />
        <view class="detail__content">{{ article.content }}</view>
      </view>

      <view class="hm-tip detail__foot">
        健康科普内容仅供参考，不作为医疗诊断依据；如有健康问题请咨询专业医疗人员。
      </view>
    </template>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

import { api } from '@/api/index'
import { imgSrc } from '@/common/image'

const article = ref(null)
const loading = ref(true)

onLoad(async (options) => {
  const id = options && options.id
  if (!id) {
    loading.value = false
    return
  }
  try {
    const res = await api.articleDetail(id)
    article.value = res.data || null
    if (article.value && article.value.title) {
      uni.setNavigationBarTitle({ title: article.value.title })
    }
  } catch (e) {
    article.value = null
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.detail__title {
  font-size: 38rpx;
  font-weight: 700;
  color: #1f2d3d;
  line-height: 1.5;
}

.detail__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 20rpx 0 24rpx;
  padding-bottom: 20rpx;
  border-bottom: 1rpx solid #e6f0e7;
}

.detail__cover {
  width: 100%;
  border-radius: 18rpx;
  margin-bottom: 24rpx;
  background: #e8f5e9;
}

.detail__content {
  font-size: 29rpx;
  color: #3c4a58;
  line-height: 1.9;
  word-break: break-all;
  white-space: pre-wrap;
}

.detail__foot {
  padding: 0 8rpx 20rpx;
}
</style>
